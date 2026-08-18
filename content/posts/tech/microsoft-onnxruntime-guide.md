---
title: "ONNX Runtime：把训练好的模型部署到任何硬件的推理加速器"
date: "2026-04-24T12:00:00+08:00"
draft: false
slug: "microsoft-onnxruntime-guide"
github_repo: "microsoft/onnxruntime"
source_key: "gh:microsoft/onnxruntime"
description: "ONNX Runtime 是微软开源的跨平台机器学习推理与训练加速器。它把 PyTorch、TensorFlow 等框架训练好的模型统一成 ONNX 格式，再通过图优化和十余个硬件执行后端，让同一份模型在云服务器、Windows、macOS、移动端和浏览器里都能跑。本文拆解它的 EP 机制、部署路径和适用边界。"
categories: ["技术笔记"]
tags: ["机器学习", "ONNX", "微软", "推理加速", "PyTorch"]
---

# ONNX Runtime：把训练好的模型部署到任何硬件的推理加速器

> **项目地址**：[github.com/microsoft/onnxruntime](https://github.com/microsoft/onnxruntime)
>
> **一句话定位**：模型训练在 PyTorch，部署到哪里都行——ORT 负责把 ONNX 格式的模型调成目标硬件上最快的样子。

## 一句话判断

ONNX Runtime（简称 ORT）解决的不是"模型跑不快"这一个点，而是"模型训练完该怎么发布"这整条链路：训练框架（PyTorch、TensorFlow）只负责产出模型，不负责部署；生产环境里 CPU、GPU、手机 NPU、浏览器各有各的加速路径，逐个去适配是重复劳动。ORT 用 ONNX 做统一中间格式，再靠一套 Execution Provider（执行后端）机制，把"同一个模型"调度到不同硬件上。推理是它的主战场，训练加速是附加能力。最新稳定版 v1.28.0（2026-08 发布），MIT 协议。

## 项目概览

| 维度 | 事实 |
|------|------|
| 仓库 | `microsoft/onnxruntime` |
| 语言 | C++ / C / C# / Python / Rust / JavaScript |
| 协议 | MIT |
| 官网 | [onnxruntime.ai](https://onnxruntime.ai/) |
| 最新版本 | v1.28.0（2026-08）；main 分支已推进到 1.30 |
| GitHub Stars | 约 21k（2026-08，以仓库为准） |
| 定位 | 跨平台推理 + 训练加速，ONNX 格式的运行时 |

## 它为什么存在

训练和部署是两个世界。

PyTorch 里 `model = YourModel()`，跑起来快，因为训练框架把算子绑定到了自己的 CUDA kernel 上；可一旦要发布，问题就来了——服务器要用 CUDA，Windows 桌面想用 DirectML 吃满显卡，iPhone 要用 Core ML 调神经引擎，浏览器里又只能靠 WebAssembly 或 WebGPU。同一个模型，每个平台写一套推理代码，维护成本跟着翻倍。

ORT 的答案分两步：

1. 用 **ONNX** 作为模型的"通用语言"。PyTorch、TensorFlow、Keras、scikit-learn、LightGBM、XGBoost 导出的模型都能转成 ONNX 图，这是一份与框架无关的计算图描述。
2. 用 **Execution Provider（EP，执行后端）** 把这份图映射到具体硬件。CPU 有 CPU EP，NVIDIA 显卡走 CUDA EP，Intel 硬件走 OpenVINO EP，Apple 设备走 Core ML EP——模型还是那一份，换个 EP 就换了个加速通道。

所以"跨平台"不是 ORT 自己实现了每个硬件上的算子，而是它给每个硬件后端留了标准接口，把框架层和硬件层解耦。

## 系统地图：EP 机制

ORT 一次推理的路径大致是：

```text
ONNX 模型 → 图优化（常量折叠 / 算子融合 / 内存规划）
          → EP 注册表（选第一个能处理该算子的后端）
          → 目标硬件执行
```

`InferenceSession` 创建时按顺序传入 `providers` 列表，ORT 从上到下找能承接整个子图的 EP；找不到的就落回 CPU EP 兜底。这是 ORT 最重要的一个概念——**性能来自"把活分给对的硬件"**，而不只是某个 kernel 快。

各平台的可用 EP 差异很大，选型时先对照这张表：

| 平台 | 主要执行后端 |
|------|-------------|
| Windows | CPU、CUDA、DirectML、TensorRT、OpenVINO、QNN |
| Linux | CPU、CUDA、TensorRT、ROCm、OpenVINO、QNN |
| macOS | CPU、Core ML |
| Android | CPU、NNAPI、QNN、XNNPACK |
| iOS | CPU、Core ML、XNNPACK |
| 浏览器（Web） | WebAssembly、WebGPU、WebNN |

两个容易踩的坑：**DirectML 只在 Windows 上**（依赖 DirectX 12），macOS 的 GPU 加速走的是 Core ML，能调 Apple 神经引擎；**Qualcomm 的旧 SNPE 已被 QNN 取代**，Android 上现在按 QNN 来用。另外 WebGPU / WebNN 是 ORT 近两年的活跃方向，浏览器里跑 transformer 已经从"演示"走向"可用"。

## 核心机制

### 1. 图优化

ORT 加载模型后先做图级优化，再交给 EP。几个主要手段：

- **常量折叠**：把输入固定的节点在加载时就算掉，省去每次推理的重复计算。
- **算子融合**：把相邻的多个算子合成一个 kernel，减少内存读写。比如 Attention 相关的多层融合，是 transformer 提速的主要来源。
- **内存规划**：预分配中间张量、复用缓冲区，避免推理过程中的频繁分配。
- **子图分割**：图太大或某个 EP 覆盖不全时，把图切成子图，能加速的给加速后端，其余的留 CPU。

优化等级用 `GraphOptimizationLevel` 控制：`ORT_ENABLE_BASIC` / `ORT_ENABLE_EXTENDED` / `ORT_ENABLE_ALL`，一般直接开 `ORT_ENABLE_ALL`。

### 2. EP 分派

EP 是"把算子执行交出去"的插件接口。主流后端：

- **CUDA EP**：NVIDIA GPU。注意 CUDA 12 支持已在 1.27.0 移除，当前 GPU 包面向 CUDA 13。
- **TensorRT EP**：NVIDIA 的高性能推理引擎，比通用 CUDA kernel 更激进，但首次构建有额外开销，适合固定形状的线上服务。
- **DirectML EP**：Windows 专属，走 DirectX 12，好处是不挑显卡品牌，AMD / Intel 核显也能用。
- **Core ML EP**：Apple 生态，能利用 Neural Engine。
- **ROCm EP**：AMD GPU，Linux 为主。
- **OpenVINO EP**：Intel CPU / GPU / NPU。
- **WebGPU / WebNN EP**：浏览器与 JS 环境的加速路径。

### 3. 会话选项

同一模型，会话配置不同，性能可以差出数量级。常用调整点：线程数（`intra_op_num_threads` 管单算子内并行，`inter_op_num_threads` 管算子间并行）、执行模式（顺序 / 并行）、是否开启 profiling。

## 一次完整部署路径

把"训练好的 PyTorch 模型部署到 GPU 服务器"串起来看，一共四步：

1. **导出**：`torch.onnx.export` 把模型转成 `model.onnx`，同时声明输入输出名和动态维度。
2. **安装**：服务器上 `pip install onnxruntime-gpu`（CUDA 13）。
3. **建会话**：`InferenceSession("model.onnx", providers=["CUDAExecutionProvider", "CPUExecutionProvider"])`，第一顺位 CUDA，起不来自动落 CPU。
4. **推理**：准备输入张量，`sess.run` 拿结果。

这四步里只有第 1 步依赖训练框架，后面全在 ORT 里，换硬件只需改第 3 步的 `providers`。

## 快速开始

### 安装

```bash
# CPU 版
pip install onnxruntime

# GPU 版（CUDA）
pip install onnxruntime-gpu
```

从 1.27.0 起 GPU 包面向 CUDA 13（CUDA 12 支持已移除）。TensorRT、OpenVINO、QNN 等后端的安装形态随版本调整，装之前以官方文档的 [pip 安装页](https://onnxruntime.ai/docs/install/) 为准。

### 基本推理

```python
import onnxruntime as ort
import numpy as np

# 创建会话
sess = ort.InferenceSession("model.onnx")

# 获取输入输出名称
input_name = sess.get_inputs()[0].name
output_name = sess.get_outputs()[0].name

# 准备输入数据（以 224x224 三通道图像为例）
input_data = np.random.randn(1, 3, 224, 224).astype(np.float32)

# 运行推理
result = sess.run([output_name], {input_name: input_data})
print(result)
```

### 指定执行后端

```python
import onnxruntime as ort

sess = ort.InferenceSession(
    "model.onnx",
    providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
)
print(sess.get_providers())  # 查看实际生效的后端
```

### PyTorch 模型导出

```python
import torch

model = YourModel()
model.eval()

dummy_input = torch.randn(1, 3, 224, 224)
torch.onnx.export(
    model,
    dummy_input,
    "model.onnx",
    export_params=True,
    opset_version=17,
    do_constant_folding=True,
    input_names=["input"],
    output_names=["output"],
    dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}},
)
```

`dynamic_axes` 声明了 batch 维可变，导出的模型就能在推理时接收不同 batch 的输入。opset 版本按你用的 PyTorch 默认值来即可，不用刻意追求新。

### 会话选项

```python
import onnxruntime as ort

sess_options = ort.SessionOptions()
sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
sess_options.execution_mode = ort.ExecutionMode.ORT_PARALLEL
sess_options.intra_op_num_threads = 4
sess_options.inter_op_num_threads = 2

sess = ort.InferenceSession("model.onnx", sess_options)
```

## 训练加速（ORTModule）

ORT 的重心是推理，但保留了训练加速能力：把 PyTorch 模型包一层 `ORTModule`，训练主循环基本不用改。

```python
import torch
from onnxruntime.training.ortmodule import ORTModule

model = ORTModule(torch_model)

optimizer = torch.optim.SGD(model.parameters())
for data, target in dataloader:
    optimizer.zero_grad()
    output = model(data)
    loss = criterion(output, target)
    loss.backward()
    optimizer.step()
```

说明边界：ORTModule 的算子覆盖和优化效果都弱于原生 PyTorch 训练路径，官方把它定位为"多节点 NVIDIA GPU 上的 transformer 训练加速"这类特定场景。绝大多数部署任务用不到它，别因为"能训练"就误以为它可以替代训练框架。

## 关于性能：别只看加速比

网上流传的"ResNet-50 快 2-3 倍""BERT 快 1.5-2 倍"这类数字，来源不一、硬件环境不透明，直接抄进文档没有意义。判断 ORT 值不值得用，看三点：

1. **测的是什么**：官方维护 [benchmark 页面](https://onnxruntime.ai/docs/performance/benchmarks.html)，覆盖分类、检测、NLP 等常见模型在 CPU / GPU 上的延迟与吞吐。数字反映的是"图优化 + 特定 EP"组合的结果。
2. **数字变化反映哪部分系统**：CPU 上提速大多来自图优化和 MLAS 算子库；GPU 上提速主要来自 CUDA / TensorRT EP 的算子实现。
3. **不能推出什么**：这些数字换硬件、换 batch、换模型就不成立了。你自己的模型、自己的机器，必须跑一遍再下结论。

正确的姿势是拿你的模型在 ORT 和框架原生推理之间各跑一次，用 profiling 定位瓶颈，而不是相信某个基准表。

## 适用边界与采用顺序

**先用起来**：模型要跨平台部署、要上 GPU 但不想绑死框架、模型来源是多个框架——这三类场景直接上 ORT，收益明确。

**可以等等**：模型已经用框架原生方案部署、性能已达标；或者你的场景强依赖训练侧能力——这时迁移的收益不值得成本。

**别用它**：追求对某个硬件 kernel 的极致手调（直接用 TensorRT / TFLite 更彻底）、模型生态完全封闭在单一框架内、或只在小范围原型里跑几次——ORT 的配置面反而成为负担。

从零接入的顺序：先把一个模型端到端跑通（导出 → 建会话 → 推理），再逐项打开图优化、换 EP、调线程，每一步用 profiling 验证收益。

## 常见问题

**Q: ORT 和 TensorRT 什么关系？**

TensorRT 是 NVIDIA 的推理优化引擎，只吃 NVIDIA GPU；ORT 通过 TensorRT EP 把它作为后端之一。模型只跑 NVIDIA GPU、且追求极限性能，直接上 TensorRT 更纯粹；要跨平台、要一份模型多处部署，走 ORT。

**Q: ORT 支持哪些模型格式？**

核心是 ONNX 格式。PyTorch、TensorFlow / Keras、scikit-learn、LightGBM、XGBoost 等都可以通过转换工具导出为 ONNX。ORT 不直接读 `.pt` 或 `.h5`。

**Q: 怎么排查性能问题？**

先确认实际生效的 EP（`sess.get_providers()`），再开 profiling：

```python
import onnxruntime as ort

sess_options = ort.SessionOptions()
sess_options.enable_profiling = True

sess = ort.InferenceSession("model.onnx", sess_options)
# 运行推理...
print(sess.end_profiling())  # 返回 profile 文件路径
```

profile 文件里能看出每个算子的耗时，据此决定是换 EP、开优化还是拆模型。

**Q: ORT 支持自定义算子吗？**

支持。通过 `register_custom_ops_library` 加载自定义算子库（C/C++ 编写），Python 端也有 `CustomOp` 通道。自定义算子的构建门槛不低，常规模型用不到。

## 延伸阅读

- [ONNX Runtime 官方文档](https://onnxruntime.ai/docs/)
- [ONNX Runtime GitHub](https://github.com/microsoft/onnxruntime)
- [Execution Providers 说明](https://onnxruntime.ai/docs/execution-providers/)
- [官方性能基准](https://onnxruntime.ai/docs/performance/benchmarks.html)
- [ONNX Runtime Inference Examples](https://github.com/microsoft/onnxruntime-inference-examples)

---

*本文基于 GitHub 仓库 [microsoft/onnxruntime](https://github.com/microsoft/onnxruntime) 的官方文档与 README 整理，版本信息以 2026-08 为基准。*
