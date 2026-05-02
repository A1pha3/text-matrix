---
title: "Superpowers：让 AI 编程助手真正学会软件工程"
date: 2026-05-02T15:04:24+08:00
slug: "superpowers-vscode-ai-pair-programming-guide"
description: "Superpowers 是一个专为 AI 编程 agent 设计的软件工程方法论与技能框架，支持 Claude Code、Cursor、Copilot 等主流 IDE，通过强制触发式技能系统让 AI agent 自动遵循 TDD、YAGNI、DRY 等工程原则，摆脱\"直觉编码\"，实现数小时级别的自主工作中不离线。"
draft: false
categories: ["技术笔记"]
tags: ["AI编程", "Claude", "Cursor", "TDD", "编程方法论", "软件工程", "Git Worktree"]
---

## 前言：AI 编程助手的工程化困境

过去两年里，AI 编程助手从简单的补全工具演变成了能独立完成模块开发的「搭档」。以 Claude Code、Cursor、GitHub Copilot 为代表的工具已经能在足够简单的场景下替代初级工程师完成实际工作。然而，当项目复杂度上升、边界条件增多时，AI 的表现往往开始偏离预期：

- **直觉先行**：看到需求就动手写代码，不做设计就写实现
- **测试缺失**：功能写完就交付，没有先写测试的习惯
- **范围蔓延**：YAGNI 原则频频被打破，一不小心就多做了很多「可能用得上」的功能
- **一次做太多**：大段代码一次性输出，中途没有阶段性的验证和检查

这些问题并非 AI 能力不足，而是缺少一种**工程化的约束框架**来引导 AI 的行为。Superpowers 正是为此而生。

---

## 一、Superpowers 是什么

[Superpowers](https://github.com/obra/superpowers) 是由 [Jesse Vincent](https://blog.fsck.com)（Perl 社区资深开发者，BackgroundPerl/PDU 主要作者）构建的开源项目，定位为 **「AI 编程 agent 的软件工程方法论」**。其核心是一组可组合的技能（Skills），以及一套在特定时机自动触发这些技能的初始指令系统。

项目核心数据：

| 指标 | 数值 |
| --- | --- |
| GitHub Star | ~175,900（截至 2026-05） |
| Fork 数 | ~15,552 |
| 编程语言 | Shell（用于安装脚本和测试框架） |
| 许可证 | MIT |
| 主要维护者 | Jesse Vincent @obra |
| 官方支持 | Claude Code、Cursor、Copilot、OpenAI Codex、OpenCode、Gemini CLI |

Superpowers 不是代码模板库，也不是提示词集合。它是一种**过程规范**——通过在 AI 的工作流中嵌入强制检查点，让 AI 在写代码之前先做设计，做设计之前先理解需求，最终产出符合工程标准的成果。

---

## 二、核心原理：强制触发式技能系统

### 2.1 技能（Skill）是什么

Superpowers 中的 Skill 不是普通提示词，而是一个结构化的技能定义文件（SKILL.md），包含以下组成部分：

```
skills/
├── brainstorming/          # 设计阶段：通过苏格拉底式提问澄清需求
├── writing-plans/         # 规划阶段：将设计拆解为可执行的小任务
├── test-driven-development/# 实现阶段：强制 RED-GREEN-REFACTOR 循环
├── systematic-debugging/  # 调试阶段：四步根源分析
├── requesting-code-review/# 评审阶段：提交代码审查
├── finishing-a-development-branch/  # 收尾阶段：合并或保留分支决策
└── ...（共 14 个核心技能）
```

每个技能目录下至少有 `SKILL.md`，有些还包含引用文档（如 `test-driven-development` 包含 testing anti-patterns 参考）。

### 2.2 自动触发机制

Superpowers 与市面上大多数提示词集合的本质区别在于**强制触发**。传统方式需要用户在每次会话中手动复制粘贴提示词，Superpowers 则利用各 AI 编程工具的插件系统，在合适的时机自动激活对应技能。

以 Claude Code 为例，当 Superpowers 插件安装后，AI 在每次**开始写代码之前**会自动激活 `brainstorming` 技能——它不会立刻动手，而是停下来问你：「你真正想解决的问题是什么？」只有当设计文档被确认后，才会进入 `writing-plans` 阶段。

这种机制解决了 AI 编程工具最核心的问题：**让 AI 在正确的时机做正确的事，而不是被上一次对话的惯性带着走**。

### 2.3 核心工程原则

Superpowers 的技能体系背后有三条明确的设计原则：

1. **TDD（Test-Driven Development）优先**：任何功能都必须先写测试，再写实现，再重构。`test-driven-development` 技能强制执行 RED→GREEN→REFACTOR 循环，写在测试之前的代码会被直接丢弃。

2. **YAGNI（You Aren't Gonna Need It）**：只做当前 spec 明确要求的功能，不提前实现「可能用得上」的东西。`writing-plans` 技能在生成任务清单时会明确审查每个任务是否属于 YAGNI 违规。

3. **DRY（Don't Repeat Yourself）**：通过 subagent 协作和代码审查机制来消除重复逻辑和设计。

---

## 三、架构分析

### 3.1 整体架构

Superpowers 的技术架构分为四层：

```
┌─────────────────────────────────────────┐
│           各 IDE / CLI 的插件层          │
│  (.claude-plugin / .codex-plugin /     │
│   .cursor-plugin / .opencode /         │
│   gemini-extension.json)                │
├─────────────────────────────────────────┤
│           引导指令层 (AGENTS.md)         │
│  初始指令让 AI 在会话开始时加载 bootstrap │
├─────────────────────────────────────────┤
│           技能执行层 (skills/)           │
│  14 个可组合技能，各自在特定时机触发      │
├─────────────────────────────────────────┤
│           测试与验证层 (tests/)          │
│  集成测试确保技能行为符合预期             │
└─────────────────────────────────────────┘
```

**插件层**负责与不同 IDE / CLI 的集成，每个受支持的平台都有对应的插件定义，声明技能的加载方式和触发条件。

**引导指令层**是 `AGENTS.md`（或各平台对应的入口文件如 `CLAUDE.md`、`GEMINI.md`），其中包含 bootstrap 指令，确保 AI 在会话开始时加载技能系统。

**技能执行层**是核心，`skills/` 目录下的每个子目录对应一个独立技能。技能之间可以相互引用（例如 `subagent-driven-development` 会调用 `test-driven-development`），形成可组合的工作流。

**测试层**采用真实的 AI 会话集成测试，在 headless 模式下运行完整的 Claude Code 会话，解析 `.jsonl` 格式的会话记录来验证行为是否符合预期。

### 3.2 subagent-driven-development 的双层评审机制

在所有技能中，`subagent-driven-development` 是最核心的执行引擎。其设计引入了**两阶段评审**（Two-Stage Review）机制：

- **第一阶段：Spec Compliance Review**——subagent 完成后，首先由独立的「评审员」验证实现是否符合设计 spec，而不是代码质量。这一步通过 `verification-before-completion` 技能来确保「修复了就要真的修好了」。
- **第二阶段：Code Quality Review**——通过后才进入代码质量审查，包括是否存在 YAGNI 违规、测试覆盖是否足够、是否存在重复逻辑等。

这种两阶段机制解决了 AI 编程中最常见的问题：agent 报告「已完成」但实际并不符合 spec。

### 3.3 使用 Git Worktree 的并行工作模型

`using-git-worktrees` 是 Superpowers 中独特的基础设施型技能。它让 AI 在开始实现前创建一个独立的 Git worktree，在新分支上工作，而不影响主分支的状态。这解决了两个问题：

1. **并行多任务**：在 subagent 驱动的开发模式下，多个 subagent 可以在不同 worktree 上并行工作，彼此隔离
2. **干净的工作环境**：每个任务开始前都验证「干净的测试基线」——即测试在当前代码状态下确实能通过，确保新代码不会因为历史遗留问题而误报成功

---

## 四、安装配置

### 4.1 支持的平台

Superpowers 目前支持的平台和安装方式如下：

#### Claude Code（官方市场）

```bash
# 方式一：从 Anthropic 官方插件市场安装
/plugin install superpowers@claude-plugins-official
```

```bash
# 方式二：从 Superpowers 自己的市场安装（包含其他相关插件）
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

#### Cursor

在 Cursor Agent 聊天中执行：

```text
/add-plugin superpowers
```

或通过插件市场搜索 "superpowers" 安装。

#### GitHub Copilot CLI

```bash
copilot plugin marketplace add obra/superpowers-marketplace
copilot plugin install superpowers@superpowers-marketplace
```

#### OpenAI Codex CLI

```bash
# 打开插件搜索界面
/plugins

# 搜索并安装
superpowers
# 选择 Install Plugin
```

#### OpenCode

```bash
Fetch and follow instructions from https://raw.githubusercontent.com/obra/superpowers/refs/heads/main/.opencode/INSTALL.md
```

#### Gemini CLI

```bash
gemini extensions install https://github.com/obra/superpowers

# 更新
gemini extensions update superpowers
```

### 4.2 验证安装

安装完成后，在支持 AI 编程的 IDE / CLI 中新建一个空白会话，输入：

```
Let's make a react todo list
```

如果 Superpowers 正常工作，AI 会自动触发 `brainstorming` 技能，在你开始写任何代码之前停下来，通过提问来澄清你真正想做的事。这是验证插件是否正确加载 bootstrap 的**验收测试**。

---

## 五、工作流实战

下面通过一个具体场景来演示 Superpowers 的完整工作流。假设我们想让 AI 帮助实现一个简单的待办事项 API。

### 第一步：brainstorming——在写代码之前先澄清需求

**触发时机**：当 AI 检测到你正在尝试构建某个功能时自动触发。

**AI 的行为**：不会立即开始写代码，而是通过苏格拉底式提问来澄清需求。例如：

> AI：「你提到的 todo list，具体是面向 C 端用户还是内部工具？需要支持多人协作还是单人使用？持久化方案有偏好吗？」

在这个阶段，AI 会将讨论出的设计以分段形式展示给你确认，确保每个模块的设计都经过你知情同意后才进入下一阶段。设计文档最终会保存下来，作为后续实现的对标。

### 第二步：writing-plans——将设计拆解为可执行任务

**触发时机**：设计文档被确认后。

**AI 的行为**：将整个实现计划分解为 2-5 分钟粒度的小任务，每个任务包含：

- 精确的文件路径
- 完整的代码（不是伪代码）
- 验证步骤（如何验证任务确实完成）

任务描述必须足够清晰，即使是一个「缺乏品味、没有项目上下文、不愿测试的热情初级工程师」也能照着执行。计划会展示给你，你说「go」之后才会真正开始。

### 第三步：subagent-driven-development——子 agent 并行执行

**触发时机**：你说「go」之后。

**工作方式**：AI 启动 subagent 驱动的开发流程，每个 engineering task 分配给一个 fresh 的 subagent。subagent 完成工作后经历两阶段评审：

```
[subagent 完成任务]
    ↓
第一阶段评审：是否符合 spec？
    ↓ 通过
第二阶段评审：代码质量如何？
    ↓ 通过
进入下一个任务
```

根据项目复杂度，一个完整的实现计划可能包含数十个任务，每个任务独立验证通过后才推进到下一个。在实践中，Claude 能够在这种机制下自主工作数小时而不偏离计划。

### 第四步：test-driven-development——红绿重构循环

**触发时机**：每个任务的实现阶段。

**强制规则**：

1. **RED**：先写一个会失败的测试，运行它，确认失败原因与预期一致
2. **GREEN**：写最少的代码让测试通过，运行确认
3. **REFACTOR**：在测试保护下重构代码，然后提交

如果在测试写好之前就写了实现代码，这些代码会被直接丢弃。`test-driven-development` 技能内置了测试反模式（testing anti-patterns）的参考文档，帮助 AI 识别常见的测试设计错误。

### 第五步：systematic-debugging——四步根源分析

**触发时机**：当出现 bug 需要修复时。

**工作流程**：

1. **定义问题**：精确描述观察到的现象
2. **收集数据**：通过条件等待、防御纵深等方式收集信息
3. **根源分析**：追踪到真正的根源而不是表面症状
4. **验证修复**：确认修复后问题确实解决

### 第六步：finishing-a-development-branch——分支收尾决策

**触发时机**：所有任务完成后。

**AI 的行为**：

1. 运行完整测试套件，验证通过
2. 展示三个选项：**合并/PR/保留分支**，并说明每个选项的利弊
3. 根据你的选择执行相应操作
4. 清理 worktree（如适用）

---

## 六、扩展与自定义

### 6.1 编写自己的技能

Superpowers 提供了 `writing-skills` 技能，详细说明了如何创建新的技能并确保其行为符合预期。新技能的创建流程：

1. fork 仓库，进入 `dev` 分支
2. 创建新分支
3. 参考 `skills/writing-skills/SKILL.md` 的完整指南进行开发和测试
4. 提交 PR

但需要注意，Superpowers 官方明确表示**一般不接受新技能的 PR**。新技能的门槛很高，需要在多种场景下经过压力测试，证明修改确实改进了结果才会被接受。如果你的技能是针对特定领域、工具或工作流的，建议作为独立插件发布。

### 6.2 集成新的 IDE / CLI

如果要将 Superpowers 集成到新的编程工具中，需要通过一个会话转录来证明集成是真实有效的：

1. 在新工具中打开一个干净的会话
2. 发送：`Let's make a react todo list`
3. 验证 `brainstorming` 技能被自动触发
4. 将完整转录附在 PR 中

官方明确指出，以下方式不算真实集成（会被直接关闭）：

- 手动复制技能文件到工具目录
- 使用 `npx skills` 或类似的运行时包装器
- 要求用户每个会话手动 opt-in

### 6.3 更新 Superpowers

Superpowers 的更新机制因平台而异，但通常是**自动的**。各平台的插件系统会在会话开始时检查更新，无需手动干预。

---

## 七、适用场景与局限性

### 7.1 适合的场景

- **中等复杂度项目**：需要明确的设计、测试覆盖和分阶段验证的项目
- **团队 AI 协作**：需要多个 AI agent 在统一工程规范下并行工作
- **TDD 实践**：团队希望在 AI 辅助下也能保持测试先行的工程纪律
- **需要 AI 长时间自主工作**：通过双层评审和检查点机制，Claude 能够自主工作数小时不偏离计划

### 7.2 局限与注意事项

- **插件系统依赖**：Superpowers 依赖 IDE/CLI 的插件系统，部分工具（如纯 API 调用方式）无法使用
- **学习曲线**：对于习惯了「直接写代码」的开发者，强制设计流程可能显得繁琐
- **PR 接受门槛极高**：项目有 94% 的 PR 拒绝率，贡献新技能几乎不可能被接受
- **测试耗时**：集成测试需要 10-30 分钟完成真实的 AI 会话执行

---

## 八、总结

Superpowers 解决的不是 AI 编程能力的问题，而是**工程纪律**的问题。在 AI 能写出越来越复杂代码的时代，如何确保它遵循人类积累了几十年的软件工程原则？答案是不要依赖 AI 的「常识」，而是在工作流层面内置强制约束。

它最核心的价值可以归结为一句话：**让 AI 在正确的时机做正确的事，而不是被上一次对话的惯性带着走。**

如果你使用 Claude Code、Cursor 或其他主流 AI 编程工具，强烈建议尝试安装 Superpowers，体验一下「AI 在动手之前先问我真正想要什么」的感觉——那才是真正有用的 AI 搭档。

---

## 参考链接

- GitHub 仓库：https://github.com/obra/superpowers
- 官方博客公告：https://blog.fsck.com/2025/10/09/superpowers/
- Discord 社区：https://discord.gg/35wsABTejz
- 插件市场：https://claude.com/plugins/superpowers
