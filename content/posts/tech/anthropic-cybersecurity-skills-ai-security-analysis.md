+++
date = '2026-05-24T00:00:00+08:00'
draft = false
title = 'Anthropic Cybersecurity Skills：Claude AI 安全分析工具包'
slug = 'anthropic-cybersecurity-skills-ai-security-analysis'
description = 'Anthropic-Cybersecurity-Skills 是一套基于 Claude AI 的网络安全分析工具集，通过预置 Agent Skills 将 Claude 推理能力与安全分析场景结合，覆盖威胁分析、漏洞检测和渗透测试。'
categories = ['技术笔记']
tags = ['AI', '安全', 'Claude', 'Agent']
+++

# Anthropic Cybersecurity Skills：Claude AI 安全分析工具包

Anthropic Cybersecurity Skills 是一个面向 AI Agent 的网络安全技能库，仓库地址 <https://github.com/mukul975/Anthropic-Cybersecurity-Skills>，作者 mukul975，许可证 Apache-2.0。项目把 754 条结构化安全技能按 26 个领域组织，每条技能映射到 5 个行业框架（MITRE ATT&CK、NIST CSF 2.0、MITRE ATLAS、MITRE D3FEND、NIST AI RMF），兼容 Claude Code、GitHub Copilot、OpenAI Codex CLI、Cursor、Gemini CLI 等 26 个以上 AI 平台。需要先说清楚的一点：这是社区项目，README 明确声明 Not affiliated with Anthropic PBC，不是 Anthropic 官方产品。

这篇文章要回答的问题是：这个技能库和传统的 SAST（Static Application Security Testing）/DAST（Dynamic Application Security Testing）工具是什么关系，它能做什么、不能做什么，以及安全团队该怎么把它放进现有工作流。

## 项目定位与事实边界

先把这个项目的几个关键事实钉死，避免后面讨论时把"技能库"和"工具"混为一谈。

| 维度 | 事实 |
|------|------|
| 仓库 | `mukul975/Anthropic-Cybersecurity-Skills` |
| 许可证 | Apache-2.0 |
| 技能数量 | 754 条结构化技能 |
| 领域覆盖 | 26 个安全领域 |
| 框架映射 | MITRE ATT&CK v18、NIST CSF 2.0、MITRE ATLAS v5.4、MITRE D3FEND v1.3、NIST AI RMF 1.0 |
| 兼容平台 | Claude Code、GitHub Copilot、OpenAI Codex CLI、Cursor、Gemini CLI 等 26+ |
| 技能标准 | agentskills.io 开放标准 |
| 单技能扫描成本 | 约 30 tokens（仅 frontmatter） |
| 单技能完整加载 | 500-2000 tokens |
| 项目性质 | 社区项目，非 Anthropic 官方 |

这个项目本质是一个知识库，不是可执行的安全扫描工具。它不直接检测漏洞，不直接抓包，不直接跑 exploit。它做的是把"资深安全分析师的决策流程"编码成 AI Agent 可以读取和执行的技能文件，让 Agent 在面对安全任务时有一套可遵循的工作流，而不是靠模型自己猜。

## 为什么需要它

ISC2 的数据显示 2024 年全球网络安全岗位缺口达到 480 万。AI Agent 可以帮着补这个缺口，但前提是 Agent 得有结构化的领域知识。现在的通用大模型能写代码、能搜索，但缺少"什么时候用什么技术、执行前检查什么、怎么验证结果"这类实操判断。现有的安全工具仓库给的是字典、payload 或 exploit 代码，没有给 Agent 一套决策工作流。

这个项目填的就是这个缺口。每条技能编码的是真实从业者的工作流，不是模型生成的摘要。

## 技能库结构

### 目录组织

每条技能遵循统一的目录结构：

```text
skills/performing-memory-forensics-with-volatility3/
├── SKILL.md          # 技能定义（YAML frontmatter + Markdown 正文）
├── references/
│   ├── standards.md  # MITRE ATT&CK、ATLAS、D3FEND、NIST 映射
│   └── workflows.md  # 深度技术流程参考
├── scripts/
│   └── process.py    # 可用的辅助脚本
└── assets/
    └── template.md   # 检查清单和报告模板
```

### YAML frontmatter 示例

```yaml
---
name: performing-memory-forensics-with-volatility3
description: >-
  Analyze memory dumps to extract running processes, network connections,
  injected code, and malware artifacts using the Volatility3 framework.
domain: cybersecurity
subdomain: digital-forensics
tags: [forensics, memory-analysis, volatility3, incident-response, dfir]
atlas_techniques: [AML.T0047]
d3fend_techniques: [D3-MA, D3-PSMD]
nist_ai_rmf: [MEASURE-2.6]
nist_csf: [DE.CM-01, RS.AN-03]
version: "1.2"
author: mukul975
license: Apache-2.0
---
```

frontmatter 字段包括：`name`（kebab-case，1-64 字符）、`description`（关键词丰富，便于 Agent 发现）、`domain`、`subdomain`、`tags`、`atlas_techniques`（MITRE ATLAS ID）、`d3fend_techniques`（MITRE D3FEND ID）、`nist_ai_rmf`（NIST AI RMF 引用）、`nist_csf`（NIST CSF 2.0 类别）。MITRE ATT&CK 技术映射记录在每条技能的 `references/standards.md` 里，并在 release 资产里附带 ATT&CK Navigator 层文件。

### Markdown 正文结构

```markdown
## When to Use
触发条件——AI Agent 什么时候应该激活这条技能

## Prerequisites
所需工具、访问权限、环境配置

## Workflow
分步执行指南，包含具体命令和决策点

## Verification
如何确认这条技能执行成功
```

这种结构的设计意图是让 Agent 能按"判断是否适用 → 检查前置条件 → 执行工作流 → 验证结果"的顺序跑完一个完整任务，而不是只生成一段文字回答。

## 26 个安全领域覆盖

技能按 26 个领域分布，下面列出几个主要领域的技能数量和能力方向。

| 领域 | 技能数 | 能力方向 |
|------|--------|----------|
| Cloud Security | 60 | AWS、Azure、GCP 加固、CSPM、云取证 |
| Threat Hunting | 55 | 假设驱动狩猎、LOTL 检测、行为分析 |
| Threat Intelligence | 50 | STIX/TAXII、MISP、情报源集成、攻击者画像 |
| Web Application Security | 42 | OWASP Top 10、SQLi、XSS、SSRF、反序列化 |
| Network Security | 40 | IDS/IPS、防火墙规则、VLAN 分段、流量分析 |
| Malware Analysis | 39 | 静态/动态分析、逆向工程、沙箱 |
| Digital Forensics | 37 | 磁盘镜像、内存取证、时间线重建 |
| Security Operations | 36 | SIEM 关联、日志分析、告警分诊 |
| Identity & Access Management | 35 | IAM 策略、PAM、零信任身份、Okta、SailPoint |
| SOC Operations | 33 | Playbook、升级流程、指标、桌面演练 |
| Container Security | 30 | K8s RBAC、镜像扫描、Falco、容器取证 |
| Vulnerability Management | 25 | Nessus、扫描工作流、补丁优先级、CVSS |
| Incident Response | 25 | 入侵遏制、勒索软件响应、IR Playbook |
| Red Teaming | 24 | 全范围演练、AD 攻击、钓鱼模拟 |
| Penetration Testing | 23 | 网络、Web、云、移动、无线渗透 |

完整 26 个领域的清单在仓库 README 里，包括 OT/ICS Security、API Security、Endpoint Security、DevSecOps、Phishing Defense、Cryptography、Zero Trust Architecture、Mobile Security、Ransomware Defense、Compliance & Governance、Deception Technology。

## 五框架映射

这个项目的一个差异化卖点是每条技能同时映射到 5 个行业框架，这在开源技能库里是独一份。

| 框架 | 版本 | 覆盖范围 | 映射内容 |
|------|------|----------|----------|
| MITRE ATT&CK | v18 | 14 战术、200+ 技术 | 对手行为和 TTP |
| NIST CSF 2.0 | 2.0 | 6 功能、22 类别 | 组织安全态势 |
| MITRE ATLAS | v5.4 | 16 战术、84 技术 | AI/ML 对抗威胁 |
| MITRE D3FEND | v1.3 | 7 类别、267 技术 | 防御性对抗措施 |
| NIST AI RMF | 1.0 | 4 功能、72 子类别 | AI 风险管理 |

举一个跨框架映射的例子：技能 `analyzing-network-traffic-of-malware` 同时映射到 ATT&CK T1071、NIST CSF DE.CM、ATLAS AML.T0047、D3FEND D3-NTA、AI RMF MEASURE-2.6。这意味着同一条技能执行后，可以同时满足 5 个合规框架的检查点。

需要留意的是 ATT&CK v19 在 2026 年 4 月 28 日发布，把 Defense Evasion（TA0005）拆成了 Stealth 和 Impair Defenses 两个新战术。README 说明技能映射会在后续版本更新，当前仓库里的映射仍基于 v18。

## 任务流案例：内存取证分析

把前面的结构串起来，看一个具体任务怎么流过系统。场景是用户给 Agent 一个提示："分析这个内存镜像，看有没有凭证窃取痕迹"。

```text
用户提示: "Analyze this memory dump for signs of credential theft"

Agent 内部流程:

1. 扫描 754 条技能的 frontmatter（每条约 30 tokens）
   → 通过 tags、description、domain 匹配，识别出 12 条相关技能

2. 加载匹配度最高的 3 条:
   • performing-memory-forensics-with-volatility3
   • hunting-for-credential-dumping-lsass
   • analyzing-windows-event-logs-for-credential-access

3. 按技能的 Workflow 部分逐步执行
   → 运行 Volatility3 插件，检查 LSASS 访问模式，
     与事件日志证据关联

4. 用技能的 Verification 部分验证结果
   → 确认 IOC，把发现映射到 ATT&CK T1003（Credential Dumping）
```

如果没有这些技能，Agent 会自己猜该跑什么命令，容易漏掉关键步骤。有了技能之后，Agent 跑的是资深 DFIR（Digital Forensics and Incident Response）分析师会用的同一套 playbook。

这个流程里有一个设计要点：渐进式披露（progressive disclosure）。Agent 先用约 30 tokens 扫描每条技能的 frontmatter，只在命中时才完整加载（500-2000 tokens）。这样 754 条技能可以在一次扫描里过完，不会撑爆上下文窗口。

## 安装与使用

### 通过 npx 安装（推荐）

```bash
npx skills add mukul975/Anthropic-Cybersecurity-Skills
```

### 通过 Git 克隆

```bash
git clone https://github.com/mukul975/Anthropic-Cybersecurity-Skills.git
cd Anthropic-Cybersecurity-Skills
```

装完之后，技能文件会被 Claude Code、GitHub Copilot、OpenAI Codex CLI、Cursor、Gemini CLI 等兼容 agentskills.io 标准的平台自动发现。不需要额外配置 API Key 给这个项目本身——它不调用任何 API，只是给 Agent 提供技能文件。

需要澄清一个常见误解：这个项目不是 pip 包，没有 `pip install cybersecurity-skills` 这样的安装方式，也没有 `cybersecurity-skills analyze` 这样的命令行工具。它是一个技能文件库，由宿主 AI 平台读取和执行。

## 与传统 SAST/DAST 工具的对比

把这个技能库和传统安全工具放在一起看，差异主要在"做什么"和"谁来做"上。

| 维度 | Anthropic Cybersecurity Skills | SAST（如 Semgrep、CodeQL） | DAST（如 Burp Suite、ZAP） |
|------|-------------------------------|-----------------------------|----------------------------|
| 形态 | AI Agent 技能文件库 | 静态代码扫描器 | 动态运行时扫描器 |
| 执行主体 | AI Agent（Claude、Copilot 等） | 扫描引擎本身 | 扫描引擎本身 |
| 输入 | 自然语言任务 + 上下文 | 源代码 | 运行中的 Web 应用 |
| 输出 | 结构化分析报告 + 框架映射 | 漏洞列表 + 代码位置 | 漏洞列表 + 请求/响应证据 |
| 误报率 | 取决于 Agent 推理质量 | 规则驱动，误报可控 | 规则驱动，误报可控 |
| 覆盖面 | 26 个领域，广但浅 | 单一领域（代码缺陷），深 | 单一领域（运行时漏洞），深 |
| 框架映射 | 5 框架同时映射 | 通常无 | 通常无 |
| 可重复性 | 取决于 Agent 温度和上下文 | 确定性 | 确定性 |

这个对比能看出边界：SAST 和 DAST 是确定性工具，同一段代码跑十次结果一样；技能库驱动的是 AI Agent，结果会受模型、温度、上下文影响。技能库的价值不在替代扫描器，而在给 Agent 提供决策框架，让 Agent 在面对日志、流量、代码时知道该按什么流程分析、该映射到哪个框架。

## 适用人群与边界

### 适合的人

- 安全工程师和渗透测试人员：用 Agent 辅助编排测试流程，减少手动查 playbook 的时间。
- 安全研究员和威胁情报分析师：用技能里的框架映射快速定位 ATT&CK、ATLAS 技术 ID。
- 企业安全团队：把技能库作为 Agent 的知识底座，统一分析口径和报告格式。
- 安全学习者：通过技能文件学习从业者工作流，每条技能就是一个完整案例。

### 不能做的事

这个技能库不替代专业工具。具体来说：

- 它不直接扫描代码漏洞，SAST 工具（Semgrep、CodeQL、Snyk）该用还得用。
- 它不直接跑渗透测试，Burp Suite、Metasploit、Nmap 该用还得用。
- 它不直接做内存取证，Volatility3、Rekall 该用还得用。
- 它不替代 SIEM 的实时告警，Splunk、Elastic Security、Microsoft Sentinel 该用还得用。

它做的是让 AI Agent 在使用这些工具时有一套结构化的决策流程，而不是随机调用。技能里的 `scripts/` 目录会提供辅助脚本，但主流程还是 Agent 调用宿主平台的能力去执行。

## 采用建议

给考虑采用这个技能库的团队三条顺序建议。

第一，先在 Claude Code 或 Cursor 里装上，挑 3-5 条和你日常工作相关的技能试跑。比如做 Web 安全的就挑 Web Application Security 领域的技能，做事件响应的就挑 Incident Response 和 Digital Forensics 领域的。这一步验证技能的工作流是否和你团队的实际流程对得上。

第二，如果技能工作流和你团队流程有差异，fork 仓库改 SKILL.md 的 Workflow 部分。技能文件是纯 Markdown + YAML，修改成本很低。改完之后在团队内部用 Git 子树或 submodule 的方式同步，保证所有人用同一版本。

第三，如果要满足合规要求（比如 SOC 2、ISO 27001），重点看技能的框架映射字段。每条技能执行后产出的报告可以带上 ATT&CK、NIST CSF 的技术 ID，直接作为合规证据归档。这一步需要配合报告生成流程，技能库本身不生成报告，报告由宿主 Agent 根据技能的 `assets/template.md` 模板生成。

适用边界：这个技能库适合已经用 AI Agent 做安全分析的团队，作为 Agent 的知识底座。如果团队还没有 Agent 工作流，先建 Agent 工作流再装技能库，顺序不能反。如果团队坚持纯人工流程或纯工具流程，这个技能库的价值发挥不出来，装了也是吃灰。
