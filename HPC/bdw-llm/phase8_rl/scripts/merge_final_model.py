#!/usr/bin/env python3
"""Merge the Phase 7 SFT and Phase 8 DPO LoRA adapters into one full model."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
import traceback
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEFAULT_BASE = ROOT / "merged" / "bdw-7b-sft"
DEFAULT_P7 = ROOT / "lora_combined" / "p7_combined" / "final"
DEFAULT_P8 = ROOT / "lora_dpo" / "p8_dpo_retune" / "final"
DEFAULT_OUT = ROOT / "merged" / "bdw7b-reasoning-dpo-final"
MIN_FREE_BYTES = 35 * 1024**3
DTYPES = ("bfloat16", "float16", "float32")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge Phase 7 SFT and Phase 8 DPO adapters into a full model."
    )
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--p7-adapter", type=Path, default=DEFAULT_P7)
    parser.add_argument("--p8-adapter", type=Path, default=DEFAULT_P8)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--dtype", choices=DTYPES, default="bfloat16")
    parser.add_argument("--max-shard-size", default="5GB")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def adapter_weights(path: Path) -> Path | None:
    for name in ("adapter_model.safetensors", "adapter_model.bin"):
        candidate = path / name
        if candidate.is_file():
            return candidate
    return None


def check_preflight(
    base: Path, p7: Path, p8: Path, out: Path, overwrite: bool
) -> tuple[list[str], list[dict[str, Any]]]:
    from peft import PeftConfig
    from transformers import AutoConfig, AutoTokenizer

    errors: list[str] = []
    details: list[dict[str, Any]] = []

    if not base.is_dir():
        errors.append(f"base model directory not found: {base}")
    else:
        if not (base / "config.json").is_file():
            errors.append(f"base config.json missing: {base}")
        weight_files = list(base.glob("*.safetensors")) + list(base.glob("*.bin"))
        if not weight_files:
            errors.append(f"base model weights missing: {base}")
        try:
            base_config = AutoConfig.from_pretrained(str(base), local_files_only=True)
            details.append({
                "kind": "base_config",
                "model_type": getattr(base_config, "model_type", None),
                "architectures": getattr(base_config, "architectures", None),
                "hidden_size": getattr(base_config, "hidden_size", None),
                "num_hidden_layers": getattr(base_config, "num_hidden_layers", None),
            })
        except Exception as error:
            errors.append(f"cannot load base config: {error}")
        try:
            AutoTokenizer.from_pretrained(str(base), local_files_only=True)
            details.append({"kind": "tokenizer", "status": "ok"})
        except Exception as error:
            errors.append(f"cannot load base tokenizer: {error}")

    for label, path in (("Phase 7 SFT", p7), ("Phase 8 DPO", p8)):
        if not path.is_dir():
            errors.append(f"{label} adapter directory not found: {path}")
            continue
        config_path = path / "adapter_config.json"
        weights_path = adapter_weights(path)
        if not config_path.is_file():
            errors.append(f"{label} adapter_config.json missing: {config_path}")
        if weights_path is None:
            errors.append(f"{label} adapter weights missing: {path}")
        try:
            config = PeftConfig.from_pretrained(str(path))
        except Exception as error:
            errors.append(f"cannot load {label} adapter config: {error}")
            continue
        target_modules = getattr(config, "target_modules", None)
        if getattr(config, "peft_type", None) != "LORA":
            errors.append(f"{label} is not a LoRA adapter: {config.peft_type}")
        if getattr(config, "task_type", None) != "CAUSAL_LM":
            errors.append(f"{label} task_type is not CAUSAL_LM: {config.task_type}")
        if not target_modules:
            errors.append(f"{label} has no target_modules")
        if not getattr(config, "r", 0) or not getattr(config, "lora_alpha", 0):
            errors.append(f"{label} has invalid r/lora_alpha")
        if getattr(config, "use_dora", False):
            errors.append(f"{label} uses DoRA; this merge path only supports standard LoRA")
        if getattr(config, "base_model_name_or_path", None):
            configured_base = Path(config.base_model_name_or_path).expanduser()
            if configured_base.exists() and configured_base.resolve() != base:
                details.append({
                    "kind": f"{label}_base_mismatch",
                    "configured": str(configured_base),
                    "actual": str(base),
                })
        if weights_path is not None:
            try:
                from safetensors import safe_open

                if weights_path.suffix == ".safetensors":
                    with safe_open(str(weights_path), framework="pt", device="cpu") as handle:
                        keys = list(handle.keys())
                    if not any("lora_A" in key for key in keys):
                        errors.append(f"{label} safetensors has no LoRA A weights")
                    if not any("lora_B" in key for key in keys):
                        errors.append(f"{label} safetensors has no LoRA B weights")
            except Exception as error:
                errors.append(f"cannot inspect {label} adapter weights: {error}")
        details.append({
            "kind": label,
            "path": str(path),
            "r": getattr(config, "r", None),
            "lora_alpha": getattr(config, "lora_alpha", None),
            "target_modules": target_modules,
            "base_model_name_or_path": getattr(config, "base_model_name_or_path", None),
            "weights": str(weights_path) if weights_path else None,
            "weights_bytes": weights_path.stat().st_size if weights_path else None,
            "weights_sha256": sha256_file(weights_path) if weights_path else None,
        })

    if out.exists():
        if not overwrite:
            errors.append(f"output already exists (use --overwrite): {out}")
        elif not out.is_dir():
            errors.append(f"output exists and is not a directory: {out}")
    probe = out.parent
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    if not probe.exists() or not os.access(probe, os.W_OK):
        errors.append(f"output parent is not writable: {out.parent}")
    else:
        free = shutil.disk_usage(probe).free
        if free < MIN_FREE_BYTES:
            errors.append(
                f"insufficient free space at {probe}: {free / 1024**3:.1f} GiB "
                f"(need at least {MIN_FREE_BYTES / 1024**3:.0f} GiB)"
            )
    details.append({"kind": "output", "path": str(out), "exists": out.exists()})
    return errors, details


def merge_adapter(model: Any, adapter: Path, label: str) -> Any:
    from peft import PeftModel

    print(f"Applying {label}: {adapter}", flush=True)
    peft_model = PeftModel.from_pretrained(
        model, str(adapter), is_trainable=False
    )
    merged = peft_model.merge_and_unload(progressbar=True, safe_merge=True)
    print(f"Merged {label}; type={type(merged).__name__}", flush=True)
    return merged


def write_manifest(path: Path, args: argparse.Namespace, details: list[dict[str, Any]]) -> None:
    manifest = {
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "method": "sequential PEFT LoRA merge_and_unload",
        "base_model": str(args.base),
        "p7_adapter": str(args.p7_adapter),
        "p8_adapter": str(args.p8_adapter),
        "output": str(args.out),
        "dtype": args.dtype,
        "max_shard_size": args.max_shard_size,
        "checks": details,
    }
    (path / "merge_manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8"
    )


def main() -> int:
    args = parse_args()
    base = args.base.expanduser().resolve()
    p7 = args.p7_adapter.expanduser().resolve()
    p8 = args.p8_adapter.expanduser().resolve()
    out = args.out.expanduser().resolve()
    args.base, args.p7_adapter, args.p8_adapter, args.out = base, p7, p8, out

    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    print("=" * 72)
    print("Phase 8 final merge: base + Phase 7 SFT + Phase 8 DPO")
    print("=" * 72)
    print("base       :", base)
    print("p7 adapter :", p7)
    print("p8 adapter :", p8)
    print("output     :", out)
    print("dtype      :", args.dtype)
    print("mode       :", "check-only" if args.check_only else "merge", flush=True)

    errors, details = check_preflight(base, p7, p8, out, args.overwrite)
    for detail in details:
        print("CHECK:", json.dumps(detail, sort_keys=True, default=str), flush=True)
    if errors:
        for error in errors:
            print("CHECK_FAIL:", error, flush=True)
        print("RESULT: PHASE8_MERGE_FINAL_CHECK_FAIL", flush=True)
        return 1
    print("RESULT: PHASE8_MERGE_FINAL_CHECK_OK", flush=True)
    if args.check_only:
        return 0

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.set_num_threads(max(1, int(os.environ.get("SLURM_CPUS_PER_TASK", "4"))))
    dtype = getattr(torch, args.dtype)
    tokenizer = AutoTokenizer.from_pretrained(str(base), local_files_only=True)
    print("Loading base model on CPU...", flush=True)
    model = AutoModelForCausalLM.from_pretrained(
        str(base),
        torch_dtype=dtype,
        local_files_only=True,
        low_cpu_mem_usage=True,
    )
    model.eval()
    model.config.use_cache = True
    model = merge_adapter(model, p7, "Phase 7 SFT")
    model = merge_adapter(model, p8, "Phase 8 DPO")
    model.eval()

    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(f".{out.name}.tmp.{os.getpid()}")
    if tmp.exists():
        shutil.rmtree(tmp)
    print(f"Saving merged model to {tmp}...", flush=True)
    model.save_pretrained(
        str(tmp),
        safe_serialization=True,
        max_shard_size=args.max_shard_size,
    )
    tokenizer.save_pretrained(str(tmp))
    write_manifest(tmp, args, details)

    required = [tmp / "config.json", tmp / "tokenizer_config.json"]
    missing = [str(path) for path in required if not path.is_file()]
    if missing or not list(tmp.glob("*.safetensors")):
        raise RuntimeError(f"incomplete merge output; missing={missing}")

    backup: Path | None = None
    if out.exists():
        if not args.overwrite:
            raise RuntimeError(f"output already exists: {out}")
        backup = out.with_name(f".{out.name}.bak.{int(time.time())}")
        out.rename(backup)
    try:
        tmp.rename(out)
    except Exception:
        if backup is not None and not out.exists():
            backup.rename(out)
        raise
    if backup is not None:
        shutil.rmtree(backup, ignore_errors=True)

    size = sum(path.stat().st_size for path in out.iterdir() if path.is_file())
    print(f"Merged model ready: {out} ({size / 1024**3:.2f} GiB)", flush=True)
    print(f"RESULT: PHASE8_MERGE_FINAL_OK output={out}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        print("RESULT: PHASE8_MERGE_FINAL_FAIL", flush=True)
        raise SystemExit(1)
