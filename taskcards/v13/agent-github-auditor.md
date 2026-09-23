# Task Card: agent-github-auditor (V13)

- Role: agent-github-auditor
- Subagent Type: DeepInvestigator
- Workspace: C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest
- Target Deliverables:
  - evidence/github/repository.json
  - evidence/github/workflows.json
  - docs/security/github_auditor_v13.md

## Mandate & Scope
1. Query GitHub official API for:
   - Full repository URL, owner, repo name, default branch
   - 40-character commit SHA of remote HEAD and its commit URL
   - Inventory of all 13 workflow files under .github/workflows/
   - Actions enabled status, workflow IDs, states, and recent runs
   - Workflow run IDs, run URLs, job IDs, head SHAs, artifact URLs, and artifact SHA-256 digests
2. Confirm zero discrepancy between remote repository state and reported metrics.
3. Reject any claims based only on local git status or short SHAs.
4. Zero em-dash (\u2014) and zero en-dash (\u2013).
