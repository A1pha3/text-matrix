---
title: "Quantization 量化技术完全指南：从原理到 LLM 实战"
date: 2026-03-29T23:28:00+08:00
slug: quantization-llm-model-compression-guide
categories: ["技术笔记"]
tags: ["Quantization", "LLM", "模型压缩", "INT8", "INT4", "GPTQ", "llama.cpp"]
description: "详解量化技术原理：对称/非对称量化、异常值处理、逐通道量化、GPTQ/AWQ/llama.cpp 实战，让大模型体积缩小 4-8 倍。"
---

# Quantization 量化技术完全指南：从原理到 LLM 实战

> **目标读者**：想深入理解量化技术、压缩大模型体积的开发者
> **核心问题**：如何将 159GB 的大模型压缩到能在笔记本运行，同时只损失 5-10% 精度？

---

## 🎯 先看一个惊人的事实

**Qwen-3-Coder-Next** 是一个 800 亿参数的模型：
- **体积：159.4GB**
- 需要至少 159GB 内存才能运行
- 这还不算「大型」模型——据说前沿模型超过 **1 万亿**参数，需要 **2TB+** 内存

**但如果我告诉你：**

> 我们可以让 LLM 体积缩小 **4 倍**，速度提升 **2 倍**，精度只损失 **5-10%**，足以在普通笔记本上运行很 capable 的模型。

这就是 **Quantization（量化）** 的魔力。

---

## 🧠 第一章：为什么大模型这么大？

### 1.1 参数（Parameters）就是模型本身

当你把 LLM 加载到内存时，它基本上就是**一堆参数（也叫权重）**。

让我们从一个最简单的例子开始：

```
输入(input) = 2.0
    ↓
[参数(parameter) = 0.5]
    ↓
输出(output) = 1.0
```

这就是现代 AI 的基本构建块：输入一个值，乘以参数，得到输出。

### 1.2 层（Layers）让模型变大

但 LLM 比这复杂得多。它们有「层」结构：

```
输入层 ──┬──→ [层1: 节点A = 2.0×0.5 = 1.0] ──┬──→ [层2: 节点C = ...]
        └──→ [层1: 节点B = 2.0×0.5 = 1.0] ──┘
```

每两个节点之间的连接都有一个**参数**。当 2 个连接汇聚到同一个节点时，值会**相加**。

### 1.3 现代 LLM 的规模

现代 LLM 的规模令人窒息：

| 规模维度 | 典型数值 |
|----------|----------|
| 输入/输出节点 | 数十万个 |
| 隐藏层层数 | 数十层 |
| 每层节点数 | 数千个 |
| 每层连接数 | 数百万到数千万 |
| **总参数量** | **数十亿到万亿** |

这解释了为什么 LLM 需要巨大的内存和计算资源。

---

## 🔢 第二章：计算机如何表示数字？

### 2.1 位（Bits）与整数

计算机用 **1 和 0**（bits）来表示一切。

一个 **unsigned int8**（无符号 8 位整数）可以表示 0-255 的值：

```
位位置:   [128] [64] [32] [16] [8] [4] [2] [1]
二进制:     0    1    0    0   0   0   0   0
值: 64
```

每个位代表 2 的幂次方，加起来就是最终值。

### 2.2 整数是「离散」的

整数是**离散**的——1 和 3 之间只有 2，没有别的东西。计算机表示离散值毫无问题。

### 2.3 浮点数是「连续」的噩梦

但小数呢？1 和 3 之间有**无穷多**个值！

计算机无法表示无穷，所以它做了个**妥协**：

> **承诺在一定范围内保证精度**，超出范围的就是「尽力而为」。

### 2.4 32 位浮点数（float32）的结构

```
┌─────────────────────────────────────────────────────────┐
│  1 位 sign（符号）  │  8 位 exponent（指数）  │  23 位 significand（尾数）  │
└─────────────────────────────────────────────────────────┘
```

| 组成部分 | 位数 | 作用 |
|----------|------|------|
| **Sign（符号）** | 1 | 0=正数，1=负数 |
| **Exponent（指数）** | 8 | 表示范围：±3.40×10³⁸ |
| **Significand（尾数）** | 23 | 表示精度：7 位有效数字 |

**关键特性**：
- float32 可以表示的范围是 **±3.40×10³⁸**
- 但精度只有 **7 位有效数字**
- 值**不是均匀分布**的——越接近 0，精度越高

### 2.5 精度分布图

```
     -3.4×10³⁸                              +3.4×10³⁸
          │───────────────────────────────────────────│
          
          │    负数区域        │    0     │    正数区域      │
          │                  │          │                 │
          │ 稀疏 ←────────────┼─────────→ 密集           │
                              ↑
                          0 附近精度最高
```

**重要发现**：大多数 float32 能表示的值都集中在 0 附近！

### 2.6 更小的浮点格式对比

| 格式 | 符号位 | 指数位 | 尾数位 | 范围 | 精度 | 内存占用 |
|------|--------|--------|--------|------|------|----------|
| **float32** | 1 | 8 | 23 | ±3.4×10³⁸ | 7位 | 32 bits (4 bytes) |
| **float16** | 1 | 5 | 10 | ±65504 | 3位 | 16 bits (2 bytes) |
| **bfloat16** | 1 | 8 | 7 | ±3.4×10³⁸ | 约 2 位十进制有效数字 | 16 bits (2 bytes) |
| **float8** | 1 | 4 | 3 | 自定义 | ~1位 | 8 bits (1 byte) |
| **float4** | 1 | 2 | 1 | ±3 或 ±6 | 0.5位 | 4 bits (0.5 bytes) |

### 2.7 bfloat16 的设计哲学

Google Brain 创造了 **bfloat16**：

- **8 个指数位** = 和 float32 一样的宽范围
- **7 个尾数位** = 约 2 位十进制有效数字

为什么这样设计？因为 Google 发现：对于很多 LLM 场景，**不需要 float32 那样的高精度**，但需要足够大的数值范围来避免溢出。

bfloat16 有接近 float32 的范围，但只有一半的内存占用——这对 LLM 来说是很实用的 tradeoff。

### 2.8 模型参数的实际分布

作者下载了 6 个主流开源模型并分析参数分布：

**惊人发现：几乎所有参数都集中在 -0.1 到 0.1 之间！**

这意味着：
1. LLM 参数正好落在 float 能**最精确表示**的范围
2. 但存在少量**异常值（Outliers）**超出这个范围

---

## 📉 第三章：朴素量化的困境

### 3.1 什么是量化？

量化就是：**把大范围的值压缩到小范围**。

最简单的方法：**Round-to-Nearest（最近舍入）**

```
原始值: 1.23
  ↓ 四舍五入
量化值: 1
```

### 3.2 直接量化的灾难

如果我们简单地把 float16 → float8 → float4：

| 格式 | 结果 |
|------|------|
| float8 | 基本可用 |
| float4 | **灾难！输出始终为 0！** |

为什么 float4 会崩溃？

```
float4 范围: -3 到 +3
参数范围:   -0.89 到 +0.16

问题：
1. float4 要预留给 Infinity 和 NaN
2. 实际可用范围只有约 -3 到 +3
3. 参数集中在 -0.89 到 +0.16
4. 大量表示空间被浪费！
```

更糟糕的是：当参数被量化后，很多值变成了 **0**，导致输入无论如何变化，输出始终是 0。

---

## ⚖️ 第四章：对称量化（Symmetric Quantization）

### 4.1 核心思想：缩放（Scaling）

不是简单舍入，而是**按比例缩放**数据到更紧凑的范围：

```
原始范围 [-14, +14]     →    量化范围 [-7, +7]
    -14 ──────────────────→ -7
     0 ───────────────────→  0  （0 保持在中心）
    +8 ───────────────────→ +4
```

### 4.2 如何找到缩放因子？

```javascript
function quantize({ values, bits }) {
    // 1. 找到最大绝对值
    const vmax = Math.max(...values.map(Math.abs));  // e.g., 0.89
    
    // 2. 计算量化后的最大值（4-bit: 7, 8-bit: 127）
    const qmax = 2 ** (bits - 1) - 1;  // 7
    
    // 3. 计算缩放因子
    const scale = vmax / qmax;  // 0.89 / 7 = 0.127
    
    // 4. 量化：除以 scale，然后四舍五入
    return {
        values: values.map(v => Math.round(v / scale)),
        scale
    };
}

function dequantize({ values, scale }) {
    // 反量化：乘以 scale
    return values.map(v => v * scale);
}
```

### 4.3 实际例子

参数：`[-0.89, 0.16, 0.08, -0.13, 0.16, -0.54]`

```javascript
vmax = 0.89
qmax = 7
scale = 0.127

// 量化结果：
[-7, 1, 1, -1, 1, -4]
```

### 4.4 误差分析

| 原始值 | 反量化值 | 误差 | 误差率 |
|--------|----------|------|--------|
| -0.89 | -0.89 | 0 | 0.0% |
| 0.16 | 0.127 | -0.033 | -20.6% |
| 0.08 | 0.127 | +0.047 | +58.9% |
| -0.13 | -0.127 | +0.003 | -2.2% |
| 0.16 | 0.127 | -0.033 | -20.6% |
| -0.54 | -0.509 | +0.031 | -5.8% |

**平均误差：约 18%**

但体积缩小了 **4 倍**（16-bit → 4-bit）！

### 4.5 为什么对称量化更好？

1. **0 保持在中心**——保持正负对称性，这对神经网络很重要
2. **自动适应数据分布**——不浪费表示空间
3. **实现简单**——只需一个 scale 参数

---

## 📊 第五章：非对称量化（Asymmetric Quantization）

### 5.1 对称量化的局限

如果数据的分布**不是以 0 为中心**呢？

对称量化会浪费一半的范围。

### 5.2 非对称量化公式

```javascript
function quantizeAsymmetric({ values, bits }) {
    const vmin = Math.min(...values);
    const vmax = Math.max(...values);
    const qmax = 2 ** (bits - 1) - 1;  // 7 for 4-bit
    const qmin = -(2 ** (bits - 1));   // -8 for 4-bit
    
    // 缩放因子
    const scale = (vmax - vmin) / (qmax - qmin);
    
    // 零点偏移（关键区别！）
    const zeroPoint = qmin - Math.round(vmin / scale);
    
    return {
        values: values.map(v => Math.round(v / scale + zeroPoint)),
        scale,
        zeroPoint
    };
}

function dequantizeAsymmetric({ values, scale, zeroPoint }) {
    return values.map(v => (v - zeroPoint) * scale);
}
```

### 5.3 对称 vs 非对称对比

| 特性 | 对称量化 | 非对称量化 |
|------|----------|------------|
| 0 的位置 | 始终在中心 | 可能偏移 |
| 存储参数 | 只需 scale | 需 scale + zeroPoint |
| 实现复杂度 | 简单 | 稍复杂 |
| 适用场景 | 参数分布均匀 | 参数分布偏斜 |

---

## 🎯 第六章：异常值（Outliers）问题

### 6.1 异常值的存在

虽然大部分参数集中在 -0.1 到 0.1，但存在少量**异常值**超出这个范围。

### 6.2 异常值的影响

异常值会导致：
1. **scale 变大**——为了容纳异常值
2. **正常值的精度损失增加**——因为 scale 变大了

### 6.3 原文中的核心解法：分块量化

原文强调：实践中**不会把整个模型一次性量化**，而是把参数拆成很多小块，每块单独计算量化参数。

常见做法是 **Block-wise Quantization（分块量化）**，通常每 **32-256** 个参数一组：

```python
# 每个 block 单独计算 scale / zero_point
for block in blocks(weight, size=128):
    vmin = block.min()
    vmax = block.max()
    scale = (vmax - vmin) / 15
    zero_point = -8 - round(vmin / scale)
    quantized_block = round(block / scale + zero_point)
```

**效果**：
- 少量异常值只会污染当前 block，不会拖累整个模型
- 每个 block 的取值范围更窄，scale 更小，量化误差通常更低

### 6.4 进一步的工程优化：逐通道量化

除了分块量化，工程上也常见 **Per-Channel Quantization（逐通道量化）**：

- 每个通道单独计算 scale
- 更适合处理不同通道分布差异明显的权重
- 但这属于比原文更进一步的扩展知识

---

## 🧪 第七章：衡量量化质量

### 7.1 困惑度（Perplexity）

这是衡量语言模型质量的主要指标：

```
Perplexity = 2^(-1/N × Σ log₂ P(wi))
```

- **越低越好**——表示模型预测越准确
- 量化后 Perplexity 略有上升是正常的

原文给出的一个实测例子：

| 格式 | Perplexity |
|------|------------|
| bfloat16 | 8.186 |
| 8-bit symmetric | 8.193（+0.1%） |
| 4-bit asymmetric | 8.563（+4.6%） |
| 4-bit symmetric | 8.710（+6.4%） |
| 2-bit asymmetric | 66.1（+707.5%） |

这个结果说明：**8-bit 几乎无损，4-bit 有一定退化但仍可用，2-bit 在该模型上已经接近崩溃。**

### 7.2 KL 散度（KL Divergence）

Perplexity 只看“正确 token 的概率”，但它看不到**整个概率分布**如何变化。

KL 散度衡量的是：**量化后的输出分布，与原始模型输出分布有多不一样**。

- **越低越好**
- 0 表示两个分布完全重合
- 适合比较“同一个模型的不同量化版本”

原文中的实测结果：

| 格式 | Mean KL divergence |
|------|--------------------|
| 8-bit symmetric | 0.0008 |
| 4-bit asymmetric | 0.0593 |
| 4-bit symmetric | 0.0675 |
| 2-bit asymmetric | 2.1447 |

### 7.3 基准测试（Benchmarking）

除了看统计指标，更直接的方式是跑任务基准。原文使用了 **GPQA Diamond** 做示例：

| 格式 | 正确率 | 错误率 | 无回答 |
|------|--------|--------|--------|
| bfloat16 | 66.7% | 33.3% | 0% |
| 8-bit symmetric | 73.2% | 26.8% | 0% |
| 4-bit asymmetric | 62.6% | 36.4% | 1% |
| 4-bit symmetric | 66.2% | 29.3% | 4.5% |
| 2-bit asymmetric | 1% | 2% | 97% |

这组结果也提醒我们：**不要把某个百分比精度损失当成普适规律**，不同模型、不同任务、不同量化实现，表现差异会很大。

### 7.4 量化精度对照表

| 量化格式 | 常见现象 | 体积缩小 | 建议理解方式 |
|----------|----------|----------|--------------|
| FP16 / BF16 | 基本作为精度基线 | 2x（相对 FP32） | 适合做参考版本 |
| INT8 | 往往接近无损 | 4x（相对 FP32） | 很多场景的稳妥选择 |
| INT4 | 可能有可感知退化，但通常仍可用 | 8x（相对 FP32） | 适合内存受限部署 |
| INT2 | 很容易质量崩溃 | 16x（相对 FP32） | 必须按具体模型实测 |

---

## 🛠️ 第八章：实战工具

### 8.1 llama.cpp

纯 C/C++ 实现，支持 CPU 和 GPU：

```bash
# 安装
brew install llama.cpp

# 下载并启动 BF16 模型
llama-server -hf unsloth/Qwen3.5-9B-GGUF:BF16 --port 8000

# 量化模型
cd ~/Library/Caches/llama.cpp
llama-quantize unsloth_Qwen3.5-9B-GGUF_Qwen3.5-9B-BF16.gguf \
               unsloth_Qwen3.5-9B-GGUF_Qwen3.5-9B-Q8_0.gguf \
               Q8_0

# 运行量化模型
llama-cli -m unsloth_Qwen3.5-9B-GGUF_Qwen3.5-9B-Q8_0.gguf
```

**原文实际使用的格式**：Q8_0（8-bit symmetric）、Q4_1（4-bit asymmetric）、Q4_0（4-bit symmetric）、Q2_K（2-bit asymmetric 风格）

### 8.2 GPTQ

常见的后训练量化方法，通常需要校准数据：

```python
pip install auto-gptq

from auto_gptq import AutoGPTQForCausalLM, BaseQuantizeConfig

quant_config = BaseQuantizeConfig(bits=4, group_size=128)
model = AutoGPTQForCausalLM.from_pretrained("your-model", quantize_config=quant_config)
```

### 8.3 AWQ（Activation-Aware Quantization）

考虑激活分布的 4-bit 量化：

```python
pip install awq

from transformers import AutoTokenizer
from awq import AutoAWQForCausalLM

model = AutoAWQForCausalLM.from_pretrained("your-model")
tokenizer = AutoTokenizer.from_pretrained("your-model")
quant_config = {"zero_point": True, "q_group_size": 128}
model.quantize(tokenizer, quant_config=quant_config)
```

### 8.4 bitsandbytes

Hugging Face 集成：

```python
pip install bitsandbytes

from transformers import AutoModelForCausalLM, BitsAndBytesConfig

quant_config = BitsAndBytesConfig(load_in_8bit=True)

model = AutoModelForCausalLM.from_pretrained(
    "your-model",
    quantization_config=quant_config,
)
```

### 8.5 工具对比

| 工具 | 量化格式 | 精度 | 速度 | 易用性 |
|------|----------|------|------|--------|
| llama.cpp | Q4/Q5/Q8 | 高 | 快 | ⭐⭐⭐ |
| GPTQ | INT4 | 很高 | 中 | ⭐⭐⭐⭐ |
| AWQ | INT4 | 很高 | 快 | ⭐⭐⭐⭐ |
| bitsandbytes | INT8/INT4 | 高 | 快 | ⭐⭐⭐⭐⭐ |

---

## 💡 第九章：核心洞察

### 9.1 量化是有损压缩

> **没有免费午餐**——量化必然损失精度。目标是让精度损失在可接受范围内。

### 9.2 对称 vs 非对称

| 场景 | 推荐方法 |
|------|----------|
| 参数分布以 0 为中心 | 对称量化 |
| 参数分布偏斜 | 非对称量化 |

### 9.3 异常值是主要瓶颈

异常值会把 scale 拉大，降低正常值的精度。原文强调的主解法是**分块量化**，这样异常值只影响局部 block；逐通道量化则是常见的进一步工程优化。

### 9.4 4-bit 是实用下限

- **INT4**（4-bit）：在很多模型上是很实用的压缩点，但精度损失要看模型、任务和实现
- **INT2**（2-bit）：在原文测试的 Qwen3.5 9B 配置里已经基本不可用
- **NF4**（4-bit 归一化）：更好地保留精度，是新兴格式

### 9.5 模型在进步，量化也要演进

随着模型能力提升，量化策略也在进化：
- 更智能的异常值处理
- 量化感知训练（QAT）
- 更高效的稀疏量化

---

## 🎯 第十章：总结与展望

### 核心公式

```python
# 对称量化
scale = max(|weight|) / (2^(bits-1) - 1)
quantized = round(weight / scale)
dequantized = quantized * scale

# 非对称量化
qmax = 2^(bits-1) - 1
qmin = -(2^(bits-1))
scale = (max(weight) - min(weight)) / (qmax - qmin)
zero_point = qmin - round(min(weight) / scale)
quantized = round(weight / scale) + zero_point
dequantized = (quantized - zero_point) * scale
```

### 关键数据

| 指标 | 数值 |
|------|------|
| Qwen-3-Coder-Next | 80B 参数，159GB |
| 量化可达到 | 体积缩小 4-8x |
| 精度损失 | 8-bit 通常很小，4-bit 常见为轻到中度退化 |
| 速度提升 | 往往会更快，但提升幅度依硬件和实现而变 |

### 实用建议

1. **内存受限？** 可以优先尝试 INT4，但不要只看权重体积；实际运行还要考虑 KV cache、buffer 和框架开销
2. **精度优先？** 用 INT8 或 FP16
3. **CPU 部署？** 用 llama.cpp，尤其适合本地机器快速验证
4. **GPU 部署？** 用 GPTQ/AWQ，GPU 加速

### 未来趋势

- **更小的模型、更高的精度**：随着量化技术进步，会有更好的 tradeoff
- **硬件支持**：新一代 NPU/VPU 内置量化支持
- **自动化量化**：AutoQ 等自动寻找最优量化策略

---

## 📚 参考资源

- [ngrok: Quantization from the Ground Up](https://ngrok.com/blog/quantization)（原文，6,658 词，含大量交互式图表）
- [GPTQ 论文](https://arxiv.org/abs/2210.17323)
- [LLM.int8() 论文](https://arxiv.org/abs/2208.07339)
- [llama.cpp GitHub](https://github.com/ggerganov/llama.cpp)
- [AWQ GitHub](https://github.com/mit-han-lab/llm-awq)
- [Hugging Face 量化文档](https://huggingface.co/docs/transformers/quantization)

---

> **最后一句话**：Quantization 让我们能在普通硬件上运行超大模型。理解它，你就能驾驭大模型的部署艺术。
