# TaskCard S1-study-01 @taskcards/S1-study-01.md

## 背景（自含）
项目目录：C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest
参考项目已克隆于：
- C:\Users\ludas\.gemini\antigravity\scratch\ref_projects\edgetunnel
- C:\Users\ludas\.gemini\antigravity\scratch\ref_projects\Trace-Web
本阶段为阶段 S1：参考源码深入研究与架构映射文档化。必须基于实际克隆的源码进行分析，禁止脑补或精神参考。

## 唯一目标
产出三份详实的映射研究报告：
1. docs/edgetunnel_porting_map.md
2. docs/trace_web_study.md
3. docs/trace_web_porting_map.md

## 输入
- 参考源码 1: C:\Users\ludas\.gemini\antigravity\scratch\ref_projects\edgetunnel\_worker.js
- 参考源码 2: C:\Users\ludas\.gemini\antigravity\scratch\ref_projects\Trace-Web\trace.py
- 本地工程目录: C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest

## 必须执行
1. 在 C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest 下创建 docs 目录。
2. 研读 edgetunnel\_worker.js，在 docs/edgetunnel_porting_map.md 中逐项给出以下特性的原函数名、行号与本项目采用/适配的具体文件与函数映射：
   - VLESS over WebSocket 协议解析与 0-RTT (?ed= / Sec-WebSocket-Protocol base64url)
   - UUID 鉴权与前 8 位校验逻辑
   - PROXYIP 环境变量与路径级动态切换 (/proxyip=xxx, ?proxyip=xxx)
   - URL 变量伪装机制 (env.URL, html1101, nginx 静态页反代)
   - ADDAPI 优选节点订阅与 Base64 聚合
3. 研读 Trace-Web\trace.py，在 docs/trace_web_study.md 中记录：
   - 候选 IP 格式与输入管道
   - 线路分类（电信/联通/移动/骨干）机制与与 nexttrace 联动
   - 指标体系（TCP RTT, TLS RTT, 丢包率, 抖动, 出口 ASN, ProxyIP）
   - 排序淘汰策略与权重模型
   - 在线优选与动态刷新流程
   - 若仓库内无预编译二进制（main.exe/nexttrace），如实记录边界与纯 Python 替代方案
4. 编写 docs/trace_web_porting_map.md，逐段给出 Trace-Web 逻辑到本项目 speedtest.py、geo_gate_verify.py 的移植实现点。
5. 确保文档语言严谨，禁止使用破折号 (em-dash)。

## 禁止事项
- 不得凭空臆测未在源码中出现的函数；
- 不得触碰用户本机网络/代理/TUN/Clash；
- 严禁任何凭据明文落盘。

## 产出（全部落盘）
- C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\docs\edgetunnel_porting_map.md
- C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\docs\trace_web_study.md
- C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\docs\trace_web_porting_map.md

## 验收清单（逐条可判 PASS/FAIL）
1. 三个文档全部真实落盘且不为空。
2. edgetunnel 映射文档中每个功能点均有 _worker.js 确切行号与函数名。
3. trace_web 映射文档明确指出本项目的对应调用与承接点。
4. 全文无破折号 (em-dash)。
