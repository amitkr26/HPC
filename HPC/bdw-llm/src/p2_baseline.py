"""P2.2: frozen 30-prompt baseline on the base Qwen2.5-7B-Instruct (blueprint S7).

Suite (deterministic; all domain prompts taken from data/bdw_sft.jsonl VAL rows
so none of them are ever trained on):

   10 exact-match circular  R1 val: deadline x2, stipend x2, org x2, post x2,
                            location x1, category x1 -- ground truth re-resolved
                            from the source Supabase row via bdw_column_map
    8 class-C explanations  4 R3 teacher + 4 R4 VLSI (fidelity vs teacher ctx)
    4 eligibility           R2 val: verbatim eligibility + Ref id
    4 should-refuse         R5 val topics
    4 general-English       constants (regression canaries)

Decoding is greedy (do_sample=False, seed 1337, max_new_tokens 300) so the
same script re-run after training (add --adapter <dir>) is directly comparable.

Metrics (same code before/after):
  ExactMatch          normalized expected field value occurs in the output
  EligibilityVerbatim normalized verbatim eligibility occurs in the output
  FieldFidelity       every >=3-digit token in the output exists in source text
  CitationResolution  "(Ref: id)" citations that resolve to a real Supabase id
  RefusalCorrect      should-refuse keeps a refusal marker; others stay on-task

Output: eval/p2_baseline.json (suite + outputs + metrics), atomic write.
RESULT: P2_BASELINE_OK ...  /  RESULT: P2_BASELINE_FAIL ...
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import traceback

SRC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SRC)
import bdw_build_sft as B  # noqa: E402  (recipes/regexps/resolve; side-effect free)

ROOT = os.path.expanduser("~/bdw-llm")
SFT = os.path.join(ROOT, "data/bdw_sft.jsonl")
TEACHER_QA = os.path.join(ROOT, "data/bdw_teacher_qa.jsonl")
RAW = os.path.join(ROOT, "data/raw")
BASE = os.path.join(ROOT, "teacher_model_7b")
OUT = os.path.join(ROOT, "eval/p2_baseline.json")

SEED = 1337
MAX_NEW = 300
EM_QUOTA = {"deadline": 2, "stipend": 2, "org": 2, "post": 2,
            "location": 1, "category": 1}
CLASS_C_N = 4
ELIG_N = 4
REFUSE_N = 4
GENERAL = [
    "Explain the difference between a CPU and a GPU in two sentences.",
    "Write a short polite email declining a meeting invitation for tomorrow.",
    "What are the three largest planets in our solar system?",
    "Summarise this in one sentence: The quick brown fox jumped over the lazy "
    "dog while the farmer watched from the porch.",
]
REF_CITE_RE = re.compile(r"\(Ref:\s*([^)]+?)\)")


def norm(s):
    return re.sub(r"\s+", " ", str(s).lower().replace(",", " ")).strip()


def r1_cat(question):
    if "last date" in question:
        return "deadline"
    if "stipend or salary" in question:
        return "stipend"
    if question.startswith("Which organization is offering"):
        return "org"
    if question.startswith("What is the post of"):
        return "post"
    if "located" in question:
        return "location"
    if "category" in question:
        return "category"
    return None


class RawRows(object):
    """Lazy id -> row lookup for every extracted Supabase table."""

    def __init__(self):
        self.tables = {}
        self.all_ids = set()

    def ensure(self, table):
        if table not in self.tables:
            rows = B.load_jsonl(os.path.join(RAW, "bdw_%s.jsonl" % table))
            self.tables[table] = {str(r.get("id", "")): r for r in rows}
            self.all_ids.update(self.tables[table].keys())
        return self.tables[table]

    def get(self, table, rid):
        return self.ensure(table).get(str(rid))

    def ids_everywhere(self):
        if not self.all_ids:
            for f in sorted(os.listdir(RAW)):
                if f.startswith("bdw_") and f.endswith(".jsonl") \
                        and f != "bdw_sft.jsonl" and not f.startswith("bdw_manifest"):
                    self.ensure(f[len("bdw_"):-len(".jsonl")])
        return self.all_ids


def teacher_contexts():
    ctx = {}
    if os.path.exists(TEACHER_QA):
        for r in B.load_jsonl(TEACHER_QA):
            q = (r.get("question") or "").strip()
            if q and r.get("context"):
                ctx.setdefault(q, r["context"])
    return ctx


def build_suite():
    rows = [r for r in B.load_jsonl(SFT)]
    by_src = {}
    for r in rows:
        by_src.setdefault(r["source"], []).append(r)
    for lst in by_src.values():
        lst.sort(key=lambda r: r["id"])
    raw = RawRows()
    cmap = B.load_map()
    tctx = teacher_contexts()
    suite = []

    quota = dict(EM_QUOTA)
    for r in by_src.get("r1", []):
        if r.get("split") != "val":
            continue
        cat = r1_cat(r["messages"][0]["content"])
        if not cat or quota.get(cat, 0) <= 0:
            continue
        quota[cat] -= 1
        srow = raw.get(r.get("table", ""), r.get("row_id", ""))
        if not srow:
            continue
        val = B.resolve(srow, cat if cat != "post" else "title", cmap)
        if not val:
            continue
        suite.append({
            "pid": "em_%02d" % (len(suite) + 1), "group": "exact_match",
            "prompt": r["messages"][0]["content"], "field": cat,
            "expected": val, "table": r.get("table", ""),
            "row_id": r.get("row_id", ""), "qid": r["id"],
            "fidelity": B.row_text(srow)})
        if sum(quota.values()) == 0:
            break

    n_em = sum(1 for p in suite if p["group"] == "exact_match")
    if n_em < 10:
        raise RuntimeError("exact_match suite short: %d/10 (quota=%s)"
                           % (n_em, quota))

    i = 0
    for src, tag in (("r3", "cc"), ("r4", "cc")):
        taken = 0
        for r in by_src.get(src, []):
            if taken >= CLASS_C_N:
                break
            if r.get("split") != "val":
                continue
            q = r["messages"][0]["content"]
            ref = r["messages"][1]["content"]
            fid = tctx.get(q) or ref
            suite.append({"pid": "%s_%02d" % (tag, i + 1), "group": "class_c",
                          "prompt": q, "source": src, "qid": r["id"],
                          "reference": ref, "fidelity": fid})
            i += 1
            taken += 1
    if i < 8:
        raise RuntimeError("class_c suite short: %d/8" % i)

    for n, r in enumerate(r for r in by_src.get("r2", [])
                          if r.get("split") == "val"):
        if n >= ELIG_N:
            break
        srow = raw.get(r.get("table", ""), r.get("row_id", ""))
        if not srow:
            continue
        elig = B.resolve(srow, "eligibility", cmap)
        suite.append({"pid": "el_%02d" % (n + 1), "group": "eligibility",
                      "prompt": r["messages"][0]["content"],
                      "expected": elig, "table": r.get("table", ""),
                      "row_id": r.get("row_id", ""), "qid": r["id"],
                      "fidelity": B.row_text(srow)})
    if sum(1 for p in suite if p["group"] == "eligibility") < ELIG_N:
        raise RuntimeError("eligibility suite short")

    for n, r in enumerate(r for r in by_src.get("r5", [])
                          if r.get("split") == "val"):
        if n >= REFUSE_N:
            break
        suite.append({"pid": "rf_%02d" % (n + 1), "group": "should_refuse",
                      "prompt": r["messages"][0]["content"],
                      "topic": r.get("topic", ""), "qid": r["id"]})
    if sum(1 for p in suite if p["group"] == "should_refuse") < REFUSE_N:
        raise RuntimeError("should_refuse suite short")

    for n, q in enumerate(GENERAL):
        suite.append({"pid": "ge_%02d" % (n + 1), "group": "general",
                      "prompt": q})
    return suite, raw


def is_refusal(text):
    return bool(B.REFUSAL_RE.match(text) or B.REF_MARK_RE.search(text))


def score(suite, raw):
    s = {"ExactMatch": {"n": 0, "hit": 0},
         "EligibilityVerbatim": {"n": 0, "hit": 0},
         "FieldFidelity": {"n": 0, "pass": 0, "nums": 0, "nums_ok": 0},
         "CitationResolution": {"prompts": 0, "cites": 0, "resolved": 0},
         "RefusalCorrect": {"should_refuse": {"n": 0, "ok": 0},
                            "should_answer": {"n": 0, "ok": 0}},
         "GeneralEnglish": {"n": 0, "on_task": 0}}
    ids = None
    for p in suite:
        out = p.get("output", "")
        g, o_n, fid_n = p["group"], norm(out), norm(p.get("fidelity", ""))
        if g == "exact_match":
            s["ExactMatch"]["n"] += 1
            if norm(p["expected"]) and norm(p["expected"]) in o_n:
                s["ExactMatch"]["hit"] += 1
        elif g == "eligibility":
            s["EligibilityVerbatim"]["n"] += 1
            if norm(p.get("expected", "")) and norm(p["expected"]) in o_n:
                s["EligibilityVerbatim"]["hit"] += 1
        if g in ("exact_match", "eligibility", "class_c"):
            f = s["FieldFidelity"]
            f["n"] += 1
            bad = False
            for num in B.NUM_RE.findall(out):
                nn = num.replace(",", "")
                if len(nn) < 3:
                    continue
                f["nums"] += 1
                if nn.lower() in fid_n or num.lower() in fid_n:
                    f["nums_ok"] += 1
                else:
                    bad = True
            if not bad:
                f["pass"] += 1
        cites = REF_CITE_RE.findall(out)
        if cites:
            if ids is None:
                ids = raw.ids_everywhere()
            c = s["CitationResolution"]
            c["prompts"] += 1
            for cid in cites:
                c["cites"] += 1
                if cid.strip() in ids:
                    c["resolved"] += 1
        if g == "should_refuse":
            rr = s["RefusalCorrect"]["should_refuse"]
            rr["n"] += 1
            if is_refusal(out):
                rr["ok"] += 1
        elif g in ("exact_match", "eligibility", "class_c", "general"):
            ra = s["RefusalCorrect"]["should_answer"]
            ra["n"] += 1
            if not is_refusal(out):
                ra["ok"] += 1
        if g == "general":
            ge = s["GeneralEnglish"]
            ge["n"] += 1
            if not is_refusal(out):
                ge["on_task"] += 1
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", default="",
                    help="optional LoRA dir (post-training rerun)")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()

    import torch
    import transformers

    t0 = time.time()
    suite, raw = build_suite()
    groups = {}
    for p in suite:
        groups[p["group"]] = groups.get(p["group"], 0) + 1
    print("suite      : %d prompts %s" % (len(suite), groups), flush=True)

    torch.manual_seed(SEED)
    tok = transformers.AutoTokenizer.from_pretrained(BASE, local_files_only=True)
    model = transformers.AutoModelForCausalLM.from_pretrained(
        BASE, torch_dtype=torch.bfloat16, local_files_only=True)
    if args.adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, args.adapter)
        print("adapter    : %s" % args.adapter, flush=True)
    model.to("cuda").eval()
    model.config.use_cache = True
    print("model      : %s | %s | seed=%d greedy max_new=%d"
          % (model.config._name_or_path, next(model.parameters()).dtype,
             SEED, MAX_NEW), flush=True)

    for n, p in enumerate(suite):
        prompt = p["prompt"]
        chat = tok.apply_chat_template([{"role": "user", "content": prompt}],
                                       tokenize=False, add_generation_prompt=True)
        enc = tok(chat, return_tensors="pt").to("cuda")
        torch.manual_seed(SEED)
        with torch.no_grad():
            gen = model.generate(
                **enc, max_new_tokens=MAX_NEW, do_sample=False,
                pad_token_id=tok.eos_token_id)
        p["output"] = tok.decode(gen[0][enc["input_ids"].shape[1]:],
                                 skip_special_tokens=True)
        print("[%2d/%d] %-10s %s -> %r"
              % (n + 1, len(suite), p["pid"], p["group"],
                 p["output"][:90]), flush=True)

    metrics = score(suite, raw)
    em = metrics["ExactMatch"]
    ff = metrics["FieldFidelity"]
    cr = metrics["CitationResolution"]
    rr = metrics["RefusalCorrect"]
    doc = {
        "suite": "p2-v1",
        "model": "Qwen2.5-7B-Instruct" + (" + %s" % args.adapter if args.adapter
                                          else ""),
        "base_dir": BASE,
        "adapter": args.adapter,
        "decoding": {"do_sample": False, "seed": SEED,
                     "max_new_tokens": MAX_NEW},
        "n_prompts": len(suite),
        "groups": groups,
        "metrics": metrics,
        "elapsed_s": round(time.time() - t0, 1),
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "prompts": suite,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    tmp = args.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, args.out)

    print("ExactMatch          : %d/%d" % (em["hit"], em["n"]))
    print("EligibilityVerbatim : %d/%d"
          % (metrics["EligibilityVerbatim"]["hit"],
             metrics["EligibilityVerbatim"]["n"]))
    print("FieldFidelity       : %d/%d prompts (%d/%d numbers)"
          % (ff["pass"], ff["n"], ff["nums_ok"], ff["nums"]))
    print("CitationResolution  : %d/%d cites resolved (%d prompts cited)"
          % (cr["resolved"], cr["cites"], cr["prompts"]))
    print("RefusalCorrect      : should-refuse %d/%d | should-answer %d/%d"
          % (rr["should_refuse"]["ok"], rr["should_refuse"]["n"],
             rr["should_answer"]["ok"], rr["should_answer"]["n"]))
    print("GeneralEnglish      : %d/%d on-task"
          % (metrics["GeneralEnglish"]["on_task"],
             metrics["GeneralEnglish"]["n"]))
    print("wrote %s (%d B)" % (args.out, os.path.getsize(args.out)))
    print("RESULT: P2_BASELINE_OK prompts=%d exact=%d/%d fidelity=%d/%d "
          "cites=%d/%d refuse=%d/%d answer_ok=%d/%d elapsed=%.0fs"
          % (len(suite), em["hit"], em["n"], ff["pass"], ff["n"],
             cr["resolved"], cr["cites"],
             rr["should_refuse"]["ok"], rr["should_refuse"]["n"],
             rr["should_answer"]["ok"], rr["should_answer"]["n"],
             doc["elapsed_s"]), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        print("RESULT: P2_BASELINE_FAIL %s" % sys.exc_info()[1], flush=True)
        sys.exit(1)
