# Cloudflare Tunnel Runbook — `ai.berojgardegreewala.com`

P5.1 decision (locked): public DNS on Cloudflare, origin reached **only**
through an outbound Cloudflare Tunnel. The GPU host opens **zero inbound
ports** — no port forwarding, no origin TLS cert to manage.

```
Internet ── HTTPS ──> Cloudflare edge ── outbound conn ──> cloudflared
                                                              │ (compose net)
                                                              v
                                                    shim:8090 ──> vllm:8000
```

## Prerequisites

- Domain `berojgardegreewala.com` **on Cloudflare DNS** (nameservers moved).
- `cloudflared` CLI on the operator machine (for login/create steps only —
  the host itself runs cloudflared via `docker compose`).
- Stack up locally: `cd phase5/deploy && bash bootstrap-host.sh`.

## 1. Authenticate (operator machine)

```bash
cloudflared tunnel login
# opens a browser; pick the zone berojgardegreewala.com and Allow.
# Writes the origin certificate to ~/.cloudflared/cert.pem
```

## 2. Create the tunnel

Dashboard (recommended, token mode) **or** CLI:

```bash
# CLI alternative — creates tunnel + credentials JSON:
cloudflared tunnel create bdw-ai
```

Dashboard path: Cloudflare Zero Trust → Networks → Tunnels → **Create a
tunnel** → Cloudflared connector → name `bdw-ai`. The dashboard then shows
an install command containing the token — copy only the token value.

## 3. Route DNS

```bash
cloudflared tunnel route dns bdw-ai ai.berojgardegreewala.com
# equivalent in the dashboard: Public Hostname
#   Subdomain: ai   Domain: berojgardegreewala.com   Service: (added below)
```

The CNAME `ai.berojgardegreewala.com -> <tunnel-id>.cfargotunnel.com` is
created automatically and is **Proxied** (orange cloud) — required.

## 4. Public hostname mapping

The ingress rules live in
[`cloudflared/config.yml`](cloudflared/config.yml) (mounted into the
container):

| Match                                            | Service             |
| ------------------------------------------------ | ------------------- |
| `ai…/metrics`, `/debug`, `/internal` (any depth) | **404 at edge**     |
| `ai…` (everything else)                          | `http://shim:8090`  |
| anything else                                    | **404**             |

`/metrics` stays reachable on the private network
(`curl 127.0.0.1:8090/metrics`) and is **never** exposed through the CDN.
If you use the dashboard UI instead of the file, reproduce the same three
rules in that order (path-exclusion rule first).

## 5. Token → host

Dashboard → Tunnels → `bdw-ai` → copy **token**. Put it on the GPU host:

```bash
# phase5/deploy/.env
TUNNEL_TOKEN=eyJhIjoi...        # chmod 600 .env; never commit
```

`docker compose up -d cloudflared` (token embeds tunnel ID + credentials —
no `credentials-file` needed).

## 6. Verify

```bash
# tunnel registered?
docker compose logs cloudflared | grep -i 'registered tunnel connection'

# edge -> origin end-to-end (public):
curl -s https://ai.berojgardegreewala.com/healthz          # {"status":"ok",...}
curl -s -H "Authorization: Bearer $P5_API_KEY" \
     https://ai.berojgardegreewala.com/v1/models

# edge blocks metrics:
curl -si https://ai.berojgardegreewala.com/metrics | head -1   # HTTP/... 404

# BDW side (ai-gateway env):  BDW_AI_BASE_URL=https://ai.berojgardegreewala.com
```

Live certification on the real model: run the `P5_LIVE_OK` probe
(blueprint §16) before flipping production traffic.

## 7. Rotation / teardown

- **Rotate token**: dashboard → tunnel → Rotate token → update `.env` →
  `docker compose up -d cloudflared`. Old token dies immediately.
- **Tear down**: `docker compose down` (stack) and delete/disable the
  tunnel + DNS record in the dashboard.
- **Blast radius**: token only grants *this* tunnel. Zone API tokens are
  never stored on the host. Edge exposes only the routes above.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `curl` to edge times out | `docker compose logs cloudflared` — "Registered tunnel connection" present? Token valid? |
| 502/530 from edge | shim down (`docker compose ps`, `logs shim`); `depends_on` should have ordered startup |
| 404 on everything | hostname in config.yml ≠ DNS target, or ingress rule order changed |
| 429/504 through edge | upstream vLLM — see `bdw_shim_upstream_errors_total` on `127.0.0.1:8090/metrics` |
| works locally, fails at edge | path rule mismatch; remember edge-blocked prefixes: `/metrics /debug /internal` |
