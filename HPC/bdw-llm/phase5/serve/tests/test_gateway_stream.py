"""P5.1 Gateway.ask_stream() unit tests - no HTTP layer.

Covers the gateway-side streaming contract: event protocol, streaming
citation gate (markers split across deltas), stale-marker stripping +
S5 note parity with ask(), usage pass-through, error events, cancellation
closing the Zone 3 stream, and Zone3LLM.complete_stream()'s SSE parsing
(including the stream_options 400 retry that covers llama-server and
vLLM behind one client).
"""
from __future__ import annotations

import json

import pytest
import requests as _requests

from phase5.serve.tests.gateway_stubs import (
    LLM_ANSWER,
    StubStreamingLLM,
    awkward_fragments,
    build_stub_gateway,
)

ASK_INPUT = {"question": "explain setup and hold time in cmos",
             "user_id": "user-a", "web_mode": None, "history": None,
             "system_prompt": None, "max_tokens": None,
             "temperature": None, "force_domain": None}


def squash(text):
    """Whitespace-insensitive normalization: the streamed concatenation is
    unstripped raw text while final.answer is the verifier's whole-string
    stripped form, so only whitespace may differ at the edges."""
    return " ".join(str(text).split())


def run_stream(gateway, **overrides):
    kwargs = dict(ASK_INPUT)
    kwargs.update(overrides)
    return list(gateway.ask_stream(**kwargs))


# --- ask() parity ----------------------------------------------------------

def test_stream_final_and_meta_match_ask_exactly():
    _, plain = build_stub_gateway()
    expected, status, err = plain.ask(**ASK_INPUT)
    assert status == 200 and err is None

    llm = StubStreamingLLM(frag_size=7)
    _, streamed = build_stub_gateway(llm=llm)
    events = run_stream(streamed)
    kinds = [e["type"] for e in events]
    assert kinds[-1] == "final"
    assert "error" not in kinds

    final = events[-1]
    assert final["answer"] == expected["answer"]
    assert final["meta"] == expected["meta"]
    concat = "".join(e["text"] for e in events
                     if e["type"] == "delta")
    assert squash(concat) == squash(final["answer"])


def test_stream_receives_usage_event_from_upstream():
    usage = {"prompt_tokens": 11, "completion_tokens": 22,
             "total_tokens": 33}
    llm = StubStreamingLLM(usage=usage)
    _, gw = build_stub_gateway(llm=llm)
    final = run_stream(gw)[-1]
    assert final["usage"] == usage


def test_stream_without_upstream_usage_reports_null():
    llm = StubStreamingLLM(usage=None)
    _, gw = build_stub_gateway(llm=llm)
    assert run_stream(gw)[-1]["usage"] is None


# --- streaming citation gate ----------------------------------------------

def test_split_marker_is_never_leaked_incomplete():
    llm = StubStreamingLLM(frag_size=7)
    _, gw = build_stub_gateway(llm=llm)
    deltas = [e["text"] for e in run_stream(gw) if e["type"] == "delta"]
    # the raw answer splits <cite id="0"/> across fragments; the gate must
    # only ever emit complete markers (or verbatim flush at end-of-stream)
    concat = "".join(deltas)
    assert "<cite id=\"0\"/>" in concat
    assert concat.count("<cite") == concat.count("/>")
    # no delta may END on a dangling '<cite' prefix that later completes
    for d in deltas[:-1]:
        assert not d.rstrip().endswith("<cite")
        assert 'id="' not in d or d.count('id="') == d.count("/>")


def test_stale_markers_are_dropped_from_the_stream_and_noted():
    _, gw = build_stub_gateway(llm=StubStreamingLLM())
    events = run_stream(gw)
    concat = "".join(e["text"] for e in events if e["type"] == "delta")
    final = events[-1]
    assert '<cite id="5"/>' not in concat
    assert '<cite id="abc"/>' not in concat
    assert final["meta"]["citations_dropped"] == ["5", "abc"]
    assert final["meta"]["citations_kept"] == ["0"]
    assert final["answer"].endswith(
        "[Note: one or more citation marks were removed "
        "by the server-side verifier (S5).]")
    assert squash(final["answer"]) == squash(concat)


def test_dangling_partial_marker_is_flushed_verbatim():
    text = "Grounded claim. <cite id=\"0\"/> tail <cite id=\"1"
    llm = StubStreamingLLM(text=text, frag_size=100)
    _, gw = build_stub_gateway(llm=llm)
    events = run_stream(gw)
    concat = "".join(e["text"] for e in events if e["type"] == "delta")
    assert concat.endswith('tail <cite id="1')
    final = events[-1]
    # verify_citations leaves unmatched fragments literal -> parity
    assert final["answer"].endswith('tail <cite id="1')
    assert squash(concat) == squash(final["answer"])


def test_marker_contradicted_mid_stream_passes_through_as_text():
    # '<citement' starts with '<cite' but can never become a marker
    text = "before <citement after <cite id=\"0\"/> done"
    llm = StubStreamingLLM(text=text, frag_size=8)
    _, gw = build_stub_gateway(llm=llm)
    events = run_stream(gw)
    concat = "".join(e["text"] for e in events if e["type"] == "delta")
    assert "<citement after" in squash(concat)
    assert final_ok(events)


@pytest.mark.parametrize("split_at", [1, 2, 3, 4, 5, 6])
def test_marker_never_reassembles_across_deltas_unevenly(split_at):
    """Whatever the fragment boundary, each emitted delta must contain
    either no part of a marker or a complete marker - a stale marker
    split across deltas must be dropped, a valid one emitted whole."""
    text = 'A <cite id="5"/> B <cite id="0"/> C'
    start = text.index("<cite") + split_at  # cut inside the first marker
    frags = [text[:start], text[start:start + 3], text[start + 3:]]
    llm = StubStreamingLLM(text=text, frag_size=10 ** 6)
    _, gw = build_stub_gateway(llm=llm)

    def split_stream(prompt, max_tokens=1024, lora_id=None,
                     temperature=0.0):
        try:
            for f in frags:
                yield {"type": "delta", "text": f}
        finally:
            llm.stream_closed = True

    llm.complete_stream = split_stream
    events = run_stream(gw)
    deltas = [e["text"] for e in events if e["type"] == "delta"]
    for d in deltas:
        low = d.lower()
        # no fragment may end on a partial opener
        for opener in ("<c", "<ci", "<cit"):
            assert not low.endswith(opener)
        # marker body and closer stay together (id-body and /> counts)
        assert d.count('id="') == d.count("/>")
    concat = "".join(deltas)
    assert '<cite id="5"/>' not in concat      # stale -> dropped
    assert concat.count('<cite id="0"/>') == 1  # valid -> kept once
    assert events[-1]["type"] == "final"
    assert events[-1]["meta"]["citations_dropped"] == ["5"]


def final_ok(events):
    return events[-1]["type"] == "final"


@pytest.mark.parametrize("tail,possible", [
    ("<cite", True),
    ("<cite ", True),
    ("<cite id=", True),
    ('<cite id="0', True),
    ('<cite id="0"', True),
    ('<cite id="0"/', True),
    ('<cite id="0">', True),
    ("<CITE ID=", True),
    ("<citement", False),
    ("<cite>", False),
    ('<cite id=""', False),
    ('<cite id="0" x', False),
    ("plain text", False),
])
def test_cite_prefix_possible_scanner(tail, possible):
    from phase5.serve.runtime import load_gateway_module
    mod = load_gateway_module()
    assert mod._cite_prefix_possible(tail) is possible


# --- error events ----------------------------------------------------------

def test_rate_limit_yields_single_error_event():
    _, gw = build_stub_gateway(llm=StubStreamingLLM())
    for _ in range(3):
        gw.lim.hit(ASK_INPUT["user_id"])
    events = run_stream(gw)
    assert events == [{"type": "error", "status": 429,
                       "code": "rate_limit_exceeded",
                       "message": "rate limit reached; retry tomorrow"}]


@pytest.mark.parametrize("failure,status,code,message", [
    (TimeoutError("upstream timeout"), 504, "upstream_timeout",
     "upstream inference timed out"),
    (RuntimeError("upstream exploded"), 502, "upstream_error",
     "upstream inference failed"),
])
def test_failure_before_first_delta_yields_error_event(failure, status,
                                                       code, message):
    llm = StubStreamingLLM(fail_after=0, failure=failure)
    _, gw = build_stub_gateway(llm=llm)
    events = run_stream(gw)
    assert events == [{"type": "error", "status": status, "code": code,
                       "message": message}]
    assert llm.stream_closed is True


def test_midstream_failure_after_deltas_yields_error_then_no_final():
    llm = StubStreamingLLM(fail_after=3, failure=RuntimeError("broke"))
    _, gw = build_stub_gateway(llm=llm)
    events = run_stream(gw)
    assert events[-1]["type"] == "error"
    assert events[-1]["status"] == 502
    assert not any(e["type"] == "final" for e in events)
    assert any(e["type"] == "delta" for e in events)
    assert llm.stream_closed is True


def test_read_timeout_from_requests_maps_to_504():
    # requests' read timeout surfaces as ReadTimeout (name contains Timeout)
    class ReadTimeout(_requests.exceptions.ReadTimeout):
        pass
    llm = StubStreamingLLM(fail_after=1, failure=ReadTimeout("stalled"))
    _, gw = build_stub_gateway(llm=llm)
    events = run_stream(gw)
    assert events[-1]["type"] == "error"
    assert events[-1]["status"] == 504


# --- cancellation ----------------------------------------------------------

def test_consumer_close_propagates_to_zone3_stream():
    llm = StubStreamingLLM(frag_size=5)
    _, gw = build_stub_gateway(llm=llm)
    gen = gw.ask_stream(**ASK_INPUT)
    first = next(gen)
    assert first["type"] == "delta"
    gen.close()
    assert llm.stream_closed is True
    # closing twice is a no-op, like any generator
    gen.close()


def test_close_before_first_next_never_touches_zone3():
    llm = StubStreamingLLM()
    _, gw = build_stub_gateway(llm=llm)
    gen = gw.ask_stream(**ASK_INPUT)
    gen.close()
    assert llm.stream_closed is False
    assert llm.stream_calls == []


# --- Zone3LLM.complete_stream SSE parsing -----------------------------------

class _FakeResp:
    def __init__(self, status_code=200, lines=()):
        self.status_code = status_code
        self._lines = list(lines)
        self.closed = False
        self.raise_calls = 0

    def raise_for_status(self):
        self.raise_calls += 1
        if self.status_code >= 400:
            raise _requests.HTTPError("http %d" % self.status_code)

    def iter_lines(self, decode_unicode=True):  # noqa: ARG002
        for line in self._lines:
            yield line

    def close(self):
        self.closed = True


def _sse_lines(*texts, usage=None, done=True):
    lines = []
    for t in texts:
        lines.append("data: " + json.dumps(
            {"choices": [{"delta": {"content": t}}]}))
    if usage is not None:
        lines.append("data: " + json.dumps(
            {"choices": [], "usage": usage}))
    if done:
        lines.append("data: [DONE]")
    return lines


def _zone3(mod):
    return mod.Zone3LLM("http://zone3.test:8080", timeout=5,
                        model="bdw-career-ai")


def test_complete_stream_parses_deltas_usage_and_done(monkeypatch):
    mod = build_stub_gateway()[0]
    resp = _FakeResp(lines=_sse_lines("Hello", " world",
                                      usage={"prompt_tokens": 3,
                                             "completion_tokens": 2,
                                             "total_tokens": 5}))
    bodies = []

    def fake_post(url, timeout=None, json=None, stream=None):  # noqa: A002
        bodies.append({"url": url, "json": json, "stream": stream})
        return resp

    monkeypatch.setattr(mod.requests, "post", fake_post)
    events = list(_zone3(mod).complete_stream("hi", max_tokens=9,
                                              temperature=0.5))
    assert [e["type"] for e in events] == ["delta", "delta", "usage"]
    assert events[0]["text"] == "Hello"
    assert events[2]["usage"]["total_tokens"] == 5
    assert bodies[0]["stream"] is True
    assert bodies[0]["json"]["stream"] is True
    assert bodies[0]["json"]["stream_options"] == {"include_usage": True}
    assert bodies[0]["json"]["model"] == "bdw-career-ai"
    assert bodies[0]["json"]["max_tokens"] == 9
    assert resp.closed is True


def test_complete_stream_retries_without_stream_options_on_400(monkeypatch):
    mod = build_stub_gateway()[0]
    first = _FakeResp(status_code=400, lines=["data: {\"error\":...}"])
    second = _FakeResp(lines=_sse_lines("ok"))
    calls = []

    def fake_post(url, timeout=None, json=None, stream=None):  # noqa: A002
        calls.append(dict(json))
        return first if len(calls) == 1 else second

    monkeypatch.setattr(mod.requests, "post", fake_post)
    events = list(_zone3(mod).complete_stream("hi"))
    assert len(calls) == 2
    assert "stream_options" in calls[0]
    assert "stream_options" not in calls[1]
    assert first.closed is True
    assert [e["text"] for e in events] == ["ok"]


def test_complete_stream_raises_on_http_error_and_closes(monkeypatch):
    mod = build_stub_gateway()[0]
    resp = _FakeResp(status_code=500)

    def fake_post(url, timeout=None, json=None, stream=None):  # noqa: A002
        return resp

    monkeypatch.setattr(mod.requests, "post", fake_post)
    with pytest.raises(_requests.HTTPError):
        list(_zone3(mod).complete_stream("hi"))
    assert resp.closed is True


def test_complete_stream_closes_connection_on_consumer_close(monkeypatch):
    mod = build_stub_gateway()[0]
    resp = _FakeResp(lines=_sse_lines(*awkward_fragments(LLM_ANSWER, 4)))

    def fake_post(url, timeout=None, json=None, stream=None):  # noqa: A002
        return resp

    monkeypatch.setattr(mod.requests, "post", fake_post)
    gen = _zone3(mod).complete_stream("hi")
    assert next(gen)["type"] == "delta"
    gen.close()
    assert resp.closed is True


def test_complete_stream_without_model_omits_the_field(monkeypatch):
    mod = build_stub_gateway()[0]
    resp = _FakeResp(lines=_sse_lines("x"))
    bodies = []

    def fake_post(url, timeout=None, json=None, stream=None):  # noqa: A002
        bodies.append(json)
        return resp

    monkeypatch.setattr(mod.requests, "post", fake_post)
    llm = mod.Zone3LLM("http://zone3.test:8080", timeout=5)
    list(llm.complete_stream("hi"))
    assert "model" not in bodies[0]
