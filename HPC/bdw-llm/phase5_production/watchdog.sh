#!/bin/bash
# =============================================================================
# BDW Phase 9 Watchdog: High-Availability Production Daemon
# Maintains vLLM GPU inference job, FastAPI agent server, and Named Tunnel
# =============================================================================

PROJECT_DIR="/home/tutor/3ioip3lt/bdw-llm"
DEPLOY_DIR="${PROJECT_DIR}/phase5_production"
LOG_DIR="${DEPLOY_DIR}/logs"
CLOUDFLARED="${HOME}/.local/bin/cloudflared"

mkdir -p "${LOG_DIR}"
cd "${PROJECT_DIR}"

# Load credentials
if [ -f "${DEPLOY_DIR}/.env" ]; then
    set -a
    source "${DEPLOY_DIR}/.env"
    set +a
fi

echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') [WATCHDOG] Starting BDW Phase 9 Production Watchdog..." >> "${LOG_DIR}/watchdog.log"

while true; do
    # 1. Ensure FastAPI Agentic Wrapper is active on login node port 8000
    if ! pgrep -f 'api_server.py' >/dev/null 2>&1; then
        echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') [WATCHDOG] api_server.py not running. Launching on port 8000..." >> "${LOG_DIR}/watchdog.log"
        nohup ${PROJECT_DIR}/venv_p2/bin/python -u ${DEPLOY_DIR}/api_server.py > "${LOG_DIR}/api_server.log" 2>&1 &
    fi

    # 2. Ensure Cloudflare Named Tunnel is active on login node
    if ! pgrep -f 'tunnel.*--token' >/dev/null 2>&1; then
        if [ -n "${TUNNEL_TOKEN:-}" ]; then
            echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') [WATCHDOG] Named tunnel not running. Launching..." >> "${LOG_DIR}/watchdog.log"
            nohup ${CLOUDFLARED} tunnel --protocol http2 --no-autoupdate run --token "${TUNNEL_TOKEN}" > "${LOG_DIR}/named_tunnel.log" 2>&1 &
        fi
    fi

    # 3. Ensure Slurm GPU job (vLLM 72B + LoRA) is active
    if ! squeue -u 3ioip3lt | grep -q "bdw_72b"; then
        echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') [WATCHDOG] No bdw_72b job in squeue. Submitting run_production.slurm..." >> "${LOG_DIR}/watchdog.log"
        sbatch ${DEPLOY_DIR}/run_production.slurm >> "${LOG_DIR}/watchdog.log" 2>&1
    fi

    sleep 20
done
