#!/usr/bin/env python3
"""Phase 6 baseline: evaluate v2.0-bdw7b-sft on held-out reasoning prompts."""
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
DEFAULT_EVAL = HERE / "data" / "reasoning_eval.jsonl"
DEFAULT_OUT = HERE / "eval" / "reasoning_baseline_v2_0_bdw7b_sft.json"
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
        "percent": round(100.0 * hits / total, 1) if total else 0.0,
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
    return float(matches[-1]) if matches else None


def logic_order(text: str, names: list[str]) -> list[str] | None:
    matches: list[tuple[int, str]] = []
    for name in names:
        matches.extend(
            (match.start(), name)
            for match in re.finditer(r"\b%s\b" % re.escape(name), text)
        )
    matches.sort()
    sequence: list[str] = []
    for _, name in matches:
        if not sequence or sequence[-1] != name:
            sequence.append(name)
    if len(sequence) == 5 and set(sequence) == set(names):
        return sequence
    windows = [
        sequence[index:index + 5]
        for index in range(max(0, len(sequence) - 4))
        if len(set(sequence[index:index + 5])) == 5
        and set(sequence[index:index + 5]) == set(names)
    ]
    return windows[-1] if windows else None


def extract_code(text: str, function_name: str) -> str | None:
    for block in reversed(CODE_FENCE_RE.findall(text)):
        if re.search(
            r"^\s*def\s+%s\s*\(" % re.escape(function_name), block, re.M
        ):
            return block.strip()
    match = re.search(
        r"(?ms)^\s*def\s+%s\s*\(.*" % re.escape(function_name), text
    )
    return match.group(0).strip() if match else None


def run_candidate_code(
    code: str, function_name: str, sample_input: Any
) -> tuple[Any, str | None]:
    arguments = [
        sys.executable, "-I", "-c", CODE_WRAPPER, code, function_name,
        json.dumps(sample_input, ensure_ascii=False),
        json.dumps(SAFE_BUILTIN_NAMES),
    ]
    try:
        completed = subprocess.run(
            arguments, capture_output=True, text=True, timeout=5,
            cwd=tempfile.gettempdir(),
            env={"PYTHONIOENCODING": "utf-8",
                 "PATH": os.environ.get("PATH", "")},
        )
    except subprocess.TimeoutExpired:
        return None, "TimeoutExpired"
    for line in reversed(completed.stdout.splitlines()):
        if line.startswith("__RESULT__"):
            try:
                return json.loads(line[len("__RESULT__"):]), None
            except json.JSONDecodeError as error:
                return None, "Invalid result JSON: %s" % error
        if line.startswith("__ERROR__"):
            return None, line[len("__ERROR__"):]
    detail = completed.stderr.strip() or "missing result marker"
    return None, detail[-500:]


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
        raise ValueError("unknown category: %s" % row["category"])

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
    parser.add_argument("--base", default=str(DEFAULT_BASE))
    parser.add_argument("--eval", dest="eval_file", default=str(DEFAULT_EVAL))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--max-new-tokens", type=int, default=384)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--limit", type=int, default=0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    import torch
    import transformers

    base_dir = Path(args.base).expanduser().resolve()
    eval_file = Path(args.eval_file).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    for path, label in ((base_dir, "base model"), (eval_file, "eval file")):
        if not path.exists():
            raise SystemExit("%s not found: %s" % (label, path))

    rows = load_rows(eval_file)
    if args.limit:
        rows = rows[: args.limit]
    if not rows:
        raise SystemExit("no eval rows")
    if len(rows) != 24 and not args.limit:
        print("WARNING: expected 24 eval rows, got %d" % len(rows), flush=True)

    print("=" * 72)
    print("Phase 6 reasoning baseline evaluation")
    print("=" * 72)
    print("base_dir    :", base_dir)
    print("eval_file   :", eval_file)
    print("eval_sha256 :", sha256_file(eval_file))
    print("rows        :", len(rows))
    print("torch       :", torch.__version__)
    print("transformers:", transformers.__version__)
    print("cuda        :", torch.cuda.is_available())
    if not torch.cuda.is_available():
        raise SystemExit("CUDA is not available in this job")
    print("gpu         :", torch.cuda.get_device_name(0))
    print("decoding    : greedy, max_new_tokens=%d, seed=%d"
          % (args.max_new_tokens, args.seed), flush=True)

    torch.manual_seed(args.seed)
    transformers.set_seed(args.seed)
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        str(base_dir), local_files_only=True
    )
    model = transformers.AutoModelForCausalLM.from_pretrained(
        str(base_dir), torch_dtype=torch.bfloat16, local_files_only=True
    )
    model.to(args.device)
    model.eval()
    model.config.use_cache = True
    print("loaded      : %s | %s"
          % (dtype_name(model), base_dir.name), flush=True)

    results: list[dict[str, Any]] = []
    started = time.time()
    for number, row in enumerate(rows, 1):
        prompt = tokenizer.apply_chat_template(
            row["messages"][:2], tokenize=False, add_generation_prompt=True
        )
        encoded = tokenizer(prompt, return_tensors="pt", add_special_tokens=False)
        encoded = {key: value.to(args.device) for key, value in encoded.items()}
        torch.manual_seed(args.seed)
        with torch.inference_mode():
            generated = model.generate(
                **encoded,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
        generated = generated[0, encoded["input_ids"].shape[1]:]
        text = tokenizer.decode(
            generated, skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )
        result = score_row(row, text)
        result["generated_tokens"] = int(generated.numel())
        results.append(result)
        print("[%02d/%02d] %-24s %-6s format=%-5s accuracy=%-5s final=%r"
              % (number, len(rows), row.get("id"), row["category"],
                 result["valid_think_format"],
                 result["answer_semantic_match"],
                 result["final_answer_text"][:120]), flush=True)

    format_rate = rate([row["valid_think_format"] for row in results])
    accuracy = rate([row["answer_semantic_match"] for row in results])
    valid_rows = [row for row in results if row["valid_think_format"]]
    conditional_accuracy = rate(
        [row["answer_semantic_match"] for row in valid_rows]
    )
    metrics = {
        "valid_think_format": format_rate,
        "complete_think_block": rate(
            [row["complete_think_block"] for row in results]
        ),
        "think_tag_present": rate(
            [row["think_tag_present"] for row in results]
        ),
        "plain_text": rate([row["plain_text"] for row in results]),
        "missing_closing_tag": rate(
            [row["missing_closing_tag"] for row in results]
        ),
        "missing_opening_tag": rate(
            [row["missing_opening_tag"] for row in results]
        ),
        "multiple_think_blocks": rate(
            [row["multiple_think_blocks"] for row in results]
        ),
        "extra_text_before_think": rate(
            [row["extra_text_before_think"] for row in results]
        ),
        "empty_reasoning": rate([row["empty_reasoning"] for row in results]),
        "empty_final_answer": rate(
            [row["empty_final_answer"] for row in results]
        ),
        "answer_semantic_match": accuracy,
        "answer_semantic_match_when_format_valid": conditional_accuracy,
    }
    by_category: dict[str, Any] = {}
    for category in CATEGORIES:
        category_rows = [row for row in results if row["category"] == category]
        by_category[category] = {
            "n": len(category_rows),
            "valid_think_format": rate(
                [row["valid_think_format"] for row in category_rows]
            ),
            "complete_think_block": rate(
                [row["complete_think_block"] for row in category_rows]
            ),
            "answer_semantic_match": rate(
                [row["answer_semantic_match"] for row in category_rows]
            ),
        }

    elapsed = round(time.time() - started, 1)
    document = {
        "suite": "phase6-reasoning-eval-v1",
        "model_label": "v2.0-bdw7b-sft",
        "base_model_dir": str(base_dir),
        "eval_file": str(eval_file),
        "eval_sha256": sha256_file(eval_file),
        "n": len(results),
        "decoding": {
            "do_sample": False,
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
    print("RESULT: PHASE6_REASONING_BASELINE_OK n=%d format_hits=%d "
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
    except Exception:
        traceback.print_exc()
        print("RESULT: PHASE6_REASONING_BASELINE_FAIL %s" % sys.exc_info()[1],
              flush=True)
        raise SystemExit(1)
