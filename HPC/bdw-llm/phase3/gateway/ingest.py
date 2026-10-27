"""P3.1 ingest pipeline: Supabase rows -> bdw_chunks seed (blueprint P3.1).

Contract (see PHASE3_INTEGRATION_BLUEPRINT.md):
  phase3/.env                        real values (never committed); names per .env.example
  phase3/supabase/schema_audit.md    owner audit; the ```json block decides table names
  bdw-llm/src/bdw_column_map.json    canonical-field candidates (P2.1 artefact)

Flow: REST-pull rows per audited table -> resolve canonical fields (NEVER raw
columns) -> chunk semantic units (an opening = one chunk; resources/news/FAQ/
orgs split by paragraph groups <=1700 chars) -> quarantine scan (S3/10.4
instruction patterns -> phase3/gateway/data/quarantine.jsonl, never seeded) ->
embed with LOCAL bge-small-en-v1.5 (384-d, normalized) -> seed bdw_chunks via
REST -> verify -> manifest.

Behaviour: aborts without --refresh when bdw_chunks is non-empty; --keep
builds the local snapshot but touches nothing in Supabase.

RESULT: P3_INGEST_OK chunks=N quarantined=M no_id=K types=...
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import traceback
import urllib.parse

GATEWAY = os.path.dirname(os.path.abspath(__file__))
PH3 = os.path.dirname(GATEWAY)                    # ...HPC/bdw-llm/phase3
BASE = os.path.dirname(PH3)                       # ...HPC/bdw-llm
SRCMAP = os.path.join(BASE, "src", "bdw_column_map.json")
DEFAULT_BGE = os.path.join(PH3, "models", "bge-small-en-v1.5")

CONTENT_CAP = 1700
DESC_CAP = 1200
EMB_BATCH = 64
UP_BATCH = 50
ALLOWED_TYPES = ("opportunity", "organization", "resource", "faq", "news",
                 "lab_tool")
QUARANTINE_PATTERNS = [
    "ignore previous instructions", "ignore all previous", "disregard all",
    "disregard previous", "system prompt", "you are now", "act as if",
    "[inst]", "<<sys>>", "<|im_start|>", "<|im_end|>", "developer mode",
    "sudo ", "rm -rf ", "as an ai language model", "your secret",
    "reveal your prompt",
]


def atomic_write_text(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)


def md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def load_env(path):
    env = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"').strip("'")
    for name in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"):
        if not env.get(name):
            raise RuntimeError("phase3/.env must define %s" % name)
    return env


def load_audit(path):
    src = open(path, encoding="utf-8").read()
    m = re.search(r"```json\s*(\{.*?\})\s*```", src, re.S)
    if not m:
        raise RuntimeError("schema_audit.md needs a ```json block "
                           "(see schema_audit.TEMPLATE.md)")
    block = json.loads(m.group(1))
    tables = block.get("tables")
    if not isinstance(tables, dict) or not tables:
        raise RuntimeError("audit json needs a non-empty 'tables' map")
    for ptype, spec in tables.items():
        if ptype not in ALLOWED_TYPES:
            raise RuntimeError("unknown parent_type %r (allowed: %s)"
                               % (ptype, ALLOWED_TYPES))
        if "table" not in spec:
            raise RuntimeError("parent_type %s needs a real 'table' name"
                               % ptype)
    return tables


class Supabase:
    """Minimal REST client over the service role (gateway-side only, S1)."""

    def __init__(self, url, svc):
        self.url = url.rstrip("/")
        import requests
        self.rq = requests
        self.headers = {"apikey": svc, "Authorization": "Bearer " + svc,
                        "Content-Type": "application/json"}

    def pull(self, table, page=1000, cap=None, where=None):
        rows, offset = [], 0
        base = {} if not where else dict(where)
        while True:
            q = urllib.parse.urlencode(dict(
                base, select="*", limit=str(page), offset=str(offset)))
            r = self.rq.get("%s/rest/v1/%s?%s" % (self.url, table, q),
                            headers=self.headers, timeout=120)
            r.raise_for_status()
            batch = r.json()
            if not isinstance(batch, list) or not batch:
                break
            rows.extend(batch)
            offset += len(batch)
            if len(batch) < page or (cap is not None and len(rows) >= cap):
                break
        return rows

    def chunk_count(self):
        r = self.rq.get(self.url + "/rest/v1/bdw_chunks?select=id&limit=1",
                        headers=self.headers, timeout=120)
        r.raise_for_status()
        return len(r.json())

    def clear_chunks(self):
        for ptype in ALLOWED_TYPES:
            q = urllib.parse.urlencode({"parent_type": "eq." + ptype})
            r = self.rq.delete(self.url + "/rest/v1/bdw_chunks?" + q,
                               headers=self.headers, timeout=120)
            r.raise_for_status()

    def insert(self, rows):
        headers = dict(self.headers)
        headers["Prefer"] = "return=representation"
        q = urllib.parse.urlencode({"select": "id"})
        r = self.rq.post(self.url + "/rest/v1/bdw_chunks?" + q,
                         headers=headers, json=rows, timeout=300)
        r.raise_for_status()
        return len(r.json())


def cano(row, cmap, canonical):
    low = {str(k).lower(): v for k, v in row.items()}
    for cand in cmap["canonical"].get(canonical, []):
        v = low.get(cand)
        if v not in (None, ""):
            return str(v).strip()
    return None


def pick(row, cmap):
    return {k: cano(row, cmap, k) for k in
            ("id", "title", "org", "location", "eligibility", "stipend",
             "deadline", "posted", "url", "description", "category")}


def split_paragraphs(body):
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    units, cur = [], ""
    for p in paras:
        cand = (cur + "\n\n" + p) if cur else p
        if len(cand) <= CONTENT_CAP:
            cur = cand
            continue
        if cur:
            units.append(cur)
        if len(p) <= CONTENT_CAP:
            cur = p
            continue
        for i in range(0, len(p), CONTENT_CAP):
            units.append(p[i:i + CONTENT_CAP])
        cur = ""
    if cur:
        units.append(cur)
    return units


def make_chunks(ptype, pk, spec, row, cmap, orgmap, stats):
    """Build all chunks for one source row (openings = a single semantic unit)."""
    pid = pk["id"]
    if not pid:
        stats["no_id"] += 1
        return []
    title = pk["title"] or "(untitled)"
    url = pk["url"] or ""
    vcol = spec.get("verified")
    if vcol:
        vvals = spec.get("verified_values")
        verified = (row.get(vcol) in vvals) if vvals else bool(row.get(vcol))
    else:
        verified = False
    org = pk.get("org")
    if not org and spec.get("org_via"):
        org = orgmap.get(row.get(spec["org_via"]))

    def seg(k, cap=240, label=None):
        v = pk.get(k)
        return ("%s: %s" % (label or k, v[:cap])) if v else ""

    if ptype == "opportunity":
        head = " | ".join(x for x in (title, seg("org", label="organization")
                                      if org else "", seg("location"),
                                      seg("category")) if x)
        facts = " | ".join(x for x in (seg("eligibility"), seg("stipend"),
                                       seg("deadline"), seg("posted")) if x)
        body = head + (("\n" + facts) if facts else ""
                       ) + ("\n" + (pk.get("description") or "")[:DESC_CAP])
        units = [body]
    else:
        body = (title + "\n" + (pk.get("description") or "")).strip()
        extra = " | ".join(x for x in (seg("org", label="organization")
                                       if org else "", seg("location"),
                                       seg("category"), seg("stipend",
                                       label="salary"), seg("url")) if x)
        if extra:
            body = (body + "\n" + extra).strip()
        units = split_paragraphs(body) or ([body] if body else [])

    out = []
    for n, content in enumerate(units):
        content = content.strip()
        if len(content) < 30:
            continue
        if len(content) > CONTENT_CAP:
            content = content[:CONTENT_CAP]
        low = content.lower()
        if any(p in low for p in QUARANTINE_PATTERNS):
            stats["quarantined"] += 1
            out.append({"parent_type": ptype, "parent_id": pid,
                        "title": title, "content": content,
                        "source_url": url, "verified": verified,
                        "part": n, "quarantined": True})
            continue
        suffix = (" — part %d" % (n + 1)) if len(units) > 1 else ""
        out.append({"parent_type": ptype, "parent_id": pid,
                    "title": (title + suffix)[:200],
                    "content": content, "source_url": url,
                    "verified": verified, "part": n, "quarantined": False})
        stats["chunks"] += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true",
                    help="wipe existing bdw_chunks, then reseed")
    ap.add_argument("--keep", action="store_true",
                    help="snapshot only; no Supabase writes or checks")
    args = ap.parse_args()

    t0 = time.time()
    env = load_env(os.path.join(PH3, ".env"))
    audit = load_audit(os.path.join(PH3, "supabase", "schema_audit.md"))
    with open(SRCMAP, encoding="utf-8") as fh:
        cmap = json.load(fh)
    sb = Supabase(env["SUPABASE_URL"], env["SUPABASE_SERVICE_ROLE_KEY"])

    from sentence_transformers import SentenceTransformer
    bge = os.environ.get("BGE_MODEL_DIR", DEFAULT_BGE)
    model = SentenceTransformer(bge, local_files_only=True)
    if model.get_sentence_embedding_dimension() != 384:
        raise RuntimeError("bge-small embedding dim must be 384")
    saf = os.path.join(bge, "model.safetensors")
    bge_md5 = md5_file(saf) if os.path.exists(saf) else "n/a"

    existing = 0 if args.keep else sb.chunk_count()
    if existing and not args.refresh:
        raise RuntimeError("bdw_chunks already has %d rows; rerun with "
                           "--refresh to wipe and reseed" % existing)
    if existing and args.refresh:
        sb.clear_chunks()
        print("refresh: cleared existing chunks", flush=True)

    stats = {"chunks": 0, "quarantined": 0, "no_id": 0, "empty": 0}
    orgmap = {}
    if any(s.get("org_via") for s in audit.values()):
        for ptype, spec in audit.items():
            if spec.get("org_via") and "organization" in audit:
                src = audit["organization"]["table"]
                q = urllib.parse.urlencode(
                    {"select": "*", "limit": "10000"})
                r = sb.rq.get("%s/rest/v1/%s?%s" % (sb.url, src, q),
                              headers=sb.headers, timeout=120)
                r.raise_for_status()
                orgmap = {p["id"]: p["title"] for p in
                          (pick(o, cmap) for o in r.json())
                          if p["id"] and p["title"]}
        print("org join: %d names loaded" % len(orgmap), flush=True)
    per_type, all_chunks = {}, []
    for ptype, spec in audit.items():
        table, vcol = spec["table"], spec.get("verified")
        rows = sb.pull(table, cap=spec.get("row_limit"),
                       where=spec.get("where"))
        if not rows:
            stats["empty"] += 1
            print("pull %-12s -> 0 rows (recheck audit name)" % table,
                  flush=True)
            continue
        made = []
        for row in rows:
            made.extend(make_chunks(ptype, pick(row, cmap), spec, row, cmap,
                                    orgmap, stats))
        plant = [c for c in made if not c["quarantined"]]
        quar = [c for c in made if c["quarantined"]]
        per_type[ptype] = {"table": table, "rows": len(rows),
                           "chunks": len(plant)}
        all_chunks.extend(plant)
        if quar:
            prov = os.path.join(PH3, "gateway", "data", "quarantine.jsonl")
            os.makedirs(os.path.dirname(prov), exist_ok=True)
            with open(prov, "a", encoding="utf-8") as fh:
                for c in quar:
                    fh.write(json.dumps(c, ensure_ascii=False) + "\n")
        print("pull %-12s -> %4d rows, %4d chunks, %d quarantined"
              % (table, len(rows), len(made) - len(quar), len(quar)),
              flush=True)

    os.makedirs(os.path.join(PH3, "gateway", "data"), exist_ok=True)
    snap = os.path.join(PH3, "gateway", "data", "seed_chunks.jsonl")
    atomic_write_text(snap, "".join(
        json.dumps(c, ensure_ascii=False) + "\n" for c in all_chunks))
    snap_md5 = md5_file(snap)

    upserted = 0
    if not args.keep:
        for i in range(0, len(all_chunks), EMB_BATCH):
            batch = all_chunks[i:i + EMB_BATCH]
            vecs = model.encode(
                ["%s\n%s" % (b["title"], b["content"]) for b in batch],
                normalize_embeddings=True, show_progress_bar=False)
            for k in range(0, len(batch), UP_BATCH):
                rows = []
                for j, b in enumerate(batch[k:k + UP_BATCH]):
                    if len(vecs[k + j]) != 384:
                        raise RuntimeError("bge dim != 384")
                    rows.append({"parent_type": b["parent_type"],
                                 "parent_id": b["parent_id"],
                                 "source_url": b["source_url"] or "",
                                 "title": b["title"],
                                 "content": b["content"],
                                 "verified": b["verified"],
                                 "embedding": vecs[k + j].tolist()})
                upserted += sb.insert(rows)
            print("embedded+upserted %6d/%d" % (upserted, len(all_chunks)),
                  flush=True)
    else:
        print("keep mode: no Supabase writes", flush=True)

    manifest = {"run": time.strftime("%Y-%m-%d %H:%M"),
                "elapsed_s": round(time.time() - t0, 1),
                "mode": "keep" if args.keep else "seed",
                "audit_tables": per_type,
                "chunks": len(all_chunks), "quarantined": stats["quarantined"],
                "no_id": stats["no_id"], "empty_tables": stats["empty"],
                "upserted_to_supabase": upserted,
                "bge_dir": bge, "bge_safetensors_md5": bge_md5,
                "snapshot": os.path.relpath(snap, BASE),
                "snapshot_md5": snap_md5}
    atomic_write_text(os.path.join(PH3, "gateway", "ingest_manifest.json"),
                      json.dumps(manifest, indent=1))
    print("manifest: chunks=%d quarantined=%d no_id=%d upserted=%d"
          % (manifest["chunks"], manifest["quarantined"], manifest["no_id"],
             manifest["upserted_to_supabase"]))
    print("RESULT: P3_INGEST_OK chunks=%d quarantined=%d no_id=%d types=%s"
          % (manifest["chunks"], manifest["quarantined"], manifest["no_id"],
             ",".join("%s:%d" % (t, v["chunks"])
                      for t, v in per_type.items())), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        traceback.print_exc()
        print("RESULT: P3_INGEST_FAIL %s" % exc, flush=True)
        sys.exit(1)
