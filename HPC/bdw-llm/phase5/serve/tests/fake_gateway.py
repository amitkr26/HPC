"""Deterministic stand-in for the Phase 3/4 Gateway used by contract tests.

Mirrors the exact return contract of phase3/gateway/app.py:Gateway.ask:
  ({"answer": str, "meta": dict}, 200, None)
  (None, 429, {"error": str})                       rate limited
  raises TimeoutError / RuntimeError                upstream failures
"""
from __future__ import annotations

import time

ANSWER = (
    "Setup time is the interval before the active clock edge during which "
    'data must be stable; hold time is the interval after it. '
    '<cite id="0"/> <cite id="99"/>'
)


class FakeDecision:
    def __init__(self, domain="embedded", confidence=0.88,
                 adapter="lora_embedded", rag_index="idx_embedded",
                 reason="test:fake"):
        self.domain = domain
        self.confidence = confidence
        self.adapter = adapter
        self.rag_index = rag_index
        self.reason = reason

    def to_dict(self):
        return {"domain": self.domain, "confidence": self.confidence,
                "adapter": self.adapter, "rag_index": self.rag_index,
                "reason": self.reason, "matched_keywords": ["watchdog"]}


class FakeClassifier:
    def classify(self, text):  # noqa: ARG002
        return FakeDecision()

    def prompt_prefix(self, domain):
        return "== DOMAIN PREFIX %s ==" % (
            domain.value if hasattr(domain, "value") else domain)


def fake_meta():
    return {
        "routing": {"mode": "auto", "web_used": False,
                    "reason": "local-sufficient", "history_turns": 1},
        "domain": {"domain": "vlsi", "confidence": 0.91,
                   "adapter": "lora_vlsi", "rag_index": "idx_vlsi",
                   "reason": "lexical+semantic",
                   "matched_keywords": ["setup time"]},
        "retrieval": {"domain_backend": "supabase"},
        "lora": {"adapter": "lora_vlsi", "llama_id": 1, "applied": True},
        "citations_kept": ["0"], "citations_dropped": ["99"],
        "chunks": [{
            "id": "957a56b904b543b1",
            "title": "Flip-flop (electronics)",
            "url": "https://en.wikipedia.org/wiki/Flip-flop_(electronics)",
            "verified": True,
            "source": "domain",
            "backend": "supabase",
        }],
    }


class FakeGateway:
    def __init__(self, answer=ANSWER, behavior="ok", delay=0.0):
        self.answer = answer
        self.behavior = behavior
        self.delay = delay
        self.calls = []
        self.classifier = FakeClassifier()

    def ask(self, question, user_id, web_mode=None, history=None,
            system_prompt=None, max_tokens=None, temperature=None,
            force_domain=None):
        self.calls.append({
            "question": question, "user_id": user_id, "web_mode": web_mode,
            "history": history, "system_prompt": system_prompt,
            "max_tokens": max_tokens, "temperature": temperature,
            "force_domain": force_domain,
        })
        if self.delay:
            time.sleep(self.delay)
        if self.behavior == "rate":
            return None, 429, {"error": "rate limit reached; retry tomorrow"}
        if self.behavior == "timeout":
            raise TimeoutError("upstream timeout")
        if self.behavior == "error":
            raise RuntimeError("upstream exploded")
        return {"answer": self.answer, "meta": fake_meta()}, 200, None
