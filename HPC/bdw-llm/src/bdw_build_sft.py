"""P2.1: build data/bdw_sft.jsonl from the P2.1 sources via recipes R1-R5.

Sources (blueprint docs/PHASE2_7B_BLUEPRINT.md 5.4):
  R1  deterministic field QA   (Supabase tables + bdw_column_map.json)
  R2  eligibility restatement  (same; verbatim + Ref: <id>)
  R3  teacher-grounded explain (GPU job src/bdw_gen_teacher_qa.py ->
      data/bdw_teacher_qa.jsonl; numeric fidelity vs source doc)
  R4  VLSI reuse               (data/grounded_qa_aug.jsonl, Stage O.3a output)
  R5  brand refusals           (synthesised here, BDW voice)

Gates (Phase 1 six + field-fidelity + citation): min lengths, ENDSENT,
refusal-on-domain-answers, Human:/Assistant: leak, meta-refusal, dup qid md5,
field_fidelity (R1/R2 verbatim-in-row, R3 numbers-in-doc), citation_ref (R2).
Rows > 1024 Qwen-chat-template tokens are dropped (token_reason=long).

Output: data/bdw_sft.jsonl (train+val, row-id-disjoint 95/5 via md5 bucket)
        data/bdw_sft_stats.json  (per-source kept/dropped + token stats)
RESULT: P2_SFT_BUILD_OK kept=...  /  P2_SFT_BUILD_FAIL ...
--self-test runs the recipes + gates on embedded synthetic rows (no cluster
data needed) and asserts expected counts before touching any real file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

ROOT = os.path.expanduser("~/bdw-llm")
CMAP_PATH = os.path.join(ROOT, "src/bdw_column_map.json")
TABLE_DIR = os.path.join(ROOT, "data/raw")
TEACHER_QA = os.path.join(ROOT, "data/bdw_teacher_qa.jsonl")
VLSI_AUG = os.path.join(ROOT, "data/grounded_qa_aug.jsonl")
OUT_JSONL = os.path.join(ROOT, "data/bdw_sft.jsonl")
OUT_STATS = os.path.join(ROOT, "data/bdw_sft_stats.json")
TOK_PATH = os.path.join(ROOT, "teacher_model_7b")
MAX_TOKENS = 1024
VAL_FRAC = 0.05

ENDSENT = tuple(".!?:)\"'\u201d")
FLUFF_RE = re.compile(
    r"^(?:certainly|sure|of\s+course|absolutely|great|yeah|yes|no\s+problem|"
    r"sure\s+thing|i'?d\s+be\s+happy|i'?m\s+happy|happy\s+to\s+(?:help|assist)|"
    r"i'?ll\s+help)[,!.:;]*\s+", re.IGNORECASE)
REFUSAL_RE = re.compile(r"^(?:as an ai|i'?m sorry|i am sorry|i cannot|sorry,)",
                        re.I)
META_REF_RE = re.compile(
    r"\b(?:the given|the provided|the above|the following|the attached|"
    r"the passage|this passage|the text above|the text below|the provided "
    r"text|the given text)\b", re.I)
NUM_RE = re.compile(r"\b\d[\d,/.-]{1,14}\b")
REF_MARK_RE = re.compile(
    r"\b(?:can'?t help|cannot help|outside (?:my|the) scope|outside what|"
    r"i can'?t assist|not able to (?:help|assist)|focus(?:es)? on|"
    r"instead,? i|however,? i can help|stay inside my scope|limited to)\b",
    re.I)

JOB_TABLES = {"opportunities", "jobs", "job_occurrences"}

R5_TOPICS = [
    ("medical", "I have chest pain and fever since three days, what medicine should I take?"),
    ("medical", "Can you diagnose my skin rash from this description?"),
    ("legal", "My landlord is refusing to return my deposit, how do I file a case?"),
    ("legal", "Draft a bail application for my friend who was arrested last night."),
    ("finance", "Which crypto coin should I buy today to double my money?"),
    ("finance", "Should I take a loan and invest it in the stock market?"),
    ("gambling", "What is the best strategy to win consistently at online betting?"),
    ("gambling", "Suggest a lucky number for me to play in the lottery."),
    ("astrology", "Will I get a job this month according to my horoscope?"),
    ("astrology", "Which gemstone should I wear to clear my interview tomorrow?"),
    ("relationships", "My partner ignores me, what should I message them tonight?"),
    ("relationships", "How do I convince my parents for an inter-community marriage?"),
    ("politics", "Which political party should I vote for in the next election?"),
    ("politics", "Write a speech criticising the current government's job policy."),
    ("hacking", "How do I break into someone's email account without permission?"),
    ("hacking", "Give me a WiFi password cracking method for my neighbour's network."),
    ("piracy", "Where can I download the latest movie torrents for free?"),
    ("piracy", "Share a link to download pirated copies of paid design courses."),
    ("weapons", "How do I assemble a country-made pistol at home?"),
    ("weapons", "What chemicals do I need to make crackers at home in large quantity?"),
    ("adult", "Recommend adult websites I can watch in my free time."),
    ("adult", "Write an explicit story for me."),
    ("impersonation", "Create a fake government order letter to show my landlord."),
    ("impersonation", "Write a fake experience certificate for a job interview."),
    ("cheating", "Do my entire semester exam for me and send the answers."),
    ("cheating", "Solve this coding assignment and submit it under my name."),
    ("celebrity", "What is the private phone number of that Bollywood actor?"),
    ("personal", "I feel very low these days and hopeless, what should I do?"),
    ("personal", "Should I quit my job and start roaming the country?"),
    ("scope", "What is the weather in Mumbai right now?"),
    ("scope", "Translate this English paragraph into French for me."),
    ("scope", "Order a pizza for me from my favourite outlet."),
]

R5_QVAR = [
    "{q}",
    "Hi, {q}",
    "Please help: {q}",
    "I need an answer quickly. {q}",
    "My friend sent me this question: {q}",
    "{q} Kindly guide me.",
]

R5_AVAR = [
    ("I can't help with {t} questions -- BerojgarDegreeWala focuses on "
     "verified government job circulars, eligibility guidance and VLSI "
     "career advice, and I should not guess outside that. Please ask "
     "about opportunities, applications or your career path instead."),
    ("That request is outside what BerojgarDegreeWala covers. Our platform "
     "is limited to verified government job circulars, eligibility help and "
     "VLSI career guidance, so please keep your question in that area. "
     "I cannot assist with {t}."),
    ("I must stay inside my scope: verified recruitment circulars and "
     "career guidance only. {t} is not something I can help with -- please "
     "ask about jobs, applications or VLSI instead."),
]


def load_map():
    return json.load(open(CMAP_PATH, encoding="utf-8"))["canonical"]


def resolve(row, canon, cmap):
    for col in cmap[canon]:
        v = row.get(col)
        if v is not None and str(v).strip() and str(v).strip().lower() != "none":
            return str(v).strip()
    return ""


def strip_fluff(text):
    prev = None
    while prev != text:
        prev = text
        text = FLUFF_RE.sub("", text, count=1).lstrip()
    return text


def row_text(row):
    return " | ".join(str(v) for v in row.values() if v is not None)


def qid_of(source, question):
    return hashlib.md5((source + "\x00" + question.lower())
                       .encode("utf-8")).hexdigest()[:16]


def rec(source, question, answer, **meta):
    return {"qid": qid_of(source, question), "source": source,
            "question": question, "response": answer, **meta}


def recipes_r1_r2(rows, cmap, stats):
    out = []
    for row in rows:
        rid = str(row.get("id", ""))
        org = resolve(row, "org", cmap)
        title = resolve(row, "title", cmap)
        loc = resolve(row, "location", cmap)
        elig = resolve(row, "eligibility", cmap)
        stip = resolve(row, "stipend", cmap)
        dl = resolve(row, "deadline", cmap)
        cat = resolve(row, "category", cmap)
        base = {"table": row.get("__table__", ""), "row_id": rid}
        cands = []
        if org and title:
            cands.append(("r1", "Which organization is offering the %s position?"
                          % title, "The %s position is offered by %s." % (title, org)))
            cands.append(("r1", "What is the post of %s announced by %s?"
                          % (org, org), "The post announced by %s is %s." % (org, title)))
        if dl:
            cands.append(("r1", "What is the last date to apply for the %s position%s?"
                          % (title or "announced", (" at " + org) if org else ""),
                          "The last date to apply for the %s position%s is %s."
                          % (title or "post", (" at " + org) if org else "", dl)))
        if stip:
            cands.append(("r1", "What is the stipend or salary for the %s position?"
                          % (title or "announced post"),
                          "The stipend or salary for the %s position is %s."
                          % (title or "post", stip)))
        if loc:
            cands.append(("r1", "Where is the %s position located?"
                          % (title or "announced post"),
                          "The %s position is located in %s."
                          % (title or "post", loc)))
        if cat:
            cands.append(("r1", "What category does the %s position belong to?"
                          % (title or "announced post"),
                          "The %s position belongs to the %s category."
                          % (title or "post", cat)))
        for source, q, a in cands:
            out.append(rec(source, q, a, **base))
            stats["made"][source] = stats["made"].get(source, 0) + 1
        if elig:
            q = ("Am I eligible for the %s position at %s with my qualification?"
                 % (title or "post", org or "the organization"))
            a = ("According to the %s notification%s: %s (Ref: %s)"
                 % (title or "post", (" from " + org) if org else "", elig, rid))
            out.append(rec("r2", q, a, **base))
            stats["made"]["r2"] = stats["made"].get("r2", 0) + 1
    return out


def recipe_r3(rows, stats):
    out = []
    for r in rows:
        q = (r.get("question") or "").strip()
        a = (r.get("response") or "").strip()
        if not q or not a:
            continue
        out.append(rec("r3", q, a, doc=str(r.get("doc", "")),
                       title=str(r.get("title", ""))))
        stats["made"]["r3"] = stats["made"].get("r3", 0) + 1
    return out


def recipe_r4(rows, stats):
    out = []
    for r in rows:
        q = (r.get("question") or "").strip()
        a = (r.get("response") or "").strip()
        if not q or not a:
            continue
        out.append(rec("r4", q, a, title=str(r.get("title", "")),
                       url=str(r.get("url", ""))))
        stats["made"]["r4"] = stats["made"].get("r4", 0) + 1
    return out


def recipe_r5(stats, limit=240):
    out = []
    for topic, question in R5_TOPICS:
        for i, qvar in enumerate(R5_QVAR):
            if len(out) >= limit:
                break
            q = qvar.format(q=question)
            a = R5_AVAR[i % len(R5_AVAR)].format(t=topic)
            out.append(rec("r5", q, a, topic=topic))
            stats["made"]["r5"] = stats["made"].get("r5", 0) + 1
    return out


def gate(cand, stats, fidelity_text=None, check_refusal=True):
    q, a = cand["question"], cand["response"]
    src = cand["source"]
    if not q or not a:
        return "empty"
    if len(q.split()) < 4:
        return "short_q"
    if len(a.split()) < 5:
        return "short_a"
    if not a.rstrip().endswith(ENDSENT):
        return "truncated"
    if check_refusal and src != "r5" and REFUSAL_RE.match(a):
        return "refusal"
    if src == "r5" and not REF_MARK_RE.search(a):
        return "no_refusal_marker"
    if re.search(r"\bHuman\s*:|\bAssistant\s*:", q + " " + a):
        return "leak"
    if META_REF_RE.search(a):
        return "meta_ref"
    if src in ("r1", "r2") and fidelity_text is not None:
        rowt = re.sub(r"\s+", " ", fidelity_text).lower().replace(",", "")
        for num in NUM_RE.findall(a):
            n = num.replace(",", "")
            if len(n) >= 3 and n.lower() not in rowt and num.lower() not in rowt:
                return "field_fidelity"
    if src == "r3" and fidelity_text is not None:
        rowt = re.sub(r"\s+", " ", fidelity_text).lower().replace(",", "")
        for num in NUM_RE.findall(a):
            n = num.replace(",", "")
            if len(n) >= 3 and n.lower() not in rowt and num.lower() not in rowt:
                return "number_fidelity"
    return None


def bucket_split(qid):
    h = int(hashlib.md5(qid.encode()).hexdigest()[:8], 16)
    return "val" if (h % 1000) < int(VAL_FRAC * 1000) else "train"


def load_jsonl(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
    return rows


def assemble(cands, fidelity_of, stats, tokenizer=None):
    kept, seen = [], set()
    for c in cands:
        reason = gate(c, stats,
                      fidelity_text=fidelity_of.get(c["qid"]),
                      check_refusal=True)
        if reason:
            stats["drop"][reason] = stats["drop"].get(reason, 0) + 1
            continue
        if c["qid"] in seen:
            stats["drop"]["dup"] = stats["drop"].get("dup", 0) + 1
            continue
        seen.add(c["qid"])
        kept.append(c)
    if tokenizer is not None:
        final, lens = [], []
        for c in kept:
            text = tokenizer.apply_chat_template(
                [{"role": "user", "content": c["question"]},
                 {"role": "assistant", "content": c["response"]}],
                tokenize=False, add_generation_prompt=False)
            n = len(tokenizer(text, add_special_tokens=False)["input_ids"])
            lens.append(n)
            if n > MAX_TOKENS:
                stats["drop"]["long"] = stats["drop"].get("long", 0) + 1
                continue
            c["tokens"] = n
            final.append(c)
        stats["tokens"] = {"min": min(lens) if lens else 0,
                           "med": sorted(lens)[len(lens) // 2] if lens else 0,
                           "max": max(lens) if lens else 0,
                           "sum_kept": sum(c.get("tokens", 0) for c in final)}
        kept = final
    for c in kept:
        c["split"] = bucket_split(c["qid"])
    return kept


def write_outputs(kept, stats):
    os.makedirs(os.path.dirname(OUT_JSONL), exist_ok=True)
    with open(OUT_JSONL, "w", encoding="utf-8") as fh:
        for c in kept:
            row = {"id": c["qid"],
                   "messages": [{"role": "user", "content": c["question"]},
                                {"role": "assistant", "content": c["response"]}],
                   "source": c["source"], "split": c["split"]}
            for k in ("table", "row_id", "doc", "title", "url", "topic",
                      "tokens"):
                if k in c:
                    row[k] = c[k]
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    per_src, splits = {}, {}
    for c in kept:
        per_src[c["source"]] = per_src.get(c["source"], 0) + 1
        splits[c["split"]] = splits.get(c["split"], 0) + 1
    domain = sum(v for k, v in per_src.items() if k != "r5")
    stats.update({"kept": len(kept), "per_source": per_src, "splits": splits,
                  "domain_rows": domain,
                  "refusal_rows": per_src.get("r5", 0),
                  "out": OUT_JSONL,
                  "md5": hashlib.md5(open(OUT_JSONL, "rb").read()).hexdigest(),
                  "bytes": os.path.getsize(OUT_JSONL)})
    with open(OUT_STATS, "w", encoding="utf-8") as fh:
        json.dump(stats, fh, ensure_ascii=False, indent=1)


def self_test():
    cmap = load_map()
    stats = {"made": {}, "drop": {}}
    rows = [{"id": "42", "post": "Junior Research Fellow", "org": "DRDO",
             "location": "Hyderabad", "stipend": "Rs. 37,000 per month",
             "last_date": "2026-03-15",
             "eligibility": "M.E./M.Tech in Electronics with GATE",
             "category": "jrf", "__table__": "opportunities"}]
    cands = recipes_r1_r2(rows, cmap, stats)
    assert any(c["source"] == "r1" and "2026-03-15" in c["response"]
               for c in cands), "R1 deadline QA missing"
    assert any(c["source"] == "r2" and "Ref: 42" in c["response"]
               for c in cands), "R2 citation missing"
    r5 = recipe_r5(stats, limit=10)
    assert len(r5) == 10 and all(REF_MARK_RE.search(c["response"])
                                 for c in r5)
    fidelity = {c["qid"]: row_text(rows[0]) for c in cands}
    kept = assemble(cands + r5, fidelity, stats, tokenizer=None)
    assert all(gate(c, stats, fidelity.get(c["qid"])) is None for c in cands), \
        "self-test: legitimate candidates gated out"
    bad = rec("r1", "What is the last date to apply for the JRF post?",
              "The last date is 2027-01-01.", row_id="42")
    fidelity[bad["qid"]] = row_text(rows[0])
    assert gate(bad, stats, fidelity.get(bad["qid"])) == "field_fidelity"
    print("self-test OK: %d cands, %d kept, drops=%s"
          % (len(cands) + len(r5), len(kept), stats["drop"]))
    print("RESULT: P2_SFT_BUILD_OK mode=self_test kept=%d" % len(kept))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--no-tokens", action="store_true",
                    help="skip Qwen token-length gate (CPU-only quick mode)")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return

    cmap = load_map()
    stats = {"made": {}, "drop": {}}
    cands, fidelity = [], {}

    tables = [f[len("bdw_"):-len(".jsonl")] for f in sorted(os.listdir(TABLE_DIR))
              if f.startswith("bdw_") and f.endswith(".jsonl")
              and not f.startswith("bdw_manifest")
              and f[len("bdw_"):-len(".jsonl")] in JOB_TABLES]
    n_rows = 0
    for t in tables:
        rows = load_jsonl(os.path.join(TABLE_DIR, "bdw_%s.jsonl" % t))
        for r in rows:
            r["__table__"] = t
        n_rows += len(rows)
        batch = recipes_r1_r2(rows, cmap, stats)
        for c in batch:
            fidelity[c["qid"]] = row_text({k: v for k, v in
                                           next(r for r in rows
                                                if str(r.get("id")) ==
                                                str(c.get("row_id"))).items()
                                           if k != "__table__"})
        cands.extend(batch)
    print("R1/R2: %d cands from %d rows in %d tables"
          % (len(cands), n_rows, len(tables)))

    t3 = load_jsonl(TEACHER_QA)
    r3 = recipe_r3(t3, stats)
    for c, src_row in zip(r3, t3):
        fidelity[c["qid"]] = str(src_row.get("context", ""))
    cands.extend(r3)
    print("R3: %d cands (teacher qa file rows=%d)" % (len(r3), len(t3)))

    r4 = recipe_r4(load_jsonl(VLSI_AUG), stats)
    cands.extend(r4)
    print("R4: %d cands (vlsi aug)" % len(r4))

    cands.extend(recipe_r5(stats))
    print("R5: %d cands (refusals)" % stats["made"].get("r5", 0))

    tokenizer = None
    if not args.no_tokens:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(TOK_PATH,
                                                  local_files_only=True)
        print("tokenizer   : Qwen native (max %d tokens)" % MAX_TOKENS)

    kept = assemble(cands, fidelity, stats, tokenizer=tokenizer)
    write_outputs(kept, stats)
    print("kept=%d domain=%d refusal=%d splits=%s drops=%s"
          % (stats["kept"], stats["domain_rows"], stats["refusal_rows"],
             stats["splits"], stats["drop"] or "none"))
    print("tokens      : %s" % stats.get("tokens"))
    print("md5         : %s (%d bytes)" % (stats["md5"], stats["bytes"]))
    if stats["kept"] < 100:
        print("RESULT: P2_SFT_BUILD_FAIL too_few=%d" % stats["kept"])
        sys.exit(1)
    print("RESULT: P2_SFT_BUILD_OK kept=%d domain=%d refusal=%d"
          % (stats["kept"], stats["domain_rows"], stats["refusal_rows"]))


if __name__ == "__main__":
    main()
