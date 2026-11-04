"""P5.1 Prometheus instrumentation for the BDW inference shim.

Exposed on GET /metrics (OpenMetrics/Prometheus text format). When
P5_METRICS_TOKEN is set, the endpoint requires `Authorization: Bearer
<token>`; leave it unset on trusted internal networks so Prometheus can
scrape without credentials.

Metric set (label cardinality is bounded by construction - domain comes
from the five P4 domains plus "none"):

  bdw_shim_requests_total{route,stream,status,domain}
      Post-validation chat requests by outcome. status is the HTTP-ish
      outcome: "200", "429", "502", "504", "499" (client disconnected
      mid-stream), "500" (unexpected). Validation 400s are not counted.
  bdw_shim_request_duration_seconds{route,stream}
      End-to-end duration; for streams this spans the whole SSE session
      (first byte to [DONE]/disconnect), measured inside the generator.
  bdw_shim_ttft_seconds{domain}
      Time from request start to the first streamed content delta
      (includes routing + retrieval + prefill - what a client feels).
  bdw_shim_tokens_total{direction,domain}
      prompt/completion tokens from the upstream usage block, falling
      back to the char/4 estimate when the server reports none.
  bdw_shim_upstream_errors_total{type}
      bounded set: timeout | rate_limit | upstream | not_ready | other.
  bdw_shim_citation_drops_total{domain}
      S5 citation marks stripped by the verifier (grounding pressure).
  bdw_shim_requests_in_flight{route}
      Gauge: requests currently being served.

All instruments are module-level singletons on the default collector
registry, so repeated create_app() calls (tests, factory re-imports)
never double-register.
"""
from __future__ import annotations

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

DOMAINS = ("math", "vlsi", "embedded", "cs", "aiml", "general", "none")

REQUESTS = Counter(
    "bdw_shim_requests_total",
    "Chat requests completed by the shim, post-validation "
    "(by route, stream flag, outcome status and routed domain).",
    ["route", "stream", "status", "domain"])

DURATION = Histogram(
    "bdw_shim_request_duration_seconds",
    "End-to-end shim request duration in seconds.",
    ["route", "stream"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0, 120.0))

TTFT = Histogram(
    "bdw_shim_ttft_seconds",
    "Time to first streamed content delta in seconds.",
    ["domain"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 15.0, 30.0, 60.0))

TOKENS = Counter(
    "bdw_shim_tokens_total",
    "Tokens processed by the shim (direction=prompt|completion).",
    ["direction", "domain"])

UPSTREAM_ERRORS = Counter(
    "bdw_shim_upstream_errors_total",
    "Upstream/inference failures surfaced to clients.",
    ["type"])

CITATION_DROPS = Counter(
    "bdw_shim_citation_drops_total",
    "Citation marks stripped by the S5 verifier.",
    ["domain"])

INFLIGHT = Gauge(
    "bdw_shim_requests_in_flight",
    "Requests currently being processed by the shim.",
    ["route"])

_ERROR_TYPE_MAP = {
    "429": "rate_limit",
    "502": "upstream",
    "503": "not_ready",
    "504": "timeout",
}


def _domain(value) -> str:
    """Bounded domain label: known domain, else 'none'."""
    d = (value or "none")
    d = str(d).lower()
    return d if d in DOMAINS else "none"


def inc_inflight(route: str) -> None:
    INFLIGHT.labels(route=route).inc()


def dec_inflight(route: str) -> None:
    INFLIGHT.labels(route=route).dec()


def observe_request(route: str, stream: str, status, domain,
                    duration_s: float) -> None:
    REQUESTS.labels(route=route, stream=str(stream),
                    status=str(status), domain=_domain(domain)).inc()
    DURATION.labels(route=route, stream=str(stream)).observe(
        max(0.0, float(duration_s)))


def observe_ttft(domain, seconds: float) -> None:
    TTFT.labels(domain=_domain(domain)).observe(max(0.0, float(seconds)))


def observe_usage(domain, usage: dict) -> None:
    if not isinstance(usage, dict):
        return
    dom = _domain(domain)
    prompt = int(usage.get("prompt_tokens") or 0)
    completion = int(usage.get("completion_tokens") or 0)
    if prompt:
        TOKENS.labels(direction="prompt", domain=dom).inc(prompt)
    if completion:
        TOKENS.labels(direction="completion", domain=dom).inc(completion)


def observe_upstream_error(status) -> None:
    kind = _ERROR_TYPE_MAP.get(str(status), "other")
    UPSTREAM_ERRORS.labels(type=kind).inc()


def observe_citations(domain, dropped) -> None:
    n = len(dropped or [])
    if n:
        CITATION_DROPS.labels(domain=_domain(domain)).inc(n)


def render():
    """(body, content_type) for the /metrics response."""
    return generate_latest(), CONTENT_TYPE_LATEST
