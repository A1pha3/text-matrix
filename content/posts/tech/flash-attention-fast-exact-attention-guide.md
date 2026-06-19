---
title: "Flash Attention：40K Stars·Tri Dao发明·2-4倍加速·O(N)内存"
date: "2026-04-12T02:31:39+08:00"
slug: flash-attention-fast-exact-attention-guide
description: "Flash Attention 是由 Tri Dao 发明的 Transformer 注意力机制加速算法，可实现 2-4 倍加速，内存复杂度从 O(N²) 降为 O(N)，被 Llama、Mistral、CodeLlama 等模型内置采用。"
draft: false
categories: ["技术笔记"]
tags: ["Flash Attention", "Transformer", "注意力机制", "深度学习", "GPU"]
---

# Flash Attention：把注意力从 HBM 带宽瓶颈里捞出来

> **目标读者**：大模型训练/推理工程师、CUDA 内核爱好者、Transformer 优化方向的研究者
> **预计阅读时间**：50-70 分钟
> **前置知识**：标准 Attention 公式、GPU 内存层级（SRAM/HBM）、PyTorch 基础
> **难度定位**：⭐⭐⭐ 中高级，需要理解 GPU 内存层级

## 这篇文章的判断

Flash Attention 不是一种近似注意力算法。它把标准 Attention 的计算重排成对 GPU 内存层级友好的形态：在片上 SRAM 里完成 softmax 与加权求和，避免把 N×N 的中间矩阵写回 HBM 再读回来。同一组数学运算，内存复杂度从 O(N²) 降到 O(N)，A100 上 2-4 倍墙钟时间加速，与标准 Attention 在数学上等价（FP16 下误差通常 < 1e-3）。

瓶颈是 HBM 带宽而不是 FLOPs——看清这一点，后面所有设计选择都有了着落：为什么 tiling 必须配 online softmax、为什么 FA2 要重新切分 warp、为什么 FA3 在 H100 上要靠 warp-specialization 把 matmul 和 softmax 重叠起来。

文章覆盖 FA1/FA2/FA3 三代的原理差异、安装与 API 调用、与 HuggingFace/xFormers/Megatron-LM 的集成、benchmark 怎么读、训练与推理场景的注意点、常见报错排查。CUTLASS 内核细节、Triton 实现版本、Flash Attention-4（Blackwell 专属，仍在快速迭代）不在范围内。

**学习路径建议**：先读"标准 Attention 的瓶颈在哪里"和"Tiling + Online Softmax"两节建立直觉，再按需跳到安装、API、集成、排查等实操章节。如果只关心怎么用，可以直接从"安装与环境验证"读起；如果要做内核优化，前两节是基础。

## 标准 Attention 的瓶颈在哪里

先把标准 Attention 写出来，再看它在哪里把 GPU 用废了。

```python
import torch
import torch.nn.functional as F

def standard_attention(Q, K, V, scale=None):
    """
    Q, K, V: (batch, seq_len, d_k)
    """
    d_k = Q.size(-1)
    if scale is None:
        scale = d_k ** -0.5

    # Step 1: 计算注意力分数
    scores = torch.matmul(Q, K.transpose(-2, -1)) * scale
    # scores: (batch, seq_len, seq_len) — 完整 N×N 矩阵驻留 HBM

    # Step 2: Softmax
    attn_weights = F.softmax(scores, dim=-1)
    # attn_weights: 同样是 N×N，再次读写 HBM

    # Step 3: 加权求和
    outputs = torch.matmul(attn_weights, V)

    return outputs
```

三行代码里，`scores` 和 `attn_weights` 都是 `(batch, seq_len, seq_len)` 的张量，对 LLaMA-7B 训练时常见的 `seq_len=4096`、`batch=8`、`heads=32`、`head_dim=128` 配置，单个 `attn_weights` 就是 8 × 32 × 4096 × 4096 × 2 bytes ≈ 8 GB 的 FP16 矩阵，要写一次、读一次，再写一次。

A100 的 HBM 带宽是 1.9 TB/s，H100 是 3.35 TB/s。这些数字看起来很大，但除以一次 attention 里要搬运的 N² 数据量，墙钟时间就上去了。FLOPs 反而不是瓶颈——A100 的 Tensor Core 算力是 312 TFLOPS（FP16），算 QK^T 和 PV 的 FLOPs 用不了那么多时间。

```mermaid
flowchart LR
    subgraph HBM ["HBM (大但慢: A100 1.9 TB/s)"]
        Q["Q<br/>(B, N, d)"]
        K["K<br/>(B, N, d)"]
        V["V<br/>(B, N, d)"]
        S["S = QK^T<br/>(B, N, N) — 写一次"]
        P["P = softmax(S)<br/>(B, N, N) — 读一次写一次"]
        O["O = PV<br/>(B, N, d) — 读一次"]
        Q --> S
        K --> S
        S --> P
        P --> O
        V --> O
    end

    subgraph SRAM ["SRAM (小但快: A100 192 KB/SM)"]
        Empty["片上几乎没干活<br/>只做了一次 matmul 调用"]
    end

    HBM -.频繁读写.-> SRAM

    style S fill:#fecaca,stroke:#ef4444
    style P fill:#fecaca,stroke:#ef4444
    style HBM fill:#dbeafe,stroke:#3b82f6
    style SRAM fill:#fef3c7,stroke:#f59e0b
```

红色标记的两个 N×N 矩阵是 HBM 带宽的主要消耗者。Flash Attention 要解决的就是这两个矩阵的来回搬运。

## Tiling + Online Softmax：怎么把 O(N²) 内存压到 O(N)

既然把 N×N 矩阵留在 HBM 是问题所在，能不能根本不 materialize 这个矩阵？难点在 softmax。softmax 的分母是 `sum(exp(scores))`，要算这个分母必须看到整行 scores。如果按块（tile）算 QK^T，每块算完就丢，怎么保证 softmax 的全局归一化？

Flash Attention 的解法是 **online softmax**（也叫 streaming softmax）。把 softmax 拆成两步：先维护每行的 running max `m` 和 running sum `l`，每来一个新的 score block 就更新 `m` 和 `l`，并对之前累积的输出做一次 rescale。所有 block 走完，输出就是正确的 softmax 加权结果。

数学上等价，中间不再需要把 N×N 矩阵写回 HBM。

下面这段伪代码展示了一次 attention 计算如何在 SRAM/HBM 间流转。这不是 FA 的真实 CUDA 实现——真实实现要处理 warp 分配、shared memory bank conflict、TMA 加载等大量细节，这里只展示数据流。

```python
def flash_attention_tiled(Q, K, V, block_size=64):
    """
    Flash Attention 数据流伪代码（非真实 CUDA 实现）
    关键点：N×N 矩阵永远不离开 SRAM
    """
    batch_size, seq_len, d_k = Q.shape

    # 输出和归一化因子都驻留 HBM，但只有 O(N) 大小
    outputs = torch.zeros_like(Q)
    l = torch.zeros((batch_size, seq_len, 1))      # running sum
    m = torch.full((batch_size, seq_len, 1), -float('inf'))  # running max

    for i in range(0, seq_len, block_size):
        # 从 HBM 加载一个 Q block 到 SRAM
        Q_block = Q[:, i:i+block_size, :]          # (B, Br, d)
        m_i = m[:, i:i+block_size, :]              # 当前 block 的 running max
        l_i = l[:, i:i+block_size, :]              # 当前 block 的 running sum
        O_i = outputs[:, i:i+block_size, :]        # 当前 block 的 running output

        for j in range(0, seq_len, block_size):
            # 从 HBM 加载 K, V block 到 SRAM
            K_block = K[:, j:j+block_size, :]
            V_block = V[:, j:j+block_size, :]

            # === 以下全部在 SRAM 内完成 ===
            # 计算 block scores
            S_ij = torch.matmul(Q_block, K_block.transpose(-2, -1)) / (d_k ** 0.5)

            # online softmax 更新
            m_ij = torch.maximum(m_i, S_ij.amax(dim=-1, keepdim=True))
            P_ij = torch.exp(S_ij - m_ij)
            l_i = l_i * torch.exp(m_i - m_ij) + P_ij.sum(dim=-1, keepdim=True)

            # rescale 之前的输出，加上当前 block 的贡献
            O_i = O_i * torch.exp(m_i - m_ij) + torch.matmul(P_ij, V_block)
            m_i = m_ij
            # === SRAM 部分结束 ===

        # 只把最终结果写回 HBM，N×N 矩阵从未离开 SRAM
        outputs[:, i:i+block_size, :] = O_i / l_i
        m[:, i:i+block_size, :] = m_i
        l[:, i:i+block_size, :] = l_i

    return outputs
```

```mermaid
flowchart TB
    subgraph HBM ["HBM"]
        Qfull["Q (B, N, d)<br/>常驻"]
        Kfull["K (B, N, d)<br/>常驻"]
        Vfull["V (B, N, d)<br/>常驻"]
        Ofull["O (B, N, d)<br/>流式写回"]
        Mfull["m, l (B, N, 1)<br/>流式写回"]
    end

    subgraph SRAM ["SRAM (每 SM ~192 KB)"]
        Qb["Q_i block<br/>(Br, d)"]
        Kb["K_j block<br/>(Bc, d)"]
        Vb["V_j block<br/>(Bc, d)"]
        S["S_ij = Q_i K_j^T<br/>(Br, Bc) — 不写回"]
        P["P_ij = exp(S_ij - m)<br/>(Br, Bc) — 不写回"]
        Oacc["O_i 累加器<br/>(Br, d)"]
        ML["m_i, l_i<br/>(Br, 1)"]
    end

    Qfull -->|逐块加载| Qb
    Kfull -->|逐块加载| Kb
    Vfull -->|逐块加载| Vb
    Qb --> S
    Kb --> S
    S --> P
    P --> Oacc
    Vb --> Oacc
    Oacc -->|block 结束写回| Ofull
    ML -->|block 结束写回| Mfull

    style S fill:#fecaca,stroke:#ef4444
    style P fill:#fecaca,stroke:#ef4444
    style HBM fill:#dbeafe,stroke:#3b82f6
    style SRAM fill:#fef3c7,stroke:#f59e0b
```

红色部分是关键：S_ij 和 P_ij 这两个 N×N 的中间量只在 SRAM 内存在一个 block 的时间，算完就丢，从不写回 HBM。O(N²) → O(N) 内存复杂度就是从这里来的。

tiling 降内存靠的不是减少计算量（FLOPs 不变），而是把 N×N 矩阵的"生命周期"压缩到一个 block 内，不再需要 HBM 来暂存。IO 感知之所以关键，是因为标准 Attention 的墙钟时间主要花在 HBM 读写 N×N 矩阵上，而不是 FLOPs 上。这两点合起来，就是 Flash Attention 的全部核心。

## 项目快照

| 属性 | 值 |
|------|-----|
| 仓库 | github.com/Dao-AILab/flash-attention |
| Stars | 40.2k |
| Forks | 3.3k |
| 贡献者 | 202 |
| 最新版本 | 3.4（2026-03-20） |
| 许可证 | BSD-3-Clause |
| 语言占比 | CUDA 60.4% / Python 21.8% / C++ 17.4% |
| 作者 | Tri Dao（Stanford 博士，Together AI 首席科学家，2024 年 9 月起任 Princeton 计算机科学助理教授） |

数字给个量级感即可。Stars 多说明生态接受度高，但和性能没有直接关系——性能要看后面 benchmark 段的测量条件。

## 三代演进：每一代在解决什么

三代差异的核心在于：每一代挪走了一个不同的瓶颈。

| 版本 | 主要瓶颈 | 解决方式 | 相对前代加速 |
|------|----------|----------|--------------|
| FA1 | HBM 带宽（N×N 矩阵来回搬运） | Tiling + online softmax | 2-4x vs 标准 Attention |
| FA2 | GPU 占用率低（只沿 seq 维度并行） | 沿 batch 和 seq 双维度并行，重切 warp | 1.5-2x vs FA1 |
| FA3 | H100 的 Tensor Core 利用率低（~35%） | warp-specialization 重叠 matmul 与 softmax，FP8 低精度 | 1.5-2x vs FA2（FP16），FP8 再多 ~1.2x |

FA1 解决的是 HBM 带宽问题。FA2 解决的是 GPU 占用率问题——FA1 只在 sequence 维度做并行，长序列时 batch 维度闲置；FA2 把并行扩展到 batch × seq，并重新分配 warp，让每个 warp 干的活更均衡。FA3 解决的是 Hopper 架构的 Tensor Core 利用率问题——FA2 在 H100 上只能跑到 ~35% 的理论 FP16 峰值，FA3 通过 warp-specialization（一部分 warp 专门做 matmul，另一部分专门做 softmax，两者重叠）和异步数据搬运（利用 TMA 指令），把 H100 的 FP16 利用率推到 ~75%，FP8 推到更高。

FA3 仍然是精确算法，不是近似算法。它的 FP8 模式因为低精度量化会引入数值误差，但这和"近似注意力算法"（如 Linformer、Performer 通过数学近似降低复杂度）是两回事。FA3 的 FP16/BF16 路径与标准 Attention 数学等价。

## 安装与环境验证

### 环境要求

| 要求 | 说明 |
|------|------|
| GPU | NVIDIA GPU（H100、A100、RTX 3090/4090、V100 等） |
| CUDA | 11.6+ 或 12.1+ |
| PyTorch | 2.0+ |
| Python | 3.8+ |

不支持 CPU。不支持 AMD GPU（社区有 ROCm 移植，但非官方维护）。V100（sm_70）能用 FA1/FA2，FA3 需要 Hopper（sm_90）。

### 安装方式

```bash
# 方式一：pip 安装（推荐，预编译 wheel）
pip install flash-attn

# 方式二：从源码安装（需要 CUDA toolkit，编译耗时 10-30 分钟）
git clone https://github.com/Dao-AILab/flash-attention.git
cd flash-attention
pip install .
```

不同 GPU 架构的安装差异主要在 wheel 来源：

```bash
# RTX 3090 / A100 (sm_80 / sm_86) — 标准 pip 即可
pip install flash-attn --no-build-isolation

# H100 (sm_90) — 用官方 wheel 仓库拉对应版本
pip install flash-attn --no-build-isolation --index-url https://wheels.flash-attention.com/3.4/

# Docker（避免本地 CUDA 版本冲突）
docker run --gpus all -it ghcr.io/dao-aeilab/flash-attention:latest
```

`--no-build-isolation` 的作用是让 pip 用当前环境里已装的 PyTorch 来编译扩展，而不是新建一个隔离环境去拉 PyTorch——后者经常因为版本不匹配导致编译失败。

### 验证安装

```python
import torch
from flash_attn import flash_attn_func

# 检查版本
import flash_attn
print(flash_attn.__version__)  # 期望: 3.4.x 或 2.x.x

# 检查 CUDA 可用性
print(torch.cuda.is_available())           # True
print(torch.cuda.get_device_name(0))       # NVIDIA A100-SXM4-80GB / H100 / ...

# 跑一次最小用例，确认 kernel 能加载
Q = torch.randn(2, 64, 32, dtype=torch.float16, device='cuda')
K = torch.randn(2, 64, 32, dtype=torch.float16, device='cuda')
V = torch.randn(2, 64, 32, dtype=torch.float16, device='cuda')
out = flash_attn_func(Q, K, V)
print(out.shape)  # torch.Size([2, 64, 32])
```

如果 `flash_attn_func` 导入失败但 `pip list` 显示已安装，多半是 CUDA 版本和编译时的 CUDA 版本不匹配。`nvidia-smi` 看驱动支持的 CUDA 版本，`nvcc --version` 看编译器版本，两者要兼容。

## API 与典型调用

### 基础调用：`flash_attn_func`

```python
import torch
from flash_attn import flash_attn_func

# 张量形状: (batch_size, seq_len, num_heads, head_dim)
Q = torch.randn(2, 64, 8, 64, dtype=torch.float16, device='cuda')
K = torch.randn(2, 64, 8, 64, dtype=torch.float16, device='cuda')
V = torch.randn(2, 64, 8, 64, dtype=torch.float16, device='cuda')

# 前向计算
output = flash_attn_func(Q, K, V, dropout_p=0.0, causal=False)
print(output.shape)  # torch.Size([2, 64, 8, 64])
```

注意张量形状是 `(batch, seq, heads, head_dim)`，不是 PyTorch 常见的 `(batch, heads, seq, head_dim)`。这是 FA 的约定，调用前别 transpose 错。

### 与标准 Attention 的误差对比

```python
def standard_attention(Q, K, V):
    # Q, K, V: (batch, seq, heads, head_dim) → 转成 (batch, heads, seq, head_dim)
    Q = Q.transpose(1, 2)
    K = K.transpose(1, 2)
    V = V.transpose(1, 2)
    d_k = Q.size(-1)
    scores = torch.matmul(Q, K.transpose(-2, -1)) / (d_k ** 0.5)
    return torch.matmul(torch.softmax(scores, dim=-1), V).transpose(1, 2)

standard_out = standard_attention(Q, K, V)
flash_out = flash_attn_func(Q, K, V)

diff = (flash_out.float() - standard_out.float()).abs().max()
print(f"Max difference: {diff.item():.6f}")  # 通常 < 1e-3
```

误差来源是 FP16 累加顺序不同，算法本身是精确的。换 BF16 误差会更小，换 FP32 会几乎为 0（但 FA 不直接支持 FP32）。

### QKV 打包格式：`flash_attn_qkvpacked_func`

当 Q、K、V 来自同一个输入投影且 head_dim 相同时，打包成单个张量更高效——少一次 kernel launch，少一次 HBM 读写。

```python
from flash_attn import flash_attn_qkvpacked_func

# qkv: (batch, seq, 3, heads, head_dim)
qkv = torch.randn(2, 64, 3, 8, 64, dtype=torch.float16, device='cuda')

output = flash_attn_qkvpacked_func(qkv, dropout_p=0.0, causal=False)
print(output.shape)  # torch.Size([2, 64, 8, 64])
```

### 变长序列：`flash_attn_varlen_func`

训练时一个 batch 里序列长度不一，常规做法是 pad 到最长再算，padding 部分浪费算力。`flash_attn_varlen_func` 用 `cu_seqlens`（累积长度）把多个变长序列拼成一个长张量，跳过 padding。

```python
from flash_attn import flash_attn_varlen_func

# 假设 batch 内有 2 个序列，长度分别为 3 和 5，拼成 8 长的张量
# cu_seqlens 是累积长度的首尾哨兵，类似 CSR 格式的行指针
cu_seqlens_q = torch.tensor([0, 3, 8], dtype=torch.int32, device='cuda')
cu_seqlens_k = torch.tensor([0, 3, 8], dtype=torch.int32, device='cuda')

Q = torch.randn(8, 8, 64, dtype=torch.float16, device='cuda')  # (total_seq, heads, head_dim)
K = torch.randn(8, 8, 64, dtype=torch.float16, device='cuda')
V = torch.randn(8, 8, 64, dtype=torch.float16, device='cuda')

output = flash_attn_varlen_func(
    Q, K, V,
    cu_seqlens_q=cu_seqlens_q,
    cu_seqlens_k=cu_seqlens_k,
    max_seqlen_q=5,
    max_seqlen_k=5,
    dropout_p=0.0,
    causal=False,
)
print(output.shape)  # torch.Size([8, 8, 64])
```

`cu_seqlens` 的语义：`[0, 3, 8]` 表示第 0 个序列占索引 0-2（长度 3），第 1 个序列占索引 3-7（长度 5）。`max_seqlen_q` 是 batch 内最长序列长度，用于 kernel 内部 block 大小选择。

## 与主流框架集成

### Hugging Face Transformers

Transformers 内置了 Flash Attention 后端，通过 `attn_implementation` 参数切换：

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model_name = "meta-llama/Llama-2-7b-hf"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto",
    attn_implementation="flash_attention_2",  # 显式指定 FA2 后端
)

inputs = tokenizer("Hello, world!", return_tensors="pt").to("cuda")
outputs = model.generate(**inputs, max_new_tokens=100)
```

`attn_implementation` 的可选值：`eager`（标准 PyTorch 实现）、`sdpa`（PyTorch 2.0 的 scaled_dot_product_attention，内部可能调 FA）、`flash_attention_2`（显式 FA2）。如果 `flash-attn` 包没装，指定 `flash_attention_2` 会直接报错；如果只指定 `sdpa`，PyTorch 会根据硬件自动选择后端。

### xFormers

xFormers 的 `memory_efficient_attention` 是另一条路径，内部会根据硬件和输入形状选择 FA 或自家的 cutlass 内核：

```python
from xformers.ops import memory_efficient_attention

# xFormers 期望 (batch, heads, seq, head_dim) 形状
Q = Q.transpose(1, 2)
K = K.transpose(1, 2)
V = V.transpose(1, 2)

output = memory_efficient_attention(Q, K, V, attn_bias=None, p=0.0)
```

xFormers 和 `flash-attn` 包不需要同时装。如果两个都装了，Transformers 默认走 `flash-attn`。

### Megatron-LM

Megatron-LM 在 `megatron.core.extensions` 里有 Flash Attention 的封装，通过 config 字段开启：

```python
# 在 Megatron config 里
# attention_backend = "flash"  # 或 "unpad", "local"
```

具体字段名随 Megatron 版本变化，以仓库 `megatron/core/transformer/attention.py` 的实现为准。Mistral、CodeLlama 这类模型在 HuggingFace 上的实现走的是 Transformers 路径，不是 Megatron。

## Benchmark 怎么读

下面这组数字来自 FA 论文与官方仓库的典型测量条件。读 benchmark 时先看测的是什么。

### 速度对比

| 配置 | 标准 Attention | Flash Attention | 加速比 |
|------|---------------|-----------------|--------|
| A100-80GB（FP16, seq=4096） | ~100 ms | ~25 ms | ~4x |
| H100-SXM（FP16, seq=4096） | ~100 ms | ~17 ms（FA3） | ~6x |
| RTX 3090（FP16, seq=2048） | ~100 ms | ~40 ms | ~2.5x |

### 内存对比

| 序列长度 | 标准 Attention（N×N 矩阵） | Flash Attention | 内存节省 |
|----------|---------------------------|-----------------|----------|
| 512 | ~1 GB | ~256 MB | ~4x |
| 2048 | ~16 GB | ~1 GB | ~16x |
| 4096 | ~64 GB | ~4 GB | ~16x |

### 这些数字测的是什么

- **测的是**：单次 attention 前向计算的墙钟时间，包含 HBM 读写和 Tensor Core 计算。`seq_len` 固定，`batch` 和 `heads` 固定，FP16 精度，causal mask 关闭。
- **反映的是**：HBM 带宽利用率和 Tensor Core 占用率的综合表现。FA 的加速主要来自减少 HBM 读写，所以序列越长（N² 增长越快），加速比越明显。
- **不能推出什么**：
  - 不能直接推出端到端训练速度提升。训练里 attention 只占总时间的一部分（通常 20-40%），FFN 和优化器通信也占大头。FA 把 attention 部分加速 4x，端到端可能只快 1.2-1.5x。
  - 不能推出推理场景的加速比。推理时 `seq_len` 短、batch 小，FA 的优势不明显，甚至可能因为 kernel launch 开销变慢。
  - 不能跨 GPU 架构外推。H100 上的 6x 是 FA3 用了 Hopper 专属指令（TMA、warp-specialization）的结果，A100 上跑 FA3 拿不到这个数。

### 自己测一次

```python
import torch
import time
from flash_attn import flash_attn_func

def benchmark_attention(seq_len, batch_size=4, heads=16, head_dim=64, repeats=100):
    Q = torch.randn(batch_size, seq_len, heads, head_dim,
                    dtype=torch.float16, device='cuda')
    K = torch.randn(batch_size, seq_len, heads, head_dim,
                    dtype=torch.float16, device='cuda')
    V = torch.randn(batch_size, seq_len, heads, head_dim,
                    dtype=torch.float16, device='cuda')

    # Warmup — 必须做，第一次调用包含 JIT 编译和缓存加载
    for _ in range(10):
        _ = flash_attn_func(Q, K, V)
    torch.cuda.synchronize()

    # 测量
    start = time.time()
    for _ in range(repeats):
        _ = flash_attn_func(Q, K, V)
    torch.cuda.synchronize()
    elapsed = (time.time() - start) / repeats * 1000  # ms
    return elapsed

for seq_len in [512, 1024, 2048, 4096, 8192]:
    ms = benchmark_attention(seq_len)
    print(f"Seq len {seq_len:>5}: {ms:.2f} ms")
```

Warmup 这一步不能省。FA 第一次调用时会根据输入形状和硬件选择 kernel 配置，这部分时间不算在实际性能里。`torch.cuda.synchronize()` 也不能省，否则测的是 launch 时间而不是执行时间。

## 训练场景的注意点

### 自定义 Attention 层

在自己的模型里用 FA，关键是把 Q/K/V 投影后的张量形状整理成 FA 期望的 `(batch, seq, heads, head_dim)`：

```python
import torch
import torch.nn as nn
from flash_attn import flash_attn_func

class FlashAttentionLayer(nn.Module):
    def __init__(self, d_model, num_heads):
        super().__init__()
        self.d_model = d_model
        self.num_heads = num_heads
        self.head_dim = d_model // num_heads

        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)

    def forward(self, x, causal=False):
        batch_size, seq_len, _ = x.shape

        # 投影后直接 reshape 成 (batch, seq, heads, head_dim)
        # 不需要 transpose 到 (batch, heads, seq, head_dim)
        Q = self.W_q(x).view(batch_size, seq_len, self.num_heads, self.head_dim)
        K = self.W_k(x).view(batch_size, seq_len, self.num_heads, self.head_dim)
        V = self.W_v(x).view(batch_size, seq_len, self.num_heads, self.head_dim)

        attn_output = flash_attn_func(Q, K, V, dropout_p=0.0, causal=causal)

        # 恢复成 (batch, seq, d_model)
        attn_output = attn_output.view(batch_size, seq_len, self.d_model)
        return self.W_o(attn_output)
```

### 反向传播

FA 的反向传播也是 IO-aware 的，会重新计算前向的中间量（recomputation），而不是存 checkpoint。反向传播的 FLOPs 大约是前向的 2 倍，但 HBM 读写量没增加——这正是 FA 在训练里也能加速的原因。代价是反向时多算一次 QK^T 和 softmax，但 Tensor Core 算这些很快，省下的 HBM 带宽远比多算的 FLOPs 值。

### DDP 与 FSDP

FA 与 DDP/FSDP 完全兼容，它只是一个 attention kernel，不涉及梯度通信。分布式训练的注意点和标准 Attention 一样：梯度同步在 backward 之后自动触发，不需要为 FA 做特殊处理。

```python
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP

model = FlashAttentionLayer(d_model=4096, num_heads=32).cuda()
model = DDP(model)

for batch in dataloader:
    optimizer.zero_grad()
    output = model(batch)
    loss = loss_fn(output, target)
    loss.backward()  # FA 反向自动触发，DDP 梯度同步也自动触发
    optimizer.step()
```

## 推理场景的注意点

推理和训练的瓶颈不同。训练时 `seq_len` 长、batch 大，attention 占比高，FA 收益明显。推理时（特别是单条请求的生成阶段）`seq_len` 短、batch=1，attention 占比低，FA 的 kernel launch 开销可能比省下的 HBM 带宽还大。

实际工程中推理用 FA 的场景：

- **Prefill 阶段**：处理长 prompt 时，attention 是 N×N 的密集计算，FA 收益和训练一样明显。
- **Batch 推理**：多个请求拼 batch，`seq_len` 和 `batch` 都不小，FA 有收益。
- **单条请求的 decode 阶段**：每步只算一个 token 对所有历史 token 的 attention，N 很小，FA 可能比标准 attention 还慢。这种场景用 PagedAttention 或其他 KV-cache 优化更合适。

vLLM、SGLang 这类推理框架内部会根据阶段切换 attention 实现，不需要手动指定。

## 常见报错与排查

下面这些报错覆盖了 FA 使用中 90% 以上的问题，按出现频率排序。

### `ImportError: cannot import name 'flash_attn_func'`

`pip list | grep flash` 看包是否真的装了。如果装了但导入失败，多半是 CUDA 版本不匹配。`python -c "import torch; print(torch.version.cuda)"` 看 PyTorch 编译时的 CUDA 版本，`nvcc --version` 看系统 CUDA 版本，两者要兼容（同一主版本号）。

### `RuntimeError: CUDA error: no kernel image is available for execution on the device`

GPU 架构和编译目标不匹配。比如在 H100（sm_90）上跑了为 sm_80 编译的 wheel。解决：用对应架构的 wheel 源重装：

```bash
# H100
pip install flash-attn --no-build-isolation --index-url https://wheels.flash-attention.com/3.4/
```

### `RuntimeError: qkv must be half precision or bfloat16`

FA 只支持 FP16 和 BF16。如果输入是 FP32，先转换：

```python
Q = Q.to(torch.bfloat16)  # 或 torch.float16
```

BF16 通常比 FP16 更稳，因为动态范围大，不容易溢出。训练时优先选 BF16。

### 数值误差过大

如果 FA 输出和标准 Attention 的误差远超 1e-3，检查：

1. 输入是否含 NaN 或 Inf——FA 的 online softmax 对异常值更敏感。
2. 是否混用了 FP16 和 BF16——两种精度的累加顺序不同，混用会放大误差。
3. `causal` 参数是否一致——标准 Attention 实现里手动加 mask 容易出错。

### OOM 在长序列时

FA 把 attention 的内存从 O(N²) 降到 O(N)，但整个模型还有 FFN、KV cache、激活值。如果还是 OOM，检查：

- KV cache 是否用了 FA 的 varlen 接口拼 batch。
- 梯度检查点（`gradient_checkpointing`）是否开启——这能把激活值内存也压下来。
- 优化器状态是否分片（FSDP 或 ZeRO-2/3）。

### 常见误区

- **"FA 能加速所有 attention 计算"**：短序列（seq_len < 512）、batch=1 的推理场景下，FA 的 kernel launch 开销可能比省下的 HBM 带宽还大。这种场景用 PyTorch 原生 `scaled_dot_product_attention` 更合适。
- **"FA3 是近似算法"**：FA3 的 FP16/BF16 路径与标准 Attention 数学等价。FP8 模式有量化误差，但这是低精度计算的固有代价，不是算法近似。
- **"装了 `flash-attn` 就一定走 FA"**：HuggingFace Transformers 默认走 `eager` 后端，需要显式指定 `attn_implementation="flash_attention_2"`。PyTorch 2.0+ 的 `sdpa` 后端会根据硬件自动选择，不一定是 FA。
- **"FA 输出和标准 Attention 完全一致"**：FP16 下误差通常 < 1e-3，来源是累加顺序不同。如果业务对数值精度敏感（如金融、科学计算），需要评估这个误差是否可接受。
- **"FA 能解决所有长上下文问题"**：FA 把 attention 内存从 O(N²) 降到 O(N)，但 KV cache 仍然是 O(N)。序列长度超过 32k 后，KV cache 内存会成为新瓶颈，需要配合 Ring Attention、PagedAttention 等方案。

## 与近似注意力算法的边界

FA 是精确算法，但有些场景下近似算法更合适。下表划清边界：

| 算法 | 精确度 | 复杂度 | 适用场景 |
|------|--------|--------|----------|
| **Flash Attention** | 精确 | O(N) 时间、O(N) 内存 | 序列长度 < 32k，GPU 内存够装 KV |
| **Reformer** | 近似（LSH） | O(N log N) | 极长序列（>32k），可接受精度损失 |
| **Linformer** | 近似（低秩投影） | O(N) | 序列长度固定，离线训练 |
| **Performer** | 近似（随机特征） | O(N) | 需要可逆性，对精度要求低 |
| **Longformer / BigBird** | 近似（稀疏模式） | O(N) | 文档级任务，有明确的局部+全局模式 |

FA 出来之后，近似算法在生产环境里的使用大幅减少。FA 在大多数实际序列长度（< 32k）下既精确又快，省去了近似算法的精度调优成本——这是它取代近似算法的主要原因，而不是它在所有场景都更快。超过 32k 的超长序列，FA 仍然能用（H100 上能跑到 128k+），但 KV cache 内存会成为新瓶颈，这时候 Ring Attention、YARN 这类长上下文方案更合适。

## 采用顺序与决策建议

从零开始一个新项目：

1. **训练**：直接用 FA2（`attn_implementation="flash_attention_2"`）。H100 上可以试 FA3，但确认你的 `flash-attn` 版本 ≥ 2.5 且 PyTorch ≥ 2.3。
2. **推理**：用 vLLM 或 SGLang，它们内部已经根据 prefill/decode 阶段选了最优 attention 实现，不需要手动指定。
3. **长上下文（>32k）**：先确认 KV cache 内存够不够，再考虑 Ring Attention 或序列并行。
4. **非 NVIDIA GPU**：FA 官方不支持，AMD GPU 看 `flash-attn` 的 ROCm 移植，Intel GPU 看 IPEX 的实现，但生态都不如 NVIDIA 完善。

从已有项目迁移：

1. 先在测试集上对比 FA 输出和原 attention 的误差，确认 < 1e-3。
2. 在小 batch 上跑通训练循环，确认 loss 曲线和原实现一致。
3. 再上大 batch 长序列，观察实际加速比——预期 attention 部分加速 2-4x，端到端 1.2-1.5x。
4. 如果加速比远低于预期，profile 一下看是不是 FFN 或通信成了新瓶颈。

## 引用

```bibtex
@article{dao2022flashattention,
  title={FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness},
  author={Dao, Tri},
  journal={Advances in Neural Information Processing Systems},
  year={2022}
}

@article{dao2023flashattention2,
  title={FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning},
  author={Dao, Tri},
  journal={arXiv preprint arXiv:2307.08691},
  year={2023}
}

@article{shah2024flashattention3,
  title={FlashAttention-3: Fast and Accurate Attention with Asynchrony and Low-precision},
  author={Shah, Jay and Bikshandi, Ganesh and Zhang, Ying and Thakkar, Vijay and Ramani, Pradeep and Dao, Tri},
  journal={arXiv preprint arXiv:2407.08608},
  year={2024}
}
```

## 相关资源

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | https://github.com/Dao-AILab/flash-attention |
| FA1 论文 | https://arxiv.org/abs/2205.14135 |
| FA2 论文 | https://arxiv.org/abs/2307.08691 |
| FA3 论文 | https://arxiv.org/abs/2407.08608 |
| Tri Dao 主页 | https://tridao.me |
