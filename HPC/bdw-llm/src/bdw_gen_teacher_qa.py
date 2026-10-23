"""P2.1 R3: 7B teacher writes grounded job/career QA from BDW's own pages.

Adapted from the proven Stage O.3a generator (src/generate_grounded_qa.py):
same wall-clock LIMIT + resume-by-chunk + left-padding + MAX_NEW=512 +
ENDSENT/refusal/leak/meta gates, minus the 16K tokenization step (Phase 2
trains with the native Qwen tokenizer in trl, not our BPE).

Context sources (same on-disk shape as Stage O.1):
  default  data/raw/bdw_domain.jsonl   (Stage P scrape of BDW public pages,
           {"text": ...} rows) -- available NOW, no Supabase needed
  --contexts data/raw/bdw_contexts.json (Supabase circulars once DNS works;
           {"chunks":[{"id","title","text"}]})

Output: data/bdw_teacher_qa.jsonl with {qid, doc, title, question, response,
context} -- context kept for the R3 number-fidelity gate in bdw_build_sft.py.

RESULT: P2_TEACHER_QA_OK pairs=... / P2_TEACHER_QA_PARTIAL chunks=... /
P2_TEACHER_QA_FAIL
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time

import torch

ROOT = os.path.expanduser("~/bdw-llm")
DOMAIN = os.path.join(ROOT, "data/raw/bdw_domain.jsonl")
OUT_JSONL = os.path.join(ROOT, "data/bdw_teacher_qa.jsonl")
TEACHER = os.path.join(ROOT, "teacher_model_7b")
TEACHER_ID = "Qwen/Qwen2.5-7B-Instruct"

BATCH = 4
MAX_NEW = 512
TEMP, TOP_P = 0.3, 0.9
SEED = 1234
LIMIT = 11 * 60

INSTRUCTION = (
    "Read the following text from BerojgarDegreeWala, a government-job and "
    "VLSI-career platform. Generate 3 accurate Question and Answer pairs that "
    "a job-seeking user would ask, based strictly on this text. "
    "Do not invent information."
)
FORMAT_SPEC = (
    "Format:\n"
    "Q1: ...\nA1: ...\nQ2: ...\nA2: ...\nQ3: ...\nA3: ...\n"
    "Good topics: eligibility, dates, organizations, roles, career guidance, "
    "salary or stipend facts mentioned in the text. "
    "Answers must be 30 to 90 words, complete sentences, using only facts "
    "from the text. Output nothing else."
)

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
PAIR_RE = re.compile(
    r"Q\s*(\d)\s*[:.\-]\s*(.+?)\s*A\s*\1\s*[:.\-]\s*(.+?)"
    r"(?=\s*Q\s*\d\s*[:.\-]|\Z)", re.S)


def strip_fluff(text):
    prev = None
    while prev != text:
        prev = text
        text = FLUFF_RE.sub("", text, count=1).lstrip()
    return text


def parse_pairs(text):
    text = re.sub(r"\*\*", "", text)
    out = []
    for m in PAIR_RE.finditer(text):
        q = " ".join(m.group(2).split())
        a = strip_fluff(" ".join(m.group(3).split()))
        out.append((q, a))
    return out


def load_contexts(args):
    if args.contexts:
        data = json.load(open(args.contexts, encoding="utf-8"))
        return data["chunks"]
    chunks = []
    with open(DOMAIN, encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            line = line.strip()
            if not line:
                continue
            text = json.loads(line).get("text", "")
            if len(text) < 200:
                continue
            title = text.split("\n", 1)[0][:80]
            chunks.append({"id": "bdwdoc_%04d" % i, "title": title,
                           "text": text[:6000]})
    return chunks


def load_done():
    done, rows = set(), []
    if os.path.exists(OUT_JSONL):
        with open(OUT_JSONL, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                rows.append(r)
                if r.get("question"):
                    done.add(r.get("doc"))
    return done, rows


def device_of(model):
    try:
        return next(model.parameters()).device
    except StopIteration:
        return "cpu"


def generate(chunks, model, tok, done, stats):
    todo = [c for c in chunks if c["id"] not in done]
    print("chunks total=%d done=%d todo=%d" % (len(chunks), len(done),
                                               len(todo)), flush=True)
    t_start = time.time()
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    with open(OUT_JSONL, "a", encoding="utf-8") as fh:
        for i in range(0, len(todo), BATCH):
            if time.time() - t_start > LIMIT:
                print("[wall] %ds elapsed, stopping -- %d chunks left"
                      % (LIMIT, len(todo) - i), flush=True)
                break
            batch = todo[i:i + BATCH]
            prompts = []
            for c in batch:
                body = "%s\n\n%s\n\nText:\n%s" % (INSTRUCTION, FORMAT_SPEC,
                                                  c["text"])
                prompts.append(tok.apply_chat_template(
                    [{"role": "user", "content": body}],
                    tokenize=False, add_generation_prompt=True))
            enc = tok(prompts, return_tensors="pt", padding=True,
                      truncation=True, max_length=2048).to(device_of(model))
            n_prompt = int(enc["input_ids"].shape[1])
            with torch.no_grad():
                out = model.generate(
                    input_ids=enc["input_ids"],
                    attention_mask=enc["attention_mask"],
                    max_new_tokens=MAX_NEW, do_sample=True,
                    temperature=TEMP, top_p=TOP_P,
                    pad_token_id=tok.pad_token_id or tok.eos_token_id,
                    eos_token_id=tok.eos_token_id)
            gen = out[:, n_prompt:]
            for c, ids in zip(batch, gen):
                raw = tok.decode(ids, skip_special_tokens=True)
                stats["chunks_done"] += 1
                pairs = parse_pairs(raw)
                if not pairs:
                    stats["drop"]["parse_fail"] = \
                        stats["drop"].get("parse_fail", 0) + 1
                written = 0
                for q, a in pairs:
                    reason = None
                    if not q or not a:
                        reason = "empty"
                    elif len(q.split()) < 4:
                        reason = "short_q"
                    elif len(a.split()) < 5:
                        reason = "short_a"
                    elif not a.rstrip().endswith(ENDSENT):
                        reason = "truncated"
                    elif REFUSAL_RE.match(a):
                        reason = "refusal"
                    elif re.search(r"\bHuman\s*:|\bAssistant\s*:", a):
                        reason = "leak"
                    elif META_REF_RE.search(a):
                        reason = "meta_ref"
                    if reason:
                        stats["drop"][reason] = stats["drop"].get(reason, 0) + 1
                        continue
                    qid = hashlib.md5(
                        (c["id"] + "\x00" + q.lower()).encode("utf-8")
                    ).hexdigest()[:16]
                    rec = {"qid": qid, "doc": c["id"], "title": c["title"],
                           "question": q, "response": a,
                           "context": c["text"][:4000],
                           "teacher": TEACHER_ID,
                           "decode": {"temperature": TEMP, "top_p": TOP_P,
                                      "max_new_tokens": MAX_NEW,
                                      "seed": SEED}}
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    written += 1
                    stats["pairs_kept"] += 1
                if written == 0:
                    fh.write(json.dumps({
                        "doc": c["id"], "qid": None, "title": c["title"],
                        "question": "", "response": "", "context": "",
                        "note": "no_usable_pairs", "teacher": TEACHER_ID},
                        ensure_ascii=False) + "\n")
                fh.flush()
            done_n = min(i + BATCH, len(todo))
            rate = done_n / max(time.time() - t_start, 1e-9)
            print("[gen] %d/%d chunks  %.2f/s  elapsed %.0fs  eta %.0fs"
                  % (done_n, len(todo), rate, time.time() - t_start,
                     (len(todo) - done_n) / max(rate, 1e-9)), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--contexts", default="",
                    help="optional Supabase contexts json (Stage O shape)")
    ap.add_argument("--limit-s", type=int, default=LIMIT)
    args = ap.parse_args()
    globals()["LIMIT"] = args.limit_s

    chunks = load_contexts(args)
    print("=" * 74)
    print("P2.1 R3 - TEACHER GROUNDED QA FROM BDW PAGES")
    print("=" * 74)
    print("chunks    : %d" % len(chunks))
    print("teacher   : %s" % TEACHER)
    print("output    : %s" % OUT_JSONL)
    if not chunks:
        print("RESULT: P2_TEACHER_QA_FAIL no_contexts")
        sys.exit(1)

    done, _ = load_done()
    print("resume    : %d doc ids already done" % len(done))

    from transformers import AutoModelForCausalLM, AutoTokenizer
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(TEACHER, local_files_only=True)
    tok.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained(
        TEACHER, torch_dtype=torch.bfloat16, local_files_only=True)
    model = model.to("cuda")
    print("[teacher] loaded in %.1fs" % (time.time() - t0), flush=True)

    stats = {"chunks_done": 0, "pairs_kept": 0, "drop": {}}
    generate(chunks, model, tok, done, stats)

    done2, rows = load_done()
    usable = [r for r in rows if (r.get("question") or "").strip()]
    print("-" * 74)
    print("docs done  : %d / %d" % (len(done2), len(chunks)))
    print("pairs kept : %d usable, drops=%s" % (len(usable),
                                                stats["drop"] or "none"))
    if len(done2) < len(chunks):
        print("RESULT: P2_TEACHER_QA_PARTIAL docs=%d/%d pairs=%d"
              % (len(done2), len(chunks), len(usable)))
        return
    print("RESULT: P2_TEACHER_QA_OK pairs=%d docs=%d"
          % (len(usable), len(done2)))


if __name__ == "__main__":
    main()
