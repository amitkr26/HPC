"""Stage I step 2: tokenise the unseen eval corpus exactly like Stage E.

Stage E built one contiguous int32 stream in which every document is encoded
with the Stage D tokenizer and followed by <|eos|> (id 2). The eval set uses
the identical recipe so the two are directly comparable.
"""
import hashlib
import json
import os
import sys
import time

import numpy as np
from tokenizers import Tokenizer

ROOT = os.path.expanduser("~/bdw-llm")
SRC = os.path.join(ROOT, "data/eval/fineweb_eval_unseen.jsonl")
TOK = os.path.join(ROOT, "tokenizer/tokenizer.json")
OUT = os.path.join(ROOT, "data/eval/eval_tokens.npy")
META = os.path.join(ROOT, "data/eval/eval_meta.json")
SEQ_LEN = 1024
EOS = 2


def main():
    t0 = time.time()
    tk = Tokenizer.from_file(TOK)
    print("tokenizer     :", TOK)
    print("vocab size    :", tk.get_vocab_size())
    print("source        :", SRC)

    ids = []
    docs = 0
    src_bytes = 0
    with open(SRC, encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            txt = rec.get("text") or ""
            if not txt:
                continue
            ids.extend(tk.encode(txt).ids)
            ids.append(EOS)
            docs += 1
            src_bytes += len(txt.encode("utf-8"))

    arr = np.asarray(ids, dtype=np.int32)
    n = int(arr.shape[0])
    print("documents     : %d" % docs)
    print("source bytes  : %d (%.1f MB)" % (src_bytes, src_bytes / 1e6))
    print("tokens        : %d (%.2f M)" % (n, n / 1e6))
    print("id range      : [%d, %d]" % (int(arr.min()), int(arr.max())))
    print("eos count     : %d" % int((arr == EOS).sum()))
    print("encode time   : %.1fs (%d tokens/s)"
          % (time.time() - t0, n / max(time.time() - t0, 1e-9)))

    rows = n // SEQ_LEN
    print("rows of %d     : %d (tail %d tokens dropped)"
          % (SEQ_LEN, rows, n - rows * SEQ_LEN))

    np.save(OUT, arr)
    with open(META, "w") as fh:
        json.dump({
            "source_jsonl": os.path.basename(SRC),
            "source_md5": hashlib.md5(open(SRC, "rb").read()).hexdigest(),
            "source_bytes": src_bytes,
            "documents": docs,
            "tokens": n,
            "rows_of_seq_len": rows,
            "seq_len": SEQ_LEN,
            "eos_id": EOS,
            "id_min": int(arr.min()),
            "id_max": int(arr.max()),
            "encode_time_s": round(time.time() - t0, 1),
            "split_note": "offsets 60000..63400, disjoint from training URLs",
        }, fh, indent=2)

    print("saved         :", OUT, os.path.getsize(OUT), "bytes")
    print("meta          :", META)
    print("TOKENIZE_EVAL_OK")


if __name__ == "__main__":
    main()
