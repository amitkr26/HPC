#!/usr/bin/env bash
# Copy Phase 4 RAG indexes + BGE-small from PARAM Rudra to the P5 GPU host.
#
# Run on the operator workstation. The cluster leg uses interactive SSH
# (password + captcha); the GPU leg uses key auth.
#
#   SYNC_MODE=all  cluster -> local staging -> GPU host   (default)
#   SYNC_MODE=pull cluster -> local staging
#   SYNC_MODE=push local staging -> GPU host
#
# Required for push: GPU_USER, GPU_HOST, GPU_KEY.
# Optional: GPU_PORT=22, RAG_DIR=/srv/bdw/rag, BGE_DIR=/srv/bdw/bge,
#           PR_USER=3ioip3lt, PR_HOST=paramrudra.cdacdelhi.in, PR_PORT=4422,
#           PR_BDW_DIR=bdw-llm (relative to the cluster home),
#           STAGE_DIR=/tmp/p5-artifacts, KEEP_STAGE=1, REMOTE_SUDO=1.
#
# A pull-only run prints the staging path; pass the same STAGE_DIR (and
# KEEP_STAGE=1) to a later push-only run.

set -euo pipefail
cd "$(dirname "$0")"

say() { printf '[sync] %s\n' "$*"; }
fail() { printf 'P5_ARTIFACTS_SYNC_FAIL %s\n' "$*" >&2; exit 1; }
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

SYNC_MODE="${SYNC_MODE:-all}"
PR_USER="${PR_USER:-3ioip3lt}"
PR_HOST="${PR_HOST:-paramrudra.cdacdelhi.in}"
PR_PORT="${PR_PORT:-4422}"
PR_BDW_DIR="${PR_BDW_DIR:-bdw-llm}"
RAG_DIR="${RAG_DIR:-/srv/bdw/rag}"
BGE_DIR="${BGE_DIR:-/srv/bdw/bge}"
STAGE_DIR="${STAGE_DIR:-}"
KEEP_STAGE="${KEEP_STAGE:-0}"
REMOTE_SUDO="${REMOTE_SUDO:-0}"

case "$SYNC_MODE" in
  all|pull|push) ;;
  *) fail "SYNC_MODE must be pull|push|all (got $SYNC_MODE)" ;;
esac
STAGE_DIR="$(to_posix "$STAGE_DIR")"
command -v scp >/dev/null 2>&1 || fail "scp not found"
command -v ssh >/dev/null 2>&1 || fail "ssh not found"

if [[ "$SYNC_MODE" == "pull" || "$SYNC_MODE" == "all" ]]; then
  STAGE_DIR="${STAGE_DIR:-$(mktemp -d "${TMPDIR:-/tmp}/p5-artifacts.XXXXXX")}"
  mkdir -p "$STAGE_DIR"
  rm -rf "$STAGE_DIR/rag" "$STAGE_DIR/bge"
  say "pulling ${PR_BDW_DIR}/phase4/rag from ${PR_USER}@${PR_HOST}:${PR_PORT}"
  scp -P "$PR_PORT" -r \
    "${PR_USER}@${PR_HOST}:${PR_BDW_DIR}/phase4/rag" \
    "$STAGE_DIR/rag" || fail "cluster scp of phase4/rag failed"
  say "pulling ${PR_BDW_DIR}/phase3/models/bge-small-en-v1.5"
  scp -P "$PR_PORT" -r \
    "${PR_USER}@${PR_HOST}:${PR_BDW_DIR}/phase3/models/bge-small-en-v1.5" \
    "$STAGE_DIR/bge" || fail "cluster scp of BGE failed"
fi

if [[ "$SYNC_MODE" == "push" || "$SYNC_MODE" == "all" ]]; then
  need_var GPU_USER
  need_var GPU_HOST
  need_var GPU_KEY
  GPU_KEY="$(to_posix "${GPU_KEY/#\~/$HOME}")"
  STAGE_DIR="$(to_posix "$STAGE_DIR")"
  [[ -f "$GPU_KEY" ]] || fail "GPU_KEY not found: $GPU_KEY"
  : "${STAGE_DIR:?STAGE_DIR is required for SYNC_MODE=push}"
  [[ -d "$STAGE_DIR/rag" ]] || fail "missing $STAGE_DIR/rag"
  [[ -d "$STAGE_DIR/bge" ]] || fail "missing $STAGE_DIR/bge"

  GPU_PORT="${GPU_PORT:-22}"
  TARGET="${GPU_USER}@${GPU_HOST}"
  SSH=(ssh -i "$GPU_KEY" -p "$GPU_PORT" -o StrictHostKeyChecking=accept-new)
  SCP=(scp -i "$GPU_KEY" -P "$GPU_PORT" -o StrictHostKeyChecking=accept-new)

  say "preparing ${RAG_DIR} and ${BGE_DIR} on ${TARGET}"
  if [[ "$REMOTE_SUDO" == "1" ]]; then
    "${SSH[@]}" "$TARGET" \
      "sudo mkdir -p '$RAG_DIR' '$BGE_DIR' && sudo chown -R \$(id -u):\$(id -g) '$RAG_DIR' '$BGE_DIR'" \
      || fail "cannot prepare destination directories (REMOTE_SUDO=2?)"
  else
    "${SSH[@]}" "$TARGET" "mkdir -p '$RAG_DIR' '$BGE_DIR'" \
      || fail "cannot create destination directories (try REMOTE_SUDO=1)"
  fi

  say "uploading RAG indexes..."
  "${SCP[@]}" -r "$STAGE_DIR/rag/." "$TARGET:$RAG_DIR/" \
    || fail "scp of RAG indexes failed"
  say "uploading BGE model..."
  "${SCP[@]}" -r "$STAGE_DIR/bge/." "$TARGET:$BGE_DIR/" \
    || fail "scp of BGE model failed"

  say "verifying remote artifacts..."
  "${SSH[@]}" "$TARGET" \
    "test -s '$RAG_DIR/idx_math/vectors.npy' && \
     test -s '$RAG_DIR/idx_vlsi/vectors.npy' && \
     test -s '$RAG_DIR/idx_embedded/vectors.npy' && \
     test -s '$RAG_DIR/idx_cs/vectors.npy' && \
     test -s '$RAG_DIR/idx_aiml/vectors.npy' && \
     test -s '$BGE_DIR/config.json' && \
     test -s '$BGE_DIR/model.safetensors'" \
    || fail "remote artifact verification failed"
fi

if [[ -n "$STAGE_DIR" && "$KEEP_STAGE" != "1" && "$SYNC_MODE" != "push" ]]; then
  say "removing staging directory $STAGE_DIR"
  rm -rf "$STAGE_DIR"
elif [[ -n "$STAGE_DIR" ]]; then
  say "staging directory kept: $STAGE_DIR"
fi

echo "P5_ARTIFACTS_SYNC_OK"
