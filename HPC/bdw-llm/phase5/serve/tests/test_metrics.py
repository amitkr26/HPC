"""P5.1 /metrics endpoint and instrument behavior.

Counters are process-global, so every assertion measures the delta
across a single action - order-independent and safe under any test
shuffling.
"""
from __future__ import annotations

from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from phase5.serve.main import Settings, create_app
from phase5.serve.tests.fake_gateway import FakeGateway, FakeStreamingGateway

KEY = "p5-metrics-key"
AUTH = {"Authorization": "Bearer " + KEY}


def make_client(gateway=None, **settings_kw):
    gateway = gateway if gateway is not None else FakeGateway()
    settings = Settings(auth_mode="required", api_key=KEY, **settings_kw)
    app = create_app(gateway=gateway, settings=settings,
                     readiness_probe=lambda: True)
    return TestClient(app), gateway


def chat_body(**overrides):
    body = {
        "model": "bdw-career-ai",
        "messages": [{"role": "user",
                      "content": "What is setup time in a flip flop?"}],
        "max_tokens": 128,
        "stream": False,
    }
    body.update(overrides)
    return body


def sample(name, labels):
    return REGISTRY.get_sample_value(name, labels) or 0.0


def req_labels(**overrides):
    labels = {"route": "chat", "stream": "0", "status": "200",
              "domain": "vlsi"}
    labels.update(overrides)
    return labels


# --- endpoint ---------------------------------------------------------------

def test_metrics_endpoint_is_open_without_token():
    client, _ = make_client()
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")
    assert b"bdw_shim_requests_total" in resp.content
    assert b"bdw_shim_ttft_seconds" in resp.content
    assert b"bdw_shim_tokens_total" in resp.content
    assert b"bdw_shim_upstream_errors_total" in resp.content
    assert b"bdw_shim_citation_drops_total" in resp.content
    assert b"bdw_shim_request_duration_seconds" in resp.content


def test_metrics_endpoint_token_gate():
    client, _ = make_client(metrics_token="metrics-secret")
    assert client.get("/metrics").status_code == 401
    assert client.get("/metrics", headers={
        "Authorization": "Bearer wrong"}).status_code == 401
    # the P5 API key is NOT the metrics token
    assert client.get("/metrics", headers=AUTH).status_code == 401
    ok = client.get("/metrics", headers={
        "Authorization": "Bearer metrics-secret"})
    assert ok.status_code == 200
    assert b"bdw_shim_requests_total" in ok.content


def test_metrics_error_envelope_on_bad_token():
    client, _ = make_client(metrics_token="metrics-secret")
    body = client.get("/metrics").json()
    assert body["error"]["type"] == "authentication_error"
    assert body["error"]["code"] == "invalid_metrics_token"


def test_metrics_route_ignores_api_auth_mode():
    # /metrics is gated only by P5_METRICS_TOKEN, never by P5_API_KEY
    app = create_app(gateway=FakeGateway(),
                     settings=Settings(auth_mode="disabled", api_key=None),
                     readiness_probe=lambda: True)
    assert TestClient(app).get("/metrics").status_code == 200


# --- request counters -------------------------------------------------------

def test_non_stream_request_is_counted_with_domain_and_tokens():
    client, _ = make_client()
    before_req = sample("bdw_shim_requests_total", req_labels())
    before_inflight = sample("bdw_shim_requests_in_flight",
                             {"route": "chat"})
    before_prompt = sample("bdw_shim_tokens_total",
                           {"direction": "prompt", "domain": "vlsi"})
    before_completion = sample("bdw_shim_tokens_total",
                               {"direction": "completion", "domain": "vlsi"})
    before_dur = sample("bdw_shim_request_duration_seconds_count",
                        {"route": "chat", "stream": "0"})
    resp = client.post("/v1/chat/completions", headers=AUTH,
                       json=chat_body())
    assert resp.status_code == 200
    assert sample("bdw_shim_requests_total",
                  req_labels()) == before_req + 1
    assert sample("bdw_shim_tokens_total",
                  {"direction": "prompt", "domain": "vlsi"}) > before_prompt
    assert sample("bdw_shim_tokens_total",
                  {"direction": "completion",
                   "domain": "vlsi"}) > before_completion
    assert sample("bdw_shim_request_duration_seconds_count",
                  {"route": "chat", "stream": "0"}) == before_dur + 1
    # inflight returned to its pre-request level
    assert sample("bdw_shim_requests_in_flight",
                  {"route": "chat"}) == before_inflight


def test_citation_drops_are_counted_per_domain():
    client, _ = make_client()
    labels = {"domain": "vlsi"}
    before = sample("bdw_shim_citation_drops_total", labels)
    resp = client.post("/v1/chat/completions", headers=AUTH,
                       json=chat_body())
    assert resp.status_code == 200
    # fake_meta reports exactly one dropped marker
    assert sample("bdw_shim_citation_drops_total",
                  labels) == before + 1


def test_upstream_timeout_counts_status_504_and_error_type():
    client, _ = make_client(gateway=FakeGateway(behavior="timeout"))
    before_req = sample("bdw_shim_requests_total",
                        req_labels(status="504", domain="none"))
    before_err = sample("bdw_shim_upstream_errors_total",
                        {"type": "timeout"})
    resp = client.post("/v1/chat/completions", headers=AUTH,
                       json=chat_body())
    assert resp.status_code == 504
    assert sample("bdw_shim_requests_total",
                  req_labels(status="504",
                             domain="none")) == before_req + 1
    assert sample("bdw_shim_upstream_errors_total",
                  {"type": "timeout"}) == before_err + 1


def test_rate_limit_counts_status_429_and_error_type():
    client, _ = make_client(gateway=FakeGateway(behavior="rate"))
    before_req = sample("bdw_shim_requests_total",
                        req_labels(status="429", domain="none"))
    before_err = sample("bdw_shim_upstream_errors_total",
                        {"type": "rate_limit"})
    resp = client.post("/v1/chat/completions", headers=AUTH,
                       json=chat_body())
    assert resp.status_code == 429
    assert sample("bdw_shim_requests_total",
                  req_labels(status="429",
                             domain="none")) == before_req + 1
    assert sample("bdw_shim_upstream_errors_total",
                  {"type": "rate_limit"}) == before_err + 1


def test_validation_errors_are_not_counted_as_requests():
    client, _ = make_client()
    before = sample("bdw_shim_requests_total", req_labels(
        status="400", domain="none"))
    resp = client.post("/v1/chat/completions", headers=AUTH,
                       json={"messages": [{"role": "user", "content": ""}]})
    assert resp.status_code == 400
    assert sample("bdw_shim_requests_total",
                  req_labels(status="400", domain="none")) == before


# --- streaming metrics ------------------------------------------------------

def test_live_stream_counts_request_ttft_and_usage():
    client, _ = make_client(gateway=FakeStreamingGateway())
    stream_labels = req_labels(stream="1")
    before_req = sample("bdw_shim_requests_total", stream_labels)
    before_inflight = sample("bdw_shim_requests_in_flight",
                             {"route": "chat"})
    before_ttft = sample("bdw_shim_ttft_seconds_count", {"domain": "vlsi"})
    before_completion = sample("bdw_shim_tokens_total",
                               {"direction": "completion", "domain": "vlsi"})
    before_dur = sample("bdw_shim_request_duration_seconds_count",
                        {"route": "chat", "stream": "1"})
    resp = client.post("/v1/chat/completions", headers=AUTH,
                       json=chat_body(stream=True))
    assert resp.status_code == 200
    assert "[DONE]" in resp.text
    assert sample("bdw_shim_requests_total",
                  stream_labels) == before_req + 1
    assert sample("bdw_shim_ttft_seconds_count",
                  {"domain": "vlsi"}) == before_ttft + 1
    assert sample("bdw_shim_tokens_total",
                  {"direction": "completion",
                   "domain": "vlsi"}) > before_completion
    assert sample("bdw_shim_request_duration_seconds_count",
                  {"route": "chat", "stream": "1"}) == before_dur + 1
    assert sample("bdw_shim_requests_in_flight",
                  {"route": "chat"}) == before_inflight


def test_live_stream_upstream_error_counts_error_type():
    client, _ = make_client(
        gateway=FakeStreamingGateway(behavior="timeout"),
        sse_heartbeat_s=0.1)
    stream_labels = req_labels(stream="1", status="504", domain="none")
    before_req = sample("bdw_shim_requests_total", stream_labels)
    before_inflight = sample("bdw_shim_requests_in_flight",
                             {"route": "chat"})
    before_err = sample("bdw_shim_upstream_errors_total",
                        {"type": "timeout"})
    resp = client.post("/v1/chat/completions", headers=AUTH,
                       json=chat_body(stream=True))
    assert resp.status_code == 200
    assert '"code": "upstream_timeout"' in resp.text or \
        '"code":"upstream_timeout"' in resp.text
    assert sample("bdw_shim_requests_total",
                  stream_labels) == before_req + 1
    assert sample("bdw_shim_upstream_errors_total",
                  {"type": "timeout"}) == before_err + 1
    assert sample("bdw_shim_requests_in_flight",
                  {"route": "chat"}) == before_inflight


def test_post_generation_fallback_stream_is_instrumented_too():
    client, _ = make_client(gateway=FakeGateway(), stream_upstream=False,
                            sse_chunk_chars=16)
    stream_labels = req_labels(stream="1")
    before_req = sample("bdw_shim_requests_total", stream_labels)
    before_inflight = sample("bdw_shim_requests_in_flight",
                             {"route": "chat"})
    resp = client.post("/v1/chat/completions", headers=AUTH,
                       json=chat_body(stream=True))
    assert resp.status_code == 200
    assert "[DONE]" in resp.text
    assert sample("bdw_shim_requests_total",
                  stream_labels) == before_req + 1
    assert sample("bdw_shim_requests_in_flight",
                  {"route": "chat"}) == before_inflight
