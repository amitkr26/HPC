#!/bin/bash
#SBATCH --job-name=bdw_p6_tools_eval_trained
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=00:15:00
#SBATCH --account=tutor
#SBATCH --qos=training
#SBATCH --output=/home/tutor/3ioip3lt/bdw-llm/phase6_advanced/tools/eval/%x-%j.out
#SBATCH --error=/home/tutor/3ioip3lt/bdw-llm/phase6_advanced/tools/eval/%x-%j.err

set -euo pipefail

trap 'rc=$?; echo "==========================================" >&2; echo "FATAL: Job ${SLURM_JOB_ID:-manual} failed at line $LINENO with exit code $rc on $(hostname)" >&2; echo "==========================================" >&2' ERR

mkdir -p "$HOME/bdw-llm/phase6_advanced/tools/eval"
source "$HOME/bdw-llm/venv_p2/bin/activate"
cd "$HOME/bdw-llm"

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false

echo "=========================================="
echo "job id      : ${SLURM_JOB_ID:-local}"
echo "node        : $(hostname)"
echo "date        : $(date -Is)"
echo "python      : $(which python)"
echo "base        : $HOME/bdw-llm/merged/bdw-7b-sft"
echo "adapter     : $HOME/bdw-llm/lora_tools/p6_tool_calling/final"
echo "eval data   : $HOME/bdw-llm/phase6_advanced/tools/data/tool_calls_eval.jsonl"
echo "=========================================="
nvidia-smi -L
echo

python phase6_advanced/tools/evaluate_tools_trained.py "$@"
rc=$?

echo "trained eval rc=$rc"
if [ $rc -eq 0 ]; then
    echo "SUCCESS: Tools trained eval job ${SLURM_JOB_ID:-manual} completed cleanly."
fi
exit $rc
