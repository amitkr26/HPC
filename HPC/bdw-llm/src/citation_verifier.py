"""Citation verifier — the mechanism behind docs/BDW_INTEGRATION.md 10.3.

Design contract (from the proposal):

    A response may not be returned to the user unless every factual clause in
    it resolves to a database row that carries a `verified` flag and a
    `source_url`.

In production the "rows" are BDW's own verified opportunities/resources. This
module is deliberately corpus-agnostic and has no model or network
dependency, so it can run server-side in the AI Gateway (Zone 2) exactly as
the proposal's S5 boundary requires.

The check per sentence:
  1. content-word recall against at least one retrieved passage >= MIN_RECALL
  2. every number in the sentence must appear verbatim in that same passage
  3. every distinctive proper noun must appear in that passage

Anything failing is a claim the system cannot source. One unattached clause
fails the whole draft -- abstain and link out, do not answer.
"""
import re
import unicodedata

MIN_RECALL = 0.5

STOP = set("""a an the and or but if then than that this these those of to in on
at by for with from as is are was were be been being it its it's he she they we
you i not no do does did have has had will would can could should may might
must about into over under again more most other some such only own same so too
very s t just don now""".split())

_NUM = re.compile(r"\d[\d,\.]*\d|\d")
_WORD = re.compile(r"[A-Za-z][A-Za-z\-']+")
# a distinctive proper noun: capitalised, not sentence-initial, not a stopword
_PROPER = re.compile(r"\b([A-Z][a-zA-Z\-']{2,})\b")


def _norm(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower()


def content_words(s):
    return {w for w in (_norm(x) for x in _WORD.findall(s))
            if len(w) > 2 and w not in STOP}


def numbers(s):
    return [m.group(0) for m in _NUM.finditer(s)]


def proper_nouns(s, skip_first=True):
    """Distinctive capitalised words, ignoring the sentence-initial token."""
    out = []
    for i, m in enumerate(_PROPER.finditer(s)):
        if skip_first and i == 0:
            continue
        w = m.group(1)
        if _norm(w) in STOP:
            continue
        out.append(w)
    return out


def split_sentences(text):
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if len(p.strip()) >= 12]


def _recall(clause, passage):
    cw = content_words(clause)
    if not cw:
        return 0.0
    pw = content_words(passage)
    return len(cw & pw) / len(cw)


def best_source(clause, passages):
    """Return (index, recall, missing_numbers, missing_proper) for the best passage."""
    best = (-1, 0.0, [], [])
    for i, p in enumerate(passages):
        r = _recall(clause, p)
        if r > best[1]:
            miss_n = [n for n in numbers(clause) if n not in p]
            miss_p = [w for w in proper_nouns(clause) if w not in p]
            best = (i, r, miss_n, miss_p)
    return best


def verify(draft, passages, min_recall=MIN_RECALL):
    """Verify every sentence of `draft` attaches to `passages`.

    Returns dict(verdict, checked, failures, sentences)
    verdict is PASS only when every sentence is sourced.
    """
    sentences = split_sentences(draft)
    report = []
    failures = []
    for s in sentences:
        idx, recall, miss_n, miss_p = best_source(s, passages)
        ok = (recall >= min_recall) and not miss_n and not miss_p
        reasons = []
        if recall < min_recall:
            reasons.append("recall %.2f < %.2f" % (recall, min_recall))
        if miss_n:
            reasons.append("unsourced number(s): %s" % ", ".join(miss_n))
        if miss_p:
            reasons.append("unsourced name(s): %s" % ", ".join(miss_p))
        entry = {"sentence": s, "source_index": idx, "recall": recall,
                 "ok": ok, "reasons": reasons}
        report.append(entry)
        if not ok:
            failures.append(entry)
    return {
        "verdict": "PASS" if sentences and not failures else "FAIL",
        "checked": len(sentences),
        "failures": failures,
        "sentences": report,
        "n_passages": len(passages),
    }


def render(res):
    lines = ["VERDICT: %s   (%d sentence(s) checked, %d sourced, %d unsourced)"
             % (res["verdict"], res["checked"],
                res["checked"] - len(res["failures"]), len(res["failures"]))]
    for e in res["sentences"]:
        mark = "ok  " if e["ok"] else "FAIL"
        src = ("passage[%d]" % e["source_index"]) if e["source_index"] >= 0 else "no source"
        lines.append("  [%s] recall=%.2f %-12s %s" % (mark, e["recall"], src, e["sentence"][:78]))
        for r in e["reasons"]:
            lines.append("         -> %s" % r)
    return "\n".join(lines)


if __name__ == "__main__":
    demo_passages = [
        "A black hole is an astronomical body so compact that its gravity "
        "prevents anything, including light, from escaping. Albert Einstein's "
        "theory of general relativity predicts that any such body collapses "
        "to a singularity surrounded by an event horizon.",
        "A supermassive black hole is the largest type, with mass on the order "
        "of millions to billions of times the mass of the Sun.",
    ]
    good = ("A black hole is an astronomical body so compact that its gravity "
            "prevents anything, including light, from escaping. It is "
            "surrounded by an event horizon.")
    bad = good + " It was first observed in 1971 by the Hubble telescope."
    print("--- good (should PASS) ---")
    print(render(verify(good, demo_passages)))
    print()
    print("--- with an injected unsourced claim (should FAIL) ---")
    print(render(verify(bad, demo_passages)))
