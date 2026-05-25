---
title: "Neural Networks: Zero to Hero：Karpathy神经网络入门到精通完全指南"
date: "2026-05-23T03:39:42+08:00"
slug: "karpathy-nn-zero-to-hero-neural-networks-guide"
description: "Neural Networks: Zero to Hero是Andrej Karpathy推出的深度学习视频课程，通过Jupyter Notebook从零构建micrograd（手动反向传播）、makemore（字符级语言模型）和GPT。课程从基础数学起步，逐步深入到现代Transformer架构。22k Stars，开源MIT，适合想真正理解神经网络原理的开发者。"
draft: false
categories: ["技术笔记"]
tags: ["深度学习", "神经网络", "Python", "Jupyter Notebook", "Andre Karpathy"]
---

## 项目概览

**Neural Networks: Zero to Hero**（简称 nn-zero-to-hero）是 OpenAI 联合创始人 Andrej Karpathy 推出的一套深度学习视频课程，通过 Jupyter Notebook 从零开始手写神经网络，最终实现 GPT 级别的语言模型。仓库收录了课程中所有 Notebook 文件，共 8 个 Lecture，22,264 Stars，3,237 Forks，MIT 许可证。

课程的核心思路是"从零搞懂，不依赖框架黑箱"——不调用高级 API，而是亲手实现每一个关键组件，在代码里建立直觉。

## 为什么值得看

深度学习入门资源已经很多了，为什么这个仓库值得关注？

Karpathy 的风格是把"看起来很复杂的东西拆成一步一步写出来"。课程从最基础的 Python 自动求导开始，一路写到 GPT-2 规模的 Transformer。中间不跳步，每行代码都有理由。

这个仓库的价值不在于提供现成的模型，而在于**让你理解模型为什么会work**。当你能徒手写出反向传播、理解张量形状变化亲手推演过程、看到 BatchNorm 为什么要那样归一化——这时候再去调框架，才是真正可控的。

## 核心能力

仓库围绕 8 个 Lecture 展开，难度逐级递进：

### Lecture 1 — micrograd：反向传播从零实现

从 `numpy` 手工实现一个极简自动求导（AutoGrad）引擎。核心是构建计算图（Computational Graph），每个运算记录自己的梯度函数，反向传播时逐层回填。

这节的目标是让你彻底理解**链式法则（Chain Rule）**在实际代码里怎么跑起来——不是公式，是 `backward()` 里真实的数值操作。

### Lecture 2 — makemore Part 1：字符级语言模型引入

用 PyTorch 实现一个 Bigram 字符级语言模型。核心引入：`torch.Tensor` 的用法、`negative log likelihood` 损失函数、语言模型的采样（sampling）逻辑。

这节解决的核心问题：**语言模型训练在做什么，loss 为什么会下降，采样出来的字符凭什么看起来"像人话"。**

### Lecture 3 — makemore Part 2：MLP 多层感知机

扩展为多层感知机（Multi-Layer Perceptron，MLP）。引入训练/验证/测试集划分、过拟合与欠拟合、学习率调参、超参数网格等基础机器学习概念。

这时候你会看到：同样一套代码，换一个字符集，就能生成新名字。

### Lecture 4 — makemore Part 3：激活函数、梯度与 BatchNorm

深入研究神经网络内部：前向激活（activation）的数值分布、后向梯度（gradient）的规模、BatchNorm 为什么要归一化。引入了神经网络"健康诊断"的可视化方法。

BatchNorm 让深层网络训练不再那么脆弱，这是 2015 年提出的经典技术，依然是理解现代网络的重要基础。

### Lecture 5 — makemore Part 4：手写反向传播

**难度最高的节之一**。把 Part 2 的 2 层 MLP（带 BatchNorm）拿出来，不使用 PyTorch 的 `autograd`，手动 backprop 穿过交叉熵损失、线性层、tanh、BatchNorm、Embedding 表。

做完这节，反向传播不再是黑箱——你能看到梯度在计算图中每一步的具体数值是什么。

### Lecture 6 — makemore Part 5：WaveNet 风格 CNN

用树状结构加深网络，引入了卷积神经网络（CNN）架构，与 DeepMind 2016 年 WaveNet 的层次结构类似。引入了 `torch.nn` 的底层用法、多维张量形状维护、文档阅读与代码切换的开发流程。

### Lecture 7 — Let's build GPT

**课程最高点**。从零实现一个 Generatively Pretrained Transformer（GPT），参考了"Attention is All You Need"论文和 OpenAI GPT-2/GPT-3 的设计。引入了自注意力（Self-Attention）机制、位置编码（Positional Encoding）、GPT 的训练和采样流程。

这节需要提前熟悉 autoregressive 语言建模框架和 PyTorch 基础，但 Karpathy 在视频里带着一步步写，几乎不跳步。

### Lecture 8 — Let's build the GPT Tokenizer

tokenizer（分词器）是 LLM 流水线中最容易被忽视但影响最大的组件。课程从零实现了 GPT 系列使用的 BPE（Byte Pair Encoding）分词算法，解释了为什么很多 LLM 的奇怪行为（中文 token 碎片化、非英语字符处理问题）根源都在 tokenization。

## 快速开始

### 环境准备

```bash
git clone https://github.com/karpathy/nn-zero-to-hero.git
cd nn-zero-to-hero
```

### 依赖

Notebook 基于 Python 3 和 PyTorch，部分 Lecture 仅需 `numpy`。推荐创建虚拟环境：

```bash
python3 -m venv nn-env
source nn-env/bin/activate  # macOS/Linux
# nn-env\Scripts\activate  # Windows
pip install jupyter numpy torch
```

### 打开第一个 Lecture

```bash
cd lectures/micrograd
jupyter notebook
```

从 `micrograd` 的 `Value` 类开始读，理解如何用 Python 对象构建计算图、实现 `backward()`。

### 视频配合

每个 Lecture 都有对应的 YouTube 视频（B站有搬运）。推荐边看视频边在 Notebook 里跟着敲。

## 适用边界

**适合：**
- 有 Python 基础、想真正理解神经网络原理的开发者
- 看过吴恩达课程但感觉"调包调通了但说不清原理"的学习者
- 希望从零实现一遍深度学习核心概念的研究人员

**不适合：**
- 需要快速拿模型去跑业务的项目（应该用 `transformers` 或 LangChain）
- 只想要高层 API 使用方法的人
- 对数学要求完全陌生、连矩阵乘法都不熟悉的完全初学者（建议先补基础）

**特别说明：** 这是一个教学性质极强的仓库，代码不是生产级实现。课程目标是"通透理解"，不是"高性能推理"。学完之后你对框架内部有直觉，再回到 HuggingFace 这些高层库，是真正的升级。

## 阅读路径

建议按顺序走：

| 阶段 | Lecture | 核心收获 |
|------|---------|-----------|
| 入门 | L1 micrograd | 搞懂反向传播 |
| 奠基 | L2~L3 makemore | 语言模型训练框架 + MLP |
| 深入 | L4~L5 | BatchNorm + 手动 backprop |
| 扩展 | L6 | CNN 与 torch.nn 底层 |
| 精通 | L7 | Transformer/GPT 完整实现 |
| 收尾 | L8 | tokenizer 原理 |

时间充裕的可以从头跟一遍；时间紧张的推荐 **L1 + L5 + L7**，这三个最能建立对深度学习的核心直觉。

## 相关项目

Karpathy 在课程中拆出来的独立仓库也值得关注：

- [micrograd](https://github.com/karpathy/micrograd)：独立的自动求导引擎，极简只有 100 行
- [makemore](https://github.com/karpathy/makemore)：更完整的字符级语言模型实现
- [minbpe](https://github.com/karpathy/minbpe)：从零实现的 BPE 分词器

如果 nn-zero-to-hero 是"课程"，这几个仓库就是"作业答案"——学完课程再去看源码，会有一种"原来这行是这里的意思"的感觉。

---

*课程视频在 [YouTube](https://www.youtube.com/@AndrejKarpathy)，B站有大量中文搬运。*