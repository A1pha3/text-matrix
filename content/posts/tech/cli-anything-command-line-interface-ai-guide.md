---
title: "CLI-Anything 上手指南：安装、生成、使用一条龙"
date: "2026-05-17T20:10:00+08:00"
lastmod: "2026-10-03"
slug: "cli-anything-command-line-interface-ai-guide"
github_repo: "HKUDS/CLI-Anything"
source_key: "gh:HKUDS/CLI-Anything"
description: "CLI-Anything 操作指南：用 cli-hub 包管理器安装现成 CLI，或在 Claude Code 等智能体里用 /cli-anything 命令为任意软件生成完整的命令行接口——七阶段流水线约 10-15 分钟，含测试、文档与 PyPI 发布。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "CLI", "Claude Code", "Python", "开源项目"]
---

# CLI-Anything 上手指南：安装、生成、使用一条龙

给 AI Agent 接上专业软件，GUI 自动化（截图加点击）脆弱，没有 API 的软件则无从下手。CLI-Anything 的做法是给软件生成一套真正的命令行接口：命令分组、会话状态、JSON 输出、测试齐全，Agent 用文本命令就能驱动 Blender 渲染、GIMP 修图、LibreOffice 出 PDF。项目由港大 HKUDS（Data Intelligence Lab@HKU）维护，Apache-2.0 协议，2026-10-03 的 GitHub 读数为 51,338 星。

上手有两条路径，按需求选：

- **只想用现成的**：装 `cli-hub` 包管理器，从注册表里挑一个装好即用。适合目标软件已经有社区 CLI 的场景。
- **要造新的**：在 Claude Code 等 Agent 里装插件，一条 `/cli-anything <软件路径>` 跑完七阶段流水线，产出可 `pip install` 的独立 CLI。适合注册表里还没有的软件、内部工具或代码库。

本文按"装好 → 生成 → 用起来 → 精化 → 测试发布"的顺序走完两条路径，所有命令示例逐一对照过仓库源码（核对基线见文末口径说明）。项目的方法论与生态分析见[方法论深读](/posts/tech/cli-anything-universal-cli-framework/)、[harness 设计解析](/posts/tech/cli-anything-agent-native-software-harness/)与[生态版图](/posts/tech/hkuds-cli-anything-universal-cli-ai-agent/)，此处不重复。

## 准备环境

开始前确认三件事：

| 前置条件 | 要求 | 验证方式 |
| -------- | ---- | -------- |
| Python | 3.10 及以上 | `python3 --version` |
| 目标软件 | 已安装且有源码或本地目录（生成路径需要） | 如 `gimp --version` |
| AI Agent | Claude Code、Cursor、Pi、OpenClaw、OpenCode、Codex、Hermes、Reasonix、Qodercli、GitHub Copilot CLI 之一 | 各平台自带版本命令 |

Windows 用户注意：Claude Code 通过 `bash` 执行命令，需要安装 Git for Windows（自带 `bash` 与 `cygpath`）或改用 WSL，否则会报 `cygpath: command not found`。

平台清单在半年内从 7 个扩到 10 个（2026 年 5 月时尚无 Cursor、Hermes、Reasonix），本文以 2026-10-03 的 README 为准；完整列表见仓库 "Pick Your Agent Platform" 一节。

## 路径一：用现成的 CLI（cli-hub）

CLI-Hub 是项目的 CLI 包管理器，PyPI 包名 `cli-anything-hub`（当前版本 0.4.1）。安装：

```bash
pip install cli-anything-hub
```

七个子命令覆盖全部生命周期：

| 命令 | 作用 |
| ---- | ---- |
| `cli-hub list` | 浏览注册表 |
| `cli-hub search <query>` | 按关键词搜索 |
| `cli-hub info <name>` | 查看某个 CLI 的详情 |
| `cli-hub install <name>` | 安装 |
| `cli-hub update <name>` | 更新 |
| `cli-hub uninstall <name>` | 卸载 |
| `cli-hub launch <name> [args...]` | 运行已安装的 CLI |

以 GIMP 为例走一遍：

```bash
cli-hub search image     # 找图像类的 CLI
cli-hub install gimp     # 安装
cli-hub launch gimp      # 直接运行
```

注意：不少 CLI 包装的是真实桌面软件。注册表条目会写明依赖，比如 GIMP CLI 需要 `gimp`，Exa CLI 需要 `EXA_API_KEY`。装 CLI 之前先把上游软件装好。

## 路径二：造新的 CLI（Agent 插件）

### 在 Claude Code 中安装

CLI-Anything 以 Claude Code 插件市场的形式分发，两条命令：

```bash
/plugin marketplace add HKUDS/CLI-Anything
/plugin install cli-anything
```

不想走市场也可以手动安装：克隆仓库后把插件目录复制到 Claude Code 的插件目录，再重载：

```bash
git clone https://github.com/HKUDS/CLI-Anything.git
cp -r CLI-Anything/cli-anything-plugin ~/.claude/plugins/cli-anything
```

然后在 Claude Code 里执行 `/reload-plugins`。

验证安装：执行 `/help cli-anything`，能看到 CLI-Anything 的命令即成功。

其他平台的安装方式各不相同：Pi 用仓库自带的 `bash .pi-extension/cli-anything/install.sh`（卸载加 `--uninstall`）；OpenClaw、Nanobot、Codex 等 SKILL 兼容平台用统一分发命令（详见下文 SKILL.md 一节）。具体步骤看 README 里对应平台的小节。

### 生成第一个 CLI

```bash
/cli-anything ./gimp
```

路径可以是本地源码目录，也可以是 GitHub 仓库地址（如 `/cli-anything https://github.com/blender/blender`）。旧版本 Claude Code 若不识别 `/cli-anything`，在确认插件已安装加载后改用旧入口 `/cli-anything:cli-anything`；辅助命令始终保持 `/cli-anything:子命令` 形式。

这条命令跑完整个流水线，官方 QUICKSTART 给出的耗时是 **10-15 分钟**（视软件复杂度）。阶段划分以插件内的 HARNESS.md（SOP 文档）为准：

| 阶段 | 名称 | 产出 |
| ---- | ---- | ---- |
| Phase 1 | Codebase Analysis | 扫描源码，把 GUI 操作映射到内部 API |
| Phase 2 | CLI Architecture Design | 命令分组、状态模型、输出格式设计 |
| Phase 3 | Implementation | 用 Click 构建 CLI，含 REPL、JSON 输出、撤销/重做 |
| Phase 4 | Test Planning | 生成 TEST.md（单元 + E2E 测试计划） |
| Phase 5 | Test Implementation | 实现完整测试套件 |
| Phase 6 | Test Documentation | 把测试结果写回 TEST.md |
| Phase 6.5 | SKILL.md Generation | 生成 Agent 可发现的能力定义文件 |
| Phase 7 | PyPI Publishing and Installation | 生成 setup.py 并安装进 PATH |

Phase 6.5 在 README 的七阶段简表里不单列，容易漏掉——它生成的 SKILL.md 是后续 Agent 自动发现这套 CLI 的入口，值得知道它在哪一步发生。

## 安装并验证

生成完成后，CLI 已经装进 PATH（Phase 7 自动完成）。手动安装或重装用：

```bash
cd gimp/agent-harness
pip install -e .
```

验证三连：

```bash
which cli-anything-gimp          # 确认在 PATH 中
cli-anything-gimp --help         # 查看全部命令组
python3 -m cli_anything.gimp.gimp_cli --help   # 绕过 PATH 直接以模块运行
```

生成物是一个标准的 Python 包：入口 `cli-anything-gimp` 定义在 `agent-harness/setup.py` 的 `console_scripts` 里，依赖只有 `click>=8.0.0` 和 `prompt-toolkit>=3.0.0`，`python_requires>=3.10`。目录里的 `skills/SKILL.md` 和 `tests/TEST.md` 分别对应 Phase 6.5 与 Phase 4-6 的产出。

## GIMP CLI 命令速览

以仓库内置的 GIMP 生成物为例（`gimp/agent-harness/`），命令形态全部来自 `gimp_cli.py` 源码。八个命令组：`project`、`layer`、`canvas`、`filter`、`media`、`export`、`session`、`draw`，外加 `repl`。

```bash
# 新建项目：宽高默认 1920x1080，-o 直接落盘
cli-anything-gimp project new --width 1920 --height 1080 -o poster.json

# 新建图层：type 取 image/text/solid，填充色用 --fill
cli-anything-gimp --json layer new -n "Background" --type solid --fill "#1a1a2e"

# 画布操作：resize/scale/crop/mode/dpi
cli-anything-gimp canvas resize --width 800 --height 600

# 滤镜：filter 名是位置参数，参数走 --param 键值对
# 可用滤镜先查 filter list-available（如 gaussian_blur、box_blur）
cli-anything-gimp filter add gaussian_blur --param radius=5

# 导出：输出路径是位置参数，preset 默认 png
cli-anything-gimp export render poster.png --quality 95

# 交互式 REPL：状态跨命令保持
cli-anything-gimp repl
```

三个容易踩的形态差异：`export` 没有 `--output` flag，路径直接跟在 `export render` 后面；`filter add` 的滤镜名是位置参数、数值参数一律 `--param key=value`；主命令挂 `--json` 切结构化输出，对 Agent 消费最友好。每个修改类命令内部都会做会话快照，支持撤销/重做（README 对 Phase 3 的官方口径）。

## 完整任务流：用 Blender CLI 渲染一张图

Blender CLI（`blender/agent-harness/`）有 scene、object、material、modifier、camera、light、animation、render 八个命令组。一次从建场景到出图的完整流程：

```bash
# 1. 新建场景：引擎三选一（CYCLES/EEVEE/WORKBENCH），默认 CYCLES
cli-anything-blender scene new --name kitchen --engine CYCLES

# 2. 加物体：mesh 类型是位置参数，8 选 1
#    cube/sphere/cylinder/cone/plane/torus/monkey/empty
cli-anything-blender object add sphere --name Demo --location 0,0,1

# 3. 建材质并指派：两个位置参数是材质索引和物体索引
cli-anything-blender material create --name Red
cli-anything-blender material assign 0 0

# 4. 配置渲染参数
cli-anything-blender render settings --engine CYCLES --resolution-x 1920 --samples 128

# 5. 执行渲染：输出路径是位置参数
cli-anything-blender render execute ./render.png
```

渲染拆成 `settings` 配置加 `execute` 执行两步，`--engine` 属于 settings 而非 execute——这是照着旧文章抄命令最容易翻车的地方。

## 用 Refine 精化覆盖面

一次生成不可能覆盖软件全部能力。refine 命令做增量补全，支持宽范围和聚焦两种：

```bash
# 全量缺口分析
/cli-anything:refine ./gimp

# 聚焦特定领域
/cli-anything:refine ./gimp "I want more CLIs on image batch processing and filters"
```

官方命令文档（commands/refine.md）对行为的原话是 "Refine never removes existing commands — it only adds or enhances"，即只加不改，可以放心多次运行，逐步逼近完整覆盖。

## 测试与发布

测试不走 CLI 自身的 flag，而是专门的辅助命令或直接 pytest：

```bash
# Agent 内运行（QUICKSTART 口径）
/cli-anything:test gimp

# 手动运行
cd gimp/agent-harness
python3 -m pytest cli_anything/gimp/tests/ -v

# 质量校验：检查 CLI 是否达到项目标准
/cli-anything:validate gimp
```

仓库 badge 的口径是 "Tests 2,461 Passing" 与 "pytest 100% pass"，这是全部已交付 CLI 的合计数字，单套 CLI 的测试结果看各自的 TEST.md。

发布是可选项。setup.py 头部注释给了完整路径：`python -m build && twine upload dist/*`，PyPI 包名沿用 `cli-anything-<software>` 约定（如 `cli-anything-gimp`）。只是自用的话，`pip install -e .` 已经够用。

## SKILL.md：让 Agent 自己发现并安装 CLI

每个生成的 CLI 都带 `skills/SKILL.md`：YAML frontmatter（name、description）加 Markdown 正文（安装方式、前置条件、用法示例）。它不是给人看的 API 文档，而是 Agent 读取后即可上手操作的能力声明。

SKILL 兼容的平台（OpenClaw、Nanobot、Claude Code、Codex、Reasonix、Antigravity 等）用一条命令安装 CLI-Hub 的元技能（meta-skill），装好后 Agent 就能自己走完"搜注册表 → 装合适的 CLI → 读 SKILL.md → 干活"整个流程：

```bash
npx skills add HKUDS/CLI-Anything --skill cli-hub-meta-skill -g -y
```

之后在 Agent 里直接下任务："Find appropriate CLI software in CLI-Hub and complete the task: ..."。

## 平台支持与常见问题

当前支持 10 个 Agent 平台，各自的安装入口：

| 平台 | 安装方式 |
| ---- | -------- |
| Claude Code | 插件市场（`/plugin marketplace add`） |
| Cursor | 见 README 对应小节 |
| Pi | `bash .pi-extension/cli-anything/install.sh` |
| OpenClaw / OpenCode / Codex / Hermes / Reasonix / Qodercli / GitHub Copilot CLI | 见 README 对应小节，SKILL 兼容平台可走 `npx skills add` |

**装完 `/cli-anything` 提示 Unknown skill 怎么办**：换入口形式没用（两种入口指向同一个技能），按顺序排查——先 `/reload-plugins` 重载，再 `/help cli-anything` 确认插件已加载，不行就从市场重装，最后重试 `/cli-anything ./gimp`。

**生成质量能上生产吗**：流水线对结构、测试覆盖、文档完整性有统一要求（HARNESS.md 的规则章），但把生成的 CLI 用于生产前，建议跑完整测试套件、核对 TEST.md 的覆盖率，再对关键命令补充错误处理。生成耗时官方口径 10-15 分钟，不按软件规模分档——比手写一套完整 CLI 快得多，但复杂软件的覆盖广度要靠 refine 迭代补。

**闭源软件能用吗**：生态以开源软件为主（registry 里绝大多数条目有公开源码或仓库）。有 API 文档的闭源软件可以按文档生成封装型 CLI（Exa CLI 就是纯 API 封装的例子）；只有二进制的软件不在设计目标内。

## 生态现状速览

截至 2026-10-03（registry.json 口径）：注册表收录 79 个 CLI，分 31 个类别，数量最多的是 ai（8 个）、devops、web、video、graphics（各 6 个）。README badge 的 "Demos 18 Apps" 指最早走通全流程的专业级验证集，不是支持总数——这是读该仓库数字时最容易混的两个口径。命令面厚薄差距很大：Exa CLI 只有 search、contents、repl 三个命令，而 Mailchimp 这类 API 面大的 CLI 有近 300 个。挑 CLI 时先用 `cli-hub info <name>` 看清命令数与依赖再决定。

## 相关资源

- 仓库：[HKUDS/CLI-Anything](https://github.com/HKUDS/CLI-Anything)（51,338 星，2026-10-03）
- CLI-Hub 官网：<https://clianything.cc/>（旧址 hkuds.github.io/CLI-Anything/ 已 301 到此）
- 中文文档：[README_CN.md](https://github.com/HKUDS/CLI-Anything/blob/main/README_CN.md)
- 技术报告：arXiv:2606.03854
- 包管理器：[PyPI cli-anything-hub](https://pypi.org/project/cli-anything-hub/)（0.4.1）
- 站内相关：[CLI-Anything 方法论深读](/posts/tech/cli-anything-universal-cli-framework/) · [harness 设计解析](/posts/tech/cli-anything-agent-native-software-harness/) · [导论判断篇](/posts/tech/hkuds-cli-anything-universal-cli-ai/) · [生态版图与采用判断](/posts/tech/hkuds-cli-anything-universal-cli-ai-agent/)

## 口径说明

本文 2026-10-03 修订，核对基线：GitHub API 当日读数、仓库 main 分支 HEAD 34f5195（2026-09-22）、QUICKSTART.md 与 HARNESS.md 全文、`gimp`/`blender`/`exa` 三套生成物的 `*_cli.py` 源码、`registry.json`（79 条）、setup.py。原文写作时点（2026-05-17）的平台清单与生态数字已按当次读数刷新，漂移项在文中标注。命令示例与源码逐字核对，若与你本地产物有出入，以生成时的源码为准。
