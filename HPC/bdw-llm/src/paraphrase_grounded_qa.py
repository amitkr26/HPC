"""Stage O.3a-v5 (paraphrase augmentation): the A/B questions are phrased
differently from training questions, and the 28M student only associates
answer content with the exact wording it saw -- eval answers came back as
paraphrastic mush. More pages of OTHER topics cannot fix four fixed A/B
questions; denser (question -> same answer) mappings can.

For every grounded pair, ask the teacher to rephrase the QUESTION twice
(the answer is reused verbatim, so factual accuracy cannot regress), then
re-tokenize originals + paraphrases together with the Stage K template.

Resume: one record per ORIGINAL pair in data/grounded_qa_par.jsonl keyed by
qid, so a MaxWall kill resumes mid-list. Accepts a paraphrase only if it is
6-30 words, not identical to the original, and not a duplicate of any
question already in the corpus.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_grounded_qa import (  # noqa: E402
    TEACHER, device_of, tokenize_and_shard,
)

ROOT = os.path.expanduser("~/bdw-llm")
SRC_JSONL = os.path.join(ROOT, "data/grounded_qa_final.jsonl")
WORK_JSONL = os.path.join(ROOT, "data/grounded_qa_par.jsonl")

BATCH = 8
MAX_NEW = 96
TEMP, TOP_P = 0.5, 0.95
SEED = 4242
LIMIT = 9 * 60
N_PARA = 2
MIN_W, MAX_W = 6, 30

INSTR = (
    "Question: {q}\n\n"
    "Write {n} different natural ways to ask exactly the same question. "
    "Keep the same meaning; change only the wording. Each phrasing must be "
    "a complete standalone question. Output only the {n} questions, one per "
    "line, like:\n1. ...\n2. ..."
)
NUM_RE = re.compile(r"^\s*\d+\s*[.)]\s*")


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


def main():
    src = [r for r in load_jsonl(SRC_JSONL)
           if (r.get("response") or "").strip() and r.get("qid")]
    done = {}
    for r in load_jsonl(WORK_JSONL):
        if r.get("qid"):
            done[r["qid"]] = r
    todo = [r for r in src if r["qid"] not in done]

    seen = {r["qid"] for r in src}
    seen_words = {" ".join(r["question"].lower().split()) for r in src}
    for rec in done.values():
        for p in rec.get("paras", []):
            seen_words.add(" ".join(p.lower().split()))

    print("=" * 74)
    print("STAGE O.3a-v5 -- QUESTION-PARAPHRASE AUGMENTATION (answers fixed)")
    print("=" * 74)
    print("source : %s (%d pairs)" % (SRC_JSONL, len(src)))
    print("work   : %s (%d done)" % (WORK_JSONL, len(done)))
    print("todo   : %d originals -> %d paraphrases" % (len(todo), len(todo) * N_PARA))

    if todo:
        t_tok = AutoTokenizer.from_pretrained(TEACHER, local_files_only=True)
        t_tok.padding_side = "left"
        t0 = time.time()
        model = AutoModelForCausalLM.from_pretrained(
            TEACHER, torch_dtype=torch.bfloat16, local_files_only=True,
            attn_implementation="sdpa").to("cuda")
        print("[teacher] loaded in %.1fs" % (time.time() - t0))

        stats = {"ok": 0, "short": 0, "same": 0, "dup": 0, "empty": 0}
        with open(WORK_JSONL, "a", encoding="utf-8") as fh:
            t_start = time.time()
            torch.manual_seed(SEED)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(SEED)
            for i in range(0, len(todo), BATCH):
                if time.time() - t_start > LIMIT:
                    print("[wall] %ds elapsed, stopping -- %d left"
                          % (LIMIT, len(todo) - i))
                    break
                batch = todo[i:i + BATCH]
                prompts = [t_tok.apply_chat_template(
                    [{"role": "user", "content": INSTR.format(q=r["question"],
                                                              n=N_PARA)}],
                    tokenize=False, add_generation_prompt=True)
                    for r in batch]
                enc = t_tok(prompts, return_tensors="pt", padding=True,
                            truncation=True, max_length=1024).to(
                                device_of(model))
                n_prompt = int(enc["input_ids"].shape[1])
                with torch.no_grad():
                    out = model.generate(
                        input_ids=enc["input_ids"],
                        attention_mask=enc["attention_mask"],
                        max_new_tokens=MAX_NEW, do_sample=True,
                        temperature=TEMP, top_p=TOP_P,
                        pad_token_id=t_tok.pad_token_id or t_tok.eos_token_id,
                        eos_token_id=t_tok.eos_token_id)
                for r, ids in zip(batch, out[:, n_prompt:]):
                    raw = t_tok.decode(ids, skip_special_tokens=True)
                    cands = []
                    for line in raw.splitlines():
                        line = " ".join(NUM_RE.sub("", line).strip().split())
                        if line:
                            cands.append(line)
                    orig = " ".join(r["question"].lower().split())
                    paras = []
                    for c in cands[:N_PARA + 2]:
                        if len(paras) >= N_PARA:
                            break
                        w = c.split()
                        if len(w) < MIN_W:
                            stats["short"] += 1
                            continue
                        if len(w) > MAX_W:
                            stats["short"] += 1
                            continue
                        if " ".join(c.lower().split()) == orig:
                            stats["same"] += 1
                            continue
                        if " ".join(c.lower().split()) in seen_words:
                            stats["dup"] += 1
                            continue
                        paras.append(c)
                        seen_words.add(" ".join(c.lower().split()))
                    if len(paras) < N_PARA:
                        stats["empty"] += N_PARA - len(paras)
                    stats["ok"] += len(paras)
                    fh.write(json.dumps({"qid": r["qid"], "paras": paras},
                                        ensure_ascii=False) + "\n")
                fh.flush()
                if (i // BATCH) % 10 == 0:
                    el = time.time() - t_start
                    rate = (i + len(batch)) / max(el, 1e-9)
                    print("[para] %d/%d ok=%d  %.1f/s  elapsed %ds"
                          % (i + len(batch), len(todo), stats["ok"], rate, el),
                          flush=True)

        missing = [r for r in src if r["qid"] not in done]
        print("-" * 74)
        print("paraphrases : %d accepted  rejects: %s"
              % (stats["ok"], {k: v for k, v in stats.items()
                               if k != "ok" and v}))
        if missing:
            print("RESULT: O3A_PARA_PARTIAL missing=%d -- resubmit" % len(missing))
            return

    # assemble originals + paraphrases (answers verbatim)
    final = []
    para_of = {}
    for rec in done.values():
        for p in rec.get("paras", []):
            para_of[p] = rec["qid"]
    for r in src:
        final.append(dict(r, augmented=False))
        for p in [p for p, o in para_of.items() if o == r["qid"]]:
            final.append({"qid": hashlib.md5(
                              p.lower().encode()).hexdigest()[:16],
                          "chunk": r["chunk"], "title": r.get("title", ""),
                          "url": r.get("url", ""),
                          "requested": r.get("requested", ""),
                          "question": p, "response": r["response"],
                          "augmented": True, "teacher": r.get("teacher", ""),
                          "para_of": r["qid"]})
    outp = os.path.join(ROOT, "data/grounded_qa_aug.jsonl")
    with open(outp, "w", encoding="utf-8") as fh:
        for rec in final:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    n_aug = sum(1 for r in final if r.get("augmented"))
    print("assembled  : %d rows (%d original + %d paraphrase) -> %s"
          % (len(final), len(final) - n_aug, n_aug, outp))
    print("\n--- tokenize (16K BPE, Stage K template) ---")
    tokenize_and_shard(final)


if __name__ == "__main__":
    main()
