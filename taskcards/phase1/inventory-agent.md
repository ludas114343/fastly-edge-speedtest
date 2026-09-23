# TaskCard: taskcards/phase1/inventory-agent.md

## 1. 背景
用户启动 V12 项目彻底重构，强制要求对所有历史产物执行隔离归档，并对六大平台（Supabase, Wasmer, Northflank, Fastly, Netlify, EdgeOne）的官方 API / CLI 进行真实部署资产清点，彻底废弃未经证明的推测数据。

## 2. 唯一目标
1. 立即冻结所有旧 speedtest 结果、旧 6000 候选统计、旧 YAML、旧延迟数字、旧国家标签，移动至 `forensics/legacy/`，并生成 `forensics/legacy_manifest.json` 记录所有文件的 SHA-256。
2. 调用六个平台的官方 API / CLI 查询实际项目、服务、部署、域名与活动版本状态，生成 6 份独立机器可读清单。若无真实项目，记录 DEPLOYMENT_COUNT=0。

## 3. 输入路径
- 当前工作区根目录及历史文件：`clash*.yaml`, `results/`, `*_candidates.json`, `*_best_nodes.json`
- 本地凭据库：`D:\Obsidian\CollegeAid\planning\平台凭据速查.md`（仅限内存读取，严禁明文落盘）

## 4. 允许操作
- 创建目录 `forensics/legacy/`, `evidence/inventory/`
- 移动旧 YAML 与测试文件到 `forensics/legacy/` 并计算 SHA-256
- 运行 Python / CLI 脚本查询 Supabase, Wasmer, Northflank, Fastly, Netlify, EdgeOne 官方 API
- 对输出 JSON 中敏感信息（Token, SecretKey）进行打码遮蔽

## 5. 禁止操作
- 严禁删除旧文件（必须移动到 `forensics/legacy/`）
- 严禁凭空脑补或根据本地文件名猜测部署状态
- 严禁修改用户 Windows 注册表、Clash Verge、TUN 适配器或系统网络代理
- 严禁在英文注释或文档中使用 em-dash (\u2014) 与 en-dash (\u2013)

## 6. 必须执行的命令或 API
- 隔离与 SHA-256 计算脚本
- Supabase API: `GET https://api.supabase.com/v1/projects`
- Wasmer CLI / API: `wasmer app list` 或 GraphQL API
- Northflank API: `GET https://api.northflank.com/v1/projects`
- Fastly API: `GET https://api.fastly.com/service`
- Netlify API: `GET https://api.netlify.com/api/v1/sites`
- EdgeOne API: 腾讯云 API `DescribeEdgeFunctions` / `DescribeL4Proxy`

## 7. 必须生成的文件
- `forensics/legacy_manifest.json`
- `evidence/inventory/supabase.json`
- `evidence/inventory/wasmer.json`
- `evidence/inventory/northflank.json`
- `evidence/inventory/fastly.json`
- `evidence/inventory/netlify.json`
- `evidence/inventory/edgeone.json`

## 8. 机器可判定验收条件
- `forensics/legacy_manifest.json` 包含移动文件的完整列表与 SHA-256 哈希值
- 6 份 inventory JSON 满足指定 schema，包含 `platform`, `account_verified`, `projects`, `services`, `deployments`, `regions`, `domains`, `active_versions`, `checked_at`, `api_response_hash`
- 若某平台项目数为 0，明确记录 `"DEPLOYMENT_COUNT": 0`

## 9. 停止条件
当 6 份 inventory 文件与 legacy_manifest 全部写入磁盘并通过格式校验后停止。
