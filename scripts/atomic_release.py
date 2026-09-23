#!/usr/bin/env python3
"""
scripts/atomic_release.py - Atomic Subscription Release and Staging Promotion Engine.

Mandate: taskcards/v13/agent-auto-update-builder.md
Provides:
1. Staging directory preparation and strict validation gates.
2. Character hygiene check (zero em-dash and zero en-dash).
3. Promotion to release/<run_id>/ with manifest.json generation.
4. Atomic update of production/current.json with last-known-good fallback.
5. Fault isolation and rollback drill support with zero production disruption.

Zero em-dash (\\u2014) and zero en-dash (\\u2013) policy strictly enforced.
"""

import os
import sys
import json
import shutil
import hashlib
import argparse
import datetime
import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGING_BASE = os.path.join(REPO_ROOT, "staging")
RELEASE_BASE = os.path.join(REPO_ROOT, "release")
PRODUCTION_DIR = os.path.join(REPO_ROOT, "production")
PRODUCTION_CURRENT = os.path.join(PRODUCTION_DIR, "current.json")
EVIDENCE_AUTO_UPDATE_DIR = os.path.join(REPO_ROOT, "evidence", "auto_update")

SUBSCRIPTION_FILES = [
    "clash.yaml",
    "clash_all.yaml",
    "clash_supabase.yaml",
    "clash_wasmer.yaml",
    "clash_northflank.yaml",
    "clash_cloudflare.yaml",
    "clash_fastly.yaml",
    "clash_netlify.yaml",
    "clash_edgeone.yaml"
]

def calculate_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def calculate_bytes_sha256(data_bytes):
    return hashlib.sha256(data_bytes).hexdigest()

def check_hygiene(text, label=""):
    if "\u2014" in text:
        raise ValueError(f"Character hygiene violation: em-dash (\\u2014) in {label}")
    if "\u2013" in text:
        raise ValueError(f"Character hygiene violation: en-dash (\\u2013) in {label}")

def prepare_staging(run_id, fault_injection=None):
    staging_dir = os.path.join(STAGING_BASE, str(run_id))
    if os.path.exists(staging_dir):
        shutil.rmtree(staging_dir)
    os.makedirs(staging_dir, exist_ok=True)

    copied = {}
    for f in SUBSCRIPTION_FILES:
        src = os.path.join(REPO_ROOT, f)
        dst = os.path.join(staging_dir, f)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            copied[f] = dst
        else:
            raise FileNotFoundError(f"Missing core subscription file: {src}")

    # Copy evidence/subscriptions
    sub_ev_src = os.path.join(REPO_ROOT, "evidence", "subscriptions")
    sub_ev_dst = os.path.join(staging_dir, "evidence_subscriptions")
    if os.path.exists(sub_ev_src):
        shutil.copytree(sub_ev_src, sub_ev_dst)

    # Apply fault injection if requested
    if fault_injection == "corrupt_yaml":
        target = os.path.join(staging_dir, "clash.yaml")
        with open(target, "a", encoding="utf-8") as f:
            f.write("\n\n!!INVALID_SYNTAX_ERROR: [unterminated_array\n")
    elif fault_injection == "forbidden_char":
        target = os.path.join(staging_dir, "clash.yaml")
        with open(target, "a", encoding="utf-8") as f:
            f.write("\n# Injected forbidden character: \u2014\n")
    elif fault_injection == "empty_proxies":
        target = os.path.join(staging_dir, "clash.yaml")
        with open(target, "w", encoding="utf-8") as f:
            f.write("port: 7890\nmode: rule\nproxies: []\n")

    return staging_dir

def validate_staging(staging_dir):
    errors = []
    
    for f in SUBSCRIPTION_FILES:
        path = os.path.join(staging_dir, f)
        if not os.path.exists(path):
            errors.append(f"Missing staged file: {f}")
            continue

        try:
            with open(path, "r", encoding="utf-8") as fh:
                content = fh.read()
        except Exception as e:
            errors.append(f"Failed reading {f}: {e}")
            continue

        # 1. Character hygiene check
        try:
            check_hygiene(content, f)
        except ValueError as e:
            errors.append(str(e))

        # 2. YAML syntax parse
        try:
            parsed = yaml.safe_load(content)
            if parsed is None:
                errors.append(f"YAML parsed as empty in {f}")
            else:
                for req in ["port", "mode", "proxies"]:
                    if req not in parsed:
                        errors.append(f"Missing root key '{req}' in {f}")
                proxies = parsed.get("proxies", [])
                if f in ["clash.yaml", "clash_all.yaml"] and len(proxies) == 0:
                    errors.append(f"Master subscription {f} has 0 proxies in staging")
        except Exception as e:
            errors.append(f"YAML parse exception in {f}: {e}")

    return errors

def promote_release(staging_dir, run_id, run_url, head_sha, timestamp=None):
    if timestamp is None:
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    release_dir = os.path.join(RELEASE_BASE, str(run_id))
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    os.makedirs(release_dir, exist_ok=True)

    file_digests = {}
    for f in SUBSCRIPTION_FILES:
        src = os.path.join(staging_dir, f)
        dst = os.path.join(release_dir, f)
        shutil.copy2(src, dst)
        file_digests[f] = calculate_sha256(dst)

    # Copy evidence subscriptions
    staged_ev = os.path.join(staging_dir, "evidence_subscriptions")
    dst_ev = os.path.join(release_dir, "evidence_subscriptions")
    if os.path.exists(staged_ev):
        shutil.copytree(staged_ev, dst_ev)

    # Manifest payload
    manifest_data = {
        "run_id": str(run_id),
        "run_url": str(run_url),
        "head_sha": str(head_sha),
        "timestamp": timestamp,
        "status": "PROMOTED",
        "subscription_files": file_digests
    }

    manifest_json_str = json.dumps(manifest_data, indent=2, sort_keys=True)
    check_hygiene(manifest_json_str, "manifest.json")
    manifest_digest = calculate_bytes_sha256(manifest_json_str.encode("utf-8"))
    manifest_data["manifest_digest"] = manifest_digest

    manifest_path = os.path.join(release_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, sort_keys=True)

    # Load existing production state for last-known-good tracking
    os.makedirs(PRODUCTION_DIR, exist_ok=True)
    current_state = {}
    if os.path.exists(PRODUCTION_CURRENT):
        try:
            with open(PRODUCTION_CURRENT, "r", encoding="utf-8") as f:
                current_state = json.load(f)
        except Exception:
            current_state = {}

    previous_good = current_state.get("last_known_good")
    if not previous_good and current_state.get("run_id"):
        previous_good = {
            "run_id": current_state.get("run_id"),
            "manifest_digest": current_state.get("manifest_digest"),
            "promoted_at": current_state.get("timestamp")
        }

    # Count master proxies
    master_yaml_path = os.path.join(release_dir, "clash.yaml")
    master_proxies_count = 0
    try:
        with open(master_yaml_path, "r", encoding="utf-8") as f:
            y = yaml.safe_load(f)
            master_proxies_count = len(y.get("proxies", []))
    except Exception:
        pass

    new_production_state = {
        "active_release": f"release/{run_id}",
        "run_id": str(run_id),
        "run_url": str(run_url),
        "head_sha": str(head_sha),
        "timestamp": timestamp,
        "manifest_path": f"release/{run_id}/manifest.json",
        "manifest_digest": manifest_digest,
        "status": "HEALTHY",
        "node_count": master_proxies_count,
        "last_known_good": {
            "run_id": str(run_id),
            "manifest_digest": manifest_digest,
            "promoted_at": timestamp
        },
        "previous_good": previous_good
    }

    prod_str = json.dumps(new_production_state, indent=2, sort_keys=True)
    check_hygiene(prod_str, "production/current.json")

    # Atomic write to production/current.json using temp file
    temp_target = os.path.join(PRODUCTION_DIR, f"current.json.tmp.{run_id}")
    with open(temp_target, "w", encoding="utf-8") as f:
        f.write(prod_str)
    os.replace(temp_target, PRODUCTION_CURRENT)

    print(f"[SUCCESS] Promoted run {run_id} to production. Manifest digest: {manifest_digest}")
    return new_production_state

def run_release_pipeline(run_id, run_url, head_sha, timestamp=None, fault_injection=None):
    os.makedirs(EVIDENCE_AUTO_UPDATE_DIR, exist_ok=True)
    staging_dir = prepare_staging(run_id, fault_injection=fault_injection)
    validation_errors = validate_staging(staging_dir)

    if validation_errors:
        print(f"[ERROR] Staging validation failed for run {run_id} with {len(validation_errors)} error(s):")
        for err in validation_errors:
            print(f"  - {err}")

        # Capture rollback / fault isolation record
        curr_prod = {}
        if os.path.exists(PRODUCTION_CURRENT):
            with open(PRODUCTION_CURRENT, "r", encoding="utf-8") as f:
                curr_prod = json.load(f)

        rollback_record = {
            "drill_type": "staging_fault_isolation",
            "fault_injected": fault_injection or "unintentional_validation_failure",
            "attempted_run_id": str(run_id),
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "validation_errors": validation_errors,
            "promotion_aborted": True,
            "production_current_intact": True,
            "last_known_good_preserved": curr_prod.get("last_known_good", {}),
            "active_production_run_id": curr_prod.get("run_id"),
            "verdict": "PASS"
        }

        rollback_log_path = os.path.join(EVIDENCE_AUTO_UPDATE_DIR, "rollback_drill_evidence.json")
        with open(rollback_log_path, "w", encoding="utf-8") as f:
            json.dump(rollback_record, f, indent=2, sort_keys=True)
        print(f"[INFO] Rollback drill evidence recorded at {rollback_log_path}")

        return False, validation_errors

    # Validation passed: proceed with promotion
    prod_state = promote_release(staging_dir, run_id, run_url, head_sha, timestamp=timestamp)
    return True, prod_state

def main():
    parser = argparse.ArgumentParser(description="Atomic Subscription Release and Promotion Engine")
    parser.add_argument("--run-id", required=True, help="GitHub Actions run ID or local execution ID")
    parser.add_argument("--run-url", required=True, help="GitHub Actions run URL")
    parser.add_argument("--head-sha", required=True, help="Commit HEAD SHA")
    parser.add_argument("--timestamp", default=None, help="Release ISO timestamp")
    parser.add_argument("--inject-staging-fault", choices=["corrupt_yaml", "forbidden_char", "empty_proxies"], default=None, help="Inject staging fault for rollback drill")

    args = parser.parse_args()

    success, result = run_release_pipeline(
        run_id=args.run_id,
        run_url=args.run_url,
        head_sha=args.head_sha,
        timestamp=args.timestamp,
        fault_injection=args.inject_staging_fault
    )

    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
