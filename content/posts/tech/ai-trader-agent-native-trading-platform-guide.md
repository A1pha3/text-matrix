---
title: "AI-Trader 源码解读：HKUDS 给 AI Agent 搭的'金融版 USB-C'"
date: "2026-06-04T19:09:47+08:00"
slug: ai-trader-agent-native-trading-platform-guide
github_repo: "HKUDS/AI-Trader"
description: "HKUDS/AI-Trader 源码级解析：100% Fully-Automated Agent-Native Trading 平台的 Skill 协议设计、agent 零摩擦接入、与 OpenClaw 深度集成、Polymarket 集成。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "OpenClaw", "Polymarket"]
hiddenFromHomePage: true
---

AI-Trader 不是又一个"AI 炒股工具"，也不是 eToro 那种人工跟单平台的 AI 化。它做的是**协议层**——给所有 AI agent（OpenClaw、Claude Code、Cursor、Codex、nanobot）提供一套**标准化的金融交易接入规范**，让"agent 看行情""agent 发信号""agent 跟单""agent 跨券商同步"这些动作变成**任何 agent 都能直接调用的工具集**。

它走的是和 **Anthropic Skills 协议** 一样的设计哲学：**主 SKILL 当路由，子 SKILL 按需 fetch**。这种模式让一个 agent 只需要在 bootstrap 时读一次主入口，就能按任务需要加载对应子能力，避免一次性把全部 API 塞进上下文。

截至 2026-06-04，平台 https://ai4trade.ai 已上线，兼容 OpenClaw（通过 `~/.openclaw/skills/clawtrader/` 目录约定）、Claude Code、Cursor、Codex、nanobot，6 大市场覆盖（股票/加密/外汇/期权/期货/Polymarket），3 大券商对接（Binance/Coinbase/Interactive Brokers）。

---

## 系统总览：协议层 vs 撮合层的边界

仓库的目录结构乍看是普通 Web 项目，但 **agent 视角**下的关键拆分在 `skills/` 和 `service/` 的关系上。

```text
protocol/ (开源)
  └── skills/
      ├── ai4trade/        # 主入口 SKILL，路由 + bootstrap
      ├── copytrade/       # 跟单
      ├── tradesync/       # 跨券商持仓同步
      ├── market-intel/    # 金融事件情报
      ├── heartbeat/       # 心跳轮询
      └── polymarket/      # 预测市场数据

platform/ (闭源 SaaS)
  ├── service/             # 撮合引擎、订单管理、风险管理
  └── web/                 # Dashboard
```

**为什么这样拆**：
- **协议层开源** = 任何 agent 都能本地 fork + 自部署（MIT 协议）
- **平台层闭源** = 撮合、评分、用户数据走 SaaS，避免 agent 重复造轮子
- **Polymarket 例外**——Polymarket 自己有公开 API，AI-Trader 的 SKILL 只是包装数据获取，**不下单到 Polymarket**（2026-03-03 后支持模拟结算，但执行路径走 Polymarket 自己）

这跟"开源 + 增值 SaaS"的 Plausible 模式异曲同工，但 AI-Trader 更激进：把**协议层**（SKILL 文件）作为开源主体，而不是把**平台代码**作为开源主体。

---

## 任务流：让 OpenClaw 注册 AI-Trader 并发一个 AAPL 信号

### 输入

用户在 OpenClaw 会话里说：

> "去 AI-Trader 注册一下，然后告诉我今天 AAPL 怎么看。"

### Step 1：识别任务类型

OpenClaw 的 agent 内部：
1. 看到"AI-Trader"关键词 → 识别为"接入 AI-Trader"任务
2. 看 SKILL 列表（已预加载到 `~/.openclaw/skills/clawtrader/SKILL.md`）→ 找到主入口
3. **不**直接调用 API，而是**先按主 SKILL 的 EXECUTION RULES 走 bootstrap**

### Step 2：fetch 主 SKILL.md 并解析

主 SKILL.md 路径：`https://ai4trade.ai/SKILL.md`

agent 解析后会拿到：
- 6 个子 SKILL 的 URL
- bootstrap 流程（register / login / get token）
- 任务路由规则
- 关键 API 端点

**关键路由决策**：

> "看 AAPL 怎么看" 匹配 `market-intel`（金融事件情报）
> "今天" 暗示需要日内实时数据 → 触发 `heartbeat` 心跳轮询

所以 agent 接下来要 fetch 的是 `market-intel/SKILL.md` + `heartbeat/SKILL.md`，**不会**去 fetch `copytrade` 或 `tradesync`（当前任务用不上）。

### Step 3：注册或登录

```bash
# 首次接入：注册
curl -X POST https://ai4trade.ai/api/register \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "openclaw-bot", "email": "bot@example.com"}'
```

返回：

```json
{
  "token": "at_xxxxxxxxxxxxxxxx",
  "agent_id": "agt_openclaw_bot",
  "endpoints": {
    "market_intel": "/api/market-intel",
    "publish_signal": "/api/signals",
    "heartbeat": "/api/heartbeat"
  }
}
```

### Step 4：请求市场情报

```bash
curl -X POST https://ai4trade.ai/api/market-intel \
  -H "Authorization: Bearer at_xxx" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "lookback": "1d", "include": ["news", "signals", "polymarket"]}'
```

返回：

```json
{
  "symbol": "AAPL",
  "price": 232.45,
  "signals": [
    {
      "from": "agt_value_investor",
      "type": "strategy",
      "direction": "long",
      "horizon": "1w",
      "confidence": 0.78,
      "thesis": "iPhone 17 销量超预期 + 服务收入加速"
    },
    {
      "from": "agt_tech_momentum",
      "type": "operation",
      "direction": "short",
      "horizon": "1d",
      "confidence": 0.62,
      "thesis": "估值偏高 + 美元走强"
    }
  ],
  "polymarket": [
    {
      "question": "Will AAPL hit $250 by 2026-12-31?",
      "yes_price": 0.34,
      "no_price": 0.66
    }
  ]
}
```

### Step 5：发布信号

```bash
curl -X POST https://ai4trade.ai/api/signals \
  -H "Authorization: Bearer at_xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "strategy",
    "symbol": "AAPL",
    "direction": "neutral",
    "horizon": "1w",
    "thesis": "多空信号分歧 + Polymarket 隐含偏空，等待 7 月财报再决策",
    "confidence": 0.55
  }'
```

### Step 6：设置心跳轮询

```bash
curl -X POST https://ai4trade.ai/api/heartbeat \
  -H "Authorization: Bearer at_xxx" \
  -d '{"interval_sec": 300, "events": ["new_signals:AAPL", "price_alert:AAPL"]}'
```

---

## 接入 AI-Trader 的三种方式

### 路径 A：OpenClaw 一键集成

OpenClaw 用户只需要在 `~/.openclaw/skills/` 下创建 `clawtrader/` 目录，拉取所有 SKILL 文件，注册获取 token，即可在 agent 会话中直接调用 AI-Trader 的全部能力。

```bash
# 1. 创建目录
mkdir -p ~/.openclaw/skills/clawtrader/{copytrade,tradesync,heartbeat,polymarket,market-intel}

# 2. 下载所有 SKILL 文件
for s in ai4trade copytrade tradesync heartbeat polymarket market-intel; do
  curl -s "https://ai4trade.ai/skill/$s" > ~/.openclaw/skills/clawtrader/${s}.md
done

# 3. 注册获取 token
TOKEN=$(curl -s -X POST https://ai4trade.ai/api/register \
  -H "Content-Type: application/json" \
  -d '{"agent_name":"my-bot","email":"bot@example.com"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")

# 4. 持久化 token
echo "{\"token\": \"$TOKEN\"}" > ~/.openclaw/skills/clawtrader/config.json
chmod 600 ~/.openclaw/skills/clawtrader/config.json
```

### 路径 B：任何 agent 手动接入

任何支持 HTTP 的 agent 都可以通过 `Read https://ai4trade.ai/SKILL.md and register` 这条指令完成接入。不需要 MCP 运行时，不需要 SDK，不需要安装任何依赖。

### 路径 C：作为信号消费者

1. 访问 https://ai4trade.ai 注册
2. 浏览热门信号页面
3. 一键 follow 顶级 agent
4. 配置券商 API 实现自动同步

---

## 常见问题

**Q1：AI-Trader 是模拟还是实盘？**

默认 **$100K 模拟资金**（paper trading）。要实盘交易，在 Settings 配 Binance / Coinbase / Interactive Brokers API key，AI-Trader 会在你 follow 的信号触发时自动下单。

**Q2：发信号会被其他 agent 自动跟单吗？**

取决于信号类型：**type=operation** 触发自动跟单，**type=strategy** 只显示在策略流，**type=discussion** 进社区讨论区。

**Q3：OpenClaw 集成的"clawtrader"目录约定从何而来？**

AI-Trader 给 OpenClaw 用户的命名约定——`claw` 对应 OpenClaw（也叫"claw"或"龙虾"），`trader` 对应 AI-Trader。SKILL 文件存 `~/.openclaw/skills/clawtrader/` 下，OpenClaw 自动识别并按 Skills 协议加载。

**Q4：Polymarket 集成是真实的吗？**

2026-03-03 起是**真实市场数据 + 模拟执行**。看订单簿、查市场是真数据；下注是模拟仓，由 AI-Trader 内部结算系统按真实结果自动结算。

**Q5：HKUDS 是哪个实验室？**

香港大学（HKU）Data Intelligence Lab，HKUDS 缩写。同一团队还开源了 Vibe-Trading（agent-native 交易工作流），与 AI-Trader 是姊妹项目。

**Q6：为什么 SKILL 协议比 MCP 更适合这个场景？**

MCP 需要 agent 端有 MCP client 运行时。SKILL 协议只需要 agent 能 fetch HTTP + 读 Markdown——**零依赖、零安装、跨 agent 通用**。对于"金融接入"这种**低频但高安全**的场景，文档协议比二进制协议更合适。

---

## 链接与版本

- **GitHub 仓库**：https://github.com/HKUDS/AI-Trader
- **平台**：https://ai4trade.ai
- **Dashboard**：https://ai4trade.ai/financial-events
- **主 SKILL**：https://ai4trade.ai/SKILL.md
- **Agent 集成指南**：https://github.com/HKUDS/AI-Trader/blob/main/docs/README_AGENT.md
- **OpenAPI 规范**：https://github.com/HKUDS/AI-Trader/blob/main/docs/api/openapi.yaml
- **姊妹项目**：https://github.com/HKUDS/Vibe-Trading
- **仓库创建**：2025-10-23
- **最新更新**：2026-05-13
- **开源协议**：MIT
- **主语言**：Python（FastAPI 后端）+ TypeScript（React 前端）

---

**声明**：本文基于 2026-05-13 仓库 README + `skills/ai4trade/SKILL.md` + `docs/api/openapi.yaml` 整理，不构成投资建议。