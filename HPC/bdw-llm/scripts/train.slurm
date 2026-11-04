#!/bin/bash
#SBATCH --job-name=bdw_g_train
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
echo "checkpoint before this run:"
ls -l $HOME/bdw-llm/checkpoints/step_*.pt 2>/dev/null | tail -5 || echo "  (none)"
echo
nvidia-smi -L
echo
exec python $HOME/bdw-llm/src/train.py "$@"
