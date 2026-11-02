"""P5.0/P5.1 - OpenAI-compatible inference shim for BerojgarDegreeWala.

This is the production-facing surface described in
docs/PHASE5_BDW_INTEGRATION_BLUEPRINT.md §5/§9. It speaks the exact subset of
the OpenAI API that backend/ai-gateway/src/providers/bdw.ts uses:

  GET  /v1/models              -> {"object": "list", "data": [...]}
  POST /v1/chat/completions    -> chat.completion (+ SSE when stream=true)
  GET  /metrics                -> Prometheus instrumentation (P5.1)

...and reuses the Phase 3/4 Zone 2 stack unchanged (hybrid domain router,
Supabase domain tables with local npz fallback, per-request LoRA, citation
verifier) through phase3/gateway/app.py:build_gateway(). Domain metadata is
returned in an additive "bdw" object; BDW reads only
choices[0].message.content.

P5.1 live streaming (blueprint ADR-4 supersession): when the gateway
exposes ask_stream() and P5_STREAM_UPSTREAM is on (both default), SSE
deltas are forwarded as Zone 3 produces them - router + RAG run once in a
producer thread, the citation gate streams per delta, heartbeats keep the
connection warm before the first token, and failures/limits surface as
in-band OpenAI error events followed by [DONE]. Gateways without
ask_stream(), or P5_STREAM_UPSTREAM=0, fall back to the P5.0
post-generation streaming path byte-for-byte.

Run (from the bdw-llm repo root):

    uvicorn phase5.serve.main:create_app --factory --host 0.0.0.0 --port 8090

Environment (see §9.3): P5_API_KEY, P5_AUTH_MODE=required|optional|disabled,
P5_MAX_QUESTION_CHARS, P5_MAX_TOKENS_DEFAULT, P5_SSE_CHUNK_CHARS,
P5_SSE_HEARTBEAT_S, P5_MODEL, P5_READY_URL, P5_STREAM_UPSTREAM,
P5_METRICS_TOKEN, plus the Phase 3/4 variables (SUPABASE_URL,
SUPABASE_SERVICE_ROLE_KEY, ZONE3_BASE_URL, ZONE3_MODEL, ...).
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import metrics

VERSION = "5.1.0"
MODEL_CREATED = 1730000000
DOMAINS = ("math", "vlsi", "embedded", "cs", "aiml")
MODEL_IDS = ("bdw-career-ai",) + tuple("bdw-" + d for d in DOMAINS)
# Note: tuple concat above is (career,) + (math..aiml) -> six IDs.

_ERR_TYPES = {
    400: "invalid_request_error",
    401: "authentication_error",
    403: "permission_error",
    404: "not_found_error",
    405: "invalid_request_error",
    422: "invalid_request_error",
    429: "rate_limit_error",
    502: "upstream_error",
    503: "service_unavailable",
    504: "upstream_timeout",
}


def _error_body(message: str, type_: str = "invalid_request_error",
                param: Optional[str] = None,
                code: Optional[str] = None) -> dict:
    return {"error": {"message": message, "type": type_,
                      "param": param, "code": code}}


def _json_error(status: int, message: str, param: Optional[str] = None,
                code: Optional[str] = None,
                headers: Optional[dict] = None) -> JSONResponse:
    return JSONResponse(_error_body(message, _ERR_TYPES.get(status, "api_error"),
                                    param, code),
                        status_code=status, headers=headers)


@dataclass(frozen=True)
class Settings:
    """Shim configuration (§9.3). Frozen so tests can build exact values."""

    model: str = "bdw-career-ai"
    auth_mode: str = "required"
    api_key: Optional[str] = None
    max_question_chars: int = 4000
    default_max_tokens: int = 1024
    sse_chunk_chars: int = 48
    sse_heartbeat_s: float = 10.0
    ready_url: Optional[str] = None
    stream_upstream: bool = True   # P5.1: live ask_stream() proxy when able
    metrics_token: Optional[str] = None  # P5.1: /metrics bearer (optional)

    @classmethod
    def from_env(cls, env: Optional[Dict[str, str]] = None) -> "Settings":
        env = env if env is not None else dict(os.environ)

        def num(key: str, default, cast):
            raw = env.get(key)
            return cast(raw) if raw not in (None, "") else default

        def flag(key: str, default: bool):
            raw = env.get(key)
            if raw in (None, ""):
                return default
            return str(raw).strip().lower() not in ("0", "false", "no", "off")

        zone3 = (env.get("ZONE3_BASE_URL") or
                 "http://127.0.0.1:8080").rstrip("/")
        if zone3.endswith("/v1"):
            zone3 = zone3[:-3]
        ready = env.get("P5_READY_URL") or (zone3 + "/health")
        return cls(
            model=env.get("P5_MODEL") or "bdw-career-ai",
            auth_mode=(env.get("P5_AUTH_MODE") or "required").lower(),
            api_key=env.get("P5_API_KEY") or None,
            max_question_chars=num("P5_MAX_QUESTION_CHARS", 4000, int),
            default_max_tokens=num("P5_MAX_TOKENS_DEFAULT", 1024, int),
            sse_chunk_chars=num("P5_SSE_CHUNK_CHARS", 48, int),
            sse_heartbeat_s=num("P5_SSE_HEARTBEAT_S", 10.0, float),
            ready_url=ready,
            stream_upstream=flag("P5_STREAM_UPSTREAM", True),
            metrics_token=env.get("P5_METRICS_TOKEN") or None,
        )


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: Optional[str] = None
    messages: List[Message] = Field(min_length=1, max_length=64)
    max_tokens: Optional[int] = None
    max_completion_tokens: Optional[int] = None
    temperature: Optional[float] = None
    stream: bool = False
    metadata: Optional[Dict[str, Any]] = None
    # OpenAI clients send top_p/stop/user/...; they are accepted and ignored.
    model_config = {"extra": "allow"}


class ClassifyRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)


def _bearer_key(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    key = parts[1].strip()
    return key or None


def _user_hash(user_id: str) -> str:
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]


def _force_domain(model: Optional[str]) -> Optional[str]:
    """bdw-<domain> / lora_<domain> force a domain; everything else routes."""
    m = (model or "").strip().lower()
    for prefix in ("bdw-", "lora_"):
        if m.startswith(prefix):
            d = m[len(prefix):]
            if d in DOMAINS:
                return d
    return None


def _clamp_temp(value: Optional[float]) -> float:
    if value is None:
        return 0.0
    return max(0.0, min(float(value), 2.0))


def _user_id(req: ChatRequest, header_user: Optional[str]) -> str:
    md = req.metadata or {}
    uid = md.get("user_id") or md.get("user") or header_user
    if not isinstance(uid, str) or not uid.strip():
        return "shared"
    return uid.strip()[:128]


def _web_mode(req: ChatRequest) -> Optional[str]:
    wm = (req.metadata or {}).get("web")
    return wm if wm in ("auto", "on", "off") else None


def _prepare(req: ChatRequest, settings: Settings):
    msgs = req.messages
    system_parts = [m.content.strip() for m in msgs
                    if m.role == "system" and m.content.strip()]
    convo = [m for m in msgs if m.role != "system"]
    if not convo or convo[-1].role != "user":
        raise HTTPException(400, _error_body(
            "the last message must have role 'user'", "invalid_request_error",
            "messages"))
    question = convo[-1].content.strip()
    if not question:
        raise HTTPException(400, _error_body(
            "the last user message is empty", "invalid_request_error",
            "messages"))
    if len(question) > settings.max_question_chars:
        raise HTTPException(400, _error_body(
            "question exceeds %d characters" % settings.max_question_chars,
            "invalid_request_error", "messages"))
    history = [{"role": m.role, "content": m.content}
               for m in convo[:-1] if m.role in ("user", "assistant")]
    system_prompt = "\n\n".join(system_parts) or None
    max_tokens = req.max_tokens if req.max_tokens is not None \
        else req.max_completion_tokens
    if max_tokens is not None and (max_tokens < 1 or max_tokens > 4096):
        raise HTTPException(400, _error_body(
            "max_tokens must be between 1 and 4096",
            "invalid_request_error", "max_tokens"))
    return question, history, system_prompt, max_tokens


def _meta_to_bdw(meta: dict, latency_ms: int) -> dict:
    dom = meta.get("domain") or {}
    lora = meta.get("lora") or {}
    routing = meta.get("routing") or {}
    chunks = meta.get("chunks") or []
    citations = [{"index": i, "title": c.get("title"),
                  "url": c.get("url"), "verified": c.get("verified"),
                  "source": c.get("source")}
                 for i, c in enumerate(chunks)]
    return {
        "domain": dom.get("domain"),
        "confidence": dom.get("confidence"),
        "adapter": lora.get("adapter"),
        "adapter_applied": lora.get("applied"),
        "router_reason": dom.get("reason"),
        "retrieval_backend": (meta.get("retrieval") or {}).get(
            "domain_backend"),
        "citations": citations,
        "sources": citations,
        "citations_kept": meta.get("citations_kept") or [],
        "citations_dropped": meta.get("citations_dropped") or [],
        "web_used": bool(routing.get("web_used")),
        "grounded": bool(chunks),
        "timings": {"total_ms": latency_ms},
    }


def _usage(req: ChatRequest, answer: str) -> dict:
    prompt_chars = sum(len(m.content) for m in req.messages)
    pt = max(1, prompt_chars // 4) if prompt_chars else 0
    ct = max(1, len(answer) // 4) if answer else 0
    return {"prompt_tokens": pt, "completion_tokens": ct,
            "total_tokens": pt + ct}


def _completion(cid: str, created: int, model: str, answer: str,
                usage: dict, bdw: dict) -> dict:
    return {
        "id": cid,
        "object": "chat.completion",
        "created": created,
        "model": model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": answer},
            "finish_reason": "stop",
        }],
        "usage": usage,
        "bdw": bdw,
    }


def _sse(obj: dict) -> str:
    return "data: " + json.dumps(obj, ensure_ascii=False,
                                 separators=(",", ":")) + "\n\n"


def _chunk(cid: str, created: int, model: str, delta: dict,
           finish: Optional[str] = None,
           extra: Optional[dict] = None) -> dict:
    body = {"id": cid, "object": "chat.completion.chunk",
            "created": created, "model": model,
            "choices": [{"index": 0, "delta": delta,
                         "finish_reason": finish}]}
    if extra:
        body.update(extra)
    return body


def _default_readiness_probe(url: Optional[str]) -> Callable[[], bool]:
    def probe() -> bool:
        if not url:
            return True
        import urllib.request
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                return 200 <= getattr(r, "status", 200) < 300
        except Exception:  # noqa: BLE001
            return False
    return probe


_STREAM_END = object()  # producer sentinel: gateway stream ended cleanly


async def stream_chat_events(gateway, req, question, user_id, web_mode,
                             history, system_prompt, max_tokens, temperature,
                             force_domain, settings, cid, created, model,
                             started) -> AsyncIterator[str]:
    """P5.1 live SSE body: proxy gateway.ask_stream() as OpenAI chunks.

    The blocking gateway generator is owned by a producer thread which
    bridges events onto an asyncio.Queue (single owner -> no
    close-while-executing races). While the upstream produces nothing the
    loop answers with `: ping` heartbeats. Client disconnect raises
    GeneratorExit at a yield: the finally sets `stop`, the producer
    abandons the bridge and closes the gateway generator (which closes the
    Zone 3 response), and the session is recorded as status 499.
    """
    loop = asyncio.get_running_loop()
    q: asyncio.Queue = asyncio.Queue()
    stop = threading.Event()

    def put(item) -> None:
        """Thread-safe hand-off; wakes after the loop closed (disconnect
        during a producer read) are dropped, never raised."""
        try:
            loop.call_soon_threadsafe(q.put_nowait, item)
        except RuntimeError:
            pass

    def produce() -> None:
        gen = None
        try:
            gen = gateway.ask_stream(question, user_id, web_mode, history,
                                     system_prompt=system_prompt,
                                     max_tokens=max_tokens,
                                     temperature=temperature,
                                     force_domain=force_domain)
            for event in gen:
                if stop.is_set():
                    break
                put(event)
            else:
                put(_STREAM_END)
        except Exception as exc:  # noqa: BLE001
            # ask_stream reports failures as events; a raise here is a
            # contract break - translate it so the client still gets an
            # in-band error instead of a stalled stream.
            name = type(exc).__name__
            print("P5_UPSTREAM_ERROR type=%s" % name, flush=True)
            timed_out = isinstance(exc, TimeoutError) or "Timeout" in name
            put({"type": "error",
                 "status": 504 if timed_out else 502,
                 "code": "upstream_timeout" if timed_out
                 else "upstream_error",
                 "message": "upstream inference timed out" if timed_out
                 else "upstream inference failed"})
        finally:
            if gen is not None:
                try:
                    gen.close()
                except Exception:  # noqa: BLE001
                    pass

    threading.Thread(target=produce, daemon=True,
                     name="p5-stream-producer").start()

    route = "chat"
    status_label, domain_label = "500", "none"
    ttft_s: Optional[float] = None
    usage_final: Optional[dict] = None
    drops: List = []
    answer_final = ""
    meta_final: dict = {}
    role_sent = False
    metrics.inc_inflight(route)
    try:
        while True:
            try:
                item = await asyncio.wait_for(
                    q.get(), timeout=settings.sse_heartbeat_s)
            except asyncio.TimeoutError:
                yield ": ping\n\n"
                continue
            if item is _STREAM_END:
                status_label = "200"
                break
            kind = item.get("type")
            if kind == "delta":
                text = item.get("text") or ""
                if not text:
                    continue
                if ttft_s is None:
                    ttft_s = time.perf_counter() - started
                if not role_sent:
                    role_sent = True
                    yield _sse(_chunk(cid, created, model,
                                      {"role": "assistant",
                                       "content": ""}))
                yield _sse(_chunk(cid, created, model,
                                  {"content": text}))
            elif kind == "error":
                raw_status = str(item.get("status") or 502)
                status_label = raw_status if raw_status.isdigit() \
                    else "502"
                yield _sse(_error_body(
                    item.get("message") or "upstream inference failed",
                    _ERR_TYPES.get(int(status_label), "api_error"),
                    code=item.get("code") or "upstream_error"))
                metrics.observe_upstream_error(status_label)
                break
            elif kind == "final":
                answer_final = item.get("answer") or ""
                meta_final = item.get("meta") or {}
                usage_final = item.get("usage")
                status_label = "200"
                break
        if status_label != "200":
            # in-band failure already emitted; no finish chunk
            yield "data: [DONE]\n\n"
            return
        # terminal success: role (if not yet), finish chunk, [DONE]
        latency_ms = int((time.perf_counter() - started) * 1000)
        bdw = _meta_to_bdw(meta_final, latency_ms)
        domain_label = bdw.get("domain")
        drops = bdw.get("citations_dropped") or []
        if usage_final is None:
            usage_final = _usage(req, answer_final)
        if not meta_final:
            print("P5_STREAM_END_WITHOUT_FINAL id=%s" % cid[-12:],
                  flush=True)
        if not role_sent:
            role_sent = True
            yield _sse(_chunk(cid, created, model,
                              {"role": "assistant", "content": ""}))
        yield _sse(_chunk(cid, created, model, {}, "stop",
                          {"usage": usage_final, "bdw": bdw}))
        yield "data: [DONE]\n\n"
        print("P5_REQUEST id=%s status=200 ms=%d ttft_ms=%d domain=%s "
              "adapter=%s user=%s stream=1 live=1" % (
                  cid[-12:], latency_ms, int((ttft_s or 0.0) * 1000),
                  bdw.get("domain"), bdw.get("adapter"),
                  _user_hash(user_id)), flush=True)
    except GeneratorExit:
        status_label = "499"
        raise
    finally:
        stop.set()
        if ttft_s is not None:
            metrics.observe_ttft(domain_label, ttft_s)
        if usage_final is not None:
            metrics.observe_usage(domain_label, usage_final)
        metrics.observe_citations(domain_label, drops)
        metrics.dec_inflight(route)
        metrics.observe_request(route, "1", status_label, domain_label,
                                time.perf_counter() - started)


async def _post_gen_events(gateway, req, question, user_id, web_mode,
                           history, system_prompt, max_tokens, temperature,
                           force_domain, settings, cid, created, model,
                           started) -> AsyncIterator[str]:
    """P5.0 post-generation SSE body (ADR-4 fallback): run the full ask()
    on a worker task, heartbeat while router/RAG/LLM work runs, then emit
    the answer as chunks. Byte-for-byte the P5.0 behavior; P5.1 only adds
    outcome instrumentation around it."""
    route = "chat"
    status_label, domain_label = "500", "none"
    ttft_s: Optional[float] = None
    usage_final: Optional[dict] = None
    drops: List = []
    metrics.inc_inflight(route)
    try:
        task = asyncio.create_task(asyncio.to_thread(
            gateway.ask, question, user_id, web_mode, history,
            system_prompt=system_prompt, max_tokens=max_tokens,
            temperature=temperature, force_domain=force_domain))
        payload = status = None
        failure = None
        try:
            while not task.done():
                try:
                    payload, status, _ = await asyncio.wait_for(
                        asyncio.shield(task),
                        timeout=settings.sse_heartbeat_s)
                    break
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
                    continue
            if payload is None:
                payload, status, _ = await task
        except Exception as e:  # noqa: BLE001
            failure = e
        if failure is not None:
            name = type(failure).__name__
            print("P5_UPSTREAM_ERROR type=%s" % name, flush=True)
            timed_out = (isinstance(failure, TimeoutError)
                         or "Timeout" in name)
            status_label = "504" if timed_out else "502"
            metrics.observe_upstream_error(status_label)
            yield _sse(_error_body(
                "upstream inference timed out" if timed_out
                else "upstream inference failed",
                "upstream_timeout" if timed_out else "upstream_error",
                code="upstream_timeout" if timed_out
                else "upstream_error"))
            yield "data: [DONE]\n\n"
            return
        latency_ms = int((time.perf_counter() - started) * 1000)
        if status == 429:
            status_label = "429"
            metrics.observe_upstream_error(429)
            yield _sse(_error_body("rate limit reached; retry tomorrow",
                                   "rate_limit_error",
                                   code="rate_limit_exceeded"))
            yield "data: [DONE]\n\n"
            return
        if status != 200 or not isinstance(payload, dict):
            status_label = "502"
            metrics.observe_upstream_error(502)
            yield _sse(_error_body("upstream returned an invalid response",
                                   "upstream_error",
                                   code="upstream_error"))
            yield "data: [DONE]\n\n"
            return
        answer = payload.get("answer") or ""
        bdw = _meta_to_bdw(payload.get("meta") or {}, latency_ms)
        status_label = "200"
        domain_label = bdw.get("domain")
        drops = bdw.get("citations_dropped") or []
        usage_final = _usage(req, answer)
        ttft_s = time.perf_counter() - started
        yield _sse(_chunk(cid, created, model,
                          {"role": "assistant", "content": ""}))
        for i in range(0, len(answer), settings.sse_chunk_chars):
            yield _sse(_chunk(cid, created, model,
                              {"content": answer[i:i +
                                                 settings.sse_chunk_chars]}))
        yield _sse(_chunk(cid, created, model, {}, "stop",
                          {"usage": usage_final, "bdw": bdw}))
        yield "data: [DONE]\n\n"
        print("P5_REQUEST id=%s status=200 ms=%d domain=%s adapter=%s "
              "user=%s stream=1" % (
                  cid[-12:], latency_ms, bdw.get("domain"),
                  bdw.get("adapter"), _user_hash(user_id)), flush=True)
    except GeneratorExit:
        status_label = "499"
        raise
    finally:
        if ttft_s is not None:
            metrics.observe_ttft(domain_label, ttft_s)
        if usage_final is not None:
            metrics.observe_usage(domain_label, usage_final)
        metrics.observe_citations(domain_label, drops)
        metrics.dec_inflight(route)
        metrics.observe_request(route, "1", status_label, domain_label,
                                time.perf_counter() - started)


def create_app(gateway=None, settings: Optional[Settings] = None,
               readiness_probe: Optional[Callable[[], bool]] = None) -> FastAPI:
    """Build the shim. Tests inject a deterministic gateway; deployment
    leaves gateway=None so runtime.build_gateway() constructs the real
    Phase 3/4 stack from the environment."""
    settings = settings or Settings.from_env()
    if settings.auth_mode not in ("required", "optional", "disabled"):
        raise ValueError("P5_AUTH_MODE must be required|optional|disabled")
    if settings.auth_mode == "required" and not settings.api_key:
        raise RuntimeError("P5_API_KEY is required when P5_AUTH_MODE=required")

    runtime_info = None
    if gateway is None:
        from .runtime import build_gateway
        gateway, runtime_info = build_gateway()

    app = FastAPI(title="BDW Inference Shim", version=VERSION,
                  docs_url=None, redoc_url=None, openapi_url=None)
    app.state.gateway = gateway
    app.state.settings = settings
    app.state.runtime_info = runtime_info
    app.state.readiness_probe = readiness_probe or \
        _default_readiness_probe(settings.ready_url)

    def require_auth(authorization: Optional[str]) -> None:
        if settings.auth_mode == "disabled":
            return
        key = _bearer_key(authorization)
        if settings.auth_mode == "optional" and key is None:
            return
        expected = settings.api_key or ""
        if not expected or key is None or not hmac.compare_digest(key,
                                                                  expected):
            raise HTTPException(
                401, _error_body("invalid or missing API key",
                                 "authentication_error", None,
                                 "invalid_api_key"),
                headers={"WWW-Authenticate": "Bearer"})

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_request, exc: StarletteHTTPException):
        if isinstance(exc.detail, dict) and "error" in exc.detail:
            body = exc.detail
        else:
            body = _error_body(str(exc.detail),
                               _ERR_TYPES.get(exc.status_code, "api_error"))
        return JSONResponse(body, status_code=exc.status_code,
                            headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_request, exc: RequestValidationError):
        first = (exc.errors() or [{}])[0]
        loc = ".".join(str(x) for x in first.get("loc", ()))
        msg = first.get("msg") or "invalid request body"
        return _json_error(400, "%s: %s" % (loc, msg) if loc else msg,
                           param=loc or None)

    @app.get("/healthz")
    async def healthz():
        return {"status": "ok", "service": "bdw-inference-shim",
                "version": VERSION}

    @app.get("/readyz")
    async def readyz():
        try:
            ok = bool(app.state.readiness_probe())
        except Exception:  # noqa: BLE001
            ok = False
        if not ok:
            return _json_error(503, "upstream inference is not ready",
                               code="not_ready")
        return {"status": "ready", "service": "bdw-inference-shim"}

    @app.get("/v1/models")
    async def models(authorization: Optional[str] = Header(default=None)):
        require_auth(authorization)
        return {"object": "list",
                "data": [{"id": m, "object": "model",
                          "created": MODEL_CREATED, "owned_by": "bdw"}
                         for m in MODEL_IDS]}

    @app.get("/metrics")
    async def prometheus_metrics(
            authorization: Optional[str] = Header(default=None)):
        """Prometheus scrape endpoint (P5.1). Open when P5_METRICS_TOKEN
        is unset; otherwise requires that exact bearer token (constant-
        time compare), independent of P5_API_KEY."""
        expected = settings.metrics_token
        if expected:
            key = _bearer_key(authorization)
            if not key or not hmac.compare_digest(key, expected):
                raise HTTPException(
                    401, _error_body("invalid or missing metrics token",
                                     "authentication_error", None,
                                     "invalid_metrics_token"))
        body, ctype = metrics.render()
        return Response(content=body, media_type=ctype)

    @app.post("/v1/classify")
    async def classify(req: ClassifyRequest,
                       authorization: Optional[str] = Header(default=None)):
        require_auth(authorization)
        classifier = getattr(gateway, "classifier", None)
        if classifier is None:
            return _json_error(503, "router is not available",
                               code="router_unavailable")
        try:
            decision = await asyncio.to_thread(classifier.classify, req.text)
            return decision.to_dict()
        except Exception:  # noqa: BLE001
            return _json_error(502, "router failed", code="router_error")

    async def _ask(req: ChatRequest, question, history, system_prompt,
                   max_tokens, model, user_id, started) -> dict:
        force = _force_domain(model)
        web_mode = _web_mode(req)
        latency_ms = 0
        try:
            payload, status, err = await asyncio.to_thread(
                gateway.ask, question, user_id, web_mode, history,
                system_prompt=system_prompt, max_tokens=max_tokens,
                temperature=req.temperature, force_domain=force)
        except HTTPException:
            raise
        except Exception as e:  # noqa: BLE001
            latency_ms = int((time.perf_counter() - started) * 1000)
            name = type(e).__name__
            print("P5_UPSTREAM_ERROR type=%s" % name, flush=True)
            if isinstance(e, TimeoutError) or "Timeout" in name:
                raise HTTPException(504, _error_body(
                    "upstream inference timed out", "upstream_timeout",
                    code="upstream_timeout"))
            raise HTTPException(502, _error_body(
                "upstream inference failed", "upstream_error",
                code="upstream_error"))
        latency_ms = int((time.perf_counter() - started) * 1000)
        if status == 429:
            raise HTTPException(429, _error_body(
                "rate limit reached; retry tomorrow", "rate_limit_error",
                code="rate_limit_exceeded"))
        if status != 200 or not isinstance(payload, dict):
            raise HTTPException(502, _error_body(
                "upstream returned an invalid response", "upstream_error",
                code="upstream_error"))
        return {"payload": payload, "latency_ms": latency_ms,
                "usage": _usage(req, payload.get("answer") or "")}

    @app.post("/v1/chat/completions")
    async def chat(req: ChatRequest,
                   authorization: Optional[str] = Header(default=None),
                   x_bdw_user_id: Optional[str] = Header(
                       default=None, alias="X-BDW-User-Id")):
        require_auth(authorization)
        started = time.perf_counter()
        question, history, system_prompt, max_tokens = _prepare(
            req, settings)
        model = req.model or settings.model
        user_id = _user_id(req, x_bdw_user_id)
        cid = "chatcmpl-" + uuid.uuid4().hex
        created = int(time.time())
        web_mode = _web_mode(req)
        force = _force_domain(model)
        stream_args = (req, question, user_id, web_mode, history,
                       system_prompt, max_tokens, req.temperature, force,
                       settings, cid, created, model, started)

        if not req.stream:
            route = "chat"
            status_label, domain_label = "500", "none"
            metrics.inc_inflight(route)
            try:
                out = await _ask(req, question, history, system_prompt,
                                 max_tokens, model, user_id, started)
                payload = out["payload"]
                answer = payload.get("answer") or ""
                bdw = _meta_to_bdw(payload.get("meta") or {},
                                   out["latency_ms"])
                usage = out["usage"]
                print("P5_REQUEST id=%s status=200 ms=%d domain=%s "
                      "adapter=%s user=%s stream=0" % (
                          cid[-12:], out["latency_ms"], bdw.get("domain"),
                          bdw.get("adapter"), _user_hash(user_id)),
                      flush=True)
                status_label = "200"
                domain_label = bdw.get("domain") or "none"
                metrics.observe_usage(domain_label, usage)
                metrics.observe_citations(
                    domain_label, bdw.get("citations_dropped") or [])
                return _completion(cid, created, model, answer, usage, bdw)
            except HTTPException as exc:
                status_label = str(exc.status_code)
                if exc.status_code in (429, 502, 503, 504):
                    metrics.observe_upstream_error(exc.status_code)
                raise
            finally:
                metrics.dec_inflight(route)
                metrics.observe_request(route, "0", status_label,
                                        domain_label,
                                        time.perf_counter() - started)

        # Streaming: P5.1 live proxy when the gateway exposes ask_stream()
        # and P5_STREAM_UPSTREAM is on; otherwise the P5.0 post-generation
        # path (ADR-4) byte-for-byte. Each generator owns its own inflight
        # gauge and outcome metrics from first byte to [DONE]/disconnect.
        if settings.stream_upstream and callable(
                getattr(gateway, "ask_stream", None)):
            body = stream_chat_events(gateway, *stream_args)
        else:
            body = _post_gen_events(gateway, *stream_args)
        return StreamingResponse(
            body, media_type="text/event-stream",
            headers={"Cache-Control": "no-cache",
                     "X-Accel-Buffering": "no",
                     "Connection": "keep-alive"})

    return app
