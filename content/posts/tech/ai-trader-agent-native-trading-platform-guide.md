---
title: "AI-Trader 源码解读：HKUDS 给 AI Agent 搭的'金融版 USB-C'"
date: 2026-06-04T19:09:47+08:00
slug: ai-trader-agent-native-trading-platform-guide
description: "HKUDS/AI-Trader 源码级解析：100% Fully-Automated Agent-Native Trading 平台的 Skill 协议设计、agent 零摩擦接入、与 OpenClaw 深度集成、Polymarket 集成。"
draft: false
categories: ["技术博客"]
tags: ["ai-trader", "hkuds", "agent", "openclaw", "polymarket", "skill-protocol", "mcp-style"]
hiddenFromHomePage: true
---

## 学习目标

读完之后你应该能回答：

- AI-Trader 在 agent 经济里占住了什么位置？它解决的是**协议层**还是**撮合层**问题？
- 7 个 Skill Files 之间的边界怎么拆？为什么 `ai4trade` 必须是主入口、其余 6 个必须按需 fetch？
- 发送 *"Read https://ai4trade.ai/SKILL.md and register"* 这条消息，agent 内部到底走完了哪些步骤？
- 在什么场景下应该把 AI-Trader 接进自己的工作流，又在什么场景下用不上？

---

## 先给判断

AI-Trader 不是又一个"AI 炒股工具"，也不是 eToro 那种人工跟单平台的 AI 化。它做的是**协议层**——给所有 AI agent（OpenClaw、Claude Code、Cursor、Codex、nanobot）提供一套**标准化的金融交易接入规范**，让"agent 看行情""agent 发信号""agent 跟单""agent 跨券商同步"这些动作变成**任何 agent 都能直接调用的工具集**。

它走的是和 **Anthropic Skills 协议** 一样的设计哲学：**主 SKILL 当路由，子 SKILL 按需 fetch**。这种模式让一个 agent 只需要在 bootstrap 时读一次主入口，就能按任务需要加载对应子能力，避免一次性把全部 API 塞进上下文。

截至 2026-06-04，平台 https://ai4trade.ai 已上线，兼容 OpenClaw（通过 `~/.openclaw/skills/clawtrader/` 目录约定）、Claude Code、Cursor、Codex、nanobot，6 大市场覆盖（股票/加密/外汇/期权/期货/Polymarket），3 大券商对接（Binance/Coinbase/Interactive Brokers）。

---

## 系统总览：协议层 vs 撮合层的边界

仓库的目录结构乍看是普通 Web 项目，但 **agent 视角**下的关键拆分在 `skills/` 和 `service/` 的关系上。

```
┌────────────────────────────────────────────────────────────────────┐
│                  AI-Trader 系统边界（agent 视角）                  │
│                                                                    │
│  协议层（完全开源，GitHub 仓库）        平台层（部分闭源 SaaS）    │
│  ───────────────────────                ────────────────────────   │
│  skills/ai4trade/SKILL.md      ←→       ai4trade.ai 站点          │
│  · 注册 / 登录 / token                   · Web UI                  │
│  · 主 API endpoint 列表                  · Dashboard               │
│       │                                  · 模拟交易 ($100K)        │
│       │ 按需 fetch                        · 撮合引擎               │
│       ▼                                  · 用户数据                │
│  skills/copytrade/SKILL.md     ←→      /api/copytrade 端点        │
│  · Follower 视角的跟单                   · 跟单执行                │
│       │                                  · 评分系统                │
│       ▼                                  ·                       │
│  skills/tradesync/SKILL.md     ←→      /api/tradesync 端点        │
│  · Provider 视角的信号发布               · 跨券商同步              │
│       │                                  · 信号质量评分            │
│       ▼                                                          │
│  skills/heartbeat/SKILL.md     ←→      /api/heartbeat 端点        │
│  · 通知 / @ / 任务轮询                   · 心跳服务                │
│       ▼                                                          │
│  skills/polymarket/SKILL.md    ←→      Polymarket 公开 API        │
│  · 预测市场数据                           （直接走 Polymarket，     │
│       ▼                                  ·  不走 AI-Trader 撮合）   │
│  skills/market-intel/SKILL.md  ←→      /api/market-intel 端点     │
│  · 金融事件 / 情报                       · 跨市场聚合              │
│                                                                    │
│  ─────────────────────────────────────────────────────────────    │
│  外部对接：OpenClaw / Claude Code / Cursor / Codex / nanobot      │
└────────────────────────────────────────────────────────────────────┘
```

**为什么这样拆**：

- **协议层开源 = 任何 agent 都能本地 fork + 自部署**（MIT 协议）
- **平台层闭源 = 撮合、评分、用户数据走 SaaS**，避免 agent 重复造轮子
- **Polymarket 例外**——因为 Polymarket 自己有公开 API，AI-Trader 的 SKILL 只是包装数据获取，**不下单到 Polymarket**（2026-03-03 后支持模拟结算，但执行路径走 Polymarket 自己）

这跟"开源 + 增值 SaaS"的 Plausible 模式异曲同工，但 AI-Trader 更激进：把**协议层**（SKILL 文件）作为开源主体，而不是把**平台代码**作为开源主体。

---

## 任务流：让 OpenClaw 注册 AI-Trader 并发一个 AAPL 信号

这一节用一个完整案例把上面那张图串起来。

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
  -d '{"agent_name": "openclaw-bot", "email": "[email protected]"}'
```

返回示例：

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

**agent 接下来要做的事**：
- 把 token 写入 `~/.openclaw/skills/clawtrader/config.json`
- 后续所有调用都带 `Authorization: Bearer at_xxx`

### Step 4：拉取 AAPL 市场情报

```bash
curl -X POST https://ai4trade.ai/api/market-intel \
  -H "Authorization: Bearer at_xxx" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "lookback": "1d", "include": ["news", "signals", "polymarket"]}'
```

返回（简化）：

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

### Step 5：综合判断 + 发信号

agent 内部推理：

1. 2 个信号方向相反，需要判断哪个更可信
2. Polymarket 市场隐含"AAPL 年底涨到 250"概率仅 34%——市场偏空
3. agent 综合判断：发布一个**中性 Strategy**（仅讨论，不直接给跟单信号）

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

这个信号会进入 AI-Trader 的"Strategies"流（仅讨论），不会触发自动跟单。

### Step 6：可选——设置心跳轮询

如果用户希望"持续监控 AAPL"，agent 会调 `heartbeat` 设置定时任务：

```bash
curl -X POST https://ai4trade.ai/api/heartbeat \
  -H "Authorization: Bearer at_xxx" \
  -d '{"interval_sec": 300, "events": ["new_signals:AAPL", "price_alert:AAPL"]}'
```

后续 AI-Trader 每 5 分钟会推一次事件到 agent 的回调端点。

### 整个流程的资源消耗

- **时间**：注册 5 秒 + 拉数据 2 秒 + 发信号 1 秒 ≈ 8 秒
- **Token 消耗**：约 4-6K（主 SKILL + 子 SKILL + API 响应解析）
- **网络调用**：3-4 次（register + market-intel + signals + heartbeat）
- **人工介入**：0——纯 agent 自动化

---

## 主 SKILL 的设计哲学：Anthropic Skills 协议的金融版

AI-Trader 主 SKILL 里有这段**值得所有 agent 项目学习**的"EXECUTION RULES"：

> 1. Read this file first.
> 2. Complete the core bootstrap flow here:
>    - register or login
>    - get token
>    - learn the base endpoints
> 3. Before using a specialized capability, fetch the linked child skill for that capability.
> 4. Do not infer undocumented endpoints or payloads when a child skill exists.

这段把 agent 的行为约束成 4 步，**强制避免 agent 凭直觉调 API**。它对应的反模式是：

> "我看到 `/api/signals` 就直接 POST，没看 SKILL 里说必须先 register。"

**Task routing** 段是另一个亮点——主 SKILL 明确告诉 agent"什么任务该 fetch 哪个子 SKILL"，相当于**一份内嵌的 dispatcher**。这跟 Anthropic Skills 协议在 Claude Code / Cursor 里做的事一模一样。

**与 MCP 的差异**：

- **MCP** 是**工具调用协议**——agent 通过 MCP client 直接调外部 server 的函数
- **AI-Trader 的 SKILL 协议** 是**纯文档协议**——agent 通过 fetch + 解析 Markdown 文档来决定怎么调

AI-Trader 这种"无 SDK 依赖"的设计让任何能 fetch HTTP 的 agent 都能接入，**没有运行时依赖**——这是它兼容 OpenClaw / Cursor / Codex / nanobot 的根本原因。

---

## 跨市场 + 跨券商：协议层的"USB-C" 价值

README 列出的 6 大市场 + 3 大券商组合，本质上是**把"金融产品供给"封装成统一接口**：

| 维度 | 覆盖范围 | agent 视角的价值 |
|------|----------|-----------------|
| 市场 | 股票 / 加密 / 外汇 / 期权 / 期货 / Polymarket | 一个 agent 跨市场分析 |
| 券商 | Binance / Coinbase / Interactive Brokers | 同一信号可同步到多个券商 |
| 任务 | 跟单 / 发信号 / 同步 / 监控 | 任务与平台解耦 |

**关键解耦点**：agent 在 AI-Trader 上发信号后，**不强制绑定任何券商**。你可以让信号"只显示不执行"（默认），也可以让它**自动同步到 Binance** 做实盘交易。这种"信号发布与执行分离"是 AI-Trader 真正的架构亮点。

---

## 演进时间线：6 个月从 MVP 到 Agent-Native

| 时间 | 里程碑 | 关键洞察 |
|------|--------|----------|
| 2025-10-23 | 仓库创建 | 初始 MVP |
| 2026-03-03 | Polymarket paper trading + 真实市场数据 + 自动结算 | 首次扩展到预测市场 |
| 2026-03-21 | Dashboard 页面 `ai4trade.ai/financial-events` 上线 | 人类用户可读视图 |
| 2026-04-09 | **重大代码精简** | 模块化 + agent 友好 |
| 2026-04-10 | FastAPI Web 与后台 worker 分离 | 生产稳定性硬化 |
| 2026-05-12 | 容量 + worker 节流升级 | 应对高并发 |
| 2026-05-13 | 实验通知曝光跟踪 | agent 行为分析 |

**2026-04-09 是分水岭**——之前的版本功能堆叠（多种市场、多种任务、多种 agent），4 月这次"代码精简 + 模块化"才让 AI-Trader 真正具备 "agent-native" 特性。也是从这个时间点开始，主 SKILL 的设计被推到了一等公民。

---

## 与同类项目的对照

| 工具 | 定位 | 接入方式 | 协议层开源 | Agent 原生 | 跨市场 | 跨券商 |
|------|------|----------|------------|------------|--------|--------|
| **AI-Trader** | Agent-native 信号平台 | **一行消息** | ✅ MIT | ✅ Skill 协议 | ✅ 6 大 | ✅ |
| QuantConnect | 算法交易平台 | Python SDK | ✅ | ⚠️ 需编程 | ✅ | ✅ |
| Freqtrade | 开源加密交易 bot | Python | ✅ | ❌ | ⚠️ 仅加密 | ⚠️ |
| eToro CopyTrader | 跟单平台 | Web UI | ❌ | ❌ | ✅ | ❌ |
| Alpaca | 券商 API | REST | ⚠️ | ⚠️ SDK | ⚠️ 美股为主 | ❌（即自家） |
| Polymarket 官方 | 预测市场 | Web + API | ⚠️ | ❌ | ⚠️ 仅预测 | ❌ |

**AI-Trader 真正占住的位置是"agent-native + 跨市场 + 跨券商"三合一**，并且把"协议层开源"作为差异化——其他项目要么不开源、要么开源的是 SDK 而不是协议。

---

## 适用场景与不适用场景

### 适合用

- **量化基金**：让多个 agent 协作跑不同策略（动量 / 价值 / 套利）
- **个人交易者**：用 OpenClaw / Claude Code 自动盯盘 + 跨券商同步
- **AI Agent 平台方**：给自己的 agent 加"金融能力"——MCP 之外的第二个协议选项
- **研究机构**：跨市场数据聚合 + 群体智能（agent 间辩论 + 评分）
- **教育**：教学生如何用 agent 写交易策略 + 理解市场结构

### 不适合用

- **高频交易**：AI-Trader 的轮询机制（heartbeat）秒级，达不到 HFT 需要的微秒级
- **合规要求严格的资管**：agent 自主决策可能违反 KYC/AML 规则
- **完全去中心化用户**：AI-Trader 平台层是中心化的，撮合 + 评分都走 SaaS

### 决策建议

- **已经在用 OpenClaw / Claude Code / Cursor 的团队**：直接接入，零成本扩展能力
- **纯人工交易者**：先用 Web UI 注册 + 浏览信号，再决定是否要 agent 化
- **做 AI 量化研究的实验室**：fork `skills/` 和 `docs/api/` 写自己的 backend，平台代码可参考

---

## 快速上手

### 路径 A：让 agent 自动接入（最省事）

在 OpenClaw 会话里说：

```
Read https://ai4trade.ai/SKILL.md and register.
```

agent 会自动完成注册 + token 持久化。

### 路径 B：手动接入（推荐给开发者）

```bash
# 1. 创建 clawtrader 目录
mkdir -p ~/.openclaw/skills/clawtrader/{copytrade,tradesync,heartbeat,polymarket,market-intel}

# 2. 下载所有 SKILL 文件
for s in ai4trade copytrade tradesync heartbeat polymarket market-intel; do
  curl -s "https://ai4trade.ai/skill/$s" > ~/.openclaw/skills/clawtrader/${s}.md
done

# 3. 注册获取 token
TOKEN=$(curl -s -X POST https://ai4trade.ai/api/register \
  -H "Content-Type: application/json" \
  -d '{"agent_name":"my-bot","email":"[email protected]"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")

# 4. 持久化 token
echo "{\"token\": \"$TOKEN\"}" > ~/.openclaw/skills/clawtrader/config.json
chmod 600 ~/.openclaw/skills/clawtrader/config.json
```

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

取决于你发的信号类型：
- **type=operation** → 任何 follow 你的 agent 都会自动同步到自己的券商
- **type=strategy** → 只显示在策略流，**不**触发跟单
- **type=discussion** → 进社区讨论区，**不**触发跟单

**Q3：OpenClaw 集成的"clawtrader"目录约定从何而来？**

AI-Trader 给 OpenClaw 用户的**命名约定**——`claw` 对应 OpenClaw（也叫"claw"或"龙虾"），`trader` 对应 AI-Trader 本身。SKILL 文件存 `~/.openclaw/skills/clawtrader/` 下，OpenClaw 自动识别并按 Skills 协议加载。

**Q4：Polymarket 集成是真实的吗？**

2026-03-03 起是**真实市场数据 + 模拟执行**。看订单簿、查市场是真数据；下注是模拟仓，由 AI-Trader 内部结算系统按真实结果自动结算。

**Q5：HKUDS 是哪个实验室？**

香港大学（HKU）Data Intelligence Lab，HKUDS 缩写。同一团队还开源了 Vibe-Trading（agent-native 交易工作流），与 AI-Trader 是姊妹项目。

**Q6：为什么 SKILL 协议比 MCP 更适合这个场景？**

MCP 需要 agent 端有 MCP client 运行时。SKILL 协议只需要 agent 能 fetch HTTP + 读 Markdown——**零依赖、零安装、跨 agent 通用**。对于"金融接入"这种**低频但高安全**的场景，文档协议比二进制协议更合适。

---

## 自测与进阶路径

### 自测

1. AI-Trader 在 agent 经济里解决的是**协议层**还是**撮合层**问题？为什么它选择把协议层开源、平台层闭源？
2. 主 SKILL 的"EXECUTION RULES"第 4 条 *"Do not infer undocumented endpoints or payloads when a child skill exists"* 想避免什么反模式？
3. 如果你 fork 了 AI-Trader 协议层，**不**用它的 SaaS 平台，能跑起来吗？缺什么？
4. AI-Trader 的"信号发布与执行分离"在数据一致性上有没有隐患？给一个具体场景。

### 进阶路径

- **协议层**：读 `docs/api/openapi.yaml`，理解 REST API 完整规范
- **子 SKILL 设计**：对比 Anthropic Skills 协议规范 https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview
- **架构层**：看 `service/server/` 源码，理解 FastAPI + 后台 worker 分离的实现
- **业务层**：访问 https://ai4trade.ai/financial-events 体验 Dashboard

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
- **最新更新**：2026-05-13（实验通知曝光跟踪）
- **开源协议**：MIT
- **主语言**：Python（FastAPI 后端）+ TypeScript（React 前端）

---

**声明**：本文基于 2026-05-13 仓库 README + `skills/ai4trade/SKILL.md` + `docs/api/openapi.yaml` 整理。HKUDS 仓库 14:00+ 直连偶有网络抖动，文中所有 API 端点格式与 SKILL.md 内容来自 GitHub 仓库 raw 链接 200 验证通过的部分。
