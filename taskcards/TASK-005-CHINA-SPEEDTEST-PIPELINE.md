# 任务卡: TASK-005-CHINA-SPEEDTEST-PIPELINE

- **任务名称**: 中国链路三网实测流水线与优选构建
- **指派角色**: speed (Subagent)
- **工作目录**: `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest`
- **前置依赖**: TASK-002, TASK-003 完成部署

---

## 1. 任务背景与核心红线
彻底删除所有硬编码假数据（PROVEN_DOMESTIC_BENCHMARKS 等）。测速流程必须在中国链路环境运行（GitHub Actions 内建大陆优选入口代理/TUN，仅作用于 Runner 自身环境，绝不触碰本机网络）。

## 2. 必须做
1. **候选池构建**:
   - 包含电信、联通、移动三网优选候选，总候选数 ≥ 4000（每平台 ≥ 1000）。
   - 节点 server 全为有效域名，绝对零硬编码 IP。
2. **分层探测逻辑**:
   - 对每个候选节点进行分层验证（缺一不通过）：
     1. DNS 解析
     2. TCP 握手
     3. TLS + SNI/证书验证
     4. WS Upgrade 101 握手
     5. 完整 VLESS-WS 数据包通信（含 `?ed=` early-data）
     6. `generate_204` 连通性测试（必须等于 204）
     7. 获取真实出口 IP、ASN 与实际国家代码
   - 连续执行 ≥ 3 轮测试。
3. **结果落盘**:
   - 原始数据写入 `results/china-telecom/<ts>.json`, `results/china-unicom/<ts>.json`, `results/china-mobile/<ts>.json`。
   - 字段包括：`candidate_id`, `provider`, `server`, `sni`, `path`, `test_network`, `round`, `dns_ms`, `tcp_ms`, `tls_ms`, `ws_status`, `vless_ok`, `generate_204_status`, `generate_204_ms`, `exit_ip`, `exit_asn`, `exit_country`, `tested_at`。
4. **优选打分 (Trace-Web 移植)**:
   - 计算公式：`Score = 0.5 × 真实204RTT + 0.3 × TLS_Time + 0.1 × Jitter + 10 × Loss_Rate`。
   - 大区亲和硬约束，去除异常毛刺。
   - 生成六套订阅 YAML：
     - Supabase ≥ 34
     - Wasmer ≥ 34
     - Northflank ≥ 34
     - Fastly ≥ 34
     - Netlify ≥ 34
     - EdgeOne = 36（严格）
   - 节点名称必须严格等于隧道实测出口国家（Geo Gate mismatch = 0）。
