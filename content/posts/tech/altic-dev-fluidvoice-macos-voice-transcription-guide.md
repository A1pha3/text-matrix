---
title: "FluidVoice：macOS 上的本地语音转文字与命令模式，8 个 ASR 后端随便挑"
date: "2026-06-28T21:11:10+08:00"
slug: "altic-dev-fluidvoice-macos-voice-transcription-guide"
description: "FluidVoice 是 altic-dev 开源的 macOS 15+ 离线听写应用，集成 Nemotron / Parakeet / Cohere / Apple Speech / Whisper 等 8 个 ASR 后端，搭配命令模式、改写模式与本地 Fluid Intelligence 润色层。本文梳理它的快速上手、模型选择路径与适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["macOS", "Swift", "语音转文字", "Parakeet", "Whisper"]
---

# FluidVoice：macOS 上的本地语音转文字与命令模式，8 个 ASR 后端随便挑

## 学习目标

读完本文后，你能够：

- 说出 FluidVoice 的核心定位与它在 macOS 听写工具里的位置
- 根据自己的语言、机器型号、延迟容忍度，从 8 个 ASR 后端里挑出最合适的一个
- 用 Homebrew Cask 装好 FluidVoice，配好权限、热键，跑通第一次听写
- 判断命令模式、改写模式、Fluid Intelligence 三项增强是不是自己需要的

## 目录

- [一、项目定位与核心特性](#一句话定位)
- [二、模型矩阵：8 个 ASR 后端对比](#模型矩阵fluidvoice-真正的差异化)
- [三、快速上手](#快速上手)
- [四、三项增强能力](#三项增强能力)
- [五、架构速览](#架构速览)
- [六、隐私模型](#隐私模型)
- [七、适用边界](#适用边界)
- [八、自测题](#八自测题)
- [九、练习](#九练习)
- [十、进阶路径](#十进阶路径)
- [十一、常见问题](#十一常见问题)
- [十二、总结](#我会怎么用)

## 一句话定位

FluidVoice 是 [altic-dev/FluidVoice](https://github.com/altic-dev/FluidVoice) 维护的一款 macOS 离线听写应用，Swift 写的，GPLv3 协议。它的特点不是某一个 ASR（Automatic Speech Recognition，自动语音识别）模型做得最准，而是把市面上常见的几个开源 / 系统级 ASR 引擎统一塞进同一个 SwiftUI 应用里，再叠一层可选的本地 AI 润色（Fluid Intelligence）和两项非常实用的 Mac 自动化能力——命令模式、改写模式。

仓库当前 3,299 stars、217 forks，最近一次发布是 2026-06-28 的 v1.6.1。30 个 release 覆盖了从 2025-09 项目初始到现在的全部迭代，开发节奏比较稳。

## 项目身份卡

| 字段 | 值 |
| --- | --- |
| 仓库 | [altic-dev/FluidVoice](https://github.com/altic-dev/FluidVoice) |
| 协议 | GPLv3（2026-02-23 起；此前版本为 Apache 2.0） |
| 主语言 | Swift 99.7% + Shell 0.3% |
| 最低系统 | macOS 15.0（Sequoia） |
| 硬件 | Apple Silicon 全模型可用；Intel 仅 Whisper 可用（1.5.1+ 起） |
| 发行 | Homebrew Cask + GitHub Releases（DMG / PKG） |
| Stars / Forks | 3,299 / 217 |
| 最近提交 | 2026-06-28 |
| 最近发布 | v1.6.1（2026-06-28），距 v1.6.0 仅 6 天 |

## 模型矩阵：FluidVoice 真正的差异化

把 FluidVoice 和同类项目（Mac 自带听写、Wispr Flow、Macwhisper 等）放在一起看，最显眼的差异就是它支持的 ASR 后端数量。下表整理自 README，所有数字以 README 当前版本为准：

| 后端 | 主要语言支持 | 模型大小 | 硬件 | 适合场景 |
| --- | --- | --- | --- | --- |
| Nemotron Speech 3.5（流式） | ~40 种语言 | ~670 MB | Apple Silicon | 低延迟多语种流式听写 |
| Nemotron 3.5 多语种 | ~40 种语言 | ~530 MB | Apple Silicon | 更高精度的多语种听写 |
| Parakeet Flash（Beta） | 英语 | ~250 MB | Apple Silicon | 英语最低延迟实时听写 |
| Parakeet TDT v3 | 25 种语言 | ~500 MB | Apple Silicon | 多语种默认快档 |
| Parakeet TDT v2 | 英语 | ~500 MB | Apple Silicon | 英语专用最快档 |
| Cohere Transcribe | 14 种语言 | ~1.4 GB | Apple Silicon | 高精度多语种 |
| Apple Speech | 跟随系统语言 | 0（系统自带） | Apple Silicon + Intel | 零下载兜底 |
| Whisper（tiny / base / small / medium / large） | 最多 99 种语言 | ~75 MB ~ 2.9 GB | Apple Silicon + Intel | 兼容性最广，Intel 唯一选择 |

几个值得关注的点：

- **Parakeet 系列由 NVIDIA 出品**，仓库 README 顶部 badge 直接指向 [parakeet_realtime_eou_120m-v1](https://huggingface.co/nvidia/parakeet_realtime_eou_120m-v1)；v1.6.0 的 release note 把"Parakeet 几乎是零延迟"作为主推卖点。
- **Whisper 是 Intel 用户的唯一选项**。FluidVoice 文档明确：Intel Mac 自 v1.5.1 起支持，且只支持 Whisper 系列。
- **Apple Speech 是零下载兜底**，没有 GPU 加速、没有独立模型，但胜在不用下任何东西。如果只想试一下听写流程是不是自己要的，选它最快。
- **Cohere Transcribe 体积最大（1.4 GB）**，对硬件要求最高，但对某些口音和术语识别更稳。

## 快速上手

README 自带的 Quick Start 是七步，这里把它压缩到真正必要的四步。

### 1. 安装

```bash
brew install --cask fluidvoice
```

或者从 [Releases](https://github.com/altic-dev/FluidVoice/releases/latest) 手动下载 DMG / PKG。两条路在功能上没有区别。

### 2. 授权

首次启动时 FluidVoice 会主动请求两个权限：

- **麦克风**：用于采集语音。这一步不给的话，按下热键也不会有任何反应。
- **辅助功能（Accessibility）**：用于把识别结果"打"进当前应用的输入框里。FluidVoice 走的是 macOS 的无障碍 API，所以理论上能"打"进任何一个文本框。

两个权限都建议"始终允许"，否则 macOS 会在系统重启或长时间空闲后反复弹窗。

### 3. 设全局热键

进设置里挑一个全局热键。FluidVoice 推荐的形态是按住说话、松开停止，类似对讲机。GlobalHotkeyManager 这一块的代码量不小（85 KB 的 Swift 文件），说明热键是它认真打磨过的部分。

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

第一次启动 Onboarding 会按这个顺序引导你选模型，并自动下载到本地。

## 三项增强能力

ASR 把声音转成文字只是 FluidVoice 的一半。下面这三项才是它真正和"系统听写 + 记事本"拉开差距的地方。

### 命令模式（Command Mode）

按下热键 + 说出命令词，FluidVoice 会触发 macOS 的应用启动、快捷键、系统操作。比如：

> "Open Safari" → 启动 Safari
>
> "Send message to Alice" → 调用 Messages
>
> "Run shortcut 晨间例程" → 执行 Apple Shortcut

底层走的是 `CommandModeService`（38 KB Swift 文件）+ `FunctionCallingProvider`（16 KB），结合 macOS 的 Shortcuts、Accessibility API 和 FluidVoice 自定义的一套 function calling schema。Command Mode 完全是本地的，不需要任何云 API。

### 改写模式（Rewrite Mode）

选中任意文本框里的一段文字，按下热键说"改写得更正式一点"或者"翻译成英文"，FluidVoice 会调用可选的 AI provider 重写这段文字，再替换回去。支持的 provider 包括：

- OpenAI（云端）
- Groq（云端，速度快）
- 自定义 OpenAI 兼容端点
- **Fluid Intelligence（本地，约 3.5 GB 模型）**

provider 的 API Key 存在 macOS Keychain 里，代码侧由 `KeychainService` 负责，README 建议选 "Always allow"。

### Fluid Intelligence：本地 AI 润色层

这是 v1.6.0 主推的新特性，需要单独拎出来说清楚：

- 定位：在 ASR 之后跑一遍，做智能格式化、上下文大小写、后处理润色（比如把"逗号 句号 句号"自动改成正常标点）
- 体积：约 3.5 GB 磁盘 + 约 3.5 GB 运行时内存
- **不**开源，README 写得很直白："We're keeping Fluid Intelligence private for now so we can sustainably offer the core dictation experience for free. This may change in the future."
- 训练数据：10 万+ 听写样本（release note 原话）

这意味着 FluidVoice 主程序是 GPLv3 的，但 Fluid Intelligence 模型本身是 altic-dev 私有的商用资产。这个分层许可在开源听写类项目里属于正常操作，但读者在评估时要分清两件事：你可以自由审计主程序，但你不能自行编译 Fluid Intelligence 模型。

## 架构速览

FluidVoice 是一个标准的 SwiftPM + Xcode 工程，目录结构比较干净：

```
FluidVoice/
├── Package.swift          # Swift Package Manager 声明
├── Fluid.xcodeproj/       # Xcode 工程
├── Sources/Fluid/
│   ├── ContentView.swift  # 188 KB，主 SwiftUI 视图
│   ├── AppDelegate.swift  # 19 KB
│   ├── Models/            # HotkeyShortcut 等
│   ├── Services/          # 49 个 Swift 文件，核心逻辑
│   │   ├── ASRService.swift              # 150 KB，转写核心
│   │   ├── GlobalHotkeyManager.swift     # 86 KB
│   │   ├── TypingService.swift           # 54 KB
│   │   ├── MenuBarManager.swift          # 35 KB
│   │   ├── CommandModeService.swift      # 38 KB
│   │   ├── NemotronProvider.swift        # 28 KB
│   │   ├── FluidAudioProvider.swift      # 23 KB
│   │   ├── WhisperProvider.swift         # 18 KB
│   │   └── ParakeetRealtimeProvider.swift
│   ├── Persistence/       # 17 个 Swift 文件，Keychain / 设置 / 历史
│   ├── Networking/        # AIProvider / ModelDownloader
│   └── Views/             # BottomOverlayView / NotchContentViews
└── docs/ scripts/ assets/
```

`Package.swift` 里列了 6 个依赖：

| 依赖 | 用途 |
| --- | --- |
| [altic-dev/FluidAudio](https://github.com/altic-dev/FluidAudio) | 自家音频框架，承载 Parakeet / Nemotron / Cohere |
| [exPHAT/SwiftWhisper](https://github.com/exPHAT/SwiftWhisper) | Whisper 的 Swift 封装 |
| [altic-dev/DynamicNotchKit](https://github.com/altic-dev/DynamicNotchKit) | 自家组件，MacBook 刘海上的实时转写浮层 |
| mxcl/AppUpdater | 自动更新 |
| mxcl/PromiseKit | Promise 链 |
| PostHog/posthog-ios | 匿名分析（opt-in，可在设置关闭） |

整套架构是"主进程 + 多个 ASR provider + 多个增强 provider"的 plug-in 形态，每个 provider 实现自己的 Swift protocol，由 `ASRService` 统一调度。从 SettingsStore 文件大小（195 KB）也能看出来，配置项非常细，包括 per-app prompt、launch at startup、nemotron language、parakeet finalization mode 等十几个扩展点。

## 隐私模型

README 单独用一节 "Privacy & Analytics" 说明：

- **默认状态**：local-first。语音、音频、转写文本默认全部留在本机。
- **会上传数据的场景**：用户显式开启了 OpenAI / Groq / 自定义云端 provider 用于增强或改写。
- **匿名分析**：默认开启（PostHog），收集 app 版本、macOS 版本、低基数 feature flag、近似使用量等。可在 `Settings → Share Anonymous Analytics` 关闭。
- **不收集**：语音、原始音频、转写文本、选中文本、提示词、AI 回复、终端命令、窗口标题、文件路径、剪贴板、键入内容。

整体态度是"默认本地，需要联网的功能需要用户主动开"。

## 适用边界

FluidVoice 不是万能听写工具。在决定要不要装之前，先看下面这些边界是否和你的场景对得上：

**适合**

- Apple Silicon + macOS 15+ 用户，希望把听写、命令模式、改写模式三件事在一个应用里搞定
- 对 Whisper 之外的开源 ASR（Parakeet / Nemotron）有明确需求，且愿意自己评估不同后端的精度 / 延迟
- 不愿意把语音数据默认上传到云端、又想要 AI 润色的用户（Fluid Intelligence 这条路）

**不太适合**

- Intel Mac 用户。除 Whisper 之外所有模型都要求 Apple Silicon，Intel + Whisper large 在 CPU 上跑会比较吃力
- macOS 14 或更早系统的用户（最低 macOS 15.0 Sequoia）
- 需要完全开源栈的用户。Fluid Intelligence 模型本身是私有的，主程序虽然 GPLv3 但无法自托管这块
- 想要"装好就能用"的极简用户。8 个 ASR 后端 + 多种 AI provider + 命令模式开关，第一次启动的决策成本不低

## 八、自测题

用以下 4 题检验理解程度。答案折叠在每题下方。

**Q1**：FluidVoice 支持哪 8 个 ASR 后端？哪个后端是 Intel Mac 的唯一选项？

<details>
<summary>点击查看参考答案</summary>

**答案**：8 个 ASR 后端：Nemotron Speech 3.5（流式）、Nemotron 3.5 多语种、Parakeet Flash（Beta）、Parakeet TDT v3、Parakeet TDT v2、Cohere Transcribe、Apple Speech、Whisper（tiny/base/small/medium/large）。Intel Mac 的唯一选项是 Whisper 系列。

</details>

**Q2**：FluidVoice 的三项增强能力是什么？它们分别解决什么问题？

<details>
<summary>点击查看参考答案</summary>

**答案**：
1. **命令模式（Command Mode）**：把语音转成的文字触发 macOS 的应用启动、快捷键、系统操作。适合"不碰键盘"的场景。
2. **改写模式（Rewrite Mode）**：选中文本框里的文字，按下热键说"改写得更正式一点"，调用 AI provider 重写并替换。适合写邮件、改文案。
3. **Fluid Intelligence**：本地 AI 润色层，在 ASR 之后跑一遍，做智能格式化、上下文大小写、后处理润色。约 3.5 GB 模型，需要单独下载。

</details>

**Q3**：FluidVoice 的隐私模型是怎样的？哪些数据会上传？

<details>
<summary>点击查看参考答案</summary>

**答案**：
- **默认状态**：local-first。语音、音频、转写文本默认全部留在本机。
- **会上传数据的场景**：用户显式开启了 OpenAI / Groq / 自定义云端 provider 用于增强或改写。
- **匿名分析**：默认开启（PostHog），收集 app 版本、macOS 版本、低基数 feature flag、近似使用量等。可在 `Settings → Share Anonymous Analytics` 关闭。
- **不收集**：语音、原始音频、转写文本、选中文本、提示词、AI 回复、终端命令、窗口标题、文件路径、剪贴板、键入内容。

</details>

**Q4**：FluidVoice 适合哪些场景？不适合哪些场景？

<details>
<summary>点击查看参考答案</summary>

**答案**：
**适合**：
- Apple Silicon + macOS 15+ 用户，希望把听写、命令模式、改写模式三件事在一个应用里搞定。
- 对 Whisper 之外的开源 ASR（Parakeet / Nemotron）有明确需求，且愿意自己评估不同后端的精度 / 延迟。
- 不愿意把语音数据默认上传到云端、又想要 AI 润色的用户（Fluid Intelligence 这条路）。

**不太适合**：
- Intel Mac 用户。除 Whisper 之外所有模型都要求 Apple Silicon，Intel + Whisper large 在 CPU 上跑会比较吃力。
- macOS 14 或更早系统的用户（最低 macOS 15.0 Sequoia）。
- 需要完全开源栈的用户。Fluid Intelligence 模型本身是私有的，主程序虽然 GPLv3 但无法自托管这块。
- 想要"装好就能用"的极简用户。8 个 ASR 后端 + 多种 AI provider + 命令模式开关，第一次启动的决策成本不低。

</details>

## 九、练习

### 练习一：安装并跑通 FluidVoice 的最小流程

**任务**：按照本文的"快速上手"章节，安装 FluidVoice 并跑通第一次听写。

**要求**：
1. 用 Homebrew Cask 安装 FluidVoice：`brew install --cask fluidvoice`
2. 首次启动时授权麦克风和辅助功能权限
3. 设置全局热键（建议按住说话、松开停止）
4. 选一个 ASR 后端（建议先用 Apple Speech，因为零下载）
5. 打开任意文本框，按下热键，说一段测试文字，观察是否成功转写
6. 记录：安装耗时、首次运行耗时、遇到的错误信息

### 练习二：对比不同 ASR 后端的精度和延迟

**任务**：在同一个场景下，对比 3 个不同的 ASR 后端（如 Apple Speech、Parakeet TDT v3、Whisper medium）。

**要求**：
1. 准备一段 1 分钟的中文测试音频（可以自己录）
2. 分别用 3 个后端转写这段音频
3. 对比转写结果的精度（字错率）和延迟（从说话结束到转写完成的时间）
4. 记录：每个后端的字错率、延迟、模型大小、适合场景
5. 得出你的结论：哪个后端最适合你的场景？

### 练习三：配置改写模式并测试

**任务**：配置 FluidVoice 的改写模式，测试它是否能正确重写选中文本。

**要求**：
1. 在 FluidVoice 设置里配置一个 AI provider（如 OpenAI 或 Groq）
2. 打开任意文本框，输入一段文字（如"今天天气很好"）
3. 选中这段文字，按下热键，说"翻译成英文"
4. 观察是否成功重写并替换
5. 测试不同的改写指令（如"改写得更正式一点"、"改写成诗歌"）
6. 记录：改写精度、响应延迟、API 成本

## 十、进阶路径

读完本文后，按以下顺序深入：

1. **安装并体验 FluidVoice**：用 `brew install --cask fluidvoice` 安装，然后跑通第一次听写，体验不同 ASR 后端的效果。
2. **阅读官方文档**：访问 [altic.dev/fluid](https://altic.dev/fluid) 查看完整文档和最新特性。
3. **研究源码**：Clone `altic-dev/FluidVoice` 仓库，阅读 `Sources/Fluid/Services/ASRService.swift` 理解多后端调度逻辑。
4. **配置命令模式**：测试 FluidVoice 的命令模式，看它是否能正确触发 macOS 的应用启动、快捷键、系统操作。
5. **配置改写模式**：选一个 AI provider（如 OpenAI），测试改写模式的效果。
6. **评估 Fluid Intelligence**：如果你有 M 系列 Mac，下载 Fluid Intelligence 模型（约 3.5 GB），测试它的润色效果。
7. **贡献到社区**：如果你改进了 FluidVoice，或者创建了自定义 ASR 后端，可以提交 PR 到 [altic-dev/FluidVoice](https://github.com/altic-dev/FluidVoice)。

## 十一、常见问题

### 1. 安装后按下热键没反应？

**排查**：
- 确认麦克风权限已授予 FluidVoice（系统设置 → 隐私与安全性 → 麦克风）
- 确认辅助功能权限已授予 FluidVoice（系统设置 → 隐私与安全性 → 辅助功能）
- 检查全局热键是否设置正确（FluidVoice 设置 → 热键）
- 尝试重启 FluidVoice 或重启 macOS

### 2. ASR 后端下载失败？

**排查**：
- 检查网络连接是否正常
- 检查磁盘空间是否足够（最大模型 Cohere Transcribe 约 1.4 GB）
- 如果是 Parakeet 或 Nemotron 系列，确认你是 Apple Silicon Mac（Intel Mac 不支持）
- 查看 FluidVoice 的下载日志（设置 → 高级 → 查看日志）

### 3. 转写精度不满意？

**建议**：
- 尝试不同的 ASR 后端（有些后端对中文支持更好）
- 检查麦克风质量（内置麦克风可能不如外接麦克风）
- 检查环境噪音（安静环境下转写精度更高）
- 如果是专业术语或人名，尝试用 Fluid Intelligence 或云端 AI provider 润色

### 4. 改写模式不工作？

**排查**：
- 确认已配置 AI provider（OpenAI / Groq / 自定义）
- 确认 API Key 正确且有效
- 检查网络连接是否正常（改写模式需要调用云端 API）
- 查看 FluidVoice 的错误日志（设置 → 高级 → 查看日志）

### 5. Fluid Intelligence 下载后占用太多内存？

**说明**：
- Fluid Intelligence 约 3.5 GB 磁盘 + 约 3.5 GB 运行时内存是正常的
- 如果你的 Mac 内存较小（如 8 GB），建议不要用 Fluid Intelligence，改用云端 AI provider
- 可以在 FluidVoice 设置里关闭 Fluid Intelligence，只在需要时用云端 API

## 资料口径说明

1. **信息来源与时效性**：本文基于 2026-06-28 发布的 v1.6.1 源码与 README 整理。FluidVoice 仍在迭代，后续版本可能在 ASR 后端支持、Fluid Intelligence 模型、命令模式语法等方面发生变化。
2. **技术细节验证**：文中涉及的模型大小、语言支持、硬件要求等数字均来自 README 描述，未经独立复测；实际表现取决于 Mac 型号、系统版本、麦克风质量和环境噪音。
3. **判断与建议的边界**：本文给出的模型选择建议、适用边界、采用顺序等判断，基于公开文档和架构分析得出，不构成官方立场，也不构成商业建议。
4. **未覆盖的内容**：本文聚焦快速上手和模型选择，未深入覆盖：Fluid Intelligence 本地模型的量化细节、命令模式的具体 Shortcut 配置、改写模式的 prompt 工程技巧、Intel Mac 上 Whisper 的性能基准测试。
5. **术语使用说明**：本文保留 ASR（Automatic Speech Recognition）、DMG（Disk Image）、PKG（Package Installer）、Homebrew Cask、SwiftUI、WebSocket 等专有名词不翻译。
6. **更新记录**：本文初稿基于 v1.6.1（2026-06-28），若 FluidVoice 后续版本有功能变化，将同步更新对应章节。

---

## 我会怎么用

如果是我自己的 M 系列 Mac，我会按这个顺序试：

1. 先用 Apple Speech 跑一遍 Onboarding，确认权限、热键、浮层都通了
2. 切到 Parakeet TDT v3 当默认，理由是 25 种语言 + ~500 MB，体积和精度的甜点
3. 如果嫌 Parakeet 偶尔识别不准，再叠 OpenAI 作为改写模式 provider（API Key 存 Keychain）
4. Fluid Intelligence 等 v1.7 系列再观察，3.5 GB 内存占用对老款 M 系列不太友好

如果你主要写英文、追求最低延迟，Parakeet Flash（Beta）那条路是 README 自己主推的，可以从那里起步。

## 链接

- 仓库：[github.com/altic-dev/FluidVoice](https://github.com/altic-dev/FluidVoice)
- 官网：[altic.dev/fluid](https://altic.dev/fluid)
- 最新发布：[github.com/altic-dev/FluidVoice/releases/latest](https://github.com/altic-dev/FluidVoice/releases/latest)
- Discord：[discord.gg/VUPHaKSvYV](https://discord.gg/VUPHaKSvYV)
- Sponsors：[github.com/sponsors/altic-dev](https://github.com/sponsors/altic-dev)
