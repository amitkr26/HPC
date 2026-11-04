#!/usr/bin/env bash
# =============================================================================
# BerojgarDegreeWala (BDW) - Phase 5.1 Zero-Cost Production Stack on PARAM Rudra
#
# Fully zero-cost $0 inference architecture:
#   1. vLLM: Serves 70B Frontier Model with Tensor Parallelism TP=2 across
#      2x NVIDIA A100 80GB PCIe GPUs (160 GB total VRAM).
#   2. FastAPI Shim: OpenAI-compatible API (/v1/chat/completions, /v1/models),
#      bearer auth, domain RAG routing, citation hold/release gating,
#      token SSE streaming, and Prometheus /metrics.
#   3. Cloudflare Tunnel (cloudflared): Outbound tunnel bypassing CDAC firewall,
#      exposing the stack publicly at https://ai.berojgardegreewala.com with
#      zero open inbound ports, DDoS protection, and SSL termination.
#
# Hardware & Partition:
#   Compute Nodes: rdgpu01 / rdgpu02 (2x A100 80GB, 192GB RAM)
#   Partition:     gpu (up to 4-day walltime, QOS=normal)
#
# Prerequisites:
#   bash phase5/deploy/prestage_cloudflared.sh   # once on the login node
#   cp phase5/deploy/.env.example phase5/deploy/.env
#   chmod 600 phase5/deploy/.env
#   # fill P5_API_KEY and TUNNEL_TOKEN in .env
#
# Launch command:
#   sbatch phase5/deploy/run_production.slurm
# =============================================================================
#SBATCH --job-name=bdw_70b_prod
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --gres=gpu:2
#SBATCH --cpus-per-task=24
#SBATCH --mem=160G
#SBATCH --time=4-00:00:00
#SBATCH --output=run_production-%j.out
#SBATCH --error=run_production-%j.err

set -euo pipefail

echo "============================================================================="
echo "BDW 70B ZERO-COST PRODUCTION STACK LAUNCH"
echo "Date:      $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "Node:      $(hostname)"
echo "Job ID:    ${SLURM_JOB_ID:-manual}"
echo "Partition: ${SLURM_JOB_PARTITION:-gpu}"
echo "============================================================================="

BDW_HOME="${BDW_HOME:-$HOME/bdw-llm}"
DEPLOY_DIR="$BDW_HOME/phase5/deploy"
RUN_DIR="$DEPLOY_DIR/run"
LOG_DIR="$DEPLOY_DIR/logs"
mkdir -p "$RUN_DIR" "$LOG_DIR"

# ---------------------------------------------------------------------------
# 1. Environment, Secrets and Preflight
# ---------------------------------------------------------------------------
ENV_FILE="$DEPLOY_DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: $ENV_FILE is missing." >&2
    echo "Create it with:" >&2
    echo "  cp $DEPLOY_DIR/.env.example $ENV_FILE && chmod 600 $ENV_FILE" >&2
    exit 1
fi

echo "Loading configuration from $ENV_FILE"
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

if [ -z "${P5_API_KEY:-}" ]; then
    echo "ERROR: P5_API_KEY is not set in $ENV_FILE." >&2
    echo "P5_AUTH_MODE=required cannot start without a bearer key." >&2
    exit 1
fi

if [ -z "${TUNNEL_TOKEN:-}" ]; then
    echo "ERROR: TUNNEL_TOKEN is not set in $ENV_FILE." >&2
    echo "Generate a Cloudflare Tunnel token in Cloudflare Dashboard ->" >&2
    echo "Zero Trust -> Networks -> Tunnels, then add it to .env." >&2
    exit 1
fi

if [ "${P5_AUTH_MODE:-required}" != "required" ]; then
    echo "WARNING: P5_AUTH_MODE=${P5_AUTH_MODE:-unset}; production expects 'required'." >&2
fi

if [ "${P4_DOMAIN_BACKEND:-supabase}" = "supabase" ]; then
    if [ -z "${SUPABASE_URL:-}" ] || [ -z "${SUPABASE_SERVICE_ROLE_KEY:-}" ]; then
        echo "ERROR: P4_DOMAIN_BACKEND=supabase requires SUPABASE_URL and" >&2
        echo "SUPABASE_SERVICE_ROLE_KEY in $ENV_FILE." >&2
        exit 1
    fi
fi

# The 72B weights are already in the shared HF cache. Keep every worker
# offline so a compute node cannot stall on a network/DNS lookup.
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false

# ---------------------------------------------------------------------------
# 2. CUDA & Python Environment
# ---------------------------------------------------------------------------
echo "--- GPU Hardware Verification ---"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader || true

module purge || true
module load cuda/12.3 2>/dev/null || module load cuda/12.1 2>/dev/null || true

# Virtualenv selection
VENV_PATH="$BDW_HOME/venv_p5"
if [ ! -d "$VENV_PATH" ]; then
    VENV_PATH="$BDW_HOME/venv"
fi

if [ -f "$VENV_PATH/bin/activate" ]; then
    echo "Activating virtualenv at $VENV_PATH"
    # shellcheck disable=SC1091
    source "$VENV_PATH/bin/activate"
else
    echo "ERROR: Virtualenv not found at $VENV_PATH" >&2
    exit 1
fi

export PYTHONPATH="$BDW_HOME:${PYTHONPATH:-}"

# ---------------------------------------------------------------------------
# 3. Cloudflared Binary Setup (pre-staged on the login node)
# ---------------------------------------------------------------------------
export PATH="$HOME/.local/bin:$PATH"
CLOUDFLARED_BIN="$HOME/.local/bin/cloudflared"
PREBUILT_CLOUDFLARED="$DEPLOY_DIR/cloudflared/cloudflared"

if [ ! -x "$CLOUDFLARED_BIN" ] && [ -x "$PREBUILT_CLOUDFLARED" ]; then
    echo "Staging cloudflared from $PREBUILT_CLOUDFLARED"
    mkdir -p "$HOME/.local/bin"
    cp -p "$PREBUILT_CLOUDFLARED" "$CLOUDFLARED_BIN"
fi

if ! command -v cloudflared &>/dev/null && [ ! -x "$CLOUDFLARED_BIN" ]; then
    echo "ERROR: cloudflared is not staged at $CLOUDFLARED_BIN." >&2
    echo "Run this once on the login node:" >&2
    echo "  bash $DEPLOY_DIR/prestage_cloudflared.sh" >&2
    exit 1
fi

CLOUDFLARED_CMD="$(command -v cloudflared || printf '%s' "$CLOUDFLARED_BIN")"
echo "Using cloudflared: $($CLOUDFLARED_CMD --version 2>&1 | head -n1)"

# ---------------------------------------------------------------------------
# 4. Service Configuration
# ---------------------------------------------------------------------------
VLLM_PORT=8000
SHIM_PORT=8090
VLLM_MODEL="${VLLM_MODEL:-Qwen/Qwen2.5-72B-Instruct}"
TP_SIZE="${TP_SIZE:-2}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-8192}"
VLLM_GPU_MEM_UTIL="${VLLM_GPU_MEM_UTIL:-0.92}"

PID_VLLM=""
PID_SHIM=""
PID_TUNNEL=""

cleanup() {
    echo ""
    echo "Caught shutdown signal. Stopping BDW production services..."
    if [ -n "$PID_TUNNEL" ] && kill -0 "$PID_TUNNEL" 2>/dev/null; then
        echo "Stopping Cloudflare Tunnel (PID $PID_TUNNEL)..."
        kill -TERM "$PID_TUNNEL" 2>/dev/null || true
    fi
    if [ -n "$PID_SHIM" ] && kill -0 "$PID_SHIM" 2>/dev/null; then
        echo "Stopping FastAPI Shim (PID $PID_SHIM)..."
        kill -TERM "$PID_SHIM" 2>/dev/null || true
    fi
    if [ -n "$PID_VLLM" ] && kill -0 "$PID_VLLM" 2>/dev/null; then
        echo "Stopping vLLM Engine (PID $PID_VLLM)..."
        kill -TERM "$PID_VLLM" 2>/dev/null || true
    fi
    wait "$PID_TUNNEL" "$PID_SHIM" "$PID_VLLM" 2>/dev/null || true
    echo "All services terminated cleanly. Job exiting."
}
trap cleanup EXIT INT TERM

# ---------------------------------------------------------------------------
# 5. Launch vLLM Server (70B Model, Tensor Parallelism = 2)
# ---------------------------------------------------------------------------
echo "Starting vLLM server on port $VLLM_PORT (Model: $VLLM_MODEL, TP=$TP_SIZE)..."

VLLM_ARGS=(
    --model "$VLLM_MODEL"
    --tensor-parallel-size "$TP_SIZE"
    --host 127.0.0.1
    --port "$VLLM_PORT"
    --max-model-len "$MAX_MODEL_LEN"
    --gpu-memory-utilization "$VLLM_GPU_MEM_UTIL"
    --trust-remote-code
    --disable-log-requests
)

# Attach LoRA adapters only when explicitly requested. The Phase-4 adapters
# are 7B-shaped and MUST NOT attach to the 70B base (shape mismatch crashes
# vLLM at load) - set ATTACH_LORA=1 only after a QLoRA retrain produces
# 72B-compatible adapters (locked decision, blueprint sec 15).
if [ "${ATTACH_LORA:-0}" = "1" ] && [ -d "$BDW_HOME/lora_math/final" ] && [ -d "$BDW_HOME/lora_vlsi/final" ]; then
    echo "Attaching Phase 4 domain LoRA adapters to vLLM..."
    VLLM_ARGS+=(
        --enable-lora
        --max-loras 5
        --max-lora-rank 64
        --lora-modules
        "math=$BDW_HOME/lora_math/final"
        "vlsi=$BDW_HOME/lora_vlsi/final"
        "embedded=$BDW_HOME/lora_embedded/final"
        "cs=$BDW_HOME/lora_cs/final"
        "aiml=$BDW_HOME/lora_aiml/final"
    )
fi

nohup python -m vllm.entrypoints.openai.api_server "${VLLM_ARGS[@]}" \
    > "$LOG_DIR/vllm.log" 2>&1 &
PID_VLLM=$!
echo "$PID_VLLM" > "$RUN_DIR/vllm.pid"
echo "vLLM launched (PID $PID_VLLM). Awaiting health endpoint..."

# Wait up to 1800s (30m) for initial 70B weights loading / KV cache allocation
VLLM_TIMEOUT=1800
VLLM_START_TIME=$(date +%s)
while true; do
    if curl -s -f "http://127.0.0.1:$VLLM_PORT/health" >/dev/null 2>&1; then
        echo "vLLM is healthy and ready to serve!"
        break
    fi
    if ! kill -0 "$PID_VLLM" 2>/dev/null; then
        echo "ERROR: vLLM process exited unexpectedly! Log tail:" >&2
        tail -n 25 "$LOG_DIR/vllm.log" >&2
        exit 1
    fi
    ELAPSED=$(( $(date +%s) - VLLM_START_TIME ))
    if [ "$ELAPSED" -gt "$VLLM_TIMEOUT" ]; then
        echo "ERROR: Timed out waiting for vLLM health after ${ELAPSED}s" >&2
        exit 1
    fi
    sleep 5
done

# ---------------------------------------------------------------------------
# 6. Launch FastAPI Production Shim
# ---------------------------------------------------------------------------
echo "Starting BDW FastAPI inference shim on port $SHIM_PORT..."

export ZONE3_BASE_URL="http://127.0.0.1:$VLLM_PORT/v1"
export ZONE3_TIMEOUT_S="${ZONE3_TIMEOUT_S:-300}"
export P5_HOST="127.0.0.1"
export P5_PORT="$SHIM_PORT"
export P5_AUTH_MODE="${P5_AUTH_MODE:-required}"
export P5_STREAM_UPSTREAM="${P5_STREAM_UPSTREAM:-true}"
export P4_DOMAIN_BACKEND="${P4_DOMAIN_BACKEND:-supabase}"

nohup python -m uvicorn phase5.serve.main:create_app --factory \
    --host 127.0.0.1 --port "$SHIM_PORT" \
    > "$LOG_DIR/shim.log" 2>&1 &
PID_SHIM=$!
echo "$PID_SHIM" > "$RUN_DIR/shim.pid"

SHIM_START_TIME=$(date +%s)
while true; do
    if curl -s -f "http://127.0.0.1:$SHIM_PORT/healthz" >/dev/null 2>&1; then
        echo "FastAPI Shim is healthy and ready!"
        break
    fi
    if ! kill -0 "$PID_SHIM" 2>/dev/null; then
        echo "ERROR: Shim process died unexpectedly! Log tail:" >&2
        tail -n 25 "$LOG_DIR/shim.log" >&2
        exit 1
    fi
    ELAPSED=$(( $(date +%s) - SHIM_START_TIME ))
    if [ "$ELAPSED" -gt 60 ]; then
        echo "ERROR: Timed out waiting for Shim health after ${ELAPSED}s" >&2
        exit 1
    fi
    sleep 2
done

# ---------------------------------------------------------------------------
# 7. Launch Cloudflare Tunnel (Outbound Reverse Tunnel)
# ---------------------------------------------------------------------------
echo "Starting Cloudflare Tunnel to expose shim to https://ai.berojgardegreewala.com..."

nohup "$CLOUDFLARED_CMD" tunnel --no-autoupdate run \
    --url "http://127.0.0.1:$SHIM_PORT" \
    --token "$TUNNEL_TOKEN" \
    > "$LOG_DIR/tunnel.log" 2>&1 &
PID_TUNNEL=$!
echo "$PID_TUNNEL" > "$RUN_DIR/tunnel.pid"

sleep 5
if ! kill -0 "$PID_TUNNEL" 2>/dev/null; then
    echo "ERROR: Cloudflare tunnel died on startup! Log tail:" >&2
    tail -n 25 "$LOG_DIR/tunnel.log" >&2
    exit 1
fi
echo "Cloudflare Tunnel is connected! Ingress routing active."

# ---------------------------------------------------------------------------
# 8. Run Local Smoke Certification
# ---------------------------------------------------------------------------
echo "Running local certification probe..."
if ! python "$DEPLOY_DIR/live_probe.py" --url "http://127.0.0.1:$SHIM_PORT" --provider off; then
    echo "ERROR: local P5 live probe failed; refusing to mark the stack ready." >&2
    echo "Inspect $LOG_DIR/shim.log and $LOG_DIR/vllm.log." >&2
    exit 1
fi

echo "============================================================================="
echo "RESULT: P5_PRODUCTION_STACK_READY"
echo "Public Endpoint:  https://ai.berojgardegreewala.com"
echo "Local Shim:       http://127.0.0.1:$SHIM_PORT"
echo "Local vLLM:       http://127.0.0.1:$VLLM_PORT"
echo "============================================================================="

# Keep job active and serving
wait "$PID_SHIM"
