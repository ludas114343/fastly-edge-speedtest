# TaskCard: taskcards/phase4/code-auditor-agent.md

## 1. 背景
Code Auditor 独立复核全库代码、配置、候选与订阅，专查假数据、明文凭据与伪造逻辑。

## 2. 唯一目标
1. 检查全库是否存在硬编码延迟、硬编码速度、随机测试结果、虚构国家、虚构 provider、重复 UUID、明文 token、占位域名。
2. 审查候选池中 raw/deduped/rejected 划分与去重规则。
3. 审查脚本确认无任何修改 Windows 注册表、TUN 适配器或系统网络代理的命令。
4. 审查全文字符纯度：0 em-dash (\u2014) 与 0 en-dash (\u2013)。

## 3. 输入路径
- 全库源码、配置文件、JSON 候选池与 YAML 订阅

## 4. 允许操作
- 运行静态代码扫描、AST 分析与正则检索
- 编写审计报告

## 5. 禁止操作
- 严禁包庇任何假常数或未清洗的硬编码
- 严禁在英文注释或文档中使用 em-dash (\u2014) 与 en-dash (\u2013)

## 6. 必须执行的命令或 API
- Python 正则扫描与 AST 语法审查命令

## 7. 必须生成的文件
- `docs/security/code_auditor_v12.md`

## 8. 机器可判定验收条件
- 给出明确各项 PASS / FAIL 判定，附行号证据
- 确认全库无修改本机代理命令，无明文 token

## 9. 停止条件
报告落盘后停止。
