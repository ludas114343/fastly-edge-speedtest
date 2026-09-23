#!/usr/bin/env python3
"""
Raw Results Formatter and SHA-256 Manifest Generator
Converts results/china-<carrier>/<ts>.json to results/raw/<ts>/<carrier>.jsonl with manifest.json
Zero em-dash and zero en-dash policy.
"""

import os
import sys
import json
import hashlib

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(REPO_DIR, "results")
RAW_BASE_DIR = os.path.join(RESULTS_DIR, "raw")

def calculate_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def process_run(ts):
    run_dir = os.path.join(RAW_BASE_DIR, ts)
    os.makedirs(run_dir, exist_ok=True)
    
    carriers = [
        ("china-telecom", "telecom.jsonl"),
        ("china-unicom", "unicom.jsonl"),
        ("china-mobile", "mobile.jsonl")
    ]
    
    files_meta = {}
    total_records = 0
    
    for dir_name, out_name in carriers:
        in_path = os.path.join(RESULTS_DIR, dir_name, f"{ts}.json")
        out_path = os.path.join(run_dir, out_name)
        
        if not os.path.exists(in_path):
            print(f"[WARN] Input path not found: {in_path}")
            continue
            
        with open(in_path, "r", encoding="utf-8") as f:
            records = json.load(f)
            
        with open(out_path, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
                
        rec_count = len(records)
        total_records += rec_count
        sha256 = calculate_sha256(out_path)
        
        files_meta[out_name] = {
            "records": rec_count,
            "sha256": sha256,
            "size_bytes": os.path.getsize(out_path)
        }
        print(f"[+] Formatted {out_name}: {rec_count} records, SHA256: {sha256[:16]}...")
        
    manifest = {
        "run_id": ts,
        "format": "jsonl",
        "total_records": total_records,
        "files": files_meta,
        "created_at": "2026-09-22T13:33:27Z"
    }
    
    manifest_path = os.path.join(run_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        
    print(f"[+] Manifest created: {manifest_path}")

if __name__ == "__main__":
    for ts in ["20260922_132834", "20260922_133327"]:
        print(f"--- Processing Run ID: {ts} ---")
        process_run(ts)
