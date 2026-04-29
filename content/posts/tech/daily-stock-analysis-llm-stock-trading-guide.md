---
title: "32k星股票智能分析系统：一键生成「AI决策仪表盘」，支持A股/港股/美股"
date: 2026-04-30T03:05:00+08:00
slug: "daily-stock-analysis-llm-stock-trading-guide"
description: "ZhuLinsen/daily_stock_analysis 是一个基于大模型的股票智能分析系统，支持A股/港股/美股多市场，通过GitHub Actions零成本定时运行，自动推送包含买卖点位、风险警报和操作检查清单的决策仪表盘。"
draft: false
categories: ["技术笔记"]
tags: ["股票", "AI", "量化交易", "Python", "Agent", "RAG"]
---

## 项目概览

[ZhuLinsen/daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis) 是一款开源的 LLM 驱动股票分析系统，GitHub 星标 32,634，Fork 数达 32,889（超过星数说明项目传播力极强）。项目支持 A股、港股、美股三大市场的智能分析，每日自动生成「AI 决策仪表盘」，推送至企业微信、飞书、Telegram、Discord、Slack、邮件等主流渠道。

核心能力一句话总结：**输入自选股代码，输出包含评分、买卖点位、风险警报、操作检查清单的决策建议，全流程零成本自动化**。

---

## 核心功能

### AI 决策仪表盘

系统的核心输出是一份结构化的决策仪表盘，包含：

- **综合评分**：0-100 分，量化当前走势强弱
- **买卖点位**：明确的多空边界与入场/离场参考价
- **风险警报**：列举 2-3 个当前最需要关注的风险因素
- **操作检查清单**：每个持仓对应的行动建议

示例输出：
```
🎯 2026-02-08 决策仪表盘
共分析3只股票 | 🟢买入:0 🟡观望:2 🔴卖出:1

⚪ 中钨高新 (000657): 观望 | 评分 65 | 看多
  🚨 风险警报:
  - 2月5日主力资金大幅净卖出3.63亿元
  - 筹码集中度35.15%，拉升阻力可能较大
  ✨ 利好催化:
  - 被定位为AI服务器HDI核心供应商
  - 2025前三季度扣非净利润同比+407.52%
```

### 多维度分析引擎

系统对每只股票从以下维度进行聚合分析：

| 维度 | 说明 |
|------|------|
| 技术面 | 均线、趋势线、K 线形态、量价关系 |
| 实时行情 | 当前价格、涨跌幅、成交量、换手率 |
| 筹码分布 | 持仓成本集中度、主力动向 |
| 新闻舆情 | 基于 SerpAPI/Anspire/Tavily 等搜索 API 抓取的最新资讯 |
| 公告 | 上市公司披露的重大事项 |
| 资金流 | 主力/散户资金净流入/流出 |
| 基本面 | 财务数据、估值指标、业绩预期 |

### 市场策略系统

内置 11 种技术分析策略，覆盖不同市场的交易者风格：

- **A股复盘**：基于 A 股特有的涨跌停、T+1 制度设计
- **美股 Regime**：基于市场状态（牛市/熊市/震荡）切换策略
- **均线策略**：MA、EMA、金叉死叉
- **缠论**：基于缠中说禅理论的走势结构分析
- **波浪理论**：Elliott Wave 计数
- **情绪周期**：基于市场情绪指标的逆向操作

### 大盘复盘

每日收盘后自动生成大盘复盘报告，包含：

- 主要指数表现（上证、深证、创业板、恒生、纳指等）
- 涨跌统计（上涨/下跌/涨停/跌停家数）
- 板块强弱排名（领涨/领跌板块）
- 情绪指标

### Agent 策略问股

提供多轮对话式 "Agent 问股" 能力，支持：

- 用自然语言询问具体股票的走势判断
- 调用内置 11 种策略进行分析（均线金叉、缠论、波浪等）
- 实时查询行情、K 线、技术指标
- 多轮追问、会话导出、发送到通知渠道

### 多渠道推送

支持以下通知渠道，按需配置：

- 企业微信机器人
- 飞书机器人
- Telegram Bot
- Discord Webhook
- Slack Bot
- 邮件（SMTP）

---

## 技术架构

### 整体架构

项目采用微服务架构，核心模块：

```
daily_stock_analysis/
├── main.py              # 入口，支持 CLI + WebUI
├── analyzer_service.py   # 分析引擎
├── server.py            # FastAPI 服务（WebUI + REST API）
├── webui.py             # Gradio/Streamlit Web 界面
├── bot/                 # Telegram Bot 等渠道接入
├── api/                 # REST API 层
├── src/                 # 核心业务逻辑
├── strategies/          # 11 种内置策略实现
├── data_provider/       # 多数据源适配层
├── templates/           # 推送模板
├── scripts/             # 定时任务脚本
└── docs/                # 完整配置指南
```

### 数据源架构

系统设计了完整的数据源优先级和降级机制：

**行情数据源**（优先级从高到低）：
TickFlow → AkShare → Tushare → Pytdx → Baostock → YFinance → Longbridge

**搜索/舆情数据源**：
Anspire → SerpAPI → Tavily → Bocha → Brave → MiniMax → SearXNG

**AI 模型支持**：
AIHubMix（一 Key 访问全系主流模型，含免费额度）→ Gemini → OpenAI 兼容 → DeepSeek → 通义千问 → Claude → Ollama（本地）

### 零成本部署方案

项目最独特的设计是通过 GitHub Actions 实现真正的零成本自动化：

1. Fork 仓库
2. 配置 Secrets（API Key、自选股列表）
3. 启用 Actions
4. 每日 18:00（北京时间）自动运行，默认只在交易日执行

GitHub Actions 运行费用为零，开发者只需承担 API 调用成本（项目推荐 AIHubMix，含免费模型）。

---

## 快速开始

### 方式一：GitHub Actions（推荐，零成本）

**Step 1: Fork 仓库**

点击 [github.com/ZhuLinsen/daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis) 右上角 Fork。

**Step 2: 配置 Secrets**

进入 `Settings → Secrets and variables → Actions`，添加以下必填 Secret：

| Secret 名称 | 示例值 | 说明 |
|------------|--------|------|
| `STOCK_LIST` | `600519,hk00700,AAPL,TSLA` | 自选股代码 |
| `AIHUBMIX_KEY` | `sk-xxxx` | AIHubMix API Key（推荐，含免费模型） |
| `FEISHU_WEBHOOK_URL` | `https://open.feishu.cn/...` | 飞书机器人 Webhook |

**Step 3: 启用 Actions**

进入 `Actions` 标签页，点击 `I understand my workflows, go ahead and enable them`。

**Step 4: 手动测试**

`Actions → 每日股票分析 → Run workflow → Run workflow`

完成后，每个工作日 18:00 会自动推送分析结果到飞书/企业微信等渠道。

### 方式二：本地运行

```bash
# 克隆项目
git clone https://github.com/ZhuLinsen/daily_stock_analysis.git
cd daily_stock_analysis

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key

# 运行分析
python main.py

# 启动 Web 界面
python main.py --webui
# 访问 http://127.0.0.1:8000
```

---

## 适用场景

| 场景 | 适用性 | 说明 |
|------|--------|------|
| 工作日盯盘但时间有限 | ⭐⭐⭐⭐⭐ | 每日 18:00 自动推送持仓诊断，无需手动复盘 |
| 多市场投资者（A股+港股+美股） | ⭐⭐⭐⭐⭐ | 一个系统覆盖三大市场，统一格式输出 |
| 量化交易者 | ⭐⭐⭐⭐ | 11 种内置策略 + 回测验证，可作为策略验证工具 |
| 消息面驱动交易者 | ⭐⭐⭐⭐ | 新闻舆情、公告监控、事件催化捕捉 |
| 轻量级量化研究 | ⭐⭐⭐⭐ | 零成本 GitHub Actions + 免费模型，适合个人投资者 |

---

## 优势与边界

### 核心优势

1. **零成本自动化**：GitHub Actions 覆盖每日定时运行，无服务器费用
2. **多市场统一**：A/H/US 三个市场用同一套框架分析，输出格式一致
3. **多渠道推送**：覆盖主流工作/社交平台，决策后立即触达
4. **策略丰富**：11 种内置策略满足不同分析风格需求
5. **数据源解耦**：多数据源优先级机制，单一数据源故障不影响整体运行

### 明确边界

- 系统输出为 **参考建议**，不构成投资建议，决策权仍在投资者手中
- 分析质量依赖 AI 模型的能力，选择更强的模型（如 Claude/GPT）效果更好
- 港股/美股的基本面数据覆盖不如 A 股完善，建议结合其他信息源
- GitHub Actions 在非交易日默认不运行，节假日需注意

---

## 总结

ZhuLinsen/daily_stock_analysis 是目前开源社区最完整的个人股票分析工具之一。32k+ 的星标和超过星数的 Fork 量说明了它的实用价值。

核心价值在于：**把 LLM 的推理能力转化为每日的、可执行的股票分析输出**，而不是让用户自己写 Prompt、调 API、格式化结果。

如果你在交易日需要一套低成本的每日持仓诊断工具，或者需要一个可以扩展的量化研究框架，这个项目值得重点关注。

- **仓库**：[github.com/ZhuLinsen/daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis)
- **完整文档**：[docs/full-guide.md](https://github.com/ZhuLinsen/daily_stock_analysis/blob/main/docs/full-guide.md)
- **Star**：32,634 ⭐
