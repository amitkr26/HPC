#!/usr/bin/env python3
"""Phase 6 reasoning evaluation: test trained LoRA adapter on held-out prompts."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEFAULT_BASE = ROOT / "merged" / "bdw-7b-sft"
DEFAULT_ADAPTER = ROOT / "lora_reasoning" / "p6_reasoning" / "final"
DEFAULT_EVAL = HERE / "data" / "reasoning_eval.jsonl"
DEFAULT_OUT = HERE / "eval" / "reasoning_trained_v2_0_bdw7b_sft.json"
OPEN_TAG = "<think>"
CLOSE_TAG = "</think>"
CATEGORIES = ("math", "logic", "coding")
CODE_FENCE_RE = re.compile(r"```(?:python3?|py)?\s*\n(.*?)```", re.S | re.I)
NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")
SAFE_BUILTIN_NAMES = (
    "abs", "all", "any", "bool", "bytes", "chr", "dict", "divmod", "enumerate",
    "filter", "float", "format", "frozenset", "hash", "int", "isinstance",
    "iter", "len", "list", "map", "max", "min", "next", "ord", "pow", "print",
    "range", "repr", "reversed", "round", "set", "sorted", "str", "sum",
    "tuple", "type", "zip", "Exception", "ValueError", "TypeError",
    "IndexError", "KeyError", "ZeroDivisionError", "RuntimeError",
)
CODE_WRAPPER = r"""
import builtins
import inspect
import json
import sys

code = sys.argv[1]
function_name = sys.argv[2]
sample = json.loads(sys.argv[3])
safe_names = json.loads(sys.argv[4])
safe = {name: getattr(builtins, name) for name in safe_names
        if hasattr(builtins, name)}
namespace = {"__builtins__": safe}
try:
    exec(code, namespace)
    function = namespace[function_name]
    parameter_count = len(inspect.signature(function).parameters)
    arguments = tuple(sample) if parameter_count > 1 else (sample,)
    result = function(*arguments)
    print("__RESULT__" + json.dumps(result, sort_keys=True, default=str))
except BaseException as error:
    print("__ERROR__" + type(error).__name__ + ": " + str(error))
"""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def rate(values: list[bool]) -> dict[str, Any]:
    hits = sum(1 for value in values if value)
    total = len(values)
    return {
        "hit": hits,
        "total": total,
        "percent": round((hits / total) * 100.0, 1) if total else 0.0,
    }


def analyze_format(text: str) -> dict[str, Any]:
    opens = text.count(OPEN_TAG)
    closes = text.count(CLOSE_TAG)
    first_open = text.find(OPEN_TAG)
    first_close = text.find(CLOSE_TAG)
    has_pair = (
        opens == 1 and closes == 1
        and first_open != -1 and first_close != -1 and first_open < first_close
    )
    reasoning = ""
    first_final = ""
    if has_pair:
        reasoning = text[first_open + len(OPEN_TAG):first_close].strip()
        first_final = text[first_close + len(CLOSE_TAG):].strip()
    final_region = text.rsplit(CLOSE_TAG, 1)[1].strip() if closes else text.strip()
    starts_with_think = text.lstrip().startswith(OPEN_TAG)
    extra_before = bool(text[:first_open].strip()) if first_open != -1 else False
    return {
        "valid_think_format": bool(
            has_pair and starts_with_think and reasoning and first_final
        ),
        "complete_think_block": bool(has_pair and reasoning and first_final),
        "think_tag_present": opens > 0 or closes > 0,
        "plain_text": opens == 0 and closes == 0,
        "missing_closing_tag": opens > 0 and closes == 0,
        "missing_opening_tag": closes > 0 and opens == 0,
        "multiple_think_blocks": opens > 1 or closes > 1,
        "extra_text_before_think": extra_before,
        "empty_reasoning": has_pair and not reasoning,
        "empty_final_answer": closes > 0 and not final_region,
        "reasoning_text": reasoning,
        "final_answer_text": final_region,
    }


def expected_number(answer: str) -> float | None:
    match = NUMBER_RE.search(answer.replace(",", ""))
    return float(match.group()) if match else None


def candidate_number(text: str) -> float | None:
    matches = NUMBER_RE.findall(text.replace(",", ""))
    if not matches:
        return None
    return float(matches[-1])


def logic_order(text: str, names: list[str]) -> list[str] | None:
    known = set(names)
    positions: list[tuple[int, str]] = []
    for name in known:
        position = text.find(name)
        if position != -1:
            positions.append((position, name))
    if len(positions) != len(known):
        return None
    positions.sort(key=lambda pair: pair[0])
    return [name for _, name in positions]


def extract_code(text: str, function_name: str) -> str | None:
    matches = CODE_FENCE_RE.findall(text)
    for block in matches:
        if f"def {function_name}(" in block:
            return block.strip()
    candidate = text.rsplit(CLOSE_TAG, 1)[1].strip() if CLOSE_TAG in text else text.strip()
    for block in CODE_FENCE_RE.findall(candidate):
        if f"def {function_name}(" in block:
            return block.strip()
    lines: list[str] = []
    recording = False
    for line in candidate.splitlines():
        if line.startswith(f"def {function_name}("):
            recording = True
        if recording:
            lines.append(line)
    return "\n".join(lines).strip() if lines else None


def run_candidate_code(
    code: str, function_name: str, sample_input: Any
) -> tuple[Any, str | None]:
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as script:
        script.write(CODE_WRAPPER)
        script_path = script.name
    try:
        command = [
            sys.executable,
            script_path,
            code,
            function_name,
            json.dumps(sample_input),
            json.dumps(SAFE_BUILTIN_NAMES),
        ]
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=5.0,
            check=False,
        )
        output = process.stdout
        for line in output.splitlines():
            if line.startswith("__RESULT__"):
                return json.loads(line[len("__RESULT__"):]), None
            if line.startswith("__ERROR__"):
                return None, line[len("__ERROR__"):]
        error = process.stderr.strip() or f"Process exited {process.returncode}"
        return None, error[:200]
    except subprocess.TimeoutExpired:
        return None, "Execution timed out (5s)"
    except Exception as exc:
        return None, f"Execution harness error: {exc}"
    finally:
        try:
            os.unlink(script_path)
        except OSError:
            pass


def score_row(row: dict[str, Any], text: str) -> dict[str, Any]:
    format_info = analyze_format(text)
    final_text = format_info["final_answer_text"]
    metadata = row.get("metadata", {})
    expected_answer = metadata.get("answer", "")
    candidate: Any = None
    code_extracted = None
    code_error = None

    if row["category"] == "math":
        expected_value = expected_number(expected_answer)
        candidate = candidate_number(final_text)
        semantic_match = (
            expected_value is not None and candidate is not None
            and math.isclose(candidate, expected_value, rel_tol=1e-9, abs_tol=1e-9)
        )
        expected_display = expected_value
    elif row["category"] == "logic":
        expected_order = [name.strip() for name in expected_answer.split("->")]
        candidate = logic_order(final_text, expected_order)
        semantic_match = candidate == expected_order
        expected_display = expected_order
    elif row["category"] == "coding":
        function_name = metadata["function_name"]
        code_extracted = extract_code(final_text, function_name)
        expected_display = metadata["sample_output"]
        if code_extracted is None:
            code_error = "No Python implementation found"
            semantic_match = False
        else:
            candidate, code_error = run_candidate_code(
                code_extracted, function_name, metadata["sample_input"]
            )
            semantic_match = code_error is None and candidate == expected_display
    else:
        raise ValueError("Unknown category: %s" % row["category"])

    return {
        "id": row.get("id"),
        "category": row["category"],
        "question": row["question"],
        "expected_answer": expected_answer,
        "expected_semantic_value": expected_display,
        "raw_output": text,
        "final_answer_text": final_text,
        "candidate_semantic_value": candidate,
        "answer_semantic_match": semantic_match,
        "code_extracted": code_extracted,
        "code_error": code_error,
        **format_info,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate v2.0-bdw7b-sft on held-out reasoning prompts."
    )
    parser.add_argument("--base", default=str(DEFAULT_BASE), help="Base model directory")
    parser.add_argument("--adapter", default=str(DEFAULT_ADAPTER), help="LoRA adapter directory")
    parser.add_argument("--eval", dest="eval_file", default=str(DEFAULT_EVAL), help="Evaluation JSONL file")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Output JSON path")
    parser.add_argument("--max-new-tokens", type=int, default=512, help="Max new tokens to generate")
    parser.add_argument("--do-sample", action="store_true", default=False, help="Enable stochastic sampling")
    parser.add_argument("--temperature", type=float, default=0.7, help="Sampling temperature")
    parser.add_argument("--top-p", type=float, default=0.9, help="Top-p sampling cutoff")
    parser.add_argument("--seed", type=int, default=1337, help="Random seed for generation")
    parser.add_argument("--device", default="cuda", help="Target execution device")
    parser.add_argument("--limit", type=int, default=0, help="Optional limit on rows")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    import torch
    import transformers
    from peft import PeftModel

    base_dir = Path(args.base).expanduser().resolve()
    adapter_dir = Path(args.adapter).expanduser().resolve()
    eval_file = Path(args.eval_file).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()

    # Preflight validations
    if not base_dir.is_dir():
        raise SystemExit(f"Base model directory not found: {base_dir}")
    if not adapter_dir.is_dir():
        raise SystemExit(
            f"Reasoning LoRA adapter directory not found: {adapter_dir}.\n"
            "Ensure train_reasoning.slurm has completed successfully before evaluating."
        )
    if not (adapter_dir / "adapter_config.json").is_file():
        raise SystemExit(f"adapter_config.json missing in {adapter_dir}. Incomplete adapter training.")
    if not eval_file.is_file():
        raise SystemExit(f"Eval file not found: {eval_file}")

    rows = load_rows(eval_file)
    if args.limit:
        rows = rows[: args.limit]
    if not rows:
        raise SystemExit("No eval rows loaded")
    if len(rows) != 24 and not args.limit:
        print("WARNING: expected 24 eval rows, got %d" % len(rows), flush=True)

    print("=" * 72)
    print("Phase 6 Reasoning Evaluation (Trained LoRA)")
    print("=" * 72)
    print("base_dir    :", base_dir)
    print("adapter_dir :", adapter_dir)
    print("eval_file   :", eval_file)
    print("eval_sha256 :", sha256_file(eval_file))
    print("rows        :", len(rows))
    print("torch       :", torch.__version__)
    print("transformers:", transformers.__version__)
    print("cuda        :", torch.cuda.is_available())
    if not torch.cuda.is_available():
        raise SystemExit("CUDA is not available on this compute node")
    print("gpu         :", torch.cuda.get_device_name(0))
    print("decoding    : %s, max_new_tokens=%d, seed=%d%s"
          % ("sampling (temp=%.2f, top_p=%.2f)" % (args.temperature, args.top_p) if args.do_sample else "greedy",
             args.max_new_tokens, args.seed, "" if not args.do_sample else ""), flush=True)

    torch.manual_seed(args.seed)
    transformers.set_seed(args.seed)
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        str(base_dir), local_files_only=True
    )
    base_model = transformers.AutoModelForCausalLM.from_pretrained(
        str(base_dir), torch_dtype=torch.bfloat16, local_files_only=True
    )
    model = PeftModel.from_pretrained(base_model, str(adapter_dir))
    model.to(args.device)
    model.eval()
    model.config.use_cache = True
    print("loaded      : %s | base=%s | adapter=%s"
          % (dtype_name(model), base_dir.name, adapter_dir.name), flush=True)

    results: list[dict[str, Any]] = []
    started = time.time()
    for number, row in enumerate(rows, 1):
        prompt = tokenizer.apply_chat_template(
            row["messages"][:2], tokenize=False, add_generation_prompt=True
        )
        encoded = tokenizer(prompt, return_tensors="pt", add_special_tokens=False)
        encoded = {key: value.to(args.device) for key, value in encoded.items()}
        torch.manual_seed(args.seed + number)

        gen_kwargs: dict[str, Any] = {
            "max_new_tokens": args.max_new_tokens,
            "pad_token_id": tokenizer.eos_token_id,
            "eos_token_id": tokenizer.eos_token_id,
        }
        if args.do_sample:
            gen_kwargs["do_sample"] = True
            gen_kwargs["temperature"] = args.temperature
            gen_kwargs["top_p"] = args.top_p
        else:
            gen_kwargs["do_sample"] = False

        with torch.inference_mode():
            generated = model.generate(
                **encoded,
                **gen_kwargs,
            )
        generated = generated[0, encoded["input_ids"].shape[1]:]
        text = tokenizer.decode(
            generated, skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )
        result = score_row(row, text)
        result["generated_tokens"] = int(generated.numel())
        results.append(result)

        preview = result["final_answer_text"].replace("\n", " ")[:60]
        print("[%02d/%02d] %-24s %-6s format=%-5s accuracy=%-5s final='%s'"
              % (number, len(rows), row["id"], row["category"],
                 str(result["valid_think_format"]),
                 str(result["answer_semantic_match"]), preview), flush=True)

    elapsed = round(time.time() - started, 1)

    metrics = {
        key: rate([bool(result[key]) for result in results])
        for key in (
            "valid_think_format",
            "complete_think_block",
            "think_tag_present",
            "plain_text",
            "missing_closing_tag",
            "missing_opening_tag",
            "multiple_think_blocks",
            "extra_text_before_think",
            "empty_reasoning",
            "empty_final_answer",
            "answer_semantic_match",
        )
    }
    format_valid_results = [
        result for result in results if result["valid_think_format"]
    ]
    metrics["answer_semantic_match_when_format_valid"] = rate(
        [bool(result["answer_semantic_match"]) for result in format_valid_results]
    )

    by_category: dict[str, Any] = {}
    for category in CATEGORIES:
        category_results = [
            result for result in results if result["category"] == category
        ]
        by_category[category] = {
            "n": len(category_results),
            "valid_think_format": rate(
                [bool(result["valid_think_format"]) for result in category_results]
            ),
            "complete_think_block": rate(
                [bool(result["complete_think_block"]) for result in category_results]
            ),
            "answer_semantic_match": rate(
                [bool(result["answer_semantic_match"]) for result in category_results]
            ),
        }

    format_rate = metrics["valid_think_format"]
    accuracy = metrics["answer_semantic_match"]
    document = {
        "suite": "phase6-reasoning-eval-v1",
        "model_label": "v2.0-bdw7b-sft-reasoning-lora",
        "base_model_dir": str(base_dir),
        "adapter_dir": str(adapter_dir),
        "eval_file": str(eval_file),
        "eval_sha256": sha256_file(eval_file),
        "n": len(results),
        "decoding": {
            "do_sample": args.do_sample,
            "temperature": args.temperature if args.do_sample else 0.0,
            "top_p": args.top_p if args.do_sample else 1.0,
            "seed": args.seed,
            "max_new_tokens": args.max_new_tokens,
        },
        "metrics": metrics,
        "format_rate": format_rate,
        "accuracy": accuracy,
        "by_category": by_category,
        "environment": {
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "cuda": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0),
        },
        "elapsed_s": elapsed,
        "results": results,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = out_path.with_suffix(out_path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    os.replace(temporary, out_path)

    print("=" * 72)
    print("format rate:", "%d/%d (%.1f%%)" % (
        format_rate["hit"], format_rate["total"], format_rate["percent"]))
    print("accuracy   :", "%d/%d (%.1f%%)" % (
        accuracy["hit"], accuracy["total"], accuracy["percent"]))
    print("by category:")
    for category, values in by_category.items():
        print("  %-6s format=%d/%d accuracy=%d/%d" % (
            category,
            values["valid_think_format"]["hit"],
            values["valid_think_format"]["total"],
            values["answer_semantic_match"]["hit"],
            values["answer_semantic_match"]["total"],
        ))
    print("result     :", out_path)
    print("elapsed    :", elapsed, "s")
    print("RESULT: PHASE6_REASONING_TRAINED_OK n=%d format_hits=%d "
          "format_total=%d format_percent=%.1f accuracy_hits=%d "
          "accuracy_total=%d accuracy_percent=%.1f"
          % (len(results), format_rate["hit"], format_rate["total"],
             format_rate["percent"], accuracy["hit"], accuracy["total"],
             accuracy["percent"]), flush=True)
    return 0


def dtype_name(model: Any) -> str:
    try:
        return str(next(model.parameters()).dtype)
    except StopIteration:
        return "unknown"


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:
        traceback.print_exc()
        print(
            "RESULT: PHASE6_REASONING_TRAINED_FAIL %s" % exc,
            file=sys.stderr,
            flush=True,
        )
        print("RESULT: PHASE6_REASONING_TRAINED_FAIL %s" % exc, flush=True)
        raise SystemExit(1)
