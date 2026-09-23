# TaskCard S3-speed-01: Stage S3 Genuine Speedtest Engine Rewrite

## Target
Target Project: `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest`
Executor: `speed` subagent
Verification Gates: Unanimous PASS from both `audit-code` and `redteam`

---

## 1. Objectives & Ground Rules

Eradicate all mock data, fake latency tables, and simulated traffic from `speedtest.py`. Build a genuine, two-stage network measurement engine that performs physical socket connections, TLS handshakes, RFC 6455 WebSocket handshakes, and 3-round latency measurements.

### Strict Red Lines
1. ZERO hardcoded latency tables: `PROVEN_DOMESTIC_BENCHMARKS` must be completely deleted.
2. ZERO progressive traffic simulation or fabricated numbers.
3. ZERO em-dashes (`\u2014`) and ZERO en-dashes (`\u2013`).
4. ZERO interference with host Clash/Mihomo or system network adapters (local port 7897 must remain untouched).
5. 100% Free tier compatible.

---

## 2. Technical Specification

### Stage 1: Handshake Verification (Physical Probes)
- **TCP Socket RTT**:
  Measure elapsed time of `socket.create_connection((server, port), timeout=3.0)`.
  Record exact floating-point milliseconds (`tcp_rtt_ms`).
- **TLS Handshake RTT**:
  Wrap socket with `ssl.create_default_context()`, configuring SNI via `server_hostname=sni`.
  Measure TLS handshake duration in milliseconds (`tls_rtt_ms`).
- **RFC 6455 WebSocket Upgrade 101**:
  Construct RFC 6455 upgrade request:
  ```http
  GET {path} HTTP/1.1\r\n
  Host: {sni}\r\n
  Upgrade: websocket\r\n
  Connection: Upgrade\r\n
  Sec-WebSocket-Key: {base64_key}\r\n
  Sec-WebSocket-Version: 13\r\n\r\n
  ```
  Inspect response status line. If response contains `101`, `ws_101_ok = True`. If response is 200, 404, or 403 (camouflage), record HTTP status code.

### Stage 2: End-to-End Latency & Packet Loss
- Perform 3 sequential rounds of RTT measurement for verified nodes.
- Record `rtt_round_1`, `rtt_round_2`, `rtt_round_3`.
- Compute `median_rtt_ms` (median of successful rounds; -1 if all failed).
- Compute `packet_loss`: ratio of timed-out rounds (0.0, 0.33, 0.67, or 1.0).

### Stage 3: Structured Metric Persistence
- Results must be appended to `results/YYYY-MM-DD.jsonl.gz`.
- Ensure directory `results/` is created if not present.
- Each record must include:
  - `node_name`
  - `server`
  - `port`
  - `sni`
  - `path`
  - `tcp_rtt_ms`
  - `tls_rtt_ms`
  - `ws_101_ok`
  - `rtt_round_1`
  - `rtt_round_2`
  - `rtt_round_3`
  - `median_rtt_ms`
  - `packet_loss`
  - `timestamp` (ISO 8601 UTC)

### Stage 4: Workflow Integration
- Update `recheck_published.py` if necessary so `edgeone-published-recheck.yml` (every 4h) uses the genuine physical handshake engine against active published nodes in the 6 subscriptions.
- Ensure `edgeone-full-sweep.yml` (daily) invokes the full candidate sweep and generates ranked YAMLs without using any mock data.

---

## 3. Deliverables & Verification
- Updated `speedtest.py` and `recheck_published.py`.
- Verified generation of `results/YYYY-MM-DD.jsonl.gz` with real network measurements.
- Write full report to `orchestration/S3_speed_report.md`.
