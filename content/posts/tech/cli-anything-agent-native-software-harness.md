---
title: "CLI-Anything：把任意软件变成 Agent 可调用的 CLI 工具"
date: "2026-05-20T15:51:00+08:00"
lastmod: 2026-10-02
slug: "cli-anything-agent-native-software-harness"
github_repo: "HKUDS/CLI-Anything"
source_key: "gh:HKUDS/CLI-Anything"
description: "HKUDS/CLI-Anything 把没有 API 的桌面软件包装成 Agent 可调用的有状态 CLI：79 个现成工具经 CLI-Hub 一键安装，SKILL.md 让 Agent 自助读懂用法。本文拆解 harness 的真实目录结构、SKILL.md 规范与多平台接入方式。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Python"]
---

# CLI-Anything：把任意软件变成 Agent 可调用的 CLI 工具

AI Agent 能调 Slack 的 API、能操作 GitHub，但让它用 Blender 渲一段动画、拿 QGIS 处理地图，路就断了——大多数桌面软件根本没有标准化 API。香港大学数据智能实验室（HKUDS）的 CLI-Anything 给出的方案是：不管软件原本怎么暴露能力，都给它包一层**有状态的命令行接口**，再配一份 SKILL.md 告诉 Agent 怎么用。项目上线七个月拿下 51,249 star（GitHub API，2026-10-02 读数），Apache 2.0 协议。

这个项目容易讲糊，因为它是三层东西的合体：生成 CLI 的插件、分发 CLI 的包管理器、以及 79 个已经生成好的 CLI 本身。多数读者的正确用法只碰后两层——装现成的，不跑生成。本文按"产物长什么样 → SKILL.md 怎么写 → 装与接"的顺序拆解；七阶段生成方法论的深读见[姊妹篇](/posts/tech/cli-anything-universal-cli-framework/)。

读完本文你应该能：判断要用的软件有没有现成 CLI；用 `cli-hub` 装一个并跑通验证；看懂 harness 的目录结构；把 CLI-Anything 接进自己用的 Agent 平台。

## 系统地图：三层各管一件事

| 层 | 载体 | 谁会用 |
|------|------|------|
| **生成层** | `cli-anything-plugin/`（Claude Code 插件 + HARNESS.md 七阶段 SOP） | 想为新软件生成 CLI 的贡献者 |
| **分发层** | CLI-Hub（`pip install cli-anything-hub`，PyPI v0.4.1） | 所有用户 |
| **产物层** | 79 个 `cli-anything-<software>` 独立 CLI（registry.json，2026-06-19 更新） | 所有用户 |

先装分发层还是直接装单个 CLI，取决于你要不要浏览注册表——两者不冲突，`cli-hub` 本质上只是帮你把产物层的包从 PyPI 装进 PATH。

## 产物层：拿 Blender 的 harness 拆开看

每个现成 CLI 在仓库里对应一个 `agent-harness` 目录。以 Blender 为例，真实结构是这样：

```
blender/agent-harness/
├── setup.py                    # 按 PEP 420 命名空间包发布，pip install 后进 PATH
├── BLENDER.md                  # 面向人的说明文档
└── cli_anything/blender/
    ├── blender_cli.py          # Click 命令定义，--json 开关在这里
    ├── core/                   # scene、objects、materials、render 等功能模块
    ├── tests/                  # 单元测试 + 调用真实 Blender 的 E2E 测试
    └── skills/SKILL.md         # 随包分发的技能描述副本
```

有两处和直觉不同。其一，仓库顶层另有 `skills/cli-anything-blender/SKILL.md` 作为规范源，包内那份是随 pip 分发的副本——2026 年 4 月起所有 SKILL.md 统一收进顶层 `skills/` 目录，方便 `npx skills` 一处安装。其二，`cli_anything/blender/` 没有 `harness.py` 这类单文件入口，功能按 `core/` 子模块拆开，`blender_cli.py` 只做命令定义和分发。

CLI 本身是双模式的：裸敲 `cli-anything-blender` 进 REPL（交互式会话，命令立即执行且保留场景状态），接子命令则单次执行，适合脚本和管道。所有命令挂 `--json` 开关，人看文本，Agent 吃 JSON。出错时输出的也是结构化 JSON——`blender_cli.py` 的 `handle_error` 装饰器把异常统一成 `{"error": ..., "type": "file_not_found"}` 这类格式，Agent 不用解析自然语言报错。

最关键的一点：**这个 CLI 不会自己画图**。SKILL.md 原话是"用 JSON 场景描述格式加 bpy 脚本生成来完成真正的 Blender 渲染"（JSON scene description format with bpy script generation for actual Blender rendering）——CLI 生成合法的 bpy 脚本，把渲染交给真实 Blender 进程。所以目标软件本身是硬依赖，SKILL.md 的 Prerequisites 写明需要 Blender 4.2 以上。

## SKILL.md：Agent 的工具说明书

SKILL.md 解决的是可发现性：Agent 装完 CLI，读一遍这个文件就知道有哪些命令组、参数怎么传、缺什么前置条件，不需要人为每个 Agent 写接入文档。Blender 这份的开头是这样的：

```markdown
---
name: "cli-anything-blender"
description: >-
  Command-line interface for Blender - A stateful command-line interface for 3D scene editing, following the same patterns as the GIMP CLI ...
---

# cli-anything-blender

A stateful command-line interface for 3D scene editing, ...
Uses a JSON scene description format with bpy script generation
for actual Blender rendering.

**Prerequisites:**
- Python 3.10+
- blender (>= 4.2) must be installed on your system
```

正文接着列安装方式、基础命令和 REPL 用法。写作有统一套路：先一句话说清"有状态 CLI 做什么"，再给前置条件，最后是可直接复制的命令。给自研软件生成 harness 时，这就是要维护的核心接口文档。

## 分发层：CLI-Hub 装现成工具

注册表 `registry.json` 收录 79 条 CLI（2026-06-19 更新），跨度远不止创意工具：办公（LibreOffice、Zotero、Calibre）、开发运维（iTerm2、LLDB、PM2）、AI 平台（ComfyUI、Ollama）、科研（QGIS）、甚至游戏自动化。另有 `public_registry.json` 收录社区在外部仓库维护的条目（如驱动 Windows 上 ArcGIS Pro 的 MCP 桥），不在这 79 条之内。

包管理器本身很薄，PyPI 包名 `cli-anything-hub`，当前版本 0.4.1，要求 Python 3.10 以上：

```bash
pip install cli-anything-hub
cli-hub list                 # 浏览注册表
cli-hub search <关键词>       # 搜索
cli-hub info <name>          # 看单条详情
cli-hub install <name>       # 安装进 PATH
cli-hub launch <name>        # 免安装直接运行
cli-hub update / uninstall   # 升级与卸载
```

一个容易误读的数字：README 徽章写 "Demos 18 Apps"——这 18 个（GIMP、Blender、Inkscape、LibreOffice 等）是最早完整走通生成管道、配了专业级测试的深度验证集，全部 2,461 项测试（1,732 单元 + 579 E2E + 19 Node.js，badge 口径）都押在它们身上。它是质量样本，不是支持总数；支持总数以 registry 的 79 条为准。

## 接进你的 Agent

按官方支持力度分三档：

- **第一梯队**：Claude Code（官方插件市场，`/cli-anything` 命令族完整支持）；Pi、Cursor 有专门适配。
- **实验性/社区维护**：OpenCode、Codex、Goose、Hermes、Reasonix；GitHub Copilot CLI、Qodercli 走社区路径。
- **SKILL 兼容路线**：装元技能（meta-skill），让 Agent 按任务自己找工具：

```bash
npx skills add HKUDS/CLI-Anything --skill cli-hub-meta-skill -g -y
```

装完后的提示词可以直接写"在 CLI-Hub 里找到合适的 CLI 并完成任务：……"。README 标注的兼容范围是 OpenClaw、Nanobot、Claude Code、Codex、Reasonix、Antigravity 及其他 SKILL 兼容 Agent。这条路线和第一梯队的差别在于自动化程度：前者 Agent 自主查目录、装 CLI、读 SKILL.md、干活；后者仍由人指定跑哪个命令。

## 快速开始

前置条件：Python 3.10+；要操作的软件已装好（CLI 只是"指挥层"，不替你装 Blender）；走生成路线另需一个受支持的编码 Agent。

最常见的路径是装现成的：

```bash
pip install cli-anything-hub
cli-hub search blender          # 确认注册表里有
cli-hub install blender
cli-anything-blender --help     # 验证：能列出命令组即安装成功
```

想接入的软件不在注册表里，才需要走生成路线：用 Claude Code 装插件后跑 `/cli-anything ./your-software`，官方参考时长约 10-15 分钟（视软件复杂度），细节见姊妹篇。

## 边界与限制

- **目标软件是硬依赖**。生成的 CLI 调用真实软件后端，上游没装，CLI 跑不了任何实际操作。
- **生成质量吃模型能力**。README 点名建议 Claude Opus 4.6、Sonnet 4.6、GPT-5.4 这档模型跑生成；弱模型产物可能不完整。
- **只有编译好的二进制会拖累质量**。管道从源码分析出发生成，闭源软件需要走反编译路线，覆盖明显下滑。
- **注册表之外没有银弹**。79 条之外的需求要么自己生成，要么等社区 PR——合并后 Hub 立刻可装，README 的 News 区持续记录新合并条目。

## 常见问题

**和直接调软件 API 有什么区别？** 如果软件有高质量 API，直接用更稳。CLI-Anything 解决的是"没有标准化 API"的空白：有的软件接口面向内嵌脚本（比如 Blender 的 bpy 得在 Blender 内部跑），有的软件根本没有编程接口——统一包装成 CLI 后，Agent 用同一套方式（子命令 + JSON）操作所有软件。

**SKILL.md 和 README 有什么不同？** README 面向人，讲安装、背景、贡献流程；SKILL.md 面向 Agent，只回答"有什么命令、参数怎么传、缺什么前置条件"。Agent 消费后者，不读前者。

**装了 CLI 就能离线用吗？** CLI 本身本地运行，但依赖目标软件进程。Blender 渲染、LibreOffice 转换都是拉起真实软件完成的，首次运行确认上游软件能正常启动。

**支持哪些 Agent？** 见上文"接进你的 Agent"一节的三档清单。选型建议：用 Claude Code 选插件路线（功能最全）；用其他 SKILL 兼容 Agent 选元技能路线；只是想试试，先 `pip install cli-anything-hub` 手动装一个。

---

**相关阅读**

- [CLI-Anything 方法论深读：七阶段管道与测试体系](/posts/tech/cli-anything-universal-cli-framework/)
- [CLI-Anything 完整上手指南](/posts/tech/cli-anything-command-line-interface-ai-guide/)
- [OpenHuman](https://github.com/tinyhumansai/openhuman)：Rust 内核的开源 agent harness，可插拔接入现有 LLM、记忆与搜索引擎，思路与 CLI-Anything 互补
- [12 Factor Agents](/posts/tech/12-factor-agents-production-llm-guide/)：构建生产级 LLM Agent 的核心原则
- [Claude Code Skills 实战](/posts/tech/andrej-karpathy-skills-claude-code-guide/)：SKILL.md 机制的同类实践
