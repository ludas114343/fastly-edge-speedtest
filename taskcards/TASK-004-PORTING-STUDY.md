# 任务卡: TASK-004-PORTING-STUDY

- **任务名称**: 开源项目精读与函数级移植对照映射分析 (Study)
- **指派角色**: study (Subagent)
- **工作目录**: `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest`

---

## 1. 任务背景与核心目标
严禁口头参考。必须精读开源标杆代码库与历史上下文，建立函数级映射文档与等价实现标准。

## 2. 精读对象与任务要求
1. **zizifn/edgetunnel & cmliu/edgetunnel (`_worker.js`)**:
   - 深入分析: VLESS 协议解析、WebSocket upgrade 握手、early-data (`?ed=`) 处理、UUID 严格校验、节点动态切换、反爬/伪装页面分离、多格式订阅生成。
   - 产出: `docs/edgetunnel_porting_map.md`。必须包含表格：原函数名 | 本项目对应文件/函数 | 是否保留 | 删除理由 | 替代实现方式 | 等价测试用例与证据。
2. **Tintac-CN/denoVlessProxy**:
   - 分析 Deno 平台的 TCP `Deno.connect` 与 WebSocket/WebStream 双向管道桥接范式。
   - 产出: `docs/denovless_porting_map.md`。
3. **Wasmer (Node.js) 与 Northflank (Go) 直出范式**:
   - Wasmer: `http.createServer` + `server.on('upgrade')` + `net.connect` 范式。
   - Northflank: Go 运行时轻量级 TCP 拨号/隧道 (`singbox-lite`) 范式。
   - 产出: `docs/runtime_direct_map.md`。
4. **wlisboy/Trace-Web**:
   - 核心逻辑: 候选节点枚举、分层探测流程 (DNS->TCP->TLS->WS->VLESS->204)、优选打分公式 (`Score = 0.5×真实204RTT + 0.3×TLS_Time + 0.1×Jitter + 10×Loss_Rate`)、大区亲和硬约束、在线淘汰与刷新机制。
   - 产出: `docs/trace_web_porting_map.md`。必须包含：原始逻辑块 | 移植后文件 | 函数名 | 调用点 | 预期输入输出。
5. **本地上下文恢复与历史审视**:
   - 分析本地历史成果、git log、walkthrough 以及 Obsidian 中的关键架构备忘。
   - 产出: `docs/context_recovery.md`。

## 3. 禁止事项
- 禁止仅提供概念性、口头概括性描述。
- 禁止遗漏任何原项目的关键安全校验 (如 early-data 长度检查、UUID 校验位)。

## 4. 交付文件
- `docs/edgetunnel_porting_map.md`
- `docs/denovless_porting_map.md`
- `docs/runtime_direct_map.md`
- `docs/trace_web_porting_map.md`
- `docs/context_recovery.md`
