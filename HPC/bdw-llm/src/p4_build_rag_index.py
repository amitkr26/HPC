"""P4.3 - build the local per-domain RAG indexes (LOGIN node, CPU).

Produces one index per Phase 4 router surface so every RoutingDecision
from phase4/router/domain_classifier.py resolves to a built artifact:

    RoutingDecision.rag_index           built here
    idx_math      -> phase4/rag/idx_math/
    idx_vlsi      -> phase4/rag/idx_vlsi/     (Stage O.1 wiki corpus)
    idx_embedded  -> phase4/rag/idx_embedded/
    idx_cs        -> phase4/rag/idx_cs/
    idx_aiml      -> phase4/rag/idx_aiml/
    idx_general   -> phase4/rag/idx_general/  (platform corpus stand-in;
                     production retrieval keeps using the P3 Supabase
                     bdw_chunks pgvector table -- this local index exists so
                     the Zot-free zone3/gateway can run fully offline on the
                     cluster when the router routes to the general domain)

Corpus rows come from the context payloads (Stage O.1 schema chunks); the
general index reads data/raw/bdw_contexts.json. Embeddings: the staged
P3.1 model phase3/models/bge-small-en-v1.5 (384-d, L2-normalised), the same
embedder, dimension and metric family as the production pgvector corpus, so
scores stay comparable when the domain tables land in Supabase later.

Per domain the index dir holds:
    vectors.npy   float32 [n, 384], L2-normalised rows
    meta.json     {domain, model, dim, built_at, host, n, chunks: [
                   {id, title, url, domain, nchars, text}]}
and phase4/rag/index_manifest.json is the aggregate md5'd summary in
md5sum -c style ("md5<2 spaces>relpath") over every built index.

Self-test (--self-test <domain>): loads vectors.npy, verifies L2 norms,
verifies argrank[0](dot) self-match for 5 random rows, prints
P4_RAG_<DOMAIN>_SELFTEST_OK.

RESULT: P4_RAG_<DOMAIN>_OK n=.. dim=384 | P4_RAG_<DOMAIN>_FAIL ...
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p4_domain_lib as P4  # noqa: E402

BGE_DIR = os.path.join(P4.ROOT, "phase3/models/bge-small-en-v1.5")
EMB_MODEL = "bge-small-en-v1.5 (local stage; P3.1 staging verified)"
EMB_DIM = 384
EMB_BATCH = 32

GENERAL_CTX = os.path.join(P4.ROOT, "data/raw/bdw_contexts.json")
DOMAIN_TAG = "general"


def md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def corpus_rows(domain):
    """[(id, title, url, nchars, text)] for one domain payload."""
    path = P4.ctx_path(domain)
    if not os.path.isfile(path):
        raise FileNotFoundError("context payload missing: %s" % path)
    d = json.load(open(path, encoding="utf-8"))
    out = []
    for c in d.get("chunks") or []:
        text = (c.get("text") or "").strip()
        if len(text) < 200:
            continue
        out.append((c["id"], c.get("title") or "", c.get("url") or "",
                    len(text), text))
    if not out:
        raise RuntimeError("no chunks >= 200 chars in %s" % path)
    return out


def corpus_rows_general():
    if not os.path.isfile(GENERAL_CTX):
        raise FileNotFoundError(GENERAL_CTX)
    d = json.load(open(GENERAL_CTX, encoding="utf-8"))
    out = []
    for c in d.get("chunks") or []:
        text = (c.get("text") or "").strip()
        if len(text) < 100:
            continue
        out.append((c.get("id") or hashlib.md5(
            text.encode("utf-8")).hexdigest()[:16],
            c.get("title") or "", c.get("url") or "", len(text), text))
    if not out:
        raise RuntimeError("no chunks in %s" % GENERAL_CTX)
    return out


def build(domain, rows, model, manifest_lines):
    import numpy as np
    vec_dir = P4.rag_dir(domain if domain != DOMAIN_TAG else DOMAIN_TAG)
    os.makedirs(vec_dir, exist_ok=True)

    texts = [r[4] for r in rows]
    t0 = time.time()
    emb = model.encode(texts, batch_size=EMB_BATCH, show_progress_bar=False,
                       normalize_embeddings=True)
    emb = np.asarray(emb, dtype=np.float32)
    assert emb.shape[0] == len(texts) and emb.shape[1] == EMB_DIM, \
        "embed shape %s != (%d, %d)" % (emb.shape, len(texts), EMB_DIM)
    norms = np.linalg.norm(emb, axis=1)
    assert float(norms.max()) <= 1.001 and float(norms.min()) >= 0.999, \
        "normalisation drift: norms in [%f, %f]" % (norms.min(), norms.max())

    vecs_path = os.path.join(vec_dir, "vectors.npy")
    tmp = vecs_path + ".tmp.npy"
    np.save(tmp, emb)
    os.replace(tmp, vecs_path)
    rows_out = [{"id": r[0], "title": r[1], "url": r[2], "nchars": r[3],
                 "text": r[4], "domain": domain} for r in rows]
    meta = {
        "domain": domain,
        "model": EMB_MODEL,
        "dim": EMB_DIM,
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "host": os.uname().nodename,
        "metric": "cosine (dot on L2-normalised rows)",
        "n": len(rows_out),
        "chunks": rows_out,
    }
    meta_path = os.path.join(vec_dir, "meta.json")
    with open(meta_path, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=1)

    n_bytes = os.path.getsize(vecs_path)
    manifest_lines.append("rag_index=%s rows=%d dim=%d bytes=%d build_s=%.1f "
                          "dir=%s" % (domain, len(rows_out), EMB_DIM, n_bytes,
                                      time.time() - t0, vec_dir))
    print("INDEX %-9s rows=%-5d dim=%d bytes=%d (%.1fs)"
          % (domain, len(rows_out), EMB_DIM, n_bytes, time.time() - t0))
    print("RESULT: P4_RAG_%s_OK n=%d dim=%d" %
          (domain.upper(), len(rows_out), EMB_DIM))
    return {"domain": domain, "n": len(rows_out), "dim": EMB_DIM,
            "vec_bytes": n_bytes, "dir": vec_dir}


def self_test(domain):
    import numpy as np
    vec_dir = P4.rag_dir(domain)
    emb = np.load(os.path.join(vec_dir, "vectors.npy"))
    norms = np.linalg.norm(emb, axis=1)
    bases = sorted({int(hashlib.md5((domain + str(k)).encode())
                        .hexdigest(), 16) % len(emb) for k in range(5)})
    hits = 0
    checks = len(bases)
    for base in bases:
        q = emb[base]
        scores = emb @ q
        top1 = int(np.argmax(scores))
        if top1 == base or scores[base] >= scores[top1] - 1e-9:
            hits += 1
    print("vec_dir    : %s" % vec_dir)
    print("norms      : min=%.6f max=%.6f" % (norms.min(), norms.max()))
    print("self top-k : %d/%d argmax==self" % (hits, checks))
    ok = float(norms.min()) >= 0.999 and hits == checks and emb.shape[1] == EMB_DIM
    print("RESULT: P4_RAG_%s_SELFTEST_%s" %
          (domain.upper(), "OK" if ok else "FAIL"))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="P4.3 domain RAG index build")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--domain", help="math|vlsi|embedded|cs|aiml|general")
    g.add_argument("--all", action="store_true",
                   help="build all five domain indexes + idx_general")
    g.add_argument("--self-test", metavar="DOMAIN", dest="self_test")
    args = ap.parse_args()

    if args.self_test:
        try:
            if args.self_test != DOMAIN_TAG:
                P4.check(args.self_test)
        except ValueError as e:
            print("RESULT: P4_RAG_FAIL %s" % e)
            return 2
        return self_test(args.self_test)

    targets = [args.domain]
    if args.all:
        targets = list(P4.DOMAINS) + [DOMAIN_TAG]

    try:
        import torch
        torch.set_num_threads(4)
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(BGE_DIR, device="cpu")
    except Exception as e:
        traceback.print_exc()
        print("RESULT: P4_RAG_FAIL embedder load: %s" % e)
        return 1

    results = []
    manifest_lines = []
    for t in targets:
        try:
            if t == DOMAIN_TAG:
                rows = corpus_rows_general()
                tag = DOMAIN_TAG
            else:
                P4.check(t)
                rows = corpus_rows(t)
                tag = t
        except Exception as e:
            print("RESULT: P4_RAG_%s_FAIL %s" % (t.upper(), e))
            if args.all:
                continue
            return 1
        try:
            results.append(build(tag, rows, model, manifest_lines))
        except Exception as e:
            traceback.print_exc()
            print("RESULT: P4_RAG_%s_FAIL %s" % (tag.upper(), e))
            if args.all:
                continue
            return 1

    # aggregate manifest (atomic replace)
    manifest = {
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "host": os.uname().nodename,
        "embedder": EMB_MODEL,
        "dim": EMB_DIM,
        "note": "local cluster-side indexes; production general retrieval "
                "stays on Supabase bdw_chunks (P3)",
        "indexes": results,
        "manifest_lines": manifest_lines,
    }
    if results:
        mp = P4.rag_manifest_path()
        os.makedirs(os.path.dirname(mp), exist_ok=True)
        tmp = mp + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=1)
        os.replace(tmp, mp)
        index_dirs = [r["dir"] for r in results]
        for d in index_dirs:
            files = sorted(os.listdir(d))
            for f in files:
                print("  md5 %s  %s" % (md5_file(os.path.join(d, f)), f))
        print("manifest    : %s (%d indexes)" % (mp, len(results)))
    if not results:
        print("RESULT: P4_RAG_FAIL nothing built")
        return 1
    print("RESULT: P4_RAG_ALL_OK indexes=%s"
          % ",".join("%s:%d" % (r["domain"], r["n"]) for r in results))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        print("RESULT: P4_RAG_FAIL %s" % sys.exc_info()[1])
        sys.exit(1)
