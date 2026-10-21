import os
import sys
import time

os.environ["OMP_NUM_THREADS"] = "4"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
import torch.nn as nn

sys.path.insert(0, "/home/tutor/3ioip3lt/bdw-llm/src")
from model import ModelConfig, TransformerLM

CKPT = "/home/tutor/3ioip3lt/bdw-llm/checkpoints_ft/step_0003000.pt"
OUT = "/home/tutor/3ioip3lt/bdw-llm/export"
os.makedirs(OUT, exist_ok=True)
torch.set_num_threads(4)

FP32 = os.path.join(OUT, "bdw_28m_fp32.onnx")
INT8 = os.path.join(OUT, "bdw_28m_int8.onnx")
SAFE = os.path.join(OUT, "bdw_28m.safetensors")


def mb(path):
    return os.path.getsize(path) / (1024.0 * 1024.0)


print("=" * 76)
print("PHASE 0 FEASIBILITY TEST  —  safetensors + ONNX + int8, CPU-only")
print("=" * 76)

# ---------------------------------------------------------------- load
t0 = time.time()
blob = torch.load(CKPT, map_location="cpu", weights_only=False)
cfg = ModelConfig(**blob["model_config"])
model = TransformerLM(cfg)
model.load_state_dict(blob["model"])
model.eval()
print("[load] %s  step=%s  params=%s  (%.1fs)"
      % (CKPT, blob.get("step"), f"{model.num_params():,}", time.time() - t0))
print("[load] cfg: vocab=%d seq_len=%d d_model=%d layers=%d heads=%d d_ff=%d"
      % (cfg.vocab_size, cfg.seq_len, cfg.d_model, cfg.n_layers,
         cfg.n_heads, cfg.d_ff))

# ------------------------------------------------------- safetensors
t0 = time.time()
from safetensors.torch import save_file, load_file, save_model, load_model

save_model(model, SAFE)
model2 = TransformerLM(cfg)
load_model(model2, SAFE)
model2.eval()
maxdiff = 0.0
for (n, a), (_, b) in zip(model.state_dict().items(), model2.state_dict().items()):
    maxdiff = max(maxdiff, float((a.float() - b.float()).abs().max()))
print("[safetensors] wrote %s  %.2f MB  roundtrip max|diff|=%.3e  (%.1fs)"
      % (SAFE, mb(SAFE), maxdiff, time.time() - t0))

# ------------------------------------------------------------ ONNX
class Wrap(nn.Module):
    def __init__(self, m):
        super().__init__()
        self.m = m

    def forward(self, idx):
        logits, _ = self.m(idx)
        return logits


wrapped = Wrap(model).eval()
dummy = torch.zeros((1, 64), dtype=torch.long)

t0 = time.time()
torch.onnx.export(
    wrapped, (dummy,), FP32,
    input_names=["input_ids"], output_names=["logits"],
    dynamic_axes={"input_ids": {0: "batch", 1: "seq"}, "logits": {0: "batch", 1: "seq"}},
    opset_version=17, do_constant_folding=True,
)
print("[onnx] exported fp32  %.2f MB  (%.1fs)" % (mb(FP32), time.time() - t0))

# -------------------------------------------------- parity: pytorch
xs = torch.randint(0, cfg.vocab_size, (2, 128), dtype=torch.long)
with torch.no_grad():
    ref, _ = model(xs)
ref = ref.float()

import onnxruntime as ort

so = ort.SessionOptions()
so.intra_op_num_threads = 4
so.inter_op_num_threads = 1

sess32 = ort.InferenceSession(FP32, so, providers=["CPUExecutionProvider"])
out32 = sess32.run(None, {"input_ids": xs.numpy()})[0]
d32 = float(abs(out32 - ref.numpy()).max())

t1 = time.time()
from onnxruntime.quantization import quantize_dynamic, QuantType

import onnx as _onnx

_m = _onnx.load(FP32)
_outname = _m.graph.output[0].name
_final = None
for _n in _m.graph.node:
    if _outname in _n.output:
        _final = _n.name
print("[onnx] final projection node: %s" % _final)

quantize_dynamic(FP32, INT8, weight_type=QuantType.QInt8, per_channel=False)
print("[quant] int8 per-tensor    %.2f MB  (%.1fs)  -> %.2fx smaller than fp32"
      % (mb(INT8), time.time() - t1, mb(FP32) / mb(INT8)))

INT8_PC = os.path.join(OUT, "bdw_28m_int8_perchannel.onnx")
quantize_dynamic(FP32, INT8_PC, weight_type=QuantType.QInt8, per_channel=True)
print("[quant] int8 per-channel   %.2f MB" % mb(INT8_PC))

INT8_EX = os.path.join(OUT, "bdw_28m_int8_exhead.onnx")
try:
    quantize_dynamic(FP32, INT8_EX, weight_type=QuantType.QInt8, per_channel=True,
                     nodes_to_exclude=[_final] if _final else [])
    print("[quant] int8 per-ch, lm_head kept fp32  %.2f MB" % mb(INT8_EX))
except Exception as ex:
    INT8_EX = None
    print("[quant] ex-head variant failed: %s: %s" % (type(ex).__name__, ex))

sess8 = ort.InferenceSession(INT8, so, providers=["CPUExecutionProvider"])
out8 = sess8.run(None, {"input_ids": xs.numpy()})[0]
d8 = float(abs(out8 - ref.numpy()).max())

sess_pc = ort.InferenceSession(INT8_PC, so, providers=["CPUExecutionProvider"])
out_pc = sess_pc.run(None, {"input_ids": xs.numpy()})[0]
d_pc = float(abs(out_pc - ref.numpy()).max())

sess_ex = None
if INT8_EX and os.path.exists(INT8_EX):
    sess_ex = ort.InferenceSession(INT8_EX, so, providers=["CPUExecutionProvider"])

def top1(a, b):
    return float((a.argmax(-1) == b.argmax(-1)).mean())

print()
print("-" * 76)
print("NUMERICAL PARITY  (batch=2, seq=128, random ids)")
print("-" * 76)
print("%-34s %12s %12s %12s" % ("runtime", "max|diff|", "top1 agree", "logit std"))
print("%-34s %12.4e %12s %12.4f" % ("pytorch fp32 (ref)", 0.0, "1.000", float(ref.std())))
print("%-34s %12.4e %12.3f %12.4f" % ("onnx fp32", d32, top1(out32, ref.numpy()), float(out32.std())))
print("%-34s %12.4e %12.3f %12.4f" % ("onnx int8 per-tensor", d8, top1(out8, ref.numpy()), float(out8.std())))
print("%-34s %12.4e %12.3f %12.4f" % ("onnx int8 per-channel", d_pc, top1(out_pc, ref.numpy()), float(out_pc.std())))
if sess_ex is not None:
    out_ex = sess_ex.run(None, {"input_ids": xs.numpy()})[0]
    print("%-34s %12.4e %12.3f %12.4f"
          % ("onnx int8 per-ch, lm_head fp32",
             float(abs(out_ex - ref.numpy()).max()), top1(out_ex, ref.numpy()), float(out_ex.std())))

# ------------------------------------------------------- benchmark
print()
print("-" * 76)
print("CPU THROUGHPUT  (4 threads, forward pass only — prefill)")
print("-" * 76)
print("%-10s %12s %12s %12s %12s" % ("seq_len", "pytorch", "onnx fp32", "onnx int8", "int8 speedup"))
for seq in (128, 256, 512, 1024):
    x = torch.zeros((1, seq), dtype=torch.long)
    rates = []
    with torch.no_grad():
        for _ in range(3):
            model(x)
        t0 = time.time()
        for _ in range(8):
            model(x)
        rates.append(seq * 8 / (time.time() - t0))
    for sess in (sess32, sess8):
        for _ in range(3):
            sess.run(None, {"input_ids": x.numpy()})
        t0 = time.time()
        for _ in range(8):
            sess.run(None, {"input_ids": x.numpy()})
        rates.append(seq * 8 / (time.time() - t0))
    print("%-10d %10.0f/s %10.0f/s %10.0f/s %11.2fx"
          % (seq, rates[0], rates[1], rates[2], rates[2] / rates[1]))

# ------------------------------------------- simulated decode loop
print()
print("-" * 76)
print("SIMULATED DECODE  (32 steps, full re-forward each step — as chat_with_rag.py does)")
print("-" * 76)
gen = 32
for name, runner in (
        ("pytorch fp32", lambda x: model(x)[0]),
        ("onnx fp32", lambda x: sess32.run(None, {"input_ids": x.numpy()})[0]),
        ("onnx int8", lambda x: sess8.run(None, {"input_ids": x.numpy()})[0])):
    ids = torch.randint(0, cfg.vocab_size, (1, 64), dtype=torch.long)
    with torch.no_grad():
        t0 = time.time()
        for _ in range(gen):
            out = runner(ids)
            nxt = int(out[0, -1].argmax())
            ids = torch.cat([ids, torch.tensor([[nxt]])], dim=1)
        dt = time.time() - t0
    print("%-14s %6.2fs   %6.1f tok/s   final_len=%d" % (name, dt, gen / dt, ids.shape[1]))

print()
print("-" * 76)
print("ARTEFACTS")
print("-" * 76)
for p in (FP32, INT8, INT8_PC, SAFE):
    print("  %-46s %8.2f MB" % (p.replace("/home/tutor/3ioip3lt/", "~/"), mb(p)))
if INT8_EX and os.path.exists(INT8_EX):
    print("  %-46s %8.2f MB" % (INT8_EX.replace("/home/tutor/3ioip3lt/", "~/"), mb(INT8_EX)))
print()
print("RESULT: PHASE0_EXPORT_TEST_OK")
