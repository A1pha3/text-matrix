---
title: "Awesome Codex Skills：Codex CLI 的技能宝库，让 AI 代理真正替你干活"
date: "2026-04-27T00:58:00+08:00"
slug: awesome-codex-skills
description: "Codex Skills 是模块化指令包，让 Codex CLI 能执行发邮件、操作 GitHub、发 Slack 等真实任务。本文全景解析十大分类热门技能及构建方法。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "Codex", "OpenAI", "自动化", "工作流"]
---


如果你一直在用 Codex CLI 或 OpenAI 的 Codex API，但感觉它"只会生成文本"，那说明你还没有真正了解 Codex Skills。

Codex Skills 是 Awesome Codex Skills 项目（以下简称 ACS）提出的核心理念：**Codex 不只能生成文本，它能替你执行完整的任务流程**——发邮件、创建 GitHub Issue、发 Slack 消息、操作 Notion、跑自动化脚本，1000+ 应用全覆盖。

本文带你彻底理解这个技能生态。

---

## 一、Codex Skills 是什么？

Codex Skills 是模块化的指令包，每个 Skill 独立存在于一个文件夹里，以 `SKILL.md` 为主入口。Codex 在运行时读取 Skill 的 `description` 元数据来判断何时触发这个技能，触发后才加载详细步骤——始终保持上下文轻量。

从结构上看，一个 Skill 通常长这样：

```
skill-name/
├── SKILL.md          # 必选：指令 + YAML frontmatter
├── scripts/          # 可选：确定性辅助脚本
├── references/       # 可选：长文档，仅在需要时加载
└── assets/          # 可选：模板或静态资源
```

而 `SKILL.md` 的基本格式也非常简单：

```markdown
---
name: my-skill-name
description: 这个技能做什么，以及何时触发。
---

# My Skill Name

执行步骤...
```

**关键设计哲学**：描述决定触发，body 决定执行。描述写得越精准，Codex 越能在对的时间调用对的技能。

---

## 二、快速上手：把 Skills 跑起来

### 方式一：Skill Installer（推荐）

```bash
git clone https://github.com/ComposioHQ/awesome-codex-skills.git
cd awesome-codex-skills/awesome-codex-skills

# 安装单个技能到 ~/.codex/skills/
python skill-installer/scripts/install-skill-from-github.py \
  --repo ComposioHQ/awesome-codex-skills \
  --path meeting-notes-and-actions
```

安装完毕后重启 Codex，新技能即生效。在对话中自然描述任务，Codex 自动匹配触发。

### 方式二：手动安装

1. 复制目标技能文件夹到 `$CODEX_HOME/skills/`（默认 `~/.codex/skills/`）
2. 重启 Codex 使其重新加载元数据
3. 开始对话

---

## 三、Skill 全景图：十大分类总览

ACS 将技能分为十大分类，以下是每个分类下的明星技能及核心能力。

### 3.1 开发与代码工具（Development & Code Tools）

| 技能 | 来源 | 能力 |
|------|------|------|
| `brooks-lint` | hyhmrright | AI 代码审查，基于六本经典工程著作，输出衰减风险诊断 + 严重等级 + 四种分析模式 |
| `codebase-migrate` | 内置 | 大型代码库迁移，支持多文件重构批量审查 + CI 验证 |
| `deploy-pipeline` | 内置 | 端到端 Stripe → Supabase → Vercel 流水线，含验证和回滚 |
| `gh-address-comments` | 内置 | 用 `gh` 命令 addressing GitHub PR 上的 review/inissue 评论 |
| `gh-fix-ci` | 内置 | 检查 GitHub Actions 失败原因并给出修复建议 |
| `mcp-builder` | 内置 | 构建和评估 MCP 服务器，含最佳实践和评估工具 |
| `sentry-triage` | 内置 | 诊断 Sentry 问题，自动映射堆栈帧到本地源码 |
| `webapp-testing` | 内置 |  Targeted Web 应用测试并汇总结果 |

### 3.2 生产力与协作（Productivity & Collaboration）

| 技能 | 能力 |
|------|------|
| `connect` | 通过 Composio CLI 连接 1000+ 应用（Slack、GitHub、Notion 等）|
| `linear` | 在 Linear 中管理 issue、project 和团队工作流 |
| `meeting-notes-and-actions` | 将会议转录稿转化为摘要，含决策和责任人 action item |
| `notion-meeting-intelligence` | 聚合 Notion 上下文 + Codex 研究，生成会议准备材料 |
| `invoice-organizer` | 规范化发票数据，支持追踪和报表 |
| `support-ticket-triage` | 客户工单分类、优先级排序 + 起草回复 |

### 3.3 通信与写作（Communication & Writing）

| 技能 | 能力 |
|------|------|
| `email-draft-polish` | 起草、润色或压缩邮件，适配目标语气和受众 |
| `changelog-generator` | 从 commit 或摘要生成清晰的 changelog |
| `content-research-writer` | 研究 + 起草内容，含引文来源 |
| `tailored-resume-generator` | 根据岗位描述定制简历，突出量化成果 |

### 3.4 数据与分析（Data & Analysis）

| 技能 | 能力 |
|------|------|
| `spreadsheet-formula-helper` | 编写和调试 Excel/Sheets 公式、透视表、数组公式 |
| `datadog-logs` | 通过 Composio CLI 过滤 Datadog 日志，输出 JSON 友好格式 |
| `lead-research-assistant` | 研究潜在客户，补充公司层面数据 |
| `langsmith-fetch` | 拉取 LangSmith 项目/测试数据用于分析 |

### 3.5 Meta 与工具（Meta & Utilities）

| 技能 | 能力 |
|------|------|
| `skill-creator` | 构建新技能的最佳实践指导 |
| `skill-installer` | 从 GitHub 安装技能的脚本工具 |
| `template-skill` | 新技能的起步模板 |

---

## 四、热门技能深度解析

### 4.1 connect：打通 1000+ 应用的钥匙

`connect` 是 ACS 中最核心的技能之一。通过 Composio CLI，它让 Codex 能够操作真实应用——不是"告诉你怎么做"，而是**真正替你执行**。

支持的生态包括：

- **协作工具**：Slack、Discord、Notion、Linear、Jira
- **代码平台**：GitHub、GitLab、Bitbucket
- **云服务**：AWS、Stripe、Supabase、Vercel
- **数据平台**：Datadog、LangSmith、Helium（实时新闻 + 市场数据）

安装后，Codex 可以代替你做类似这样的事："在 Slack 发一条消息说上线成功"、"在 GitHub 创建一个 issue"、"在 Notion 更新这篇文档的状态"。

### 4.2 meeting-notes-and-actions：从会议记录到可执行任务

这个技能解决了一个经典痛点：**会议开完了，决策散落在聊天记录里，没人跟进**。

输入一段会议转录稿，它会输出：

- 结构化摘要（议程、讨论点、决策）
- 每个 action item 标注负责人的标签
- 清晰的跟进项列表

配合 `notion-meeting-intelligence`，还能在会前基于 Notion 中的上下文自动准备材料，会后自动同步到 Notion 知识库。

### 4.3 brooks-lint：用经典工程智慧做代码审查

`brooks-lint` 是一个独特的 AI 审查框架，核心理念是"将经典工程著作的智慧引入代码审查"。它基于六本经典书籍（《人月神话》《代码大全》等），对代码进行以下维度的诊断：

- **衰减风险诊断**：识别代码退化的早期信号
- **严重等级**：Critical / Major / Minor / Note 四级
- **四种分析模式**：PR review、架构审计、技术债务评估、测试质量分析

每个问题都会附带书籍引用，让审查结果有据可查，而不只是模型拍拍脑袋。

### 4.4 sentry-triage：告别复制粘贴堆栈帧

Sentry 报警来了，通常的流程是：复制堆栈帧 → 打开代码 → 手动匹配。有了 `sentry-triage`，这个流程被自动化了：

1. 读取 Sentry 报警的堆栈信息
2. 自动映射到本地源码文件
3. 输出诊断结果和修复建议

全程不需要复制粘贴，消除了人工匹配的误差。

---

## 五、如何构建自己的 Skill

ACS 提供了完整的 [skill-creator](./skill-creator/) 指导，以及 [template-skill](./template-skill/) 起步模板。构建流程概括如下：

### 第一步：定义触发条件（description）

```markdown
---
name: my-new-skill
description: 当用户要求 [具体任务] 时触发这个技能。
---
```

描述要具体到 Codex 能准确判断"这个技能该上场了"。避免过于泛化的描述。

### 第二步：写执行步骤

- 保持步骤清晰、可执行
- 使用确定性脚本处理重复操作
- 将长文档放进 `references/`，正文按需引用

### 第三步：测试与调优

1. 放入 `$CODEX_HOME/skills/`
2. 重启 Codex
3. 用触发描述测试，看是否精准命中
4. 调整 description 措辞直到稳定

---

## 六、Skill 安装器的工作原理

`skill-installer` 是 ACS 提供的一个 Python 脚本，核心逻辑很简洁：

1. 从 GitHub 指定 repo + path 拉取技能文件夹
2. 将内容移动到 `$CODEX_HOME/skills/<skill-name>/`
3. Codex 重启后自动扫描并加载元数据

如果你维护着自己的技能库，只需提供 `--repo` 和 `--path` 即可分发。安装路径完全可控，不满意默认位置也可以手动搬运。

---

## 七、适用场景横向对比

| 场景 | 推荐技能 |
|------|---------|
| 会议管理全流程 | `meeting-notes-and-actions` + `notion-meeting-intelligence` |
| 代码审查与 CI 修复 | `brooks-lint` + `gh-fix-ci` + `pr-review-ci-fix` |
| 客户支持工单处理 | `support-ticket-triage` + `email-draft-polish` |
| 数据分析与日志查询 | `datadog-logs` + `langsmith-fetch` + `spreadsheet-formula-helper` |
| 跨应用自动化 | `connect` + `linear` + `notion-knowledge-capture` |
| 内容创作流水线 | `content-research-writer` + `changelog-generator` + `tailored-resume-generator` |

---

## 八、与 MCP 的关系：helium-mcp

ACS 中有一个值得单独关注的技能——`helium-mcp/`。它集成了实时新闻搜索（含偏差评分）、实时市场数据、ML 期权定价和平衡新闻综合，通过 MCP（Model Context Protocol）协议为 Codex 提供实时数据能力。

如果你在构建需要**实时信息**的 AI 代理，helium-mcp 是一个将 Codex 接入 live data 的出色方案。

---

## 总结

Awesome Codex Skills 不是一个单纯的技能列表，它是一个**让 AI 代理从"会说"到"会做"的完整生态**。通过模块化的 Skill 设计，Codex 可以在保持上下文精简的同时，按需调用任意复杂度的任务执行能力。

如果你在用 Codex CLI，不妨先从 `connect` 和 `meeting-notes-and-actions` 入手——一个打通外部工具，一个解决日常协作痛点，两者的组合就能显著提升工作效率。在此基础上，根据自己的日常工作流选择对应的 Skills，逐步构建起属于你的个人 AI 代理体系。

**相关链接：**

- GitHub：https://github.com/ComposioHQ/awesome-codex-skills
- Composio 官网：https://dashboard.composio.dev
- Discord 社区：https://discord.com/invite/composio

🦞 每日08:00自动更新
