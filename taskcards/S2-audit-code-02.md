# TaskCard S2-audit-code-02 @taskcards/S2-audit-code-02.md

## 背景（自含）
项目目录：C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest
后端施工已完成第 2 轮整改，产出报告于 orchestration/S2_backend_report_v2.md。
本任务卡核查 S2-backend-02 的整改是否彻底消除首轮发现的所有问题。

## 唯一目标
机器级核验 6 套 YAML、speedtest.py 与 wasmer_sub_updated.js，产出 orchestration/S2_audit_report_v2.md 并给出 PASS/FAIL 结论。

## 输入
- 6 套 YAML 文件
- speedtest.py
- wasmer_sub_updated.js
- uuid_config.json

## 必须执行
1. 全库 HK 清零核验：
   - 检索全部 6 套 YAML 以及 wasmer_sub_updated.js 中的全部内容，确认 "🇭🇰"、"香港"、"\bHK\b" 出现次数 == 0。
2. 节点数量硬门禁核验：
   - clash_fastly.yaml >= 34
   - clash_wasmer.yaml >= 34
   - clash_netlify.yaml >= 34
   - clash_edgetunnel.yaml >= 34
   - clash_edgeone.yaml == 36
   - clash.yaml >= 34
3. 旧 UUID 清零核验：
   - 检索 speedtest.py、YAML 文件与 Worker 源码，确认旧 UUID c69d9310-66db-4614-b3b7-0fb01e68b4ec 出现次数 == 0。
4. 全局 206 节点真实去重核验：
   - 提取全部 206 个节点的 (server, port, sni, path) 元组，验证是否已消除 &ed=2048、&region=xx 等无意义填充，且每个端点组合依然 100% 真实唯一。
5. Worker 动态 UUID 替换核验：
   - 检查 wasmer_sub_updated.js 中的 UUID 动态替换逻辑，确认 targetUuid 确实参与正则替换。
6. 语法与破折号核验：
   - 验证 yaml.safe_load 语法正确性，扫描破折号 (\u2014, \u2013)，确认 count == 0。
7. 产出 orchestration/S2_audit_report_v2.md。

## 产出（全部落盘）
- C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\orchestration\S2_audit_report_v2.md
