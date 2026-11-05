#!/bin/bash
#SBATCH --job-name=bdw_p6_eval
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=00:15:00
#SBATCH --account=tutor
#SBATCH --qos=training
#SBATCH --output=%x-%j.out
#SBATCH --error=%x-%j.err
set -euo pipefail
source "$HOME/bdw-llm/venv_p2/bin/activate"
cd "$HOME/bdw-llm"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
echo "node        : $(hostname)"
echo "date        : $(date -Is)"
echo "python      : $(which python)"
echo "base        : $HOME/bdw-llm/merged/bdw-7b-sft"
echo "adapter     : $HOME/bdw-llm/lora_tools/p6_tool_calling/final"
echo "eval data   : $HOME/bdw-llm/phase6_advanced/tools/data/tool_calls_eval.jsonl"
echo
nvidia-smi -L
echo
python phase6_advanced/tools/evaluate_tools_trained.py "$@"
