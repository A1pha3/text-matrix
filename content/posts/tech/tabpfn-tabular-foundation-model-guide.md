---
title: "TabPFN: 表格数据的 Foundation Model 完整指南"
date: "2026-05-06T10:07:31+08:00"
slug: "tabpfn-tabular-foundation-model-guide"
github_repo: "PriorLabs/TabPFN"
source_key: "gh:PriorLabs/TabPFN"
description: "TabPFN 是一个基于 Transformer 架构的表格数据 Foundation Model，完全在合成数据上训练，可同时处理分类与回归任务，无需传统训练过程即可在数秒内完成推理。本文详细介绍其关键概念、使用方法、适用边界与生态体系。"
draft: false
categories: ["技术笔记"]
tags: ["机器学习", "Python", "Transformer", "深度学习"]
---

# TabPFN: 表格数据的 Foundation Model 完整指南

机器学习实践中，表格数据是最常见也最麻烦的领域之一。长期以来，处理表格数据的标准流程是：选模型、调超参、反复训练——这一套下来，少则几十分钟，多则几天。面对一个陌生数据集，光是跑通一个 Baseline，就可能耗掉工程师大半天时间。

**TabPFN**（Tabular Prior-Data Fitted Network）走的是另一条路。它是一个基于 Transformer 的 Foundation Model，专门针对表格数据设计，完全在**合成数据**上预训练，**无需微调**即可直接用于分类和回归任务。传入训练数据、调用预测接口，几秒钟内就能拿到结果，且这一过程发生在一次前向传播里。

本文基于 [PriorLabs/TabPFN](https://github.com/PriorLabs/TabPFN) 编写，信息均来自该仓库的 README、官方文档（docs.priorlabs.ai）与论文，可逐条溯源。

> **快速信息卡**：TabPFN 是一个基于 Transformer 架构的表格数据 Foundation Model，完全在合成数据上训练，可同时处理分类与回归任务，无需传统训练过程即可在数秒内完成推理。默认模型为 TabPFN-3，支持 KV Cache 加速、模型版本选择、模型微调、环境变量配置。

## 学习目标

读完本文后，你应该能够：

- 理解 TabPFN 的基本原理：为什么完全在合成数据上训练的模型可以直接用于真实表格数据
- 判断 TabPFN 是否适合你的数据集（规模、任务类型、硬件条件）
- 使用 TabPFNClassifier 和 TabPFNRegressor 完成分类和回归任务
- 配置 KV Cache、模型版本、环境变量等进阶选项
- 针对常见问题独立完成排查

---

## 目录

- [什么是 TabPFN？](#什么是-tabpfn)
- [关键概念](#关键概念)
- [安装](#安装)
- [快速开始](#快速开始)
- [进阶用法](#进阶用法)
- [性能与基准](#性能与基准)
- [TabPFN 生态体系](#tabpfn-生态体系)
- [适用场景与局限](#适用场景与局限)
- [常见问题排查](#常见问题排查)
- [总结](#总结)
- [练习与进阶路径](#练习与进阶路径)

---

## 什么是 TabPFN？

TabPFN 的基本思想来自 **Prior-Data Fitted Network**（基于先验数据拟合的网络）。它不是一个传统的监督学习模型，而是一个已经"见过"大量合成数据集的 Transformer——这个 Transformer 不是在真实数据上训练的，而是在**程序生成的虚拟数据集**上学会如何做预测的。

这样做有一个实际好处：模型不需要针对你的具体数据做训练，就能给出可用的结果。原因在于：合成数据的分布足够广、足够多样，模型从中学会的是"如何根据数据结构做出预测"这一通用能力，而不是某几个特定数据集上的统计规律。

TabPFN 的版本线如下：

| 版本 | 说明 | 许可 |
|------|------|------|
| v1 | 最初论文，ICLR 2023 | 开源 |
| v2 | Nature 论文（2025 年 1 月出版） | Prior Labs License（Apache 2.0 + 署名要求） |
| 2.5 | 技术报告 arXiv:2511.08667，最大 50,000 行 × 2,000 特征 | 权重非商业许可 |
| 2.6 | 上一代默认模型，推荐上限 100,000 行 × 2,000 特征 | 权重非商业许可 |
| **3** | **当前默认模型**，技术报告 arXiv:2605.13986 | 权重非商业许可 |

默认安装加载的是 **TabPFN-3**，无需额外指定。TabPFN-3 支持最大 1,000,000 × 200、100,000 × 2,000 或 1,000 × 20,000（行 × 特征），特征数增加会压缩行容量。TabPFN-3 之后还有面向 AWS Marketplace 的 TabPFN-3-Plus，在 TabArena 基准上登顶，并原生支持文本列。

## 关键概念

### Foundation Model 在表格数据上的意义

在自然语言处理和计算机视觉领域，Foundation Model（如 GPT 系列、DALL·E）已经彻底改变了应用开发的方式——一个预训练模型，配合少量样本或简单提示，就能适配无数下游任务。表格数据领域此前一直没有类似的突破性模型，原因在于表格数据的异构性（不同数据集的列含义、类型、分布差异巨大）使得跨任务迁移极为困难。

TabPFN 是对这一困境的直接回应：既然无法在真实数据上预训练（会泄露下游任务信息），那就**在无限多样、程序生成的合成数据上训练**，让模型学到的是"表格预测"本身的结构，而非任何特定数据集的规律。

### 合成数据训练的原理

TabPFN 的训练流程大致分三步：

1. **程序生成合成数据集**：通过随机组合不同的数据生成过程（线性模型、非线性模型、交互效应、噪声结构等），生成海量不同"形状"的表格数据。TabPFN-3 使用的是结构因果模型（structural causal model）先验。
2. **在合成数据上做监督学习**：模型在这些合成数据集上学习"给定训练集，预测测试集"的通用能力。
3. **不接触任何真实数据集**：整个训练过程完全在合成数据上进行，避免了数据泄露问题。

这意味着 TabPFN 不会"记住"任何真实数据的模式，而是学会了如何从任意表格数据的结构中推断预测规则。

### 支持的任务类型

TabPFN 同时支持**分类**和**回归**两类任务：

- **二分类**（Binary Classification）
- **多分类**（Multi-class Classification）
- **回归**（Regression），支持点估计、分位数预测、众数预测等多种输出模式

### 关键约束与使用边界

使用 TabPFN 前，必须了解它的硬性约束：

| 约束项 | 说明 |
|--------|------|
| **数据集规模** | TabPFN-3 支持最大 1,000,000 × 200、100,000 × 2,000 或 1,000 × 20,000（行 × 特征） |
| **GPU** | 有 GPU（哪怕 8GB 显存的旧卡）强烈推荐，大数据集需 16GB 显存；CPU 上 TabPFN-3 默认最多 5,000 个样本（旧版本 1,000） |
| **Python 版本** | 仅支持 Python 3.10+（3.10、3.11、3.12、3.13、3.14） |
| **首次使用认证** | 首次使用需要通过浏览器登录 [PriorLabs](https://ux.priorlabs.ai) 接受许可协议，无浏览器环境需设置 `TABPFN_TOKEN` 环境变量 |

超过模型预训练规模时，可以设置 `ignore_pretraining_limits=True` 突破限制（速度会明显下降），或改用 [TabPFN Client](https://github.com/PriorLabs/tabpfn-client) 云端推理。

## 安装

TabPFN 提供三种安装方式。

### 方式一：pip 官方安装（推荐）

```bash
pip install tabpfn
```

`pip install tabpfn` 会同时安装兼容的 PyTorch 版本。如果你想要更小的纯 CPU 安装、需要针对特定加速器或 CUDA 版本的 PyTorch，先到 [PyTorch 安装选择器](https://pytorch.org/get-started/locally/) 选好对应命令，再安装 TabPFN。

### 方式二：从 GitHub 安装最新版本

```bash
pip install "tabpfn @ git+https://github.com/PriorLabs/TabPFN.git"
```

这种方式拿到的是 main 分支的最新代码，适合需要抢先体验新特性或跟进修复的场景。

### 方式三：本地开发安装

```bash
git clone https://github.com/PriorLabs/TabPFN.git
cd TabPFN
uv sync
```

本地开发安装需要先[安装 uv](https://docs.astral.sh/uv/getting-started/installation)（版本 0.10.0+）。

> **注意**：在 Apple Silicon 上要获得最佳性能，建议使用 PyTorch 2.13 或更新的版本，这样才能启用 flash attention。

### 首次使用认证

首次调用 TabPFN 时，模型会自动打开浏览器窗口，引导你在 [PriorLabs](https://ux.priorlabs.ai) 登录并接受许可协议。认证令牌会缓存到本地，之后无需重复操作。

**无浏览器环境**（如 CI/CD 服务器）下，按以下步骤操作：

1. 访问 [https://ux.priorlabs.ai](https://ux.priorlabs.ai)，进入 **License** 标签页接受许可
2. 从账户页面获取 Token
3. 设置环境变量：

```bash
export TABPFN_TOKEN="your_token_here"
```

### 离线使用

TabPFN 首次运行时会自动下载模型权重到本地缓存目录。若需手动下载，可使用仓库自带的脚本：

```bash
python scripts/download_all_models.py
```

或者直接从 HuggingFace 手动下载：

- 分类模型：[tabpfn-v3-classifier-v3_default.ckpt](https://huggingface.co/Prior-Labs/tabpfn_3/blob/main/tabpfn-v3-classifier-v3_default.ckpt)
- 回归模型：[tabpfn-v3-regressor-v3_default.ckpt](https://huggingface.co/Prior-Labs/tabpfn_3/blob/main/tabpfn-v3-regressor-v3_default.ckpt)

下载后将文件放入平台对应的缓存目录（macOS: `~/Library/Caches/tabpfn/`，Linux: `~/.cache/tabpfn/`，Windows: `%APPDATA%\tabpfn\`），或通过 `TabPFNClassifier(model_path="/path/to/model.ckpt")` 直接指定路径。

## 快速开始

### 二分类示例

使用 scikit-learn 内置的乳腺癌数据集演示二分类：

```python
from sklearn.datasets import load_breast_cancer
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split

from tabpfn import TabPFNClassifier

# 加载数据
X, y = load_breast_cancer(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.33, random_state=42
)

# 初始化分类器（首次使用会自动下载模型权重）
clf = TabPFNClassifier()
clf.fit(X_train, y_train)

# 预测概率（用于 ROC AUC）
prediction_probabilities = clf.predict_proba(X_test)
print("ROC AUC:", roc_auc_score(y_test, prediction_probabilities[:, 1]))

# 预测类别
predictions = clf.predict(X_test)
print("Accuracy:", accuracy_score(y_test, predictions))
```

用法与 scikit-learn 的 estimator 一致，不需要手动特征工程、不需要数据标准化、不需要 one-hot 编码。

### 回归示例

使用糖尿病数据集演示回归：

```python
from sklearn.datasets import load_diabetes
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from tabpfn import TabPFNRegressor

# 加载数据
X, y = load_diabetes(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.33, random_state=42
)

# 初始化回归器
reg = TabPFNRegressor()
reg.fit(X_train, y_train)

# 点估计（均值预测）
predictions = reg.predict(X_test)
print("MSE:", mean_squared_error(y_test, predictions))
print("MAE:", mean_absolute_error(y_test, predictions))
print("R^2:", r2_score(y_test, predictions))

# 分位数预测
quantile_predictions = reg.predict(
    X_test,
    output_type="quantiles",
    quantiles=[0.25, 0.5, 0.75],
)
for q, q_pred in zip([0.25, 0.5, 0.75], quantile_predictions):
    print(f"Quantile {q} MAE:", mean_absolute_error(y_test, q_pred))

# 众数预测
mode_predictions = reg.predict(X_test, output_type="mode")
print("Mode MAE:", mean_absolute_error(y_test, mode_predictions))
```

回归器支持多种输出类型：点估计（均值）、分位数预测和众数预测，适用于不同需求的决策场景。

### 批量预测

每次 `predict` 都会重新计算训练集表示。如果测试集很大，**不要逐条调用** `predict`——把 100 条样本分开预测，几乎比一次批量预测慢 100 倍。建议把测试集按 1,000 条一批切分后批量调用。

## 进阶用法

### 使用 KV Cache 加速推理

TabPFN 默认在每次 `predict` 时重新计算训练集表示。对于训练集较大且需要多次预测的场景（如交叉验证、批量推理），可以启用 **KV Cache** 模式，将训练集表示缓存在内存中，换取预测阶段的速度提升：

```python
from tabpfn import TabPFNClassifier

# 启用 KV Cache：fit 阶段构建缓存，predict 直接复用
clf = TabPFNClassifier(fit_mode="fit_with_cache")
clf.fit(X_train, y_train)

# 后续所有 predict 调用都会复用缓存，速度显著提升
predictions = clf.predict(X_test)
```

代价是额外的 GPU 显存占用（大约 O(样本数 × 特征数)），以及 `fit` 阶段本身会稍慢。缓存推理时单次前向最多处理的测试行数由 `TABPFN_MAX_BATCHED_TEST_ROWS` 控制（默认 32,768），更大的测试集会按此上限自动分块。

### 模型版本选择

TabPFN 默认加载 TabPFN-3。需要使用其他版本时，通过 `ModelVersion` 指定：

```python
from tabpfn import TabPFNClassifier, TabPFNRegressor
from tabpfn.constants import ModelVersion

# 使用 TabPFN-2.6（上一代默认模型，适合 10 万行以内数据）
clf_v26 = TabPFNClassifier.create_default_for_version(ModelVersion.V2_6)
reg_v26 = TabPFNRegressor.create_default_for_version(ModelVersion.V2_6)

# 使用 TabPFN v2（Prior Labs License，Apache 2.0 + 署名要求）
clf_v2 = TabPFNClassifier.create_default_for_version(ModelVersion.V2)
```

各检查点的详细说明见仓库 [README](https://github.com/PriorLabs/TabPFN#what-are-the-different-checkpoints-on-hugging-face)。

### 模型微调

对特定任务，TabPFN 支持在下游真实数据上做梯度微调。微调沿用 `TabPFNClassifier`/`TabPFNRegressor` 的接口，入口是 `tabpfn.finetuning` 里的 `FinetunedTabPFNClassifier` 和 `FinetunedTabPFNRegressor`：

```python
from tabpfn.finetuning import FinetunedTabPFNClassifier

finetuned_clf = FinetunedTabPFNClassifier(
    device="cuda",
    epochs=30,
    learning_rate=1e-5,
)
finetuned_clf.fit(X_train, y_train)

predictions = finetuned_clf.predict(X_test)
```

默认配置下，训练时会切出 10% 的数据做验证，并用早停（patience 8）控制过拟合。也可以用 `fit(X_train, y_train, X_val=X_val, y_val=y_val)` 传入自己的验证集。多 GPU 场景用 `torchrun --nproc-per-node=4 your_finetuning_script.py` 启动，DDP 会自动配置，无需改代码。

微调更适合以下场景：对同一份 schema 反复预测、数据分布超出预训练先验（分子性质、专用传感器数据等）、需要跨多个相关表格训练单一模型。数据少于约 1,000 行时，过拟合风险往往大于收益，先跑默认模型的 Baseline 再决定。详见[官方 Fine-Tuning 文档](https://docs.priorlabs.ai/capabilities/fine-tuning)。

### 突破规模限制

数据集超过模型的预训练规模时，会触发内置的规模检查。确认可接受速度下降后，用 `ignore_pretraining_limits=True` 关掉护栏：

```python
from tabpfn import TabPFNClassifier

clf = TabPFNClassifier(ignore_pretraining_limits=True)
clf.fit(X_train, y_train)
```

### 环境变量配置

TabPFN 通过 Pydantic Settings 支持完整的环境变量配置：

```bash
# 自定义模型缓存目录
export TABPFN_MODEL_CACHE_DIR="/path/to/models"

# 允许 CPU 处理大数据集（默认禁止，会很慢）
export TABPFN_ALLOW_CPU_LARGE_DATASET=true

# 禁用浏览器自动登录
export TABPFN_NO_BROWSER=true

# Apple Silicon 上 MPS 显存占比（默认 0.7，防止系统崩溃；不建议超过 1.0）
export TABPFN_MPS_MEMORY_FRACTION=0.7

# KV Cache 推理时单次前向的最大测试行数（默认 32768）
export TABPFN_MAX_BATCHED_TEST_ROWS=32768
```

## 性能与基准

TabPFN 的竞争力来自官方基准与论文：

- **秒级推理**：在标准 CPU/GPU 硬件上，大多数中小规模数据集的推理在数秒内完成，因为推理是一次前向传播，无需超参搜索。
- **TabArena 基准**：官方宣称 TabPFN-2.5 在 TabArena 上超越所有经过调优的树模型，精度与调优 4 小时的 AutoGluon 1.4 集成相当；TabPFN-3-Plus 则在分类与回归上登顶 TabArena。
- **Nature 论文**：TabPFN v2 论文发表于 Nature（2025 年 1 月，doi: 10.1038/s41586-024-08328-6），验证了在中小规模表格分类任务上与调优后的梯度提升树性能相当，推理耗时从 AutoML 的分钟级降至秒级。

但需要注意：TabPFN 的优势区间集中在中小规模数据集。对于超大规模数据或需要极致的领域适配性能，传统 Gradient Boosting 方法（XGBoost、LightGBM、CatBoost）仍然是更稳妥的选择。

## TabPFN 生态体系

TabPFN 本身之外，还有一组配套工具：

| 组件 | 说明 |
|------|------|
| [TabPFN Client](https://github.com/PriorLabs/tabpfn-client) | 云端推理 API 客户端（`pip install tabpfn-client`），无需本地 GPU，适合快速原型验证与生产 |
| [TabPFN Extensions](https://github.com/PriorLabs/tabpfn-extensions) | 扩展库（`pip install tabpfn-extensions`）：SHAP 解释与特征选择（interpretability）、超多分类（many_class）、异常检测与合成数据生成（unsupervised）、嵌入提取（embedding）、数据增强（tabebm）、统计检验（pval_crt）、贝叶斯优化（bayesian_optimization）等 |
| [TabPFN UX](https://ux.priorlabs.ai) | 无代码图形界面，适合业务用户和快速原型 |
| [TabPFN Time-Series](https://github.com/PriorLabs/tabpfn-time-series) | 时间序列零样本预测扩展（`pip install tabpfn-time-series`），把预测当作表格回归处理，默认使用 TabPFN-TS-3 检查点 |

安装 TabPFN Extensions：

```bash
pip install tabpfn-extensions
```

## 适用场景与局限

### 适合使用 TabPFN 的场景

- **快速原型验证**：拿到数据后几分钟内就能得到一个不错的 Baseline，无需调参
- **中小规模表格数据**（10 万行以内）：推理速度快，效果与调优后的 GBDT 相当
- **分类与回归兼有**：同一个 API 支持两种任务，切换成本低
- **无 GPU 资源**：配合 TabPFN Client 云端推理，CPU 机器也能用
- **需要可解释性**：配合 TabPFN Extensions 的 SHAP、特征重要性等工具

### TabPFN 的局限

- **大规模数据**：超过模型预训练规模时受限制，需 `ignore_pretraining_limits=True` 或使用 TabPFN Client / Enterprise Edition
- **GPU 推荐**：CPU 仅适合小数据集（TabPFN-3 默认上限 5,000 样本），否则速度难以接受
- **许可限制**：TabPFN-2.5、2.6、3 的权重采用非商业许可；代码与 v2 权重采用 Prior Labs License（Apache 2.0 + 署名要求）
- **文本支持**：v2 及更早版本无内置文本处理，含文本列的数据集需要先做特征工程；TabPFN-3 系列开始原生支持文本列

---

## 常见问题排查

**Q: 首次运行时自动打开浏览器登录 PriorLabs，但浏览器无法打开怎么办？**

如果你在无浏览器环境（如 CI/CD 服务器、远程 SSH 终端）中运行，可以按以下步骤操作：
1. 在本地有浏览器的机器上访问 [https://ux.priorlabs.ai](https://ux.priorlabs.ai)，登录并接受许可协议
2. 从账户页面获取 Token
3. 在目标机器上设置环境变量：`export TABPFN_TOKEN="your_token_here"`
4. 重新运行代码，应该会自动使用 Token 认证

**Q: 推理速度很慢，怎么办？**

首先检查是否在使用 GPU。TabPFN 强烈推荐使用 GPU 推理，哪怕 8GB 显存的旧卡也会有明显加速。如果没有 GPU，确保数据集规模在 CPU 上限内（TabPFN-3 为 5,000 样本），否则 CPU 推理会非常慢。

其次，可以尝试启用 KV Cache 模式（`fit_mode="fit_with_cache"`），在多次预测场景下会有显著加速。最后，确认测试集是批量预测而不是逐条调用 `predict`。

**Q: 安装了 tabpfn 但导入时提示 ModuleNotFoundError**

检查 Python 版本是否为 3.10+。TabPFN 不支持 Python 3.9 及以下版本。如果版本正确，尝试重新安装：`pip install --upgrade tabpfn`。

**Q: 模型权重下载失败怎么办？**

手动从 HuggingFace 下载权重文件（TabPFN-3 为 `tabpfn-v3-classifier-v3_default.ckpt` 和 `tabpfn-v3-regressor-v3_default.ckpt`），然后放入平台对应的缓存目录：
- macOS: `~/Library/Caches/tabpfn/`
- Linux: `~/.cache/tabpfn/`
- Windows: `%APPDATA%\tabpfn\`

或者通过设置环境变量 `TABPFN_MODEL_CACHE_DIR` 指定自定义缓存目录。

**Q: 商业项目可以使用 TabPFN 吗？**

TabPFN-2.5、2.6、3 的权重采用非商业许可；代码与 v2 权重采用 Prior Labs License（Apache 2.0 + 署名要求）。如果需要商业使用，可以：
1. 使用 v2 权重（Prior Labs License，可商用）
2. 联系 Prior Labs 获取商业许可（[sales@priorlabs.ai](mailto:sales@priorlabs.ai)）
3. 对于商业项目，考虑使用传统 Gradient Boosting 方法（XGBoost、LightGBM）

---

## 总结

TabPFN 改变了表格数据建模的思路：让模型在无限多样的合成数据上学会"预测"本身，然后零样本泛化到任意真实表格数据，而不是针对每个数据集从头训练。默认的 TabPFN-3 把推理压缩到一次前向传播，秒级出结果，省去了超参搜索的痛点，同时在中小数据集上与调优后 GBDT 方法性能相当。

处理中小规模表格数据时，TabPFN 可以作为第一站——几分钟内就能得到一个可用的 Baseline，再决定是否需要花费更多时间在传统方法上做精调。

---

## 练习与进阶路径

### 自测练习

1. **快速开始**：用 scikit-learn 的内置数据集（如乳腺癌数据集、糖尿病数据集）运行本文中的二分类和回归示例，观察输出结果。

2. **性能对比**：在同一个数据集上，分别用 TabPFN 和 XGBoost/LightGBM 训练模型，对比准确率/MAE 和训练时间。

3. **KV Cache 实验**：在一个稍大的数据集上，分别用默认模式和 `fit_mode="fit_with_cache"` 模式运行，对比预测速度。

4. **回归输出类型对比**：用回归示例中的 `output_type="quantiles"` 和 `output_type="mode"`，观察不同输出类型的差异。

5. **批量预测**：把测试集切成 1,000 条一批，对比逐条预测与批量预测的耗时差距。

### 进阶方向

- **深入原理**：阅读 TabPFN v2 论文（Nature 2025）和 TabPFN-3 技术报告，理解 Prior-Data Fitted Network 的训练原理
- **模型微调**：如果有 GPU 资源，用 `FinetunedTabPFNClassifier` 在下游数据集上微调 TabPFN，观察性能变化
- **TabPFN Extensions**：安装并试用 SHAP 解释、特征选择、异常检测等扩展功能
- **与其他方法对比**：在 OpenML 基准数据集上，系统对比 TabPFN、XGBoost、LightGBM、CatBoost 的性能
- **贡献社区**：查看 GitHub Issues，选择一个感兴趣的问题参与讨论或提交 PR

---

## 实践案例

### 案例1：用 TabPFN 快速预测客户流失

假设你有一个客户数据集，想预测哪些客户会流失：

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from tabpfn import TabPFNClassifier

# 加载数据
df = pd.read_csv("customer_churn.csv")
X = df.drop("churn", axis=1)
y = df["churn"]

# 分割数据
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 用 TabPFN 训练
clf = TabPFNClassifier()
clf.fit(X_train, y_train)

# 预测
predictions = clf.predict(X_test)
print(f"Accuracy: {(predictions == y_test).mean():.2%}")
```

不需要调参，TabPFN 自动适应数据特征。

### 案例2：回归任务 - 预测房价

```python
from sklearn.datasets import fetch_california_housing
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split

from tabpfn import TabPFNRegressor

# 加载数据
X, y = fetch_california_housing(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# 训练回归器
reg = TabPFNRegressor()
reg.fit(X_train, y_train)

# 预测（点估计）
predictions = reg.predict(X_test)
print(f"MAE: {mean_absolute_error(y_test, predictions):.2f}")

# 预测（分位数）
quantile_preds = reg.predict(X_test, output_type="quantiles", quantiles=[0.25, 0.5, 0.75])
print("分位数预测完成")
```

### 案例3：用 KV Cache 加速交叉验证

```python
from sklearn.model_selection import cross_val_score
from tabpfn import TabPFNClassifier

clf = TabPFNClassifier(fit_mode="fit_with_cache")

# 交叉验证 - KV Cache 让第二次及以后的预测更快
scores = cross_val_score(clf, X, y, cv=5)
print(f"Cross-validation scores: {scores}")
```

`fit_mode="fit_with_cache"` 在交叉验证时显著提升速度。

---

## 延伸阅读

- 仓库地址：[https://github.com/PriorLabs/TabPFN](https://github.com/PriorLabs/TabPFN)
- 官方文档：[https://docs.priorlabs.ai](https://docs.priorlabs.ai)
- TabPFN v2 论文：[Nature 2025](https://doi.org/10.1038/s41586-024-08328-6)
- TabPFN-2.5 技术报告：[arXiv:2511.08667](https://arxiv.org/abs/2511.08667)
- TabPFN-3 技术报告：[arXiv:2605.13986](https://arxiv.org/abs/2605.13986)
- 交互式 Colab 教程：[TabPFN Demo Notebook](https://colab.research.google.com/github/PriorLabs/TabPFN/blob/main/examples/notebooks/TabPFN_Demo_Local.ipynb)
- 官方 Discord 社区：[https://discord.gg/BHnX2Ptf4j](https://discord.gg/BHnX2Ptf4j)
