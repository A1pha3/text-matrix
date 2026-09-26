---
title: "KTransformers：让 CPU-GPU 异构推理跑超大 MoE 的实战框架"
date: 2026-07-20T03:02:36+08:00
lastmod: 2026-09-19T00:00:00+08:00
categories: ["技术笔记"]
tags: ["MoE", "LLM 推理", "微调"]
description: "KTransformers 是清华 MADSys 实验室与 Approaching.AI 主导的 CPU-GPU 异构 LLM 推理/微调框架，约 19.5K stars，SOSP 2025 论文工作。GPU 放高频激活的 MoE 专家、CPU 内存放其余专家，GLM-5.3-flash（1M 上下文）、DeepSeek-V4-Flash、Kimi-K2.5 等超大 MoE 在 24GB 级消费显卡 + 大内存上即可运行，并经 LLaMA-Factory 集成提供 LoRA 与全参微调。本文拆解 expert 放置机制、CPU 内核精度格式、三层 KV cache 与微调路径，附官方 benchmark 的正确读法和采用建议。"
slug: kvcache-ai-ktransformers-heterogeneous-llm
github_repo: "kvcache-ai/ktransformers"
source_key: "gh:kvcache-ai/ktransformers"

---

# KTransformers：让 CPU-GPU 异构推理跑超大 MoE 的实战框架

## 一句话判断

KTransformers 解决的问题非常具体：MoE（Mixture of Experts，混合专家）模型总参数大到单张显卡装不下，但每次推理只激活其中一小部分专家。它把专家权重当作可以放置的资产——GPU 放高频激活的，CPU 内存放其余的——用 CPU 侧计算换显存容量，让 24GB 级消费显卡加一台大内存主机，也能跑起 DeepSeek-V3、GLM-5.3-flash、Kimi-K2.5 这个量级的模型。

微调走同一条思路：GPU 承担 Attention 和共享专家，路由专家（routed experts）留在 CPU 内存里参与训练。推理与微调共用一套异构内核（kt-kernel），对外分别提供 serving（kvcache-ai 维护的 SGLang fork）与 LLaMA-Factory 集成两条入口。

项目由清华大学 MADSys 实验室与 Approaching.AI 等团队维护，背后是 SOSP 2025 论文工作（*KTransformers: Unleashing the Full Potential of CPU/GPU Hybrid Inference for MoE Models*）。2026 年 9 月仓库当天仍有提交；GLM-5.3-flash 在 8 月底拿到原生支持，Kimi K2.5/K2.6 的 LoRA 微调 9 月中旬跟上——在新模型支持这件事上，它是更新最勤的开源实现之一。

## 项目档案

- **仓库**：`kvcache-ai/ktransformers`，Apache-2.0，Python + C++/CUDA
- **热度**：约 19.5K stars、1.6K forks（2026-09-19 GitHub API 数据）
- **学术**：SOSP 2025（第 31 届 ACM 操作系统原理会议）
- **版本**：v0.6.1（2026-04）起推理与微调统一到 kt-kernel 源码树，当前 v0.7.0；重构前的旧框架整体移入 `archive/` 目录
- **Roadmap**：2026 Q2 路线图见 [issue #1921](https://github.com/kvcache-ai/ktransformers/issues/1921)
- **模型支持节奏**：README 的 Updates 时间线里，2026 上半年五款主流模型标注 Day0 Support——Kimi-K2.5（01-27）、GLM-5（02-12）、MiniMax-M2.5（02-13）、GLM-5.2（06-17）、MiniMax-M3（06-21）；DeepSeek-V4-Flash（05-02）与 GLM-5.3-flash（08-26）也在支持列表中

## 系统地图

| 组件 | 职责 | 入口 |
|------|------|------|
| kt-kernel | 异构推理内核：CPU 侧 MoE 专家计算 + GPU 侧 Attention | `pip install kt-kernel`，文档 `kt-kernel/README.md` |
| SGLang-KT | SGLang 的 kvcache-ai fork，承接 serving：OpenAI 兼容 API、动态专家更新 | `pip install sglang-kt` 或 `pip install "ktransformers[sglang]"` |
| KT SFT（Supervised Fine-Tuning，监督微调） | LLaMA-Factory 集成微调，LoRA 与全参 | `pip install "ktransformers[sft]"`，见官方 Cookbook |
| Balance Serve + prefix cache | 多并发 serving 下的三层 KV cache 存储与复用 | `doc/en/prefix_cache.md` |
| KT-CLI | 命令行入口：`kt chat` / `kt run` / `kt version` | `doc/en/kt-kernel/kt-cli.md` |

两条主线在架构上是对称的：GPU 负责 Attention 与高频专家，CPU 内存负责被路由的专家。推理时这个动作叫 expert placement，微调时叫 CPU-GPU 混合训练。与上游 SGLang 的融合始于 2025 年 10 月（[roadmap issue](https://github.com/sgl-project/sglang/issues/11425)、[LMSYS 博客](https://lmsys.org/blog/2025-10-22-KTransformers/)），现在以 `sglang-kt` fork 的形式分发。

## 机制一：专家放置与调度

### 为什么需要"放置"

MoE 层里每个 token 只会路由到少数几个专家，所以"全模型放不进显存"和"单步计算只需要一小部分"同时成立。KTransformers 的做法不是把专家在 CPU/GPU 之间来回搬运，而是先决定哪些专家常驻 GPU，其余留在 CPU 内存按需计算。放置策略用四个启动参数表达：

| 策略 | 行为 | 适用 |
|------|------|------|
| `uniform` | 均匀铺到各 MoE 层 | 默认值，无需先验统计 |
| `frequency` | 最常被激活的专家上 GPU | 有激活统计时性能最好 |
| `front-loading` | 从第一层往后填满 GPU | 测试或特定负载 |
| `random` | 固定种子随机放置 | 基线对照 |

GPU 上放多少专家由 `--kt-num-gpu-experts`（每层数量）或 `--kt-gpu-experts-ratio`（总比例 0.0-1.0）控制。`frequency` 策略需要用 `--init-expert-location` 传入一份激活统计文件（`.pt`），统计本身可以用自带的录制功能（`--record-kt-gpu-expert-distribution`）采集。

### 动态更新与双通道 prefill

文档里真正"动态"的部分有两处，不要混淆：

- **动态专家更新**（`--kt-enable-dynamic-expert-update`）：在 prefill（预填充，处理输入 token 的阶段）期间按 `--kt-gpu-prefill-token-threshold` 阈值触发专家重分布，让 GPU 常驻专家逐步对齐当前负载的激活分布。
- **双通道 prefill**：短请求（token 数低于阈值）走 CPU-GPU 混合计算；长 prefill 切到 Layerwise Prefill——把 CPU 侧权重搬运到 GPU 上逐层算，用带宽换吞吐。

也就是说，调度粒度是"请求的 prefill 阶段"，不是"每个 token"。把它理解成每来一个 token 就换入换出专家是不对的——那既不必要，代价也高得离谱。

### 放置策略值多少吞吐

官方在 Qwen3-Next-80B-A3B-Instruct-FP8 上测过一组对照：4×RTX 4090 + Xeon Gold 6454S，张量并行度 4（tensor parallel 4），ShareGPT 负载（完整 11 行数据见[官方教程](https://github.com/kvcache-ai/ktransformers/blob/main/doc/en/kt-kernel/experts-sched-Tutorial.md)，此处取关键行）：

| GPU 专家比例 | random | uniform | frequency | 动态更新 |
|-------------|--------|---------|-----------|---------|
| 0% | 53.01 | 52.96 | 52.72 | 53.37 |
| 10% | 56.63 | 56.57 | 58.60 | 70.22 |
| 30% | 62.86 | 62.08 | 66.50 | 75.55 |
| 50% | 70.38 | 65.25 | 76.19 | 81.17 |
| 90% | 88.82 | 81.06 | 107.15 | 95.04 |
| 100% | 112.61 | 112.32 | 114.26 | 112.99 |

这组数字在测什么：固定硬件与负载，吞吐如何随"GPU 上放多少专家、按什么策略放"变化。

数字主要反映哪部分系统：CPU 侧专家计算是主要瓶颈。GPU 专家占 0% 时全部专家计算压在 CPU 上，吞吐约 53 tokens/s；放到 100% 翻倍出头。策略质量在低放置比例时影响最大——10% 比例下动态更新（70.22）比 uniform（56.57）高约 24%，说明"哪 10% 上 GPU"远比"放不放"重要；比例到 90% 后差距收窄，因为大部分计算已经不经过 CPU。

从这些数字不能推出：其他模型或其他硬件上的表现（这是 80B-A3B、4×4090、ShareGPT 负载下的单点数据）；与全 GPU 方案的通用性能对比（表里没有延迟指标，也没有对比对象）。

## 机制二：CPU 内核与精度格式

### 六档内核，按 CPU 自动选择

`pip install kt-kernel` 的 wheel 里带 6 个编译变体，运行时检测 CPU 自动挑最优：AMX（Intel Sapphire Rapids 2023+，最优）、AVX512+BF16 / VBMI / VNNI / Base、AVX2 兜底（Haswell 2013+）。AVX2 的老服务器能跑，只是慢。GPU 侧要求 NVIDIA SM80 及以上（A100 / RTX 30 系起），Turing、Volta 不受支持；DeepSeek-V4-Flash 与 GLM-5.3-flash 两条新教程额外覆盖 SM120（RTX 50 系）。

### 精度格式是 CPU 侧概念

`--kt-method` 选的是 CPU 内核算专家时用的精度，不是 GPU 量化方案：

| kt-method | 格式 | 说明 | 指令集 |
|-----------|------|------|--------|
| `BF16` | BF16 原生 | 零精度损失，直接用原始权重 | AMX + AVX512 |
| `FP8` | FP8 blockwise | 分块 scale 量化 | AVX512 |
| `FP8_PERCHANNEL` | FP8 per-channel | 逐通道 scale，粒度比 blockwise 更细 | AVX512 |
| `RAWINT4` | INT4 原生 | CPU 与 GPU 共用同一份 INT4 权重 | AVX512 |

一个值得注意的设计：模型官方权重直接读。GLM-5.3-flash 的官方 FP8 权重（约 306 GiB）不做转换直接加载，省掉一步离线量化；DeepSeek-V4-Flash 的 MXFP4（4-bit 浮点格式）路由专家直接在 CPU 和 GPU 之间拆分。

## 机制三：三层 KV cache

这是 Balance Serve（多并发 serving 模式）的能力，2025-06-30 加入：KV cache（Key-Value 缓存）分三层存放与复用——GPU、CPU 内存（配置示例给了 500GB 量级）、磁盘（指定 `disk_path`），跨请求复用已经算过的前缀 KV。典型受益场景是多轮对话的历史部分、多个请求共享的长系统提示——命中前缀的请求跳过重复 prefill。

两个现状要清楚：开启该模式需要改配置并重新编译（会拉取 PhotonLibOS 子模块）；KV cache 目前不支持自动删除，满了只能手动清理缓存文件。

## 机制四：微调主线（LLaMA-Factory 集成）

### 架构分工

推理与微调共享同一套异构思路：GPU 跑 Attention 与共享专家，KTransformers 管理驻留在 CPU 内存里的路由专家。LLaMA-Factory 保持原有的编排角色——数据处理、LoRA（Low-Rank Adaptation，低秩适配）注入、训练循环——KTransformers 在底下替换执行后端。

官方 [Cookbook](https://github.com/kvcache-ai/ktransformers/blob/main/doc/en/SFT/KTransformers-Fine-Tuning_Cookbook.md)（2026-08-25）给出的判断是：1-4 张 RTX 4090 加一台内存足够的 CPU 机器，就能微调 DeepSeek-V3/V4 系列、Kimi-K2.5、GLM-5.2 这个量级的模型。

### 官方微调数据的读法

| 模型 | 显存占用 | 训练速度 | 硬件 |
|------|---------|---------|------|
| DeepSeek-V3 | 约 80GB 总显存 | 3.7 it/s | 4×RTX 4090 |
| DeepSeek-R1 | 约 80GB 总显存 | 3.7 it/s | 4×RTX 4090 |
| Qwen3-30B-A3B | 约 24GB 总显存 | 8+ it/s | 1×RTX 4090 |

两个注记。其一，it/s 是迭代速度，换算成 tokens/s 取决于每步 batch 配置，不能直接横向比较。其二，"比 ZeRO-Offload（DeepSpeed 的 CPU 卸载训练方案）快 6-12 倍"是官方在测过的 MoE SFT 负载上的口径，CPU 内存占用约为上一代 KT SFT 路径的一半——数字出自 README，适用范围限定在 benchmark 负载内。

### 2026 年的微调能力时间线

- **2026-07-23**：MoE 模型 BF16 全参数微调端到端跑通，含完整 checkpoint 保存（PR #2094）
- **2026-08-05**：原生 block-FP8 LoRA（PR #2141）
- **2026-08-17（v0.7.0）**：LoRA 不再要求 AMX，兼容 AVX512 x86 CPU，含 AMD 服务器
- **2026-09-13**：Kimi K2.5 / K2.6 LoRA，原生 RAWINT4 路由专家

全参、FP8、无 AMX 三个补齐，意味着"内存够大的普通 x86 服务器"进入了可用范围，不再绑定特定指令集。

## 一次真实部署：DeepSeek-V4-Flash 单卡跑通

用一个官方验证过的配置把上面的机制串起来。DeepSeek-V4-Flash 的路由专家是 MXFP4 格式，官方教程验证的配置：1×RTX 5090（32GB 显存）+ 200GB 以上系统内存 + 约 340GB 磁盘。

1. 下载权重（约 340GB）；
2. 安装 `pip install "ktransformers[sglang]"`，或直接用官方 Docker 镜像 `approachingai/ktransformers:DSV4-specific`；
3. `python -m sglang.launch_server` 启动，`--kt-num-gpu-experts` 决定多少专家常驻 32GB 显存，其余路由专家留在 CPU 内存，由 kt-kernel 的 cpuinfer 线程计算；
4. 请求进来：prefill 长度低于阈值走 CPU-GPU 混合计算，长 prefill 触发 Layerwise Prefill；
5. 可选打开 MTP（Multi-Token Prediction）投机解码加速 decode；
6. 用 `kt chat` 或 OpenAI 兼容 API（`:30000/v1`）验证。

RTX 4090（SM89）、RTX 3090（SM86）也在支持矩阵里，代价是吞吐下降。同一个模型还有单张昇腾 NPU + CPU expert offload 的教程（2026-08-16 加入），这是国产硬件路径。

## 硬件门槛速查

| 模型 | 官方验证 / 最低配置 | 上下文 | 出处 |
|------|--------------------|--------|------|
| DeepSeek-V3 / R1（推理） | 24GB 显存 + 382GB 内存（INT4 权重） | 139K | README 2025-02-10、03-05 |
| DeepSeek-V4-Flash（推理） | 1×RTX 5090 32GB + ≥200GB 内存 + 340GB 磁盘 | — | V4-Flash 教程 |
| GLM-5.3-flash（推理） | SM89/SM120 GPU + ≥350GB 内存（FP8 权重约 306GiB） | 1M | GLM-5.3-flash 教程 |
| Qwen3-Next-80B（推理） | 最低 24GB 显存 + 256GB 内存；测过 4×4090 + 512GB | — | 专家调度教程 |
| DeepSeek-V3 / R1（LoRA 微调） | 4×RTX 4090，约 80GB 总显存 | — | README SFT 表 |
| Qwen3-30B-A3B（微调） | 1×RTX 4090，约 24GB | — | README SFT 表 |

规律很清楚：显存门槛落在 24-32GB 这个消费级区间，真正的门槛在内存——从 200GB 到 382GB 不等。这台机器的主要成本往往不是显卡，是内存条。

硬件演进的历史值得交代一句：2025 年上半年项目曾加入 AMD ROCm（3 月）与 Intel Arc XPU（5 月）支持，属于重构前原框架时期的能力；当前 kt-kernel 主线是 NVIDIA SM80+ 与 x86 CPU，昇腾 NPU 路线在 2026 年持续更新。

## 采用建议

**适合现在就用**：

- 想在本地跑最新开源 MoE 的个人开发者——模型发布当天往往就有教程，从 `pip install "ktransformers[sglang]"` 开始，按 GLM-5.3-flash 或 DeepSeek-V4-Flash 教程走；
- 研究 CPU-GPU 异构推理的人——SOSP 2025 论文、可读性不错的 kt-kernel 源码、明确的 roadmap（issue #1921）三者齐备；
- 需要本地微调超大 MoE、又租不起 8×H100 的研究者——Cookbook 从硬件检查、安装、BF16/FP8/INT8 配方到排障是完整链路；
- 手上有 AVX512/AMX 服务器或昇腾硬件的团队——两条硬件路径都有官方教程。

**不必急着上**：

- 高并发生产 serving——全 GPU 方案（vLLM、上游 SGLang）在这个象限更成熟；Balance Serve 虽支持多并发，但这个项目的主战场始终是"模型放不下显存"的约束；
- 稠密模型推理——整套设计围绕 MoE 专家的可放置性展开，稠密模型没有可放置的专家，用 vLLM / SGLang 即可。

**一个维护性提醒**：项目在 2026 年经历了大重构（旧框架整体归档，推理与微调统一到 kt-kernel 源码树），入口与参数名在演进中。部署前先读当前版本（v0.7.0）对应的教程确认参数，不要照抄几个月前的旧文章。

## 仓库地址

https://github.com/kvcache-ai/ktransformers
