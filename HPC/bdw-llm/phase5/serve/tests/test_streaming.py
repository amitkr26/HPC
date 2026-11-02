"""P5.1 live SSE proxy tests - HTTP surface of stream_chat_events().

Runs the shim over TestClient with FakeStreamingGateway (ask_stream
contract) and pins: role-first chunking, heartbeat-before-first-delta,
in-band pre-delta failures, rate limits, mid-stream failures, usage
pass-through vs fallback, metadata passthrough, the P5.0 fallback switch,
and direct-drive cancellation reaching the gateway generator.
"""
from __future__ import annotations

import asyncio
import json
import time

from fastapi.testclient import TestClient

from phase5.serve.main import (
    ChatRequest,
    Message,
    Settings,
    create_app,
    stream_chat_events,
)
from phase5.serve.tests.fake_gateway import (
    ANSWER,
    FakeGateway,
    FakeStreamingGateway,
)

KEY = "p5-stream-key"
AUTH = {"Authorization": "Bearer " + KEY}


def make_client(gateway=None, **settings_kw):
    gateway = gateway if gateway is not None else FakeStreamingGateway()
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
        "stream": True,
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


def payloads_of(text: str):
    return [json.loads(e["data"]) for e in sse_events(text)
            if "data" in e and e["data"] != "[DONE]"]


def content_of(payloads):
    return "".join(p["choices"][0]["delta"].get("content", "")
                   for p in payloads
                   if "error" not in p)


# --- live path contract -----------------------------------------------------

def test_live_stream_contract_usage_and_metadata():
    client, gw = make_client()
    resp = client.post("/v1/chat/completions", headers=AUTH,
                       json=chat_body())
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    assert gw.ask_stream_used is True
    events = sse_events(resp.text)
    assert events[-1]["data"] == "[DONE]"
    payloads = payloads_of(resp.text)
    assert payloads
    for p in payloads:
        assert p["object"] == "chat.completion.chunk"
        assert p["choices"][0]["index"] == 0
        assert p["model"] == "bdw-career-ai"
        assert p["id"].startswith("chatcmpl-")
    # role chunk arrives first, then live deltas reassemble the answer
    assert payloads[0]["choices"][0]["delta"] == {
        "role": "assistant", "content": ""}
    assert content_of(payloads) == ANSWER
    final = payloads[-1]
    assert final["choices"][0]["finish_reason"] == "stop"
    # usage fell back to the char estimate (gateway reported none)
    assert final["usage"]["total_tokens"] > 0
    # metadata came from the final event's meta
    assert final["bdw"]["domain"] == "vlsi"
    assert final["bdw"]["adapter"] == "lora_vlsi"
    assert final["bdw"]["citations_dropped"] == ["99"]
    assert final["bdw"]["grounded"] is True
    # forward controls unchanged
    call = gw.calls[-1]
    assert call["question"] == "What is setup time in a flip flop?"
    assert call["force_domain"] is None


def test_live_stream_passes_upstream_usage_through():
    usage = {"prompt_tokens": 5, "completion_tokens": 7, "total_tokens": 12}
    client, _ = make_client(gateway=FakeStreamingGateway(usage=usage))
    resp = client.post("/v1/chat/completions", headers=AUTH,
                       json=chat_body())
    payloads = payloads_of(resp.text)
    assert payloads[-1]["usage"] == usage


def test_live_heartbeat_flows_before_first_delta():
    client, gw = make_client(
        gateway=FakeStreamingGateway(first_delay=0.35),
        sse_heartbeat_s=0.1)
    resp = client.post("/v1/chat/completions", headers=AUTH,
                       json=chat_body())
    assert resp.status_code == 200
    assert ": ping" in resp.text
    # at least one heartbeat precedes the first data frame
    blocks = [b for b in resp.text.split("\n\n") if b.strip()]
    first_ping = next(i for i, b in enumerate(blocks) if ": ping" in b)
    first_data = next(i for i, b in enumerate(blocks)
                      if b.lstrip().startswith("data: ")
                      and "[DONE]" not in b)
    assert first_ping < first_data
    assert gw.ask_stream_used is True
    assert sse_events(resp.text)[-1]["data"] == "[DONE]"


# --- in-band failures before the first delta --------------------------------

def test_live_pre_delta_timeout_is_in_band():
    client, gw = make_client(
        gateway=FakeStreamingGateway(behavior="timeout"),
        sse_heartbeat_s=0.1)
    resp = client.post("/v1/chat/completions", headers=AUTH,
                       json=chat_body())
    assert resp.status_code == 200
    events = sse_events(resp.text)
    assert events[-1]["data"] == "[DONE]"
    payloads = payloads_of(resp.text)
    errs = [p["error"] for p in payloads if "error" in p]
    assert errs and errs[-1]["code"] == "upstream_timeout"
    # nothing but the error may precede it (no role/content frames)
    assert content_of(payloads) == ""
    assert not any(p.get("choices") for p in payloads)
    assert gw.stream_closed is True


def test_live_pre_delta_upstream_error_is_in_band():
    client, _ = make_client(gateway=FakeStreamingGateway(behavior="error"),
                            sse_heartbeat_s=0.1)
    resp = client.post("/v1/chat/completions", headers=AUTH,
                       json=chat_body())
    assert resp.status_code == 200
    payloads = payloads_of(resp.text)
    errs = [p["error"] for p in payloads if "error" in p]
    assert errs and errs[-1]["code"] == "upstream_error"
    assert sse_events(resp.text)[-1]["data"] == "[DONE]"


def test_live_rate_limit_is_in_band():
    client, _ = make_client(gateway=FakeStreamingGateway(behavior="rate"))
    resp = client.post("/v1/chat/completions", headers=AUTH,
                       json=chat_body())
    assert resp.status_code == 200
    payloads = payloads_of(resp.text)
    errs = [p["error"] for p in payloads if "error" in p]
    assert errs and errs[-1]["code"] == "rate_limit_exceeded"
    assert errs[-1]["type"] == "rate_limit_error"
    assert sse_events(resp.text)[-1]["data"] == "[DONE]"


def test_live_midstream_failure_emits_deltas_then_error_without_finish():
    client, gw = make_client(
        gateway=FakeStreamingGateway(fail_after=2),
        sse_heartbeat_s=0.1)
    resp = client.post("/v1/chat/completions", headers=AUTH,
                       json=chat_body())
    assert resp.status_code == 200
    payloads = payloads_of(resp.text)
    errs = [p for p in payloads if "error" in p]
    assert errs and errs[-1]["error"]["code"] == "upstream_error"
    # some content flowed before the failure...
    assert content_of(payloads)
    # ...and no finish/usage frame is ever sent after an error
    assert not any(p.get("choices")
                   and p["choices"][0].get("finish_reason")
                   for p in payloads)
    assert sse_events(resp.text)[-1]["data"] == "[DONE]"
    assert gw.stream_closed is True


# --- P5.0 fallback switch ---------------------------------------------------

def test_gateway_without_ask_stream_falls_back_to_post_generation():
    gw = FakeGateway()  # no ask_stream attribute
    client, _ = make_client(gateway=gw, sse_chunk_chars=16)
    resp = client.post("/v1/chat/completions", headers=AUTH,
                       json=chat_body())
    assert resp.status_code == 200
    payloads = payloads_of(resp.text)
    assert content_of(payloads) == ANSWER
    assert payloads[0]["choices"][0]["delta"] == {
        "role": "assistant", "content": ""}
    assert payloads[-1]["choices"][0]["finish_reason"] == "stop"
    assert sse_events(resp.text)[-1]["data"] == "[DONE]"
    assert gw.calls  # ask() drove the response


def test_stream_upstream_flag_off_forces_post_generation():
    client, gw = make_client(gateway=FakeStreamingGateway(split=6),
                             stream_upstream=False, sse_chunk_chars=16)
    resp = client.post("/v1/chat/completions", headers=AUTH,
                       json=chat_body())
    assert resp.status_code == 200
    payloads = payloads_of(resp.text)
    assert content_of(payloads) == ANSWER
    # live path was available but disabled by P5_STREAM_UPSTREAM=0
    assert gw.ask_stream_used is False
    assert gw.calls  # fallback went through ask()


# --- cancellation -----------------------------------------------------------

async def _cancel_after_first_frame(agen):
    """Advance the SSE generator until a data frame arrives (heartbeats
    may legitimately come first), then close it - the GeneratorExit path
    a client disconnect takes."""
    for _ in range(100):
        item = await agen.__anext__()
        if item.lstrip().startswith("data:"):
            break
    else:
        raise AssertionError("no data frame before cancellation")
    await agen.aclose()


def _drain(closed):
    deadline = time.time() + 2.0
    while time.time() < deadline and not closed():
        time.sleep(0.02)
    return closed()


def test_direct_cancellation_closes_gateway_stream():
    gw = FakeStreamingGateway(split=6, chunk_delay=0.05)
    settings = Settings(auth_mode="required", api_key=KEY,
                        sse_heartbeat_s=0.05, stream_upstream=True)
    req = ChatRequest(messages=[Message(role="user", content="hello")])
    agen = stream_chat_events(
        gw, req, "What is setup time?", "user-1", None, [], None, None,
        None, None, settings, "chatcmpl-cancel", int(time.time()),
        "bdw-career-ai", time.perf_counter())

    asyncio.run(_cancel_after_first_frame(agen))
    # consumer disconnect -> producer observes `stop` -> gateway generator
    # closed (Zone 3 response released) even while deltas were pending
    assert _drain(lambda: gw.stream_closed)


def test_cancellation_releases_inflight_gauge():
    from prometheus_client import REGISTRY

    def inflight():
        return REGISTRY.get_sample_value(
            "bdw_shim_requests_in_flight", {"route": "chat"}) or 0.0

    gw = FakeStreamingGateway(split=6, chunk_delay=0.05)
    settings = Settings(auth_mode="required", api_key=KEY,
                        sse_heartbeat_s=0.05)
    req = ChatRequest(messages=[Message(role="user", content="hello")])
    before = inflight()
    agen = stream_chat_events(
        gw, req, "q", "u", None, [], None, None, None, None, settings,
        "chatcmpl-gauge", int(time.time()), "bdw-career-ai",
        time.perf_counter())

    asyncio.run(_cancel_after_first_frame(agen))
    assert _drain(lambda: gw.stream_closed)
    # finally ran on aclose: gauge returned to its pre-session value
    assert inflight() == before
