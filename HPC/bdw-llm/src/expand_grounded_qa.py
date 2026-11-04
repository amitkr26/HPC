"""Stage O.3a-v4 (expand pass): the teacher writes grounded answers but its
extractive temperament ignores length floors (v2 med=18 words, v3 med=21
words despite a "40 to 90 words" spec). Short training answers made the
student emit one-liners then whitespace-spam in the Stage O.4 A/B.

Deterministic fix: for every pair whose answer is under 40 words, ask the
teacher to REWRITE just the answer to 40-70 words using only the same chunk.
Accept an expansion only if it passes the full grounded gate (length, clean
sentence ending, no refusal/leak/meta-ref) -- otherwise keep the original,
so accuracy can never regress. Then tokenize with the Stage K template.

Resume: results are appended to data/grounded_qa_exp.jsonl keyed by qid, so
a MaxWall kill resumes mid-list; already-long pairs are written without a
teacher call. Final rows are reassembled in source order and handed to
generate_grounded_qa.tokenize_and_shard (all 10 Stage K checks + RESULT).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_grounded_qa import (  # noqa: E402
    CTX, ENDSENT, META_REF_RE, REFUSAL_RE, TEACHER, TEACHER_ID, device_of,
    strip_fluff, tokenize_and_shard,
)

ROOT = os.path.expanduser("~/bdw-llm")
SRC_JSONL = os.path.join(ROOT, "data/grounded_qa.jsonl")
WORK_JSONL = os.path.join(ROOT, "data/grounded_qa_exp.jsonl")

BATCH = 6
MAX_NEW = 200
TEMP, TOP_P = 0.4, 0.9
SEED = 1234
LIMIT = 9 * 60
MIN_WORDS, MAX_WORDS = 40, 150
EXPAND_BELOW = 40

REWRITE = (
    "Text:\n{text}\n\n"
    "Question: {q}\n"
    "Current short answer: {a}\n\n"
    "Rewrite ONLY the answer so it is 40 to 70 words: 3 or 4 complete "
    "sentences that explain the concept fully. Use ONLY facts from the text "
    "above; add no outside information. Keep the question exactly as given. "
    "Output only the rewritten answer, nothing else."
)


def load_jsonl(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def verdict(a):
    w = a.split()
    if len(w) < MIN_WORDS:
        return None, "short"
    if len(w) > MAX_WORDS:
        return None, "too_long"
    if not a.rstrip().endswith(ENDSENT):
        return None, "truncated"
    if REFUSAL_RE.match(a):
        return None, "refusal"
    if "Human:" in a or "Assistant:" in a:
        return None, "leak"
    if META_REF_RE.search(a):
        return None, "meta_ref"
    return a, None


def main():
    src = [r for r in load_jsonl(SRC_JSONL)
           if (r.get("response") or "").strip() and r.get("qid")]
    done = {}
    for r in load_jsonl(WORK_JSONL):
        if r.get("qid"):
            done[r["qid"]] = r
    todo = [r for r in src if r["qid"] not in done]
    n_long = sum(1 for r in todo
                 if len(r["response"].split()) >= EXPAND_BELOW)

    with open(CTX, encoding="utf-8") as fh:
        chunks = {c["id"]: c for c in json.load(fh)["chunks"]}

    print("=" * 74)
    print("STAGE O.3a-v4 -- EXPAND PASS (short grounded answers -> 40-70 w)")
    print("=" * 74)
    print("source     : %s (%d usable pairs)" % (SRC_JSONL, len(src)))
    print("work file  : %s (%d done)" % (WORK_JSONL, len(done)))
    print("todo       : %d  (of which already-long, no gen: %d)"
          % (len(todo), n_long))
    print("expand if  : answer < %d words; accept %d-%d words + clean end"
          % (EXPAND_BELOW, MIN_WORDS, MAX_WORDS))
    if not todo:
        print("RESULT: O3A_EXPAND_NOOP")
        assemble_and_tokenize(src, done)
        return

    t_tok = AutoTokenizer.from_pretrained(TEACHER, local_files_only=True)
    t_tok.padding_side = "left"           # job 32344 lesson
    t0 = time.time()
    model = AutoModelForCausalLM.from_pretrained(
        TEACHER, torch_dtype=torch.bfloat16, local_files_only=True,
        attn_implementation="sdpa").to("cuda")
    print("[teacher] loaded in %.1fs" % (time.time() - t0))

    gen_todo = [r for r in todo if len(r["response"].split()) < EXPAND_BELOW]
    passthru = [r for r in todo if len(r["response"].split()) >= EXPAND_BELOW]
    stats = {"expand_ok": 0, "reject": {}, "passthru": 0, "calls": 0}
    with open(WORK_JSONL, "a", encoding="utf-8") as fh:
        for r in passthru:
            fh.write(json.dumps(dict(r, expanded=False, via="orig_long"),
                                ensure_ascii=False) + "\n")
            done[r["qid"]] = r
            stats["passthru"] += 1
        fh.flush()

        t_start = time.time()
        torch.manual_seed(SEED)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(SEED)
        for i in range(0, len(gen_todo), BATCH):
            if time.time() - t_start > LIMIT:
                print("[wall] %ds elapsed, stopping -- %d pairs left"
                      % (LIMIT, len(gen_todo) - i))
                break
            batch = gen_todo[i:i + BATCH]
            prompts = []
            for r in batch:
                c = chunks.get(r["chunk"], {"text": ""})
                body = REWRITE.format(text=c["text"], q=r["question"],
                                      a=r["response"])
                prompts.append(t_tok.apply_chat_template(
                    [{"role": "user", "content": body}],
                    tokenize=False, add_generation_prompt=True))
            enc = t_tok(prompts, return_tensors="pt", padding=True,
                        truncation=True, max_length=2048).to(device_of(model))
            n_prompt = int(enc["input_ids"].shape[1])
            with torch.no_grad():
                out = model.generate(
                    input_ids=enc["input_ids"],
                    attention_mask=enc["attention_mask"],
                    max_new_tokens=MAX_NEW, do_sample=True,
                    temperature=TEMP, top_p=TOP_P,
                    pad_token_id=t_tok.pad_token_id or t_tok.eos_token_id,
                    eos_token_id=t_tok.eos_token_id)
            stats["calls"] += 1
            for r, ids in zip(batch, out[:, n_prompt:]):
                raw = strip_fluff(" ".join(
                    t_tok.decode(ids, skip_special_tokens=True).split()))
                ok, reason = verdict(raw)
                if ok:
                    rec = dict(r, response=ok, expanded=True, via="expand",
                               orig_words=len(r["response"].split()))
                    stats["expand_ok"] += 1
                else:
                    rec = dict(r, expanded=False, via="expand_rejected",
                               reject=reason)
                    stats["reject"][reason] = \
                        stats["reject"].get(reason, 0) + 1
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                done[r["qid"]] = rec
            fh.flush()
            if stats["calls"] % 5 == 0:
                el = time.time() - t_start
                left = len(gen_todo) - i - len(batch)
                rate = (i + len(batch)) / max(el, 1e-9)
                print("[exp] %d/%d ok=%d rej=%d  %.2f/s  elapsed %ds  eta %ds"
                      % (i + len(batch), len(gen_todo), stats["expand_ok"],
                         sum(stats["reject"].values()), rate, el,
                         left / max(rate, 1e-9)), flush=True)

    missing = [r for r in src if r["qid"] not in done]
    print("-" * 74)
    print("expanded ok : %d / %d attempted" % (stats["expand_ok"], len(gen_todo)))
    print("passthru    : %d (already >= %d words)" % (stats["passthru"], EXPAND_BELOW))
    print("rejected    : %s  (original kept)" % (stats["reject"] or "none"))
    if missing:
        print("RESULT: O3A_EXPAND_PARTIAL missing=%d -- resubmit to resume"
              % len(missing))
        return

    del model
    torch.cuda.empty_cache()
    assemble_and_tokenize(src, done)


def assemble_and_tokenize(src, done):
    final = []
    for r in src:
        rec = done.get(r["qid"])
        if rec is None:
            rec = r
        final.append({"qid": rec["qid"], "chunk": rec["chunk"],
                      "title": rec.get("title", ""), "url": rec.get("url", ""),
                      "requested": rec.get("requested", ""),
                      "question": rec["question"],
                      "response": rec["response"],
                      "expanded": bool(rec.get("expanded")),
                      "teacher": TEACHER_ID})
    outp = os.path.join(ROOT, "data/grounded_qa_final.jsonl")
    with open(outp, "w", encoding="utf-8") as fh:
        for rec in final:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    wc = sorted(len(r["response"].split()) for r in final)
    print("final pairs : %d  -> %s" % (len(final), outp))
    print("answer words min/med/max = %d/%d/%d"
          % (wc[0], wc[len(wc) // 2], wc[-1]))
    print("expanded    : %d" % sum(1 for r in final if r["expanded"]))
    print("\n--- tokenize (16K BPE, Stage K template) ---")
    tokenize_and_shard(final)


if __name__ == "__main__":
    main()
