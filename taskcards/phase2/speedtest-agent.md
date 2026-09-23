# TaskCard: taskcards/phase2/speedtest-agent.md

## 1. 背景
V12 重构要求建立真实、隔离、可复算的中国三网测速流水线，彻底清除伪造常数与估算延迟。

## 2. 唯一目标
1. 建立候选池三层分离：`candidates/raw.jsonl`, `candidates/deduped.jsonl`, `candidates/rejected.jsonl`，报告分别显示 raw, deduped, deployed, tested, published 计数。
2. 三网入口验证：测速开始前验证运营商入口 ASN（电信、联通、移动），记录于 `results/route-proof/<run_id>.json`。
3. 严格隔离：测试进程仅运行在临时沙箱与专用高端口，绝对禁止触碰用户本机 Clash、TUN 或 127.0.0.1 代理。
4. 分层探测：
   - 第一层：DNS, TCP, TLS, SAN, HTTP Upgrade
   - 第二层：完整 VLESS-WS 双向转发（临时 Mihomo / Sing-box 沙箱）
   - 第三层：generate_204=204
   - 第四层：出口 IP, ASN, 组织, 实际国家
   - 第五层：受控测速源真实吞吐
5. 执行 3 个运营商 x 每运营商 3 轮 = 最少 9 轮完整测试，结果落盘至 `results/raw/<run_id>/<carrier>.jsonl` 并生成 SHA-256 manifest。

## 3. 输入路径
- `candidates/deduped.jsonl`
- `evidence/deployments/summary.json`

## 4. 允许操作
- 运行沙箱测速脚本
- 生成不可变 JSONL 结果

## 5. 禁止操作
- 严禁使用 TLS 握手时间冒充下载速度，严禁随机数生成 Mbps
- 严禁使用固定延迟（如 140ms）或假常数
- 严禁在英文注释或文档中使用 em-dash (\u2014) 与 en-dash (\u2013)

## 6. 必须执行的命令或 API
- 独立沙箱 Python 测速引擎

## 7. 必须生成的文件
- `candidates/raw.jsonl`
- `candidates/deduped.jsonl`
- `candidates/rejected.jsonl`
- `results/route-proof/<run_id>.json`
- `results/raw/<run_id>/telecom.jsonl`
- `results/raw/<run_id>/unicom.jsonl`
- `results/raw/<run_id>/mobile.jsonl`
- `results/raw/<run_id>/manifest.json`

## 8. 机器可判定验收条件
- 9 轮测试记录完整，无缺失关键字段
- 各记录经数学校验无固定步长规律
- SHA-256 manifest 完整校验通过

## 9. 停止条件
三网 9 轮实测完成且 manifest 生成后停止。
