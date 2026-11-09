#!/usr/bin/env python3
"""
End-to-End Orchestrator for Secure Ingestion, Privacy Filtering, and Dataset Preparation
Target Environment: Param Rudra HPC Cluster
"""

import os
import sys
import argparse
import time

# Ensure current directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from download_and_extract import download_and_extract
from data_triage import classify_and_filter
from prepare_study_data import process_study_materials, purge_raw_temp

RAW_TEMP_DIR = os.path.expanduser("~/bdw-llm/raw_zip_temp")
STUDY_MATERIALS_DIR = os.path.expanduser("~/bdw-llm/training/study_materials")
STUDY_CHUNKS_DIR = os.path.expanduser("~/bdw-llm/training/study_chunks")

def run_end_to_end(gdrive_input: str):
    start_time = time.time()
    print("=" * 70)
    print("=== BEROJGARDEGREEWALA: SECURE DATA INGESTION & PRIVACY PIPELINE ===")
    print("=" * 70)
    
    # Step 1: Secure Download and Extraction
    print("\n>>> STEP 1: Secure Download & Isolation")
    extract_res = download_and_extract(gdrive_input, target_dir=RAW_TEMP_DIR)
    print(f"Extraction completed successfully into sandbox: {RAW_TEMP_DIR}")
    
    # Step 2: Automated AI Privacy Filter & Triage
    print("\n>>> STEP 2: Strict Privacy Filtering & Document Triage")
    triage_res = classify_and_filter(raw_temp_dir=RAW_TEMP_DIR, target_safe_dir=STUDY_MATERIALS_DIR)
    
    # Step 3: Parse and Vector/QLoRA Chunk Generation
    print("\n>>> STEP 3: Study Data Parsing & Dataset Chunking")
    prepare_res = process_study_materials(materials_dir=STUDY_MATERIALS_DIR, output_chunks_dir=STUDY_CHUNKS_DIR)
    
    # Step 4: Aggressive Sandbox Purge
    print("\n>>> STEP 4: Aggressive Sandbox Purge")
    purge_raw_temp(raw_temp_dir=RAW_TEMP_DIR)
    
    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print("=== FINAL EXECUTION REPORT ===")
    print("=" * 70)
    print(f"Execution Time:          {elapsed:.2f} seconds")
    print(f"Total Files Scanned:     {triage_res['total_scanned']}")
    print(f"Verified Study Preserved:{triage_res['safe_retained']}")
    print(f"Sensitive Purged:        {triage_res['danger_deleted']} (hard deleted with os.remove)")
    print(f"Media Purged:            {triage_res['media_deleted']} (hard deleted with os.remove)")
    print(f"Ambiguous Purged:        {triage_res['ambiguous_deleted']} (hard deleted with os.remove)")
    print(f"Total Chunks Generated:  {prepare_res['total_chunks']}")
    print(f"Clean TXT Chunks Dir:    {os.path.join(STUDY_CHUNKS_DIR, 'txt_chunks')}")
    print(f"Supabase RAG JSONL:      {prepare_res['rag_jsonl']}")
    print(f"QLoRA Dataset JSONL:     {prepare_res['qlora_jsonl']}")
    print(f"Temporary Sandbox Purge: CONFIRMED DELETED ({not os.path.exists(RAW_TEMP_DIR)})")
    print("=" * 70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="End-to-end secure privacy filtering & study chunking pipeline.")
    parser.add_argument("gdrive_input", nargs="?", default="1la9xhtkfQiEGGdDwHz41Lu5JyWWY942z", help="Google Drive link or File ID")
    args = parser.parse_args()
    
    run_end_to_end(args.gdrive_input)
