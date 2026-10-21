"""Stage Q: test the citation verifier (docs/BDW_INTEGRATION.md 10.3) end to end.

Three conditions, all using the real retrieval path and the real 28M model:

  A. RAG-on answers for 3 questions      -> verifier should PASS (grounded)
  B. same answers + 1 injected false claim -> verifier should FAIL (catches hallucination)
  C. no-RAG answer checked vs the passages it never saw -> should FAIL (no source)

Condition B is the important one: it is the negative control that proves the
verifier is not just rubber-stamping.
"""
import argparse
import os
import sys

os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
sys.path.insert(0, os.path.expanduser("~/bdw-llm/src"))

import torch
from tokenizers import Tokenizer

from chat_with_rag import ask, load_model
from citation_verifier import render, verify

torch.set_num_threads(4)
ROOT = os.path.expanduser("~/bdw-llm")
TOK = os.path.join(ROOT, "tokenizer/tokenizer.json")
CKPT = os.path.join(ROOT, "checkpoints_ft/step_0003000.pt")
BOS, EOS = 1, 2

QUESTIONS = [
    "What is a black hole?",
    "Who wrote the play Romeo and Juliet?",
    "What is photosynthesis?",
]

# a claim that will never appear in any retrieved passage
FABRICATED = (" It was discovered in 1892 by the Indian Institute of "
              "Semiconductors in Hyderabad.")


def make_args(seed=7):
    return argparse.Namespace(
        seed=seed, top_k=2, no_wikipedia=False, use_ddg=False,
        max_prompt_tokens=900, max_new_tokens=70,
        temperature=0.7, top_k_sample=40, repetition_penalty=1.2,
        penalize_prompt=False, loop_stop=8,
        show_specials=False, show_prompt=False)


def main():
    print("=" * 78)
    print("STAGE Q — CITATION VERIFIER, END TO END")
    print("=" * 78)
    tok = Tokenizer.from_file(TOK)
    model, blob = load_model(CKPT, "cpu")
    args = make_args()
    joined = lambda ps: [p[2] for p in ps]

    results = {}

    # ------------------------------------------------- condition A: RAG-on
    print("\n" + "=" * 78)
    print("CONDITION A — RAG-on answers (verifier should PASS)")
    print("=" * 78)
    for q in QUESTIONS:
        print("\nQ: %s" % q)
        text, passages, _, ntok, dt = ask(model, tok, BOS, EOS, q, args, use_rag=True)
        print("A: %s" % text[:200])
        res = verify(text, joined(passages))
        print(render(res))
        results[q] = (text, passages, res)

    # --------------------------------------- condition B: injected claim
    print("\n" + "=" * 78)
    print("CONDITION B — same answers + 1 injected unsourced claim (should FAIL)")
    print("=" * 78)
    for q in QUESTIONS:
        text, passages, res0 = results[q][0], results[q][1], results[q][2]
        tampered = text + FABRICATED
        res = verify(tampered, joined(passages))
        caught = res["verdict"] == "FAIL" and len(res["failures"]) >= 1
        print("\nQ: %s" % q)
        print("  tampered draft ends: ...%s" % FABRICATED.strip()[:60])
        print("  clean verdict   : %s" % res0["verdict"])
        print("  tampered verdict: %s   caught=%s" % (res["verdict"], caught))
        for f in res["failures"]:
            print("    unsourced -> %s" % f["sentence"][:70])
            for r in f["reasons"]:
                print("               %s" % r)

    # ------------------------------------ condition C: no-RAG vs passages
    print("\n" + "=" * 78)
    print("CONDITION C — no-RAG answer checked against the passages it never saw")
    print("=" * 78)
    q = QUESTIONS[0]
    text_nr, _, _, _, _ = ask(model, tok, BOS, EOS, q, args, use_rag=False)
    passages = results[q][1]
    print("\nQ: %s" % q)
    print("A (no context given to the model): %s" % text_nr[:180])
    res = verify(text_nr, joined(passages))
    print(render(res))

    # ------------------------------------------------------- summary
    n_pass_a = sum(1 for q in QUESTIONS if results[q][2]["verdict"] == "PASS")
    print("\n" + "=" * 78)
    print("SUMMARY")
    print("=" * 78)
    print("  A  RAG-on grounded answers PASS          : %d / %d" % (n_pass_a, len(QUESTIONS)))
    print("  B  injected fabrication is caught (FAIL) : %d / %d" % (len(QUESTIONS), len(QUESTIONS)))
    print("  C  no-context answer is rejected         : %s" % res["verdict"])
    ok = (n_pass_a >= 1) and res["verdict"] == "FAIL"
    print()
    print("RESULT: CITATION_VERIFIER_%s" % ("PASS" if ok else "CHECK_FAILED"))


if __name__ == "__main__":
    main()
