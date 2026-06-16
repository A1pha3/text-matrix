---
title: "Kronos：金融市场的语言基础模型"
date: "2026-05-14T20:17:49+08:00"
categories:
  - "技术笔记"
tags:
  - "时间序列预测"
  - "金融AI"
  - "基础模型"
  - "K线数据"
  - "Transformer"
description: "Kronos 是首个针对金融 K 线数据的开源基础模型，基于分层分词器将 OHLCV 多维连续数据量化为离散 Token，覆盖 45 个全球交易所数据。AAAI 2026。"
slug: kronos-financial-market-foundation-model
---

# Kronos：金融市场的语言基础模型

K 线序列（OHLCV）承载着全球市场的情绪与趋势，但深度学习模型在处理这类数据时面临高噪声、不规则间隔、多维耦合等挑战。Kronos 用一个两阶段框架来应对：分层分词器把连续的多维 K 线数据量化为离散 Token，自回归 Transformer 在 45 个交易所的数据上预训练，覆盖从 4.1M 到 499M 参数的四种规格。

论文已被 AAAI 2026 接收（[arXiv:2508.02739](https://arxiv.org/abs/2508.02739)），GitHub 仓库约 24.5k Stars。

## 设计思路：从 K 线到 Token

Kronos 的主要贡献在于其**两阶段框架**：

### 第一阶段：分层分词器（Hierarchical Tokenizer）

连续的、多维的 K 线数据（OHLCV，即 Open/High/Low/Close/Volume）无法直接被语言模型处理。Kronos 的分词器首先将这些数据量化为离散的层次化 Token。

分词器有两种规格：

| 分词器 | 词表大小 | 适用模型 |
|--------|---------|---------|
| Kronos-Tokenizer-2k | 2k | Kronos-mini |
| Kronos-Tokenizer-base | — | Kronos-small / Kronos-base |

分词过程将每个时间步的 OHLCV 数据映射为语义有序的离散符号，使得模型能够学习到 K 线序列中的局部结构与全局时序依赖。

### 第二阶段：自回归 Transformer

经过分词后的 K 线序列由大型自回归 Transformer 模型处理。Kronos 是 decoder-only 架构的模型家族，与 GPT 系列在大语言模型中的角色类似——它将历史 K 线序列作为上下文，自回归地生成未来预测。

预训练数据覆盖了**超过 45 个全球交易所**的行情数据，真正实现了金融市场的"语言"建模。

## 模型家族（Model Zoo）

Kronos 提供四个参数规模的预训练模型，均可直接从 Hugging Face Hub 下载：

| 模型 | 分词器 | 上下文长度 | 参数量 | 开源 |
|------|--------|-----------|--------|------|
| Kronos-mini | Kronos-Tokenizer-2k | 2048 | 4.1M | ✅ NeoQuasar/Kronos-mini |
| Kronos-small | Kronos-Tokenizer-base | 512 | 24.7M | ✅ NeoQuasar/Kronos-small |
| Kronos-base | Kronos-Tokenizer-base | 512 | 102.3M | ✅ NeoQuasar/Kronos-base |
| Kronos-large | Kronos-Tokenizer-base | 512 | 499.2M | ❌ |

> ⚠️ 注意：Kronos-small 和 Kronos-base 的最大上下文（max_context）为 512，即模型可处理的最大序列长度。建议输入数据的回看窗口（lookback）不超过此限制，KronosPredictor 会自动对过长上下文做截断处理。

## 快速上手：如何用 Kronos 做预测

Kronos 提供了简洁易用的 `KronosPredictor` API，几行代码即可完成从原始数据到预测结果的全流程。

### 安装

```bash
pip install -r requirements.txt
```

### 完整预测流程

```python
from model import Kronos, KronosTokenizer, KronosPredictor

# 1. 加载分词器和模型
tokenizer = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
model = Kronos.from_pretrained("NeoQuasar/Kronos-small")

# 2. 初始化预测器
predictor = KronosPredictor(model, tokenizer, max_context=512)

# 3. 准备输入数据
import pandas as pd

df = pd.read_csv("./data/XSHG_5min_600977.csv")
df['timestamps'] = pd.to_datetime(df['timestamps'])

lookback = 400
pred_len = 120

x_df = df.loc[:lookback-1, ['open', 'high', 'low', 'close', 'volume', 'amount']]
x_timestamp = df.loc[:lookback-1, 'timestamps']
y_timestamp = df.loc[lookback:lookback+pred_len-1, 'timestamps']

# 4. 生成预测
pred_df = predictor.predict(
    df=x_df,
    x_timestamp=x_timestamp,
    y_timestamp=y_timestamp,
    pred_len=pred_len,
    T=1.0,       # 采样温度
    top_p=0.9,   # Nucleus 采样概率
    sample_count=1  # 采样路径数量，聚合平均
)

print(pred_df.head())
```

### 批量预测

多标的场景下，可使用 `predict_batch` 并行处理，充分利用 GPU：

```python
pred_df_list = predictor.predict_batch(
    df_list=[df1, df2, df3],
    x_timestamp_list=[x_ts1, x_ts2, x_ts3],
    y_timestamp_list=[y_ts1, y_ts2, y_ts3],
    pred_len=pred_len,
    T=1.0, top_p=0.9, sample_count=1, verbose=True
)
```

> **批量预测要求**：所有序列历史长度（lookback）和预测长度（pred_len）必须一致；每个 DataFrame 必须包含 `['open', 'high', 'low', 'close']` 列，volume 和 amount 可选（缺失时填充 0）。

## 微调：针对自有数据定制 Kronos

Kronos 提供了完整的微调流程，以 A 股市场为例，使用 Qlib 进行数据准备和回测。

### Step 1：配置实验参数

在 `finetune/config.py` 中设置以下路径：

```python
qlib_data_path        # Qlib 数据本地目录
dataset_path          # 处理后的 train/val/test pickle 文件保存目录
save_path             # 模型 checkpoint 保存目录
backtest_result_path  # 回测结果保存目录
pretrained_tokenizer_path  # 预训练分词器路径（本地或 HF 模型名）
pretrained_predictor_path  # 预训练预测器路径
```

### Step 2：数据预处理

```bash
python finetune/qlib_data_preprocess.py
```

执行后生成 `train_data.pkl`、`val_data.pkl`、`test_data.pkl`。

### Step 3：微调分词器

```bash
torchrun --standalone --nproc_per_node=NUM_GPUS finetune/train_tokenizer.py
```

此步骤将分词器适配到目标市场的数据分布。

### Step 4：微调预测器

```bash
torchrun --standalone --nproc_per_node=NUM_GPUS finetune/train_predictor.py
```

### Step 5：回测评估

```bash
python finetune/qlib_test.py --device cuda:0
```

输出策略表现并绘制累计收益曲线。

> ⚠️ **重要提示**：示例中的回测仅为演示微调流程，属于简化示例而非成熟量化策略。真实生产环境需要更复杂的技术，如组合优化、风险因子中性化等。预测信号（raw predictions）本身并非纯 Alpha，通常需要接入投资组合优化模型进行二次处理。

## 设计要点

### 1. 金融数据的"语言"建模

Kronos 的出发点是：K 线数据本质上是一种序列语言——每个 K 线的 OHLCV 值相当于一个"词"，连续若干根 K 线构成一个"句子"，整个市场历史是一部"长篇文本"。将 Transformer 架构应用于这一"语言"，可以实现跨市场、跨资产的通用时序建模。

### 2. 分层量化的必要性

金融数据的连续性（continuous）是一大挑战：OHLCV 都是浮点数，直接映射到语言模型的离散 token 空间会损失大量信息。Kronos 的分层分词器通过将连续值分层量化（hierarchical quantization），在保留价格结构信息的同时实现了有效的离散表示。

### 3. 高噪声环境的适配

与标准时间序列不同，K 线数据充满噪声和异常波动。Kronos 在预训练阶段通过大量真实市场数据的暴露，使其能够学习到噪声模式与真实趋势之间的区别，从而在预测时具备更强的鲁棒性。

## 限制与注意事项

- **Kronos-large 尚未开源**：目前仅 mini/small/base 三个规模开源，large 模型闭源。
- **上下文长度有限**：small/base 模型最大 512，mini 模型为 2048。对于超高频数据或需要更长历史的场景，可能需要权衡。
- **预测为概率性**：通过 `T` 和 `top_p` 参数控制采样过程，单次预测具有随机性，多次采样平均可获得更稳定的结果。
- **raw signal ≠ Alpha**：模型输出的是价格变化的预测信号，实际策略需要组合优化和风险管理模块。

## 小结

Kronos 是**首个专门针对 K 线数据开源的基础模型**。通过将金融市场的价格语言建模为离散 Token，并通过大规模 Transformer 学习其内在结构，Kronos 为量化研究者提供了一个通用、可微调的基础工具。

无论是做短期价格预测、波动率建模，还是将其作为因子生成的骨干网络，Kronos 都值得深入研究。

**相关链接：**

- 论文：https://arxiv.org/abs/2508.02739
- GitHub：https://github.com/shiyu-coder/Kronos
- Hugging Face：https://huggingface.co/NeoQuasar/Kronos-small

---

*如在研究中使用 Kronos，请引用：*
```bibtex
@misc{shi2025kronos,
  title={Kronos: A Foundation Model for the Language of Financial Markets}, 
  author={Yu Shi and Zongliang Fu and Shuo Chen and Bohan Zhao and Wei Xu and Changshui Zhang and Jian Li},
  year={2025},
  eprint={2508.02739},
  archivePrefix={arXiv},
  primaryClass={q-fin.ST},
  url={https://arxiv.org/abs/2508.02739}, 
}
```