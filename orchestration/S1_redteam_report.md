# S1 Adversarial Red Team Audit Report: Study and Porting Verification

- **TaskCard**: `S1-redteam-01.md`
- **Auditor**: Adversarial Red Team Subagent
- **Target Repository**: `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest`
- **Execution Date**: 2026-09-20
- **Final Verdict**: **FAIL**

---

## 1. Executive Summary and Verdict

An adversarial audit was conducted on the architectural and porting research artifacts in `docs/`:
1. `docs/edgetunnel_porting_map.md`
2. `docs/trace_web_study.md`
3. `docs/trace_web_porting_map.md`

While the Code Auditor verified citation accuracy against reference repositories, the Adversarial Red Team challenged the technical veracity, runtime feasibility, and actual implementation status of the claimed ports.

The audit has uncovered multiple critical architectural failures, ungrounded runtime assumptions, fabricated implementation claims, and simulated metrics:
- **Cloudflare Runtime Lock-in**: Cloudflare Workers proprietary APIs (`connect()`, `WebSocketPair`, `request.cf`) are treated as universally portable to Wasmer and EdgeOne without providing any server-side runtime socket adaptation.
- **Fabricated Implementation Claims**: `edgetunnel_porting_map.md` claims that `speedtest.py` implements `/proxyip={egress_ip}` dynamic path injection and DNS TXT DoH candidate resolution (Table rows 321 to 323). In reality, `speedtest.py` contains zero lines of PROXYIP or DoH resolution code.
- **Phantom WebSocket 101 Handshake Code**: `trace_web_porting_map.md` Section 3.2 presents Python code claiming that `speedtest.py` sends `Upgrade: websocket` and validates `101 Switching Protocols`. In reality, `speedtest.py` performs only raw TCP and TLS handshakes, completely omitting WebSocket negotiation.
- **Faked Download Throughput**: Rather than measuring actual download speed as Trace-Web does, `speedtest.py` fabricates speed values using a static formula based on RTT (`avg_rtt < 60 -> "35.0Mbps"`).
- **Contradiction on External Binary Dependencies**: `trace_web_porting_map.md` claims "Zero External Binary Dependencies", yet `geo_gate_verify.py` strictly mandates the closed-source external binary `verge-mihomo.exe`.
- **Carrier Route Tracing Fallacy**: The porting document conflates post-tunnel exit IP lookups (`ip-api.com`) with client-to-edge domestic hop traceroutes (`nexttrace`), eliminating genuine inbound carrier classification.

Due to these critical defects and unsubstantiated claims, the audit verdict is **FAIL**.

---

## 2. In-Depth Adversarial Findings

### 2.1 Finding 1: Fatal Runtime Incompatibility on Wasmer, EdgeOne, and Deno (Cloudflare API Lock-in)

- **Source Reference**: `_worker.js` Lines 3331 to 3334, Lines 43 to 48, Lines 67 to 70.
- **Porting Document Claims**: `docs/edgetunnel_porting_map.md` Section 1, Section 2.2.2, Section 3.
- **Adversarial Analysis**:
  In `_worker.js`, all outbound network communication relies exclusively on Cloudflare Workers proprietary APIs:
  ```javascript
  // _worker.js Lines 3331-3333
  function 创建TCP连接(request) {
      const fetcher = request?.fetcher;
      if (!fetcher || typeof fetcher.connect !== 'function') throw new Error('request.fetcher.connect unavailable');
      return (options, init) => fetcher.connect(options, init);
  }
  ```
  Inbound WebSocket termination relies on Cloudflare-specific `WebSocketPair` and `response.webSocket.accept()`. Datacenter routing relies on Cloudflare-specific metadata `request.cf.colo`.

  `docs/edgetunnel_porting_map.md` claims this architecture is ported across Wasmer, EdgeOne, Fastly, Netlify, and Supabase.
  This claim collapses under technical scrutiny:
  1. **Tencent EdgeOne**: EdgeOne edge functions run in a restricted JavaScript environment that does not expose raw outbound TCP socket dialing APIs (such as `connect()`). EdgeOne serves primarily as a CDN and reverse proxy.
  2. **Wasmer Edge**: Wasmer executes WebAssembly / WinterJS workloads. It does not provide `request.fetcher.connect()` nor `WebSocketPair`.
  3. **Fastly Compute@Edge**: Fastly uses Viceroy / Wasmtime with `fastly:backend` and strictly requires pre-declared backends. It does not permit arbitrary TCP socket dials via Cloudflare APIs.
  4. **Supabase Edge Functions**: Supabase runs on Deno. Deno requires `Deno.connect({ hostname, port })` for raw TCP sockets and `Deno.upgradeWebSocket(request)` for WebSockets. Neither `WebSocketPair` nor `request.cf` exists.

  `docs/edgetunnel_porting_map.md` completely evades the server-side runtime porting reality. It points solely to client-side Clash configuration generation (`speedtest.py`), misleading developers into believing that `_worker.js` runs unmodified on these heterogeneous edge runtimes.

---

### 2.2 Finding 2: Fabricated PROXYIP Porting Claims in `speedtest.py`

- **Porting Document Claims**: `docs/edgetunnel_porting_map.md` Section 2.3.2 (Lines 208 to 213) and Synthesis Table (Lines 321 to 323).
  - Claim 1: "In `speedtest.py`, when routing edge traffic through designated regional proxy egresses, the node path can dynamically inject `/proxyip={egress_ip}` into the WebSocket URL, forcing the edge worker to egress through specific regional nodes."
  - Claim 2: `PROXYIP Env & Selection` ported to `speedtest.py multi-region backend routing` (Status: Complete).
  - Claim 3: `PROXYIP Query & Path` ported to `speedtest.py URL generation with regional proxy parameters` (Status: Complete).
  - Claim 4: `PROXYIP DNS TXT Resolve` ported to `speedtest.py candidate resolution` (Status: Complete).
- **Adversarial Verification in Codebase**:
  A global text and regular expression search for `proxyip` across the entire codebase yields zero occurrences in `speedtest.py`, `generate_all_pools.py`, or `generate_edgeone_pool.py`.
  In `speedtest.py`:
  - Node subscription paths are configured as:
    `ws-opts.path: /functions/v1/edgetunnel?forceFunctionRegion=ap-northeast-1`
  - There is zero dynamic injection of `/proxyip={egress_ip}` or `?proxyip=...`.
  - There is zero implementation of DNS TXT DoH parsing (`解析地址端口`).
  Marking these features as "Complete" in the porting map is an absolute fabrication.

---

### 2.3 Finding 3: Phantom WebSocket 101 Handshake Verification Code

- **Porting Document Claims**: `docs/trace_web_porting_map.md` Section 3.2 (Lines 91 to 106).
  The document details the following implementation:
  ```python
  # docs/trace_web_porting_map.md Lines 93-106
  req = (
      f"GET /?ed=2560 HTTP/1.1\r\n"
      f"Host: {sni_host}\r\n"
      f"Upgrade: websocket\r\n"
      f"Connection: Upgrade\r\n"
      f"Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
      f"Sec-WebSocket-Version: 13\r\n\r\n"
  )
  tls_sock.sendall(req.encode())
  resp = tls_sock.recv(4096).decode("utf-8", errors="ignore")
  if "101" not in resp:
      return None  # Disqualified: Failed WebSocket negotiation
  ```
  The document asserts that this code resides in `speedtest.py` `benchmark_single_edgeone_candidate` (Lines 595 to 661).
- **Adversarial Verification in Codebase**:
  Direct inspection of `speedtest.py` lines 613 to 630 reveals:
  ```python
  # speedtest.py Lines 613-630
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.settimeout(0.6)
  s.connect((host, port))

  ctx = ssl.create_default_context()
  ctx.check_hostname = False
  ctx.verify_mode = ssl.CERT_NONE
  with ctx.wrap_socket(s, server_hostname=EDGEONE_SNI) as ss:
      t1 = time.perf_counter()
      rtt = (t1 - t0) * 1000.0
      latencies.append(rtt)
  ```
  The function terminates immediately after the TLS handshake. It never transmits an HTTP GET request, never requests a WebSocket upgrade, and never validates HTTP 101 status. The code published in the study document is non-existent in the target repository.

---

### 2.4 Finding 4: Falsified Download Speed Metrics in `speedtest.py`

- **Porting Document Claims**: `docs/trace_web_study.md` Section 4 & 5.1, `docs/trace_web_porting_map.md` Section 2 (Row 25) and Section 3.
  Both documents reference Trace-Web's Stage 3 download benchmarking (`下载速度` in MB/s via payload download).
- **Adversarial Verification in Codebase**:
  In `speedtest.py` lines 642 to 650:
  ```python
  if avg_rtt < 60:
      spd = "35.0Mbps"
  elif avg_rtt < 90:
      spd = "28.0Mbps"
  elif avg_rtt < 150:
      spd = "22.0Mbps"
  else:
      spd = "18.0Mbps"
  ```
  In `PROVEN_DOMESTIC_BENCHMARKS` (Lines 145 to 203), speeds are hardcoded strings (`"28.5Mbps"`, `"25.0Mbps"`).
  The system performs no actual data transfer to measure throughput. Speed metrics are simulated from latency buckets. Claiming this fulfills Trace-Web's download benchmarking is deceptive.

---

### 2.5 Finding 5: Carrier Route Classification Fallacy

- **Porting Document Claims**: `docs/trace_web_porting_map.md` Section 3.4.
  The document claims to port Trace-Web's `nexttrace` route classification (AS4809 CN2 GIA, AS9929 CU Premium, AS58453 CMIN2) into pure Python via:
  1. Post-tunnel egress IP lookups (`ip-api.com`).
  2. Inbound latency tiers (<90ms for Asian routes).
- **Adversarial Technical Challenge**:
  1. **Egress vs Ingress Route**: The egress IP resolved through the proxy tunnel identifies only the exit datacenter (e.g. AWS Tokyo AS16509). It reveals zero information regarding whether the domestic transit network from China to the edge frontend traversed CN2 GIA, AS9929, or congested 163 backbone.
  2. **Latency Heuristic Failure**: Sub-90ms latency to Hong Kong or Tokyo can easily occur over standard transit (AS4134 or CMI) during off-peak periods, yet experience severe packet loss and jitter during peak hours. Conflating latency thresholds with hop-by-hop BGP AS route inspection is a technical flaw.

---

### 2.6 Finding 6: Unacknowledged External Binary Dependency on Mihomo

- **Porting Document Claims**: `docs/trace_web_porting_map.md` Section 1:
  "1. Zero External Binary Dependencies: All networking, handshake measurement, subnet expansion, and route auditing logic is implemented purely in Python standard libraries (`socket`, `ssl`, `urllib.request`, `concurrent.futures`, `json`, `ipaddress`). No external `.exe` or raw ICMP kernel privileges are required."
- **Adversarial Verification in Codebase**:
  In `geo_gate_verify.py` lines 93 to 99:
  ```python
  mihomo_bin = r"C:\Program Files\Clash Verge\verge-mihomo.exe"
  if not os.path.exists(mihomo_bin):
      mihomo_bin = "mihomo"
  proc = subprocess.Popen([mihomo_bin, "-d", sandbox_dir, "-f", cfg_file], ...)
  ```
  The entire pre-publish verification gate (`geo_gate_verify.py`) fails if `verge-mihomo.exe` is absent. Claiming "Zero External Binary Dependencies" while depending on a local Clash Verge installation is a direct contradiction.

---

### 2.7 Finding 7: Static Candidate Illusion and Hardcoded Winners

- **Porting Document Claims**: `speedtest.py` header notes claim testing 1500+ endpoints with dynamic optimization.
- **Adversarial Verification in Codebase**:
  In `speedtest.py` lines 205 to 256:
  `generate_broad_candidate_pool` merely returns `PROVEN_DOMESTIC_BENCHMARKS`, which contains only 28 static hardcoded entries. `benchmark_and_select_top_nodes` performs no network I/O; it simply sorts this static dictionary.
  In `benchmark_edgeone_nodes` lines 708 to 730, if live probes fail, the script injects synthetic fallback IPs with hardcoded latency values (`162.14.128.21`, 58.8ms). The claim of continuous dynamic multi-thousand endpoint optimization is largely illusory in the default execution flow.

---

### 2.8 Finding 8: Em-Dashes and Credential Inspection

- **Em-Dashes**: Systematic unicode analysis across all `.md`, `.py`, `.json`, and `.yaml` files confirms **zero em-dashes (`\u2014`)** and **zero en-dashes (`\u2013`)**.
- **Credential Leakage**: No plaintext administrative passwords, private signing keys, or cloud access tokens (AWS AKIA, GitHub PAT, etc.) are committed. All identifiers represent UUID v4 tokens or public test endpoints.

---

## 3. Comprehensive Red Team Evaluation Matrix

| Audit Dimension | Requirement / Target | Current Reality in Artifacts & Code | Red Team Assessment |
| :--- | :--- | :--- | :--- |
| **Trace-Web Binary Absence** | Acknowledge missing Go binaries | Accurately identified missing `main.exe` and `nexttrace-core.exe` | **PASS** |
| **Python Network Replacement** | Sound pure Python networking | Simulated download speed; statistical insignificance with N=2 probes | **FAIL** |
| **Carrier Route Auditing** | Inbound carrier transit validation | Relies on exit IP lookup + latency heuristic; cannot detect transit AS | **FAIL** |
| **External Binary Boundary** | Claimed "Zero External Binary Dependencies" | Mandates `verge-mihomo.exe` for sandbox verification gate | **FAIL** |
| **edgetunnel Runtime Mapping** | Realistic multi-runtime adaptation | Blindly maps Cloudflare `connect()` to Wasmer/EdgeOne without adapter | **FAIL** |
| **PROXYIP Implementation** | Porting of dynamic PROXYIP & DNS TXT | Claimed "Complete" in map, but zero lines of code in `speedtest.py` | **FAIL** |
| **WebSocket 101 Verification** | Live WS handshake probing | Code cited in porting map does not exist in `speedtest.py` | **FAIL** |
| **Purity of Formatting** | Zero em-dashes (`\u2014`) | Exactly 0 em-dashes found across entire repository | **PASS** |
| **Secret Leakage Prevention** | Zero committed credentials/secrets | No private keys or administrative secrets committed | **PASS** |

---

## 4. Remediation Requirements

Before Phase S1 can be considered verified and eligible for a PASS verdict, the following actions must be executed:

1. **Correct Porting Documentation**:
   - Downgrade the porting status of PROXYIP path injection and DNS TXT resolution from "Complete" to "Not Implemented / Conceptual Only" in `docs/edgetunnel_porting_map.md`.
   - Remove fictional code blocks from `docs/trace_web_porting_map.md` Section 3.2, or genuinely implement HTTP 101 WebSocket negotiation in `speedtest.py`.
2. **Explicit Runtime Adaptation Clarification**:
   - Add an explicit runtime compatibility section in `docs/edgetunnel_porting_map.md` documenting that `_worker.js` cannot run directly on Wasmer or EdgeOne due to lack of `connect()` / `cloudflare:sockets` support.
   - Clarify that `fastly-edge-speedtest` is a client-side probe and configuration synthesizer, not a server-side edge runtime implementation.
3. **Honest Metric Transparency**:
   - Explicitly document in `trace_web_porting_map.md` that download throughput is estimated from RTT rather than measured via live chunk transfers.
   - Acknowledge that carrier route classification relies on an ingress latency heuristic combined with egress datacenter ASN verification rather than hop-by-hop tracerouting.
4. **Binary Dependency Declaration**:
   - Update `trace_web_porting_map.md` to accurately state that `geo_gate_verify.py` requires an external Mihomo executable for sandbox egress verification.
