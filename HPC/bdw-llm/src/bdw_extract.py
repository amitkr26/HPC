"""P2.1 D0/D1: Supabase schema discovery + resumable table extraction.

Runs on the LOGIN node (only node with internet). Reads credentials from
~/bdw-llm/secrets/supabase.env (SUPABASE_URL, SUPABASE_SERVICE_KEY; chmod 600,
never committed). Blueprint: docs/PHASE2_7B_BLUEPRINT.md section 5.

  discover : GET $SUPABASE_URL/rest/v1/ -> PostgREST OpenAPI spec, snapshotted
             to data/raw/supabase_openapi.json; table list printed.
  extract  : per table, GET /rest/v1/{table}?select=* with Range paging
             (rows=0-999, ...), appended to data/raw/bdw_{table}.jsonl, resumable
             by primary key (already-seen ids skipped), manifest with row
             counts + md5 -> data/raw/bdw_manifest.json.

RESULT lines: P2_EXTRACT_OK / P2_EXTRACT_FAIL (driver greps these).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.expanduser("~/bdw-llm")
SECRETS = os.path.join(ROOT, "secrets/supabase.env")
RAW_DIR = os.path.join(ROOT, "data/raw")
OPENAPI = os.path.join(RAW_DIR, "supabase_openapi.json")
MANIFEST = os.path.join(RAW_DIR, "bdw_manifest.json")
PAGE = 1000
SLEEP_S = 0.15


def load_env():
    env = {}
    with open(SECRETS, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    url = env.get("SUPABASE_URL", "").rstrip("/")
    key = env.get("SUPABASE_SERVICE_KEY", "")
    if not url or not key:
        print("RESULT: P2_EXTRACT_FAIL no_credentials in %s" % SECRETS)
        sys.exit(1)
    return url, key


def api_get(url, key, path, headers=None, timeout=60, retries=4):
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(url + path, headers={
            "apikey": key, "Authorization": "Bearer " + key,
            **(headers or {})})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read(), dict(r.headers), r.status
        except urllib.error.HTTPError as e:
            return e.read(), dict(e.headers), e.code
        except urllib.error.URLError as e:
            last = e
            wait = 2 * (attempt + 1)
            print("   [retry %d/%d] %s -- sleeping %ds"
                  % (attempt + 1, retries, repr(e)[:120], wait), flush=True)
            time.sleep(wait)
    raise last


def discover(url, key):
    body, _, status = api_get(url, key, "/rest/v1/")
    if status != 200:
        print("RESULT: P2_EXTRACT_FAIL openapi_http_%d %s"
              % (status, body[:200]))
        sys.exit(1)
    os.makedirs(RAW_DIR, exist_ok=True)
    with open(OPENAPI, "wb") as fh:
        fh.write(body)
    spec = json.loads(body)
    tables = []
    for p, ops in sorted(spec.get("paths", {}).items()):
        if p.startswith("/") and "get" in ops and p.count("/") == 1:
            name = p[1:]
            if name and not name.startswith("rpc/"):
                tables.append(name)
    print("openapi     : %s (%d bytes)" % (OPENAPI, len(body)))
    print("tables      : %d -> %s" % (len(tables), tables))
    return tables, spec


def load_manifest():
    if os.path.exists(MANIFEST):
        try:
            return json.load(open(MANIFEST, encoding="utf-8"))
        except Exception:
            return {}
    return {}


def seen_ids(path):
    ids = set()
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    ids.add(str(json.loads(line).get("id")))
                except Exception:
                    continue
    return ids


def extract_table(url, key, table):
    out_path = os.path.join(RAW_DIR, "bdw_%s.jsonl" % table)
    done = seen_ids(out_path)
    total_written = 0
    offset = 0
    if done:
        print("[%s] resume: %d ids already on disk" % (table, len(done)))
    while True:
        if offset > 200000:
            print("[%s] ABORT offset>200000 (runaway guard)" % table)
            return None
        # limit/offset query params: one distinct URL per page (Range headers
        # were being served stale by an intermediary cache on this cluster)
        path = ("/rest/v1/%s?select=*&order=id&limit=%d&offset=%d"
                % (urllib.parse.quote(table, safe=""), PAGE, offset))
        body, hdrs, status = api_get(url, key, path,
                                     headers={"Prefer": "count=exact"})
        if status not in (200, 206):
            print("[%s] HTTP %d %s" % (table, status, body[:200]))
            return None
        rows = json.loads(body or b"[]")
        new = 0
        first_id = last_id = ""
        with open(out_path, "a", encoding="utf-8") as fh:
            for r in rows:
                rid = str(r.get("id"))
                if not first_id:
                    first_id = rid
                last_id = rid
                if rid in done:
                    continue
                done.add(rid)
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
                new += 1
                total_written += 1
        content_range = hdrs.get("Content-Range", "-")
        print("[%s] offset=%d -> %d rows (%d new, ids %s..%s, disk=%d) %s"
              % (table, offset, len(rows), new, first_id, last_id,
                 len(done), content_range), flush=True)
        if len(rows) < PAGE:
            break
        offset += PAGE
        time.sleep(SLEEP_S)
    data = open(out_path, "rb").read()
    return {"table": table, "rows_on_disk": len(done),
            "bytes": len(data), "md5": hashlib.md5(data).hexdigest(),
            "file": os.path.basename(out_path),
            "extracted_at": time.strftime("%Y-%m-%dT%H:%M:%S")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tables", default="",
                    help="comma list; default = every OpenAPI table")
    ap.add_argument("--discover-only", action="store_true")
    args = ap.parse_args()

    url, key = load_env()
    print("target      : %s (key redacted)" % url)
    tables_all, spec = discover(url, key)
    if args.discover_only:
        defs = spec.get("components", {}).get("schemas", {})
        for name in sorted(defs):
            props = defs[name].get("properties", {})
            print("SCHEMA %s fields=%d" % (name, len(props)))
            for k, v in props.items():
                print("   %-28s %s" % (k, v.get("type", v.get("format", "?"))))
        print("RESULT: P2_EXTRACT_OK mode=discover tables=%d" % len(tables_all))
        return

    tables = [t.strip() for t in args.tables.split(",") if t.strip()] \
        or tables_all
    manifest = load_manifest()
    ok = True
    for t in tables:
        info = extract_table(url, key, t)
        if info is None:
            ok = False
            manifest[t] = {"error": "http_failed",
                           "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
        else:
            manifest[t] = info
        with open(MANIFEST, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=1)
    total_rows = sum(m.get("rows_on_disk", 0) for m in manifest.values()
                     if isinstance(m, dict))
    if not ok:
        print("RESULT: P2_EXTRACT_FAIL partial tables=%d rows=%d"
              % (len(manifest), total_rows))
        sys.exit(1)
    print("manifest    : %s" % MANIFEST)
    print("RESULT: P2_EXTRACT_OK tables=%d rows=%d"
          % (len(tables), total_rows))


if __name__ == "__main__":
    main()
