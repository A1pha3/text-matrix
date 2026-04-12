---
title: "股票智能分析系统：A股/港股/美股 AI 驱动量化投资平台"
date: 2026-04-08T11:30:00+08:00
slug: daily-stock-analysis-ai-quantitative-investment
aliases:
  - /posts/tech/daily-stock-analysis-ai-quantitative-investment/
categories: ["技术笔记"]
tags: ["量化投资", "AI", "股票分析", "LiteLLM", "Python", "GitHub Actions"]
description: "详解 daily_stock_analysis：一个基于 AI 大模型的 A股/港股/美股智能分析系统，支持多渠道推送、内置交易策略、零成本 GitHub Actions 运行。"
---

> **目标读者**：想了解如何用 AI 构建量化投资系统的开发者、个人投资者
> **核心问题**：如何用大模型技术构建一个完整的股票分析、决策与自动推送系统？
> **难度**：⭐⭐⭐⭐（专家设计）
> **预计阅读时间**：40 分钟

---

## §0 三分钟速览

如果你现在只想快速判断这个项目值不值得深入，先记住下面 4 点：

1. **daily_stock_analysis 是一个基于 AI 大模型的 A股/港股/美股智能分析系统，通过 GitHub Actions 实现零成本定时推送，而非开箱即用的实盘策略。**
2. **它最适合的场景是个人投资者的研究辅助和决策参考，而不是机构级量化交易系统。**
3. **核心优势在于多渠道推送、多市场覆盖、内置交易纪律，以及极低的运行成本。**
4. **AI 分析仅供参考，不构成投资建议，这是所有类似工具都必须明确的边界。**

如果你带着不同目标阅读，可以直接按下面的顺序跳读：

| 你的目标 | 建议优先阅读 |
| ---- | ---- |
| 先判断项目边界是否靠谱 | §1、§2、§7 |
| 想快速上手体验 | §3、§4、§5 |
| 想从架构和源码切入 | §2、§6 |
| 想评估是否适合二次开发 | §2、§6、§8 |

---

## §1 阅读目标

读完本文后，你应该能够：

- 准确理解 daily_stock_analysis 的定位和边界。
- 理解它当前已经公开实现的核心功能。
- 完成从安装配置到定时推送的基本流程。
- 看懂系统的多渠道推送、多市场覆盖、策略系统等核心能力。
- 判断这个项目是否适合你的需求。

---

## §2 项目概述

### 2.1 什么是 daily_stock_analysis

**daily_stock_analysis**（股票智能分析系统）是一个基于 AI 大模型的 A股/港股/美股自选股智能分析系统，每日自动分析并推送「决策仪表盘」到企业微信、飞书、Telegram 等渠道。

**它解决的核心问题是**：

| 痛点 | 系统能力 |
|------|---------|
| 信息碎片化 | 统一数据层（AkShare + Tushare + YFinance） |
| 分析主观性 | AI 客观分析 + 内置交易纪律 |
| 跟踪困难 | GitHub Actions 定时推送 |
| 执行繁琐 | 多渠道统一推送（企业微信/飞书/Telegram） |

### 2.2 关键数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | 26.8k |
| GitHub Forks | 27.6k |
| 提交数 | 480 |
| 分支数 | 67 |
| 许可证 | MIT |
| Python 版本 | 3.10+ |

### 2.3 核心能力

| 能力 | 说明 |
|------|------|
| **AI 决策仪表盘** | 一句话核心结论 + 精确买卖点位 + 操作检查清单 |
| **多维度分析** | 技术面（盘中实时 MA/多头排列）+ 筹码分布 + 舆情情报 + 实时行情 |
| **全球市场** | 支持 A股、港股、美股及美股指数（SPX、DJI、IXIC 等） |
| **策略系统** | 内置 A股「三段式复盘策略」与美股「Regime Strategy」 |
| **自动化推送** | GitHub Actions 定时执行，零成本无需服务器 |

### 2.4 这篇文章适合谁读

| 读者类型 | 是否适合 | 原因 |
| ---- | ---- | ---- |
| 个人投资者 | 适合 | 有量化分析需求，想学习思路 |
| 量化开发者 | 适合 | 有完整的数据层、AI 层、策略层架构 |
| 技术开发者 | 适合 | 可以二次开发，扩展数据源和渠道 |
| 寻找实盘系统的人 | 不适合 | 系统定位为研究辅助，非实盘执行 |

---

## §3 先建立边界：哪些是事实，哪些需要谨慎

### 3.1 当前可确认的已实现能力

| 能力 | 当前状态 | 说明 |
|------|---------|------|
| 多市场数据获取 | ✅ 已实现 | AkShare/Tushare/YFinance |
| AI 分析决策 | ✅ 已实现 | LiteLLM 统一接口 |
| 多渠道推送 | ✅ 已实现 | 企业微信/飞书/Telegram/Discord/邮件 |
| 内置策略 | ✅ 已实现 | 三段式复盘/Regime Strategy |
| GitHub Actions 定时 | ✅ 已实现 | 零成本运行 |
| Web 工作台 | ✅ 已实现 | Web 界面 |

### 3.2 需要特别注意的事项

| 注意事项 | 说明 |
|---------|------|
| **AI 分析仅供参考** | 不构成投资建议 |
| **需要配置 API Key** | AI 模型和数据源需要配置 |
| **GitHub Actions 有频率限制** | 免费计划每月 2000 分钟 |
| **数据质量依赖第三方** | AkShare/Tushare 等数据可能有延迟 |

### 3.3 为什么这个边界必须写清楚

金融工具和普通效率工具不同。用户不仅关心"能不能跑"，还关心：

- 这个分析结果是否可作为决策依据。
- 这个策略是否经过充分回测。
- 这个系统是否有实盘执行能力。

daily_stock_analysis 明确是一个**研究辅助工具**，不是实盘系统，这一点必须在文档中反复强调。

---

## §4 系统架构

### 4.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         daily_stock_analysis 系统架构                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐      │
│  │    数据层        │     │    搜索层        │     │    AI 层        │      │
│  │                 │     │                 │     │                 │      │
│  │  AkShare        │     │  Tavily 新闻     │     │  LiteLLM        │      │
│  │  Tushare        │     │  SerpAPI        │     │  Agent 决策引擎  │      │
│  │  YFinance       │     │  Bocha          │     │  策略系统       │      │
│  │  Baostock       │     │  MiniMax        │     │                 │      │
│  └────────┬────────┘     └────────┬────────┘     └────────┬────────┘      │
│           │                        │                        │                │
│           └────────────────────────┼────────────────────────┘                │
│                                    │                                         │
│                                    ▼                                         │
│                        ┌─────────────────┐                                   │
│                        │    推送层        │                                   │
│                        │                 │                                   │
│                        │  企业微信        │                                   │
│                        │  飞书           │                                   │
│                        │  Telegram       │                                   │
│                        │  Discord        │                                   │
│                        │  邮件           │                                   │
│                        └────────┬────────┘                                   │
│                                 │                                            │
│                                 ▼                                            │
│                        ┌─────────────────┐                                   │
│                        │    界面层        │                                   │
│                        │                 │                                   │
│                        │  Web 工作台      │                                   │
│                        │  Bot 问股       │                                   │
│                        │  API 接口       │                                   │
│                        └─────────────────┘                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 目录结构

```
daily_stock_analysis/
├── api/                    # API 模块
│   ├── stock_api.py        # 股票数据 API
│   └── fundamental_api.py # 基本面 API
├── apps/                   # 应用模块
│   ├── analyzer.py         # 分析器
│   └── reporter.py         # 报告生成
├── bot/                     # Bot 模块
│   ├── telegram_bot.py     # Telegram Bot
│   ├── feishu_bot.py       # 飞书 Bot
│   └── webhook.py          # Webhook 接收
├── data_provider/           # 数据提供器
│   ├── akshare_provider.py # AkShare 数据
│   ├── tushare_provider.py # Tushare 数据
│   └── yfinance_provider.py# YFinance 数据
├── docker/                  # Docker 配置
├── scripts/                  # 脚本工具
├── src/                      # 核心源码
│   ├── analyzer_service.py # 分析服务
│   ├── main.py             # 入口文件
│   └── webui.py            # Web 界面
├── strategies/               # 策略模块
│   ├── a_share_strategy.py # A股策略
│   └── us_strategy.py      # 美股策略
├── templates/                # 报告模板
├── tests/                    # 测试
├── docs/                     # 文档
├── AGENTS.md                # Agent 定义
├── CLAUDE.md                # Claude 配置
└── README.md                # 项目说明
```

### 4.3 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| **数据层** | AkShare/Tushare/YFinance | 多源行情数据 |
| **搜索层** | Tavily/SerpAPI/Bocha | 新闻和舆情数据 |
| **AI 层** | LiteLLM | 统一模型接口 |
| **推送层** | 企业微信/飞书/Telegram | 多渠道通知 |
| **界面层** | Web 工作台/Bot | 用户交互 |
| **自动化** | GitHub Actions | 零成本定时任务 |

---

## §5 核心模块详解

### 5.1 数据层：多源行情数据

系统统一通过 AkShare、Tushare、YFinance 获取行情数据，支持 A股、港股、美股：

| 数据源 | 覆盖市场 | 特点 |
|--------|----------|------|
| AkShare | A股、港股 | 免费开源，数据全面 |
| Tushare | A股 | 专业级数据，需注册 |
| YFinance | 美股 | Yahoo 官方，实时性强 |
| Baostock | A股 | 专注基本面数据 |
| Pytdx | A股 | 直连交易所，低延迟 |

### 5.2 AI 层：LiteLLM 统一接口

系统通过 LiteLLM 封装所有 AI 模型，支持统一调用和负载均衡：

| 模型类别 | 支持的模型 |
|---------|-----------|
| OpenAI | GPT-4, GPT-3.5-turbo |
| Anthropic | Claude-3-opus, Claude-3-sonnet |
| Google | Gemini-pro |
| DeepSeek | DeepSeek-chat |
| 阿里 | 通义千问 |
| Mistral | Mistral-medium |

### 5.3 决策仪表盘：AI 生成投资建议

核心输出格式，包含三个部分：

```markdown
## 📈 贵州茅台（600519）分析

### 💡 一句话结论
**多头趋势延续，短期回调是买入机会，目标价 1850 元**

### 🎯 决策点位
| 类型 | 价格 | 理由 |
|------|------|------|
| 买入价 | 1750 | MA5 支撑位 |
| 止损价 | 1700 | MA10 跌破 |
| 目标价 | 1850 | 前高压力位 |

### ✅ 操作检查清单
- [x] MA5 > MA10 > MA20 多头排列 ✓
- [x] 乖离率 3.2% < 5% 阈值 ✓
- [x] 成交量放大 20% ✓
- [ ] 北向资金净流入（需确认）
```

### 5.4 策略系统：内置交易纪律

#### A股「三段式复盘策略」

```python
class AShareThreeStageStrategy:
    """
    A股三段式复盘策略

    原理：
    1. 趋势判断：MA 多头排列确认方向
    2. 位置评估：乖离率判断贵贱
    3. 仓位决策：综合给出买入/持有/卖出建议
    """
```

#### 内置交易纪律

| 规则 | 说明 | 可配置 |
|------|------|--------|
| 严禁追高 | 乖离率超 5% 提示风险 | ✅ |
| 趋势交易 | MA5 > MA10 > MA20 多头排列 | ✅ |
| 精确点位 | 买入价、止损价、目标价 | ✅ |
| 检查清单 | 每项条件「满足/注意/不满足」 | ✅ |
| 新闻时效 | 默认 3 天内新闻 | ✅ |

### 5.5 推送系统：多渠道通知

支持 8 大推送渠道：

| 渠道 | 说明 |
|------|------|
| 企业微信 | 群机器人 Webhook |
| 飞书 | 自定义机器人 |
| Telegram | Bot 推送 |
| Discord | Webhook |
| 邮件 | SMTP 发送 |

---

## §6 安装与配置

### 6.1 GitHub Actions 部署（推荐，零成本）

#### 步骤 1：Fork 本仓库

点击 GitHub 右上角 **Fork** 按钮

#### 步骤 2：配置 Secrets

进入 `Settings → Secrets and variables → Actions → New repository secret`：

| Secret 名称 | 说明 | 必填 |
|-------------|------|------|
| `AIHUBMIX_KEY` | AIHubMix API Key（推荐，一 Key 用全系模型） | 至少配置一个 |
| `GEMINI_API_KEY` | Google AI Studio Key | 可选 |
| `ANTHROPIC_API_KEY` | Anthropic Claude Key | 可选 |
| `TUSHARE_TOKEN` | Tushare 数据 Token | 可选 |

#### 步骤 3：启用定时任务

编辑 `.github/workflows/schedule.yml`：

```yaml
on:
  schedule:
    - cron: '0 9 * * 1-5'  # 周一至周五 09:00 执行
  workflow_dispatch:           # 支持手动触发
```

#### 步骤 4：查看推送

每天 09:00（北京时间）自动分析并推送到配置的通知渠道。

### 6.2 本地运行

```bash
# 克隆仓库
git clone https://github.com/ZhuLinsen/daily_stock_analysis.git
cd daily_stock_analysis

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key

# 运行分析
python main.py --stock 600519 --market cn
```

---

## §7 LLM 配置详解

### 7.1 配置方式对比

| 方式 | 说明 | 适用场景 |
|------|------|---------|
| 方式 1：简单模式 | 单个 API Key | 快速体验 |
| 方式 2：多模型回退 | fallback 机制 | 提高稳定性 |
| 方式 3：多渠道负载均衡 | 高级配置 | 生产环境 |

### 7.2 方式 1：简单模式

```bash
# .env 文件
AIHUBMIX_KEY=your-key-here
```

### 7.3 方式 2：多模型回退

```bash
LITELLM_MODEL=gpt-4
LITELLM_FALLBACK_MODELS=gpt-3.5-turbo,claude-3-haiku
```

### 7.4 方式 3：多渠道负载均衡

```bash
# 渠道 1
LLM_CHANNELS=openai,anthropic
LLM_OPENAI_PROTOCOL=https://api.openai.com/v1
LLM_OPENAI_API_KEY=sk-xxx
LLM_OPENAI_MODELS=gpt-4,gpt-3.5-turbo
LLM_OPENAI_ENABLED=true

# 渠道 2
LLM_ANTHROPIC_PROTOCOL=https://api.anthropic.com
LLM_ANTHROPIC_API_KEY=sk-ant-xxx
LLM_ANTHROPIC_MODELS=claude-3-opus,claude-3-sonnet
LLM_ANTHROPIC_ENABLED=true
```

---

## §8 与类似项目对比

| 功能 | daily_stock_analysis | QuantConnect | 聚宽 |
|------|---------------------|--------------|------|
| AI 驱动 | ✅ GPT/Claude/Gemini | ❌ | ❌ |
| 中文优化 | ✅ 深度优化 | ❌ | ✅ |
| 零服务器 | ✅ GitHub Actions | ❌ | ❌ |
| 多渠道推送 | ✅ 8 大渠道 | ❌ | ❌ |
| 内置策略 | ✅ 三段式/Regime | ✅ | ✅ |
| 成本 | 免费 | 免费/付费 | 付费 |

---

## §9 风险提示

> **重要声明**：
> 本系统仅供学习研究，**不构成投资建议**。

| 风险类型 | 说明 |
|---------|------|
| AI 预测不确定性 | AI 模型的预测存在不确定性 |
| 数据质量 | 依赖第三方数据源的准确性和时效性 |
| 市场风险 | 交易表现可能因多种因素而异 |
| 策略风险 | 量化策略有风险，过往业绩不代表未来表现 |

**底线建议**：

- 本系统仅作为研究工具使用。
- 不要用于真实交易决策。
- 投资有风险，决策需谨慎。
- 系统默认配置适合学习，实盘使用请充分测试。

---

## §10 常见问题

### Q1: 推送没收到？

检查以下几点：
1. GitHub Actions 是否成功运行（查看 Actions 日志）
2. Secrets 配置是否正确
3. Webhook URL 是否有效
4. 通知渠道是否正常（如企业微信群是否满员）

### Q2: 分析结果不准确？

AI 分析仅供参考：
1. AI 模型能力有限，请勿作为唯一决策依据
2. 可以调整 `temperature` 参数改变创造性
3. 建议结合自身判断使用

### Q3: 如何添加自选股？

编辑 `config/stocks.yml`：

```yaml
a_stock:
  - code: 600519
    name: 贵州茅台
  - code: 000858
    name: 五粮液

us_stock:
  - code: AAPL
    name: Apple
  - code: TSLA
    name: Tesla
```

---

## §11 总结

如果要用一句话概括 daily_stock_analysis，我会这样定义：

**它是一个基于 AI 的股票智能分析系统，通过多渠道定时推送帮助个人投资者跟踪市场，定位为研究辅助工具，而非实盘交易系统。**

它的优势在于：

- 零成本运行（GitHub Actions）
- 多渠道实时推送
- 内置交易纪律，避免情绪化决策
- 支持 A股、港股、美股
- 活跃社区，持续更新

它的边界也同样明确：

- AI 分析仅供参考，不构成投资建议
- 需要一定技术基础配置
- 实盘使用需充分回测验证
- GitHub Actions 有免费额度限制

适合 **有技术背景的投资者** 学习量化分析思路，或作为 **个人投资管理工具** 辅助决策。

---

## 资源链接

- **GitHub 仓库**：https://github.com/ZhuLinsen/daily_stock_analysis
- **完整指南**：https://github.com/ZhuLinsen/daily_stock_analysis/blob/main/docs/full-guide.md
- **常见问题**：https://github.com/ZhuLinsen/daily_stock_analysis/blob/main/docs/FAQ.md
- **LLM 配置指南**：https://github.com/ZhuLinsen/daily_stock_analysis/blob/main/docs/LLM_CONFIG_GUIDE.md

---

## 文档元信息

- 难度：⭐⭐⭐⭐
- 类型：技术笔记 / 项目解读
- 更新日期：2026-04-08
- 依据来源：GitHub 仓库 README、公开文档与源码结构
