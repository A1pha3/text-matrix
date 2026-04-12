---
title: "NeMo Skills：NVIDIA 开源 LLM 技能提升流水线"
date: 2026-04-12T11:00:00+08:00
slug: nemo-skills-llm-skill-pipeline-guide
aliases:
  - /posts/tech/nemo-skills-llm-skill-pipeline-guide/
categories: ["技术笔记"]
tags: ["NeMo Skills", "NVIDIA", "LLM训练", "合成数据", "模型评估", "OpenReasoning"]
description: "NeMo Skills 是 NVIDIA 开源的 LLM 技能提升工具集，覆盖合成数据生成、模型训练与基准评估全流程。本文基于仓库 README，梳理核心功能、已发布模型与数据集、评估基准体系与快速上手路径。"
---

> **目标读者**：LLM 训练工程师、模型优化研究者
> **核心问题**：如何用 NeMo Skills 构建从数据生成到评估的完整 LLM 技能提升流水线？
> **难度**：⭐⭐⭐⭐（高级）
> **事实边界**：本文基于 NVIDIA-NeMo/Skills 仓库 README 和官方文档。CLI 命令的具体参数格式请以 `ns --help` 和官方文档为准。

## 一、项目概述

### 1.1 什么是 NeMo Skills

NeMo Skills（[NVIDIA-NeMo/Skills](https://github.com/NVIDIA-NeMo/Skills)）是 NVIDIA 开源的 LLM 技能提升工具集，提供从合成数据生成（Synthetic Data Generation, SDG）、模型训练到基准评估的完整流水线。核心设计理念是：在本地工作站开发，一行配置切换到大规模 Slurm 集群。

> 免责声明：此项目仅用于研究目的，非 NVIDIA 官方产品。

### 1.2 核心能力

| 能力 | 说明 |
|------|------|
| **灵活推理** | 无缝切换 API 提供商、本地服务和 Slurm 集群；支持 TensorRT-LLM、vLLM、sglang、Megatron 托管模型 |
| **弹性扩展** | SDG 任务从 1 块 GPU 扩展到数万块 GPU |
| **多基准评估** | 覆盖数学、代码、科学、指令遵循、长上下文、工具调用、多语言、语音、视觉等 10+ 类别 |
| **并行评估** | 每个评估可跨多个 Slurm 作业并行，支持自托管 LLM 评判 |
| **模型训练** | 支持 NeMo-RL 和 verl 两个训练框架 |

### 1.3 项目数据

| 指标 | 数值 |
|------|------|
| Stars | 905+ |
| Forks | 169+ |
| 协议 | Apache-2.0 |
| 主语言 | Python |
| 文档 | [nvidia-nemo.github.io/Skills](https://nvidia-nemo.github.io/Skills/) |

---

## 二、评估基准体系

NeMo Skills 支持广泛的评估基准，覆盖 LLM 的核心能力维度：

| 类别 | 基准示例 | 说明 |
|------|----------|------|
| **数学（自然语言）** | aime24、aime25、hmmt_feb25 | 数学竞赛题，自然语言作答 |
| **数学（形式语言）** | minif2f、proofnet、putnam-bench | 形式化证明，严格验证 |
| **代码** | swe-bench、livecodebench、bird | 代码生成与调试 |
| **科学知识** | hle、scicode、gpqa | 高难度科学问答 |
| **指令遵循** | ifbench、ifeval | 指令遵循能力 |
| **长上下文** | ruler、mrcr、aalcr、longbench-v2 | 长文本理解与检索 |
| **工具调用** | bfcl_v3 | 函数调用能力 |
| **多语言** | mmlu-prox、flores-200、wmt24pp | 跨语言能力 |
| **语音与音频** | asr-leaderboard、mmau-pro | 语音理解 |
| **视觉语言模型** | mmmu-pro | 多模态理解 |

每个评估基准都支持自定义 Prompt 和配置，且可并行化到多个 Slurm 作业。

---

## 三、已发布模型与数据集

NeMo Skills 已基于该流水线发布多个有影响力的模型和数据集。

### 3.1 OpenReasoning（2025-07-18）

OpenReasoning 模型在数学、代码和科学基准上达到开源模型 SoTA。

相关数据集：
- 数学与代码数据：Nemotron-Post-Training-Dataset-v1
- 科学数据：OpenScienceReasoning-2

### 3.2 OpenMathReasoning（2025-04-23）

OpenMathReasoning 数据集规模：

| 数据类型 | 数量 |
|----------|------|
| 唯一数学问题 | 306K（来自 AoPS 论坛） |
| 长链式思维（CoT）解决方案 | 3.2M |
| 工具集成推理（TIR）解决方案 | 1.7M |
| GenSelect 样本 | 566K |

GenSelect 是一种从多个候选解中选择最优解的方法，用于提升模型在数学推理上的准确率。

OpenMath-Nemotron 系列模型在发布时为开源数学推理最强模型。

### 3.3 OpenMathInstruct-2（2024-10-03）

- 14M 问题-解决方案对
- 使用 Llama3.1-405B-Instruct 生成
- OpenMath-2-Llama 系列相比 Llama3.1-Instruct 有显著提升

### 3.4 Nemotron-Math-v2

用于训练 NVIDIA-Nemotron-3-Nano-30B-A3B-BF16 的数据集。2025-12-15 发布了复现配方（recipe）。

### 3.5 Nemotron-Post-Training-Dataset-v1

用于训练 OpenReasoning 模型的后训练数据集，包含数学和代码数据。

### 3.6 最新动态

| 日期 | 事件 |
|------|------|
| 2025-12-15 | 发布 Nemotron-Math-v2 和 Nemotron-Math-Proofs-v1 数据集复现配方 |
| 2025-11-25 | 发布生成式验证器（Generative Verifiers）实验复现方案 |
| 2025-08-22 | 发布 Nemotron-Nano-9B-v2 评估复现 |
| 2025-08-15 | 发布 Llama-3_3-Nemotron-Super-49B-v1_5 评估复现 |

---

## 四、训练框架

NeMo Skills 支持两个训练框架：

| 框架 | 来源 | 说明 |
|------|------|------|
| **NeMo-RL** | NVIDIA | NVIDIA 自研 RL 训练框架 |
| **verl** | Volcengine | 字节跳动开源 RL 训练框架 |

两个框架均支持分布式训练，可从单节点扩展到多节点 Slurm 集群。

---

## 五、快速开始

### 5.1 安装

```bash
git clone https://github.com/NVIDIA-NeMo/Skills.git
cd Skills
pip install -e .
```

### 5.2 查看可用命令

```bash
ns --help
```

README 建议通过 `ns --help` 查看所有可用命令和选项。更多示例见官方 [tutorials 页面](https://nvidia-nemo.github.io/Skills/)。

### 5.3 推理后端配置

NeMo Skills 支持多种推理后端，可根据硬件和需求选择：

| 后端 | 适用场景 |
|------|----------|
| TensorRT-LLM | 高吞吐推理（NVIDIA GPU） |
| vLLM | 通用高吞吐推理 |
| sglang | 低延迟推理 |
| Megatron | 大规模分布式推理 |

---

## 六、架构与扩展

### 6.1 目录结构

```
Skills/
├── nemo_skills/          # 核心代码
├── recipes/              # 训练与评估配方
├── cluster_configs/      # 集群配置模板
├── dockerfiles/          # Docker 构建文件
├── docs/                 # 文档
├── requirements/         # 依赖
└── tests/                # 测试
```

### 6.2 扩展点

| 扩展点 | 说明 |
|--------|------|
| 自定义基准 | 添加新的评估基准配置 |
| 自定义 Prompt | 修改基准的 Prompt 模板 |
| 自托管评判 | 部署本地 LLM 作为评判模型 |
| 自定义推理后端 | 接入新的推理引擎 |

---

## 七、适用场景与边界

### 7.1 适合的场景

| 场景 | 说明 |
|------|------|
| **数学推理增强** | 使用 SDG 生成数学训练数据，评估数学推理能力 |
| **代码能力提升** | 生成代码数据，在 swe-bench 等基准上评估 |
| **模型后训练** | 使用 NeMo-RL/verl 进行 RL 训练 |
| **大规模评估** | 在 Slurm 集群上并行运行多基准评估 |
| **数据集发布** | 基于流水线生成和发布高质量训练数据 |

### 7.2 边界与注意事项

| 边界 | 说明 |
|------|------|
| **研究用途** | 项目明确声明仅用于研究，非 NVIDIA 官方产品 |
| **硬件要求** | 本地推理可运行，但大规模 SDG 和训练需要多卡 GPU |
| **CLI 参数待验证** | 具体命令参数格式请以 `ns --help` 和官方文档为准 |
| **Slurm 依赖** | 大规模并行需要 Slurm 集群环境 |

---

## 相关链接

- GitHub：[NVIDIA-NeMo/Skills](https://github.com/NVIDIA-NeMo/Skills)
- 官方文档：[nvidia-nemo.github.io/Skills](https://nvidia-nemo.github.io/Skills/)
- Tutorials：[nvidia-nemo.github.io/Skills/tutorials](https://nvidia-nemo.github.io/Skills/tutorials)
- Papers & Releases：[nvidia-nemo.github.io/Skills/papers](https://nvidia-nemo.github.io/Skills/papers)
