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

vLLM 的工程实现经过多年优化，代码库已经膨胀到难以通读的程度。MinivLLM 做的事情是把这条实现路径还原成学习路径：从一个激活函数开始，逐层往上搭，直到拼出一个能跑通 Qwen3 的推理引擎。它的价值不在性能——作者明确说不要拿它上生产——而在于让读者能在一个仓库里读完 PagedAttention、张量并行、调度器、CUDA Graph 这些原本散落在 vLLM 各处的机制是怎么咬合的。

项目地址：[Wenyueh/MinivLLM](https://github.com/Wenyueh/MinivLLM)（721 Stars，98 Forks）。配套中文学习指南：[HowToApproachvLLM_zh.md](https://github.com/Wenyueh/MinivLLM/blob/main/HowToApproachvLLM_zh.md)。

读这篇文章之前需要一点前置知识：注意力机制、KV Cache 的概念、PyTorch 基本用法。读完之后你应该能回答三个问题——PagedAttention 为什么能减少显存碎片、Prefill 和 Decode 为什么需要不同的注意力实现、调度器为什么把 Prefill 排在 Decode 前面。

## 1. 这个项目解决什么问题

vLLM 是当前开源社区最流行的 LLM 推理框架之一，其核心技术 PagedAttention 源自 UVA 苏立德实验室的 [vLLM 论文](https://arxiv.org/abs/2309.06119)，借鉴操作系统的虚拟内存管理，把 KV Cache 切成固定大小的 block，从而大幅降低显存碎片和占用。问题在于，vLLM 本体经过多年工程迭代，理解门槛很高——光调度器一个文件就牵涉到抢占、重计算、前缀缓存、连续批处理多条相互耦合的逻辑。

MinivLLM 把这条路径压成六个步骤，每步只新增一个组件，每步都有对应代码和中文讲解。项目还附带两个基准测试脚本，分别测 Prefill 和 Decode 阶段不同注意力实现的性能差异：

- `benchmark_prefilling.py`：测输入 prompt 一次性计算注意力的吞吐和显存
- `benchmark_decoding.py`：测逐 token 生成时读取 KV Cache 的效率

理论学习和实验验证放在同一个仓库里，不用再到处找对照实验。

## 2. 系统总览：六个步骤拼出一个推理引擎

MinivLLM 的技术路径不是平铺的六个模块，而是一条自底向上的构建链——每一步在前一步的基础上新增职责。下图展示了从请求进入到 token 输出的完整数据流，以及六个 Step 在其中的位置。

```mermaid
flowchart TB
    subgraph Engine["Step 6: LLM Engine 顶层 API"]
        A["add_request(prompt)"] --> B["waiting 队列"]
        B --> C["step() 调度循环"]
    end

    subgraph Sched["Step 5: Scheduler 调度器"]
        C --> D{"waiting 队列有新序列?"}
        D -->|是| E["Prefill 优先"]
        D -->|否| F["Decode 批次"]
        E --> G["BlockManager 检查显存"]
        F --> G
        G --> H["分配/复用 KV Cache block"]
    end

    subgraph Runner["Step 4: Model Runner 前向执行"]
        H --> I["prepare_prefill/decode"]
        I --> J["Pinned Memory 异步传输"]
        J --> K["模型前向"]
        K --> L{"当前阶段?"}
        L -->|Prefill| M["FlashAttention"]
        L -->|Decode| N["PagedAttention + CUDA Graph"]
        M --> O["采样下一个 token"]
        N --> O
    end

    subgraph Lower["Step 1-3: 层 / 模型 / 序列与块"]
        K -.->. S1["Layers: RoPE/RMSNorm/Linear/Attention"]
        K -.->. S2["Model: Qwen3 组装"]
        H -.->. S3["Sequence + BlockManager"]
    end

    O --> P["更新 Sequence 状态"]
    P --> Q{"生成完成?"}
    Q -->|否| C
    Q -->|是| R["返回结果"]
```

六个 Step 的职责边界如下表，先记住分工，再进入细节会轻松很多。

| Step | 组件 | 解决的问题 | 关键文件 |
|------|------|-----------|----------|
| 1 | Layers | 神经网络基础结构块（含张量并行） | `src/myvllm/layers/` |
| 2 | Model | 把层组装成可前向的完整模型 | `src/myvllm/models/qwen3.py` |
| 3 | Sequence / Block | 序列状态跟踪与 KV Cache 显存管理 | `sequence.py`、`block_manager.py` |
| 4 | Model Runner | 数据准备、前向执行、CUDA Graph 捕获 | `model_runner.py` |
| 5 | Scheduler | Prefill/Decode 调度、抢占、显存仲裁 | `scheduler.py` |
| 6 | LLM Engine | 顶层 API 与请求生命周期 | `llm_engine.py` |

这里有一条容易混淆的边界：Step 3 的 BlockManager 管 KV Cache 的显存分配，Step 4 的 Model Runner 管 token 在前向时怎么写进这些 block。前者是"账本"，后者是"搬运工"，两者通过 `slot_mapping` 这个数据结构对接。

## 3. 一次推理请求如何流过系统

假设用户输入 `"中国的首都是"`，期望引擎生成 `"北京"`。一次完整请求的流转如下。

**第 1 步：请求进入。** 用户调用 `engine.add_request("中国的首都是")`。Engine 把字符串 tokenize 成 token id 列表，包装成 `Sequence` 对象，状态标记为 `waiting`，推入 waiting 队列。此时还没有任何 KV Cache 被分配。

**第 2 步：调度器决定批次。** `engine.generate()` 进入 `step()` 循环，调用 `scheduler.schedule()`。调度器看到 waiting 队列非空，且 GPU 显存够用，于是把这个序列选入 Prefill 批次。这里体现了"Prefill 优先"策略——只要还有新序列没做 prefill，就先做 prefill，不让 decode 占满 GPU。

**第 3 步：BlockManager 分配 KV Cache。** 调度器调用 `block_manager.can_append()` 检查显存，确认有足够 block 后，调用 `allocate_with_cache()` 为这个序列的 5 个 token 分配 KV Cache 空间。如果之前有其他序列用过相同前缀（比如系统提示词），这里会命中前缀缓存，直接复用已有 block，ref_count 加 1。

**第 4 步：Model Runner 准备数据。** `prepare_prefill()` 把 token 列表拍平成一维张量，计算 `cu_seqlens_q` 标记每个序列的边界（FlashAttention 要求单次 kernel launch 处理所有序列），并构建 `slot_mapping`——一个映射表，告诉后续 kernel "序列 i 的第 j 个 token 的 K/V 写到哪个 block 的哪个 slot"。token 张量通过 pinned memory 异步拷贝到 GPU。

**第 5 步：模型前向（Prefill 阶段）。** token 经过 embedding → RoPE → QKV 投影（张量并行切分）→ **FlashAttention**（分块在线 softmax，一次性算完整个 prompt 的注意力）→ MLP → LayerNorm → LM Head。注意 Prefill 阶段用的是 FlashAttention 而不是 PagedAttention，因为输入是连续的，没有分页必要。前向结束后得到 logits，采样得到第一个输出 token，比如 `"北"`。

**第 6 步：状态更新，转入 Decode。** Sequence 状态从 `waiting` 改为 `running`，新 token 追加到序列末尾。BlockManager 为新 token 对应的 K/V 调用 `append()` 写入已分配的 block。

**第 7 步：Decode 循环。** 下一轮 `step()` 中，调度器发现 waiting 为空，于是把 running 队列的序列组成 Decode 批次。Model Runner 这次走 `prepare_decode()`，每序列只输入 1 个 token，但需要读取所有历史 K/V。前向时切换到 **PagedAttention**——通过 `block_table` 索引离散存储的 KV Cache，配合 CUDA Graph 回放消除 kernel 启动开销。采样得到 `"京"`。

**第 8 步：终止。** 生成遇到 EOS token 或达到 max_tokens，Engine 把最终序列从 running 队列移除，返回 `"北京"`。

这条路径里有几个值得记住的切换点：waiting → running 的状态切换发生在 Prefill 完成后；FlashAttention → PagedAttention 的切换发生在阶段切换时；普通前向 → CUDA Graph 回放的切换只发生在 Decode 阶段。理解了这三个切换，就理解了 vLLM 调度的骨架。

## 4. 从层到 Engine：六步构建路径

### Step 1：层组件（Layers）

构建 LLM 最基础的结构块，对应 `src/myvllm/layers/` 下的六个模块。

**激活函数**（`activation.py`）实现 SiLU 和 GELU。作者在这里做了 `torch.compile` 的基准测试，发现它在大 Tensor 场景下能显著加速，但小 Tensor 反而因为编译开销拖慢性能。这个反直觉结论在 CUDA 编程里很常见——kernel 融合的收益要够大，才能盖过编译本身的开销。

**RMS LayerNorm**（`layernorm.py`）只用 RMS 均方根归一化，跳过均值中心化步骤，相比标准 LayerNorm 计算更轻量，对大模型训练稳定性有意义。

**线性层与张量并行**（`linear.py`）是这一步最复杂的部分，需要支持分布式训练。作者实现了四种并行线性层：

- `ColumnParallelLinear`：沿输出维度切分，多 GPU 并行计算，前向传播无需通信
- `RowParallelLinear`：沿输入维度切分，需要 `dist.all_reduce` 聚合部分结果
- `MergedColumnParallelLinear`：将 gate 和 up 两个投影合并，适合 MLP 层的高效权重加载
- `QKVColumnParallel`：Q/K/V 投影的特殊实现，每张 GPU 保留完整的 head，不切 head 维度

**词表嵌入与 LM Head**（`embedding_head.py`）的关键在于 `dist.gather` 和 `dist.all_gather` 的区别——前者只有目标 GPU 收到数据，后者所有 GPU 都收到。在张量并行中这决定了权重聚合的行为。

**注意力层**（`attention.py`）引入 FlashAttention 实现。作者特别讨论了 stride 概念：当张量存储在连续内存中时，沿着某个维度移动到下一个元素需要跳过多少个元素。理解 stride 是读懂 Triton Kernel 参数的关键——很多 kernel bug 不是算法错，而是 stride 算错导致读写错位。

**旋转位置编码 RoPE**（`rotary_embedding.py`）讨论了 base 参数对远距离位置编码的影响，以及 YARN 和 NTK 两种长上下文外推策略。

### Step 2：模型构建（Model）

`src/myvllm/models/qwen3.py` 把所有层组装为完整模型。几个设计决策值得注意：

- RMS Norm 只作用于 Q 和 K，不作用于 V——只有 Q 和 K 参与 attention score 计算，V 只做加权求和，归一化 V 没有几何意义
- 残差连接在 attention 输出归一化之后和最后一层归一化之后都必须添加，否则深层模型梯度会消失
- gate_up 使用 `MergedColumnParallelLinear` 而非简单的 `ColumnParallelLinear`，是为了与预训练 checkpoint 的结构精确对齐，否则权重加载会错位

### Step 3：序列管理与内存块

PagedAttention 的核心基础在这一步落地。三个关键类：

**Sequence**（`sequence.py`）管理单个序列的全部信息——输入 prompt 和生成中不断增长的 token 序列。内部通过 `copy()` 复制 token_ids 列表，防止外部修改影响内部状态。

**Block**（`block_manager.py`）表示一个固定大小的内存块，用于存储 KV Cache。关键概念是**引用计数（ref_count）**：跟踪有多少个序列正在使用该块。当多个序列共享前缀（prefix caching）时，ref_count 确保块不会被提前释放——这是 PagedAttention 能安全共享显存的前提。

**BlockManager** 管理所有序列的 KV Cache 显存分配与释放。核心方法：

- `can_append()`：检查 GPU 上是否还有可用 block 空间
- `append()`：在 `can_append()` 返回 True 后实际分配新 block
- `allocate_with_cache()`：尝试复用已缓存块，只为未命中的 token 分配新空间
- `deallocate()`：递减 ref_count，为 0 时释放 block

下面是 `BlockManager` 的核心接口示意，对照上面的方法名看职责边界：

```python
class BlockManager:
    def __init__(self, num_blocks: int, block_size: int):
        # num_blocks: GPU 上可分配的 block 总数
        # block_size: 每个 block 容纳多少个 token 的 K/V
        self.free_blocks: list[Block] = [Block(i) for i in range(num_blocks)]
        self.used_blocks: dict[int, Block] = {}

    def can_append(self, seq: Sequence) -> bool:
        # 判断是否还有空闲 block 容纳 seq 即将新增的 token
        return len(self.free_blocks) > 0

    def allocate_with_cache(self, token_ids: list[int], prefix_hash: int) -> list[Block]:
        # 前缀缓存命中则复用，未命中部分从 free_blocks 取新 block
        cached_blocks, missed_count = self._lookup_cache(prefix_hash, token_ids)
        new_blocks: list[Block] = []
        for _ in range(missed_count):
            block = self.free_blocks.pop()
            self.used_blocks[block.id] = block
            new_blocks.append(block)
        return cached_blocks + new_blocks

    def deallocate(self, block: Block) -> None:
        # 引用计数减 1，归零才真正归还到 free_blocks
        block.ref_count -= 1
        if block.ref_count == 0:
            self.free_blocks.append(block)
            del self.used_blocks[block.id]
```

`can_append` 只看 free_blocks 是否非空，`allocate_with_cache` 才真正动账本——这两个方法分开是为了让调度器先做一次轻量检查再决定是否把序列选入批次，避免选进来又分配不出的尴尬。

**前缀缓存**（prefix caching）机制值得展开：当两个序列有相同的前缀 prompt 时，它们的 KV Cache 可以复用。BlockManager 通过计算 token 序列的哈希值来快速检测前缀是否已缓存。哈希设计上有一个细节——block 哈希时包含 prefix 参数，即使 tokens 序列相同，不同前缀上下文也产生不同哈希值，避免跨会话的哈希碰撞。在多轮对话或系统提示词固定的场景下，这个优化能直接省掉重复的 prefill 计算。

### Step 4：模型运行器（Model Runner）

推理引擎中最复杂的组件，对应 `src/myvllm/engine/model_runner.py`，包含六个核心子系统。

**数据准备**：`prepare_prefill()` 将多个序列的 token 合并为一个扁平列表，通过 `cu_seqlens_q/k` 累计序列长度标记边界——FlashAttention 要求单次 kernel launch 处理所有序列。`slot_mapping` 跟踪"哪个序列的哪个 token"写入哪个位置，是 PagedAttention 的关键数据结构，把 BlockManager 的账本翻译成 kernel 能用的索引。

`prepare_prefill` 和 `prepare_decode` 的输入形状差异是后续切换注意力实现的根因，对照看更清楚：

```python
def prepare_prefill(self, seqs: list[Sequence]) -> PrefillInputs:
    # 多个序列的 prompt 拍平成一维张量，单次 kernel launch 处理
    flat_tokens: list[int] = []
    cu_seqlens_q: list[int] = [0]
    slot_mapping: list[int] = []
    for seq in seqs:
        flat_tokens.extend(seq.token_ids)
        cu_seqlens_q.append(cu_seqlens_q[-1] + len(seq.token_ids))
        # 把每个 token 映射到 BlockManager 分配的 (block_id, slot_in_block)
        slot_mapping.extend(self._compute_slots(seq))
    return PrefillInputs(
        tokens=tensor(flat_tokens, pin_memory=True),  # pinned memory 异步拷贝
        cu_seqlens_q=tensor(cu_seqlens_q),
        slot_mapping=tensor(slot_mapping),
    )

def prepare_decode(self, seqs: list[Sequence]) -> DecodeInputs:
    # 每个序列只输入上一步生成的 1 个 token，但需要读取全部历史 K/V
    last_tokens: list[int] = [seq.token_ids[-1] for seq in seqs]
    slot_mapping: list[int] = [self._compute_slots(seq)[-1] for seq in seqs]
    # block_table: 每个序列的 KV Cache 散落在哪些 block，按顺序索引
    block_table: list[list[int]] = [seq.block_ids for seq in seqs]
    return DecodeInputs(
        tokens=tensor(last_tokens, pin_memory=True),
        slot_mapping=tensor(slot_mapping),
        block_table=tensor(block_table),
    )
```

`prepare_prefill` 输出 `cu_seqlens_q` 给 FlashAttention 切分序列边界，`prepare_decode` 输出 `block_table` 给 PagedAttention 索引离散存储的 K/V——这两份输入决定了后续 kernel 走哪条路径。

**Pinned Memory**：在 `prepare_prefill()` 中使用 `pin_memory=True`。这是一种将物理内存页锁定（禁止 swap 到磁盘）的机制，使得 CPU 到 GPU 的 DMA 传输只需一次拷贝，而普通 pageable memory 需要两次。配合 `non_blocking=True` 实现异步传输，CPU 和 GPU 可以并行工作。

**CUDA Graph 优化**（`capture_cudagraph()`）记录 CUDA kernel 执行序列以便快速回放，消除每次 kernel 启动的 CPU 开销。为什么只在 decode 阶段使用？因为 decode 输入长度固定（每序列 1 个 token），形状稳定，可以捕获成一张图反复回放；prefill 输入长度随 prompt 变化，无法用单一图形覆盖。

**多卡通信**：通过 `read_shm()` 和 `write_shm()` 在 master 进程和 worker 进程之间使用共享内存传递数据，配合 `Event` 实现进程间同步信号。

### Step 5：调度器（Scheduler）

调度逻辑在 `src/myvllm/engine/scheduler.py` 中实现。核心策略是 **Prefill 优先于 Decode**：调度器总是先尝试处理 waiting 队列中的新序列进行 prefill，只有当没有新 prefill 可加入时才调度 decode。

这个优先级背后是 TTFT（Time To First Token，首个 token 响应时间）的考量。Prefill 的计算量远大于 decode，如果让 decode 先占满 GPU，prefill 会一直被推迟，用户感受到的延迟就是首字响应时间变长。在交互式场景下，TTFT 比 decode 吞吐更重要。

调度主循环的核心判断如下，对照"Prefill 优先"看更直观：

```python
def schedule(self) -> SchedulerOutputs:
    # 1. 先看 waiting 队列有没有新序列，且显存够不够做 prefill
    if self.waiting and self.block_manager.can_append(self._next_prefill_seq()):
        seq = self.waiting.popleft()
        seq.status = SequenceStatus.RUNNING
        self.running.append(seq)
        return SchedulerOutputs(
            scheduled=seq,
            stage="prefill",
            blocks_to_allocate=self.block_manager.allocate_with_cache(
                seq.token_ids, seq.prefix_hash
            ),
        )

    # 2. waiting 为空或显存不够，转 decode 批次
    if self.running:
        return SchedulerOutputs(
            scheduled=list(self.running),
            stage="decode",
        )

    # 3. 显存不够容纳新 prefill，且 running 队列也吃满了——抢占优先级最低的
    if self.waiting and not self.block_manager.can_append(self._next_prefill_seq()):
        victim = self._pick_victim()  # 通常选 decode 时间最长的
        self._preempt(victim)  # recompute 或 swap，MinivLLM 是简化版
        return self.schedule()  # 抢占后重试
```

`can_append` 是调度器和 BlockManager 之间的握手协议——调度器不直接看显存数字，只问"能不能塞下"，由 BlockManager 根据自己的账本回答。这种解耦让调度器可以专注于策略（先 prefill 还是先 decode、抢谁），把显存细节留给 BlockManager。

当 GPU 显存不足以容纳更多序列时，调度器会**抢占**优先级最低的序列（通常是 decode 时间最长的）。被抢占的序列有两种处理方式：重新计算（recompute）或换出（swap），MinivLLM 这里实现的是简化版。

### Step 6：LLM Engine

顶层 API，封装了 Scheduler、ModelRunner 和请求管理。核心方法：

- `add_request()`：将 prompt 字符串转为 Sequence 对象，加入 waiting 队列
- `step()`：一次调度循环——调用 Scheduler 获取待运行序列 → ModelRunner 执行前向 → 更新序列状态
- `generate()`：推理主入口，重复调用 `step()` 直到所有序列生成完毕

## 5. 基准测试：FlashAttention 与 PagedAttention 各测什么

MinivLLM 提供两个独立的基准测试脚本，分别在预填充和解码阶段测量不同注意力实现的性能差异。读这两个 benchmark 之前，先要搞清楚它们各自测的是系统的哪一部分，否则容易得出错误结论。

### Prefilling 阶段（`benchmark_prefilling.py`）

对比三种实现：

| 实现 | 内存复杂度 | 说明 |
|------|-----------|------|
| PyTorch Standard | O(N²) | 传统注意力，生成完整注意力矩阵 |
| Naive Triton | O(N²) | GPU kernel，同样受共享内存限制（≤128 tokens） |
| FlashAttention | **O(N)** | 分块计算的在线 softmax 算法 |

FlashAttention 把注意力计算拆分为块，按块读取 K/V 并进行增量 softmax 计算，从而将显存复杂度从 O(N²) 降到 O(N)。在长序列场景下这是决定性优势——一个 4096 tokens 的序列，传统实现需要约 64M 个元素构成的注意力矩阵，而 FlashAttention 只需常数级显存。

**这个 benchmark 测的是什么：** 长 prompt 一次性计算注意力时的吞吐和显存峰值。它反映的是 kernel 层面的计算效率——分块在线 softmax 是否真的能在 GPU 上跑出理论上的显存优势。

**不能推出什么：** 不能从这里推出 decode 阶段的性能。Decode 是内存访问受限（memory-bound），每步只算 1 个 token 但要读全部历史 K/V，瓶颈在显存带宽而不在计算密度。也不能推出端到端推理延迟——还要算上调度开销、采样时间、Python 层开销。

### Decoding 阶段（`benchmark_decoding.py`）

解码阶段每步只处理 1 个新 token，但 KV Cache 已经积累到很长。三种实现：

| 实现 | 说明 |
|------|------|
| Naive PyTorch | 基于循环，使用分页 KV Cache |
| Optimized PyTorch | 向量化实现，批量 gathering 和 masking |
| Triton Kernel | 针对 PagedAttention decode 优化 |

解码阶段的关键挑战不是计算复杂度，而是**内存访问模式**。每生成一个 token，需要读取整个 KV Cache 中所有历史 token 的 K/V。PagedAttention 通过将 KV Cache 离散化到多个固定大小的 block 中，配合 `block_table` 索引，使得不同序列可以共享显存且不会产生碎片。

**这个 benchmark 测的是什么：** 分页内存访问模式下的 kernel 效率。它反映的是 PagedAttention 的 block_table 索引、gather 操作、跨 block 读取是否被 Triton kernel 优化到位。

**不能推出什么：** 不能推出多序列并发下的吞吐。这个 benchmark 通常是单序列或固定 batch，而真实推理的吞吐提升来自连续批处理（continuous batching）和前缀缓存，那些是调度器和 BlockManager 的功劳，不在 decode kernel 测量范围内。

### 两个 benchmark 的关系

把两个 benchmark 放在一起看，能发现 vLLM 设计的一个核心拆分：Prefill 用 FlashAttention（计算密集，吃 GPU 算力），Decode 用 PagedAttention（内存密集，吃显存带宽和分页索引效率）。这种拆分源于两个阶段瓶颈的根本不同——用同一个 kernel 跑两个阶段，必然有一个阶段被浪费。

## 6. 安装与快速开始

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

### 常见问题

**`uv sync` 失败提示 CUDA 版本不匹配。** PyTorch 的 CUDA 版本要和系统驱动对齐。先 `nvidia-smi` 看驱动支持的 CUDA 版本，再在 `pyproject.toml` 里选对应的 torch wheel。MinivLLM 默认配置不一定匹配你的机器。

**多卡运行卡在 `dist.init_process_group`。** 这是一个集合屏障，所有 worker 必须同时到达。检查 `world_size` 是否和实际启动的进程数一致，以及 master 端口的占用情况。Scheduler 必须在 ModelRunner 完全初始化后才能创建，初始化顺序错了会死锁。

**前缀缓存没命中预期。** 哈希计算包含 prefix 参数，相同 token 序列在不同前缀上下文下会产生不同哈希。如果跨会话没命中，先确认 prefix 参数是否真的相同，而不是只看 token 内容。

## 7. 项目结构一览

```text
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

## 8. 适用边界与采用建议

**谁应该读这个项目：**

- 想深入理解 PagedAttention 和 KV Cache 管理机制的工程师——这是 vLLM 论文之外最直接的代码路径
- 需要在特定硬件/场景下定制推理引擎的研究者——可以拿 MinivLLM 当脚手架，不用从 vLLM 庞杂的代码里找入口
- 想学习 Triton Kernel 编写的实践者——`benchmark_decoding.py` 里的 Triton 实现是很好的参考
- 教授或学习 LLM 推理系统架构的课程项目——六步路径天然适合教学

**谁不应该用这个项目：**

- 需要直接投入生产环境的高性能推理——直接用 vLLM 或 SGLang，它们有更完善的量化、分布式、监控支持
- 没有 CUDA 基础的初学者——先补 GPU 编程和 PyTorch 分布式基础，否则会在张量并行和 Triton 部分卡住

**采用顺序建议：** 如果目标是理解 vLLM，先跑通 `main.py` 看整体流程，再按 Step 1→6 顺序读代码，配合 `HowToApproachvLLM_zh.md`。如果目标是定制引擎，先读 Step 3（BlockManager）和 Step 5（Scheduler），这两块是 vLLM 调度的核心，也是定制最常发生的地方。如果目标是写 Triton kernel，直接看 `benchmark_decoding.py` 的三种实现对比，从 Naive PyTorch 版本入手，理解分页索引后再看 Triton 优化版。

**几个值得记住的工程细节：**

1. **torch.compile 与 CUDA Graph 的分工**：前者融合多个操作成单一 kernel，后者记录 kernel 执行序列消除启动开销。两者作用于不同层次——torch.compile 优化 kernel 内部，CUDA Graph 优化 kernel 之间的调度开销，组合使用才能覆盖两个层面的开销。

2. **张量并行的初始化顺序**：当 `world_size > 1` 时，`dist.init_process_group` 是一个集合屏障，Scheduler 必须在 ModelRunner 完全初始化后才能创建，否则会死锁在屏障上。

3. **前缀缓存的哈希设计**：block 哈希时包含 prefix 参数，即使 tokens 序列相同，不同前缀上下文也产生不同哈希值，避免跨会话的哈希碰撞。这个设计在多轮对话场景下尤其重要。

## 9. 延伸学习与练习

仓库提供了一个课程练习：读者可以在本地将 Llama-3.2-1B-Instruct 添加为第二个支持模型。这个练习只涉及四个文件的新增和修改（`llama.py`、`rotary_embedding.py`、`model_runner.py`、`main_llama32.py`），作者已给出了完整实现参考路径。做完这个练习能验证你是否理解了 Step 1-2 的层组件如何复用。

如果想要进一步深入，建议对照阅读：

- [vLLM 官方论文](https://arxiv.org/abs/2309.06119)——PagedAttention 的原始设计，重点看 block table 和引用计数部分
- [FlashAttention 论文](https://arxiv.org/abs/2205.14135)——分块在线 softmax 的理论证明，理解为什么分块不会损失精度
- [HazyResearch FlashAttention 实现](https://github.com/HazyState/Flash-Attention)——Triton 版本的具体优化思路

读完 MinivLLM 后，建议对照 vLLM 本体的 `scheduler.py` 和 `block_manager.py` 阅读生产场景的边界处理——多租户隔离、动态批大小、量化兼容性这些工程优化在 vLLM 中有完整实现，可以按需挑选模块深入。如果要做定制引擎，先从 Step 3 和 Step 5 入手改起，这两块是 vLLM 调度的核心，也是定制最常发生的位置。

---

🦞 每日 08:00 自动更新

**数据来源**：Wenyueh/MinivLLM GitHub 仓库、HowToApproachvLLM_zh.md、README_zh.md、pyproject.toml
