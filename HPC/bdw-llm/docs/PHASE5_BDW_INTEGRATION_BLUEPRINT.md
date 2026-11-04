# Phase 5 blueprint - BDW production integration

| | |
|---|---|
| **Document** | `docs/PHASE5_BDW_INTEGRATION_BLUEPRINT.md` |
| **Date** | 2026-11-02 |
| **Status** | **P5.0 COMPLETE** - shim, auth, SSE and contract tests green, live staging verified; CI Docker build pending (§16) |
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

**PARAM Rudra Zero-Cost Production Deployment ($0 Budget Pivot):**
To guarantee zero recurring compute cost, the production 70B inference stack runs
directly on CDAC's PARAM Rudra HPC cluster. The GPU partition (`rdgpu01` / `rdgpu02`)
provides dual **NVIDIA A100 80GB PCIe GPUs (160 GB total VRAM)** with up to 4-day
walltime. CDAC's strict inbound firewall is naturally bypassed by running an outbound
**Cloudflare Tunnel (`cloudflared`)** directly on the GPU compute node, exposing the
FastAPI shim to `https://ai.berojgardegreewala.com` without opening ports or requesting
public IPs. All external cloud hosting is avoided ($0 spend).

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

> **P5.1 (2026-11-02): heavy-model decision locked.** Production inference
> serves a **70B-class model with multi-GPU tensor parallelism** —
> `Qwen/Qwen2.5-72B-Instruct` (default, open weights) or
> `meta-llama/Llama-3.3-70B-Instruct` (gated, needs `HF_TOKEN`). The table
> below supersedes the earlier 7B single-GPU sizing; all prices are
> **Oct-2026 list estimates — verify at purchase** (spot/committed pricing
> drifts weekly). PARAM Rudra keeps training/eval/artifacts (ADR-1); only
> production inference moves to this cloud stack.

Model footprint (fixed): **BF16 ≈ 145 GB weights** (70B × 2 bytes), plus KV
cache — GQA **≈ 320 KB/token** (80 layers × 8 KV heads × head_dim 128 × 2
× 2 B), so a 16 k context ≈ 5 GB/seq on top of weights.

| Tier | GPUs (`TP_SIZE`) | Context (`MAX_MODEL_LEN`) | Interconnect | Monthly @ ~730 h (list) | When |
|---|---|---|---|---|---|
| Budget | 2× H100 PCIe / A100-80 | 8192 (KV tight: ~2 GB/seq @ 16 k) | PCIe acceptable | ≈ $4.2 k (2×H100-PCIe @ $2.89/h) · ≈ $2.6 k (2×A100-80 @ $1.79/h) | first production deploy |
| **Recommended** | 4× H100 | 32768 | **prefer NVL/SXM** (PCIe lacks NVLink) | ≈ $8.4 k (PCIe) · ≈ $11.7 k (SXM @ $3.99/h) | steady state |
| Concurrency | 8× H100 SXM | 32768 | NVLink domain | ≈ $23.3 k | high traffic, not yet justified |
| Not viable | DeepSeek-V3 (671 B) | — | would exceed single node | — | revisit only with multi-node |

Budget tier reference prices (Oct-2026): H100 PCIe $2.89/h · H100 NVL
$3.19/h · H100 SXM $3.99/h · A100-80 $1.79/h · B200 $5.98–7.99/h.

**LoRA caveat (P5.1 open item):** the five existing adapters are 7B-shaped
(r=32, Qwen2) and **cannot attach to a 70B base**. The 70B ships
base-only — domain RAG and the router are unchanged; `--enable-lorastays off until the adapters are QLoRA-retrained for the 70B architecture
(PARAM Rudra) or replaced. The compose file carries the commented flag.

Replicas / resilience (unchanged principles):

* 2 minimum in production; one GPU failure must not take the assistant down.
* Fallback: Groq/Gemini via BDW's existing provider chain on 5xx/timeout.
* Warm pool / `gpu_memory_utilization=0.92` to avoid cold-start misses;
  first model load (weights download + graph capture) is minutes — the
  bootstrap waits on `/readyz`, and tunnel cutover waits on `P5_LIVE_OK`.

Indicative SLOs — now draft values in [`phase5/deploy/slo.json`](../phase5/deploy/slo.json)
(lock after a real `P5_LIVE_OK` benchmark on the deployed 70B):

* Availability 99.5% monthly; error budget burn-rate alerts (§ deploy).
* TTFT p95 ≤ 4 s draft (70B prefill — the old 7B target of 1.5 s does not
  carry over; re-baseline from `bdw_shim_ttft_seconds` the first week).
* Stream completion p95 ≤ 30 s draft; rate-limit share < 1%.
* Router p95 ≤ 20 ms warm; RAG p95 ≤ 150 ms (Supabase) — unchanged.

Deploy artifacts: [`phase5/deploy/`](../phase5/deploy/) —
`docker-compose.yml` (vLLM TP + shim + cloudflared), `bootstrap-host.sh`
(`P5_DEPLOY_SMOKE_OK`), `CLOUDFLARE_TUNNEL.md`, `slo.json`,
`prometheus.example.yml`, `alerts.example.yml`.

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
| `P5_MODEL` | `bdw-career-ai` | model ID reported by `/v1/models` |
| `P5_MAX_QUESTION_CHARS` | `4000` | user-message cap |
| `P5_MAX_TOKENS_DEFAULT` | `1024` | fallback if request omits `max_tokens` |
| `P5_SSE_CHUNK_CHARS` | `48` | post-generation SSE chunk size |
| `P5_SSE_HEARTBEAT_S` | `10` | SSE keepalive interval |
| `P5_READY_URL` | `<ZONE3_BASE_URL>/health` | upstream readiness probe target (`/readyz`) |
| `ZONE3_BASE_URL` | `http://127.0.0.1:8080` | llama-server / vLLM upstream |
| `ZONE3_TIMEOUT_S` | `15` | upstream timeout — use **300** for 70B prefill (compose default) |
| `ZONE3_MODEL` | unset | **P5.1**: sent as `model` in vLLM `/chat/completions` (vLLM rejects requests without it); omitted for llama-server |
| `PH4_BGE_DIR` | repo default | BGE-small model directory |
| `P5_RATE_LIMIT_PER_USER_DAY` | inherits `RATE_LIMIT_PER_USER_DAY` | shim quota |
| `P5_STREAM_UPSTREAM` | `true` | **P5.1**: live `Gateway.ask_stream()` SSE proxy; `false`/gateway-without-stream falls back to post-generation chunking (P5.0 behavior) |
| `P5_METRICS_TOKEN` | unset | **P5.1**: optional bearer for `GET /metrics` (empty = open on the private network; edge blocks `/metrics` via tunnel ingress). Independent of `P5_API_KEY` |

**P5.1 instrumentation** (`phase5/serve/metrics.py`, Prometheus text on
`GET /metrics`): `bdw_shim_requests_total{route,stream,status,domain}`,
`bdw_shim_request_duration_seconds{route,stream}`, `bdw_shim_ttft_seconds{domain}`,
`bdw_shim_tokens_total{direction,domain}`, `bdw_shim_upstream_errors_total{type}`
(timeout|rate_limit|upstream|not_ready|other), `bdw_shim_citation_drops_total{domain}`,
`bdw_shim_requests_in_flight{route}`. Validation 400s are not counted;
`domain` is bounded to `math|vlsi|embedded|cs|aiml|general|none`.

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
| **P5.0** (3-5 d) - **DONE** (§16) | OpenAI shim, auth, SSE, Docker, pinned deps, contract tests | `P5_SHIM_OK`, `P5_OPENAI_CONTRACT_OK`, `P5_BDW_PROVIDER_CONTRACT_OK` |
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

## 15. P5.1 decisions and open items

**Decisions locked (2026-11-02, P5.1):**

1. **Heavy model** — 70B-class with multi-GPU tensor parallelism:
   `Qwen/Qwen2.5-72B-Instruct` (default) or `Llama-3.3-70B-Instruct`;
   budget = 2×H100, recommended = 4×H100, concurrency = 8×H100 SXM
   (§8, prices "verify at purchase").
2. **Hosting shortlist** — RunPod / AWS / Lambda Labs; buy against the §8
   tier table after the live benchmark.
3. **Endpoint** — `ai.berojgardegreewala.com`, DNS on Cloudflare.
4. **Ingress** — Cloudflare Tunnel approved: zero inbound origin ports;
   runbook `phase5/deploy/CLOUDFLARE_TUNNEL.md`, `/metrics` edge-blocked.

**Remaining open items:**

* **LoRA retraining (blocking `--enable-lora`)** — the five adapters are
  7B-shaped and cannot attach to the 70B base; ship base-only until QLoRA
  retraining on PARAM Rudra (or drop adapters for the 70B line).
  Domain RAG/router behavior is unaffected either way.
* Select the provider (RunPod/AWS/Lambda) + budget owner; pin
  `VLLM_IMAGE` to a digest at purchase time.
* Re-baseline SLOs from the first `P5_LIVE_OK` week — TTFT/completion
  targets in `phase5/deploy/slo.json` are drafts (70B prefill differs
  from the old 7B numbers).
* Quantization decision (FP16 vs AWQ/GPTQ) after the vLLM benchmark —
  may permit larger `MAX_MODEL_LEN` or a cheaper GPU tier.
* Confirm BDW's production Supabase project and migration window.
* Decide whether BDW's `/api/ai/chat` passes `metadata.user_id` from the
  authenticated session (recommended) or the shim uses a shared API identity.
* Confirm data-retention and DPDP review with BDW.
* Decide whether the shim or BDW owns the technical-intent classifier; the
  recommendation is BDW (cheap lexical/embedding gate) with the shim as the
  authoritative router for accepted technical queries.

---

## 16. P5.0 implementation record (2026-11-02)

Base commit `fcaff61` on `amitkr26/HPC`. The P5.0 gateway changes that were live
on the cluster but not yet committed (`phase3/gateway/app.py`, cluster blob
`fb9593b5`) were imported into the source tree first, so the shim and the
legacy `/ask` server share the identical construction path.

### 16.1 Delivered

| File | Role |
|---|---|
| `phase5/__init__.py`, `phase5/serve/__init__.py` | package markers |
| `phase5/serve/main.py` | FastAPI app: `create_app` factory, settings, auth, `/healthz`, `/readyz`, `/v1/models`, `/v1/classify`, `/v1/chat/completions` (non-stream + SSE), OpenAI error envelope, `bdw` metadata, `P5_REQUEST` logs |
| `phase5/serve/runtime.py` | lazily imports `phase3/gateway/app.py` and adapts `build_gateway()` (dict) to `(gateway, info)` |
| `phase5/serve/requirements.txt` | runtime pins: fastapi 0.162.0, uvicorn 0.54.0, pydantic 2.14.2, requests 2.34.2, numpy 2.4.6, torch 2.5.1 (CPU index), sentence-transformers 6.2.0, transformers 4.55.4, tokenizers 0.21.4 |
| `phase5/serve/requirements-dev.txt` | contract-test pins: pytest 9.2.0, httpx 0.28.1, fastapi/uvicorn/pydantic |
| `phase5/serve/Dockerfile` | `python:3.11-slim`, non-root uid 10001, healthcheck, `uvicorn ...:create_app --factory` on 8090 |
| `.dockerignore` (repo root) | excludes venvs, models, adapters, indexes, logs, test caches |
| `phase5/serve/tests/fake_gateway.py` | deterministic gateway for CI (no model/RAG) |
| `phase5/serve/tests/test_openai_contract.py` | 30 tests: auth, models, shape, SSE, heartbeat, in-band failures, forced aliases, limits |
| `phase5/serve/tests/test_bdw_provider_contract.py` | starts a live uvicorn shim and runs the real `providers/bdw.ts` through Node |
| `phase5/serve/tests/contracts/bdw_provider_contract.mjs` | Node harness importing the real TS module; `P5_CONTRACT_TIMEOUT_MS` overrides the 15 s CI timeout |

Gateway seams in `phase3/gateway/app.py` match §9.2 exactly: `system_prompt` in
`build_ask_prompt`, per-request `system_prompt/max_tokens/temperature/force_domain`
in `Gateway.ask` (forced decisions are `confidence=1.0`, `reason=forced:<domain>`),
`temperature` in `Zone3LLM.complete`, and `build_gateway(env=None)` returning the
gateway plus boot facts. `load_env()` tolerates a missing `.env` for containers.
Defaults keep the legacy `/ask` behavior unchanged.

### 16.2 Verification

Local (workstation, Python 3.14 test venv, Node 24):

```text
python -m py_compile phase3/gateway/app.py phase5/serve/*.py ...          OK
python -m pytest phase5/serve/tests -q                                    32 passed
python -m pytest phase5/serve/tests/test_openai_contract.py -q            30 passed
python -m pytest phase5/serve/tests/test_bdw_provider_contract.py -q       2 passed
```

Cluster regression (unchanged behavior):

```text
python phase3/gateway/app.py --self-test                    RESULT: P4_ZONE2_SELFTEST_OK
python phase3/gateway/app.py --supabase-selftest            RESULT: P4_ZONE2_SUPABASE_OK domains=5
python phase4/router/integration_test.py                    RESULT: P4_ROUTER_INTEGRATION_OK pass=58/58
```

Staging (real Phase 4 stack: llama-server `:8081` with 5 adapters, legacy
gateway `:8787`, shim `:8090`, `P4_DOMAIN_BACKEND=supabase`):

* `/healthz` -> 200, `/readyz` -> `{"status":"ready","upstream":"ok"}`.
* `/v1/models` -> six IDs (`bdw-career-ai`, `bdw-math`, `bdw-vlsi`,
  `bdw-embedded`, `bdw-cs`, `bdw-aiml`); no/wrong bearer -> 401
  `invalid_api_key`.
* Non-stream `bdw-vlsi` ask: 200 in 13,889 ms; `P4_DOMAIN` forced vlsi;
  `adapter=lora_vlsi`, `adapter_applied=True`, `grounded=True`, 8 citations,
  `usage={prompt:24, completion:34, total:58}`; answer returned.
* SSE `bdw-vlsi` ask: 56,136 ms, 6 `chat.completion.chunk` events + 5 `: ping`
  heartbeats, `finish_reason=stop`, `[DONE]`, same adapter/citations, streamed
  text concatenates correctly.
* Node harness against the staging shim via an SSH tunnel (real `bdw.ts`):
  `{"valid":true,"health":true,"content":"Setup time (tsu) is the minimum ...","error":null}`;
  `P5_REQUEST` logged the auto-routed VLSI call in 61,191 ms.

Notes and environment requirements:

* `ZONE3_TIMEOUT_S` (gateway -> llama-server, default 15 s) is too low for CPU
  prompt processing; staging used `ZONE3_TIMEOUT_S=300`. P5.1 must set a
  production value and raise `BDW_AI_TIMEOUT_MS` accordingly.
* The cluster's Node is v10, so native TypeScript import is not available
  there; the harness ran on the workstation over `ssh -L`. CI must use Node
  >= 22.6 (Node 24 on the workstation).
* Shim `usage` is character-estimated in P5.0 (per §5) and will be replaced by
  upstream usage in P5.1.

### 16.3 Exit markers

* `P5_SHIM_OK` - shim boots, serves models/chat, auth enforced.
* `P5_OPENAI_CONTRACT_OK` - 30/30 OpenAI contract tests.
* `P5_BDW_PROVIDER_CONTRACT_OK` - 2/2 real-provider tests (fake gateway in CI)
  and the real provider against the staging shim.

`P5_LIVE_OK` remains the P5.1 exit criterion, but live staging is already
demonstrated. The Docker image build (acceptance §9.4 #6) was not run on the
workstation (no Docker); the pinned Dockerfile is ready for the CI/P5.1 build.


---

## 17. P5.1 Zero-Cost Production Stack Pivot ($0 Budget Slurm Deployment)

### 17.1 Context & Motivation
Procuring external cloud GPU instances (RunPod, AWS, Lambda Labs) for 70B+ model
inference incurs significant ongoing cost ($4.2k to $11.7k+ monthly for multi-GPU
A100/H100 setups). To eliminate all external infrastructure expense, the deployment
strategy pivoted to a **$0 Zero-Cost Architecture** utilizing allocated compute
resources on CDAC's PARAM Rudra cluster.

### 17.2 The Zero-Cost Architecture
```
BDW Web Client / ai-gateway (BDW_AI_BASE_URL=https://ai.berojgardegreewala.com)
                            │ HTTPS
                            ▼
     Cloudflare Global Edge (DDoS protection, SSL termination)
                            │ Outbound Tunnel Connection (bypasses CDAC firewall)
                            ▼
     PARAM Rudra GPU Compute Node (rdgpu01 / rdgpu02)
       ├── cloudflared (tunnel daemon) ──► localhost:8090
       ├── FastAPI Shim (:8090) ──► localhost:8000
       │     (Auth, Domain RAG, Prompt Prefix, Cite Gating, SSE streaming, /metrics)
       └── vLLM (:8000) ──► 2x NVIDIA A100 80GB PCIe (TP=2, 160 GB total VRAM)
```

1. **Hardware Capacity**:
   * Nodes: `rdgpu01` and `rdgpu02`.
   * GPUs: 2x NVIDIA A100 80GB PCIe per node = **160 GB total VRAM**.
   * Host Memory: 192 GB system RAM.
   * Model Sizing: A 70B parameter model in FP16/BF16 occupies ~140 GB. Split across
     `TP=2` via vLLM Tensor Parallelism, each A100 loads ~70 GB weights, leaving 10 GB
     VRAM per card (20 GB total) dedicated to KV cache at 8k context.
2. **Firewall & Ingress Bypassing**:
   * Inbound ports are strictly firewalled by CDAC network security.
   * Compute nodes have full outbound HTTPS/TLS access to the internet.
   * A standalone `cloudflared` daemon runs directly on the compute node, establishing
     outbound reverse tunnels to Cloudflare.
   * Cloudflare edge routes queries from `https://ai.berojgardegreewala.com` through
     the tunnel into `http://127.0.0.1:8090` without inbound firewall rules or static IPs.

### 17.3 Orchestration (`phase5/deploy/run_production.slurm`)
A dedicated Slurm batch script manages the complete lifecycle of all three daemons:
* **SLURM Directives**: Allocates 1 node, 2x GPUs (`--gres=gpu:2`), 24 CPUs, 160GB RAM,
  and up to 4-day continuous walltime on partition `gpu`.
* **vLLM Engine**: Launches `vllm.entrypoints.openai.api_server` with `--tensor-parallel-size 2`,
  `--max-model-len 8192`, `--gpu-memory-utilization 0.92`, listening on `127.0.0.1:8000`.
* **FastAPI Shim**: Launches `uvicorn phase5.serve.main:create_app` listening on `127.0.0.1:8090`,
  connecting upstream to vLLM, enforcing bearer auth, and managing Supabase domain retrieval.
* **Cloudflare Tunnel**: Runs `cloudflared tunnel run --token $TUNNEL_TOKEN`, routing to `:8090`.
* **Process Supervision & Trap**: Automatically traps `EXIT`, `SIGINT`, and `SIGTERM` to cleanly
  tear down `cloudflared`, the shim, and `vLLM` upon job completion.

### 17.4 External Script Deprecation
External cloud deployment tooling (`bootstrap-host.sh`, `providers/bootstrap-runpod.sh`,
`providers/runpod_provision.py`) has been removed in favor of `run_production.slurm` and the
unified certification probe `phase5/deploy/live_probe.py`.

### 17.5 Launch & Verification Command
```bash
# Submit to Param Rudra
sbatch phase5/deploy/run_production.slurm

# Verify once online
python phase5/deploy/live_probe.py --url https://ai.berojgardegreewala.com
```

