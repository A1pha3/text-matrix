---
title: "openai/skills 谢幕解读：Agent Skills 官方样本库的遗产与迁移路径"
date: "2026-09-11T03:45:00+08:00"
slug: "openai-skills-deprecated-catalog-legacy-migration"
github_repo: "openai/skills"
source_key: "gh:openai/skills"
aliases:
  - "/posts/tech/openai-skills-deprecated-catalog-legacy-migration/"
description: "openai/skills 是 OpenAI 为 Codex 打造的 Agent Skills 官方目录，2026 年 6 月正式废弃并入 openai/plugins。本文解读它留下的技能包结构标准、skill-installer 机制与完整迁移路径。"
draft: false
categories: ["技术笔记"]
tags: ["OpenAI", "Codex", "Agent Skills", "AI Agent", "开源项目"]
---

# openai/skills 谢幕解读：Agent Skills 官方样本库的遗产与迁移路径

> **目标读者**：使用 OpenAI Codex 的开发者；关注 Agent Skills（智能体技能）开放标准的工程师
> **核心问题**：openai/skills 为什么废弃？它留下了什么值得学的东西？已有的技能（skill）工作流该迁到哪里？
> **难度**：⭐（概念导读 + 迁移指引）
> **来源**：GitHub [openai/skills](https://github.com/openai/skills)，26,848 ★ / 1,800 fork / 2026-09-10 仍在接收镜像更新

## 先给结论

openai/skills 是一个**已经官方废弃、但仍然值得读一次**的仓库。它于 2025 年 11 月创建，是 OpenAI 为 Codex（其编码智能体）建立的第一个 Agent Skills 官方目录；2026 年 6 月 22 日，一条名为 "Deprecate skills repository" 的提交正式宣布了它的谢幕——技能与插件（plugin）示例统一迁往 [openai/plugins](https://github.com/openai/plugins)，自定义技能的开发流程收敛到官方文档的 [Build plugins](https://developers.openai.com/codex/plugins/build) 指南。

它值得读，是因为这个仓库本身就是 "Agent Skills" 开放标准（agentskills.io）最完整的官方实现样本：一个技能包长什么样、SKILL.md 怎么写、脚本和资源怎么组织、如何被安装器发现和调用——这些约定在迁移后全部被保留。读懂它，等于读懂了 Codex 技能体系的底层语法。

## 它解决过什么问题

Agent Skills 的核心思想是"一次编写，到处使用"（write once, use everywhere）：把完成某类任务所需的指令、脚本和资源打包成一个文件夹，AI 智能体可以自主发现并调用它。在它出现之前，给编码智能体扩展能力的主要方式是 MCP（Model Context Protocol，模型上下文协议）服务器——需要常驻进程和协议握手；而技能包只是静态文件加说明书，智能体按需读取，成本几乎为零。

openai/skills 承担的角色是这个体系的"官方货架"：

- **`.system/`**：随最新版 Codex 自动安装的系统级技能，包括 `skill-creator`（创建技能）、`skill-installer`（安装技能）、`plugin-creator`、`imagegen`、`openai-docs` 等五个；
- **`.curated/`**：官方精选目录，39 个技能覆盖 Figma 设计转码（8 个 figma 系列）、Notion 知识管理（4 个）、CI 修复（`gh-fix-ci`）、安全分析（威胁建模、安全最佳实践）、部署（Vercel / Netlify / Cloudflare / Render）等场景。

以 `gh-fix-ci` 为例，一个精选技能包的标准结构是：

```
gh-fix-ci/
├── LICENSE.txt      # 每个技能独立授权
├── SKILL.md         # 入口说明书（frontmatter 含 name + 触发式 description）
├── agents/          # 可选：子智能体定义
├── assets/          # 可选：静态资源
└── scripts/         # 可选：可执行脚本（如 inspect_pr_checks.py）
```

SKILL.md 的 frontmatter 只有两个字段：`name` 和 `description`。description 不是文档摘要，而是**触发条件**——写明"当用户要求修复 GitHub PR 检查失败时使用"，智能体据此判断何时激活该技能。正文则按 Overview / Inputs / Quick start / Workflow 组织，把人类专家的排障流程固化为智能体可执行的步骤。这个极简约定，正是它留给整个生态最重要的遗产。

## 安装机制：skill-installer

旧仓库内技能的安装统一通过 Codex 内置的 `$skill-installer`：

```
$skill-installer gh-address-comments
```

按名字安装，默认从 `.curated` 目录解析；实验性技能需要指明来源文件夹或 GitHub 目录 URL；安装后重启 Codex 生效。最后一条有效提交（2026-06-24）正是更新 skill-installer 的安装后引导——这也暗示废弃后的过渡策略：安装器本身仍在 Codex 侧持续维护，只是货架换了。

## 迁移路径：三条去向

如果你的工作流还依赖这个仓库，按场景对号入座：

| 你的场景 | 迁移去向 |
|---|---|
| 寻找现成技能 / 插件示例 | [openai/plugins](https://github.com/openai/plugins)，官方精选合集 |
| 想给 Codex 写自定义技能 | [Build plugins](https://developers.openai.com/codex/plugins/build) 指南，技能可作为"仅含技能的插件"发布 |
| 了解技能概念与标准 | [Using skills in Codex](https://developers.openai.com/codex/skills) 与 [agentskills.io](https://agentskills.io) |

需要说明的边界：仓库 README 未给出旧技能与新插件目录的一一对应表，`.curated` 中的技能是否全部平移进 openai/plugins，需以新仓库实际内容为准，本文不做推断。

## 适用边界

- 它是**历史样本库**，新项目不应再基于它构建；
- 它没有仓库级 LICENSE——授权按每个技能目录内的 `LICENSE.txt` 独立声明，引用代码前需逐个确认；
- 26,848 星让它仍出现在月度趋势榜上，但热度是"遗产热度"：主语言 Python 只是安装器脚本的副产物，真正的内容是 Markdown 与目录约定；
- 本文写作时其最新提交停留在 2026 年 6 月底，此后只有镜像性更新，不再演进。

## 为什么还值得收藏

把 openai/skills 理解为一本"已绝版但不过时的教材"：技能包结构、SKILL.md 触发式写法、静态资源式扩展（对比 MCP 的常驻进程式扩展）——这些设计决策在 openai/plugins 和 agentskills.io 标准中全部延续。如果你在评估"该给自己的智能体配 MCP 服务器还是技能包"，花二十分钟翻一翻 `.curated` 里的几个 SKILL.md，比读任何二手解读都直接。
