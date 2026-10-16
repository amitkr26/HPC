"""Stage F smoke test: prove the model runs and trains on a real GPU.

Checks, in order:
  1. CUDA is actually available and the right device is visible
  2. the model builds with the expected parameter count
  3. a dummy forward pass produces correctly-shaped logits
  4. cross-entropy loss is finite and close to ln(vocab) for random init
  5. backward pass populates every gradient, all finite
  6. a few AdamW steps reduce the loss
"""
from __future__ import annotations

import json
import math
import os
import sys
import time

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import ModelConfig, TransformerLM

ROOT = os.path.expanduser("~/bdw-llm")
BATCH = 8
SEQ = 1024
WARMUP_STEPS = 3


def fail(msg: str) -> None:
    print("SMOKE_FAIL: %s" % msg)
    raise SystemExit(1)


def main() -> None:
    print("=" * 70)
    print("Stage F smoke test")
    print("=" * 70)

    if not torch.cuda.is_available():
        fail("torch.cuda.is_available() is False")
    n = torch.cuda.device_count()
    props = torch.cuda.get_device_properties(0)
    print("torch              :", torch.__version__)
    print("torch.version.cuda :", torch.version.cuda)
    print("device_count       :", n)
    print("device_name        :", torch.cuda.get_device_name(0))
    print("capability         :", torch.cuda.get_device_capability(0))
    print("total_mem GiB      : %.1f" % (props.total_memory / 2**30))
    print("SMs                :", props.multi_processor_count)

    cfg = ModelConfig(vocab_size=16384, seq_len=SEQ, d_model=512,
                      n_layers=6, n_heads=8, d_ff=2048, dropout=0.1)
    print("\nconfig:", json.dumps(cfg.to_dict(), indent=2))

    device = "cuda"
    model = TransformerLM(cfg).to(device)
    np_total = model.num_params()
    np_nonemb = model.num_params(non_embedding=True)
    print("\nparams total       : %d (%.2f M)" % (np_total, np_total / 1e6))
    print("params non-embedding: %d (%.2f M)" % (np_nonemb, np_nonemb / 1e6))
    if np_total <= 0:
        fail("parameter count is not positive")

    tied = model.lm_head.weight is model.tok_emb.weight
    print("weight tying       :", tied, "(expected True)")
    if not tied:
        fail("lm_head is not tied to tok_emb")

    torch.manual_seed(1234)
    x = torch.randint(0, cfg.vocab_size, (BATCH, SEQ), device=device)
    y = torch.randint(0, cfg.vocab_size, (BATCH, SEQ), device=device)

    print("\n--- forward ---")
    torch.cuda.synchronize()
    t0 = time.time()
    logits, loss = model(x, y)
    torch.cuda.synchronize()
    fwd_t = time.time() - t0
    print("logits shape       :", tuple(logits.shape))
    expected = (BATCH, SEQ, cfg.vocab_size)
    if tuple(logits.shape) != expected:
        fail("logits shape %s != %s" % (tuple(logits.shape), expected))
    if not torch.isfinite(logits).all():
        fail("logits contain NaN/Inf")
    print("fwd time           : %.3fs" % fwd_t)
    print("loss               : %.6f" % loss.item())
    print("ln(vocab)          : %.6f  (expected init loss)" % math.log(cfg.vocab_size))
    if not torch.isfinite(loss):
        fail("loss is not finite")
    drift = abs(loss.item() - math.log(cfg.vocab_size))
    print("|loss - ln(vocab)| : %.6f" % drift)
    if drift > 1.0:
        fail("init loss drifted %.3f from ln(vocab); check init/output scaling" % drift)

    print("\n--- backward ---")
    torch.cuda.synchronize()
    t0 = time.time()
    model.zero_grad(set_to_none=True)
    loss.backward()
    torch.cuda.synchronize()
    bwd_t = time.time() - t0
    print("bwd time           : %.3fs" % bwd_t)

    named_params = list(model.named_parameters())
    total_grad = 0
    missing = []
    nonfinite = []
    for name, p in named_params:
        if p.grad is None:
            missing.append(name)
            continue
        g = p.grad
        total_grad += g.numel()
        if not torch.isfinite(g).all():
            nonfinite.append(name)
    print("tensors with grads : %d / %d" % (len(named_params) - len(missing),
                                            len(named_params)))
    print("grad elements      : %d" % total_grad)
    if missing:
        fail("no gradient for: %s" % missing[:5])
    if nonfinite:
        fail("non-finite gradient in: %s" % nonfinite[:5])

    print("\n--- %d AdamW steps on this batch (overfit sanity) ---" % WARMUP_STEPS)
    opt = torch.optim.AdamW(model.parameters(), lr=3e-4, betas=(0.9, 0.95),
                            weight_decay=0.1)
    losses = [loss.item()]
    for step in range(WARMUP_STEPS):
        torch.cuda.synchronize()
        t0 = time.time()
        opt.zero_grad(set_to_none=True)
        _, loss = model(x, y)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        torch.cuda.synchronize()
        losses.append(loss.item())
        print("  step %d loss=%.6f  (%.3fs)"
              % (step + 1, loss.item(), time.time() - t0))
    if not all(math.isfinite(v) for v in losses):
        fail("loss became non-finite during optimisation")
    if losses[-1] >= losses[0]:
        fail("loss did not decrease: %s" % losses)
    print("loss decreased     : %.6f -> %.6f" % (losses[0], losses[-1]))

    print("\n--- generation (shape only) ---")
    with torch.no_grad():
        idx = torch.zeros((1, 1), dtype=torch.long, device=device)
        out = model.generate(idx, max_new_tokens=8, temperature=0.8, top_k=40)
    print("generate out shape :", tuple(out.shape))
    if tuple(out.shape) != (1, 1 + 8):
        fail("generate returned wrong shape")

    print("\n--- throughput ---")
    tok_per_fwd = BATCH * SEQ
    print("tokens/step        : %d" % tok_per_fwd)
    print("fwd tok/s          : %.0f" % (tok_per_fwd / max(fwd_t, 1e-9)))
    print("fwd+bwd tok/s      : %.0f" % (tok_per_fwd / max(fwd_t + bwd_t, 1e-9)))

    mem = torch.cuda.max_memory_allocated() / 2**30
    print("peak GPU mem GiB   : %.2f" % mem)

    out_path = os.path.join(ROOT, "checkpoints", "smoke_test.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as fh:
        json.dump({
            "device": torch.cuda.get_device_name(0),
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "capability": list(torch.cuda.get_device_capability(0)),
            "config": cfg.to_dict(),
            "params_total": np_total,
            "params_non_embedding": np_nonemb,
            "weight_tied": bool(tied),
            "init_loss": losses[0],
            "ln_vocab": math.log(cfg.vocab_size),
            "losses": losses,
            "peak_mem_gib": mem,
            "grad_tensors_missing": missing,
            "grad_tensors_nonfinite": nonfinite,
        }, fh, indent=2)
    print("\nsaved ->", out_path)

    print("\nSMOKE_PASS")


if __name__ == "__main__":
    main()
