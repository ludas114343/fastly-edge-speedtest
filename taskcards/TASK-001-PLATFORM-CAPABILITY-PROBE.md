# 任务卡: TASK-001-PLATFORM-CAPABILITY-PROBE

- **任务名称**: 阶段 A - 平台能力探针真实部署与能力矩阵判定 (强制第一门禁)
- **指派角色**: probe (Subagent)
- **工作目录**: `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest`
- **依赖门禁**: TASK-000 探活通过

---

## 1. 任务背景与核心目标
在编写任何后端代码之前，必须通过平台最小能力探针真实部署到 Netlify、Fastly、EdgeOne 三个平台，测试其底层运行时对任意 TCP 拨号及 WebSocket 的真实支持情况，推翻或确认历史假设，落盘原始凭证与判定矩阵。

## 2. 必须做 (Strict Requirements)
1. **读取凭据**:
   - 从 Obsidian 库或本地凭据存储读取 Netlify (token/site)、Fastly (api_token/service_id)、EdgeOne (SecretId/SecretKey/site_id) 真实鉴权凭据。
   - 凭据仅在内存变量中使用，严禁打印到终端日志、代码提交或落盘文件。
2. **探针 A1: Netlify Edge Function (测 Deno.connect)**
   - 探针代码:
     ```javascript
     // netlify/edge-functions/tcp-test.js
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
   - 部署至 Netlify 站点，真实 HTTP GET 请求 `/tcp-test`，记录原始返回字符串、HTTP 状态码及运行日志。
3. **探针 A2: Fastly Compute (测 WS GA / 动态任意 host 拨号)**
   - 探针代码:
     ```javascript
     // src/index.js (Fastly Compute, JS SDK)
     addEventListener("fetch", (event) => event.respondWith(handleRequest(event.request)));
     async function handleRequest(req) {
       try {
         const resp = await fetch("https://example.com/", { backend: "test_backend" });
         return new Response("Backend fetch status: " + resp.status);
       } catch (e) {
         return new Response("FAILED: " + e.message);
       }
     }
     ```
   - 额外必测:
     a) 动态任意 host 拨号测试 (非 fastly.toml 预配置 backend，尝试直接 `fetch("https://1.1.1.1/")` 或非预定 backend)。
     b) WebSocket 全双工终结能力测试。
   - 部署至 Fastly Compute 服务，记录原始返回与判定。
4. **探针 A3: EdgeOne Node Functions (测 node:net 原生拨号与 L4)**
   - 探针代码:
     ```javascript
     // functions/api/tcp-test.js (Node Functions, Node.js v20)
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
   - 若 Node Functions 拨号失败，根据 Tencent EdgeOne 文档 (edgeone.ai/document/56430) 实测 L4 Proxy (四层 TCP/UDP) 转发能力。
5. **原始记录与判定落盘**:
   - 原始返回分别保存在 `docs/probes/netlify_raw.txt`, `docs/probes/fastly_raw.txt`, `docs/probes/edgeone_raw.txt`。
   - 汇总并编写 `docs/platform_capability_matrix.md`，逐平台判定三态之一:
     - `CAPABLE_DIRECT`: 平台原生可拨号任意 host:port → 做独立真后端 (自出站)
     - `CAPABLE_FRONT`: 只能终结入口/固定回源 → 做“入口层→真实后端 (Supabase/Wasmer/Northflank)”
     - `INCAPABLE`: 连接被沙盒拦截/超时/报错 → 不作出站节点，只做分发/伪装
   - 必须附带：原始返回字符串、部署日志摘要、运行时版本号、判定依据。

## 3. 禁止做 (Strict Prohibitions)
- 绝对禁止在无真实探针返回的情况下脑补或推测。
- 绝对禁止使用 Supabase / Cloudflare 冒充任何测不通的平台。
- 绝对禁止向代码库、Git 提交或日志输出包含真实 API Key / Token / Secret 的明文。
- 绝对禁止跳过探针直接开始编写 VLESS 业务后端代码。

## 4. 交付物与验收条件
- `docs/probes/netlify_raw.txt` 存在且包含 Netlify 真实返回。
- `docs/probes/fastly_raw.txt` 存在且包含 Fastly 真实返回。
- `docs/probes/edgeone_raw.txt` 存在且包含 EdgeOne 真实返回。
- `docs/platform_capability_matrix.md` 完整三态判定及证据。
