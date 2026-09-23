# 任务卡: TASK-007-AUDIT-NET-AND-REDTEAM

- **任务名称**: 网络端到端实测复核与红蓝对抗质检 (Audit-Net & RedTeam)
- **指派角色**: audit-net & redteam (Subagents)
- **工作目录**: `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest`

---

## 1. 任务目标
采取对抗性视角，独立从线上订阅 URL / 生成文件逐节点拉取，进行 VLESS + 204 + ASN 实测，专证是否存在套壳、虚标与造假。

## 2. 红队对抗审查核心清单
1. **专证：平台是否冒充/套壳**:
   - 检查 Fastly/Netlify/EdgeOne 节点是否实际直接回源到了 Cloudflare / Supabase，是否在 FRONT 架构下伪造了“独立出口 ASN”。
2. **专证：同连接多国改名**:
   - 验证是否存在同一个 `server + port + SNI + Host + path + UUID` 在 YAML 中被换个国家名字复用多次。
3. **专证：探针结果真实性**:
   - 独立验证 `docs/probes/` 中的原始输出和部署日志，排查探针返回是否被手工伪造。
4. **Geo Gate 实测校验**:
   - 逐个节点发起真实 204 请求，测定出站真实 IP，查询其国家代码与 ASN。
   - 验证名称标注国家是否 100% 匹配出口国家（容忍度必须为 0 mismatch）。
5. **反 Cloudflare 判定**:
   - 确认无节点 DNS 解析命中 Cloudflare ASN 13335。

## 3. 产出文档
- `docs/security/redteam_adversarial_report.md`
- `docs/security/audit_net_verification.md`
