"""Stage K: build the instruction-tuning dataset (synthetic/curated Q&A).

Runs on the LOGIN node because it is the only machine with DNS. It pulls
databricks-dolly-15k through the datasets-server rows API (the same bounded,
resume-capable route used for the Stage C pilot corpus), then formats every
record with the Stage D tokenizer into the conversational layout

    <|bos|>User: [Question]<|eos|><|bos|>Assistant: [Answer]<|eos|>

and writes one contiguous int32 stream plus fixed-length shards, matching
the Stage E training format so Stage L can reuse the same data path.

When a dolly record carries a `context` field it is appended to the user
turn under a "Context:" label -- closed_qa and summarization rows are
unanswerable without it. The raw fields are kept in data/raw/dolly15k.jsonl
so the formatting stays auditable and can be re-run without re-downloading.
"""
import json
import os
import sys
import time
import urllib.request

import numpy as np
from tokenizers import Tokenizer

ROOT = os.path.expanduser("~/bdw-llm")
RAW = os.path.join(ROOT, "data/raw/dolly15k.jsonl")
PROG = RAW + ".progress.json"
TOK = os.path.join(ROOT, "tokenizer/tokenizer.json")
OUTDIR = os.path.join(ROOT, "data/instruct_tokens")

DS, CFG, SPL = "databricks/databricks-dolly-15k", "default", "train"
PAGE = 100
SLEEP = 0.9          # be polite to the shared Hub endpoint
SEQ_LEN = 1024
SHARD_TOKENS = 1_000_000
MIN_INSTR = 5        # ignore degenerate prompts
MIN_RESP = 1         # ignore empty answers
MAX_CONTEXT_CHARS = 6000   # stop one long passage from dominating a row

FMT = "<|bos|>User: {q}<|eos|><|bos|>Assistant: {a}<|eos|>"


# ---------------------------------------------------------------- formatting
def build_user(instruction, context=""):
    ins = " ".join((instruction or "").split())
    ctx = " ".join((context or "").split())
    if not ctx:
        return ins
    if len(ctx) > MAX_CONTEXT_CHARS:
        ctx = ctx[:MAX_CONTEXT_CHARS].rstrip() + " ..."
    return "%s\n\nContext:\n%s" % (ins, ctx)


def format_example(instruction, response, context=""):
    """Return (text, question, answer) for the conversational record."""
    q = build_user(instruction, context)
    a = " ".join((response or "").split())
    return FMT.format(q=q, a=a), q, a


def encode_example(tok, bos, eos, instruction, response, context=""):
    """Build token ids programmatically so the layout cannot drift."""
    text, q, a = format_example(instruction, response, context)
    ids = ([bos]
           + tok.encode("User: " + q, add_special_tokens=False).ids
           + [eos]
           + [bos]
           + tok.encode("Assistant: " + a, add_special_tokens=False).ids
           + [eos])
    return ids, text, q, a


# ------------------------------------------------------------------ download
def load_prog():
    if os.path.exists(PROG):
        p = json.load(open(PROG))
        return p.get("offset", 0), p.get("kept", 0)
    return 0, 0


def save_prog(offset, kept):
    with open(PROG, "w") as fh:
        json.dump({"offset": offset, "kept": kept}, fh)


def fetch(offset, tries=10):
    url = ("https://datasets-server.huggingface.co/rows"
           "?dataset=%s&config=%s&split=%s&offset=%d&length=%d"
           % (DS, CFG, SPL, offset, PAGE))
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "bdw-stageK/1.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            last = e
            code = getattr(e, "code", None)
            base = 8 if code in (429, 503, 502) else 3
            wait = min(base * (2 ** i), 90)
            print("    retry %d/%d offset=%d code=%s sleep=%ds"
                  % (i + 1, tries, offset, code, wait))
            sys.stdout.flush()
            time.sleep(wait)
    raise RuntimeError("offset %d failed after %d tries: %r" % (offset, tries, last))


def download():
    os.makedirs(os.path.dirname(RAW), exist_ok=True)
    offset, kept = load_prog()
    mode = "a" if offset > 0 and os.path.exists(RAW) else "w"
    if mode == "w":
        offset, kept = 0, 0
    t0 = time.time()
    total = 0
    print("download: %s/%s/%s  resuming at offset=%d kept=%d mode=%s"
          % (DS, CFG, SPL, offset, kept, mode))
    sys.stdout.flush()
    with open(RAW, mode, encoding="utf-8") as fh:
        while True:
            data = fetch(offset)
            rows = data.get("rows") or []
            if not rows:
                print("no more rows at offset %d (reached end)" % offset)
                break
            for r in rows:
                rec = r.get("row") or {}
                keep = {
                    "instruction": rec.get("instruction") or "",
                    "response": rec.get("response") or "",
                    "context": rec.get("context") or "",
                    "category": rec.get("category") or "",
                }
                rec_bytes = json.dumps(keep, ensure_ascii=False) + "\n"
                fh.write(rec_bytes)
                total += len(rec_bytes.encode("utf-8"))
                kept += 1
            fh.flush()
            offset += len(rows)
            save_prog(offset, kept)
            time.sleep(SLEEP)
            if (offset // PAGE) % 25 == 0:
                print("  offset=%-6d kept=%-6d %.1f MB (%.0fs)"
                      % (offset, kept, total / 1e6, time.time() - t0))
                sys.stdout.flush()
    print("download DONE: kept=%d bytes=%d (%.1f MB) elapsed=%.1fs"
          % (kept, total, total / 1e6, time.time() - t0))
    return kept


# --------------------------------------------------------------- tokenisation
def tokenise_and_shard():
    tok = Tokenizer.from_file(TOK)
    bos = tok.token_to_id("<|bos|>")
    eos = tok.token_to_id("<|eos|>")
    pad = tok.token_to_id("<|pad|>")
    vs = tok.get_vocab_size()
    print("\ntokenizer   :", TOK)
    print("vocab_size  :", vs)
    print("special ids : pad=%d bos=%d eos=%d" % (pad, bos, eos))

    # probe: does encode() add anything of its own?
    probe = tok.encode("hello world")
    print("encode probe: ids=%s  (no post-processor expected)" % probe.ids)

    chunks = []
    n_ex = n_skip = n_ctx = n_long = 0
    cat_counts = {}
    example_log = []
    t0 = time.time()
    with open(RAW, encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            ins, resp, ctx = rec.get("instruction"), rec.get("response"), rec.get("context")
            if not ins or not resp:
                n_skip += 1
                continue
            if len(" ".join(ins.split())) < MIN_INSTR:
                n_skip += 1
                continue
            if len(" ".join(resp.split())) < MIN_RESP:
                n_skip += 1
                continue
            ids, text, q, a = encode_example(tok, bos, eos, ins, resp, ctx)
            if len(ids) > SEQ_LEN:
                n_long += 1
            if ctx.strip():
                n_ctx += 1
            cat = rec.get("category") or "?"
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
            chunks.append(np.asarray(ids, dtype=np.int32))
            n_ex += 1
            if len(example_log) < 4:
                example_log.append({"category": cat, "ids": ids, "text": text,
                                    "question": q, "answer": a})

    stream = np.concatenate(chunks) if chunks else np.zeros(0, dtype=np.int32)
    del chunks
    enc_t = time.time() - t0
    print("\nexamples    : %d (skipped %d, with context %d, longer than %d ids %d)"
          % (n_ex, n_skip, n_ctx, SEQ_LEN, n_long))
    print("tokens      : %d  (%.2f per example)" % (stream.size, stream.size / max(n_ex, 1)))
    print("encode_time : %.1fs (%.0f tokens/s)"
          % (enc_t, stream.size / max(enc_t, 1e-9)))
    print("id range    : min=%d max=%d (vocab=%d)" % (stream.min(), stream.max(), vs))
    print("categories  :", json.dumps(cat_counts, sort_keys=True))
    if stream.max() >= vs or stream.min() < 0:
        raise SystemExit("token id out of range")

    os.makedirs(OUTDIR, exist_ok=True)
    stream_path = os.path.join(OUTDIR, "stream.npy")
    np.save(stream_path, stream)
    print("saved       :", stream_path, os.path.getsize(stream_path), "bytes")

    n_rows = stream.size // SEQ_LEN
    rows = stream[: n_rows * SEQ_LEN].reshape(n_rows, SEQ_LEN)
    shard_dir = os.path.join(OUTDIR, "shards")
    os.makedirs(shard_dir, exist_ok=True)
    rows_per_shard = max(1, SHARD_TOKENS // SEQ_LEN)
    n_shards = (n_rows + rows_per_shard - 1) // rows_per_shard
    shard_sizes = []
    for i in range(n_shards):
        part = rows[i * rows_per_shard: (i + 1) * rows_per_shard]
        p = os.path.join(shard_dir, "shard_%04d.npy" % i)
        np.save(p, part)
        shard_sizes.append((os.path.basename(p), part.shape, os.path.getsize(p)))
    print("\nseq_len     : %d" % SEQ_LEN)
    print("rows        : %d  (tail %d tokens dropped)"
          % (n_rows, stream.size - n_rows * SEQ_LEN))
    print("shards      : %d" % n_shards)
    for name, shape, sz in shard_sizes:
        print("   %-16s %-14s %d bytes" % (name, str(shape), sz))
    return (tok, bos, eos, pad, vs, stream, rows, n_shards, n_ex, n_skip,
            n_ctx, n_long, cat_counts, example_log, shard_dir, shard_sizes)


# --------------------------------------------------------------- verification
def verify(ctx):
    (tok, bos, eos, pad, vs, stream, rows, n_shards, n_ex, n_skip,
     n_ctx, n_long, cat_counts, example_log, shard_dir, shard_sizes) = ctx

    print("\n--- verification ---")
    failures = []

    # 1. the literal template and the programmatic build must agree
    for ex in example_log:
        lit = ex["text"]
        prog_ids = ([bos]
                    + tok.encode("User: " + ex["question"], add_special_tokens=False).ids
                    + [eos, bos]
                    + tok.encode("Assistant: " + ex["answer"], add_special_tokens=False).ids
                    + [eos])
        same = prog_ids == ex["ids"]
        lit_ids = tok.encode(lit, add_special_tokens=False).ids
        print("  template-vs-build match : %s   (literal-encode match: %s)"
              % (same, lit_ids == ex["ids"]))
        if not same or lit_ids != ex["ids"]:
            failures.append("template/build mismatch")

    # 2. bos/eos counts must be exactly 2 per example
    n_bos = int(np.count_nonzero(stream == bos))
    n_eos = int(np.count_nonzero(stream == eos))
    print("  bos count = %d (expected %d)  -> %s"
          % (n_bos, 2 * n_ex, n_bos == 2 * n_ex))
    print("  eos count = %d (expected %d)  -> %s"
          % (n_eos, 2 * n_ex, n_eos == 2 * n_ex))
    if n_bos != 2 * n_ex or n_eos != 2 * n_ex:
        failures.append("special-token counts wrong")

    # 3. every example must start with bos and end with eos
    starts = ends = 0
    pos = 0
    with open(RAW, encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            if (not rec.get("instruction")) or (not rec.get("response")):
                continue
            if len(" ".join(rec["instruction"].split())) < MIN_INSTR:
                continue
            ids, _, _, _ = encode_example(
                tok, bos, eos, rec["instruction"], rec["response"], rec.get("context"))
            if pos < stream.size and stream[pos] == bos:
                starts += 1
            if pos + len(ids) - 1 < stream.size and stream[pos + len(ids) - 1] == eos:
                ends += 1
            pos += len(ids)
    print("  examples starting with bos : %d / %d  -> %s"
          % (starts, n_ex, starts == n_ex))
    print("  examples ending with eos   : %d / %d  -> %s"
          % (ends, n_ex, ends == n_ex))
    if starts != n_ex or ends != n_ex:
        failures.append("example boundary alignment wrong")

    # 4. shards must be int32, (n, 1024), and tile the stream exactly
    total_rows = 0
    for name, shape, _sz in shard_sizes:
        arr = np.load(os.path.join(shard_dir, name))
        if arr.dtype != np.int32:
            failures.append("%s dtype %s" % (name, arr.dtype))
        if arr.ndim != 2 or arr.shape[1] != SEQ_LEN:
            failures.append("%s shape %s" % (name, str(arr.shape)))
        total_rows += arr.shape[0]
    print("  shard dtypes/shapes ok    : %s   (rows %d vs %d)"
          % (not any("shard" in f for f in failures), total_rows, rows.shape[0]))
    if total_rows != rows.shape[0]:
        failures.append("shard row count mismatch")

    # 5. decode a full example back and show it
    ex = example_log[0]
    dec = tok.decode(ex["ids"], skip_special_tokens=False)
    print("\n  sample category : %s" % ex["category"])
    print("  sample ids      : %s ... %s" % (ex["ids"][:6], ex["ids"][-4:]))
    print("  decoded text    :\n%s" % "\n".join("    " + l for l in dec.splitlines()))
    rt = (tok.encode(dec, add_special_tokens=False).ids == ex["ids"])
    print("  decode->encode round-trip : %s" % rt)
    if not rt:
        failures.append("round-trip failed")

    # 6. held-out shard note for Stage L
    held_out = [os.path.basename(p) for p, _s, _z in shard_sizes[-1:]] if shard_sizes else []
    print("  held-out shard for Stage L: %s" % held_out)

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print("  -", f)
        raise SystemExit("VERIFY_FAILED")
    print("\nall checks passed")
    return held_out


def preflight():
    """Format/encode a handful of live rows and exit -- no download, no files."""
    tok = Tokenizer.from_file(TOK)
    bos = tok.token_to_id("<|bos|>")
    eos = tok.token_to_id("<|eos|>")
    pad = tok.token_to_id("<|pad|>")
    vs = tok.get_vocab_size()
    print("vocab=%d pad=%d bos=%d eos=%d" % (vs, pad, bos, eos))
    print("encode('hello world') ->", tok.encode("hello world", add_special_tokens=False).ids)
    data = fetch(0)
    rows = [r.get("row") or {} for r in (data.get("rows") or [])[:3]]
    print("fetched %d live rows, fields=%s" % (len(rows), sorted(rows[0].keys()) if rows else []))
    bad = 0
    for i, rec in enumerate(rows):
        ids, text, q, a = encode_example(tok, bos, eos, rec.get("instruction"),
                                         rec.get("response"), rec.get("context"))
        dec = tok.decode(ids, skip_special_tokens=False)
        lit = tok.encode(text, add_special_tokens=False).ids
        rt = tok.encode(dec, add_special_tokens=False).ids == ids
        ok = (ids[0] == bos and ids[-1] == eos and lit == ids and rt
              and ids.count(bos) == 2 and ids.count(eos) == 2)
        if not ok:
            bad += 1
        print("\n[%d] category=%s len=%d ok=%s (template==build:%s roundtrip:%s)"
              % (i, rec.get("category"), len(ids), ok, lit == ids, rt))
        print("    decoded:\n%s" % "\n".join("      " + l for l in dec.splitlines()))
    print("\nPREFLIGHT_%s" % ("FAILED" if bad else "OK"))
    if bad:
        raise SystemExit("preflight failed for %d rows" % bad)


def main():
    print("=== Stage K: instruction data (dolly-15k) ===")
    if "--preflight" in sys.argv:
        preflight()
        return
    download()
    ctx = tokenise_and_shard()
    held_out = verify(ctx)
    (tok, bos, eos, pad, vs, stream, rows, n_shards, n_ex, n_skip,
     n_ctx, n_long, cat_counts, example_log, shard_dir, shard_sizes) = ctx

    meta = {
        "stage": "K",
        "dataset": "%s/%s/%s" % (DS, CFG, SPL),
        "dataset_rows_total": 15011,
        "raw_jsonl": RAW,
        "tokenizer": TOK,
        "vocab_size": vs,
        "format": FMT,
        "special_ids": {"pad": pad, "bos": bos, "eos": eos},
        "examples": n_ex,
        "skipped": n_skip,
        "examples_with_context": n_ctx,
        "examples_longer_than_seq": n_long,
        "tokens": int(stream.size),
        "tokens_per_example": round(stream.size / max(n_ex, 1), 2),
        "seq_len": SEQ_LEN,
        "rows": int(rows.shape[0]),
        "shards": n_shards,
        "dtype": "int32",
        "held_out_shards": held_out,
        "category_counts": cat_counts,
    }
    meta_path = os.path.join(OUTDIR, "instruct_meta.json")
    with open(meta_path, "w") as fh:
        json.dump(meta, fh, indent=2, sort_keys=True)
    print("\nmeta ->", meta_path)
    print("STAGE_K_OK examples=%d tokens=%d shards=%d" % (n_ex, stream.size, n_shards))


if __name__ == "__main__":
    main()
