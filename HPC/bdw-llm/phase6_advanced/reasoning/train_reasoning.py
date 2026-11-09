#!/usr/bin/env python
"""Phase 6 LoRA SFT for Qwen2.5 reasoning (<think> tags) on v2.0-bdw7b-sft."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
from datasets import Dataset
from peft import LoraConfig, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)

REASONING_DIR = Path(__file__).resolve().parent
ROOT = REASONING_DIR.parents[1]
BASE_DIR = ROOT / "merged" / "bdw-7b-sft"
TRAIN_FILE = REASONING_DIR / "data" / "reasoning_train.jsonl"
EVAL_FILE = REASONING_DIR / "data" / "reasoning_eval.jsonl"
RUN_DIR = ROOT / "sft_runs" / "p6_reasoning"
ADAPTER_DIR = ROOT / "lora_reasoning" / "p6_reasoning" / "final"
TARGET_MODULES = [
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="LoRA SFT for the Phase 6 reasoning task."
    )
    parser.add_argument("--base", type=Path, default=BASE_DIR, help="Base model directory")
    parser.add_argument("--data", type=Path, default=TRAIN_FILE, help="Training JSONL dataset")
    parser.add_argument("--eval-data", type=Path, default=EVAL_FILE, help="Evaluation JSONL dataset")
    parser.add_argument("--run-dir", type=Path, default=RUN_DIR, help="Checkpoint run output directory")
    parser.add_argument("--adapter-dir", type=Path, default=ADAPTER_DIR, help="Final adapter output directory")
    parser.add_argument("--max-seq-len", type=int, default=768, help="Maximum sequence length")
    parser.add_argument("--epochs", type=float, default=3.0, help="Number of training epochs")
    parser.add_argument("--max-steps", type=int, default=0, help="Override steps limit if > 0")
    parser.add_argument("--batch-size", type=int, default=4, help="Per-device train batch size")
    parser.add_argument("--grad-accum", type=int, default=1, help="Gradient accumulation steps")
    parser.add_argument("--eval-batch-size", type=int, default=4, help="Per-device eval batch size")
    parser.add_argument("--lr", "--learning-rate", dest="lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--lora-r", type=int, default=16, help="LoRA rank")
    parser.add_argument("--lora-alpha", type=int, default=32, help="LoRA alpha scaling factor")
    parser.add_argument("--lora-dropout", type=float, default=0.05, help="LoRA dropout rate")
    parser.add_argument("--seed", type=int, default=1337, help="Random seed")
    parser.add_argument("--tag", default="p6_reasoning", help="Trainer run tag")
    parser.add_argument("--resume", default="", help="Resume checkpoint (path, 'auto', or 'latest')")
    parser.add_argument("--limit-train", type=int, default=0, help="Optional limit on training rows")
    parser.add_argument("--limit-eval", type=int, default=0, help="Optional limit on eval rows")
    parser.add_argument("--check-only", action="store_true", help="Tokenize and validate dataset without training")
    parser.add_argument("--no-eval", action="store_true", help="Disable evaluation during training")
    return parser.parse_args()


def read_jsonl(path: Path, limit: int = 0) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"Dataset file does not exist: {path}")
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
            if not isinstance(row.get("messages"), list):
                raise ValueError(f"{path}:{line_no}: missing 'messages' list")
            if "tools" in row and not isinstance(row.get("tools"), list):
                raise ValueError(f"{path}:{line_no}: invalid 'tools' list")
            rows.append(row)
    if limit > 0:
        rows = rows[:limit]
    if not rows:
        raise ValueError(f"{path}: no rows loaded")
    return rows


def token_ids(tokenizer: Any, text: str) -> list[int]:
    return tokenizer(text, add_special_tokens=False)["input_ids"]


def render(tokenizer: Any, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None) -> str:
    kwargs: dict[str, Any] = {}
    if tools:
        kwargs["tools"] = tools
    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False,
        **kwargs,
    )


def encode_row(tokenizer: Any, row: dict[str, Any], max_len: int) -> dict[str, list[int]]:
    messages = row["messages"]
    tools = row.get("tools")
    full_text = render(tokenizer, messages, tools)
    full_ids = token_ids(tokenizer, full_text)
    if len(full_ids) > max_len:
        raise ValueError(
            f"{row.get('id')}: sequence {len(full_ids)} exceeds --max-seq-len {max_len}"
        )
    labels = [-100] * len(full_ids)
    for index, message in enumerate(messages):
        if message.get("role") != "assistant":
            continue
        before_text = render(tokenizer, messages[:index], tools)
        through_text = render(tokenizer, messages[: index + 1], tools)
        header_text = before_text + "<|im_start|>assistant\n"
        if not full_text.startswith(through_text):
            raise ValueError(f"{row.get('id')}: rendered prefix is not stable")
        if not through_text.startswith(header_text):
            raise ValueError(f"{row.get('id')}: assistant header mismatch")
        before_ids = token_ids(tokenizer, before_text)
        through_ids = token_ids(tokenizer, through_text)
        header_ids = token_ids(tokenizer, header_text)
        if full_ids[: len(before_ids)] != before_ids:
            raise ValueError(f"{row.get('id')}: token prefix mismatch")
        if full_ids[: len(through_ids)] != through_ids:
            raise ValueError(f"{row.get('id')}: token suffix mismatch")
        if full_ids[: len(header_ids)] != header_ids:
            raise ValueError(f"{row.get('id')}: assistant header token mismatch")
        start = len(header_ids)
        end = len(through_ids)
        if start >= end:
            raise ValueError(f"{row.get('id')}: empty assistant target")
        labels[start:end] = full_ids[start:end]
    if all(label == -100 for label in labels):
        raise ValueError(f"{row.get('id')}: no assistant tokens to train")
    return {
        "input_ids": full_ids,
        "attention_mask": [1] * len(full_ids),
        "labels": labels,
    }


def dataset_stats(rows: list[dict[str, Any]], records: list[dict[str, list[int]]]) -> dict[str, Any]:
    seq_lengths = [len(record["input_ids"]) for record in records]
    label_lengths = [
        sum(1 for label in record["labels"] if label != -100) for record in records
    ]
    modes: dict[str, int] = {}
    for row in rows:
        mode = str(row.get("category", row.get("metadata", {}).get("mode", "unknown")))
        modes[mode] = modes.get(mode, 0) + 1
    return {
        "rows": len(records),
        "seq_min": min(seq_lengths),
        "seq_mean": sum(seq_lengths) / len(seq_lengths),
        "seq_max": max(seq_lengths),
        "label_min": min(label_lengths),
        "label_mean": sum(label_lengths) / len(label_lengths),
        "label_max": max(label_lengths),
        "modes": modes,
    }


def make_dataset(
    tokenizer: Any,
    rows: list[dict[str, Any]],
    max_len: int,
) -> tuple[Dataset, dict[str, Any]]:
    records = [encode_row(tokenizer, row, max_len) for row in rows]
    return Dataset.from_list(records), dataset_stats(rows, records)


@dataclass
class CausalCollator:
    pad_token_id: int

    def __call__(self, features: list[dict[str, Any]]) -> dict[str, torch.Tensor]:
        max_len = max(len(feature["input_ids"]) for feature in features)
        input_ids: list[list[int]] = []
        attention_mask: list[list[int]] = []
        labels: list[list[int]] = []
        for feature in features:
            length = len(feature["input_ids"])
            pad = max_len - length
            input_ids.append(feature["input_ids"] + [self.pad_token_id] * pad)
            attention_mask.append(feature["attention_mask"] + [0] * pad)
            labels.append(feature["labels"] + [-100] * pad)
        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
        }


def resolve_resume(run_dir: Path, resume: str) -> str | None:
    if not resume:
        return None
    if resume not in {"latest", "auto"}:
        return resume
    checkpoints = [
        path
        for path in run_dir.glob("checkpoint-*")
        if path.is_dir() and path.name.rsplit("-", 1)[-1].isdigit()
    ]
    if not checkpoints:
        raise ValueError(f"No checkpoint found under {run_dir} to resume from")
    return str(max(checkpoints, key=lambda path: int(path.name.rsplit("-", 1)[-1])))


def last_metric(history: list[dict[str, Any]], key: str) -> float | None:
    for entry in reversed(history):
        if key in entry:
            return float(entry[key])
    return None


def json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(temporary, path)


def main() -> None:
    args = parse_args()
    started = time.time()
    if args.max_seq_len < 1:
        raise ValueError("--max-seq-len must be positive")
    if args.epochs <= 0 and args.max_steps <= 0:
        raise ValueError("Set --epochs > 0 or --max-steps > 0")

    base_dir = Path(args.base).expanduser().resolve()
    train_file = Path(args.data).expanduser().resolve()
    eval_file = Path(args.eval_data).expanduser().resolve()

    # Preflight checks
    if not base_dir.is_dir():
        raise FileNotFoundError(f"Base model directory does not exist: {base_dir}")
    if not train_file.is_file():
        raise FileNotFoundError(f"Training dataset does not exist: {train_file}")
    if not args.no_eval and not eval_file.is_file():
        raise FileNotFoundError(f"Evaluation dataset does not exist: {eval_file}")

    print("=" * 72)
    print("Phase 6 Reasoning LoRA SFT")
    print("=" * 72)
    print("base_dir    :", base_dir)
    print("train_file  :", train_file)
    print("eval_file   :", eval_file if not args.no_eval else "disabled")
    print("adapter_dir :", args.adapter_dir)
    print("run_dir     :", args.run_dir)

    tokenizer = AutoTokenizer.from_pretrained(str(base_dir), local_files_only=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    if tokenizer.pad_token_id is None:
        raise ValueError("Tokenizer has no pad or eos token")

    train_rows = read_jsonl(train_file, args.limit_train)
    train_dataset, train_stats = make_dataset(
        tokenizer, train_rows, args.max_seq_len
    )
    print(
        "train       : rows=%d seq=%d..%d mean=%.1f labels=%d..%d mean=%.1f modes=%s"
        % (
            train_stats["rows"],
            train_stats["seq_min"],
            train_stats["seq_max"],
            train_stats["seq_mean"],
            train_stats["label_min"],
            train_stats["label_max"],
            train_stats["label_mean"],
            train_stats["modes"],
        ),
        flush=True,
    )

    eval_dataset = None
    eval_stats = None
    if not args.no_eval and args.max_steps <= 0:
        eval_rows = read_jsonl(eval_file, args.limit_eval)
        eval_dataset, eval_stats = make_dataset(
            tokenizer, eval_rows, args.max_seq_len
        )
        print(
            "eval        : rows=%d seq=%d..%d mean=%.1f labels=%d..%d mean=%.1f"
            % (
                eval_stats["rows"],
                eval_stats["seq_min"],
                eval_stats["seq_max"],
                eval_stats["seq_mean"],
                eval_stats["label_min"],
                eval_stats["label_max"],
                eval_stats["label_mean"],
            ),
            flush=True,
        )

    if args.check_only:
        print(
            "RESULT: P6_TOKENS_OK train_rows=%d eval_rows=%d max_seq=%d"
            % (
                train_stats["rows"],
                eval_stats["rows"] if eval_stats else 0,
                args.max_seq_len,
            ),
            flush=True,
        )
        return

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for this training script")

    gpu_name = torch.cuda.get_device_name(0)
    gpu_mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    print("device      : %s (%.1f GB VRAM)" % (gpu_name, gpu_mem), flush=True)

    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    model = AutoModelForCausalLM.from_pretrained(
        str(base_dir),
        torch_dtype=torch.bfloat16,
        local_files_only=True,
    )
    lora = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=TARGET_MODULES,
    )
    model = get_peft_model(model, lora)
    model.config.use_cache = False
    model.enable_input_require_grads()
    model.print_trainable_parameters()

    args.run_dir.mkdir(parents=True, exist_ok=True)
    eval_strategy = "no" if eval_dataset is None else "epoch"
    save_strategy = "no" if args.max_steps > 0 else "epoch"
    training_args = TrainingArguments(
        output_dir=str(args.run_dir),
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.eval_batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        num_train_epochs=args.epochs,
        max_steps=args.max_steps if args.max_steps > 0 else -1,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        weight_decay=0.0,
        max_grad_norm=1.0,
        logging_steps=10,
        logging_first_step=True,
        eval_strategy=eval_strategy,
        save_strategy=save_strategy,
        save_total_limit=2,
        prediction_loss_only=True,
        bf16=True,
        tf32=True,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        optim="paged_adamw_8bit",
        report_to=[],
        seed=args.seed,
        data_seed=args.seed,
        remove_unused_columns=False,
        dataloader_pin_memory=True,
        disable_tqdm=True,
        run_name=args.tag,
        label_names=["labels"],
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=CausalCollator(tokenizer.pad_token_id),
    )
    resume = resolve_resume(args.run_dir, args.resume)
    if resume:
        print("resume      : %s" % resume, flush=True)
    trainer.train(resume_from_checkpoint=resume)
    if trainer.state.global_step <= 0:
        raise RuntimeError("Training completed without registering a global step")
    trainer.save_state()
    args.adapter_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(args.adapter_dir))
    tokenizer.save_pretrained(str(args.adapter_dir))

    elapsed = time.time() - started
    train_loss = last_metric(trainer.state.log_history, "loss")
    eval_loss = last_metric(trainer.state.log_history, "eval_loss")
    summary = {
        "result": "P6_TRAIN_OK",
        "base": str(base_dir),
        "adapter_dir": str(args.adapter_dir),
        "run_dir": str(args.run_dir),
        "train_rows": train_stats["rows"],
        "eval_rows": eval_stats["rows"] if eval_stats else 0,
        "global_step": trainer.state.global_step,
        "train_loss": train_loss,
        "eval_loss": eval_loss,
        "elapsed_s": round(elapsed, 3),
        "lora": {
            "r": args.lora_r,
            "alpha": args.lora_alpha,
            "dropout": args.lora_dropout,
            "targets": TARGET_MODULES,
        },
        "training": {
            "epochs": args.epochs,
            "max_steps": args.max_steps,
            "batch_size": args.batch_size,
            "grad_accum": args.grad_accum,
            "learning_rate": args.lr,
            "max_seq_len": args.max_seq_len,
        },
        "dataset_sha256": hashlib.sha256(train_file.read_bytes()).hexdigest(),
        "args": json_safe(vars(args)),
    }
    write_json(args.adapter_dir / "training_metadata.json", summary)
    write_json(args.run_dir / "training_summary.json", summary)
    print(
        "RESULT: P6_TRAIN_OK job=%s step=%d train_loss=%s eval_loss=%s "
        "seconds=%.1f adapter=%s"
        % (
            os.environ.get("SLURM_JOB_ID", "local"),
            trainer.state.global_step,
            f"{train_loss:.4f}" if train_loss is not None else "na",
            f"{eval_loss:.4f}" if eval_loss is not None else "na",
            elapsed,
            args.adapter_dir,
        ),
        flush=True,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        traceback.print_exc()
        print(
            "RESULT: P6_TRAIN_FAIL job=%s error=%s"
            % (os.environ.get("SLURM_JOB_ID", "local"), exc),
            file=sys.stderr,
            flush=True,
        )
        print(
            "RESULT: P6_TRAIN_FAIL job=%s error=%s"
            % (os.environ.get("SLURM_JOB_ID", "local"), exc),
            flush=True,
        )
        sys.exit(1)
