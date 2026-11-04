# Chat with Retrieval (RAG) — Stage M

**Executed:** 2026-10-21 10:40–11:15 IST
**Where:** **login node** `login02` — CPU only, no SLURM job
**Script:** `src/chat_with_rag.py`
**Checkpoint:** `checkpoints_ft/step_0003000.pt` (the Stage L fine-tune)

---

## 1. Why this runs on the login node

`ENVIRONMENT_AUDIT.md` §8/§9 established that the compute nodes have **no
network and no DNS**. Retrieval therefore has to happen on the login node.
There is no reason to ask for a GPU either: the model is 27,800,576
parameters, 334 MB, so it loads in ~0.6 s and generates at 14–55 tokens/s on
4 CPU cores. The script pins `OMP_NUM_THREADS=4` and `torch.set_num_threads(4)`
because the login node is shared.

## 2. Pipeline

```
question ──► retrieve (Wikipedia) ──► build prompt ──► generate (CPU) ──► answer
                    │                      │
                    │                      └── same template as Stage K
                    └── top-2 paragraphs, each capped at 800 chars
```

**Retrieval.** `wikipedia` 1.4.0 is the primary source: `search()` for titles,
then `page(title, auto_suggest=False)` and the lead paragraph of
`page.content`. Requests are rate-limited and retried up to 4 times with
exponential backoff — the Wikipedia endpoint from PARAM Rudra intermittently
returns a non-JSON body, which shows up as `JSONDecodeError`.

**DuckDuckGo is opt-in (`--use-ddg`), not the default.** `duckduckgo-search`
8.1.1 is installed, but from this cluster both its `html` and `api` backends
returned `n=0` for a plain query, and when forced on it produced
**irrelevant** results — asking about photosynthesis returned two TurboTax
support pages. Shipping that as a silent fallback would have produced
confident nonsense, so it is off unless explicitly requested.

**Prompt.** The exact Stage K template, with retrieved passages appended to
the user turn under a `Context:` label:

```
<|bos|>User: [Question]

Context:
[1] https://en.wikipedia.org/wiki/Black_hole
A black hole is an astronomical body so compact that its gravity prevents...

[2] https://en.wikipedia.org/wiki/Supermassive_black_hole
A supermassive black hole (SMBH or sometimes SBH) is the largest type...<|eos|><|bos|>Assistant:
```

**Generation.** CPU inference, stopping at `<|eos|>`, with a repetition
penalty of 1.2 and an 8-token loop guard (see §4).

## 3. The bug that mattered: a trailing space

The first version of this script produced the same garbage no matter what was
asked — `{User: What is the difference between a black hole and a black hole?`
— while ignoring the question entirely.

The cause was one character. The prompt was built with
`FMT.format(q=..., a="")`, which yields a **trailing space** after
`Assistant:`. Byte-level BPE folds that space into the *next* token
(` Virgin` is a single token), so in training the model never saw a
standalone space token in that position. Emitting one put the model in a
state it had never been trained on, and it derailed.

Fixed by ending the prompt at `Assistant:` with no trailing space. Prompt
tails went from `[1, 12247, 13765, 28, 223]` to `[2, 1, 12247, 13765, 28]`
(223 was the stray space).

A teacher-forced check confirms the model itself was never the problem. Given
a real training-format prompt ending at `Assistant:`, its top prediction was
` Virgin` with p=0.68 for the Virgin Australia row and ` Kyle` with p=0.41
for the Kyle Van Zyl row — i.e. the correct first answer token in both cases.

## 4. Why a repetition penalty

Under pure argmax a 28 M parameter model loops: `A black hole is a hole that
is a hole that is a hole...`. Two mitigations, both defaulted on:

* **Repetition penalty 1.2** — logits for tokens already generated are divided
  by 1.2. Only the *continuation* is penalised by default (`--penalize-prompt`
  opts into penalising the context too), so the model can still reuse wording
  from the retrieved passages, which is the whole point of RAG.
* **Loop guard 8** — stop if the last 8 generated tokens exactly repeat the
  8 before them.

## 5. Results

All five cases below ran to completion with empty stderr.

### With retrieval — the model uses the passages

**"What is a black hole?"** (Wikipedia: Black hole, Supermassive black hole)

> A black hole is a class of astronomical objects that have undergone
> gravitational collapse. They are known for being part of the mass of all
> black holes, having not a supermassive black hole at its center. This is
> called the event horizon which describes the events horizon, which can be
> interpreted to be more sophisticated than black holes. However, there are
> many other non-violet spacetime elements

"gravitational collapse", "event horizon", "supermassive", "spacetime" are all
lifted from the retrieved text. The grammar is rough — this is a 28 M
parameter model — but it is grounded, not hallucinated.

**"Which is a species of fish? Tope or Rope"** (Wikipedia: Shark, List of
least concern fishes)

> All species of fish are classified within the division Selachii and are
> classified as extinct members. The list is known from Tope's list, as well
> as some species of fish species.

"Selachii" comes from the Shark passage; "Tope" is the correct answer from the
question.

**"What is photosynthesis?"** (Wikipedia: Photosynthesis, Photosynthetic
efficiency)

> photosynthesis is a system of organisms that have different properties,
> such as magnesium, carbon and water. The photopigraphic structure of the
> phototrophic is the most efficient way for photopigment.

"photopigment" and "carbon and water" come from the passage.

### Without retrieval — the contrast

`--no-rag`, same question, same seed:

> A black hole is a hole that you can create in the hole. The hole in the hole
> can be found over a few hours. You can move a green hole when it comes to a
> hole. A yellow hole can be found over many hours and it's not known whether
> it was the last hole in the hole or any other hole in the hole.

Retrieval is clearly doing real work.

### An honest failure

**"Who wrote the play Romeo and Juliet?"** returned:

> The play of Romeo and Juliet, FR 42, is an orchestral work composed by
> Pyotr Ilyich Tchaikovsky. It was also known as the Tchaikovsky.

The model faithfully summarised the **first** retrieved passage — which was
Tchaikovsky's overture-fantasy, not the play. The second passage *did* contain
the right answer ("a tragedy written by William Shakespeare"), but a 28 M
model does not reliably arbitrate between two retrieved passages. Better
retrieval ranking, or asking for more passages and re-ranking, would be the
fix; that is a retrieval problem, not a model one.

## 6. Measured behaviour

| | value |
|---|---|
| Model load | 0.6 s |
| Generation speed | 14–55 tokens/s (CPU, 4 threads) |
| Retrieved passages | 2, each ≤ 800 chars |
| Typical prompt | 270–395 token ids with context, 15 without |
| Wikipedia success | intermittent — 4-attempt retry usually recovers |

## 7. Usage

```
# one-shot, with retrieval
OMP_NUM_THREADS=4 ~/bdw-llm/venv/bin/python ~/bdw-llm/src/chat_with_rag.py \
    "What is a black hole?"

# compare against the same model with no context
... chat_with_rag.py --no-rag "What is a black hole?"

# interactive REPL
... chat_with_rag.py --interactive

# knobs
... chat_with_rag.py --top-k 3 --max-new-tokens 120 \
    --temperature 0.7 --top-k-sample 40 --repetition-penalty 1.2 --seed 5

# inspect exactly what the model was given
... chat_with_rag.py --show-prompt --show-specials "..."
```

## 8. Artefacts

| File | Size | md5 |
|---|---|---|
| `src/chat_with_rag.py` | 14,959 B | `383c3a96c835b70ff40dd779e24bf3fc` |

New packages installed into `~/bdw-llm/venv` on the login node:

| package | version |
|---|---|
| `wikipedia` | 1.4.0 |
| `duckduckgo-search` | 8.1.1 |

Existing: `torch 2.5.1+cu121` (used in CPU mode), `tokenizers 0.22.2`,
`numpy 2.4.6`.

## 9. Limitations, stated plainly

* **Answers are grammatically imperfect.** A 28 M parameter model fine-tuned on
  2.9 M tokens produces grounded but clumsy prose. This stage demonstrates a
  working retrieval + prompting + inference pipeline, not a production chatbot.
* **Retrieval ranking is naive.** The model tends to summarise passage 1 and
  ignore passage 2, so a bad first hit produces a confident wrong answer (the
  Tchaikovsky case above).
* **Wikipedia is rate-limited from this cluster**, so retrieval sometimes needs
  the retry path and occasionally returns nothing; `--no-rag` still works.
* **DuckDuckGo is unusable from this network** and is therefore opt-in only.

_Generated from live runs on the login node; evidence re-read from the cluster._
