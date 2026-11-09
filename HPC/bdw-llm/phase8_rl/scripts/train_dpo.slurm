#!/usr/bin/env bash
#SBATCH --job-name=bdw_p8_dpo_train
#SBATCH --account=tutor
#SBATCH --partition=gpu
#SBATCH --qos=training
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --time=00:15:00
#SBATCH --output=phase8_rl/eval/logs/%x-%j.out
#SBATCH --error=phase8_rl/eval/logs/%x-%j.err

set -euo pipefail

trap 'echo "[ERROR] Slurm job $SLURM_JOB_ID failed at line $LINENO with exit code $?" >&2' ERR

echo "============================================================"
echo "Phase 8 DPO Reinforcement Learning Job: ${SLURM_JOB_ID:-manual}"
echo "Node: $(hostname) | Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "============================================================"

PROJECT_DIR="/home/tutor/3ioip3lt/bdw-llm"
cd "${PROJECT_DIR}"

BASE_DIR="${PROJECT_DIR}/merged/bdw-7b-sft"
ADAPTER_DIR="${PROJECT_DIR}/lora_combined/p7_combined/final"
TRAIN_FILE="${PROJECT_DIR}/phase8_rl/data/dpo_train.jsonl"
EVAL_FILE="${PROJECT_DIR}/phase8_rl/data/dpo_eval.jsonl"
RUN_DIR="${PROJECT_DIR}/sft_runs/p8_dpo"
OUT_DIR="${PROJECT_DIR}/lora_dpo/p8_dpo/final"

mkdir -p "${RUN_DIR}/logs"
mkdir -p "${OUT_DIR}"
mkdir -p "${PROJECT_DIR}/phase8_rl/eval/logs"

# Preflight assertions
if [ ! -d "${BASE_DIR}" ]; then
    echo "[FATAL] Base model directory not found: ${BASE_DIR}" >&2
    exit 1
fi
if [ ! -f "${TRAIN_FILE}" ]; then
    echo "[FATAL] Train file not found: ${TRAIN_FILE}" >&2
    exit 1
fi

source "${PROJECT_DIR}/venv_p2/bin/activate"

echo "[INFO] Python interpreter: $(which python3)"
python3 -c "import torch; print(f'PyTorch {torch.__version__} | CUDA: {torch.cuda.is_available()} | Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"

# Run DPO Training
python3 -u "${PROJECT_DIR}/phase8_rl/scripts/train_dpo.py" \
    --base "${BASE_DIR}" \
    --adapter "${ADAPTER_DIR}" \
    --data "${TRAIN_FILE}" \
    --eval-data "${EVAL_FILE}" \
    --run-dir "${RUN_DIR}" \
    --output-dir "${OUT_DIR}" \
    --beta 0.1 \
    --lr 5e-5 \
    --epochs 2.0 \
    --batch-size 2 \
    --grad-accum 2 \
    --max-len 1024 \
    --max-prompt-len 512 \
    --lora-r 16 \
    --lora-alpha 32 \
    --seed 42

echo "============================================================"
echo "[SUCCESS] Phase 8 DPO Training completed successfully."
echo "Output: ${OUT_DIR}"
echo "============================================================"
