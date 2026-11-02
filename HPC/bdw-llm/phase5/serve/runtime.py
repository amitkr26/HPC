"""P5.0 runtime - build the Phase 3/4 Zone 2 gateway in-process.

The shim deliberately does not reimplement routing, domain RAG, LoRA
selection or citation verification: it imports phase3/gateway/app.py and
calls the shared build_gateway(env). The import is deferred so the
OpenAI contract tests can inject a deterministic fake gateway without
torch/sentence-transformers installed.
"""
from __future__ import annotations

import importlib.util
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
GATEWAY_PATH = os.path.join(REPO_ROOT, "phase3", "gateway", "app.py")
_MODULE_NAME = "bdw_zone2_gateway"


def load_gateway_module():
    """Import phase3/gateway/app.py once under a stable module name."""
    mod = sys.modules.get(_MODULE_NAME)
    if mod is not None:
        return mod
    if not os.path.isfile(GATEWAY_PATH):
        raise RuntimeError("Zone 2 gateway not found at %s" % GATEWAY_PATH)
    spec = importlib.util.spec_from_file_location(_MODULE_NAME, GATEWAY_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Zone 2 gateway from %s" % GATEWAY_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[_MODULE_NAME] = mod
    spec.loader.exec_module(mod)
    return mod


def build_gateway(env=None):
    """Return (gateway, info) exactly as the shim's create_app expects.

    phase3/gateway/app.py:build_gateway returns a dict carrying the gateway
    and the boot facts; the shim wants the (gateway, info) pair, so adapt in
    one place. Tuple returns are accepted for forward compatibility.
    """
    rt = load_gateway_module().build_gateway(env)
    if isinstance(rt, dict) and "gateway" in rt:
        return rt["gateway"], rt
    gateway, info = rt
    return gateway, info
