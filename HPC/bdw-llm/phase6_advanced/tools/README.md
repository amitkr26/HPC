# Phase 6 - Tool Use / Function Calling Dataset

Deterministic, CPU-only dataset generator for teaching BDW/Qwen2.5 to emit
JSON tool calls. No external APIs, paid services, GPUs, or network access are
required after the tokenizer is cached.

## Files

| File | Purpose |
|---|---|
| `generate_tool_dataset.py` | Deterministic generator (stdlib + cached HF tokenizer). |
| `data/tool_calls_train.jsonl` | 120 training rows. |
| `data/tool_calls_eval.jsonl` | 24 held-out evaluation rows. |
| `data/dataset_summary.json` | Counts, token stats, and SHA-256 hashes. |
| `train_tool_calling.py` | Masked assistant-only LoRA SFT on the Phase 2 model. |
| `train_tools.slurm` | 15-minute, one-A100 training launcher. |
| `evaluate_tools_trained.py` | Post-SFT evaluator using the same 24 held-out prompts and metrics. |
| `evaluate_tools_trained.slurm` | 15-minute, one-A100 post-SFT evaluation launcher. |
| `eval/tool_trained_v2_0_bdw7b_sft_lora_p6.json` | Raw post-SFT outputs and metrics. |

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

## Baseline result: v2.0-bdw7b-sft

Run on 2026-11-05 on `rdgpu01` (A100 80GB), bf16, greedy decoding, 192 new
tokens, 24 eval rows. The job loaded only local `merged/bdw-7b-sft`; no model
downloads or external APIs were used (Slurm job `185940`).

Valid means exactly one complete `<tool_call>...</tool_call>` block containing
a JSON object with a string `name` and an object `arguments`.

| Metric | Result |
|---|---:|
| Valid Tool Call Format Rate | **13/24 (54.2%)** |
| JSON body present after `<tool_call>` (missing close accepted) | 22/24 (91.7%) |
| Missing closing `</tool_call>` | 9/24 (37.5%) |
| Plain text, no tool tags | 2/24 (8.3%) |
| Valid tool name / argument schema | 13/24 (54.2%) |
| Exact semantic match | 12/24 (50.0%) |

Interpretation: the current Phase 2 model already selects tools and emits
argument JSON well (22/24 JSON bodies), but only 13/24 close the `<tool_call>`
block. The dominant baseline failure is the missing closing tag, not tool
selection. Two simple sum questions are answered directly in plain text. This
is the primary gap for tool-use SFT.

Reproduce:

```bash
cd ~/bdw-llm
sbatch phase6_advanced/tools/evaluate_tools_baseline.slurm
```

Raw outputs: `eval/tool_baseline_v2_0_bdw7b_sft.json`.

## LoRA fine-tuning

The tool-format repair is a LoRA SFT run on the shipped `v2.0-bdw7b-sft`
weights; the base model is never modified.

- `train_tool_calling.py` - masked assistant-only LoRA SFT on
  `data/tool_calls_train.jsonl`.
- `train_tools.slurm` - 15-minute, one-A100 Slurm launcher.
- Base model: `merged/bdw-7b-sft`.
- Adapter output: `lora_tools/p6_tool_calling/final`.
- Trainer state: `sft_runs/p6_tools`.

Default recipe: LoRA `r=16`, `alpha=32`, dropout `0.05`, on the seven Qwen2
projection modules (`40,370,176` trainable parameters, `0.5273%`); 3 epochs,
`1e-4` cosine, 3% warmup, batch 4, sequence length 768, bf16, and
`paged_adamw_8bit`. Loss is applied only to assistant tokens; system, user,
and tool-response tokens are masked. The 24-row eval split is held out and
used only for eval loss. Expected schedule: 90 optimizer steps.

```bash
cd ~/bdw-llm
sbatch phase6_advanced/tools/train_tools.slurm
```

Monitor:

```bash
squeue -u "$USER"
tail -f bdw_p6_train-<jobid>.out
```

Outputs include `lora_tools/p6_tool_calling/final/adapter_model.safetensors`,
`training_metadata.json`, and epoch checkpoints under `sft_runs/p6_tools`.
The adapter can be loaded over the base with PEFT:

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM

base = AutoModelForCausalLM.from_pretrained("merged/bdw-7b-sft")
model = PeftModel.from_pretrained(base, "lora_tools/p6_tool_calling/final")
```

Full training (`job 185946`) completed in 1m55s: 90 optimizer steps,
final logged train loss `0.0001` (mean `0.0107`), held-out eval loss
`0.0000436`. The final adapter is
`lora_tools/p6_tool_calling/final`; `adapter_model.safetensors` SHA-256 is
`9ce5c70035f1824ac83d7ae83cdb6cc73302a2ddc214819353742dc53200d7ec`.

## Post-SFT result: v2.0-bdw7b-sft + P6 LoRA

Evaluation job `185947` on `rdgpu01` (A100 80GB) loaded the base model plus
`lora_tools/p6_tool_calling/final` and ran the same 24 held-out questions,
prompt rendering, greedy decoding, seed 1337, and 192-token limit as the
baseline.

| Metric | Baseline | + P6 LoRA | Delta |
|---|---:|---:|---:|
| Valid Tool Call Format Rate | 13/24 (54.2%) | **24/24 (100.0%)** | **+11 / +45.8 pp** |
| Missing closing `</tool_call>` | 9/24 (37.5%) | 0/24 (0.0%) | -9 |
| Plain text / no tags | 2/24 (8.3%) | 0/24 (0.0%) | -2 |
| Exact semantic match | 12/24 (50.0%) | 24/24 (100.0%) | +12 / +50.0 pp |

All 24 outputs contained exactly one complete tool-call block, a valid tool
name and argument schema, no extra text outside the tags, and no multiple
calls. The missing-closing-tag failure mode is eliminated on this suite.

Caveat: the 24 prompts use unseen numeric values but the same two tools and
templates as training. The 100% result is evidence for this seed suite, not
production-scale generalization.

Reproduce:

```bash
cd ~/bdw-llm
sbatch phase6_advanced/tools/evaluate_tools_trained.slurm
```

Raw outputs: `eval/tool_trained_v2_0_bdw7b_sft_lora_p6.json`.

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
