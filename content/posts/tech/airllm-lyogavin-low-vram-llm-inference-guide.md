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

`AirLLM`（仓库 [lyogavin/airllm](https://github.com/lyogavin/airllm)）是少有的"**不靠量化蒸馏剪枝，4GB 单卡跑 70B**"的 LLM 推理库。它的核心思路简单粗暴——**把大模型拆成单层逐块加载**：平时只把当前正在计算的那一层参数读进显存，其它层都在 NVMe/SSD 上待机。

它的护城河在三件别家没做到的"硬功夫"：

1. **4GB VRAM 跑 70B**：不量化（保精度）、不蒸馏（保能力）、不剪枝（保通用性），纯靠"分时换入"
2. **8GB VRAM 跑 405B Llama3.1**：405B 级别是工业模型上限，AirLLM 把它从"8×H100"压到"8GB 单卡"
3. **块级量化（4bit/8bit）3x 加速**：自研 block-wise 量化只压权重、不压激活，磁盘加载瓶颈被一枪打掉

> 重要前提：AirLLM 不是"无损加速"——逐层换入意味着 **throughput 较低**（70B 跑 20 token 大约 4-6 秒）。它的定位是"**单卡 / 边缘设备能跑起来**"，而不是"高 QPS 服务"。

## 项目地图

| 维度 | 关键信息 |
|------|----------|
| 仓库 | [lyogavin/airllm](https://github.com/lyogavin/airllm) |
| PyPI | [pypi.org/project/airllm](https://pypi.org/project/airllm/) |
| 许可证 | Apache-2.0 |
| Stars | 19,070 / Forks 2,086 |
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

## 快速上手

### 安装

```bash
pip install airllm
```textbash
pip install -U bitsandbytes
```textpython
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
```textpython
from airllm import AutoModel

model = AutoModel.from_pretrained(
    "meta-llama/Meta-Llama-3.1-405B-Instruct",
    compression="4bit",  # 或 "8bit"
)
# ... 同上 tokenizer + generate
```textpython
model = AutoModel.from_pretrained(
    "garage-bAInd/Platypus2-70B-instruct",
    compression="4bit",  # 或 "8bit"
)
```textpython
model = AutoModel.from_pretrained(
    "garage-bAInd/Platypus2-70B-instruct",
    prefetching=True,  # 默认 True
)
```textpython
# Apple Silicon（M1/M2/M3/M4）原生支持
# 需要先装 mlx 和 torch
pip install mlx torch
```textbash
# 1. 4GB 显卡 + 256GB 磁盘（HF cache）
pip install airllm

# 2. 跑
python -c "
from airllm import AutoModel
m = AutoModel.from_pretrained('garage-bAInd/Platypus2-70B-instruct', compression='4bit')
"
# 第一次会下载 + 拆分模型（~1-2 小时）
# 之后每次启动直接用
```textpython
from airllm import AutoModel
m = AutoModel.from_pretrained("meta-llama/Meta-Llama-3-70B-Instruct", compression="4bit")
# ... Apple Silicon 走统一内存，4bit 后大约 35GB 占用
```textpython
# profiling_mode 打印每层耗时
model = AutoModel.from_pretrained(
    "...",
    profiling_mode=True,
    compression="4bit",
)
# 输出: layer 0: 0.3s, layer 1: 0.28s, ...
# 帮你定位 GPU 瓶颈 / IO 瓶颈
```texttext
safetensors_rust.SafetensorError: Error while deserializing header: MetadataIncompleteBuffer
```textpython
from airllm import AutoModel  # 不要用 AirLLMLlama2
m = AutoModel.from_pretrained("Qwen/Qwen-7B")
```textpython
m = AutoModel.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    hf_token="hf_xxx",
)
```textpython
input_tokens = model.tokenizer(
    input_text,
    return_tensors="pt",
    return_attention_mask=False,
    truncation=True,
    max_length=MAX_LENGTH,
    padding=False,  # 关掉 padding
)
```textbibtex
@software{airllm2023,
  author = {Gavin Li},
  title = {AirLLM: scaling large language models on low-end commodity computers},
  url = {https://github.com/lyogavin/airllm/},
  version = {0.0},
  year = {2023},
}
```

## 采用建议

### 适合谁

- 手里是 4-8GB 显存卡（M1/M2/M3、小型 RTX 3060/4060、Jetson Orin）但**想跑 70B/405B**
- 个人研究 / 论文实验 / 边缘 demo
- 想**保精度**地评估大模型（不量化、不蒸馏、不剪枝）

### 不适合谁

- 需要生产级 QPS（>10 req/s）——用 vLLM / TensorRT-LLM
- 已有 24GB+ 显卡（4090/A5000）——直接 `transformers.from_pretrained` 更简单
- 需要 batch > 1 —— 走 vLLM / SGLang

### 落地顺序

1. **先装先试**：`pip install airllm`，跑 Platypus2-70B 试手感
2. **再开 4bit 加速**：`compression="4bit"`，看提速幅度
3. **最后换 405B**：8GB 显存 + 4bit 跑 Meta-Llama-3.1-405B（如果磁盘扛得住）
4. **配合 `delete_original=True`**：磁盘紧张时只留 sharded 版本

## 一句话总结

> AirLLM 是当下"**低显存跑超大模型**"细分赛道的最优解——4GB 跑 70B、8GB 跑 405B、不量化保精度；代价是吞吐低、磁盘大、不适合生产。个人研究者和边缘部署的务实之选。

---

*📚 仓库地址：[lyogavin/airllm](https://github.com/lyogavin/airllm) · PyPI：[pypi.org/project/airllm](https://pypi.org/project/airllm/) · License：Apache-2.0 · 出品方：Gavin Li*
