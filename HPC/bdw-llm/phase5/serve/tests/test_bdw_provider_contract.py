"""P5.0 BDW provider contract test - runs the REAL providers/bdw.ts.

A uvicorn instance of the shim is started in-process with a deterministic
fake gateway; the actual TypeScript provider module from the BDW repository
is imported by Node (native type stripping) and exercised through its public
functions:

  loadBDWConfig()   -> configuration parsing
  isBDWConfigValid() -> enable flag
  healthCheck()     -> GET /v1/models
  callBDWEndpoint() -> POST /v1/chat/completions

Set BDW_PROVIDER_TS to override the provider path; otherwise the sibling
SiliconPath checkout is used. Node >= 22.6 is required (24.x recommended).
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import threading
import time
from pathlib import Path

import pytest
import uvicorn

from phase5.serve.main import Settings, create_app
from phase5.serve.tests.fake_gateway import ANSWER, FakeGateway

KEY = "p5-node-contract-key"
ROOT = Path(__file__).resolve().parents[3]
HARNESS = Path(__file__).resolve().parent / "contracts" / \
    "bdw_provider_contract.mjs"


def _provider_ts():
    candidates = []
    env_path = os.environ.get("BDW_PROVIDER_TS")
    if env_path:
        candidates.append(Path(env_path))
    base = ROOT.parent.parent.parent
    candidates.extend([
        base / "SiliconPath" / "backend" / "ai-gateway" / "src" /
        "providers" / "bdw.ts",
        base / "BerojgarDegreeWala" / "backend" / "ai-gateway" / "src" /
        "providers" / "bdw.ts",
    ])
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    pytest.skip("providers/bdw.ts not found; set BDW_PROVIDER_TS")
    return None


def _node_cmd(*args):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not installed")
    version = subprocess.run([node, "--version"], capture_output=True,
                             text=True, timeout=30).stdout.strip()
    try:
        major = int(version.lstrip("v").split(".")[0])
    except ValueError:
        pytest.skip("unrecognized Node version: %s" % version)
    cmd = [node]
    if major == 22:
        cmd.append("--experimental-strip-types")
    elif major < 22:
        pytest.skip("Node >= 22.6 is required for native TypeScript import")
    return cmd + list(args)


def _run_harness(ts_path, base_url, api_key):
    proc = subprocess.run(_node_cmd(str(HARNESS), ts_path, base_url, api_key),
                          capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        pytest.fail("node harness failed (exit %d)\nstdout:\n%s\nstderr:\n%s"
                    % (proc.returncode, proc.stdout, proc.stderr))
    lines = [line for line in proc.stdout.strip().splitlines() if line.strip()]
    if not lines:
        pytest.fail("node harness produced no output\n%s" % proc.stderr)
    return json.loads(lines[-1])


@pytest.fixture(scope="module")
def shim():
    gateway = FakeGateway()
    app = create_app(
        gateway=gateway,
        settings=Settings(auth_mode="required", api_key=KEY,
                          sse_heartbeat_s=2.0),
        readiness_probe=lambda: True,
    )
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port,
                                           log_level="error", lifespan="off"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.time() + 20
    while time.time() < deadline and not server.started:
        time.sleep(0.05)
    if not server.started:
        pytest.fail("uvicorn shim did not start")
    yield {"base": "http://127.0.0.1:%d/v1" % port, "gateway": gateway}
    server.should_exit = True
    thread.join(timeout=10)


def test_real_provider_healthcheck_and_chat(shim):
    ts_path = _provider_ts()
    out = _run_harness(ts_path, shim["base"], KEY)
    assert out["valid"] is True
    assert out["health"] is True, out
    assert out["error"] is None, out
    assert out["content"] == ANSWER
    call = shim["gateway"].calls[-1]
    assert call["system_prompt"] == ("You are BDW, a deep-tech career "
                                     "assistant.")
    assert call["max_tokens"] == 2048
    assert call["temperature"] == pytest.approx(0.3)


def test_real_provider_exposes_401_as_failure(shim):
    ts_path = _provider_ts()
    out = _run_harness(ts_path, shim["base"], "wrong-key")
    assert out["valid"] is True
    assert out["health"] is False
    assert out["content"] is None
    assert out["error"].startswith("BDW AI error 401")
