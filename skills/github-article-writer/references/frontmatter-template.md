# GitHub 文章 Frontmatter 模板

```yaml
---
title: "{项目名}：{一句话描述}"
date: YYYY-MM-DDTHH:MM:SS+08:00
slug: "{小写英文连字符}"
github_repo: "{owner/repo}"
source_key: "gh:{owner/repo}"
description: "{50-100字的摘要，纯文本}"
draft: true
categories: ["技术笔记"]
tags: ["标签1", "标签2", "标签3"]
---
```

> **`draft` 与 `source_key` 是免审批自动发布管线的两个开关**（2026-08-06 师父拍板）：
> - 写完落盘一律 `draft: true`（暂存，Hugo 构建排除、不上线）。
> - 经 cn-doc-writer 三维评分达 **B 级（≥70）** 才翻 `draft: false` 并 commit+push 上线；<70 留 draft 转人工。
> - 写完**直接落 `content/posts/tech/<slug>/index.md`**，**严禁落 `state/` 中间态**（旧两段式接力是重复发布与误报的病根，已废弃）。

## 字段说明

| 字段 | 要求 |
|------|------|
| title | 中文标题，包含项目名和一句话描述 |
| date | **必须**是当前系统时间，格式 `YYYY-MM-DDTHH:MM:SS+08:00` |
| slug | 小写英文+连字符，如 `hyperagents-guide` |
| github_repo | **必须**：`owner/repo`，取自 `gh repo view` 的 nameWithOwner，大小写原样保留（如 `0xNyk/council`）— trending 去重的结构化身份字段 |
| source_key | **必须**：`gh:{owner/repo}`，与 `github_repo` 同源、一键生成（前缀 `gh:`）。发布去重/防漏判定的唯一稳定身份锚点，frontmatter_lint 强制校验 |
| description | 50-100字，纯文本摘要，无 Markdown 格式 |
| draft | **必须 `true`**：写完默认暂存不上线；评分达标（≥B 级）后才翻 `false` |
| categories | 必须且仅一个：`["技术笔记"]` |
| tags | 2-5个精准名词，如 `["AI", "机器学习", "开源"]` |

## 示例

```yaml
---
title: "Hyperagents：自指性自我改进智能体完全指南"
date: 2026-04-02T18:00:00+08:00
slug: "hyperagents-self-referential-ai-agents-guide"
github_repo: "facebookresearch/HyperAgents"
source_key: "gh:facebookresearch/HyperAgents"
description: "Hyperagents是Meta FAIR提出的自指性自我改进智能体框架，通过任务智能体和元智能体的双层架构实现开放式自我改进。本文详细解析了其核心原理、算法流程、代码架构及在各领域的应用。"
draft: true
categories: ["技术笔记"]
tags: ["AI Agent", "Hyperagents", "元学习", "自我改进", "Meta FAIR"]
---
```

## 常见错误

❌ `date: 2026-04-02` —— 缺少时间
❌ `date: 2026-04-02T18:00` —— 缺少时区
❌ `categories: ["技术笔记", "其他"]` —— 多个分类
❌ `tags: ["技术"]` —— 标签过少（需2-5个）
❌ `hiddenFromHomePage: true` —— 技术笔记不应有此字段
❌ 漏写 `github_repo` —— trending 去重依赖此字段，漏写会导致未来该 repo 被重复写
❌ 漏写 `source_key` 或写成非 `gh:owner/repo` 格式 —— 发布去重/防漏判定失灵，frontmatter_lint 会 fatal 拦截
❌ `draft: false` 直接落盘 —— 写完必须 `draft: true` 暂存，评分达标才翻 `false`
❌ 落盘到 `state/` 而非 `content/posts/tech/` —— state 中间态已废弃，是重复发布病根
❌ `slug: index` —— 全站构建冲突毒药（Duplicate target paths），会把文章卡在构建外不上线；slug 必须是语义化小写连字符
❌ `github_repo: "0xnyk/council"` —— 大小写错（应为 `0xNyk`，与 GitHub 实际一致）
