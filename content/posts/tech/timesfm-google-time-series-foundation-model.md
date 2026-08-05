---
title: "TimesFM: Google Research开源的时序预测基础模型"
date: 2026-05-23T13:09:23+08:00
draft: false
categories:
  - 技术笔记
tags:
  - GitHub-Trending
slug: timesfm-google-time-series-foundation-model
github_repo: "google-research/timesfm"
author: 钳岳星君
description: "TimesFM 用 decoder-only 架构在 1000 亿真实时间点上预训练了一个仅 2 亿参数的模型，实现跨领域的零样本时序预测。"
---

# TimesFM：时序预测的预训练模型

TimesFM 用 decoder-only 架构在 1000 亿真实时间点上预训练了一个仅 2 亿参数的模型，实现跨领域的零样本时序预测。它把时序预测的做法从「每个场景单独训一个模型」改成「一个模型接不同数据，直接出预测」。

本文覆盖以下内容：

- TimesFM 为什么用 decoder-only 而不是 encoder-decoder，以及 patching 要解决什么计算瓶颈
- 如何跑通一个零样本预测，拿到结果
- 如何判断一个具体业务场景适不适合直接用零样本预测、什么时候该微调
- TimesFM v2.5 相比 v2.0 做了什么取舍，尤其是为什么砍掉了频率指示器

## 总览：TimesFM 的三条主线

TimesFM 内部有三条容易混淆的主线，先拆开再看细节：

| 主线 | 做什么 | 为什么关键 |
|------|--------|-----------|
| **Patching（分块）** | 把连续时间点打包成固定长度的块（patch），作为 transformer 的输入 token | 不 patching 的话，序列太长 transformer 根本推不动；patching 让模型同时学到局部形状和长程趋势 |
| **Decoder-only 因果推理** | 每个 patch token 只能看到它之前的 token，预测下一个 patch | 和 GPT 一样的自回归逻辑，天然适合"给历史推未来" |
| **频率感知与归一化** | 输入时做 per-patch 归一化，v2.0 还注入频率标记（v2.5 移除） | 不同场景的量纲差异巨大（零售销量 vs 股价 vs 温度），不归一化模型会把量纲当信号 |

一句话总结：**TimesFM = 把时间序列切成块（patch）→ 扔进一个小型 GPT → 逐块预测未来**。

## 核心架构：patched decoder-only

TimesFM 的架构选型到 2.5 版已经收敛得很明确：

```text
原始时序 → 归一化 → 分块(patch) → 残差块 + 输入投影
                                    ↓
                          stacked transformer layers
                          (因果注意力, 只往左看)
                                    ↓
                          输出头 → 预测 patch
```

与传统时序模型的关键区别：

- 传统方法（ARIMA、Prophet、DeepAR）要么逐点建模、要么依赖显式的季节性和趋势分解。TimesFM 不显式建模这些——它依赖 transformer 的注意力机制自己去学。
- 和 T5/GPT 等文本模型的区别在于 token 的含义不同：文本 token 是离散子词，TimesFM 的 token 是连续时间点的打包。这意味着输入投影和输出头需要特殊设计（不是简单查表 embedding），而是小型的残差 MLP（多层感知机）。

### Patching 为什么不是可有可无

不 patching 时，1000 个时间点就是 1000 个 token，transformer 的计算量随序列长度平方增长。patching 把 32 个连续点压缩成一个 token，序列长度当场除以 32。32 这个数字不是随便选的——太短学不到局部模式，太长则在"token 内平滑"和"token 间推理"之间失衡。

### Decoder-only 为什么比 encoder-decoder 更合适

时序预测是天然的单向任务：已知过去，推未来。decoder-only 的因果注意力恰好匹配这个约束——不让模型"偷看"未来信息。encoder-decoder 结构在翻译任务里有优势是因为源语言和目标语言的关系不是简单的时间先后，但对时序预测来说，所有输入（历史值、协变量）和输出（预测值）都沿同一个时间轴排列，decoder-only 的结构负担更小。

## 一条数据怎么流过 TimesFM

以零售 SKU（库存单位）日销量预测为例。假设某个 SKU 过去 512 天的日销量已知，要预测未来 64 天。

**第一步：归一化。** 输入序列的每个 patch 先除以自己的均值（per-patch normalization）。这一步把"日均销量 1000 件的 SKU"和"日均销量 3 件的 SKU"拉到同一量级，让模型专注形状而非绝对值。

**第二步：分块。** 512 个历史点被切成 16 个 patch，每个 patch 32 个时间点。每个 patch 先过一个小的残差块做投影，得到一个固定维度的向量。

**第三步：transformer 前向。** 16 个 patch token 依次经过多层 causal transformer。第 1 个 token 只能看自己，第 9 个 token 能看前 8 个——和 GPT 生成文本的逻辑一样。

**第四步：输出。** 最后一个 transformer 层的输出 token 走过输出头，预测下一个 patch（未来第 1～32 天）。然后这个预测 patch 被拼回序列末尾，再预测下下个 patch，直到凑满 64 天（2 个 patch）。

**第五步：还原尺度。** 预测值乘以对应 patch 的归一化因子，回到原始量纲。

整个过程不需要任何模型训练——权重是 Google 预训练好的。这也就是"零样本预测"的含义：直接把数据喂进去，拿结果。

## 版本变化：v1.0 → v2.5

TimesFM 经历了三次迭代。参数量走过一条「先增后减」的曲线：v1.0 是 200M，v2.0 升到 500M，v2.5 又压回 200M，但上下文从 2,048 一路拉到 16,384。

| 特性 | v2.0 | v2.5 |
|------|------|------|
| 参数量 | 500M | 200M |
| 上下文长度 | 2,048 时间点 | 16,384 时间点 |
| 频率指示器 | 有 | 移除 |
| 分位数预测 | 有限 | 连续分位数头（约 30M 参数） |
| 协变量输入 | 无 | XReg（2025-10 加入） |
| 微调 | 无 | LoRA（2026-04 加入） |
| 框架 | PyTorch | PyTorch + Flax/JAX 双后端 |

参数减半、上下文翻 8 倍，靠的是注意力机制和分块表示本身的效率改进。移除频率指示器是一个信号：per-patch 归一化配合足够的训练数据，模型能自己学到频率特征，不再需要用户显式声明数据是日频、周频还是月频。

分位数预测让 TimesFM 不只给一个点预测，还能输出区间（比如"第 30 天销量有 90% 概率落在 80～120 之间"），对库存和安全库存决策有直接价值。2.5 还补上了两条工程能力：2025 年 10 月加入的 XReg 协变量输入，以及 2026 年 4 月加入的 LoRA 微调（走 HuggingFace PEFT）。

## 安装与快速验证

```bash
pip install timesfm
```

零样本预测的最小可跑示例（直接加载 v2.5 的 PyTorch 权重）：

```python
import numpy as np
import timesfm

model = timesfm.TimesFM_2p5_200M_torch.from_pretrained(
    "google/timesfm-2.5-200m-pytorch"
)
model.compile(
    timesfm.ForecastConfig(
        normalize_inputs=True,
        use_continuous_quantile_head=True,
    )
)
point_forecast, quantile_forecast = model.forecast(
    horizon=12,
    inputs=[
        np.linspace(0, 1, 100),          # 一条趋势序列
        np.sin(np.linspace(0, 20, 67)),  # 一条周期序列
    ],
)
# point_forecast.shape    → (2, 12)：两条序列、各 12 步点预测
# quantile_forecast.shape → (2, 12, 10)：均值 + 10th~90th 分位数
```

`forecast()` 返回点预测和分位数两个结果。想要更长的历史或更远的预测，在 `ForecastConfig` 里调 `max_context` 和 `max_horizon`。

## 零样本预测的边界

零样本不等于万能。以下场景中零样本效果通常打折扣：

- **高噪声稀疏序列**。如果序列里大部分是 0 或缺失值，patching 机制会把噪声当作信号。此时传统统计方法（如 Croston）可能更合适。
- **强外生变量驱动**。如果预测高度依赖促销活动、节假日、政策变化等外部协变量（covariate），零样本模式下模型看不到这些信息，需要走微调或改用支持协变量的接口（TimesFM 2.5 支持 XReg 协变量输入）。
- **极短历史**。少于 32 个时间点（一个 patch 的长度）的序列，模型基本没有足够上下文做推理。

零样本更适合的场景：有足够历史长度（≥ 128 个时间点）、规律性较强、不需要复杂外部特征的时序——零售 SKU 日销量、服务器 CPU 利用率、网站日活、电网小时负荷，都在这个范围内。

## benchmark：数字在说什么

TimesFM 论文和社区评测（GIFT-Eval）主要测试指标是 MAE（平均绝对误差）和 sMAPE（对称平均绝对百分比误差）。核心结论：

- 在 Monash 时序预测基准的多个数据集上，TimesFM 的零样本结果与各数据集上专门训练的最优模型差距在 10%～20% 以内，部分数据集持平。
- 当目标序列与预训练语料分布接近时（如零售、金融、IoT），零样本效果最好；偏离较大的领域（如流行病传播）效果下降明显。

这些数字**能说明**的是：用一个模型覆盖多个领域是可行的，预训练语料中的时序模式确实可以迁移。**不能说明**的是：TimesFM 可以替代所有专业模型——在需要极高精度且允许投入训练资源的场景，微调后的专用模型仍然有优势。

## 适用场景与采用顺序

按优先级从高到低：

1. **先上的团队**：有大量不同 SKU/传感器/指标的时序需要预测，但每个序列单独建模不现实。TimesFM 的零样本能力让你先拿到可用基线，再决定哪些序列值得微调。
2. **可以试试的团队**：已经在用 Prophet 或统计方法做基线的团队。TimesFM 的 point forecast 和分位数区间可以作为第二意见，尤其是在 Prophet 对趋势转折点不敏感的场景。
3. **不急着上的团队**：只在 1～2 条核心时序上做预测，且已有成熟专用模型。此时 TimesFM 的边际收益有限；但可以关注它的微调路线——在自己的数据上 fine-tune 后替换现有模型。
4. **需要评估后再决定的团队**：预测严重依赖外部特征（促销、天气、新闻事件）。TimesFM 2.5 的 XReg 支持这类协变量，但要先跑零样本对比，看与现有带协变量模型的差距。

如果不想自己部署模型，TimesFM 2.5 也原生集成在 BigQuery ML、Vertex AI 和 Google Sheets 里，可以直接用 SQL 或表格公式调用，适合已经在 Google Cloud 生态里的团队。

## 常见问题

**我的数据是 15 分钟级的风电功率，TimesFM 能处理吗？**

可以。TimesFM 不依赖显式的频率标记（v2.5 已移除），靠 per-patch 归一化适配任意时间间隔。但默认的 32 点 patch 在 15 分钟级数据上只覆盖 8 小时，不一定能捕获日周期——建议根据业务周期（如日周期 96 个点）调整 patch 长度。

**零样本预测准不准？能直接上线吗？**

看场景和容忍度。在零售、IoT 等与预训练语料接近的领域，零样本通常能达到专用模型的 80%～95% 水平。如果是关键决策系统（库存补货量直接影响营收），建议先用零样本出基线，再在自己的历史数据上微调后上线。

**怎么选 patch size？**

默认的 32 是个通用起点。如果序列有明显周期——比如小时级数据的日周期 = 24 点——patch size 最好能被周期整除或与之对齐，让每个 patch 完整覆盖一个模式段。太短学不到局部形状，太长则 patch 内平滑过度、patch 间推理能力下降。

**微调需要多少数据？**

建议至少几千个时间点。数据太少（比如只有几百个点）时，微调提升不明显，还不如直接用零样本预测。数据量够但场景与预训练语料差异大（如流行病传播）时，微调收益最显著。

**TimesFM 能替代 Prophet 吗？**

Prophet 适合强季节性、需要可解释性的场景（比如"为什么这个月预测偏高"——Prophet 能分解出趋势、季节性、节假日分量）。TimesFM 的优势在"大量不同序列、每个序列单独建模不现实"的场景——比如你有 10,000 个 SKU 的日销量，用 Prophet 逐个建模太慢，TimesFM 零样本一次出结果。建议：先用 TimesFM 出基线，对关键序列再用 Prophet 做可解释分析。

**v2.5 的连续分位数预测怎么用？**

在 `ForecastConfig` 里打开 `use_continuous_quantile_head=True`，`model.forecast()` 就会返回分位数结果。可以取任意分位水平，比如"第 30 天销量有 90% 概率落在 80～120 之间"——这对库存和安全库存决策有直接价值。

**TimesFM 的预训练语料包含哪些领域？我的数据不在这些领域怎么办？**

预训练语料主要包含零售、金融、IoT 等领域的时间序列。如果你的数据不在这些领域（如流行病传播、传感器故障预测），零样本效果会下降明显。此时有两个选项：1) 在自己的数据上微调；2) 用传统统计方法（如 ARIMA、Croston）做基线，TimesFM 作为第二意见。

**CPU 推理够用吗？**

CPU 推理可用但较慢，生产环境建议 GPU。v2.5 移除了频率指示器，意味着模型对数据频率的自动适配依赖归一化策略，极端频率（如毫秒级 tick 数据）可能需要重采样。

---

**仓库地址：** https://github.com/google-research/timesfm
**论文：** https://arxiv.org/pdf/2310.10688.pdf

---

**相关工具：** [Telegraf](telegraf-influxdb-time-series-agent-guide)