#!/usr/bin/env python3
"""Phase 7 LoRA SFT: Train v2.0-bdw7b-sft for sequential <think> and <tool_call> generation.

Applies assistant-only loss masking on combined reasoning and tool-calling trajectories.
Target: 7 projection modules (q, k, v, o, gate, up, down), r=16, alpha=32, lr=1e-4 with cosine decay.
"""
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

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent if (HERE.parent / "merged").exists() else HERE.parents[1]
DEFAULT_BASE = ROOT / "merged" / "bdw-7b-sft"
DEFAULT_TRAIN = HERE / "data" / "combined_train.jsonl"
DEFAULT_EVAL = HERE / "data" / "combined_eval.jsonl"
DEFAULT_RUN = ROOT / "sft_runs" / "p7_combined"
DEFAULT_ADAPTER = ROOT / "lora_combined" / "p7_combined" / "final"

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
    parser = argparse.ArgumentParser(description="Phase 7 Combined Reasoning + Tool LoRA SFT")
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE, help="Base model directory")
    parser.add_argument("--data", type=Path, default=DEFAULT_TRAIN, help="Training JSONL dataset")
    parser.add_argument("--eval-data", type=Path, default=DEFAULT_EVAL, help="Evaluation JSONL dataset")
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN, help="Checkpoint run directory")
    parser.add_argument("--adapter-dir", type=Path, default=DEFAULT_ADAPTER, help="Final adapter output directory")
    parser.add_argument("--max-seq-len", type=int, default=1024, help="Maximum sequence length (tokens)")
    parser.add_argument("--epochs", type=float, default=3.0, help="Number of training epochs")
    parser.add_argument("--max-steps", type=int, default=0, help="Override steps limit if > 0")
    parser.add_argument("--batch-size", type=int, default=4, help="Per-device train batch size")
    parser.add_argument("--grad-accum", type=int, default=1, help="Gradient accumulation steps")
    parser.add_argument("--eval-batch-size", type=int, default=4, help="Per-device eval batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--lora-r", type=int, default=16, help="LoRA rank")
    parser.add_argument("--lora-alpha", type=int, default=32, help="LoRA alpha scaling factor")
    parser.add_argument("--lora-dropout", type=float, default=0.05, help="LoRA dropout rate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--check-only", action="store_true", help="Validate dataset tokenization without training")
    parser.add_argument("--no-eval", action="store_true", help="Disable evaluation during training")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
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
            rows.append(row)
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
    categories: dict[str, int] = {}
    for row in rows:
        cat = str(row.get("category", "unknown"))
        categories[cat] = categories.get(cat, 0) + 1
    return {
        "rows": len(records),
        "seq_min": min(seq_lengths),
        "seq_mean": sum(seq_lengths) / len(seq_lengths),
        "seq_max": max(seq_lengths),
        "label_min": min(label_lengths),
        "label_mean": sum(label_lengths) / len(label_lengths),
        "label_max": max(label_lengths),
        "categories": categories,
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


def last_metric(history: list[dict[str, Any]], key: str) -> float | None:
    for entry in reversed(history):
        if key in entry:
            return float(entry[key])
    return None


def main() -> None:
    args = parse_args()
    started = time.time()
    base_dir = Path(args.base).expanduser().resolve()
    train_file = Path(args.data).expanduser().resolve()
    eval_file = Path(args.eval_data).expanduser().resolve()

    if not base_dir.is_dir():
        raise FileNotFoundError(f"Base model directory does not exist: {base_dir}")
    if not train_file.is_file():
        raise FileNotFoundError(f"Training dataset does not exist: {train_file}")
    if not args.no_eval and not eval_file.is_file():
        raise FileNotFoundError(f"Evaluation dataset does not exist: {eval_file}")

    print("=" * 72)
    print("Phase 7 Combined Reasoning + Tool LoRA SFT")
    print("=" * 72)
    print("Base Model:   ", base_dir)
    print("Train Dataset:", train_file)
    print("Eval Dataset: ", eval_file if not args.no_eval else "disabled")
    print("Adapter Out:  ", args.adapter_dir)
    print("Run Out:      ", args.run_dir)
    print(f"LoRA Config:   r={args.lora_r}, alpha={args.lora_alpha}, dropout={args.lora_dropout}")
    print(f"Training Args: epochs={args.epochs}, lr={args.lr}, batch_size={args.batch_size}")

    tokenizer = AutoTokenizer.from_pretrained(str(base_dir), local_files_only=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    if tokenizer.pad_token_id is None:
        raise ValueError("Tokenizer has no pad or eos token")

    train_rows = read_jsonl(train_file)
    train_dataset, train_stats = make_dataset(tokenizer, train_rows, args.max_seq_len)
    print(
        f"Train Set:    rows={train_stats['rows']}, seq_len=[{train_stats['seq_min']}..{train_stats['seq_max']}, avg={train_stats['seq_mean']:.1f}], "
        f"label_len=[{train_stats['label_min']}..{train_stats['label_max']}, avg={train_stats['label_mean']:.1f}], categories={train_stats['categories']}",
        flush=True,
    )

    eval_dataset = None
    eval_stats = None
    if not args.no_eval:
        eval_rows = read_jsonl(eval_file)
        eval_dataset, eval_stats = make_dataset(tokenizer, eval_rows, args.max_seq_len)
        print(
            f"Eval Set:     rows={eval_stats['rows']}, seq_len=[{eval_stats['seq_min']}..{eval_stats['seq_max']}, avg={eval_stats['seq_mean']:.1f}], "
            f"label_len=[{eval_stats['label_min']}..{eval_stats['label_max']}, avg={eval_stats['label_mean']:.1f}]",
            flush=True,
        )

    if args.check_only:
        print("RESULT: PHASE7_TOKENS_OK")
        return

    print("\nLoading base model in bfloat16...")
    model = AutoModelForCausalLM.from_pretrained(
        str(base_dir),
        torch_dtype=torch.bfloat16,
        device_map="cuda",
        local_files_only=True,
    )
    model.config.use_cache = False

    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules=TARGET_MODULES,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    trainable_params, all_params = model.get_nb_trainable_parameters()
    print(
        f"Trainable Parameters: {trainable_params:,} / {all_params:,} "
        f"({100.0 * trainable_params / all_params:.4f}%)"
    )

    training_args = TrainingArguments(
        output_dir=str(args.run_dir),
        num_train_epochs=args.epochs,
        max_steps=args.max_steps if args.max_steps > 0 else -1,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        per_device_eval_batch_size=args.eval_batch_size,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        logging_steps=10,
        eval_strategy="epoch" if not args.no_eval else "no",
        save_strategy="epoch",
        save_total_limit=2,
        fp16=False,
        bf16=True,
        optim="paged_adamw_8bit",
        seed=args.seed,
        report_to="none",
        dataloader_drop_last=False,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=CausalCollator(pad_token_id=tokenizer.pad_token_id),
    )

    print("\nStarting LoRA fine-tuning...")
    train_result = trainer.train()
    history = trainer.state.log_history
    final_train_loss = train_result.training_loss
    final_eval_loss = last_metric(history, "eval_loss")

    print(f"\nTraining completed in {time.time() - started:.2f}s")
    print(f"Final Train Loss: {final_train_loss:.6f}")
    if final_eval_loss is not None:
        print(f"Final Eval Loss:  {final_eval_loss:.6f}")

    args.adapter_dir.mkdir(parents=True, exist_ok=True)
    print(f"Saving final adapter to {args.adapter_dir}...")
    model.save_pretrained(str(args.adapter_dir))
    tokenizer.save_pretrained(str(args.adapter_dir))

    metadata = {
        "base_model": str(base_dir),
        "train_rows": len(train_dataset),
        "eval_rows": len(eval_dataset) if eval_dataset else 0,
        "epochs": args.epochs,
        "train_loss": final_train_loss,
        "eval_loss": final_eval_loss,
        "target_modules": TARGET_MODULES,
        "lora_r": args.lora_r,
        "lora_alpha": args.lora_alpha,
        "elapsed_s": round(time.time() - started, 2),
    }
    with open(args.adapter_dir / "training_metadata.json", "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)

    print(
        f"RESULT: PHASE7_TRAIN_OK adapter={args.adapter_dir} "
        f"train_loss={final_train_loss:.6f} eval_loss={final_eval_loss if final_eval_loss is not None else -1:.6f}"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        traceback.print_exc()
        print(f"RESULT: PHASE7_TRAIN_FAIL error={exc}", file=sys.stderr)
        sys.exit(1)
