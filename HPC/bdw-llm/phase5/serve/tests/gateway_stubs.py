"""Deterministic Zone 2 gateway stubs shared by the golden capture script
(capture_gateway_golden.py) and the post-refactor parity test
(test_gateway_parity.py).

Only the two I/O edges are stubbed - the retriever (fixture rows) and the
LLM (fixture answer). The real DomainClassifier (lexical, stdlib-only)
routes every question, so routing, prompt assembly, LoRA resolution,
rate limiting and the S5 citation verifier all exercise production code.

The fixture rows and answer are intentionally awkward: two stale citation
markers (`5` out of range, `abc` non-numeric) plus a text-form `[1]`
mention, so the golden output pins the verifier's strip/note behavior.
"""
from __future__ import annotations

from phase5.serve.runtime import load_gateway_module

CFG = {
    "RETRIEVAL_TOPK": 20,
    "MAX_TOKENS": 1024,
    "RATE_LIMIT_PER_USER_DAY": 3,
    "WEB_RAG_MODE": "auto",
    "WEB_TOPK": 5,
}

LORA_MAP = {"lora_vlsi": 3}

ROWS = [
    {"id": "chunk-0", "title": "Setup and hold time",
     "content": "Setup time is the window before the active clock edge "
                "during which data must be stable.",
     "source_url": "https://example.edu/setup-hold", "verified": True,
     "parent_type": "domain", "domain": "vlsi", "score": 0.81,
     "backend": "local"},
    {"id": "chunk-1", "title": "Sequential logic",
     "content": "Flip-flops sample their inputs on the active clock edge.",
     "source_url": "", "verified": True, "parent_type": "domain",
     "domain": "vlsi", "score": 0.62, "backend": "local"},
]

EMPTY_QUERY = "hello there, how are you"

LLM_ANSWER = (
    "Setup time is the window before the active clock edge during which "
    "data must be stable; hold time is the window after it. "
    '<cite id="0"/> The metastability risk grows with '
    '<cite id="5"/> while <cite id="abc"/> never matched the pattern. '
    "\n[1] Text-form mentions stay in the body.\n"
)


class StubRetriever:
    """Returns the fixture rows for every query except EMPTY_QUERY."""

    def __init__(self):
        self.calls = []

    def search(self, query, k, domain=None, rag_index=None):
        self.calls.append({"query": query, "k": k, "domain": domain,
                           "rag_index": rag_index})
        if query == EMPTY_QUERY:
            return []
        return list(ROWS)[:k]


class StubLLM:
    """Fixed non-stream answer; records every completion call."""

    def __init__(self, answer=LLM_ANSWER):
        self.answer = answer
        self.calls = []

    def complete(self, prompt, max_tokens=1024, lora_id=None,
                 temperature=0.0):
        self.calls.append({"prompt": prompt, "max_tokens": max_tokens,
                           "lora_id": lora_id, "temperature": temperature})
        return self.answer


def awkward_fragments(text, size=7):
    """Slice text into fixed-size fragments. With size=7 every 13-char
    <cite id="N"/> marker necessarily spans at least two deltas, which is
    exactly the split-marker case _CiteGate must survive."""
    return [text[i:i + size] for i in range(0, len(text), size)]


class StubStreamingLLM(StubLLM):
    """Streaming twin of StubLLM implementing the complete_stream contract
    of phase3/gateway/app.py:Zone3LLM (delta/usage events, generator-close
    flag), with failure injection for timeout and mid-stream tests."""

    def __init__(self, text=LLM_ANSWER, frag_size=7, fail_after=None,
                 failure=None, usage=None):
        super().__init__(answer=text)
        self.text = text
        self.frag_size = frag_size
        self.fail_after = fail_after       # deltas to emit before failing
        self.failure = failure             # exception instance (or None)
        self.usage = usage                 # final usage dict (or None)
        self.stream_calls = []
        self.stream_closed = False

    def complete_stream(self, prompt, max_tokens=1024, lora_id=None,
                        temperature=0.0):
        self.stream_calls.append({"prompt": prompt, "max_tokens": max_tokens,
                                  "lora_id": lora_id,
                                  "temperature": temperature})
        try:
            frags = awkward_fragments(self.text, self.frag_size)
            for i, frag in enumerate(frags):
                if (self.failure is not None
                        and self.fail_after is not None
                        and i >= self.fail_after):
                    raise self.failure
                yield {"type": "delta", "text": frag}
            if self.failure is not None and self.fail_after is None:
                raise self.failure
            if self.usage:
                yield {"type": "usage", "usage": dict(self.usage)}
        finally:
            self.stream_closed = True


def build_stub_gateway(lora_map=None, llm=None):
    """Return (module, gateway) with stub I/O edges and the real router."""
    mod = load_gateway_module()
    lmap = dict(LORA_MAP if lora_map is None else lora_map)

    def lora_resolver(adapter):
        if not adapter:
            return None
        return lmap.get(adapter)

    gate = mod.Gateway(StubRetriever(), llm or StubLLM(), dict(CFG),
                       web=None, lora_resolver=lora_resolver)
    return mod, gate


# Ordered golden cases. They share one gateway at capture time; the
# rate-limited case carries rate_hits_before so each test can rebuild the
# same limiter state on a fresh gateway.
GOLDEN_CASES = [
    {"name": "grounded_stale_cites",
     "rate_hits_before": 0,
     "inputs": {"question": "explain setup and hold time in cmos",
                "user_id": "user-a", "web_mode": None, "history": None,
                "system_prompt": None, "max_tokens": None,
                "temperature": None, "force_domain": None}},
    {"name": "freshness_question_without_web_client",
     "rate_hits_before": 0,
     "inputs": {"question": "latest mtech admissions deadline 2026",
                "user_id": "user-a", "web_mode": None, "history": None,
                "system_prompt": None, "max_tokens": None,
                "temperature": None, "force_domain": None}},
    {"name": "history_system_prompt_forced_domain_controls",
     "rate_hits_before": 0,
     "inputs": {"question": "derive the gradient of a convex loss function",
                "user_id": "user-a", "web_mode": "off",
                "history": [{"role": "user", "content": "first question"},
                            {"role": "assistant", "content": "first answer"}],
                "system_prompt": "You are BDW, deep-tech assistant.",
                "max_tokens": 512, "temperature": 0.4,
                "force_domain": "vlsi"}},
    {"name": "rate_limited_on_fourth_hit",
     "rate_hits_before": 3,
     "inputs": {"question": "explain setup and hold time in cmos",
                "user_id": "user-a", "web_mode": None, "history": None,
                "system_prompt": None, "max_tokens": None,
                "temperature": None, "force_domain": None}},
    {"name": "weak_local_general_question",
     "rate_hits_before": 0,
     "inputs": {"question": EMPTY_QUERY, "user_id": "user-b",
                "web_mode": None, "history": None, "system_prompt": None,
                "max_tokens": None, "temperature": None,
                "force_domain": None}},
]
