# Sequence-Level Knowledge Distillation — Stages N.1–N.3

**Executed:** 2026-10-22 10:20–11:09 IST
**Where:** login node `login02` (teacher download + tokenization), compute node `rdgpu01` (A100 80GB) for generation and distillation
**Scripts:** `src/download_teacher.py`, `src/generate_teacher_data.py`, `src/prep_distilled_data.py`, `src/finetune.py`, `scripts/run_teacher.slurm`, `scripts/distill_student.slurm`
**Outputs:** `~/bdw-llm/data/distilled_teacher_data.jsonl`, `~/bdw-llm/data/distilled_tokens/`, `~/bdw-llm/checkpoints_distilled/`

**Naming:** the operator calls this workstream *Stage N*; the repo's own
Stage N is the BDW proposal (`docs/BDW_INTEGRATION.md`). The scripts are
labelled N.1 (teacher), N.2 (generation), N.3a/N.3b (tokenize + fine-tune) to
match the workstream, and both are referred to explicitly below.

Distils the live **Qwen2.5-7B-Instruct** teacher into the 27.8 M student by
generating teacher answers as text, re-tokenizing them with our 16 K BPE, and
fine-tuning the Stage L checkpoint on them with the exact Stage L machinery
(auto-resume, 5-minute wall checkpoint, SIGTERM save).

---

## 1. Why sequence-level KD, not KL on logits

| | student | teacher |
|---|---|---|
| vocab | 16,384 (Stage D BPE) | 151,643 (Qwen BPE) |
| tokenizer | byte-level 16 K, pad=0/bos=1/eos=2 | Qwen3-style 151 K |

Logit-level KL requires both models to share a target vocabulary. They do not,
and there is no principled projection between a 16 K and a 151 K vocabulary.
Sequence-level KD sidesteps this: the teacher contributes *sequences* in
plain text, which are then re-tokenized by the student's own tokenizer — the
only interface both models share. The student is therefore trained with
ordinary cross-entropy on teacher-generated targets, conditioned on the Stage K
prompt format.

The starting weights are the **Stage L instruction checkpoint**
(`checkpoints_ft/step_0003000.pt`), not the raw 200k-step base: distillation
should refine an instruction-following model, not re-teach instruction
following from scratch.

## 2. N.1 — teacher selection (measured, not assumed)

`src/download_teacher.py <repo> <local_dir> [min_gb]` pulls with
`local_dir=` (no symlink into the HF cache), verifies file counts/sizes, then
loads offline in bf16 as a pre-flight check. Each candidate was also asked the
VLSI questions that later formed the generation set before being accepted.

| teacher | size | params (offline load) | download | verdict |
|---|---|---|---|---|
| Qwen2.5-0.5B-Instruct | 999.60 MB / 10 files | 494,032,768 | 91.3 s | **rejected** — invented *"ATPG = Automated Testing Program Generator"* (software) and called STA a software technique |
| Qwen2.5-1.5B-Instruct | 3.09 GB | 1,543,714,304 | ~5 min | **rejected** — right acronyms, but fabricated specifics: corner simulation presented as a digital truth table, *"buffers fix setup by adding delay"* (backwards) |
| **Qwen2.5-7B-Instruct** | **15.24 GB / 14 files / 4 shards** | **7,615,616,512** (bf16, 8.7 s) | 1,396.5 s | **selected** |

The 7B pull was launched detached (`nohup setsid … > ~/dl7b.log`) so it
survived the local session being interrupted, and was resumed by re-running the
same command (size-based skip). Key md5s: `config.json` `a15e0d76132ea3fe3a19d0e48e210341`,
`tokenizer.json` `3f99a313c3754208a7f3acfccadc53cd`,
`tokenizer_config.json` `898cd7942ca145c7828f36af58f62ddf`.

## 3. N.2 — teacher generation

`src/generate_teacher_data.py` + `scripts/run_teacher.slurm` (job `bdw_teach`).

* **Chat template is mandatory.** The first runs prompted the model raw and the
  answers leaked transcript voice (`Human:`, `Humanity`); everything below uses
  `tok.apply_chat_template(..., add_generation_prompt=True)` with left padding
  and an explicit `attention_mask`.
* **Hyperparameters:** temperature 0.3, top-p 0.9, `max_new_tokens=224`,
  seed 1234, batch size 8 (teacher rows are what the decode record reports:
  `{"chat_template": true, "temperature": 0.3, "top_p": 0.9, "max_new_tokens": 224, "seed": 1234}`).
* **Kill-proof resume:** each row is keyed by `md5(question)[:16]`; already
  answered keys are skipped on restart, so a 15-minute MaxWall kill loses at
  most the in-flight batch.
* **Content:** 208 domain prompts across 9 VLSI categories (digital, RTL,
  verification, physical, DFT, analog, fabrication, career, open) + 320 Dolly
  rows (40 × 8 categories) = 528 prompts.

Result of the accepted run (**job 32338**, `bdw_teach-32338.out`):
`COMPLETED 00:06:55 exit 0`, **1.40 prompts/s**, **528 rows**,
`data/distilled_teacher_data.jsonl` **745,845 B**,
md5 `c073cd802abdc819ec6fcec76460d226`. Quality split: domain **208/208 clean**
(0 refusals, 0 transcript leaks), Dolly 316/320 usable, 1–3-word answers kept
where genuinely extractive (`'Fearless'`, `'Jon Randall'` are correct).

Earlier runs are preserved rather than overwritten:
`distilled_teacher_data.run1.bak` (0.5 B teacher, 426 rows) and
`distilled_teacher_data.20261022-103421.bak` (1.5 B teacher, 528 rows).

### Teacher answer quality, 1.5B → 7B (VLSI)

All six cases the 1.5B fabricated are correct at 7B: corner simulation
(*process/temperature/voltage corners*), buffer insertion (*reduces delay*),
setup/hold (*stability before the clock edge*), ATPG (+ fault models), Gray
code pointer (one bit changes per transition, correct 3-bit sequence), CDC
(one or more flop stages). The 1.5B's fluent-but-wrong answers are exactly the
failure mode this pipeline had to eliminate — a small teacher's confidence is
not a proxy for correctness.

## 4. N.3a — tokenize with the Stage K recipe (login node)

`src/prep_distilled_data.py` builds ids exactly as `docs/INSTRUCTION_DATA.md` §3
specifies — `<|bos|>User: {q}<|eos|><|bos|>Assistant: {a}<|eos|>` — packs them
into one int32 stream and tiles rows of 1024, mirroring Stage K.

* **528 in → 524 kept** (dropped: 2 refusal/apology prefixes, 2
  `Human:`/`Assistant:` transcript leaks — exact ids recorded in
  `distill_meta.json`).
* **154,992 tokens**, 295.79 per example; stream md5 `3f3a97239b7dab67afccd5620b1f8ad9`.
* **All 10 verification checks true**: id range within vocab (min 1, max 16,383 —
  no pad leak), bos/eos counts = 2 × 524, literal template string encodes
  byte-identically to the programmatic build, every example starts bos/ends eos,
  decode→encode round-trip lossless (with `skip_special_tokens=False`, as Stage K
  did), shards int32 `(n, 1024)`, rows tile the stream.
* **Shards balanced 51/50/50.** Stage K's `1,000,000 // 1024 = 976` rows-per-shard
  would emit 128 one-row shards from 151 rows, so N.3a sizes shards for a small
  dataset instead: ≥2 shards are mandatory (the loader holds the last one out for
  validation), and the sizes are balanced so the held-out tail is ~1/3 rather
  than most of the data. The first attempt produced a 51/100 split — fixed and
  re-verified before training.

| shard | rows | bytes | md5 |
|---|---|---|---|
| `shard_0000.npy` | 51 | 209,024 | `4e2ff1882506d89cb7b0083b14baa953` |
| `shard_0001.npy` | 50 | 204,928 | `4d011c3c91e9da9e9a28bba3bc00dfb3` |
| `shard_0002.npy` (held out) | 50 | 204,928 | `f1c8946d8e86a9bb12c8cadec0f39a61` |

Train = 101 rows / 103,424 tokens, val = 50 rows / 51,200 tokens.

## 5. N.3b — distillation fine-tune (job 32339)

`scripts/distill_student.slurm` runs two passes: an `--eval-only` baseline
score of the Stage L checkpoint on the distilled held-out shard, then the
training run. `src/finetune.py` gained only three explicit arguments
(`--shard-dir`, `--ckpt-dir`, `--stage-tag`) — the auto-resume, the
`--ckpt-interval-s 300` wall checkpoint and the SIGTERM/SIGUSR1 immediate save
are unchanged from Stage L.

| | value |
|---|---|
| base | `checkpoints_ft/step_0003000.pt` (fresh optimizer, step 0) |
| output | `checkpoints_distilled/`, metrics tagged `stage: N3` |
| schedule | 200 steps, warmup 20, cosine lr 1.5e-5 → 1.5e-6 |
| batch | 8 × 1024 → 1,638,400 tokens = **15.84 epochs** |
| eval / ckpt | every 25 steps / every 300 s, keep 3 |
| wall | job **COMPLETED 00:00:30, exit 0, stderr 0 B** (~24 s load + 5.9 s train) |

**Result — held-out shard (50 rows, `rounds=16`):**

| | val loss | val ppl |
|---|---|---|
| Stage L checkpoint (baseline) | 3.3037 | 27.21 |
| after 200 distillation steps | **2.9590** | **19.28** |

−0.3447 nats (**−10.4 %** loss), **−29.2 %** perplexity. Train loss went
3.4531 → 2.7229 with `loss decreased: True`; the eval curve improved through
step 100 (ppl 18.60) and then plateaued (19.4–20.3), i.e. the run saturated the
101-row training shard rather than over-running it.

Checkpoint: `checkpoints_distilled/step_0000200.pt` **333,674,930 B**,
md5 `781990d283e0f0e9489035298b932a9a`, `.meta` records
`base_ckpt: step_0003000.pt`, `tokens_seen: 1638400`, `saved_at 2026-10-22T11:08:51`.
`logs/finetune_metrics.jsonl` tail carries `"stage": "N3"` entries, so Stage L
and N.3 records coexist in one file without ambiguity.

## 6. Artefacts

| artefact | bytes / md5 |
|---|---|
| `data/distilled_teacher_data.jsonl` | 745,845 / `c073cd802abdc819ec6fcec76460d226` |
| `data/distilled_tokens/stream.npy` | 620,096 / `3f3a97239b7dab67afccd5620b1f8ad9` |
| `data/distilled_tokens/distill_meta.json` | 2,415 (all 10 checks true) |
| `data/distilled_tokens/shards/shard_000{0,1,2}.npy` | see §4 table |
| `checkpoints_distilled/step_0000200.pt` | 333,674,930 / `781990d283e0f0e9489035298b932a9a` |
| job logs | `bdw_distill-32339.out` (baseline + train), `bdw_teach-32338.out` (generation) |
| teacher | `~/bdw-llm/teacher_model_7b/` 15.24 GB / 14 files |

## 7. Limitations / next steps

* The held-out shard is 50 rows from the same distribution as training, so
  `19.28` is a regression number, not a task benchmark; a qualitative
  before/after chat comparison on VLSI questions is the honest follow-up.
* 15.84 epochs over 101 rows saturated by step ~100 — further gains need *more
  teacher data* (raise the domain prompt count or `DOLLY_PER_CAT`), not more
  steps over the same rows.
* Logit/KL distillation stays off the table until the student's vocabulary
  grows past the Stage P gate (see `docs/BDW_INTEGRATION.md` §8.2).
