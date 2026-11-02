#!/usr/bin/env bash
# P5.1 host bootstrap: NVIDIA runtime check -> compose validation -> up ->
# smoke. Idempotent; safe to re-run after edits.
#
#   cd phase5/deploy && cp .env.example .env   # then fill in
#   bash bootstrap-host.sh
#
# Emits exactly one of:
#   P5_DEPLOY_SMOKE_OK   shim healthy, OpenAI-compatible endpoint live
#   P5_DEPLOY_SMOKE_FAIL <reason>          (exit 1)
#
# Runs on the GPU host (Ubuntu/Debian assumed for auto-install hints;
# other distros: install docker + nvidia-container-toolkit manually).

set -euo pipefail
cd "$(dirname "$0")"

say()  { printf '[bootstrap] %s\n' "$*"; }
fail() { printf 'P5_DEPLOY_SMOKE_FAIL %s\n' "$*" >&2; exit 1; }

# ---------------------------------------------------------------- env -----
[[ -f .env ]] || fail ".env missing (cp .env.example .env, fill in values)"
set -a; . ./.env; set +a
: "${P5_API_KEY:?P5_API_KEY must be set in .env}"
: "${TUNNEL_TOKEN:?TUNNEL_TOKEN must be set in .env}"
: "${RAG_DIR:?RAG_DIR must be set in .env}"
: "${BGE_DIR:?BGE_DIR must be set in .env}"

# ------------------------------------------------------------- NVIDIA -----
if ! command -v nvidia-smi >/dev/null 2>&1; then
  fail "nvidia-smi not found (install GPU drivers first)"
fi
say "GPU(s): $(nvidia-smi --query-gpu=name --format=csv,noheader | paste -sd ',' -)"
GPU_COUNT=$(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l)
NEED="${TP_SIZE:-2}"
if (( GPU_COUNT < NEED )); then
  fail "TP_SIZE=${NEED} but only ${GPU_COUNT} GPU(s) visible"
fi

# ------------------------------------------------------------- docker -----
if ! command -v docker >/dev/null 2>&1; then
  say "installing docker (distro packages)..."
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker "$USER" || true
  fail "docker installed — log out/in, then re-run this script"
fi
docker compose version >/dev/null 2>&1 || fail "docker compose v2 plugin missing"

if ! docker info 2>/dev/null | grep -qi nvidia; then
  say "installing nvidia-container-toolkit..."
  distribution=$(. /etc/os-release && echo "${ID}${VERSION_ID:-}")
  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
    sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
  curl -fsSL "https://nvidia.github.io/libnvidia-container/${distribution}/libnvidia-container.list" | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list >/dev/null
  sudo apt-get update -qq && sudo apt-get install -y -qq nvidia-container-toolkit
  sudo systemctl restart docker
  docker info 2>/dev/null | grep -qi nvidia || \
    fail "nvidia runtime not visible after install (check /etc/docker/daemon.json)"
fi

# ---------------------------------------------------------- compose up ----
say "validating compose file..."
docker compose config -q || fail "docker compose config rejected the file"

say "building shim + pulling images (vLLM pull is large; first run only)..."
docker compose build shim
docker compose pull vllm cloudflared

say "starting stack..."
docker compose up -d

# --------------------------------------------------------------- smoke ----
SHIM=http://127.0.0.1:8090
# 1) liveness: process is up (public, no auth).
say "waiting for shim ${SHIM}/healthz ..."
for i in $(seq 1 60); do
  if curl -fsS -m 2 "${SHIM}/healthz" >/dev/null 2>&1; then break; fi
  (( i == 60 )) && fail "shim /healthz never became ready (docker compose logs shim)"
  sleep 2
done

# 2) readiness: upstream Zone 3 (vLLM) healthy. Cold model load takes many
#    minutes (weights download + graph capture) — /readyz returns 503 until
#    then. Public endpoint, no auth required.
READY=0
say "waiting for ${SHIM}/readyz (vLLM model load, up to 20 min)..."
for i in $(seq 1 120); do
  if curl -fsS -m 3 "${SHIM}/readyz" >/dev/null 2>&1; then READY=1; break; fi
  sleep 10
done
(( READY == 1 )) || fail "shim /readyz never passed (ZONE3/vLLM down? docker compose logs vllm shim)"

# OpenAI-compat probe (no completion billing: 1 token).
MODELS=$(curl -fsS -m 5 -H "Authorization: Bearer ${P5_API_KEY}" \
         "${SHIM}/v1/models") || fail "GET /v1/models failed"
printf '%s' "${MODELS}" | grep -q '"bdw-career-ai"' || \
  fail "/v1/models missing bdw-career-ai: ${MODELS}"

# /metrics reachable on the private network (edge blocks it).
METRICS_HDR=()
[[ -n "${P5_METRICS_TOKEN:-}" ]] && METRICS_HDR=(-H "Authorization: Bearer ${P5_METRICS_TOKEN}")
curl -fsS -m 3 "${METRICS_HDR[@]}" "${SHIM}/metrics" 2>/dev/null | grep -q \
  'bdw_shim_requests_total' || fail "/metrics missing instruments"

if [[ -z "${P5_METRICS_TOKEN:-}" ]]; then
  say "note: /metrics has no token (P5_METRICS_TOKEN empty) — fine on the private network, edge-blocked"
fi

say "tunnel check: docker compose logs cloudflared | grep -i 'Registered tunnel connection'"
say "edge check:   curl -I https://ai.berojgardegreewala.com/healthz"
echo "P5_DEPLOY_SMOKE_OK"
