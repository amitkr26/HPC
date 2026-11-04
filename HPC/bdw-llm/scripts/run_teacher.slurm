#!/bin/bash
#SBATCH --job-name=bdw_teach
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --cpus-per-task=4
#SBATCH --time=00:15:00
#SBATCH --account=tutor
#SBATCH --qos=training
#SBATCH --output=%x-%j.out
#SBATCH --error=%x-%j.err
source $HOME/bdw-llm/env.sh
echo "node      : $(hostname)"
echo "date      : $(date -Is)"
echo "which py  : $(which python)"
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"
echo
echo "teacher model (offline, downloaded on login node):"
ls -lh $HOME/bdw-llm/teacher_model_7b/ | tail -8
echo
echo "no network on this node (for reference):"
getent hosts huggingface.co || echo "  huggingface.co UNRESOLVED (expected)"
echo
nvidia-smi -L
echo
exec python $HOME/bdw-llm/src/generate_teacher_data.py "$@"
