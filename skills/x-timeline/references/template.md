# 文章模板（x-timeline）

## Frontmatter 规则

- `date` = 实际写入磁盘时刻 − 5 分钟（`TZ=Asia/Shanghai date -v-5M "+%Y-%m-%dT%H:%M:%S+08:00"`），**禁止填计划发布时刻**。
- `slug` 固定 `x-timeline-YYYY-MM-DD`，输出文件名 = `slug.md`，路径 `content/posts/news/`。
- `categories` 固定 `["行业快讯"]`；必须含 `draft: false` 与 `hiddenFromHomePage: true`。
- `description` 50–100 字纯文本。
- 正文不写 H1（页面主标题由 `title` 提供）。

```yaml
---
title: "X时间线精选 YYYY-MM-DD"
date: YYYY-MM-DDTHH:MM:SS+08:00
slug: x-timeline-YYYY-MM-DD
description: "YYYY年MM月DD日 X 时间线 24 小时精选：AI、市场与创业领域值得关注的 N 条内容。"
draft: false
categories: ["行业快讯"]
tags: ["X精选", "时间线", "AI", "资讯"]   # 2-5 个精准名词
hiddenFromHomePage: true
---
```

## 正文模板

```markdown
🦞 每日定时更新 · 覆盖过去 24 小时 X 时间线

---

## 🏆 今日头条

### 标题（中文提炼）
作者: 名称（@handle） · 分类: 🤖 AI 与技术
摘要: 2-3 句实质性提炼
原文摘录: "译文或中文原文（≤3 行）"

<details>
<summary>原文（English）</summary>

Original tweet text...

</details>

原文: [原文](https://x.com/xxx/status/123)

---

## 🤖 AI 与技术

### 标题
作者: 名称（@handle） · 发布于 3 小时前
摘要: 2-3 句实质性提炼
原文摘录: "……"
原文: [原文](https://x.com/xxx/status/123)

### 标题（转推条目示例）
转推者: 名称（@handle） · 原帖发布于 2 天前
摘要: 2-3 句实质性提炼
原文摘录: "……"
原文: [原文](https://x.com/原作者/status/456)

### 标题（thread 合并条目示例，全串 5 篇）
作者: 名称（@handle） · 发布于 6 小时前
摘要: 覆盖全串要点的 2-3 句提炼
原文摘录: "串首推文本（≤3 行）"
原文: [原文](https://x.com/xxx/status/串首推id)

## 💰 市场与投资
（同上结构，空分类省略）

---

## 📋 采集报告

| 指标 | 数值 |
| ------ | ------ |
| 采集总数 | N 条 |
| 结构合并 | thread 合并 a 组 / 重复转推去重 b 条 |
| 过滤数 | N 条（广告 a / 低价值 b / 超窗 c / 墓碑 d / 跨日重复 e） |
| 收录数 | N 条 |
| 时间窗 | 闭合（HH:mm ~ HH:mm）/ 未闭合（实际覆盖 X 小时，原因） |

**待人工复核**：@handle 的 1 条内容（原因：拿不准价值）— [链接](url)
（无待复核时写：无）

**数据来源**：X（x.com）「正在关注」时间线，采集窗口 YYYY-MM-DD HH:mm ~ YYYY-MM-DD HH:mm
```

## 要素与链接规范

- 每条三要素齐备：摘要（2–3 句实质提炼）+ 原文摘录（≤3 行）+ `[原文](url)`，缺一不可。
- 非中文条目：摘要与摘录用中文译文，`<details>` 块保留原文原貌（`show_original_in_details: false` 时省略 details 块）。
- 原文链接固定 `[原文](https://x.com/<user>/status/<id>)`，由采集数据的 `post_id` 构造；禁止裸 URL、禁止聚合页、禁止猜测。
- 引用推文保留时，需同时给出被引对象链接。
- 转推条目链接指向**原推**，展示行标注转推者与原帖发布时间。
- 文末统计数字必须与正文条目数一致，禁止保留模板占位值。
