# 任务卡: TASK-006-AUDIT-CODE-AND-SECURITY

- **任务名称**: 代码与安全审计（假数据排查、凭据撤销与脱敏审计）
- **指派角色**: audit-code (Subagent)
- **工作目录**: `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest`

---

## 1. 任务目标
独立重跑代码静态扫描、历史提交审计与凭据安全排查，核验系统是否存在假数据硬编码或凭据泄露。

## 2. 必须做
1. **假数据全量审计**:
   - 扫描所有 Python/JS/JSON/YAML 文件，检索是否存在 `PROVEN_DOMESTIC_BENCHMARKS`、伪造的延迟与速度常数、无网络调用的 benchmark 脚本。
   - 发现立即报错并要求清零。
2. **凭据安全审计**:
   - 检查历史泄露的 `gho_` GitHub Token 是否已被 revoke，全库 Git 历史、代码与日志是否有明文 Token / SecretKey。
   - 验证敏感凭据是否仅从 Obsidian / Secret 安全注入。
3. **独立 UUID 验证**:
   - 审计六大平台的订阅 UUID，验证是否满足平台间独立互斥，旧 UUID 是否具备 24h 灰度作废机制。
4. **本机配置防护审计**:
   - 确保本机 Clash/TUN/profile 零触碰，测速完全限制在 GitHub Actions Runner 容器内。

## 3. 产出文档
- `docs/security/code_and_security_audit.md`
