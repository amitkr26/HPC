#!/bin/bash
#SBATCH --job-name=bdw_i_eval
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --cpus-per-task=4
#SBATCH --time=00:05:00
#SBATCH --account=tutor
#SBATCH --qos=training
#SBATCH --output=%x-%j.out
#SBATCH --error=%x-%j.err
source $HOME/bdw-llm/env.sh
echo "node      : $(hostname)"
echo "date      : $(date -Is)"
echo "which py  : $(which python)"
nvidia-smi -L
echo
exec python $HOME/bdw-llm/src/eval_model.py "$@"
