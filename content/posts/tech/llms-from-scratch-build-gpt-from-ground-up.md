---
title: "LLMs-from-Scratch 完全指南：跟着 Sebastian Raschka 从零手写一个 GPT（约 10.6 万 Star）"
date: "2026-05-14T12:46:00+08:00"
lastmod: "2026-09-30T00:00:00+08:00"
slug: "llms-from-scratch-build-gpt-from-ground-up"
github_repo: "rasbt/LLMs-from-scratch"
source_key: "gh:rasbt/LLMs-from-scratch"
description: "LLMs-from-scratch（rasbt/LLMs-from-scratch，约 10.6 万 Star）是 Sebastian Raschka 所著《Build a Large Language Model (From Scratch)》的官方配套代码仓库，按 7 章主代码加 5 个附录组织，另带大量跟进前沿的 bonus 材料。本文梳理其章节结构、环境搭建、可运行的代码路径与学习方式。"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "GPT", "深度学习", "Python", "PyTorch", "Transformer"]
---

## 学习目标

读完本文，你应该能：

- 说出这本书 7 章主代码的内容主线，判断它和你已有知识的衔接关系
- 在自己的笔记本上装好环境，跑通 ch02 到 ch04 的主代码
- 指出注意力、因果掩码、位置嵌入在 `GPTModel` 代码里各自的位置，并说清它们为什么缺一不可
- 用 `GPT_CONFIG_124M` 这份配置起步训练和采样，知道"124M"这个数字怎么来的
- 知道 bonus 材料覆盖了什么（KV cache、Qwen3 权重加载、LoRA、DPO），什么时候该翻它们
- 判断什么时候该从这本书转向 Raschka 的续作或其他进阶资源

## 阅读导航

- 想直接开始写代码 → 看 `§3 环境搭建` 和 `§5 实践`
- 想先弄明白"为什么要从零构建" → 看 `§1`
- 想搞清楚注意力机制到底在算什么 → 看 `§4.2`
- 想知道这本书适不适合自己 → 看 `§6`

---

## §1 为什么要「从零构建」

大多数开发者使用 LLM 的方式是调 API：发一段 messages，收一段回答。这条路能完成工作，但当输出不符合预期时，你能动的只有 prompt——模型内部发生了什么，摸不到。

Sebastian Raschka 的《Build a Large Language Model (From Scratch)》（Manning 出版，2024 年 9 月发行，ISBN 978-1633437166）给出的路径是把模型亲手写一遍：词元化、注意力、Transformer 块、预训练循环、分类微调、指令微调，全部用 PyTorch 逐行实现，不借助任何现成的 LLM 库。配套代码仓库 [rasbt/LLMs-from-scratch](https://github.com/rasbt/LLMs-from-scratch) 按章节组织了全部 notebook 和脚本，目前约 10.6 万 Star（105,773，2026-09-30 快照）。

写它不是为了训练出一个能和 GPT 竞争的模型——那需要数亿美元的计算资源。它回答的问题更基础：注意力矩阵里的每个数字是怎么算出来的？因果掩码加在哪一步？位置信息从哪里进入模型？这些问题，调 API 永远回答不了。

| 学习路径 | 代表资源 | 适合人群 | 局限 |
|---------|---------|---------|------|
| 只用 API | OpenAI / Anthropic 文档 | 应用开发者 | 无法理解内部机制 |
| 读论文 | Attention Is All You Need 等 | 研究者 | 数学门槛高，缺实现细节 |
| **从零构建（本书）** | **LLMs-from-scratch** | 想理解内部的工程师 | 需要基础 Python 和深度学习知识 |
| 直接读工业源码 | HuggingFace transformers | 高级开发者 | 工程封装重，学习曲线陡 |

## §2 仓库概览

### 2.1 数据快照

| 维度 | 数据 |
|------|------|
| 仓库 | [rasbt/LLMs-from-scratch](https://github.com/rasbt/LLMs-from-scratch) |
| Stars / Forks | 105,773 / 16,234（2026-09-30 快照） |
| 最近推送 | 2026-09-22 |
| 代码许可证 | Apache-2.0（书稿版权归 Manning） |
| Python 要求 | >=3.10，<3.15（`pyproject.toml`） |
| 出版配套 | Manning《Build a Large Language Model (From Scratch)》，2024-09-12 发行 |

### 2.2 章节结构

仓库按书的 7 章主代码加 5 个附录组织，每个目录下有 `README.md`、主 notebook 和练习答案：

| 目录 | 主题 |
|------|------|
| `ch01/` | Understanding Large Language Models（导论，无代码，附阅读建议） |
| `ch02/` | Working with Text Data（词元化与数据加载） |
| `ch03/` | Coding Attention Mechanisms（从简到繁写注意力） |
| `ch04/` | Implementing a GPT Model from Scratch（组装 GPT 架构） |
| `ch05/` | Pretraining on Unlabeled Data（预训练循环与权重加载） |
| `ch06/` | Finetuning for Classification（垃圾短信分类微调） |
| `ch07/` | Finetuning to Follow Instructions（指令微调） |
| `appendix-A/` | Introduction to PyTorch（PyTorch 速成） |
| `appendix-B/` | References and Further Reading |
| `appendix-C/` | Exercise Solutions（练习答案） |
| `appendix-D/` | Adding Bells and Whistles to the Training Loop |
| `appendix-E/` | Parameter-efficient Finetuning with LoRA |

内容主线是一条完整的流水线：文本 → 词元（ch02）→ 注意力（ch03）→ GPT 模型（ch04）→ 预训练（ch05）→ 分类微调（ch06）→ 指令微调（ch07）。前四章从零搭建，后三章在搭好的模型上做下游任务。

### 2.3 bonus 材料是这个仓库的第二生命

如果只看主章节，你会错过这个仓库近两年最活跃的部分。各章的 bonus 子目录持续跟进 2025—2026 年的前沿实践，目录名一目了然：

- **ch04 架构扩展**：KV cache、GQA（分组查询注意力）、MLA（DeepSeek 多头潜在注意力）、SWA（滑动窗口注意力）、MoE（混合专家）、DeltaNet、KV sharing——把书里的基础 GPT 逐一改造成现代架构变体。
- **ch05 训练与权重**：学习率调度器、超参调优、Gutenberg 语料真实预训练、把 GPT-2 权重转换加载到 LLaMA / Qwen3 / Gemma3 / OLMo3 / Qwen3.5 / Gemma4、Muon 优化器、CPU 与 MPS 设备差异分析。
- **ch07 对齐**：DPO 偏好微调、数据集生成与模型评估。
- **appendix-E**：LoRA 参数高效微调。

另一个值得注意的细节：仓库根目录挂着 `reasoning-from-scratch` 子模块，指向 Raschka 续作《Build a Reasoning Model (From Scratch)》的配套仓库。读完本书想继续深入推理模型，顺着它走即可。

## §3 环境搭建

### 3.1 安装

```bash
git clone https://github.com/rasbt/LLMs-from-scratch.git
cd LLMs-from-scratch

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

核心依赖：`torch>=2.2.2`、`jupyterlab>=4.0`、`tiktoken>=0.5.1`、`matplotlib`、`numpy`、`pandas`。ch05 到 ch07 还需要 `tensorflow>=2.18`——不是用来训练，而是因为 ch05 的 `gpt_download.py` 要下载 OpenAI 官方的 GPT-2 预训练权重，那是 TensorFlow checkpoint 格式。

仓库的 `setup/README.md` 还提供了几条替代路径：用 `uv` 一行装齐依赖、Docker DevContainer、Google Colab（可白嫖 GPU，跑 ch05 预训练时有用）。

### 3.2 硬件与系统要求

官方 README 的原话是：主章节代码为"常规笔记本在合理时间内运行"设计，不需要专用硬件；检测到 GPU 会自动使用。预训练（ch05）和两个微调章节在 GPU 上明显更快，但没有 GPU 也走得完。

一个容易想错的点：本书训练用的语料很小（见 `§5.1`），显存压力远小于你训练自己的模型。别按"训练 LLM"想象硬件门槛。

### 3.3 验证安装

进入 `ch04/01_main-chapter-code/` 目录（各章代码按同目录 import 设计，仓库的单元测试也是这么跑的），加载完整模型：

```python
import torch
from gpt import GPTModel, GPT_CONFIG_124M

model = GPTModel(GPT_CONFIG_124M)
total_params = sum(p.numel() for p in model.parameters())
print(f"PyTorch 版本: {torch.__version__}")
print(f"参数量: {total_params:,}")   # 约 163M——权重未绑定时的数字
```

能打印出参数量，环境就通了。顺便你会撞见书里一个著名的"意外"：配置名叫 124M，未做权重绑定的参数量却是 1.63 亿左右——`out_head` 输出层与词嵌入层共用权重（weight tying）之后，才是 1.24 亿。这个数字游戏在 ch04 里有完整交代。

### 3.4 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| `ModuleNotFoundError` | 从错误的目录运行 | 在项目根目录运行，或设置 `PYTHONPATH` |
| 下载 GPT-2 权重失败 | 网络问题 | ch05 的 `gpt_download.py` 需能访问 OpenAI 的存储桶；也可参考 bonus 里的替代权重源 |
| CUDA out of memory | 显存不足 | 减小 `batch_size` 和 `context_length`，或改用 CPU / Colab |

## §4 核心概念：书里的四个关键设计

### 4.1 词元化：模型只认整数

LLM 不处理文字，处理整数。词元化器（tokenizer）把文本转成整数序列，每个整数对应词表里的一个词元。本书用的是 OpenAI 的 tiktoken 库和 GPT-2 的 BPE 词表（50,257 个词元）。

BPE（Byte Pair Encoding）的思路：从字符级词表开始，反复把最高频的相邻对合并成新词元。跑下来常见词（"the"、"is"、完整的 "hello"）各占一个词元，罕见词被切成多个子词。仓库 `ch04/01_main-chapter-code/tests.py` 里有一个现成的编码示例：

```python
import tiktoken

tokenizer = tiktoken.get_encoding("gpt2")
print(tokenizer.encode("Hello, I am"))  # [15496, 11, 314, 716]——4 个词元
```

这是两个极端之间的折中——按词切，词表太大、罕见词训练不足；按字符切，序列太长、长距离依赖难学。

### 4.2 注意力与因果掩码

在注意力出现之前，RNN、LSTM 这类模型逐词元处理序列，把前面所有信息压进一个固定大小的隐藏状态。两个问题随之而来：固定向量装不下长句子的全部信息（信息瓶颈），句首的信息在多步传递中逐渐衰减。注意力让序列中每个位置直接看到所有其他位置，绕过中间状态。

自注意力本身是一次加权求和。对每个词元：拿它的 Query 向量和所有词元的 Key 向量算相似度，softmax 归一化成权重，再用权重对 Value 向量求和：

```text
Attention(Q, K, V) = softmax(QK^T / √d_k) × V
```

除以 √d_k 是为了防止点积随维度增大而过大，把 softmax 推进梯度极小的饱和区。Q、K、V 三个投影矩阵在 ch03 从简到繁写了四个版本，最终形态是 `ch04/01_main-chapter-code/gpt.py` 里的 `MultiHeadAttention(d_in, d_out, context_length, dropout, num_heads, qkv_bias=False)`。

因果掩码（causal mask）解决自回归的顺序问题：GPT 生成第 t 个词时不能看到第 t+1 个之后的词。实现上，`MultiHeadAttention` 用一行代码注册一个上三角掩码缓冲区：

```python
self.register_buffer("mask", torch.triu(torch.ones(context_length, context_length), diagonal=1))
```

前向计算时，注意力分数矩阵里被掩码盖住的位置（对角线右上部分）被置为 `-inf`，softmax 之后这些位置的权重精确为 0——每个词元只"看得见"自己和前文。掩码矩阵以 buffer 形式常驻，跟随模型移动到 GPU，不参与梯度。

### 4.3 位置嵌入：顺序信息的唯一入口

注意力有个数学特性：把输入序列的顺序打乱，输出跟着同样打乱，但每个词元的"感受"不变——它天然不知道谁在前谁在后。而语言的顺序就是语义（"狗咬人"和"人咬狗"），所以必须把位置信息显式喂进去。

本书的做法是 GPT-2 同款的可学习绝对位置嵌入：再建一张 `nn.Embedding(context_length, emb_dim)` 位置表，词元嵌入加上对应位置的位置嵌入，一起进入模型（`gpt.py` 里 `GPTModel.__init__` 的 `tok_emb` 和 `pos_emb` 两行）。这是全书实际实现并使用的位置编码方案。

至于 RoPE（旋转位置编码）这类相对位置方案，本书正文没有实现。它出自 RoFormer 论文（Su et al., 2021），如今是主流 LLM 的标配——如果你读本书是为了给读现代模型源码打底，记住这个差异即可，ch04 的架构 bonus（MLA、SWA 等）可以作为对照现代设计的切入点。

### 4.4 Transformer 块：组装

一个 GPT 的 Transformer 块由两个子层堆成：

```text
输入
  ↓
LayerNorm → Multi-Head Attention → 残差连接
  ↓
LayerNorm → Feed-Forward → 残差连接
  ↓
输出
```

三个设计各有用意：

- **残差连接**给梯度开一条直通路，缓解深层网络的梯度消失；
- **LayerNorm 放在子层之前**（Pre-LN，GPT-2 起的惯例）让训练更稳，块末尾还有一个 `final_norm` 收尾；
- **前馈网络**先升维 4 倍再降回来，中间夹 GELU 激活，对每个位置独立做非线性变换。

`ch04` 把 `TransformerBlock` 重复 `n_layers` 次（124M 配置下 12 次），加上词元/位置嵌入和输出层，就是完整的 `GPTModel`。

## §5 实践：训练与采样

### 5.1 数据：小到故意的语料

书里预训练用的语料是《The Verdict》，一篇约 20 KB 的公有领域短篇小说（`ch02/01_main-chapter-code/the-verdict.txt`）。选这么小不是偷懒——2 万词的文本让笔记本几分钟就能跑完一个预训练循环，把流程走通。代价也要清楚：在这个语料上训练出的模型只会背课文，成不了对话模型。这正是理解"真实预训练为什么需要海量语料"的最短入口：流程一模一样，量的差距就是能力的差距。

数据加载在 ch02 完成（函数在 ch02 的 notebook 中逐行实现，`ch04/01_main-chapter-code/gpt.py` 里收录了同一实现，可直接复用）：

```python
from gpt import create_dataloader_v1  # ch04/01_main-chapter-code/gpt.py

with open("the-verdict.txt", "r", encoding="utf-8") as f:
    raw_text = f.read()

train_loader = create_dataloader_v1(
    raw_text,
    batch_size=4,
    max_length=256,   # 每个样本 256 个词元
    stride=128,       # 滑动窗口步长，窗口之间留一半重叠
    shuffle=True
)
```

`stride` 小于 `max_length` 意味着相邻样本共享一半文本——小语料下这是凑够训练样本的现实手段，同时也带来训练样本之间的相关性（书里讨论了这个取舍）。

### 5.2 模型配置

书里反复使用这份"小型 GPT-2"配置，键名以 `ch04/01_main-chapter-code/gpt.py` 为准：

```python
GPT_CONFIG_124M = {
    "vocab_size": 50257,     # GPT-2 词表大小
    "context_length": 1024,  # 最大序列长度
    "emb_dim": 768,          # 嵌入维度
    "n_heads": 12,           # 注意力头数
    "n_layers": 12,          # Transformer 块数
    "drop_rate": 0.1,        # dropout 比例
    "qkv_bias": False        # QKV 投影是否加偏置
}
```

这组超参数逐项对应 GPT-2 small（124M）。`qkv_bias=False` 是与原始 GPT-2 的一个差异——实践中关掉偏置不损性能还省参数，书里专门解释过。

### 5.3 训练

训练循环就是标准 PyTorch 五步：前向、算交叉熵损失、`optimizer.zero_grad()`、`loss.backward()`、`optimizer.step()`。完整可运行的实现在 `ch05/01_main-chapter-code/gpt_train.py`，配套 notebook 里有训练曲线和损失解读。appendix-D 进一步补齐真实训练的常规配置：学习率预热、余弦退火、梯度裁剪。

### 5.4 生成文本

书里有两个生成函数，建议分清用途：

```python
# ch04/01_main-chapter-code/gpt.py：最简贪心解码，理解自回归循环用
from gpt import generate_text_simple
# generate_text_simple(model, idx, max_new_tokens, context_size)

# ch05/01_main-chapter-code/previous_chapters.py：带温度采样与 top-k
from previous_chapters import generate
# generate(model, idx, max_new_tokens, context_size,
#          temperature=0.0, top_k=None, eos_id=None)
```

`generate_text_simple` 每步取 logits 的 argmax，输出确定；`generate` 把最后一个位置的 logits 除以温度再采样，`temperature=0.0` 时退回贪心，`top_k` 则把采样范围限制在最可能的 k 个词元内。两个函数都维护一个不断增长的 `idx` 张量，每轮把新词元拼到序列尾部——自回归的全部含义就在这个循环里。

## §6 适用读者与学习路径

### 6.1 谁该读

- **有 Python 基础、天天调 LLM API 的工程师**：最直接的目标读者。API 用得越顺手，越值得补上内部机制这一课。
- **深度学习研究者**：把熟悉的公式落到逐行代码，能检验理解的成色。
- **想转进 LLM 领域的后端/系统工程师**：Python 和 PyTorch 基础够用，配合 appendix-A 入门即可上手。

**不适合**：只想快速搭一个 LLM 应用的人（直接用 HuggingFace 或 API 更快）；对 Transformer 已经很熟、想追最新架构的人（直接读论文和现代模型源码更有效率，本书的现代扩展在 bonus 里也只是入口）。

### 6.2 三遍读法

**第一遍，跑通**（1–2 周）：不纠结细节，把 ch02 到 ch07 的主 notebook 依次跑完，看着损失下降、模型吐出第一批"像话"的文本。先建立全局感。

**第二遍，搞懂为什么**（2–4 周）：回到每个组件问一句为什么——BPE 为什么比按词切好？因果掩码不加会怎样（可以真去掉试试）？`qkv_bias` 关掉的依据是什么？这一遍的重点是 §4 的四个设计。

**第三遍，动手改**（持续）：换语料重新预训练；把 `emb_dim`、`n_layers` 调大观察显存和损失变化；照着 ch04 的 bonus 给自己的模型加 KV cache；用 appendix-E 的 LoRA 在小显存上微调。

### 6.3 常见陷阱

| 陷阱 | 表现 | 规避 |
|------|------|------|
| 跳过 ch02 直接搭模型 | 词元化、数据流水线一知半解 | ch02 是全书地基，别跳 |
| 一上来就用大配置 | OOM，笔记本风扇起飞 | 用 `GPT_CONFIG_124M` 起步，确认跑通再放大 |
| 期望小语料训练出对话能力 | 模型只会复读训练文本 | 认清 The Verdict 只是流程演示，能力来自数据规模 |
| 分不清两个 generate | 想要多样输出却用了贪心版 | 采样实验用 ch05 的 `generate` |

## §7 自测练习

1. **词元化观察**：用 tiktoken 的 `gpt2` 编码分别对 "artificial intelligence" 和 "AI" 编码，比较词元数，并解释差异与 BPE 合并策略的关系。
2. **掩码消融**：把 `MultiHeadAttention` 里的掩码去掉（或全部置 0），在 The Verdict 上继续训练，观察生成文本发生了什么。
3. **配置实验**：保持数据不变，分别用 `n_layers` 为 2、6、12 的配置训练，比较训练损失曲线和过拟合出现的时机。
4. **权重迁移**：照着 ch05 的 bonus，把下载的 GPT-2 权重加载进自己写的 `GPTModel`，对比加载前后的生成质量——这是检验你的实现是否正确的最硬标准。

---

## 参考资源

- 原书：Sebastian Raschka, *Build a Large Language Model (From Scratch)*, Manning, 2024（ISBN 978-1633437166）
- 代码仓库：[github.com/rasbt/LLMs-from-scratch](https://github.com/rasbt/LLMs-from-scratch)
- 续作配套：[rasbt/reasoning-from-scratch](https://github.com/rasbt/reasoning-from-scratch)（《Build a Reasoning Model (From Scratch)》）
- Karpathy 视频：["Let's build GPT: from scratch, in code, spelled out"](https://www.youtube.com/watch?v=kCc8FmEb1nY)，与本书 ch02–ch04 路线相近，可互补观看
- 交互式 Transformer 可视化：[Transformer Explainer](https://poloclub.github.io/transformer-explainer/)

## 资料口径说明

1. **数据来源**：Stars、Forks、最近推送时间取自 GitHub API（快照时间 2026-09-30）；章节结构、目录名、代码签名、配置键名逐一对照 `main` 分支源码（`ch04/01_main-chapter-code/gpt.py`、`ch05/01_main-chapter-code/previous_chapters.py`、`requirements.txt`、`pyproject.toml`、`setup/README.md`、根 `README.md`）；出版信息取自仓库 `CITATION.cff`。
2. **版本锚点**：Python 要求 `>=3.10,<3.15`；核心依赖 `torch>=2.2.2`、`tiktoken>=0.5.1`；ch05–ch07 需要 `tensorflow>=2.18`（GPT-2 权重下载用）。
3. **代码示例**：正文代码引用的模块路径与函数签名均为仓库实证；标注"示意"的片段请以对应章节 notebook 为准。
4. **更新状态**：bonus 材料目录持续新增（快照前最近一次推送为 2026-09-22），以仓库实况为准。
