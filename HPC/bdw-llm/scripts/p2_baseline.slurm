#!/bin/bash
#SBATCH --job-name=bdw_p2base
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
source $HOME/bdw-llm/venv_p2/bin/activate
echo "node      : $(hostname)"
echo "date      : $(date -Is)"
echo "which py  : $(which python)"
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"
echo
ls -lh $HOME/bdw-llm/data/bdw_sft.jsonl
echo
nvidia-smi -L
echo
python $HOME/bdw-llm/src/p2_baseline.py
rc=$?
echo "baseline rc=$rc"
exit $rc
