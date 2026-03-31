---
title: "ValueCell：社区驱动的多智能体金融应用平台完全指南"
slug: "valuecell-multi-agent-finance-platform-guide"
date: 2026-04-01T02:16:00+08:00
categories: ["技术笔记"]
tags: ["ValueCell", "多智能体", "Multi-Agent", "金融科技", "量化交易", "AI Agent", "Binance", "OKX", "Hyperliquid", "去中心化金融"]
description: "深度解析 ValueCell：社区驱动的多智能体金融应用平台，支持DeepResearch Agent/Strategy Agent/News Retrieval Agent，提供选股、调研、跟踪、交易全流程服务，完全本地存储敏感信息，Apache-2.0许可证，Python 3.12+，支持Binance/Hyperliquid/OKX等交易所。"
---

# ValueCell：社区驱动的多智能体金融应用平台完全指南

## §1 学习目标

完成本文档后，你将能够：

- ✅ 理解 ValueCell 的定位与设计理念
- ✅ 掌握 ValueCell 的核心功能与使用方法
- ✅ 部署和配置 ValueCell 开发环境
- ✅ 配置 AI 模型提供商和交易所连接
- ✅ 使用多智能体进行投资研究
- ✅ 创建和执行交易策略
- ✅ 扩展开发 ValueCell 智能体
- ✅ 集成到生产级金融应用

---

## §2 项目概述

### 2.1 什么是 ValueCell？

**ValueCell**（[GitHub 仓库](https://github.com/ValueCell-ai/valuecell)）是一个**社区驱动的多智能体金融应用平台**，使命是打造世界最大的去中心化金融智能体社区。

**官方描述**：

> ValueCell 是一个社区驱动的多智能体金融应用平台，我们的使命是打造世界最大的去中心化金融智能体社区。它为您提供顶级的投资智能体团队，帮助您完成选股、调研、跟踪，甚至交易。系统会将您的敏感信息完全托管在本地，确保核心数据安全。

**官网**：[valuecell.ai](https://valuecell.ai)

**产品状态**：🔥🔥🔥 产品已上线，提供 A 股深度研究与市场分析，无需部署。

### 2.2 核心数据

| 指标 | 数值 |
|------|------|
| **许可证** | Apache-2.0 |
| **语言** | Python 3.12+ |
| **社区** | Discord、Twitter、LinkedIn、YouTube |

### 2.3 使命与愿景

| 维度 | 内容 |
|------|------|
| **使命** | 打造世界最大的去中心化金融智能体社区 |
| **愿景** | 让每个人都能获得顶级的投资智能体服务 |
| **核心价值** | 用户数据完全本地托管，确保安全 |
| **社区** | 欢迎开发者参与共建 |

### 2.4 与其他平台的区别

| 特性 | ValueCell | TradingAgents | AutoGen | LangChain Agents |
|------|-----------|---------------|---------|------------------|
| **金融专注** | 原生 | 部分 | 否 | 否 |
| **多智能体** | 原生 | 是 | 是 | 是 |
| **交易所集成** | 内置 | 部分 | 否 | 否 |
| **本地存储** | 完全本地 | 部分 | 否 | 否 |
| **A 股支持** | 原生 | 否 | 否 | 否 |

---

## §3 核心功能详解

### 3.1 多智能体系统

**核心理念**：为金融投资场景打造专业的多智能体协作团队。

#### 3.1.1 DeepResearch Agent

**深度研究智能体**：

| 能力 | 说明 |
|------|------|
| **基本面分析** | 获取并分析股票的基本面文件 |
| **数据输出** | 输出准确的数据、可解释性的总结 |
| **研究范围** | 股票基本面、财务报表、行业分析 |

```python
# DeepResearch Agent 使用示例
from valuecell.agents import DeepResearchAgent

agent = DeepResearchAgent()
result = await agent.research("AAPL")
# 输出：财务数据 + 可解释的研究总结
```

#### 3.1.2 Strategy Agent

**策略交易智能体**：

| 能力 | 说明 |
|------|------|
| **多币种支持** | 支持多种加密资产 |
| **多策略执行** | 支持多种交易策略 |
| **自动执行** | 自动执行你的交易策略 |
| **风险管理** | 内置风险控制机制 |

```python
# Strategy Agent 使用示例
from valuecell.agents import StrategyAgent

agent = StrategyAgent(
    exchange="binance",
    strategy="grid",
    pairs=["BTC/USDT"]
)
await agent.start()
```

#### 3.1.3 News Retrieval Agent

**新闻检索智能体**：

| 能力 | 说明 |
|------|------|
| **个性化定时任务** | 支持个性化定时任务的新闻推送 |
| **及时跟踪** | 及时跟踪关键信息 |
| **多源整合** | 整合多个新闻来源 |
| **智能过滤** | 基于用户偏好过滤新闻 |

### 3.2 灵活集成

#### 3.2.1 多 LLM 提供商支持

| 提供商 | 说明 | 状态 |
|--------|------|------|
| **OpenRouter** | 聚合多个模型的路由服务 | ✅ 支持 |
| **SiliconFlow** | 国产模型聚合平台 | ✅ 支持 |
| **Azure** | 微软云 OpenAI 服务 | ✅ 支持 |
| **OpenAI-compatible** | 兼容 OpenAI 格式的 API | ✅ 支持 |
| **Google** | Google Gemini 系列 | ✅ 支持 |
| **OpenAI** | OpenAI GPT 系列 | ✅ 支持 |
| **DeepSeek** | 国产深度求索模型 | ✅ 支持 |

#### 3.2.2 市场数据覆盖

| 市场 | 说明 | 状态 |
|------|------|------|
| **美国市场** | 股票、ETF、期权 | ✅ 支持 |
| **加密货币市场** | BTC、ETH、主流 altcoin | ✅ 支持 |
| **香港市场** | 港股、ETF | ✅ 支持 |
| **中国市场** | A 股、ETF | ✅ 支持 |

#### 3.2.3 多智能体框架兼容

| 框架 | 协议 | 状态 |
|------|------|------|
| **LangChain** | A2A | ✅ 支持 |
| **Agno** | A2A | ✅ 支持 |
| **AutoGen** | 待定 | 🔜 规划中 |

#### 3.2.4 交易所连接

| 交易所 | 说明 | 状态 | 合约类型 |
|--------|------|------|----------|
| **Binance** | 仅国际站，不支持美国站 | ✅ 已测试 | USDT 本位合约 |
| **Hyperliquid** | 仅支持 USDC 保证金 | ✅ 已测试 | USDC 本位合约 |
| **OKX** | USDT 本位合约 | ✅ 已测试 | USDT 本位合约 |
| **Coinbase** | USDT 本位合约 | 🟡 部分测试 | USDT 本位合约 |
| **Gate.io** | USDT 本位合约 | 🟡 部分测试 | USDT 本位合约 |
| **MEXC** | USDT 本位合约 | 🟡 部分测试 | USDT 本位合约 |
| **Blockchain.com** | USDT 本位合约 | 🟡 部分测试 | USDT 本位合约 |

**图例说明**：
- ✅ 已测试：在生产环境中经过充分测试和验证
- 🟡 部分测试：代码实现已完成但未完全测试，可能需要调试
- 🔜 规划中：功能正在开发中

### 3.3 安全机制

| 安全特性 | 说明 |
|----------|------|
| **本地存储** | 敏感信息完全托管在本地 |
| **密钥保护** | API 密钥本地存储，不通过互联网发送 |
| **定期轮换** | 建议定期重置 API 密钥 |
| **IP 白名单** | 支持交易所 API IP 白名单配置 |

---

## §4 技术架构

### 4.1 核心模块

| 模块 | 说明 |
|------|------|
| **Agents** | 核心智能体实现 |
| **Backend** | 后端 API 服务 |
| **Frontend** | Web UI 界面 |
| **Exchange Adapters** | 交易所适配器 |
| **LLM Adapters** | LLM 提供商适配器 |
| **Storage** | 本地存储（LanceDB/SQLite） |

### 4.2 架构图

```
┌─────────────────────────────────────────────────────────┐
│                    ValueCell Platform                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────┐ │
│  │ DeepResearch │   │   Strategy    │   │    News    │ │
│  │    Agent    │   │    Agent      │   │  Retrieval  │ │
│  └──────┬───────┘   └──────┬───────┘   └──────┬─────┘ │
│          │                   │                    │        │
│          └───────────────────┼────────────────────┘        │
│                              │                           │
│                    ┌──────────┴──────────┐               │
│                    │    Agent Manager    │               │
│                    │   (A2A Protocol)   │               │
│                    └──────────┬──────────┘               │
│                               │                           │
│  ┌────────────────────────────┼────────────────────────┐  │
│  │                    Adapters Layer                    │  │
│  ├─────────────┬─────────────┬─────────────┬─────────┤  │
│  │ LLM Adapters│Exchange     │ Market Data │ Storage  │  │
│  │ (OpenAI/    │ Adapters    │  Adapters   │(LanceDB/ │  │
│  │ DeepSeek)   │(Binance/   │ (US/HK/CN/  │ SQLite)  │  │
│  │             │ OKX/Hyper)  │  Crypto)    │          │  │
│  └─────────────┴─────────────┴─────────────┴─────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 4.3 数据流

```
用户请求
    ↓
Web UI (localhost:1420)
    ↓
Backend API (FastAPI)
    ↓
Agent Manager (A2A Protocol)
    ↓
┌─────────────────────────────────────┐
│         Agent Execution              │
│                                      │
│ DeepResearch / Strategy / News       │
│      ↓              ↓                │
│ LLM Adapter    Exchange Adapter    │
│      ↓              ↓                │
│ OpenAI/DeepSeek  Binance/OKX       │
└─────────────────────────────────────┘
    ↓
Local Storage (LanceDB + SQLite)
    ↓
结果返回 Web UI
```

---

## §5 快速开始

### 5.1 新用户安装

#### 5.1.1 下载应用程序

从 GitHub 的[发布页面](https://github.com/ValueCell-ai/valuecell/releases)下载：

| 平台 | 安装包 | 说明 |
|------|--------|------|
| **macOS** | ValueCell.dmg | Apple Silicon + Intel |
| **Windows** | ValueCell.exe | x64 |

#### 5.1.2 配置 AI 模型

1. 通过网页 UI 界面添加你的 AI 模型 API Key
2. 选择提供商（OpenAI/DeepSeek/SiliconFlow 等）
3. 配置模型参数

#### 5.1.3 配置交易所

1. 在交易所申请 API Key
2. 设置 IP 白名单（可选）
3. 配置 API 凭证到 ValueCell

### 5.2 开发者安装

#### 5.2.1 克隆仓库

```bash
git clone https://github.com/ValueCell-ai/valuecell.git
cd valuecell
```

#### 5.2.2 运行应用程序

**Linux / macOS**：

```bash
bash start.sh
```

**Windows (PowerShell)**：

```powershell
.\start.ps1
```

#### 5.2.3 访问界面

- **Web UI**：[http://localhost:1420](http://localhost:1420)
- **日志**：在终端查看应用程序日志

### 5.3 实时交易配置

#### 5.3.1 配置 AI 模型

```python
# 在 Web UI 中配置
# 提供商: OpenAI / DeepSeek / SiliconFlow
# API Key: xxx
# 模型: gpt-4 / deepseek-chat / silicon-flow-xxx
```

#### 5.3.2 配置交易所

**Binance 配置**：

```
交易所: Binance
交易对: BTC/USDT
合约类型: USDT 本位永续合约
注意事项:
- 仅支持国际站 (binance.com)，不支持美国站
- 请确保永续合约账户有足够的 USDT 余额
- 交易对格式: BTC/USDT
```

**Hyperliquid 配置**：

```
交易所: Hyperliquid
保证金货币: USDC
认证方式: 主钱包地址 + API 钱包私钥
交易对格式: SYMBOL/USDC (例如 WIF/USDC)
最低交易额: 10 USDC
```

**OKX 配置**：

```
交易所: OKX
认证信息: API Key + Secret + Passphrase
合约类型: USDT 本位合约
交易对格式: BTC/USDT
```

---

## §6 使用指南

### 6.1 创建研究任务

```python
from valuecell.agents import DeepResearchAgent

# 创建研究智能体
agent = DeepResearchAgent()

# 执行研究
result = await agent.research(
    symbol="AAPL",
    report_type="fundamental",
    depth="comprehensive"
)

print(result)
```

### 6.2 创建交易策略

```python
from valuecell.agents import StrategyAgent
from valuecell.config import ExchangeConfig

# 配置交易所
config = ExchangeConfig(
    exchange="binance",
    api_key="your-api-key",
    api_secret="your-secret",
    testnet=False
)

# 创建策略智能体
agent = StrategyAgent(
    exchange=config,
    strategy="grid",
    pairs=["BTC/USDT", "ETH/USDT"],
    grid_spacing=0.01,
    position_size=0.1
)

# 启动策略
await agent.start()
```

### 6.3 新闻监控

```python
from valuecell.agents import NewsRetrievalAgent

# 创建新闻智能体
agent = NewsRetrievalAgent()

# 设置定时任务
agent.add_schedule(
    keyword="BTC",
    frequency="hourly",
    callback=my_notification_function
)

# 启动监控
await agent.start()
```

### 6.4 实时监控

```python
from valuecell.monitoring import Dashboard

# 创建监控面板
dashboard = Dashboard(port=1420)

# 添加监控指标
dashboard.add_metric("pnl")
dashboard.add_metric("positions")
dashboard.add_metric("orders")

# 启动
await dashboard.start()
```

---

## §7 交易所配置详解

### 7.1 Binance

| 配置项 | 说明 |
|--------|------|
| **交易所** | Binance (仅国际站) |
| **合约类型** | USDT 本位永续合约 |
| **交易对格式** | BTC/USDT |
| **注意事项** | 确保合约账户有足够 USDT 余额 |
| **API 设置** | 申请 API，添加 IP 白名单（通过搜索引擎搜索 "My IP" 查看） |

### 7.2 Hyperliquid

| 配置项 | 说明 |
|--------|------|
| **保证金货币** | USDC |
| **认证方式** | 主钱包地址 + API 钱包私钥 |
| **申请地址** | app.hyperliquid.xyz/API |
| **交易对格式** | 必须手动调整为 SYMBOL/USDC |
| **最低交易额** | 10 USDC |
| **订单类型** | 市价单自动转换为 IoC 限价单 |

### 7.3 OKX

| 配置项 | 说明 |
|--------|------|
| **认证信息** | API Key + Secret + Passphrase |
| **合约类型** | USDT 本位合约 |
| **交易对格式** | BTC/USDT |
| **注意** | 需要提供 OKX 账号密码 |

---

## §8 数据管理

### 8.1 本地存储结构

| 数据类型 | 存储位置 | 说明 |
|----------|----------|------|
| **LanceDB** | 与 .env 同路径 | 智能体知识库 |
| **Knowledge** | 与 .env 同路径 | 知识目录 |
| **SQLite** | 与 .env 同路径 | 应用数据库 |

### 8.2 存储路径

**macOS**：

```
~/Library/Application Support/ValueCell/
├── lancedb/           # 知识库
├── .knowledge/        # 知识目录
└── valuecell.db       # SQLite 数据库
```

**Linux**：

```
~/.config/valuecell/
├── lancedb/
├── .knowledge/
└── valuecell.db
```

**Windows**：

```
%APPDATA%\ValueCell\
├── lancedb\
├── .knowledge\
└── valuecell.db
```

### 8.3 数据重置

如长时间没有更新，可以删除本地数据并重新启动：

```bash
# 删除 LanceDB 目录
rm -rf ~/Library/Application\ Support/ValueCell/lancedb

# 删除知识目录
rm -rf ~/Library/Application\ Support/ValueCell/.knowledge

# 删除数据库
rm ~/Library/Application\ Support/ValueCell/valuecell.db
```

---

## §9 开发扩展

### 9.1 ValueCell SDK

#### 9.1.1 Python SDK

```python
from valuecell import ValueCellSDK

# 初始化 SDK
sdk = ValueCellSDK(
    api_key="your-api-key",
    base_url="http://localhost:8000"
)

# 创建研究任务
result = await sdk.research(symbol="AAPL")

# 创建交易策略
strategy = await sdk.create_strategy(
    exchange="binance",
    strategy="grid",
    pairs=["BTC/USDT"]
)
```

#### 9.1.2 WebSocket 支持

```python
from valuecell.sdk import WebSocketClient

# 创建 WebSocket 客户端
client = WebSocketClient("ws://localhost:8000/ws")

# 订阅事件
client.subscribe("trade.executed")
client.subscribe("order.filled")
client.subscribe("position.updated")

# 处理事件
@client.on("trade.executed")
async def on_trade(trade):
    print(f"Trade executed: {trade}")

# 启动
await client.connect()
```

### 9.2 插件架构

```python
from valuecell.plugins import Plugin

class MyCustomPlugin(Plugin):
    name = "my-custom-plugin"
    version = "1.0.0"

    async def on_trade(self, trade):
        # 自定义交易逻辑
        pass

    async def on_order(self, order):
        # 自定义订单逻辑
        pass

# 注册插件
ValueCellSDK.register_plugin(MyCustomPlugin())
```

### 9.3 智能体注册

```python
from valuecell.agents import AgentRegistry

# 注册自定义智能体
@AgentRegistry.register
class MyCustomAgent:
    name = "my-custom-agent"
    description = "Custom investment research agent"

    async def research(self, symbol):
        # 自定义研究逻辑
        pass
```

---

## §10 最佳实践

### 10.1 安全实践

| 实践 | 说明 |
|------|------|
| **密钥保管** | 妥善保管 API 密钥，避免泄露 |
| **本地存储** | 敏感信息仅存储在本地 |
| **定期轮换** | 定期重置 API 密钥 |
| **IP 白名单** | 尽量配置交易所 API IP 白名单 |
| **最小权限** | 仅授予交易所 API 必要的权限 |

### 10.2 交易实践

| 实践 | 说明 |
|------|------|
| **仓位管理** | 控制单笔交易仓位不超过 10% |
| **止损设置** | 始终设置止损单 |
| **策略测试** | 先在测试网验证策略 |
| **风险监控** | 实时监控持仓和盈亏 |
| **多样化** | 不要把所有资金放在一个策略 |

### 10.3 开发实践

| 实践 | 说明 |
|------|------|
| **环境隔离** | 开发、测试、生产环境分离 |
| **日志记录** | 详细记录运行日志 |
| **错误处理** | 实现完善的错误捕获和处理 |
| **单元测试** | 为核心功能编写单元测试 |
| **代码审查** | 提交前进行代码审查 |

---

## §11 应用场景

### 11.1 个人投资者

**场景**：帮助个人投资者进行股票研究和交易。

```python
# 个股研究
researcher = DeepResearchAgent()
report = await researcher.research("AAPL")

# 创建交易策略
strategy = StrategyAgent(
    exchange="binance",
    strategy="dca",
    pairs=["BTC/USDT"],
    amount=100,
    frequency="daily"
)
await strategy.start()
```

### 11.2 量化团队

**场景**：为量化团队提供智能体协作框架。

```python
# 多智能体协作
team = AgentTeam()

researcher = DeepResearchAgent()
analyst = AnalystAgent()
trader = StrategyAgent()

team.add_agent(researcher)
team.add_agent(analyst)
team.add_agent(trader)

# 协作流程
await team.execute("Research and trade BTC")
```

### 11.3 财富管理

**场景**：为财富管理公司提供智能投顾服务。

```python
# 财富管理智能体
wealth_manager = WealthManagementAgent(
    risk_profile="moderate",
    investment_horizon="long-term"
)

# 生成投资建议
recommendations = await wealth_manager.generate_recommendations(
    client_id="client-123",
    goals=["retirement", "education"]
)
```

---

## §12 常见问题

### Q1: ValueCell 和 TradingAgents 有什么区别？

ValueCell 专注于金融投资场景，原生支持 A 股和加密货币，提供完整的本地存储和交易所集成。TradingAgents 是一个更通用的多智能体框架。

### Q2: 支持中国 A 股交易吗？

是的，ValueCell 产品已上线 A 股深度研究与市场分析，可访问 valuecell.ai 使用。

### Q3: 如何确保资金安全？

- API 密钥仅存储在本地设备
- 不通过互联网传输敏感信息
- 建议设置交易所 API IP 白名单
- 定期轮换 API 密钥
- 仅授予交易所 API 必要的权限

### Q4: 支持哪些交易所？

主要支持 Binance、Hyperliquid、OKX（均已测试），部分支持 Coinbase、Gate.io、MEXC、Blockchain.com。

### Q5: 如何参与开发？

欢迎开发者加入 Discord 讨论组，交流社区 Roadmap 及未来贡献者权益规划。开发流程及标准详见 CONTRIBUTING.md。

---

## §13 总结

### 13.1 核心优势

| 优势 | 说明 |
|------|------|
| **金融专注** | 原生支持股票、加密货币投资 |
| **多智能体** | 专业的研究、策略、新闻智能体团队 |
| **本地存储** | 敏感信息完全本地托管 |
| **灵活集成** | 支持多个 LLM 提供商和交易所 |
| **开源免费** | Apache-2.0 许可证 |
| **社区驱动** | 欢迎开发者参与共建 |

### 13.2 适用场景

| 场景 | 说明 |
|------|------|
| **个人投资** | 股票研究和交易辅助 |
| **量化交易** | 策略开发和自动化执行 |
| **财富管理** | 智能投顾服务 |
| **机构研究** | 团队协作投研平台 |

### 13.3 项目信息

| 项目 | 信息 |
|------|------|
| **许可证** | Apache-2.0 |
| **语言** | Python 3.12+ |
| **官网** | valuecell.ai |
| **社区** | Discord、Twitter、YouTube |

### 13.4 相关链接

| 资源 | 链接 |
|------|------|
| **GitHub** | https://github.com/ValueCell-ai/valuecell |
| **官网** | https://valuecell.ai |
| **Discord** | https://discord.com/invite/84Kex3GGAh |
| **Twitter** | @valuecell |
| **YouTube** | Watch on YouTube |

---

*文档版本 1.0 | 撰写日期：2026-04-01 | 基于 ValueCell (Apache-2.0)*