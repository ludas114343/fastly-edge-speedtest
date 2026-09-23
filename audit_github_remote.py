import os
import sys
import json
import ctypes
from ctypes import wintypes
import requests

CRED_TYPE_GENERIC = 1

class CREDENTIAL(ctypes.Structure):
    _fields_ = [
        ('Flags', wintypes.DWORD),
        ('Type', wintypes.DWORD),
        ('TargetName', wintypes.LPWSTR),
        ('Comment', wintypes.LPWSTR),
        ('LastWritten', wintypes.FILETIME),
        ('CredentialBlobSize', wintypes.DWORD),
        ('CredentialBlob', ctypes.POINTER(ctypes.c_byte)),
        ('Persist', wintypes.DWORD),
        ('AttributeCount', wintypes.DWORD),
        ('Attributes', ctypes.c_void_p),
        ('TargetAlias', wintypes.LPWSTR),
        ('UserName', wintypes.LPWSTR),
    ]

PCREDENTIAL = ctypes.POINTER(CREDENTIAL)
Advapi32 = ctypes.WinDLL('Advapi32.dll')
CredReadW = Advapi32.CredReadW
CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(PCREDENTIAL)]
CredReadW.restype = wintypes.BOOL

def get_github_token():
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    if token:
        return token
    pcred = PCREDENTIAL()
    if CredReadW('git:https://github.com', CRED_TYPE_GENERIC, 0, ctypes.byref(pcred)):
        blob = ctypes.string_at(pcred.contents.CredentialBlob, pcred.contents.CredentialBlobSize)
        token = blob.decode('utf-16le')
        Advapi32.CredFree(pcred)
        return token
    raise RuntimeError('GitHub token not found in env or Windows Credential Manager')

def main():
    token = get_github_token()
    session = requests.Session()
    session.proxies = {'http': 'http://127.0.0.1:7897', 'https': 'http://127.0.0.1:7897'}
    session.headers.update({
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'GitHubAuditor/1.0',
        'X-GitHub-Api-Version': '2022-11-28'
    })

    base_url = 'https://api.github.com/repos/ludas114343/fastly-edge-speedtest'

    print('=== 1. REPOSITORY METADATA ===', flush=True)
    repo_resp = session.get(base_url, timeout=15)
    repo = repo_resp.json()
    print('Repository URL:', repo.get('html_url'), flush=True)
    print('Owner/Repo:', repo.get('full_name'), flush=True)
    print('Default Branch:', repo.get('default_branch'), flush=True)
    print('Visibility / Private:', repo.get('visibility'), repo.get('private'), flush=True)

    print('\n=== 2. REMOTE HEAD COMMIT ===', flush=True)
    default_branch = repo.get('default_branch', 'main')
    branch_resp = session.get(f'{base_url}/branches/{default_branch}', timeout=15)
    branch = branch_resp.json()
    head_sha = branch.get('commit', {}).get('sha')
    head_commit_url = branch.get('commit', {}).get('html_url')
    print('Remote HEAD SHA:', head_sha, flush=True)
    print('Remote HEAD Commit URL:', head_commit_url, flush=True)
    commit_obj = branch.get('commit', {}).get('commit', {})
    print('Commit Message:', commit_obj.get('message', '').strip(), flush=True)
    print('Commit Date:', commit_obj.get('author', {}).get('date'), flush=True)

    print('\n=== 3. WORKFLOW FILES (.github/workflows) ===', flush=True)
    contents_resp = session.get(f'{base_url}/contents/.github/workflows?ref={default_branch}', timeout=15)
    contents = contents_resp.json()
    if isinstance(contents, list):
        print(f'Total workflow files in repo: {len(contents)}', flush=True)
        for item in contents:
            print(f'  - {item.get("name")} (SHA: {item.get("sha")}, size: {item.get("size")})', flush=True)
    else:
        print('Error fetching workflow files:', contents, flush=True)

    print('\n=== 4. ACTIONS WORKFLOWS INVENTORY ===', flush=True)
    wf_resp = session.get(f'{base_url}/actions/workflows', timeout=15)
    wf_data = wf_resp.json()
    print('Total Actions Workflows registered:', wf_data.get('total_count'), flush=True)
    for w in wf_data.get('workflows', []):
        print(f'  - ID: {w.get("id")}, Name: {w.get("name")}, State: {w.get("state")}, Path: {w.get("path")}', flush=True)

    print('\n=== 5. ACTIONS PERMISSIONS ===', flush=True)
    perm_resp = session.get(f'{base_url}/actions/permissions', timeout=15)
    print('Actions permissions:', perm_resp.json(), flush=True)

    print('\n=== 6. WORKFLOW RUNS & ARTIFACTS ===', flush=True)
    runs_resp = session.get(f'{base_url}/actions/runs?per_page=50', timeout=15)
    runs_data = runs_resp.json()
    print(f'Total runs count: {runs_data.get("total_count")}', flush=True)
    runs = runs_data.get('workflow_runs', [])
    print(f'Fetched {len(runs)} runs.', flush=True)

    artifacts_resp = session.get(f'{base_url}/actions/artifacts?per_page=50', timeout=15)
    artifacts_data = artifacts_resp.json()
    print(f'Total repository artifacts: {artifacts_data.get("total_count")}', flush=True)
    for art in artifacts_data.get('artifacts', []):
        print(f'  Artifact ID: {art.get("id")}, Name: {art.get("name")}, Size: {art.get("size_in_bytes")}, Expired: {art.get("expired")}, Workflow Run ID: {art.get("workflow_run", {}).get("id")}', flush=True)
        print(f'  Download URL: {art.get("archive_download_url")}', flush=True)

    for run in runs[:10]:
        run_id = run.get('id')
        print(f'\n--- Run ID: {run_id} | Workflow: {run.get("name")} ({run.get("event")}) ---', flush=True)
        print(f'  Status: {run.get("status")}, Conclusion: {run.get("conclusion")}, Head SHA: {run.get("head_sha")}', flush=True)
        print(f'  Run HTML URL: {run.get("html_url")}', flush=True)

if __name__ == '__main__':
    main()
