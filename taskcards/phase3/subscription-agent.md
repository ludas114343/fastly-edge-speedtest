# TaskCard: taskcards/phase3/subscription-agent.md

## 1. 背景
依据三网实测原始 JSONL，应用公开、可复算的独立优选算法，生成并发布稳定订阅链接与自动运维工作流。

## 2. 唯一目标
1. 优选算法实现：
   - 硬门禁：真实 deployment_id, 9 轮 VLESS 鉴权成功, 9 轮 generate_204=204, 出口国家与 ASN 稳定, 标签正确, 无重复连接参数。
   - 跨三网排名：先最小化最差一网的 p95，再最小化三网 p50 平均值，再最小化 jitter，再最大化下载中位数。
   - 稳定性迟滞：综合指标改善 >= 15% 或旧节点连续两轮失效才替换，防止频繁抖动。
2. 订阅链接构建与发布：
   - 支持 URL: `/all`, `/supabase`, `/wasmer`, `/northflank`, `/cloudflare`, `/fastly`, `/netlify`, `/edgeone`
   - 平台无合格节点时诚实返回 `proxies: []`，`metadata: status: NO_VERIFIED_PROXY, reason: ...`
   - 验证订阅：HTTP 200, YAML 结构合法, 节点数与 manifest 一致，生成 `evidence/subscriptions/<token>.json`。
3. 建立 10 个独立 GitHub Actions 自动更新与监控工作流。

## 3. 输入路径
- `results/raw/<run_id>/`
- `evidence/deployments/summary.json`

## 4. 允许操作
- 编写订阅分发 Worker 或脚本
- 生成各平台订阅 YAML
- 编写 `.github/workflows/`

## 5. 禁止操作
- 严禁在无合格节点时用其他平台节点伪造填充
- 严禁在英文注释或文档中使用 em-dash (\u2014) 与 en-dash (\u2013)

## 6. 必须执行的命令或 API
- 优选与订阅生成 Python 脚本

## 7. 必须生成的文件
- 8 个订阅 YAML 文件
- `evidence/subscriptions/<token>.json`
- 10 个 GitHub Actions 工作流文件

## 8. 机器可判定验收条件
- 各订阅链接通过 YAML 解析与结构完整性检查
- 自动更新工作流语法校验通过
- 订阅验收 JSON 包含状态码 200、内容哈希与节点解析数

## 9. 停止条件
订阅文件与工作流就绪并通过测试后停止。
