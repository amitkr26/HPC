#!/usr/bin/env bash
#SBATCH --job-name=bdw_p8_merge_final
#SBATCH --account=tutor
#SBATCH --partition=cpu
#SBATCH --qos=training
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=00:15:00
#SBATCH --output=phase8_rl/eval/logs/%x-%j.out
#SBATCH --error=phase8_rl/eval/logs/%x-%j.err

set -euo pipefail
trap 'echo "[ERROR] Slurm job ${SLURM_JOB_ID:-manual} failed at line ${LINENO} with exit code $?" >&2' ERR

PROJECT_DIR="/home/tutor/3ioip3lt/bdw-llm"
BASE_DIR="${PROJECT_DIR}/merged/bdw-7b-sft"
P7_ADAPTER="${PROJECT_DIR}/lora_combined/p7_combined/final"
P8_ADAPTER="${PROJECT_DIR}/lora_dpo/p8_dpo_retune/final"
OUT_DIR="${PROJECT_DIR}/merged/bdw7b-reasoning-dpo-final"

cd "${PROJECT_DIR}"
mkdir -p "${PROJECT_DIR}/phase8_rl/eval/logs"

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-4}"

source "${PROJECT_DIR}/venv_p2/bin/activate"

echo "============================================================"
echo "Phase 8 final merge: base + Phase 7 SFT + Phase 8 DPO"
echo "Job: ${SLURM_JOB_ID:-manual} | Node: $(hostname) | Date: $(date -Is)"
echo "CPUs: ${SLURM_CPUS_PER_TASK:-?} | Memory: 64G requested"
echo "Base: ${BASE_DIR}"
echo "P7:   ${P7_ADAPTER}"
echo "P8:   ${P8_ADAPTER}"
echo "Out:  ${OUT_DIR}"
echo "============================================================"
nproc
free -h
df -h "${PROJECT_DIR}"

python -u "${PROJECT_DIR}/phase8_rl/scripts/merge_final_model.py" \
    --base "${BASE_DIR}" \
    --p7-adapter "${P7_ADAPTER}" \
    --p8-adapter "${P8_ADAPTER}" \
    --out "${OUT_DIR}" \
    --dtype bfloat16 \
    --max-shard-size 5GB

echo "============================================================"
echo "[SUCCESS] Final merge completed."
echo "Output: ${OUT_DIR}"
echo "============================================================"
