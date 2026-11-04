#!/usr/bin/env python3
"""Generate a deterministic Phase 6 function-calling SFT dataset.

The output is JSONL suitable for a Qwen2.5 chat-template SFT pipeline. Each
row carries:

  tools     - JSON-schema definitions visible to the model
  messages  - system / user / assistant tool_calls / optional tool result /
              final assistant answer
  text      - the exact Qwen2.5 chat-template rendering (unless --no-render)
  tokens    - token count of text (unless --no-render)
  metadata  - expected tool, arguments, result, and trajectory mode

Only the Python standard library is required for generation. Rendering uses
the open-source transformers tokenizer already present on Param Rudra.

RESULT: PHASE6_TOOL_DATASET_OK train=... eval=... | PHASE6_TOOL_DATASET_FAIL ...
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import operator
import os
import random
import sys
from datetime import datetime, timezone

SCHEMA_VERSION = "phase6-tools-v1"
SOURCE = "phase6-tools-v1"
DEFAULT_TOKENIZER = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "merged", "bdw-7b-sft")

SYSTEM_PROMPT = (
    "You are BDW, a precise assistant. Use the provided tools when a "
    "calculation or unit conversion is needed. Emit exactly one tool call "
    "when required and never invent a tool result."
)

UNIT_NAMES = {
    "km": "kilometers", "mi": "miles", "m": "meters", "ft": "feet",
    "kg": "kilograms", "lb": "pounds", "c": "Celsius", "f": "Fahrenheit",
}

# Linear conversions only; Celsius/Fahrenheit are handled separately.
UNIT_FACTORS = {
    ("km", "mi"): 0.621371, ("mi", "km"): 1.609344,
    ("m", "ft"): 3.280839895, ("ft", "m"): 0.3048,
    ("kg", "lb"): 2.2046226218, ("lb", "kg"): 0.45359237,
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluate a basic arithmetic expression using "
                           "numbers, parentheses, +, -, *, and /.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Arithmetic expression, e.g. (12 + 7) * 3.",
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
            "description": "Convert a numeric value between supported units.",
            "parameters": {
                "type": "object",
                "properties": {
                    "value": {"type": "number"},
                    "from_unit": {
                        "type": "string",
                        "enum": ["km", "mi", "m", "ft", "kg", "lb", "c", "f"],
                    },
                    "to_unit": {
                        "type": "string",
                        "enum": ["km", "mi", "m", "ft", "kg", "lb", "c", "f"],
                    },
                },
                "required": ["value", "from_unit", "to_unit"],
                "additionalProperties": False,
            },
        },
    },
]

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _eval_ast(node):
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        return _BIN_OPS[type(node.op)](_eval_ast(node.left), _eval_ast(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval_ast(node.operand))
    raise ValueError("unsupported arithmetic expression")


def _safe_eval(expression: str):
    return _eval_ast(ast.parse(expression, mode="eval"))


def _format_number(value):
    if isinstance(value, float):
        rounded = round(value, 6)
        if rounded.is_integer():
            value = int(rounded)
        else:
            return format(rounded, ",.6g")
    if isinstance(value, int):
        return format(value, ",")
    return str(value)


def _compact(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def _convert(value, from_unit, to_unit):
    if from_unit == to_unit:
        return float(value)
    if (from_unit, to_unit) == ("c", "f"):
        return value * 9.0 / 5.0 + 32.0
    if (from_unit, to_unit) == ("f", "c"):
        return (value - 32.0) * 5.0 / 9.0
    try:
        return value * UNIT_FACTORS[(from_unit, to_unit)]
    except KeyError as exc:
        raise ValueError("unsupported conversion: %s -> %s" % (from_unit, to_unit)) from exc


def _calculator_case(rng, seen):
    while True:
        a = rng.randint(11, 9999)
        b = rng.randint(11, 999)
        c = rng.randint(2, 99)
        variant = rng.randrange(8)
        if variant == 0:
            question = "What is %d + %d?" % (a, b)
            expression = "%d + %d" % (a, b)
        elif variant == 1:
            question = "Calculate %d minus %d." % (a, b)
            expression = "%d - %d" % (a, b)
        elif variant == 2:
            question = "What is %d times %d?" % (a, b)
            expression = "%d * %d" % (a, b)
        elif variant == 3:
            question = "Compute %d divided by %d." % (a, c)
            expression = "%d / %d" % (a, c)
        elif variant == 4:
            question = "What is (%d + %d) times %d?" % (a, b, c)
            expression = "(%d + %d) * %d" % (a, b, c)
        elif variant == 5:
            question = "Evaluate %d * %d - %d." % (a, b, c)
            expression = "%d * %d - %d" % (a, b, c)
        elif variant == 6:
            pct = rng.randint(5, 95)
            base = rng.randint(100, 5000)
            question = "What is %d%% of %d?" % (pct, base)
            expression = "%d * %d / 100" % (base, pct)
        else:
            question = "Calculate (%d - %d) / %d." % (a, b, c)
            expression = "(%d - %d) / %d" % (a, b, c)
        if question not in seen:
            seen.add(question)
            return question, expression, _safe_eval(expression)


def _unit_case(rng, seen):
    pairs = list(UNIT_FACTORS) + [("c", "f"), ("f", "c")]
    while True:
        from_unit, to_unit = rng.choice(pairs)
        value = round(rng.uniform(0.5, 1000.0), 1)
        from_name = UNIT_NAMES[from_unit]
        to_name = UNIT_NAMES[to_unit]
        variant = rng.randrange(3)
        if variant == 0:
            question = "Convert %s %s to %s." % (value, from_name, to_name)
        elif variant == 1:
            question = "How many %s are in %s %s?" % (to_name, value, from_name)
        else:
            question = "What is %s %s in %s?" % (value, from_name, to_name)
        if question not in seen:
            seen.add(question)
            result = round(_convert(value, from_unit, to_unit), 6)
            return question, value, from_unit, to_unit, result


def _row(case_id, split, mode, question, tool_name, arguments, expected_result,
         final_answer):
    call_id = "call_%s" % case_id.rsplit("_", 1)[-1]
    assistant_call = {
        "role": "assistant",
        "content": "",
        "tool_calls": [{
            "id": call_id,
            "type": "function",
            "function": {"name": tool_name, "arguments": arguments},
        }],
    }
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
        assistant_call,
    ]
    if mode == "full":
        messages.extend([
            {
                "role": "tool",
                "tool_call_id": call_id,
                "content": _compact({"result": expected_result}),
            },
            {"role": "assistant", "content": final_answer},
        ])
    return {
        "id": case_id,
        "split": split,
        "source": SOURCE,
        "tools": TOOLS,
        "messages": messages,
        "metadata": {
            "tool": tool_name,
            "mode": mode,
            "expected_arguments": arguments,
            "expected_result": expected_result,
        },
    }


def _build_train(size, seed):
    rng = random.Random(seed)
    seen = set()
    rows = []
    for idx in range(size):
        mode = "full" if idx % 3 == 0 else "call_only"
        use_unit = (idx % 5 == 0)
        case_id = "tool_train_%04d" % (idx + 1)
        if use_unit:
            question, value, from_unit, to_unit, result = _unit_case(rng, seen)
            args = {"value": value, "from_unit": from_unit, "to_unit": to_unit}
            final = "%s %s is approximately %s %s." % (
                value, UNIT_NAMES[from_unit], _format_number(result),
                UNIT_NAMES[to_unit])
            rows.append(_row(case_id, "train", mode, question,
                             "unit_converter", args, result, final))
        else:
            question, expression, result = _calculator_case(rng, seen)
            args = {"expression": expression}
            final = "The result is %s." % _format_number(result)
            rows.append(_row(case_id, "train", mode, question,
                             "calculator", args, result, final))
    return rows


def _build_eval(size, seed):
    rng = random.Random(seed + 1)
    seen = set()
    rows = []
    for idx in range(size):
        use_unit = (idx % 5 == 0)
        case_id = "tool_eval_%04d" % (idx + 1)
        if use_unit:
            question, value, from_unit, to_unit, result = _unit_case(rng, seen)
            args = {"value": value, "from_unit": from_unit, "to_unit": to_unit}
            final = "%s %s is approximately %s %s." % (
                value, UNIT_NAMES[from_unit], _format_number(result),
                UNIT_NAMES[to_unit])
            rows.append(_row(case_id, "eval", "call_only", question,
                             "unit_converter", args, result, final))
        else:
            question, expression, result = _calculator_case(rng, seen)
            args = {"expression": expression}
            final = "The result is %s." % _format_number(result)
            rows.append(_row(case_id, "eval", "call_only", question,
                             "calculator", args, result, final))
    return rows


def _write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _render(rows, tokenizer_path):
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, local_files_only=True)
    for row in rows:
        row["text"] = tokenizer.apply_chat_template(
            row["messages"], tools=row["tools"], tokenize=False,
            add_generation_prompt=False)
        row["tokens"] = len(tokenizer(row["text"], add_special_tokens=False)["input_ids"])
    return tokenizer_path


def main():
    parser = argparse.ArgumentParser(description="Generate Phase 6 tool-use JSONL")
    parser.add_argument("--out-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"))
    parser.add_argument("--train-size", type=int, default=120)
    parser.add_argument("--eval-size", type=int, default=24)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--tokenizer", default=DEFAULT_TOKENIZER)
    parser.add_argument("--no-render", action="store_true",
                        help="emit messages/tools only; skip Qwen text/token rendering")
    args = parser.parse_args()

    try:
        train = _build_train(args.train_size, args.seed)
        eval_rows = _build_eval(args.eval_size, args.seed)
        os.makedirs(args.out_dir, exist_ok=True)
        train_path = os.path.join(args.out_dir, "tool_calls_train.jsonl")
        eval_path = os.path.join(args.out_dir, "tool_calls_eval.jsonl")
        if not args.no_render:
            _render(train + eval_rows, args.tokenizer)
        _write_jsonl(train_path, train)
        _write_jsonl(eval_path, eval_rows)

        all_rows = train + eval_rows
        tool_counts = {}
        mode_counts = {}
        for row in all_rows:
            tool_counts[row["metadata"]["tool"]] = tool_counts.get(row["metadata"]["tool"], 0) + 1
            mode_counts[row["metadata"]["mode"]] = mode_counts.get(row["metadata"]["mode"], 0) + 1
        token_values = [row["tokens"] for row in all_rows if "tokens" in row]
        summary = {
            "schema_version": SCHEMA_VERSION,
            "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "seed": args.seed,
            "train_rows": len(train),
            "eval_rows": len(eval_rows),
            "tool_counts": tool_counts,
            "mode_counts": mode_counts,
            "tokenizer": None if args.no_render else args.tokenizer,
            "token_stats": {
                "min": min(token_values) if token_values else None,
                "mean": round(sum(token_values) / len(token_values), 2) if token_values else None,
                "max": max(token_values) if token_values else None,
            },
            "files": {
                "train": os.path.relpath(train_path, args.out_dir),
                "eval": os.path.relpath(eval_path, args.out_dir),
                "train_sha256": _sha256(train_path),
                "eval_sha256": _sha256(eval_path),
            },
            "schema": {
                "tools": "OpenAI-style tool definitions (JSON object arguments for Qwen2.5)",
                "messages": "system, user, assistant tool_calls, optional tool result and final answer",
                "text": "Qwen2.5 chat-template rendering including # Tools and <tool_call> tags",
                "tokens": "token count of text",
            },
        }
        summary_path = os.path.join(args.out_dir, "dataset_summary.json")
        with open(summary_path, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        print("RESULT: PHASE6_TOOL_DATASET_OK train=%d eval=%d tools=%s modes=%s"
              % (len(train), len(eval_rows), tool_counts, mode_counts))
        print("train: %s" % train_path)
        print("eval:  %s" % eval_path)
        print("summary: %s" % summary_path)
        if token_values:
            print("tokens: min=%d mean=%.2f max=%d" % (
                min(token_values), sum(token_values) / len(token_values),
                max(token_values)))
        print("preview_id: %s" % all_rows[0]["id"])
    except Exception as exc:
        print("RESULT: PHASE6_TOOL_DATASET_FAIL %s: %s" % (type(exc).__name__, exc))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
