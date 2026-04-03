---
name: morning-report
description: 每日早报生成工作流。适用于每天08:00-09:00窗口生成AI新闻早报、经济财经早报、AI副业早报。当用户说"做早报"、"写早报"、"生成早报"、"morning report"时触发。包含三大早报的采集规范、格式要求、链接核查流程。
---

# 每日早报生成 Skill

## 概述

每日生成三份早报：
- **AI新闻早报** (08:00) - AI行业新闻
- **经济财经早报** (08:30) - 财经市场资讯
- **AI副业早报** (09:00) - AI副业/招聘/赚钱机会

## ⚠️ 铁律（必须严格遵守）

### 时间窗口
- 只采集**过去24小时内**的新闻
- 每篇文章必须核实发布时间
- 超过24小时的必须删除

### 链接要求
- **每条新闻必须带原文链接**：`[原文](url)`
- 链接必须来自**实际浏览**，禁止猜测
- V2EX帖子**必须先打开帖子验证内容**，不能只看标题列表
- 发布前必须**逐条打开链接验证**

### 数据源要求
- AI新闻早报：至少6个来源（36kr + 量子位 + 机器之心 + FT中文网 + Hacker News）
- 经济财经早报：华尔街见闻 + 金十数据 + 新浪财经
- AI副业早报：V2EX + Reddit + 微信公众号(量子位/机器之心)

## 输出路径

```
GitHub: ~/.openclaw/workspace/GitHub/text-matrix/content/posts/news/
飞书: 对应的早报文档
```

## 通用格式

```markdown
---
title: "XXX早报 YYYY-MM-DD"
date: YYYY-MM-DDTHH:MM:SS+08:00
slug: xxx-morning-yyyy-mm-dd
categories: ["行业快讯"]
tags: ["标签1", "标签2"]
description: "YYYY年MM月DD日XXX早报，..."
---

# XXX早报 YYYY-MM-DD

🦞 每日HH:00自动更新

---

## 分类名称

### 文章标题

来源: 来源名称
发布者: xxx
原文: [原文](url)
摘要: 2-3句描述

标签: #标签1 #标签2

---

🦞 每日HH:00自动更新

**数据来源**：来源1、来源2
```

## 工作流程

### 1. 采集数据（07:30前必须开始）

1. 打开浏览器，访问各数据源
2. 采集过去24小时内的新闻
3. **逐条打开文章，记录原文链接**

### 2. 写作

1. 按分类整理新闻
2. 每条新闻必须包含：
   - 标题
   - 2-3句实质性描述
   - 原文链接 `[原文](url)`
   - 标签

### 3. 自检

- [ ] 时间窗口：全部是24小时内
- [ ] 链接格式：`[原文](url)` 正确
- [ ] 逐条打开链接验证可访问
- [ ] V2EX帖子：必须打开帖子页面验证内容
- [ ] 数据源：使用多个来源

### 4. Hugo Frontmatter 生成（必须执行）

在写作完成后、GitHub push之前，**必须**调用 `hugo-writer` skill 来生成标准的 Hugo Frontmatter。

执行步骤：
1. 调用 `hugo-writer` skill
2. 输入当前文章的内容和标题
3. 获取标准化的 frontmatter YAML
4. 将 frontmatter 添加到文章顶部

**⚠️ 严禁手动编写 frontmatter**，必须使用 `hugo-writer` skill 生成！

### 5. 发布

1. GitHub push
2. 创建/更新飞书文档
3. **检查push是否成功**（如果失败，执行 `git pull --rebase && git push`）
4. 更新对应飞书文档

## 参考资料

- [AI新闻数据源](references/ai-news-sources.md)
- [经济财经数据源](references/finance-sources.md)
- [AI副业数据源](references/side-hustle-sources.md)
