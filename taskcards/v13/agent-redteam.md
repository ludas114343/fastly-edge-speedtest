# Task Card: agent-redteam (V13)

- Role: agent-redteam
- Subagent Type: DeepInvestigator
- Workspace: C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest
- Target Deliverables:
  - docs/security/redteam_v13.md
  - evidence/reconciliation/redteam_findings.json

## Mandate & Scope
1. Conduct rigorous adversarial audit challenging all claims:
   - Verify whether public subscription URLs actually resolve, return HTTP 200, and contain valid YAML/proxies.
   - Verify whether Wasmer deployment IDs match node count (<= 4).
   - Check if Supabase regional routes are mislabeled as physical deployments.
   - Verify that Fastly, Netlify, EdgeOne, and Cloudflare are honestly reported as unfinished: true with 0 verified proxies.
   - Verify that 348 candidate pool results and 9-round tests are not fabricated or hardcoded.
   - Confirm zero touch of host system proxy (127.0.0.1:7897), TUN adapter, or registry.
2. Ensure radical honesty: if any flaw exists, report FAIL.
3. Zero em-dash (\u2014) and zero en-dash (\u2013).
