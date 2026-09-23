import os
import json
import hashlib
import re

WORKSPACE = r'C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest'
MANIFEST = os.path.join(WORKSPACE, 'forensics', 'legacy_manifest.json')
INVENTORY = os.path.join(WORKSPACE, 'evidence', 'inventory')

# 1. Verify manifest
assert os.path.isfile(MANIFEST), 'Missing legacy_manifest.json'
with open(MANIFEST, 'r', encoding='utf-8') as f:
    m = json.load(f)

assert m['total_files'] == len(m['files'])
assert m['total_files'] > 0
print(f"Legacy files count: {m['total_files']}")

for rec in m['files']:
    orig = os.path.join(WORKSPACE, rec['original_path'])
    arch = os.path.join(WORKSPACE, rec['archived_path'])
    assert os.path.isfile(arch), f"Archived file missing: {arch}"
    with open(arch, 'rb') as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    assert sha == rec['sha256'], f"SHA mismatch for {arch}"
    # Skip orig comparison for files under results/ (speedtest re-runs generate new files in results/)
    norm_orig = rec['original_path'].replace('\\', '/')
    if not norm_orig.startswith('results/'):
        if os.path.isfile(orig):
            with open(orig, 'rb') as f:
                cur_sha = hashlib.sha256(f.read()).hexdigest()
            assert cur_sha != rec['sha256'], f"Unmodified legacy file still present in original location: {orig}"

print("Legacy freeze and manifest verification: PASS")

# 2. Check no legacy-exclusive files in root or legacy results in results dir
root_files = os.listdir(WORKSPACE)
assert not any(f.endswith('_candidates.json') for f in root_files), 'legacy candidates JSON still in root'
assert not any(f.endswith('_best_nodes.json') for f in root_files), 'legacy best_nodes JSON still in root'
assert 'clash_edgetunnel.yaml' not in root_files, 'legacy clash_edgetunnel.yaml still in root'
assert 'geo_audit_report.json' not in root_files, 'geo_audit_report.json still in root'
assert 'usage_metrics.json' not in root_files, 'usage_metrics.json still in root'

legacy_results_items = [
    '2026-09-21.jsonl.gz',
    '2026-09-22.jsonl.gz',
    'china-telecom',
    'china-unicom',
    'china-mobile',
    'stage_b_independent_verification.json',
    'stage_c_geogate_audit.json'
]
results_dir = os.path.join(WORKSPACE, 'results')
if os.path.exists(results_dir):
    current_results_items = os.listdir(results_dir)
    for item in legacy_results_items:
        if item in current_results_items:
            item_path = os.path.join(results_dir, item)
            arch_path = os.path.join(WORKSPACE, 'forensics', 'legacy', 'results', item)
            if os.path.isfile(item_path) and os.path.isfile(arch_path):
                with open(item_path, 'rb') as f1, open(arch_path, 'rb') as f2:
                    assert hashlib.sha256(f1.read()).hexdigest() != hashlib.sha256(f2.read()).hexdigest(), (
                        f"Legacy results item '{item}' still present in results/ with identical legacy hash"
                    )

print("Root hygiene verification: PASS")

# 3. Check 6 inventory JSONs
req_keys = [
    'platform', 'account_verified', 'projects', 'services', 'deployments',
    'regions', 'domains', 'active_versions', 'checked_at', 'api_response_hash', 'DEPLOYMENT_COUNT'
]
platforms = ['supabase', 'wasmer', 'northflank', 'fastly', 'netlify', 'edgeone']

# Dynamically extract actual secret substrings from credentials file to verify they are NOT leaked in output
CREDS_FILE = r'D:\Obsidian\CollegeAid\planning\平台凭据速查.md'
raw_secrets = []
if os.path.isfile(CREDS_FILE):
    with open(CREDS_FILE, 'r', encoding='utf-8') as f:
        creds_text = f.read()
    secret_patterns = [
        r"Supabase.*?`(sbp_[A-Za-z0-9_-]+)`",
        r"Wasmer.*?`(wap_[A-Za-z0-9_-]+)`",
        r"Netlify.*?`(nfp_[A-Za-z0-9_-]+)`",
        r"Fastly \(操作/工程\).*?`([A-Za-z0-9_-]{20,})`",
        r"Fastly \(财务/账单\).*?`([A-Za-z0-9_-]{20,})`",
        r"SecretKey:\s*`([A-Za-z0-9_-]{20,})`",
        r"Northflank.*?`(nf-[A-Za-z0-9_.-]{30,})`",
    ]
    for pat in secret_patterns:
        m_sec = re.search(pat, creds_text)
        if m_sec:
            raw_secrets.append(m_sec.group(1).strip())
    assert len(raw_secrets) >= 6, f"Expected at least 6 platform secrets dynamically extracted, got {len(raw_secrets)}"

unmasked_regex = re.compile(r'(sbp_|wap_|nfp_)[A-Za-z0-9_-]{20,}')

for p in platforms:
    p_path = os.path.join(INVENTORY, f'{p}.json')
    assert os.path.isfile(p_path), f"Missing {p}.json"
    with open(p_path, 'r', encoding='utf-8') as f:
        content = f.read()
    assert '\u2014' not in content, f"Em-dash in {p}.json"
    assert '\u2013' not in content, f"En-dash in {p}.json"
    assert not unmasked_regex.search(content), f"Unmasked token pattern detected in {p}.json"
    for s in raw_secrets:
        assert s not in content, f"Leaked secret in {p}.json: {s[:6]}...[masked]"
    data = json.loads(content)
    for k in req_keys:
        assert k in data, f"Missing {k} in {p}.json"
    assert data['platform'] == p
    assert data['account_verified'] is True
    assert isinstance(data['DEPLOYMENT_COUNT'], int)
    assert len(data['api_response_hash']) == 64
    print(f"{p}.json PASS: DEPLOYMENT_COUNT={data['DEPLOYMENT_COUNT']}, verified={data['account_verified']}")

print("\nALL AUDIT CRITERIA PASSED 100%")
