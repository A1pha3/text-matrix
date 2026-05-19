---
title: "Spec Kit：GitHub 官方的 Spec-Driven Development 全栈指南"
date: 2026-05-14T11:40:00+08:00
slug: "github-spec-kit-spec-driven-development"
description: "Spec Kit 是 GitHub 官方开源的 Spec-Driven Development（规格驱动开发）工具包，通过将规格文档变为可执行产出物，配合 AI 编码智能体实现从需求到实现的结构化工作流。本文解析其核心概念、CLI 安装、五步开发流程及扩展开发生态。"
draft: false
categories: ["技术笔记"]
tags: ["GitHub", "Spec-Driven Development", "AI Agent", "SDD", "Python"]
---

## 项目概览

[github/spec-kit](https://github.com/github/spec-kit) 是 GitHub 官方开源的一款**规格驱动开发（Spec-Driven Development，SDD）**工具包，当前已获得约 **98,500 颗 Stars** 和 **8,581 个 Fork**，采用 MIT 许可证，主要语言为 Python。

核心定位一句话概括：**让规格文档成为可执行产出物，直接生成可工作的实现代码，而不是停留在"仅供参考"的阶段。**

| 指标 | 数值 |
|------|------|
| Stars | ~98,500 |
| Forks | ~8,581 |
| 语言 | Python |
| 许可证 | MIT |
| 官方文档 | [github.github.io/spec-kit](https://github.github.io/spec-kit/) |

## 核心思路：从"写规格"到"运行规格"

传统软件开发中，规格文档（Spec）往往是一个"先写后扔"的过渡产物——编码开始后，规格文档就被束之高阁。Spec Kit 试图翻转这个范式：规格不是起点，而是**贯穿整个开发流程的核心载体**。

SDD 的三条基本原则：

1. **意图驱动（Intent-driven）**：先定义"做什么（What）"和"为什么做（Why）"，技术选型（How）放在后面。
2. **多步细化（Multi-step refinement）**：不追求一步到位由 AI 生成完整代码，而是通过结构化的多阶段逐步逼近。
3. **规格即产出物（Specs as deliverables）**：规格文档本身是开发过程的正式输出，可追踪、可验证。

## Specify CLI 安装

### 方式一：持久安装（推荐）

需要先安装 [uv](https://docs.astral.sh/uv/)（快速 Python 包管理器）：

```bash
# 安装稳定版本（推荐）
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z

# 或安装 main 分支最新版本
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git

# 验证版本
specify version
```

> ⚠️ 官方明确声明：唯一官方维护的包发布渠道只有当前 GitHub 仓库，PyPI 上同名包与本项目无关。

### 方式二：一次性运行

不想全局安装，可用 `uvx` 直接运行：

```bash
uvx --from git+https://github.com/github/spec-kit.git@vX.Y.Z specify init <PROJECT_NAME>
```

### 方式三：离线/企业环境

若网络受限，官方提供了利用 `pip download` 在联网机器上打包 wheel 再迁移到隔离环境的详细指南。

## 核心工作流：五步从需求到实现

Spec Kit 为 AI 编码智能体（如 Claude Code、GitHub Copilot、Cursor 等）提供了一套结构化的 slash 命令体系。完整流程如下：

### Step 1：建立项目宪法 `/speckit.constitution`

```bash
/speckit.constitution Create principles focused on code quality, testing standards, user experience consistency, and performance requirements
```

生成 `.specify/memory/constitution.md`，定义项目治理原则，后续所有阶段都参照这份文档做决策。

### Step 2：描述需求 `/speckit.specify`

```bash
/speckit.specify Build an application that can help me organize my photos in separate photo albums. Albums are grouped by date and can be re-organized by dragging and dropping on the main page.
```

这一步**不涉及技术选型**，只描述"做什么"和"为什么做"。LLM 根据提示词生成用户故事和功能规格文档，写入 `specs/<feature>/spec.md`。

### Step 3：技术规划 `/speckit.plan`

```bash
/speckit.plan The application uses Vite with minimal number of libraries. Use vanilla HTML, CSS, and JavaScript as much as possible.
```

在规格已明确的基础上，指定技术栈、架构设计，输出 `plan.md`、`research.md`、`data-model.md` 等实现细节文档。

### Step 4：拆解任务 `/speckit.tasks`

```bash
/speckit.tasks
```

根据 `plan.md` 自动生成 `tasks.md`，包含：按依赖排序的任务列表、并行任务标记 `[P]`、TDD 测试优先顺序，以及每个任务的执行路径。

### Step 5：执行实现 `/speckit.implement`

```bash
/speckit.implement
```

执行所有任务，严格按照 `tasks.md` 的顺序和检查点推进。

## 扩展开发生态

### 扩展（Extensions）

扩展为 Spec Kit 添加全新命令和能力，例如 Jira 集成、代码审查、V-Model 测试追溯等。安装方式：

```bash
specify extension search
specify extension add <extension-name>
```

社区已贡献了 **80+ 个扩展**，涵盖：

| 类别 | 说明 |
|------|------|
| `docs` | 规格文档的读取、验证、生成 |
| `code` | 代码审查、验证、修改 |
| `process` | 跨阶段工作流编排 |
| `integration` | 外部平台同步（Jira、Azure DevOps、Linear 等） |
| `visibility` | 项目健康度报告 |

### 预设（Presets）

预设不添加新能力，而是**改变现有工作流的行为方式**——覆盖模板、命令格式和术语。例如：强制合规性审查标准、采用领域特定术语、或将整个工作流本地化为其他语言。

```bash
specify preset search
specify preset add <preset-name>
```

扩展和预设的解析优先级：项目本地覆盖 > 预设 > 扩展 > 核心默认。

## 适用场景与边界

### 适合

- **Greenfield 项目**：从零开始，需要 AI 辅助做结构化探索
- **需求模糊但有方向**：通过多步澄清（`/speckit.clarify`）逐步收敛规格
- **团队需要统一开发规范**：通过 Constitution + Preset 固化团队开发原则
- **需要可追溯的规格文档**：SDD 天然支持从 spec → plan → tasks → implementation 的全链路追溯

### 不适合

- 快速原型验证（SDD 的结构化开销在探索阶段偏重）
- 已有大型遗留代码库的全量迁移（建议用 Brownfield 扩展渐进式引入）
- 纯手动开发流程（Spec Kit 强依赖 AI 编码智能体）

## 总结

Spec Kit 是 GitHub 在 AI 原生开发工作流上的重要实践。它没有试图让 AI 凭空生成代码，而是提供了一套**以规格为中心、人机协作的结构化方法论**。对于希望用 AI 智能体做系统性开发而非"vibe coding"的团队，这是一个值得关注的项目。

**延伸阅读：**

- 官方文档：https://github.github.io/spec-kit/
- 完整 SDD 方法论：https://github.com/github/spec-kit/blob/main/spec-driven.md
- 社区扩展目录：https://speckit-community.github.io/extensions/
