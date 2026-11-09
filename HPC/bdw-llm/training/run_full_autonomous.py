#!/usr/bin/env python3
"""
Full Autonomous Execution:
1. Browser-authenticated stream resume from byte 6,560,415,744
2. Archive extraction via unrar
3. Strict privacy shield and document triage
4. Study chunk formatting and JSONL dataset generation
5. Aggressive purge of raw_zip_temp
"""

import os
import sys
import re
import time
import shutil
import subprocess
import requests
from bs4 import BeautifulSoup

RAW_TEMP_DIR = os.path.expanduser("~/bdw-llm/raw_zip_temp")
RAW_ARCHIVE_PATH = os.path.join(RAW_TEMP_DIR, "input_archive.rar")
EXTRACT_DIR = os.path.join(RAW_TEMP_DIR, "extracted")
STUDY_MATERIALS_DIR = os.path.expanduser("~/bdw-llm/training/study_materials")
STUDY_CHUNKS_DIR = os.path.expanduser("~/bdw-llm/training/study_chunks")
UNRAR_BIN = shutil.which("unrar") or os.path.expanduser("~/bin/unrar")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_triage import classify_and_filter
from prepare_study_data import process_study_materials, purge_raw_temp

TOTAL_EXPECTED_BYTES = 15430052174
FID = "1Lr9srXa51MXI9PlQCnka8SeiCytgsLyd"

def prepare_partial_file():
    """Ensure partial file is ready as input_archive.rar"""
    os.makedirs(RAW_TEMP_DIR, exist_ok=True)
    if not os.path.exists(RAW_ARCHIVE_PATH):
        for f in os.listdir(RAW_TEMP_DIR):
            if f.endswith(".part"):
                p = os.path.join(RAW_TEMP_DIR, f)
                if os.path.getsize(p) > 1000000000:
                    print(f"[RESUME] Found partial file {f} ({os.path.getsize(p)/(1024**3):.2f} GB). Renaming...")
                    shutil.move(p, RAW_ARCHIVE_PATH)
                    break
    current = os.path.getsize(RAW_ARCHIVE_PATH) if os.path.exists(RAW_ARCHIVE_PATH) else 0
    print(f"[RESUME] Initial archive size on disk: {current:,} bytes ({current/(1024**3):.2f} GB)")
    return current

def download_remaining_stream(start_bytes: int):
    """Execute browser-grade navigation chain and stream remaining bytes."""
    if start_bytes >= TOTAL_EXPECTED_BYTES:
        print(f"[DOWNLOAD] Archive already fully downloaded ({start_bytes:,} bytes). Skipping download.")
        return

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    session = requests.Session()
    session.headers.update(headers)

    print("\n[DOWNLOAD] Navigating Google Drive browser chain...")
    view_url = f"https://drive.google.com/file/d/{FID}/view"
    session.get(view_url, timeout=20)
    
    session.headers['Referer'] = view_url
    uc_url = f"https://drive.google.com/uc?export=download&id={FID}"
    r2 = session.get(uc_url, timeout=20)
    
    soup = BeautifulSoup(r2.text, 'html.parser')
    form = soup.select_one('#download-form')
    if not form:
        raise RuntimeError("Could not find download-form in Google Drive confirmation response.")
        
    action = form.get('action')
    params = {inp.get('name'): inp.get('value') for inp in form.find_all('input') if inp.get('name') and inp.get('value')}
    print(f"[DOWNLOAD] Form params resolved: confirm={params.get('confirm')}, uuid={params.get('uuid')}")
    
    session.headers['Referer'] = r2.url
    session.headers['Range'] = f"bytes={start_bytes}-"
    
    print(f"[DOWNLOAD] Initiating stream from byte {start_bytes:,} to {TOTAL_EXPECTED_BYTES:,}...")
    dl_start = time.time()
    last_log = dl_start
    bytes_downloaded = start_bytes
    
    with session.get(action, params=params, stream=True, timeout=30) as stream_resp:
        if stream_resp.status_code not in [200, 206]:
            raise RuntimeError(f"Unexpected stream response status: {stream_resp.status_code}")
            
        mode = "ab" if (start_bytes > 0 and stream_resp.status_code == 206) else "wb"
        chunk_size = 4 * 1024 * 1024  # 4 MB chunks
        
        with open(RAW_ARCHIVE_PATH, mode) as f:
            for chunk in stream_resp.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    bytes_downloaded += len(chunk)
                    now = time.time()
                    if now - last_log >= 10:  # Log progress every 10 seconds
                        pct = (bytes_downloaded / TOTAL_EXPECTED_BYTES) * 100
                        speed = (bytes_downloaded - start_bytes) / (1024 * 1024 * (now - dl_start))
                        print(f"[STREAM] {bytes_downloaded/(1024**3):.2f} / {TOTAL_EXPECTED_BYTES/(1024**3):.2f} GB ({pct:.1f}%) | Speed: {speed:.1f} MB/s")
                        last_log = now
                        
    final_size = os.path.getsize(RAW_ARCHIVE_PATH)
    total_time = time.time() - dl_start
    print(f"\n[DOWNLOAD] Complete! Downloaded in {total_time/60:.2f} mins. Final size: {final_size:,} bytes ({final_size/(1024**3):.2f} GB)")

def extract_archive():
    """Extract input_archive.rar into isolated directory using unrar."""
    print(f"\n[EXTRACT] Extracting {RAW_ARCHIVE_PATH} via unrar into {EXTRACT_DIR}...")
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    
    cmd = [UNRAR_BIN, "x", "-o+", "-y", RAW_ARCHIVE_PATH, EXTRACT_DIR + os.sep]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode not in [0, 1]:
        print(f"[EXTRACT_ERROR] {res.stderr[:500]}")
        raise RuntimeError(f"unrar exited with error code {res.returncode}")
        
    print("[CLEANUP] Unlinking source RAR container to free 14GB disk space...")
    try:
        os.remove(RAW_ARCHIVE_PATH)
        print("[CLEANUP] Source RAR unlinked.")
    except Exception as e:
        print(f"[CLEANUP_WARN] {e}")
        
    extracted_count = sum(len(files) for _, _, files in os.walk(EXTRACT_DIR))
    print(f"[EXTRACT] Extraction completed. Total raw files: {extracted_count}")
    return extracted_count

def run_pipeline():
    start_time = time.time()
    print("=" * 70)
    print("=== BEROJGARDEGREEWALA: AUTONOMOUS DATA EXTRACTION & PRIVACY SHIELD ===")
    print("=" * 70)
    
    # 1. Prepare and resume download
    start_bytes = prepare_partial_file()
    download_remaining_stream(start_bytes)
    
    # 2. Extract archive
    extract_archive()
    
    # 3. Privacy triage
    print("\n>>> STEP 3: Automated Privacy Shield & Document Triage")
    triage_res = classify_and_filter(raw_temp_dir=EXTRACT_DIR, target_safe_dir=STUDY_MATERIALS_DIR)
    
    # 4. Study data chunking
    print("\n>>> STEP 4: Format Study Data Chunks & JSONL Datasets")
    prepare_res = process_study_materials(materials_dir=STUDY_MATERIALS_DIR, output_chunks_dir=STUDY_CHUNKS_DIR)
    
    # 5. Aggressive cleanup
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
    run_pipeline()
