"""Shared Phase 4 domain constants + path helpers.

The five domains are the exact Phase 4 router surfaces ("Supported domains"
in phase4/router/domain_classifier.py): math, vlsi, embedded, cs, aiml.
GENERAL stays base-model-only (adapter=None in the router targets) and is
served from the existing P3 Supabase bdw_chunks pipeline, so it has no
per-domain artifact of its own here.

Corpus naming contract:
  contexts   data/raw/p4_<domain>_contexts.json   (Stage O.1 payload shape)
             vlsi defaults to the proven Stage O.1 file
             data/raw/vlsi_wikipedia.json until a p4_vlsi file exists
  qa         data/p4/qa/<domain>_qa.jsonl         (teacher QA, P4.1)
  sft        data/p4/sft/<domain>_sft.jsonl       (TRL rows, P4.2)
  run/ckpt   sft_runs/p4_<domain>/                (resumable TRL checkpoints)
  adapter    lora_<domain>/                       (router adapter name root)
  rag        phase4/rag/idx_<domain>/             (local npz index + meta)
  base       merged/bdw-7b-sft                    (the shipped P2.5 SFT model)

Everything downstream prints `RESULT: P4_*` markers (house discipline).
"""
from __future__ import annotations

import os

ROOT = os.path.expanduser("~/bdw-llm")

DOMAINS = ("math", "vlsi", "embedded", "cs", "aiml")


def check(domain: str) -> str:
    """Raise ValueError for anything outside the router domain surfaces."""
    if domain not in DOMAINS:
        raise ValueError("unknown domain %r -- expected one of %s"
                         % (domain, ", ".join(DOMAINS)))
    return domain


def ctx_path(domain: str) -> str:
    """Context payload for a domain (Stage O.1 schema, p4 stage tag).

    vlsi falls back to the shipped Stage O.1 wiki corpus unless a p4 refresh
    payload exists on disk (then the p4 file wins).
    """
    dom = check(domain)
    dom_p4 = os.path.join(ROOT, "data/raw/p4_%s_contexts.json" % dom)
    if os.path.isfile(dom_p4):
        return dom_p4
    if dom == "vlsi":
        return os.path.join(ROOT, "data/raw/vlsi_wikipedia.json")
    return dom_p4


def qa_path(domain: str) -> str:
    return os.path.join(ROOT, "data/p4/qa/%s_qa.jsonl" % check(domain))


def sft_path(domain: str) -> str:
    return os.path.join(ROOT, "data/p4/sft/%s_sft.jsonl" % check(domain))


def sft_stats_path(domain: str) -> str:
    return os.path.join(ROOT, "data/p4/sft/%s_stats.json" % check(domain))


def run_dir(domain: str) -> str:
    return os.path.join(ROOT, "sft_runs/p4_%s" % check(domain))


def snap_dir(domain: str) -> str:
    """Adapter root -- matches phase4/router Domain name ("lora_math" etc.)."""
    return os.path.join(ROOT, "lora_%s" % check(domain))


def metrics_path(domain: str) -> str:
    return os.path.join(ROOT, "logs/p4_%s_metrics.jsonl" % check(domain))


def progress_path(domain: str) -> str:
    return os.path.join(ROOT, "logs/p4_%s_progress.json" % check(domain))


def adapter_gguf_path(domain: str) -> str:
    return os.path.join(ROOT, "export/p4_lora_%s.gguf" % check(domain))


def rag_dir(target: str) -> str:
    """Index dir for a domain or the general stand-in ("idx_<target>")."""
    if target != "general":
        check(target)
    return os.path.join(ROOT, "phase4/rag/idx_%s" % target)


def rag_manifest_path() -> str:
    return os.path.join(ROOT, "phase4/rag/index_manifest.json")


def base_dir() -> str:
    """LoRA SFT base = the shipped P2.5 model (Qwen2.5-7B + p2LoRA merge)."""
    return os.path.join(ROOT, "merged/bdw-7b-sft")


def teacher_dir() -> str:
    """QA-generation teacher = the same P2.5 teacher (Qwen2.5-7B-Instruct)."""
    return os.path.join(ROOT, "teacher_model_7b")
