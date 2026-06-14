---
title: "LiteRT-LM：Google 生产级边缘设备 LLM 推理框架指南"
date: "2026-04-06T20:00:00+08:00"
slug: "litert-lm-google-edge-llm-inference-guide"
description: "介绍 Google LiteRT-LM 边缘设备 LLM 推理框架，涵盖核心特性、技术架构、多语言API、工具调用、多模态能力和全平台部署实践。"
draft: false
categories: ["技术笔记"]
tags: ["LiteRT-LM", "Google AI Edge", "LLM推理", "边缘计算", "Android", "Gemma"]
---

# LiteRT-LM：Google 生产级边缘设备 LLM 推理框架指南

## 这篇文章覆盖什么

- LiteRT-LM 的项目定位与边缘 AI 推理的技术背景
- 核心特性、技术架构和支持的模型
- 在 Android、iOS、Web、桌面端和 IoT 设备上部署 LLM
- 多语言 API（Kotlin、Python、C++、Swift）
- Tool Use / Function Calling 在边缘设备上的实现方式
- LiteRT-LM CLI 快速原型开发和测试
- 从源码编译和定制优化
- Gemma、Llama、Phi-4、Qwen 等模型的部署实践

---

## 1. 项目概述

### 1.1 是什么

**LiteRT-LM** 是 Google AI Edge 推出的**生产级、高性能、开源边缘设备 LLM 推理框架**。它专为在资源受限的边缘设备上部署大型语言模型而设计，覆盖 Android、iOS、Web、桌面端和 IoT（如树莓派）等全平台。

LiteRT-LM 已集成到 Google 的多个产品中，包括 **Chrome、Chromebook Plus、Pixel Watch** 等。也就是说它经过了大量真实用户场景的验证，不是实验性项目。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | 3.8k |
| GitHub Forks | 368 |
| Watchers | 47 |
| 最新版本 | v0.10.2（2026-04-14） |
| 发布版本数 | 17 个 |
| 分支数 | 137 |
| 提交数 | 1,350 |
| License | Apache-2.0 |

### 1.3 技术栈

| 语言 | 占比 |
|------|------|
| C++ | 76.6% |
| CMake | 7.1% |
| Starlark | 5.0% |
| Rust | 4.1% |
| Python | 3.9% |
| Kotlin | 1.8% |
| 其他 | 1.5% |

### 1.4 版本历史

| 版本 | 发布内容 |
|------|---------|
| **v0.10.1** | 最新版本，DataStream 增强 |
| **v0.10.0** | Tool Use 工具调用持续改进 |
| **v0.9.0** | Function Calling 能力改进，应用性能稳定性增强 |
| **v0.8.0** | 桌面 GPU 支持和多模态能力 |
| **v0.7.0** | Gemma 模型的 NPU 加速支持 |

---

## 2. 核心特性详解

### 2.1 跨平台支持

LiteRT-LM 支持的平台覆盖了主流边缘设备场景：

| 平台 | 状态 | 说明 |
|------|------|------|
| **Android** | ✅ 稳定 | Kotlin API，生产就绪 |
| **iOS** | 🚧 开发中 | Swift API，即将发布 |
| **Web** | ✅ 稳定 | 通过 Wasm/WebGL |
| **桌面端** | ✅ 稳定 | Linux/macOS/Windows (WSL) |
| **IoT** | ✅ 稳定 | Raspberry Pi 等 ARM 设备 |

**Android 覆盖范围**：手机、平板、Android Auto、车载系统
**iOS 覆盖范围**：iPhone、iPad、Apple Watch（未来规划）

### 2.2 硬件加速

LiteRT-LM 通过 GPU 和 NPU 加速器实现峰值性能：

| 加速类型 | 支持硬件 |
|----------|---------|
| **GPU 加速** | Qualcomm Adreno、ARM Mali、Apple GPU |
| **NPU 加速** | Qualcomm Hexagon、Apple Neural Engine、联发科 NPU |
| **CPU 优化** | ARM NEON、SIMD 指令集优化 |

### 2.3 多模态支持

LiteRT-LM 支持**视觉和音频输入**的多模态模型：

| 模态 | 支持的输入 | 示例模型 |
|------|-----------|---------|
| **视觉** | 图片、图表、文档 | Gemma Vision、Qwen2-VL |
| **音频** | 语音、音频流 | Gemma 3n（语音模型） |

### 2.4 工具调用（Tool Use）

LiteRT-LM 实现了 **Function Calling / Tool Use** API，支持代理工作流（Agentic Workflows）：

| 功能 | 说明 |
|------|------|
| **函数调用** | 结构化输出，JSON Schema 约束 |
| **外部约束** | 支持 Llguidance 语法约束 |
| **RAG 支持** | 检索增强生成的内置支持 |

### 2.5 支持的模型

LiteRT-LM 广泛支持主流开源大模型：

| 模型家族 | 代表模型 | 说明 |
|----------|---------|------|
| **Gemma** | Gemma 4、Gemma 3n | Google 自家模型，深度优化 |
| **Llama** | Llama 3.x | Meta 开源模型 |
| **Phi** | Phi-4 | Microsoft 小而美模型 |
| **Qwen** | Qwen2、Qwen2.5 | 阿里通义千问 |
| ** Gemma Tool** | FunctionGemma | 工具调用专用变体 |

---

## 3. 技术架构解析

### 3.1 整体架构

LiteRT-LM 采用分层架构设计：

```
┌─────────────────────────────────────────────────────────┐
│                    应用层 (Application)                 │
├─────────────────────────────────────────────────────────┤
│  Kotlin API  │  Python API  │  C++ API  │  Swift API  │
├─────────────────────────────────────────────────────────┤
│                    推理引擎 (Inference Engine)          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ Tokenizer  │  │   Model    │  │  Tool Use  │    │
│  │   分词器   │  │   推理    │  │  函数调用  │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
├─────────────────────────────────────────────────────────┤
│                 硬件适配层 (Hardware Adaptation)         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │    GPU     │  │    NPU     │  │    CPU     │    │
│  │  加速器   │  │   加速器   │  │   优化    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
├─────────────────────────────────────────────────────────┤
│                    运行时 (Runtime)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  Android   │  │    iOS     │  │   Linux    │    │
│  │  Runtime   │  │  Runtime   │  │  Runtime   │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 3.2 核心模块

| 模块 | 路径 | 功能 |
|------|------|------|
| **runtime** | `/runtime` | C++ 核心推理引擎 |
| **kotlin** | `/kotlin` | Android/iOS Kotlin API |
| **python** | `/python` | Python 绑定（nanobind） |
| **c** | `/c` | C API 接口 |
| **rust** | `/rust` | Rust 绑定 |
| **cmake** | `/cmake` | CMake 构建系统 |

### 3.3 数据流

LiteRT-LM 的推理数据流：

```
用户输入 (Prompt)
       ↓
   Tokenizer (分词器)
       ↓
模型推理 (Model Inference)
       ↓
  Tool Use / Function Calling
       ↓
  Tokenizer (解码器)
       ↓
结构化输出 (JSON/Function Call)
```

### 3.4 构建系统

LiteRT-LM 支持多种构建系统：

| 构建系统 | 用途 | 平台 |
|----------|------|------|
| **Bazel** | Google 内部构建 | 全平台 |
| **CMake** | 跨平台构建 | Linux/macOS/Windows/Android |
| **Bazelisk** | Bazel 版本管理 | 自动管理 |

---

## 4. 快速上手

### 4.1 CLI 快速尝鲜（无需写代码）

使用 `uv` 安装 LiteRT-LM CLI：

```bash
# 安装 LiteRT-LM
uv tool install litert-lm

# 运行 Gemma 3n 模型
litert-lm run \
  --from-huggingface-repo=google/gemma-3n-E2B-it-litert-lm \
  gemma-3n-E2B-it-int4 \
  --prompt="What is the capital of France?"

# 运行带工具调用的示例
litert-lm run \
  --from-huggingface-repo=litert-community/gemma-4-E2B-it-litert-lm \
  gemma-4-E2B-it.litertlm \
  --prompt="What's the weather in Beijing?"
```

### 4.2 Android (Kotlin) 开发

**添加依赖**：

```kotlin
dependencies {
    implementation("com.google.ai.edge.litert:litert:0.10.1")
}
```

**基本用法**：

```kotlin
import com.google.ai.edge.litert.Model

// 加载模型
val model = Model.fromFile("gemma-3n-e2b-it.litertlm")

// 推理
val response = model.generate("What is the capital of France?")
println(response.text)
```

### 4.3 Python 开发

**安装**：

```bash
pip install litertlm
```

**基本用法**：

```python
from litertlm import Model

# 加载模型
model = Model.from_huggingface("google/gemma-3n-E2B-it-litert-lm")

# 推理
result = model.generate("What is the capital of France?")
print(result.text)
```

### 4.4 C++ 开发

**CMake 配置**：

```cmake
find_package(litert_lm REQUIRED)
target_link_libraries(your_app PRIVATE litert_lm::litert_lm)
```

**基本用法**：

```cpp
#include <litert_lm/litert_lm.h>

// 加载模型
auto model = litert_lm::Model::FromFile("gemma-3n-e2b-it.litertlm");

// 推理
litert_lm::GenerateOptions options;
options.prompt = "What is the capital of France?";
auto result = model->Generate(options);
std::cout << result.text << std::endl;
```

---

## 5. 工具调用（Function Calling）详解

### 5.1 什么是工具调用

工具调用允许 LLM 生成结构化的函数调用请求，而非自由文本输出。这使得 LLM 可以：

| 能力 | 说明 |
|------|------|
| **外部 API** | 查询天气、搜索网页、操作数据库 |
| **设备能力** | 发送消息、设置闹钟、控制智能家居 |
| **计算器** | 精确数学运算 |

### 5.2 定义工具

```kotlin
// 定义工具
val weatherTool = Tool(
    name = "get_weather",
    description = "Get current weather for a location",
    parameters = listOf(
        Parameter("location", Type.STRING, "City name")
    )
)

// 加载带工具的模型
val model = Model.fromFile("function-gemma.litertlm")
model.setTools(listOf(weatherTool))
```

### 5.3 调用工具

```kotlin
// 用户输入
val input = "What's the weather in Beijing?"

// 生成工具调用
val response = model.generate(input)

// 解析工具调用
if (response.hasToolCall()) {
    val toolCall = response.toolCall
    val args = toolCall.parseArguments()
    val weather = callWeatherAPI(args["location"])
    
    // 提交工具结果
    val finalResponse = model.submitToolResult(toolCall.id, weather)
    println(finalResponse.text)
}
```

### 5.4 Llguidance 约束

LiteRT-LM 支持 Llguidance 语法进行输出约束：

```kotlin
// 定义 Llguidance 约束
val grammar = """
    {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["search", "click", "scroll"]},
            "query": {"type": "string"}
        }
    }
""".trimIndent()

model.setGrammar(grammar)
```

---

## 6. 多模态能力

### 6.1 视觉输入

```kotlin
// 加载视觉模型
val model = Model.fromFile("gemma-4-vision.litertlm")

// 图片输入
val image = Image.fromFile("chart.png")
val response = model.generate(
    prompt = "Describe this chart",
    image = image
)
```

### 6.2 音频输入

```kotlin
// 加载音频模型
val model = Model.fromFile("gemma-3n-audio.litertlm")

// 音频输入
val audio = Audio.fromFile("speech.wav")
val response = model.generate(
    prompt = "Transcribe and translate this audio",
    audio = audio
)
```

---

## 7. 性能优化

### 7.1 量化支持

LiteRT-LM 支持多种量化精度：

| 精度 | 内存占用 | 性能 | 适用场景 |
|------|-----------|------|---------|
| **FP16** | 100% | 最优 | 桌面端、服务器 |
| **INT8** | 50% | 良好 | 移动端 |
| **INT4** | 25% | 较好 | 资源受限设备 |
| **INT2** | 12.5% | 可用 | 极致受限场景 |

### 7.2 KV Cache 量化

```kotlin
// 启用 KV Cache 量化
val options = LmOptions(
    kvCacheQuantization = KvCacheQuantization.INT8,
    kvCacheQuantizationThreshold = 0.8f
)
val model = Model.fromFile("model.litertlm", options)
```

### 7.3 批处理优化

```kotlin
// 批量推理
val prompts = listOf(
    "What is AI?",
    "What is ML?",
    "What is DL?"
)
val results = model.batchGenerate(prompts)
```

---

## 8. 平台特定配置

### 8.1 Android 配置

**AndroidManifest.xml**：

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
```

**GPU 加速**（通过 ML Pipeline）：

```kotlin
val options = LmOptions(
    runtime = Runtime.GPU,  // 使用 GPU 加速
    threads = 4
)
```

### 8.2 iOS 配置

**Swift Package Manager**：

```swift
dependencies: [
    .package(url: "https://github.com/google-ai-edge/LiteRT-LM.git", from: "0.10.0")
]
```

**Metal 加速**：

```swift
let options = LmOptions(
    runtime: .metal,
    gpuMemoryFraction: 0.8
)
```

### 8.3 树莓派配置

```bash
# 安装依赖
sudo apt-get install libopenblas-dev liblapack-dev

# 编译（使用 CMake）
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
make -j$(nproc)
```

---

## 9. 从源码构建

### 9.1 准备环境

```bash
# 安装 Bazelisk
npm install -g @bazel/bazelisk

# 克隆仓库
git clone https://github.com/google-ai-edge/LiteRT-LM.git
cd LiteRT-LM

# 查看可构建目标
bazel query //...
```

### 9.2 Android 构建

```bash
# 构建 AAR
bazel build //kotlin:litert-lm-aar

# 构建 APK 示例
bazel build //examples/android:llm-chat
```

### 9.3 C++ 库构建

```bash
# 使用 CMake
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release \
      -DLITERT_BUILD_TESTS=ON \
      ..
make -j$(nproc)
```

---

## 10. 与同类框架对比

### 10.1 对比 llama.cpp

| 维度 | LiteRT-LM | llama.cpp |
|------|-----------|------------|
| **定位** | Google 生产级 | 学术/民间 |
| **多平台** | Android/iOS/Web/IoT | 桌面端为主 |
| **工具调用** | 原生支持 | 需第三方扩展 |
| **Google 集成** | 深度集成 Gemma | 无 |
| **多模态** | 原生支持 | 有限 |

### 10.2 对比 MNN

| 维度 | LiteRT-LM | MNN |
|------|-----------|-----|
| **厂商支持** | Google 官方 | 阿里开源 |
| **移动端优化** | 深度优化 | 优秀 |
| **工具调用** | 原生支持 | 需扩展 |
| **开源生态** | 活跃 | 活跃 |

---

## 11. 常见问题

### Q: LiteRT-LM 和 LiteRT 是什么关系？

A: LiteRT-LM 是 LiteRT（Google 的移动端机器学习运行时）的 LLM 专用版本。LiteRT-LM 专注于语言模型的推理优化，而 LiteRT 是更通用的 ML 推理框架。

### Q: 支持中文模型吗？

A: 支持。Qwen、Phi 等主流开源中文模型都已通过测试。

### Q: iOS 版本什么时候发布？

A: Swift API 正在开发中（"🚀 In Dev"状态），预计近期发布。

### Q: 如何贡献代码？

A: 查看 CONTRIBUTING.md，提交 PR 后会经过 Google 团队的代码审查。

---

## 12. 总结

LiteRT-LM 代表了**边缘设备 LLM 推理**的最先进方案。它的关键价值在于：

**为什么选择 LiteRT-LM：**

| 优势 | 说明 |
|------|------|
| **Google 生产验证** | 已在 Chrome、Pixel Watch 等产品中大规模部署 |
| **全平台覆盖** | Android、iOS、Web、桌面端、IoT 一站式解决方案 |
| **工具调用原生支持** | 无需第三方扩展，原生 Function Calling |
| **多模态能力** | 视觉、音频多模态开箱即用 |
| **Gemma 深度优化** | Google 自家模型，性能最优 |

**适用场景：**

- 移动应用需要本地 LLM 能力
- 隐私敏感场景（数据不离设备）
- 离线 LLM 应用
- 边缘计算场景（IoT、嵌入式）

**不适用场景：**

- 超大模型（>70B）部署（内存受限）
- 需要最强推理性能（应使用云端）

LiteRT-LM 将成为移动和边缘设备上部署 LLM 的重要选择。

---

**附录：相关资源**

- GitHub 仓库：https://github.com/google-ai-edge/LiteRT-LM
- 产品官网：https://ai.google.dev/edge/litert-lm
- 技术概述：https://ai.google.dev/edge/litert-lm/overview
- CLI 指南：https://ai.google.dev/edge/litert-lm/cli
- Android 文档：https://ai.google.dev/edge/litert-lm/android
- Python 文档：https://ai.google.dev/edge/litert-lm/python
- C++ 文档：https://ai.google.dev/edge/litert-lm/cpp