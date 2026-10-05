---
title: "CLI-Anything：79 个 CLI 背后，把软件控制权从像素交还给命令"
date: "2026-05-19T20:25:00+08:00"
lastmod: 2026-10-03
slug: "cli-anything-universal-cli-ai-agent"
github_repo: "HKUDS/CLI-Anything"
source_key: "gh:HKUDS/CLI-Anything"
description: "HKUDS/CLI-Anything 不教 AI 看截图，而是给软件配一套结构化 CLI：79 个已建成的 CLI 覆盖 31 个类目，厚薄从 4 个命令到 292 个不等。本篇梳理生态版图与采用判断。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "CLI", "开源工具", "工作流自动化"]
---

## 先给判断

让 AI 代理操作桌面软件，主流做法是 GUI 代理：截屏、找按钮、模拟点击。CLI-Anything 的技术报告（arXiv:2606.03854，2026-06-02）对这条路线的批评很直接——像素级交互脆弱、动作依赖时序、坐标随界面改版失效，等于逼着算力充裕的代理去模仿人类的感知局限。它的替代方案是给软件配一套命令行接口：结构化命令、显式的状态表示、确定性的反馈，让代理用它本来擅长的方式干活。

这套思路如今不缺样本。截至 2026-10-03，registry.json 登记了 79 个建成的 CLI，横跨 31 个类目，从 Blender、GIMP 这些创意工具到 Zotero、LibreOffice 这些办公软件，连《杀戮尖塔 II》都有自己的 harness（一套把软件能力封装成命令的工具层）。项目由香港大学数据智能实验室（HKUDS，Data Intelligence Lab@HKU）维护，上线七个月拿下 51,338 star（GitHub API 读数），Apache 2.0 协议。

<!--more -->

如果你只想知道"现在能不能控制我手头这个软件"，直接跳到生态版图一节；想知道生成的 CLI 长什么样、怎么装，文末给了三篇姊妹篇的索引。

## 系统地图

```
┌─────────────────────────────────────────────────────┐
│    AI 代理（Claude Code / Cursor / Pi / OpenClaw）  │
└─────────────┬───────────────────────────────────────┘
             │ SKILL.md 发现 + 标准命令调用
             ▼
┌─────────────────────────────────────────────────────┐
│  分发层：skills/ 统一目录 + cli-hub 包管理器        │
└─────────────┬───────────────────────────────────────┘
             │ pip 安装 cli-anything-<software>
             ▼
┌─────────────────────────────────────────────────────┐
│  （install / list / search / update / launch）      │
│  79 个 CLI（registry.json 登记，31 个类目）         │
│  Click 构建，--json 输出，REPL 交互，撤销/重做      │
└─────────────┬───────────────────────────────────────┘
             │ 读写场景/工程文件，调真实后端
             ▼
    Blender、FreeCAD、Zotero、OBS Studio 等真实软件
```

值得注意的一条设计决策：harness 通常不直接戳软件内部，而是读写 JSON 场景文件，再由真实软件后端执行。以 Blender 为例，CLI 生成 bpy 脚本交给 Blender 本体渲染——代理拿到的是真实渲染结果，不是模拟。

## 生态版图：79 个 CLI 覆盖了什么

项目文档里有三个规模口径，混着说容易误导：

| 口径 | 数字 | 含义 |
|------|------|------|
| 专业级验证集 | 18 个应用 | 最早完整走通生成管道并经真实软件验证的一批（README 原话 "Battle-tested across 18 major applications"） |
| 顶层 harness 目录 | 69 个 | 仓库里实际存在的 agent-harness 目录 |
| registry.json 登记 | 79 个 CLI | CLI-Hub 可检索、可安装的完整清单（meta 更新于 2026-06-19，含 11 个托管在独立仓库的社区 CLI） |

宣传里最常见的"18"是第一个口径——验证集规模，不是支持总数。写作时按 registry 当次读数引用，才不会把生态说小。

按 registry 的 category 字段统计，79 个 CLI 分布在 31 个类目。最大的一组是 AI 工具链（comfyui、ollama、openwebui、dify-workflow、novita 等 8 个），其后是 devops、web、video、graphics 各 6 个，office 4 个（calibre、libreoffice、zotero、mubu）。单条类目里藏着一些意外的样本：金融记账 firefly-iii、分子科学 unimol_tools、统计软件 stata、甚至游戏《杀戮尖塔 II》。

覆盖广不等于覆盖深。同一版图里，命令数从 exa 的 4 个到 mailchimp 的 292 个，差了两个数量级（`@*.command` 装饰器逐仓实测）：Blender 10 个命令组 54 个子命令，Zotero 46 个，FreeCAD 20 个组 277 个子命令（v1.1.0，要求 FreeCAD ≥ 1.1）。拿之前评估过"几十条命令处理一个软件"的直觉来套，会低估 mailchimp、firefly-iii（103）这类厚 harness，也会高估部分薄封装。

生态的另一半是社区。registry 里登记了 60 多位贡献者名，11 个 CLI 直接托管在贡献者自己的仓库（Zotero CLI 就是从独立仓库 PiaoyangGuohai1/cli-anything-zotero 发版的），主仓只做登记与分发。README 的更新日志从 2026 年 3 月起几乎每天都有合并记录——这个生态不是官方批量生产的，是长出来的。

## 一条命令生成的管道

79 个 CLI 里，官方早期手工打磨的是少数，大多数由生成管道产出：装好插件后，对代理说 `/cli-anything ./gimp`（本地路径或 GitHub 仓库皆可），它按七个阶段跑完——分析源码、设计命令结构、用 Click 实现含 REPL 与撤销/重做的 CLI、规划并编写测试、写测试文档、最后发布成 `setup.py` 装进 PATH。QUICKSTART 给的时长口径是 10-15 分钟。生成后可以继续 `/cli-anything:refine` 补覆盖面，官方明确这条命令不做破坏性改动。

生成管道的方法论深读（HARNESS.md 逐阶段拆解）见姊妹篇[《CLI-Anything 方法论》](/posts/tech/cli-anything-universal-cli-framework/)；单个 harness 的目录结构与多平台接入细节见[《产物拆解篇》](/posts/tech/cli-anything-agent-native-software-harness/)。

## 任务流案例：让代理搭一个 Blender 场景

以仓库自带的 Blender harness 为例（v1.0.0，要求 Blender ≥ 4.2），看一个任务怎么流过系统。假设需求是"一个带红色材质的球体、一盏太阳光，渲染一张 1080p 图"：

```bash
# 1. 建场景工程（生成 JSON 场景文件）
cli-anything-blender scene new -o demo.blend-cli.json --engine CYCLES

# 2. 加球体（--json 让输出可供代理直接解析）
cli-anything-blender --json --project demo.blend-cli.json object add sphere \
  --name MySphere --location 0,0,1

# 3. 建材质并赋给球体（assign 按索引取参：材质 0 → 对象 0）
cli-anything-blender --project demo.blend-cli.json material create \
  --name Red --color 1,0,0,1
cli-anything-blender --project demo.blend-cli.json material assign 0 0

# 4. 加太阳光（类型限定 point/sun/spot/area，--power 给功率）
cli-anything-blender --project demo.blend-cli.json light add sun --power 2

# 5. 设渲染参数并执行（execute 需要输出路径，实际渲染交由 Blender 本体完成）
cli-anything-blender --project demo.blend-cli.json render settings \
  --resolution-x 1920 --resolution-y 1080
cli-anything-blender --project demo.blend-cli.json render execute renders/demo.png
```

三条约束贯穿全程，也是这类 CLI 对代理友好的原因：参数类型在定义处收紧（`object add` 的 mesh_type 只接受 cube/sphere/cylinder 等 8 个枚举值，传别的直接报错）；每步操作先写快照，代理可以撤销重来；`--json` 全局开关把输出变成结构化数据，代理不需要解析人读的文本。不装 Blender 本体，这套命令跑不出真实渲染——harness 的前提是目标软件已安装。

## 快速开始

**用现成的 CLI（消费端）**，两条路任选：

```bash
# 路 A：给 SKILL 兼容代理装元技能，让代理自己发现并装 CLI
npx skills add HKUDS/CLI-Anything --skill cli-hub-meta-skill -g -y

# 路 B：直接用包管理器
pip install cli-anything-hub
cli-hub list          # 浏览 79 个 CLI
cli-hub search zotero # 按关键词搜
cli-hub install zotero
```

注意 skill 名带 `cli-anything-` 前缀（如 `cli-anything-blender`），`npx skills add HKUDS/CLI-Anything --list` 可以列出全部。cli-hub 的一级命令共 10 个：install、uninstall、update、list、search、info、launch、previews、can、matrix。

**生成新的 CLI（生成端）**，以 Claude Code 为例：

```bash
/plugin marketplace add HKUDS/CLI-Anything
/plugin install cli-anything
/cli-anything ./your-software
```

平台支持是分层的：Claude Code 有正式插件市场；Cursor、Pi（编码代理）、OpenCode、Codex、Hermes、Reasonix、Qodercli、GitHub Copilot CLI 各有接入指南；SKILL 兼容面覆盖 OpenClaw、Nanobot、Reasonix、Antigravity 等。README 里 Windsurf 标注 coming soon——别把它算进现有支持面。

## 适用边界

**该用：**
- 目标软件只有 GUI 或接口风格杂乱，代理每次都要重新适配——harness 一次生成，永久复用
- 批量、重复、可描述成命令序列的工作流（批量渲染、文献整理、资产处理）
- 想让多个代理共享同一套工具面——SKILL.md 是统一发现入口

**不该用或先确认：**
- 软件已有文档完善的 CLI 或 SDK——直接用原生的更稳，harness 是封装不是替代
- 带运行时前提的 harness 要先看 requires：Zotero CLI 要求 Zotero 7/8 桌面端在运行，Obsidian CLI 依赖 Local REST API 插件，Unreal Insights 只支持 Windows 且需要 UnrealEditor，Kdenlive 需要 melt 在 PATH
- 需要 GUI 精确操作的活（排版微调、像素级修图）——命令行表达不了这类交互
- 79 个 CLI 厚薄悬殊，exa 只有 4 个命令。上生产前先 `--help` 看一眼覆盖面，别按最大样本想象

## 结论

CLI-Anything 的赌注是：代理不需要被教会"看"软件，只需要软件给出能被读懂的接口。七个月长出 79 个 CLI、31 个类目，说明这个赌注至少在开源软件世界立得住；exa 的 4 个命令与 mailchimp 的 292 个并存，也说明它是生态不是产品——质量随贡献者浮动。

给读者的采用顺序：工作流里恰好有 Blender、GIMP、Zotero 这类已有厚 harness 的软件，先装 CLI-Hub 试消费端；有自己想接管的软件且有源码，再走生成端；纯 GUI 交互密集的场景，等 GUI 代理路线成熟或者继续人肉。

三篇姊妹篇按需深入：[方法论深读](/posts/tech/cli-anything-universal-cli-framework/)讲七阶段管道的设计取舍，[产物拆解篇](/posts/tech/cli-anything-agent-native-software-harness/)拆 harness 目录与平台接入，[导论篇](/posts/tech/hkuds-cli-anything-universal-cli-ai/)讲三层结构与 69 个 harness 的厚薄实测。

---

**仓库信息**：https://github.com/HKUDS/CLI-Anything | 官网：https://clianything.cc/ | Stars: 51,338（2026-10-03）| License: Apache 2.0 | 语言：Python
