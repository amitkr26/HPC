"""Phase 4 - Dynamic domain router for the BDW assistant.

Intercepts a user query, classifies the engineering domain, and emits a
routing decision that names either a specialized LoRA adapter to hot-swap
or a technical RAG index to query. Supports:
  - "hybrid": fast word-boundary lexical matching + dense semantic embedding
              scoring (BGE-small-en-v1.5) over precomputed domain anchors.
  - "semantic": pure dense embedding cosine similarity against domain anchors.
  - "keyword": legacy keyword/heuristic matching (zero external deps).
  - Pluggable custom_hook for arbitrary model/external overrides.

Supported domains: math, vlsi, embedded, cs, aiml. Everything else is
routed to the general domain (base model + generic index).

Designed to drop into the existing Zone 2 gateway: instantiate
DomainClassifier once at startup, call .classify(question) per request,
and consume RoutingDecision.adapter / .rag_index / .confidence.

Usage:
    python domain_classifier.py --query "explain setup and hold time"
    python domain_classifier.py --self-test
Exit marker: RESULT: P4_DOMAIN_CLASSIFIER_OK | P4_DOMAIN_CLASSIFIER_FAIL
"""
from __future__ import annotations

import argparse
import json
import os
import re
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Tuple


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
# Keyword lexicon per domain (word-boundary matched).
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
        "clock domain crossing", "metastability", "atpg", "jtag",
        "finfet", "chiplet", "uvm", "serdes", "pll",
        "useful skew", "eye diagram", "leakage current", "signal integrity",
    ],
    Domain.EMBEDDED: [
        "mcu", "microcontroller", "arm", "cortex", "rtos", "freertos",
        "zephyr", "gpio", "i2c", "spi", "uart", "can bus", "interrupt",
        "isr", "dma", "bootloader", "bare metal", "embedded c", "stm32",
        "nrf", "esp32", "watchdog", "sleep mode", "low power", "jtag",
        "swd", "debugger", "linker script", "memory map", "register",
        "peripheral", "bare-metal", "firmware", "priority inversion",
    ],
    Domain.CS: [
        "algorithm", "data structure", "big-o", "complexity", "sorting",
        "graph", "tree", "compiler", "kernel", "os", "operating system",
        "distributed", "tcp/ip", "http", "database", "sql", "concurrency",
        "thread", "lock", "deadlock", "virtual memory", "paging",
        "file system", "rest", "grpc", "api", "git", "python", "java",
        "c++", "rust", "javascript", "heapsort", "quicksort",
        "dynamic programming", "recurrence relation", "master theorem",
        "np-complete", "segfault", "segfaults", "malloc",
        "stack overflow", "memory leak", "memory leaks",
    ],
    Domain.AIML: [
        "neural network", "transformer", "llm", "cuda", "pytorch",
        "tensorflow", "backpropagation", "deep learning", "machine learning",
        "fine-tuning", "fine tuning", "quantization",
        "embedding", "vector database", "rag", "attention", "diffusion",
        "computer vision", "nlp", "reinforcement learning", "tokenizer",
        "checkpoint", "weights", "inference", "training", "model",
        "lora", "adapter", "gguf", "kv cache", "autoregressive",
        "overfitting", "regularization", "bias-variance",
        "cross-validation", "flash attention",
    ],
}

# ---------------------------------------------------------------------------
# Routing targets per domain: (lora adapter name, rag index name).
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
DEFAULT_SEMANTIC_THRESHOLD = 0.52
# A semantic winner is only trusted on its own when it has no lexical support
# AND clears a higher floor: pure conceptual paraphrases ("area between two
# curves") score >= 0.60, while off-domain prose ("summarize Hamlet") does not.
ZERO_LEXICAL_SEMANTIC_MIN = 0.60
# When the best and runner-up domains are nearly tied, the decision is
# ambiguous: prefer a supporting lexical winner, otherwise route to general.
MIN_SEMANTIC_MARGIN = 0.015

# Default system-prompt prefix injected per domain by the gateway.
_DOMAIN_PROMPT_PREFIX: Dict[Domain, str] = {
    Domain.MATH: "You are a mathematics expert. Show derivations step by step.",
    Domain.VLSI: "You are a VLSI design expert. Reference timing/physical constraints.",
    Domain.EMBEDDED: "You are an embedded-systems expert. Reference MCU peripherals and RTOS behavior.",
    Domain.CS: "You are a computer-science expert. Favor complexity analysis and concrete examples.",
    Domain.AIML: "You are an AI/ML expert. Reference model architectures and training details.",
    Domain.GENERAL: "You are a helpful technical assistant.",
}


# ---------------------------------------------------------------------------
# Dense Semantic Anchor Phrases (63 topics across 5 engineering domains)
# ---------------------------------------------------------------------------
_DOMAIN_ANCHOR_PHRASES: List[Tuple[Domain, str]] = [
    # Math
    (Domain.MATH, "calculus derivatives integrals limits fundamental theorem of calculus multivariable calculus"),
    (Domain.MATH, "linear algebra eigenvalues eigenvectors matrix factorization svd qr decomposition vector spaces"),
    (Domain.MATH, "probability theory bayes theorem conditional probability distributions random variables expectation"),
    (Domain.MATH, "mathematical statistics hypothesis testing maximum likelihood estimation confidence intervals"),
    (Domain.MATH, "mathematical optimization convex optimization lagrange multipliers gradient descent dual problem"),
    (Domain.MATH, "differential equations ordinary differential equations partial differential equations ode pde boundary value"),
    (Domain.MATH, "complex analysis fourier transform laplace transform z transform fourier series harmonic analysis"),
    (Domain.MATH, "numerical analysis root finding newton raphson numerical integration finite difference methods"),
    (Domain.MATH, "discrete mathematics combinatorics graph theory mathematical proofs lemmas axioms induction"),
    (Domain.MATH, "calculating the area enclosed between curves on a coordinate plane or integration limits"),
    # VLSI
    (Domain.VLSI, "static timing analysis setup time hold time clock skew clock jitter timing slack critical path"),
    (Domain.VLSI, "clock domain crossing metastability synchronizer two flip flop synchronizer async fifo"),
    (Domain.VLSI, "hardware description language verilog vhdl systemverilog behavioral rtl logic design"),
    (Domain.VLSI, "universal verification methodology uvm testbench assertions sva coverage driven verification formal verification"),
    (Domain.VLSI, "logic synthesis electronic design automation eda standard cell library logic gates netlist"),
    (Domain.VLSI, "physical design floorplanning placement routing clock tree synthesis cts power distribution network"),
    (Domain.VLSI, "design rule checking drc layout versus schematic lvs parasitic extraction rc delay"),
    (Domain.VLSI, "design for testability dft scan chain automatic test pattern generation atpg jtag boundary scan bist"),
    (Domain.VLSI, "semiconductor device fabrication photolithography extreme ultraviolet lithography euv etching cmp diffusion"),
    (Domain.VLSI, "transistor technology cmos mosfet finfet gate all around fet ribbonfet high-k metal gate"),
    (Domain.VLSI, "low power design clock gating power gating unified power format upf dynamic power leakage current"),
    (Domain.VLSI, "integrated circuit packaging 2.5d 3d ic chiplets cowos wire bonding ball grid array bga interposer"),
    (Domain.VLSI, "analog mixed signal phase locked loop pll serdes high speed serializer deserializer bandgap reference"),
    (Domain.VLSI, "interconnects signal integrity electromigration ir drop crosstalk noise coupling capacitance"),
    (Domain.VLSI, "application specific integrated circuit asic field programmable gate array fpga lookup tables clb"),
    (Domain.VLSI, "useful skew setup violation hold violation slack optimization eye diagram signal integrity high speed serial link serdes equalization"),
    # Embedded
    (Domain.EMBEDDED, "microcontroller firmware bare metal c programming arm cortex-m stm32 esp32 registers"),
    (Domain.EMBEDDED, "real time operating system rtos task scheduling preemptive priority inversion semaphore mutex isr"),
    (Domain.EMBEDDED, "hardware peripheral communication gpio i2c spi uart can bus usb serial interface"),
    (Domain.EMBEDDED, "direct memory access dma controller peripheral to memory transfer circular buffer"),
    (Domain.EMBEDDED, "interrupt handling nested vectored interrupt controller nvic isr latency interrupt service routine"),
    (Domain.EMBEDDED, "low power sleep modes deep sleep standby wake up timer battery operated embedded device"),
    (Domain.EMBEDDED, "watchdog timer system reset windowed watchdog brownout detector supervisor"),
    (Domain.EMBEDDED, "bootloader firmware update over the air ota flash memory partitioning linker script memory map"),
    (Domain.EMBEDDED, "embedded debugging jtag swd openocd gdb hardware breakpoints logic analyzer"),
    (Domain.EMBEDDED, "memory mapped input output mmio register bit manipulation device drivers peripheral configuration"),
    (Domain.EMBEDDED, "timers pwm generation input capture output compare dead time control motor control"),
    (Domain.EMBEDDED, "sensors actuators analog to digital converter adc sampling dac peripheral interface"),
    (Domain.EMBEDDED, "digital signal processing dsp low pass filter high pass filter ecg signal sampling filtering"),
    (Domain.EMBEDDED, "freertos real time operating system rtos task scheduling priority inversion mutex semaphore queue mailbox context switch"),
    # CS
    (Domain.CS, "data structures binary search tree red black tree avl tree hash map heap priority queue trie"),
    (Domain.CS, "algorithms sorting quicksort mergesort heapsort binary search graph traversal dfs bfs dijkstra"),
    (Domain.CS, "asymptotic time complexity space complexity big o notation computational complexity np complete"),
    (Domain.CS, "operating systems kernel virtual memory paging page table page fault cpu scheduling deadlock avoidance"),
    (Domain.CS, "concurrency multithreading race conditions mutex semaphores locks thread pool atomic operations"),
    (Domain.CS, "computer networking tcp ip stack udp socket programming http https dns routing congestion control"),
    (Domain.CS, "relational databases sql queries b tree indexing acid transactions foreign keys database normalization"),
    (Domain.CS, "distributed systems consensus algorithms raft paxos cap theorem distributed transactions rpc grpc"),
    (Domain.CS, "compilers lexical analysis parsing abstract syntax tree intermediate representation code generation"),
    (Domain.CS, "computer science software engineering design patterns object oriented programming functional programming"),
    (Domain.CS, "dynamic programming recurrence relation master theorem divide and conquer amortized analysis complexity classes np complete"),
    # AIML
    (Domain.AIML, "machine learning supervised learning unsupervised learning classification regression clustering evaluation"),
    (Domain.AIML, "deep learning artificial neural networks multilayer perceptron backpropagation gradient descent loss functions"),
    (Domain.AIML, "transformer architecture self attention multi head attention cross attention causal attention mechanism"),
    (Domain.AIML, "large language models llm pretraining instruction tuning rlhf alignment prompt engineering"),
    (Domain.AIML, "parameter efficient fine tuning peft lora low rank adaptation qlora adapter layers weights"),
    (Domain.AIML, "model optimization quantization gguf awq gptq pruning distillation kv cache tensor parallelism"),
    (Domain.AIML, "computer vision convolutional neural networks cnn object detection image segmentation resnet"),
    (Domain.AIML, "natural language processing nlp tokenization embeddings word2vec subword byte pair encoding"),
    (Domain.AIML, "retrieval augmented generation rag dense vector embeddings similarity search chunking reranker vector database"),
    (Domain.AIML, "reinforcement learning policy gradient q learning reward modeling markov decision process actor critic"),
    (Domain.AIML, "bias variance tradeoff overfitting underfitting regularization cross validation model selection generalization error"),
    (Domain.AIML, "kv cache key value cache autoregressive decoding inference latency memory bandwidth flash attention"),
]

# Default paths
_DEFAULT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DEFAULT_BGE_DIR = os.path.join(_DEFAULT_ROOT, "phase3", "models", "bge-small-en-v1.5")
_DEFAULT_ANCHORS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "domain_anchors.npz")


class DomainClassifier:
    """Hybrid domain classifier: word-boundary lexical matching + dense semantic embeddings."""

    def __init__(
        self,
        mode: str = "hybrid",
        keywords: Optional[Dict[Domain, List[str]]] = None,
        targets: Optional[Dict[Domain, tuple[Optional[str], str]]] = None,
        custom_hook: Optional[Callable[[str], Optional[RoutingDecision]]] = None,
        bge_dir: Optional[str] = None,
        anchors_path: Optional[str] = None,
        semantic_threshold: float = DEFAULT_SEMANTIC_THRESHOLD,
        embedder: Optional[object] = None,
    ) -> None:
        self.mode = mode.lower()
        self.keywords = dict(keywords) if keywords else _DOMAIN_KEYWORDS
        self.targets = dict(targets) if targets else _ROUTING_TARGETS
        self.custom_hook = custom_hook
        self.bge_dir = bge_dir or _DEFAULT_BGE_DIR
        self.anchors_path = anchors_path or _DEFAULT_ANCHORS_PATH
        self.semantic_threshold = float(semantic_threshold)

        self._embedder = embedder
        self._anchor_vecs = None
        self._anchor_domains = None
        self._semantic_failed = False
        self._encode_lock = threading.Lock()

        # Build word-boundary regexes for accurate lexical matching
        self._keyword_res: Dict[Domain, List[Tuple[str, re.Pattern]]] = {}
        for dom, terms in self.keywords.items():
            compiled = []
            for t in terms:
                pattern = r"\b" + re.escape(t) + r"\b"
                compiled.append((t, re.compile(pattern, re.IGNORECASE)))
            self._keyword_res[dom] = compiled

        # Load precomputed anchors if available
        if self.mode in ("hybrid", "semantic"):
            self._load_anchors()


    def build_anchors(self, output_path: Optional[str] = None) -> bool:
        """Precompute dense semantic anchor embeddings from _DOMAIN_ANCHOR_PHRASES."""
        target_path = output_path or self.anchors_path
        model = self._get_embedder()
        if model is None:
            print("[router] error: sentence-transformers model unavailable to build anchors")
            return False
        try:
            import numpy as np
            phrases = [text for _, text in _DOMAIN_ANCHOR_PHRASES]
            doms = [dom.value for dom, _ in _DOMAIN_ANCHOR_PHRASES]
            vecs = model.encode(phrases, normalize_embeddings=True, show_progress_bar=False)
            os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
            np.savez_compressed(
                target_path,
                vectors=vecs,
                domains=np.array(doms),
                texts=np.array(phrases),
            )
            self._anchor_vecs = vecs
            self._anchor_domains = np.array(doms)
            print(f"[router] successfully built {len(phrases)} domain anchors -> {target_path}")
            return True
        except Exception as e:
            print(f"[router] error building domain anchors: {e}")
            return False

    def _load_anchors(self) -> None:
        if not os.path.isfile(self.anchors_path):
            built = self.build_anchors(self.anchors_path)
            if not built:
                self._semantic_failed = True
                return
        try:
            import numpy as np
            data = np.load(self.anchors_path)
            expected = [text for _, text in _DOMAIN_ANCHOR_PHRASES]
            stored = list(data["texts"]) if "texts" in data.files else None
            # Self-healing: a stale anchor cache (lexicon/anchor edits) must be
            # re-encoded, otherwise semantic scores and domain labels drift.
            if stored is None or stored != expected:
                print("[router] anchor cache stale -> rebuilding")
                if not self.build_anchors(self.anchors_path):
                    self._anchor_vecs = data["vectors"]
                    self._anchor_domains = data["domains"]
                return
            self._anchor_vecs = data["vectors"]
            self._anchor_domains = data["domains"]
        except Exception as e:
            print(f"[router] warning: failed to load {self.anchors_path}: {e}")
            self._semantic_failed = True

    def _get_embedder(self):
        if self._embedder is not None:
            return self._embedder
        if self._semantic_failed:
            return None
        try:
            import torch
            torch.set_num_threads(4)
            from sentence_transformers import SentenceTransformer
            candidates = [
                self.bge_dir,
                os.path.join(os.path.expanduser("~"), "bdw-llm", "phase3", "models", "bge-small-en-v1.5"),
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "phase3", "models", "bge-small-en-v1.5"),
            ]
            chosen = None
            for c in candidates:
                if c and os.path.isdir(c):
                    chosen = c
                    break
            if chosen is not None:
                self._embedder = SentenceTransformer(chosen, device="cpu")
            else:
                try:
                    self._embedder = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu")
                except Exception:
                    self._semantic_failed = True
        except Exception as e:
            print(f"[router] warning: sentence_transformers unavailable: {e}")
            self._semantic_failed = True
        return self._embedder

    def _score_semantic(self, query: str) -> Optional[Tuple[Domain, float, float, Dict[str, float]]]:
        """Compute cosine similarity against domain semantic anchors."""
        if self._anchor_vecs is None or self._anchor_domains is None:
            return None
        model = self._get_embedder()
        if model is None:
            return None
        try:
            import numpy as np
            with self._encode_lock:
                q_vec = model.encode([query], normalize_embeddings=True)[0]
            sims = self._anchor_vecs @ q_vec

            domain_scores: Dict[str, float] = {}
            for dom in (Domain.MATH, Domain.VLSI, Domain.EMBEDDED, Domain.CS, Domain.AIML):
                mask = (self._anchor_domains == dom.value)
                if np.any(mask):
                    dom_sims = sims[mask]
                    # Score = 70% max anchor + 30% top-3 average
                    s_max = float(np.max(dom_sims))
                    s_top3 = float(np.mean(np.sort(dom_sims)[-3:])) if len(dom_sims) >= 3 else s_max
                    domain_scores[dom.value] = 0.70 * s_max + 0.30 * s_top3

            sorted_doms = sorted(domain_scores.items(), key=lambda x: -x[1])
            best_dom_str, best_score = sorted_doms[0]
            runner_up_score = sorted_doms[1][1] if len(sorted_doms) > 1 else 0.0
            return Domain(best_dom_str), best_score, runner_up_score, domain_scores
        except Exception as e:
            print(f"[router] semantic scoring error: {e}")
            return None

    # -- public API --------------------------------------------------------

    def classify(self, query: str) -> RoutingDecision:
        """Return the routing decision for a user query."""
        if not query or not query.strip():
            return self._decision(Domain.GENERAL, 0.0, [], "empty query -> general")

        # 1) custom hook first (external or manual override)
        if self.custom_hook is not None:
            override = self.custom_hook(query)
            if override is not None:
                return override

        # 2) lexical matching across domains
        scores: Dict[Domain, int] = {}
        matched: Dict[Domain, List[str]] = {}
        for domain, compiled_terms in self._keyword_res.items():
            hits = [orig for orig, rx in compiled_terms if rx.search(query)]
            if hits:
                scores[domain] = len(hits)
                matched[domain] = hits

        lex_best_domain = max(scores, key=lambda d: scores[d]) if scores else None
        lex_best_hits = scores.get(lex_best_domain, 0) if lex_best_domain else 0
        lex_runner_up = max([s for d, s in scores.items() if d != lex_best_domain], default=0)

        # Mode: pure keyword
        if self.mode == "keyword" or (self._semantic_failed and self.mode == "hybrid"):
            return self._lexical_decision(scores, matched, prefix="lexical")

        # Mode: semantic or hybrid
        sem_res = self._score_semantic(query)

        # Hybrid Decision Fusion
        if self.mode == "hybrid":
            # Semantic engine unavailable (missing model/index or an encode
            # failure): degrade to the deterministic lexical decision instead
            # of misrouting the first request to general.
            if sem_res is None:
                return self._lexical_decision(
                    scores, matched, prefix="lexical fallback (semantic unavailable)"
                )

            # Decisive lexical winner (>= 2 hits with strict dominant margin >= 2)
            if lex_best_hits >= 2 and (lex_best_hits - lex_runner_up) >= 2:
                return self._decision(
                    lex_best_domain,
                    1.0,
                    matched[lex_best_domain],
                    f"lexical decisive: {lex_best_hits} hits (margin={lex_best_hits - lex_runner_up}) for {lex_best_domain.value}",
                )

            sem_domain, sem_score, sem_runner_up, all_scores = sem_res
            margin = sem_score - sem_runner_up
            has_lexical = lex_best_hits > 0
            threshold = (
                self.semantic_threshold
                if has_lexical
                else max(self.semantic_threshold, ZERO_LEXICAL_SEMANTIC_MIN)
            )

            # Both lexical and semantic agree
            if lex_best_domain == sem_domain and sem_score >= threshold:
                conf = min(1.0, 0.70 + margin * 1.5)
                return self._decision(
                    sem_domain,
                    conf,
                    matched.get(sem_domain, []),
                    f"hybrid consensus: lex_hits={lex_best_hits}, sem_score={sem_score:.3f} (margin={margin:.3f}) for {sem_domain.value}",
                )

            # Lexical/semantic disagreement with a near-tie: keep the
            # word-boundary evidence rather than flipping on noise.
            if has_lexical and lex_best_domain != sem_domain and margin < MIN_SEMANTIC_MARGIN:
                return self._lexical_decision(
                    scores,
                    matched,
                    prefix="lexical override (semantic margin too small)",
                )

            # No lexical support and a near-tie in embedding space: the query
            # is off-domain prose, not a technical paraphrase.
            if not has_lexical and margin < MIN_SEMANTIC_MARGIN:
                return self._decision(
                    Domain.GENERAL,
                    round(1.0 - sem_score, 3),
                    [],
                    f"ambiguous semantic: score={sem_score:.3f} margin={margin:.3f} -> general",
                )

            # High semantic confidence overrides weak/zero keyword hit
            if sem_score >= threshold:
                conf = min(1.0, max(0.60, (sem_score - 0.45) / 0.35 + margin * 0.5))
                return self._decision(
                    sem_domain,
                    conf,
                    matched.get(sem_domain, []),
                    f"semantic match: score={sem_score:.3f} >= {threshold:.2f} (margin={margin:.3f}) for {sem_domain.value}",
                )

            # Below semantic threshold and no solid lexical match -> general
            return self._decision(
                Domain.GENERAL,
                round(1.0 - sem_score, 3),
                [],
                f"semantic below threshold: max_score={sem_score:.3f} < {threshold:.2f} -> general",
            )

        # Mode: pure semantic
        if self.mode == "semantic":
            if sem_res is not None:
                sem_domain, sem_score, sem_runner_up, _ = sem_res
                if sem_score >= self.semantic_threshold:
                    conf = min(1.0, (sem_score - 0.45) / 0.35)
                    return self._decision(
                        sem_domain,
                        conf,
                        matched.get(sem_domain, []),
                        f"semantic: score={sem_score:.3f} for {sem_domain.value}",
                    )
            return self._decision(
                Domain.GENERAL,
                0.0,
                [],
                "semantic: below threshold -> general",
            )

        # Fallback default
        return self._decision(Domain.GENERAL, 0.0, [], "fallback -> general")

    def register_hook(
        self, hook: Callable[[str], Optional[RoutingDecision]]
    ) -> None:
        """Replace/add a custom pre-classification hook."""
        self.custom_hook = hook

    def prompt_prefix(self, domain: Domain) -> str:
        """System-prompt prefix the gateway can prepend for the domain."""
        return _DOMAIN_PROMPT_PREFIX.get(domain, _DOMAIN_PROMPT_PREFIX[Domain.GENERAL])

    # -- internals ---------------------------------------------------------

    def _lexical_decision(
        self,
        scores: Dict[Domain, int],
        matched: Dict[Domain, List[str]],
        prefix: str = "lexical",
    ) -> RoutingDecision:
        """Deterministic word-boundary decision (also the semantic fallback)."""
        if not scores:
            return self._decision(
                Domain.GENERAL, 0.0, [], f"{prefix}: no domain keywords matched -> general"
            )
        best = max(scores, key=lambda d: scores[d])
        best_hits = scores[best]
        runner_up = max([s for d, s in scores.items() if d != best], default=0)
        confidence = min(best_hits / max(sum(scores.values()), 1), 1.0)
        if best_hits >= 2 and best_hits > runner_up:
            confidence = 1.0
        elif best_hits >= 2:
            confidence = max(confidence, MED_CONFIDENCE)
        return self._decision(
            best,
            confidence,
            matched[best],
            f"{prefix}: {best_hits} keyword hit(s) for {best.value}",
        )

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
    print("=" * 72)
    print("PHASE 4 HYBRID DOMAIN ROUTER SELF-TEST")
    print("=" * 72)
    clf = DomainClassifier(mode="hybrid")

    # Canonical cases (blueprint original contract)
    canonical_cases = [
        ("explain setup and hold time in cmos", Domain.VLSI, "lora_vlsi"),
        ("stm32 gpio interrupt handler in bare metal c", Domain.EMBEDDED, "lora_embedded"),
        ("derive the gradient of a convex loss function", Domain.MATH, "lora_math"),
        ("big-o complexity of graph traversal", Domain.CS, "lora_cs"),
        ("fine-tune a transformer with lora on a single gpu", Domain.AIML, "lora_aiml"),
        ("hello how are you", Domain.GENERAL, None),
    ]

    # Complex / Paraphrased non-keyword cases
    complex_cases = [
        ("how do you calculate the area enclosed between two intersecting curves on a plane", Domain.MATH, "lora_math"),
        ("what is the geometric interpretation of the determinant of a transformation matrix", Domain.MATH, "lora_math"),
        ("why do signals entering different clock domains cause unpredictable output states", Domain.VLSI, "lora_vlsi"),
        ("what causes capacitive crosstalk between adjacent parallel metal layers in a nanoscale chip", Domain.VLSI, "lora_vlsi"),
        ("how does uvm phase execution synchronize drivers monitors and scoreboards in a testbench", Domain.VLSI, "lora_vlsi"),
        ("how to configure an on-chip peripheral to transfer incoming samples to memory without cpu", Domain.EMBEDDED, "lora_embedded"),
        ("how to handle an unhandled exception in an interrupt handler on a Cortex-M4", Domain.EMBEDDED, "lora_embedded"),
        ("how do you configure a windowed watchdog to recover from firmware deadlock", Domain.EMBEDDED, "lora_embedded"),
        ("what is the worst-case number of comparisons in heapsort", Domain.CS, "lora_cs"),
        ("explain how the operating system handles a page fault when referencing swapped pages", Domain.CS, "lora_cs"),
        ("how does the two-phase commit protocol achieve atomicity in distributed databases", Domain.CS, "lora_cs"),
        ("why do deep networks suffer from vanishing activations during reverse mode differentiation", Domain.AIML, "lora_aiml"),
        ("how does quantized k-quants in gguf reduce memory footprint during inference", Domain.AIML, "lora_aiml"),
        ("why does lora update low-rank matrices instead of modifying full weight tensors", Domain.AIML, "lora_aiml"),
        ("what is the capital of France", Domain.GENERAL, None),
        ("how do I bake a chocolate cake at home", Domain.GENERAL, None),
    ]

    # Cross-domain / mixed-signal queries: the dominant domain must win even
    # when a secondary domain's vocabulary appears in the sentence.
    cross_cases = [
        ("write a verilog testbench to verify a uart transmitter", {Domain.VLSI, Domain.EMBEDDED}),
        ("implement a pid controller on an stm32 using fixed point arithmetic", {Domain.EMBEDDED}),
        ("use dynamic programming to optimize matrix chain multiplication", {Domain.CS, Domain.MATH}),
        ("what is the difference between a mutex and a semaphore in freertos", {Domain.EMBEDDED}),
        ("explain the bias variance tradeoff in model selection", {Domain.AIML}),
        ("what is the role of the kv cache during autoregressive decoding", {Domain.AIML}),
        ("solve the recurrence relation t(n) = 2t(n/2) + n", {Domain.CS, Domain.MATH}),
        ("why does my rtos task starve under priority inversion", {Domain.EMBEDDED}),
        ("how does clock gating reduce dynamic power in cmos", {Domain.VLSI}),
        ("give me a summary of the plot of hamlet", {Domain.GENERAL}),
        ("explain quantum entanglement and its applications", {Domain.GENERAL}),
    ]

    all_cases = (
        [("CANONICAL", c, {c[1]}) for c in canonical_cases]
        + [("COMPLEX", c, {c[1]}) for c in complex_cases]
        + [("CROSS", (q, None, None), expected) for q, expected in cross_cases]
    )
    ok = True
    passed = 0

    for suite, (query, expect_domain, expect_adapter), expected in all_cases:
        dec = clf.classify(query)
        match = dec.domain in expected
        if expect_adapter is not None:
            match = match and dec.adapter == expect_adapter
        ok = ok and match
        if match:
            passed += 1
        status = "PASS" if match else "FAIL"
        print(f"[{status}] suite={suite:<9} domain={dec.domain.value:<8} conf={dec.confidence:.2f} | query='{query[:55]}'")
        if not match:
            want = "/".join(sorted(d.value for d in expected))
            print(f"       EXPECTED: domain={want} adapter={expect_adapter}")
            print(f"       GOT:      domain={dec.domain.value} adapter={dec.adapter} reason={dec.reason}")

    print("-" * 72)
    print(f"SUMMARY: {passed}/{len(all_cases)} passed ({passed / len(all_cases) * 100:.1f}%)")
    result_marker = "P4_DOMAIN_CLASSIFIER_OK" if ok else "P4_DOMAIN_CLASSIFIER_FAIL"
    print(f"RESULT: {result_marker}")
    return ok


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phase 4 dynamic domain router"
    )
    parser.add_argument("--query", help="user query to classify")
    parser.add_argument(
        "--self-test", action="store_true", help="run built-in classification suite"
    )
    parser.add_argument(
        "--build-anchors", action="store_true", help="precompute domain anchors to npz"
    )
    parser.add_argument(
        "--mode", default="hybrid", choices=["hybrid", "semantic", "keyword"],
        help="classification mode (default: hybrid)"
    )
    args = parser.parse_args()

    clf = DomainClassifier(mode=args.mode)
    if args.build_anchors:
        ok = clf.build_anchors()
        if ok:
            print("RESULT: P4_BUILD_ANCHORS_OK")
        return
    if args.self_test:
        ok = _self_test()
        return
    if args.query:
        dec = clf.classify(args.query)
        print(json.dumps(dec.to_dict(), indent=2))
        print("RESULT: P4_DOMAIN_CLASSIFIER_OK")
        return
    parser.print_help()


if __name__ == "__main__":
    main()