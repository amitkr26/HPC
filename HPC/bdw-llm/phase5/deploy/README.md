# phase5/deploy — Zero-Cost Production Stack on PARAM Rudra ($0 Budget)

Runs the **70B-class vLLM server (multi-GPU Tensor Parallelism)**, the **BDW FastAPI inference shim**, and the **Cloudflare Tunnel** entirely on CDAC's **PARAM Rudra HPC cluster** for **$0 additional infrastructure cost**.

```
BDW Web Client / ai-gateway (BDW_AI_BASE_URL=https://ai.berojgardegreewala.com)
                            │ HTTPS
                            ▼
     Cloudflare Global Edge (DDoS protection, SSL termination)
                            │ Outbound Tunnel Connection (bypasses CDAC firewall)
                            ▼
     PARAM Rudra GPU Compute Node (rdgpu01 / rdgpu02)
       ├── cloudflared (tunnel daemon) ──► localhost:8090
       ├── FastAPI Shim (:8090) ──► localhost:8000
       │     (Auth, Domain RAG, Prompt Prefix, Cite Gating, SSE streaming, /metrics)
       └── vLLM (:8000) ──► 2x NVIDIA A100 80GB PCIe (TP=2, 160 GB total VRAM)
```

---

## 1. Zero-Cost ($0) Architecture Principles

1. **Zero External Cloud Spend ($0 Budget)**:
   - No external cloud instances (RunPod, AWS, Lambda Labs, GCP) are used.
   - Computations run on allocated CDAC Param Rudra nodes with dual **NVIDIA A100 80GB PCIe GPUs (160 GB total VRAM)**.
2. **Firewall Ingress via Cloudflare Tunnel**:
   - Param Rudra blocks all inbound internet traffic.
   - `cloudflared` runs directly on the GPU compute node, opening an **outbound** TLS connection to Cloudflare’s global edge.
   - The public endpoint `https://ai.berojgardegreewala.com` routes incoming traffic through this tunnel to the local FastAPI shim on port `8090`. No static public IP or port forwarding is required.
3. **High-Performance Frontier Serving**:
   - 70B model (`Qwen/Qwen2.5-72B-Instruct` or `Llama-3.3-70B-Instruct`) served via **vLLM with Tensor Parallelism (`TP=2`)** across both 80GB A100s.
   - FastAPI shim provides full compatibility with `backend/ai-gateway/src/providers/bdw.ts` in BerojgarDegreeWala.

---

## 2. Directory Files

| File | Purpose |
| --- | --- |
| `run_production.slurm` | **Slurm batch launcher**: starts vLLM (TP=2), FastAPI shim, and Cloudflare Tunnel on Param Rudra |
| `live_probe.py` | **Live certification probe**: validates health, streaming, citations, `/metrics`, and real `bdw.ts` contract |
| `.env.example` | Configuration template (copy to `.env`, `chmod 600`) |
| `CLOUDFLARE_TUNNEL.md` | Runbook for setting up Cloudflare Tunnel token and DNS routing |
| `cloudflared/config.yml` | Ingress rules: blocks `/metrics`, `/debug`, routes all other paths to shim:8090 |
| `slo.json` | Production SLO targets (availability 99.5%, TTFT p95 ≤ 4s) |
| `prometheus.example.yml` | Prometheus scrape configuration for shim `/metrics` |
| `alerts.example.yml` | Alerting rules for latency, error rate, and inflight connection leaks |

---

## 3. Launching on PARAM Rudra

### Step 1: Configure `.env`
On the cluster:
```bash
cd ~/bdw-llm/phase5/deploy
cp .env.example .env
chmod 600 .env
```
Fill in the required secrets:
- `TUNNEL_TOKEN`: Your Cloudflare Zero Trust Tunnel token for `ai.berojgardegreewala.com`.
- `P5_API_KEY`: The shared bearer key used by `BDW_API_KEY` in the Next.js app.
- `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`: For domain RAG table access.

### Step 2: Submit the Slurm Batch Job
```bash
sbatch phase5/deploy/run_production.slurm
```

To monitor job startup:
```bash
squeue --me
tail -f run_production-<job_id>.out
```

### Step 3: Verify Live Public Service
Once the log prints `RESULT: P5_PRODUCTION_STACK_READY`, run the certification probe:
```bash
python phase5/deploy/live_probe.py --url https://ai.berojgardegreewala.com
```
When successful, it emits:
```
RESULT: P5_LIVE_OK
```
