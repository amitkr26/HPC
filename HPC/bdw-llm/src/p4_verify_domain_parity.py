"""P4.4 parity check - Supabase domain RPC vs the local npz index.

For each domain (one canonical query by default) the script embeds the
question with the same staged bge-small-en-v1.5 used by both paths and
retrieves top-k from:

  (a) phase4/rag/idx_<domain>/ (numpy cosine over vectors.npy), and
  (b) the live Supabase RPC match_p4_<domain>_chunks (service role,
      JSON-array embedding, exactly what DomainHybridRetriever sends).

PASS per domain = identical id sets (or local < k) and per-id similarity
delta <= 0.01 (only 6-decimal embedding rounding should differ).

Usage:
  venv/bin/python -X utf8 src/p4_verify_domain_parity.py
  venv/bin/python -X utf8 src/p4_verify_domain_parity.py --domains vlsi,cs
  venv/bin/python -X utf8 src/p4_verify_domain_parity.py --domain vlsi \
      --query "what is hold time"

RESULT: P4_PARITY_<DOM>_OK overlap=8/8 max_delta=0.00012 top1=<id> sim=..
RESULT: P4_PARITY_ALL_OK domains=5
RESULT: P4_PARITY_FAIL <reason>
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAG_DIR = os.path.join(ROOT, "phase4", "rag")
BGE_DIR = os.path.join(ROOT, "phase3", "models", "bge-small-en-v1.5")
ENV_CANDIDATES = [os.path.join(ROOT, "phase3", "gateway", ".env"),
                  os.path.join(ROOT, "phase3", ".env")]
DOMAINS = ("math", "vlsi", "embedded", "cs", "aiml")
QUERIES = {
    "math": "what does Bayes' theorem relate",
    "vlsi": "what is setup and hold time in a flip flop",
    "embedded": "what does a watchdog timer do",
    "cs": "what is the time complexity of binary search",
    "aiml": "what is backpropagation used for",
}


def load_env():
    env = {}
    for path in ENV_CANDIDATES:
        if os.path.isfile(path):
            with open(path, encoding="utf-8-sig") as fh:
                for line in fh:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        k, _, v = line.partition("=")
                        env[k.strip()] = v.strip()
            break
    env.update(os.environ)
    url = env.get("SUPABASE_URL") or env.get("NEXT_PUBLIC_SUPABASE_URL")
    svc = env.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not svc:
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY missing")
    return url.rstrip("/"), svc


def local_topk(domain, q, k):
    import numpy as np
    idx = os.path.join(RAG_DIR, "idx_" + domain)
    vecs = np.load(os.path.join(idx, "vectors.npy"))
    with open(os.path.join(idx, "meta.json"), encoding="utf-8") as fh:
        chunks = json.load(fh)["chunks"]
    scores = vecs @ np.asarray(q, dtype=vecs.dtype)
    top = np.argsort(-scores)[:k]
    return [(str(chunks[i]["id"]), float(scores[i]),
             chunks[i].get("title") or "") for i in top]


def rpc_topk(url, svc, domain, q, k, min_sim):
    payload = {"query_embedding": [round(float(x), 6) for x in q],
               "match_count": int(k),
               "min_similarity": float(min_sim)}
    r = requests.post("%s/rest/v1/rpc/match_p4_%s_chunks" % (url, domain),
                      headers={"apikey": svc,
                               "Authorization": "Bearer " + svc,
                               "Content-Type": "application/json"},
                      data=json.dumps(payload).encode(), timeout=60)
    if r.status_code != 200:
        raise RuntimeError("rpc %s -> %d %s"
                           % (domain, r.status_code, r.text[:160]))
    return [(str(row["id"]), float(row["similarity"]),
             row.get("title") or "") for row in r.json()]


def main():
    ap = argparse.ArgumentParser(description="P4.4 domain parity check")
    ap.add_argument("--domains", default=",".join(DOMAINS))
    ap.add_argument("--domain", default=None)
    ap.add_argument("--query", default=None)
    ap.add_argument("--k", type=int, default=8)
    ap.add_argument("--min-sim", type=float, default=0.30)
    args = ap.parse_args()

    domains = [d.strip() for d in args.domains.split(",") if d.strip()]
    if args.domain:
        domains = [args.domain]
    bad = [d for d in domains if d not in DOMAINS]
    if bad:
        print("RESULT: P4_PARITY_FAIL unknown domain(s): %s" % ",".join(bad))
        return 2

    url, svc = load_env()
    print("supabase   : %s" % urllib.parse.urlparse(url).netloc)

    import torch
    torch.set_num_threads(4)
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(BGE_DIR, device="cpu")

    ok = True
    for d in domains:
        query = args.query if (args.domain and args.query) else QUERIES[d]
        q = model.encode([query], normalize_embeddings=True)[0]
        loc = local_topk(d, q, args.k)
        rpc = rpc_topk(url, svc, d, q, args.k, args.min_sim)
        loc_ids = [x[0] for x in loc]
        rpc_ids = [x[0] for x in rpc]
        overlap = len(set(loc_ids) & set(rpc_ids))
        common = set(loc_ids) & set(rpc_ids)
        delta = max((abs(dict((i, s) for i, s, _ in loc)[i]
                         - dict((i, s) for i, s, _ in rpc)[i])
                     for i in common), default=0.0)
        same = overlap == min(args.k, len(loc_ids)) and delta <= 0.01
        ok = ok and same
        print("== %s q=%r" % (d, query))
        print("   local top1 : %s %.4f %s"
              % (loc[0][0], loc[0][1], loc[0][2]))
        print("   rpc   top1 : %s %.4f %s"
              % (rpc[0][0], rpc[0][1], rpc[0][2]))
        print("RESULT: P4_PARITY_%s_%s overlap=%d/%d max_delta=%.5f "
              "top1=%s sim=%.4f"
              % (d.upper(), "OK" if same else "FAIL", overlap,
                 min(args.k, len(loc_ids)), delta, rpc[0][0], rpc[0][1]))
    print("RESULT: %s" % ("P4_PARITY_ALL_OK domains=%d" % len(domains)
                          if ok else "P4_PARITY_FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001
        import traceback
        traceback.print_exc()
        print("RESULT: P4_PARITY_FAIL %s" % sys.exc_info()[1])
        sys.exit(1)
