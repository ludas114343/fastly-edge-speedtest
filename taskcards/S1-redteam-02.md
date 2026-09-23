# TaskCard S1-redteam-02 @taskcards/S1-redteam-02.md

## 背景（自含）
项目目录：C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest
Red Team 首轮发出的 6 项致命缺陷已由 study 角色在 S1-study-02 中声称全量整改完毕。Red Team 必须针对整改后的三份文档进行第二轮对抗复查。

## 唯一目标
对照 S1_redteam_report.md 中的 6 条问题，逐一核验 study 角色是否彻底认账并完成技术纠偏，是否存在新形式的混淆或推诿，产出 S1_redteam_report_v2.md 并做出最终终审（PASS 或 FAIL）。

## 输入
- docs/edgetunnel_porting_map.md
- docs/trace_web_study.md
- docs/trace_web_porting_map.md
- orchestration/S1_redteam_report.md (首轮报告)

## 必须执行
1. 逐条核验首轮报告中 6 条致命缺陷的整改结果：
   - Issue 1: 运行时 API 锁定与多云 Socket 差异。
   - Issue 2: PROXYIP 虚标。
   - Issue 3: WS 101 虚假已实现。
   - Issue 4: 静态假测速公式废除与真 HTTP 测速要求。
   - Issue 5: 国内跳数路由与隧道出口国家区分。
   - Issue 6: 外部二进制真实依赖声明。
2. 审查给出的 Supabase Deno WebSocket/TCP Adapter 代码蓝图是否有语法或逻辑漏洞。
3. 扫描破折号与凭据安全。
4. 产出 orchestration/S1_redteam_report_v2.md。

## 产出（全部落盘）
- C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\orchestration\S1_redteam_report_v2.md

## 验收清单（逐条可判 PASS/FAIL）
1. 6 项缺陷整改情况逐一复核完毕。
2. 给出终审结论 (PASS/FAIL)。
