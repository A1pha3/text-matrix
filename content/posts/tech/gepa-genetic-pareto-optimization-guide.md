---
title: "GEPA：基于反射式文本进化的 AI 系统优化框架完全指南"
date: 2026-04-01T01:04:00+08:00
slug: "gepa-genetic-pareto-optimization-guide"
description: "深度解析 GEPA (3.1k Stars)：基于 LLM 反射和 Pareto 高效进化搜索的 AI 系统优化框架。比 RL 快 35 倍，只需 100-500 次评估即可超越 5000-25000 次的 RL 效果。开源模型+GEPA 以 1/90 成本击败 Claude Opus 4.1。"
draft: false
categories: ["技术笔记"]
tags: ["GEPA", "Pareto优化", "AI优化", "提示词工程", "DSPy", "反射式进化", "MLflow", "智能体架构", "文本优化", "机器学习"]
---

# GEPA：基于反射式文本进化的 AI 系统优化框架完全指南

## §1 学习目标

完成本文档后，你将能够：

- ✅ 理解 GEPA 的核心定位与设计理念
- ✅ 掌握 GEPA 的安装与基本使用方法
- ✅ 理解 GEPA 的反射式进化算法工作原理
- ✅ 使用 GEPA 优化提示词、系统配置和智能体架构
- ✅ 掌握 GEPA 与 DSPy、MLflow 等主流框架的集成方法
- ✅ 理解 Pareto 前沿与 Actionable Side Information 概念
- ✅ 使用 GEPA 适配器构建自定义优化系统

---

## §2 项目概述

### 2.1 什么是 GEPA？

**GEPA**（Genetic-Pareto，[GitHub 仓库](https://github.com/gepa-ai/gepa)）是一个用于优化任何文本参数系统的框架，支持提示词、代码、智能体架构、配置等任何文本内容的优化。

**官方描述**：

> GEPA (Genetic-Pareto) is a framework for optimizing any system with textual parameters against any evaluation metric. Unlike RL or gradient-based methods that collapse execution traces into a single scalar reward, GEPA uses LLMs to read full execution traces — error messages, profiling data, reasoning logs — to diagnose why a candidate failed and propose targeted fixes. Through iterative reflection, mutation, and Pareto-aware selection, GEPA evolves high-performing variants with minimal evaluations.

**核心哲学**：如果你能测量它，你就能优化它。

### 2.2 核心数据

| 指标 | 数值 |
|------|------|
| **Stars** | 3,087 (3.1k) |
| **Forks** | 262 |
| **Watchers** | 9 |
| **提交数** | 750 |
| **发布版本** | 42 个 |
| **部署数** | 121 |
| **许可证** | MIT |

### 2.3 技术栈

| 类别 | 技术 | 占比 |
|------|------|------|
| **核心开发** | Python | 27.3% |
| **文档/示例** | Jupyter Notebook | 72.6% |
| **前端** | HTML | 0.1% |

### 2.4 核心特性

| 特性 | 说明 |
|------|------|
| **反射式进化** | 使用 LLM 读取执行轨迹诊断失败原因 |
| **Pareto 优化** | 多目标优化，找到不同任务子集的最佳平衡 |
| **Actionable Side Information** | 可操作的诊断反馈，类比梯度 |
| **最小化评估** | 仅需 100-500 次评估 vs RL 的 5000-25000+ |
| **API 调用** | 无需模型权重访问，直接通过 API 优化 |
| **可解释性** | 人类可读的优化轨迹 |

### 2.5 核心优势

| 优势 | 说明 |
|------|------|
| **成本效率** | 开源模型 + GEPA 以 1/90 成本击败 Claude Opus 4.1 |
| **速度** | 比 RL 快 35 倍 |
| **数据效率** | 只需 3 个样本即可开始优化 |
| **通用性** | 提示词/代码/智能体架构/配置/SVG 均可优化 |
| **可解释** | 清晰展示每个提示词改变的原因 |

---

## §3 核心成果

### 3.1 性能对比

| 成果 | 指标 |
|------|------|
| **成本优化** | 比 Claude Opus 4.1 低 90 倍（开源模型 + GEPA） |
| **速度提升** | 比 RL 快 35 倍（100-500 次评估 vs 5000-25000+） |
| **智能体准确率** | ARC-AGI 从 32% 提升至 89% |
| **成本节省** | 云调度策略节省 40.2% |
| **编码智能体** | Jinja 解决率从 55% 提升至 82% |

### 3.2 实际应用

| 场景 | 成果 |
|------|------|
| **Databricks** | 开源模型 + GEPA 击败 Claude Opus 4.1 |
| **Jinja 编码** | 自动学习技能，解决率 55% → 82% |
| **云调度** | 发现比专家启发式更好的策略 |
| **数学推理** | MATH 准确率 67% → 93% |

### 3.3 生产使用

已在 **50+** 生产环境中使用，包括 Shopify、Databricks、Dropbox、OpenAI、Pydantic、MLflow、Comet ML 等。

---

## §4 工作原理

### 4.1 传统优化器的局限

传统优化器知道候选方案**失败**（that），但不知道**为什么**失败（why）。它们将执行轨迹压缩成单一标量奖励，无法提供具体的改进方向。

### 4.2 GEPA 的解决思路

GEPA 采用**反射式进化**方法，核心五步：

1. **Select（选择）**：从 Pareto 前沿中选择候选方案（在不同任务子集上表现出色的方案）

2. **Execute（执行）**：在小型批处理上执行，捕获完整执行轨迹

3. **Reflect（反射）**：LLM 读取轨迹（错误消息、性能分析器输出、推理日志）并诊断失败原因

4. **Mutate（变异）**：基于所有祖先累积的经验教训生成改进的候选方案

5. **Accept（接受）**：如果改进则添加到池中，更新 Pareto 前沿

### 4.3 Actionable Side Information (ASI)

**核心概念**：由评估器返回的诊断反馈，作为文本优化的梯度类比。

ASI 使得 GEPA 能够：
- 理解**为什么**候选方案失败
- 提供**具体**的改进建议
- 保留丰富的上下文信息

### 4.4 System-Aware Merge

GEPA 还支持**系统感知合并**，将两个在不同任务上表现出色的 Pareto 最优候选方案的优势结合起来。

---

## §5 安装与部署

### 5.1 pip 安装

```bash
pip install gepa
```

### 5.2 从源码安装

```bash
pip install git+https://github.com/gepa-ai/gepa.git
```

### 5.3 依赖

GEPA 需要：
- Python 3.10+
- 一个 LLM 提供者（OpenAI、Anthropic、Google 等）

---

## §6 快速开始

### 6.1 简单的提示词优化

```python
import gepa

# 初始化数据集
trainset, valset, _ = gepa.examples.aime.init_dataset()

# 定义初始提示词
seed_prompt = {
    "system_prompt": (
        "You are a helpful assistant. Answer the question. "
        "Put your final answer in the format '### <answer>'"
    )
}

# 运行优化
result = gepa.optimize(
    seed_candidate=seed_prompt,
    trainset=trainset,
    valset=valset,
    task_lm="openai/gpt-4.1-mini",
    max_metric_calls=150,
    reflection_lm="openai/gpt-5",
)

print("Optimized prompt:", result.best_candidate['system_prompt'])
```

**结果**：GPT-4.1 Mini 在 AIME 2025 上从 46.6% 提升至 56.6%（+10 个百分点）。

### 6.2 与 DSPy 集成（推荐用于 AI 流水线）

```python
import dspy

# 创建 GEPA 优化器
optimizer = dspy.GEPA(
    metric=your_metric,
    max_metric_calls=150,
    reflection_lm="openai/gpt-5",
)

# 编译优化后的程序
optimized_program = optimizer.compile(
    student=MyProgram(),
    trainset=trainset,
    valset=valset,
)
```

### 6.3 optimize_anything：超越提示词

`optimize_anything` API 可以优化**任何**文本产物，不仅仅是提示词：

```python
from gepa.optimize_anything import optimize_anything, GEPAConfig, EngineConfig

def evaluate(candidate: str) -> float:
    result = run_my_system(candidate)
    # 记录可操作的关键信息
    oa.log(f"Output: {result.output}")
    oa.log(f"Error: {result.error}")  # 反馈到反射中
    return result.score

result = optimize_anything(
    seed_candidate="<your initial artifact>",
    evaluator=evaluate,
    objective="Describe what you want to optimize for.",
    config=GEPAConfig(
        engine=EngineConfig(max_metric_calls=100)
    ),
)
```

---

## §7 内置适配器

### 7.1 适配器概览

| 适配器 | 说明 |
|--------|------|
| **DefaultAdapter** | 单轮 LLM 任务的系统提示词优化 |
| **DSPy Full Program** | 进化整个 DSPy 程序（签名、模块、控制流），MATH 上 67% → 93% |
| **Generic RAG** | 向量存储无关的 RAG 优化（ChromaDB、Weaviate、Qdrant、Pinecone） |
| **MCP Adapter** | 优化 MCP 工具描述和系统提示词 |
| **TerminalBench** | 优化 Terminus 终端使用智能体 |
| **AnyMaths** | 数学问题解决和推理任务 |

### 7.2 DefaultAdapter

用于单轮 LLM 任务的系统提示词优化：

```python
from gepa.adapters.default_adapter import DefaultAdapter

adapter = DefaultAdapter()
```

### 7.3 DSPy Full Program Adapter

进化整个 DSPy 程序，包括签名、模块和控制流：

```python
from gepa.adapters.dspy_full_program_adapter import DSPyFullProgramAdapter

adapter = DSPyFullProgramAdapter()
```

**效果**：MATH 准确率从 67% 提升至 93%。

### 7.4 Generic RAG Adapter

向量存储无关的 RAG 优化：

```python
from gepa.adapters.generic_rag_adapter import GenericRAGAdapter

adapter = GenericRAGAdapter()
```

支持：ChromaDB、Weaviate、Qdrant、Pinecone 等。

### 7.5 MCP Adapter

优化 Model Context Protocol (MCP) 工具描述：

```python
from gepa.adapters.mcp_adapter import MCPAdapter

adapter = MCPAdapter()
```

### 7.6 自定义适配器

通过实现 `evaluate` 和 `make_reflective_dataset` 方法构建自己的适配器：

```python
from gepa.core.adapter import GEPAAdapter

class MyAdapter(GEPAAdapter):
    def evaluate(self, candidate: dict) -> float:
        # 实现评估逻辑
        return score

    def make_reflective_dataset(self, candidate: dict) -> ReflectiveDataset:
        # 实现反射数据集创建
        return dataset
```

---

## §8 框架集成

### 8.1 DSPy 集成

```python
import dspy

optimizer = dspy.GEPA(
    metric=your_metric,
    max_metric_calls=150,
    reflection_lm="openai/gpt-5",
)

optimized_program = optimizer.compile(
    student=MyProgram(),
    trainset=trainset,
    valset=valset,
)
```

### 8.2 MLflow 集成

```python
import mlflow

# mlflow.genai.optimize_prompts() API
```

### 8.3 Comet ML Opik 集成

Opik Agent Optimizer 的核心优化算法。

### 8.4 Pydantic AI 集成

用于 Pydantic AI 的提示词优化。

### 8.5 OpenAI Cookbook 集成

构建自进化智能体。

### 8.6 HuggingFace Cookbook 集成

DSPy + GEPA 提示词优化指南。

### 8.7 Google ADK 集成

优化 Google Agent Development Kit 智能体。

---

## §9 适用场景

### 9.1 GEPA 擅长的场景

| 场景 | 描述 | GEPA 优势 |
|------|------|-----------|
| **昂贵执行** | 科学模拟、复杂智能体工具调用、慢编译 | 仅需 100-500 次评估 vs RL 的 10K+ |
| **数据稀缺** | 只需 3 个样本即可开始 | 无需大型训练集 |
| **API-only 模型** | 无权重访问权限 | 直接通过 API 优化 GPT-5、Claude、Gemini |
| **可解释性** | 需要理解为什么改变 | 人类可读的优化轨迹展示每个提示词改变的原因 |

### 9.2 GEPA 与 RL 的互补

使用 GEPA 进行快速初始优化，然后应用 RL/微调获得额外收益。

---

## §10 项目结构

### 10.1 目录结构

```
gepa/
├── src/gepa/           # 核心源代码
│   ├── core/           # 核心组件
│   │   └── adapter.py  # GEPAAdapter 接口
│   ├── adapters/       # 内置适配器
│   │   ├── default_adapter/
│   │   ├── dspy_full_program_adapter/
│   │   ├── generic_rag_adapter/
│   │   ├── mcp_adapter/
│   │   ├── terminal_bench_adapter/
│   │   └── anymaths_adapter/
│   └── examples/      # 示例
├── tests/              # 测试
├── docs/               # 文档
├── examples/           # 示例
├── assets/             # 资源
├── pyproject.toml       # Python 项目配置
└── README.md          # 项目文档
```

### 10.2 核心模块

| 模块 | 说明 |
|------|------|
| **core/adapter.py** | GEPAAdapter 接口定义 |
| **adapters/** | 内置适配器实现 |
| **examples/** | 使用示例 |

---

## §11 最佳实践

### 11.1 优化策略

| 阶段 | 策略 |
|------|------|
| **初始优化** | 使用 GEPA 快速找到好的候选方案 |
| **深度优化** | 使用 RL/微调获得额外收益 |
| **评估设计** | 设计有意义的评估指标 |

### 11.2 Actionable Side Information

确保评估器返回**可操作**的诊断反馈：
- 具体的错误信息
- 性能分析数据
- 推理日志

### 11.3 并行优化

```python
config = GEPAConfig(
    engine=EngineConfig(
        max_metric_calls=100,
        parallel_evaluations=4  # 并行评估
    )
)
```

---

## §12 常见问题

### Q1：GEPA 与 RL 有何区别？

| 方面 | GEPA | RL |
|------|------|-----|
| **评估次数** | 100-500 | 5000-25000+ |
| **速度** | 快 35 倍 | 较慢 |
| **数据需求** | 3 个样本 | 需要大量数据 |
| **可解释性** | 高 | 低 |

### Q2：GEPA 可以优化哪些内容？

任何文本内容：提示词、代码、智能体架构、配置、SVG 等。

### Q3：需要什么数据来开始？

只需 3 个样本即可开始优化。

### Q4：GEPA 支持哪些 LLM？

通过 API 支持任何 LLM：OpenAI、Anthropic、Google、Meta 等。

### Q5：如何构建自定义适配器？

实现 `GEPAAdapter` 接口的 `evaluate` 和 `make_reflective_dataset` 方法。

---

## §13 总结

### 13.1 核心优势

| 优势 | 说明 |
|------|------|
| **成本效率** | 1/90 成本击败 Claude Opus 4.1 |
| **速度** | 比 RL 快 35 倍 |
| **数据效率** | 只需 3 个样本 |
| **通用性** | 优化任何文本内容 |
| **可解释性** | 清晰的优化轨迹 |

### 13.2 适用对象

| 对象 | 使用场景 |
|------|----------|
| **AI 研究员** | 提示词和智能体架构优化 |
| **开发团队** | 生产级 AI 系统优化 |
| **数据科学家** | 快速原型和迭代 |
| **企业** | 定制化 AI 解决方案 |

### 13.3 项目信息

| 项目 | 信息 |
|------|------|
| **Stars** | 3.1k |
| **Forks** | 262 |
| **许可证** | MIT |
| **最新版本** | v0.1.1 |

### 13.4 相关链接

| 资源 | 链接 |
|------|------|
| **GitHub** | https://github.com/gepa-ai/gepa |
| **文档** | https://gepa-ai.github.io/gepa/ |
| **论文** | https://arxiv.org/abs/2507.19457 |
| **PyPI** | https://pypi.org/project/gepa/ |
| **Discord** | https://discord.gg/WXFSeVGdbW |

---

## §14 附录：术语表

| 术语 | 说明 |
|------|------|
| **GEPA** | Genetic-Pareto，进化式 Pareto 优化 |
| **ASI** | Actionable Side Information，可操作的诊断反馈 |
| **Pareto Front** | Pareto 前沿，不同目标间最优解的集合 |
| **Reflection** | 反射，LLM 读取执行轨迹诊断失败 |
| **Mutation** | 变异，基于历史经验生成改进候选 |
| **DSPy** | Stanford 的声明式 AI 编程框架 |

---

*文档版本 1.0 | 撰写日期：2026-04-01 | 基于 GEPA (3.1k Stars) | 性能数据来源：官方基准测试*