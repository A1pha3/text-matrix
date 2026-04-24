---
title: "TensorLogic：Pedro Domingos论文实现·神经符号统一推理框架·FB15k-237基准MRR 0.347"
date: 2026-04-24T19:10:00+08:00
slug: "tensorlogic-ai-unified-reasoning-guide"
description: "TensorLogic是基于Pedro Domingos论文的Python实现，通过Tensor方程统一神经推理和符号推理。Boolean模式零幻觉、RESCAL自动谓词发明、Transformer/RNN全部用Tensor方程表达，FB15k-237 MRR 0.347超越LibKGE参考实现。"
draft: false
categories: ["技术笔记"]
tags: ["TensorLogic", "神经符号推理", "知识图谱", "RESCAL", "Transformer"]
---

# TensorLogic：Pedro Domingos论文实现·神经符号统一推理框架·FB15k-237基准MRR 0.347

<!-- truncate -->

## 一、项目概述

### 1.1 TensorLogic是什么

**TensorLogic** 是一个基于 **"Tensor Logic: The Language of AI"** 论文（Pedro Domingos, arXiv:2510.12269）的 **Python实现**，旨在通过 **Tensor方程** 统一 **神经推理** 和 **符号推理**，为AI提供一种结合神经网络学习能力与逻辑推理可解释性的新范式。

> 原文：`"A unified programming language for AI that combines neural and symbolic reasoning through tensor equations."`

**核心定位**：不是又一个LLM替代品，而是**神经+符号混合推理**的基础设施——在需要可解释性、零幻觉、或高效小模型的场景下，提供清晰的技术路径。

### 1.2 核心数据

| 指标 | 数值 | 说明 |
|------|------|------|
| **Stars** | **43** ⭐ | 学术型项目，小而精 |
| **组织** | Kocoro-lab | 与ShanClaw同组织 |
| **语言** | Python 100% | PyTorch生态 |
| **创建时间** | 2025-10-16 | 较新项目 |
| **最新提交** | 2026-04-24 | 活跃维护中 |
| **论文引用** | arXiv:2510.12269 | 学术支撑扎实 |

### 1.3 为什么需要TensorLogic

**传统AI的困境**：

| 类型 | 优势 | 困境 |
|------|------|------|
| **大语言模型 (LLM)** | 知识广博、生成自然 | 幻觉严重、不可解释、推理成本高 |
| **纯符号系统** | 逻辑严谨、可解释 | 缺乏学习能力、知识获取困难 |
| **知识图谱嵌入** | 知识结构化、可推理 | 无法处理复杂逻辑链 |

**TensorLogic的解决思路**：

```
✅ Tensor方程 = 统一的计算原语（神经+符号都用）
✅ Boolean模式 = 零幻觉的符号推理（严格逻辑）
✅ Continuous模式 = 可学习的嵌入推理（概率化）
✅ Predicate Invention = 自动发现隐藏关系（无需标签）
✅ 模型极小 = 10-500KB vs LLM的GB级
```

### 1.4 与Kocoro-lab其他项目的关系

TensorLogic与同组织的 **ShanClaw**（macOS原生AI Agent CLI）形成互补：

| 项目 | 定位 | 技术栈 |
|------|------|--------|
| **TensorLogic** | 推理引擎/底层框架 | Python + PyTorch |
| **ShanClaw** | Agent上层应用 | macOS原生CLI + Shannon Gateway |

```
ShanClaw (Agent应用)
    ↓ 调用
TensorLogic (推理引擎) ←→ 知识图谱/规则库
```

---

## 二、核心概念详解

### 2.1 Tensor Programs（张量程序）

Tensor Programs是TensorLogic的核心抽象——用**Tensor方程**同时表达**数据**（facts, relations, weights）和**规则**（equations）。

**核心思想**：
- 万物皆Tensor：实体、关系、权重都是多维数组
- 计算即方程：所有操作都表示为tensor equation
- 前向/后向链：推理过程是tensor的传播

**与标准PyTorch的区别**：

| 维度 | PyTorch | TensorLogic |
|------|---------|-------------|
| **目标** | 通用深度学习 | 神经+符号统一推理 |
| **核心抽象** | Layer/Module | TensorProgram + Equation |
| **推理模式** | 概率输出 | Boolean(0/1) + Continuous(概率) |
| **可解释性** | 黑盒梯度 | 符号化的tensor方程 |

### 2.2 Boolean模式 vs Continuous模式

TensorLogic支持两种推理模式，适用不同场景：

#### 2.2.1 Boolean模式（符号推理）

**特点**：
- 输出严格0/1，无概率模糊
- 前向链/后向链推理
- **零幻觉**：逻辑保证的正确性
- 无需训练，直接使用规则

**适用场景**：
| 场景 | 示例 | 为什么选Boolean |
|------|------|----------------|
| **规则推理** | 税收规则、法律合规 | 逻辑严密、不可出错 |
| **家族关系** | grandparent = parent ∘ parent | 确定性推导 |
| **医疗禁忌** | 药物相互作用检查 | 人命关天、零容忍 |
| **审计追溯** | 合规性检查 | 每步可追溯 |

**核心机制**：
```
事实: parent(Alice, Bob) = 1
规则: grandparent(X, Y) :- parent(X, Z) ∧ parent(Z, Y)

查询: grandparent(Alice, ?) → 前向链追踪 → Bob
```

#### 2.2.2 Continuous模式（概率推理）

**特点**：
- 输出概率值（0-1之间）
- 可学习的嵌入和关系矩阵
- 完全可微，可纳入神经网络pipeline
- 支持temperature控制确定性

**适用场景**：

| 场景 | 示例 | 为什么选Continuous |
|------|------|-------------------|
| **知识图谱补全** | 预测缺失的实体关系 | 从已知三元组学习 |
| **相似度推理** | 找相似的实体 | 向量空间运算 |
| **多跳推理** | 链式关系推导 | 矩阵乘法组合 |
| **嵌入学习** | 实体/关系向量化 | 端到端训练 |

**核心机制**：
```
score(subject, relation, object) = subject^T × relation_matrix × object

# 分数 > threshold → 关系成立
# 通过正/负样本对学习 W_relation
```

### 2.3 Embedding Space（嵌入空间推理）

Embedding Space是Continuous模式的核心——将**实体**编码为向量，**关系**编码为矩阵。

**表示学习**：

| 元素 | Tensor形式 | 维度 | 说明 |
|------|-----------|------|------|
| **实体** | 向量 e ∈ R^d | d维 | 编码实体身份 |
| **关系** | 矩阵 W_r ∈ R^{d×d} | d×d | 编码关系变换 |
| **三元组** | (e_s, W_r, e_o) | - | 头实体、关系矩阵、尾实体 |

**评分函数**：
```python
score(e_s, W_r, e_o) = e_s^T @ W_r @ e_o

# 分数高 → 关系成立的可能性大
# 通过sigmoid转换为概率
```

**关系组合**：
```python
# grandparent = parent @ parent
W_grandparent = W_parent @ W_parent

# 多跳推理：friend → colleague → same_company → ...
```

**训练过程**：
```
1. 初始化：随机实体嵌入 + 随机关系矩阵
2. 批量加载：正样本三元组 + 负样本三元组
3. 前向计算：score(head, relation, tail)
4. 计算损失：margin-based loss 或 cross-entropy
5. 反向传播：更新嵌入和关系矩阵
6. 重复直到收敛
```

### 2.4 Predicate Invention（谓词自动发明）

这是TensorLogic最独特的特性——通过 **RESCAL张量分解** 自动发现**隐藏关系**，无需人工标签。

**传统方式 vs TensorLogic**：

| 维度 | 传统方式 | TensorLogic |
|------|----------|-------------|
| **特征工程** | 人工定义 | ❌ |
| **标签获取** | 需要标注数据 | ❌ |
| **隐含关系** | 无法自动发现 | ✅ RESCAL分解 |
| **可解释性** | 取决于人工设计 | ✅ 关系矩阵可查看 |

**RESCAL分解原理**：
```
输入：知识图谱 → 三维张量 X ∈ R^{n×n×m}
     n = 实体数，m = 关系数
     X[i,j,k] = 1 表示 entity_i --relation_k--> entity_j

分解：X ≈ Σ_r A @ W_r @ A^T
     A ∈ R^{n×d} = 实体嵌入矩阵
     W_r ∈ R^{d×d} = 关系矩阵

输出：分解得到的 W_r 就是"发明"出的新谓词
```

**应用场景**：
- 知识图谱精化：发现缺失的隐含关系
- 关系预测：预测未来可能成立的三元组
- 数据补全：填补知识图谱的稀疏区域

---

## 三、系统架构分析

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      TensorLogic                             │
├─────────────────────────────────────────────────────────────┤
│  examples/                                                   │
│  ├── family_tree_symbolic.py      # Boolean模式示例          │
│  ├── family_tree_embedding.py     # Continuous模式示例       │
│  ├── learnable_demo.py            # Composer多跳推理         │
│  ├── predicate_invention_demo.py  # RESCAL谓词发明           │
│  ├── fb15k237_benchmark.py        # 标准KG基准测试           │
│  ├── benchmark_suite.py           # 内部基准测试套件         │
│  ├── transformer_reasoning_demo.py # Transformer推理          │
│  └── shakespeare/                 # 语言模型训练              │
├─────────────────────────────────────────────────────────────┤
│  tensorlogic/                                               │
│  ├── core/              # TensorProgram核心                 │
│  │   └── program.py     # TensorProgram定义                 │
│  ├── reasoning/         # 推理引擎                           │
│  │   ├── embed.py       # EmbeddingSpace                    │
│  │   ├── composer.py    # GatedMultiHopComposer             │
│  │   ├── closure.py     # 闭包推理                          │
│  │   ├── decomposition.py # 张量分解                        │
│  │   └── predicate_invention/ # RESCAL谓词发明              │
│  ├── learn/             # 训练模块                           │
│  │   ├── trainer.py     # 训练器基类                        │
│  │   ├── embedding_trainer.py # 嵌入训练                     │
│  │   └── losses.py      # 损失函数                         │
│  ├── utils/            # 工具                                │
│  │   ├── diagnostics.py # 梯度诊断                          │
│  │   ├── init.py        # 初始化策略                        │
│  │   ├── sparse.py      # 稀疏张量                          │
│  │   └── visualization.py # 可视化                           │
│  └── transformers/     # Transformer/RNN实现                 │
│      ├── transformer.py # 标准Transformer                   │
│      ├── lstm.py        # LSTM/GRU                         │
│      └── decoder_lm.py  # Decoder-only LM                  │
├─────────────────────────────────────────────────────────────┤
│  PyTorch 2.0+ / NumPy / Python 3.8+                          │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 核心模块详解

#### 3.2.1 core/program.py — TensorProgram

`TensorProgram`是所有tensor程序的基类，封装了前向计算和反向传播。

**核心接口**：
```python
class TensorProgram:
    def forward(self, inputs) -> Tensor:
        """执行前向计算"""
        
    def backward(self, grad_outputs) -> List[Tensor]:
        """执行反向传播"""
        
    def to_tensor_equations(self) -> List[str]:
        """导出为tensor方程字符串"""
```

**Boolean vs Differentiable**：
```python
# Boolean模式：离散逻辑，无梯度
program = TensorProgram(mode='boolean')
result = program.forward(facts)  # 返回0/1

# Differentiable模式：连续概率，可训练
program = TensorProgram(mode='differentiable')
loss = program.forward(positive_pairs, negative_pairs)
loss.backward()
```

#### 3.2.2 reasoning/embed.py — EmbeddingSpace

`EmbeddingSpace`管理实体嵌入和关系矩阵，提供知识图谱推理能力。

**核心功能**：
```python
from tensorlogic.reasoning.embed import EmbeddingSpace

# 创建嵌入空间
space = EmbeddingSpace(num_entities=1000, embedding_dim=100, num_relations=50)

# 注册三元组
space.register(entity_name, entity_id)
space.add_triplet(head_id, relation_id, tail_id)

# 学习嵌入
space.learn(positive_triplets, negative_triplets, epochs=100)

# 推理查询
score = space.score(subject_id, relation_id, object_id)
candidates = space.query(head=subject_id, relation=relation_id)
```

**评分机制**：
```python
# 双线性评分函数
score(e_s, W_r, e_o) = σ(e_s^T @ W_r @ e_o)

# 或基于范数的评分
score(e_s, W_r, e_o) = ||e_s + W_r - e_o||
```

#### 3.2.3 reasoning/composer.py — GatedMultiHopComposer

`GatedMultiHopComposer`学习**多跳关系组合**，例如从"父亲"+"父亲的父亲"推导出"祖父"。

**核心思想**：
```python
from tensorlogic.reasoning.composer import GatedMultiHopComposer

# 创建组合器
composer = GatedMultiHopComposer(embedding_dim=100)

# 学习关系组合
# 输入：(head, [relation_path], tail)
#       e.g., (Alice, [parent, parent], Bob)
training_data = [
    (alice_id, [parent_id, parent_id], bob_id),   # Alice的祖父是Bob
    (charlie_id, [parent_id, parent_id], diana_id), # Charlie的祖父是Diana
]

composer.learn(training_data)

# 推理：给定头实体和关系路径，预测尾实体
predicted_tail = composer.predict(head=alice_id, relation_path=[parent_id, parent_id])
```

**门控机制**：
```python
# 不是简单的矩阵乘法，而是学习何时"激活"每跳
gate_output = sigmoid(W_gate @ [e_s; W_r1 @ e_s; ...])

# 最终输出是门控加权的多跳组合
e_final = Σ_i gate_i * (W_ri @ e_s)
```

#### 3.2.4 reasoning/predicate_invention/ — RESCAL谓词发明

通过张量分解自动发现隐藏关系。

```python
from tensorlogic.reasoning.predicate_invention import invent_and_register_rescal

# 输入：已知的知识图谱三元组
known_triplets = [
    (alice, parent, bob),
    (bob, parent, charlie),
    # ... 更多三元组
]

# 执行RESCAL分解
invented_predicates = invent_and_register_rescal(
    triplets=known_triplets,
    num_entities=100,
    num_relations=10,
    rank=50,  # 分解维度
    num_invented=5  # 发明多少个新谓词
)

# invented_predicates 现在包含新发现的关系
# e.g., "ancestor", "sibling", ...
```

**数学原理**：
```python
# 知识图谱可以表示为三维稀疏张量
# X[i,j,k] = 1 如果 entity_i --relation_k--> entity_j

# RESCAL分解
# X ≈ Σ_r A @ W_r @ A^T
# A: 实体嵌入矩阵 (n × d)
# W_r: 关系矩阵 (d × d)

# 分解后，W_r 就是新发现的"谓词"
# 这些谓词不是人工定义的，而是从数据中自动学习到的
```

### 3.3 Transformer与RNN实现

TensorLogic的一个独特之处是将Transformer和RNN也用**tensor方程**重新实现，实现**神经+符号的统一**。

#### 3.3.1 Transformer as Tensor Equations

```python
from tensorlogic.transformers import Transformer

# 构建Transformer
transformer = Transformer(
    d_model=512,
    nhead=8,
    num_encoder_layers=6,
    num_decoder_layers=6
)

# 导出为tensor方程——可以看到Attention的数学本质！
equations = transformer.to_tensor_equations()
for eq in equations:
    print(eq)

# 输出示例：
# Attention: Q×K^T/√d → softmax → ×V
# FFN: max(0, X@W1)@W2
# LayerNorm: (X - μ) / σ * γ + β
```

**核心特点**：
- **Multi-head Attention** = `Q×K^T/√d → softmax → ×V`
- 编码器-解码器架构，带交叉注意力
- 可添加知识图谱约束的符号mask
- 完全可微，可与符号推理模块联合训练

#### 3.3.2 RNN/LSTM as Tensor Equations

```python
from tensorlogic.transformers import LSTM

# 标准LSTM
lstm = LSTM(input_size=128, hidden_size=256)

# Boolean模式LSTM（离散状态）
lstm_bool = LSTM(input_size=128, hidden_size=256, mode='boolean')
# hidden_state 是离散的 {0, 1}，而非连续向量
# 可解释性强，适合符号逻辑与神经的混合系统
```

**Boolean LSTM的应用**：
```python
# 场景：时序推理 + 逻辑约束
# 例如：监控网络入侵，要求：
# - 异常检测（神经部分）
# - 但必须满足特定的逻辑规则（符号部分）
# Boolean LSTM保证状态转换遵守规则
```

#### 3.3.3 Decoder-only Language Model

```python
from tensorlogic.transformers import DecoderOnlyLM

# GPT风格的语言模型
lm = DecoderOnlyLM(
    vocab_size=50304,
    d_model=768,
    n_layer=12,
    nhead=12
)

# 训练
PYTHONPATH=. python3 examples/shakespeare/train_shakespeare.py

# 生成
generated = lm.generate(prompt, max_new_tokens=100)
```

**Shakespeare模型效果**：
- ~1.5的验证loss（可与nanoGPT对比）
- TensorLogic特有：用tensor方程解释生成过程

---

## 四、快速入门

### 4.1 环境要求

| 依赖 | 版本要求 | 说明 |
|------|----------|------|
| Python | 3.8+ | 基础环境 |
| PyTorch | 2.0+ | 核心计算框架 |
| NumPy | - | 数值计算 |

### 4.2 安装方式

#### 方式一：开发安装（推荐贡献者）

```bash
git clone https://github.com/Kocoro-lab/tensorlogic.git
cd tensorlogic
pip install -e .
```

#### 方式二：直接安装

```bash
pip install git+https://github.com/Kocoro-lab/tensorlogic.git
```

#### 方式三：手动安装依赖

```bash
git clone https://github.com/Kocoro-lab/tensorlogic.git
cd tensorlogic
pip install -r requirements.txt

# 运行示例时需要设置PYTHONPATH
PYTHONPATH=. python3 examples/family_tree_symbolic.py
```

### 4.3 示例运行

#### 4.3.1 Boolean模式（家族关系推理）

```bash
python3 examples/family_tree_symbolic.py
```

**输出示例**：
```
Facts:
  parent(Alice, Bob) = True
  parent(Bob, Charlie) = True

Rules:
  grandparent(X, Y) :- parent(X, Z) ∧ parent(Z, Y)

Queries:
  grandparent(Alice, ?) → [Charlie]
  grandparent(?, Charlie) → [Alice]
```

**无训练，零成本推理**——规则即程序。

#### 4.3.2 Embedding模式（家族关系学习）

```bash
python3 examples/family_tree_embedding.py
```

**学习过程**：
```
Epoch 100, Loss: 0.0234, MRR: 0.892

# 学习到的嵌入可以用于：
# - 预测缺失的关系
# - 找相似的实体
# - 多跳推理
```

#### 4.3.3 多跳推理（Composer）

```bash
python3 examples/learnable_demo.py
```

**学习"祖父"关系**：
```
# 输入数据：只有parent(X, Y)三元组
# 学习目标：从少量样本学习grandparent = parent ∘ parent

Training: 10 epochs
  Epoch 1: Loss=0.52, Accuracy=0.45
  Epoch 10: Loss=0.01, Accuracy=0.99

# 模型学会了组合关系：parent @ parent → grandparent
```

#### 4.3.4 RESCAL谓词发明

```bash
python3 examples/predicate_invention_demo.py
```

**发现隐藏关系**：
```
Input: 基础家庭关系（parent, sibling）
RESCAL分解: rank=20, invented=3

Invented predicates:
  1. "ancestor" - 祖先关系
  2. "cousin" - 堂/表亲关系
  3. "same_family" - 同家族

这些关系没有人工标签，是从数据中自动发现的！
```

### 4.4 API最小使用

```python
from tensorlogic import TensorProgram
from tensorlogic.reasoning.embed import EmbeddingSpace
from tensorlogic.reasoning.composer import GatedMultiHopComposer

# ===== Boolean模式 =====
program = TensorProgram(mode='boolean')
result = program.forward(facts_and_rules)

# ===== Embedding模式 =====
space = EmbeddingSpace(num_entities=1000, embedding_dim=64, num_relations=50)
space.learn(positive_triplets, negative_triplets)
score = space.score(entity_a, relation_r, entity_b)

# ===== Composer模式 =====
composer = GatedMultiHopComposer(embedding_dim=64)
composer.learn(multi_hop_examples)
prediction = composer.predict(head=e1, relation_path=[r1, r2])
```

---

## 五、基准测试与性能分析

### 5.1 FB15k-237知识图谱基准

FB15k-237是标准的知识图谱链接预测基准：
- **实体数**：14,541
- **关系数**：237
- **三元组**：310,116

#### 5.1.1 测试方法

```bash
python3 examples/fb15k237_benchmark.py
```

使用RESCAL模型 + 1vsAll评分 + filtered MRR/Hits@K评估。

#### 5.1.2 结果对比

| 模型 | MRR | H@1 | H@3 | H@10 |
|------|-----|-----|-----|------|
| **TensorLogic RESCAL** | **0.347** | **0.258** | **0.382** | **0.524** |
| LibKGE RESCAL (参考) | 0.304 | 0.242 | 0.331 | 0.419 |
| DistMult | 0.241 | 0.155 | 0.263 | 0.419 |
| ComplEx | 0.247 | 0.158 | 0.275 | 0.428 |
| RotatE | 0.338 | 0.241 | 0.375 | 0.533 |

**结论**：TensorLogic RESCAL在所有指标上显著超越LibKGE参考实现（+14% MRR），且与RotatE等复杂模型竞争力相当。

### 5.2 内部基准测试套件

```bash
python3 examples/benchmark_suite.py
```

测试场景：
- **Family Tree**：家族关系推理（Boolean vs Embedding vs Composer）
- **Small KG**：小规模知识图谱（链路预测）
- **Synthetic**：合成数据（控制噪声/复杂度）

输出指标：
| 指标 | 说明 |
|------|------|
| **AUC** | 分类/预测质量 |
| **Hits@K** | Top-K准确率 |
| **F1** | 精确率/召回率平衡 |
| **训练时间** | 收敛速度 |
| **查询速度** | 推理延迟 |
| **内存** | 显存占用 |

### 5.3 性能优势

| 维度 | TensorLogic | 大模型 (LLM) |
|------|-------------|--------------|
| **模型大小** | 10-500 KB | GB级 |
| **训练时间** | 秒-分钟 | 小时-天 |
| **推理延迟** | <10ms | >100ms (API) |
| **幻觉** | Boolean模式=零 | 普遍存在 |
| **可解释性** | Tensor方程可见 | 黑盒 |

---

## 六、高级用法

### 6.1 混合推理（神经+符号）

TensorLogic可以将符号约束注入神经网络：

```python
from tensorlogic.transformers import Transformer
from tensorlogic.reasoning.embed import EmbeddingSpace

# 创建知识图谱约束
kg_space = EmbeddingSpace(...)
kg_space.learn(triplets)

# 创建Transformer并添加KG约束
transformer = Transformer(d_model=512, nhead=8)
transformer.add_knowledge_constraint(kg_space)

# 前向传播时，注意力会考虑KG结构
output = transformer.forward(input_ids, kg_mask=kg_adjacency)
```

**应用场景**：
- 知识感知的文本生成
- 带逻辑约束的对话系统
- 可解释的推荐系统

### 6.2 时序推理（LSTM + Boolean）

```python
from tensorlogic.transformers import LSTM

# Boolean LSTM：离散状态，适合状态机推理
lstm = LSTM(
    input_size=128,
    hidden_size=256,
    mode='boolean'  # 离散状态，而非连续向量
)

# 应用：网络入侵检测
# - 神经部分：异常检测
# - 符号部分：状态转换规则（如：SYN→ESTABLISHED→CLOSED）
```

### 6.3 Shakespeare语言模型

```bash
# 训练
PYTHONPATH=. python3 examples/shakespeare/train_shakespeare.py

# 生成
PYTHONPATH=. python3 examples/shakespeare/generate_shakespeare.py \
    --checkpoint checkpoints/shakespeare/best.pt
```

**TensorLogic特色**：可以用tensor方程解释生成过程：
```bash
PYTHONPATH=. python3 examples/shakespeare/generate_tensorlogic_shakespeare.py

# 输出每一步的tensor方程，而非黑盒生成
```

---

## 七、技术对比

### 7.1 与其他知识图谱嵌入对比

| 框架 | 评分函数 | 可微 | 组合推理 | 谓词发明 |
|------|----------|------|----------|----------|
| **TensorLogic** | 双线性 + 多种 | ✅ | ✅ GatedMultiHop | ✅ RESCAL |
| PyKEEN | 多种 | ✅ | ❌ | ❌ |
| LibKGE | 多种 | ✅ | ❌ | ❌ |
| AmpliGraph | 仅TransE | ✅ | ❌ | ❌ |
| Datalog Reasoners | 逻辑规则 | ❌ | ✅ | ❌ |

### 7.2 与LLM的互补关系

TensorLogic**不**是LLM替代品，而是互补工具：

| 场景 | 推荐方案 |
|------|----------|
| 开放域问答 | LLM |
| 确定性规则推理 | TensorLogic Boolean |
| 需要可解释性的决策 | TensorLogic Boolean |
| 知识图谱补全 | TensorLogic Embedding |
| 需要学习的复杂模式 | LLM |
| 小模型/边缘部署 | TensorLogic |

**混合架构示例**：
```
用户查询
    ↓
LLM理解意图 + 实体识别
    ↓
TensorLogic执行确定性推理
    ↓
LLM生成自然语言回答
```

---

## 八、局限性与未来方向

### 8.1 当前局限

| 局限 | 说明 | 变通方案 |
|------|------|----------|
| CNN/PGM未实现 | 卷积和概率图模型 | 期待后续 |
| Typed嵌入不完整 | 目前是方阵关系矩阵 | 计划支持矩形矩阵 |
| 非1:N/N:M关系 | 目前仅支持1:1 | 未来扩展 |
| GPU稀疏优化不足 | 当前实现未充分优化 | 期待GPU kernel |

### 8.2 未来规划

| 功能 | 状态 | 说明 |
|------|------|------|
| Tucker/CP分解 | 计划中 | 更高效的分解 |
| GPU稀疏kernel | 计划中 | 加速大规模KG |
| Datalog完整支持 | 计划中 | 后向链+溯因推理 |
| Typed嵌入 | 计划中 | 实体/关系类型系统 |

---

## 九、总结

### 9.1 核心价值

TensorLogic代表了**神经符号AI**的一个重要方向：

| 价值 | 说明 |
|------|------|
| **统一抽象** | Tensor方程同时表达神经+符号计算 |
| **零幻觉** | Boolean模式提供逻辑保证 |
| **自动发现** | RESCAL无需标签即可发明新谓词 |
| **极小模型** | 10-500KB，适合边缘部署 |
| **学术支撑** | 基于Domingos的论文，可复现可追溯 |

### 9.2 适用场景

| 场景 | 推荐模式 |
|------|----------|
| 合规/审计/医疗 | Boolean |
| 知识图谱补全 | Embedding |
| 多跳关系学习 | Composer |
| 隐藏关系发现 | Predicate Invention |
| 知识感知生成 | Transformer Hybrid |
| 时序+规则推理 | RNN Boolean |

### 9.3 资源链接

- 🌐 项目主页：https://github.com/Kocoro-lab/tensorlogic
- 📄 论文：https://arxiv.org/abs/2510.12269
- 🐍 PyPI：`pip install git+https://github.com/Kocoro-lab/tensorlogic.git`
- 📖 文档：项目README + examples/
- 🧪 基准测试：`examples/fb15k237_benchmark.py`
