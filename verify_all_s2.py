#!/usr/bin/env python3
"""
Comprehensive S2 Backend Verification Suite
Validates all aspects of TaskCard S2-backend-01
"""

import os
import json
import yaml
from collections import Counter

BASE_DIR = r"C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest"
WORKER_PATH = r"C:\Users\ludas\.gemini\antigravity\scratch\wasmer_sub_updated.js"

with open(os.path.join(BASE_DIR, "uuid_config.json"), "r", encoding="utf-8") as f:
    cfg = json.load(f)

UUIDS = cfg["subscriptions"]
RETIRED_UUID = cfg["retired_uuid"]

YAML_FILES = {
    "clash_fastly.yaml": (UUIDS["fastly"], 34, True),
    "clash_wasmer.yaml": (UUIDS["wasmer"], 34, False),
    "clash_netlify.yaml": (UUIDS["netlify"], 34, False),
    "clash_edgetunnel.yaml": (UUIDS["edgetunnel"], 34, False),
    "clash_edgeone.yaml": (UUIDS["edgeone"], 36, True), # Exactly 36
    "clash.yaml": (UUIDS["all"], 34, False)
}

def verify():
    print("==================================================")
    print("S2 Backend Comprehensive Verification Suite")
    print("==================================================")

    all_global_endpoints = []
    total_nodes = 0

    for fname, (expected_uuid, min_count, exact) in YAML_FILES.items():
        fpath = os.path.join(BASE_DIR, fname)
        assert os.path.exists(fpath), f"File missing: {fname}"

        with open(fpath, "r", encoding="utf-8") as f:
            raw_content = f.read()

        # Zero em-dash and en-dash verification
        assert "\u2014" not in raw_content, f"Em-dash detected in {fname}!"
        assert "\u2013" not in raw_content, f"En-dash detected in {fname}!"
        assert RETIRED_UUID not in raw_content, f"Retired UUID leaked into {fname}!"

        # yaml.safe_load
        data = yaml.safe_load(raw_content)
        assert data is not None, f"Failed to parse {fname}"
        proxies = data.get("proxies", [])
        proxy_groups = data.get("proxy-groups", [])
        rules = data.get("rules", [])

        count = len(proxies)
        total_nodes += count
        print(f"\n[PASS] {fname}: yaml.safe_load parsed successfully ({count} proxies, {len(proxy_groups)} groups, {len(rules)} rules)")

        if exact and fname == "clash_edgeone.yaml":
            assert count == min_count, f"{fname} must have exactly {min_count} nodes, got {count}"
        else:
            assert count >= min_count, f"{fname} must have >= {min_count} nodes, got {count}"

        # Internal duplicate names
        names = [p["name"] for p in proxies]
        name_counts = Counter(names)
        dup_names = [n for n, c in name_counts.items() if c > 1]
        assert not dup_names, f"Duplicate node names in {fname}: {dup_names}"

        # Internal duplicate endpoints
        ep_tuples = [(p["server"], p["port"], p.get("sni"), (p.get("ws-opts") or {}).get("path")) for p in proxies]
        ep_counts = Counter(ep_tuples)
        dup_eps = [ep for ep, c in ep_counts.items() if c > 1]
        assert not dup_eps, f"Duplicate endpoint tuples in {fname}: {dup_eps}"

        # UUID isolation
        for p in proxies:
            assert p["uuid"] == expected_uuid, f"Mismatched UUID in {fname} node {p['name']}: {p['uuid']} != {expected_uuid}"
            assert p["uuid"] != RETIRED_UUID, f"Retired UUID found in {fname} node {p['name']}"

            # Global uniqueness record
            all_global_endpoints.append((p["server"], p["port"], p.get("sni"), (p.get("ws-opts") or {}).get("path"), p["uuid"]))

        # Topological Authenticity checks
        if fname == "clash_fastly.yaml":
            for p in proxies:
                server = str(p["server"])
                sni = str(p.get("sni", ""))
                assert "fastly" in sni, f"Fastly node SNI must contain fastly: {sni}"
                assert ("fastly" in server) or server.startswith("151.101."), f"Fastly node server must be fastly domain or Fastly Anycast VIP: {server}"
                assert not server.endswith(".supabase.co"), f"Fastly server cannot be bare supabase.co: {server}"

        elif fname == "clash_wasmer.yaml":
            for p in proxies:
                if "66.42.98.41" in p["server"] or "w-la.ruoyemu.asia" in p["server"]:
                    assert "洛杉矶" in p["name"] or "美西" in p["name"], f"Wasmer LA node wrongly placed/named: {p['name']}"
                    assert "[Wasmer" in p["name"], f"Wasmer node missing honest [Wasmer] label: {p['name']}"
                assert "香港" not in p["name"], f"Wasmer YAML must have 0 HK nodes: {p['name']}"

        elif fname == "clash_edgetunnel.yaml":
            for p in proxies:
                assert "香港" not in p["name"], f"edgetunnel YAML must have 0 HK nodes: {p['name']}"
                assert p["server"].endswith(".supabase.co"), f"edgetunnel nodes must point directly to multi-region Supabase: {p['server']}"

        elif fname == "clash_edgeone.yaml":
            for p in proxies:
                server = str(p["server"])
                assert ("eo.ruoyemu.asia" in server) or ("edgefunctions" in server) or server.startswith("117.185.125."), f"EdgeOne node server invalid: {server}"

        elif fname == "clash_netlify.yaml":
            for p in proxies:
                path = (p.get("ws-opts") or {}).get("path", "")
                assert "404" not in path, f"Netlify path must not have 404: {path}"

    # Global Deduplication
    print("\n--- Cross-File Global Deduplication Matrix ---")
    print(f"Total nodes across all 6 YAML subscriptions: {total_nodes}")
    global_counts = Counter(all_global_endpoints)
    global_dups = [ep for ep, c in global_counts.items() if c > 1]
    assert not global_dups, f"Global duplicate endpoints detected: {global_dups}"
    print(f"Globally unique endpoints: {len(set(all_global_endpoints))} / {total_nodes} (100% Unique)")

    # Verify Worker code
    print("\n--- Verifying wasmer_sub_updated.js ---")
    assert os.path.exists(WORKER_PATH), "wasmer_sub_updated.js missing!"
    with open(WORKER_PATH, "r", encoding="utf-8") as f:
        wcontent = f.read()

    assert "\u2014" not in wcontent, "Em-dash found in wasmer_sub_updated.js!"
    assert RETIRED_UUID not in wcontent, "Retired UUID leaked into wasmer_sub_updated.js!"
    assert "env.GITHUB_TOKEN" in wcontent or "getGithubToken" in wcontent, "Worker does not reference GITHUB_TOKEN dynamically!"
    assert "UUID_MAP" in wcontent, "Worker missing UUID_MAP!"
    assert "FALLBACK_EDGEONE_YAML" in wcontent, "Worker missing FALLBACK_EDGEONE_YAML!"
    assert "FALLBACK_MASTER_YAML" in wcontent, "Worker missing FALLBACK_MASTER_YAML!"

    print("[PASS] wasmer_sub_updated.js verified cleanly (0 em-dashes, 0 retired UUIDs, multi-UUID support present)")

    print("\n==================================================")
    print("ALL TESTS PASSED WITH 100% COMPLIANCE!")
    print("==================================================")

if __name__ == "__main__":
    verify()
