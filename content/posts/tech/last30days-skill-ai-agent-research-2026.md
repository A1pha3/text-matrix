---
title: "GitHub趋势榜新星：last30days-skill 一键搞定全网AI研究"
date: 2026-03-28T12:00:00+08:00
slug: "last30days-skill-ai-agent-research-2026"
description: "last30days-skill是一个AI Agent技能工具，能在Reddit、X、YouTube、Hacker News、Polymarket和整个网络上研究任何主题，然后合成一个基于事实的摘要。今日新增2821 stars，GitHub趋势榜第一。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "GitHub", "Claude", "Agent", "研究工具"]
---

# GitHub趋势榜新星：last30days-skill 一键搞定全网AI研究

**今日新增 2,821 stars，GitHub趋势榜第一。这个工具让AI拥有了「上网冲浪做研究」的能力。**

## 功能特点

last30days-skill 是一个专为 AI Agent 和 Claude Code 设计的**研究技能**。它的核心能力是：

> 输入一个主题，AI 自动去 Reddit、X (Twitter)、YouTube、Hacker News、Polymarket 和整个 Web 抓取相关信息，最终合成一份有理有据的研究摘要。

用大白话说：**你给 AI 一个问题，它自己去全网搜答案，最后给你整理成一份报告**。

## 核心特性

1. **多平台覆盖**：Reddit、X、YouTube、HN、Polymarket、Web
2. **自动合成摘要**：把分散的信息整合成一份结构化报告
3. **Claude Code 原生集成**：可以作为 Claude Code 的 skill 直接调用
4. **开源可定制**：MIT 协议，可自行部署修改

## 技术原理

从代码结构来看，这个 skill 主要包含：

- **平台 API/爬虫适配器**：对接各平台的搜索和数据获取接口
- **信息检索与过滤**：去重、排序、相关性计算
- **LLM 合成层**：调用大模型将原始信息转化为连贯摘要
- **输出格式化**：支持 Markdown、JSON 等多种格式

核心思路是**让 AI Agent 具备「使用工具」的能力**，在Planning阶段就能决定去哪里查、怎么查、查完后怎么整合。

## 使用场景

### 适用人群

- **研究人员**：快速了解某个领域最新动态
- **投资者**：追踪 Web3/AI赛道热点和社区情绪
- **产品经理**：做竞品分析和市场调研
- **开发者**：了解某技术的实际使用反馈

### 使用示例

```bash
# 安装 (需要 Claude Code 环境)
claude code install last30days-skill

# 使用
claude "研究一下最近火热的 AI Agent 框架有哪些"
```

## 为什么爆火？

2026年3月，AI Agent 赛道持续火热。但大部分 Agent 工具还停留在「单点突破」——要么只能聊天，要么只能执行命令。**last30days-skill 的创新在于打通了信息获取的最后一公里**：让 AI 不仅能思考，还能主动去全网检索最新信息再回答。

这解决了 AI 固有的「知识截止日期」问题——**AI 可以实时联网研究新问题了**。

## 快速上手

### 环境要求

- Python 3.10+
- Claude Code 或兼容的 Claude Agent 环境
- 各平台 API Token（部分平台需要）

### 安装步骤

```bash
# 方法1：直接安装
pip install last30days-skill

# 方法2：从源码安装
git clone https://github.com/mvanhorn/last30days-skill
cd last30days-skill
pip install -e .
```

### 配置 API Keys

```bash
export REDDIT_CLIENT_ID="your_reddit_id"
export REDDIT_CLIENT_SECRET="your_reddit_secret"
export TWITTER_BEARER_TOKEN="your_twitter_token"
# ... 其他平台类似
```

### 基本使用

```python
from last30days import ResearchAgent

agent = ResearchAgent()
result = agent.research("AI Agent 编程框架哪家强")
print(result.summary)
```

## 项目信息

| 项目 | 信息 |
|------|------|
| GitHub | [mvanhorn/last30days-skill](https://github.com/mvanhorn/last30days-skill) |
| Stars | 12,886 ⭐ (今日 +2,821) |
| Forks | 1,031 |
| License | MIT |
| 语言 | Python |
| 主要贡献者 | mvanhorn, claude, j-sperling, phjlljp, iliaal |

## 竞争产品对比

| 工具 | 平台覆盖 | 开源 | 今日 Stars |
|------|----------|------|-----------|
| last30days-skill | Reddit/X/YouTube/HN/Polymarket/Web | ✅ | 2,821 |
| Custom GPTs | 有限 | ❌ | N/A |
| Perplexity API | Web only | ❌ | N/A |

## 总结

last30days-skill 代表了一个新趋势：**AI Agent 不仅要能执行任务，还要能自主研究和学习**。它让 AI 拥有了「上网查资料」的能力，这对于需要最新信息的场景（投资决策、市场调研、技术选型等）简直是神器。

如果你在构建 AI 应用或 Agent 系统，这个项目值得研究一下源码，思路很有启发性。

---

*数据来源：GitHub Trending 2026-03-28*
