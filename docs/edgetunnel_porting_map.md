# Architectural Study and Porting Map: cmliu/edgetunnel (_worker.js) to fastly-edge-speedtest

- **Target Workspace**: `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest`
- **Source Reference**: `C:\Users\ludas\.gemini\antigravity\scratch\ref_projects\edgetunnel\_worker.js` (cmliu/edgetunnel, 6643 lines)
- **Secondary Reference**: `zizifn/edgetunnel` (Original minimalist VLESS over WebSocket implementation)
- **Output Document**: `docs/edgetunnel_porting_map.md`
- **Role**: source-study-agent (V12 Refactoring Investigation Worker)
- **Task Mandate**: `taskcards/phase1/source-study-agent.md`

---

## 1. Executive Overview and Scope

This document provides a line-level investigation of `cmliu/edgetunnel` (`_worker.js`, 6643 lines), delivering a function-level porting map across ten core wire-level proxy capabilities to the multi-runtime platform architecture of `fastly-edge-speedtest`.

### 1.1 Architectural Evolution: zizifn vs cmliu

1. **zizifn/edgetunnel (Minimalist Foundation)**:
   - Pioneered serverless VLESS over WebSocket tunneling directly inside Cloudflare Workers.
   - Core footprint: ~400 lines of JavaScript.
   - Key mechanisms: HTTP request upgrade detection, `WebSocketPair` termination, binary VLESS header parsing (UUID, target port, address), outbound socket creation via `connect()`, and bidirectional stream piping via `readable.pipeTo(writable)`.
   - Structural constraints: Hardcoded single proxy destination, zero dynamic egress routing, no SOCKS5 outbound chaining, minimal error teardown, and manual subscription management.

2. **cmliu/edgetunnel (Industrial Multi-Feature Iteration)**:
   - Expanded into an edge gateway (6643 lines of JavaScript in `_worker.js`).
   - Integrated features:
     * Dynamic `PROXYIP` routing with path-level `/proxyip=...` and query-level `?proxyip=...` overrides.
     * DoH (DNS over HTTPS) resolution for DNS TXT records containing candidate proxy IP pools with deterministic LCG pseudo-random shuffling.
     * Multi-candidate concurrent race dialing (`connectProxyIP`) with fast-failover affinity caching and fallback to direct connection (`connectDirect`).
     * SOCKS5 and HTTP CONNECT forward proxy chaining (`socks5Connect`, `httpConnect`, `httpsConnect`) with domain whitelist matching (`SOCKS5白名单`).
     * Advanced early-data extraction from `Sec-WebSocket-Protocol` supporting both VLESS and Trojan wire protocols with strict byte-length guards.
     * High-entropy UUID authentication: deterministic MD5MD5 fallback derivation and first-8 hex character summation verification on the `/version` endpoint.
     * Dynamic camouflage engine: Nginx default page (`nginx`), Cloudflare Error 1101 simulation with real-time Ray ID (`html1101`), and reverse proxying with text-stream domain replacement.
     * Robust socket lifecycle management: generation-based connection invalidation (`失效TCP连接世代`), quiet socket closure (`closeSocketQuietly`), and dual-side teardown in stream `finally` blocks.

### 1.2 Boundary Definition for fastly-edge-speedtest

`fastly-edge-speedtest` is an automated multi-platform edge benchmarking, candidate selection, and subscription generation engine. It interacts with `_worker.js` across two distinct execution domains:
- **Client/Pipeline Side (Python)**: Implemented in `speedtest.py`, `geo_gate_verify.py`, and `generate_all_pools.py`. It probes edge frontends, executes WebSocket handshakes, validates UUID authentication, tests 0-RTT early data negotiation, audits real exit IP geolocation against declared regions, and outputs calibrated Clash Meta YAML configs.
- **Server/Backend Side (TypeScript / Go / Node.js)**: Deployed across non-Cloudflare target runtimes (Supabase Deno, Wasmer Node.js, Northflank Go, Fastly Compute, EdgeOne). Because non-Cloudflare runtimes lack Cloudflare-specific APIs (`request.fetcher.connect`, `new WebSocketPair()`, `request.cf`), server-side logic requires runtime-native socket adapters (`net.connect`, `Deno.connect`, `net.Dialer`).

---

## 2. In-Depth Study of 10 Core Functional Mechanisms

### 2.1 Feature 1: VLESS Protocol Header Parsing (VLESS 请求头解析)

In `_worker.js` lines 1964 to 2012 (`解析魏烈思请求`), the incoming binary payload is parsed according to the VLESS protocol specification:

```
+---------+----------------+---------+---------+--------+----------+---------+---------------+
| Version | UUID (16B)     | Addons  | Command | Port   | AddrType | Address | Initial Data  |
| 1 Byte  | Binary Buffer  | Length  | 1 Byte  | 2 Byte | 1 Byte   | Var len | Var len       |
| (0x00)  | Byte 1..16     | 1 Byte  | (1=TCP) | BigEnd | 1/2/3    | Var len | (ClientHello) |
+---------+----------------+---------+---------+--------+----------+---------+---------------+
```

1. **Wire Layout Details**:
   - `Byte 0 (Version)`: Checked against VLESS protocol version 0 (`0x00`). If mismatched or `chunk.byteLength < 24`, returns `{ hasError: true, message: 'invalid data' }`.
   - `Bytes 1 to 16 (UUID)`: 16-byte raw binary array. Verified against target authenticated user UUID via `UUID字节匹配(chunk, 1, token)`. If mismatch, returns `{ hasError: true, message: 'invalid user' }`.
   - `Byte 17 (Addons Length optLength)`: Specifies length of addon bytes (`chunk.slice(17, 18)[0]`).
   - `Byte cmdIndex = 18 + optLength (Command)`:
     * `0x01`: TCP stream.
     * `0x02`: UDP packet.
     * Any other value throws an invalid command error.
   - `Bytes portIdx = cmdIndex + 1 to portIdx + 1 (Target Port)`: Big-endian unsigned 16-bit integer: `port = (data[portIdx] << 8) | data[portIdx + 1]`.
   - `Byte addrTypeIdx = portIdx + 2 (Address Type)`:
     * `0x01` (IPv4): 4 bytes, parsed as `a.b.c.d`.
     * `0x02` (Domain Name): 1-byte length prefix `L`, followed by `L` bytes of UTF-8 encoded domain name string.
     * `0x03` (IPv6): 16 bytes, parsed as eight 16-bit colon-delimited hexadecimal blocks.
   - `Remaining Bytes (Initial Payload)`: Offset `rawIndex = addrValIdx + addrLen` through packet end contains initial application payload (e.g. TLS ClientHello or HTTP GET), returned as `rawData = chunk.slice(rawIndex)`.
2. **Porting Implementation**:
   - Node.js (`configs/wasmer/server.js` lines 165 to 206): Uses native `Buffer` slicing and `readUInt16BE` for port parsing.
   - Deno (`configs/supabase/functions/edgetunnel/index.ts`): Uses typed `Uint8Array` slicing and `DataView` for big-endian integer reading.
   - Go (`configs/northflank/main.go`): Uses `binary.BigEndian.Uint16` on slice offsets.

### 2.2 Feature 2: UUID Strict Validation and Parsing (UUID 严格校验)

`_worker.js` implements a multi-tier UUID validation and fallback hierarchy:
1. **Binary Wire Comparison (`UUID字节匹配`, Lines 1955-1962)**:
   - Pre-converts canonical 36-character UUID string into a 16-byte Uint8Array via `获取UUID字节(uuid)` (Lines 1934-1953) with global `UUID缓存Map` caching.
   - Compares bytes 1..16 directly in memory with zero allocations.
2. **High-Entropy First-8 Hex Checksum (`/version` Endpoint, Lines 54-66)**:
   - Computes integer sum of first 8 characters (`0-9` mapped to `0-9`, `a-f` mapped to `10-15`).
   - Requires both the sum and the exact last 12 characters (`.slice(-12)`) to match the target UUID.
3. **Deterministic Fallback Derivation (`MD5MD5`, Lines 5402-5415)**:
   - If `env.UUID` is absent, derives deterministic UUID v4 via double MD5: `userIDMD5 = MD5MD5(ADMIN_PASSWORD + KEY)` formatted into standard 8-4-4-4-12 with version byte forced to `4` and variant byte forced to `8`.
4. **Porting Implementation in fastly-edge-speedtest**:
   - Discards fragile MD5MD5 derivation in favor of statically generated RFC 4122 UUID v4 tokens configured per platform (`uuid_config.json`).
   - Employs constant-time byte comparisons (`Buffer.equals()` in Node, `subtle.ConstantTimeCompare` in Go) to defend against timing side-channel attacks.

### 2.3 Feature 3: WebSocket Bidirectional Duplex Streaming (WebSocket 双向流)

1. **WebSocket Termination & Flow Control in `_worker.js`**:
   - Lines 1290-1787 (`处理WS请求`): Uses Cloudflare-specific `new WebSocketPair()`, accepts server side `webSocket.accept()`, and establishes remote TCP connection via `connecttoPry()`.
   - `创建上行Grain合包流` (Lines 2601-2680): Aggregates small WebSocket frames into 20KB (`上行合包目标字节`) chunks to minimize kernel context switching.
   - `创建上行写入队列` (Lines 2682-2824): Flow control queue (`上行队列最大字节 = 16MB`, `上行队列最大条目 = 4096`) preventing memory exhaustion when remote TCP socket writable stream is congested.
   - `创建下行Grain发送器` (Lines 2826-3024): Batches remote TCP stream reads into 32KB (`下行Grain包字节`) frames.
   - `connectStreams(remoteSocket, webSocket, headerData, ...)` (Lines 3026-3094): Bridges `remoteSocket.readable` to `webSocket` using BYOB reader mode (`mode: 'byob'`) with 64KB read buffers.
2. **Porting Implementation**:
   - Because `WebSocketPair` does not exist on Wasmer, Supabase, or Northflank:
     * Wasmer: Uses Node `http.createServer` with `server.on('upgrade')` and pipes raw TCP socket to Node `net.Socket`.
     * Supabase: Uses `Deno.upgradeWebSocket(req)` and bridges message events directly to `Deno.connect` TCP streams.
     * Northflank: Uses Go `gorilla/websocket` or `nhooyr.io/websocket` bridging to `net.Conn` duplex copy (`io.Copy`).

### 2.4 Feature 4: early-data (?ed= and Sec-WebSocket-Protocol)

1. **Wire Mechanism in `_worker.js`**:
   - Functions: `解码WS早期数据(header, token)` (Lines 1260-1287) and `是有效WS早期数据(bytes, token)` (Lines 1248-1258).
   - Extracts base64url payload from `Sec-WebSocket-Protocol` header.
   - Guard limit: `WS早期数据最大字节 = 8192` (8 KB), `WS早期数据最大头长度 = Math.ceil(8192 * 4 / 3) + 4`. If length is exceeded, returns null.
   - Base64url decoding: Transforms `-` to `+`, `_` to `/`, appends `=` padding, and decodes into Uint8Array.
   - Validity check: Verifies `bytes.length >= 18` and `UUID字节匹配(bytes, 1, token)`.
   - Queueing: In lines 1776 to 1784, decoded early data buffer is passed as `initialData` to `connecttoPry` before subsequent WebSocket `message` events are processed.
   - Client parameter: Clients append `?ed=2560` to the WebSocket path. Mihomo and Xray detect this parameter and pack the initial VLESS request frame into `Sec-WebSocket-Protocol` during the initial HTTP request, saving a full round-trip time.
2. **Porting Implementation**:
   - Node.js: Uses `Buffer.from(proto, 'base64url')` with strict 8KB upper boundary check.
   - Deno: Decodes base64url string to Uint8Array and injects into outbound TCP stream before starting WebSocket message loop.
   - Client pipeline: `speedtest.py` tests 0-RTT compatibility by injecting `?ed=2560` in the probing request.

### 2.5 Feature 5: TCP Connect and Dialing Architecture (TCP connect)

1. **Mechanism in `_worker.js`**:
   - `创建请求TCP连接器(request)` (Lines 3329-3334): Relies on `request.fetcher.connect(options)` provided by Cloudflare Workers runtime.
   - `打开TCP连接(address, port, options)` (Lines 2223-2233): Creates outbound socket with optional TLS wrapper.
   - `并发打开候选连接(候选列表)` (Lines 2241-2263): Races multiple connection promises via `Promise.race`, returning the fastest established socket and canceling losers.
   - `connectDirect(address, port, data, 启用预加载)` (Lines 2295-2316): Directly dials target host:port with `TCP并发拨号数 = 2`.
2. **Porting Implementation**:
   - Replaces Cloudflare `request.fetcher.connect` with runtime-native socket factories:
     * Wasmer: Node `require('net').connect({ host, port })`.
     * Supabase: Deno `Deno.connect({ hostname, port })`.
     * Northflank: Go `net.Dialer{Timeout: 10 * time.Second}.Dial("tcp", target)`.
     * Fastly Compute: Backend-defined static upstream or dynamic backend.

### 2.6 Feature 6: ProxyIP Dynamic Routing and Fallback (ProxyIP fallback)

1. **Mechanism in `_worker.js`**:
   - `connectProxyIP(address, port, data, 所有反代数组, 启用反代失败兜底)` (Lines 2318-2350):
     * Iterates through candidate proxy IPs in batches of `反代并发拨号数`.
     * Dials candidates concurrently via `并发打开候选连接(候选列表)`.
     * If a candidate connects successfully, writes initial payload, updates `反代数组索引 = candidate.index` for session affinity, and returns the active socket.
     * Fallback Trigger (Line 2345):
       ```javascript
       if (启用反代失败兜底) return connectDirect(address, port, data, false);
       else throw new Error('[反代连接] 所有反代连接失败，且未启用反代兜底，连接终止。');
       ```
       When all proxy IP candidates fail, `connectProxyIP` seamlessly falls back to `connectDirect` to reach the target directly.
   - Resolution and Discovery:
     * `解析地址端口(ctx反代IP, host, yourUUID)` (Lines 6437-6451): Parses proxy IP targets, issuing parallel DoH TXT queries (`DoH查询`, Lines 5437-5595) to parse embedded proxy endpoint lists.
     * Uses deterministic Linear Congruential Generator (LCG) seeded with target domain and UUID to shuffle proxy IP candidates.
2. **Porting Implementation**:
   - Server-side: Simplified proxy IP query extraction (`?proxyip=ip:port` or `/proxyip=ip:port`) with direct dialing.
   - Client-side: `speedtest.py` offloads DoH querying and candidate pool generation to client preprocessing, testing both direct and proxy IP routes to evaluate route performance.

### 2.7 Feature 7: SOCKS5 and HTTP Forward Proxy Chaining (SOCKS5/HTTP chain)

1. **Mechanism in `_worker.js`**:
   - `socks5Connect(targetHost, targetPort, initialData, TCP连接, parsedSocks5)` (Lines 3134-3168):
     * Connects to SOCKS5 server via `TCP连接({ hostname, port })`.
     * Step 1 (Method Negotiation, L3138): Sends `[0x05, 0x02, 0x00, 0x02]` (User/Pass + No Auth) or `[0x05, 0x01, 0x00]`.
     * Step 2 (Auth Subnegotiation, L3144-L3151): If selected method is `0x02`, encodes username/password into `[0x01, uLen, ...user, pLen, ...pass]` and asserts response `[0x01, 0x00]`.
     * Step 3 (Connect Request, L3153-L3157): Sends `[0x05, 0x01, 0x00, 0x03, domainLen, ...domain, portHigh, portLow]` and asserts response `[0x05, 0x00, ...]`.
     * Step 4 (Payload Flush, L3159): Writes initial payload and returns active socket.
   - `httpConnect(targetHost, targetPort, initialData, HTTPS代理, TCP连接, parsedSocks5)` (Lines 3170-3226):
     * Connects to HTTP proxy and sends `CONNECT targetHost:targetPort HTTP/1.1\r\nHost: targetHost:targetPort\r\nProxy-Authorization: Basic ...\r\n\r\n`.
     * Parses HTTP response header (up to 8192 bytes), validates HTTP 2xx status, and flushes initial payload.
   - `httpsConnect(...)` (Lines 3228-3327): Connects over TLS to HTTPS forward proxy.
   - Routing Gate (Lines 2432-2440 in `connecttoPry`):
     * Evaluates: `if (ctx代理类型 && (ctx代理全局 || SOCKS5白名单.some(p => new RegExp(...).test(host))))`.
     * Whitelist: `SOCKS5白名单` initialized at Line 3 (`['*tapecontent.net', '*cloudatacdn.com', '*loadshare.org', '*cdn-centaurus.com', 'scholar.google.com']`).
     * If matched, routes through `socks5Connect` or `httpConnect`.
2. **Porting Implementation**:
   - Outbound chaining enables edge nodes to tunnel egress through secondary VPS or cloud proxies (e.g. Cloudflare ingress -> AWS/Supabase egress).
   - In Northflank Go: Implemented via standard `golang.org/x/net/proxy` (`proxy.SOCKS5("tcp", addr, auth, forward)`).
   - In Node.js (Wasmer): Implemented via `socks` or `http-proxy-agent`.
   - In Supabase Deno: Implemented via lightweight SOCKS5 handshake function.

### 2.8 Feature 8: Camouflage and Anti-Probe Architecture (伪装页面)

1. **Mechanism in `_worker.js`**:
   - `nginx()` (Lines 6522-6550): Returns HTTP 200 OK with standard Nginx "Welcome to nginx!" HTML template.
   - `html1101()` (Lines 6552-6627): Returns Cloudflare Error 1101 simulation containing real-time UTC timestamp, dynamic 16-hex Ray ID generated via `crypto.getRandomValues`, client IP from `request.headers.get('cf-connecting-ip')`, and official Cloudflare error CSS links.
   - Reverse Proxy Upstream (Lines 4, Lines 120-135): Forwards unmatched HTTP GET requests to `Pages静态页面 = 'https://edt-pages.github.io'` or `env.URL`, rewriting `Host`, `Origin`, and `Referer` headers.
2. **Porting Implementation**:
   - Preserved in `configs/wasmer/server.js` and `configs/supabase/functions/edgetunnel/index.ts`.
   - Any non-WebSocket HTTP request or request without valid authentication receives the camouflage response, preventing active scanning probes from identifying the endpoint as a proxy gateway.

### 2.9 Feature 9: Path Parameters and URL Routing (路径参数)

1. **Mechanism in `_worker.js`**:
   - URL Normalization (Lines 19-26 in `fetch`): Strips escaped backslashes `%5C`, isolates URL anchors `#`, and normalizes `%3F` query delimiters.
   - `获取传输路径参数值(pathname, prefix)` (Lines 4810-4815): Matches route prefixes.
   - `反代参数获取(url, env)` (Lines 6171-6305): Extracts `/proxyip=...`, `?proxyip=...`, `/pyip=...`, `/ip=...`, `/sub`, `/version`, and `/clean` parameters.
2. **Porting Implementation**:
   - Direct runtimes support dynamic query parsing via standard `new URL(req.url)`.
   - Probing pipelines dynamically format paths (e.g. `/?ed=2560&proxyip=...`) to test different upstream paths and early data options.

### 2.10 Feature 10: Error Closing and Socket Lifecycle Teardown (错误关闭)

1. **Mechanism in `_worker.js`**:
   - `closeSocketQuietly(socket)` (Lines 2507-2513):
     ```javascript
     function closeSocketQuietly(socket) {
         try {
             if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CLOSING) {
                 socket.close();
             }
         } catch (error) { }
     }
     ```
     Guards socket state and suppresses unhandled exceptions during closure.
   - Connection Generation Invalidation (`失效TCP连接世代`, Lines 789-798): Increments generation counter to discard stale async callbacks when a connection is aborted.
   - Teardown in `connectStreams` (Lines 3074-3082, Line 3093):
     * Executes in `finally` block: `reader.cancel()`, `reader.releaseLock()`, `remoteSocket.close()`, and `closeSocketQuietly(webSocket)`.
   - Failure Teardown in `connecttoPry` (Lines 2411-2418):
     * If dialing fails, ensures `newSocket?.close()`, sets `remoteConnWrapper.socket = null`, and calls `closeSocketQuietly(ws)`.
2. **Porting Implementation**:
   - Implemented across all platform runtimes (`server.js`, `index.ts`, `main.go`).
   - Sockets on both sides (edge WebSocket and outbound TCP socket) are bound by lifecycle event listeners (`close`, `error`, `end`), ensuring that closure of one side immediately tears down the remote side without leaking file descriptors.

---

## 3. Mandatory 10-Feature Function-Level Porting Map Table

The table below provides the function-level mapping between `_worker.js` and `fastly-edge-speedtest`, covering all 10 core features:

| 原函数名 | 移植位置 | 是否保留 | 替代实现 | 等价测试 |
| :--- | :--- | :--- | :--- | :--- |
| `解析魏烈思请求` (L1964-L2012) | `wasmer/server.js:parseVlessHeader`<br>`supabase/index.ts:parseVlessHeader`<br>`northflank/main.go:parseVless` | 保留并适配 | 保持 VLESS 协议规范: Byte 0 版本 (0x00), Bytes 1-16 UUID, Addons 长度, Command (0x01=TCP), Port 大端解析, 地址类型 (1=IPv4, 2=Domain, 3=IPv6); 适配各平台 Buffer / Uint8Array / Go byte slice。 | `tests/test_edgetunnel_compat.py::test_parse_vless_header_valid`<br>`test_sb_vless.py`<br>`test_nf_vless.py` |
| `获取UUID字节` (L1934-L1953)<br>`UUID字节匹配` (L1955-L1962)<br>`MD5MD5` (L5402-L5415) | `wasmer/server.js:matchUuid`<br>`supabase/index.ts:compareUuid`<br>`uuid_config.json` | 替代重构 | 废弃脆弱的 MD5MD5 动态派生，改用 `uuid_config.json` 为各运行时预配强随机 RFC 4122 UUID v4; 字节比对采用常量时间比对 (`Buffer.equals`, `ConstantTimeCompare`) 防御时序侧信道。 | `tests/test_edgetunnel_compat.py::test_uuid_constant_time_match`<br>`tests/test_edgetunnel_compat.py::test_parse_vless_header_invalid_uuid` |
| `处理WS请求` (L1290-L1787)<br>`connectStreams` (L3026-L3094)<br>`创建上行Grain合包流` (L2601-L2680)<br>`创建下行Grain发送器` (L2826-L3024) | `wasmer/server.js:handleUpgrade`<br>`supabase/index.ts:handleWebSocket`<br>`northflank/main.go:handleWS` | 替代重构 | 剥离 Cloudflare 专属 `new WebSocketPair()`; 在 Wasmer 中使用 Node `http.createServer` upgrade 事件与 raw socket 桥接; 在 Supabase 中使用 `Deno.upgradeWebSocket`; 在 Northflank 中使用 Go websocket 库与 TCP conn 双向 copy。 | `tests/test_direct_runtimes.py::test_rfc6455_handshake`<br>`tests/test_deno_proxy.py::test_supabase_entry`<br>`speedtest.py:probe_candidate_multilayer` |
| `解码WS早期数据` (L1260-L1287)<br>`是有效WS早期数据` (L1248-L1258) | `wasmer/server.js:decodeEarlyData`<br>`supabase/index.ts:decodeEarlyData`<br>`speedtest.py:pack_early_data` | 保留并适配 | 从 `Sec-WebSocket-Protocol` 提取 Base64URL early-data; 强制执行 8192 字节上限防御; 解码后校验 >=18 字节及 UUID; 在建立出站连接前将数据作为 `initialData` 发送; 客户端在 URL 追加 `?ed=2560` 触发。 | `tests/test_edgetunnel_compat.py::test_early_data_base64url_decode`<br>`tests/test_edgetunnel_compat.py::test_early_data_length_overflow`<br>`speedtest.py:test_early_data_roundtrip` |
| `创建请求TCP连接器` (L3329-L3334)<br>`打开TCP连接` (L2223-L2233)<br>`connectDirect` (L2295-L2316) | `wasmer/server.js:net.connect`<br>`supabase/index.ts:Deno.connect`<br>`northflank/main.go:net.Dialer` | 平台重写 | 彻底移除 Cloudflare 专有 `request.fetcher.connect`; 在 Node.js 使用 `net.connect({ host, port })`; 在 Deno 使用 `Deno.connect({ hostname, port })`; 在 Go 使用 `net.Dialer{Timeout}.Dial("tcp", target)`。 | `tests/test_direct_runtimes.py::test_node_net_connect`<br>`tests/test_deno_proxy.py::test_deno_connect_tcp`<br>`verify_all_deployments.py` |
| `connectProxyIP` (L2318-L2350)<br>`解析地址端口` (L6437-L6451)<br>`DoH查询` (L5437-L5595) | `wasmer/server.js:connectProxyIP`<br>`speedtest.py:resolve_proxyip_doh`<br>`generate_all_pools.py` | 拆分重构 | 服务端仅保留轻量级 ProxyIP 转发与失败回退直连 (`if (启用反代失败兜底) return connectDirect(...)`); 复杂 DoH TXT 查询、LCG 乱序与候选池维护前移至客户端测速流水线 (`speedtest.py`) 离线预处理。 | `tests/test_edgetunnel_compat.py::test_proxyip_url_injection`<br>`tests/test_edgetunnel_compat.py::test_doh_txt_resolution`<br>`geo_gate_verify.py` |
| `socks5Connect` (L3134-L3168)<br>`httpConnect` (L3170-L3226)<br>`httpsConnect` (L3228-L3327)<br>`获取SOCKS5账号` (L6313-L6344) | `northflank/main.go:dialSocks5`<br>`wasmer/server.js:socks5Agent`<br>`supabase/index.ts:socks5Connect` | 保留并标准化 | 完整保留 SOCKS5 协商握手 (Method 0x00/0x02, Auth 0x01, Connect 0x05 0x01 0x00 0x03) 与 HTTP CONNECT 代理链; Go 采用 `golang.org/x/net/proxy`; Node 采用 `socks` 代理库; 实现出站出口重定向与防封锁链式代理。 | `tests/test_edgetunnel_compat.py::test_socks5_handshake_chain`<br>`tests/test_edgetunnel_compat.py::test_http_connect_chain`<br>`independent_audit_verify.py` |
| `nginx` (L6522-L6550)<br>`html1101` (L6552-L6627)<br>反代上游页面 (L4, L120-L135) | `wasmer/server.js:serveCamouflage`<br>`supabase/index.ts:serveCamouflage`<br>`configs/fastly/routing.vcl` | 保留并精简 | 非代理请求或未通过 UUID 鉴权请求，返回标准 Nginx 200 OK 页面或模拟 Cloudflare Error 1101 (动态伪造 Ray ID、时间戳、客户端 IP); Fastly VCL 配置回源伪装网站，彻底掩盖网关特征。 | `tests/test_edgetunnel_compat.py::test_nginx_welcome_camouflage`<br>`tests/test_edgetunnel_compat.py::test_html1101_camouflage_headers`<br>`check_wasmer_status.py` |
| URL规范化 (L19-L26)<br>`获取传输路径参数值` (L4810-L4815)<br>`反代参数获取` (L6171-L6305) | `wasmer/server.js:extractParams`<br>`supabase/index.ts:extractParams`<br>`speedtest.py:inject_proxyip_path` | 保留并精简 | 保持对 `/proxyip=ip:port` 与 `?proxyip=ip:port` 以及 `?ed=2560` 的解析能力; 剥离冗余历史兼容分支，采用标准 URL 查询参数与正则提取。 | `tests/test_edgetunnel_compat.py::test_extract_path_token`<br>`tests/test_edgetunnel_compat.py::test_parse_proxy_url` |
| `closeSocketQuietly` (L2507-L2513)<br>`失效TCP连接世代` (L789-L798)<br>`connectStreams.finally` (L3074-L3082) | `wasmer/server.js:teardownSockets`<br>`supabase/index.ts:cleanupSockets`<br>`northflank/main.go:deferClose` | 保留并增强 | 保留静默安全关闭状态判断 (`readyState === OPEN || CLOSING`); 强化双端生命周期监听，一旦任意一端发生 EOF、网络异常或重置，必须在 `finally` 块立即关闭对端 socket，严防文件描述符泄漏与悬空连接。 | `tests/test_edgetunnel_compat.py::test_socket_graceful_teardown`<br>`tests/test_edgetunnel_compat.py::test_remote_eof_ws_closure`<br>`verify_all_deployments.py` |

---

## 4. Runtime Incompatibility Analysis and Adaptation Table

Attempting to deploy `_worker.js` directly onto non-Cloudflare edge runtimes fails due to proprietary APIs:

```
+------------------------+------------------------------------+-----------------------------------+
| Platform               | Proprietary Cloudflare API         | Native Platform Equivalent        |
+------------------------+------------------------------------+-----------------------------------+
| Cloudflare Workers     | connect() / cloudflare:sockets     | Native                            |
| Wasmer (Node.js / WASI)| request.fetcher.connect            | require('net').connect            |
| Supabase Edge (Deno)   | new WebSocketPair()                | Deno.upgradeWebSocket(req)        |
| Supabase Edge (Deno)   | connect()                          | Deno.connect({ hostname, port })  |
| Northflank (Go)        | Cloudflare JS runtime              | net.Dialer / singbox-lite binary  |
| Tencent EdgeOne        | Raw outbound TCP socket            | NOT SUPPORTED (L7 Frontend Only)  |
| Fastly Compute         | Dynamic arbitrary TCP socket       | Static Backend via fastly:backend |
+------------------------+------------------------------------+-----------------------------------+
```

### 4.1 Strict Architectural Constraints
1. **Zero Cloudflare API Bleed-Through**: No code deployed to Wasmer, Supabase, Northflank, Fastly, or EdgeOne may import `cloudflare:sockets` or reference `request.cf`.
2. **Deterministic Early Data Termination**: The server-side WebSocket handler must accept both buffered 0-RTT early data and standard WebSocket binary frames interchangeably.
3. **Strict Socket Lifecycle Guards**: When the outbound TCP socket encounters an error or reaches EOF, the edge WebSocket must be closed with standard closure codes (1000 or 1006). Remote sockets must be destroyed immediately.

---

## 5. Equivalent Verification Test Matrix

To guarantee 100% behavioral equivalence across the ported logic, the test suite verifies:

1. `test_parse_vless_header_valid`: Packs synthetic VLESS binary frame (Version 0, matching UUID, Command 1, Port 443, Domain `example.com`), verifies extracted fields.
2. `test_parse_vless_header_invalid_uuid`: Supplies mismatched UUID, asserts authentication failure.
3. `test_early_data_base64url_decode`: Encodes valid VLESS packet as base64url, passes to decoder, asserts byte equality.
4. `test_early_data_length_overflow`: Supplies base64url string exceeding 8192 decoded bytes, asserts rejection.
5. `test_uuid_constant_time_match`: Benchmarks UUID matching logic to verify constant-time execution characteristics.
6. `test_socks5_handshake_chain`: Verifies full SOCKS5 handshake (Methods, Auth, Connect) with mock upstream.
7. `test_proxyip_url_injection`: Asserts query `?proxyip=` correctly redirects target connection.
8. `test_socket_graceful_teardown`: Simulates remote server abort, asserts local WebSocket receives clean close frame.
