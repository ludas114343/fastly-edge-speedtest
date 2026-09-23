# TaskCard S2-redteam-02 @taskcards/S2-redteam-02.md

## 背景（自含）
项目目录：C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest
后端在 S2-backend-02 中宣称已解决 EdgeOne HK 节点残留、旧 UUID 清理、Fastly 激活、去除虚假路径填充及 Worker 动态分发。
Red Team 必须执行第二轮对抗复查，验证整改是否真实、是否引入新漏洞。

## 唯一目标
对抗审查第二轮后端重修成果，实测 Fastly 激活状态与 EdgeOne 边界透明度，产出 orchestration/S2_redteam_report_v2.md 并给出终审判决 (PASS/FAIL)。

## 输入
- 6 套 YAML 文件
- wasmer_sub_updated.js
- speedtest.py
- Fastly Service 8K5HGyXmr8P6XuzRc5UPk0
- orchestration/S2_backend_report_v2.md

## 必须执行
1. 对抗复查 HK 节点清零情况：确认 EdgeOne 与 Worker fallback 中是否已真正清除所有 HK 节点。
2. 对抗复查 Fastly Service 状态：确认 Version 11 是否已真实 active。
3. 对抗复查人工路径填充移除：确认 &ed=2048 与 &region= 是否已被干净移除，物理去重是否真实可靠。
4. 对抗复查 Worker 动态分发逻辑：确认是否存在正则表达式替换漏洞或边界条件注入风险。
5. 检查破折号与敏感信息。
6. 产出 orchestration/S2_redteam_report_v2.md。

## 产出（全部落盘）
- C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\orchestration\S2_redteam_report_v2.md
