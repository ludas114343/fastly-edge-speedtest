# Architecture and Mechanics Study: Trace-Web

## 1. Executive Summary and Binary Boundary Assessment

### 1.1 Source Code Inventory and Execution Boundary
This study provides an exhaustive analysis of `Trace-Web` based directly on the reference repository located at:
`C:\Users\ludas\.gemini\antigravity\scratch\ref_projects\Trace-Web\trace.py` (Version `1.0.0`, 1230 lines of Python).

An inspection of the file system of `Trace-Web` reveals the following structure:
- `trace.py` (50,809 bytes)
- `README.md` (4,059 bytes)
- `LICENSE` (1,085 bytes)
- `.git` directory

**Critical Boundary Finding**:
The repository contains only the Python frontend script (`trace.py`) and documentation. It **does not contain** the precompiled Go backend (`backend/main.exe`) nor the traceroute binary (`backend/nexttrace-core.exe` or `backend/nexttrace.exe`).

In `trace.py` lines 88 to 120, the script enforces mandatory pre-flight checks:
```python
_BACKEND_CANDIDATES = (
    PROJECT_ROOT / "backend" / "main.exe",
)
_NEXTTRACE_CANDIDATES = (
    PROJECT_ROOT / "backend" / "nexttrace-core.exe",
    PROJECT_ROOT / "backend" / "nexttrace.exe",
)

def ensure_backend_available() -> None:
    """Check whether backend and nexttrace-core exist before launching."""
    if not os.path.isfile(BACKEND_EXECUTABLE):
        _fail("backend/main.exe not found. Please build backend: "
              "cd backend && go build -o main.exe .")
    if not os.path.isfile(NEXTTRACE_EXECUTABLE):
        _fail("nexttrace-core.exe / nexttrace.exe not found in backend directory.")
```
Both `cli_main` (Line 570) and `web_main` (Line 840) call `ensure_backend_available()`. Without the external Go binary, `trace.py` immediately exits with code 1. Therefore, `trace.py` serves strictly as a process supervisor, IPC translator, CLI parser, and Web/SSE user interface.

### 1.2 Binary Dependency Boundary in fastly-edge-speedtest
To address the missing Go backend while keeping the system production-grade, `fastly-edge-speedtest` divides the pipeline into two decoupled tiers:
1. **Candidate Scanning and TCP/TLS Probing Tier (`speedtest.py`)**:
   Implemented with standard Python networking libraries (`socket`, `ssl`, `urllib.request`, `concurrent.futures`, `ipaddress`). Requires zero external binaries or root permissions.
2. **End-to-End Proxy Verification Gate Tier (`geo_gate_verify.py`)**:
   Requires an external portable Mihomo binary (`verge-mihomo.exe` on Windows or `mihomo` executable on Linux). This binary runs inside an ephemeral, non-invasive sandbox (`sandbox_geogate`) on dedicated high-range loopback ports (39950 to 39953). It is completely isolated from host proxy configurations, system network adapters, and user applications.

---

## 2. Candidate IP Formats and Input Ingestion Pipeline

### 2.1 Supported Token Grammar and Regex Definitions
In `trace.py`, target parsing and normalization are handled in lines 126 to 220:

1. **Regular Expressions**:
   - Dotted IPv4: `_IPV4_RE = re.compile(r"(?:\d{1,3}\.){3}\d{1,3}")` (Line 126)
   - CIDR Notation: `_CIDR_RE = re.compile(r"(?:\d{1,3}(?:\.\d{1,3}){3}|[0-9A-Fa-f:]+)/\d{1,3}")` (Line 128)
   - IP Range: `_RANGE_RE = re.compile(r"(?:\d{1,3}(?:\.\d{1,3}){3}|[0-9A-Fa-f:]+)\s*-\s*(?:\d{1,3}(?:\.\d{1,3}){3}|[0-9A-Fa-f:]+)")` (Line 129)
   - General Target Token:
     ```python
     _TARGET_TOKEN_RE = re.compile(
         r"\[[0-9A-Fa-f:.]+\](?::\d+)?"
         r"|(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?"
         r"|[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
         r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])*)+(?::\d+)?"
     )
     ```
     (Lines 130 to 134)
   - Bare IPv6: `_BARE_IPV6_RE = re.compile(r"[0-9A-Fa-f:]+")` (Line 135)

2. **Accepted Target Formats**:
   - `1.0.0.1` (IPv4 without port)
   - `1.0.0.1:443` (IPv4 with explicit port)
   - `[2606:4700::1]` (Bracketed IPv6 without port)
   - `[2606:4700::1]:443` (Bracketed IPv6 with explicit port)
   - `2606:4700::1` (Bare IPv6 without port)
   - `2606:4700::1:443` (Bare IPv6 with port: parsed via `content.rpartition(":")` if the last component is 1 to 5 digits, Lines 190 to 199)
   - `example.com` / `example.com:443` (Domain with optional port)
   - `1.0.0.0/24` / `2606:4700::/48` (CIDR blocks: permitted exclusively in online optimization mode, Line 216)
   - `1.0.0.0 - 1.0.0.255` (IP ranges: permitted exclusively in online optimization mode, Line 216)

### 2.2 Ingestion, Sanitization, and Validation Logic
- **Comment Stripping and Whitespace Enforcement**:
  Line 179 strips comments: `content = raw_line.split("#", 1)[0].strip()`.
  Line 182 rejects embedded whitespace: `if re.search(r"\s", content): _raise_target(...)`.
- **Target Token Validation**:
  `_validate_target_token(token, line_number)` (Lines 142 to 171) enforces:
  - Bracket closure and trailing colon for port (`[IPv6]:port`).
  - Strict port range integer validation: `1 <= int(port) <= 65535`.
  - IPv4 octet value validation via `ipaddress.ip_address(host)`.

### 2.3 Subnet Expansion and Scale Limits
- **Scale Ceiling**:
  Line 72 defines strict task quotas:
  ```python
  TARGET_LIMITS = {TASK_TRACE: 300, TASK_OPTIMIZE: 100_000}
  ```
  - For `TASK_TRACE` (`line`): Maximum 300 targets. Lines 285 to 288 silently truncate inputs exceeding 300 items (`tokens = tokens[:limit]`).
  - For `TASK_OPTIMIZE` (`optimize`): Maximum 100,000 expanded addresses. Exceeding this triggers a hard `ValueError`.
- **Merge-Spans Estimation Algorithm**:
  `estimate_expand_count(tokens, limit)` (Lines 221 to 275) parses CIDRs and IP ranges into integer numeric tuples `(start_int, end_int)`:
  - Lines 227 to 240 define `merge_spans(spans)`: sorts interval tuples and merges overlapping or contiguous address spans (`start <= cur_end + 1`) to ensure accurate pre-expansion deduplication.
  - Enforces `count <= limit` and `total <= limit` before writing input files.

### 2.4 Input Pipelines
- **CLI Pipeline**: `read_targets(path, task)` (Lines 291 to 304) opens files with `utf-8-sig` encoding (stripping UTF-8 BOM headers commonly added by Windows Notepad).
- **Web Pipeline**: `validate_targets(task, values)` (Lines 307 to 317) sanitizes arrays posted to `/api/jobs`.
- **IPC Serialization**: `temporary_input_file(targets)` (Lines 347 to 356) creates a temporary file containing JSON Lines:
  ```json
  {"token": "1.0.0.1:443"}
  {"token": "104.16.0.0/24"}
  ```
  and passes this path to the backend via `-i <path> -input-json=true`.

---

## 3. Route Classification and NextTrace Integration

### 3.1 Subprocess IPC Architecture
In `TraceBackend` (Lines 367 to 435):
- For line tracing:
  ```python
  BACKEND_EXECUTABLE, "-nexttrace", "-i", input_path, "-input-json=true",
  "-r", str(options.worker), "-max-hops", str(options.max_hops)
  ```
  (Lines 376 to 379)
- Defaults: Concurrency `worker = 15` (Line 63), `max_hops = 12` (Line 64).
- Stream Handling: Stderr is consumed by a daemon thread `drain_stderr` (Line 413) to capture crash diagnostics. Stdout is decoded line-by-line via `_decode_backend_output` (Lines 359 to 365), attempting UTF-8 first with a fallback to `gb18030`.

### 3.2 Domestic Transit Carrier Routing vs Egress Lookup: Critical Distinction

A foundational distinction must be maintained between inbound transit carrier routing and post-tunnel egress lookup:

1. **Inbound Domestic Transit Carrier Route Inspection (Traceroute / NextTrace)**:
   - Measures the network hops traversed by traffic exiting domestic ISP networks (China Telecom, China Unicom, China Mobile) to reach edge Anycast frontends.
   - Identifies high-priority transit backbones:
     - China Telecom: AS4809 (CN2 GIA) vs AS4134 (163 Backbone)
     - China Unicom: AS9929 (CU Premium / A-Net) vs AS4837 (169 Backbone)
     - China Mobile: AS58453 (CMIN2) vs AS9808 (CMI)
   - Inspecting these paths requires active hop-by-hop tracerouting (via ICMP/UDP with incremental TTLs) originating from within mainland China.

2. **Post-Tunnel Egress Lookup (Tunnel Landing Verification)**:
   - Measures the exit IP and ASN observed by upstream servers when traffic exits the proxy tunnel (e.g. AWS Tokyo AS16509, Cloudflare Hong Kong AS13335).
   - Validates that the node does not suffer from cross-ocean double detour (for example, an Asian node landing in US West).
   - **Critical Limitation**: Egress lookup reveals nothing about the domestic transit carrier network. A node can land cleanly in Tokyo while the domestic leg travels over an unoptimized, congested 163 backbone link.

3. **fastly-edge-speedtest Multi-Phase Strategy**:
   - Phase S1 Reality: Verifies exit country and landing ASN via `geo_gate_verify.py` (`ip-api.com` query through tunnel), while using domestic latency threshold heuristics (<90ms for East Asia) to filter out Pacific round-trips.
   - Future Phase Roadmap: Deployment of dedicated traceroute probes on domestic runner infrastructure to measure true hop-by-hop transit carriers directly.

---

## 4. Comprehensive Metric System

In online optimization mode, Trace-Web evaluates nodes across a multi-dimensional metric vector defined by `OPTIMIZE_HEADERS` (Lines 77 to 81):

```python
OPTIMIZE_HEADERS = [
    "IP地址", "端口号", "TLS", "HTTP", "丢包率", "网络延迟", "下载速度",
    "出站IP", "IP类型", "数据中心", "源IP位置", "地区", "城市",
    "ASN号码", "ASN组织", "ProxyIP", "风险等级",
]
```

### 4.1 Detailed Breakdown of Individual Metrics
1. **IP地址 (IP Address)**: Formatted via `format_ip_for_display` (Lines 440 to 448). IPv6 addresses are enclosed in brackets (e.g. `[2606:4700::1]`).
2. **端口号 (Port Number)**: Edge listening port (e.g. 443, 8443, 2053, 80).
3. **TLS (TLS Status)**: Boolean or string indicator of successful TLS 1.2/1.3 handshake negotiation.
4. **HTTP (HTTP Status)**: HTTP status code returned upon probing the root or speedtest path (e.g. 200, 204, 101).
5. **丢包率 (Packet Loss Rate)**: Percentage of lost packets during handshake probes (0% to 100%).
6. **网络延迟 (Network Latency)**: Handshake RTT in milliseconds. Filtered at the CLI/API level by `-latency-min` (default 0ms) and `-latency-max` (default 999ms) (Lines 336 to 337, 386 to 387).
7. **下载速度 (Download Speed)**: Throughput in MB/s. Controlled by `--download-speed` (Line 1211).
8. **出站IP (Egress Outbound IP)**: Real exit IP observed at upstream echo/test backends.
9. **IP类型 (IP Type)**: Identifies Anycast versus Unicast IP routing.
10. **数据中心 (Data Center)**: Cloudflare Colo IATA airport code (e.g. HKG, NRT, KIX, ICN, SIN, LAX, SJC, FRA, LHR).
11. **源IP位置 / 地区 / 城市 (Geo-location)**: Geographic metadata resolved from IP databases.
12. **ASN号码 / ASN组织 (Autonomous System)**: Origin AS number and carrier or hosting entity name.
13. **ProxyIP (Proxy IP Functionality)**: Activated by `--proxyip-check` (Line 1213). Validates whether the target IP can reverse-proxy traffic to Cloudflare edge services.
14. **风险等级 (Risk Score)**: Activated by `--risk-check` (Line 1214). Queries IP reputation databases for abuse scores and proxy/VPN risk levels.

### 4.2 Repudiation of Static RTT Pseudo-Bandwidth Formulas
In `speedtest.py` lines 642 to 650, download speed is currently calculated via a static heuristic:
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
**Architectural Repudiation**:
This formula is an artificial placeholder. RTT reflects propagation delay and does not correlate reliably with available TCP window bandwidth or actual link capacity.
In Phase S3, this pseudo-formula must be completely decommissioned and replaced by genuine chunked HTTP download benchmarking. Real payloads (5MB to 10MB) must be streamed from Cloudflare/Fastly speedtest endpoints through the proxy client, measuring elapsed time to compute true transfer throughput:
`Throughput_Mbps = (bytes_received * 8) / (elapsed_seconds * 1_000_000)`

---

## 5. Sorting, Elimination Strategy, and Weight Model

### 5.1 Pipeline Execution Stages
The backend executes a 4-phase pipeline, communicating progress via `opt_stage` events (Lines 532 to 534):
- **Stage 1 (Filter Phase)**:
  - Concurrency: `DEFAULT_FILTER_WORKERS = 200` (Line 65).
  - High-concurrency TCP/TLS RTT ping sweeps the candidate address pool.
  - Nodes outside the latency window `[latency_min, latency_max]` are discarded.
- **Stage 2 (Subnet Slimming / Sampling)**:
  - Concurrency: `DEFAULT_SLIM_WORKERS = 32` (Line 67).
  - Activated by `-s / --slim`.
  - Groups IPv4 by `/24` and IPv6 by `/48`. Retains only one representative IP per subnet for downstream tests, reducing candidate volume by 80% to 95%.
- **Stage 3 (Download Benchmark)**:
  - Concurrency: `DEFAULT_DOWNLOAD_WORKERS = 5` (Line 66).
  - Downloads sample payloads from the designated URL, computing sustained transfer rates in MB/s.
- **Stage 4 (ProxyIP and Risk Audit)**:
  - Checks if candidate IPs pass Cloudflare reverse proxy validation and abuse reputation thresholds.

### 5.2 Elimination and Qualification Criteria
In `result_row_for_event(mode, event)` (Lines 462 to 470):
```python
if event.get("type") != "opt_record" or not event.get("display", True):
    return None
record = event.get("record") or {}
return list(event.get("row") or []) if record.get("qualified") else None
```
Only events marked `qualified: true` are admitted into the final result set. Disqualification occurs if:
- Handshake timeout exceeds threshold.
- Latency falls outside user boundaries.
- Packet loss exceeds tolerance.
- ProxyIP verification fails when `--proxyip-check` is enabled.
- Risk check exceeds security threshold when `--risk-check` is enabled.

---

## 6. Online Optimization and Dynamic Refresh Workflow

### 6.1 State Management and Threading Architecture
In lines 613 to 641:
- `Job` dataclass encapsulates state:
  ```python
  @dataclass
  class Job:
      mode: str
      target_count: int
      created_at: float
      status: str = "running"
      result_count: int = 0
      events: list[dict] = field(default_factory=list)
      rows: list[list] = field(default_factory=list)
  ```
- Global thread safety: All mutations and reads are protected by `JOBS_LOCK = threading.Lock()` (Line 626).
- Background execution: `start_job(request)` allocates a random 16-hex ID and launches `_run_job` on a background daemon thread.

### 6.2 Real-time Server-Sent Events (SSE) Stream
- Endpoint: `GET /api/jobs/<job_id>/events` handled by `_stream_events` (Lines 785 to 809).
- Response headers: `Content-Type: text/event-stream`, `Cache-Control: no-store`, `Connection: close`.
- Polling loop: Every `SSE_POLL_INTERVAL_SECONDS = 0.2` seconds (Line 74), new events from `job.events` are streamed as `data: {...}\n\n`.
- Stream termination: When `job_done` is encountered, the loop flushes and flushes cleanly.

---

## 7. Missing Binaries: Boundary Definition and Pure Python Alternative Strategy

### 7.1 Gap Analysis and Execution Boundary Matrix

| Feature | Trace-Web Go Backend Expectation | Available in Cloned Repo? | Target Implementation in fastly-edge-speedtest | Reality and Status |
| :--- | :--- | :--- | :--- | :--- |
| **CLI and Web Wrapper** | `trace.py` script | YES (50KB) | Reference architecture, data structures, and metric models | Documented |
| **TCP/TLS Latency Engine** | `backend/main.exe` | **NO** | Native Python `socket.create_connection` and `ssl.wrap_socket` | Complete in `speedtest.py` |
| **WebSocket 101 Probing** | `backend/main.exe` | **NO** | Raw socket HTTP upgrade request sending `Upgrade: websocket` | **Pending Rewrite in Phase S3** |
| **Download Speed Engine** | `backend/main.exe` | **NO** | Chunked HTTP payload download timing | **Planned for Phase S3** (Pseudo-formula repudiated) |
| **Traceroute Engine** | `backend/nexttrace-core.exe` | **NO** | Exit IP/ASN lookup + latency threshold heuristic | Ingress route lookup planned for future phase |
| **Subnet Expansion** | Go net/ip package | **NO** | Pure Python `ipaddress` module and subnet bucketing | Complete in `generate_all_pools.py` |
| **End-to-End Proxy Verification**| External validation | **NO** | Ephemeral sandbox Mihomo instance (`sandbox_geogate`) | Complete in `geo_gate_verify.py` (Mihomo dependency acknowledged) |

### 7.2 Multi-Phase Pure Python Roadmap
1. **TCP / TLS Handshake Timing [Current Implementation]**:
   - `socket.create_connection((ip, port), timeout=0.6)` for TCP SYN-ACK RTT.
   - `ssl.SSLContext.wrap_socket(sock, server_hostname=sni)` for complete TLS handshake RTT.
2. **WebSocket 101 Upgrade Negotiation [Phase S3 Target Blueprint]**:
   - Send RFC 6455 HTTP upgrade headers over established TLS socket, parse response status, verify HTTP 101 Switching Protocols.
3. **Loss and Jitter Computation [Current Implementation]**:
   - Executes multi-round handshake probes, computing loss percentage and latency variance.
4. **Real Throughput Measurement [Phase S3 Target Blueprint]**:
   - Stream test payloads from official edge test endpoints, compute actual transfer speed in Mbps over time, replacing static latency heuristics.
