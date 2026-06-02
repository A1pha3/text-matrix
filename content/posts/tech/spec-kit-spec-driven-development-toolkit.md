---
title: "Spec Kit：GitHub 官方推出的规范驱动开发工具包，让规格文档直接生成代码"
date: "2026-05-14T16:08:00+08:00"
slug: "spec-kit-spec-driven-development-toolkit"
description: "Spec Kit 是 GitHub 官方开源的规范驱动开发工具包，通过将规格文档变成可执行资产，直接生成工作实现而非仅作为编码指导。它包含 Specify CLI 工具和一套完整的开发工作流，支持 Copilot 等多种 AI 编码 Agent 集成。"
draft: false
categories: ["技术笔记"]
tags: ["Spec-Driven Development", "GitHub", "Specify CLI", "AI Coding Agent", "Python"]
---

# Spec Kit：GitHub 官方推出的规范驱动开发工具包，让规格文档直接生成代码

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

---

**延伸阅读**：[官方文档](https://github.github.io/spec-kit/) · [GitHub 仓库](https://github.com/github/spec-kit) · [Specify CLI 安装指南](./docs/install/uv.md)