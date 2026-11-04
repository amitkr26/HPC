"""Stage O.3a (grounded distillation): 7B teacher writes Q&A ONLY from real
Wikipedia text, then we tokenize into grounded_shards/ for the student.

Why this exists (Stage N lesson): free generation let the teacher fabricate,
and max_new_tokens=224 then truncated 72% of answers mid-sentence -- the
student learned to ramble and stop anywhere while held-out ppl still fell.
Grounded generation fixes both:

  * context: data/raw/vlsi_wikipedia.json (Stage O.1) is the ONLY knowledge
    source; the teacher is instructed to invent nothing.
  * max_new_tokens=512 (CRITICAL) and any answer that does not end in
    terminal punctuation is DROPPED, so a truncated answer can never enter
    the training shards.
  * chat-style fluff openers are stripped from answers.

Pipeline (single GPU job, wall-safe via resume):

  1. resume by chunk id -- already-written chunks are skipped, so a 15-min
     MaxWall kill loses at most the in-flight batch.
  2. for each chunk: one teacher call generating 3 Q&A pairs, parsed as
     Q1:/A1: ... Q3:/A3:.
  3. filter/dedupe -> data/grounded_qa.jsonl (audit trail with provenance).
  4. when every chunk is done: tokenize with the Stage K 16K-BPE template
     and pack balanced shards into data/distilled_tokens/grounded_shards/,
     running the full Stage K verification suite before RESULT.
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
from tokenizers import Tokenizer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.expanduser("~/bdw-llm")
CTX = os.path.join(ROOT, "data/raw/vlsi_wikipedia.json")
OUT_JSONL = os.path.join(ROOT, "data/grounded_qa.jsonl")
OUT_DIR = os.path.join(ROOT, "data/distilled_tokens")
SHARD_DIR = os.path.join(OUT_DIR, "grounded_shards")
META = os.path.join(OUT_DIR, "grounded_meta.json")
TEACHER = os.path.join(ROOT, "teacher_model_7b")
TEACHER_ID = "Qwen/Qwen2.5-7B-Instruct"
TOK_PATH = os.path.join(ROOT, "tokenizer/tokenizer.json")

BATCH = 4
MAX_NEW = 512                 # CRITICAL: N.2's 224 truncated 72% mid-sentence
TEMP, TOP_P = 0.3, 0.9
SEED = 1234
LIMIT = 11 * 60               # stop with walltime headroom; resume re-submits
SEQ_LEN = 1024

INSTRUCTION = (
    "Read the following text. Generate 3 accurate Question and Answer pairs "
    "based strictly on this text. Do not invent information."
)
FORMAT_SPEC = (
    "Format:\n"
    "Q1: ...\nA1: ...\nQ2: ...\nA2: ...\nQ3: ...\nA3: ...\n"
    "Answers must be 40 to 90 words, written as complete sentences that "
    "explain the concept, using only facts from the text. Output nothing else."
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
                done.add(r.get("chunk"))
    return done, rows


def generate(chunks, model, tok, done, stats):
    todo = [c for c in chunks if c["id"] not in done]
    print("chunks total=%d done=%d todo=%d" % (len(chunks), len(done), len(todo)))
    t_start = time.time()
    torch.manual_seed(SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(SEED)
    with open(OUT_JSONL, "a", encoding="utf-8") as fh:
        for i in range(0, len(todo), BATCH):
            if time.time() - t_start > LIMIT:
                print("[wall] %ds elapsed, stopping -- %d chunks left"
                      % (LIMIT, len(todo) - i))
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
                stats["tokens_raw"] += int(ids.shape[0])
                pairs = parse_pairs(raw)
                if not pairs:
                    stats["drop"]["parse_fail"] = \
                        stats["drop"].get("parse_fail", 0) + 1
                written = 0
                for qi, (q, a) in enumerate(pairs, 1):
                    reason = None
                    if not q or not a:
                        reason = "empty"
                    elif len(q.split()) < 4:
                        reason = "short_q"
                    elif len(a.split()) < 5:
                        reason = "short_a"
                    elif not a.rstrip().endswith(ENDSENT):
                        reason = "truncated"          # the N.2 bug, gated here
                    elif REFUSAL_RE.match(a):
                        reason = "refusal"
                    elif re.search(r"\bHuman\s*:|\bAssistant\s*:", a):
                        reason = "leak"
                    elif META_REF_RE.search(a):
                        reason = "meta_ref"
                    if reason:
                        stats["drop"][reason] = stats["drop"].get(reason, 0) + 1
                        continue
                    qid = hashlib.md5(q.lower().encode("utf-8")).hexdigest()[:16]
                    if qid in stats["seen_q"]:
                        stats["drop"]["dup"] = stats["drop"].get("dup", 0) + 1
                        continue
                    stats["seen_q"].add(qid)
                    rec = {"qid": qid, "chunk": c["id"], "title": c["title"],
                           "url": c["url"], "requested": c["requested"],
                           "question": q, "response": a,
                           "teacher": TEACHER_ID,
                           "decode": {"chat_template": True,
                                      "temperature": TEMP, "top_p": TOP_P,
                                      "max_new_tokens": MAX_NEW, "seed": SEED}}
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    written += 1
                    stats["pairs_kept"] += 1
                if written == 0:
                    # mark the chunk processed so resume never loops on it;
                    # tokenization filters these markers out
                    fh.write(json.dumps({
                        "chunk": c["id"], "qid": None, "title": c["title"],
                        "url": c["url"], "requested": c["requested"],
                        "question": "", "response": "",
                        "note": "no_usable_pairs", "teacher": TEACHER_ID,
                        "decode": {"max_new_tokens": MAX_NEW, "seed": SEED}},
                        ensure_ascii=False) + "\n")
                fh.flush()
                stats["pairs_written_this_call"] += written
            done_n = min(i + BATCH, len(todo))
            rate = done_n / max(time.time() - t_start, 1e-9)
            print("[gen] %d/%d chunks  %.2f/s  elapsed %.0fs  eta %.0fs"
                  % (done_n, len(todo), rate, time.time() - t_start,
                     (len(todo) - done_n) / max(rate, 1e-9)), flush=True)


def device_of(model):
    try:
        return next(model.parameters()).device
    except StopIteration:
        return "cpu"


def tokenize_and_shard(rows):
    tok = Tokenizer.from_file(TOK_PATH)
    bos = tok.token_to_id("<|bos|>")
    eos = tok.token_to_id("<|eos|>")
    pad = tok.token_to_id("<|pad|>")
    checks = {}

    def build(q, a):
        return ([bos] + tok.encode("User: " + q, add_special_tokens=False).ids
                + [eos, bos]
                + tok.encode("Assistant: " + a, add_special_tokens=False).ids
                + [eos])

    all_ids, lens = [], []
    for r in rows:
        ids = build(r["question"], r["response"])
        all_ids.extend(ids)
        lens.append(len(ids))
    n = len(rows)
    arr_ids = all_ids
    checks["id_range_in_vocab"] = min(arr_ids) >= 1 and max(arr_ids) < tok.get_vocab_size()
    checks["no_pad_leak"] = pad not in arr_ids
    checks["bos_exact"] = arr_ids.count(bos) == 2 * n
    checks["eos_exact"] = arr_ids.count(eos) == 2 * n
    checks["all_start_bos"] = all(build(r["question"], r["response"])[0] == bos for r in rows)
    checks["all_end_eos"] = all(build(r["question"], r["response"])[-1] == eos for r in rows)

    tmpl_ok = rt_ok = 0
    sample = rows[:6]
    for r in sample:
        lit = tok.encode(
            "<|bos|>User: %s<|eos|><|bos|>Assistant: %s<|eos|>"
            % (r["question"], r["response"]), add_special_tokens=False).ids
        if lit == build(r["question"], r["response"]):
            tmpl_ok += 1
        text = tok.decode(build(r["question"], r["response"]),
                          skip_special_tokens=False)
        if tok.encode(text, add_special_tokens=False).ids == build(r["question"], r["response"]):
            rt_ok += 1
    checks["literal_template_matches_build"] = (tmpl_ok == len(sample))
    checks["decode_encode_roundtrip"] = (rt_ok == len(sample))

    import numpy as np
    stream = np.asarray(arr_ids, dtype=np.int32)
    np.save(os.path.join(OUT_DIR, "grounded_stream.npy"), stream)
    rows_total = stream.size // SEQ_LEN
    tail = stream.size % SEQ_LEN
    print("tokens=%d rows=%d tail=%d  pair_tokens min/med/max=%d/%d/%d"
          % (stream.size, rows_total, tail, min(lens),
             sorted(lens)[len(lens) // 2], max(lens)))
    if rows_total < 4:
        print("RESULT: O3A_GROUNDED_FAILED too_few_rows=%d" % rows_total)
        sys.exit(1)

    n_shards = 3 if rows_total >= 30 else 2
    base, rem = rows_total // n_shards, rows_total % n_shards
    sizes = [base + (1 if k < rem else 0) for k in range(n_shards)]

    os.makedirs(SHARD_DIR, exist_ok=True)
    for f in os.listdir(SHARD_DIR):
        if f.endswith(".npy"):
            os.remove(os.path.join(SHARD_DIR, f))

    import hashlib as _hl
    written, i = [], 0
    shard_info = []
    for s, rows_s in enumerate(sizes):
        if rows_s <= 0:
            break
        block = stream[i * SEQ_LEN:(i + rows_s) * SEQ_LEN].reshape(rows_s, SEQ_LEN)
        p = os.path.join(SHARD_DIR, "shard_%04d.npy" % s)
        np.save(p, block)
        shard_info.append({
            "file": os.path.basename(p), "rows": int(rows_s),
            "bytes": os.path.getsize(p),
            "md5": _hl.md5(open(p, "rb").read()).hexdigest()})
        written.append(rows_s)
        i += rows_s
    total_rows = sum(written)
    checks["rows_tile_stream"] = (total_rows == rows_total)

    shard_ok = True
    for info in shard_info:
        a_ = np.load(os.path.join(SHARD_DIR, info["file"]), mmap_mode="r")
        if a_.dtype != np.int32 or a_.ndim != 2 or a_.shape[1] != SEQ_LEN:
            shard_ok = False
    checks["shards_int32_seq_len"] = shard_ok
    print("shards: %s" % [(s["file"], s["rows"], s["md5"][:8]) for s in shard_info])
    print("checks: %s" % checks)

    meta = {"stage": "O.3a", "teacher": TEACHER_ID, "pairs": n,
            "stream_tokens": int(stream.size), "rows": int(rows_total),
            "tail_tokens_dropped": int(tail), "n_shards": len(shard_info),
            "held_out_shard": shard_info[-1]["file"] if shard_info else None,
            "shards": shard_info, "checks": checks,
            "pair_tokens_min_med_max": [min(lens),
                                        sorted(lens)[len(lens) // 2],
                                        max(lens)],
            "finished": time.strftime("%Y-%m-%dT%H:%M:%S")}
    with open(META, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=1)

    if not all(checks.values()):
        print("FAILED checks: %s" % {k: v for k, v in checks.items() if not v})
        print("RESULT: O3A_GROUNDED_FAILED checks")
        sys.exit(1)
    print("RESULT: O3A_GROUNDED_OK pairs=%d tokens=%d rows=%d shards=%d"
          % (n, int(stream.size), rows_total, len(shard_info)))


def main():
    ap = argparse.ArgumentParser(description="Stage O.3a grounded QA generation")
    ap.add_argument("--limit-s", type=int, default=LIMIT)
    args = ap.parse_args()
    globals()["LIMIT"] = args.limit_s

    ctx = json.load(open(CTX, encoding="utf-8"))
    chunks = ctx["chunks"]
    print("=" * 74)
    print("STAGE O.3a - GROUNDED QA GENERATION (7B teacher, GPU)")
    print("=" * 74)
    print("context   : %s (%d chunks, %d chars)" % (CTX, len(chunks),
                                                    ctx["chunk_chars"]))
    print("teacher   : %s" % TEACHER)
    print("instruction: %r" % INSTRUCTION)
    print("max_new   : %d  (N.2's 224 truncated 72%% -- fixed)" % MAX_NEW)
    print("output    : %s -> %s" % (OUT_JSONL, SHARD_DIR))

    done, existing = load_done()
    print("resume    : %d chunk ids already in jsonl (%d rows)"
          % (len(done), len(existing)))

    from transformers import AutoModelForCausalLM, AutoTokenizer
    t0 = time.time()
    t_tok = AutoTokenizer.from_pretrained(TEACHER, local_files_only=True)
    # CRITICAL (job 32344): right-padding on a decoder-only model conditions
    # generation on pad tokens -> 44/131 chunks came back unparseable.
    # Left-pad, exactly as Stage N.2 did.
    t_tok.padding_side = "left"
    # no device_map="cuda": accelerate is not installed on PARAM Rudra (same
    # constraint Stage N.2 worked around with a plain .to())
    model = AutoModelForCausalLM.from_pretrained(
        TEACHER, torch_dtype=torch.bfloat16, local_files_only=True)
    model = model.to("cuda")
    print("[teacher] loaded in %.1fs  params=%d"
          % (time.time() - t0, sum(p.numel() for p in model.parameters())))

    stats = {"chunks_done": 0, "tokens_raw": 0, "pairs_kept": 0,
             "pairs_written_this_call": 0, "drop": {}, "seen_q": set()}
    generate(chunks, model, t_tok, done, stats)

    done2, rows = load_done()
    usable = [r for r in rows
              if (r.get("response") or "").strip()
              and (r.get("question") or "").strip()]
    print("-" * 74)
    print("chunks written : %d / %d" % (len(done2), len(chunks)))
    print("pairs kept     : %d (this run), %d usable rows, %d markers"
          % (stats["pairs_kept"], len(usable), len(rows) - len(usable)))
    print("drops          : %s" % (stats["drop"] or "none"))

    if len(done2) < len(chunks):
        print("RESULT: O3A_PARTIAL chunks=%d/%d -- resubmit to resume"
              % (len(done2), len(chunks)))
        return

    del model
    torch.cuda.empty_cache()
    print("\n--- tokenize (16K BPE, Stage K template) ---")
    tokenize_and_shard(usable)


if __name__ == "__main__":
    main()
