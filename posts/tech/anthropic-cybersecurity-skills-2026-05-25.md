---
title: "Anthropic-Cybersecurity-Skills：给 AI agent 一个专家级安全知识库"
date: "2026-05-25T11:30:00+08:00"
slug: "anthropic-cybersecurity-skills-ai-agent"
description: "Anthropic-Cybersecurity-Skills 是目前规模最大的开源 AI agent 网络安全技能库，754个技能覆盖26个安全领域，所有技能均映射至 MITRE ATT&CK、NIST CSF 2.0、MITRE ATLAS、MITRE D3FEND、NIST AI RMF 五大框架。本文深入剖析 agentskills.io 标准设计、目录结构、五框架映射机制，并通过真实任务流展示 AI agent 如何借助结构化技能执行专家级安全分析。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "网络安全", "Anthropic", "MITRE ATT&CK", "AI Agent", "Claude Code", "agentskills.io"]
---

## 核心判断

Anthropic-Cybersecurity-Skills 解决的根本问题不是"让 AI 搜索安全文档"，而是**给 AI agent 一个结构化的安全专家知识库**，使其在威胁狩猎、事件响应、渗透测试等任务中能够按已知 playbook 执行，而不是靠概率生成操作步骤。

这个仓库的核心价值在于：它将 754 个网络安全技能的 YAML frontmatter 开放给 AI 做毫秒级检索，同时提供完整的 Markdown 执行流程，使 AI agent 的决策路径从"猜命令"变为"查表执行"。

> ⚠️ 社区项目，与 Anthropic PBC 无附属关系。

---

## 系统总览：三个子系统如何协作

这套技能库由三个相互依赖的子系统构成，缺一不可：

```
┌─────────────────────────────────────────────────────┐
│                 agentskills.io 标准层               │
│  YAML frontmatter（技能元数据，供 agent 快速检索）    │
├─────────────────────────────────────────────────────┤
│               技能内容层（Markdown 正文）             │
│  When to Use / Prerequisites / Workflow / Verification│
├─────────────────────────────────────────────────────┤
│              参考文件层（框架映射 + 技术细节）        │
│  MITRE ATT&CK · ATLAS · D3FEND · NIST CSF · AI RMF │
└─────────────────────────────────────────────────────┘
```

**前端检索层**负责在 ~30 tokens 成本内扫描全部 754 个技能 frontmatter，返回候选技能列表；**中端执行层**负责在 500–2,000 tokens 成本内加载完整技能正文，提供分步操作指南；**后端映射层**负责将每个技能关联到五大行业框架的对应条目，使安全分析结果可以直接用于合规报告。

---

## agentskills.io 标准：技能如何被 AI 发现

agentskills.io 是一个开放标准，定义了网络安全技能的机器可读格式。每个技能目录下包含：

```
skills/performing-memory-forensics-with-volatility3/
├── SKILL.md              ← YAML frontmatter + Markdown 正文
├── references/
│   ├── standards.md      ← 框架映射（ATT&CK、ATLAS、D3FEND、NIST）
│   └── workflows.md      ← 深层技术参考
├── scripts/
│   └── process.py        ← 辅助脚本
└── assets/
    └── template.md       ← 填充式检查清单和报告模板
```

### YAML frontmatter 的关键字段

以 `performing-memory-forensics-with-volatility3` 技能为例：

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

`description` 是 AI agent 扫描时的主要匹配字段，设计上要求 keyword-rich，使得基于 embedding 或关键词的检索都能命中。MITRE ATT&CK 的 technique 映射放在每个技能的 `references/standards.md` 中，通过 release 包里的 ATT&CK Navigator layer 文件提供可视化覆盖图。

### 渐进式 token 消耗设计

这套设计的核心约束是 **AI agent 的 context window 有限**：

- **前端扫描**：754 个技能的 frontmatter 总计约 ~22,620 tokens（754 × 30），一次 LLM 调用可以全部扫描
- **中端加载**：单个技能完整加载 500–2,000 tokens，只在需要执行时加载
- **后端深读**：参考文件（workflows.md、standards.md）按需加载，不在扫描路径上

这意味着 agent 可以在一次 context 中完成"全库检索 → 选优 → 执行"三步，而不需要对每个技能都做完整加载。

---

## 五框架映射：每项技能的五个身份证

这是目前唯一将单一技能库同时映射到五个行业框架的开源项目：

| 框架 | 版本 | 覆盖范围 | 本仓库映射内容 |
|------|------|----------|---------------|
| MITRE ATT&CK | v18 | 14 tactics · 200+ techniques | 对手行为与 TTP |
| NIST CSF 2.0 | 2.0 | 6 functions · 22 categories | 组织安全态势 |
| MITRE ATLAS | v5.4 | 16 tactics · 84 techniques | AI/ML 对抗威胁 |
| MITRE D3FEND | v1.3 | 7 categories · 267 techniques | 防御性对抗措施 |
| NIST AI RMF | 1.0 | 4 functions · 72 subcategories | AI 风险管理 |

一个技能映射到五个框架的实例：

| 技能 | ATT&CK | NIST CSF | ATLAS | D3FEND | NIST AI RMF |
|------|--------|----------|-------|--------|-------------|
| analyzing-network-traffic-of-malware | T1071 | DE.CM | AML.T0047 | D3-NTA | MEASURE-2.6 |

对于 SOC 分析师来说，这意味着技能执行结果可以直接填入合规报告的对应章节，无需手动二次映射。对于 AI agent 来说，这意味着它可以同时以 ATT&CK 视角和 NIST CSF 视角给出分析结论。

---

## 26 个安全领域：目录树设计

754 个技能分布在 26 个安全领域，部分领域技能数量：

| 安全领域 | 技能数 | 核心能力 |
|----------|--------|----------|
| Cloud Security | 60 | AWS/Azure/GCP 加固 · CSPM · 云取证 |
| Threat Hunting | 55 | 假设驱动狩猎 · LOTL 检测 · 行为分析 |
| Threat Intelligence | 50 | STIX/TAXII · MISP · 威胁情报源 · 攻击者画像 |
| Web Application Security | 42 | OWASP Top 10 · SQLi · XSS · SSRF · 反序列化 |
| Network Security | 40 | IDS/IPS · 防火墙规则 · VLAN 分割 · 流量分析 |
| Malware Analysis | 39 | 静态/动态分析 · 逆向工程 · 沙箱 |
| Digital Forensics | 37 | 磁盘镜像 · 内存取证 · 时间线重建 |
| Container Security | 30 | K8s RBAC · 镜像扫描 · Falco · 容器取证 |

值得注意的是，**Deception Technology（2个技能）和 Compliance & Governance（5个技能）** 是当前技能数量最少的领域，项目在 CONTRIBUTING.md 中明确标注这两个领域最需要社区贡献。

---

## 任务流案例：AI agent 如何用技能分析内存镜像

以下是一次完整任务在系统中的流转路径：

**用户 prompt**：`"Analyze this memory dump for signs of credential theft"`

**Step 1 — 前端扫描**（~30 tokens × 754 ≈ 22,620 tokens）
agent 扫描全部 754 个 frontmatter，通过 `description` 字段匹配和 `tags` 过滤，返回 Top-12 相关技能候选列表。

**Step 2 — 精选加载**（500–2,000 tokens × 3 = ~4,500 tokens）
加载相关性最高的三个技能：
- `performing-memory-forensics-with-volatility3`
- `hunting-for-credential-dumping-lsass`
- `analyzing-windows-event-logs-for-credential-access`

**Step 3 — 执行 Workflow**（以 `performing-memory-forensics-with-volatility3` 为例）
```bash
# 1. 识别内存镜像的操作系统
volatility3 -f memory_dump.raw windows.info

# 2. 列出运行进程，查找异常
volatility3 -f memory_dump.raw windows.pslist

# 3. 检查 LSASS 进程访问模式（凭证转储关键路径）
volatility3 -f memory_dump.raw windows.lsass

# 4. 转储可疑进程
volatility3 -f memory_dump.raw -o ./dumps windows.memmap --pid <PID>
```

**Step 4 — Verification**
对照技能的 Verification 章节，确认 IOC 指标、检查 ATT&CK T1003（Credential Dumping）映射是否成立。

**Step 5 — 框架报告生成**
执行结果按五大框架分类输出，可直接用于合规文档对应章节。

---

## 能力边界：不是万能的

这套技能库有明确的适用边界，理解它不能做什么比了解它能做什么更重要。

**它解决的**：
- AI agent 不知道该用什么工具、什么命令的问题
- 安全分析流程缺乏结构化步骤的问题
- 分析结果无法直接映射到合规框架的问题

**它不解决的**：
- 实时恶意软件检测（技能库是离线 playbook，不是实时监控）
- 零日漏洞识别（playbook 依赖已知技术模式）
- 误报消除（最终判断仍需人类分析师）

值得注意的是，这个仓库的 v1.0.0 发布于 2026 年 3 月 11 日，v1.2.0 是当前最新版本，仍处于活跃开发阶段。ATT&CK Navigator layer 和五框架映射覆盖范围在持续更新中，部分技能的框架映射丰富度存在差异。

---

## 兼容平台与集成方式

支持三类集成路径：

**零配置集成**（agentskills.io 兼容平台）：
```bash
npx skills add mukul975/Anthropic-Cybersecurity-Skills
```
支持平台：Claude Code、GitHub Copilot、Cursor、Windsurf、Cline、Aider、Continue、Roo Code、Amazon Q Developer、Tabnine、Sourcegraph Cody、JetBrains AI。

**CLI 集成**：OpenAI Codex CLI、Gemini CLI。

**框架集成**：LangChain、CrewAI、AutoGen、Semantic Kernel、Haystack、Vercic AI SDK、任意 MCP 兼容 agent。

---

## 采用建议

| 团队类型 | 建议 |
|----------|------|
| SOC 自动化团队 | 优先集成，用于告警分诊和事件响应的结构化编排 |
| 威胁狩猎团队 | 使用 Threat Hunting 领域技能增强 hypothesis-driven hunt |
| Red Team / 渗透测试 | 使用 Red Teaming 和 Penetration Testing 领域技能构建自动化评估流程 |
| AI 安全研究团队 | 参考五框架映射方法，构建自己的技能库标准 |
| 初级安全分析师 | 结合 Casky.ai Playground 实践，以技能库为学习路径 |

Cloud Security（60技能）和 Threat Hunting（55技能）是目前技能最密集的两个领域，可以优先探索。

---

## 总结

Anthropic-Cybersecurity-Skills 的核心价值不是 754 这个数字本身，而是它证明了**结构化的专家知识可以让 AI agent 脱离"命令猜测器"的定位**。通过 agentskills.io 标准将技能开放给机器检索，通过五框架映射将分析结果直接嵌入合规流程，通过目录树设计将 26 个安全领域组织成可发现的技能网络——这是一套完整的"AI 安全专家知识管理"工程方案。

如果你正在构建 AI 安全分析 pipeline，或在研究如何给 autonomous agent 注入专业领域能力，这个仓库的架构设计比技能本身更值得参考。
