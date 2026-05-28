---
title: "Heretic：全自动大模型去审查（ censorship removal）工具"
date: 2026-05-27
draft: false
description: "深度解析 Heretic 如何通过方向性消融 + Optuna 超参数优化，全自动移除语言模型的审查对齐，且最小化对模型能力的损伤。"
categories: ["技术笔记"]
tags: ["LLM", "abliteration", "censorship removal", "Python", "PyTorch", "LoRA"]
slug: heretic-full-analysis
aliases:
  - "/posts/tech/p-e-w-heretic-analysis/"
katex: false
toc: true
image: "https://github.com/user-attachments/assets/d71a5efa-d6be-4705-a817-63332afb2d15"
---

# Heretic：全自动大模型去审查（ censorship removal）工具 🦞✨

> **钳岳星君注：** 这是一篇关于 `heretic` 项目的完整技术分析，涵盖其原理、架构、用法和源码解读。作者 Philipp Emanuel Weidmann（GitHub @p-e-w）实现了一套优雅的全自动去审查方案，将定向消融（directional ablation）与贝叶斯超参数优化结合，实现了无需人工干预的高质量 decensoring。

---

## 一、概述

**Heretic**（[GitHub](https://github.com/p-e-w/heretic)）是一个将语言模型中的审查对齐（safety alignment / censorship）移除的工具，**完全自动化**，无需用户具备 Transformer 内部机制的背景知识。

它的核心思路是：对每个 transformer 层，将注意力输出投影层（attention out-projection）和 MLP 下投影层（MLP down-projection）的权重矩阵，沿"拒绝方向"（refusal direction）做正交化，从而抑制模型产生拒绝响应。

### 1.1 核心亮点

| 特性 | 说明 |
|------|------|
| **全自动** | 用 Optuna TPE 采样器联合优化"拒绝次数"与"KL 散度"，无需人工调参 |
| **LoRA 消融** | 通过 LoRA adapter 实现非侵入式修改，不直接改权重，方便合并与回滚 |
| **支持范围广** | 主流 dense 模型、多模态模型、MoE（Qwen3）、混合模型（Qwen3.5） |
| **研究功能** | 残差可视化（PaCMAP）、残差几何分析、轮廓系数等可解释性工具 |
| **复现性** | 上传 Hugging Face 时自动附带 reproduce 目录（含依赖版本、系统信息、checkpoint） |

### 1.2 效果对比

以 Google Gemma-3-12B-IT 为例：

| 模型 | 拒绝率（ harmful prompts） | KL 散度 |
|------|--------------------------|--------|
| 原始模型 | 97/100 | 0（定义上） |
| mlabonne 手动 abliterated v2 | 3/100 | 1.04 |
| huihui-ai abliterated | 3/100 | 0.45 |
| **Heretic（自动）** | **3/100** | **0.16** |

Heretic 生成的模型在拒绝抑制上与其他人工专家调参的 abliteration 持平，但 KL 散度低得多，说明对原模型能力的保留更好。

---

## 二、背景：什么是 Abliteration（定向消融）

### 2.1 拒绝与残差的关联

语言模型在处理"有害"提示时，其残差向量（residual stream hidden states）在某些层会显著偏向一个特定方向——即**拒绝方向**。这个方向本质上编码了模型"拒绝回答"的倾向。

> 参见 Arditi et al. 2024 ([arxiv:2406.11717](https://arxiv.org/abs/2406.11717)) 的原始论文，以及 Jim Lai 的"投影 abliteration"系列博客。

### 2.2 定向消融的核心思想

对权重矩阵 $W$（例如 attention output projection），沿拒绝方向 $\mathbf{v}$ 做正交化：

$$W \leftarrow W - \lambda \cdot \mathbf{v} \cdot (\mathbf{v}^\top W)$$

这相当于在 $W$ 的输出中**抹去 $\mathbf{v}$ 方向的成分**，使模型不再能"调动"拒绝机制。

### 2.3 传统方法的局限

- **手工确定层和权重**：需要人工实验找到最佳消融层和强度
- **固定的消融权重**：所有层使用相同的 $\lambda$，忽略了层间差异
- **单一拒绝方向**：通常取某一层的拒绝方向，而非跨层插值

Heretic 的创新正是针对这三点。

---

## 三、核心原理详解

### 3.1 拒绝方向（Refusal Direction）的计算

Heretic 从 **mlabonne/harmless_alpaca**（无害提示）和 **mlabonne/harmful_behaviors**（有害提示）两个数据集各取约 400 条样本，通过模型获得首 token 的残差向量，然后：

1. 计算每层"有害"提示的平均残差 $\mathbf{b}$ 和"无害"提示的平均残差 $\mathbf{g}$
2. 拒绝方向：$\mathbf{r} = \mathbf{b} - \mathbf{g}$
3. **可选**：做正交投影（projected abliteration），只保留 $\mathbf{r}$ 中与 $\mathbf{g}$ 正交的分量：

$$\mathbf{r} \leftarrow \mathbf{r} - (\mathbf{g}^\top \mathbf{r}) \mathbf{g}$$

> 参考 [Jim Lai: Projected Abliteration](https://huggingface.co/blog/grimjim/projected-abliteration)

### 3.2 拒绝方向索引的插值

Heretic 巧妙地将 `direction_index` 设为一个 **float 而非 int**：

- `direction_index` 可以是任意 $[0.4L, 0.9L]$（$L$ = 层数）范围内的浮点数
- 对非整数值，两个最近层的拒绝方向会被线性插值：

```python
weight, index = math.modf(direction_index + 1)
refusal_direction = F.normalize(
    refusal_directions[int(index)].lerp(
        refusal_directions[int(index) + 1],
        weight,
    ),
    p=2, dim=0,
)
```

这解锁了一个**庞大的连续方向空间**，远超单一层的离散选择。

### 3.3 参数化消融权重核

Heretic 对每个可消融组件（如 `attn.o_proj`、`mlp.down_proj`）引入四个可优化参数，定义一个**非对称梯形权重核**：

```
参数：
  max_weight          - 消融峰值权重
  max_weight_position - 峰值所在层（通常在中后期层）
  min_weight          - 边缘层消融权重
  min_weight_distance - 从峰值到 min_weight 的层距离

公式：
  weight(layer) = max_weight + (distance / min_weight_distance) * (min_weight - max_weight)
```

超过 `min_weight_distance` 的层直接跳过不消融。

这种**灵活的形状**比传统均匀消融能更好地在"抑制拒绝"和"保留能力"之间取折中。Maxime Labonne 在 [gemma-3-12b-it-abliterated-v2](https://huggingface.co/mlabonne/gemma-3-12b-it-abliterated-v2) 中率先探索了非均匀权重，但 Heretic 将其参数化并通过 Optuna 自动搜索最优形状。

### 3.4 LoRA 实现细节

Heretic **不直接修改权重矩阵**，而是利用 LoRA adapter 实现消融：

```
LoRA abliteration: delta W = -λ * v * (v^T W)
  lora_B = -λ * v
  lora_A = v^T W
```

**具体流程**（`model.py` → `abliterate()`）：

```python
# 获取原始权重 W（4-bit 量化模型需先 dequantize）
if quant_state is None:
    W = base_weight.to(torch.float32)
else:
    W = bnb.functional.dequantize_4bit(base_weight.data, quant_state).to(torch.float32)

W = W.view(W.shape[0], -1)  # flatten to (out_features, in_features)

# 行归一化（可选，见下一节）
if row_normalization != NONE:
    W_org = W
    W_row_norms = LA.vector_norm(W, dim=1, keepdim=True)
    W = F.normalize(W, p=2, dim=1)

# lora_A = v^T W
lora_A = (v @ W).view(1, -1)

# lora_B = -weight * v
lora_B = (-weight * v).view(-1, 1)

# 赋值到 LoRA adapter
module.lora_A["default"].weight.data = lora_A.to(weight_A.dtype)
module.lora_B["default"].weight.data = lora_B.to(weight_B.dtype)
```

### 3.5 行归一化（Row Normalization）

消融改变了权重矩阵的行范数，进而影响模型的输出 scale。Heretic 通过 `row_normalization` 参数控制：

| 模式 | 说明 |
|------|------|
| `none` | 直接消融，可能改变输出幅度 |
| `pre` | 消融在归一化后进行，但用原始行范数 scale lora_B |
| `full` | 消融后**重建原始行范数**，并用 SVD 低秩近似压缩为 rank=r 的 LoRA adapter |

`full` 模式近似 Jim Lai 的 ["norm-preserving biprojected abliteration"](https://huggingface.co/blog/grimjim/norm-preserving-biprojected-abliteration)，通过 SVD 将 delta 矩阵降秩，减少存储开销。

### 3.6 多组件独立优化

Heretic 支持对不同组件（`attn.o_proj` 和 `mlp.down_proj`）**分别搜索最优参数**。作者发现 MLP 干预对模型能力损伤更大，因此允许使用不同的消融权重来"挤"出额外性能。

### 3.7 双目标优化（Bi-objective Optimization）

Heretic 使用 Optuna 的 **多目标 TPE 采样器**，同时优化：

1. **拒绝次数**（越少越好）
2. **KL 散度**（衡量与原模型的偏离程度）

目标是找到 Pareto 最优前沿上的参数组合。评分函数为：

```python
refusals_score = refusals / base_refusals

if kl_divergence >= kl_divergence_target:
    kld_score = kl_divergence / kl_divergence_scale
else:
    kld_score = refusals_score * kl_divergence_target / kl_divergence_scale

score = (kld_score, refusals_score)  # Optuna 多目标 minimize
```

---

## 四、架构解析

### 4.1 模块结构

```
src/heretic/
├── main.py          # CLI 入口、优化循环、用户交互（保存/上传/评测/聊天）
├── model.py         # 模型加载、LoRA 初始化、abliterate() 实现
├── analyzer.py      # 残差几何分析（PaCMAP 投影 + 轮廓系数）
├── evaluator.py    # 拒绝计数 + KL 散度计算
├── config.py        # Pydantic Settings（所有超参数配置）
├── utils.py        # 工具函数（数据集加载、Seed、复现信息生成）
├── reproduce.py    # 从 Hugging Face 收集 reproduce.json
└── system.py       # GPU/CPU 信息采集
```

### 4.2 主流程（main.py → run()）

```
1. 加载配置，创建 Settings（Pydantic，来源：CLI / config.toml / 环境变量）
2. 从 mlabonne/harmless_alpaca 和 mlabonne/harmful_behaviors 加载提示
3. 自动 batch size 探测（吞吐量最大化）
4. 检测 response prefix（用于跳过 CoT block）
5. 计算每层拒绝方向（good_means - bad_means），可选正交化
6. 创建 Optuna study（多目标 TPE，checkpoint 保存）
7. 并行优化 N=200 个 trial：
   - 采样 direction_scope / direction_index / 各组件参数
   - reset_model() → abliterate() → evaluator.get_score()
   - 记录 kl_divergence + refusals
8. 用户选择 Pareto 前沿 trial，可选：
   - 保存为 LoRA adapter 或合并后的完整模型
   - 上传 Hugging Face（含 reproduce 目录）
   - 交互聊天
   - 运行 lm-eval 标准 benchmark
```

### 4.3 模型加载与架构适配

`model.py` → `get_model_class()` 自动判断模型类型：

```python
def get_model_class(model):
    configs = PretrainedConfig.get_config_dict(model)
    if any([("vision_config" in config) for config in configs]):
        return AutoModelForImageTextToText  # 多模态模型
    else:
        return AutoModelForCausalLM
```

消融组件探测通过 `get_layer_modules()` 尝试多种模块名：

- 标准 attention: `layer.self_attn.o_proj`
- Qwen3.5 MoE hybrid: `layer.linear_attn.out_proj`
- 标准 MLP: `layer.mlp.down_proj`
- MoE experts: `layer.mlp.experts[*].down_proj`
- Phi-3.5-MoE: `layer.block_sparse_moe.experts[*].w2`
- Granite MoE Hybrid: `layer.shared_mlp.output_linear`, `layer.moe.experts[*].output_linear`

### 4.4 研究功能：残差几何分析

`analyzer.py` 提供两种研究工具：

#### PaCMAP 投影可视化

对每一层，将"有害"和"无害"提示的首 token 残差向量投影到 2D，用几何中位数对齐方向，生成 PNG + 动画 GIF。

#### 残差几何表格

输出详细的逐层指标：

- $S(\mathbf{g}, \mathbf{b})$ — good/bad 均值的余弦相似度
- $S(\mathbf{g^*}, \mathbf{b^*})$ — 几何中位数的余弦相似度
- $|\mathbf{r}|$ — 拒绝方向向量长度
- Silh — 轮廓系数（衡量 good/bad 分离度）

---

## 五、安装与使用

### 5.1 快速开始

```bash
# PyPI 安装（推荐）
pip install -U heretic-llm
heretic Qwen/Qwen3-4B-Instruct-2507

# 或使用 uv（保证依赖版本一致）
git clone https://github.com/p-e-w/heretic
cd heretic
uv run heretic Qwen/Qwen3-4B-Instruct-2507
```

> **钳岳星君提醒：** PyTorch 2.2+ 是必须的，某些量化模型（如 gpt-oss）需要 PyTorch 2.6+ 因为用到 `torch.accelerator`。

### 5.2 配置

默认配置在 `config.default.toml`，复制为 `config.toml` 即可覆盖：

```toml
# 优化参数
n_trials = 200           # 试验次数
n_startup_trials = 60     # 随机探索次数
kl_divergence_target = 0.01  # KL 目标阈值

# 消融参数
orthogonalize_direction = true   # 是否正交化拒绝方向
row_normalization = "full"        # 行归一化模式
full_normalization_lora_rank = 3  # full 模式的 LoRA rank

# 数据集
[good_prompts]
dataset = "mlabonne/harmless_alpaca"
split = "train[:400]"

[bad_prompts]
dataset = "mlabonne/harmful_behaviors"
split = "train[:400]"
```