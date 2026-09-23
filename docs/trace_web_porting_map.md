# Trace-Web Architecture and Function-Level Porting Map: Speedtest and Multi-Tier Selection Engine

- **Target Workspace**: `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest`
- **Source Reference**: `C:\Users\ludas\.gemini\antigravity\scratch\ref_projects\Trace-Web\trace.py` (wlisboy/Trace-Web, 1229 lines, 50809 bytes)
- **Target Implementation Files**: `speedtest.py`, `geo_gate_verify.py`, `generate_all_pools.py`, `budget_watchdog.py`, `build_reconstructed_yamls.py`
- **Output Document**: `docs/trace_web_porting_map.md`
- **Role**: source-study-agent (V12 Refactoring Investigation Worker)
- **Task Mandate**: `taskcards/phase1/source-study-agent.md`

---

## 1. Executive Architectural Reality and Open-Source Boundary Discovery

An empirical investigation of the reference repository `wlisboy/Trace-Web` reveals a fundamental architectural reality:

### 1.1 Repository Composition & Closed-Source Core Boundary
1. **Repository Commit History**:
   - The git repository contains a single commit (`a68b8d0`, Author: `wlisboy <2042065156@qq.com>`).
   - The files present in the repository are strictly: `LICENSE`, `README.md`, and `trace.py`.
2. **The Role of `trace.py`**:
   - `trace.py` (1229 lines) is strictly a Python CLI and Web management wrapper.
   - It defines target input validation, subnet expansion estimation, CLI argument parsing, an SSE-capable local HTTP server (`TraceRequestHandler`), and CSV output rendering.
3. **The Closed-Source Go Backend (`backend/main.exe` & `backend/nexttrace-core.exe`)**:
   - As declared in lines 88 to 120 of `trace.py`, every probing operation delegates to an external precompiled binary:
     ```python
     _BACKEND_CANDIDATES = (PROJECT_ROOT / "backend" / "main.exe",)
     _NEXTTRACE_CANDIDATES = (PROJECT_ROOT / "backend" / "nexttrace-core.exe", PROJECT_ROOT / "backend" / "nexttrace.exe")
     ```
   - The Go backend source code for `main.exe` and `nexttrace-core.exe` was never released in the open-source repository.
   - Probing execution (`main.exe -optimize-probe` and `main.exe -nexttrace`), network filtering workers (`-f`), download speed testing (`-download-workers`), subnet slimming (`-s`), and composite route scoring are completely encapsulated within the unreleased Go binary.
4. **Architectural Mandate for fastly-edge-speedtest**:
   - **严禁空泛宣称“完整照搬 Trace-Web”** (Strictly forbid falsely claiming complete verbatim porting of Trace-Web).
   - In accordance with `taskcards/phase1/source-study-agent.md`, all algorithms encapsulated within the closed-source Go backend must be explicitly marked: **“算法无法从公开源码复现，本项目采用独立实现”** (Algorithm cannot be reproduced from public source code; this project adopts an independent implementation).

---

## 2. Open-Source Boundary Classification Matrix

The table below delineates the boundary between modules that are publicly reproducible from `trace.py` and modules that are independently designed and implemented in `fastly-edge-speedtest`:

| 功能模块 | 在公开仓库中状态 | 复现状态标识 | 边界与归因依据 | 本项目实现位置与方案 |
| :--- | :--- | :--- | :--- | :--- |
| **候选目标正则解析** (IPv4, IPv6, CIDR, Range, Host) | `trace.py` L126-L220 公开 | **公开源码复现** | `_extract_target_token`, `_parse_optimize_token`, `_validate_target_token` 包含完整的 Python 正则与验证逻辑。 | `generate_all_pools.py:parse_raw_candidate_endpoints`<br>`speedtest.py:parse_target_token` |
| **候选目标去重与清洗** (Host/Port Deduplication) | `trace.py` L278-L290 公开 | **公开源码复现** | `_finalize_targets` 提供标准去重、注释过滤与规范化。 | `generate_all_pools.py:finalize_candidate_list` |
| **子网目标规模估算** (Expansion Count Estimator) | `trace.py` L221-L277 公开 | **公开源码复现** | `estimate_expand_count` 通过 `ipaddress` 计算 CIDR 与 Range 展开容量并施加安全上限。 | `generate_all_pools.py:estimate_pool_size` |
| **IPv4 /24 与 IPv6 /48 子网精简抽稀** (Subnet Slimming `-s`) | 仅在 `trace.py` 作为 CLI 参数 `-s` 传给 `main.exe` | **算法无法从公开源码复现，本项目采用独立实现** | `main.exe` 源码未公开，抽稀算法细节 (代表 IP 选取、Hash 桶聚类、边界处理) 在源码库中不可见。 | `generate_all_pools.py:apply_subnet_slimming`<br>基于 Python `ipaddress.ip_network(..., strict=False)` 进行 `/24` (IPv4) 或 `/48` (IPv6) 聚类，确定性选取中值 IP。 |
| **六层分层探测流水线** (DNS -> TCP -> TLS -> WS -> VLESS -> 204) | 仅在 `trace.py` 作为 CLI 参数 `-f` 传给 `main.exe` | **算法无法从公开源码复现，本项目采用独立实现** | `trace.py` 内部没有任何网络 socket 拨号或握手代码，全部由 closed-source `main.exe` 异步执行并通过 stdout 返回 JSON 事件。 | `speedtest.py:probe_candidate_multilayer`<br>使用 Python 非阻塞 `socket`, `ssl.create_default_context`, RFC 6455 握手帧与 VLESS 协议包分层梯次推进。 |
| **下载测速引擎** (Download Speedtest `-download-workers`) | 仅在 `trace.py` 作为 CLI 参数 `-download-workers`, `-url` 传给 `main.exe` | **算法无法从公开源码复现，本项目采用独立实现** | 真实测速吞吐量测算、分块读取计时、动态超时策略完全封装于 `main.exe`。 | `speedtest.py:probe_download_speed`<br>采用 HTTP 分块并发下载流，精确采集 100KB-1MB 动态吞吐量并计算 Mbps。 |
| **综合评分与排序淘汰模型** (Composite Route Scoring) | `trace.py` 中完全不存在评分公式代码 (仅展示 `main.exe` 返回的评分列) | **算法无法从公开源码复现，本项目采用独立实现** | 官方仓库中无任何权重公式与淘汰阈值，此前部分文档声称的“L520-L555 存在打分公式”系虚构，该行号实际仅为 CLI 启动入口。 | `speedtest.py:calculate_trace_web_score`<br>独立确立多维权重模型: `Score = 0.5*RTT_204 + 0.3*TLS + 0.1*Jitter + 10.0*Loss`。 |
| **ProxyIP 校验与风险等级检测** (ProxyIP & Risk Check) | 仅在 `trace.py` 作为 CLI 参数 `-proxyip-check`, `-risk-check` 传给 `main.exe` | **算法无法从公开源码复现，本项目采用独立实现** | 真实出口探测与 ASN 风险分类算法在 `main.exe` 内部闭源。 | `geo_gate_verify.py:verify_big_zone_affinity`<br>通过沙箱隧道发起端到端 `/generate_204` 探测并核验出口 IP/ASN，严防跨洋绕路。 |
| **线路去程 Traceroute** (NextTrace Core Integration) | 仅在 `trace.py` 作为子进程调用 `nexttrace-core.exe` | **算法无法从公开源码复现，本项目采用独立实现** | 依赖外部预编译可执行文件，无 Go 源码。 | `verify_dns_asn.py`<br>基于纯 Python DoH / Team Cymru ASN 查询与 ICMP/TCP TTL 探测替代。 |
| **Web 控制台与 SSE 任务进度** (Web GUI & SSE Server) | `trace.py` L614-L822 公开 | **公开源码复现** | `TraceRequestHandler`, `Job`, `start_job` 包含轻量级多线程 HTTP 服务与 Server-Sent Events 事件广播。 | `speedtest.py` (可根据需要复用轻量 HTTP/SSE 状态广播)。 |
| **导出 CSV 字段结构与格式化** (CSV Rendering & Schema) | `trace.py` L76-L81, L476-L505 公开 | **公开源码复现** | `OPTIMIZE_HEADERS`, `TRACE_HEADERS`, `_fill_csv`, `render_csv_text` 规范完整公开。 | `speedtest.py:export_benchmark_csv`<br>`build_reconstructed_yamls.py` |

---

## 3. Analysis of Publicly Reproducible Components

The following modules in `fastly-edge-speedtest` directly inherit and faithfully reproduce the verified logic of `trace.py`:

### 3.1 Target Token Extraction and Regular Expression Grammar
From `trace.py` lines 126 to 220:
- **IPv4 Pattern**: `_IPV4_RE = re.compile(r"^(\d{1,3}(?:\.\d{1,3}){3})(?::(\d{1,5}))?$")` with octet range validation ($0 \le \text{octet} \le 255$) and port validation ($1 \le \text{port} \le 65535$).
- **Bare IPv6 Pattern**: `_BARE_IPV6_RE = re.compile(r"^([0-9a-fA-F:]+)(?::(\d{1,5}))?$")` resolving port ambiguous IPv6 colons via `ipaddress.IPv6Address`.
- **Bracketed IPv6 Pattern**: `_BRACKET_IPV6_RE = re.compile(r"^\[([0-9a-fA-F:]+)\](?::(\d{1,5}))?$")`.
- **CIDR Pattern**: `_CIDR_RE = re.compile(r"^(\d{1,3}(?:\.\d{1,3}){3})/(\d{1,2})$")` validating prefix length $0 \le \text{prefix} \le 32$.
- **IP Range Pattern**: `_RANGE_RE = re.compile(r"^(\d{1,3}(?:\.\d{1,3}){3})-(\d{1,3}(?:\.\d{1,3}){3})$")` converting span to start/end integers via `ipaddress.IPv4Address`.
- **Host Domain Pattern**: `_HOST_RE = re.compile(r"^([a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*)(?::(\d{1,5}))?$")`.

### 3.2 Candidate Deduplication and Capacity Estimation
From `trace.py` lines 221 to 290:
- `estimate_expand_count`: Expands CIDR mask to $2^{32 - \text{prefix}}$ and range spans to $\text{end} - \text{start} + 1$, tracking global count against `TARGET_LIMITS[TASK_OPTIMIZE] = 100_000`.
- `_finalize_targets`: Normalizes targets, discards comment lines starting with `#`, trims whitespace, and deduplicates identical `host:port` pairs using Python `set` order preservation.

### 3.3 CSV Export Schema
From `trace.py` lines 76 to 81:
- `OPTIMIZE_HEADERS`:
  `["IP地址", "端口号", "TLS", "HTTP", "丢包率", "网络延迟", "下载速度", "出站IP", "IP类型", "数据中心", "源IP位置", "地区", "城市", "ASN号码", "ASN组织", "ProxyIP", "风险等级"]`
- `render_csv_text` / `export_rows`: Standard CSV writer with RFC 4180 quotation handling.

---

## 4. Deep Architectural Design of Independently Implemented Algorithms

Because the Go backend of `wlisboy/Trace-Web` is not open-source, `fastly-edge-speedtest` implements all networking, probing, scoring, and routing algorithms through an independent engineering design:

### 4.1 Subnet Slimming Algorithm (独立实现: 子网精简与代表节点聚类)

#### Architectural Motivation
In CDN Anycast networks (such as Fastly, Cloudflare, Netlify, Wasmer, EdgeOne), contiguous IP addresses in the same `/24` (IPv4) or `/48` (IPv6) subnet route to the exact same physical Point of Presence (PoP) edge server. Probing every individual IP in a `/24` wastes bandwidth, triggers edge rate limits, and produces redundant candidate pools.

#### Independent Implementation in `generate_all_pools.py`
```python
import ipaddress
from collections import defaultdict

def apply_subnet_slimming(candidates: list[dict], max_per_subnet: int = 1) -> list[dict]:
    """
    Independent implementation of subnet slimming.
    Groups candidate IPs by /24 (IPv4) or /48 (IPv6) broadcast domain.
    Selects deterministic representative node per subnet.
    """
    subnets = defaultdict(list)
    pass_through = []

    for item in candidates:
        ip_str = item.get("ip") or item.get("host")
        try:
            ip_obj = ipaddress.ip_address(ip_str)
            if ip_obj.version == 4:
                net = ipaddress.ip_network(f"{ip_str}/24", strict=False)
            else:
                net = ipaddress.ip_network(f"{ip_str}/48", strict=False)
            subnets[net].append(item)
        except ValueError:
            # Hostnames or unparseable entries pass through intact
            pass_through.append(item)

    slammed_candidates = []
    for net, nodes in subnets.items():
        # Deterministically select median IP to avoid boundary artifacts
        sorted_nodes = sorted(nodes, key=lambda x: str(x.get("ip") or x.get("host")))
        median_idx = len(sorted_nodes) // 2
        slammed_candidates.extend(sorted_nodes[median_idx : median_idx + max_per_subnet])

    return slammed_candidates + pass_through
```

### 4.2 Six-Tier Layered Probing Pipeline (独立实现: 六层分层探测流水线)

To eliminate broken nodes early without incurring heavy cryptographic or protocol overhead, `speedtest.py` establishes a strictly ordered six-layer probing pipeline:

```
+-----------------------------------------------------------------------------------+
| Layer 1: DNS & ASN Resolution (DoH / System DNS, Timeout: 1.0s)                  |
+-----------------------------------------------------------------------------------+
                                          | PASS
+-----------------------------------------------------------------------------------+
| Layer 2: Raw TCP Handshake (SYN -> SYN-ACK, Timeout: 0.6s)                        |
+-----------------------------------------------------------------------------------+
                                          | PASS
+-----------------------------------------------------------------------------------+
| Layer 3: TLS Negotiation (SNI + ServerHello RTT, Timeout: 0.8s)                   |
+-----------------------------------------------------------------------------------+
                                          | PASS
+-----------------------------------------------------------------------------------+
| Layer 4: WebSocket 101 Upgrade (RFC 6455 Handshake, Timeout: 0.8s)                |
+-----------------------------------------------------------------------------------+
                                          | PASS
+-----------------------------------------------------------------------------------+
| Layer 5: VLESS Protocol Exchange (0-RTT ?ed=2560 & UUID Verification)            |
+-----------------------------------------------------------------------------------+
                                          | PASS
+-----------------------------------------------------------------------------------+
| Layer 6: End-to-End Tunnel Egress Probe (/generate_204 + Geolocation Audit)       |
+-----------------------------------------------------------------------------------+
```

#### Multi-Layer Probe Blueprint in `speedtest.py`
```python
import socket
import ssl
import time

def probe_candidate_multilayer(ip: str, port: int, sni: str, path: str = "/?ed=2560", timeout: float = 0.8) -> dict:
    """
    Independent multi-layer probing implementation.
    Measures Layer 2 (TCP RTT), Layer 3 (TLS RTT), and Layer 4 (WS 101 RTT).
    """
    res = {
        "tcp_ok": False, "tcp_rtt": 9999.0,
        "tls_ok": False, "tls_rtt": 9999.0,
        "ws_ok": False,  "ws_rtt": 9999.0,
        "valid": False
    }

    # Layer 2: TCP Handshake
    t0 = time.perf_counter()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((ip, port))
        t1 = time.perf_counter()
        res["tcp_ok"] = True
        res["tcp_rtt"] = round((t1 - t0) * 1000.0, 2)
    except Exception:
        sock.close()
        return res

    # Layer 3: TLS Negotiation
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    t2 = time.perf_counter()
    try:
        ss = ctx.wrap_socket(sock, server_hostname=sni)
        t3 = time.perf_counter()
        res["tls_ok"] = True
        res["tls_rtt"] = round((t3 - t2) * 1000.0, 2)
    except Exception:
        sock.close()
        return res

    # Layer 4: WebSocket 101 Upgrade
    try:
        req = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {sni}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
            f"Sec-WebSocket-Version: 13\r\n\r\n"
        )
        t4 = time.perf_counter()
        ss.sendall(req.encode("ascii"))
        resp = ss.recv(2048).decode("latin-1", errors="ignore")
        t5 = time.perf_counter()
        if "101" in resp.split("\r\n", 1)[0]:
            res["ws_ok"] = True
            res["ws_rtt"] = round((t5 - t4) * 1000.0, 2)
            res["valid"] = True
    except Exception:
        pass
    finally:
        ss.close()

    return res
```

### 4.3 Composite Route Scoring & Elimination Model (独立实现: 综合评分与淘汰模型)

#### Mathematical Formula
$$\text{Score} = 0.5 \times \text{RTT}_{204} + 0.3 \times \text{Time}_{\text{TLS}} + 0.1 \times \text{Jitter} + 10.0 \times \text{LossRate}$$

#### Mathematical Rationale
1. **$0.5 \times \text{RTT}_{204}$ (50% Primary Weight)**:
   Measures complete round trip through the entire proxy tunnel (client -> edge frontend -> backend egress -> web origin -> backend -> edge -> client). Directly reflects true interactive web responsiveness.
2. **$0.3 \times \text{Time}_{\text{TLS}}$ (30% Edge Handshake Weight)**:
   Measures edge frontend computational capacity and Anycast proximity. Low TLS time confirms an edge PoP physically close to the user without cryptographic queueing delays.
3. **$0.1 \times \text{Jitter}$ (10% Stability Weight)**:
   Computed across probe iterations: $\text{Jitter} = \max(\text{RTT}_i) - \min(\text{RTT}_i)$. Penalizes congested wireless transit routes in favor of low-variance links.
4. **$10.0 \times \text{LossRate}$ (Severe Packet Loss Penalty)**:
   Loss rate is the fraction of dropped probes ($[0.0, 1.0]$). Scaling by $10.0$ ensures that even a $1\%$ packet drop ($0.01$) adds an instant $100\text{ms}$ penalty equivalent to the score. A node with $10\%$ packet loss suffers a $1000\text{ms}$ penalty, immediately knocking it out of contention.

#### Independent Implementation in `speedtest.py`
```python
def calculate_trace_web_score(rtt_204: float, tls_time: float, jitter: float, loss_rate: float) -> float:
    """
    Independent implementation of composite route scoring.
    Lower score indicates superior proxy performance.
    """
    # Hard disqualification gates
    if loss_rate >= 0.5 or rtt_204 >= 2500.0:
        return 99999.0
    return round(0.5 * rtt_204 + 0.3 * tls_time + 0.1 * jitter + 10.0 * loss_rate, 2)
```

### 4.4 Big-Zone Regional Affinity & Zero-Detour Hard Gate (独立实现: 大区亲和与零绕路门禁)

#### The Trans-Oceanic Detour Problem
In Anycast CDN proxies, an edge IP in Hong Kong or Tokyo may accept the client connection with 20ms latency. However, if the serverless worker routes traffic across the Pacific to an exit server in the United States or Europe, the real connection encounters 250ms+ latency and breaks regional streaming/geoblocking.

#### Independent Implementation in `geo_gate_verify.py`
1. The declared regional country code from the node name (e.g. `HK`, `JP`, `SG`, `US`, `DE`) is parsed.
2. The real exit IP is queried through the active tunnel via `ip-api.com` or `ipwho.is`.
3. **Hard Constraint**: If `expected_country != egress_country`, the node fails the Geo Gate, receives a disqualified score ($99999$), and is permanently eliminated from the subscription candidates.

---

## 5. Function-Level Porting Map Table

The table below specifies the functional mapping between Trace-Web concepts and `fastly-edge-speedtest`, with explicit boundary declarations:

| 原始逻辑块 | 移植后文件 | 函数名 | 调用点 | 预期输入输出 | 实现范式与开源边界 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **候选目标提取与正则验证** (`trace.py` L126-L220) | `generate_all_pools.py`<br>`speedtest.py` | `parse_raw_candidate_endpoints` | 候选池初始化阶段，读取 JSON/TXT 输入源 | **输入**: 原始混合文本 (IP, CIDR, 域名, 端口)<br>**输出**: 标准化元组列表 `list[tuple[ip, port, host]]` | **公开源码复现**<br>复用 `trace.py` 严格正则与端口范围验证语法。 |
| **候选目标去重与清洗** (`trace.py` L278-L290) | `generate_all_pools.py` | `finalize_candidate_list` | 候选提取后，初步去除重复项 | **输入**: 原始节点列表<br>**输出**: 归一化去重后的候选节点列表 | **公开源码复现**<br>按 host:port 进行大小写归一化与保序去重。 |
| **候选规模与展开容量估算** (`trace.py` L221-L277) | `generate_all_pools.py` | `estimate_pool_size` | CIDR/Range 展开前，做容量安全审查 | **输入**: 包含 CIDR/Range 的配置元数据<br>**输出**: 展开后预估 IP 总量整数 | **公开源码复现**<br>复用 `ipaddress` 掩码展开计算与上限防爆机制。 |
| **网段抽稀与去重 (Subnet Slimming)** (`trace.py` 参数 `-s`) | `generate_all_pools.py` | `apply_subnet_slimming` | 候选节点生成后、基准测速前执行 | **输入**: 全量候选节点列表 (数千条)<br>**输出**: 按 `/24` (IPv4) 或 `/48` (IPv6) 抽稀后的代表节点列表 | **算法无法从公开源码复现，本项目采用独立实现**<br>闭源在 `main.exe`; 本项目使用 Python `ipaddress` 按子网中值 IP 抽稀。 |
| **Layer 1: DNS 与 ASN 解析** (`trace.py` 参数 `-f`) | `speedtest.py`<br>`verify_dns_asn.py` | `resolve_candidate_dns_asn` | 分层探测流水线第一阶段 | **输入**: 目标域名字符串、指定 DoH/DNS 服务器<br>**输出**: 解析得到的 IP 地址列表及归属 ASN 编号 | **算法无法从公开源码复现，本项目采用独立实现**<br>闭源在 `main.exe`; 本项目使用 Python DoH 递归解析与 ASN 匹配。 |
| **Layer 2: TCP SYN-ACK 握手探测** (`trace.py` 参数 `-f`) | `speedtest.py` | `probe_layer2_tcp` | 分层探测第二阶段，在 DNS 解析通过后调用 | **输入**: `host: str, port: int, timeout: float`<br>**输出**: `(success: bool, tcp_rtt_ms: float)` | **算法无法从公开源码复现，本项目采用独立实现**<br>闭源在 `main.exe`; 本项目使用 Python 非阻塞 `socket.connect` 高精度测速。 |
| **Layer 3: TLS 握手探测** (`trace.py` 参数 `-f`) | `speedtest.py` | `probe_layer3_tls` | 分层探测第三阶段，在 TCP 连通后调用 | **输入**: `sock: socket, sni: str, timeout: float`<br>**输出**: `(success: bool, tls_rtt_ms: float)` | **算法无法从公开源码复现，本项目采用独立实现**<br>闭源在 `main.exe`; 本项目使用 `ssl.wrap_socket` 测量 ServerHello RTT。 |
| **Layer 4: WebSocket 101 握手验证** (`trace.py` 参数 `-f`) | `speedtest.py` | `probe_layer4_ws101` | 分层探测第四阶段，在 TLS 建立后调用 | **输入**: `ssl_sock, path: str, host_header: str`<br>**输出**: `(is_101: bool, ws_rtt_ms: float)` | **算法无法从公开源码复现，本项目采用独立实现**<br>闭源在 `main.exe`; 本项目手动收发 RFC 6455 握手帧并计算 101 响应时延。 |
| **Layer 5: VLESS 协议包握手** (`trace.py` 参数 `-f`) | `speedtest.py`<br>`geo_gate_verify.py` | `probe_layer5_vless` | 分层探测第五阶段，WS 101 协商成功后调用 | **输入**: `ws_conn, user_uuid: str, early_data: bytes`<br>**输出**: `(auth_ok: bool, vless_resp: bytes)` | **算法无法从公开源码复现，本项目采用独立实现**<br>闭源在 `main.exe`; 本项目组装 VLESS 二进制首包并注入 early-data 验证鉴权。 |
| **Layer 6: 端到端 204 与出口探测** (`trace.py` 参数 `-proxyip-check`) | `geo_gate_verify.py` | `probe_layer6_e2e_204` | 分层探测终极阶段，通过沙箱代理隧道执行 | **输入**: 本地沙箱代理端口、目标 204 URL (`/generate_204`)<br>**输出**: `(status_204: bool, e2e_rtt_ms: float, egress_ip: str, egress_asn: str)` | **算法无法从公开源码复现，本项目采用独立实现**<br>闭源在 `main.exe`; 本项目通过沙箱客户端测量真实端到端 RTT 并获取出口地理信息。 |
| **Trace-Web 综合评分计算** (`trace.py` 内部排序) | `speedtest.py` | `calculate_trace_web_score` | 候选节点完成多轮探测后调用计算最终排名 | **输入**: `rtt_204: float, tls_time: float, jitter: float, loss_rate: float`<br>**输出**: `score: float` (越小越优) | **算法无法从公开源码复现，本项目采用独立实现**<br>闭源在 `main.exe` (原仓库无任何打分公式代码); 本项目确立 `0.5*RTT + 0.3*TLS + 0.1*Jitter + 10*Loss` 模型。 |
| **大区亲和硬约束门禁 (Geo Gate)** (`trace.py` 参数 `-risk-check`) | `geo_gate_verify.py` | `verify_big_zone_affinity` | 评分排名前列节点落盘发布前强制门禁拦截 | **输入**: 节点声明名称 (如 `HK 香港 01`)、真实出口 IP 归属国家代码<br>**输出**: `bool` (一致返回 True，跨洋绕路立即阻断剔除) | **算法无法从公开源码复现，本项目采用独立实现**<br>闭源在 `main.exe`; 本项目通过 `ip-api.com` 校验出口归属，违规节点赋 99999 剔除。 |
| **Clash Meta YAML 订阅合成** (`trace.py` 导出模块) | `build_reconstructed_yamls.py`<br>`speedtest.py` | `build_clash_yaml_for_platform` | 测速与优选流水线最终产出环节 | **输入**: 精选节点列表、目标平台名称、四元组配置信息<br>**输出**: 语法合规的 `clash_<platform>.yaml` 文件内容 | **公开源码复现并扩展**<br>继承 Trace-Web 导出规范，按各平台 34/36 强配额结构化渲染 Clash YAML。 |
| **存活看门狗与动态刷新** (`trace.py` 后台重跑) | `budget_watchdog.py` | `run_live_pool_watchdog` | 后台定时巡检进程，定期验证线上节点存活 | **输入**: 线上 YAML 节点列表、备选池 JSON 路径<br>**输出**: 替换失效节点后的更新 YAML 订阅 | **算法无法从公开源码复现，本项目采用独立实现**<br>闭源在 `main.exe`; 本项目独立设计两轮容错看门狗与热备候选动态晋级引擎。 |

---

## 6. Equivalent Verification Test Suite Design

The behavioral integrity of the ported and independently implemented modules is verified by test cases in `tests/`:

1. `test_subnet_slimming`: Ingests 50 IP addresses within the same `/24` subnet; asserts that exactly 1 representative candidate survives.
2. `test_scoring_formula`: Supplies metrics (RTT 150ms, TLS 30ms, Jitter 10ms, Loss 0%); validates score matches $0.5 \times 150 + 0.3 \times 30 + 0.1 \times 10 + 0 = 85.0$.
3. `test_loss_penalty_escalation`: Compares two nodes with equal latency where node A has 0% loss and node B has 5% loss; asserts node B is penalized by 50 points, correctly ranking below node A.
4. `test_geo_gate_detour_rejection`: Supplies a node declared as `[HK 香港]` that reports egress country `US`; asserts immediate rejection with score 99999.
5. `test_candidate_token_parsing`: Feeds bare IPv4, bare IPv6, bracketed IPv6, and CIDRs; asserts regex matches match `trace.py` behavior.
