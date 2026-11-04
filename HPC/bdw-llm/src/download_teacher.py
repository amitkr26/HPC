"""Stage N.1: download a teacher model on the login node (has internet).

Run this on the login node only -- compute nodes have no DNS. Everything is
pulled into a repo-local directory so Step N.2 (GPU node, offline) can load it
with no network at all.

Usage:
    python download_teacher.py <repo_id> <local_dir> [expected_min_gb]

Sequence-level distillation, not logit distillation: the student owns a custom
16,384-token byte-level BPE, so the teacher's vocabulary does not align with
the student's and logit-space KL divergence is not defined. We only take the
teacher's TEXT.

Teacher progression measured on real VLSI questions:
  Qwen2.5-0.5B  - invented "ATPG = Automated Testing Program Generator"
                  (software framing); called STA a software technique. Rejected.
  Qwen2.5-1.5B  - correct domain/acronyms, but still fabricated specifics
                  (described corner simulation as a digital truth table;
                  claimed buffers fix setup by "adding delay"). Used as a
                  baseline, not as the final teacher.
  Qwen2.5-7B    - chosen for accuracy over speed; see generate_teacher_data.py.
"""
import hashlib
import json
import os
import sys
import time

CHECK = ["config.json", "generation_config.json", "tokenizer.json",
         "tokenizer_config.json"]


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if len(sys.argv) < 3:
        print("usage: download_teacher.py <repo_id> <local_dir> [min_gb]")
        sys.exit(2)
    repo = sys.argv[1]
    dest = os.path.expanduser(sys.argv[2])
    min_gb = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0

    print("=" * 76)
    print("STAGE N.1 - TEACHER MODEL DOWNLOAD (login node, internet OK)")
    print("=" * 76)
    print("repo    :", repo)
    print("dest    :", dest)
    print("host    :", os.uname().nodename)
    print("started :", time.strftime("%Y-%m-%dT%H:%M:%S"))
    sys.stdout.flush()

    from huggingface_hub import snapshot_download

    t0 = time.time()
    path = snapshot_download(repo_id=repo, local_dir=dest)
    print("\n[snapshot] downloaded in %.1fs -> %s" % (time.time() - t0, path))
    sys.stdout.flush()

    files = []
    for root, _dirs, names in os.walk(dest):
        for n in sorted(names):
            p = os.path.join(root, n)
            rel = os.path.relpath(p, dest)
            if ".cache" in rel.split(os.sep):
                continue
            files.append((rel, os.path.getsize(p)))
    total = sum(s for _, s in files)
    print("\n[inventory] %d files, %.2f MB total" % (len(files), total / 1e6))
    for rel, size in sorted(files):
        print("  %-46s %12d B" % (rel, size))
    sys.stdout.flush()

    print("\n[checksums]")
    digests = {}
    for name in CHECK:
        p = os.path.join(dest, name)
        if os.path.exists(p):
            digests[name] = md5(p)
            print("  %-46s %s" % (name, digests[name]))
    with open(os.path.join(dest, "_download_manifest.json"), "w") as fh:
        json.dump({"repo": repo, "bytes": total, "files": len(files),
                   "md5": digests,
                   "finished": time.strftime("%Y-%m-%dT%H:%M:%S")}, fh, indent=2)
    sys.stdout.flush()

    print("\n[offline test] HF_HUB_OFFLINE=1, no network allowed ...")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    t0 = time.time()
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tok = AutoTokenizer.from_pretrained(dest, local_files_only=True)
        enc = tok("What is a hold violation in VLSI?", return_tensors="pt")
        print("  tokenizer OK  vocab=%d" % tok.vocab_size)
        # dtype=bf16 avoids materialising 15 GB of fp32 RAM on the login node
        model = AutoModelForCausalLM.from_pretrained(
            dest, local_files_only=True, dtype=torch.bfloat16)
        n = sum(p.numel() for p in model.parameters())
        print("  weights OK    params=%s (%.2f B)  loaded in %.1fs"
              % (f"{n:,}", n / 1e6, time.time() - t0))
        del model
    except Exception as e:
        print("  OFFLINE TEST FAILED: %s: %s" % (type(e).__name__, e))
        print("RESULT: N1_TEACHER_DOWNLOAD_FAILED")
        sys.exit(1)

    gb = total / 1e9
    ok = gb >= min_gb
    print()
    print("RESULT: N1_TEACHER_DOWNLOAD_%s (%s, %.2f GB)"
          % ("OK" if ok else "TOO_SMALL", repo, gb))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
