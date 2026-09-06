---
title: "Voice-Pro：跑在本地 Gradio 里的 YouTube 配音流水线"
date: "2026-08-02T02:59:48+08:00"
slug: "abus-aikorea-voice-pro-ai-voice-dubbing-workbench"
github_repo: "abus-aikorea/voice-pro"
source_key: "gh:abus-aikorea/voice-pro"
description: "Voice-Pro（abus-aikorea/voice-pro）把 yt-dlp 下载、Demucs 人声分离、Whisper 识别、Deep-Translator 翻译、F5-TTS/CosyVoice 声音克隆串成一条本地 Gradio 流水线。项目已完全开源（LGPL）、完全免费，但作者已暂停更新。本文拆它的工序、机制、排查方法和该不该用。"
draft: false
categories: ["技术笔记"]
tags: ["AI 语音", "Whisper", "F5-TTS", "CosyVoice", "Edge-TTS", "ElevenLabs 替代"]
---

# Voice-Pro：跑在本地 Gradio 里的 YouTube 配音流水线

Voice-Pro（`abus-aikorea/voice-pro`）不发明任何模型。它把 yt-dlp、Demucs、Whisper、Deep-Translator、F5-TTS 这些各自独立的开源工具，按真实配音工序的顺序粘进同一个 Gradio 页面：下载视频 → 分离人声 → 识别出字幕 → 翻译 → 按时间戳合成配音。官方把它定位为 ElevenLabs 的本地替代。

动手之前，有两个事实比功能列表更影响决策：

- **项目已暂停更新。** README 的 Notice 写明，因为团队转做另一个产品 WeConnect，Voice-Pro 暂时不会再有更新。最后一个版本是 2026 年 7 月的 v4.0。
- **代码已完全开源、完全免费。** v3.2 起全部代码开源（LGPL），早年的 60 秒试用限制和 Shopify 订阅制已经取消，任何人可以自由使用、分发和修改。

换句话说，这是一个不会再长大、但已经够用且免费的工具。适合把它当作一条稳定的本地流水线来用，不适合期待它持续演进。

## 系统地图：六个模块按工序排列

WebUI 按任务分成四个标签页，背后是六组开源依赖：

| 模块 | 关键依赖 | 角色 |
|------|---------|------|
| YouTube 下载 | yt-dlp | 拉取音视频源 |
| 人声分离 | Demucs、MDX-Net | 把 BGM 和人声拆开 |
| 语音识别 | Whisper、Faster-Whisper、Whisper-Timestamped | 出带时间戳的字幕 |
| 翻译 | Deep-Translator（默认免费）+ Azure Translator（自带 Key） | 100+ 语言 |
| 多语种 TTS | F5-TTS、E2-TTS、CosyVoice、Edge-TTS、kokoro | 配音与声音克隆 |
| WebUI | Gradio 6.20 | 整合界面 |

四个标签页的分工：

- **Dubbing Studio**：主入口，下载、降噪、字幕、翻译、TTS 在一个页面串完，支持 ffmpeg 兼容格式，音频输出可选 WAV/FLAC/MP3。
- **Whisper Caption**：纯字幕工具，90+ 语言，支持词级高亮和降噪选项，字幕直接嵌在视频播放器里对照显示。
- **Translate**：100+ 语言翻译，能吃现成的 ASS/SSA/SRT 字幕文件，也支持实时语音识别加翻译。
- **Speech Generation**：TTS 出口，Edge-TTS、F5-TTS、CosyVoice、kokoro 四选一；配了 Azure Key 后第一个选项会变成 Azure-TTS。

## 从订阅制到全开源：版本脉络

Voice-Pro 的"完全免费"不是天上掉下来的，看版本历史就明白它经历了什么。

v2.0 时代（2025 年），它是半个商业产品：免费试用只处理 60 秒以内的素材，Shopify 订阅解锁无限用量，订阅版附带 Azure Translator 和 Azure TTS。首次运行要下载 9GB 的 CosyVoice2-0.5B，网速慢时要等一个多小时。

v3.0 和 v3.1 做了两件铺垫：移除 AI Cover 功能；给 F5-TTS 接上各语言社区微调模型（英、中、法、日、俄、西、意、芬兰、印地语各有专用权重）。

v3.2 是转折点。作者自述几个月都在做 WeConnect、完全没精力维护 Voice-Pro，于是决定把全部代码开源、完全免费。同一版 README 宣布支持 Windows/Mac/Linux——但后文又承认只在 Windows + NVIDIA GPU 上验证过，Mac/Linux 用户要自己承担试错成本。

v4.0（2026 年 7 月，当前版本）是一次面向"没人维护之后"的工程收尾：

- 安装器从 Miniconda/pip 整体迁移到 [uv](https://docs.astral.sh/uv/)，依赖锁进 `uv.lock`，`uv sync` 拿到的就是作者锁定的同一组包。
- 运行时升级到 Python 3.12、Torch 2.8.0+cu128（RTX 50 系支持）、Gradio 6.20。
- whisperX 因依赖锁与 Gradio 6 不兼容被移除，旧配置自动回退到 faster-whisper。
- 新增可选模型 Fun-CosyVoice3-0.5B，覆盖包括韩语在内的 9 种语言，首次启用时从 HuggingFace 官方仓库下载。
- CUDA Toolkit 和 Visual Studio Build Tools 不再是前置要求——全部依赖带预编译 wheel，PyTorch 自带 CUDA runtime。

uv 迁移的实际意义在故障恢复：删掉 `installer_files/` 再跑 `start.bat`，几分钟就能干净重装，`model/` 里已下载的模型不丢。对一个停更项目来说，"随时能重装"比"持续加功能"重要得多。

## 安装与硬件门槛

先对照官方要求，不满足就不用往下走：

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10/11 64-bit（Mac/Linux 有脚本但官方未验证） |
| GPU | NVIDIA，驱动 ≥ 570（RTX 50 系支持），无需安装 CUDA Toolkit |
| 显存 | 4GB 起步，8GB 以上更稳（Denoise level 2 至少要 8GB） |
| 内存 | 4GB+ |
| 磁盘 | 20GB 以上空闲空间 |
| 网络 | 必须在线，首次运行要下载约 10GB 模型 |

安装就两步。`configure.bat` 是可选的（装 git 和 ffmpeg，需要管理员权限，只跑一次；没权限就跳过，`start.bat` 会自动下载便携版 ffmpeg）。`start.bat` 是主入口：首次运行依次下载 uv、Python 3.12、锁文件里的全部依赖，再下载约 10GB 的 AI 模型——这是整个安装里最慢的部分。GPU/CPU 自动检测，也可以用 `GPU_CHOICE` 环境变量覆盖（`G` 指定 NVIDIA，`C` 指定 CPU）。跑起来后 WebUI 地址是 `http://127.0.0.1:7870`。

后续维护同样两条脚本：`update.bat` 把 Python 环境重新同步到锁文件；`uninstall.bat` 不需要管理员权限，只删 `installer_files/`，`model/` 和 `workspace/` 都保留。

默认配置下所有在线服务都走免费通道：翻译用 Deep-Translator（Google 免费网页端点），TTS 用 Edge-TTS。有 Azure 订阅的话值得切换：企业内网的安全设备经常对 `translate.google.com` 限流，长字幕翻译会变慢甚至失败——Voice-Pro 会带退避地重试，失败的行保留原文并在界面上报失败数量，但配了 Azure Translator 可以绕开这个问题，TTS 音色也更稳定。配置方法是复制 `.env.example` 为 `.env`，填入 `AZURE_SPEECH_KEY` 和 `AZURE_TRANSLATOR_KEY`，重启后启动时自动检测生效。`.env` 里有私钥，别提交进版本库。

## 一次完整配音流程

以"YouTube 英文科普视频 → 中英双语字幕 + 韩语配音"为样本，看任务怎么穿过这条流水线：

1. **下载**：贴入 YouTube URL，yt-dlp 拉取视频和音轨。
2. **人声分离**：Demucs 把人声和伴奏拆开。这一步放在识别之前，因为后续的识别和克隆都只需要人声，BGM 只会干扰识别准确率。
3. **识别**：Faster-Whisper large-v3-turbo 输出带时间戳的 SRT；需要词级时间戳时走 Whisper-Timestamped。
4. **翻译**：Deep-Translator 按句翻译（spaCy 负责自然分句，避免按逗号切碎句子），目标语言选中文和韩文；内网受限环境可切 Azure。
5. **配音**：在 Speech Generation 里选模型。要保留原说话人的音色，用 F5-TTS 或 CosyVoice 的零样本克隆，给一段参考音频即可；韩语推荐 Fun-CosyVoice3-0.5B。不需要克隆的旁白，Edge-TTS（100+ 语言、400+ 音色）和 kokoro（官方口径为 HuggingFace TTS Arena 第 2 名）更快、更省显存。
6. **输出**：合成音轨按 WAV/FLAC/MP3 导出，字幕在播放器里与视频对照显示。把配音轨替回原视频这一步，需要自己在剪辑软件里完成——它输出的是流水线半成品，不是一键渲染的成品片。

TTS 的速度、音量、音调都可以在界面上调。整条流程不需要写一行代码。

## 声音克隆怎么选模型

三个 TTS 家族的能力边界不同，选错模型是新手最常见的翻车点。

F5-TTS、E2-TTS、CosyVoice 这一支支持零样本（zero-shot）克隆：不需要几小时的训练数据，只给一段几十秒的参考音频，模型照着参考音频的音色朗读新文本。跨语言是这条路线的强项——参考音频是英语，也能让它用同样的音色说韩语，这正是"英文视频 → 韩语配音"场景的核心能力。多语言文本建议用对应语言的微调模型，F5-TTS 各语种微调权重在 v3.1 就已接入，发音比 base 模型准。

CosyVoice 这边，v4.0 新增的 Fun-CosyVoice3-0.5B 覆盖韩语等 9 种语言，是韩语配音的推荐项。克隆用的参考音色样本库也在持续积累，README 甚至接受用户在 Issues 里点名求某位名人的参考音色——克隆谁的声音、拿去做什么，合规责任始终在调用方自己。

Edge-TTS 和 kokoro 是另一条路线：不克隆，靠预置音色合成。音色不可定制，但速度快、显存占用低，适合不需要"原声复刻"的旁白和翻译腔配音。

## 排查与调优

- **CUDA Out-Of-Memory**：先在任务管理器的性能页看显存占用。降 Denoise level 到 0 或 1（level 2 至少需要 8GB 显存）；把 Compute Type 从 float 换成 int——float 质量更好但吃显存，int 是量化版，用一点质量换显存和速度。
- **字幕质量不理想**：模型越大质量越好的大方向成立（large > medium > small > base > tiny），但不必然；Denoise level 调高会滤掉更多背景音，但背景音本身不总是噪音，不是调越高越好。
- **浏览器没有自动弹出**：关掉命令行窗口重跑 `start.bat`，或者手动访问命令行里显示的地址（默认 `http://127.0.0.1:7870`）。
- **翻译大面积失败**：大概率是免费 Google 端点被限流。等一会儿重试，或者配 Azure Key；失败的行保留原文，界面上有失败计数可以核对。
- **各种奇怪的安装/启动故障**：删 `installer_files/` 再跑 `start.bat`，几分钟完成干净重装，模型不丢。
- **看不清错误原因**：v4.0 起错误以红色 toast 常驻显示，不再是一闪而过的 10 秒警告；常见错误（缺 ffmpeg、没注册媒体文件）会给出可操作提示。

## 和 ElevenLabs、SaaS 摆在一起

| 维度 | ElevenLabs | Voice-Pro |
|------|-----------|-----------|
| 部署 | SaaS（也提供本地） | 完全本地 Gradio |
| TTS 模型 | 自家 Multilingual v2 / Turbo 等 | F5-TTS / E2-TTS / CosyVoice / Edge-TTS / kokoro 多选 |
| 声音克隆 | 自家合规流程 | 取决于所选模型，授权责任在调用方 |
| 翻译 | 与自家 voice 协同 | Deep-Translator（免费默认）+ Azure（自带 Key） |
| 费用 | 订阅制 | 免费开源（LGPL），只花电费 |
| 维护 | 商业公司持续迭代 | 作者已停更，代码可自行 fork |

成本差距可以用 README 自带的一张 SaaS 对比表量化：处理一条 60 分钟的视频（字幕 + 翻译 + 配音），Maestra 约 $23.70、Kapwing 约 $30-40、HappyScribe 约 $36-48（2025 年 4 月的价格口径）。Voice-Pro 做同样的事，订阅费是零，代价是自己的显存、磁盘和等待时间。

反过来的代价也要说清楚：ElevenLabs 的音质、克隆合规和服务稳定性是商业产品级别的，Voice-Pro 的合成质量取决于你选的开源模型，遇到 bug 没有客服，只有 Issues 页面和一份停更的代码。

## 采用建议

按这个顺序试水，每一步不合适就停：

1. 确认硬件：Windows + NVIDIA GPU、显存 4GB 以上、磁盘 20GB 以上。Mac/Linux 用户先放弃，官方没验证过。
2. clone 仓库，跑 `start.bat`，接受约 10GB 的首次下载。
3. 拿一条 5 分钟的视频在 Dubbing Studio 里跑完整流程，确认识别和翻译质量达到你的底线。
4. 再试克隆：给 F5-TTS 一段参考音频，判断音色相似度是否可接受。
5. 上长视频或批量任务之前，把 Denoise level 和 Compute Type 调到与显存匹配的档位。

适合投入的场景：有 NVIDIA GPU 的 Windows 工作站，素材或声音样本不方便上传云端，预算为零的个人创作者和搬运团队。不适合的：需要 SLA 的 ToC 配音服务（它只是一个本地 Gradio 应用，没有服务化能力）；实时直播配音（离线流水线，架构不针对延迟优化）；期待持续更新的用户——它的功能边界就是 v4.0 的边界。

Voice-Pro 的价值不在任何单个模型——Whisper、F5-TTS、Demucs 单独拿出来都有各自的成熟用法——而在把配音工序里的工程胶水做完了：格式转换、时间戳对齐、分句翻译、显存降级这些脏活都有现成处理。停更改变了它的性质：从"会演进的产品"变成"可以整条拿走的流水线模板"。对本地、免费、一次性任务的场景，这个变化不致命；对想把这套能力集成进自己产品的团队，完整开源的代码反而是更直接的入口。用之前，以仓库 [github.com/abus-aikorea/voice-pro](https://github.com/abus-aikorea/voice-pro) 的 README 为准——免费渠道和模型版本这类信息，过时得很快。
