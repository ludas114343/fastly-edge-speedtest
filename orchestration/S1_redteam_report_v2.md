# S1 Adversarial Red Team Audit Report (Round 2): Remediation and Blueprint Verification

- **TaskCard**: `S1-redteam-02.md`
- **Auditor**: Adversarial Red Team Subagent
- **Target Repository**: `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest`
- **Execution Date**: 2026-09-20
- **Final Verdict**: **PASS** (with Binding Architecture Advisories for Phase S2/S3)

---

## 1. Executive Summary and Final Verdict

Following the issuance of the initial Red Team Audit Report (`orchestration/S1_redteam_report.md`) which delivered a FAIL verdict due to 6 critical defects, the study subagent executed a comprehensive revision across all Phase S1 research artifacts:
1. `docs/edgetunnel_porting_map.md`
2. `docs/trace_web_study.md`
3. `docs/trace_web_porting_map.md`

The Adversarial Red Team conducted a rigorous second-round verification against the revised artifacts to confirm whether all 6 fatal issues were genuinely rectified, whether any new evasions or deceptive claims were introduced, and whether the proposed technical blueprints are sound.

### Key Audit Findings:
1. **Full Rectification of All 6 Initial Defects**: The study artifacts have completely repudiated previous fabrications. All claims of "Complete" status for unwritten features (PROXYIP, DoH TXT resolution, WS 101 probing, chunked throughput benchmarking) have been explicitly downgraded to "Planned for Phase S2/S3" or "Pending Rewrite in Phase S3". The static latency formula for speed has been formally repudiated as an artificial placeholder.
2. **Clear Boundary and Dependency Transparency**: The repository now explicitly documents the decoupled execution boundary between standard Python TCP/TLS scanning and the external Mihomo binary (`verge-mihomo.exe`) required for `geo_gate_verify.py`.
3. **Runtime Incompatibility and Socket Dialing Reality**: The study map now accurately details Cloudflare runtime API lock-in (`connect()`, `WebSocketPair`, `request.cf`) and specifies the exact runtime constraints of EdgeOne, Wasmer, Fastly, and Supabase Deno.
4. **Adversarial Discovery on Proposed Deno Socket Blueprint**: While the documentation changes are honest and accurate, deep technical review of the newly added Supabase Deno adapter blueprint revealed three critical engineering flaws (concurrency race on `onmessage`, omission of the 2-byte VLESS server response header, and resource leak on aborted connections). These are logged as binding architectural advisories for Phase S2 implementation.
5. **Zero Em-Dashes and Zero Secret Leaks**: Automated byte-level scans confirm zero em-dashes (`\u2014`), zero en-dashes (`\u2013`), and zero leaked credentials across the entire repository.

Based on complete remediation and honest technical documentation, the final verdict for Phase S1 is **PASS**.

---

## 2. Verification of the 6 Initial Audit Defects

### 2.1 Issue 1: Runtime API Lock-in and Multi-Cloud Socket Differences
- **Initial Defect**: Claimed `_worker.js` was portable across Wasmer, EdgeOne, and Deno without addressing Cloudflare Workers proprietary APIs (`connect()`, `WebSocketPair`, `request.cf`).
- **Remediation Status in v2**: **VERIFIED / PASS**
- **Verification Evidence**:
  - `docs/edgetunnel_porting_map.md` Section 1.1 explicitly defines the architectural boundary: `fastly-edge-speedtest` is a client-side probe and configuration synthesis pipeline, not a monolithic copy of `_worker.js`.
  - Section 2.6 provides an exhaustive multi-cloud runtime compatibility matrix:
    - **Tencent EdgeOne**: Sandbox strictly prohibits raw outbound TCP socket dials; EdgeOne functions exclusively as an Anycast CDN reverse proxy frontend.
    - **Wasmer Edge (WinterJS)**: Lacks `connect()`; requires WASI preview2 socket syscalls (`wasi:sockets`).
    - **Fastly Compute@Edge**: Outbound connections restricted to pre-declared static backends via `fastly:backend`.
    - **Supabase Edge (Deno)**: Requires explicit translation to `Deno.connect` and `Deno.upgradeWebSocket`.
  - Synthesis Table Row 469 explicitly marks server socket adaptation as "Planned for Phase S2/S3 (Blueprint Documented)".

### 2.2 Issue 2: Fabricated PROXYIP Porting Claims in `speedtest.py`
- **Initial Defect**: Claimed `speedtest.py` implemented `/proxyip={egress_ip}` dynamic path injection and DNS TXT DoH resolution with "Complete" status, whereas zero lines of code existed.
- **Remediation Status in v2**: **VERIFIED / PASS**
- **Verification Evidence**:
  - `docs/edgetunnel_porting_map.md` Section 2.3.2 includes an explicit "Honest Technical Disclosure":
    > "In the current Phase S1 implementation of speedtest.py, there is zero dynamic injection of /proxyip={egress_ip} or DoH DNS TXT candidate resolution... Previous claims that PROXYIP injection and DoH resolution were 'Complete' in Phase S1 were factually incorrect."
  - The status has been downgraded to "Planned for Phase S2 and S3 (Not Implemented in Phase S1)".
  - Concrete future blueprints (`inject_proxyip_path` for Phase S2, `resolve_proxyip_doh` for Phase S3) are provided with accurate scoping.

### 2.3 Issue 3: Phantom WebSocket 101 Handshake Code
- **Initial Defect**: Published a fabricated Python code snippet claiming `speedtest.py` lines 595 to 661 executed WebSocket upgrade and validated HTTP 101, when the code actually stopped after TLS wrap.
- **Remediation Status in v2**: **VERIFIED / PASS**
- **Verification Evidence**:
  - `docs/trace_web_porting_map.md` Section 3.2 now faithfully quotes the actual code in `speedtest.py` (lines 613 to 627) and explicitly notes:
    > "The routine terminates immediately after the TLS handshake. It does not send an HTTP GET request, does not request a WebSocket upgrade, and does not check for HTTP 101."
  - The status in Section 2 Matrix is marked: "Full HTTP 101 negotiation over TLS socket. (Status: Pending Rewrite in Phase S3)".
  - A sound pure-Python blueprint `probe_ws101_edge_candidate` is provided strictly as a target design for Phase S3.

### 2.4 Issue 4: Falsified Download Speed Metrics and Formula Repudiation
- **Initial Defect**: Fabricated speed values from latency tiers (`avg_rtt < 60 -> 35.0Mbps`) while claiming to fulfill Trace-Web download benchmarking.
- **Remediation Status in v2**: **VERIFIED / PASS**
- **Verification Evidence**:
  - `docs/trace_web_study.md` Section 4.2 and `docs/trace_web_porting_map.md` Section 3.3 include dedicated sections titled "Repudiation of Static RTT Pseudo-Bandwidth Formulas".
  - The documents explicitly declare:
    > "This formula is an artificial placeholder. RTT reflects propagation delay and does not correlate reliably with available TCP window bandwidth or actual link capacity. In Phase S3, this pseudo-formula must be completely decommissioned and replaced by genuine chunked HTTP download benchmarking."
  - The status in the component matrix is marked: "Status: Planned for Phase S3, static pseudo-formula repudiated".
  - A real chunked payload download blueprint (`measure_download_throughput`) is defined for Phase S3.

### 2.5 Issue 5: Carrier Route Classification vs Post-Tunnel Egress Lookup
- **Initial Defect**: Conflated post-tunnel exit IP lookups (`ip-api.com`) with client-to-edge domestic hop tracerouting (`nexttrace`), claiming pure Python route classification.
- **Remediation Status in v2**: **VERIFIED / PASS**
- **Verification Evidence**:
  - `docs/trace_web_study.md` Section 3.2 establishes the critical technical distinction:
    1. Domestic Transit Carrier Route Inspection requires hop-by-hop tracerouting (ICMP/UDP with incremental TTLs) originating inside China to classify AS4809 (CN2 GIA), AS9929 (CU Premium), and AS58453 (CMIN2).
    2. Post-Tunnel Egress Lookup verifies only upstream exit datacenter ASN and landing country, which cannot inspect the domestic transit link.
  - Documents acknowledge that Phase S1 relies on post-tunnel egress checking and latency heuristics, with true transit tracerouting designated for future domestic runner deployment.

### 2.6 Issue 6: Unacknowledged External Binary Dependency on Mihomo
- **Initial Defect**: Claimed "Zero External Binary Dependencies" while `geo_gate_verify.py` strictly required `verge-mihomo.exe`.
- **Remediation Status in v2**: **VERIFIED / PASS**
- **Verification Evidence**:
  - `docs/trace_web_study.md` Section 1.2 and `docs/trace_web_porting_map.md` Section 1 replace the zero-dependency claim with "Decoupled Binary Execution Boundary".
  - The dependency on `verge-mihomo.exe` (or Linux `mihomo`) is prominently declared.
  - Section 3.5 provides full operational documentation of the ephemeral sandbox (`sandbox_geogate`) and its allocated high-range loopback ports (39950 to 39953).

---

## 3. Adversarial Deep-Dive: Socket Adapter and Probing Blueprints

As part of TaskCard `S1-redteam-02`, the Adversarial Red Team conducted an in-depth code audit of the blueprints proposed for future phases.

### 3.1 Review of Supabase Deno WebSocket/TCP Adapter Blueprint (`edgetunnel_porting_map.md` L379-447)

While the blueprint correctly identifies `Deno.upgradeWebSocket` and `Deno.connect` as the required APIs, our analysis identified three critical vulnerabilities and protocol omissions that would cause failures in production:

#### Flaw 1: Asynchronous Concurrency Race on `socket.onmessage`
In the blueprint:
```typescript
let tcpConn: Deno.TcpConn | null = null;
socket.onmessage = async (event) => {
    // ...
    if (!tcpConn) {
        // ...
        tcpConn = await Deno.connect({ hostname: parsed.hostname, port: parsed.port });
        // ...
    } else {
        await tcpConn.write(rawData);
    }
};
```
- **Hazard**: `socket.onmessage` is an async event callback. While `await Deno.connect(...)` is in flight (taking 50ms to 300ms of network I/O), subsequent incoming WebSocket frames trigger `onmessage` concurrently.
- Because `tcpConn` remains `null` until `Deno.connect` resolves, subsequent data frames enter the `if (!tcpConn)` branch.
- This causes the handler to attempt `parseVlessHeader(rawData)` on arbitrary data payloads, which triggers an immediate `socket.close(1008, "Unauthorized")` or attempts duplicate TCP connections!
- **Mandatory Fix for Phase S2**: The adapter must maintain an explicit connection state (`connecting = true`) and a FIFO packet queue (`pendingQueue: Uint8Array[]`) to buffer incoming frames until `Deno.connect` resolves.

#### Flaw 2: Omission of Mandatory VLESS Server Response Header
- **Hazard**: According to the VLESS protocol specification (and `_worker.js` lines 1770 to 1775), upon validating the client VLESS request, the server MUST send a 2-byte response header back to the client over WebSocket before forwarding any remote TCP data:
  - Byte 0: Protocol version (matching request version, typically `0x00`).
  - Byte 1: Addons length (`0x00`).
- The blueprint omits this header completely, directly piping raw TCP data:
  ```typescript
  socket.send(buf.subarray(0, n));
  ```
- **Consequence**: When the target server sends initial data (such as TLS `ServerHello` or HTTP response bytes), the client proxy (Clash Meta, Mihomo, Sing-box) interprets the first two bytes as the VLESS response header. This triggers immediate protocol decoding failure and connection teardown.
- **Mandatory Fix for Phase S2**: The server must invoke `socket.send(new Uint8Array([parsed.version, 0]))` immediately after `Deno.connect` succeeds and before entering the TCP read loop.

#### Flaw 3: Dangling Connection Leak on Premature Socket Teardown
- **Hazard**: If the client closes the WebSocket (`socket.onclose`) while `await Deno.connect(...)` is still awaiting, `socket.onclose` finds `tcpConn === null` and does nothing. When `Deno.connect` subsequently resolves, `tcpConn` is opened but never closed, leaking TCP sockets and memory.
- In addition, `await Deno.connect` lacks a `try...catch` wrapper. Any connection refusal or DNS failure results in an unhandled promise rejection, leaving the WebSocket hanging.
- **Mandatory Fix for Phase S2**: Wrap `Deno.connect` in `try...catch` with `socket.close(1011, "Connect failed")` on error, and maintain a `closed` boolean flag checked immediately after `await Deno.connect`.

---

## 4. Security, Credentials, and Formatting Inspection

### 4.1 Em-Dash and En-Dash Compliance
- A byte-level search across the entire project directory (`fastly-edge-speedtest`) was executed targeting UTF-8 encodings `\xe2\x80\x94` (`\u2014`, em-dash) and `\xe2\x80\x93` (`\u2013`, en-dash).
- **Result**: Exactly **0** em-dashes and **0** en-dashes found. Full compliance verified.

### 4.2 Credential and Secret Leak Audit
- An automated regex audit was executed scanning for unmasked API tokens, AWS access keys (`AKIA...`), GitHub PATs (`ghp_...`), private cryptographic keys, and administrative secrets.
- **Result**: Exactly **0** leaked credentials found. All tokens in use are either documented public test UUIDs (`c69d9310-66db-4614-b3b7-0fb01e68b4ec`) or standard sample nonces.

---

## 5. Comprehensive Red Team Evaluation Matrix

| Audit Item | Task Requirement | Verification Finding | Verdict |
| :--- | :--- | :--- | :--- |
| **Issue 1: Runtime API Lock-in** | Verify multi-cloud socket differences documented | Explicitly details EdgeOne, Wasmer, Fastly, and Deno constraints | **PASS** |
| **Issue 2: PROXYIP Claims** | Remove fake completion claims; accurate status | Explicitly downgraded to Planned for Phase S2/S3 with honest disclosure | **PASS** |
| **Issue 3: WS 101 Probing** | Remove non-existent code; present real code | Quotes real code, downgrades status to Phase S3 blueprint | **PASS** |
| **Issue 4: Speed Formula** | Repudiate static RTT pseudo-formula | Formally repudiated as artificial placeholder; HTTP download blueprint provided | **PASS** |
| **Issue 5: Route Classification** | Distinguish domestic transit vs egress lookup | Clearly separated hop-by-hop transit from post-tunnel egress ASN | **PASS** |
| **Issue 6: Binary Dependency** | Declare Mihomo executable requirement | Explicitly declared Mihomo requirement and documented sandbox port ranges | **PASS** |
| **Deno Socket Blueprint** | Audit proposed adapter for logic/protocol flaws | Found 3 flaws (race condition, missing VLESS response header, connection leak) | **ADVISORY LOGGED** |
| **Formatting Integrity** | Zero em-dashes (`\u2014`) in codebase and docs | 0 occurrences verified by byte-level scanning | **PASS** |
| **Secret Protection** | Zero committed credentials or private keys | 0 leaks detected | **PASS** |

---

## 6. Final Conclusion and Phase Sign-Off

The study subagent has demonstrated exemplary engineering integrity in responding to the initial adversarial audit:
- Every fabricated claim has been retracted and replaced with honest disclosures.
- Every architectural boundary between client-side probing, server-side execution, and external binary dependencies has been clearly delineated.
- The research artifacts now constitute a rigorous, verifiable baseline for implementation.

The three architectural advisories regarding the Supabase Deno adapter blueprint must be treated as mandatory requirements when entering Phase S2.

**Final Phase S1 Adversarial Verdict**: **PASS**
