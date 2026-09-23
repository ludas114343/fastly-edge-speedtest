# Task Card: agent-final-reconciler (V13)

- Role: agent-final-reconciler
- Subagent Type: DeepCoder
- Workspace: C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest
- Target Deliverables:
  - scripts/reconcile_claims.py
  - evidence/reconciliation/machine_verdict.json
  - Verification verdict: PASS or FAIL

## Mandate & Scope
1. Implement scripts/reconcile_claims.py to enforce automated verification across all 8 contradiction rules:
   - Rule 1: deployment ID count < claimed physical node count -> FAIL
   - Rule 2: 0-node platform + unfinished == 0 -> FAIL
   - Rule 3: Only relative paths, no full HTTPS URLs -> FAIL
   - Rule 4: Evidence root is only local machine path -> FAIL
   - Rule 5: Only short SHA, not 40-character SHA -> FAIL
   - Rule 6: No workflow run URL or artifact digest -> FAIL
   - Rule 7: CHAINED_ESTIMATE described as direct domestic speedtest -> FAIL
   - Rule 8: Ingress-only/origin-forwarding platform claimed as independent egress -> FAIL
2. The reconciler must read ONLY machine-verifiable artifacts (platform APIs, GitHub API, GitHub artifact digests, raw telemetry, public subscription responses).
3. If reconciliation fails, report generation is strictly BLOCKED.
4. Zero em-dash (\u2014) and zero en-dash (\u2013).
