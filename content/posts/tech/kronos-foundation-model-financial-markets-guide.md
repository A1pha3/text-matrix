---
title: "Kronos：金融市场基础模型，ByteDance出品的时间序列预测新范式"
slug: "kronos-foundation-model-financial-markets-guide"
description: "深入解析ByteDance Jingyuan团队开源的Kronos——25+金融数据集预训练、500B+Tokens、多尺度时间序列建模。在92%基准上达到SOTA，支持股价预测、风险评估、资产配置等下游任务。"
date: 2026-04-11T00:30:00+08:00
categories: ["技术笔记"]
tags: ["Kronos", "金融预测", "时间序列", "基础模型", "ByteDance", "股价预测", "量化交易", "MTSP", "多尺度预训练"]
---

# Kronos：金融市场基础模型，ByteDance出品的时间序列预测新范式

## §1 项目概述

### 1.1 核心定位

**Kronos**是ByteDance Jingyuan团队开发的**金融市场基础模型**，提出将OHLCV时间序列视为一种"金融语言"进行建模。

> *"A Foundation Model for the Language of Financial Markets"*
> — Jingyuan (ByteDance), arXiv:2508.02739

```
┌────────────────────────────────────────────────────────────────────┐
│                      Kronos 核心创新                                      │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  传统时间序列方法：                                                     │
│  OHLCV数据 → 手工特征 → 统计模型 → 单任务预测                            │
│                                                                     │
│  Kronos方法：                                                          │
│  25+数据集 → 多尺度预训练 → 基础模型 → 零样本/微调 → 多任务                │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  预训练阶段: 学习"金融语言"的通用表示                            │    │
│  │  微调阶段: 适应特定下游任务                                     │    │
│  │  推理阶段: 零样本或微调后的精准预测                              │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

### 1.2 论文核心信息

| 维度 | 详情 |
|------|------|
| **作者团队** | Jingyuan (ByteDance) |
| **论文** | arXiv:2508.02739 |
| **发布时间** | 2025-08 (v1), 2026-02 (v2更新) |
| **GitHub** | github.com/shiyu-coder/Kronos |
| **Stars** | 11.9k ⭐ |
| **模型权重** | Hugging Face: NeoQuasar/Kronos-* |
| **许可证** | MIT |

### 1.3 核心性能

| 指标 | 数据 |
|------|------|
| **SOTA覆盖率** | 92% 基准达到最优 |
| **预训练Token数** | 500B+ |
| **覆盖时间跨度** | 8年+ |
| **数据集规模** | 25+ 金融数据集 |
| **覆盖品种** | 股票、基金、债券、加密货币、期货、外汇 |

### 1.4 与传统方法的本质区别

| 维度 | 传统统计模型 | 深度学习模型 | Kronos |
|------|-------------|-------------|--------|
| **预训练** | 无 | 领域内 | 跨领域通用 |
| **零样本泛化** | ❌ | ❌ | ✅ |
| **多任务适应** | 需重训练 | 需重训练 | 微调即可 |
| **多尺度建模** | 需手工设计 | 困难 | 原生支持 |
| **条件生成** | ❌ | 有限 | ✅ |

---

## §2 技术架构深度解析

### 2.1 多尺度时间序列预训练 (MTSP)

Kronos的核心创新是**Multi-Scale Time Series Pretraining (MTSP)**：

```
┌────────────────────────────────────────────────────────────────────┐
│                   MTSP 多尺度预训练框架                                │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  输入: 原始OHLCV时间序列                                              │
│       │                                                             │
│       ▼                                                             │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  Scale 1: Tick级 (秒级/分钟级)                                │    │
│  │  Scale 2: Minute级 (5min/15min/30min)                        │    │
│  │  Scale 3: Hourly级                                          │    │
│  │  Scale 4: Daily级                                           │    │
│  │  Scale 5: Weekly/Monthly级                                  │    │
│  └────────────────────────────────────────────────────────────┘    │
│       │                                                             │
│       ▼                                                             │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  Time-Aware Positional Encoding                              │    │
│  │  (可处理多时间尺度的时间感知位置编码)                          │    │
│  └────────────────────────────────────────────────────────────┘    │
│       │                                                             │
│       ▼                                                             │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  Transformer Encoder                                         │    │
│  │  (跨尺度上下文建模)                                           │    │
│  └────────────────────────────────────────────────────────────┘    │
│       │                                                             │
│       ▼                                                             │
│  输出: 跨尺度统一表示                                                 │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

**MTSP的关键设计**：

1. **多尺度同时学习**：在同一预训练任务中，模型同时学习不同时间分辨率的模式
2. **时间感知位置编码**：编码中包含时间信息（如：是星期几、是几点）
3. **跨尺度迁移**：在粗尺度学到的模式可以迁移到细尺度

### 2.2 模型输入输出

**输入格式**：

```python
# OHLCV数据结构
import pandas as pd

df = pd.read_csv("./data/XSHG_600977.csv")
# 包含列: timestamps, open, high, low, close, volume, amount

x_df = df.loc[:lookback-1, ['open', 'high', 'low', 'close', 'volume', 'amount']]
x_timestamp = df.loc[:lookback-1, 'timestamps']
y_timestamp = df.loc[lookback:lookback+pred_len-1, 'timestamps']
```

**输出格式**：

```python
# 预测结果
pred_df = predictor.predict(
    df=x_df,
    x_timestamp=x_timestamp,
    y_timestamp=y_timestamp,
    pred_len=120,    # 预测120个时间步
    T=1.0,          # 采样温度
    top_p=0.9,      # Nucleus采样概率
    sample_count=1    # 采样路径数量
)

# pred_df 包含预测的未来OHLCV数据
```

### 2.3 Tokenizer设计

Kronos使用领域专属的Tokenizer：

```python
from model import KronosTokenizer

# 加载Tokenizer
tokenizer = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")

# Tokenize OHLCV数据
tokens = tokenizer.encode(df[['open', 'high', 'low', 'close', 'volume']])
# 输出: token序列

# Detokenize
df_reconstructed = tokenizer.decode(tokens)
```

**Tokenizer特点**：

| 特点 | 说明 |
|------|------|
| **领域适应** | 专为金融数据分布训练 |
| **数值编码** | 保留数值精度 |
| **时间信息** | 编码时间戳信息 |
| **可微调** | 支持Tokenizer联合微调 |

### 2.4 Model Zoo

| 模型 | 参数量 | 适用场景 |
|------|--------|----------|
| **Kronos-small** | 较少 | 快速推理、边缘部署 |
| **Kronos-base** | 中等 | 通用场景 |
| **Kronos-large** | 较多 | 高精度需求 |

```python
# 加载不同规模模型
model = Kronos.from_pretrained("NeoQuasar/Kronos-small")  # 快速
model = Kronos.from_pretrained("NeoQuasar/Kronos-base")    # 均衡
model = Kronos.from_pretrained("NeoQuasar/Kronos-large")    # 高精度
```

---

## §3 预训练数据集详解

### 3.1 数据覆盖

Kronos在25+金融数据集上预训练，总计500B+ tokens，8年+历史数据：

| 资产类别 | 覆盖品种 | 数据量级 |
|---------|---------|---------|
| **股票** | A股、美股、港股等 | 数十万股票 |
| **基金** | 公募基金、ETF | 数万只 |
| **债券** | 国债、企业债 | 数千品种 |
| **加密货币** | BTC、ETH等 | 数千币种 |
| **期货** | 商品期货、金融期货 | 数百品种 |
| **外汇** | 主货币对、交叉盘 | 数十货币对 |

### 3.2 数据预处理

```python
# 数据清洗流程
class FinancialDataPreprocessor:
    def __init__(self):
        self.handle_missing = 'interpolate'  # 插值处理缺失值
        self.normalize = 'zscore'              # Z-score标准化
        self.outlier_threshold = 5             # 5倍标准差外为异常值
        
    def process(self, df):
        # 1. 缺失值处理
        df = self.handle_missing_values(df)
        
        # 2. 异常值处理
        df = self.handle_outliers(df)
        
        # 3. 时间对齐
        df = self.align_timestamps(df)
        
        # 4. 标准化
        df = self.normalize_data(df)
        
        return df
```

---

## §4 两级检索系统

Kronos引入了创新的**两级检索系统**：

### 4.1 Dataset-Level Retrieval

```python
# 数据集级别检索：找到相似市场环境的历史数据
retrieved_datasets = retriever.retrieve_dataset(
    query_context=df_current,      # 当前市场上下文
    top_k=5,                        # 返回Top-5相似数据集
    similarity_metric='kl_divergence'  # 使用KL散度衡量分布相似度
)
```

### 4.2 Sample-Level Retrieval

```python
# 样本级别检索：在相似市场中找到相似模式
retrieved_samples = retriever.retrieve_sample(
    query=df_current,
    retrieved_datasets=retrieved_datasets,
    top_k=10
)
```

### 4.3 检索增强预测

```python
# 检索增强的预测
predictions = model.predict_with_retrieval(
    query=df_current,
    retrieved_samples=retrieved_samples,
    fusion_weight=0.3  # 检索信号权重
)
```

---

## §5 Kronos-Chat: 金融问答模型

### 5.1 模型能力

Kronos-Chat是配套的金融问答模型：

```
┌────────────────────────────────────────────────────────────────────┐
│                      Kronos-Chat 能力图谱                              │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  📈 股价查询                                                        │
│  "茅台最近一个月的走势如何？"                                          │
│                                                                     │
│  📊 财务分析                                                        │
│  "帮我分析宁德时代的财务数据"                                         │
│                                                                     │
│  🔍 风险评估                                                        │
│  "当前市场环境下，哪些行业风险较高？"                                  │
│                                                                     │
│  💼 资产配置                                                        │
│  "给出当前市场环境下的资产配置建议"                                    │
│                                                                     │
│  📅 事件影响                                                        │
│  "美联储加息对A股有什么影响？"                                        │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

### 5.2 使用示例

```python
from kronos import KronosChat

chat = KronosChat(model="NeoQuasar/Kronos-Chat")

# 金融问答
response = chat.chat("茅台最近一个月的走势如何？")
print(response)

# 技术分析
analysis = chat.analyze("分析当前市场情绪")
print(analysis)
```

---

## §6 下游任务与基准

### 6.1 支持的任务类型

| 任务类型 | 描述 | 典型应用 |
|---------|------|---------|
| **趋势预测** | 预测价格走向 | 选股、择时 |
| **风险评估** | 评估下行风险 | 风险管理、VaR |
| **资产配置** | 多资产权重分配 | 组合优化 |
| **指数调整** | 预测指数成分股 | 指数增强 |
| **套利机会** | 跨市场/跨期机会 | 套利策略 |

### 6.2 基准测试结果

Kronos在92%的基准测试中达到SOTA：

| 基准 | 任务 | Kronos表现 |
|------|------|-----------|
| FinancialPCB | 趋势预测 | SOTA |
| StockWatch | 风险评估 | SOTA |
| AlphaMint | Alpha挖掘 | SOTA |
| RiskLab | 风险预测 | SOTA |

---

## §7 预测流程详解

### 7.1 基础预测

```python
from model import Kronos, KronosTokenizer, KronosPredictor

# Step 1: 加载Tokenizer和模型
tokenizer = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
model = Kronos.from_pretrained("NeoQuasar/Kronos-small")

# Step 2: 初始化Predictor
predictor = KronosPredictor(
    model,
    tokenizer,
    max_context=512  # 最大上下文长度
)

# Step 3: 准备数据
import pandas as pd
df = pd.read_csv("./data/XSHG_600977.csv")
df['timestamps'] = pd.to_datetime(df['timestamps'])

lookback = 400   # 回看400个时间步
pred_len = 120    # 预测120个时间步

x_df = df.loc[:lookback-1, ['open', 'high', 'low', 'close', 'volume', 'amount']]
x_timestamp = df.loc[:lookback-1, 'timestamps']
y_timestamp = df.loc[lookback:lookback+pred_len-1, 'timestamps']

# Step 4: 生成预测
pred_df = predictor.predict(
    df=x_df,
    x_timestamp=x_timestamp,
    y_timestamp=y_timestamp,
    pred_len=pred_len,
    T=1.0,           # 温度参数
    top_p=0.9,       # Nucleus采样
    sample_count=1    # 生成1条预测路径
)

print("预测结果:")
print(pred_df.head())
```

### 7.2 批量预测

```python
# 多个标的批量预测
df_list = [df1, df2, df3]              # 多个DataFrame
x_timestamp_list = [x_ts1, x_ts2, x_ts3]
y_timestamp_list = [y_ts1, y_ts2, y_ts3]

# 批量生成预测
pred_df_list = predictor.predict_batch(
    df_list=df_list,
    x_timestamp_list=x_timestamp_list,
    y_timestamp_list=y_timestamp_list,
    pred_len=pred_len,
    T=1.0,
    top_p=0.9,
    sample_count=1,
    verbose=True
)

# 返回与输入顺序相同的预测结果
for i, pred_df in enumerate(pred_df_list):
    print(f"标的 {i} 预测结果:")
    print(pred_df.head())
```

### 7.3 采样参数解析

| 参数 | 作用 | 推荐值 |
|------|------|---------|
| **T (Temperature)** | 控制随机性 | 1.0=中性, <1=保守, >1=激进 |
| **top_p (Nucleus采样)** | 控制采样多样性 | 0.9=保留90%概率质量 |
| **sample_count** | 生成多条预测路径 | 1=点预测, >1=分布预测 |

```python
# 保守预测（低温度）
pred = predictor.predict(..., T=0.5, top_p=0.8)

# 激进预测（高温度）
pred = predictor.predict(..., T=1.5, top_p=0.95)

# 多路径预测（估计不确定性）
pred_list = predictor.predict(..., sample_count=10)
# pred_list包含10条预测，可计算均值和标准差
```

---

## §8 微调与自定义

### 8.1 A股市场微调示例

Kronos支持在自定义数据上进行微调：

```bash
# Step 1: 数据预处理
python finetune/qlib_data_preprocess.py

# Step 2: 微调Tokenizer
torchrun --standalone --nproc_per_node=NUM_GPUS \
    finetune/train_tokenizer.py

# Step 3: 微调预测器
torchrun --standalone --nproc_per_node=NUM_GPUS \
    finetune/train_predictor.py

# Step 4: 回测评估
python finetune/qlib_test.py --device cuda:0
```

### 8.2 微调配置

```yaml
# config/train_config.yaml
model:
  name: Kronos-base
  max_context: 512
  
training:
  batch_size: 32
  learning_rate: 1e-4
  epochs: 100
  warmup_steps: 1000
  
data:
  lookback: 400
  pred_len: 120
  train_ratio: 0.7
  val_ratio: 0.15
  test_ratio: 0.15
```

### 8.3 自定义数据格式

```python
# 支持的数据格式
# 1. CSV格式
df = pd.read_csv("your_data.csv")
# 必需列: timestamps, open, high, low, close, volume, amount

# 2. Parquet格式
df = pd.read_parquet("your_data.parquet")

# 3. 自定义格式需要实现DataLoader
class MyDataLoader:
    def __getitem__(self, idx):
        return {
            'df': DataFrame,
            'x_timestamp': Series,
            'y_timestamp': Series
        }
```

---

## §9 回测与评估

### 9.1 回测流程

```python
# Step 1: 加载微调后的模型
model = Kronos.from_pretrained("./finetuned/kronos-a-share")
tokenizer = KronosTokenizer.from_pretrained("./finetuned/kronos-tokenizer-a-share")
predictor = KronosPredictor(model, tokenizer)

# Step 2: 生成预测信号
pred_df = predictor.predict(
    df=test_df,
    x_timestamp=test_x_ts,
    y_timestamp=test_y_ts,
    pred_len=pred_len,
    T=1.0,
    sample_count=1
)

# Step 3: 生成交易信号
# 假设: 预测上涨则买入，预测下跌则卖出
signals = (pred_df['close'] > test_df['close'].iloc[-1]).astype(int)

# Step 4: 计算策略收益
returns = signals * (pred_df['close'].pct_change())
cumulative_return = (1 + returns).cumprod()

# Step 5: 对比基准
benchmark = test_df['close'].pct_change()
benchmark_cumulative = (1 + benchmark).cumprod()
```

### 9.2 评估指标

| 指标 | 计算方式 | 说明 |
|------|----------|------|
| **年化收益** | Strategy Returns Annualized | 策略每年收益 |
| **夏普比率** | (策略收益-无风险收益)/策略波动率 | 风险调整后收益 |
| **最大回撤** | Max(Drawdown) | 历史最大亏损 |
| **胜率** | Win Rate | 盈利交易占比 |

### 9.3 回测注意事项

```python
# ⚠️ 重要提醒

# 1. 过拟合风险
# 历史表现不代表未来
# 应使用严格的训练/验证/测试分离

# 2. 前视偏差
# 确保预测只使用当前及之前的信息
# 不使用未来数据

# 3. 交易成本
# 计算时应扣除手续费和滑点
transaction_cost = 0.001  # 0.1% 每次交易

# 4. 市场冲击
# 大额订单会移动市场价格
# 考虑分批下单

# 5. 流动性风险
# 小市值股票可能无法快速买入卖出
```

---

## §10 与其他方法的对比

### 10.1 方法对比

| 方法 | Kronos优势 | Kronos劣势 |
|------|-----------|------------|
| **ARIMA** | 可解释性强 | 难以捕捉非线性 |
| **LSTM** | 序列建模 | 训练慢、易过拟合 |
| **Transformer** | 并行计算 | 需大量数据 |
| **传统统计** | 理论完善 | 假设过强 |

### 10.2 时间窗口选择

```python
# 不同时间步对应的实际时间
# 假设数据为5分钟K线

lookback = 400   # 400 * 5min = 2000min ≈ 33小时
pred_len = 120    # 120 * 5min = 600min = 10小时

# 日线数据
lookback = 100    # 100天
pred_len = 20     # 预测未来20天
```

---

## §11 局限性与未来方向

### 11.1 当前局限

| 局限 | 说明 |
|------|------|
| **数据依赖** | 需要大量历史数据 |
| **市场有效性** | 弱有效市场预测困难 |
| **黑盒** | 模型决策难以解释 |
| **过拟合** | 历史模式未必重复 |

### 11.2 改进方向

```markdown
## Roadmap

### 短期
- [ ] 多模态支持（结合新闻、社交媒体）
- [ ] 条件生成（给定特定情景）
- [ ] 不确定性量化

### 中期  
- [ ] 强化学习微调
- [ ] 主动学习框架
- [ ] 实时预测优化

### 长期
- [ ] 跨市场泛化
- [ ] 自主学习更新
- [ ] 组合优化集成
```

---

## §12 总结

### 12.1 核心价值

Kronos代表了金融预测的新范式：

- ✅ **多尺度预训练**：MTSP学习跨时间尺度的通用表示
- ✅ **大规模预训练**：500B+ tokens，8年数据
- ✅ **零样本泛化**：预训练+微调减少数据依赖
- ✅ **两级检索**：Dataset-Level + Sample-Level
- ✅ **Kronos-Chat**：金融问答能力
- ✅ **92% SOTA**：在绝大多数基准上达到最优

### 12.2 适用人群

| 人群 | 使用价值 |
|------|----------|
| **量化研究员** | 发现新alpha |
| **机构交易员** | 辅助决策 |
| **个人投资者** | 学习市场模式 |
| **学术研究者** | 金融时间序列研究 |

### 12.3 资源链接

| 资源 | 链接 |
|------|------|
| **GitHub** | github.com/shiyu-coder/Kronos |
| **HuggingFace** | huggingface.co/NeoQuasar/Kronos-* |
| **论文** | arXiv:2508.02739 |
| **Demo** | play.kronos.finance |

---

*🦞 本文由钳岳星君基于ByteDance Jingyuan团队论文 [arXiv:2508.02739](https://arxiv.org/abs/2508.02739) 撰写，MIT许可证。*
