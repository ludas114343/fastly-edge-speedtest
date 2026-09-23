# TaskCard S2-backend-02 @taskcards/S2-backend-02.md

## 背景（自含）
项目目录：C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest
阶段 S2 首轮代码审计（audit-code）与对抗红队（redteam）双双给出 FAIL 判定。
具体报告详见：
- orchestration/S2_audit_report.md
- orchestration/S2_redteam_report.md
必须逐条清零两组审计指出的全部缺陷，严禁任何形式的糊弄、假差异化或遗留历史脏数据。

## 唯一目标
彻底重构修复 6 套 YAML 文件、speedtest.py 与 Worker 代码，彻底清除 4 个残留香港节点与旧 UUID，修复 Fastly 域名激活与 Worker 动态替换逻辑，消除虚假路径填充，如实记录 EdgeOne 运行时实测边界。

## 必须执行的具体整改清单（6 大项硬性指标）
1. [EdgeOne 与全库 HK 绝对清零]:
   - 彻底删除 clash_edgeone.yaml 中的 4 个 "🇭🇰 中国香港" 节点，用真实的 JP (ap-northeast-1) / KR (ap-northeast-2) / SG (ap-southeast-1) 补位，确保总节点数仍为 36 个。
   - 同步清理 wasmer_sub_updated.js 中 FALLBACK_EDGEONE_YAML 内的所有香港节点与策略组。
   - 确保全库 6 套 YAML 的 HK 节点数绝对为 0。
2. [彻底清零旧 UUID]:
   - 打开 speedtest.py，将第 32 行与第 560 行硬编码的旧 UUID c69d9310-66db-4614-b3b7-0fb01e68b4ec 彻底删除，改为从 uuid_config.json 动态加载对应订阅的 UUID。
3. [修复 Worker 动态 UUID 分发代码]:
   - 修复 wasmer_sub_updated.js 中 targetUuid "声明但未被使用" 的死代码 Bug。
   - 实现真实生效的正则或文本替换，确保请求 token=fastly 时输出的内容 100% 替换为 UUID_FASTLY，请求 token=wasmer 时替换为 UUID_WASMER，依此类推。
4. [Fastly 域名服务激活]:
   - 检查 Fastly Service 8K5HGyXmr8P6XuzRc5UPk0，针对 version 11 添加并激活 ruoyemu.freetls.fastly.net 与 fastly.ruoyemu.asia，下发激活指令（PUT /service/8K5HGyXmr8P6XuzRc5UPk0/version/11/activate），消除 421 Misdirected Request。
   - 在 clash_fastly.yaml 中将 SNI 和 Host 准确对齐到已激活的 Fastly 域名。
5. [消除虚假路径填充，实现物理合法异构]:
   - 彻底删除 clash_edgetunnel.yaml、clash_netlify.yaml、clash_edgeone.yaml 中为了规避去重检查而随意拼接的 &ed=2048、&region=xx 等无意义填充参数。
   - 依靠真实的异构后端组合实现差异化：3 个不同的 Supabase 独立后端域名、11 个真实不同的 AWS 函数区域、Wasmer 洛杉矶真实物理端点、Northflank GCP 独立端点、Netlify 独立网关 IP。
6. [EdgeOne 真实技术边界记录]:
   - 诚实记录实测发现：腾讯云 EdgeOne 边缘函数运行时返回 {"hasWebSocket": false, "hasConnect": false}，且添加加速域名触发 FailedOperation.NoRealNameAuth。在报告中附上真实 API 证据与日志路径，禁止声称 EdgeOne 已单机自闭环跑通原生 VLESS。

## 禁止事项
- 严禁任何路径伪差异化；
- 严禁触碰用户本机运行中的 Clash Verge / TUN / 代理；
- 全文严禁使用破折号 (em-dash)。

## 产出（全部落盘）
- 6 套重构清理后的 YAML
- C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\speedtest.py (清理旧 UUID)
- C:\Users\ludas\.gemini\antigravity\scratch\wasmer_sub_updated.js (修复 UUID 分发)
- C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\orchestration\S2_backend_report_v2.md
