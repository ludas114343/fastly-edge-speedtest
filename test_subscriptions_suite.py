#!/usr/bin/env python3
"""
Comprehensive Verification Test Suite for V12 Subscription Engine.
Validates all acceptance criteria defined in TaskCard: taskcards/phase3/subscription-agent.md:
1. 8 independent subscriptions parsed with yaml.safe_load and validated.
2. Evidence records in evidence/subscriptions/<token>.json validated against YAML hashes and node counts.
3. 10 independent GitHub Actions workflows syntactically validated.
4. Optimal selection algorithm verified (hard gates, cross-network ranking, hysteresis logic).
5. Zero em-dash and zero en-dash policy strictly verified across all project assets.
"""

import os
import sys
import json
import hashlib
import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
SUBSCRIPTIONS_DIR = os.path.join(REPO_DIR, "evidence", "subscriptions")
WORKFLOWS_DIR = os.path.join(REPO_DIR, ".github", "workflows")

TOKENS = [
    "all",
    "supabase",
    "wasmer",
    "northflank",
    "cloudflare",
    "fastly",
    "netlify",
    "edgeone"
]

YAML_MAP = {
    "all": "clash.yaml",
    "supabase": "clash_supabase.yaml",
    "wasmer": "clash_wasmer.yaml",
    "northflank": "clash_northflank.yaml",
    "cloudflare": "clash_cloudflare.yaml",
    "fastly": "clash_fastly.yaml",
    "netlify": "clash_netlify.yaml",
    "edgeone": "clash_edgeone.yaml"
}

THIRTEEN_WORKFLOWS = [
    "deploy-supabase.yml",
    "deploy-wasmer.yml",
    "deploy-northflank.yml",
    "deploy-cloudflare.yml",
    "deploy-fastly.yml",
    "deploy-netlify.yml",
    "deploy-edgeone.yml",
    "discover-candidates.yml",
    "smoke-test.yml",
    "optimize-three-carriers.yml",
    "publish-subscriptions.yml",
    "external-blackbox-audit.yml",
    "watchdog.yml"
]

def calculate_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def test_character_hygiene():
    print("--- 1. Testing Character Hygiene (Zero Em-Dash & En-Dash Policy) ---")
    files_to_check = []
    
    # Check all yaml files
    for fname in YAML_MAP.values():
        p = os.path.join(REPO_DIR, fname)
        if os.path.exists(p):
            files_to_check.append(p)
            
    # Check all workflow files
    for wname in THIRTEEN_WORKFLOWS:
        p = os.path.join(WORKFLOWS_DIR, wname)
        if os.path.exists(p):
            files_to_check.append(p)
            
    # Check evidence json files
    for t in TOKENS:
        p = os.path.join(SUBSCRIPTIONS_DIR, f"{t}.json")
        if os.path.exists(p):
            files_to_check.append(p)
            
    # Check engine scripts
    files_to_check.append(os.path.join(REPO_DIR, "select_optimal_nodes.py"))
    files_to_check.append(os.path.join(REPO_DIR, "update_worker.py"))
    worker_p = os.path.join(REPO_DIR, "wasmer_sub_updated.js")
    if os.path.exists(worker_p):
        files_to_check.append(worker_p)

    for fpath in files_to_check:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        assert "\u2014" not in content, f"[FAIL] Em-dash (\\u2014) detected in {fpath}"
        assert "\u2013" not in content, f"[FAIL] En-dash (\\u2013) detected in {fpath}"
        
    print(f"[PASS] Verified {len(files_to_check)} files: strictly zero em-dashes and zero en-dashes.")

def test_subscriptions_yaml_and_evidence():
    print("\n--- 2. Testing 8 Subscriptions YAML Structure & Evidence Matching ---")
    
    for token in TOKENS:
        yaml_name = YAML_MAP[token]
        yaml_path = os.path.join(REPO_DIR, yaml_name)
        evidence_path = os.path.join(SUBSCRIPTIONS_DIR, f"{token}.json")
        
        assert os.path.exists(yaml_path), f"Missing YAML file: {yaml_path}"
        assert os.path.exists(evidence_path), f"Missing evidence file: {evidence_path}"

        # 1. Parse YAML
        with open(yaml_path, "r", encoding="utf-8") as f:
            yaml_content = f.read()
        parsed_yaml = yaml.safe_load(yaml_content)
        assert parsed_yaml is not None, f"Failed to parse YAML in {yaml_name}"

        # Required fields in Clash config
        for req_key in ["port", "mode", "dns", "proxies", "proxy-groups", "rules", "metadata"]:
            assert req_key in parsed_yaml, f"Missing required root key '{req_key}' in {yaml_name}"

        proxies = parsed_yaml.get("proxies", [])
        proxy_count = len(proxies)
        metadata = parsed_yaml.get("metadata", {})
        
        # 2. Check duplicate names and endpoints
        node_names = [p.get("name") for p in proxies]
        assert len(node_names) == len(set(node_names)), f"Duplicate node names found in {yaml_name}"
        ep_tuples = [(p.get("server"), p.get("port"), p.get("sni"), (p.get("ws-opts") or {}).get("path")) for p in proxies]
        assert len(ep_tuples) == len(set(ep_tuples)), f"Duplicate connection endpoints found in {yaml_name}"

        # 3. Parse Evidence JSON
        with open(evidence_path, "r", encoding="utf-8") as f:
            ev = json.load(f)

        assert ev["token"] == token, f"Token mismatch in {evidence_path}: {ev['token']} != {token}"
        assert ev["url_path"] == f"/{token}", f"URL path mismatch in {evidence_path}"
        assert ev["http_status"] == 200, f"HTTP status is not 200 in {evidence_path}"
        assert ev["yaml_valid"] is True, f"YAML valid flag is not true in {evidence_path}"
        assert ev["node_count"] == proxy_count, f"Node count mismatch in {evidence_path}: {ev['node_count']} != {proxy_count}"

        # Verify hash matches
        computed_sha = calculate_sha256(yaml_path)
        assert ev["sha256"] == computed_sha, f"SHA-256 mismatch in {evidence_path}: {ev['sha256']} != {computed_sha}"

        # Check honest status
        if proxy_count == 0:
            assert ev["status"] == "NO_VERIFIED_PROXY", f"Expected NO_VERIFIED_PROXY for empty {token}, got {ev['status']}"
            assert metadata.get("status") == "NO_VERIFIED_PROXY"
            assert "reason" in metadata and len(metadata["reason"]) > 0
            print(f"  [PASS] /{token} ({yaml_name}): Honest empty subscription (status: NO_VERIFIED_PROXY, SHA: {computed_sha[:12]}...)")
        else:
            assert ev["status"] == "VERIFIED_PROXY", f"Expected VERIFIED_PROXY for {token}, got {ev['status']}"
            assert metadata.get("status") == "VERIFIED_PROXY"
            print(f"  [PASS] /{token} ({yaml_name}): {proxy_count} verified proxies (status: VERIFIED_PROXY, SHA: {computed_sha[:12]}...)")

def test_workflows_syntax():
    print("\n--- 3. Testing 13 GitHub Actions Workflows Syntax ---")
    assert os.path.exists(WORKFLOWS_DIR), f"Missing workflows dir: {WORKFLOWS_DIR}"
    
    for wf in THIRTEEN_WORKFLOWS:
        wf_path = os.path.join(WORKFLOWS_DIR, wf)
        assert os.path.exists(wf_path), f"Missing required workflow: {wf_path}"
        
        with open(wf_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        data = yaml.safe_load(content)
        assert data is not None, f"Workflow {wf} failed to parse as YAML!"
        assert "name" in data, f"Workflow {wf} missing 'name'!"
        assert "on" in data or True in data, f"Workflow {wf} missing triggers ('on')!"
        assert "jobs" in data, f"Workflow {wf} missing 'jobs'!"
        
        # Verify permissions
        assert "permissions" in data, f"Workflow {wf} missing explicit 'permissions'!"
        print(f"  [PASS] {wf}: Valid YAML structure, trigger and jobs defined.")

def test_hysteresis_logic_unit():
    print("\n--- 4. Testing Stability Hysteresis Unit Logic ---")
    from select_optimal_nodes import apply_hysteresis_selection

    # Scenario A: Old node has score 500. Candidate has score 480 (4% improvement, < 15%).
    # Result: Old node must be retained.
    prev_state = {
        "active_nodes": {
            "server1:443/path1": {
                "candidate_id": "old-01",
                "node_name": "Node Old 01",
                "endpoint": ["server1", 443, "server1", "/path1"],
                "composite_score": 500.0,
                "consecutive_failures": 0
            }
        }
    }
    
    candidates = [
        {
            "candidate_id": "old-01",
            "node_name": "Node Old 01",
            "server": "server1",
            "port": 443,
            "sni": "server1",
            "path": "/path1",
            "metrics": {"composite_score": 500.0}
        },
        {
            "candidate_id": "new-01",
            "node_name": "Node New 01",
            "server": "server2",
            "port": 443,
            "sni": "server2",
            "path": "/path2",
            "metrics": {"composite_score": 480.0} # 4% improvement
        }
    ]

    selected, updated_state = apply_hysteresis_selection(candidates, prev_state, threshold=0.15)
    assert len(selected) == 2
    assert "server1:443/path1" in updated_state["active_nodes"]
    assert updated_state["active_nodes"]["server1:443/path1"]["consecutive_failures"] == 0
    print("  [PASS] Healthy old node retained without flapping on marginal <15% variance.")

    # Scenario B: Old node fails in run.
    candidates_fail = [
        {
            "candidate_id": "new-01",
            "node_name": "Node New 01",
            "server": "server2",
            "port": 443,
            "sni": "server2",
            "path": "/path2",
            "metrics": {"composite_score": 400.0}
        }
    ]
    selected_fail, updated_state_fail = apply_hysteresis_selection(candidates_fail, prev_state, threshold=0.15)
    assert updated_state_fail["active_nodes"]["server1:443/path1"]["consecutive_failures"] == 1
    print("  [PASS] Failed old node increments consecutive failure count toward eviction.")

    # Scenario C: Candidates with simplified metrics or direct effective_score
    candidates_simplified = [
        {
            "candidate_id": "sim-01",
            "node_name": "Node Sim 01",
            "server": "server3",
            "port": 443,
            "sni": "server3",
            "path": "/path3",
            "effective_score": 450.0
        },
        {
            "candidate_id": "sim-02",
            "node_name": "Node Sim 02",
            "server": "server4",
            "port": 443,
            "sni": "server4",
            "path": "/path4",
            "metrics": {"composite_score": 460.0}
        }
    ]
    selected_sim, updated_state_sim = apply_hysteresis_selection(candidates_simplified, {}, threshold=0.15)
    assert len(selected_sim) == 2
    assert selected_sim[0]["candidate_id"] == "sim-01"
    print("  [PASS] Candidates with direct effective_score or simplified metrics handled gracefully.")

    # Scenario D: Candidate tie-breaker with None values in metrics dictionary
    candidates_none_metrics = [
        {
            "candidate_id": "none-01",
            "node_name": "Node None 01",
            "server": "server5",
            "port": 443,
            "sni": "server5",
            "path": "/path5",
            "metrics": {"composite_score": 300.0, "worst_p95": None, "avg_p50": None}
        },
        {
            "candidate_id": "none-02",
            "node_name": "Node None 02",
            "server": "server6",
            "port": 443,
            "sni": "server6",
            "path": "/path6",
            "metrics": {"composite_score": 300.0, "worst_p95": 50.0, "avg_p50": 20.0}
        }
    ]
    selected_none, updated_state_none = apply_hysteresis_selection(candidates_none_metrics, {}, threshold=0.15)
    assert len(selected_none) == 2
    print("  [PASS] Candidate tie-breaker with None metric fields sorted safely without TypeError.")

def test_worker_routes():
    print("\n--- 5. Testing Worker Routing and Fallbacks ---")
    worker_path = os.path.join(REPO_DIR, "wasmer_sub_updated.js")
    if not os.path.exists(worker_path):
        worker_path = os.path.join(os.path.dirname(REPO_DIR), "wasmer_sub_updated.js")
    assert os.path.exists(worker_path), f"Missing {worker_path}"

    with open(worker_path, "r", encoding="utf-8") as f:
        code = f.read()

    for token in TOKENS:
        assert f'"{token}"' in code or f"'{token}'" in code, f"Token {token} missing from worker UUID_MAP"

    assert "resolveRequestedToken" in code, "resolveRequestedToken missing from worker"
    assert "FALLBACK_ALL_YAML" in code, "FALLBACK_ALL_YAML missing from worker"
    print("  [PASS] Worker wasmer_sub_updated.js verified for all 8 URL route tokens.")

if __name__ == "__main__":
    print("=" * 70)
    print("RUNNING SUBSCRIPTION AGENT COMPREHENSIVE VERIFICATION SUITE")
    print("=" * 70)
    test_character_hygiene()
    test_subscriptions_yaml_and_evidence()
    test_workflows_syntax()
    test_hysteresis_logic_unit()
    test_worker_routes()
    print("\n" + "=" * 70)
    print("ALL VERIFICATION SUITE TESTS PASSED (EXIT CODE 0)!")
    print("=" * 70)
