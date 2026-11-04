#!/usr/bin/env bash
# Pre-stage cloudflared on the PARAM Rudra login node (network-enabled).
# The compute nodes have no reliable outbound network, so run this once
# before submitting run_production.slurm.
#
#   bash phase5/deploy/prestage_cloudflared.sh
#   sbatch phase5/deploy/run_production.slurm
set -euo pipefail

BIN="${CLOUDFLARED_BIN:-$HOME/.local/bin/cloudflared}"
mkdir -p "$(dirname "$BIN")"

if [ -x "$BIN" ]; then
    echo "cloudflared already staged: $BIN"
    "$BIN" --version
    exit 0
fi

case "$(uname -m)" in
    x86_64|amd64) ASSET="cloudflared-linux-amd64" ;;
    aarch64|arm64) ASSET="cloudflared-linux-arm64" ;;
    *)
        echo "ERROR: unsupported architecture: $(uname -m)" >&2
        exit 1
        ;;
esac

URL="https://github.com/cloudflare/cloudflared/releases/latest/download/$ASSET"
TMP="$(mktemp "$BIN.XXXXXX")"
trap 'rm -f "$TMP"' EXIT

echo "Downloading $URL"
curl -fsSL "$URL" -o "$TMP"
chmod 755 "$TMP"
mv -f "$TMP" "$BIN"
trap - EXIT

echo "Staged cloudflared at $BIN"
"$BIN" --version
