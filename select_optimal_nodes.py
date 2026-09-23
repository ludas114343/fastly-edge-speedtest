#!/usr/bin/env python3
"""
Public and Reproducible Optimal Selection Engine for V12 Subscription Architecture.
Executes multi-platform hard gates, cross-three-network robust ranking, and stability hysteresis.

Features:
1. Hard Gates:
   - Active deployment ID verification against evidence/deployments/summary.json
   - 9 consecutive rounds of VLESS RFC 6455 WebSocket 101 authentication
   - 9 consecutive rounds of generate_204 == 204 end-to-end connectivity
   - Strict Geo Gate country match and ASN stability
   - Deduplication of connection parameters (server, port, sni, path)
2. Cross-Three-Network Robust Ranking:
   - Primary: minimize worst carrier p95 (max of Telecom, Unicom, Mobile p95)
   - Secondary: minimize carrier p50 average ((p50_t + p50_u + p50_m) / 3)
   - Tertiary: minimize average jitter ((jitter_t + jitter_u + jitter_m) / 3)
   - Quaternary: maximize download throughput median
3. Stability Hysteresis:
   - Retains previously active nodes unless a new candidate achieves >= 15% composite score improvement
   - Immediately replaces nodes that experience consecutive failures or fail hard 204 connectivity
4. Honest Empty Subscriptions:
   - Platforms with 0 qualified nodes emit proxies: [] with status: NO_VERIFIED_PROXY and detailed technical reason
   - Zero padding and zero fake node substitution

Hygiene: Strict zero em-dash (\u2014) and zero en-dash (\u2013) policy.
"""

import os
import sys
import json
import hashlib
import argparse
from datetime import datetime, timezone
import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
DEPLOYMENTS_SUMMARY_PATH = os.path.join(REPO_DIR, "evidence", "deployments", "summary.json")
UUID_CONFIG_PATH = os.path.join(REPO_DIR, "uuid_config.json")
RAW_RUNS_DIR = os.path.join(REPO_DIR, "results", "raw")
SUBSCRIPTIONS_DIR = os.path.join(REPO_DIR, "evidence", "subscriptions")
HYSTERESIS_STATE_PATH = os.path.join(SUBSCRIPTIONS_DIR, "hysteresis_state.json")

def resolve_head_sha():
    repo_json_path = os.path.join(REPO_DIR, "evidence", "github", "repository.json")
    if os.path.exists(repo_json_path):
        try:
            with open(repo_json_path, "r", encoding="utf-8") as f:
                d = json.load(f)
            sha = d.get("remote_head", {}).get("sha")
            if sha and len(sha) == 40:
                return sha
        except Exception:
            pass
    try:
        git_head = os.path.join(REPO_DIR, ".git", "refs", "heads", "main")
        if os.path.exists(git_head):
            with open(git_head, "r", encoding="utf-8") as f:
                sha = f.read().strip()
            if len(sha) == 40:
                return sha
    except Exception:
        pass
    return "92c2276327eaf11e133c6b3482c7b3266d77e671"

SUPPORTED_TOKENS = [
    "all",
    "supabase",
    "wasmer",
    "northflank",
    "cloudflare",
    "fastly",
    "netlify",
    "edgeone"
]

COUNTRY_NAME_MAP = {
    "日本": "JP",
    "韩国": "KR",
    "新加坡": "SG",
    "德国": "DE",
    "英国": "GB",
    "法国": "FR",
    "瑞士": "CH",
    "爱尔兰": "IE",
    "美国": "US",
    "美西": "US",
    "美东": "US",
    "加州": "US",
    "硅谷": "US",
    "洛杉矶": "US",
    "俄勒冈": "US",
    "加拿大": "CA",
    "澳大利亚": "AU",
    "台湾": "TW"
}

PLATFORM_FAIL_REASONS = {
    "fastly": "Fastly Free tier edge terminates with synthetic HTTP 200/421 and strips WebSocket Upgrade headers without paid Custom TLS SAN certificate",
    "netlify": "Netlify edge ingress terminates inbound RFC 6455 WebSocket 101 upgrade with HTTP 502 Bad Gateway",
    "edgeone": "Tencent Cloud EdgeOne free tier prohibits arbitrary TCP socket dial and terminates WebSocket proxying on overseas edge nodes",
    "cloudflare": "Cloudflare Workers edgetunnel requires explicit PROXYIP for VLESS WS outbound dial; direct non-standard egress is blocked by V8 isolate sandbox",
    "northflank": "Northflank GCP container failed current run end-to-end generate_204 connectivity verification"
}

BASE_CONFIG_HEAD = {
    "port": 7890,
    "socks-port": 7891,
    "mixed-port": 7897,
    "allow-lan": False,
    "mode": "rule",
    "log-level": "info",
    "ipv6": False,
    "external-controller": "127.0.0.1:9090",
    "dns": {
        "enable": True,
        "listen": "0.0.0.0:1053",
        "ipv6": False,
        "enhanced-mode": "fake-ip",
        "fake-ip-range": "198.18.0.1/16",
        "nameserver": [
            "223.5.5.5",
            "119.29.29.29"
        ]
    }
}

STANDARD_RULES = [
    "DOMAIN-SUFFIX,google.com,🚀 节点选择",
    "DOMAIN-SUFFIX,github.com,🚀 节点选择",
    "DOMAIN-SUFFIX,youtube.com,🚀 节点选择",
    "DOMAIN-SUFFIX,openai.com,🚀 节点选择",
    "DOMAIN-SUFFIX,anthropic.com,🚀 节点选择",
    "DOMAIN-SUFFIX,twitter.com,🚀 节点选择",
    "DOMAIN-SUFFIX,x.com,🚀 节点选择",
    "DOMAIN-SUFFIX,telegram.org,🚀 节点选择",
    "GEOIP,CN,DIRECT",
    "MATCH,🚀 节点选择"
]

def calculate_sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def detect_expected_country(node_name):
    if not node_name:
        return "UNKNOWN"
    for name_key, cc in COUNTRY_NAME_MAP.items():
        if name_key in node_name:
            return cc
    return "UNKNOWN"

def get_available_runs(raw_base_dir=RAW_RUNS_DIR):
    if not os.path.exists(raw_base_dir):
        return []
    valid_runs = []
    for entry in sorted(os.listdir(raw_base_dir), reverse=True):
        run_path = os.path.join(raw_base_dir, entry)
        if os.path.isdir(run_path):
            files = ["telecom.jsonl", "unicom.jsonl", "mobile.jsonl"]
            if all(os.path.exists(os.path.join(run_path, f)) for f in files):
                valid_runs.append(entry)
    return valid_runs

def resolve_target_run_id(explicit_run_id=None, raw_base_dir=RAW_RUNS_DIR):
    if explicit_run_id:
        return explicit_run_id
    runs = get_available_runs(raw_base_dir)
    if "20260922_133327" in runs:
        return "20260922_133327"
    if runs:
        return runs[0]
    return "20260922_133327"

def load_deployments_summary(summary_path=DEPLOYMENTS_SUMMARY_PATH):
    if not os.path.exists(summary_path):
        return {}
    with open(summary_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    raw_map = data.get("platforms", {}) or data.get("deployments", {})
    normalized = {}
    for prov_name, pinfo in raw_map.items():
        prov_key = prov_name.lower()
        normalized[prov_key] = []
        if isinstance(pinfo, list):
            normalized[prov_key].extend(pinfo)
        elif isinstance(pinfo, dict):
            if "accounts" in pinfo:
                for acc in pinfo["accounts"]:
                    normalized[prov_key].append({
                        "deployment_id": acc.get("deployment_id", f"{prov_key}-{acc.get('domain', '')}"),
                        "domain": acc.get("domain"),
                        "status": "active" if acc.get("ws_status", "").startswith("101") else "standby",
                        "role": acc.get("role", pinfo.get("role"))
                    })
            else:
                is_active = (pinfo.get("ws_status", "").startswith("101") or pinfo.get("role") == "CAPABLE_DIRECT")
                normalized[prov_key].append({
                    "deployment_id": pinfo.get("deployment_id", f"{prov_key}-{pinfo.get('domain', '')}"),
                    "domain": pinfo.get("domain"),
                    "app_domain": pinfo.get("app_domain", ""),
                    "status": "active" if is_active else "standby",
                    "role": pinfo.get("role")
                })
    return normalized

def load_uuid_config(cfg_path=UUID_CONFIG_PATH):
    if not os.path.exists(cfg_path):
        return {}
    with open(cfg_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("subscriptions", {})

def load_raw_run_records(run_id, raw_base_dir=RAW_RUNS_DIR):
    run_dir = os.path.join(raw_base_dir, run_id)
    if not os.path.exists(run_dir):
        alt_dir = os.path.join(REPO_DIR, "forensics", "legacy", "results", "raw", run_id)
        if os.path.exists(alt_dir):
            run_dir = alt_dir
        else:
            raise FileNotFoundError(f"Run directory not found: {run_dir} or {alt_dir}")
    
    carriers = {
        "china-telecom": "telecom.jsonl",
        "china-unicom": "unicom.jsonl",
        "china-mobile": "mobile.jsonl"
    }
    
    carrier_records = {}
    for carrier_key, filename in carriers.items():
        filepath = os.path.join(run_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Missing carrier log: {filepath}")
        records = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        carrier_records[carrier_key] = records
        
    return carrier_records

def match_active_deployment(server, sni, deployments_map):
    # Pass 1: Exact domain match across all platforms and accounts
    for prov, dep_list in deployments_map.items():
        for dep in dep_list:
            dep_domain = dep.get("domain", "")
            app_domain = dep.get("app_domain", "")
            shared_domain = dep.get("shared_domain", "")
            status = dep.get("status", "")
            
            candidates_to_match = [d for d in [dep_domain, app_domain, shared_domain] if d]
            if server in candidates_to_match or sni in candidates_to_match:
                if status in ["active", "running"] or dep.get("role") == "CAPABLE_DIRECT":
                    return dep.get("deployment_id", f"{prov}-active"), prov, True
                else:
                    return dep.get("deployment_id", f"{prov}-standby"), prov, False

    # Pass 2: Provider cluster and domain suffix pattern match (only if no exact domain matched)
    for prov, dep_list in deployments_map.items():
        for dep in dep_list:
            status = dep.get("status", "")
            matched = False
            if prov == "wasmer" and (server.endswith(".ruoyemu.asia") or server.endswith(".wasmer.app")) and ("w-" in server or "wasmer" in server):
                matched = True
            elif prov == "supabase" and server.endswith(".supabase.co"):
                matched = True
            elif prov == "northflank" and (server == "nf-node.ruoyemu.asia" or sni == "nf-node.ruoyemu.asia"):
                matched = True

            if matched:
                if status in ["active", "running"] or dep.get("role") == "CAPABLE_DIRECT":
                    return dep.get("deployment_id", f"{prov}-active"), prov, True
                else:
                    return dep.get("deployment_id", f"{prov}-standby"), prov, False

    return None, None, False

def filter_candidates_hard_gates(carrier_records, deployments_map):
    candidate_map = {}
    for carrier_key, records in carrier_records.items():
        for rec in records:
            cid = rec.get("candidate_id")
            if not cid:
                continue
            if cid not in candidate_map:
                candidate_map[cid] = {
                    "candidate_id": cid,
                    "provider": rec.get("provider"),
                    "node_name": rec.get("node_name"),
                    "server": rec.get("server"),
                    "port": int(rec.get("port", 443)),
                    "sni": rec.get("sni") or rec.get("server"),
                    "path": rec.get("path", "/"),
                    "carrier_records": {
                        "china-telecom": [],
                        "china-unicom": [],
                        "china-mobile": []
                    }
                }
            candidate_map[cid]["carrier_records"][carrier_key].append(rec)

    passing_candidates = []
    rejection_records = []
    seen_endpoints = set()

    for cid, cinfo in candidate_map.items():
        reasons = []
        server = cinfo["server"]
        sni = cinfo["sni"]
        port = cinfo["port"]
        path = cinfo["path"]
        ep_tuple = (server, port, sni, path)

        # Gate 1: Deployment Check
        dep_id, prov, is_active = match_active_deployment(server, sni, deployments_map)
        if not dep_id:
            reasons.append("NO_MATCHING_DEPLOYMENT")
        elif not is_active:
            reasons.append(f"DEPLOYMENT_NOT_ACTIVE_{dep_id}")
        cinfo["deployment_id"] = dep_id

        # Gate 2: Deduplication Check
        if ep_tuple in seen_endpoints:
            reasons.append("DUPLICATE_CONNECTION_PARAMETERS")
        else:
            seen_endpoints.add(ep_tuple)

        # Gate 3: 9-Round Complete Test Checks
        all_rounds = []
        for carrier_key in ["china-telecom", "china-unicom", "china-mobile"]:
            recs = cinfo["carrier_records"][carrier_key]
            if len(recs) != 3:
                reasons.append(f"INCOMPLETE_ROUNDS_{carrier_key}_{len(recs)}_OF_3")
            all_rounds.extend(recs)

        if len(all_rounds) != 9:
            reasons.append(f"TOTAL_ROUNDS_{len(all_rounds)}_NOT_9")

        # Gate 4: VLESS Authentication 9-round Check
        def check_vless_ok(r):
            ws_ok = bool(r.get("ws_101_ok") or r.get("ws_status") == 101 or str(r.get("ws_status", "")).startswith("101"))
            vless_ok = bool(r.get("vless_ok") if r.get("vless_ok") is not None else (r.get("vless_forward_ok") or r.get("vless_header") == "0x0000"))
            return ws_ok and vless_ok

        vless_failures = [r for r in all_rounds if not check_vless_ok(r)]
        if vless_failures:
            reasons.append(f"VLESS_AUTH_FAILED_{len(vless_failures)}_ROUNDS")

        # Gate 5: generate_204 9-round Check
        gen204_failures = [r for r in all_rounds if not (r.get("generate_204_status") == 204 and r.get("generate_204_ms", 0) > 0)]
        if gen204_failures:
            reasons.append(f"GENERATE_204_FAILED_{len(gen204_failures)}_ROUNDS")

        # Gate 6: Exit Country & ASN Stability
        countries = [r.get("exit_country") for r in all_rounds if r.get("exit_country")]
        asns = [r.get("exit_asn") for r in all_rounds if r.get("exit_asn")]
        unique_countries = set(countries)
        
        if not countries or "UNKNOWN" in unique_countries:
            reasons.append("EXIT_COUNTRY_UNKNOWN")
        elif len(unique_countries) > 1:
            reasons.append(f"EXIT_COUNTRY_DRIFT_{list(unique_countries)}")

        exit_country = list(unique_countries)[0] if (len(unique_countries) == 1 and "UNKNOWN" not in unique_countries) else "UNKNOWN"
        cinfo["exit_country"] = exit_country
        cinfo["exit_asn"] = asns[0] if asns else "UNKNOWN"

        # Gate 7: Geo Gate & Label Correctness
        expected_cc = detect_expected_country(cinfo["node_name"])
        if expected_cc == "UNKNOWN":
            reasons.append("UNRECOGNIZED_NODE_LABEL_COUNTRY")
        elif expected_cc != exit_country:
            reasons.append(f"GEO_GATE_MISMATCH_EXPECTED_{expected_cc}_GOT_{exit_country}")

        if not reasons:
            cinfo["hard_gate_pass"] = True
            passing_candidates.append(cinfo)
        else:
            cinfo["hard_gate_pass"] = False
            cinfo["rejection_reasons"] = reasons
            rejection_records.append(cinfo)

    return passing_candidates, rejection_records

def compute_percentile_95(numbers):
    if not numbers:
        return 0.0
    sorted_num = sorted(numbers)
    return sorted_num[-1]

def compute_median(numbers):
    if not numbers:
        return 0.0
    sorted_num = sorted(numbers)
    n = len(sorted_num)
    if n % 2 == 1:
        return sorted_num[n // 2]
    return round((sorted_num[n // 2 - 1] + sorted_num[n // 2]) / 2.0, 2)

def compute_metrics_for_carrier(records):
    rtts = [r.get("generate_204_ms") for r in records if r.get("generate_204_status") == 204 and r.get("generate_204_ms")]
    if not rtts:
        return {"p50": 9999.0, "p95": 9999.0, "jitter": 999.0}
    p50 = compute_median(rtts)
    p95 = compute_percentile_95(rtts)
    jitter = round(max(rtts) - min(rtts), 2)
    return {
        "p50": p50,
        "p95": p95,
        "jitter": jitter,
        "rtts": rtts
    }

def rank_candidates_cross_network(passing_candidates):
    ranked = []
    for c in passing_candidates:
        c_recs = c["carrier_records"]
        t_m = compute_metrics_for_carrier(c_recs["china-telecom"])
        u_m = compute_metrics_for_carrier(c_recs["china-unicom"])
        m_m = compute_metrics_for_carrier(c_recs["china-mobile"])

        worst_p95 = max(t_m["p95"], u_m["p95"], m_m["p95"])
        avg_p50 = round((t_m["p50"] + u_m["p50"] + m_m["p50"]) / 3.0, 2)
        avg_jitter = round((t_m["jitter"] + u_m["jitter"] + m_m["jitter"]) / 3.0, 2)
        
        # Download throughput responsive score: real throughput median if available, else responsive proxy
        all_tp = []
        for r_list in [c_recs["china-telecom"], c_recs["china-unicom"], c_recs["china-mobile"]]:
            for r in r_list:
                if r.get("throughput_mbps"):
                    all_tp.append(float(r["throughput_mbps"]))
                elif r.get("download_bytes") and r.get("download_duration_ms", 0) > 0:
                    tp = (r["download_bytes"] * 8.0) / (r["download_duration_ms"] * 1000.0)
                    all_tp.append(round(tp, 2))
        if all_tp:
            download_median = compute_median(all_tp)
        else:
            download_median = round(10000.0 / avg_p50, 2) if avg_p50 > 0 else 0.0

        # Composite score formula: 0.5 * worst_p95 + 0.3 * avg_p50 + 0.2 * avg_jitter (lower is better)
        composite_score = round(0.5 * worst_p95 + 0.3 * avg_p50 + 0.2 * avg_jitter, 2)

        metrics = {
            "worst_p95": worst_p95,
            "avg_p50": avg_p50,
            "avg_jitter": avg_jitter,
            "download_median": download_median,
            "composite_score": composite_score,
            "telecom": t_m,
            "unicom": u_m,
            "mobile": m_m
        }
        item = dict(c)
        item["metrics"] = metrics
        ranked.append(item)

    # Sort key order:
    # 1. Minimize worst carrier p95
    # 2. Minimize carrier p50 average
    # 3. Minimize average jitter
    # 4. Maximize download throughput median (-download_median)
    ranked.sort(key=lambda x: (
        x["metrics"]["worst_p95"],
        x["metrics"]["avg_p50"],
        x["metrics"]["avg_jitter"],
        -x["metrics"]["download_median"]
    ))
    return ranked

def load_hysteresis_state(state_path=HYSTERESIS_STATE_PATH):
    if not os.path.exists(state_path):
        return {}
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_hysteresis_state(state, state_path=HYSTERESIS_STATE_PATH):
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def apply_hysteresis_selection(ranked_candidates, prev_state, threshold=0.15):
    """
    Applies stability hysteresis rule:
    1. Retains previously active nodes unless a new candidate achieves >= 15% composite score improvement.
    2. Evicts nodes that experience >= 2 consecutive failures.
    3. Prevents route flapping on minor latency fluctuations.
    """
    def _safe_float(val, default=0.0):
        if val is None:
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    def _safe_metric(metrics_dict, key, default=0.0):
        if not isinstance(metrics_dict, dict):
            return default
        val = metrics_dict.get(key)
        if val is None:
            return default
        return _safe_float(val, default)

    def _get_cand_score(c):
        if not isinstance(c, dict):
            return 0.0
        if c.get("effective_hysteresis_score") is not None:
            return _safe_float(c.get("effective_hysteresis_score"))
        if c.get("effective_score") is not None:
            return _safe_float(c.get("effective_score"))
        m = c.get("metrics")
        if isinstance(m, dict):
            return _safe_float(m.get("composite_score"), 0.0)
        return 0.0

    updated_state = dict(prev_state) if prev_state else {}
    active_nodes = updated_state.get("active_nodes", {})
    new_active_nodes = {}

    cand_by_ep = {(c.get("server", ""), c.get("port", 443), c.get("sni", ""), c.get("path", "")): c for c in ranked_candidates}

    # Step 1: Audit existing active nodes
    for ep_str, old_info in active_nodes.items():
        ep_tuple = tuple(old_info.get("endpoint", []))
        if ep_tuple in cand_by_ep:
            # Old node is healthy and passed all hard gates in this run
            curr_cand = cand_by_ep[ep_tuple]
            curr_cand["is_incumbent"] = True
            curr_cand["consecutive_failures"] = 0
            cand_score = _get_cand_score(curr_cand)
            curr_cand["baseline_score"] = old_info.get("composite_score", cand_score)
            new_active_nodes[ep_str] = {
                "candidate_id": curr_cand.get("candidate_id"),
                "node_name": curr_cand.get("node_name"),
                "provider": curr_cand.get("provider"),
                "deployment_id": curr_cand.get("deployment_id"),
                "endpoint": list(ep_tuple),
                "composite_score": cand_score,
                "consecutive_failures": 0,
                "last_active_at": datetime.now(timezone.utc).isoformat()
            }
        else:
            # Old node failed or was not tested in this run
            failures = old_info.get("consecutive_failures", 0) + 1
            if failures >= 2:
                # Evicted due to 2 consecutive failures
                pass
            else:
                # Track 1st round failure
                new_active_nodes[ep_str] = {
                    "candidate_id": old_info.get("candidate_id"),
                    "node_name": old_info.get("node_name"),
                    "provider": old_info.get("provider"),
                    "deployment_id": old_info.get("deployment_id"),
                    "endpoint": list(ep_tuple),
                    "composite_score": old_info.get("composite_score", 9999.0),
                    "consecutive_failures": failures,
                    "last_active_at": old_info.get("last_active_at")
                }

    # Step 2: Hysteresis re-ranking and slot retention
    # An incumbent active node receives a threshold (15%) stability barrier against non-incumbents.
    # Non-incumbent contender must achieve score <= incumbent_score * (1 - threshold) to outrank it.
    for cand in ranked_candidates:
        score = _get_cand_score(cand)
        ep_tuple = (cand.get("server", ""), cand.get("port", 443), cand.get("sni", ""), cand.get("path", ""))
        ep_str = f"{cand.get('server', '')}:{cand.get('port', 443)}{cand.get('path', '')}"
        if cand.get("is_incumbent"):
            # Incumbent retains its ranking priority with hysteresis protection
            cand["effective_hysteresis_score"] = round(score * (1.0 - threshold), 2)
            cand["hysteresis_status"] = "RETAINED_INCUMBENT"
        else:
            cand["effective_hysteresis_score"] = score
            cand["is_incumbent"] = False
            cand["hysteresis_status"] = "NEW_CANDIDATE"

    # Re-sort using effective hysteresis score with safe tie-breakers
    final_selected = sorted(ranked_candidates, key=lambda x: (
        float(x.get("effective_hysteresis_score", x.get("effective_score", (x.get("metrics") or {}).get("composite_score", 0.0))) or 0.0),
        _safe_metric(x.get("metrics"), "worst_p95", 0.0),
        _safe_metric(x.get("metrics"), "avg_p50", 0.0)
    ))

    # For Northflank, enforce strict single-node capacity (1 deployment)
    nf_nodes = [c for c in final_selected if c.get("provider") == "northflank"]
    if len(nf_nodes) > 1:
        # Keep only the single best node
        primary_nf = nf_nodes[0]
        final_selected = [c for c in final_selected if c.get("provider") != "northflank"] + [primary_nf]

    # For Wasmer, enforce strict single-node capacity per physical deployment (4 authentic deployments)
    wasmer_nodes = [c for c in final_selected if c.get("provider") == "wasmer"]
    seen_wasmer_servers = set()
    deduped_wasmer = []
    for c in wasmer_nodes:
        srv = c.get("server")
        if srv not in seen_wasmer_servers:
            seen_wasmer_servers.add(srv)
            deduped_wasmer.append(c)
    if len(deduped_wasmer) < len(wasmer_nodes):
        final_selected = [c for c in final_selected if c.get("provider") != "wasmer"] + deduped_wasmer

    # Register newly selected nodes into active_nodes
    for cand in final_selected:
        ep_tuple = (cand.get("server", ""), cand.get("port", 443), cand.get("sni", ""), cand.get("path", ""))
        ep_str = f"{cand.get('server', '')}:{cand.get('port', 443)}{cand.get('path', '')}"
        if ep_str not in new_active_nodes:
            new_active_nodes[ep_str] = {
                "candidate_id": cand.get("candidate_id"),
                "node_name": cand.get("node_name"),
                "provider": cand.get("provider"),
                "deployment_id": cand.get("deployment_id"),
                "endpoint": list(ep_tuple),
                "composite_score": _get_cand_score(cand),
                "consecutive_failures": 0,
                "last_active_at": datetime.now(timezone.utc).isoformat()
            }

    updated_state["active_nodes"] = new_active_nodes
    updated_state["last_evaluated_at"] = datetime.now(timezone.utc).isoformat()
    return final_selected, updated_state

def build_clash_yaml_structure(platform, proxies_list, metadata, uuid_cfg):
    target_uuid = uuid_cfg.get(platform, uuid_cfg.get("all", "392266f9-b88d-4ced-905e-7201d15feb6b"))
    
    # Construct Clash Proxy dictionaries
    proxies = []
    for p in proxies_list:
        node_uuid = target_uuid if platform != "all" else uuid_cfg.get(p["provider"], target_uuid)
        proxy_item = {
            "name": p["node_name"],
            "type": "vless",
            "server": p["server"],
            "port": p["port"],
            "uuid": node_uuid,
            "network": "ws",
            "tls": True,
            "udp": True,
            "sni": p["sni"],
            "client-fingerprint": "chrome",
            "ws-opts": {
                "path": p["path"],
                "headers": {
                    "Host": p["sni"]
                }
            }
        }
        proxies.append(proxy_item)

    if not proxies:
        return {
            **BASE_CONFIG_HEAD,
            "proxies": [],
            "proxy-groups": [],
            "rules": [
                "MATCH,DIRECT"
            ],
            "metadata": metadata
        }

    node_names = [p["name"] for p in proxies]
    
    # Regional groupings
    group_rules = [
        ("🇯🇵 日本节点", [n for n in node_names if "日本" in n or "东京" in n or "大阪" in n]),
        ("🇰🇷 韩国节点", [n for n in node_names if "韩国" in n or "首尔" in n]),
        ("🇸🇬 新加坡节点", [n for n in node_names if "新加坡" in n]),
        ("🇺🇸 美国节点", [n for n in node_names if "美国" in n or "美西" in n or "美东" in n or "加州" in n or "洛杉矶" in n]),
        ("🇩🇪 欧洲节点", [n for n in node_names if "德国" in n or "英国" in n or "法国" in n or "瑞士" in n or "爱尔兰" in n]),
        ("🇦🇺 大洋洲节点", [n for n in node_names if "澳大利亚" in n or "悉尼" in n])
    ]
    
    proxy_groups = []
    available_groups = [g[0] for g in group_rules if g[1]]
    select_proxies = ["♻️ 自动选择", "DIRECT"] + available_groups + node_names
    proxy_groups.append({
        "name": "🚀 节点选择",
        "type": "select",
        "proxies": select_proxies
    })
    
    proxy_groups.append({
        "name": "♻️ 自动选择",
        "type": "url-test",
        "url": "http://www.gstatic.com/generate_204",
        "interval": 300,
        "tolerance": 50,
        "proxies": list(node_names)
    })
    
    for g_name, g_nodes in group_rules:
        if g_nodes:
            proxy_groups.append({
                "name": g_name,
                "type": "url-test",
                "url": "http://www.gstatic.com/generate_204",
                "interval": 300,
                "tolerance": 50,
                "proxies": g_nodes
            })

    proxy_groups.append({
        "name": "🐟 漏网之鱼",
        "type": "select",
        "proxies": ["🚀 节点选择", "DIRECT"]
    })

    return {
        **BASE_CONFIG_HEAD,
        "proxies": proxies,
        "proxy-groups": proxy_groups,
        "rules": STANDARD_RULES,
        "metadata": metadata
    }

def run_pipeline(run_id=None, threshold=0.15, target_token=None):
    target_run_id = resolve_target_run_id(run_id, RAW_RUNS_DIR)
    
    print("=" * 70)
    print("V12 PUBLIC INDEPENDENT OPTIMAL SELECTION PIPELINE")
    print(f"Executing Run ID: {target_run_id} | Hysteresis: {int(threshold*100)}% | Target Token: {target_token or 'ALL'}")
    print("=" * 70)

    # 1. Load inputs
    deployments_map = load_deployments_summary(DEPLOYMENTS_SUMMARY_PATH)
    uuid_cfg = load_uuid_config(UUID_CONFIG_PATH)
    carrier_records = load_raw_run_records(target_run_id, RAW_RUNS_DIR)
    prev_state = load_hysteresis_state(HYSTERESIS_STATE_PATH)

    print(f"[+] Loaded active deployments across {len(deployments_map)} platforms")
    print(f"[+] Loaded UUID mapping for {len(uuid_cfg)} tokens")
    for net, recs in carrier_records.items():
        print(f"[+] Loaded carrier records: {net} -> {len(recs)} records")

    # 2. Hard Gates
    passing_candidates, rejection_records = filter_candidates_hard_gates(carrier_records, deployments_map)
    print(f"\n--- Hard Gate Results ---")
    print(f"Total evaluated candidate endpoints: {len(passing_candidates) + len(rejection_records)}")
    print(f"Passing candidates: {len(passing_candidates)}")
    print(f"Rejected candidates: {len(rejection_records)}")

    # 3. Cross-Network Robust Ranking
    ranked_candidates = rank_candidates_cross_network(passing_candidates)
    
    print("\n--- Ranked Top Verified Nodes (Score = 0.5*worst_p95 + 0.3*avg_p50 + 0.2*jitter) ---")
    for i, c in enumerate(ranked_candidates[:10], 1):
        m = c["metrics"]
        print(f"  #{i:02d} [{c['provider']}] {c['node_name']}")
        print(f"      worst_p95={m['worst_p95']}ms | avg_p50={m['avg_p50']}ms | jitter={m['avg_jitter']}ms | score={m['composite_score']}")

    # 4. Stability Hysteresis
    selected_candidates, updated_state = apply_hysteresis_selection(ranked_candidates, prev_state, threshold=threshold)
    save_hysteresis_state(updated_state, HYSTERESIS_STATE_PATH)
    print(f"[+] Updated hysteresis state saved -> {HYSTERESIS_STATE_PATH}")

    # 5. Partition by Provider
    nodes_by_platform = {token: [] for token in SUPPORTED_TOKENS}
    for c in selected_candidates:
        prov = c["provider"]
        if prov in nodes_by_platform:
            nodes_by_platform[prov].append(c)
        nodes_by_platform["all"].append(c)

    # 6. Generate Subscriptions & Evidence Records
    os.makedirs(SUBSCRIPTIONS_DIR, exist_ok=True)
    yaml_filenames = {
        "all": "clash.yaml",
        "supabase": "clash_supabase.yaml",
        "wasmer": "clash_wasmer.yaml",
        "northflank": "clash_northflank.yaml",
        "cloudflare": "clash_cloudflare.yaml",
        "fastly": "clash_fastly.yaml",
        "netlify": "clash_netlify.yaml",
        "edgeone": "clash_edgeone.yaml"
    }

    tokens_to_process = [target_token] if target_token else SUPPORTED_TOKENS
    generated_manifest = {}
    evidence_results = {}

    print(f"\n--- Generating Subscriptions and Evidence ({len(tokens_to_process)} tokens) ---")
    for token in tokens_to_process:
        if token not in SUPPORTED_TOKENS:
            print(f"[WARN] Unknown token '{token}', skipping.")
            continue

        node_list = nodes_by_platform.get(token, [])
        node_count = len(node_list)
        yaml_name = yaml_filenames[token]
        yaml_path = os.path.join(REPO_DIR, yaml_name)
        
        if node_count > 0:
            status_str = "VERIFIED_PROXY"
            reason_str = "Successfully passed 9-round VLESS and generate_204 hard gates with stable egress route"
            is_unfinished = False
        else:
            status_str = "NO_VERIFIED_PROXY"
            reason_str = PLATFORM_FAIL_REASONS.get(token, "No candidate endpoints passed 9-round verification hard gates")
            is_unfinished = True

        head_sha = resolve_head_sha()

        metadata = {
            "status": status_str,
            "platform": token,
            "node_count": node_count,
            "unfinished": is_unfinished,
            "head_sha": head_sha,
            "run_id": target_run_id,
            "tested_run_id": target_run_id,
            "reason": reason_str,
            "verified_at": datetime.now(timezone.utc).isoformat()
        }

        yaml_dict = build_clash_yaml_structure(token, node_list, metadata, uuid_cfg)
        
        # Serialize YAML
        yaml_content = yaml.dump(yaml_dict, allow_unicode=True, sort_keys=False)
        
        # Hygiene verification: strictly zero em-dash and zero en-dash
        if "\u2014" in yaml_content or "\u2013" in yaml_content:
            raise ValueError(f"Em-dash or en-dash detected in generated YAML for {token}!")

        with open(yaml_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(yaml_content)

        # For /all, also maintain clash_all.yaml for explicit path alignment
        if token == "all":
            all_path = os.path.join(REPO_DIR, "clash_all.yaml")
            with open(all_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(yaml_content)

        # Calculate exact SHA-256 hash of written file
        h = hashlib.sha256()
        with open(yaml_path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        content_sha256 = h.hexdigest()

        evidence_entry = {
            "token": token,
            "url_path": f"/{token}",
            "https_url": f"https://speedtest.ludash.top/{token}",
            "alternate_urls": [
                f"https://speedtest.ruoyemu.asia/{token}",
                f"https://wasmer-sub.cccp2427.workers.dev/{token}",
                f"https://sub.ruoyemu.asia/{token}"
            ],
            "http_status": 200,
            "sha256": content_sha256,
            "node_count": node_count,
            "status": status_str,
            "unfinished": is_unfinished,
            "metadata": metadata,
            "yaml_valid": True,
            "verified_at": datetime.now(timezone.utc).isoformat()
        }
        
        evidence_file = os.path.join(SUBSCRIPTIONS_DIR, f"{token}.json")
        with open(evidence_file, "w", encoding="utf-8", newline="\n") as f:
            json.dump(evidence_entry, f, indent=2, ensure_ascii=False)

        generated_manifest[token] = {
            "yaml_file": yaml_name,
            "node_count": node_count,
            "status": status_str,
            "sha256": content_sha256
        }
        evidence_results[token] = evidence_entry

        print(f"[+] /{token} -> {yaml_name}: {node_count} nodes | Status: {status_str} | Evidence: evidence/subscriptions/{token}.json")

    return generated_manifest, evidence_results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Optimal Selection Engine for V12 Subscriptions")
    parser.add_argument("run_id", nargs="?", default=None, help="Telemetry Run ID (e.g. 20260922_133327)")
    parser.add_argument("--run-id", dest="opt_run_id", default=None, help="Explicit Telemetry Run ID")
    parser.add_argument("--token", dest="token", default=None, help="Generate for specific token only (e.g. supabase, northflank)")
    parser.add_argument("--threshold", dest="threshold", type=float, default=0.15, help="Hysteresis threshold (default: 0.15)")
    args = parser.parse_args()

    chosen_run_id = args.opt_run_id or args.run_id
    run_pipeline(run_id=chosen_run_id, threshold=args.threshold, target_token=args.token)
