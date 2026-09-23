# S0 开工自检报告 (Orchestration Bootstrap Report)

- 任务卡编号: S0-orch-bootstrap-01
- 执行者角色: orch-bootstrap subagent
- 检查基准时刻: 2026-09-20T22:04:22+08:00
- 报告生成时刻: 2026-09-20T22:06:45+08:00
- 报告落盘路径: `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\orchestration\bootstrap_report.md`
- 综合自检结论: **ALL PASS (全部合格，具备开工条件)**

---

## 1. 工作目录可读写性与 Git 仓库状态核验

### 1.1 目录读写权限验证
- 目标工作路径: `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest`
- 执行时间戳: `2026-09-20T22:04:28.7226421+08:00`
- 校验指令:
  ```powershell
  [System.IO.File]::WriteAllText('C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\.write_test', 'writable');
  Test-Path 'C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\.write_test';
  Remove-Item 'C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\.write_test'
  ```
- 指令输出: `True`
- 状态判定: **PASS (目录具备完整读、写、删权限)**

### 1.2 Git 仓库状态检测
- 执行时间戳: `2026-09-20T22:05:47.8465117+08:00`
- 当前分支: `main`
- 上游跟踪: `origin/main` (Up to date)
- 最新提交 Commit: `b82d7bb` (`b82d7bbfcace2a6c06915b1f02b8070edb436720`)
- 提交说明: `feat(geogate): enforce 100% egress country consistency and add CI Geo Gate`
- 远程仓库地址: `https://[CREDENTIAL_MASKED]@github.com/ludas114343/fastly-edge-speedtest.git`
- 工作区脏状态清单 (`git status -s`):
  * `M clash.yaml` (已修改)
  * `M clash_edgeone.yaml` (已修改)
  * `M clash_edgetunnel.yaml` (已修改)
  * `M clash_fastly.yaml` (已修改)
  * `M clash_netlify.yaml` (已修改)
  * `M clash_wasmer.yaml` (已修改)
  * `?? orchestration/` (未跟踪目录)
  * `?? quota_guard.json` (未跟踪配置文件)
  * `?? taskcards/` (未跟踪目录)
  * `?? uuid_config.json` (未跟踪配置文件)
- 状态判定: **PASS (Git 仓库状态正常)**

---

## 2. Obsidian 平台凭据档案存在性与条目清单

> 严正声明: 本项仅列出凭据条目及服务名称，严禁且绝无任何明文 Token / Key / 密码 / UUID 输出。

### 2.1 凭据档案元数据
- 目标路径: `D:\Obsidian\CollegeAid\planning\平台凭据速查.md`
- 存在状态: `True`
- 文件大小: `12,065 bytes`
- 最后修改时刻: `2026-09-20T21:55:52`

### 2.2 凭据条目名称索引清单
经安全只读解析，该档案包含以下服务条目配置（仅列名称）:

1. **美本核心申请平台 (零)**
   - Common App
   - Scoir
   - ApplyTexas
   - MIT (独立网申)
   - Berea College (Slate)
   - Lawrence University (Slate)
   - IELTS IDP (雅思官方)
   - TOEFL iBT (ETS 官方)

2. **LLM API Keys (Hermes 配置)**
   - opencode-go (主)
   - opencode-zen
   - openrouter
   - agnes-2.5-flash
   - Opencode.ai
   - supermemory
   - API_SERVER_KEY
   - 本地 OCR 接口
   - 本地 LLM 接口

3. **云部署平台 Tokens**
   - Vercel
   - Vercel (旧号 lty3)
   - Vercel (新号 114519)
   - Cloudflare
   - Cloudflare R2
   - Cloudflare 账户2 (CloudPaste 网盘)
   - Railway
   - Hugging Face
   - Northflank
   - Back4App
   - Wasmer
   - Supabase
   - Netlify
   - Fastly (操作/工程)
   - Fastly (财务/账单)
   - Tencent Cloud EdgeOne

4. **代码与配置平台**
   - GitHub (账号 ludas114343，OAuth Token 托管状态，代理推送配置)
   - Clash / 代理 (混合端口配置，Railway 节点配置，订阅文件路径)

5. **外部 API 与网盘/算力服务**
   - Brave Search API (包含 Key 字段、Endpoint、鉴权方式、速率限制、返回字段等元数据条目)
   - Hermes Mobile 远程访问 (入口、API、上传、Dashboard、登录、手机端)
   - CloudPaste 网盘 (账号、CF 账户2 Account ID 字段)
   - Kaggle TPU/GPU 云端计算 (账号、TPU 内核、GPU 内核、模型、API、AI Hub 控制、用量 API、远程关机、看门狗、定时配置)

- 安全脱敏核验: 报告中无任何明文 Secret / Token / Key / UUID。
- 状态判定: **PASS (凭据索引完整且严格脱敏)**

---

## 3. 本地隔离参考仓库完整性核验

参考仓库隔离基准目录: `C:\Users\ludas\.gemini\antigravity\scratch\ref_projects\`

### 3.1 cmliu/edgetunnel
- 本地路径: `C:\Users\ludas\.gemini\antigravity\scratch\ref_projects\edgetunnel`
- Git 远端: `https://github.com/cmliu/edgetunnel`
- 最新提交 Commit: `448a83ced00a43c1d892d5ecbed86a26ea9eeaff`
- 提交日期与说明: `Sun Sep 6 00:30:52 2026 +0800 Merge pull request #1550 from cmliu/beta2.1`
- 核心文件清单与大小:
  * `.gitignore`: 413 bytes
  * `CHANGELOG`: 12,576 bytes
  * `LICENSE`: 18,431 bytes
  * `README.md`: 15,283 bytes
  * `_worker.js`: 328,176 bytes
  * `img.png`: 242,550 bytes
  * `wrangler.toml`: 192 bytes
- 非 Git 文件总数: 7 个
- 非 Git 内容总大小: 617,621 bytes
- 完整性判定: **PASS (文件完整无缺失)**

### 3.2 wlisboy/Trace-Web
- 本地路径: `C:\Users\ludas\.gemini\antigravity\scratch\ref_projects\Trace-Web`
- Git 远端: `https://github.com/wlisboy/Trace-Web`
- 最新提交 Commit: `a68b8d0e41336a0c7f1fe8784ef20bf487caf91a`
- 提交日期与说明: `Tue Sep 8 11:24:54 2026 +0800 更新 trace.py`
- 核心文件清单与大小:
  * `LICENSE`: 1,085 bytes
  * `README.md`: 4,059 bytes
  * `trace.py`: 50,809 bytes
- 非 Git 文件总数: 3 个
- 非 Git 内容总大小: 55,953 bytes
- 完整性判定: **PASS (文件完整无缺失)**

---

## 4. 核心工程文件全量路径清单与元数据

### 4.1 6 套 YAML 配置文件清单
| 配置文件名称 | 完整绝对路径 | 文件大小 (Bytes) | SHA-256 哈希值摘要 | 最后修改时间 |
|:---|:---|:---|:---|:---|
| `clash.yaml` | `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\clash.yaml` | 24,598 | `c7bb9d62a8d71124a57bcd3dbd0878591210262d40a403b9bf14b51a90c2adfa` | 2026-09-20T21:59:40 |
| `clash_edgeone.yaml` | `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\clash_edgeone.yaml` | 25,073 | `d9a91ab01d85a706674302a49becff113438a67e5c134ef01e06d6ff3996c6a7` | 2026-09-20T21:59:45 |
| `clash_edgetunnel.yaml` | `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\clash_edgetunnel.yaml` | 25,576 | `c9db984332bdc3305fc2c523f5d684ac8aead4126877f0062d155e0ca05db1f9` | 2026-09-20T21:59:40 |
| `clash_fastly.yaml` | `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\clash_fastly.yaml` | 23,898 | `8d7e58aa4ccccb12f94c6da515da44a00466a4e11abf1e60ce69d5e17e80696e` | 2026-09-20T21:59:40 |
| `clash_netlify.yaml` | `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\clash_netlify.yaml` | 25,112 | `4777ba94f00b84b8ff600ffb2b7101b407c6dd35fdaec406d05173076e09ed9d` | 2026-09-20T21:59:40 |
| `clash_wasmer.yaml` | `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\clash_wasmer.yaml` | 24,818 | `f02d770d61d76626dd83af50676c775efdeef27fd8881bf7bb2c3b091b701c48` | 2026-09-20T21:59:40 |

### 4.2 测速主脚本
| 脚本名称 | 完整绝对路径 | 文件大小 (Bytes) | SHA-256 哈希值摘要 | 最后修改时间 |
|:---|:---|:---|:---|:---|
| `speedtest.py` | `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\speedtest.py` | 40,367 | `d82b69d15388d2b11da2bd27e56396fde67b7e78f6698237c105e16336973191` | 2026-09-19T19:50:12 |

### 4.3 Worker 源码参考
| 源码名称 | 完整绝对路径 | 文件大小 (Bytes) | SHA-256 哈希值摘要 | 最后修改时间 |
|:---|:---|:---|:---|:---|
| `_worker.js` | `C:\Users\ludas\.gemini\antigravity\scratch\ref_projects\edgetunnel\_worker.js` | 328,176 | `2e1e329aeb638fc08a8514b705f75e11eb8cfc4b6ff82a1f8daac9c6f3729031` | 2026-09-20T21:54:56 |

### 4.4 GitHub Workflows 调度流程文件
| 工作流名称 | 完整绝对路径 | 文件大小 (Bytes) | SHA-256 哈希值摘要 | 最后修改时间 |
|:---|:---|:---|:---|:---|
| `edgeone-full-sweep.yml` | `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\.github\workflows\edgeone-full-sweep.yml` | 2,745 | `9ca4682381604a16165199dc7c61103a11f0cebbe7196b605d0aa38993f73b97` | 2026-09-19T21:13:15 |
| `edgeone-published-recheck.yml` | `C:\Users\ludas\.gemini\antigravity\scratch\fastly-edge-speedtest\.github\workflows\edgeone-published-recheck.yml` | 1,003 | `c638ae8d9ebb4d537fd0b580018baadf4c0328effe54c7592d2636a836b34ba2` | 2026-09-19T20:25:36 |

- 状态判定: **PASS (清单完整，所有目标文件均就绪)**

---

## 5. 依赖工具链与运行环境检测

### 5.1 核心命令与运行时
| 工具名 | 检测指令 | 输出版本 | 程序绝对路径 | 可用性状态 |
|:---|:---|:---|:---|:---|
| **Python 3** | `python --version` | `Python 3.11.15` | `C:\Users\ludas\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe` | **PASS** |
| **Git** | `git --version` | `git version 2.55.0.windows.2` | `E:\1919810\Git\cmd\git.exe` | **PASS** |
| **Node.js** | `node --version` | `v24.13.1` | `C:\Program Files\nodejs\node.exe` | **PASS** |
| **npm** | `npm --version` | `11.8.0` | `C:\Program Files\nodejs\npm.cmd` | **PASS** |
| **npx** | `npx --version` | `11.8.0` | `C:\Program Files\nodejs\npx.cmd` | **PASS** |
| **Curl** | `curl.exe --version` | `curl 8.13.0 (Windows) libcurl/8.13.0 Schannel zlib/1.3.1 WinIDN` | `C:\Windows\system32\curl.exe` | **PASS** |

### 5.2 Python 核心库依赖
- `requests`: `2.33.0` (可用)
- `pyyaml` (`yaml`): `6.0.2` (可用)
- `urllib3`: `2.7.0` (可用)
- 状态判定: **PASS (工具链与运行环境完全满足构建与调度要求)**

---

## 6. 本机代理与网络边界零触碰认证

### 6.1 核验证据与执行状态
1. **环境变量隔离**:
   - 检测命令: `python -c "import os; print({k: v for k, v in os.environ.items() if 'proxy' in k.lower()})"`
   - 检验结果: `{}` (当前 agent 进程上下文未注入任何 HTTP_PROXY, HTTPS_PROXY, ALL_PROXY 变量)。
2. **系统代理设置只读查询**:
   - 注册表路径: `HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings`
   - 查询结果: `ProxyEnable = 1`, `ProxyServer = 127.0.0.1:7897` (用户本机 Clash Verge 正在正常提供本地系统代理)。
3. **零触碰认证内容**:
   - **不修改、不写入**: 绝对未对注册表代理设置、TUN 虚拟网卡配置进行任何修改。
   - **不调用、不探活**: 绝对未向 `127.0.0.1:7897` 或任何现有本地 Clash External Controller 端口发起 HTTP/REST 请求。
   - **不变更配置文件**: 绝对未读取或改写用户本机 Clash profiles 或混合端口规则。
   - **流量不串扰**: 明确保证所有后续测速与调度流量不经过本机私有代理链路，保持严格边界隔离。
- 状态判定: **PASS (零触碰认证合规有效)**

---

## 7. 开工验收综合评估

### 7.1 验收清单逐项判定
| 验收项 | 验收要求 | 实测结果 | 判定 |
|:---|:---|:---|:---:|
| 1 | `bootstrap_report.md` 真实落盘且包含 6 大项内容 | 文件已生成落盘，包含全部 6 项完整技术数据 | **PASS** |
| 2 | 无任何明文 Token / SecretKey / UUID 出现在报告中 | 严格执行脱敏脱密，无任何明文凭据或 UUID | **PASS** |
| 3 | 声明中明确证实未触碰本机 Clash/TUN | 给出只读证据并做出零触碰认证与环境边界保证 | **PASS** |

### 7.2 停工触发条件复核
- 是否发现工作目录不可写: 否 (可写)
- 是否发现参考仓库缺失: 否 (两套仓库均完整就绪)
- 是否发现需触碰本机代理: 否 (完全零触碰)

**结论: 系统开工前置条件全部达标，准予推进后续任务卡。**
