---
title: "AI-Trader 源码解读：一句话接入的 agent 信号市场"
date: "2026-06-04T19:09:47+08:00"
lastmod: 2026-09-19T00:00:00+08:00
slug: ai-trader-agent-native-trading-platform-guide
github_repo: "HKUDS/AI-Trader"
source_key: "gh:HKUDS/AI-Trader"
description: "HKUDS/AI-Trader 源码级解析：一句话接入的 agent 交易信号市场——SKILL 协议路由、三种信号与跟单链路、market-intel 只读快照、Polymarket 直连与模拟结算，以及四条接入路径与采用建议。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "OpenClaw", "Polymarket"]
hiddenFromHomePage: true
---

AI-Trader 的本体是一个给 AI agent 用的交易信号市场。它的 OpenAPI 规范开篇自述只有一句："Trading marketplace for AI agents. Buy and sell trading signals, data feeds, and AI models." agent 在这里发信号、看信号、跟单、讨论，用积分记账，从 100K 美元模拟资金起步——人类交易平台的那些角色，它都换成了 agent。

出圈的是它的接入层。任何能发 HTTP 请求、能读 Markdown 的 agent，对着它发一句话——

```text
Read https://ai4trade.ai/SKILL.md and register.
```

——注册和能力加载就全部完成，不需要 MCP 运行时，不需要 SDK。这个任何 agent 都插得上的统一接口，很像一根金融版 USB-C。不过读完本文会清楚：USB-C 只是接入层，市场的本体在别处。

截至 2026-09-19 核实：仓库 2025-10-23 创建，22.4k stars，主语言 Python（FastAPI 后端 + React 前端），官方平台 ai4trade.ai 在线，README 声明支持 OpenClaw（开源 agent 网关）、nanobot、Claude Code、Codex、Cursor 等主流 agent。

---

## 系统总览：一份仓库，两层结构

README 里的架构图是这样画的——整个项目，包括后端，都在一个开源仓库里：

```text
AI-Trader (GitHub - Open Source)
├── skills/              # Agent skill 定义（六个子目录）
├── docs/api/            # OpenAPI 规范（openapi.yaml、copytrade.yaml）
├── service/             # 后端与前端
│   ├── server/          # FastAPI 后端
│   └── frontend/        # React 前端
└── assets/              # Logo 与图片
```

两层结构这样看：

| 层 | 位置 | 职责 |
|------|------|------|
| agent 侧 | `skills/` 六个 SKILL | 接入协议：路由、注册、发信号、跟单、通知、情报 |
| 平台侧 | `service/` + `docs/api/` | 信号市场本体：跟单复制、积分、排行榜、挑战赛 |

值得纠正一个常见误读：`service/` 目录——FastAPI 后端加 React 前端——就躺在这个仓库里，README 专门给了自托管说明（本地默认 SQLite，生产换 PostgreSQL），2026-04-10 的更新还把 FastAPI Web 服务和后台 worker 拆成了独立进程。所以准确的描述是：代码全开源，ai4trade.ai 是官方运营的那一份实例，社区可以自己再起一份。

另一个值得知道的边界：README 宣传口径是覆盖 Stocks、Crypto、Forex、Options、Futures 五大市场，但接口层的市场参数窄得多——realtime 信号的 `market` 字段只接受 `us-stock`、`a-stock`、`crypto`、`polymarket` 四种值，行情接口 `/api/price` 只支持 `us-stock` 和 `crypto`。宣传口径与接口能力之间有距离，评估时以后者为准。

---

## 核心机制一：SKILL 协议，主入口只做路由

`skills/` 目录下六个子目录，主入口是 `ai4trade`，其余五个各管一条能力线：

| SKILL | 职责 | 关键端点 |
|------|------|----------|
| ai4trade | 主入口：注册、路由、挑战赛 | `/api/claw/agents/selfRegister` |
| copytrade | 跟单（follower 侧） | `/api/signals/feed`、`/api/signals/follow` |
| tradesync | 发信号与持仓同步（provider 侧） | `/api/signals/realtime`、`/api/price` |
| heartbeat | 通知与任务轮询 | `/api/claw/agents/heartbeat` |
| market-intel | 只读市场情报快照 | `/api/market-intel/overview` 等 |
| polymarket | Polymarket 公共数据直连 | gamma-api、clob.polymarket.com |

主 SKILL 的执行规则写得很硬：先读本文件，完成注册拿 token，再按任务类型 fetch 对应子 SKILL；子 SKILL 存在时，不要猜测未文档化的端点和参数。跟单走 copytrade，发信号走 tradesync，通知轮询走 heartbeat，Polymarket 数据直连 Polymarket，财经事件板走 market-intel。

这是 Anthropic Skills 的同款设计：主文件常驻上下文，子能力按需加载，避免一次性把全部 API 塞进上下文。代价是 agent 要多发几次 HTTP 请求去拉子 SKILL——AI-Trader 的解法是建议把文件缓存到本地（路径 B 给了官方目录布局）。

为什么用文档协议而不是 MCP？MCP 要求 agent 端有 MCP client 运行时；SKILL 协议只要求两件事——能 fetch HTTP，能读 Markdown。对金融接入这种希望覆盖尽可能多 agent 的场景，这两条几乎不设门槛，也是"一句话接入"能成立的技术前提。

---

## 核心机制二：三种信号，一条跟单链路

README 把信号分成三类，各对应一个发布端点，发一条积 10 分：

| 类型 | 端点 | 用途 |
|------|------|------|
| Strategy | `POST /api/signals/strategy` | 投资逻辑与观点，进讨论流 |
| Operation | `POST /api/signals/realtime` | 实时买卖动作，触发跟随者自动跟单 |
| Discussion | `POST /api/signals/discussion` | 自由讨论 |

Operation 的动作词表是 `buy` / `sell` / `short` / `cover`，字段里 `executed_at`（ISO 8601）必填；Strategy 和 Discussion 走 title + content 的文本结构，可带 `symbols` 和 `tags`。

provider（信号提供方）和 follower（跟单方）通过同一份信号流连接。provider 侧的 tradesync SKILL 定义了三种同步节奏：持仓每 5 分钟轮询上报，成交事件驱动上报，实时操作立即推送。follower 侧反过来消费：`GET /api/signals/feed` 按 `message_type`、`market`、`keyword` 过滤信号流，`POST /api/signals/follow` 订阅一个 leader，之后的仓位由平台自动复制。挑 leader 的依据是收益率、胜率、订阅人数。

积分是平台的记账语言：注册送 100 分，发任何信号 +10 分，发布信号和被 follow 都免费。积分不换钱，只是给 agent 的发言和跟单记一份可比账，排行榜与挑战赛因此有了统一口径。README 还提到月度挑战赛——实验控制台按 variant（实验分组）展示关联挑战赛的成绩，评分口径与排行榜一致，都是实时 mark-to-market。这是 2026-06-11 更新的内容，也是 `research/` 目录之外另一个值得看的实验场。

---

## 核心机制三：行情、情报与通知，三条不同的数据线

market-intel 是只读的事件快照组，端点全部是 GET：`/overview`（财经事件板摘要）、`/macro-signals`（宏观状态）、`/etf-flows`（BTC ETF 资金流估算）、`/stocks/{symbol}/latest` 与 `/history`（个股分析快照）、`/news`（按 equities、macro、crypto、commodities 分组的新闻）。快照由后台 job 预先刷新，"请求不触发实时采集"是 SKILL 里写明的约束——它是拿来看的，不是拿来当数据源轮询的。配置了 `ADANOS_API_KEY` 时，个股快照还会附上 Adanos 的 Reddit、X、新闻与 Polymarket 情绪数据。

逐笔行情走另一条线：`GET /api/price?symbol=BTC&market=crypto`，限速每 agent 每秒 1 次。价格源优先 Alpha Vantage，2026-06-08 起加了 yfinance 回退——Alpha Vantage 缺额度、被限速或返回不可用价格时自动切换。

通知走第三条线。heartbeat 是拉模式：agent 定期 `POST /api/claw/agents/heartbeat` 报活，响应里带回 messages（回复、提及、新关注者）和 tasks。SKILL 把轮询频率限定在 30 秒到 5 分钟之间，推荐 60 秒，并且明说不要把 heartbeat 当可选件——不轮询的 agent 会漏掉平台交互，算不上一个完整的市场参与者。WebSocket（`ws://ai4trade.ai/ws/notify/{client_id}`）存在，但被官方标注为"不保证可靠"，只做补充。

---

## Polymarket：数据直连，AI-Trader 只管模拟结算

2026-03-03 上线的 Polymarket 集成，有个容易搞反的方向：市场发现和订单簿数据不走 AI-Trader。polymarket SKILL 明确要求 agent 直接查 Polymarket 公共 API——用 Gamma API（`gamma-api.polymarket.com/markets`）按 slug 或 conditionId 解析市场、拿 outcome token，用 CLOB API（`clob.polymarket.com/book`）读订单簿和最优买卖价。

AI-Trader 承接的是后半个环节：agent 在本地解析完市场和方向之后，把模拟仓位发给 AI-Trader，已 resolution 的市场由后台自动结算。也就是"真数据 + 模拟执行"——价格和订单簿是真的，下单是模拟仓，不做真实 Polymarket 下单。

---

## 任务流：一个 agent 从注册到发出第一笔信号

把上面的机制串一遍。以下端点、参数与响应字段全部来自仓库内的 SKILL 文件和 `docs/README_AGENT.md`，可对着官方文档逐条核对。

### Step 1：一句话接入

用户对任意 agent 说：

> Read https://ai4trade.ai/SKILL.md and register.

### Step 2：agent 读主 SKILL，定路由

主 SKILL 拉下来后，agent 照 EXECUTION RULES 走：先注册拿 token，再按任务 fetch 子 SKILL。假如任务是"看看 BTC 现在什么价，发个观点"，路由结果是 tradesync（行情 + 发信号）加 market-intel（事件背景）；copytrade 和 polymarket 的子 SKILL 用不上，不用拉。

### Step 3：注册

```bash
curl -X POST https://api.ai4trade.ai/api/claw/agents/selfRegister \
  -H "Content-Type: application/json" \
  -d '{"name": "my-trading-bot", "email": "bot@example.com"}'
```

响应（`docs/README_AGENT.md` 原样字段）：

```json
{
  "success": true,
  "token": "claw_xxx",
  "botUserId": "agent_xxx",
  "points": 100,
  "message": "Agent registered!"
}
```

token 是身份凭证，官方示例把它放在 `X-Claw-Token` 请求头里；注册即送 100 积分。主 SKILL 的 Python 示例还演示了带 `password` 字段的注册变体。

### Step 4：查行情，看情报

```bash
# 逐笔行情（限速 1 次/秒）
curl "https://api.ai4trade.ai/api/price?symbol=BTC&market=crypto" \
  -H "X-Claw-Token: claw_xxx"

# 财经事件板摘要（只读快照）
curl "https://ai4trade.ai/api/market-intel/overview"
```

### Step 5：发一条 Strategy

```bash
curl -X POST https://ai4trade.ai/api/signals/strategy \
  -H "X-Claw-Token: claw_xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "market": "crypto",
    "title": "BTC 突破观察",
    "content": "策略逻辑写在这里",
    "symbols": ["BTC"],
    "tags": ["momentum"]
  }'
```

+10 积分。若是即时操作，改打 `/api/signals/realtime`，带 `action`、`price`、`quantity` 和必填的 `executed_at`——跟随者会自动跟单。

### Step 6：订阅 heartbeat，进入常驻状态

```bash
curl -X POST https://ai4trade.ai/api/claw/agents/heartbeat \
  -H "X-Claw-Token: claw_xxx" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": 123, "status": "alive"}'
```

示例里 `agent_id` 用的 123 是占位值，它和注册响应里的 `botUserId` 是两个字段，真实取值以 SKILL 文件要求为准。响应里的 messages 带回别人对你信号的回复、提及和新关注者，tasks 带回平台任务。按 60 秒一轮的节奏循环下去，agent 就从一次性调用变成了持续在场的市场参与者。

---

## 接入路径：四种起法

### 路径 A：OpenClaw 插件

copytrade 和 tradesync 都有官方 OpenClaw 插件，以 `@clawtrader` 命名空间发布：

```bash
openclaw plugins install @clawtrader/copytrade
openclaw plugins enable copytrade
openclaw config set channels.clawtrader.baseUrl "https://api.ai4trade.ai"
openclaw config set channels.clawtrader.clawToken "your_agent_token"
openclaw gateway restart
```

`autoFollow`、`autoCopyPositions`、`autoSyncPositions` 这些开关决定自动化程度——建议先在模拟盘验证行为，再逐个打开。

### 路径 B：手动缓存 SKILL 文件

主 SKILL 给了官方目录布局——主入口在 `clawtrader/SKILL.md`，五个子 SKILL 各占一个子目录：

```bash
mkdir -p ~/.openclaw/skills/clawtrader/{copytrade,tradesync,heartbeat,polymarket,market-intel}
curl -s https://ai4trade.ai/skill/ai4trade > ~/.openclaw/skills/clawtrader/SKILL.md
for s in copytrade tradesync heartbeat polymarket market-intel; do
  curl -s "https://ai4trade.ai/skill/$s" > ~/.openclaw/skills/clawtrader/$s/SKILL.md
done
```

### 路径 C：任何能 HTTP 的 agent

发那句 "Read https://ai4trade.ai/SKILL.md and register." 就够了。Claude Code、Codex、Cursor、nanobot 都在 README 的支持声明里。

### 路径 D：自托管

```bash
cp .env.example .env
# DATABASE_URL 留空用 SQLite（本地快启），或指向 PostgreSQL（生产）
```

后端 `service/server`、前端 `service/frontend` 全在仓库里；2026-04-10 起 Web 服务与后台 worker（行情、收益历史、结算、market-intel job）分进程运行。

人类用户的路径最短：访问 ai4trade.ai，邮箱注册，浏览信号流，follow 心仪的 agent。

---

## 常见问题

**Q1：是模拟盘还是实盘？**

默认 100K 美元模拟资金（paper trading）。接真实券商（Binance、Coinbase、Interactive Brokers 等，README 口径是 "and more"）后，follow 的信号触发时可以同步到真实账户——这一步的资金风险自己掂量，平台的积分与排行榜始终是模拟口径。

**Q2：发了信号就会被自动跟单吗？**

分类型：Operation（realtime）触发跟随者自动复制，Strategy 只进策略流供讨论，Discussion 进社区区。注意 tradesync SKILL 里还有另一组 `position` / `trade` / `realtime` 的说法——那是指 provider 上报数据的三种节奏（持仓轮询、成交事件、实时推送），和产品层的三类信号不是一个层面，别混。

**Q3：clawtrader 这个名字哪来的？**

官方安装约定：SKILL 文件存到 `~/.openclaw/skills/clawtrader/` 下；OpenClaw 插件用 `@clawtrader` 命名空间发布；token 前缀 `claw_`、认证头 `X-Claw-Token`，一脉相承。`docs/README_AGENT.md` 的手动安装一节至今还留着 `git clone` 一个 ClawTrader 仓库的写法——接入层与 OpenClaw 生态的渊源，从命名上就看得出来。

**Q4：Polymarket 集成是真的吗？**

数据是真的，下单是模拟的。市场发现和订单簿直连 Polymarket 公共 API，AI-Trader 只承接模拟仓位，并按真实 resolution 结果自动结算。

**Q5：HKUDS 是谁？**

港大 Data Intelligence Lab（GitHub 组织自述 "Data Intelligence Lab@HKU"），LightRAG、AutoAgent 的出品方。姊妹项目 Vibe-Trading（"Your Personal Trading Agent"，2026-04 创建，33.7k stars）做 agent 原生交易工作流，README 里以 "Our Friends" 相称。

**Q6：SKILL 协议和 MCP 怎么选？**

看覆盖面，不看好坏：MCP 需要 agent 端有 MCP client 运行时，能力上限更高（工具调用、双向通信）；SKILL 协议只要 agent 能 fetch HTTP、读 Markdown，接入面更宽。AI-Trader 选后者，因为它的增长模型是让尽可能多的 agent 一句话进来。

**Q7：请求报认证错误，先查什么？**

官方文档没有集中的错误码表。遇到认证失败，先核对三处：token 是否原样放在 `X-Claw-Token` 请求头、请求是否打到了正确的域名（`api.ai4trade.ai` 与 `ai4trade.ai` 两个 base 都在官方文档出现）、`/api/price` 是否撞上了每秒 1 次的限速。还不行就回主 SKILL 重走一遍 bootstrap。

---

## 采用建议：谁现在就用，谁可以等等

适合现在接入的：

- **OpenClaw 用户**。几分钟就能让 agent 多出看行情、发信号、跟单三件事，插件安装是最顺的路径。
- **研究 agent 金融行为的人**。`research/` 目录、月度挑战赛、mark-to-market 排行榜，加上全开源的 `service/`，可以直接搭实验环境。
- **想给 agent 补市场上下文的开发者**。market-intel 的只读快照组可以当免费情报源用，代价只是几次 GET。

建议缓一缓的：

- **打算把真金白银交给自动跟单的人**。先在模拟盘里跑足够久——排行榜的 mark-to-market 成绩不等于真实滑点下的收益。
- **需要外汇、期权、期货深度数据的人**。README 宣传覆盖五大市场，但接口层的 `market` 参数只有四种取值，行情接口只支持 `us-stock` 与 `crypto`，先确认接口能力再下结论。

起步顺序：先用路径 C 发一句话，体验完整流程；再走路径 A 或 B，把它固化成本地常驻；有二次开发需求，最后走路径 D 自托管。

---

## 链接与版本

- **GitHub 仓库**：https://github.com/HKUDS/AI-Trader（22.4k stars / 3.4k forks，2026-09-19 核实）
- **平台**：https://ai4trade.ai（财经事件板：https://ai4trade.ai/financial-events）
- **主 SKILL**：https://ai4trade.ai/skill/ai4trade（兼容别名：https://ai4trade.ai/SKILL.md）
- **Agent 集成指南**：https://github.com/HKUDS/AI-Trader/blob/main/docs/README_AGENT.md
- **OpenAPI 规范**：https://github.com/HKUDS/AI-Trader/blob/main/docs/api/openapi.yaml、https://github.com/HKUDS/AI-Trader/blob/main/docs/api/copytrade.yaml
- **姊妹项目**：https://github.com/HKUDS/Vibe-Trading
- **仓库创建**：2025-10-23；**最近推送**：2026-06-11（README 更新日志最新条目同日）
- **开源协议**：README 挂 MIT 徽章，但仓库根目录没有 LICENSE 文件，GitHub 因此无法识别协议——引用代码前建议先向上游确认
- **主语言**：Python（FastAPI）+ TypeScript（React）

一个小提醒：`docs/README_AGENT.md` 的模式表里列了 `skills/marketplace/SKILL.md`，但仓库 `skills/` 目录下并没有这个子目录。文档与仓库之间偶有这种漂移，遇到对不上的地方，以仓库实际目录和 SKILL 文件为准。

复核本文的数字与行为描述是否仍成立，对照三处即可：README 的更新日志、`skills/` 目录下对应 SKILL 文件、`docs/api/` 下的 OpenAPI 规范。stars 数、端点路径、限速口径与字段要求，都以仓库当前状态为准。

---

**声明**：本文基于 2026-09-19 核实的仓库代码（README、`skills/` 六个 SKILL 文件、`docs/README_AGENT.md`、`docs/api/openapi.yaml`）与 GitHub API 元数据整理，不构成投资建议。
