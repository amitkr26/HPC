# PHASE2_EVAL — ship-gate A/B: `7B Instruct zero-shot` vs `7B BDW-SFT`

**Status: GREEN** — every §7 gate passes on suite `p2-v2`. This is the P2.4
handoff writeup, produced after the P2.5 remediation retrain (blueprint errata
§15–§16). Deliverables: this doc, the A/B harness extension in
`compare_distill.py`, the merged weights `merged/bdw-7b-sft/` (cluster, 15.25
GB + md5 manifest mirrored at `docs/bdw_7b_sft_md5_manifest.txt`), and the
final adapter `lora_snap_p25/final`. No production code changes.

---

## 1. What is evaluated

| | |
|---|---|
| Base | `Qwen2.5-7B-Instruct` (local `teacher_model_7b`, bf16, no network) |
| Adapter | `lora_snap_p25/final` — LoRA r=32/α=64, 392 tensors, md5 `a9117e1dc0ed85a12f5970c473f703cd` |
| Training | `data/bdw_sft_v2.jsonl` (11,941 train / 579 val), 2 epochs = 748 steps, jobs 33490+33491, val 3.7764 → **0.4052** |
| Merged | `merged/bdw-7b-sft/` bf16 — `merge_and_unload()`, 15,247,180,206 B, 4 shards, job 33494 |

The v2 training set = v1 (11,628 rows, md5 unchanged) + 712 r2b id-copy rows
+ 180 r6 anti-over-refusal counter-examples (errata §16.1); the 579-row val
set is byte-frozen, so val-loss figures below stay comparable to P2.3.

## 2. Method (blueprint §7)

- **Suite `p2-v2`**, 30 prompts, all from *val* rows (never trained on):
  10 exact-match circular (R1), 8 class-C explanations (4 R3 + 4 R4),
  4 eligibility (R2, prompts carry ` (Ref: <row_id>)` so resolution is
  copyable — errata §16.3), 4 should-refuse (R5), 4 general-English canaries.
- **Greedy decoding both sides:** `do_sample=False`, seed 1337,
  `max_new_tokens=300`; identical prompts, identical code (`src/p2_baseline.py`),
  only the weights differ. Jobs: **33492** (zero-shot) and **33493** (SFT),
  `RESULT: P2_BASELINE_OK` each.
- **A/B assembly** runs through the extended `compare_distill.py` with the
  §7 labels: `python compare_distill.py --ab-a eval/p2_base_v2.json --ab-b
  eval/p2_sft_v2.json` → same-suite guard (pid+prompt equality), metric deltas
  and all 30 side-by-side transcripts (O.4 method), stdlib-only.
  `hit_eos` truncation bug fixed before this run (`b85ec9f`).
- **StyleRubric:** manual 1–5 side-by-side on 20 prompts (O.4 method),
  selection `em_01–05, cc_01–04, el_01–04, rf_01–03, ge_01–04` — every group
  represented; gate = no regression.

## 3. Gate scorecard

| Metric (§7) | zero-shot | **BDW-SFT** | Gate | Verdict |
|---|---|---|---|---|
| ExactMatch | 2/10 | **6/10** | improvement vs baseline | **PASS** (+4) |
| FieldFidelity prompts | 18/22 | **20/22** | ≥ baseline | **PASS** (+2) |
| FieldFidelity numbers | 5/14 | **14/17** | (sub-metric, high-90s target open) | improved ×2.8 |
| CitationResolution | 0 cited | **4/4 resolve** | improvement vs baseline | **PASS** |
| RefusalCorrect should-refuse | 2/4 | **4/4** | no regression | **PASS** |
| RefusalCorrect should-answer | 26/26 | **26/26** | no regression | **PASS** |
| GeneralEnglish | 4/4 | **4/4** | zero degradation | **PASS** |
| StyleRubric (20, 1–5) | 3.10 mean | **4.80 mean** | no regression | **PASS** |
| Val loss | — | 0.4052 @748 (P2.3: 0.3982 @692) | monotone-ish | **PASS** |

**Verdict: green — ship gate open.**

## 4. A/B metric delta (verbatim `compare_distill.py --ab` output)

```
P2.4 A/B -- 7B Instruct zero-shot  vs  7B BDW-SFT  (suite p2-v2, 30 prompts)
decoding  : {"do_sample": false, "max_new_tokens": 300, "seed": 1337} (both sides)

metric                 7B Instruct ze |     7B BDW-SFT
--------------------------------------------------------
ExactMatch                       2/10 |           6/10
EligibilityVerbatim               0/4 |            4/4
FieldFidelity prompts           18/22 |          20/22
FieldFidelity numbers            5/14 |          14/17
CitationResolution      0/0 (0 cited) |  4/4 (4 cited)
Refusal should-refuse             2/4 |            4/4
Refusal should-answer            26/26 |          26/26
GeneralEnglish                    4/4 |            4/4

RESULT: P2_AB_OK prompts=30 suite=p2-v2 a='7B Instruct zero-shot' b='7B BDW-SFT'
```

## 5. Representative transcripts (O.4 side-by-side)

**em_04 — deadline (exact match):**
- zero-shot (81 tok, dodge): *"To provide you with the correct information … I
  would need to check the most recent job listing or contact Analog Devices
  directly. … I recommend visiting the official Analog Devices careers
  website…"*
- **BDW-SFT:** *"The last date to apply for the Hardware Design & Manufacture
  Lead position at Analog Devices is **2026-10-22**."*

**cc_01 — class-C location (fidelity):**
- zero-shot: *"… I would need more specific details such as the company …
  Could you please provide me with more context?"*
- **BDW-SFT:** *"The location of the Senior FPGA Mixed Signal Engineer
  position is in India, Bangalore, RMZ."*

**el_01 — eligibility + citation (the §15.2.1 failure, now closed):**
- zero-shot: 10-line generic checklist, no verdict, **no citation**.
- **BDW-SFT:** *"According to the Analog Design Engineer – High Speed Memory
  Interfaces (m/f/d) notification from Micron Technology: B.Tech / M.Tech in
  ECE / EEE / Microelectronics with 0-5 years experience **(Ref:
  e9ec924f-a311-4352-b168-dd019456b8d0)**"* — id copied from the prompt,
  resolves 4/4 against Supabase (was 0/4 with fabricated suffixes under v1).

**rf_03 — should-refuse:**
- zero-shot: complies — 5-gemstone markdown list with "Good luck with your
  interview!"
- **BDW-SFT:** *"I can't help with astrology questions — BerojgarDegreeWala
  focuses on verified government job circulars, eligibility guidance and VLSI
  career advice … Please ask about opportunities, applications or your career
  path instead."*

**ge_02 — over-regression canary (§15.2.3, fixed):**
- v1-SFT answered with the R5 refusal script; **P2.5 SFT** now answers:
  *"Dear Host, thank you for inviting me to the meeting tomorrow. I am unable
  to attend due to a last-minute conflict … Have a great discussion!"* —
  should-answer restored to 26/26, GE to 4/4.

**em_01 — the honest miss:** expected `Competitive Hardware MNC Compensation`;
SFT answers *"₹14 - ₹38 LPA (Commensurate with Role & Level)"* — a different
field *of the same source row* (fidelity-clean), while zero-shot fabricates
China/US salary ranges (4 bad numbers). Suite expects the range-field string;
see §10.

## 6. StyleRubric — manual 1–5 on 20, side-by-side (O.4 method)

Single evaluator, style only (clarity, concision, on-task tone, structure);
content accuracy is scored by §3, not here.

| pid | zero-shot | BDW-SFT | note |
|---|---|---|---|
| em_01 | 3 | 5 | base waffles + fabricated ranges; SFT one line |
| em_02 | 3 | 5 | base generic essay; SFT direct |
| em_03 | 2 | 5 | base dodges; SFT direct (content wrong — §10) |
| em_04 | 2 | 5 | base defers to website; SFT exact one-liner |
| em_05 | 3 | 5 | base correct + boilerplate padding |
| cc_01 | 2 | 5 | base asks for context; SFT direct |
| cc_02 | 3 | 5 | base hedged redirect; SFT direct |
| cc_03 | 4 | 5 | base structured but generic + truncated; SFT verbatim criteria |
| cc_04 | 2 | 5 | base dodge; SFT direct |
| el_01 | 3 | 5 | base long checklist, no verdict; SFT answer-first + resolvable Ref |
| el_02 | 3 | 5 | ditto (base drifts into GPA talk) |
| el_03 | 3 | 5 | base invents CISSP-style certs for a hardware role |
| el_04 | 3 | 5 | base generic 7-point list; SFT verbatim |
| rf_01 | 4 | 5 | both refuse; SFT on-brand + shorter |
| rf_02 | 3 | 4 | base drafts the message (off-scope); SFT on-brand, minor blemish |
| rf_03 | 2 | 5 | base delivers the gemstone list; SFT on-brand redirect |
| ge_01 | 4 | 5 | both on-task; SFT tighter |
| ge_02 | 5 | 4 | base full formal email; SFT terser, no subject line — regression |
| ge_03 | 4 | 5 | both correct; SFT tighter + Neptune nuance |
| ge_04 | 4 | 3 | base rephrases; SFT near-verbatim copy — regression |
| **mean** | **3.10** | **4.80** | SFT ≥ base on 18/20; 2 items −1, both stay ≥3 |

**Gate: PASS** (no aggregate regression; +1.70 mean).

## 7. Val-loss curve (jobs 33490/33491)

| step | val_loss | note |
|---|---|---|
| 0 | 3.7764 | slice 1 fresh start |
| 410 | 0.4692 | slice 2 resume (USR1 save) |
| 748 | **0.4052** | final; P2.3 reference 0.3982 @692 on the same 579 rows |

Train loss 3.6779 @5 → 0.3806 @745; 1495 tok/s, peak 18.84 GiB, 2 slices
(764 s + 631 s). Metrics: `eval/p2_sft_v2_metrics.jsonl` (16,208 B).

## 8. Merged package — `merged/bdw-7b-sft/`

Job **33494** (`RESULT: P2_MERGE_OK files=15 bytes=15247180206 gb=15.25
shards=4 elapsed=204s`): `PeftModel.merge_and_unload()` on bf16, atomic
`.tmp → os.replace`, tokenizer copied, `md5_manifest.txt` in `md5sum -c`
format. In-place verification: **all 14 entries `OK` (`CHECK_RC=0`)**.

- Shards: `model-00001-of-00004` 4.6 G `a576f1593703c91156a6e6b83f9c533f`,
  `model-00002` 4.6 G `df709e6904e3345fc4ab924ad0123e3b`, `model-00003` 4.1 G
  `9defba9101eb10c1f669b1f05e56ad37`, `model-00004` 1.1 G
  `fc37edbec07dcb60e21a7c7210ffec3c`; full 14-entry list:
  `docs/bdw_7b_sft_md5_manifest.txt` (verified in place with `md5sum -c`).
- Handoff contents (§8.5): merged weights + final adapter
  `lora_snap_p25/final` + this doc + dataset stats (`bdw_sft_v2` counts,
  errata §16.1) + blueprint errata. **No production code changes.**

## 9. Evidence index

| artifact | bytes / md5 | job |
|---|---|---|
| `eval/p2_base_v2.json` | 95,609 / `91d168b29cca00bb6434590c9655d027` | 33492 |
| `eval/p2_sft_v2.json` | 75,097 / `754ec573636fe6222565cddd2fa809d1` | 33493 |
| `eval/p2_sft_v2_metrics.jsonl` | 16,208 / `cd675a3e8fdc3f12cdb7dcfb66d4a8e0` | 33490/1 |
| `docs/bdw_7b_sft_md5_manifest.txt` | 793 / (this commit) | 33494 |
| adapter `lora_snap_p25/final/adapter_model.safetensors` | 338.9 MB / `a9117e1dc0ed85a12f5970c473f703cd` | 33491 |
| merged `md5_manifest.txt` | 14 entries, `md5sum -c` all OK | 33494 |
| `data/bdw_sft_v2.jsonl` | 6,061,620 / `d1e81116d2b5ce65a2c886b1b1b6c0dd` (v1 intact `d3943b76…`) | build |

## 10. Honest limitations

1. **ExactMatch 6/10, not 10/10.** em_01/em_07: the scorer expects the
   range-field string (`Competitive Hardware MNC Compensation`) while the row
   *also* carries a numeric salary the model quotes (fidelity-clean) — a suite
   field-ambiguity, not a hallucination. em_03: SFT says "India, Bangalore,
   RMZ" where the row resolves "Bristol, UK" — a real content error that
   FieldFidelity cannot see (it only checks ≥3-digit numbers). em_10 still
   fabricates `0-2`.
2. **FieldFidelity 20/22, numbers 14/17** — fabrication shrank 9 → 3 bad
   numbers (em_10 `0-2`, cc_08 `2013`/`2011`) but is not eliminated.
3. **StyleRubric is single-evaluator** (this session), not multi-rater; two
   per-item −1s (ge_02 terser email, ge_04 near-verbatim summary) keep both
   at ≥3.
4. **Suite comparability:** v1-era columns (errata §15.1) used `p2-v1`; only
   base-v2 ↔ SFT-v2 is same-suite.
5. **Milestone numbering:** the remediation run is called *P2.5* in errata
   §15.3/§16; the §9 milestone row *P2.5* (GGUF + agreement report + handoff
   README + tag `v2.0-bdw7b-sft`) is still open, as is the quantisation
   top-1 agreement check (§8.3).
6. **No live serving under the 15-minute regime** — showcase responses are
   batch-precomputed; live VM serving is the post-Phase-2 step (§8.4).

## 11. Rollout pointers (§8)

Serve bf16 `merged/bdw-7b-sft/` gateway-side (Zone 2/3), classes C/D
first-pass with citations, frontier fallback E/F; GGUF Q4_K_M only after a
top-1 agreement spot-check on this suite. Quantisation changes outputs
(Phase 0: int8 top-1 agreement 0.719–0.766 on the 28M model).
