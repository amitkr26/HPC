"""P2.2 profiling slice: real P2.3-style LoRA SFT under the 15-minute regime.

Measures, on one A100 slice, exactly what the P2.2 milestone needs:
  * throughput  -- steps/s, rows/s, useful tok/s (16 rows/step = 4 x grad-accum 4)
  * VRAM        -- torch.cuda.max_memory_allocated watermark (grad ckpt on)
  * the atomic save / signal-kill mechanism:
      - mid-slice wall-clock snapshot at --mid-save seconds (save, CONTINUE)
      - Slurm --signal=B:USR1@60 arrives as SIGUSR1 -> atomic snapshot + exit
      - SIGTERM (job time limit) and a SIGALRM backup do the same
    every snapshot: save to a .tmp dir -> verify adapter_config.json (r=32) and
    392 safetensors lora tensors -> os.rename() to step_XXXXXX (atomic) ->
    RESULT line + metrics json -> hard exit before the scheduler's SIGKILL.

Config mirrors blueprint S6: LoRA r=32 alpha=64 dropout .05 on all 7 linears,
per-device 4 x grad-accum 4, seq 1024 (packing OFF), bf16 + tf32 + grad ckpt,
1e-4 cosine warmup 3%, paged_adamw_8bit (falls back to adamw_torch).

RESULT: P2_PROFILE_OK steps=... reason=... tok_s=... peak_alloc=... save=...
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import sys
import time
import traceback

from transformers import TrainerCallback

ROOT = os.path.expanduser("~/bdw-llm")
SFT = os.path.join(ROOT, "data/bdw_sft.jsonl")
BASE = os.path.join(ROOT, "teacher_model_7b")
OUTDIR = os.path.join(ROOT, "lora_profile")
METRICS = os.path.join(ROOT, "logs/p2_profile.json")
TARGETS = ["q_proj", "k_proj", "v_proj", "o_proj",
           "gate_proj", "up_proj", "down_proj"]
LORA_R, LORA_ALPHA = 32, 64
EXPECTED_LORA_TENSORS = 392  # 28 layers x 7 targets x (A + B)
EFFECTIVE_BATCH = 4 * 4      # per-device x grad-accum

REASON = ""
WALL_ALARM_S = 870           # backup save (USR1 should land at 840 = T-60s)
DEADLINE_S = 895             # belt-and-braces in the step callback


def handler(signum, frame):
    global REASON
    if not REASON:
        REASON = {signal.SIGUSR1: "usr1", signal.SIGTERM: "term",
                  signal.SIGALRM: "alarm_backup"}.get(signum, "sig%d" % signum)
        print("\n[signal] %d received -> will snapshot at next step end (%s)"
              % (signum, REASON), flush=True)


class Profile(TrainerCallback):
    def __init__(self, trainer, mean_tokens, mid_save_s, save_root):
        self.trainer = trainer
        self.mean_tokens = mean_tokens
        self.mid_save_s = mid_save_s
        self.save_root = save_root
        self.t0 = None
        self.mid_done = False
        self.losses = []
        self.step_t = None

    def on_train_begin(self, args, state, control, **kw):
        self.t0 = time.time()
        self.step_t = self.t0
        print("[prof] train begin: max_steps=%d mean_tokens/row=%.1f "
              "mid_save@%ds alarm@%ds" % (state.max_steps, self.mean_tokens,
                                          self.mid_save_s, WALL_ALARM_S),
              flush=True)

    def on_log(self, args, state, control, logs=None, **kw):
        if logs and "loss" in logs:
            self.losses.append({"step": logs.get("step", state.global_step),
                                "loss": logs["loss"],
                                "lr": logs.get("learning_rate")})

    def on_step_end(self, args, state, control, **kw):
        import torch
        global REASON
        now = time.time()
        elapsed = now - (self.t0 or now)
        step = state.global_step
        if step % 10 == 0 or self.losses:
            loss = self.losses[-1]["loss"] if self.losses else None
            rows = step * EFFECTIVE_BATCH
            tok_s = rows * self.mean_tokens / max(elapsed, 1e-9)
            print("[prof] step=%d loss=%s elapsed=%.0fs rows=%d "
                  "rows_per_s=%.2f tok_s=%.0f peak=%.2fGiB"
                  % (step, ("%.4f" % loss) if loss is not None else "-",
                     elapsed, rows, rows / max(elapsed, 1e-9), tok_s,
                     torch.cuda.max_memory_allocated() / 2**30), flush=True)
        if not self.mid_done and self.mid_save_s \
                and elapsed >= self.mid_save_s:
            self.mid_done = True
            path = self.snapshot("wall_mid", step, exit_after=False)
            print("[prof] mid-slice wall snapshot -> %s (continuing)"
                  % path, flush=True)
        if not REASON and elapsed >= DEADLINE_S:
            REASON = "deadline"
        if REASON:
            self.finalize(REASON, step, elapsed)
        self.step_t = now

    # ------------------------------------------------------------- snapshots
    def snapshot(self, tag, step, exit_after):
        import torch
        final = os.path.join(self.save_root, "step_%06d" % step)
        if os.path.exists(final):
            final += "_" + tag
        tmp = final + ".tmp"
        shutil.rmtree(tmp, ignore_errors=True)
        t_save = time.time()
        self.trainer.save_model(tmp)
        cfg = json.load(open(os.path.join(tmp, "adapter_config.json")))
        assert cfg.get("r") == LORA_R, "adapter_config r=%s" % cfg.get("r")
        from safetensors import safe_open
        st = [f for f in os.listdir(tmp) if f.endswith(".safetensors")]
        assert len(st) == 1, "safetensors files: %s" % st
        with safe_open(os.path.join(tmp, st[0]), framework="pt") as f:
            n = len(f.keys())
        assert n == EXPECTED_LORA_TENSORS, "lora tensors=%d" % n
        os.rename(tmp, final)          # atomic: dir appears only when complete
        assert os.path.isdir(final) and not os.path.exists(tmp)
        size_mb = sum(os.path.getsize(os.path.join(final, x))
                      for x in os.listdir(final)) / 1e6
        print("[save] reason=%s step=%d -> %s (%.1f MB, %.2fs, %d tensors, "
              "r=%d, atomic=OK)" % (tag, step, final, size_mb,
                                    time.time() - t_save, n, LORA_R),
              flush=True)
        torch.cuda.synchronize()
        return final

    def finalize(self, reason, step, elapsed):
        import torch
        rows = step * EFFECTIVE_BATCH
        tok_s = rows * self.mean_tokens / max(elapsed, 1e-9)
        peak = torch.cuda.max_memory_allocated() / 2**30
        final = self.snapshot(reason, step, exit_after=True)
        info = {
            "reason": reason, "steps": step,
            "elapsed_s": round(elapsed, 1),
            "train_s": round(elapsed, 1),
            "steps_per_s": round(step / max(elapsed, 1e-9), 3),
            "rows": rows,
            "rows_per_s": round(rows / max(elapsed, 1e-9), 3),
            "mean_tokens_per_row": round(self.mean_tokens, 1),
            "tok_s": round(tok_s, 1),
            "peak_alloc_gib": round(peak, 2),
            "peak_reserved_gib": round(
                torch.cuda.max_memory_reserved() / 2**30, 2),
            "loss_first": self.losses[0] if self.losses else None,
            "loss_last": self.losses[-1] if self.losses else None,
            "save": final,
            "lora": {"r": LORA_R, "alpha": LORA_ALPHA,
                     "targets": TARGETS, "tensors": EXPECTED_LORA_TENSORS},
            "batch": {"per_device": 4, "grad_accum": 4, "seq": 1024,
                      "effective_rows": EFFECTIVE_BATCH},
        }
        os.makedirs(os.path.dirname(METRICS), exist_ok=True)
        tmp = METRICS + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(info, fh, indent=1)
        os.replace(tmp, METRICS)
        print("RESULT: P2_PROFILE_OK steps=%d reason=%s tok_s=%.0f "
              "rows_per_s=%.2f steps_per_s=%.3f peak_alloc=%.2fGiB "
              "loss=%.4f->%.4f save=%s"
              % (step, reason, tok_s, rows / max(elapsed, 1e-9),
                 step / max(elapsed, 1e-9), peak,
                 info["loss_first"]["loss"] if info["loss_first"] else -1,
                 info["loss_last"]["loss"] if info["loss_last"] else -1,
                 final), flush=True)
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mid-save", type=int, default=300)
    ap.add_argument("--fresh", action="store_true", default=True)
    args = ap.parse_args()

    import torch
    import transformers
    import trl
    from datasets import load_dataset
    from peft import LoraConfig, get_peft_model
    from trl import SFTConfig, SFTTrainer

    shutil.rmtree(OUTDIR, ignore_errors=True)
    os.makedirs(OUTDIR, exist_ok=True)

    print("python      : %s %s" % (sys.version.split()[0], sys.executable),
          flush=True)
    print("node        :", os.uname().nodename)
    print("device      :", torch.cuda.get_device_name(0))
    print("torch       : %s | cuda %s" % (torch.__version__, torch.version.cuda))
    print("transformers: %s | trl %s" % (transformers.__version__,
                                         trl.__version__))

    ds = load_dataset("json", data_files=[SFT], split="train")
    n_all = len(ds)
    ds = ds.filter(lambda r: r.get("split") == "train")
    mean_tokens = float(sum(ds["tokens"])) / max(len(ds), 1)
    print("dataset     : %d rows (%d train) mean_tokens=%.1f columns=%s"
          % (n_all, len(ds), mean_tokens, ds.column_names), flush=True)

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
        output_dir=os.path.join(OUTDIR, "trainer"),
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        learning_rate=1e-4,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        max_steps=100000,
        logging_steps=5,
        save_strategy="no",
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
                         processing_class=tok)
    prof = Profile(trainer, mean_tokens, args.mid_save, OUTDIR)
    trainer.add_callback(prof)

    for sig in (signal.SIGUSR1, signal.SIGTERM, signal.SIGALRM):
        signal.signal(sig, handler)
    signal.alarm(WALL_ALARM_S)
    print("signals     : SIGUSR1/SIGTERM/SIGALRM armed "
          "(usr1 expected at T-60s, alarm backup at %ds)" % WALL_ALARM_S,
          flush=True)

    try:
        trainer.train()
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        print("RESULT: P2_PROFILE_FAIL %s" % sys.exc_info()[1], flush=True)
        sys.exit(1)
    global REASON
    if not REASON:
        REASON = "completed"
    prof.finalize(REASON, trainer.state.global_step,
                  time.time() - (prof.t0 or time.time()))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        print("RESULT: P2_PROFILE_FAIL %s" % sys.exc_info()[1], flush=True)
        sys.exit(1)
