# Phase 8: Reinforcement Learning via Direct Preference Optimization (DPO)

Phase 8 elevates the reasoning and tool-calling agent beyond Supervised Fine-Tuning (SFT) using Direct Preference Optimization (DPO), culminating in our production hybrid model `merged/bdw7b-reasoning-dpo-final`.

---

## 1. Objective

While SFT instills valid syntax imitation, DPO directly optimizes the policy $\pi_\theta$ against preference pairs $(x, y_w, y_l)$:
- **Chosen ($y_w$):** Rigorous, logically sound step-by-step reasoning inside `<think>...</think>`, followed immediately by syntactically valid `<tool_call>...</tool_call>` actions or verified final answers.
- **Rejected ($y_l$):** Flawed trajectories including reasoning omissions (direct tool shortcuts), unclosed XML tags, hallucinated arguments, flawed math derivations, and inverted tag orders.

Loss Objective:
$$\mathcal{L}_{\text{DPO}}(\pi_\theta; \pi_{\text{ref}}) = -\mathbb{E}_{(x, y_w, y_l)}\left[\log \sigma\left(\beta \log \frac{\pi_\theta(y_w|x)}{\pi_{\text{ref}}(y_w|x)} - \beta \log \frac{\pi_\theta(y_l|x)}{\pi_{\text{ref}}(y_l|x)}\right)\right] + \lambda_{\text{sft}} \mathcal{L}_{\text{sft}}(y_w|x)$$

---

## 2. Directory Structure

```
phase8_rl/
├── README.md
├── scripts/
│   ├── generate_dpo_data.py       # Preference dataset generator (170 train, 30 eval pairs)
│   ├── train_dpo.py               # DPO training script using Hugging Face TRL + LoRA
│   ├── train_dpo.slurm            # Baseline DPO Slurm batch launcher
│   ├── train_dpo_retune.slurm     # Tuned DPO launcher (beta=0.5, lr=1e-5, sft auxiliary loss)
│   ├── evaluate_dpo.py            # Comprehensive evaluation harness for think + tool formats
│   ├── evaluate_dpo.slurm         # Evaluation launcher for baseline DPO adapter
│   ├── evaluate_dpo_retune.slurm  # Evaluation launcher for retuned DPO adapter
│   ├── merge_final_model.py       # Sequential PEFT LoRA merger (Base + P7 SFT + P8 DPO)
│   └── merge_final.slurm          # Slurm batch launcher for final model merge
├── data/
│   ├── dpo_train.jsonl            # 170 training preference pairs (gitignored)
│   └── dpo_eval.jsonl             # 30 held-out preference evaluation pairs (gitignored)
└── eval/
    ├── dpo_eval_v2_0_bdw7b_sft_p7_p8.json         # Baseline DPO evaluation report
    ├── dpo_eval_checkpoint43_v2_0_bdw7b_sft_p7_p8.json  # Checkpoint-43 evaluation report
    └── dpo_eval_retune_v2_0_bdw7b_sft_p7_p8.json  # Final retuned DPO evaluation report (100% format)
```

---

## 3. Training & Evaluation Progression

| Model / Stage | Combined Format | Think Tag Format | Tool Call Format | Tag Ordering | Tool Args Match |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Phase 7 Baseline (`v2.0-bdw7b-sft`)** | 0.0% (0/30) | 0.0% (0/30) | 63.3% (19/30) | 0.0% (0/30) | 53.3% (16/30) |
| **Phase 7 Trained (`p7_combined`)** | 100.0% (30/30) | 100.0% (30/30) | 100.0% (30/30) | 100.0% (30/30) | 90.0% (27/30) |
| **Phase 8 DPO Initial (`p8_dpo`, $\beta=0.1$)** | 50.0% (15/30) | 63.3% (19/30) | 50.0% (15/30) | 50.0% (15/30) | 46.7% (14/30) |
| **Phase 8 DPO Retune (`p8_dpo_retune`, $\beta=0.5$)** | **100.0% (30/30)** | **100.0% (30/30)** | **100.0% (30/30)** | **100.0% (30/30)** | **93.3% (28/30)** |

### Retune Hyperparameters
- Base Policy: `merged/bdw-7b-sft` + `lora_combined/p7_combined/final`
- DPO Beta ($\beta$): 0.5
- Learning Rate: $1 \times 10^{-5}$ (cosine decay)
- LoRA Rank $r$: 8, $\alpha$: 16
- Loss Formulation: Sigmoid DPO with SFT regularization (`--loss-weights 1.0 0.5`)
- Target Modules: All 7 projection layers (`q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`)

---

## 4. Final Hybrid Model Merge

The final unified model was synthesized via sequential PEFT LoRA folding into full precision `bfloat16` weights:
- **Base Model:** `merged/bdw-7b-sft` (Qwen2 7B architecture, 28 layers, hidden size 3584)
- **Adapter 1:** Phase 7 Combined Reasoning & Tool Calling LoRA (`lora_combined/p7_combined/final`, $r=16, \alpha=32$)
- **Adapter 2:** Phase 8 Retuned DPO LoRA (`lora_dpo/p8_dpo_retune/final`, $r=8, \alpha=16$)
- **Final Output:** `merged/bdw7b-reasoning-dpo-final`
  - Total Size: 14.20 GiB (4 sharded `.safetensors` files $\le$ 5 GB)
  - Full Hugging Face compatible tokenizer configs, special tokens map, and `merge_manifest.json`.
