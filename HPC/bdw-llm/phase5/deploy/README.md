# phase5/deploy — P5.1 production stack

Brings up the **70B-class vLLM server (multi-GPU TP)**, the **BDW
inference shim**, and the **Cloudflare Tunnel** in one compose project.
No inbound ports on the origin — public ingress is the Tunnel only.

```
BDW ai-gateway (BDW_AI_BASE_URL=https://ai.berojgardegreewala.com)
        │ HTTPS
        ▼
Cloudflare edge ──► cloudflared ──► shim:8090 ──► vllm:8000 (TP=2/4/8)
   (proxied DNS)     (outbound)      (CPU router)    (70B, GPU)
```

## Files

| File | Purpose |
| --- | --- |
| `docker-compose.yml` | vLLM (TP, GPU, HF cache volume) + shim (built from `../serve/Dockerfile`) + cloudflared |
| `.env.example` | full env matrix — copy to `.env` (**chmod 600**, gitignored) |
| `bootstrap-host.sh` | idempotent host setup: NVIDIA runtime → compose validate → up → smoke → `P5_DEPLOY_SMOKE_OK/FAIL` |
| `CLOUDFLARE_TUNNEL.md` | DNS + tunnel runbook (`ai.berojgardegreewala.com`), rotation, troubleshooting |
| `cloudflared/config.yml` | ingress: edge-blocks `/metrics /debug /internal`, everything else → shim |
| `slo.json` | draft SLOs (availability 99.5%, TTFT p95 ≤4 s — re-baseline with `P5_LIVE_OK`) |
| `prometheus.example.yml` | scrape block for `bdw_shim_*` instruments |
| `alerts.example.yml` | example page/ticket rules incl. inflight-leak detector |

## Quickstart (GPU host, Ubuntu/Debian)

```bash
cd phase5/deploy
cp .env.example .env && chmod 600 .env
$EDITOR .env          # P5_API_KEY, TUNNEL_TOKEN, RAG_DIR, BGE_DIR, TP_SIZE…
bash bootstrap-host.sh
# ... first run downloads the 70B weights (large) ...
# → P5_DEPLOY_SMOKE_OK
```

Manual alternative: `docker compose config -q && docker compose up -d`,
then follow the smoke steps inside `bootstrap-host.sh`.

### Sizing knobs (blueprint §8 — "verify at purchase")

| Env | Budget tier | Recommended | Concurrency tier |
| --- | --- | --- | --- |
| `TP_SIZE` | 2 (H100/A100) | 4 | 8 |
| `MAX_MODEL_LEN` | 8192 | 32768 | 32768 |
| GPU interconnect | PCIe acceptable | prefer NVL/SXM | SXM |
| Monthly @ ~730 h | ≈ $4.2k (2×H100-PCIe) | ≈ $8.4k–11.7k | ≈ $23.3k |

`VLLM_MODEL`: `Qwen/Qwen2.5-72B-Instruct` (default, open weights) or
`meta-llama/Llama-3.3-70B-Instruct` (gated → set `HF_TOKEN`).

**LoRA**: the five existing adapters are 7B-shaped and **cannot** attach to
a 70B base. Ship base-only until QLoRA retraining (see blueprint §15 open
item); do not enable `--enable-lora` before then.

## After deploy

1. Tunnel: `docker compose logs cloudflared | grep -i 'registered tunnel connection'`.
2. Edge: `curl https://ai.berojgardegreewala.com/healthz` → `{"status":"ok"…}`.
3. Metrics (private): `curl 127.0.0.1:8090/metrics` (edge returns 404).
4. Point BDW: `BDW_AI_BASE_URL=https://ai.berojgardegreewala.com`.
5. Live certification probe `P5_LIVE_OK` before production traffic (§16).

## Teardown

```bash
docker compose down          # stop stack (keep HF cache volume)
docker compose down -v       # also drop hf-cache volume
```
Plus: disable/delete the tunnel + DNS record (runbook §7).

## Security notes

- `.env` holds the only secrets on the host (shim bearer + tunnel token) —
  `chmod 600`, never committed, rotate per runbook §7.
- vLLM has **no** host port mapping; the shim binds `127.0.0.1:8090` only.
- `/metrics` is edge-blocked; optional `P5_METRICS_TOKEN` bearer for
  private scrapers (independent of `P5_API_KEY`).
- Pin `VLLM_IMAGE` to a digest before production (supply-chain).
