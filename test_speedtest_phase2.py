#!/usr/bin/env python3
"""
Comprehensive Verification Suite for Speedtest Agent Phase 2 Deliverables
Validates all machine-checkable criteria in taskcards/phase2/speedtest-agent.md
"""

import os
import sys
import json
import hashlib
import statistics

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
RUN_ID = "20260922_152129"

def calculate_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def test_all():
    print("==================================================")
    print("Starting Comprehensive Verification Suite for Phase 2")
    print(f"Run ID: {RUN_ID}")
    print("==================================================")

    # 1. Verify existence of all 8 required deliverables
    required_files = [
        os.path.join(REPO_DIR, "candidates", "raw.jsonl"),
        os.path.join(REPO_DIR, "candidates", "deduped.jsonl"),
        os.path.join(REPO_DIR, "candidates", "rejected.jsonl"),
        os.path.join(REPO_DIR, "results", "route-proof", f"{RUN_ID}.json"),
        os.path.join(REPO_DIR, "results", "raw", RUN_ID, "telecom.jsonl"),
        os.path.join(REPO_DIR, "results", "raw", RUN_ID, "unicom.jsonl"),
        os.path.join(REPO_DIR, "results", "raw", RUN_ID, "mobile.jsonl"),
        os.path.join(REPO_DIR, "results", "raw", RUN_ID, "manifest.json"),
    ]

    for rf in required_files:
        assert os.path.exists(rf), f"Missing required deliverable: {rf}"
        assert os.path.getsize(rf) > 0, f"Empty required deliverable: {rf}"
        print(f"[PASS] File exists and non-empty: {os.path.relpath(rf, REPO_DIR)} ({os.path.getsize(rf)} bytes)")

    # 2. Candidate pool counts and checksum
    raw_path = os.path.join(REPO_DIR, "candidates", "raw.jsonl")
    dedup_path = os.path.join(REPO_DIR, "candidates", "deduped.jsonl")
    rej_path = os.path.join(REPO_DIR, "candidates", "rejected.jsonl")

    with open(raw_path, "r", encoding="utf-8") as f:
        raw_lines = [json.loads(l) for l in f if l.strip()]
    with open(dedup_path, "r", encoding="utf-8") as f:
        dedup_lines = [json.loads(l) for l in f if l.strip()]
    with open(rej_path, "r", encoding="utf-8") as f:
        rej_lines = [json.loads(l) for l in f if l.strip()]

    raw_cnt = len(raw_lines)
    dedup_cnt = len(dedup_lines)
    rej_cnt = len(rej_lines)

    assert raw_cnt == 6120, f"Expected 6120 raw candidates, got {raw_cnt}"
    assert dedup_cnt == 348, f"Expected 348 deduped candidates, got {dedup_cnt}"
    assert rej_cnt == 5772, f"Expected 5772 rejected candidates, got {rej_cnt}"
    assert dedup_cnt + rej_cnt == raw_cnt, "Mathematical invariant failure: deduped + rejected != raw"
    print(f"[PASS] Candidate pools: raw={raw_cnt}, deduped={dedup_cnt}, rejected={rej_cnt} (Check sum = {raw_cnt})")

    # 3. Verify Route Proof
    proof_path = os.path.join(REPO_DIR, "results", "route-proof", f"{RUN_ID}.json")
    with open(proof_path, "r", encoding="utf-8") as f:
        proof = json.load(f)
    assert proof["run_id"] == RUN_ID, "Route proof run_id mismatch"
    assert proof["overall_verification"] == "PASS", "Route proof verification not PASS"
    carriers = proof["carriers"]
    assert "china-telecom" in carriers and carriers["china-telecom"]["status"] == "VERIFIED" and carriers["china-telecom"]["echo_asn"] == "AS4134"
    assert "china-unicom" in carriers and carriers["china-unicom"]["status"] == "VERIFIED" and carriers["china-unicom"]["echo_asn"] == "AS4837"
    assert "china-mobile" in carriers and carriers["china-mobile"]["status"] == "VERIFIED" and carriers["china-mobile"]["echo_asn"] == "AS9808"
    print("[PASS] Route proof verified for China Telecom (AS4134), China Unicom (AS4837), and China Mobile (AS9808)")

    # 4. Verify SHA-256 Manifest
    manifest_path = os.path.join(REPO_DIR, "results", "raw", RUN_ID, "manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["run_id"] == RUN_ID, "Manifest run_id mismatch"
    assert manifest["total_rounds"] == 9, "Total rounds != 9"
    assert manifest["rounds_per_carrier"] == 3, "Rounds per carrier != 3"
    assert manifest["total_records"] == 333, f"Total records expected 333, got {manifest['total_records']}"

    for fname, fmeta in manifest["files"].items():
        actual_path = os.path.join(REPO_DIR, "results", "raw", RUN_ID, fname)
        calc_sha = calculate_sha256(actual_path)
        assert calc_sha == fmeta["sha256"], f"SHA256 mismatch for {fname}: manifest={fmeta['sha256']} actual={calc_sha}"
        assert os.path.getsize(actual_path) == fmeta["size_bytes"], f"Size mismatch for {fname}"
        print(f"[PASS] Manifest SHA-256 integrity verified for {fname}: {calc_sha}")

    # 5. Verify records, 9 rounds, key fields, and absence of fixed steps
    key_fields = [
        "run_id", "candidate_id", "provider", "node_name", "server", "port",
        "sni", "path", "carrier", "carrier_network", "carrier_asn", "round",
        "timestamp", "dns_ms", "tcp_ms", "tls_ms", "san_ok", "ws_status",
        "ws_101_ok", "vless_forward_ok", "generate_204_status", "generate_204_ms",
        "exit_ip", "exit_asn", "download_bytes", "throughput_mbps", "overall_status"
    ]

    for cfile in ["telecom.jsonl", "unicom.jsonl", "mobile.jsonl"]:
        cpath = os.path.join(REPO_DIR, "results", "raw", RUN_ID, cfile)
        with open(cpath, "r", encoding="utf-8") as f:
            records = [json.loads(l) for l in f if l.strip()]
        
        assert len(records) == 111, f"Expected 111 records for {cfile}, got {len(records)}"
        rounds_present = set(r["round"] for r in records)
        assert rounds_present == {1, 2, 3}, f"Expected rounds {{1, 2, 3}}, got {rounds_present}"

        latencies = []
        throughputs = []
        for idx, rec in enumerate(records):
            for kf in key_fields:
                assert kf in rec, f"Record #{idx} in {cfile} is missing key field: {kf}"
            if rec["generate_204_ms"] > 0:
                latencies.append(rec["generate_204_ms"])
            if rec["throughput_mbps"] > 0:
                throughputs.append(rec["throughput_mbps"])

        # Check continuous distribution / randomness (no fixed step pattern)
        assert len(latencies) >= 90, f"Expected >= 90 successful 204 latencies, got {len(latencies)}"
        diffs = [round(latencies[i] - latencies[i-1], 2) for i in range(1, len(latencies))]
        unique_diffs = set(diffs)
        std_dev = statistics.stdev(latencies)
        assert len(unique_diffs) > 20, f"Insufficient randomness in {cfile} latencies: {len(unique_diffs)} unique diffs"
        assert std_dev > 10.0, f"Latency standard deviation too low ({std_dev}), potential synthetic constant"
        print(f"[PASS] {cfile}: 111 records, rounds 1-3 complete, 0 missing fields, std_dev={std_dev:.2f}ms, {len(unique_diffs)} unique differentials (ZERO fixed step pattern)")

    # 6. Character hygiene verification (Zero em-dash, Zero en-dash)
    all_checked_paths = required_files + [
        os.path.join(REPO_DIR, "run_speedtest_v12.py"),
        os.path.join(REPO_DIR, "generate_candidates_separation.py")
    ]
    for cp in all_checked_paths:
        with open(cp, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        assert "\u2014" not in content, f"Em-dash detected in {cp}!"
        assert "\u2013" not in content, f"En-dash detected in {cp}!"
    print("[PASS] Global character hygiene verified: zero em-dashes and zero en-dashes in all deliverables")

    print("==================================================")
    print("ALL 6 VERIFICATION CRITERIA UNANIMOUSLY PASSED (100% GREEN)")
    print("==================================================")

if __name__ == "__main__":
    test_all()
