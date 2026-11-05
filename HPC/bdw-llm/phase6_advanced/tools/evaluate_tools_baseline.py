#!/usr/bin/env python3
"""Phase 6 baseline: measure tool-call formatting on v2.0-bdw7b-sft.

The model is the shipped Phase 2 SFT model at merged/bdw-7b-sft. It is loaded
locally with transformers in bf16; no network or new model download is used.

For every row in data/tool_calls_eval.jsonl:
  * build the same Qwen2.5 prompt used for training (system + tools + user),
  * greedy-generate one assistant response,
  * extract <tool_call>...</tool_call> blocks,
  * count valid JSON/tool-call formatting.

Primary metric: Valid Tool Call Format Rate. A response counts only when it
contains exactly one complete <tool_call>...</tool_call> block whose body is a
JSON object with a string "name" and an object "arguments". A secondary
metric accepts valid JSON after an opening tag even when the closing tag is
missing. Plain-text answers are counted separately. Semantic correctness is
reported but is not part of the format metric.

Output: phase6_advanced/tools/eval/tool_baseline_v2_0_bdw7b_sft.json
RESULT: PHASE6_TOOL_BASELINE_OK ... / PHASE6_TOOL_BASELINE_FAIL ...
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import traceback
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
ROOT = TOOLS_DIR.parents[1]
DEFAULT_MODEL = ROOT / "merged" / "bdw-7b-sft"
DEFAULT_EVAL = TOOLS_DIR / "data" / "tool_calls_eval.jsonl"
DEFAULT_OUT = TOOLS_DIR / "eval" / "tool_baseline_v2_0_bdw7b_sft.json"
TOOL_CALL_RE = re.compile(r"<tool_call>\s*(.*?)\s*</tool_call>", re.DOTALL)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_rows(path: Path) -> list:
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def parse_calls(text: str):
    blocks = [m.group(1).strip() for m in TOOL_CALL_RE.finditer(text)]
    parsed, errors = [], []
    for i, block in enumerate(blocks):
        try:
            parsed.append(json.loads(block))
        except Exception as exc:
            errors.append({"index": i, "error": str(exc), "body": block[:500]})
    return blocks, parsed, errors


def parse_open_tag(text: str):
    if "</tool_call>" in text or "<tool_call>" not in text:
        return None, None
    body = text.split("<tool_call>", 1)[1].strip()
    if not body:
        return "", None
    try:
        return body, json.loads(body)
    except Exception:
        return body, None


def call_shape_ok(obj) -> bool:
    return (
        isinstance(obj, dict)
        and isinstance(obj.get("name"), str)
        and isinstance(obj.get("arguments"), dict)
    )


def schema_ok(call, tools) -> bool:
    if not call_shape_ok(call):
        return False
    name = call["name"]
    spec = None
    for tool in tools:
        fn = tool.get("function", {}) if isinstance(tool, dict) else {}
        if fn.get("name") == name:
            spec = fn
            break
    if spec is None:
        return False
    params = spec.get("parameters") or {}
    props = params.get("properties") or {}
    args = call["arguments"]
    for key in params.get("required", []):
        if key not in args:
            return False
    for key, value in args.items():
        prop = props.get(key)
        if prop is None:
            return False
        kind = prop.get("type")
        if kind == "string" and not isinstance(value, str):
            return False
        if kind == "number" and not isinstance(value, (int, float)):
            return False
    return True


def add(metrics, key, value):
    bucket = metrics.setdefault(key, {"hit": 0, "n": 0})
    bucket["n"] += 1
    bucket["hit"] += int(bool(value))


def rate(bucket):
    n = bucket["n"]
    hit = bucket["hit"]
    return {"hit": hit, "n": n,
            "rate": round(hit / n, 4) if n else 0.0,
            "percent": round(100.0 * hit / n, 1) if n else 0.0}


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 6 tool-call baseline")
    ap.add_argument("--model", default=str(DEFAULT_MODEL))
    ap.add_argument("--eval", dest="eval_file", default=str(DEFAULT_EVAL))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--max-new-tokens", type=int, default=192)
    ap.add_argument("--seed", type=int, default=1337)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--limit", type=int, default=0,
                    help="optional smoke-test limit (0 = all 24)")
    args = ap.parse_args()

    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

    import torch
    import transformers

    model_dir = Path(args.model).expanduser().resolve()
    eval_file = Path(args.eval_file).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    if not model_dir.is_dir():
        raise SystemExit("model dir not found: %s" % model_dir)
    if not eval_file.is_file():
        raise SystemExit("eval file not found: %s" % eval_file)

    rows = load_rows(eval_file)
    if args.limit:
        rows = rows[:args.limit]
    if not rows:
        raise SystemExit("no eval rows")
    if len(rows) != 24 and not args.limit:
        print("WARNING: expected 24 eval rows, got %d" % len(rows), flush=True)

    print("=" * 72)
    print("Phase 6 tool-call baseline")
    print("=" * 72)
    print("model_dir   :", model_dir)
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
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        str(model_dir), local_files_only=True)
    model = transformers.AutoModelForCausalLM.from_pretrained(
        str(model_dir), torch_dtype=torch.bfloat16, local_files_only=True)
    model.to(args.device).eval()
    model.config.use_cache = True
    print("loaded      : %s | %s"
          % (model.config._name_or_path, next(model.parameters()).dtype),
          flush=True)

    metrics = {}
    results = []
    t0 = time.time()
    for n, row in enumerate(rows, 1):
        user = row["messages"][1]["content"]
        tools = row.get("tools", [])
        expected = row.get("metadata", {})
        expected_tool = expected.get("tool")
        expected_args = expected.get("expected_arguments")
        prompt = tokenizer.apply_chat_template(
            row["messages"][:2], tools=tools, tokenize=False,
            add_generation_prompt=True)
        enc = tokenizer(prompt, return_tensors="pt", add_special_tokens=False)
        enc = {k: v.to(args.device) for k, v in enc.items()}
        torch.manual_seed(args.seed)
        with torch.inference_mode():
            generated = model.generate(
                **enc, max_new_tokens=args.max_new_tokens,
                do_sample=False, pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id)
        generated = generated[0, enc["input_ids"].shape[1]:]
        text = tokenizer.decode(generated, skip_special_tokens=True,
                                clean_up_tokenization_spaces=False)

        blocks, parsed, errors = parse_calls(text)
        open_body, open_obj = parse_open_tag(text)
        open_shape = call_shape_ok(open_obj)
        has_tag = "<tool_call>" in text or "</tool_call>" in text
        valid_format = (
            len(blocks) == 1 and len(parsed) == 1
            and call_shape_ok(parsed[0])
        )
        json_parse_valid = len(blocks) == 1 and len(parsed) == 1
        json_body_in_tag = (
            (len(parsed) == 1 and call_shape_ok(parsed[0]))
            or (not blocks and open_shape)
        )
        missing_closing_tag = bool(open_body) and not blocks and open_shape
        name_valid = (
            valid_format and parsed[0]["name"] in
            {t.get("function", {}).get("name") for t in tools}
        )
        args_schema_valid = (
            valid_format and schema_ok(parsed[0], tools)
        )
        semantic_match = (
            valid_format and parsed[0]["name"] == expected_tool
            and parsed[0]["arguments"] == expected_args
        )
        plain_text = not has_tag
        malformed = has_tag and not valid_format
        multiple_calls = len(blocks) > 1
        extra_text = bool(TOOL_CALL_RE.sub("", text).strip())
        clean_format = valid_format and not extra_text

        add(metrics, "valid_tool_call_format", valid_format)
        add(metrics, "clean_tool_call_format", clean_format)
        add(metrics, "json_parse_valid", json_parse_valid)
        add(metrics, "json_body_in_tool_call_tag", json_body_in_tag)
        add(metrics, "missing_closing_tag", missing_closing_tag)
        add(metrics, "tool_name_valid", name_valid)
        add(metrics, "arguments_schema_valid", args_schema_valid)
        add(metrics, "exact_semantic_match", semantic_match)
        add(metrics, "plain_text", plain_text)
        add(metrics, "malformed_or_non_json", malformed)
        add(metrics, "multiple_tool_calls", multiple_calls)
        add(metrics, "extra_text_outside_tags", extra_text)

        results.append({
            "id": row.get("id"),
            "user": user,
            "expected_tool": expected_tool,
            "expected_arguments": expected_args,
            "raw_output": text,
            "tool_call_blocks": blocks,
            "parsed_calls": parsed,
            "parse_errors": errors,
            "valid_tool_call_format": valid_format,
            "clean_tool_call_format": clean_format,
            "json_parse_valid": json_parse_valid,
            "json_body_in_tool_call_tag": json_body_in_tag,
            "missing_closing_tag": missing_closing_tag,
            "tool_name_valid": name_valid,
            "arguments_schema_valid": args_schema_valid,
            "exact_semantic_match": semantic_match,
            "plain_text": plain_text,
            "malformed_or_non_json": malformed,
            "multiple_tool_calls": multiple_calls,
            "extra_text_outside_tags": extra_text,
            "output_tokens": int(generated.numel()),
        })
        print("[%02d/%02d] %-16s format=%-5s plain=%-5s raw=%r"
              % (n, len(rows), row.get("id"), valid_format, plain_text,
                 text[:160]), flush=True)

    metrics_out = {k: rate(v) for k, v in metrics.items()}
    primary = metrics_out["valid_tool_call_format"]
    doc = {
        "suite": "phase6-tools-eval-v1",
        "model_label": "v2.0-bdw7b-sft",
        "model_dir": str(model_dir),
        "eval_file": str(eval_file),
        "eval_sha256": sha256_file(eval_file),
        "n": len(results),
        "decoding": {"do_sample": False, "seed": args.seed,
                     "max_new_tokens": args.max_new_tokens},
        "metrics": metrics_out,
        "environment": {
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "cuda": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0),
        },
        "elapsed_s": round(time.time() - t0, 1),
        "prompts": results,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(out_path) + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, out_path)

    print("-" * 72)
    print("Valid Tool Call Format Rate: %d/%d (%.1f%%)"
          % (primary["hit"], primary["n"], primary["percent"]))
    print("  clean (no extra text)   : %d/%d"
          % (metrics_out["clean_tool_call_format"]["hit"],
             metrics_out["clean_tool_call_format"]["n"]))
    print("  JSON parseable          : %d/%d"
          % (metrics_out["json_parse_valid"]["hit"],
             metrics_out["json_parse_valid"]["n"]))
    print("  JSON body in tag         : %d/%d"
          % (metrics_out["json_body_in_tool_call_tag"]["hit"],
             metrics_out["json_body_in_tool_call_tag"]["n"]))
    print("  missing closing tag      : %d/%d"
          % (metrics_out["missing_closing_tag"]["hit"],
             metrics_out["missing_closing_tag"]["n"]))
    print("  valid tool name         : %d/%d"
          % (metrics_out["tool_name_valid"]["hit"],
             metrics_out["tool_name_valid"]["n"]))
    print("  valid argument schema   : %d/%d"
          % (metrics_out["arguments_schema_valid"]["hit"],
             metrics_out["arguments_schema_valid"]["n"]))
    print("  exact semantic match    : %d/%d"
          % (metrics_out["exact_semantic_match"]["hit"],
             metrics_out["exact_semantic_match"]["n"]))
    print("  plain text / no tags    : %d/%d"
          % (metrics_out["plain_text"]["hit"],
             metrics_out["plain_text"]["n"]))
    print("  malformed / non-JSON    : %d/%d"
          % (metrics_out["malformed_or_non_json"]["hit"],
             metrics_out["malformed_or_non_json"]["n"]))
    print("  multiple tool calls     : %d/%d"
          % (metrics_out["multiple_tool_calls"]["hit"],
             metrics_out["multiple_tool_calls"]["n"]))
    print("wrote %s (%d B)" % (out_path, out_path.stat().st_size))
    print("RESULT: PHASE6_TOOL_BASELINE_OK valid_format=%d/%d rate=%.4f "
          "json_body=%d missing_close=%d plain_text=%d malformed=%d elapsed=%.0fs"
          % (primary["hit"], primary["n"], primary["rate"],
             metrics_out["json_body_in_tool_call_tag"]["hit"],
             metrics_out["missing_closing_tag"]["hit"],
             metrics_out["plain_text"]["hit"],
             metrics_out["malformed_or_non_json"]["hit"],
             doc["elapsed_s"]), flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        print("RESULT: PHASE6_TOOL_BASELINE_FAIL %s"
              % sys.exc_info()[1], flush=True)
        raise SystemExit(1)
