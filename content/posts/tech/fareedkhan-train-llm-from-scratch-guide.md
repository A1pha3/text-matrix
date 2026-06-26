---
title: "TrainLLMFromScratch: 从零训练你自己的大语言模型"
date: "2026-05-31T10:15:00+08:00"
slug: "fareedkhan-train-llm-from-scratch"
description: "TrainLLMFromScratch 是一个从零实现 Transformer 架构的 PyTorch 项目，支持百万到十亿参数级别的 LLM 训练。使用 Pile 数据集，单块 GPU 即可训练，提供完整的代码注释和一步步的详细讲解。"
draft: false
categories: ["技术笔记"]
tags: ["LLM训练", "PyTorch", "Transformer", "深度学习", "从零实现"]
---

## 读完这篇文章你会知道

- 一套最小但完整的 Transformer 训练管线长什么样
- 从 13M 到 2B 参数，不同规模模型的代码差异在哪里
- 一次前向 + 反向传播在代码里实际流过哪些模块
- 你自己的 GPU 能训多大规模的模型，应该从哪一步开始

---

很多人在学大语言模型时，卡在一个尴尬的位置：论文看完了，但不知道代码怎么写；HuggingFace 的 `model.fit()` 跑通了，但不知道里面发生了什么。**TrainLLMFromScratch** 填的就是这个坑——纯 PyTorch、零外部封装，从 tokenizer 到 loss 反向传播，每一步都摊开给你看。

---

## 项目速览

| 字段 | 值 |
|------|-----|
| 仓库 | [FareedKhan-dev/train-llm-from-scratch](https://github.com/FareedKhan-dev/train-llm-from-scratch) |
| Stars | 7,454+ |
| Forks | 1,052+ |
| License | MIT |
| 主语言 | Python |
| 核心依赖 | PyTorch、tiktoken、HDF5 |
| 训练数据 | Pile 数据集（825 GB） |

---

## 系统总览

在进入细节之前，先把整条管线看清楚。下图是一次完整训练的数据流：

```mermaid
flowchart LR
    A[Pile 原始文本] --> B[tiktoken 分词]
    B --> C[HDF5 存储 token 序列]
    C --> D[DataLoader 采样 batch]
    D --> E[Token Embedding + Position Embedding]
    E --> F[N× Transformer Block]
    F --> G[Final LayerNorm]
    G --> H[Linear → logits]
    H --> I[CrossEntropyLoss]
    I --> J[反向传播 + AdamW 更新]
```

两条主线要分开理解：

| 主线 | 职责 | 关键模块 |
|------|------|----------|
| **数据管线** | 原始文本 → token → batch | `data_download.py` → `data_preprocess.py` → `DataLoader` |
| **模型管线** | token → embedding → attention → logits → loss | `Transformer` → `Block` → `MultiHeadAttention` + `MLP` |

下面先拆模型管线，再讲数据管线，最后用一次具体的训练步骤把两条线串起来。

---

## 项目核心架构

### Transformer 总体结构

项目实现的 Transformer 包含以下核心组件：

```
输入 Token → Token Embedding + Position Embedding
         → N 个 Transformer Block（每个 Block 包含）
         │   ├── LayerNorm
         │   ├── Multi-Head Attention
         │   ├── LayerNorm
         │   └── MLP（4x 扩展 + ReLU + 投影）
         → LayerNorm → Linear(vocab_size) → 输出
```

关键参数配置（13M vs 2B）：

| 参数 | 13M 模型 | 2B 模型 |
|------|---------|---------|
| VOCAB_SIZE | 50304 | 50304 |
| CONTEXT_LENGTH | 128 | 512 |
| N_EMBED | 128 | 2048 |
| N_HEAD | 8 | 16 |
| N_BLOCKS | 1 | 64 |

注意看 N_BLOCKS：13M 模型只有 **1 个** Transformer Block，2B 模型有 **64 个**。参数量的差距主要来自 embedding 维度（128 → 2048）和层数（1 → 64），而非词表或 head 数。

### Multi-Head Attention 实现

多头注意力是 Transformer 的核心。项目实现的单头 Attention 包含：

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

> **注意**：代码中 `scale_factor = 1 / math.sqrt(C)` 取的是 `n_embed` 而非 `head_size`，这与原论文 `1/sqrt(d_k)` 略有出入。此处 `C` 来自 `x.shape[-1]`，即输入维度 `n_embed`。实际运行中不影响收敛，但如果你要严格复现论文精度，建议改成 `1 / math.sqrt(head_size)`。

Multi-Head Attention 将多个 Head 的输出拼接：

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

为什么是 4 倍？原论文的设计选择：扩展 → 激活 → 投影，中间的 4x 扩展给了 FFN 足够的容量来学习 token 间的非线性关系，同时保证输入输出维度一致，方便残差连接。

---

## 一次训练步骤如何流过系统

把上面的模块拼起来，看一个具体的 `(B=1, T=128)` 的 batch 怎么流过整个模型：

```text
1. DataLoader 给出一个 batch: shape (1, 128)，每行是 token id
2. Token Embedding: (1, 128) → (1, 128, 128)   # 查表得到 128 维向量
3. Position Embedding: (1, 128) → (1, 128, 128) # 位置编码
4. 逐元素相加: x = tok_emb + pos_emb → (1, 128, 128)
5. 进入唯一的 Transformer Block（13M 模型只有 1 个）:
   a. LayerNorm → (1, 128, 128)
   b. MultiHeadAttention: 8 个头各算自己的 QKV，每个头输出 (1, 128, 16)，拼接回 (1, 128, 128)
   c. 残差连接: x = x + attn_out
   d. LayerNorm → (1, 128, 128)
   e. MLP: (1, 128, 128) → (1, 128, 512) → ReLU → (1, 128, 128)
   f. 残差连接: x = x + mlp_out
6. Final LayerNorm → (1, 128, 128)
7. Linear(vocab_size=50304) → (1, 128, 50304)  # 每个位置预测下一个 token 的概率
8. CrossEntropyLoss: 拿最后一个维度和标签 token 算 loss
9. loss.backward() → 梯度沿原路回传
10. optimizer.step() → AdamW 更新所有参数
```

这 10 步就是一次完整的训练迭代。13M 模型因为只有 1 个 Block，所以第 5 步只跑一次；2B 模型会把第 5 步循环 64 次。

---

## 训练流程详解

### 数据准备：Pile 数据集

项目使用 [EleutherAI 的 Pile 数据集](https://huggingface.co/datasets/monology/pile-uncopyrighted)，825 GB，涵盖 PubMed、GitHub、ArXiv 等 22 个子集。数据以 JSONL + Zstandard 压缩格式存储：

```python
# 下载示例
!wget https://huggingface.co/datasets/monology/pile-uncopyrighted/resolve/main/train/00.jsonl.zst

# 解压读取
with zstd.open(in_file, 'r') as in_f:
    for line in in_f:
        data = json.loads(line)
        print(data['text'])  # 原始文本
```

数据预处理后存为 HDF5 格式，比原始 JSONL 读取快一个数量级——这对训练吞吐量影响很大。

### Tokenizer 选择

使用 OpenAI 的 `tiktoken`（`r50k_base` 编码，与 GPT-2/GPT-3 相同）。每个文本末尾追加 `<|endoftext|>` 作为序列结束标记。选择 `r50k_base` 而非更新的 `cl100k_base` 的原因很简单：词表更小（50257 vs 100256），13M 模型撑不起太大的 embedding 矩阵。

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

先训 13M 参数模型跑通流程，确认没问题后再按显存比例放大。13M 模型在一块 RTX 3060 上就能跑，不需要云 GPU。

### 训练损失曲线说明了什么

项目作者对比了 1B 和 13M 两个模型的 loss 曲线：

| 观察 | 1B 模型 | 13M 模型 |
|------|---------|----------|
| 初始 loss | ~3.0，很高 | 较低 |
| 波动幅度 | 大，学习率衰减后才稳定 | 平滑，几乎无波动 |
| 最终 loss | ~0.23 | 更高但稳定 |

**这组对比测的是什么**：两个模型在同一份 Pile 数据上的训练 loss 下降曲线，反映的是模型容量与优化难度的关系。

**数字说明了什么**：1B 模型的低最终 loss 代表更强的建模能力，但代价是训练不稳定、对学习率调度敏感。13M 模型的训练过程几乎"不需要调参"，但 loss 下不去——容量不够。

**不能推出什么**：不能根据 loss 曲线直接断言"1B 模型生成质量一定更好"。loss 衡量的是下一个 token 的预测准确度，不代表生成文本的连贯性、事实正确性或实用性。另外，loss 曲线没到平台期不代表模型没学到东西——小模型可能在 loss 还很高时就已经学到了语法和拼写。

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

几个观察：

1. 13M 模型已经能生成语法正确、拼写正确的句子——这验证了作者的核心观点：**1300 万参数就足以学会英语的基本语法结构**。
2. 2B 模型输出更长、词汇更丰富，但连贯性仍然有限——规模变大不等于自动变"聪明"，数据质量和训练策略同样重要。
3. 两个模型都没有生成有意义的语义内容，因为它们是在 Pile 的随机切片上从头训练的，没有经过指令微调或 RLHF（基于人类反馈的强化学习）。

---

## 适用边界与采用建议

这个项目不是让你训出一个 ChatGPT 竞品。它的真实价值在于：

**适合你，如果你**：

- 正在学习 Transformer，需要一套干净、可单步调试的参考实现
- 想在自己的领域数据上从头训一个小模型（比如法律文书、医学报告）
- 准备面试或教学，需要能逐行解释的代码

**不适合你，如果**：

- 你需要一个可以直接部署的生产级模型——去找 LLaMA、Mistral 的微调版
- 你没有 GPU——13M 模型 CPU 也能跑但会很慢
- 你想要 SOTA 效果——这个项目的目标是"可理解"，不是"最强"

**推荐采用顺序**：

1. 克隆仓库，用 13M 配置跑通完整管线（数据下载 → 预处理 → 训练 → 生成）
2. 把 `N_BLOCKS=1` 改成 `N_BLOCKS=2`，观察参数量和训练时间的变化
3. 换成自己的文本数据（几百 MB 就够了），看模型能不能学到领域特有的词汇和句式
4. 如果你有 ≥24GB 显存的 GPU，尝试 500M-1B 参数配置

作者的原话很务实：

> "I found that 13+ million-parameter models are enough to start making sense in terms of proper grammar and punctuation. This means we can use a very specific dataset to further fine-tune our previously trained model for a narrowed task."

小模型打基础 + 专精数据微调，这条路对资源有限的独立开发者来说，比租 8 张 A100 从零训大模型实际得多。

---

## 常见问题

**Q: 13M 参数模型真的能学到东西吗？**

能。13M 参数足以学会英语的基本语法、拼写和标点。作者实验表明，13M 模型在 Pile 数据上训练后生成的句子语法基本正确。但语义理解和事实知识需要更大容量，13M 模型做不到。

**Q: 我的 GPU 只有 8GB 显存，能跑吗？**

能。用默认的 13M 配置（`N_EMBED=128`, `N_BLOCKS=1`），8GB 显存绰绰有余。把 `CONTEXT_LENGTH` 保持在 128 以内即可。如果要放大模型，按上文的 GPU 对照表来。

**Q: 数据下载太慢了，能用自己的数据吗？**

可以。预处理脚本接受 JSONL 格式的文本文件。把你自己的文本按行写成 JSONL（每行 `{"text": "你的内容"}`），替换 `data_download.py` 的输出路径就行。注意数据量：13M 模型几百 MB 文本就够，不需要 825GB。

**Q: 训练时 loss 不下降怎么办？**

先检查学习率（默认配置是可行的），然后确认数据预处理没问题（token 序列长度是否合理，特殊 token 是否正确添加）。如果还是不行，降低 `CONTEXT_LENGTH` 到 64，减少 `N_BLOCKS` 到 1，用最小配置先跑通。

**Q: 这个项目的代码和 GPT-2 有什么区别？**

核心架构几乎一样——Pre-Norm Transformer + GELU/ReLU 激活。主要区别在规模：GPT-2 Small 有 124M 参数、12 层，这个项目的 13M 版本只有 1 层。另外项目使用 ReLU 而非 GELU，去掉了 Dropout，简化了训练流程。

---

## 自测：检查你的理解

读完这篇文章和项目代码后，尝试回答以下问题：

1. 13M 模型的 `N_EMBED=128`，`N_HEAD=8`，每个 Head 的维度是多少？这个维度在代码的哪个位置起作用？
2. 为什么 Causal Mask 使用的是 `torch.tril`（下三角矩阵）？如果不加这个 mask，会发生什么？
3. MLP 的 4x 扩展因子如果改成 2x 或 8x，分别会对模型容量和训练速度造成什么影响？
4. 你有一块 RTX 3090（24GB），想训练一个中等规模的模型。参考文中的 GPU 对照表，你最大能训多少参数的模型？实际训练时应该先训多大的？
5. 训练 loss 从 3.0 降到 0.23 意味着什么？能直接说"模型变聪明了"吗？

这些问题不需要标准答案——它们是为了帮你确认自己是否真正理解了 Transformer 训练管线，而不是只看懂了表层的 API 调用。

---

## 延伸阅读

- **代码层面**：读完这个项目后，可以去看 [nanoGPT](https://github.com/karpathy/nanoGPT)（Andrej Karpathy 的极简 GPT 实现），对比两者的设计取舍
- **理论层面**：原论文 [Attention Is All You Need](https://arxiv.org/abs/1706.03762) + [The Annotated Transformer](http://nlp.seas.harvard.edu/annotated-transformer/) 逐行讲解
- **数据层面**：了解 [Pile 数据集论文](https://arxiv.org/abs/2101.00027)，理解训练数据构成如何影响模型行为
- **扩展开源**：看看 [TinyLlama](https://github.com/jzhang38/TinyLlama)（1.1B 参数，在 3T token 上训练），体会"小模型 + 大数据"路线的效果

---

## 进阶路径

**阶段 1：跑通 13M 模型（1-2 天）**

按文章「快速上手」节的步骤，用默认配置跑通完整管线。重点不是模型效果，而是确认数据流和模型管线都理解清楚了。训练时观察 loss 曲线——13M 模型的 loss 应该平滑下降，几乎无波动。

**阶段 2：改动一个超参数观察影响（3-7 天）**

把 `N_BLOCKS=1` 改成 `N_BLOCKS=2`，或者把 `CONTEXT_LENGTH=128` 改成 `CONTEXT_LENGTH=256`。重新训练，观察：
- 参数量增加了多少？
- 训练时间增加了多少？
- loss 曲线有什么变化？

这个练习能帮你建立「模型规模 ↔ 训练资源 ↔ 效果」的直觉。

**阶段 3：换成自己的数据（1-2 周）**

找几百 MB 你熟悉的领域的文本（比如代码、法律文档、医学论文），按文章「常见问题 Q3」的方法预处理。观察模型能不能学到领域特有的词汇和句式。

**阶段 4：放大到 500M-1B 参数（需要 ≥24GB 显存）**

如果你有 RTX 3090 或更好的 GPU，尝试 `N_EMBED=1024`, `N_HEAD=16`, `N_BLOCKS=24` 这个配置（约 500M 参数）。这个阶段你会遇到「显存不够」和「训练不稳定」两个新问题——解决它们的过程，就是真正理解 Transformer 训练的时候。

---