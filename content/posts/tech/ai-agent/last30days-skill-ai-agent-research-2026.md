---
title: "last30days-skill：AI 全网研究助手从入门到精通"
date: "2026-03-28T17:30:00+08:00"
lastmod: "2026-09-22T10:00:00+08:00"
slug: "last30days-skill-ai-agent-research"
github_repo: "mvanhorn/last30days-skill"
source_key: "gh:mvanhorn/last30days-skill"
aliases:
  - /posts/tech/last30days-skill-ai-agent-research/
description: "深度解析 last30days-skill：62.6k stars 的 AI Agent 研究助手，横跨 Reddit/X/YouTube/TikTok/Polymarket 等 20 个数据源，详解 v3 流水线（搜索前情报解析、LLM 重排、跨源聚类）、doctor 健康检查、完整安装配置与趋势监控指南。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Reddit", "Polymarket"]
---

# last30days-skill：AI 全网研究助手从入门到精通

> 预计阅读时间：28 分钟 | 难度：⭐⭐⭐

---

> **目标读者**：做 AI 辅助研究、信息聚合、趋势追踪的研究人员、投资者、产品经理、开发者与内容创作者
> **核心问题**：如何让 AI Agent 自主检索全网近期讨论，聚合跨平台信号，生成有出处的深度简报？
> **难度**：⭐⭐⭐（中级）
> **预计阅读时间**：28 分钟

本文以 v3.25.0（2026-09-18 发布）为口径。数据读数（stars、数据源清单、评分机制）核对于 2026-09-22，项目迭代很快，以仓库现行文档为准。

---

## 一、它解决什么问题

### 1.1 LLM 的知识截止日期

大语言模型有一个绕不开的局限：**训练数据有时间边界**。模型对截止日期之后的事件、新发布的工具、正在进行的社区讨论一无所知。而下面这些场景恰恰都活在"最近"里：

| 场景 | 需要的信息 |
|------|-----------|
| 投资决策 | 公司近况、市场情绪、预测市场赔率 |
| 技术选型 | 某个工具最近的真实用户反馈 |
| 竞品分析 | 对手的产品更新与社区反应 |
| 见面准备 | 对方最近一个月在说什么、做什么 |
| 趋势研究 | 正在爆发但还没被媒体注意到的话题 |

### 1.2 传统检索的盲区

搜索引擎聚合的是编辑与 SEO 信号。Reddit 的评论区、X 上的专家串、YouTube 45 分钟深度视频里的某句话——这些"人真正在说什么"的内容，Google 搜不到，ChatGPT 只签了 Reddit 一家，Gemini 只有 YouTube。每个平台都是带独立 API、独立鉴权的围墙花园。

last30days 的思路是**自带钥匙（bring your own keys）**：把你各平台的 API key 和浏览器会话拼在一起，让一个 AI Agent 同时搜遍所有花园，再按"真实用户的互动量"互相打分。它的自我定位一句话就能说清：Google 聚合编辑，/last30days 搜索人。

### 1.3 三类别人拿不到的信号

- **社交互动**：Reddit 的 upvote、X 的 likes、HN 的 points——几百万人每天用注意力投票；
- **真金白银**：Polymarket 预测市场的赔率背后是实打实的资金仓位，比评论员的猜测难反驳得多；
- **长内容转写**：YouTube 完整转写稿、TikTok 文案、Instagram 口播——搜索引擎索引不到的深度内容。

---

## 二、架构分析：v3 流水线

### 2.1 两层结构：契约与引擎

项目由两层组成：

- **`skills/last30days/SKILL.md`（约 258KB）**：运行时契约，规定宿主 Agent（Claude Code、Codex、Gemini CLI 等）的行为——如何理解用户意图、何时调用引擎、如何合成报告。宿主模型就是"规划器 + 合成器"。
- **`scripts/last30days.py` + `scripts/lib/`（90 余个模块）**：Python 引擎本体，负责多源并行检索、评分、聚类与渲染。主入口是单文件 `last30days.py`（约 184KB），检索编排集中在 `pipeline.py`。

无头运行（cron、CI）时没有宿主模型，引擎会用一条自动检测链找推理模型做规划与重排：Gemini → OpenAI → xAI → OpenRouter → 本地确定性兜底。

### 2.2 一次研究的完整流程

README 的"How it works"七步：

1. **输入主题**——人物、公司、产品、技术、"X vs Y"均可；
2. **解析谁在参与**——搜索发生之前，先把话题涉及的 X 账号、GitHub 仓库、subreddit、TikTok 话题标签、YouTube 频道解析出来（见 2.3）；
3. **全部数据源并行检索**——多查询扩展，各源并发抓取；
4. **拿别人没有的深度**——YouTube 完整转写、带 upvote 的热门评论、TikTok 文案、Polymarket 赔率，不只是标题和链接；
5. **同一件事合并成一个簇**——Reddit 上的公告、X 上的讨论、TikTok 上的视频指向同一新闻时，合并为一条证据簇而非三条孤立条目；
6. **合成一份简报**——按真实互动量排序、逐条注明出处；
7. **变成你的专家**——跑完一次，当前会话就掌握了社区近 30 天的认知，可以接着追问、写提示词、起草邮件。

### 2.3 搜索前的情报解析

v3 引擎在发起任何 API 调用之前，先跑一个"搜索前大脑"：把话题解析成具体的检索目标——人物对应哪个 X 账号、产品对应哪个 GitHub 仓库、话题活跃在哪个 subreddit。解析是双向的：可以从人物找到公司，也可以从产品找到创始人。

X 账号解析是最能体现价值的一步。以搜索"Dor Brothers"（一个电影制作团队）为例：他们发帖时不会每次都写自己的名字，关键词搜索容易漏掉当事人的帖子。SKILL.md 指导 Agent 先做一次定向搜索找到官方账号（核对蓝标、官网互链、命名一致性，排除仿冒号，比如认 `@thedorbrothers` 而不是 `@DorBrosFan`），然后把账号作为 `--x-handle` 参数传给引擎，直接检索该账号的帖子——把"没提自己名字"的当事人内容捞回来。

### 2.4 数据源与密钥

v3 已覆盖 **20 个数据源**（README"Sources"表口径）：Reddit、X、YouTube、TikTok、Instagram Reels、Hacker News、Polymarket、GitHub、Digg、arXiv、Techmeme、LinkedIn、Meta Ads、StockTwits、Threads、Pinterest、小红书、Bluesky、Perplexity、Web，另有 Truth Social 等小众源在路上。

按获取成本分三档：

| 档位 | 数据源 | 条件 |
|------|--------|------|
| 零配置免费 | Reddit（含评论）、HN、Polymarket、GitHub、StockTwits（金融话题自动激活） | 不需要任何密钥 |
| 免费工具 | YouTube（yt-dlp）、arXiv/Techmeme/Digg（配套 CLI 由首次运行向导自动安装） | CLI 在 PATH 即可 |
| 带密钥解锁 | X、TikTok、Instagram、Threads、Pinterest、LinkedIn、YouTube 评论备份（ScrapeCreators，1 万次免费）、Bluesky（App Password）、Web 搜索（Brave 每月 2000 次免费）等 | 各平台 key |

X 是结构最复杂的一路：后端按 bird（浏览器 cookie 驱动的内置 Bird 客户端，免费）→ xai（`XAI_API_KEY`）→ xurl → xquik 的顺序自动降级；官方 X API（`X_BEARER_TOKEN`）与 grok CLI 通道需显式 opt-in。官方 API 只覆盖最近约一周的帖子，除非你的 X 开发者项目有全档检索权限。X 检索分 FROM 与 ABOUT 两条泳道：当事人自己发的、和社区谈论当事人的，两边都能排序上榜。

小红书（Xiaohongshu/RED）是显式请求制：本机运行已登录的 `xiaohongshu-mcp` 服务后，用 `--search xhs` 按次启用，引擎自动探测 `localhost:18060`。

### 2.5 评分与重排：让真实互动说了算

检索结果怎么排序，是这个项目的核心竞争力。v3 的重排器（`lib/rerank.py`）把几类信号融合成一个最终分：

- **LLM 评审分**：检索相关性由"以查询为中心"的匹配引擎（`lib/relevance.py`）给出 0–1 分，精确短语命中得高分；重排阶段再由评审模型按 0–100 细化。
- **实体惩罚**：标题与摘要完全没提主实体的候选扣 25 分。源码注释解释了这个数字的来历——短名单的典型分差在 30–70 分之间，25 分足以把跑题项压到有效分之下，又不至于一刀切清零。
- **一手帖加成**：由已解析官方账号发出的帖子加 5 分——目的只是不被埋掉，强势的第三方内容依然可以赢过它。
- **跨源佐证**：同一件事每多一个独立来源，佐证加成 +15%。Reddit、X、YouTube 同时在讨论的故事排在最前。
- **新鲜度**：按 `1/√(发帖天数+1)` 衰减。
- **速度主导**：最终融合时互动速度（velocity）以 0.5x–1.5x 乘数调制得分，评审给出的"内容价值"参与调制比例。

另有两条防止评分失真的规则：**单作者上限**——同一作者最多 3 条上榜，防止大 V 刷屏；**Best Takes**——第二个并行评审模型专门给幽默、机智、病毒式传播潜力打分，把社区最好的段子放进简报的独立版块。

**Polymarket 有专用评分**。语义相关性占主导，市场质量只做调节：

```text
relevance = text_score × (0.75 + 0.25 × market_quality)
market_quality = 0.50×成交量分 + 0.25×流动性分 + 0.15×价格变动分 + 0.10×竞争度
```

其中成交量分按 `log1p(月成交量)/16` 归一（约 900 万美元封顶）、流动性分按 `log1p(流动性)/14`（约 120 万美元封顶）、价格变动看单日变动（20% 封顶）、竞争度直接采用市场自身的 competitive 值——越接近 50/50 的市场争议越大，信号越有意思。已结算的市场会被过滤掉。

### 2.6 目录结构

```text
mvanhorn/last30days-skill/
├── skills/last30days/
│   ├── SKILL.md              # 运行时契约（258KB，Agent 行为规范）
│   ├── scripts/
│   │   ├── last30days.py     # 引擎主入口（单文件）
│   │   ├── watchlist.py      # 定时监控的主题清单
│   │   ├── briefing.py       # 日/周摘要生成
│   │   ├── store.py          # SQLite 持久化
│   │   └── lib/              # 90+ 模块：pipeline、rerank、relevance、
│   │                         # polymarket、bird_x、xai_x、doctor……
│   ├── agents/               # 子 Agent 定义
│   └── references/
├── mcp/                      # Go 语言 MCP 服务器（Claude Desktop 用）
├── docs/                     # how-search-works、JSON 导出规范等
├── CONFIGURATION.md          # 全部配置项参考（82KB）
├── CONCEPTS.md               # 概念解析
└── CHANGELOG.md              # 版本历史（142KB）
```

---

## 三、使用指南

### 3.1 安装

| 宿主环境 | 安装方式 |
|---------|---------|
| **Claude Code**（推荐） | `/plugin marketplace add mvanhorn/last30days-skill`，然后 `/plugin install last30days`。插件缓存版本化，随发布自动更新 |
| **Codex / Cursor / Copilot / Gemini CLI 等 50+ 宿主** | `npx skills add mvanhorn/last30days-skill -g`（`-g` 全局安装，跨项目可用） |
| **Grok**（xAI Build CLI） | `grok plugin marketplace add mvanhorn/last30days-skill`，然后 `grok plugin install last30days` |
| **claude.ai 网页版** | 从 Releases 下载 `last30days.skill`，在 Customize > Skills 中上传（需先开启代码执行能力） |
| **Claude Desktop** | 从 Releases 下载对应平台的 `.mcpb` 包，拖入 Settings > Extensions，以 MCP 服务器形式接入 |
| **OpenClaw** | `clawhub install last30days-official` |
| **开发者** | `git clone` 后把 `skills/last30days` 软链到 `~/.claude/skills/last30days`，工作区改动即时生效 |

宿主要求 Python 3.12+；没有系统 Python 时，向导会通过 uv 自动配置受管的 3.12。

### 3.2 首次运行：零配置即用，向导按需解锁

Reddit、HN、Polymarket、GitHub 不需要任何配置，装完就能跑。第一次执行 `/last30days` 会触发一次征求同意的引导流程（Claude Code 上是弹窗，其他宿主是对话式）：

1. **浏览器 cookie**：询问是否读取 Firefox/Safari 的登录态以解锁 X 等平台（Chrome 默认不读，需显式配置）。macOS 上若权限不足，会引导开启"完全磁盘访问权限"；
2. **ScrapeCreators 注册**：提供 GitHub 设备授权登录，成功后密钥自动持久化到本地 `.env`（权限 600），解锁 TikTok、Instagram 及 YouTube 转写备份，附 1 万次免费调用；
3. **评论源选择**：推荐档开启 TikTok + Instagram + YouTube 的评论抓取；"全部"档额外加入 Threads 与 Pinterest。评论默认开启，这两项是仅有的可选项。

### 3.3 配置密钥

密钥按优先级从三处读取：进程环境变量 > `.env` 文件 > macOS 钥匙串/Linux pass（最低优先级）。`.env` 支持两个位置：

- `~/.config/last30days/.env`：用户级全局配置；
- `.claude/last30days.env`：项目级配置，**必须**先设置 `LAST30DAYS_TRUST_PROJECT_CONFIG=1` 才会被读取——不可信仓库里的项目配置不会被加载，防止恶意仓库劫持你的密钥。

一份常用的全局配置：

```bash
# ~/.config/last30days/.env（权限应为 600）
LAST30DAYS_MEMORY_DIR=~/Documents/Last30Days   # 研究报告保存位置

# ScrapeCreators：一个密钥解锁 TikTok/Instagram/Threads/Pinterest/LinkedIn
# 注册与设备授权: https://scrapecreators.com
SCRAPECREATORS_API_KEY=your_key_here

# X/Twitter：浏览器 cookie 方式（免费，推荐）
# 登录 x.com 后从 DevTools 复制 auth_token 与 ct0 两个 Cookie
AUTH_TOKEN=your_auth_token
CT0=your_ct0_token

# X 备用通道（可选）
XAI_API_KEY=xai-your_key              # xAI
X_BEARER_TOKEN=your_token             # 官方 X API，需 LAST30DAYS_X_BACKEND=xapi

# 其他可选源
BSKY_HANDLE=your.bsky.social          # Bluesky
BSKY_APP_PASSWORD=xxxx-xxxx-xxxx
BRAVE_API_KEY=your_key                # Web 搜索，每月 2000 次免费
```

每次研究的产物默认存为 `~/Documents/Last30Days/<主题slug>-raw.md`，同一主题同日重跑会覆盖，不同日期会追加日期戳。

### 3.4 日常调用

```text
/last30days Claude Code best practices
/last30days OpenClaw vs Hermes vs Paperclip        ← 单趟对比模式
/last30days prompting techniques for ChatGPT
/last30days what's exploding in AI agents?         ← 趋势发现模式
```

几个实用开关：`--days=7` 或 `--days=90` 调整时间窗口；`--quick`/`--deep` 控制深度（以 X 为例，默认档每个查询抓 30 条，deep 档 60 条）；跑完一次后输入 `eli5 on` 切换到通俗解读模式；`--emit=html` 产出可分享的自包含网页；`--as-of` 做历史回看；`--hiring-signals` 专门解读公司的招聘信号；`--competitors` 自动发现竞品并做横向对比。

无头/脚本场景直接调引擎：

```bash
python3 skills/last30days/scripts/last30days.py "AI coding agents" --emit=json
```

### 3.5 健康检查：doctor

多源系统最烦人的问题是"为什么 X 这次没结果"。`doctor` 命令把所有数据源过一遍，按四态给出体检报告——WORKING（正常）/ TURNED ON - UNVERIFIED（已开启未验证）/ NOT WORKING（故障）/ COULD BE ON（可开启未开启），每个故障项附具体的修复指引：缺哪个 key、哪个 CLI 不在 PATH、哪个 cookie 过期了。

```bash
python3 skills/last30days/scripts/last30days.py doctor              # 四态体检（文本）
python3 skills/last30days/scripts/last30days.py doctor --json       # 机器可读
python3 skills/last30days/scripts/last30days.py doctor --postmortem # 上次运行哪里出了问题
python3 skills/last30days/scripts/last30days.py doctor --probe      # 有界在线探测
```

`doctor` 与 `--postmortem` 不读浏览器 cookie、不消耗任何付费额度，退出码恒为 0（报告问题本身就是成功运行）；`--probe` 只对免费源做有界探测，信用计费源一概不碰。体检结果缓存 15 分钟（`LAST30DAYS_DOCTOR_TTL` 可调）。

### 3.6 趋势监控与研究库

默认模式每次产出一份快照。要持续追踪，仓库内置三件套：

**SQLite 持久化**。任意运行加 `--store`（或在 `.env` 设 `LAST30DAYS_STORE=1`），发现按 `source_url` 去重后写入 `~/.local/share/last30days/research.db`——同一 URL 跨运行更新而非重复入库，形成时间序列。

**主题清单 watchlist.py**。登记需要定期研究的主题，由外部调度器（cron、launchd）触发：

```bash
# 登记主题（默认每天早 8 点，--weekly 改为每周一）
python3 skills/last30days/scripts/watchlist.py add "british airways middle east" --weekly

# 配置 Slack webhook：仅当出现新发现时推送
python3 skills/last30days/scripts/watchlist.py config delivery "https://hooks.slack.com/services/..."
python3 skills/last30days/scripts/watchlist.py run-all
```

配合 crontab 即可全自动化（示意）：`0 8 * * 1 cd ~/project && python3 scripts/watchlist.py run-all`。

**简报与研究库**。`briefing.py` 汇总日/周摘要；`library feed` 把历史研究变成带 Atom 订阅源的本地站点（`index.html` + `feed.xml`），`library search` 用 SQLite FTS5 离线检索你研究过的一切。新的研究会自动携带"From your library"小节，提示与你过去研究重叠的部分。

### 3.7 趋势发现模式

不知道该研究什么时，问一句"什么正在爆发"：

```text
/last30days what's exploding in AI agents?
```

引擎切换到发现模式：先横扫 Reddit 分类榜、HN 前沿、Digg 聚类等榜单提名候选话题，再对每个候选做完整研究，最后给出 5–10 个按热度速度排序的话题，每个都附跨源数据、动量标签和一条可直接执行的跟进命令。每个话题必须跨过置信度门槛（跨源确认或单一来源的显著爆发），过不了就如实报告"本窗口没有可靠发现"，而不是硬凑榜单。脚本直调用 `--discover`；`--drill` 可以对上次结果中的任意证据簇做深挖追问。

---

## 四、扩展与工程质量

**结构化输出**。`--emit=json` 输出带版本的稳定 Agent 配置文件，字段规范见 `docs/reference/json-export.md`，适合接入下游工作流。

**本地语料**。`--corpus <目录>` 把你自己的 `.md`/`.txt`（装了 pdftotext 还支持 PDF）注册为私有检索源，命中内容以"From your files"版块出现。语料文件只在本地读取，不进任何网络请求，也不会写入对外发布的内容。

**受众预设**。`--register exec/dev/creator/eli5` 调整简报体裁：exec 决策优先、dev 偏技术信号、creator 突出传播钩子、eli5 通俗化——检索本身不变。

**MCP 接入**。`mcp/` 目录是一个 Go 语言实现的 MCP 服务器，Claude Desktop 的 `.mcpb` 包即由它构建，把研究能力以 `research` 工具的形式暴露给任何支持 MCP 的客户端。

**测试与供应链**。2700+ 测试，覆盖率门槛从 60% 提到 84%；CI 集成 OpenSSF Scorecard、Semgrep、OSV-Scanner 与构建来源证明；HTML 渲染器修复过存储型 XSS。MIT 协议，无追踪无遥测，研究数据全部留在本机。

---

## 五、局限性

| 局限 | 说明 |
|------|------|
| 平台依赖 | 免费通道依赖各平台的公开接口，接口变动会直接影响可用性——Reddit 公共 `.json` API 关停后，项目靠 keyless RSS + 页面抓取重建了免费通道，这类波动未来还可能发生 |
| X 覆盖窗口 | 官方 X API 默认只覆盖最近约一周（除非开发者项目有全档权限）；浏览器 cookie 方式免费但需要定期更新登录态 |
| API 成本 | ScrapeCreators 1 万次免费后按量付费；xAI、Perplexity Deep Research（约 $0.90/次）等均为付费通道 |
| 语言偏向 | 已支持 CJK 分词与希伯来语等非拉丁语言，但信号密度最高的仍是英文社区 |
| 合成质量 | 报告质量与宿主模型能力直接相关；无头模式的推理链自动降级到本地确定性兜底时，合成质量明显下降 |

---

## 六、与其他工具对比

| 工具 | 定位 | 信号来源 | 适合场景 |
|------|------|---------|---------|
| **last30days** | 社交证据检索 + Agent 合成 | 20 个数据源的真实互动、预测市场赔率、完整转写 | 深度研究、趋势发现、见面准备 |
| Perplexity | AI 问答引擎 | 索引网页与编辑内容 | 快速问答；last30days 也可把它作为可选源接入 |
| Google | 索引聚合 | SEO 与编辑排序 | 通用检索，弱在社区实时讨论 |
| RSS + AI 摘要 | 被动信息流 | 依赖订阅源 | 已有稳定信息源的读者 |

差异化在于： Perplexity 和 Google 回答"网上怎么说"，last30days 回答"人最近在说什么、押注什么"——互动数据和真金白银的赔率是前两者拿不到的信号。

---

## 七、版本演进

| 版本 | 时间 | 里程碑 |
|------|------|--------|
| v1.0.0 | 2026-01 | 首个正式版 |
| v2.9.4 | 2026-03-06 | 2.x 线终点 |
| v3.0.0 | 2026-04-11 | 引擎重构：搜索前大脑、Best Takes、跨源聚类、单趟对比、GitHub 源（架构出自 @j-sperling） |
| v3.11.x | 2026-07 | 自 5 月 v3.3 公告以来合并 175 个 PR，其中 122 个来自 52 位社区贡献者 |
| v3.25.0 | 2026-09-18 | 本文口径版本 |

v2 时代的评分是纯启发式：Reddit 条目按 `0.50×log1p(赞) + 0.35×log1p(评论) + 0.05×(好评率×10) + 0.10×log1p(顶评)` 计算参与度，总分再按相关性 0.45、新鲜度 0.25、参与度 0.30 加权；Polymarket 用语义 30%、成交量 30%、流动性 15%、价格变动 15%、竞争度 10% 的五因子加权。v3 换成"LLM 评审 + 实体 grounding + 速度主导"的混合体系后，这些公式已整体退役。

这条演进线也解释了项目的测试策略：2026-04 的 v3.0.0 跑通 852 个测试，半年后测试数增长到 2700+——多源爬取系统的回归风险集中在平台接口变动上，测试密度就是它的保费。

---

## 八、参考资源

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | https://github.com/mvanhorn/last30days-skill |
| 运行时契约（SKILL.md） | skills/last30days/SKILL.md |
| 配置参考 | CONFIGURATION.md |
| 搜索机制详解 | docs/how-search-works.md |
| JSON 导出规范 | docs/reference/json-export.md |
| ScrapeCreators | https://scrapecreators.com |

---

## 参考来源与口径说明

- **版本锚点**：v3.25.0（2026-09-18 发布）。stars 62,628、forks 5,453、MIT 协议、最近推送 2026-09-20，均读自 GitHub API（2026-09-22）。
- **机制描述**：检索/评分/doctor/监控各节对照仓库现行源码（`lib/relevance.py`、`lib/rerank.py`、`lib/polymarket.py`、`scripts/watchlist.py`）与官方文档（README、CONFIGURATION.md、SKILL.md、docs/how-search-works.md）；评分权重、超时与默认值均为源码读数，非转述。
- **历史口径**：v2.9.4 评分公式与五因子权重对照该版本 tag 的 `scripts/lib/score.py`、`scripts/lib/polymarket.py` 原文；v2.9.x 止于 v2.9.4，其后直接进入 v3.0.0。
- **示例数据**：3.4 节调用示例为语法演示；Dor Brothers 与 OpenClaw/Hermes/Paperclip 例句取自 SKILL.md 与 README 原文。文中未标注来源的具体运行数字一律不写。
