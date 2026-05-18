---
title: daily_stock_analysis - LLM驱动的A股/港股/美股智能分析系统
date: 2026-05-18
tags:
  - 量化交易
  - 金融科技
  - LLM应用
  - A股
  - 开源
---

# daily_stock_analysis：零成本搭建 LLM 驱动的 A/H/美股智能分析系统

**Stars: 36,812** | **今日: +36,091** | **Python**

GitHub: [ZhuLinsen/daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis)

## 一句话评价

一个用大模型分析 A股/港股/美股的自动化系统，每日自动抓取行情、新闻、公告，经 LLM 生成「AI 决策仪表盘」推送至企业微信/飞书/Telegram/Discord/Slack/邮箱，零成本依赖 GitHub Actions 定时运行。

## 核心功能

### AI 决策报告
每支自选股生成包含以下内容的完整分析报告：
- **核心结论**：涨跌概率、趋势判断一目了然
- **AI 评分**：0-100 综合评分
- **买卖点位**：关键支撑/压力位提示
- **风险警报**：利空信号识别
- **催化因素**：近期影响股价的事件
- **操作检查清单**：结构化的下一步行动指南

### 多市场数据覆盖
| 市场 | 数据类型 |
|------|----------|
| A股 / 港股 / 美股 / ETF | 行情、K线、技术指标、资金流、筹码分布 |
| 财报层面 | 公告、基本面数据 |
| 舆情层面 | 实时新闻、社交媒体情绪 |

### Agent 策略问股
多轮对话式问股，支持 15 种内置策略：均线、缠论、波浪、趋势、热点、事件、成长、预期等，覆盖 Web 界面 / Bot / API 三种交互方式。

### 推送渠道
企业微信 · 飞书 · Telegram · Discord · Slack · 邮箱，自选时间自动推送。

## 技术架构

**AI 模型**：Anspire、AIHubMix、Gemini、OpenAI 兼容、DeepSeek、通义千问、Claude、Ollama 本地模型

**数据源**：AkShare、Tushare、Pytdx、Baostock、YFinance、Longbridge、SerpAPI（百度搜索）、Tavily、Brave Search 等

**部署方式**：
- GitHub Actions（推荐，零成本定时运行）
- Docker 本地部署
- FastAPI 服务自托管

## 快速上手

```bash
# 1. Fork 本仓库
# 2. 在 Settings → Secrets 配置 API Key
# 3. 编辑 config/stocks.yml 添加自选股
# 4. GitHub Actions 自动定时执行
```

配置文件示例：
```yaml
stocks:
  - symbol: 600519  # 茅台
  - symbol: 00700   # 腾讯
  - symbol: AAPL    # 苹果
```

## 亮点

- **零成本**：GitHub Actions 免费额度足够个人使用
- **多数据源聚合**：告别在多个 app 间切换
- **LLM 决策解读**：把原始数据变成可操作的投资建议
- **多渠道推送**：在哪个平台用就推到哪个平台
- **HelloGitHub 推荐项目**，社区活跃

## 为什么今日暴涨 +36k Stars

这个项目恰好踩中了"散户用 AI 炒股"这个在中国开发者圈子里极度热门的需求。36k Stars 单日增长说明它的实用性和传播性极强——不需要昂贵的 Bloomberg 数据，不需要服务器，一键 Fork 就能用。