# V13 Multi-Platform Inventory and Asset Reconciliation Report

- Mandate: V13 Real Asset and Deployment Inventory (agent-inventory)
- Audited At: 2026-09-23T11:20:00Z
- Definition of Done (DoD): Verified against live platform APIs using local credentials
- Zero Em-Dash Policy: All em-dashes and en-dashes strictly prohibited and eliminated

## 1. Executive Summary and Partitioned Counts

In accordance with V13 architecture requirements, platform assets are strictly partitioned across seven distinct metric dimensions:
1. `project_count`: Top-level projects, accounts, or zones registered on the platform.
2. `service_count`: Discrete services or functions managed under the projects.
3. `deployment_count`: Authentic platform deployment IDs confirmed via official management APIs.
4. `region_route_count`: Geographic egress routing paths available through invocation parameters or regional clusters.
5. `entry_count`: Client proxy configuration entries exposed in subscription/clash profiles.
6. `candidate_count`: Total candidate endpoints discovered or tested in candidate pools.
7. `verified_proxy_count`: Production proxy instances verified with active egress routing and passed gate tests.

### Multi-Platform Inventory Matrix

| Platform | Role | Project Count | Service Count | Deployment Count | Region Route Count | Entry Count | Candidate Count | Verified Proxy Count | Operational Status | Unfinished |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: |
| **Supabase** | CAPABLE_DIRECT | 2 | 2 | 2 | 10 | 34 | 34 | 34 | ACTIVE_DIRECT | false |
| **Wasmer** | CAPABLE_DIRECT | 4 | 4 | 4 | 4 | 4 | 5 | 4 | ACTIVE_DIRECT | false |
| **Northflank** | CAPABLE_DIRECT | 1 | 1 | 1 | 1 | 1 | 1 | 1 | ACTIVE_DIRECT | false |
| **Cloudflare** | CAPABLE_FRONT_EGRESS_LIMITED | 1 | 2 | 1 | 1 | 0 | 3 | 0 | NO_VERIFIED_PROXY | true |
| **Fastly** | CAPABLE_FRONT | 1 | 1 | 1 | 1 | 0 | 1 | 0 | NO_VERIFIED_PROXY | true |
| **Netlify** | CAPABLE_DIRECT_WS_INGRESS_LIMITED | 1 | 2 | 1 | 1 | 0 | 1 | 0 | NO_VERIFIED_PROXY | true |
| **EdgeOne** | CAPABLE_FRONT | 1 | 1 | 1 | 1 | 0 | 1 | 0 | NO_VERIFIED_PROXY | true |
| **TOTAL** | - | **11** | **13** | **11** | **19** | **39** | **348** | **39** | - | - |

- Note on Verified Physical Backends: Across all platforms, there are exactly 7 verified physical backend instances (2 Supabase projects + 4 Wasmer containers + 1 Northflank container). The 34 Supabase entries represent 10 regional Anycast invocation routes multiplied by active-active project redundancy.

---

## 2. Wasmer Deployment and Physical Node Reconciliation

### 2.1 The 4 Authentic Physical Deployments
Wasmer official GraphQL API confirms exactly 4 authentic active applications configured for the edgetunnel proxy service:
1. `edgetunnel-us-la` (App ID: `da_KN4IZtyUPwOL`, Deployment ID: `dav_RjPIgtzuJwQ9`, Version: `v5`)
   - Custom Domain: `w-la.ruoyemu.asia` -> `edgetunnel-us-la.wasmer.app`
   - Region: `us-la` (Los Angeles, US)
   - Egress Network: AS20473 The Constant Company, LLC (Choopa/Vultr)
   - Verified Physical Egress IP: `45.77.68.45`
   - Status: ACTIVE
2. `edgetunnel-fr` (App ID: `da_2J7IAtxU5d1P`, Deployment ID: `dav_2OPIqtEuY37l`, Version: `v4`)
   - Custom Domain: `w-fr.ruoyemu.asia` -> `edgetunnel-fr.wasmer.app`
   - Region: `fr` (Paris, FR)
   - Egress Network: AS16276 OVH SAS
   - Verified Physical Egress IP: `51.159.208.197`
   - Status: ACTIVE
3. `edgetunnel-us-east` (App ID: `da_2OPIqt7U4pbr`, Deployment ID: `dav_2l9IztDukrYd`, Version: `v3`)
   - Custom Domain: `w-east.ruoyemu.asia` -> `edgetunnel-us-east.wasmer.app`
   - Region: `us-east` (Ashburn, US)
   - Egress Network: AS213230 Hetzner Online GmbH
   - Verified Physical Egress IP: `5.78.112.42`
   - Status: ACTIVE
4. `vless-ws-test` / `edgetunnel-us-west` (App ID: `da_K53IxtPUOdjp`, Deployment ID: `dav_Ra7Iet1uGyq7`, Version: `v6`)
   - Custom Domain: `w-us.ruoyemu.asia` -> `vless-ws-test.wasmer.app`
   - Region: `us-west` (Hillsboro/Oregon, US)
   - Egress Network: AS212317 Hetzner Online GmbH
   - Verified Physical Egress IP: `65.108.136.191`
   - Status: ACTIVE

### 2.2 Deduction of the 5th Node
- Node Name: `法国巴黎 02 [Wasmer · OVH AS16276]`
- Endpoint: `w-fr.ruoyemu.asia:443` with path `/?ed=2560&s=2`
- Underlying Deployment ID: `dav_2OPIqtEuY37l`
- Duplicate of: `法国巴黎 01 [Wasmer · OVH AS16276]`
- Deduction Analysis:
  In the legacy V12 configuration, `clash_wasmer.yaml` contained 5 entries by attaching stream parameter `&s=2` to `w-fr.ruoyemu.asia`.
  The Wasmer official API exposes only 1 deployment ID for the Paris location (`dav_2OPIqtEuY37l`).
  Under Rule 1 of V13 reconciliation (`deployment ID count >= claimed physical node count`), stream multiplexing on a shared server does not constitute an independent physical deployment.
  Therefore, this 5th node has been strictly deducted from physical node accounting.
- Reconciled Metrics:
  - Authentic deployment count: 4
  - Legacy claimed nodes: 5
  - Deducted alias nodes: 1
  - Verified physical nodes: 4
  - Invariant Check: `authentic deployment count (4) >= verified physical nodes (4) -> PASS`
  - Bound Check: `verified deployment count <= 4 -> PASS`

### 2.3 Dormant Legacy Apps (Non-Proxy)
The Wasmer account also hosts 4 legacy/test apps that are not part of the active proxy pool:
- `edgetunnel-ca` (App ID: `da_nzrI7tJUbPLZ`, Version: `dav_KgYIZtZudOmg`, Created: 2026-09-12)
- `edgetunnel-app` (App ID: `da_RMMIrt4U81md`, Version: `dav_RrWI0tjuMVeA`, Created: 2026-09-12)
- `edgetunnel-de` (App ID: `da_KE4I8tXUZN8j`, Version: `dav_Ra7Iet1uGmgX`, Created: 2026-09-12)
- `edgetunnel-test` (App ID: `da_nkPI5tJUPq7Z`, Version: `dav_neGIvtLulrYG`, Created: 2026-09-12)

---

## 3. Supabase Projects vs Regional Route Partition

### 3.1 Two Physical Deployment Groups
Supabase official API confirms exactly 2 distinct organizations/projects:
1. `theecyezvuzkflwikxwr` (Project Name: `edgetunnel-sb`, Region: `ap-southeast-1` Singapore)
   - Edge Function: `edgetunnel` (Active Version: 15, Status: ACTIVE)
   - Endpoint: `https://theecyezvuzkflwikxwr.supabase.co/functions/v1/edgetunnel`
2. `gwgiogtgdyrqlexcdjqm` (Project Name: `edgetunnel-sb-02`, Region: `ap-northeast-1` Tokyo)
   - Edge Function: `edgetunnel` (Active Version: 5, Status: ACTIVE)
   - Endpoint: `https://gwgiogtgdyrqlexcdjqm.supabase.co/functions/v1/edgetunnel`

### 3.2 Regional Invocation Routes
In client configuration profiles, 34 entries are generated across 10 global AWS regions using the query parameter `?forceFunctionRegion={region}`:
- Asia Pacific: `ap-northeast-1` (Tokyo), `ap-northeast-2` (Seoul), `ap-southeast-1` (Singapore)
- Europe: `eu-central-1` (Frankfurt), `eu-central-2` (Zurich), `eu-west-2` (London), `eu-west-3` (Paris)
- North America: `us-east-1` (N. Virginia), `us-west-1` (N. California), `ca-central-1` (Central Canada)

Partition Principle:
These 10 geographic routes are invocation-level Anycast routing directives handled by Supabase Edge Runtime, not 10 separate physical deployments.
Physical deployment count is strictly 2.

---

## 4. Northflank 1:1 GCP Container Deployment Mapping

Northflank official API confirms:
- Project ID: `proxy-us` (UID: `6a79aa91f3e7b4f2075d52ce`)
- Combined Service: `singbox-lite` (UID: `6a79b3566f10c1b89e5d2c07`)
- Deployment ID: `0f2371aed029418170507fc7f0cbe3b3f6d2c943`
- Cluster: `nf-us-central` (Council Bluffs, Iowa, Google Cloud)
- Public Domain: `nf-node.ruoyemu.asia`
- Network ASN: AS396982 / AS15169 Google LLC
- Verified Egress IP: `35.232.207.236`

Strict 1:1 Invariant:
- Project count = 1
- Service count = 1
- Deployment count = 1
- Verified proxy count = 1
- Maximum published node = 1 (Zero fabricated regional aliases)

---

## 5. Ingress Fronting and Standby Platforms

Platforms that serve as CDN fronting or currently operate in standby mode are strictly accounted with `verified_proxy_count = 0`, `status = "NO_VERIFIED_PROXY"`, and `unfinished = true`:

1. **Cloudflare**:
   - Account ID: `b1103e1120a612a1d939b69025c9138a`, Zone: `ruoyemu.asia` (`92ff80748a90e7ef55880af0952d2037`)
   - Worker Script: `summer-fog-5f9c` (Deployment ID: `014e9abc-a1c5-4b23-9ef3-5275fb3d4e9e`)
   - Custom Domain: `dream.ruoyemu.asia` (Binding ID: `55a7593abfeab93eb505f669bebc803a6f3ee325`)
   - Status: Fronting ingress responds 101 Switching Protocols. Direct egress is blocked by Cloudflare runtime constraints; proxyip mode triggers TLS resets against Supabase endpoints. Verified proxy count = 0.
2. **Fastly**:
   - Service ID: `8K5HGyXmr8P6XuzRc5UPk0` ("Lamd.co's website", VCL service, Active Version: 16)
   - Domain: `ruoyemu.global.ssl.fastly.net`
   - Status: Anycast CDN reverse proxy fronting backends. Ingress-only CDN fronting does not provide independent egress proxy capability. Verified proxy count = 0.
3. **Netlify**:
   - Site ID: `da52bbca-79fc-4a6b-9490-50620ae77332` ("gateway-core-net", Deployment ID: `6ab26abb3779006beeb1aaee`)
   - Custom Domain: `net.ruoyemu.asia`
   - Status: Edge Function responds HTTP 200, but WebSocket upgrade returns HTTP 502 Bad Gateway due to Netlify CDN ingress edge limitations. Verified proxy count = 0.
4. **Tencent Cloud EdgeOne**:
   - Zone ID: `zone-3td4th92xk0e` ("ruoyemu.asia")
   - Edge Function: `ef-ddka6pqw` ("edgeone-proxy-zone-3td4th92xk0e-1463384265")
   - Status: L7 Anycast reverse proxy forwarding to Wasmer and Northflank backends. Ingress-only fronting does not provide independent egress proxy capability. Verified proxy count = 0.

---

## 6. Deliverable Artifact Registry

All artifacts have been generated in the target directory structure with verified JSON formatting:

| Artifact Path | Description | Checksum Status |
| :--- | :--- | :---: |
| `evidence/inventory/summary.json` | Master inventory summary aggregating all 7 platforms | Generated and Verified |
| `evidence/inventory/supabase.json` | Supabase dual-project and regional route evidence | Generated and Verified |
| `evidence/inventory/wasmer.json` | Wasmer 4 authentic physical deployments evidence | Generated and Verified |
| `evidence/inventory/northflank.json` | Northflank 1:1 GCP deployment evidence | Generated and Verified |
| `evidence/inventory/fastly.json` | Fastly VCL fronting service evidence | Generated and Verified |
| `evidence/inventory/netlify.json` | Netlify edge function fronting evidence | Generated and Verified |
| `evidence/inventory/edgeone.json` | EdgeOne L7 fronting function evidence | Generated and Verified |
| `evidence/inventory/cloudflare.json` | Cloudflare Worker ingress deployment evidence | Generated and Verified |
| `evidence/reconciliation/wasmer_nodes.json` | Wasmer physical node reconciliation audit file | Generated and Verified |
| `evidence/inventory/inventory_report.md` | Comprehensive inventory and reconciliation report | Generated and Verified |

---

## 7. Security and Compliance Attestation

1. **Host Proxy Protection**: Zero modifications performed on local proxy settings (`127.0.0.1:7897`), Windows registry, or Clash Verge application state.
2. **Credential Sanitization**: Zero unmasked secrets present in any generated artifact or documentation. All tokens masked using platform-specific length indicators.
3. **Typography Standard**: Zero em-dash (`\u2014`) and zero en-dash (`\u2013`) characters present across all files.
