+++
date = '2026-05-24T23:07:00+08:00'
draft = false
title = 'cmux：Ghostty 内核 macOS 终端，AI 编程助手专属分屏'
slug = 'cmux-ghostty-terminal-ai-coding'
description = 'cmux 是专为 AI 编程助手打造的终端增强工具，基于 Ghostty 内核，提供分屏、通知等 macOS 专属功能，让 AI Agent 与终端交互更流畅。'
categories = ['技术笔记']
tags = ['终端', 'macOS', 'AI 编程', '开发工具']
+++
# cmux：Ghostty 内核 macOS 终端，AI 编程助手专属分屏+通知

> 当终端开始理解 AI 工作流，效率不只是提升一点。

## 📌 一句话概括

`cmux`（全称 Claude Multi-UX）是 manaflow-ai 出品的基于 Ghostty 的 macOS 终端模拟器，内置 AI 编程助手专用分屏布局、垂直标签页和智能通知系统，18K+ Star。

## 🌟 核心亮点

- **Ghostty 内核**：Apple Silicon 原生优化，GPU 渲染，启动速度极快
- **AI 分屏布局**：一键把终端分成「代码编辑 + AI 对话」双视图
- **垂直标签页**：多会话管理更高效，不乱
- **通知集成**：Agent 执行完毕、编译错误自动推 macOS 通知
- **18K Star**：Trending 第十名，成熟度高

## 🔧 安装与配置

```bash
# 安装（需 macOS）
brew install cmux

# 或从 GitHub Releases 下载 .app
open https://github.com/manaflow-ai/cmux/releases
```

## 🎯 AI 编程助手工作流

### 分屏模式
```
┌─────────────────────┬──────────────────────┐
│   编辑器 / 代码     │   Claude / GPT 会话  │
│                     │                      │
│   (vim/vscode)      │   (pi / claude CLI)  │
└─────────────────────┴──────────────────────┘
```
在 cmux 中按 `Cmd+D` 开启分屏，`Cmd+Shift+D` 切换主从位置。

### Agent 通知集成
```bash
# 设置编译完成后通知
export CMUX_NOTIFY=on
make build && cmux-notify "构建完成！"
```

## 📊 技术对比

| 特性 | cmux | iTerm2 | Terminal.app |
|------|------|--------|-------------|
| AI 分屏 | ✅ | ❌ | ❌ |
| Apple Silicon 优化 | ✅ 原生 | ⚠️ 通用 | ⚠️ 通用 |
| GPU 渲染 | ✅ | ❌ | ❌ |
| 启动速度 | <100ms | ~500ms | ~300ms |
| 垂直标签 | ✅ | ⚠️ 需配置 | ❌ |
| 通知系统 | ✅ | ⚠️ 有限 | ⚠️ 有限 |

## 💡 使用场景

1. **结对编程**：左边 VSCode，右边 Claude Terminal
2. **Agent 监控**：跑 pi agent，左边看日志，右边对话
3. **多项目并行**：垂直标签管理多个项目，互不干扰

## ⚠️ 注意事项

1. **仅支持 macOS**，Linux/Windows 暂无计划
2. 需要 macOS 13+（Ventura 及以上）
3. 分屏模式需要全屏或大屏窗口效果最佳

## 🔗 相关链接

- GitHub: https://github.com/manaflow-ai/cmux
- 官网： https://manaflow.ai/cmux

---

*Tags: #终端 #macOS #Ghostty #AI 编程 #分屏 #效率工具*