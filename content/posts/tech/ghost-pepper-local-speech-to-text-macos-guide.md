---
title: "Ghost Pepper：1.4k Stars本地语音转文字，Hold Control即可转录粘贴"
date: "2026-04-08T08:35:00+08:00"
slug: ghost-pepper-local-speech-to-text-macos-guide
description: "深度解析Ghost Pepper：macOS本地语音转文字工具。基于WhisperKit语音识别+Qwen3.5清理模型，Hold Control录音，松开自动转文字并粘贴到任意文本框。完全本地运行，保护隐私。"
categories: ["技术笔记"]
tags: ["macOS", "语音识别", "Whisper", "本地AI", "Qwen"]
draft: false
---

# Ghost Pepper：1.4k Stars 本地语音转文字

## 项目概述

**Ghost Pepper**是一款 macOS 上的本地语音转文字工具，核心特点是**100%本地运行**，不依赖任何云端 API。用户只需按住`Control`键说话，松开后即可自动将语音转录为文字并粘贴到任意文本框中。

| 指标 | 数值 |
|------|------|
| **GitHub Stars** | 1.4k |
| **Forks** | 59 |
| **贡献者** | 4 (matthartman, claude, obra, ttulttul) |
| **最新版本** | v2.0.1 (Apr 7, 2026) |
| **许可证** | MIT |
| **语言** | Swift 99.1%, Shell 0.9% |
| **系统要求** | macOS 14.0+, Apple Silicon (M1+) |

**官方 Slogan：** "100% local hold-to-talk speech-to-text for macOS. Hold Control to record, release to transcribe and paste. No cloud APIs, no data leaves your machine."

---

## 核心特性

### 1. Hold-to-Talk 操作

按住`Control`键录音，松开自动转录并粘贴到焦点文本框。操作直觉，无需点击按钮。

### 2. 100%本地运行

所有模型在 Apple Silicon 本地运行，**没有任何数据离开你的电脑**。语音转录和清理完全离线完成。

### 3. Smart Cleanup

使用本地 LLM（Qwen3.5）自动清理转录内容：
- 移除填充词（"uh"、"um"等）
- 处理自我纠正
- 格式化输出

### 4. 菜单栏应用

常驻菜单栏，无 Dock 图标，更轻量。默认开机自启动。

### 5. 完全可定制

- 可编辑 cleanup prompt
- 可选择麦克风
- 可开关各项功能

---

## 技术架构

### 整体架构

```
用户按住Control
    ↓
麦克风录音（本地Whisper模型）
    ↓
语音→文字转录
    ↓
本地LLM清理（Qwen3.5）
    ↓
模拟按键粘贴到焦点文本框
```

### 语音识别模型

Ghost Pepper 使用**WhisperKit**作为语音识别引擎，支持多种模型：

| 模型 | 大小 | 最佳场景 | 速度 |
|------|------|----------|------|
| Whisper tiny.en | ~75 MB | 最快，仅英语 | ⚡⚡⚡⚡⚡ |
| Whisper small.en (默认) | ~466 MB | 最佳精度，仅英语 | ⚡⚡⚡ |
| Whisper small (multilingual) | ~466 MB | 多语言支持 | ⚡⚡⚡ |
| Parakeet v3 (25 languages) | ~1.4 GB | 多语言+ FluidAudio | ⚡⚡ |

### Cleanup 模型

使用**Qwen3.5**系列进行语音清理：

| 模型 | 大小 | 速度 | 质量 |
|------|------|------|------|
| Qwen 3.5 0.8B (默认) | ~535 MB | ~1-2 秒 | 基础 |
| Qwen 3.5 2B | ~1.3 GB | ~4-5 秒 | 标准 |
| Qwen 3.5 4B | ~2.8 GB | ~5-7 秒 | 最佳 |

### 技术栈

- **语音识别**：WhisperKit (argmaxinc)
- **LLM 推理**：LLM.swift (eastriverlee)
- **模型托管**：Hugging Face
- **自动更新**：Sparkle
- **开发框架**：Swift + Xcode

---

## 安装与使用

### 方式一：下载 DMG（推荐）

1. 下载 GhostPepper.dmg
2. 打开 DMG，将 Ghost Pepper 拖到 Applications
3. 首次启动时授予麦克风和辅助功能权限
4. 按住**Control**键说话

### 方式二：从源码构建

```bash
# 克隆仓库
git clone https://github.com/matthartman/ghost-pepper.git

# 进入项目目录
cd ghost-pepper

# 用Xcode打开
open GhostPepper.xcodeproj

# 在Xcode中构建并运行 (Cmd+R)
```

### 权限说明

| 权限 | 用途 |
|------|------|
| **麦克风** | 录制语音 |
| **辅助功能** | 全局快捷键 + 模拟按键粘贴 |

---

## Cleanup 工作流程

Ghost Pepper 的 Smart Cleanup 功能通过本地 LLM 提升转录质量：

### 原始转录（Whisper 输出）
```
uh i think we should um maybe go with the the first option
but actually um let me reconsider the second one is is better
```

### Cleanup 后（Qwen3.5 输出）
```
I think we should go with the first option,
but actually let me reconsider - the second one is better.
```

### 自定义 Cleanup Prompt

用户可编辑 cleanup prompt 来自定义清理行为：

**沉默词移除**
```
Remove all filler words: "uh", "um", "ah", "er"
```

**格式化**
```
Convert to clean prose with proper punctuation.
Break into logical paragraphs.
```

**语气标准化**
```
Maintain the speaker's casual tone but remove all disfluencies.
```

---

## 与同类产品对比

| 产品 | 运行方式 | 隐私 | 特色 |
|------|----------|------|------|
| **Ghost Pepper** | 100%本地 | ⭐⭐⭐⭐⭐ | Hold-to-Talk + LLM Cleanup |
| Whisper Desktop | 本地/云端 | ⭐⭐⭐ | 开源，跨平台 |
| MacWhisper | 本地/云端 | ⭐⭐⭐ | 专业音频编辑 |
| Otter.ai | 云端 | ⭐ | 实时字幕 |
| Apple Voice Control | 系统级 | ⭐⭐⭐⭐ | 系统集成 |

Ghost Pepper 的独特之处：
1. **最直觉的操作**：Hold-to-Talk 比点击录音更自然
2. **本地 LLM Cleanup**：转录质量远超原生 Whisper 输出
3. **完全隐私保护**：没有任何数据上传

---

## 企业部署

Ghost Pepper 需要**辅助功能权限**来实现全局快捷键和模拟按键。企业环境可通过 MDM（Jamf、Kandji、Mosaic 等）预置：

### PPPC Privacy Preferences Policy Control 配置

| 字段 | 值 |
|------|------|
| Bundle ID | `com.github.matthartman.ghostpepper` |
| Team ID | `BBVMGXR9AY` |
| 权限 | Accessibility (`com.apple.security.accessibility`) |

### 配置示例

```xml
<key>com.apple.security.accessibility</key>
<dict>
    <key>Identifier</key>
    <string>com.github.matthartman.ghostpepper</string>
    <key>IdentifierType</key>
    <string>bundleID</string>
    <key>Persona</key>
    <string>Accessibility</string>
</dict>
```

---

## 开发者贡献

Ghost Pepper 是一个开源项目，欢迎开发者贡献。贡献者包括：

| 贡献者 | 角色 |
|--------|------|
| @matthartman | 创始人，主要开发 |
| @claude | Claude Code 贡献代码 |
| @obra | Jesse Vincent (Perl 之父) |
| @ttulttul | Ken Simpson |

---

## 版本历史

- **v2.0.1** (Apr 7, 2026): 修复麦克风权限问题
- **v2.0.0** (Apr 5, 2026): 新增 Pepper Chat 语音助手功能
- **v1.x**: 初始版本发布

---

## 项目结构

```
ghost-pepper/
├── GhostPepper/           # 主应用
│   ├── App/              # 应用入口
│   ├── Views/            # SwiftUI视图
│   ├── Models/           # 数据模型
│   ├── Services/         # 核心服务（录音、转录、粘贴）
│   └── Utilities/         # 工具类
├── GhostPepperTests/      # 测试
├── CleanupModelProbe/     # 模型探针工具
├── docs/                  # 文档
├── scripts/               # 构建脚本
└── project.yml           # XcodeGen配置
```

---

## 使用场景

### 1. 程序员编码

```python
# 不用打字，直接说出代码
Hold Control: "def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)"

# 自动粘贴到编辑器
```

### 2. 写作助手

```markdown
Hold Control: "The key insight is that local-first AI
represents a fundamental shift in how we think about
privacy and computation."

# 自动粘贴到写作应用
```

### 3. 会议记录

```text
Hold Control: "Action items: first, review the PR
by Friday. Second, schedule the team sync for next
week. Third, update the documentation."

# 快速记录，无需打断思路
```

---

## 总结

Ghost Pepper 代表了**本地 AI 应用**的一个优秀范例：

1. **隐私优先**：100%本地运行，数据从不离开设备
2. **直觉交互**：Hold-to-Talk 比点击录音更自然
3. **质量保证**：本地 LLM Cleanup 提升转录可读性
4. **轻量高效**：菜单栏应用，资源占用低
5. **开源透明**：代码完全可见，社区共建

**适用人群：**
- ✅ 隐私敏感用户（医疗、法律、金融）
- ✅ 程序员（快速记录代码思路）
- ✅ 作家/写手（不打断思路的语音输入）
- ✅ 企业用户（支持 MDM 部署）

**项目地址：**

| 项目 | 地址 |
|------|------|
| **GitHub** | https://github.com/matthartman/ghost-pepper |
| **下载** | GhostPepper.dmg (macOS 14.0+) |

---

*本文基于 Ghost Pepper 项目编写，发布时间：2026-04-08*
