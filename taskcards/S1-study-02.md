# TaskCard S1-study-02 @taskcards/S1-study-02.md

## 背景（自含）
项目目录：C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest
第一轮 Red Team 对抗审查判定 FAIL，报告落盘于 orchestration/S1_redteam_report.md。
必须根据 Red Team 的硬核挑刺证据，全面重修 docs/ 下的三份研究与移植文档，严禁虚假声称"已完成"、严禁混淆概念。

## 唯一目标
彻底重修 docs/ 下的三份文档，消除所有虚报与假实现承诺，如实说明现状与阶段规划，达到 Red Team 验收标准：
1. docs/edgetunnel_porting_map.md
2. docs/trace_web_study.md
3. docs/trace_web_porting_map.md

## Red Team 原始失败证据清单（必须逐条彻底清零）
1. [致命运行时兼容性]: edgetunnel 的 _worker.js 严重依赖 Cloudflare Workers 特有 API（connect(), WebSocketPair, request.cf）。必须明确指出这些 API 在 Wasmer (WinterJS)、Tencent EdgeOne、Supabase (Deno) 上的真实差异，并给出各平台的适配层实现方案（Deno.connect, 标准 WebSocket, 或 Node net 模块），禁止宣称可直接通用。
2. [虚报 PROXYIP 现状]: 严禁在文档中宣称 speedtest.py 已实现 PROXYIP 注入或 DoH 解析（实际代码 0 行）。必须如实标注为"【阶段 S2/S3 计划实现】"，并给出具体函数规格设计。
3. [虚报 WS 101 现状]: 严禁声称 speedtest.py 已实现 WS 101 握手（当前仅有 TCP/TLS）。如实标注为"【阶段 S3 待重写项】"，并给出真实的 socket/ssl 发送 Upgrade: websocket 的纯 Python 代码蓝图。
4. [假测速公式曝光]: 承认并指出 speedtest.py 中静态推算带宽 (avg_rtt < 60 -> 35Mbps) 的伪测速缺陷，明确说明在阶段 S3 必须采用真实分块 HTTP 下载计时的替代实现。
5. [混淆路由与出口]: 澄清出口国家查询 (ipwho.is) 与国内三网路由 (CN2/9929/CMI) 的区别，明确 Actions Runner 内部自建 TUN 是为了测国内入口延迟，出口 ASN 则是测隧道落地归属。
6. [外部二进制矛盾]: 诚实纠正"零外部依赖"的不实表述，明确说明 geo_gate_verify.py 依赖沙箱 portable mihomo 验证，并说明其隔离性。

## 禁止事项
- 严禁将尚未编写的代码标记为"已实现"或"Complete"；
- 严禁模糊运行时差异；
- 全文严禁使用破折号 (em-dash)。

## 产出（全部落盘）
- C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\docs\edgetunnel_porting_map.md
- C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\docs\trace_web_study.md
- C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\docs\trace_web_porting_map.md

## 验收清单（逐条可判 PASS/FAIL）
1. 6 大虚假/兼容性缺陷全部修正到位。
2. 文档状态与实际代码现状 100% 诚实对应。
3. 全文 0 破折号。
