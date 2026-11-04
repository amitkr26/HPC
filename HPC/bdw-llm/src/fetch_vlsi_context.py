"""Stage O.1 (grounded distillation): fetch real VLSI reference text on the
LOGIN node (compute nodes have no DNS).

Talks to the MediaWiki API directly with requests instead of the `wikipedia`
package: that package's search endpoint started returning non-JSON (blocked
/ rate-limited) after Stage M, which made both "Setup and hold time" and
"Clock domain crossing" resolve to nothing even though their articles exist.
The extracts endpoint still works, and we do not need search at all -- each
concept lists its candidate titles in order (exact title first, canonical or
related article as fallback).

For each concept we pull the article, clean it (citation markers, whitespace),
split it into ~700-character chunks suitable for one teacher call, and save
data/raw/vlsi_wikipedia.json. O.3's teacher is then allowed to write Q&A ONLY
from these chunks (context-grounded distillation).

Extra titles may be passed on the command line:
    python src/fetch_vlsi_context.py "Logic synthesis" "Flip-flop"
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time

ROOT = os.path.expanduser("~/bdw-llm")
OUT = os.path.join(ROOT, "data/raw/vlsi_wikipedia.json")

API = "https://en.wikipedia.org/w/api.php"
UA = {"User-Agent": "BDW-VLSI-Research/1.0 (PARAM Rudra student project; "
                    "educational use)"}

# (requested concept, candidate article titles in priority order)
CONCEPTS = [
    ("Setup and hold time",
     ["Setup and hold time", "Setup time", "Flip-flop (electronics)",
      "Flip-flop"]),
    ("Automatic test pattern generation",
     ["Automatic test pattern generation"]),
    ("FinFET",
     ["FinFET", "Fin field-effect transistor"]),
    ("Clock domain crossing",
     ["Clock domain crossing", "Metastability (electronics)",
      "Asynchronous circuit", "Clock signal"]),
    ("Static timing analysis",
     ["Static timing analysis"]),
]

MIN_PARA_CHARS = 40
CHUNK_TARGET = 700
CHUNK_MAX = 1100
TRIES = 4


def api_get(params, tries=TRIES):
    import requests
    for attempt in range(tries):
        try:
            r = requests.get(API, params=params, headers=UA, timeout=30)
            if r.status_code == 200 and r.text.startswith("{"):
                return r.json()
            raise RuntimeError("HTTP %d %r" % (r.status_code, r.text[:80]))
        except Exception as e:
            if attempt + 1 < tries:
                time.sleep(min(2 * (2 ** attempt), 20))
            else:
                print("    api failed after %d tries: %s: %s"
                      % (tries, type(e).__name__, e))
    return None


def fetch_extract(title):
    """Resolve one title (following redirects) -> plain-text extract or None."""
    j = api_get({"action": "query", "titles": title, "redirects": "1",
                 "prop": "extracts", "explaintext": "1",
                 "format": "json", "formatversion": "2"})
    if not j:
        return None
    pages = (j.get("query") or {}).get("pages") or []
    if not pages or pages[0].get("missing"):
        return None
    page = pages[0]
    text = (page.get("extract") or "").strip()
    if len(text) < 500:
        return None
    return {"title": page["title"],
            "url": "https://en.wikipedia.org/wiki/"
                   + page["title"].replace(" ", "_"),
            "text": text}


def clean(text):
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"\[citation needed\]", "", text, flags=re.I)
    text = re.sub(r"\[\s*\]", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def split_long(text, target):
    parts, buf = [], ""
    for sent in re.split(r"(?<=[.!?])\s+", text):
        if buf and len(buf) + len(sent) + 1 > target:
            parts.append(buf.strip())
            buf = sent
        else:
            buf = (buf + " " + sent).strip()
    if buf:
        parts.append(buf.strip())
    return parts


def build_chunks(pages):
    pairs = []
    for meta in pages:
        paras = [clean(x) for x in meta["raw"].split("\n")]
        paras = [p for p in paras if len(p) >= MIN_PARA_CHARS]
        for para in paras:
            pieces = split_long(para, CHUNK_TARGET) if len(para) > CHUNK_MAX \
                else [para]
            buf = ""
            for piece in pieces:
                if buf and len(buf) + len(piece) + 1 > CHUNK_TARGET:
                    pairs.append((meta, buf))
                    buf = piece
                else:
                    buf = (buf + " " + piece).strip()
            if buf:
                pairs.append((meta, buf))
    out = []
    for meta, text in pairs:
        text = text.strip()
        if len(text) < 200:
            continue
        out.append({
            "id": hashlib.md5(text.encode("utf-8")).hexdigest()[:16],
            "title": meta["title"],
            "url": meta["url"],
            "requested": meta["requested"],
            "nchars": len(text),
            "text": text,
        })
    return out


def main():
    extra = [a for a in sys.argv[1:]]
    concepts = list(CONCEPTS)
    for a in extra:
        concepts.append((a, [a]))
    print("=" * 74)
    print("STAGE O.1 - fetch VLSI reference context (login node, MediaWiki API)")
    print("=" * 74)
    print("concepts  : %d" % len(concepts))
    print("output    : %s" % OUT)
    print("chunking  : target %d, max %d, min 200 chars" % (CHUNK_TARGET, CHUNK_MAX))

    pages, missing = [], []
    for requested, candidates in concepts:
        t0 = time.time()
        got = None
        for cand in candidates:
            got = fetch_extract(cand)
            if got:
                if cand != candidates[0]:
                    print("[alt] %r not exact -> used %r" % (requested, cand))
                break
            time.sleep(0.4)
        if not got:
            missing.append(requested)
            print("[miss] %r (tried: %s)" % (requested, candidates))
            continue
        if any(p["title"] == got["title"] for p in pages):
            print("[dup] %r resolved to already-fetched %r"
                  % (requested, got["title"]))
            continue
        got["requested"] = requested
        got["raw"] = got.pop("text")
        got["chars"] = len(got["raw"])
        pages.append(got)
        print("[ok] %-33s -> %-33s %6d chars  %.1fs"
              % (requested, got["title"][:33], got["chars"], time.time() - t0))
        time.sleep(0.4)

    if not pages:
        print("RESULT: O1_FETCH_FAILED (no pages)")
        sys.exit(1)

    chunks = build_chunks(pages)
    payload = {
        "stage": "O.1",
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "host": os.uname().nodename,
        "source": "en.wikipedia.org (MediaWiki API, prop=extracts)",
        "chunk_target_chars": CHUNK_TARGET,
        "pages": [{k: v for k, v in p.items() if k != "raw"} for p in pages],
        "missing": missing,
        "chunks": chunks,
        "total_chars": sum(p["chars"] for p in pages),
        "chunk_chars": sum(c["nchars"] for c in chunks),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)

    print("-" * 74)
    print("pages ok    : %d / %d   missing: %s" % (len(pages), len(concepts),
                                                   missing or "none"))
    print("total chars : %d" % payload["total_chars"])
    print("chunks      : %d  (%d chars ~%d tokens of source text)"
          % (len(chunks), payload["chunk_chars"], payload["chunk_chars"] // 4))
    print("file        : %s (%d bytes)" % (OUT, os.path.getsize(OUT)))
    ok = len(pages) >= 5 and len(chunks) >= 40
    print("RESULT: O1_FETCH_%s pages=%d chunks=%d"
          % ("OK" if ok else "FAILED", len(pages), len(chunks)))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
