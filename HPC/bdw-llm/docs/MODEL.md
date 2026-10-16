# Model — Architecture + GPU Smoke Test (BDW Stage F)

**Executed:** 2026-10-16 14:04:32 IST
**Job:** `bdw_f_smoke` (job 31809) on `rdgpu01` — **COMPLETED / SMOKE_PASS**
**Code:** `src/model.py`, `src/smoke_test.py`, `scripts/smoke_test.slurm`

The model is written from scratch in PyTorch. **No pretrained weights are
loaded at any point** — every parameter comes from the init scheme below.

---

## 1. Architecture

Decoder-only Transformer (GPT-style), fully configurable via `ModelConfig`:

| Component | Choice |
|---|---|
| Token embedding | `Embedding(vocab_size, d_model)` |
| Positional embedding | learned absolute `Embedding(seq_len, d_model)` |
| Block | pre-LN: `x + attn(LN(x))`, `x + MLP(LN(x))` |
| Attention | multi-head causal self-attention via `F.scaled_dot_product_attention(..., is_causal=True)` |
| MLP | `Linear(d_model, d_ff)` -> GELU -> `Linear(d_ff, d_model)`, no biases |
| Final | `LayerNorm` + `lm_head` |
| Weight tying | `lm_head.weight is tok_emb.weight` |
| Dropout | 0.1 (attention output, MLP output, embeddings) |

### Configuration used for this run

| Key | Value | Why |
|---|---|---|
| `vocab_size` | **16384** | matches the Stage D tokenizer |
| `seq_len` | **1024** | matches the Stage E shard shape |
| `d_model` | 512 | |
| `n_layers` | 6 | |
| `n_heads` | 8 | `512 % 8 == 0`, head_dim 64 |
| `d_ff` | 2048 | 4 x d_model |
| `dropout` | 0.1 | |
| `tie_weights` | true | saves 8.4 M parameters |

`ModelConfig` validates `d_model % n_heads == 0` and positive sizes, and can be
saved/loaded as JSON, so later stages can retune the architecture without
touching the model code.

### Initialisation

* `nn.Linear` / `nn.Embedding`: `normal_(0, 0.02)`
* `nn.LayerNorm`: weight 1, bias 0
* residual output projections (`attn.proj`, `mlp.proj`): `normal_(0, 0.02 / sqrt(2 * n_layers))`
  — the GPT-2 trick that keeps residual-stream variance stable with depth.

## 2. SLURM directives used

```
#SBATCH --job-name=bdw_f_smoke
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --cpus-per-task=4
#SBATCH --time=00:15:00
#SBATCH --account=tutor
#SBATCH --qos=training
#SBATCH --output=%x-%j.out
#SBATCH --error=%x-%j.err
```

Exactly the four hard limits from the audit: `--partition=gpu`, `--gpus=1`,
`--cpus-per-task=4`, `--time=00:15:00` (QOS `training` allows `cpu<=4`,
`gpu<=1`, `MaxWall=00:15:00`).

## 3. Smoke test log

Read from `~/bdw-llm/scripts/bdw_f_smoke-31809.out`:

```
==========================================
SLURM_CLUSTER_NAME = paramrudra
SLURM_ARRAY_JOB_ID = 
SLURM_ARRAY_TASK_ID = 
SLURM_ARRAY_TASK_COUNT = 
SLURM_ARRAY_TASK_MAX = 
SLURM_ARRAY_TASK_MIN = 
SLURM_JOB_ACCOUNT = tutor
SLURM_JOB_ID = 31809
SLURM_JOB_NAME = bdw_f_smoke
SLURM_JOB_NODELIST = rdgpu01
SLURM_JOB_USER = 3ioip3lt
SLURM_JOB_UID = 56027
SLURM_JOB_PARTITION = gpu
SLURM_TASK_PID = 3213621
SLURM_SUBMIT_DIR = /home/tutor/3ioip3lt/bdw-llm/scripts
SLURM_CPUS_ON_NODE = 4
SLURM_NTASKS = 1
SLURM_TASK_PID = 3213621
==========================================
node      : rdgpu01
date      : 2026-10-16T14:03:07+05:30
which py  : /home/tutor/3ioip3lt/bdw-llm/venv/bin/python
CUDA_VISIBLE_DEVICES=0
nproc     : 48

GPU 0: NVIDIA A100 80GB PCIe (UUID: GPU-16845317-cfa6-e9c5-4858-eb7ffd7d6be2)

======================================================================
Stage F smoke test
======================================================================
torch              : 2.5.1+cu121
torch.version.cuda : 12.1
device_count       : 1
device_name        : NVIDIA A100 80GB PCIe
capability         : (8, 0)
total_mem GiB      : 79.2
SMs                : 108

config: {
  "vocab_size": 16384,
  "seq_len": 1024,
  "d_model": 512,
  "n_layers": 6,
  "n_heads": 8,
  "d_ff": 2048,
  "dropout": 0.1,
  "tie_weights": true,
  "layer_norm_eps": 1e-05,
  "init_std": 0.02
}

params total       : 27800576 (27.80 M)
params non-embedding: 27276288 (27.28 M)
weight tying       : True (expected True)

--- forward ---
logits shape       : (8, 1024, 16384)
fwd time           : 0.539s
loss               : 9.812388
ln(vocab)          : 9.704061  (expected init loss)
|loss - ln(vocab)| : 0.108328

--- backward ---
bwd time           : 0.133s
tensors with grads : 52 / 52
grad elements      : 27800576

--- 3 AdamW steps on this batch (overfit sanity) ---
  step 1 loss=9.812270  (0.213s)
  step 2 loss=9.533508  (0.099s)
  step 3 loss=9.231314  (0.100s)
loss decreased     : 9.812388 -> 9.231314

--- generation (shape only) ---
generate out shape : (1, 9)

--- throughput ---
tokens/step        : 8192
fwd tok/s          : 15205
fwd+bwd tok/s      : 12188
peak GPU mem GiB   : 4.41

saved -> /home/tutor/3ioip3lt/bdw-llm/checkpoints/smoke_test.json

SMOKE_PASS

SMOKE_STAGE_DONE rc=0
```

## 4. What was verified

| Check | Result |
|---|---|
| CUDA available on the node | yes — A100 80GB PCIe, compute 8.0, 108 SMs |
| Parameter count | **27,800,576** (27.80 M); 27.28 M excluding positional embedding |
| Weight tying | `lm_head.weight is tok_emb.weight` -> **True** |
| Forward output shape | `(8, 1024, 16384)` as specified |
| Loss finite | yes |
| Init loss vs `ln(vocab)` | `9.812388` vs `9.704061`, drift **0.108** (< 1.0) |
| Gradients present | **52 / 52** parameter tensors |
| Gradient element count | 27,800,576 (matches parameter count exactly) |
| Non-finite gradients | **none** |
| Optimiser steps reduce loss | `9.812388 -> 9.231314` over 3 AdamW steps |
| `generate()` shape | `(1, 9)` for 8 new tokens |
| Peak GPU memory | 4.41 GiB of 79.2 GiB |
| Throughput | 15,205 tok/s forward; 12,188 tok/s forward+backward |

The `ln(vocab)` comparison is the most useful check here: with random weights
the logits are near-uniform, so cross-entropy must land close to
`ln(16384) = 9.704`. A large drift would mean the init or output scaling is
wrong — it does not.

## 5. Result artefact

`~/bdw-llm/checkpoints/smoke_test.json` records config, parameter counts,
the loss sequence and peak memory for later comparison.

## 6. Next step

Stage G builds the training loop on top of this model, with checkpointing
every few minutes so it survives the 15-minute wall.

_Generated by the Stage F script; evidence re-read from the job log._
