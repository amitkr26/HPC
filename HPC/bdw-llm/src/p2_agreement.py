"""P2.5: top-1 agreement report, merged bf16 vs Q4_K_M GGUF (blueprint S8.3).

Method (Phase-0 export_test.py metric, re-pointed at the quantisation pair):
for each prompt of the frozen suite p2-v2 the MERGED bf16 model answers
greedily; the full token-id sequence (chat-prompt ids + answer ids) is handed
to the llama.cpp tool `top1agree`, which -- given ids[0..i-1] -- reports its
argmax token and we compare it to the bf16 token ids[i].  One llama_decode per
prompt, every answer position evaluated (teacher-forced), so the number is a
true next-token agreement rate and not a decode-path artefact.

S8.3 rule: if agreement is poor, serve bf16.  Verdict thresholds (documented
up-front, not fitted after the fact):
    rate >= 0.90            PASS          -> Q4_K_M is a safe serving target
    0.85 <= rate < 0.90     MARGINAL      -> prefer bf16 for fidelity-critical
    rate <  0.85            POOR          -> serve bf16 (quant off the table)

Also re-scores the merged bf16 answers with the exact p2-baseline gate code
(merged weights must reproduce the SFT-v2 gates) and counts pid-by-pid string
equality against eval/p2_sft_v2.json (base+adapter) -- a merge-correctness
check folded into the same pass.

Resumable: generation writes eval/p2_agreement_ids.tsv +
eval/p2_agreement_gen.jsonl atomically; a re-run without --force reuses them
(only the llama.cpp pass and aggregation repeat).

RESULT: P2_AGREEMENT_OK prompts=.. positions=.. rate=.. identical=..
        verdict=.. /  RESULT: P2_AGREEMENT_FAIL ...
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import traceback

SRC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SRC)
import p2_baseline as PB  # noqa: E402  build_suite + score (import-safe)

ROOT = os.path.expanduser("~/bdw-llm")
MERGED = os.path.join(ROOT, "merged/bdw-7b-sft")
GGUF_Q4 = os.path.join(ROOT, "merged/bdw-7b-sft-Q4_K_M.gguf")
TOP1 = os.path.join(ROOT, "llama_cpp/build/bin/top1agree")
IDS = os.path.join(ROOT, "eval/p2_agreement_ids.tsv")
GEN = os.path.join(ROOT, "eval/p2_agreement_gen.jsonl")
AGREE = os.path.join(ROOT, "eval/p2_agreement_top1.tsv")
OUT = os.path.join(ROOT, "eval/p2_agreement.json")
SFTV2 = os.path.join(ROOT, "eval/p2_sft_v2.json")

SEED = 1337
MAX_NEW = 300
LLAMA_CPP_COMMIT = "d854d98bae598388ecea1ed84396587e5edc326d"


def atomic_write_text(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)


def atomic_write_json(path, obj):
    atomic_write_text(path, json.dumps(obj, ensure_ascii=False, indent=1))


def md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def generate(suite, force):
    """Greedy merged-bf16 trajectories -> ids.tsv + gen.jsonl (resumable)."""
    if not force and os.path.exists(IDS) and os.path.exists(GEN):
        with open(GEN, encoding="utf-8") as fh:
            outputs = {r["pid"]: r["output"] for r in map(json.loads, fh)}
        print("reuse     : %s (%d gens)" % (GEN, len(outputs)), flush=True)
        return outputs

    import torch
    import transformers

    tok = transformers.AutoTokenizer.from_pretrained(MERGED,
                                                      local_files_only=True)
    model = transformers.AutoModelForCausalLM.from_pretrained(
        MERGED, torch_dtype=torch.bfloat16, local_files_only=True)
    model.to("cuda").eval()
    model.config.use_cache = True
    print("model     : %s | %s | greedy seed=%d max_new=%d"
          % (MERGED, next(model.parameters()).dtype, SEED, MAX_NEW), flush=True)

    tsv_rows = []
    outputs = {}
    for n, p in enumerate(suite):
        chat = tok.apply_chat_template(
            [{"role": "user", "content": p["prompt"]}],
            tokenize=False, add_generation_prompt=True)
        enc = tok(chat, return_tensors="pt").to("cuda")
        torch.manual_seed(SEED)
        with torch.no_grad():
            gen = model.generate(**enc, max_new_tokens=MAX_NEW,
                                 do_sample=False, pad_token_id=tok.eos_token_id)
        prompt_len = enc["input_ids"].shape[1]
        ids = gen[0].tolist()
        assert ids[:prompt_len] == enc["input_ids"][0].tolist()
        tsv_rows.append("%s\t%d\t%s"
                        % (p["pid"], prompt_len,
                           " ".join(str(t) for t in ids)))
        outputs[p["pid"]] = tok.decode(ids[prompt_len:],
                                       skip_special_tokens=True)
        print("[%2d/%d] %-10s %r"
              % (n + 1, len(suite), p["pid"], outputs[p["pid"]][:70]),
              flush=True)

    atomic_write_text(IDS, "\n".join(tsv_rows) + "\n")
    atomic_write_text(GEN, "".join(json.dumps({"pid": k, "output": v},
                                              ensure_ascii=False) + "\n"
                                   for k, v in outputs.items()))
    print("wrote %s (%d B) + %s (%d B)"
          % (IDS, os.path.getsize(IDS), GEN, os.path.getsize(GEN)),
          flush=True)
    return outputs


def run_top1():
    if not os.path.exists(TOP1):
        raise RuntimeError("top1agree binary missing: %s" % TOP1)
    if not os.path.exists(GGUF_Q4):
        raise RuntimeError("Q4_K_M gguf missing: %s" % GGUF_Q4)
    cmd = [TOP1, "--model", GGUF_Q4, "--input", IDS, "--output", AGREE,
           "--threads", "4", "--ctx", "2048"]
    t0 = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
    sys.stdout.write(res.stdout)
    sys.stderr.write(res.stderr)
    if res.returncode != 0:
        raise RuntimeError("top1agree rc=%d" % res.returncode)
    print("top1agree : %.1fs" % (time.time() - t0), flush=True)
    return " ".join(res.stdout.split())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--force", action="store_true",
                    help="regenerate trajectories even if cached")
    args = ap.parse_args()

    t0 = time.time()
    suite, raw = PB.build_suite()
    groups = {}
    for p in suite:
        groups[p["group"]] = groups.get(p["group"], 0) + 1
    print("suite      : %d prompts %s" % (len(suite), groups), flush=True)

    outputs = generate(suite, args.force)
    for p in suite:
        p["output"] = outputs[p["pid"]]

    summary = run_top1()

    rows = []
    with open(AGREE, encoding="utf-8") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 4:
                continue
            pid, agree, total, first = parts
            rows.append({"pid": pid, "agree": int(agree),
                         "total": int(total), "first_div": int(first)})
    if not rows:
        raise RuntimeError("no rows parsed from %s" % AGREE)

    valid = [r for r in rows if r["first_div"] >= -1]
    positions = sum(r["total"] for r in valid)
    agree_n = sum(r["agree"] for r in valid)
    identical = sum(1 for r in valid if r["first_div"] == -1)
    errors = [r for r in rows if r["first_div"] <= -3]
    rate = agree_n / positions if positions else 0.0
    verdict = ("PASS_SERVE_Q4" if rate >= 0.90 else
               "MARGINAL_PREFER_BF16" if rate >= 0.85 else
               "POOR_SERVE_BF16")

    merged_gates = PB.score(suite, raw)

    merged_match = None
    if os.path.exists(SFTV2):
        with open(SFTV2, encoding="utf-8") as fh:
            prev = json.load(fh)
        ref = {p["pid"]: p.get("output", "") for p in prev.get("prompts", [])}
        merged_match = sum(1 for p in suite
                           if ref.get(p["pid"]) == p.get("output"))

    doc = {
        "suite": "p2-v2",
        "method": ("teacher-forced top-1 agreement: llama.cpp argmax vs "
                   "merged-bf16 greedy token at every answer position "
                   "(teacher-forced, not decode-path)"),
        "pair": {"a": "merged/bdw-7b-sft (bf16, transformers)",
                 "b": "merged/bdw-7b-sft-Q4_K_M.gguf (llama.cpp)"},
        "llama_cpp_commit": LLAMA_CPP_COMMIT,
        "gguf": {"path": GGUF_Q4, "bytes": os.path.getsize(GGUF_Q4),
                 "md5": md5_file(GGUF_Q4)},
        "n_prompts": len(rows),
        "positions": positions,
        "agree": agree_n,
        "rate": round(rate, 6),
        "identical_prompts": identical,
        "decode_errors": len(errors),
        "thresholds": {"pass": 0.90, "marginal": 0.85},
        "verdict": verdict,
        "tool_summary": summary,
        "per_prompt": rows,
        "merged_gates": merged_gates,
        "merged_equals_sft_v2_outputs": merged_match,
        "elapsed_s": round(time.time() - t0, 1),
        "top1_tool": TOP1,
    }
    atomic_write_json(args.out, doc)

    print("positions  : %d across %d prompts" % (positions, len(rows)))
    print("agreement  : %d/%d = %.4f  identical_trajectories=%d"
          % (agree_n, positions, rate, identical))
    print("verdict    : %s  (thresholds: PASS>=0.90 MARGINAL>=0.85)" % verdict)
    em = merged_gates["ExactMatch"]
    cr = merged_gates["CitationResolution"]
    rr = merged_gates["RefusalCorrect"]
    print("merged gates: EM %d/%d | cites %d/%d | refuse %d/%d | "
          "answer_ok %d/%d | equals_sft_v2=%s"
          % (em["hit"], em["n"], cr["resolved"], cr["cites"],
             rr["should_refuse"]["ok"], rr["should_refuse"]["n"],
             rr["should_answer"]["ok"], rr["should_answer"]["n"],
             merged_match))
    print("wrote %s (%d B)" % (args.out, os.path.getsize(args.out)))
    print("RESULT: P2_AGREEMENT_OK prompts=%d positions=%d rate=%.4f "
          "identical=%d verdict=%s equals_sft_v2=%s elapsed=%.0fs"
          % (len(rows), positions, rate, identical, verdict, merged_match,
             doc["elapsed_s"]), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        print("RESULT: P2_AGREEMENT_FAIL %s" % sys.exc_info()[1], flush=True)
        sys.exit(1)
