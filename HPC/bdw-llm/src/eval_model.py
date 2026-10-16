"""Stage I: evaluate the trained model on genuinely unseen text.

Three measurements, all on the SAME held-out token stream
(data/eval/eval_tokens.npy, URL-disjoint from training):

  1. random-init baseline  - what an untrained net scores
  2. trained checkpoint     - the actual model
  3. training rows (seen)   - what the model scores on data it memorised

(2) - (1) shows training did work; (3) - (2) shows how much was memorised.
"""
import argparse
import glob
import json
import math
import os
import random
import sys
import time

import numpy as np
import torch
import torch.nn.functional as F
from tokenizers import Tokenizer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import ModelConfig, TransformerLM

ROOT = os.path.expanduser("~/bdw-llm")
CKPT_DIR = os.path.join(ROOT, "checkpoints")
EVAL_NPY = os.path.join(ROOT, "data/eval/eval_tokens.npy")
EVAL_META = os.path.join(ROOT, "data/eval/eval_meta.json")
TRAIN_SHARDS = os.path.join(ROOT, "tokens/shards/shard_0000.npy")
TOK_PATH = os.path.join(ROOT, "tokenizer/tokenizer.json")
OUT_JSON = os.path.join(ROOT, "logs/eval_results.json")

PROMPTS = [
    "The history of",
    "In recent years,",
    "Scientists have",
]


def parse_args():
    p = argparse.ArgumentParser(description="BDW held-out evaluation")
    p.add_argument("--ckpt", default="", help="checkpoint path (default: newest)")
    p.add_argument("--fresh", action="store_true",
                   help="evaluate random init only (no checkpoint load)")
    p.add_argument("--with-baseline", action="store_true",
                   help="also score a random-init copy before loading the checkpoint")
    p.add_argument("--train-rows", type=int, default=500,
                   help="rows of TRAINING data to score for the seen/unseen gap (0=skip)")
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--gen-tokens", type=int, default=80)
    p.add_argument("--seed", type=int, default=1337)
    return p.parse_args()


def newest_ckpt():
    files = sorted(glob.glob(os.path.join(CKPT_DIR, "step_*.pt")))
    return files[-1] if files else None


def rows_of(arr, seq_len):
    flat = np.asarray(arr, dtype=np.int32).reshape(-1)
    n = (flat.size // seq_len) * seq_len
    return flat[:n].reshape(-1, seq_len)


@torch.no_grad()
def evaluate(model, rows, device, batch_size):
    model.eval()
    nll_sum, tok_count, correct = 0.0, 0, 0
    per_row = []
    for i in range(0, rows.shape[0], batch_size):
        x = torch.from_numpy(rows[i:i + batch_size]).long().to(device)
        y = torch.roll(x, shifts=-1, dims=1)
        y[:, -1] = 0
        with torch.autocast("cuda", dtype=torch.bfloat16):
            logits, _ = model(x, y)
        logits = logits.float()
        row_nll = F.cross_entropy(
            logits.reshape(-1, logits.size(-1)), y.reshape(-1),
            reduction="none").reshape(y.shape)
        per_row.append(row_nll.mean(dim=1).cpu().numpy())
        nll_sum += float(row_nll.sum())
        tok_count += int(y.numel())
        correct += int((logits.argmax(dim=-1) == y).sum())

    pr = np.concatenate(per_row)
    mean = float(pr.mean())
    se = float(pr.std(ddof=1) / math.sqrt(pr.size)) if pr.size > 1 else 0.0
    return {
        "rows": int(pr.size),
        "tokens": tok_count,
        "mean_nll": mean,
        "perplexity": math.exp(mean),
        "ci95_low": math.exp(mean - 1.96 * se),
        "ci95_high": math.exp(mean + 1.96 * se),
        "token_accuracy": correct / max(tok_count, 1),
        "row_nll_min": float(pr.min()),
        "row_nll_max": float(pr.max()),
    }


@torch.no_grad()
def generate_samples(model, tokenizer, device, seq_len, max_new, seed):
    model.eval()
    out = []
    torch.manual_seed(seed)
    for prompt in PROMPTS:
        ids = tokenizer.encode(prompt).ids or [1]
        idx = torch.tensor([ids], dtype=torch.long, device=device)
        greedy = model.generate(idx, max_new, temperature=1.0, top_k=1)
        sampled = model.generate(idx, max_new, temperature=0.8, top_k=50)
        out.append({
            "prompt": prompt,
            "greedy": tokenizer.decode(greedy[0].tolist()),
            "sample_t0.8_k50": tokenizer.decode(sampled[0].tolist()),
        })
    return out


def main():
    a = parse_args()
    device = "cuda"
    if not torch.cuda.is_available():
        raise SystemExit("CUDA is not available")
    torch.manual_seed(a.seed)
    random.seed(a.seed)
    np.random.seed(a.seed)

    ckpt_path = a.ckpt or (None if a.fresh else newest_ckpt())
    if not a.fresh and not ckpt_path:
        raise SystemExit("no checkpoint in %s" % CKPT_DIR)

    print("=" * 70)
    print("BDW evaluation")
    print("=" * 70)
    print("device        :", torch.cuda.get_device_name(0))
    print("torch         :", torch.__version__)
    print("checkpoint    :", ckpt_path or "(fresh random init)")

    eval_meta = json.load(open(EVAL_META))
    print("eval tokens   : %d from %s (%d docs, source md5 %s)"
          % (eval_meta["tokens"], eval_meta["source_jsonl"],
             eval_meta["documents"], eval_meta["source_md5"]))
    print("train urls / eval urls are disjoint (verified at fetch time)")

    blob = None
    cfg = ModelConfig()
    if ckpt_path:
        blob = torch.load(ckpt_path, map_location="cpu", weights_only=False)
        cfg = ModelConfig(**blob["model_config"])
        step = int(blob["step"])
        tokens_seen = int(blob["tokens_seen"])
        print("ckpt step     : %d  tokens_seen=%d  (%.2f epochs)"
              % (step, tokens_seen, tokens_seen / 37978112))
    else:
        step, tokens_seen = 0, 0

    eval_rows = rows_of(np.load(EVAL_NPY, mmap_mode="r"), cfg.seq_len)
    print("eval rows     : %d x %d" % (eval_rows.shape[0], eval_rows.shape[1]))

    results = {"checkpoint": ckpt_path, "ckpt_step": step,
               "ckpt_tokens_seen": tokens_seen,
               "eval_source_md5": eval_meta["source_md5"]}

    def build():
        torch.manual_seed(a.seed)
        return TransformerLM(cfg).to(device)

    if a.with_baseline and not a.fresh:
        print("\n[baseline] scoring random-init model on unseen eval set ...")
        t0 = time.time()
        results["baseline_unseen"] = evaluate(build(), eval_rows, device, a.batch_size)
        print("[baseline] perplexity=%.2f  nll=%.4f  acc=%.4f  (%.1fs)"
              % (results["baseline_unseen"]["perplexity"],
                 results["baseline_unseen"]["mean_nll"],
                 results["baseline_unseen"]["token_accuracy"],
                 time.time() - t0))

    model = build()
    if blob is not None:
        model.load_state_dict(blob["model"])
        del blob
    print("\nparams        :", sum(p.numel() for p in model.parameters()))

    print("\n[unseen] scoring %d held-out rows ..." % eval_rows.shape[0])
    t0 = time.time()
    results["trained_unseen"] = evaluate(model, eval_rows, device, a.batch_size)
    u = results["trained_unseen"]
    print("[unseen] perplexity=%.2f  nll=%.4f  95%% CI=[%.2f, %.2f]  acc=%.4f  (%.1fs)"
          % (u["perplexity"], u["mean_nll"], u["ci95_low"], u["ci95_high"],
             u["token_accuracy"], time.time() - t0))

    if a.train_rows > 0:
        seen = rows_of(np.load(TRAIN_SHARDS, mmap_mode="r"), cfg.seq_len)[:a.train_rows]
        print("\n[seen] scoring %d training rows (data the model WAS trained on) ..."
              % seen.shape[0])
        t0 = time.time()
        results["trained_seen"] = evaluate(model, seen, device, a.batch_size)
        s = results["trained_seen"]
        print("[seen] perplexity=%.2f  nll=%.4f  acc=%.4f  (%.1fs)"
              % (s["perplexity"], s["mean_nll"], s["token_accuracy"], time.time() - t0))
        results["generalisation_gap_nll"] = u["mean_nll"] - s["mean_nll"]

    tok = Tokenizer.from_file(TOK_PATH)
    print("\n--- generation ---")
    samples = generate_samples(model, tok, device, cfg.seq_len, a.gen_tokens, a.seed)
    results["samples"] = samples
    for s in samples:
        print("\nPROMPT : %r" % s["prompt"])
        print("GREEDY : %s" % s["greedy"])
        print("SAMPLE : %s" % s["sample_t0.8_k50"])

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w") as fh:
        json.dump(results, fh, indent=2)
    print("\nsaved ->", OUT_JSON)
    print("EVAL_OK")


if __name__ == "__main__":
    main()
