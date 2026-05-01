---
title: "Awesome Codex Skills：Codex编码智能体技能库，支持1000+应用集成"
date: 2026-04-29T15:00:00+08:00
lastmod: 2026-04-29T15:00:00+08:00
draft: false
tags: ["Codex", "AI智能体", "技能库", "自动化", "工作流"]
categories: ["技术笔记"]
description: "Awesome Codex Skills 是 ComposioHQ 维护的 Codex 编码智能体技能库，涵盖代码开发、产品协作、写作、数据分析等场景，支持 Slack/GitHub/Notion 等 1000+ 应用集成。"
slug: awesome-codex-skills-codex-agent-skills
author: ""
---

# Awesome Codex Skills：Codex编码智能体技能库，支持1000+应用集成

## 概述

**Awesome Codex Skills** 是由 [ComposioHQ](https://github.com/ComposioHQ) 维护的 **Codex 编码智能体实用技能库**，收录了一系列模块化的技能指令集（Skills），帮助 Codex 在代码开发、产品协作、写作、数据分析等多个场景中执行真实任务。

Codex 不仅仅是一个生成代码的模型——它可以发送邮件、创建 GitHub Issue、发布 Slack 消息、操作 Notion、生成 PPTX/DOCX 文档，甚至调用 1000+ 应用接口。Awesome Codex Skills 就是这些「技能」的集合。

**GitHub**: [ComposioHQ/awesome-codex-skills](https://github.com/ComposioHQ/awesome-codex-skills)  
**Discord**: [discord.com/invite/composio](https://discord.com/invite/composio)  
**官网**: [composio.dev](https://dashboard.composio.dev/login?utm_source=Github&utm_medium=Youtube&utm_campaign=2025-11&utm_content=AwesomeCodexSkills)

---

## 什么是 Codex Skills？

**Codex Skills** 是模块化的指令包，告诉 Codex 如何按照你期望的方式执行任务。每个技能放在独立文件夹中，包含：

- `SKILL.md`：包含元数据（name + description）和分步指导
- `scripts/`：可选的辅助脚本，用于确定性操作
- `references/`：可选的长文档，只在需要时加载
- `assets/`：可选的模板或资源文件

Codex 通过读取 `SKILL.md` 的元数据来决定何时触发技能，加载时只加载必要的上下文，保持轻量。

### 基本结构

```
skill-name/
├── SKILL.md          # 必需：指令 + YAML frontmatter
├── scripts/          # 可选：辅助脚本
├── references/       # 可选：详细文档（按需加载）
└── assets/          # 可选：模板或资源文件
```

### SKILL.md 模板

```markdown
---
name: my-skill-name
description: 技能描述，说明 Codex 何时应触发此技能
---

# My Skill Name

清晰的分步指导，让 Codex 执行任务
```

---

## 快速上手

### 安装技能（推荐方式）

```bash
git clone https://github.com/ComposioHQ/awesome-codex-skills.git
cd awesome-codex-skills

# 安装单个技能到 ~/.codex/skills/
python skill-installer/scripts/install-skill-from-github.py \
  --repo ComposioHQ/awesome-codex-skills \
  --path meeting-notes-and-actions
```

技能安装到 `$CODEX_HOME/skills`（默认为 `~/.codex/skills/`）。重启 Codex 即可加载新技能。

### 手动安装

1. 复制技能文件夹（如 `./spreadsheet-formula-helper`）到 `~/.codex/skills/`
2. 重启 Codex 以加载新技能元数据
3. 在下一轮对话中自然描述任务，或直接提技能名称触发

---

## 技能分类与精选

### 🛠️ 开发与代码工具（Development & Code Tools）

| 技能 | 描述 |
|------|------|
| [brooks-lint](https://github.com/hyhmrright/brooks-lint) | AI 代码审查，基于六本经典工程书籍（Brooks、McConnell 等），包含衰减风险诊断、严重性标签、四种分析模式（PR审查/架构审计/技术债/测试质量） |
| [codebase-migrate/](https://github.com/ComposioHQ/awesome-codex-skills/tree/main/codebase-migrate) | 大型代码库迁移和多文件重构，支持 CI 验证和可审查的批次处理 |
| [codebase-recon](https://github.com/yujiachen-y/codebase-recon-skill) | 分析 git 历史，理解代码库：热点文件、bug 集中区、总线因子、趋势、高风险文件 |
| [pr-review-ci-fix/](https://github.com/ComposioHQ/awesome-codex-skills/tree/main/pr-review-ci-fix) | **自动化 GitHub/GitLab PR 审查 + CI 自动修复循环**，通过 Composio CLI 执行 |
| [gh-fix-ci/](https://github.com/ComposioHQ/awesome-codex-skills/tree/main/gh-fix-ci) | 检查 GitHub Actions 失败，构建失败摘要并提出修复建议 |
| [mcp-builder/](https://github.com/ComposioHQ/awesome-codex-skills/tree/main/mcp-builder) | 使用最佳实践构建和评估 MCP 服务器 |
| [sentry-triage/](https://github.com/ComposioHQ/awesome-codex-skills/tree/main/sentry-triage) | 诊断 Sentry 问题，将堆栈帧映射到本地源码，无需复制粘贴 |
| [AuraKit](https://github.com/smorky850612/Aurakit) | 全能技能框架：46 种模式、23 个子智能体、6 层 OWASP 安全、10 个生命周期钩子，~55% token 节省 |

### 📊 产品与协作（Productivity & Collaboration）

| 技能 | 描述 |
|------|------|
| [connect/](https://github.com/ComposioHQ/awesome-codex-skills/tree/main/connect) | **通过 Composio CLI 将 Codex 连接到 1000+ 应用**（Slack、GitHub、Notion、Linear 等） |
| [linear/](https://github.com/ComposioHQ/awesome-codex-skills/tree/main/linear) | 在 Linear 中管理 issue、项目和团队工作流 |
| [notion-knowledge-capture/](https://github.com/ComposioHQ/awesome-codex-skills/tree/main/notion-knowledge-capture) | 将聊天或笔记转换为结构化的 Notion 页面，带正确链接 |
| [notion-meeting-intelligence/](https://github.com/ComposioHQ/awesome-codex-skills/tree/main/notion-meeting-intelligence) | 用 Notion 上下文准备会议材料 + Codex 研究 |
| [issue-triage/](https://github.com/ComposioHQ/awesome-codex-skills/tree/main/issue-triage) | 对 Linear 或 Jira 待办事项进行分类，执行 bug 清查 |
| [meeting-notes-and-actions/](https://github.com/ComposioHQ/awesome-codex-skills/tree/main/meeting-notes-and-actions) | 将会议记录转化为摘要，包含决策和带责任人的行动项 |
| [paperjsx/](https://github.com/ComposioHQ/awesome-codex-skills/tree/main/paperjsx) | **从结构化 JSON 生成 PPTX/DOCX/XLSX/PDF 文档**，本地运行 via `@paperjsx/mcp-server`，无需 API key，无需网络调用 |
| [support-ticket-triage/](https://github.com/ComposioHQ/awesome-codex-skills/tree/main/support-ticket-triage) | 客户支持工单分类：类别、优先级、下一步行动、草稿回复 |

### ✍️ 通信与写作（Communication & Writing）

| 技能 | 描述 |
|------|------|
| [unslop](https://github.com/MohamedAbdallah-14/unslop) | **移除 AI 写作模式**（三冒号、过度使用破折号、对冲堆砌、谄媚开头），支持 Codex、Claude Code、Gemini CLI 和 Cursor，五种强度级别和纯审计模式 |
| [email-draft-polish/](https://github.com/ComposioHQ/awesome-codex-skills/tree/main/email-draft-polish) | 为正确语气和受众起草、重写或压缩邮件 |
| [changelog-generator/](https://github.com/ComposioHQ/awesome-codex-skills/tree/main/changelog-generator) | 从提交记录或摘要创建清晰的更新日志 |
| [content-research-writer/](https://github.com/ComposioHQ/awesome-codex-skills/tree/main/content-research-writer) | 带引用的研究和起草内容 |
| [tailored-resume-generator/](https://github.com/ComposioHQ/awesome-codex-skills/tree/main/tailored-resume-generator) | 根据职位描述定制简历，突出可量化的影响力 |

### 📈 数据与分析（Data & Analysis）

| 技能 | 描述 |
|------|------|
| [spreadsheet-formula-helper/](https://github.com/ComposioHQ/awesome-codex-skills/tree/main/spreadsheet-formula-helper) | 编写和调试电子表格公式、数据透视表和数组公式 |
| [datadog-logs/](https://github.com/ComposioHQ/awesome-codex-skills/tree/main/datadog-logs) | 通过 Composio CLI 从终端过滤 Datadog 日志，JSON 友好输出 |
| [developer-growth-analysis/](https://github.com/ComposioHQ/awesome-codex-skills/tree/main/developer-growth-analysis) | 分析 Codex 聊天历史，发现编码模式和学习差距 |
| [langsmith-fetch/](https://github.com/ComposioHQ/awesome-codex-skills/tree/main/langsmith-fetch) | 拉取 LangSmith 项目/测试数据进行分析 |

### 🔧 元工具（Meta & Utilities）

| 技能 | 描述 |
|------|------|
| [skill-installer/](https://github.com/ComposioHQ/awesome-codex-skills/tree/main/skill-installer) | 辅助脚本：从策展列表或 GitHub 路径安装技能 |
| [skill-creator/](https://github.com/ComposioHQ/awesome-codex-skills/tree/main/skill-creator) | 构建高效 Codex 技能的分步指导 |
| [template-skill/](https://github.com/ComposioHQ/awesome-codex-skills/tree/main/template-skill) | 构建新技能的起始模板 |
| [image-enhancer/](https://github.com/ComposioHQ/awesome-codex-skills/tree/main/image-enhancer) | 使用可配置预设升级和优化图像 |

---

## 精选技能详解

### pr-review-ci-fix：自动化 PR 审查 + CI 自动修复

这是 Awesome Codex Skills 中最实用的技能之一。它实现了自动化的 PR 审查 + CI 修复循环：

1. Codex 检测到 PR 的 CI 失败
2. 自动分析失败原因
3. 提出修复方案并执行
4. 推送修复并等待 CI 再次运行

```bash
# 安装
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo ComposioHQ/awesome-codex-skills \
  --path pr-review-ci-fix
```

### paperjsx：从 JSON 生成 PPTX/DOCX/XLSX/PDF

**无需 API key，无需网络调用**，完全本地运行：

```bash
# 通过 MCP server 运行
npx @paperjsx/mcp-server
```

支持：
- PPTX 演示文稿
- DOCX 文档
- XLSX 电子表格（含图表）
- PDF 报告（含图表）

### unslop：移除 AI 写作模式

支持多种 AI 写作模式的检测和移除：
- 三冒号列表（`::: `{something}`:::`）
- 过度使用 em-dash
- 对冲语言堆砌
- 谄媚性开头句

**五种强度级别**，支持 lint-only 审计模式。

### connect：1000+ 应用集成

通过 Composio CLI 将 Codex 连接到真实应用：
- **Slack**：发送消息、创建频道
- **GitHub**：创建 Issue、评论 PR
- **Notion**：创建页面、更新数据库
- **Linear**：管理项目、分配任务
- **更多**：1000+ 应用覆盖

---

## 技能创作指南

### 技能最佳实践

1. **description 要详尽**：清楚说明 Codex 何时应触发此技能
2. **保持主体简洁**：详细文档放入 `references/`，在 `SKILL.md` 中按需引用
3. **包含辅助脚本**：用于可重复或确定性的操作
4. **避免多余文档**：不在技能文件夹内放置 README 或 changelog，保持上下文轻量

### 创作流程

1. 复制 `template-skill/` 作为起始模板
2. 编写 `SKILL.md`（name + description + 指导步骤）
3. 添加必要的 `scripts/` 和 `references/`
4. 测试元数据是否适合上下文限制
5. 提交 PR 到 [awesome-codex-skills](https://github.com/ComposioHQ/awesome-codex-skills)

---

## 适用场景

| 场景 | 推荐技能 |
|------|---------|
| **代码审查** | brooks-lint, pr-review-ci-fix |
| **大型重构** | codebase-migrate, codebase-recon |
| **PR 自动修复** | pr-review-ci-fix, gh-fix-ci |
| **会议记录** | meeting-notes-and-actions, notion-meeting-intelligence |
| **文档生成** | paperjsx, changelog-generator |
| **Notion 集成** | notion-knowledge-capture, notion-research-documentation |
| **AI 写作去噪** | unslop |
| **数据分析** | spreadsheet-formula-helper, langsmith-fetch |

---

## 总结

Awesome Codex Skills 是 **Codex 编码智能体的技能中心**，通过模块化的 SKILL.md 格式，让 Codex 在真实工作流中发挥作用。从代码审查（brooks-lint）、PR 自动修复（pr-review-ci-fix）到文档生成（paperjsx）、Notion 集成（connect），再到 AI 写作去噪（unslop），这个技能库覆盖了开发、协作、写作、数据分析等多个维度。

通过 Composio CLI，Codex 可以连接到 **1000+ 真实应用**（Slack、GitHub、Notion、Linear 等），真正实现「AI 执行真实任务」而不仅仅是「生成文本」。

**推荐指数**：⭐⭐⭐⭐⭐

**适用人群**：使用 Codex/Claude Code 等 AI 编码智能体的开发者，希望提升自动化效率的团队

---

> 📌 **更多信息**
> - GitHub: [ComposioHQ/awesome-codex-skills](https://github.com/ComposioHQ/awesome-codex-skills)
> - Discord: [discord.com/invite/composio](https://discord.com/invite/composio)
> - 官网: [composio.dev](https://dashboard.composio.dev/login)
