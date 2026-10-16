# Environment Setup — PARAM Rudra (BDW Stage B)

**Executed:** 2026-10-16 10:58:14 IST
**Workspace:** `/home/tutor/3ioip3lt/bdw-llm`
**Verified on:** `rdgpu01` (job 31739)

This document records how the Python environment was built and the literal
output that proves it works on a GPU node. Nothing here was inferred: every
transcript block is captured from the cluster.

---

## 1. The binding constraint: the GPU driver

```
source: /home/tutor/3ioip3lt/hpc/jobs/bdw_a_gpu-31730.out
| NVIDIA-SMI 545.23.06              Driver Version: 545.23.06    CUDA Version: 12.3     |
```

The driver is **CUDA 12.3**. PyTorch refuses to initialise CUDA when it was
compiled for a *newer* CUDA runtime than the driver supports.

The first attempt (`pip install torch`, which resolves to `2.14.1+cu130`) was
installed and then tested on the GPU node. It failed:

```
torch.__version__   : 2.14.1+cu130
cuda.is_available() : False
UserWarning: CUDA initialization: The NVIDIA driver on your system is too old
(found version 12030). ... install a PyTorch version that has been compiled
with your version of the CUDA driver.
```

`found version 12030` = the driver's CUDA version, 12.3. Torch was built
against CUDA 13.0, so `torch.cuda.is_available()` returned `False`.

## 2. Why `torch==2.5.1+cu121` and nothing newer

Wheel indices checked on `download.pytorch.org`:

| Index | Newest torch available | Usable here? |
|---|---|---|
| `whl/cu121` | `2.5.1+cu121` | **yes** — CUDA 12.1 <= driver 12.3 |
| `whl/cu124` | `2.5.1+cu124` | borderline (12.4 > 12.3) |
| `whl/cu126` | `2.14.1+cu126` | **no** — 12.6 > 12.3 |
| `whl/cu128` | `2.9.1+cu128` | **no** — 12.8 > 12.3 |
| PyPI default | `2.14.1+cu130` | **no** — 13.0 > 12.3 |

PyTorch requires the driver version to be **>=** the CUDA version it was built
with, so the highest usable build is **`torch==2.5.1+cu121`**.

## 3. Knock-on version pinning

`transformers` 5.x requires `torch>=2.6`, which we cannot have. So the whole
HF stack is pinned to the last coherent 4.x combination:

| Package | Version | Why |
|---|---|---|
| `torch` | `2.5.1+cu121` | newest build the 12.3 driver accepts |
| `transformers` | `4.57.6` | newest 4.x; 5.x needs torch>=2.6 |
| `datasets` | `3.6.0` | 4.x/5.x need `huggingface-hub>=1.31`, incompatible with transformers 4.x |
| `huggingface-hub` | `0.36.2` | required by transformers 4.x |
| `tokenizers` | `0.22.2` | required by transformers 4.57 (`>=0.22,<0.23.1`) |
| `sentencepiece` | `0.2.2` | optional fast path for tokenization |

`pip check` confirms the set is self-consistent:

```
No broken requirements found.
```

## 4. Workspace layout

```
.
./.gitignore
./README.md
./checkpoints
./data
./data/raw
./data/tokens
./docs
./docs/ENVIRONMENT_AUDIT.md
./docs/ENVIRONMENT_SETUP.md
./env.sh
./logs
./requirements.txt
./scripts
./src
./tokenizer
```

| Path | Purpose |
|---|---|
| `docs/` | environment audit + this document |
| `data/raw/` | downloaded corpus (login node only) |
| `data/tokens/` | tokenized shards |
| `tokenizer/` | trained byte-level BPE vocabulary |
| `src/` | model / training / data code |
| `scripts/` | one SLURM script per stage |
| `checkpoints/` | checkpoints (15-min walltime forces frequent saves) |
| `logs/` | job logs |
| `venv/` | pinned environment (5.7G) |
| `env.sh` | source this to select the project venv |

## 5. How to activate

```bash
source $HOME/bdw-llm/env.sh
```

`env.sh` activates `~/bdw-llm/venv`. This matters because `.bashrc`
auto-activates the unrelated `~/hpc/venv`; `env.sh` overrides it. Verified on
the GPU node:

```
which py  : /home/tutor/3ioip3lt/bdw-llm/venv/bin/python
VIRTUAL_ENV=/home/tutor/3ioip3lt/bdw-llm/venv
```

## 6. Pinned requirements

`requirements.txt` is a full `pip freeze` (81 packages):

```
datasets==3.6.0
sentencepiece==0.2.2
tokenizers==0.22.2
torch==2.5.1+cu121
transformers==4.57.6
```

(Full list in `requirements.txt`.)

## 7. Verification — login node

```
transformers        4.57.6
torch               2.5.1+cu121
torch.version.cuda  12.1
torch available     True
datasets            3.6.0
tokenizers          0.22.2
```

`cuda.is_available()` is `False` here, which is **correct**: the login node has
no GPU (see `ENVIRONMENT_AUDIT.md` §5). Importing cleanly with
`is_torch_available() == True` is the login-side check.

## 8. Verification — GPU node (the test that matters)

`sbatch` on `--partition=gpu --gpus=1`, reading
`~/hpc/jobs/bdw_b_gpu-31739.out`:

```
==========================================
SLURM_CLUSTER_NAME = paramrudra
SLURM_ARRAY_JOB_ID = 
SLURM_ARRAY_TASK_ID = 
SLURM_ARRAY_TASK_COUNT = 
SLURM_ARRAY_TASK_MAX = 
SLURM_ARRAY_TASK_MIN = 
SLURM_JOB_ACCOUNT = tutor
SLURM_JOB_ID = 31739
SLURM_JOB_NAME = bdw_b_gpu
SLURM_JOB_NODELIST = rdgpu01
SLURM_JOB_USER = 3ioip3lt
SLURM_JOB_UID = 56027
SLURM_JOB_PARTITION = gpu
SLURM_TASK_PID = 3206932
SLURM_SUBMIT_DIR = /home/tutor/3ioip3lt/hpc/jobs
SLURM_CPUS_ON_NODE = 4
SLURM_NTASKS = 1
SLURM_TASK_PID = 3206932
==========================================
node      : rdgpu01
date      : 2026-10-16T10:55:11+05:30
which py  : /home/tutor/3ioip3lt/bdw-llm/venv/bin/python
python -V : Python 3.11.4
VIRTUAL_ENV=/home/tutor/3ioip3lt/bdw-llm/venv
base sys.prefix check: /home/tutor/3ioip3lt/bdw-llm/venv

--- nvidia-smi ---
GPU 0: NVIDIA A100 80GB PCIe (UUID: GPU-16845317-cfa6-e9c5-4858-eb7ffd7d6be2)

--- torch import + cuda ---
torch.__version__   : 2.5.1+cu121
torch.version.cuda  : 12.1
built with cuda     : True
cuda.is_available() : True
device_count()      : 1
device_name(0)      : NVIDIA A100 80GB PCIe
capability(0)       : (8, 0)
total_mem GiB       : 79.2
matmul on GPU       : OK  shape=(1024, 1024) sum=10254.1992
bf16 tensor on GPU  : OK torch.bfloat16 cuda:0
PROBE_OK

--- disk of the venv (NFS) ---
5.7G	/home/tutor/3ioip3lt/bdw-llm/venv
GPU_PROBE_DONE
```

---

## 9. Notes for later stages

* **Downloads must run on the login node.** Compute nodes have no DNS at all
  (`ENVIRONMENT_AUDIT.md` §8/§9). The venv works on compute nodes only because
  it lives on `/home`, which is NFS-mounted everywhere.
* `/home` is at 94% (1.6 T free). The venv is 5.7 G; installs used
  `--no-cache-dir` to avoid leaving wheels on the shared filesystem.
* Walltime is capped at **15 minutes** by QOS `training`; every training stage
  must checkpoint frequently.
* `transformers` is present for convenience (schedulers, tokenizer wrappers),
  but the model itself is written from scratch — no pretrained weights.

_Generated by the Stage B setup script; evidence re-read from the cluster._
