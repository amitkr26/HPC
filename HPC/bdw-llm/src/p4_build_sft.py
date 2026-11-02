"""P4.2 - build the per-domain TRL SFT dataset (login node, deterministic).

Consumes the P4.1 teacher QA (data/p4/qa/<domain>_qa.jsonl) and, for vlsi,
may also fold in the proven Stage O.3a grounded rows (data/grounded_qa.jsonl,
same corpus provenance -- teacher-written from vlsi_wikipedia.json chunks).

Guarantees:
  * every emitted answer ends in terminal punctuation and carries no refusal,
    Human:/Assistant: leak, or meta-reference phrasing, with >=4-word
    questions and >=5-word answers (the exact Stage O.3a pair gate the
    0.9682-agreement model was trained through -- short factual answers are
    valid teaching rows); the gate is re-applied here so it holds regardless
    of which source contributed rows;
  * rows are deduped on the exact (question, response) pair;
  * deterministic split: md5(qid) oddity -- md5(qid) as int % 20 == 0 means
    val, everything else train; the val set is grown to >= --min-val rows by
    taking the lowest-hash train rows so a small dataset still yields a
    usable eval split;
  * rows beyond --max-train train rows are dropped lowest-hash-first
    (deterministic, no sampling);
  * output row schema is byte-compatible with the P2 SFT data
    ({"id", "messages", "source", "split", "row_id", "tokens"}), so
    p4_lora_sft.py loads it exactly like p2_sft.py loads bdw_sft.jsonl;
  * "tokens" is the chat-template-templated token length (teacher tokenizer
    preflight; rows above P4_MAX_TOKENS are dropped, never truncated).

RESULT: P4_SFTDATA_<DOMAIN>_OK train=.. val=.. | P4_SFTDATA_<DOMAIN>_FAIL ...
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p4_domain_lib as P4  # noqa: E402

P4_MAX_TOKENS = 1024

ENDSENT = tuple(".!?:)\"'\u201d")
REFUSAL_RE = re.compile(
    r"^(?:as an ai|i'?m sorry|i am sorry|i cannot|sorry,)", re.I)
LEAK_RE = re.compile(r"\bHuman\s*:|\bAssistant\s*:")
META_REF_RE = re.compile(
    r"\b(?:the given|the provided|the above|the following|the attached|"
    r"the passage|this passage|the text above|the text below|the provided "
    r"text|the given text)\b", re.I)

SOURCE_NEW = "p4"          # rows straight from P4.1
SOURCE_GROUNDED = "p4g"    # rows reused from Stage O.3a grounded_qa.jsonl


def gate(question: str, response: str):
    """House O.3a pair contract (the exact criteria Stage O.3a kept with a
    0.9682-agreement model): >=4-word question, >=5-word complete-sentence
    answer, no refusal, no Human:/Assistant: leak, no meta reference.
    Short factual answers are valid teaching rows. Returns the cleaned
    pair or None."""
    q = " ".join((question or "").split())
    resp = " ".join((response or "").split())
    if not q or not resp:
        return None
    if len(q.split()) < 4 or len(resp.split()) < 5:
        return None
    if resp[-1] not in ENDSENT:
        return None
    if REFUSAL_RE.match(resp) or LEAK_RE.search(resp) \
            or META_REF_RE.search(resp):
        return None
    return q, resp


def main():
    ap = argparse.ArgumentParser(description="P4.2 domain SFT dataset build")
    ap.add_argument("--domain", required=True,
                    help="math|vlsi|embedded|cs|aiml")
    ap.add_argument("--max-train", type=int, default=800)
    ap.add_argument("--min-val", type=int, default=8)
    ap.add_argument("--merge-grounded", action="store_true", default=None,
                    help="also fold in data/grounded_qa.jsonl (default: on "
                         "for vlsi, off for the rest)")
    args = ap.parse_args()
    try:
        domain = P4.check(args.domain)
    except ValueError as e:
        print("RESULT: P4_SFTDATA_FAIL %s" % e)
        return 2
    dom = domain.upper()

    merge_ground = args.merge_grounded
    if merge_ground is None:
        merge_ground = (domain == "vlsi")

    qa_path = P4.qa_path(domain)
    grounded = os.path.join(P4.ROOT, "data/grounded_qa.jsonl")
    if os.path.isfile(qa_path):
        srcs = [(SOURCE_NEW, qa_path)]
        if merge_ground and os.path.isfile(grounded):
            srcs.append((SOURCE_GROUNDED, grounded))
        else:
            grounded = None
    elif merge_ground and os.path.isfile(grounded):
        # vlsi reuse path: Stage O.3a grounded rows are the sole source
        srcs = [(SOURCE_GROUNDED, grounded)]
        qa_path = None
    else:
        print("RESULT: P4_SFTDATA_%s_FAIL no QA file %s -- run "
              "scripts/p4_domain_gen.slurm (P4.1) first" % (dom, qa_path))
        return 1

    print("domain     : %s" % domain)
    print("sources    : %s" % ", ".join("%s=%s" % (s, p) for s, p in srcs))

    # ---- teacher tokenizer preflight -----------------------------------
    import transformers
    try:
        tok = transformers.AutoTokenizer.from_pretrained(
            P4.teacher_dir(), local_files_only=True)
    except Exception as e:
        print("RESULT: P4_SFTDATA_%s_FAIL tokenizer: %s" % (dom, e))
        return 1

    rows = {}
    stats = {"raw": 0, "dup": 0, "failed_gate": 0, "too_long": 0}
    stats["by_source"] = {}
    for source, path in srcs:
        seen_src = stats["by_source"].setdefault(source, {"in": 0, "out": 0})
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if r.get("valid") is False:
                    continue
                q = r.get("question")
                resp = r.get("response") or r.get("answer")
                if not q or not resp:
                    continue
                stats["raw"] += 1
                seen_src["in"] += 1
                gated = gate(q, resp)
                if gated is None:
                    stats["failed_gate"] += 1
                    continue
                q, resp = gated
                key = (q.lower(), resp.lower())
                if key in rows:
                    stats["dup"] += 1
                    continue
                messages = [{"role": "user", "content": q},
                            {"role": "assistant", "content": resp}]
                ids = tok.apply_chat_template(messages)
                if not ids or len(ids) > P4_MAX_TOKENS:
                    stats["too_long"] += 1
                    continue
                qid = r.get("qid") or hashlib.md5(
                    (q + "\x00" + resp).encode("utf-8")).hexdigest()[:16]
                rows[key] = {
                    "id": hashlib.md5((q + "\x00" + resp)
                                      .encode("utf-8")).hexdigest()[:16],
                    "messages": messages,
                    "source": source,
                    "split": "train",          # finalised below
                    "row_id": r.get("chunk") or r.get("row_id") or "",
                    "tokens": len(ids),
                    "qid": qid,
                }
                seen_src["out"] += 1

    out_rows = list(rows.values())
    if not out_rows:
        print("RESULT: P4_SFTDATA_%s_FAIL zero valid rows after gates "
              "(raw=%d)" % (dom, stats["raw"]))
        return 1

    # ---- deterministic split + val floor --------------------------------
    def qhash(qid):
        return int(hashlib.md5(qid.encode("utf-8")).hexdigest(), 16)

    train, val = [], []
    for r in out_rows:
        (val if qhash(r["qid"]) % 20 == 0 else train).append(r)
    train.sort(key=lambda r: qhash(r["qid"]))
    val.sort(key=lambda r: qhash(r["qid"]))
    while len(val) < args.min_val and train:
        val.append(train.pop(0))
    if len(train) > args.max_train:
        train = train[:args.max_train]

    if len(val) < args.min_val:
        print("RESULT: P4_SFTDATA_%s_FAIL val rows=%d < %d"
              % (dom, len(val), args.min_val))
        return 1

    final = []
    for r in val:
        r2 = dict(r)
        r2["split"] = "val"
        final.append(r2)
    final.extend(r for r in train)
    final.sort(key=lambda r: qhash(r["id"]))
    for r in final:
        r.pop("qid")

    n_train, n_val = len(train), len(val)
    mean_tok = sum(r["tokens"] for r in final) / len(final)

    out = P4.sft_path(domain)
    stats_out = P4.sft_stats_path(domain)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    tmp = out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        for r in final:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, out)

    by_source = {}
    for r in final:
        by_source[r["source"]] = by_source.get(r["source"], 0) + 1
    payload = {
        "domain": domain,
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "file": out,
        "bytes": os.path.getsize(out),
        "train": n_train, "val": n_val, "total": n_train + n_val,
        "mean_tokens": round(mean_tok, 1),
        "max_train_cap": args.max_train, "min_val": args.min_val,
        "merge_grounded": bool(merge_ground),
        "max_token_filter": P4_MAX_TOKENS,
        "by_source": by_source,
        "gates": {"raw": stats["raw"], "failed_gate": stats["failed_gate"],
                  "dup": stats["dup"], "too_long": stats["too_long"]},
    }
    with open(stats_out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1)

    print("file       : %s (%d bytes)" % (out, payload["bytes"]))
    print("rows       : train=%d val=%d mean_tokens=%.1f"
          % (n_train, n_val, mean_tok))
    print("by_source  : %s" % ", ".join("%s=%d" % kv for kv in by_source.items()))
    print("gates      : raw=%d failed_gate=%d dup=%d too_long=%d"
          % (stats["raw"], stats["failed_gate"], stats["dup"],
             stats["too_long"]))
    print("RESULT: P4_SFTDATA_%s_OK train=%d val=%d" % (dom, n_train, n_val))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        print("RESULT: P4_SFTDATA_FAIL %s" % sys.exc_info()[1])
        sys.exit(1)
