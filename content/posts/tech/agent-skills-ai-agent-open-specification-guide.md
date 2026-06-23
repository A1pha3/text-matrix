---
title: "Agent Skills：AI Agent 能力扩展开放规范完全指南"
date: "2026-04-02T17:49:04+08:00"
slug: "agent-skills-ai-agent-open-specification-guide"
description: "Agent Skills 是 Anthropic 主导的 AI Agent 能力扩展开放规范。本文详细介绍了 Skill 格式、工作原理、渐进式披露机制，以及如何创建、评估和部署生产级 Skill。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Anthropic", "Skill 扩展", "开放规范", "渐进式披露"]
---

# Agent Skills：AI Agent 能力扩展开放规范完全指南

Agent Skills 解决的是工具数量增长后上下文被挤占、同一能力跨平台重写这两件具体事。它把"启动时全量加载工具描述"改造成"按需发现并激活"，让 Agent 启动时只承担元数据开销，未命中的 Skill 始终只占约 100 token。本文按"为什么需要 → 格式规范 → 工作原理 → 上手 → 进阶 → 集成 → 适用边界 → 采用建议"的顺序展开，结尾给出团队引入顺序。

## 学习目标

读完可以对照检查下面几个问题：

- Agent Skills（智能体技能）解决的是哪类工具调用问题？什么时候不该用它？
- 怎么写一个符合规范的 `SKILL.md`，frontmatter（前置元数据）每个字段管什么？
- 从零开始做一个带指令、脚本和参考资料的 Skill，需要走哪些步骤？
- discovery（发现）、activation（激活）和 progressive disclosure（渐进式披露）三个阶段是怎么串起来的？
- 在自己团队的 Agent 系统里集成 Skill 支持，要实现哪些接口？
- 团队引入 Skill 时，按什么顺序试错成本最低？

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

Agent Skills（智能体技能，下文简称 Skill）是 Anthropic 主导的开放规范，由规范文档、参考实现、官方示例库和兼容 Agent 实现四部分组成。它针对两个具体场景：工具数量一多，启动时塞进上下文的工具描述就挤占任务可用空间；同一个能力要在 Claude Code、Copilot Chat、Codex 等不同实现里各写一遍。

官网地址：[https://agentskills.io](https://agentskills.io)
规范文档：[https://agentskills.io/specification](https://agentskills.io/specification)

### 1.1 传统工具调用的三个痛点

传统架构要求 Agent 在启动时把所有可用工具的描述加载进上下文。工具数量少时开销可控，但增长到几十个时会出现三个具体问题：

- **能力膨胀**：Agent 启动时加载的工具描述随工具数量线性增长，每个工具描述通常占用 200-500 token（令牌）
- **上下文污染**：与当前任务无关的工具描述占据上下文窗口，挤压了实际任务可用的空间
- **跨平台困难**：不同 Agent 实现（Claude Code、Copilot Chat、Codex 等）各自定义工具格式，同一个能力要为每个平台重写一遍

### 1.2 Agent Skills 的解决思路

Agent Skills 把"能力"从启动时加载的工具描述，拆成三个阶段按需加载：

| 阶段 | 加载内容 | 触发时机 | 典型 token 开销 |
|------|----------|----------|----------------|
| 元数据 | `name` + `description` | Agent 启动时 | 每个 Skill 约 100 token |
| 指令 | `SKILL.md` body | 用户请求匹配 description 时 | 500-2000 token |
| 资源 | `scripts/`、`references/`、`assets/` | 执行指令过程中需要时 | 按实际使用量 |

启动时只承担元数据开销，未激活的 Skill 不会把指令和资源塞进上下文。这样工具数量增长时，启动开销只与 Skill 总数的元数据线性相关，激活开销只与命中 Skill 数量相关，两条增长曲线被拆开。

### 1.3 项目生态与兼容实现

Agent Skills 规范由四个部分支撑：规范文档、参考实现、官方示例库和兼容的 Agent 实现。

```text
┌─────────────────────────────────────────────────────────┐
│                    Agent Skills 生态                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────┐    ┌─────────────────────────┐    │
│  │  Specification  │    │   Official Repository    │    │
│  │  (规范定义)     │    │   agentskills/agentskills│    │
│  │  agentskills.io │    │   (16.3k Stars)         │    │
│  └────────┬────────┘    └────────────┬────────────┘    │
│           │                              │                │
│           ▼                              ▼                │
│  ┌─────────────────┐    ┌─────────────────────────┐    │
│  │   skills-ref    │    │   Example Skills       │    │
│  │  (Python SDK)   │    │   anthropics/skills    │    │
│  │  验证/读取/转换 │    │   (108.9k Stars)       │    │
│  └────────┬────────┘    └────────────┬────────────┘    │
│           │                              │                │
│           ▼                              ▼                │
│  ┌─────────────────────────────────────────────┐         │
│  │           兼容的 Agent 实现                  │         │
│  │  Claude Code │ Claude.ai │ OpenAI Codex │   │         │
│  │  VS Code Copilot │ 其他兼容实现              │         │
│  └─────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────┘
```

### 1.4 技术规格

下表数据采集于 2026-03-28，后续引用的 Stars 数均以此表为准：

| 指标 | 数值 |
|------|------|
| 规范版本 | v1.0 |
| 主仓库 Stars | 16,306 |
| 示例库 Stars | 108,862 |
| Forks | 959（主仓库）/ 12,170（示例库） |
| 贡献者 | 35 人（主仓库） |
| 最新提交 | 2026-03-28 |
| 许可证 | Apache-2.0 |
| 主要语言 | Python 99.1%, Shell 0.9% |

---

## 二、Skill 格式规范

### 2.1 目录结构

一个 Skill 本质上是一个文件夹，至少包含一个 `SKILL.md` 文件：

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

命名约束的存在有两层原因：一是目录名要直接作为文件系统路径，全小写加连字符可以避免 macOS/Windows 大小写敏感差异；二是 `name` 字段会被 Agent 用作唯一标识，禁止连续连字符可以防止与 `--flag` 形式的命令行参数混淆。

### 2.2 SKILL.md 格式

`SKILL.md` 采用 YAML frontmatter（前置元数据）加 Markdown body（正文）的混合格式。选 YAML frontmatter 是因为它可被标准解析器（PyYAML、rufo 等）直接读取，Agent 在 discovery 阶段只需解析 frontmatter 就能拿到元数据，不必扫整个 body；Markdown body 则可以直接作为指令喂给 LLM，不需要二次转换。

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

`name` 限 64 字符是为了在 discovery 阶段做索引时控制单条记录大小；`description` 限 1024 字符是因为它会在启动时全量加载进上下文，过长会直接抵消渐进式披露的收益；`compatibility` 限 500 字符是因为它只在激活后才会被读取，但仍要避免被当作指令注入。

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

Skill 的运行可以拆成三个相对独立的机制：discovery 负责建索引、activation 负责匹配并加载指令、progressive disclosure 负责按需加载资源。三者触发时机不同、token 开销不同、失败时的影响面也不同，需要分开看。

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

三个阶段的边界是"什么时候读、读多少"。阶段 1 是固定开销，与任务无关；阶段 2 是命中开销，只与激活的 Skill 数相关；阶段 3 是执行开销，只与实际用到的资源相关。这种拆分让 token 预算可以分别估算，也方便在某一层失败时单独排查。

### 3.2 Discovery 机制

当 Agent 启动时，会执行 discovery（发现）阶段：

1. **扫描 Skill 目录**：默认扫描 `.agents/skills/`
2. **读取元数据**：仅读取 `name` 和 `description` 字段
3. **构建索引**：将所有 Skill 的元数据加入可用 Skill 列表
4. **等待激活**：仅保存索引，不加载完整内容

```text
# 默认 Skill 目录结构
project/
├── .agents/
│   └── skills/           # 默认扫描此目录
│       ├── roll-dice/
│       │   └── SKILL.md
│       ├── pdf-processing/
│       │   └── SKILL.md
│       └── ...
```

discovery 阶段只读 frontmatter，不解析 body，这是它能把单 Skill 开销压到约 100 token 的原因。如果 discovery 阶段失败（比如 `SKILL.md` 缺失或 frontmatter 解析错误），该 Skill 不会进入索引，后续 activation 阶段也不会命中它。

### 3.3 Activation 机制

当用户请求触发某个 Skill 时，进入 activation（激活）阶段：

1. **匹配判断**：Agent 将用户请求与所有 Skill 的 `description` 匹配
2. **加载指令**：将匹配的 Skill 的完整 `SKILL.md` 加载到上下文
3. **执行指令**：Agent 按照指令执行任务
4. **按需加载资源**：执行过程中需要时，再加载 `scripts/`、`references/` 等

activation 阶段会把整个 `SKILL.md` body 读进上下文，所以 body 长度直接决定单次激活的 token 开销。规范推荐 body 控制在 5000 token 以内，超过这个值时建议把详细参考拆到 `references/`，让 body 只保留执行路径。

### 3.4 任务流案例：一次完整的 Skill 调用

以 VS Code + GitHub Copilot 为例，假设 `.agents/skills/` 下有 10 个 Skill。用户在 Copilot Chat 中输入 `Roll a d20`，整个调用过程如下：

**阶段 1：启动时的 discovery（一次性开销）**

Agent 启动时扫描 `.agents/skills/`，读取 10 个 Skill 的 `name` + `description`。假设每个 Skill 的元数据约 100 token，这一阶段固定消耗约 1000 token，与后续任务无关。

**阶段 2：用户请求触发 activation**

用户输入 `Roll a d20` 后，Agent 把请求与 10 个 Skill 的 `description` 做匹配。`roll-dice` 的 description 中包含 "roll dice"、"d20" 等关键词，匹配命中。Agent 加载 `roll-dice/SKILL.md` 的完整 body，这部分约 500 token。

**阶段 3：执行指令，按需加载资源**

`roll-dice` 的指令是执行 `echo $((RANDOM % 20 + 1))`，不需要加载 `scripts/` 或 `references/`。如果换成 `pdf-processing`，Agent 会在执行到"调用 `pdfplumber.extract_text()`"时才加载 `scripts/extract_text.py`，这就是资源按需加载的触发点——指令中明确引用了某个文件，Agent 才会把该文件内容读入上下文。

**token 消耗对比**

| 加载方式 | 启动时 | 用户请求时 | 资源加载时 | 总计 |
|----------|--------|------------|------------|------|
| 传统工具调用（10 个工具） | 约 5000 token | 0 | 0 | 约 5000 token |
| Agent Skills（10 个 Skill，激活 1 个） | 约 1000 token | 约 500 token | 按需 | 约 1500 token 起 |

传统工具调用在启动时就把 10 个工具的完整描述塞进上下文；Agent Skills 只在用户请求匹配到具体 Skill 时才加载它的指令，未命中的 9 个 Skill 始终只占用元数据开销。当 Skill 数量增长到 50 个时，这个差距会进一步拉大：传统方式启动时就要消耗约 25000 token，而 Agent Skills 仍只消耗约 5000 token 的元数据开销。

```bash
# 1. 用户在 Copilot Chat 中输入
/Roll a d20

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

**安装命令**：

```bash
# 克隆 skills-ref 库
git clone https://github.com/agentskills/agentskills.git
cd agentskills/skills-ref

# 使用 uv 安装（推荐）
uv pip install skills-ref

# 或使用 pip
pip install skills-ref
```

### 4.2 创建第一个 Skill

**目标**：创建一个投骰子的 Skill

**步骤 1**：创建 Skill 目录

```bash
mkdir -p .agents/skills/roll-dice
```

**步骤 2**：编写 SKILL.md

```markdown
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
```

### 4.3 验证 Skill

```bash
# 使用 skills-ref 验证 Skill 格式
skills-ref validate .agents/skills/roll-dice
```

如果验证失败，常见原因包括：`name` 字段包含大写字母或下划线、`description` 超过 1024 字符、`SKILL.md` 缺少必需字段。根据错误提示修正后重新验证。

### 4.4 在 Agent 中使用

1. 打开 VS Code，进入 Copilot Chat
2. 选择 **Agent** 模式
3. 输入 `/skills` 确认 Skill 已注册
4. 输入 "Roll a d20"
5. Agent 自动激活 `roll-dice` Skill 并执行

---

## 五、skills-ref 参考库

### 5.1 简介

`skills-ref` 是 Agent Skills 官方提供的 Python 参考库，提供：

- **Skill 验证**：检查 SKILL.md 格式是否符合规范
- **属性读取**：提取 Skill 的 frontmatter 字段
- **Prompt 生成**：将 Skill 转换为适合 LLM 的 prompt（提示词）格式

GitHub：[https://github.com/agentskills/agentskills/tree/main/skills-ref](https://github.com/agentskills/agentskills/tree/main/skills-ref)

### 5.2 CLI 命令

```bash
# 验证 Skill 格式
skills-ref validate ./my-skill

# 读取 Skill 属性
skills-ref read-properties ./my-skill

# 生成 prompt
skills-ref to-prompt ./my-skill
```

### 5.3 API 设计模式说明

`skills-ref` 的 CLI 命令对应三类内部操作：验证、属性读取和 prompt 生成。如果需要在 Python 代码中调用这些能力，建议直接查阅 [skills-ref 官方文档](https://github.com/agentskills/agentskills/tree/main/skills-ref) 确认当前的 API 签名，因为包的导入路径和函数签名可能随版本变化。

从 CLI 命令推断，Python API 大致遵循以下设计模式：

| CLI 命令 | 对应的内部职责 | 输入 | 输出 |
|----------|----------------|------|------|
| `validate` | 检查 SKILL.md 格式 | Skill 目录路径 | 验证结果（是否通过 + 错误列表） |
| `read-properties` | 解析 frontmatter | Skill 目录路径 | 包含 name、description 等字段的对象 |
| `to-prompt` | 拼装 LLM 可用的 prompt | Skill 目录路径 | 格式化的 prompt 字符串 |

实际函数名、参数和返回类型以官方文档为准。在生产环境使用时，建议先用 `skills-ref validate` 等 CLI 命令做集成，等 API 稳定后再迁移到 Python 调用。

---

## 六、高级用法与实践建议

### 6.1 脚本集成

Skill 可以包含可执行脚本，扩展其能力。脚本要做到：

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

```markdown
---
name: git-analysis
description: 分析 Git 仓库的提交历史、贡献者统计和代码变更。
---

## 使用分析脚本

运行 scripts/analyze.py 进行深度分析：

Bash 命令：
echo "请在 Skill 激活后使用以下命令："
echo "python scripts/analyze.py --repo ./ --format json"
```

**输出格式**（JSON）：

```json
{
  "total_commits": 1234,
  "contributors": 42,
  "top_contributors": [...]
}
```

### 6.2 参考资料分离

对于大型 Skill，建议将详细参考文档分离到 `references/` 目录。这样做的原因是 `SKILL.md` body 在激活时会被全量读入上下文，把 API 全文写进 body 会直接吃掉几千 token；而 `references/` 只在指令显式引用时才加载，未引用的部分不占上下文。

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

description 是 Agent 决定是否激活 Skill 的唯一依据，写不好就会出现"该激活时不激活"或"不该激活时误激活"。经验上有三条。

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

description 应控制在 1024 字符以内，优先用主动语态：

```yaml
# 简洁主动
description: 验证 API 响应是否符合 OpenAPI 规范。当需要测试 API、
             验证 JSON 响应或检查 REST 端点时使用。

# 冗长被动
description: 这个 Skill 可以被用来进行 API 相关的验证工作，
             它将会检查输入的 JSON 数据是否...
```

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

**评估维度**：

| 维度 | 指标 | 评估方法 |
|------|------|----------|
| 激活准确率 | 相关请求中 Skill 被正确激活的比例 | 日志分析 |
| 完成率 | 激活后任务成功完成的比例 | 用户反馈 |
| 上下文效率 | 平均使用的 token 数量 | 埋点统计 |
| 错误率 | 执行过程中的错误频率 | 监控告警 |

**迭代流程**：

```text
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  编写   │───▶│  测试   │───▶│  评估   │───▶│  发布   │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
     │             │             │             │
     ▼             ▼             ▼             ▼
  初步实现    单元测试       A/B 测试      版本发布
            集成测试       用户反馈      监控迭代
```

---

## 七、开发扩展

### 7.1 创建兼容 Agent

如果正在开发一个 AI Agent 系统，可以通过以下步骤添加 Agent Skills 支持：

**步骤 1：实现 Discovery**

```python
import os
from pathlib import Path
from typing import List, Dict

def discover_skills(skills_dir: Path) -> List[Dict[str, str]]:
    """发现目录中的所有 Skills"""
    skills = []
    
    for skill_path in skills_dir.iterdir():
        if not skill_path.is_dir():
            continue
            
        skill_md = skill_path / "SKILL.md"
        if not skill_md.exists():
            continue
        
        # 读取 frontmatter
        frontmatter = parse_frontmatter(skill_md.read_text())
        
        skills.append({
            "name": frontmatter.get("name"),
            "description": frontmatter.get("description"),
            "path": str(skill_path)
        })
    
    return skills
```

**步骤 2：实现 Activation**

```python
def activate_skill(skill_path: Path) -> str:
    """加载完整 Skill 内容"""
    skill_md = skill_path / "SKILL.md"
    return skill_md.read_text()
```

**步骤 3：实现渐进式加载**

```python
def load_skill_resources(skill_path: Path, resource_path: str) -> str:
    """按需加载 Skill 资源"""
    full_path = skill_path / resource_path
    if full_path.exists():
        return full_path.read_text()
    return ""
```

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

### 7.3 Skill 市场集成

发布 Skill 到市场的标准流程：

1. **创建独立仓库**：`my-skill/` 格式
2. **添加 LICENSE**：明确许可证
3. **编写 README**：说明用途和使用方法
4. **提交到市场**：通过 GitHub PR 或社区提名

---

## 八、使用场景与适用边界

### 8.1 何时该把能力做成 Skill

满足以下任一条件时，把能力做成 Skill 比写进系统提示词更合适：

- **能力需要按需加载**：不是每次对话都会用到，避免常驻上下文。例如 PDF 处理、Git 工作流、合同审查。
- **能力有明确的触发关键词**：description 能写出具体的激活条件，而非泛泛的"辅助开发"。
- **能力需要附带脚本或参考资料**：Skill 的 `scripts/`、`references/`、`assets/` 结构适合承载多文件资源。
- **能力需要跨项目复用**：Skill 是独立文件夹，可以放进不同项目的 `.agents/skills/` 直接使用。
- **能力需要版本管理和团队共享**：Skill 是独立 Git 仓库或子模块，便于版本控制和分发。

### 8.2 何时直接写系统提示词更合适

满足以下任一条件时，写进系统提示词比做成 Skill 更合适：

- **能力是全局基础行为**：例如输出语言偏好、代码风格约束、回复格式要求，每次对话都要生效。
- **能力描述很短且不需要附带资源**：几行指令就能说清，没有脚本和参考资料。
- **能力每次对话都会用到**：做成 Skill 反而多一层 activation 开销。
- **能力是项目特定的临时指令**：只服务于当前项目，不需要复用。

### 8.3 团队引入 Skill 的推荐顺序

按以下顺序引入可以降低试错成本：

1. **先用现成的官方 Skill**：从 [anthropics/skills](https://github.com/anthropics/skills) 挑选团队高频场景对应的 Skill（如代码审查、文档生成），放进 `.agents/skills/` 直接使用，验证 Skill 机制是否适合团队工作流。
2. **再把团队高频操作封装成 Skill**：识别团队内部重复执行的流程（如发布前检查、数据库迁移、日志排查），把这些流程的检查清单和脚本封装成 Skill。这一步建议由熟悉 Skill 格式的成员主导，先做 2-3 个高质量 Skill 作为模板。
3. **最后把领域专家知识封装成 Skill**：把安全合规检查、合同条款分析、领域特定规范等需要专家知识的能力做成 Skill。这类 Skill 的指令编写需要领域专家参与，建议采用"专家提供内容 + 工程师整理格式"的协作模式。

### 8.4 典型场景示例

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

可以，但建议控制并发激活的 Skill 数量以优化上下文使用。通常：

- **简单任务**：1 个 Skill
- **复杂任务**：2-3 个相关 Skill
- **避免**：5 个以上 Skill 同时激活（上下文膨胀）

### Q3：Skill 的 token 开销是多少？

估算如下：

| 阶段 | 平均 token | 触发时机 |
|------|-----------|----------|
| 元数据 | 约 100 | 每次启动 |
| 指令 | 500-2000 | 每次激活 |
| 资源 | 按需 | 执行中 |

### Q4：如何处理 Skill 之间的冲突？

如果两个 Skill 的 description 都能匹配同一个请求，可以通过以下方式处理：

1. **细化 description**：在 description 中明确各自的使用范围，减少重叠
2. **互斥标识**：在 metadata 中添加 `conflicts-with` 字段
3. **Agent 决策**：让 Agent 根据上下文选择更合适的 Skill

### Q5：可以使用哪些脚本语言？

取决于 Agent 实现。常见支持：

- **Bash/PowerShell**：系统命令
- **Python**：通用脚本
- **JavaScript/Node**：Web 相关任务
- **Go**：高性能工具

### Q6：Skill 可以访问网络吗？

取决于具体实现和 `compatibility` 设置。

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

## 十、采用建议与总结

### 采用顺序

如果团队准备引入 Skill，建议按下面的顺序推进，每一步验证通过后再进入下一步：

1. **先跑通官方 Skill**：从 [anthropics/skills](https://github.com/anthropics/skills) 挑 1-2 个高频场景的 Skill 放进 `.agents/skills/`，确认团队选用的 Agent（Claude Code、Copilot Chat、Codex 等）能正确 discovery 和 activation。这一步只验证机制可用，不写新 Skill。
2. **再封装团队高频操作**：识别团队内部重复执行的流程（发布前检查、数据库迁移、日志排查），先做 2-3 个高质量 Skill 作为模板，再让其他成员按模板补齐。
3. **最后封装领域专家知识**：安全合规、合同条款、领域规范这类需要专家参与的能力放到最后，采用"专家提供内容 + 工程师整理格式"的协作模式。

### 适用边界

Skill 适合承载按需加载、有明确触发词、需要附带脚本或参考资料、需要跨项目复用的能力。下面这些情况写进系统提示词更合适：每次对话都要生效的全局基础行为（语言偏好、代码风格、回复格式）；几行就能说清且不需要附带资源的指令；只服务于当前项目的临时指令。

### 关键事实

- Agent Skills 把工具加载从"启动时全量塞进上下文"改成"按需激活"，工具数量增长后上下文不会被无关描述挤占
- 渐进式披露分三阶段：启动时只读元数据，请求匹配时才加载指令，执行过程中按需读取 `scripts/`、`references/`、`assets/`
- 同一个 Skill 文件夹可以在 Claude Code、Copilot Chat、Codex 等兼容实现里直接用，不需要为每个平台重写
- 新增能力只需在 `.agents/skills/` 下加文件夹，不用改 Agent 本身的代码

### 生态现状

- **官方库**：agentskills/agentskills（16.3k Stars，数据采集于 2026-03-28，后续可能变化）
- **示例库**：anthropics/skills（108.9k Stars，数据采集于 2026-03-28）
- **社区**：Discord 服务器 + GitHub Discussions
- **文档**：agentskills.io（Mintlify 托管）

### 参与贡献

```bash
# 克隆官方仓库
git clone https://github.com/agentskills/agentskills.git

# 创建新 Skill
cd skills-ref/skills/
mkdir my-new-skill
cd my-new-skill
touch SKILL.md

# 提交 PR
git checkout -b feature/my-new-skill
git add .
git commit -m "feat: add my-new-skill"
git push origin feature/my-new-skill
```

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

*文档版本：2026-04-02 | 规范版本：v1.0 | 来源：[agentskills/agentskills](https://github.com/agentskills/agentskills)*
