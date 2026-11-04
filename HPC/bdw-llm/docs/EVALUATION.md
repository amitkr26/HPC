# Stage I — Honest Evaluation on Unseen Text

This document records Stage I: measuring how well the trained model
performs on text it has **never been trained on**, and showing what it
generates.

Every number below is quoted from job **31871** (and the earlier snapshot
job **31862**) on `rdgpu01`, and from `~/bdw-llm/logs/eval_results.json`.

---

## 1. Why the in-training validation split was not enough

Stage G introduced a held-out shard (`val shards: 1 rows=227`), and its
`val_loss` numbers looked reasonable. That split is still **not a valid
generalisation measurement**, for two reasons that this project owns openly:

1. **The held-out shard was memorised before it became held-out.** The first
   training job (31814) and job 31833 ran with the *old* loader that used
   all 39 shards. The shard that is now "validation" was in the training
   set for steps 0–34,038. Its early `val_loss` values (3.71 at step 34,500)
   are therefore contaminated.
2. **It is tiny** — 232,448 tokens, 0.61% of the corpus — so it is noisy.

Because essentially every row of the pilot corpus was drawn into training
at some point, **no document inside `fineweb_pilot.jsonl` is unseen by the
model.** A valid test therefore had to come from *outside* that file.

---

## 2. Building a genuinely unseen evaluation set

Stage C consumed raw offsets `0..50600` of
`HuggingFaceFW/fineweb` config `sample-10BT`, split `train`, through the
datasets-server **rows** API with client-side filters
(`language == "en"`, `token_count >= 50`).

Offsets index the **raw** split, so Stage I started at **offset 60000** — a
deliberate gap past 50700 — and applied the identical filters:

| Property | Value |
|---|---|
| Source offsets (raw) | `60000` .. `63400`, 100 rows per request, 34 requests |
| Documents kept | 3,400 |
| Bytes | 10,509,967 (10.5 MB) |
| File | `~/bdw-llm/data/eval/fineweb_eval_unseen.jsonl` |
| **md5** | **`2e59ca70d9ad03e753a5963c84c75fde`** |
| Hub 5xx/429 retries | recovered automatically (shared endpoint) |

### Disjointness proof

```
train urls   : 50689
eval urls    : 3400
overlap      : 0
disjoint     : True
```

Zero URL overlap with the 50,689 training URLs. This is the central
claim of this stage and it is machine-checked, not assumed.

---

## 3. Tokenisation parity

The eval corpus is encoded with the **same Stage D tokenizer and the same
recipe as Stage E** — one contiguous `int32` stream, each document followed
by `<|eos|>` (id 2):

```
documents     : 3400
tokens        : 2556206 (2.56 M)
id range      : [2, 16383]
eos count     : 3400
encode time   : 4.2s (614083 tokens/s)
rows of 1024     : 2496 (tail 302 tokens dropped)
```

| Artifact | Size | md5 |
|---|---|---|
| `data/eval/eval_tokens.npy` | 10,224,952 B | `37269502b81ce92eba1d244f5f351bde` |
| `data/eval/eval_meta.json` | 359 B | — |

The scoring set is **2,555,904 tokens** (2,496 × 1024); the 302-token tail
is dropped so every scored row has identical length.

---

## 4. Method

`src/eval_model.py`, run through `scripts/eval.slurm`
(`--partition=gpu --gpus=1 --cpus-per-task=4 --time=00:05:00`):

* mean negative log-likelihood per token over **all** rows,
* perplexity = `exp(mean NLL)`,
* 95% confidence interval from the standard error across rows,
* top-1 token accuracy,
* **three** measurements so the numbers can be interpreted:

| Measurement | Purpose |
|---|---|
| random-init model on unseen text | what an untrained net scores (floor) |
| trained model on unseen text | the real result |
| trained model on **seen** rows | how much is memorisation |

The random-init baseline is built with the same `seed=1337` used throughout
the project, so it is a controlled comparison on the *same* 2,496 rows.

---

## 5. Results

### Job 31871 — final model at step 200,000

```
checkpoint    : /home/tutor/3ioip3lt/bdw-llm/checkpoints/step_0200000.pt
ckpt step     : 200000  tokens_seen=1638400000  (43.14 epochs)
eval rows     : 2496 x 1024

[baseline] perplexity=18603.31  nll=9.8311  acc=0.0001
[unseen]   perplexity=52.40  nll=3.9589  95% CI=[51.49, 53.32]  acc=0.3213
[seen]     perplexity=35.29  nll=3.5636  acc=0.3600
```

| Measurement | NLL | Perplexity | Token accuracy |
|---|---|---|---|
| Random init, unseen text | 9.8311 | **18,603.31** | 0.00007 |
| **Trained, unseen text** | **3.9589** | **52.40** (CI 51.49–53.32) | **0.3213** |
| Trained, seen text | 3.5636 | 35.29 (CI 34.08–36.54) | 0.3600 |

* **Perplexity falls 18,603 → 52.40, a factor of ~355**, on text the model
  never saw. That is the headline result: training learned real English
  structure, not just a lookup table.
* Random-init token accuracy `6.93e-05` sits right at the `1/16384 =
  6.10e-05` floor, confirming the baseline is genuinely untrained.
* Random-init NLL `9.8311` sits just above `ln(16384) = 9.7041` (uniform),
  as expected for a fresh net — and matches the Stage F smoke test.
* `generalisation_gap_nll = 0.3953` — unseen text costs **0.395 nats**
  more than seen text. Real, but small: the model is mostly generalising.

### Improvement during the second half of training (job 31862 → 31871)

| | step 117,602 | step 200,000 | change |
|---|---|---|---|
| Unseen perplexity | 58.34 | **52.40** | −10.2% |
| Unseen token accuracy | 0.3085 | **0.3213** | +4.1% |
| Seen perplexity | 43.85 | 35.29 | −19.5% |
| Generalisation gap | 0.286 nats | 0.395 nats | +0.109 nats |

Finished cosine decay to `min_lr = 6e-5` improved held-out perplexity by
10%. The widening gap (0.286 → 0.395 nats) is the honest cost of running
43 epochs over a 165 MB corpus: the model memorised progressively more.

### Sanity checks that passed

* `perplexity = exp(NLL)`: `exp(3.9589) = 52.40` ✓
* `tokens_seen = 200000 × 8192 = 1,638,400,000` ✓ (matches the checkpoint)
* `exp(9.8311) = 18,603` and `ln(16384) = 9.704` bracket the baseline ✓
* `eval_results.json` parses as valid JSON ✓

---

## 6. Generated text

Three prompts, 80 tokens each (job 31871). Greedy uses `top_k=1`;
"sample" uses `temperature=0.8, top_k=50`.

**Prompt: `Scientists have`** (sampled)

> Scientists have studied how it can be done in order to establish a new
> perspective on the field of biology and the field of science. This is a
> unique tool for the development of science in science and the field of
> science, which is why scientists should take the time to develop an
> understanding of science and science.

**Prompt: `In recent years,`** (sampled)

> In recent years, the company has been on the water for nearly a decade.
> When the company began to focus on environmental change, its product and
> service operations continue to grow, and the company has been doing a
> tremendous job in that area.

**Prompt: `The history of`** (greedy)

> The history of the country is not a new one. It is a new one. It is a
> new one. It is a new one. It is a new one. It is a new one. It is a new
> one. It is a new one.

Honest reading:

* **Grammar and local fluency are good.** Sentences are well formed, with
  plausible punctuation and paragraph breaks.
* **Content is unreliable.** The text says nothing verifiably true; it is
  fluent filler.
* **Greedy decoding collapses into repetition.** This is the expected
  behaviour of argmax decoding on a 27.8 M parameter model — the argmax
  path enters a loop it cannot leave. Sampling (`t=0.8, k=50`) avoids it.
* Only three prompts × 80 tokens were inspected. **We did not audit for
  verbatim memorisation of training documents**, which remains an open
  limitation (see §7).

---

## 7. Limitations

- The eval set is **unseen but in-distribution**: same dataset, same
  config, same filters as training. It measures generalisation to new
  documents, not to new domains.
- The 95% CI treats rows as independent, but adjacent rows often belong to
  the same document, so the true interval is **wider** than reported.
- Perplexity 52.40 is far from state of the art and should not be compared
  with published LLMs: this is a 27.8 M parameter model trained from
  random init on 165 MB of text.
- Memorisation was quantified only as an aggregate NLL gap over 500 rows;
  no per-document or n-gram overlap analysis was performed.
- Greedy-decoding repetition is a decoding artefact, not a training bug,
  but no repetition penalty was applied because it would change the
  measurement.

---

## 8. Artifacts

| Path | md5 |
|---|---|
| `~/bdw-llm/data/eval/fineweb_eval_unseen.jsonl` | `2e59ca70d9ad03e753a5963c84c75fde` |
| `~/bdw-llm/data/eval/eval_tokens.npy` | `37269502b81ce92eba1d244f5f351bde` |
| `~/bdw-llm/logs/eval_results.json` | `6e58e3a5e75e18e814cc5f2474c66ad6` |
| `~/bdw-llm/src/eval_model.py` | `7794290932475b25fe27ea183cadb7dc` |
| `~/bdw-llm/scripts/eval.slurm` | `3f42942032982111bcdd93e2b3758afe` |
| `~/bdw-llm/checkpoints/step_0200000.pt` | 333,675,250 B (final weights) |

Jobs: **31862** (interim, step 117,602, `COMPLETED`, `00:00:29`) and
**31871** (final, step 200,000, `COMPLETED`, `00:00:18`).
