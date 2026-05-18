---
title: "Supertonic 3: 99M参数本地多语言TTS引擎，完全基于ONNX实现端侧推理"
date: "2026-05-18T20:00:00+08:00"
slug: "supertonic-onnx-tts-engine-guide
description: "Supertonic是一款99M参数的本地多语言TTS引擎，基于ONNX Runtime实现纯端侧推理，支持31种语言和44.1kHz高保真音频输出。本文详解其核心能力、Python SDK快速上手及本地HTTP API部署方法。"
draft: false
categories: ["技术笔记"]
tags: ["TTS", "ONNX", "语音合成", "本地推理", "开源", "多语言"]
---

# Supertonic 3: 99M参数本地多语言TTS引擎，完全基于ONNX实现端侧推理

## 核心价值：纯端侧、隐私优先

Supertonic 3 是 Supertone 公司开源的**超高速本地多语言 TTS 引擎**，99M 参数，ONNX 格式，完全离线运行。与云端 TTS 服务相比，核心差异在于：

- **数据不出设备**：纯端侧推理，医疗、金融、客服等隐私敏感场景天然适用
- **零 API 调用成本**：不依赖任何云服务，无配额限制
- **31 种语言覆盖**：英语、中文、日语、韩语、阿拉伯语、德语、法语等主流语言开箱即用
- **44.1kHz 高保真音频**：输出质量对标商业级 TTS 服务
- **<laugh>、<breath>、<sigh> 表达标签**：插入自然韵律，让合成语音更真实

GitHub：[https://github.com/supertone-inc/supertonic](https://github.com/supertone-inc/supertonic)，HuggingFace 模型：[Supertone/supertonic-3](https://huggingface.co/Supertone/supertonic-3)。

---

## 快速上手：pip install，一行代码合成语音

### 安装

```bash
pip install supertonic
```

首次运行会自动从 Hugging Face 下载模型（约百MB），无需手动配置。

### Python 基本用法

```python
from supertonic import TTS

tts = TTS(model="supertonic-3")

# 基础合成
audio = tts.tts("你好，欢迎使用 Supertonic 3。")
tts.save(audio, "hello.wav")

# 使用表达标签增强自然度
audio = tts.tts("大家好<breath>，今天我们来聊一聊<laugh>最新的 AI 技术进展。")
tts.save(audio, "expressive.wav")
```

### 多语言示例

```python
tts = TTS(model="supertonic-3")

texts = {
    "英语": "Hello, this is a test of multilingual TTS.",
    "中文": "你好，这是一条中文测试语音。",
    "日语": "こんにちは、音声合成のテストです。",
    "韩语": "안녕하세요, 다국어 음성 합성 테스트입니다.",
    "阿拉伯语": "مرحبا، هذا اختبار للغة العربية.",
}

for lang, text in texts.items():
    audio = tts.tts(text)
    tts.save(audio, f"{lang}.wav")
```

---

## 本地 HTTP API 部署：supertonic serve

Python SDK v1.3.1 起内置了 `supertonic serve` 命令，一键启动本地 HTTP 服务，暴露 OpenAI 兼容接口，方便 AI Agent 和语音助手集成。

### 启动服务

```bash
supertonic serve
```

默认监听 `http://localhost:18792`，模型会在首次请求时自动下载。

### 接口一：/v1/tts（原生接口）

```bash
curl -X POST http://localhost:18792/v1/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，Supertonic。",
    "output_path": "output.wav"
  }' \
  --output output.wav
```

### 接口二：/v1/audio/speech（OpenAI 兼容）

与 OpenAI TTS API 完全兼容，现有应用无缝切换：

```bash
curl -X POST http://localhost:18792/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "supertonic-3",
    "input": "你好，Supertonic。",
    "voice": "default"
  }' \
  --output output.wav
```

Python SDK 调用方式：

```python
import requests

response = requests.post(
    "http://localhost:18792/v1/audio/speech",
    json={
        "model": "supertonic-3",
        "input": "你好，欢迎使用 Supertonic 3。",
        "voice": "default"
    }
)

with open("output.wav", "wb") as f:
    f.write(response.content)
```

---

## 多 Runtime SDK 矩阵

除了 Python，Supertonic 还提供多语言 SDK，覆盖从生产环境到嵌入式的各种场景：

| SDK | 命令 | 适用场景 |
|-----|------|---------|
| Python | `pip install supertonic` | AI Agent、云服务、脚本 |
| Node.js | `npm install supertonic` | Web 应用、后端服务 |
| Browser (WebGPU) | CDN 引入 | 纯前端语音合成 |
| Java | Maven/Gradle | 企业级 Java 应用 |
| C++ | CMake 集成 | 高性能实时系统 |
| C# | NuGet | .NET 生态 |
| Go | go get | 微服务 / 云原生 |
| Swift / iOS | CocoaPods/SPM | iOS/macOS 原生应用 |
| Rust | Cargo | 嵌入式 / 高性能场景 |
| Flutter | pub dev | 跨平台移动应用 |

---

## Voice Builder：创建自定义音色

Supertonic 提供 **Voice Builder** 功能，允许用户通过少量语音样本创建**永久自定义音色**，无需 Fine-tuning，适合品牌声音定制和个性化场景。

具体步骤需参考官方文档（仓库 README），核心流程：

1. 准备一段目标音色的参考音频（短则几十秒）
2. 通过 Voice Builder API 注册音色 profile
3. 合成时指定音色 ID，即可生成个性化语音

---

## 适用边界

### 适合的场景

- **隐私敏感行业**：医疗记录、金融客服、法律咨询，数据不离设备
- **AI Agent / Assistant 集成**：作为语音输出层，配合 ASR 实现端到端语音对话
- **嵌入式 / 边缘设备**：树莓派、Jetson Nano 等 ARM 设备上的离线语音助手
- **多语言内容生成**：电子书朗读、教育内容多语言配音

### 不适合的场景

- 超长文本（>5分钟）的广播级音质需求，当前版本更适合短句实时合成
- 需要精细情感控制的角色扮演场景，表达标签支持有限
- 无 GPU 的极低端设备（如老旧手机）上追求低延迟

---

## 总结

Supertonic 3 的核心定位是**端侧多语言 TTS 基础设施**：

- **纯本地**：ONNX Runtime 驱动，无云依赖，数据完全私有
- **高性能**：99M 参数 + 流式推理，44.1kHz 输出，适合实时场景
- **开箱即用**：pip install + supertonic serve，两条命令完成部署
- **多语言**：31 种语言 + 表达标签，覆盖大多数语音合成需求
- **多 SDK**：从 Python 到 Swift，从浏览器到嵌入式，覆盖全平台

AI Agent 大爆发时代，本地 TTS 是语音交互层的关键基础设施，Supertonic 3 是目前开源生态中技术参数最扎实、平台覆盖最全面的选择之一。

**相关链接：**

- GitHub：https://github.com/supertone-inc/supertonic
- HuggingFace：https://huggingface.co/Supertone/supertonic-3
- PyPI：https://pypi.org/project/supertonic/