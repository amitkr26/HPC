#!/usr/bin/env bash
# Zone 3 + Zone 2 stack launcher for PARAM Rudra (P3.4/P3.5 prep).
#
# Boots the offline llama.cpp server (merged GGUF) and the Zone 2 gateway,
# health-checks both, and writes pidfiles for clean restarts. Run on the
# cluster (login or a GPU node via srun); no root, no internet needed.
#
#   ./run_stack.sh            start (or restart) the stack
#   ./run_stack.sh --stop     stop both services
#   ./run_stack.sh --status   report state of both services
#
# Env overrides: LLAMA_BIN, GGUF, CTX, THREADS, LLM_PORT, GW_PORT, GW_DIR
set -u

BASE="${BDW_HOME:-$HOME/bdw-llm}"
LLAMA_BIN="${LLAMA_BIN:-$BASE/llama_cpp/build/bin/llama-server}"
GGUF="${GGUF:-$BASE/merged/bdw-7b-sft-Q4_K_M.gguf}"
CTX="${CTX:-4096}"
THREADS="${THREADS:-4}"
LLM_PORT="${LLM_PORT:-8081}"
GW_PORT="${GW_PORT:-8787}"
GW_DIR="${GW_DIR:-$BASE/phase3/gateway}"
PYTHON="${PYTHON:-$BASE/venv/bin/python3}"
[ ! -x "$PYTHON" ] && PYTHON="python3"
RUN_DIR="$BASE/run"
LOG_LLM="$RUN_DIR/llama.log"
LOG_GW="$RUN_DIR/gateway.log"
PID_LLM="$RUN_DIR/llama.pid"
PID_GW="$RUN_DIR/gateway.pid"

mkdir -p "$RUN_DIR"

alive() { [ -f "$1" ] && kill -0 "$(cat "$1")" 2>/dev/null; }

stop_one() { # pidfile name
    if alive "$1"; then
        kill "$(cat "$1")" 2>/dev/null
        echo "stopped $2 (pid $(cat "$1"))"
    fi
    rm -f "$1"
}

wait_http() { # url name tries
    for _ in $(seq 1 "$3"); do
        if curl -fsS -o /dev/null "$1" 2>/dev/null; then
            echo "$2 up: $1"
            return 0
        fi
        sleep 2
    done
    echo "ERROR: $2 did not come up ($1); see its log"
    return 1
}

case "${1:-}" in
--stop)
    stop_one "$PID_GW" "gateway"
    stop_one "$PID_LLM" "llama-server"
    echo "RESULT: P3_STACK_STOPPED"
    exit 0
    ;;
--status)
    if alive "$PID_LLM"; then echo "llama-server: RUNNING (pid $(cat "$PID_LLM"))"; else echo "llama-server: DOWN"; fi
    if alive "$PID_GW"; then echo "gateway:      RUNNING (pid $(cat "$PID_GW"))"; else echo "gateway:      DOWN"; fi
    exit 0
    ;;
esac

if [ ! -x "$LLAMA_BIN" ]; then
    echo "ERROR: llama-server not found at $LLAMA_BIN" >&2
    exit 1
fi
if [ ! -f "$GGUF" ]; then
    echo "ERROR: merged GGUF not found at $GGUF" >&2
    exit 1
fi
if [ ! -f "$GW_DIR/app.py" ]; then
    echo "ERROR: gateway app.py not found at $GW_DIR/app.py" >&2
    exit 1
fi
if [ ! -f "$GW_DIR/.env" ]; then
    echo "ERROR: $GW_DIR/.env missing - SFTP the phase3/.env next to app.py" >&2
    exit 1
fi

stop_one "$PID_GW" "gateway"
stop_one "$PID_LLM" "llama-server"

nohup "$LLAMA_BIN" -m "$GGUF" --host 127.0.0.1 --port "$LLM_PORT" \
    -c "$CTX" -t "$THREADS" >"$LOG_LLM" 2>&1 &
echo $! >"$PID_LLM"

nohup env ZONE3_BASE_URL="http://127.0.0.1:$LLM_PORT" \
    ZONE3_TIMEOUT_S="${ZONE3_TIMEOUT_S:-300}" \
    "$PYTHON" -X utf8 "$GW_DIR/app.py" >"$LOG_GW" 2>&1 &
echo $! >"$PID_GW"

if ! wait_http "http://127.0.0.1:$LLM_PORT/health" "llama-server" 60; then
    exit 1
fi
if ! wait_http "http://127.0.0.1:$GW_PORT/health" "gateway" 15; then
    exit 1
fi

echo "llama-server pid=$(cat "$PID_LLM") log=$LOG_LLM"
echo "gateway      pid=$(cat "$PID_GW") log=$LOG_GW"
echo "RESULT: P3_STACK_UP llm_port=$LLM_PORT gateway_port=$GW_PORT"
