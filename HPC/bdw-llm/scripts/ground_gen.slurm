#!/bin/bash
#SBATCH --job-name=bdw_ground
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
echo "context file (Stage O.1):"
ls -lh $HOME/bdw-llm/data/raw/vlsi_wikipedia.json
echo
echo "teacher (offline):"
ls -lh $HOME/bdw-llm/teacher_model_7b/model.safetensors.index.json
echo
echo "resume state (grounded_qa.jsonl):"
wc -l $HOME/bdw-llm/data/grounded_qa.jsonl 2>/dev/null || echo "  (none yet -- full run)"
echo
nvidia-smi -L
echo
exec python $HOME/bdw-llm/src/generate_grounded_qa.py "$@"
