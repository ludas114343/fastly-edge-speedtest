# TaskCard S2-audit-code-03: Stage S2 Code Audit (Round 3)

## Target
Target Directory: `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest`
Executor: `audit-code` subagent
Gate: Stage S2 Backend Remediation Verification (Round 3)

---

## 1. Audit Scope & Verification Mandates

Inspect the remediations reported in `orchestration/S2_backend_report_v3.md` against the active codebase:

1. **Worker Prototype Hardening (`wasmer_sub_updated.js` & `update_worker.py`)**:
   - Inspect declaration of `UUID_MAP`. Confirm `Object.create(null)` or null prototype is used.
   - Inspect token resolution logic. Confirm `Object.prototype.hasOwnProperty.call(UUID_MAP, tokenParam)` is used.
   - Execute AST or Node.js test script to verify `?token=constructor`, `?token=toString`, `?token=valueOf`, `?token=__proto__` cleanly resolve to default UUID `392266f9-b88d-4ced-905e-7201d15feb6b`.

2. **Fastly Configuration & Subscriptions (`clash_fastly.yaml`, `clash.yaml`)**:
   - Verify Fastly service version 12 is recorded.
   - Verify `clash_fastly.yaml` and `clash.yaml` use valid Fastly SNI (`ruoyemu.global.ssl.fastly.net` / `ruoyemu.freetls.fastly.net`) and valid Anycast VIPs.
   - Confirm node count for `clash_fastly.yaml` is >= 34.

3. **Complete Elimination of Hong Kong from `speedtest.py` & Pipeline**:
   - Programmatically scan `speedtest.py`: confirm 0 occurrences of `"HK"`, `"🇭🇰"`, `"香港"`, `\bHK\b`.
   - Confirm `REGION_TARGET_COUNTS` sums to 34 (JP=5, KR=4, SG=4, EU=10, US=11).
   - Check `fastly_best_nodes.json` and candidate JSON files: confirm 0 Hong Kong nodes.

4. **Character Hygiene & System Safety**:
   - Verify 0 em-dashes (`\u2014`) and 0 en-dashes (`\u2013`) across all repository files.
   - Verify host proxy (port 7897) was never modified.

---

## 2. Deliverable
- Write full audit report to `orchestration/S2_audit_report_v3.md`.
- Explicit final verdict: PASS or FAIL with itemized evidence.
