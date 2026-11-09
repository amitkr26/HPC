#!/bin/bash
PROJECT_DIR="${HOME}/bdw-llm"
TRAIN_DIR="${PROJECT_DIR}/training"
LOG_DIR="${TRAIN_DIR}/logs"
mkdir -p "${LOG_DIR}"

cd "${PROJECT_DIR}"

while true; do
    # Check if final adapter is already created (training completed)
    if [ -f "${TRAIN_DIR}/lora_adapter/adapter_model.safetensors" ] || [ -f "${TRAIN_DIR}/lora_adapter/adapter_model.bin" ]; then
        echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') [WATCHDOG] Final adapter detected. Training completed successfully." >> "${LOG_DIR}/watchdog_train.log"
        exit 0
    fi

    # Check if bdw_72b_qlora is running or pending in squeue
    if ! squeue -u 3ioip3lt -O name:30 | grep -q "bdw_72b_qlora"; then
        echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') [WATCHDOG] No bdw_72b_qlora job in queue. Submitting Slurm job with auto-resume..." >> "${LOG_DIR}/watchdog_train.log"
        sbatch training/run_qlora.slurm >> "${LOG_DIR}/watchdog_train.log" 2>&1
    fi
    sleep 20
done
