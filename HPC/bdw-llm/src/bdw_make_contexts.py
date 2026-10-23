"""P2.1: turn extracted Supabase tables into teacher-context chunks for R3.

Reads data/raw/bdw_{table}.jsonl for the requested tables, serialises each
row as generic "key: value" lines (no per-table column hardcoding beyond a
noise-key skip list), drops rows shorter than 200 chars, dedupes on text md5
(circular descriptions repeat heavily), and writes the Stage-O chunk shape:

    data/raw/bdw_contexts.json  {"chunks": [{"id", "title", "text"}]}

Feed to the GPU teacher with:
    python src/bdw_gen_teacher_qa.py --contexts data/raw/bdw_contexts.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os

ROOT = os.path.expanduser("~/bdw-llm")
RAW = os.path.join(ROOT, "data/raw")
OUT = os.path.join(RAW, "bdw_contexts.json")

DEFAULT_TABLES = ["opportunities", "jobs", "job_occurrences", "organizations",
                  "resources", "resource_bank", "learning_resources",
                  "learning_questions", "learning_tracks", "company_pages"]
NOISE_KEYS = {"id", "created_at", "updated_at", "created_by", "audit_notes",
              "last_verified_at", "last_link_checked", "verified_at",
              "screening_questions", "employer_id", "organization_id",
              "scrape_source_id", "verification_source", "applies_from",
              "user_id", "profile_id"}
MIN_CHARS = 200


def row_to_text(row):
    parts = []
    for k, v in row.items():
        if k in NOISE_KEYS or k.endswith("_id"):
            continue
        if v is None:
            continue
        s = str(v).strip()
        if not s or s in ("[]", "{}", "None", "False", "True"):
            continue
        parts.append("%s: %s" % (k.replace("_", " "), s[:600]))
    return "\n".join(parts)


def row_title(row, table):
    for k in ("title", "name", "question", "heading"):
        v = row.get(k)
        if v:
            return str(v).strip()[:80]
    return "%s record" % table


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tables", default=",".join(DEFAULT_TABLES))
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    seen_text, chunks = set(), []
    stats = {}
    for t in [x.strip() for x in args.tables.split(",") if x.strip()]:
        path = os.path.join(RAW, "bdw_%s.jsonl" % t)
        if not os.path.exists(path):
            print("[%s] missing, skipped" % t)
            continue
        n_rows = n_short = n_dup = 0
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                n_rows += 1
                text = row_to_text(row)
                if len(text) < MIN_CHARS:
                    n_short += 1
                    continue
                h = hashlib.md5(text.encode("utf-8")).hexdigest()
                if h in seen_text:
                    n_dup += 1
                    continue
                seen_text.add(h)
                rid = str(row.get("id", "%04d" % len(chunks)))[:8]
                chunks.append({"id": "%s_%s" % (t[:6], rid),
                               "title": row_title(row, t),
                               "text": text})
        stats[t] = {"rows": n_rows, "short": n_short, "dup": n_dup,
                    "kept": sum(1 for c in chunks
                                if c["id"].startswith(t[:6] + "_"))}
        print("[%s] rows=%d short=%d dup_text=%d" % (t, n_rows, n_short, n_dup))

    if args.limit and len(chunks) > args.limit:
        chunks = chunks[:args.limit]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"chunks": chunks, "tables": args.tables,
                   "total_chars": sum(len(c["text"]) for c in chunks)},
                  fh, ensure_ascii=False)
    print("contexts=%d chars=%d -> %s"
          % (len(chunks), sum(len(c["text"]) for c in chunks), OUT))
    if not chunks:
        print("RESULT: P2_CONTEXTS_FAIL empty")
        raise SystemExit(1)
    print("RESULT: P2_CONTEXTS_OK chunks=%d" % len(chunks))


if __name__ == "__main__":
    main()
