"""Stage N.3 (qualitative): before/after distillation chat comparison.

N.3b moved held-out perplexity 27.21 -> 19.28, but a regression number on the
same distribution says nothing about technical accuracy. This asks BOTH
students the same VLSI questions and prints the answers side by side:

    checkpoints_ft/step_0003000.pt          Stage L  (before distillation)
    checkpoints_distilled/step_0000200.pt   after 200 steps on 7B-teacher data

Both models get the identical prompt (chat_with_rag.PROMPT_TAIL, which is
exactly the Stage K training format) and the identical decoding: greedy
(temperature 0, top_k 0 -> argmax), repetition penalty 1.2, loop guard 8 --
the settings Stage M established for this 28M model. The only variable is
the weights.

CPU only, no network: runs on the LOGIN node like Stage M did.

P2.4 extension (ship gate, blueprint S7): the same script now assembles the
Phase-2 A/B from two p2_baseline eval JSONs --

    python compare_distill.py --ab-a eval/p2_base_v2.json \
                              --ab-b eval/p2_sft_v2.json

with labels `7B Instruct zero-shot` vs `7B BDW-SFT`: it verifies both files
are the same suite (pid + prompt equality), prints the metric deltas and the
30 prompt transcripts side by side (O.4 method) for docs/PHASE2_EVAL.md.
That mode is stdlib-only (no torch) so it also runs on a laptop; the Stage
N.3 path above is untouched.
"""
from __future__ import annotations

import argparse
import gc
import os
import sys
import textwrap
import time

try:
    import torch
    from tokenizers import Tokenizer
    from chat_with_rag import (PROMPT_TAIL, build_prompt, generate_ids,
                               load_model)
except ImportError:            # --ab-a/--ab-b mode is stdlib-only
    torch = None
    Tokenizer = None
    PROMPT_TAIL = build_prompt = generate_ids = load_model = None

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.expanduser("~/bdw-llm")
TOKENIZER = os.path.join(ROOT, "tokenizer/tokenizer.json")
STAGE_L = os.path.join(ROOT, "checkpoints_ft/step_0003000.pt")
DISTILLED = os.path.join(ROOT, "checkpoints_distilled_v2/step_0000200.pt")

QUESTIONS = [
    "Explain setup time and hold time in a flip-flop. "
    "What happens if either is violated?",
    "What is ATPG, and why is it used in chip testing?",
    "Why did the semiconductor industry move from planar MOSFETs to FinFETs?",
    "How do you safely pass a signal from one clock domain to another?",
]


def parse_args():
    p = argparse.ArgumentParser(
        description="Stage N.3 qualitative A/B: Stage L vs distilled student")
    p.add_argument("--stage-l-ckpt", default=STAGE_L)
    p.add_argument("--distilled-ckpt", default=DISTILLED)
    p.add_argument("--max-new-tokens", type=int, default=180)
    p.add_argument("--temperature", type=float, default=0.0,
                   help="0.0 = greedy (argmax); identical for both models")
    p.add_argument("--repetition-penalty", type=float, default=1.2)
    p.add_argument("--threads", type=int, default=4,
                   help="CPU threads -- login node is shared, stay at 4")
    p.add_argument("--cols", type=int, default=46,
                   help="width of each side-by-side column")
    p.add_argument("--label-a", default="7B Instruct zero-shot",
                   help="left label for --ab-a/--ab-b mode")
    p.add_argument("--label-b", default=None,
                   help="right label (default: DISTILLED ... in Stage N.3 "
                        "mode, 7B BDW-SFT in --ab mode)")
    p.add_argument("--ab-a", default="",
                   help="baseline eval JSON (p2_baseline output)")
    p.add_argument("--ab-b", default="",
                   help="post-training eval JSON (same suite)")
    p.add_argument("--pids", default="",
                   help="comma list of pids to print (default: all)")
    p.add_argument("--ab-out", default="",
                   help="also write the A/B dump to this file")
    p.add_argument("--seed", type=int, default=1337)
    return p.parse_args()


def ask_one(model, tok, bos, eos, question, args):
    """One no-context answer. Same code path for both checkpoints."""
    prompt = build_prompt(question, [])        # no passages == --no-rag
    ids = tok.encode(prompt, add_special_tokens=False).ids
    torch.manual_seed(args.seed)
    t0 = time.time()
    out, hit_eos = generate_ids(model, list(ids), args.max_new_tokens,
                                args.temperature, 0, eos,  # top_k 0 -> argmax
                                repetition_penalty=args.repetition_penalty,
                                penalize_prompt=False, loop_stop=8)
    dt = time.time() - t0
    new_ids = out[len(ids):]
    text = tok.decode(new_ids, skip_special_tokens=True).strip()
    return text, len(new_ids), dt, hit_eos, ids[:1] == [bos]


def ab_mode(args):
    """P2.4 A/B: two p2_baseline JSONs -> metric deltas + side-by-side
    transcripts (O.4 method), the material docs/PHASE2_EVAL.md quotes."""
    import json

    with open(args.ab_a, encoding="utf-8") as fh:
        a = json.load(fh)
    with open(args.ab_b, encoding="utf-8") as fh:
        b = json.load(fh)
    if a.get("suite") != b.get("suite"):
        raise SystemExit("suite mismatch: %r vs %r"
                         % (a.get("suite"), b.get("suite")))
    pa, pb = a["prompts"], b["prompts"]
    if [p["pid"] for p in pa] != [p["pid"] for p in pb] \
            or [p["prompt"] for p in pa] != [p["prompt"] for p in pb]:
        raise SystemExit("suite mismatch: pids/prompts differ between files")
    known = [p["pid"] for p in pa]
    sel = known
    if args.pids:
        want = [x.strip() for x in args.pids.split(",") if x.strip()]
        missing = [x for x in want if x not in known]
        if missing:
            raise SystemExit("pids not in suite: %s" % missing)
        sel = want
    la, lb = args.label_a, (args.label_b or "7B BDW-SFT")

    lines = []

    def emit(s=""):
        print(s)
        lines.append(s)

    def fr(n, d):
        return "%d/%d" % (n, d)

    emit("=" * 100)
    emit("P2.4 A/B -- %s  vs  %s  (suite %s, %d prompts)"
         % (la, lb, a.get("suite"), len(pa)))
    emit("=" * 100)
    emit("files     : %s | %s" % (args.ab_a, args.ab_b))
    emit("decoding  : %s (both sides)"
         % json.dumps(a.get("decoding", {}), sort_keys=True))
    emit("models    : %s | %s" % (a.get("model"), b.get("model")))
    emit()

    ma, mb = a["metrics"], b["metrics"]

    def row(label, va, vb):
        emit("%-22s %14s | %14s" % (label, va, vb))

    emit("%-22s %14s | %14s" % ("metric", la[:14], lb[:14]))
    emit("-" * 56)
    row("ExactMatch", fr(ma["ExactMatch"]["hit"], ma["ExactMatch"]["n"]),
        fr(mb["ExactMatch"]["hit"], mb["ExactMatch"]["n"]))
    row("EligibilityVerbatim",
        fr(ma["EligibilityVerbatim"]["hit"], ma["EligibilityVerbatim"]["n"]),
        fr(mb["EligibilityVerbatim"]["hit"], mb["EligibilityVerbatim"]["n"]))
    row("FieldFidelity prompts",
        fr(ma["FieldFidelity"]["pass"], ma["FieldFidelity"]["n"]),
        fr(mb["FieldFidelity"]["pass"], mb["FieldFidelity"]["n"]))
    row("FieldFidelity numbers",
        fr(ma["FieldFidelity"]["nums_ok"], ma["FieldFidelity"]["nums"]),
        fr(mb["FieldFidelity"]["nums_ok"], mb["FieldFidelity"]["nums"]))
    ca, cb = ma["CitationResolution"], mb["CitationResolution"]
    row("CitationResolution",
        "%s (%d cited)" % (fr(ca["resolved"], ca["cites"]), ca["prompts"]),
        "%s (%d cited)" % (fr(cb["resolved"], cb["cites"]), cb["prompts"]))
    row("Refusal should-refuse",
        fr(ma["RefusalCorrect"]["should_refuse"]["ok"],
           ma["RefusalCorrect"]["should_refuse"]["n"]),
        fr(mb["RefusalCorrect"]["should_refuse"]["ok"],
           mb["RefusalCorrect"]["should_refuse"]["n"]))
    row("Refusal should-answer",
        fr(ma["RefusalCorrect"]["should_answer"]["ok"],
           ma["RefusalCorrect"]["should_answer"]["n"]),
        fr(mb["RefusalCorrect"]["should_answer"]["ok"],
           mb["RefusalCorrect"]["should_answer"]["n"]))
    row("GeneralEnglish",
        fr(ma["GeneralEnglish"]["on_task"], ma["GeneralEnglish"]["n"]),
        fr(mb["GeneralEnglish"]["on_task"], mb["GeneralEnglish"]["n"]))
    emit()
    emit("=" * 100)
    emit("TRANSCRIPTS (identical prompt + greedy decode; only the weights differ)")
    emit("=" * 100)

    by_b = {p["pid"]: p for p in pb}
    cite_re = __import__("re").compile(r"\(Ref:\s*([^)]+?)\)")
    for p in pa:
        if p["pid"] not in sel:
            continue
        q = by_b[p["pid"]]
        emit()
        emit("%s [%s]  %s" % (p["pid"], p["group"], p["prompt"]))
        if p.get("expected"):
            emit("expected: %s" % p["expected"])
        oa, ob = p.get("output", "") or "(empty)", \
            q.get("output", "") or "(empty)"
        ra = textwrap.fill(oa, args.cols).split("\n")
        rb = textwrap.fill(ob, args.cols).split("\n")
        emit("%-*s | %s" % (args.cols, la[:args.cols], lb[:args.cols]))
        emit("-" * args.cols + "-+-" + "-" * args.cols)
        for k in range(max(len(ra), len(rb))):
            emit("%-*s | %s" % (args.cols,
                                ra[k] if k < len(ra) else "",
                                rb[k] if k < len(rb) else ""))
        emit("cites: %s | %s"
             % (cite_re.findall(oa) or "-", cite_re.findall(ob) or "-"))

    emit()
    emit("RESULT: P2_AB_OK prompts=%d suite=%s a=%r b=%r"
         % (len(sel), a.get("suite"), la, lb))
    if args.ab_out:
        with open(args.ab_out, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        print("wrote %s (%d B)" % (args.ab_out, os.path.getsize(args.ab_out)))


def main():
    args = parse_args()
    if args.ab_a or args.ab_b:
        if not (args.ab_a and args.ab_b):
            raise SystemExit("--ab-a and --ab-b must be given together")
        ab_mode(args)
        return
    if torch is None:
        raise SystemExit("Stage N.3 mode needs torch + chat_with_rag; the "
                         "--ab-a/--ab-b mode is stdlib-only")
    torch.set_num_threads(args.threads)

    tok = Tokenizer.from_file(TOKENIZER)
    bos = tok.token_to_id("<|bos|>")
    eos = tok.token_to_id("<|eos|>")
    print("=" * 100)
    print("STAGE N.3 QUALITATIVE A/B -- Stage L (before) vs distilled (after)")
    print("=" * 100)
    print("tokenizer : vocab=%d bos=%d eos=%d  %s"
          % (tok.get_vocab_size(), bos, eos, TOKENIZER))
    print("prompt    : %r" % PROMPT_TAIL)
    print("decode    : greedy temp=%g top_k=0 rep_penalty=%.1f loop_stop=8 "
          "max_new=%d seed=%d threads=%d"
          % (args.temperature, args.repetition_penalty, args.max_new_tokens,
             args.seed, args.threads))
    print("questions : %d (identical for both models)" % len(QUESTIONS))
    print()

    ckpts = [("Stage L (before KD)", args.stage_l_ckpt),
             ("Distilled (after KD)", args.distilled_ckpt)]
    results = {}
    for label, path in ckpts:
        if not os.path.exists(path):
            raise SystemExit("checkpoint missing: %s" % path)
        model, blob = load_model(path, "cpu")
        rows = []
        for i, q in enumerate(QUESTIONS, 1):
            text, n_new, dt, hit, started_bos = ask_one(
                model, tok, bos, eos, q, args)
            rows.append({"text": text, "n": n_new, "s": dt, "eos": hit})
            print("[%-19s] Q%d  %3d new tok  %5.1fs  %.1f tok/s  eos=%s%s"
                  % (label, i, n_new, dt, n_new / max(dt, 1e-9), hit,
                     "" if started_bos else "  [WARN prompt !bos]"))
        results[label] = rows
        del model
        gc.collect()
        print()

    print("=" * 100)
    print("SIDE BY SIDE (same prompt, same decode; only the weights differ)")
    print("=" * 100)
    for i, q in enumerate(QUESTIONS, 1):
        print()
        print("Q%d: %s" % (i, q))
        left_label = "STAGE L  (step 3000, before KD)"
        right_label = args.label_b or "DISTILLED  (step 200, after KD)"
        print("%-*s | %s" % (args.cols, left_label, right_label))
        print("-" * args.cols + "-+-" + "-" * args.cols)

        a = results["Stage L (before KD)"][i - 1]
        b = results["Distilled (after KD)"][i - 1]
        la = textwrap.fill(a["text"] or "(empty -- no text before eos)",
                           args.cols)
        lb = textwrap.fill(b["text"] or "(empty -- no text before eos)",
                           args.cols)
        ra, rb = la.split("\n"), lb.split("\n")
        for k in range(max(len(ra), len(rb))):
            print("%-*s | %s" % (args.cols,
                                 ra[k] if k < len(ra) else "",
                                 rb[k] if k < len(rb) else ""))
        print("gen: %d tok in %.1fs eos=%s   ||   %d tok in %.1fs eos=%s"
              % (a["n"], a["s"], a["eos"], b["n"], b["s"], b["eos"]))

    print()
    print("RESULT: N3C_QUAL_OK questions=%d models=%d"
          % (len(QUESTIONS), len(ckpts)))


if __name__ == "__main__":
    main()
