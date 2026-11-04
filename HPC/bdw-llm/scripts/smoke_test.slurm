#!/bin/bash
#SBATCH --job-name=bdw_f_smoke
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
echo "nproc     : $(nproc)"
echo
nvidia-smi -L
echo
python $HOME/bdw-llm/src/smoke_test.py
rc=$?
echo
echo "SMOKE_STAGE_DONE rc=$rc"
exit $rc
