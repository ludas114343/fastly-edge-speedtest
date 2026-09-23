#!/usr/bin/env python3
"""
scripts/reconcile_claims.py - V13 Machine Final Reconciler Engine.

Mandate: taskcards/v13/agent-final-reconciler.md
Audits claims against machine-verifiable artifacts across 8 contradiction rules:
- Rule 1: deployment ID count < claimed physical node count -> FAIL
- Rule 2: 0-node platform + unfinished == 0 -> FAIL
- Rule 3: Only relative paths, no full HTTPS URLs -> FAIL
- Rule 4: Evidence root is only local machine path -> FAIL
- Rule 5: Only short SHA, not 40-character SHA -> FAIL
- Rule 6: No workflow run URL or artifact digest -> FAIL
- Rule 7: CHAINED_ESTIMATE described as direct domestic speedtest -> FAIL
- Rule 8: Ingress-only/origin-forwarding platform claimed as independent egress -> FAIL

Pure machine parsing of platform APIs, GitHub API, GitHub artifacts, and online subscriptions.
Zero em-dash (\u2014) and zero en-dash (\u2013) policy strictly enforced.
Output: evidence/reconciliation/machine_verdict.json
"""

import os
import sys
import json
import re
import hashlib
from datetime import datetime, timezone

# Ensure stdout uses UTF-8 without buffer issues
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE_DIR = os.path.join(REPO_ROOT, "evidence")
INVENTORY_DIR = os.path.join(EVIDENCE_DIR, "inventory")
DEPLOYMENTS_DIR = os.path.join(EVIDENCE_DIR, "deployments")
SUBSCRIPTIONS_DIR = os.path.join(EVIDENCE_DIR, "subscriptions")
GITHUB_EVIDENCE_DIR = os.path.join(EVIDENCE_DIR, "github")
RECON_DIR = os.path.join(EVIDENCE_DIR, "reconciliation")
OUTPUT_FILE = os.path.join(RECON_DIR, "machine_verdict.json")

# Platform tokens
PLATFORMS = [
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

def load_json_safe(path):
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def load_yaml_safe(path):
    if not os.path.isfile(path):
        return None
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return None

def check_no_dashes(text, context_name=""):
    assert "\u2014" not in text, f"Character hygiene violation: em-dash (\\u2014) in {context_name}"
    assert "\u2013" not in text, f"Character hygiene violation: en-dash (\\u2013) in {context_name}"

# ==============================================================================
# RULE 1: deployment ID count < claimed physical node count -> FAIL
# ==============================================================================
def eval_rule_1():
    rule_id = 1
    rule_name = "deployment_id_count_vs_claimed_physical_nodes"
    violations = []
    details = {}

    # 1. Wasmer: Authentic physical deployment IDs count <= 4
    wasmer_inv = load_json_safe(os.path.join(INVENTORY_DIR, "wasmer.json")) or {}
    wasmer_dep_summary = (load_json_safe(os.path.join(DEPLOYMENTS_DIR, "summary.json")) or {}).get("platforms", {}).get("Wasmer", {})
    wasmer_yaml = load_yaml_safe(os.path.join(REPO_ROOT, YAML_MAP["wasmer"])) or {}
    wasmer_proxies = wasmer_yaml.get("proxies", [])
    wasmer_published_nodes = len(wasmer_proxies)

    # Dynamically extract authentic deployment IDs from machine inventory and deployment summary
    summary_wasmer_ids = [app.get("deployment_id") for app in wasmer_dep_summary.get("apps", []) if app.get("deployment_id")]
    inv_wasmer_ids = [d.get("deployment_id") for d in wasmer_inv.get("deployments", []) if d.get("deployment_id")]
    authentic_wasmer_deployments = summary_wasmer_ids if summary_wasmer_ids else inv_wasmer_ids
    wasmer_verified_dep_count = len(authentic_wasmer_deployments)
    wasmer_claimed_physical = wasmer_inv.get("DEPLOYMENT_COUNT", len(summary_wasmer_ids))

    details["wasmer"] = {
        "verified_deployment_count": wasmer_verified_dep_count,
        "authentic_deployment_ids": authentic_wasmer_deployments,
        "claimed_physical_nodes": wasmer_claimed_physical,
        "published_proxy_nodes": wasmer_published_nodes
    }

    if wasmer_verified_dep_count == 0:
        violations.append("Wasmer has 0 verified deployment IDs in machine inventory.")
    if wasmer_verified_dep_count > 4:
        violations.append(
            f"Wasmer verified deployment count ({wasmer_verified_dep_count}) exceeds hard ceiling of 4 physical applications."
        )
    if wasmer_verified_dep_count < wasmer_claimed_physical:
        violations.append(
            f"Wasmer deployment ID count ({wasmer_verified_dep_count}) < claimed physical node count ({wasmer_claimed_physical})."
        )
    if wasmer_verified_dep_count < wasmer_published_nodes:
        violations.append(
            f"Wasmer deployment ID count ({wasmer_verified_dep_count}) < published proxy count ({wasmer_published_nodes}). "
            f"Clash config contains {wasmer_published_nodes} proxies exceeding authentic physical deployments."
        )

    # 2. Northflank: Exactly 1 deployment ID
    nf_inv = load_json_safe(os.path.join(INVENTORY_DIR, "northflank.json")) or {}
    nf_dep_summary = (load_json_safe(os.path.join(DEPLOYMENTS_DIR, "summary.json")) or {}).get("platforms", {}).get("Northflank", {})
    nf_yaml = load_yaml_safe(os.path.join(REPO_ROOT, YAML_MAP["northflank"])) or {}
    nf_proxies = nf_yaml.get("proxies", [])
    nf_published_nodes = len(nf_proxies)

    nf_deployments = [d.get("deployment_id") for d in nf_inv.get("deployments", []) if d.get("deployment_id")]
    if not nf_deployments and nf_dep_summary.get("deployment_id"):
        nf_deployments = [nf_dep_summary.get("deployment_id")]
    nf_dep_count = len(nf_deployments)
    nf_claimed_physical = nf_inv.get("DEPLOYMENT_COUNT", 1)

    details["northflank"] = {
        "verified_deployment_count": nf_dep_count,
        "deployment_ids": nf_deployments,
        "claimed_physical_nodes": nf_claimed_physical,
        "published_proxy_nodes": nf_published_nodes
    }

    if nf_dep_count == 0:
        violations.append("Northflank has 0 verified deployment IDs in machine inventory.")
    if nf_dep_count < nf_claimed_physical:
        violations.append(
            f"Northflank deployment ID count ({nf_dep_count}) < claimed physical node count ({nf_claimed_physical})."
        )
    if nf_dep_count < nf_published_nodes:
        violations.append(
            f"Northflank deployment ID count ({nf_dep_count}) < published proxy count ({nf_published_nodes})."
        )

    # 3. Supabase: Exactly 2 physical project deployments
    sb_inv = load_json_safe(os.path.join(INVENTORY_DIR, "supabase.json")) or {}
    sb_dep_summary = (load_json_safe(os.path.join(DEPLOYMENTS_DIR, "summary.json")) or {}).get("platforms", {}).get("Supabase", {})
    sb_claimed_physical = sb_dep_summary.get("physical_deployments_count", sb_inv.get("DEPLOYMENT_COUNT", 2))

    authentic_sb_deployments = [acc.get("deployment_id") for acc in sb_dep_summary.get("accounts", []) if acc.get("deployment_id")]
    sb_verified_dep_count = len(authentic_sb_deployments)

    sb_yaml = load_yaml_safe(os.path.join(REPO_ROOT, YAML_MAP["supabase"])) or {}
    sb_proxies = sb_yaml.get("proxies", [])
    sb_regional_routes_count = len(sb_proxies)

    details["supabase"] = {
        "verified_deployment_count": sb_verified_dep_count,
        "authentic_deployment_ids": authentic_sb_deployments,
        "claimed_physical_nodes": sb_claimed_physical,
        "regional_invocation_routes_count": sb_regional_routes_count,
        "note": "Regional routes via forceFunctionRegion are invocation routes, not independent physical backends"
    }

    if sb_verified_dep_count == 0:
        violations.append("Supabase has 0 verified deployment IDs in deployments summary.")
    if sb_verified_dep_count < sb_claimed_physical:
        violations.append(
            f"Supabase physical deployment count ({sb_verified_dep_count}) < claimed physical node count ({sb_claimed_physical})."
        )

    # 4. Zero-node platforms: Cloudflare, Fastly, Netlify, EdgeOne
    zero_platforms = ["cloudflare", "fastly", "netlify", "edgeone"]
    for zp in zero_platforms:
        zyaml = load_yaml_safe(os.path.join(REPO_ROOT, YAML_MAP[zp]))
        zproxies = zyaml.get("proxies", []) if zyaml else []
        details[zp] = {
            "verified_deployment_count": 0,
            "claimed_proxy_node_count": len(zproxies)
        }
        if len(zproxies) > 0:
            violations.append(
                f"{zp} has 0 verified physical proxy deployments but claims {len(zproxies)} proxy nodes."
            )

    # 5. Combined Subscription clash.yaml audit
    clash_all_yaml = load_yaml_safe(os.path.join(REPO_ROOT, "clash.yaml")) or {}
    all_proxies = clash_all_yaml.get("proxies", [])
    details["combined_subscription_clash_yaml"] = {
        "total_proxies": len(all_proxies),
        "expected_proxies": 21
    }
    if len(all_proxies) != 21:
        violations.append(
            f"Combined subscription clash.yaml contains {len(all_proxies)} proxies, expected 21 "
            "(16 Supabase regional invocation routes + 4 Wasmer + 1 Northflank)."
        )

    status = "FAIL" if violations else "PASS"
    return {
        "rule_id": rule_id,
        "rule_name": rule_name,
        "status": status,
        "violations": violations,
        "details": details
    }

# ==============================================================================
# RULE 2: 0-node platform + unfinished == 0 -> FAIL
# ==============================================================================
def eval_rule_2():
    rule_id = 2
    rule_name = "zero_node_platform_must_have_unfinished_flag"
    violations = []
    details = {}

    zero_platforms = ["cloudflare", "fastly", "netlify", "edgeone"]
    unfinished_true_count = 0

    for token in zero_platforms:
        yaml_path = os.path.join(REPO_ROOT, YAML_MAP[token])
        ev_path = os.path.join(SUBSCRIPTIONS_DIR, f"{token}.json")
        inv_path = os.path.join(INVENTORY_DIR, f"{token}.json")

        parsed_yaml = load_yaml_safe(yaml_path) or {}
        yaml_proxies = parsed_yaml.get("proxies", [])
        yaml_meta = parsed_yaml.get("metadata", {})

        ev_data = load_json_safe(ev_path) or {}
        ev_meta = ev_data.get("metadata", {})

        inv_data = load_json_safe(inv_path) or {}

        yaml_unfinished = yaml_meta.get("unfinished")
        yaml_status = yaml_meta.get("status")
        ev_unfinished = ev_data.get("unfinished", ev_meta.get("unfinished"))
        ev_status = ev_data.get("status")
        inv_unfinished = inv_data.get("unfinished")
        inv_status = inv_data.get("status")

        is_zero_node = len(yaml_proxies) == 0

        details[token] = {
            "zero_node": is_zero_node,
            "yaml_status": yaml_status,
            "yaml_unfinished": yaml_unfinished,
            "evidence_status": ev_status,
            "evidence_unfinished": ev_unfinished,
            "inventory_status": inv_status,
            "inventory_unfinished": inv_unfinished
        }

        if is_zero_node:
            # Rigorous audit: Every source (subscription YAML metadata, evidence JSON, inventory JSON)
            # representing a 0-node platform MUST declare unfinished: true and status: NO_VERIFIED_PROXY.
            if yaml_unfinished is not True:
                violations.append(
                    f"Platform {token} subscription YAML metadata lacks unfinished: true flag (got {yaml_unfinished})."
                )
            if yaml_status != "NO_VERIFIED_PROXY":
                violations.append(
                    f"Platform {token} subscription YAML metadata status is '{yaml_status}', expected 'NO_VERIFIED_PROXY'."
                )
            if ev_unfinished is not True:
                violations.append(
                    f"Platform {token} subscription evidence lacks unfinished: true flag (got {ev_unfinished})."
                )
            if ev_status != "NO_VERIFIED_PROXY":
                violations.append(
                    f"Platform {token} subscription evidence status is '{ev_status}', expected 'NO_VERIFIED_PROXY'."
                )
            if inv_unfinished is not True:
                violations.append(
                    f"Platform {token} inventory lacks unfinished: true flag (got {inv_unfinished})."
                )
            if inv_status != "NO_VERIFIED_PROXY":
                violations.append(
                    f"Platform {token} inventory status is '{inv_status}', expected 'NO_VERIFIED_PROXY'."
                )

            if (yaml_unfinished is True and ev_unfinished is True and inv_unfinished is True and
                yaml_status == "NO_VERIFIED_PROXY" and ev_status == "NO_VERIFIED_PROXY" and inv_status == "NO_VERIFIED_PROXY"):
                unfinished_true_count += 1
        else:
            violations.append(
                f"Platform {token} is categorized as zero-node platform but has {len(yaml_proxies)} proxies in YAML."
            )

    details["total_unfinished_zero_node_platforms"] = unfinished_true_count
    if unfinished_true_count < len(zero_platforms):
        violations.append(
            f"Expected {len(zero_platforms)} zero-node platforms marked with unfinished: true, found {unfinished_true_count}."
        )

    status = "FAIL" if violations else "PASS"
    return {
        "rule_id": rule_id,
        "rule_name": rule_name,
        "status": status,
        "violations": violations,
        "details": details
    }

# ==============================================================================
# RULE 3: Only relative paths, no full HTTPS URLs -> FAIL
# ==============================================================================
def eval_rule_3():
    rule_id = 3
    rule_name = "full_https_urls_required_no_relative_only"
    violations = []
    details = {}

    all_tokens = ["all"] + PLATFORMS
    relative_paths_found = []
    https_urls_found = []
    missing_https_tokens = []

    for token in all_tokens:
        ev_path = os.path.join(SUBSCRIPTIONS_DIR, f"{token}.json")
        ev_data = load_json_safe(ev_path)
        if not ev_data:
            missing_https_tokens.append(f"{token} (file missing)")
            continue

        url_path = ev_data.get("url_path")
        https_url = ev_data.get("https_url") or ev_data.get("url")

        if url_path and not str(url_path).startswith("http"):
            relative_paths_found.append(f"{token}: {url_path}")

        if https_url and str(https_url).startswith("https://"):
            https_urls_found.append(f"{token}: {https_url}")
        else:
            missing_https_tokens.append(f"{token} (missing full https URL, got: {https_url})")

    details["relative_paths_in_evidence"] = relative_paths_found
    details["https_urls_in_evidence"] = https_urls_found
    details["missing_https_tokens"] = missing_https_tokens

    # Expected public HTTPS endpoints
    expected_endpoints = [
        f"https://speedtest.ludash.top/{t}" for t in all_tokens
    ]
    details["expected_public_https_endpoints"] = expected_endpoints

    if missing_https_tokens:
        violations.append(
            f"Subscription evidence lacks full verified HTTPS URLs for tokens: {missing_https_tokens}. "
            "Every subscription deliverable must provide a full public HTTPS endpoint."
        )

    if len(https_urls_found) < len(all_tokens):
        violations.append(
            f"Only {len(https_urls_found)} / {len(all_tokens)} subscription tokens have full HTTPS URLs."
        )

    status = "FAIL" if violations else "PASS"
    return {
        "rule_id": rule_id,
        "rule_name": rule_name,
        "status": status,
        "violations": violations,
        "details": details
    }

# ==============================================================================
# RULE 4: Evidence root is only local machine path -> FAIL
# ==============================================================================
def eval_rule_4():
    rule_id = 4
    rule_name = "remote_evidence_root_required_no_local_only"
    violations = []
    details = {}

    repo_ev = load_json_safe(os.path.join(GITHUB_EVIDENCE_DIR, "repository.json"))
    dep_summary = load_json_safe(os.path.join(DEPLOYMENTS_DIR, "summary.json"))
    bootstrap = load_json_safe(os.path.join(REPO_ROOT, "orchestration", "bootstrap_receipt.json"))

    details["repository_evidence_loaded"] = bool(repo_ev)
    details["deployments_summary_loaded"] = bool(dep_summary)
    details["bootstrap_receipt_loaded"] = bool(bootstrap)

    # Check if remote repository metadata is verified
    remote_repo_url = None
    if repo_ev:
        remote_repo_url = repo_ev.get("repository", {}).get("html_url")
    elif bootstrap:
        remote_repo_url = bootstrap.get("repository_url")

    details["remote_repo_url"] = remote_repo_url

    # Check for local-only absolute machine paths in evidence records
    local_only_fields = []

    if dep_summary:
        modes_file = dep_summary.get("platforms", {}).get("Cloudflare", {}).get("modes_comparison_file")
        if modes_file and not str(modes_file).startswith("http"):
            local_only_fields.append(f"Cloudflare.modes_comparison_file: {modes_file}")

    # Inspect subscription evidence files for local machine paths
    for token in ["all"] + PLATFORMS:
        ev_path = os.path.join(SUBSCRIPTIONS_DIR, f"{token}.json")
        ev_data = load_json_safe(ev_path) or {}
        raw_ev = json.dumps(ev_data)
        if "C:\\Users" in raw_ev or "C:/Users" in raw_ev or "/Users/ludas" in raw_ev:
            local_only_fields.append(f"subscriptions/{token}.json contains local machine path")

    details["local_only_fields"] = local_only_fields

    # Verify remote repository anchor
    if not remote_repo_url or not str(remote_repo_url).startswith("https://"):
        violations.append(
            "Evidence root is only local machine path. No verified remote repository HTTPS root anchor found."
        )

    # Verify remote HEAD commit SHA exists and is valid
    remote_head_sha = repo_ev.get("remote_head", {}).get("sha") if repo_ev else None
    details["remote_head_sha"] = remote_head_sha
    if not remote_head_sha or len(str(remote_head_sha)) != 40:
        violations.append(
            f"Evidence repository remote head SHA missing or invalid: {remote_head_sha}."
        )

    if local_only_fields:
        violations.append(
            f"Evidence records contain local machine absolute paths without remote HTTPS anchors: {local_only_fields}."
        )

    status = "FAIL" if violations else "PASS"
    return {
        "rule_id": rule_id,
        "rule_name": rule_name,
        "status": status,
        "violations": violations,
        "details": details
    }

# ==============================================================================
# RULE 5: Only short SHA, not 40-character SHA -> FAIL
# ==============================================================================
def eval_rule_5():
    rule_id = 5
    rule_name = "full_40_char_sha_required_no_short_sha"
    violations = []
    details = {}

    sha_pattern = re.compile(r"^[0-9a-fA-F]{40}$")

    # 1. Check bootstrap receipt
    bootstrap = load_json_safe(os.path.join(REPO_ROOT, "orchestration", "bootstrap_receipt.json"))
    if bootstrap:
        b_sha = bootstrap.get("remote_head_sha", "")
        details["bootstrap_remote_head_sha"] = b_sha
        if not sha_pattern.match(b_sha):
            violations.append(
                f"Bootstrap receipt contains invalid or short commit SHA: '{b_sha}' (length: {len(b_sha)})."
            )

    # 2. Check GitHub auditor evidence
    repo_ev = load_json_safe(os.path.join(GITHUB_EVIDENCE_DIR, "repository.json"))
    if repo_ev:
        r_sha = repo_ev.get("remote_head", {}).get("sha", "")
        details["github_evidence_remote_head_sha"] = r_sha
        if not sha_pattern.match(r_sha):
            violations.append(
                f"GitHub repository evidence contains invalid or short commit SHA: '{r_sha}' (length: {len(r_sha)})."
            )

    # 3. Check subscription evidence metadata: must contain full 40-character head_sha
    sub_shas = {}
    missing_sub_shas = []
    for token in ["all"] + PLATFORMS:
        ev_path = os.path.join(SUBSCRIPTIONS_DIR, f"{token}.json")
        ev_data = load_json_safe(ev_path)
        if ev_data:
            meta = ev_data.get("metadata", {})
            head_sha = meta.get("head_sha") or ev_data.get("head_sha")
            sub_shas[token] = head_sha
            if not head_sha or not sha_pattern.match(str(head_sha)):
                missing_sub_shas.append(token)

    details["subscription_head_shas"] = sub_shas
    if missing_sub_shas:
        violations.append(
            f"Subscription evidence metadata lacks full 40-character head_sha for tokens: {missing_sub_shas}. "
            "Task card requires full 40-character head_sha in all subscription metadata."
        )

    # 4. Check client-facing subscription YAML files for 40-character head_sha
    yaml_shas = {}
    missing_yaml_shas = []
    for token in ["all"] + PLATFORMS:
        y_path = os.path.join(REPO_ROOT, YAML_MAP[token])
        y_data = load_yaml_safe(y_path)
        if y_data:
            y_meta = y_data.get("metadata", {})
            y_sha = y_meta.get("head_sha")
            yaml_shas[token] = y_sha
            if not y_sha or not sha_pattern.match(str(y_sha)):
                missing_yaml_shas.append(token)

    details["subscription_yaml_head_shas"] = yaml_shas
    if missing_yaml_shas:
        violations.append(
            f"Client subscription YAML metadata lacks full 40-character head_sha for tokens: {missing_yaml_shas}."
        )

    # 5. Check production release current.json manifest
    prod_current = load_json_safe(os.path.join(REPO_ROOT, "production", "current.json"))
    if prod_current:
        p_sha = prod_current.get("head_sha", "")
        details["production_current_head_sha"] = p_sha
        if not sha_pattern.match(p_sha):
            violations.append(
                f"Production current.json manifest contains invalid or short commit SHA: '{p_sha}'."
            )

    status = "FAIL" if violations else "PASS"
    return {
        "rule_id": rule_id,
        "rule_name": rule_name,
        "status": status,
        "violations": violations,
        "details": details
    }

# ==============================================================================
# RULE 6: No workflow run URL or artifact digest -> FAIL
# ==============================================================================
def eval_rule_6():
    rule_id = 6
    rule_name = "workflow_run_url_and_artifact_digest_required"
    violations = []
    details = {}

    wf_ev = load_json_safe(os.path.join(GITHUB_EVIDENCE_DIR, "workflows.json"))
    details["workflows_evidence_loaded"] = bool(wf_ev)

    if wf_ev:
        # Check artifacts
        artifacts_meta = wf_ev.get("artifacts_inventory", {})
        artifacts_count = artifacts_meta.get("total_count", 0)
        details["remote_artifacts_total_count"] = artifacts_count

        artifacts_list = artifacts_meta.get("artifacts", [])
        verified_artifact_digests = [
            a.get("digest") for a in artifacts_list if a.get("digest") and str(a.get("digest")).startswith("sha256:")
        ]
        details["verified_artifact_digests_count"] = len(verified_artifact_digests)

        # Check registered workflows
        registered = wf_ev.get("actions_workflows", [])
        wf_paths = [w.get("path") for w in registered]
        details["remote_registered_workflow_paths"] = wf_paths

        # Check workflow runs
        runs = wf_ev.get("workflow_runs", [])
        details["remote_workflow_runs_count"] = len(runs)
        verified_run_urls = [r.get("html_url") for r in runs if r.get("html_url")]
        details["verified_workflow_run_urls_count"] = len(verified_run_urls)

        # Rigorous check: verify ALL required V13 deployment and audit workflows exist on remote
        required_v13_workflows = [
            "external-blackbox-audit.yml",
            "deploy-wasmer.yml",
            "deploy-supabase.yml",
            "deploy-northflank.yml",
            "deploy-cloudflare.yml",
            "deploy-fastly.yml",
            "deploy-netlify.yml",
            "deploy-edgeone.yml",
            "publish-subscriptions.yml",
            "smoke-test.yml"
        ]
        missing_workflows = [w for w in required_v13_workflows if not any(w in p for p in wf_paths)]
        details["missing_v13_workflows"] = missing_workflows
        details["remote_has_all_v13_workflows"] = len(missing_workflows) == 0

        if missing_workflows:
            violations.append(
                f"Missing required V13 deployment/audit workflows on remote: {missing_workflows}."
            )

        if artifacts_count == 0 or len(verified_artifact_digests) == 0:
            violations.append(
                "Remote GitHub Actions artifacts count is 0 or lacks verified SHA-256 digest. "
                "No artifact URL or SHA-256 digest exists for blackbox audit or subscription release."
            )

        if len(verified_run_urls) == 0:
            violations.append(
                "No verified GitHub Actions workflow run URLs found in repository evidence."
            )

    else:
        violations.append(
            "Missing evidence/github/workflows.json. No GitHub Actions workflow run URLs or artifact records available."
        )

    status = "FAIL" if violations else "PASS"
    return {
        "rule_id": rule_id,
        "rule_name": rule_name,
        "status": status,
        "violations": violations,
        "details": details
    }

# ==============================================================================
# RULE 7: CHAINED_ESTIMATE described as direct domestic speedtest -> FAIL
# ==============================================================================
def eval_rule_7():
    rule_id = 7
    rule_name = "chained_estimate_methodology_disclosure"
    violations = []
    details = {}

    forbidden_phrases = [
        "真实三网直测",
        "国内端到端直测",
        "国内物理直连测速",
        "真实国内直测",
        "genuine China 3-Network measurement pipeline",
        "genuine China 3-Network measurement",
        "中国三网测速流水线"
    ]

    # 1. Machine telemetry route-proof inspection
    route_proof_dir = os.path.join(REPO_ROOT, "results", "route-proof")
    has_chained_estimate_in_route_proof = False
    route_proof_files = []
    contradictions_in_telemetry = []

    if os.path.isdir(route_proof_dir):
        for rf in os.listdir(route_proof_dir):
            if rf.endswith(".json"):
                rf_path = os.path.join(route_proof_dir, rf)
                route_proof_files.append(rf)
                rf_data = load_json_safe(rf_path) or {}
                raw_text = json.dumps(rf_data, ensure_ascii=False)
                if rf_data.get("methodology") == "CHAINED_ESTIMATE" or "CHAINED_ESTIMATE" in raw_text:
                    has_chained_estimate_in_route_proof = True
                for phrase in forbidden_phrases:
                    if phrase in raw_text:
                        contradictions_in_telemetry.append(f"{rf}: '{phrase}'")

    details["route_proof_files"] = route_proof_files
    details["has_chained_estimate_in_route_proof"] = has_chained_estimate_in_route_proof

    # 2. Raw telemetry manifests inspection
    has_chained_estimate_in_manifest = False
    raw_dir = os.path.join(REPO_ROOT, "results", "raw")
    if os.path.isdir(raw_dir):
        for run_id in os.listdir(raw_dir):
            m_path = os.path.join(raw_dir, run_id, "manifest.json")
            if os.path.isfile(m_path):
                m_data = load_json_safe(m_path) or {}
                raw_m_text = json.dumps(m_data, ensure_ascii=False)
                if m_data.get("methodology") == "CHAINED_ESTIMATE" or "CHAINED_ESTIMATE" in raw_m_text:
                    has_chained_estimate_in_manifest = True
                for phrase in forbidden_phrases:
                    if phrase in raw_m_text:
                        contradictions_in_telemetry.append(f"manifest_{run_id}: '{phrase}'")

    details["has_chained_estimate_in_manifest"] = has_chained_estimate_in_manifest

    # 3. Route proof methodology disclosure file
    rp_readme = os.path.join(route_proof_dir, "README.md")
    readme_discloses_chained = False
    if os.path.isfile(rp_readme):
        with open(rp_readme, "r", encoding="utf-8") as f:
            rp_readme_text = f.read()
        if "CHAINED_ESTIMATE" in rp_readme_text and "overhead" in rp_readme_text.lower():
            readme_discloses_chained = True
    details["route_proof_readme_discloses_chained"] = readme_discloses_chained

    # 4. Unified telemetry manifest inspection
    telemetry_manifest = load_json_safe(os.path.join(REPO_ROOT, "results", "telemetry", "manifest.json")) or {}
    has_chained_in_telemetry = (telemetry_manifest.get("methodology") == "CHAINED_ESTIMATE")
    details["has_chained_in_telemetry_manifest"] = has_chained_in_telemetry
    raw_tm_text = json.dumps(telemetry_manifest, ensure_ascii=False)
    for phrase in forbidden_phrases:
        if phrase in raw_tm_text:
            contradictions_in_telemetry.append(f"telemetry_manifest: '{phrase}'")

    details["contradictions_in_telemetry"] = contradictions_in_telemetry

    if not has_chained_estimate_in_route_proof and not has_chained_estimate_in_manifest and not has_chained_in_telemetry:
        violations.append(
            "Speedtest telemetry and route-proof evidence lack mandatory CHAINED_ESTIMATE methodology declaration. "
            "Task card requires explicit documentation that testing mode is CHAINED_ESTIMATE with route overhead."
        )

    if not has_chained_in_telemetry:
        violations.append(
            "Unified telemetry manifest (results/telemetry/manifest.json) lacks methodology: 'CHAINED_ESTIMATE'."
        )

    if not readme_discloses_chained:
        violations.append(
            "Route proof documentation (results/route-proof/README.md) lacks explicit CHAINED_ESTIMATE overhead disclosure."
        )

    if contradictions_in_telemetry:
        violations.append(
            f"Measurement methodology improperly characterized with forbidden domestic direct speedtest phrases: {contradictions_in_telemetry}. "
            "Testing performed via overseas runners or intermediate proxies must be explicitly labeled as CHAINED_ESTIMATE "
            "with disclosed route overhead, never as direct domestic user-terminal speedtest."
        )

    status = "FAIL" if violations else "PASS"
    return {
        "rule_id": rule_id,
        "rule_name": rule_name,
        "status": status,
        "violations": violations,
        "details": details
    }

# ==============================================================================
# RULE 8: Ingress-only/origin-forwarding platform claimed as independent egress -> FAIL
# ==============================================================================
def eval_rule_8():
    rule_id = 8
    rule_name = "ingress_forwarding_vs_independent_egress"
    violations = []
    details = {}

    dep_summary = load_json_safe(os.path.join(DEPLOYMENTS_DIR, "summary.json")) or {}
    inv_summary = load_json_safe(os.path.join(INVENTORY_DIR, "summary.json")) or {}

    fronting_platforms = ["cloudflare", "fastly", "edgeone"]
    ws_limited_platforms = ["netlify"]

    # 1. Check clash YAML configs for published proxies
    published_fronting_proxies = {}
    for p in fronting_platforms + ws_limited_platforms:
        yaml_path = os.path.join(REPO_ROOT, YAML_MAP[p])
        parsed = load_yaml_safe(yaml_path) or {}
        proxies = parsed.get("proxies", [])
        published_fronting_proxies[p] = len(proxies)
        if len(proxies) > 0:
            violations.append(
                f"{p} is an ingress fronting or WS-ingress-limited platform but published {len(proxies)} proxy nodes as independent egress."
            )

    details["published_fronting_proxies"] = published_fronting_proxies

    # 2. Check clash.yaml (combined subscription) for fronting platform domain leaks
    clash_all = load_yaml_safe(os.path.join(REPO_ROOT, "clash.yaml")) or {}
    fronting_domains = ["fastly.net", "eo-edgefunctions1.com", "workers.dev", "netlify.app", "dream.ruoyemu.asia", "net.ruoyemu.asia"]
    fronting_leaks_in_combined = []
    for prx in clash_all.get("proxies", []):
        srv = prx.get("server", "")
        for fd in fronting_domains:
            if fd in srv:
                fronting_leaks_in_combined.append(f"{prx.get('name')}: {srv}")

    details["fronting_leaks_in_combined"] = fronting_leaks_in_combined
    if fronting_leaks_in_combined:
        violations.append(
            f"Combined subscription clash.yaml contains fronting/ingress domains published as proxies: {fronting_leaks_in_combined}."
        )

    # 3. Check evidence/subscriptions/<platform>.json
    sub_fronting_node_counts = {}
    for p in fronting_platforms + ws_limited_platforms:
        ev_path = os.path.join(SUBSCRIPTIONS_DIR, f"{p}.json")
        ev_data = load_json_safe(ev_path) or {}
        n_count = ev_data.get("node_count", 0)
        p_status = ev_data.get("status")
        sub_fronting_node_counts[p] = {"node_count": n_count, "status": p_status}
        if n_count > 0:
            violations.append(
                f"{p} subscription evidence claims {n_count} nodes as independent egress."
            )
        if p_status == "VERIFIED_PROXY":
            violations.append(
                f"{p} subscription evidence has status VERIFIED_PROXY instead of NO_VERIFIED_PROXY."
            )

    details["subscription_fronting_evidence"] = sub_fronting_node_counts

    # 4. Check deployments summary platform roles and active direct backends
    platforms_meta = dep_summary.get("platforms", {})
    active_direct_backends = dep_summary.get("active_direct_backends", [])
    zero_proxy_platforms = dep_summary.get("zero_proxy_platforms", [])

    details["active_direct_backends"] = active_direct_backends
    details["zero_proxy_platforms"] = zero_proxy_platforms

    for fp in fronting_platforms:
        p_capital = fp.capitalize() if fp != "edgeone" else "EdgeOne"
        if p_capital in active_direct_backends:
            violations.append(
                f"{p_capital} is an ingress fronting layer (CAPABLE_FRONT) but is registered in active_direct_backends."
            )
        p_info = platforms_meta.get(p_capital, {})
        if p_info.get("role") == "CAPABLE_DIRECT":
            violations.append(
                f"{p_capital} incorrectly marked as CAPABLE_DIRECT instead of CAPABLE_FRONT."
            )

    # Netlify WS ingress limitation check
    netlify_info = platforms_meta.get("Netlify", {})
    if netlify_info:
        if netlify_info.get("verified_proxy_count", 0) > 0:
            violations.append(
                "Netlify claims verified proxy count > 0 despite RFC 6455 WebSocket 101 ingress termination limitation."
            )
        if netlify_info.get("role") == "CAPABLE_DIRECT":
            violations.append(
                "Netlify marked as CAPABLE_DIRECT without disclosing WS ingress 502 limitation and L4 standby role."
            )

    status = "FAIL" if violations else "PASS"
    return {
        "rule_id": rule_id,
        "rule_name": rule_name,
        "status": status,
        "violations": violations,
        "details": details
    }

# ==============================================================================
# Main Orchestration & Output Generation
# ==============================================================================
def run_reconciliation():
    print("=" * 80)
    print("V13 MACHINE FINAL RECONCILIATION ENGINE (scripts/reconcile_claims.py)")
    print("=" * 80)

    now_iso = datetime.now(timezone.utc).isoformat()

    evaluators = [
        eval_rule_1,
        eval_rule_2,
        eval_rule_3,
        eval_rule_4,
        eval_rule_5,
        eval_rule_6,
        eval_rule_7,
        eval_rule_8
    ]

    results = {}
    passed_count = 0
    failed_count = 0

    for ev in evaluators:
        res = ev()
        r_id = f"rule_{res['rule_id']}_{res['rule_name']}"
        results[r_id] = res

        prefix = "[PASS]" if res["status"] == "PASS" else "[FAIL]"
        print(f"\n{prefix} Rule {res['rule_id']}: {res['rule_name']}")
        if res["violations"]:
            for v in res["violations"]:
                print(f"       - Violation: {v}")
        else:
            print("       - Clean: No contradiction detected.")

        if res["status"] == "PASS":
            passed_count += 1
        else:
            failed_count += 1

    overall_verdict = "PASS" if failed_count == 0 else "FAIL"
    report_blocked = (overall_verdict == "FAIL")

    blocking_reason = (
        f"Reconciliation detected {failed_count} contradiction violation(s) across 8 rules. "
        "Under Definition of Done and Mandate Rule 3, report generation is strictly BLOCKED."
        if report_blocked else None
    )

    verdict_data = {
        "version": "v13",
        "auditor": "agent-final-reconciler",
        "timestamp": now_iso,
        "overall_verdict": overall_verdict,
        "report_generation_blocked": report_blocked,
        "blocking_reason": blocking_reason,
        "rules_summary": {
            "total_rules": len(evaluators),
            "passed_count": passed_count,
            "failed_count": failed_count
        },
        "rules": results
    }

    # Verify character hygiene before serialization
    verdict_json_str = json.dumps(verdict_data, indent=2, ensure_ascii=False)
    check_no_dashes(verdict_json_str, "machine_verdict.json content")

    os.makedirs(RECON_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(verdict_json_str)

    print("\n" + "=" * 80)
    print(f"FINAL MACHINE VERDICT: {overall_verdict}")
    print(f"Passed Rules: {passed_count} / {len(evaluators)}")
    print(f"Failed Rules: {failed_count} / {len(evaluators)}")
    print(f"Report Generation Blocked: {report_blocked}")
    print(f"Deliverable Output: {OUTPUT_FILE}")
    print("=" * 80)

    # Re-verify written file
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        saved_text = f.read()
    check_no_dashes(saved_text, "saved machine_verdict.json")
    print("[PASS] Character hygiene verified: strictly zero em-dashes and zero en-dashes.")

    return verdict_data

if __name__ == "__main__":
    verdict = run_reconciliation()
    if "--strict" in sys.argv or "--fail-on-violation" in sys.argv:
        sys.exit(1 if verdict["report_generation_blocked"] else 0)
    sys.exit(0)
