# BDW-7B-SFT — handoff README (P2.5)

**Status: Phase 2 COMPLETE.** This file is the §9 milestone *P2.5 handoff
README*; it ships under tag **`v2.0-bdw7b-sft`**. Every number below is
reproducible from the evidence chain: `PHASE2_7B_BLUEPRINT.md` errata §12–§17
→ `PHASE2_EVAL.md` (ship gate) → `eval/p2_agreement.json` (this milestone).

**One-line recommendation:** serve **`bdw-7b-sft-Q4_K_M.gguf`** (agreement
rate **0.9682 ≥ 0.90 → `PASS_SERVE_Q4`**, job 33498); keep the merged bf16
weights as the fidelity fallback. **Owner sign-off recorded (2026-10-27):**
serving placement confirmed — Zone 3, offline llama.cpp, Q4_K_M serve target,
merged bf16 retained for fidelity-critical workloads (§8.3 rule). Phase 2 is
closed; no open items.

---

## 1. What the model is

Qwen2.5-7B-Instruct + LoRA (r=32, α=64, effective batch 32) trained 748/748
steps (2 epochs) on `bdw_sft_v2` — 11,941 train / 579 val rows (v1 11,049/579
+ 712 r2b id-copy + 180 r6 anti-over-refusal; errata §16.1), then merged to
standalone bf16 weights. Val loss 0.4052 @748. P2.3 predecessor (v1 data,
val 0.3982 @692) kept untouched as history.

## 2. Artefact inventory (cluster: `/home/tutor/3ioip3lt/bdw-llm/`)

| Artefact | Where | Size / md5 |
|---|---|---|
| **Merged weights (serve/fallback)** | `merged/bdw-7b-sft/` | ~15.25 GB, 4 shards + 10 files — `docs/bdw_7b_sft_md5_manifest.txt` (14 entries, `md5sum -c` green) |
| **Q4_K_M GGUF (serve target)** | `merged/bdw-7b-sft-Q4_K_M.gguf` | 4,683,073,696 B, **4.91 BPW**, `c681fafe042ca8277fc08c526cc6de8b` |
| f16 GGUF (quantise source) | `merged/bdw-7b-sft-f16.gguf` | 15,237,853,344 B, `f2dfcb4de60e6e036c86bc6c16bca02c` |
| GGUF md5 mirror | cluster `merged/gguf_md5.txt` = `docs/bdw_gguf_md5_manifest.txt` | 2 lines |
| Final SFT adapter (v2 data) | `lora_snap_p25/final/` | 338.9 MB; `adapter_model.safetensors` `a9117e1dc0ed85a12f5970c473f703cd` |
| SFT train data v2 / v1 | `data/bdw_sft_v2.jsonl` / `data/bdw_sft.jsonl` | 6,061,620 B `d1e81116…` / `d3943b76a7703f4ec5567159aee9097c` (v1 unchanged) |
| Ship-gate evidence | `eval/p2_sft_v2.json` (75,097 B, `754ec573…`), `eval/p2_base_v2.json`, `eval/p2_sft_v2_metrics.jsonl` | gates, transcripts, loss curve |
| Agreement evidence (this milestone) | `eval/p2_agreement.json` | 3,786 B, `1da97da336165267fa1a739c9d4f4c78` |
| Loss curves / metrics | `eval/p2_sft_v2_metrics.jsonl` | 16,208 B |

Repo mirrors the small artefacts; the 15 GB weights and GGUFs stay on-cluster
(`/home`, 1.5 TB free, 95% used — mind quota before any copy).

## 3. Ship gate (suite p2-v2, job 33493 vs base 33492 — `PHASE2_EVAL.md` §3)

| Metric | zero-shot | **BDW-SFT** | Verdict |
|---|---|---|---|
| ExactMatch | 2/10 | **6/10** | PASS (+4) |
| EligibilityVerbatim | 0/4 | **4/4** | PASS |
| FieldFidelity prompts | 18/22 | **20/22** | PASS (≥ base) |
| FieldFidelity numbers | 5/14 | **14/17** | improved ×2.8 |
| CitationResolution | 0 cited | **4/4 resolve** | PASS |
| Refusal should-refuse | 2/4 | **4/4** | PASS |
| Refusal should-answer | 26/26 | **26/26** | PASS |
| GeneralEnglish | 4/4 | **4/4** | PASS |
| StyleRubric (20 prompts, 1–5) | 3.10 | **4.80** | PASS |

**Verdict: green — ship gate open** (errata §16.4; A/B output verbatim in
`PHASE2_EVAL.md` §4).

## 4. Top-1 agreement: bf16 vs Q4_K_M (job 33498, errata §17.3)

- **Method** (blueprint §8.3, Phase-0 metric re-pointed): teacher-forced —
  merged-bf16 greedy trajectories over the frozen 30-prompt suite; custom
  `tools/top1agree.cpp` (linked against llama.cpp `d854d98`) gives Q4_K_M's
  argmax at every answer position under the same prefix; one `llama_decode`
  per prompt. Not a decode-path artefact.
- **Thresholds (pre-declared):** ≥0.90 PASS → Q4_K_M safe; ≥0.85 MARGINAL →
  prefer bf16; <0.85 POOR → serve bf16 (quant off the table).
- **Result: 1,219/1,259 positions agree → rate 0.9682**, 17/30 prompts have
  *identical* trajectories, 0 decode errors, elapsed 207 s →
  **verdict `PASS_SERVE_Q4`**.
- **Merge sanity in the same pass:** merged-bf16 re-scored with the §16.4
  gate code reproduces the scorecard *exactly* (EM 6/10, elig 4/4, cites 4/4,
  fidelity 20/22, refuse 4/4 + 26/26, GE 4/4); outputs string-identical to
  base+adapter on **24/30** prompts (the 6 differ only in wording after a
  later divergence point; all gates equal).
- Worst groups are the long-explanation/GE prompts where a mid-answer flip
  changes wording but not factuality (`ge_03` 51/60, `cc_08` 20/26); all
  rf/refusal prompts agree 100% (safety behaviour preserved under quant).

## 5. How to run

```bash
# llama.cpp server (Q4_K_M; build llama-server separately — our pinned build
# has llama-quantize + top1agree only, see scripts/p2_gguf_build.slurm and
# flip -DLLAMA_BUILD_SERVER=ON):
./llama-server -m merged/bdw-7b-sft-Q4_K_M.gguf -c 4096 -t 4 --port 8080

# transformers, merged bf16 (local_files_only on the cluster):
python -c "from transformers import AutoModelForCausalLM, AutoTokenizer; \
  m=AutoModelForCausalLM.from_pretrained('merged/bdw-7b-sft', \
  torch_dtype='bfloat16', local_files_only=True); \
  t=AutoTokenizer.from_pretrained('merged/bdw-7b-sft', local_files_only=True)"

# re-run the agreement report (resumable; --force regenerates trajectories):
source venv_p2/bin/activate && sbatch scripts/p2_agreement.slurm
#   expect: RESULT: P2_AGREEMENT_OK prompts=30 positions=1259 rate=0.9682 …

# re-run the full gate suite (eval recipe: PHASE2_EVAL.md §2)
# re-export / re-quantise (idempotent, `test -s` guards):
sbatch scripts/p2_gguf_convert.slurm   # expect: RESULT: P2_GGUF_QUANT_OK …
```

All four P2.5 scripts (`p2_gguf_build|convert`, `p2_agreement.slurm`,
`src/p2_agreement.py`) + `tools/top1agree.cpp` are committed; the two `RESULT`
lines above are the machine-checkable contract.

## 6. Provenance & environment quirks (errata §17.1)

- Jobs: 33490/33491 retrain → 33492/33493 evals → 33494 merge →
  **33497 quant (5 m 19 s)** → **33498 agreement (3 m 29 s)**.
  33495/33496 were toolchain probes (failed as expected).
- **Compute nodes cannot compile C/C++** (`/usr/include/stdint.h` absent).
  The llama.cpp build therefore ran on the *login* node, 126 s at `-j4`,
  explicit `gcc-12.3` toolchain + `-DGGML_NATIVE=OFF` (runtime dispatch keeps
  the best kernels; portable across nodes).
- **Site egress outage this session** (no DNS/direct route; Phase 0 §6 had it
  up): llama.cpp `d854d98` (0.7.0-dev) + cmake 3.31.6 wheel fetched on the
  workstation and pushed over SFTP; everything else was offline/venv-based.
- llama.cpp provenance: commit `d854d98bae598388ecea1ed84396587e5edc326d`,
  extracted under `llama_cpp/`, local patch = the `top1agree` CMake target
  (documented in errata §17.3; source committed at `tools/top1agree.cpp`).

## 7. Honest limitations

1. ExactMatch 6/10 — 4 circular prompts still paraphrase instead of copying;
   fidelity numbers 14/17 (3 numeric slips). Do not claim “resolved”.
2. Val loss 0.4052 sits +0.007 vs P2.3 on the *same* 579 rows — expected
   (id-heavy r2b targets); gates, not val, are the arbiter (errata §16.2).
3. Agreement is teacher-forced on CPU forwards; decode-path runs can diverge
   slightly earlier than 0.9682 suggests — re-check with `top1agree` after any
   llama.cpp upgrade (commit pinned above).
4. Merged vs base+adapter is 24/30 string-equal (gates identical) — bf16
   merge is numerically, not bit-, equivalent to adapter inference.
5. Serving binaries for `llama-server` are not prebuilt (wall-time budget);
   recipe in §5.

## 8. Chain of custody

`v1.0-research-complete` (70f5661) → P2.0–P2.4 + remediation + ship gate
(`59647bd`, `240c87a`, `b237af9`, `2553c0f`, `ab6f3e2`, `ca8c121`,
`b85ec9f`, `85bac62`, `ab4120f`) → **P2.5 = this document** → tag
`v2.0-bdw7b-sft`. Every commit pushed and byte-verified against raw GitHub;
no secrets in-tree (the blueprint §11 scans — Supabase JWT prefix, private-key
blocks, session password — all green before each push).
