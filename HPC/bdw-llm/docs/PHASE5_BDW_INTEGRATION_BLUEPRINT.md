# Phase 5 blueprint - BDW production integration

| | |
|---|---|
| **Document** | `docs/PHASE5_BDW_INTEGRATION_BLUEPRINT.md` |
| **Date** | 2026-11-02 |
| **Status** | **PLANNED** - P5.0 (OpenAI-compatible shim) starts after this document is committed |
| **Upstream** | Phase 4 complete: 5 domain LoRAs, hybrid router, 5 RAG indexes, Supabase domain tables, live gateway |
| **Downstream** | `amitkr26/BerojgarDegreeWala` production (Next.js 14 / Vercel / Supabase) |
| **Result markers** | `P5_SHIM_OK`, `P5_OPENAI_CONTRACT_OK`, `P5_BDW_PROVIDER_CONTRACT_OK`, `P5_LIVE_OK` |

---

## 1. Executive summary

Phase 4 delivered a working domain-aware assistant on PARAM Rudra. Phase 5 turns it
into a production dependency of BerojgarDegreeWala (BDW) without changing BDW's
product surfaces.

The key finding from the BDW repository is that the integration contract already
exists:

* `backend/ai-gateway/src/providers/bdw.ts` is a first-class, OpenAI-compatible
  provider. It is provider **#1** in `DEFAULT_PROVIDER_ORDER`, ahead of Groq,
  Gemini, NVIDIA, OpenRouter, Cloudflare, Bedrock and HuggingFace.
* It is disabled by default (`BDW_AI_ENABLED=false`) and activates when
  `BDW_AI_BASE_URL` points at an OpenAI-compatible endpoint.
* `frontend/src/app/api/ai/chat/route.ts` already implements the BDW persona,
  RAG grounding, seven server-only tools, citations, caching and rate limiting.
* `project-bible/architecture/INTEGRATION_ARCHITECTURE.md` already names
  provider #1 as "BDW Custom Silicon LLM (Local / Param Rudra)".

Therefore Phase 5 is not a greenfield integration. It supplies the missing
production inference surface, runs it on a GPU host, and routes technical
questions to it while keeping BDW's existing career/opportunity RAG intact.

**PARAM Rudra is not a production host.** It is firewalled, subject to a
15-minute QOS wall on GPU nodes, and has no public ingress or SLA. It remains
the training, evaluation and artifact-build environment. Production inference
moves to a dedicated GPU host running vLLM; a CPU llama.cpp stack remains the
offline/dev fallback.

---

## 2. Verified BDW integration surface

Read from the private repository at commit `7c03a519d0c73b52675e3074f8dc859bac5dc564`
(GitHub API/webfetch return 404; authenticated `git` access works).

### 2.1 Provider contract (`backend/ai-gateway/src/providers/bdw.ts`)

| Item | Value |
|---|---|
| Enable flag | `BDW_AI_ENABLED=true` |
| Base URL | `BDW_AI_BASE_URL` (OpenAI-compatible root, typically `https://host/v1`) |
| Model | `BDW_AI_MODEL` (default `bdw-career-ai`) |
| Auth | `BDW_AI_API_KEY` as `Authorization: Bearer <key>` |
| Timeout | `BDW_AI_TIMEOUT_MS` (default `30000`) |
| Health check | `GET {base}/models` must return 2xx |
| Chat call | `POST {base}/chat/completions` with `{model, messages, max_tokens: 2048, temperature: 0.3}` |
| Response read | `choices[0].message.content` must be a string |
| Failover | Any error/5xx/429/timeout places the provider in a 60 s cooldown and falls through the chain |

### 2.2 Chat orchestrator (`frontend/src/app/api/ai/chat/route.ts`)

* Authenticated and anonymous paths; anonymous guests are limited to 15 queries/hour/IP.
* `BDW_AI_ENABLED=true` + admin Supabase configured selects `handleBDWChat`
  (RAG + tool loop); otherwise the legacy grounded path is used.
* Responses already carry `answer`, `opportunities`, `sources`, `domain`,
  `provider`, `model`, `grounded`, token estimates and freshness metadata.
* `/ask-ai` already renders sources and a provider/model line.

### 2.3 Consequences

1. No new BDW backend is required to prove the connection.
2. The shim must expose `/v1/models` and `/v1/chat/completions` (not `/ask`).
3. Domain/confidence/adapter/citations are additive metadata; BDW reads only
   `choices[0].message.content`, so extra fields are backward compatible.
4. The current 30 s provider timeout cannot cover CPU generation (~67 s observed).
   Staging must raise `BDW_AI_TIMEOUT_MS`; production on GPU must meet the SLO.

---

## 3. Target architecture

```text
BerojgarDegreeWala (Next.js 14 on Vercel)
  |
  |  /api/ai/chat  (existing RAG + tools + citations)
  |      |
  |      +-- technical/hardware intent ------------------------------+
  |      |                                                           |
  |      +-- career/opportunity intent -> existing BDW RAG/tools     |
  |                                                                  v
  |                                             BDW Inference Service (GPU host)
  |                                               FastAPI shim (:8090, HTTPS)
  |                                                 - API-key auth, quotas, SSE
  |                                                 - OpenAI /v1 surface
  |                                                 - hybrid domain router
  |                                                 - domain RAG (Supabase)
  |                                                 - citation verifier
  |                                                 - request/timing logs
  |                                                       |
  |                                                       v
  |                                             vLLM (:8000, private)
  |                                               base 7B + 5 PEFT LoRAs
  |                                               per-request adapter selection
  |
  +-- provider fallback chain: Groq -> Gemini -> OpenRouter -> ...
                                             |
                                             v
                              Supabase production DB1
                                p4_domain_math/vlsi/embedded/cs/aiml
                                p4_domain_* RPCs, service-role only
                              Neon (analytics / ai_usage_log)
                              Object storage (versioned adapters + RAG indexes)
```

### 3.1 Request flow (technical path)

1. BDW's AI gateway calls provider `bdw` first.
2. Shim authenticates the bearer key and validates the OpenAI request.
3. Shim extracts the last user message, optional system prompt and history.
4. Router classifies the question into math/vlsi/embedded/cs/aiml/general.
5. Domain RAG retrieves from the matching Supabase table (or local npz fallback).
6. Prompt = optional external system prompt + domain prefix + grounding
   instructions + numbered context + history + question.
7. vLLM generates with the matching LoRA adapter (or the base model).
8. Citation verifier strips out-of-set `<cite>` tags.
9. Shim returns OpenAI `choices[0].message.content` plus a `bdw` metadata object.
10. BDW keeps its existing sanitizer, link allowlist, caching and telemetry.

### 3.2 RAG ownership (no duplicate retrieval)

| Query class | Retrieval owner | Reason |
|---|---|---|
| Opportunities, organizations, eligibility, deadlines, news | BDW `bdw-rag.ts` + tools | Structured BDW data and live records |
| Math, VLSI, embedded, CS, AI/ML concepts | BDW inference service | Domain indexes + LoRA specialization |
| Mixed (e.g. "how do I prepare for a VLSI role") | Both, merged citations | Career intent plus technical grounding |

BDW's existing `isOpportunityIntent`/`detectDomain` helpers can drive the split.
The shim must not query BDW's `bdw_chunks` for technical questions, and BDW must
not inject opportunity records into pure technical prompts.

---

## 4. Architecture decisions

### ADR-1 - Dedicated GPU host, not PARAM Rudra

Production inference runs on a GPU host (AWS g5/g6, Azure, or managed GPU).
PARAM Rudra keeps training, evaluation, artifact builds and offline validation.
Reasons: firewall/direct-tcpip restrictions, 15-minute QOS, login-node policy,
no public ingress, no SLA.

### ADR-2 - vLLM for production, llama.cpp as fallback

vLLM provides native multi-LoRA, continuous batching, OpenAI-compatible
streaming and Prometheus metrics. It consumes the existing PEFT adapter
directories directly, so five adapters do not require five merged models.
llama.cpp remains the CPU/offline fallback and the current staging stack.

### ADR-3 - Keep the OpenAI contract

`/v1/models` and `/v1/chat/completions` are the only required endpoints. This
lets `providers/bdw.ts` work unchanged and keeps future clients portable.
Domain metadata is additive, never required.

### ADR-4 - Stream by default, non-stream for compatibility

BDW's current provider is non-streaming, so P5.0 must support both. SSE uses
standard `chat.completion.chunk` events and `[DONE]`. In P5.0 the answer is
chunked after generation; true token streaming lands with vLLM in P5.1.
This keeps the router, RAG and citation verifier on one code path initially.

### ADR-5 - Production data is separate from research data

The Phase 4 Supabase project is a research/dev project. Production applies
migration `0003_p4_domain_chunks.sql` to BDW's primary Supabase, seeds the
3,732 rows, enables service-role-only RLS, verifies parity, and then rotates
the research keys.

### ADR-6 - Auth at the edge and per-user identity

The shim requires a bearer key. BDW passes the end-user identity in
`metadata.user_id` (P5.3). Until then, the shim uses `X-BDW-User-Id` or a
shared API identity with a high limit; BDW's own per-user/IP rate limiter
remains the primary abuse control.

### ADR-7 - Fail closed, fail over fast

If the shim is unhealthy, times out, or returns a low-confidence general
answer for a clearly technical query, BDW falls through to Groq/Gemini.
The shim never serves unverified citations; the verifier strips them.

---

## 5. API contract (P5.0)

### 5.1 `GET /v1/models`

Auth: bearer key. Response:

```json
{
  "object": "list",
  "data": [
    {"id": "bdw-career-ai", "object": "model", "created": 1730000000, "owned_by": "bdw"},
    {"id": "bdw-math", "object": "model", "created": 1730000000, "owned_by": "bdw"},
    {"id": "bdw-vlsi", "object": "model", "created": 1730000000, "owned_by": "bdw"},
    {"id": "bdw-embedded", "object": "model", "created": 1730000000, "owned_by": "bdw"},
    {"id": "bdw-cs", "object": "model", "created": 1730000000, "owned_by": "bdw"},
    {"id": "bdw-aiml", "object": "model", "created": 1730000000, "owned_by": "bdw"}
  ]
}
```

`bdw-career-ai` and unknown IDs auto-route. `bdw-<domain>` and `lora_<domain>`
force the adapter/domain for testing and future model selectors.

### 5.2 `POST /v1/chat/completions`

Request (OpenAI-compatible, extra fields ignored):

```json
{
  "model": "bdw-career-ai",
  "messages": [
    {"role": "system", "content": "You are BDW..."},
    {"role": "user", "content": "Why do clock domain crossings cause metastability?"}
  ],
  "max_tokens": 1024,
  "temperature": 0.0,
  "stream": false,
  "metadata": {"user_id": "uuid", "web": "auto"}
}
```

Response:

```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1730000000,
  "model": "bdw-career-ai",
  "choices": [{
    "index": 0,
    "message": {"role": "assistant", "content": "..."},
    "finish_reason": "stop"
  }],
  "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
  "bdw": {
    "domain": "vlsi",
    "confidence": 0.896,
    "adapter": "lora_vlsi",
    "adapter_applied": true,
    "router_reason": "lexical+semantic",
    "citations": [{"index": 0, "title": "...", "url": "...", "verified": true, "source": "domain"}],
    "sources": [{"index": 0, "title": "...", "url": "...", "verified": true, "source": "domain"}],
    "citations_dropped": [],
    "web_used": false,
    "grounded": true,
    "timings": {"total_ms": 0}
  }
}
```

`usage` is estimated from character counts in P5.0 and replaced by vLLM usage
in P5.1. `bdw` is additive; `providers/bdw.ts` ignores it.

### 5.3 Streaming

`stream: true` returns `text/event-stream`:

```text
data: {"id":"chatcmpl-...","object":"chat.completion.chunk","created":...,"model":"...","choices":[{"index":0,"delta":{"role":"assistant","content":""},"finish_reason":null}]}

data: {...,"choices":[{"index":0,"delta":{"content":"..."},"finish_reason":null}]}

data: {...,"choices":[{"index":0,"delta":{},"finish_reason":"stop"}],"bdw":{...},"usage":{...}}

data: [DONE]
```

Heartbeat comments (`: ping`) keep the connection alive while the blocking
router/RAG/LLM work runs. In-band `{"error": {...}}` events report failures
after headers are sent.

### 5.4 Ops endpoints

| Endpoint | Auth | Purpose |
|---|---|---|
| `GET /healthz` | none | liveness: process is up |
| `GET /readyz` | none | readiness: upstream llama-server `/health` reachable |
| `POST /v1/classify` | bearer | router-only `{text}` -> domain decision (intent split/debug) |

### 5.5 Error envelope

OpenAI-style:

```json
{"error": {"message": "...", "type": "invalid_request_error", "param": null, "code": "..."}}
```

Status mapping: 400 invalid request, 401 auth, 404 unknown route, 429 rate
limit, 502 upstream failure, 504 upstream timeout, 503 not ready.

---

## 6. Security model

* Bearer key on every `/v1/*` route; constant-time comparison; keys never logged.
* `/healthz` and `/readyz` are unauthenticated but bound to the private network.
* Shim listens on a private interface; only the BDW server (Vercel) and ops
  network can reach it. No browser calls, no CORS by default.
* vLLM and llama-server are never exposed publicly; only the shim is.
* Supabase service-role key stays server-side in the inference service.
* Prompt-injection defenses: grounding instructions, citation allowlist,
  out-of-set citation stripping, answer URL allowlist at the BDW layer.
* Per-user quotas at BDW and the shim; body size and message length caps.
* PII: no prompt logging by default; redact user IDs in metrics; retention policy
  documented before production. DPDP Act obligations reviewed with BDW.
* Rotate the Phase 4 research Supabase service key after production migration.
* Secrets in Vercel/Render/host secret stores, never in git or images.

---

## 7. Production data plan

1. Create/confirm the production Supabase project and backup policy.
2. Apply `phase4/supabase/migrations/0003_p4_domain_chunks.sql`.
3. Create the five `p4_domain_*` tables, RPCs, indexes and RLS policies.
4. Seed 3,732 rows (math 736, vlsi 1,235, embedded 582, cs 566, aiml 613).
5. Run parity: 8/8 ID overlap per domain, max delta 0.00000.
6. Verify service-role-only access; anon/authenticated must see nothing.
7. Pin the BGE model and RAG index versions; store checksums in object storage.
8. Add a refresh job for content changes; rebuild embeddings and re-seed.
9. Keep a read-only snapshot of the research project until production parity
   is signed off.

---

## 8. GPU deployment and sizing

| Item | Recommendation |
|---|---|
| GPU | NVIDIA L40S 48 GB or A100 80 GB for multi-LoRA headroom; L4 24 GB for a cost-first pilot |
| Serving | vLLM with `--enable-lora --max-loras 5`, base 7B (4-bit/AWQ or FP16 depending on GPU) |
| Adapters | Existing PEFT `lora_<domain>/final` directories (no GGUF conversion required) |
| CPU router | 2-4 vCPU, 4 GB RAM; BGE-small on CPU is sufficient |
| Replicas | 2 minimum in production; one GPU failure must not take the assistant down |
| Scaling | Queue-depth / TTFT based; warm pool to avoid cold-start timeouts |
| Cost guard | Autoscale to zero in staging; production keeps one warm replica |
| Fallback | Groq/Gemini via BDW's existing provider chain |

Indicative SLOs (lock after P5.1 benchmark):

* TTFT <= 1.5 s (streaming), p95 total <= 10 s for a 300-token answer.
* >= 25 output tokens/s per stream on the selected GPU/quantization.
* Error rate < 1% excluding client errors; availability 99.5% monthly.
* Router p95 <= 20 ms warm; RAG p95 <= 150 ms (Supabase).

---

## 9. P5.0 scope - OpenAI-compatible shim

### 9.1 Deliverables

```text
phase5/__init__.py
phase5/serve/__init__.py
phase5/serve/main.py              FastAPI app, routes, auth, SSE, error envelope
phase5/serve/runtime.py           builds the existing Zone 2 Gateway from env
phase5/serve/requirements.txt     runtime pins (FastAPI, uvicorn, sentence-transformers, torch CPU)
phase5/serve/requirements-dev.txt contract-test pins (pytest, httpx)
phase5/serve/Dockerfile           CPU shim image (vLLM is a separate service)
phase5/serve/tests/fake_gateway.py
phase5/serve/tests/test_openai_contract.py
phase5/serve/tests/test_bdw_provider_contract.py
phase5/serve/tests/contracts/bdw_provider_contract.mjs
.dockerignore                     exclude venvs, models, adapters, indexes, logs
```

### 9.2 Small, backward-compatible gateway changes

`phase3/gateway/app.py`:

* `build_ask_prompt(..., system_prompt=None)` - optional external system prompt
  before the domain prefix.
* `Gateway.ask(..., system_prompt=None, max_tokens=None, temperature=None,
  force_domain=None)` - per-request generation controls and optional forced
  domain for model aliases.
* `Zone3LLM.complete(..., temperature=0.0)` - honor the request temperature.
* `build_gateway(env=None)` - extract the boot wiring from `main()` so the shim
  and the legacy `/ask` server share one construction path.
* Defaults preserve the existing `/ask` behavior; no existing caller changes.

### 9.3 Configuration

| Variable | Default | Meaning |
|---|---|---|
| `P5_PORT` | `8090` | shim listen port |
| `P5_API_KEY` | none | required bearer key when auth mode is `required` |
| `P5_AUTH_MODE` | `required` | `required`, `optional`, `disabled` |
| `P5_MAX_QUESTION_CHARS` | `4000` | user-message cap |
| `P5_MAX_TOKENS_DEFAULT` | `1024` | fallback if request omits `max_tokens` |
| `P5_SSE_CHUNK_CHARS` | `48` | post-generation SSE chunk size |
| `P5_SSE_HEARTBEAT_S` | `10` | SSE keepalive interval |
| `ZONE3_BASE_URL` | `http://127.0.0.1:8080` | llama-server / vLLM upstream |
| `PH4_BGE_DIR` | repo default | BGE-small model directory |
| `P5_RATE_LIMIT_PER_USER_DAY` | inherits `RATE_LIMIT_PER_USER_DAY` | shim quota |

### 9.4 Acceptance criteria

1. `GET /v1/models` returns the six model IDs and passes `healthCheck()` from
   the real `providers/bdw.ts`.
2. `callBDWEndpoint()` from the real `providers/bdw.ts` returns a non-empty
   string against the shim (fake gateway in CI, real gateway on staging).
3. Non-stream response has `choices[0].message.content` and `bdw` metadata.
4. Streaming yields valid OpenAI chunk SSE, concatenates to the same answer,
   and terminates with `[DONE]`.
5. Missing/wrong bearer -> 401 OpenAI error; rate limit -> 429; upstream
   failure -> 502; timeout -> 504.
6. Docker image builds and `/healthz` passes without GPU or model mounts.
7. Existing `phase3/gateway/app.py --self-test` still passes (no regression).

---

## 10. Test plan

### 10.1 Automated (no GPU)

* `test_openai_contract.py` - auth, models, non-stream shape, SSE shape,
  error mapping, forced model aliases, header/user mapping.
* `test_bdw_provider_contract.py` - starts uvicorn with a deterministic fake
  gateway and runs the **actual** `backend/ai-gateway/src/providers/bdw.ts`
  through Node 26 native TypeScript import; asserts `healthCheck()` and
  `callBDWEndpoint()`.
* Existing `phase4/router/integration_test.py` (58/58) and
  `phase3/gateway/app.py --self-test` (6/6) remain green.

### 10.2 Staging (real cluster)

* Deploy the shim next to the running Phase 4 stack (`:8081` llama-server,
  `:8787` legacy gateway, `:8090` shim).
* `curl /v1/models`, `/readyz`, then a real VLSI query through the shim.
* Confirm `P4_DOMAIN` and `P4_ADAPTER` logs, citations, `bdw.adapter`.
* Run the Node provider harness against the staging shim with a raised
  `BDW_AI_TIMEOUT_MS`.

### 10.3 Production gates

* 58-case router battery + golden technical set >= baseline.
* Load test at expected peak with p95 within SLO.
* Security review: auth, RLS, secrets, prompt injection, URL allowlist.
* Canary 5% -> 25% -> 100% with provider fallback rehearsed.
* Rollback: set `BDW_AI_ENABLED=false`; traffic returns to Groq/Gemini.

---

## 11. Phased roadmap

| Phase | Scope | Exit criteria |
|---|---|---|
| **P5.0** (3-5 d) | OpenAI shim, auth, SSE, Docker, pinned deps, contract tests | `P5_SHIM_OK`, `P5_OPENAI_CONTRACT_OK`, `P5_BDW_PROVIDER_CONTRACT_OK` |
| **P5.1** (1-2 w) | GPU host + vLLM base/5 LoRAs, warm pool, TLS, autoscaling, token streaming | SLOs measured; live staging `P5_LIVE_OK` |
| **P5.2** (2-3 d) | Production Supabase migration/seed/parity/RLS/backups | 5 tables live; parity 8/8; keys rotated |
| **P5.3** (3-5 d) | BDW provider metadata, technical intent split, UI badges/citations, feature flag | Canary passes; fallback verified |
| **P5.4** (1 w) | Eval gates, load/security tests, canary, dashboards, runbooks | Error budget met; rollback rehearsed |
| **P5.5** (ongoing) | Feedback flywheel, quarterly LoRA refresh, cost tuning | Each refresh passes eval gate |

---

## 12. Observability and operations

* Structured logs: `P5_REQUEST` (id, route, status, latency, domain, adapter,
  user hash), `P4_DOMAIN`, `P4_ADAPTER`, `P4_DOMAIN_BACKEND`.
* Metrics: request count/latency by route/status/domain, TTFT, tokens/s,
  queue depth, upstream errors, RAG hits/misses, citation drops.
* Dashboards: availability, p50/p95/p99, cost per 1k answers, fallback rate.
* Alerts: readiness failures, 5xx > 1%, p95 > SLO, GPU memory > 90%,
  Supabase RPC failures, adapter load failures.
* Runbooks: restart shim, vLLM, rotate key, disable provider, re-seed index,
  roll back a LoRA, fail over to cloud providers.

---

## 13. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| HPC used as production | Outages, policy violation | Dedicated GPU host; HPC only for training/eval |
| Vercel/BDW 30 s timeout vs CPU latency | Provider marked failed, fallback to generic models | GPU + streaming; raise staging timeout; SLO gate |
| RAG ownership overlap | Conflicting answers/citations | Intent split; one retrieval owner per class |
| LoRA quality drift | Regressions in a domain | Golden eval gate; canary; per-domain rollback |
| Supabase RLS mistake | Data exposure | Service-role-only policy tests; anon denied |
| Prompt injection via retrieved text | Unsafe output/links | Grounding, allowlists, citation verifier, sanitizers |
| Single GPU failure | Assistant unavailable | 2 replicas; warm pool; provider fallback |
| Cost overrun | Budget | Autoscale, quantized model, per-user quotas, cost telemetry |
| Key leakage | Unauthorized inference | Secret stores, rotation, no client keys, audit logs |

---

## 14. Non-negotiables

1. No production traffic through PARAM Rudra login nodes or port 8787.
2. No `service_role` or provider keys in the browser or git.
3. No release without the router/eval gates and a working provider fallback.
4. No unverified citations; the verifier strips out-of-set references.
5. No duplicate RAG: technical vs career intent has one owner per class.
6. No silent model changes: adapters and indexes are versioned and checksummed.

---

## 15. Open items before P5.1

* Select GPU hosting and budget owner.
* Confirm BDW's production Supabase project and migration window.
* Decide whether BDW's `/api/ai/chat` passes `metadata.user_id` from the
  authenticated session (recommended) or the shim uses a shared API identity.
* Confirm data-retention and DPDP review with BDW.
* Pick the production quantization (AWQ/GPTQ vs FP16) after the vLLM benchmark.
* Decide whether the shim or BDW owns the technical-intent classifier; the
  recommendation is BDW (cheap lexical/embedding gate) with the shim as the
  authoritative router for accepted technical queries.
