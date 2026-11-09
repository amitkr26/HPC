#!/usr/bin/env python3
"""
Direct Authenticated Stream Download, Extraction, Strict Privacy Triage, and Dataset Formatting
Target Environment: Param Rudra HPC Cluster
"""

import os
import sys
import time
import shutil
import subprocess

RAW_TEMP_DIR = os.path.expanduser("~/bdw-llm/raw_zip_temp")
RAW_ARCHIVE_PATH = os.path.join(RAW_TEMP_DIR, "input_archive.rar")
EXTRACT_DIR = os.path.join(RAW_TEMP_DIR, "extracted")
STUDY_MATERIALS_DIR = os.path.expanduser("~/bdw-llm/training/study_materials")
STUDY_CHUNKS_DIR = os.path.expanduser("~/bdw-llm/training/study_chunks")
UNRAR_BIN = shutil.which("unrar") or os.path.expanduser("~/bin/unrar")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_triage import classify_and_filter
from prepare_study_data import process_study_materials, purge_raw_temp

def download_stream(direct_url: str):
    """Download the archive using curl with resume support."""
    os.makedirs(RAW_TEMP_DIR, exist_ok=True)
    current_size = os.path.getsize(RAW_ARCHIVE_PATH) if os.path.exists(RAW_ARCHIVE_PATH) else 0
    print(f"[DOWNLOAD] Starting/resuming download into {RAW_ARCHIVE_PATH}...")
    print(f"[DOWNLOAD] Current size on disk: {current_size:,} bytes ({current_size/(1024**3):.2f} GB)")
    
    cmd = [
        "curl", "-L",
        "-C", "-",
        "--retry", "5",
        "--retry-delay", "3",
        direct_url,
        "-o", RAW_ARCHIVE_PATH
    ]
    
    start_time = time.time()
    # Run curl subprocess
    proc = subprocess.Popen(cmd)
    
    # Progress logger loop
    while proc.poll() is None:
        time.sleep(10)
        if os.path.exists(RAW_ARCHIVE_PATH):
            sz = os.path.getsize(RAW_ARCHIVE_PATH)
            elapsed = time.time() - start_time
            speed = (sz - current_size) / (1024 * 1024 * max(elapsed, 1))
            pct = (sz / 15430052174) * 100
            print(f"[PROGRESS] {sz/(1024**3):.2f} / 14.37 GB ({pct:.1f}%) | Speed: {speed:.1f} MB/s | Elapsed: {elapsed/60:.1f}m")
            
    if proc.returncode != 0:
        raise RuntimeError(f"curl download failed with return code {proc.returncode}")
        
    final_size = os.path.getsize(RAW_ARCHIVE_PATH)
    total_time = time.time() - start_time
    print(f"\n[DOWNLOAD] Download Finished! Final size: {final_size:,} bytes ({final_size/(1024**3):.2f} GB) in {total_time/60:.2f} mins")

def extract_archive():
    """Extract archive into isolated extracted/ folder using unrar."""
    print(f"\n[EXTRACT] Extracting {RAW_ARCHIVE_PATH} via unrar into {EXTRACT_DIR}...")
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    
    cmd = [UNRAR_BIN, "x", "-o+", "-y", RAW_ARCHIVE_PATH, EXTRACT_DIR + os.sep]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode not in [0, 1]:
        print(f"[EXTRACT_ERROR] {res.stderr[:500]}")
        raise RuntimeError(f"unrar exited with code {res.returncode}")
        
    print("[CLEANUP] Unlinking source RAR container to free up 15 GB of cluster storage...")
    try:
        os.remove(RAW_ARCHIVE_PATH)
        print("[CLEANUP] Source RAR unlinked.")
    except Exception as e:
        print(f"[CLEANUP_WARN] {e}")
        
    raw_files_count = sum(len(files) for _, _, files in os.walk(EXTRACT_DIR))
    print(f"[EXTRACT] Extraction completed. Total raw files: {raw_files_count}")
    return raw_files_count

def run_pipeline(direct_url: str):
    start_time = time.time()
    print("=" * 70)
    print("=== BEROJGARDEGREEWALA: AUTONOMOUS DATA EXTRACTION & PRIVACY SHIELD ===")
    print("=" * 70)
    
    # 1. Stream download
    download_stream(direct_url)
    
    # 2. Extract archive
    extract_archive()
    
    # 3. Privacy triage
    print("\n>>> STEP 3: Automated Privacy Shield & Document Triage")
    triage_res = classify_and_filter(raw_temp_dir=EXTRACT_DIR, target_safe_dir=STUDY_MATERIALS_DIR)
    
    # 4. Study data chunking
    print("\n>>> STEP 4: Format Study Data Chunks & JSONL Datasets")
    prepare_res = process_study_materials(materials_dir=STUDY_MATERIALS_DIR, output_chunks_dir=STUDY_CHUNKS_DIR)
    
    # 5. Aggressive cleanup of entire raw_zip_temp directory
    print("\n>>> STEP 5: Aggressive Wipe of All Raw & Unclassified Data")
    purge_raw_temp(RAW_TEMP_DIR)
    
    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print("=== FINAL EXECUTION REPORT ===")
    print("=" * 70)
    print(f"Total Pipeline Runtime:   {elapsed/60:.2f} minutes ({elapsed:.1f} seconds)")
    print(f"Total Raw Files Scanned:  {triage_res['total_scanned']}")
    print(f"Verified Study Preserved: {triage_res['safe_retained']} files")
    print(f"Sensitive Files Purged:   {triage_res['danger_deleted']} (permanently deleted)")
    print(f"Media Files Purged:       {triage_res['media_deleted']} (permanently deleted)")
    print(f"Ambiguous Files Purged:   {triage_res['ambiguous_deleted']} (permanently deleted)")
    print(f"Total Text Chunks Made:   {prepare_res['total_chunks']}")
    print(f"Study Materials Folder:   {STUDY_MATERIALS_DIR}")
    print(f"Text Chunks Output:       {os.path.join(STUDY_CHUNKS_DIR, 'txt_chunks')}")
    print(f"Supabase Vector RAG JSONL:{prepare_res['rag_jsonl']}")
    print(f"QLoRA ChatML Dataset:     {prepare_res['qlora_jsonl']}")
    print(f"Raw Sandbox Purge Status: CONFIRMED DELETED ({not os.path.exists(RAW_TEMP_DIR)})")
    print("=" * 70)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 resume_direct_url.py <DIRECT_DOWNLOAD_URL>")
        sys.exit(1)
    run_pipeline(sys.argv[1])
