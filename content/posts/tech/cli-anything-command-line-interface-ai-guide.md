---
title: "CLI-Anything: 一条命令让任意软件变身AI Agent可控工具"
date: "2026-05-17T20:10:00+08:00"
slug: "cli-anything-command-line-interface-ai-guide"
description: "CLI-Anything 是一个开源的CLI自动生成框架，通过7阶段流水线将任意软件（Blender、GIMP、LibreOffice等）转化为AI Agent可直接控制的命令行工具，支持Claude Code、OpenClaw、Pi等主流平台，GitHub星标超3.5万。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "CLI", "Claude Code", "OpenClaw", "Python", "自动化工具", "Blender"]
---

# CLI-Anything: 一条命令让任意软件变身 AI Agent 可控工具

> **目标读者**：有基础编程经验的开发者，已了解 AI Agent 基本概念，想把 AI Agent 能力扩展到真实专业软件
> **预计阅读时间**：25 分钟
> **前置知识**：[AI Agent 入门指南](/posts/tech/ai-agents-for-beginners-microsoft-complete-guide.md) ⭐

---

## 📝 概念定义

### 一句话定位

**CLI-Anything** 是港大 HKUDS 实验室开源的 CLI 自动生成框架——给它一个软件代码库，它就能自动生成一套完整的命令行接口（CLI），让 AI Agent 能够以结构化、可靠的方式控制任意专业软件。

### 类比理解

> 💡 就像 USB 转接头让各种设备都能接入电脑一样，CLI-Anything 把任意软件「转接」成 AI Agent 能理解的命令行接口。不同的是，它不是简单桥接，而是**重新为软件生成一套完整的 CLI 设计**，包含命令分组、状态管理、测试和文档。

### 为什么需要它

AI Agent 很擅长推理，但在实际使用专业软件时存在根本障碍：GUI 自动化脆弱、需要 API 的软件受限于接口、没有 API 的软件完全无法控制。

CLI-Anything 给出了第三条路——不需要 API，不需要截图，点击一下就生成生产级的 CLI 层，把专业软件的能力暴露给 Agent。

---

## 🎯 核心场景

### 场景 1：让 Agent 操作真实专业软件

**问题**：Agent 需要生成一张 Blender 渲染图，但 Blender 是 GUI 软件，Agent 无法操作。

**解决**：

```bash
# Claude Code 中，一条命令生成 Blender CLI
/cli-anything /path/to/blender

# 然后 Agent 可以直接用命令行控制 Blender
cli-anything-blender render --scene kitchen --output ./render.png --engine CYCLES
```

生成的 CLI 直接调用 Blender 真实后端，没有任何模拟层——渲染出来的东西和手动操作的结果完全一致。

### 场景 2：统一多个 API 为一个 CLI

**问题**：一个项目需要调用多个云服务 API，每个都有不同的 SDK 和接口，Agent 每次都要拼装不同的调用逻辑。

**解决**：把 API 文档或 SDK 代码喂给 CLI-Anything，它会生成一个统一的 CLI，封装所有底层调用：

```bash
# 一个命令，管理所有API
cli-anything-exa search "AI agent趋势" --limit 10 --output json
cli-anything-exa find-similar "doc-url" --limit 5
```

### 场景 3：替换 GUI 自动化

**问题**：用截图+点击的 RPA 方案控制软件脆弱且不稳定。

**解决**：用 CLI 替代 GUI 操作，结构化、可测试、可重复：

```bash
# 不再是截图点击
# 而是直接命令行
cli-anything-gimp layer add --name "背景" --type solid --color "#1a1a2e"
cli-anything-gimp filter blur --radius 5 --layer "背景"
cli-anything-gimp export --format png --quality 95 --output poster.png
```

---

## 🚀 快速开始

### 环境检查清单

- [ ] Python 3.10+
- [ ] 目标软件已安装（Blender、GIMP 等）
- [ ] 支持的 AI Agent 平台之一

### 支持的平台

| 平台 | 安装方式 | 备注 |
| ---- | -------- | ---- |
| **Claude Code** | Plugin Marketplace | 官方支持 |
| **Pi Coding Agent** | Extension 脚本 | 社区支持 |
| **OpenClaw** | SKILL.md 复制 | 社区支持 |
| **OpenCode** | 命令文件复制 | 实验性 |
| **Codex** | 安装脚本 | 实验性 |
| **Goose** | CLI Provider | 社区支持 |
| **GitHub Copilot CLI** | Plugin | 社区支持 |
| **Qodercli** | Plugin 注册 | 社区支持 |

### 以 Claude Code 为例

**第一步：添加市场**

```bash
/plugin marketplace add HKUDS/CLI-Anything
```

**第二步：安装插件**

```bash
/plugin install cli-anything
```

**第三步：生成 CLI**

```bash
# 生成 GIMP 的完整 CLI（7个阶段全部自动执行）
/cli-anything ./gimp
```

这条命令执行完整流水线：

1. 🔍 **分析** — 扫描源码，映射 GUI 操作到 API
2. 📐 **设计** — 架构命令分组、状态模型、输出格式
3. 🔨 **实现** — 用 Click 构建 CLI，含 REPL、JSON 输出、撤销/重做
4. 📋 **计划测试** — 创建含单元+E2E 测试计划的 TEST.md
5. 🧪 **编写测试** — 实现完整测试套件
6. 📝 **文档** — 更新 TEST.md 附上结果
7. 📦 **发布** — 创建 setup.py，安装到 PATH

**第四步：使用生成的 CLI**

```bash
# 进入项目目录
cd gimp/agent-harness && pip install -e .

# 随时使用
cli-anything-gimp --help
cli-anything-gimp project new --width 1920 --height 1080 -o poster.json
cli-anything-gimp --json layer add -n "Background" --type solid --color "#1a1a2e"

# 进入交互式 REPL
cli-anything-gimp
```

### 验证安装成功

```bash
# 检查 CLI 是否在 PATH 中
which cli-anything-gimp

# 查看帮助，应看到所有命令组
cli-anything-gimp --help

# 测试 REPL 启动
echo "project list" | cli-anything-gimp
```

---

## 🔧 七阶段流水线详解

### Phase 1：分析（Analyze）

Agent 扫描软件代码库，理解：

- GUI 操作的代码实现位置
- 内部 API 和数据结构
- 命令行参数的可行性
- 输出格式和错误处理

**产出**：Capability Map，列出所有可 CLI 化的功能。

### Phase 2：设计（Design）

根据分析结果，架构：

- **命令分组**：按功能领域组织（如 GIMP 分 layer、filter、export 等组）
- **状态模型**：如何跟踪项目/会话状态
- **输出格式**：JSON（Agent 友好）+ 人类可读双轨输出

**设计文档**保存在 `HARNESS.md`。

### Phase 3：实现（Implement）

用 Python Click 框架构建 CLI：

```python
# 生成的 CLI 结构示例
import click

@click.group()
def cli():
    """Generated CLI for GIMP"""
    pass

@cli.group()
def layer():
    """Layer management commands"""
    pass

@layer.command()
@click.option('--name', required=True)
@click.option('--type', default='solid')
def add(name, type):
    """Add a new layer"""
    # 调用真实 GIMP Python API
    pass
```

**关键特性**：

- REPL 交互模式：状态保持，命令可组合
- JSON 输出：`--json` flag 输出结构化数据
- 撤销/重做：每步操作记录，支持回滚

### Phase 4-6：测试计划、编写、文档

自动生成测试计划并实现：

```bash
# 阶段 4：创建 TEST.md，包含测试策略
# 阶段 5：用 pytest 实现单元测试+E2E测试
# 阶段 6：更新 TEST.md 附测试结果

# 运行测试
cli-anything-gimp --test
```

**测试覆盖**：

- 单元测试：合成数据，验证命令逻辑
- E2E 测试：真实文件和软件，验证集成
- CLI 子进程验证：`which cli-anything-gimp` 确认 PATH 安装

### Phase 7：发布（Publish）

```bash
# 自动生成 setup.py
# 发布到 PyPI（可选）
python -m build
twine upload dist/*
```

生成 `cli-anything-<software>` 包名，直接 `pip install -e .` 即可用。

---

## 🔍 进阶用法：Refine 迭代改进

初始生成后，CLI 覆盖率不可能一步到位。Refine 命令增量分析缺口并补全。

### 宽范围精化

```bash
# 分析所有功能的覆盖缺口
/cli-anything:refine ./gimp
```

### 聚焦精化

```bash
# 只针对特定功能领域扩展
/cli-anything:refine ./gimp "I want more CLIs on image batch processing and filters"
```

**Refine 的行为**：

1. 对比软件完整能力 vs 当前 CLI 覆盖范围
2. 识别未覆盖的命令/选项/场景
3. 实现新命令、测试、文档
4. 每次运行增量、不破坏已有命令

可以多次运行，逐步扩展到完整覆盖。

---

## 🔌 CLI-Hub：AI Agent 的应用商店

CLI-Hub 是 CLI-Anything 的元技能（meta-skill），让 Agent 能够**自主发现和安装**社区构建的 CLI。

### 安装

```bash
# OpenClaw
openclaw skills install cli-anything-hub

# nanobot
nanobot skills install cli-anything-hub
```

### Agent 自主使用

给 Agent 一个任务，它会：

1. 浏览 CLI-Hub 目录（catalog 自动更新）
2. 识别适合的 CLI
3. 用一条 `pip install` 命令安装
4. 读取该 CLI 的 SKILL.md 获取详细用法
5. 执行任务

### 内置 SKILL.md 生成

每个生成的 CLI 都包含 `SKILL.md`——AI Agent 可发现的能力定义文件：

```yaml
---
name: cli-anything-gimp
description: GIMP image editor CLI harness
commands:
  - group: layer
    description: Layer management
    subcommands:
      - name: add
        description: Add a new layer
        args: [...]
---
```

这让 CLI-Anything 的整个生态都支持 `npx skills add HKUDS/CLI-Anything --list` 式的探索。

---

## 📊 已支持的软件生态

截至 2026 年 4 月，CLI-Anything 社区已为以下软件生成 CLI：

| 类别 | 软件 |
| ---- | ---- |
| **3D 建模** | Blender、FreeCAD、Godot Engine |
| **图像处理** | GIMP、Inkscape、Krita、Darktable |
| **视频编辑** | Kdenlive、Shotcut、OBS Studio |
| **办公套件** | LibreOffice |
| **开发工具** | iTerm2、Jenkins、Gitea、Portainer |
| **科研工具** | ImageJ、QGIS、ParaView、KiCad |
| **AI/ML 平台** | Stable Diffusion WebUI、ComfyUI、Ollama |
| **浏览器** | Safari（via safari-mcp） |
| **游戏引擎** | Godot、s&box |
| **其他** | Zotero、Obsidian、Draw.io、Zoom |

**总计**：18 个主要应用，2269 个测试通过，覆盖率在持续增长。

---

## ⚠️ 常见误区

### 误区 1：生成的 CLI 不如手写的好

**实际情况**：生成流水线使用经过 18 个应用验证的同一套方法论，产出的 CLI 在结构、测试覆盖、文档完整性上都经过质量门禁。手写一个完整 CLI 往往需要数日，生成只需数分钟。

### 误区 2：只能处理开源软件

**实际情况**：CLI-Anything 最擅长处理有源码的软件（分析源码映射 API），但也支持：
- GitHub 仓库：`/cli-anything https://github.com/blender/blender`
- 闭源软件的命令行接口（如果软件暴露 CLI）
- API 文档和 SDK 代码（生成封装 CLI）

### 误区 3：Refine 会破坏已有命令

**实际情况**：Refine 设计为增量、非破坏性。每次运行只添加新命令，不修改已有命令。已有测试持续通过。

---

## 📋 总结速查

### 核心要点

1. **CLI-Anything 做什么**：把任意软件转成 AI Agent 可控的 CLI
2. **一条命令搞定**：`/cli-anything <path>` 生成完整 CLI
3. **七阶段流水线**：分析→设计→实现→测试计划→测试编写→文档→发布
4. **迭代改进**：用 `/cli-anything:refine` 增量扩展覆盖
5. **跨平台**：Claude Code、Pi、OpenClaw、OpenCode 等都支持
6. **CLI-Hub**：Agent 自主发现和安装社区 CLI

### 快速参考

```bash
# Claude Code 中构建 CLI
/plugin marketplace add HKUDS/CLI-Anything
/plugin install cli-anything
/cli-anything ./gimp

# 安装生成的 CLI
cd gimp/agent-harness && pip install -e .

# 使用
cli-anything-gimp --help
cli-anything-gimp --json layer add -n "Background" --type solid

# 精化扩展
/cli-anything:refine ./gimp "batch processing"
```

---

## 🔗 相关资源

- **仓库**：[HKUDS/CLI-Anything](https://github.com/HKUDS/CLI-Anything) ⭐ 35.2k
- **CLI-Hub**：https://hkuds.github.io/CLI-Anything/
- **中文文档**：[README_CN.md](https://github.com/HKUDS/CLI-Anything/blob/main/README_CN.md)
- **快速开始指南**：[§Quick Start](https://github.com/HKUDS/CLI-Anything#-quick-start)
- **贡献指南**：[CONTRIBUTING.md](https://github.com/HKUDS/CLI-Anything/blob/main/CONTRIBUTING.md)

---

**文档元信息**
难度：⭐⭐ | 类型：核心概念 | 更新日期：2026-05-17 | 预计阅读时间：25 分钟