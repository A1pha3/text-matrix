---
title: "Anthropic Cybersecurity Skills：754 个结构化网络安全技能让 AI 智能体具备专家级分析能力"
date: "2026-05-23T20:00:00+08:00"
slug: "anthropic-cybersecurity-skills-ai-agents-security-analysis"
description: "Anthropic Cybersecurity Skills 是开源的网络安全技能库，包含 754 个结构化技能，覆盖 26 个安全领域，映射到 MITRE ATT&CK、NIST CSF 2.0、MITRE ATLAS、D3FEND 和 NIST AI RMF 五大框架。遵循 agentskills.io 标准，可直接用于 Claude Code、GitHub Copilot、Cursor 等平台。"
draft: false
categories: ["技术笔记"]
tags: ["Python", "AI Agent", "网络安全", "MITRE ATT&CK", "自动化"]
---

# Anthropic Cybersecurity Skills：让 AI 智能体具备安全分析能力

一个初级安全分析师知道怎么用 Volatility3 分析可疑内存 dump，知道哪条 Sigma 规则能检测 Kerberoasting，知道怎么跨云服务商做入侵范围评估。**大多数 AI 智能体不知道——除非你把这些技能给它。**

Anthropic Cybersecurity Skills 就是这个"给 AI 智能体注入安全分析能力"的技能库。754 个结构化技能，覆盖 26 个安全领域，每个技能都映射到五大行业框架，遵循 agentskills.io 开放标准，可直接插到 Claude Code、Copilot 和 Cursor 等主流 AI 开发工具里使用。

## 先判断这个项目值不值得看

如果你在以下场景，这个项目直接相关：

- 正在构建 AI 安全智能体，需要结构化的知识库而不是靠 LLM 自由发挥
- 需要把安全分析流程自动化，但不想从零写所有 playbook
- 想让 AI 在 DFIR、渗透测试、威胁情报等任务上达到资深分析师的判断水准

如果你只是需要一些 IOC 列表或检测规则，这个项目不适合——它的核心价值是结构化的**执行流程**，不是数据本身。

## 系统地图

项目结构分为四个层级：

| 层级 | 内容 | 说明 |
|------|------|------|
| 技能库 | 754 个 `.md` 技能文件 | 每个对应一个具体安全任务 |
| 框架映射 | 五框架对照表 | 每个技能链接到 ATT&CK、NIST CSF 等 |
| 目录结构 | `domain/subdomain` 二级分类 | 按技能类型组织 |
| agentskills.io 标准 | YAML frontmatter | 机器可读，AI 快速检索 |

## 五框架映射的价值

这是这个项目最有特色的部分。同一个技能，同时映射到五个不同框架：

| 框架 | 覆盖范围 |
|------|---------|
| MITRE ATT&CK | 14 tactics · 200+ techniques |
| NIST CSF 2.0 | 6 functions · 22 categories |
| MITRE ATLAS | 16 tactics · 84 techniques（AI/ML 威胁） |
| MITRE D3FEND | 7 categories · 267 techniques（防御对策） |
| NIST AI RMF | 4 functions · 72 subcategories（AI 风险管理） |

一个技能文件同时满足五个合规方向。对于需要同时满足多个框架要求的企业，这意味着一个 skill 直接覆盖多个合规检查项，不需要分别维护五套独立的映射表。

**举例**：技能 `analyzing-network-traffic-of-malware` 同时映射到：
- T1071（ATT&CK：应用层协议）
- DE.CM（NIST CSF：持续监控）
- AML.T0047（ATLAS：ML 威胁指标）
- D3-NTA（D3FEND：网络流量分析）
- MEASURE-2.6（NIST AI RMF：AI 度量）

## 26 个安全领域

覆盖范围如下（按技能数量排序，前十）：

| 领域 | 技能数 | 代表能力 |
|------|--------|---------|
| 云安全 | 60 | AWS/Azure/GCP 加固 · CSPM · 云取证 |
| 威胁狩猎 | 55 | 假设驱动狩猎 · LOTL 检测 · 行为分析 |
| 威胁情报 | 50 | STIX/TAXII · MISP · feed 集成 · 攻击者画像 |
| Web 应用安全 | 42 | OWASP Top 10 · SQLi · XSS · SSRF |
| 网络安全 | 40 | IDS/IPS · 防火墙规则 · VLAN · 流量分析 |
| 恶意软件分析 | 39 | 静态/动态分析 · 逆向工程 · 沙箱 |
| 数字取证 | 37 | 磁盘镜像 · 内存取证 · 时间线重构 |
| 安全运营 | 36 | SIEM 关联 · 日志分析 · 告警分诊 |

## 技能解剖

每个技能的目录结构是标准化的：

```
skills/<skill-name>/
├── SKILL.md              # 技能定义（YAML frontmatter + Markdown body）
├── references/
│   ├── standards.md      # 框架映射详情
│   └── workflows.md      # 深度技术步骤参考
├── scripts/
│   └── process.py        # 辅助脚本
└── assets/
    └── template.md       # 填写式检查清单和报告模板
```

YAML frontmatter 包含的关键字段：

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
---
```

AI 读取技能时采用**渐进式加载**：frontmatter 约 30 tokens，完整 workflow 约 500-2,000 tokens。这意味着 AI 可以在单次 context 窗口内扫描全部 754 个技能 frontmatter 找到相关项，然后只加载需要的那几个完整技能，不会撑爆上下文。

## AI 智能体如何使用这些技能

典型工作流（以"分析内存 dump 中的凭证窃取"为例）：

1. **扫描**（约 30 tokens × 754）：AI 读取所有 frontmatter，匹配 `memory-analysis`、`dfir`、`credential-access` 等标签
2. **加载**（500-2,000 tokens × 3）：加载 top 3 匹配技能：`volatility3 内存取证`、`LSASS 凭证窃取狩猎`、`Windows 事件日志分析`
3. **执行**：按 workflow 步骤执行——运行 Volatility3 插件、检查 LSASS 访问模式、关联事件日志证据
4. **验证**：用 Verification 段验证结果，确认 IOC，映射到 ATT&CK T1003

没有这些技能，AI 会猜工具命令、漏关键步骤。有了这些技能，AI 遵循的是资深 DFIR 分析师同款 playbook。

## 与现有安全工具的区别

| 维度 | 传统工具（Volatility、Sigma、YARA） | 本项目 |
|------|-----------------------------------|--------|
| 交付物 | 命令行工具/规则文件/特征库 | 结构化执行流程 + 框架映射 |
| 使用者 | 安全工程师手动操作 | AI 智能体按 playbook 自动执行 |
| 文档化 | 工具文档散落，playbook 缺失 | 每个 skill 内置完整 step-by-step |
| 框架映射 | 单独维护 | 技能自带五框架映射 |

## 快速开始

```bash
# npx（推荐）
npx skills add mukul975/Anthropic-Cybersecurity-Skills

# 或 Git clone
git clone https://github.com/mukul975/Anthropic-Cybersecurity-Skills.git
cd Anthropic-Cybersecurity-Skills
```

支持 Claude Code、GitHub Copilot、OpenAI Codex CLI、Cursor、Gemini CLI，以及任何兼容 agentskills.io 标准的平台。

## 采用建议

**先上的团队：**
- 正在构建 AI 安全智能体/自动化分析流水线的团队
- 有合规需求（多框架覆盖的企业）
- 需要快速让 LLM 具备 DFIR/威胁狩猎能力的团队

**可以等等的团队：**
- 只需要 IOC 列表或简单规则（现有开源规则库够用）
- 团队没有 AI Agent 开发能力
- 安全分析完全依赖人工，自动化场景有限

## 项目元数据

| 项目 | 信息 |
|------|------|
| 仓库 | [mukul975/Anthropic-Cybersecurity-Skills](https://github.com/mukul975/Anthropic-Cybersecurity-Skills) |
| 语言 | Python |
| Stars | 6,902 |
| Forks | 972 |
| 许可证 | Apache 2.0 |
| 主页 | [mahipal.engineer/Anthropic-Cybersecurity-Skills](https://mahipal.engineer/Anthropic-Cybersecurity-Skills/) |

---

⚠️ **社区项目声明**：本项目是独立社区项目，与 Anthropic PBC 无附属关系。