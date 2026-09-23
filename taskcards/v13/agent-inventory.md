# Task Card: agent-inventory (V13)

- Role: agent-inventory
- Subagent Type: DeepCoder
- Workspace: C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest
- Target Deliverables:
  - evidence/inventory/summary.json
  - evidence/inventory/supabase.json
  - evidence/inventory/wasmer.json
  - evidence/inventory/northflank.json
  - evidence/inventory/fastly.json
  - evidence/inventory/netlify.json
  - evidence/inventory/edgeone.json
  - evidence/inventory/cloudflare.json
  - evidence/reconciliation/wasmer_nodes.json

## Mandate & Scope
1. Query official platform APIs (Supabase, Wasmer, Northflank, Fastly, Netlify, EdgeOne, Cloudflare) using secure local credentials.
2. Strictly partition inventory into:
   - project_count
   - service_count
   - deployment_count
   - region_route_count
   - entry_count
   - candidate_count
   - verified_proxy_count
3. Reconcile Wasmer: Only 4 authentic physical deployments exist (edgetunnel-us-la, edgetunnel-fr, edgetunnel-us-east, edgetunnel-us-west). The 5th node must be removed or strictly bounded: verified deployment count <= 4. Output evidence/reconciliation/wasmer_nodes.json.
4. Supabase: Clearly distinguish 2 projects/deployment groups from regional invocation routes (forceFunctionRegion). Region routes are NOT independent physical deployments.
5. Northflank: Exactly 1 deployment (singbox-lite in GCP Iowa). Max published node = 1.
6. Zero touch of local host proxy (127.0.0.1:7897), Clash Verge, or Windows registry.
7. Zero em-dash (\u2014) and zero en-dash (\u2013).
