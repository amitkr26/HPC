# BDW — From-Scratch LLM on PARAM Rudra

Decoder-only Transformer trained from **random initialisation** on
PARAM Rudra (CDAC Delhi). No pretrained weights, no pretrained tokenizer.

## Layout

| Path | Purpose |
|---|---|
| `docs/` | environment audit, setup notes, stage reports |
| `data/raw/` | downloaded corpus (login node only — see docs) |
| `data/tokens/` | tokenized shards produced from `data/raw/` |
| `tokenizer/` | trained byte-level BPE vocabulary |
| `src/` | model / training / data code |
| `scripts/` | one SLURM script per stage |
| `checkpoints/` | model checkpoints (frequent, 15-min walltime) |
| `logs/` | job logs |
| `venv/` | pinned Python environment |
| `env.sh` | `source` this to select the project venv |

## Environment

```bash
source $HOME/bdw-llm/env.sh      # selects ~/bdw-llm/venv
python -V && pip freeze > requirements.txt
```

`requirements.txt` is an exact `pip freeze` of the working environment.

## Network (verified — see docs/ENVIRONMENT_AUDIT.md)

* Login node: outbound HTTPS works (PyPI, Hugging Face, Wikimedia, GitHub).
* Compute nodes: **no DNS at all** — all downloads must run on the login
  node and be written to `/home`; jobs read them from shared storage.
