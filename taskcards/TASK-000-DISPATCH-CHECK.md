# 任务卡: TASK-000-DISPATCH-CHECK

- **任务名称**: Subagent 派遣探活与环境基线检查
- **指派角色**: probe (Subagent)
- **输入路径**: `orchestration/ledger.md`
- **执行目录**: `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest`

---

## 1. 任务背景与目标
验证主 Agent 与 Subagent 之间的通信、命令执行以及文件写入链路 100% 畅通。完成环境探活后输出验证 JSON 文件。

## 2. 必须做
1. 检查当前工作目录 `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest`。
2. 确认 Node.js / Python / Git 环境是否可用。
3. 将探活证据以标准 JSON 写入 `orchestration/evidence/dispatch_ping.json`。
4. 返回给主 Agent 探活结果。

## 3. 禁止做
- 禁止篡改历史数据或捏造状态。
- 禁止修改本机系统网络代理/TUN/Clash 配置。

## 4. 交付产出
- `orchestration/evidence/dispatch_ping.json`，内容必须包含:
  ```json
  {
    "subagent_role": "probe",
    "status": "HEALTHY",
    "timestamp": "<ISO-TIMESTAMP>",
    "node_version": "<version>",
    "python_version": "<version>",
    "git_version": "<version>",
    "verified_by": "probe-subagent"
  }
  ```

## 5. 验收条件
- 文件 `orchestration/evidence/dispatch_ping.json` 真实存在且各字段均有效非空。
