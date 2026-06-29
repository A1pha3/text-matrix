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

## 学习目标

阅读本文后，你应该能够：

1. **了解 Qiaomu 项目**：理解其定位、支持的内容源和输出格式
2. **理解付费墙绕过机制**：掌握其 6 层级联策略的原理和应用场景
3. **掌握安装和配置**：能够成功安装 Qiaomu 并配置到 Claude Code
4. **实际应用**：能够使用 Qiaomu 完成内容转换任务（如公众号文章转播客）
5. **评估适用性**：判断 Qiaomu 是否适合你的工作流

## 目录

- [项目定位](#一项目定位)
- [支持的内容源](#二支持的内容源15-种)
- [付费墙绕过](#三付费墙绕过6-层级联策略)
- [输出格式](#四输出格式)
- [安装与前置需求](#五安装与前置需求)
- [工作流程示例](#六工作流程示例)
- [适用人群](#七适用人群)
- [技术栈](#八技术栈)
- [项目状态](#九项目状态)
- [快速判断](#十快速判断是否值得用)
- [常见问题](#常见问题)
- [自测题](#自测题)
- [练习](#练习)
- [进阶路径](#进阶路径)
- [资料口径说明](#资料口径说明)
- [总结](#总结)

信息源碎片化是现代知识工作的常态——公众号文章要转成播客、付费新闻要变成思维导图、YouTube 视频要做成 PPT。以前这些转换分散在七八个工具之间，Qiaomu（GitHub 2,602 Stars）试图做一件事：**用自然语言指令，把任何内容变成任何格式**。

---

## 一、项目定位

Qiaomu 是一个 **Claude Code Skill**，本质上是给 Claude Code 增加了一个「内容获取 + 格式转换」的工具层。用户说「把这篇公众号文章生成播客」，Qiaomu 自动完成：绕过付费墙 → 提取正文 → 上传 NotebookLM → 生成音频文件。

它的关键价值不在于做了全新的技术，而在于把多款工具串联成一个自然语言可驱动的管道，让 AI 替你做格式转换的操作链。

---

## 二、支持的内容源（15+ 种）

### 社交与媒体
- **微信公众号**：通过 MCP 浏览器模拟获取
- **X/Twitter**：推文 + 长线程
- **YouTube 视频**：自动提取字幕
- **播客**：小宇宙 / 喜马拉雅 / B 站

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

## 常见问题

### Q1: Qiaomu 的付费墙绕过是否合法？
这取决于你所在地区的法律和你要访问的网站的服务条款。Qiaomu 项目声明仅用于研究和教育目的。使用前请咨询法律意见。

### Q2: Qiaomu 支持哪些语言的内容？
主要支持英文和中文内容。英文付费媒体（NYT、WSJ 等）的绕过策略较完善；中文媒体支持较少。

### Q3: 使用 Qiaomu 需要付费吗？
Qiaomu 本身是开源免费的，但使用 NotebookLM 需要 Google 账号（免费版有使用限制）。

### Q4: 如果 Qiaomu 无法绕过某个网站的付费墙怎么办？
可以尝试：1. 检查网站是否在 Qiaomu 的支持列表中；2. 手动提取内容然后处理；3. 向 Qiaomu 项目提交 Issue 或 PR。

## 自测题

1. **Qiaomu 的核心价值是什么？**
   <details>
   <summary>查看答案</summary>
   把多款工具串联成一个自然语言可驱动的管道，让 AI 替你做格式转换的操作链。
   </details>

2. **Qiaomu 的付费墙绕过采用什么策略？**
   <details>
   <summary>查看答案</summary>
   6 层级联策略：每层失败后自动切换下一层，从代理服务到本地工具逐级降级。
   </details>

3. **Qiaomu 支持哪些输出格式？**
   <details>
   <summary>查看答案</summary>
   播客、PPT、思维导图、Quiz、视频、报告、信息图等，由 Google NotebookLM 驱动生成。
   </details>

4. **使用 Qiaomu 的前提条件是什么？**
   <details>
   <summary>查看答案</summary>
   1. 已安装 Claude Code；2. 已配置 Qiaomu Skill；3. 有 Google 账号（用于 NotebookLM）。
   </details>

5. **Qiaomu 的技术栈中，付费墙绕过依赖什么技术？**
   <details>
   <summary>查看答案</summary>
   层级降级策略，借鉴 Bypass Paywalls Clean 项目的思路，结合浏览器模拟、UA 伪装、存档服务等多种手段。
   </details>

## 练习

### 练习 1：安装和配置 Qiaomu
**目标**：成功安装 Qiaomu 并配置到 Claude Code。

**步骤**：
1. 克隆 Qiaomu 仓库：`git clone https://github.com/joeseesun/qiaomu-anything-to-notebooklm.git`
2. 按照 README 说明配置到 Claude Code 的 skills 目录
3. 启动 Claude Code 并验证 Qiaomu 是否加载成功

**验证**：在 Claude Code 中输入"帮我处理这篇文章"，看是否能触发 Qiaomu 的辅助提示。

### 练习 2：转换一篇公众号文章为播客
**目标**：使用 Qiaomu 将一篇微信公众号文章转为播客格式。

**步骤**：
1. 找到一篇微信公众号文章（获取链接）
2. 在 Claude Code 中输入："把这篇公众号文章生成播客 [链接]"
3. 等待 Qiaomu 处理（绕过付费墙、提取正文、上传 NotebookLM、生成音频）
4. 下载并收听生成的播客

**反思**：播客质量如何？哪些地方可以改进？

### 练习 3：评估 Qiaomu 对你的工作流的价值
**目标**：基于你的实际工作场景，评估 Qiaomu 是否值得使用。

**步骤**：
1. 列出你日常需要处理的内容类型和格式转换需求
2. 评估 Qiaomu 能否覆盖这些需求
3. 考虑付费墙绕过的法律和合规风险
4. 决定是否采用 Qiaomu

**输出**：一份简短的评估报告（200-300 字）

## 进阶路径

如果你想深入使用和扩展 Qiaomu，可以按照以下路径进阶：

### Level 1：基础使用者 ⭐
- 能够安装和配置 Qiaomu
- 能够使用现有功能完成内容转换
- 能够排查常见问题（如网络连接、API 限制）

### Level 2：高级使用者 ⭐⭐
- 能够自定义内容源支持（修改或新增绕过策略）
- 能够优化付费墙绕过成功率
- 能够调整 NotebookLM 的生成参数

### Level 3：贡献者 ⭐⭐⭐
- 能够理解 Qiaomu 的代码结构
- 能够修复 Bug 和提交 PR
- 能够编写新的内容源支持模块

### Level 4：维护者 ⭐⭐⭐⭐
- 能够维护 Qiaomu 项目
- 能够跟进 Claude Code 和 NotebookLM 的 API 变化
- 能够建立社区和支持文档

## 资料口径说明

本文档基于以下来源编写，请注意其局限性：

1. **信息来源**：主要基于 Qiaomu GitHub 仓库的 README（2026-05-16 访问）。项目相对年轻（创建于 2026-01-25），信息可能快速变化。
2. **付费墙绕过时效性**：付费墙绕过策略可能随时失效，因为网站会持续更新其反爬虫机制。
3. **未实际测试**：本文档未实际测试 Qiaomu 的所有功能。实际使用时可能会遇到文档中未说明的问题。
4. **法律合规性**：付费墙绕过可能涉及法律和合规风险（如违反网站服务条款、版权法等）。使用前请咨询法律意见。
5. **NotebookLM 限制**：NotebookLM 的免费版有使用限制（如生成次数、文件大小、音频长度）。具体限制请查看 Google 官方说明。
6. **更新频率**：Qiaomu 项目活跃维护中，本文档无法实时同步最新状态。

## 总结

Qiaomu 是一个**创新的内容转换工具**，通过把多款工具串联成自然语言可驱动的管道，让 AI 替你做格式转换的操作链。它特别适合已经在使用 Claude Code 的用户，尤其是需要处理大量碎片化内容的知识工作者。

项目相对年轻但活跃维护中，代码开源（MIT 协议），可自行审计绕过策略。如果你有大量的内容格式转换需求，Qiaomu 值得一试。但请注意付费墙绕过的法律和合规风险，并确保仅用于研究和教育目的。

---

🦞 钳岳星君整理 | 2026 年 5 月 16 日