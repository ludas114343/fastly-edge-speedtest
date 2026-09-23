# TaskCard S2-backend-03: Stage S2 Backend Remediation (Round 3)

## Target
Target Project: `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest`
Executor: `backend` subagent
Verification Gates: Unanimous PASS from both `audit-code` and `redteam`

---

## 1. Context & Red Team Findings (from `S2_redteam_report_v2.md`)

The Adversarial Red Team reported FAIL on Stage S2 Round 2 due to 3 specific defects:
1. **Worker Hub Prototype Injection / Boundary Vulnerability (`wasmer_sub_updated.js`)**:
   `tokenParam in UUID_MAP` evaluates `true` for standard prototype properties (`constructor`, `toString`, `valueOf`, `__proto__`). When querying `?token=constructor`, `targetUuid` becomes `function Object() { [native code] }`, which replaces UUIDs with native function strings and corrupts client YAML configurations.
2. **Fastly Edge Routing & Domain Validation (Service `8K5HGyXmr8P6XuzRc5UPk0`)**:
   - SNI `fastly.ruoyemu.asia` on Fastly Anycast VIPs returns `HTTP/1.1 421 Misdirected Request` because no active Fastly TLS subscription matches this SAN.
   - Host `ruoyemu.freetls.fastly.net` / `ruoyemu.global.ssl.fastly.net` returns `HTTP/1.1 500 Domain Not Found` ("unknown domain: ruoyemu.global.ssl.fastly.net. Please check that this domain has been added to a service.").
   - You must inspect Fastly Service `8K5HGyXmr8P6XuzRc5UPk0` via Fastly API (token in `D:\Obsidian\CollegeAid\planning\平台凭据速查.md`), add `ruoyemu.global.ssl.fastly.net` and `ruoyemu.freetls.fastly.net` to the service version domains, activate the new version, verify that live TLS requests to Fastly edge return HTTP 200/404/camouflage instead of 421 or 500, and ensure `clash_fastly.yaml` uses working SNI/Host and valid Anycast VIPs.
3. **`speedtest.py` Hong Kong Cleanup & Quota Redistribution**:
   - Lines 60, 69, 121, 137, 152-156 in `speedtest.py` still reference `"HK"`.
   - Purge `"HK"` from `WASMER_DOMAINS`, `WASMER_PHYSICAL_ENDPOINTS`, `REGION_CODES`, `REGION_TARGET_COUNTS`, `PROVEN_DOMESTIC_BENCHMARKS`.
   - Redistribute the 3 HK quotas to APAC regions: JP (+1, total 5), KR (+1, total 4), SG (+1, total 4) or similar to ensure total node count is exactly 34.
   - Ensure running `speedtest.py` and `build_reconstructed_yamls.py` yields 34 nodes for Fastly, Wasmer, Netlify, edgetunnel, Master, and 36 for EdgeOne.
   - Clean any residual HK entries from `fastly_best_nodes.json` and candidate files.

---

## 2. Action Items for `backend` Subagent

### Action 1: Fix Worker Dynamic UUID Prototype Boundary (`wasmer_sub_updated.js`)
In `wasmer_sub_updated.js`:
Replace:
```javascript
const tokenParam = (url.searchParams.get("token") || "all").toLowerCase();
const token = tokenParam in UUID_MAP ? tokenParam : "all";
```
With safe own-property checking:
```javascript
const tokenParam = (url.searchParams.get("token") || "all").toLowerCase();
const hasToken = Object.prototype.hasOwnProperty.call(UUID_MAP, tokenParam);
const token = hasToken ? tokenParam : "all";
```
Or create `UUID_MAP` with `Object.create(null)`.
Verify with Node.js that `?token=constructor`, `?token=toString`, `?token=__proto__` cleanly fall back to `"all"` and return valid UUID `392266f9-b88d-4ced-905e-7201d15feb6b`.

### Action 2: Remediate Fastly Edge Domain & Routing Live
1. Read Fastly credentials from `D:\Obsidian\CollegeAid\planning\平台凭据速查.md`.
2. Query Fastly API for service `8K5HGyXmr8P6XuzRc5UPk0`:
   - Inspect existing domains on the active version: `GET https://api.fastly.com/service/8K5HGyXmr8P6XuzRc5UPk0/version/<active_version>/domain`.
   - Check what domains are present (e.g. `fastly.ruoyemu.asia`, `ruoyemu.global.ssl.fastly.net`, `ruoyemu.freetls.fastly.net`).
   - Clone the active version to a new draft version.
   - Add both `ruoyemu.global.ssl.fastly.net` and `ruoyemu.freetls.fastly.net` (and any necessary Fastly Free TLS domain) using `POST /service/8K5HGyXmr8P6XuzRc5UPk0/version/<new_version>/domain`.
   - Activate the new version.
3. Live test:
   - Run a Python / curl socket probe to Fastly edge IP `151.101.2.79` (or `151.101.1.6`) with SNI and Host `ruoyemu.global.ssl.fastly.net` and `ruoyemu.freetls.fastly.net`.
   - Confirm that it NO LONGER returns HTTP 500 "unknown domain" or HTTP 421 "Misdirected Request".
   - If `ruoyemu.global.ssl.fastly.net` is the valid working FreeTLS domain, update `clash_fastly.yaml`, Worker fallbacks, and `speedtest.py` to use it as the SNI/Host where applicable.

### Action 3: Sanitize `speedtest.py` & Synchronize Pipeline
1. Remove all `"HK"` keys and values from:
   - `WASMER_DOMAINS`
   - `WASMER_PHYSICAL_ENDPOINTS`
   - `REGION_CODES`
   - `REGION_TARGET_COUNTS`
   - `PROVEN_DOMESTIC_BENCHMARKS`
2. Redistribute the 3 quotas across JP, KR, SG:
   - JP: 5 (was 4)
   - KR: 4 (was 3)
   - SG: 4 (was 3)
   - US: 11
   - EU: 10
   - Total: 5 + 4 + 4 + 11 + 10 = 34 nodes!
3. Ensure running `speedtest.py` or node generator produces exactly 34 proxies with 0 HK nodes.
4. Clean `fastly_best_nodes.json` so no HK entries remain.

---

## 3. Deliverable & Reporting
- Write full report to `orchestration/S2_backend_report_v3.md`.
- Ensure zero em-dashes (`\u2014`) and zero en-dashes (`\u2013`).
- Provide concrete command output, exit codes, and live probe logs.
