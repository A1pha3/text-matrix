---
title: "CLI-Anything: 一个命令让任意软件具备 Agent 原生能力"
date: "2026-05-18T20:00:00+08:00"
slug: "cli-anything-universal-cli-framework"
description: "CLI-Anything是HKUDS开源的AI Agent原生CLI工具，通过生成标准化命令接口让任意软件具备Agent可调用能力。本文详解其核心原理、支持工具生态、CLI-Hub安装及快速上手方法。"
categories: ["技术笔记"]
---

# CLI-Anything: 一个命令让任意软件具备 Agent 原生能力

如果未来的用户不再是人类，而是 AI Agent，软件应该如何设计？

香港大学研究团队 HKUDS 给出了他们的答案——**CLI-Anything**，一个将任意软件自动转化为 Agent 可调用工具的开源框架。项目在 GitHub 上已斩获 **36,283 Stars**，一跃成为 AI Agent 工具生态中最受关注的基础设施项目之一。

## 为什么 CLI 对 AI Agent 至关重要？

GUI（图形界面）是人类友好型接口，但对 AI Agent 而言，**CLI 才是真正的"母语"**：

- **结构化、可组合**：命令行的输出可以管道传递、解析、再利用，形成复杂的工作流。
- **轻量且通用**：几乎所有操作系统、所有软件都提供命令行接口，无需额外的 GUI 自动化。
- **自描述**：大多数 CLI 工具内置 `--help`，Agent 可以自主探索用法。
- **幂等性**：同样的命令执行多次结果一致，Agent 可以安全地重试。

然而现实情况是：**大量专业软件的 CLI 接口设计混乱，缺乏标准化封装，可机器读懂的元信息严重不足。** 这正是 CLI-Anything 试图解决的核心问题。

## 核心原理：Harness 生成

CLI-Anything 的核心思路是为目标软件生成一个 **Harness（测试 harness 的概念）**——一个标准化的 CLI 包装层，它具备以下能力：

1. **统一参数解析**：将散乱的命令行参数映射为统一的接口规范。
2. **结构化输出**：将软件原始输出转化为 JSON 等机器可读格式。
3. **错误标准化**：统一的错误码和错误信息，Agent 可以做出有意义的判断。
4. **交互式支持**：对于需要用户输入的软件，支持静默模式和预设响应。

生成的 Harness 本质上是一个 Python CLI 程序，遵循 Click 框架的最佳实践，输出符合 Agent 的调用约定。

## 主要特性一览

### 支持 18+ 主流应用

开箱即用，支持大量专业工具的 Harness 生成，涵盖 3D 建模、工程设计、创意工具、研究软件、通信平台等类别：

| 类别 | 支持工具 |
|------|----------|
| 3D 建模 | **Blender**, FreeCAD |
| 创意工具 | **Krita**, GIMP, Inkscape |
| 游戏开发 | **Unreal Insights**, Unity CLI |
| 学术研究 | **Zotero**, Mendeley, JabRef |
| 视频会议 | **Zoom**, Google Meet, Teams |
| 终端/文件 | tmux, rsync, ffmpeg, ImageMagick |

持续扩充中，社区也在贡献新的 Harness。

### 轨迹回放与 Live Preview

支持多轮交互轨迹录制，生成可回放的 Agent 对话轨迹文件。同时提供实时预览功能，调试 Harness 时可以直观看到每一步的输入输出。

### 一键生成 SKILL.md

为 OpenClaw、nanobot、Cursor、Claude Code 等主流 Agent 平台**自动生成 SKILL.md**，让工具直接注册到 Agent 的技能列表中，无需手工编写 prompt 工程文件。

### 标准化 CLI-Hub 生态

官方维护的 [CLI-Hub](https://hkuds.github.io/CLI-Anything/) 平台提供所有生成 Harness 的集中分发，通过 pip 即可安装和管理：

```bash
# 查看可用包
pip index versions cli-hub

# 安装某个 Harness
pip install cli-hub-blender
```

这与 npm/yarn 的包管理模式完全对齐，Agent 在运行时动态安装所需工具成为可能。

## 快速上手

### 环境要求

- Python ≥ 3.10
- Click ≥ 8.0
- pytest（测试用）

```bash
pip install cli-anything
```

### 为 Blender 生成 Harness

```bash
# 初始化一个 Harness 项目
cli-anything init --tool blender --output ./harnesses/blender

# 进入目录，查看自动生成的接口
cd ./harnesses/blender
cat blender_harness.py

# 运行测试，确保 100% 通过
pytest tests/ -v
```

生成的 `blender_harness.py` 大致结构如下（以渲染场景为例）：

```python
@click.command()
@click.option('--scene', default='default', help='Blender scene file')
@click.option('--output', default='./render.png', help='Output path')
@click.option('--engine', default='CYCLES', type=click.Choice(['CYCLES', 'EEVEE']))
def render(scene, output, engine):
    """Render a Blender scene via CLI."""
    # 标准化调用 blender -b {scene} -o {output} -E {engine}
    result = subprocess.run([...], capture_output=True, text=True)
    click.echo(json.dumps({"status": "success", "output": output}))
```

### Agent 端集成

生成 SKILL.md 后，在 OpenClaw（或其他 Agent 平台）中注册：

```bash
cli-anything generate-skill --harness ./harnesses/blender --platform openclaw
# 输出: blender_skill.md
```

将生成的 SKILL.md 复制到 Agent 的 skills 目录即可。

## 适用边界

CLI-Anything 非常适合以下场景：

- ✅ 专业工具（Blender、FreeCAD、Zotero 等）的 Agent 化封装
- ✅ 需要跨平台一致性 CLI 接口的团队
- ✅ 为 Agent 构建自定义工具链

但也需要注意其边界：

- ⚠️ 高度依赖图形交互的工具，Harness 覆盖有限
- ⚠️ 商业闭源软件的 CLI 支持受限于工具自身提供的接口
- ⚠️ Harness 质量依赖于社区贡献和维护活跃度

## 结语

CLI-Anything 提供了一种优雅的方式来弥合"专业软件"与"AI Agent"之间的鸿沟。当我们畅想 Agent 作为主要用户（human-in-the-loop 变成 agent-in-the-loop）的未来时，标准化的 CLI 接口将是构建可靠 Agent 工作流的基础设施。

项目采用 **Apache 2.0** 开源许可，代码质量通过完整的 pytest 测试套件保障。如果你正在构建 Agent 工具链，或有兴趣探索 Agent-Native 软件设计范式，这个项目值得深入关注。

> **相关链接**
> - GitHub: [HKUDS/CLI-Anything](https://github.com/HKUDS/CLI-Anything)
> - CLI-Hub: [https://clianything.cc/](https://clianything.cc/)
> - 文档: [https://hkuds.github.io/CLI-Anything/](https://hkuds.github.io/CLI-Anything/)