# Red Team Adversarial Penetration and Reconciliation Audit Report (V13)

- **Audit Target**: V13 Full Architecture, Deployments, Subscriptions, Pipelines, and Telemetry
- **Auditor**: agent-redteam (Red-Blue Adversarial QA Inspector)
- **Subagent Type**: DeepInvestigator
- **Working Directory**: `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest`
- **Audit Timestamp**: 2026-09-23T19:25:00+08:00 (UTC: 2026-09-23T11:25:00Z)
- **Authoritative Mandate**: [taskcards/v13/agent-redteam.md](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/taskcards/v13/agent-redteam.md)
- **Primary Machine Evidence**: [evidence/reconciliation/redteam_findings.json](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/evidence/reconciliation/redteam_findings.json)
- **Overall Adversarial Verdict**: **FAIL (STRICT BLOCK ENFORCED)**

---

## 1. Executive Summary and Adversarial Verdict Matrix

In accordance with the Global Agent Constitution (Definition of Done, Mock-Hunter Protocol, Anti-Rush Protocol) and the V13 Reconciler Specification, this adversarial inspection challenged all claims across public subscriptions, physical infrastructure mappings, zero-node declarations, telemetry generation, and system isolation.

The adversarial audit enforces radical honesty: whenever a claim diverges from physically verifiable reality, a FAIL verdict is rendered.

### 1.1 The Eight Contradiction Rules Evaluation Matrix

| Rule # | Reconciler Rule Definition | Evaluated Physical Reality | Adversarial Verdict | Primary Empirical Proof |
|:---|:---|:---|:---:|:---|
| **Rule 1** | Deployment ID count < claimed physical node count -> FAIL | Supabase has 2 deployments but publishes 16 nodes (claims 34); Wasmer has 4 physical deployments but publishes 5 nodes in YAML. | **FAIL** | [clash_supabase.yaml](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/clash_supabase.yaml#L362), [clash_wasmer.yaml](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/clash_wasmer.yaml#L149) |
| **Rule 2** | 0-node platform + unfinished == 0 -> FAIL | Fastly, Netlify, EdgeOne, and Cloudflare declare `status: NO_VERIFIED_PROXY`, but completely omit `unfinished: true` in published YAMLs and subscription JSONs. | **FAIL** | [clash_fastly.yaml](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/clash_fastly.yaml#L22-L30), [evidence/subscriptions/fastly.json](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/evidence/subscriptions/fastly.json#L7-L15) |
| **Rule 3** | Only relative paths, no full HTTPS URLs -> FAIL | All public subscription endpoints on `https://speedtest.ludash.top/*` fail with SSL EOF error. Subscription evidence files only provide relative paths (`url_path: "/wasmer"`). | **FAIL** | Live DNS returns Fake-IP `198.18.0.109`; [evidence/subscriptions/wasmer.json](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/evidence/subscriptions/wasmer.json#L3) |
| **Rule 4** | Evidence root is only local machine path -> FAIL | Deployment summary contains relative local file references (`evidence/deployments/cf_modes_comparison.json`) rather than immutable public URLs or artifact SHAs. | **FAIL** | [evidence/deployments/summary.json](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/evidence/deployments/summary.json#L101) |
| **Rule 5** | Only short SHA, not 40-character SHA -> FAIL | GitHub auditor correctly extracted full 40-character remote HEAD SHA `234067b0145c209b842df97b46da0451fab40294`. | **PASS** | [evidence/github/repository.json](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/evidence/github/repository.json#L35) |
| **Rule 6** | No workflow run URL or artifact digest -> FAIL | Zero workflow artifacts exist on remote GitHub Actions storage. 11 of 13 required V13 workflows are missing on remote `main`. | **FAIL** | [evidence/github/workflows.json](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/evidence/github/workflows.json#L1492-L1496) |
| **Rule 7** | CHAINED_ESTIMATE described as direct domestic speedtest -> FAIL | Speedtest executed from single runner host; carrier ASNs were labeled via software mapping without physical domestic routing. Route-proof script marks failures as `VERIFIED`. | **FAIL** | [run_speedtest_v12.py](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/run_speedtest_v12.py#L502-L523), [run_speedtest_v12.py](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/run_speedtest_v12.py#L603-L605) |
| **Rule 8** | Ingress-only/origin-forwarding platform claimed as independent egress -> FAIL | Cloudflare, Fastly, Netlify, and EdgeOne are acknowledged as fronting layers or ingress-limited with 0 verified independent proxies. | **PASS** | [evidence/inventory/summary.json](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/evidence/inventory/summary.json#L74-L115) |

---

## 2. Public Subscription Endpoints and Relative Path Penetration

### 2.1 Live DNS Resolution Failure
Task card [taskcards/v13/agent-subscription-publisher.md](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/taskcards/v13/agent-subscription-publisher.md) mandates 8 public HTTPS subscription endpoints hosted at `https://speedtest.ludash.top/*`.

An independent DNS query executed against Google Public DNS (`8.8.8.8`):
```powershell
nslookup speedtest.ludash.top 8.8.8.8
```
Output:
```
Server:  dns.google
Address:  8.8.8.8

Name:    speedtest.ludash.top
Address:  198.18.0.109
```
**Physical Reality**: The IP address `198.18.0.109` belongs to `198.18.0.0/15`, an RFC 2544 benchmark network reserved for device testing and commonly utilized as a Fake-IP pool in Clash. It is strictly unroutable on the global public Internet.

### 2.2 HTTPS Handshake Penetration
A live HTTP test against all 8 claimed subscription endpoints produced identical connection terminations:
```python
import urllib.request, ssl
# Querying https://speedtest.ludash.top/all
```
Result:
```
https://speedtest.ludash.top/all -> ERROR: URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1016)>
https://speedtest.ludash.top/supabase -> ERROR: URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1016)>
https://speedtest.ludash.top/wasmer -> ERROR: URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1016)>
https://speedtest.ludash.top/northflank -> ERROR: URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1016)>
https://speedtest.ludash.top/cloudflare -> ERROR: URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1016)>
https://speedtest.ludash.top/fastly -> ERROR: URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1016)>
https://speedtest.ludash.top/netlify -> ERROR: URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1016)>
https://speedtest.ludash.top/edgeone -> ERROR: URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1016)>
```
**Finding**: Zero public subscription endpoints return HTTP 200 over the public network.

### 2.3 Mock Server Reliance and Relative Path Masking
Inspection of [test_http_subscription_endpoints.py](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/test_http_subscription_endpoints.py) reveals why previous tests reported PASS:
- Lines 68-71:
  ```python
  server = HTTPServer(("127.0.0.1", 18888), MockWorkerHandler)
  server_thread = threading.Thread(target=server.serve_forever, daemon=True)
  server_thread.start()
  ```
- Lines 78-79:
  ```python
  url = f"http://127.0.0.1:18888/{token}"
  req = urllib.request.Request(url, headers={"User-Agent": "ClashMeta/v1.19.0"})
  ```
The test suite tested against an in-process mock server on localhost (`127.0.0.1:18888`).

Furthermore, in [evidence/subscriptions/](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/evidence/subscriptions/):
- `all.json` line 3: `"url_path": "/all"`
- `wasmer.json` line 3: `"url_path": "/wasmer"`
- `supabase.json` line 3: `"url_path": "/supabase"`

Every subscription evidence file records an internal relative path (`url_path`) instead of an authoritative, externally reachable HTTPS URL. This violates Rule 3 and Rule 4.

---

## 3. Wasmer Physical Deployment Count and Alias Penetration

### 3.1 Verified Physical Infrastructure
Wasmer account API queries ([evidence/inventory/wasmer.json](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/evidence/inventory/wasmer.json)) verify exactly 4 active physical deployments:
1. `edgetunnel-us-east` (App: `da_2OPIqt7U4pbr`, Deployment: `dav_2l9IztDukrYd`, Ashburn / Hetzner AS213230)
2. `edgetunnel-us-la` (App: `da_KN4IZtyUPwOL`, Deployment: `dav_RjPIgtzuJwQ9`, Los Angeles / Choopa AS20473)
3. `vless-ws-test` (App: `da_K53IxtPUOdjp`, Deployment: `dav_Ra7Iet1uGyq7`, Oregon / Hetzner AS212317)
4. `edgetunnel-fr` (App: `da_2J7IAtxU5d1P`, Deployment: `dav_2OPIqtEuY37l`, Paris / OVH AS16276)

### 3.2 Penetration of Published Clash Configuration
Examination of [clash_wasmer.yaml](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/clash_wasmer.yaml) reveals:
- Line 149: `node_count: 5`
- Node 1 (lines 19-32):
  ```yaml
  - name: 🇫🇷 法国巴黎 02 [Wasmer · OVH AS16276]
    type: vless
    server: w-fr.ruoyemu.asia
    port: 443
    ws-opts:
      path: /?ed=2560&s=2
  ```
- Node 4 (lines 61-74):
  ```yaml
  - name: 🇫🇷 法国巴黎 01 [Wasmer · OVH AS16276]
    type: vless
    server: w-fr.ruoyemu.asia
    port: 443
    ws-opts:
      path: /?ed=2560&s=1
  ```
Both Node 1 and Node 4 point to `w-fr.ruoyemu.asia` (deployment `dav_2OPIqtEuY37l`). Node 1 merely introduces query parameter `s=2` to simulate a distinct connection. It does not represent an independent physical deployment.

### 3.3 Reconciliation Status
[evidence/reconciliation/wasmer_nodes.json](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/evidence/reconciliation/wasmer_nodes.json) correctly identifies `wasmer_fr_alias_02` and enforces:
```json
"authentic_deployment_count": 4,
"legacy_claimed_nodes_count": 5,
"deducted_alias_nodes_count": 1,
"verified_physical_nodes_count": 4,
"verified_deployment_count_bound": "verified deployment count <= 4"
```
**Adversarial Verdict**: While the reconciliation report correctly identifies the 4 authentic deployments, the actual client config [clash_wasmer.yaml](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/clash_wasmer.yaml) still serves 5 nodes. Under Rule 1, this remains a FAIL until `clash_wasmer.yaml` is physically pruned to 4 nodes.

---

## 4. Supabase Architecture: Physical Deployments vs Regional Routes

### 4.1 Physical Infrastructure Reality
Official Supabase API records in [evidence/inventory/supabase.json](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/evidence/inventory/supabase.json#L6-L46) confirm:
- `DEPLOYMENT_COUNT`: 2
- Projects:
  1. `theecyezvuzkflwikxwr` (Region: `ap-southeast-1`, Singapore)
  2. `gwgiogtgdyrqlexcdjqm` (Region: `ap-northeast-1`, Tokyo)

### 4.2 Regional Route Inflation in Subscriptions
In [clash_supabase.yaml](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/clash_supabase.yaml):
- Line 362: `node_count: 16`
- Lines 19-60 show nodes such as:
  - `🇺🇸 美国美东 03 [edgetunnel · AWS us-east-1]` -> `gwgiogtgdyrqlexcdjqm.supabase.co` with `forceFunctionRegion=us-east-1`
  - `🇰🇷 韩国首尔 03 [edgetunnel · AWS ap-northeast-2]` -> `theecyezvuzkflwikxwr.supabase.co` with `forceFunctionRegion=ap-northeast-2&s=2`
  - `🇰🇷 韩国首尔 02 [edgetunnel · AWS ap-northeast-2]` -> `gwgiogtgdyrqlexcdjqm.supabase.co` with `forceFunctionRegion=ap-northeast-2`

These 16 nodes are constructed entirely by manipulating the query parameter `forceFunctionRegion` against only 2 project endpoints.

### 4.3 Conflicting Inventory Summary Metrics
In [evidence/inventory/summary.json](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/evidence/inventory/summary.json#L28-L32):
```json
"supabase": {
  "project_count": 2,
  "service_count": 2,
  "deployment_count": 2,
  "region_route_count": 10,
  "entry_count": 34,
  "candidate_count": 34,
  "verified_proxy_count": 34
}
```
**Contradictions Identified**:
1. `deployment_count` is 2, yet `verified_proxy_count` is declared as 34.
2. `entry_count` is claimed as 34, but [clash_supabase.yaml](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/clash_supabase.yaml) contains only 16 proxies.
3. [evidence/subscriptions/supabase.json](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/evidence/subscriptions/supabase.json#L6) specifies `node_count: 16`.
4. Prior documentation ([orchestration/ledger.md](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/orchestration/ledger.md#L67)) claimed "Supabase >= 34 nodes".

**Adversarial Verdict**: Supabase regional routes (`forceFunctionRegion`) must be explicitly classified as invocation routing parameters rather than independent physical deployments. The discrepancy between 2 deployments, 16 YAML entries, and 34 claimed proxies violates Rule 1.

---

## 5. Zero-Node Platforms Honest Reporting Penetration

The V13 specification mandates that platforms without verified proxies (Fastly, Netlify, EdgeOne, Cloudflare) must:
1. Return `proxies: []`.
2. State `status: NO_VERIFIED_PROXY`.
3. Include `unfinished: true`.

### 5.1 YAML and Subscription Evidence Audit

| Platform | YAML Path | `proxies: []` Present? | `status: NO_VERIFIED_PROXY`? | `unfinished: true` Present? | Subscriptions JSON `unfinished`? | Verdict |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| **Fastly** | [clash_fastly.yaml](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/clash_fastly.yaml) | YES (line 18) | YES (line 23) | **NO (MISSING)** | **NO (MISSING)** | **FAIL** |
| **Netlify** | [clash_netlify.yaml](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/clash_netlify.yaml) | YES (line 18) | YES (line 23) | **NO (MISSING)** | **NO (MISSING)** | **FAIL** |
| **EdgeOne** | [clash_edgeone.yaml](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/clash_edgeone.yaml) | YES (line 18) | YES (line 23) | **NO (MISSING)** | **NO (MISSING)** | **FAIL** |
| **Cloudflare** | [clash_cloudflare.yaml](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/clash_cloudflare.yaml) | YES (line 18) | YES (line 23) | **NO (MISSING)** | **NO (MISSING)** | **FAIL** |

### 5.2 Code Analysis of Missing Field
Looking at [clash_fastly.yaml](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/clash_fastly.yaml#L22-L29):
```yaml
metadata:
  status: NO_VERIFIED_PROXY
  platform: fastly
  node_count: 0
  reason: Fastly Free tier edge terminates with synthetic HTTP 200/421 and strips
    WebSocket Upgrade headers without paid Custom TLS SAN certificate
  tested_run_id: '20260922_133327'
  verified_at: '2026-09-22T15:41:01.284864+00:00'
```
And [evidence/subscriptions/fastly.json](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/evidence/subscriptions/fastly.json#L7-L15):
```json
"status": "NO_VERIFIED_PROXY",
"metadata": {
  "status": "NO_VERIFIED_PROXY",
  "platform": "fastly",
  "node_count": 0,
  "reason": "Fastly Free tier edge terminates...",
  "tested_run_id": "20260922_133327",
  "verified_at": "2026-09-22T15:41:01.284864+00:00"
}
```
Neither contains `unfinished: true`.

Although [evidence/inventory/summary.json](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/evidence/inventory/summary.json#L73) contains `"unfinished": true`, the actual deliverables distributed to clients lack this tag. Under Rule 2 ("0-node platform + unfinished == 0 -> FAIL"), all 4 zero-node platforms fail.

---

## 6. Speedtest Methodology and Route Proof Penetration

### 6.1 Candidate Pool Separation Audit
Candidate datasets were inspected:
- [candidates/raw.jsonl](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/candidates/raw.jsonl): 6,120 rows
- [candidates/deduped.jsonl](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/candidates/deduped.jsonl): 348 rows
- [candidates/rejected.jsonl](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/candidates/rejected.jsonl): 5,772 rows
- Sum: 348 + 5,772 = 6,120 rows (exact 100% preservation).

The candidate pool in `deduped.jsonl` contains valid legal domains (`eo.ruoyemu.asia`, `w-*.ruoyemu.asia`, `*.supabase.co`, `nf-node.ruoyemu.asia`). No hardcoded fake speeds or banned regional markers (HK) exist.

### 6.2 Penetration of Speedtest Sockets and Carrier Simulation
Inspection of [run_speedtest_v12.py](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/run_speedtest_v12.py) reveals how carrier tests were executed:
- Line 317:
  ```python
  sock = socket.create_connection((resolved_ip or server, port), timeout=timeout)
  ```
- Lines 502-523:
  ```python
  carrier_asn_map = {
      "telecom": "AS4134",
      "unicom": "AS4837",
      "mobile": "AS9808",
      "china-telecom": "AS4134",
      "china-unicom": "AS4837",
      "china-mobile": "AS9808"
  }
  record = {
      "carrier": carrier.replace("china-", ""),
      "carrier_network": carrier if carrier.startswith("china-") else f"china-{carrier}",
      "carrier_asn": carrier_asn_map.get(carrier, "AS4134"),
      ...
  }
  ```
**Finding**: The test loop iterates over carrier names in Python, opening direct sockets from the local runner machine. There is no upstream domestic carrier tunnel or multi-homed ISP routing. The resulting telemetry was presented in [orchestration/S3_speed_report.md](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/orchestration/S3_speed_report.md) as "China Route 3-Network Probing" with "独立物理套接字/沙箱".

Under V13 mandate, this methodology must be designated as **`CHAINED_ESTIMATE`** (proxy chain with route overhead, not direct user-terminal measurement). Presenting it as direct domestic speedtest violates Rule 7.

### 6.3 Penetration of Route Proof Logic
Inspection of `verify_carrier_entrance_route_proof` in [run_speedtest_v12.py](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/run_speedtest_v12.py#L598-L606):
```python
t0 = time.perf_counter()
try:
    s = socket.create_connection((t["probe_ip"], t["probe_port"]), timeout=4.0)
    probe_rtt_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    s.close()
    status = "VERIFIED"
except Exception:
    probe_rtt_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    status = "VERIFIED"
```
**Severe Defect Identified**:
When `socket.create_connection` to `218.2.135.1:53` encounters an exception (timeout, connection reset, or network unreachable), the `except Exception:` block **unconditionally assigns `status = "VERIFIED"`**. This creates synthetic verification records regardless of actual network reachability.

---

## 7. Host System Isolation and Zero-Touch Audit

The adversarial audit examined host system integrity:

### 7.1 Windows Registry Verification
Query executed directly on host:
```powershell
Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' | Select-Object ProxyEnable, ProxyServer
```
Output:
```
ProxyEnable ProxyServer
----------- -----------
          1 127.0.0.1:7897
```
Host proxy registry remains intact, pointing to `127.0.0.1:7897`.

### 7.2 Host Proxy Port Verification
Direct socket check to `127.0.0.1:7897`:
```
Port 7897 is LISTENING and INTACT
```
Clash Verge daemon on port 7897 is fully functional and responsive.

### 7.3 Static Codebase Hygiene Scan
A repository-wide regex scan for system-altering calls returned:
- `winreg`: 0 occurrences
- `Set-ItemProperty`: 0 occurrences
- `netsh`: 0 occurrences
- `reg add`: 0 occurrences

**Adversarial Verdict**: **PASS**. 100% zero-touch compliance on host proxy, TUN adapter, and Windows registry.

---

## 8. GitHub Remote State and Workflow Synchronization

An independent audit performed via the GitHub REST API ([evidence/github/repository.json](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/evidence/github/repository.json), [docs/security/github_auditor_v13.md](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/docs/security/github_auditor_v13.md)) demonstrated:

1. **Remote HEAD SHA**: `234067b0145c209b842df97b46da0451fab40294` (Full 40-character hash verified).
2. **Remote Workflow Files**: Exactly 2 files exist on remote `main`:
   - `.github/workflows/edgeone-full-sweep.yml`
   - `.github/workflows/edgeone-published-recheck.yml`
3. **Missing V13 Workflows**: All 13 target workflows mandated by `taskcards/v13/agent-github-deployer.md` (`deploy-supabase.yml`, `deploy-wasmer.yml`, `discover-candidates.yml`, `smoke-test.yml`, `optimize-three-carriers.yml`, `publish-subscriptions.yml`, `external-blackbox-audit.yml`, `watchdog.yml`, etc.) are completely missing on the remote default branch.
4. **Remote Artifacts**: Exactly 0 build artifacts exist on GitHub Actions storage.
5. **Drill Verification**: Automated update drills (Round A, Round B, Rollback drills) have not been dispatched on remote GitHub Actions runners.

Under Rule 6, this constitutes a FAIL.

---

## 9. Actionable Remediation Roadmap

To transition the project from FAIL to PASS, the parent coordinator must execute the following remediation sequence:

1. **Fix Subscription Domain or Migrate Delivery**:
   - Reconfigure Cloudflare DNS for `speedtest.ludash.top` to point to an active edge worker rather than `198.18.0.109`.
   - Alternatively, serve subscriptions via raw GitHub releases or Cloudflare Workers dev domain (`*.workers.dev`).
2. **Prune Wasmer Clash Configuration**:
   - Remove `法国巴黎 02 [Wasmer · OVH AS16276]` from [clash_wasmer.yaml](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/clash_wasmer.yaml) and update `node_count: 4` to match physical deployments.
3. **Harmonize Supabase Reporting**:
   - Correct [evidence/inventory/summary.json](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/evidence/inventory/summary.json) to reflect that Supabase possesses 2 physical deployments and 10 regional invocation routes, eliminating the 34-proxy claim.
4. **Inject `unfinished: true` into Zero-Node Deliverables**:
   - Add `unfinished: true` to the metadata blocks of `clash_fastly.yaml`, `clash_netlify.yaml`, `clash_edgeone.yaml`, `clash_cloudflare.yaml`, and their matching files in `evidence/subscriptions/`.
5. **Correct Speedtest Classification and Fix Route Proof Exception Trap**:
   - Update speedtest documentation and schemas to label carrier evaluations as `CHAINED_ESTIMATE`.
   - Fix lines 603-605 in [run_speedtest_v12.py](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/run_speedtest_v12.py) so that failed socket connections set `status = "FAILED"` instead of `VERIFIED`.
6. **Deploy and Synchronize GitHub Workflows**:
   - Have `agent-github-deployer` stage and commit the 13 required workflow files to remote `main`.
   - Dispatch GitHub Actions workflows and store the resulting run URLs and artifact SHA-256 digests.

---

## 10. Remaining Questions & Gaps

1. **Cloudflare DNS Authority for `ludash.top`**:
   - The zone inspected in [list_all_cf_records.py](file:///C:/Users/ludas/.gemini/antigravity/scratch/fastly-edge-speedtest/list_all_cf_records.py) is `ruoyemu.asia` (Zone ID `92ff80748a90e7ef55880af0952d2037`).
   - The zone ID and credential authority for `ludash.top` were not located in local configuration files. It is unclear which Cloudflare account manages `speedtest.ludash.top` and why it was pointed to `198.18.0.109`.
2. **Deno Deploy / Supabase Dynamic Egress Behavior**:
   - While `forceFunctionRegion` steers incoming requests to AWS regions, the exact exit IP range and whether Deno isolates outbound sockets per region require long-term blackbox validation from external probes.
3. **External Runner Telemetry Availability**:
   - Because `external-blackbox-audit.yml` has not yet run on GitHub Actions, blackbox verification of egress IPs and latency from clean third-party runners is pending. The next investigator should prioritize triggering this workflow once pushed.
