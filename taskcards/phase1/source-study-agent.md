# TaskCard: taskcards/phase1/source-study-agent.md

## 1. 背景
V12 重构要求精读并函数级移植开源项目，彻底杜绝口头参考或伪造照搬。必须对照 `cmliu/edgetunnel` 与 `wlisboy/Trace-Web`。

## 2. 唯一目标
1. 精读 `cmliu/edgetunnel` (_worker.js)：覆盖 VLESS 请求头解析、UUID 严格校验、WebSocket 双向流、early-data(?ed=)、TCP connect、ProxyIP fallback、SOCKS5/HTTP chain、伪装页面、路径参数、错误关闭。生成函数级移植映射文档 `docs/edgetunnel_porting_map.md`。
2. 严谨分析 `wlisboy/Trace-Web`：明确指明哪些算法能够从公开源码复现（候选解析、去重、IPv4 /24 精简、分层筛选、下载测试、排序导出），若核心 Go backend 或排序无法公开获取，明确标注“算法无法从公开源码复现，本项目采用独立实现”。

## 3. 输入路径
- 开源参考源码库及本地已有分析文档：`docs/*porting_map.md`, `configs/`

## 4. 允许操作
- 查阅本地与公开的 edgetunnel 与 Trace-Web 源码
- 编写与更新 Markdown 映射规范

## 5. 禁止操作
- 严禁空泛宣称“完整照搬 Trace-Web”
- 严禁遗漏 ProxyIP fallback 或 SOCKS5 chain 分析
- 严禁在英文注释或文档中使用 em-dash (\u2014) 与 en-dash (\u2013)

## 6. 必须执行的命令或 API
- 文本与结构化检查命令

## 7. 必须生成的文件
- `docs/edgetunnel_porting_map.md`
- `docs/trace_web_porting_map.md`

## 8. 机器可判定验收条件
- `docs/edgetunnel_porting_map.md` 包含 10 项核心功能的函数级对照表格（原函数名、移植位置、是否保留、替代实现、等价测试）
- `docs/trace_web_porting_map.md` 明确声明独立实现的算法模块与公开复现的模块边界

## 9. 停止条件
两份文档落盘且无语法或格式错误后停止。
