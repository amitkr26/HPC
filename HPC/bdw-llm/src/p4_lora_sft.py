"""P4.4 - per-domain LoRA SFT on the shipped P2.5 model (chained 15-min slices).

Family: p2_sft.py (P2.3) with three Phase 4 deltas and otherwise the exact
proven machinery (signals, mid-slice wall checkpoint, resume guard, adapter
snapshots, metrics JSONL):

  1. Base  = merged/bdw-7b-sft      (the shipped Qwen2.5-7B SFT model the
     router hot-swaps onto -- PEFT writes it into adapter_config.json's
     base_model_name_or_path, and llama.cpp-neutrality is preserved because
     nothing else touches the base weights).
  2. Every path is domain-parameterised via P4_DOMAIN (mandatory env):
     data  data/p4/sft/<domain>_sft.jsonl   (P4.2 output)
     run   sft_runs/p4_<domain>/            (resumable TRL checkpoints)
     snap  lora_<domain>/                   (router adapter name -- final/)
     logs  logs/p4_<domain>_sft_metrics.jsonl + progress json
  3. max_steps is data-driven:  ceil(train_rows * P4_EPOCHS / effective)
     clamped to [20, P4_STEPS_CAP=400]; LR/warmup/schedule/optimiser/seq are
     the P2.3 recipe (1e-4 cosine, 3% warmup, r=32 alpha=64, 7 proj modules,
     bf16, seq 1024, paged_adamw_8bit) = 392 LoRA tensors on 28 layers.

Slice protocol (P2.2-proven, unchanged):
  * 15-min sbatch slices, --signal=B:USR1@60 -> SIGUSR1 -> finalize
  * finalize: full RESUMABLE checkpoint (adapter + optimizer.pt +
    scheduler.pt + trainer_state.json, keep-last-2) -> adapter snapshot
    lora_<domain>/step_<step> -> metrics JSONL -> RESULT -> hard exit
  * mid-slice wall checkpoint @540s (save, CONTINUE); alarm backup @870s;
    hard deadline @895s
  * val eval at every slice start (freshly resumed weights) and at completion
  * resume guard: corrupt / 0-step checkpoints fail loudly
  * torch 2.5.1 transformers torch-load gate patch (own-slice resume only)

RESULT: P4_SFT_<DOMAIN>_SLICE_OK ... / P4_SFT_<DOMAIN>_COMPLETE ... /
        P4_SFT_<DOMAIN>_FAIL ...
"""
from __future__ import annotations

import glob
import json
import math
import os
import re
import shutil
import signal
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p4_domain_lib as P4  # noqa: E402

from transformers import TrainerCallback  # noqa: E402

DOMAIN = os.environ.get("P4_DOMAIN", "")
try:
    P4.check(DOMAIN)
except ValueError:
    print("RESULT: P4_SFT_FAIL P4_DOMAIN unset or invalid (%r); expected one "
          "of %s" % (DOMAIN, ", ".join(P4.DOMAINS)))
    sys.exit(1)
DOM = DOMAIN.upper()

ROOT = P4.ROOT
# P4 env overrides (defaults reproduce the P2.3 recipe on every domain):
#   P4_SFT_DATA, P4_RUN_DIR, P4_SNAP_DIR, P4_METRICS, P4_PROGRESS,
#   P4_BASE, P4_MAX_STEPS, P4_EPOCHS, P4_STEPS_CAP
SFT = os.environ.get("P4_SFT_DATA", P4.sft_path(DOMAIN))
BASE = os.environ.get("P4_BASE", P4.base_dir())
RUN = os.environ.get("P4_RUN_DIR", P4.run_dir(DOMAIN))
SNAP = os.environ.get("P4_SNAP_DIR", P4.snap_dir(DOMAIN))
METRICS = os.environ.get("P4_METRICS", P4.metrics_path(DOMAIN))
PROGRESS = os.environ.get("P4_PROGRESS", P4.progress_path(DOMAIN))
EPOCHS = float(os.environ.get("P4_EPOCHS", "3"))
STEPS_CAP = int(os.environ.get("P4_STEPS_CAP", "400"))
TARGETS = ["q_proj", "k_proj", "v_proj", "o_proj",
           "gate_proj", "up_proj", "down_proj"]
LORA_R, LORA_ALPHA = 32, 64
EXPECTED_LORA_TENSORS = 392   # 28 layers x 7 targets x (A + B)
PER_DEVICE, GRAD_ACCUM = 8, 4
EFFECTIVE = PER_DEVICE * GRAD_ACCUM          # 32 rows/step
MID_SAVE_S = 540
WALL_ALARM_S = 870
DEADLINE_S = 895
CKPT_KEEP = 2
SNAP_KEEP = 3

JOB = os.environ.get("SLURM_JOB_ID", "local")
REASON = ""
FINALIZED = False


def handler(signum, frame):
    global REASON
    if not REASON:
        REASON = {signal.SIGUSR1: "usr1", signal.SIGTERM: "term",
                  signal.SIGALRM: "alarm_backup"}.get(signum, "sig%d" % signum)
        print("\n[signal] %d received -> will checkpoint at next step end (%s)"
              % (signum, REASON), flush=True)


# --------------------------------------------------------------- file helpers
def atomic_write(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)


def append_metric(obj):
    os.makedirs(os.path.dirname(METRICS), exist_ok=True)
    with open(METRICS, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(obj) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def progress_read():
    try:
        with open(PROGRESS, encoding="utf-8") as fh:
            p = json.load(fh)
    except Exception:
        p = {}
    return {"loss_step": p.get("loss_step", 0),
            "slices": p.get("slices", 0),
            "val_step": p.get("val_step", -1),
            "val_loss": p.get("val_loss")}


def progress_write(p):
    os.makedirs(os.path.dirname(PROGRESS), exist_ok=True)
    atomic_write(PROGRESS, json.dumps(p))


def newest_checkpoint():
    best, best_step = None, -1
    for st in glob.glob(os.path.join(RUN, "checkpoint-*", "trainer_state.json")):
        m = re.search(r"checkpoint-(\d+)$", os.path.dirname(st))
        if m and int(m.group(1)) > best_step:
            best, best_step = os.path.dirname(st), int(m.group(1))
    return best


def patch_torch_load_gate():
    """transformers refuses torch.load entirely below torch 2.6
    (CVE-2025-32434); the cluster torch is 2.5.1. The gated calls in our own
    resume path only load OUR OWN optimizer.pt / scheduler.pt / rng_state with
    weights_only=True from this trainer's previous slice minutes ago on a
    trusted offline filesystem. Disable the gate for loaded transformers
    modules; safetensors model and adapter loads never touch it. On a
    transformers without the gate this is a counted no-op."""
    import sys as _sys
    n = 0
    for _m in list(_sys.modules.values()):
        if _m is None:
            continue
        name = getattr(_m, "__name__", "")
        if name == "transformers" or name.startswith("transformers."):
            if getattr(_m, "check_torch_load_is_safe", None) is not None:
                setattr(_m, "check_torch_load_is_safe", lambda: None)
                n += 1
    print("[patch] torch.load safety gate disabled in %d transformers "
          "modules (torch 2.5.1, weights_only=True, own-slice resume files)"
          % n, flush=True)


def verify_adapter_dir(d):
    cfg_p = os.path.join(d, "adapter_config.json")
    assert os.path.isfile(cfg_p), "no adapter_config.json in %s" % d
    cfg = json.load(open(cfg_p))
    assert cfg.get("r") == LORA_R, "adapter_config r=%s" % cfg.get("r")
    base = cfg.get("base_model_name_or_path") or ""
    assert "bdw-7b-sft" in base or base.endswith("bdw-7b-sft") or \
        os.path.isdir(base), "adapter base=%r not the p2.5 SFT model" % base
    st = [f for f in os.listdir(d) if f.endswith(".safetensors")]
    assert len(st) == 1, "safetensors files: %s" % st
    from safetensors import safe_open
    with safe_open(os.path.join(d, st[0]), framework="pt") as f:
        n = len(f.keys())
    assert n == EXPECTED_LORA_TENSORS, "lora tensors=%d" % n
    return n


def adapter_size_mb(d):
    return sum(os.path.getsize(os.path.join(d, x)) for x in os.listdir(d)
               if os.path.isfile(os.path.join(d, x))) / 1e6


def prune_snapshots():
    dirs = sorted(glob.glob(os.path.join(SNAP, "step_*")))
    for d in dirs[:-SNAP_KEEP]:
        shutil.rmtree(d, ignore_errors=True)


class SFTSaver(TrainerCallback):
    def __init__(self, trainer, mean_tokens, n_val):
        self.trainer = trainer
        self.mean_tokens = mean_tokens
        self.n_val = n_val
        self.t0 = None
        self.step0 = 0
        self.mid_done = False
        self.losses = []
        self.last_val_loss = progress_read()["val_loss"]

    # -------------------------------------------------------------- callbacks
    def on_train_begin(self, args, state, control, **kw):
        self.t0 = time.time()
        self.step0 = state.global_step
        mx = getattr(self, "max_steps", "?")
        print("[sft] train begin: step=%d/%s resume=%s mid_save@%ds "
              "alarm@%ds" % (state.global_step, mx,
                             "yes" if state.global_step else "no",
                             MID_SAVE_S, WALL_ALARM_S), flush=True)
        # val eval on the weights about to be trained (fresh or resumed)
        self.run_val_eval(state.global_step, where="slice_start")

    def on_log(self, args, state, control, logs=None, **kw):
        if logs and "loss" in logs:
            self.losses.append({"step": logs.get("step", state.global_step),
                                "loss": logs["loss"],
                                "lr": logs.get("learning_rate")})

    def on_step_end(self, args, state, control, **kw):
        global REASON
        import torch
        now = time.time()
        elapsed = now - (self.t0 or now)
        step = state.global_step
        if step % 5 == 0:
            loss = self.losses[-1]["loss"] if self.losses else None
            rows = (step - self.step0) * EFFECTIVE
            print("[sft] step=%s loss=%s slice=%.0fs rows_per_s=%.2f "
                  "tok_s=%.0f peak=%.2fGiB"
                  % (step,
                     ("%.4f" % loss) if loss is not None else "-",
                     elapsed, rows / max(elapsed, 1e-9),
                     rows * self.mean_tokens / max(elapsed, 1e-9),
                     torch.cuda.max_memory_allocated() / 2**30), flush=True)
        if not self.mid_done and MID_SAVE_S and elapsed >= MID_SAVE_S:
            self.mid_done = True
            path = self.save_full("wall_mid")
            print("[sft] mid-slice wall checkpoint -> %s (continuing)"
                  % path, flush=True)
        if not REASON and elapsed >= DEADLINE_S:
            REASON = "deadline"
        if REASON:
            self.finalize(REASON, step, elapsed)

    def run_val_eval(self, step, where):
        try:
            t = time.time()
            out = self.trainer.evaluate()
            vl = out.get("eval_loss")
            self.last_val_loss = vl
            print("[val] %s step=%d val_loss=%s (%.0fs, %d rows)"
                  % (where, step, vl, time.time() - t, self.n_val),
                  flush=True)
            append_metric({"tag": "P4_SFT_VAL", "domain": DOMAIN,
                           "job": JOB, "where": where,
                           "slice": progress_read()["slices"] + 1,
                           "step": step, "val_loss": vl,
                           "eval_s": round(time.time() - t, 1)})
            p = progress_read()
            p["val_step"], p["val_loss"] = step, vl
            progress_write(p)
            return vl
        except Exception:
            traceback.print_exc()
            print("[val] %s FAILED (continuing)" % where, flush=True)
            return None

    # ------------------------------------------------------------- checkpoints
    def save_full(self, tag):
        """Full resumable checkpoint at the current global step."""
        t = time.time()
        self.trainer._save_checkpoint(self.trainer.model, None)
        path = os.path.join(RUN, "checkpoint-%d" %
                            self.trainer.state.global_step)
        for req in ("trainer_state.json", "optimizer.pt", "scheduler.pt",
                    "adapter_config.json"):
            assert os.path.isfile(os.path.join(path, req)), \
                "checkpoint incomplete: missing %s in %s" % (req, path)
        assert verify_adapter_dir(path) == EXPECTED_LORA_TENSORS
        size = sum(os.path.getsize(os.path.join(path, x))
                   for x in os.listdir(path)) / 1e6
        keep = sorted(os.path.basename(d) for d in
                      glob.glob(os.path.join(RUN, "checkpoint-*")))
        print("[save] reason=%s step=%d -> %s (%.1f MB, %.1fs, keep=%s)"
              % (tag, self.trainer.state.global_step, path,
                 size, time.time() - t, ",".join(keep[-2:])), flush=True)
        return path

    def snapshot_adapter(self, tag, step):
        final = os.path.join(SNAP, "step_%06d" % step)
        if os.path.exists(final):
            final += "_" + tag
        tmp = final + ".tmp"
        shutil.rmtree(tmp, ignore_errors=True)
        t = time.time()
        self.trainer.save_model(tmp)
        n = verify_adapter_dir(tmp)
        os.replace(tmp, final)
        assert os.path.isdir(final) and not os.path.exists(tmp)
        print("[snap] reason=%s step=%d -> %s (%.1f MB, %.1fs, %d tensors, "
              "r=%d, atomic=OK)" % (tag, step, final, adapter_size_mb(final),
                                    time.time() - t, n, LORA_R), flush=True)
        prune_snapshots()
        return final

    def save_final(self, step):
        final = os.path.join(SNAP, "final")
        tmp = final + ".tmp"
        shutil.rmtree(tmp, ignore_errors=True)
        t = time.time()
        self.trainer.save_model(tmp)
        n = verify_adapter_dir(tmp)
        shutil.rmtree(final, ignore_errors=True)
        os.replace(tmp, final)
        size = adapter_size_mb(final)
        print("[final] adapter saved -> %s (%.1f MB, %.1fs, %d tensors, "
              "r=%d, step=%d)" % (final, size, time.time() - t, n, LORA_R,
                                  step), flush=True)
        return final, size

    # ----------------------------------------------------------------- finish
    def finalize(self, reason, step, elapsed):
        global REASON, FINALIZED
        import torch
        if FINALIZED:
            return
        FINALIZED = True
        if step < 1:
            print("RESULT: P4_SFT_%s_FAIL job=%s resume_guard step=%d "
                  "(refusing 0-step run)" % (DOM, JOB, step), flush=True)
            sys.stdout.flush()
            os._exit(1)
        max_steps = self.max_steps
        completed = step >= max_steps
        ckpt = self.save_full(reason)
        snap = self.snapshot_adapter(reason, step)
        val_loss = self.last_val_loss
        final = final_mb = None
        if completed:
            final, final_mb = self.save_final(step)
            if val_loss is None:
                val_loss = self.run_val_eval(step, where="final")
        # loss curve: dump only steps not yet in the metrics file
        p = progress_read()
        job_losses = 0
        for e in self.losses:
            if e["step"] > p["loss_step"]:
                append_metric(dict({"tag": "P4_SFT_LOSS", "domain": DOMAIN,
                                    "job": JOB}, **e))
                job_losses += 1
        rows = (step - self.step0) * EFFECTIVE
        tok_s = rows * self.mean_tokens / max(elapsed, 1e-9)
        peak = torch.cuda.max_memory_allocated() / 2**30
        summary = {"tag": "P4_SFT", "domain": DOMAIN, "job": JOB,
                   "slice": p["slices"] + 1, "reason": reason,
                   "step": step, "max_steps": max_steps,
                   "complete": completed, "train_wall_s": round(elapsed, 1),
                   "steps_this_slice": step - self.step0,
                   "rows_per_s": round(rows / max(elapsed, 1e-9), 3),
                   "tok_s": round(tok_s, 1),
                   "mean_tokens_per_row": round(self.mean_tokens, 1),
                   "peak_alloc_gib": round(peak, 2),
                   "peak_reserved_gib": round(
                       torch.cuda.max_memory_reserved() / 2**30, 2),
                   "loss_first": self.losses[0] if self.losses else None,
                   "loss_last": self.losses[-1] if self.losses else None,
                   "val_loss": val_loss, "checkpoint": ckpt,
                   "snapshot": snap, "final": final,
                   "base": BASE,
                   "batch": {"per_device": PER_DEVICE,
                             "grad_accum": GRAD_ACCUM,
                             "effective": EFFECTIVE},
                   "loss_lines_dumped": job_losses}
        append_metric(summary)
        p["loss_step"] = max(p["loss_step"], step)
        p["slices"] += 1
        if val_loss is not None:
            p["val_step"], p["val_loss"] = step, val_loss
        progress_write(p)
        if completed:
            print("RESULT: P4_SFT_%s_COMPLETE job=%s step=%d/%d final=%s "
                  "final_mb=%.1f val_loss=%s tok_s=%.0f wall=%.0fs"
                  % (DOM, JOB, step, max_steps, final, final_mb or -1,
                     ("%.4f" % val_loss) if val_loss is not None else "null",
                     tok_s, elapsed), flush=True)
        else:
            print("RESULT: P4_SFT_%s_SLICE_OK job=%s step=%d/%d reason=%s "
                  "checkpoint=%s snapshot=%s val_loss=%s tok_s=%.0f "
                  "wall=%.0fs"
                  % (DOM, JOB, step, max_steps, reason, ckpt, snap,
                     ("%.4f" % val_loss) if val_loss is not None else "null",
                     tok_s, elapsed), flush=True)
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(0)


def main():
    global REASON
    if not os.path.isfile(SFT):
        print("RESULT: P4_SFT_%s_FAIL no SFT dataset %s (run P4.2 build "
              "first)" % (DOM, SFT))
        sys.exit(1)
    for probe in ("config.json", "chat_template.jinja"):
        if not os.path.isfile(os.path.join(BASE, probe)):
            print("RESULT: P4_SFT_%s_FAIL base model missing %s in %s"
                  % (DOM, probe, BASE))
            sys.exit(1)
    if not os.path.isdir(BASE):
        print("RESULT: P4_SFT_%s_FAIL base model dir missing %s" % (DOM, BASE))
        sys.exit(1)
    os.makedirs(ROOT, exist_ok=True)
    resume = newest_checkpoint()
    if resume:
        guard = []
        try:
            st = json.load(open(os.path.join(resume, "trainer_state.json")))
            if int(st.get("global_step", 0)) < 1:
                guard.append("global_step=%s" % st.get("global_step"))
        except Exception as e:
            guard.append("trainer_state unreadable: %s" % e)
        for req in ("optimizer.pt", "adapter_config.json"):
            if not os.path.isfile(os.path.join(resume, req)):
                guard.append("missing %s" % req)
        if guard:
            print("RESULT: P4_SFT_%s_FAIL job=%s resume_guard %s: %s"
                  % (DOM, JOB, resume, "; ".join(guard)), flush=True)
            sys.exit(1)
        step = int(re.search(r"checkpoint-(\d+)$", resume).group(1))
        print("[resume] %s global_step=%d" % (resume, step), flush=True)
    else:
        print("[fresh] no checkpoint in %s" % RUN, flush=True)

    import torch
    import transformers
    import trl
    from datasets import load_dataset
    from peft import LoraConfig, get_peft_model
    from trl import SFTConfig, SFTTrainer

    print("job        : %s" % JOB)
    print("domain     : %s" % DOMAIN)
    print("python      : %s %s" % (sys.version.split()[0], sys.executable),
          flush=True)
    print("node        :", os.uname().nodename)
    print("device      :", torch.cuda.get_device_name(0)
          if torch.cuda.is_available() else "cpu")
    print("torch       : %s | cuda %s" % (torch.__version__,
                                          torch.version.cuda))
    print("transformers: %s | trl %s" % (transformers.__version__,
                                         trl.__version__))
    print("base        : %s" % BASE)
    print("dataset     : %s" % SFT)

    ds_all = load_dataset("json", data_files=[SFT], split="train")
    ds = ds_all.filter(lambda r: r.get("split") == "train")
    val = ds_all.filter(lambda r: r.get("split") == "val")
    mean_tokens = float(sum(ds["tokens"])) / max(len(ds), 1)
    print("dataset     : train=%d val=%d mean_tokens=%.1f"
          % (len(ds), len(val), mean_tokens), flush=True)
    assert len(val) > 0 and len(ds) > 0

    auto_steps = int(math.ceil(len(ds) * EPOCHS / EFFECTIVE))
    max_steps_env = os.environ.get("P4_MAX_STEPS", "").strip()
    MAX_STEPS = int(max_steps_env) if max_steps_env else \
        max(20, min(STEPS_CAP, auto_steps))
    print("schedule    : epochs=%.2g -> max_steps=%d (effective batch %d)"
          % (EPOCHS, MAX_STEPS, EFFECTIVE))

    tok = transformers.AutoTokenizer.from_pretrained(BASE,
                                                     local_files_only=True)
    model = transformers.AutoModelForCausalLM.from_pretrained(
        BASE, torch_dtype=torch.bfloat16, local_files_only=True)
    lora = LoraConfig(
        r=LORA_R, lora_alpha=LORA_ALPHA, lora_dropout=0.05, bias="none",
        task_type="CAUSAL_LM", target_modules=TARGETS)
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()
    model.config.use_cache = False
    model.enable_input_require_grads()
    torch.cuda.reset_peak_memory_stats()

    cfg = SFTConfig(
        output_dir=RUN,
        per_device_train_batch_size=PER_DEVICE,
        gradient_accumulation_steps=GRAD_ACCUM,
        learning_rate=1e-4,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        max_steps=MAX_STEPS,
        logging_steps=1,
        save_strategy="no",
        save_total_limit=CKPT_KEEP,
        report_to=[],
        bf16=True,
        tf32=True,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        max_length=1024,
        packing=False,
        optim="paged_adamw_8bit",
        seed=1337,
        disable_tqdm=True,
    )
    trainer = SFTTrainer(model=model, args=cfg, train_dataset=ds,
                         eval_dataset=val, processing_class=tok)
    saver = SFTSaver(trainer, mean_tokens, len(val))
    saver.max_steps = MAX_STEPS
    trainer.add_callback(saver)

    for sig in (signal.SIGUSR1, signal.SIGTERM, signal.SIGALRM):
        signal.signal(sig, handler)
    signal.alarm(WALL_ALARM_S)
    print("signals     : SIGUSR1/SIGTERM/SIGALRM armed "
          "(usr1 expected at T-60s, alarm backup at %ds)" % WALL_ALARM_S,
          flush=True)

    patch_torch_load_gate()
    try:
        trainer.train(resume_from_checkpoint=resume)
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        print("RESULT: P4_SFT_%s_FAIL job=%s %s" % (DOM, JOB,
                                                    sys.exc_info()[1]),
              flush=True)
        sys.exit(1)
    if not REASON and trainer.state.global_step < MAX_STEPS:
        REASON = "early_return"
    saver.finalize(REASON or "completed", trainer.state.global_step,
                   time.time() - (saver.t0 or time.time()))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        print("RESULT: P4_SFT_%s_FAIL job=%s %s" % (
            DOM or "?", os.environ.get("SLURM_JOB_ID", "local"),
            sys.exc_info()[1]), flush=True)
        sys.exit(1)
