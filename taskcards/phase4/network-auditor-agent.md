# TaskCard: taskcards/phase4/network-auditor-agent.md

## 1. 背景
Network Auditor 只能获得线上/本地生成的订阅 URL，不得获得 Builder 的推论，独立进行套接字网络对抗实测。

## 2. 唯一目标
1. 独立下载订阅并解析全部节点。
2. 对各节点发起独立 VLESS-WS 握手与 generate_204 探针，测量真实延迟。
3. 提取实际物理出口 IP、ASN 与国家，核验 Geo Gate（mismatch 必须为 0）。
4. 逐节点反向关联 deployment ID，确证无一物多名或虚构地区。

## 3. 输入路径
- 订阅文件及本地服务入口

## 4. 允许操作
- 发起真实的物理套接字网络探针
- 编写独立网络审计报告

## 5. 禁止操作
- 严禁调用用户本机现有代理端口 (7897)
- 严禁在英文注释或文档中使用 em-dash (\u2014) 与 en-dash (\u2013)

## 6. 必须执行的命令或 API
- 独立网络测试脚本

## 7. 必须生成的文件
- `docs/security/network_auditor_v12.md`

## 8. 机器可判定验收条件
- 包含每个测试节点的 HTTP 状态码、RTT、出口 IP、ASN 与国家
- Geo Gate mismatch 错误数严格可机判

## 9. 停止条件
测试完成且报告落盘后停止。
