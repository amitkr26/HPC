# Phase 7: Combining Reasoning with Tool Calling

Phase 7 unites the Phase 6 capabilities:
1. **Chain-of-Thought Reasoning (`<think>...</think>`)**
2. **Deterministic Function / Tool Calling (`<tool_call>...</tool_call>`)**

The target trajectory requires the assistant to first formulate an explicit, step-by-step reasoning plan inside `<think>...</think>` tags to break down complex queries, then immediately invoke the structured tool call within `<tool_call>...</tool_call>` tags.

---

## 1. Directory Structure

```
phase7_combined/
├── README.md
├── generate_combined_dataset.py       # Deterministic dataset generator
├── evaluate_combined_baseline.py      # Baseline evaluation on v2.0-bdw7b-sft
├── evaluate_combined_baseline.slurm   # 4 CPU, 48GB, 10m A100 Slurm launcher
├── data/
│   ├── combined_train.jsonl           # 150 training rows
│   └── combined_eval.jsonl            # 30 held-out evaluation rows
└── eval/
    ├── logs/                          # Slurm execution logs
    └── combined_baseline_v2_0_bdw7b_sft.json
```

---

## 2. Dataset Schema

Each JSONL row contains:
- `id`: Unique identifier (e.g., `comb_train_0001`, `comb_eval_0001`).
- `split`: `"train"` or `"eval"`.
- `source`: `"phase7-combined-v1"`.
- `category`: Problem domain (`"vlsi"`, `"hpc"`, `"physics_math"`, `"finance_analytics"`).
- `question`: Complex engineering/scientific user request requiring calculation or unit scaling.
- `tools`: Function signatures visible to the model (`calculator`, `unit_converter`).
- `messages`: System prompt, user question, and assistant response formatted with `<think>` and `tool_calls`.
- `metadata`: Expected tool, arguments, reasoning steps, and expected numerical result.
- `text`: Fully rendered Qwen 2.5 chat template representation.
- `tokens`: Exact token length encoded by `v2.0-bdw7b-sft` tokenizer.

---

## 3. Usage Commands

### Generate and Validate Dataset
```bash
python3 phase7_combined/generate_combined_dataset.py --train-count 150 --eval-count 30 --seed 42
```

### Dry-Run Validation Only
```bash
python3 phase7_combined/generate_combined_dataset.py --check-only
```

### Run Baseline Evaluation on Cluster (Slurm)
```bash
sbatch phase7_combined/evaluate_combined_baseline.slurm
```
