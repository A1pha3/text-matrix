---
title: "Spec Kit：GitHub 官方推出的规范驱动开发工具包，让规格文档直接生成代码"
date: "2026-05-14T16:08:00+08:00"
slug: "spec-kit-spec-driven-development-toolkit"
description: "Spec Kit 是 GitHub 官方开源的规范驱动开发工具包，通过将规格文档变成可执行资产，直接生成工作实现而非仅作为编码指导。它包含 Specify CLI 工具和一套完整的开发工作流，支持 Copilot 等多种 AI 编码 Agent 集成。"
draft: false
categories: ["技术笔记"]
tags: ["Spec-Driven Development", "GitHub", "Specify CLI", "AI Coding Agent", "Python"]
---

# Spec Kit：GitHub 官方推出的规范驱动开发工具包，让规格文档直接生成代码#

## 学习目标

读完本文后，你应该能够：

1. 理解 Spec Kit 的核心思路——把规格文档提到 AI 编码流程的第一位，让代码和原始意图之间的关联不再断裂
2. 区分 Spec Kit 工作流中的两个关键角色（Specify CLI 和 AI 编码 Agent）及其产物
3. 独立完成 Spec Kit 的安装、项目初始化和与 Copilot 等 AI Agent 的集成
4. 编写合格的规格文件（`.spec/features/*.md`），包含端点定义、请求参数、返回格式和验收条件
5. 判断 Spec Kit 是否适合你的团队场景，以及按什么顺序引入风险最低#

## 目录#

- [学习目标](#学习目标)
- [Spec Kit 解决什么](#spec-kit-解决什么)
- [系统地图：两个关键角色](#系统地图两个关键角色)
- [一个最小流转案例](#一个最小流转案例)
- [Specify CLI：安装与初始化](#specify-cli安装与初始化)
- [社区生态](#社区生态)
- [技术细节](#技术细节)
- [开发节奏](#开发节奏)
- [适合谁、什么时候用](#适合谁什么时候用)
- [自测题](#自测题)
- [进阶路径](#进阶路径)
- [常见问题](#常见问题)#

## Spec Kit 解决什么

大多数 AI 编码工具的工作方式是：你给一句 prompt，它生成一段代码。这种方式的问题在于，prompt 的生命周期很短——写完就丢了，代码和原始意图之间的关联也随之断裂。

Spec Kit 把规格文档提到 AI 编码流程的第一位：不是让 AI 从模糊 prompt 猜你的意图，而是从一份结构化的规格文档出发，生成符合规格的代码。规格文档不再是用完就扔的产物，而是后续所有改动的起点。

项目由 GitHub 官方维护，当前 98,770 Stars，8,600 Forks。

## 系统地图：两个关键角色

Spec Kit 的工作流里有两个角色在配合，各自管不同的事：

| 角色 | 做什么 | 产物 |
|------|--------|------|
| **Specify CLI** | 管理项目模板、初始化规格文件、校验工具链 | 目录结构、规格模板、配置 |
| **AI 编码 Agent**（Copilot / Claude Code 等） | 根据规格文件生成、修改、验证代码 | 源代码、测试、实现 |

Specify CLI 不直接生成代码——它生成的是给 AI Agent 吃的结构化输入。AI Agent 不管理项目结构——它只负责把规格翻译成实现。

## 一个最小流转案例

假设要给一个 Python 项目加一个 `/export` API 端点，返回 JSON 和 CSV 两种格式。

**不用 Spec Kit**：打开 Copilot Chat → 输入 "add an /export endpoint that returns JSON and CSV" → Copilot 生成一段代码 → 手动检查输出字段对不对、边界情况有没有处理 → 来回改 prompt。

**用 Spec Kit 的流程**：

```text
1. specify init . --integration copilot
   → 项目里生成 .spec/ 目录和规格模板

2. 填写 .spec/features/export-endpoint.md：
   → 定义端点路径、请求参数、返回格式（JSON/CSV）
   → 写入验收条件：空数据集返回什么、CSV BOM 怎么处理

3. 让 Copilot 读取 .spec/features/export-endpoint.md 生成代码
   → Copilot 不仅生成 endpoint，还会根据验收条件生成对应的测试

4. 需求变更时，先改规格文件，再让 Agent 重新生成
   → 代码和规格始终保持一致
```

整个流程里，规格文件是唯一的事实来源。AI Agent 每次生成的代码都以这份文件为准，不再依赖对话历史里散落的 prompt。

## Specify CLI：安装与初始化

Spec Kit 的核心工具是 Specify CLI，通过 uv（或 pipx）安装：

```bash
# 安装稳定版（推荐，先查看 Releases 获取最新 tag）
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z

# 或安装最新版（可能包含未发布变化）
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git

# 验证安装
specify version

# 初始化新项目
specify init <PROJECT_NAME>

# 在现有项目中初始化
specify init . --integration copilot
```

常用命令：

```bash
# 检查已安装工具
specify check

# 创建新项目
specify init my-project

# 指定 AI 集成
specify init --here --integration copilot
```

通过 `--integration` 参数在初始化时选择目标 AI Agent，目前支持 Copilot（含 Claude）、GitHub Copilot 等。

## 社区生态

社区贡献覆盖了四个方向：

- **扩展（Extensions）**：扩展 Specify CLI 能力的插件
- **预设（Presets）**：预置的规格模板，覆盖特定场景
- **演练（Walkthroughs）**：逐步指南，帮助上手
- **工具集成（Friends）**：与 Specify 配合使用的第三方工具

这四个方向各自解决的问题不同：扩展改变 CLI 行为，预设决定规格模板长什么样，演练降低上手成本，集成把其他工具接入工作流。实际用的时候可以按需选择，不必一开始全装上。

## 技术细节

- **语言**：Python
- **安装方式**：仅通过 GitHub 发布，不在 PyPI 上发布官方包（PyPI 上同名包与本项目无关）
- **包管理器**：推荐使用 [uv](https://docs.astral.sh/uv/)
- **文档**：托管在 GitHub Pages [github.github.io/spec-kit](https://github.github.io/spec-kit/)

## 开发节奏

README 中列出了多个开发阶段，从基础 CLI 工具到完整工作流逐步推进。官方同时列出了实验性目标（Experimental Goals），目前已知的方向包括：支持更多 AI Agent 后端、增强规格模板的可组合性、提供 CI/CD 集成方案。

项目的迭代节奏较快，关注 Release Notes 比关注 Roadmap 更能判断当前可用程度。

## 适合谁、什么时候用

**适合先上的团队**：
- 产品规格文档已经存在，但和代码实现脱节
- AI 编码 Agent 已经用起来了，但生成结果的质量波动大
- 多人协作时，不同人写 prompt 风格差异导致代码风格不一致

**可以先等等的场景**：
- 团队还在探索阶段，尚未形成稳定的规格编写习惯
- 项目规模小、单人开发、需求变化极快——此时规格维护成本可能超过收益
- 已经有一套成熟的代码审查和测试流程，且运转良好

**从哪开始**：挑一个需求明确、边界清晰的小功能，走一遍"写规格 → Agent 生成 → 验证"的完整流程。评估规格是否真的减少了返工，再决定是否推广到更大范围。

## 自测题

1. **Spec Kit 解决的核心问题是什么？对比「直接写 prompt」，它的长期优势在哪里？**
   答：规格文档是持久化的——需求变更时先改规格，再让 Agent 重新生成。Prompt 是一次性的，代码和原始意图之间的关联随对话结束而断裂。

2. **Specify CLI 和 AI Agent 的分工是什么？**#
   答：Specify CLI 管理项目模板、初始化规格文件、校验工具链；AI Agent 根据规格文件生成、修改、验证代码。CLI 不生成代码，Agent 不管理项目结构。#

3. **验收条件为什么重要？写不好的验收条件会导致什么问题？**#

   答：验收条件是 Agent 生成代码的判断依据。模糊的验收条件（例如"正确处理错误"）会导致 Agent 理解偏差，生成的代码不符合预期，需要反复返工。#

4. **`--integration` 参数的作用是什么？目前支持哪些 AI Agent？**#

   答：选择目标 AI Agent，让 Spec Kit 生成对应的配置。目前支持 Copilot（含 Claude）、GitHub Copilot 等。#


5. **如果团队还没形成稳定的规格编写习惯，直接上 Spec Kit 会遇到什么问题？**#

   答：规格文件本身需要投入时间编写和维护。如果需求变化极快、项目规模小、单人开发，规格维护成本可能超过收益。#


## 进阶路径#

### 阶段一：基础使用（1-2 天）#

- 安装 Specify CLI（推荐用 `uv tool install`）#
- 用 `specify init . --integration copilot` 在现有项目中初始化#
- 写一个最小的规格文件（一个端点的路径、参数、返回格式、验收条件）#
- 让 Copilot 读取规格文件生成代码，对比「有规格」和「没规格」的输出差异#

### 阶段二：规格编写习惯（3-5 天）#

- 把团队现有的一个需求写成规格文件，走一遍"写规格 → Agent 生成 → 验证"流程#
- 学习官方文档的规格模板示例，理解验收条件怎么写才能被 Agent 正确理解#
- 评估：规格是否真的减少了返工？哪些地方 Agent 仍然会理解偏差？#

### 阶段三：团队推广（1-2 周）#

- 挑一个边界清晰的小功能，在团队内走完整流程#
- 评估不同人写的规格质量差异，是否需要统一的规格编写规范#
- 如果有常用模式（例如 CRUD 端点的标准验收条件），写成预设（Presets）共享#

### 阶段四：社区贡献（可选）#

- 编写一个扩展（Extension），为团队常用的框架生成规格模板#
- 写一个演练（Walkthrough），帮助新人上手 Spec Kit#
- 给官方仓库提 PR——GitHub 维护，社区友好#

---#

**延伸阅读**：[官方文档](https://github.github.io/spec-kit/) · [GitHub 仓库](https://github.com/github/spec-kit) · [Specify CLI 安装指南](./docs/install/uv.md)