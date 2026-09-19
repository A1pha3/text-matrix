---
title: "Qlib：微软 AI 量化投资平台深度指南"
date: "2026-04-08T15:00:00+08:00"
slug: qlib-ai-quantitative-investment-platform-guide
github_repo: "microsoft/qlib"
source_key: "gh:microsoft/qlib"
aliases:
  - /posts/tech/qlib-ai-quantitative-investment-platform-guide/
description: "Qlib 是微软研究院开源的 AI 量化投资平台，本文梳理其三层架构（数据层、模型层、策略层）、表达式引擎、因子库、qrun 自动化工作流与实验管理，并给出可运行的安装与上手示例。"
draft: false
categories: ["技术笔记"]
tags: ["量化投资", "机器学习", "Python"]
---

> **目标读者**：想用 Qlib 搭建量化研究流水线的开发者与量化研究者（需要 Python 基础，不要求量化背景）
> **关键问题**：Qlib 的三层架构如何组织；表达式引擎怎么用；qrun 如何跑通完整工作流
> **难度**：⭐⭐⭐⭐
> **预计阅读时间**：50 分钟

---

## 学习目标

读完本文后，你应该能够：

1. 说清 Qlib 的定位（研究基础设施，不是交易系统）与 DataLayer、ModelLayer、StrategyLayer 三层架构的分工
2. 用表达式引擎写因子，理解 `$close`、`Mean($close, 5)` 这类声明式语法，以及它与手写 pandas 滚动计算的区别
3. 按「数据准备 → qrun」的步骤跑通一条完整的量化研究工作流，并读懂回测报告里的指标
4. 基于 `Model` / `ModelFT` 基类接入自定义模型，用 Recorder 记录实验
5. 判断 Qlib 适合哪些场景，避开实盘执行与数据源上的常见误解

---

## §0 三分钟速览

先回答四个问题，判断这篇文档是否值得读下去：

1. **Qlib 是什么**：微软研究院（Microsoft Research）开源的 AI 量化投资平台，定位是研究基础设施，不是开箱即用的实盘策略系统。
2. **它解决什么问题**：把数据组织、特征工程、模型训练、策略生成、回测评估组织成一条可复用流水线，并提供一个表达式引擎，让上百个因子可以用声明式语法一次批量计算。
3. **怎么用**：官方提供 `qrun` 工具，读一个 YAML 配置文件就能自动完成建数据集、训练、回测和评估；想深入控制每一步时，也可以全部用 Python API 拼装。
4. **当前状态**：PyPI 包名 `pyqlib`，最新版本 0.9.7（2025 年 8 月发布）；GitHub 约 48.6k stars，MIT 协议。官方数据下载工具覆盖中国、美国、印度三个市场，仓库里还有巴西指数、加密货币、基金等采集脚本；Tushare、AkShare、BaoStock 等属于社区适配。注意：官方托管的 A 股数据集因数据安全政策暂停分发，起步数据建议用社区维护的数据源（见 §9.3）。

按阅读目标跳读：

| 你的目标 | 建议优先阅读 |
| ---- | ---- |
| 判断项目边界 | §0、§2、§3、§11 |
| 想快速上手体验 | §9、§7.2 |
| 想从架构和源码切入 | §2、§4、§5、§6 |
| 想评估是否适合二次开发 | §4、§5.4、§6.3、§8 |

---

## §1 本文覆盖范围

- Qlib 作为 AI 量化研究基础设施的定位与适用边界
- DataLayer、ModelLayer、StrategyLayer 三层分离的设计思想
- 表达式引擎、Alpha158/Alpha360 因子库、Dataset 与 DataHandler 的作用
- 内置模型体系与自定义模型接入方式
- `qrun` 自动化工作流、回测指标与 Recorder 实验管理
- 安装配置、常见问题排查，以及这个项目是否适合你的需求

---

## §2 项目概述

### 2.1 什么是 Qlib

Qlib 是微软开源的 AI 量化投资平台，目标是降低把 AI 技术引入量化投资研究的门槛。官方将其覆盖范围描述为量化投资的完整研究链路——alpha 挖掘、风险建模、组合优化、订单执行；其中"订单执行"指的是回测中的执行模拟（含嵌套决策框架与高频示例），平台本身不提供对接券商的实盘交易通道。主要组成部分：

- 数据获取与组织（`DataLayer`）
- 特征工程与因子计算（表达式引擎 + 因子库）
- 模型训练与预测（`ModelLayer`）
- 策略生成与回测（`StrategyLayer`）
- 实验记录与结果分析（Recorder、MLflow）

### 2.2 关键数据

| 指标 | 数值 |
|------|------|
| **GitHub Stars** | 约 48.6k（2026-09） |
| **最新 PyPI 版本** | pyqlib 0.9.7（2025-08-15） |
| **首次开源** | 2020 年 8 月 |
| **协议** | MIT |
| **主要语言** | Python |

论文：*Qlib: An AI-oriented Quantitative Investment Platform*（[arXiv:2009.11189](https://arxiv.org/abs/2009.11189)）。

此外，微软基于 Qlib 推出了 [RD-Agent](https://github.com/microsoft/RD-Agent)，用 LLM 智能体自动完成因子挖掘与模型优化的循环，2024 年 8 月起可用，可与 Qlib 工作流直接衔接。

### 2.3 设计思路

Qlib 的核心设计是**三层分离**：

| 层级 | 职责 | 可替换性 |
|------|------|---------|
| **DataLayer** | 数据的获取、存储、组织、因子计算 | 可独立使用 |
| **ModelLayer** | 模型训练、预测、更新 | 插拔式设计 |
| **StrategyLayer** | 策略生成、组合管理、回测 | 可自定义 |

每一层只依赖下层的稳定接口。这样你可以在不换数据层的前提下切换模型，也可以在不改模型的前提下换策略。

### 2.4 适合谁读

| 读者类型 | 是否适合 | 原因 |
| ---- | ---- | ---- |
| 量化研究者 | 适合 | 有完整的流水线框架支撑因子与模型实验 |
| AI 开发者 | 适合 | 模型接入方式统一，表达式引擎降低特征工程成本 |
| 金融从业者 | 部分适合 | 需要一定的 Python 与统计基础 |
| 寻找实盘系统的人 | 不适合 | Qlib 只覆盖研究链路，不含对接券商的实盘通道 |

---

## §3 哪些是事实，哪些需要谨慎

### 3.1 当前可确认的已实现能力

| 能力 | 状态 | 说明 |
|------|---------|------|
| 三层分离架构 | ✅ 已实现 | DataLayer / ModelLayer / StrategyLayer |
| 列式数据存储 | ✅ 已实现 | 自研 `.bin` 格式，支持快速切片 |
| 表达式引擎 | ✅ 已实现 | `$close`、`Mean($close, 5)` 等声明式因子 |
| 因子库 | ✅ 已实现 | Alpha158（158 因子）、Alpha360（360 因子） |
| 模型库 | ✅ 已实现 | LightGBM、XGBoost、MLP、LSTM、Transformer、GATs 等 20+ 模型 |
| 自动化工作流 | ✅ 已实现 | `qrun` + YAML 配置一键跑通 |
| 回测与报告 | ✅ 已实现 | 内置回测框架与图形化分析 |
| 实验管理 | ✅ 已实现 | Recorder，支持 MLflow 后端 |
| 在线推理 | 部分实现 | 提供预测服务示例，生产化需自行完善 |

### 3.2 需要特别注意的事项

| 注意事项 | 说明 |
|---------|------|
| **实盘交易** | Qlib 的执行模块用于回测中的执行模拟，不提供对接券商的实盘通道；实盘需要自己接券商或交易网关 |
| **数据源限制** | 官方 `get_data` 支持 A 股、美股、印度市场；官方托管的 A 股数据集目前因数据安全政策暂停分发，社区数据源（chenditc/investment_data）与 Yahoo 采集脚本可替代 |
| **License 差异** | 主体是 MIT，但 `examples/benchmarks` 中部分模型代码沿用了各自上游项目的协议，商用前需逐一确认 |
| **实时性能** | 以离线研究为主，实时场景需要额外开发 |

### 3.3 为什么要区分这些

Qlib 主要解决研究环节的效率与可复现问题；交易执行只在回测里模拟，真正下单要另建通道。数据质量、特征有效性和模型效果取决于你自己的数据集与实验设计，Qlib 提供的是让这些工作可复现、可比较的基础设施。

---

## §4 架构分析

### 4.1 整体架构

```text
┌────────────────────────────────────────────────────────────────┐
│                        用户入口                                 │
│  命令行（qrun / qlib workflow）   Python API    Jupyter Notebook │
└──────────────────────────────┬─────────────────────────────────┘
                               ▼
┌────────────────────────────────────────────────────────────────┐
│                    工作流与实验管理层                              │
│        qrun 配置驱动   Recorder 记录   MLflow 实验追踪            │
└──────────────────────────────┬─────────────────────────────────┘
                               ▼
┌────────────────────────────────────────────────────────────────┐
│                     StrategyLayer（策略层）                       │
│     TopkDropoutStrategy   WeightStrategyBase   自研策略          │
│                      回测引擎 / 组合管理                          │
└──────────────────────────────┬─────────────────────────────────┘
                               ▼
┌────────────────────────────────────────────────────────────────┐
│                     ModelLayer（模型层）                          │
│     LightGBM  XGBoost  MLP  LSTM  Transformer  GATs  Localformer │
│                 Model / ModelFT 基类  Trainer 训练器             │
└──────────────────────────────┬─────────────────────────────────┘
                               ▼
┌────────────────────────────────────────────────────────────────┐
│                     DataLayer（数据层）                           │
│   Provider（数据源）  .bin 存储  Dataset / DataHandler            │
│   表达式引擎（Alpha158 / Alpha360 因子）  日历 / 股票池            │
└────────────────────────────────────────────────────────────────┘
```

### 4.2 数据流

以 `qrun` 跑官方 LightGBM + Alpha158 示例（§7.2）为例，数据是这样流动的：

1. `get_data` 把原始行情下载并转成 Qlib 的 `.bin` 列式格式
2. DataHandler 从 `.bin` 里取数，套用表达式引擎算出因子，再交给 Dataset 切片
3. Dataset 把特征和标签喂给模型；模型训练与预测由 Trainer 控制
4. 预测信号进入策略层，生成持仓组合
5. 回测引擎按成本模型模拟执行，产出收益、回撤等指标
6. Recorder 把整个过程记录为可回溯的实验

---

## §5 数据层详解

### 5.1 数据组织结构

Qlib 用自研的 `.bin` 列式格式存储行情，数据紧凑、拼装成数组做科学计算的代价小。官方用同一个特征构建任务对比过几种存储方案：从 800 只股票 2007–2020 年的日线数据构建 14 个特征的数据集，Qlib 开启表达式与数据集两级缓存后 1 核 7.4 秒完成，MySQL 需要 365.3 秒——通用数据库的时间大多耗在多层接口转换上。下载完成后目录结构如下：

```text
~/.qlib/qlib_data/cn_data/
├── calendars/       # 交易日历
├── instruments/     # 股票池定义（all.txt、csi300.txt、csi500.txt）
├── features/        # 每只股票一个目录（如 sh600519/），内含 .bin 列文件
└── dataset_cache/   # 处理后的缓存（另有 features_cache/）
```

两个细节值得注意：

- 行情价格是**复权价**，Qlib 把每只股票上市首日价格归一为 1；要还原原始价格，用 `$close / $factor`。
- 股票代码格式是交易所前缀加代码，如 `SH600519`、`SZ000001`；`features/` 下对应的目录名是小写的 `sh600519/`。它不是 Wind、聚宽等数据源常见的 `600519.SH` 后缀式，也不是 `.XSHG` 风格，写错格式查数会返回空。

### 5.2 数据获取

官方下载命令如下（注意：官方托管的 A 股数据集目前暂停分发，命令待官方恢复后可用；当前起步数据用 §9.3 的社区数据源）。

下载 A 股日线数据：

```bash
python scripts/get_data.py qlib_data --target_dir ~/.qlib/qlib_data/cn_data --region cn
```

下载美股日线数据：

```bash
python scripts/get_data.py qlib_data --target_dir ~/.qlib/qlib_data/us_data --region us
```

需要分钟级数据时加 `--interval 1min`。仓库 `scripts/data_collector/` 下还提供 Yahoo、A 股指数成分等增量抓取脚本，用于更新最新行情。官方数据由 Yahoo Finance 抓取，质量有限；官方文档明确建议手上有高质量数据集的用户自行转换数据（支持 CSV 导入）。

### 5.3 表达式引擎与数据访问

初始化并读取数据：

```python
import qlib
from qlib.constant import REG_CN
from qlib.data import D

qlib.init(provider_uri="~/.qlib/qlib_data/cn_data", region=REG_CN)

instruments = ["SH600519"]
fields = ["$close", "Mean($close, 5)", "Std($close, 20)"]
df = D.features(instruments, fields, start_time="2024-01-01", end_time="2024-12-31")
```

`D.features` 返回带 MultiIndex（instrument、datetime）的 DataFrame，列名就是表达式本身。表达式引擎支持的算子可以在 `qlib/data/ops.py` 里查到，常用几个：

| 表达式 | 含义 |
| ------ | ---- |
| `$close` | 原生字段：收盘价 |
| `Mean($close, 5)` | 5 日均线 |
| `Std($close, 20)` | 20 日标准差 |
| `Ref($close, 1)` | 1 个交易日前的收盘价 |
| `($close - $open) / $open` | 当日涨跌幅 |
| `$close / $factor` | 还原原始收盘价 |

写 50 个因子时，表达式引擎会把它们编译成一张计算图，合并重复子表达式后一次性批量计算，而不是对每个因子各跑一遍。

### 5.4 DataHandler 与 Dataset

DataHandler 负责把原始行情加工成特征和标签；Dataset 负责按时间段切片，产出模型能直接读取的训练集。官方因子库 Alpha158 本身就是一种 DataHandler：

```python
from qlib.contrib.data.handler import Alpha158
from qlib.data.dataset import DatasetH

handler = Alpha158(
    instruments="csi300",
    start_time="2017-01-01",
    end_time="2023-12-31",
    fit_start_time="2017-01-01",
    fit_end_time="2020-12-31",
    freq="day",
)

dataset = DatasetH(
    handler,
    segments={
        "train": ("2017-01-01", "2020-12-31"),
        "valid": ("2021-01-01", "2022-06-30"),
        "test": ("2022-07-01", "2023-12-31"),
    },
)
```

`fit_start_time` / `fit_end_time` 指定标准化等统计量只在训练段上拟合，避免未来数据泄漏。这是 Qlib 在防止数据泄漏上做得最仔细的地方之一。

---

## §6 模型层详解

### 6.1 内置模型

模型实现集中在 `examples/benchmarks/` 与 `qlib/contrib/model/`，官方维护 20+ 个：

| 模型 | 类型 | 说明 |
|------|------|------|
| LightGBM（`LGBModel`） | 树模型 | 默认主力，CPU 可跑 |
| XGBoost（`XGBModel`） | 树模型 | 与 LightGBM 互补 |
| MLP | 神经网络 | 基础全连接网络 |
| LSTM / GRU | 序列模型 | 捕捉时序依赖 |
| Transformer | 序列模型 | 注意力机制 |
| GATs | 图模型 | 图注意力，刻画股票间关联 |
| Localformer | 序列模型 | 改进注意力，降低复杂度 |
| TRA | 序列模型 | Temporal Routing Adaptor |

### 6.2 Alpha158 因子库

Alpha158 是最常用的因子集：基于量价数据定义 158 个技术因子，覆盖价格、成交量、波动率等维度；Alpha360 进一步扩展到 360 个。它们都通过表达式引擎声明，可以直接喂给 `LGBModel`、MLP 等模型。

注意：因子的有效性依赖市场环境，Alpha158 是"基线因子集"而非"必胜因子集"。换市场、换周期时先做因子检验，再决定是否沿用。

### 6.3 模型基类与训练流程

所有模型继承自 `qlib.model.base.Model`（含 `fit` / `predict` 两个核心方法）；需要迁移学习或微调的模型继承 `ModelFT`（额外提供 `finetune`）：

```python
from qlib.model.base import Model

class CustomModel(Model):
    def fit(self, dataset):
        # dataset 已按 train 段切片好
        ...

    def predict(self, dataset):
        ...
```

接入 `qrun` 工作流时，模型以配置形式声明。下面是官方示例 `examples/benchmarks/LightGBM/workflow_config_lightgbm_Alpha158.yaml` 中的模型段：

```yaml
model:
  class: LGBModel
  module_path: qlib.contrib.model.gbdt
  kwargs:
    loss: mse
    colsample_bytree: 0.8879
    learning_rate: 0.2
    subsample: 0.8789
    lambda_l1: 205.6999
    lambda_l2: 580.9768
    max_depth: 8
    num_leaves: 210
    num_threads: 20
```

这组超参数是官方调过的结果，不必照抄到自己的市场与数据上；换数据后重新调参是常规动作。

代码方式训练并记录实验：

```python
from qlib.utils import init_instance_by_config
from qlib.workflow import R

model = init_instance_by_config(model_config)
with R.start(experiment_name="model_training_demo"):
    R.log_params(**model_config["kwargs"])
    model.fit(dataset)
```

---

## §7 策略层与回测

### 7.1 策略类型

`qlib/contrib/strategy/` 提供常用策略：

| 策略 | 说明 | 典型参数 |
|------|------|----------|
| **TopkDropoutStrategy** | 按预测分数选 Top-K 持仓，表现差的被轮换掉 | `topk`、`n_drop`、`hold_thresh` |
| **WeightStrategyBase** | 按给定权重生成组合 | 自定义权重 |
| **EnhancedIndexingStrategy** | 增强指数 | 基准、跟踪误差约束 |

### 7.2 qrun 自动化工作流

`qrun` 是 Qlib 的命令行入口，读一个 YAML 配置即可串起"建数据 → 训练 → 回测 → 评估"：

```bash
cd examples
qrun benchmarks/LightGBM/workflow_config_lightgbm_Alpha158.yaml
```

回测部分在配置里声明策略与回测参数，官方示例的策略与回测段如下：

```yaml
port_analysis_config:
    strategy:
        class: TopkDropoutStrategy
        module_path: qlib.contrib.strategy
        kwargs:
            signal: <PRED>        # 占位符，运行时替换为模型预测信号
            topk: 50
            n_drop: 5
    backtest:
        start_time: 2017-01-01
        end_time: 2020-08-01
        account: 100000000
        benchmark: SH000300       # 沪深300指数
        exchange_kwargs:
            limit_threshold: 0.095  # 涨跌停阈值，触板不成交
            deal_price: close
            open_cost: 0.0005       # 买入费率
            close_cost: 0.0015      # 卖出费率
            min_cost: 5             # 单笔最低成本（元）
```

`open_cost`、`close_cost`、`min_cost` 直接决定 `with_cost` 口径的成本，按自己的市场与券商费率改。

### 7.3 读懂回测指标

`qrun` 结束后输出风险分析报告，分无成本与含成本两组，字段相同：

```text
excess_return_without_cost    # 相对基准的超额收益（不扣交易成本）
excess_return_with_cost       # 扣除交易成本后的超额收益
  mean                # 日均超额收益
  std                 # 波动
  annualized_return   # 年化超额收益
  information_ratio   # 信息比率 IR
  max_drawdown        # 最大回撤
```

两组对比能看出策略对成本是否敏感：n_drop 越大换手越高，含成本与不含成本的差距通常越大。`annualized_return` 与 `information_ratio` 是核心参考，`max_drawdown` 反映回撤风险。具体数字取决于数据、区间、模型与成本配置，没有"官方基准值"可言——对比的基准是同数据、同区间下你自己改动的每一版实验，这也是 Recorder 存在的意义。

---

## §8 实验管理与结果分析

### 8.1 Recorder 与 MLflow

每次实验（训练、回测）都会写入 Recorder，参数、指标、产物（模型、预测结果）都可通过 `R` 接口检索（`R.start` 的用法见 §6.3）。记录默认以 MLflow 格式落在本地 `mlruns` 目录，团队共享时可以指向自建的 MLflow 服务：

```python
from qlib.workflow import R

R.uri                          # 当前记录后端地址
recorder = R.get_recorder()    # 当前实验的记录器
recorder.list_metrics()        # 已记录指标
recorder.list_artifacts()      # 已保存的产物
```

### 8.2 图形化报告

`examples/workflow_by_code.ipynb` 展示了用代码拼装工作流并获得图形化报告的方法，包括：

- 预测分数分布与 IC（信息系数）、Rank IC
- 组合累计收益曲线、回撤曲线
- 分位数分组收益对比

模型是否真的在排序上有效，主要看这几张图。

---

## §9 安装与配置

### 9.1 环境要求

| 依赖 | 要求 |
|------|----------|
| Python | 3.8 – 3.12（官方支持范围） |
| numpy | 安装依赖，源码安装前需先就位 |
| cython | 源码安装时需要 |

官方建议用 conda 管理环境——在 conda 之外直接装，某些情况下会因缺少头文件导致依赖编译失败。深度学习模型需要 PyTorch；LightGBM 需要 lightgbm 包，都可通过 pip 安装。

### 9.2 安装步骤

**方式一：pip 安装（最常用）**：

```bash
pip install pyqlib
```

**方式二：源码安装（适合二次开发）**：

```bash
git clone https://github.com/microsoft/qlib.git
cd qlib
pip install numpy
pip install --upgrade cython
pip install .            # 开发场景官方推荐 pip install -e .[dev]
```

两个平台相关提示：Mac（M 系列）上 LightGBM 编译可能因缺 OpenMP 失败，先 `brew install libomp` 再安装；想跳过本地环境问题，也可以直接用官方 Docker 镜像 `pyqlib/qlib_image_stable:stable`。

注意 PyPI 上的包名是 `pyqlib`，`pip install qlib` 装的是另一个同名旧包，不要混淆。

### 9.3 数据初始化

先说当前状态：**官方托管的 A 股数据集因数据安全政策暂停分发**（README 明确标注，恢复时间未定）。README 推荐的替代方案是社区维护的 [chenditc/investment_data](https://github.com/chenditc/investment_data/releases)：

```bash
wget https://github.com/chenditc/investment_data/releases/latest/download/qlib_bin.tar.gz
mkdir -p ~/.qlib/qlib_data/cn_data
tar -zxvf qlib_bin.tar.gz -C ~/.qlib/qlib_data/cn_data --strip-components=1
rm -f qlib_bin.tar.gz
```

官方下载工具（数据集恢复后可用）：

```bash
# 下载 A 股日线数据
python scripts/get_data.py qlib_data --target_dir ~/.qlib/qlib_data/cn_data --region cn
```

数据就位后用 `qlib.init(provider_uri=...)` 初始化即可开始研究。需要校验数据完整性时，运行官方健康检查脚本：

```bash
python scripts/check_data_health.py check_data --qlib_dir ~/.qlib/qlib_data/cn_data
```

---

## §10 常见问题

### Q1：Qlib 和聚宽 / 米筐这类平台有什么区别？

| 维度 | Qlib | 聚宽 / 米筐 |
|------|------|----------|
| **定位** | AI 量化研究基础设施 | 量化平台（研究 + 实盘） |
| **主要能力** | 因子、模型、回测、实验管理 | 回测、模拟盘、实盘 |
| **代码开源** | 完全开源 | 闭源为主 |
| **AI 支持** | 深度集成（表达式引擎、模型库） | 有限，主要靠自行接入 |
| **上手成本** | 需要自己管理数据与代码 | 在线环境开箱即用 |

想快速在云端做研究并接实盘，平台更省事；想搭建可复现、可扩展的 AI 量化流水线，Qlib 更合适。

### Q2：需要多少数据才能跑起来？

社区维护的 A 股日线数据集（chenditc/investment_data）下载解压即可直接用，覆盖全市场股票与指数（获取方式见 §9.3）。最小实践建议：

- 用 `csi300` 股票池起步（300 只，规模可控）
- 训练段至少 3 年日线，验证段半年以上
- 确保股票池与交易日历完整，否则回测结果不可比

### Q3：模型训练需要 GPU 吗？

- LightGBM、XGBoost 在 CPU 上即可高效训练
- MLP、LSTM、Transformer 等神经网络建议 GPU，尤其数据集较大时
- 因子计算只涉及表达式引擎，CPU 足够

### Q4：`D.features` 返回空 DataFrame？

两个最常见的原因：一是时间范围超出了本地数据覆盖范围，先用 `D.calendar()` 确认交易日历起止再设定查询区间；二是股票代码格式写错（应为 `SH600519` 前缀式，写成 `600519.SH` 会查不到）。

### Q5：回测结果和实盘差距大？

回测基于历史数据与假设的成本模型。检查三件事：交易成本参数是否合理、是否用了未来数据（`fit_start_time` 是否只覆盖训练段）、股票池是否包含停牌或退市样本。

---

## §11 总结

Qlib 是一个 AI 量化投资研究基础设施，通过 DataLayer、ModelLayer、StrategyLayer 三层分离，把数据、因子、模型、策略、回测组织成可复现、可比较的流水线，并用 `qrun` 把整条流水线压缩成一条命令。

它的优势：

- 三层分离架构，各层可独立替换
- 表达式引擎大幅降低因子工程成本
- 内置 20+ 模型与 Alpha158/Alpha360 因子库
- `qrun` 一键跑通完整工作流，Recorder 让实验可追溯
- 微软持续维护（2026 年仍有活跃提交），并与 RD-Agent（LLM 自动因子挖掘与模型优化）衔接

它的局限：

- 不提供对接券商的实盘通道，执行只存在于回测模拟中
- 官方托管的 A 股数据集当前暂停分发，起步要依赖社区数据源或自行采集
- 部分示例模型沿用上游 License，商用需确认
- 实时场景需额外开发

如果决定采用，建议按这个顺序推进：

1. 用 §9.3 的社区数据源 + §7.2 的官方 LightGBM/Alpha158 示例跑通第一条基线工作流
2. 把自己的数据源转换为 Qlib 格式（CSV 导入或参考 `scripts/data_collector/` 的采集脚本）
3. 用表达式引擎写自己的因子，与 Alpha158 基线对比
4. 从 `examples/benchmarks/` 挑模型替换基线，或按 §6.3 接入自定义模型
5. 有持续服务需求时，再看官方的在线推理（online serving）与模型滚动更新方案
6. 实盘执行环节自建通道，不指望 Qlib 提供

适合有量化研究需求的开发者与研究者，不适合寻找开箱即用实盘系统的用户。

---

## 自测

1. `Mean($close, 5)` 和手写 `df["close"].rolling(5).mean()` 有什么区别？表达式引擎解决了什么问题？
2. `fit_start_time` / `fit_end_time` 的作用是什么？不设置会带来什么风险？
3. `excess_return_without_cost` 和 `excess_return_with_cost` 两列差异很大，说明什么？
4. 想在 Qlib 里跑自己的神经网络模型，最少需要实现哪些方法？
5. Qlib 为什么不适合直接用于实盘？缺了什么模块？

---

## 资源链接

| 资源 | 链接 |
|------|------|
| **GitHub 仓库** | https://github.com/microsoft/qlib |
| **官方文档** | https://qlib.readthedocs.io |
| **快速入门** | https://qlib.readthedocs.io/en/latest/introduction/quick.html |
| **工作流管理** | https://qlib.readthedocs.io/en/latest/component/workflow.html |
| **论文** | https://arxiv.org/abs/2009.11189 |
| **RD-Agent（自动因子挖掘）** | https://github.com/microsoft/RD-Agent |
| **社区数据源** | https://github.com/chenditc/investment_data |

---

## 文档元信息

- 难度：⭐⭐⭐⭐
- 类型：技术笔记 / 项目解读
- 更新日期：2026-09-17
- 依据来源：GitHub 仓库 README、官方文档、PyPI 发布信息与公开源码
