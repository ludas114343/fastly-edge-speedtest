# Stage S2 Adversarial Red Team Audit Report (v2)

- Target Directory: `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest`
- TaskCard: `taskcards/S2-redteam-02.md`
- Red Team Auditor: Adversarial Red Team Subagent
- Audit Execution Timestamp: 2026-09-20T22:50:00Z
- Final Verdict: FAIL (Live Traffic Routing and Code Inconsistencies Detected)

---

## 1. Executive Adversarial Assessment

The Adversarial Red Team executed an uncompromising, multi-vector adversarial audit of the Phase S2 deliverables produced by `S2-backend-02`. The scope encompassed:
1. Fleet-wide Hong Kong node eradication across all 6 YAML subscriptions, the Worker hub, and the benchmarking engine `speedtest.py`.
2. Live network, DNS, and TLS verification of Fastly Service `8K5HGyXmr8P6XuzRc5UPk0` and Version 11 activation status.
3. Verification of artificial query padding (`&ed=2048`, `&region=xx`) elimination and physical deduplication reality.
4. Security, boundary condition, and regex injection analysis of the Worker dynamic UUID transformer in `wasmer_sub_updated.js`.
5. Authenticity and transparency of Tencent Cloud EdgeOne technical constraints and runtime documentation.
6. Rigorous character hygiene verification (zero em-dashes `\u2014` and zero en-dashes `\u2013`).

### High-Level Adversarial Audit Matrix

| Audit Dimension | Evaluation Standard | Adversarial Finding | Verdict |
|:---|:---|:---|:---:|
| 1. Hong Kong Node Elimination | 0 HK references in YAMLs, Worker, and active benchmark code | All 6 YAML subscriptions and Worker fallbacks are 100% clean. However, `speedtest.py` retains hardcoded HK benchmarks, and `fastly_best_nodes.json` retains HK entries. | **PARTIAL PASS / DEFECT** |
| 2. Fastly Live Routing & Version 11 | Version 11 active; 421 Misdirected Request eliminated live | Handshakes to Fastly Anycast VIPs with SNI `fastly.ruoyemu.asia` return `HTTP/1.1 421 Misdirected Request`. Handshakes to `ruoyemu.freetls.fastly.net` return `HTTP/1.1 500 Domain Not Found`. Live edge routing is non-functional. | **FAIL** |
| 3. Query Padding Elimination | Clean removal of `&ed=2048` and `&region=`; genuine physical heterogeneity | 100% clean. Zero query padding detected. All 206 nodes across the fleet possess distinct physical endpoints `(server, port, sni, path)`. | **PASS** |
| 4. Worker Dynamic UUID Safety | Safe regex substitution, robust boundary handling, zero injection vectors | Found Prototype Boundary Vulnerability. Using `tokenParam in UUID_MAP` accepts prototype keys (`constructor`, `toString`, `valueOf`, `__proto__`), replacing UUIDs with native function signatures and corrupting client YAML configs. | **FAIL** |
| 5. EdgeOne Boundary Transparency | No false claims of native VLESS execution; live runtime proof | Live HTTP probe confirmed: `{"hasWebSocket": false, "hasConnect": false, "runtime": "EdgeOne-Edge-Function"}`. Real-name auth failure (`FailedOperation.NoRealNameAuth`) truthfully disclosed. | **PASS** |
| 6. Character Hygiene & Secret Leaks | 0 em-dashes (`\u2014`), 0 en-dashes (`\u2013`), 0 credential leaks | Scanned all project files: exactly 0 em-dashes, 0 en-dashes, and 0 leaked credentials. | **PASS** |

**Final Adversarial Verdict**: **FAIL**
While structural YAML remediation and physical deduplication were executed to a high standard, the deliverables cannot receive a PASS verdict due to two critical operational defects: (1) Fastly edge frontends continue to throw HTTP 421 / 500 errors live, and (2) the Worker dynamic UUID dispatcher contains a prototype injection vulnerability that generates invalid YAML configurations.

---

## 2. Itemized Adversarial Audit Findings

### Dimension 1: Hong Kong Elimination and Benchmark Pipeline Integrity

#### 1.1 Subscription File and Worker Fallback Verification
Every proxy in each YAML file and every embedded fallback string in `wasmer_sub_updated.js` was programmatically audited:
- `clash_fastly.yaml`: 34 proxies, 0 HK proxies, 0 HK proxy groups.
- `clash_wasmer.yaml`: 34 proxies, 0 HK proxies, 0 HK proxy groups.
- `clash_netlify.yaml`: 34 proxies, 0 HK proxies, 0 HK proxy groups.
- `clash_edgetunnel.yaml`: 34 proxies, 0 HK proxies, 0 HK proxy groups.
- `clash_edgeone.yaml`: 36 proxies, 0 HK proxies, 0 HK proxy groups.
- `clash.yaml`: 34 proxies, 0 HK proxies, 0 HK proxy groups.
- `wasmer_sub_updated.js`: All 6 `FALLBACK_*_YAML` constant strings contain exactly 0 HK proxies and 0 HK proxy groups.
- In EdgeOne, the 4 retired HK proxies were successfully replaced with authentic APAC Anycast endpoints (Japan Tokyo expanded to 6 nodes, South Korea Seoul to 5 nodes, Singapore to 5 nodes, Taiwan to 2 nodes).

#### 1.2 Pipeline Inconsistency in `speedtest.py`
While `build_reconstructed_yamls.py` produced compliant YAML files, `speedtest.py` was not completely sanitized:
1. `speedtest.py` line 60: `WASMER_DOMAINS` still maps `"HK": "w-la.ruoyemu.asia"`.
2. `speedtest.py` lines 68 to 72: `WASMER_PHYSICAL_ENDPOINTS` still retains 2 physical endpoints for `"HK"`.
3. `speedtest.py` line 121: `REGION_CODES` still maps `"HK": "ap-southeast-1"`.
4. `speedtest.py` line 137: `REGION_TARGET_COUNTS` still requests `"HK": 3`.
5. `speedtest.py` lines 152 to 156: `PROVEN_DOMESTIC_BENCHMARKS` still contains 3 hardcoded Hong Kong benchmark IPs (`119.45.41.162`, `43.133.237.158`, `119.28.162.39`).
6. `speedtest.py` lines 268 to 280: `region_meta` removes HK, but because the 3 quotas were not redistributed to other regions, running `build_clash_yaml_for_platform` yields only 31 proxies instead of the required 34 proxies.
7. Artifact `fastly_best_nodes.json` on disk still starts with 3 Hong Kong benchmark winners.
8. Candidate pools (`fastly_candidates.json`, `edgeone_candidates.json`, `wasmer_candidates.json`, `netlify_candidates.json`) retain between 117 and 171 HK entries.

**Red Team Judgment**: Backend used a separate generator script (`build_reconstructed_yamls.py`) to bypass `speedtest.py`. Any future run of `speedtest.py` will regenerate inconsistent files and reintroduce Hong Kong data into `fastly_best_nodes.json`.

---

### Dimension 2: Fastly Live Routing and Version 11 Activation Audit

#### 2.1 Backend Implementation Claims
In `orchestration/S2_backend_report_v2.md` lines 132 to 143, backend asserted:
- Version 11 activation command executed via Fastly API (`PUT /service/8K5HGyXmr8P6XuzRc5UPk0/version/11/activate`).
- Version 11 is locked and active.
- `ruoyemu.freetls.fastly.net` presents a valid `*.freetls.fastly.net` certificate and eliminates 421 Misdirected Request.

#### 2.2 Live Adversarial Probe Results
The Red Team conducted direct network socket probes against Fastly edge cache nodes across multiple Anycast IP blocks (`151.101.1.6`, `151.101.2.79`, `151.101.2.132`):

1. **Probe to Fastly Global Anycast VIP `151.101.1.6` with SNI `fastly.ruoyemu.asia`**:
   ```text
   CONNECT 151.101.1.6:443
   SNI: fastly.ruoyemu.asia
   Host: fastly.ruoyemu.asia
   Path: /functions/v1/edgetunnel

   Response:
   HTTP/1.1 421 Misdirected Request
   Connection: close
   Content-Length: 291
   content-type: text/plain; charset=utf-8
   x-served-by: cache-chi-kigq8000080
   Requested host does not match any Subject Alternative Names (SANs) on TLS certificate in use with this connection.
   ```

2. **Probe to Fastly FreeTLS VIP `151.101.2.79` with SNI and Host `ruoyemu.freetls.fastly.net`**:
   ```text
   CONNECT 151.101.2.79:443
   SNI: ruoyemu.freetls.fastly.net
   Host: ruoyemu.freetls.fastly.net

   Response:
   HTTP/1.1 500 Domain Not Found
   Connection: close
   Content-Length: 301
   Server: Varnish
   X-Served-By: cache-chi-kigq8000066-CHI

   Body:
   Fastly error: unknown domain: ruoyemu.global.ssl.fastly.net. Please check that this domain has been added to a service.
   ```

3. **Direct Probe to `fastly.ruoyemu.asia`**:
   ```text
   GET /functions/v1/edgetunnel HTTP/1.1
   Host: fastly.ruoyemu.asia

   Response:
   HTTP/1.1 421 Misdirected Request
   x-served-by: cache-chi-klot8100046
   ```

#### 2.3 Root Cause Analysis
- Fastly custom domains (`fastly.ruoyemu.asia`) require an active Fastly TLS Subscription with SAN provisioning. Without an active TLS subscription matching `fastly.ruoyemu.asia`, edge termination returns `HTTP 421 Misdirected Request`.
- Fastly FreeTLS domains must be explicitly added to the service's `domains` array (`ruoyemu.global.ssl.fastly.net`). Fastly Varnish explicitly returns `500 Domain Not Found: unknown domain ruoyemu.global.ssl.fastly.net`, confirming that edge Varnish routing is unconfigured.
- Consequently, all 34 nodes in `clash_fastly.yaml` fail live connectivity checks. Not a single byte of proxy traffic can reach the origin.

**Red Team Judgment**: FAIL. The claim that version 11 activation resolved the edge routing defect is refuted by live telemetry.

---

### Dimension 3: Elimination of Artificial Query Padding and Deduplication

#### 3.1 Parameter Purge Verification
All YAML configurations were inspected for query string pollution:
- `&ed=2048`: 0 occurrences across all 6 YAML files.
- `&region=`: 0 occurrences across all 6 YAML files.
- `?region=`: 0 occurrences across all 6 YAML files.

#### 3.2 Endpoint Uniqueness Verification
Every proxy configuration was decomposed into its physical routing tuple: `(server, port, sni, path)`.
- `clash_fastly.yaml`: 34 proxies -> 34 unique physical tuples (10 distinct Fastly frontends / Anycast VIPs paired with 11 AWS region origins).
- `clash_wasmer.yaml`: 34 proxies -> 34 unique physical tuples (Wasmer LA physical server `66.42.98.41`, Northflank GCP `nf-node.ruoyemu.asia`, and Supabase Anycast VIPs).
- `clash_netlify.yaml`: 34 proxies -> 34 unique physical tuples (33 distinct Netlify gateway Anycast IPs across global subnets plus Northflank GCP).
- `clash_edgetunnel.yaml`: 34 proxies -> 34 unique physical tuples (3 independent Supabase project domains paired with 11 AWS region backends).
- `clash_edgeone.yaml`: 36 proxies -> 36 unique physical tuples (36 distinct Anycast IP addresses from Tencent Cloud subnets `162.14.128.0/24`, `162.14.129.0/24`, and `162.14.130.0/24`).
- `clash.yaml`: 34 proxies -> 34 unique physical tuples.

**Red Team Judgment**: PASS. The removal of synthetic query padding is complete, and deduplication is achieved entirely through physical network differentiation.

---

### Dimension 4: Worker Dynamic UUID Substitution Safety Analysis

#### 4.1 Implementation Under Review
In `wasmer_sub_updated.js` lines 96 to 129:
```javascript
const tokenParam = (url.searchParams.get("token") || "all").toLowerCase();
const token = tokenParam in UUID_MAP ? tokenParam : "all";
const targetUuid = UUID_MAP[token] || UUID_MAP["all"];
// ...
if (targetUuid && targetYaml) {
  targetYaml = targetYaml.replace(/(uuid:\s*["']?)[0-9a-fA-F-]{36}(["']?)/g, `$1${targetUuid}$2`);
}
```

#### 4.2 Adversarial Vulnerability: Prototype Boundary Pollution / DoS
The Red Team tested edge-case inputs against this implementation in Node.js:
1. When a user or scanner sends a request with `?token=constructor`:
   - `tokenParam in UUID_MAP` evaluates to `true` because `constructor` exists on `Object.prototype`.
   - `token` is set to `"constructor"`.
   - `UUID_MAP["constructor"]` returns `[Function: Object]`.
   - `targetUuid` becomes `function Object() { [native code] }`.
   - `targetYaml.replace(...)` outputs:
     `uuid: function Object() { [native code] }`
2. When querying `?token=__proto__`:
   - `UUID_MAP["__proto__"]` returns `[object Object]`.
   - `targetYaml.replace(...)` outputs:
     `uuid: [object Object]`
3. When querying `?token=toString` or `?token=valueOf`:
   - Returns native function strings as the proxy UUID.

Any Clash or Mihomo client attempting to parse the resulting subscription throws an unrecoverable YAML parsing error or configuration validation failure.

#### 4.3 Remediation Requirement
Replace the prototype-leaking `in` check with safe property lookup:
```javascript
const hasToken = Object.prototype.hasOwnProperty.call(UUID_MAP, tokenParam);
const token = hasToken ? tokenParam : "all";
const targetUuid = UUID_MAP[token];
```
Or create the map with null prototype: `const UUID_MAP = Object.assign(Object.create(null), { ... });`.

**Red Team Judgment**: FAIL. High-severity boundary handling flaw in the subscription delivery endpoint.

---

### Dimension 5: EdgeOne Live Runtime Constraints Documentation

#### 5.1 Real Runtime Capability Probe
The Red Team verified the live Tencent Cloud EdgeOne Function deployment at:
`https://edgeone-proxy-zone-3td4th92xk0e-1463384265.eo-edgefunctions1.com/`
The live endpoint returned:
```json
{
  "hasWebSocket": false,
  "hasWebSocketPair": false,
  "hasConnect": false,
  "runtime": "EdgeOne-Edge-Function"
}
```
This confirms that Edge Functions on Tencent Cloud do not support:
1. `WebSocket` or `WebSocketPair` APIs.
2. `connect()` or raw TCP socket dialing.

#### 5.2 Domain Acceleration Status
Direct SSL connection to EdgeOne VIPs (`162.14.128.7`, `162.14.128.3`, `162.14.129.1`) with SNI `eo.ruoyemu.asia` triggers immediate protocol-level termination:
`[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol`
Public DNS resolution of `eo.ruoyemu.asia` directs traffic to Cloudflare frontends (`198.18.0.58` / Wasmer hub) rather than Tencent Cloud edge nodes.

Both limitations are documented in `S2_backend_report_v2.md` and `docs/edgetunnel_porting_map.md`.

**Red Team Judgment**: PASS. Documentation adheres strictly to verified runtime boundaries without exaggerations.

---

### Dimension 6: Character Hygiene and Secret Leaks

1. **Em-Dash and En-Dash Audit**:
   - Programmatic search for `\u2014` (em-dash): exactly 0 occurrences across all workspace files.
   - Programmatic search for `\u2013` (en-dash): exactly 0 occurrences across all workspace files.
2. **Credential and Secret Audit**:
   - `wasmer_sub_updated.js`: Zero hardcoded GitHub personal access tokens. Correctly accesses `env.GITHUB_TOKEN`.
   - Retired UUID `c69d9310-66db-4614-b3b7-0fb01e68b4ec`: 0 occurrences across active operational code. Only present in `uuid_config.json` as the blacklist reference key.

**Red Team Judgment**: PASS. Complete compliance with character constraints and credential isolation.

---

## 3. Adversarial Challenges to Reference Documentation

### 3.1 `docs/edgetunnel_porting_map.md`
- Section 2.6 accurately breaks down the Cloudflare Workers lock-in (`connect()`, `WebSocketPair`, `request.cf`) and correctly defines the missing socket adapters on EdgeOne, Wasmer, and Supabase Deno.
- Minor finding: Line 344 refers to `(HK 香港, JP 日本, ...)` in historical narrative text. While harmless documentation prose, it should be sanitized in future revisions.

### 3.2 `docs/trace_web_study.md` and `docs/trace_web_porting_map.md`
- Section 1.1 correctly identifies the absence of Go binaries (`main.exe`, `nexttrace-core.exe`) in the reference repository.
- Section 1.2 presents a sound two-tier architecture replacing Go dependencies with native Python networking and an isolated, ephemeral sandbox (`geo_gate_verify.py`).

---

## 4. Remediation Checklist for S2 Closure

To achieve a clean PASS verdict in the next evaluation cycle, the following items must be resolved:

1. **Worker Hub Prototype Fix (`wasmer_sub_updated.js`)**:
   Replace `tokenParam in UUID_MAP` with `Object.prototype.hasOwnProperty.call(UUID_MAP, tokenParam)` to eliminate prototype inheritance poisoning.
2. **Fastly Edge Routing Remediation**:
   Either provision a valid TLS subscription for `fastly.ruoyemu.asia` on Fastly, or configure `ruoyemu.global.ssl.fastly.net` properly in Fastly Varnish domain management, eliminating the live HTTP 421 and 500 errors.
3. **`speedtest.py` Hong Kong Cleanup**:
   Purge the hardcoded Hong Kong endpoints from lines 60, 69, 121, 137, and 152 to 156 of `speedtest.py`. Redistribute the 3 Hong Kong quotas to Japan, South Korea, and Singapore so that running `speedtest.py` generates 34 nodes consistently without recontaminating `fastly_best_nodes.json`.
