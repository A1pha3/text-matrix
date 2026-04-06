---
title: "TimesFM：Google Research 时间序列基础模型完全指南"
date: 2026-04-06T21:28:00+08:00
slug: "timesfm-google-time-series-foundation-model-guide"
description: "全面介绍 Google Research 的 TimesFM 时间序列基础模型，涵盖 2.5 版本的 200M 参数、16k 上下文、连续分位数预测等核心升级，以及 PyTorch/Flax 推理部署和 BigQuery 集成。"
draft: false
categories: ["技术笔记"]
tags: ["TimesFM", "时间序列", "Google Research", "ICML", "预测模型", "PyTorch", "BigQuery"]
---

## 学习目标

通过本文，你将全面掌握以下核心能力：

- 深入理解 TimesFM 的项目定位、技术架构和 1-bit 预测原理
- 掌握 TimesFM 2.5 的核心升级（200M 参数、16k 上下文、连续分位数预测）
- 学会使用 PyTorch 和 Flax 两种后端进行时间序列预测
- 理解 XReg 共变量支持和高频/低频时间序列处理
- 掌握在 BigQuery 和 Hugging Face 上的部署方法
- 理解 AGENTS.md 技能入口和 AI Agent 集成

---

## 1. 项目概述

### 1.1 是什么

TimesFM（Time Series Foundation Model）是 Google Research 开发的**预训练时间序列基础模型**，专门用于时间序列预测任务。

它基于 **ICML 2024** 论文 "A decoder-only foundation model for time-series forecasting"，代表了时间序列预测领域的重要突破。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | **15.1k** |
| GitHub Forks | **1.3k** |
| Watchers | **104** |
| 贡献者 | **21** |
| License | **Apache-2.0** |

### 1.3 技术栈

| 语言 | 占比 |
|------|------|
| Python | 68.3% |
| HTML | 22.7% |
| Jupyter Notebook | 8.6% |

### 1.4 版本历史

| 版本 | 发布日期 | 主要变化 |
|------|----------|----------|
| **TimesFM 2.5** | 2025-09-15 | 200M 参数，16k 上下文，连续分位数 |
| TimesFM 2.0 | 早期版本 | 500M 参数，2048 上下文 |
| TimesFM 1.0 | 存档 | 位于 v1 目录 |

---

## 2. TimesFM 2.5 核心升级

### 2.1 与 2.0 对比

TimesFM 2.5 相比 2.0 实现了**更小、更强、更长上下文**的突破：

| 特性 | TimesFM 2.0 | TimesFM 2.5 |
|------|--------------|---------------|
| **参数量** | 500M | **200M** ⬇️ |
| **上下文长度** | 2048 | **16k** ⬆️ |
| **分位数预测** | 固定 | **连续分位数**（最高 1k horizon） |
| **频率指示器** | 需要 | **移除** ⬇️ |
| **分位数头** | 内置 | **可选 30M** |

### 2.2 为什么参数减少反而更强

TimesFM 2.5 使用了更先进的**知识蒸馏**和**量化技术**：

```python
# 更小的模型 = 更低的延迟和成本
# 但通过更好的预训练策略保持精度
model = timesfm.TimesFM_2p5_200M_torch.from_pretrained(
    "google/timesfm-2.5-200m-pytorch"
)
```

### 2.3 连续分位数预测

TimesFM 2.5 支持**连续分位数预测**，最高可达 1k horizon：

```python
model.compile(
    timesfm.ForecastConfig(
        max_context=1024,
        max_horizon=256,
        use_continuous_quantile_head=True,  # 启用连续分位数
        # 可选 30M 分位数头
    )
)

# 输出形状: (batch_size, horizon, num_quantiles)
# num_quantiles 包括均值 + 10个分位数 (10th-90th)
```

---

## 3. 核心技术原理

### 3.1 基础架构

TimesFM 基于 **Transformer decoder-only 架构**：

```
输入时间序列
    ↓
Patch Embedding（补丁化）
    ↓
Transformer Decoder（自注意力）
    ↓
预测头（Point / Quantile）
    ↓
输出预测
```

### 3.2 补丁化（Patchification）

TimesFM 将时间序列划分为**固定大小的补丁**：

```python
# 示例：将 100 个时间点划分为 10 个补丁（每个补丁 10 个点）
input_series = np.linspace(0, 1, 100)  # 输入
# 补丁化后变成更短的表示
```

### 3.3 频率感知

虽然 2.5 版本移除了频率指示器，但模型仍然**频率感知**：

```python
# 不同频率的时间序列应该有不同的表现
# 模型通过预训练学会了处理高频（股票）和低频（GDP）数据
```

### 3.4 XReg 共变量支持

TimesFM 2.5 支持**外部共变量（XReg）**：

```python
from timesfm.plotters import forecast_with_covariates

# 预测时可以加入外部变量（节假日、促销等）
result = forecast_with_covariates(
    model=model,
    covariates=[holiday_indicator, price_promotion],
    horizon=24
)
```

---

## 4. 快速上手

### 4.1 安装

**克隆仓库**

```bash
git clone https://github.com/google-research/timesfm.git
cd timesfm
```

**创建虚拟环境**

```bash
# 使用 uv 创建虚拟环境
uv venv
source .venv/bin/activate  # Linux/Mac
# Windows: .venv\Scripts\activate
```

**安装依赖**

```bash
# PyTorch 后端（推荐）
uv pip install -e .[torch]

# 或者 Flax 后端
uv pip install -e .[flax]

# 如果需要 XReg 支持
uv pip install -e .[xreg]
```

### 4.2 基本预测

```python
import torch
import numpy as np
import timesfm

# 设置高精度矩阵乘法
torch.set_float32_matmul_precision("high")

# 加载模型
model = timesfm.TimesFM_2p5_200M_torch.from_pretrained(
    "google/timesfm-2.5-200m-pytorch"
)

# 编译模型（加速推理）
model.compile(
    timesfm.ForecastConfig(
        max_context=1024,
        max_horizon=256,
        normalize_inputs=True,
        use_continuous_quantile_head=True,
        force_flip_invariance=True,
        infer_is_positive=True,
        fix_quantile_crossing=True,
    )
)

# 预测
point_forecast, quantile_forecast = model.forecast(
    horizon=12,  # 预测未来 12 个时间点
    inputs=[
        np.linspace(0, 1, 100),        # 输入序列 1
        np.sin(np.linspace(0, 20, 67)), # 输入序列 2
    ],
)

print(f"点预测形状: {point_forecast.shape}")      # (2, 12)
print(f"分位数预测形状: {quantile_forecast.shape}") # (2, 12, 10)
```

### 4.3 输出解释

```python
# point_forecast: 每个序列的点预测
# shape: (num_series, horizon)

# quantile_forecast: 分位数预测
# shape: (num_series, horizon, num_quantiles)
# quantiles: [mean, 10th, 20th, ..., 90th]

# 提取特定分位数
mean_pred = quantile_forecast[:, :, 0]      # 均值
lower_80 = quantile_forecast[:, :, 1]       # 10th 分位数（下界）
upper_80 = quantile_forecast[:, :, -1]      # 90th 分位数（上界）
```

---

## 5. 高级用法

### 5.1 长上下文预测

TimesFM 2.5 支持最高 **16k 上下文**：

```python
# 使用长上下文
long_input = np.random.randn(16000)  # 16k 长度的输入

point_pred, quantile_pred = model.forecast(
    horizon=100,
    inputs=[long_input],
)
```

### 5.2 多序列同时预测

```python
# 同时预测多个序列
inputs = [
    np.sin(np.linspace(0, 10, 500)),   # 序列 1: 正弦波
    np.random.randn(500),               # 序列 2: 随机
    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], # 序列 3: 线性增长
]

point_pred, quantile_pred = model.forecast(
    horizon=24,
    inputs=inputs,
)

# 输出形状: (3, 24) 和 (3, 24, 10)
```

### 5.3 批量预测

```python
from timesfm.data_loader import DatasetLoader

# 使用数据加载器批量处理
loader = DatasetLoader("etth1", batch_size=32)
batch = loader.get_batch()

forecasts = model.forecast(
    horizon=24,
    inputs=batch["input"],
)
```

### 5.4 共变量预测

```python
# 带有外部变量的预测
holidays = [0, 0, 0, 1, 0, 0, 0] * 4  # 节假日标记
promotions = [0, 1, 0, 0, 0, 0, 1] * 4  # 促销标记

covariates = np.stack([holidays, promotions], axis=0)

point_pred, quantile_pred = forecast_with_covariates(
    model=model,
    covariates=covariates,
    horizon=24,
    context=input_series,
)
```

---

## 6. Hugging Face 集成

### 6.1 模型下载

```python
from huggingface_hub import hf_hub_download

# 下载模型
model_path = hf_hub_download(
    repo_id="google/timesfm-2.5-200m-pytorch",
    filename="timesfm-2.5-200m-pytorch.pt",
)

# 加载
model = timesfm.TimesFM_2p5_200M_torch.from_pretrained(model_path)
```

### 6.2 Hugging Face 集合

TimesFM 官方 Hugging Face 集合：https://huggingface.co/collections/google/timesfm-release-66e4be5fdb56e960c1e482a6

包含所有版本的模型权重：

| 模型 | 说明 |
|------|------|
| google/timesfm-2.5-200m-pytorch | PyTorch 版本 |
| google/timesfm-2.5-200m-flax | Flax 版本 |
| google/timesfm-2.0-500m | 旧版本（存档） |

---

## 7. BigQuery 集成

### 7.1 官方支持

TimesFM 已集成到 **Google BigQuery**：

```sql
-- BigQuery ML 预测
SELECT *
FROM ML.FORECAST(
    MODEL `timesfm`,
    STRUCT(24 AS horizon),
    input_series
)
```

参考：https://cloud.google.com/bigquery/docs/timesfm-model

### 7.2 企业部署优势

| 特性 | 说明 |
|------|------|
| **无需管理基础设施** | Google Cloud 托管 |
| **自动扩缩容** | 随数据量自动调整 |
| **安全合规** | 企业级安全标准 |
| **与其他 BigQuery ML 集成** | 端到端 ML 管道 |

---

## 8. AGENTS.md 技能入口

### 8.1 什么是 AGENTS.md

TimesFM 在 2026-03-19 添加了 **AGENTS.md 技能入口**（由 @borealBytes 贡献）：

```bash
# 仓库根目录有 AGENTS.md
ls -la AGENTS.md
# -rw-r--r--  1 user  staff  1583 Mar 23  2026 AGENTS.md
```

### 8.2 AI Agent 集成

```markdown
<!-- AGENTS.md 内容示例 -->
# TimesFM AI Agent Skills

## Forecasting Agent
Use TimesFM to forecast time series data.

## Anomaly Detection
Detect anomalies using quantile predictions.

## Usage
1. Load your time series data
2. Call TimesFM forecast
3. Interpret quantile predictions
```

### 8.3 技能使用

```python
# 在 AI Agent 中使用 TimesFM
from timesfm.agents import ForecastingAgent

agent = ForecastingAgent(model=model)
result = agent.run(
    task="Forecast the next 24 hours of sales data",
    data=sales_df
)
```

---

## 9. 技术架构深度解析

### 9.1 整体架构

```
TimesFM
├── src/timesfm/
│   ├── models/           # 模型定义
│   │   ├── patchformer.py  # PatchFormer 架构
│   │   └──塔头
│   ├── data_loader.py    # 数据加载
│   ├── trainer.py        # 训练逻辑
│   └── plotters.py       # 可视化
├── timesfm-forecasting/  # 预测工具
├── v1/                   # v1.0 存档代码
└── notebooks/            # 示例笔记
```

### 9.2 PatchFormer 核心

```python
class PatchFormer(nn.Module):
    """TimesFM 核心架构"""
    
    def __init__(self, config):
        super().__init__()
        # 补丁嵌入
        self.patch_embed = nn.Linear(
            config.patch_len,
            config.d_model
        )
        
        # Transformer 解码器
        self.blocks = nn.ModuleList([
            TransformerBlock(config)
            for _ in range(config.n_layers)
        ])
        
        # 输出头
        self.head = nn.Linear(
            config.d_model,
            config.patch_len
        )
```

### 9.3 预测配置

```python
@dataclass
class ForecastConfig:
    max_context: int = 2048      # 最大上下文长度
    max_horizon: int = 512       # 最大预测长度
    normalize_inputs: bool = True  # 是否归一化输入
    use_continuous_quantile_head: bool = False  # 连续分位数
    force_flip_invariance: bool = False  # 翻转不变性
    infer_is_positive: bool = False     # 推断非负
    fix_quantile_crossing: bool = True  # 修复分位数交叉
```

---

## 10. 性能基准

### 10.1 主要基准数据集

| 数据集 | 说明 | 领域 |
|--------|------|------|
| ETT | 电力变压器温度 | 能源 |
| Weather | 气象数据 | 气象 |
| Electricity | 用电量 | 能源 |
| M4 | 竞赛数据集 | 综合 |
| LongForecast | 长预测任务 | 综合 |

### 10.2 性能表现

TimesFM 在多个基准数据集上表现优异：

```python
# 典型性能（M4 数据集）
# MSAE (Mean Scaled Absolute Error): 领先基线模型
# 预测速度: 10-100x 加速 vs 传统方法
```

### 10.3 延迟对比

| 方法 | 1000 序列预测延迟 |
|------|-------------------|
| 传统 ARIMA | ~10 分钟 |
| Prophet | ~5 分钟 |
| **TimesFM 2.5** | **~10 秒** |

---

## 11. 常见问题

### 11.1 如何选择 PyTorch vs Flax

| 场景 | 推荐后端 |
|------|---------|
| **通用场景** | PyTorch |
| **TPU 训练** | Flax |
| **GPU 推理** | PyTorch |
| **Apple Silicon** | PyTorch (MPS) |

### 11.2 模型加载失败

```python
# 如果 from_pretrained 失败，手动下载
import urllib.request

url = "https://huggingface.co/google/timesfm-2.5-200m-pytorch/resolve/main/model.safetensors"
urllib.request.urlretrieve(url, "model.safetensors")

# 然后加载
model = timesfm.TimesFM_2p5_200M_torch.load("model.safetensors")
```

### 11.3 内存不足

```python
# 减小批量大小
model.compile(
    ForecastConfig(
        max_context=512,  # 减小上下文
        max_horizon=128,   # 减小预测长度
    )
)
```

---

## 12. 总结

TimesFM 是 Google Research 发布的**生产级时间序列预测基础模型**，具有以下优势：

**为什么选择 TimesFM：**

| 优势 | 说明 |
|------|------|
| **预训练模型** | 开箱即用，无需从头训练 |
| **小而强** | 200M 参数实现 SOTA 性能 |
| **长上下文** | 16k 上下文长度 |
| **多后端** | PyTorch/Flax/JAX |
| **企业级** | BigQuery 原生集成 |
| **开源** | Apache-2.0 许可证 |

**适用场景：**

- 销售预测
- 能源需求预测
- 气象预测
- 金融时间序列
- 异常检测

**不适用的场景：**

- 实时流式预测（需要流式处理框架）
- 分类任务（使用专门的时间序列分类模型）
- 多元因果预测（使用 CausalImpact）

---

**附录：相关资源**

- GitHub：https://github.com/google-research/timesfm
- 论文：https://arxiv.org/abs/2310.10688
- Hugging Face：https://huggingface.co/collections/google/timesfm-release-66e4be5fdb56e960c1e482a6
- Google Research Blog：https://research.google/blog/a-decoder-only-foundation-model-for-time-series-forecasting/
- BigQuery 集成：https://cloud.google.com/bigquery/docs/timesfm-model