"""Stage N.3a: format and tokenise the 7B teacher's answers with our 16K BPE.

Input : data/distilled_teacher_data_v2.jsonl (Qwen2.5-7B-Instruct, Stage N.4)
Output: data/distilled_tokens/{stream.npy, shards/shard_*.npy, distill_meta.json}

The conversational layout and the id construction are byte-for-byte the Stage K
recipe from docs/INSTRUCTION_DATA.md sec.3, so Stage L's loader and Stage M's
prompt builder keep working unchanged:

    ids = [bos] + encode("User: " + q).ids + [eos, bos]
          + encode("Assistant: " + a).ids + [eos]

Filters (only genuine defects -- a 3-word extractive answer is a CORRECT
answer, not a truncated one):
    * refusal / apology prefixes from the teacher
    * "Human:" or "Assistant:" transcript leaks
    * empty responses

Sequence-level distillation note: the student never sees the teacher's
vocabulary. Only the TEXT crosses over, re-encoded with our own 16,384-token
byte-level BPE -- which is exactly why logit/KL distillation was not an option.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time

ROOT = os.path.expanduser("~/bdw-llm")
IN_JSONL = os.path.join(ROOT, "data/distilled_teacher_data_v2.jsonl")
OUT_DIR = os.path.join(ROOT, "data/distilled_tokens")
STREAM = os.path.join(OUT_DIR, "stream.npy")
SHARD_DIR = os.path.join(OUT_DIR, "shards")
META = os.path.join(OUT_DIR, "distill_meta.json")
TOKENIZER = os.path.join(ROOT, "tokenizer/tokenizer.json")

SEQ_LEN = 1024
REFUSAL = ("as an ai", "i'm sorry", "i am sorry", "i cannot", "i can't",
           "i do not have personal")
LEAK = re.compile(r"\b(Human|Assistant)\s*:")
MIN_WORDS = 2
N_TEMPLATE_CHECKS = 6


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_ids(tok, q, a):
    """Stage K recipe -- programmatic build (verified against the literal
    template below, so training and inference cannot drift)."""
    return ([tok.token_to_id("<|bos|>")]
            + tok.encode("User: " + q).ids
            + [tok.token_to_id("<|eos|>"), tok.token_to_id("<|bos|>")]
            + tok.encode("Assistant: " + a).ids
            + [tok.token_to_id("<|eos|>")])


def main():
    print("=" * 76)
    print("STAGE N.3a - FORMAT + TOKENISE 7B TEACHER DATA (Stage K recipe)")
    print("=" * 76)
    print("in      :", IN_JSONL)
    print("out     :", OUT_DIR)
    print("tokenizer:", TOKENIZER)
    print("host    :", os.uname().nodename)
    print("started :", time.strftime("%Y-%m-%dT%H:%M:%S"))

    if not os.path.exists(IN_JSONL):
        raise SystemExit("missing %s -- run Step N.2 first" % IN_JSONL)

    from tokenizers import Tokenizer

    tok = Tokenizer.from_file(TOKENIZER)
    vocab = tok.get_vocab_size()
    bos, eos, pad = (tok.token_to_id(t) for t in ("<|bos|>", "<|eos|>", "<|pad|>"))
    print("\nvocab      : %d   special ids: pad=%d bos=%d eos=%d" % (vocab, pad, bos, eos))
    probe = tok.encode("hello world").ids
    print("encode probe: %s  (no post-processor expected)" % probe)
    if len(probe) != 3:
        print("[warn] encode('hello world') = %d ids, Stage K recorded 3" % len(probe))

    # ------------------------------------------------ load + filter
    rows, dropped = [], []
    with open(IN_JSONL, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            try:
                r = json.loads(line)
            except Exception as e:
                dropped.append({"line": lineno, "reason": "corrupt json: %s" % e})
                continue
            q = (r.get("question") or "").strip()
            a = (r.get("response") or "").strip()
            if not q or not a:
                dropped.append({"line": lineno, "id": r.get("id"),
                                "reason": "empty question/response"})
                continue
            low = a.lower()
            if low.startswith(REFUSAL):
                dropped.append({"line": lineno, "id": r.get("id"),
                                "reason": "refusal/apology prefix"})
                continue
            if LEAK.search(a):
                dropped.append({"line": lineno, "id": r.get("id"),
                                "reason": "Human:/Assistant: transcript leak"})
                continue
            if len(a.split()) < MIN_WORDS:
                dropped.append({"line": lineno, "id": r.get("id"),
                                "reason": "shorter than %d words" % MIN_WORDS})
                continue
            rows.append({"q": q, "a": a, "id": r.get("id"),
                         "category": r.get("category"), "source": r.get("source")})

    src_n = sum(1 for _ in open(IN_JSONL, encoding="utf-8"))
    print("\ninput rows : %d" % src_n)
    print("kept       : %d" % len(rows))
    print("dropped    : %d" % len(dropped))
    by_reason = {}
    for d in dropped:
        by_reason[d["reason"]] = by_reason.get(d["reason"], 0) + 1
    for k, v in sorted(by_reason.items(), key=lambda kv: -kv[1]):
        print("   %-42s %d" % (k, v))
    if not rows:
        raise SystemExit("nothing survived the filter")

    # ------------------------------------------------ tokenise
    t0 = time.time()
    streams, lens = [], []
    for r in rows:
        ids = build_ids(tok, r["q"], r["a"])
        streams.extend(ids)
        lens.append(len(ids))
    enc_t = time.time() - t0
    n_ex = len(rows)
    bos_count = sum(1 for i in streams if i == bos)
    eos_count = sum(1 for i in streams if i == eos)
    mn, mx = min(streams), max(streams)
    print("\nexamples    : %d" % n_ex)
    print("tokens      : %d  (%.2f per example)   encode %.1fs (%d tok/s)"
          % (len(streams), len(streams) / n_ex, enc_t, len(streams) / max(enc_t, 1e-9)))
    print("id range    : min=%d max=%d (vocab=%d)" % (mn, mx, vocab))
    print("bos count   : %d  (expected %d)  -> %s"
          % (bos_count, 2 * n_ex, bos_count == 2 * n_ex))
    print("eos count   : %d  (expected %d)  -> %s"
          % (eos_count, 2 * n_ex, eos_count == 2 * n_ex))

    # --------------------------------------- verification (Stage K checks)
    checks = {}
    checks["id_range_in_vocab"] = (mn >= 0 and mx < vocab)
    checks["no_pad_leak"] = (mn >= 1)          # <|pad|> == 0 must not appear
    checks["bos_exact"] = (bos_count == 2 * n_ex)
    checks["eos_exact"] = (eos_count == 2 * n_ex)

    # literal template == programmatic build
    lit_ok = 0
    for r in rows[:N_TEMPLATE_CHECKS]:
        literal = ("<|bos|>User: %s<|eos|><|bos|>Assistant: %s<|eos|>"
                   % (r["q"], r["a"]))
        if tok.encode(literal).ids == build_ids(tok, r["q"], r["a"]):
            lit_ok += 1
    checks["literal_template_matches_build"] = (lit_ok == N_TEMPLATE_CHECKS)
    print("\ntemplate-vs-build match : %d / %d" % (lit_ok, N_TEMPLATE_CHECKS))

    # every example begins with bos and ends with eos (rebuild per example)
    beg = end = 0
    pos = 0
    for r in rows:
        n = len(build_ids(tok, r["q"], r["a"]))
        chunk = streams[pos:pos + n]
        pos += n
        if chunk[0] == bos:
            beg += 1
        if chunk[-1] == eos:
            end += 1
    checks["all_start_bos"] = (beg == n_ex)
    checks["all_end_eos"] = (end == n_ex)
    print("examples starting with bos : %d / %d" % (beg, n_ex))
    print("examples ending with eos   : %d / %d" % (end, n_ex))

    # decode -> encode round-trip on a sample.
    # MUST be skip_special_tokens=False (as Stage K did): the specials live in
    # the vocab, so keeping them is what makes the round-trip meaningful.
    rt_ok = 0
    for r in rows[:N_TEMPLATE_CHECKS]:
        text = tok.decode(build_ids(tok, r["q"], r["a"]),
                          skip_special_tokens=False)
        re_ids = tok.encode(text).ids
        if re_ids == build_ids(tok, r["q"], r["a"]):
            rt_ok += 1
    checks["decode_encode_roundtrip"] = (rt_ok == N_TEMPLATE_CHECKS)
    print("decode->encode round-trip : %d / %d  (specials kept)"
          % (rt_ok, N_TEMPLATE_CHECKS))

    if not all(checks.values()):
        print("\nFAILED checks: %s" % {k: v for k, v in checks.items() if not v})
        print("RESULT: N3A_TOKENIZE_FAILED")
        sys.exit(1)

    # ------------------------------------------------ shard
    import numpy as np

    arr = np.asarray(streams, dtype=np.int32)
    os.makedirs(OUT_DIR, exist_ok=True)
    np.save(STREAM, arr)

    rows_total = arr.shape[0] // SEQ_LEN
    tail = arr.shape[0] % SEQ_LEN
    if rows_total < 4:
        raise SystemExit("only %d rows of %d -- too small to shard"
                         % (rows_total, SEQ_LEN))
    # >=2 shards are mandatory: finetune.py holds the LAST N out for validation,
    # and one shard would leave zero training shards. Sizes are balanced so the
    # held-out tail is a reasonable fraction rather than most of the dataset.
    n_shards = 3 if rows_total >= 90 else 2
    base = rows_total // n_shards
    rem = rows_total % n_shards
    shard_sizes = [base + (1 if k < rem else 0) for k in range(n_shards)]

    os.makedirs(SHARD_DIR, exist_ok=True)
    for f in os.listdir(SHARD_DIR):
        if f.endswith(".npy"):
            os.remove(os.path.join(SHARD_DIR, f))

    written, shard_files = [], []
    i = 0
    for s, rows_s in enumerate(shard_sizes):
        if rows_s <= 0:
            break
        block = arr[i * SEQ_LEN:(i + rows_s) * SEQ_LEN].reshape(rows_s, SEQ_LEN)
        p = os.path.join(SHARD_DIR, "shard_%04d.npy" % s)
        np.save(p, block)
        shard_files.append(p)
        written.append(rows_s)
        i += rows_s

    print("\nseq_len     : %d" % SEQ_LEN)
    print("rows        : %d  (tail %d tokens dropped)" % (rows_total, tail))
    print("shards      : %d" % len(shard_files))
    total_rows = 0
    for p, n in zip(shard_files, written):
        a_ = np.load(p, mmap_mode="r")
        total_rows += int(a_.shape[0])
        print("   %-16s %-14s %d bytes   dtype=%s"
              % (os.path.basename(p), str(a_.shape), os.path.getsize(p), a_.dtype))
    print("row total   : %d vs %d -> %s"
          % (total_rows, rows_total, total_rows == rows_total))

    # Stage K also asserted dtype/shape/tiling on the written shards
    shard_ok, bad_shards = True, []
    for p in shard_files:
        a_ = np.load(p, mmap_mode="r")
        if a_.dtype != np.int32 or a_.ndim != 2 or a_.shape[1] != SEQ_LEN:
            shard_ok = False
            bad_shards.append("%s dtype=%s shape=%s" % (os.path.basename(p),
                                                        a_.dtype, a_.shape))
    checks["shards_int32_seq_len"] = shard_ok
    checks["rows_tile_stream"] = (total_rows == rows_total)
    print("shard dtype/shape ok : %s %s" % (shard_ok, bad_shards or ""))

    if not all(checks.values()):
        print("\nFAILED checks: %s" % {k: v for k, v in checks.items() if not v})
        print("RESULT: N3A_TOKENIZE_FAILED")
        sys.exit(1)

    cats, srcs = {}, {}
    for r in rows:
        cats[r["category"]] = cats.get(r["category"], 0) + 1
        srcs[r["source"]] = srcs.get(r["source"], 0) + 1
    print("by source   : %s" % srcs)

    meta = {
        "stage": "N.3a",
        "input_jsonl": IN_JSONL,
        "input_md5": md5(IN_JSONL),
        "input_rows": src_n,
        "kept_rows": n_ex,
        "dropped_rows": len(dropped),
        "dropped_by_reason": by_reason,
        "dropped_detail": dropped[:40],
        "teacher": "Qwen/Qwen2.5-7B-Instruct",
        "format": "<|bos|>User: {q}<|eos|><|bos|>Assistant: {a}<|eos|>",
        "seq_len": SEQ_LEN,
        "tokens": int(arr.shape[0]),
        "tokens_per_example": round(len(streams) / n_ex, 2),
        "rows": rows_total,
        "tail_tokens_dropped": tail,
        "shards": [{"file": os.path.basename(p), "rows": int(n),
                    "bytes": os.path.getsize(p),
                    "md5": md5(p)}
                   for p, n in zip(shard_files, written)],
        "held_out_shard": os.path.basename(shard_files[-1]),
        "by_source": srcs,
        "by_category": cats,
        "checks": checks,
        "tokenizer": TOKENIZER,
        "vocab_size": vocab,
        "stream_md5": md5(STREAM),
        "finished": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    with open(META, "w") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)

    print("\nheld-out shard for validation: %s" % meta["held_out_shard"])
    print("meta -> %s" % META)
    print()
    print("RESULT: N3A_TOKENIZE_OK examples=%d tokens=%d shards=%d"
          % (n_ex, int(arr.shape[0]), len(shard_files)))


if __name__ == "__main__":
    main()
