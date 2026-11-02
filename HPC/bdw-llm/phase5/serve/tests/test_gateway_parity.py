"""P5.1 ask() parity - replay the pre-refactor golden fixture.

The fixture was produced by capture_gateway_golden.py against the original
Gateway.ask before the P5.1 refactor that extracted _prep/_meta and added
ask_stream(). Any behavioral drift in routing, prompt assembly, LoRA
resolution, citation verification, meta shaping or rate limiting fails here.
"""
from __future__ import annotations

import json
import os

import pytest

from phase5.serve.tests.gateway_stubs import build_stub_gateway

GOLDEN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "golden", "gateway_ask_golden.json")


def _load_fixture():
    if not os.path.isfile(GOLDEN_PATH):
        pytest.fail("golden fixture missing; run "
                    "phase5/serve/tests/capture_gateway_golden.py first")
    with open(GOLDEN_PATH, encoding="utf-8") as fh:
        return json.load(fh)


_FIXTURE = _load_fixture()
CASES = _FIXTURE["cases"]


@pytest.mark.parametrize("case", CASES,
                         ids=[c["name"] for c in CASES])
def test_ask_matches_golden(case):
    _, gate = build_stub_gateway()
    for _ in range(case.get("rate_hits_before", 0)):
        gate.lim.hit(case["inputs"]["user_id"])
    actual = json.loads(json.dumps(gate.ask(**case["inputs"])))
    assert actual == case["result"]
    if case["llm_call"] is None:
        assert gate.llm.calls == []
    else:
        assert gate.llm.calls == [case["llm_call"]]


def test_fixture_covers_the_contract_matrix():
    """Guard: the fixture must keep exercising the interesting branches."""
    names = {c["name"] for c in CASES}
    assert names >= {
        "grounded_stale_cites",
        "history_system_prompt_forced_domain_controls",
        "rate_limited_on_fourth_hit",
        "weak_local_general_question",
    }
    grounded = next(c for c in CASES
                    if c["name"] == "grounded_stale_cites")
    assert grounded["result"][0]["meta"]["citations_dropped"] == ["5", "abc"]
    assert grounded["result"][0]["meta"]["citations_kept"] == ["0"]
