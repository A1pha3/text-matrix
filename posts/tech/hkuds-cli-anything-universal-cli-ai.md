---
title: "HKUDS/CLI-Anything：一个命令让任何软件变成AI Agent可用的CLI"
date: 2026-05-17T20:15:00+08:00
categories: ["技术笔记"]
tags: ["AI", "CLI", "Agent", "HKUDS", "开源"]
---

在 AI coding agent 大行其道的今天，几乎所有主流平台（Claude Code、Pi、OpenClaw、OpenCode……）都在用自然语言理解代码、执行任务。但它们和"真实软件"之间的接口，却始终是个问题。

**HKUDS/CLI-Anything** 试图回答这个问题：如何把**任何软件**—— GIMP、Blender、FreeCAD、Zoom、Zotero、Krita——变成 AI Agent 能直接调用的命令行工具？

<!--more-->

## 一句话概括

> **CLI-Anything**：给任意软件生成一套完整的、符合 agent 使用规范的 CLI 接口。

你只需运行一条命令：

```bash
/cli-anything ./gimp
```

背后的 7 相（7-Phase）流程就会自动完成：

1. **🔍 分析（Analyze）** — 扫描源代码和 GUI，映射出可操作的 API 节点
2. **📐 设计（Design）** — 规划命令分组、状态模型、输出格式
3. **🔨 实现（Implement）** — 用 Click 构建 CLI，含 REPL、JSON 输出、撤销/重做
4. **📋 计划测试（Plan Tests）** — 生成 TEST.md，列出单元测试和 E2E 测试方案
5. **🧪 编写测试（Write Tests）** — 实现完整测试套件
6. **📝 文档化（Document）** — 将测试结果回填到 TEST.md
7. **📦 发布（Publish）** — 生成 setup.py，安装到 PATH

这套流程跑完，你就能拿到一个开箱即用的 `gimp` CLI。

## 核心特性

### 支持平台多

Claude Code、Pi、OpenCode、OpenClaw、Goose、Codex、GitHub Copilot CLI、Qodercli……基本上主流 AI coding 平台都有插件或 skill。

安装方式也很简单，以 Claude Code 为例：

```bash
/plugin marketplace add HKUDS/CLI-Anything
/plugin install cli-anything
```

以 OpenClaw 为例，复制 skill 文件即可：

```bash
mkdir -p ~/.openclaw/skills/cli-anything
cp CLI-Anything/openclaw-skill/SKILL.md ~/.openclaw/skills/cli-anything/
```

然后直接喊：`@cli-anything build a CLI for ./gimp`

### CLI-Hub：社区 CLI 的应用商店

项目还搭了一个 [CLI-Hub](https://hkuds.github.io/CLI-Anything/)：

```bash
pip install cli-anything-hub
cli-hub install <name>
```

现在已经有数十个社区贡献的 CLI 工具——Blender、FreeCAD、QGIS、Godot、Zotero、Obsidian、Draw.io……直接 install 就能用，不用自己生成。

### 迭代优化（Refine）

初次生成可能覆盖不全，可以用 refine 命令增量补充：

```bash
/cli-anything:refine ./gimp "batch processing and filters"
```

每次 refine 都是非破坏性的增量扩展，可以反复跑直到满意为止。

### 输出双模式

CLI 同时支持 `--json` 和人类可读文本两种输出模式。Agent 用 JSON 确保稳定性，人类查看用普通文本，两不耽误。

## 数字说话

根据 GitHub API 数据（2026-05-17）：

| 指标 | 数值 |
|------|------|
| ⭐ Stars | **35,254** |
| 🍴 Forks | 3,465 |
| 编程语言 | Python |
| 创建时间 | 2026-03-08 |
| License | Apache 2.0 |

从 3 月初上线到 5 月中旬，两个多月拿下 3.5 万星，增长速度相当可观。

## 一些典型场景

- **Blender**：258 个命令，覆盖渲染、建模、动画全流程
- **FreeCAD**：258 个命令，17 个分组
- **Zotero**：文献管理、收藏、引用生成
- **Godot**：游戏引擎工作流，含完整 demo-game E2E 测试
- **Krita**：数字绘画、图层管理
- **QGIS**：GIS/地图创作工具

每个生成的 CLI 都自带 SKILL.md，AI agent 可以自主发现和安装，闭环。

## 个人看法

CLI-Anything 解决了一个很实在的问题：AI Agent 能理解代码，但真正要和某个专业软件交互时，没有统一接口。不同软件 API 风格差异巨大，GUI 软件往往根本没有 CLI——这些问题被它用一套自动化的 pipeline 统一处理了。

加上 CLI-Hub 把生态做成了"一键安装"的模式，对开发者来说省了不少重复造轮子的功夫。唯一的隐忧可能是生成的 CLI 质量参差不齐——不同软件复杂度差异太大，自动分析的效果能不能稳定还需要观察。

不过开源项目才两个月就破 3.5 万星，说明社区已经在用脚投票了。如果你有需要让 AI Agent 操作某个没有 CLI 的软件，可以试试。

- **GitHub**：https://github.com/HKUDS/CLI-Anything
- **CLI-Hub**：https://clianything.cc/