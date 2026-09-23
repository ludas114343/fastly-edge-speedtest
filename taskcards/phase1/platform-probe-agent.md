# TaskCard: taskcards/phase1/platform-probe-agent.md

## 1. 背景
V12 重构要求严禁根据历史推测或博客经验断言，必须对 Netlify, Fastly, EdgeOne 执行真实探针测试，获取物理原始返回。

## 2. 唯一目标
1. Netlify 实测：N1 (typeof Deno.connect), N2 (Deno.connect 拨号 TCP echo), N3 (入站 WS Upgrade 函数接管), N4 (双向二进制 WS 保持 60s), N5 (WS 接收地址后 TCP 拨号并回传)。
2. Fastly 实测：F1 (Compute service), F2 (绑定自有域名), F3 (WebSocket 权限), F4 (WebSocket handoff 到自有 origin), F5 (保持双向 WS 60s), F6 (Raw TCP socket API 存在性), F7 (dynamic backend 是否支持原始 TCP)。
3. EdgeOne 实测：E1 (Edge Function fetch), E2 (Node Functions node:net), E3 (node:net 连接 TCP echo), E4 (Node Functions 接管 WS), E5 (双向二进制 WS 60s), E6 (L4 Proxy 权限), E7 (L4 TCP 转发), E8 (Site Acceleration WS 回源)。
4. 判定各平台三态：CAPABLE_DIRECT, CAPABLE_FRONT, 或 DISTRIBUTION_ONLY。

## 3. 输入路径
- `evidence/inventory/` 中的平台凭据与域名配置
- 探针源码目录：`configs/`

## 4. 允许操作
- 部署最小探针函数或调用 API 测试
- 记录原始返回与 HTTP 状态码

## 5. 禁止操作
- 严禁把普通 fetch 成功当成 Raw TCP 成功
- 严禁仅凭 WebSocket 类存在证明能接管入站 Upgrade
- 严禁在英文注释或文档中使用 em-dash (\u2014) 与 en-dash (\u2013)

## 6. 必须执行的命令或 API
- 部署命令或 HTTP/WebSocket 测试探针脚本

## 7. 必须生成的文件
- `docs/platform_capability_matrix.json`
- `docs/probes/netlify_raw.txt`
- `docs/probes/fastly_raw.txt`
- `docs/probes/edgeone_raw.txt`

## 8. 机器可判定验收条件
- `docs/platform_capability_matrix.json` 包含 netlify, fastly, edgeone 三大平台明确的枚举判定（CAPABLE_DIRECT, CAPABLE_FRONT, DISTRIBUTION_ONLY），附部署 ID、时间戳与原始返回哈希

## 9. 停止条件
原始日志落盘且能力矩阵 JSON 写入完成并验证格式合法后停止。
