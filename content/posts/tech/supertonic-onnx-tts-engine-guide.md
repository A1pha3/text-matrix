---
title: "Supertonic 3: 99M参数本地多语言TTS引擎，完全基于ONNX实现端侧推理"
date: "2026-05-18T20:00:00+08:00"
slug: "supertonic-onnx-tts-engine-guide"
aliases:
  - "/posts/tech/supertonic-3-onnx-tts-engine/"
  - "/posts/tech/supertonic-on-device-multilingual-tts/"
description: "Supertonic是一款99M参数的本地多语言TTS引擎，基于ONNX Runtime实现纯端侧推理，支持31种语言和44.1kHz高保真音频输出。本文详解其核心能力、Python SDK快速上手及本地HTTP API部署方法。"
draft: false
categories: ["技术笔记"]
tags: ["TTS", "ONNX", "语音合成", "本地推理", "开源", "多语言"]
---

# Supertonic 3: 99M 参数本地多语言 TTS 引擎，完全基于 ONNX 实现端侧推理

## 快速信息卡

| 指标 | 数值 |
|------|------|
| 仓库 | [supertone-inc/supertonic](https://github.com/supertone-inc/supertonic) |
| Stars | 12,712+ |
| Forks | 1,305+ |
| License | MIT |
| 主要语言 | Swift（核心引擎）+ Python（SDK） |
| 参数规模 | 99M |
| 支持语言 | 31 种 |
| 音频质量 | 44.1kHz |

## 学习目标

读完本文后，你应该能够：

- 理解 Supertonic 3 的核心价值：纯端侧推理、隐私优先、零 API 成本
- 掌握 Python SDK 的基本用法：安装、基础合成、多语言合成、表达标签
- 部署本地 HTTP API（supertonic serve）并提供 OpenAI 兼容接口
- 了解多 Runtime SDK 矩阵，选择适合你场景的集成方式
- 判断 Supertonic 是否适合你的项目（适用边界）

## 目录

- [快速信息卡](#快速信息卡)
- [学习目标](#学习目标)
- [关键价值：纯端侧、隐私优先](#关键价值纯端侧隐私优先)
- [快速上手：pip install，一行代码合成语音](#快速上手pip-install一行代码合成语音)
- [本地 HTTP API 部署：supertonic serve](#本地-http-api-部署supertonic-serve)
- [多 Runtime SDK 矩阵](#多-runtime-sdk-矩阵)
- [Voice Builder：创建自定义音色](#voice-builder创建自定义音色)
- [适用边界](#适用边界)
- [FAQ](#faq)
- [自测题](#自测题)
- [进阶路径](#进阶路径)
- [总结](#总结)

---

## 关键价值：纯端侧、隐私优先

Supertonic 3 是 Supertone 公司开源的**超高速本地多语言 TTS 引擎**，99M 参数，ONNX 格式，完全离线运行。与云端 TTS 服务相比，核心差异在于：

- **数据不出设备**：纯端侧推理，医疗、金融、客服等隐私敏感场景天然适用
- **零 API 调用成本**：不依赖任何云服务，无配额限制
- **31 种语言覆盖**：英语、中文、日语、韩语、阿拉伯语、德语、法语等主流语言开箱即用
- **44.1kHz 高保真音频**：输出质量对标商业级 TTS 服务
- **&lt;laugh&gt;、&lt;breath&gt;、&lt;sigh&gt; 表达标签**：插入自然韵律，让合成语音更真实

GitHub：[https://github.com/supertone-inc/supertonic](https://github.com/supertone-inc/supertonic)，HuggingFace 模型：[Supertone/supertonic-3](https://huggingface.co/Supertone/supertonic-3)。

---

## 快速上手：pip install，一行代码合成语音

### 安装

```bash
pip install supertonic
```

首次运行会自动从 Hugging Face 下载模型（约百 MB），无需手动配置。

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

- 超长文本（>5 分钟）的广播级音质需求，当前版本更适合短句实时合成
- 需要精细情感控制的角色扮演场景，表达标签支持有限
- 无 GPU 的极低端设备（如老旧手机）上追求低延迟

---

## FAQ

**Q1：Supertonic 支持哪些语言？中文效果如何？**

支持 31 种语言，包括中文、英文、日语、韩语、阿拉伯语、德语、法语等。中文合成效果自然，支持表达标签（`<breath>`、`<laugh>`、`<sigh>`）增强真实感。

**Q2：supertonic serve 的默认端口是多少？如何修改？**

默认端口是 `18792`。修改方式是在启动时指定 `--port` 参数：`supertonic serve --port 8080`。

**Q3：Supertonic 支持流式输出吗？**

支持。Python SDK 的 `tts.tts_stream()` 方法可以流式返回音频数据，适合实时语音对话场景。

**Q4：Voice Builder 需要多少参考音频？**

官方建议至少 30 秒的清晰参考音频。音频质量越高，生成的自定义音色越接近目标声音。

**Q5：Supertonic 能在生产环境使用吗？**

可以。Supertonic 3 已经相对稳定，且 MIT 许可证允许商用。但建议先在小规模场景验证，确保满足你的延迟和音质要求。

---

## 自测题

**问题 1**：Supertonic 的核心价值是什么？与云端 TTS 服务相比有哪些优势？

<details>
<summary>参考答案</summary>
核心价值：纯端侧推理、隐私优先、零 API 成本。优势：数据不出设备、无配额限制、31 种语言支持、44.1kHz 高保真输出。
</details>

**问题 2**：如何启动本地 HTTP API 服务？OpenAI 兼容接口的端点是哪个？

<details>
<summary>参考答案</summary>
运行 `supertonic serve` 启动服务，默认监听 `http://localhost:18792`。OpenAI 兼容接口：`/v1/audio/speech`。
</details>

**问题 3**：表达标签有哪些？如何使用？

<details>
<summary>参考答案</summary>
支持 `<laugh>`（笑声）、`<breath>`（呼吸）、`<sigh>`（叹气）。用法：在文本中直接插入，如 `"大家好<breath>，今天我们来聊一聊<laugh>"`。
</details>

**问题 4**：Supertonic 支持哪些 Runtime SDK？列举至少 5 个。

<details>
<summary>参考答案</summary>
Python、Node.js、Browser (WebGPU)、Java、C++、C#、Go、Swift/iOS、Rust、Flutter。
</details>

**问题 5**：什么场景下不适合使用 Supertonic？

<details>
<summary>参考答案</summary>
超长文本（>5 分钟）的广播级音质需求、需要精细情感控制的角色扮演场景、无 GPU 的极低端设备上追求低延迟。
</details>

---

## 进阶路径

### 阶段 1：基础集成（1-2 周）

- [ ] 安装 Supertonic Python SDK，运行官方示例
- [ ] 部署本地 HTTP API（supertonic serve）
- [ ] 集成到现有 AI Agent 或 Assistant 项目
- [ ] 测试 31 种语言的合成效果

### 阶段 2：生产优化（2-4 周）

- [ ] 配置 GPU 加速（如果有 NVIDIA GPU）
- [ ] 优化音频后处理（降噪、音量归一化）
- [ ] 实现缓存机制（相同文本不重复合成）
- [ ] 监控服务性能和可用性

### 阶段 3：高级功能（1-2 个月）

- [ ] 使用 Voice Builder 创建自定义音色
- [ ] 集成到多模态 Agent（配合 ASR、LLM）
- [ ] 优化延迟（流式输出、批处理）
- [ ] 贡献代码或插件到社区

### 阶段 4：生态贡献（持续优化）

- [ ] 修复 Bug 或提交 Feature Request
- [ ] 编写插件或扩展（WASM 插件）
- [ ] 分享最佳实践（博客、会议演讲）
- [ ] 参与社区讨论（Discord、GitHub Discussions）

**进阶资源**：

- 官方文档：https://supertone.github.io/supertonic/
- HuggingFace 模型：https://huggingface.co/Supertone/supertonic-3
- 示例代码：https://github.com/supertone-inc/supertonic/tree/main/examples
- Discord 社区：https://discord.gg/supertone

---

## 总结

Supertonic 3 做的事情很简单：把 TTS 引擎做成 99M 的 ONNX 模型，塞进设备本地跑，不连云、不掏钱、不挑语言。31 种语言、44.1kHz 输出、`<laugh>` `<breath>` 表达标签——这些参数在 2026 年的开源 TTS 里算扎实的。

但它是不是你的唯一选择，取决于场景：

- 做 AI Agent 的语音输出层，或者医疗/金融这种数据不能出设备的场景 → 选它。
- 要广播级音质、超长文本合成 → 还是得用云端商业服务（Azure TTS、Google Cloud TTS）。
- 要精细情感控制的角色扮演 → 表达标签目前支持有限，得等后续版本或者自己训练。

部署只要两条命令：`pip install supertonic` + `supertonic serve`。OpenAI 兼容接口让现有应用几乎不用改代码。多 Runtime SDK 覆盖从 Python 到 Swift，从浏览器到嵌入式——集成成本不高。

GitHub: https://github.com/supertone-inc/supertonic（12,712+ ⭐）
HuggingFace: https://huggingface.co/Supertone/supertonic-3
PyPI: https://pypi.org/project/supertonic/