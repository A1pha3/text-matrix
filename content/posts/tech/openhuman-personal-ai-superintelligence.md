---
title: "OpenHuman：你的个人AI超智能体，私有、简单、极其强大"
date: "2026-05-14T16:05:00+08:00"
slug: "openhuman-personal-ai-superintelligence"
description: "OpenHuman是一个开源AI智能体，设计为桌面端个人助理，通过118+第三方集成、Memory Tree本地记忆、Obsidian Wiki知识库和TokenJuice智能压缩，让AI在几分钟内真正了解你，而不是几周。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "OpenHuman", "本地记忆", "Obsidian", "Rust"]
---

# OpenHuman：你的个人AI超智能体，私有、简单、极其强大

## 项目概览

**OpenHuman** 是由 tinyhumansai 开发的开源智能体项目，定位为「个人AI超智能体」——Private、Simple、extremely powerful。该项目当前处于 Early Beta 阶段，采用 Rust + Tauri/CEF 构建桌面端体验，、星数 6,595，Forks 532。

核心差异点在于：它不是又一个命令行 Agent，而是真正具有桌面形象（Mascot）的 AI 助理，能加入 Google Meet 作为真实参与者、记住用户跨周上下文、在后台持续思考，且所有数据优先本地存储在 SQLite 和 Obsidian 兼容的 Markdown 知识库中。

## 核心特性

### Memory Tree + Obsidian Wiki

这是 OpenHuman 最核心的差异化设计。Karpathy 曾在推特分享他用 Obsidian 构建 LLM 知识库的工作流，而 OpenHuman 将这个模式自动化了：

- 连接 Gmail、Notion、GitHub、Slack 等118+应用后，**auto-fetch** 每20分钟拉取一次最新数据
- 所有数据被规范化为 ≤3k token 的 Markdown 块，评分后折叠进层级摘要树，存储在本机 SQLite
- 同一批数据同时以 `.md` 文件形式出现在 Obsidian 兼容的 Vault 中，用户可以直接打开、浏览和编辑

换言之，Agent 的记忆就是你的 Obsidian 知识库，两者是同一个东西。

### TokenJuice 智能压缩

每次工具调用、爬取结果、邮件正文、搜索负载，都会经过一层 token 压缩：HTML 转 Markdown、长 URL 缩短、非 ASCII 字符移除等。官方宣称可节省最高 80% 的 tokens 和延迟。

### 内置工具开箱即用

不同于「安装插件才能读取文件」的 Agent，OpenHuman 默认绑定了：网络搜索、Web 抓取、完整 coder 工具集（文件系统、git、lint、test、grep）、本地语音（STT 进、ElevanLabs TTS 出），以及模型路由（自动将任务分配给合适的 LLM）。

### 可选本地 AI

支持通过 Ollama 接入本地模型，处理设备上的工作负载，不依赖云端。

## 安装方式

项目提供了各平台安装脚本：

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/tinyhumansai/openhuman/main/scripts/install.sh | bash

# Windows
irm https://raw.githubusercontent.com/tinyhumansai/openhuman/main/scripts/install.ps1 | iex
```

也可以直接访问 [tinyhumans.ai/openhuman](https://tinyhumans.ai/openhuman) 下载 DMG/EXE 安装包。

## 技术栈与构建要求

- **语言**：Rust（Tauri/CEF 桌面壳）+ Node.js（Web UI）
- **依赖**：Node.js 24+、pnpm 10.10.0、Rust 1.93.0（rustfmt + clippy）、CMake
- **开发命令**：`pnpm dev`（仅 UI）、`pnpm --filter openhuman-app dev:app`（完整桌面壳）
- **贡献流程**：Fork → PR，需通过 `pnpm typecheck`、`pnpm format:check`、`cargo check -p openhuman --lib`

## 与其他 Agent 框架的对比

OpenHuman 主打的是「零配置上手 + 本地记忆 + 完整 UI」，对比 Hermes Agent、OpenClaw 等开源方案，优势在于：

- UI-first：无需折腾终端，开箱即用的桌面体验
- 118+ OAuth 一键集成：没有 BYO 痛苦
- 20 分钟自动同步 + Memory Tree：冷启动从几天缩短到分钟级
- TokenJuice + 模型路由：单订阅搞定成本控制

## 适用场景

- 需要 AI 助理真正理解你日常工作的用户（邮件、日历、文档、代码）
- 希望知识本地化、不全部上云的开发者
- 需要在 Google Meet 中有 AI 代理参与的场景
- 想把 Karpathy 的 Obsidian Wiki 工作流自动化但不想自己写脚本的人

## 当前局限

- 仍处于 Early Beta，功能可能会有破坏性变化
- Web 端仅支持 Chrome 134+（Windows/macOS）
- 依赖云端 LLM 订阅（虽然支持 Ollama，但默认仍需外部 API Key）

---

**延伸阅读**：[OpenHuman 官方文档](https://tinyhumans.gitbook.io/openhuman/) · [GitHub 仓库](https://github.com/tinyhumansai/openhuman)