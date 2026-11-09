#!/usr/bin/env bash
#SBATCH --job-name=bdw_p7_comb_train
#SBATCH --account=tutor
#SBATCH --partition=gpu
#SBATCH --qos=training
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --time=00:15:00
#SBATCH --output=sft_runs/p7_combined/logs/%x-%j.out
#SBATCH --error=sft_runs/p7_combined/logs/%x-%j.err

set -euo pipefail

trap 'echo "[ERROR] Slurm job $SLURM_JOB_ID failed at line $LINENO with exit code $?" >&2' ERR

echo "============================================================"
echo "Phase 7 Combined Reasoning + Tool SFT Job: ${SLURM_JOB_ID:-manual}"
echo "Node: $(hostname) | Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "============================================================"

PROJECT_DIR="/home/tutor/3ioip3lt/bdw-llm"
cd "${PROJECT_DIR}"

BASE_DIR="${PROJECT_DIR}/merged/bdw-7b-sft"
TRAIN_FILE="${PROJECT_DIR}/phase7_combined/data/combined_train.jsonl"
EVAL_FILE="${PROJECT_DIR}/phase7_combined/data/combined_eval.jsonl"
RUN_DIR="${PROJECT_DIR}/sft_runs/p7_combined"
ADAPTER_DIR="${PROJECT_DIR}/lora_combined/p7_combined/final"

mkdir -p "${RUN_DIR}/logs"
mkdir -p "${ADAPTER_DIR}"

# Activate virtualenv
source "${PROJECT_DIR}/venv_p2/bin/activate"

echo "[INFO] Python: $(which python3)"
python3 -c "import torch; print(f'PyTorch {torch.__version__} | CUDA: {torch.cuda.is_available()} | Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"

# Run SFT
python3 -u "${PROJECT_DIR}/phase7_combined/train_combined.py" \
    --base "${BASE_DIR}" \
    --data "${TRAIN_FILE}" \
    --eval-data "${EVAL_FILE}" \
    --run-dir "${RUN_DIR}" \
    --adapter-dir "${ADAPTER_DIR}" \
    --max-seq-len 1024 \
    --epochs 3.0 \
    --batch-size 4 \
    --grad-accum 1 \
    --lr 1e-4 \
    --lora-r 16 \
    --lora-alpha 32 \
    --lora-dropout 0.05 \
    --seed 42

echo "============================================================"
echo "[SUCCESS] Phase 7 LoRA SFT finished successfully."
echo "Final Adapter: ${ADAPTER_DIR}"
echo "============================================================"
