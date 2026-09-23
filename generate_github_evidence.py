import os
import sys
import json
import datetime
import hashlib
import requests
import audit_github_remote

def fetch_all():
    token = audit_github_remote.get_github_token()
    session = requests.Session()
    session.proxies = {'http': 'http://127.0.0.1:7897', 'https': 'http://127.0.0.1:7897'}
    session.headers.update({
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'GitHubAuditor/1.0',
        'X-GitHub-Api-Version': '2022-11-28'
    })

    base_url = 'https://api.github.com/repos/ludas114343/fastly-edge-speedtest'
    audit_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

    print('1. Fetching repository details...', flush=True)
    repo = session.get(base_url, timeout=20).json()

    print('2. Fetching branch / remote HEAD...', flush=True)
    default_branch = repo.get('default_branch', 'main')
    branch = session.get(f'{base_url}/branches/{default_branch}', timeout=20).json()
    head_commit = branch.get('commit', {})

    print('3. Fetching Actions permissions...', flush=True)
    perms = session.get(f'{base_url}/actions/permissions', timeout=20).json()

    print('4. Fetching branches and tags...', flush=True)
    branches = session.get(f'{base_url}/branches', timeout=20).json()
    tags = session.get(f'{base_url}/tags', timeout=20).json()

    print('5. Fetching .github/workflows directory contents...', flush=True)
    contents = session.get(f'{base_url}/contents/.github/workflows?ref={default_branch}', timeout=20).json()

    print('6. Fetching registered Actions workflows...', flush=True)
    workflows = session.get(f'{base_url}/actions/workflows', timeout=20).json()

    print('7. Fetching workflow runs (all pages)...', flush=True)
    all_runs = []
    page = 1
    while True:
        r = session.get(f'{base_url}/actions/runs?per_page=100&page={page}', timeout=20).json()
        runs_page = r.get('workflow_runs', [])
        if not runs_page:
            break
        all_runs.extend(runs_page)
        if len(all_runs) >= r.get('total_count', 0):
            break
        page += 1
    print(f'   Total workflow runs fetched: {len(all_runs)}', flush=True)

    print('8. Fetching artifacts...', flush=True)
    art_resp = session.get(f'{base_url}/actions/artifacts?per_page=100', timeout=20).json()
    artifacts = art_resp.get('artifacts', [])
    print(f'   Total artifacts fetched: {len(artifacts)}', flush=True)

    # Fetch jobs for recent runs (e.g. top 15 runs to keep it fast and thorough)
    print('9. Fetching jobs for runs...', flush=True)
    runs_with_jobs = []
    for idx, run in enumerate(all_runs):
        run_entry = {
            'id': run.get('id'),
            'name': run.get('name'),
            'node_id': run.get('node_id'),
            'head_branch': run.get('head_branch'),
            'head_sha': run.get('head_sha'),
            'path': run.get('path'),
            'display_title': run.get('display_title'),
            'run_number': run.get('run_number'),
            'event': run.get('event'),
            'status': run.get('status'),
            'conclusion': run.get('conclusion'),
            'workflow_id': run.get('workflow_id'),
            'url': run.get('url'),
            'html_url': run.get('html_url'),
            'created_at': run.get('created_at'),
            'updated_at': run.get('updated_at'),
            'run_started_at': run.get('run_started_at'),
            'jobs_url': run.get('jobs_url'),
            'logs_url': run.get('logs_url'),
            'artifacts_url': run.get('artifacts_url'),
            'jobs': []
        }
        # For the top 15 runs, fetch exact job records
        if idx < 15:
            try:
                j_resp = session.get(run.get('jobs_url'), timeout=15).json()
                for j in j_resp.get('jobs', []):
                    run_entry['jobs'].append({
                        'id': j.get('id'),
                        'run_id': j.get('run_id'),
                        'name': j.get('name'),
                        'status': j.get('status'),
                        'conclusion': j.get('conclusion'),
                        'started_at': j.get('started_at'),
                        'completed_at': j.get('completed_at'),
                        'html_url': j.get('html_url'),
                        'runner_id': j.get('runner_id'),
                        'runner_name': j.get('runner_name'),
                        'steps_count': len(j.get('steps', []))
                    })
            except Exception as e:
                print(f'   Warning: failed to fetch jobs for run {run.get("id")}: {e}', flush=True)
        runs_with_jobs.append(run_entry)

    # Scan local workflow files
    local_wf_dir = os.path.join(os.getcwd(), '.github', 'workflows')
    local_workflows = []
    if os.path.exists(local_wf_dir):
        for fname in sorted(os.listdir(local_wf_dir)):
            fpath = os.path.join(local_wf_dir, fname)
            if os.path.isfile(fpath):
                with open(fpath, 'rb') as f:
                    content = f.read()
                local_workflows.append({
                    'name': fname,
                    'path': f'.github/workflows/{fname}',
                    'size_bytes': len(content),
                    'sha256': hashlib.sha256(content).hexdigest()
                })

    # Prepare repository.json
    repo_data = {
        'audit_timestamp': audit_time,
        'auditor': 'agent-github-auditor',
        'repository': {
            'id': repo.get('id'),
            'node_id': repo.get('node_id'),
            'name': repo.get('name'),
            'full_name': repo.get('full_name'),
            'owner': {
                'login': repo.get('owner', {}).get('login'),
                'id': repo.get('owner', {}).get('id'),
                'node_id': repo.get('owner', {}).get('node_id'),
                'type': repo.get('owner', {}).get('type'),
                'site_admin': repo.get('owner', {}).get('site_admin'),
                'html_url': repo.get('owner', {}).get('html_url')
            },
            'private': repo.get('private'),
            'html_url': repo.get('html_url'),
            'description': repo.get('description'),
            'fork': repo.get('fork'),
            'url': repo.get('url'),
            'created_at': repo.get('created_at'),
            'updated_at': repo.get('updated_at'),
            'pushed_at': repo.get('pushed_at'),
            'git_url': repo.get('git_url'),
            'ssh_url': repo.get('ssh_url'),
            'clone_url': repo.get('clone_url'),
            'size': repo.get('size'),
            'default_branch': default_branch,
            'open_issues_count': repo.get('open_issues_count'),
            'visibility': repo.get('visibility')
        },
        'remote_head': {
            'branch': default_branch,
            'sha': head_commit.get('sha'),
            'commit_url': head_commit.get('html_url'),
            'author': head_commit.get('commit', {}).get('author'),
            'committer': head_commit.get('commit', {}).get('committer'),
            'message': head_commit.get('commit', {}).get('message'),
            'tree': head_commit.get('commit', {}).get('tree'),
            'parents': head_commit.get('parents', [])
        },
        'actions_permissions': perms,
        'branches': [b.get('name') for b in branches] if isinstance(branches, list) else [],
        'tags': [t.get('name') for t in tags] if isinstance(tags, list) else []
    }

    # Prepare workflows.json
    workflows_data = {
        'audit_timestamp': audit_time,
        'auditor': 'agent-github-auditor',
        'summary': {
            'expected_workflows_count': 13,
            'actual_remote_workflow_files_count': len(contents) if isinstance(contents, list) else 0,
            'actual_registered_actions_workflows_count': workflows.get('total_count', 0),
            'actual_local_workflow_files_count': len(local_workflows),
            'discrepancy_detected': not (len(contents) == 13 and len(local_workflows) == 13 and workflows.get('total_count', 0) == 13),
            'discrepancy_reason': None if (len(contents) == 13 and len(local_workflows) == 13 and workflows.get('total_count', 0) == 13) else 'Workflow count mismatch between expected and actual.'
        },
        'remote_workflow_files': contents if isinstance(contents, list) else [],
        'actions_workflows': workflows.get('workflows', []),
        'local_workflow_files': local_workflows,
        'workflow_runs_summary': {
            'total_runs_count': len(all_runs),
            'completed_runs': sum(1 for r in all_runs if r.get('status') == 'completed'),
            'in_progress_runs': sum(1 for r in all_runs if r.get('status') == 'in_progress'),
            'queued_runs': sum(1 for r in all_runs if r.get('status') == 'queued'),
            'success_runs': sum(1 for r in all_runs if r.get('conclusion') == 'success'),
            'failure_runs': sum(1 for r in all_runs if r.get('conclusion') == 'failure'),
            'cancelled_runs': sum(1 for r in all_runs if r.get('conclusion') == 'cancelled')
        },
        'workflow_runs': runs_with_jobs,
        'artifacts_inventory': {
            'total_count': len(artifacts),
            'artifacts': artifacts
        }
    }

    # Ensure evidence/github directory exists
    os.makedirs(os.path.join(os.getcwd(), 'evidence', 'github'), exist_ok=True)

    repo_file = os.path.join(os.getcwd(), 'evidence', 'github', 'repository.json')
    with open(repo_file, 'w', encoding='utf-8') as f:
        json.dump(repo_data, f, indent=2, ensure_ascii=False)
    print(f'Wrote {repo_file} ({os.path.getsize(repo_file)} bytes)', flush=True)

    wf_file = os.path.join(os.getcwd(), 'evidence', 'github', 'workflows.json')
    with open(wf_file, 'w', encoding='utf-8') as f:
        json.dump(workflows_data, f, indent=2, ensure_ascii=False)
    print(f'Wrote {wf_file} ({os.path.getsize(wf_file)} bytes)', flush=True)

if __name__ == '__main__':
    fetch_all()
