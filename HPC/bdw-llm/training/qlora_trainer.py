#!/usr/bin/env python3
"""
BerojgarDegreeWala (BDW) — Phase 6/7 QLoRA Fine-Tuning Pipeline
Model: Qwen/Qwen2.5-72B-Instruct in 4-bit (bitsandbytes NF4)
Target: NVIDIA A100-80GB on Param Rudra cluster with aggressive checkpointing
and automatic checkpoint-resumption to survive 15-minute Slurm QOS limits.
"""

import os
import sys
import glob
import re
import argparse
import logging
from typing import Optional

import torch
from datasets import load_dataset, Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from transformers.trainer_utils import get_last_checkpoint
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    TaskType,
)
from trl import SFTTrainer, SFTConfig

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("BDW-QLoRA")


def parse_args():
    parser = argparse.ArgumentParser(description="BDW QLoRA 72B Fine-Tuning")
    parser.add_argument(
        "--model_id",
        type=str,
        default=None,
        help="Model ID or path to cached snapshots.",
    )
    parser.add_argument(
        "--data_path",
        type=str,
        default=None,
        help="Path to training jsonl dataset.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="training/checkpoints",
        help="Directory to save periodic step checkpoints.",
    )
    parser.add_argument(
        "--adapter_dir",
        type=str,
        default="training/lora_adapter",
        help="Directory to save the final merged/standalone LoRA adapter.",
    )
    parser.add_argument(
        "--max_seq_length",
        type=int,
        default=1024,
        help="Maximum token sequence length.",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=1,
        help="Per-device train batch size.",
    )
    parser.add_argument(
        "--grad_accum",
        type=int,
        default=4,
        help="Gradient accumulation steps.",
    )
    parser.add_argument(
        "--learning_rate",
        type=float,
        default=2e-4,
        help="AdamW peak learning rate.",
    )
    parser.add_argument(
        "--lora_r",
        type=int,
        default=16,
        help="LoRA rank dimension.",
    )
    parser.add_argument(
        "--lora_alpha",
        type=int,
        default=32,
        help="LoRA scaling alpha.",
    )
    parser.add_argument(
        "--lora_dropout",
        type=float,
        default=0.05,
        help="LoRA dropout probability.",
    )
    parser.add_argument(
        "--save_steps",
        type=int,
        default=5,
        help="Aggressive checkpoint saving interval (steps).",
    )
    parser.add_argument(
        "--save_total_limit",
        type=int,
        default=5,
        help="Maximum number of step checkpoints to preserve.",
    )
    parser.add_argument(
        "--max_steps",
        type=int,
        default=50,
        help="Total training steps.",
    )
    parser.add_argument(
        "--logging_steps",
        type=int,
        default=1,
        help="Step interval for loss logging.",
    )
    return parser.parse_args()


def resolve_model_path(model_arg: Optional[str]) -> str:
    """Resolve model path to local Hugging Face snapshot if available, or fallback."""
    if model_arg and os.path.exists(model_arg):
        return model_arg

    snapshot_dir = os.path.expanduser(
        "~/.cache/huggingface/hub/models--Qwen--Qwen2.5-72B-Instruct/snapshots"
    )
    if os.path.isdir(snapshot_dir):
        snapshots = [
            os.path.join(snapshot_dir, d)
            for d in os.listdir(snapshot_dir)
            if os.path.isdir(os.path.join(snapshot_dir, d))
        ]
        if snapshots:
            logger.info(f"Discovered local snapshot: {snapshots[0]}")
            return snapshots[0]

    return model_arg or "Qwen/Qwen2.5-72B-Instruct"


def find_latest_checkpoint(checkpoint_dir: str) -> Optional[str]:
    """
    Search for the latest checkpoint-* folder in checkpoint_dir.
    Returns path to the checkpoint with the highest step number, or None.
    """
    if not os.path.exists(checkpoint_dir):
        return None

    # Try transformers helper
    last_ckpt = get_last_checkpoint(checkpoint_dir)
    if last_ckpt is not None:
        return last_ckpt

    # Fallback manual scan
    checkpoints = glob.glob(os.path.join(checkpoint_dir, "checkpoint-*"))
    if not checkpoints:
        return None

    def extract_step(path: str) -> int:
        match = re.search(r"checkpoint-(\d+)", path)
        return int(match.group(1)) if match else -1

    valid_ckpts = [c for c in checkpoints if extract_step(c) >= 0]
    if not valid_ckpts:
        return None

    best = max(valid_ckpts, key=extract_step)
    logger.info(f"Manually resolved latest checkpoint: {best}")
    return best


def main():
    args = parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(args.adapter_dir, exist_ok=True)

    model_path = resolve_model_path(args.model_id)
    logger.info(f"Target model path: {model_path}")
    logger.info(f"Checkpoint output directory: {args.output_dir}")
    logger.info(f"Final adapter directory: {args.adapter_dir}")

    # 1. 4-Bit NormalFloat Quantization Configuration
    logger.info("Configuring bitsandbytes 4-bit NF4 quantization...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    # 2. Tokenizer Initialization
    logger.info("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        trust_remote_code=True,
        padding_side="right",
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        logger.info(f"Assigned pad_token = eos_token ({tokenizer.pad_token})")

    # 3. Model Loading with 4-bit Quantization
    logger.info("Loading base 72B model in 4-bit NF4 precision with device_map='auto'...")
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
    )

    # 4. Enable Gradient Checkpointing and Prepare for k-bit Training
    logger.info("Enabling gradient checkpointing and preparing for k-bit training...")
    model.gradient_checkpointing_enable()
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    model.config.use_cache = False

    # 5. Apply PEFT / LoRA Configuration
    logger.info(
        f"Applying LoRA: r={args.lora_r}, alpha={args.lora_alpha}, "
        "modules=['q_proj', 'v_proj', 'k_proj', 'o_proj']"
    )
    peft_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # 6. Load Training Dataset
    if args.data_path and os.path.exists(args.data_path):
        logger.info(f"Loading dataset from file: {args.data_path}")
        dataset = load_dataset("json", data_files=args.data_path, split="train")
    else:
        logger.warning("No data_path provided or file not found. Generating fallback in-memory dataset...")
        fallback_examples = [
            {
                "text": (
                    "<|im_start|>system\nYou are BerojgarDegreeWala AI, India's deep-tech hardware career and research intelligence model.<|im_end|>\n"
                    "<|im_start|>user\nWhat is the static memory required per GPU for a 70B model sharded with DeepSpeed ZeRO-3 across 32 GPUs?<|im_end|>\n"
                    "<|im_start|>assistant\n<think>\nModel weights: 70B * 2B = 140GB. Gradients: 70B * 2B = 140GB. Adam states: 70B * 16B = 1120GB. Total = 1400GB. 1400 / 32 = 43.75GB per GPU.\n</think>\n"
                    "Under DeepSpeed ZeRO-3 across 32 GPUs, the static memory required per GPU is **43.75 GB**.<|im_end|>"
                )
            }
        ]
        dataset = Dataset.from_list(fallback_examples)

    logger.info(f"Training dataset size: {len(dataset)} examples")

    # 7. Configure SFT Training Arguments with Aggressive Checkpointing
    logger.info(
        f"Training configuration: save_steps={args.save_steps}, "
        f"max_steps={args.max_steps}, grad_accum={args.grad_accum}, lr={args.learning_rate}"
    )
    training_args = SFTConfig(
        output_dir=args.output_dir,
        dataset_text_field="text",
        max_length=args.max_seq_length,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.learning_rate,
        weight_decay=0.01,
        warmup_ratio=0.05,
        lr_scheduler_type="cosine",
        bf16=True,
        optim="paged_adamw_8bit",
        logging_steps=args.logging_steps,
        save_strategy="steps",
        save_steps=args.save_steps,
        save_total_limit=args.save_total_limit,
        max_steps=args.max_steps,
        report_to="none",
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        processing_class=tokenizer,
    )

    # 8. Checkpoint Resumption Logic (Survival of 15-Minute Slurm Limits)
    latest_checkpoint = find_latest_checkpoint(args.output_dir)
    if latest_checkpoint:
        logger.info(
            f"===> [RESUME] Found existing checkpoint: {latest_checkpoint}. "
            "Resuming training state seamlessly..."
        )
        trainer.train(resume_from_checkpoint=latest_checkpoint)
    else:
        logger.info("===> [START] No existing checkpoint found. Initiating training from step 0...")
        trainer.train()

    # 9. Save Final Adapter
    logger.info(f"Saving final trained LoRA adapter to: {args.adapter_dir}")
    trainer.model.save_pretrained(args.adapter_dir)
    tokenizer.save_pretrained(args.adapter_dir)
    logger.info("Training pipeline successfully finished!")


if __name__ == "__main__":
    main()
