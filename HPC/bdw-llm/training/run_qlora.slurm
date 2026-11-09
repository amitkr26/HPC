#!/usr/bin/env bash
# =============================================================================
# BerojgarDegreeWala (BDW) — QLoRA 72B Fine-Tuning Slurm Launcher
#
# Hardware & Topology:
#   Compute Node:  PARAM Rudra rdgpu01 / rdgpu02 (NVIDIA A100 80GB PCIe)
#   Model:         Qwen/Qwen2.5-72B-Instruct (NF4 4-bit Quantization)
#   QOS:           training (MaxWall = 00:15:00)
#   Resumption:    Auto-resumes from latest checkpoint-* in checkpoints/
# =============================================================================
#SBATCH --job-name=bdw_72b_qlora
#SBATCH --account=tutor
#SBATCH --partition=gpu
#SBATCH --qos=training
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=160G
#SBATCH --time=00:15:00
#SBATCH --output=training/logs/%x-%j.out
#SBATCH --error=training/logs/%x-%j.err

set -euo pipefail

trap 'echo "[ERROR] Slurm job $SLURM_JOB_ID failed at line $LINENO" >&2' ERR

echo "============================================================================="
echo "BDW Model Fine-Tuning: QLoRA 72B Advanced Reasoning Pipeline"
echo "Job ID:    ${SLURM_JOB_ID:-manual}"
echo "Node:      $(hostname)"
echo "Date:      $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "Partition: ${SLURM_JOB_PARTITION:-gpu}"
echo "============================================================================="

PROJECT_DIR="/home/tutor/3ioip3lt/bdw-llm"
TRAIN_DIR="${PROJECT_DIR}/training"
LOG_DIR="${TRAIN_DIR}/logs"
CHECKPOINT_DIR="${TRAIN_DIR}/checkpoints"
ADAPTER_DIR="${TRAIN_DIR}/lora_adapter"

cd "${PROJECT_DIR}"
mkdir -p "${LOG_DIR}" "${CHECKPOINT_DIR}" "${ADAPTER_DIR}"

# 1. Environment & CUDA
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export OMP_NUM_THREADS=4

# 2. Activate Python Virtual Environment
VENV_PATH="${PROJECT_DIR}/venv_p2"
if [ -f "${VENV_PATH}/bin/activate" ]; then
    source "${VENV_PATH}/bin/activate"
else
    echo "[ERROR] Virtualenv not found at ${VENV_PATH}" >&2
    exit 1
fi

echo "Python: $(which python3)"
python3 -c "import torch; print(f'PyTorch {torch.__version__} | CUDA Available: {torch.cuda.is_available()} | GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"

# 3. Model Resolution
SNAPSHOT_DIR="${HOME}/.cache/huggingface/hub/models--Qwen--Qwen2.5-72B-Instruct/snapshots"
if [ -d "${SNAPSHOT_DIR}" ]; then
    LATEST_SNAPSHOT=$(ls -d "${SNAPSHOT_DIR}"/* 2>/dev/null | head -n1)
    if [ -n "${LATEST_SNAPSHOT}" ] && [ -d "${LATEST_SNAPSHOT}" ]; then
        MODEL_PATH="${LATEST_SNAPSHOT}"
    else
        MODEL_PATH="Qwen/Qwen2.5-72B-Instruct"
    fi
else
    MODEL_PATH="Qwen/Qwen2.5-72B-Instruct"
fi
echo "Target Model: ${MODEL_PATH}"

# 4. Execute QLoRA Training with Auto-Resume and Logging to training.log
echo "Starting QLoRA training script..."
python3 -u "${TRAIN_DIR}/qlora_trainer.py" \
    --model_id "${MODEL_PATH}" \
    --data_path "${TRAIN_DIR}/data/reasoning_train.jsonl" \
    --output_dir "${CHECKPOINT_DIR}" \
    --adapter_dir "${ADAPTER_DIR}" \
    --max_seq_length 1024 \
    --batch_size 1 \
    --grad_accum 4 \
    --learning_rate 2e-4 \
    --save_steps 5 \
    --max_steps 50 \
    2>&1 | tee -a "${TRAIN_DIR}/training.log"

echo "============================================================================="
echo "[SUCCESS] QLoRA execution step completed."
echo "Checkpoints: ${CHECKPOINT_DIR}"
echo "Log:         ${TRAIN_DIR}/training.log"
echo "============================================================================="
