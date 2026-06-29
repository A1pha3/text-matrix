---
title: "Anthropic Cybersecurity Skills：把 817 个安全分析任务打包成 AI Agent 可直接调用的标准技能库"
date: "2026-06-26T18:07:28+08:00"
slug: "mukul975-anthropic-cybersecurity-skills-guide"
description: "mukul975 维护的开源项目把 817 个网络安全技能按 agentskills.io 标准封装,统一映射到 MITRE ATT&CK、NIST CSF 2.0、MITRE ATLAS、D3FEND、AI RMF 和 MITRE F3 六个框架,支持 Claude Code、Cursor、Codex CLI 等 26+ AI 平台。本文拆解其渐进式披露机制、单技能目录结构与跨框架映射设计,并以 Volatility3 内存取证为案例展示一个安全任务如何被 AI Agent 拆解执行。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "网络安全", "MITRE ATT&CK", "agentskills.io", "开源工具"]
---

## 一句话判断

`mukul975/Anthropic-Cybersecurity-Skills` 不是漏洞扫描器、不是 payload 仓库、也不是写给人类看的安全手册。它把 817 个"资深安全分析师在特定场景下会做的标准操作"按 [agentskills.io](https://agentskills.io) 规范打包成结构化技能单元,每个技能都映射到 6 套主流安全框架(MITRE ATT&CK v19.1、NIST CSF 2.0、MITRE ATLAS v5.4、MITRE D3FEND v1.3、NIST AI RMF 1.0、MITRE F3 v1.1),目的是让 LLM(大语言模型)驱动的 Agent(自主智能体)在执行真实安全任务时,有一套和人类专家同构的决策脚手架。

项目名虽带 "Anthropic",但仓库明确标注是社区项目,与 Anthropic PBC 无隶属关系。

## 系统地图:三轴结构

仓库的核心结构可以用三个正交轴来读:

| 维度 | 数量 | 含义 |
|---|---|---|
| 技能(Skill) | 817 | 单一可执行单元,目录名为 kebab-case(连字符小写),如 `performing-memory-forensics-with-volatility3` |
| 安全领域(Domain) | 29 | 横向分类,涵盖云安全、威胁狩猎、恶意软件分析、IAM、勒索软件防御等 |
| 框架映射(Framework) | 6 | 每个技能同时声明自己对应的 MITRE ATT&CK 战术、CSF 子类、ATLAS 攻击面、D3FEND 防御措施、AI RMF 控制项、F3 欺诈战术 |

这套结构是**领域 × 框架**的双重视角:同一个 `hunting-for-credential-dumping-lsass` 既属于 `digital-forensics` / `endpoint-security` 域,又同时打上 ATT&CK T1003、NIST CSF DE.AE、ATLAS AML.T0047、D3FEND D3-PSMD 等标签。审计和合规时一个 ID 就能跨框架追溯。

仓库当前为 Python 主语言,Stars 21,564(截至 2026-06-26 API 查询),License Apache 2.0,创建于 2026-02-25,最近一次 push 在 2026-06-22。社区活跃:每个 PR 48 小时内由维护者审核,Issues 区有"good first issue"标签。

## 技能单元解剖:SKILL.md 的标准结构

每个技能目录遵循同一套四段式骨架,这是它能被 Agent 直接消费的根本原因:

```
skills/<skill-name>/
├── SKILL.md          # 入口: YAML 元信息 + Markdown 工作流
├── references/       # 深读: 框架映射文档、命令清单
├── scripts/          # 辅助: 可直接调用的脚本
└── assets/           # 模板: 报告模板、检查清单
```

以 `performing-memory-forensics-with-volatility3` 为例,`SKILL.md` 的 YAML frontmatter(前置元数据)声明:

```yaml
---
name: performing-memory-forensics-with-volatility3
description: Analyze volatile memory dumps using Volatility 3 to extract
  running processes, network connections, loaded modules, and evidence of
  malicious activity.
domain: cybersecurity
subdomain: digital-forensics
tags: [forensics, memory-analysis, volatility, ram-analysis,
       malware-detection, incident-response]
nist_csf: [RS.AN-01, RS.AN-03, DE.AE-02, RS.MA-01]
mitre_attack: [T1005, T1074, T1119, T1070, T1059]
version: "1.0"
author: mahipal
license: Apache-2.0
---
```

YAML 字段是 Agent 检索的"索引面":`description` 决定能否被关键词召回,`tags` 决定粗筛粒度,`mitre_attack` / `nist_csf` 决定合规口径。Markdown 正文则是执行面,严格按四个 H2 小节展开:

1. **When to Use**: 触发条件,告诉 Agent 在什么场景下激活这个技能
2. **Prerequisites**: 前置条件,工具、权限、依赖
3. **Workflow**: 步骤化执行,带具体命令与决策分支
4. **Verification**: 验收标准,如何确认执行成功

这种"元信息 vs 步骤"的双层分离不是装饰:它直接对应渐进式披露(progressive disclosure)机制,也是这个项目最核心的工程设计。

## 核心机制:渐进式披露为什么重要

817 个技能如果全量塞进 LLM 上下文,任何 200K 上下文窗口都扛不住。这个项目的解法是**两级 token(模型计量单位)成本**:

- **扫描成本 ≈ 30 tokens/技能**:Agent 只读 frontmatter(约 1KB),可以在一次会话中遍历全部 817 个技能
- **完整加载成本 500–2000 tokens/技能**:只有当某个技能被选中执行时,才把 `SKILL.md` 的 Workflow 段、`references/` 里的命令清单按需注入

具体到一次任务的执行轨迹(README 中给出的"分析内存 dump 中的凭据窃取"案例):

```
User prompt: "Analyze this memory dump for signs of credential theft"

Step 1: Agent 扫描 817 个 frontmatter → 按 tags/description/domain 命中 12 个候选
Step 2: 加载 Top 3:
        - performing-memory-forensics-with-volatility3
        - hunting-for-credential-dumping-lsass
        - analyzing-windows-event-logs-for-credential-access
Step 3: 按 Workflow 逐步执行 vol.py 插件、检查 LSASS 访问模式、关联事件日志
Step 4: 用 Verification 段验证 IOC(失陷指标,即入侵痕迹),把发现映射到 ATT&CK T1003
```

这一步到位的设计绕开了 RAG(检索增强生成,Retrieval-Augmented Generation)常见的"召回不准、注入干扰"问题:Agent 不需要先把整本安全手册切块、嵌入(embedding)、再向量检索,而是直接消费结构化元数据。代价是写入侧更累——每个技能都要手工维护好 frontmatter 和 Workflow,这就是为什么 CONTRIBUTING.md 强调"Add a new skill"是当前最缺的方向(Deception Technology 域只有 2 个技能,Compliance 域 5 个)。

## 跨框架映射:一个技能如何被 6 套体系同时承认

仓库在 README 中以"单技能示例"展示了跨框架映射的实际价值:

| 技能 | ATT&CK | NIST CSF | ATLAS | D3FEND | AI RMF | F3 |
|---|---|---|---|---|---|---|
| `analyzing-network-traffic-of-malware` | T1071 | DE.CM | AML.T0047 | D3-NTA | MEASURE-2.6 | — |
| `detecting-business-email-compromise` | T1566 | DE.AE | — | — | — | F1005.006 |

不同框架之间并不是简单复述,而是有侧重地分配 ID:

- **ATT&CK** 提供战术 ID(T1003 凭据转储、T1071 应用层协议),定位"对手在做什么"
- **D3FEND** 提供防御技术 ID(D3-NTA 网络流量分析),定位"我应该用什么对策"
- **ATLAS** 单独覆盖 AI/ML 系统的对抗威胁(模型权重窃取、提示注入、agent 上下文投毒)
- **AI RMF** 落在 MEASURE/MANAGE 子类,对应 NIST AI 风险管理功能
- **F3**(2026-04-09 发布)补充 ATT&CK 留白的金融欺诈 TTP(战术、技术与过程),把 BEC(商业邮件诈骗)类攻击拉到与初始入侵同等的战术等级

六套体系全打通的代价是:每个技能需要 5–10 分钟手工标注,且任何一方的 ID 体系更新都会触发批量重映射(README 提到 ATT&CK v19 即将把 Defense Evasion 拆成 Stealth / Impair Defenses 两个新战术,会带动一波 mapping 更新)。

## 域与技能分布:29 个安全域,云和取证居前

按 README 提供的统计,Top 10 域如下:

| 域 | 技能数 | 典型场景 |
|---|---|---|
| Cloud Security | 66 | AWS/Azure/GCP 加固、CSPM(云安全态势管理)、云攻击模拟 |
| Threat Hunting | 58 | 假设驱动狩猎、LOTL(无文件攻击)检测、EVTX 日志狩猎 |
| Threat Intelligence | 52 | STIX/TAXII(威胁情报结构化标准/传输协议)、MISP、OpenCTI、行为者画像 |
| Network Security | 43 | IDS/IPS、防火墙规则、VLAN 隔离 |
| Web Application Security | 42 | OWASP Top 10、SQLi、XSS、SSRF、反序列化 |
| Digital Forensics | 41 | 磁盘镜像、内存取证、Hayabusa/KAPE/Plaso 时间线 |
| Malware Analysis | 39 | 静态/动态分析、逆向、沙箱 |
| Identity & Access Mgmt | 37 | Entra ID/ROADtools、设备码钓鱼、零信任身份 |
| SOC Operations | 35 | 告警分诊、升级流程、桌面演练 |
| Red Teaming | 33 | ADCS/Certipy、BloodHound CE、Sliver/Havoc C2、NTLM 中继 |

域的分布偏检测响应和攻击面,而非纯开发侧(DevSecOps 仅 18)。AI Security 域目前 14 个技能,覆盖 LLM 红队(garak/PyRIT)、提示注入、MCP(Model Context Protocol,模型上下文协议)安全等,体现仓库对 AI 系统自身威胁的关注。

## 快速接入:三种方式

仓库提供两种官方安装路径,加上 playground 试用一共三种:

```bash
# 方式 1:npx(推荐)
npx skills add mukul975/Anthropic-Cybersecurity-Skills

# 方式 2:直接克隆
git clone https://github.com/mukul975/Anthropic-Cybersecurity-Skills.git
cd Anthropic-Cybersecurity-Skills
```

完成后,只要你的 Agent 框架遵循 agentskills.io 标准,即可直接加载;覆盖的平台包括 Claude Code、GitHub Copilot、Cursor、Windsurf、Cline、OpenAI Codex CLI、Gemini CLI、Devin、Replit Agent、SWE-agent、LangChain、CrewAI、AutoGen、Semantic Kernel、Haystack、Vercel AI SDK 以及任意 MCP 兼容 agent。

如果只想快速看效果,Casky.ai 提供了 [Playground](https://casky.ai/?utm_source=github&utm_medium=readme&utm_campaign=cohort_launch#waitlist),可以浏览器内直接跑几个真实的威胁狩猎/DFIR(数字取证与事件响应)流程,免安装。

## 适用边界与不适用场景

要把这个仓库当作"安全 AI Agent 基础设施"而不是"安全工具书",需要注意几个边界:

| 适用 | 不适用 |
|---|---|
| 给 LLM 驱动的 Agent 装上"安全分析师"的工作流 | 直接当作漏洞扫描器使用 |
| 把 ATT&CK / CSF / D3FEND 等框架 ID 作为审计与合规的统一口径 | 替代 Splunk / Elastic / Defender 这类生产 SIEM(安全信息与事件管理平台) |
| 蓝队/红队场景下让 Agent 走标准操作流程 | 在生产系统上直接让 Agent 自动执行(技能提供的是工作流,不是带审批的 runtime) |
| 教学:让新人通过结构化模板学会做内存取证、云审计等 | 替代 Pentest 工具链(网络代理、payload 生成) |

另外三点限制值得留意:

1. **不带执行 runtime**:技能只是 Markdown 工作流,Agent 平台决定它能不能真的跑 `vol.py`,仓库不提供沙箱或权限代理
2. **跨框架映射是声明式**:ATT&CK ID 是否准确,依赖各技能贡献者手工核对,可能出现 "ID 存在但工作流并未真正涉及该技术" 的弱映射
3. **仓库节奏依赖社区**:NIST CSF 2.0 的 Govern 函数 2024 年加入,ATLAS 5.4 的 agentic AI 攻击向量 2025 年底加入,跟得很快但需要持续盯;README 提示 ATT&CK v19 在 2026-04-28 落地后,会触发一次 mapping 大改

## 实际收益:什么时候值得引入

如果团队已经在用 Claude Code / Cursor / Codex CLI 跑安全相关任务(告警分诊、内存镜像初查、合规对照),这个仓库的边际收益最高:

- **节省模板编写时间**:每个技能都自带 When-to-Use / Workflow / Verification 骨架,直接复用而不是从零写 prompt
- **审计口径一致**:同一份技能清单可以在 ATT&CK 报告、CSF 自评、D3FEND 对策表里复用,避免"每个分析师一份自查表"
- **可被 Agent 训练 / 微调**:YAML 字段统一格式后,可以把 frontmatter 当作标注数据,反过来训练安全领域专用的检索/分类模型

如果团队还在用纯命令行的 Splunk 查询或者手工 Playbook,且没有引入 AI Agent 的计划,这个仓库的优先级就不高——它本质上是给 Agent 时代的运维/安全人员准备的,而不是给纯人工流程准备的。

## 引用与延伸

学术或商业引用建议使用 README 末尾的 BibTeX 条目(`@software{anthropic_cybersecurity_skills}`),作者署名为 `Jangra, Mahipal`。仓库在 `awesome-agent-skills`、`awesome-ai-security`、`awesome-codex-cli` 等 awesome 列表均有收录,同时被 SkillsLLM、NeverSight/skills_feed 等自动索引。

值得跟踪的外部变量:
- **MITRE ATT&CK v19** 落地后,Defense Evasion 战术拆分带来的 mapping 更新
- **MITRE F3** 从 v1.1 继续迭代,可能扩展到电信欺诈、加密资产欺诈
- 仓库自身从 v1.0.0(2026-03-11,734 技能、26 域)演进到当前 817 技能、6 框架的速度

## 关联资料

- 仓库: <https://github.com/mukul975/Anthropic-Cybersecurity-Skills>
- 标准规范: <https://agentskills.io>
- 试用 Playground: <https://casky.ai>
- 作者: <https://github.com/mukul975>
