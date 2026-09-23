# Task Card: agent-platform-deployer (V13)

- Role: agent-platform-deployer
- Subagent Type: DeepCoder
- Workspace: C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest
- Target Deliverables:
  - evidence/deployments/summary.json
  - configs/wasmer/ (reconciled to 4 physical apps)
  - docs/platform_reconciliation.md

## Mandate & Scope
1. Reconcile platform deployments:
   - Supabase: 2 projects (theecyezvuzkflwikxwr, gwgiogtgdyrqlexcdjqm). ForceFunctionRegion invocation routes provide geographic diversity, not 16 independent physical deployments.
   - Wasmer: Exactly 4 authentic deployment IDs (dav_RjPIgtzuJwQ9, dav_2VbInozrPwQz, dav_6N1Ip1znJwA1, dav_8V7IzpyjPlnE). Remove any 5th alias node so that published nodes count <= 4.
   - Northflank: Exactly 1 deployment ID (0f2371aed029418170507fc7f0cbe3b3f6d2c943). 1:1 mapped to 1 verified proxy.
   - Fastly, Netlify, EdgeOne, Cloudflare: All 0 verified proxy nodes. Must be marked with unfinished: true and status: NO_VERIFIED_PROXY.
2. Ensure strict 1:1 alignment between platform deployment IDs and proxy backend instances.
3. Zero touch of local host proxy or network configuration.
4. Zero em-dash (\u2014) and zero en-dash (\u2013).
