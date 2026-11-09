#!/usr/bin/env python3
"""Phase 8: Direct Preference Optimization (DPO) for Reasoning + Tool Calling.

Uses DPOTrainer from Hugging Face TRL to align model policy against human/synthetic
preferences, penalizing missing reasoning traces, malformed tool calls, and hallucinations.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import torch
# PyTorch 2.5 compatibility shim for TRL
import torch.distributed.fsdp
try:
    from torch.distributed._composable.fsdp import FSDPModule
    torch.distributed.fsdp.FSDPModule = FSDPModule
except ImportError:
    pass

from datasets import Dataset
from peft import LoraConfig, PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import DPOConfig, DPOTrainer

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[0] if (HERE.parent / "merged").exists() else HERE.parents[1]
DEFAULT_BASE = ROOT / "merged" / "bdw-7b-sft"
DEFAULT_ADAPTER = ROOT / "lora_combined" / "p7_combined" / "final"
DEFAULT_TRAIN = HERE.parent / "data" / "dpo_train.jsonl" if HERE.name == "scripts" else HERE / "data" / "dpo_train.jsonl"
DEFAULT_EVAL = HERE.parent / "data" / "dpo_eval.jsonl" if HERE.name == "scripts" else HERE / "data" / "dpo_eval.jsonl"
DEFAULT_RUN = ROOT / "sft_runs" / "p8_dpo"
DEFAULT_OUT = ROOT / "lora_dpo" / "p8_dpo" / "final"

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
    parser = argparse.ArgumentParser(description="Phase 8 DPO Training")
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE, help="Base SFT model path")
    parser.add_argument("--adapter", type=Path, default=DEFAULT_ADAPTER, help="Phase 7 SFT LoRA adapter to merge before DPO")
    parser.add_argument("--data", type=Path, default=DEFAULT_TRAIN, help="DPO train dataset")
    parser.add_argument("--eval-data", type=Path, default=DEFAULT_EVAL, help="DPO eval dataset")
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN, help="Run output dir")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT, help="Final adapter output dir")
    parser.add_argument("--beta", type=float, default=0.1, help="DPO temperature beta (default: 0.1)")
    parser.add_argument("--lr", type=float, default=5e-5, help="Learning rate (default: 5e-5)")
    parser.add_argument("--epochs", type=float, default=2.0, help="Epochs (default: 2.0)")
    parser.add_argument("--batch-size", type=int, default=2, help="Batch size per device (default: 2)")
    parser.add_argument("--grad-accum", type=int, default=2, help="Gradient accumulation (default: 2)")
    parser.add_argument("--max-len", type=int, default=1024, help="Max total length (default: 1024)")
    parser.add_argument("--max-prompt-len", type=int, default=512, help="Max prompt length (default: 512)")
    parser.add_argument("--lora-r", type=int, default=16, help="LoRA rank")
    parser.add_argument("--lora-alpha", type=int, default=32, help="LoRA alpha")
    parser.add_argument("--loss-type", nargs="+", default=["sigmoid"], help="DPO loss components, e.g. sigmoid sft")
    parser.add_argument("--loss-weights", nargs="+", type=float, default=None, help="Weights for --loss-type components")
    parser.add_argument("--append-eos", action="store_true", help="Append the tokenizer EOS token to completions")
    parser.add_argument("--seed", type=int, default=42, help="Seed")
    parser.add_argument("--check-only", action="store_true", help="Validate architectures and dataset without training")
    return parser.parse_args()


def load_dpo_dataset(path: Path, append_eos: bool = False, eos_token: str | None = None) -> Dataset:
    if not path.is_file():
        raise FileNotFoundError(f"DPO dataset not found: {path}")
    records = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                d = json.loads(line)
                chosen = d["chosen"]
                rejected = d["rejected"]
                if append_eos and eos_token:
                    chosen = chosen.rstrip()
                    rejected = rejected.rstrip()
                    if not chosen.endswith(eos_token):
                        chosen += eos_token
                    if not rejected.endswith(eos_token):
                        rejected += eos_token
                records.append({
                    "prompt": d["prompt"],
                    "chosen": chosen,
                    "rejected": rejected,
                })
    return Dataset.from_list(records)


def main() -> None:
    args = parse_args()
    print("=" * 70)
    print("Phase 8 Reinforcement Learning: Direct Preference Optimization (DPO)")
    print("=" * 70)
    print(f"Base Model:      {args.base}")
    print(f"Initial Adapter: {args.adapter}")
    print(f"Train Dataset:   {args.data}")
    print(f"Eval Dataset:    {args.eval_data}")
    print(f"Hyperparameters: beta={args.beta}, lr={args.lr}, r={args.lora_r}, alpha={args.lora_alpha}")
    print(f"Loss components: {args.loss_type}, weights={args.loss_weights}, append_eos={args.append_eos}")

    # Preflight checks
    if not args.base.is_dir():
        raise FileNotFoundError(f"Base model not found: {args.base}")
    if not args.adapter.is_dir():
        raise FileNotFoundError(f"Phase 7 SFT adapter not found: {args.adapter}")
    if not (args.adapter / "adapter_config.json").is_file():
        raise FileNotFoundError(f"Phase 7 SFT adapter config not found: {args.adapter / 'adapter_config.json'}")
    if not args.data.is_file():
        raise FileNotFoundError(f"Train dataset not found: {args.data}")

    tokenizer = AutoTokenizer.from_pretrained(str(args.base), local_files_only=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    eos_token = tokenizer.eos_token
    train_ds = load_dpo_dataset(args.data, append_eos=args.append_eos, eos_token=eos_token)
    eval_ds = (
        load_dpo_dataset(args.eval_data, append_eos=args.append_eos, eos_token=eos_token)
        if args.eval_data.is_file()
        else None
    )
    print(f"Loaded {len(train_ds)} train preference pairs and {len(eval_ds) if eval_ds else 0} eval pairs.")

    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=0.05,
        target_modules=TARGET_MODULES,
        bias="none",
        task_type="CAUSAL_LM",
    )

    if args.check_only:
        print("\n--- Dry Run Check ---")
        print("Sample Prompt (first 120 chars):", repr(train_ds[0]["prompt"][:120]))
        print("Sample Chosen (first 80 chars):", repr(train_ds[0]["chosen"][:80]))
        print("Sample Rejected (first 80 chars):", repr(train_ds[0]["rejected"][:80]))
        print(f"Phase 7 Adapter: {args.adapter}")
        print(f"LoRA Target Modules: {TARGET_MODULES}")
        print("TRL & DPO imports verified successfully.")
        print("RESULT: PHASE8_DPO_CHECK_OK")
        return

    print("\nLoading base model for DPO...")
    model = AutoModelForCausalLM.from_pretrained(
        str(args.base),
        torch_dtype=torch.bfloat16,
        device_map="cuda",
        local_files_only=True,
    )
    print(f"Loading and merging Phase 7 SFT adapter from {args.adapter}...")
    model = PeftModel.from_pretrained(model, str(args.adapter), is_trainable=False)
    model = model.merge_and_unload(safe_merge=True)
    model.config.use_cache = False
    torch.cuda.empty_cache()

    dpo_config = DPOConfig(
        output_dir=str(args.run_dir),
        beta=args.beta,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        warmup_ratio=0.1,
        logging_steps=10,
        eval_strategy="epoch" if eval_ds else "no",
        save_strategy="epoch",
        loss_type=args.loss_type,
        loss_weights=args.loss_weights,
        max_length=args.max_len,
        bf16=True,
        fp16=False,
        optim="paged_adamw_8bit",
        seed=args.seed,
        report_to="none",
    )

    dpo_trainer = DPOTrainer(
        model=model,
        ref_model=None,
        args=dpo_config,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        processing_class=tokenizer,
        peft_config=lora_config,
    )

    print("\nStarting DPO Training...")
    dpo_trainer.train()

    print(f"\nSaving aligned DPO adapter to {args.output_dir}...")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    dpo_trainer.save_model(str(args.output_dir))
    tokenizer.save_pretrained(str(args.output_dir))
    print(f"RESULT: PHASE8_DPO_TRAIN_OK adapter={args.output_dir}")


if __name__ == "__main__":
    main()
