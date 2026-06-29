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

## 学习目标

在阅读完本文后，你应该能够：

1. **理解 Scientific Agent Skills 的核心价值**：了解为什么 AI 编码助手需要领域特定的技能文档，以及这套合集如何解决科研场景下的工具链调用问题
2. **掌握安装与配置方法**：能够通过 `npx`、GitHub CLI 或手动方式安装技能，并配置到 Cursor、Claude Code、Codex 等 AI 助手
3. **识别适用场景**：判断你的科研工作流是否适合使用 Scientific Agent Skills，以及如何选择合适的技能包
4. **安全使用技能**：了解技能执行的安全风险，掌握使用 Cisco AI Defense Skill Scanner 进行安全扫描的方法
5. **扩展与定制**：了解如何基于现有技能创建自定义技能，或为该开源项目贡献新技能

## 目录

1. [项目概览](#项目概览)
2. [解决的问题](#解决的问题)
3. [核心能力一览](#核心能力一览)
4. [安装方式](#安装方式)
5. [技能内容结构](#技能内容结构)
6. [适用场景与优势](#适用场景与优势)
7. [安全注意事项](#安全注意事项)
8. [相关项目](#相关项目)
9. [自测题](#自测题)
10. [练习](#练习)
11. [进阶路径](#进阶路径)
12. [资料口径说明](#资料口径说明)
13. [总结](#总结)

## 项目概览

[Scientific Agent Skills](https://github.com/K-Dense-AI/scientific-agent-skills) 是 K-Dense-AI 团队维护的一套开源 Agent Skills 合集，目标是把常见的 AI 编码助手（Cursor、Claude Code、Codex 等）变成能够执行复杂科研任务的"AI 科学家"。

该项目最早名为 Claude Scientific Skills，后来随着 [Agent Skills](https://agentskills.io/) 开放标准的推出，升级为通用版本——只要 AI 助手支持这一开放标准，即可使用全部技能。截至本文写作时，仓库累计获得 **21,231 颗 Stars**、**2,333 个 Forks**，在 GitHub 的 AI+科学类项目中关注度高。

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

AI 编码助手本身具备执行任意 Python 代码的能力，但在面对专业科研场景时，往往缺乏针对特定领域工具链的可靠调用经验。Scientific Agent Skills 的做法是为这些领域提供经过验证的技能文档（SKILL.md），包含该领域常用 Python 包或 API 的使用模式、实践建议和代码示例，让 AI 助手在这些场景下表现得更可靠、更高效。

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
- **Use cases and best practices** — 适用场景与实践建议
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
- 活跃维护，持续新增技能并更新依赖包的实践建议

## 安全注意事项

项目文档中明确提示：Skills 可以执行代码并影响 AI 助手的行为，在安装前应阅读每个技能的 SKILL.md，了解它会调用哪些包、访问哪些外部服务。对于社区贡献的技能，建议通过 Cisco AI Defense Skill Scanner 自行扫描：

```bash
uv pip install cisco-ai-skill-scanner
skill-scanner scan /path/to/skill --use-behavioral
```

项目方会定期（约每周）运行安全扫描并更新 [SECURITY.md](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/SECURITY.md)。

## 相关项目

K-Dense-AI 同期开源了 **[K-Dense BYOK](https://github.com/K-Dense-AI/k-dense-byok)**，这是一个免费的桌面端 AI 共同科学家应用，基于 Scientific Agent Skills 构建，支持自备 API Key、可选 40+ 模型、100+ 科学数据库访问，数据保留在本地，也可选择扩展到 Modal 云端处理大规模任务。

## 自测题

以下问题用于检验你对 Scientific Agent Skills 的理解程度：

1. **Scientific Agent Skills 的核心设计理念是什么？**
   <details>
   <summary>点击查看答案</summary>
   通过提供经过验证的技能文档（SKILL.md），包含特定领域常用 Python 包或 API 的使用模式、实践建议和代码示例，让 AI 编码助手在专业科研场景下表现得更可靠、更高效，而不是重新训练模型。
   </details>

2. **这个项目支持哪些 AI 编码助手？**
   <details>
   <summary>点击查看答案</summary>
   支持 Cursor、Claude Code、Codex 等遵循 Agent Skills 开放标准的 AI 编码助手。随着 Agent Skills 标准的推广，更多 AI 助手将会支持。
   </details>

3. **Scientific Agent Skills 包含多少个技能？覆盖哪些领域？**
   <details>
   <summary>点击查看答案</summary>
   包含 135 个技能，覆盖 17 个科学领域：生物信息学与基因组学、化学信息学与药物发现、蛋白质组与质谱、临床研究与精准医学、医疗 AI 与临床机器学习、医学影像与数字病理、机器学习与 AI、材料科学与化学、物理与天文、工程与仿真、数据分析与可视化、地理空间科学与遥感、实验室自动化、科学交流、多组学与系统生物学、蛋白质工程与设计、研究方法论。
   </details>

4. **如何安全地使用社区贡献的技能？**
   <details>
   <summary>点击查看答案</summary>
   在安装前应阅读每个技能的 SKILL.md，了解它会调用哪些包、访问哪些外部服务。对于社区贡献的技能，建议使用 Cisco AI Defense Skill Scanner 自行扫描：`skill-scanner scan /path/to/skill --use-behavioral`。
   </details>

5. **Scientific Agent Skills 与 K-Dense BYOK 的关系是什么？**
   <details>
   <summary>点击查看答案</summary>
   K-Dense BYOK 是一个免费的桌面端 AI 共同科学家应用，基于 Scientific Agent Skills 构建。它支持自备 API Key、可选 40+ 模型、100+ 科学数据库访问，数据保留在本地。
   </details>

## 练习

以下练习帮助你实践使用 Scientific Agent Skills：

### 练习 1：安装并验证 Scientific Agent Skills

**任务**：在你的 AI 编码助手（Cursor/Claude Code/Codex）中安装 Scientific Agent Skills，并验证安装是否成功。

**步骤**：
1. 使用 `npx skills add K-Dense-AI/scientific-agent-skills` 命令安装
2. 打开你的 AI 编码助手，检查是否识别到新技能
3. 尝试调用一个生物信息学相关的技能（如 `database-lookup`），验证它能正确查询公共数据库

**参考答案**：安装成功后，在 AI 助手的技能列表中应该能看到 Scientific Agent Skills 的条目。调用 `database-lookup` 技能时，AI 助手应该能够生成正确的 Python 代码来查询 PubChem、ChEMBL 等数据库。

### 练习 2：使用 Scientific Agent Skills 完成一个科研任务

**任务**：选择一个你熟悉的科研场景（如基因序列分析、分子性质预测、医学影像处理），使用对应的 Scientific Agent Skills 完成一个实际任务。

**步骤**：
1. 确定你的科研任务属于哪个领域（参考"核心能力一览"章节）
2. 找到对应的技能文档（SKILL.md）
3. 在 AI 编码助手中调用该技能
4. 验证生成的代码是否正确、可运行

**参考答案**：以一个基因序列分析任务为例，你可以调用生物信息学相关的技能，AI 助手会生成使用 BioPython 等库的代码，正确读取 FASTA 格式、进行序列比对、注释变异等。

### 练习 3：评估技能质量与安全性

**任务**：选择一个你感兴趣的技能，阅读其 SKILL.md 文档，评估其质量和安全性。

**步骤**：
1. 从 GitHub 仓库浏览技能目录（`skills/` 目录下）
2. 阅读该技能的 SKILL.md 文档
3. 检查是否包含：代码示例、使用模式、实践建议、集成指南
4. 使用 Cisco AI Defense Skill Scanner 扫描该技能（如果是社区贡献的）

**参考答案**：高质量的技能文档应该包含完整的代码示例（可运行）、明确的使用场景说明、潜在问题的实践建议、以及与其他工具集成的指南。安全性方面，应该清楚说明调用的外部服务、需要的 API Key、以及可能的权限需求。

## 进阶路径

如果你希望更深入地使用或贡献 Scientific Agent Skills，可以按照以下路径进行：

1. **掌握多个领域的技能**：不要只停留在你熟悉的领域，尝试了解其他领域的技能，拓展跨学科研究能力
2. **阅读技能源码**：深入阅读 SKILL.md 和配套的代码示例，理解为什么这些使用模式被验证为可靠
3. **贡献新技能**：如果你开发了某个领域的高质量 AI 助手调用经验，可以按照仓库的 CONTRIBUTING.md 指南贡献新技能
4. **定制化技能**：基于现有技能进行定制化修改，适配你的特定科研场景（如特定的数据库、分析流程）
5. **集成到科研工作流**：将 Scientific Agent Skills 集成到你的日常科研流程中，建立标准化的 AI 助手调用规范
6. **参与社区**：加入项目的 Discord 或 GitHub Discussions，与其他科研工作者交流使用经验
7. **反馈与改进**：向项目维护者反馈使用中发现的问题或改进建议，帮助完善技能质量

## 资料口径说明

本文档基于以下来源和假设：

1. **信息来源**：本文主要基于 Scientific Agent Skills 的 GitHub 仓库（https://github.com/K-Dense-AI/scientific-agent-skills）的 README、技能文档和配置信息。所有数字（Stars、Forks、技能数量等）来自仓库公开信息，截至本文写作时（2026-05-14）。
2. **技能覆盖范围**：文章列出了 17 个科学领域，但具体可用的技能数量、每个领域下的技能名称和功能会随项目更新而变化。请以仓库最新版本为准。
3. **安装方式**：文章描述了多种安装方式，但不同 AI 编码助手对 Agent Skills 标准的支持程度可能不同。部分功能可能需要特定版本的 AI 助手才能使用。
4. **安全性评估**：文章提及使用 Cisco AI Defense Skill Scanner 进行安全扫描，但该工具本身可能需要单独安装和配置。扫描结果的解读需要安全专业知识。
5. **K-Dense BYOK 关系**：文章说明 K-Dense BYOK 基于 Scientific Agent Skills 构建，但两个项目的具体集成方式、功能差异需要参考各自文档。
6. **局限性**：本文未深入评估每个技能的实际效果、代码质量、或在不同科研场景下的适用性。这些评估需要结合实际使用经验。

## 总结

Scientific Agent Skills 的做法是给 AI 编码助手补上领域技能文档（SKILL.md），而不是直接改模型权重。好处是立即可用，不需要重新训练。如果你的工作涉及科研数据处理，值得试一试。

项目地址：https://github.com/K-Dense-AI/scientific-agent-skills
