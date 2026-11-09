#!/usr/bin/env bash
#SBATCH --job-name=bdw_p8_live_test
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
trap 'echo "[ERROR] Slurm job ${SLURM_JOB_ID:-manual} failed at line ${LINENO} with exit code $?" >&2' ERR

PROJECT_DIR="/home/tutor/3ioip3lt/bdw-llm"
cd "${PROJECT_DIR}"

mkdir -p "${PROJECT_DIR}/phase8_rl/eval/logs"
source "${PROJECT_DIR}/venv_p2/bin/activate"

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false

echo "============================================================"
echo "Phase 8 Live Test Job: ${SLURM_JOB_ID:-manual}"
echo "Node: $(hostname) | Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "============================================================"

python3 -u "${PROJECT_DIR}/phase8_rl/scripts/live_test.py" \
    --model-path "${PROJECT_DIR}/merged/bdw7b-reasoning-dpo-final" \
    --temperature 0.1 \
    --max-new-tokens 512 \
    --device cuda

echo "============================================================"
echo "[SUCCESS] Phase 8 Live Test completed successfully."
echo "============================================================"
