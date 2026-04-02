# GitHub 文章 Frontmatter 模板

```yaml
---
title: "{项目名}：{一句话描述}"
date: YYYY-MM-DDTHH:MM:SS+08:00
slug: "{小写英文连字符}"
description: "{50-100字的摘要，纯文本}"
draft: false
categories: ["技术笔记"]
tags: ["标签1", "标签2", "标签3"]
---
```

## 字段说明

| 字段 | 要求 |
|------|------|
| title | 中文标题，包含项目名和一句话描述 |
| date | **必须**是当前系统时间，格式 `YYYY-MM-DDTHH:MM:SS+08:00` |
| slug | 小写英文+连字符，如 `hyperagents-guide` |
| description | 50-100字，纯文本摘要，无 Markdown 格式 |
| categories | 必须且仅一个：`["技术笔记"]` |
| tags | 2-5个精准名词，如 `["AI", "机器学习", "开源"]` |

## 示例

```yaml
---
title: "Hyperagents：自指性自我改进智能体完全指南"
date: 2026-04-02T18:00:00+08:00
slug: "hyperagents-self-referential-ai-agents-guide"
description: "Hyperagents是Meta FAIR提出的自指性自我改进智能体框架，通过任务智能体和元智能体的双层架构实现开放式自我改进。本文详细解析了其核心原理、算法流程、代码架构及在各领域的应用。"
draft: false
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
