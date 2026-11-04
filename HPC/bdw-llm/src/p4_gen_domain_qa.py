"""P4.1 - per-domain grounded Q&A generation (GPU, teacher-forced knowledge).

Same discipline as Stage O.3a (generate_grounded_qa.py): the 7B teacher
writes Q&A ONLY from real fetched text and is allowed to invent nothing.

  * context: the domain payload (Stage O.1 schema) resolved by
    p4_domain_lib.ctx_path() -- data/raw/p4_<domain>_contexts.json, with
    vlsi defaulting to the existing data/raw/vlsi_wikipedia.json.
  * chunk selection: round-robin one chunk per page until --max-chunks
    (default 96), so every concept is represented fairly and the slice fits
    the 15-minute MaxWall with teacher-model load time included.
  * max_new_tokens=512 and answers that do not end in terminal punctuation
    are DROPPED (N.2 lesson: a truncated answer must never reach training).
  * the pair gate is the exact Stage O.3a acceptance set (>=4-word question,
    >=5-word complete-sentence answer, no refusal, no Human:/Assistant: leak,
    no meta reference) -- short factual answers are valid teaching rows;
    the 40-90-word wording stays in the INSTRUCTION only, as in O.3a.
  * resume by chunk id: already-written chunk ids (including tombstones for
    chunks that produced no valid pairs) are skipped, so a wall kill loses at
    most the in-flight batch.

Rows write to data/p4/qa/<domain>_qa.jsonl, one row per accepted pair:
    {"qid", "chunk", "title", "url", "requested", "domain", "question",
     "response", "teacher", "decode"}
Tombstone rows (no valid pair from the chunk family) keep the chunk
provenance but carry "valid": false and are consumed only by no-op resume.

RESULT: P4_GEN_<DOMAIN>_COMPLETE chunks=.. qa=..           (all selected done)
RESULT: P4_GEN_<DOMAIN>_SLICE_OK  done=.. left=..           (wall stop, resumable)
RESULT: P4_GEN_<DOMAIN>_FAIL ...                             (exit 1)
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

BATCH = 4
MAX_NEW = 512                 # CRITICAL: O.2's 224 truncated 72% mid-sentence
TEMP, TOP_P = 0.3, 0.9
SEED = 1234
MICRO_CAP = 200               # per-chunk char cap guard for the prompt body

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
LEAK_RE = re.compile(r"\bHuman\s*:|\bAssistant\s*:")
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


def verdict_pair(question, answer):
    """House O.3a pair gate (the exact criteria Stage O.3a kept rows with):
    >=4-word question, >=5-word complete-sentence answer, no refusal, no
    generation leak markers, no meta references. Numbers and short factual
    answers are valid teaching rows. Returns None or the cleaned answer."""
    if not question or not answer:
        return None
    if len(question.split()) < 4:
        return None
    if len(answer.split()) < 5:
        return None
    if answer[-1] not in ENDSENT:
        return None
    if REFUSAL_RE.match(answer) or LEAK_RE.search(answer) \
            or META_REF_RE.search(answer):
        return None
    return answer


def load_done(path):
    done, n_pairs = set(), 0
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                ch = r.get("chunk")
                if ch:
                    done.add(ch)
                if r.get("valid", None) is not False and r.get("question"):
                    n_pairs += 1
    return done, n_pairs


def select_chunks(chunks, max_chunks):
    """Round-robin one chunk per page-buffer (by requested concept) until the
    per-domain cap, keeping deterministic order and full-title coverage."""
    by_page = {}
    for c in chunks:
        by_page.setdefault((c.get("requested") or c["title"]), []).append(c)
    picked = []
    keys = sorted(by_page.keys())
    i = 0
    while len(picked) < max_chunks:
        progressed = False
        for k in keys:
            if i < len(by_page[k]):
                picked.append(by_page[k][i])
                progressed = True
                if len(picked) >= max_chunks:
                    break
        if not progressed:
            break
        i += 1
    return picked


def device_of(model):
    import torch
    return next(model.parameters()).device


def main():
    ap = argparse.ArgumentParser(description="P4.1 domain teacher QA gen")
    ap.add_argument("--domain", required=True,
                    help="math|vlsi|embedded|cs|aiml")
    ap.add_argument("--ctx", default=None, help="context payload override")
    ap.add_argument("--max-chunks", type=int, default=96)
    ap.add_argument("--wall-s", type=int, default=11 * 60)
    ap.add_argument("--batch", type=int, default=BATCH)
    args = ap.parse_args()
    try:
        domain = P4.check(args.domain)
    except ValueError as e:
        print("RESULT: P4_GEN_FAIL %s" % e)
        return 2
    dom = domain.upper()
    ctx_path = args.ctx or P4.ctx_path(domain)
    out_path = P4.qa_path(domain)

    if not os.path.isfile(ctx_path):
        print("RESULT: P4_GEN_%s_FAIL missing context payload %s"
              % (dom, ctx_path))
        return 1
    payload = json.load(open(ctx_path, encoding="utf-8"))
    chunks_all = payload.get("chunks") or []
    if not chunks_all:
        print("RESULT: P4_GEN_%s_FAIL empty chunk list in %s" % (dom, ctx_path))
        return 1
    chunks = select_chunks(chunks_all, max(1, args.max_chunks))

    print("=" * 74)
    print("P4.1 - teacher QA generation for domain %s" % domain)
    print("=" * 74)
    print("context   : %s (%d chunks on disk, %d selected)"
          % (os.path.basename(ctx_path), len(chunks_all), len(chunks)))
    print("out       : %s" % out_path)
    print("teacher   : %s" % P4.teacher_dir())

    import torch
    import transformers

    tok = transformers.AutoTokenizer.from_pretrained(
        P4.teacher_dir(), local_files_only=True)
    model = transformers.AutoModelForCausalLM.from_pretrained(
        P4.teacher_dir(), torch_dtype=torch.bfloat16,
        local_files_only=True).to("cuda" if torch.cuda.is_available() else "cpu")
    model.eval()
    device = device_of(model)

    done, n_pairs = load_done(out_path)
    todo = [c for c in chunks if c["id"] not in done]
    print("resume    : done=%d pairs=%d todo=%d (selected %d)"
          % (len(done), n_pairs, len(todo), len(chunks)))
    print("decode    : batch=%d temp=%.2f top_p=%.2f max_new=%d"
          % (args.batch, TEMP, TOP_P, MAX_NEW))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    stats = {"kept": 0, "no_parse": 0, "wall_stop": False}
    t_start = time.time()
    torch.manual_seed(SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(SEED)

    with open(out_path, "a", encoding="utf-8") as fh:
        for bi in range(0, len(todo), args.batch):
            if time.time() - t_start > args.wall_s:
                stats["wall_stop"] = True
                print("[wall] %ds elapsed, stopping -- %d chunks left"
                      % (args.wall_s, len(todo) - bi), flush=True)
                break
            batch = todo[bi:bi + args.batch]
            prompts = []
            for c in batch:
                body = "%s\n\n%s\n\nText:\n%s" % (INSTRUCTION, FORMAT_SPEC,
                                                  c["text"])
                prompts.append(tok.apply_chat_template(
                    [{"role": "user", "content": body}],
                    tokenize=False, add_generation_prompt=True))
            enc = tok(prompts, return_tensors="pt", padding=True,
                      truncation=True, max_length=2048).to(device)
            n_prompt = int(enc["input_ids"].shape[1])
            with torch.no_grad():
                out = model.generate(
                    input_ids=enc["input_ids"],
                    attention_mask=enc["attention_mask"],
                    max_new_tokens=MAX_NEW, do_sample=True,
                    temperature=TEMP, top_p=TOP_P,
                    pad_token_id=tok.pad_token_id or tok.eos_token_id)
            dec = tok.batch_decode(
                out[:, n_prompt:], skip_special_tokens=True)

            # figure out which texts produced at least one valid pair so a
            # chunk family with zero output gets a tombstone (no-op resume)
            for c, raw in zip(batch, dec):
                pairs = parse_pairs(raw)
                if not pairs:
                    stats["no_parse"] += 1
                good = 0
                for q, a in pairs:
                    reason = None
                    if not q or not a:
                        reason = "empty"
                    elif len(q.split()) < 4:
                        reason = "short_q"
                    else:
                        answer = verdict_pair(q, a)
                        if answer is None:
                            if len(a.split()) < 5:
                                reason = "short_a"
                            elif a[-1] not in ENDSENT:
                                reason = "truncated"
                            elif REFUSAL_RE.match(a):
                                reason = "refusal"
                            elif LEAK_RE.search(a):
                                reason = "leak"
                            else:
                                reason = "meta_ref"
                    if reason:
                        stats["drop_" + reason] = \
                            stats.get("drop_" + reason, 0) + 1
                        continue
                    if answer is None:
                        continue
                    answer = " ".join(answer.split())
                    stats["kept"] += 1
                    good += 1
                    row = {
                        "qid": hashlib.md5((q + "\x00" + answer)
                                           .encode("utf-8")).hexdigest()[:16],
                        "chunk": c["id"],
                        "title": c["title"],
                        "url": c["url"],
                        "requested": c.get("requested") or c["title"],
                        "domain": domain,
                        "question": q,
                        "response": answer,
                        "teacher": "teacher_model_7b (Qwen2.5-7B-Instruct)",
                        "decode": {"chat_template": True,
                                   "temperature": TEMP, "top_p": TOP_P,
                                   "max_new_tokens": MAX_NEW, "seed": SEED},
                    }
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                if good == 0:
                    fh.write(json.dumps({
                        "qid": "tomb_" + c["id"], "chunk": c["id"],
                        "title": c["title"], "url": c["url"],
                        "requested": c.get("requested") or c["title"],
                        "domain": domain, "valid": False,
                        "reason": "no_usable_pairs",
                    }, ensure_ascii=False) + "\n")
            fh.flush()
            if bi % (args.batch * 6) == 0:
                print("[gen] %d/%d chunks kept=%d (%.0fs)"
                      % (bi + len(batch), len(todo), stats["kept"],
                         time.time() - t_start), flush=True)

    # ---- summary -------------------------------------------------------
    done_now, pairs_now = load_done(out_path)
    selected_ids = {c["id"] for c in chunks}
    remaining = len(selected_ids - done_now)
    complete = remaining == 0 and todo
    elapsed = time.time() - t_start
    print("-" * 74)
    print("chunks     : selected=%d done=%d remaining=%d"
          % (len(chunks), len(selected_ids & done_now), remaining))
    print("qa written : kept=%d drops=%s" % (stats["kept"], ", ".join(
        "%s=%d" % (k[5:], v) for k, v in sorted(stats.items())
        if k.startswith("drop_")) or "none"))
    print("file       : %s (%d bytes, %.0fs)"
          % (out_path, os.path.getsize(out_path) if os.path.exists(out_path)
             else -1, elapsed))
    if stats["wall_stop"] and not complete:
        print("RESULT: P4_GEN_%s_SLICE_OK done=%d left=%d "
              "(resubmit to resume)"
              % (dom, len(selected_ids & done_now), remaining))
        return 0
    if complete:
        print("RESULT: P4_GEN_%s_COMPLETE chunks=%d qa=%d"
              % (dom, len(chunks), pairs_now))
        return 0
    print("RESULT: P4_GEN_%s_FAIL no progress (%.0fs)"
          % (dom, elapsed))
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        print("RESULT: P4_GEN_FAIL %s" % sys.exc_info()[1])
        sys.exit(1)
