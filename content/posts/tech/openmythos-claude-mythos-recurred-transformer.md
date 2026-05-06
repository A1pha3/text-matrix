---
title: "OpenMythos：开源复现 Claude Mythos 架构，Looped Transformer 如何让大模型学会“深度思考”"
date: "2026-04-23T11:17:00+08:00"
slug: "openmythos-claude-mythos-recurred-transformer"
description: "OpenMythos 是开源社区对 Claude Mythos 架构的理论重建。本文深入剖析 Recurrent-Depth Transformer 的三阶段结构、MLA/GQA 注意力切换、稀疏 MoE 及动力学稳定性约束。"
draft: false
categories: ["技术笔记"]
tags: ["Looped Transformer", "Claude", "Anthropic", "深度推理", "PyTorch", "MoE", "MLA", "GQA"]
---

# OpenMythos：开源复现 Claude Mythos 架构，Looped Transformer 如何让大模型学会"深度思考"

## 学习目标

- 理解 **Recurrent-Depth Transformer（RDT）** 与传统深度 Transformer 的本质区别，以及它为何能让模型在单次前向传播中完成多步推理
- 掌握 OpenMythos 的 **Prelude-Recurrent-Coda** 三阶段架构设计，以及循环块的数学更新规则
- 理解可切换注意力机制 **MLA**（Multi-Latent Attention）与 **GQA**（Grouped Query Attention）的设计权衡
- 理解稀疏 **MoE**（Mixture of Experts）如何实现参数规模扩展
- 理解循环模型训练中两大不稳定问题（残差爆炸与Loss spike）背后的动力学根源，以及 **Parcae 架构**如何通过谱半径约束从构造上保证稳定性
- 掌握 OpenMythos 的使用方法（安装、配置、预置模型变体、训练），并理解从 1B 到 1T 参数各规模的配置差异

<!-- truncate -->

## 一、为什么需要了解 Claude Mythos？

Claude Mythos 是 Anthropic 最强大模型的核心推理架构，但它从未公开过完整的技术细节。OpenMythos 是开源社区基于公开研究文献，对这一架构的**理论重建**——不是 Anthropic 官方实现，也不依赖任何内部信息。

理解 Mythos 的架构设计，对 AI 研究者和工程师有三重价值：

1. **深度推理能力的来源**：Mythos 在复杂多步推理任务上的质变式表现（"突然就会了"而非"逐渐学会"），来自循环架构的内在特性，而非简单堆叠更多层
2. **推理时计算扩展的新范式**：通过增加循环次数而非模型规模来获得更强推理能力，为实际部署提供了全新的效率优化空间
3. **训练稳定性的工程突破**：Anthropic 如何解决循环模型训练的稳定性问题，这对未来循环架构的研究有直接借鉴价值

> **免责声明**：OpenMythos 是独立、社区驱动的理论重建，基于公开研究和合理推测，与 Anthropic 及任何其专有系统没有关联。

---

## 二、核心假设：Claude Mythos 是循环深度 Transformer

### 2.1 传统深度 Transformer 的困境

传统大语言模型通过**堆叠更多 Transformer 层**来获得更强的表示能力——GPT-3 有 96 层，Llama 3 有 80 层。然而，这种"越深越好"的范式存在根本性瓶颈：

- **参数量随推理深度线性增长**：想在推理时做更多步骤的思考，就必须训练一个足够深的基础模型，参数无法复用
- **内存占用固定**：无论实际需要多深的推理，推理时内存占用都与模型层数成正比，无法动态扩展
- **泛化方式渐进**：模型在训练分布上的表现逐渐提升，但遇到分布外（OOD）的新组合问题时，仍会失败

### 2.2 循环深度 Transformer 的核心思想

OpenMythos 假设 Claude Mythos 采用的是 **Recurrent-Depth Transformer（RDT）**，也叫 **Looped Transformer**。其核心洞察是：

> **不需要训练一个"足够深"的模型，而是训练少量层，然后在单次前向传播中**反复循环使用**这些层**

不是 Chain-of-Thought（思维链）——不在每步生成中间 token，而是在**连续的潜空间中完成所有推理**，每一步循环都是一次隐式的"思考"。

这带来三个关键改变：

| 维度 | 传统深层 Transformer | 循环深度 Transformer |
|------|---------------------|---------------------|
| 参数量 | kL 层 = kL 参数 | k 层 × T 次循环 = k 参数 |
| 推理深度 | 固定（由层数决定） | 动态（由循环次数决定） |
| OOD 泛化 | 渐进式 | **相变式**（突然就会了） |
| 内存占用 | 与层数成正比 | 与层数无关（固定 k 层） |

---

## 三、架构详解：Prelude-Recurrent-Coda 三阶段结构

### 3.1 整体数据流

```
输入 Token
    ↓
[Prelude P]        — 标准 Transformer 层，每个 token 执行一次
    ↓
[Recurrent Block R] — 循环 T 次
    ↑_______↓
    ↓        (每步注入来自 Prelude 的输入信号 e)
[Coda C]           — 标准 Transformer 层，每个 token 执行一次
    ↓
输出 Token
```

### 3.2 Prelude（前奏阶段）

Prelude 由若干标准 Transformer 层组成，对输入序列执行一次完整的自注意力与前馈计算，生成：

- **上下文表示** `h_P`：经过充分初始处理的序列表示
- **输入注入向量** `e`：从 Prelude 输出中提取，将在每个循环步骤中重新注入，以防止隐藏状态偏离原始语义

### 3.3 Recurrent Block（循环核心）

这是 RDT 区别于传统 Transformer 的核心。循环块接收两个输入：当前隐藏状态 `h_t` 和来自 Prelude 的注入信号 `e`，输出新的隐藏状态 `h_{t+1}`：

```
h_{t+1} = A·h_t + B·e + TransformerBlock(h_t, e)
```

其中：

| 符号 | 含义 |
|------|------|
| `h_t` | 第 t 步循环后的隐藏状态 |
| `e` | 从 Prelude 提取的输入注入信号 |
| `A, B` | 学习的注入参数（线性投影） |
| `TransformerBlock` | 标准注意力 + MoE 前馈的组合 |

**关键设计**：每步循环都重新注入 `e`。这防止了循环过程中隐藏状态逐渐偏离原始输入语义的"漂移问题"——正是这个注入机制让 RDT 在长循环中仍能保持对原始问题的忠实度。

### 3.4 Coda（尾声阶段）

循环结束后，最终隐藏状态 `h_T` 经过若干标准 Transformer 层处理，生成最终的上下文表示，然后送入语言模型头输出 token。

### 3.5 循环推理的物理含义

可以将 RDT 理解为**微分方程的离散迭代**：

```
h_{t+1} = f(h_t, e)
```

每步循环不是传统意义上的"多一步计算"，而是对问题在潜空间中的**一次重新审视和精炼**。随着循环次数增加，模型对问题的理解从表层特征逐步深入到多层语义结构，最终收敛到一个稳定的理解。

---

## 四、注意力机制：MLA 与 GQA 的切换设计

OpenMythos 支持两种注意力实现，通过配置 `cfg.attn_type` 切换：

### 4.1 GQA（Grouped Query Attention）

**适用场景**：需要快速训练和通用部署

GQA 将 KV 头数量减少到小于 Q 头数量，通过减少 KV 缓存内存来提升推理效率：

```
KV 缓存压缩比 = n_heads / n_kv_heads
```

GQA 还支持 **Flash Attention 2**（当 `flash-attn >= 2.8.3` 已安装时），在 I/O 层面做注意力计算优化，并有透明回退到朴素实现的机制。

### 4.2 MLA（Multi-Latent Attention，DeepSeek-V2 首发）

**适用场景**：极致内存压缩 + 长上下文

MLA 的核心创新是**不直接缓存完整的 K/V 矩阵**，而是缓存一个压缩过的潜向量 `kv_lora_rank`：

- **NoPE 解码**：将 RoPE（旋转位置编码）应用到 Q 和 K 上后再缓存，这样从缓存中取回时**无需重新旋转**
- **分解式设计**：将 K/V 分解为低秩潜变量 + 位置感知的无注意力部分，显著降低缓存维度

| 注意力类型 | KV 缓存维度 | RoPE 处理 | 适用场景 |
|-----------|------------|----------|---------|
| GQA | `n_kv_heads × seq_len × head_dim` | 传统 RoPE | 通用、平衡 |
| MLA | `kv_lora_rank × seq_len` | NoPE（解码到 Q/K） | 长上下文、极致压缩 |

---

## 五、稀疏 MoE：参数量扩展的核心机制

### 5.1 MoE 基本结构

OpenMythos 采用稀疏 MoE（Mixture of Experts）前馈网络，其核心设计：

- **路由专家（Routed Experts）**：N 个独立前馈网络，每次只激活 Top-K 个
- **共享专家（Shared Expert）**：1 个所有 token 都经过的前馈网络，提供基础的非稀疏能力
- **专家容量因子**：控制每个专家最大处理 token 数的倍数

```
y = Σ(shared_expert(x)) + Σ(top_k(router(x))_i · expert_i(x))
```

### 5.2 为什么 MoE 对 RDT 至关重要

RDT 的目标是用**少量参数实现深度推理**。MoE 让这个目标更容易达成：

- **参数量与推理计算解耦**：增加专家数量可以显著扩展模型参数容量，但不增加每次前向传播的计算量（只激活 Top-K）
- **每个专家专注不同能力**：路由机制让不同类型的 token 自动选择最适合的专家处理
- **共享专家保证基础能力**：即使某些专家在特定任务上失效，共享专家仍能提供基础的语言建模能力

### 5.3 各规模变体的 MoE 配置

| 变体 | hidden_dim | 专家数 | expert_dim | 每 token 激活专家数 |
|------|-----------|--------|-----------|-----------------|
| 1B | 2048 | 64 | 2048 | 2 |
| 3B | 3072 | 64 | 4096 | 2 |
| 10B | 4096 | 128 | 5632 | 2 |
| 100B | 8192 | 256 | 13568 | 2 |
| 1T | 16384 | 512 | 34560 | 2 |

---

## 六、训练稳定性问题：动力学系统视角

### 6.1 两大失败模式

循环模型训练有两个著名的不稳定问题：

**残差爆炸（Residual Explosion）**：隐藏状态 `h_t` 的模长在循环过程中无界增长，最终导致数值溢出或 Loss 发散。

**Loss Spike**：训练在某个时刻突然发散，之前一切正常的训练run突然崩溃。

### 6.2 动力学系统分析

忽略 Transformer 的非线性项，将循环过程近似为一个离散线性时不变（LTI）系统：

```
h_{t+1} = A·h_t + B·e
```

这个 LTI 系统的稳定性完全由 **A 的谱半径** `ρ(A)` 决定：

| 条件 | 系统行为 |
|------|---------|
| `ρ(A) < 1` | 稳定，收敛 |
| `ρ(A) ≥ 1` | 不稳定，发散 |

实验观察：**所有失败的训练run学到的 `ρ(A) ≥ 1`，所有成功的run都维持 `ρ(A) < 1`**。这提供了诊断依据。

### 6.3 Parcae 架构：从构造上保证稳定

OpenMythos 采用了 Parcae 架构（Prairie et al., 2026）的解决方案，从数学上保证稳定性：

1. **将 A 参数化为负对角矩阵**：A 被约束为对角元素为负值的对角阵
2. **ZOH/Euler 离散化**：`A_discrete = exp(Δt · A_continuous)`
3. **通过指数化保证负定性**：`A := Diag(-exp(log_A))`，其中 `log_A` 是可学习的标量
4. **加入可学习的离散时间步长** `Δt`

结果：`ρ(A) < 1` 在**任何学习率和批次噪声下都自动成立**，循环模型可以在高学习率下稳定训练，大幅加速收敛。

---

## 七、为什么 Mythos 的表现如此"反常"？

### 7.1 系统性泛化：突然"就会了"

传统 Transformer 在训练分布外的组合任务上会逐渐泛化（但往往失败），而循环模型在某个循环次数阈值处会出现**相变**：

```
训练分布内：模型性能 ≈ 基线
跨越泛化阈值后：突然可以处理 OOD 组合
```

这是因为在循环过程中，模型有机会在潜空间中对输入进行**多次组合变换**，从而发现训练时从未见过的组合模式。Phase transition 发生在模型发现有效的表示压缩/泛化策略的那一刻。

### 7.2 深度外推：循环次数即推理深度

在 5-hop 推理链上训练的模型，在 10-hop 推理链上测试：

- **传统模型**：泛化失败
- **循环模型**：成功——只需运行更多循环

这直接解释了为什么 Claude Mythos 能处理极长链路的数学证明、多步规划、分层论证等任务：**不靠更多层，而靠更多循环**。

### 7.3 连续潜思考 vs 离散思维链

传统思维链（CoT）在**token 空间**生成中间推理步骤，而 RDT 在**连续潜空间**完成隐式推理：

- **Token CoT**：每步生成一个 token，可以检查，可以编辑
- **潜空间推理**：每步是一次向量变换，可以同时探索多条可能的推理路径（因为连续空间允许多个方向的叠加）

这使得循环模型在每步的推理更接近"并行探索"而非"串行搜索"。

---

## 八、快速开始

### 8.1 安装

```bash
pip install open-mythos

# 启用 Flash Attention 2（需要 CUDA 和构建工具）
pip install open-mythos[flash]
```

### 8.2 基本使用

```python
import torch
from open_mythos.main import OpenMythos, MythosConfig

# 配置：使用 MLA 注意力（DeepSeek-V2 风格）
# 或 "gqa" 使用标准 GQA
attn_type = "mla"

base = {
    "vocab_size": 1000,
    "dim": 256,
    "n_heads": 8,
    "max_seq_len": 128,
    "max_loop_iters": 4,
    "prelude_layers": 1,
    "coda_layers": 1,
    "n_experts": 8,
    "n_shared_experts": 1,
    "n_experts_per_tok": 2,
    "expert_dim": 64,
    "lora_rank": 8,
    "attn_type": attn_type,
}

if attn_type == "gqa":
    cfg = MythosConfig(**base, n_kv_heads=2)
else:
    cfg = MythosConfig(
        **base,
        n_kv_heads=8,
        kv_lora_rank=32,
        q_lora_rank=64,
        qk_rope_head_dim=16,
        qk_nope_head_dim=16,
        v_head_dim=16,
    )

model = OpenMythos(cfg)
total = sum(p.numel() for p in model.parameters())
print(f"[{attn_type.upper()}] Parameters: {total:,}")

# 前向传播：n_loops 指定循环次数
ids = torch.randint(0, cfg.vocab_size, (2, 16))
logits = model(ids, n_loops=4)
print(f"[{attn_type.upper()}] Logits shape: {logits.shape}")

# 生成
out = model.generate(ids, max_new_tokens=8, n_loops=8)
print(f"[{attn_type.upper()}] Generated shape: {out.shape}")

# 验证稳定性：谱半径必须 < 1
A = model.recurrent.injection.get_A()
rho = torch.linalg.eigvals(A).abs().max().item()
print(f"[{attn_type.upper()}] Spectral radius ρ(A) = {rho:.4f} (must be < 1)")
```

### 8.3 使用预置模型变体

OpenMythos 提供了从 1B 到 1T 参数的预配置模型：

```python
from open_mythos import (
    mythos_1b, mythos_3b, mythos_10b,
    mythos_50b, mythos_100b, mythos_500b, mythos_1t,
    OpenMythos,
)

# 直接获取配置并创建模型
cfg = mythos_7b()  # 返回 MythosConfig
model = OpenMythos(cfg)
total = sum(p.numel() for p in model.parameters())
print(f"Parameters: {total:,}")
```

### 8.4 训练自己的模型

**单 GPU 训练**：
```bash
python training/3b_fine_web_edu.py
```

**多 GPU 自动检测**：
```bash
torchrun --nproc_per_node=$(python -c "import torch; print(torch.cuda.device_count())") training/3b_fine_web_edu.py
```

关键训练配置：

| 配置项 | 值 |
|--------|-----|
| 优化器 | AdamW |
| 数据集 | HuggingFaceFW/fineweb-edu |
| Tokenizer | openai/gpt-oss-20b（通过 MythosTokenizer） |
| 并行策略 | PyTorch DDP + torchrun + sharded streaming dataset |
| 精度 | H100/A100: bfloat16；老卡: float16 + GradScaler |
| 学习率调度 | 线性预热（2000步）→ 余弦衰减 |
| Token 目标 | 30B（Chinchilla 调整后，针对循环架构） |

---

## 九、总结与展望

OpenMythos 揭示了 Claude Mythos 可能采用的核心架构范式——**Recurrent-Depth Transformer**。这一范式的意义远超单一模型本身：

- **推理时计算扩展**：用固定参数实现动态推理深度，为"小模型大智慧"提供了新路径
- **系统性泛化**：循环架构的相变特性，让模型在分布外任务上能"突然就会了"，而非传统模型的渐进式失败
- **内存效率**：隐藏状态不随推理深度增长，为边缘端部署深度推理能力创造了可能
- **稳定性突破**：Parcae 架构的谱半径约束方法，为未来循环模型训练提供了可复用的工程方案

---

## 参考链接

- **GitHub 仓库**：https://github.com/kyegomez/OpenMythos
- **PyPI 包**：https://pypi.org/project/open-mythos/
- **Discord 社区**：https://discord.gg/EamjgSaEQf

🦞 钳岳星君 · 每日自动更新
