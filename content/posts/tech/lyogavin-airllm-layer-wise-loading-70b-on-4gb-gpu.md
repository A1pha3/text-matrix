---
title: "AirLLM：用层式分片加载在 4GB 显卡跑 70B 模型是怎么做到的"
date: 2026-07-20T03:02:36+08:00
categories: ["技术笔记"]
tags: ["llm-inference", "low-vram", "layer-wise", "70b-model", "airllm"]
description: "AirLLM 用层式分片加载 + 按需 swap 的方式让 70B 模型在单卡 4GB 显存上跑，不做量化、不蒸馏、不剪枝。本文拆它的 layer-wise loading 机制、3x 量化加速路径和适用边界。"
---

# AirLLM：用层式分片加载在 4GB 显卡跑 70B 模型是怎么做到的

## 一句话判断

AirLLM 的核心承诺很硬核：**70B 模型在单卡 4GB GPU 上跑**——不需要量化、不蒸馏、不剪枝。23.5K stars 说明这个承诺击中了"我有 4GB 老显卡但想跑 70B 模型"这个广泛痛点。它的实现方式是**层式分片加载**（layer-wise loading）+ 按需 swap，让模型参数从磁盘到内存到显存按层流动，而不是一次性全部加载到 GPU。

## 项目定位

- **仓库**：`lyogavin/airllm`，Apache-2.0 协议
- **GitHub Stars**：23.6K，Forks 2.7K（2026-07-16 数据）
- **核心能力**：低显存 LLM 推理，支持 4GB / 8GB / 12GB 显存跑 70B / 405B / 671B 模型
- **模型范围**：
  - 4GB GPU：跑 70B 模型
  - 8GB GPU：跑 405B Llama 3.1
  - ~12GB：跑 DeepSeek-V3 671B
- **作者**：Gavin Li（BELLE 团队）
- **PyPI**：[`airllm`](https://pypi.org/project/airllm/)

## 系统地图

| 模块 | 责任 |
|------|------|
| Layer-wise Loader | 把模型按 transformer layer 分片，按需加载到 GPU |
| Disk Cache | 第一次运行时把模型按 layer 分片保存到磁盘 |
| Inference Engine | 执行 layer-by-layer 的前向计算 |
| Optional Quantization | Block-wise quantization，3x 推理加速 |
| MacOS Backend | Metal / MPS 后端 |

## 关键机制拆解

### 1. Layer-wise Loading 的核心思想

传统 LLM 推理一次性把整个模型加载到 GPU 显存——70B 模型需要 ~140GB 显存（FP16），普通 GPU 跑不动。AirLLM 改成**按 layer 加载**：

```python
from airllm import AutoModel

# 一行代码，4GB 显存跑 70B
model = AutoModel.from_pretrained("Qwen/Qwen3-32B")

input_tokens = model.tokenizer(input_text, return_tensors="pt", ...)
generation_output = model.generate(
    input_tokens['input_ids'].cuda(), 
    max_new_tokens=20,
    use_cache=True,
    return_dict_in_generate=True
)
```

按 layer 加载的代价是**速度慢**——每次只能算一层 transformer block，需要 swap in / out。但对显存极小的卡（4GB）来说，这是**唯一可行**的路径。

### 2. Disk 分片缓存

第一次跑 `AutoModel.from_pretrained` 时，AirLLM 会：

1. 从 HuggingFace Hub 下载模型
2. 按 transformer layer 切分
3. 保存到 `layer_shards_saving_path`（默认 huggingface cache 目录）
4. 后续推理直接读 cache，不再下载

这意味着首次运行需要"下载 + 分片"两步（耗时较长），之后每次推理直接从 cache 加载 layer shard。

### 3. 3x 推理加速：Block-wise Quantization

README 给出的第二条核心能力：

> We just added model compression based on block-wise quantization-based model compression. Which can further **speed up the inference speed** for up to **3x**, with **almost ignorable accuracy loss!**

Block-wise quantization 是基于 [arXiv:2212.09720](https://arxiv.org/abs/2212.09720) 的方法：

- **传统 per-tensor quantization**：整张 tensor 共享一个量化参数，精度损失大
- **Block-wise quantization**：把 tensor 分成小块，每块单独量化，精度损失小

3x 加速来自更激进的量化（更低位宽）+ 几乎可忽略的精度损失。这让 4GB 显卡 + block-wise quantization 的组合在"70B 模型推理"场景下从"能跑"升级到"能用"。

### 4. 显存 vs 速度的权衡

AirLLM 的代价是速度：4GB 显卡跑 70B 模型，每个 token 需要 ~20-50 次 layer swap，比全 GPU 慢 50-100 倍。这意味着 AirLLM **不适合实时对话**，但适合：

- **离线 batch 处理**：几十个 prompt 一起算，最后统一返回
- **个人开发者实验**：跑一下看看模型输出，不要求毫秒级延迟
- **研究 / 教学**：让学生用笔记本显卡跑前沿模型

### 5. MacOS 支持

README 提到 "Run on MacOS" 是单独章节，意味着 Apple Silicon（M1/M2/M3）走 Metal 后端，可以用统一内存架构（UMA）替代 layer-wise swap——因为 Mac 的统一内存可达 32-128GB，70B 模型能直接放进 UMA。这让 AirLLM 在 Mac 上比 PC 4GB 显卡表现好得多。

## 适用人群

- **4GB 老显卡用户**：M6000 / P4 / 早期消费级卡
- **笔记本开发者**：MacBook Air / 集成显卡笔记本
- **学习 / 实验场景**：跑一下前沿模型但不需要生产吞吐
- **离线 batch 任务**：每天跑几十个 prompt 的 ETL 场景
- **研究 layer-wise 推理的学者**：代码简单清晰，是好的研究起点

## 不适合谁

- **需要实时对话的人**：速度太慢（每个 token 20-50 次 swap）
- **生产环境高 QPS（Queries Per Second，每秒查询数）服务**：AirLLM 设计就是低 QPS / 高参数
- **显存充足的用户**：有 24GB+ 显存直接用 vLLM / SGLang / TensorRT-LLM
- **想要 KV cache 优化的人**：layer-wise 模式下 KV cache 管理复杂，AirLLM 这块还在演进

## 仓库地址

https://github.com/lyogavin/airllm

## 阅读路径建议

1. `pip install airllm`，确认 Python 环境
2. 跑 README 的最小 demo，确认 layer-wise loading 在你的机器上能工作
3. 试一下 block-wise quantization，看 3x 加速是否复现
4. 如果在 Mac 上跑，读 "Run on MacOS" 章节，看 Metal 后端的配置