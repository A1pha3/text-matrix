---
title: "Quantization 量化：从原理到实践，让大模型体积缩小 4 倍"
date: 2026-03-29T23:23:00+08:00
slug: quantization-llm-model-compression-guide
categories: ["技术笔记"]
tags: ["Quantization", "LLM", "模型压缩", "INT8", "INT4"]
description: "详解量化技术原理：对称/非对称量化、异常值处理、GPTQ/llama.cpp 实战，让大模型体积缩小 4-8 倍同时只损失少量精度。"
---

# Quantization 量化：从原理到实践，让大模型体积缩小 4 倍

> **目标读者**：想了解如何压缩大模型体积的开发者
> **核心问题**：如何将大模型压缩到能在笔记本电脑上运行，同时只损失少量精度？

---

## 🎯 概述

**Quantization（量化）** 是一种**有损压缩**技术，通过将高精度浮点数映射到低精度表示来减小模型体积。

> Qwen-3-Coder-Next 是一个 80B 参数模型，占用 **159.4GB** 内存。这还不算大，因为据说前沿模型的参数超过 1 万亿，需要至少 **2TB** 内存。

但通过量化技术，我们可以：
- **体积缩小 4 倍**（16-bit → 4-bit）
- **速度提升 2 倍**
- **精度只损失 5-10%**

---

## 🧠 为什么大模型这么大？

### 1. 参数即模型

大模型的**参数（Parameters）**，也叫「权重（Weights）」，就是模型在内存或磁盘中的主体。

```
输入(2.0) → [参数 0.5] → 输出(1.0)
```

### 2. 层（Layers）结构

现代 LLM 有数百层的节点，每层有数千个节点，全部密集连接：

```
输入层 → 隐藏层1 → 隐藏层2 → ... → 输出层
```

一个典型的 Transformer 架构：
- **数百个输入/输出节点**
- **数十层隐藏层**
- **每层数千个节点**

这导致：
- **数十亿甚至数万亿个参数**

---

## 🔢 计算机如何存储数字？

### 整数 vs 浮点数

**整数（Integer）** 是离散的：1 和 3 之间只有 2。

**浮点数（Float）** 用于表示小数，1 和 3 之间有**无穷多**个值。计算机无法表示无穷，所以做了妥协：**承诺在一定范围内保证精度**。

### 32 位浮点数（float32）

```
┌──────────────────────────────────────────┐
│  1 位 sign（符号）  │  8 位 exponent（指数）  │  23 位 significand（尾数）  │
└──────────────────────────────────────────┘
```

| 组成部分 | 位数 | 作用 |
|----------|------|------|
| Sign（符号） | 1 | 正负号 |
| Exponent（指数） | 8 | 表示范围：±3.40×10³⁸ |
| Significand（尾数） | 23 | 表示精度：7 位有效数字 |

### 精度与范围的取舍

| 格式 | 指数位 | 尾数位 | 范围 | 精度 |
|------|--------|--------|------|------|
| float32 | 8 | 23 | ±3.40×10³⁸ | 7 位有效数字 |
| float16 | 5 | 10 | ±65504 | 3 位有效数字 |
| bfloat16 | 8 | 7 | ±3.40×10³⁸ | 2 位有效数字 |
| float8 | 4 | 3 | 自定义 | 自定义 |

### 关键发现：参数分布

对 6 个主流开源模型的分析显示：

**绝大多数参数集中在 -0.1 到 0.1 之间**——这正好是 float 能最精确表示的范围！

这意味着：
1. 模型不需要很宽的**范围（Range）**
2. 但需要较高的**精度（Precision）**
3. 异常值（Outliers）很少但存在

---

## 📉 朴素量化的困境

### 直接舍入（Round-to-Nearest）

最简单的量化方法：将 float16 四舍五入到 float8。

但这会出问题：

| 格式 | 结果 |
|------|------|
| float8 | 基本可用 |
| float4 | **完全崩溃**——输出始终为 0！ |

### 问题根源

float4 的范围是 -3 到 3，但参数的分布是 -0.89 到 0.16。大部分范围被浪费了，而且 float4 还要预留给 Infinity 和 NaN。

```
  -3                              3
   │───────────────────────────────│
   -0.89         0                0.16
        └─────────────────────────┘
              参数分布范围
   └───────────────────────────────┘
           float4 范围（浪费）
```

---

## ⚖️ 对称量化（Symmetric Quantization）

### 核心思想

不是简单舍入，而是**缩放（Scaling）** 数据到更紧凑的范围。

### 量化公式

```javascript
function quantize({ values, bits }) {
    const vmax = Math.max(...values.map(Math.abs));  // 最大绝对值
    const qmax = 2 ** (bits - 1) - 1;              // 量化后最大值（如 4-bit: 7）
    const scale = vmax / qmax;                       // 缩放因子
    
    return {
        values: values.map(v => Math.round(v / scale)),
        scale
    };
}

function dequantize({ values, scale }) {
    return values.map(v => v * scale);
}
```

### 示例

假设参数为：`[-0.89, 0.16, 0.08, -0.13, 0.16, -0.54]`

量化到 4-bit（范围 -7 到 7）：

```javascript
const vmax = 0.89;
const qmax = 7;
const scale = 0.89 / 7 = 0.127;

// 量化结果
[-7, 1, 1, -1, 1, -4]
```

### 误差分析

| 原始值 | 反量化值 | 误差 |
|--------|----------|------|
| -0.89 | -0.89 | 0% |
| 0.16 | 0.127 | -20.6% |
| 0.08 | 0.127 | +58.9% |
| -0.13 | -0.127 | -2.2% |
| 0.16 | 0.127 | -20.6% |
| -0.54 | -0.509 | -5.8% |

**平均误差约 18%**——体积却缩小了 4 倍！

### 为什么对称量化更好？

1. **0 始终在中心**——保持正负对称性
2. **缩放因子自动适应数据分布**——不浪费范围
3. **没有预留 Infinity/NaN**——全部用于有效值

---

## 📊 非对称量化（Asymmetric Quantization）

### 对称量化的局限

对称量化要求 0 在中心，但如果数据的分布**不对称**呢？

例如：参数全为正数，或大部分为负数。

### 非对称量化公式

```javascript
function quantizeAsymmetric({ values, bits }) {
    const vmin = Math.min(...values);
    const vmax = Math.max(...values);
    const qmin = 0;
    const qmax = 2 ** bits - 1;
    
    const scale = (vmax - vmin) / (qmax - qmin);
    const zeroPoint = Math.round(qmin - vmin / scale);
    
    return {
        values: values.map(v => Math.round(v / scale) + zeroPoint),
        scale,
        zeroPoint
    };
}

function dequantizeAsymmetric({ values, scale, zeroPoint }) {
    return values.map(v => (v - zeroPoint) * scale);
}
```

### 对比

| 方法 | 优点 | 缺点 |
|------|------|------|
| 对称量化 | 0 居中，实现简单 | 不适合不对称分布 |
| 非对称量化 | 范围利用更充分 | 实现复杂，需存储 zero_point |

---

## 📈 异常值问题

### 异常值的存在

虽然大部分参数集中在 0 附近，但**存在少量异常值（Outliers）**——这些值超出正常范围。

### 影响

异常值会导致：
1. **缩放因子变大**——正常值的精度损失增加
2. **量化效果变差**

### 解决方案

1. **逐通道量化（Per-Channel Quantization）**：每个通道独立计算缩放因子
2. **GPTQ/QAT 等高级方法**：使用校准数据集优化量化参数

---

## 🧪 如何衡量量化后的质量损失？

### 困惑度（Perplexity）

这是衡量语言模型质量的主要指标：

```
Perplexity = 2^(-1/N * Σ log₂ P(wi))
```

- **越低越好**——表示模型预测越准确

### 比特每字节（BPB）

```python
val_bpb = validation_bits / bytes_per_character
```

- 用于 LLM 训练研究
- **越低越好**

### 任务指标

| 任务类型 | 指标 |
|----------|------|
| 文本生成 | BLEU, ROUGE |
| 问答 | Exact Match, F1 |
| 代码生成 | Pass@1, Code-BLEU |

---

## 🛠️ 实战：使用量化模型

### 常见量化格式

| 格式 | 精度损失 | 体积缩小 | 适用场景 |
|------|----------|----------|----------|
| FP16 | 无 | 2x | 精度优先 |
| INT8 | 1-3% | 4x | 平衡之选 |
| INT4 | 5-10% | 8x | 内存受限 |
| INT2 | 10-20% | 16x | 边缘设备 |

### 使用 GPTQ 量化

```bash
pip install auto-gptq

from transformers import AutoModelForCausalLM, AutoTokenizer
from gptq import GPTQQuantizer

model = AutoModelForCausalLM.from_pretrained("your-model")
quantizer = GPTQQuantizer(bits=4)
quantized_model = quantizer.quantize_model(model, tokenizer)
```

### 使用 llama.cpp

```bash
# 量化模型
./quantize ./models/llama-7b/ggml-model-f16.gguf ./models/llama-7b/ggml-model-q4_0.gguf q4_0

# 运行量化模型
./main -m ./models/llama-7b/ggml-model-q4_0.gguf -n 512
```

---

## 📚 常见量化工具

| 工具 | 支持格式 | 特点 |
|------|----------|------|
| llama.cpp | FP16, INT8, INT4, INT2 | 纯 C/C++，支持 GPU 加速 |
| GPTQ | INT4 | 4-bit 量化，需校准数据 |
| AWQ | INT4 | 激活感知量化 |
| bitsandbytes | INT8, NF4 | Hugging Face 集成 |
| TensorRT-LLM | FP16, INT8, INT4 | NVIDIA 优化 |

---

## 💡 核心洞察

1. **量化是有损压缩**——必然会损失精度
2. **对称 vs 非对称**：对称适合分布均匀，非对称适合极端分布
3. **异常值是关键瓶颈**——需要特殊处理
4. **4-bit 是实用下限**——再低精度损失过大
5. **逐通道量化优于逐张量量化**——更好地保留重要特征

---

## 🎯 总结

Quantization 是让大模型走向实用的关键技术：

- **体积缩小 4-8 倍**（INT8/INT4）
- **速度提升 2-4 倍**
- **精度只损失 5-10%**

配合 GPU 加速和量化感知训练，**在普通笔记本电脑上运行 70B 模型**已经成为可能。

随着模型能力提升和硬件进步，最优的量化策略也在不断演进。持续关注这一领域，你就能在模型部署上获得显著收益。

---

## 📚 参考资源

- [ngrok: Quantization from the Ground Up](https://ngrok.com/blog/quantization)（原文）
- [GPTQ 论文](https://arxiv.org/abs/2210.17323)
- [llama.cpp GitHub](https://github.com/ggerganov/llama.cpp)
- [Hugging Face 量化文档](https://huggingface.co/docs/transformers/quantization)