---
title: "Scientific Agent Skills：把 AI 编码助手变成\"AI 科学家\"的 135 个科研技能集合"
date: 2026-05-14T11:42:48+08:00
slug: "scientific-agent-skills-ai-scientist-research-agent"
aliases:
  - "/posts/tech/scientific-agent-skills-research-ai-agent/"
  - "/posts/tech/scientific-agent-skills-ai-scientist-complete-guide/"
description: "Scientific Agent Skills 是 K-Dense-AI 开源的一套 Agent Skills 合集，包含 135 个面向科研场景的即用型技能，覆盖生物信息学、药物发现、临床研究、机器学习等 17 个科学领域，让 Cursor、Claude Code、Codex 等 AI 编码助手可以直接执行复杂的跨学科科研工作流。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "科学研究", "生物信息学", "药物发现", "开源工具"]
---

# Scientific Agent Skills：把 AI 编码助手变成"AI 科学家"的 135 个科研技能集合

## 项目概览

[Scientific Agent Skills](https://github.com/K-Dense-AI/scientific-agent-skills) 是 K-Dense-AI 团队维护的一套开源 Agent Skills 合集，目标是把常见的 AI 编码助手（Cursor、Claude Code、Codex 等）变成能够执行复杂科研任务的"AI 科学家"。

该项目最早名为 Claude Scientific Skills，后来随着 [Agent Skills](https://agentskills.io/) 开放标准的推出，升级为通用版本——只要 AI 助手支持这一开放标准，即可使用全部技能。截至本文写作时，仓库累计获得 **21,231 颗 Stars**、**2,333 个 Forks**，已成为 AI+科学领域最受欢迎的技能集合之一。

| 指标 | 数值 |
|------|------|
| Stars | 21,231 |
| Forks | 2,333 |
| 主要语言 | Python |
| License | MIT |
| 技能总数 | 135 |
| 支持的数据库 | 100+ |
| 创建时间 | 2025-10-19 |

## 解决的问题

AI 编码助手本身具备执行任意 Python 代码的能力，但在面对专业科研场景时，往往缺乏针对特定领域工具链的可靠调用经验。Scientific Agent Skills 的做法是为这些领域提供经过验证的技能文档（SKILL.md），包含该领域常用 Python 包或 API 的使用模式、最佳实践和代码示例，让 AI 助手在这些场景下表现得更可靠、更高效。

## 核心能力一览

135 个技能覆盖以下科研领域：

- **生物信息学与基因组学** — 序列分析、单细胞 RNA-seq、基因调控网络、变异注释、系统发育分析
- **化学信息学与药物发现** — 分子性质预测、虚拟筛选、ADMET 分析、分子对接、先导化合物优化
- **蛋白质组与质谱** — LC-MS/MS 处理、多肽鉴定、蛋白质定量
- **临床研究与精准医学** — 临床试验、药物基因组学、变异解读、临床决策支持
- **医疗 AI 与临床机器学习** — 电子健康记录分析、生理信号处理、医学影像、临床预测模型
- **医学影像与数字病理** — DICOM 处理、全切片图像分析、计算病理、影像工作流
- **机器学习与 AI** — 深度学习、强化学习、时间序列分析、模型可解释性、贝叶斯方法
- **材料科学与化学** — 晶体结构分析、相图、代谢建模、计算化学
- **物理与天文** — 天文数据分析、坐标变换、宇宙学计算、符号数学
- **工程与仿真** — 离散事件仿真、多目标优化、代谢工程、系统建模
- **数据分析与可视化** — 统计分析、网络分析、时间序列、出版级图表、大规模数据处理
- **地理空间科学与遥感** — 卫星影像处理、GIS 分析、空间统计、地形分析
- **实验室自动化** — 液体处理协议、仪器控制、工作流自动化、LIMS 集成
- **科学交流** — 文献综述、科学写作、同行评审、文档处理、海报、幻灯片
- **多组学与系统生物学** — 多模态数据整合、通路分析、网络生物学
- **蛋白质工程与设计** — 蛋白质语言模型、结构预测、序列设计
- **研究方法论** — 假设生成、科研头脑风暴、批判性思维、基金申请书撰写

## 安装方式

支持多种安装途径，最简单的是通过 `npx` 一行命令完成：

```bash
npx skills add K-Dense-AI/scientific-agent-skills
```

也可以使用 GitHub CLI（v2.90.0+）按 agent 类型安装：

```bash
# 安装到指定 agent
gh skill install K-Dense-AI/scientific-agent-skills --agent cursor
gh skill install K-Dense-AI/scientific-agent-skills --agent claude-code
gh skill install K-Dense-AI/scientific-agent-skills --agent codex

# 固定版本
gh skill install K-Dense-AI/scientific-agent-skills --pin v1.0.0
```

## 技能内容结构

每个技能目录下至少包含：

- **SKILL.md** — 完整的技能文档
- **Practical code examples** — 可运行的代码示例
- **Use cases and best practices** — 适用场景与最佳实践
- **Integration guides** — 集成指南
- **Reference materials** — 参考资料

以数据库访问为例，项目提供了统一的 `database-lookup` 技能，可以直接查询 PubChem、ChEMBL、UniProt、COSMIC、ClinicalTrials.gov 等 78 个公共数据库，同时还有针对 DepMap、Imaging Data Commons、PrimeKG、U.S. Treasury Fiscal Data 等的独立技能。BioServices（约 40 个生物信息服务）、BioPython（38 个 NCBI 子库）、gget（20+ 基因组数据库）等套餐进一步扩展了覆盖范围。

## 适用场景与优势

**适合的场景：**

- 需要在多个科学数据库之间交叉查询的文献调研
- 药物靶点筛选、分子性质预测等计算化学工作流
- 单细胞测序、基因变异注释等生物信息学分析
- 医学影像批量处理、DICOM 格式转换
- 卫星遥感数据的地物分类与时空分析
- 科学论文、基金申请书的辅助撰写

**优势：**

- 跳过各工具的 API 文档研究，直接获得经过验证的调用路径
- 每个技能提供测试过的代码示例，减少 AI"幻觉"代码的概率
- 支持多步骤复杂科研工作流的自动化编排
- 活跃维护，持续新增技能并更新依赖包的最佳实践

## 安全注意事项

项目文档中明确提示：Skills 可以执行代码并影响 AI 助手的行为，在安装前应阅读每个技能的 SKILL.md，了解它会调用哪些包、访问哪些外部服务。对于社区贡献的技能，建议通过 Cisco AI Defense Skill Scanner 自行扫描：

```bash
uv pip install cisco-ai-skill-scanner
skill-scanner scan /path/to/skill --use-behavioral
```

项目方会定期（约每周）运行安全扫描并更新 [SECURITY.md](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/SECURITY.md)。

## 相关项目

K-Dense-AI 同期开源了 **[K-Dense BYOK](https://github.com/K-Dense-AI/k-dense-byok)**，这是一个免费的桌面端 AI 共同科学家应用，基于 Scientific Agent Skills 构建，支持自备 API Key、可选 40+ 模型、100+ 科学数据库访问，数据保留在本地，也可选择扩展到 Modal 云端处理大规模任务。

## 总结

Scientific Agent Skills 代表了一种将通用 AI 编码助手扩展到专业科研领域的务实路径——不重新训练模型，而是通过高质量的技能文档让现有模型在特定领域表现得更可靠。对于需要频繁与科学数据打交道的开发者或科研人员来说，这是一个值得关注的效率工具。

项目地址：https://github.com/K-Dense-AI/scientific-agent-skills
