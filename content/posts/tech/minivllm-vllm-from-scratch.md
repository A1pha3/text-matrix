---
title: "MinivLLM：从零理解vLLM推理引擎的完整指南"
date: 2026-05-12T10:50:00+08:00
slug: minivllm-vllm-from-scratch
description: "MinivLLM 是一个基于 Nano-vLLM 的自定义 vLLM 推理引擎实现，提供了从层组件到调度器的完整代码路径，并通过基准测试对比 FlashAttention（预填充阶段）和 PagedAttention（解码阶段）的性能差异。项目作者还提供了配套的中文学习指南，适合想要深入理解 LLM 推理系统工程细节的开发者。"
draft: false
categories: ["技术笔记"]
tags: ["vLLM", "LLM推理", "PagedAttention", "FlashAttention", "CUDA", "Triton", "Paged KV Cache"]
hiddenFromHomePage: true
---

# MinivLLM：从零理解 vLLM 推理引擎的完整指南

如果想理解 vLLM 背后的工程原理，却没有数万平方米的代码库让你望而生畏，MinivLLM 或许是一个合适的起点。这个仓库基于 Nano-vLLM，从头实现了一个最小化的 vLLM 推理引擎，将完整的技术路径拆解为六个步骤——从最基础的神经网络层，到最终的调度器和 Engine 顶层 API，每一步都有对应的代码和中文学习指南。

项目地址：[Wenyueh/MinivLLM](https://github.com/Wenyueh/MinivLLM)（721 Stars，98 Forks）

## 1. 背景与项目定位

vLLM 是当前开源社区最流行的 LLM 推理框架之一，其核心技术——PagedAttention——源自 UVA 苏立德实验室的 [vLLM 论文](https://arxiv.org/abs/2309.06119)，通过操作系统式内存管理将 KV Cache 的显存占用大幅降低。然而 vLLM 本身的代码经过多年工程优化，理解门槛较高。

MinivLLM 做的事很明确：**把 vLLM 的实现路径还原为学习路径**。作者在仓库中提供了配套文档 [HowToApproachvLLM_zh.md](https://github.com/Wenyueh/MinivLLM/blob/main/HowToApproachvLLM_zh.md)，从层组件讲起，一路讲到 Scheduler 和 Engine，按步骤逐一构建出一个可运行的推理系统。

项目包含三个基准测试脚本，可以直接对比不同注意力实现方案的性能差异：

- **Prefilling 阶段**（处理输入 prompt）：`benchmark_prefilling.py`
- **Decoding 阶段**（逐 token 生成）：`benchmark_decoding.py`

这使得理论学习和实验验证可以紧密结合。

## 2. 核心架构：从层到 Engine

MinivLLM 的完整技术路径分为六个步骤，每一步在前一步的基础上添加新的系统组件：

### Step 1：层组件（Layers）

构建 LLM 最基础的结构块。这一步对应 `src/myvllm/layers/` 下的六个模块：

**激活函数**（`activation.py`）：实现 SiLU 和 GELU。作者在这里做了 `torch.compile` 的基准测试，发现它在大 Tensor 场景下可显著加速，但小 Tensor 反而因为编译开销拖慢性能——这个结论反直觉，却是 CUDA 编程中的常见陷阱。

**RMS LayerNorm**（`layernorm.py`）：只使用 RMS 均方根进行归一化，跳过均值中心化步骤，相比标准 LayerNorm 计算更轻量，对大模型训练稳定性有重要意义。

**线性层与张量并行**（`linear.py`）：这是最复杂的一层，需要支持分布式训练。作者实现了四种并行线性层：

- `ColumnParallelLinear`：沿输出维度切分，多 GPU 并行计算，前向传播无需通信
- `RowParallelLinear`：沿输入维度切分，需要 `dist.all_reduce` 聚合部分结果
- `MergedColumnParallelLinear`：将 gate 和 up 两个投影合并，适合 MLP 层的高效权重加载
- `QKVColumnParallel`：Q/K/V 投影的特殊实现，每张 GPU 保留完整的 head，不切 head 维度

**词表嵌入与 LM Head**（`embedding_head.py`）：关键在于 `dist.gather` 和 `dist.all_gather` 的区别——前者只有目标 GPU 收到数据，后者所有 GPU 都收到。在张量并行中这决定了权重聚合的行为。

**注意力层**（`attention.py`）：引入了 FlashAttention 实现。作者特别讨论了 stride 概念：当张量存储在连续内存中时，沿着某个维度移动到下一个元素需要跳过多少个元素。理解 stride 是读懂 Triton Kernel 参数的关键。

**旋转位置编码 RoPE**（`rotary_embedding.py`）：详细讨论了 base 参数对远距离位置编码的影响，以及 YARN 和 NTK 两种长上下文外推策略。

### Step 2：模型构建（Model）

在 `src/myvllm/models/qwen3.py` 中将所有层组装为完整模型。这里有几个值得注意的设计决策：

- RMS Norm 只作用于 Q 和 K，不作用于 V——因为只有 Q 和 K 参与 attention score 的计算
- 残差连接（residual connection）在 attention 输出归一化之后和最后一层归一化之后都必须添加
- gate_up 使用 `MergedColumnParallelLinear` 而非简单的 `ColumnParallelLinear`，是为了与预训练 checkpoint 的结构精确对齐

### Step 3：序列管理与内存块

这是 PagedAttention 的核心基础。三个关键类：

**Sequence**（`sequence.py`）：管理单个序列的全部信息——输入 prompt 和生成中不断增长的 token 序列。内部通过 `copy()` 复制 token_ids 列表，防止外部修改影响内部状态。

**Block**（`block_manager.py`）：表示一个固定大小的内存块，用于存储 KV Cache。关键概念是**引用计数（ref_count）**：跟踪有多少个序列正在使用该块。当多个序列共享前缀（prefix caching）时，ref_count 确保块不会被提前释放。

**BlockManager**：管理所有序列的 KV Cache 显存分配与释放。核心方法：

- `can_append()`：检查 GPU 上是否还有可用 block 空间
- `append()`：在 `can_append()` 返回 True 后实际分配新 block
- `allocate_with_cache()`：尝试复用已缓存块，只为未命中的 token 分配新空间
- `deallocate()`：递减 ref_count，为 0 时释放 block

**前缀缓存**（prefix caching）机制值得展开：当两个序列有相同的前缀 prompt 时，它们的 KV Cache 可以复用。BlockManager 通过计算 token 序列的哈希值来快速检测前缀是否已缓存——这是高吞吐量推理场景中的重要优化。

### Step 4：模型运行器（Model Runner）

这是推理引擎中最复杂的组件，对应 `src/myvllm/engine/model_runner.py`。包含六个核心子系统：

**数据准备**：`prepare_prefill()` 将多个序列的 token 合并为一个扁平列表，通过 `cu_seqlens_q/k` 累计序列长度标记边界——FlashAttention 要求单次 kernel launch 处理所有序列。`slot_mapping` 跟踪"哪个序列的哪个 token"写入哪个位置，是 PagedAttention 的关键数据结构。

**Pinned Memory**：在 `prepare_prefill()` 中使用 `pin_memory=True`。这是一种将物理内存页锁定（禁止 swap 到磁盘）的机制，使得 CPU 到 GPU 的 DMA 传输只需一次拷贝，而普通 pageable memory 需要两次。配合 `non_blocking=True` 实现异步传输，CPU 和 GPU 可以并行工作。

**CUDA Graph 优化**（`capture_cudagraph()`）：记录 CUDA kernel 执行序列以便快速回放，消除了每次 kernel 启动的 CPU 开销。为什么只在 decode 阶段使用？因为 decode 输入长度固定（每序列 1 个 token），而 prefill 输入长度变化，无法用单一图形覆盖。

**多卡通信**：通过 `read_shm()` 和 `write_shm()` 在 master 进程和 worker 进程之间使用共享内存传递数据，配合 `Event` 实现进程间同步信号。

### Step 5：调度器（Scheduler）

调度逻辑在 `src/myvllm/engine/scheduler.py` 中实现。核心策略：**Prefill 优先于 Decode**。调度器总是先尝试处理 waiting 队列中的新序列进行 prefill，只有当没有新 prefill 可加入时才调度 decode。

这个优先级策略背后有工程考量：prefill 的计算量远大于 decode，如果让 decode 先占满 GPU，prefill 会一直被推迟，导致首个 token 的响应时间（TTFT）变差。

当 GPU 显存不足以容纳更多序列时，调度器会**抢占**优先级最低的序列（通常是 decode 时间最长的）。

### Step 6：LLM Engine

顶层 API，封装了 Scheduler、ModelRunner 和请求管理。核心方法：

- `add_request()`：将 prompt 字符串转为 Sequence 对象，加入 waiting 队列
- `step()`：一次调度循环——调用 Scheduler 获取待运行序列 → ModelRunner 执行前向 → 更新序列状态
- `generate()`：推理主入口，重复调用 `step()` 直到所有序列生成完毕

## 3. 基准测试：FlashAttention vs PagedAttention

MinivLLM 提供了两个独立的基准测试脚本，分别在预填充和解码阶段测量不同注意力实现的性能差异。

### Prefilling 阶段（`benchmark_prefilling.py`）

对比三种实现：

| 实现 | 内存复杂度 | 说明 |
|------|-----------|------|
| PyTorch Standard | O(N²) | 传统注意力，生成完整注意力矩阵 |
| Naive Triton | O(N²) | GPU kernel，同样受共享内存限制（≤128 tokens） |
| FlashAttention | **O(N)** | 分块计算的在线 softmax 算法 |

FlashAttention 的核心思想是将注意力计算拆分为块，按块读取 K/V 并进行增量 softmax 计算，从而将显存复杂度从 O(N²) 降到 O(N)。这在长序列场景下是决定性优势——一个 4096 tokens 的序列，传统实现需要约 64M 个元素构成的注意力矩阵，而 FlashAttention 只需常数级显存。

### Decoding 阶段（`benchmark_decoding.py`）

解码阶段每步只处理 1 个新 token，但 KV Cache 已经积累到很长。三种实现：

| 实现 | 说明 |
|------|------|
| Naive PyTorch | 基于循环，使用分页 KV Cache |
| Optimized PyTorch | 向量化实现，批量 gathering 和 masking |
| Triton Kernel | 针对 PagedAttention decode 优化 |

解码阶段的关键挑战不是计算复杂度，而是**内存访问模式**。每生成一个 token，需要读取整个 KV Cache 中所有历史 token 的 K/V。PagedAttention 通过将 KV Cache 离散化到多个固定大小的 block 中，配合 block_table 索引，使得不同序列可以共享显存且不会产生碎片。

## 4. 安装与快速开始

```bash
# 安装 uv 包管理器
curl -LsSf https://astral.sh/uv/install.sh | sh

# 同步依赖
uv sync

# 运行推理引擎演示（使用随机初始化的 Qwen3-0.6B）
uv run python main.py

# 预填充阶段基准测试
uv run python benchmark_prefilling.py

# 解码阶段基准测试
uv run python benchmark_decoding.py
```

多卡运行只需在 `main.py` 的 config 中修改 `world_size` 为 n > 1 即可。

运行环境要求：Python ≥3.11（<3.12）、CUDA 可用的 GPU、依赖 transformers、torch、xxhash。

## 5. 项目结构一览

```
MinivLLM/
├── src/myvllm/
│   ├── models/          # 模型实现（Qwen3、LLaMa3.2）
│   ├── engine/
│   │   ├── sequence.py    # 序列管理与状态跟踪
│   │   ├── block_manager.py  # KV Cache 块管理 + 前缀缓存
│   │   ├── scheduler.py  # 调度逻辑
│   │   ├── model_runner.py  # 前向执行 + CUDA Graph
│   │   └── llm_engine.py  # 顶层 API
│   ├── layers/
│   │   ├── activation.py    # SiLU / GELU
│   │   ├── layernorm.py     # RMS LayerNorm
│   │   ├── linear.py       # 张量并行线性层
│   │   ├── embedding_head.py  # 词表嵌入 + LM Head
│   │   ├── attention.py    # 注意力机制
│   │   └── rotary_embedding.py  # RoPE
│   └── utils/           # 权重加载等工具
├── main.py              # 完整推理演示
├── benchmark_prefilling.py   # 预填充注意力对比
├── benchmark_decoding.py     # 解码注意力对比
└── HowToApproachvLLM_zh.md  # 配套中文学习指南
```

## 6. 技术亮点与适用场景

**这个项目适合谁：**

- 想深入理解 PagedAttention 和 KV Cache 管理机制的工程师
- 需要在特定硬件/场景下定制推理引擎的研究者
- 想学习 CUDA 编程中 Triton Kernel 编写的实践者
- 教授或学习 LLM 推理系统架构的课程项目

**不适合谁：**

- 需要直接投入生产环境的高性能推理方案（直接用 vLLM 或 SGLang）
- 没有 CUDA 基础的初学者（需要先补充 GPU 编程知识）

**值得关注的工程细节：**

1. **torch.compile vs CUDA Graph 的分工**：前者融合多个操作成单一 kernel，后者记录 kernel 执行序列消除启动开销——两者作用于不同层次，组合使用才能最大化推理效率

2. **张量并行的初始化顺序**：当 `world_size > 1` 时，`dist.init_process_group` 是一个集合屏障，Scheduler 必须在 ModelRunner 完全初始化后才能创建

3. **前缀缓存的哈希设计**：block 哈希时包含 prefix 参数，即使 tokens 序列相同，不同前缀上下文也产生不同哈希值，避免了跨会话的哈希碰撞

## 7. 延伸学习与练习

仓库提供了一个课程练习：读者可以在本地将 Llama-3.2-1B-Instruct 添加为第二个支持模型。这个练习只涉及四个文件的新增和修改（`llama.py`、`rotary_embedding.py`、`model_runner.py`、`main_llama32.py`），作者已给出了完整实现参考路径。

如果想要进一步深入，建议对照阅读：

- [vLLM 官方论文](https://arxiv.org/abs/2309.06119)——PagedAttention 的原始设计
- [FlashAttention 论文](https://arxiv.org/abs/2205.14135)——分块在线 softmax 的理论证明
- [HazyResearch FlashAttention 实现](https://github.com/HazyState/Flash-Attention)—— Triton 版本的具体优化思路

---

🦞 每日 08:00 自动更新

**数据来源**：Wenyueh/MinivLLM GitHub 仓库、HowToApproachvLLM_zh.md、README_zh.md、pyproject.toml
