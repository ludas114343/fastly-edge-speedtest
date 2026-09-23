# TaskCard S0-orch-bootstrap-01 @taskcards/S0-orch-bootstrap-01.md

## 背景（自含）
项目目录：C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest。
本阶段为阶段 S0：开工自检。必须由独立 orch-bootstrap subagent 完成系统可用性、路径、凭据档案存在性、克隆仓库存在性、依赖环境检测，产出 bootstrap_report.md。

## 唯一目标
生成 C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\orchestration\bootstrap_report.md，逐项验证系统开工条件并给出明确状态。

## 输入
- 工作目录：C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest
- 隔离参考仓库目录：C:\Users\ludas\.gemini\antigravity\scratch\ref_projects\edgetunnel，C:\Users\ludas\.gemini\antigravity\scratch\ref_projects\Trace-Web
- 凭据档案路径：D:\Obsidian\CollegeAid\planning\平台凭据速查.md

## 必须执行
1. 确认工作目录可读写、Git 仓库状态。
2. 确认 Obsidian 凭据文件存在，列出凭据条目名称（只列条目名，严禁输出任何 Token/Key 值）。
3. 确认 cmliu/edgetunnel 与 wlisboy/Trace-Web 已克隆在本地隔离目录且文件完整。
4. 列出 6 套 YAML 文件、speedtest.py、Worker 源码、GitHub workflows 的完整路径清单及大小。
5. 检查 Python 3、git、node、curl 等环境可用性。
6. 明确核验并声明：未触碰用户本机 Clash/TUN/profile/系统代理。
7. 将自检结果完整落盘至 bootstrap_report.md。

## 禁止事项
- 不触碰用户本机 Clash Verge / Mihomo / TUN / system proxy / profiles；
- 不调用 127.0.0.1 上任何既有 controller；
- 测速流量不得经过用户本机网络或现有代理；
- 凭据只列名字，永不落盘/打印/进 git；
- 不执行跨阶段施工任务。

## 产出（全部落盘）
- C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\orchestration\bootstrap_report.md

## 验收清单（逐条可判 PASS/FAIL）
1. bootstrap_report.md 真实落盘且包含 6 大项内容。
2. 无任何明文 Token / SecretKey / UUID 出现在报告中。
3. 声明中明确证实未触碰本机 Clash/TUN。

## 触发即停工的情况
- 发现工作目录不可写；
- 发现参考仓库缺失；
- 发现需触碰本机代理。
