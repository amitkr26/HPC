#!/bin/bash
#SBATCH -J bdw_gpu_embed
#SBATCH -p gpu
#SBATCH --gres=gpu:1
#SBATCH -c 4
#SBATCH -A tutor
#SBATCH --qos=training
#SBATCH --time=00:10:00
#SBATCH -o /home/tutor/3ioip3lt/bdw-llm/training/study_chunks/gpu_embed.log
#SBATCH -e /home/tutor/3ioip3lt/bdw-llm/training/study_chunks/gpu_embed.err

echo "=== STARTING GPU VECTOR GENERATION ==="
echo "Node: $(hostname)"
echo "Date: $(date -u)"
nvidia-smi

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export CUDA_VISIBLE_DEVICES=0

source /home/tutor/3ioip3lt/bdw-llm/venv_p2/bin/activate
python -u /home/tutor/3ioip3lt/bdw-llm/training/study_chunks/embed_on_gpu.py
echo "=== GPU VECTOR GENERATION COMPLETE ==="
