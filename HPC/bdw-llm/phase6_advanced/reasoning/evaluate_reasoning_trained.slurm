#!/bin/bash
#SBATCH --job-name=bdw_p6_reason_eval
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=00:10:00
#SBATCH --account=tutor
#SBATCH --qos=training
#SBATCH --output=/home/tutor/3ioip3lt/bdw-llm/phase6_advanced/reasoning/eval/%x-%j.out
#SBATCH --error=/home/tutor/3ioip3lt/bdw-llm/phase6_advanced/reasoning/eval/%x-%j.err

set -euo pipefail

trap 'rc=$?; echo "==========================================" >&2; echo "FATAL: Job $SLURM_JOB_ID failed at line $LINENO with exit code $rc on $(hostname)" >&2; echo "==========================================" >&2' ERR

mkdir -p "$HOME/bdw-llm/phase6_advanced/reasoning/eval"
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
echo "adapter     : $HOME/bdw-llm/lora_reasoning/p6_reasoning/final"
echo "eval data   : $HOME/bdw-llm/phase6_advanced/reasoning/data/reasoning_eval.jsonl"
echo "output json : $HOME/bdw-llm/phase6_advanced/reasoning/eval/reasoning_trained_v2_0_bdw7b_sft.json"
echo "=========================================="
nvidia-smi -L
echo

python phase6_advanced/reasoning/evaluate_reasoning_trained.py "$@"
rc=$?

if [ $rc -eq 0 ]; then
    echo "=========================================="
    echo "SUCCESS: Reasoning trained evaluation job $SLURM_JOB_ID completed cleanly."
    echo "=========================================="
fi
exit $rc
