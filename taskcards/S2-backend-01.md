# TaskCard S2-backend-01 @taskcards/S2-backend-01.md

## 背景（自含）
项目目录：C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest
阶段 S1 研究与架构映射已获审计与对抗红队双 PASS 通过。本阶段为阶段 S2：真实后端重建。
必须严格消灭套壳、消灭假标、消灭全域单 UUID，实现六套订阅的真实拓扑归属。

## 唯一目标
完成全部 6 套订阅 YAML 的物理重构与真实后端落地，确保 0 假套壳、0 香港假节点、Wasmer 诚实标注美西、0 重复节点、6 套独立 UUID 隔离，并产出 orchestration/S2_backend_report.md。

## 平台真实归属标准（硬性门禁）
1. Fastly (clash_fastly.yaml): server/SNI 必须指向 Fastly 服务 (8K5HGyXmr8P6XuzRc5UPk0) 真实绑定的前端域名 (fastly.ruoyemu.asia / ruoyemu.freetls.fastly.net) 或 Fastly 官方 Anycast VIP (151.101.x.x)。严禁直接填 *.supabase.co 裸链。
2. Wasmer (clash_wasmer.yaml): 物理机 66.42.98.41 / w-la.ruoyemu.asia 仅限置于美西节点组，诚实命名为 "🇺🇸 美国洛杉矶 [Wasmer]"。池中 Supabase 与 Northflank 腿分别明确标注 [Supabase] 与 [Northflank]。严禁将 Wasmer LA 标为日韩德等非美地区。
3. Netlify (clash_netlify.yaml): 恢复 Netlify 伪装网关入口 + Northflank + Supabase 容灾腿。严禁使用 404 函数路径。
4. edgetunnel (clash_edgetunnel.yaml): 直连 Supabase 多 region；物理删除所有 HK 节点，用真实 JP (ap-northeast-1) / KR (ap-northeast-2) / SG (ap-southeast-1) 补齐保数。
5. EdgeOne (clash_edgeone.yaml): 必须对应腾讯云 TEO 已部署的边缘函数 ef-ddka6pqw 与规则 rule-1tf0643v，节点使用 TEO 专属 UUID。在报告中附上真实 TEO API 部署凭证摘要（脱敏）。
6. Master (clash.yaml): 聚合上述真实池中验证合格的节点，保留来源标签。

## 必须执行
1. 校验 uuid_config.json 中的 6 枚独立强随机 UUID，将其注入对应的 6 个 YAML 文件中。全库物理下线并禁止旧 UUID (c69d9310-...)。
2. 消除跨全部 6 个 YAML 的全部重复配置。确保每一个 (server, port, sni, path, uuid) 组合均为全局唯一。
3. 节点数量硬门禁：
   - clash_fastly.yaml >= 34
   - clash_wasmer.yaml >= 34
   - clash_netlify.yaml >= 34
   - clash_edgetunnel.yaml >= 34
   - clash_edgeone.yaml == 36
   - clash.yaml >= 34
4. 更新 wasmer_sub_updated.js Worker 代码：
   - 彻底移除硬编码 GitHub Token，统一走 env.GITHUB_TOKEN；
   - 按照 token 参数分发对应的专属 UUID；
   - 刷新 FALLBACK_EDGEONE_YAML 与 FALLBACK_MASTER_YAML 为重构后的纯净版。
5. 全量执行 yaml.safe_load 校验，确保语法无误。
6. 将重建成果、各平台拓扑、去重矩阵、UUID 映射与 TEO API 证据落盘至 orchestration/S2_backend_report.md。

## 禁止事项
- 严禁触碰用户本机运行中的 Clash Verge / Mihomo / TUN / 系统代理；
- 严禁假套壳或名称欺诈；
- 全文严禁使用破折号 (em-dash)。

## 产出（全部落盘）
- 6 套重构后的 YAML 文件 (clash.yaml, clash_fastly.yaml, clash_wasmer.yaml, clash_netlify.yaml, clash_edgetunnel.yaml, clash_edgeone.yaml)
- C:\Users\ludas\.gemini\antigravity\scratch\wasmer_sub_updated.js
- C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\orchestration\S2_backend_report.md
