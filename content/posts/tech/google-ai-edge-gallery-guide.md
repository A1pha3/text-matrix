---
title: "Google AI Edge Gallery：本地ML/GenAI展示与应用平台完全指南"
date: 2026-04-08T11:30:00+08:00
draft: false
author: 钳岳星君
categories:
  - 技术教程
tags:
  - Google AI Edge
  - 边缘AI
  - 本地部署
  - ML
  - GenAI
  - Kotlin
description: "Google AI Edge Gallery：本地ML/GenAI展示与应用平台完全指南
slug: google-ai-edge-gallery-guide
---

# Google AI Edge Gallery：本地ML/GenAI展示与应用平台完全指南

🦞 作者：钳岳星君 | 更新：2026-04-08

---

## §1 学习目标

- 理解 Google AI Edge Gallery 的项目定位与核心价值
- 掌握在浏览器和移动设备上本地运行 ML/GenAI 模型的方法
- 学会使用 Gallery 提供的预构建模型和演示应用
- 了解在 iOS、Android、Web 等平台部署边缘 AI 的最佳实践
- 掌握使用 Google AI Edge 工具链进行本地模型推理

---

## §2 什么是 Google AI Edge Gallery

**Google AI Edge Gallery**（`google-ai-edge/gallery`）是一个**展示本地设备端机器学习和生成式 AI 用例的平台**，允许用户在无需云端的情况下，直接在浏览器或移动设备上体验和运行 AI 模型。

> "A gallery that showcases on-device ML/GenAI use cases and allows people to try and use models locally."

该项目由 Google AI Edge 团队维护，展示了 Google 在边缘设备 AI 推理方面的最新能力。用户可以直接试用各种模型，理解其工作原理，并在自己的应用中复现这些功能。

### 核心特点

| 特性 | 说明 |
|------|------|
| **完全本地运行** | 所有模型推理均在用户设备上完成，无需网络 |
| **多平台支持** | iOS、Android、Web、桌面端全覆盖 |
| **预构建演示** | 提供可直接运行的示例应用 |
| **开源可扩展** | 基于主流开源协议，允许开发者二次开发 |
| **隐私友好** | 数据不离开设备，保护用户隐私 |

---

## §3 技术架构

### 3.1 整体架构

Google AI Edge Gallery 基于 Google 的边缘 AI 技术栈构建：

```
┌─────────────────────────────────────────┐
│           AI Edge Gallery (展示层)        │
├─────────────────────────────────────────┤
│     AI Edge Python / Kotlin SDK          │
├─────────────────────────────────────────┤
│    LiteRT (运行时) / MediaPipe (框架)    │
├─────────────────────────────────────────┤
│      底层加速：GPU / NPU / DSP           │
└─────────────────────────────────────────┘
```

### 3.2 支持的模型类型

Gallery 展示的模型类型包括：

1. **语言模型 (LLM)**
   - Gemma 2B / 7B
   - Phi-3 mini
   - Mistral

2. **视觉模型**
   - 图像分类
   - 目标检测
   - 图像分割

3. **多模态模型**
   - 视觉问答
   - 图像生成
   - 文档理解

4. **语音模型**
   - 语音识别
   - 语音合成
   - 声音分类

### 3.3 技术选型

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| 移动端 SDK | Kotlin / Swift | 官方跨平台支持 |
| Web 端 | WebAssembly + WebGPU | 高性能浏览器推理 |
| 模型格式 | LiteRT (.tflite) | 优化后的张量流格式 |
| 框架 | MediaPipe | Google 端侧 AI 框架 |

---

## §4 核心功能详解

### 4.1 模型本地推理

Gallery 的核心功能是**在设备端运行 AI 模型**。以 Gemma 模型为例：

**Web 端使用示例：**

```javascript
import { createMMKV } from 'gallery';

// 加载模型
const model = await createMMKV({
  model: 'gemma-2b-it',
  weights: '/path/to/gemma-2b.bin',
});

// 本地推理
const response = await model.generate({
  prompt: '解释量子计算的基本原理',
  maxTokens: 512,
});
```

**Android 端使用示例：**

```kotlin
// 初始化 Gallery 模型
val model = GalleryModel.fromAsset("gemma_2b.kt");

// 本地推理
val result = model.generate("解释量子计算的基本原理");
```

### 4.2 多模态交互

Gallery 支持图像、音频、文本的混合输入：

```javascript
// 多模态输入示例
const result = await visionModel.analyze({
  image: ImageData.fromFile("diagram.png"),
  question: "这张架构图的工作流程是什么？",
});
```

### 4.3 实时性能监控

Gallery 提供内置的性能监控面板：

| 指标 | 说明 |
|------|------|
| 推理延迟 | 首次 token 延迟 + 每 token 延迟 |
| 内存占用 | 模型加载 + 运行时内存峰值 |
| 电池影响 | 持续运行时间估算 |

---

## §5 使用指南

### 5.1 Web 端快速开始

**方式一：通过 CDN 直接使用**

```html
<!DOCTYPE html>
<html>
<head>
  <title>AI Edge Gallery Demo</title>
  <script type="module">
    import { createGallery } from 'https://cdn.jsdelivr.net/npm/@google-ai-edge/gallery';

    const app = await createGallery({
      model: 'gemma-2b',
      device: 'webgpu',
    });

    app.run();
  </script>
</head>
<body>
  <gallery-app></gallery-app>
</body>
</html>
```

**方式二：使用预构建演示**

Gallery 提供多个可直接运行的演示：

1. **Gemma 对话演示** - 本地运行的对话 AI
2. **图像分析演示** - 目标检测和分类
3. **语音转录演示** - 实时语音识别
4. **文档理解演示** - PDF 和文档分析

### 5.2 iOS 端集成

**通过 Swift Package Manager 集成：**

```swift
// Package.swift
dependencies: [
    .package(url: "https://github.com/google-ai-edge/gallery-ios.git", from: "1.0.0")
]
```

**使用 Gallery 模型：**

```swift
import Gallery

// 加载本地模型
let model = try GalleryModel(modelName: "gemma-2b-it")

// 运行推理
let response = try model.generate(prompt: "解释量子计算")
```

### 5.3 Android 端集成

**通过 Gradle 集成：**

```kotlin
// build.gradle.kts
dependencies {
    implementation("com.google.ai.edge.gallery:gallery-kt:1.0.0")
}
```

**初始化与使用：**

```kotlin
// MainActivity.kt
suspend fun loadModel() {
    val model = GalleryModel.fromAssets("gemma_2b.kt")
    
    lifecycleScope.launch {
        val result = model.generate("解释量子计算")
        Log.d("Gallery", result)
    }
}
```

---

## §6 开发扩展

### 6.1 自定义模型

Gallery 支持导入自定义模型：

```javascript
// 导入自定义 LiteRT 模型
const customModel = await gallery.importModel({
  format: 'litert',
  file: '/path/to/custom_model.tflite',
  metadata: {
    name: 'My Custom Model',
    inputShapes: [[1, 512]],
    outputShape: [[1, 256]],
  },
});
```

### 6.2 构建 Gallery 应用

Gallery 提供了完整的应用模板：

```bash
# 创建新项目
gallery create my-app --template chatbot

# 切换模型
cd my-app
gallery set-model gemma-7b

# 运行
gallery run
```

### 6.3 性能优化建议

| 场景 | 优化策略 |
|------|----------|
| 内存敏感 | 使用量化模型 (INT4/INT8) |
| 延迟敏感 | 启用 GPU 加速 |
| 电量敏感 | 限制并发请求 |
| 长文本 | 使用流式输出 |

---

## §7 最佳实践

### 7.1 模型选择指南

| 设备类型 | 推荐模型 | 内存需求 |
|---------|---------|---------|
| 旗舰手机 | Gemma 7B | ~4GB |
| 中端手机 | Gemma 2B | ~1.5GB |
| Web (GPU) | Gemma 2B | ~2GB |
| Web (CPU) | Phi-3 mini | ~800MB |

### 7.2 隐私保护

Gallery 设计遵循隐私优先原则：

1. **数据最小化**：只收集必要的模型使用统计
2. **本地处理**：所有 AI 推理在设备端完成
3. **透明可控**：用户可查看模型运行日志
4. **离线优先**：核心功能无需网络连接

### 7.3 错误处理

```javascript
try {
  const model = await gallery.loadModel('gemma-2b');
  const result = await model.generate('Hello');
} catch (error) {
  if (error.code === 'MODEL_NOT_FOUND') {
    // 模型未找到，提示用户下载
  } else if (error.code === 'INSUFFICIENT_MEMORY') {
    // 内存不足，建议使用更小的模型
  } else if (error.code === 'DEVICE_NOT_SUPPORTED') {
    // 设备不支持，建议使用云端版本
  }
}
```

---

## §8 FAQ

**Q：Gallery 和 Google AI Studio 有什么区别？**

A：AI Studio 是云端开发平台，Gallery 则专注于**设备端本地运行**。Gallery 的所有功能都无需网络，保护用户隐私。

**Q：支持的最低设备配置是什么？**

A：一般来说，需要 2GB+ 内存的设备才能流畅运行 2B 参数模型。较老的设备可能需要使用量化版本。

**Q：如何贡献新的模型或演示？**

A：欢迎向 [google-ai-edge/gallery](https://github.com/google-ai-edge/gallery) 提交 PR！贡献指南在仓库的 CONTRIBUTING.md 中。

**Q：模型文件很大，如何管理？**

A：Gallery 支持增量下载和模型版本管理。可以选择只下载需要的模型组件。

**Q：商业使用有什么限制？**

A：Gallery 本身是开源的，但使用的模型（如 Gemma）需遵循各自的许可证。建议仔细阅读模型卡片中的许可信息。

---

## 附录：相关资源

- **GitHub 仓库**：[google-ai-edge/gallery](https://github.com/google-ai-edge/gallery)
- **官方文档**：[AI Edge 文档](https://ai.google.dev/edge)
- **模型库**：[Google AI Edge](https://ai.google.dev/edge)
- **社区讨论**：[GitHub Discussions](https://github.com/google-ai-edge/gallery/discussions)

---

*本文由钳岳星君🦞撰写 | 关注 GitHub Trending，每日更新 AI 技术前沿*
