#!/usr/bin/env python3
"""Live inference test for merged/bdw7b-reasoning-dpo-final.

Tests simultaneous <think> reasoning and <tool_call> generation
on a challenging deep-tech hardware VLSI timing constraint problem.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = ROOT / "merged" / "bdw7b-reasoning-dpo-final"

SYSTEM_PROMPT = (
    "You are BDW, a precise reasoning assistant for deep-tech hardware, computing, "
    "and scientific engineering. When a user query requires computation, sizing, timing, "
    "or conversion: 1. Formulate your reasoning step by step inside a <think>...</think> block. "
    "2. Conclude by calling the appropriate tool within a <tool_call>...</tool_call> block. "
    "Never skip the reasoning block and never omit closing tags."
)

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
                        "description": "Mathematical expression string, e.g. '(180 + 450 + 120 + 50)' or '1.25 + 0.045 - 0.085 - 0.035 - 1.04'."
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

COMPLEX_VLSI_PROMPT = (
    "In a 5nm FinFET multi-corner static timing analysis (STA) run, a critical launch-to-capture "
    "data path has a clock period T_clk = 1.25 ns, clock network skew T_skew = 0.045 ns, capture "
    "flip-flop setup time T_setup = 0.085 ns, clock jitter uncertainty T_jitter = 0.035 ns, and a "
    "combinational logic data path delay consisting of 4 buffer stages with delays 0.18 ns, 0.24 ns, "
    "0.31 ns, and 0.19 ns, plus an interconnect net delay of 0.12 ns. Calculate the worst-case setup "
    "timing slack (T_slack = T_clk + T_skew - T_setup - T_jitter - T_data_path) to determine if the "
    "path meets timing closure."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Live inference test for BDW hybrid model.")
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--prompt", type=str, default=COMPLEX_VLSI_PROMPT)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--device", type=str, default="auto")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    model_path = args.model_path.resolve()

    print("=" * 72)
    print("BDW-7B Ultimate Hybrid Model — Live Inference Test")
    print("=" * 72)
    print(f"Model Path     : {model_path}")
    print(f"Max New Tokens : {args.max_new_tokens}")
    print(f"Temperature    : {args.temperature}")
    print(f"Device         : {args.device}")

    if not model_path.exists():
        print(f"[FATAL] Model directory does not exist: {model_path}", file=sys.stderr)
        return 1

    # Device selection
    if args.device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device = args.device

    print(f"Using device   : {device}")
    if device == "cuda":
        print(f"GPU Device Name: {torch.cuda.get_device_name(0)}")

    # Load Tokenizer
    print("\nLoading tokenizer...")
    t0 = time.time()
    tokenizer = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True)
    print(f"Tokenizer loaded in {time.time() - t0:.2f}s (Vocab: {len(tokenizer)})")

    # Load Model
    print("Loading model in bfloat16...")
    t1 = time.time()
    model = AutoModelForCausalLM.from_pretrained(
        str(model_path),
        torch_dtype=torch.bfloat16,
        device_map=device if device == "cuda" else None,
        local_files_only=True,
        low_cpu_mem_usage=True,
    )
    if device == "cpu":
        model = model.to(torch.bfloat16)
    model.eval()
    print(f"Model loaded in {time.time() - t1:.2f}s")

    # Construct conversation messages
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": args.prompt},
    ]

    # Render prompt with Chat Template + Tool Schemas
    prompt_text = tokenizer.apply_chat_template(
        messages,
        tools=TOOLS,
        add_generation_prompt=True,
        tokenize=False,
    )

    print("\n" + "-" * 72)
    print("RENDERED PROMPT (Chat Template + Tool Schemas):")
    print("-" * 72)
    print(prompt_text)
    print("-" * 72)

    # Tokenize input
    inputs = tokenizer(prompt_text, return_tensors="pt").to(model.device)
    input_length = inputs["input_ids"].shape[1]
    print(f"Prompt tokens  : {input_length}")

    # Generate
    print("Generating response...")
    t2 = time.time()
    gen_kwargs = {
        "max_new_tokens": args.max_new_tokens,
        "pad_token_id": tokenizer.eos_token_id,
    }
    if args.temperature > 0.0:
        gen_kwargs["temperature"] = args.temperature
        gen_kwargs["do_sample"] = True
    else:
        gen_kwargs["do_sample"] = False

    with torch.no_grad():
        output_ids = model.generate(**inputs, **gen_kwargs)

    gen_time = time.time() - t2
    generated_tokens = output_ids[0][input_length:]
    num_gen_tokens = len(generated_tokens)
    tokens_per_sec = num_gen_tokens / gen_time if gen_time > 0 else 0.0

    raw_output = tokenizer.decode(generated_tokens, skip_special_tokens=False)

    print("\n" + "=" * 72)
    print(f"EXACT RAW MODEL GENERATION ({num_gen_tokens} tokens in {gen_time:.2f}s, {tokens_per_sec:.1f} tok/s):")
    print("=" * 72)
    print(raw_output)
    print("=" * 72)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
