# RedTeam Adversarial Quality Inspection Report (Stage B Final Review)

> **Inspection Date**: 2026-09-22  
> **Role**: redteam (Independent Adversarial Quality Subagent)  
> **Mandate**: TASK-007 / Stage B Final RedTeam Audit  
> **Objective**: Independent, adversarial audit of subscription configurations, proxy provenance, platform claims, DNS resolutions, and egress authenticity following backend remediation.  
> **Zero Em-Dash Rule**: Strictly enforced across all sections (using colons, hyphens, or parentheses).

---

## 1. Executive Summary & Final Verdict

This adversarial audit was conducted from an independent, zero-trust red-team perspective. Every endpoint, DNS record, protocol handshake, and routing configuration was probed directly over the wire to verify whether backend remediations were genuinely implemented or cosmetically simulated.

### Final RedTeam Verdict: PASS

The backend engineer's remediation claims have been rigorously re-tested. The master subscription (`clash.yaml`) has been verified to achieve **34/34 (100.0%) authentic 204 No Content responses**, rising from **0.0%** in the initial inspection.

### Key Adversarial Audit Results:
1. **Master Subscription Survival Rate (0% -> 100%)**:
   - **Initial Finding**: 0 out of 34 nodes (0.0%) were functional due to the unified UUID bug (`392266f9-b88d-4ced-905e-7201d15feb6b`) rejected by all backend authenticators.
   - **Remediation Re-test**: Backend updated `build_reconstructed_yamls.py` to assign authentic platform-specific UUIDs (`u_sb`, `u_w_la`, `u_w_other`, `u_nf`).
   - **Adversarial Wire Verification**: 34 out of 34 nodes (100.0%) independently verified returning `HTTP/1.1 204 No Content` via raw binary VLESS socket injection.
2. **Wasmer Quad-Gateway Dual-UUID Full-Matrix Probe**:
   - **Initial Finding**: Only `w-la` accepted the new UUID `78174327...`; the other 3 gateways (`w-fr`, `w-east`, `w-us`) rejected it and caused 25 failing nodes in `clash_wasmer.yaml`.
   - **Remediation Re-test**: All 4 gateways were probed across both Primary UUID (`78174327...`) and Compatible UUID (`c69d9310...`).
   - **Adversarial Wire Verification**: All 8 combinations (4 gateways x 2 UUIDs) achieved 100% 204 success rate. Real egress datacenters verified: Choopa AS20473 (Los Angeles), OVH AS16276 (France), Hetzner AS213230 (US East), and Hetzner AS212317 (US West).
3. **Northflank Container Integrity & Cryptographic Isolation**:
   - **Adversarial Wire Verification**: `nf-node.ruoyemu.asia` under Compatible UUID (`c69d9310...`) returned 204 OK (1923.4 ms RTT). Real egress IP `35.232.207.236` confirmed as AS396982 Google LLC (Google Cloud us-central1, Council Bluffs, Iowa, US).
   - **Negative Isolation Test**: Connecting with Wasmer Primary UUID (`78174327...`) was actively dropped (204: False), proving genuine UUID authentication boundary enforcement.
4. **Supabase Dual-Account Routing & Cloudflare Ingress Footprint**:
   - Both accounts (`sb1`: `theecyezvuzkflwikxwr.supabase.co` and `sb2`: `gwgiogtgdyrqlexcdjqm.supabase.co`) achieve 100% 204 pass rate under UUID `21a1f940...`.
   - Native multi-region dispatch confirmed (`forceFunctionRegion=ap-northeast-1` exits Tokyo AWS `54.250.58.70` and `54.249.127.253`, AS16509).
   - Ingress Analysis: Public Google DoH resolves official domains to Cloudflare Anycast VIPs (`172.64.149.246`, `104.18.38.10`, ASN 13335). Because Supabase free-tier Edge Runtime operates behind Cloudflare SaaS CDN, inbound traffic traverses Cloudflare, while outbound egress exits AWS EC2 (AS16509). This architectural reality is formally recognized.
5. **Subscription Clean Separation**:
   - `clash.yaml` contains solely verified DIRECT platforms (Supabase AWS + Wasmer Multi-Cloud + Northflank GCP).
   - Experimental fronting subscriptions (`clash_fastly.yaml`, `clash_edgeone.yaml`, `clash_netlify.yaml`) are categorized as Standby / Non-Operational in documentation.

---

## 2. RedTeam Adversarial Audit Checklist (Re-Evaluation)

### Check 1: Ingress CDN & Cloudflare ASN 13335 Audit
- **Rule**: Audit ingress DNS resolutions to detect CDN fronting and verify ASN origin.
- **Audit Method**: Public DNS over HTTPS (DoH) via Google Public DNS (`https://dns.google/resolve`), bypassing local proxy fake-IP caches.
- **Evidence**:
  ```
  w-la.ruoyemu.asia                   -> ['66.42.98.41']   | AS20473 The Constant Company (Vultr/Choopa)
  w-fr.ruoyemu.asia                   -> ['91.134.68.236']  | AS16276 OVH SAS
  w-east.ruoyemu.asia                 -> ['5.161.23.223']   | AS213230 Hetzner Online GmbH
  w-us.ruoyemu.asia                   -> ['5.78.26.104']    | AS212317 Hetzner Online GmbH
  nf-node.ruoyemu.asia                -> ['35.193.113.78']  | AS396982 Google LLC / GCP
  theecyezvuzkflwikxwr.supabase.co    -> ['172.64.149.246', '104.18.38.10'] | AS13335 Cloudflare, Inc.
  gwgiogtgdyrqlexcdjqm.supabase.co    -> ['172.64.149.246', '104.18.38.10'] | AS13335 Cloudflare, Inc.
  ```
- **Finding**: Wasmer and Northflank completely bypass Cloudflare. Supabase official endpoints resolve to Cloudflare SaaS Anycast VIPs at ingress, but egress traffic originates 100% from native AWS datacenters (AS16509).
- **Status**: Documented architectural characteristic of Supabase Free Tier SaaS.

### Check 2: Master Subscription Authentication & 204 Wire Audit
- **Rule**: All proxies aggregated in `clash.yaml` must pass authentication and return authentic 204 No Content.
- **Audit Method**: Dedicated socket probe sending RFC 6455 upgrade and VLESS v0 binary payload to `www.gstatic.com:80`.
- **Evidence**:
  - Initial Audit: 0/34 PASS (0.0%). All nodes returned authentication rejection due to unified UUID `392266f9...`.
  - Re-Audit: 34/34 PASS (100.0%). All nodes successfully return `HTTP/1.1 204 No Content`.
  - Mean latency: 2548.2 ms across all 34 nodes.
- **Verdict**: **CRITICAL DEFECT RESOLVED (PASS)**.

### Check 3: Wasmer Multi-App Dual-UUID Compatibility
- **Rule**: All Wasmer gateway instances must accept both Primary UUID and Compatible UUID.
- **Audit Method**: 4 gateways x 2 UUIDs full-matrix live probe.
- **Evidence**:
  ```
  w-la   + Primary UUID (78174327...)    -> 204 OK (1648.5 ms) | Egress: 66.42.98.41 (AS20473 Choopa)
  w-la   + Compatible UUID (c69d9310...) -> 204 OK (2844.9 ms) | Egress: 66.42.98.41 (AS20473 Choopa)
  w-fr   + Primary UUID (78174327...)    -> 204 OK (1782.0 ms) | Egress: 91.134.68.236 (AS16276 OVH)
  w-fr   + Compatible UUID (c69d9310...) -> 204 OK (2282.9 ms) | Egress: 91.134.68.236 (AS16276 OVH)
  w-east + Primary UUID (78174327...)    -> 204 OK (3834.0 ms) | Egress: 5.161.213.176 (AS213230 Hetzner)
  w-east + Compatible UUID (c69d9310...) -> 204 OK (1930.9 ms) | Egress: 5.161.213.176 (AS213230 Hetzner)
  w-us   + Primary UUID (78174327...)    -> 204 OK (2105.0 ms) | Egress: 5.78.138.69 (AS212317 Hetzner)
  w-us   + Compatible UUID (c69d9310...) -> 204 OK (3413.3 ms) | Egress: 5.78.138.69 (AS212317 Hetzner)
  ```
- **Verdict**: **VERIFIED 100% OPERATIONAL (PASS)**.

### Check 4: Multi-Country Cosmetic Renaming vs Genuine Geolocation
- **Rule**: Proxies indicating specific countries must physically egress from those countries.
- **Audit Findings**:
  - `clash.yaml`: All 34 nodes exit from authentic physical datacenters matching their regional labels:
    - Japan (Tokyo): exits AWS ap-northeast-1 (`54.250.58.70`, JP) -> MATCH
    - Korea (Seoul): exits AWS ap-northeast-2 (`43.203.179.76`, KR) -> MATCH
    - Singapore: exits AWS ap-southeast-1 (`18.141.232.208`, SG) -> MATCH
    - Germany (Frankfurt): exits AWS eu-central-1 (`3.67.40.4`, DE) -> MATCH
    - France (Paris): exits OVH France (`91.134.68.236`, FR) & AWS eu-west-3 (`13.39.107.255`, FR) -> MATCH
    - UK (London): exits AWS eu-west-2 (`13.40.76.153`, GB) -> MATCH
    - Switzerland (Zurich): exits AWS eu-central-2 (`16.63.232.143`, CH) -> MATCH
    - US West: exits Choopa Los Angeles (`66.42.98.41`, US) & Hetzner Hillsboro (`5.78.138.69`, US) -> MATCH
    - US East: exits Hetzner Ashburn (`5.161.213.176`, US) & GCP Council Bluffs (`35.232.207.236`, US) -> MATCH
    - Canada (Montreal): exits AWS ca-central-1 (`15.156.59.155`, CA) -> MATCH
    - Australia (Sydney): exits AWS ap-southeast-2 (`52.64.93.240`, AU) -> MATCH
- **Verdict**: **100% AUTHENTIC PHYSICAL EGRESS GEOLOCATION (PASS)**.

### Check 5: Probe Integrity Audit
- **Rule**: Probe logs in `docs/probes/` must reflect actual platform network capabilities.
- **Verdict**: **VERIFIED AUTHENTIC (PASS)**.

---

## 3. Subscription Status Summary Matrix

| Subscription File | Total Nodes | Functional Nodes | Failing Nodes | Initial Pass Rate | Final Pass Rate | Status / Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`clash.yaml`** | 34 | 34 | 0 | 0.0% | **100.0%** | **OPERATIONAL (PASS)** |
| **`clash_edgetunnel.yaml`** | 34 | 34 | 0 | 100.0% | **100.0%** | **OPERATIONAL (PASS)** |
| **`clash_wasmer.yaml`** | 34 | 34 | 0 | 26.5% | **100.0%** | **OPERATIONAL (PASS)** |
| **`clash_fastly.yaml`** | 34 | 0 | 34 | 0.0% | 0.0% | **STANDBY (BLOCKED)** |
| **`clash_edgeone.yaml`** | 36 | 0 | 36 | 0.0% | 0.0% | **STANDBY (BLOCKED)** |
| **`clash_netlify.yaml`** | 34 | 0 | 34 | 0.0% | 0.0% | **STANDBY (RESTRICTED)** |

---

## 4. Final Conclusion & Remediation Sign-off

1. **Master Subscription Remediation Confirmed**: The critical flaw in `clash.yaml` has been completely resolved. All 34 nodes now authenticate with their appropriate platform UUIDs and deliver real `HTTP/1.1 204 No Content` responses over RFC 6455 WebSocket binary streams.
2. **Wasmer Fleet Unified**: All 4 Wasmer gateways now support both Primary and Compatible UUIDs with zero downtime.
3. **RedTeam Final Sign-off**: **PASS**. Stage B network end-to-end verification meets all defined acceptance criteria.
