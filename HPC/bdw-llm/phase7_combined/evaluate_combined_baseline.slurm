#!/usr/bin/env bash
#SBATCH --job-name=bdw_p7_comb_baseline
#SBATCH --account=tutor
#SBATCH --partition=gpu
#SBATCH --qos=training
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=48G
#SBATCH --time=00:10:00
#SBATCH --output=phase7_combined/eval/logs/%x-%j.out
#SBATCH --error=phase7_combined/eval/logs/%x-%j.err

set -euo pipefail

trap 'echo "[ERROR] Slurm job $SLURM_JOB_ID failed at line $LINENO with exit code $?" >&2' ERR

echo "============================================================"
echo "Phase 7 Combined Baseline Evaluation Job: ${SLURM_JOB_ID:-manual}"
echo "Node: $(hostname) | Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "============================================================"

PROJECT_DIR="/home/tutor/3ioip3lt/bdw-llm"
cd "${PROJECT_DIR}"

# Preflight checks
MODEL_DIR="${PROJECT_DIR}/merged/bdw-7b-sft"
EVAL_FILE="${PROJECT_DIR}/phase7_combined/data/combined_eval.jsonl"
OUT_FILE="${PROJECT_DIR}/phase7_combined/eval/combined_baseline_v2_0_bdw7b_sft.json"

if [ ! -d "${MODEL_DIR}" ]; then
    echo "[FATAL] Base model directory not found: ${MODEL_DIR}" >&2
    exit 1
fi

if [ ! -f "${EVAL_FILE}" ]; then
    echo "[FATAL] Evaluation file not found: ${EVAL_FILE}" >&2
    exit 1
fi

mkdir -p "${PROJECT_DIR}/phase7_combined/eval/logs"

# Activate environment
source "${PROJECT_DIR}/venv_p2/bin/activate"

echo "[INFO] Python interpreter: $(which python3)"
echo "[INFO] CUDA device check:"
python3 -c "import torch; print(f'PyTorch {torch.__version__} | CUDA Available: {torch.cuda.is_available()} | Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"

# Run evaluation
python3 -u "${PROJECT_DIR}/phase7_combined/evaluate_combined_baseline.py" \
    --model "${MODEL_DIR}" \
    --eval "${EVAL_FILE}" \
    --out "${OUT_FILE}" \
    --max_new_tokens 512 \
    --device cuda

echo "============================================================"
echo "[SUCCESS] Baseline evaluation completed successfully."
echo "Output: ${OUT_FILE}"
echo "============================================================"
