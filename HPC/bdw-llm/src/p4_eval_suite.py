"""P4.5 - domain adapter evaluation harness (agreement vs golden facts).

Scores the five P4 LoRA adapters against the base model on the SAME live
llama-server (per-request lora activation), using 5 golden prompts per
domain. Every prompt carries the reference facts a correct answer must
reproduce (lower-case stems, substring match); a prompt score is the
fraction of reference facts present in the answer. The harness reports,
per domain:

  adapter_mean / base_mean   mean golden-fact agreement (0.0 .. 1.0)
  gain                       adapter_mean - base_mean
  wins/ties/losses           per-prompt comparison (tie: |delta| < 0.05)
  pairwise_jaccard           informational divergence vs base

Scoring is deterministic (temperature 0, keyword stems, no LLM judge) so
runs are reproducible and cheap; the prompt set is grounded in the same
Wikipedia corpora the adapters were SFT'd on (data/raw/p4_*_contexts.json
+ data/raw/vlsi_wikipedia.json), so a low score means the adapter did not
learn its corpus, not that the question was unfair.

Modes (same server, same sampling):
  adapter - /v1/chat/completions with request-scoped lora {id: N, scale}
            (ids resolved from GET /lora-adapters paths, never guessed)
  base    - identical request WITHOUT the lora field; run_stack.sh
            attaches adapters with --lora-init-without-apply so the
            global scale is 0 and this is the plain merged GGUF

Results stream to logs/p4_eval_<run>.jsonl (resume-safe: re-running with
the same --run-id skips completed (domain, mode, prompt) triples) and
aggregate to logs/p4_eval_<run>.json + logs/p4_eval_latest.json.

Usage:
  python src/p4_eval_suite.py --dry-run
  python src/p4_eval_suite.py --max-tokens 128
  python src/p4_eval_suite.py --domains math,vlsi --modes adapter,base

RESULT: P4_EVAL_<DOM>_OK adapter=.. base=.. gain=.. wins=../ties=../losses=..
RESULT: P4_EVAL_ALL_OK adapter=.. base=.. gain=.. wins=.. ties=.. losses=..
RESULT: P4_EVAL_FAIL <reason>
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

DEFAULT_BASE = "http://127.0.0.1:8081"
DOMAINS = ("math", "vlsi", "embedded", "cs", "aiml")
PASS_MIN = 0.60     # prompt "pass" = >= 60% of golden facts + all anchors
TIE_EPS = 0.05      # |adapter - base| below this counts as a tie

# ---------------------------------------------------------------------------
# Golden prompt set: 5 per domain. "expected" = reference fact stems
# (lower-case substrings; stems like "differenti" match all word forms).
# "must" = anchor terms a passing answer must contain (usually a subset).
# Prompts are bare domain questions -- the exact distribution the P4
# adapters were SFT'd on (question -> grounded answer, no retrieval).
# ---------------------------------------------------------------------------
PROMPTS = {
    "math": [
        {"id": "math-1",
         "q": "What does Bayes' theorem relate?",
         "expected": ["prior", "posterior", "likelihood"],
         "must": ["posterior"]},
        {"id": "math-2",
         "q": "What is an eigenvalue?",
         "expected": ["scalar", "eigenvector", "linear"],
         "must": []},
        {"id": "math-3",
         "q": "What is the derivative of sin x?",
         "expected": ["cos"],
         "must": ["cos"]},
        {"id": "math-4",
         "q": "What does the Laplace transform convert a function into?",
         "expected": ["complex", "frequency", "domain"],
         "must": ["complex"]},
        {"id": "math-5",
         "q": "What is numerical analysis concerned with?",
         "expected": ["approximat", "algorithm", "numerical"],
         "must": ["approximat"]},
    ],
    "vlsi": [
        {"id": "vlsi-1",
         "q": "What is setup time in a flip-flop?",
         "expected": ["before", "clock", "stable"],
         "must": ["before"]},
        {"id": "vlsi-2",
         "q": "What is hold time in a flip-flop?",
         "expected": ["after", "clock", "stable"],
         "must": ["after"]},
        {"id": "vlsi-3",
         "q": "What is static timing analysis used for?",
         "expected": ["timing", "simulat", "without"],
         "must": ["timing"]},
        {"id": "vlsi-4",
         "q": "What is metastability in digital circuits?",
         "expected": ["unstable", "indeterminate", "settle"],
         "must": ["settle"]},
        {"id": "vlsi-5",
         "q": "What does Verilog describe?",
         "expected": ["hardware", "circuit", "digital"],
         "must": ["hardware"]},
    ],
    "embedded": [
        {"id": "emb-1",
         "q": "What is the I2C bus used for?",
         "expected": ["peripheral", "serial", "bus"],
         "must": ["peripheral"]},
        {"id": "emb-2",
         "q": "What is an interrupt?",
         "expected": ["signal", "processor", "event"],
         "must": ["signal"]},
        {"id": "emb-3",
         "q": "What does a watchdog timer do?",
         "expected": ["reset", "timeout", "system"],
         "must": ["reset"]},
        {"id": "emb-4",
         "q": "What is direct memory access used for?",
         "expected": ["memory", "cpu", "peripheral"],
         "must": ["memory"]},
        {"id": "emb-5",
         "q": "What does a real-time operating system guarantee?",
         "expected": ["deadline", "deterministic", "real"],
         "must": ["deadline"]},
    ],
    "cs": [
        {"id": "cs-1",
         "q": "What is the time complexity of binary search?",
         "expected": ["log"],
         "must": ["log"]},
        {"id": "cs-2",
         "q": "What is a deadlock?",
         "expected": ["wait", "resource", "process"],
         "must": ["wait"]},
        {"id": "cs-3",
         "q": "What is virtual memory?",
         "expected": ["physical", "address", "memory"],
         "must": ["physical"]},
        {"id": "cs-4",
         "q": "What does a compiler do?",
         "expected": ["source", "machine", "translat"],
         "must": ["source"]},
        {"id": "cs-5",
         "q": "What is the difference between TCP and UDP?",
         "expected": ["reliable", "connection", "unreliable"],
         "must": ["reliable"]},
    ],
    "aiml": [
        {"id": "aiml-1",
         "q": "What is backpropagation used for?",
         "expected": ["gradient", "weight", "error"],
         "must": ["gradient"]},
        {"id": "aiml-2",
         "q": "How does the attention mechanism work?",
         "expected": ["weight", "query", "value"],
         "must": ["weight"]},
        {"id": "aiml-3",
         "q": "What is overfitting?",
         "expected": ["training", "generaliz", "memoriz"],
         "must": ["training"]},
        {"id": "aiml-4",
         "q": "What is stochastic gradient descent?",
         "expected": ["gradient", "random", "sample"],
         "must": ["gradient"]},
        {"id": "aiml-5",
         "q": "What is the purpose of a convolutional neural network?",
         "expected": ["image", "feature", "filter"],
         "must": ["feature"]},
    ],
}


# ---------------------------------------------------------------------------
# Rubric v2: fact groups (any accepted variant in a group = fact hit) plus
# misconception gates (a confidently wrong answer is zeroed). Variants were
# derived from the corpus lead sentences (src/lead_dump.py), NOT from model
# answers, and v2 is applied by rescoring the SAME saved answers offline --
# no model re-runs, so v1/v2 compare identical generations.
# ---------------------------------------------------------------------------
RUBRIC_V2 = {
    "math-1": {"facts": [["conditional"],
                         ["invers", "reverse", "prior", "posterior",
                          "likelihood", "cause", "effect"]],
               "wrong": []},
    "math-2": {"facts": [["scalar", "\u03bb", "lambda"], ["vector"],
                         ["matrix"], ["non-zero", "nonzero", "non zero"],
                         ["direction", "transformation", "eigen"]],
               "wrong": []},
    "math-3": {"facts": [["cos"]], "wrong": []},
    "math-4": {"facts": [["complex"], ["frequency"],
                         ["s-domain", "s domain", "s-plane", "domain"]],
               "wrong": []},
    "math-5": {"facts": [["algorithm"], ["approximat", "numeric"],
                         ["continuous", "analysis", "mathematic"]],
               "wrong": []},
    "vlsi-1": {"facts": [["before"], ["clock"],
                         ["stable", "valid", "settled", "available",
                          "present"]],
               "wrong": []},
    "vlsi-2": {"facts": [["after"], ["clock"],
                         ["stable", "held", "valid", "sampled"]],
               "wrong": []},
    "vlsi-3": {"facts": [["delay"], ["clock", "cycle", "path", "timing"],
                         ["verif", "check", "ensur", "sign-off", "analyz",
                          "measur"]],
               "wrong": ["execution time"]},
    "vlsi-4": {"facts": [["metastab", "intermediate", "neither",
                          "forbidden", "unstable"],
                         ["settl"],
                         ["fault", "undefined", "uncertain", "indefinite",
                          "glitch"]],
               "wrong": []},
    "vlsi-5": {"facts": [["hardware description", "hdl"],
                         ["model", "describe", "design"],
                         ["digital", "electronic", "circuit"]],
               "wrong": ["algorithm"]},
    "emb-1": {"facts": [["serial"], ["bus"],
                        ["peripheral", "device", "ic", "sensor"],
                        ["microcontroller", "processor", "master", "slave"]],
              "wrong": []},
    "emb-2": {"facts": [["signal", "request"],
                        ["processor", "cpu", "computer"],
                        ["event", "attention", "timely"],
                        ["handler", "isr", "service routine", "suspend",
                         "save", "function"]],
              "wrong": []},
    "emb-3": {"facts": [["monitor", "detect", "watch"],
                        ["malfunction", "fault", "failure", "responsive",
                         "recover", "reset", "timeout"]],
              "wrong": []},
    "emb-4": {"facts": [["memory"], ["cpu", "processor"],
                        ["peripheral", "device", "transfer"]],
              "wrong": []},
    "emb-5": {"facts": [["time", "deadline", "constraint"],
                        ["guarantee", "deterministic", "real-time"],
                        ["task", "event", "process", "response"]],
              "wrong": []},
    "cs-1": {"facts": [["log"]], "wrong": []},
    "cs-2": {"facts": [["wait"], ["resource", "lock"],
                       ["process", "thread"]],
             "wrong": []},
    "cs-3": {"facts": [["physical", "physically"], ["address"],
                       ["abstract", "more memory", "appear", "swap",
                        "paging", "disk"]],
             "wrong": []},
    "cs-4": {"facts": [["translat", "convert"], ["source"],
                       ["machine", "object code", "target", "low-level",
                        "intermediate"]],
             "wrong": []},
    "cs-5": {"facts": [["reliable"],
                       ["unreliable", "does not guarantee", "no guarantee",
                        "connectionless"],
                       ["connection", "handshake"]],
             "wrong": []},
    "aiml-1": {"facts": [["gradient"], ["weight", "parameter"],
                         ["loss", "error", "chain rule", "derivative"]],
               "wrong": []},
    "aiml-2": {"facts": [["weight"], ["query", "key", "value"],
                         ["relevance", "importance", "similarity", "score",
                          "attend"]],
               "wrong": []},
    "aiml-3": {"facts": [["training"],
                         ["generaliz", "new data", "unseen", "future",
                          "additional"],
                         ["memoriz", "noise", "too closely", "exactly",
                          "overfit"]],
               "wrong": []},
    "aiml-4": {"facts": [["gradient"],
                         ["random", "single", "subset", "noisy", "estimate",
                          "mini-batch", "stochastic"],
                         ["update", "optimiz", "iterative", "step"]],
               "wrong": []},
    "aiml-5": {"facts": [["feature", "filter", "kernel"],
                         ["image", "vision", "spatial", "data"],
                         ["learn", "extract", "process", "predict"]],
               "wrong": []},
}


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def normalize(text):
    out = str(text or "").lower()
    out = out.replace("\u2013", "-").replace("\u2014", "-")
    out = out.replace("\u2019", "'").replace("\u201c", '"') \
             .replace("\u201d", '"')
    return re.sub(r"\s+", " ", out).strip()


def score_answer(answer, prompt):
    """(frac, hits, missing, passed) for one answer against one prompt."""
    a = normalize(answer)
    expected = prompt["expected"]
    hits = [e for e in expected if e in a]
    missing = [e for e in expected if e not in a]
    frac = (len(hits) / len(expected)) if expected else 0.0
    anchors_ok = all(m in a for m in prompt.get("must") or [])
    passed = frac >= PASS_MIN and anchors_ok
    return round(frac, 4), hits, missing, bool(passed)


def score_answer_v2(answer, prompt_id):
    """Rubric v2: fact groups + misconception gate.

    Returns (frac, hit_groups, missing_groups, passed, wrong_hit)."""
    rubric = RUBRIC_V2[prompt_id]
    a = normalize(answer)
    hit, miss = [], []
    for i, group in enumerate(rubric["facts"]):
        (hit if any(v in a for v in group) else miss).append(i)
    frac = len(hit) / len(rubric["facts"])
    wrong_hit = next((w for w in rubric["wrong"] if w in a), None)
    if wrong_hit:
        frac = 0.0
    return (round(frac, 4), hit, miss, frac >= PASS_MIN, wrong_hit)


def jaccard(a, b):
    ta = set(re.findall(r"[a-z0-9]+", normalize(a)))
    tb = set(re.findall(r"[a-z0-9]+", normalize(b)))
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    return round(len(ta & tb) / len(ta | tb), 4)


def summarize(done, domains, modes):
    """Aggregate per-domain metrics from scored records."""
    summary = {}
    for d in domains:
        per_mode = {m: [done[(d, m, p["id"])] for p in PROMPTS[d]]
                    for m in modes}
        row = {"prompts": len(PROMPTS[d])}
        for m in modes:
            recs = per_mode[m]
            row[m + "_mean"] = round(
                sum(r["frac"] for r in recs) / len(recs), 4)
            row[m + "_pass"] = round(
                sum(1 for r in recs if r["passed"]) / len(recs), 4)
        if "adapter" in modes and "base" in modes:
            a, b = per_mode["adapter"], per_mode["base"]
            row["gain"] = round(row["adapter_mean"] - row["base_mean"], 4)
            row["wins"] = sum(1 for x, y in zip(a, b)
                              if x["frac"] > y["frac"] + TIE_EPS)
            row["losses"] = sum(1 for x, y in zip(a, b)
                                if y["frac"] > x["frac"] + TIE_EPS)
            row["ties"] = len(a) - row["wins"] - row["losses"]
            row["pairwise_jaccard"] = round(
                sum(jaccard(x["answer"], y["answer"])
                    for x, y in zip(a, b)) / len(a), 4)
        summary[d] = row
    totals = {}
    if "adapter" in modes and "base" in modes:
        n = sum(summary[d]["prompts"] for d in domains)
        totals["prompts"] = n
        for m in modes:
            totals[m + "_mean"] = round(
                sum(summary[d][m + "_mean"] * summary[d]["prompts"]
                    for d in domains) / n, 4)
        totals["gain"] = round(totals["adapter_mean"]
                               - totals["base_mean"], 4)
        totals["wins"] = sum(summary[d]["wins"] for d in domains)
        totals["ties"] = sum(summary[d]["ties"] for d in domains)
        totals["losses"] = sum(summary[d]["losses"] for d in domains)
    return summary, totals


def print_table(summary, totals, domains, modes, prefix="P4_EVAL"):
    print("")
    if "adapter" in modes and "base" in modes:
        print("%-9s %8s %8s %8s %6s %6s %6s %8s"
              % ("domain", "adapter", "base", "gain",
                 "wins", "ties", "losses", "jaccard"))
        for d in domains:
            r = summary[d]
            print("%-9s %8.3f %8.3f %+8.3f %6d %6d %6d %8.3f"
                  % (d, r["adapter_mean"], r["base_mean"], r["gain"],
                     r["wins"], r["ties"], r["losses"],
                     r["pairwise_jaccard"]))
            print("RESULT: %s_%s_OK adapter=%.3f base=%.3f gain=%+.3f "
                  "wins=%d ties=%d losses=%d pass_a=%.2f pass_b=%.2f"
                  % (prefix, d.upper(), r["adapter_mean"], r["base_mean"],
                     r["gain"], r["wins"], r["ties"], r["losses"],
                     r["adapter_pass"], r["base_pass"]))
        print("%-9s %8.3f %8.3f %+8.3f %6d %6d %6d"
              % ("ALL", totals["adapter_mean"], totals["base_mean"],
                 totals["gain"], totals["wins"], totals["ties"],
                 totals["losses"]))
        print("RESULT: %s_ALL_OK adapter=%.3f base=%.3f gain=%+.3f "
              "wins=%d ties=%d losses=%d prompts=%d"
              % (prefix, totals["adapter_mean"], totals["base_mean"],
                 totals["gain"], totals["wins"], totals["ties"],
                 totals["losses"], totals["prompts"]))
    else:
        m = modes[0]
        for d in domains:
            r = summary[d]
            print("%-9s %-8s mean=%.3f pass=%.2f"
                  % (d, m, r[m + "_mean"], r[m + "_pass"]))
            print("RESULT: %s_%s_OK %s=%.3f pass=%.2f"
                  % (prefix, d.upper(), m, r[m + "_mean"], r[m + "_pass"]))
        print("RESULT: %s_ALL_OK mode=%s" % (prefix, m))


# ---------------------------------------------------------------------------
# llama-server client
# ---------------------------------------------------------------------------

def http_json(method, url, payload=None, timeout=600, tries=3):
    import requests
    last = None
    for attempt in range(tries):
        try:
            r = requests.request(method, url, json=payload, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001
            last = e
            if attempt < tries - 1:
                time.sleep(2 + attempt * 3)
    raise RuntimeError("%s %s failed: %s" % (method, url, last))


def lora_map(base_url):
    """{"math": id, ...} from GET /lora-adapters paths."""
    items = http_json("GET", base_url + "/lora-adapters", timeout=30)
    out = {}
    for it in items:
        m = re.search(r"p4_lora_(%s)\.gguf$" % "|".join(DOMAINS),
                      os.path.basename(it.get("path") or ""))
        if m:
            out[m.group(1)] = int(it["id"])
    return out


def ask(base_url, question, max_tokens, timeout, lora_id=None):
    body = {"messages": [{"role": "user", "content": question}],
            "max_tokens": int(max_tokens), "temperature": 0.0,
            "stream": False}
    if lora_id is not None:
        body["lora"] = [{"id": int(lora_id), "scale": 1.0}]
    t0 = time.time()
    data = http_json("POST", base_url + "/v1/chat/completions", body,
                     timeout=timeout)
    elapsed = round(time.time() - t0, 2)
    try:
        answer = data["choices"][0]["message"].get("content") or ""
    except (KeyError, IndexError, TypeError):
        raise RuntimeError("no chat content: %s" % str(data)[:160])
    usage = data.get("usage") or {}
    return answer.strip(), elapsed, usage


# ---------------------------------------------------------------------------
# Harness
# ---------------------------------------------------------------------------

def load_done(path):
    done = {}
    if not os.path.isfile(path):
        return done
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:  # noqa: BLE001
                continue
            done[(r["domain"], r["mode"], r["prompt_id"])] = r
    return done


def run(args):
    base_url = args.base_url.rstrip("/")
    domains = [d.strip() for d in args.domains.split(",") if d.strip()]
    modes = [m.strip() for m in args.modes.split(",") if m.strip()]
    for d in domains:
        if d not in PROMPTS:
            print("RESULT: P4_EVAL_FAIL unknown domain %r" % d)
            return 1
    for m in modes:
        if m not in ("adapter", "base"):
            print("RESULT: P4_EVAL_FAIL unknown mode %r" % m)
            return 1

    if args.dry_run:
        total = 0
        for d in domains:
            for p in PROMPTS[d]:
                total += 1
                print("%-9s %-8s %s" % (d, p["id"], p["q"]))
                print("          expected=%s must=%s"
                      % (p["expected"], p["must"]))
        print("prompts=%d domains=%s modes=%s calls=%d"
              % (total, ",".join(domains), ",".join(modes),
                 total * len(modes)))
        try:
            lm = lora_map(base_url)
            print("lora_adapters=%s"
                  % (",".join("%s:%d" % (k, v)
                              for k, v in sorted(lm.items())) or "none"))
        except Exception as e:  # noqa: BLE001
            print("lora_adapters=unreachable (%s)" % e)
        print("RESULT: P4_EVAL_DRYRUN_OK prompts=%d" % total)
        return 0

    # adapter ids must resolve before any call: never score a mislabelled run
    lm = lora_map(base_url)
    if "adapter" in modes:
        missing = [d for d in domains if d not in lm]
        if missing:
            print("RESULT: P4_EVAL_FAIL adapters not attached for %s "
                  "(P4_ADAPTERS=all run_stack.sh); attached=%s"
                  % (",".join(missing), lm))
            return 1

    os.makedirs(args.out_dir, exist_ok=True)
    run_id = args.run_id or time.strftime("%Y%m%d_%H%M%S")
    jsonl = os.path.join(args.out_dir, "p4_eval_%s.jsonl" % run_id)
    done = load_done(jsonl)
    print("run_id     : %s" % run_id)
    print("base_url   : %s" % base_url)
    print("adapters   : %s" % ", ".join("%s:%d" % (k, v)
                                        for k, v in sorted(lm.items())))
    print("modes      : %s  domains: %s" % (",".join(modes),
                                            ",".join(domains)))
    print("resume     : %d completed triples" % len(done))

    with open(jsonl, "a", encoding="utf-8") as fh:
        for d in domains:
            for mode in modes:
                for p in PROMPTS[d]:
                    key = (d, mode, p["id"])
                    if key in done:
                        continue
                    lid = lm.get(d) if mode == "adapter" else None
                    try:
                        answer, elapsed, usage = ask(
                            base_url, p["q"], args.max_tokens,
                            args.timeout, lora_id=lid)
                    except Exception as e:  # noqa: BLE001
                        print("RESULT: P4_EVAL_FAIL %s/%s/%s: %s"
                              % (d, mode, p["id"], e))
                        return 1
                    frac, hits, missing, passed = score_answer(answer, p)
                    rec = {"domain": d, "mode": mode, "prompt_id": p["id"],
                           "question": p["q"], "answer": answer,
                           "lora_id": lid, "frac": frac, "hits": hits,
                           "missing": missing, "passed": passed,
                           "elapsed_s": elapsed,
                           "completion_tokens":
                               (usage or {}).get("completion_tokens")}
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    fh.flush()
                    done[key] = rec
                    print("  %-9s %-7s %-7s frac=%.2f %s (%.0fs)"
                          % (d, mode, p["id"], frac,
                             "PASS" if passed else "....", elapsed),
                          flush=True)

    # ---- aggregate -----------------------------------------------------
    summary, totals = summarize(done, domains, modes)
    agg = {"run_id": run_id, "base_url": base_url, "modes": modes,
           "max_tokens": args.max_tokens, "pass_min": PASS_MIN,
           "tie_eps": TIE_EPS, "adapters": lm, "domains": summary,
           "totals": totals}
    out_json = os.path.join(args.out_dir, "p4_eval_%s.json" % run_id)
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(agg, fh, ensure_ascii=False, indent=1)
    latest = os.path.join(args.out_dir, "p4_eval_latest.json")
    with open(latest, "w", encoding="utf-8") as fh:
        json.dump(agg, fh, ensure_ascii=False, indent=1)

    print_table(summary, totals, domains, modes)
    print("artifacts  : %s" % out_json)
    return 0


def rescore(args):
    """Apply rubric v2 to a finished JSONL (no model calls)."""
    path = args.rescore
    if not os.path.isfile(path):
        print("RESULT: P4_EVAL_FAIL no such jsonl %s" % path)
        return 1
    done_v1 = load_done(path)
    if not done_v1:
        print("RESULT: P4_EVAL_FAIL empty jsonl %s" % path)
        return 1
    domains = [d for d in DOMAINS
               if any(k[0] == d for k in done_v1)]
    modes = [m for m in ("adapter", "base")
             if any(k[1] == m for k in done_v1)]
    done = {}
    v1 = {}
    for key, r in done_v1.items():
        frac2, hit, miss, passed2, wrong = score_answer_v2(
            r["answer"], r["prompt_id"])
        rec = dict(r)
        rec["frac_v1"] = r["frac"]
        rec["passed_v1"] = r["passed"]
        rec["frac"] = frac2
        rec["passed"] = passed2
        rec["hit_groups"] = hit
        rec["missing_groups"] = miss
        rec["wrong_hit"] = wrong
        done[key] = rec
        old = dict(r)
        old["frac"] = r["frac"]
        old["passed"] = r["passed"]
        v1[key] = old
    summary, totals = summarize(done, domains, modes)
    summary_v1, totals_v1 = summarize(v1, domains, modes)

    print("rubric     : v2 (fact groups + misconception gate)")
    print("%-8s %-7s %5s %5s %5s %5s  %s"
          % ("domain", "prompt", "v1_a", "v2_a", "v1_b", "v2_b", "wrong"))
    for d in domains:
        for p in PROMPTS[d]:
            a = done.get((d, "adapter", p["id"]))
            b = done.get((d, "base", p["id"]))
            if not a or not b:
                continue
            w = a["wrong_hit"] or b["wrong_hit"] or ""
            print("%-8s %-7s %5.2f %5.2f %5.2f %5.2f  %s"
                  % (d, p["id"], a["frac_v1"], a["frac"],
                     b["frac_v1"], b["frac"], w))
            if a["wrong_hit"]:
                print("RESULT: P4_EVAL_V2_WRONG %s/adapter/%s matched=%r"
                      % (d, p["id"], a["wrong_hit"]))
            if b["wrong_hit"]:
                print("RESULT: P4_EVAL_V2_WRONG %s/base/%s matched=%r"
                      % (d, p["id"], b["wrong_hit"]))

    run_id = os.path.basename(path).replace("p4_eval_", "") \
                                 .replace(".jsonl", "")
    agg = {"run_id": run_id, "source": path, "rubric": "v2",
           "pass_min": PASS_MIN, "tie_eps": TIE_EPS,
           "v1": {"domains": summary_v1, "totals": totals_v1},
           "v2": {"domains": summary, "totals": totals},
           "records": [done[k] for k in sorted(done)]}
    out = os.path.join(args.out_dir, "p4_eval_%s_v2.json" % run_id)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(agg, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(args.out_dir, "p4_eval_latest_v2.json"),
              "w", encoding="utf-8") as fh:
        json.dump(agg, fh, ensure_ascii=False, indent=1)

    print_table(summary, totals, domains, modes, prefix="P4_EVAL_V2")
    print("v1_totals  : adapter=%.3f base=%.3f gain=%+.3f"
          % (totals_v1["adapter_mean"], totals_v1["base_mean"],
             totals_v1["gain"]))
    print("artifacts  : %s" % out)
    return 0


def main():
    ap = argparse.ArgumentParser(description="P4.5 adapter eval harness")
    ap.add_argument("--base-url", default=DEFAULT_BASE)
    ap.add_argument("--domains", default=",".join(DOMAINS))
    ap.add_argument("--modes", default="adapter,base")
    ap.add_argument("--max-tokens", type=int, default=128)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--out-dir", default=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"))
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--rescore", default=None,
                    help="JSONL from a finished run; applies rubric v2 "
                         "offline (no model calls)")
    args = ap.parse_args()
    try:
        return rescore(args) if args.rescore else run(args)
    except KeyboardInterrupt:
        print("RESULT: P4_EVAL_FAIL interrupted")
        return 130
    except Exception as e:  # noqa: BLE001
        import traceback
        traceback.print_exc()
        print("RESULT: P4_EVAL_FAIL %s" % e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
