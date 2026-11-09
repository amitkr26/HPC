#!/bin/bash
#SBATCH --job-name=bdw_p6_tools_train
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=00:15:00
#SBATCH --account=tutor
#SBATCH --qos=training
#SBATCH --output=/home/tutor/3ioip3lt/bdw-llm/sft_runs/p6_tools/%x-%j.out
#SBATCH --error=/home/tutor/3ioip3lt/bdw-llm/sft_runs/p6_tools/%x-%j.err

set -euo pipefail

trap 'rc=$?; echo "==========================================" >&2; echo "FATAL: Job ${SLURM_JOB_ID:-manual} failed at line $LINENO with exit code $rc on $(hostname)" >&2; echo "==========================================" >&2' ERR

mkdir -p "$HOME/bdw-llm/sft_runs/p6_tools" "$HOME/bdw-llm/lora_tools/p6_tool_calling/final"
source "$HOME/bdw-llm/venv_p2/bin/activate"
cd "$HOME/bdw-llm"

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

echo "=========================================="
echo "job id      : ${SLURM_JOB_ID:-local}"
echo "node        : $(hostname)"
echo "date        : $(date -Is)"
echo "python      : $(which python)"
echo "cpus        : ${SLURM_CPUS_PER_TASK:-4}"
echo "base        : $HOME/bdw-llm/merged/bdw-7b-sft"
echo "train data  : $HOME/bdw-llm/phase6_advanced/tools/data/tool_calls_train.jsonl"
echo "eval data   : $HOME/bdw-llm/phase6_advanced/tools/data/tool_calls_eval.jsonl"
echo "run dir     : $HOME/bdw-llm/sft_runs/p6_tools"
echo "adapter dir : $HOME/bdw-llm/lora_tools/p6_tool_calling/final"
echo "=========================================="
nvidia-smi -L
echo

python phase6_advanced/tools/train_tool_calling.py "$@"
rc=$?

if [ $rc -eq 0 ]; then
    echo "=========================================="
    echo "SUCCESS: Tools SFT job ${SLURM_JOB_ID:-manual} completed cleanly."
    echo "=========================================="
fi
exit $rc
