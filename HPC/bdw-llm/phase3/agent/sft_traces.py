"""Agent SFT pipeline - ReAct trace validator + ground-truth generator.

Produces JSONL instruction/completion pairs that EXACTLY match the
runtime prompt format of loop_controller.py (same SYSTEM_PROMPT, same
transcript layout) so the fine-tuned model is trained on the served
distribution. Ground truth comes from REALLY executing each action
through the same Sandbox jail the runtime uses - observations are never
invented.

Modes:
  --demo                       generate built-in demo traces (executed)
  --from-jsonl raw.jsonl       validate + re-execute external traces;
                               stored observations are replaced by real
                               sandbox results (or the violation text)
Output records:
  {"instruction": <build_prompt(task, transcript-so-far)>,
   "completion": <one JSON action object as text>,
   "meta": {"task": ..., "step": i, "action": ...}}
Final marker: RESULT: P3_AGENT_SFT_OK n=<records>
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from loop_controller import Sandbox, SandboxViolation, build_prompt  # noqa: E402

ACTIONS = {
    "terminal": {"required": ("cmd",), "optional": ()},
    "read_file": {"required": ("path",), "optional": ()},
    "write_file": {"required": ("path", "content"), "optional": ()},
    "list_files": {"required": (), "optional": ()},
    "task_complete": {"required": ("summary",), "optional": ()},
}


def validate_step(step, strict=True):
    """Return (thought, action, action_input) or raise ValueError."""
    if not isinstance(step, dict):
        raise ValueError("step is not an object")
    thought = step.get("thought")
    action = step.get("action")
    arg = step.get("action_input", {})
    if not isinstance(thought, str) or not thought.strip():
        raise ValueError("thought missing/empty")
    if action not in ACTIONS:
        raise ValueError("unknown action: %r" % action)
    if not isinstance(arg, dict):
        raise ValueError("action_input must be an object")
    spec = ACTIONS[action]
    missing = [k for k in spec["required"] if k not in arg]
    extra = [k for k in arg if k not in spec["required"] + spec["optional"]]
    if missing and strict:
        raise ValueError("%s missing keys %s" % (action, missing))
    if extra and strict:
        raise ValueError("%s extra keys %s" % (action, extra))
    if action == "terminal" and (not isinstance(arg.get("cmd"), str)
                                 or not arg.get("cmd", "").strip()):
        raise ValueError("terminal cmd must be a non-empty string")
    if action in ("read_file", "write_file") and not isinstance(
            arg.get("path"), str):
        raise ValueError("%s path must be a string" % action)
    if action == "write_file" and "content" not in arg:
        raise ValueError("write_file content missing")
    if action == "task_complete" and (not isinstance(arg.get("summary"), str)
                                      or not arg.get("summary", "").strip()):
        raise ValueError("task_complete summary must be a non-empty string")
    return thought, action, arg


def validate_trace(trace):
    """Full trace: {"task": str, "steps": [...], "summary": str}."""
    if not isinstance(trace, dict) or not isinstance(trace.get("task"), str):
        raise ValueError("trace needs a task string")
    steps = trace.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("trace needs a non-empty steps list")
    out = []
    for s in steps:
        out.append(validate_step(s))
    last = steps[-1]
    if last.get("action") != "task_complete":
        raise ValueError("last step must be task_complete")
    if not isinstance(trace.get("summary", last.get(
            "action_input", {}).get("summary", "")), str):
        raise ValueError("summary must be a string")
    return out


def execute_all(task, steps, box):
    """Run the trace through the sandbox, collecting REAL observations;
    returns (records, observations) where records are SFT pairs."""
    records, transcript, observations = [], [], []
    for i, (thought, action, arg) in enumerate(steps):
        prompt = build_prompt(task, transcript)
        completion = json.dumps({"thought": thought, "action": action,
                                 "action_input": arg})
        records.append({"instruction": prompt, "completion": completion,
                        "meta": {"task": task, "step": i,
                                 "action": action}})
        if action == "task_complete":
            transcript.append("MODEL: " + completion)
            break
        try:
            obs = box.execute(action, arg)
        except SandboxViolation as exc:
            obs = "ERROR: sandbox violation: %s" % exc
        except Exception as exc:  # noqa: BLE001
            obs = "ERROR: tool failure: %s" % str(exc)[:200]
        observations.append(obs)
        transcript.append("MODEL: " + completion)
        transcript.append("OBSERVATION: %s" % obs)
    return records, observations


DEMO_TRACES = [
    {"task": "Create hello.py that prints OK-DEMO, then run it.",
     "steps": [
         {"thought": "I need a file first; write hello.py with a print.",
          "action": "write_file",
          "action_input": {"path": "hello.py",
                           "content": "print('OK-DEMO')"}},
         {"thought": "File written; run it to verify the output.",
          "action": "terminal",
          "action_input": {"cmd": "python hello.py"}},
         {"thought": "Output shows OK-DEMO; the goal is met.",
          "action": "task_complete",
          "action_input": {"summary": "wrote hello.py and ran it; "
                                      "output OK-DEMO"}}],
     "summary": "wrote hello.py and ran it"},
    {"task": "Make notes.txt with two lines, then show it back.",
     "steps": [
         {"thought": "write the notes file",
          "action": "write_file",
          "action_input": {"path": "notes.txt",
                           "content": "line one\nline two"}},
         {"thought": "read it back to confirm the content",
          "action": "read_file",
          "action_input": {"path": "notes.txt"}},
         {"thought": "content confirmed; done",
          "action": "task_complete",
          "action_input": {"summary": "notes.txt written and verified"}}],
     "summary": "notes.txt written and verified"},
    {"task": "List what is in the sandbox, then finish.",
     "steps": [
         {"thought": "inventory first",
          "action": "list_files", "action_input": {}},
         {"thought": "inventory seen; done",
          "action": "task_complete",
          "action_input": {"summary": "listed sandbox contents"}}],
     "summary": "listed sandbox contents"},
]


def main():
    ap = argparse.ArgumentParser(description="Agent SFT trace pipeline")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--from-jsonl", dest="from_jsonl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--sandbox", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "sft_sandbox"))
    args = ap.parse_args()
    box = Sandbox(args.sandbox, cmd_timeout=30)
    traces = []
    if args.demo:
        traces = DEMO_TRACES
    elif args.from_jsonl:
        with open(args.from_jsonl, encoding="utf-8") as fh:
            for ln, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    traces.append(json.loads(line))
                except ValueError as exc:
                    raise SystemExit("line %d invalid JSON: %s"
                                     % (ln, exc))
    if not traces:
        ap.error("nothing to do: pass --demo or --from-jsonl")
    n = 0
    bad = []
    with open(args.out, "w", encoding="utf-8", newline="\n") as out:
        for ti, trace in enumerate(traces):
            try:
                steps = validate_trace(trace)
            except ValueError as exc:
                bad.append((ti, str(exc)))
                continue
            records, observations = execute_all(trace["task"], steps, box)
            for rec in records:
                out.write(json.dumps(rec) + "\n")
                n += 1
    for ti, err in bad:
        print("trace %d rejected: %s" % (ti, err))
    print("sandbox=%s out=%s" % (box.root, os.path.abspath(args.out)))
    print("RESULT: P3_AGENT_SFT_OK n=%d rejected=%d" % (n, len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())