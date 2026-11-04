"""P2.4 ship gate: merge the P2.5 LoRA adapter into bf16 weights (blueprint S8.1).

Qwen2.5-7B-Instruct (teacher_model_7b, local) + lora_snap_p25/final
(r=32, alpha=64, 392 tensors) -> model.merge_and_unload() ->
merged/bdw-7b-sft/ in bf16 (~15.2 GB; shards at 5000 MB) plus tokenizer files
and md5_manifest.txt in `md5sum -c` format ("md5<2 spaces>relpath", every file
in the dir except the manifest itself).

Atomic: everything is written to <out>.tmp and renamed with os.replace, so a
wall kill can never leave a half-merged directory that looks complete.
Fresh-guard: fails if <out> exists (delete it to re-run); a stale <out>.tmp
from a killed run is removed automatically.

No network (local_files_only), CPU code path for the merge itself.

RESULT: P2_MERGE_OK files=... bytes=... gb=... shards=... manifest=...
RESULT: P2_MERGE_FAIL <reason>
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
import time
import traceback

ROOT = os.path.expanduser("~/bdw-llm")
BASE = os.path.join(ROOT, "teacher_model_7b")
ADAPTER = os.path.join(ROOT, "lora_snap_p25/final")
OUT = os.path.join(ROOT, "merged/bdw-7b-sft")
MANIFEST = "md5_manifest.txt"
SHARD = "5000MB"


def md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description="merge LoRA -> bf16 weights")
    ap.add_argument("--base", default=BASE)
    ap.add_argument("--adapter", default=ADAPTER)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--force", action="store_true",
                    help="overwrite an existing <out> directory")
    args = ap.parse_args()

    import torch
    import transformers
    from peft import PeftModel

    t0 = time.time()
    for label, p in (("base", args.base), ("adapter", args.adapter)):
        if not os.path.isdir(p):
            raise SystemExit("%s missing: %s" % (label, p))
    if os.path.isdir(args.out) and os.listdir(args.out):
        if not args.force:
            raise SystemExit("out exists (fresh guard): %s  "
                             "--force to overwrite" % args.out)
        shutil.rmtree(args.out)
    tmp = args.out + ".tmp"
    if os.path.isdir(tmp):
        shutil.rmtree(tmp)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    print("base      : %s" % args.base, flush=True)
    print("adapter   : %s" % args.adapter, flush=True)
    print("out       : %s  (via %s.tmp, bf16, max_shard=%s)"
          % (args.out, args.out, SHARD), flush=True)

    tok = transformers.AutoTokenizer.from_pretrained(
        args.base, local_files_only=True)
    model = transformers.AutoModelForCausalLM.from_pretrained(
        args.base, torch_dtype=torch.bfloat16, local_files_only=True)
    print("loaded    : %s params=%.2fB dtype=%s (%.0fs)"
          % (model.config.model_type,
             sum(p.numel() for p in model.parameters()) / 1e9,
             next(model.parameters()).dtype, time.time() - t0), flush=True)

    model = PeftModel.from_pretrained(model, args.adapter)
    merged = model.merge_and_unload()
    if isinstance(merged, PeftModel):
        raise SystemExit("merge_and_unload still returns a PeftModel")
    print("merged    : %s (%.0fs)"
          % (type(merged).__name__, time.time() - t0), flush=True)
    del model
    torch.cuda.empty_cache()

    t1 = time.time()
    merged.save_pretrained(tmp, safe_serialization=True,
                           max_shard_size=SHARD)
    tok.save_pretrained(tmp)
    save_s = time.time() - t1
    shards = sorted(f for f in os.listdir(tmp) if f.endswith(".safetensors"))

    files = sorted(f for f in os.listdir(tmp))
    total = 0
    lines = []
    for f in files:
        p = os.path.join(tmp, f)
        total += os.path.getsize(p)
        lines.append("%s  %s" % (md5_file(p), f))
    with open(os.path.join(tmp, MANIFEST), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    os.replace(tmp, args.out)
    print("saved     : %d files (+manifest), %d shards, %.2f GB, "
          "%.0fs save" % (len(files), len(shards), total / 1e9, save_s),
          flush=True)
    print("manifest  : %s (%d entries)" % (os.path.join(args.out, MANIFEST),
                                          len(lines)), flush=True)
    print("RESULT: P2_MERGE_OK files=%d bytes=%d gb=%.2f shards=%d "
          "manifest=%s elapsed=%.0fs"
          % (len(files) + 1, total, total / 1e9, len(shards),
             os.path.join(args.out, MANIFEST), time.time() - t0), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        print("RESULT: P2_MERGE_FAIL %s" % sys.exc_info()[1], flush=True)
        sys.exit(1)
