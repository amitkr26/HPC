#!/usr/bin/env python3
"""
BDW End-to-End Ingestion, Virus-Bypass Resume, Triage, and Chunking Orchestrator
Target Environment: Param Rudra HPC Cluster
"""

import os
import sys
import re
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

def setup_partial_file():
    """Ensure existing partial download is named input_archive.rar for curl resume."""
    os.makedirs(RAW_TEMP_DIR, exist_ok=True)
    
    # Check if a .part file exists
    if not os.path.exists(RAW_ARCHIVE_PATH):
        for f in os.listdir(RAW_TEMP_DIR):
            if f.endswith(".part") and os.path.getsize(os.path.join(RAW_TEMP_DIR, f)) > 1000000000:
                part_path = os.path.join(RAW_TEMP_DIR, f)
                print(f"[RESUME] Found existing {os.path.getsize(part_path)/(1024**3):.2f} GB partial file: {f}")
                print(f"[RESUME] Renaming to {RAW_ARCHIVE_PATH} for curl resume...")
                shutil.move(part_path, RAW_ARCHIVE_PATH)
                break
                
    if os.path.exists(RAW_ARCHIVE_PATH):
        current_bytes = os.path.getsize(RAW_ARCHIVE_PATH)
        print(f"[RESUME] Current archive size on disk: {current_bytes:,} bytes ({current_bytes/(1024**3):.2f} GB)")
    else:
        print("[RESUME] Starting fresh download into input_archive.rar")

def download_with_curl_bypass(file_id: str):
    """Fetch virus warning tokens and stream archive using curl with cookie jar and resume."""
    print(f"\n[DOWNLOAD] Connecting to Google Drive for File ID: {file_id}...")
    cookie_jar = os.path.join(RAW_TEMP_DIR, "cookies.txt")
    confirm_html = os.path.join(RAW_TEMP_DIR, "confirm.html")
    
    # Step 1: Initial request to get virus warning page and session cookies
    print("[DOWNLOAD] Fetching initial confirmation metadata and cookiejar...")
    cmd1 = [
        "curl", "-s", "-L",
        "-c", cookie_jar,
        f"https://drive.google.com/uc?export=download&id={file_id}",
        "-o", confirm_html
    ]
    subprocess.run(cmd1, check=True)
    
    with open(confirm_html, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()
        
    uuid_match = re.search(r'name="uuid"\s+value="([^"]+)"', html)
    confirm_match = re.search(r'name="confirm"\s+value="([^"]+)"', html)
    
    if not uuid_match or not confirm_match:
        # Fallback check for alternate confirm regex
        alt_confirm = re.search(r'confirm=([0-9A-Za-z_-]+)', html)
        confirm_token = alt_confirm.group(1) if alt_confirm else "t"
        uuid_token = ""
    else:
        uuid_token = uuid_match.group(1)
        confirm_token = confirm_match.group(1)
        
    print(f"[DOWNLOAD] Parsed Security Tokens -> confirm={confirm_token}, uuid={uuid_token}")
    
    if uuid_token:
        download_url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm={confirm_token}&uuid={uuid_token}"
    else:
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}&confirm={confirm_token}"
        
    print(f"[DOWNLOAD] Streaming remaining archive directly to {RAW_ARCHIVE_PATH} (curl -C -)...")
    
    # Run curl with resume (-C -)
    cmd2 = [
        "curl", "-L",
        "-b", cookie_jar,
        "-c", cookie_jar,
        "-C", "-",
        "--retry", "5",
        "--retry-delay", "3",
        download_url,
        "-o", RAW_ARCHIVE_PATH
    ]
    
    res = subprocess.run(cmd2)
    if res.returncode != 0:
        raise RuntimeError(f"curl download failed with exit code {res.returncode}")
        
    final_size = os.path.getsize(RAW_ARCHIVE_PATH)
    print(f"[DOWNLOAD] Download Complete! Final Archive Size: {final_size:,} bytes ({final_size/(1024**3):.2f} GB)")

def extract_archive():
    """Extract input_archive.rar into isolated extracted folder using unrar."""
    print(f"\n[EXTRACT] Extracting {RAW_ARCHIVE_PATH} via unrar...")
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    
    cmd = [UNRAR_BIN, "x", "-o+", "-y", RAW_ARCHIVE_PATH, EXTRACT_DIR + os.sep]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode not in [0, 1]:
        print(f"[EXTRACT_ERROR] {res.stderr[:500]}")
        raise RuntimeError(f"unrar failed with code {res.returncode}")
        
    # Immediately remove the 14GB archive to free up disk space
    print("[CLEANUP] Unlinking source RAR container from disk to reclaim 14GB space...")
    try:
        os.remove(RAW_ARCHIVE_PATH)
        print("[CLEANUP] Source RAR file deleted successfully.")
    except Exception as e:
        print(f"[CLEANUP_WARNING] Could not delete RAR file: {e}")
        
    extracted_count = sum(len(files) for _, _, files in os.walk(EXTRACT_DIR))
    print(f"[EXTRACT] Extraction completed. Total raw files: {extracted_count}")
    return extracted_count

def run_full_pipeline(file_id: str):
    start_time = time.time()
    print("=" * 70)
    print("=== BEROJGARDEGREEWALA: AUTONOMOUS DATA EXTRACTION & PRIVACY SHIELD ===")
    print("=" * 70)
    
    # Step 1: Prepare partial cache and resume download
    setup_partial_file()
    download_with_curl_bypass(file_id)
    
    # Step 2: Extract archive
    raw_count = extract_archive()
    
    # Step 3: Strict Privacy Triage
    print("\n>>> STEP 3: Automated Privacy Shield & Document Triage")
    triage_res = classify_and_filter(raw_temp_dir=EXTRACT_DIR, target_safe_dir=STUDY_MATERIALS_DIR)
    
    # Step 4: Format Study Data into Vector RAG & QLoRA chunks
    print("\n>>> STEP 4: Format Study Data Chunks & JSONL Datasets")
    prepare_res = process_study_materials(materials_dir=STUDY_MATERIALS_DIR, output_chunks_dir=STUDY_CHUNKS_DIR)
    
    # Step 5: Aggressive cleanup of entire raw_zip_temp directory
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
    target_id = sys.argv[1] if len(sys.argv) > 1 else "1Lr9srXa51MXI9PlQCnka8SeiCytgsLyd"
    run_full_pipeline(target_id)
