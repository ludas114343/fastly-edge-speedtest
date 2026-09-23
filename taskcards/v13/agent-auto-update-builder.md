# Task Card: agent-auto-update-builder (V13)

- Role: agent-auto-update-builder
- Subagent Type: DeepCoder
- Workspace: C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest
- Target Deliverables:
  - Round A and Round B execution evidence via GitHub Actions API:
    - Distinct run IDs
    - Distinct run URLs
    - Distinct timestamps
    - Distinct artifact digests
  - Rollback drill evidence:
    - Inject staging fault
    - Verify production/current.json remains intact (last-known-good)
    - Verify failure logged without breaking production
  - Watchdog workflow verification (60-day activity guard).

## Mandate & Scope
1. Dispatch and verify Round A and Round B workflows on remote GitHub Actions.
2. Capture full run metadata from GitHub API (run_id, run_url, job_ids, head_sha, artifact_urls, artifact_digests).
3. Execute rollback drill and capture evidence.
4. Zero em-dash (\u2014) and zero en-dash (\u2013).
