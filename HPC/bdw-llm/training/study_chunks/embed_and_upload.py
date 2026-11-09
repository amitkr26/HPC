#!/usr/bin/env python3
"""
Phase 8: RAG Memory Bank Builder - Embed & Upload to Supabase
============================================================
Target Environment: Param Rudra HPC Cluster (A100-80GB GPU)
Embedder:           BAAI/bge-large-en-v1.5 (1024-dim, normalized)
Vector Store:       Supabase PostgreSQL (public.bdw_study_chunks)
RPC Search:         public.match_study_chunks
"""

import os
import sys
import time
import json
import hashlib
import argparse
from typing import List, Dict, Any

try:
    import torch
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Error: sentence-transformers or torch not found in environment.")
    sys.exit(1)

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:
    print("Error: psycopg not found in environment.")
    sys.exit(1)

# Paths
INPUT_JSONL = os.path.expanduser("~/bdw-llm/training/study_chunks/rag_documents.jsonl")
CHECKPOINT_FILE = os.path.expanduser("~/bdw-llm/training/study_chunks/embed_upload.checkpoint")
LOG_FILE = os.path.expanduser("~/bdw-llm/training/study_chunks/embed_upload.log")
PG_URL_FILE = os.path.expanduser("~/bdw-llm/phase3/pg_url.txt")
GATEWAY_ENV_FILE = os.path.expanduser("~/bdw-llm/phase3/gateway/.env")

MODEL_NAME = "BAAI/bge-large-en-v1.5"
EMBED_BATCH_SIZE = 256
UPLOAD_BATCH_SIZE = 250
DELAY_BETWEEN_BATCHES = 0.05  # seconds delay between batches to respect rate limits


def get_db_connection_string() -> str:
    """Retrieve database connection string safely."""
    if os.path.isfile(PG_URL_FILE):
        with open(PG_URL_FILE, "r") as f:
            url = f.read().strip()
            if url:
                return url
    if "DATABASE_URL" in os.environ:
        return os.environ["DATABASE_URL"]
    raise RuntimeError(f"Database connection string not found in {PG_URL_FILE} or environment.")


def load_checkpoint() -> set:
    """Load set of already uploaded chunk IDs."""
    if os.path.isfile(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, "r") as f:
                return set(line.strip() for line in f if line.strip())
        except Exception as e:
            print(f"[WARN] Could not load checkpoint: {e}")
    return set()


def append_checkpoint(chunk_ids: List[str]):
    """Record successfully uploaded chunk IDs."""
    try:
        with open(CHECKPOINT_FILE, "a") as f:
            for cid in chunk_ids:
                f.write(f"{cid}\n")
    except Exception as e:
        print(f"[WARN] Could not append checkpoint: {e}")


def infer_topic(filename: str, content: str) -> str:
    """Extract or infer relevant domain topic from filename and text."""
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


def run_embedding_and_upload(limit: int = None, verify_only: bool = False):
    print("=" * 70)
    print("=== BDW PHASE 8: RAG MEMORY BANK BUILDER & VECTOR INDEXER ===")
    print("=" * 70)
    
    if not os.path.isfile(INPUT_JSONL):
        raise FileNotFoundError(f"Source JSONL dataset not found: {INPUT_JSONL}")

    # Connect to PostgreSQL
    pg_url = get_db_connection_string()
    conn = psycopg.connect(pg_url)
    conn.autocommit = False
    print("[DB] Connected to Supabase PostgreSQL.")

    # Device check
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        torch.set_num_threads(24)
        print("[CPU] Configured PyTorch MKL with 24 threads for multi-core parallelism.")
    print(f"[MODEL] Loading '{MODEL_NAME}' onto device '{device}'...")
    if device == "cuda":
        gpu_name = torch.cuda.get_device_name(0)
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"[GPU] Active Accelerator: {gpu_name} ({gpu_mem:.1f} GB VRAM)")

    model = SentenceTransformer(MODEL_NAME, device=device)
    if device == "cuda":
        model.half()  # fp16 on A100 for maximum throughput
    print("[MODEL] Model ready for high-throughput batch vector generation.\n")

    if verify_only:
        test_search(conn, model)
        conn.close()
        return

    # Load checkpoint
    uploaded_ids = load_checkpoint()
    print(f"[CHECKPOINT] Previously indexed chunks: {len(uploaded_ids):,}")

    # Read records from JSONL
    print(f"[DATA] Reading chunks from {INPUT_JSONL}...")
    records_to_process = []
    total_in_file = 0

    with open(INPUT_JSONL, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            total_in_file += 1
            if limit and len(records_to_process) >= limit:
                break
            line_str = line.strip()
            if not line_str:
                continue
            item = json.loads(line_str)
            
            # Deterministic unique ID
            src = item.get("source", "unknown")
            c_idx = item.get("chunk_index", idx)
            chunk_id = hashlib.md5(f"{src}_{c_idx}".encode("utf-8")).hexdigest()
            
            if chunk_id in uploaded_ids:
                continue
                
            content = item.get("content", "").strip()
            if not content:
                continue
                
            topic = infer_topic(src, content)
            metadata = item.get("metadata", {})
            metadata["chunk_index"] = c_idx
            metadata["total_chunks"] = item.get("total_chunks", 1)
            metadata["source"] = src

            records_to_process.append({
                "id": chunk_id,
                "topic": topic,
                "filename": src,
                "content": content,
                "metadata": metadata
            })

    print(f"[DATA] Total chunks in file:     {total_in_file:,}")
    print(f"[DATA] Already in Supabase:      {len(uploaded_ids):,}")
    print(f"[DATA] Remaining to embed & push:{len(records_to_process):,}\n")

    if not records_to_process:
        print("[COMPLETE] All chunks already embedded and uploaded to Supabase!")
        test_search(conn, model)
        conn.close()
        return

    # Process in batches
    start_time = time.time()
    total_new_uploaded = 0
    num_batches = (len(records_to_process) + UPLOAD_BATCH_SIZE - 1) // UPLOAD_BATCH_SIZE

    print(f"[PIPELINE] Starting vector generation & Supabase batch uploads ({num_batches} batches)...")

    for b_idx in range(num_batches):
        b_start = b_idx * UPLOAD_BATCH_SIZE
        b_end = min(b_start + UPLOAD_BATCH_SIZE, len(records_to_process))
        batch = records_to_process[b_start:b_end]

        # 1. Generate Embeddings on GPU
        texts = [b["content"] for b in batch]
        # bge models expect query instruction for queries, but raw text for documents
        embeddings = model.encode(
            texts,
            batch_size=min(len(texts), EMBED_BATCH_SIZE),
            normalize_embeddings=True,
            show_progress_bar=False
        )

        # 2. Upload batch via direct psycopg with ON CONFLICT
        # Format embedding as vector string "[0.123,0.456,...]"
        insert_data = []
        batch_ids = []
        for r_item, emb in zip(batch, embeddings):
            vec_str = "[" + ",".join(f"{float(x):.6f}" for x in emb) + "]"
            insert_data.append((
                r_item["id"],
                r_item["topic"],
                r_item["filename"],
                r_item["content"],
                json.dumps(r_item["metadata"]),
                vec_str
            ))
            batch_ids.append(r_item["id"])

        sql = """
            INSERT INTO public.bdw_study_chunks (id, topic, filename, content, metadata, embedding)
            VALUES (%s, %s, %s, %s, %s, %s::extensions.vector)
            ON CONFLICT (id) DO UPDATE SET
                topic = EXCLUDED.topic,
                filename = EXCLUDED.filename,
                content = EXCLUDED.content,
                metadata = EXCLUDED.metadata,
                embedding = EXCLUDED.embedding,
                created_at = now();
        """
        
        retry_count = 0
        while retry_count < 3:
            try:
                with conn.cursor() as cur:
                    cur.executemany(sql, insert_data)
                conn.commit()
                break
            except Exception as e:
                retry_count += 1
                conn.rollback()
                print(f"[WARN] Batch {b_idx + 1} upload failed (attempt {retry_count}): {e}")
                time.sleep(2 * retry_count)
                if retry_count >= 3:
                    raise RuntimeError(f"Failed to upload batch {b_idx + 1} after 3 attempts.")

        append_checkpoint(batch_ids)
        total_new_uploaded += len(batch)

        elapsed = time.time() - start_time
        speed = total_new_uploaded / max(elapsed, 1)
        progress_pct = (total_new_uploaded / len(records_to_process)) * 100
        overall_total = len(uploaded_ids) + total_new_uploaded
        overall_pct = (overall_total / total_in_file) * 100

        if (b_idx + 1) % 5 == 0 or (b_idx + 1) == num_batches:
            print(f"[PROGRESS] Batch {b_idx + 1:3d}/{num_batches} | Uploaded: {overall_total:,} / {total_in_file:,} ({overall_pct:.1f}%) | Speed: {speed:.1f} chunks/sec | Elapsed: {elapsed/60:.1f}m")

        time.sleep(DELAY_BETWEEN_BATCHES)

    total_time = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"[SUCCESS] Embedded & indexed {total_new_uploaded:,} new chunks in {total_time/60:.2f} mins ({total_time:.1f}s)!")
    print(f"[TOTAL] Supabase Memory Bank now holds {len(uploaded_ids) + total_new_uploaded:,} verified chunks.")
    print("=" * 70 + "\n")

    # Run verification test query
    test_search(conn, model)
    conn.close()


def test_search(conn, model):
    """Run an end-to-end vector similarity test using match_study_chunks RPC."""
    print(">>> VERIFICATION TEST: Querying Supabase pgvector Memory Bank...")
    test_query = "VLSI static timing analysis setup and hold slack equations"
    
    # bge query prefix
    query_text = f"Represent this sentence for searching relevant passages: {test_query}"
    query_vec = model.encode(query_text, normalize_embeddings=True)
    vec_str = "[" + ",".join(f"{float(x):.6f}" for x in query_vec) + "]"

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT id, topic, filename, content, similarity
            FROM public.match_study_chunks(%s::extensions.vector, %s, %s);
            """,
            (vec_str, 3, None)
        )
        results = cur.fetchall()

    print(f"\n[QUERY] '{test_query}'")
    print(f"[RESULTS] Returned {len(results)} matches:\n")
    for idx, r in enumerate(results):
        print(f"--- Result #{idx + 1} (Similarity: {r['similarity']:.4f}) ---")
        print(f"Topic:    {r['topic']}")
        print(f"Filename: {r['filename']}")
        print(f"Snippet:  {r['content'][:250].strip()}...")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Embed study chunks and upload to Supabase.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of chunks to upload")
    parser.add_argument("--verify-only", action="store_true", help="Only run verification test query")
    args = parser.parse_args()

    run_embedding_and_upload(limit=args.limit, verify_only=args.verify_only)
