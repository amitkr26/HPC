#!/usr/bin/env python3
"""
Automated AI Privacy Filter and Document Triage
Target Environment: Param Rudra HPC Cluster
Destination: ~/bdw-llm/training/study_materials/

Strict Privacy Protocol:
- If a file matches ANY Danger keywords, has a media extension, or is ambiguous,
  it is IMMEDIATELY DELETED using os.remove().
- Only files explicitly verified as educational / study materials are preserved.
"""

import os
import re
import sys
import shutil
import argparse
from typing import Dict, List, Tuple

# Safe Study Keywords (case-insensitive)
SAFE_KEYWORDS = [
    "chapter", "lecture", "syllabus", "vlsi", "hardware", 
    "notes", "exam", "tutorial", "assignment", "unit",
    "semiconductor", "verilog", "vhdl", "cmos", "microelectronics",
    "fpga", "timing", "clock", "memory", "gate", "circuit",
    "schematic", "architecture", "digital", "analog", "processor"
]

# Danger / Sensitive Personal Keywords (case-insensitive)
DANGER_KEYWORDS = [
    "bank", "statement", "passport", "id", "invoice", 
    "personal", "photo", "image", "receipt", "aadhar", 
    "pan", "confidential", "salary", "tax", "credit",
    "debit", "license", "voter", "medical", "bill",
    "payslip", "resume", "cv", "aadhaar"
]

# Media extensions to delete immediately without reading
MEDIA_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".svg",
    ".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".webm",
    ".mp3", ".wav", ".aac", ".ogg", ".flac", ".m4a",
    ".exe", ".bin", ".dmg", ".iso", ".apk"
}

DOCUMENT_EXTENSIONS = {
    ".txt", ".pdf", ".docx", ".doc", ".md", ".rtf", 
    ".py", ".v", ".sv", ".c", ".cpp", ".h", ".json", ".csv"
}

def matches_keyword_strict(text: str, keywords: List[str]) -> bool:
    """Delimiter-aware keyword matching preventing accidental substring collisions (e.g. 'id' in 'divider')."""
    for kw in keywords:
        # Match standalone keyword delimited by non-alphanumeric chars or boundaries
        pattern = r"(?:^|[^a-zA-Z0-9])" + re.escape(kw) + r"(?:[^a-zA-Z0-9]|$)"
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

def extract_first_words(file_path: str, max_words: int = 50) -> str:
    """Safely extract the first ~50 words from supported document types."""
    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    
    try:
        if ext in [".txt", ".md", ".py", ".v", ".sv", ".c", ".cpp", ".h", ".json", ".csv", ".rtf"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(4096)
                words = content.split()[:max_words]
                text = " ".join(words)
                
        elif ext == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            if reader.pages:
                page_text = reader.pages[0].extract_text() or ""
                words = page_text.split()[:max_words]
                text = " ".join(words)
                
        elif ext in [".docx", ".doc"]:
            import docx
            doc = docx.Document(file_path)
            all_paras = []
            for p in doc.paragraphs:
                if p.text.strip():
                    all_paras.append(p.text)
                if len(" ".join(all_paras).split()) >= max_words:
                    break
            words = " ".join(all_paras).split()[:max_words]
            text = " ".join(words)
            
    except Exception as e:
        text = ""
        
    return text.lower()

def classify_and_filter(raw_temp_dir: str, target_safe_dir: str) -> Dict[str, any]:
    """Iterate through extracted files, strictly filter personal data, and preserve only verified study materials."""
    raw_temp_dir = os.path.abspath(raw_temp_dir)
    target_safe_dir = os.path.abspath(target_safe_dir)
    os.makedirs(target_safe_dir, exist_ok=True)
    
    stats = {
        "total_scanned": 0,
        "safe_retained": 0,
        "danger_deleted": 0,
        "media_deleted": 0,
        "ambiguous_deleted": 0,
        "safe_files": [],
        "deleted_audit": []
    }
    
    # Collect all files recursively
    all_files = []
    for root, _, files in os.walk(raw_temp_dir):
        for f in files:
            all_files.append(os.path.join(root, f))
            
    stats["total_scanned"] = len(all_files)
    print(f"[PRIVACY_FILTER] Analyzing {len(all_files)} extracted files under strict zero-leakage rules...")
    
    for file_path in all_files:
        if not os.path.exists(file_path):
            continue
            
        filename = os.path.basename(file_path)
        filename_lower = filename.lower()
        ext = os.path.splitext(filename)[1].lower()
        
        # 1. Rule: Media extension check -> Immediate Hard Delete
        if ext in MEDIA_EXTENSIONS:
            os.remove(file_path)
            stats["media_deleted"] += 1
            stats["deleted_audit"].append({"type": "MEDIA_DELETED", "filename": filename})
            print(f"[DELETE: MEDIA] Purged media file: {filename}")
            continue
            
        # 2. Rule: Danger keywords in filename -> Immediate Hard Delete
        if matches_keyword_strict(filename_lower, DANGER_KEYWORDS):
            os.remove(file_path)
            stats["danger_deleted"] += 1
            stats["deleted_audit"].append({"type": "DANGER_KEYWORD_NAME", "filename": filename})
            print(f"[DELETE: PRIVACY] Purged sensitive filename: {filename}")
            continue
            
        # 3. Rule: Non-document unrecognized extension -> Immediate Hard Delete (Ambiguous)
        if ext not in DOCUMENT_EXTENSIONS:
            os.remove(file_path)
            stats["ambiguous_deleted"] += 1
            stats["deleted_audit"].append({"type": "UNKNOWN_EXTENSION", "filename": filename})
            print(f"[DELETE: UNKNOWN] Purged non-document file: {filename}")
            continue
            
        # 4. Extract first 50 words of content
        content_sample = extract_first_words(file_path, max_words=50)
        
        # 5. Rule: Danger keywords in content -> Immediate Hard Delete
        if matches_keyword_strict(content_sample, DANGER_KEYWORDS):
            os.remove(file_path)
            stats["danger_deleted"] += 1
            stats["deleted_audit"].append({"type": "DANGER_KEYWORD_CONTENT", "filename": filename})
            print(f"[DELETE: PRIVACY] Purged file matching sensitive keywords in body: {filename}")
            continue
            
        # 6. Rule: Safe Study Keywords verification (in filename OR content)
        has_safe_in_name = matches_keyword_strict(filename_lower, SAFE_KEYWORDS)
        has_safe_in_content = matches_keyword_strict(content_sample, SAFE_KEYWORDS)
        
        if has_safe_in_name or has_safe_in_content:
            # Verified safe study material -> Relocate to study_materials
            dest_path = os.path.join(target_safe_dir, filename)
            base, extension = os.path.splitext(filename)
            counter = 1
            while os.path.exists(dest_path):
                dest_path = os.path.join(target_safe_dir, f"{base}_{counter}{extension}")
                counter += 1
                
            shutil.move(file_path, dest_path)
            stats["safe_retained"] += 1
            stats["safe_files"].append(os.path.basename(dest_path))
            print(f"[RETAIN: STUDY] Verified educational material preserved: {os.path.basename(dest_path)}")
        else:
            # 7. Rule: Ambiguous content (does not match safe study criteria) -> Strict Deletion
            os.remove(file_path)
            stats["ambiguous_deleted"] += 1
            stats["deleted_audit"].append({"type": "AMBIGUOUS_NON_STUDY", "filename": filename})
            print(f"[DELETE: AMBIGUOUS] Purged unverified file: {filename}")
            
    print("\n[PRIVACY_FILTER] Triage Summary:")
    print(f"  Total Scanned:      {stats['total_scanned']}")
    print(f"  Verified Study:     {stats['safe_retained']} files preserved")
    print(f"  Sensitive Deleted:  {stats['danger_deleted']} files purged")
    print(f"  Media Deleted:      {stats['media_deleted']} files purged")
    print(f"  Ambiguous Deleted:  {stats['ambiguous_deleted']} files purged")
    
    return stats

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Strict AI Privacy Filter and Document Triage.")
    parser.add_argument("--raw_dir", default=os.path.expanduser("~/bdw-llm/raw_zip_temp"), help="Raw extracted directory")
    parser.add_argument("--dest_dir", default=os.path.expanduser("~/bdw-llm/training/study_materials"), help="Verified study directory")
    args = parser.parse_args()
    
    res = classify_and_filter(args.raw_dir, args.dest_dir)
