#!/usr/bin/env python3
"""
Step 1: High-Speed A100 GPU Vector Generation
Generates 1024-dim BGE-large-en-v1.5 embeddings for all 35,187 study chunks
and saves them to vector_records.jsonl on cluster NFS.
"""

import os
import sys
import time
import json
import hashlib
from typing import List, Dict, Any

import torch
from sentence_transformers import SentenceTransformer

INPUT_JSONL = os.path.expanduser("~/bdw-llm/training/study_chunks/rag_documents.jsonl")
OUTPUT_JSONL = os.path.expanduser("~/bdw-llm/training/study_chunks/vector_records.jsonl")
MODEL_NAME = "BAAI/bge-large-en-v1.5"
BATCH_SIZE = 256


def infer_topic(filename: str, content: str) -> str:
    combined = (filename + " " + content[:200]).lower()
    if any(k in combined for k in ["vlsi", "asic", "timing", "sta", "setup", "hold", "slack", "rtl", "verilog", "vhdl"]):
        return "vlsi_design"
    if any(k in combined for k in ["semiconductor", "cmos", "mosfet", "bjt", "fabrication", "cleanroom", "doping", "pn junction"]):
        return "semiconductor_devices"
    if any(k in combined for k in ["embedded", "microprocessor", "8085", "8086", "arm", "gpio", "interrupt", "firmware"]):
        return "embedded_systems"
    if any(k in combined for k in ["signal", "fourier", "laplace", "fft", "filter", "dsp", "convolution"]):
        return "signals_and_systems"
    if any(k in combined for k in ["antenna", "waveguide", "electromagnetic", "emft", "maxwell", "microwave"]):
        return "electromagnetics_rf"
    if any(k in combined for k in ["math", "calculus", "differential", "matrix", "algebra"]):
        return "applied_mathematics"
    return "general_hardware_electronics"


def sanitize(text: str) -> str:
    """Strip NUL bytes and invalid characters for Postgres compatibility."""
    if not isinstance(text, str):
        return ""
    return text.replace("\x00", "").replace("\u0000", "")


def main():
    print("=" * 70)
    print("=== STEP 1: A100 GPU VECTOR GENERATION FOR RAG MEMORY BANK ===")
    print("=" * 70)
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    if device == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / (1024**3):.1f} GB")

    print(f"Loading {MODEL_NAME}...")
    t0 = time.time()
    model = SentenceTransformer(MODEL_NAME, device=device)
    if device == "cuda":
        model.half()
    print(f"Model loaded in {time.time() - t0:.2f}s")

    print(f"Reading dataset: {INPUT_JSONL}")
    records = []
    with open(INPUT_JSONL, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            line_str = line.strip()
            if not line_str:
                continue
            item = json.loads(line_str)
            src = sanitize(item.get("source", "unknown"))
            c_idx = item.get("chunk_index", idx)
            chunk_id = hashlib.md5(f"{src}_{c_idx}".encode("utf-8")).hexdigest()
            content = sanitize(item.get("content", "").strip())
            if not content:
                continue
            topic = infer_topic(src, content)
            meta = item.get("metadata", {})
            meta["chunk_index"] = c_idx
            meta["total_chunks"] = item.get("total_chunks", 1)
            meta["source"] = src

            records.append({
                "id": chunk_id,
                "topic": topic,
                "filename": src,
                "content": content,
                "metadata": meta
            })

    total_records = len(records)
    print(f"Loaded {total_records:,} sanitized chunks for embedding.")

    t_start = time.time()
    num_batches = (total_records + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"Processing in {num_batches} batches of {BATCH_SIZE}...")

    # Open output file
    with open(OUTPUT_JSONL, "w", encoding="utf-8") as out_f:
        for b_idx in range(num_batches):
            b_start = b_idx * BATCH_SIZE
            b_end = min(b_start + BATCH_SIZE, total_records)
            batch = records[b_start:b_end]

            texts = [r["content"] for r in batch]
            embeddings = model.encode(
                texts,
                batch_size=len(texts),
                normalize_embeddings=True,
                show_progress_bar=False
            )

            for r_item, emb in zip(batch, embeddings):
                # Round to 6 decimal places for compact JSON storage
                r_item["embedding"] = [round(float(x), 6) for x in emb]
                out_f.write(json.dumps(r_item, ensure_ascii=False) + "\n")

            if (b_idx + 1) % 10 == 0 or (b_idx + 1) == num_batches:
                processed = b_end
                elapsed = time.time() - t_start
                rate = processed / max(elapsed, 0.001)
                pct = (processed / total_records) * 100
                print(f"[A100 EMBED] Batch {b_idx + 1:3d}/{num_batches} | {processed:,}/{total_records:,} ({pct:.1f}%) | {rate:.1f} chunks/sec | Elapsed: {elapsed:.1f}s")

    dur = time.time() - t_start
    print("=" * 70)
    print(f"[SUCCESS] All {total_records:,} chunks embedded in {dur:.2f}s ({total_records/dur:.1f} chunks/sec)!")
    print(f"Output saved to: {OUTPUT_JSONL}")
    print("=" * 70)


if __name__ == "__main__":
    main()
