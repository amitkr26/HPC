"""Phase 4 - Dynamic domain router for the BDW assistant.

Intercepts a user query, classifies the engineering domain, and emits a
routing decision that names either a specialized LoRA adapter to hot-swap
or a technical RAG index to query. Classifier is keyword/heuristic based
by design (deterministic, zero external deps) but exposes pluggable
hooks so a model-backed classifier can be swapped in later without
changing the call contract.

Supported domains: math, vlsi, embedded, cs, aiml. Everything else is
routed to the general domain (base model + generic index).

Designed to drop into the existing Zone 2 gateway: instantiate
DomainClassifier once at startup, call .classify(question) per request,
and consume RoutingDecision.adapter / .rag_index / .confidence.

Usage:
    python domain_classifier.py --query "explain setup and hold time"
    python domain_classifier.py --self-test          (offline, prints JSON)
Exit marker: RESULT: P4_DOMAIN_CLASSIFIER_OK | P4_DOMAIN_CLASSIFIER_FAIL
"""
from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional


class Domain(str, Enum):
    MATH = "math"
    VLSI = "vlsi"
    EMBEDDED = "embedded"
    CS = "cs"
    AIML = "aiml"
    GENERAL = "general"


@dataclass(frozen=True)
class RoutingDecision:
    domain: Domain
    confidence: float
    adapter: Optional[str]
    rag_index: str
    reason: str
    matched_keywords: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "domain": self.domain.value,
            "confidence": round(self.confidence, 3),
            "adapter": self.adapter,
            "rag_index": self.rag_index,
            "reason": self.reason,
            "matched_keywords": self.matched_keywords,
        }


# ---------------------------------------------------------------------------
# Keyword lexicon per domain (lower-case, substring match on the query).
# Order matters: first-match wins on ties; more specific terms should be
# listed before generic ones.
# ---------------------------------------------------------------------------
_DOMAIN_KEYWORDS: Dict[Domain, List[str]] = {
    Domain.MATH: [
        "calculus", "derivative", "integral", "differential equation",
        "linear algebra", "eigenvalue", "matrix", "vector space",
        "probability", "statistics", "bayes", "theorem", "proof",
        "lemma", "optimization", "convex", "gradient", "laplace",
        "fourier", "z-transform", "numerical", "root finding",
    ],
    Domain.VLSI: [
        "verilog", "vhdl", "systemverilog", "rtl", "synthesis",
        "place and route", "placement", "routing", "asic", "fpga",
        "setup time", "hold time", "static timing analysis", "sta",
        "clock gating", "power gating", "macro", "standard cell",
        "spice", "hspice", "cadence", "synopsys", "mentor", "lithography",
        "cmos", "transistor", "gate", "netlist", "floorplan", "drc", "lvs",
        "tapeout", "physical design", "timing closure", "scan", "dft",
    ],
    Domain.EMBEDDED: [
        "mcu", "microcontroller", "arm", "cortex", "rtos", "freertos",
        "zephyr", "gpio", "i2c", "spi", "uart", "can bus", "interrupt",
        "isr", "dma", "bootloader", "bare metal", "embedded c", "stm32",
        "nrf", "esp32", "watchdog", "sleep mode", "low power", "jtag",
        "swd", "debugger", "linker script", "memory map", "register",
        "peripheral", "bare-metal", "firmware",
    ],
    Domain.CS: [
        "algorithm", "data structure", "big-o", "complexity", "sorting",
        "graph", "tree", "compiler", "kernel", "os", "operating system",
        "distributed", "tcp/ip", "http", "database", "sql", "concurrency",
        "thread", "lock", "deadlock", "virtual memory", "paging",
        "file system", "rest", "grpc", "api", "git", "python", "java",
        "c++", "rust", "javascript",
    ],
    Domain.AIML: [
        "neural network", "transformer", "llm", "cuda", "pytorch",
        "tensorflow", "backpropagation", "deep learning", "machine learning",
        "fine-tuning", "fine tuning", "quantization",
        "embedding", "vector database", "rag", "attention", "diffusion",
        "computer vision", "nlp", "reinforcement learning", "tokenizer",
        "checkpoint", "weights", "inference", "training", "model",
        "lora", "adapter",
    ],
}

# ---------------------------------------------------------------------------
# Routing targets per domain: (lora adapter name, rag index name).
# adapter=None means "keep the base model".
# ---------------------------------------------------------------------------
_ROUTING_TARGETS: Dict[Domain, tuple[Optional[str], str]] = {
    Domain.MATH: ("lora_math", "idx_math"),
    Domain.VLSI: ("lora_vlsi", "idx_vlsi"),
    Domain.EMBEDDED: ("lora_embedded", "idx_embedded"),
    Domain.CS: ("lora_cs", "idx_cs"),
    Domain.AIML: ("lora_aiml", "idx_aiml"),
    Domain.GENERAL: (None, "idx_general"),
}

# Confidence thresholds
HIGH_CONFIDENCE = 0.85
MED_CONFIDENCE = 0.55

# Default system-prompt prefix injected per domain by the gateway.
_DOMAIN_PROMPT_PREFIX: Dict[Domain, str] = {
    Domain.MATH: "You are a mathematics expert. Show derivations step by step.",
    Domain.VLSI: "You are a VLSI design expert. Reference timing/physical constraints.",
    Domain.EMBEDDED: "You are an embedded-systems expert. Reference MCU peripherals and RTOS behavior.",
    Domain.CS: "You are a computer-science expert. Favor complexity analysis and concrete examples.",
    Domain.AIML: "You are an AI/ML expert. Reference model architectures and training details.",
    Domain.GENERAL: "You are a helpful technical assistant.",
}


class DomainClassifier:
    """Keyword-driven domain classifier with pluggable override hooks."""

    def __init__(
        self,
        keywords: Optional[Dict[Domain, List[str]]] = None,
        targets: Optional[Dict[Domain, tuple[Optional[str], str]]] = None,
        custom_hook: Optional[Callable[[str], Optional[RoutingDecision]]] = None,
    ) -> None:
        self.keywords = dict(keywords) if keywords else _DOMAIN_KEYWORDS
        self.targets = dict(targets) if targets else _ROUTING_TARGETS
        self.custom_hook = custom_hook

    # -- public API --------------------------------------------------------

    def classify(self, query: str) -> RoutingDecision:
        """Return the routing decision for a user query."""
        if not query or not query.strip():
            return self._decision(Domain.GENERAL, 0.0, [], "empty query -> general")

        normalized = query.lower()

        # 1) custom hook first (model-backed or rule-based override)
        if self.custom_hook is not None:
            override = self.custom_hook(query)
            if override is not None:
                return override

        # 2) keyword scoring across domains
        scores: Dict[Domain, int] = {}
        matched: Dict[Domain, List[str]] = {}
        for domain, terms in self.keywords.items():
            hits = [t for t in terms if t in normalized]
            if hits:
                scores[domain] = len(hits)
                matched[domain] = hits

        if not scores:
            return self._decision(
                Domain.GENERAL, 0.0, [], "no domain keywords matched -> general"
            )

        best_domain = max(scores, key=lambda d: scores[d])
        best_hits = scores[best_domain]
        total_hits = sum(scores.values())

        # Confidence: share of hits on the winner, floored/capped.
        confidence = min(best_hits / max(total_hits, 1), 1.0)
        runner_up = max(
            [s for d, s in scores.items() if d != best_domain],
            default=0,
        )
        # A clear winner (strictly more hits than any rival, >= 2 hits)
        # is a definitive routing decision -> full confidence.
        if best_hits >= 2 and best_hits > runner_up:
            confidence = 1.0
        elif best_hits >= 3:
            confidence = max(confidence, HIGH_CONFIDENCE)
        elif best_hits >= 2:
            confidence = max(confidence, MED_CONFIDENCE)

        return self._decision(
            best_domain,
            confidence,
            matched[best_domain],
            f"{best_hits} keyword hit(s) for {best_domain.value}",
        )

    def register_hook(
        self, hook: Callable[[str], Optional[RoutingDecision]]
    ) -> None:
        """Replace/add a custom pre-classification hook."""
        self.custom_hook = hook

    def prompt_prefix(self, domain: Domain) -> str:
        """System-prompt prefix the gateway can prepend for the domain."""
        return _DOMAIN_PROMPT_PREFIX.get(domain, _DOMAIN_PROMPT_PREFIX[Domain.GENERAL])

    # -- internals ---------------------------------------------------------

    def _decision(
        self,
        domain: Domain,
        confidence: float,
        keywords: List[str],
        reason: str,
    ) -> RoutingDecision:
        adapter, rag_index = self.targets.get(
            domain, self.targets[Domain.GENERAL]
        )
        return RoutingDecision(
            domain=domain,
            confidence=confidence,
            adapter=adapter,
            rag_index=rag_index,
            reason=reason,
            matched_keywords=list(keywords),
        )


def _self_test() -> bool:
    cases = [
        ("explain setup and hold time in cmos", Domain.VLSI, "lora_vlsi"),
        ("stm32 gpio interrupt handler in bare metal c", Domain.EMBEDDED, "lora_embedded"),
        ("derive the gradient of a convex loss function", Domain.MATH, "lora_math"),
        ("big-o complexity of graph traversal", Domain.CS, "lora_cs"),
        ("fine-tune a transformer with lora on a single gpu", Domain.AIML, "lora_aiml"),
        ("hello how are you", Domain.GENERAL, None),
    ]
    clf = DomainClassifier()
    ok = True
    for query, expect_domain, expect_adapter in cases:
        dec = clf.classify(query)
        match = dec.domain == expect_domain and dec.adapter == expect_adapter
        ok = ok and match
        print(json.dumps(dec.to_dict(), indent=2))
        print("EXPECT domain=%s adapter=%s -> %s\n"
              % (expect_domain.value, expect_adapter, "PASS" if match else "FAIL"))
    print("RESULT: %s" % ("P4_DOMAIN_CLASSIFIER_OK" if ok else "P4_DOMAIN_CLASSIFIER_FAIL"))
    return ok


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phase 4 dynamic domain router scaffold"
    )
    parser.add_argument("--query", help="user query to classify")
    parser.add_argument(
        "--self-test", action="store_true", help="run built-in classification suite"
    )
    args = parser.parse_args()

    clf = DomainClassifier()
    if args.self_test:
        _self_test()
        return
    if args.query:
        dec = clf.classify(args.query)
        print(json.dumps(dec.to_dict(), indent=2))
        print("RESULT: P4_DOMAIN_CLASSIFIER_OK")
        return
    parser.print_help()


if __name__ == "__main__":
    main()
