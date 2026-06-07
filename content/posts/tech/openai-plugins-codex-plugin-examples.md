---
title: "openai/plugins 深度解析：OpenAI 官方维护的 Codex 插件示例集合，Codex 时代的'看这一个仓库就够'模板"
date: "2026-06-07T15:03:00+08:00"
slug: "openai-plugins-codex-plugin-examples"
description: "2026-06-07 GitHub Trending 当日榜 #5，1,845 stars / 单日 +213。不要被 stars 数字骗了——这是 OpenAI 自己维护的 Codex 插件'官方模板集'，figma/notion/build-ios-apps/build-macos-apps/build-web-apps/expo 等 7 个高质量范例决定了 Codex 插件的'事实标准'长什么样。"
draft: false
categories: ["技术笔记"]
tags: ["OpenAI", "Codex", "Plugin", "MCP", "AI Agent", "开源项目深拆"]
toc: true
---

## 这篇文章在回答什么

`openai/plugins` 在 2026-06-07 出现在 GitHub Trending 当日榜第 5 名（1,845 stars / 单日 +213）。它的 star 数绝对值不大（和今天 trending 榜的其他项目相比），但**它是 OpenAI 官方维护的 Codex 插件示例仓库**——这意味着它定义了 Codex 插件的"事实标准"长什么样。

README 全文只有 100 字，但每个字都重要：

> This repository contains a curated collection of Codex plugin examples. Each plugin lives under `plugins/<name>/` with a required `.codex-plugin/plugin.json` manifest and optional companion surfaces such as `skills/`, `.app.json`, `.mcp.json`, plugin-level `agents/`, `commands/`, `hooks.json`, `assets/`, and other supporting files.

——三件事：

1. **结构是约定的**：`plugins/<name>/` + `.codex-plugin/plugin.json` 是 manifest 入口
2. **能力面是组合的**：单个 plugin 可以挂 skills / agents / commands / hooks / assets / MCP
3. **OpenAI 自己在写范例**：figma、notion、build-ios-apps、build-macos-apps、build-web-apps、expo、netlify、remotion、google-slides

## 为什么这个仓库会 trending

`openai/plugins` 跟 Claude Code 的 `anthropics/skills` 仓库是同一种东西——**生态里"插件规范"这件事需要一个被维护的官方范例集**。Star 数小是因为它不解决具体问题，但所有想要做 Codex 插件的开发者都要 fork 它、改 manifest、参考它的目录约定。

## 一个 Codex plugin 的最小结构

按 README 描述的目录约定：

```
plugins/<name>/
├── .codex-plugin/
│   └── plugin.json       # required: manifest
├── skills/               # optional: 行为规范
├── .app.json             # optional: 配套 app 元数据
├── .mcp.json             # optional: 挂的 MCP server
├── agents/               # optional: 插件专属子 agent
├── commands/             # optional: 斜杠命令
├── hooks.json            # optional: 生命周期 hook
└── assets/               # optional: 资源文件
```

这个结构和 Claude Code 的 `anthropics/skills`（`.claude/skills/...`）有强映射关系，也和 OpenClaw 的 `clawhub` 规范兼容。它不是 Codex 独有，而是 OpenAI 在推的"**OpenAI 生态统一插件规范**"。

## 9 个高信号范例

仓库自带 9 个高质量范例，按用途分类：

| 范例 | 用途 | 关键能力 |
|------|------|---------|
| `figma` | 设计与代码同步 | `use_figma`、Code to Canvas、Code Connect、design system rules |
| `notion` | 知识管理 | 规划、研究、会议、知识捕获 |
| `build-ios-apps` | iOS 开发 | SwiftUI 实现、重构、性能、调试 |
| `build-macos-apps` | macOS 开发 | SwiftUI/AppKit 工作流、build/run/debug 循环、打包 |
| `build-web-apps` | Web 开发 | 部署、UI、支付、数据库 |
| `expo` | 跨端移动 | Expo / React Native / SDK 升级 / EAS / Codex Run |
| `netlify` | 部署 | Netlify 工作流 |
| `remotion` | 视频生成 | React 视频程序化生成 |
| `google-slides` | 演示文稿 | 编程化生成 slide |

读这 9 个范例目录就能看出 OpenAI 押的几个方向：**设计协作 + 知识管理 + 全栈应用构建 + 多端开发 + 部署**。基本就是"个人开发者用 AI 写完整产品"的整个链条。

## 和 Claude Code / OpenClaw 插件生态的关系

`openai/plugins` 不是孤岛——它和几个生态的对应关系如下：

| 平台 | 插件规范 | 官方范例仓库 |
|------|---------|-------------|
| **Codex** | `.codex-plugin/plugin.json` | `openai/plugins` (本仓库) |
| **Claude Code** | `SKILL.md` + `.claude-plugin/` | `anthropics/skills` |
| **OpenClaw** | `clawhub install` | `clawhub` registry |
| **通用 agent skill** | `agentskills.io` 规范 | `vercel-labs/skills` |

OpenAI 这里做了一个值得注意的选择：**把自己规范直接叫 "plugin" 而不是 "skill"**（虽然目录里也有 `skills/`）。这是市场用语差异——Claude Code / OpenClaw 偏 "skill"（技能），OpenAI 偏 "plugin"（插件）。功能上几乎可以 1:1 对应。

## 谁该用这个仓库

1. **想做 Codex 插件的开发者**：直接 fork，改 `plugin.json` 适配自己的工具，不要从零造结构
2. **做 AI 工具产品的厂商**：看 figma/notion/expo 这 3 个范例是怎么把 MCP server、design system rules、`use_figma` 组合起来的——这是"AI agent 调用第三方 SaaS"的范式
3. **跨 agent 平台兼容**：研究 manifest 字段，看你的 plugin 如何同一份代码既能在 Codex 跑也能在 OpenClaw 跑

## 安装 / 使用

仓库本身是"参考实现"，没有 npm install。可直接：

```bash
git clone https://github.com/openai/plugins
cd plugins
ls plugins/
# 然后挑一个范例进 plugins/<name>/ 读
```

## 参考

- 仓库：[github.com/openai/plugins](https://github.com/openai/plugins)
- 对照生态：`anthropics/skills`（Claude Code）、`clawhub`（OpenClaw）、`vercel-labs/skills`（通用 agentskills.io）
