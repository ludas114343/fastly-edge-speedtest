# TaskCard S1-audit-code-02 @taskcards/S1-audit-code-02.md

## 背景（自含）
项目目录：C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest
研究文档已经历第二轮重修，落地于 docs/。本任务卡核查 S1-study-02 是否如实落实了对 6 大缺陷的修正。

## 唯一目标
复核 docs/edgetunnel_porting_map.md、trace_web_study.md、trace_web_porting_map.md，确认所有前述错误表述已彻底清除，输出 S1_audit_report_v2.md 并给出裁决。

## 输入
- docs/edgetunnel_porting_map.md
- docs/trace_web_study.md
- docs/trace_web_porting_map.md
- orchestration/S1_redteam_report.md

## 必须执行
1. 检查 docs/edgetunnel_porting_map.md 是否明确将 PROXYIP 标注为 Planned for Phase S2，而非 Complete。
2. 检查 trace_web_porting_map.md 是否明确将 WS 101 握手标注为 Pending Rewrite in Phase S3，并删除了声称当前已实现的虚假断言。
3. 检查是否严正废除了 static RTT 估算带宽的公式。
4. 检查是否诚实记录了 geo_gate_verify.py 对沙箱 mihomo 二进制的依赖。
5. 正则扫描三份文档中的破折号 (\u2014, \u2013)，要求 count == 0。
6. 产出 orchestration/S1_audit_report_v2.md。

## 产出（全部落盘）
- C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\orchestration\S1_audit_report_v2.md

## 验收清单（逐条可判 PASS/FAIL）
1. 虚假完成标注已 100% 纠正为计划项。
2. 零破折号。
3. 给出 PASS/FAIL 明确判定。
