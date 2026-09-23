# TaskCard S2-audit-code-01 @taskcards/S2-audit-code-01.md

## 背景（自含）
项目目录：C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest
阶段 S2 后端施工产物已落盘：6 套 YAML 文件与 wasmer_sub_updated.js。
本任务卡由 audit-code 独立执行，不听信 backend 汇报，对所有 YAML 与 Worker 代码进行机器级逐项核验。

## 唯一目标
对 6 套 YAML 文件与 Worker 源码进行全量独立静态代码核验，产出 orchestration/S2_audit_report.md 并给出 PASS/FAIL。

## 输入
- clash.yaml, clash_fastly.yaml, clash_wasmer.yaml, clash_netlify.yaml, clash_edgetunnel.yaml, clash_edgeone.yaml
- uuid_config.json
- C:\Users\ludas\.gemini\antigravity\scratch\wasmer_sub_updated.js

## 必须执行
1. 校验节点数量：
   - clash_fastly.yaml >= 34
   - clash_wasmer.yaml >= 34
   - clash_netlify.yaml >= 34
   - clash_edgetunnel.yaml >= 34
   - clash_edgeone.yaml == 36
   - clash.yaml >= 34
2. 校验地理真实性：
   - 检索全部 6 套 YAML，确认 "🇭🇰" 或 "香港" 或 "HK" 出现次数 == 0。
   - 检查 clash_wasmer.yaml，确认 w-la / 66.42.98.41 仅出现在美国组，未被冠以任何非美地区名称。
3. 校验唯一性与去重：
   - 提取全部 206 个节点的 (server, port, sni, path, uuid) 元组，验证去重后集合长度 == 206。
4. 校验 UUID 隔离性：
   - 确认每个 YAML 分别使用了 uuid_config.json 对应的独立 UUID。
   - 检索全库确认旧 UUID c69d9310-66db-4614-b3b7-0fb01e68b4ec 出现次数 == 0。
5. 校验安全凭据：
   - 检索 wasmer_sub_updated.js 确认 gho_REDACTED 出现次数 == 0，确实改用 env.GITHUB_TOKEN。
6. 校验语法与编码：
   - 运行 yaml.safe_load 校验 6 套文件。
   - 正则扫描破折号 (\u2014, \u2013)，确认 count == 0。
7. 产出 orchestration/S2_audit_report.md。

## 产出（全部落盘）
- C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\orchestration\S2_audit_report.md

## 验收清单（逐条可判 PASS/FAIL）
1. 节点数量硬指标 100% 达标。
2. 香港节点数 == 0。
3. 全局去重率 100% (206/206 唯一)。
4. 旧 UUID == 0，旧 Token == 0。
5. 全文 0 破折号。
