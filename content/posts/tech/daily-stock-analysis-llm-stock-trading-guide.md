---
title: "daily_stock_analysis：LLM驱动的 A/H/美股智能分析系统"
date: "2026-05-18T19:56:00+08:00"
categories: ["技术笔记"]
tags: ["股票分析", "LLM", "Python", "AI量化", "量化交易", "飞书机器人", "GitHub Actions"]
slug: "daily-stock-analysis-llm-a-h-us-stock-analysis"
description: "一款基于 AI 大模型的 A股/港股/美股自选股智能分析系统，支持多数据源行情、实时新闻、LLM决策仪表盘，以及企业微信/飞书/Telegram/Discord/Slack/邮箱等多渠道推送，零成本 GitHub Actions 定时运行。"
---

在量化投资日益普及的今天，如何高效地将 AI 能力引入个人股票分析？`daily_stock_analysis` 项目给出了答案——一个完全开源、零成本、靠 GitHub Actions 驱动的 LLM 股票智能分析系统。今日斩获约 290 颗星（累计 36,757 ⭐），成为近期最热门的金融 AI 开源项目之一。

<!--more-->

## 核心能力：从行情到决策一站式覆盖

该系统的设计目标是**每日自动分析自选股并推送决策报告**，覆盖A股、港股和美股三大市场。报告内容相当丰富，包括：

- **核心结论与评分**：AI 直接给出多空判断和综合评分
- **趋势判断与买卖点位**：压力位、支撑位、操作建议一应俱全
- **风险警报**：识别潜在黑天鹅事件和流动性风险
- **催化因素追踪**：并购重组、政策利好、业绩预告等事件驱动因子
- **操作检查清单**：明确下一步操作步骤

数据来源覆盖 AkShare、Tushare、Pytdx、Baostock、YFinance、Longbridge 等主流行情库，以及 Anspire、SerpAPI、Tavily、Bocha、Brave Search、MiniMax 等新闻搜索服务。

## 技术架构：Python + 多模型支持

项目基于 **Python 3.10+** 构建，核心技术栈包括：

- **LLM 驱动层**：支持 Anspire、AIHubMix、Google Gemini、OpenAI 兼容 API（含 DeepSeek、通义千问）、Anthropic Claude、Ollama 本地模型等，几乎涵盖了所有主流模型提供商
- **数据层**：AkShare（财经数据）、Tushare（A股）、Pytdx（行情）、Baostock（基本面）、YFinance（美股）
- **推送层**：企业微信机器人、飞书机器人、Telegram Bot、Discord Webhook、Slack Bot、邮件

## 部署方式：5 分钟 GitHub Actions 零成本运行

该项目最大的亮点在于**极低的接入门槛**。只需：

1. Fork 仓库
2. 在 GitHub Secrets 中配置 API Key（LLM + 推送渠道 + 自选股代码）
3. 启用 Actions

即可实现**每个工作日 18:00（北京时间）自动执行**，生成分析报告并推送到指定渠道。默认会跳过非交易日（含 A/H/US 节假日），也支持手动触发和断点续传。

对于不想依赖 GitHub Actions 的用户，项目同样支持本地运行和 Docker 部署，提供完整的 `.env` 配置模板。

## Web 工作台：手动分析与历史回溯

除了自动化推送，项目还提供了功能完备的 **Web/桌面工作台**，支持：

- 手动触发分析，实时查看任务进度
- 历史报告完整 Markdown 导出
- 持仓管理、配置管理
- 浅色/深色主题切换

这个工作台基于 FastAPI 构建，可通过 `python main.py --webui` 直接启动。

## Agent 策略问股：多轮对话式分析

系统中内置了 **15 种分析策略**（均线、缠论、波浪、趋势、热点、事件、成长、预期等），通过 Agent 模块支持多轮追问。用户可以通过 Web/Bot/API 三种方式与系统对话，获取更深度的个股分析。

## 快速上手

```bash
# 克隆项目
git clone https://github.com/ZhuLinsen/daily_stock_analysis.git && cd daily_stock_analysis

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env && vim .env

# 运行分析（示例：分析茅台）
python main.py --stocks 600519
```

## 小结

`daily_stock_analysis` 将 LLM 能力与金融数据深度结合，通过 GitHub Actions 实现了零成本的自动化每日分析。适合有自选股管理需求的个人投资者，尤其是习惯使用飞书/企业微信的国内用户。项目文档详尽，部署门槛低，是近期最值得关注的开源金融 AI 项目之一。

🔗 GitHub：[ZhuLinsen/daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis)