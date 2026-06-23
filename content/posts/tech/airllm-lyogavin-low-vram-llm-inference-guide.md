---
title: "AirLLM 完全指南：4GB 显存跑 70B 模型，单 GPU 玩转大模型推理"
date: "2026-06-04T15:00:00+08:00"
slug: airllm-lyogavin-low-vram-llm-inference-guide
description: "AirLLM 是 lyogavin 开源的 LLM 推理优化库，4GB 单卡跑 70B 模型、8GB 跑 405B Llama3.1，无需量化蒸馏剪枝；本文解析其分层加载 + 块级量化加速原理与上手姿势。"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "推理优化", "PyTorch", "低显存", "量化", "MacOS"]
---

# AirLLM 完全指南：4GB 显存跑 70B 模型，单 GPU 玩转大模型推理

## 核心判断

`AirLLM`（仓库 [lyogavin/airllm](https://github.com/lyogavin/airllm)）解决的是一个被多数推理库放弃的问题：**在 4-8GB 显存的消费级硬件上，跑起 70B 甚至 405B 参数的原始权重模型**。它走的是"分时换入"这条路——平时只把当前正在计算的那一层参数读进显存，其它层在 NVMe/SSD 上待机，算完即弃，下一层顶上。

这条路换来了三件别家没同时做到的事：

1. **4GB VRAM 跑 70B**：不量化、不蒸馏、不剪枝，权重保持原始 fp16/bf16 精度
2. **8GB VRAM 跑 405B Llama3.1**：405B 级别原本要 8×H100，AirLLM 把它压到单卡 8GB
3. **块级量化（4bit/8bit）3x 加速**：自研 block-wise 量化只压权重、不压激活，把磁盘 IO 这个主要瓶颈缩短到原来的三分之一

代价同样明确。逐层换入意味着每生成一个 token 都要把全部层从磁盘读一遍，**吞吐很低**（社区报告 70B 模型 20 token 大约 4-6 秒，数据为 2024 年中用户反馈，未在官方 benchmark 中复测）。AirLLM 的定位是"单卡 / 边缘设备能跑起来"，对应个人研究、论文复现、边缘 demo 这类对延迟不敏感、对显存极度敏感的场景；高 QPS 服务请直接走 vLLM / TensorRT-LLM。

下文先给项目地图和版本里程碑，再拆解分层加载、块级量化、预取三条机制的边界，用一个 70B 推理的完整任务流把机制串起来，然后解读性能数字的测量范围，最后给上手示例、常见问题和采用决策。

## 项目地图

| 维度 | 关键信息 |
|------|----------|
| 仓库 | [lyogavin/airllm](https://github.com/lyogavin/airllm) |
| PyPI | [pypi.org/project/airllm](https://pypi.org/project/airllm/) |
| 许可证 | Apache-2.0 |
| Stars / Forks | 19,070 / 2,086（截至 2024-08，数据来自 GitHub 仓库页） |
| 支持模型 | Llama / Llama2 / Llama3 / Llama3.1（含 405B）/ QWen / ChatGLM / Baichuan / Mistral / InternLM / Mixtral |

### 版本里程碑

| 时间 | 事件 |
|------|------|
| 2023-11 | AirLLM 初始版本 |
| 2023-12 | v2.0：safetensors 支持、块级量化 3x 加速 |
| 2023-12 | ChatGLM / QWen / Baichuan / Mistral / InternLM 全支持 |
| 2023-12 | v2.6：`AutoModel` 自动识别模型类型 |
| 2023-12 | v2.7：Mixtral 支持 |
| 2023-12 | v2.8.2：macOS 跑 70B |
| 2024-04 | Llama3 70B 在 4GB 单卡原生支持 |
| 2024-07 | Llama3.1 405B 在 8GB VRAM + 8bit/4bit 量化 |
| 2024-08 | v2.10：CPU 推理支持 |
| 2024-08 | v2.11：Qwen2.5 支持 |

## 工作原理：三条并行机制如何配合

AirLLM 的低显存能力来自三条相互独立、可以单独开关的机制。理解它们的边界，才能判断该不该开、开哪条、开了换什么。

### 分层加载：用时间换显存

大模型推理的本质是逐层矩阵乘法。第 N 层的输出是第 N+1 层的输入，任意时刻只有一层的权重真正参与计算。AirLLM 利用这一点，把整个模型按层切分成 shard 文件存放在磁盘上，推理时只把当前层读进显存，算完立即释放，再读下一层。

这样做的代价是显存占用从"全部权重"降到"单层权重 + KV cache + 激活"。70B 模型 fp16 全量约 140GB，单层 transformer block 权重约 1.4GB（80 层 × 688M 参数/层 × 2 字节），加上 KV cache 和中间激活，4GB 显存仍能容纳。代价是每生成一个 token，都要把全部 80 层从磁盘读一遍，IO 成为吞吐瓶颈。

为什么这条路在 70B 上可行、在 7B 上反而没必要？因为 7B 模型全量 fp16 只有 14GB，24GB 显卡能整体装下，走标准 `transformers` 推理比逐层换入快一个数量级。分层加载的价值随模型规模放大——模型越大，全量装载越不现实，逐层换入的相对代价越可接受。

### 块级量化：用精度换磁盘带宽

分层加载的瓶颈在磁盘 IO 一侧，计算端通常有余。块级量化（block-wise quantization）针对的就是这个瓶颈：把权重从 fp16 压到 4bit 或 8bit，磁盘读取量直接减半或减到四分之一，IO 时间相应缩短。

AirLLM 的块级量化有两个设计选择值得注意：

- **只压权重，不压激活**。激活值在推理时动态产生，量化会引入误差累积；权重是静态的，可以离线量化好存盘。这种不对称让精度损失主要来自权重 round-to-nearest，可控且可预测。
- **按 block 量化，不是按 tensor 量化**。把权重张量切成小块（block），每块独立计算 scale 和 zero point。相比全 tensor 量化，block 量化能更好适应权重数值分布的局部差异，精度损失更小。

官方报告 4bit 量化带来约 3x 加速。这个数字主要反映 IO 时间缩短——磁盘读取量降到四分之一，加上反量化开销，净加速约 3 倍。它不反映计算加速，因为反量化后实际计算仍在 fp16/bf16 进行。

### 预取：用线程换延迟

分层加载的朴素实现是串行的：读层 N → 计算 → 释放 → 读层 N+1 → 计算。预取（prefetching）用一个后台线程，在层 N 计算的同时把层 N+1 的权重读进显存，计算和 IO 重叠。

预取默认开启（`prefetching=True`）。它有效的前提是计算时间和 IO 时间可比——如果计算极快（小 batch、短序列），预取线程来不及读完下一层，加速有限；如果 IO 极快（NVMe RAID、内存盘），预取本身就成了多余开销。在 70B + 4bit + NVMe 的典型配置下，预取能再省 20-30% 单 token 时间。

### 三条机制的边界对照

| 机制 | 换什么 | 主要瓶颈 | 何时开 |
|------|--------|----------|--------|
| 分层加载 | 用时间换显存 | 磁盘 IO 带宽 | 默认开，无法关 |
| 块级量化 | 用精度换 IO 带宽 | 反量化计算开销 | 磁盘是瓶颈时开 |
| 预取 | 用线程换延迟 | 后台线程调度 | 计算和 IO 可比时开 |

三条机制作用在流水线的不同阶段：分层加载决定显存上限，块级量化决定 IO 时间，预取决定 IO 与计算的重叠程度。它们可以独立调参，但效果上限受最弱一环制约——开了 4bit 量化后若磁盘仍是瓶颈，预取收益就有限。

## 一次推理如何流过系统

以 70B 模型生成 20 个 token 为例，假设 4bit 量化 + 预取开启，跟踪一次完整推理的流程：

1. **模型加载阶段**（首次启动，约 1-2 小时）：`AutoModel.from_pretrained` 下载原始权重，按层切分成 shard 文件写入 HF cache 目录。70B 4bit 量化后磁盘占用约 35GB。
2. **prompt 编码**：tokenizer 把输入文本转成 token ids，放进显存的 KV cache 槽位。这一步在 GPU 上完成，不涉及权重读取。
3. **第一个 token 生成（prefill 阶段）**：
   - 主线程读取 layer 0 权重到显存，计算 attention + FFN，输出传给 layer 1
   - 后台预取线程同时读取 layer 1 权重
   - layer 0 计算完毕，释放显存，主线程拿预取好的 layer 1 开始计算
   - 后台预取线程转去读 layer 2
   - 如此推进 80 层，最后一层输出经 lm_head 得到第一个 token
4. **后续 token 生成（decode 阶段）**：每个新 token 都要重走一遍 80 层，区别是 KV cache 已经存了历史 token 的 K/V，attention 计算量随序列长度增长。每个 token 都触发一次完整的 80 层磁盘读取。
5. **20 个 token 完成**：总耗时约 4-6 秒（社区报告值），其中 IO 占大头，计算占比随序列长度上升。

这个流程里有一个反直觉的细节：**生成长序列时，AirLLM 的单 token 延迟会随序列变长而上升**，因为 attention 计算量在增长，而 IO 时间基本恒定。这与 vLLM 等 batch 推理引擎的行为相反——后者主要受 batch 大小影响。

## 性能特征：数字在测什么

社区报告的"70B 4-6 秒 / 20 token"主要测的是**单请求 decode 阶段的端到端延迟**，包含磁盘 IO + 计算 + 反量化开销。它反映的是 AirLLM 在消费级硬件（NVMe + 4-8GB 显卡）上的典型表现。

从这些数字里能推出什么：

- AirLLM 适合交互式或离线场景，单次生成几十到几百 token 可接受
- 4bit 量化相对 fp16 的精度损失在多数生成任务上不显著（weight-only 量化的 perplexity 上升通常在个位数百分比，具体数值因模型和量化方案而异）

从这些数字里**不能**推出什么：

- 不能推出 batch 推理性能。AirLLM 的设计不支持 batch > 1 的高效推理，因为每层都要为 batch 中每个样本读权重，IO 放大严重
- 不能推出与 vLLM 的直接对比。vLLM 测的是吞吐（token/s over batch），AirLLM 测的是单请求延迟，两者不在同一坐标轴
- 不能推出生产可用性。4-6 秒 / 20 token 折合约 3-5 token/s，远低于生产级 chat 服务的延迟要求

## 快速上手

### 安装

```bash
pip install airllm
```

如果要用 4bit/8bit 量化加速，还需要 bitsandbytes：

```bash
pip install -U bitsandbytes
```

### 基础推理

```python
from airllm import AutoModel

MAX_LENGTH = 128
model = AutoModel.from_pretrained("garage-bAInd/Platypus2-70B-instruct")

input_text = ["What is the capital of United States?"]
input_tokens = model.tokenizer(
    input_text,
    return_tensors="pt",
    return_attention_mask=False,
    truncation=True,
    max_length=MAX_LENGTH,
    padding=False,
)

generation_output = model.generate(
    input_tokens["input_ids"].cuda(),
    max_new_tokens=20,
    use_cache=True,
    return_dict_in_generate=True,
)
print(model.tokenizer.decode(generation_output.sequences[0]))
```

### 启用量化加速

4bit 量化把磁盘 IO 降到四分之一，是 70B 以上模型必备选项：

```python
from airllm import AutoModel

model = AutoModel.from_pretrained(
    "garage-bAInd/Platypus2-70B-instruct",
    compression="4bit",  # 或 "8bit"
)
# ... 同上 tokenizer + generate
```

405B 模型必须配合量化使用，8GB 显存才能装下：

```python
model = AutoModel.from_pretrained(
    "meta-llama/Meta-Llama-3.1-405B-Instruct",
    compression="4bit",  # 或 "8bit"
)
```

### 预取调优

预取默认开启。显存极紧张时可以关掉，省下预取缓冲区的显存，代价是单 token 延迟上升约 20-30%：

```python
model = AutoModel.from_pretrained(
    "garage-bAInd/Platypus2-70B-instruct",
    prefetching=True,  # 默认 True
)
```

### macOS / Apple Silicon

Apple Silicon（M1/M2/M3/M4）走统一内存架构，4bit 量化后 70B 模型约 35GB 占用，需要 64GB 以上内存的机型。先装 mlx 和 torch：

```bash
pip install mlx torch
```

```python
from airllm import AutoModel
m = AutoModel.from_pretrained("meta-llama/Meta-Llama-3-70B-Instruct", compression="4bit")
# ... Apple Silicon 走统一内存，4bit 后大约 35GB 占用
```

### profiling 定位瓶颈

不确定瓶颈在 IO 还是计算时，开 `profiling_mode` 打印每层耗时：

```python
# profiling_mode 打印每层耗时
model = AutoModel.from_pretrained(
    "...",
    profiling_mode=True,
    compression="4bit",
)
# 输出: layer 0: 0.3s, layer 1: 0.28s, ...
# 帮你定位 GPU 瓶颈 / IO 瓶颈
```

如果各层耗时均匀且都接近磁盘读取时间，瓶颈在 IO，开 4bit 量化或换更快的 NVMe；如果某些层耗时明显偏高，瓶颈在计算，考虑换更大显存的卡或减小序列长度。

## 常见问题

### safetensors 反序列化错误

首次运行报错：

```text
safetensors_rust.SafetensorError: Error while deserializing header: MetadataIncompleteBuffer
```

通常是模型下载不完整或 shard 文件损坏。删除 HF cache 目录下对应模型文件夹，重新运行 `from_pretrained` 触发完整下载。

### 不要直接用 AirLLMLlama2

旧版 API `AirLLMLlama2` 已废弃，新版统一走 `AutoModel` 自动识别模型类型：

```python
from airllm import AutoModel  # 不要用 AirLLMLlama2
m = AutoModel.from_pretrained("Qwen/Qwen-7B")
```

### HuggingFace gated 模型鉴权

Llama 系列需要 HF token，在 `from_pretrained` 里传入：

```python
m = AutoModel.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    hf_token="hf_xxx",
)
```

### batch 推理 OOM 或极慢

AirLLM 设计上不支持 batch > 1 的高效推理。每层都要为 batch 中每个样本读权重，IO 放大严重。需要 batch 推理走 vLLM / SGLang。

### 关掉 padding 避免 OOM

单样本推理时显存仍紧张，检查 tokenizer 是否开了 padding：

```python
input_tokens = model.tokenizer(
    input_text,
    return_tensors="pt",
    return_attention_mask=False,
    truncation=True,
    max_length=MAX_LENGTH,
    padding=False,  # 关掉 padding
)
```

## 采用建议

### 适合谁

- 手里是 4-8GB 显存卡（M1/M2/M3、小型 RTX 3060/4060、Jetson Orin），想跑 70B/405B 做研究或 demo
- 个人研究 / 论文实验 / 边缘 demo，对延迟不敏感
- 想保精度评估大模型——不量化、不蒸馏、不剪枝的 fp16 路径在 AirLLM 里是一等公民

### 不适合谁

- 需要生产级 QPS（>10 req/s）：用 vLLM / TensorRT-LLM
- 已有 24GB+ 显卡（4090/A5000）：直接 `transformers.from_pretrained` 更快，AirLLM 的逐层换入反而是负担
- 需要 batch > 1：走 vLLM / SGLang，AirLLM 的 IO 放大会让 batch 收益归零

### 落地顺序

1. **先装先试**：`pip install airllm`，跑 Platypus2-70B 试手感，确认环境通
2. **再开 4bit 加速**：`compression="4bit"`，对比提速幅度，确认磁盘能跟上
3. **最后换 405B**：8GB 显存 + 4bit 跑 Meta-Llama-3.1-405B，确认磁盘空间足够（约 200GB）
4. **磁盘紧张时配合 `delete_original=True`**：只留 sharded 版本，删掉原始权重

## 结尾判断

AirLLM 在"低显存跑超大模型"这个细分场景里没有真正的竞品。它的价值不在快，在于让原本需要 8×H100 的 405B 模型能在一张 8GB 显卡上跑起来——哪怕慢到 3-5 token/s。这个能力对个人研究者和边缘部署有意义，对生产服务无意义。

判断该不该用 AirLLM，看两个问题：你的显存是否装不下目标模型的全量权重？你能否接受单 token 秒级延迟？两个答案都是"是"，AirLLM 是当前唯一选择；任何一个是否定的，都有更好的方案。

---

*📚 仓库地址：[lyogavin/airllm](https://github.com/lyogavin/airllm) · PyPI：[pypi.org/project/airllm](https://pypi.org/project/airllm/) · License：Apache-2.0 · 出品方：Gavin Li*

```bibtex
@software{airllm2023,
  author = {Gavin Li},
  title = {AirLLM: scaling large language models on low-end commodity computers},
  url = {https://github.com/lyogavin/airllm/},
  version = {0.0},
  year = {2023},
}
```
