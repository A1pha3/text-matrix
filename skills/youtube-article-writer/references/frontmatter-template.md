# 视频精读 Frontmatter 模板

## 字段规范

| 字段 | 必填 | 规则 |
|------|------|------|
| title | 是 | 中文标题，英文专有名词保留原文，用双引号包裹 |
| date | 是 | `YYYY-MM-DDTHH:MM:SS+08:00`，必须 ≤ 当前北京时间 |
| slug | 是 | 小写英文 + 连字符，无空格（**严禁 `index`**，会把文章卡在构建外） |
| source_key | 是 | 视频稿稳定身份锚点：`bv:{bvid}`（B站）或 `yt:{视频ID}`（YouTube）。发布去重/防漏判定用，frontmatter_lint 强制校验 |
| description | 是 | 50-100 字纯文本摘要，无 Markdown |
| draft | 是 | **`true`**：写完默认暂存不上线；cn-doc-writer 三维评分达 B 级（≥70）才翻 `false` 并 push 上线 |
| categories | 是 | 固定为 `["视频精读"]`（inline array，不用 YAML 短横线格式） |
| tags | 是 | 2-5 个精准名词，inline array 格式 |
| hiddenFromHomePage | 否 | 视频精读分类禁止使用此字段 |

> **落盘契约（2026-08-06 师父拍板）**：写完**直接落 `content/posts/video/<slug>/index.md`**，**严禁落 `state/` 中间态**（旧两段式接力是重复发布与误报病根，已废弃）。上线与否只由 `draft` 布尔位决定。

## 模板

```yaml
---
title: "{中文标题}"
date: {YYYY-MM-DDTHH:MM:SS+08:00}
slug: "{lowercase-english-slug}"
source_key: "bv:{bvid}"
description: "{50-100字摘要}"
draft: true
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
source_key: "yt:dQw4w9WgXcQ"
description: "Nick Saraev AI Agents全栈课程深度解析，涵盖ReAct、Tool Use、Memory、Multi-Agent系统与生产级部署，从入门到专家的完整技术路径。"
draft: true
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
| `slug: index`（或 `slug : index`） | 语义化小写连字符 slug——`index` 会造成全站 Duplicate target paths 冲突，把文章卡在构建外 |
| 漏写 `source_key` | `bv:{bvid}` 或 `yt:{视频ID}`，漏写则 lint fatal |
| `draft: false` 直接落盘 | 写完必须 `draft: true`，评分达标才翻 `false` |
| 落盘到 `state/` | 直接落 `content/posts/video/<slug>/`，state 中间态已废弃 |
| description 含 Markdown | 50-100 字纯文本 |
| tags 只有 1 个 | 至少 2 个 |
| `hiddenFromHomePage: true` | 删除此字段（仅行业快讯使用） |
