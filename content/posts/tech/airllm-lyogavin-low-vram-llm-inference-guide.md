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
```

如果要用量化加速：

```bash
pip install -U bitsandbytes
```

### 4 行代码跑 70B

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

> 第一次跑会**自动分层拆分模型**并落盘——请确保 HF cache 目录磁盘足够（70B ≈ 140GB）。

### 405B Llama3.1（8GB 单卡 + 4bit）

```python
from airllm import AutoModel

model = AutoModel.from_pretrained(
    "meta-llama/Meta-Llama-3.1-405B-Instruct",
    compression="4bit",  # 或 "8bit"
)
# ... 同上 tokenizer + generate
```

## 核心机制

### 1. 分层加载（Layer-wise Loading）

AirLLM 不把整个模型一次性塞进显存。流程是：

1. 把模型按 transformer block 拆成 N 份 sharded checkpoint
2. 推理时**只在算到第 i 层时**，把第 i 层从 NVMe/SSD 读进 GPU 显存
3. 算完第 i 层、**算第 i+1 层之前**，释放第 i 层
4. KV cache 跨层常驻显存（这一段是省不掉的）

> 这是为什么"4GB 跑 70B"可能——**单层 70B / 80 ≈ 1.7GB 权重 + 1GB KV cache = 2.7GB，4GB 显存够用**。

### 2. 块级量化（Block-wise Quantization）

来自 [arXiv:2212.09720](https://arxiv.org/abs/2212.09720) 的 block-wise 量化是 AirLLM 2.0 引入的杀手锏。

```python
model = AutoModel.from_pretrained(
    "garage-bAInd/Platypus2-70B-instruct",
    compression="4bit",  # 或 "8bit"
)
```

**与普通量化的关键区别**：

| 方案 | 量化范围 | 推理加速 | 精度损失 | 适配难度 |
|------|----------|----------|----------|----------|
| 标准 INT8/INT4 量化 | 权重 + 激活 | 高 | 中-高（outlier 敏感） | 高（需要 calib） |
| **AirLLM 块级量化** | **只压权重** | 中（**3x 加速磁盘加载**） | 低 | **零**（calibration-free） |

> 设计哲学：瓶颈是**磁盘加载**不是计算，所以只压缩权重就能拿到 3x 加速；不动激活，outlier 不破坏精度。

### 3. 预取（Prefetching）

```python
model = AutoModel.from_pretrained(
    "garage-bAInd/Platypus2-70B-instruct",
    prefetching=True,  # 默认 True
)
```

把"加载第 i+1 层"和"算第 i 层"做**流水线 overlap**——大约 10% 速度提升。

### 4. MacOS / Apple Silicon 支持

```python
# Apple Silicon（M1/M2/M3/M4）原生支持
# 需要先装 mlx 和 torch
pip install mlx torch
```

详见 [run_on_macos.ipynb](https://github.com/lyogavin/airllm/blob/main/air_llm/examples/run_on_macos.ipynb)。

## 配置选项速查

| 参数 | 用途 | 默认值 |
|------|------|--------|
| `compression` | `"4bit"` / `"8bit"` / `None` | `None` |
| `profiling_mode` | 打印每层耗时 | `False` |
| `layer_shards_saving_path` | 拆分后模型保存路径 | HF cache |
| `hf_token` | 拉 gated model 用 | – |
| `prefetching` | 加载-计算流水线 | `True` |
| `delete_original` | 拆分后删原模型，**省一半磁盘** | `False` |

> `delete_original=True` 是磁盘紧张时的救命稻草——HF 下载后会被删除，只保留拆分版本（省 ~50% 磁盘）。

## 性能直觉

| 场景 | 硬件 | 大致吞吐 | 备注 |
|------|------|----------|------|
| 70B Llama2 / Llama3 | 4GB 单卡 | ~4-6 s / 20 token | 逐层换入是瓶颈 |
| 70B + 4bit | 4GB 单卡 | ~1.5-2 s / 20 token | 块级量化打掉磁盘瓶颈 |
| 405B Llama3.1 + 4bit | 8GB 单卡 | ~10-15 s / 20 token | 405B 体量在那儿 |
| 70B Mac M-series | 32GB 统一内存 | 类似单卡 | Apple Silicon 适合个人开发者 |
| 70B CPU only | 多核 x86 | 极慢 | 临时方案，**不推荐** |

> **不要拿 AirLLM 当生产 inference server**——它的设计目标是"能跑起来"而不是"高 QPS"。

## 典型场景

### 场景 A：个人开发者本地试 70B

```bash
# 1. 4GB 显卡 + 256GB 磁盘（HF cache）
pip install airllm

# 2. 跑
python -c "
from airllm import AutoModel
m = AutoModel.from_pretrained('garage-bAInd/Platypus2-70B-instruct', compression='4bit')
"
# 第一次会下载 + 拆分模型（~1-2 小时）
# 之后每次启动直接用
```

### 场景 B：MacBook M3 试 Llama3

```python
from airllm import AutoModel
m = AutoModel.from_pretrained("meta-llama/Meta-Llama-3-70B-Instruct", compression="4bit")
# ... Apple Silicon 走统一内存，4bit 后大约 35GB 占用
```

### 场景 C：边缘 / 嵌入式部署

把 70B + 4bit 量化后的 sharded checkpoint 烧进 Jetson Orin（32GB 共享内存），配合 `prefetching=True` 可以在边缘设备跑出"能对话"的体验。

### 场景 D：研究 / 评测

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

## 边界与盲点

- **吞吐低**：逐层换入 70B 一次生成 20 token 要 4-6 秒，**不适合实时聊天**
- **磁盘占用大**：70B 拆分后 ~140GB，405B 拆分后 ~800GB
- **不支持 batch > 1**：分层加载假设了 batch=1
- **KV cache 不能卸载**：超长 context + 大模型会爆显存
- **MacOS 只支持 Apple Silicon**：Intel Mac 不能用
- **量化不压激活**：和 vLLM / TensorRT-LLM 比，**纯计算加速** 不可比

## 与同类的对比

| 工具 | 核心思路 | 4GB 跑 70B | 吞吐 | 易用性 | 适用场景 |
|------|----------|------------|------|--------|----------|
| **AirLLM** | 分层换入 + 块级量化 | ✅ | 低 | 高（一行代码） | 边缘/个人/研究 |
| vLLM | PagedAttention + 连续 batching | ❌（要全模型） | **极高** | 中 | 生产服务 |
| TensorRT-LLM | 编译优化 + 量化 | ❌ | **极高** | 低 | NVIDIA 生产 |
| llama.cpp | GGUF 量化 + CPU/GPU 混合 | ✅（需 GGUF） | 中 | 中 | 跨平台 |
| Ollama | llama.cpp 包装 | ✅ | 中 | **极高** | 本地对话 |
| SGLang | RadixAttention + 结构化生成 | ❌ | **极高** | 中 | 高 QPS 服务 |

> AirLLM 的真正位置是"**4GB-8GB 显存跑超大模型**"这个细分生态——llama.cpp / Ollama 适合 13B 以下，vLLM / TensorRT-LLM 适合生产服务，AirLLM 适合"我的卡小但我想跑 70B/405B"。

## 常见问题（FAQ）

### 1. `MetadataIncompleteBuffer`

```text
safetensors_rust.SafetensorError: Error while deserializing header: MetadataIncompleteBuffer
```

**磁盘满了**。拆模型非常吃盘，需要 `du -sh ~/.cache/huggingface` 检查，扩容后删 cache 重跑。

### 2. `ValueError: max() arg is an empty sequence`

你可能用 `AirLLMLlama2` 加载了 QWen / ChatGLM。**统一用 `AutoModel`**：

```python
from airllm import AutoModel  # 不要用 AirLLMLlama2
m = AutoModel.from_pretrained("Qwen/Qwen-7B")
```

### 3. `401 Client Error: ... is gated`

部分模型是 gated（meta-llama/Llama-2 等），需要 HF token：

```python
m = AutoModel.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    hf_token="hf_xxx",
)
```

### 4. `ValueError: Asking to pad but the tokenizer does not have a padding token`

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

## 引用

```bibtex
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
