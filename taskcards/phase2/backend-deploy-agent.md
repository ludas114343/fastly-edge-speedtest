# TaskCard: taskcards/phase2/backend-deploy-agent.md

## 1. 背景
根据能力矩阵定架构，真实执行部署。直出后端（Supabase, Wasmer, Northflank, Cloudflare）与条件后端（Fastly, Netlify, EdgeOne）全部必须有真实项目部署记录，但只有完整 VLESS 真实通过的平台才能发布代理节点。

## 2. 唯一目标
1. 真实部署并验证 Supabase VLESS-WS 后端、Wasmer VLESS-WS 后端、Northflank VLESS-WS 容器、Cloudflare edgetunnel。
2. 纠错 Northflank：如果 API 只返回 1 个 US-East deployment，则严格只发布 1 个真实 Northflank 节点，绝对禁止复制为 34 个虚构地区节点！
3. 对照实验 Cloudflare edgetunnel：分别测试并记录 A. 不配 PROXYIP, B. 配 AWS/Supabase PROXYIP, C. 配 SOCKS5，严格按 [Cloudflare入口→AWS出口] 区分命名。
4. 按探针结果完成 Fastly / Netlify / EdgeOne 真实部署。

## 3. 输入路径
- `docs/platform_capability_matrix.json`
- `evidence/inventory/`
- 各平台源码工程：`configs/`

## 4. 允许操作
- 部署或更新各平台真实服务
- 绑定合法域名与安全独立 UUID
- 记录真实 deployment ID, service ID, commit SHA 与公网入口

## 5. 禁止操作
- 严禁同一后端复制改名成多国节点
- 严禁修改用户 Windows 注册表、TUN 适配器或系统网络代理
- 严禁在英文注释或文档中使用 em-dash (\u2014) 与 en-dash (\u2013)

## 6. 必须执行的命令或 API
- 真实部署与状态查询 CLI/API

## 7. 必须生成的文件
- `docs/deployments_verification.md`
- `evidence/deployments/summary.json`
- `evidence/deployments/cf_modes_comparison.json`

## 8. 机器可判定验收条件
- 6 个平台均具备真实 deployment ID / service ID
- Northflank 部署数量与发布节点数量严格一致
- CF 对照实验 A/B/C 三种模式数据完整无混淆

## 9. 停止条件
各部署状态经公网测试确认为 active/running 并落盘证据后停止。
