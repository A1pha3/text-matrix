---
title: "股票智能分析系统：A股/港股/美股 AI 驱动量化投资平台"
date: 2026-03-29T22:43:00+08:00
slug: daily-stock-analysis-ai-quantitative-investment
categories: ["技术笔记"]
tags: ["量化投资", "AI", "股票分析", "LiteLLM", "Python"]
description: "详解 daily_stock_analysis：一个基于 AI 大模型的 A股/港股/美股智能分析系统，支持多渠道推送、内置交易策略、零成本 GitHub Actions 运行。"
---

# 股票智能分析系统：A股/港股/美股 AI 驱动量化投资平台 ⭐⭐⭐⭐

> **目标读者**：想了解如何用 AI 构建量化投资系统的开发者、投资者
> **核心问题**：如何用大模型技术构建一个完整的股票分析、决策与自动推送系统？

---

## 🎯 项目概述

**股票智能分析系统**（daily_stock_analysis）是一个基于 AI 大模型的 A股/港股/美股自选股智能分析系统，每日自动分析并推送「决策仪表盘」到企业微信、飞书、Telegram 等渠道。

### 核心数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | 26.8k |
| GitHub Forks | 27.6k |
| 提交数 | 480 |
| 分支数 | 67 |
| 许可证 | MIT |
| Python 版本 | 3.10+ |

### 五大核心能力

1. **AI 决策仪表盘**：一句话核心结论 + 精确买卖点位 + 操作检查清单
2. **多维度分析**：技术面（盘中实时 MA/多头排列）+ 筹码分布 + 舆情情报 + 实时行情
3. **全球市场**：支持 A股、港股、美股及美股指数（SPX、DJI、IXIC 等）
4. **策略系统**：内置 A股「三段式复盘策略」与美股「Regime Strategy」
5. **自动化推送**：GitHub Actions 定时执行，零成本无需服务器

---

## 🧠 为什么需要这个系统？

### 传统股票分析的痛点

| 痛点 | 描述 |
|------|------|
| 信息碎片化 | 行情、基本面、新闻、舆情分散在不同平台 |
| 分析主观性 | 人工分析受情绪影响，难以保持纪律 |
| 跟踪困难 | 无法 24 小时监控，尤其夜间美股 |
| 执行繁琐 | 看盘、分析、下单需要在多个 App 间切换 |

### 系统解决思路

```
用户痛点 ──────────────────────────────────────────────────────► 系统能力
信息碎片化 ──► 统一数据层（AkShare + Tushare + YFinance）
分析主观性 ──► AI 客观分析 + 内置交易纪律
跟踪困难   ──► GitHub Actions 定时推送
执行繁琐   ──► 多渠道统一推送（企业微信/飞书/Telegram）
```

---

## 🏛️ 系统架构

### 整体架构

```mermaid
graph TB
    subgraph 数据层["📊 数据层"]
        AK[AkShare 行情]
        TS[Tushare 数据]
        YF[YFinance 美股]
        BL[Baostock 数据]
        PX[Pytdx 直连]
    end
    
    subgraph 搜索层["🔍 搜索层"]
        TV[Tavily 新闻]
        SC[SerpAPI 搜索]
        BC[Bocha 搜索]
        MX[MiniMax 搜索]
    end
    
    subgraph AI层["🤖 AI 层"]
        LLM[LiteLLM 统一接口]
        AGENT[Agent 决策引擎]
        STRAT[策略系统]
    end
    
    subgraph 推送层["📱 推送层"]
        WX[企业微信]
        FS[飞书]
        TG[Telegram]
        DC[Discord]
        EM[邮件]
    end
    
    subgraph 界面层["🖥️ 界面层"]
        WEB[Web 工作台]
        BOT[Bot 问股]
        API[API 接口]
    end
    
    数据层 ─► AI层
    搜索层 ─► AI层
    AI层 ─► 推送层
    AI层 ─► 界面层
```

### 目录结构

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
│   ├── tushare_provider.py# Tushare 数据
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

---

## 📊 核心模块详解

### 1. 数据层：多源行情数据

系统统一通过 AkShare、Tushare、YFinance 获取行情数据，支持A股、港股、美股：

| 数据源 | 覆盖市场 | 特点 |
|--------|----------|------|
| AkShare | A股、港股 | 免费开源，数据全面 |
| Tushare | A股 | 专业级数据，需注册 |
| YFinance | 美股 | Yahoo 官方，实时性强 |
| Baostock | A股 | 专注基本面数据 |
| Pytdx | A股 | 直连交易所，低延迟 |

**数据获取示例**：

```python
from data_provider.akshare_provider import AkShareProvider

provider = AkShareProvider()
# 获取A股实时行情
df = provider.realtime_quote("000001")
# 获取历史 K 线
kline = provider.historical_data("000001", start="2024-01-01")
```

### 2. AI 层：LiteLLM 统一接口

系统通过 LiteLLM 封装所有 AI 模型，支持统一调用和负载均衡：

```python
from litellm import completion

# 配置多模型渠道
model_config = {
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "分析贵州茅台走势"}],
    "temperature": 0.7
}

# 支持的模型列表
models = [
    "gpt-4", "gpt-3.5-turbo",           # OpenAI
    "claude-3-opus", "claude-3-sonnet",   # Anthropic
    "gemini-pro",                           # Google
    "deepseek-chat",                        # DeepSeek
    "qwen-turbo",                          # 阿里通义
    "mistral-medium",                       # Mistral
]
```

### 3. 决策仪表盘：AI 生成投资建议

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

### 4. 策略系统：内置交易纪律

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
    
    def evaluate(self, stock_code: str) -> StrategyResult:
        # 阶段 1：趋势判断
        trend = self.check_trend(stock_code)  # MA5 > MA10 > MA20
        
        # 阶段 2：位置评估
        deviation = self.calc_deviation(stock_code)  # 当前价偏离 MA5 的百分比
        
        # 阶段 3：综合决策
        if trend.bullish and deviation < 5:
            return StrategyResult(action=ACTION.BUY, confidence=0.85)
        elif trend.bullish and deviation > 8:
            return StrategyResult(action=ACTION.HOLD, confidence=0.60)
        else:
            return StrategyResult(action=ACTION.WAIT, confidence=0.50)
```

#### 内置交易纪律

| 规则 | 说明 | 可配置 |
|------|------|--------|
| 严禁追高 | 乖离率超 5% 提示风险 | ✅ |
| 趋势交易 | MA5 > MA10 > MA20 多头排列 | ✅ |
| 精确点位 | 买入价、止损价、目标价 | ✅ |
| 检查清单 | 每项条件「满足/注意/不满足」 | ✅ |
| 新闻时效 | 默认 3 天内新闻 | ✅ |

### 5. 推送系统：多渠道通知

支持 8 大推送渠道：

```python
from bot.notifier import Notifier

notifier = Notifier()

# 企业微信
notifier.send_wechat(
    title="📈 每日股票分析",
    content=report_content,
    webhook_url=WEBHOOK_URL
)

# 飞书
notifier.send_feishu(
    content=report_content,
    webhook_url=FEISHU_WEBHOOK
)

# Telegram
notifier.send_telegram(
    text=report_content,
    chat_id=CHAT_ID,
    bot_token=BOT_TOKEN
)
```

---

## 🚀 快速开始

### 方式一：GitHub Actions（推荐，零成本）

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

### 方式二：本地运行

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

## 🔧 配置详解

### LLM 配置（支持三种方式）

#### 方式 1：简单模式（单个 Key）

```bash
# .env 文件
AIHUBMIX_KEY=your-key-here
```

#### 方式 2：多模型回退

```bash
LITELLM_MODEL=gpt-4
LITELLM_FALLBACK_MODELS=gpt-3.5-turbo,claude-3-haiku
```

#### 方式 3：多渠道负载均衡（高级）

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

## 📱 推送渠道配置

### 企业微信

1. 在企业微信群添加「群机器人」
2. 复制 Webhook URL
3. 配置为 `WECOM_WEBHOOK` Secret

### 飞书

1. 在飞书群添加「自定义机器人」
2. 复制 Webhook URL
3. 配置为 `FEISHU_WEBHOOK` Secret

### Telegram

1. 创建 Bot（@BotFather）
2. 获取 Bot Token
3. 配置为 `TG_BOT_TOKEN` 和 `TG_CHAT_ID`

---

## 📊 界面展示

### Web 工作台

系统提供完整的 Web 界面，支持：

- **首页**：自选股仪表盘
- **问股**：对话式股票分析
- **回测**：历史准确率分析
- **持仓**：管理模拟/实盘持仓
- **设置**：API Key、通知渠道配置

### 主题切换

支持浅色/深色主题一键切换，移动端适配。

---

## 🔄 与类似项目对比

| 功能 | daily_stock_analysis | QuantConnect |聚宽 |
|------|---------------------|--------------|------|
| AI 驱动 | ✅ GPT/Claude/Gemini | ❌ | ❌ |
| 中文优化 | ✅ 深度优化 | ❌ | ✅ |
| 零服务器 | ✅ GitHub Actions | ❌ | ❌ |
| 多渠道推送 | ✅ 8 大渠道 | ❌ | ❌ |
| 内置策略 | ✅ 三段式/Regime | ✅ | ✅ |
| 成本 | 免费 | 免费/付费 | 付费 |

---

## ⚠️ 风险提示

**重要声明**：

1. **本系统仅供学习研究**，不构成投资建议
2. 量化策略有风险，过往业绩不代表未来表现
3. 股票投资需谨慎，请根据自身风险承受能力决策
4. 系统默认配置适合学习，实盘使用请充分测试

---

## 🛠️ 开发扩展

### 添加新的数据源

```python
from data_provider.base import DataProviderBase

class MyDataProvider(DataProviderBase):
    """自定义数据源示例"""
    
    def realtime_quote(self, code: str) -> pd.DataFrame:
        # 实现实时行情获取
        pass
    
    def historical_data(self, code: str, days: int) -> pd.DataFrame:
        # 实现历史数据获取
        pass
    
    def fundamental_data(self, code: str) -> dict:
        # 实现基本面数据获取
        pass
```

### 添加新的推送渠道

```python
from bot.base import NotifierBase

class CustomNotifier(NotifierBase):
    """自定义推送渠道示例"""
    
    def send(self, title: str, content: str, **kwargs) -> bool:
        # 实现推送逻辑
        pass
```

---

## ❓ 常见问题

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

## 📚 资源链接

- **GitHub 仓库**：https://github.com/ZhuLinsen/daily_stock_analysis
- **完整指南**：https://github.com/ZhuLinsen/daily_stock_analysis/blob/main/docs/full-guide.md
- **常见问题**：https://github.com/ZhuLinsen/daily_stock_analysis/blob/main/docs/FAQ.md
- **LLM 配置指南**：https://github.com/ZhuLinsen/daily_stock_analysis/blob/main/docs/LLM_CONFIG_GUIDE.md

---

## 🎓 总结

股票智能分析系统是一个功能完整的 AI 量化投资平台：

**优点**：
- ✅ 零成本运行（GitHub Actions）
- ✅ 多渠道实时推送
- ✅ 内置交易纪律，避免情绪化决策
- ✅ 支持 A股、港股、美股
- ✅ 活跃社区，持续更新

**局限性**：
- ⚠️ AI 分析仅供参考，不构成投资建议
- ⚠️ 需要一定技术基础配置
- ⚠️ 实盘使用需充分回测验证

适合 **有技术背景的投资者** 学习量化分析思路，或作为 **个人投资管理工具** 辅助决策。
