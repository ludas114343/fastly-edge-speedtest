# 任务卡: TASK-002-DIRECT-BACKEND-DEPLOY

- **任务名称**: 三大 CAPABLE_DIRECT 基线后端真实部署上线与连通性验证
- **指派角色**: backend (Subagent)
- **工作目录**: `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest`
- **前置依赖**: TASK-000 通过，无个人境外 VPS

---

## 1. 任务目标
真实部署并验证三大已知具备原生自出站能力（CAPABLE_DIRECT）的后端基线平台：
1. **Supabase**: Deno 运行时 (`Deno.connect` 直出 AWS 出口)。
2. **Wasmer**: Node.js 运行时 (`net.connect` 直出)。
3. **Northflank**: Go 运行时 (`singbox-lite` / `net.Dial` 直出)。

## 2. 必须做
1. 从 Obsidian/本地配置安全读取 Supabase / Wasmer / Northflank 的部署凭据。
2. 针对每个平台，配置独立的 UUID（严禁六平台共用同一 UUID）。
3. 真实部署上线，获取公网解析域名。
4. 验证 VLESS-WS 连接与 `generate_204` 真实出站测试，记录出站 IP 与 ASN。
5. 部署日志与配置留档至 `configs/supabase/`, `configs/wasmer/`, `configs/northflank/`。

## 3. 禁止做
- 严禁假部署或使用伪造响应。
- 严禁使用 hardcoded IP，节点 server 必须为真实自定义或平台合法域名。
- 严禁明文记录凭据。

## 4. 交付产出
- 三大平台的真实部署域名与测试结果记录落盘。
- 各平台独立 UUID 记录（仅哈希或安全索引，敏感凭据脱敏）。
