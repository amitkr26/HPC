"""Stage P: build a domain corpus from BerojgarDegreeWala's own live pages.

The proposal (docs/BDW_INTEGRATION.md 8) recommends retraining the BPE on
BDW's own text -- circulars, resources, FAQ, org profiles, JDs, news. We do
not have the production DB from here, so this builds the closest available
proxy: the public pages of berojgardegreewala.app themselves.

Writes data/raw/bdw_domain.jsonl in the same {"text": ...} format that
src/train_tokenizer.py already consumes.
"""
import html as htmlmod
import json
import os
import re
import time
import urllib.request

ROOT = os.path.expanduser("~/bdw-llm")
OUT = os.path.join(ROOT, "data/raw/bdw_domain.jsonl")
BASE = "https://www.berojgardegreewala.app"

PATHS = [
    "/", "/ask-ai", "/opportunities", "/organizations", "/news", "/resources",
    "/about", "/contact", "/privacy", "/terms",
    "/resources/vlsi-salary-india", "/resources/vlsi-career-roadmap",
    "/resources/drdo-internship-guide", "/resources/jrf-vs-srf-difference",
    "/resources/vlsi-career-guide",
    "/category/jrf", "/category/govt-job", "/category/internship",
    "/opportunities/freshers",
    "/opportunities/role/asic-design", "/opportunities/role/physical-design",
    "/opportunities/role/design-verification", "/opportunities/role/rtl-design",
    "/opportunities/role/dft", "/opportunities/role/analog-design",
    "/opportunities/role/fpga-design", "/opportunities/role/vlsi-layout",
    "/opportunities/role/embedded-systems",
    "/opportunities/location/bengaluru", "/opportunities/location/hyderabad",
    "/opportunities/location/noida", "/opportunities/location/pune",
    "/opportunities/location/chennai", "/opportunities/location/ahmedabad",
    "/organizations/intel", "/organizations/qualcomm", "/organizations/cadence",
    "/organizations/synopsys", "/organizations/texas-instruments",
    "/organizations/tessolve", "/organizations/nxp-semiconductors",
    "/organizations/micron-technology", "/organizations/analog-devices",
    "/organizations/arm-holdings", "/organizations/tsmc",
]

TAG = re.compile(r"<(script|style|noscript|svg)[^>]*>.*?</\1>", re.S | re.I)
BR = re.compile(r"<(br|/p|/div|/li|/h[1-6]|/tr)[^>]*>", re.I)
TAGONLY = re.compile(r"<[^>]+>")
WS = re.compile(r"[ \t]+")


def to_text(raw):
    raw = TAG.sub(" ", raw)
    raw = BR.sub("\n", raw)
    raw = TAGONLY.sub(" ", raw)
    raw = htmlmod.unescape(raw)
    lines = [WS.sub(" ", l).strip() for l in raw.split("\n")]
    return "\n".join(l for l in lines if l)


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    total_chars = total_bytes = 0
    seen = set()
    with open(OUT, "w", encoding="utf-8") as fh:
        for p in PATHS:
            url = BASE + p
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "BDW-corpus/1.0"})
                with urllib.request.urlopen(req, timeout=45) as r:
                    raw = r.read().decode("utf-8", "replace")
                    status = r.status
            except Exception as e:
                print("  %-46s FAIL %s: %s" % (p, type(e).__name__, e))
                time.sleep(0.4)
                continue
            text = to_text(raw)
            key = text[:400]
            print("  %-46s %3d  %7d B text  %6d chars" % (p, status, len(raw), len(text)))
            total_bytes += len(raw.encode("utf-8", "replace"))
            if len(text) >= 200 and key not in seen:
                seen.add(key)
                fh.write(json.dumps({"text": text, "source": url}) + "\n")
                total_chars += len(text)
            time.sleep(0.35)
    n = sum(1 for _ in open(OUT, encoding="utf-8"))
    print()
    print("pages fetched     : %d" % len(PATHS))
    print("docs written      : %d" % n)
    print("corpus chars      : %d" % total_chars)
    print("corpus bytes      : %d (~%.1f MB)" % (total_chars, total_chars / 1e6))
    print("saved             :", OUT, os.path.getsize(OUT), "bytes")
    print("RESULT: DOMAIN_CORPUS_%s" % ("OK" if total_chars > 20000 else "TOO_SMALL"))


if __name__ == "__main__":
    main()
