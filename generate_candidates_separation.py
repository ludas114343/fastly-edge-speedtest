#!/usr/bin/env python3
"""
Candidate Pool 3-Tier Separation Pipeline
Separates candidate endpoints into:
- candidates/raw.jsonl
- candidates/deduped.jsonl
- candidates/rejected.jsonl

Strict red lines:
- Zero em-dash (\u2014) and zero en-dash (\u2013).
- Zero HK references.
- Zero fake constants.
"""

import os
import sys
import json
import glob

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
CANDIDATES_DIR = os.path.join(REPO_DIR, "candidates")
FORENSICS_DIR = os.path.join(REPO_DIR, "forensics", "legacy")
EVIDENCE_DIR = os.path.join(REPO_DIR, "evidence", "deployments")

os.makedirs(CANDIDATES_DIR, exist_ok=True)

# Load retired UUID if present
UUID_CONFIG_PATH = os.path.join(REPO_DIR, "uuid_config.json")
retired_uuid = ""
if os.path.exists(UUID_CONFIG_PATH):
    with open(UUID_CONFIG_PATH, "r", encoding="utf-8") as f:
        uuid_cfg = json.load(f)
    retired_uuid = uuid_cfg.get("retired_uuid", "")

def run_separation():
    # 1. Ingest raw candidates
    candidate_files = sorted(glob.glob(os.path.join(FORENSICS_DIR, "*candidates.json")))
    if not candidate_files:
        candidate_files = sorted(glob.glob(os.path.join(REPO_DIR, "*candidates.json")))
    
    raw_candidates = []
    for cfile in candidate_files:
        with open(cfile, "r", encoding="utf-8") as f:
            pool = json.load(f)
            raw_candidates.extend(pool)

    # 2. Write raw.jsonl
    raw_jsonl_path = os.path.join(CANDIDATES_DIR, "raw.jsonl")
    with open(raw_jsonl_path, "w", encoding="utf-8") as f_raw:
        for c in raw_candidates:
            f_raw.write(json.dumps(c, ensure_ascii=False) + "\n")

    # 3. Deduplicate and reject
    seen_routes = set()
    deduped_candidates = []
    rejected_candidates = []

    for c in raw_candidates:
        cid = c.get("candidate_id", "unknown")
        provider = c.get("provider", "unknown")
        server = c.get("server") or c.get("host") or ""
        port = int(c.get("port", 443))
        sni = c.get("sni") or server
        path = c.get("path", "/")
        target_network = c.get("target_network", "china-telecom")
        region = c.get("region", "UNKNOWN")

        # Clean path: strip synthetic query iterations
        clean_path = path.split("?s=")[0].split("&s=")[0]

        # Rejection checks:
        # Check 1: HK / Hong Kong red line
        if "HK" in region or "Hong Kong" in region or "香港" in region or "\U0001f1ed\U0001f1f0" in region:
            rejected_candidates.append({
                "candidate_id": cid,
                "provider": provider,
                "server": server,
                "path": path,
                "target_network": target_network,
                "rejection_reason": "RED_LINE_HK_REGION_FORBIDDEN",
                "rejection_category": "GEOGRAPHIC_POLICY"
            })
            continue

        # Check 2: Retired UUID
        if retired_uuid and (retired_uuid in path or retired_uuid in cid):
            rejected_candidates.append({
                "candidate_id": cid,
                "provider": provider,
                "server": server,
                "path": path,
                "target_network": target_network,
                "rejection_reason": "RETIRED_UUID_DETECTED",
                "rejection_category": "SECURITY_POLICY"
            })
            continue

        # Check 3: Invalid server or port
        if not server or port <= 0:
            rejected_candidates.append({
                "candidate_id": cid,
                "provider": provider,
                "server": server,
                "path": path,
                "target_network": target_network,
                "rejection_reason": "INVALID_SERVER_OR_PORT",
                "rejection_category": "VALIDATION"
            })
            continue

        # Check 4: Route Deduplication Key
        route_key = (provider, server, port, sni, clean_path, target_network)
        if route_key in seen_routes:
            rejected_candidates.append({
                "candidate_id": cid,
                "provider": provider,
                "server": server,
                "port": port,
                "path": path,
                "target_network": target_network,
                "rejection_reason": "DUPLICATE_SYNTHETIC_ROUTE",
                "rejection_category": "DEDUPLICATION"
            })
        else:
            seen_routes.add(route_key)
            accepted_item = dict(c)
            accepted_item["clean_path"] = clean_path
            accepted_item["dedup_key"] = f"{provider}:{server}:{port}:{clean_path}:{target_network}"
            accepted_item["dedup_status"] = "ACCEPTED"
            deduped_candidates.append(accepted_item)

    # 4. Write deduped.jsonl
    deduped_jsonl_path = os.path.join(CANDIDATES_DIR, "deduped.jsonl")
    with open(deduped_jsonl_path, "w", encoding="utf-8") as f_dedup:
        for c in deduped_candidates:
            f_dedup.write(json.dumps(c, ensure_ascii=False) + "\n")

    # 5. Write rejected.jsonl
    rejected_jsonl_path = os.path.join(CANDIDATES_DIR, "rejected.jsonl")
    with open(rejected_jsonl_path, "w", encoding="utf-8") as f_rej:
        for c in rejected_candidates:
            f_rej.write(json.dumps(c, ensure_ascii=False) + "\n")

    # 6. Count deployed endpoints
    summary_path = os.path.join(EVIDENCE_DIR, "summary.json")
    deployed_hosts = set()
    if os.path.exists(summary_path):
        with open(summary_path, "r", encoding="utf-8") as f:
            sum_data = json.load(f)
        for p_name, p_info in sum_data.get("platforms", {}).items():
            if "domain" in p_info:
                deployed_hosts.add(p_info["domain"])
            if "accounts" in p_info:
                for acc in p_info["accounts"]:
                    if "domain" in acc:
                        deployed_hosts.add(acc["domain"])
            if "backends_configured" in p_info:
                for b in p_info["backends_configured"]:
                    if "(" in b and ")" in b:
                        host_part = b.split("(")[1].split(")")[0].split(",")[0].strip()
                        deployed_hosts.add(host_part)
    
    # Also add known canonical hosts for deployed platforms
    deployed_hosts.update([
        "theecyezvuzkflwikxwr.supabase.co", "gwgiogtgdyrqlexcdjqm.supabase.co",
        "sb.ruoyemu.asia", "sb2.ruoyemu.asia", "sb3.ruoyemu.asia", "sb4.ruoyemu.asia",
        "w-la.ruoyemu.asia", "w-fr.ruoyemu.asia", "w-east.ruoyemu.asia", "w-us.ruoyemu.asia",
        "w-ca.ruoyemu.asia", "w-de.ruoyemu.asia", "w-sg.ruoyemu.asia", "wasmer.ruoyemu.asia",
        "nf-node.ruoyemu.asia", "nf.ruoyemu.asia", "nf-sub.ruoyemu.asia",
        "net.ruoyemu.asia", "fastly.ruoyemu.asia", "ruoyemu.global.ssl.fastly.net",
        "edgeone-proxy-zone-3td4th92xk0e-1463384265.eo-edgefunctions1.com", "eo.ruoyemu.asia"
    ])

    deployed_count = sum(1 for c in deduped_candidates if (c.get("server") in deployed_hosts or c.get("host") in deployed_hosts))

    print("==================================================")
    print("Candidate Pool 3-Tier Separation Summary")
    print("==================================================")
    print(f"Raw candidates count:       {len(raw_candidates)}")
    print(f"Deduped candidates count:   {len(deduped_candidates)}")
    print(f"Rejected candidates count:  {len(rejected_candidates)}")
    print(f"Deployed candidates count:  {deployed_count}")
    print(f"Check sum (dedup+rej==raw): {len(deduped_candidates) + len(rejected_candidates) == len(raw_candidates)}")
    print("==================================================")

if __name__ == "__main__":
    run_separation()
