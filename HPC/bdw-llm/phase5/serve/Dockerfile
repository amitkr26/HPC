# syntax=docker/dockerfile:1
# P5.0 CPU inference shim. vLLM runs as a separate GPU service (P5.1);
# this image only needs the router + BGE query embedder.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY phase5/serve/requirements.txt /app/phase5/serve/requirements.txt
RUN pip install --no-cache-dir -r /app/phase5/serve/requirements.txt

# Code only: models, adapters, indexes and checkpoints are mounts, never
# baked into the image (.dockerignore excludes them).
COPY phase3 /app/phase3
COPY phase4 /app/phase4
COPY phase5 /app/phase5

RUN addgroup --system --gid 10001 shim \
    && adduser --system --uid 10001 --ingroup shim shim \
    && chown -R shim:shim /app
USER shim

EXPOSE 8090

HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8090/healthz', timeout=2)"

# Secrets and endpoint config come from the host environment/secret store.
# P5_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, ZONE3_BASE_URL,
# PH4_BGE_DIR, PH4_RAG_DIR, P4_DOMAIN_BACKEND.
CMD ["uvicorn", "phase5.serve.main:create_app", "--factory", \
     "--host", "0.0.0.0", "--port", "8090", "--proxy-headers"]
