+++
date = '2026-05-17T20:15:00+08:00'
draft = false
title = 'CLI-Anything：将任意软件变成 AI Agent 可用的 CLI 工具'
slug = 'hkuds-cli-anything-universal-cli-ai'
description = 'HKUDS/CLI-Anything 通过 7 阶段管道自动分析软件源代码，为 GIMP、Blender、FreeCAD 等任意软件生成完整的 CLI 接口，让 AI Coding Agent 直接调用。'
categories = ['技术笔记']
tags = ['AI', 'Agent', 'CLI', '开源']
+++

## 学习目标

读完本文后，你应该能够：

1. 解释 CLI-Anything 解决的是什么问题，为什么 AI Agent 需要统一的 CLI 接口
2. 在自己的环境上跑通 `/cli-anything ./gimp`，生成第一个软件 CLI
3. 用 `refine` 命令增量补充生成的 CLI 覆盖不全的地方
4. 从 CLI-Hub 安装一个社区贡献的 CLI 工具，并接入 Claude Code 或 OpenClaw
5. 判断 CLI-Anything 适不适合你当前的 AI Agent 工作流

## 目录

| → | [一句话概括](#一句话概括) | [核心特性](#核心特性) | [数字说话](#数字说话) | [一些典型场景](#一些典型场景) | [个人看法](#个人看法) | [自测](#自测) | [进阶路径](#进阶路径) |

# CLI-Anything：将任意软件变成 AI Agent 可用的 CLI 工具

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

1. **分析（Analyze）** — 扫描源代码和 GUI，映射出可操作的 API 节点
2. **设计（Design）** — 规划命令分组、状态模型、输出格式
3. **实现（Implement）** — 用 Click 构建 CLI，含 REPL、JSON 输出、撤销/重做
4. **计划测试（Plan Tests）** — 生成 TEST.md，列出单元测试和 E2E 测试方案
5. **编写测试（Write Tests）** — 实现完整测试套件
6. **文档化（Document）** — 将测试结果回填到 TEST.md
7. **发布（Publish）** — 生成 setup.py，安装到 PATH

这套流程跑完，你就能拿到一个开箱即用的 `gimp` CLI。

---

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

---

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

---

## 一些典型场景

- **Blender**：258 个命令，覆盖渲染、建模、动画全流程
- **FreeCAD**：258 个命令，17 个分组
- **Zotero**：文献管理、收藏、引用生成
- **Godot**：游戏引擎工作流，含完整 demo-game E2E 测试
- **Krita**：数字绘画、图层管理
- **QGIS**：GIS/地图创作工具

每个生成的 CLI 都自带 SKILL.md，AI agent 可以自主发现和安装，闭环。

---

## 个人看法

CLI-Anything 解决了一个很实在的问题：AI Agent 能理解代码，但真正要和某个专业软件交互时，没有统一接口。不同软件 API 风格差异巨大，GUI 软件往往根本没有 CLI——这些问题被它用一套自动化的 pipeline 统一处理了。

加上 CLI-Hub 把生态做成了"一键安装"的模式，对开发者来说省了不少重复造轮子的功夫。唯一的隐忧可能是生成的 CLI 质量参差不齐——不同软件复杂度差异太大，自动分析的效果能不能稳定还需要观察。

不过开源项目才两个月就破 3.5 万星，说明社区已经在用脚投票了。如果你有需要让 AI Agent 操作某个没有 CLI 的软件，可以试试。

---

## 常见问题

**Q: 生成的 CLI 质量怎么样？**

分软件。Blender、FreeCAD 这种有完整 API 文档的，生成质量很高。但如果是 GUI 为主、API 文档不全的软件，生成的 CLI 可能覆盖不全。用 `refine` 命令可以增量补充。

**Q: 支持 Windows 吗？**

支持。CLI-Anything 本身是 Python 写的，跨平台。生成的 CLI 也是 Python，只要目标软件能在 Windows 上跑，生成的 CLI 就能用。

**Q: 如果我用的软件不在 CLI-Hub 里怎么办？**

自己跑 `/cli-anything ./your-software` 生成。如果生成质量不满意，用 `refine` 增量补充，或者去 GitHub 提 Issue 让作者优先支持。

**Q: 生成的 CLI 会破坏我的软件吗？**

不会。生成的 CLI 只是调用软件的现有 API，不会修改软件本身。如果你想保险，先在一个测试项目上跑，确认没问题再用到生产环境。

**Q: 和手动写 CLI 比，优势在哪？**

速度。手动为一个大型软件（比如 Blender）写完整 CLI 可能需要几周。CLI-Anything 几分钟就能生成第一版，然后你用 `refine` 增量补充。省下的是"从零开始写"的时间。

---

## 自测

1. 你现在用的 AI Coding Agent 是什么？它能不能直接操作你常用的专业软件（Blender、FreeCAD、GIMP……）？如果不能，卡在哪？
2. 如果你给 Agent 加一个"操作 GIMP 做批量图片处理"的能力，你会怎么实现？先写 Skill，还是先找有没有现成的 CLI？
3. CLI-Anything 的 7 相流程里，哪一相最容易被生成的 CLI 质量卡住？如果你是自己实现，会怎么改进这一相？
4. 你有没有试过从 CLI-Hub 安装一个社区 CLI？如果试过，哪个最好用？如果没试过，今天装一个试试（比如 `cli-hub install obsidian`）。
5. 如果你在带团队，你会不会把 CLI-Anything 推给大家用？为什么？什么类型的团队适合，什么类型的不适合？

---

## 进阶路径

**阶段一：跑通第一个生成（今天）**

装好 CLI-Anything，找一个简单的软件（比如一个你写的小脚本），跑 `/cli-anything ./your-script`。感受一下：从"没有 CLI"到"有完整 CLI"需要几分钟？

**阶段二：把生成结果用进真实工作流（本周）**

选一个你每天用的软件（GIMP、Blender、FreeCAD……），生成 CLI 后接进 Claude Code 或 OpenClaw。记录哪步卡住了、哪步的文档不够清楚。

**阶段三：给社区贡献一个 CLI（本月）**

如果你生成了一个好用的 CLI，而且它不在 CLI-Hub 里，提一个 PR 把它加进去。需要做什么：写清楚依赖、测试覆盖、使用示例。目标是让下一个人 `cli-hub install` 就能直接用。

**阶段四：如果你在带团队，做一次工具选型（下个月）**

用 CLI-Anything 生成你们团队最常用的 3 个软件的 CLI，然后让团队里不同的人试。记录：谁觉得好用、谁觉得不够细、哪功能生成质量不行。最后输出一份「我们团队的 AI Agent CLI 工具清单」。

---

- **GitHub**：https://github.com/HKUDS/CLI-Anything
- **CLI-Hub**：https://clianything.cc/
