---
title: "LLMs-from-Scratch：用 PyTorch 从零实现 ChatGPT 级大模型"
date: "2026-05-13T20:15:00+08:00"
slug: "llms-from-scratch-pytorch-llm-from-scratch-guide"
github_repo: "rasbt/LLMs-from-scratch"
source_key: "gh:rasbt/LLMs-from-scratch"
description: "LLMs-from-Scratch 是 Sebastian Raschka 的著作《Build a Large Language Model (From Scratch)》配套代码库，通过 Jupyter Notebook 由浅入深地讲解如何从零构建 GPT 类 LLM，涵盖数据处理、注意力机制、预训练、微调全流程。105k+ Stars，零依赖外部 LLM 库，纯 PyTorch 实现。"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "PyTorch", "深度学习"]
---

# LLMs-from-Scratch：用 PyTorch 从零实现 ChatGPT 级大模型

直接调用 `transformers`、Hugging Face 等现成库出结果很快，但模型的内部机制、权重从何而来、注意力如何计算，很多人说不清楚。

**LLMs-from-scratch** 解决的就是这个问题。它是 Sebastian Raschka（《Python 机器学习》作者）著作《Build a Large Language Model (From Scratch)》的配套代码库，105,000+ Stars，GitHub 机器学习分类常年热门。这个仓库不依赖任何外部 LLM 库，全程使用 PyTorch，从张量、嵌入、位置编码开始，手把手实现一个完整可用的 GPT 类模型。

先澄清一个说法：所谓"ChatGPT 级"，指架构同源——你实现的是 GPT-2 架构的模型（124M 参数级别），与 ChatGPT 共享同一骨架：自注意力、因果掩码、位置编码、Transformer Block。规模小，但机制不缩水；把 124M 换成更大配置表，就是 GPT-2 全系列。

## 学习目标

读完本文，你将能够：

- 说出本书与仓库的章节编排，以及每一章解决什么问题
- 讲清自注意力为什么要除以 $\sqrt{d_k}$，因果掩码如何挡住未来词
- 复述 GPT 各组件（词嵌入、LayerNorm、GELU、残差连接、输出头）的职责
- 区分预训练、分类微调、指令微调三种训练阶段
- 知道加载预训练权重、LoRA、KV Cache、MoE 等进阶方向去哪里学
- 判断这个仓库适不适合自己的学习阶段

## 目录

1. [作者与写作动机](#作者与写作动机)
2. [项目速览](#项目速览)
3. [章节地图：从文本到指令模型](#章节地图从文本到指令模型)
4. [核心章节拆解](#核心章节拆解)
5. [附录与 Bonus 材料](#附录与-bonus-材料)
6. [环境搭建：三分钟跑起来](#环境搭建三分钟跑起来)
7. [为什么选择这个仓库](#为什么选择这个仓库)
8. [适用场景](#适用场景)
9. [自测清单](#自测清单)
10. [练习](#练习)
11. [进阶路径](#进阶路径)
12. [总结](#总结)

## 作者与写作动机

Sebastian Raschka 是一位长期活跃于机器学习社区的研究者与教育者，以清晰的技术写作著称，代表作有《Python 机器学习》。在 LLM 爆发的时代，他选择反其道而行：不是教人"怎么用 Llama"，而是教人"Llama 内部是怎么工作的"。

这本书和代码库的核心观点是：**理解 LLM 内部机制的最好方式，是从零编码实现它**。当你亲手写出注意力机制的矩阵乘法、实现了 GPT 的前向传播逻辑，你会发现很多之前模糊的概念——Context Window、KV Cache、Rotary Embedding、Group-Query Attention——突然清晰起来。

## 项目速览

| 维度 | 内容 |
|------|------|
| 仓库 | [rasbt/LLMs-from-scratch](https://github.com/rasbt/LLMs-from-scratch) |
| Stars | 105,659（截至 2026-09-28 快照） |
| 主要语言 | Jupyter Notebook、Python |
| 作者 | Sebastian Raschka |
| 配套书籍 | [Build a Large Language Model (From Scratch)](https://amzn.to/4fqvn0D)，Manning 出版，ISBN 9781633437166 |
| 配套课程 | [17 小时视频课程](https://www.manning.com/livevideo/master-and-build-large-language-models)，按章节逐行编码 |
| 许可证 | Apache License 2.0（`LICENSE.txt`） |
| 正文章节 | 7 章 + 附录 A–E |
| 后续作品 | [Build A Reasoning Model (From Scratch)](https://mng.bz/lZ5B)，本书的精神续作 |

仓库按书籍章节组织（`ch01`–`ch07`）。每章必有 `01_main-chapter-code` 目录，装着主 Notebook、精简版 `.py` 脚本和练习解答；Bonus 与专项内容以编号目录平铺在旁，各章数量不一——`ch04` 有 10 个专题目录（KV Cache、GQA、MLA、MoE 等），`ch05` 多达 19 个。书外还有一份免费的 170 页 PDF《Test Yourself on Build a Large Language Model (From Scratch)》，Manning 官网可下载，每章约 30 道自测题附答案。

## 章节地图：从文本到指令模型

仓库按书籍章节组织，每章都有配套的 `.ipynb` 主代码文件和对应的 `.py` 精简脚本，适合不同学习习惯的读者。七章是一条直线路径：

| 章节 | 主题 | 产出 |
| ---- | ---- | ---- |
| Ch 1 | 理解大语言模型 | 概念与 GPT 架构全景 |
| Ch 2 | 处理文本数据 | BPE 分词器 + 数据加载器 |
| Ch 3 | 编码注意力机制 | 自注意力 → 多头注意力 |
| Ch 4 | 实现 GPT 模型 | 能生成文本的 GPT 前向传播 |
| Ch 5 | 在无标签数据上预训练 | 预训练权重 + 生成能力 |
| Ch 6 | 分类微调 | 垃圾短信分类器等下游任务 |
| Ch 7 | 指令微调 | 能听指令的助手 |

## 核心章节拆解

### Ch 1–2：理解语言模型与文本数据处理

第 1 章以概念为主：LLM 是什么、Transformer 从何而来、GPT 架构由哪些组件构成、构建一个 LLM 要经过哪些阶段。第 2 章开始动手，核心是两件事：

- **手写 BPE 分词器**：逐字符统计相邻 token 对的频率、迭代合并高频对，把文本变成 token id；WordPiece、SentencePiece 等其他方案只做对比提及
- **实现数据加载器**：用滑动窗口从语料切出上下文序列，构造"输入与目标错位一位"的 (inputs, targets) 对，供自监督训练使用

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

在此基础上构建完整的 `MultiHeadAttention` 模块，代码透明，没有隐藏任何魔法。两个细节值得停下来想：

- **除以 $\sqrt{d_k}$**：维度增大时，分数分布的方差随之增大，softmax 会过早饱和、梯度趋近于零。缩放后分布更平缓，训练更稳定
- **因果掩码**：用上三角矩阵配合 `masked_fill` 把未来位置的分数置为 `-inf`，softmax 后权重归零，模型就"看不见"未来词

KV Cache 的工程实现不在本章，而在 Ch 4 的 Bonus 目录（`ch04/03_kv-cache`）单独展开。

### Ch 4：从零实现 GPT 模型

基于前三章的积累，第四章完整实现了一个 GPT-2 架构的模型，并跑通文本生成：

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
        self.trf_blocks = torch.nn.ModuleList(
            [TransformerBlock(cfg) for _ in range(cfg["n_layers"])]
        )
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

注意这里 `bias=False` 的线性层——这是 GPT-2 相对于原始 Transformer 的一个细节改进，移除偏置项以提升训练稳定性。

GPT-2 的经典配置（书中以此训练 124M 小模型）：

| 配置项 | 124M | 355M | 774M | 1558M |
| ---- | ---- | ---- | ---- | ---- |
| n_layers | 12 | 24 | 36 | 48 |
| emb_dim | 768 | 1024 | 1280 | 1600 |
| n_heads | 12 | 16 | 20 | 25 |

124M 的具体取值：`vocab_size=50257`、`context_length=1024`、`drop_rate=0.1`、`qkv_bias=False`。只改配置字典里的数字，同一个 `GPTModel` 就能长出更大规模——这也是本书实现可扩展的原因。

### Ch 5：预训练——从海量文本到语言能力

第五章进入训练阶段，涵盖了：

- 交叉熵损失的正确计算方式（忽略 padding token），以及用 perplexity 评估生成质量
- 学习率调度：warmup + cosine decay
- 解码策略：temperature 缩放与 top-k 采样，控制生成的随机性
- 保存与加载权重，包括从 OpenAI 直接加载预训练权重
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

作者还提供了预训练数据集的建议来源（公开书籍、Project Gutenberg 语料等），并附上在 Gutenberg 上完整预训练一个 GPT 的脚本。多 GPU（DDP）训练脚本放在附录 A，用到时再取。

顺带提醒：上面的 `lr=3e-4`、`weight_decay=0.1` 是书中示例值，不是万能解。超参数该怎么调，Ch 5 的 Bonus 目录里有专门实验（`ch05/05_bonus_hparam_tuning`）。

### Ch 6：分类微调——让模型做选择题

第六章把预训练模型接到具体任务上，以垃圾短信分类为例：

- 复用预训练权重，把输出层替换为分类头
- 取序列最后一个 token 的隐藏状态作为整条文本的表示
- 计算分类损失与准确率，在带标签数据上有监督微调

这一章演示了"能力 → 任务适配"的标准路径：预训练负责语言能力，微调负责指哪打哪。

### Ch 7：指令微调——让模型听指挥

第七章把模型从"优秀的文本补全器"变成"听从指令的助手"：

- 构造指令-响应对数据集（可基于 Alpaca、LIMA 等公开数据集）
- 损失只计算在 response 部分，指令部分被掩码掉——否则模型会把"复述指令"也当成本事
- 加载预训练模型做有监督微调，生成后抽取并保存回复
- 用 `ollama`（本地）或 OpenAI API 对微调后模型做对比评估

微调结束，一条"从数据到指令助手"的完整链路就走通了。偏好对齐方面，本章 Bonus 目录提供了从零实现的 DPO（Direct Preference Optimization）训练；至于 RLHF（人类反馈强化学习，含 PPO、GRPO），书中并未展开——那是续作《Build A Reasoning Model (From Scratch)》的主战场。

## 附录与 Bonus 材料

附录覆盖了正文之外的进阶主题：

- **Appendix A：PyTorch 入门** — 面向不熟悉 PyTorch 的读者，讲张量操作与梯度计算，附多 GPU（DDP）训练脚本
- **Appendix B：参考文献与延伸阅读** — 每章对应的论文与资料清单
- **Appendix C：练习解答** — 全书练习的参考实现
- **Appendix D：为训练循环加料** — Gradient Clipping、Mixed Precision 训练、Early Stopping 等工程细节
- **Appendix E：LoRA 参数高效微调** — 只训练低秩分解的小矩阵，用少量参数微调大模型，是 PEFT（Parameter-Efficient Fine-Tuning，参数高效微调）的主流方法

更值得挖的是仓库里的 **Bonus 实验目录**——很多"书里没细讲但大家都会问"的话题都在这里：

- **注意力变体**：KV Cache、Grouped-Query Attention（GQA）、Multi-Head Latent Attention（MLA）、Sliding Window Attention、DeepSeek Sparse Attention、Cross-Layer KV Sharing
- **架构扩展**：Mixture-of-Experts（MoE），以及 Llama 3.2、Qwen3、Gemma 3、Olmo 3、Qwen3.5、Gemma 4 的从零实现
- **工程主题**：FLOPs 分析、内存友好的权重加载、扩展 tiktoken 分词器、PyTorch 训练提速
- **动手实践**：BPE 从零实现、给预训练模型加个聊天界面、把 GPT 架构转成 Llama

也就是说，读完正文只是开始——仓库把这些进阶方向的代码都给你备好了。

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

作者在 [setup/README.md](https://github.com/rasbt/LLMs-from-scratch/tree/main/setup) 中提供了更完整的环境配置建议，包括 Docker DevContainer 方案。遇到问题先翻根目录的 [troubleshooting.md](https://github.com/rasbt/LLMs-from-scratch/blob/main/troubleshooting.md)，Notebook 图片不显示、fork 后如何同步上游更新、Apple Silicon 上 MPS 后端的行为差异等常见问题都有说明。

## 为什么选择这个仓库

**优点：**

1. **零依赖外部 LLM 库**：所有 Transformer 实现都是手写的，代码量不大但逻辑清晰
2. **配套书籍，内容系统**：代码背后有整本教材支撑，学的是一条系统路径，无需自己拼凑零散片段
3. **Notebook + 脚本双版本**：适合边学边实验，也适合直接引用到项目里
4. **作者持续维护**：Issues 响应积极，代码跟随 PyTorch 与最新架构更新
5. **覆盖预训练 + 微调完整流程**：从海量文本到指令助手，模型每一步获得什么能力，都有一行行代码对应

**局限性：**

1. 教学优先于性能：训练规模小（124M 级别），工程化的吞吐优化不展开
2. 不包含量化、Flash Attention 等推理优化——这些属于续作与专门仓库的范围
3. 预训练数据集规模有限（个人 GPU 可承受的范围），模型能力以演示机制为主

## 适用场景

- **零基础入门 LLM 内部机制**：第一次学习 attention、transformer、GPT 架构的同学
- **有 PyTorch 基础，想深入理解 LLM**：用过 `transformers` 库但想搞清楚原理的工程师
- **高校/自学机器学习课程**：需要一套完整、可运行的 LLM 实验代码
- **面试准备**：LLM 架构、注意力机制、预训练/微调流程是 AI 方向面试的高频考点

## 自测清单

读完全文，用下面几个问题检验自己：

- [ ] 能用一句话说出预训练和微调的区别，以及为什么要先预训练再微调
- [ ] 能解释注意力分数为什么要除以 $\sqrt{d_k}$，不除会怎样
- [ ] 能画出 GPT 一个 Transformer Block 的数据流：输入 → LayerNorm → 多头注意力 → 残差相加 → LayerNorm → FFN → 残差相加
- [ ] 能说出分类微调与指令微调在"输出头"和"损失"上的差异
- [ ] 能按顺序说出这条学习路径的产物：分词器、注意力模块、GPT 模型、预训练权重、分类器、指令助手

答不上来的，回到对应小节再读一遍。

## 练习

动笔之前，先做三道热身题：

1. **改配置**：把 `GPT_CONFIG_124M` 换成 355M 配置（`n_layers=24`、`emb_dim=1024`、`n_heads=16`），数一数参数量是否约为原来的 3 倍
2. **画掩码**：手写一个 4×4 因果掩码矩阵，推演 `masked_fill` 之后 softmax 每一行哪些位置会归零
3. **读代码**：打开 `ch04/01_main-chapter-code/gpt.py`，找出 `TransformerBlock` 里残差连接的写法，比较它与经典 ResNet 的异同

## 进阶路径

按目标选下一站：

- **想接轨主流架构**：读 Ch 5 的 Bonus——Llama 3.2、Qwen3、Gemma 3、Olmo 3 等从零实现，看 GPT 骨架如何长出不同变体
- **想搞懂推理加速**：研究 Bonus 里的 KV Cache、GQA、MLA、Sliding Window Attention
- **想省显存微调**：做一遍 Appendix E 的 LoRA，对比它与全量微调的参数量与效果
- **想再进一步**：续作《Build A Reasoning Model (From Scratch)》讲推理模型，覆盖推理时缩放、强化学习（GRPO）、蒸馏
- **想回到工程实践**：回头读 `transformers` 库源码，对照书中手写实现，很多设计决策会豁然开朗

## 总结

LLMs-from-scratch 拆掉了大模型的黑箱：从文本表示、注意力计算、模型训练到指令微调，完整知识链条都有可运行的代码。模型本身不大，价值在另一个方向——以后再遇到 KV Cache、GQA 这些名词，你脑子里有对应的矩阵乘法。

如果你之前学 LLM 时跳过了"从零实现"这一步，建议找一个周末，按章节顺序把这个仓库的代码跑一遍。跑完再打开 PyTorch 的 `nn.MultiheadAttention` 文档，参数含义、掩码写法，一眼就能对上自己写过的代码。

> **配套书籍**：想配套阅读的，可以购买 Sebastian Raschka 的《Build a Large Language Model (From Scratch)》（Manning，ISBN 9781633437166）。不想买书的话，GitHub 上的代码和 README 本身已经是完整的教程。

---

**延伸阅读：**

- [Sebastian Raschka 博客](https://sebastianraschka.com/blog/)
- [LLMs-from-scratch 仓库](https://github.com/rasbt/LLMs-from-scratch)
- [17 小时配套视频课程](https://www.manning.com/livevideo/master-and-build-large-language-models)（逐章编码，可配合书使用）
- [Build A Reasoning Model (From Scratch)](https://mng.bz/lZ5B)（续作，讲推理模型）
- [transformers 库源码阅读](../transformers-huggingface-nlp-guide/)（学完这个仓库后推荐）
- [Flash Attention 原理详解](../flash-attention-fast-exact-attention-guide/)（注意力机制的工程优化方向）