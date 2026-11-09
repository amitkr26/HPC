#!/usr/bin/env python3
"""
Study Material Parser & Vector RAG / QLoRA Chunker
Target Environment: Param Rudra HPC Cluster
Input Directory:  ~/bdw-llm/training/study_materials/
Output Directory: ~/bdw-llm/training/study_chunks/
"""

import os
import re
import sys
import json
import shutil
import argparse
from typing import List, Dict

CHUNK_SIZE = 900
CHUNK_OVERLAP = 150

def parse_full_text(file_path: str) -> str:
    """Extract complete text content from PDF, DOCX, TXT, or code files."""
    ext = os.path.splitext(file_path)[1].lower()
    full_text = ""
    
    try:
        if ext in [".txt", ".md", ".py", ".v", ".sv", ".c", ".cpp", ".h", ".json", ".csv"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                full_text = f.read()
                
        elif ext == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            pages_text = []
            for idx, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    pages_text.append(f"[Page {idx + 1}]\n{text.strip()}")
            full_text = "\n\n".join(pages_text)
            
        elif ext in [".docx", ".doc"]:
            import docx
            doc = docx.Document(file_path)
            paras = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            full_text = "\n\n".join(paras)
            
    except Exception as e:
        print(f"[PARSER_WARNING] Error reading {os.path.basename(file_path)}: {e}")
        
    # Clean whitespace and control characters
    full_text = re.sub(r"\r\n", "\n", full_text)
    full_text = re.sub(r"\n{3,}", "\n\n", full_text)
    full_text = re.sub(r"[ \t]{2,}", " ", full_text)
    return full_text.strip()

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split clean text into overlapping chunks for semantic retrieval."""
    if len(text) <= chunk_size:
        return [text] if text.strip() else []
        
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        if end >= text_len:
            chunk = text[start:].strip()
            if chunk:
                chunks.append(chunk)
            break
            
        # Try finding paragraph or sentence boundary
        split_pos = text.rfind("\n\n", start, end)
        if split_pos == -1 or split_pos < start + (chunk_size // 2):
            split_pos = text.rfind(". ", start, end)
            if split_pos != -1:
                split_pos += 1
                
        if split_pos == -1 or split_pos < start + (chunk_size // 2):
            split_pos = end
            
        chunk = text[start:split_pos].strip()
        if chunk:
            chunks.append(chunk)
            
        start = max(start + 1, split_pos - overlap)
        
    return chunks

def process_study_materials(materials_dir: str, output_chunks_dir: str) -> Dict[str, any]:
    """Process all verified study materials into clean .txt chunks and RAG/QLoRA jsonl artifacts."""
    materials_dir = os.path.abspath(materials_dir)
    output_chunks_dir = os.path.abspath(output_chunks_dir)
    os.makedirs(output_chunks_dir, exist_ok=True)
    
    txt_chunks_dir = os.path.join(output_chunks_dir, "txt_chunks")
    os.makedirs(txt_chunks_dir, exist_ok=True)
    
    rag_jsonl_path = os.path.join(output_chunks_dir, "rag_documents.jsonl")
    qlora_jsonl_path = os.path.join(output_chunks_dir, "qlora_study_dataset.jsonl")
    
    total_docs = 0
    total_chunks = 0
    rag_records = []
    qlora_records = []
    
    files = [f for f in os.listdir(materials_dir) if os.path.isfile(os.path.join(materials_dir, f))]
    print(f"[PREPARE] Formatting {len(files)} verified study materials into vector RAG chunks...")
    
    for filename in sorted(files):
        file_path = os.path.join(materials_dir, filename)
        content = parse_full_text(file_path)
        if not content or len(content) < 50:
            print(f"[SKIP] Minimal or empty content in: {filename}")
            continue
            
        total_docs += 1
        chunks = chunk_text(content, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
        base_name = os.path.splitext(filename)[0]
        
        for idx, chunk in enumerate(chunks):
            total_chunks += 1
            chunk_filename = f"{base_name}_chunk_{idx + 1:04d}.txt"
            chunk_path = os.path.join(txt_chunks_dir, chunk_filename)
            
            with open(chunk_path, "w", encoding="utf-8") as cf:
                cf.write(f"Source: {filename} | Chunk: {idx + 1}/{len(chunks)}\n\n{chunk}\n")
                
            # Record for Supabase Vector RAG
            rag_records.append({
                "source": filename,
                "chunk_index": idx + 1,
                "total_chunks": len(chunks),
                "content": chunk,
                "metadata": {
                    "source": filename,
                    "domain": "deep_tech_study_materials",
                    "chunk_id": f"{base_name}_{idx + 1}"
                }
            })
            
            # Format as ChatML pair for QLoRA fine-tuning
            qlora_records.append({
                "messages": [
                    {"role": "system", "content": "You are BerojgarDegreeWala AI, India's deep-tech hardware career and research intelligence model."},
                    {"role": "user", "content": f"Summarize and explain the technical principles covered in {filename} regarding:\n{chunk[:120]}..."},
                    {"role": "assistant", "content": chunk}
                ]
            })
            
    # Write JSONL outputs
    with open(rag_jsonl_path, "w", encoding="utf-8") as rf:
        for rec in rag_records:
            rf.write(json.dumps(rec, ensure_ascii=False) + "\n")
            
    with open(qlora_jsonl_path, "w", encoding="utf-8") as qf:
        for rec in qlora_records:
            qf.write(json.dumps(rec, ensure_ascii=False) + "\n")
            
    print(f"\n[PREPARE] Formatting Complete:")
    print(f"  Processed Documents: {total_docs}")
    print(f"  Generated Chunks:    {total_chunks}")
    print(f"  Saved TXT Chunks:    {txt_chunks_dir}")
    print(f"  Vector RAG JSONL:    {rag_jsonl_path}")
    print(f"  QLoRA Dataset JSONL: {qlora_jsonl_path}")
    
    return {
        "processed_documents": total_docs,
        "total_chunks": total_chunks,
        "rag_jsonl": rag_jsonl_path,
        "qlora_jsonl": qlora_jsonl_path
    }

def purge_raw_temp(raw_temp_dir: str):
    """Aggressively wipe the raw temporary extraction directory from cluster storage."""
    raw_temp_dir = os.path.abspath(raw_temp_dir)
    if os.path.exists(raw_temp_dir):
        print(f"[CLEANUP] Executing aggressive purge of temporary sandbox: {raw_temp_dir}")
        shutil.rmtree(raw_temp_dir, ignore_errors=True)
        if not os.path.exists(raw_temp_dir):
            print("[CLEANUP] CONFIRMED: Raw extraction folder and all personal remnants completely erased from disk.")
        else:
            print("[CLEANUP_WARNING] Directory still present, attempting force unlink...")
            for root, dirs, files in os.walk(raw_temp_dir, topdown=False):
                for f in files:
                    try: os.remove(os.path.join(root, f))
                    except: pass
                for d in dirs:
                    try: os.rmdir(os.path.join(root, d))
                    except: pass
            shutil.rmtree(raw_temp_dir, ignore_errors=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse verified study materials into clean RAG chunks.")
    parser.add_argument("--materials_dir", default=os.path.expanduser("~/bdw-llm/training/study_materials"), help="Directory containing verified study materials")
    parser.add_argument("--chunks_dir", default=os.path.expanduser("~/bdw-llm/training/study_chunks"), help="Destination for clean chunks")
    parser.add_argument("--cleanup_raw", default=os.path.expanduser("~/bdw-llm/raw_zip_temp"), help="Raw sandbox to purge")
    args = parser.parse_args()
    
    stats = process_study_materials(args.materials_dir, args.chunks_dir)
    if args.cleanup_raw:
        purge_raw_temp(args.cleanup_raw)
