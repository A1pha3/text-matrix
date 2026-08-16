---
title: "WeatherNext 2：Google DeepMind 开源气象预报模型家族解析"
date: "2026-08-16T03:32:00+08:00"
slug: "weathernext-2-deepmind-weather-forecasting-models"
github_repo: "google-deepmind/weathernext"
source_key: "gh:google-deepmind/weathernext"
description: "WeatherNext 是 Google DeepMind 的全球中期大气与气旋预报模型家族，仓库收纳 WN2、GraphCast、GenCast 三代模型与预训练权重。本文梳理模型谱系、获取数据的四条官方通道与本地运行门槛。"
draft: false
categories: ["技术笔记"]
tags: ["DeepMind", "气象预报", "机器学习", "JAX"]
---

# WeatherNext 2：Google DeepMind 开源气象预报模型家族解析

先给判断：这个仓库的价值不在「又一个 AI 模型」，而在于它是 DeepMind 气象预报三代技术路线（图神经网络、扩散模型、FGN）的合集发布口——模型代码、预训练权重、论文、免费数据通道一次性给齐。对多数读者来说，正确的打开方式甚至不是跑模型，而是直接消费它每日更新的预报数据。

`google-deepmind/weathernext` 约 7,500 stars，主语言 Python（JAX 生态），Apache 2.0（代码）+ CC BY 4.0（其余材料）双许可，2023 年 7 月创建，最近提交 2026-08-11。仓库明确定位为研究代码：不保证 API 稳定，建议锁定具体 release 安装。

## 模型谱系：三代路线一个仓库

WeatherNext 2（WN2）是当前主力——Google DeepMind 与 Google Research 联合开发的全球中期大气与气旋预报模型。仓库同时收容两代前辈：

| 模型 | 技术路线 | 发布名 |
| --- | --- | --- |
| WeatherNext Graph | 图神经网络（GNN），确定性中期预报 | GraphCast |
| WeatherNext Gen | 扩散模型（diffusion），集合预报 | GenCast |
| WeatherNext 2（FGN） | 从边缘概率构造联合概率预报 | WN2 |

三者的分野是理解这个家族的钥匙：GraphCast 回答「最可能发生什么」，GenCast 回答「不确定性如何分布」，WN2 的技术报告标题（Skillful joint probabilistic weather forecasting from marginals）则点明它在边际分布之上直接构造联合概率——这也是它能同时输出大气场与气旋路径的概率预报的原因。 WN2 与气旋专用版共享同一套算法，仅因独立训练而权重不同。

## 预训练模型矩阵：按年份分档，不是按版本号

仓库提供的权重按「训练数据截止年」分档，这个设计初看容易困惑，实际逻辑很清晰：

- **WeatherNext2_<2025**：0.25° 分辨率（约 30km），在 ECMWF HRES 上微调、由业务 HRES 初始条件直接初始化，2024 年数据训练——这是业务运行版本，权重为 `WeatherNext2_<2025_model{1,2,3,4}.npz`。
- **WeatherNextCyclones_<2025**：2025 年大西洋飓风季实际值班过的版本（对外称 FNV3），复现论文结果用。
- **WeatherNextCyclones_<2024 / <2023**：分别复现论文在 2024、2023 年的结果。
- **Cyclones Mini（1° 分辨率）**：轻量版，面向低显存场景（单 TPU/GPU、本地测试），官方明言性能不及大版本。

注意 WN2 与 Cyclones 的差别只有一点：WN2 额外预报 100 米高度风场。

## 大多数人该走的路：不跑模型，直接拿数据

这是本文最实用的一节。自建运行环境需要 TPU（或 H100 级 GPU）才能跑非 Mini 权重，而官方提供了四条免费数据通道，覆盖从研究到应用的各种需求：

| 通道 | 形态 | 适合 |
| --- | --- | --- |
| Google Cloud（Earth Engine / BigQuery / Vertex AI） | 数据湖/查询 | 大规模研究、批量回算 |
| WeatherLab（含气旋路径） | 交互式可视化 | 直观看预报与不确定性 |
| Open-Meteo API（含交互式构建器） | REST API | 应用集成、轻量验证 |
| GCS bucket `dm_graphcast` | 权重 + 样例数据 | 本地复现 |

第三条通道对应用开发者尤其友好——一个 HTTP 请求就能拿到模型输出，不必碰任何 ML 基础设施。

## 真要本地跑：门槛与路径

硬件边界（README 明示）：推荐 TPU；GPU 路线必须切换 attention 实现，非 Mini 模型需要 H100 级显存，Mini 版 P100 即可推理。最快路径是官方 Colab 笔记本（`docs/weathernext2/wn2_demo.ipynb`），默认跑 Cyclones Mini，Colab 免费 `v5e-1` 运行时就能开。

本地安装锁定版本：

```bash
pip install git+https://github.com/google-deepmind/weathernext.git@v0.3.0
```

笔记本内完成的是一套完整闭环：加载云端权重 → 读 HRES 初始场 → 初始化 WN2（FGN）架构 → 自回归（autoregressive）滚动预报 → 可视化温度/风速/位势高度 → 跑直接气旋追踪器输出路径 → 计算损失并做一次梯度下降。也就是说，它把「推理」与「训练一步」都演示了。

想完整训练则要另备数据：ERA5（经 WeatherBench2 以 Zarr 提供）做基础训练，WeatherBench2 的 HRES 数据做业务微调。注意这些数据集有独立条款，使用前需自查合规。

仓库结构上，`utils/` 收纳了跨模型共享的基础设施——自回归滚动、输入归一化、图构建块、损失计算、xarray 兼容层——这意味着读这个目录等于读三代模型共用的工程骨架。

## 边界与风险声明

仓库的免责条款值得转述：这不是 Google 官方支持的产品；模型未与任何气象机构合作产出，也未被其背书，不能替代官方预警。对要做下游应用的人，这段话是产品设计的硬约束——AI 预报可以当参考源，不能当决策源。

## 采用建议

按需求分三档：做应用（天气类产品、可视化、研究分析）→ 直接走 Open-Meteo API 或 WeatherLab，零基础设施成本；做研究（模型改进、极端天气分析）→ Colab + Mini 权重起步，必要时上 TPU 复现完整版；做工程（业务化部署）→ 评估 GCS 数据通道订阅，比自运维模型便宜得多。真正需要 clone 仓库跑训练的，只剩「要在自有数据上微调」这一类需求。
