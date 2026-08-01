---
title: "Voice-Pro：把 YouTube 配音流程做到一键化的 AI 语音工作台"
date: 2026-08-02T02:59:48+08:00
slug: "abus-aikorea-voice-pro-ai-voice-dubbing-workbench"
description: "Voice-Pro（abus-aikorea/voice-pro）是一个集成 Whisper/Faster-Whisper 语音识别、yt-dlp 视频下载、F5-TTS/E2-TTS/CosyVoice 声音克隆、Edge-TTS/kokoro 多语种 TTS、Deep-Translator 翻译与 Demucs/MDX-Net 人声分离的 Gradio 工作台，被定位为 ElevenLabs 的开源替代。"
draft: false
categories: ["技术笔记"]
tags: ["AI 语音", "Whisper", "F5-TTS", "CosyVoice", "Edge-TTS", "ElevenLabs 替代"]
---

## 一句话判断

`abus-aikorea/voice-pro` 是一个把"下载 → 人声分离 → 语音识别 → 翻译 → 多语种配音 → 字幕合并"全部串成一条流水线的本地 Gradio 应用；它本身不发明模型，而是把 Whisper/Faster-Whisper、yt-dlp、F5-TTS/E2-TTS/CosyVoice、Edge-TTS/kokoro、Deep-Translator 等开源 TTS/ASR 工具按真实配音工序粘合成可一键运行的 GUI，被作者明确标榜为 ElevenLabs 的本地化替代。

## 项目定位

README 顶部把 Voice-Pro 定义为 "AI-powered web application for speech recognition, translation, and dubbing"，技术栈列表直接写在 HTML 注释里：

```
Whisper、Faster-Whisper、Whisper-Timestamped、Edge-TTS、Gradio、CUDA、F5-TTS、E2-TTS、
CosyVoice、kokoro、yt-dlp、Demucs、MDX-Net、Deep-Translator、uv
```

围绕这条主线，工作台被划分成 6 个高频模块：

| 模块 | 关键依赖 | 角色 |
|------|---------|------|
| YouTube 下载 | yt-dlp | 拉取音视频源 |
| 人声分离 | Demucs、MDX-Net | 把 BGM 和人声拆开 |
| 语音识别 | Whisper、Faster-Whisper、Whisper-Timestamped | 出字幕时间戳 |
| 翻译 | Deep-Translator（默认）+ Azure Translator（BYOK） | 100+ 语言 |
| 多语种 TTS | F5-TTS、E2-TTS、CosyVoice（含 Fun-CosyVoice3-0.5B）、Edge-TTS、kokoro | 配音 |
| WebUI | Gradio 6.20 | 整合界面 |

按作者的说法，这是 **ElevenLabs 的开源本地替代**。

## v4.0：放弃 Miniconda，投向 uv

最近一个值得专门记录的版本是 4.0。v4.0 的核心改动是 **安装器从 Miniconda/pip 整体迁移到 [uv](https://docs.astral.sh/uv/)**，并锁入 `uv.lock`。这意味着：

1. **依赖完全可复现** —— `uv sync` 后拿到的就是仓库作者锁定的同一组包
2. **安装耗时大幅缩短** —— `start.bat` 一次性下载 uv + Python + 全部依赖
3. **不需要管理员权限** —— `installer_files/` 目录下跑完整流程，Restricted/Corporate PC 也能装
4. **CUDA Toolkit 不再必须** —— 所有依赖都带预编译 wheel，PyTorch 自带 CUDA runtime

这一节看着像常规升级，对实际使用的影响是"干净重装只用几分钟"：README 给的故障恢复建议就是"删除 `installer_files/` 后再 `start.bat`"，已下载的模型放在 `model/` 不丢。

## 栈的最新状态（v4.0）

- Python 3.12 + Torch 2.8.0+cu128（RTX 50 系列已支持）
- ASR：faster-whisper 1.2.1（large-v3-turbo、distil-large-v3.5）、openai-whisper 20250625、whisper-timestamped 1.15.9
- TTS：F5-TTS 1.1.21、kokoro 0.9.4、edge-tts 7.x、re-vendored CosyVoice（upstream main）
- 新增可选模型：**Fun-CosyVoice3-0.5B**，9 种语言（首次启用时下载）
- whisperX 被移除（依赖锁与 Gradio 6 不兼容，原配置自动 fallback 到 faster-whisper）

## 一次完整配音流程

把"YouTube 一段英文科普视频 → 中英双语字幕 + 韩语配音"当成端到端样本：

1. **下载**：`YouTube URL` 走 yt-dlp 拉取 mp4 + 自动音轨
2. **人声分离**：Demucs 把 vocals 与 accompaniment 拆开，方便后续只对人声做 ASR 与配音
3. **识别 + 字幕**：Faster-Whisper large-v3-turbo 输出带时间戳的 SRT
4. **翻译**：Deep-Translator 把每行字幕翻译成目标语言（中文/韩文/日文等），Azure 用户可切 BYOK
5. **配音**：选择 F5-TTS 或 CosyVoice（韩语推荐 Fun-CosyVoice3-0.5B），按字幕时间戳逐句合成
6. **合并**：把合成音轨与原视频时间轴对齐，输出最终 mp4

整条流水线全部在本地 Gradio 页面上点完，不需要写一行 Python。

## 适用边界与不适用边界

**适用**：

- 已经有 NVIDIA GPU + Windows 工作站，想做 YouTube/播客的多语种搬运或本地化配音
- 想要 ElevenLabs 的能力但不放心把素材/声音样本传到云端的团队
- 已经习惯 Faster-Whisper、F5-TTS 这套开源工具栈，需要一个统一面板的人

**不适用**：

- 没有 NVIDIA GPU：README 明确说 Windows + NVIDIA GPU 是被验证的组合，Mac/Linux 没有跑过
- 期待实时直播配音：当前架构是离线流水线，不针对延迟优化
- 期待它做"声音版权清理 / 克隆授权审计"：这部分始终在调用方自己的合规边界

## 与 ElevenLabs 的实际差异

| 维度 | ElevenLabs | Voice-Pro |
|------|-----------|-----------|
| 部署 | SaaS（也提供本地） | 完全本地 Gradio |
| TTS 模型 | 自家 Multilingual v2 / Turbo 等 | F5-TTS / E2-TTS / CosyVoice / Edge-TTS / kokoro 多选 |
| 克隆授权 | 自家合规 | 取决于你选哪个模型 |
| 翻译 | 与自家 voice 协同 | Deep-Translator（默认免费） + Azure（BYOK） |
| UI 形态 | 官方 Web | 本地 Gradio 6.20 |
| 适合"做完整 YouTube 搬运" | 需要外部脚本 | 一站式 |

Voice-Pro 适合"我希望今天晚上就能把这条英文视频压成中韩双语 + 韩语配音"的场景；它不适合"我要做一个 ToC SaaS 配音产品并提供 SLA"——但那种场景 ElevenLabs 也只是其中一环。