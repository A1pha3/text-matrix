---
title: "Palmier Pro 深度上手：macOS 26 上第一个面向 AI Agent 的开源视频编辑器"
date: "2026-06-19T21:04:05+08:00"
slug: "palmier-pro-macos-ai-video-editor-mcp-guide"
description: "Palmier Pro 是 YC S24 团队发布的开源 macOS 视频编辑器，以 Swift 原生构建并通过本地 MCP 服务器把 Claude / Codex / Cursor 接入时间线。本文从安装、MCP 配置、典型协作流程、闭源边界四个角度拆解它为何值得看。"
draft: false
categories: ["技术笔记"]
tags: ["视频编辑", "macOS", "MCP", "AI Agent", "Swift"]
---

## 一句话定位

Palmier Pro 是 YC S24 团队 Palmier 在 2026 年开源的 macOS 视频编辑器。它不是又一个 CapCut 克隆，而是把"AI Agent 与时间线协作"当作一等公民来做：本地 HTTP MCP 服务器（端口 19789）让 Claude Code、Codex、Cursor 都能直接读写工程文件，编辑器本体用 Swift 从头写，对标的是 Adobe Premiere Pro。

## 平台与开源边界

- 平台：**macOS 26 (Tahoe) + Apple Silicon**。Intel Mac 不支持。
- 协议：**GPLv3**。视频编辑器、MCP 服务器、Agent 对话全部开源；唯一闭源的是"生成式 AI 处理"部分（接入 Seedance、Kling、Nano Banana Pro 的后端）。
- 价格：编辑器本体与 MCP 免费，无登录即可使用；生成式 AI 走订阅。
- 商业化：作者把 AI 部分做成付费，编辑器本体留住开源基本盘，这是 YC 类项目里相对干净的分割方式。

## 三块核心能力

### 1. Swift 原生时间线

对标 Premiere Pro，作者刻意避开 Electron 路线，全部用 Swift 重写 UI 与渲染管线。带来的直接好处是 macOS 系统手势、Metal 加速、Finder 拖拽能直接复用，劣势是平台被锁死在 Apple Silicon。

### 2. 内置生成式 AI

时间线内可直接调用 SOTA 视频/图像模型：

- **视频生成**：Seedance、Kling
- **图像生成**：Nano Banana Pro

不需要切出编辑器就能补素材，本质上把"找素材"压缩成"时间线里的几段生成指令"。

### 3. MCP 服务器（最值得关注的部分）

打开应用后，App 会在 `http://127.0.0.1:19789/mcp` 起一个 HTTP MCP Server（注意：本地回环，只在本机可访问）。这样任何 MCP 兼容客户端都能把时间线当成可编程对象操作。

**Claude Code**

```bash
claude mcp add --transport http palmier-pro http://127.0.0.1:19789/mcp
```

**Codex**

```bash
codex mcp add palmier-pro --url http://127.0.0.1:19789/mcp
```

**Cursor**

应用内 `Help` → `MCP Instructions` → `Install in Cursor` 一键写 `~/.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "palmier-pro": {
      "type": "http",
      "url": "http://127.0.0.1:19789/mcp"
    }
  }
}
```

**Claude Desktop**

README 标注了 `.mcpb`（MCP Bundle），`Help` → `MCP Instructions` → `Install in Claude Desktop` 一键加载 Desktop Extension。

## 典型协作流程

1. 在 Cursor 里让 Agent 读取当前时间线（通过 MCP 暴露的 `get_timeline` / `list_clips` 类工具）。
2. Agent 根据脚本生成补帧素材（Seedance）或封面图（Nano Banana Pro）。
3. 通过 MCP 调用 `add_clip` / `set_in_out` 把素材塞回时间线指定位置。
4. 人在编辑器里做最终审片、配音、转场。

这等于把"让 AI 帮我剪视频"从 prompt 玄学变成可追溯的工具调用链：每一步 Agent 写了哪个文件、插到哪个轨道都有 MCP 日志可查。

## 适用边界

- ✅ **适合**：Apple Silicon 用户、需要"AI 代理直接改时间线"的短视频 / 演示 / 教程工作流。
- ❌ **不适合**：跨平台团队（Windows / Linux 路径被锁）、长片专业调色（Premiere / DaVinci 仍是主战场）、完全离线的纯本地素材剪辑（生成式 AI 依赖云端推理）。
- ⚠️ **关注点**：MCP Server 只在 `127.0.0.1` 监听，理论上不存在远程攻击面，但仍需关注未来开放 LAN 监听时的权限模型。

## 写给读者的判断

如果你正在做 AI Agent × 创意工具的整合，Palmier Pro 提供了少见的"完整代码 + 真实闭源边界 + 真实 YC 团队背书"组合。它的 MCP 设计可以当作参考实现：把一个 GUI 应用的内部状态以 HTTP MCP 暴露给 coding agent，工具描述清晰、协议对齐现成标准，比临时写 CLI wrapper 优雅得多。

如果你只是想找一个"替代 CapCut 的 macOS 编辑器"，可以先看演示视频再决定——它的 AI 部分需要订阅，免费版只是编辑器本体。
