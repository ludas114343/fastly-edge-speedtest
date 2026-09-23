# Task Card: agent-speedtest-builder (V13)

- Role: agent-speedtest-builder
- Subagent Type: DeepCoder
- Workspace: C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest
- Target Deliverables:
  - candidates/raw.jsonl (6,120 rows)
  - candidates/deduped.jsonl (348 rows)
  - candidates/rejected.jsonl (5,772 rows)
  - Raw telemetry records with full round details:
    results/telemetry/YYYY-MM-DD.jsonl.gz (or JSONL per node)
  - Route proof documentation with proxy chain overhead disclaimer:
    results/route-proof/
  - Clear methodology statement: CHAINED_ESTIMATE (proxy chain with route overhead, not direct user-terminal measurement).

## Mandate & Scope
1. Decouple raw candidates (6120), deduplicated candidates (348), and final verified nodes.
2. Ensure each verified node has 3 carriers x 3 rounds = 9 independent protocol records with real 204 status.
3. Explicitly document that testing mode is CHAINED_ESTIMATE and explain the chain overhead.
4. Route proof must contain real egress IP, ASN, ASN organization, echo response, and timestamp.
5. Zero em-dash (\u2014) and zero en-dash (\u2013).
