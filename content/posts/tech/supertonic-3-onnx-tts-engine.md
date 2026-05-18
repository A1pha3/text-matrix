---
title: "Supertonic 3：99M参数本地运行的多语言TTS引擎（31语言，WebGPU）"
date: 2026-05-18
tags: ["TTS", "语音合成", "开源", "ONNX", "WebGPU", "本地部署"]
categories: ["AI模型"]
---

# Supertonic 3：99M参数本地运行的多语言TTS引擎

**Supertonic** 是一个极速本地多语言文字转语音系统，基于 ONNX Runtime 在设备端运行，无需网络、无需 API 调用、隐私完全保障。Supertonic 3 版本支持 31 种语言，约 99M 参数（约 0.1B），输出 44.1kHz 高质量音频。

<!-- more -->

## 核心特性

- ⚡ **极速合成** — 桌面端可在 1 秒内将整页网页转为音频
- 🌍 **31 语言支持** — 阿拉伯语、保加利亚语、中文、克罗地亚语、捷克语、丹麦语、荷兰语、英语、爱沙尼亚语、芬兰语、法语、德语、希腊语、印地语、匈牙利语、印尼语、意大利语、日语、韩语、拉脱维亚语、立陶宛语、波兰语、葡萄牙语、罗马尼亚语、俄语、斯洛伐克语、斯洛文尼亚语、西班牙语、瑞典语、土耳其语、乌克兰语、越南语
- 🪶 **99M 参数** — 远小于 0.7B–2B 级别的开源 TTS 系统，冷启动快，内存占用低
- 📱 **边缘设备支持** — 树莓派、e-reader 等无 GPU 设备也能运行
- 🔊 **44.1kHz 高质量音频** — 直接输出无需升采样
- 🎭 **10 种 Expression Tags** — `<laugh>`、`<breath>`、`<sigh>` 等自然表达标签，无需 prompt 工程
- 🛠️ **多运行时 SDK** — Python、Node.js、Browser (WebGPU)、Java、C++、C#、Go、Swift、iOS、Rust、Flutter

## Supertonic 3 vs 前代

| 特性 | Supertonic 3 | Supertonic 2 | Supertonic 1 |
|---|:---:|:---:|:---:|
| 参数规模 | ~99M | ~66M | ~66M |
| 语言数 | 31 | 5 | 1 (英语) |
| Expression Tags | ✅ 10种 | ❌ | ❌ |

## 快速开始

```bash
pip install supertonic
```

```python
from supertonic import TTS

tts = TTS(auto_download=True)  # 首次运行自动下载模型
style = tts.get_voice_style(voice_name="M1")
wav, duration = tts.synthesize(
    text="Hello, this is Supertonic TTS.",
    lang="en",
    voice_style=style,
    total_steps=8,  # 质量: 5(低) 到 12(高)，默认8
    speed=1.05,    # 速度: 0.7 到 2.0
)
# wav: numpy array (1, num_samples,) float32 @ 44100 Hz
```

## 本地 HTTP 服务器（v1.3.1 新增）

```bash
supertonic serve
```

- `/v1/tts` — 原始 TTS 接口
- `/v1/audio/speech` — OpenAI 兼容接口

## 学术支撑

Supertonic 基于三篇论文：
- **SupertonicTTS** (arXiv:2503.23108) — 主架构
- **LARoPE** (arXiv:2509.11084) — Length-Aware RoPE 文本-语音对齐
- **Self-Purifying Flow Matching** (arXiv:2509.19091) — 噪声标签训练

## 许可

- 代码: MIT License
- 模型权重: OpenRAIL-M License

- GitHub: https://github.com/supertone-inc/supertonic
- Hugging Face: https://huggingface.co/Supertone/supertonic-3
- Demo: https://supertonic3.github.io/