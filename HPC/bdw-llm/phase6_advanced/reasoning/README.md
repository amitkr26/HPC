# Phase 6 - Reasoning Dataset

Deterministic, CPU-only generator for teaching the BDW/Qwen2.5 model to produce
short, explicit `<think>...</think>` reasoning traces before a final answer.
No external APIs, paid services, GPUs, or network access are required after the
tokenizer is cached.

## Files

| File | Purpose |
|---|---|
| `generate_reasoning_dataset.py` | Deterministic generator (stdlib + cached HF tokenizer). |
| `data/reasoning_train.jsonl` | 120 training rows. |
| `data/reasoning_eval.jsonl` | 24 held-out evaluation rows. |
| `data/dataset_summary.json` | Counts, token stats, and SHA-256 hashes. |

> `data/*.jsonl` and `dataset_summary.json` are generated artifacts and are
> Git-ignored. Run the generator to recreate them; the script and README are
> the committed source of truth.

## Regenerate

From `~/bdw-llm` on Param Rudra:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
venv_p2/bin/python phase6_advanced/reasoning/generate_reasoning_dataset.py
```

The default tokenizer is `merged/bdw-7b-sft` (local files only) and the default
output directory is `phase6_advanced/reasoning/data`. Both can be overridden
with `--tokenizer` and `--out-dir`.

The seed is `20261105`. The train/eval split uses a separate deterministic
shuffle, so rerunning the same command produces byte-identical files.

## Row schema

```json
{
  "id": "reason_train_math_0001",
  "category": "math",
  "difficulty": "medium",
  "question": "...",
  "messages": [
    {"role": "system", "content": "You are a careful reasoning assistant..."},
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "<think>\n1. ...\n</think>\n\n..."}
  ],
  "metadata": {
    "kind": "production",
    "reasoning_steps": ["...", "..."],
    "answer": "1586 parts",
    "split": "train"
  },
  "text": "<|im_start|>system ... <|im_end|>",
  "tokens": 175
}
```

Every assistant target contains exactly one `<think>` block followed by a
non-empty final answer. The `question` field matches the user message, and the
`text` field is rendered with the real Qwen2.5 chat template for direct
text-field SFT. Coding rows additionally include `sample_input`,
`sample_output`, and `function_name` in `metadata`; tuple inputs are serialized
as JSON arrays.

## Coverage

| Category | Templates | Total | Train / eval |
|---|---|---:|---:|
| Math | inventory, discount, production, area difference (12 each) | 48 | 40 / 8 |
| Logic | five-item ordering puzzles: race 14, line 20, shelf 14 | 48 | 40 / 8 |
| Coding | 12 Python functions x 4 calls each | 48 | 40 / 8 |

Math and logic targets use numbered reasoning steps. Coding targets use the
same step format and end with a fenced ```python implementation.

## Example

Train row `reason_train_math_0001`:

**Question**

```text
A machine produces 26 parts per minute. It runs for 2 hours, but 59 minutes are lost to maintenance. How many parts does it produce?
```

**Assistant**

```text
<think>
1. 2 hours is 2 x 60 = 120 minutes.
2. With 59 minutes lost, the machine runs for 120 - 59 = 61 minutes.
3. At 26 parts per minute, it produces 26 x 61 = 1586 parts.
</think>

1586 parts
```

## Verified generation

```
RESULT: PHASE6_REASONING_DATASET_OK train=120 eval=24
categories={'math': {'train': 40, 'eval': 8},
            'logic': {'train': 40, 'eval': 8},
            'coding': {'train': 40, 'eval': 8}}
tokens: train min=166 mean=206.29 max=335
        eval  min=174 mean=214.54 max=317
train sha256: 9b79d4d77ccd463ee2233ab514e1a1826b6509315485bc6393d38dc7f59209ba
eval  sha256: 9af52700204698c9db3e9feba32032eb48abb193b198e802c96f0c1f864b5046
```

Generator SHA-256:
`b2b5c5727d45382622cf88b68746bc395feb3993037280cf7cc422d3d9928b3f`

Validation performed on the generated files:

- 120 train / 24 eval rows, with 40 / 8 in each category.
- 144 unique questions and no cross-split duplicates.
- Math answers independently recomputed from the question values.
- All logic answers satisfy every ordering clue.
- Every coding implementation executes and returns the stated sample output.
- Every row has exactly one non-empty `<think>` block and a final answer.
- A second generation run produced identical SHA-256 hashes.
- `data/` is confirmed Git-ignored.

This is a small, templated seed dataset for capability bring-up, not a
production-scale reasoning corpus. The held-out prompts use unseen values but
share templates with training; expand the templates and add adversarial cases
before making generalization claims.
