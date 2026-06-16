---
title: "LLMs-from-Scratch：用 PyTorch 从零实现 ChatGPT 级大模型"
date: "2026-05-13T20:15:00+08:00"
slug: "llms-from-scratch-pytorch-llm-from-scratch-guide"
description: "LLMs-from-Scratch 是 Sebastian Raschka 的著作《Build a Large Language Model (From Scratch)》配套代码库，通过 Jupyter Notebook 由浅入深地讲解如何从零构建 GPT 类 LLM，涵盖数据处理、注意力机制、预训练、微调全流程。94k+ Stars，零依赖外部 LLM 库，纯 PyTorch 实现。"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "PyTorch", "深度学习", "大模型", "Sebastian Raschka"]
---

# LLMs-from-Scratch：用 PyTorch 从零实现 ChatGPT 级大模型

直接调用 `transformers`、`Hugging Face` 等现成库出结果很快，但模型的内部机制、权重从何而来、注意力如何计算，很多人说不清楚。

**LLMs-from-scratch** 解决的就是这个问题。它是 Sebastian Raschka（《Python 机器学习》作者）著作《Build a Large Language Model (From Scratch)》的配套代码库，94,000+ Stars，GitHub 机器学习分类常年热门。这个仓库不依赖任何外部 LLM 库，全程使用 PyTorch，从张量、嵌入、位置编码开始，手把手实现一个完整可用的 GPT 类模型。

## 谁在做这件事，为什么值得写

Sebastian Raschka 是一位长期活跃于机器学习社区的研究者与教育者，以清晰的技术写作著称。在 LLM 爆发的时代，他选择反其道而行：不是教人"怎么用 Llama"，而是教人"Llama 内部是怎么工作的"。

这本书和代码库的核心观点是：**理解 LLM 内部机制的最好方式，是从零编码实现它**。当你亲手写出注意力机制的矩阵乘法、实现了 GPT 的前向传播逻辑，你会发现很多之前模糊的概念——Context Window、KV Cache、Rotary Embedding、Group-Query Attention——突然清晰起来。

## 项目速览

| 维度 | 内容 |
|------|------|
| 仓库 | [rasbt/LLMs-from-scratch](https://github.com/rasbt/LLMs-from-scratch) |
| Stars | 94,189（截至 2026-05-13） |
| 主要语言 | Jupyter Notebook、Python |
| 作者 | Sebastian Raschka |
| 配套书籍 | [Build a Large Language Model (From Scratch)](https://amzn.to/4fqvn0D)， Manning 出版 |
| 许可证 | MIT |
| 最新动态 | 持续维护，2026 年 5 月仍有提交 |

## 学习路径：从第一个字符到微调指令模型

仓库按书籍章节组织，每章都有配套的 `.ipynb` 主代码文件和对应的 `.py` 纯脚本，适合不同学习习惯的读者。

### Ch 1–2：理解语言模型与文本数据处理

前两章没有代码，主要讲解 LLM 的基本概念与发展历史，以及如何将文本转换为模型可以处理的数值表示。这一阶段会涉及：

- Tokenizer（分词器）的基本原理：BPE、WordPiece、SentencePiece
- 数据集构造：如何将原始语料转换为模型训练的输入序列
- 数据加载器的高效实现：batch、padding、mask

### Ch 3：注意力机制——从理论到实现

这是全书最核心的章节之一。作者从 **Scaled Dot-Product Attention** 讲起，逐步扩展到 **Multi-Head Attention（MHA）**：

```python
import torch
import torch.nn.functional as F
import math

def scaled_dot_product_attention(Q, K, V, mask=None):
    """
    Q, K, V: (batch, heads, seq_len, d_k)
    返回注意力输出与注意力权重
    """
    d_k = Q.size(-1)
    # 注意力分数：Q @ K^T / sqrt(d_k)
    scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(d_k)
    
    if mask is not None:
        scores = scores.masked_fill(mask == 0, float('-inf'))
    
    # 归一化指数，得到注意力权重
    attn_weights = F.softmax(scores, dim=-1)
    return torch.matmul(attn_weights, V), attn_weights
```

在此基础上构建完整的 `MultiHeadAttention` 模块，代码透明，没有隐藏任何魔法。你会清楚看到 `causal mask`（因果掩码）是如何通过简单矩阵操作实现的，以及为什么推理时 KV Cache 能大幅降低计算复杂度。

### Ch 4：从零实现 GPT 模型

基于前三章的积累，第四章完整实现了一个 GPT-2 架构的模型：

- **嵌入层**：词嵌入 + 位置嵌入相加
- **Transformer Block**：LayerNorm → Attention → Residual → LayerNorm → FFN → Residual
- **语言模型头**：线性层输出 vocab 大小的 logits

```python
class GPTModel(torch.nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.tok_emb = torch.nn.Embedding(cfg["vocab_size"], cfg["emb_dim"])
        self.pos_emb = torch.nn.Embedding(cfg["context_length"], cfg["emb_dim"])
        self.drop_emb = torch.nn.Dropout(cfg["drop_rate"])
        self.trf_blocks = torch.nn.ModuleList([TransformerBlock(cfg) for _ in range(cfg["n_layers"])])
        self.final_norm = torch.nn.LayerNorm(cfg["emb_dim"])
        self.out_head = torch.nn.Linear(cfg["emb_dim"], cfg["vocab_size"], bias=False)
    
    def forward(self, x):
       tok_emb = self.tok_emb(x)
        pos_emb = self.pos_emb(torch.arange(x.size(1), device=x.device))
        x = self.drop_emb(tok_emb + pos_emb)
        for block in self.trf_blocks:
            x = block(x)
        return self.out_head(self.final_norm(x))
```

注意这里 `bias=False` 的线性层——这是 GPT-2 相对于原始 Transformer 的一个细节改进，移除了偏置项以提升训练稳定性。

### Ch 5：预训练——从海量文本到语言能力

第五章进入训练阶段，涵盖了：

- 交叉熵损失的正确计算方式（忽略 padding token）
- 学习率调度：warmup + cosine decay
- 分布式训练（Multi-GPU）脚本，使用 PyTorch DDP
- 生成脚本：给定前缀文本，模型续写后续内容

```python
# 简化的训练循环
model = GPTModel(gpt_config)
optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.1)

for batch in train_loader:
    inputs, targets = batch
    logits = model(inputs)
    loss = F.cross_entropy(logits.view(-1, logits.size(-1)), targets.view(-1))
    loss.backward()
    optimizer.step()
    optimizer.zero_grad()
```

作者还提供了预训练数据集的建议来源（公开书籍、Wikipedia 语料等），并说明了如何对数据进行预处理和分词。

### Ch 6–7：微调——让模型听指挥

第六章讲解 **指令微调（Instruction Fine-tuning）**，让模型从"优秀的文本补全器"变为"听从指令的助手"：

- 构造指令-响应对数据集
- 有监督微调的基本流程
- 使用 `ollama` 或 OpenAI API 对微调后模型进行评估

第七章则进一步介绍 **RLHF（人类反馈强化学习）** 的核心概念，包括 Reward Model 的训练和 PPO（Proximal Policy Optimization）的基本原理——尽管完整的 RLHF 实现需要大量计算资源，但作者给出了清晰的概念框架和简化实现。

## 附录：工程深水区

书籍附录覆盖了多个进阶主题，其中值得关注：

- **Appendix A：PyTorch 速查** — 面向不熟悉 PyTorch 的读者，讲解张量操作、GPU 训练、梯度计算等基础
- **Appendix D：训练细节调优** — Gradient Clipping、Mixed Precision Training、Early Stopping
- **Appendix E：LoRA 微调** — 介绍 Parameter-Efficient Fine-Tuning（PEFT）的主流方法，用少量参数微调大模型

## 环境搭建：三分钟跑起来

### 方式一：pip 直接安装

```bash
git clone --depth 1 https://github.com/rasbt/LLMs-from-scratch.git
cd LLMs-from-scratch
pip install -r requirements.txt
```

### 方式二：uv（推荐）

```bash
git clone --depth 1 https://github.com/rasbt/LLMs-from-scratch.git
cd LLMs-from-scratch
pip install uv
uv pip install -r requirements.txt
```

### 方式三：Google Colab

每个章节的 `.ipynb` 文件都可以直接上传到 Google Colab 运行。Colab 已内置 GPU 支持，训练小规模模型完全够用。如果想在 Colab 中安装依赖，运行：

```python
!pip install uv && uv pip install --system -r https://raw.githubusercontent.com/rasbt/LLMs-from-scratch/refs/heads/main/requirements.txt
```

作者在 [setup/README.md](https://github.com/rasbt/LLMs-from-scratch/tree/main/setup) 中提供了更完整的环境配置建议，包括 Docker DevContainer 方案。

## 为什么选择这个仓库

**优点：**

1. **零依赖外部 LLM 库**：所有 Transformer 实现都是手写的，代码量不大但逻辑清晰
2. **配套书籍，内容系统**：不是碎片化的代码片段，而是有教材支撑的系统学习路径
3. **Jupyter Notebook + 纯脚本双版本**：适合边学边实验，也适合直接引用到项目中
4. **作者持续维护**：Issues 响应积极，代码跟随 PyTorch 最新版本更新
5. **覆盖预训练 + 微调完整流程**：不只是"加载预训练权重"，而是完整理解模型如何获得能力

**局限性：**

1. 代码主要面向教学，部分工程化优化（如 KV Cache 的高效实现）未展开
2. 不包含推理优化（量化、Flash Attention 的融合实现）相关内容
3. 预训练部分使用的数据集规模有限，模型规模也较小（受限于个人 GPU 时间）

## 适用场景

- **零基础入门 LLM 内部机制**：第一次学习 attention、transformer、GPT 架构的同学
- **有 PyTorch 基础，想深入理解 LLM**：用过 `transformers` 库但想搞清楚原理的工程师
- **高校/自学机器学习课程**：需要一套完整、可运行的 LLM 实验代码
- **面试准备**：LLM 架构、注意力机制、预训练/微调流程是 AI 方向面试的高频考点

## 总结

LLMs-from-scratch 拆掉了大模型的黑箱：从文本表示、注意力计算、模型训练到指令微调，完整知识链条都有可运行的代码。它不是提供一个"更强大"的模型，而是让你理解手里的模型怎么工作。

如果你之前学 LLM 时跳过了"从零实现"这一步，建议找一个周末，按章节顺序把这个仓库的代码跑一遍。你会发现，再去看 `transformers` 库的源码，很多设计决策突然有了意义。

> **配套书籍**：想配套阅读的，可以购买 Sebastian Raschka 的《Build a Large Language Model (From Scratch)》（Manning，ISBN 9781633437166）。不想买书的话，GitHub 上的代码和 README 本身已经是完整的教程。

---

**延伸阅读：**

- [Sebastian Raschka 博客](https://sebastianraschka.com/blog/)
- [LLMs-from-scratch 仓库](https://github.com/rasbt/LLMs-from-scratch)
- [transformers 库源码阅读](../transformers-huggingface-nlp-guide/)（学完这个仓库后推荐）
- [Flash Attention 原理详解](../flash-attention-fast-exact-attention-guide/)（注意力机制的工程优化方向）