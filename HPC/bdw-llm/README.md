# BDW-LLM: Dual-Track Sovereign Hardware AI Platform

BerojgarDegreeWala (BDW) deep-tech research intelligence and sovereign hardware LLM platform, built for India's semiconductor, VLSI, embedded systems, and supercomputing ecosystem.

This repository actively maintains our **Dual-Track Development Strategy**:
1. **Track 1: 7B Production Deployment (Kaggle + Vercel)** — Scaled-down Qwen-7B GGUF model served on Kaggle free GPU resources for zero-cost public access on `berojgardegreewala.app`.
2. **Track 2: 72B Frontier R&D (Param Rudra HPC Cluster)** — Primary Qwen-72B sovereign model with deep-tech hardware LoRA adapters, multi-hop agentic loop, code interpreter, and Supabase vector RAG running on the Param Rudra supercomputer.

---

## Architecture Overview

```
                                      ┌─────────────────────────────────────────────────────────┐
                                      │              BerojgarDegreeWala Frontend                │
                                      │   (Vercel: berojgardegreewala.app & bdw-llm-frontend)   │
                                      └───────────────────────────┬─────────────────────────────┘
                                                                  │
                                                ┌─────────────────┴─────────────────┐
                                                │ Model Selector / Routing Gateway  │
                                                └────────┬────────────────────┬─────┘
                                                         │                    │
                        "BerojgarDegreeWala Custom 7B"   │                    │ "BDW Sovereign 72B"
                                 (Production Track)      │                    │     (Frontier R&D Track)
                                                         ▼                    ▼
                                           ┌───────────────────────┐ ┌───────────────────────────────┐
                                           │    Kaggle GPU Host    │ │    Param Rudra HPC Cluster    │
                                           │ (kaggle_backend.ipynb)│ │     (CDAC Delhi Supercomputer)│
                                           │   llama.cpp-python    │ │  vLLM 72B + Hardware LoRA     │
                                           │   bdw-7b-sft-Q4_K_M   │ │  api_server.py + watchdog.sh  │
                                           └───────────┬───────────┘ └───────────────┬───────────────┘
                                                       │                             │
                                                       └──────────────┬──────────────┘
                                                                      ▼
                                                       ┌─────────────────────────────┐
                                                       │   Cloudflare Named Tunnel   │
                                                       │ (ai.berojgardegreewala.app) │
                                                       └─────────────────────────────┘
```

---

## Track 1: 7B Production Deployment (Kaggle + Vercel)

- **Model Artifacts**:
  - Model: `bdw-7b-sft-Q4_K_M.gguf` (Quantized 4-bit Medium GGUF, ~4.68 GB)
  - Domain Adapters: `loras/p4_lora_vlsi.gguf`, `loras/p4_lora_embedded.gguf`, `loras/p4_lora_cs.gguf`, `loras/p4_lora_math.gguf`, `loras/p4_lora_aiml.gguf`
  - Hugging Face Repo: `aamitkr26/bdw-7b-sft` (Private)
- **Serving Stack**:
  - Jupyter Notebook: [`kaggle_backend.ipynb`](kaggle_backend.ipynb)
  - Runtime: FastAPI OpenAI-compatible server on port 8000 via `llama-cpp-python`
  - Ingress: Cloudflare Tunnel daemon (`cloudflared`) exposing endpoints:
    - `https://ai.berojgardegreewala.app/v1`
    - `https://kaggle.berojgardegreewala.app/v1`
- **Frontend Integration**:
  - UI model selector options: `"BerojgarDegreeWala Custom 7B (Kaggle)"`
  - Automated edge failover and keep-alive SSE streaming

---

## Track 2: 72B Frontier R&D (Param Rudra HPC Cluster)

- **Model Specifications**:
  - Base: `Qwen/Qwen2.5-72B-Instruct`
  - LoRA Adapter: `bdw-hardware-lora`
  - High-Performance Inference: Multi-GPU Slurm batch deployment (`run_production.slurm`) via vLLM on A100 80GB nodes
  - Agentic Gateway: `phase5_production/api_server.py` with multi-hop tool execution, dynamic Python code execution, and Supabase RAG
  - Process Watchdog: `phase5_production/watchdog.sh` monitoring API server, Named Tunnel, and Slurm queue
- **Completed R&D Milestones**:
  - **Phase 1**: From-scratch decoder-only pretraining on cluster
  - **Phase 2**: 7B SFT (`v2.0-bdw7b-sft`)
  - **Phase 3**: Supabase vector embeddings (384-d BGE-small) and RAG match engine
  - **Phase 4**: Domain-specific LoRA adapters (VLSI, Embedded, Math, CS, AIML)
  - **Phase 6**: Tool-use function calling & structured reasoning traces (100% format compliance)
  - **Phase 7**: Combined reasoning + tool execution (SFT job 186019, eval 186020: 100% format compliance)
  - **Phase 8**: Reinforcement learning via DPO (Direct Preference Optimization, job 186025) and final sequential PEFT merge (`merged/bdw7b-reasoning-dpo-final`, 14.20 GiB)
  - **Phase 9**: Production Agentic API Server with SSE keep-alive streaming and automatic cluster heartbeat

---

## Repository Structure

| Directory / File | Description |
|---|---|
| `agentic_skills/` | Agent reasoning loop and code execution runtime |
| `frontend/` | Vercel Next.js web application (`bdw-llm-frontend`) |
| `kaggle_backend.ipynb` | Autonomous Kaggle 7B production backend launcher |
| `phase3/` | Supabase RAG schemas, migrations, and vector match functions |
| `phase4/` | Domain adaptation pipelines and evaluation scripts |
| `phase5_production/` | Production 72B API server (`api_server.py`), Slurm harness, and `watchdog.sh` |
| `phase6_advanced/` | Tool-use function calling and reasoning dataset synthesis |
| `phase7_combined/` | Combined reasoning + tool-calling SFT and evaluation suite |
| `phase8_rl/` | Direct Preference Optimization (DPO) and sequential PEFT model merge |
| `tokenizer_domain/` | Specialized hardware and deep-tech BPE vocabularies |
| `training/` | Cluster Slurm launchers and training harnesses |
| `status.md` | Authoritative cluster R&D and synchronization tracking document |

---

## Security & Compliance Policy

- **Zero-Secret Commitment**: All private keys, Cloudflare tokens (`eyJh...`, `cfat_...`), Hugging Face tokens (`hf_...`), and Kaggle API keys are strictly excluded via `.gitignore` and managed exclusively through environment variables or secure vault secrets.
