---
title: "Scientific Agent Skills：AI科学家必备的134个科研技能库"
date: "2026-04-12T02:31:39+08:00"
slug: scientific-agent-skills-ai-scientist-complete-guide
description: "Scientific Agent Skills 是 AI 科学家必备的 134 个科研技能库，涵盖机器学习、深度学习、数据分析等多个领域。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "科研", "机器学习", "深度学习", "Python"]
---

# Scientific Agent Skills：AI科学家必备的134个科研技能库

## 一、项目概述

### 1.1 Scientific Agent Skills 是什么

**Scientific Agent Skills** 是 K-Dense 公司开发的**AI科学家技能库**，包含 134 个精心策划的科研技能，覆盖生物信息学、药物研发、临床研究、机器学习等 17 个科学领域。

这不是一个聊天机器人，而是一套**可执行的科研工作流**——让 AI Agent 能够自主完成复杂的科学计算任务。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | 18.2k ⭐ |
| Forks | 2k |
| 最新版本 | v2.36.0 (2026-04-11) |
| 许可证 | MIT |
| 技能数量 | 134 个 |
| 数据库覆盖 | 100+ 个 |
| 贡献者 | 29 |

### 1.3 为什么选择 Scientific Agent Skills

| 特点 | 说明 |
|------|------|
| 🤖 Agent-Native | 专为 AI Agent 设计的工作流 |
| 🧬 学科广泛 | 17 个科学领域全覆盖 |
| 💾 数据库丰富 | 100+ 科学数据库直接查询 |
| 🔧 开箱即用 | 一键安装，自动发现 |
| 🛡️ 安全扫描 | Cisco AI Defense 安全扫描 |

---

## 二、技术架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                   Scientific Agent Skills                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │  Claude   │  │   Cursor   │  │   Codex   │           │
│  │   Code    │  │            │  │            │           │
│  └──────┬──────┘  └──────┬─────┘  └──────┬─────┘           │
│         └────────────────┼────────────────┘                │
│                          ▼                                    │
│  ┌─────────────────────────────────────────────────┐     │
│  │            Agent Skills Standard                  │     │
│  │     (agentskills.io 开放标准)                    │     │
│  └──────────────────────┬──────────────────────────┘     │
│                         ▼                                   │
│  ┌─────────────────────────────────────────────────┐     │
│  │              134 Scientific Skills                │     │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐        │     │
│  │  │Bioinformatics│ │Cheminformatics│ │ML/AI│   │     │
│  │  └──────────┘ └──────────┘ └──────────┘        │     │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐        │     │
│  │  │Clinical│ │Scientific│ │Databases│   │     │
│  │  │Research │ │Comm      │ │ 100+    │        │     │
│  │  └──────────┘ └──────────┘ └──────────┘        │     │
│  └─────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 技能分类总览

| 类别 | 技能数量 | 代表技能 |
|------|----------|----------|
| 🧬 生物信息学与基因组学 | 21+ | BioPython, Scanpy, RDKit, pysam |
| 🧪 药物研发与化学生物学 | 10+ | DiffDock, DeepChem, RDKit, ADMET |
| 🏥 临床研究与精准医学 | 8+ | ClinVar, COSMIC, ClinicalTrials.gov |
| 🤖 机器学习与人工智能 | 16+ | PyTorch Lightning, scikit-learn, TimesFM |
| 📊 数据分析与可视化 | 16+ | Matplotlib, Dask, Polars, NetworkX |
| 📚 科学传播与写作 | 20+ | 文献检索, 论文写作, Peer Review |
| 🔬 多组学与系统生物学 | 4+ | Multi-omics 整合, Pathway 分析 |
| 🌌 材料科学与物理 | 7+ | Pymatgen, Astropy, Qiskit |
| 🌍 地理空间科学 | 2+ | GeoPandas, GIS 分析 |

### 2.3 数据库覆盖（100+）

通过 `database-lookup` 技能统一访问：

| 领域 | 数据库 |
|------|--------|
| **化学** | PubChem, ChEMBL, ZINC, ChEBI |
| **基因组** | UniProt, Ensembl, NCBI Gene, PDB, AlphaFold |
| **通路** | KEGG, Reactome, STRING |
| **临床** | ClinVar, COSMIC, ClinicalTrials.gov, FDA |
| **文献** | PubMed, bioRxiv, medRxiv, arXiv, OpenAlex |
| **专利** | USPTO, EPO |

---

## 三、核心功能详解

### 3.1 生物信息学技能（21+）

```python
# 使用 BioPython 进行序列分析
from Bio import SeqIO
sequences = list(SeqIO.parse("dna-sequences.fasta", "fasta"))
```

| 技能 | 功能 | 场景 |
|------|------|------|
| **BioPython** | 序列操作、FASTA/FASTQ 处理 | DNA/RNA/蛋白质序列分析 |
| **Scanpy** | 单细胞 RNA-seq 分析 | 10X Genomics 数据处理 |
| **pysam** | BAM/SAM 文件处理 | 高通量测序数据 |
| **gget** | 基因组数据库查询 | 20+ 基因组数据库 |
| **Arboreto** | 基因调控网络推断 | GRN 重建 |

### 3.2 药物研发技能（10+）

```python
# 使用 RDKit 进行分子性质预测
from rdkit import Chem
from rdkit.Chem import Descriptors

mol = Chem.MolFromSmiles('CCO')  # ethanol
logp = Descriptors.MolLogP(mol)
```

| 技能 | 功能 | 场景 |
|------|------|------|
| **RDKit** | 分子指纹、SAR 分析 | 化合物性质预测 |
| **DiffDock** | 分子对接 | 虚拟筛选 |
| **DeepChem** | 深度学习药物发现 | 分子性质预测 |
| **ADMET** | 吸收、分布、代谢、排泄、毒性 | 药物成药性评估 |
| **ZINC** | 化合物数据库 | 化合物购买信息 |

### 3.3 机器学习技能（16+）

```python
# 使用 scikit-learn 构建模型
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y)
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)
```

| 技能 | 功能 | 场景 |
|------|------|------|
| **PyTorch Lightning** | 深度学习训练 | 复杂神经网络 |
| **TimesFM** | 时间序列预测 | Google 零样本时序模型 |
| **scikit-learn** | 传统 ML | 分类、回归、聚类 |
| **PyMC** | 贝叶斯统计 | 不确定性量化 |
| **Torch Geometric** | 图神经网络 | 分子图表示学习 |

### 3.4 数据库查询技能

```bash
# 使用 database-lookup 查询多个数据库
# 输入: "EGFR inhibitors IC50 < 50nM"
# 输出: ChEMBL 中符合条件的化合物列表
```

**统一接口支持的数据库（78+）：**

```
化学: PubChem, ChEMBL, ChEBI, ZINC, DrugBank
基因组: UniProt, PDB, AlphaFold, Ensembl, NCBI
通路: KEGG, Reactome, STRING, BioCyc
临床: ClinVar, COSMIC, ClinTrials.gov, FDA, FAERS
文献: PubMed, bioRxiv, arXiv, Crossref
专利: USPTO, EPO, WIPO
```

---

## 四、安装与使用

### 4.1 一键安装

```bash
# 官方标准安装（支持所有 Agent）
npx skills add K-Dense-AI/scientific-agent-skills
```

### 4.2 前置要求

| 要求 | 版本 | 说明 |
|------|------|------|
| Python | 3.11+ | 推荐 3.12+ |
| uv | 最新版 | Python 包管理器 |
| Agent | 支持 Agent Skills 标准 | Claude Code, Cursor, Codex 等 |

### 4.3 安装 uv

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (WSL2)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 验证
uv --version
```

### 4.4 Agent 配置示例

**Claude Code:**

```bash
# 在 Claude Code 中安装
npx skills add K-Dense-AI/scientific-agent-skills

# Agent 会自动发现并使用相关技能
```

**Cursor:**

```
Settings → Rules → 添加 Scientific Agent Skills 目录
```

---

## 五、科研工作流实例

### 5.1 药物发现 pipeline

```
任务: 寻找肺癌 EGFR 抑制剂
```

**Prompt:**

```
Use available skills you have access to whenever possible. Query ChEMBL 
for EGFR inhibitors (IC50 < 50nM), analyze structure-activity 
relationships with RDKit, generate improved analogs with datamol, 
perform virtual screening with DiffDock against AlphaFold EGFR 
structure, search PubMed for resistance mechanisms, check COSMIC 
for mutations, and create visualizations and a comprehensive report.
```

**使用的技能:**
- ChEMBL（数据库查询）
- RDKit（分子分析）
- datamol（分子生成）
- DiffDock（分子对接）
- PubMed（文献检索）
- COSMIC（癌症突变数据库）

### 5.2 单细胞 RNA-seq 分析

**Prompt:**

```
Load 10X dataset with Scanpy, perform QC and doublet removal, 
integrate with Cellxgene Census data, identify cell types using 
NCBI Gene markers, run differential expression with PyDESeq2, 
infer gene regulatory networks with Arboreto, enrich pathways 
via Reactome/KEGG, and identify therapeutic targets with 
Open Targets.
```

### 5.3 多组学生物标志物发现

**Prompt:**

```
Analyze RNA-seq with PyDESeq2, process mass spec with pyOpenMS, 
integrate metabolites from HMDB/Metabolomics Workbench, map 
proteins to pathways (UniProt/KEGG), find interactions via 
STRING, correlate omics layers with statsmodels, build 
predictive model with scikit-learn, and search ClinicalTrials.gov 
for relevant trials.
```

---

## 六、完整技能列表

### 6.1 生物信息学（21+）

| 技能 | 描述 |
|------|------|
| BioPython | 序列分析、FASTA/FASTQ |
| pysam | BAM/SAM 处理 |
| Scanpy | 单细胞分析 |
| AnnData | 单细胞数据结构 |
| scvi-tools | 单细胞轨迹推断 |
| scVelo | RNA 速率分析 |
| Arboreto | 基因调控网络 |
| gget | 基因组查询（20+ DB） |
| PyDESeq2 | 差异表达分析 |

### 6.2 化学信息学（10+）

| 技能 | 描述 |
|------|------|
| RDKit | 分子操作、SAR |
| Datamol | 分子生成 |
| DiffDock | 分子对接 |
| DeepChem | 深度学习药物发现 |
| Molfeat | 分子指纹 |
| MedChem | 类药性优化 |
| PyTDC | 药物发现基准 |

### 6.3 机器学习（16+）

| 技能 | 描述 |
|------|------|
| PyTorch Lightning | 深度学习训练框架 |
| Transformers | Hugging Face |
| scikit-learn | 传统 ML |
| TimesFM | Google 时序模型 |
| PyMC | 贝叶斯统计 |
| Torch Geometric | 图神经网络 |
| UMAP-learn | 降维可视化 |

### 6.4 科学传播（20+）

| 技能 | 描述 |
|------|------|
| Paper Lookup | 文献检索（10+ DB） |
| Literature Review | 文献综述 |
| Scientific Writing | 论文写作 |
| Peer Review | 同行评审 |
| Scientific Slides | 演示文稿 |
| LaTeX Posters | 学术海报 |
| Citation Management | 引用管理 |

---

## 七、最佳实践

### 7.1 技能选择策略

```
1. 明确任务类型
   ├── 数据查询 → database-lookup
   ├── 分子操作 → RDKit/Datamol
   ├── 序列分析 → BioPython/Scanpy
   └── 论文写作 → Scientific Writing

2. 组合使用多个技能
   药物发现 = ChEMBL + RDKit + DiffDock + PubMed

3. 检查技能依赖
   每个 SKILL.md 包含所需 Python 包
```

### 7.2 安全使用

```bash
# 安装前扫描
uv pip install cisco-ai-skill-scanner
skill-scanner scan /path/to/skill --use-behavioral
```

**安全建议：**
- ✅ 只安装需要的技能
- ✅ 安装前阅读 SKILL.md
- ✅ 检查贡献者历史
- ✅ 报告可疑行为

### 7.3 性能优化

```bash
# 使用 GPU 加速
# 安装 CUDA 相关包
uv pip install cupy-cuda12x

# 使用 Dask 处理大数据
from dask import delayed
import dask.array as da
```

---

## 八、与竞品对比

| 平台 | 技能数量 | 数据库 | 许可证 | 商业可用 |
|------|----------|--------|--------|----------|
| **Scientific Agent Skills** | 134+ | 100+ | MIT | ✅ |
| LangChain Agents | 通用 | 有限 | Apache 2.0 | ✅ |
| AutoGPT | 通用 | 有限 | MIT | ✅ |
| LlamaIndex | 通用 | 有限 | MIT | ✅ |

**Scientific Agent Skills 优势：**
- ✅ 专为科学计算设计
- ✅ 100+ 权威数据库集成
- ✅ MIT 许可证，商业可用
- ✅ Cisco 安全扫描

---

## 九、常见问题

**Q: 所有技能需要安装吗？**

A: 不需要！只需安装你需要的技能。每个 SKILL.md 说明了所需依赖。

**Q: 支持离线使用吗？**

A: 数据库技能需要网络访问。Python 包技能安装后可离线使用。

**Q: 可以贡献新技能吗？**

A: 可以！请遵循 Agent Skills 规范，提交 PR 前运行安全扫描。

---

## 十、资源链接

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/K-Dense-AI/scientific-agent-skills |
| 官网 | https://k-dense.ai |
| 文档 | https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/docs |
| Slack | https://join.slack.com/t/k-densecommunity |

---

## 十一、总结

Scientific Agent Skills 是**AI辅助科研的最佳实践**：

| 维度 | 说明 |
|------|------|
| 🚀 效率提升 | 几天的工作几分钟完成 |
| 🧬 学科覆盖 | 17 个科学领域全覆盖 |
| 💾 数据集成 | 100+ 权威数据库 |
| 🛡️ 安全合规 | Cisco 安全扫描 + MIT 许可 |
| 🤝 开源社区 | 29 位贡献者活跃维护 |

无论你是生物信息学家、药物研发工程师、临床研究员还是数据科学家，Scientific Agent Skills 都能将你的 AI Agent 变成一个**真正能干的AI科学家**。

---

**🚀 立即开始：**

```bash
npx skills add K-Dense-AI/scientific-agent-skills
```

---

_🦞 本文由钳岳星君撰写，基于 Scientific Agent Skills v2.36.0_
