#!/usr/bin/env python3
"""Generate a deterministic Phase 8 DPO preference dataset for Reinforcement Learning.

Schema per row:
  prompt:      rendered chat template prompt ending with `<|im_start|>assistant\\n`
  chosen:      complete `<think>...</think>\\n<tool_call>...</tool_call><|im_end|>`
  rejected:    flawed trajectory (no think, malformed tags, flawed logic, or plain text)
  messages_chosen: list of messages for chosen trajectory
  messages_rejected: list of messages for rejected trajectory
  category:    problem domain (vlsi, hpc, physics_math, finance_analytics)
  metadata:    details on reject reason, expected tools, and mathematical values

Outputs:
  phase8_rl/data/dpo_train.jsonl (~170 rows)
  phase8_rl/data/dpo_eval.jsonl  (~30 rows)

CLI:
  python3 generate_dpo_data.py [--check-only] [--train-count 170] [--eval-count 30] [--seed 42]
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import operator
import os
import random
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[0] if (HERE.parent / "merged").exists() else HERE.parents[1]
DEFAULT_OUT = HERE.parent / "data" if HERE.name == "scripts" else HERE / "data"
DEFAULT_TOKENIZER = ROOT / "merged" / "bdw-7b-sft"

SYSTEM_PROMPT = (
    "You are BDW, a precise reasoning assistant for deep-tech hardware, computing, and scientific engineering. "
    "When a user query requires computation, sizing, timing, or conversion: "
    "1. Formulate your reasoning step by step inside a <think>...</think> block. "
    "2. Conclude by calling the appropriate tool within a <tool_call>...</tool_call> block. "
    "Never skip the reasoning block and never omit closing tags."
)

SCHEMA_VERSION = "phase8-dpo-v1"
SOURCE = "phase8-dpo-v1"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluate an exact arithmetic expression supporting numbers, parentheses, +, -, *, /, and exponents (**).",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression string, e.g. '(180 + 450 + 120 + 50)' or '12.5 / (1.1**2 * 1.8e9)'."
                    }
                },
                "required": ["expression"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "unit_converter",
            "description": "Convert a numeric quantity between compatible physical, engineering, or computing units.",
            "parameters": {
                "type": "object",
                "properties": {
                    "value": {
                        "type": "number",
                        "description": "The numeric magnitude to convert."
                    },
                    "from_unit": {
                        "type": "string",
                        "description": "Source unit symbol (e.g. ps, ns, um, nm, mw, uw, gb, mb, tb, gbps, km, mi, m, ft, kg, lb, c, f, s, hr)."
                    },
                    "to_unit": {
                        "type": "string",
                        "description": "Target unit symbol (e.g. ps, ns, um, nm, mw, uw, gb, mb, tb, gbps, km, mi, m, ft, kg, lb, c, f, s, hr)."
                    }
                },
                "required": ["value", "from_unit", "to_unit"],
                "additionalProperties": False,
            },
        },
    },
]

UNIT_CONVERSIONS = {
    ("ps", "ns"): 1e-3, ("ns", "ps"): 1e3,
    ("ns", "us"): 1e-3, ("us", "ns"): 1e3,
    ("nm", "um"): 1e-3, ("um", "nm"): 1e3,
    ("km", "mi"): 0.621371, ("mi", "km"): 1.609344,
    ("m", "ft"): 3.28084, ("ft", "m"): 0.3048,
    ("kg", "lb"): 2.20462, ("lb", "kg"): 0.453592,
    ("mw", "uw"): 1e3, ("uw", "mw"): 1e-3,
    ("gb", "mb"): 1024.0, ("mb", "gb"): 1.0 / 1024.0,
    ("tb", "gb"): 1024.0, ("gb", "tb"): 1.0 / 1024.0,
    ("gbps", "gb/s"): 0.125, ("gb/s", "gbps"): 8.0,
    ("s", "hr"): 1.0 / 3600.0, ("hr", "s"): 3600.0,
    ("min", "s"): 60.0, ("s", "min"): 1.0 / 60.0,
}

_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_eval(expr: str) -> float:
    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        elif isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        elif isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
            return _SAFE_OPS[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
            return _SAFE_OPS[type(node.op)](_eval(node.operand))
        raise ValueError(f"Unsupported AST node: {type(node).__name__}")
    return _eval(ast.parse(expr, mode="eval"))


def convert_units(val: float, f_u: str, t_u: str) -> float:
    f_u, t_u = f_u.lower(), t_u.lower()
    if f_u == t_u:
        return val
    if (f_u, t_u) == ("c", "f"):
        return val * 9.0 / 5.0 + 32.0
    if (f_u, t_u) == ("f", "c"):
        return (val - 32.0) * 5.0 / 9.0
    if (f_u, t_u) in UNIT_CONVERSIONS:
        return val * UNIT_CONVERSIONS[(f_u, t_u)]
    raise ValueError(f"Unsupported conversion: {f_u} -> {t_u}")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# -----------------------------------------------------------------------------
# Generators
# -----------------------------------------------------------------------------
def gen_case(rng: random.Random) -> dict[str, Any]:
    cat = rng.choice(["vlsi", "hpc", "physics_math", "finance_analytics"])
    if cat == "vlsi":
        variant = rng.choice(["timing", "power", "unit"])
        if variant == "timing":
            t_cq, t_comb, t_setup, t_skew = rng.randint(80, 220), rng.randint(300, 800), rng.randint(60, 150), rng.randint(20, 80)
            q = f"In a sequential VLSI datapath, a flip-flop has T_cq = {t_cq} ps and setup time T_setup = {t_setup} ps. Combinational delay is {t_comb} ps with clock skew {t_skew} ps. What is the minimum clock period T_min (ps)?"
            steps = [
                f"Extract timing parameters: T_cq = {t_cq} ps, T_comb = {t_comb} ps, T_setup = {t_setup} ps, T_skew = {t_skew} ps.",
                "To satisfy setup timing constraints: T_min >= T_cq + T_comb + T_setup + T_skew.",
                f"Formulate expression: {t_cq} + {t_comb} + {t_setup} + {t_skew}.",
                "Call calculator to evaluate exact sum."
            ]
            expr = f"{t_cq} + {t_comb} + {t_setup} + {t_skew}"
            return {"category": cat, "question": q, "tool": "calculator", "args": {"expression": expr}, "steps": steps, "res": safe_eval(expr)}
        elif variant == "power":
            c_pf, vdd, f_ghz = rng.randint(20, 80), round(rng.uniform(0.8, 1.2), 2), round(rng.uniform(1.2, 3.5), 1)
            q = f"A submicron processor core operates at Vdd = {vdd} V with f = {f_ghz} GHz. Effective switched capacitance is {c_pf} pF. Calculate dynamic power in watts using P = C_eff * Vdd^2 * f."
            steps = [
                f"Identify parameters: C_eff = {c_pf}e-12 F, Vdd = {vdd} V, f = {f_ghz}e9 Hz.",
                "CMOS dynamic power equation: P_dyn = C_eff * Vdd^2 * f.",
                f"Substitute values: ({c_pf} * 1e-12) * ({vdd}**2) * ({f_ghz} * 1e9).",
                "Invoke calculator tool."
            ]
            expr = f"({c_pf} * 1e-12) * ({vdd}**2) * ({f_ghz} * 1e9)"
            return {"category": cat, "question": q, "tool": "calculator", "args": {"expression": expr}, "steps": steps, "res": safe_eval(expr)}
        else:
            val, f_u, t_u = rng.randint(150, 4500), "ps", "ns"
            q = f"A physical design interconnect wire delay is measured at {val} picoseconds. Convert this delay to nanoseconds."
            steps = [f"Input value: {val} picoseconds (ps).", "Target unit: nanoseconds (ns). 1 ns = 1000 ps.", "Call unit_converter with value and respective unit symbols."]
            return {"category": cat, "question": q, "tool": "unit_converter", "args": {"value": val, "from_unit": f_u, "to_unit": t_u}, "steps": steps, "res": convert_units(val, f_u, t_u)}

    elif cat == "hpc":
        variant = rng.choice(["cluster", "unit"])
        if variant == "cluster":
            nodes, gpus, watts, pue = rng.choice([16, 32, 64]), 8, rng.choice([350, 400, 700]), round(rng.uniform(1.15, 1.35), 2)
            q = f"A supercomputing cluster has {nodes} compute nodes each hosting {gpus} GPUs drawing {watts} W each, with 800 W host overhead per node. If facility PUE is {pue}, compute total power in kW."
            steps = [
                f"Calculate IT power per node: ({gpus} * {watts}) + 800 W.",
                f"Scale across {nodes} nodes, apply PUE {pue}, and divide by 1000 for kilowatts.",
                f"Expression: ({nodes} * ({gpus} * {watts} + 800) * {pue}) / 1000.",
                "Call calculator tool."
            ]
            expr = f"({nodes} * ({gpus} * {watts} + 800) * {pue}) / 1000"
            return {"category": cat, "question": q, "tool": "calculator", "args": {"expression": expr}, "steps": steps, "res": safe_eval(expr)}
        else:
            val, f_u, t_u = rng.choice([100, 200, 400, 800]), "gbps", "gb/s"
            q = f"An InfiniBand network fabric supports a line rate of {val} Gbps. Convert this transmission rate to GB/s."
            steps = [f"Bandwidth magnitude: {val} Gbps.", "Target unit: GB/s. 1 GB/s = 8 Gbps.", "Invoke unit_converter to evaluate."]
            return {"category": cat, "question": q, "tool": "unit_converter", "args": {"value": val, "from_unit": f_u, "to_unit": t_u}, "steps": steps, "res": convert_units(val, f_u, t_u)}

    elif cat == "physics_math":
        variant = rng.choice(["kinetic", "unit"])
        if variant == "kinetic":
            m, v = round(rng.uniform(150.0, 1800.0), 1), round(rng.uniform(15.0, 75.0), 1)
            q = f"A drone with mass {m} kg travels at velocity {v} m/s. Calculate its kinetic energy in joules using E_k = 0.5 * m * v^2."
            steps = [f"Mass m = {m} kg, velocity v = {v} m/s.", "Kinetic energy formula: E = 0.5 * m * v^2.", f"Substitute: 0.5 * {m} * ({v}**2).", "Call calculator."]
            expr = f"0.5 * {m} * ({v}**2)"
            return {"category": cat, "question": q, "tool": "calculator", "args": {"expression": expr}, "steps": steps, "res": safe_eval(expr)}
        else:
            val, f_u, t_u = round(rng.uniform(10.0, 250.0), 1), "km", "mi"
            q = f"A remote optical sensor is positioned {val} kilometers from the base station. Convert this distance to miles."
            steps = [f"Distance: {val} km.", "Target unit: miles (mi). 1 km = 0.621371 mi.", "Invoke unit_converter."]
            return {"category": cat, "question": q, "tool": "unit_converter", "args": {"value": val, "from_unit": f_u, "to_unit": t_u}, "steps": steps, "res": convert_units(val, f_u, t_u)}

    else:  # finance_analytics
        variant = rng.choice(["cloud", "unit"])
        if variant == "cloud":
            inst, rate, days, disc = rng.randint(8, 36), round(rng.uniform(3.5, 12.0), 2), rng.choice([7, 14, 30]), rng.choice([0, 10, 20])
            q = f"A distributed cluster runs {inst} GPU instances at ${rate}/hour continuously for {days} days with a {disc}% discount. Calculate total billed cost in dollars."
            steps = [
                f"Total hours: {days} * 24 = {days * 24} hours.",
                f"Gross cost: {inst} instances * {rate} * {days * 24} hours.",
                f"Net cost after {disc}% discount: gross * (1 - {disc}/100).",
                "Invoke calculator with mathematical formula."
            ]
            expr = f"({inst} * {rate} * {days * 24}) * (1.0 - {disc} / 100)"
            return {"category": cat, "question": q, "tool": "calculator", "args": {"expression": expr}, "steps": steps, "res": safe_eval(expr)}
        else:
            val, f_u, t_u = rng.choice([3600, 7200, 14400, 86400]), "s", "hr"
            q = f"An analytics query batch runs for {val} seconds. Convert this duration to hours."
            steps = [f"Recorded runtime: {val} seconds.", "Target unit: hours (hr). 1 hr = 3600 s.", "Call unit_converter."]
            return {"category": cat, "question": q, "tool": "unit_converter", "args": {"value": val, "from_unit": f_u, "to_unit": t_u}, "steps": steps, "res": convert_units(val, f_u, t_u)}


def build_dpo_row(
    case_id: str,
    split: str,
    item: dict[str, Any],
    rng: random.Random,
    tokenizer: Any,
) -> dict[str, Any]:
    question = item["question"]
    tool = item["tool"]
    args = item["args"]
    steps = item["steps"]

    # 1. Prompt messages
    prompt_msgs = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    prompt_text = tokenizer.apply_chat_template(
        prompt_msgs,
        tools=TOOLS,
        add_generation_prompt=True,
        tokenize=False,
    )

    # 2. Chosen Response
    think_text = "\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1))
    call_json = json.dumps({"name": tool, "arguments": args}, ensure_ascii=False)
    chosen_text = f"<think>\n{think_text}\n</think>\n<tool_call>\n{call_json}\n</tool_call><|im_end|>\n"

    # 3. Rejected Response (Sample among realistic flaws)
    flaw_type = rng.choice(["no_think", "flawed_logic", "unclosed_tag", "plain_text", "inverted"])
    if flaw_type == "no_think":
        # Missing think block entirely
        rejected_text = f"<tool_call>\n{call_json}\n</tool_call><|im_end|>\n"
    elif flaw_type == "flawed_logic":
        # Wrong formula reasoning
        bad_steps = [
            "1. Just multiply all numbers together regardless of equations.",
            "2. Ignore physical units and formula constraints.",
            "3. Submit ad-hoc calculation."
        ]
        bad_think = "\n".join(bad_steps)
        bad_args = {"expression": "0.0"} if tool == "calculator" else {"value": -1, "from_unit": "invalid", "to_unit": "invalid"}
        bad_json = json.dumps({"name": tool, "arguments": bad_args}, ensure_ascii=False)
        rejected_text = f"<think>\n{bad_think}\n</think>\n<tool_call>\n{bad_json}\n</tool_call><|im_end|>\n"
    elif flaw_type == "unclosed_tag":
        # Missing closing </think> tag
        rejected_text = f"<think>\n{think_text}\n<tool_call>\n{call_json}\n</tool_call><|im_end|>\n"
    elif flaw_type == "inverted":
        # Tool call before think
        rejected_text = f"<tool_call>\n{call_json}\n</tool_call>\n<think>\n{think_text}\n</think><|im_end|>\n"
    else:  # plain_text
        rejected_text = f"The answer is approximately {item['res']}.<|im_end|>\n"

    return {
        "id": case_id,
        "split": split,
        "source": SOURCE,
        "category": item["category"],
        "prompt": prompt_text,
        "chosen": chosen_text,
        "rejected": rejected_text,
        "metadata": {
            "flaw_type": flaw_type,
            "tool": tool,
            "expected_arguments": args,
            "expected_result": item["res"],
        },
    }


def generate_all(train_count: int, eval_count: int, seed: int, tokenizer_path: Path, out_dir: Path) -> tuple[Path, Path]:
    rng = random.Random(seed)
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(str(tokenizer_path))

    seen_questions: set[str] = set()

    def sample_items(n: int) -> list[dict[str, Any]]:
        items = []
        while len(items) < n:
            c = gen_case(rng)
            if c["question"] not in seen_questions:
                seen_questions.add(c["question"])
                items.append(c)
        return items

    print(f"[*] Generating {train_count} train rows and {eval_count} eval rows for DPO...")
    train_items = sample_items(train_count)
    eval_items = sample_items(eval_count)

    out_dir.mkdir(parents=True, exist_ok=True)
    train_path = out_dir / "dpo_train.jsonl"
    eval_path = out_dir / "dpo_eval.jsonl"

    with open(train_path, "w", encoding="utf-8") as fh:
        for i, item in enumerate(train_items, 1):
            row = build_dpo_row(f"dpo_train_{i:04d}", "train", item, rng, tokenizer)
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    with open(eval_path, "w", encoding="utf-8") as fh:
        for i, item in enumerate(eval_items, 1):
            row = build_dpo_row(f"dpo_eval_{i:04d}", "eval", item, rng, tokenizer)
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"[+] Wrote {train_path} ({train_count} rows, sha256={sha256_file(train_path)[:12]}...)")
    print(f"[+] Wrote {eval_path} ({eval_count} rows, sha256={sha256_file(eval_path)[:12]}...)")
    return train_path, eval_path


def check_dataset(train_path: Path, eval_path: Path) -> int:
    print("[*] Running dry-run validation on DPO preference dataset...")
    for label, path in [("TRAIN", train_path), ("EVAL", eval_path)]:
        if not path.is_file():
            print(f"[FAIL] Missing {label} file: {path}")
            return 1
        rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
        flaws: dict[str, int] = {}
        for r in rows:
            for k in ["id", "split", "prompt", "chosen", "rejected", "metadata"]:
                if k not in r:
                    print(f"[FAIL] Missing key {k} in {r.get('id')}")
                    return 1
            flaw = r["metadata"]["flaw_type"]
            flaws[flaw] = flaws.get(flaw, 0) + 1
            # Chosen must have both think and tool_call
            if "<think>" not in r["chosen"] or "</think>" not in r["chosen"] or "<tool_call>" not in r["chosen"]:
                print(f"[FAIL] Chosen response missing required tags in {r['id']}")
                return 1
        print(f"\n--- {label} SET ({len(rows)} rows) ---")
        print(f"Flaw distribution in rejected: {flaws}")

    # Check zero overlap
    with open(train_path, encoding="utf-8") as fh:
        train_p = {json.loads(line)["prompt"] for line in fh if line.strip()}
    with open(eval_path, encoding="utf-8") as fh:
        eval_p = {json.loads(line)["prompt"] for line in fh if line.strip()}
    overlap = train_p.intersection(eval_p)
    if overlap:
        print(f"[FAIL] Found {len(overlap)} overlapping prompts!")
        return 1
    print(f"\n[OK] Zero prompt overlap verified ({len(train_p)} train vs {len(eval_p)} eval).")
    print("RESULT: PHASE8_DPO_DATASET_OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Phase 8 DPO dataset")
    parser.add_argument("--train-count", type=int, default=170, help="Train row count (default: 170)")
    parser.add_argument("--eval-count", type=int, default=30, help="Eval row count (default: 30)")
    parser.add_argument("--seed", type=int, default=42, help="Seed (default: 42)")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT, help="Output directory")
    parser.add_argument("--tokenizer", type=Path, default=DEFAULT_TOKENIZER, help="Tokenizer directory")
    parser.add_argument("--check-only", action="store_true", help="Dry run validation only")
    args = parser.parse_args()

    train_p = args.out_dir / "dpo_train.jsonl"
    eval_p = args.out_dir / "dpo_eval.jsonl"

    if args.check_only:
        return check_dataset(train_p, eval_p)

    generate_all(args.train_count, args.eval_count, args.seed, args.tokenizer, args.out_dir)
    return check_dataset(train_p, eval_p)


if __name__ == "__main__":
    sys.exit(main())
