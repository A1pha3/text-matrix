---
title: "Neural Networks: Zero to Hero - Karpathy 的神经网络从零到英雄课程"
date: "2026-05-23T15:30:00+08:00"
slug: karpathy-nn-zero-to-hero-neural-networks-course
description: "Andrej Karpathy 从最基本的 Python 知识出发，用一系列 YouTube 视频和 Jupyter Notebook，带你从零实现神经网络核心概念，最终抵达 GPT 级别语言模型。22.5k stars 的明星课程。"
tags: [Neural Networks, Deep Learning, Karpathy, PyTorch, Jupyter Notebook, Language Model, GPT, Backpropagation]
categories: ["技术笔记"]
author: 钳岳星君
---

Andrej Karpathy 的 [Neural Networks: Zero to Hero](https://github.com/karpathy/nn-zero-to-hero) 是 GitHub 上最受欢迎的神经网络教学仓库之一，22,500 颗星、3,249 个 Fork。这门课的特殊之处在于：它不是"看完就忘"的概述，而是一套**跟着敲代码、亲眼看每一步梯度计算**的实战型教程。

## 课程结构：从 micrograd 到 GPT

整个课程是一系列环环相扣的视频 + Jupyter Notebook，路径如下：

### Lecture 1: micrograd — 手动实现反向传播

从零实现一个极简的自动微分（autograd）引擎。你会看到 loss.backward() 背后到底发生了什么——所有梯度是如何从 loss 一路反向传播回每一个参数的手动求导过程。假设你会写 Python，记得一点高中数学就能跟上。

**视频：** [YouTube](https://www.youtube.com/watch?v=VMj-3S1tku0) | **Notebook:** [micrograd](https://github.com/karpathy/micrograd)

### Lecture 2: makemore Part 1 — 字符级语言模型

用 PyTorch 实现第一个 bigram 字符级语言模型。核心是理解 torch.Tensor 的使用方式和语言建模的整体框架：训练 → 采样 → 评估 loss（负对数似然）。

**视频：** [YouTube](https://www.youtube.com/watch?v=PaCmpygFfXo)

### Lecture 3: makemore Part 2 — MLP

在 Part 1 基础上扩展为多层感知器（MLP）字符级语言模型，同时引入大量机器学习基础知识：学习率调参、超参数、Train/Dev/Test 划分、欠拟合与过拟合判断等。

**视频：** [YouTube](https://youtu.be/TCH_1BHY58I)

### Lecture 4: makemore Part 3 — 激活函数、梯度与 BatchNorm

深入 MLPs 内部，考察前向传播激活值的统计分布和反向传播梯度流。理解深度网络训练为何脆弱，以及 Batch Normalization 是如何解决这一问题的。

**视频：** [YouTube](https://youtu.be/P6sfmUTpUmc)

### Lecture 5: 成为反向传播忍者

在不用 PyTorch autograd 的情况下，手动反向传播穿过整个网络：Cross Entropy Loss → 线性层 → Tanh → BatchNorm → Embedding 表。这是整个系列中最"硬核"的部分，帮助你真正建立对梯度流向的直觉。

**视频：** [YouTube](https://youtu.be/P6Y锄?si=xxx)（视频链接见 GitHub）

## 这门课适合谁

| 条件 | 适合程度 |
|------|----------|
| 会写 Python，了解基础数据结构 | ✅ 必需 |
| 了解微积分（导数、偏导） | ✅ 建议有，但视频会解释 |
| 有深度学习经验 | ✅ 可以当复习 |
| 纯零基础（连 Python 都不会） | ❌ 不适合 |

## 为什么这门课值得投入时间

1. **真正理解而非调库**：市面大多数教程教你"怎么用 PyTorch"，这门课教你"神经网络到底在算什么"。
2. **从零造轮子**：先手工实现一遍，再看高级框架，你会对现有工具的理解提升一个层次。
3. **Karpathy 的教学风格**：他擅长用直观的可视化解释复杂概念，这是同类课程少有的。
4. **后续可通往 GPT**：课程终点不是"跑通一个 MLP"，而是带你一步步从 bigram 模型走向 Transformer 语言模型。

## 如何开始

```bash
git clone https://github.com/karpathy/nn-zero-to-hero.git
cd nn-zero-to-hero/lectures
# 按课程顺序依次打开 Jupyter notebook
```

建议配合对应视频一起看，在本地跟着敲一遍代码。

## 延伸阅读

- [micrograd](https://github.com/karpathy/micrograd) — 独立的自动微分引擎仓库
- [makemore](https://github.com/karpathy/makemore) — makemore 的独立版本
- Karpathy 的博客和更多项目可以在 [karpathy.github.io](https://karpathy.github.io/) 找到

---

**一句话总结：** 如果你想真正理解神经网络的工作原理，而不是停留在调 API 层面，这门课是最值得投入时间的路径。从零到英雄，从 micrograd 到 GPT，代码量不大，但每一步都扎扎实实。