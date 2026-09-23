# TaskCard S2-redteam-03: Stage S2 Adversarial Red Team Audit (Round 3)

## Target
Target Directory: `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest`
Executor: `redteam` subagent
Gate: Stage S2 Adversarial Gate (Round 3)

---

## 1. Adversarial Audit Scope & Attack Vectors

The Red Team must conduct independent, adversarial verification of the remediations reported in `orchestration/S2_backend_report_v3.md`:

1. **Attack Vector 1: Worker Prototype Boundary Fuzzing**:
   - Query `wasmer_sub_updated.js` logic with adversarial inputs: `constructor`, `toString`, `valueOf`, `__proto__`, `isPrototypeOf`, `propertyIsEnumerable`, empty string, special characters.
   - Confirm that none of these inputs produce corrupted YAML or native function signatures in the output.
   - Confirm safe fallback to default UUID `392266f9-b88d-4ced-905e-7201d15feb6b`.

2. **Attack Vector 2: Fastly Live Edge Connectivity & 421/500 Verification**:
   - Perform live TCP + TLS socket probes to Fastly Anycast VIPs (`151.101.2.79`, `151.101.66.79`, `151.101.1.194`) and domains (`ruoyemu.global.ssl.fastly.net`, `ruoyemu.freetls.fastly.net`).
   - Confirm that Fastly edge NO LONGER returns `HTTP 421 Misdirected Request` or `HTTP 500 Domain Not Found`.
   - Verify that edge Varnish routes traffic to the backend without throwing edge domain errors.

3. **Attack Vector 3: Pipeline Integrity & Hong Kong Eradication**:
   - Inspect `speedtest.py` programmatically. Verify 0 occurrences of HK strings.
   - Inspect `fastly_best_nodes.json`, `edgeone_best_nodes.json`, and all candidate JSON files.
   - Execute a syntax/compilation check on `speedtest.py` (`python -m py_compile speedtest.py`).
   - Confirm total node counts across all 6 YAML subscriptions: Fastly >= 34, Wasmer >= 34, Netlify >= 34, edgetunnel >= 34, EdgeOne == 36, Master >= 34.

4. **Attack Vector 4: Character Hygiene & Environment Integrity**:
   - Verify 0 em-dashes (`\u2014`) and 0 en-dashes (`\u2013`).
   - Confirm zero disruption to user's local network/proxy environment.

---

## 2. Deliverable
- Write full adversarial audit report to `orchestration/S2_redteam_report_v3.md`.
- Explicit final verdict: PASS or FAIL with reproduction commands and logs.
