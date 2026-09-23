# GitHub Remote Infrastructure and Workflow Audit Report (V13 Architecture)

- Target Repository: `ludas114343/fastly-edge-speedtest`
- Audit Role: agent-github-auditor (Independent Investigation Worker)
- Working Directory: `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest`
- Audit Timestamp: 2026-09-23T19:17:10+08:00 (UTC: 2026-09-23T11:17:10Z)
- Mandate: `taskcards/v13/agent-github-auditor.md`
- Primary Evidence Files:
  - `evidence/github/repository.json`
  - `evidence/github/workflows.json`
- Overall Audit Status: **EMPIRICALLY COMPLETED WITH CRITICAL DISCREPANCIES IDENTIFIED**

---

## 1. Executive Summary and Findings Matrix

This audit was conducted by directly interrogating the official GitHub REST API (v2022-11-28) via an authenticated HTTPS session over proxy `http://127.0.0.1:7897`. The findings reject any conclusions derived solely from local git tracking branches or truncated 7-character commit hashes.

| # | Audit Dimension | Evaluated Target | Specification / Expectation | Live GitHub API Reality | Discrepancy Verdict | Primary Evidence Source |
|---|---|---|---|---|---|---|
| 1 | **Repository Identity** | `GET /repos/{owner}/{repo}` | `ludas114343/fastly-edge-speedtest` | `ludas114343/fastly-edge-speedtest` (ID: `1371538374`, Node: `R_kgDOUcADxg`, Private) | **MATCH** | `evidence/github/repository.json` lines 4-32 |
| 2 | **Default Branch** | Repository metadata | Default branch `main` | Default branch `main`, 1 branch total, 0 tags | **MATCH** | `evidence/github/repository.json` lines 29, 65-68 |
| 3 | **Remote HEAD 40-char SHA** | `GET /repos/{owner}/{repo}/branches/main` | Authoritative remote 40-character commit hash | `234067b0145c209b842df97b46da0451fab40294` (Date: `2026-09-23T08:54:54Z`) | **CRITICAL DRIFT FROM LOCAL** | `evidence/github/repository.json` lines 33-59; Local git ref is stale at `b82d7bbfcace2a6c06915b1f02b8070edb436720` |
| 4 | **Actions Permissions** | `GET /repos/{owner}/{repo}/actions/permissions` | Actions enabled, all actions allowed | `enabled: true`, `allowed_actions: "all"`, `sha_pinning_required: false` | **MATCH** | `evidence/github/repository.json` lines 60-64 |
| 5 | **Workflow Files Inventory** | `GET /repos/{owner}/{repo}/contents/.github/workflows` | 13 V13 deployment and pipeline workflows | Exactly 2 legacy workflows present on remote `main`: `edgeone-full-sweep.yml` and `edgeone-published-recheck.yml` | **CRITICAL DISCREPANCY** | `evidence/github/workflows.json` lines 12-45; 11 required V13 workflows missing from remote |
| 6 | **Actions Workflows Registration** | `GET /repos/{owner}/{repo}/actions/workflows` | 13 active registered workflows | Exactly 2 active registered workflows (IDs: `362053412`, `362053413`) | **CRITICAL DISCREPANCY** | `evidence/github/workflows.json` lines 46-71 |
| 7 | **Workflow Run History** | `GET /repos/{owner}/{repo}/actions/runs` | Active pipeline executions | 49 completed runs (38 success, 11 failure, 0 running); all associated with the 2 legacy workflows | **OBSERVED** | `evidence/github/workflows.json` lines 112-1490 |
| 8 | **Artifacts and SHA-256 Digests** | `GET /repos/{owner}/{repo}/actions/artifacts` | Verification of remote build artifacts | Total count: 0 artifacts; legacy workflows commit changes directly to repository rather than uploading artifacts | **OBSERVED (0 ARTIFACTS)** | `evidence/github/workflows.json` lines 1492-1496 |

---

## 2. Remote Repository and HEAD Analysis

### 2.1 Repository Attributes
- **Full Name**: `ludas114343/fastly-edge-speedtest`
- **Repository ID**: `1371538374`
- **Node ID**: `R_kgDOUcADxg`
- **Visibility**: `private`
- **HTML URL**: [Repository URL](https://github.com/ludas114343/fastly-edge-speedtest)
- **Clone URL**: `https://github.com/ludas114343/fastly-edge-speedtest.git`
- **Default Branch**: `main`
- **Open Issues Count**: `0`

### 2.2 Remote HEAD Commit Details
Direct query to `https://api.github.com/repos/ludas114343/fastly-edge-speedtest/branches/main` reveals:
- **Full 40-Character Remote HEAD SHA**: `234067b0145c209b842df97b46da0451fab40294`
- **Commit URL**: [Remote Commit URL](https://github.com/ludas114343/fastly-edge-speedtest/commit/234067b0145c209b842df97b46da0451fab40294)
- **Author**: `github-actions[bot] <github-actions[bot]@users.noreply.github.com>`
- **Author Timestamp**: `2026-09-23T08:54:54Z`
- **Commit Message**: `chore(auto): record 4-hour published nodes health check [skip ci]`
- **Tree SHA**: `998b753275374fe5bef60efe9a14aa8cf8f66685`
- **Parent Commit**: `25cfb5d973f9592b8467e93f6cc8303a17761d0c`

### 2.3 Empirical Demonstration of Local vs Remote Desynchronization
Local git status displays:
```
On branch main
Your branch is up to date with 'origin/main'.
```
However, running `git rev-parse HEAD` returns:
```
b82d7bbfcace2a6c06915b1f02b8070edb436720
```
This is a commit from `2026-09-19T21:14:41+08:00`. The local repository has not fetched changes since September 19, leaving the local tracking ref behind the remote repository by multiple automated commits authored by `github-actions[bot]`. Relying on local `git status` produces false assurances. The true remote HEAD is `234067b0145c209b842df97b46da0451fab40294`.

---

## 3. Workflow Files and Registration Audit

### 3.1 Remote `.github/workflows/` Directory Contents
Querying `GET /repos/ludas114343/fastly-edge-speedtest/contents/.github/workflows?ref=main` returned exactly 2 entries:
1. **`edgeone-full-sweep.yml`**:
   - Blob SHA: `d14ef7fa90f1a57dbae8abc3fcac664582d405d0`
   - File Size: `2,745` bytes
   - HTML URL: [edgeone-full-sweep.yml](https://github.com/ludas114343/fastly-edge-speedtest/blob/main/.github/workflows/edgeone-full-sweep.yml)
2. **`edgeone-published-recheck.yml`**:
   - Blob SHA: `f6cce4899beb6e6102f718bac829ab06af5650b7`
   - File Size: `1,003` bytes
   - HTML URL: [edgeone-published-recheck.yml](https://github.com/ludas114343/fastly-edge-speedtest/blob/main/.github/workflows/edgeone-published-recheck.yml)

### 3.2 Registered GitHub Actions Workflows
Querying `GET /repos/ludas114343/fastly-edge-speedtest/actions/workflows` returned:
- **Total Registered Workflows**: 2
- **Workflow 1**:
  - ID: `362053412`
  - Name: `Edge Multi-Platform Full Candidate Sweep`
  - Path: `.github/workflows/edgeone-full-sweep.yml`
  - State: `active`
- **Workflow 2**:
  - ID: `362053413`
  - Name: `Edge Published Nodes Recheck`
  - Path: `.github/workflows/edgeone-published-recheck.yml`
  - State: `active`

### 3.3 Identification of Discrepancies vs Task Card Mandate
The V13 task card specified the verification of 13 workflows:
1. `deploy-supabase.yml`
2. `deploy-wasmer.yml`
3. `deploy-northflank.yml`
4. `deploy-cloudflare.yml`
5. `deploy-fastly.yml`
6. `deploy-netlify.yml`
7. `deploy-edgeone.yml`
8. `discover-candidates.yml`
9. `smoke-test.yml`
10. `optimize-three-carriers.yml`
11. `publish-subscriptions.yml`
12. `external-blackbox-audit.yml`
13. `watchdog.yml`

**Findings**:
- None of these 13 workflows exist on remote `main`.
- None of these 13 workflows exist in the local `.github/workflows/` directory.
- The local `.github/workflows/` directory contains 12 files following an alternate naming convention (`sub-sync-*.yml`, `pipeline-china-speedtest.yml`, `watchdog-subscription-audit.yml`), all of which remain untracked in git.
- **Root Cause**: The designated deployment agent (`agent-github-deployer`) has not yet generated or synchronized the 13 required workflow files, nor executed a `git push` to origin.

---

## 4. Workflow Run History and Artifact Verification

### 4.1 Execution Metrics
- **Total Historical Runs**: 49
- **Completed Runs**: 49
- **In-Progress / Queued**: 0
- **Successful Runs**: 38
- **Failed Runs**: 11
- **Recent Execution Sampling**:
  - Run ID: `35839802459`, Workflow: `Edge Published Nodes Recheck`, Status: `completed`, Conclusion: `success`, Head SHA: `25cfb5d973f9592b8467e93f6cc8303a17761d0c`, HTML: [Run 35839802459](https://github.com/ludas114343/fastly-edge-speedtest/actions/runs/35839802459)
  - Run ID: `35828592288`, Workflow: `Edge Multi-Platform Full Candidate Sweep`, Status: `completed`, Conclusion: `failure`, Head SHA: `25cfb5d973f9592b8467e93f6cc8303a17761d0c`, HTML: [Run 35828592288](https://github.com/ludas114343/fastly-edge-speedtest/actions/runs/35828592288)
  - Run ID: `35809768065`, Workflow: `Edge Published Nodes Recheck`, Status: `completed`, Conclusion: `success`, Head SHA: `0204526a12cbfc94514f9ec06036043248985d26`, HTML: [Run 35809768065](https://github.com/ludas114343/fastly-edge-speedtest/actions/runs/35809768065)

### 4.2 Job Telemetry
Job inspection on top runs confirms that jobs execute on `ubuntu-latest` GitHub-hosted runners using standard checkout and Python setup actions. For example:
- Run `35839802459` Job ID: `102925585093`, Name: `published-nodes-recheck`, Conclusion: `success`, Runner: `GitHub Actions 33`.

### 4.3 Artifact Telemetry and Digests
Querying `GET /repos/ludas114343/fastly-edge-speedtest/actions/artifacts` returned:
- **Total Artifact Count**: 0
- **Artifact Records**: `[]`
- **Explanation**: The existing workflow definitions do not include `actions/upload-artifact` steps. Instead, candidate evaluations and subscription updates are committed directly back into the git tree via `git commit` by the runner bot. As a consequence, no downloadable archive artifacts or corresponding SHA-256 digests exist on GitHub Actions storage.

---

## 5. Remaining Questions and Gaps

1. **Unsynchronized V13 Workflows**:
   - The coordinator assumed 13 active workflows were committed and active on remote `main`.
   - The physical evidence demonstrates that `agent-github-deployer` has not pushed the required workflows. The parent orchestrator must sequence `agent-github-deployer` prior to final GitHub remote audit acceptance.
2. **Local vs Remote Working Tree Reconciliation**:
   - The local working tree has untracked files (`sub-sync-*.yml`) differing in naming and structure from the V13 specification (`deploy-*.yml`). A reconciliation step is required to align local files with the target naming scheme before pushing.
3. **Stale Local Tracking Branch**:
   - The local repository tracking ref `origin/main` is stale at `b82d7bbfcace2a6c06915b1f02b8070edb436720`, whereas remote HEAD is `234067b0145c209b842df97b46da0451fab40294`. Prior to pushing new commits, a git pull or fetch/rebase must occur to prevent push rejections.

---

## 6. Audit Verdict

The remote audit is successfully completed and grounded entirely in live GitHub REST API data. All collected evidence is structured and committed to disk:
- `evidence/github/repository.json` (verified authentic API payload)
- `evidence/github/workflows.json` (verified authentic workflow inventory and run history)

The assertion that 13 active workflows exist on remote `main` is **REFUTED** by physical API evidence. Remediation by `agent-github-deployer` is required.
