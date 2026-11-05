#!/usr/bin/env python3
"""Phase 6 post-SFT: evaluate v2.0-bdw7b-sft plus the P6 tool LoRA adapter."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import traceback
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
ROOT = TOOLS_DIR.parents[1]
DEFAULT_BASE = ROOT / "merged" / "bdw-7b-sft"
DEFAULT_ADAPTER = ROOT / "lora_tools" / "p6_tool_calling" / "final"
DEFAULT_EVAL = TOOLS_DIR / "data" / "tool_calls_eval.jsonl"
DEFAULT_BASELINE = TOOLS_DIR / "eval" / "tool_baseline_v2_0_bdw7b_sft.json"
DEFAULT_OUT = TOOLS_DIR / "eval" / "tool_trained_v2_0_bdw7b_sft_lora_p6.json"

from evaluate_tools_baseline import (  # noqa: E402
    TOOL_CALL_RE,
    add,
    call_shape_ok,
    load_rows,
    parse_calls,
    parse_open_tag,
    rate,
    schema_ok,
    sha256_file,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate the Phase 6 LoRA adapter on held-out tool calls."
    )
    parser.add_argument("--base", default=str(DEFAULT_BASE))
    parser.add_argument("--adapter", default=str(DEFAULT_ADAPTER))
    parser.add_argument("--eval", dest="eval_file", default=str(DEFAULT_EVAL))
    parser.add_argument("--baseline", default=str(DEFAULT_BASELINE))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--max-new-tokens", type=int, default=192)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--limit", type=int, default=0)
    return parser.parse_args()


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    args = parse_args()
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

    import torch
    import transformers
    from peft import PeftModel

    base_dir = Path(args.base).expanduser().resolve()
    adapter_dir = Path(args.adapter).expanduser().resolve()
    eval_file = Path(args.eval_file).expanduser().resolve()
    baseline_path = Path(args.baseline).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()

    for path, label in (
        (base_dir, "base model"),
        (adapter_dir, "adapter"),
        (eval_file, "eval file"),
        (baseline_path, "baseline result"),
    ):
        if not path.exists():
            raise SystemExit("%s not found: %s" % (label, path))

    rows = load_rows(eval_file)
    if args.limit:
        rows = rows[: args.limit]
    if not rows:
        raise SystemExit("no eval rows")
    if len(rows) != 24 and not args.limit:
        print("WARNING: expected 24 eval rows, got %d" % len(rows), flush=True)

    baseline = load_json(baseline_path)
    baseline_metric = baseline["metrics"]["valid_tool_call_format"]
    adapter_file = adapter_dir / "adapter_model.safetensors"
    metadata_file = adapter_dir / "training_metadata.json"
    training_metadata = load_json(metadata_file) if metadata_file.is_file() else {}

    print("=" * 72)
    print("Phase 6 tool-call post-SFT evaluation")
    print("=" * 72)
    print("base_dir    :", base_dir)
    print("adapter_dir :", adapter_dir)
    print("adapter_sha :", sha256_file(adapter_file))
    print("eval_file   :", eval_file)
    print("eval_sha256 :", sha256_file(eval_file))
    print("baseline    :", baseline_path)
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
        str(base_dir), local_files_only=True
    )
    base_model = transformers.AutoModelForCausalLM.from_pretrained(
        str(base_dir), torch_dtype=torch.bfloat16, local_files_only=True
    )
    model = PeftModel.from_pretrained(base_model, str(adapter_dir))
    model.to(args.device)
    model.eval()
    model.config.use_cache = True
    dtype = next(model.parameters()).dtype
    print("loaded      : base + LoRA | %s | adapter=%s"
          % (dtype, adapter_dir.name), flush=True)

    metrics = {}
    results = []
    started = time.time()
    for number, row in enumerate(rows, 1):
        user = row["messages"][1]["content"]
        tools = row.get("tools", [])
        expected = row.get("metadata", {})
        expected_tool = expected.get("tool")
        expected_args = expected.get("expected_arguments")
        prompt = tokenizer.apply_chat_template(
            row["messages"][:2], tools=tools, tokenize=False,
            add_generation_prompt=True
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
            clean_up_tokenization_spaces=False
        )

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
            {tool.get("function", {}).get("name") for tool in tools}
        )
        args_schema_valid = valid_format and schema_ok(parsed[0], tools)
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
              % (number, len(rows), row.get("id"), valid_format, plain_text,
                 text[:160]), flush=True)

    metrics_out = {key: rate(bucket) for key, bucket in metrics.items()}
    primary = metrics_out["valid_tool_call_format"]
    delta_hits = primary["hit"] - baseline_metric["hit"]
    delta_points = round(primary["percent"] - baseline_metric["percent"], 1)
    doc = {
        "suite": "phase6-tools-eval-v1",
        "model_label": "v2.0-bdw7b-sft+p6-tool-lora",
        "base_model_dir": str(base_dir),
        "adapter_dir": str(adapter_dir),
        "adapter_sha256": sha256_file(adapter_file),
        "adapter_training": {
            key: training_metadata.get(key)
            for key in ("result", "global_step", "train_loss", "eval_loss",
                        "elapsed_s", "train_rows", "dataset_sha256")
        },
        "eval_file": str(eval_file),
        "eval_sha256": sha256_file(eval_file),
        "n": len(results),
        "decoding": {
            "do_sample": False,
            "seed": args.seed,
            "max_new_tokens": args.max_new_tokens,
        },
        "metrics": metrics_out,
        "environment": {
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "cuda": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0),
        },
        "baseline": {
            "path": str(baseline_path),
            "sha256": sha256_file(baseline_path),
            "valid_tool_call_format": baseline_metric,
        },
        "comparison": {
            "valid_tool_call_delta_hits": delta_hits,
            "valid_tool_call_delta_points": delta_points,
            "previous_percent": baseline_metric["percent"],
            "current_percent": primary["percent"],
        },
        "elapsed_s": round(time.time() - started, 1),
        "prompts": results,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(str(out_path) + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(doc, handle, ensure_ascii=False, indent=2)
    os.replace(temporary, out_path)

    print("-" * 72)
    print("Valid Tool Call Format Rate: %d/%d (%.1f%%)"
          % (primary["hit"], primary["n"], primary["percent"]))
    print("  baseline                : %d/%d (%.1f%%)"
          % (baseline_metric["hit"], baseline_metric["n"],
             baseline_metric["percent"]))
    print("  delta                   : %+d hits / %+.1f points"
          % (delta_hits, delta_points))
    print("  clean (no extra text)   : %d/%d"
          % (metrics_out["clean_tool_call_format"]["hit"],
             metrics_out["clean_tool_call_format"]["n"]))
    print("  JSON parseable          : %d/%d"
          % (metrics_out["json_parse_valid"]["hit"],
             metrics_out["json_parse_valid"]["n"]))
    print("  JSON body in tag        : %d/%d"
          % (metrics_out["json_body_in_tool_call_tag"]["hit"],
             metrics_out["json_body_in_tool_call_tag"]["n"]))
    print("  missing closing tag     : %d/%d"
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
    print("RESULT: PHASE6_TOOL_TRAINED_OK valid_format=%d/%d rate=%.4f "
          "baseline=%d/%d baseline_rate=%.4f delta_points=%+.1f "
          "missing_close=%d plain_text=%d malformed=%d elapsed=%.0fs"
          % (primary["hit"], primary["n"], primary["rate"],
             baseline_metric["hit"], baseline_metric["n"],
             baseline_metric["rate"], delta_points,
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
        print("RESULT: PHASE6_TOOL_TRAINED_FAIL %s" % sys.exc_info()[1],
              flush=True)
        raise SystemExit(1)
