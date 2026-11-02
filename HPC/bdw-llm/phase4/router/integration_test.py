"""Phase 4 router integration test - complex / cross-domain query battery.

Exercises the model-backed dual-engine router the way the Zone 2 gateway
does: one DomainClassifier instance, many production-style questions,
including paraphrases, mixed-domain wording, and off-domain prose.

Run on a host that has the local BGE model (PARAM Rudra login node):
    venv/bin/python phase4/router/integration_test.py
If sentence-transformers/BGE is unavailable the router degrades to the
lexical engine, and the semantic-only cases are expected to miss.

Exit marker:
    RESULT: P4_ROUTER_INTEGRATION_OK pass=N/M
    RESULT: P4_ROUTER_INTEGRATION_FAIL pass=N/M
"""
from __future__ import annotations

import argparse
import sys
import time

from domain_classifier import Domain, DomainClassifier

# (suite, query, accepted domains)
CASES = [
    # -- canonical contract (single-domain, unambiguous) -------------------
    ("CANONICAL", "explain setup and hold time in cmos", {Domain.VLSI}),
    ("CANONICAL", "stm32 gpio interrupt handler in bare metal c", {Domain.EMBEDDED}),
    ("CANONICAL", "derive the gradient of a convex loss function", {Domain.MATH}),
    ("CANONICAL", "big-o complexity of graph traversal", {Domain.CS}),
    ("CANONICAL", "fine-tune a transformer with lora on a single gpu", {Domain.AIML}),
    ("CANONICAL", "hello how are you", {Domain.GENERAL}),
    # -- paraphrase (no canonical keywords, semantic engine required) ------
    ("PARAPHRASE", "how do you calculate the area enclosed between two intersecting curves on a plane", {Domain.MATH}),
    ("PARAPHRASE", "what is the geometric interpretation of the determinant of a transformation matrix", {Domain.MATH}),
    ("PARAPHRASE", "explain the fourier transform of a gaussian function", {Domain.MATH}),
    ("PARAPHRASE", "why do signals entering different clock domains cause unpredictable output states", {Domain.VLSI}),
    ("PARAPHRASE", "what causes capacitive crosstalk between adjacent parallel metal layers in a nanoscale chip", {Domain.VLSI}),
    ("PARAPHRASE", "how to configure an on-chip peripheral to transfer incoming samples to memory without cpu", {Domain.EMBEDDED}),
    ("PARAPHRASE", "how to handle an unhandled exception in an interrupt handler on a cortex-m4", {Domain.EMBEDDED}),
    ("PARAPHRASE", "explain how the operating system handles a page fault when referencing swapped pages", {Domain.CS}),
    ("PARAPHRASE", "how does the two-phase commit protocol achieve atomicity in distributed databases", {Domain.CS}),
    ("PARAPHRASE", "why do deep networks suffer from vanishing activations during reverse mode differentiation", {Domain.AIML}),
    ("PARAPHRASE", "how does quantized k-quants in gguf reduce memory footprint during inference", {Domain.AIML}),
    # -- cross-domain (secondary vocabulary must not hijack the winner) ----
    ("CROSS", "write a verilog testbench to verify a uart transmitter", {Domain.VLSI, Domain.EMBEDDED}),
    ("CROSS", "implement a pid controller on an stm32 using fixed point arithmetic", {Domain.EMBEDDED}),
    ("CROSS", "use dynamic programming to optimize matrix chain multiplication", {Domain.CS, Domain.MATH}),
    ("CROSS", "what is the difference between a mutex and a semaphore in freertos", {Domain.EMBEDDED}),
    ("CROSS", "why does my rtos task starve under priority inversion", {Domain.EMBEDDED}),
    ("CROSS", "how does clock gating reduce dynamic power in cmos", {Domain.VLSI}),
    ("CROSS", "how do you fix setup violations using useful skew", {Domain.VLSI}),
    ("CROSS", "what is the significance of the eye diagram in high speed serdes links", {Domain.VLSI}),
    ("CROSS", "how to debug a hard fault on cortex-m using fault registers", {Domain.EMBEDDED}),
    ("CROSS", "how do i configure dma to sample an adc at a fixed rate", {Domain.EMBEDDED}),
    ("CROSS", "explain the bias variance tradeoff in model selection", {Domain.AIML}),
    ("CROSS", "what is the role of the kv cache during autoregressive decoding", {Domain.AIML}),
    ("CROSS", "how does lora reduce trainable parameters during fine tuning", {Domain.AIML}),
    ("CROSS", "what is the role of attention in transformer models", {Domain.AIML}),
    ("CROSS", "solve the recurrence relation t(n) = 2t(n/2) + n", {Domain.CS, Domain.MATH}),
    ("CROSS", "what is the time complexity of the simplex algorithm", {Domain.CS, Domain.MATH}),
    ("CROSS", "how does the compiler vectorize a matrix multiply loop for avx-512", {Domain.CS, Domain.MATH}),
    ("CROSS", "write a python script to simulate a verilog counter", {Domain.CS, Domain.VLSI}),
    ("CROSS", "implement a low pass filter in matlab for an ecg signal", {Domain.EMBEDDED, Domain.MATH}),
    ("CROSS", "why does my fpga design fail timing closure after place and route", {Domain.VLSI}),
    # -- core CS / AIML / math coverage ------------------------------------
    ("CORE", "how does tcp congestion control avoid network collapse", {Domain.CS}),
    ("CORE", "why is quicksort o(n log n) on average but o(n^2) worst case", {Domain.CS}),
    ("CORE", "how does b+ tree indexing improve database query performance", {Domain.CS}),
    ("CORE", "how do i optimize a sql query with multiple joins", {Domain.CS}),
    ("CORE", "what is the difference between a process and a thread", {Domain.CS}),
    ("CORE", "my program segfaults when allocating memory in a loop", {Domain.CS}),
    ("CORE", "how does the linux kernel schedule processes", {Domain.CS}),
    ("CORE", "explain the difference between a compiler and an interpreter", {Domain.CS}),
    ("CORE", "what is the difference between supervised and unsupervised learning", {Domain.AIML}),
    ("CORE", "how does a convolutional layer extract features from an image", {Domain.AIML}),
    ("CORE", "how does quantization reduce inference memory footprint", {Domain.AIML}),
    ("CORE", "how do i train a model with pytorch on multiple gpus", {Domain.AIML}),
    ("CORE", "how do i compute the determinant of a 3x3 matrix", {Domain.MATH}),
    # -- negative / off-domain (must route to general) ---------------------
    ("NEGATIVE", "what is the capital of france", {Domain.GENERAL}),
    ("NEGATIVE", "summarize the plot of hamlet", {Domain.GENERAL}),
    ("NEGATIVE", "explain quantum entanglement and its applications", {Domain.GENERAL}),
    ("NEGATIVE", "who won the 2024 cricket world cup", {Domain.GENERAL}),
    ("NEGATIVE", "how do i write a cover letter for a job application", {Domain.GENERAL}),
    ("NEGATIVE", "how do i bake a chocolate cake at home", {Domain.GENERAL}),
    ("NEGATIVE", "what is the weather in delhi today", {Domain.GENERAL}),
    ("NEGATIVE", "", {Domain.GENERAL}),
]


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 4 router integration test")
    ap.add_argument("--mode", default="hybrid",
                    choices=["hybrid", "semantic", "keyword"])
    ap.add_argument("--fail-fast", action="store_true")
    args = ap.parse_args()

    clf = DomainClassifier(mode=args.mode)
    passed = 0
    failures = []
    by_suite = {}
    t0 = time.time()

    print("=" * 96)
    print("PHASE 4 ROUTER INTEGRATION TEST  mode=%s  cases=%d" % (args.mode, len(CASES)))
    print("=" * 96)
    for suite, query, accepted in CASES:
        dec = clf.classify(query)
        match = dec.domain in accepted
        by_suite.setdefault(suite, [0, 0])
        by_suite[suite][1] += 1
        if match:
            passed += 1
            by_suite[suite][0] += 1
        else:
            failures.append((suite, query, accepted, dec))
        print("[%s] %-10s %-8s c=%.2f | %-62s | %s"
              % ("PASS" if match else "FAIL", suite, dec.domain.value,
                 dec.confidence, query[:62] or "<empty>", dec.reason[:60]))
        if args.fail_fast and not match:
            break

    elapsed = time.time() - t0
    print("-" * 96)
    for suite in ("CANONICAL", "PARAPHRASE", "CROSS", "CORE", "NEGATIVE"):
        if suite in by_suite:
            ok, total = by_suite[suite]
            print("  %-10s %2d/%2d" % (suite, ok, total))
    print("  elapsed     %.2fs (%.1f ms/query)"
          % (elapsed, 1000.0 * elapsed / max(len(CASES), 1)))
    for suite, query, accepted, dec in failures:
        print("  MISS [%s] '%s' expected=%s got=%s (%s)"
              % (suite, query[:60],
                 "/".join(sorted(d.value for d in accepted)),
                 dec.domain.value, dec.reason))
    ok = passed == len(CASES)
    print("SUMMARY: %d/%d passed (%.1f%%)"
          % (passed, len(CASES), 100.0 * passed / len(CASES)))
    print("RESULT: %s pass=%d/%d"
          % ("P4_ROUTER_INTEGRATION_OK" if ok else "P4_ROUTER_INTEGRATION_FAIL",
             passed, len(CASES)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
