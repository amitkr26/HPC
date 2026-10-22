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
"""
from __future__ import annotations

import argparse
import gc
import os
import sys
import textwrap
import time

import torch
from tokenizers import Tokenizer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chat_with_rag import PROMPT_TAIL, build_prompt, generate_ids, load_model

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
    p.add_argument("--label-b", default="DISTILLED  (step 200, after KD)",
                   help="display label for the second model")
    p.add_argument("--seed", type=int, default=1337)
    return p.parse_args()


def ask_one(model, tok, bos, eos, question, args):
    """One no-context answer. Same code path for both checkpoints."""
    prompt = build_prompt(question, [])        # no passages == --no-rag
    ids = tok.encode(prompt, add_special_tokens=False).ids
    torch.manual_seed(args.seed)
    t0 = time.time()
    out = generate_ids(model, list(ids), args.max_new_tokens,
                       args.temperature, 0, eos,          # top_k 0 -> pure argmax
                       repetition_penalty=args.repetition_penalty,
                       penalize_prompt=False, loop_stop=8)
    dt = time.time() - t0
    new_ids = out[len(ids):]
    text = tok.decode(new_ids, skip_special_tokens=True).strip()
    hit_eos = bool(new_ids) and out[-1] == eos
    return text, len(new_ids), dt, hit_eos, ids[:1] == [bos]


def main():
    args = parse_args()
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
        right_label = args.label_b
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
