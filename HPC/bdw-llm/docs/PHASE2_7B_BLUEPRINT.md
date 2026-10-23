# Phase 2 Blueprint: LoRA-SFT of a 7B Model for BDW

| | |
|---|---|
| **Document** | `docs/PHASE2_7B_BLUEPRINT.md` |
| **Author** | Phase 1 (Stages A–O), tag `v1.0-research-complete` (`70f5661`) |
| **Date** | 2026-10-22 |
| **Status** | Blueprint for kickoff — no code written yet |
| **Precedents** | `BDW_INTEGRATION.md` (proposal, Stage N), `DISTILLATION.md` (Stages N–O), Stage P/Q results |
| **Audience** | BDW platform owner + engineering |

---

## 1. Phase 1 is closed; what Phase 2 is

Phase 1 is **complete and tagged**: from-scratch 28M LLM end to end —
16,384-token byte-level BPE, 200k pre-training steps (held-out ppl 52.40),
Dolly instruction tuning (27.98, `step_0003000.pt`), RAG chat, sequence-level
KD from a live Qwen2.5-7B teacher (ppl 19.28), and context-grounded
distillation (ppl 23.24 → 15.15). The Stage O A/B established the honest
verdict: **the 28M model reached its natural capacity** — loops, entity
fabrication and thin prose are parameter limits, not tuning gaps. Every claim
in `docs/` is md5/raw-byte verified against GitHub.

**Phase 2 is a different task**: supervised fine-tuning (LoRA) of an *existing*
7B/8B instruction model on **BDW's own data** (Supabase circulars +
VLSI content), on PARAM Rudra's 15-minute slices, then evaluation, merge, and
a serving handoff. Explicitly **not** in scope: training from scratch,
production-code changes, BPE retraining (§10), frontier-gateway changes.

Why this order works: Phase 1 built every *mechanic* (tokenization discipline,
wall-clock checkpointing, quality gates, A/B harnesses, offline operation) on
a model cheap enough to make mistakes with. Phase 2 reuses those mechanics on
a model that can actually hold a conversation.

---

## 2. Model selection

| | **Qwen2.5-7B-Instruct (recommended)** | Llama-3.1-8B-Instruct (fallback) |
|---|---|---|
| On disk already | **Yes** — `~/bdw-llm/teacher_model_7b/`, 15.24 GB, 14 files | No — gated repo (Meta license + HF token required) |
| Config (measured) | `qwen2`, 28 layers, `d_model` 3584, vocab 152064, 4×safetensors | ~8B, 32 layers, `d_model` 4096, vocab 128256 |
| License | Apache-2.0 (permissive, no click-through) | Llama-3.1 community license (usage gates) |
| Dual role | **Is already the teacher** for data generation (Stages N/O) | Adds a second model type to the workflow |
| Scripted history | `download_teacher.py`, `generate_*.py` all pin `TEACHER_ID = "Qwen/Qwen2.5-7B-Instruct"` | New download + template plumbing |

**Choice: Qwen2.5-7B-Instruct.** It is on disk (zero download risk on a
cluster whose compute nodes have no internet), its chat template and
tokenizer are already exercised by the Stage N/O generation scripts, and its
Apache-2.0 license needs no approval step. Reuse it *in place* as the SFT
start point; it doubles as the teacher for any additional instruction data.
Llama-3.1-8B remains the documented fallback only if Qwen fails the style
eval in §7 — budget +16 GB disk and a gated download through the login node.

**Base vs Instruct:** start from **Instruct**. Phase 2's dataset will be
1k–10k curated rows — enough to teach BDW's domain, voice and citation habit,
not enough to instil instruction-following from a raw base model. Continuing
pre-training from base on BDW text is §8.2 step-2 territory (Phase 3, gated on
evidence).

**Tokenizer policy: keep the native Qwen BPE.** Stage P measured why not to
retrain: 0.39 MB of BDW text saturated the trainer at 5,300 merges and made
general English **32% worse** for a 19% domain gain (`BDW_INTEGRATION.md`
§8.3). The ≥50 MB corpus gate stays open as an *optional* P2.D4 experiment
once the full 590+ openings with JD text are exported — separate acceptance
gate, never mixed into the main run.

---

## 3. Hardware envelope and the 15-minute slice

### 3.1 Measured SLURM constraints

| Constraint | Value |
|---|---|
| Partition / account / qos | `gpu` / `tutor` / `training` |
| Resources | `--gpus=1 --cpus-per-task=4 --time=00:15:00` (`MaxWall=15:00`, `MaxTRESPU=cpu=4, gres/gpu=1`) |
| Submit limit | `MaxSubmitJobs=1` — jobs are **serial**; automation must chain, not fan out |
| Node (measured) | `rdgpu01`, A100 80 GB PCIe, CUDA 12.3, torch 2.5.1+cu121 |
| Network | **Login node: internet. Compute: no internet, no DNS** (wheel pre-fetch is mandatory) |
| Disk | `/home` 25 T total, **1.5 T free (94%)** at `/home/tutor/3ioip3lt` — budget ≈40 GB for Phase 2 |

### 3.2 Per-slice budget (measured where marked, estimated where not)

| Phase of a slice | Time | Basis |
|---|---|---|
| `sbatch` → job RUNNING | 25–35 s | measured (Phase 1, `[0]` marker at ~30 s) |
| venv activate + imports | 5–10 s | estimate |
| 7B bf16 load + tokenizer + LoRA attach | 20–40 s | load measured 7.3 s; setup estimated |
| **Training window** | **≈ 700 s** | remainder of 900 s wall |
| Adapter + optimizer save | 5–15 s | estimate (≈110 M LoRA params ≈ 0.45 GB adapter + ≈1 GB optimizer state) |
| **Usable train time / slice** | **≈ 700 s** | |

**Save protocol (the Phase 1 lesson, hardened).** `finetune.py` already saves
on wall-clock, on SIGTERM, and auto-resumes. Phase 2 adds the standard SLURM
pre-kill hook so the hard wall kill becomes a *safety net*, not the save
mechanism:

```bash
#SBATCH --signal=B:USR1@60        # USR1 60 s before the wall kill
trap 'kill -USR1 "$child"' USR1   # batch script forwards to the python process
```

Python sets a stop flag on USR1 → Trainer saves → clean `COMPLETED` exit →
driver reads the RESULT line and resubmits. All saves are **atomic**: write to
`lora_out.tmp/` then `os.replace` onto the final directory, so a kill at the
worst instant never leaves a half-written checkpoint as the newest resume
point.

**Throughput — to be measured, not assumed.** Training costs `6×N` FLOPs per
token ≈ 4.6e10 for 7.6 B params; an A100 at a realistic 100–200 effective
TFLOPS with gradient checkpointing gives an **estimate of 1,500–3,000 tok/s**
→ **1.0–2.1 M tokens per slice**. P2.2 runs a 60-second profiling slice that
prints measured tok/s, and the slice plan in §9 is recomputed from that
number before any long run starts. Formula:

```
slices = ceil(dataset_tokens × epochs ÷ measured_tokens_per_slice) + 1 safety
```

### 3.3 Driver and the resume trap

The proven Phase 1 driver pattern (upload → compile → `sbatch` → 30 s poll →
grep `RESULT:` → auto-resume loop) is reused as `p2_driver.py`. Two rules
carried over verbatim:

1. **`MaxSubmitJobs=1` ⇒ strictly serial submission.** One job in flight, ever.
2. **The auto-resume trap (job 32364 trained 0 steps):** `finetune.py:279`
   auto-loads the newest checkpoint; if it was already past `total_steps` the
   job exits immediately with no `[resume]` log line. Before any *fresh* run,
   the driver **archives** `lora_out/` → `lora_out_alt/<tag>/` and asserts the
   directory is empty; a resumed run must print `[resume] from step N` or the
   driver kills and reports.

---

## 4. Training stack

### 4.1 Environment (login node has internet; compute does not)

```bash
python -m venv --system-site-packages ~/bdw-llm/venv_p2   # inherits cluster torch 2.5.1+cu121
~/bdw-llm/venv_p2/bin/pip install "trl==<pin>" "peft==<pin>" "transformers==<pin>" \
    "accelerate==<pin>" "datasets==<pin>" "safetensors==<pin>"   # pin exact versions
~/bdw-llm/venv_p2/bin/pip download -r requirements_p2.txt -d wheels/   # offline cache
# compute jobs: pip install --no-index --find-links wheels/  (once) → no network needed
```

`--system-site-packages` is deliberate: it inherits the cluster's
torch 2.5.1+cu121 / CUDA 12.3 instead of reinstalling ~2.5 GB. **`accelerate`
is missing on the cluster** (Phase 1 finding) — it must be installed into
`venv_p2`, because HF `Trainer`/`SFTTrainer` requires it. Verification is a
dedicated smoke job (`smoke_p2.slurm`): import all libs + print versions,
`torch.cuda.get_device_name(0)`, load the 7B offline, run 3 optimizer steps,
save an adapter, reload it, exit `RESULT: P2_SMOKE_OK`.

### 4.2 Reference stack vs accelerator

| Layer | Choice | Notes |
|---|---|---|
| **Reference (default)** | HF `transformers` + **`trl` `SFTTrainer`** + **`peft` LoRA** + `accelerate` | Standard, well-documented resume via `resume_from_checkpoint`; adapter-only saves |
| Precision | **bf16 LoRA** (full precision base weights) | 15.2 GB weights + ≈6–10 GB activations (grad ckpt) + ≈1 GB optimizer ≈ **25–30 GB of 80 GB** — no quantisation noise in training |
| Fallback | **QLoRA** (bitsandbytes NF4, double-quant, `paged_adamw_8bit`) | Only if P2.2 profiling pushes VRAM (longer seq 2048, bigger batch); weights drop to ≈5.5 GB; adds a bf16↔NF4 dequant tax (~10–20% slower — verify with the profiling slice) |
| Optional accelerator | **Unsloth** (`FastLanguageModel`) | Advertises ≈2× speed / 60–80% VRAM. Adopt **only if** the measured slice math fails the dataset budget; adoption gate = 1-slice equivalence check (same rows → same loss trajectory + same eval suite) against the HF reference. Risk: wheel/torch pin friction |
| Metrics | `report_to=[]` + `logs/finetune_metrics.jsonl` (stage tag **`P2_SFT`**) | Compute has no internet — wandb/HF-hub reporting would fail; JSONL keeps the Phase 1 convention |

### 4.3 Why bf16-LoRA-first (the decision, in one line)

80 GB buys headroom for **sequence length and batch size** — the two things
that determine whether one 15-minute slice holds enough tokens — so train in
bf16 and spend the savings there; reach for QLoRA only if the measured budget
says otherwise.

---

## 5. Data pipeline: Supabase → SFT rows

### 5.1 Access and secrets

* Credentials live in `~/bdw-llm/secrets/supabase.env` (chmod 600) as
  `SUPABASE_URL` / `SUPABASE_SERVICE_KEY`; scripts `source` it. **Never in the
  repo**: `.env*` gitignored, no `export` lines in committed shell scripts,
  redacted URLs (`https://***.supabase.co`) in logs.
* Pre-commit secret scan: `git grep -iE "eyJ[A-Za-z0-9_-]{20,}"` (Supabase
  JWTs start `eyJ`) must return nothing before every push.
* Service-role key (bypasses RLS, read-only usage here); anon key only sees
  public tables.

### 5.2 D0 — schema discovery (first task, login node)

```
GET $SUPABASE_URL/rest/v1/          # PostgREST root returns an OpenAPI spec:
                                    # every exposed table, column, type
```

Snapshot the raw spec to `docs/supabase_schema_2026-10-22.json` plus a human
table (table → row estimate → which §4.2 class it feeds) in this document's
errata. If the spec endpoint is disabled, probe the expected names
(`opportunities`, `circulars`, `organizations`, `resources`, `faq`, `news`)
with `?select=*&limit=1`. Column names are **never hardcoded in generators**:
a mapping file `src/bdw_column_map.json` (`{"post": ["post","designation",…]}`)
decouples recipes from drift.

### 5.3 Extraction (login node — the only node with internet)

* REST paging via PostgREST `Range` headers (`rows=0-999`, advancing until
  short page), `select=*`, service-role key.
* Resumable per table: `data/raw/bdw_{table}.jsonl` keyed by primary id —
  already-seen ids skipped (Phase 1 resume pattern); rate-limit friendly
  (sleep 0.2 s/page).
* Manifest: row counts + md5 per table → `data/raw/bdw_manifest.json`.
* Volume (estimate): 590+ openings with full JDs, DRDO/ISRO/CSIR circulars,
  160+ ATS platforms, news archive, resources/FAQ — plausibly tens of MB raw.
  **Instruction rows: est. 4–10 k** after recipes below; recalibrated at D0.

### 5.4 Recipe table (BDW rows → SFT pairs)

Every recipe targets the proposal's §4.2 classes; A/B stay deterministic
(no generation), so the model trains on **C (grounded explain), D
(eligibility), G (refusal)** — the classes where prose is the product.

| # | Class | Recipe | Generator | Gates |
|---|---|---|---|---|
| R1 | B/D numbers | Templated Q from fields ("last date?", "stipend?", "post at org?") + **verbatim** field as A | deterministic, no model | answer substring ∈ source row (machine check) → doubles as the exact-match eval set |
| R2 | D | "Am I eligible with X?" → restatement of the row's eligibility text + `Ref: <id>` | deterministic template | verbatim eligibility substring + citation id present |
| R3 | C | Row context → teacher QA (dates/roles/duties), then **expand** short answers and **paraphrase** — Stage O pipeline reused unchanged (`generate_grounded_qa.py` → `expand_grounded_qa.py` → `paraphrase_grounded_qa.py`, same offline teacher) | teacher (local 7B) | Stage O's six gates + ENDSENT + **field-fidelity**: every date/number in the answer must regex-match the source row |
| R4 | C VLSI | Reuse `data/grounded_qa_aug.jsonl` (**3,140 rows, 1,959,235 B** — measured) + BDW `resources/` pages through the same R3 pipeline | teacher | as R3 |
| R5 | G | ≈200 synthetic out-of-scope refusals in BDW's brand voice ("Evidence-Gated Verification") | hand-written + teacher polish | refusal marker required; min/max length; no meta-text |

**Format:** native Qwen chat template via `tokenizer.apply_chat_template` (TRL
formatting func) — no custom special tokens, no BPE work. `max_seq_length`
1024; rows >1024 dropped **with per-reason counts logged** (long circulars
truncate context-side, never answer-side). Packing starts OFF (clean per-row
loss comparability); switch ON only if measured slice math is short.

**Splits (Stage I discipline):** 95/5 train/val, **row-id disjoint**,
stratified by recipe + source table; the R1 exact-match eval set is held out
*entirely* (never trained on). Zero id/URL overlap between splits.

**Gates — Phase 1's six + two new**, every drop counted by reason into
`data/bdw_sft_stats.json`: min length, ENDSENT punctuation, refusal patterns,
`Human:`/`Assistant:` leak, meta-refusal, duplicate-qid md5 → plus
**field-fidelity** (R1–R3) and **citation-id resolution** (R2, checked with
Stage Q's `citation_verifier.py`, commit `a9f91be`).

---

## 6. Training plan

| Knob | Value | Rationale |
|---|---|---|
| LoRA | r=32, alpha=64, dropout 0.05, targets `q,k,v,o,gate,up,down` (all 7 linears) | ≈110 M trainable (printed at runtime); full-attention coverage on 80 GB |
| Batch | per-device 4 × grad-accum 4 × seq 1024 ≈ 16.4 k tok/step | fits the measured VRAM with grad ckpt; bump after P2.2 profile |
| LR / sched | 1e-4 cosine, warmup 3% | standard LoRA range; watch for the O.4 lesson — **more epochs never fix data quality** |
| Epochs | 2, early-stop watch on val loss | stop at plateau; do not chase train loss |
| Precision | bf16, tf32, grad checkpointing | §4.3 |
| Optimiser | `paged_adamw_8bit` (bnb) else `adamw_torch` | ≈1 GB state either way |
| Saves | mid-slice wall-clock save + USR1 save + keep-last-2 trainer ckpts + adapter snapshot per slice into `lora_snap/step_*/` (keep 3) | ≈5 GB disk for checkpoints |
| Resume | `resume_from_checkpoint` auto + §3.3 archive discipline | job 32364 lesson |
| Logging | JSONL, tag `P2_SFT`: step, loss, lr, tok/s, wall, job id; val eval each slice (64 batches) | no-wandb convention |

Run protocol: **P2.2 profiling slice first** (measured tok/s + VRAM watermark
via `torch.cuda.max_memory_allocated`) → recompute slice plan → **P2.3 driver
loop** resubmits serially until epochs complete or val loss plateaus.

---

## 7. Evaluation

**Baseline before training** (P2.2): a frozen 30-prompt suite, greedy
(temp 0, fixed seed), saved as `eval/p2_baseline.json` — 10 exact-match
circular, 8 class-C explanations, 4 eligibility, 4 should-refuse, 4
general-English regression. The *same* suite runs after training; success
criteria are **set after the baseline is read**, not promised up front.

| Metric | How | Gate |
|---|---|---|
| ExactMatch | regex date/stipend/org/post vs R1 ground truth | improvement vs baseline |
| FieldFidelity | every date/number in answers ⊆ source row | ≥ baseline, target high-90s |
| CitationResolution | Stage Q `citation_verifier.py` on cited ids | improvement vs baseline |
| RefusalCorrect | should-refuse / should-answer sets | no regression |
| StyleRubric | manual 1–5 on 20, side-by-side (O.4 method) | no regression |
| GeneralEnglish | 20-prompt sanity vs baseline | **zero degradation** (Stage P lesson: never silently trade the majority class) |
| Val loss | per-slice curve | monotone-ish, early-stop signal |

A/B runs through the extended `compare_distill.py` harness (labels: `7B
Instruct zero-shot` vs `7B BDW-SFT`) → `docs/PHASE2_EVAL.md` with
representative transcripts. **Known bug to fix while in there:** the latent
`hit_eos` truncation bug in `compare_distill.py` / `chat_with_rag.ask` (noted
in Stage O) skews truncation reporting — small, in-scope fix for P2.4.

---

## 8. Deliverables and rollout

1. **Merge** (one GPU slice): `model.merge_and_unload()` →
   `merged/bdw-7b-sft/` bf16 ≈15.2 GB + md5 manifest (Phase 1 discipline).
2. **Serving placement** (proposal §5): the 7B lives **gateway-side in Zone
   2/3**, never inside the Vercel app (§5.1); Zone 3's no-egress rule is fine
   — weights are local, Supabase is reachable. Classes A/B/D-numeric keep
   their deterministic handlers; the SFT model takes class C/D first-pass with
   citations, frontier stays the fallback (classes E/F).
3. **Quantisation — measured caution:** Phase 0 showed quantisation changes
   output tokens (int8 → top-1 agreement 0.719–0.766 on the 28M model). GGUF
   Q4_K_M (≈4.4 GB, est) is the CPU-pilot candidate, but **only after a
   top-1 agreement spot-check bf16-vs-Q4 on the eval suite**; if agreement is
   poor, serve bf16 on a small GPU VM instead.
4. **Demo under the 15-minute regime:** no interactive serving on the cluster.
   Batch-precompute the eval suite + a curated showcase set (`bdw_infer.py`,
   left-pad batched generation from Stage O) as static JSON for the frontend;
   live serving is the post-Phase-2 VM step.
5. **Handoff package:** merged weights + final adapter + `PHASE2_EVAL.md` +
   dataset stats + this blueprint's errata. **No production code changes.**

---

## 9. Milestones

| ID | Deliverable | Acceptance |
|---|---|---|
| **P2.0** | `venv_p2` + pinned `requirements_p2.txt` + `wheels/` + `smoke_p2.slurm` | `RESULT: P2_SMOKE_OK` (imports, offline 7B load, 3 steps, adapter save/reload) |
| **P2.1** | schema snapshot + extraction + `bdw_sft.jsonl` (recipes R1–R5) + `bdw_sft_stats.json` | all gates pass; row/token counts published; manifest md5s recorded |
| **P2.2** | `eval/p2_baseline.json` + profiling slice (measured tok/s, VRAM) | slice plan recomputed in this doc's errata from measured numbers |
| **P2.3** | driver loop → final adapter; `P2_SFT` metrics JSONL + val-loss curve | epochs complete or val plateau; zero 0-step jobs (resume trap guard proves itself) |
| **P2.4** | `PHASE2_EVAL.md` (A/B + all metrics) + merged `bdw-7b-sft/` | ship gate per §7; `hit_eos` bug fixed; byte-verified |
| **P2.5** | GGUF + agreement report + handoff README | agreement number recorded; serving placement confirmed with owner; tag `v2.0-bdw7b-sft` |

Working estimate (pending P2.2): ≈5 M SFT tokens × 2 epochs → **4–7 slices
≈ 1.5–2 h wall** — comfortably inside the Phase 1 pattern of chained 15-minute
jobs.

---

## 10. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Wall kill mid-save | `USR1@60` pre-kill save + atomic tmp→rename; hard kill is the safety net |
| OOM | grad ckpt → shrink batch/seq → QLoRA fallback (all pre-built configs) |
| 0-step resume trap | driver archives + asserts empty dir on fresh runs; requires `[resume]` line |
| Data too small / thin | teacher augment loop (R3 expand+paraphrase, proven in O.3a); honest plateau → report, don't pad epochs |
| Supabase schema drift | OpenAPI snapshot + `bdw_column_map.json`; generators never hardcode columns |
| Secret leak | env-file-only keys, redacted logs, `eyJ` pre-commit scan |
| `/home` at 94% | ≈40 GB budget (wheels ~3 GB, ckpts ~5 GB, merged ~15 GB); prune `*_alt` ckpts after P2.4 |
| Gated Llama download | Qwen primary; Llama is a documented fallback, not a dependency |
| Unsloth divergence | 1-slice equivalence gate before adoption |
| Quant changes outputs | agreement spot-check before serving (Phase 0 lesson) |
| Demo vs 15-min wall | precomputed batch answers; live serving is a post-Phase-2 step |
| Licensing | Qwen Apache-2.0 ✓; BDW's own DB data ✓; Stage O Wikipedia pairs keep CC BY-SA attribution note |

---

## 11. Discipline (unchanged from Phase 1)

One staged commit per milestone (`git add` scoped paths → `-F` message file →
push → **raw GitHub byte-verify** of every file's md5), table/whitespace lint
before commit, `git status` clean between milestones, version tags preserved
(`v1.0-research-complete` must survive all Phase 2 history). Estimates are
labelled estimates; every number promoted to "measured" is read back from
live cluster output.

---

## 12. Errata — measured results (P2.1, 2026-10-23)

`RESULT: P2_SFT_BUILD_OK kept=11628 domain=11436 refusal=192`

| Metric | Measured |
|---|---|
| Schema snapshot | Supabase OpenAPI = **70 tables**; 13 content tables extracted (2,949 rows) via `limit`/`offset` paging — `Range:` headers proved stale on the cluster (`Content-Range` stuck at `0-999/1122`) |
| R1 field QA | made 5,369 → **kept 4,023** |
| R2 eligibility restatement | made 835 → **kept 761** |
| R3 teacher grounded QA | 1,498 deduped contexts (10 tables, 1.22 M chars) + 44 BDW pages → 3 GPU slices (jobs 32641/32642/32645, 660 s wall each, resume-by-doc-id) → 4,485 pairs → **kept 3,512** |
| R4 VLSI augment | **kept 3,140** (Phase 1 `grounded_qa_aug.jsonl`) |
| R5 refusals | made 192 (32 topics × 6 Q-variants × 3 A-variants) → **kept 192** |
| Gates rejected | dup 1,954 · field_fidelity 171 · number_fidelity 268 (**439** fabricated / in-fidelity candidates) |
| Splits | train **11,049** / val **579** (5 %) |
| Tokens (Qwen chat template, ≤1024) | min 44 · med 77 · max 229 · **sum 950,567** |
| Output | `data/bdw_sft.jsonl` 5,525,456 B, md5 `d3943b76a7703f4ec5567159aee9097c` |

Scope correction (found by reviewing R1 phrasing): recipe templates assume job
rows, so R1/R2 run only over `JOB_TABLES = {opportunities, jobs,
job_occurrences}`; news/learning/content tables feed R3 teacher contexts via
`bdw_make_contexts.py` instead. Field-fidelity was likewise fixed from a
whole-answer substring test (false-flagged every templated sentence) to
numeric fidelity — dates/amounts in answers must exist verbatim in the row.

Slice estimate unchanged: ≈0.95 M SFT tokens stays inside the 4–7 slice band;
P2.2 profiling decides the final number.

---

## 13. Errata — P2.2 measured results (2026-10-23)

**Deliverables:** `eval/p2_baseline.json` (suite `p2-v1`, 30 prompts,
95,660 B) + `eval/p2_profile.json`; jobs 32652 (baseline) / 32658 (profile).

### 13.1 Baseline — base Qwen2.5-7B-Instruct, greedy, seed 1337 (137 s)

| Metric | Baseline | Notes |
|---|---|---|
| ExactMatch (10) | **2/10** | zero-shot model guesses orgs/dates; strict normalized substring vs source-row ground truth |
| EligibilityVerbatim (4) | **0/4** | never restates the circular's own eligibility text |
| FieldFidelity (22 domain) | **17/22 prompts · 2/13 numbers** | passes come from answers that cite *no* numbers; of the 13 concrete numbers emitted, 2 exist in the source row |
| CitationResolution | **0 cites** | base model never emits `(Ref: id)` |
| RefusalCorrect | should-refuse **2/4** · should-answer **26/26** | answers the astrology/gemstone asks substantively instead of declining; never refuses on-domain |
| GeneralEnglish (4) | **4/4 on-task** | zero-degradation reference for P2.4 |

These are the gates post-training must beat (blueprint §7: criteria set after
the baseline is read). The suite is val-disjoint — never trained on.

### 13.2 Profiling slice — job 32661, `RESULT: P2_PROFILE_OK`

Config as §6 (LoRA r=32/α=64, 7 targets, 4×4×1024, bf16+tf32+grad ckpt,
paged_adamw_8bit): **677 steps in 793 s** before the scheduler's USR1.

| Metric | Measured |
|---|---|
| Throughput | **0.854 steps/s · 13.66 rows/s · 1,115 useful tok/s** (81.6 tok/row) |
| VRAM | **peak alloc 16.60 GiB · reserved 26.49 GiB** of 80 GiB — large headroom |
| Loss | 3.878 (step 5) → **0.821** (step 675) — ≈1 epoch already moved it |
| Wall-clock save | step 254 snapshot: 338.9 MB, 1.14 s, 392 tensors, r=32, atomic rename OK (continued training) |
| USR1 save+kill | `[signal] 10 received` → step 677 snapshot in 1.09 s → `RESULT` → exit **rc=0**, no SIGKILL, no data loss |
| Atomicity | save to `.tmp` → verify adapter_config r + 392 safetensors tensors → `os.rename` |

Two bugs found and fixed en route (both committed): the trainer callback must
subclass `TrainerCallback` (job 32653), and bash's `wait` returns
`128+signo` the instant a trap fires — without a re-wait loop the script exited
mid-save and Slurm tore python down (job 32654); `p2_profile.slurm` now loops
on `kill -0`.

### 13.3 Recomputed slice plan (supersedes §9 estimate)

- 1 epoch = 11,049 rows ÷ 13.656 rows/s ≈ **809 s**; usable train window per
  slice = **793 s** (measured, USR1@60 s) ⇒ 2 epochs = 1,618 s
  → **3 slices ≈ 45 min wall** for 2 epochs + val eval + full ckpt saves
  (was: 4–7 slices). One epoch in reserve if val plateaus later.
- P2.3 must set `max_steps = ceil(2 × 11049 / 16) = 1382` so the cosine
  schedule reaches 1e-4 and decays (the profile's `max_steps=100000` only
  reached 2.2e-5 — fine for profiling, wrong for training).
- VRAM headroom allows `per_device_train_batch_size` 4→8 (32 rows/step,
  ≈405 s/epoch, **2 slices**); P2.3 starts at 4 (conservative) and may bump
  after the first full slice confirms the watermark.
- Loss at 0.82 after one slice: do **not** chase train loss (O.4 lesson) —
  val loss per slice decides early stop.
