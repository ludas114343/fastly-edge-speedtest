# TaskCard S1-redteam-01 @taskcards/S1-redteam-01.md

## 背景（自含）
项目目录：C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest
研究文档已由 study 角色产出并由 audit-code 审查。Red Team 必须以对抗视角进行深度挑刺与证伪。

## 唯一目标
对 docs/ 下三份研究报告执行对抗审查，寻找虚构、不可落地、假参考、破折号违规或安全漏洞，产出 S1_redteam_report.md 并给出 PASS/FAIL。

## 输入
- docs/edgetunnel_porting_map.md
- docs/trace_web_study.md
- docs/trace_web_porting_map.md
- 参考项目源码目录: C:\Users\ludas\.gemini\antigravity\scratch\ref_projects\

## 必须执行
1. 对抗审查 Trace-Web 移植可行性：是否诚实指出了缺少 Go 编译产物的问题？给出的 Python 替代方案是否有技术可行性漏洞？
2. 对抗审查 edgetunnel 伪装与 PROXYIP 方案：是否把 Cloudflare 特有 API（如 connect()）硬套在非 CF 平台（如 Wasmer/Tencent EdgeOne）上？是否给出了各平台的真实运行时适配方案？
3. 检查是否有任何空洞泛化的描述或无法落地的假实现承诺。
4. 全文检索破折号与凭据泄露风险。
5. 产出 S1_redteam_report.md。

## 产出（全部落盘）
- C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\orchestration\S1_redteam_report.md

## 验收清单（逐条可判 PASS/FAIL）
1. 挑刺点有具体技术依据。
2. 给出明确结论 (PASS 或 FAIL)。
