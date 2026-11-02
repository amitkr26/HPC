#!/usr/bin/env bash
# Zone 3 + Zone 2 stack launcher for PARAM Rudra (P3.4/P3.5 + P4).
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
#
# P4 LoRA wiring (phase4 blueprint §6.1):
#   P4_ADAPTERS=$BASE/export/p4_lora_<domain>.gguf attachments for the
#   five domains.  empty (default) = base model only, exactly P3 behavior;
#   "all" = math,vlsi,embedded,cs,aiml; anything else is a domain csv
#   (order defines llama ids 0..N-1).  Adapters are attached with
#   --lora-init-without-apply so NONE is applied globally; the gateway
#   activates exactly one per request via the request-scoped "lora" field
#   (RoutingDecision.adapter -> llama id from GET /lora-adapters paths).
#   After the health waits each attached adapter gets an /completion probe
#   (P4_PROBE_TOKENS tokens, temperature 0) and the launcher prints
#   RESULT: P4_SERVE_OK domain=<d> id=<i> or P4_SERVE_FAIL domain=<d>.
#
# P4.4 domain tables (blueprint §6.3):
#   P4_DOMAIN_BACKEND=auto|supabase|local (default auto). auto/supabase make
#   the gateway query the dedicated Supabase pgvector tables
#   (public.p4_domain_<domain> via match_p4_<domain>_chunks) and fall back to
#   the local phase4/rag/idx_<domain> npz index on RPC failure/empty hits;
#   local forces the offline npz path.
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

P4_ADAPTERS="${P4_ADAPTERS:-}"
P4_ALL_DOMAINS="math vlsi embedded cs aiml"
if [ "$P4_ADAPTERS" = "all" ]; then
    P4_ADAPTER_LIST="$P4_ALL_DOMAINS"
else
    P4_ADAPTER_LIST=""
    if [ -n "$P4_ADAPTERS" ]; then
        for d in $(echo "$P4_ADAPTERS" | tr ', ' '  '); do
            case " $P4_ALL_DOMAINS " in
                *" $d "*) P4_ADAPTER_LIST="$P4_ADAPTER_LIST $d" ;;
                *) echo "ERROR: unknown P4_ADAPTER domain '$d'" >&2; exit 1 ;;
            esac
        done
    fi
fi
P4_PROBE_TOKENS="${P4_PROBE_TOKENS:-12}"
P4_DOMAIN_BACKEND="${P4_DOMAIN_BACKEND:-auto}"

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
    if [ -s "$RUN_DIR/p4_adapters.env" ]; then
        echo "p4-adapters:  $(cat "$RUN_DIR/p4_adapters.env")"
    else
        echo "p4-adapters:  none"
    fi
    echo "domain-backend: $P4_DOMAIN_BACKEND"
    if [ -n "$P4_ADAPTER_LIST" ] && alive "$PID_LLM"; then
        curl -fsS "http://127.0.0.1:$LLM_PORT/lora-adapters" 2>/dev/null | head -c 400
        echo
    fi
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
for d in $P4_ADAPTER_LIST; do
    if [ ! -f "$BASE/export/p4_lora_$d.gguf" ]; then
        echo "ERROR: P4 adapter missing: $BASE/export/p4_lora_$d.gguf" >&2
        echo "(build it with the blueprint §6 command: convert_lora_to_gguf.py lora_$d/final --base merged/bdw-7b-sft)" >&2
        exit 1
    fi
done

stop_one "$PID_GW" "gateway"
stop_one "$PID_LLM" "llama-server"

echo "llama-server starting (adapters:${P4_ADAPTER_LIST:- none})..." | tee "$LOG_LLM"

LLAMA_ARGS=(-m "$GGUF")
for d in $P4_ADAPTER_LIST; do
    LLAMA_ARGS+=(--lora "$BASE/export/p4_lora_$d.gguf")
done
if [ -n "$P4_ADAPTER_LIST" ]; then
    LLAMA_ARGS+=(--lora-init-without-apply)
fi
echo "llama args: ${LLAMA_ARGS[*]}" >>"$LOG_LLM"
nohup "$LLAMA_BIN" "${LLAMA_ARGS[@]}" --host 127.0.0.1 --port "$LLM_PORT" \
    -c "$CTX" -t "$THREADS" >>"$LOG_LLM" 2>&1 &
echo $! >"$PID_LLM"

if ! wait_http "http://127.0.0.1:$LLM_PORT/health" "llama-server" 60; then
    if alive "$PID_LLM"; then
        echo "   (llama-server log tail:)"
        tail -8 "$LOG_LLM" || true
    fi
    exit 1
fi

nohup env ZONE3_BASE_URL="http://127.0.0.1:$LLM_PORT" \
    ZONE3_TIMEOUT_S="${ZONE3_TIMEOUT_S:-600}" \
    P4_DOMAIN_BACKEND="$P4_DOMAIN_BACKEND" \
    "$PYTHON" -X utf8 "$GW_DIR/app.py" >"$LOG_GW" 2>&1 &
echo $! >"$PID_GW"

if ! wait_http "http://127.0.0.1:$GW_PORT/health" "gateway" 15; then
    exit 1
fi

# P4 bring-up record: which adapters the server actually loaded (ids are
# the gateway's per-request "lora" contract keys).
if [ -n "$P4_ADAPTER_LIST" ]; then
    echo "$P4_ADAPTER_LIST" | tr ' ' '\n' | paste -sd, > "$RUN_DIR/p4_adapters.env"
else
    printf 'none' > "$RUN_DIR/p4_adapters.env"
fi

echo "llama-server pid=$(cat "$PID_LLM") log=$LOG_LLM"
echo "gateway      pid=$(cat "$PID_GW") log=$LOG_GW"
echo "RESULT: P3_STACK_UP llm_port=$LLM_PORT gateway_port=$GW_PORT"

# P4 per-adapter serve probes (blueprint §6.1/§6.4): one tiny /completion
# per attached adapter, activated the same way the gateway will do it
# (request-scoped lora field, scale 1.0). Fails the launch when any probe
# misbehaves so a broken adapter chapter cannot silently survive boot.
probe_failed=0
id=0
for d in $P4_ADAPTER_LIST; do
    body="{\"messages\":[{\"role\":\"user\",\"content\":\"Answer with one or two words: what is a matrix?\"}],\"max_tokens\":$P4_PROBE_TOKENS,\"temperature\":0.0,\"lora\":[{\"id\":$id,\"scale\":1.0}],\"stream\":false}"
    code=$(curl -sS -m 180 -o "$RUN_DIR/p4_probe_$d.json" -w "%{http_code}" \
        -H "Content-Type: application/json" -d "$body" \
        "http://127.0.0.1:$LLM_PORT/v1/chat/completions" 2>/dev/null)
    if [ "$code" != "200" ]; then
        echo "RESULT: P4_SERVE_FAIL domain=$d id=$id http_code=$code"
        probe_failed=1
        id=$((id + 1))
        continue
    fi
    content=$("$PYTHON" -X utf8 -c "import json,sys;print((json.load(open(sys.argv[1],'r',encoding='utf-8'))['choices'][0]['message'].get('content') or '').strip())" "$RUN_DIR/p4_probe_$d.json" 2>/dev/null)
    if [ -n "$content" ]; then
        echo "RESULT: P4_SERVE_OK domain=$d id=$id answer=${content:0:60}"
    else
        echo "RESULT: P4_SERVE_FAIL domain=$d id=$id empty_content"
        probe_failed=1
    fi
    id=$((id + 1))
done
if [ "$probe_failed" != "0" ]; then
    echo "ERROR: one or more P4 adapter probes failed; see $LOG_LLM and $RUN_DIR/p4_probe_*.json" >&2
    exit 1
fi
[ -n "$P4_ADAPTER_LIST" ] && echo "RESULT: P4_SERVE_ALL_OK adapters=$P4_ADAPTER_LIST"
exit 0
