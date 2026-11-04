"""Stage P: domain-tokenizer A/B/C test.

Trains two byte-level BPE tokenizers on BDW's own corpus and compares all
three against the exact probe set used in Stage O (docs/BDW_INTEGRATION.md 8):

    general-16K  the tokenizer shipped in tokenizer/tokenizer.json (FineWeb)
    domain-16K   same config, trained on BDW text   -> isolates the CORPUS effect
    domain-32K   BDW text, vocab 32000              -> the proposal's 8.2 step 1

Everything except the training corpus/vocab is held identical to Stage D
(byte-level BPE, no unk token, ByteLevel pre-tokenizer, min_frequency=2,
same 3 special tokens), so any difference is attributable to corpus/vocab.
"""
import os
import sys
import time

from tokenizers import Tokenizer, decoders, models, pre_tokenizers, trainers

ROOT = os.path.expanduser("~/bdw-llm")
DOMAIN = os.path.join(ROOT, "data/raw/bdw_domain.jsonl")
GEN16 = os.path.join(ROOT, "tokenizer/tokenizer.json")
OUTDIR = os.path.join(ROOT, "tokenizer_domain")
SPECIAL = ["<|pad|>", "<|bos|>", "<|eos|>"]
MIN_FREQ = 2
os.makedirs(OUTDIR, exist_ok=True)


def texts(path):
    import json
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            t = rec.get("text")
            if t:
                yield t


def train(corpus_path, vocab_size, name):
    tok = Tokenizer(models.BPE(unk_token=None))
    tok.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tok.decoder = decoders.ByteLevel()
    trainer = trainers.BpeTrainer(
        vocab_size=vocab_size, min_frequency=MIN_FREQ, special_tokens=SPECIAL,
        show_progress=False, initial_alphabet=pre_tokenizers.ByteLevel.alphabet())
    t0 = time.time()
    tok.train_from_iterator(texts(corpus_path), trainer=trainer)
    path = os.path.join(OUTDIR, name + ".json")
    tok.save(path)
    print("[train] %-14s target=%-6d actual=%-6d %.1fs -> %s"
          % (name, vocab_size, tok.get_vocab_size(), time.time() - t0, path))
    return tok, path


# ------------------------------------------------------------------ probe
TERMS = [
    "SerDes", "FinFET", "tape-out", "tapeout", "hold violation",
    "setup violation", "static timing analysis", "Design for Testability",
    "Gate-All-Around", "nanosheet", "ATMP", "OSAT", "UCIe", "ATPG",
    "scan chain", "clock tree synthesis", "latch-up", "DRC", "LVS", "PDK",
    "MPW", "shuttle", "wafer", "yield", "fabless", "foundry", "signoff",
    "IR drop", "crosstalk", "dummy fill", "JRF", "SRF", "HRA", "RAC",
    "CSIR", "CeNSE", "SSPL", "DLRL", "LRDE", "DEAL", "URSC", "VSSC",
    "Tessolve", "Cadence", "Synopsys", "Qualcomm", "SystemVerilog",
    "UVM", "RTL", "STA", "DFT", "FPGA", "ASIC", "CMOS", "GAA",
]
PHRASES = [
    "A hold violation occurs when data arrives too early at the receiving flip-flop.",
    "The primary role of the EDA tool during synthesis is to translate RTL code into a gate-level netlist.",
    "Gate-All-Around 3D transistors overcome short-channel leakage at sub-3nm nanosheet fabrication nodes.",
    "JRF vs SRF: DST OM stipend rules, eligibility criteria, and promotion roadmap.",
    "Serializer/Deserializer interconnect for PCIe Gen 6/7, Ethernet, and UCIe chiplets.",
]
ENGLISH = [
    "the", "temperature", "electrical", "information", "government",
    "opportunity", "engineering", "international", "development",
    "approximately", "characteristics", "responsibilities",
    "The quick brown fox jumps over the lazy dog.",
    "A black hole is an astronomical body so compact that its gravity prevents anything from escaping.",
]


def stats(tok, items):
    c = t = frag = 0
    for s in items:
        ids = tok.encode(s).ids
        c += len(s)
        t += len(ids)
        if len(ids) > 1 and " " not in s:
            frag += 1
    return c, t, (c / t if t else 0), frag


def main():
    print("=" * 90)
    print("STAGE P — DOMAIN TOKENIZER A/B/C")
    print("=" * 90)
    if not os.path.exists(DOMAIN):
        raise SystemExit("domain corpus missing: " + DOMAIN)
    nchars = sum(len(t) for t in texts(DOMAIN))
    ndocs = sum(1 for _ in open(DOMAIN, encoding="utf-8"))
    print("domain corpus: %s  docs=%d  chars=%d (~%.2f MB)"
          % (DOMAIN, ndocs, nchars, nchars / 1e6))
    if nchars < 20000:
        raise SystemExit("corpus too small to train a meaningful BPE")

    gen16 = Tokenizer.from_file(GEN16)
    d16, p16 = train(DOMAIN, 16384, "domain_bpe_16k")
    d32, p32 = train(DOMAIN, 32000, "domain_bpe_32k")
    tks = [("general-16K (shipped)", gen16), ("domain-16K", d16), ("domain-32K", d32)]

    # round-trip must stay lossless for all three
    print("\n--- round-trip lossless check (100 domain docs) ---")
    ok = True
    for name, tk in tks:
        bad = 0
        n = 0
        for t in texts(DOMAIN):
            if tk.decode(tk.encode(t).ids) != t:
                bad += 1
            n += 1
            if n >= 100:
                break
        print("  %-22s docs=%3d mismatches=%d" % (name, n, bad))
        ok = ok and (bad == 0)

    # ---------------------------------------------------- domain terms
    print()
    print("=" * 90)
    print("DOMAIN TERMS  (chars/token — higher is better compression)")
    print("=" * 90)
    print("%-22s %14s %14s %14s %12s" % ("tokenizer", "domain terms", "chars/tok",
                                         "tokens/55 terms", "split>1"))
    print("-" * 90)
    base_tok_per_term = None
    for name, tk in tks:
        c, t, cpt, frag = stats(tk, TERMS)
        if base_tok_per_term is None:
            base_tok_per_term = t
        print("%-22s %14s %14.2f %14d %11d/%d"
              % (name, "%d chars" % c, cpt, t, frag, len(TERMS)))
    print("-" * 90)
    _, _, cpt_g, _ = stats(gen16, TERMS)
    for name, tk in tks[1:]:
        _, t, cpt, _ = stats(tk, TERMS)
        print("  vs general-16K: domain-%s -> %.2f vs %.2f chars/tok  (%.2fx), tokens %d -> %d (%.0f%% fewer)"
              % ("16K" if "16K" in name else "32K", cpt, cpt_g, cpt / cpt_g,
                 base_tok_per_term, t, 100.0 * (base_tok_per_term - t) / base_tok_per_term))

    # ---------------------------------------------------------- phrases
    print()
    print("=" * 90)
    print("REAL BDW PHRASES")
    print("=" * 90)
    print("%-22s %12s %12s %12s %12s %12s" % ("tokenizer", "ph1", "ph2", "ph3", "ph4", "total"))
    print("-" * 90)
    for name, tk in tks:
        counts = [len(tk.encode(p).ids) for p in PHRASES]
        print("%-22s %12d %12d %12d %12d %12d" % (name, counts[0], counts[1],
                                                  counts[2], counts[3], sum(counts)))

    # ------------------------------------------------- general English
    print()
    print("=" * 90)
    print("GENERAL ENGLISH  (regression guard — must not degrade much)")
    print("=" * 90)
    print("%-22s %14s %14s %12s" % ("tokenizer", "chars", "chars/tok", "tokens"))
    print("-" * 90)
    for name, tk in tks:
        c, t, cpt, _ = stats(tk, ENGLISH)
        print("%-22s %14d %14.2f %12d" % (name, c, cpt, t))
    print("-" * 90)
    _, _, cpt_ge, _ = stats(gen16, ENGLISH)
    _, _, cpt_de, _ = stats(d32, ENGLISH)
    print("  general-English regression: %.2f -> %.2f chars/tok (%.0f%% change)"
          % (cpt_ge, cpt_de, 100.0 * (cpt_de - cpt_ge) / cpt_ge))

    # --------------------------------------------- worst offenders now
    print()
    print("=" * 90)
    print("WORST OFFENDERS UNDER general-16K, RE-MEASURED")
    print("=" * 90)
    worst = sorted(TERMS, key=lambda s: -len(gen16.encode(s).ids))[:12]
    print("%-22s %-14s %-16s %-16s" % ("term", "general-16K", "domain-16K", "domain-32K"))
    print("-" * 90)
    for s in worst:
        print("%-22s %-14s %-16s %-16s"
              % (s,
                 " + ".join(gen16.decode([i]) for i in gen16.encode(s).ids),
                 " + ".join(d16.decode([i]) for i in d16.encode(s).ids),
                 " + ".join(d32.decode([i]) for i in d32.encode(s).ids)))

    print()
    print("artefacts:")
    for p in (p16, p32):
        print("  %-46s %8.2f MB" % (p.replace(ROOT + "/", "~/"), os.path.getsize(p) / 1e6))
    print()
    print("RESULT: DOMAIN_TOKENIZER_AB_%s" % ("OK" if ok else "ROUNDTRIP_FAILED"))


if __name__ == "__main__":
    main()
