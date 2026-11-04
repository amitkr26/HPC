"""P2.0 environment smoke test (docs/PHASE2_7B_BLUEPRINT.md, milestone P2.0).

Proves inside one 15-minute A100 slice, on a compute node with no internet:

  1. venv_p2 imports the LoRA-SFT stack (transformers/trl/peft/accelerate)
  2. Qwen2.5-7B-Instruct loads offline in bf16 onto the GPU
  3. a LoRA adapter attaches and one real train step (2 x 1024) runs -- no OOM
  4. the adapter saves, reloads onto a fresh base, bitwise-identical
  5. greedy generation works end to end

Success prints "RESULT: P2_SMOKE_OK ..."; any exception prints
"RESULT: P2_SMOKE_FAIL ..." and exits 1.
"""
import gc
import inspect
import os
import shutil
import sys
import time
import traceback

import torch

ROOT = os.path.expanduser("~/bdw-llm")
BASE = os.path.join(ROOT, "teacher_model_7b")
SMOKE_DIR = os.path.join(ROOT, "lora_smoke")
ADIR = os.path.join(SMOKE_DIR, "adapter")
SEQ_LEN, BATCH = 1024, 2
TARGETS = ["q_proj", "k_proj", "v_proj", "o_proj",
           "gate_proj", "up_proj", "down_proj"]


def mem(tag):
    torch.cuda.synchronize()
    print("[mem] %-14s peak_alloc=%.2f GiB  reserved=%.2f GiB" % (
        tag,
        torch.cuda.max_memory_allocated() / 2**30,
        torch.cuda.memory_reserved() / 2**30), flush=True)


def main():
    import accelerate
    import datasets
    import peft
    import transformers
    import trl
    from peft import LoraConfig, PeftModel, get_peft_model

    print("python      : %s %s" % (sys.version.split()[0], sys.executable),
          flush=True)
    print("node        :", os.uname().nodename)
    print("device      :", torch.cuda.get_device_name(0))
    print("torch       : %s | cuda %s" % (torch.__version__, torch.version.cuda))
    print("transformers:", transformers.__version__)
    print("trl         :", trl.__version__)
    print("peft        :", peft.__version__)
    print("accelerate  :", accelerate.__version__)
    print("datasets    :", datasets.__version__)
    try:
        import bitsandbytes as bnb
        print("bitsandbytes:", bnb.__version__)
    except Exception as e:
        print("bitsandbytes: UNAVAILABLE (%s) -- bf16 path unaffected" % e)
    params = list(inspect.signature(trl.SFTTrainer.__init__).parameters)
    print("SFTTrainer  : %s" % " ".join(params[2:]), flush=True)

    t0 = time.time()
    torch.cuda.reset_peak_memory_stats()
    tok = transformers.AutoTokenizer.from_pretrained(BASE, local_files_only=True)
    model = transformers.AutoModelForCausalLM.from_pretrained(
        BASE, torch_dtype=torch.bfloat16, local_files_only=True)
    model.to("cuda")
    model.config.use_cache = False
    n_all = sum(p.numel() for p in model.parameters())
    print("base loaded : %.1f s | %.3f B params | dtype=%s"
          % (time.time() - t0, n_all / 1e9, next(model.parameters()).dtype),
          flush=True)
    mem("base+kv")

    lora_cfg = LoraConfig(
        r=16, lora_alpha=32, lora_dropout=0.05, bias="none",
        task_type="CAUSAL_LM", target_modules=TARGETS)
    model = get_peft_model(model, lora_cfg)
    model.print_trainable_parameters()
    mem("lora attach")

    text = ("Eligibility: B.E./B.Tech in Electronics for the JRF post at DRDO. "
            "The last date to apply is 2026-03-15. ") * 60
    enc = tok(text, return_tensors="pt", truncation=True, max_length=SEQ_LEN)
    batch = {k: torch.cat([v, v], dim=0).to("cuda")
             for k, v in enc.items()}
    batch["labels"] = batch["input_ids"].clone()
    trainable = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(trainable, lr=1e-4)
    t1 = time.time()
    out = model(**batch)
    out.loss.backward()
    opt.step()
    opt.zero_grad(set_to_none=True)
    torch.cuda.synchronize()
    print("train step  : loss=%.4f wall=%.1f s | %d x %d tokens"
          % (out.loss.item(), time.time() - t1, BATCH, SEQ_LEN), flush=True)
    mem("after step")

    os.makedirs(SMOKE_DIR, exist_ok=True)
    kept = {k: v.detach().float().cpu().clone()
            for k, v in model.state_dict().items() if "lora_" in k}
    t2 = time.time()
    model.save_pretrained(ADIR)
    size_mb = sum(os.path.getsize(os.path.join(ADIR, f))
                  for f in os.listdir(ADIR)) / 1e6
    print("adapter save: %.1f MB in %.1f s -> %s"
          % (size_mb, time.time() - t2, ADIR), flush=True)

    del model, opt, out, batch, enc, trainable
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()

    t3 = time.time()
    base2 = transformers.AutoModelForCausalLM.from_pretrained(
        BASE, torch_dtype=torch.bfloat16, local_files_only=True)
    m2 = PeftModel.from_pretrained(base2, ADIR)
    m2.to("cuda")
    m2.eval()
    m2.config.use_cache = True
    got = {k: v.detach().float().cpu()
           for k, v in m2.state_dict().items() if "lora_" in k}
    same = len(got) == len(kept) and all(
        torch.equal(kept[k], got[k]) for k in kept)
    print("reload      : %d lora tensors | bitwise-equal=%s | %.1f s"
          % (len(got), same, time.time() - t3), flush=True)
    if not same:
        raise RuntimeError("adapter save/reload roundtrip mismatch")
    mem("reloaded")

    ids = tok("What is the last date", return_tensors="pt").input_ids.to("cuda")
    t4 = time.time()
    gen = m2.generate(ids, max_new_tokens=8, do_sample=False,
                      pad_token_id=tok.eos_token_id)
    reply = tok.decode(gen[0][ids.shape[1]:], skip_special_tokens=True)
    print("generate    : %r | %.1f s" % (reply, time.time() - t4), flush=True)

    peak = torch.cuda.max_memory_allocated() / 2**30
    shutil.rmtree(SMOKE_DIR, ignore_errors=True)
    print("RESULT: P2_SMOKE_OK peak_alloc=%.2fGiB load=%.1fs total=%.1fs"
          % (peak, t1 - t0, time.time() - t0), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        print("RESULT: P2_SMOKE_FAIL %s" % sys.exc_info()[1], flush=True)
        sys.exit(1)
