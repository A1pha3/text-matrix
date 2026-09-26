---
title: "Agent Skills：AI Agent 能力扩展开放规范完全指南"
date: "2026-04-02T17:49:04+08:00"
slug: "agent-skills-ai-agent-open-specification-guide"
github_repo: "agentskills/agentskills"
source_key: "gh:agentskills/agentskills"
description: "Agent Skills 是 Anthropic 发起的 AI Agent 能力扩展开放规范。内容覆盖 Skill 格式、工作原理、渐进式披露机制，以及创建、评估和部署生产级 Skill 的完整流程。"
lastmod: "2026-09-20T16:00:00+08:00"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Anthropic"]
---

# Agent Skills：AI Agent 能力扩展开放规范完全指南

Agent Skills 解决的是工具数量增长后上下文被挤占、同一能力跨平台重写两个问题。它把"启动时全量加载工具描述"改成"按需发现并激活"，Agent 启动时只承担元数据开销，未激活的 Skill 始终只占约 50-100 token。这个格式由 Anthropic 于 2025 年 10 月在 Claude 产品线落地，同年 12 月 18 日作为开放标准发布，现在由 agentskills.io 承载规范与文档。

## 目录

- [一、为什么需要 Agent Skills](#一为什么需要-agent-skills)
  - [1.1 传统工具调用的三个痛点](#11-传统工具调用的三个痛点)
  - [1.2 Agent Skills 的解决思路](#12-agent-skills-的解决思路)
  - [1.3 项目生态与兼容实现](#13-项目生态与兼容实现)
  - [1.4 技术规格](#14-技术规格)
- [二、Skill 格式规范](#二skill-格式规范)
  - [2.1 目录结构](#21-目录结构)
  - [2.2 SKILL.md 格式](#22-skillmd-格式)
  - [2.3 Frontmatter 字段详解](#23-frontmatter-字段详解)
  - [2.4 Body 内容](#24-body-内容)
- [三、Skill 工作原理](#三skill-工作原理)
  - [3.1 渐进式披露](#31-渐进式披露)
  - [3.2 Discovery 机制](#32-discovery-机制)
  - [3.3 Activation 机制](#33-activation-机制)
  - [3.4 任务流案例：一次完整的 Skill 调用](#34-任务流案例一次完整的-skill-调用)
- [四、快速入门](#四快速入门)
- [五、skills-ref 参考库](#五skills-ref-参考库)
- [六、高级用法与实践建议](#六高级用法与实践建议)
- [七、开发扩展](#七开发扩展)
- [八、使用场景与适用边界](#八使用场景与适用边界)
- [九、FAQ](#九faq)
- [十、采用建议与总结](#十采用建议与总结)

---

## 一、为什么需要 Agent Skills

传统工具调用方式在工具数量增长后暴露了三个问题，Agent Skills 用渐进式加载来应对。

官网地址：[https://agentskills.io](https://agentskills.io)
规范文档：[https://agentskills.io/specification](https://agentskills.io/specification)

### 1.1 传统工具调用的三个痛点

传统架构要求 Agent 在启动时把所有可用工具的描述加载进上下文。工具数量少时开销可控，但增长到几十个时会出现三个问题：

- **能力膨胀**：Agent 启动时加载的工具描述随工具数量线性增长，这些描述在启动那一刻就全部写死进上下文，无法按任务裁剪
- **上下文污染**：与当前任务无关的工具描述占据上下文窗口，挤压了实际任务可用的空间
- **跨平台困难**：不同 Agent 实现（Claude Code、Copilot Chat、Codex 等）各自定义工具格式，同一个能力要为每个平台重写一遍

### 1.2 Agent Skills 的解决思路

Agent Skills 把"能力"从启动时加载的工具描述，拆成三个阶段按需加载：

| 阶段 | 加载内容 | 触发时机 | 典型 token 开销 |
|------|----------|----------|----------------|
| 元数据 | `name` + `description` | Agent 启动时 | 每个 Skill 约 50-100 token |
| 指令 | `SKILL.md` body | 用户请求匹配 description 时 | 推荐 < 5000 token |
| 资源 | `scripts/`、`references/`、`assets/` | 执行指令过程中需要时 | 按实际使用量 |

启动时只承担元数据开销，未激活的 Skill 不会把指令和资源塞进上下文。工具数量增长时，启动开销只与 Skill 总数的元数据线性相关，激活开销只与命中 Skill 数量相关，两者就此解耦。

### 1.3 项目生态与兼容实现

整个生态由规范文档、参考实现、官方示例库和兼容 Agent 实现四部分组成：

```text
┌─────────────────────────────────────────────────────────┐
│                    Agent Skills 生态                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────┐    ┌─────────────────────────┐    │
│  │  Specification  │    │   Official Repository    │    │
│  │  (规范定义)     │    │   agentskills/agentskills│    │
│  │  agentskills.io │    │   (25.5k Stars)         │    │
│  └────────┬────────┘    └────────────┬────────────┘    │
│           │                              │                │
│           ▼                              ▼                │
│  ┌─────────────────┐    ┌─────────────────────────┐    │
│  │   skills-ref    │    │   Example Skills       │    │
│  │  (Python 参考库)│    │   anthropics/skills    │    │
│  │  验证/读取/生成 │    │   (177k Stars)         │    │
│  └────────┬────────┘    └────────────┬────────────┘    │
│           │                              │                │
│           ▼                              ▼                │
│  ┌─────────────────────────────────────────────┐         │
│  │           兼容的 Agent 实现                  │         │
│  │  Claude Code │ Claude │ ChatGPT/Codex │     │         │
│  │  VS Code │ GitHub Copilot │ Cursor │ …      │         │
│  └─────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────┘
```

兼容实现远不止图中几家：官方 Client Showcase 已收录 46 个产品，从编码工具（Cursor、Gemini CLI、OpenCode、Roo Code）到终端 Agent（Goose、OpenClaw）再到数据平台（Databricks、Snowflake）都有。

### 1.4 技术规格

下表数据采集于 2026-09-20（GitHub API），下文 Stars 数均以此为准：

| 指标 | 数值 |
|------|------|
| 规范版本 | 官方文档未标注版本号 |
| 主仓库 Stars | 25,531 |
| 示例库 Stars | 177,251 |
| Forks | 1,920（主仓库）/ 20,996（示例库） |
| 贡献者 | 41 人（主仓库） |
| 最新提交 | 2026-08-09（Client Showcase 列表更新） |
| 许可证 | 代码 Apache-2.0，文档 CC-BY-4.0 |
| 主要语言 | Python 99.1%, Shell 0.9% |

---

## 二、Skill 格式规范

### 2.1 目录结构

一个 Skill 就是一个文件夹，至少包含一个 `SKILL.md` 文件：

```text
skill-name/
├── SKILL.md          # 必需：元数据 + 指令
├── scripts/          # 可选：可执行脚本
├── references/       # 可选：参考资料文档
├── assets/           # 可选：静态资源（模板、图片、数据文件）
└── ...               # 任意其他文件或目录
```

**命名约束**：

- Skill 目录名必须与 `SKILL.md` 中的 `name` 字段完全一致
- 只能包含小写字母（a-z）、数字（0-9）和连字符（-）
- 不能以连字符开头或结尾
- 不能包含连续两个连字符（`--`）

命名约束有一条硬规则：目录名必须与 `name` 字段完全一致，因为 `name` 是 Skill 在索引里的唯一标识，而目录名就是它在文件系统中的路径。全小写加连字符也是跨平台的稳妥选择——各操作系统文件系统对大小写的处理不同（macOS 默认不敏感，Linux 敏感），统一小写可以避免同一个 Skill 在不同平台上出现两种名字。

### 2.2 SKILL.md 格式

`SKILL.md` 采用 YAML frontmatter（前置元数据）加 Markdown body（正文）的混合格式。frontmatter 可被标准 YAML 解析器（PyYAML、ruamel.yaml 等）直接读取，Agent 在 discovery 阶段只解析 frontmatter 就能拿到元数据，不必扫整个 body；Markdown body 可以直接作为指令喂给 LLM，不需要二次转换。

```markdown
---
name: pdf-processing
description: 提取 PDF 文本和表格、填写表单、合并文件。当处理 PDF 文档或用户提到 PDF、表单、文档提取时使用。
license: Apache-2.0
compatibility: 需要 Python 3.10+ 和 pdfplumber 库
metadata:
  author: example-org
  version: "1.0"
allowed-tools: Bash(python:*) Read
---

# PDF 处理 Skill

[你的指令内容...]
```

### 2.3 Frontmatter 字段详解

| 字段 | 必需 | 约束条件 |
|------|------|----------|
| `name` | 是 | 最多 64 字符，仅小写字母、数字、连字符 |
| `description` | 是 | 最多 1024 字符，描述 Skill 功能和激活时机 |
| `license` | 否 | 许可证名称或对打包许可证文件的引用 |
| `compatibility` | 否 | 最多 500 字符，说明环境要求 |
| `metadata` | 否 | 任意键值对，用于额外元数据 |
| `allowed-tools` | 否 | 空格分隔的预批准工具列表（实验性） |

`name` 限 64 字符、`description` 限 1024 字符，都是规范层面定死的上限：description 会在启动时全量加载进上下文，写太长反而吃掉渐进式披露省下来的空间，官方的建议是"几句话到一小段"；`compatibility` 限 500 字符，它主要在激活时被模型读取，用来说明执行环境要求，官方同时提醒大多数 Skill 其实不需要这个字段。

#### name 字段规则

```yaml
# 合法示例
name: pdf-processing
name: data-analysis
name: code-review

# 非法示例
name: PDF-Processing      # 不能大写
name: -pdf                # 不能以连字符开头
name: pdf--processing     # 不能有连续连字符
```

#### description 字段实践建议

```yaml
# 优秀描述：包含功能 + 激活时机 + 关键词
description: 提取 PDF 文本和表格、填写表单、合并多个 PDF。当处理 PDF 文档、填写表单或文档提取时使用。

# 差劲描述：信息不足
description: Helps with PDFs.
```

### 2.4 Body 内容

Markdown body 包含 Agent 激活 Skill 时执行的指令，没有格式限制。建议包含以下部分：

- **逐步指令**：清晰的操作步骤
- **输入输出示例**：具体的使用案例
- **边界情况处理**：错误处理和特殊情况

```markdown
## 使用步骤

1. 安装依赖：`pip install pdfplumber`
2. 使用 `pdfplumber.extract_text()` 提取文本
3. 使用 `pdfplumber.extract_tables()` 提取表格

## 示例

**输入**：`path/to/document.pdf`
**输出**：`{"text": "...", "tables": [...]}`

## 注意事项

- 扫描版 PDF 需要先 OCR
- 加密 PDF 需要先解密
```

---

## 三、Skill 工作原理

Skill 的运行可以拆成三个相对独立的机制：discovery 负责建索引、activation 负责匹配并加载指令、progressive disclosure 负责按需加载资源。三者触发时机不同、token 开销不同、失败时的影响面也不同。

### 3.1 渐进式披露

Agent Skills 用 progressive disclosure（渐进式披露）控制上下文开销：把内容分成三个阶段按需加载。

```text
┌──────────────────────────────────────────────────────────┐
│                    渐进式披露流程                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  阶段 1：元数据（每个 Skill 约 100 tokens）              │
│  ┌────────────────────────────────────────────────────┐  │
│  │ name + description                                 │  │
│  │ 启动时加载，用于快速匹配和过滤                      │  │
│  └────────────────────────────────────────────────────┘  │
│                          │                               │
│                          ▼                               │
│  阶段 2：指令（推荐 < 5000 tokens）                      │
│  ┌────────────────────────────────────────────────────┐  │
│  │ SKILL.md body                                      │  │
│  │ 激活时加载，完整执行指令                            │  │
│  └────────────────────────────────────────────────────┘  │
│                          │                               │
│                          ▼                               │
│  阶段 3：资源（按需加载）                                │
│  ┌────────────────────────────────────────────────────┐  │
│  │ scripts/、references/、assets/                     │  │
│  │ 仅当执行到相关部分时才加载                          │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

三个阶段的边界是"什么时候读、读多少"。阶段 1 是固定开销，与任务无关；阶段 2 是命中开销，只与激活的 Skill 数相关；阶段 3 是执行开销，只与实际用到的资源相关。做 token 预算时可以分别估这三层，某一层出问题也能单独定位。

### 3.2 Discovery 机制

当 Agent 启动时，会执行 discovery（发现）阶段：

1. **扫描 Skill 目录**：按项目级、用户级两个作用域扫描（见下文）
2. **读取元数据**：仅读取 `name` 和 `description` 字段
3. **构建索引**：将所有 Skill 的元数据加入可用 Skill 列表
4. **等待激活**：仅保存索引，不加载完整内容

先说目录在哪。规范本身不规定 Skill 目录的位置，只定义了目录内部的结构——放哪里是各实现的约定。事实上的跨客户端共享约定是 `.agents/skills/`，分项目级（`<项目>/.agents/skills/`）和用户级（`~/.agents/skills/`）两层，VS Code 默认扫描它；不少实现还同时扫描自己的原生目录（如 Claude 系工具会扫 `.claude/skills/`），以兼容存量 Skill。

```text
# 用户级目录示例
~/.agents/skills/
├── roll-dice/
│   └── SKILL.md
├── pdf-processing/
│   └── SKILL.md
└── README.md        # 不是 Skill 目录，忽略
```

官方实现指南归纳了几条通用扫描规则：项目级、用户级都要扫；跳过 `.git/`、`node_modules/` 这类目录；限制扫描深度（4-6 层、约 2000 个目录）防止大仓库拖慢启动。两个作用域出现同名 Skill 时，通行约定是**项目级覆盖用户级**，并记录警告。

还有一个容易忽略的点：项目级 Skill 来自正在开发的仓库，可能是刚克隆的陌生项目，而 Skill 的指令最终会进入 Agent 上下文——不可信仓库等于一条注入指令的通道。官方工程博客的原话是"只从可信来源安装 Skill"，实现指南则建议给项目级 Skill 加信任门控（例如仅在用户标记该目录为受信任后才加载）。

discovery 阶段只读 frontmatter，不解析 body，单 Skill 开销因此能压到约 100 token。解析策略上官方建议宽松处理：`name` 与目录名不一致、`name` 超长这类问题给警告但照常加载；`description` 缺失或 frontmatter 完全无法解析的 Skill 跳过，不进索引，后续 activation 阶段也不会命中。

### 3.3 Activation 机制

当用户请求触发某个 Skill 时，进入 activation（激活）阶段：

1. **激活判断**：模型对照索引里的 Skill 描述，自行判断当前任务是否命中。官方实现指南特别指出：大多数实现依赖模型自己的判断，而不是在代码层面做关键词匹配
2. **加载指令**：将命中 Skill 的完整 `SKILL.md` 加载到上下文——既可以用模型自带的文件读取工具直接读，也可以通过专用的激活工具返回内容，后者多数会把 frontmatter 剥掉、只喂正文
3. **执行指令**：Agent 按照指令执行任务
4. **按需加载资源**：执行过程中需要时，再加载 `scripts/`、`references/` 等

除了模型自主激活，用户也可以显式触发：主流实现支持斜杠命令（`/skill-name`）或提及语法（`$skill-name`），由客户端直接查找并注入 Skill 内容，跳过模型判断这一步。

activation 阶段会把整个 `SKILL.md` body 读进上下文，body 长度直接决定单次激活的 token 开销。规范给出的是推荐上限：body 控制在 5000 token 以内，超过这个值时把详细参考拆到 `references/`，让 body 只保留执行路径——需要时按"如果 API 返回非 200 就读 references/api-errors.md"这样的条件指令加载，而不是一股脑全读。

两个实现层面的细节值得知道：Skill 内容进入上下文后应当**豁免于上下文压缩**——压缩掉 Skill 指令不会报错，但 Agent 会无声地失去这项能力；如果 Agent 有文件权限系统，应把 Skill 目录加入允许列表，否则每次读捆绑脚本都弹确认框，体验会很割裂。

### 3.4 任务流案例：一次完整的 Skill 调用

以 VS Code + GitHub Copilot 为例，假设 `.agents/skills/` 下有 10 个 Skill。用户在 Copilot Chat 中输入 `Roll a d20`，调用过程分三步：

**阶段 1：启动时的 discovery（一次性开销）**

Agent 启动时扫描 `.agents/skills/`，读取 10 个 Skill 的 `name` + `description`。假设每个 Skill 的元数据约 100 token，这一阶段固定消耗约 1000 token，与后续任务无关。

**阶段 2：用户请求触发 activation**

用户输入 `Roll a d20` 后，Agent 把请求与 10 个 Skill 的 `description` 做匹配。`roll-dice` 的 description 中包含 "roll dice"、"d20" 等关键词，匹配命中。Agent 加载 `roll-dice/SKILL.md` 的完整 body，这部分约 500 token。

**阶段 3：执行指令，按需加载资源**

`roll-dice` 的指令是执行 `echo $((RANDOM % 20 + 1))`，不需要加载 `scripts/` 或 `references/`。如果换成 `pdf-processing`，Agent 会在执行到"调用 `pdfplumber.extract_text()`"时才加载 `scripts/extract_text.py`——指令中明确引用了某个文件，Agent 才会把该文件内容读入上下文。

**token 消耗对比**（估算假设：每个工具描述约 500 token，每个 Skill 元数据约 100 token，只为对比量级）

| 加载方式 | 启动时 | 用户请求时 | 资源加载时 | 总计 |
|----------|--------|------------|------------|------|
| 传统工具调用（10 个工具） | 约 5000 token | 0 | 0 | 约 5000 token |
| Agent Skills（10 个 Skill，激活 1 个） | 约 1000 token | 约 500 token | 按需 | 约 1500 token 起 |

传统工具调用在启动时就把 10 个工具的完整描述塞进上下文；Agent Skills 只在用户请求匹配到具体 Skill 时才加载它的指令，未命中的 9 个 Skill 始终只占用元数据开销。按同样的假设外推到 50 个：传统方式启动时就要消耗约 25000 token，Agent Skills 仍只消耗约 5000 token 的元数据开销。官方实现指南的表述是：装了 20 个 Skill 的 Agent 也不必预付 20 份完整指令的 token，只有当次对话真正用到的才计入。

```bash
# 1. 用户在 Copilot Chat 中输入
Roll a d20

# 2. Copilot 发现 roll-dice skill 的 description 匹配
"Roll dice using a random number generator..."

# 3. 激活 Skill，加载完整 SKILL.md（约 500 token）

# 4. 执行技能指令
# Agent 执行：echo $((RANDOM % 20 + 1))
# 返回：15
```

---

## 四、快速入门

### 4.1 环境准备

**前置条件**：

- VS Code
- GitHub Copilot 扩展（或其他兼容 Agent）

**安装 skills-ref（可选，用于格式校验）**：

```bash
# 克隆官方仓库
git clone https://github.com/agentskills/agentskills.git
cd agentskills/skills-ref

# 官方推荐方式：虚拟环境 + 源码安装
python -m venv .venv
source .venv/bin/activate
pip install -e .

# 或者用 uv 一键完成（自动建虚拟环境并装依赖）
uv sync
source .venv/bin/activate
```

PyPI 上也有 `skills-ref` 包，但官方 README 把这个库定位为"仅供演示，不用于生产"，推荐从源码安装以便跟进仓库的变化。

### 4.2 创建第一个 Skill

**目标**：创建一个投骰子的 Skill

**步骤 1**：创建 Skill 目录

```bash
mkdir -p .agents/skills/roll-dice
```

**步骤 2**：编写 SKILL.md

````markdown
---
name: roll-dice
description: 使用随机数生成器投骰子。当被问到投骰子（d6、d20 等）、
             roll dice 或生成随机骰子点数时使用。
---

# 投骰子指令

## 使用方法

投掷任意面数的骰子，使用以下命令生成 1 到指定面数之间的随机数：

### Bash（Linux/macOS）

```bash
echo $((RANDOM % <sides> + 1))
```

### PowerShell（Windows）

```powershell
Get-Random -Minimum 1 -Maximum (<sides> + 1)
```

## 参数说明

- `<sides>`：骰子的面数
  - d6：`<sides>` = 6
  - d20：`<sides>` = 20
  - d100：`<sides>` = 100

## 示例

**请求**："Roll a d20"
**命令**：`echo $((RANDOM % 20 + 1))`
**结果**：返回 1-20 之间的随机整数
````

官方 quickstart 的原版更精简——参数说明和示例全省了，全篇不到 20 行。Skill 的入门门槛就是一个文件。

### 4.3 验证 Skill

```bash
# 使用 skills-ref 验证 Skill 格式
skills-ref validate .agents/skills/roll-dice
```

这一步是可选的——官方 quickstart 不依赖 skills-ref，写完直接在 Agent 里测也能跑。验证失败时的常见原因：`name` 字段包含大写字母或下划线、`description` 超过 1024 字符、`SKILL.md` 缺少必需字段。根据错误提示修正后重新验证。

### 4.4 在 Agent 中使用

1. 打开 VS Code，进入 Copilot Chat
2. 选择 **Agent** 模式
3. 输入 `/skills` 确认 Skill 已注册
4. 输入 "Roll a d20"
5. Agent 自动激活 `roll-dice` Skill 并执行（可能请求运行终端命令的权限，允许即可）

官方提醒：不同模型对工具调用的可靠性不一样，有的会稳定按 Skill 指令执行命令，有的可能自己直接作答。如果 Agent 没跑终端命令而是自行回复，换一个模型再试。

---

## 五、skills-ref 参考库

### 5.1 简介

`skills-ref` 是 Agent Skills 官方提供的 Python 参考库，提供：

- **Skill 验证**：检查 SKILL.md 格式是否符合规范
- **属性读取**：提取 Skill 的 frontmatter 字段
- **Prompt 生成**：生成 `<available_skills>` XML 块，用于拼进 Agent 的系统提示词

GitHub：[https://github.com/agentskills/agentskills/tree/main/skills-ref](https://github.com/agentskills/agentskills/tree/main/skills-ref)

### 5.2 CLI 命令

```bash
# 验证 Skill 格式
skills-ref validate ./my-skill

# 读取 Skill 属性（输出 JSON）
skills-ref read-properties ./my-skill

# 生成 <available_skills> XML，可一次传多个 Skill
skills-ref to-prompt ./my-skill-a ./my-skill-b
```

### 5.3 Python API

三个 CLI 命令对应三个同名函数，导入路径是 `skills_ref`（下划线），输入输出都是 `pathlib.Path`：

```python
from pathlib import Path
from skills_ref import validate, read_properties, to_prompt

# 验证 Skill 目录，返回问题列表（空列表表示通过）
problems = validate(Path("my-skill"))

# 读取 Skill 属性，返回带 name、description 属性的对象
props = read_properties(Path("my-skill"))

# 生成 <available_skills> XML 字符串
prompt = to_prompt([Path("skill-a"), Path("skill-b")])
```

`to-prompt` 生成的 XML 是官方建议的系统提示词编目格式，`location` 元素告诉模型去哪里读完整指令：

```xml
<available_skills>
<skill>
<name>
my-skill
</name>
<description>
What this skill does and when to use it
</description>
<location>
/path/to/my-skill/SKILL.md
</location>
</skill>
</available_skills>
```

官方 README 说明这个格式是给 Anthropic 模型的建议格式，其他客户端可以按所用模型调整编目样式。要注意 `skills-ref` 的定位：README 明说"仅供演示，不用于生产"——给自研 Agent 集成 Skill 支持时，把它的解析和校验逻辑当参考实现来读，比直接依赖它更稳妥。

---

## 六、高级用法与实践建议

### 6.1 脚本集成

Skill 可以包含可执行脚本。脚本要做到：

- 自包含，或者在注释里写清依赖怎么装
- 报错信息能直接指向失败原因，包含失败文件、行号和具体参数
- 对缺文件、缺参数、缺依赖这类常见边界情况给出可读的提示

**目录结构**：

```text
git-analysis/
├── SKILL.md
└── scripts/
    └── analyze.py    # 可执行的分析脚本
```

**SKILL.md 示例**：

````markdown
---
name: git-analysis
description: 分析 Git 仓库的提交历史、贡献者统计和代码变更。
---

## 使用分析脚本

运行 `scripts/analyze.py` 进行深度分析，输出 JSON 格式的统计结果：

```bash
python scripts/analyze.py --repo ./ --format json
```

脚本会返回包含 `total_commits`、`contributors`、`top_contributors` 字段的 JSON。
````

**输出格式**（JSON）：

```json
{
  "total_commits": 1234,
  "contributors": 42,
  "top_contributors": [
    {"name": "alice", "commits": 320},
    {"name": "bob", "commits": 215},
    {"name": "carol", "commits": 180}
  ]
}
```

### 6.2 参考资料分离

大型 Skill 应把详细参考文档分离到 `references/` 目录。`SKILL.md` body 在激活时会被全量读入上下文，把 API 全文写进 body 会直接吃掉几千 token；`references/` 只在指令显式引用时才加载，未引用的部分不占上下文。

```text
pdf-processing/
├── SKILL.md
├── scripts/
│   ├── extract_text.py
│   └── extract_tables.py
└── references/
    ├── API_REFERENCE.md    # 详细的 API 文档
    ├── FORMATS.md         # 支持的 PDF 格式
    └── EXAMPLES.md        # 更多示例
```

在 SKILL.md 中引用：

```markdown
## 详细 API

请参阅 [API 参考文档](references/API_REFERENCE.md) 获取完整的函数签名。

## 示例

更多示例请查看 [示例集](references/EXAMPLES.md)。
```

### 6.3 资源管理

`assets/` 目录用于存储静态资源：

```text
document-generator/
├── SKILL.md
└── assets/
    ├── templates/          # 文档模板
    │   ├── report.md
    │   └── memo.md
    ├── images/            # 示例图片
    │   └── flowchart.png
    └── data/             # 数据文件
        └── config.json
```

### 6.4 条件兼容性

使用 `compatibility` 字段声明环境要求：

```yaml
---
name: docker-deployment
description: 自动化 Docker 容器部署。当需要构建镜像、部署容器或管理 Docker 环境时使用。
compatibility: 需要 Docker daemon 运行、docker 和 docker-compose 命令可用
---
```

### 6.5 Skill 描述优化

description 是 Agent 判断是否激活 Skill 的主要依据，写不好就会出现"该激活时不激活"或"不该激活时误激活"。三条经验：

**把触发关键词写进去**

```yaml
# 包含多种触发方式
description: 提取 PDF 文本和表格、填写 PDF 表单、合并多个 PDF。
             当用户提到 PDF、表单、文档提取、文本提取时激活。

# 缺少触发词
description: 提取文档内容。
```

**说清激活时机**

```yaml
# 清晰说明使用场景
description: 当需要创建符合公司品牌规范的文档（报告、备忘录、邮件）时使用。
             包含公司徽标、配色方案、字体要求。

# 模糊不清
description: 帮助创建文档。
```

**控制长度，用主动语态**

description 应控制在 1024 字符以内，用主动语态：

```yaml
# 简洁主动
description: 验证 API 响应是否符合 OpenAPI 规范。当需要测试 API、
             验证 JSON 响应或检查 REST 端点时使用。

# 冗长被动
description: 这个 Skill 可以被用来进行 API 相关的验证工作，
             它将会检查输入的 JSON 数据是否...
```

官方的 description 优化指南把这几条经验归纳成四个原则：用祈使句写（"当……时使用"而不是"这个 Skill 可以……"——Agent 是在决定要不要行动，直接告诉它何时行动）；描述用户意图而不是内部实现；宁可把适用场景列得啰嗦一点，用户没直接说出关键词时也要能命中；保持简洁。另有一个容易被忽略的细节：Agent 通常只在任务超出自身基本能力时才去翻 Skill——"读一下这个 PDF"这种一步能完成的请求，即使 description 完美匹配也可能不触发；越是生僻 API、领域流程、不常见格式，description 的价值越大。触发效果可以按 6.7 节的方法量化测试。

### 6.6 指令编写规范

**保持 SKILL.md 在 500 行以内**

```markdown
# 精简指令（< 500 行）

## 核心功能
[2-3 句话概括]

## 使用方法
1. 步骤 1
2. 步骤 2

## 示例
[2-3 个典型案例]

## 注意事项
[关键边界情况]

# 冗长指令
[将详细参考全部写入 SKILL.md]
```

**分离详细参考文档**

```markdown
# SKILL.md - 仅保留摘要

## 功能
计算并验证国际标准书号（ISBN-10 和 ISBN-13）。

## 使用
1. 使用 `scripts/validate_isbn.py <isbn>`
2. 脚本返回验证结果

## 示例
- `python scripts/validate_isbn.py 0-306-40615-2` → 有效

## 详细参考
见 `references/isbn_standard.md`
```

### 6.7 评估与迭代

官方把 Skill 评估拆成两个问题：该触发时有没有触发，触发之后产出质量如何。

**触发评估**（针对 description）：准备约 20 条真实用户提问，一半应该触发、一半不应该。不该触发的重点挑"近失"用例——共享关键词但实际需要别的能力（对 CSV 分析 Skill 来说，"写个 Python 脚本读 CSV 传进数据库"就是高质量的负例）。每条查询跑 3 次算触发率：应触发的要求高于 0.5，不应触发的压在 0.5 以下。再把查询集按 60/40 拆成训练集和验证集——用训练集的失败指导改写 description，用验证集检查改动是否泛化。改写时别把失败查询里的关键词直接抄进 description，那是过拟合；找准这些查询代表的一般类别来回应。通常 5 轮迭代就够，不再提升时问题多半出在查询本身。

**输出质量评估**（针对 SKILL.md 指令）：每个测试用例跑两遍——带 Skill 和不带 Skill（改进已有 Skill 时用旧版本做基线），记录通过率、耗时和 token，用两者的差值（delta）衡量 Skill 的真实贡献：一个通过率提升 50 个百分点但多花 13 秒的 Skill 通常值得，token 翻倍却只换来 2 个百分点提升就未必。测试用例放在 Skill 目录的 `evals/evals.json`（prompt、期望输出、输入文件），断言要可验证（"输出文件是合法 JSON"、"图表有坐标轴标签"）且每项判定附证据。两类断言要专门清理：两种配置下都通过的说明模型本来就会，都在失败的说明断言或用例有问题——它们都不能反映 Skill 的价值。断言覆盖不到的主观质量交给人工复核。

这两套循环重复劳动很多，官方在 anthropics/skills 里提供了 [skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator) 来自动化：拆分评估集、并行测触发率、调用 Claude 提出改进建议、生成 HTML 报告。

**迭代原则**（来自官方最佳实践）：读 Agent 的执行轨迹而不只看最终输出——指令太含糊（Agent 反复试错）、指令不适用于当前任务（Agent 照做不误）、选项太多没有默认值，是浪费步骤的三个常见原因；每次纠正过 Agent 的错误，就把纠正沉淀进指令；给默认值而不是罗列菜单；指令解释"为什么"比生硬的"永远/绝不"更可靠。

---

## 七、开发扩展

### 7.1 创建兼容 Agent

开发 AI Agent 系统时，按以下步骤添加 Skill 支持：

**步骤 1：实现 Discovery**

```python
import re
from pathlib import Path
from typing import Dict, List

def parse_frontmatter(content: str) -> Dict[str, str]:
    """从 SKILL.md 文本中解析 YAML frontmatter。

    只做最简单的 key: value 提取，不处理多行字符串和嵌套结构。
    生产环境建议改用 PyYAML 或 python-frontmatter 库。
    """
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}

    frontmatter: Dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            frontmatter[key.strip()] = value.strip()
    return frontmatter

def discover_skills(skills_dir: Path) -> List[Dict[str, str]]:
    """扫描目录中的所有 Skill，返回元数据索引。

    Args:
        skills_dir: 存放 Skill 子目录的路径，通常是 .agents/skills/。

    Returns:
        包含 name、description、path 三项的字典列表。
    """
    skills: List[Dict[str, str]] = []

    for skill_path in skills_dir.iterdir():
        if not skill_path.is_dir():
            continue

        skill_md = skill_path / "SKILL.md"
        if not skill_md.exists():
            continue

        frontmatter = parse_frontmatter(skill_md.read_text(encoding="utf-8"))

        skills.append({
            "name": frontmatter.get("name", ""),
            "description": frontmatter.get("description", ""),
            "path": str(skill_path),
        })

    return skills
```

**步骤 2：实现 Activation**

```python
def activate_skill(skill_path: Path) -> str:
    """加载完整 SKILL.md 内容到上下文。"""
    skill_md = skill_path / "SKILL.md"
    return skill_md.read_text(encoding="utf-8")
```

**步骤 3：实现渐进式加载**

```python
def load_skill_resources(skill_path: Path, resource_path: str) -> str:
    """按需加载 Skill 内的脚本或参考文档。

    Args:
        skill_path: Skill 根目录。
        resource_path: 相对于 Skill 根目录的文件路径，如 scripts/extract.py。

    Returns:
        文件文本内容；文件不存在时返回空字符串。
    """
    full_path = skill_path / resource_path
    if full_path.exists():
        return full_path.read_text(encoding="utf-8")
    return ""
```

以上是最小骨架。官方的[实现指南](https://agentskills.io/client-implementation/adding-skills-support)把完整生命周期拆成五步，几个关键点值得补进生产实现：

- **扫描边界**：同时扫项目级和用户级两个作用域，同名时项目级覆盖用户级并记录警告；跳过 `.git/`、`node_modules/`，限制扫描深度
- **宽松校验**：`name` 不匹配或超长给警告但照常加载；只有 `description` 缺失、YAML 完全不可解析才跳过。为其他客户端写的 Skill 常有轻微不合规范的 YAML（典型是未加引号的值里含冒号），可以做引号包装的兜底重试
- **信任门控**：项目级 Skill 可能来自刚克隆的陌生仓库，官方建议仅在用户信任该目录后才加载
- **目录编目**：把 `name`、`description`、`location` 以 `<available_skills>` XML 或列表放进系统提示词，附一段简短指令告诉模型怎么加载；没有任何可用 Skill 时，编目和指令都不要输出
- **上下文管理**：给 Skill 内容套上可识别的结构化标签（如 `<skill_content name="...">`），上下文压缩时豁免；同一会话重复激活同一 Skill 时去重
- **权限**：把 Skill 目录加入文件读取允许列表，避免每次读捆绑资源都弹确认框

### 7.2 工具预批准机制

`allowed-tools` 字段允许 Skill 定义可使用的预批准工具：

```markdown
---
name: git-workflow
description: 执行标准 Git 工作流程。用于提交代码、创建分支、合并请求等。
allowed-tools: Bash(git:*) Bash(gh:*) Read
---

# Git 工作流 Skill

## 创建分支并提交

1. 使用 `gh auth` 验证 GitHub CLI
2. 执行 `git checkout -b feature/new-feature`
3. 执行 `git add . && git commit -m "feat: add new feature"`
```

### 7.3 发布与分发

Skill 的分发没有中心化市场，官方仓库在 CONTRIBUTING.md 里明确表示**目前不接受社区 Skill 提交**——官方不维护社区 Skill 目录。实际可行的路径：

1. **自建仓库分发**：把 Skill 放进独立 Git 仓库或组织内部仓库，团队克隆后装进各自的 `.agents/skills/`，靠版本控制管理更新
2. **贡献官方示例库**：通用性强的 Skill 可以向 [anthropics/skills](https://github.com/anthropics/skills) 提 PR
3. **加入 Client Showcase**：如果你做的是 Agent 产品且已实现 Skill 支持，按 CONTRIBUTING.md 的要求提交 PR——产品必须公开可用、能实际发现和执行 Skill，仅宣布支持或还在私测的产品不收；通过审核后列入 agentskills.io 的展示页

---

## 八、使用场景与适用边界

### 8.1 何时该把能力做成 Skill

满足以下任一条件时，把能力做成 Skill 比写进系统提示词更合适：

- **按需加载**：不是每次对话都会用到，避免常驻上下文。例如 PDF 处理、Git 工作流、合同审查。
- **有明确触发关键词**：description 能写出具体的激活条件，而非泛泛的"辅助开发"。
- **需要附带脚本或参考资料**：Skill 的 `scripts/`、`references/`、`assets/` 结构适合承载多文件资源。
- **跨项目复用**：Skill 是独立文件夹，放进不同项目的 `.agents/skills/` 就能直接用。
- **需要版本管理和团队共享**：作为独立 Git 仓库或子模块，便于版本控制和分发。

### 8.2 何时直接写系统提示词更合适

满足以下任一条件时，写进系统提示词比做成 Skill 更合适：

- **全局基础行为**：例如输出语言偏好、代码风格约束、回复格式要求，每次对话都要生效。
- **指令很短且无附带资源**：几行就能说清，没有脚本和参考资料。
- **每次对话都会用到**：做成 Skill 反而多一层 activation 开销。
- **项目特定的临时指令**：只服务于当前项目，不需要复用。

### 8.3 典型场景示例

#### 企业内部工具

**场景**：为团队创建统一的代码审查 Skill

```markdown
---
name: enterprise-code-review
description: 按照公司安全规范进行代码审查。检查 SQL 注入、XSS、
             敏感信息暴露等安全问题。当需要进行代码审查、
             安全扫描或合规检查时激活。
compatibility: 需要 SonarQube CLI 和公司安全规则库
metadata:
  team: security
  tier: critical
---

# 企业代码审查 Skill

## 安全检查清单

- [ ] SQL 注入防护
- [ ] XSS 输出编码
- [ ] 敏感信息加密存储
- [ ] API 限流实现
```

#### 领域专家助手

**场景**：创建法律文档分析 Skill

```markdown
---
name: contract-analysis
description: 分析商业合同条款，识别风险点。用于审阅采购合同、
             服务协议、劳动合同等。当用户提到合同审查、
             法律风险或条款分析时激活。
---

# 合同分析 Skill

## 风险识别

### 高风险条款
1. 无限责任条款
2. 竞业禁止过宽
3. 违约金不成比例

### 红旗标志
- "乙方自愿放弃一切诉讼权利"
- "甲方有权随时解除合同"
```

#### 自动化工作流

**场景**：CI/CD 流水线 Skill

```markdown
---
name: ci-pipeline-debug
description: 诊断和修复 CI/CD 流水线问题。用于 GitHub Actions、
             GitLab CI 或 Jenkins 构建失败排查。当构建失败、
             流水线报错或部署问题时激活。
allowed-tools: Bash(git:*) Bash(docker:*) Read
---

# CI/CD 调试 Skill

## 诊断流程

1. 读取 `.github/workflows/*.yml`
2. 分析错误日志
3. 定位问题步骤
4. 提供修复建议
```

---

## 九、FAQ

### Q1：Skill 和普通的系统提示词有什么区别？

主要区别在于加载时机和复用方式：

| 特性 | 系统提示词 | Agent Skills |
|------|-----------|--------------|
| 加载时机 | 固定加载 | 按需激活 |
| 上下文影响 | 全局占用 | 局部加载 |
| 复用性 | 平台锁定 | 开放格式 |
| 版本管理 | 需修改代码 | 通过增删 Skill 文件管理 |

### Q2：一个 Agent 可以同时激活多个 Skill 吗？

可以，Skill 在设计上就是可组合的，同一个任务加载多个 Skill 是正常用法。真正的约束是上下文预算：每多激活一个 Skill，就多一份 body 的上下文占用。控制的关键在粒度——一个 Skill 封装一个内聚的工作单元（官方的最佳实践类比是"像决定一个函数该做什么"）：粒度太细会逼着单个任务加载一堆 Skill，增加指令相互冲突的风险；太粗又难以精准触发。

### Q3：Skill 的 token 开销是多少？

各阶段开销：

| 阶段 | token | 触发时机 |
|------|-------|----------|
| 元数据 | 约 50-100 | 每次启动 |
| 指令 | < 5000（推荐上限） | 每次激活 |
| 资源 | 按需 | 执行中 |

### Q4：如何处理 Skill 之间的冲突？

规范层面没有冲突仲裁机制，description 是模型判断的主要入口：

1. **细化 description**：在 description 中明确各自的使用范围和边界，减少重叠
2. **让模型决策**：两个都命中时，模型会根据当前任务上下文选择更合适的
3. **自定义元数据**：`metadata` 是任意键值对，官方建议把键名取得足够独特以避免意外冲突，可以用它放自己的标记——但这只是扩展点，没有通用的"冲突解决"语义

### Q5：可以使用哪些脚本语言？

取决于 Agent 实现。规范列出的常见选项是 Python、Bash 和 JavaScript。除了打包进 `scripts/` 的脚本，官方也推荐在指令里直接用一次性命令：Python 生态的 uvx、pipx，Node 生态的 npx、bunx，以及 `deno run`、`go run`，用 `@版本` 固定版本保证可复现。

### Q6：Skill 可以访问网络吗？

取决于 Agent 实现的权限和沙箱机制。`compatibility` 字段只负责声明需求，不是授权开关：

```yaml
# 声明网络需求
compatibility: 需要互联网访问，用于调用外部 API
```

### Q7：Skill 执行失败时如何排查？

常见排查路径：

1. **验证格式**：先运行 `skills-ref validate ./my-skill` 确认 SKILL.md 格式正确
2. **检查 description**：确认 description 中包含足够的触发关键词
3. **查看 Agent 日志**：检查 Skill 是否被 discovery 阶段正确扫描到
4. **测试脚本独立执行**：如果 Skill 调用了 `scripts/` 下的脚本，先在终端中独立运行该脚本，确认脚本本身没有问题
5. **检查 compatibility**：确认运行环境满足 `compatibility` 字段声明的依赖

---

## 练习题

### 练习一：创建一个文件备份 Skill（入门）

**目标**：创建一个能在本地自动备份指定文件的 Skill。

**步骤**：
1. 创建 `.agents/skills/backup-file` 目录
2. 编写 `SKILL.md`，包含 `name`、`description`、`license` 字段
3. 在 `scripts/` 下写备份脚本，接受源路径和目标路径两个参数
4. 用 `skills-ref validate` 验证格式
5. 在 Agent 中测试激活

**验收标准**：
- `description` 中包含"备份文件""增量备份"等触发关键词
- 脚本能处理"文件不存在""目标目录不存在"两种边界情况
- 激活后 Agent 能正确执行备份并记录备份时间

<details>
<summary>参考答案</summary>

**SKILL.md 核心字段**：

```yaml
name: backup-file
description: 备份指定文件到目标目录，支持增量备份。
             当用户提到备份文件、保存副本、同步文档时使用。
license: MIT
```

**评分要点**：
1. `name` 全小写、无连续连字符（1 分）
2. `description` 包含触发关键词（1 分）
3. 脚本处理"文件不存在"边界（1 分）
4. 用 `skills-ref validate` 验证通过（1 分）
5. Agent 激活测试能正确执行（1 分）

</details>

### 练习二：把团队高频操作用 Skill 封装（进阶）

选一个你的团队每周至少执行 3 次的操作用 Skill 封装：
- 发布前检查清单
- 数据库迁移脚本
- 日志排查快捷命令

完成以下任务：
1. 写出这个操作的「触发关键词表」（`description` 字段用）
2. 判断哪些资源该放进 `scripts/`，哪些该放进 `references/`
3. 写一个 50 行以内的 `SKILL.md` body，只保留执行路径
4. 找一个同事，让他不看 `SKILL.md` 原文，只通过 Agent 对话来完成这个操作——记录他卡在哪一步

**信号**：如果同事卡在"不知道该说什么才能触发"，说明 `description` 缺少触发关键词；如果卡在"激活了但执行不对"，说明指令不够精确。

### 练习三：在已有 Agent 系统里评估 Skill 迁移收益（高阶）

如果你团队的 Agent 系统目前把所有工具描述在启动时全量加载，按以下步骤评估迁移到 Skill 的收益：

1. 统计当前启动时加载的工具描述总 token 数
2. 估算日常对话中实际命中的工具比例（例如 10 个工具里平均用 2 个）
3. 按 Skill 渐进式披露的三阶段模型，计算迁移后的 token 节省量
4. 列出迁移成本：需要改的几个接口、需要转换的几个工具描述

**决策规则**：如果启动时 token 开销超过 3000 且日常命中率低于 40%，迁移通常有正 ROI。

---

## 自测题

读完本文后，先自己想 30 秒再展开答案：

<details>
<summary>1. Skill 的 `name` 字段和目录名必须完全一致，这条规则解决了哪两个问题？</summary>

第一，`name` 必须与父目录名一致，而目录名就是文件系统路径——各操作系统对大小写的处理不同（macOS 默认不敏感，Linux 敏感），全小写加连字符能保证同一个 Skill 在任何平台上都是同一个名字；第二，`name` 是 Agent 索引 Skill 的唯一标识，规范因此把字符集收得很紧：只允许小写字母、数字和连字符，不能以连字符开头或结尾，也不能出现连续连字符。
</details>

<details>
<summary>2. 渐进式披露的三阶段分别解决什么开销问题？</summary>

阶段 1（元数据）解决「启动开销」——Agent 启动时只扫 `name` + `description`，每个 Skill 约 100 token；阶段 2（指令）解决「命中开销」——只加载被用户请求匹配的 Skill 的完整 `SKILL.md`；阶段 3（资源）解决「执行开销」——只在指令显式引用时才读 `scripts/`、`references/`、`assets/` 里的文件。
</details>

<details>
<summary>3. 什么时候该把能力做成 Skill，什么时候直接写进系统提示词？</summary>

做成 Skill：不是每次对话都用得到、有明确触发关键词、需要附带脚本或参考资料、需要跨项目复用、需要版本管理。写进系统提示词：全局基础行为（如输出语言偏好）、指令很短且无附带资源、每次对话都会用到、只服务于当前项目的临时指令。
</details>

<details>
<summary>4. `description` 字段写得好不好，直接影响什么指标？</summary>

直接影响「激活准确率」——相关请求中 Skill 被正确激活的比例。写得好：`description` 包含功能描述 + 触发时机 + 关键词，Agent 能准确匹配；写得差：只写"帮助处理文档"这种模糊描述，会导致该激活时不激活、不该激活时误激活。
</details>

<details>
<summary>5. 如果 `SKILL.md` 的 body 超过 5000 token，规范推荐怎么处理？</summary>

把详细参考文档拆到 `references/` 目录，让 `SKILL.md` body 只保留执行路径和摘要。`references/` 里的文件只在指令显式引用时才加载，未引用的部分不占上下文。`body` 控制在 5000 token 以内，激活时的上下文开销更可控。
</details>

---

## Skill 快速参考卡

### 最小 SKILL.md

```yaml
---
name: my-skill
description: 功能描述。触发时机。关键词。
license: MIT
compatibility: 需要 Python 3.10+
---

# 技能名

## 使用步骤
1. ...

## 示例
...
```

### 渐进式披露：三阶段 token 开销

| 阶段 | 加载内容 | 典型 token |
|------|----------|-------------|
| 元数据 | `name` + `description` | ~50-100 / Skill |
| 指令 | `SKILL.md` body | < 5000（推荐上限） |
| 资源 | `scripts/` / `references/` | 按需 |

### `description` 写作三问

1. **功能**：这个 Skill 能做什么？
2. **时机**：用户说什么会激活它？
3. **关键词**：哪些术语应该命中？

### 常见 discovery 失败原因

- `SKILL.md` 文件不存在
- YAML frontmatter 格式错误（缺少 `---` 或字段格式不对）
- `name` 包含大写字母或非法字符

---

## 进阶路径

读完本文后，按以下顺序深入：

1. **跑通一个官方 Skill**：从 [anthropics/skills](https://github.com/anthropics/skills) 挑一个高频场景的 Skill 放进 `.agents/skills/`，确认你选用的 Agent 能正确 discovery 和 activation
2. **封装一个团队高频操作**：识别团队内部重复执行 3 次/周以上的流程，按本文的 Skill 格式规范做成 Skill
3. **接入 Skill 发现机制**：如果团队现有 Agent 系统是全量加载工具描述，评估迁移到 Skill 渐进式披露的 ROI
4. **读 `skills-ref` 源码**：理解 `validate`、`read-properties`、`to-prompt` 三个命令的内部实现，为团队定制 Skill 校验规则做准备
5. **关注 Agent Skills 社区**：Bug 走 [GitHub Issues](https://github.com/agentskills/agentskills/issues)，规范提案和开放讨论走 [GitHub Discussions](https://github.com/agentskills/agentskills/discussions)，官方 Discord（[邀请链接](https://discord.gg/MKPE9g8aUy)）用于交流正在构建的东西

---

## 十、采用建议与总结

### 采用顺序

如果团队准备引入 Skill，建议按这个顺序推进，每步验证通过再进入下一步：

1. **先跑通官方 Skill**：从 [anthropics/skills](https://github.com/anthropics/skills) 挑 1-2 个高频场景的 Skill 放进 `.agents/skills/`，确认团队选用的 Agent（Claude Code、Copilot Chat、Codex 等）能正确 discovery 和 activation。这一步只验证机制可用，不写新 Skill。
2. **再封装团队高频操作**：识别团队内部重复执行的流程（发布前检查、数据库迁移、日志排查），先做 2-3 个高质量 Skill 作为模板，再让其他成员按模板补齐。
3. **最后封装领域专家知识**：安全合规、合同条款、领域规范这类需要专家参与的能力放到最后，采用"专家提供内容 + 工程师整理格式"的协作模式。

### 适用边界

Skill 适合承载按需加载、有明确触发词、需要附带脚本或参考资料、需要跨项目复用的能力；每次对话都要生效的全局基础行为、几行就能说清的指令、只服务于当前项目的临时指令，写进系统提示词更合适。详细判断标准见 8.1 和 8.2 节。

### 关键事实

- Agent Skills 把工具加载从"启动时全量塞进上下文"改成"按需激活"，工具数量增长后上下文不会被无关描述挤占
- 渐进式披露分三阶段：启动时只读元数据，请求匹配时才加载指令，执行过程中按需读取 `scripts/`、`references/`、`assets/`
- 同一个 Skill 文件夹可以在 Claude Code、Copilot Chat、Codex 等兼容实现里直接用，不需要为每个平台重写
- 新增能力在 `.agents/skills/` 下加文件夹即可，不用改 Agent 本身的代码

### 生态现状

- **官方库**：agentskills/agentskills（25.5k Stars，数据截至 2026-09-20，后续可能变化）
- **示例库**：anthropics/skills（177k Stars，含 Excel、PowerPoint、Word、可填写 PDF 等官方技能和 skill-creator）
- **兼容实现**：Client Showcase 收录 46 家——Claude Code、Claude、ChatGPT/Codex、VS Code、GitHub Copilot、Cursor、Gemini CLI、Goose、OpenClaw 等
- **社区**：Discord 服务器 + GitHub Discussions
- **文档**：agentskills.io（Mintlify 托管，文档以 CC-BY-4.0 发布）

### 参与贡献

贡献方式见仓库的 CONTRIBUTING.md，不同事项走不同通道：

```bash
# 克隆官方仓库
git clone https://github.com/agentskills/agentskills.git
cd agentskills

# 文档改进：docs/ 目录，直接提 PR
# Bug 报告：GitHub Issues
# 规范提案与讨论：GitHub Discussions
```

两点官方立场值得知道：其一，规范新增功能门槛很高，CONTRIBUTING.md 的原话是"往规范里加东西比移除容易得多……拿不准就别加"，提案要附上真实遇到的实现难题而不是理论担忧；其二，skills-ref 参考库暂时不接受代码贡献（方向还在确定），Bug 和反馈走 Issue 和 Discussion。

---

## 相关链接

| 资源 | 地址 |
|------|------|
| 官网 | [https://agentskills.io](https://agentskills.io) |
| 规范文档 | [https://agentskills.io/specification](https://agentskills.io/specification) |
| 快速入门 | [https://agentskills.io/skill-creation/quickstart](https://agentskills.io/skill-creation/quickstart) |
| GitHub 主仓库 | [https://github.com/agentskills/agentskills](https://github.com/agentskills/agentskills) |
| 示例 Skill 库 | [https://github.com/anthropics/skills](https://github.com/anthropics/skills) |
| Discord 社区 | [https://discord.gg/MKPE9g8aUy](https://discord.gg/MKPE9g8aUy) |

---

*文档更新：2026-09-20 | 来源：[agentskills/agentskills](https://github.com/agentskills/agentskills)*

## 资料口径说明

1. **数据时效**：文中 Stars、贡献者等数据采集于 2026-09-20（GitHub API），仅为当日快照；Agent Skills 生态迭代很快，使用时请以最新数据为准。
2. **规范版本**：官方规范文档未标注版本号，本文以 2026-09-20 的 [agentskills.io/specification](https://agentskills.io/specification) 为口径。
3. **目录约定**：`.agents/skills/` 是跨客户端共享的行业约定而非规范强制（规范不规定目录位置）；各 Agent 另有自己的原生目录（如 `.claude/skills/`），以各工具官方文档为准。
4. **工具兼容性**：文中提到的 Claude Code、Claude、ChatGPT/Codex、VS Code、GitHub Copilot、Cursor 等对 Skill 的支持方式可能随版本变化，实际使用时请参考各工具的官方文档。
5. **skills-ref 定位**：参考库按官方 README 说明"仅供演示，不用于生产"；文中 Python API 与 CLI 输出以 skills-ref README（2026-09-20 版）为口径，可能随版本变化。
6. **原文来源**：本文基于 [agentskills/agentskills](https://github.com/agentskills/agentskills) 开源项目与 agentskills.io 官方文档。如需引用，请注明项目链接。

