"""Stage L: instruction fine-tuning of the 200k-step base model.

Same skeleton as Stage G -- auto-resume, a wall-clock checkpoint every
`--ckpt-interval-s`, and an immediate save on SIGTERM/SIGUSR1 -- because the
cluster's QOS `training` limits still apply (15 min wall, 4 CPUs, 1 GPU).

Three deliberate differences from pre-training:

  * Weights are loaded from `checkpoints/step_0200000.pt`. The architecture
    comes from that checkpoint's own `model_config`, not from a hardcoded
    constructor, so the fine-tuned model is guaranteed to match the base.
  * Fine-tuning checkpoints go to a SEPARATE directory (`checkpoints_ft/`).
    The 200k-step pre-training checkpoint is never overwritten.
  * The optimizer is re-created fresh and `step` restarts at 0 with a short
    warmup and a much lower peak LR. Carrying the pre-training optimizer
    state and its 200k-step cosine schedule into a fine-tune would be wrong:
    the loss landscape and the data distribution have both changed.

Data is `data/instruct_tokens/shards/` from Stage K; the last shard is held
out for validation.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import random
import signal
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import ModelConfig, TransformerLM

ROOT = os.path.expanduser("~/bdw-llm")
SHARD_DIR = os.path.join(ROOT, "data/instruct_tokens/shards")
CKPT_DIR = os.path.join(ROOT, "checkpoints_ft")
BASE_CKPT = os.path.join(ROOT, "checkpoints/step_0200000.pt")
LOG_DIR = os.path.join(ROOT, "logs")
CKPT_PREFIX = "step_"

_stop_requested = False


def handle_signal(signum, frame):
    global _stop_requested
    _stop_requested = True
    print("\n[signal] %d received -> will checkpoint and stop" % signum, flush=True)


def parse_args():
    p = argparse.ArgumentParser(description="BDW instruction fine-tuning")
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--seq-len", type=int, default=1024)
    p.add_argument("--lr", type=float, default=3e-5)
    p.add_argument("--min-lr", type=float, default=3e-6)
    p.add_argument("--warmup-steps", type=int, default=100)
    p.add_argument("--total-steps", type=int, default=3000)
    p.add_argument("--weight-decay", type=float, default=0.1)
    p.add_argument("--beta1", type=float, default=0.9)
    p.add_argument("--beta2", type=float, default=0.95)
    p.add_argument("--grad-clip", type=float, default=1.0)
    p.add_argument("--ckpt-interval-s", type=float, default=300.0)
    p.add_argument("--log-interval", type=int, default=20)
    p.add_argument("--eval-interval", type=int, default=100)
    p.add_argument("--keep-ckpt", type=int, default=3)
    p.add_argument("--seed", type=int, default=1337)
    p.add_argument("--val-shards", type=int, default=1,
                   help="reserve the last N shards as held-out validation")
    p.add_argument("--no-resume", action="store_true",
                   help="ignore checkpoints_ft/ and restart from the base model")
    p.add_argument("--max-steps", type=int, default=0,
                   help="stop after this many steps in THIS invocation (0 = no cap)")
    p.add_argument("--base-ckpt", default=BASE_CKPT,
                   help="pre-training checkpoint whose weights we start from")
    p.add_argument("--ckpt-dir", default=CKPT_DIR,
                   help="where fine-tune checkpoints are written (never the base dir)")
    p.add_argument("--eval-only", action="store_true",
                   help="report held-out loss for --eval-ckpt and exit (no training)")
    p.add_argument("--eval-ckpt", default="",
                   help="checkpoint to score in --eval-only mode")
    return p.parse_args()


def lr_at(step: int, a) -> float:
    if step < a.warmup_steps:
        return a.lr * (step + 1) / max(a.warmup_steps, 1)
    if step >= a.total_steps:
        return a.min_lr
    prog = (step - a.warmup_steps) / max(a.total_steps - a.warmup_steps, 1)
    cos = 0.5 * (1.0 + math.cos(math.pi * prog))
    return a.min_lr + (a.lr - a.min_lr) * cos


def set_lr(opt, lr):
    for g in opt.param_groups:
        g["lr"] = lr


def load_shards(val_shards=1):
    paths = sorted(glob.glob(os.path.join(SHARD_DIR, "shard_*.npy")))
    if not paths:
        raise SystemExit("no shards in %s" % SHARD_DIR)
    if not 0 <= val_shards < len(paths):
        raise SystemExit("--val-shards=%d invalid for %d shards"
                         % (val_shards, len(paths)))

    def load(ps):
        return [(p, np.load(p, mmap_mode="r")) for p in ps]

    return (load(paths[:len(paths) - val_shards]),
            load(paths[len(paths) - val_shards:]))


def shard_stats(shards):
    rows = sum(int(a.shape[0]) for _, a in shards)
    toks = sum(int(a.shape[0]) * int(a.shape[1]) for _, a in shards)
    return rows, toks


def get_batch(shards, batch_size, device, rng):
    p, arr = shards[rng.randrange(len(shards))]
    n = arr.shape[0]
    idx = rng.sample(range(n), min(batch_size, n))
    rows = arr[idx]
    x = torch.from_numpy(np.ascontiguousarray(rows)).long().to(device, non_blocking=True)
    y = torch.roll(x, shifts=-1, dims=1)
    y[:, -1] = 0
    return x, y.to(device, non_blocking=True)


def find_latest_ckpt(ckpt_dir):
    files = sorted(glob.glob(os.path.join(ckpt_dir, CKPT_PREFIX + "*.pt")))
    return files[-1] if files else None


def save_ckpt(path, model, opt, step, tokens_seen, args, losses, meta=None):
    payload = {
        "model": model.state_dict(),
        "optimizer": opt.state_dict(),
        "step": step,
        "tokens_seen": tokens_seen,
        "model_config": model.cfg.to_dict(),
        "train_args": vars(args),
        "losses": losses[-200:],
        "stage": "L",
        "torch_version": torch.__version__,
        "saved_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    tmp = path + ".tmp"
    torch.save(payload, tmp)
    os.replace(tmp, path)
    info = {"step": step, "tokens_seen": tokens_seen,
            "saved_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    if meta:
        info.update(meta)
    with open(path + ".meta", "w") as fh:
        json.dump(info, fh, indent=2)


def rotate_ckpts(ckpt_dir, keep):
    files = sorted(glob.glob(os.path.join(ckpt_dir, CKPT_PREFIX + "*.pt")))
    for f in files[:-keep] if keep > 0 else []:
        try:
            os.remove(f)
            if os.path.exists(f + ".meta"):
                os.remove(f + ".meta")
            print("[ckpt] rotated out", os.path.basename(f), flush=True)
        except OSError as e:
            print("[ckpt] could not remove %s: %s" % (f, e), flush=True)


def val_loss(model, val_shards, batch_size, device, rng, rounds=4):
    model.eval()
    with torch.no_grad():
        ev = []
        for _ in range(rounds):
            ex, ey = get_batch(val_shards, batch_size, device, rng)
            with torch.autocast("cuda", dtype=torch.bfloat16):
                _, l = model(ex, ey)
            ev.append(float(l.item()))
    model.train()
    return sum(ev) / len(ev)


def eval_only(a, device):
    """Score one checkpoint on the held-out instruction shard."""
    path = a.eval_ckpt or find_latest_ckpt(a.ckpt_dir)
    if not path:
        raise SystemExit("--eval-only: no checkpoint given and none in %s" % a.ckpt_dir)
    blob = torch.load(path, map_location=device, weights_only=False)
    cfg = ModelConfig(**blob["model_config"])
    model = TransformerLM(cfg).to(device)
    model.load_state_dict(blob["model"])
    _, val_shards = load_shards(a.val_shards)
    vrng = random.Random(a.seed + 991)
    eloss = val_loss(model, val_shards, a.batch_size, device, vrng, rounds=16)
    print("EVAL_ONLY ckpt=%s step=%s" % (path, blob.get("step")))
    print("EVAL_ONLY held_out_val_loss=%.4f  held_out_val_ppl=%.2f"
          % (eloss, math.exp(min(eloss, 20.0))))
    return eloss


def main():
    global _stop_requested
    a = parse_args()

    if os.path.abspath(a.ckpt_dir) == os.path.abspath(os.path.dirname(a.base_ckpt)):
        raise SystemExit("--ckpt-dir must not be the pre-training checkpoint dir")

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGUSR1, handle_signal)

    os.makedirs(a.ckpt_dir, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    metrics_path = os.path.join(LOG_DIR, "finetune_metrics.jsonl")

    if not torch.cuda.is_available():
        raise SystemExit("CUDA is not available")
    device = "cuda"
    torch.manual_seed(a.seed)
    np.random.seed(a.seed)
    random.seed(a.seed)
    rng = random.Random(a.seed)

    if a.eval_only:
        eval_only(a, device)
        return

    if not os.path.exists(a.base_ckpt):
        raise SystemExit("base checkpoint missing: %s" % a.base_ckpt)

    print("=" * 70, flush=True)
    print("BDW Stage L: instruction fine-tuning", flush=True)
    print("=" * 70, flush=True)
    print("device        :", torch.cuda.get_device_name(0), flush=True)
    print("torch         :", torch.__version__, flush=True)
    print("args          :", json.dumps(vars(a), indent=2), flush=True)

    train_shards, val_shards = load_shards(a.val_shards)
    train_rows, train_tokens = shard_stats(train_shards)
    val_rows, val_tokens = shard_stats(val_shards)
    total_tokens = train_tokens
    print("train shards   : %d  rows=%d  tokens=%d"
          % (len(train_shards), train_rows, train_tokens), flush=True)
    print("val shards     : %d  rows=%d  tokens=%d  (held out)"
          % (len(val_shards), val_rows, val_tokens), flush=True)

    opt = None
    step = 0
    tokens_seen = 0
    losses: list[float] = []
    last_saved_step = -1
    val_rng = random.Random(a.seed + 991)

    latest = None if a.no_resume else find_latest_ckpt(a.ckpt_dir)
    if latest:
        print("\n[resume] loading fine-tune checkpoint %s" % latest, flush=True)
        blob = torch.load(latest, map_location=device, weights_only=False)
        model = TransformerLM(ModelConfig(**blob["model_config"])).to(device)
        model.load_state_dict(blob["model"])
        opt = torch.optim.AdamW(model.parameters(), lr=a.lr,
                                betas=(a.beta1, a.beta2),
                                weight_decay=a.weight_decay)
        opt.load_state_dict(blob["optimizer"])
        step = int(blob["step"])
        tokens_seen = int(blob["tokens_seen"])
        losses = list(blob.get("losses", []))
        print("[resume] step=%d tokens_seen=%d last_loss=%s"
              % (step, tokens_seen,
                 ("%.4f" % losses[-1]) if losses else "n/a"), flush=True)
    else:
        print("\n[base] loading pre-training weights from %s" % a.base_ckpt, flush=True)
        blob = torch.load(a.base_ckpt, map_location=device, weights_only=False)
        base_cfg = ModelConfig(**blob["model_config"])
        model = TransformerLM(base_cfg).to(device)
        model.load_state_dict(blob["model"])
        print("[base] architecture: vocab=%d seq_len=%d d_model=%d layers=%d "
              "heads=%d d_ff=%d" % (base_cfg.vocab_size, base_cfg.seq_len,
                                    base_cfg.d_model, base_cfg.n_layers,
                                    base_cfg.n_heads, base_cfg.d_ff), flush=True)
        print("[base] pre-training provenance: step=%s tokens_seen=%s "
              "saved_at=%s" % (blob.get("step"), blob.get("tokens_seen"),
                               blob.get("saved_at")), flush=True)
        print("[base] fresh optimizer + step 0 (not inheriting pre-training "
              "optimizer state or its 200k-step schedule)", flush=True)
        losses = []
        step = 0
        tokens_seen = 0

    if opt is None:
        opt = torch.optim.AdamW(model.parameters(), lr=a.lr,
                                betas=(a.beta1, a.beta2),
                                weight_decay=a.weight_decay)

    if int(getattr(model.cfg, "seq_len", a.seq_len)) != a.seq_len:
        print("[warn] --seq-len=%d differs from model seq_len=%d; using model value"
              % (a.seq_len, model.cfg.seq_len), flush=True)
        a.seq_len = model.cfg.seq_len

    print("\nparams        : %d (%.2f M)" % (model.num_params(),
                                             model.num_params() / 1e6), flush=True)

    tok_per_step = a.batch_size * a.seq_len
    start_wall = time.time()
    last_ckpt = time.time()
    last_log_t = time.time()
    steps_this_run = 0
    lr = lr_at(step, a)

    print("\n--- fine-tuning ---", flush=True)
    print("%-8s %-12s %-10s %-10s %-9s %-8s" %
          ("step", "loss", "lr", "tok/s", "elapsed", "epoch%"), flush=True)

    model.train()
    while step < a.total_steps and not _stop_requested:
        if a.max_steps and steps_this_run >= a.max_steps:
            print("[max-steps] reached %d this run" % a.max_steps, flush=True)
            break

        lr = lr_at(step, a)
        set_lr(opt, lr)
        x, y = get_batch(train_shards, a.batch_size, device, rng)

        t0 = time.time()
        with torch.autocast("cuda", dtype=torch.bfloat16):
            _, loss = model(x, y)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), a.grad_clip)
        opt.step()
        torch.cuda.synchronize()
        dt = time.time() - t0

        loss_val = float(loss.item())
        step += 1
        steps_this_run += 1
        tokens_seen += tok_per_step
        losses.append(loss_val)

        if step % a.log_interval == 0:
            now_log = time.time()
            el = now_log - start_wall
            eps = a.log_interval * tok_per_step / max(now_log - last_log_t, 1e-9)
            print("%-8d %-12.4f %-10.2e %-10.0f %-9s %.1f"
                  % (step, loss_val, lr, eps, "%dm%02ds" % (el // 60, el % 60),
                     100.0 * tokens_seen / total_tokens), flush=True)
            last_log_t = now_log

        now = time.time()
        if now - last_ckpt >= a.ckpt_interval_s or _stop_requested:
            path = os.path.join(a.ckpt_dir, "%s%07d.pt" % (CKPT_PREFIX, step))
            save_ckpt(path, model, opt, step, tokens_seen, a, losses,
                      meta={"loss": loss_val, "lr": lr,
                            "wall_s": now - start_wall,
                            "base_ckpt": os.path.basename(a.base_ckpt)})
            rotate_ckpts(a.ckpt_dir, a.keep_ckpt)
            print("[ckpt] saved %s  (wall %.0fs, step %d, lr %.2e)"
                  % (os.path.basename(path), now - last_ckpt, step, lr), flush=True)
            last_ckpt = now
            last_saved_step = step
            model.train()

        if step % a.eval_interval == 0 and not _stop_requested:
            eloss = val_loss(model, val_shards, a.batch_size, device, val_rng)
            tail = losses[-min(200, len(losses)):]
            print("[eval] step %d  val_loss=%.4f  val_ppl=%.2f  (train-window %.4f)"
                  % (step, eloss, math.exp(min(eloss, 20.0)),
                     sum(tail) / len(tail)), flush=True)
            with open(metrics_path, "a") as fh:
                fh.write(json.dumps({"stage": "L", "step": step,
                                     "train_loss": loss_val, "eval_loss": eloss,
                                     "lr": lr, "tokens_seen": tokens_seen,
                                     "wall_s": time.time() - start_wall}) + "\n")

    if step != last_saved_step:
        path = os.path.join(a.ckpt_dir, "%s%07d.pt" % (CKPT_PREFIX, step))
        save_ckpt(path, model, opt, step, tokens_seen, a, losses,
                  meta={"loss": losses[-1] if losses else None, "lr": lr,
                        "wall_s": time.time() - start_wall,
                        "base_ckpt": os.path.basename(a.base_ckpt)})
        rotate_ckpts(a.ckpt_dir, a.keep_ckpt)
        print("\n[final] saved %s" % os.path.basename(path), flush=True)
    else:
        print("\n[final] step %d already saved during this run" % step, flush=True)

    if _stop_requested:
        stop_reason = "signal"
    elif step >= a.total_steps:
        stop_reason = "total-steps"
    elif a.max_steps and steps_this_run >= a.max_steps:
        stop_reason = "max-steps"
    else:
        stop_reason = "loop-exit"

    final_val = val_loss(model, val_shards, a.batch_size, device, val_rng, rounds=16)
    print("\n=== summary ===", flush=True)
    print("steps total     :", step, flush=True)
    print("tokens seen     : %d (%.2f epochs)" % (tokens_seen,
                                                  tokens_seen / max(total_tokens, 1)), flush=True)
    print("steps this run  :", steps_this_run, flush=True)
    print("wall this run   : %.1fs" % (time.time() - start_wall), flush=True)
    if losses:
        first = losses[0]
        last = losses[-1]
        tail = losses[-min(200, len(losses)):]
        print("loss first      : %.4f" % first, flush=True)
        print("loss last       : %.4f" % last, flush=True)
        print("loss tail mean  : %.4f" % (sum(tail) / len(tail)), flush=True)
        print("loss decreased  : %s" % (last < first), flush=True)
    print("final held-out  : val_loss=%.4f val_ppl=%.2f" % (final_val,
                                                            math.exp(min(final_val, 20.0))), flush=True)
    print("stop reason     : %s" % stop_reason, flush=True)
    print("FINETUNE_DONE", flush=True)


if __name__ == "__main__":
    main()
