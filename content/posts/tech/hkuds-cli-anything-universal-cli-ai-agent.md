---
title: "CLI-Anything：用AI代理的通用接口桥接世界所有软件"
date: "2026-05-19T20:25:00+08:00"
slug: "cli-anything-universal-cli-ai-agent"
description: "CLI-Anything是香港大学DDS实验室推出的开源项目，通过为各类软件生成标准化CLI接口，让AI代理（Agent）能够以结构化方式控制任意软件，目前支持18+应用并提供可扩展的CLI-Hub生态。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "CLI", "Hong Kong University", "开源工具", "工作流自动化"]
---

## 先给判断

CLI-Anything 解决的不是一个技术细节，而是一个生态问题：AI 代理很强，但它们不知道怎么处理 Word 文档、3D 建模软件、CAD 工具——因为这些软件没有 AI 友好的接口。这个项目为闭源软件生成 AI 可发现的 CLI 封装层，让 AI 代理用自然语言控制一切。

它的关键价值不是某个具体 CLI，而是**让 AI 代理能够"看到"并"操作"非 API 软件的标准路径**。如果你的工作流涉及大量闭源工具，这个项目值得关注。

<!--more-->

## 系统地图

```
┌─────────────────────────────────────────────────────────────────┐
│                      AI 代理 (Pi, OpenClaw, nanobot, Cursor...)  │
└────────────────────────────┬────────────────────────────────────┘
                             │ 标准CLI调用
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        CLI-Anything 框架                        │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Blender CLI   │  │ FreeCAD CLI  │  │ Zotero CLI   │  ...    │
│  │ 101 commands  │  │ 258 commands │  │ 48 commands  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  CLI-Hub Registry (https://hkuds.github.io/CLI-Anything/)       │
└─────────────────────────────────────────────────────────────────┘
```

## 核心能力

### 1. CLI 生成框架

CLI-Anything 为每个软件生成一套标准化的 CLI 工具，包含：

- **命令发现**：`--help`自动解析，AI 可直接发现可用操作
- **参数约束**：类型安全，AI 不会传入非法参数
- **输出标准化**：JSON 输出，方便 AI 解析和处理
- **SKILL.md 生成**：每个 CLI 自动生成 AI 可读的技能描述文件

### 2. CLI-Hub 生态

通过`pip install cli-anything-hub`，用户可以：

```bash
# 浏览所有可用CLI
cli-hub browse

# 安装特定CLI
cli-hub install blender

# 更新CLI
cli-hub update zotero
```

### 3. 支持的软件（部分）

| 软件 | 命令数 | 场景 |
|------|--------|------|
| Blender | 101+ | 3D 建模、渲染、动画 |
| FreeCAD | 258 (17 组) | CAD、工程建模 |
| Zotero | 48 | 文献管理、引用 |
| Godot | 完整 | 游戏引擎自动化 |
| Kdenlive | 完整 | 视频编辑 |
| QGIS | 完整 | GIS 地图制作 |
| Obsidian | 完整 | 知识管理 |
| Unreal Insights | 完整 | 游戏性能分析 |

总计支持 18+应用，覆盖 3D 建模、GIS、视频、文献、游戏开发等多个领域。

### 4. 多智能体支持

CLI-Anything 生成的 CLI 可以与以下 AI 代理集成：

- Pi, OpenClaw, nanobot
- Cursor, Claude Code
- GitHub Copilot, Antigravity
- Gemini CLI, OpenCode, Aider, Windsurf, Kimi Code

## 技术架构

### CLI Harness 结构

每个 CLI 的生成遵循统一框架（Harness），核心是：

1. **发现层**：解析软件 CLI 接口
2. **适配层**：转换为标准化 CLI 格式
3. **输出层**：生成 AI 可解析的 JSON/文本输出
4. **描述层**：生成 SKILL.md 供 AI 发现

### 目录结构

```
CLI-Anything/
├── harnesses/           # 各软件CLI实现
│   ├── blender/
│   ├── freecad/
│   ├── zotero/
│   └── ...
├── hub/                 # CLI-Hub包
├── guides/              # 详细指南
└── skills/              # AI技能描述
```

## 快速开始

### 安装

```bash
# 安装CLI-Hub
pip install cli-anything-hub

# 浏览可用CLI
cli-hub browse

# 安装特定CLI
cli-hub install blender
```

### AI 代理中使用

以 OpenClaw 为例：

```bash
# 在OpenClaw中激活Blender CLI技能
npx skills add HKUDS/CLI-Anything --skill blender -g -y

# 之后可以自然语言控制Blender
"创建一个半径2单位的球体"
```

## 任务流案例：让 AI 代理创建 Blender 3D 场景

```
1. 开发者向AI代理说："帮我创建一个包含球体、立方体和灯光的简单3D场景"
2. AI代理加载 Blender CLI 技能
3. 通过技能描述发现可用命令：blender create-object, blender set-material, etc.
4. AI按顺序调用：
   - blender create-object --type sphere --radius 2 --name MySphere
   - blender create-object --type cube --size 1 --name MyCube
   - blender create-light --type sun --energy 2
5. Blender 自动执行所有命令，输出完成场景
```

## 适用边界

**该用：**
- 需要 AI 代理控制非 API 软件（闭源工具、3D 软件等）
- 想让 AI 自动化复杂的多软件工作流
- 在研究或生产中需要批量处理 3D 资产

**不该用：**
- 软件本身已有良好 API——直接用 API 更稳定
- 只用命令行工具的简单场景——原生 CLI 更直接
- 需要实时交互的 GUI 操作——CLI 不适合做像素级控制

## 结论

CLI-Anything 代表了 AI 代理向真实世界软件生态扩展的一个重要方向：通过为闭源软件生成标准化接口，让 AI 代理不再受限于有 API 的软件。

它的关键价值是**降低 AI 代理操作真实软件的门槛**——不需要为每个软件写专门的集成，只需要一个标准化的 CLI 框架。

项目由香港大学 DDS 实验室维护，代码质量较高（有测试覆盖、CI 流程），社区活跃。如果你的 AI 工作流需要与大量闭源软件交互，这个项目值得关注。

---

**仓库信息**：https://github.com/HKUDS/CLI-Anything | Stars: 37,313 | License: Apache 2.0 | 语言： Python