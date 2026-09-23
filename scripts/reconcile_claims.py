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
    # Task card: Only 4 authentic physical deployments exist
    # (dav_RjPIgtzuJwQ9, dav_2VbInozrPwQz, dav_6N1Ip1znJwA1, dav_8V7IzpyjPlnE)
    wasmer_inv = load_json_safe(os.path.join(INVENTORY_DIR, "wasmer.json"))
    wasmer_yaml = load_yaml_safe(os.path.join(REPO_ROOT, "clash_wasmer.yaml"))
    wasmer_proxies = wasmer_yaml.get("proxies", []) if wasmer_yaml else []
    wasmer_claimed_nodes = len(wasmer_proxies)

    # Wasmer deployment IDs verified
    authentic_wasmer_deployments = [
        "dav_RjPIgtzuJwQ9",
        "dav_2VbInozrPwQz",
        "dav_6N1Ip1znJwA1",
        "dav_8V7IzpyjPlnE"
    ]
    wasmer_verified_dep_count = len(authentic_wasmer_deployments)

    details["wasmer"] = {
        "verified_deployment_count": wasmer_verified_dep_count,
        "authentic_deployment_ids": authentic_wasmer_deployments,
        "claimed_proxy_node_count": wasmer_claimed_nodes
    }

    if wasmer_verified_dep_count < wasmer_claimed_nodes:
        violations.append(
            f"Wasmer deployment ID count ({wasmer_verified_dep_count}) < claimed node count ({wasmer_claimed_nodes}). "
            f"Clash config contains {wasmer_claimed_nodes} proxies exceeding 4 authentic physical deployments."
        )

    # 2. Northflank: Exactly 1 deployment ID (0f2371aed029418170507fc7f0cbe3b3f6d2c943)
    nf_inv = load_json_safe(os.path.join(INVENTORY_DIR, "northflank.json"))
    nf_yaml = load_yaml_safe(os.path.join(REPO_ROOT, "clash_northflank.yaml"))
    nf_proxies = nf_yaml.get("proxies", []) if nf_yaml else []
    nf_claimed_nodes = len(nf_proxies)
    nf_dep_count = 1

    details["northflank"] = {
        "verified_deployment_count": nf_dep_count,
        "deployment_id": "0f2371aed029418170507fc7f0cbe3b3f6d2c943",
        "claimed_proxy_node_count": nf_claimed_nodes
    }

    if nf_dep_count < nf_claimed_nodes:
        violations.append(
            f"Northflank deployment ID count ({nf_dep_count}) < claimed node count ({nf_claimed_nodes})."
        )

    # Check historical or ledger claims for Northflank (e.g. 34 nodes in legacy ledger)
    ledger_path = os.path.join(REPO_ROOT, "orchestration", "ledger.md")
    if os.path.isfile(ledger_path):
        with open(ledger_path, "r", encoding="utf-8") as f:
            ledger_text = f.read()
        if "Northflank" in ledger_text and "34" in ledger_text:
            details["northflank"]["legacy_claim_detected"] = "Legacy claim of 34 nodes for Northflank"

    # 3. Supabase: 2 physical project deployments
    # (theecyezvuzkflwikxwr, gwgiogtgdyrqlexcdjqm)
    # Regional invocation routes (forceFunctionRegion) provide geographic diversity, not 16 independent physical deployments.
    sb_inv = load_json_safe(os.path.join(INVENTORY_DIR, "supabase.json"))
    sb_yaml = load_yaml_safe(os.path.join(REPO_ROOT, "clash_supabase.yaml"))
    sb_proxies = sb_yaml.get("proxies", []) if sb_yaml else []
    sb_claimed_nodes = len(sb_proxies)
    sb_physical_deployments = 2

    details["supabase"] = {
        "physical_project_deployments": sb_physical_deployments,
        "claimed_proxy_node_count": sb_claimed_nodes,
        "note": "Regional routes via forceFunctionRegion are invocation routes, not independent physical backends"
    }

    if sb_physical_deployments < sb_claimed_nodes:
        violations.append(
            f"Supabase physical deployment count ({sb_physical_deployments}) < claimed node count ({sb_claimed_nodes}). "
            f"Regional routes mischaracterized as independent physical deployments without 1:1 physical deployment mapping."
        )

    # 4. Zero-node platforms: Cloudflare, Fastly, Netlify, EdgeOne
    # Verified physical proxy deployments = 0.
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

        parsed_yaml = load_yaml_safe(yaml_path) or {}
        yaml_proxies = parsed_yaml.get("proxies", [])
        yaml_meta = parsed_yaml.get("metadata", {})

        ev_data = load_json_safe(ev_path) or {}
        ev_meta = ev_data.get("metadata", {})

        yaml_unfinished = yaml_meta.get("unfinished")
        ev_unfinished = ev_data.get("unfinished", ev_meta.get("unfinished"))

        is_zero_node = len(yaml_proxies) == 0

        details[token] = {
            "zero_node": is_zero_node,
            "yaml_status": yaml_meta.get("status"),
            "yaml_unfinished": yaml_unfinished,
            "evidence_status": ev_data.get("status"),
            "evidence_unfinished": ev_unfinished
        }

        if is_zero_node:
            if yaml_unfinished is not True or ev_unfinished is not True:
                violations.append(
                    f"Platform {token} is a 0-node platform (proxies: 0) but unfinished flag is not set to true. "
                    f"yaml_unfinished={yaml_unfinished}, evidence_unfinished={ev_unfinished}."
                )
            if yaml_unfinished is True and ev_unfinished is True:
                unfinished_true_count += 1

    details["total_unfinished_zero_node_platforms"] = unfinished_true_count
    if unfinished_true_count == 0:
        violations.append(
            "Total count of 0-node platforms marked with unfinished: true is 0. "
            "All 0-node platforms must explicitly declare unfinished: true and status: NO_VERIFIED_PROXY."
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

    relative_paths_found = []
    https_urls_found = []

    # Check evidence/subscriptions/*.json
    for token in ["all"] + PLATFORMS:
        ev_path = os.path.join(SUBSCRIPTIONS_DIR, f"{token}.json")
        ev_data = load_json_safe(ev_path)
        if ev_data:
            url_path = ev_data.get("url_path")
            https_url = ev_data.get("https_url") or ev_data.get("url")

            if url_path and not str(url_path).startswith("http"):
                relative_paths_found.append(f"{token}: {url_path}")

            if https_url and str(https_url).startswith("https://"):
                https_urls_found.append(f"{token}: {https_url}")

    details["relative_paths_in_evidence"] = relative_paths_found
    details["https_urls_in_evidence"] = https_urls_found

    # Expected public HTTPS endpoints
    expected_endpoints = [
        f"https://speedtest.ludash.top/{t}" for t in ["all"] + PLATFORMS
    ]
    details["expected_public_https_endpoints"] = expected_endpoints

    if len(https_urls_found) == 0:
        violations.append(
            "Evidence subscriptions contain only relative paths (e.g. url_path: '/all') and zero full HTTPS URLs. "
            "Deliverables must provide verified, full HTTPS subscription endpoints."
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

    # Check for local path reliance in evidence records
    local_path_patterns = [r"^[A-Za-z]:\\", r"^file:///", r"^\./evidence/"]
    local_only_fields = []

    if dep_summary:
        modes_file = dep_summary.get("platforms", {}).get("Cloudflare", {}).get("modes_comparison_file")
        if modes_file and not modes_file.startswith("http"):
            local_only_fields.append(f"Cloudflare.modes_comparison_file: {modes_file}")

    details["local_only_fields"] = local_only_fields

    # Check for git desynchronization (local HEAD != remote HEAD)
    if repo_ev:
        remote_head_sha = repo_ev.get("remote_head", {}).get("sha")
        details["remote_head_sha"] = remote_head_sha
        # Read local git HEAD
        git_head_file = os.path.join(REPO_ROOT, ".git", "refs", "heads", "main")
        local_head_sha = None
        if os.path.isfile(git_head_file):
            with open(git_head_file, "r", encoding="utf-8") as f:
                local_head_sha = f.read().strip()
        details["local_head_sha"] = local_head_sha

        if remote_head_sha and local_head_sha and remote_head_sha != local_head_sha:
            violations.append(
                f"Local git HEAD ({local_head_sha}) is desynchronized from remote authoritative HEAD ({remote_head_sha}). "
                "Evidence relying solely on local workspace path without pushing to remote origin violates the remote root mandate."
            )

    if not remote_repo_url or not str(remote_repo_url).startswith("https://"):
        violations.append(
            "Evidence root is only local machine path. No verified remote repository HTTPS root anchor found."
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
    # Task card: Subscription metadata must contain full 40-character head_sha and run_id.
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

    artifacts_count = None
    v13_runs_found = []
    v13_artifacts_found = []

    if wf_ev:
        # Check artifacts
        artifacts_meta = wf_ev.get("artifacts_inventory", {})
        artifacts_count = artifacts_meta.get("total_count", 0)
        details["remote_artifacts_total_count"] = artifacts_count

        # Check registered workflows
        registered = wf_ev.get("actions_workflows", [])
        wf_paths = [w.get("path") for w in registered]
        details["remote_registered_workflow_paths"] = wf_paths

        # Check workflow runs
        runs = wf_ev.get("workflow_runs", [])
        details["remote_workflow_runs_count"] = len(runs)

        # Look for V13 workflows: external-blackbox-audit, smoke-test, optimize-three-carriers
        v13_wf_names = [
            "external-blackbox-audit.yml",
            "deploy-wasmer.yml",
            "deploy-supabase.yml",
            "deploy-northflank.yml",
            "publish-subscriptions.yml",
            "smoke-test.yml"
        ]
        remote_has_v13_wf = any(any(v in p for v in v13_wf_names) for p in wf_paths)
        details["remote_has_v13_workflows"] = remote_has_v13_wf

        if not remote_has_v13_wf:
            violations.append(
                "None of the required V13 deployment or audit workflows are registered on remote main repository. "
                "Only legacy workflows (edgeone-full-sweep, edgeone-published-recheck) exist on remote."
            )

        if artifacts_count == 0:
            violations.append(
                "Remote GitHub Actions artifacts count is 0. "
                "No artifact URL or SHA-256 digest exists for blackbox audit or subscription release."
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

    ledger_path = os.path.join(REPO_ROOT, "orchestration", "ledger.md")
    legacy_speed_report = os.path.join(REPO_ROOT, "orchestration", "S3_speed_report.md")

    forbidden_phrases = [
        "真实三网直测",
        "国内端到端直测",
        "国内物理直连测速",
        "真实国内直测",
        "genuine China 3-Network measurement pipeline",
        "genuine China 3-Network measurement",
        "中国三网测速流水线"
    ]

    found_forbidden = []

    # Check orchestration ledger
    if os.path.isfile(ledger_path):
        with open(ledger_path, "r", encoding="utf-8") as f:
            l_text = f.read()
        for phrase in forbidden_phrases:
            if phrase in l_text and "CHAINED_ESTIMATE" not in l_text:
                found_forbidden.append(f"ledger.md: '{phrase}'")

    # Check S3 speed report if exists
    if os.path.isfile(legacy_speed_report):
        with open(legacy_speed_report, "r", encoding="utf-8") as f:
            s_text = f.read()
        for phrase in forbidden_phrases:
            if phrase in s_text and "CHAINED_ESTIMATE" not in s_text:
                found_forbidden.append(f"S3_speed_report.md: '{phrase}'")

    details["forbidden_methodology_phrases_detected"] = found_forbidden

    # Check route-proof and raw manifest for explicit CHAINED_ESTIMATE declaration
    route_proof_dir = os.path.join(REPO_ROOT, "results", "route-proof")
    has_chained_estimate_in_route_proof = False
    route_proof_files = []
    if os.path.isdir(route_proof_dir):
        for rf in os.listdir(route_proof_dir):
            if rf.endswith(".json"):
                rf_path = os.path.join(route_proof_dir, rf)
                route_proof_files.append(rf)
                rf_data = load_json_safe(rf_path) or {}
                if "CHAINED_ESTIMATE" in json.dumps(rf_data):
                    has_chained_estimate_in_route_proof = True

    details["route_proof_files"] = route_proof_files
    details["has_chained_estimate_in_route_proof"] = has_chained_estimate_in_route_proof

    # Check manifests under results/raw/*/manifest.json
    has_chained_estimate_in_manifest = False
    raw_dir = os.path.join(REPO_ROOT, "results", "raw")
    if os.path.isdir(raw_dir):
        for run_id in os.listdir(raw_dir):
            m_path = os.path.join(raw_dir, run_id, "manifest.json")
            if os.path.isfile(m_path):
                m_data = load_json_safe(m_path) or {}
                if "CHAINED_ESTIMATE" in json.dumps(m_data):
                    has_chained_estimate_in_manifest = True

    details["has_chained_estimate_in_manifest"] = has_chained_estimate_in_manifest

    if not has_chained_estimate_in_route_proof and not has_chained_estimate_in_manifest:
        violations.append(
            "Speedtest telemetry and route-proof evidence lack mandatory CHAINED_ESTIMATE methodology declaration. "
            "Task card requires explicit documentation that testing mode is CHAINED_ESTIMATE with route overhead."
        )

    if found_forbidden:
        violations.append(
            f"Measurement methodology improperly characterized without chained proxy qualification: {found_forbidden}. "
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

    dep_summary = load_json_safe(os.path.join(DEPLOYMENTS_DIR, "summary.json"))
    ledger_path = os.path.join(REPO_ROOT, "orchestration", "ledger.md")

    # 1. Netlify: Edge functions have WS 502 ingress limitation
    # In earlier ledger line 20, Netlify was labeled CAPABLE_DIRECT (独立真后端)
    if os.path.isfile(ledger_path):
        with open(ledger_path, "r", encoding="utf-8") as f:
            l_text = f.read()
        if "Netlify" in l_text and "CAPABLE_DIRECT" in l_text:
            violations.append(
                "Netlify previously labeled as CAPABLE_DIRECT (独立真后端). "
                "Netlify Edge Functions suffer from RFC 6455 WebSocket 101 ingress termination (HTTP 502 Bad Gateway) "
                "and cannot function as an independent direct VLESS proxy egress."
            )
        # Check if Fastly or EdgeOne claimed with >=34 nodes in ledger
        if "Fastly" in l_text and "34" in l_text:
            violations.append(
                "Fastly previously claimed with 34 nodes in orchestration ledger. "
                "Fastly is an ingress Anycast CDN fronting layer (CAPABLE_FRONT), not an independent direct egress."
            )
        if "EdgeOne" in l_text and "36" in l_text:
            violations.append(
                "EdgeOne previously claimed with 36 nodes in orchestration ledger. "
                "EdgeOne is an edge function fronting layer (CAPABLE_FRONT), not an independent direct egress."
            )

    # 2. Fastly & EdgeOne: Both are CAPABLE_FRONT (Anycast CDN / reverse proxy)
    # Check if Fastly or EdgeOne are published as independent direct proxies in clash configs
    fastly_yaml = load_yaml_safe(os.path.join(REPO_ROOT, "clash_fastly.yaml"))
    fastly_proxies = fastly_yaml.get("proxies", []) if fastly_yaml else []

    edgeone_yaml = load_yaml_safe(os.path.join(REPO_ROOT, "clash_edgeone.yaml"))
    edgeone_proxies = edgeone_yaml.get("proxies", []) if edgeone_yaml else []

    details["fastly_proxies_count"] = len(fastly_proxies)
    details["edgeone_proxies_count"] = len(edgeone_proxies)

    if len(fastly_proxies) > 0:
        violations.append(
            f"Fastly is an ingress Anycast CDN fronting platform (CAPABLE_FRONT) but published {len(fastly_proxies)} proxy nodes as independent egress."
        )

    if len(edgeone_proxies) > 0:
        violations.append(
            f"EdgeOne is an edge function fronting platform (CAPABLE_FRONT) but published {len(edgeone_proxies)} proxy nodes as independent egress."
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
