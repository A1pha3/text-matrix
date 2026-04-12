---
title: "AI Scientist-v2：智能体树搜索驱动的自动化科研论文生成"
date: 2026-03-29T15:47:00+08:00
slug: "ai-scientist-v2-agentic-tree-search"
aliases:
  - /posts/tech/ai-scientist-v2-agentic-tree-search/
description: "AI Scientist-v2 是首个生成论文被 ICLR Workshop 接收的 AI 科研系统，使用智能体树搜索实现完全自主的科学研究流程：假设生成、实验设计、论文撰写。"
draft: false
categories: ["技术笔记"]
tags: ["AI科研", "智能体", "树搜索", "自动化", "LLM"]
---

# AI Scientist-v2：智能体树搜索驱动的自动化科研论文生成

> 预计阅读时间：30分钟 | 难度：⭐⭐⭐

---

## 一、项目概览

**AI Scientist-v2** 是由 SakanaAI 开发的一个通用端到端智能体系统，能够自主完成科学研究流程：提出假设、设计实验、运行实验、分析数据，并撰写科学论文。该项目在 GitHub 上获得了 **3.6k Stars** 和 **545 Forks**，成为 AI 自动化科研领域的标杆项目。

### 1.1 核心定位

AI Scientist-v2 的诞生代表了 AI 自动化科研的重大突破：

1. **完全自主的研究流程**：从假设生成到实验设计，从结果分析到论文撰写，全流程无需人类干预
2. **超越模板限制**：不同于 v1 版本依赖人类编写的模板，v2 版本实现了完全自主的开放式科学探索
3. **首个 AI 生成的 Workshop 论文被接收**：ICLR Workshop 接收了完全由 AI Scientist-v2 生成的论文，开创了 AI 科研的新纪元

### 1.2 技术统计

| 指标 | 数值 |
|------|------|
| Stars | 3.6k |
| Forks | 545 |
| Commits | 58 |
| 贡献者 | 8 人 |
| 最新提交 | 2025-12-19 |
| 许可证 | AI Scientist Source Code License |
| 主要语言 | Python 70.4% |

### 1.3 v1 与 v2 对比

| 维度 | AI Scientist v1 | AI Scientist v2 |
|------|-----------------|-----------------|
| 模板依赖 | 依赖人类编写模板 | 无需模板 |
| 成功率 | 较高 | 较低 |
| 适用场景 | 目标明确、基础扎实的任务 | 开放性科学探索 |
| 灵活性 | 受限于模板 | 广泛探索 |

**重要说明**：v2 并不一定比 v1 产生更好的论文，特别是当有强起始模板可用时。v1 遵循明确的模板，成功率高；v2 采用更广泛、更具探索性的方法，成功率较低。

## 二、核心功能

### 2.1 假设生成（Ideation）

AI Scientist-v2 能够自主生成研究假设：

- 基于用户提供的研究主题描述（Markdown 格式）
- 通过 LLM 大脑风暴并精炼研究想法
- 访问 Semantic Scholar 检查新颖性
- 输出结构化的 JSON 格式研究想法

```python
# 运行假设生成脚本
python ai_scientist/perform_ideation_temp_free.py \
  --workshop-file "ai_scientist/ideas/my_research_topic.md" \
  --model gpt-4o-2024-05-13 \
  --max-num-generations 20 \
  --num-reflections 5
```

### 2.2 智能体树搜索（Agentic Tree Search）

这是 v2 版本的核心创新：

- **最佳优先树搜索（BFTS，Best-First Tree Search）**：系统地探索多个实验路径
- **实验管理器智能体**：指导整个探索过程
- **并行探索**：可同时扩展多个节点
- **自适应调试**：自动尝试修复失败的实验节点

**关键参数配置**（`bfts_config.yaml`）：

| 参数 | 说明 |
|------|------|
| `num_workers` | 并行探索路径数 |
| `steps` | 最大探索节点数 |
| `max_debug_depth` | 最大调试次数 |
| `debug_prob` | 调试概率 |
| `num_drafts` | 独立树的数量 |

### 2.3 论文撰写

基于实验结果自动生成 LaTeX 论文：

- 分析实验数据
- 生成可视化图表
- 撰写 Introduction、Method、Experiment、Conclusion 等章节
- 生成参考文献
- 完整 PDF 输出

### 2.4 文献检索

集成 Semantic Scholar API：

- 搜索相关学术文献
- 检查假设的新颖性
- 自动生成参考文献引用

## 三、技术架构

### 3.1 系统流程

```
研究主题描述 (Markdown)
       ↓
[阶段1：假设生成]
       ↓
结构化研究想法 (JSON)
       ↓
[阶段2：智能体树搜索实验]
       ↓
实验结果 + 树可视化
       ↓
[阶段3：论文撰写]
       ↓
完整论文 PDF
```

### 3.2 支持的模型

AI Scientist-v2 支持多种 LLM 后端：

| 模型 | 调用方式 | 用途 |
|------|----------|------|
| OpenAI GPT-4o | `OPENAI_API_KEY` | 写作/审核 |
| Gemini | `GEMINI_API_KEY` | 写作/审核 |
| Claude (via AWS Bedrock) | `AWS_*` 环境变量 | 实验/写作/审核 |

### 3.3 成本估算

| 阶段 | 成本 | 说明 |
|------|------|------|
| 假设生成 | ~$2-3 | 取决于使用的 LLM |
| 实验运行 | ~$15-20 | 使用 Claude 3.5 Sonnet |
| 论文撰写 | ~$5 | 写作 + 引用 |

**一次完整运行的典型成本约为 $20-25**。

### 3.4 项目结构

```
AI-Scientist-v2/
├── ai_scientist/              # 核心代码目录
│   ├── perform_ideation_temp_free.py   # 假设生成脚本
│   └── ideas/                 # 研究想法目录
├── bfts_config.yaml           # BFTS 树搜索配置
├── launch_scientist_bfts.py   # 主启动脚本
├── docs/                     # 文档
└── requirements.txt           # Python 依赖
```

## 四、快速开始

### 4.1 环境要求

- **操作系统**：Linux（需 NVIDIA GPU）
- **Python**：3.11
- **CUDA** + **PyTorch**：GPU 计算支持
- **LaTeX**：PDF 文档生成

### 4.2 安装步骤

```bash
# 1. 创建 conda 环境
conda create -n ai_scientist python=3.11
conda activate ai_scientist

# 2. 安装 PyTorch（根据你的 CUDA 版本调整）
conda install pytorch torchvision torchaudio pytorch-cuda=12.4 -c pytorch -c nvidia

# 3. 安装 PDF 和 LaTeX 工具
conda install anaconda::poppler
conda install conda-forge::chktex

# 4. 安装 Python 依赖
pip install -r requirements.txt
```

### 4.3 配置 API Key

```bash
# OpenAI
export OPENAI_API_KEY="YOUR_OPENAI_KEY_HERE"

# Semantic Scholar（可选）
export S2_API_KEY="YOUR_S2_KEY_HERE"

# AWS（使用 Claude via Bedrock）
export AWS_ACCESS_KEY_ID="YOUR_AWS_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="YOUR_AWS_SECRET_KEY"
export AWS_REGION_NAME="your-aws-region"
```

### 4.4 运行完整流程

**第一步：生成研究想法**

```bash
python ai_scientist/perform_ideation_temp_free.py \
  --workshop-file "ai_scientist/ideas/my_research_topic.md" \
  --model gpt-4o-2024-05-13 \
  --max-num-generations 20 \
  --num-reflections 5
```

**第二步：运行实验并生成论文**

```bash
python launch_scientist_bfts.py \
  --load_ideas "ai_scientist/ideas/my_research_topic.json" \
  --load_code \
  --add_dataset_ref \
  --model_writeup o1-preview-2024-09-12 \
  --model_citation gpt-4o-2024-11-20 \
  --model_review gpt-4o-2024-11-20 \
  --model_agg_plots o3-mini-2025-01-31 \
  --num_cite_rounds 20
```

## 五、使用指南

### 5.1 准备研究主题

创建一个 Markdown 文件描述研究领域：

```markdown
# Title: 探索新的深度学习优化器

# Keywords:
深度学习, 优化器, 神经网络, 自适应学习率

# TL;DR:
提出一种新的自适应优化算法...

# Abstract:
我们提出一种...
```

### 5.2 理解树搜索结果

实验完成后，在 `experiments/"timestamp"/logs/0-run/` 目录下可以找到：

- **unified_tree_viz.html**：树搜索过程的可视化
- **实验日志**：每个节点的详细执行信息

### 5.3 故障排除

**问题：没有生成 PDF 或审核结果**

- 成功取决于选择的模型和想法的复杂性
- 建议使用 Claude 3.5 Sonnet 以获得更高成功率

**问题：CUDA 内存不足**

- 在研究主题文件中指定使用更小的模型
- 减少 `num_workers` 以降低并行度

## 六、安全与责任

### 6.1 警告

> ⚠️ **Caution!** 此代码将执行 LLM 生成的代码。存在多种与自主性相关的风险和挑战，包括潜在的危险包使用、不可控的网络访问，以及可能产生意外进程的可能性。**确保在受控的沙箱环境中运行**（例如 Docker 容器）。

### 6.2 强制性披露

根据许可证，使用此代码生成的科学论文必须：

- 在论文的显眼位置明确披露 AI 的使用
- 在摘要或方法部分添加适当的归属声明

**推荐引用格式：**

> "This manuscript was autonomously generated using The AI Scientist."

## 七、最佳实践

### 7.1 研究主题设计

- 提供清晰的研究领域描述
- 包含足够的背景信息帮助 LLM 理解研究 context
- 明确研究的目标和预期贡献

### 7.2 模型选择

| 场景 | 推荐模型 | 理由 |
|------|----------|------|
| 实验阶段 | Claude 3.5 Sonnet | 高成功率 |
| 写作阶段 | GPT-4o 或 o1 | 成本效益 |
| 引用生成 | GPT-4o | 成本控制 |

### 7.3 成本优化

- 使用较便宜的模型进行引用生成（`model_citation`）
- 仔细选择 `num_workers` 和 `steps` 参数
- 在 ideation 阶段使用较小模型

## 八、常见问题

**Q: AI Scientist-v2 和 v1 哪个更好？**

A: 取决于你的需求。v1 适合有明确目标和良好基础的场景，成功率更高。v2 适合开放性科学探索，但成功率较低。

**Q: 运行一次完整实验需要多少时间？**

A: 完整流程通常需要数小时，具体取决于并行度和实验复杂度。

**Q: 是否需要 GPU？**

A: 是的，需要 NVIDIA GPU 和 CUDA 支持来运行深度学习实验。

**Q: 如何处理 Semantic Scholar API 限制？**

A: 可以跳过引用阶段，或者使用 `S2_API_KEY` 提高 API 限额。

## 九、总结

AI Scientist-v2 代表了 AI 自动化科研的前沿：

- ✅ **完全自主**：从假设到论文，全流程无需人类干预
- ✅ **智能体树搜索**：系统化探索实验空间
- ✅ **多模型支持**：OpenAI、Gemini、Claude 均可使用
- ✅ **首个被接收的 AI 论文**：证明了可行性

**局限性**：

- 成功率不如 v1 高
- 需要强大的 LLM 支持
- GPU 资源需求较高

无论你是 AI 研究者还是对自动化科研感兴趣，AI Scientist-v2 都是一个值得深入了解的项目。

---

**相关资源：**

- 📄 [论文](https://pub.sakana.ai/ai-scientist-v2/paper)
- 📝 [博客文章](https://sakana.ai/ai-scientist-first-publication/)
- 🧪 [ICLR2025 Workshop 实验](https://github.com/SakanaAI/AI-Scientist-ICLR2025-Workshop-Experiment)
- 🐙 [GitHub](https://github.com/SakanaAI/AI-Scientist-v2)
