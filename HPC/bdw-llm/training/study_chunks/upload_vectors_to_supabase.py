#!/usr/bin/env python3
"""
Step 2: Stream Pre-Computed Vector Records to Supabase PostgreSQL
================================================================
Reads vector_records.jsonl and uploads in high-throughput batches
into public.bdw_study_chunks using ON CONFLICT (id) DO UPDATE.
"""

import os
import sys
import time
import json
import argparse
from typing import List, Dict, Any

import psycopg
from psycopg.rows import dict_row

VECTORS_JSONL = os.path.expanduser("~/bdw-llm/training/study_chunks/vector_records.jsonl")
CHECKPOINT_FILE = os.path.expanduser("~/bdw-llm/training/study_chunks/embed_upload.checkpoint")
PG_URL_FILE = os.path.expanduser("~/bdw-llm/phase3/pg_url.txt")

UPLOAD_BATCH_SIZE = 500
DELAY_BETWEEN_BATCHES = 0.05


def get_db_url() -> str:
    if os.path.isfile(PG_URL_FILE):
        with open(PG_URL_FILE, "r") as f:
            url = f.read().strip()
            if url:
                return url
    if "DATABASE_URL" in os.environ:
        return os.environ["DATABASE_URL"]
    raise RuntimeError("Database connection string not found.")


def load_checkpoint() -> set:
    if os.path.isfile(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()


def append_checkpoint(chunk_ids: List[str]):
    with open(CHECKPOINT_FILE, "a") as f:
        for cid in chunk_ids:
            f.write(f"{cid}\n")


def main():
    print("=" * 70)
    print("=== STEP 2: STREAMING VECTORS INTO SUPABASE MEMORY BANK ===")
    print("=" * 70)

    if not os.path.isfile(VECTORS_JSONL):
        raise FileNotFoundError(f"Vector records file not found: {VECTORS_JSONL}")

    pg_url = get_db_url()
    conn = psycopg.connect(pg_url)
    conn.autocommit = False
    print("[DB] Connected to Supabase PostgreSQL.")

    uploaded_ids = load_checkpoint()
    print(f"[CHECKPOINT] Previously indexed chunks: {len(uploaded_ids):,}")

    records_to_upload = []
    total_in_file = 0

    print(f"[DATA] Reading {VECTORS_JSONL}...")
    with open(VECTORS_JSONL, "r", encoding="utf-8") as f:
        for line in f:
            total_in_file += 1
            line_str = line.strip()
            if not line_str:
                continue
            item = json.loads(line_str)
            cid = item["id"]
            if cid in uploaded_ids:
                continue
            records_to_upload.append(item)

    print(f"[DATA] Total in vector file:     {total_in_file:,}")
    print(f"[DATA] Already in Supabase:      {len(uploaded_ids):,}")
    print(f"[DATA] Remaining to upload:      {len(records_to_upload):,}\n")

    if not records_to_upload:
        print("[COMPLETE] All chunks are already uploaded to Supabase!")
        verify_db(conn)
        conn.close()
        return

    num_batches = (len(records_to_upload) + UPLOAD_BATCH_SIZE - 1) // UPLOAD_BATCH_SIZE
    print(f"[UPLOAD] Starting batch stream ({num_batches} batches of {UPLOAD_BATCH_SIZE})...")

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

    t_start = time.time()
    uploaded_count = 0

    for b_idx in range(num_batches):
        b_start = b_idx * UPLOAD_BATCH_SIZE
        b_end = min(b_start + UPLOAD_BATCH_SIZE, len(records_to_upload))
        batch = records_to_upload[b_start:b_end]

        insert_data = []
        batch_ids = []
        for item in batch:
            vec_str = "[" + ",".join(str(x) for x in item["embedding"]) + "]"
            insert_data.append((
                item["id"],
                item["topic"].replace("\x00", ""),
                item["filename"].replace("\x00", ""),
                item["content"].replace("\x00", ""),
                json.dumps(item["metadata"]).replace("\x00", ""),
                vec_str
            ))
            batch_ids.append(item["id"])

        retry = 0
        while retry < 3:
            try:
                with conn.cursor() as cur:
                    cur.executemany(sql, insert_data)
                conn.commit()
                break
            except Exception as e:
                retry += 1
                conn.rollback()
                print(f"[WARN] Batch {b_idx + 1} failed (attempt {retry}): {e}")
                time.sleep(2 * retry)
                if retry >= 3:
                    raise

        append_checkpoint(batch_ids)
        uploaded_count += len(batch)

        elapsed = time.time() - t_start
        rate = uploaded_count / max(elapsed, 0.001)
        total_now = len(uploaded_ids) + uploaded_count
        pct = (total_now / total_in_file) * 100

        if (b_idx + 1) % 5 == 0 or (b_idx + 1) == num_batches:
            print(f"[UPLOAD PROGRESS] Batch {b_idx + 1:3d}/{num_batches} | Uploaded: {total_now:,}/{total_in_file:,} ({pct:.1f}%) | Speed: {rate:.1f} rows/sec | Elapsed: {elapsed:.1f}s")

        time.sleep(DELAY_BETWEEN_BATCHES)

    dur = time.time() - t_start
    print("\n" + "=" * 70)
    print(f"[SUCCESS] Streamed {uploaded_count:,} chunks into Supabase in {dur:.2f}s ({uploaded_count/dur:.1f} rows/sec)!")
    print("=" * 70)

    verify_db(conn)
    conn.close()


def verify_db(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM public.bdw_study_chunks;")
        total_rows = cur.fetchone()[0]
    print(f"\n[VERIFIED] Total indexed chunks in public.bdw_study_chunks: {total_rows:,}")


if __name__ == "__main__":
    main()
