---
title: "KTransformers：让 CPU-GPU 异构推理跑超大 MoE 的实战框架"
date: 2026-07-20T03:02:36+08:00
categories: ["技术笔记"]
tags: ["llm-inference", "moe", "cpu-gpu", "fine-tuning", "ktransformers"]
description: "KTransformers 是一个 CPU-GPU 异构 LLM 推理 / 微调框架，18K stars，支持 DeepSeek-V3/V4、Kimi-K2.5、GLM-5.2、MiniMax-M3 等主流 MoE 模型在 24GB 单卡上跑，集成 LLaMA-Factory 做 SFT，是当下最活跃的国产 LLM 优化框架之一。"
---

# KTransformers：让 CPU-GPU 异构推理跑超大 MoE 的实战框架

## 一句话判断

KTransformers 是当前**最活跃的 CPU-GPU 异构 LLM 推理 / 微调框架**之一——18K stars，2026 年 6-7 月连续 Day0 支持 MiniMax-M3 / GLM-5.2 / Kimi-K2.5 / DeepSeek-V4-Flash 等主流 MoE（Mixture of Experts，混合专家）模型。它把"超大 MoE 模型在 24GB 单卡 + 256GB DRAM"这件事做成了一行命令 + LlamaFactory 集成，是个人开发者和中小团队跑前沿 MoE 的现实路径。

## 项目定位

- **仓库**：`kvcache-ai/ktransformers`，Apache-2.0 协议，Python + C++/CUDA
- **GitHub Stars**：18.3K，Forks 1.4K（2026-07-19 数据）
- **核心能力**：CPU-GPU 异构推理 + LLaMA-Factory 集成 SFT（Supervised Fine-Tuning，监督微调）
- **Day0 模型支持节奏**（节选）：
  - 2026-06-21：MiniMax-M3
  - 2026-06-17：GLM-5.2
  - 2026-05-02：DeepSeek-V4-Flash
  - 2026-02-13：MiniMax-M2.5
  - 2026-02-12：GLM-5
  - 2026-01-27：Kimi-K2.5
  - 2026-01-22：CPU-GPU Expert Scheduling + Native BF16/FP8 + AutoDL 集成

## 系统地图

| 模块 | 责任 | 入口 |
|------|------|------|
| kt-kernel inference | CPU-GPU 异构推理核心，expert offload + prefix cache | `kt-kernel/README.md` |
| KTransformers SFT | 集成 LLaMA-Factory 做微调 | `doc/en/SFT/KTransformers-Fine-Tuning_Quick-Start.md` |
| Prefix Cache | 3 层 GPU-CPU-Disk prefix cache 复用 | `doc/en/prefix_cache.md` |
| CPU-GPU Expert Scheduling | MoE expert 在 CPU/GPU 之间调度 | `doc/en/kt-kernel/experts-sched-Tutorial.md` |
| Native Precision | Native BF16 / FP8 per channel | `doc/en/kt-kernel/Native-Precision-Tutorial.md` |
| Ascend NPU 支持 | 国产 NPU 适配 | `doc/zh/DeepseekR1_V3_tutorial_zh_for_Ascend_NPU.md` |
| SGLang 集成 | 接入 SGLang serving stack | [sgl-project/sglang#11425](https://github.com/sgl-project/sglang/issues/11425) |

## 关键机制拆解

### 1. CPU-GPU 异构推理

MoE 模型的核心矛盾是"参数太多放不进单卡 GPU"。DeepSeek-V3 671B 全部加载需要 ~1.3TB 显存，普通数据中心 GPU 都跑不动。KTransformers 的解法是 **CPU-GPU 异构 + expert offload**：

- **Hot experts**（推理时高频激活的 expert）：放在 GPU
- **Cold experts**（低频激活的 expert）：放在 CPU DRAM 或 NVMe SSD
- **动态调度**：根据输入 token 动态决定哪些 expert 需要 swap in / out

这意味着单卡 24GB + 256GB DRAM 就能跑 DeepSeek-V3 671B——代价是吞吐比全 GPU 方案低，但成本是 1/N。

### 2. Prefix Cache 3 层

2025-06-30 加入的 3 层 prefix cache（GPU-CPU-Disk）：

- **L1 GPU**：当前请求的 KV cache
- **L2 CPU**：同一 session 的历史 KV cache
- **L3 Disk**：跨 session 的 prefix cache

3 层 cache 把"长上下文 + 多轮对话"的延迟从 O(n²) 降到接近 O(n)，是 KTransformers 处理 100K+ 上下文的核心。

### 3. Native BF16 / FP8 per channel

2026-01-22 加入 native precision 支持：

- **BF16**：训练 / 推理通用精度
- **FP8 per channel**：H100 / H200 GPU 的原生 FP8，per channel 量化比 per tensor 更精确

这两层精度支持让 KTransformers 能用上 H100/H200 的硬件 FP8 加速，同时不丢精度。

### 4. LLaMA-Factory 集成 SFT

KTransformers 把推理和微调做了清晰的模块拆分：

- **推理**：`kt-kernel/`，原生 CPU-GPU 异构
- **微调**：集成 LLaMA-Factory，走标准 SFT 流程

这种"推理自研、微调复用社区"的模式让用户**不需要在两套框架间切换**——同一个 KTransformers 仓库里既能跑推理也能跑 SFT。微调完直接用 KTransformers 推理，零迁移成本。

### 5. Day0 模型支持节奏

KTransformers 的一个重要竞争力是**新模型发布后几乎 Day0 上线**——2026 年上半年每一次国产新模型发布，KTransformers 都在 1-2 周内提供 Day0 教程。这背后是一个小而精的维护团队 + 紧密的模型厂商协作。对想用最新模型的开发者来说，这意味着"新模型发布第二天就能本地跑"。

### 6. 多硬件支持

支持的硬件范围比 vLLM / SGLang 更广：

- **NVIDIA GPU**：CUDA
- **AMD GPU**：ROCm（2025-03-15 加入）
- **Intel Arc GPU**：XPU（2025-05-14 加入）
- **Ascend NPU**：国产 NPU（2025-10-27 加入）

多硬件支持意味着无论你的硬件是 NVIDIA / AMD / Intel / 昇腾，都能跑 KTransformers——对国产硬件用户尤其友好。

## 适用人群

- **想跑最新 MoE 模型的人**：Day0 支持，DeepSeek-V3/V4、Kimi-K2.5、GLM-5.2、MiniMax-M3 都能跑
- **消费级硬件用户**：单卡 24GB + 256GB DRAM 即可，门槛比 full GPU 部署低得多
- **国产硬件用户**：Ascend NPU 适配，国内自托管场景
- **需要本地 SFT 的人**：LLaMA-Factory 集成 + CPU-GPU 异构微调
- **研究 CPU-GPU 异构推理的学者**：代码可读、有详细 doc、有 roadmap

## 不适合谁

- **追求最大吞吐的生产环境**：异构推理的吞吐比全 GPU 低 30-50%
- **完全不懂 CUDA / 推理优化的人**：虽然有一键脚本，但出问题排查需要理解 CPU-GPU 调度
- **只想跑稠密模型（Dense LLM）的人**：KTransformers 的优势在 MoE，dense LLM 用 vLLM / SGLang 更成熟

## 仓库地址

https://github.com/kvcache-ai/ktransformers

## 阅读路径建议

1. 读 README 的 Updates 节，确认你要跑的模型已被 Day0 支持
2. 按 `kt-kernel/README.md` 跑通 inference 最小 demo
3. 看 `doc/en/kt-kernel/experts-sched-Tutorial.md` 理解 expert 调度逻辑
4. 如果要 SFT，读 `doc/en/SFT/KTransformers-Fine-Tuning_Quick-Start.md` 走 LLaMA-Factory 流程