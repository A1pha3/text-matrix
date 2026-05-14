---
title: "Scientific Agent Skills：135个科研技能让AI变成全能科学家"
date: "2026-05-14T16:06:00+08:00"
slug: "scientific-agent-skills-research-ai-agent"
description: "Scientific Agent Skills是K-Dense维护的开源项目，收录135个科研技能，覆盖癌症基因组学、药物发现、单细胞RNA-seq、量子计算、材料科学等18个领域，兼容Cursor、Claude Code、Codex等主流AI编码Agent，让AI真正能做科研工作。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "科学研究", "生物信息学", "Python", "开源", "药物发现"]
---

# Scientific Agent Skills：135个科研技能让AI变成全能科学家

## 项目概览

**Scientific Agent Skills** 由 K-Dense 维护，是一个收录了 **135 个可直接使用的科研技能**的开源仓库，当前星数 **21,352**，Forks 2,346。项目经历了从 Claude Scientific Skills 到 Scientific Agent Skills 的品牌升级，核心变化是：从仅支持 Claude 扩展为支持任何实现了 [Agent Skills](https://agentskills.io/) 开放标准的 AI Agent，包括 Cursor、Claude Code、Codex 等。

项目的设计理念是：虽然 AI Agent 本身可以用任何 Python 包或 API，但这些显式定义的技能通过配套文档和示例，显著提升了在特定科研工作流中的可靠性和效果。

## 技能覆盖领域

135 个技能横跨18个科研方向：

| 领域 | 覆盖内容 |
|------|---------|
| 🧬 生物信息学与基因组学 | 序列分析、单细胞 RNA-seq、基因调控网络、变异注释、系统发育分析 |
| 🧪 化学信息学与药物发现 | 分子属性预测、虚拟筛选、ADMET 分析、分子对接、先导化合物优化 |
| 🔬 蛋白质组学与质谱 | LC-MS/MS 处理、肽段鉴定、谱图匹配、蛋白质定量 |
| 🏥 临床研究与精准医学 | 临床试验、药物基因组学、变异解读、药物安全、临床决策支持 |
| 🧠 医疗AI与临床ML | 电子病历分析、生理信号处理、医学影像、临床预测模型 |
| 🖼️ 医学影像与数字病理 | DICOM 处理、全切片图像分析、计算病理学、影像工作流 |
| 🤖 机器学习与AI | 深度学习、强化学习、时间序列分析、模型可解释性、贝叶斯方法 |
| 🔮 材料科学与化学 | 晶体结构分析、相图、代谢建模、计算化学 |
| 🌌 物理与天文 | 天文数据分析、坐标变换、宇宙学计算、符号数学 |
| ⚙️ 工程与仿真 | 离散事件仿真、多目标优化、代谢工程、系统建模 |
| 📊 数据分析与可视化 | 统计分析、网络分析、时间序列、出版级图表、大规模数据处理 |
| 🌍 地球科学与遥感 | 卫星图像处理、GIS 分析、空间统计、地形分析 |
| 🧪 实验室自动化 | 液相处理协议、实验设备控制、工作流自动化、LIMS 集成 |
| 📚 科研沟通 | 文献综述、科学写作、同行评审、文档处理、海报、幻灯片 |
| 🔬 多组学与系统生物学 | 多模态数据整合、通路分析、网络生物学 |
| 🧬 蛋白质工程与设计 | 蛋白语言模型、结构预测、序列设计、功能注释 |
| 🎓 研究方法论 | 假设生成、科研头脑风暴、批判性思维、基金写作 |

## 具体包含什么

- **100+ 科学数据库**：通过 database-lookup 技能统一访问 78 个公共数据库（PubChem、ChEMBL、UniProt、COSMIC、ClinicalTrials.gov、FRED、USPTO 等），另有专用技能访问 DepMap、Imaging Data Commons、PrimeKG、美国财政部数据等。BioServices（约40个生物信息服务）、BioPython（38个 NCBI 子库通过 Entrez）、gget（20+ 基因组数据库）等多数据库包进一步扩展覆盖。
- **70+ 优化 Python 包技能**：RDKit、Scanpy、PyTorch Lightning、scikit-learn、BioPython、pyzotero、BioServices、PennyLane、Qiskit、OpenMM、MDAnalysis、scVelo、TimesFM 等，都有配套文档、示例和最佳实践。
- **9 个科学集成技能**：Benchling、DNAnexus、LatchBio、OMERO、Protocols.io、Open Notebook 等平台的优化路径。
- **30+ 分析与通信工具**：文献综述、科学写作、同行评审、文档处理、海报、幻灯片、图表、Mermaid 图表等信息沟通工具。
- **10+ 研究与临床工具**：假设生成、基金写作、临床决策支持、治疗计划、监管合规、场景分析等。

## 快速开始

安装方式取决于目标 Agent，以 Claude Code 为例：

1. 将 skills 目录复制到 Claude Code 的 skills 目录
2. Agent 自动发现并使用相关技能
3. 开始科研任务时，直接调用技能名称

项目的 YouTube 频道有 Getting Started 视频，GitHub 也提供了详细文档。

## 配套项目：K-Dense BYOK

值得注意的延伸项目是 **[K-Dense BYOK](https://github.com/K-Dense-AI/k-dense-byok)**——一个免费开源的 AI 科学家桌面应用，基于 Scientific Agent Skills 构建。用户自带 API keys，从 40+ 模型中选择，本地运行，配有网络搜索、文件处理、100+ 科学数据库访问和全套 135 个技能。数据留在本机，可选通过 Modal 扩展到云端做重型计算。

## 适用场景

- 需要 AI 辅助进行文献综述、数据分析、论文撰写的科研人员
- 想要把 AI Agent 变成真正能做实验的数据科学团队
- 药物发现、基因组学、临床研究领域的专业人士
- 需要多数据库联合查询的跨学科研究项目

---

**延伸阅读**：[GitHub 仓库](https://github.com/K-Dense-AI/scientific-agent-skills) · [K-Dense BYOK](https://github.com/K-Dense-AI/k-dense-byok) · [YouTube 教程](https://youtu.be/ZxbnDaD_FVg)