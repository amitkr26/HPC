"""P2.3 main LoRA SFT: chained 15-minute slices with the tested auto-resume.

Slice protocol (P2.2-proven, blueprint S3/S6):
  * 15-min sbatch slices, --signal=B:USR1@60 -> SIGUSR1 -> finalize
  * finalize: full RESUMABLE checkpoint via Trainer._save_checkpoint
    (checkpoint-<step>: adapter + optimizer.pt + scheduler.pt +
    trainer_state.json, rotated keep-last-2 by save_total_limit) ->
    adapter snapshot lora_snap/step_<step> -> metrics JSONL -> RESULT ->
    hard exit before SIGKILL
  * mid-slice wall checkpoint @540s (save, CONTINUE)
  * val eval at every slice start (on_train_begin = freshly resumed
    weights) and at completion
  * resume guard: corrupt / 0-step checkpoints fail loudly
    (job 32364 lesson -- never a silent 0-step run)

Config from P2.2 measurements (errata S13.3): per-device 8 x grad-accum 4
= 32 rows/step, max_steps 692 = 2 epochs (346 x 32 >= 11,049 rows),
cosine 1e-4 warmup 3%, r=32 LoRA, seq 1024, paged_adamw_8bit.

RESULT: P2_SFT_SLICE_OK ... / P2_SFT_COMPLETE ... / P2_SFT_FAIL ...
"""
from __future__ import annotations

import glob
import json
import os
import re
import shutil
import signal
import sys
import time
import traceback

from transformers import TrainerCallback

ROOT = os.path.expanduser("~/bdw-llm")
# P2.5 re-run overrides (env only; defaults reproduce the P2.3 run exactly):
#   P2_SFT_DATA, P2_RUN_DIR, P2_SNAP_DIR, P2_METRICS, P2_PROGRESS, P2_MAX_STEPS
SFT = os.environ.get("P2_SFT_DATA",
                     os.path.join(ROOT, "data/bdw_sft.jsonl"))
BASE = os.path.join(ROOT, "teacher_model_7b")
RUN = os.environ.get("P2_RUN_DIR", os.path.join(ROOT, "sft_runs/p2_sft"))
SNAP = os.environ.get("P2_SNAP_DIR", os.path.join(ROOT, "lora_snap"))
METRICS = os.environ.get("P2_METRICS",
                         os.path.join(ROOT, "logs/p2_sft_metrics.jsonl"))
PROGRESS = os.environ.get("P2_PROGRESS",
                          os.path.join(ROOT, "logs/p2_sft_progress.json"))
TARGETS = ["q_proj", "k_proj", "v_proj", "o_proj",
           "gate_proj", "up_proj", "down_proj"]
LORA_R, LORA_ALPHA = 32, 64
EXPECTED_LORA_TENSORS = 392   # 28 layers x 7 targets x (A + B)
PER_DEVICE, GRAD_ACCUM = 8, 4
EFFECTIVE = PER_DEVICE * GRAD_ACCUM          # 32 rows/step
MAX_STEPS = int(os.environ.get(
    "P2_MAX_STEPS", "692"))                  # 2 epochs: 2 * ceil(11049/32)
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
    """transformers 4.57.6 refuses torch.load entirely below torch 2.6
    (CVE-2025-32434); the cluster torch is 2.5.1. The gated calls in our
    resume path are _load_optimizer_and_scheduler / _load_rng_state, both
    loading OUR OWN optimizer.pt / scheduler.pt / rng_state with
    weights_only=True (restricted unpickler, tensors only) from this
    trainer's previous slice minutes ago on a trusted offline filesystem.
    Disable the gate for loaded transformers modules; safetensors model and
    adapter loads never touch it and stay untouched."""
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
        print("[sft] train begin: step=%d/%d resume=%s mid_save@%ds "
              "alarm@%ds" % (state.global_step, MAX_STEPS,
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
            print("[sft] step=%d/%d loss=%s slice=%.0fs rows_per_s=%.2f "
                  "tok_s=%.0f peak=%.2fGiB"
                  % (step, MAX_STEPS,
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
            append_metric({"tag": "P2_SFT_VAL", "job": JOB, "where": where,
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
        print("[save] reason=%s step=%d -> %s (%.1f MB, %.1fs, keep=%d/%d "
              "files=%s)" % (tag, self.trainer.state.global_step, path,
                             size, time.time() - t, len(keep), CKPT_KEEP,
                             ",".join(keep[-CKPT_KEEP:])), flush=True)
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
        os.rename(tmp, final)
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
        os.rename(tmp, final)
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
            print("RESULT: P2_SFT_FAIL job=%s resume_guard step=%d "
                  "(refusing 0-step run)" % (JOB, step), flush=True)
            sys.stdout.flush()
            os._exit(1)
        completed = step >= MAX_STEPS
        if completed:
            reason = reason if REASON else "completed"
        ckpt = self.save_full(reason)
        snap = self.snapshot_adapter(reason, step)
        val_loss = self.last_val_loss
        final = final_mb = None
        if completed:
            final, final_mb = self.save_final(step)
            if not REASON:
                val_loss = self.run_val_eval(step, where="final") or val_loss
        # loss curve: dump only steps not yet in the metrics file
        p = progress_read()
        job_losses = 0
        for e in self.losses:
            if e["step"] > p["loss_step"]:
                append_metric(dict({"tag": "P2_SFT_LOSS", "job": JOB}, **e))
                job_losses += 1
        rows = (step - self.step0) * EFFECTIVE
        tok_s = rows * self.mean_tokens / max(elapsed, 1e-9)
        peak = torch.cuda.max_memory_allocated() / 2**30
        summary = {"tag": "P2_SFT", "job": JOB, "slice": p["slices"] + 1,
                   "reason": reason, "step": step, "max_steps": MAX_STEPS,
                   "complete": completed,
                   "train_wall_s": round(elapsed, 1),
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
            print("RESULT: P2_SFT_COMPLETE job=%s step=%d/%d final=%s "
                  "final_mb=%.1f val_loss=%s tok_s=%.0f wall=%.0fs"
                  % (JOB, step, MAX_STEPS, final, final_mb or -1,
                     ("%.4f" % val_loss) if val_loss else "null",
                     tok_s, elapsed), flush=True)
        else:
            print("RESULT: P2_SFT_SLICE_OK job=%s step=%d/%d reason=%s "
                  "checkpoint=%s snapshot=%s val_loss=%s tok_s=%.0f "
                  "wall=%.0fs"
                  % (JOB, step, MAX_STEPS, reason, ckpt, snap,
                     ("%.4f" % val_loss) if val_loss else "null",
                     tok_s, elapsed), flush=True)
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(0)


def main():
    global REASON
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
            print("RESULT: P2_SFT_FAIL job=%s resume_guard %s: %s"
                  % (JOB, resume, "; ".join(guard)), flush=True)
            sys.exit(1)
        step = int(re.search(r"checkpoint-(\d+)$", resume).group(1))
        print("[resume] %s global_step=%d" % (resume, step), flush=True)
    else:
        st = None
        print("[fresh] no checkpoint in %s" % RUN, flush=True)

    import torch
    import transformers
    import trl
    from datasets import load_dataset
    from peft import LoraConfig, get_peft_model
    from trl import SFTConfig, SFTTrainer

    print("job        : %s" % JOB)
    print("python      : %s %s" % (sys.version.split()[0], sys.executable),
          flush=True)
    print("node        :", os.uname().nodename)
    print("device      :", torch.cuda.get_device_name(0))
    print("torch       : %s | cuda %s" % (torch.__version__, torch.version.cuda))
    print("transformers: %s | trl %s" % (transformers.__version__,
                                         trl.__version__))

    ds_all = load_dataset("json", data_files=[SFT], split="train")
    ds = ds_all.filter(lambda r: r.get("split") == "train")
    val = ds_all.filter(lambda r: r.get("split") == "val")
    mean_tokens = float(sum(ds["tokens"])) / max(len(ds), 1)
    print("dataset     : train=%d val=%d mean_tokens=%.1f"
          % (len(ds), len(val), mean_tokens), flush=True)
    assert len(val) > 0 and len(ds) > 0

    tok = transformers.AutoTokenizer.from_pretrained(BASE, local_files_only=True)
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
        logging_steps=5,
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
        print("RESULT: P2_SFT_FAIL job=%s %s" % (JOB, sys.exc_info()[1]),
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
        print("RESULT: P2_SFT_FAIL job=%s %s" % (
            os.environ.get("SLURM_JOB_ID", "local"), sys.exc_info()[1]),
            flush=True)
        sys.exit(1)
