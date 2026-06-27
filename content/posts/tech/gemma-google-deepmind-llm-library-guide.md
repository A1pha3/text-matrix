---
title: "Gemma：Google DeepMind开源LLM库完全指南"
date: "2026-04-12T02:31:39+08:00"
slug: gemma-google-deepmind-llm-library-guide
description: "Gemma 是 Google DeepMind 开源的大语言模型库，提供 Gemma 2/3/3n/4 等多种规模的模型，支持 JAX 和 PyTorch。"
draft: false
categories: ["技术笔记"]
tags: ["Gemma", "Google", "DeepMind", "LLM", "JAX"]
---

# Gemma：Google DeepMind 开源 LLM 库完全指南

> **目标读者**：LLM 应用开发者、AI 研究人员、对本地部署大模型感兴趣的实践者
> **预计阅读时间**：30-40 分钟
> **前置知识**：Python 基础、深度学习框架概念（JAX/PyTorch）
> **难度定位**：⭐⭐⭐ 中级实用

---

## §0 学习目标

完成本篇文章后，你将能够：

1. **理解 Gemma 系列模型的定位与演进**：Gemma 1/2/3/3n/4 的区别与适用场景
2. **掌握 Gemma 的基础使用**：安装、加载模型、多轮对话
3. **使用多模态能力**：图像 + 文本混合输入
4. **执行高效微调**：LoRA 配置与训练流程
5. **选择适合的部署方案**：本地推理、量化、批处理优化
6. **判断何时用 Gemma vs Gemini**：开源权重与闭源 API 的决策边界

---

## §0.5 目录

- [§1 项目概述](#一项目概述)：Gemma 是什么、核心数据、支持版本
- [§2 系统要求](#二系统要求)：硬件支持、软件依赖
- [§3 快速开始](#三快速开始)：安装、基础使用、多轮对话
- [§4 模型架构](#四模型架构)：Gemma 系列演进、核心模块、可用模型路径
- [§5 多模态能力](#五多模态能力)：图像支持、采样器配置
- [§6 微调指南](#六微调指南)：LoRA 微调、全量微调
- [§7 示例与 Colabs](#七示例与-colabs)：官方 Colabs、文本生成、聊天示例
- [§8 模型下载](#八模型下载)：检查点路径、下载权重
- [§9 实践建议](#九实践建议)：推理优化、训练优化、常见问题
- [§10 技术报告](#十技术报告)：各版本技术报告链接
- [§11 项目结构](#十一项目结构)：代码库结构概览
- [§12 与 Gemini 的关系](#十二与-gemini-的关系)：Gemma vs Gemini 对比
- [§13 自测题](#自测题)：巩固知识点的 5 道题
- [§14 进阶路径](#进阶路径)：从入门到生产的四个阶段

---

## 一、项目概述

### 1.1 Gemma 是什么

**Gemma** 是 Google DeepMind 开发的**开源权重大语言模型（LLM）**系列，基于 Gemini 研究和技术。这个仓库提供了 `gemma` PyPI 包——一个用于使用和微调 Gemma 模型的 JAX 库。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | 5,477+ ⭐ |
| Forks | 973+ |
| 贡献者 | 30 |
| 许可证 | Apache-2.0 |
| 最新版本 | v3.3.0 (2025-11-18) |
| 最新提交 | 2026-04-10（gemma 4）|
| 语言 | Python 58.9%, Jupyter Notebook 41.1% |

### 1.3 支持的模型版本

| 版本 | 说明 |
|------|------|
| **Gemma 2** | 第二代开源模型 |
| **Gemma 3** | 第三代开源模型 |
| **Gemma 3n** | Gemma 3 多模态版本 |
| **Gemma 4** | 最新一代（2026-04-10 更新）|

---

## 二、系统要求

### 2.1 硬件支持

Gemma 可以在 **CPU、GPU 和 TPU** 上运行：

| 模型大小 | GPU 显存要求 | 推荐配置 |
|----------|-------------|----------|
| **2B** | 8GB+ | RTX 3080 / RTX 4090 等 |
| **7B** | 24GB+ | A100 / H100 等 |
| 更大模型 | 更高 | 多卡并行 |

### 2.2 软件依赖

| 依赖 | 说明 |
|------|------|
| **JAX** | 核心深度学习框架（CPU/GPU/TPU）|
| **Python** | 推荐 3.10+ |

---

## 三、快速开始

### 3.1 安装

```bash
# 安装 JAX（CPU/GPU/TPU）
# 详见：https://jax.readthedocs.io/en/latest/installation.html

# 安装 Gemma
pip install gemma
```

### 3.2 基础使用

```python
from gemma import gm

# 加载 Gemma 4 模型
model = gm.nn.Gemma4_E4B()
params = gm.ckpts.load_params(gm.ckpts.CheckpointPath.GEMMA4_E4B_IT)
```

### 3.3 多轮对话

```python
from gemma import gm

# 创建对话采样器
sampler = gm.text.ChatSampler(
    model=model,
    params=params,
    multi_turn=True,  # 启用多轮对话
)

# 第一轮对话
prompt = """Which of the 2 images do you prefer ?
Image 1: <|image|>
Image 2: <|image|>
Write your answer as a poem."""

out0 = sampler.chat(prompt, images=[image1, image2])

# 第二轮对话（自动继承上下文）
out1 = sampler.chat("What about the other image?")
```

> 💡 `ChatSampler` API 统一支持所有 Gemma 版本（2, 3, 3n, 4）

---

## 四、模型架构

### 4.1 Gemma 系列演进

| 版本 | 发布时间 | 参数量 | 特色 |
|------|----------|--------|------|
| Gemma 1 | 2024 Q1 | 2B / 7B | 基础开源模型 |
| Gemma 2 | 2024 Q3 | 2B / 7B / 9B / 27B | 改进架构 |
| Gemma 3 | 2025 Q1 | 多尺寸 | 多模态支持 |
| Gemma 3n | 2025 Q2 | - | 优化的多模态 |
| Gemma 4 | 2026 Q2 | - | 最新一代 |

### 4.2 核心模块

```
gemma/
├── nn/                 # 神经网络模块
│   ├── Gemma2_*       # Gemma 2 模型
│   ├── Gemma3_*        # Gemma 3 模型
│   └── Gemma4_*        # Gemma 4 模型
├── text/               # 文本处理
│   └── ChatSampler     # 多轮对话采样器
├── ckpts/              # 检查点加载
│   └── CheckpointPath  # 模型路径枚举
└── image/              # 图像处理（多模态）
```

### 4.3 可用模型路径

```python
import gemma as gm

# 列出所有可用的检查点路径
print(gm.ckpts.CheckpointPath._member_names_)
# ['GEMMA2_2B_IT', 'GEMMA2_2B_PT', 'GEMMA2_7B_IT', 'GEMMA2_7B_PT', ...]
```

---

## 五、多模态能力

### 5.1 图像支持

Gemma 支持**图像 + 文本**的多模态对话：

```python
from gemma import gm
from PIL import Image

# 加载图像
image1 = Image.open("image1.jpg")
image2 = Image.open("image2.jpg")

# 多模态对话
prompt = """Which of the 2 images do you prefer?
Image 1: <|image|>
Image 2: <|image|>
Write your answer as a poem."""

result = sampler.chat(prompt, images=[image1, image2])
print(result)
```

### 5.2 采样器配置

```python
sampler = gm.text.ChatSampler(
    model=model,
    params=params,
    multi_turn=True,           # 启用多轮对话
    temperature=0.8,           # 生成温度
    top_p=0.95,               # Nucleus sampling
    max_tokens=2048,           # 最大生成长度
)
```

---

## 六、微调指南

### 6.1 LoRA 微调

Gemma 支持 **Low-Rank Adaptation (LoRA)** 高效微调：

```python
from gemma import gm

# 加载基础模型
model = gm.nn.Gemma4_E4B()
params = gm.ckpts.load_params(gm.ckpts.CheckpointPath.GEMMA4_E4B_IT)

# 配置 LoRA
lora_config = gm.lora.LoRAConfig(
    rank=8,
    alpha=16,
    target_modules=["attn", "ffw"],
)

# 应用 LoRA
model.apply_lora(lora_config)

# 微调训练
trainer = gm.training.Trainer(model, optimizer)
trainer.train(train_dataset)
```

### 6.2 全量微调

```python
# 全量微调（需要更多显存）
model = gm.nn.Gemma4_E4B()
params = gm.ckpts.load_params(...)

# 使用更大的 batch size
trainer = gm.training.Trainer(
    model,
    optimizer,
    batch_size=16,           # 更大 batch
    gradient_accumulation=4,
)
```

---

## 七、示例与 Colabs

### 7.1 官方 Colabs

| Colab | 说明 |
|-------|------|
| **Sampling** | 基础文本生成 |
| **Multi-modal** | 多模态图像+文本对话 |
| **Fine-tuning** | 全量微调教程 |
| **LoRA** | 高效 LoRA 微调 |

### 7.2 文本生成示例

```python
from gemma import gm

# 加载模型
model = gm.nn.Gemma4_E4B()
params = gm.ckpts.load_params(...)

# 创建采样器
sampler = gm.text.Sampler(model=model, params=params)

# 生成文本
prompt = "Explain the concept of attention mechanisms in transformers."
output = sampler(prompt, max_len=512)
print(output)
```

### 7.3 聊天示例

```python
from gemma import gm

# 多轮聊天
sampler = gm.text.ChatSampler(
    model=model,
    params=params,
    multi_turn=True,
)

# 第一轮
response1 = sampler.chat("What is machine learning?")
print(response1)

# 第二轮（自动带上下文）
response2 = sampler.chat("Tell me more about neural networks.")
print(response2)
```

---

## 八、模型下载

### 8.1 检查点路径

```python
from gemma import gm

# 查看所有可用路径
for path in gm.ckpts.CheckpointPath:
    print(path.name, path.value)
```

### 8.2 下载模型权重

详细说明请参阅[官方文档](https://gemma-llm.readthedocs.io/en/latest/checkpoints.html)。

---

## 九、实践建议

### 9.1 推理优化

| 优化项 | 建议 |
|--------|------|
| **量化** | INT8/INT4 量化减少显存 |
| **KV Cache** | 启用加速生成 |
| **批处理** | 多请求批处理提高吞吐 |
| **Flash Attention** | 启用加速注意力计算 |

### 9.2 训练优化

| 优化项 | 建议 |
|--------|------|
| **混合精度** | BF16 加速训练 |
| **梯度累积** | 大 batch 模拟 |
| **LoRA** | 推荐用于微调 |
| **学习率调度** | Cosine decay |

### 9.3 常见问题

| 问题 | 解决方案 |
|------|----------|
| OOM | 减小 batch_size 或使用量化 |
| 慢推理 | 启用 KV Cache + Flash Attention |
| 多模态不工作 | 检查模型版本（Gemma 3+）|

---

## 十、技术报告

| 版本 | 报告链接 |
|------|----------|
| **Gemma 1** | [技术报告](https://goo.gle/GemmaReport) |
| **Gemma 2** | [技术报告](https://goo.gle/gemma2report) |
| **Gemma 3** | [技术报告](https://storage.googleapis.com/deepmind-media/gemma/Gemma3Report.pdf) |
| **Gemma 4** | 即将发布 |

---

## 十一、项目结构

```
gemma/
├── gemma/                  # 核心包
│   ├── __init__.py
│   ├── nn/                # 神经网络模块
│   │   ├── __init__.py
│   │   ├── gemma2.py     # Gemma 2
│   │   ├── gemma3.py     # Gemma 3
│   │   └── gemma4.py     # Gemma 4
│   ├── text/              # 文本处理
│   │   ├── __init__.py
│   │   ├── sampler.py    # 采样器
│   │   └── chat_sampler.py  # 聊天采样器
│   ├── ckpts/            # 检查点加载
│   │   └── loader.py
│   └── training/         # 训练工具
│       └── trainer.py
├── examples/             # 示例脚本
├── colabs/               # Jupyter Colabs
├── docs/                 # 文档
├── .github/workflows/     # CI/CD
├── pyproject.toml
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
└── LICENSE
```

---

## 十二、与 Gemini 的关系

Gemma 基于 Gemini 的研究和技术，但有如下区别：

| 维度 | Gemma | Gemini |
|------|-------|--------|
| **权重** | 开源可下载 | 闭源 API |
| **规模** | 2B - 27B | 更大规模 |
| **定制** | 完全可微调 | API 访问 |
| **许可证** | Apache 2.0 | 专有 |

---

## 自测题

完成阅读后，请自检以下知识点：

**Q1**：Gemma 3n 相比 Gemma 3 的主要区别是什么？
<details>
<summary>参考答案</summary>
Gemma 3n 是 Gemma 3 的多模态优化版本，主要增强了图像 + 文本的混合输入能力。`ChatSampler` 的 `images` 参数只在 Gemma 3+ 版本可用。
</details>

**Q2**：`ChatSampler` 的 `multi_turn=True` 参数起什么作用？
<details>
<summary>参考答案</summary>
启用多轮对话模式后，每次调用 `chat()` 会自动携带之前的对话历史作为上下文，实现连贯的对话体验。不需要手动管理历史消息。
</details>

**Q3**：LoRA 微调相比全量微调的主要优势是什么？
<details>
<summary>参考答案</summary>
LoRA（Low-Rank Adaptation）只训练少量新增参数（rank 和 alpha 控制参数量），显存占用大幅降低，训练速度更快，且可以在同一个基础模型上叠加多个 LoRA 权重，方便切换不同任务。
</details>

**Q4**：Gemma 和 Gemini 的核心区别是什么？什么场景选哪个？
<details>
<summary>参考答案</summary>
Gemma 是开源权重（可下载、可微调、Apache 2.0），Gemini 是闭源 API。需要本地部署、定制模型、离线运行的场景选 Gemma；需要最强模型能力、不想管理基础设施的场景选 Gemini API。
</details>

**Q5**：Gemma 的 `CheckpointPath` 枚举的作用是什么？
<details>
<summary>参考答案</summary>
`gm.ckpts.CheckpointPath` 枚举了所有可用的预训练模型检查点路径（如 `GEMMA2_2B_IT`、`GEMMA4_E4B_IT`），通过 `gm.ckpts.load_params()` 加载对应权重，避免手动拼接路径。
</details>

---

## 进阶路径

### 阶段一：跑起来（1-2 天）
- 安装 JAX 和 Gemma
- 运行官方 Colabs（Sampling、Multi-modal）
- 完成一次基础文本生成

### 阶段二：接到自己的项目（3-7 天）
- 将 Gemma 集成到现有 Python 项目
- 实现多轮对话接口
- 配置合适的采样参数（temperature、top_p、max_tokens）

### 阶段三：微调与优化（1-2 周）
- 准备自己的数据集
- 配置并运行 LoRA 微调
- 量化部署（INT8/INT4）
- 启用 KV Cache 和 Flash Attention 加速推理

### 阶段四：生产级部署（2-4 周）
- 批量推理优化
- 多 GPU/TPU 分布式推理
- 监控与日志
- A/B 测试不同模型版本

**推荐资源**：
- [Gemma 官方文档](https://gemma-llm.readthedocs.io)
- [JAX 官方文档](https://jax.readthedocs.io)
- [Hugging Face Gemma 模型页](https://huggingface.co/google/gemma)

---

## 十三、总结

Gemma 是 Google DeepMind 开源的 LLM 库，基于 Gemini 的研究积累，提供从 2B 到 27B 规模的模型权重。核心优势是 Apache 2.0 许可证下的可微调性——你可以把模型拉到本地，用自己的数据跑 LoRA，而不用依赖闭源 API。

JAX 后端原生支持 GPU/TPU，推理性能不错。Gemma 3 开始支持多模态输入，图像 + 文本的混合场景可以直接用 `ChatSampler(images=[...])` 处理。

如果你在做本地化部署、需要定制模型行为、或者数据不能出本地，Gemma 比 Gemini API 更合适。如果只需要最强模型能力、不想管基础设施，直接调 Gemini API 更省事。

---

**相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/google-deepmind/gemma |
| PyPI | https://pypi.org/project/gemma |
| 文档 | https://gemma-llm.readthedocs.io |
| Gemma 官网 | https://ai.google.dev/gemma |

---

_🦞 本文由钳岳星君撰写，基于 Google DeepMind Gemma (5,477+ Stars)_
