#!/usr/bin/env bash
# =============================================================================
# BDW Phase 8: RAG Memory Bank Builder (A100-80GB GPU)
# Embed 35,187 study chunks via BAAI/bge-large-en-v1.5 & upload to Supabase pgvector
# =============================================================================
#SBATCH --job-name=bdw_embed_upload
#SBATCH --account=tutor
#SBATCH --partition=gpu
#SBATCH --qos=training
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=80G
#SBATCH --time=00:15:00
#SBATCH --output=/home/tutor/3ioip3lt/bdw-llm/training/study_chunks/embed_upload.log
#SBATCH --error=/home/tutor/3ioip3lt/bdw-llm/training/study_chunks/embed_upload.err

set -e
PROJECT_DIR="${HOME}/bdw-llm"
cd "${PROJECT_DIR}"

source "${PROJECT_DIR}/venv_p2/bin/activate"

echo "=== STARTING EMBEDDING & UPLOAD PIPELINE ON A100 GPU ==="
echo "Node: $(hostname)"
echo "Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
nvidia-smi

python3 -u training/study_chunks/embed_and_upload.py

echo "=== EMBEDDING & UPLOAD FINISHED SUCCESSFULLY ==="

