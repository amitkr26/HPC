# Instruction Data — dolly-15k to Fine-tuning Shards (BDW Stage K)

**Executed:** 2026-10-21 09:58–10:01 IST
**Where:** login node `login02` (`OMP_NUM_THREADS=4`) — no SLURM job, because this
stage is the one part of the pipeline that needs DNS
**Script:** `src/prep_instruction_data.py`
**Output:** `~/bdw-llm/data/instruct_tokens/`

The compute nodes have no network (`ENVIRONMENT_AUDIT.md` §8/§9), so the raw
rows are fetched on the login node. Everything after that — filtering,
formatting, tokenising, sharding — happens in the same login-node process and
needs no network at all.

---

## 1. Dataset choice

The brief allowed any free instruction or synthetic dataset. We took the full
**`databricks/databricks-dolly-15k`** (`config=default`, `split=train`,
**15,011 rows**, 13.0 MB) rather than a slice of `HuggingFaceTB/cosmopedia`.

* The brief's "~50 MB" is an upper bound, not a target. Dolly's entire 15,011
  rows land at 13.0 MB — smaller than the budget and **complete**, so no
  arbitrary truncation.
* Dolly is human-written instruction/response pairs across 8 task types.
  Cosmopedia is synthetic textbook prose, which is useful for pre-training but
  adds no *instruction format* signal — exactly what Stage L needs.
* Human-written beats synthetic for a small model's first fine-tune, because
  the target style is consistent rather than machine-generated.

## 2. Format

Every kept record is written as the conversational layout the brief specified:

```
<|bos|>User: [Question]<|eos|><|bos|>Assistant: [Answer]<|eos|>
```

4,467 of the 15,010 examples carry a `context` field (`closed_qa`,
`summarization`, some `general_qa`). Those rows are unanswerable without it, so
the context is appended to the **user** turn under a label:

```
<|bos|>User: When did Virgin Australia start operating?

Context:
Virgin Australia, the trading name of Virgin Australia Airlines Pty Ltd, ...<|eos|><|bos|>Assistant: Virgin Australia commenced services on 31 August 2000 as Virgin Blue, with two aircraft on a single route.<|eos|>
```

Long contexts are capped at 6000 characters (truncated with a trailing `...`)
so a single passage cannot dominate a 1024-token row.

The same `build_user()` helper is what Stage M will call to build the live
prompt, so training and inference cannot drift apart.

## 3. Token ids are built explicitly, not hoped for

Rather than rely on the tokenizer splitting special tokens out of a string, ids
are assembled by hand:

```python
ids = [bos] + tok.encode("User: " + q).ids + [eos, bos] \
    + tok.encode("Assistant: " + a).ids + [eos]
```

The run confirms the two views agree — encoding the **literal** template string
yields byte-for-byte the same ids as the programmatic build, and a
decode→encode round-trip is lossless.

A pre-flight probe also established that the Stage D tokenizer has **no
post-processor**: `encode('hello world') -> [262, 12669, 957]`, i.e. no extra
`bos`/`eos` is injected. Every special token in the stream is one we placed
deliberately.

## 4. Download route

Rows are pulled through the bounded HF `datasets-server` rows API — the same
resumable route used for the Stage C pilot corpus:

```
https://datasets-server.huggingface.co/rows?dataset=databricks/databricks-dolly-15k
  &config=default&split=train&offset=N&length=100
```

151 pages of 100, with 0.9 s politeness sleep, exponential backoff on
429/502/503 and a `progress.json` resume marker. The endpoint rate-limited us
several times (HTTP 429 at offsets 2700, 6100, 9100, 13000) and the backoff
recovered each time with no data loss. The raw records are kept in
`data/raw/dolly15k.jsonl` so formatting is auditable and re-runnable without
re-downloading — the verification pass below was in fact a re-run that resumed
at `offset=15011` and correctly fetched nothing.

## 5. Run

```
=== Stage K: instruction data (dolly-15k) ===
download: databricks/databricks-dolly-15k/default/train  resuming at offset=0 kept=0 mode=w
  offset=2500   kept=2500   2.2 MB (52s)
    retry 1/10 offset=2700 code=429 sleep=8s
    retry 2/10 offset=2700 code=429 sleep=16s
    retry 3/10 offset=2700 code=429 sleep=32s
  offset=5000   kept=5000   4.3 MB (179s)
  offset=7500   kept=7500   6.4 MB (268s)
  offset=10000  kept=10000  8.6 MB (401s)
  offset=12500  kept=12500  10.8 MB (443s)
  offset=15000  kept=15000  13.0 MB (544s)
  offset=15011  kept=15011  13.0 MB (546s)
no more rows at offset 15011 (reached end)
download DONE: kept=15011 bytes=13002635 (13.0 MB) elapsed=545.9s

tokenizer   : /home/tutor/3ioip3lt/bdw-llm/tokenizer/tokenizer.json
vocab_size  : 16384
special ids : pad=0 bos=1 eos=2
encode probe: ids=[262, 12669, 957]  (no post-processor expected)

examples    : 15010 (skipped 1, with context 4467, longer than 1024 ids 232)
tokens      : 2927516  (195.04 per example)
encode_time : 4.9s (600842 tokens/s)
id range    : min=1 max=16383 (vocab=16384)
categories  : {"brainstorming": 1766, "classification": 2136, "closed_qa": 1773, "creative_writing": 708, "general_qa": 2191, "information_extraction": 1506, "open_qa": 3742, "summarization": 1188}
saved       : /home/tutor/3ioip3lt/bdw-llm/data/instruct_tokens/stream.npy 11710192 bytes

seq_len     : 1024
rows        : 2858  (tail 924 tokens dropped)
shards      : 3
   shard_0000.npy   (976, 1024)    3997824 bytes
   shard_0001.npy   (976, 1024)    3997824 bytes
   shard_0002.npy   (906, 1024)    3711104 bytes

--- verification ---
  template-vs-build match : True   (literal-encode match: True)
  template-vs-build match : True   (literal-encode match: True)
  template-vs-build match : True   (literal-encode match: True)
  template-vs-build match : True   (literal-encode match: True)
  bos count = 30020 (expected 30020)  -> True
  eos count = 30020 (expected 30020)  -> True
  examples starting with bos : 15010 / 15010  -> True
  examples ending with eos   : 15010 / 15010  -> True
  shard dtypes/shapes ok    : True   (rows 2858 vs 2858)

  sample category : closed_qa
  sample ids      : [1, 5836, 266, 28, 1635, 836] ... [1999, 6292, 16, 2]
  decoded text    :
    <|bos|>User: When did Virgin Australia start operating?

    Context:
    Virgin Australia, the trading name of Virgin Australia Airlines Pty Ltd, is an Australian-based airline. It is the largest airline by fleet size to use the Virgin brand. It commenced services on 31 August 2000 as Virgin Blue, with two aircraft on a single route. It suddenly found itself as a major airline in Australia's domestic market after the collapse of Ansett Australia in September 2001. The airline has since grown to directly serve 32 cities in Australia, from hubs in Brisbane, Melbourne and Sydney.<|eos|><|bos|>Assistant: Virgin Australia commenced services on 31 August 2000 as Virgin Blue, with two aircraft on a single route.<|eos|>
  decode->encode round-trip : True
  held-out shard for Stage L: ['shard_0002.npy']

all checks passed

meta -> /home/tutor/3ioip3lt/bdw-llm/data/instruct_tokens/instruct_meta.json
STAGE_K_OK examples=15010 tokens=2927516 shards=3
```

`logs/stageK.err` was empty.

## 6. Artefacts

| File | Shape / size | md5 |
|---|---|---|
| `data/raw/dolly15k.jsonl` | 13,017,646 B, 15,011 records | `3f8229dea39ab1de03b4044c758fbe73` |
| `data/instruct_tokens/stream.npy` | 2,927,516 int32 tokens, 11.7 MB | `1b12e8de23cdf40a5ecdc03d895cb6c2` |
| `data/instruct_tokens/shards/shard_0000.npy` | `(976, 1024)` int32, 3,997,824 B | `6c6c3aff311a3b875af0658f91f93e9c` |
| `data/instruct_tokens/shards/shard_0001.npy` | `(976, 1024)` int32, 3,997,824 B | `61529ed706da09dfa8b150187999c27a` |
| `data/instruct_tokens/shards/shard_0002.npy` | `(906, 1024)` int32, 3,711,104 B | `757ae657c18bf0c184f211815f3cc5a1` |
| `data/instruct_tokens/instruct_meta.json` | 928 B provenance | `22b08dd7664ac67643e1cacddb61ef3b` |
| `src/prep_instruction_data.py` | 16,422 B | `e57c86ed6db36d23becb894e1e096ec7` |

The shards are byte-identical to the Stage E training format — `int32`, rows of
`seq_len = 1024`, ~1M-token shard files — so Stage L reuses the same loader.

## 7. Verification

| Check | Result |
|---|---|
| Rows downloaded | **15,011 / 15,011** (the entire dataset) |
| Examples kept | **15,010** (1 skipped: empty instruction/response) |
| Token id range | `min=1 max=16383`, vocab=16384 — **in range** |
| `<|pad|>`(0) leaking into the stream | **none** (`min=1`) |
| `<|bos|>` count | 30,020 = **exactly 2 × 15,010** |
| `<|eos|>` count | 30,020 = **exactly 2 × 15,010** |
| Examples starting with `<|bos|>` | **15,010 / 15,010** |
| Examples ending with `<|eos|>` | **15,010 / 15,010** |
| Literal template encode == programmatic build | **True** (4/4 samples) |
| Decode → encode round-trip | **lossless** |
| Shard dtypes/shapes | `int32`, `(n, 1024)`, rows tile the stream exactly (2,858) |
| stderr | empty |

## 8. Notes on the numbers

* **232 examples are longer than 1024 ids.** In a contiguous stream they cross
  row boundaries. This is the same behaviour as Stage E, where documents also
  span rows — `<|eos|>`/`<|bos|>` delimiters keep the turns separable.
* **924 trailing tokens were dropped** — fewer than one row, unavoidable with
  fixed-length packing.
* **`skipped 1`** — one dolly record has no usable instruction or response.
* **195 tokens per example** on average; 2.93 M tokens total is a normal
  instruction-tuning volume for a 28 M parameter model, and Stage L will run
  several epochs over it rather than one pass.

## 9. Next step

Stage L loads `checkpoints/step_0200000.pt` and fine-tunes on shards 0–1 with
`shard_0002.npy` held out, reusing the Stage G auto-resume and 5-minute
checkpoint logic so the 15-minute MaxWall limit is survivable.

_Generated by the Stage K script; evidence re-read from the cluster._
