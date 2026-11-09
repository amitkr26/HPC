#!/usr/bin/env python3
"""Phase 8 DPO evaluation: base + Phase 7 SFT + Phase 8 DPO adapter."""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Any

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEFAULT_MODEL = ROOT / "merged" / "bdw-7b-sft"
DEFAULT_P7_ADAPTER = ROOT / "lora_combined" / "p7_combined" / "final"
DEFAULT_P8_ADAPTER = ROOT / "lora_dpo" / "p8_dpo" / "final"
DEFAULT_EVAL = ROOT / "phase7_combined" / "data" / "combined_eval.jsonl"
DEFAULT_OUT = ROOT / "phase8_rl" / "eval" / "dpo_eval_v2_0_bdw7b_sft_p7_p8.json"

OPEN_THINK = "<think>"
CLOSE_THINK = "</think>"
OPEN_TOOL = "<tool_call>"
CLOSE_TOOL = "</tool_call>"

TOOL_CALL_RE = re.compile(r"<tool_call>\s*(.*?)\s*</tool_call>", re.DOTALL)


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("phase8_dpo_eval")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", datefmt="%H:%M:%S")
        )
        logger.addHandler(handler)
    return logger


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_rows(path: Path) -> list[dict[str, Any]]:
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def parse_tool_call(text: str) -> tuple[dict[str, Any] | None, str | None]:
    match = TOOL_CALL_RE.search(text)
    if not match:
        return None, "No <tool_call>...</tool_call> block found"
    raw = match.group(1).strip()
    try:
        obj = json.loads(raw)
        if not isinstance(obj, dict):
            return None, "Parsed JSON is not an object"
        if "name" not in obj or not isinstance(obj["name"], str):
            return None, "Missing or invalid 'name' field in tool call"
        if "arguments" not in obj or not isinstance(obj["arguments"], dict):
            return None, "Missing or invalid 'arguments' dict in tool call"
        return obj, None
    except Exception as exc:
        return None, f"JSON decode error: {exc}"


def analyze_combined_format(text: str) -> dict[str, Any]:
    opens_think = text.count(OPEN_THINK)
    closes_think = text.count(CLOSE_THINK)
    first_open_think = text.find(OPEN_THINK)
    first_close_think = text.find(CLOSE_THINK)

    opens_tool = text.count(OPEN_TOOL)
    closes_tool = text.count(CLOSE_TOOL)
    first_open_tool = text.find(OPEN_TOOL)
    first_close_tool = text.find(CLOSE_TOOL)

    has_think_pair = (
        opens_think == 1
        and closes_think == 1
        and first_open_think != -1
        and first_close_think != -1
        and first_open_think < first_close_think
    )
    starts_with_think = text.lstrip().startswith(OPEN_THINK)
    reasoning_text = ""
    if has_think_pair:
        reasoning_text = text[first_open_think + len(OPEN_THINK):first_close_think].strip()

    valid_think = bool(has_think_pair and starts_with_think and reasoning_text)

    has_tool_pair = (
        opens_tool == 1
        and closes_tool == 1
        and first_open_tool != -1
        and first_close_tool != -1
        and first_open_tool < first_close_tool
    )
    parsed_call, tool_err = parse_tool_call(text) if has_tool_pair else (None, "Missing tag pair")
    valid_tool = bool(has_tool_pair and parsed_call is not None)

    correct_order = False
    if has_think_pair and has_tool_pair:
        correct_order = first_close_think < first_open_tool

    extra_before = bool(text[:first_open_think].strip()) if first_open_think != -1 else bool(text.strip())
    plain_text = opens_think == 0 and closes_think == 0 and opens_tool == 0 and closes_tool == 0

    valid_combined = bool(valid_think and valid_tool and correct_order and not extra_before)

    return {
        "valid_combined_format": valid_combined,
        "valid_think_format": valid_think,
        "valid_tool_format": valid_tool,
        "correct_order": correct_order,
        "think_tag_present": opens_think > 0 or closes_think > 0,
        "tool_tag_present": opens_tool > 0 or closes_tool > 0,
        "missing_closing_think": opens_think > 0 and closes_think == 0,
        "missing_closing_tool": opens_tool > 0 and closes_tool == 0,
        "plain_text": plain_text,
        "extra_text_before_think": extra_before,
        "reasoning_text": reasoning_text,
        "parsed_tool_call": parsed_call,
        "tool_parse_error": tool_err,
    }


def compute_rate(items: list[bool]) -> dict[str, Any]:
    hits = sum(1 for item in items if item)
    total = len(items)
    return {
        "hit": hits,
        "total": total,
        "percent": round(100.0 * hits / total, 1) if total else 0.0,
    }


def merge_adapter(model: Any, adapter: Path, label: str, logger: logging.Logger) -> Any:
    logger.info("Loading %s adapter from %s...", label, adapter)
    model = PeftModel.from_pretrained(model, str(adapter), is_trainable=False)
    model = model.merge_and_unload(safe_merge=True)
    torch.cuda.empty_cache()
    logger.info("%s adapter merged and unloaded.", label)
    return model


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 8 DPO combined-format evaluation")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL, help="Base model")
    parser.add_argument("--p7-adapter", type=Path, default=DEFAULT_P7_ADAPTER, help="Phase 7 SFT LoRA adapter")
    parser.add_argument("--p8-adapter", type=Path, default=DEFAULT_P8_ADAPTER, help="Phase 8 DPO LoRA adapter")
    parser.add_argument("--eval", dest="eval_file", type=Path, default=DEFAULT_EVAL, help="Eval jsonl")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output JSON")
    parser.add_argument("--max_new_tokens", type=int, default=512, help="Max generation tokens")
    parser.add_argument("--limit", type=int, default=0, help="Optional row limit for smoke checks")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()

    logger = setup_logger()
    logger.info("=== Phase 8 Combined DPO Evaluation ===")
    logger.info("Base Model:    %s", args.model)
    logger.info("Phase 7 LoRA:  %s", args.p7_adapter)
    logger.info("Phase 8 DPO:   %s", args.p8_adapter)
    logger.info("Eval Dataset:  %s", args.eval_file)
    logger.info("Output File:   %s", args.out)
    logger.info("Compute Device: %s", args.device)

    if not args.model.is_dir():
        logger.error("Base model path does not exist: %s", args.model)
        return 1
    for label, adapter in (("Phase 7", args.p7_adapter), ("Phase 8", args.p8_adapter)):
        if not adapter.is_dir():
            logger.error("%s adapter path does not exist: %s", label, adapter)
            return 1
        if not (adapter / "adapter_config.json").is_file():
            logger.error("%s adapter config missing: %s", label, adapter / "adapter_config.json")
            return 1
    if not args.eval_file.is_file():
        logger.error("Eval file does not exist: %s", args.eval_file)
        return 1

    eval_rows = load_rows(args.eval_file)
    if args.limit > 0:
        eval_rows = eval_rows[: args.limit]
    if not eval_rows:
        logger.error("No evaluation rows loaded")
        return 1
    eval_hash = sha256_file(args.eval_file)
    logger.info("Loaded %d eval rows (sha256=%s...)", len(eval_rows), eval_hash[:12])

    logger.info("Loading tokenizer from %s...", args.model)
    tokenizer = AutoTokenizer.from_pretrained(str(args.model), local_files_only=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    logger.info("Loading base model in bfloat16...")
    t0 = time.time()
    model = AutoModelForCausalLM.from_pretrained(
        str(args.model),
        torch_dtype=torch.bfloat16 if args.device == "cuda" else torch.float32,
        device_map=args.device,
        local_files_only=True,
    )
    model = merge_adapter(model, args.p7_adapter, "Phase 7 SFT", logger)
    model = merge_adapter(model, args.p8_adapter, "Phase 8 DPO", logger)
    model.eval()
    logger.info("Merged model loaded in %.2fs", time.time() - t0)

    results: list[dict[str, Any]] = []
    t_gen_start = time.time()

    for idx, row in enumerate(eval_rows, 1):
        case_id = row["id"]
        category = row["category"]
        question = row["question"]
        tools = row.get("tools", [])
        expected_meta = row.get("metadata", {})
        expected_tool = expected_meta.get("tool")
        expected_args = expected_meta.get("expected_arguments", {})

        prompt_msgs = [m for m in row["messages"] if m["role"] in ("system", "user")]
        prompt_text = tokenizer.apply_chat_template(
            prompt_msgs,
            tools=tools,
            add_generation_prompt=True,
            tokenize=False,
        )

        inputs = tokenizer(prompt_text, return_tensors="pt").to(args.device)
        input_len = inputs["input_ids"].shape[1]

        with torch.inference_mode():
            outputs = model.generate(
                **inputs,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )

        gen_tokens = outputs[0][input_len:]
        raw_output = tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()

        analysis = analyze_combined_format(raw_output)

        tool_name_match = False
        tool_args_match = False
        parsed_call = analysis["parsed_tool_call"]
        if parsed_call:
            tool_name_match = parsed_call.get("name") == expected_tool
            gen_args = parsed_call.get("arguments", {})
            if expected_tool == "calculator":
                tool_args_match = gen_args.get("expression") == expected_args.get("expression")
            elif expected_tool == "unit_converter":
                tool_args_match = (
                    str(gen_args.get("from_unit", "")).lower() == str(expected_args.get("from_unit", "")).lower()
                    and str(gen_args.get("to_unit", "")).lower() == str(expected_args.get("to_unit", "")).lower()
                )

        record = {
            "id": case_id,
            "category": category,
            "question": question,
            "expected_tool": expected_tool,
            "expected_arguments": expected_args,
            "raw_output": raw_output,
            "generated_tokens": len(gen_tokens),
            "tool_name_match": tool_name_match,
            "tool_args_match": tool_args_match,
            **analysis,
        }
        results.append(record)
        logger.info(
            "[%02d/%02d] %s (%s): combined=%s think=%s tool=%s tokens=%d",
            idx,
            len(eval_rows),
            case_id,
            category,
            analysis["valid_combined_format"],
            analysis["valid_think_format"],
            analysis["valid_tool_format"],
            len(gen_tokens),
        )

    t_total = time.time() - t_gen_start
    logger.info("Evaluation completed in %.2fs (%.2fs/row)", t_total, t_total / len(eval_rows))

    combined_valid = [r["valid_combined_format"] for r in results]
    think_valid = [r["valid_think_format"] for r in results]
    tool_valid = [r["valid_tool_format"] for r in results]
    think_present = [r["think_tag_present"] for r in results]
    tool_present = [r["tool_tag_present"] for r in results]
    plain_text = [r["plain_text"] for r in results]
    missing_closing_think = [r["missing_closing_think"] for r in results]
    missing_closing_tool = [r["missing_closing_tool"] for r in results]
    correct_order = [r["correct_order"] for r in results]
    name_matches = [r["tool_name_match"] for r in results]
    args_matches = [r["tool_args_match"] for r in results]

    summary = {
        "suite": "phase8-dpo-eval-v1",
        "model": str(args.model),
        "p7_adapter": str(args.p7_adapter),
        "p8_adapter": str(args.p8_adapter),
        "eval_file": str(args.eval_file),
        "eval_sha256": eval_hash,
        "n": len(results),
        "elapsed_seconds": round(t_total, 2),
        "metrics": {
            "valid_combined_format": compute_rate(combined_valid),
            "valid_think_format": compute_rate(think_valid),
            "valid_tool_format": compute_rate(tool_valid),
            "correct_tag_order": compute_rate(correct_order),
            "think_tag_present": compute_rate(think_present),
            "tool_tag_present": compute_rate(tool_present),
            "missing_closing_think": compute_rate(missing_closing_think),
            "missing_closing_tool": compute_rate(missing_closing_tool),
            "plain_text": compute_rate(plain_text),
            "tool_name_match": compute_rate(name_matches),
            "tool_args_match": compute_rate(args_matches),
        },
        "by_category": {},
        "results": results,
    }

    for cat in sorted({r["category"] for r in results}):
        cat_rows = [r for r in results if r["category"] == cat]
        summary["by_category"][cat] = {
            "n": len(cat_rows),
            "valid_combined_format": compute_rate([r["valid_combined_format"] for r in cat_rows]),
            "valid_think_format": compute_rate([r["valid_think_format"] for r in cat_rows]),
            "valid_tool_format": compute_rate([r["valid_tool_format"] for r in cat_rows]),
        }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)
    logger.info("Saved DPO evaluation summary to %s", args.out)

    print("\n" + "=" * 65)
    print("    PHASE 8 DPO METRICS (v2.0-bdw7b-sft + P7 SFT + P8 DPO)")
    print("=" * 65)
    print(f"Total Evaluation Rows:       {len(results)}")
    print(f"Valid Combined Format Rate:  {summary['metrics']['valid_combined_format']['hit']}/{len(results)} ({summary['metrics']['valid_combined_format']['percent']}%)")
    print(f"Valid Think Format Rate:     {summary['metrics']['valid_think_format']['hit']}/{len(results)} ({summary['metrics']['valid_think_format']['percent']}%)")
    print(f"Valid Tool Call Format Rate: {summary['metrics']['valid_tool_format']['hit']}/{len(results)} ({summary['metrics']['valid_tool_format']['percent']}%)")
    print(f"Correct Tag Order Rate:      {summary['metrics']['correct_tag_order']['hit']}/{len(results)} ({summary['metrics']['correct_tag_order']['percent']}%)")
    print(f"Tool Name Match Rate:        {summary['metrics']['tool_name_match']['hit']}/{len(results)} ({summary['metrics']['tool_name_match']['percent']}%)")
    print(f"Tool Args Match Rate:        {summary['metrics']['tool_args_match']['hit']}/{len(results)} ({summary['metrics']['tool_args_match']['percent']}%)")
    print(f"Missing Closing Think:       {summary['metrics']['missing_closing_think']['hit']}/{len(results)} ({summary['metrics']['missing_closing_think']['percent']}%)")
    print(f"Missing Closing Tool:        {summary['metrics']['missing_closing_tool']['hit']}/{len(results)} ({summary['metrics']['missing_closing_tool']['percent']}%)")
    print(f"Plain Text (No Tags):        {summary['metrics']['plain_text']['hit']}/{len(results)} ({summary['metrics']['plain_text']['percent']}%)")
    print("=" * 65)

    print(
        f"RESULT: PHASE8_DPO_EVAL_OK "
        f"combined={summary['metrics']['valid_combined_format']['hit']}/{len(results)} "
        f"think={summary['metrics']['valid_think_format']['hit']}/{len(results)} "
        f"tool={summary['metrics']['valid_tool_format']['hit']}/{len(results)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
