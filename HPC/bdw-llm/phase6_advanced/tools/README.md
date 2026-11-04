# Phase 6 - Tool Use / Function Calling Dataset

Deterministic, CPU-only dataset generator for teaching BDW/Qwen2.5 to emit
JSON tool calls. No external APIs, paid services, GPUs, or network access are
required after the tokenizer is cached.

## Files

| File | Purpose |
|---|---|
| `generate_tool_dataset.py` | Deterministic generator (stdlib + cached HF tokenizer). |
| `evaluate_tools_baseline.py` | Evaluates models on `data/tool_calls_eval.jsonl` (format & semantic metrics). |
| `evaluate_tools_baseline.slurm` | Slurm GPU batch job harness on PARAM Rudra. |
| `data/tool_calls_train.jsonl` | 120 training rows. |
| `data/tool_calls_eval.jsonl` | 24 held-out evaluation rows. |
| `data/dataset_summary.json` | Counts, token stats, and SHA-256 hashes. |
| `eval/tool_baseline_v2_0_bdw7b_sft.json` | Baseline evaluation results for `v2.0-bdw7b-sft`. |

> `data/*.jsonl` and `dataset_summary.json` are generated artifacts and are
> Git-ignored. Run the generator to recreate them; the script and README are
> the committed source of truth.

## Regenerate

From `~/bdw-llm` on Param Rudra:

```bash
venv_p5/bin/python phase6_advanced/tools/generate_tool_dataset.py \
  --train-size 120 --eval-size 24 --seed 1337
```

Use `--no-render` if the Qwen tokenizer is unavailable; rows then contain
`tools` + `messages` only.

## Row schema

```json
{
  "id": "tool_train_0002",
  "split": "train",
  "source": "phase6-tools-v1",
  "tools": [{"type": "function", "function": {"name": "calculator", "...": "..."}}],
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "What is 86% of 3047?"},
    {"role": "assistant", "content": "", "tool_calls": [{
      "id": "call_0002",
      "type": "function",
      "function": {"name": "calculator", "arguments": {"expression": "3047 * 86 / 100"}}
    }]}
  ],
  "metadata": {
    "tool": "calculator",
    "mode": "call_only",
    "expected_arguments": {"expression": "3047 * 86 / 100"},
    "expected_result": 2620.42
  },
  "text": "<|im_start|>system ... <tool_call>...</tool_call><|im_end|>",
  "tokens": 410
}
```

`arguments` is a JSON **object** (Qwen2.5/Hermes style), not OpenAI's
string-encoded arguments. The `text` field is rendered with the real Qwen2.5
chat template, including the `# Tools` block and `<tool_call>` tags, so it can
be used directly by a text-field SFT pipeline.

## Tools

- `calculator(expression: string)` - basic arithmetic with numbers,
  parentheses, `+`, `-`, `*`, `/`.
- `unit_converter(value: number, from_unit: string, to_unit: string)` -
  km/mi, m/ft, kg/lb, Celsius/Fahrenheit.

## Modes

- `call_only` (104 rows) - system, user, assistant tool call.
- `full` (40 rows) - the same plus a tool result and a final assistant answer.

The eval split is call-only and uses unseen generated values.

## Verified generation

```
RESULT: PHASE6_TOOL_DATASET_OK train=120 eval=24
tools={'unit_converter': 29, 'calculator': 115}
modes={'full': 40, 'call_only': 104}
tokens: min=403 mean=421.86 max=467
```

This is a small seed dataset for capability bring-up, not a production-scale
tool-use corpus. Expand templates, tools, and adversarial cases before making
quality claims.

## Baseline Evaluation (`v2.0-bdw7b-sft`)

Run baseline evaluation against the 24 held-out evaluation questions using the
Phase 2 model (`merged/bdw-7b-sft`):

```bash
# Interactive / compute node
venv_p2/bin/python phase6_advanced/tools/evaluate_tools_baseline.py

# Slurm batch job (PARAM Rudra gpu partition)
sbatch phase6_advanced/tools/evaluate_tools_baseline.slurm
```

### Verified Baseline Results (Slurm Job `185937`, A100 80GB, 14.7s)

| Metric | Score | Percentage | Notes |
|---|---|---|---|
| **Valid Tool Call Format Rate** | **13 / 24** | **54.2%** | Primary metric: complete `<tool_call>` tag with valid JSON object. |
| **Clean Format (no extra text)** | 13 / 24 | 54.2% | Exact match to valid format. |
| **JSON Body in `<tool_call>` tag** | 22 / 24 | 91.7% | Initiated `<tool_call>` with valid JSON payload. |
| **Missing Closing Tag (`</tool_call>`)** | 9 / 24 | 37.5% | Emitted valid JSON inside `<tool_call>` but stopped at EOS without `</tool_call>`. |
| **Plain Text (Bypassed Tool)** | 2 / 24 | 8.3% | Answered basic addition directly in plain text instead of invoking `calculator`. |
| **Exact Semantic Match** | 12 / 24 | 50.0% | Correct tool name and exact matching arguments. |

### Failure Analysis

1. **Tag Termination (37.5% / 9 rows)**: The model demonstrates clear intent and outputs syntactically valid JSON arguments inside `<tool_call>`, but halts at end-of-sequence before emitting the closing `</tool_call>` delimiter. This indicates that fine-tuning on Phase 6 trajectory pairs will easily bridge this syntax gap.
2. **Plain-Text Direct Arithmetic (8.3% / 2 rows)**: For trivial addition questions (e.g., `What is 7553 + 868?`), the model bypasses the tool call and directly generates `"The sum of 7553 and 868 is 8421."` Fine-tuning will reinforce tool enforcement when tools are defined in the prompt.
