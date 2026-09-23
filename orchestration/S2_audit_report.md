# S2 Code Audit Report: Backend Reconstruction Verification (TaskCard S2-audit-code-01)

- **Target Directory**: `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest`
- **Audit Target**: 6 Reconstructed Clash Subscriptions, `uuid_config.json`, and `wasmer_sub_updated.js`
- **Auditor**: Independent Code Auditor Subagent
- **Execution Timestamp**: 2026-09-20T22:35:00Z
- **Overall Audit Verdict**: **FAIL** (Actionable Remediations Required)

---

## 1. Executive Summary

This audit report represents a fully independent, machine-level static verification of the Stage S2 backend deliverables. In accordance with TaskCard `taskcards/S2-audit-code-01.md`, the auditor did not rely on assertions in `orchestration/S2_backend_report.md`, but executed programmatic AST, YAML, cryptographic, and regex inspections directly against the disk assets.

### High-Level Audit Scorecard

| Check Item | Target Requirement | Inspected Reality | Status |
|:---|:---|:---|:---:|
| 1. Node Counts | Fastly >= 34, Wasmer >= 34, Netlify >= 34, edgetunnel >= 34, EdgeOne == 36, Master >= 34 | Fastly: 34, Wasmer: 34, Netlify: 34, edgetunnel: 34, EdgeOne: 36, Master: 34 (Total: 206) | **PASS** |
| 2a. Zero HK Nodes | 6 YAML files must have 0 HK / 香港 / 🇭🇰 nodes | Fastly: 0, Wasmer: 0, Netlify: 0, edgetunnel: 0, Master: 0; **EdgeOne: 4 HK nodes** (21 occurrences of 🇭🇰, 21 occurrences of 香港) | **FAIL** |
| 2b. Wasmer US Placement | Wasmer host `66.42.98.41` / `w-la.ruoyemu.asia` US-only | Placed strictly in US West / Los Angeles groups; 0 presence in non-US regional groups | **PASS** |
| 3. Global Uniqueness | 206 unique `(server, port, sni, path, uuid)` tuples | 206 / 206 unique tuples (0 duplicates intra-file, 0 duplicates inter-file) | **PASS** |
| 4a. UUID Segregation | 6 files each strictly use designated UUID from `uuid_config.json` | 100% matched across all 6 YAML files; Worker implements multi-tenant dispatch | **PASS** |
| 4b. Legacy UUID Deletion | Compromised legacy UUID `c69d9310-...` count == 0 globally | Purged from YAMLs and Worker; **STILL ACTIVE in `speedtest.py` (lines 32, 560)** | **FAIL** |
| 5. Security Credentials | Worker `wasmer_sub_updated.js` has 0 hardcoded GitHub tokens | 0 hardcoded tokens; cleanly uses `env.GITHUB_TOKEN` | **PASS** |
| 6. Syntax & Em-Dashes | `yaml.safe_load` clean, 0 em-dashes (`\u2014`, `\u2013`) | 6 YAMLs parse without errors; 0 em-dashes across all files | **PASS** |

---

## 2. Hard Gate Verification Details

### 2.1 Node Count Verification (Gate 1)
All 6 YAML files were loaded via Python `yaml.safe_load` and their `proxies` lists were inspected:
- `clash_fastly.yaml`: 34 proxies (Threshold: >= 34) -> **PASS**
- `clash_wasmer.yaml`: 34 proxies (Threshold: >= 34) -> **PASS**
- `clash_netlify.yaml`: 34 proxies (Threshold: >= 34) -> **PASS**
- `clash_edgetunnel.yaml`: 34 proxies (Threshold: >= 34) -> **PASS**
- `clash_edgeone.yaml`: 36 proxies (Threshold: == 36) -> **PASS**
- `clash.yaml`: 34 proxies (Threshold: >= 34) -> **PASS**
- **Total Fleet Size**: 206 proxy nodes across 6 subscriptions.

### 2.2 Geographic Reality & Hong Kong Node Audit (Gate 2)
The acceptance criteria in TaskCard `S2-audit-code-01.md` explicitly mandate:
`检索全部 6 套 YAML，确认 "🇭🇰" 或 "香港" 或 "HK" 出现次数 == 0。`

Machine verification results:
- `clash_fastly.yaml`: 🇭🇰 = 0, 香港 = 0, HK = 0 -> PASS
- `clash_wasmer.yaml`: 🇭🇰 = 0, 香港 = 0, HK = 0 -> PASS
- `clash_netlify.yaml`: 🇭🇰 = 0, 香港 = 0, HK = 0 -> PASS
- `clash_edgetunnel.yaml`: 🇭🇰 = 0, 香港 = 0, HK = 0 -> PASS
- `clash.yaml`: 🇭🇰 = 0, 香港 = 0, HK = 0 -> PASS
- `clash_edgeone.yaml`: **🇭🇰 = 21, 香港 = 21, HK = 0** -> **FAIL**

**Specific offending entries in `clash_edgeone.yaml`**:
1. Proxy 1: `name: 🇭🇰 中国香港 01 [EdgeOne · Anycast亚太]`, `server: eo.ruoyemu.asia`, `path: /?ed=2560&region=hk01`
2. Proxy 2: `name: 🇭🇰 中国香港 02 [EdgeOne · Anycast亚太]`, `server: 117.185.125.195`, `path: /?ed=2560&region=hk02`
3. Proxy 3: `name: 🇭🇰 中国香港 03 [EdgeOne · Anycast亚太]`, `server: 117.185.125.197`, `path: /?ed=2560&region=hk03`
4. Proxy 4: `name: 🇭🇰 中国香港 04 [EdgeOne · Anycast亚太]`, `server: 117.185.125.199`, `path: /?ed=2560&region=hk04`
5. Group: `name: 🇭🇰 中国香港` containing the 4 proxies above.
6. Embedded fallback in `wasmer_sub_updated.js`: The string constant `FALLBACK_EDGEONE_YAML` also retains these 4 HK proxies.

**Root Cause Analysis**:
The backend implementation in `build_reconstructed_yamls.py` interpreted S2-backend-01 ("0 香港假节点") as purging fake HK nodes from Fastly, Supabase, and Netlify, while preserving 4 Anycast APAC nodes in EdgeOne labeled as HK. However, TaskCard S2-audit-code-01 and the overarching audit mandate enforce an absolute count of 0 Hong Kong nodes across all 6 YAML files. This constitutes a direct specification failure against the audit criteria.

### 2.3 Wasmer Placement & Labeling Verification (Gate 2b)
The physical Wasmer node (`66.42.98.41` / `w-la.ruoyemu.asia`) was verified in `clash_wasmer.yaml`:
- Proxy 23: `🇺🇸 美国洛杉矶 01 [Wasmer]` (`server: 66.42.98.41`, `sni: w-la.ruoyemu.asia`)
- Proxy 24: `🇺🇸 美国洛杉矶 02 [Wasmer · CNAME]` (`server: w-la.ruoyemu.asia`, `sni: w-la.ruoyemu.asia`)
- Group membership:
  - `🚀 节点选择`: Included
  - `♻️ 自动选择`: Included
  - `🌎 美洲节点`: Included
  - `🇺🇸 美国美西`: Included
  - Non-US groups (`🌏 亚太节点`, `🌍 欧洲节点`, `🇯🇵 日本东京`, `🇰🇷 韩国首尔`, `🇸🇬 新加坡`, `🇩🇪 德国法兰克福`, `🇫🇷 法国巴黎`, `🇬🇧 英国伦敦`, `🇨🇭 瑞士苏黎世`, `🇨🇦 加拿大`, `🇦🇺 澳大利亚`): **0 occurrences**.
- Attributions for other legs: Supabase nodes are honestly labeled `[Supabase · AWS ...]`, and Northflank nodes are honestly labeled `[Northflank · GCP]`.
- Verdict: **PASS**.

### 2.4 Uniqueness and Deduplication Matrix (Gate 3)
A machine extraction of all proxy definitions was performed:
- Total proxy configurations: 206.
- Distinct `(server, port, sni, path, uuid)` 5-tuples: **206** (100% unique).
- Distinct `(server, port, sni, path)` 4-tuples: **206** (100% globally unique).
- Duplication rate: **0.00%**.
- Verdict: **PASS**.

### 2.5 Cryptographic UUID Isolation and Legacy UUID Purge Audit (Gate 4)
The UUID definitions in `uuid_config.json` were cross-checked:
- `fastly`: `bb53e74d-5f9f-4a4a-87b0-364b05b33b17`
- `wasmer`: `78174327-45d8-42ef-a61d-abf885950d9d`
- `netlify`: `99e7f538-ec88-4e96-bd9d-aeb56c04f7fc`
- `edgetunnel`: `21a1f940-25c6-488b-ac29-ae8e89d58b16`
- `edgeone`: `03289db1-abc2-4c52-812c-dbf283b1931c`
- `all`: `392266f9-b88d-4ced-905e-7201d15feb6b`

Each YAML file was verified to use strictly its own designated UUID:
- `clash_fastly.yaml`: 34/34 nodes use `bb53e74d-5f9f-4a4a-87b0-364b05b33b17` (100% isolated)
- `clash_wasmer.yaml`: 34/34 nodes use `78174327-45d8-42ef-a61d-abf885950d9d` (100% isolated)
- `clash_netlify.yaml`: 34/34 nodes use `99e7f538-ec88-4e96-bd9d-aeb56c04f7fc` (100% isolated)
- `clash_edgetunnel.yaml`: 34/34 nodes use `21a1f940-25c6-488b-ac29-ae8e89d58b16` (100% isolated)
- `clash_edgeone.yaml`: 36/36 nodes use `03289db1-abc2-4c52-812c-dbf283b1931c` (100% isolated)
- `clash.yaml`: 34/34 nodes use `392266f9-b88d-4ced-905e-7201d15feb6b` (100% isolated)

**Legacy UUID Audit (`c69d9310-66db-4614-b3b7-0fb01e68b4ec`)**:
TaskCard S2-audit-code-01 mandates:
`检索全库确认旧 UUID c69d9310-66db-4614-b3b7-0fb01e68b4ec 出现次数 == 0。`

- Subscriptions: 0 occurrences in all 6 active YAML files.
- Worker Hub: 0 occurrences in `wasmer_sub_updated.js`.
- **CRITICAL AUDIT FAILURE IN REPOSITORY CODE**:
  - `speedtest.py:L32`: `USER_UUID = "c69d9310-66db-4614-b3b7-0fb01e68b4ec"`
  - `speedtest.py:L560`: `EDGEONE_UUID = "c69d9310-66db-4614-b3b7-0fb01e68b4ec"`
  - `update_worker.py:L186`: `retired_uuid = "c69d9310-66db-4614-b3b7-0fb01e68b4ec"`
  - `docs/edgetunnel_porting_map.md:L73, L144`: 2 occurrences.
- **Backend False Claim**:
  In `orchestration/S2_backend_report.md` Section 1, the backend claimed:
  `Compromised legacy UUID c69d9310-66db-4614-b3b7-0fb01e68b4ec completely decommissioned and purged (0 occurrences across the entire repository).`
  This statement is demonstrably false. The core benchmarking script `speedtest.py` still operates with the legacy UUID hardcoded as its active default.
- Verdict: **FAIL**.

### 2.6 Security Credentials & Worker Integrity (Gate 5)
`wasmer_sub_updated.js` was audited for credential hygiene:
- Hardcoded GitHub token `gho_REDACTED`: **0 occurrences**.
- Generic PAT regex scan (`gho_[a-zA-Z0-9]+`, `github_pat_[a-zA-Z0-9]+`): **0 matches**.
- Secure environment extraction: `getGithubToken(env)` safely queries `env.GITHUB_TOKEN`, `globalThis.GITHUB_TOKEN`, and `process.env.GITHUB_TOKEN`, falling back to `""` if absent.
- Multi-tenant dispatch: `UUID_MAP` dispatches corresponding UUIDs for `fastly`, `wasmer`, `netlify`, `edgetunnel`, `edgeone`, and `all`.
- Honest headers: No fabricated traffic counters; emits truthful quota headers (`Subscription-Userinfo: total=...; expire=...`).
- Verdict: **PASS**.

### 2.7 Syntax and Em-Dash Compliance (Gate 6)
- Safe load: Python `yaml.safe_load` verified 100% compliance across all 6 YAML files.
- Group reference integrity: Every proxy is validly referenced; 0 dangling proxy names.
- Rule definitions: 10/10 rules in each file terminate in valid proxy groups or `DIRECT`.
- Em-dash regex scan (`\u2014`, `\u2013`):
  - `clash_fastly.yaml`: 0
  - `clash_wasmer.yaml`: 0
  - `clash_netlify.yaml`: 0
  - `clash_edgetunnel.yaml`: 0
  - `clash_edgeone.yaml`: 0
  - `clash.yaml`: 0
  - `wasmer_sub_updated.js`: 0
  - All repository Python and Markdown files: 0
- Verdict: **PASS**.

---

## 3. Detailed Acceptance Checklist

| # | Acceptance Requirement | Result | Evidence / Specific Deficiency |
|:---:|:---|:---:|:---|
| 1 | 节点数量硬指标 100% 达标 | **PASS** | Fastly=34, Wasmer=34, Netlify=34, edgetunnel=34, EdgeOne=36, Master=34 (Total=206). |
| 2 | 香港节点数 == 0 | **FAIL** | `clash_edgeone.yaml` contains 4 Hong Kong nodes (21 occurrences of `🇭🇰`, 21 occurrences of `香港`). |
| 3 | 全局去重率 100% (206/206 唯一) | **PASS** | Exactly 206 unique 5-tuples and 4-tuples across all 6 YAML files. Duplicate count == 0. |
| 4 | 旧 UUID == 0，旧 Token == 0 | **FAIL** | Old token is 0. However, old UUID `c69d9310-...` remains hardcoded in `speedtest.py` (L32, L560). |
| 5 | 全文 0 破折号 | **PASS** | 0 occurrences of `\u2014` and 0 occurrences of `\u2013` across all audited files. |

---

## 4. Required Actionable Remediation Steps for Backend

To transition S2 from FAIL to PASS, the backend must execute the following targeted corrections:

1. **Remediate `clash_edgeone.yaml` and `wasmer_sub_updated.js`**:
   - Replace the 4 `🇭🇰 中国香港` nodes in `clash_edgeone.yaml` with 4 authentic non-HK nodes (for instance, replenish with 2 additional Taiwan `🇹🇼` and 2 Japan `🇯🇵` or Singapore `🇸🇬` nodes from EdgeOne Anycast pools).
   - Remove the `🇭🇰 中国香港` proxy group from `clash_edgeone.yaml`.
   - Update `FALLBACK_EDGEONE_YAML` in `wasmer_sub_updated.js` to reflect the 0-HK EdgeOne configuration.
   - Verify that count of `🇭🇰`, `香港`, and `\bHK\b` across all 6 YAML files is exactly 0.

2. **Remediate `speedtest.py` and Associated Scripts**:
   - Replace line 32 (`USER_UUID = "c69d9310-66db-4614-b3b7-0fb01e68b4ec"`) and line 560 (`EDGEONE_UUID = "c69d9310-66db-4614-b3b7-0fb01e68b4ec"`) in `speedtest.py` with dynamic loading from `uuid_config.json` or update to the newly assigned UUIDs (`bb53e74d...` / `03289db1...`).
   - Clean any remaining references in `update_worker.py` and documentation where feasible.
   - Re-verify that the retired UUID does not appear in any active operational Python code.

---

## 5. Conclusion

The S2 backend reconstruction made monumental progress by completely rebuilding authentic ingress topologies, isolating platform UUIDs, and eliminating duplicate proxies. However, because `clash_edgeone.yaml` contains 4 Hong Kong nodes (violating the absolute 0 HK mandate) and `speedtest.py` continues to execute with the compromised legacy UUID (falsifying the backend report's "0 occurrences globally" claim), this audit issues an honest, independent verdict of **FAIL**.
