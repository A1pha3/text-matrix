+++
github_repo = "HKUDS/CLI-Anything"
source_key = "gh:HKUDS/CLI-Anything"
date = '2026-05-17T20:15:00+08:00'
lastmod = 2026-10-02
draft = false
title = 'CLI-Anything：将任意软件变成 AI Agent 可用的 CLI 工具'
slug = 'hkuds-cli-anything-universal-cli-ai'
description = 'HKUDS/CLI-Anything 用一条命令把有源码的软件改造成 Agent 可调用的 CLI。导论篇：三层结构、七个半阶段的生成管道、CLI-Hub 安装，以及 69 个 harness 的厚薄实测。'
categories = ['技术笔记']
tags = ['AI Agent', 'CLI', '开源']
+++

# CLI-Anything：将任意软件变成 AI Agent 可用的 CLI 工具

AI coding agent 已经能读懂一个代码库并替你改代码，但它大概率操作不了 Blender——不是不会，是没有接口。桌面软件要么只有 GUI，要么有一套风格各异的 API，Agent 每换一个软件就要重学一遍。香港大学数据智能实验室（HKUDS）的 CLI-Anything 给出的答案是：只要软件有源码，就用 Agent 把它整个改造成一套命令行接口，一条 `/cli-anything ./gimp` 跑完，装进 PATH 的就是一个 Agent 能直接调用的 `cli-anything-gimp`。

这个项目上线七个月拿下 51,252 star（GitHub API，2026-10-02 读数），Apache 2.0 协议。它容易讲糊，因为实际是三层东西的合体：生成 CLI 的插件、分发 CLI 的包管理器、以及 79 个已经生成好的 CLI 本身。本文是导论——把三层各是什么、生成管道怎么跑、怎么装现成的讲清楚；七阶段方法论的深读见[姊妹篇](/posts/tech/cli-anything-universal-cli-framework/)，单个 harness 的目录结构与多平台接入细节见[产物拆解篇](/posts/tech/cli-anything-agent-native-software-harness/)。

## 三层结构：生成、分发、产物

| 层 | 载体 | 谁会用 |
|------|------|------|
| **生成层** | `cli-anything-plugin/`（Claude Code 插件 + HARNESS.md 七阶段 SOP） | 想为新软件生成 CLI 的贡献者 |
| **分发层** | CLI-Hub（`pip install cli-anything-hub`，PyPI v0.4.1） | 所有用户 |
| **产物层** | 79 个 `cli-anything-<software>` 独立 CLI（registry.json，2026-06-19 更新） | 所有用户 |

多数读者的正确用法只碰后两层：先查注册表里有没有现成的，有就 `cli-hub install` 直接装；没有才轮到生成层出场。这个顺序能省大量时间——生成一个新 CLI 要 Agent 跑十来分钟乃至更久，而装现成的是秒级。

## 生成管道：七个半阶段

`/cli-anything` 命令背后是 HARNESS.md 定义的流水线，实际有八个节点——阶段 6 和 7 之间还插着一个 6.5：

1. **Codebase Analysis** — 扫描源代码，映射可操作的 API 节点
2. **CLI Architecture Design** — 规划命令分组、状态模型、输出格式
3. **Implementation** — 用 Click 构建 CLI，含 REPL 与 JSON 输出
4. **Test Planning** — 生成 TEST.md 前半部分，列出测试方案
5. **Test Implementation** — 实现完整测试套件
6. **Test Documentation** — 测试结果回填 TEST.md 后半部分
6.5. **SKILL.md Generation** — 生成给 Agent 看的工具说明书
7. **PyPI Publishing and Installation** — 发 PyPI，装进 PATH

初版覆盖不全时用 refine 命令增量补充：

```bash
/cli-anything:refine ./gimp "all batch processing and scripting filters"
```

`refine` 接受一个可选的能力域描述，指定了就跳过全面缺口分析、直奔目标区域。插件一共五个命令：`cli-anything`（生成）、`refine`（增量）、`test`（跑测试）、`validate`（验证）、`list`（列出已生成的 harness）。

耗时有个官方口径：QUICKSTART 写明一次完整生成约 10-15 分钟，"取决于软件复杂度"。这不是秒级魔法——Agent 要读完源码、设计接口、写实现、补测试。但对比人肉给 Blender 这类软件写一套完整 CLI 的工程量，这个数仍然成立。

## 接入你的 Agent

支持平台在 README 里有正式清单：Claude Code、Cursor、Pi、OpenClaw、OpenCode、Codex、Hermes、Reasonix、Qodercli、GitHub Copilot CLI，另有 Goose 等社区贡献的实验性接入。以 Claude Code 为例：

```bash
/plugin marketplace add HKUDS/CLI-Anything
/plugin install cli-anything
```

OpenClaw 走 skill 文件：把仓库里的 SKILL.md 复制到 `~/.openclaw/skills/cli-anything/` 即可。注意一个坑——README 目前仍写 `cp CLI-Anything/openclaw-skill/SKILL.md`，但这个目录已经整体改名为 `macrocli`（提交记录原话 "rename openclaw-skill → macrocli throughout"），README 还没跟上；照旧路径 cp 会报文件不存在，实际应复制 `CLI-Anything/macrocli/SKILL.md`。

Windows 用户多一步前置：Claude Code 经由 bash 执行命令，README 要求装 Git for Windows（自带 bash 和 `cygpath`）或改用 WSL，否则会报 `cygpath: command not found`。

## 装现成的：CLI-Hub

```bash
pip install cli-anything-hub
cli-hub list          # 按分类浏览（image、3d、video、audio、office、ai……）
cli-hub install gimp  # 安装单个 harness
```

注册表当前收录 79 个 CLI（registry.json 的 `clis` 字段，2026-06-19 更新），Blender、FreeCAD、GIMP、Godot、Krita、QGIS、Zotero、Obsidian、Draw.io、Zoom 都在里面。另有 24 个收录在 public_registry.json，偏向网络服务类（Sentry、Shopify、飞书、企业微信等）。`cli-hub` 本身只是把对应的 `cli-anything-<software>` 包从 PyPI 装进 PATH，另有 `search`/`info`/`update`/`uninstall` 子命令。

一个隐私细节：cli-hub 默认发送匿名使用事件给 PostHog（README 自述，不收集个人数据），介意的读者可以留意。

## 69 个 harness，厚度差了两个数量级

厚薄差到什么程度，实测比印象有说服力。仓库里 69 个 agent-harness 目录（harness 是项目对单个生成产物的称呼，一套带测试和 SKILL.md 的完整 CLI 实现；68 个 Python，唯一的例外 sketch 是 JS），统计各 harness 全部 `@*.command` 装饰器，命令注册数分布极端：

| harness | 命令数 | 说明 |
|------|------|------|
| mailchimp | 292 | 最厚 |
| freecad | 277 | 19 个分组（part/sketch/body/techdraw/fem/cam 等） |
| firefly-iii | 106 | 记账软件，覆盖面完整 |
| iterm2 | 73 | 中游 |
| blender | 54 | 10 个分组（scene/objects/materials/render 等） |
| exa | 4 | 最薄一档 |

厚度取决于两件事：目标软件的 API 面积，以及生成时的覆盖深度。FreeCAD 这类有完整 Python API 文档的软件，harness 厚得像产品；纯 GUI、接口面窄的软件，可能只有几个命令。所以"CLI-Anything 能不能用"很大程度上是"你要的那个软件的 harness 够不够厚"——装之前先跑 `cli-hub info <name>` 看一眼，或者直接查仓库对应目录。

典型场景核实后的真实形态：

- **Blender**：不自己画图。CLI 生成合法的 bpy 脚本，渲染交给真实 Blender 进程执行，需要 Blender 4.2 以上。它只读写工程文件、不动软件本体，拿不准可以加 `--dry-run` 先试
- **FreeCAD**：277 个命令覆盖 part/sketch/body/techdraw/fem/cam 等十九个分组，厚得可以做正式工作
- **Zotero**：collection/item 两组命令覆盖条目检索、笔记、附件，`item citation` 直接出引用
- **Krita**：project/layer/filter/canvas/export 五个分组，图层增删改查都有
- **Godot**：自带要求 Godot 4.x 在 PATH 的 E2E 测试，二进制不可用时自动跳过

## 数字与增长

| 指标 | 数值（GitHub API，2026-10-02） |
|------|------|
| Stars | 51,252 |
| Forks | 4,672 |
| 语言 | Python |
| 创建时间 | 2026-03-08 |
| 最近推送 | 2026-09-22 |
| License | Apache 2.0 |

2026 年 3 月 8 日创建，七个月到 51k star。增长曲线陡，但更值得注意的是 pushed_at——最近一次推送在 9 月下旬，仓库处于活跃维护状态。

## 采用判断

适合的情况：你要让 Agent 操作的软件有源码、且注册表里已有现成 harness（秒级接入）；或者软件 API 面积大、文档全（生成质量有保障）。不适合的情况：软件是闭源 GUI（生成层需要读源码）、或者现成 harness 太薄覆盖不了你的工作流——先用 `cli-hub info` 探底，再决定装现成还是自己生成。

三个使用前的预期管理：其一，harness 之间厚度差两个数量级，别拿 FreeCAD 的体验预期所有软件；其二，生成耗时以 QUICKSTART 的 10-15 分钟口径为准，别信"几分钟出全套"；其三，文档滞后于代码是这个仓库的常态（OpenClaw skill 改名没同步 README、cli-hub README 还写 "40+ CLI harnesses" 而注册表已 79 条），关键路径以仓库实测为准。

---

- **GitHub**：https://github.com/HKUDS/CLI-Anything
- **CLI-Hub**：https://clianything.cc/
- **方法论深读**：[CLI-Anything：真正的资产是七阶段方法论](/posts/tech/cli-anything-universal-cli-framework/)
- **产物拆解**：[CLI-Anything：harness 目录结构与 SKILL.md 规范](/posts/tech/cli-anything-agent-native-software-harness/)
- **操作指南**：[CLI-Anything 完整上手指南](/posts/tech/cli-anything-command-line-interface-ai-guide/)
