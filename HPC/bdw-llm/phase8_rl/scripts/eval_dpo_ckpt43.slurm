#!/usr/bin/env bash
#SBATCH --job-name=bdw_p8_dpo_ck43_eval
#SBATCH --account=tutor
#SBATCH --partition=gpu
#SBATCH --qos=training
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=48G
#SBATCH --time=00:10:00
#SBATCH --output=phase8_rl/eval/logs/%x-%j.out
#SBATCH --error=phase8_rl/eval/logs/%x-%j.err

set -euo pipefail

trap 'echo "[ERROR] Slurm job $SLURM_JOB_ID failed at line $LINENO with exit code $?" >&2' ERR

echo "============================================================"
echo "Phase 8 DPO Checkpoint-43 Evaluation Job: ${SLURM_JOB_ID:-manual}"
echo "Node: $(hostname) | Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "============================================================"

PROJECT_DIR="/home/tutor/3ioip3lt/bdw-llm"
cd "${PROJECT_DIR}"

MODEL_DIR="${PROJECT_DIR}/merged/bdw-7b-sft"
P7_ADAPTER_DIR="${PROJECT_DIR}/lora_combined/p7_combined/final"
P8_ADAPTER_DIR="${PROJECT_DIR}/sft_runs/p8_dpo/checkpoint-43"
EVAL_FILE="${PROJECT_DIR}/phase7_combined/data/combined_eval.jsonl"
OUT_FILE="${PROJECT_DIR}/phase8_rl/eval/dpo_eval_checkpoint43_v2_0_bdw7b_sft_p7_p8.json"

for path in "${MODEL_DIR}" "${P7_ADAPTER_DIR}" "${P8_ADAPTER_DIR}"; do
    if [ ! -d "${path}" ]; then
        echo "[FATAL] Required directory not found: ${path}" >&2
        exit 1
    fi
done

if [ ! -f "${EVAL_FILE}" ]; then
    echo "[FATAL] Evaluation file not found: ${EVAL_FILE}" >&2
    exit 1
fi

mkdir -p "${PROJECT_DIR}/phase8_rl/eval/logs"
source "${PROJECT_DIR}/venv_p2/bin/activate"

python3 -u "${PROJECT_DIR}/phase8_rl/scripts/evaluate_dpo.py" \
    --model "${MODEL_DIR}" \
    --p7-adapter "${P7_ADAPTER_DIR}" \
    --p8-adapter "${P8_ADAPTER_DIR}" \
    --eval "${EVAL_FILE}" \
    --out "${OUT_FILE}" \
    --max_new_tokens 512 \
    --device cuda

echo "============================================================"
echo "[SUCCESS] Checkpoint-43 evaluation completed successfully."
echo "Output: ${OUT_FILE}"
echo "============================================================"
