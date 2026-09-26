---
title: "FluidVoice：macOS 上的本地语音转文字与命令模式，8 个 ASR 后端随便挑"
date: "2026-06-28T21:11:10+08:00"
slug: "altic-dev-fluidvoice-macos-voice-transcription-guide"
github_repo: "altic-dev/FluidVoice"
source_key: "gh:altic-dev/FluidVoice"
description: "FluidVoice 是 altic-dev 开源的 macOS 15+ 离线听写应用，集成 Nemotron / Parakeet / Cohere / Apple Speech / Whisper 等 8 个 ASR 后端，搭配命令模式、书写模式与本地 Fluid Intelligence 润色层。本文梳理它的快速上手、模型选择路径与适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["macOS", "Swift", "Parakeet", "Whisper"]
---

# FluidVoice：macOS 上的本地语音转文字与命令模式，8 个 ASR 后端随便挑

## 学习目标

读完本文，你应该能做到：

- 说清 FluidVoice 的定位：它和 Mac 自带听写、Wispr Flow 这类产品差在哪
- 按自己的语言、机器型号和延迟容忍度，从 8 个 ASR 后端里挑出一个合适的
- 用 Homebrew 装好 FluidVoice，配好权限和热键，跑通第一次听写
- 判断命令模式、书写模式、Fluid Intelligence、自定义词典、录音历史这几项能力，哪些用得上

## 目录

- [一句话定位](#一句话定位)
- [项目身份卡](#项目身份卡)
- [模型矩阵：8 个 ASR 后端](#模型矩阵8-个-asr-后端)
- [快速上手](#快速上手)
- [五项增强能力](#五项增强能力)
- [架构速览](#架构速览)
- [隐私模型](#隐私模型)
- [适用边界](#适用边界)
- [自测题](#自测题)
- [练习](#练习)
- [进阶路径](#进阶路径)
- [常见问题](#常见问题)
- [资料口径说明](#资料口径说明)
- [我会怎么用](#我会怎么用)
- [链接](#链接)

## 一句话定位

[FluidVoice](https://github.com/altic-dev/FluidVoice) 是 altic-dev 开源的 macOS 本地听写应用，Swift 写的，GPLv3 协议。它不是靠某一个 ASR（Automatic Speech Recognition，自动语音识别）模型做得最准取胜，而是把市面上主流的几个开源 / 系统级 ASR 引擎装进同一个 SwiftUI 应用，再叠一层自家训练的本地 AI 润色（Fluid Intelligence），加上两项 Mac 自动化能力——命令模式、书写模式。仓库描述里给自己的对照物很直白：a local Wispr Flow alternative，本地的 Wispr Flow 替代品。

项目节奏比较稳：30 个 release 覆盖了从 2025-09 创立至今的全部迭代，最近一次发布是 2026-08-18 的 v1.6.9。macOS 之外，iOS 和 Windows 版本在排队（README 让感兴趣的人去 [waitlist](https://www.altic.dev/fluid/waitlist) 排队等通知），还没有可下载的构建。

## 项目身份卡

| 字段 | 值 |
| --- | --- |
| 仓库 | [altic-dev/FluidVoice](https://github.com/altic-dev/FluidVoice) |
| 协议 | GPLv3（2026-02-23 起；此前版本为 Apache 2.0） |
| 主语言 | Swift |
| 最低系统 | macOS 15.0（Sequoia） |
| 硬件 | Apple Silicon 全模型可用；Intel 仅 Whisper 可用（1.5.1+ 起） |
| 发行 | Homebrew Cask + GitHub Releases（DMG / ZIP） |
| Stars / Forks | 11,647 / 834（2026-09-20 核实） |
| 最近提交 | 2026-09-18 |
| 最近发布 | v1.6.9（2026-08-18） |

## 模型矩阵：8 个 ASR 后端

把 FluidVoice 和同类项目（Mac 自带听写、Wispr Flow、Macwhisper 等）放在一起看，最显眼的差异是它支持的 ASR 后端数量。下表整理自 README，所有数字以 README 当前版本为准：

| 后端 | 主要语言支持 | 模型大小 | 硬件 | 适合场景 |
| --- | --- | --- | --- | --- |
| Nemotron Speech 3.5（流式） | ~40 种语言 | ~670 MB | Apple Silicon | 低延迟多语种流式听写 |
| Nemotron 3.5 多语种 | ~40 种语言 | ~530 MB | Apple Silicon | 更高精度的多语种听写 |
| Parakeet Flash（Beta） | 英语 | ~250 MB | Apple Silicon | 英语最低延迟实时听写 |
| Parakeet TDT v3 | 25 种语言 | ~500 MB | Apple Silicon | 多语种默认快档 |
| Parakeet TDT v2 | 英语 | ~500 MB | Apple Silicon | 英语专用最快档 |
| Cohere Transcribe | 14 种语言 | ~1.4 GB | Apple Silicon | 高精度多语种 |
| Apple Speech | 跟随系统语言 | 0（系统自带） | Apple Silicon + Intel | 零下载兜底 |
| Whisper（tiny / base / small / medium / large） | 最多 99 种语言 | ~75 MB 至 ~2.9 GB | Apple Silicon + Intel | 兼容性最广，Intel 唯一选择 |

几个值得单独说的点：

- **Parakeet 系列是 NVIDIA 的模型**。仓库 README 顶部的 badge 直接指向 [parakeet_realtime_eou_120m-v1](https://huggingface.co/nvidia/parakeet_realtime_eou_120m-v1)，v1.6.0 的 release note 把"Parakeet 几乎零延迟"列为主推卖点。v1.6.7 又做了一轮优化：Parakeet 转写在 Apple Silicon 上最高快到原来的 2 倍，M4 / M5 提升最大，M1–M3 也有大约 1.3–1.5 倍。
- **Whisper 是 Intel 用户的唯一选项**。Intel Mac 自 v1.5.1 起受支持，且只支持 Whisper 系列；模型越大，CPU 上跑得越慢。
- **Apple Speech 是零下载兜底**，没有独立模型、没有 GPU 加速，但不用下任何东西。只想确认听写流程是不是自己要的，选它最快。
- **Cohere Transcribe 体积最大（1.4 GB）**，对硬件要求最高，README 把它标成高精度多语种档。

## 快速上手

README 的 Quick Start 有七步，其中三步是可选配置，真正必要的就四步。

### 1. 安装

```bash
brew install --cask fluidvoice
```

或者从 [Releases](https://github.com/altic-dev/FluidVoice/releases/latest) 手动下载 DMG / ZIP，两条路没有功能差别。

### 2. 授权

首次启动时 FluidVoice 会请求两个权限：

- **麦克风**：用于采集语音。不给这个权限，按下热键也不会有任何反应。
- **辅助功能（Accessibility）**：用于把识别结果"打"进当前应用的输入框。FluidVoice 走 macOS 的无障碍 API，所以理论上能写进任何文本框。

两个权限都建议设为始终允许，避免系统之后反复弹窗。

### 3. 设全局热键

在设置里挑一个全局热键。FluidVoice 推荐的形态是按住说话、松开停止，类似对讲机。热键管理器 `GlobalHotkeyManager.swift` 有 110 KB，是 `Services/` 目录里第二大的文件，这块是它认真打磨过的部分。

### 4. 选一个 ASR 后端

按下面的决策树挑：

```
你有 Apple Silicon Mac 吗？
├── 是 → 主要说中文 / 多语种吗？
│       ├── 是 → Parakeet TDT v3（25 语种，约 500 MB）
│       └── 否 → 英语专用，要最低延迟？
│               ├── 是 → Parakeet Flash 或 TDT v2
│               └── 否 → Nemotron Speech 3.5
│
└── 否（Intel Mac）→ Whisper medium 或 large
        （注意：模型越大，CPU 上跑得越慢）
```

首次启动的 Onboarding 会按这个顺序引导你选模型，并自动下载到本地。如果愿意尝鲜，`Settings → Automatic Updates → Beta Releases` 可以打开 beta 更新通道，提前用上新特性。

## 五项增强能力

ASR 把声音变成文字只是 FluidVoice 的一半。下面这五项才是它和"系统听写 + 记事本"拉开差距的地方，也是 v1.6 系列迭代的重点。

### 命令模式（Command Mode）

按下热键说出命令，FluidVoice 会执行对应的 Mac 操作。README 给出的能力范围是：启动应用、运行 Shortcuts、触发系统操作、自动化工作流，全程不碰键盘。"Open Safari"这类指令属于启动应用的典型场景。底层是 `CommandModeService.swift`（37 KB）加上 `Networking/` 目录下的 `FunctionCallingProvider.swift`（16 KB），结合 macOS 的 Shortcuts 与辅助功能 API 实现一套本地的 function calling。整个过程在本地完成，不经过任何云 API。

### 书写模式（Write Mode）

在任意应用的文本框里，选中一段文字让它改写，或者直接口述新内容插入。比如选一段话按热键说"翻译成英文"，FluidVoice 会调用 AI provider 重写并替换回去。可用的 provider 有四类：

- OpenAI（云端）
- Groq（云端，速度快）
- 自定义 OpenAI 兼容端点
- **Fluid Intelligence（本地，约 3.5 GB 模型）**

provider 的 API Key 存在 macOS Keychain 里，由 `Persistence/` 目录下的 `KeychainService` 负责。README 建议对密钥访问选 "Always allow"。

### Fluid Intelligence：本地 AI 润色层

这是 v1.6.0 主推的特性，需要单独说清楚：

- 定位：在 ASR 结果之后跑一遍，做智能格式化、上下文大小写和后处理润色（比如把"逗号 句号"这类口语标点自动换成正常符号）
- 体积：约 3.5 GB 磁盘 + 约 3.5 GB 运行时内存（v1.6.0 release note 原话）
- 训练数据：10 万+ 听写数据点（release note 原话）
- 模型名是 Fluid-1，后续版本持续在提速：v1.6.3 在 Apple Silicon 上快了 2.2 倍；v1.6.2 把可处理的文本长度从约 200 词提到约 2000 词，还提供一个多占约 100 MB 内存、换 15% 输出提速的开关
- **不**开源，README 写得很直白："We're keeping Fluid Intelligence private for now so we can sustainably offer the core dictation experience for free. This may change in the future."

这意味着 FluidVoice 主程序是 GPLv3 的，但 Fluid Intelligence 模型本身是 altic-dev 私有的资产。这种分层许可在开源听写项目里不算罕见，但评估时要分清两件事：主程序可以自由审计，Fluid Intelligence 模型不能自行编译或自托管。

### 自定义词典与口语标点

v1.6.2 到 v1.6.9 连续加了一组"让模型听懂你的词"的能力：

- **Custom Dictionary**：把常被听错的词登记成替换规则；用得多了，它还会在你反复手动纠正之后主动建议条目（v1.6.3）
- **Train by Voice**：对着麦克风把难词念几遍，把听错的版本存成一条替换规则，适合人名和同音词（v1.6.2 / v1.6.3）
- **Spoken Formatting**：说"new line""tab"这类词就能插入换行、制表符、标点，触发词可以自己配置（v1.6.9）
- **口语标点转符号**：说 dash、question mark、period 直接变 `-`、`?`、`.`，不需要 Fluid Intelligence，也不需要任何 AI（v1.6.2）
- **/commands 与 @mentions**：口述时用 `/` 命令和 `@` 提及，为 Slack、Discord 这类应用做了间距优化，默认关闭（v1.6.2）

### 录音历史与说话人标签

- **Audio History**（v1.6.0 起）：可选的本地录音历史，带磁盘预算控制和 ZIP 导出，全部留在本机
- **离线说话人标签**（v1.6.8 起）：对上传的音频文件做转写时，可以按说话人分段、加时间戳，历史支持 text / JSON 导出。相关代码在 `SpeakerDiarizationService.swift` 和 `TranscriptionHistoryStore.swift`（42 KB）

## 架构速览

FluidVoice 是一个标准的 SwiftPM + Xcode 工程。`Sources/Fluid/` 下有 173 个 Swift 文件，分在 8 个子目录里：

```
FluidVoice/
├── Package.swift          # Swift Package Manager 声明
├── Fluid.xcodeproj/       # Xcode 工程
├── Sources/Fluid/
│   ├── ContentView.swift  # 239 KB，主 SwiftUI 视图
│   ├── AppDelegate.swift  # 21 KB
│   ├── Models/            # 1 个文件，数据模型
│   ├── Services/          # 73 个文件，核心逻辑
│   │   ├── ASRService.swift              # 286 KB，转写核心
│   │   ├── GlobalHotkeyManager.swift     # 110 KB
│   │   ├── TypingService.swift           # 63 KB
│   │   ├── MenuBarManager.swift          # 45 KB
│   │   ├── CommandModeService.swift      # 37 KB
│   │   ├── FluidAudioProvider.swift      # 36 KB
│   │   ├── NemotronProvider.swift        # 26 KB
│   │   ├── WhisperProvider.swift         # 19 KB
│   │   └── ParakeetRealtimeProvider.swift
│   ├── Persistence/       # 14 个文件，Keychain / 设置 / 历史
│   │   └── SettingsStore.swift           # 246 KB，配置中心
│   ├── Networking/        # 3 个文件，AIProvider / FunctionCallingProvider
│   ├── Analytics/         # 7 个文件，匿名分析
│   ├── Theme/             # 11 个文件，主题
│   ├── UI/                # 53 个文件
│   └── Views/             # 5 个文件，刘海浮层等
├── Tests/
└── docs/  scripts/  assets/
```

`Package.swift` 里列了 5 个依赖：

| 依赖 | 用途 |
| --- | --- |
| [altic-dev/FluidAudio](https://github.com/altic-dev/FluidAudio) | 自家音频框架，承载 Parakeet / Nemotron / Cohere |
| [altic-dev/transcribe-cpp-swift](https://github.com/altic-dev/transcribe-cpp-swift) | Whisper 的 C++ 转写后端封装 |
| [altic-dev/DynamicNotchKit](https://github.com/altic-dev/DynamicNotchKit) | 自家组件，MacBook 刘海上的实时转写浮层 |
| mxcl/AppUpdater | 自动更新 |
| mxcl/PromiseKit | Promise 链 |

整套架构是"主进程 + 多个 ASR provider + 多个增强 provider"的插件形态，每个 provider 实现各自的 Swift protocol，由 `ASRService` 统一调度。Whisper 一侧从早期版本的 Swift 封装换成了 C++ 后端（`TranscribeCpp`），v1.6.3 的 release note 提到"所有 Whisper 模型回归菜单且更快"，对应的就是这次更换。配置项的粒度从 246 KB 的 `SettingsStore.swift`（外加 CommandMode、NemotronLanguage 等多个扩展文件）也能看出来，per-app prompt、开机自启、nemotron language 这些开关都被拆成了独立设置。

## 隐私模型

README 用单独一节 "Privacy & Analytics" 说明数据流向，现行版本的口径是这样的：

- **默认状态**：local-first。语音、音频、转写文本默认全部留在本机，只有显式开启 OpenAI / Groq / 自定义云端 provider 用于润色或改写时，相关文本才会离开本机。
- **匿名分析**：每天记录一个匿名活动信号，缓存一周后批量上传；信号内容是随机安装 ID、日期、应用版本和 macOS 平台标签。在此之上，详细匿名分析默认开启（每日功能与模型使用总量、Onboarding 进度、模型下载开始与结果），可以在 `Settings → Share Detailed Anonymous Analytics` 里关掉；关闭后每周只上传那一条活动信号。
- **明确不收集**：语音、原始音频、转写文本、选中文本、提示词、AI 回复、终端命令、窗口标题、文件路径、剪贴板、键入内容。

早期版本曾通过 PostHog SDK 做分析，现行版本已经移除该依赖，换成了上面这套自建的周批信号。整体态度没有变：默认本地，联网的功能需要用户主动开。

## 适用边界

FluidVoice 不是万能听写工具，装之前先对照一下这些边界：

**适合**

- Apple Silicon + macOS 15+ 用户，想把听写、命令模式、书写模式放进同一个应用
- 对 Whisper 之外的开源 ASR（Parakeet / Nemotron / Cohere）有明确需求，愿意自己评估不同后端的精度和延迟
- 不想把语音数据默认交给云端、又想要 AI 润色的用户（Fluid Intelligence 这条路）

**不太适合**

- Intel Mac 用户。除 Whisper 外所有模型都要求 Apple Silicon，Intel + Whisper large 在 CPU 上跑得吃力
- macOS 14 或更早系统的用户（最低要求 macOS 15.0 Sequoia）
- 需要完全开源栈的用户。Fluid Intelligence 模型私有，主程序虽是 GPLv3 但无法自托管这一层
- Windows / iOS 用户。两个平台都还在 waitlist 阶段，没有可下载的构建
- 想要"装好就能用"的极简用户。8 个 ASR 后端 + 多种 AI provider + 命令模式开关，第一次启动的决策成本不低

## 自测题

用以下 4 题检验理解程度，答案折叠在每题下方。

**Q1**：FluidVoice 支持哪 8 个 ASR 后端？哪个后端是 Intel Mac 的唯一选项？

<details>
<summary>点击查看参考答案</summary>

**答案**：Nemotron Speech 3.5（流式）、Nemotron 3.5 多语种、Parakeet Flash（Beta）、Parakeet TDT v3、Parakeet TDT v2、Cohere Transcribe、Apple Speech、Whisper（tiny/base/small/medium/large）。Intel Mac 的唯一选项是 Whisper 系列（自 v1.5.1 起支持）。

</details>

**Q2**：命令模式、书写模式、Fluid Intelligence 分别解决什么问题？

<details>
<summary>点击查看参考答案</summary>

**答案**：命令模式把语音当遥控器，触发启动应用、运行 Shortcuts、系统操作；书写模式在任意应用的文本框里改写选中文字或直接口述插入新内容；Fluid Intelligence 是本地润色层，在转写结果之后做智能格式化、上下文大小写和后处理，不经过云端。

</details>

**Q3**：FluidVoice 主程序和 Fluid Intelligence 模型的许可有什么差别？这对使用者意味着什么？

<details>
<summary>点击查看参考答案</summary>

**答案**：主程序自 2026-02-23 起是 GPLv3（此前 Apache 2.0），可以自由审计、修改、编译；Fluid Intelligence（Fluid-1）模型是 altic-dev 私有的，官方理由是用它来持续免费提供核心听写功能。使用者能审计听写主链路，但不能自行编译或自托管润色模型——要本地润色就只能用官方发布的模型。

</details>

**Q4**：为什么说 FluidVoice 是"local-first"而不是"完全离线"？

<details>
<summary>点击查看参考答案</summary>

**答案**：默认情况下语音、音频、转写文本都留在本机，但两处例外由用户决定：开启 OpenAI / Groq / 自定义云端 provider 后，润色相关文本会发往云端；匿名分析默认开启，每天一条信号、每周批量上传一次（可在设置里只保留周批信号或全部关闭详细分析）。所以它是"默认本地、可选择性联网"，不是断网也能全功能运行的"完全离线"。

</details>

## 练习

### 练习一：跑通最小流程

按"快速上手"装好 FluidVoice，完成授权、热键设置，用 Apple Speech 跑通第一次听写。顺手记下两件事：模型下载用了多久，转写结果和你说话的内容差在哪里。

### 练习二：对比三个后端

准备一段 1 分钟的中文音频（自己录即可），分别用 Apple Speech、Parakeet TDT v3、Whisper medium 转写，比较三份结果的错误多不多、出字快不快、模型各占多大磁盘。结论写在你的使用场景里才算数：同一台机器上，最准的不一定是等待感最低的。

### 练习三：配置书写模式并测试

在设置里配一个 AI provider（OpenAI 或 Groq，或直接开 Fluid Intelligence），在任意文本框输入一段话，选中后说"翻译成英文"，观察替换结果。再试几个不同风格的指令（更正式、更口语、改写成列表），感受不同 provider 的响应速度差异。

## 进阶路径

1. **装上并体验**：`brew install --cask fluidvoice`，跑通第一次听写，把 8 个后端里符合你语言的两三个都试一遍。
2. **读官方文档**：[altic.dev/fluid](https://altic.dev/fluid) 有完整文档和最新特性说明。
3. **读源码**：clone 仓库后从 `Sources/Fluid/Services/ASRService.swift` 入手，它是 286 KB 的转写调度核心，能看清多后端如何统一抽象。
4. **配命令模式**：试启动应用和运行 Shortcuts 两类指令，确认它在你常用的应用里能正常触发。
5. **配书写模式**：选一个 provider 测试改写效果，API Key 存 Keychain。
6. **评估 Fluid Intelligence**：M 系列 Mac 且内存 ≥ 16 GB 的可以下载 Fluid-1（约 3.5 GB）试用润色；8 GB 内存的机器建议绕开。
7. **参与社区**：改进了代码可以给 [altic-dev/FluidVoice](https://github.com/altic-dev/FluidVoice) 提 PR，v1.6.5 之后的多个修复都来自社区贡献者。

## 常见问题

### 1. 安装后按下热键没反应？

依次检查：系统设置 → 隐私与安全性 → 麦克风，确认 FluidVoice 已授权；同页面的辅助功能列表，确认已授权；FluidVoice 设置里的全局热键是否设置成功。都正常的话，重启应用再试。

### 2. ASR 后端下载失败？

检查网络连接和磁盘剩余空间（最大的是 Cohere Transcribe，约 1.4 GB）。Parakeet 和 Nemotron 系列要求 Apple Silicon，Intel Mac 下载会失败。v1.6.3 之后的版本对模型下载做了连续的字节级进度显示，如果进度条长时间不动，先确认网络能正常访问模型托管在 Hugging Face 上的下载源。

### 3. 转写精度不满意？

先换后端实测——同一台机器上不同后端表现差别很大，模型矩阵表格就是为这个准备的。再检查麦克风质量和环境噪音，内置麦克风在嘈杂环境下的表现通常不如外接。专有名词反复听错的话，用 Custom Dictionary 或 Train by Voice 登记替换规则。

### 4. 书写模式不工作？

确认已配置 AI provider 且 API Key 有效（Keychain 里可以核对）；用云端 provider 时检查网络；Fluid Intelligence 则确认模型已下载完成。改写只对选中的文本生效，没有选中内容时会走口述插入而不是改写。

### 5. Fluid Intelligence 占用太多内存？

约 3.5 GB 运行时内存是设计内开销，不是泄漏。8 GB 内存的机器建议不用 Fluid Intelligence，改用云端 provider 或纯 ASR 输出；设置里可以单独关闭它。

## 资料口径说明

1. **信息来源与时效性**：本文基于 v1.6.9（2026-08-18 发布）的 README、release notes、`Package.swift` 与源码目录结构整理，关键数字（stars / forks、模型大小、文件大小、依赖列表、隐私口径）于 2026-09-20 通过 GitHub API 与仓库原文核对。FluidVoice 仍在迭代，后续版本可能改变 ASR 后端支持、Fluid Intelligence 能力和隐私细节。
2. **技术细节验证**：模型大小、语言支持、硬件要求等数字来自 README 与 release note 原文，未经独立复测；实际表现取决于 Mac 型号、系统版本、麦克风质量和环境噪音。
3. **判断与建议的边界**：模型选择建议、适用边界等判断基于公开文档与架构分析，不构成官方立场，也不构成商业建议。
4. **未覆盖的内容**：Fluid Intelligence 模型的量化细节、命令模式的 Shortcut 具体配置方法、Intel Mac 上 Whisper 的性能基准、Windows / iOS 版本的发布时间表。
5. **术语使用说明**：ASR（Automatic Speech Recognition）、DMG（Disk Image）、ZIP、Homebrew Cask、SwiftUI、SwiftPM、MLX 等专有名词保留原文。
6. **更新记录**：初稿基于 v1.6.1（2026-06-28）；2026-09-20 更新至 v1.6.9，同步了模型提速、自定义词典、说话人标签、隐私口径与依赖变更。

---

## 我会怎么用

如果是我自己的 M 系列 Mac，我会按这个顺序来：

1. 先用 Apple Speech 跑一遍 Onboarding，确认权限、热键、浮层都通了
2. 切到 Parakeet TDT v3 当默认——25 种语言、约 500 MB，体积和精度的平衡点；v1.6.7 之后 Parakeet 在 Apple Silicon 上最高有 2 倍提速，出字延迟已经不是问题
3. 专有名词听错就登记 Custom Dictionary，比换模型便宜
4. 润色需求优先试 Fluid Intelligence：Fluid-1 已经比刚发布时快了 2.2 倍，能吃约 2000 词的长文本，16 GB 内存的机器可以日常开着；云端 provider 留给想要特定文风改写的场景
5. 命令模式先从启动应用这一类指令用起，Shortcuts 自动化等有真实需求再配

如果你主要写英文、追求最低延迟，Parakeet Flash（Beta）是 README 自己主推的那条路，可以从它起步。Windows 用户暂时只能等 waitlist 放号。

## 链接

- 仓库：[github.com/altic-dev/FluidVoice](https://github.com/altic-dev/FluidVoice)
- 官网：[altic.dev/fluid](https://altic.dev/fluid)
- 最新发布：[github.com/altic-dev/FluidVoice/releases/latest](https://github.com/altic-dev/FluidVoice/releases/latest)
- Discord：[discord.gg/VUPHaKSvYV](https://discord.gg/VUPHaKSvYV)
- X：[@fluidvoiceapp](https://x.com/fluidvoiceapp)
- Sponsors：[github.com/sponsors/altic-dev](https://github.com/sponsors/altic-dev)
