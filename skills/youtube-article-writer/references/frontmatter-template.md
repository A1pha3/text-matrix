# 视频精读 Frontmatter 模板

## 字段规范

| 字段 | 必填 | 规则 |
|------|------|------|
| title | 是 | 中文标题，英文专有名词保留原文，用双引号包裹 |
| date | 是 | `YYYY-MM-DDTHH:MM:SS+08:00`，必须 ≤ 当前北京时间 |
| slug | 是 | 小写英文 + 连字符，无空格 |
| description | 是 | 50-100 字纯文本摘要，无 Markdown |
| draft | 是 | `false` |
| categories | 是 | 固定为 `["视频精读"]`（inline array，不用 YAML 短横线格式） |
| tags | 是 | 2-5 个精准名词，inline array 格式 |
| hiddenFromHomePage | 否 | 视频精读分类禁止使用此字段 |

## 模板

```yaml
---
title: "{中文标题}"
date: {YYYY-MM-DDTHH:MM:SS+08:00}
slug: "{lowercase-english-slug}"
description: "{50-100字摘要}"
draft: false
categories: ["视频精读"]
tags: ["{tag1}", "{tag2}", "{tag3}"]
---
```

## 示例

```yaml
---
title: "AI Agents 全栈指南：Nick Saraev 2小时大师班深度解析"
date: 2026-04-29T15:01:00+08:00
slug: "ai-agents-full-course-2026-nick-saraev-200k-views"
description: "Nick Saraev AI Agents全栈课程深度解析，涵盖ReAct、Tool Use、Memory、Multi-Agent系统与生产级部署，从入门到专家的完整技术路径。"
draft: false
categories: ["视频精读"]
tags: ["AI Agent", "Nick Saraev", "Multi-Agent", "LangChain", "生产部署"]
---
```

## 常见错误

| 错误 | 正确 |
|------|------|
| `categories:\n  - 视频精读` | `categories: ["视频精读"]` |
| `date: 2026-04-29` | `date: 2026-04-29T15:01:00+08:00` |
| `slug: "AI Agents Full Course"` | `slug: "ai-agents-full-course-2026-nick-saraev-200k-views"` |
| description 含 Markdown | 50-100 字纯文本 |
| tags 只有 1 个 | 至少 2 个 |
| `hiddenFromHomePage: true` | 删除此字段（仅行业快讯使用） |
