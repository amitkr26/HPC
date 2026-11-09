#!/usr/bin/env python3
"""
Secure Google Drive Archive Downloader and Extractor
Target Environment: Param Rudra HPC Cluster
Isolated Extraction Path: ~/bdw-llm/raw_zip_temp/
Supported Formats: ZIP, TAR, RAR (via standalone unrar)
"""

import os
import re
import sys
import shutil
import zipfile
import tarfile
import subprocess
import argparse
from typing import List, Dict
import requests
import gdown

RAW_TEMP_DIR = os.path.expanduser("~/bdw-llm/raw_zip_temp")

def extract_file_id(input_str: str) -> str:
    """Extract standard Google Drive File ID from URL or raw ID."""
    input_str = input_str.strip().strip("'\"")
    
    patterns = [
        r"drive\.google\.com/file/d/([a-zA-Z0-9_-]+)",
        r"drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)",
        r"drive\.google\.com/uc\?.*id=([a-zA-Z0-9_-]+)",
        r"id=([a-zA-Z0-9_-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, input_str)
        if match:
            return match.group(1)
            
    if re.fullmatch(r"[a-zA-Z0-9_-]{20,50}", input_str):
        return input_str
        
    raise ValueError(f"Could not parse valid Google Drive File ID from: {input_str}")

def is_rar_archive(file_path: str) -> bool:
    """Check if file starts with RAR signature bytes."""
    try:
        with open(file_path, "rb") as f:
            header = f.read(8)
            return header.startswith(b"Rar!\x1a\x07")
    except Exception:
        return False

def extract_rar(archive_path: str, destination_dir: str) -> List[str]:
    """Extract RAR archive using standalone unrar binary."""
    unrar_bin = shutil.which("unrar") or os.path.expanduser("~/bin/unrar")
    if not os.path.exists(unrar_bin):
        raise FileNotFoundError(f"unrar binary not found at {unrar_bin}")
        
    print(f"[EXTRACTOR] Using unrar binary: {unrar_bin}")
    cmd = [unrar_bin, "x", "-o+", "-y", archive_path, destination_dir]
    if not cmd[-1].endswith(os.sep):
        cmd[-1] += os.sep
        
    print(f"[EXTRACTOR] Running unrar command...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode not in [0, 1]:
        print(f"[EXTRACTOR] unrar stderr: {res.stderr[:500]}")
        raise RuntimeError(f"unrar failed with code {res.returncode}")
        
    extracted_files = []
    for root, _, files in os.walk(destination_dir):
        for f in files:
            full_path = os.path.join(root, f)
            if full_path != archive_path:
                extracted_files.append(full_path)
    return extracted_files

def download_and_extract(gdrive_input: str, target_dir: str = RAW_TEMP_DIR) -> dict:
    """Download Google Drive archive, extract to isolated temporary directory, and unlink archive."""
    file_id = extract_file_id(gdrive_input)
    print(f"[EXTRACTOR] Parsed Google Drive File ID: {file_id}")
    
    os.makedirs(target_dir, exist_ok=True)
    temp_archive_path = os.path.join(target_dir, "input_archive.zip")
    
    # Clean up stale placeholder if present
    if os.path.exists(temp_archive_path) and os.path.getsize(temp_archive_path) < 100000:
        print(f"[EXTRACTOR] Removing stale placeholder ({os.path.getsize(temp_archive_path)} bytes)")
        os.remove(temp_archive_path)
        
    download_url = f"https://drive.google.com/uc?id={file_id}"
    print(f"[EXTRACTOR] Initiating/resuming secure download via gdown from {download_url}...")
    
    out_path = gdown.download(download_url, output=temp_archive_path, quiet=False, resume=True)
    
    if not out_path or not os.path.exists(temp_archive_path) or os.path.getsize(temp_archive_path) < 1024:
        raise RuntimeError(f"Failed to download valid archive from Google Drive (ID: {file_id}).")
        
    file_size_mb = os.path.getsize(temp_archive_path) / (1024 * 1024)
    file_size_gb = file_size_mb / 1024
    print(f"[EXTRACTOR] Downloaded archive successfully ({file_size_gb:.2f} GB / {file_size_mb:.1f} MB).")
    
    extracted_files = []
    print(f"[EXTRACTOR] Extracting archive contents into isolated sandbox: {target_dir}")
    
    if zipfile.is_zipfile(temp_archive_path):
        print("[EXTRACTOR] Detected ZIP format.")
        with zipfile.ZipFile(temp_archive_path, "r") as zf:
            zf.extractall(target_dir)
            for zip_info in zf.infolist():
                if not zip_info.is_dir():
                    extracted_files.append(os.path.join(target_dir, zip_info.filename))
                    
    elif tarfile.is_tarfile(temp_archive_path):
        print("[EXTRACTOR] Detected TAR format.")
        with tarfile.open(temp_archive_path, "r:*") as tf:
            tf.extractall(target_dir)
            for member in tf.getmembers():
                if member.isfile():
                    extracted_files.append(os.path.join(target_dir, member.name))
                    
    elif is_rar_archive(temp_archive_path):
        print("[EXTRACTOR] Detected RAR format. Extracting via unrar...")
        extracted_files = extract_rar(temp_archive_path, target_dir)
        
    else:
        print("[EXTRACTOR] Archive header ambiguous. Attempting unrar fallback...")
        try:
            extracted_files = extract_rar(temp_archive_path, target_dir)
        except Exception as e:
            raise ValueError(f"Downloaded file ({file_size_gb:.2f} GB) could not be extracted as ZIP, TAR, or RAR: {e}")
            
    # Immediate removal of the source archive container and any partial artifacts
    if os.path.exists(temp_archive_path):
        os.remove(temp_archive_path)
        print("[EXTRACTOR] Source archive container securely unlinked from disk.")
        
    for item in os.listdir(target_dir):
        if item.endswith(".part"):
            try:
                os.remove(os.path.join(target_dir, item))
            except Exception:
                pass
                
    print(f"[EXTRACTOR] Extraction complete. Total raw files extracted: {len(extracted_files)}")
    return {
        "status": "success",
        "file_id": file_id,
        "target_dir": target_dir,
        "total_files": len(extracted_files),
        "files": extracted_files
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download and extract Google Drive archive to isolated cluster sandbox.")
    parser.add_argument("gdrive_input", help="Google Drive shared link or File ID")
    parser.add_argument("--target_dir", default=RAW_TEMP_DIR, help="Destination directory for raw extraction")
    args = parser.parse_args()
    
    res = download_and_extract(args.gdrive_input, args.target_dir)
    print(f"[RESULT] Extracted {res['total_files']} files to {res['target_dir']}")
