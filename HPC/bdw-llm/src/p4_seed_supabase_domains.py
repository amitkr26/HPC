"""P4.4 - seed the Supabase per-domain pgvector tables (LOGIN node).

Mirrors phase4/rag/idx_<domain>/ (built by p4_build_rag_index.py) into the
tables created by phase4/supabase/migrations/0003_p4_domain_chunks.sql:

    idx_math      -> public.p4_domain_math
    idx_vlsi      -> public.p4_domain_vlsi
    idx_embedded  -> public.p4_domain_embedded
    idx_cs        -> public.p4_domain_cs
    idx_aiml      -> public.p4_domain_aiml
    manifest      -> public.p4_domain_index_manifest (provenance row)

Transport is PostgREST with the service-role key (the Zone 2 gateway uses the
same credentials). Writes are idempotent upserts on the local chunk id, so a
re-run reconciles instead of duplicating. Embeddings are sent as pgvector
text literals ("[0.1,0.2,...]"); if PostgREST rejects the text form the batch
is retried with a JSON array (both are valid PostgREST inputs for vector).

Per domain the run proves three things before printing OK:
  1. table row count == meta.json n (HEAD/GET with Prefer: count=exact),
  2. the domain RPC returns rows for a real embedding,
  3. self-match: for 3 deterministic chunks, the RPC returns the chunk
     itself with similarity >= 0.999 (cosine identity).

Env resolution matches phase3/gateway/app.py: phase3/gateway/.env first,
then os.environ overrides. Only the Supabase host is ever printed.

Usage:
  venv/bin/python -X utf8 src/p4_seed_supabase_domains.py --dry-run
  venv/bin/python -X utf8 src/p4_seed_supabase_domains.py
  venv/bin/python -X utf8 src/p4_seed_supabase_domains.py --verify-only
  venv/bin/python -X utf8 src/p4_seed_supabase_domains.py --domains vlsi,cs

RESULT: P4_SEED_<DOM>_OK rows=.. count=.. self_top1=.. sim=..
RESULT: P4_SEED_ALL_OK domains=5 rows=..
RESULT: P4_SEED_FAIL <reason>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.parse

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAG_DIR = os.path.join(ROOT, "phase4", "rag")
ENV_CANDIDATES = [os.path.join(ROOT, "phase3", "gateway", ".env"),
                  os.path.join(ROOT, "phase3", ".env")]
DOMAINS = ("math", "vlsi", "embedded", "cs", "aiml")
BATCH = 25


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
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY missing "
                           "(phase3/gateway/.env or environment)")
    return url.rstrip("/"), svc


def md5_bytes(data):
    return hashlib.md5(data).hexdigest()


def table(domain):
    return "p4_domain_" + domain


def vec_text(vec, nd=6):
    return "[" + ",".join("%.*f" % (nd, float(x)) for x in vec) + "]"


def load_index(domain):
    import numpy as np
    idx_dir = os.path.join(RAG_DIR, "idx_" + domain)
    with open(os.path.join(idx_dir, "meta.json"), encoding="utf-8") as fh:
        meta = json.load(fh)
    vecs = np.load(os.path.join(idx_dir, "vectors.npy"))
    if vecs.ndim != 2 or vecs.shape[1] != 384:
        raise RuntimeError("bad vector shape %r" % (vecs.shape,))
    if len(meta["chunks"]) != vecs.shape[0]:
        raise RuntimeError("meta/vectors drift %d vs %d"
                           % (len(meta["chunks"]), vecs.shape[0]))
    norms = np.linalg.norm(vecs, axis=1)
    if float(norms.min()) < 0.999 or float(norms.max()) > 1.001:
        raise RuntimeError("rows not L2-normalised: [%f, %f]"
                           % (norms.min(), norms.max()))
    with open(os.path.join(idx_dir, "vectors.npy"), "rb") as fh:
        vec_md5 = md5_bytes(fh.read())
    with open(os.path.join(idx_dir, "meta.json"), "rb") as fh:
        meta_md5 = md5_bytes(fh.read())
    return meta, vecs, md5_bytes((vec_md5 + meta_md5).encode())


def auth_headers(url, svc, prefer=None):
    h = {"apikey": svc, "Authorization": "Bearer " + svc,
         "Content-Type": "application/json"}
    if prefer:
        h["Prefer"] = prefer
    return h


def post_rows(url, svc, table_name, rows, conflict, timeout):
    body = json.dumps(rows, ensure_ascii=False).encode("utf-8")
    r = requests.post("%s/rest/v1/%s?on_conflict=%s"
                      % (url, table_name, conflict),
                      headers=auth_headers(
                          url, svc,
                          "resolution=merge-duplicates,return=minimal"),
                      data=body, timeout=timeout)
    if r.status_code in (200, 201, 204):
        return
    # Fallback: some PostgREST versions reject vector text literals but accept
    # JSON arrays for the vector input function.
    if r.status_code == 400 and "vector" in (r.text or "").lower():
        alt = []
        for row in rows:
            row = dict(row)
            row["embedding"] = json.loads(row["embedding"])
            alt.append(row)
        r2 = requests.post("%s/rest/v1/%s?on_conflict=%s"
                           % (url, table_name, conflict),
                           headers=auth_headers(
                               url, svc,
                               "resolution=merge-duplicates,return=minimal"),
                           data=json.dumps(alt, ensure_ascii=False).encode(),
                           timeout=timeout)
        if r2.status_code in (200, 201, 204):
            return
        raise RuntimeError("upsert %s -> %d %s"
                           % (table_name, r2.status_code, r2.text[:160]))
    raise RuntimeError("upsert %s -> %d %s"
                       % (table_name, r.status_code, r.text[:160]))


def truncate_table(url, svc, table_name, timeout):
    r = requests.delete("%s/rest/v1/%s?id=not.is.null" % (url, table_name),
                        headers=auth_headers(url, svc), timeout=timeout)
    if r.status_code not in (200, 204):
        raise RuntimeError("truncate %s -> %d %s"
                           % (table_name, r.status_code, r.text[:120]))


def count_rows(url, svc, table_name, timeout):
    r = requests.get("%s/rest/v1/%s?select=id" % (url, table_name),
                     headers=dict(auth_headers(url, svc, "count=exact"),
                                  Range="0-0"),
                     timeout=timeout)
    if r.status_code not in (200, 206):
        raise RuntimeError("count %s -> %d %s"
                           % (table_name, r.status_code, r.text[:120]))
    cr = r.headers.get("content-range") or ""
    if "/" not in cr:
        raise RuntimeError("count %s: no content-range %r" % (table_name, cr))
    return int(cr.rsplit("/", 1)[1])


def rpc(url, svc, fn, payload, timeout):
    r = requests.post("%s/rest/v1/rpc/%s" % (url, fn),
                      headers=auth_headers(url, svc),
                      data=json.dumps(payload).encode(), timeout=timeout)
    if r.status_code == 200:
        return r.json()
    if r.status_code == 400 and "vector" in (r.text or "").lower():
        payload = dict(payload)
        payload["query_embedding"] = json.loads(payload["query_embedding"])
        r2 = requests.post("%s/rest/v1/rpc/%s" % (url, fn),
                           headers=auth_headers(url, svc),
                           data=json.dumps(payload).encode(), timeout=timeout)
        if r2.status_code == 200:
            return r2.json()
        raise RuntimeError("rpc %s -> %d %s"
                           % (fn, r2.status_code, r2.text[:160]))
    raise RuntimeError("rpc %s -> %d %s" % (fn, r.status_code, r.text[:160]))


def seed_domain(url, svc, domain, args, stats):
    import numpy as np
    meta, vecs, index_md5 = load_index(domain)
    n = len(meta["chunks"])
    tbl = table(domain)
    print("== %s: rows=%d dim=%d embedder=%s"
          % (domain, n, meta["dim"], meta.get("model", "?")), flush=True)

    if not args.verify_only:
        if getattr(args, "truncate", False):
            truncate_table(url, svc, tbl, args.timeout)
            print("  table truncated before seeding", flush=True)
        rows = []
        for i, chunk in enumerate(meta["chunks"]):
            rows.append({"id": str(chunk["id"]),
                         "domain": domain,
                         "title": chunk.get("title") or "",
                         "source_url": chunk.get("url") or "",
                         "content": chunk.get("text") or "",
                         "embedding": vec_text(vecs[i])})
        total = (len(rows) + args.batch - 1) // args.batch
        for b in range(total):
            batch = rows[b * args.batch:(b + 1) * args.batch]
            post_rows(url, svc, tbl, batch, "id", args.timeout)
            print("  batch %d/%d rows=%d" % (b + 1, total, len(batch)),
                  flush=True)
        post_rows(url, svc, "p4_domain_index_manifest",
                  [{"domain": domain,
                    "embedder": meta.get("model") or "",
                    "dim": int(meta["dim"]),
                    "n": n,
                    "built_at": meta.get("built_at"),
                    "source_manifest_md5": index_md5,
                    "notes": "seeded from phase4/rag/idx_%s" % domain}],
                  "domain", args.timeout)
        print("  manifest upserted (md5=%s)" % index_md5[:12], flush=True)

    count = count_rows(url, svc, tbl, args.timeout)
    if count != n:
        raise RuntimeError("row count %d != meta n %d" % (count, n))

    # self-match on 3 deterministic chunks (same idea as the local self-test)
    bases = sorted({int(hashlib.md5((domain + str(k)).encode())
                        .hexdigest(), 16) % n for k in range(3)})
    checks, top1_id, top1_sim = 0, None, 0.0
    for base in bases:
        payload = {"query_embedding": vec_text(vecs[base]),
                   "match_count": 8, "min_similarity": 0.0}
        rows = rpc(url, svc, "match_p4_%s_chunks" % domain, payload,
                   args.timeout)
        if not rows:
            raise RuntimeError("rpc returned no rows for chunk %d"
                               % base)
        want = str(meta["chunks"][base]["id"])
        got = next((r for r in rows if str(r.get("id")) == want), None)
        sim = float(got["similarity"]) if got else -1.0
        if sim < 0.999:
            raise RuntimeError("self-match chunk %s sim=%.4f"
                               % (want, sim))
        checks += 1
        if top1_sim == 0.0:
            top1_id, top1_sim = want, sim
    print("RESULT: P4_SEED_%s_OK rows=%d count=%d self_checks=%d "
          "self_top1=%s sim=%.4f"
          % (domain.upper(), n, count, checks, top1_id, top1_sim))
    stats.append((domain, n, count))


def main():
    ap = argparse.ArgumentParser(description="P4.4 Supabase domain seed")
    ap.add_argument("--domains", default=",".join(DOMAINS))
    ap.add_argument("--batch", type=int, default=BATCH)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--truncate", action="store_true", help="truncate table before seeding")
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--fail-fast", action="store_true")
    args = ap.parse_args()

    domains = [d.strip() for d in args.domains.split(",") if d.strip()]
    bad = [d for d in domains if d not in DOMAINS]
    if bad:
        print("RESULT: P4_SEED_FAIL unknown domain(s): %s" % ",".join(bad))
        return 2

    if args.dry_run:
        for d in domains:
            meta, vecs, index_md5 = load_index(d)
            print("%-9s table=public.%s rows=%d dim=%d md5=%s id0=%r"
                  % (d, table(d), len(meta["chunks"]), meta["dim"],
                     index_md5[:12], str(meta["chunks"][0]["id"])))
        print("RESULT: P4_SEED_DRYRUN_OK domains=%d rows=%d"
              % (len(domains),
                 sum(len(load_index(d)[0]["chunks"]) for d in domains)))
        return 0

    try:
        url, svc = load_env()
    except Exception as e:  # noqa: BLE001
        print("RESULT: P4_SEED_FAIL %s" % e)
        return 1
    host = urllib.parse.urlparse(url).netloc
    print("supabase   : %s" % host)
    print("mode       : %s batch=%d domains=%s"
          % ("verify-only" if args.verify_only else "seed", args.batch,
             ",".join(domains)))

    stats, failed = [], []
    for d in domains:
        try:
            seed_domain(url, svc, d, args, stats)
        except Exception as e:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            failed.append(d)
            print("RESULT: P4_SEED_%s_FAIL %s" % (d.upper(), e))
            if args.fail_fast:
                break
    if failed:
        print("RESULT: P4_SEED_FAIL domains_failed=%s" % ",".join(failed))
        return 1
    print("RESULT: P4_SEED_ALL_OK domains=%d rows=%d"
          % (len(stats), sum(s[1] for s in stats)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001
        import traceback
        traceback.print_exc()
        print("RESULT: P4_SEED_FAIL %s" % sys.exc_info()[1])
        sys.exit(1)
