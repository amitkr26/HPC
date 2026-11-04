"""Stage E: tokenize the pilot corpus into a training token stream.

Runs on a compute node. Reads /home only -- no network. Every document is
encoded with our Stage D tokenizer and separated by <|eos|>, producing one
contiguous int32 token stream plus fixed-length shards for training.
"""
import json
import os
import time

import numpy as np
from tokenizers import Tokenizer

ROOT = os.path.expanduser("~/bdw-llm")
RAW = os.path.join(ROOT, "data/raw/fineweb_pilot.jsonl")
TOK = os.path.join(ROOT, "tokenizer/tokenizer.json")
OUTDIR = os.path.join(ROOT, "tokens")
SEQ_LEN = 1024
SHARD_TOKENS = 1_000_000          # ~2 MB per int32 shard file


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    tok = Tokenizer.from_file(TOK)
    eos = tok.token_to_id("<|eos|>")
    pad = tok.token_to_id("<|pad|>")
    bos = tok.token_to_id("<|bos|>")
    vs = tok.get_vocab_size()
    print("tokenizer   :", TOK)
    print("vocab_size  :", vs)
    print("special ids : pad=%d bos=%d eos=%d" % (pad, bos, eos))

    t0 = time.time()
    chunks = []          # list of np arrays, one per document (stream building)
    n_docs = 0
    n_skipped = 0
    with open(RAW, encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            text = rec.get("text") or ""
            if not text:
                n_skipped += 1
                continue
            ids = tok.encode(text).ids
            ids.append(eos)
            chunks.append(np.asarray(ids, dtype=np.int32))
            n_docs += 1

    stream = np.concatenate(chunks) if chunks else np.zeros(0, dtype=np.int32)
    del chunks
    enc_t = time.time() - t0
    print("docs        : %d (skipped %d)" % (n_docs, n_skipped))
    print("tokens      : %d" % stream.size)
    print("encode_time : %.1fs (%.0f tokens/s)" % (enc_t, stream.size / max(enc_t, 1e-9)))
    print("id range    : min=%d max=%d (vocab=%d)" % (stream.min(), stream.max(), vs))
    if stream.max() >= vs or stream.min() < 0:
        raise SystemExit("token id out of range")

    stream_path = os.path.join(OUTDIR, "stream.npy")
    np.save(stream_path, stream)
    print("saved       :", stream_path, os.path.getsize(stream_path), "bytes")

    # fixed-length shards for training (drop the tail that doesn't fill a row)
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
        shard_sizes.append((p, part.shape, os.path.getsize(p)))
    print("seq_len     : %d" % SEQ_LEN)
    print("rows        : %d  (tail %d tokens dropped)" % (n_rows, stream.size - n_rows * SEQ_LEN))
    print("shards      : %d" % n_shards)
    for p, shape, sz in shard_sizes[:4]:
        print("   %-52s %-16s %d" % (os.path.basename(p), str(shape), sz))
    if n_shards > 4:
        print("   ... (%d more)" % (n_shards - 4))

    # ---- verification ----
    print("\n--- verification ---")
    idx = np.random.default_rng(0).integers(0, n_rows)
    chunk = rows[idx]
    dec = tok.decode(chunk.tolist())
    print("random row %d: ids=%d first10=%s" % (idx, len(chunk), chunk[:10].tolist()))
    print("decoded head: %r" % dec[:120])
    print("decoded tail: %r" % dec[-60:])
    # a row is a slice across document boundaries, so it is not required to
    # decode cleanly; instead verify round-trip on a whole document
    with open(RAW, encoding="utf-8") as fh:
        rec = json.loads(fh.readline())
    t = rec["text"]
    rt = tok.decode(tok.encode(t).ids) == t
    print("doc round-trip lossless:", rt)
    if not rt:
        raise SystemExit("round-trip failed")

    meta = {
        "source_jsonl": RAW,
        "tokenizer": TOK,
        "vocab_size": vs,
        "docs": n_docs,
        "tokens": int(stream.size),
        "seq_len": SEQ_LEN,
        "rows": int(n_rows),
        "shards": n_shards,
        "dtype": "int32",
        "special_ids": {"pad": pad, "bos": bos, "eos": eos},
    }
    with open(os.path.join(OUTDIR, "meta.json"), "w") as fh:
        json.dump(meta, fh, indent=2)
    print("\nmeta ->", os.path.join(OUTDIR, "meta.json"))
    print("TOKENIZE_%s" % ("OK" if rt else "FAILED"))


if __name__ == "__main__":
    main()
