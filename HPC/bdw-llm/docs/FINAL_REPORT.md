# Stage J — Final Report: From-Scratch LLM on PARAM Rudra

**Project:** BDW — build a small language model completely from scratch on
the PARAM Rudra HPC cluster.
**Date:** 2026-10-16
**Account / user:** `tutor` / `3ioip3lt`
**Result:** all stages A through I completed and verified from literal
cluster output. Model trained from **random init** to step **200,000**;
held-out perplexity **52.40** vs **18,603.31** for the untrained model.

---

## 1. What was actually built

| | |
|---|---|
| Architecture | decoder-only Transformer, pre-norm, learned positional embeddings, multi-head causal self-attention (`F.scaled_dot_product_attention`, `is_causal=True`) |
| Parameters | **27,800,576** |
| Layers / heads | 6 / 8, `n_embd=512`, context 1024 |
| Vocab | **16,384** byte-level BPE, built here (not downloaded) |
| Training data | FineWeb (English, ≥50 tokens), **165 MB / 50,689 documents** |
| Tokens trained | **1,638,400,000** (200,000 steps × 8192) = 43.14 epochs |
| Hardware | 1× NVIDIA A100 80 GB PCIe on `rdgpu01`, CUDA 12.3, torch 2.5.1+cu121 |
| Throughput | ~383,000 tokens/s (~47 steps/s) |
| Wall time | 5 chained 15-minute jobs + 1 finishing job |

Nothing was imported from a pretrained model: no pretrained weights, no
downloaded tokenizer, no `AutoModel.from_pretrained`.

---

## 2. Stage-by-stage summary

| Stage | Deliverable | Key evidence | Job(s) |
|---|---|---|---|
| **A** Environment audit | `ENVIRONMENT_AUDIT.md` | login vs compute node, GPU, QOS limits | 31730, 31731 |
| **B** Pinned environment | `ENVIRONMENT_SETUP.md`, venv | 81 packages, CUDA OK on GPU node | 31739 |
| **C** Pilot corpus | `DATASET.md`, `fineweb_pilot.jsonl` | 165 MB, 50,689 docs, 50,689 unique URLs | 31752 |
| **D** Tokenizer | `TOKENIZER.md`, `tokenizer.json` | vocab 16,384, round-trip 0 mismatches | 31776 |
| **E** Tokenised stream | `TOKENS.md`, `stream.npy` | 38,210,943 raw tokens → 37,315 rows × 1024 | 31783 |
| **F** Model + smoke test | `MODEL.md`, `src/model.py` | `SMOKE_PASS`, 52/52 grads finite, loss 9.81 | 31809 |
| **G** Training infrastructure | `TRAINING.md` §1–7 | auto-resume, signal save, held-out split | 31814, 31831, 31833, 31836 |
| **H** Chained training | `TRAINING.md` §8–10 | 5 jobs chained to 200,000 steps | 31844, 31859, 31863, 31866, 31870 |
| **I** Evaluation | `EVALUATION.md` | unseen ppl **52.40**, baseline **18,603.31** | 31862, 31871 |
| **J** This report | `FINAL_REPORT.md` | md5s below | — |

---

## 3. Headline numbers (job 31871, checkpoint `step_0200000.pt`)

| Measurement | NLL | Perplexity | Token accuracy |
|---|---|---|---|
| Random-init model, unseen text | 9.8311 | **18,603.31** | 0.00007 |
| **Trained model, unseen text** | **3.9589** | **52.40** (95% CI 51.49–53.32) | **0.3213** |
| Trained model, seen text | 3.5636 | 35.29 (95% CI 34.08–36.54) | 0.3600 |

* **≈355× perplexity reduction** versus the untrained network, measured on
  **2,555,904 tokens** from documents whose URLs have **zero overlap** with
  the 50,689 training URLs.
* Generalisation gap: **+0.395 nats** (unseen costs more than seen).
* Final training loss **3.5953**, learning rate finished exactly at
  `min_lr = 6e-5`.

---

## 4. Documentation and verification

Every stage document was uploaded and its md5 compared between the local
copy and the cluster copy. All eight matched:

| Document | Bytes | md5 |
|---|---|---|
| `ENVIRONMENT_AUDIT.md` | 25,564 | `d07d97d361dcface090c8579318c19ff` |
| `ENVIRONMENT_SETUP.md` | 6,552 | `5ea855f7f29b75fdb331927d82c343a7` |
| `DATASET.md` | 6,281 | `315cf92c319675cb67633f1ac4c99f41` |
| `TOKENIZER.md` | 4,361 | `0b537103fe5c09f3881fadc6646dd402` |
| `TOKENS.md` | 4,219 | `81a3c29a19a1e0d8b7da36e074d57c25` |
| `MODEL.md` | 6,211 | `c61a6adb8d1e5c4806645760774fd4a5` |
| `TRAINING.md` | 19,363 | `5c90b082b805b2a0770497a08f0d7d92` |
| `EVALUATION.md` | 8,996 | `a685b54dc05c79bd15eea832c3fb5cfd` |

Data, code and script hashes (cluster side):

> **Note on `TOKENIZER.md`.** Its first recorded md5 was
> `96dd8b1112fec26c506ba068fa49a60b` (4,336 bytes). That version embedded
> one literal NUL byte in a probe-string example, which caused git to treat
> the document as binary and refuse to diff it. During repository setup the
> example was rewritten as readable escapes (`\x00 \x01 \x02 \x7F \u0080
> \u00FF`) — same meaning, now pure UTF-8 text — giving the value in the
> table above. Both md5s are recorded so the change stays traceable.

| Artifact | md5 |
|---|---|
| `data/raw/fineweb_pilot.jsonl` (165 MB) | `2614cff01bf217ae13199ce9216935e4` |
| `data/eval/fineweb_eval_unseen.jsonl` (10.5 MB) | `2e59ca70d9ad03e753a5963c84c75fde` |
| `data/eval/eval_tokens.npy` (10.2 MB) | `37269502b81ce92eba1d244f5f351bde` |
| `logs/eval_results.json` | `6e58e3a5e75e18e814cc5f2474c66ad6` |
| `src/train.py` | `eb012c3eb69822974a32e3ea0845f259` |
| `src/eval_model.py` | `7794290932475b25fe27ea183cadb7dc` |
| `scripts/train.slurm` | `3e2ec27a1e12ad04efb121964c7883d1` |
| `scripts/eval.slurm` | `3f42942032982111bcdd93e2b3758afe` |

---

## 5. Job ledger

31 jobs submitted; states taken from `sacct`:

| State | Count | Job IDs |
|---|---|---|
| `COMPLETED` | 22 | 31720 31721 31723 31724 31725 31726 31727 31728 31729 31730 31731 31736 31739 31752 31776 31783 31809 31831 31836 31862 31870 31871 |
| `TIMEOUT` | 6 | 31814 31833 31844 31859 31863 31866 |
| `FAILED` | 1 | 31808 |
| `CANCELLED` | 2 | 31722 31757 |

Of the six `TIMEOUT` jobs, five (31833, 31844, 31859, 31863, 31866) ended
with their **batch process** in state `COMPLETED`, i.e. the script caught
the signal, saved, printed its summary and exited cleanly — only
**31814** ended with the batch process `CANCELLED`.

Nothing was hidden: `31808` was the first smoke-test submission that died on
a script error before any computation; `31757` was cancelled by hand when
its QOS quota was needed elsewhere; `31722` was a deliberate connectivity
check cancelled after it proved the job could reach the network. `31814`
(the very first training run) is the one job that ended with its batch
process `CANCELLED` — that is exactly the bug that was later fixed by
switching to `exec python` (§7 of `TRAINING.md`).

---

## 6. What went wrong and was fixed (8 bugs, all verified live)

1. Throughput printed `183` instead of ~385,000 (cumulative vs interval
   elapsed time).
2. `(train-window …)` printed `9706` instead of ~4.1 (unreset cumulative sum).
3. Final save wrote no `.meta` sidecar.
4. Rotation orphaned `.meta` sidecars.
5. Graceful shutdown never fired because `python` was a child of `bash`
   under `sbatch` — fixed with `exec python`.
6. `sbatch --max-steps 60 train.slurm` passed options to `sbatch` instead
   of the script.
7. `stop reason` label always reported `total-steps`; replaced with an
   explicit `signal` / `total-steps` / `max-steps` / `loop-exit`.
8. Duplicate final save; guarded with `last_saved_step`.

> **Post-hoc documentation correction (Stage O, 2026-10-21).** The
> architecture row in §1 originally described the model as using RoPE with
> "learned positional embeddings removed in favour of RoPE". That is wrong.
> `src/model.py` uses **learned positional embeddings** (`pos_emb =
> nn.Embedding(seq_len, d_model)`, added to the token embedding in
> `TransformerLM.forward`) and contains **no rotary embedding code at all** —
> attention is plain `F.scaled_dot_product_attention(..., is_causal=True)`.
> `MODEL.md` §1 was always correct; this report's summary row was not, and
> has been fixed. The trained weights and all measured results are unaffected
> — only the prose was wrong.

---

## 7. Honest limitations

1. **43 epochs over 165 MB is a lot.** The model was trained on the same
   small corpus 43 times. Held-out perplexity improved 10% from step
   117,602 to 200,000, but the generalisation gap widened from 0.286 to
   0.395 nats — memorisation grew alongside skill. A larger corpus would
   have been the better trade, but the Stage C QOS and the 15-minute wall
   limited how much could be downloaded and processed.
2. **The in-training validation split is not trustworthy** as a
   generalisation measure: it is 232,448 tokens and was inside the training
   stream for steps 0–34,038. `EVALUATION.md` documents this and replaces it
   with a URL-disjoint test set.
3. **The evaluation set is unseen but in-distribution** — same dataset,
   same config, same filters. It measures generalisation to new documents,
   not to new domains.
4. **Confidence intervals are narrower than they should be**, because
   adjacent rows of the same document are treated as independent.
5. **Generation quality is limited.** Greedy decoding collapses into
   repetition; sampling produces fluent but factually unreliable English.
   No repetition penalty was applied, since that would change the
   measurement.
6. **No memorisation audit was performed** beyond an aggregate NLL gap
   over 500 training rows — no n-gram overlap search against the corpus.
7. **Every job ran on a single A100** under the `training` QOS (15 min,
   4 CPUs, 1 GPU, 1 job). No multi-GPU, mixed-precision or hyperparameter
   sweep was attempted, so this is one point in configuration space, not a
   tuned result.
8. **The loss curve is stitched from separate processes**, not one
   uninterrupted run. Resume correctness is proven, but the gradient-noise
   statistics differ from a single long run.

---

## 8. Conclusion

A 27.8 M parameter decoder-only Transformer was built from nothing —
tokenizer, data pipeline, model, training loop, checkpointing, evaluation —
trained from random initialisation on PARAM Rudra for 200,000 steps / 1.64 B
tokens, and evaluated honestly on text it had never seen.

Perplexity fell from **18,603.31** (untrained) to **52.40** (trained) on
2.56 M held-out tokens with zero URL overlap with training — a **~355×**
improvement, and a token accuracy of **32.1%** against a 16,384-token
vocabulary.

The model is small and it over-fits its small corpus, and that is stated
plainly rather than papered over. Every claim in this report is traceable
to a job ID, a log line, or an md5.
