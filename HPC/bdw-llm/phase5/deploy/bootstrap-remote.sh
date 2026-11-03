#!/usr/bin/env bash
# Upload phase5/deploy/.env (and optionally the bdw-llm code) to the GPU host,
# then run bootstrap-host.sh there.
#
# Run on the operator workstation from phase5/deploy after pasting
# TUNNEL_TOKEN into .env. Key auth is required.
#
# Required: GPU_USER, GPU_HOST, GPU_KEY
# Optional: GPU_PORT=22, REMOTE_BDW_DIR=bdw-llm, SYNC_CODE=0
#
# SYNC_CODE=1 copies the current bdw-llm tree (excluding weights/indexes/
# venvs/.git) to REMOTE_BDW_DIR. Leave it 0 when the host already has a
# checkout at that path.

set -euo pipefail
cd "$(dirname "$0")"

say() { printf '[remote] %s\n' "$*"; }
fail() { printf 'P5_REMOTE_BOOTSTRAP_FAIL %s\n' "$*" >&2; exit 1; }
need_var() { [[ -n "${!1:-}" ]] || fail "$1 is required"; }
to_posix() {
  case "$1" in
    [A-Za-z]:[\\/]*)
      if command -v cygpath >/dev/null 2>&1; then
        cygpath -u "$1"
      else
        local drive rest
        drive=$(printf '%s' "${1%%:*}" | tr '[:upper:]' '[:lower:]')
        rest="${1#*:}"
        rest="${rest//\\//}"
        printf '/mnt/%s%s' "$drive" "$rest"
      fi
      ;;
    *)
      printf '%s' "$1"
      ;;
  esac
}

need_var GPU_USER
need_var GPU_HOST
need_var GPU_KEY
GPU_PORT="${GPU_PORT:-22}"
REMOTE_BDW_DIR="${REMOTE_BDW_DIR:-bdw-llm}"
SYNC_CODE="${SYNC_CODE:-0}"

[[ -f .env ]] || fail ".env missing (run this from phase5/deploy)"
set -a
. ./.env
set +a
: "${P5_API_KEY:?P5_API_KEY missing in .env}"
: "${TUNNEL_TOKEN:?TUNNEL_TOKEN missing in .env (paste it first)}"
: "${RAG_DIR:?RAG_DIR missing in .env}"
: "${BGE_DIR:?BGE_DIR missing in .env}"

GPU_KEY="$(to_posix "${GPU_KEY/#\~/$HOME}")"
[[ -f "$GPU_KEY" ]] || fail "GPU_KEY not found: $GPU_KEY"
command -v ssh >/dev/null 2>&1 || fail "ssh not found"
command -v scp >/dev/null 2>&1 || fail "scp not found"

TARGET="${GPU_USER}@${GPU_HOST}"
SSH=(ssh -i "$GPU_KEY" -p "$GPU_PORT" -o StrictHostKeyChecking=accept-new)
SCP=(scp -i "$GPU_KEY" -P "$GPU_PORT" -o StrictHostKeyChecking=accept-new)

say "checking ${TARGET}:${GPU_PORT}"
"${SSH[@]}" "$TARGET" "mkdir -p '$REMOTE_BDW_DIR/phase5/deploy'" \
  || fail "cannot reach host or create $REMOTE_BDW_DIR"

if [[ "$SYNC_CODE" == "1" ]]; then
  say "syncing bdw-llm code to ${TARGET}:${REMOTE_BDW_DIR}"
  tar -czf - \
    --exclude='.git' --exclude='./.git' \
    --exclude='venv*' --exclude='./venv*' \
    --exclude='__pycache__' --exclude='*.pyc' \
    --exclude='.env' --exclude='./.env' \
    --exclude='phase5/deploy/.env' --exclude='./phase5/deploy/.env' \
    --exclude='phase3/models' --exclude='./phase3/models' \
    --exclude='phase4/rag/idx_*' --exclude='./phase4/rag/idx_*' \
    --exclude='checkpoints*' --exclude='./checkpoints*' \
    --exclude='export' --exclude='./export' \
    --exclude='logs' --exclude='./logs' \
    --exclude='*.gguf' --exclude='*.log' \
    -C ../.. . | "${SSH[@]}" "$TARGET" "tar -xzf - -C '$REMOTE_BDW_DIR'" \
    || fail "code sync failed"
fi

say "uploading .env"
"${SCP[@]}" .env "$TARGET:$REMOTE_BDW_DIR/phase5/deploy/.env" \
  || fail ".env upload failed"

say "running bootstrap-host.sh on ${TARGET} (this can take 20+ minutes)"
"${SSH[@]}" -t "$TARGET" \
  "chmod 600 '$REMOTE_BDW_DIR/phase5/deploy/.env' && \
   cd '$REMOTE_BDW_DIR/phase5/deploy' && bash bootstrap-host.sh"
