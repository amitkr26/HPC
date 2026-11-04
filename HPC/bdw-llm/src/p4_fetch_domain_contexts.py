"""P4.0 - fetch per-domain reference contexts (LOGIN node, MediaWiki API).

Runs on the login node only: compute nodes have no DNS (Stage M lesson).
Reuses the proven Stage O.1 fetch machinery (fetch_vlsi_context.py) verbatim --
direct MediaWiki extracts API, ~700-char chunking, md5 chunk ids -- and
generalises it over the Phase 4 router domains:

    math | vlsi | embedded | cs | aiml   (phase4/router/domain_classifier.py)

Output per domain: data/raw/p4_<domain>_contexts.json with the same payload
schema, so P4.1 teacher QA generation (p4_gen_domain_qa.py) and the P4 RAG
index builder (p4_build_rag_index.py) share one format through
p4_domain_lib.ctx_path().

vlsi default: the Stage O.1 corpus data/raw/vlsi_wikipedia.json is already on
disk and stays the context source of record (no network, no rewrite);
`--refresh` fetches the (extended) VLSI concept list into a p4 payload that
then supersedes it for every consumer via ctx_path().

Extra concepts accepted on the command line (exact title candidates, one
fallback each, shared with the domain list):
    python src/p4_fetch_domain_contexts.py --domain vlsi --refresh "Logic synthesis"

RESULT: P4_FETCH_<DOMAIN>_OK pages=.. chunks=.. | P4_FETCH_FAIL ...
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p4_domain_lib as P4  # noqa: E402

ROOT = P4.ROOT

API = "https://en.wikipedia.org/w/api.php"
UA = {"User-Agent": "BDW-Research/1.0 (https://github.com/amitkr26/BerojgarDegreeWala; contact@berojgardegreewala.in)"}

MIN_PARA_CHARS = 40
CHUNK_TARGET = 700
CHUNK_MAX = 1100
MIN_CHUNK_CHARS = 200
TRIES = 4

# (requested concept, candidate article titles in priority order, fallback
# titles) -- the same tuple form Stage O.1 used; list extra fallbacks after
# the exact title and exact-candidate list when the article may live under a
# different canonical name.
CONCEPTS = {
    "math": [
        ("Calculus", ["Calculus"]),
        ("Derivative", ["Derivative"]),
        ("Integral", ["Integral"]),
        ("Linear algebra", ["Linear algebra"]),
        ("Eigenvalues and eigenvectors", ["Eigenvalues and eigenvectors"]),
        ("Matrix calculus", ["Matrix calculus", "Matrix (mathematics)"]),
        ("Vector space", ["Vector space"]),
        ("Probability", ["Probability"]),
        ("Probability distribution", ["Probability distribution"]),
        ("Bayes' theorem", ["Bayes' theorem", "Bayesian probability"]),
        ("Statistics", ["Statistics"]),
        ("Fourier transform", ["Fourier transform"]),
        ("Laplace transform", ["Laplace transform"]),
        ("Differential equation", ["Differential equation",
                                   "Ordinary differential equation"]),
        ("Numerical analysis", ["Numerical analysis"]),
        ("Mathematical optimization", ["Mathematical optimization",
                                       "Optimization (mathematics)"]),
    ],
    "vlsi": [
        ("Setup and hold time", ["Flip-flop (electronics)", "Flip-flop"]),
        ("Static timing analysis", ["Static timing analysis"]),
        ("Clock domain crossing", ["Clock domain crossing", "Metastability (electronics)"]),
        ("Metastability (electronics)", ["Metastability (electronics)"]),
        ("Verilog", ["Verilog", "Hardware description language"]),
        ("SystemVerilog", ["SystemVerilog"]),
        ("Universal Verification Methodology", ["Universal Verification Methodology"]),
        ("VHDL", ["VHDL"]),
        ("Hardware description language", ["Hardware description language"]),
        ("Automatic test pattern generation", ["Automatic test pattern generation"]),
        ("Design for testing", ["Design for testing"]),
        ("Boundary scan", ["Boundary scan", "JTAG"]),
        ("JTAG", ["JTAG"]),
        ("Built-in self-test", ["Built-in self-test"]),
        ("CMOS", ["CMOS", "MOSFET"]),
        ("Fin field-effect transistor", ["Fin field-effect transistor", "FinFET"]),
        ("Field-programmable gate array", ["Field-programmable gate array"]),
        ("Application-specific integrated circuit", ["Application-specific integrated circuit"]),
        ("Electronic design automation", ["Electronic design automation"]),
        ("Logic synthesis", ["Logic synthesis"]),
        ("Physical design (electronics)", ["Physical design (electronics)",
                                           "Physical design (semiconductors)",
                                           "Integrated circuit layout"]),
        ("Semiconductor device fabrication", ["Semiconductor device fabrication"]),
        ("Photolithography", ["Photolithography"]),
        ("Extreme ultraviolet lithography", ["Extreme ultraviolet lithography", "Photolithography"]),
        ("Chemical-mechanical planarization", ["Chemical-mechanical planarization"]),
        ("Standard cell", ["Standard cell"]),
        ("Clock distribution network", ["Clock distribution network"]),
        ("Placement (EDA)", ["Placement (EDA)", "Integrated circuit layout"]),
        ("Routing (electronic design automation)", ["Routing (electronic design automation)", "Integrated circuit layout"]),
        ("Design rule checking", ["Design rule checking"]),
        ("Layout Versus Schematic", ["Layout Versus Schematic"]),
        ("Power gating", ["Power gating"]),
        ("Clock gating", ["Clock gating"]),
        ("Integrated circuit packaging", ["Integrated circuit packaging", "Semiconductor package"]),
        ("Chiplet", ["Chiplet"]),
        ("Three-dimensional integrated circuit", ["Three-dimensional integrated circuit"]),
        ("Phase-locked loop", ["Phase-locked loop"]),
        ("SerDes", ["SerDes", "Serializer/Deserializer"]),
        ("Electromigration", ["Electromigration"]),
    ],
    "embedded": [
        ("Embedded system", ["Embedded system"]),
        ("Microcontroller", ["Microcontroller"]),
        ("Real-time operating system", ["Real-time operating system"]),
        ("ARM architecture", ["ARM architecture", "ARM Cortex-M"]),
        ("Interrupt", ["Interrupt"]),
        ("Direct memory access", ["Direct memory access"]),
        ("Serial Peripheral Interface", ["Serial Peripheral Interface",
                                         "Serial Peripheral Bus"]),
        ("I\u00b2C", ["I\u00b2C", "Inter-Integrated Circuit"]),
        ("UART", ["UART", "Universal asynchronous receiver-transmitter"]),
        ("Watchdog timer", ["Watchdog timer"]),
        ("Bootloader", ["Bootloader"]),
        ("Firmware", ["Firmware"]),
        ("Memory-mapped I/O", ["Memory-mapped I/O"]),
        ("GPIO", ["GPIO", "General-purpose input/output"]),
    ],
    "cs": [
        ("Algorithm", ["Algorithm"]),
        ("Analysis of algorithms", ["Analysis of algorithms"]),
        ("Big O notation", ["Big O notation"]),
        ("Data structure", ["Data structure"]),
        ("Graph traversal", ["Graph traversal", "Depth-first search",
                             "Breadth-first search"]),
        ("Operating system", ["Operating system"]),
        ("Database", ["Database"]),
        ("SQL", ["SQL"]),
        ("Compiler", ["Compiler"]),
        ("Concurrency (computer science)", ["Concurrency (computer science)",
                                            "Concurrent computing"]),
        ("Thread (computing)", ["Thread (computing)"]),
        ("Internet protocol suite", ["Internet protocol suite"]),
        ("Distributed computing", ["Distributed computing"]),
    ],
    "aiml": [
        ("Machine learning", ["Machine learning"]),
        ("Deep learning", ["Deep learning"]),
        ("Artificial neural network", ["Artificial neural network",
                                       "Neural network"]),
        ("Backpropagation", ["Backpropagation"]),
        ("Convolutional neural network", ["Convolutional neural network"]),
        ("Recurrent neural network", ["Recurrent neural network"]),
        ("Long short-term memory", ["Long short-term memory"]),
        ("Transformer (machine learning model)",
         ["Transformer (machine learning model)",
          "Transformer (deep learning architecture)",
          "Transformer (machine learning)"]),
        ("Attention (machine learning)", ["Attention (machine learning)"]),
        ("Stochastic gradient descent", ["Stochastic gradient descent"]),
        ("Overfitting", ["Overfitting"]),
        ("Large language model", ["Large language model"]),
        ("Retrieval-augmented generation", ["Retrieval-augmented generation"]),
    ],
}


def api_get(params, tries=TRIES):
    import requests
    for attempt in range(tries):
        try:
            r = requests.get(API, params=params, headers=UA, timeout=30)
            if r.status_code == 200 and r.text.startswith("{"):
                return r.json()
            if r.status_code == 429:
                backoff = 15 * (attempt + 1)
                print("    [HTTP 429] rate limit encountered, backing off for %ds..." % backoff, flush=True)
                time.sleep(backoff)
                continue
            raise RuntimeError("HTTP %d %r" % (r.status_code, r.text[:80]))
        except Exception as e:
            if attempt + 1 < tries:
                time.sleep(min(3 * (2 ** attempt), 30))
            else:
                print("    api failed after %d tries: %s: %s"
                      % (tries, type(e).__name__, e), flush=True)
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
        if len(text) < MIN_CHUNK_CHARS:
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
    ap = argparse.ArgumentParser(description="P4.0 domain context fetch")
    ap.add_argument("--domain", default="math", help="math|vlsi|embedded|cs|aiml")
    ap.add_argument("--refresh", action="store_true",
                    help="fetch (again) even for vlsi; writes the p4 payload")
    ap.add_argument("extras", nargs="*", help="extra concept titles")
    args = ap.parse_args()
    try:
        domain = P4.check(args.domain)
    except ValueError as e:
        print("RESULT: P4_FETCH_FAIL %s" % e)
        return 2

    out_path = os.path.join(ROOT, "data/raw/p4_%s_contexts.json" % domain)

    # vlsi default-pass: the Stage O.1 wiki corpus stays the source of record.
    if domain == "vlsi" and not args.refresh and not args.extras:
        wiki = os.path.join(ROOT, "data/raw/vlsi_wikipedia.json")
        if not os.path.isfile(wiki):
            print("RESULT: P4_FETCH_VLSI_FAIL missing %s" % wiki)
            return 1
        d = json.load(open(wiki, encoding="utf-8"))
        n_chunks = len(d.get("chunks") or [])
        print("vlsi reuse : %s (Stage O.1 corpus on disk)" % wiki)
        print("pages      : %d  chunks: %d" % (len(d.get("pages") or []), n_chunks))
        print("RESULT: P4_FETCH_VLSI_OK pages=%d chunks=%d reused=%s"
              % (len(d.get("pages") or []), n_chunks,
                 os.path.basename(wiki)))
        return 0

    concepts = list(CONCEPTS[domain]) + [(x, [x]) for x in args.extras]
    print("=" * 74)
    print("P4.0 - fetch %s reference context (login node, MediaWiki API)"
          % domain)
    print("=" * 74)
    print("concepts  : %d" % len(concepts))
    print("output    : %s" % out_path)
    print("chunking  : target %d, max %d, min %d chars"
          % (CHUNK_TARGET, CHUNK_MAX, MIN_CHUNK_CHARS))

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
            time.sleep(1.2)
        if not got:
            missing.append(requested)
            print("[miss] %r (tried: %s)" % (requested, candidates),
                  flush=True)
            continue
        if any(p["title"] == got["title"] for p in pages):
            print("[dup] %r resolved to already-fetched %r"
                  % (requested, got["title"]))
            continue
        got["requested"] = requested
        got["raw"] = got.pop("text")
        got["chars"] = len(got["raw"])
        pages.append(got)
        print("[ok] %-36s -> %-32s %6d chars  %.1fs"
              % (requested[:36], got["title"][:32], got["chars"],
                 time.time() - t0), flush=True)
        time.sleep(1.2)

    if not pages:
        print("RESULT: P4_FETCH_%s_FAILED (no pages)" % domain.upper())
        return 1

    chunks = build_chunks(pages)
    payload = {
        "stage": "P4.0",
        "domain": domain,
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
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, out_path)

    print("-" * 74)
    print("pages ok    : %d / %d   missing: %s"
          % (len(pages), len(concepts), missing or "none"))
    print("total chars : %d" % payload["total_chars"])
    print("chunks      : %d" % len(chunks))
    print("file        : %s (%d bytes)" % (out_path, os.path.getsize(out_path)))
    ok = len(pages) >= 8 and len(chunks) >= 60 and len(missing) <= 6
    print("RESULT: P4_FETCH_%s_%s pages=%d chunks=%d missing=%d"
          % (domain.upper(), "OK" if ok else "DEGRADED", len(pages),
             len(chunks), len(missing)))
    return 0 if ok else 3


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        print("RESULT: P4_FETCH_FAIL %s" % sys.exc_info()[1])
        sys.exit(1)
