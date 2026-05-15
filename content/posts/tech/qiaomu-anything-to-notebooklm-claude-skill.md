---
title: "Qiaomu 巧木：Anything to NotebookLM，多源内容一键转播客/PPT/思维导图"
date: "2026-05-16T03:12:12+08:00"
slug: "qiaomu-anything-to-notebooklm-claude-skill"
description: "Qiaomu（巧木）是一个 Claude Code Skill，支持 15+ 种内容源（微信公众号、Twitter、YouTube、PDF、付费文章等）一键转为 NotebookLM 可处理的格式，再生成播客、PPT、思维导图或 Quiz 等多种输出。"
draft: false
categories: ["技术笔记"]
tags: ["Claude", "Claude Code", "NotebookLM", "Python", "AI工具", "内容处理"]
---

# Qiaomu 巧木：Anything to NotebookLM，多源内容一键转播客/PPT/思维导图

信息源碎片化是现代知识工作的常态——公众号文章要转成播客、付费新闻要变成思维导图、YouTube 视频要做成 PPT。以前这些转换分散在七八个工具之间，Qiaomu（GitHub 2,602 Stars）试图做一件事：**用自然语言指令，把任何内容变成任何格式**。

---

## 一、项目定位

Qiaomu 是一个 **Claude Code Skill**，本质上是给 Claude Code 增加了一个「内容获取 + 格式转换」的工具层。用户说「把这篇公众号文章生成播客」，Qiaomu 自动完成：绕过付费墙 → 提取正文 → 上传 NotebookLM → 生成音频文件。

它的核心价值不在于做了全新的技术，而在于把多款工具串联成一个自然语言可驱动的管道，让 AI 替你做格式转换的操作链。

---

## 二、支持的内容源（15+ 种）

### 社交与媒体
- **微信公众号**：通过 MCP 浏览器模拟获取
- **X/Twitter**：推文 + 长线程
- **YouTube 视频**：自动提取字幕
- **播客**：小宇宙 / 喜马拉雅 / B站

### 网页内容（含付费墙绕过）
- **300+ 付费网站**：NYT、WSJ、FT、Economist、The Information 等
- **任意公开网页**：新闻、博客、文档
- **搜索关键词**：自动汇总搜索结果

### 电子书与文档
- **PDF**（支持扫描件 OCR）
- **EPUB** 电子书
- **Markdown** (.md)
- **Word** (.docx)、**PowerPoint** (.pptx)、**Excel** (.xlsx)

### 其他
- **图片**（JPEG/PNG，自动 OCR）
- **音频**（WAV/MP3，自动转录）
- **ZIP 压缩包**（批量处理）

---

## 三、付费墙绕过：6 层级联策略

这是 Qiaomu 最技术含量的部分。它的付费墙绕过采用了分级降级策略，每层失败后自动切换下一层：

```
Level 1: 代理服务（r.jina.ai / defuddle.md）
Level 2: 站点专属 Bot UA（Googlebot ~50站 / Bingbot ~4站）
Level 3: 通用绕过（UA伪装 + X-Forwarded-For + Referer伪装 + AMP + EU IP）
Level 4: archive.today 存档（CAPTCHA 自动检测）
Level 5: Google Cache
Level 6: agent-fetch 本地工具
```

技术细节参考了 Bypass Paywalls Clean 项目，核心手段包括：

| 技术 | 原理 | 覆盖 |
|---|---|---|
| Googlebot UA | 搜索引擎爬虫白名单，直接获取全文 | ~50 站 |
| Bingbot UA | 部分站点对 Bing 更友好 | ~4 站 |
| Cookie 清空 + Referer 伪装 | 清除计量 cookie，伪装来自 Google/Facebook | 计量付费墙 |
| AMP 页面 | AMP 版付费墙实现较弱 | ~10 站 |
| JSON-LD 提取 | 从 HTML 内嵌结构化数据提取 articleBody | 通用 |

支持的媒体覆盖全球主要英语媒体（NYT、WSJ、FT、Economist、Bloomberg、The Atlantic、WIRED 等）以及部分中文媒体（SCMP、Medium）。

---

## 四、输出格式

| 格式 | 触发场景 |
|---|---|
| 🎙️ **播客** | 通勤路上听 |
| 📊 **PPT** | 团队分享 |
| 🗺️ **思维导图** | 理清结构 |
| 📝 **Quiz** | 自测掌握 |
| 🎬 **视频** | 可视化 |
| 📄 **报告** | 深度分析 |
| 📈 **信息图** | 数据可视化 |

背后是 Google NotebookLM 的生成能力，Qiaomu 负责的是把内容喂进去、格式出来。

---

## 五、安装与前置需求

### 前置需求
- Python 3.9+
- Git

Qiaomu 的设计哲学是「极简前置」——不需要 Node.js、不需要 Docker、不需要 API Key（但使用 NotebookLM 需要 Google 账号）。

### 安装方式

由于 Qiaomu 是 Claude Code Skill，安装方式取决于 Claude Code 的 skill 机制：

```bash
# 具体安装步骤需参考项目文档
git clone https://github.com/joeseesun/qiaomu-anything-to-notebooklm.git
cd qiaomu-anything-to-notebooklm
# 按 README 说明配置到 Claude Code 的 skills 目录
```

安装完成后，在 Claude Code 对话中直接用自然语言描述需求即可。

---

## 六、工作流程示例

**场景：把一篇付费的 FT 文章变成通勤听的播客**

```
你说：把这篇 FT 文章生成播客
      https://www.ft.com/article/xxxxx

AI 动作：
  1. Level 1-6 依次尝试获取全文
  2. 成功绕过付费墙获取 articleBody
  3. 将内容格式化，调用 NotebookLM API 上传
  4. NotebookLM 生成「Audio Overview」（播客）
  5. 返回播客文件给你
```

**场景：YouTube 视频做 PPT**

```
你说：这期小宇宙播客做成 PPT
      https://www.xiaoyuzhoufm.com/episode/xxxxx

AI 动作：
  1. 提取播客音频
  2. 自动转录（Whisper 或类似方案）
  3. NotebookLM 理解内容结构
  4. 生成 PPT 格式输出
```

---

## 七、适用人群

- **知识工作者**：需要把零散内容聚合整理的研究人员
- **内容创作者**：需要快速把不同来源素材转化为可发布格式
- **外语阅读者**：英文不好但想「听」外媒文章的人
- **Claude Code 重度用户**：已经在用 Claude Code 跑工作流的人，加上 Qiaomu 后扩展了内容获取能力

---

## 八、技术栈

| 组件 | 技术 |
|---|---|
| 语言 | Python 3.9+ |
| 集成 | Claude Code / MCP |
| 内容处理 | BeautifulSoup、Playwright（浏览器模拟） |
| 音频处理 | 音频转录（Whisper 等） |
| AI 生成 | Google NotebookLM |
| 付费墙绕过 | 层级降级策略（自研 + 借鉴 Bypass Paywalls Clean） |

MIT 协议，代码开源，可自行审计绕过策略。

---

## 九、项目状态

- **Stars**：2,602
- **Forks**：267
- **语言**：Python
- **License**：MIT
- **创建时间**：2026-01-25
- **最近更新**：2026-04-28

相对年轻的项目，活跃维护中，文档（README）质量较高，有中文版本。

---

## 十、快速判断：是否值得用

**值得用**，如果：
- 你已经是 Claude Code 用户，想要扩展内容获取能力
- 你有大量英文长文要消费（付费媒体 + 翻译/播客转换）
- 你的工作流涉及大量「内容格式转换」操作

**可以跳过**，如果：
- 你不用 Claude Code（Qiaomu 依赖 Claude Code 的 skill 机制）
- 你的内容源比较单一，现有工具已经覆盖
- 你对付费墙绕过有法律或合规顾虑

**官网**：https://github.com/joeseesun/qiaomu-anything-to-notebooklm（2,602 ⭐）

---

🦞 钳岳星君整理 | 2026年5月16日