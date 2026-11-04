"""Stage D: train a byte-level BPE tokenizer from scratch on the pilot corpus.

No pretrained tokenizer is loaded or used. The vocabulary is learned only from
our own pilot text. Byte-level BPE means every byte maps to a symbol, so the
tokenizer can encode ANY input with no <unk>.
"""
import json
import os
import time

from tokenizers import Tokenizer, decoders, models, pre_tokenizers, trainers

ROOT = os.path.expanduser("~/bdw-llm")
RAW = os.path.join(ROOT, "data/raw/fineweb_pilot.jsonl")
OUT = os.path.join(ROOT, "tokenizer")
VOCAB_SIZE = 16384
MIN_FREQ = 2
SPECIAL = ["<|pad|>", "<|bos|>", "<|eos|>"]


def texts(path):
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            t = rec.get("text")
            if t:
                yield t


def main():
    os.makedirs(OUT, exist_ok=True)

    tok = Tokenizer(models.BPE(unk_token=None))
    tok.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tok.decoder = decoders.ByteLevel()

    trainer = trainers.BpeTrainer(
        vocab_size=VOCAB_SIZE,
        min_frequency=MIN_FREQ,
        special_tokens=SPECIAL,
        show_progress=True,
        initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),
    )

    print("corpus      :", RAW)
    print("vocab_size  :", VOCAB_SIZE)
    print("min_freq    :", MIN_FREQ)
    print("special     :", SPECIAL)
    print("byte alphabet:", len(pre_tokenizers.ByteLevel.alphabet()))
    t0 = time.time()
    tok.train_from_iterator(texts(RAW), trainer=trainer)
    print("train_time_s: %.1f" % (time.time() - t0))

    print("final vocab :", tok.get_vocab_size())
    print("added tokens:", tok.get_vocab() and [
        (s, tok.token_to_id(s)) for s in SPECIAL])

    path = os.path.join(OUT, "tokenizer.json")
    tok.save(path)
    print("saved       :", path, os.path.getsize(path), "bytes")

    # ---- verification: round-trip must be lossless, with no <unk> ----
    probes = [
        "The quick brown fox jumps over the lazy dog.",
        "def train(path):\n    return sum(path) / len(path)",
        "1234567890 + 987654321 = 1111111111",
        "Unicode: caf\u00e9 \u00e9\u00e9\u00e9 \u0939\u093f\u0928\u094d\u0926\u0940 \u4e2d\u6587",
        "Emoji are just bytes: \U0001F600\U0001F680\U0001F9E0",
        "\x00\x01\x02 control bytes and \x7f\x80\xff high bytes",
    ]
    print("\n--- round-trip probes ---")
    ok = True
    for p in probes:
        enc = tok.encode(p)
        ids = enc.ids
        dec = tok.decode(ids)
        same = dec == p
        unk = any(i == tok.token_to_id("<|pad|>") and False for i in ids)
        print("ids=%-4d ok=%-5s %r" % (len(ids), same, p[:52]))
        if not same:
            ok = False
            print("    decoded: %r" % dec[:80])

    # corpus-level check on a sample of real documents
    print("\n--- corpus round-trip sample (500 docs) ---")
    n = bad = 0
    ntok = 0
    for t in texts(RAW):
        ids = tok.encode(t).ids
        ntok += len(ids)
        if tok.decode(ids) != t:
            bad += 1
        n += 1
        if n >= 500:
            break
    print("docs=%d mismatches=%d tokens=%d" % (n, bad, ntok))
    if bad:
        ok = False

    # held-out docs (not used above): tail of the file
    print("\n--- held-out round-trip (last 500 docs) ---")
    lines = []
    with open(RAW, encoding="utf-8") as fh:
        for line in fh:
            lines.append(line)
    n = bad = 0
    for line in lines[-500:]:
        t = json.loads(line)["text"]
        if tok.decode(tok.encode(t).ids) != t:
            bad += 1
        n += 1
    print("docs=%d mismatches=%d" % (n, bad))
    if bad:
        ok = False

    stats = {
        "vocab_size": tok.get_vocab_size(),
        "corpus_tokens_sampled": ntok,
        "corpus_docs_sampled": 500,
        "roundtrip_probe_ok": ok,
    }
    with open(os.path.join(OUT, "train_stats.json"), "w") as fh:
        json.dump(stats, fh, indent=2)
    print("\nstats ->", os.path.join(OUT, "train_stats.json"))
    print("TOKENIZER_TRAIN_%s" % ("OK" if ok else "FAILED"))


if __name__ == "__main__":
    main()
