# Task Card: agent-blackbox-auditor (V13)

- Role: agent-blackbox-auditor
- Subagent Type: DeepInvestigator
- Workspace: C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest
- Target Deliverables:
  - Remote blackbox audit run results from clean GitHub-hosted runner:
    - .github/workflows/external-blackbox-audit.yml execution proof
    - Run URL, Run ID, Job ID
    - Artifact URL and SHA-256 digest
    - Node-by-node verification logs
  - docs/security/blackbox_audit_v13.md

## Mandate & Scope
1. Perform blackbox validation exclusively from a fresh, isolated GitHub-hosted runner.
2. Fetch live subscriptions via public HTTPS URLs (no local files or relative paths).
3. Validate DNS resolution, TLS certificates, HTTP 200, YAML parsing, and proxy connectivity to generate_204.
4. Verify egress IP, ASN, and country matching.
5. Strictly zero touch of user host proxy, localhost, Windows registry, or Clash Verge.
6. Zero em-dash (\u2014) and zero en-dash (\u2013).
