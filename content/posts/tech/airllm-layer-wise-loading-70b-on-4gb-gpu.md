---
title: "AirLLM 技术拆解：单张 4GB GPU 如何跑 70B 大模型"
date: "2026-07-19T03:10:00+08:00"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "显存优化", "推理优化", "低资源"]
description: "AirLLM 通过逐层加载策略，让 70B 参数大模型在单张 4GB 显存 GPU 上完成推理，无需量化或剪枝；v3.0 后支持 FP8 与 MoE 模型，2026 年 9 月起还能在小显存上流式微调千亿级模型。本文拆解其核心原理、压缩加速机制与适用边界。"
slug: airllm-layer-wise-loading-70b-on-4gb-gpu
github_repo: "lyogavin/airllm"
source_key: "gh:lyogavin/airllm"
---

## 核心判断

AirLLM 不把模型"塞进"显存，而是让模型"流过"显存。70B 参数按 Transformer 层切分后存放在磁盘，推理时只加载当前计算层进 GPU，算完丢弃，再加载下一层。GPU 只需容纳单层参数——这是 4GB 显存跑 70B 的根本原因，也是它与 vLLM、TGI、TensorRT-LLM 等"整模型驻留"路线的本质分歧。

代价同样明确：层间磁盘 I/O 和加载开销显著拉高首字延迟并限制吞吐。AirLLM 适合显存受限但对延迟容忍度高的场景——离线批处理、研究复现、个人开发者跑大模型——不适合在线实时对话。

## 问题背景：大模型推理的显存墙

大模型推理的显存占用由四部分组成：

1. **模型权重**：FP16 下每参数 2 字节，70B 模型约 140GB
2. **KV Cache**：推理时为避免重复计算注意力键值而缓存的中间状态，随上下文长度线性增长
3. **激活值**：前向计算过程中的中间张量，受 batch size 与序列长度影响
4. **运行时开销**：CUDA context、框架运行时、显存碎片等

主流优化方向几乎都集中在缩小前两项：量化（GPTQ、AWQ、bitsandbytes）、剪枝、蒸馏、PagedAttention（vLLM 的方案）、张量并行 / 流水线并行。AirLLM 走另一条路——逐层加载：不改精度、不改结构、不改并行拓扑，只把"整模型驻留显存"替换为"一次只驻留一层"。权重总数不变，磁盘占用不变，但峰值显存需求被压到单层大小。

## 核心原理：逐层加载如何突破显存限制

### 传统推理的显存模式

主流推理框架（HuggingFace Transformers、vLLM、TGI）加载模型时，在初始化阶段把所有权重从磁盘读入 GPU 显存并驻留。70B FP16 模型约 140GB，这就是为什么一般要求多张 A100/H100 或者至少一张 80GB 的 A800。

### AirLLM 的层流式模型

AirLLM 重新组织加载流程：

1. **磁盘存储**：模型按 Transformer layer 切分，每层权重（attention + FFN）单独保存为 safetensors 分片
2. **推理循环**：每生成一个 token，依次执行每一层——加载当前层权重进 GPU，完成前向计算，释放，再加载下一层
3. **流水线掩盖 I/O**：异步预取把下一层加载与当前层计算重叠

70B 模型（以 Llama 3 70B 为例）FP16 下约 80 层，每层权重约 1.7GB。加上 attention 的临时激活和 KV Cache，峰值显存由"单层权重 + 当前层 KV Cache + 激活"决定——这就是 4GB 跑 70B 的来源。

### 和主流方案对比

| 方案 | 显存占用 | 精度损失 | 适用硬件 |
|---|---|---|---|
| 整模型 FP16 加载 | 140GB（70B） | 无 | 多卡 80GB（2×A100/H100） |
| GPTQ/AWQ 4bit | ~40GB（70B） | 轻微 | 单卡 48GB |
| vLLM PagedAttention | 同整模型 | 无 | 多卡高端 |
| **AirLLM 逐层** | **~4GB（70B）** | **无** | **单卡 4GB** |
| AirLLM + 4bit 压缩 | ~1.5–2GB（70B） | 轻微 | 单卡 2GB |

逐层加载没有量化精度损失，不依赖特殊硬件，对显存极小的设备（消费级 GPU、Apple Silicon 入门款）特别友好。

## 压缩加速：4bit/8bit block-wise quantization 的 3x 加速

逐层加载解决了"显存放不下"的问题，但代价是吞吐下降——每层都要做一次磁盘到 GPU 的搬运。AirLLM v2 引入块级量化作为可选加速档。

### 压缩机制

4bit/8bit block-wise quantization 在逐层加载的基础上，对每层权重再做 4bit 或 8bit 量化。量化在加载过程中完成（边加载边反量化），显存里驻留的仍然是反量化后的 FP16/BF16 张量，计算图保持 FP16 精度。压缩效果是把磁盘上的层大小减到原来的 1/4（4bit）或 1/2（8bit），单层加载时间成比例下降。

### 3x 加速的来源

官方给出的"最高 3x 推理加速"出自 airllm 2.0 的更新日志，依据是 block-wise quantization 论文（arXiv:2212.09720）。逻辑不复杂：这条管线的瓶颈在磁盘到 GPU 的搬运，权重体积缩到几分之一，搬运时间就等比缩短——4bit 把单层从约 1.7GB 压到 400MB 出头，读一层的时间也降到原来的四分之一左右。预取调度带来的额外收益有限，官方数据是 v2.5 加入异步预取时记录的约 10% 提升；压缩之后层变小，预取在同样的缓冲里能铺更多层，流水线断流更少，属于顺带的好处。

3x 是上限值，不是普遍实测值。实际加速比取决于磁盘速度（NVMe SSD 远优于 HDD）、PCIe 世代（4.0/5.0）和 CPU 反量化能力。HDD 或慢速网络盘上做逐层加载，瓶颈根本不在计算，压缩救不回来。

### 2026 年的更新：FP8、MoE 与训练

v3.0 之后 AirLLM 的更新节奏明显加快，方向都是同一条——把"单层驻留"的极限继续往下压：

- **2026/06 v3.0**：原生支持 FP8 精度的预训练模型，权重体积比 FP16 再小一半。DeepSeek-V3（671B）FP8 下逐层加载约 12GB 显存，Qwen3-235B（MoE，混合专家架构——每次前向只有部分专家参数参与计算）约 3GB，全部走同一个 `AutoModel` 接口
- **2026/07 Kimi K3（2.8T）**：迄今最大的开源模型，在单张 RTX 6000 Ada 上端到端实测 3.72GB 显存。关键机制是**按专家流式加载**——MoE 层只读取当前 token 实际路由到的专家权重，没被路由到的专家不进显存。代价是依赖项偏多：需要装 `compressed-tensors` 和 `flash-attn`（其模型代码强制 flash attention）、CUDA 12 版本的 torch（flash-attn 暂无 CUDA 13 预编译包），且 `transformers` 必须停在 4.56.x（其 remote code 在 5.x 上无法加载）
- **2026/08 Qwen3.8 系列**：Flash-Next（125B MoE，另带约 51B 参数的 n-gram 嵌入表，该表以文件映射方式留在主机内存、不占显存）实测 5.95GB（RTX 4090）；27B 稠密视觉语言模型实测 3.33GB（RTX 3090）
- **2026/09 训练支持**：冻结的基础权重按层从磁盘流过 GPU，显存里只常驻 LoRA adapter（低秩适配矩阵，微调时只训练它）——Qwen3.8-Flash-Next（125B）能在 RTX 3060 Ti 的 6GB 显存内完成微调，Qwen3.8-27B 在 seq 512 下约 2GB

| 模型 | 参数规模 | 实测/标称显存 |
|---|---|---|
| Qwen3 / Mistral / Phi（8B 级） | ~8B | ~1–2GB |
| Qwen3-30B / Mixtral（MoE） | 30–47B | ~1–3GB |
| Qwen3.8-27B（视觉语言） | 27B | 3.33GB |
| Qwen3-235B（MoE） | 235B | ~3GB |
| Llama 3.x 70B（全精度） | 70B | ~4GB |
| Kimi K3（MoE） | 2.8T | 3.72GB |
| Llama 3.1 405B | 405B | ~8GB |
| DeepSeek-V3（FP8） | 671B | ~12GB |

从 8B 到 2.8T，显存需求被钉死在"单层大小"上，和总参数量几乎脱钩——这就是这张表想说明的事。

## 性能权衡：延迟 vs 显存的取舍

逐层加载本质上是用延迟换显存。

### 首字延迟显著放大

生成是逐层的，延迟却不只是"单层加载"的量级。以 70B FP16、4GB GPU 为例：每生成一个 token 都要依次读完整份模型（约 140GB），即使有预取掩盖，I/O 等待也会把单 token 时间推到秒级甚至数十秒（见下文磁盘测算），对比整模型驻留时毫秒级。对交互式对话（期望 100ms–500ms 首字响应），这个延迟通常不可接受。

### 批处理不是它的主场

AirLLM 的接口就是单流生成范式，README 和示例都围绕一次一条输入展开。想提高总吞吐，实际做法是在外层把多条请求串行排队——好在显存受限的离线场景里，用户要的本来就是"能跑完"，不是"跑得快"。反过来，4GB 的显存预算也塞不下多少并行请求的 KV Cache，靠增大 batch 换吞吐在这里没有空间。

### 磁盘是新的"显存"

AirLLM 把显存约束转嫁到磁盘带宽和容量。模型权重的"工作集"仍在磁盘上，只是把"全量驻留显存"换成了"按层滚动"。这里有两个容易被低估的现实：

**磁盘速度决定单 token 耗时。** 每生成一个 token，都要把整份模型读一遍。粗略估算，`单 token 耗时 ≈ 模型磁盘体积 ÷ 磁盘读速`。以 70B FP16（约 140GB）为例：Gen4 NVMe（约 7GB/s）约 20 秒，Gen3 NVMe（约 3.5GB/s）约 40 秒，SATA SSD（约 0.5GB/s）则到分钟级，HDD 基本不可用。作为对照，把量化 70B 完整装进显存的推理方案（llama.cpp、vLLM），单流速度通常在每秒数个到几十个 token——逐层加载比它们慢两到三个数量级。所以这句话值得写明白：**AirLLM 不是让 70B 变快，而是让它在 4GB 显卡上变得可能。**

**逐层切分会占用大量磁盘。** 推理前需把模型按层切分成独立 safetensors 分片，磁盘占用约翻倍，且持续预留缓存空间。官方 FAQ 里最常见的报错 `MetadataIncompleteBuffer`（safetensors 反序列化失败），第一嫌疑就是切分过程中磁盘写满。好在有 `delete_original` 选项可在切分后删除原始权重，回收一半空间。因此：

- 模型文件必须常驻本地磁盘，不能放在慢速网络盘
- NVMe SSD 几乎是必需品，SATA SSD 也能跑但延迟更高
- 动手前先确认 HuggingFace 缓存目录所在分区有足够空闲空间
- Apple Silicon 走 unified memory 架构，SSD 吞吐也不错

## 适用场景与边界

### 典型适用场景

- **个人开发者在小显存设备上跑大模型**：MacBook 16GB、Apple Silicon、单张消费级显卡（3060/4060 8GB、3060 12GB 等）
- **离线批量推理**：数据标注、批量摘要、长文档分析，对单条延迟不敏感
- **研究和复现**：低预算实验室验证 70B+ 模型行为
- **小显存微调**：冻结权重流式加载 + LoRA adapter 常驻的方案，把微调门槛也压了下来（见上文 2026/09 更新）
- **资源受限环境部署**：在没有 80GB 级显卡的边缘节点或开发机上提供大模型能力
- **显存扩容前的临时方案**：采购 80GB 显卡前先用 AirLLM 跑起来

### 不适合的场景

- **实时对话 / 聊天产品**：首字延迟太高
- **高并发在线服务**：逐层 I/O 会成为瓶颈，QPS 受限
- **需要低延迟流式输出逐字显示的场景**：可以输出流式，但每个字的间隔仍受逐层加载影响
- **极慢磁盘或网络盘**：单 token 耗时公式在这里直接退化到不可用，没有优化余地

### 安装与上手

```bash
pip install airllm
# 使用 4bit/8bit 块级压缩加速时，还需安装量化内核依赖
pip install -U bitsandbytes
```

```python
from airllm import AutoModel

# 完整精度，仅逐层加载。开箱即用的模型直接传 HF repo id
model = AutoModel.from_pretrained("Qwen/Qwen3-32B")

# 需要更快时叠加块级压缩（精度损失极小，瓶颈是权重 IO）
model = AutoModel.from_pretrained("Qwen/Qwen3-32B", compression="4bit")

# Llama 这类 gated 模型需要传 HuggingFace token
# model = AutoModel.from_pretrained("meta-llama/Meta-Llama-3-70B-Instruct",
#                                   hf_token="hf_xxx")
```

接口与 HuggingFace `AutoModel` 高度一致，仅需替换 import，无需手动切分模型——切分在首次推理时自动完成。常用参数还有 `layer_shards_saving_path`（指定分片保存目录）、`delete_original`（切分后删除原始权重释放一半磁盘）、`prefetching`（异步预取，默认开启）与 `profiling_mode`（输出各阶段耗时，排查 I/O 瓶颈时有用）。支持 Linux 与 Apple Silicon macOS（后者需安装 MLX 与 torch），模型覆盖 Llama 2/3.x/4、Qwen 1–3.8、DeepSeek V2/V3/R1、Kimi K3、Phi、Gemma、ChatGLM、Mistral、Baichuan、InternLM、Yi 等主流架构。

想跑 Kimi K3 的注意两点：需要额外安装 `compressed-tensors` 与 `flash-attn`，并固定 `transformers` 到 4.56.x；2.8T 参数的权重本身就是 TB 级体积，切分期间还要等量空间存放分片，动手前先把磁盘账算清（`delete_original=True` 可在切分后回收原始权重）。

微调走仓库自带的训练脚本，数据是逐行 JSON 的 jsonl 文件：

```bash
python air_llm/examples/train_qwen38_flash_next_lora.py \
  --data my_data.jsonl \
  --seq-len 512 \
  --epochs 1 \
  --save-adapter qwen38-flash-next-lora.pt
```

Python 侧对应 `AirLLMLoRAQwen4Exp`（Flash-Next）与 `AirLLMLoRA`（27B dense）两个训练器，`train_step` 逐步喂数据，结束时 `save_adapter` 保存 LoRA 权重。注意这条路不是 HuggingFace Trainer / bitsandbytes QLoRA，依赖与显存行为都以官方 README 的 Training 一节为准。

## 结论

AirLLM 的路线是：不压模型，只压显存驻留时间。把整模型加载变成 Transformer 层的流式管道，用磁盘带宽和异步预取掩盖单层加载开销，换来极低的峰值显存需求。

块级量化让这条管线快了最多 3 倍；v3.0 加入 FP8 与 MoE 支持后，天花板从 70B 推到 DeepSeek-V3 的 671B，再到 Kimi K3 的 2.8T；2026 年 9 月的训练支持又把小显存微调纳入同一条管线。对显存受限、延迟不敏感的离线推理与研究场景，AirLLM 是当下最务实的选择；对实时在线服务，vLLM、TGI、TensorRT-LLM 仍是更优解。

理解 AirLLM 的关键不在于"用了什么魔法"，而在于重新定义了推理的显存假设：**GPU 显存不需要装得下整个模型，只需要装得下一层。**