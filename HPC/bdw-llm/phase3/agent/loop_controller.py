"""Zone 2.5 - Agentic Loop (ReAct scaffold) for the BDW 7B model.

Gives the Zone 3 model a bounded autonomous software-engineering loop:
strict-JSON Thought/Action/Action_Input protocol, a sandboxed tool
executor (terminal + file I/O confined to phase3/agent/sandbox/), and a
while-loop capped at 10 iterations that feeds each tool result back as an
OBSERVATION until the model emits task_complete.

Zone 3 connection is the existing offline llama.cpp server (POST
/completion, non-streaming) - base URL/timeouts from phase3/.env
(ZONE3_BASE_URL, ZONE3_TIMEOUT_S), overridable by CLI.

Usage:
  python loop_controller.py --task "write hello.py that prints OK, run it"
  python loop_controller.py --self-test          (offline, stub server)

Exit markers: RESULT: P3_AGENT_DONE | P3_AGENT_MAXITERS | P3_AGENT_ERROR
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time

import requests

MAX_ITERS_DEFAULT = 10
CMD_TIMEOUT_DEFAULT = 30
READ_CAP = 4000
OUTPUT_CAP = 2000
LIST_CAP = 100
PH3 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SANDBOX_DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "sandbox")
SYSTEM_PROMPT = """\
You are BDW-Agent, an autonomous software engineer working inside a
sandboxed project folder. Reply with EXACTLY ONE JSON object per turn and
nothing else, in this schema:

{"thought": "<brief reasoning about what to do next>",
 "action": "<one of: terminal | read_file | write_file | list_files | task_complete>",
 "action_input": {<arguments for the action>}}

Actions and their action_input:
  terminal     {"cmd": "<shell command to run inside the sandbox>"}
  read_file    {"path": "<sandbox-relative path>"}
  write_file   {"path": "<sandbox-relative path>", "content": "<full file text>"}
  list_files   {}
  task_complete {"summary": "<one-paragraph report of what was accomplished>"}

Hard rules:
- Paths are sandbox-relative. Never absolute, never '..', never ~.
- After every action you receive exactly one OBSERVATION with the tool
  result. Use it before acting again. One action per turn.
- Work iteratively: check state, make small changes, verify by running.
- When the goal is met (and only then), emit task_complete with a summary.
- Output raw JSON only. No markdown fences, no extra keys, no prose."""

DENYLIST = (re.compile(r"\brm\s+(-[a-z]*r[a-z]*f|-[a-z]*f[a-z]*r)\b"),
            re.compile(r"\bmkfs\b"), re.compile(r":\(\)\s*\{.*\}\s*;"),
            re.compile(r"\bdel\s+/[sq]", re.I), re.compile(r"\bformat\s+[a-z]:", re.I),
            re.compile(r"\b(shutdown|rdisk|reg\s+delete)\b", re.I))


class SandboxViolation(Exception):
    pass


class Sandbox:
    """Filesystem + process jail rooted at `root`. Every path argument is
    resolved and must stay inside; commands run with cwd=root."""

    def __init__(self, root, cmd_timeout):
        self.root = os.path.realpath(root)
        os.makedirs(self.root, exist_ok=True)
        self.cmd_timeout = cmd_timeout

    def resolve(self, rel):
        if not rel or not isinstance(rel, str):
            raise SandboxViolation("path required")
        rel = rel.strip().replace("\\", "/").lstrip("/")
        if rel.startswith("~") or ":" in rel:
            raise SandboxViolation("absolute paths not allowed: %r" % rel)
        parts = [p for p in rel.split("/") if p not in ("", ".")]
        if any(p == ".." for p in parts):
            raise SandboxViolation("'..' not allowed: %r" % rel)
        cand = os.path.realpath(os.path.join(self.root, *parts))
        if cand != self.root and not cand.startswith(self.root + os.sep):
            raise SandboxViolation("escapes sandbox: %r" % rel)
        return cand

    def read_file(self, rel):
        p = self.resolve(rel)
        if not os.path.isfile(p):
            return "ERROR: no such file: %s" % rel
        with open(p, "r", encoding="utf-8", errors="replace") as fh:
            data = fh.read()
        if len(data) > READ_CAP:
            return data[:READ_CAP] + "\n...[truncated at %d chars]" % READ_CAP
        return data or "[empty file]"

    def write_file(self, rel, content):
        p = self.resolve(rel)
        os.makedirs(os.path.dirname(p) or self.root, exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(str(content if content is not None else ""))
        return "OK: wrote %s (%d bytes)" % (rel, os.path.getsize(p))

    def list_files(self):
        out = []
        for base, dirs, files in os.walk(self.root):
            rel = os.path.relpath(base, self.root)
            for f in files:
                out.append(f if rel == "." else rel.replace(os.sep, "/")
                           + "/" + f)
            if len(out) > LIST_CAP:
                break
        out.sort()
        if not out:
            return "[sandbox empty]"
        shown = out[:LIST_CAP]
        tail = ("\n...[%d more]" % (len(out) - LIST_CAP)
                if len(out) > LIST_CAP else "")
        return "\n".join(shown) + tail

    def terminal(self, cmd):
        if not isinstance(cmd, str) or not cmd.strip():
            return "ERROR: cmd required"
        for pat in DENYLIST:
            if pat.search(cmd):
                return "ERROR: command blocked by sandbox policy"
        try:
            r = subprocess.run(cmd, shell=True, cwd=self.root,
                               capture_output=True, text=True,
                               timeout=self.cmd_timeout)
        except subprocess.TimeoutExpired:
            return "ERROR: command exceeded %ds timeout" % self.cmd_timeout
        out = ((r.stdout or "") + (("\n[stderr] " + r.stderr) if r.stderr
                                   else "")).strip()
        if len(out) > OUTPUT_CAP:
            out = out[:OUTPUT_CAP] + "\n...[output truncated]"
        return "exit=%d\n%s" % (r.returncode, out or "[no output]")

    def execute(self, action, arg):
        if action == "terminal":
            return self.terminal(arg.get("cmd", ""))
        if action == "read_file":
            return self.read_file(arg.get("path", ""))
        if action == "write_file":
            return self.write_file(arg.get("path", ""),
                                   arg.get("content", ""))
        if action == "list_files":
            return self.list_files()
        return "ERROR: unknown action: %r" % action


def parse_action(text):
    """Extract the first valid JSON object with the required keys."""
    dec = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            obj, _ = dec.raw_decode(text[i:])
        except ValueError:
            continue
        if isinstance(obj, dict) and "action" in obj and "thought" in obj:
            arg = obj.get("action_input")
            return obj["thought"], obj["action"], (arg if isinstance(arg, dict) else {})
    return None


class Zone3:
    def __init__(self, base, timeout):
        self.base = base.rstrip("/")
        self.timeout = timeout

    def complete(self, prompt, max_tokens=512):
        r = requests.post(self.base + "/completion", timeout=self.timeout,
                          json={"prompt": prompt, "n_predict": max_tokens,
                                "stream": False, "temperature": 0.0})
        r.raise_for_status()
        return r.json().get("content", "")


class AgentLoop:
    def __init__(self, llm, sandbox, max_iters, log=print):
        self.llm = llm
        self.box = sandbox
        self.max_iters = max_iters
        self.log = log

    def run(self, task):
        transcript = []
        for i in range(1, self.max_iters + 1):
            prompt = (SYSTEM_PROMPT + "\n\nTASK: " + task
                      + "\n\nTRANSCRIPT:\n" + "\n".join(transcript)
                      + "\n\nYour move (one JSON object):")
            raw = self.llm.complete(prompt)
            parsed = parse_action(raw)
            if parsed is None:
                obs = ("ERROR: reply was not a valid JSON action object. "
                       "Re-emit exactly one JSON object with thought, "
                       "action, action_input.")
                self.log("[iter %d] PARSE-FAIL: %r" % (i, raw[:160]))
                transcript.append("MODEL: %s" % raw.strip()[:400])
                transcript.append("OBSERVATION: %s" % obs)
                continue
            thought, action, arg = parsed
            self.log("[iter %d] [THOUGHT] %s" % (i, thought))
            if action == "task_complete" or "TASK_COMPLETE" in raw:
                summary = str(arg.get("summary", "")) or raw.strip()[:400]
                self.log("[iter %d] [TASK_COMPLETE] %s" % (i, summary))
                return summary
            self.log("[iter %d] [ACTION] %s %s" % (i, action, json.dumps(arg)[:200]))
            t0 = time.time()
            try:
                obs = self.box.execute(action, arg)
            except SandboxViolation as exc:
                obs = "ERROR: sandbox violation: %s" % exc
            except Exception as exc:  # noqa: BLE001
                obs = "ERROR: tool failure: %s" % str(exc)[:200]
            self.log("[iter %d] [OBSERVATION] (%.1fs) %s"
                     % (i, time.time() - t0, obs.replace("\n", " | ")[:300]))
            transcript.append("MODEL: {\"thought\": %s, \"action\": %s, "
                              "\"action_input\": %s}"
                              % (json.dumps(thought), json.dumps(action),
                                 json.dumps(arg)))
            transcript.append("OBSERVATION: %s" % obs)
        self.log("[loop] iteration cap (%d) reached without task_complete"
                 % self.max_iters)
        return None


def load_env():
    env = {}
    p = os.path.join(PH3, ".env")
    if os.path.isfile(p):
        with open(p, encoding="utf-8-sig") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    k, _, v = line.partition("=")
                    env[k.strip()] = v.strip()
    return env


def main():
    ap = argparse.ArgumentParser(description="BDW ReAct agent loop")
    ap.add_argument("--task", help="goal for the agent")
    ap.add_argument("--max-iters", type=int, default=MAX_ITERS_DEFAULT)
    ap.add_argument("--cmd-timeout", type=int, default=CMD_TIMEOUT_DEFAULT)
    ap.add_argument("--zone3-url", default=None)
    ap.add_argument("--sandbox", default=SANDBOX_DEFAULT)
    ap.add_argument("--self-test", action="store_true",
                    help="run offline against a scripted stub server")
    args = ap.parse_args()
    env = load_env()
    base = args.zone3_url or env.get("ZONE3_BASE_URL", "http://127.0.0.1:8080")
    llm = Zone3(base, int(env.get("ZONE3_TIMEOUT_S", "120")))
    box = Sandbox(args.sandbox, args.cmd_timeout)

    if args.self_test:
        sys.exit(self_test(box))

    if not args.task:
        ap.error("--task is required (or use --self-test)")
    print("BDW-Agent sandbox=%s zone3=%s max_iters=%d"
          % (box.root, base, args.max_iters), flush=True)
    agent = AgentLoop(llm, box, args.max_iters)
    summary = agent.run(args.task)
    if summary is not None:
        print("RESULT: P3_AGENT_DONE %s" % summary[:200], flush=True)
    else:
        print("RESULT: P3_AGENT_MAXITERS", flush=True)


def self_test(box):
    """Offline stub: scripted llama server drives write->run->complete."""
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    import threading

    run_script = {"steps": [
        {"thought": "create file", "action": "write_file",
         "action_input": {"path": "hello.py", "content": "print('OK-123')"}},
        {"thought": "run it", "action": "terminal",
         "action_input": {"cmd": "python hello.py"}},
        {"thought": "done", "action": "task_complete",
         "action_input": {"summary": "wrote and ran hello.py"}},
    ], "n": 0}

    class Stub(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            self.rfile.read(n)
            steps = run_script["steps"]
            i = run_script["n"]
            step = steps[min(i, len(steps) - 1)]
            if i < len(steps):
                run_script["n"] = i + 1
            raw = json.dumps({"content": json.dumps(step)}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

    srv = ThreadingHTTPServer(("127.0.0.1", 0), Stub)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    stub_url = "http://127.0.0.1:%d" % srv.server_address[1]

    agent = AgentLoop(Zone3(stub_url, 10), box, 10)
    summary = agent.run("self-test: create and run hello.py")
    hello = os.path.join(box.root, "hello.py")
    assert summary is not None and "hello.py" in summary, summary
    assert os.path.isfile(hello), "stub write_file never landed"
    with open(hello, encoding="utf-8") as fh:
        assert "OK-123" in fh.read()
    run_script["steps"] = [
        {"thought": "try to escape the sandbox", "action": "write_file",
         "action_input": {"path": "../../evil.txt", "content": "x"}},
        {"thought": "done", "action": "task_complete",
         "action_input": {"summary": "escape blocked, gave up"}},
    ]
    run_script["n"] = 0
    summary2 = agent.run("escape test: write ../../evil.txt")
    assert summary2 is not None, summary2
    assert not os.path.isfile(os.path.join(os.path.dirname(box.root),
                                           "evil.txt")), "sandbox escaped!"
    srv.shutdown()
    print("RESULT: P3_AGENT_SELFTEST_OK", flush=True)
    return 0


if __name__ == "__main__":
    main()
