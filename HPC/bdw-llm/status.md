# BDW-LLM Project Status

**Last updated:** 2026-11-05 15:02 IST
**Audit host:** `paramrudra.cdacdelhi.in:4422` (`3ioip3lt`)
**Cluster project:** `/home/tutor/3ioip3lt/bdw-llm`
**Local project:** `C:\Users\STUDENT\Desktop\Amit\HPC\bdw-llm`
**Maintenance rule:** Update this file after every work session on Param Rudra. The cluster copy and canonical GitHub copy are authoritative; do not create new persistent project files on the local device. Never record secrets, tokens, or keys here.

## 1. Executive Summary

**Overall status: AMBER - core R&D works; P5 is paused and not live; Phase 6 tool-use LoRA SFT is complete and the post-SFT adapter scores 100% (24/24) on the held-out seed suite; the reasoning baseline is established and no reasoning adapter has been trained yet.**

- Phase 1, Phase 2, and Phase 4 are complete.
- Phase 6 tool-use capability: deterministic generator (120 train / 24 eval rows), baseline (54.2% valid format), LoRA SFT (job `185946`), and post-SFT evaluation (job `185947`) are complete. The adapter scores 24/24 (100.0%) on the same held-out prompts, with 0 missing closing tags and 0 plain-text answers; this is seed-suite evidence, not production generalization.
- Phase 6 reasoning baseline: deterministic `<think>` dataset (120 train / 24 eval rows) is complete; base `v2.0-bdw7b-sft` scored 0/24 (0.0%) strict `<think>` format and 15/24 (62.5%) semantic accuracy (math 8/8, logic 7/8, coding 0/8). All 24 outputs were plain prose; math/logic show native step-by-step reasoning, while coding described algorithms without code. No reasoning SFT adapter has been trained or evaluated yet.
- Phase 3 core (Supabase, RAG, gateway, demo UI) is live. P3.4/P3.5 release-gate and production UI integration are not evidenced as complete.
- P5.0 shim is complete. P5.1 zero-cost production is scaffolded, hardened, and test-green but not launched.
- The P4 7B stack is live and serving correctly.
- The P5 70B public endpoint is not live; DNS does not resolve and no production job exists.
- Canonical GitHub reasoning baseline commit is `18ccd2c`; cluster reasoning baseline commit is `4ca8498`; canonical reasoning dataset commit is `86ba553`; cluster reasoning dataset commit is `6cc0e1e`; cluster post-SFT evaluation is committed at `701cccd`; the legacy local checkout remains at `b25b71d`.

Approximate completion: **model/R&D ~100%, integration ~85-90%, production ~5-10%, overall ~85%** by planned scope.

## 2. Phase Status

| Scope | Status | Evidence / notes |
|---|---|---|
| Phase 1 - from-scratch 28M model | DONE | 27.8M decoder-only model, 200,000 steps, held-out ppl `52.40` vs `18,603.31` untrained. |
| Phase 2 - 7B SFT | DONE | `v2.0-bdw7b-sft`, LoRA r=32/alpha=64, 748 steps, val loss `0.4052`; p2-v2 gates green; Q4 top-1 agreement `0.9682`. |
| Phase 3 - RAG/Supabase/gateway/UI | LIVE / PARTIAL | Core stack live; Supabase and gateway verified. P3.4/P3.5 production release gate, Next.js integration, and telemetry not evidenced. |
| Phase 4 - domain LoRA + RAG | DONE | Five adapters, five exported GGUFs, five domain RAG indexes, Supabase domain tables, router integration `58/58` tests, P4 eval v2 scored. |
| Phase 5.0 - shim/contract | DONE | Earlier `P5_SHIM_OK port=8090 auth=required models=6`; P5.0 contract tests previously passed. |
| Phase 5.1 - zero-cost production | READY / SECRETS PENDING | Isolated venv, clean `pip check`, `97 passed / 2 skipped`, hardened launcher, staged `cloudflared`, `.env` scaffolded. `P5_API_KEY` and `TUNNEL_TOKEN` remain empty; DNS unresolved; no Slurm job. |
| Phase 5.2 - production Supabase | TODO | Migration/seed/parity/RLS/backups/key rotation not started. |
| Phase 5.3 - BDW integration | TODO | Provider/model `bdw-career-ai`, metadata `user_id`, technical-intent split, citations, feature flag, canary not done. |
| Phase 5.4 - release gates | TODO | Eval gates, load/security tests, dashboards, rollback runbook, SLO certification not done. |
| Phase 5.5 - feedback flywheel | TODO | Feedback capture and LoRA refresh loop not started. |
| Phase 6 - tool use/function calling | POST-SFT EVALUATED | Deterministic generator (120 train / 24 eval rows); baseline 54.2% strict format (13/24); LoRA SFT job `185946`; post-SFT adapter 100.0% strict format (24/24), 0 missing closing tags, 0 plain-text answers, 24/24 exact semantic; seed-suite evidence, not production-scale. |
| Phase 6 - reasoning traces | BASELINE EVALUATED | Deterministic generator and 120 train / 24 eval `<think>` rows (40 / 8 per category); baseline 0/24 strict format, 15/24 semantic accuracy (math 8/8, logic 7/8, coding 0/8); no reasoning adapter trained. |
| Cluster source control | DONE / CANONICAL PUSHED | Cluster reasoning baseline `4ca8498`; canonical GitHub reasoning baseline `18ccd2c`; cluster post-SFT evaluation `701cccd`; cluster push still requires GitHub credentials. |

## 3. Current Live State

| Component | State |
|---|---|
| P4 llama.cpp server | PID `2547486`, `127.0.0.1:8081`, approximately 2d uptime, Q4_K_M 7B plus five LoRA GGUFs. |
| P4 gateway | PID `2547658`, `127.0.0.1:8787`; `/health` 200 and `/` 200. |
| P4 live smoke test | POST `/ask` for CMOS setup/hold returned the correct VLSI answer, routed to `lora_vlsi`/`idx_vlsi`, confidence `1.0`. |
| P4 Supabase selftest | All five domain tables readable; `P4_ZONE2_SUPABASE_OK domains=5`. |
| P5 shim | Not running. Stale PIDs `2576876` and `3425896`; port `8090` is dead. |
| P5 production job | Not submitted; no `bdw_70b_prod` in `squeue` or `sacct`. |
| P5 public endpoint | `ai.berojgardegreewala.com` does not resolve from the workstation. |
| Disk | Home filesystem 25T, 99% used, 476G available. Project `~/bdw-llm` is about 83G; HF cache is 136G. |
| Git | Cluster reasoning baseline at `4ca8498`; canonical GitHub reasoning baseline at `18ccd2c`; cluster post-SFT evaluation at `701cccd`; local legacy checkout at `b25b71d`, intentionally not updated under cluster-only policy. |
| P5 venv | `venv_p5`: 6.9G, isolated, Python 3.11.4, `include-system-site-packages=false`. Old venv backed up as `venv_p5.pre-isolation-20261104-095234` (ignored). |
| Phase 6 tool dataset | `phase6_advanced/tools/data/`: 120 train / 24 eval; 406,742 B / 79,171 B; train SHA-256 `47f7bd8a2f801067cee717da000c9de69bb671a7c5dda720aa1a2c46f2265c3a`; eval SHA-256 `9a525bde07da6f5daa2843b813810c147b7c605e64b36e557c799c0cb57f905f`; Git-ignored. |
| Phase 6 reasoning dataset | `phase6_advanced/reasoning/data/`: 120 train / 24 eval; 40 / 8 per category (math, logic, coding); train SHA-256 `9b79d4d77ccd463ee2233ab514e1a1826b6509315485bc6393d38dc7f59209ba`; eval SHA-256 `9af52700204698c9db3e9feba32032eb48abb193b198e802c96f0c1f864b5046`; Git-ignored. |

## 4. Verified Metrics

### Phase 1

- Model: 27.8M parameters, decoder-only Transformer trained from random initialization.
- Training: 200,000 steps.
- Held-out perplexity: `52.40` vs `18,603.31` untrained.

### Phase 2

- Model: `v2.0-bdw7b-sft` (Qwen2.5-7B-Instruct + LoRA).
- LoRA: rank 32, alpha 64.
- Training: 748 steps; validation loss `0.4052`.
- Evaluation: p2-v2 gates green.
- Quantized serving agreement: Q4_K_M top-1 agreement `0.9682` (`PASS_SERVE_Q4`).
- Artifacts: Q4_K_M GGUF 4.4G; f16 GGUF 15G.

### Phase 4

25 prompts total, 5 per domain, rubric v2:

| Domain | Adapter | Base | Gain | Pass |
|---|---|---:|---:|---:|
| math | 0.9333 | 0.7267 | +0.2066 | 100% |
| vlsi | 0.9333 | 0.4000 | +0.5333 | 100% |
| embedded | 0.9500 | 0.7500 | +0.2000 | 100% |
| cs | 0.8000 | 0.8667 | -0.0667 | 80% |
| aiml | 0.8667 | 0.8667 | 0.0000 | 100% |
| **Overall** | **0.8967** | **0.7220** | **+0.1747** | - |

Overall record: 10 wins / 13 ties / 2 losses. The CS adapter regresses against base; bypass or retrain it. The 25-prompt evaluation is directional, not production-grade evidence.

Phase 4 artifacts: five adapters (~309M each), five `export/p4_lora_*.gguf` files, five domain RAG indexes, Supabase domain tables, and a model-backed router.

### Phase 6

- Generator: `phase6_advanced/tools/generate_tool_dataset.py` (403 lines, CPU-only, stdlib plus cached tokenizer).
- Dataset: 120 train / 24 eval rows; 115 calculator, 29 unit-converter; 104 call-only, 40 full trajectories.
- Rendering: Qwen2.5 `# Tools` plus `<tool_call>`; JSON object arguments; token range 403-467, mean 421.86.
- Validation: 144 unique IDs/questions, no cross-split duplicates, full rows contain tool result plus final answer; deterministic rerun hashes match.
- Outputs: `tool_calls_train.jsonl`, `tool_calls_eval.jsonl`, `dataset_summary.json` (Git-ignored).
- Baseline Evaluator: `phase6_advanced/tools/evaluate_tools_baseline.py` and `phase6_advanced/tools/evaluate_tools_baseline.slurm`; published at `9f7f7d9`.
- Baseline Results (`v2.0-bdw7b-sft`, Slurm Job `185940`, 14.7s generation / 52s job):
  - Valid Tool Call Format Rate: **54.2% (13/24)**
  - Clean Tool Call Format: 54.2% (13/24)
  - JSON Body in `<tool_call>` Tag: 91.7% (22/24)
  - Missing Closing Tag (`</tool_call>`): 37.5% (9/24)
  - Plain Text (Bypassed Tool): 8.3% (2/24)
  - Exact Semantic Match: 50.0% (12/24)
- Status: baseline established; model understands tool intent (91.7%) but requires fine-tuning to reliably close tags and avoid arithmetic shortcutting.

### Phase 6 LoRA training pipeline

- Training script: `phase6_advanced/tools/train_tool_calling.py` (SHA-256 `38b42e26937c988ff4d15dcac95a93f3a44024b1fcf4ce66cdfda900c0c56a32`).
- Launcher: `phase6_advanced/tools/train_tools.slurm` (SHA-256 `2adc52a1f9e57c29f4b27e4e6e099c38761b883daf17a9d7dc5d84645b6c5e1a`), one A100, 4 CPUs, 48G RAM, wall time `00:15:00`, QOS `training`.
- Base/adapter: `merged/bdw-7b-sft` -> `lora_tools/p6_tool_calling/final`; trainer state in `sft_runs/p6_tools`.
- LoRA: `r=16`, `alpha=32`, dropout `0.05`, seven Qwen2 projection modules; 40,370,176 trainable parameters (`0.5273%`).
- Objective: loss on assistant tokens only; system/user/tool-response tokens are masked. The 24-row eval split is held out for eval loss.
- Schedule: 3 epochs, batch 4, sequence length 768, lr `1e-4` cosine, 3% warmup, bf16, `paged_adamw_8bit`; expected 90 optimizer steps.
- Smoke test: Job `185944` completed `RESULT: P6_TRAIN_OK` at one step in 44s (29.8s internal), producing adapter and metadata; smoke outputs were removed.
- Full training: job `185946` completed in 1m55s at step 90; final adapter SHA-256 `9ce5c70035f1824ac83d7ae83cdb6cc73302a2ddc214819353742dc53200d7ec`.
- Full training command: `cd ~/bdw-llm && sbatch phase6_advanced/tools/train_tools.slurm`.

### Phase 6 post-SFT evaluation

- Evaluator: `phase6_advanced/tools/evaluate_tools_trained.py`; launcher `evaluate_tools_trained.slurm`.
- Model: base `merged/bdw-7b-sft` plus `lora_tools/p6_tool_calling/final`; adapter SHA-256 `9ce5c70035f1824ac83d7ae83cdb6cc73302a2ddc214819353742dc53200d7ec`.
- Evaluation: same 24 rows and SHA-256 `9a525bde07da6f5daa2843b813810c147b7c605e64b36e557c799c0cb57f905f`, same prompt rendering, greedy decoding, seed 1337, 192 new tokens.
- Job `185947`: completed in 1m13s on `rdgpu01` A100 80GB; 32s model evaluation.
- Valid Tool Call Format Rate: **24/24 (100.0%)**, up from 13/24 (54.2%): **+11 hits / +45.8 points**.
- Missing closing tag: 0/24 (baseline 9/24); plain text: 0/24 (baseline 2/24); malformed: 0/24; multiple calls: 0/24.
- Exact semantic match: 24/24 (100.0%); clean format (no extra text): 24/24.
- Raw output: `phase6_advanced/tools/eval/tool_trained_v2_0_bdw7b_sft_lora_p6.json` (30,216 B; SHA-256 `b8ec30b51421959cbf7aa6db7927bb6af93667c5b93b1c13861e19b5bc38260a`).
- Caveat: the eval values are unseen, but the prompts use the same two tools and templates as training; 24/24 is evidence for this seed suite, not production-scale generalization.

### Phase 6 reasoning dataset

- Generator: `phase6_advanced/reasoning/generate_reasoning_dataset.py` (SHA-256 `b2b5c5727d45382622cf88b68746bc395feb3993037280cf7cc422d3d9928b3f`); README `phase6_advanced/reasoning/README.md`.
- Dataset: 120 train / 24 eval rows; 40 / 8 each for math, logic, and coding; deterministic seed `20261105`.
- Rendering: Qwen2.5 chat template; each assistant target has one non-empty `<think>` block followed by a final answer; coding targets end in a fenced Python implementation.
- Math coverage: inventory, discount, production, and area difference (12 each). Logic: five-item ordering puzzles (race 14, line 20, shelf 14). Coding: 12 functions x 4 sample calls.
- Token range: train `166-335`, mean `206.29`; eval `174-317`, mean `214.54`.
- Train SHA-256 `9b79d4d77ccd463ee2233ab514e1a1826b6509315485bc6393d38dc7f59209ba`; eval SHA-256 `9af52700204698c9db3e9feba32032eb48abb193b198e802c96f0c1f864b5046`.
- Validation: 144 unique questions with no cross-split duplicates; math answers independently recomputed; all logic answers satisfy every clue; all coding samples execute with the stated output; think tags and final answers checked; rerun produced identical hashes.
- Status: baseline evaluated. No reasoning SFT adapter has been trained or evaluated.

### Phase 6 reasoning baseline

- Evaluator: `phase6_advanced/reasoning/evaluate_reasoning_baseline.py` (SHA-256 `b8a45f123d054efe3f20dc5fef6b5ee91ababf34d09b1d854b120acad155cb10`); launcher `evaluate_reasoning_baseline.slurm` (SHA-256 `93a9f5fc39534955f6a869e7e3b8bddb06a4a678354db7332493c5e1f21e3b34`).
- Model: `merged/bdw-7b-sft` (`v2.0-bdw7b-sft`), no adapter; job `185954` on `rdgpu01` A100 80GB; greedy, seed `1337`, `max_new_tokens=384`.
- Result: `phase6_advanced/reasoning/eval/reasoning_baseline_v2_0_bdw7b_sft.json` (43,867 B; SHA-256 `a99c2b22806d3b2743525c4ecec258b855aaaed43486f03d1667c862d1340784`); 33.8s generation, 1m09s job.
- Strict `<think>` format: **0/24 (0.0%)**; plain text/no tags: 24/24; complete think block: 0/24.
- Semantic accuracy: **15/24 (62.5%)**; math 8/8 (100.0%), logic 7/8 (87.5%), coding 0/8 (0.0%).
- All outputs were prose. Math/logic responses contain explicit multi-step natural-language reasoning; coding responses described an algorithm but never emitted a Python implementation.
- Sole logic miss `reason_eval_logic_0012` reversed the order; all coding misses had no implementation to execute.
- Conditional accuracy on valid format is undefined (0 valid rows).
- Status: baseline established; reasoning LoRA SFT/eval still TODO.

## 5. P5 Deployment Inventory

| Item | State |
|---|---|
| Qwen2.5-72B-Instruct weights | Cached, 136G; `~/bdw-llm-72b.done` contains `ok`. |
| vLLM | Isolated in `venv_p5`: `0.6.6.post1`; torch `2.5.1+cu121`; torchvision `0.20.1+cu121`; transformers `4.55.4`. |
| P5 dependency set | `phase5/deploy/requirements-cluster.txt`; `pip check` clean. NumPy `1.26.4`, pyarrow `20.0.0`, datasets `3.6.0`, sentence-transformers `4.1.0`. |
| `phase5/deploy/run_production.slurm` | Hardened, tracked, syntax-checks. Fails on missing `.env`, `P5_API_KEY`, `TUNNEL_TOKEN`, or Supabase credentials; sets offline HF flags; fails if `live_probe.py` fails. |
| `phase5/deploy/live_probe.py` | Updated cluster version, tracked, compiles. Local harness requires `P5_API_KEY`. |
| `cloudflared` | Staged at `~/.local/bin/cloudflared`, version `2026.10.7`, 40,274,445 B. `prestage_cloudflared.sh` is idempotent. |
| Cluster `phase5/deploy/.env` | Present, chmod `600`, Git-ignored. `TP_SIZE=2`, `MAX_MODEL_LEN=8192`, `P4_DOMAIN_BACKEND=supabase`; Supabase URL/service key set. |
| `P5_API_KEY` | Empty in cluster `.env`; must be supplied by the user. |
| `TUNNEL_TOKEN` | Empty in cluster `.env`; must be supplied by the user. |
| Supabase credentials | Present in `phase3/.env` and copied into P5 `.env`; not committed. |
| Public DNS | `ai.berojgardegreewala.com` has no resolving record from the workstation. |
| Slurm test-only | Accepted: Job `185909`, estimated start `2026-11-06T05:20:34`, `rdgpu01`, 24 processors. |
| Actual production job | Not submitted. |
| P5 test suite on cluster | `97 passed, 2 skipped` in 2.10s. Golden parity uses the deterministic keyword classifier; semantic classifier separately smoke-tested. |
| BGE model | Re-saved from ST 6.2 format to ST 4.1-compatible format; embeddings match existing anchors at cosine `1.0`; both `venv_p5` and P4 `venv` load it. Backup: `phase3/models/bge-small-en-v1.5.st6-backup-20261104-100843`. |
| `P5_LIVE_OK` marker | Not found; only documentation/probe references exist. |

## 6. Critical Blockers

### P0 - Required before launch

1. **Supply launch secrets.**
   - Add `P5_API_KEY` and `TUNNEL_TOKEN` to `phase5/deploy/.env` (chmod 600).
   - The launcher now refuses to start if either is empty.
   - Do not commit `.env`.

2. **Configure Cloudflare Tunnel/DNS.**
   - `cloudflared` is installed; the tunnel token and public hostname route are still missing.
   - Create the tunnel route for `ai.berojgardegreewala.com` to `http://127.0.0.1:8090`.
   - The current public hostname does not resolve.

3. **Submit and certify the production job.**
   - No `bdw_70b_prod` job exists yet.
   - After secrets/DNS, submit `sbatch phase5/deploy/run_production.slurm`.
   - Run local and public `live_probe.py`; require `P5_LIVE_OK`.

### P1 - Production readiness

4. Validate 72B VRAM headroom, first-token latency, streaming, auth, `/metrics`, and public TLS.
5. Re-baseline SLOs from measured cluster behavior.
6. Close the 70B domain-quality gap. All five P4 adapters are 7B-shaped and cannot attach to 72B; initial 70B serving is base-only with router/RAG. Retrain 70B adapters if LoRA quality is required.
7. Complete P5.2 production Supabase migration, RLS, backups, and key rotation.
8. Complete P5.3 BDW integration, P5.4 canary/rollback gates, and P5.5 feedback loop.

### P2 - Debt and cleanup

9. Fix or bypass the CS adapter regression.
10. Expand P4 evaluation beyond 25 prompts.
11. Consolidate documentation: root `README.md` is outdated; local and cluster Phase 5 docs diverge; cluster section 17 zero-cost plan is now in GitHub via `9f7f7d9`.
12. Keep the cluster and canonical GitHub `status.md` copies synchronized under the cluster-only policy.
13. Add CI Docker build only if the Docker path is retained; zero-cost Slurm uses the venv path.
14. Monitor disk: 476G free; `venv_p5` is 6.9G and model artifacts are large.

## 7. Next Actions

- [x] Commit/push cluster source and docs; add a remote.
- [x] Push canonical updates to GitHub `HPC` (latest Phase 6 reasoning commit `86ba553`).
- [x] Copy cluster-only deployment files into local repo.
- [x] Sync local P5.1 `phase3/gateway/app.py` to the cluster.
- [x] Repair `venv_p5` NumPy/pyarrow/sentence-transformers conflicts.
- [x] Create cluster `phase5/deploy/.env` with `TP_SIZE=2` and `MAX_MODEL_LEN=8192`.
- [x] Pre-stage `cloudflared` and set `HF_HUB_OFFLINE=1`.
- [x] Make `run_production.slurm` fail on missing config or live-probe failure.
- [x] Re-run P5 tests: `97 passed, 2 skipped`.
- [x] Create and validate the Phase 6 tool-call dataset generator.
- [x] Generate 120/24 seed dataset; verify schema and deterministic hashes.
- [x] Push Phase 6 script/README to GitHub under `HPC/bdw-llm/phase6_advanced/tools`.
- [x] Add a small held-out tool-use eval and run the 7B model against it (baseline: 54.2% format rate).
- [x] Decide to fine-tune on the Phase 6 seed data and add the masked assistant-only LoRA SFT pipeline.
- [x] Launch the full Phase 6 training job and inspect `training_metadata.json` (job `185946`, 90 steps).
- [x] Evaluate the resulting adapter on the held-out 24-row tool-call set (job `185947`, 24/24).
- [x] Generate and validate the 120/24 `<think>` reasoning dataset; publish cluster `6cc0e1e` and canonical `86ba553`.
- [ ] Train and evaluate a reasoning LoRA on the 120-row seed dataset.
- [ ] Expand beyond the 24-row synthetic seed suite; add adversarial tool calls, unseen tools, and longer outputs before production claims.
- [ ] Add `P5_API_KEY` and `TUNNEL_TOKEN` to cluster `.env`.
- [ ] Configure Cloudflare DNS/tunnel for `ai.berojgardegreewala.com`.
- [ ] Submit the actual Slurm job and wait for the allocation.
- [ ] Run local and public live probes; require `P5_LIVE_OK`.
- [ ] Decide 70B LoRA retraining vs base-only launch.
- [ ] Start P5.2/P5.3 and expand P4 evaluation.

## 8. Change Log

### 2026-11-05 - Phase 6 reasoning dataset

- Added `phase6_advanced/reasoning/generate_reasoning_dataset.py` and `README.md`; deterministic, CPU-only, local Qwen tokenizer, no external APIs.
- Generated 120 train / 24 eval rows with 40 / 8 each for math, logic, and coding; each assistant target contains one `<think>` block plus a final answer.
- Math templates: inventory, discount, production, area difference. Logic: five-item ordering puzzles. Coding: 12 Python functions with 4 sample calls each.
- Token range: train `166-335` (mean `206.29`); eval `174-317` (mean `214.54`).
- Train SHA-256 `9b79d4d77ccd463ee2233ab514e1a1826b6509315485bc6393d38dc7f59209ba`; eval SHA-256 `9af52700204698c9db3e9feba32032eb48abb193b198e802c96f0c1f864b5046`.
- Verified 144 unique questions, no cross-split duplicates, arithmetic answers, all logic clue constraints, coding sample execution, think-tag shape, and byte-identical rerun hashes.
- Dataset files remain cluster-only and Git-ignored; no local project files were created.
- Cluster commit `6cc0e1e`; canonical GitHub commit `86ba553`.
- Status: dataset only; no reasoning SFT training or evaluation yet.

### 2026-11-04

- Performed full SSH audit of `/home/tutor/3ioip3lt/bdw-llm`.
- Verified Phase 1, Phase 2, and Phase 4 completion evidence.
- Verified P4 live stack, Supabase domains, `/health`, and a live VLSI `/ask` request.
- Verified P5 inventory: 72B cache, vLLM, Slurm script, live probe, missing secrets, missing `cloudflared`, unresolved public DNS.
- Recorded original cluster P5 test result: 41 failed, 56 passed, 2 skipped.
- Recorded original cluster git risk: no remote, 54 tracked files, 16,640 untracked files.
- Created this status report and synced it to the local project and Param Rudra.
- Backed up cluster source and deployment files under `/home/tutor/3ioip3lt/bdw-llm-backups/20261104-095013/`.
- Synced local P5.1 `phase3/gateway/app.py` (55,397 B) to the cluster; verified hash.
- Replaced `.gitignore` with strict exclusions; committed 169 source/deployment files in cluster commit `e03849a`.
- Added cluster `origin` (`https://github.com/amitkr26/HPC.git`); cluster push requires GitHub credentials.
- Hardened `run_production.slurm` and `live_probe.py`; added `prestage_cloudflared.sh` and `requirements-cluster.txt`.
- Staged `cloudflared 2026.10.7` on the login node.
- Created cluster `phase5/deploy/.env`, chmod 600, with TP=2, max length 8192, Supabase credentials, and empty `P5_API_KEY`/`TUNNEL_TOKEN`.
- Rebuilt `venv_p5` isolated: Python 3.11.4, NumPy 1.26.4, pyarrow 20.0.0, sentence-transformers 4.1.0, transformers 4.55.4, vLLM 0.6.6.post1; `pip check` clean.
- Re-saved the BGE model in ST 4.1-compatible format and verified anchor embeddings match at cosine `1.0`.
- Made gateway golden tests deterministic (`DomainClassifier(mode="keyword")`); cluster commit `cd61711`.
- Re-ran P5 tests: `97 passed, 2 skipped`.
- Pushed local repo changes to GitHub `main` as `5f19c28`.
- Updated this status report for the current P5-ready state.

### 2026-11-05 - Phase 6 LoRA training pipeline

- Added `phase6_advanced/tools/train_tool_calling.py`: masked assistant-only LoRA SFT, local `v2.0-bdw7b-sft`, held-out eval loss, adapter/metadata output, resumable Trainer checkpoints.
- Added `phase6_advanced/tools/train_tools.slurm`: one A100, 15-minute `training` QOS job.
- Default recipe: r=16/alpha=32, seven projection modules, 40,370,176 trainable parameters (0.5273%), 3 epochs/90 steps, lr 1e-4 cosine, batch 4, seq 768, bf16, paged AdamW 8-bit.
- Verified tokenization/labels on all 120 train and 24 eval rows; no sequence exceeds 467 tokens; assistant targets have 27-59 tokens.
- One-step A100 smoke test Job `185944` completed `P6_TRAIN_OK` in 44s; adapter and metadata serialized successfully. Smoke artifacts removed.
- Cluster commit `7164baf`; canonical GitHub commit `d081f26`.
- Full training was subsequently completed as job `185946` (see the post-SFT entry).

### 2026-11-05 - Phase 6 post-SFT evaluation

- Added `phase6_advanced/tools/evaluate_tools_trained.py` and `evaluate_tools_trained.slurm`.
- Loaded base `merged/bdw-7b-sft` plus LoRA adapter `lora_tools/p6_tool_calling/final`; used the same 24 eval rows and decoding settings as the baseline.
- Post-SFT Valid Tool Call Format Rate: **24/24 (100.0%)** vs baseline 13/24 (54.2%); delta **+11 hits / +45.8 points**.
- Missing closing tags: 9/24 -> 0/24; plain-text answers: 2/24 -> 0/24; exact semantic match: 12/24 -> 24/24.
- Evaluation job `185947` completed in 1m13s; raw output `eval/tool_trained_v2_0_bdw7b_sft_lora_p6.json`.
- Cluster commit `701cccd`; canonical GitHub commit `9620913`.
- Full training job `185946` completed at step 90; adapter SHA-256 `9ce5c70035f1824ac83d7ae83cdb6cc73302a2ddc214819353742dc53200d7ec`.

### 2026-11-05 - Phase 6 baseline evaluation

- Developed `phase6_advanced/tools/evaluate_tools_baseline.py` and `evaluate_tools_baseline.slurm`.
- Evaluated `v2.0-bdw7b-sft` on 24 held-out evaluation prompts from `data/tool_calls_eval.jsonl` using PARAM Rudra single A100 80GB GPU (Job `185940`, 14.7s generation / 52s job; local weights only).
- Valid Tool Call Format Rate: **54.2%** (13/24).
- Tag intent rate (`<tool_call>` with valid JSON body): **91.7%** (22/24).
- Key failure modes: 9 missing closing tags (37.5%) and 2 plain-text arithmetic shortcuts (8.3%).
- Saved baseline results to `phase6_advanced/tools/eval/tool_baseline_v2_0_bdw7b_sft.json`.
- Published evaluator, Slurm launcher, result, and README update to canonical GitHub at `9f7f7d9`.

### 2026-11-04 - Phase 6 seed

- Created `phase6_advanced/tools/generate_tool_dataset.py` with calculator/unit_converter tools and Qwen2.5 rendering.
- Generated 120 train / 24 eval JSONL rows; train SHA-256 `47f7bd8a2f801067cee717da000c9de69bb671a7c5dda720aa1a2c46f2265c3a`, eval SHA-256 `9a525bde07da6f5daa2843b813810c147b7c605e64b36e557c799c0cb57f905f`.
- Verified 144 unique IDs/questions, no cross-split duplicates, schema and full-trajectory shape.
- Re-ran generation to a temp directory; train/eval hashes matched exactly.
- Added `phase6_advanced/tools/README.md`; published script and README to canonical GitHub at `60319aa` (tree diff from `b25b71d` is only the two additions).
- Dataset files remain cluster-only and Git-ignored; no local project files were created.

## 9. Update and Sync Procedure

After every work session:

1. Update this file on Param Rudra with the new state and append a Change Log entry.
2. Keep the canonical GitHub copy current at `HPC/bdw-llm/status.md`.
3. Verify the cluster file and canonical remote blob have the same SHA-256.
4. Do not put secrets in this file.
5. Keep the phase table, blockers, next actions, and change log current.

Cluster file: `/home/tutor/3ioip3lt/bdw-llm/status.md`

Legacy local checkout (read-only under current policy): `C:\Users\STUDENT\Desktop\Amit\HPC\bdw-llm\status.md`

## 10. References

- `docs/PHASE5_BDW_INTEGRATION_BLUEPRINT.md` - Phase 5 architecture; cluster copy has section 17 zero-cost Slurm pivot.
- `phase5/deploy/run_production.slurm` - hardened production Slurm launcher.
- `phase5/deploy/live_probe.py` - live certification probe.
- `phase5/deploy/prestage_cloudflared.sh` - login-node tunnel binary staging.
- `phase5/deploy/requirements-cluster.txt` - vLLM-compatible P5 dependency pins.
- `phase5/deploy/.env.example` - cluster P5 environment template.
- `phase3/gateway/app.py` - P5.1 gateway with `ask_stream()`.
- `phase5/serve/tests/test_gateway_parity.py` - gateway golden-parity test; passing.
- `phase5/serve/tests/gateway_stubs.py` - deterministic keyword-mode test gateway.
- `phase6_advanced/tools/generate_tool_dataset.py` - Phase 6 function-calling dataset generator.
- `phase6_advanced/tools/README.md` - Phase 6 schema, regeneration command, baseline result, and dataset summary.
- `phase6_advanced/tools/evaluate_tools_baseline.py` - v2.0-bdw7b-sft tool-call baseline evaluator.
- `phase6_advanced/tools/evaluate_tools_baseline.slurm` - 15-minute A100 baseline job.
- `phase6_advanced/tools/evaluate_tools_trained.py` - post-SFT evaluator for the base plus P6 LoRA adapter.
- `phase6_advanced/tools/evaluate_tools_trained.slurm` - 15-minute A100 post-SFT evaluation job.
- `phase6_advanced/tools/eval/tool_trained_v2_0_bdw7b_sft_lora_p6.json` - raw 24-prompt post-SFT outputs and metrics.
- `phase6_advanced/tools/eval/tool_baseline_v2_0_bdw7b_sft.json` - raw 24-prompt baseline outputs and metrics.
- `phase6_advanced/tools/train_tool_calling.py` - masked assistant-only LoRA SFT for tool-format repair.
- `phase6_advanced/tools/train_tools.slurm` - 15-minute A100 launcher for the tool-format LoRA run.
- `phase6_advanced/reasoning/generate_reasoning_dataset.py` - deterministic math/logic/coding reasoning dataset generator.
- `phase6_advanced/reasoning/README.md` - reasoning dataset schema, regeneration command, hashes, and validation notes.
- `phase3/models/bge-small-en-v1.5` - ST 4.1-compatible BGE model used by the router.
- `logs/p4_eval_latest_v2.json` - P4 evaluation source.
- `logs/eval_results.json` - Phase 1 evaluation source.
- `merged/bdw-7b-sft-Q4_K_M.gguf` - P4 served model.
- `lora_*/final` and `export/p4_lora_*.gguf` - P4 adapters.
- `phase4/rag/` - domain indexes.
- `~/.cache/huggingface/hub/models--Qwen--Qwen2.5-72B-Instruct` - 72B weights.
- `venv_p5/` - isolated P5 Python environment.
