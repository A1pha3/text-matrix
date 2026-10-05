---
title: "CLI-Anything：真正的资产不是那堆 CLI，而是把软件改造成 Agent 接口的七阶段方法论"
date: "2026-05-18T00:00:00+08:00"
lastmod: 2026-10-02
slug: "cli-anything-universal-cli-framework"
github_repo: "HKUDS/CLI-Anything"
source_key: "gh:HKUDS/CLI-Anything"
description: "香港大学数据智能实验室（HKUDS）的 CLI-Anything 用七阶段管道把有源码的软件自动改造成 Agent 可调用的 CLI。本文拆解 HARNESS.md 方法论、测试体系与 CLI-Hub 分发生态，并给出采用建议。"
draft: false
categories: ["技术笔记"]
tags: ["CLI", "AI Agent", "开源"]
---

# CLI-Anything：真正的资产不是那堆 CLI，而是把软件改造成 Agent 接口的七阶段方法论

AI Agent 会写代码、会查资料，但让它操作 GIMP 修图、用 Blender 渲染一段动画，路只有两条：要么对着截图点鼠标，要么等软件官方开放 API。香港大学数据智能实验室（HKU Data Intelligence Lab，GitHub 组织 HKUDS）开源的 CLI-Anything 走了第三条路：只要软件有源码，就用 Agent 自己把整个软件改造成一套命令行接口——一条 `/cli-anything ./gimp`，跑完七个阶段，装进 PATH 的就是一个 Agent 能直接调用的 `cli-anything-gimp`。

这个项目常被概括成"给软件自动生成 CLI 的工具"。看完仓库会发现这个概括漏了重点：仓库里躺着 79 个现成的 CLI（registry.json 口径，2026-06 快照），但它们更像方法论的样例集。真正的资产是 `cli-anything-plugin/HARNESS.md`——一份 747 行的标准作业程序（SOP），把"分析代码库、设计接口、写实现、补测试、发 PyPI"每一步都写成可检验的标准，再由 Claude Code 这类编码 Agent 逐步执行。CLI 可以过时，方法论可以复制到任何新软件上，这才是它拿下 51,217 star（GitHub API，2026-10-02 读数）的原因。

对想快速上手的读者，仓库另有一篇偏操作向的[CLI-Anything 完整指南](/posts/tech/cli-anything-command-line-interface-ai-guide/)可对照阅读。本文聚焦机制：这套管道到底怎么跑，质量怎么保证，哪些数字该怎么读。

## 系统地图：生成、分发、产物三层

CLI-Anything 的结构分三层，混在一起谈容易迷失：

| 层 | 载体 | 干什么 |
|------|------|------|
| **生成层** | `cli-anything-plugin/`（Claude Code 插件 + HARNESS.md SOP） | 把有源码的软件自动改造成 CLI，七阶段管道 |
| **分发性** | CLI-Hub（`pip install cli-anything-hub`，PyPI v0.4.1） | 包管理器，浏览、搜索、安装社区构建好的 CLI |
| **产物层** | 79 个 `cli-anything-<software>` 命令 | 装进 PATH 的独立 CLI，REPL + 子命令双模式，`--json` 结构化输出 |

日常使用绝大多数时候只碰分发层：`cli-hub install gimp` 装一个现成的。生成层只在注册表里没有你想要的软件时才启动。这个区分很重要——很多人以为用了 CLI-Anything 就要跑一遍生成管道，实际上生态里已有的 79 个 CLI 都是装完即用。

## 为什么是 CLI：三条老路的死角

Agent 操控软件的三种常见方案各有硬伤，README 的概括很准：GUI 自动化脆弱（截图加点击，界面一改就崩）；API 受限于接口（多数桌面软件根本不提供）；把软件功能用 Python 重写一遍则成了玩具实现，丢掉九成能力。

CLI-Anything 的立身之本是 HARNESS.md 里的第一条规则：**调用真实软件，绝不重实现**。生成的 CLI 不自己画图、不自己剪视频——它生成合法的项目文件（ODF 文档、MLT 时间线、SVG 图形），然后把渲染交给真正的后端：LibreOffice 用 `--headless --convert-to` 转 PDF，Blender 用 `--background --python` 跑渲染，GIMP 走 Script-Fu，OBS 走 obs-websocket 协议。README 把反面模式写得很直白：用 Pillow 拼一个图像合成器来替代 GIMP，得到的只是一个处理不了真实工作量的玩具。

配套的是"渲染鸿沟"（Rendering Gap）教训：GUI 应用在渲染时才套用滤镜效果，如果你的 CLI 只操作项目文件却用简陋的导出工具，效果会被静默丢弃。解法是原生渲染器加滤镜翻译层，这套经验全部沉淀在 HARNESS.md 的 Critical Lessons 表里。

## 七阶段管道：一份写成 SOP 的生成流程

跑 `/cli-anything <软件路径或仓库>` 时，编码 Agent 执行的是 HARNESS.md 定义的七个阶段。注意阶段划分和直觉不同——测试被拆成"计划"和"实现"两段，文档不是独立阶段，而发布上 PyPI 反而是正式的第七阶段：

| 阶段 | 名称 | 核心动作 |
|------|------|------|
| Phase 1 | Codebase Analysis | 找后端引擎（如 Shotcut 背后的 MLT）、把 GUI 动作映射到 API 调用、识别数据模型、盘点软件自带的 CLI |
| Phase 2 | CLI Architecture Design | 定交互模型（有状态 REPL、子命令、或两者都支持）、划命令组、设计状态持久化、约定 `--json` 输出 |
| Phase 3 | Implementation | 从数据层写起，先加只读的探查命令再加修改命令，用 `subprocess.run` 包装真实软件后端，配会话管理与统一 REPL 皮肤 |
| Phase 4 | Test Planning | 动手写测试前先产出 TEST.md 测试计划：哪些文件、多少用例 |
| Phase 5 | Test Implementation | 单元测试（合成数据）、E2E 中间文件校验、真后端 E2E（必须调用真实软件）、CLI 子进程测试 |
| Phase 6 | Test Documentation | 把 `pytest -v` 完整输出回填进 TEST.md，测试计划与结果合归档 |
| Phase 6.5 | SKILL.md Generation | 用 `skill_generator.py` 从 Click 装饰器和 setup.py 提取元数据，生成 Agent 可发现的技能描述文件 |
| Phase 7 | PyPI Publishing | 按 PEP 420 命名空间包发布安装，`cli_anything/` 本身无 `__init__.py`，各软件子包独立分发 |

三个阶段值得展开。

**Phase 3 的架构选择**决定了生成物的形态。每个 CLI 默认双模式：裸敲 `cli-anything-blender` 进 REPL（交互会话，带历史和状态），接子命令则走单次执行（适合脚本和管道）。所有命令都挂 `--json` 开关，人类看表格，Agent 吃 JSON。统一 REPL 皮肤（repl_skin.py）让几十个 CLI 的交互观感一致——品牌横幅、彩色提示、进度条都是现成的。

**Phase 5 的测试纪律**是这套方法论里最较真的部分。E2E 测试被明确要求必须调用真实软件验证产物：导出的 PDF 要检查 `%PDF-` 魔数，DOCX 要验证 OOXML 的 ZIP 结构，视频要逐帧分析像素。更重要的一条是"零妥协依赖"——目标软件没装，测试直接失败（fail），而不是跳过（skip）。README 原话是"no fallbacks, no graceful degradation"，保证绿灯不掺水。

**Phase 6.5 的 SKILL.md** 解决的是可发现性。每个 CLI 自带一份技能描述文件，写清命令组、参数和 Agent 专属的使用建议（JSON 输出、错误处理），仓库内统一放在 `skills/cli-anything-<software>/SKILL.md`，pip 安装后的包内还会带一份兼容副本。Agent 装完 CLI 读这份文件就知道怎么用，不需要人写接入文档。

## 测试数字怎么读：2,461、79 和 18 各是什么口径

README 里反复出现的几个数字容易混着引用，分开看：

- **2,461 个测试**（README 徽章口径）：1,732 个单元测试 + 579 个端到端测试 + 19 个 Node.js 测试，标称 100% 通过率。README 内部其实有三套数字并存——徽章和正文写 2,461，测试汇总表合计 2,464，特性表格和页脚还留着旧的 2,280+。引用时以徽章口径为准，差额来自文档更新不同步。
- **79 个 CLI**（registry.json，2026-06-19 更新）：仓库里实际有 69 个 `agent-harness` 目录，主注册表收录 79 条；另一份 public_registry.json 挂着社区在外部仓库维护的条目，比如驱动 Windows 商业软件 ArcGIS Pro 的 MCP 桥，不在这 79 条之内。PyPI 包简介的口径是"40+"，偏保守。
- **18 个应用**：README 徽章写 "Demos 18 Apps"，正文说 "Tested across 18 diverse applications"。这 18 个指最早一批完整走通七阶段、配了专业级测试的核心 harness（GIMP 107 项测试、Blender 208 项、Inkscape 202 项、LibreOffice 158 项等），HARNESS.md 自述方法论正是从这 18 个的生产过程中提炼的。它是"深度验证集"，不是支持软件总数。

79 个 CLI 的分布远不止创意工具：3D 建模（Blender、FreeCAD）、图像（GIMP、Inkscape、Krita）、视频（Kdenlive、Shotcut、OpenScreen）、办公（LibreOffice、Zotero、Calibre、Joplin）、AI 平台（ComfyUI、Ollama、Open WebUI）、开发运维（iTerm2、LLDB、RenderDoc、Nsight Graphics、PM2）、科研（QGIS、Uni-Mol）、甚至游戏自动化（Slay the Spire II 的整局对局由 Agent 打完）。分类目录可以在 CLI-Hub 官网（clianything.cc）直接浏览。

## 一个任务的生命周期：从一条命令到 REPL 会话

以给 GIMP 生成 CLI 为例，走一遍完整流程。环境要求 Python 3.10+ 和一个受支持的编码 Agent，以 Claude Code 为例装插件：

```bash
/plugin marketplace add HKUDS/CLI-Anything
/plugin install cli-anything
```

然后一条命令启动生成：

```bash
/cli-anything ./gimp          # 本地源码目录，也可以给 GitHub 仓库地址
```

官方快速上手文档给的参考时长是 10-15 分钟（视复杂度），七个阶段自动走完，产出落在 `gimp/agent-harness/`。安装进 PATH：

```bash
cd gimp/agent-harness && pip install -e .
which cli-anything-gimp       # 确认安装
```

之后 Agent 就能像下面这样工作（README 的 Blender 演示）：

```bash
$ cli-anything-blender
blender> scene new --name ProductShot
✓ Created scene: ProductShot
blender[ProductShot]> object add-mesh --type cube --location 0 0 1
✓ Added mesh: Cube at (0, 0, 1)
blender[ProductShot]> render execute --output render.png --engine CYCLES
✓ Rendered: render.png (1920×1080, 2.3 MB) via blender --background
```

注意最后一行的 `via blender --background`——渲染是真实 Blender 进程干的，CLI 只是结构化的指挥层。首次生成覆盖不全时，用 `/cli-anything:refine <路径> [关注点]` 做增量扩展：它会先盘点现有覆盖、再对软件全量能力做差距分析、然后只补缺失的命令。refine 的文档里写死了两条约束——"Refine 从不删除已有命令，只增改"和"所有既有测试必须继续通过"，所以迭代没有破坏性。配套还有 `/cli-anything:test`（跑测试并回填 TEST.md）和 `/cli-anything:validate`（对照 HARNESS.md 标准体检）。

## CLI-Hub：让 Agent 自己去装工具

生成层面向贡献者，分发层才是普通用户的入口。装包管理器：

```bash
pip install cli-anything-hub
cli-hub list                   # 浏览注册表
cli-hub install gimp           # 安装
cli-hub launch gimp            # 直接运行
```

子命令一共七个：`list`、`search`、`info`、`install`、`update`、`uninstall`、`launch`。自 2026 年 4 月的 v0.2.0 起，Hub 还能装注册表之外的三方公共 CLI（pip、npm、brew 多源），官网页面分 "CLI-Anything CLIs" 和 "Public CLIs" 两栏。

更进一步的玩法是给 Agent 装元技能（meta-skill），让它按任务自己找工具：

```bash
npx skills add HKUDS/CLI-Anything --skill cli-hub-meta-skill -g -y
```

之后的提示词可以直接写"在 CLI-Hub 里找到合适的 CLI 并完成任务：……"。Agent 查目录、装 CLI、读它的 SKILL.md、干活，全程无需人工指定工具。生态的社区机制也简单：为新软件生成的 harness 提 PR，合并后 Hub 立刻可装——registry 里每条目都带贡献者署名，进展记录在 README 的 News 区——2026-05-20 一天就合入了 Rekordbox、Calibre、3MF、MiniMax 四个社区 CLI。

## 限制与边界

三类硬限制，README 不回避：

1. **强模型依赖**。七阶段靠前沿模型跑（README 点名 Claude Opus 4.6、Sonnet 4.6、GPT-5.4），弱模型生成的 CLI 可能不完整甚至出错，需要大量手工修正。
2. **必须有源码**。管道从源码分析生成，目标软件只有编译好的二进制时要走反编译，质量和覆盖会明显下滑。闭源但有 API 文档的 Web 服务可以喂文档生成封装（Roadmap 里"把闭源软件与 Web 服务打包成 CLI"仍是未完成项）。
3. **一次生成未必到位**。单次 `/cli-anything` 很难覆盖软件全部能力，跑一两次 `refine` 推到生产质量是常态。

还有两个工程细节：Windows 上 Claude Code 通过 bash 执行命令，需要装 Git for Windows 或用 WSL，否则会报 `cygpath` 找不到；生成的 CLI 是真实软件的"指挥层"，目标软件本身是硬依赖，装 CLI 之前得先把 GIMP、Blender 这些上游软件装好。

## 谁该用，怎么用

按需求对号入座：

- **只是想让 Agent 操作常见软件**：直接 `pip install cli-anything-hub`，在 79 个现成 CLI 里找，装完即用，不碰生成管道。
- **有内部工具或小众软件要接入 Agent**：这是 CLI-Anything 的主场。用 Claude Code 插件跑一遍生成，配 `refine` 迭代；团队有多个内部系统时，这套 SOP 可以沉淀成标准的接入流程。
- **在做 GUI Agent 相关的评测或研究**：把 GUI 软件改成 CLI 后，Agent 任务的合成、评测、基准都可以纯代码完成，README 明确把"替代或增强 GUI Agent"列为三大用途之一。项目还配了技术报告（arXiv:2606.03854，*CLI-Anything: Towards Agent-Native Computer Use*）。
- **不该用的场景**：目标软件闭源无文档、手头只有弱模型、或者只是想"点一下就出生产级 CLI"——管道跑得完，产物质量撑不住预期。

平台选择上，Claude Code 是第一梯队（官方插件市场，四个命令完整支持）；Pi、Cursor 有专门适配；OpenCode、Codex、Goose、Hermes、Reasonix 标注实验性或社区维护；GitHub Copilot CLI、Qodercli、OpenClaw 走社区路径。装元技能的话，OpenClaw、Nanobot、Antigravity 等 SKILL 兼容 Agent 都能用。

回头看，CLI-Anything 做对的事情是把"给软件写接口"从一次性劳动变成了可复现的工程流程：SOP 写成文档让任何 Agent 都能执行，质量纪律（真后端测试、fail 不 skip）写进流程而不是靠自觉，产物用命名空间包和统一 REPL 规模化管理。CLI 会随软件版本过时，这套方法论本身才是可以长期复利的东西。

---

**相关资源**

- **仓库**：[HKUDS/CLI-Anything](https://github.com/HKUDS/CLI-Anything)（Apache 2.0，51,217★ / 2026-10-02）
- **CLI-Hub 官网**：[clianything.cc](https://clianything.cc/)
- **技术报告**：[arXiv:2606.03854](https://arxiv.org/abs/2606.03854)
- **中文文档**：[README_CN.md](https://github.com/HKUDS/CLI-Anything/blob/main/README_CN.md)
- **上手篇**：[CLI-Anything 完整指南](/posts/tech/cli-anything-command-line-interface-ai-guide/)
