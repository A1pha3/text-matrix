---
title: "CLI-Anything：让所有软件变成Agent可调用的CLI工具"
date: "2026-05-20T15:51:00+08:00"
slug: "cli-anything-agent-native-software-harness"
description: "HKUDS出品的AI Agent工具链，通过为各种软件生成标准化CLI接口，让AI Agent能够以统一方式调用任意软件。目前支持18个领域的200+工具（CAD、3D建模、视频编辑等），通过SKILL.md规范和CLI-Hub实现一键安装与版本管理，测试覆盖2,269个用例。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "CLI-Anything", "工具集成", "Agent工作流", "Python"]
---

# CLI-Anything：让所有软件变成 Agent 可调用的 CLI 工具

## 一句话判断

CLI-Anything 通过为各类软件生成符合 SKILL.md 规范的 CLI 接口，解决了"AI Agent 无法标准化调用非 API 软件"的难题——200+工具覆盖 CAD、3D 建模、视频编辑等，用一条命令让 AI 与任何软件交互。

## 项目概览

| 指标 | 数据 |
|------|------|
| GitHub | [HKUDS/CLI-Anything](https://github.com/HKUDS/CLI-Anything) |
| Stars | 38,051 |
| 语言 | Python ≥3.10 |
| 测试覆盖率 | 2,269 个用例全部通过 |
| CLI-Hub | [clianything.cc](https://clianything.cc/) |

## 核心问题：AI Agent 与软件的断链

目前大多数 AI Agent 能调用 API（Slack、Web API 等），但无法调用大量**没有标准化 API 接口的软件**——Blender、Audacity、QGIS、FreeCAD、Inkscape 等。这意味着 Agent 的能力被限制在有 API 的工具范围内。

CLI-Anything 的核心思路是：**不管目标软件原本怎么暴露能力，都给它包装成一个标准 CLI**，再通过 SKILL.md 告诉 Agent 怎么用。

## 工作原理

### 1. Agent Harness — 为每个软件写"桥接层"

对每个目标软件（如 Blender、QGIS），CLI-Anything 在`{software}/agent-harness/`目录下创建一个桥接模块。它的职责是：
- 把软件的命令行接口转换为标准 JSON 输出
- 实现健康检查、参数验证、错误标准化
- 通过`SKILL.md`描述工具能力，供 Agent 读取

```
blender/agent-harness/
├── SKILL.md          # 工具描述，Agent读取的接口规范
├── cli.py            # CLI包装器
├── harness.py        # Blender交互逻辑
└── test_blender.py   # 测试用例
```

### 2. SKILL.md — Agent 的"读懂工具"规范

每个 harness 的核心是 SKILL.md，它告诉 Agent：
- 这个工具能做什么（功能描述）
- 怎么调用（命令格式、参数）
- 什么情况下适合用它（适用边界）
- 常见错误和注意事项

这是一个结构化的"工具说明书"，Agent 读取后即可正确使用该工具，无需人工介入每次调用。

### 3. CLI-Hub — 一键安装管理

通过 CLI-Hub，用户可以：
```bash
pip install cli-anything-hub
cli-hub install blender     # 安装Blender的CLI harness
cli-hub list               # 查看所有可用工具
```

支持的工具覆盖 18 个领域，包括：CAD（QGIS）、3D 建模（Blender、FreeCAD）、视频（Audacity、Kdenlive）、图像处理（GIMP、Inkscape）等。

### 4. 支持多种 Agent

CLI-Anything 不只是给某一个 Agent 用——它通过标准化接口，同时支持：
- OpenClaw（本文所在平台）
- Claude Code
- Cursor
- Codex（OpenAI）
- Gemini CLI
- Factory Droid
- OpenCode
- GitHub Copilot CLI

## 技术亮点

**标准化输出**：无论底层软件怎么输出，CLI 包装层统一为结构化 JSON 或人类可读文本两种模式，通过`--json`和`--human`参数切换。

**测试驱动**：2,269 个测试用例覆盖 unit test 和 e2e，确保每个 harness 在不同场景下正确工作。

**贡献友好**：有完整的[CONTRIBUTING.md](https://github.com/HKUDS/CLI-Anything/blob/main/CONTRIBUTING.md)，任何软件都可以提交新的 harness 申请，社区活跃度高（640 Commits）。

## 快速开始

```bash
# 安装CLI-Hub
pip install cli-anything-hub

# 浏览可用工具
cli-hub search <keyword>

# 安装特定工具的harness
cli-hub install blender

# 升级
cli-hub update
```

## 适用边界

**适合：**
- 想让 AI Agent 操作非 API 软件（3D、视频、CAD 等）的场景
- 需要标准化工具接口，方便切换不同 Agent 的场景
- 开发者想为某软件贡献一个 agent harness

**不适合：**
- 目标软件本身已有高质量 API 的情况（直接用 API 更稳定）
- 只有简单任务，不需要复杂工具集成的场景

## 相关项目

- [OpenHuman](https://github.com/tinyhumansai/openhuman)：本地优先的个人 AI Super Intelligence，同样支持通过 Agent 方式操作各种服务
- [12-factor-agents](/posts/tech/12-factor-agents-production-llm-guide/)：构建生产级 LLM Agent 的核心原则
- [Claude Code Skills](/posts/tech/andrej-karpathy-skills-guide/)：提升 Claude Code 行为的实战指南