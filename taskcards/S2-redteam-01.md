# TaskCard S2-redteam-01 @taskcards/S2-redteam-01.md

## 背景（自含）
项目目录：C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest
后端施工声称已消灭套壳、消灭假标、完成去重与 Worker 多 UUID 改造。
Red Team 必须针对 6 套 YAML 与 Worker 执行矩阵级对抗比对与找茬审查。

## 唯一目标
对抗审查阶段 S2 交付物，寻找"换皮不换心"、伪差异化、漏网重复配置或边缘函数调用漏洞，产出 orchestration/S2_redteam_report.md 并给出终审判决 (PASS 或 FAIL)。

## 输入
- 6 套 YAML 文件
- wasmer_sub_updated.js
- uuid_config.json
- orchestration/S2_backend_report.md

## 必须执行
1. 对抗比对 Fastly vs edgetunnel：
   - 审查 clash_fastly.yaml 是否存在裸连 supabase.co 的情况。
   - 确认 Fastly 节点的 server/SNI 是否真实走 Fastly 前端网络 (fastly.ruoyemu.asia / 151.101.x.x)。
2. 对抗比对 Wasmer 伪标：
   - 审查是否仍有任何单点 LA 出口被伪装成亚太或欧洲节点。
3. 对抗审查 EdgeOne 真实性：
   - 验证 EdgeOne 报告中引用的 ef-ddka6pqw 与 rule-1tf0643v 凭证是否符合腾讯云 TEO 规则规范。
4. 对抗比对全局端点差异性：
   - 检查是否有通过无意义路径修改（如随意加字符）强行凑数的行为。
5. 对抗审查 Worker 多 UUID 路由逻辑：
   - 审查 wasmer_sub_updated.js 在不同 token 参数下的 UUID 替换与 Fallback 是否存在空指针或回退旧 UUID 漏洞。
6. 全文检索破折号与敏感信息。
7. 产出 orchestration/S2_redteam_report.md。

## 产出（全部落盘）
- C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\orchestration\S2_redteam_report.md

## 验收清单（逐条可判 PASS/FAIL）
1. 逐条完成 5 大项对抗比对。
2. 给出明确终审结论 (PASS 或 FAIL)。
