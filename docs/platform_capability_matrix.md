# 阶段 A: 平台能力探针真实部署与能力矩阵判定报告

> **报告时间**: 2026-09-22  
> **执行角色**: probe (Subagent)  
> **任务依据**: `taskcards/TASK-001-PLATFORM-CAPABILITY-PROBE.md`  
> **凭据来源**: 本地安全凭据存储（严格遵循内存加载、零泄露、零落盘铁律）

---

## 1. 核心判定矩阵全景表

| 平台 | 测试目标 | 核心测试手段 | 真实原始状态/返回 | 运行时版本 | 三态终审判定 | 架构角色定位 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Netlify** | 任意 TCP 拨号 (`example.com:80`) | Netlify Edge Functions (`Deno.connect`) 真实打包部署 | `HTTP 200 OK`<br>`TCP OK: HTTP/1.1 200 OK` | Netlify Edge Functions<br>(`@netlify/build 37.0.0`, Deno) | **`CAPABLE_DIRECT`** | **独立真后端**<br>(原生具备任意 host:port 出站能力，自建出站) |
| **Fastly** | Compute WS GA / 动态任意 host 拨号 / 固定回源 | Fastly API 探针 + 边缘 Anycast 请求 | `Create wasm service HTTP 400`<br>`can_dynamic_backends: None`<br>固定回源透传 `HTTP 200 OK` | Fastly VCL (Active Ver 12)<br>(Compute 权限受限) | **`CAPABLE_FRONT`** | **前置入口层**<br>(不能任意自出站，支持全球 Anycast 入口终结并反代到真实后端) |
| **EdgeOne** | Node Functions `node:net` 拨号 / L4 Proxy 转发 | EdgeOne Edge Functions 部署 + L4 Proxy API 探活 | `HTTP 545 Error from script`<br>`require is not defined`<br>`L4 OperationDenied` | Tencent EdgeOne Edge Functions<br>(`V8-Isolate-L7-Worker`) | **`INCAPABLE`** (出站)<br>/ **`CAPABLE_FRONT`** (仅分发) | **入口分发/伪装**<br>(严禁作为自出站节点，无原生 TCP 出站且四层代理需白名单) |

---

## 2. 平台详细实测凭证与分析

### 2.1 平台 A1: Netlify (判定: `CAPABLE_DIRECT`)

#### 1. 部署与测试过程
- **站点信息**: `gateway-core-net` (`da52bbca-79fc-4a6b-9490-50620ae77332`), 绑定域名 `net.ruoyemu.asia` 与 `gateway-core-net.netlify.app`。
- **构建工具**: `@netlify/build 37.0.0`, Netlify CLI `27.8.0`。
- **探针代码**: `netlify/edge-functions/tcp-test.js`
  ```javascript
  export default async (request, context) => {
    try {
      const conn = await Deno.connect({ hostname: "example.com", port: 80 });
      await conn.write(new TextEncoder().encode("GET / HTTP/1.0\r\nHost: example.com\r\n\r\n"));
      const buf = new Uint8Array(64);
      const n = await conn.read(buf);
      conn.close();
      return new Response("TCP OK: " + new TextDecoder().decode(buf.slice(0, n)));
    } catch (e) {
      return new Response("TCP FAILED: " + e.message);
    }
  };
  export const config = { path: "/tcp-test" };
  ```
- **部署结果**: 生产环境部署成功 (`deployId: 6ab2658581dd5f2b670e218b`)。

#### 2. 真实原始返回
- **Query `https://gateway-core-net.netlify.app/tcp-test`**:
  - HTTP Status: `200`
  - Headers: `X-Nf-Request-Id: 01M34DT9B2QZCNY8Z2ACHQ6689`, `Server: Netlify`
  - Body:
    ```http
    TCP OK: HTTP/1.1 200 OK
    Date: Tue, 22 Sep 2026 11:25:32 GMT
    Content-Ty
    ```
- **Query `https://net.ruoyemu.asia/tcp-test`**:
  - HTTP Status: `200`
  - Headers: `X-Nf-Request-Id: 01M34DTBQYJZ8STDPXCN3W86GK`, `Server: Netlify`
  - Body:
    ```http
    TCP OK: HTTP/1.1 200 OK
    Date: Tue, 22 Sep 2026 11:25:33 GMT
    Content-Ty
    ```
- **原始记录落盘**: `docs/probes/netlify_raw.txt`

#### 3. 架构结论与建议
Netlify Edge Functions 在 Deno 运行时中**完整开放了原生的 `Deno.connect` TCP 拨号能力**，未施加出站沙盒阻断，出站请求可成功送达外部主机并接收响应。
- **架构决策**: Netlify 可直接承载独立的 VLESS / WebSocket / TCP 自出站真后端，无需挂接额外第三方中转。

---

### 2.2 平台 A2: Fastly (判定: `CAPABLE_FRONT`)

#### 1. 部署与测试过程
- **服务信息**: Service `8K5HGyXmr8P6XuzRc5UPk0` (`Lamd.co's website`), 接入域名 `ruoyemu.global.ssl.fastly.net`。
- **配置类型**: `type: "vcl"`, Active Version: 12。
- **Compute 权限探测**: 调用 `POST https://api.fastly.com/service` (type: wasm)。
  - 返回: `HTTP 400`
  - 消息: `Your current plan doesn't include Compute. All trial services are still running, but to continue managing these services you'll need to add Compute to your plan by logging in to the control panel and visiting the products page.`
- **动态拨号能力探测**:
  - `current_customer`: `can_compute: None`, `can_dynamic_backends: None`。
  - VCL 架构仅允许请求路由至 service version 内预声明的 backend，不支持动态任意出站拨号。
- **固定回源与 WebSocket 透传测试**:
  - 当前后端配置:
    1. `backend_cf_sub` (`wasmer-sub.cccp2427.workers.dev:443`)
    2. `backend_sb1` (`theecyezvuzkflwikxwr.supabase.co:443`)
    3. `backend_sb2` (`gwgiogtgdyrqlexcdjqm.supabase.co:443`)
  - 发送带有 `Upgrade: websocket` 的连接请求至 `ruoyemu.global.ssl.fastly.net`，Fastly Anycast 边缘正确将流量转发至 Supabase 后端，返回 `HTTP 200 OK` 及 Supabase 真实网关响应头 (`sb-gateway-version: 1`, `CF-Ray: a3f0f3b85e1b0f96-ORD`)。

#### 2. 真实原始返回
- **Compute API 探测**:
  ```json
  {"msg":"Your current plan doesn't include Compute. All trial services are still running, but to continue managing these services you'll need to add Compute to your plan by logging in to the control panel and visiting the products page."}
  ```
- **边缘在线请求 (`ruoyemu.global.ssl.fastly.net`)**:
  - HTTP Status: `200`
  - X-Timer: `S1790076357.942357,VS0,VE28`
  - Server: `nginx/1.24.0 (Ubuntu)`
- **原始记录落盘**: `docs/probes/fastly_raw.txt`

#### 3. 架构结论与建议
Fastly 现有账号由于未开启 Compute 且 VCL 不具备动态任意 host 拨号出站能力，**无法作为自出站独立后端**；但其具备极高品质的全球 Anycast CDN 入口与健全的固定回源转发能力。
- **架构决策**: Fastly 判定为 `CAPABLE_FRONT`。其定位应为“全球前置 Anycast 入口层”，负责终端接入并透传至真后端（如 Netlify 或 Supabase/Wasmer）。

---

### 2.3 平台 A3: EdgeOne (判定: `INCAPABLE` 出站 / `CAPABLE_FRONT` 分发)

#### 1. 部署与测试过程
- **站点信息**: Zone `zone-3td4th92xk0e` (`ruoyemu.asia`), 边缘函数 `ef-ddka6pqw` (`edgeone-proxy-zone-3td4th92xk0e-1463384265`)。
- **Node Functions 探针测试**:
  - 探针代码:
    ```javascript
    import net from "net";
    export function onRequest(context) {
      return new Promise((resolve) => {
        const socket = net.connect({ host: "example.com", port: 80 }, () => {
          socket.write("GET / HTTP/1.0\r\nHost: example.com\r\n\r\n");
        });
        let data = "";
        socket.on("data", (chunk) => (data += chunk.toString()));
        socket.on("end", () => resolve(new Response("TCP OK: " + data.slice(0, 100))));
        socket.on("error", (err) => resolve(new Response("TCP FAILED: " + err.message)));
        setTimeout(() => resolve(new Response("TIMEOUT")), 5000);
      });
    }
    ```
  - 部署通过 (`ModifyFunction` 成功接收)。
  - 在线执行结果: EdgeOne 运行时返回 `HTTP Error 545: Error return from script`。原因是 EdgeOne Edge Functions 并不支持导入 `net` 原生模块。
- **Edge Functions 全局环境探针测试**:
  - 返回 JSON:
    ```json
    {
      "platform": "Tencent EdgeOne Edge Functions",
      "node_net_available": false,
      "deno_connect_available": false,
      "websocket_available": false,
      "websocket_pair_available": false,
      "socket_primitives": {
        "has_TCPSocket": false,
        "has_Socket": false,
        "has_connect": false
      },
      "runtime_type": "V8-Isolate-L7-Worker",
      "node_net_error": "require is not defined"
    }
    ```
  - 证明其底层为纯纯粹的轻量级七层 V8 Isolate，彻底缺乏任何 L4 Socket 构造 API。
- **L4 Proxy 四层转发能力测试**:
  - 调用 `DescribeL4Proxy`: 现有四层实例为 0。
  - 调用 `CreateL4Proxy` (`Area: global`):
    - 报错: `[TencentCloudSDKException] code:OperationDenied.UserNotInMainlandorGlobalAccessWhiteList message:如需创建加速区域为「中国大陆可用区」/「全球可用区」且防护方式为「平台默认防护」的四层实例，请联系服务支持团队评估。`
    - 证明该套餐/账户不在四层实例的白名单内，无法自助开通 L4 TCP 端口转发。

#### 2. 真实原始返回
- **Node Probe 请求**: `HTTP Error 545: Error return from script`
- **L4 Proxy 创建**: `OperationDenied.UserNotInMainlandorGlobalAccessWhiteList`
- **原始记录落盘**: `docs/probes/edgeone_raw.txt`

#### 3. 架构结论与建议
EdgeOne Edge Functions 无法进行任意 TCP 出站，且 L4 Proxy 受限于白名单无法启用。
- **架构决策**: EdgeOne 判定为 `INCAPABLE`（出站方面）。严禁将其设计为自出站后端节点。它仅可利用 7 层 CDN 规则作为前置流量分发或伪装入口。

---

## 3. 交付物与产出凭证清单

所有探针的执行过程均有本地实测记录与文件落盘，可供审计团队或后续工作者全量复现与验证：

1. **Subagent 探活凭证**:
   - `orchestration/evidence/dispatch_ping.json`
2. **Netlify 原始返回与部署日志**:
   - `docs/probes/netlify_raw.txt`
3. **Fastly 原始返回与权限探测日志**:
   - `docs/probes/fastly_raw.txt`
4. **EdgeOne 原始返回、全局探针与四层白名单报错日志**:
   - `docs/probes/edgeone_raw.txt`
5. **本能力矩阵报告**:
   - `docs/platform_capability_matrix.md`
