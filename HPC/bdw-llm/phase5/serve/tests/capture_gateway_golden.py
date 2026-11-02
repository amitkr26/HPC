"""Capture the golden Gateway.ask() output BEFORE the P5.1 refactor.

Run from the bdw-llm repo root (needs only the light test deps):

    python phase5/serve/tests/capture_gateway_golden.py

Writes golden/gateway_ask_golden.json next to this script. The parity test
(test_gateway_parity.py) replays the recorded inputs against the refactored
gateway and asserts byte-identical results, so ask() behavior cannot drift
while ask_stream()/ _prep are introduced. Re-running this script after a
deliberate ask() change refreshes the fixture (review the diff!).
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# make `python phase5/serve/tests/capture_gateway_golden.py` from the repo
# root import both the sibling stubs and the phase5 package
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(HERE))))

from gateway_stubs import GOLDEN_CASES, build_stub_gateway  # noqa: E402

OUT_PATH = os.path.join(HERE, "golden", "gateway_ask_golden.json")


def main():
    _, gate = build_stub_gateway()
    cases = []
    for case in GOLDEN_CASES:
        for _ in range(case.get("rate_hits_before", 0)):
            gate.lim.hit(case["inputs"]["user_id"])
        calls_before = len(gate.llm.calls)
        raw = gate.ask(**case["inputs"])
        llm_call = (gate.llm.calls[-1]
                    if len(gate.llm.calls) > calls_before else None)
        cases.append({
            "name": case["name"],
            "rate_hits_before": case.get("rate_hits_before", 0),
            "inputs": case["inputs"],
            "llm_call": llm_call,
            "result": json.loads(json.dumps(raw)),
        })
    fixture = {
        "captured_from": "phase3/gateway/app.py:Gateway.ask",
        "note": ("Golden output captured before the P5.1 ask_stream/_prep "
                 "refactor; regenerate only for a deliberate ask() change."),
        "cases": cases,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(fixture, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    print("wrote %s (%d cases)" % (OUT_PATH, len(cases)))
    for c in cases:
        status = c["result"][1]
        answer = (c["result"][0] or {}).get("answer")
        print("  %-45s status=%s answer=%s" % (
            c["name"], status,
            ("<none>" if answer is None
             else "%d chars" % len(answer))))


if __name__ == "__main__":
    main()
