# 任务卡: TASK-003-FRONT-OR-DIRECT-DEPLOY

- **任务名称**: Fastly、Netlify、EdgeOne 依据探针判定的真实部署与回源配置
- **指派角色**: backend (Subagent)
- **工作目录**: `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest`
- **前置依赖**: TASK-001 探针判定矩阵完成

---

## 1. 任务背景与核心架构规则
根据 TASK-001 落盘的 `docs/platform_capability_matrix.md` 对 Fastly, Netlify, EdgeOne 实施部署：
- 若判定为 `CAPABLE_DIRECT`：平台原生拨号任意 host:port，部署为独立真后端（自出站）。
- 若判定为 `CAPABLE_FRONT`：由于用户明确“无个人 VPS”，必须配置为“入口层→真实后端 (Supabase/Wasmer/Northflank)”。
  - 节点名称必须诚实标注“入口→真实后端”，绝不许虚标为“Fastly/Netlify/EdgeOne 出口”。
  - 出口 ASN 严格如实对应真实后端 ASN。
- 若判定为 `INCAPABLE`：严禁作为出站节点，仅作为前置反代/分发/伪装。

## 2. 必须做
1. 分别为 Fastly, Netlify, EdgeOne 部署服务并上线。
2. 配置各平台独立 UUID。
3. 真实发起 VLESS-WS 连接测试并验证 204。
4. 部署记录与真实状态落盘至对应目录。

## 3. 禁止做
- 严禁在 FRONT 架构下声称自出站。
- 严禁域名解析命中 Cloudflare ASN 13335（测试分发除外）。
- 严禁使用共享证书域（如 *.netlify.app, *.workers.dev, *.pages.dev, *.global.ssl.fastly.net）作为节点 server。
