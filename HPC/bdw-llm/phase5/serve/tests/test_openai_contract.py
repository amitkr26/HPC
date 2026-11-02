"""P5.0 OpenAI contract tests - fast, no GPU, no ML stack.

The app is built with a deterministic FakeGateway (same ask() contract as
phase3/gateway/app.py:Gateway), so these tests pin the HTTP/SSE surface
without importing torch or sentence-transformers.
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from phase5.serve.main import MODEL_IDS, Settings, create_app
from phase5.serve.tests.fake_gateway import ANSWER, FakeGateway

KEY = "p5-test-key"
AUTH = {"Authorization": "Bearer " + KEY}


def make_client(gateway=None, **settings_kw):
    gateway = gateway or FakeGateway()
    settings = Settings(auth_mode="required", api_key=KEY, **settings_kw)
    app = create_app(gateway=gateway, settings=settings,
                     readiness_probe=lambda: True)
    return TestClient(app), gateway


def chat_body(**overrides):
    body = {
        "model": "bdw-career-ai",
        "messages": [
            {"role": "system", "content": "You are BDW."},
            {"role": "user", "content": "What is setup time in a flip flop?"},
        ],
        "max_tokens": 128,
        "temperature": 0.3,
        "stream": False,
    }
    body.update(overrides)
    return body


def sse_events(text: str):
    events = []
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        if block.startswith(":"):
            events.append({"comment": block})
            continue
        for line in block.splitlines():
            if line.startswith("data: "):
                events.append({"data": line[len("data: "):]})
    return events


def test_health_and_readiness_are_public():
    client, _ = make_client()
    assert client.get("/healthz").json()["status"] == "ok"
    assert client.get("/readyz").json()["status"] == "ready"


def test_readiness_reports_503_when_upstream_down():
    app = create_app(gateway=FakeGateway(),
                     settings=Settings(auth_mode="required", api_key=KEY),
                     readiness_probe=lambda: False)
    resp = TestClient(app).get("/readyz")
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "not_ready"


def test_models_requires_bearer():
    client, _ = make_client()
    resp = client.get("/v1/models")
    assert resp.status_code == 401
    assert resp.json()["error"]["type"] == "authentication_error"
    assert resp.headers["www-authenticate"] == "Bearer"
    assert client.get("/v1/models", headers=AUTH).status_code == 200


def test_models_shape_matches_bdw_healthcheck():
    client, _ = make_client()
    data = client.get("/v1/models", headers=AUTH).json()
    assert data["object"] == "list"
    ids = [m["id"] for m in data["data"]]
    assert ids == list(MODEL_IDS)
    for model in data["data"]:
        assert model["object"] == "model"
        assert model["owned_by"] == "bdw"


def test_chat_non_stream_contract_and_metadata():
    client, gw = make_client()
    resp = client.post("/v1/chat/completions", headers=AUTH,
                       json=chat_body())
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"].startswith("chatcmpl-")
    assert body["object"] == "chat.completion"
    assert body["model"] == "bdw-career-ai"
    assert isinstance(body["created"], int)
    choice = body["choices"][0]
    assert choice["index"] == 0
    assert choice["message"] == {"role": "assistant", "content": ANSWER}
    assert choice["finish_reason"] == "stop"
    assert body["usage"]["total_tokens"] == (
        body["usage"]["prompt_tokens"] + body["usage"]["completion_tokens"])
    bdw = body["bdw"]
    assert bdw["domain"] == "vlsi"
    assert bdw["confidence"] == 0.91
    assert bdw["adapter"] == "lora_vlsi"
    assert bdw["adapter_applied"] is True
    assert bdw["citations"][0]["index"] == 0
    assert bdw["citations"][0]["title"] == "Flip-flop (electronics)"
    assert bdw["sources"] == bdw["citations"]
    assert bdw["citations_dropped"] == ["99"]
    assert bdw["grounded"] is True
    assert bdw["timings"]["total_ms"] >= 0
    call = gw.calls[-1]
    assert call["question"] == "What is setup time in a flip flop?"
    assert call["system_prompt"] == "You are BDW."
    assert call["history"] == []
    assert call["max_tokens"] == 128
    assert call["temperature"] == 0.3
    assert call["force_domain"] is None


def test_chat_accepts_the_exact_provider_body():
    """Body constructed the way backend/ai-gateway/src/providers/bdw.ts does."""
    client, gw = make_client()
    body = {
        "model": "bdw-career-ai",
        "messages": [
            {"role": "system", "content": "You are BDW, deep-tech assistant."},
            {"role": "user", "content": "What is setup time in a flip flop?"},
        ],
        "max_tokens": 2048,
        "temperature": 0.3,
    }
    resp = client.post("/v1/chat/completions", headers=AUTH, json=body)
    assert resp.status_code == 200
    assert isinstance(resp.json()["choices"][0]["message"]["content"], str)
    assert gw.calls[-1]["max_tokens"] == 2048
    assert gw.calls[-1]["temperature"] == pytest.approx(0.3)


@pytest.mark.parametrize("model,expected", [
    ("bdw-career-ai", None),
    ("bdw-vlsi", "vlsi"),
    ("bdw-embedded", "embedded"),
    ("lora_math", "math"),
    ("gpt-4o", None),
])
def test_model_aliases_force_domains(model, expected):
    client, gw = make_client()
    resp = client.post("/v1/chat/completions", headers=AUTH,
                       json=chat_body(model=model))
    assert resp.status_code == 200
    assert resp.json()["model"] == model
    assert gw.calls[-1]["force_domain"] == expected


def test_metadata_user_web_and_header_fallback():
    client, gw = make_client()
    body = chat_body(metadata={"user_id": "user-42", "web": "off"})
    assert client.post("/v1/chat/completions", headers=AUTH,
                       json=body).status_code == 200
    assert gw.calls[-1]["user_id"] == "user-42"
    assert gw.calls[-1]["web_mode"] == "off"

    body = chat_body()
    headers = dict(AUTH)
    headers["X-BDW-User-Id"] = "header-user"
    assert client.post("/v1/chat/completions", headers=headers,
                       json=body).status_code == 200
    assert gw.calls[-1]["user_id"] == "header-user"


def test_history_is_passed_without_system_messages():
    client, gw = make_client()
    body = chat_body(messages=[
        {"role": "system", "content": "You are BDW."},
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "second"},
        {"role": "user", "content": "third"},
    ])
    assert client.post("/v1/chat/completions", headers=AUTH,
                       json=body).status_code == 200
    call = gw.calls[-1]
    assert call["question"] == "third"
    assert call["history"] == [{"role": "user", "content": "first"},
                               {"role": "assistant", "content": "second"}]


@pytest.mark.parametrize("messages,status", [
    ([], 400),
    ([{"role": "assistant", "content": "no user"}], 400),
    ([{"role": "user", "content": "   "}], 400),
])
def test_invalid_messages_map_to_400(messages, status):
    client, _ = make_client()
    resp = client.post("/v1/chat/completions", headers=AUTH,
                       json={"messages": messages})
    assert resp.status_code == status
    assert resp.json()["error"]["type"] == "invalid_request_error"


def test_question_length_cap():
    client, _ = make_client(max_question_chars=20)
    resp = client.post("/v1/chat/completions", headers=AUTH,
                       json={"messages": [
                           {"role": "user", "content": "x" * 21}]})
    assert resp.status_code == 400
    assert "exceeds 20 characters" in resp.json()["error"]["message"]


def test_max_tokens_bounds():
    client, _ = make_client()
    for value in (0, -1, 9000):
        resp = client.post("/v1/chat/completions", headers=AUTH,
                           json={"messages": [
                               {"role": "user", "content": "hi"}],
                               "max_tokens": value})
        assert resp.status_code == 400


def test_rate_limit_maps_to_429():
    client, _ = make_client(gateway=FakeGateway(behavior="rate"))
    resp = client.post("/v1/chat/completions", headers=AUTH,
                       json=chat_body())
    assert resp.status_code == 429
    assert resp.json()["error"]["type"] == "rate_limit_error"
    assert resp.json()["error"]["code"] == "rate_limit_exceeded"


def test_upstream_error_maps_to_502():
    client, _ = make_client(gateway=FakeGateway(behavior="error"))
    resp = client.post("/v1/chat/completions", headers=AUTH,
                       json=chat_body())
    assert resp.status_code == 502
    assert resp.json()["error"]["type"] == "upstream_error"


def test_upstream_timeout_maps_to_504():
    client, _ = make_client(gateway=FakeGateway(behavior="timeout"))
    resp = client.post("/v1/chat/completions", headers=AUTH,
                       json=chat_body())
    assert resp.status_code == 504
    assert resp.json()["error"]["code"] == "upstream_timeout"


def test_unknown_route_uses_openai_error_envelope():
    client, _ = make_client()
    resp = client.get("/v1/nope", headers=AUTH)
    assert resp.status_code == 404
    assert resp.json()["error"]["type"] == "not_found_error"


def test_sse_stream_contract():
    client, _ = make_client(sse_chunk_chars=16)
    resp = client.post("/v1/chat/completions", headers=AUTH,
                       json=chat_body(stream=True))
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    events = sse_events(resp.text)
    assert events[-1]["data"] == "[DONE]"
    payloads = [json.loads(e["data"]) for e in events
                if "data" in e and e["data"] != "[DONE]"]
    assert payloads
    for p in payloads:
        assert p["object"] == "chat.completion.chunk"
        assert p["choices"][0]["index"] == 0
        assert p["model"] == "bdw-career-ai"
        assert p["id"].startswith("chatcmpl-")
    assert payloads[0]["choices"][0]["delta"] == {
        "role": "assistant", "content": ""}
    content = "".join(p["choices"][0]["delta"].get("content", "")
                      for p in payloads)
    assert content == ANSWER
    final = payloads[-1]
    assert final["choices"][0]["finish_reason"] == "stop"
    assert final["usage"]["total_tokens"] > 0
    assert final["bdw"]["domain"] == "vlsi"
    assert final["bdw"]["adapter"] == "lora_vlsi"


def test_sse_heartbeat_while_generating():
    client, _ = make_client(gateway=FakeGateway(delay=0.35),
                            sse_heartbeat_s=0.1)
    resp = client.post("/v1/chat/completions", headers=AUTH,
                       json=chat_body(stream=True))
    assert resp.status_code == 200
    assert ": ping" in resp.text
    events = sse_events(resp.text)
    assert events[-1]["data"] == "[DONE]"


@pytest.mark.parametrize("behavior,code", [
    ("error", "upstream_error"),
    ("timeout", "upstream_timeout"),
])
def test_sse_upstream_failure_is_in_band(behavior, code):
    client, _ = make_client(gateway=FakeGateway(behavior=behavior),
                            sse_heartbeat_s=0.1)
    resp = client.post("/v1/chat/completions", headers=AUTH,
                       json=chat_body(stream=True))
    assert resp.status_code == 200
    events = sse_events(resp.text)
    assert events[-1]["data"] == "[DONE]"
    data_events = [e["data"] for e in events if "data" in e]
    errs = [json.loads(x) for x in data_events if x != "[DONE]"]
    assert errs and errs[-1]["error"]["code"] == code


def test_classify_endpoint():
    client, _ = make_client()
    resp = client.post("/v1/classify", headers=AUTH,
                       json={"text": "watchdog timer"})
    assert resp.status_code == 200
    assert resp.json()["domain"] == "embedded"
    assert resp.json()["adapter"] == "lora_embedded"
    assert client.post("/v1/classify",
                       json={"text": "x"}).status_code == 401


def test_optional_auth_mode():
    app = create_app(gateway=FakeGateway(),
                     settings=Settings(auth_mode="optional", api_key=None),
                     readiness_probe=lambda: True)
    client = TestClient(app)
    assert client.get("/v1/models").status_code == 200
    assert client.get("/v1/models", headers={
        "Authorization": "Bearer wrong"}).status_code == 401


def test_disabled_auth_mode():
    app = create_app(gateway=FakeGateway(),
                     settings=Settings(auth_mode="disabled", api_key=None),
                     readiness_probe=lambda: True)
    assert TestClient(app).get("/v1/models").status_code == 200


def test_required_auth_without_key_refuses_boot():
    with pytest.raises(RuntimeError):
        create_app(gateway=FakeGateway(),
                   settings=Settings(auth_mode="required", api_key=None))
