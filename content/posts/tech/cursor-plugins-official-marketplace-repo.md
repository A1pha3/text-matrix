---
title: "Cursor 官方插件仓库：从 plugin.json 到可发布插件"
date: "2026-08-23T03:21:00+08:00"
slug: cursor-plugins-official-marketplace-repo
github_repo: "cursor/plugins"
source_key: "gh:cursor/plugins"
description: "cursor/plugins 是 Cursor 官方插件市场仓库，用统一的 .cursor-plugin/plugin.json 清单承载技能、规则、MCP 集成与 Agent 定义。本文解析仓库结构、plugin.json schema 与创建插件的完整流程，帮读者理解 Cursor 插件体系的组装方式。"
draft: false
categories: ["技术笔记"]
tags: ["Cursor", "插件", "MCP", "AI 编程", "Agent"]
---

# Cursor 官方插件仓库：从 plugin.json 到可发布插件

## 核心判断

cursor/plugins 不是一个「插件代码库」，而是一个**插件市场仓库**——每个插件是仓库根目录下一个独立目录，靠 `.cursor-plugin/plugin.json` 清单把 `skills`（Agent 技能）、`rules`（规则）、`mcp.json`（MCP 集成）、agents、commands 组装成一份可被 Cursor 市场消费的插件。看懂这个仓库的组装规则，就懂了 Cursor 插件体系的最小骨架。

仓库当前约 4600 stars，MIT 协议，活跃维护（最近提交集中在 2026-08-21），作者字段与各插件 `plugin.json` 的 `author.name` 一致（Cursor 官方插件统一登记为 `plugins@cursor.com`）。

## 仓库结构：一个 marketplace，一堆插件目录

根目录的 `.cursor-plugin/marketplace.json` 列出所有插件（name + source + description），每个插件目录自带自己的 `.cursor-plugin/plugin.json`：

```
plugins/
├── .cursor-plugin/
│   └── marketplace.json       # 市场清单：登记所有插件
├── plugin-name/
│   ├── .cursor-plugin/
│   │   └── plugin.json        # 单插件清单
│   ├── skills/                # Agent 技能（SKILL.md，带 frontmatter）
│   ├── rules/                 # Cursor 规则（.mdc 文件）
│   ├── mcp.json               # MCP 服务器定义
│   ├── README.md
│   ├── CHANGELOG.md
│   └── LICENSE
└── ...
```

`schemas/` 下提供两份 JSON Schema：`plugin.schema.json`（单插件清单）与 `marketplace.schema.json`（市场清单），供校验与补全使用。

## plugin.json：插件的身份证明

`plugin.schema.json` 定义了 `plugin.json` 的约束。核心字段如下：

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | kebab-case 唯一标识，必填 |
| `displayName` | string | 人类可读的插件名 |
| `description` | string | 插件做什么的一句话描述 |
| `version` | string | 语义化版本号 |
| `minClientVersions` | object | 各客户端标识对应的最低版本 |
| `author` / `publisher` | object / string | 作者信息与发布方 |
| `category` / `tags` | string / array | 市场分类与发现标签 |
| `commands` / `agents` / `skills` / `rules` | string / array | 各组件文件的 glob 或路径 |
| `hooks` | string / object | 钩子配置文件的路径或内联对象 |
| `variables` | object | 变量定义（含 `type`） |

关键点：`plugin.json` 不内联插件内容，而是**声明组件文件的位置**。`skills`、`rules`、`commands`、`agents` 都是指向目录下实际文件的 glob/path，`mcp.json` 单独承载 MCP 服务器定义。这个「清单 + 目录约定」的组合，让市场既能预览插件能力，又能按需加载组件。

## 官方插件：从工具到工作流

仓库按来源分两类：Cursor 自研（根目录）与第三方集成（`third_party/`）。自研插件覆盖了开发工作流的不同层次：

- **开发工具类**：`thermos`（分支深度审查）、`pr-review-canvas`（PR diff 画布）、`docs-canvas`（文档导航画布）、`cli-for-agent`（面向编码 Agent 的 CLI 设计模式）
- **Agent 工作流类**：`orchestrate`（跨云 Agent 并行派发）、`ralph-loop`（迭代自指循环）、`continual-learning`（增量转录驱动的记忆更新）、`agent-compatibility`（仓库兼容性扫描）
- **教学类**：`teaching`（技能映射与练习计划）
- **基础设施类**：`cursor-sdk`（TypeScript SDK）、`create-plugin`（脚手架与校验）

`third_party/` 下是与 SaaS 的集成：gmail、google-drive、google-calendar、github、playwright、salesforce、zoom、intercom、hubspot 等，基本覆盖「读邮件 / 查日历 / 管代码 / 抓页面」的办公自动化主干。

## 创建插件：create-plugin 的典型流程

`create-plugin` 插件把「做一个市场可用的插件」拆成可执行的步骤：

1. 用 `/create-plugin` 命令，带插件名、用途、目标组件类型
2. 生成或更新 `plugin.json`，按需添加 rules / skills / agents / commands
3. 发布或提交市场前，跑 `review-plugin-submission` 做提交前质量检查

配套的 `plugin-quality-gates` 规则负责保持清单、组件元数据与路径的有效性和一致性；`plugin-architect` agent 根据具体用例设计插件结构与组件组合。

## 采用建议与边界

- **想写 Cursor 插件**：clone 这个仓库当参考，照 `plugin.json` schema 起步，再用 `create-plugin` 脚手架省掉手搓清单的功夫
- **想理解 Cursor 插件体系**：本文的「清单 + 目录约定」是核心心智模型——插件不是一段代码，是一份描述组件位置的清单
- **边界**：cursor/plugins 是市场仓库，不是 Cursor 客户端源码；插件实际执行机制（skills/rules 如何被加载运行）要看 Cursor 客户端与 `cursor-sdk`，本仓库只负责「组织与分发」。第三方插件由对应 SaaS 方维护，质量与更新节奏不一

本文聚焦仓库结构、plugin.json 与创建流程，不展开单个第三方集成的内部实现。
