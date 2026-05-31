---
title: "TrainLLMFromScratch: 从零训练你自己的大语言模型"
date: "2026-05-31T10:15:00+08:00"
slug: "fareedkhan-train-llm-from-scratch"
description: "TrainLLMFromScratch 是一个从零实现 Transformer 架构的 PyTorch 项目，支持百万到十亿参数级别的 LLM 训练。使用 Pile 数据集，单块 GPU 即可训练，提供完整的代码注释和一步步的详细讲解。"
draft: false
categories: ["技术笔记"]
tags: ["LLM训练", "PyTorch", "Transformer", "深度学习", "从零实现"]
---

很多人在学习大语言模型时，往往止步于"调用 API"或"Fine-tuning 预训练模型"，很少有人真正从零理解 Transformer 的每一行代码是怎么运转的。**TrainLLMFromScratch** 这个项目正是为解决这个痛点而生——它用纯 PyTorch 从零实现了一个完整的 Transformer 架构，支持从 1300 万参数到 20 亿参数的灵活配置，并提供了目前全网最详尽的代码逐行解读。

---

## 为什么这个项目值得研究

市面上的 LLM 教程大多分为两类：一类是过于抽象的论文解读，看完还是不知道代码怎么写；另一类是直接调用 HuggingFace 的 API，底层细节被完全封装。对于真正想掌握 LLM 核心原理的工程师来说，这两者之间存在巨大的鸿沟。

TrainLLMFromScratch 恰好填补了这个空白：

- **代码完整可运行**：从数据下载、预处理、模型定义到训练、推理，一条龙完整实现
- **参数规模灵活**：1300 万参数模型单卡可训练，20 亿参数模型需要 A100
- **讲解极为细致**：提供了 Medium 级别的逐行代码解析，连 MLP、Attention 这样基础模块都画了架构图
- **零门槛入门**：配套了 OOP、神经网络、PyTorch 的视频资源链接

---

## 项目核心架构

### Transformer 总体结构

项目实现的 Transformer 包含以下几个核心组件：

```
输入 Token → Token Embedding + Position Embedding
         → N 个 Transformer Block（每个 Block 包含）
         │   ├── LayerNorm
         │   ├── Multi-Head Attention
         │   ├── LayerNorm
         │   └── MLP（4x 扩展 + ReLU + 投影）
         → LayerNorm → Linear(vocab_size) → 输出
```

关键参数配置（以 13M 参数模型为例）：

| 参数 | 13M 模型 | 2B 模型 |
|------|---------|---------|
| VOCAB_SIZE | 50304 | 50304 |
| CONTEXT_LENGTH | 128 | 512 |
| N_EMBED | 128 | 2048 |
| N_HEAD | 8 | 16 |
| N_BLOCKS | 1 | 64 |

### Multi-Head Attention 实现

多头注意力机制是 Transformer 的核心。项目实现的单头 Attention 包含：
- Key/Query/Value 三个线性投影（无 bias）
- Scaled dot-product attention（缩放因子 `1/sqrt(head_size)`）
- Causal mask（因果掩码，防止看到未来 token）

```python
class Head(nn.Module):
    def __init__(self, head_size, n_embed, context_length):
        super().__init__()
        self.key = nn.Linear(n_embed, head_size, bias=False)
        self.query = nn.Linear(n_embed, head_size, bias=False)
        self.value = nn.Linear(n_embed, head_size, bias=False)
        self.register_buffer('tril', torch.tril(torch.ones(context_length, context_length)))
    
    def forward(self, x):
        B, T, C = x.shape
        k = self.key(x)
        q = self.query(x)
        scale_factor = 1 / math.sqrt(C)
        attn_weights = q @ k.transpose(-2, -1) * scale_factor
        attn_weights = attn_weights.masked_fill(self.tril[:T, :T] == 0, float('-inf'))
        attn_weights = F.softmax(attn_weights, dim=-1)
        v = self.value(x)
        out = attn_weights @ v
        return out
```

Multi-Head Attention 则将多个 Head 的输出拼接起来：

```python
class MultiHeadAttention(nn.Module):
    def __init__(self, n_head, n_embed, context_length):
        super().__init__()
        self.heads = nn.ModuleList([
            Head(n_embed // n_head, n_embed, context_length) 
            for _ in range(n_head)
        ])
    
    def forward(self, x):
        x = torch.cat([h(x) for h in self.heads], dim=-1)
        return x
```

### MLP 模块

MLP 采用 4 倍扩展因子（Transformer 论文标准做法）：

```python
class MLP(nn.Module):
    def __init__(self, n_embed):
        super().__init__()
        self.hidden = nn.Linear(n_embed, 4 * n_embed)
        self.relu = nn.ReLU()
        self.proj = nn.Linear(4 * n_embed, n_embed)
    
    def forward(self, x):
        x = self.relu(self.hidden(x))
        x = self.proj(x)
        return x
```

---

## 训练流程详解

### 数据准备：Pile 数据集

项目使用 [EleutherAI 的 Pile 数据集](https://huggingface.co/datasets/monology/pile-uncopyrighted)，这是一个 825GB 的多样化文本数据集，涵盖 PubMed、GitHub、ArXiv 等 22 个子数据集。数据以 JSONL + Zstandard 压缩格式存储，每行一个 JSON 对象：

```python
# 下载示例
!wget https://huggingface.co/datasets/monology/pile-uncopyrighted/resolve/main/train/00.jsonl.zst

# 解压读取
with zstd.open(in_file, 'r') as in_f:
    for line in in_f:
        data = json.loads(line)
        print(data['text'])  # 原始文本
```

### Tokenizer 选择

项目使用 OpenAI 的 `tiktoken`（r50k_base，与 GPT-2/GPT-3 相同）进行分词。每个文本末尾追加 `<|endoftext|>` 作为序列结束标记。

### 训练配置对照表

| GPU | 显存 | 适合训练规模 |
|-----|------|------------|
| NVIDIA A100 40GB | 40GB | ~6B-8B |
| NVIDIA RTX 4090 24GB | 24GB | ~4B |
| NVIDIA RTX 3090 24GB | 24GB | ~3.5B-4B |
| Tesla T4 / RTX 3080 | 16GB | ~1.5B-2B |
| Colab T4 | 16GB | ~1.5B-2B |
| RTX 3060 Ti | 8GB | ~1B |
| RTX 4050 | 6GB | ~750M |

建议**先训练 13M 参数模型**（一块普通游戏卡即可），确认流程跑通后，再按 GPU 显存比例放大到更大规模。

### 训练损失曲线对比

作者对比了 1B 参数和 13M 参数两个模型的训练损失曲线：

- **1B 模型**：初始损失高（~3.0），波动大，在学习率衰减后才趋于稳定，最终 loss ~0.23
- **13M 模型**：初始损失低，曲线平滑，几乎没有波动，训练更稳定

这个对比说明：规模越大的模型，对学习率调度、数据多样性的要求越高，不能简单地把小模型配置直接线性放大。

---

## 快速上手

### 环境安装

```bash
git clone https://github.com/FareedKhan-dev/train-llm-from-scratch.git
cd train-llm-from-scratch

# 推荐使用 uv 管理 Python 环境
uv python install 3.11
uv sync --frozen

# 或使用 pip
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 配置 PYTHONPATH

```bash
export PYTHONPATH="$PYTHONPATH:."
```

### 下载训练数据

```bash
python scripts/data_download.py
# 可选参数 --train_max 控制下载文件数量，默认 1 个（约 11GB）
```

### 预处理数据

```bash
python scripts/data_preprocess.py
# 默认将 Pile 数据集 tokenize 后存储为 HDF5 格式
```

### 配置模型参数

修改 `config/config.py`，以 13M 参数模型为例：

```python
VOCAB_SIZE = 50304
CONTEXT_LENGTH = 128
N_EMBED = 128
N_HEAD = 8
N_BLOCKS = 1
```

### 开始训练

```bash
python scripts/train_transformer.py
```

### 文本生成

```bash
python scripts/generate_text.py --model_path models/your_model.pth --input_text "hi"
# 可选 --max_new_tokens 控制生成长度
```

---

## 生成效果对比

| 模型规模 | 示例输出 |
|---------|---------|
| **13M 参数** | "In 1978, The park was returned to the factory-plate that the public share to the lower of the electronic fence that follow from the Station's cities. The Canal of ancient Western nations were confined to the city spot..." |
| **2B 参数** | "There are two miles east coast from 1037 and 73 million refugees (hypotetus) as the same men and defeated Harvard, and Croft. At right east and West Nile's Mediterranean Sea jets..." |

13M 参数模型已经能生成语法正确、拼写正确的句子；2B 参数模型输出更丰富但连贯性仍有限。这验证了作者的观点：**13M-1B 参数范围内，可以训出专精特定任务的实用模型**，不必一味追求超大参数。

---

## 项目设计哲学

这个项目最值得学习的地方，不是代码本身，而是作者的设计哲学：

> "I found that 13+ million-parameter models are enough to start making sense in terms of proper grammar and punctuation, which is a positive point. This means we can use a very specific dataset to further fine-tune our previously trained model for a narrowed task."

作者鼓励先训练一个 13M 参数的基础模型，再用特定领域数据微调到 500M-1B 参数规模，往往比直接从零训一个大模型效果好十倍。这种"小模型打基础 + 专精数据微调"的思路，对资源有限的个人开发者和独立研究者非常有参考价值。

---

如果你对 LLM 底层机制感兴趣，想真正从零掌握 Transformer 的每一步实现细节，这个项目是目前全网最完整、最可运行的参考资料。无论是面试备战、学术研究还是产品预研，都能从中获得实质性的提升。