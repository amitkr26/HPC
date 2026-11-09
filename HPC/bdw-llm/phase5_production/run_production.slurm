#!/usr/bin/env bash
# =============================================================================
# BerojgarDegreeWala (BDW) - Phase 9 Production 70B Agentic Architecture
#
# Hardware & Topology:
#   Compute Node:  PARAM Rudra rdgpu01 / rdgpu02 (NVIDIA A100 80GB PCIe)
#   Model:         Qwen/Qwen2.5-72B-Instruct + bdw-hardware-lora
#   vLLM Port:     8001 (Internal backend)
#   Agent API:     8000 (FastAPI Interceptor on login node 172.10.0.10)
#   Tunnel:        Dual Cloudflare Tunnel (Named ai.berojgardegreewala.app + Quick)
#   QOS:           training (MaxWall = 00:15:00)
# =============================================================================
#SBATCH --job-name=bdw_72b_prod
#SBATCH --account=tutor
#SBATCH --partition=gpu
#SBATCH --qos=training
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=160G
#SBATCH --time=00:15:00
#SBATCH --output=phase5_production/logs/%x-%j.out
#SBATCH --error=phase5_production/logs/%x-%j.err

set -euo pipefail

echo "============================================================================="
echo "BDW Phase 9: Production 70B Agentic Stack (vLLM + LoRA + FastAPI Interceptor)"
echo "Job ID:    ${SLURM_JOB_ID:-manual}"
echo "Node:      $(hostname)"
echo "Date:      $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "Partition: ${SLURM_JOB_PARTITION:-gpu}"
echo "============================================================================="

PROJECT_DIR="/home/tutor/3ioip3lt/bdw-llm"
DEPLOY_DIR="${PROJECT_DIR}/phase5_production"
LOG_DIR="${DEPLOY_DIR}/logs"

cd "${PROJECT_DIR}"
mkdir -p "${LOG_DIR}"

# 1. Environment & Credentials
ENV_FILE="${DEPLOY_DIR}/.env"
if [ ! -f "${ENV_FILE}" ]; then
    echo "[ERROR] Missing credentials file: ${ENV_FILE}" >&2
    exit 1
fi

set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

if [ -z "${P5_API_KEY:-}" ]; then
    echo "[ERROR] P5_API_KEY is not configured in ${ENV_FILE}" >&2
    exit 1
fi

# 2. Ensure cloudflared binary is available (NFS shared ~/.local/bin)
CLOUDFLARED="${HOME}/.local/bin/cloudflared"
if [ ! -x "${CLOUDFLARED}" ] && ! command -v cloudflared &>/dev/null; then
    echo "Downloading standalone cloudflared binary..."
    mkdir -p "${HOME}/.local/bin"
    curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o "${CLOUDFLARED}"
    chmod +x "${CLOUDFLARED}"
elif command -v cloudflared &>/dev/null; then
    CLOUDFLARED="$(command -v cloudflared)"
fi

echo "cloudflared binary: ${CLOUDFLARED} ($(${CLOUDFLARED} --version 2>&1 | head -n1))"

# 3. Activate Python venv with vLLM
VENV_PATH="${PROJECT_DIR}/venv_p5"
if [ -f "${VENV_PATH}/bin/activate" ]; then
    source "${VENV_PATH}/bin/activate"
else
    echo "[ERROR] vLLM virtualenv not found at ${VENV_PATH}" >&2
    exit 1
fi

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false

# 4. Process Lifecycle Management
VLLM_PID=""
cleanup() {
    echo ""
    echo "Caught termination signal. Tearing down Phase 9 production services..."
    if [ -n "${VLLM_PID}" ] && kill -0 "${VLLM_PID}" 2>/dev/null; then
        echo "Stopping vLLM engine (PID ${VLLM_PID})..."
        kill -TERM "${VLLM_PID}" 2>/dev/null || true
        wait "${VLLM_PID}" 2>/dev/null || true
    fi
    ssh -o StrictHostKeyChecking=no 172.10.0.10 "fuser -k 8001/tcp || true" 2>/dev/null || true
    echo "Services cleanly stopped."
}
trap cleanup EXIT INT TERM

# 5. Model Resolution & Sizing
SNAPSHOT_DIR="${HOME}/.cache/huggingface/hub/models--Qwen--Qwen2.5-72B-Instruct/snapshots"
if [ -d "${SNAPSHOT_DIR}" ]; then
    LATEST_SNAPSHOT=$(ls -d "${SNAPSHOT_DIR}"/* 2>/dev/null | head -n1)
    if [ -n "${LATEST_SNAPSHOT}" ] && [ -d "${LATEST_SNAPSHOT}" ]; then
        MODEL_TARGET="${LATEST_SNAPSHOT}"
    else
        MODEL_TARGET="Qwen/Qwen2.5-72B-Instruct"
    fi
else
    MODEL_TARGET="Qwen/Qwen2.5-72B-Instruct"
fi

MAX_MODEL_LEN="${MAX_MODEL_LEN:-8192}"
GPU_COUNT=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | wc -l || echo 1)

echo "Detected GPU Count: ${GPU_COUNT}"
VLLM_EXTRA_ARGS=()
if [ "${GPU_COUNT}" -ge 2 ]; then
    TP_SIZE="${GPU_COUNT}"
    echo "Multi-GPU configuration: Tensor Parallelism TP=${TP_SIZE}"
else
    TP_SIZE=1
    echo "Single-GPU configuration: TP=1 with 80GB CPU offload for 72B model"
    VLLM_EXTRA_ARGS+=(--cpu-offload-gb 80)
fi

echo "Launching vLLM server in background on 127.0.0.1:8001..."
echo "  Target:       ${MODEL_TARGET}"
echo "  LoRA Adapter: ${HOME}/bdw-llm/training/lora_adapter/"
echo "  Tensor Para:  ${TP_SIZE}"
echo "  Max Context:  ${MAX_MODEL_LEN}"

# Set CUDA and Triton paths so Triton JIT compiles SGMV LoRA kernel cleanly
export CC="/usr/bin/gcc"
export CUDA_HOME="/home/apps/cuda-12.3"
export PATH="/home/apps/cuda-12.3/bin:${PATH}"
export TRITON_LIBCUDA_PATH="${HOME}/libcuda_dir"
export LIBRARY_PATH="${HOME}/libcuda_dir:/home/apps/cuda-12.3/lib64/stubs:/usr/lib64:${LIBRARY_PATH:-}"
export LD_LIBRARY_PATH=/home/apps/cuda-12.3/lib64:/home/apps/openmpi-4.1.5/lib:/home/apps/gcc-12.3/lib64
export CPATH="${HOME}/system_include:/usr/include:${CPATH:-}"
export C_INCLUDE_PATH="${HOME}/system_include:/usr/include:${C_INCLUDE_PATH:-}"

nohup vllm serve "${MODEL_TARGET}" \
    --tensor-parallel-size "${TP_SIZE}" \
    --max-model-len "${MAX_MODEL_LEN}" \
    --gpu-memory-utilization 0.90 \
    --host 127.0.0.1 \
    --port 8001 \
    --api-key "${P5_API_KEY}" \
    --dtype auto \
    --trust-remote-code \
    --enforce-eager \
    --enable-lora \
    --lora-modules bdw-hardware-lora=${HOME}/bdw-llm/training/lora_adapter/ \
    --served-model-name "Qwen/Qwen2.5-72B-Instruct" \
    "${VLLM_EXTRA_ARGS[@]}" \
    > "${LOG_DIR}/vllm.log" 2>&1 &
VLLM_PID=$!
echo "vLLM launched with PID ${VLLM_PID}. Tail logs with: tail -f ${LOG_DIR}/vllm.log"

# 6. Establish Reverse Port Forward to Edge Gateway (login node 172.10.0.10:8001 -> compute 127.0.0.1:8001)
echo "Configuring reverse tunnel to gateway node 172.10.0.10..."
ssh -f -N -R 8001:127.0.0.1:8001 -o StrictHostKeyChecking=no 172.10.0.10 2>/dev/null || true

# 7. Ensure FastAPI Agentic Wrapper and Cloudflare Named Tunnel on 172.10.0.10 are running
echo "Ensuring API server and Cloudflare Tunnels are active on 172.10.0.10..."
ssh -o StrictHostKeyChecking=no 172.10.0.10 "
    # Start api_server.py (port 8000) if not running
    if ! pgrep -f 'api_server.py' >/dev/null 2>&1; then
        nohup ${PROJECT_DIR}/venv_p2/bin/python -u ${PROJECT_DIR}/phase5_production/api_server.py > ${LOG_DIR}/api_server.log 2>&1 &
        echo 'Started api_server.py on 172.10.0.10:8000'
    else
        echo 'api_server.py already active on 172.10.0.10:8000'
    fi

    # Start named tunnel (ai.berojgardegreewala.app) if not running
    if ! pgrep -f 'tunnel.*--token' >/dev/null 2>&1; then
        nohup ${CLOUDFLARED} tunnel --protocol http2 --no-autoupdate run --token '${TUNNEL_TOKEN}' > ${LOG_DIR}/named_tunnel.log 2>&1 &
        echo 'Started named tunnel on 172.10.0.10'
    else
        echo 'Named tunnel already active on 172.10.0.10'
    fi
"

# 8. Also run Quick Tunnel in foreground so Slurm job stays active and logs the trycloudflare.com URL
echo "Launching Cloudflare Quick Tunnel on edge gateway in foreground..."
ssh -o StrictHostKeyChecking=no 172.10.0.10 "${CLOUDFLARED} tunnel --protocol http2 --no-autoupdate --url http://127.0.0.1:8000"
