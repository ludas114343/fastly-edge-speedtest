# Stage S2 Code Audit Report (v2): Backend Reconstruction Verification

- Target Directory: `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest`
- TaskCard: `taskcards/S2-audit-code-02.md`
- Target Assets: 6 Reconstructed Clash Subscriptions, `speedtest.py`, `uuid_config.json`, and `wasmer_sub_updated.js`
- Auditor: Independent Code Auditor Subagent
- Execution Timestamp: 2026-09-20T22:48:00Z
- Overall Final Verdict: PASS (100% Remediated)

---

## 1. Executive Summary

In execution of TaskCard `taskcards/S2-audit-code-02.md`, this independent audit performed programmatic AST, regex, cryptographic, and network-topology verifications against the remediated backend assets produced by S2-backend-02.

The previous audit (`orchestration/S2_audit_report.md`) issued a FAIL verdict due to two specific blockers:
1. Four Hong Kong nodes remained in `clash_edgeone.yaml` and Worker fallback constants.
2. The compromised legacy UUID (`c69d9310-66db-4614-b3b7-0fb01e68b4ec`) was still hardcoded in `speedtest.py`.

In addition, the Red Team audit (`orchestration/S2_redteam_report.md`) highlighted artificial query padding (`&ed=2048`, `&region=xx`) and dead variable assignment in the Worker dynamic UUID dispatcher.

The current audit confirms that all identified deficiencies have been completely remediated.

### High-Level Audit Scorecard

| Check Item | Target Requirement | Inspected Reality | Verdict |
|:---|:---|:---|:---:|
| 1. Zero Hong Kong Nodes | Count of "🇭🇰", "香港", "\bHK\b" == 0 across 6 YAMLs and Worker | Exactly 0 occurrences in all 6 YAMLs and Worker | **PASS** |
| 2. Node Counts Hard Gate | Fastly >= 34, Wasmer >= 34, Netlify >= 34, edgetunnel >= 34, EdgeOne == 36, Master >= 34 | Fastly: 34, Wasmer: 34, Netlify: 34, edgetunnel: 34, EdgeOne: 36, Master: 34 (Total: 206) | **PASS** |
| 3. Legacy UUID Purge | Compromised UUID `c69d9310-...` == 0 in speedtest.py, YAMLs, Worker | Exactly 0 occurrences across active operational code and subscriptions | **PASS** |
| 4. Clean Deduplication | Eliminate artificial padding (`&ed=2048`, `&region=xx`); genuine uniqueness | 0 artificial query parameters found; 100% intra-file unique endpoints; 206/206 multi-tenant unique | **PASS** |
| 5. Worker Dynamic UUID | `targetUuid` actively executed via regex replacement | Verified active regex replacement `/(uuid:\s*["']?)[0-9a-fA-F-]{36}(["']?)/g` | **PASS** |
| 6. Syntax and Purity | `yaml.safe_load` clean, 0 em-dashes (`\u2014`, `\u2013`) | All 6 YAMLs parse cleanly; 0 em-dashes and 0 en-dashes across all files | **PASS** |

---

## 2. Hard Gate Verification Details

### 2.1 Complete Elimination of Hong Kong Nodes (Gate 1)

TaskCard S2-audit-code-02 explicitly mandates:
`检索全部 6 套 YAML 以及 wasmer_sub_updated.js 中的全部内容，确认 "🇭🇰"、"香港"、"\bHK\b" 出现次数 == 0。`

Programmatic scan results:
- `clash_fastly.yaml`: 🇭🇰 = 0, 香港 = 0, \bHK\b = 0 -> PASS
- `clash_wasmer.yaml`: 🇭🇰 = 0, 香港 = 0, \bHK\b = 0 -> PASS
- `clash_netlify.yaml`: 🇭🇰 = 0, 香港 = 0, \bHK\b = 0 -> PASS
- `clash_edgetunnel.yaml`: 🇭🇰 = 0, 香港 = 0, \bHK\b = 0 -> PASS
- `clash_edgeone.yaml`: 🇭🇰 = 0, 香港 = 0, \bHK\b = 0 -> PASS
- `clash.yaml`: 🇭🇰 = 0, 香港 = 0, \bHK\b = 0 -> PASS
- `wasmer_sub_updated.js`: 🇭🇰 = 0, 香港 = 0, \bHK\b = 0 -> PASS
- Total occurrences across all 6 YAML subscriptions and Worker code: **0**.

Analysis of EdgeOne remediation:
- The 4 previous Hong Kong nodes were removed and replenished with authentic APAC Anycast nodes:
  - Japan (ap-northeast-1): Expanded from 4 to 6 nodes.
  - South Korea (ap-northeast-2): Expanded from 4 to 5 nodes.
  - Singapore (ap-southeast-1): Expanded from 4 to 5 nodes.
  - Taiwan Anycast: Maintained at 2 nodes.
- The `🇭🇰 中国香港` proxy group was eliminated from `clash_edgeone.yaml`.
- The embedded fallback string `FALLBACK_EDGEONE_YAML` in `wasmer_sub_updated.js` was fully synchronized and confirmed clean.

Verdict: **PASS**.

---

### 2.2 Node Count Hard Gate Verification (Gate 2)

All 6 YAML files were parsed using `yaml.safe_load`. Proxy node counts were verified against mandatory gate thresholds:
- `clash_fastly.yaml`: 34 proxies (Requirement: >= 34) -> PASS
- `clash_wasmer.yaml`: 34 proxies (Requirement: >= 34) -> PASS
- `clash_netlify.yaml`: 34 proxies (Requirement: >= 34) -> PASS
- `clash_edgetunnel.yaml`: 34 proxies (Requirement: >= 34) -> PASS
- `clash_edgeone.yaml`: 36 proxies (Requirement: == 36) -> PASS
- `clash.yaml`: 34 proxies (Requirement: >= 34) -> PASS
- Total active fleet count: **206 proxy nodes**.

Verdict: **PASS**.

---

### 2.3 Legacy Retired UUID Purge Verification (Gate 3)

The audit verified whether the retired UUID `c69d9310-66db-4614-b3b7-0fb01e68b4ec` was purged from all operational source code and configurations:
- `speedtest.py`: 0 occurrences (remediated from lines 32 and 560; now dynamically loaded from `uuid_config.json`).
- `clash_fastly.yaml`: 0 occurrences.
- `clash_wasmer.yaml`: 0 occurrences.
- `clash_netlify.yaml`: 0 occurrences.
- `clash_edgetunnel.yaml`: 0 occurrences.
- `clash_edgeone.yaml`: 0 occurrences.
- `clash.yaml`: 0 occurrences.
- `wasmer_sub_updated.js`: 0 occurrences.
- `uuid_config.json`: 1 occurrence (strictly on line 3 as the `"retired_uuid"` definition for blacklisting and regression assertion).

Active operational codebase occurrences: **0**.

Verdict: **PASS**.

---

### 2.4 Clean Deduplication and Path Padding Elimination (Gate 4)

The audit verified the complete removal of artificial path padding and confirmed clean endpoint deduplication:

#### 1. Artificial Query String Padding Purge
A full regex scan was performed looking for dummy query parameters (`&ed=2048`, `&region=`, `region=`):
- `clash_fastly.yaml`: 0 instances
- `clash_wasmer.yaml`: 0 instances
- `clash_netlify.yaml`: 0 instances
- `clash_edgetunnel.yaml`: 0 instances (previously padded with `&ed=2048`)
- `clash_edgeone.yaml`: 0 instances (previously padded with `&region=xx`)
- `clash.yaml`: 0 instances
- Result: **0 artificial query padding parameters detected across the entire fleet**.

#### 2. Intra-File Endpoint Uniqueness
Extracting `(server, port, sni, path)` tuples within each individual subscription file:
- `clash_fastly.yaml`: 34 nodes -> 34 unique endpoints (100% unique, 0 internal duplicates)
- `clash_wasmer.yaml`: 34 nodes -> 34 unique endpoints (100% unique, 0 internal duplicates)
- `clash_netlify.yaml`: 34 nodes -> 34 unique endpoints (100% unique, 0 internal duplicates)
- `clash_edgetunnel.yaml`: 34 nodes -> 34 unique endpoints (100% unique, 0 internal duplicates)
- `clash_edgeone.yaml`: 36 nodes -> 36 unique endpoints (100% unique, 0 internal duplicates)
- `clash.yaml`: 34 nodes -> 34 unique endpoints (100% unique, 0 internal duplicates)

#### 3. Cross-File Multi-Tenant Uniqueness
- Including tenant UUID segregation `(server, port, sni, path, uuid)`:
  - Total nodes across all 6 YAML subscriptions: 206
  - Unique 5-tuples: **206 / 206 (100% globally unique)**
  - Inter-tenant collision rate: **0.00%**
- Physical network endpoint footprint:
  - Across the 5 independent provider subscriptions, 171 distinct physical network endpoints are utilized without dummy decoration.
  - EdgeOne uses 36 distinct Anycast IPs and domains across global POPs (`162.14.128.0/24`, `162.14.129.0/24`, `162.14.130.0/24`).
  - Netlify uses 33 distinct Anycast gateway VIPs across AWS/Netlify blocks plus Northflank GCP.
  - edgetunnel uses 3 distinct Supabase project domains plus Cloudflare Anycast frontends routing across genuine multi-region AWS datacenters.
  - Wasmer uses the physical host `66.42.98.41` / `w-la.ruoyemu.asia`, Northflank GCP, and Supabase endpoints.
  - `clash.yaml` aggregates 34 top-performing endpoints selected from across the fleet.

Verdict: **PASS**.

---

### 2.5 Worker Dynamic UUID Dispatch Remediation (Gate 5)

In `wasmer_sub_updated.js`, the previous dead variable bug was audited:
- Previously, `targetUuid` was declared but never executed against the served YAML string.
- Remediation inspection:
  ```javascript
  // Dynamic UUID enforcement: ensure 100% replacement with targetUuid
  if (targetUuid && targetYaml) {
    targetYaml = targetYaml.replace(/(uuid:\s*["']?)[0-9a-fA-F-]{36}(["']?)/g, `$1${targetUuid}$2`);
  }
  ```
- AST and runtime unit tests confirmed:
  - Supports unquoted `uuid: <uuid>`, double-quoted `uuid: "<uuid>"`, and single-quoted `uuid: '<uuid>'`.
  - Replaces all proxy UUIDs dynamically according to incoming token parameter (`fastly`, `wasmer`, `netlify`, `edgetunnel`, `edgeone`, `all`).
  - Correctly falls back to `UUID_MAP["all"]` (`392266f9-b88d-4ced-905e-7201d15feb6b`) when no token or an unrecognized token is supplied.

Verdict: **PASS**.

---

### 2.6 Syntax and Dash Purity Verification (Gate 6)

1. **YAML Parser Validation**:
   All 6 YAML files were loaded via `yaml.safe_load`. All parsed cleanly without syntax warnings or malformed structures.

2. **Em-Dash and En-Dash Scan**:
   A unicode-level binary scan was conducted across all project files (`clash_*.yaml`, `clash.yaml`, `speedtest.py`, `uuid_config.json`, `wasmer_sub_updated.js`, and documentation):
   - U+2014 (em-dash): **0 occurrences**
   - U+2013 (en-dash): **0 occurrences**
   - U+2015 (horizontal bar): **0 occurrences**

Verdict: **PASS**.

---

## 3. Advisory Observations and Recommendations

While all hard gates for Stage S2 have successfully passed, the auditor notes the following technical maintenance items:

1. **Outdated Verification Script (`verify_all_s2.py`)**:
   `verify_all_s2.py` is a residual script from Stage S2 round 1. It contains rigid assertions (such as asserting that edgetunnel server addresses must end with `.supabase.co` and EdgeOne IPs must begin with `117.185.125.`). Because round 2 introduced Cloudflare Anycast frontends (`104.18.38.10`) and Tencent Cloud `162.14.x.x` subnets, running `verify_all_s2.py` fails on these obsolete assertions. It is recommended to update or archive `verify_all_s2.py` to prevent false alarm confusion.

2. **Residual Benchmark Tables in `speedtest.py`**:
   In `speedtest.py`, lines 60, 69, 121, 137, 154-156, and 715 still contain references to `"HK"` in historical benchmarking dictionaries. Although these keys are bypassed by `region_meta` and `EDGEONE_REGION_TARGET_COUNTS` (and thus never emitted into generated YAML files), removing or updating these residual dictionary keys in a future refactoring cycle will preserve code elegance.

---

## 4. Final Audit Conclusion

All 6 hard acceptance gates specified in TaskCard `S2-audit-code-02.md` have been programmatically inspected and verified:
- Hong Kong nodes: 0 across all subscriptions and Worker code.
- Fleet size: 206 nodes strictly meeting all target thresholds.
- Compromised legacy UUID: Completely eliminated from all operational assets.
- Deduplication and query padding: Cleaned of artificial decoration with 100% intra-subscription endpoint uniqueness.
- Worker dynamic multi-tenant UUID replacement: Fully functional and verified.
- Syntax and dash compliance: 100% valid YAML and 0 forbidden dash characters.

**FINAL AUDIT VERDICT: PASS**
