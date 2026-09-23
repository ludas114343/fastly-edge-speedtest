import os
import json
import hashlib
import re

WORKSPACE = r'C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest'
MANIFEST = os.path.join(WORKSPACE, 'forensics', 'legacy_manifest.json')
INVENTORY = os.path.join(WORKSPACE, 'evidence', 'inventory')
RECONCILIATION = os.path.join(WORKSPACE, 'evidence', 'reconciliation')

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

# 3. Check 7 inventory JSONs
req_keys = [
    'platform', 'account_verified', 'projects', 'services', 'deployments',
    'regions', 'domains', 'active_versions', 'checked_at', 'api_response_hash', 'DEPLOYMENT_COUNT',
    'project_count', 'service_count', 'deployment_count', 'region_route_count',
    'entry_count', 'candidate_count', 'verified_proxy_count', 'status', 'unfinished'
]
platforms = ['supabase', 'wasmer', 'northflank', 'fastly', 'netlify', 'edgeone', 'cloudflare']

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
        r"Cloudflare.*?`(cfut_[A-Za-z0-9]+)`",
    ]
    for pat in secret_patterns:
        m_sec = re.search(pat, creds_text)
        if m_sec:
            raw_secrets.append(m_sec.group(1).strip())
    assert len(raw_secrets) >= 7, f"Expected at least 7 platform secrets dynamically extracted, got {len(raw_secrets)}"

unmasked_regex = re.compile(r'(sbp_|wap_|nfp_|cfut_)[A-Za-z0-9_-]{20,}')

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
    print(f"{p}.json PASS: DEPLOYMENT_COUNT={data['DEPLOYMENT_COUNT']}, verified={data['account_verified']}, status={data['status']}")

# 4. Rigorous platform-specific assertion gates
# Supabase: 2 projects / deployments vs 10 regional routes
sb_data = json.load(open(os.path.join(INVENTORY, 'supabase.json'), 'r', encoding='utf-8'))
assert sb_data['DEPLOYMENT_COUNT'] == 2, f"Supabase DEPLOYMENT_COUNT must be 2, got {sb_data['DEPLOYMENT_COUNT']}"
assert sb_data['project_count'] == 2, f"Supabase project_count must be 2, got {sb_data['project_count']}"
assert sb_data['region_route_count'] == 10, f"Supabase region_route_count must be 10, got {sb_data['region_route_count']}"
assert sb_data['entry_count'] == 34, f"Supabase entry_count must be 34, got {sb_data['entry_count']}"

# Wasmer: Exactly 4 authentic deployments, verified deployment count <= 4
w_data = json.load(open(os.path.join(INVENTORY, 'wasmer.json'), 'r', encoding='utf-8'))
assert w_data['DEPLOYMENT_COUNT'] == 4, f"Wasmer DEPLOYMENT_COUNT must be 4, got {w_data['DEPLOYMENT_COUNT']}"
assert w_data['DEPLOYMENT_COUNT'] <= 4, "Wasmer DEPLOYMENT_COUNT must be <= 4"
assert w_data['project_count'] == 4, f"Wasmer project_count must be 4, got {w_data['project_count']}"
assert w_data['verified_proxy_count'] == 4, f"Wasmer verified_proxy_count must be 4, got {w_data['verified_proxy_count']}"

# Northflank: Exactly 1 GCP deployment ID = 1 verified proxy node
nf_data = json.load(open(os.path.join(INVENTORY, 'northflank.json'), 'r', encoding='utf-8'))
assert nf_data['DEPLOYMENT_COUNT'] == 1, f"Northflank DEPLOYMENT_COUNT must be 1, got {nf_data['DEPLOYMENT_COUNT']}"
assert nf_data['project_count'] == 1, f"Northflank project_count must be 1, got {nf_data['project_count']}"
assert nf_data['verified_proxy_count'] == 1, f"Northflank verified_proxy_count must be 1, got {nf_data['verified_proxy_count']}"

# Fastly, Netlify, EdgeOne, Cloudflare: verified_proxy_count == 0, unfinished == True
for p in ['fastly', 'netlify', 'edgeone', 'cloudflare']:
    p_data = json.load(open(os.path.join(INVENTORY, f'{p}.json'), 'r', encoding='utf-8'))
    assert p_data['verified_proxy_count'] == 0, f"{p} verified_proxy_count must be 0, got {p_data['verified_proxy_count']}"
    assert p_data['entry_count'] == 0, f"{p} entry_count must be 0, got {p_data['entry_count']}"
    assert p_data['unfinished'] is True, f"{p} unfinished must be True, got {p_data['unfinished']}"
    assert p_data['status'] == 'NO_VERIFIED_PROXY', f"{p} status must be NO_VERIFIED_PROXY, got {p_data['status']}"

# 5. Check Wasmer Reconciliation File
wasmer_rec_file = os.path.join(RECONCILIATION, 'wasmer_nodes.json')
assert os.path.isfile(wasmer_rec_file), 'Missing evidence/reconciliation/wasmer_nodes.json'
with open(wasmer_rec_file, 'r', encoding='utf-8') as f:
    wrec_content = f.read()
assert '\u2014' not in wrec_content, 'Em-dash in wasmer_nodes.json'
assert '\u2013' not in wrec_content, 'En-dash in wasmer_nodes.json'
wrec_data = json.loads(wrec_content)
assert wrec_data['verdict'] == 'RECONCILED_PASS'
assert wrec_data['authentic_deployment_count'] == 4
assert wrec_data['verified_physical_nodes_count'] == 4
assert wrec_data['deducted_alias_nodes_count'] == 1
assert len(wrec_data['authentic_deployments']) == 4
assert len(wrec_data['deducted_nodes']) == 1
print("wasmer_nodes.json PASS: verdict=RECONCILED_PASS, authentic=4, physical=4, deducted=1")

# 6. Check Summary JSON
summary_file = os.path.join(INVENTORY, 'summary.json')
assert os.path.isfile(summary_file), 'Missing evidence/inventory/summary.json'
with open(summary_file, 'r', encoding='utf-8') as f:
    sum_content = f.read()
assert '\u2014' not in sum_content, 'Em-dash in summary.json'
assert '\u2013' not in sum_content, 'En-dash in summary.json'
sum_data = json.loads(sum_content)
assert sum_data['total_platforms'] == 7
assert sum_data['total_projects'] == 11
assert sum_data['total_deployments'] == 11
assert sum_data['total_region_routes'] == 19
assert sum_data['total_published_entries'] == 39
assert sum_data['total_verified_physical_backends'] == 7
print(f"summary.json PASS: total_platforms=7, deployments=11, entries=39, physical_backends=7")

# 7. Check Inventory Markdown Report
report_file = os.path.join(INVENTORY, 'inventory_report.md')
assert os.path.isfile(report_file), 'Missing evidence/inventory/inventory_report.md'
with open(report_file, 'r', encoding='utf-8') as f:
    rep_content = f.read()
assert '\u2014' not in rep_content, 'Em-dash in inventory_report.md'
assert '\u2013' not in rep_content, 'En-dash in inventory_report.md'
print("inventory_report.md PASS: formatting and zero em-dash verified")

print("\nALL V13 INVENTORY AUDIT CRITERIA PASSED 100%")
