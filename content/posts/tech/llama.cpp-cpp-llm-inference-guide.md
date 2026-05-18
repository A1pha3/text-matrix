---
title: llama.cpp - 纯C/C++实现的高效LLM推理引擎
date: 2026-05-18
tags:
  - LLM推理
  - 本地AI
  - 开源
  - 量化
  - GGUF
---

# llama.cpp：纯C/C++实现的高性能LLM推理引擎

**Stars: 110,785** | **今日: +18,344** | **C++**

GitHub: [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp)

## 一句话评价

llama.cpp 是用纯 C/C++ 重写 LLaMA 推理的项目，如今已成为本地 LLM 推理的事实标准，支持 1.5bit~8bit 量化、Apple Silicon 硬件加速、CUDA/ROCm/Vulkan 多后端，无需任何依赖即可在任意设备运行百亿参数模型。

## 核心特性

### 极致轻量与便携
- **零依赖**：纯 C/C++，无外部库依赖，单文件编译
- **跨平台**：支持 macOS (NEON/Accelerate/Metal)、Linux (AVX/AVX2/AVX512/AMX)、Windows (CUDA)、RISC-V
- **多硬件后端**：CUDA、AMD ROCm、摩尔线程 MUSA、Vulkan、Sycl、CPU+GPU 混合推理

### 量化支持
支持 1.5bit / 2bit / 3bit / 4bit / 5bit / 6bit / 8bit 量化，大幅降低显存占用同时保持模型质量。GGUF 格式已成为 Hugging Face 的标准模型格式。

### 多模态与工具链
- `llama-server` 提供 OpenAI 兼容 API，支持多模态输入（图生文）
- `llama-cli` 命令行直接运行模型
- VS Code 插件（代码补全）、Vim/Neovim 插件（FIM）
- Hugging Face Inference Endpoints 原生支持 GGUF

### 模型支持
支持 LLaMA 全系列、Mistral、Mixtral MoE、Falcon、Bloom、Yi、Baichuan、Qwen、Phi、Gemma 等几乎所有主流开源模型。

## 快速上手

```bash
# 安装（macOS）
brew install llama.cpp

# 直接运行 Hugging Face 模型
llama-cli -hf ggml-org/gemma-3-1b-it-GGUF

# 启动 OpenAI 兼容 API 服务
llama-server -hf ggml-org/gemma-3-1b-it-GGUF
```

```bash
# 使用本地模型文件
llama-cli -m my_model.gguf

# 量化自己的模型
llama-quantize my_model.gguf my_model-q4_k_m.gguf Q4_K_M
```

## 技术亮点

**Apple Silicon 原生优化**：利用 ARM NEON、Accelerate 框架和 Metal GPU 加速，在 M 系列芯片上效率极高。

**自定义 CUDA 内核**：NVIDIA GPU 专用优化，同时通过 HIP 支持 AMD GPU。

**Hugging Face 缓存迁移**：新版本模型统一存储在标准 HF 缓存目录，与其他 HF 工具完全共享。

## 适用场景

- 本地部署开源大模型（隐私敏感场景）
- 低配置机器运行大模型（量化压缩）
- 嵌入式 / 边缘设备 AI 推理
- 作为服务端的高性能推理（llama-server）
- AI 代码补全插件后端

## 为什么值得关注

llama.cpp 将曾经"需要高端 GPU 才能跑"的开源模型，变成了任何设备都能运行的工具。它的存在让本地 AI 推理真正普及，也催生了大量基于 GGUF 的应用生态（如 Ollama、Jan、LM Studio 等）。110k Stars、18k 今日增长说明了社区对其稳定性和实用性的持续认可。