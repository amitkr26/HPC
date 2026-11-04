#!/bin/bash
#SBATCH --job-name=bdw_p6tools
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=00:15:00
#SBATCH --account=tutor
#SBATCH --qos=training
#SBATCH --output=/home/tutor/3ioip3lt/bdw-llm/phase6_advanced/tools/eval/%x-%j.out
#SBATCH --error=/home/tutor/3ioip3lt/bdw-llm/phase6_advanced/tools/eval/%x-%j.err

set -euo pipefail
source "$HOME/bdw-llm/venv_p2/bin/activate"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false

echo "node      : $(hostname)"
echo "date      : $(date -Is)"
echo "which py  : $(which python)"
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"
nvidia-smi -L
echo

python "$HOME/bdw-llm/phase6_advanced/tools/evaluate_tools_baseline.py" "$@"
rc=$?
echo "baseline rc=$rc"
exit $rc
