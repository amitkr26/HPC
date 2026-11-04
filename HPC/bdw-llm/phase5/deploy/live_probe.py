#!/usr/bin/env python3
"""P5_LIVE_OK probe - live certification of the deployed BDW shim.

The exit criterion for P5.1 (blueprint sec 16.3): the REAL stack (shim ->
vLLM -> tunnel/edge) must answer, stream, report upstream usage, expose
metrics, and pass the real bdw.ts provider path. Produces exactly one
marker on stdout:

    P5_LIVE_OK
    P5_LIVE_FAIL <step>: <reason>

Runs anywhere (Param Rudra compute node, workstation against localhost,
or the public edge): stdlib only. Reads P5_API_KEY / P5_METRICS_TOKEN
from phase5/deploy/.env or the environment; secrets are never printed.

usage:
  live_probe.py [--url URL] [--provider auto|on|off] [--json OUT.json]
                [--ready-timeout 120] [--gen-timeout 180]

  --url   default http://127.0.0.1:8090 (on the compute node); edge:
          https://ai.berojgardegreewala.com
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent            # .../phase5/deploy
DEPLOY = HERE                                     # .../phase5/deploy
BDW_ROOT = DEPLOY.parent.parent                   # .../bdw-llm
HARNESS = BDW_ROOT / "phase5" / "serve" / "tests" / "contracts" / \
    "bdw_provider_contract.mjs"
SLO_FILE = DEPLOY / "slo.json"


# ------------------------------------------------------------------ util ---

def load_env(path: Path) -> dict:
    env = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            env[k] = v
    env.update(os.environ)
    return env


ENV = load_env(DEPLOY / ".env")


def say(msg: str) -> None:
    print(f"[live] {msg}", flush=True)


def fail(step: str, detail: str) -> None:
    print(f"P5_LIVE_FAIL {step}: {detail}", flush=True)
    sys.exit(1)


def squash(text: str) -> str:
    return " ".join((text or "").split())


def _lower(headers) -> dict:
    """Header dict with lowercase keys (h11 stores them lowercase, so a
    plain-dict lookup must match that or Content-Type checks miss)."""
    return {k.lower(): v for k, v in headers.items()}


def http(url: str, *, key: str | None = None, body: dict | None = None,
         timeout: float = 60, stream: bool = False):
    """GET/POST helper. Returns (status, headers, payload).

    For stream=True payload is the live response object (caller reads and
    closes it); otherwise payload is the body bytes. Connection failures
    come back as status -1 with the reason as payload, so every step fails
    via the P5_LIVE_FAIL marker instead of a traceback."""
    data = json.dumps(body).encode() if body is not None else None
    headers = {"accept": "*/*"}
    if body is not None:
        headers["content-type"] = "application/json"
    if key:
        headers["authorization"] = f"Bearer {key}"
    req = urllib.request.Request(url, data=data, headers=headers,
                                 method="POST" if data else "GET")
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as exc:
        return exc.code, _lower(exc.headers), exc.read()
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        reason = getattr(exc, "reason", exc)
        return -1, {}, str(reason).encode()
    if stream:
        return resp.status, _lower(resp.headers), resp
    with resp:
        return resp.status, _lower(resp.headers), resp.read()


# ----------------------------------------------------------------- steps ---

def step_health(base: str, ready_timeout: float) -> None:
    say("GET /healthz")
    st, _, raw = http(f"{base}/healthz", timeout=10)
    if st != 200 or b'"status":"ok"' not in raw:
        fail("healthz", f"status={st} body={raw[:200]!r}")
    say("GET /readyz (waiting for upstream readiness)")
    deadline = time.time() + ready_timeout
    while True:
        st, _, raw = http(f"{base}/readyz", timeout=10)
        if st == 200 and b'"status":"ready"' in raw:
            return
        if time.time() >= deadline:
            fail("readyz", f"not ready after {ready_timeout:.0f}s "
                           f"(status={st} body={raw[:200]!r})")
        time.sleep(3)


def step_models(base: str, key: str) -> None:
    say("GET /v1/models")
    st, _, raw = http(f"{base}/v1/models", key=key, timeout=15)
    if st != 200 or b"bdw-career-ai" not in raw:
        fail("models", f"status={st} body={raw[:200]!r}")


def step_auth_enforced(base: str, key: str) -> str:
    say("auth: request without bearer must be rejected")
    st, _, _ = http(f"{base}/v1/chat/completions", body={
        "model": "bdw-career-ai",
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 1,
    }, timeout=30)
    if st == 401:
        return "enforced"
    if st == 200:
        say("warning: auth not enforced (P5_AUTH_MODE!=required)")
        return "disabled"
    fail("auth", f"expected 401 (or 200 when auth disabled), got {st}")


def step_completion(base: str, key: str, gen_timeout: float) -> dict:
    say("POST /v1/chat/completions (non-stream)")
    t0 = time.time()
    st, _, raw = http(
        f"{base}/v1/chat/completions", key=key, timeout=gen_timeout,
        body={"model": "bdw-career-ai", "max_tokens": 32, "stream": False,
              "messages": [{"role": "user",
                            "content": "Reply with the single word: pong"}]})
    latency = time.time() - t0
    if st != 200:
        fail("completion", f"status={st} body={raw[:300]!r}")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        fail("completion", f"non-JSON body {raw[:200]!r}")
    choices = data.get("choices") or []
    if not choices or not (choices[0].get("message", {}).get("content") or "").strip():
        fail("completion", f"empty choices: {raw[:300]!r}")
    usage = data.get("usage")
    say(f"latency {latency:.2f}s · usage={usage} "
        f"· answer={choices[0]['message']['content'].strip()[:40]!r}")
    return {"latency_s": round(latency, 3), "usage": usage}


def step_stream(base: str, key: str, gen_timeout: float) -> dict:
    """Certify the shim's SSE surface: OpenAI chat.completion.chunk events
    (the gateway-internal delta/final protocol is translated to this at
    main.py stream_chat_events): lazy role chunk -> content chunks ->
    finish chunk carrying usage + bdw meta -> [DONE], heartbeats as
    ': ping' comments, failures as an in-band {\"error\": ...} chunk."""
    say("POST /v1/chat/completions (stream=true)")
    t0 = time.time()
    st, headers, resp = http(
        f"{base}/v1/chat/completions", key=key, timeout=gen_timeout,
        stream=True,
        body={"model": "bdw-career-ai", "max_tokens": 64, "stream": True,
              "stream_options": {"include_usage": True},
              "messages": [{"role": "user",
                            "content": "Count from 1 to 8, comma separated."}]})
    if st != 200:
        body = resp if isinstance(resp, bytes) else (
            resp.read() if hasattr(resp, "read") else b"")
        fail("stream", f"status={st} body={body[:300]!r}")
    ctype = headers.get("content-type", "")
    if "text/event-stream" not in ctype:
        say(f"warning: content-type={ctype!r} (expected text/event-stream)")

    ttft = None
    parts: list[str] = []
    usage = None
    finish = None
    bdw = None
    got_done = False
    try:
        while True:
            try:
                line = resp.readline()
            except (OSError, TimeoutError) as exc:
                fail("stream", f"read error: {exc}")
            if not line:
                break
            line = line.decode(errors="replace").strip()
            if not line or line.startswith(":"):
                continue                      # heartbeat comment
            if not line.startswith("data:"):
                continue
            payload = line[len("data:"):].strip()
            if payload == "[DONE]":
                got_done = True
                break
            try:
                event = json.loads(payload)
            except json.JSONDecodeError:
                fail("stream", f"bad SSE JSON {payload[:160]!r}")
            if event.get("error") is not None:
                err = event["error"]
                msg = (err.get("message") if isinstance(err, dict)
                       else str(err))
                fail("stream", f"in-band error: {msg}")
            choices = event.get("choices") or []
            if choices:
                choice = choices[0]
                text = (choice.get("delta") or {}).get("content") or ""
                if text:
                    if ttft is None:
                        ttft = time.time() - t0
                    parts.append(text)
                if choice.get("finish_reason"):
                    finish = choice["finish_reason"]
            if event.get("usage"):
                usage = event["usage"]
            if event.get("bdw"):
                bdw = event["bdw"]
    finally:
        resp.close()
    total = time.time() - t0

    if not got_done:
        fail("stream", "connection ended without [DONE]")
    if not parts:
        fail("stream", "no content deltas received")
    if finish != "stop":
        fail("stream", f"finish_reason={finish!r} (expected 'stop')")
    if not usage:
        # the shim always attaches usage on the finish chunk (upstream
        # vLLM numbers, or the char-estimate fallback) - absence is a
        # P5.1 contract break.
        fail("stream", "finish chunk carries no usage")

    answer = "".join(parts)
    completion_tokens = usage.get("completion_tokens") or 0
    tps = round(completion_tokens / total, 2) if completion_tokens else None
    say(f"ttft {ttft:.2f}s · total {total:.2f}s · "
        f"tokens {completion_tokens} · tps {tps} · finish=stop · usage ok")
    if bdw:
        say(f"bdw meta: domain={bdw.get('domain')} "
            f"adapter={bdw.get('adapter')}")
    return {"ttft_s": round(ttft, 3), "total_s": round(total, 3),
            "usage": usage, "tps": tps,
            "answer_preview": squash(answer)[:80]}


def step_metrics(base: str, token: str | None) -> str:
    say("GET /metrics")
    key = token or None
    st, _, raw = http(f"{base}/metrics", key=key, timeout=10)
    if st == 404:
        say("metrics 404 at this URL (expected behind the edge) - skipped")
        return "absent"
    if st == 401:
        fail("metrics", "401 - P5_METRICS_TOKEN mismatch (set the same "
                        "value in .env for probe and shim)")
    if st != 200 or b"bdw_shim_requests_total" not in raw:
        fail("metrics", f"status={st} instruments missing")
    if b"bdw_shim_ttft_seconds" not in raw:
        fail("metrics", "ttft histogram missing")
    return "ok"


def step_provider(base: str, key: str, mode: str) -> str:
    """Run the REAL bdw.ts through its node harness against this shim."""
    if mode == "off":
        return "skipped"
    node = shutil.which("node")
    ts = os.environ.get("BDW_PROVIDER_TS")
    candidates = [Path(ts)] if ts else []
    outer = BDW_ROOT.parent.parent.parent       # .../Tinkerscape
    candidates += [
        outer / "SiliconPath" / "backend" / "ai-gateway" / "src" /
        "providers" / "bdw.ts",
        outer / "BerojgarDegreeWala" / "backend" / "ai-gateway" / "src" /
        "providers" / "bdw.ts",
    ]
    ts_path = next((c for c in candidates if c.is_file()), None)
    problems = []
    if not node:
        problems.append("node not on PATH")
    if not HARNESS.is_file():
        problems.append(f"harness missing: {HARNESS}")
    if not ts_path:
        problems.append("bdw.ts not found (set BDW_PROVIDER_TS)")
    if problems:
        msg = "; ".join(problems)
        if mode == "on":
            fail("provider", msg)
        say(f"provider check skipped: {msg}")
        return "skipped"

    say(f"node harness vs real bdw.ts ({ts_path.name})")
    # bdw.ts appends /models and /chat/completions -> its base must carry /v1
    harness_base = base if base.endswith("/v1") else f"{base}/v1"
    env = dict(os.environ)
    env.setdefault("P5_CONTRACT_TIMEOUT_MS", "120000")  # 70B non-stream
    proc = subprocess.run(
        [node, str(HARNESS), str(ts_path), harness_base, key],
        capture_output=True, text=True, timeout=180, env=env, check=False)
    if proc.returncode != 0:
        fail("provider", f"node exit {proc.returncode}: "
                         f"{proc.stderr.strip()[:300]}")
    try:
        result = json.loads(proc.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        fail("provider", f"bad harness output: {proc.stdout[:300]!r}")
    if not result.get("valid"):
        fail("provider", "isBDWConfigValid=false")
    if not result.get("health"):
        fail("provider", "healthCheck=false")
    if result.get("error"):
        fail("provider", f"callBDWEndpoint error: {result['error']}")
    content = (result.get("content") or "").strip()
    if not content:
        fail("provider", "empty content from real provider path")
    say(f"provider content: {content[:70]!r}")
    return "ok"


def slo_report(stream_result: dict) -> dict:
    """Compare single-sample observations against slo.json draft targets.

    Single samples stand in for the p95 objectives only as a first
    sanity check; the targets stay draft until re-baselined from a real
    P5_LIVE_OK week (slo.json note)."""
    if not SLO_FILE.is_file():
        return {}
    slo = json.loads(SLO_FILE.read_text(encoding="utf-8"))
    observed: dict = {}
    ttft = stream_result.get("ttft_s")
    total = stream_result.get("total_s")
    if ttft is not None:
        observed["ttft_p95_seconds"] = ttft
    if total is not None:
        observed["stream_completion_p95_seconds"] = total
    verdicts = {}
    for obj in slo.get("objectives", []):
        name = obj.get("name")
        target = obj.get("target_seconds")
        if target is None or name not in observed:
            continue
        value = observed[name]
        over = value > target
        verdicts[name] = {
            "observed": value, "target": target,
            "draft": bool(obj.get("draft")),
            "status": "OVER-DRAFT-TARGET" if over else "within",
        }
        tag = "warning (draft)" if obj.get("draft") else "breach"
        if over:
            say(f"SLO {tag}: {name} {value:.2f}s > {target}s")
        else:
            say(f"SLO ok: {name} {value:.2f}s <= {target}s")
    return verdicts


# ------------------------------------------------------------------ main ---

def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="http://127.0.0.1:8090",
                    help="shim base URL (default: on-node localhost)")
    ap.add_argument("--provider", choices=("auto", "on", "off"),
                    default="auto",
                    help="run the real bdw.ts node harness (auto=skip if "
                         "node/bdw.ts unavailable)")
    ap.add_argument("--json", metavar="PATH", default=None,
                    help="write a machine-readable summary for SLO re-baseline")
    ap.add_argument("--ready-timeout", type=float, default=120)
    ap.add_argument("--gen-timeout", type=float, default=180)
    args = ap.parse_args()

    base = args.url.rstrip("/")
    if base.endswith("/v1"):          # accept .../v1 too; steps add it back
        base = base[:-3].rstrip("/")
    key = ENV.get("P5_API_KEY")
    if not key:
        fail("config", "P5_API_KEY missing from .env or environment")
    metrics_token = ENV.get("P5_METRICS_TOKEN") or None

    say(f"target {base}")
    summary: dict = {"url": base}

    step_health(base, args.ready_timeout)
    step_models(base, key)
    summary["auth"] = step_auth_enforced(base, key)
    summary["completion"] = step_completion(base, key, args.gen_timeout)
    summary["stream"] = step_stream(base, key, args.gen_timeout)
    summary["metrics"] = step_metrics(base, metrics_token)
    summary["provider"] = step_provider(base, key, args.provider)
    summary["slo"] = slo_report(summary["stream"])

    if args.json:
        Path(args.json).write_text(json.dumps(summary, indent=2),
                                   encoding="utf-8")
        say(f"summary -> {args.json}")

    print("P5_LIVE_OK", flush=True)


if __name__ == "__main__":
    main()
