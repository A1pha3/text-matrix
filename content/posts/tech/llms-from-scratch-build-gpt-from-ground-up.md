---
title: "LLMs-from-Scratch 完全指南：从零构建 GPT 大语言模型"
date: "2026-05-14T12:46:00+08:00"
slug: "llms-from-scratch-build-gpt-from-ground-up"
description: "LLMs-from-scratch 是 Sebastian Raschka 所著《Build a Large Language Model (From Scratch)》的官方配套代码仓库。本文提供完整的学习路径、核心概念解析、代码实践指导和常见陷阱提醒，帮助你在不依赖高阶数学的前提下真正理解 LLM 的内部工作机制。"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "GPT", "深度学习", "Python", "PyTorch", "Transformer"]
---

## 学习目标

读完本文并完成配套练习后，你将能够：

- 解释词元化（tokenization）为什么是 LLM 的第一步，以及 BPE 算法如何把文本变成整数序列
- 从零实现一个完整的多头自注意力（Multi-Head Self-Attention）模块，并说清楚每一行代码在做什么
- 理解 Transformer 块中残差连接、层归一化和前馈网络各自的角色，以及它们为什么这样排列
- 区分预训练（pre-training）和微调（fine-tuning）的目标差异，并在一个小数据集上完成整个流程
- 判断什么时候应该从头训练、什么时候应该用预训练模型做微调，以及这个选择对项目成本的影响

---

## 阅读导航

- 想直接开始写代码 → 跳到 `§3 环境搭建`
- 想先理解"为什么要从零构建 LLM" → 重点看 `§1 核心动机`
- 想搞清楚注意力机制到底在算什么 → 重点看 `§4.2 注意力机制`
- 想知道怎么在本地跑起来 → 重点看 `§5 实践：从零训练一个 GPT`
- 想判断这本书适不适合自己 → 重点看 `§6 适用读者与学习路径`

---

## §1 核心动机：为什么要「从零构建」

### 1.1 当前大多数开发者的困境

2026 年，大语言模型已经渗透到开发流程的各个环节——代码补全、文档生成、测试用例编写、需求分析。但大多数开发者对 LLM 的理解止步于调用 API：

```python
# 大多数开发者的 LLM 使用方式
from openai import OpenAI
client = OpenAI(api_key="...")
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "写一个快速排序"}]
)
```

这种方式能完成工作，但有一个根本问题：**你不知道模型为什么给出了这个答案**。当输出不符合预期时，你只能调整 prompt，无法触及模型内部的决策逻辑。

### 1.2 「从零构建」解决什么问题

Sebastian Raschka 的这本书（及其配套代码 `LLMs-from-scratch`）的核心主张是：**只有亲手实现过，你才真正理解**。

这不是为了让你去和 GPT-4 竞争——那需要数亿美元的计算资源。而是为了让你理解：

- 词元化器为什么要把 "hello" 切成 ["hello"] 而不是 ["h", "e", "l", "l", "o"]
- 注意力机制到底在"注意"什么，为什么它能捕捉到词语之间的关系
- 位置编码为什么必要，没有它 Transformer 会丢失什么信息
- 预训练后的模型为什么能通过微调（fine-tuning）适应完全不同的任务

### 1.3 这本书的位置

| 学习路径 | 代表资源 | 适合人群 | 局限性 |
|---------|---------|---------|---------|
| **只用 API** | OpenAI / Anthropic 文档 | 应用开发者 | 无法理解内部机制 |
| **读论文** | Attention Is All You Need, GPT 系列论文 | 研究者 | 数学门槛高，缺实现细节 |
| **从零构建** | **LLMs-from-scratch（本书）** | 想理解内部的工程师 | 需要基础 Python 和深度学习知识 |
| **直接读源码** | HuggingFace transformers 库 | 高级开发者 | 工程封装重，学习曲线陡 |

本书的定位是填补「只用 API」和「读论文/源码」之间的空白。

---

## §2 项目概览

### 2.1 仓库结构

`LLMs-from-scratch` 按书籍章节组织，每一章对应一个可独立运行的代码模块：

```
LLMs-from-scratch/
├── ch01/          # 词元化与数据准备
├── ch02/          # 嵌入与线性层
├── ch03/          # 用 GPT 做文本分类（微调入门）
├── ch04/          # 从零实现自注意力
├── ch05/          # 完整的 Transformer 块
├── ch06/          # 预训练大语言模型（下一词预测）
├── ch07/          # 微调到下游任务
└── appendix/      # 数学背景补充
```

### 2.2 技术栈与前置知识

**必须会的东西：**
- Python 基础（类、函数、列表推导）
- 深度学习基础概念（反向传播、梯度下降、训练/验证集划分）
- PyTorch 基础（张量操作、nn.Module、DataLoader）

**不需要的东西：**
- Transformer 或 LLM 的前置知识（书里会从零讲）
- 高级数学（所有公式都有直观解释，不涉及形式化证明）
- 大模型训练经验（书里用小规模数据集，笔记本 GPU 就能跑）

### 2.3 代码运行需求

| 资源 | 最低配置 | 推荐配置 |
|------|---------|---------|
| 内存（RAM） | 8GB | 16GB+ |
| GPU | 可选（CPU 能跑但慢） | NVIDIA GPU 4GB+ 显存 |
| 磁盘空间 | 2GB | 5GB（含示例数据集） |
| Python 版本 | 3.9+ | 3.10+ |

---

## §3 环境搭建

### 3.1 安装步骤

```bash
# 克隆仓库
git clone https://github.com/rasbt/LLMs-from-scratch.git
cd LLMs-from-scratch

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3.2 验证安装

```python
# test_setup.py
import torch
from ch04.ch04_main import MultiHeadAttention

# 检查 PyTorch 是否可用
print(f"PyTorch 版本: {torch.__version__}")
print(f"CUDA 可用: {torch.cuda.is_available()}")

# 快速测试注意力模块
mha = MultiHeadAttention(d_in=128, d_out=128, num_heads=4)
x = torch.randn(2, 10, 128)  # (batch, seq_len, embed_dim)
output = mha(x)
print(f"输出形状: {output.shape}")  # 应该是 (2, 10, 128)
```

如果看到正确的输出形状，说明环境配置成功。

### 3.3 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| `ModuleNotFoundError: No module named 'ch04'` | 从错误的目录运行 | 在项目根目录运行，或设置 `PYTHONPATH` |
| `CUDA out of memory` | GPU 显存不足 | 减小 `batch_size`，或用 CPU 运行（慢 10-50 倍） |
| `TypeError in attention forward` | PyTorch 版本不兼容 | 确保 PyTorch ≥ 2.0 |

---

## §4 核心概念解析

### 4.1 词元化：LLM 如何「看」文本

**为什么需要词元化？**

LLM 不直接处理文字。它们处理整数。词元化器（tokenizer）的作用是：把一段文本转换成一个整数序列，每个整数对应词表中的一个「词元」。

```python
# 直观例子
from tiktoken import encoding_for_model

enc = encoding_for_model("gpt-3.5-turbo")
text = "Building LLMs from scratch is rewarding."
tokens = enc.encode(text)
print(tokens)
# 输出: [73448, 2672, 310, 2428, 437, 6740, 13, 23441, 12047, 29879, 11337, 264, 4157, 12240, 264, 9820, 9391, 28671, 264, 4145, 220, 428, 1022, 372, 9006, 29892, 5614, 139, 231, 8698, 304, 10215, 13]
```

**BPE（Byte Pair Encoding）算法直觉**

BPE 的核心思想是：从字符级别开始，反复把「最常相邻出现的字符对」合并成一个新的词元。

1. 初始词表 = 所有字符
2. 统计所有相邻字符对的出现频率
3. 把最频繁的那对合并，加入词表
4. 重复步骤 2-3，直到词表达到目标大小

这样做的结果是：常见词（如 "the", "is"）会变成一个词元；罕见词会被切成多个子词。

**为什么这样设计？**

- 如果每个词一个词元 → 词表太大（英语有几十万词），罕见词训练不足
- 如果每个字符一个词元 → 序列太长，模型难以捕捉长距离依赖
- BPE 是两者之间的平衡：常见词完整保留，罕见词合理切分

### 4.2 注意力机制：LLM 的核心引擎

**先回答「为什么需要注意力」**

在没有注意力机制之前，语言模型（如 RNN、LSTM）逐个处理词元，把前面所有的信息压缩成一个固定大小的「隐藏状态」。这样做有两个问题：

1. **信息瓶颈**：固定大小的向量无法完整保留长句子的所有信息
2. **长距离依赖衰减**：句子开头的信息在经过多步传递后会逐渐消失

注意力机制解决了这个问题：它让序列中的每个位置都能「直接看到」所有其他位置，不需要通过中间状态传递信息。

**自注意力在算什么？**

自注意力本质上是一个「加权求和」操作：

```
对于每个词元，计算它和所有其他词元的相似度 → 得到注意力权重 → 用权重对其他词元的表示做加权求和
```

用公式表达：

```
Attention(Q, K, V) = softmax(QK^T / √d_k) × V
```

- Q（Query）：当前词元在「问」什么
- K（Key）：其他词元提供的「标签」
- V（Value）：其他词元实际包含的「信息」
- softmax(QK^T)：计算相似度，得到注意力权重

**代码直觉**

```python
# 简化版自注意力（单头，无掩码）
def simple_attention(X):
    """
    X: 输入序列, shape (seq_len, embed_dim)
    返回: 注意力输出, shape (seq_len, embed_dim)
    """
    # Step 1: 生成 Q, K, V
    W_q = torch.randn(embed_dim, embed_dim)
    W_k = torch.randn(embed_dim, embed_dim)
    W_v = torch.randn(embed_dim, embed_dim)
    
    Q = X @ W_q
    K = X @ W_k
    V = X @ W_v
    
    # Step 2: 计算注意力分数
    scores = Q @ K.T  # shape: (seq_len, seq_len)
    
    # Step 3: 缩放（为什么除以 √d_k？让梯度更稳定）
    d_k = K.shape[-1]
    scores = scores / torch.sqrt(torch.tensor(d_k, dtype=torch.float32))
    
    # Step 4: softmax 得到注意力权重
    attn_weights = torch.softmax(scores, dim=-1)
    
    # Step 5: 加权求和
    output = attn_weights @ V
    return output
```

**因果掩码（Causal Mask）为什么必要？**

GPT 是「自回归」模型：生成每个词时，只能看到前面的词，不能看到后面的词。因果掩码就是把注意力矩阵的上三角部分设为 `-inf`，这样 softmax 后这些位置的权重就是 0。

```
# 没有掩码: 每个词都能看到所有词（包括未来的词）
# 有掩码:  每个词只能看到自己和前面的词

注意力矩阵（无掩码）:       注意力矩阵（有因果掩码）:
[1.0  0.8  0.3]          [1.0  0.0  0.0]
[0.7  1.0  0.6]    →     [0.7  1.0  0.0]
[0.2  0.5  1.0]          [0.2  0.5  1.0]
```

### 4.3 位置编码：让模型知道词的顺序

**为什么需要位置编码？**

注意力机制有一个特性：它是「排列不变」的。如果把输入序列的词元顺序打乱，注意力输出不变（因为 QK^T 的计算与顺序无关）。

但语言是有顺序的——"狗咬人"和"人咬狗"意思完全不同。所以需要显式地把位置信息注入模型。

**两种主流方案：**

| 方案 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| **绝对位置编码** | 给每个位置一个固定向量，直接加到词嵌入上 | 简单 | 无法泛化到训练时未见过的序列长度 |
| **RoPE（旋转位置编码）** | 用旋转矩阵编码相对位置信息 | 能泛化到更长序列 | 实现稍复杂 |

本书第 6 章会带你完整实现 RoPE。

### 4.4 Transformer 块：把部件组装起来

一个完整的 Transformer 块（Decoder-only 架构，用于 GPT）包含：

```
输入
  ↓
LayerNorm
  ↓
Multi-Head Attention (+ 残差连接)
  ↓
LayerNorm
  ↓
Feed-Forward Network (+ 残差连接)
  ↓
输出
```

**为什么这样排列？**

- **残差连接**（skip connection）：让梯度能直接反向传播到浅层，缓解梯度消失
- **LayerNorm 在注意力之前**（Pre-LN）：让训练更稳定，这是现代 LLM 的标准做法（GPT-2 之后）
- **前馈网络**：对每个位置独立做非线性变换，增加模型的表达能力

---

## §5 实践：从零训练一个 GPT

### 5.1 数据准备

本书使用一个小型数据集（~10MB 文本）来演示完整流程。你也可以用自己的文本数据：

```python
# 准备训练数据
from ch06.ch06_main import create_dataloader

with open("data/the-verdict.txt", "r", encoding="utf-8") as f:
    raw_text = f.read()

# 词元化
tokenizer = tiktoken.get_encoding("gpt2")
token_ids = tokenizer.encode(raw_text)

# 创建数据加载器
train_loader = create_dataloader(
    token_ids,
    batch_size=4,
    max_length=256,    # 每个样本最多 256 个词元
    stride=128,         # 滑动窗口步长（有重叠）
    shuffle=True
)
```

### 5.2 模型配置

```python
# GPT 模型配置（小型版本，适合本地训练）
GPT_CONFIG_SMALL = {
    "vocab_size": 50257,      # GPT-2 词表大小
    "d_model": 768,           # 嵌入维度
    "n_heads": 12,            # 注意力头数
    "n_layers": 12,           # Transformer 块数
    "max_seq_len": 1024,      # 最大序列长度
    "dropout": 0.1,          # dropout 比例
    "qkv_bias": False         # 注意力的 QKV 是否加偏置
}
```

### 5.3 训练循环

```python
# 简化版训练循环
model = GPTModel(GPT_CONFIG_SMALL)
optimizer = torch.optim.AdamW(model.parameters(), lr=5e-4, weight_decay=0.1)

for epoch in range(num_epochs):
    for batch in train_loader:
        input_ids, target_ids = batch
        
        # 前向传播
        logits = model(input_ids)        # shape: (batch, seq_len, vocab_size)
        loss = cross_entropy(logits, target_ids)
        
        # 反向传播
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    
    print(f"Epoch {epoch}, Loss: {loss.item():.4f}")
```

### 5.4 生成文本

训练完成后，用自回归方式生成文本：

```python
def generate(model, idx, max_new_tokens, temperature=1.0):
    """
    idx: 初始词元序列, shape (batch, seq_len)
    """
    model.eval()
    with torch.no_grad():
        for _ in range(max_new_tokens):
            # 前向传播得到下一个词元的 logits
            logits = model(idx)                      # (batch, seq_len, vocab_size)
            logits = logits[:, -1, :]              # 只看最后一个位置 (batch, vocab_size)
            
            # 温度采样
            if temperature > 0:
                logits = logits / temperature
                probs = torch.softmax(logits, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1)
            else:
                # greedy 解码
                next_token = torch.argmax(logits, dim=-1, keepdim=True)
            
            # 把新词元追加到序列
            idx = torch.cat([idx, next_token], dim=1)
    
    return idx

# 使用
prompt = "Once upon a time"
token_ids = tokenizer.encode(prompt)
token_ids = torch.tensor(token_ids).unsqueeze(0)  # 加 batch 维度
output_ids = generate(model, token_ids, max_new_tokens=100, temperature=0.8)
print(tokenizer.decode(output_ids.squeeze().tolist()))
```

---

## §6 适用读者与学习路径

### 6.1 适用读者

| 读者类型 | 推荐指数 | 理由 |
|---------|---------|------|
| **有 Python 基础的 AI 工程师** | ⭐⭐⭐⭐⭐ | 最直接的目标读者，能立即应用 |
| **深度学习研究者** | ⭐⭐⭐⭐ | 能加深对架构设计决策的理解 |
| **技术管理者** | ⭐⭐⭐ | 不需要写代码，但能帮助理解技术边界和成本结构 |
| **完全零基础的初学者** | ⭐⭐ | 需要先补 Python 和深度学习基础 |

### 6.2 推荐学习路径

**第一遍：跑通代码（1-2 周）**

不要纠结每个细节。把每一章的代码跑起来，看着损失函数下降，生成一些文本。目标是建立直觉。

**第二遍：搞懂「为什么」（2-4 周）**

回到每一章，搞懂：
- 这个词元化算法为什么比字符级好？
- 注意力机制到底在算什么？
- 为什么要用残差连接？

**第三遍：改动和实验（持续）**

- 换一个小数据集重新训练
- 改变模型大小，观察性能变化
- 实现书里没覆盖的变体（如不同的位置编码方案）

### 6.3 常见陷阱

| 陷阱 | 表现 | 如何避免 |
|------|------|---------|
| **跳过数学直觉** | 能跑代码但不理解原理 | 每一章先读概念解释，再写代码 |
| **直接用大模型配置** | OOM（显存不足） | 先用小型配置跑通，再逐步扩大 |
| **忽略数据质量** | 模型生成乱码 | 用小但干净的数据集，观察过拟合 |
| **不理解因果掩码** | 训练正常但生成效果差 | 动手画一下注意力矩阵，确认上三角全为 0 |

---

## §7 采用建议

### 7.1 这本书/代码库适合你，如果：

- 你想真正理解 LLM 内部机制，而不只是调用 API
- 你需要向别人解释 Transformer 架构，想用代码而不是数学公式
- 你在做 LLM 相关的工程项目，需要判断某些行为是不是架构导致的

### 7.2 这本书/代码库不适合你，如果：

- 你只想快速用 LLM 做一个应用 → 直接用 HuggingFace 或 API
- 你已经对 Transformer 架构很熟悉，想研究最新技术 → 直接读论文和 SOTA 模型源码
- 你没有 Python 或深度学习基础 → 先学 PyTorch 基础

### 7.3 和其他资源配合使用

| 配合资源 | 用途 |
|---------|------|
| **Attention Is All You Need（论文）** | 理解原始 Transformer 的设计动机 |
| **HuggingFace transformers 文档** | 了解工业级实现和 API 设计 |
| **Andrej Karpathy 的 "Let's build GPT" 视频** | 补充直觉（免费，1 小时讲完核心思想） |
| **scale AI 的 "Mechanistic Interpretability" 系列** | 深入理解训练后模型内部在发生什么 |

---

## §8 自测练习

完成以下练习，检验你的理解程度：

1. **词元化器分析**：用 tiktoken 对 "artificial intelligence" 和 "AI" 分别做词元化，观察结果差异，并解释为什么会有这样的差异。

2. **注意力可视化**：取一个训练好的小模型，选一句话，画出注意力权重热力图。观察某些头是否稳定地关注特定模式（如相邻词、句首词等）。

3. **位置编码消融实验**：去掉位置编码，在相同数据上训练，比较困惑度（perplexity）差异。

4. **模型缩放实验**：保持数据量不变，分别训练 2 层、6 层、12 层的模型，画出训练曲线，观察过拟合出现的时机。

---

**参考资源：**

- 原书：Sebastian Raschka, *Build a Large Language Model (From Scratch)*, 2024
- 代码仓库：https://github.com/rasbt/LLMs-from-scratch
- 配套视频：Andrej Karpathy, "Let's build GPT: from scratch, in code, spelled out" (YouTube)
- 交互式 Transformer 可视化：https://poloclub.github.io/transformer-explainer/

> **每日 GitHub 趋势榜自动分析 | 数据来源：GitHub Trending**
