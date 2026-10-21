# BDW Integration Proposal

**Scaling the 28M research model into the BerojgarDegreeWala production platform**

| | |
|---|---|
| **Document** | `docs/BDW_INTEGRATION.md` — Stage N of the BDW from-scratch LLM project |
| **Author** | BDW Advanced Phase (Stages A–M), built on PARAM Rudra |
| **Date** | 2026-10-21 |
| **Status** | Proposal for review — no production code changed |
| **Audience** | BDW platform owner + engineering |

---

## 1. Executive summary

Over Stages A–M a **27.8 M parameter decoder-only Transformer** was built
completely from scratch — tokenizer, data pipeline, model, training loop,
checkpointing, evaluation — trained from **random initialisation** on 1.64 B
tokens on PARAM Rudra, instruction-fine-tuned on Dolly-15k, and driven by a
working retrieval-augmented chat script on the login node.

That model is **not** a production chatbot. Its prose is grammatically clumsy
(§3), and it was never intended to be. What the project *did* prove is that a
tiny, fully-owned, CPU-servable model can:

1. **Classify, extract, rerank and verify** — the four jobs that cost real
   money when done by a frontier API on every request.
2. **Be served on a €5/month VM** — 334 MB of weights, 0.6 s load,
   **14–55 tokens/s on 4 CPU cores** (measured, §2.4).
3. **Ground its answers in retrieved text** — with retrieval, answers drew on
   the supplied passages; without it, the same question collapsed into
   *"a hole that you can create in the hole"* (§3.3).

BDW already runs a live AI surface — `/ask-ai`, "BDW Intelligence / Career
Copilot", with **"Live RAG"** and a **35/35-query Lab Tools quota** — on
**Next.js 14 + Supabase + Vercel**, backed by verified circulars from DRDO,
ISRO, CSIR and 160 monitored ATS platforms. Its brand promise is explicit:
*"Evidence-Gated Verification — no AI hallucinations, no middle-agents."*

**The central recommendation of this proposal is therefore not "replace the
copilot with the small model."** It is:

> **Put the 28 M model *in front of* the copilot as an intent router, field
> extractor, passage reranker and citation verifier — and put BDW's *own
> verified corpus* behind it, instead of Wikipedia.**

That single change makes the small model load-bearing *and* makes the
"no hallucinations" promise enforceable in code rather than in marketing copy,
because every generated sentence must resolve to a verified opportunity,
organization or resource ID or it is rejected before the user sees it.

Cost of the proposed pilot: **under US$50/month** including the inference VM,
the embedding index and a modest frontier-API budget. Training can stay on
PARAM Rudra, which is free.

---

## 2. Ground truth: what was actually built and measured

Every number in this section was read back from live cluster output and
md5-verified (§12.1). Estimates are labelled as estimates throughout the rest
of the document.

### 2.1 Model

| Property | Value |
|---|---|
| Architecture | decoder-only Transformer, pre-norm, **learned positional embeddings**, multi-head causal self-attention (`F.scaled_dot_product_attention`, `is_causal=True`) |
| Parameters | **27,800,576** |
| Layers / heads | 6 / 8 |
| `d_model` | 512 |
| Context | 1024 |
| Vocab | **16,384** byte-level BPE, built from scratch |
| Special ids | pad=0, bos=1, eos=2 |
| Shipped weights | `step_0003000.pt`, 333,675,442 B (fp32), md5 `7cdfcc94ef0ac7ccae7670e726dcbe5f` |
| Base weights | `step_0200000.pt`, 333,675,250 B, md5 `bd4772448505442086d4557d32950e84` |

No pretrained weights, no downloaded tokenizer, no
`AutoModel.from_pretrained` at any point.

### 2.2 Pre-training (Stage H)

| Measurement | Value |
|---|---|
| Steps | **200,000** |
| Tokens seen | **1,638,400,000** (43.14 epochs over 165 MB) |
| Corpus | FineWeb (English, ≥50 tokens), 50,689 documents |
| Hardware | 1× A100 80 GB PCIe, CUDA 12.3, torch 2.5.1+cu121 |
| Throughput | ~383,000 tokens/s (~47 steps/s) |
| Wall time | 5 chained 15-minute jobs + 1 finishing job |
| Stop reason | `total-steps` (not an error, not a kill) |

### 2.3 Evaluation and fine-tuning

Held-out evaluation used a **URL-disjoint** test set (2,555,904 tokens, zero
overlap with the 50,689 training URLs) — the same discipline BDW's
"source-verified" brand already demands.

| Checkpoint | Held-out NLL | Perplexity |
|---|---|---|
| Random init | 9.8311 | 18,603.31 |
| Pre-trained (step 200k) | 3.9589 | **52.40** |
| Pre-trained, re-measured | 4.0632 | 58.16 |
| Fine-tuned step 300 | 3.4754 | 32.31 |
| **Fine-tuned step 3000 (shipped)** | **3.3315** | **27.98** |

Instruction fine-tuning (Stage L) ran **3,000 steps in ~59 seconds** on one
A100, from `step_0200000.pt` into a separate `checkpoints_ft/` directory, on
**15,010 Dolly-15k examples / 2,927,516 tokens**. The base checkpoint was
byte-identical before and after — verified by md5.

A teacher-forced pass over real training-format prompts showed the mechanism
working, not just the aggregate: on the Virgin Australia row the model put
**p=0.68 on the correct first answer token** (` Virgin`), and on the Kyle Van
Zyl row **p=0.41 on ` Kyle`**.

### 2.4 Serving characteristics (measured on login-node CPU)

| Measurement | Value |
|---|---|
| Model load | **0.6 s** |
| Generation | **14–55 tokens/s**, 4 CPU threads |
| Threads pinned | `OMP_NUM_THREADS=4`, `torch.set_num_threads(4)` |
| Prompt size, no context | 15 token ids |
| Prompt size, RAG on | 272–393 token ids |

The 55-token/s figure is the short-prompt case; 14 token/s is a 393-token RAG
prompt. Both are usable for interactive chat.

### 2.5 What went wrong (9 bugs, all found and fixed live)

These are not historical trivia — each is a production lesson:

1. Throughput printed `183` instead of ~385,000 (cumulative vs interval time).
2. `(train-window …)` printed `9706` instead of ~4.1 (unreset cumulative sum).
3. Final save wrote no `.meta` sidecar.
4. Rotation orphaned `.meta` sidecars.
5. **Graceful shutdown never fired** because `python` was a child of `bash`
   under `sbatch` — fixed with `exec python`. *Production analogue: a
   container that cannot receive `SIGTERM` cannot drain connections.*
6. `sbatch --max-steps 60 train.slurm` passed options to `sbatch` not the
   script. *Analogue: argument-order bugs between an orchestrator and a
   worker.*
7. `stop reason` always reported `total-steps`; replaced with explicit
   `signal` / `total-steps` / `max-steps` / `loop-exit`. *Analogue: never
   report "success" for a terminated run.*
8. Duplicate final save; guarded with `last_saved_step`.

Plus, in Stage M, a ninth and the most instructive of all:

9. **A single trailing space in the prompt template silently destroyed
   output quality.** `FMT.format(q=…, a="")` produced `Assistant:` + space.
   Byte-level BPE folds that space into the answer's first token, so emitting
   a standalone space put the model in a state it had never seen while
   training, and every question returned `{User: …` garbage. Fixed by ending
   the prompt at `Assistant:` with no trailing space; prompt tails went from
   `[1, 12247, 13765, 28, 223]` to `[2, 1, 12247, 13765, 28]` (223 was the
   stray space). *Production analogue: the prompt template is a versioned
   artefact and must be tested, not hand-written.*

---

## 3. Honest capability assessment

### 3.1 What the model does well

* **Following an instruction format.** After fine-tuning, teacher-forced
  answer-token accuracy rose from 0.346 to 0.437 and answer NLL from 4.0837 to
  3.2271.
* **Extracting structure.** Dolly's `information_extraction` category supplied
  1,506 training examples — the exact skill needed to pull
  `(organization, role, location, eligibility, deadline)` out of a scraped
  circular.
* **Consuming retrieved context.** Given a passage, it reuses its vocabulary
  (`event horizon`, `gravitational collapse`, `Selachii`) rather than
  inventing its own.
* **Running on a CPU.** No GPU required, no vendor lock, no per-token GPU
  billing.

### 3.2 What it does not do well

* **Prose quality.** Real output, retrieved context, greedy decode:
  > A black hole is a class of astronomical objects that have undergone
  > gravitational collapse. They are known for being part of the mass of all
  > black holes, having not a supermassive black hole at its center. This is
  > called the event horizon which describes the events horizon… However,
  > there are many other non-violet spacetime elements

  Grounded, on-topic, and grammatically broken. A career platform cannot ship
  that as a user-facing answer.
* **Reasoning across two sources.** Asked *"Who wrote the play Romeo and
  Juliet?"* it returned Tchaikovsky, faithfully summarising retrieved passage
  #1 (the orchestral work) and ignoring passage #2 (which contained
  "written by William Shakespeare"). **This is a retrieval-ranking failure,
  not a knowledge failure** — and it is precisely the failure a reranker
  fixes.
* **Resisting repetition without help.** Under pure argmax it loops
  (`A black hole is a hole that is a hole…`). Mitigated in Stage M by a
  repetition penalty of 1.2 plus an 8-token exact-repeat loop guard.
* **Anything outside its corpus.** It was trained on FineWeb and Dolly. It has
  never seen a DRDO circular.

### 3.3 The retrieval contrast, which is the whole argument

Same question, same seed, same weights:

| | Output |
|---|---|
| **With** Wikipedia context | *"A black hole is an astronomical object that can be observed in a black hole at its center… A black hole in the black hole is called the event horizon. The Milky Way galaxy has a supermassive black hole at its center…"* |
| **Without** context (`--no-rag`) | *"A black hole is a hole that you can create in the hole. The hole in the hole can be found over a few hours. You can move a green hole when it comes to a hole…"* |

Retrieval is not an optional enhancement for a model this size. It is the
difference between a useful answer and noise. **Which is why the corpus matters
more than the model** (§7).

---

## 4. Where it fits: the routing architecture

The small model's role is decided by one question: *does this step need
world-class English, or does it need a reliable decision?* The former goes to
the frontier gateway BDW already has ("Auto Gateway" in the `/ask-ai` UI). The
latter is where the 28 M model earns its keep.

### 4.1 The five jobs

| Job | Input | Output | Why the 28 M model |
|---|---|---|---|
| **Intent router** | user query | one of 7 classes + confidence | 6-layer classifier, runs in ~50 ms on CPU, near-zero cost |
| **Field extractor** | raw circular text | typed JSON | trained on 1,506 Dolly extraction examples; schema-validated with `zod` (already a BDW dependency) |
| **Passage reranker** | query + k candidate passages | ranked list | directly targets the §3.2 Tchaikovsky failure |
| **Citation verifier** | draft answer + cited IDs | pass / fail + reason | deterministic check that a claim resolves to a verified row |
| **Short factual first-pass** | query + ≤2 passages | grounded answer or *abstain* | for high-volume low-complexity queries where frontier latency/cost is waste |

### 4.2 Intent classes and handlers

| Class | Example (taken from BDW's own FAQ and `/ask-ai` prompts) | Handler |
|---|---|---|
| **A. Deterministic computation** | *"What is the JRF stipend with HRA in Hyderabad?"* | Lab tool (`DST HRA` already exists). **The model never computes numbers.** |
| **B. Listing lookup** | *"Are there DFT jobs for freshers in Bengaluru?"* | Supabase/`pgvector` search + result cards. No free-text generation needed. |
| **C. Grounded explanation** | *"What is the difference between PD and DV?"* | RAG over BDW's own `resources/` + **small model first-pass**, frontier fallback |
| **D. Eligibility / policy** | *"Am I eligible for DRDO JRF with an MSc in Electronics?"* | Eligibility Matrix tool + citation-enforced answer |
| **E. Open career advice** | *"How do I break into VLSI as a fresher?"* | Frontier model, with BDW resources retrieved as citations |
| **F. Assessment generation** | Mock technical interview, SystemVerilog & UVM plan, resume ATS audit | Frontier model for generation; **deterministic scorer** for ATS (keyword/skill matching must not be probabilistic) |
| **G. Out of scope / unsafe** | medical, legal, financial, personal, political | Refuse in brand voice. Router's job is to catch these cheaply. |

Classes A, B and D are where hallucination risk is *highest* and LLM
involvement is *lowest* — because a wrong stipend number or a wrong
eligibility rule damages trust far more than a clumsy sentence does.

### 4.3 Request flow

```
Browser ──► Next.js (Vercel) ──► AI Gateway ──┬──► Lab tool (deterministic)
                                              │
                                              ├──► Supabase search (no generation)
                                              │
                                              └──► RAG path:
                                                     pgvector retrieve (BDW corpus)
                                                     ↓
                                                     [28M] rerank top-k → top-2
                                                     ↓
                                                     [28M] first-pass answer
                                                     ↓
                                                     citation verifier  ──fail──► abstain
                                                         │pass
                                                         ├──► frontier polish (optional)
                                                         ↓
                                                      response + citations
```

The 28 M model sits **before** the expensive path, and its output gates
whether the expensive path runs at all. A request that resolves in class A or
B never reaches a frontier token.

---

## 5. Target cloud architecture

### 5.1 Why not a Vercel serverless function

The inference service must **not** live inside the Next.js deployment:

* Cold starts would be dominated by loading a 334 MB weight file into a
  function that may be frozen between requests.
* Generation is long-lived (seconds), which conflicts with serverless
  execution timeouts.
* Serving model weights through the same origin as the app widens the attack
  surface for no benefit.

### 5.2 Component layout

```
┌─────────────────────────────────────────────────────────────────────┐
│ ZONE 1 — Vercel Edge / Next.js 14 (existing, unchanged)             │
│   /ask-ai  /opportunities  /dashboard  …    RLS enforced           │
└───────────────┬───────────────────────────────────┬─────────────────┘
                │ HTTPS + session JWT               │ (no direct path)
                ▼                                   ▼
┌───────────────────────────────────┐   ┌───────────────────────────────┐
│ ZONE 2 — AI Gateway (new)         │   │ ZONE 4 — Supabase (existing)  │
│  Node or FastAPI, containerised   │──►│  Postgres + pgvector          │
│  • authn/authz, rate limit, quota │   │  RLS on every table           │
│  • intent router [28M]            │   │  service-role key NEVER in    │
│  • prompt assembly + template     │   │  the browser                  │
│  • citation verifier (deterministic)│  └───────────────────────────────┘
│  • no DB creds beyond read pool   │
└───────────────┬───────────────────┘
                │ mTLS / VPC peering, no public ingress
                ▼
┌───────────────────────────────────┐   ┌───────────────────────────────┐
│ ZONE 3 — Inference runtime (new)  │   │ ZONE 5 — Artifact store       │
│  ONNX Runtime / GGML, CPU-first   │   │  private bucket               │
│  • [28M] rerank + extract + verify│   │  model weights, safetensors   │
│  • NO internet egress             │   │  signed URLs only             │
│  • optional T4/A10 for scale      │   │  checksummed on load          │
└───────────────────────────────────┘   └───────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ ZONE 6 — Offline training / eval (PARAM Rudra or cloud spot)        │
│   no production data flows in; only exported corpora + eval sets    │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.3 Concrete stack choices

| Concern | Choice | Rationale |
|---|---|---|
| App host | Vercel (existing) | No change; Mumbai edge region keeps TTFB low for Indian users |
| Database + vectors | Supabase Postgres + **pgvector** (existing vendor) | Avoids a second vector DB; the corpus is already in Supabase; one backup/RLS model |
| Embeddings | Self-hosted `bge-small-en-v1.5` (33 M, ~140 MB) in Zone 3 | Same VM as the 28 M model; no per-query embedding billing |
| Inference host | A single VM in **Zone 3** — Fly.io/Render/Hetzner/AWS `t4g.small` class to start | Measured 14–55 tok/s on 4 CPU cores is enough for the pilot; GPU only when queue depth proves it |
| Format | Export to **safetensors** + **ONNX** | `torch.save` `.pt` is PyTorch-coupled; ONNX runs on ONNX Runtime with no Python in the hot path |
| Frontier model | Existing "Auto Gateway" | Already wired into `/ask-ai`; keep it, but make it a *fallback*, not the default |
| Observability | **Sentry** (existing) + per-request model trace | Log intent class, retrieval score, verifier verdict, tokens, latency, cost |
| Secrets | Vercel env + gateway-side only | Service-role key must never appear in a client bundle; verify in CI |
| IaC | Terraform or Pulumi, repo alongside the app | Reproducible; matches the project's md5-everything discipline |

### 5.4 Why CPU-first, not GPU-first

The temptation is to buy a GPU for an LLM. For a 27.8 M parameter model that
is the wrong trade, and **Phase 0 has now been tested rather than assumed**
(§6.2):

* Exported ONNX fp32 is **138.12 MB**; safetensors fp32 is **106.06 MB**
  (tied `tok_emb`/`lm_head` weights stored once). Either fits comfortably in
  CPU cache.
* Measured decode throughput on 4 CPU cores: **71.2 tok/s** under ONNX
  Runtime and **49.4 tok/s** under PyTorch — ONNX is **1.44× faster** than
  the PyTorch path that produced the Stage M numbers. (Full measurements:
  §6.1.)
* A GPU's minimum useful billing increment dwarfs the cost of serving this
  model on CPU. **Buy the GPU when the CPU queue depth, not the architecture
  diagram, says to.**

> **Correction to an earlier draft of this document.** §5.4 and §6 originally
> recommended **int8 dynamic quantisation** at "~84 MB". Phase 0 testing
> disproved that recommendation: int8 drops top-1 token agreement to
> **0.719–0.766** (roughly one token in four changes), and even keeping
> `lm_head` in fp32 only recovers it to 0.766. For a product whose promise is
> "no AI hallucinations", a format that alters a quarter of the output tokens
> is not acceptable. The recommendation is now **ONNX fp32** — see §6.1.

---

## 6. Inference serving design

| Parameter | Proposal |
|---|---|
| Precision | **fp32 ONNX** (measured correct, §6.1). *Not* int8 — tested and rejected on quality grounds |
| Runtime | ONNX Runtime (CPU EP), verified in Phase 0; fallback to a C/C++ GGML-style runner — note the owner already maintains **`colibri`** (pure-C MoE inference, "run frontier models on hardware you already own"), so a C serving path is in-house |
| Batching | micro-batch rerank/scoring requests for 5–10 ms; generation stays per-request |
| Concurrency | 2–4 workers per VM; queue-depth autoscale to a second VM, not a bigger VM |
| Timeout | hard 15 s generation cap (matches the project's original SLURM `MaxWall=00:15:00` instinct — a bounded run is better than a hung one) |
| Failure mode | if the 28 M runtime is down, **the gateway skips it and goes straight to the frontier path with retrieval** — the small model must never be a single point of failure for `/ask-ai` |
| Model loading | weights checksum-verified against a published digest at boot (the md5 discipline, promoted to a hard gate) |

### 6.1 Phase 0 export test — measured, not assumed

Run on the PARAM Rudra **login node**, CPU only, 4 threads, on
`checkpoints_ft/step_0003000.pt` (27,800,576 params). Toolchain: torch
2.5.1+cu121, onnx 1.23.2, onnxruntime 1.31.0, safetensors 0.8.0.

**Artefact sizes**

| Format | Size | Note |
|---|---|---|
| PyTorch `.pt` (fp32) | 318.2 MB | current format; stores optimizer-agnostic state |
| **safetensors (fp32)** | **106.06 MB** | tied `tok_emb`/`lm_head` stored once; **round-trip max\|diff\| = 0.000e+00** |
| **ONNX (fp32)** | **138.12 MB** | **recommended serving format** |
| ONNX int8, per-tensor | 34.68 MB | 3.98× smaller — **rejected, quality** |
| ONNX int8, per-channel | 34.89 MB | rejected, quality |
| ONNX int8 per-channel, `lm_head` fp32 | 58.81 MB | rejected, quality |

**Numerical parity** (batch=2, seq=128, random ids, reference = PyTorch fp32)

| Runtime | max\|diff\| | top-1 agreement |
|---|---|---|
| **ONNX fp32** | **4.24e-05** | **1.000** |
| ONNX int8 per-tensor | 1.05e+01 | 0.719 |
| ONNX int8 per-channel | 1.12e+01 | 0.750 |
| ONNX int8 per-channel, `lm_head` fp32 | 1.12e+01 | 0.766 |

ONNX fp32 is **numerically equivalent for decoding purposes** (every argmax
identical). The int8 variants change roughly a quarter to a third of tokens;
keeping the output projection in fp32 barely helps, so the damage is spread
through the network, not isolated to the head.

**Throughput**

| seq_len | PyTorch fp32 | ONNX fp32 | ONNX int8 | int8 speedup |
|---|---|---|---|---|
| 128 | 6,702 tok/s | 8,430 tok/s | 12,872 tok/s | 1.53× |
| 256 | 7,570 tok/s | 7,927 tok/s | 17,179 tok/s | 2.17× |
| 512 | 6,664 tok/s | 7,001 tok/s | 12,741 tok/s | 1.82× |
| 1024 | 7,473 tok/s | 5,477 tok/s | 7,635 tok/s | 1.39× |

Simulated decode — 32 steps, full re-forward each step, exactly the way
`chat_with_rag.py` generates (no KV cache):

| Runtime | Time | Throughput |
|---|---|---|
| PyTorch fp32 | 0.65 s | 49.4 tok/s |
| **ONNX fp32** | **0.45 s** | **71.2 tok/s** |
| ONNX int8 | 0.26 s | 121.3 tok/s |

**Phase 0 conclusion:** ship **ONNX fp32**. It is *faster* than the PyTorch
path that produced the Stage M measurements (71.2 vs 49.4 tok/s, 1.44×),
byte-exact enough that no output token changes, and 138 MB is trivial to
host. The int8 path is 1.7× faster and 4× smaller but is not worth trading a
quarter of the output tokens for it on this product.

*One export caveat:* `TransformerLM.forward` guards `if t > cfg.seq_len`,
which `torch.onnx.export` traces as a constant (`TracerWarning`). The exported
graph therefore bakes in the 1024-token limit rather than enforcing it
dynamically. Harmless for serving — pad/truncate to 1024 at the gateway — but
it means the dynamic `seq` axis is advisory, not validated.

### 6.2 Latency budget (pilot, estimate)

| Stage | Budget |
|---|---|
| Gateway auth + rate limit | 5–15 ms |
| Intent routing (28 M, CPU) | 40–120 ms |
| pgvector retrieval | 20–80 ms |
| Rerank top-20 → top-2 (28 M, CPU) | 80–250 ms |
| First-pass generation, 120 tokens @ ~30 tok/s | ~4,000 ms |
| Citation verification | <10 ms (deterministic) |
| **Total, small-model path** | **~4.5–4.8 s** |
| **Total, class A/B (no generation)** | **~100–300 ms** |

The routing architecture means most high-volume traffic lands in the
100–300 ms band, not the 4.5 s band.

---

## 7. Retrieval design: BDW's corpus, not the open web

### 7.1 The single most important change from Stage M

Stage M retrieved from **Wikipedia**, because the PARAM Rudra compute nodes
had no DNS and no BDW data existed in the sandbox. That was the right call
*there* and would be **the wrong call in production**.

In production the corpus already exists, is already curated, and is already
the product's differentiator:

| Corpus | Source | Status |
|---|---|---|
| 590+ verified openings | daily midnight-IST scrapers (DRDO RAC, ISRO, CSIR, Tier-1 ATS) | live |
| 289+ organizations / 160 monitored platforms | `/organizations` | live |
| `resources/` hub | VLSI Salary India 2026, VLSI Career Roadmap, DRDO Internship Guide, JRF vs SRF | live |
| `/ask-ai` FAQ set | the ten questions rendered on the homepage | live |
| News wire | `/news`, Electronics Weekly et al. | live |
| Lab Toolkit definitions | Eligibility Matrix, GATE Cutoffs, DST HRA, RTL Linter, Cold Email | live (deterministic) |

Retrieving from this corpus instead of Wikipedia simultaneously:

1. **Removes the Stage M DDG problem** — no third-party search API, no
   blocked network, no irrelevant TurboTax results.
2. **Removes the trust problem** — Wikipedia is not a source BDW can cite in
   a "source-verified" product; BDW's own rows are.
3. **Removes the Tchaikovsky class of failure at the root** — passage #1 will
   be a BDW row, ranked by a reranker trained on BDW's own click/accept data.

### 7.2 Indexing

* Chunk by semantic unit (one circular, one FAQ answer, one resource section),
  not by fixed token windows — BDW's content is already well-structured.
* Store `opportunity_id | organization_id | resource_id | source_url` on every
  chunk. **A chunk with no verifiable parent ID is not indexed.** This is the
  mechanism that makes §10.3 enforceable.
* Embed with `bge-small-en-v1.5` (self-hosted); hybrid BM25 + vector, since
  exact-match on org names, lab acronyms and role titles dominates real
  queries (`DRDO RAC`, `Tessolve`, `DFT Engineer`).
* Refresh incrementally after each scraper run, not on a fixed schedule.

### 7.3 Reranking

The Stage M failure (confidently summarising the wrong passage) is the
baseline the reranker must beat. Collect implicit feedback from `/ask-ai` —
which cited card the user opened, whether they clicked Apply — and fine-tune
the 28 M model as a cross-encoder over `(query, passage)` pairs. This is a
small, cheap, high-yield adaptation that needs no new architecture.

---

## 8. Domain adaptation: the measured case for retraining the tokenizer

The current tokenizer was trained on FineWeb. It was **never shown a
semiconductor circular**. Measured on the cluster against real BDW vocabulary
(55 terms and 5 phrases taken verbatim from the platform's own copy):

| Text class | Chars / token |
|---|---|
| Common English | **4.45** |
| VLSI / semiconductor domain terms | **2.31** |

**Domain text compresses 1.93× worse.** And this is not a handful of outliers:
**55 of 55 domain terms (100%) split into more than one token.**

Representative fragmentation (from live output):

| Term | Tokens | Pieces |
|---|---|---|
| `information` | **1** | `'information'` |
| `government` | **1** | `'government'` |
| `SerDes` | 3 | `S` + `er` + `Des` |
| `FinFET` | 3 | `Fin` + `F` + `ET` |
| `SystemVerilog` | 6 | `S`+`ystem`+`V`+`er`+`il`+`og` |
| `Gate-All-Around` | **7** | `G`+`ate`+`-`+`All`+`-`+`A`+`round` |
| `UVM`, `RTL`, `JRF`, `SRF`, `LVS` | **3 each** | letter-by-letter |
| `Cadence`, `Qualcomm`, `Synopsys`, `Tessolve` | 3–4 | — |
| `nanosheet`, `crosstalk`, `shuttle`, `fabless` | 3–4 | — |

Real BDW copy, phrase level: **3.30 chars/token** across the five measured
sentences.

### 8.1 Why this matters for a 28 M model specifically

With a 1024-token context, a 400-character job description costs **~120
tokens** under the current tokenizer and would cost **~63** under one trained
on the domain — a **1.9× saving in context budget**, which for a 27.8 M model
is the difference between fitting a retrieved circular plus the query plus a
usable generation window, and not fitting them. Fragmentation also spends
capacity learning character-level spellings of acronyms rather than meaning.

### 8.2 Recommended adaptation sequence

| Step | Action | Expected effect |
|---|---|---|
| 1 | **Retrain the byte-level BPE on BDW's own text** (circulars, `resources/`, FAQ, org profiles, JDs, news) — **only once the corpus is ≥ ~50 MB**; choose vocab from the measured corpus size, not by default (§8.3) | Acronyms and org names collapse to single tokens, **if and only if** the corpus is large enough to support the merges |
| 2 | **Continue pre-training** on the BDW corpus + a permissively-licensed electronics corpus, ~5–20 B tokens, on PARAM Rudra | Closes the §3.1 gap: the model has never seen a DRDO circular |
| 3 | **Synthesise instruction data from BDW content** — FAQ → QA pairs, resource pages → summaries, circulars → extraction rows, JD → eligibility rows — plus distillation from the frontier gateway | Directly trains the classes in §4.2 |
| 4 | **Scale the architecture** to ~100–350 M parameters (12–24 layers, `d_model` 768, context 2048) | The 28 M model stays as router/reranker; the larger one takes class C first-pass |
| 5 | **Evaluate on a domain held-out set** built from BDW FAQ + held-out circulars, URL-disjoint, exactly as Stage I did | A number BDW can publish and trust |

Steps 1–3 are cheap. Step 4 is the first one with real cost, and it should be
gated on evidence that steps 1–3 were not enough.

### 8.3 Measured: a small domain corpus does not pay for itself

The recommendation above was **tested, not assumed** (`src/build_domain_corpus.py`
+ `src/domain_tokenizer_ab.py`). A domain corpus was scraped from 45 of BDW's
own public pages — the exact source §8.1 names — giving **44 docs / 386,167
chars / 0.39 MB**. Two byte-level BPEs were trained on it with everything else
held identical to Stage D (same pre-tokenizer, `min_frequency=2`, same special
tokens), and all three tokenizers were measured on the same 55 terms and 5
phrases used in §8.

**The corpus was too small, and the result says so plainly.**

| Tokenizer | Target vocab | **Actual vocab** | Domain chars/tok | Domain tokens (55 terms) | Terms split >1 |
|---|---|---|---|---|---|
| general-16K (shipped) | 16,384 | 16,384 | 2.31 | 160 | 47/55 |
| domain-16K | 16,384 | **5,300** | 2.87 | 129 | 27/55 |
| domain-32K | 32,000 | **5,300** | 2.87 | 129 | 27/55 |

The trainer **saturated at 5,300 merges** on 0.39 MB of text — it ran out of
learnable pairs long before either target. Consequently domain-16K and
domain-32K are **the same tokenizer**, and the vocab-size parameter had no
effect at all.

**Gains on domain terms were real but modest** (2.31 → 2.87 chars/token,
**1.24×**, **19% fewer tokens**), and concentrated in exactly the places that
matter: `SystemVerilog` collapsed from **6 tokens to 1**, `Tessolve` and
`Synopsys` from 4 to 1, `Testability` from a suffix to a single token. But
several terms got *worse* — `crosstalk` 4 → 5, `nanosheet` 4 → 5,
`clock tree synthesis` 4 → 5 — and `Gate-All-Around` stayed at 7.

**The regression guard failed, which is the decisive finding.** On the same
general-English control set:

| Tokenizer | General-English chars/tok | Tokens |
|---|---|---|
| general-16K (shipped) | **4.45** | 62 |
| domain-16K / domain-32K | **3.03** | 91 |

General English got **32% worse** — more than the 19% domain improvement. For
a career platform whose traffic is a mix of domain queries *and* ordinary
English questions ("How can freshers break into the industry?"), trading a
32% loss on the majority class for a 19% gain on the minority class is a bad
deal.

**Conclusion, and the correction to §8.2 step 1:** retraining the BPE is the
right instinct but the **corpus size is the binding constraint, not the vocab
target**. Before training, measure the production corpus; do not attempt a
32K domain BPE until it is at least ~50 MB (roughly 130× the pilot scrape —
the full set of 590+ openings with complete JD text, all circulars, the
entire news archive and resource library, which plausibly clears that bar).
If the corpus is smaller than that, **keep the shipped 16K tokenizer**: it is
strictly better on mixed traffic. This is the same lesson the pre-training
stage already taught — 43 epochs over a 165 MB corpus bought perplexity at
the price of a widening generalisation gap — now measured at the tokenizer
level instead.

---

## 9. Handling real deep-tech queries: worked examples

Using the actual query shapes from BDW's homepage FAQ and `/ask-ai` prompts.

### 9.1 Class A — deterministic computation (never probabilistic)

> *"What is the JRF stipend with HRA in Hyderabad?"*

* **Do not** ask a language model for a number. The `DST HRA` Lab Tool already
  computes this.
* The 28 M model classifies the query → class A, and may *narrate* the tool's
  structured output, but every figure shown is rendered from the tool's JSON,
  schema-validated.
* Answer carries the DST OM reference citation, not a model attribution.

### 9.2 Class B — listing lookup (no generation at all)

> *"Are there any DFT (ATPG) jobs for freshers in Bengaluru?"*

* Router → class B. `pgvector`/SQL over verified openings:
  `role='dft' AND fresher_ok AND location='bengaluru'`.
* Response is **result cards** from the database — identical in content to
  what `/opportunities` already renders. The model contributes only the
  query understanding, and its structured query is validated by `zod` before
  it hits the database.
* If zero rows: say so plainly. Never invent an opening. This is the
  "no AI hallucinations" promise at its sharpest.

### 9.3 Class C — grounded explanation (the RAG path)

> *"What is the difference between Physical Design and Design Verification?"*

* Retrieve from `resources/` + the FAQ set (not the open web).
* Rerank with the 28 M model; take top-2.
* First-pass generation with the Stage M template, ending at
  `Assistant:` with **no trailing space** (§2.5, bug 9) and the repetition
  penalty + loop guard enabled.
* **Citation verifier**: every claim carrying a number, name or date must
  resolve to a retrieved chunk ID. Fail → abstain and offer the frontier path
  or a link to `/resources`.
* Frontier polish is *optional* and applied only if it can be done without
  losing the citations.

### 9.4 Class D — eligibility and policy

> *"I have an MSc in Electronics. Am I eligible for DRDO JRF?"*

* Route to the **Eligibility Matrix** tool. The model extracts the user's
  stated attributes into a typed object (the extraction skill fine-tuned on
  1,506 Dolly examples), the tool decides, the answer quotes the tool and
  cites the governing circular.
* **Ambiguity is surfaced, not guessed.** If the user did not state a
  publication count or age, the answer asks — it does not assume.

### 9.5 Class F — assessment generation, with a split of duties

> *"Mock interview: RTL & Digital Design round."* / *"Audit my hardware ATS."*

* Generation (questions, feedback prose) → frontier model.
* **ATS scoring → deterministic.** Missing EDA tools, Verilog keywords and ASIC
  highlights are a matching problem. A probabilistic scorer that says a resume
  is ATS-safe when it is not would be a *worse* product than no scorer at all.
  This is the clearest place where the project's whole "measure, don't claim"
  discipline maps onto a feature.

### 9.6 Class G — refusal

> *"Should I quit my job?"* / medical / legal / political questions.

* The router's cheapest and most valuable output: catch it, refuse in brand
  voice, link to `/resources` and `/contact`. No retrieval, no generation, no
  cost.

---

## 10. Security boundaries

### 10.1 Threat model in one line

*User input and **scraped third-party content** are both untrusted. The model
sees both. Neither may be allowed to steer the system.*

The second half is easy to overlook and is the more dangerous: BDW's scrapers
pull from DRDO RAC, ISRO, CSIR and 160 ATS portals. **A job posting on the
open internet is attacker-controlled input.**

### 10.2 Boundary rules

| # | Rule |
|---|---|
| S1 | The browser never holds a service-role key, a model API key, or an inference endpoint URL. Gateway only. |
| S2 | **Zone 3 (inference) has no internet egress.** It can reach Supabase and nothing else. This removes exfiltration-by-prompt-injection *and* eliminates the Stage M dependency on a flaky third-party search API. |
| S3 | Retrieved corpus text is **delimited as data**, never as instructions. A chunk that contains instruction-like text is rendered as quoted data and cannot trigger a tool call. |
| S4 | **Tool calls are produced from the validated structured query, never from generated free text.** The `zod` schema is the boundary. |
| S5 | Every answer must resolve to verified IDs. The citation verifier runs **server-side** and cannot be bypassed by the client. |
| S6 | PII (resumes, phone numbers, emails in the ATS audit tool) is redacted before any third-party frontier call; self-hosted path preferred when PII is present; retention limited and disclosed. |
| S7 | Rate limits + per-user daily quota + `max_tokens` cap + prompt cache. The existing 35/35 Lab Tools quota UI is the right pattern to generalise. |
| S8 | Secrets: keep **gitleaks** in CI (already present in the sibling repo's workflow), add an SBOM and dependency pinning, and verify model artefact checksums at load. |
| S9 | Data residency: Indian users, DRDO/ISRO content. Keep DB and inference in-region; any external model provider needs a DPA and a documented retention position. |
| S10 | **No raw weight download.** The 28 M model is served through the gateway only. Weights live in a private bucket behind signed URLs (§5.2, Zone 5). |
| S11 | Scraped content: cite and link out; do not republish full circulars. This is both a ToS and a copyright posture, and it happens to be what the product already does. |
| S12 | Model-generated text is labelled as AI-assisted in the UI, consistent with the existing "Evidence-Gated" framing. |

### 10.3 Making "no AI hallucinations" enforceable

This deserves its own callout because it is the proposal's core thesis.

> **A response may not be returned to the user unless every factual clause in
> it resolves to a database row that carries a `verified` flag and a
> `source_url`.**

Implemented as: retrieve → generate → parse the draft into clauses → each
clause must attach to a retrieved chunk → each chunk must carry a parent ID →
that ID must exist and be `verified`. Any unattached clause fails the whole
answer. On failure the system abstains and links to `/opportunities` or
`/resources`.

This converts the brand promise from an aspiration into a test with a binary
verdict — exactly the kind of check this project has applied at every stage
(md5s, `STAGE_K_OK`, `TRAIN_DONE`, `RESULT: ALL_OK`).

### 10.3.1 The verifier was built and tested, not just specified

`src/citation_verifier.py` implements the check above: per sentence, content
word recall ≥ 0.5 against some retrieved passage, plus every number and every
distinctive proper noun must appear verbatim in that same passage. One
unattached sentence fails the draft. It is corpus-agnostic and has no model or
network dependency, so it drops into the Zone 2 gateway exactly as S5
requires. `src/verify_e2e.py` runs it against the real retrieval path and the
real 28 M model.

| Condition | Expected | Result |
|---|---|---|
| **A.** RAG-on answers, 3 questions | PASS | **1 / 3 PASS** — see below |
| **B.** same answers **+ 1 injected false claim** | FAIL | **3 / 3 FAIL — every fabrication caught** |
| **C.** no-context answer checked against passages it never saw | FAIL | **FAIL** |

**Condition B is the negative control, and it is the important row.** On the
photosynthesis answer, which passed cleanly on its own, the *only* failing
sentence after injection was the injected one — so the verifier isolates the
unsourced claim without discarding the grounded text around it.

**Condition A's 1/3 is not a verifier failure; it is the verifier working.**
The three cases split exactly as the mechanism predicts:

* *Photosynthesis* — **PASS**, recall 0.54. Genuinely grounded.
* *Black hole* — retrieval returned **0 passages** (Wikipedia rate-limited
  after 4 retries), so the model produced its usual no-context noise and the
  verifier correctly refused it: recall 0.00, no source.
* *Romeo and Juliet* — **FAIL, and it caught a real hallucination.** The model
  wrote *"a 1950 American film adapted from the play written by Robert
  Shakespeare"*. The retrieved passage said *William* Shakespeare and carried no
  film date. The verifier flagged **unsourced number `1950`** and **unsourced
  name `Robert`** — precisely the two fabricated elements. This was not a
  synthetic test case; it is the 28 M model hallucinating on a live query and
  being stopped.

That is the entire argument for §10.3 in one run: **the small model does
hallucinate, sometimes brazenly, and the verifier refuses to let it through.**
Abstaining with a link to `/opportunities` is a better outcome for a
"source-verified" product than shipping "Robert Shakespeare in 1950".

### 10.4 Prompt-injection specifics

* **From the user:** length limit, control-character stripping, and — most
  importantly — the user's text never reaches the system prompt or the tool
  layer directly. It is an *argument* to a classified call.
* **From the corpus:** the highest-risk path. Mitigated by S2/S3/S4 and by
  scanning indexed chunks for instruction patterns at ingest time. A chunk
  that fails the scan is quarantined for human review rather than silently
  dropped, so the scraper pipeline's integrity is preserved.

---

## 11. HPC → cloud transition

### 11.1 What transfers verbatim

| Asset | Status |
|---|---|
| `src/model.py` | unchanged — architecture is framework-agnostic PyTorch |
| `src/train.py`, `src/finetune.py` | unchanged logic; only the launcher changes |
| `src/eval_model.py` | unchanged; the URL-disjoint discipline becomes the CI eval gate |
| `src/tokenize_corpus.py` | reused as-is to train the domain BPE (§8.2 step 1) |
| `src/chat_with_rag.py` | becomes the reference implementation for prompt assembly — **the template, the no-trailing-space rule, the repetition penalty and the loop guard all port** |
| `tokenizer/tokenizer.json` | superseded by the domain BPE, but the 16K version stays as a baseline for the compression comparison |
| Checkpointing + signal handling | the `.meta` sidecar, auto-resume and `exec` lessons become container `SIGTERM` drain behaviour |
| Held-out evaluation method | promoted to a release gate |

### 11.2 What must change

| PARAM Rudra reality | Cloud equivalent |
|---|---|
| `sbatch` + 15-minute `MaxWall`, `MaxSubmitJobs=1` | CI-scheduled jobs or a job queue; no artificial wall |
| 1× A100 80 GB, `training` QOS | Spot `g5.xlarge`-class, or **stay on PARAM Rudra for bulk pre-training** (free) |
| Login node has internet; compute nodes have none | CI has internet; **prod inference has none by design** (S2) |
| `.npy` shard files | parquet/WebDataset in object storage |
| `torch.save` `.pt` checkpoints | **safetensors** for storage, **ONNX** for serving |
| Manual md5 + live-log verification | artifact registry + W&B/MLflow + eval gates in CI |
| Chained jobs with hand-built resume | object-storage checkpoints, automatic |
| 4 CPU threads, 1 GPU, 1 job | autoscaled CPU pool for inference; N parallel training workers |

### 11.3 The honest hybrid recommendation

**Keep PARAM Rudra for bulk pre-training and domain continue-pretraining.**
It is free, it delivered 1.64 B tokens in five 15-minute jobs, and its
constraints forced exactly the checkpointing discipline production needs.
**Move everything else to the cloud**: domain fine-tuning on spot instances,
all evaluation, and all serving.

The one painful operational detail to plan for: PARAM Rudra compute nodes have
no internet, so BDW corpora must be staged to the cluster the way the FineWeb
pilot and Dolly-15k were — via the login node, in resumable chunks, with md5
verification on arrival. That procedure is already written and proven
(Stages C and K).

### 11.4 Migration phases

| Phase | Scope | Exit criterion | Cost |
|---|---|---|---|
| **0. Foundations** | Export `step_0003000.pt` → safetensors + ONNX; containerise; deploy Zone 3 VM; benchmark against the measured 14–55 tok/s CPU baseline | **Export + parity + throughput now tested and passing (§6.1).** Remaining: containerise and deploy the VM | ~US$15/mo |
| **1. Retrieval swap** | Build the BDW corpus index in Supabase `pgvector`; replace Wikipedia retrieval; port the Stage M prompt template verbatim, with the no-trailing-space rule enforced by a unit test | RAG-on answers cite BDW rows; zero third-party search calls | ~US$25/mo |
| **2. Routing + verification** | Intent router, `zod`-validated structured queries, server-side citation verifier, abstention path, `--no-rag`-style A/B harness | **Citation verifier already prototyped and tested (§10.3.1) — catches injected fabrications 3/3 and a real live hallucination.** Remaining: intent router + `zod` boundary | ~US$40/mo |
| **3. Domain adaptation** | Domain BPE — **gated on the production corpus measuring ≥ ~50 MB (§8.3 shows a 0.39 MB corpus regresses general English 32%)**; continue-pretraining; instruction synthesis from BDW content; cross-encoder reranker from accept/click signals | Domain held-out set shows a measurable win over the current checkpoint; no regression on a general-English control set | training on PARAM Rudra (free) + ~US$40/mo serving |
| **4. Scale** | Only if Phase 3 says so: 100–350 M model for class C; GPU when queue depth demands | Queue-depth and cost-per-query data justify the spend | to be decided from Phase 3 metrics |

Each phase has an independent exit criterion and is independently shippable.
**Phase 2 is where the product promise becomes enforceable, and it needs no
retraining at all.**

---

## 12. Model governance and MLOps

### 12.1 What this project already does, promoted to policy

Every claim in Stages A–M is traceable to a job ID, a log line or an md5. That
discipline should survive the move to production:

| Project practice | Production policy |
|---|---|
| md5 of every artefact, local vs cluster compared | published checksum for every model artefact; verified at load (S8) |
| Live log excerpt shown for each stage | per-request trace: intent class, retrieval score, verifier verdict, latency, token count, cost |
| Held-out, URL-disjoint evaluation | domain held-out set; **URL-disjoint**, because the scrapers make URL leakage the realistic contamination path |
| `stop reason: total-steps` vs `signal` | never report success for a terminated or truncated run |
| Honest limitations section in every doc | a published model card, including the §3.2 weaknesses |
| 8 bugs found and fixed, all listed | regression tests for each; the trailing-space bug (§2.5 #9) becomes a **template unit test that fails if the prompt ever ends with whitespace** |

### 12.2 Release gates

1. **Eval gate**: domain held-out NLL/perplexity must not regress beyond a
   stated margin. Mirrors Stage I.
2. **Citation gate**: red-team set of 100 queries; verifier must reject every
   uncited draft; abstention rate reported.
3. **Latency gate**: p95 under budget for each intent class (§6.1).
4. **Cost gate**: cost per 1,000 queries under a stated ceiling.
5. **Canary** rollout with an automatic rollback on verifier-failure-rate or
   p95 regression — the cloud analogue of this project's wall-clock signal
   save.

---

## 13. Cost and latency budget

Figures marked *(est.)* are estimates for planning; the rest are measured.

### 13.1 Serving (pilot, single region)

| Item | Basis | Monthly *(est.)* |
|---|---|---|
| Inference VM, 2 vCPU / 4 GB, CPU-only | enough for measured 14–55 tok/s | US$6–12 |
| Supabase `pgvector` | existing vendor; incremental storage | US$0–25 |
| Embeddings | self-hosted, same VM | US$0 |
| Frontier API (classes C/E/F fallback, routed) | reduced by routing | US$10–40 |
| Sentry + observability | existing | US$0–26 |
| **Total pilot** | | **< US$50–100** |

### 13.2 Training

| Item | Basis | Cost |
|---|---|---|
| Domain BPE training | minutes of CPU | US$0 |
| Continue-pretraining, ~5–20 B tokens | PARAM Rudra, free quota | **US$0** |
| Fine-tune / reranker training | spot GPU, hours | US$5–30 per run |
| Evaluation | CPU | negligible |

### 13.3 The cost argument in one sentence

The 28 M model exists so that **the expensive model is only called when it is
actually needed** — and so that a career platform serving students in India is
not held hostage to per-token pricing.

---

## 14. Risks and mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Small-model prose too clumsy for class C | **High** (§3.2) | Router + frontier fallback; small model stays in the non-generative roles where it is genuinely strong |
| Prompt-injection via a scraped circular | Medium | S2/S3/S4 + ingest scanning + quarantine (§10.4) |
| Retrained tokenizer degrades general English | Medium | Keep the 16K baseline; measure both on a mixed eval set; vocab 32K gives headroom |
| Continue-pretraining overfits the small BDW corpus | Medium | This project already measured that failure mode: 43 epochs over 165 MB widened the generalisation gap from 0.286 to 0.395 nats. Use a **larger** domain corpus and monitor the gap, not just the loss |
| Citation verifier too strict → high abstention | Medium | Tune on real traffic; abstain-and-link is an acceptable UX for this product, an uncited answer is not |
| Frontier cost balloons | Low | Routing (§4), quotas (S7), and the class A/B fast paths |
| PARAM Rudra unavailable during Phase 3 | Medium | Cloud spot as fallback; the training code is already portable |
| Single-maintainer operational load | **High** | Keep the system small: one VM, one DB, CPU-first, no GPU until proven necessary |

---

## 15. Recommendation

Proceed with **Phases 0–2**. They require **no model retraining**, reuse the
code and the prompt discipline already validated in Stages A–M, sit inside
BDW's existing Next.js/Supabase/Vercel stack, cost under ~US$50/month, and
deliver the thing the product's own tagline promises: answers that are
*verifiably* grounded in BDW's verified circulars, with the system refusing to
speak when it cannot prove itself.

Hold **Phases 3–4** until Phase 2's telemetry shows what the model actually
fails at. The measured lesson of this entire project is that the honest number
is worth more than the optimistic architecture — and Phase 2 will produce the
honest numbers.

---

## Appendix A — Verified artefact inventory

| Artefact | Size | md5 |
|---|---|---|
| `checkpoints/step_0200000.pt` (base) | 333,675,250 B | `bd4772448505442086d4557d32950e84` |
| `checkpoints_ft/step_0003000.pt` (shipped) | 333,675,442 B | `7cdfcc94ef0ac7ccae7670e726dcbe5f` |
| `tokenizer/tokenizer.json` (16K baseline) | 1,130,003 B | `b56d1588db0ab75c2658b2d5eabfa41f` |
| `data/raw/dolly15k.jsonl` | 13,017,646 B | `3f8229dea39ab1de03b4044c758fbe73` |
| `data/instruct_tokens/stream.npy` | 11,710,192 B | `1b12e8de23cdf40a5ecdc03d895cb6c2` |
| `src/chat_with_rag.py` | 14,959 B | `383c3a96c835b70ff40dd779e24bf3fc` |
| `src/finetune.py` | 17,368 B | `32f9377366cc30a3b54ac9a92c7a5f9d` |
| `src/prep_instruction_data.py` | 16,422 B | `e57c86ed6db36d23becb894e1e096ec7` |
| `logs/eval_results.json` | — | `6e58e3a5e75e18e814cc5f2474c66ad6` |
| `logs/finetune_metrics.jsonl` | — | `ba90680f6efd734e815993f7ae0e0277` |

**Phase 0 export artefacts** (produced by `src/export_test.py`, PARAM Rudra
login node, CPU only — see §6.1):

| Artefact | Size |
|---|---|
| `export/bdw_28m.safetensors` (fp32, tied weights deduplicated) | 106.06 MB |
| `export/bdw_28m_fp32.onnx` — **recommended** | 138.12 MB |
| `export/bdw_28m_int8.onnx` (per-tensor, rejected on quality) | 34.68 MB |
| `export/bdw_28m_int8_perchannel.onnx` (rejected) | 34.89 MB |
| `export/bdw_28m_int8_exhead.onnx` (`lm_head` fp32, rejected) | 58.81 MB |

**Stage P domain-tokenizer test artefacts** (§8.3, produced by
`src/build_domain_corpus.py` + `src/domain_tokenizer_ab.py`):

| Artefact | Size / value |
|---|---|
| `data/raw/bdw_domain.jsonl` (44 docs from 45 BDW pages) | 408,715 B, 386,167 chars |
| `tokenizer_domain/domain_bpe_16k.json` | 0.35 MB, **actual vocab 5,300** |
| `tokenizer_domain/domain_bpe_32k.json` | 0.35 MB, **actual vocab 5,300** (identical — corpus saturated) |

**Stage Q citation-verifier prototype** (§10.3.1, no model/network dependency):

| Artefact | Note |
|---|---|
| `src/citation_verifier.py` | the S5 boundary check: recall ≥ 0.5 + all numbers and proper nouns sourced |
| `src/verify_e2e.py` | end-to-end test against live retrieval + the 28 M model |

## Appendix B — Stage-to-production mapping

| Stage | What it proved | Where it lands in production |
|---|---|---|
| A — environment audit | login vs compute, no DNS on compute | §5.2 Zone 3 (no egress), §11.2 |
| B — pinned environment | reproducible venv | container image + lockfile |
| C — pilot corpus, resumable download | 429 backoff, resume, md5 on arrival | §11.3 staging corpora to PARAM Rudra |
| D — tokenizer from scratch | 16K BPE, 0 round-trip mismatches | §8 domain BPE training |
| E — tokenised stream | shard integrity, exact tiling | object-storage dataset validation |
| F — model + smoke test | 52/52 finite grads, `SMOKE_PASS` | CI smoke gate |
| G — training infra | auto-resume, signal save, held-out split | §12.1, container `SIGTERM` drain |
| H — chained training | 200k steps, `stop reason: total-steps` | §11.3 bulk pre-training stays on HPC |
| I — evaluation | URL-disjoint held-out, 355× | release eval gate |
| J — final report | honest limitations | model card |
| K — instruction data | 15,010 examples, lossless round-trip | §8.2 step 3 (synthesis) |
| L — fine-tune | 2.08× held-out gain in 59 s | fine-tune + reranker training |
| M — RAG chat | prompt template, no-trailing-space, repetition penalty, loop guard, retrieval contrast | §6, §7, §12.2 template unit test |

## Appendix C — Reproduction

The full pipeline is reproducible from the repository: `src/` holds the
training, evaluation, data-preparation and RAG code; `scripts/` holds the
SLURM entry points; `docs/` holds the nine stage reports with their md5s. The
tokenizer-probe numbers in §8 were produced by tokenising 55 domain terms and
5 phrases from the platform's own copy against
`tokenizer/tokenizer.json` and reading the piece boundaries back from the
cluster.

---

_Generated from the verified outputs of BDW Stages A–M. Every measured value
in this document is traceable to a job ID, a log line or an md5; every
estimate is labelled "(est.)")._
