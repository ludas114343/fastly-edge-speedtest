# TaskCard S1-audit-code-01 @taskcards/S1-audit-code-01.md

## 背景（自含）
项目目录：C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest
研究产物已落盘于 docs/ 目录：
- docs/edgetunnel_porting_map.md
- docs/trace_web_study.md
- docs/trace_web_porting_map.md
参考源码目录：
- C:\Users\ludas\.gemini\antigravity\scratch\ref_projects\edgetunnel\_worker.js
- C:\Users\ludas\.gemini\antigravity\scratch\ref_projects\Trace-Web\trace.py

## 唯一目标
独立核验 docs/ 下三份映射研究报告的真实性、源码行号引用吻合度与合规性，输出 S1_audit_report.md 并给出 PASS/FAIL。

## 输入
- C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\docs\edgetunnel_porting_map.md
- C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\docs\trace_web_study.md
- C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\docs\trace_web_porting_map.md
- C:\Users\ludas\.gemini\antigravity\scratch\ref_projects\edgetunnel\_worker.js
- C:\Users\ludas\.gemini\antigravity\scratch\ref_projects\Trace-Web\trace.py

## 必须执行
1. 检查三个 markdown 文件是否存在且非空（文件大小 > 5KB）。
2. 抽查 edgetunnel_porting_map.md 中提及的至少 5 处 _worker.js 源码函数与行号（如 VLESS解析、0-RTT解码、PROXYIP解析、html1101、UUID检验），对比真实 _worker.js 确认代码真实存在且逻辑吻合。
3. 抽查 trace_web_study.md 中提及的 trace.py 源码点（如缺少二进制的发现、指标字段、expand计算），确认其与真实 trace.py 一致。
4. 全文正则检索三个文档，验证是否存在破折号 (em-dash, \u2014) 或任何敏感凭据泄露。
5. 结果落盘至 orchestration/S1_audit_report.md。

## 禁止事项
- 不得直接沿用 study-subagent 的自述，必须亲自读取源文件验证行号；
- 严禁触碰用户本机网络/代理/Clash。

## 产出（全部落盘）
- C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\orchestration\S1_audit_report.md

## 验收清单（逐条可判 PASS/FAIL）
1. 行号抽查吻合率 100%。
2. 全文 0 破折号 (em-dash)。
3. S1_audit_report.md 明确给出 PASS 判定。
