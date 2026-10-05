---
title: "TrendRadar 拆解：热点聚合、AI 筛选与多渠道推送如何拼成一条零成本流水线"
slug: trendradar-54k-stars-hot-news-assistant
github_repo: "sansan0/TrendRadar"
source_key: "gh:sansan0/TrendRadar"
date: "2026-04-22T15:50:00+08:00"
lastmod: "2026-10-03T00:00:00+08:00"
description: "对照 sansan0/TrendRadar 源码与 README（v6.10.0，MCP v4.1.0）拆解 TrendRadar：newsnow 聚合 11 个热榜平台，关键词与 AI 双轨筛选，timeline 调度分时段切换策略，10 个推送渠道，以及一个只读本地新闻库的 MCP 服务。"
categories: ["技术笔记"]
tags: ["MCP", "RSS", "GitHub Actions"]
---

# TrendRadar 拆解：热点聚合、AI 筛选与多渠道推送如何拼成一条零成本流水线

## 先给判断

TrendRadar 不生产新闻，也不训练模型。它做的事是把三个现成件组装成一条流水线：数据来自 [newsnow](https://github.com/newsnext/newsnow) 项目的聚合 API，智能来自 LiteLLM 接入的任意大模型，托管来自 GitHub Actions 或 Docker——它自己专注的是中间那层分发逻辑：什么时间、按什么策略、把哪些新闻、发到哪个渠道。

这个定位决定了它的性格。README 里"最快 30 秒部署"的底气来自 Use this template 加一组 GitHub Secrets，全程不碰服务器；代价是数据链路依附于第三方——newsnow 的公共 API 挂了或者限流，热榜就断供（项目自己也承认这点，在 README 里请求用户"合理控制推送频率，勿竭泽而渔"）。它适合"我要按自己的兴趣重构热点分发"的人，不适合想要独家信息源或者毫秒级时效的场景——热榜本身就是平台排好序的二手信息。

## 项目坐标（2026-10-03 核对）

| 字段 | 值 |
|------|------|
| 仓库 | [sansan0/TrendRadar](https://github.com/sansan0/TrendRadar)，分支 `master`，建于 2025-04-28 |
| Stars / Forks | 62,641 / 24,885（GitHub API 当日读数） |
| 版本 | v6.10.0（2026-06-19 发布），config schema 2.4.0 |
| MCP 模块 | 独立版本线，当前 mcp-v4.1.0 |
| License | GPL-3.0 |
| 语言 | Python（约 1.30 MB，占绝对主体），HTML、Shell、Dockerfile 为辅 |
| 官网 | [trendradar.sandev.cc](https://trendradar.sandev.cc) |
| Docker 镜像 | `wantcat/trendradar`（推送服务）、`wantcat/trendradar-mcp`（AI 分析，可选） |

版本主线从 v3.0.0（2025-10）走到 v6.10.0（2026-06），八个月里完成了 v3 到 v6 四次大版本升级，功能版几乎月月都有。读它的更新日志能看出一条主线：先把"抓新闻、推通知"做稳（v2.x），再补存储和 RSS（v4.x），然后加 AI 能力（v5.x），最后把调度统一成一套配置（v6.0.0，伴随一次 Breaking Change——旧版 `push_window`/`analysis_window` 配置不再兼容）。MCP 则单独一条版本线，从 2025-10 的 v1.0 到现在的 v4.1，节奏与主程序解耦。

## 系统地图：采集、筛选、分发三条链路

```text
采集                筛选                      分发
─────────          ─────────                ─────────
newsnow API ─┐                               ┌→ 飞书 / 钉钉 / 企业微信
（11 个热榜） ├→ 汇合入库 ─→ 关键词匹配 ─┐     ├→ Telegram / 邮件 / Slack
RSS/Atom  ───┘   （SQLite      AI 智能筛选 ─┼→ ntfy / Bark / 通用 Webhook
                  或 S3）        （二选一）  │   ├→ HTML 报告 / 邮件网页版
                          ↑                  └→ MCP 服务（AI Agent 读取）
                    timeline.yaml
                 （何时采集/推送/分析）
```

三条链路职责不同，容易搞混的地方也在这里：

- **采集链**解决"数据从哪来"：热榜走 newsnow 的 API，RSS 自己抓，两边格式统一成"标题 + 平台 + 排名"。
- **筛选链**解决"发什么"：关键词匹配和 AI 智能筛选二选一，调度系统还能按时段切换。
- **分发链**解决"何时发、发到哪"：三种推送模式控制重复度，10 个渠道各自适配格式，超长消息按渠道字节限制拆分。

下面逐段拆。

## 采集：热榜靠 newsnow，长尾靠 RSS

热榜部分默认监控 11 个平台：今日头条、百度热搜、华尔街见闻、澎湃新闻、bilibili 热搜、财联社、凤凰网、贴吧、微博、抖音、知乎。每条源在 `config/config.yaml` 里三项配置：`id`（平台标识，勿改）、`name`（显示名，可改）、`expected_domain`（域名安全校验）。

`expected_domain` 是 v6.9.0 加的防御性设计：校验返回数据里的链接是否为 HTTPS 且域名匹配，不匹配就丢弃该平台数据并警告。配置注释里写得很直白——只要 api_url 不是你自己部署的实例，都推荐配上，防的是链接劫持和数据篡改。另一个值得注意的配置是 `api_url`：可以指向自部署的 newsnow 实例，把数据命脉收回来。

RSS 是 v4.5.0 加入的第二条采集路。它和热榜走同一套关键词匹配和推送格式，默认配置里就带着 Hacker News、阮一峰的网络日志、雅虎财经三个示例源。RSS 源有独立的新鲜度过滤（`freshness_filter.max_age_days`，默认只推 1 天内的文章，可按单源覆盖），防止更新慢的博客反复推送旧文。

两条路的分工：热榜覆盖"大家都在看什么"，RSS 覆盖"我认定的信息源在发什么"。一个横向，一个纵向。

## 筛选：关键词和 AI 双轨，坏了自动切回

筛选是 TrendRadar 最值得拆的部分，因为它给了两种思路完全不同的机制，并且允许按时段混用。

### 关键词轨：frequency_words.txt

关键词文件有自己的小语法，分两个区：

```text
[GLOBAL_FILTER]        全局过滤区：命中即排除，与词组无关
震惊                    过滤标题党

[WORD_GROUPS]          词组定义区：空行分隔词组，组内关键词是"或"关系
[组别名]               给整组命名
/正则/                 正则匹配，自动忽略大小写
关键词 => 别名          换个显示名
```

这套语法没有门槛，也绝不消耗 token。问题在于关键词匹配理解不了意图——"AI 创业"和"AI 裁员"都会命中"AI"。

### AI 轨：ai_interests.txt

v6.5.0（2026-03）加入的 AI 智能筛选把"选新闻"变成两个阶段：先让 AI 从兴趣描述里提取结构化标签，再对每条新闻按标签批量打分。兴趣描述就是一段日常语言，写在 `config/ai_interests.txt` 里（自定义文件放 `config/custom/ai/` 目录，可放多份独立使用）：

```text
我想看 AI 和新能源相关新闻

具体来说：
- AI 行业动态：大模型发布、AI 创业公司、技术突破
- 新能源汽车：特斯拉、比亚迪、宁德时代
- 不看：AI 娱乐化内容、游戏 AI
```

关键配置在 `config.yaml` 的两段里：

```yaml
filter:
  method: ai          # keyword（默认，不耗 token）| ai（灵活但每次运行消耗 token）

ai_filter:
  min_score: 0.7      # 推送最低分数阈值（0.0~1.0），推荐 0.5~0.7 起步
  batch_size: 200     # 每批发给 AI 的标题数
  reclassify_threshold: 0.6   # 兴趣变更时，全量重分类的触发阈值
```

三个设计值得单独说：

**自动回退**。AI 筛选失败时直接切回关键词匹配，推送不中断（源码 `trendradar/__main__.py` 里能找到这行日志：`AI 筛选失败: …，回退到关键词匹配`）。这条保底让 AI 轨敢于用在生产——API 限流、模型抽风都不会让你错过新闻，只是筛选精度降级。

**省钱机制**。已分析过的新闻不会重复消耗 token；兴趣描述改了之后，AI 先对比新旧描述的变化幅度，小改动只增量更新受影响的标签，超过 `reclassify_threshold` 才全量重分类。

**每时段独立**。调度系统的每个时间段可以单独指定 `filter_method` 和兴趣文件——早上用科技词库做关键词快筛，晚上换成金融兴趣描述做 AI 深筛，同一个部署两条口味。

## 调度：timeline.yaml 把"什么时候做什么"收进一套配置

v6.0.0 之前，推送窗口和分析窗口是两个独立配置；v6.0.0 把它们合并进 `timeline.yaml`，配 `schedule.preset` 选用。内置五种预设：

| 预设 | 行为 |
|------|------|
| `always_on` | 全天候，有新增即推送 |
| `morning_evening`（默认推荐） | 全天推送 + 晚间当日汇总 |
| `office_hours` | 工作日三段式（到岗→午间→收工），周末增量 |
| `night_owl` | 午后速览 + 深夜全天汇总 |
| `custom` | 完全自定义 |

以默认的 `morning_evening` 为例，能看清这套配置的三层结构：

```yaml
morning_evening:
  default:                  # 不命中任何时段时的兜底行为
    collect: true
    push: true
    report_mode: "current"  # 推当前在榜
  periods:                  # 特殊时段：晚间汇总
    evening_summary:
      start: "20:00"
      end: "22:00"
      report_mode: "daily"  # 切换为当日全部新闻
      ai_mode: "daily"
      once:
        analyze: true       # 窗口内只分析一次
        push: true
  day_plans:                # 把时段组装成一天的安排
    all_day:
      periods: ["evening_summary"]
  week_map:                 # 周一到周日各用哪个日计划
```

`periods` 定义时间窗，`day_plans` 把窗口组装成一天，`week_map` 决定一周七天各用哪套安排——工作日和周末差异化就是在这里做的。时段有重叠时系统直接报错，不让你带着冲突配置跑。

和调度配合的还有推送模式（`report.mode`），三个值对应三种重复度：

| 模式 | 行为 | 适合 |
|------|------|------|
| `daily` | 推当日所有匹配，含之前推过的 | 要完整日报的人 |
| `current` | 推当前在榜的，持续在榜每次都出现 | 看榜单趋势的人 |
| `incremental` | 只推新增，零重复，无新增不推 | 投资者、不想被打扰的人 |

## 分发：10 个渠道，三种配置姿势

推送渠道共 10 个：企业微信（`msg_type: text` 可走个人微信应用推送）、飞书、钉钉、Telegram、邮件（SMTP）、ntfy、Bark、Slack、通用 Webhook（`payload_template` 支持 `{title}`/`{content}` 占位符，可对接 Discord、IFTTT 等）。可以同时启用多个，多账号用分号分隔。

同一个系统，配置密钥的姿势有三种，取决于部署方式：

- **GitHub Actions 部署**：密钥进仓库 Secrets，名称严格固定（如 `FEISHU_WEBHOOK_URL`、`AI_API_KEY`），config.yaml 里留空即可。
- **Docker 部署**：敏感信息写 `docker/.env`，环境变量覆盖 `config.yaml` 的对应配置（v3.0.5+ 起的机制，优先级：环境变量 > config.yaml），且 `.env` 不进 git。
- **本地运行**：直接填 `config/config.yaml`。

除了推送渠道，每次运行还会在 `output/` 生成一份 HTML 报告（浏览器打开解锁宽屏、暗色模式、实时搜索、Markdown 导出等增强，邮件客户端里仍是基础排版）。托管方式见后文部署一节。

推送侧还有一层容易被忽略的适配，主要体现在 MCP 的通知直推链路上：各渠道对消息体大小限制不同，超长内容按渠道上限自动拆批（飞书 30KB、钉钉 20KB 等，上限读自 config.yaml），Markdown 自动转成各渠道的格式。这套能力是 mcp-v4.0.0 做"AI 消息直推"时补齐的，批次处理函数直接复用主程序的核心模块。

## AI 能力三件套，共用一个模型配置

TrendRadar 的 AI 功能有三件：筛选（v6.5.0）、分析（v5.0.0）、翻译（v5.2.0）。三件套共享 `config.yaml` 里同一个 `ai` 配置段：

```yaml
ai:
  model: "deepseek/deepseek-v4-flash"   # LiteLLM 格式：提供商/模型名
  api_key: ""                            # 建议用环境变量 AI_API_KEY
  fallback_models: []                    # 备用模型，主模型失败自动切换
```

模型名是 LiteLLM 格式（`提供商/模型名`），这意味着 DeepSeek、OpenAI、Gemini、Anthropic、本地 Ollama 等 100+ 提供商开箱即用；不在列表里的服务商，只要接口兼容通用格式，加 `openai/` 前缀配 `api_base` 就能接。默认模型是 `deepseek/deepseek-v4-flash`——对一个每天定时跑、按条计费的筛选任务来说，选便宜模型是合理的工程默认值。

三个功能各有分工：筛选决定"这条推不推"，分析生成"这些热点意味着什么"（提示词可在 `config/ai_analysis_prompt.txt` 自定义），翻译解决"海外 RSS 源看不懂"（v6.10.0 起大量标题自动分批翻译，防单次请求超限）。分析的范围可以和推送独立——推送只发新增免打扰，AI 却分析当天全量看趋势。

## MCP：给 AI Agent 一个只读新闻库的入口

这是 TrendRadar 最容易被误解的部分。它提供的是标准 MCP（Model Context Protocol）服务（基于 FastMCP 2.0，应用名 `trendradar-news`），接入 Cherry Studio、Cursor、VS Code（Cline/Continue）等客户端后，可以用自然语言查新闻、做分析。但有一个前置认知必须建立：

**MCP 服务分析的是本地已积累的数据（`output` 目录），不是实时网络查询。** 项目自带 2025-12-21 至 12-27 一周的测试数据供快速体验；要分析最新热点，得先让主程序跑起来积累数据。查"最近 7 天特斯拉的热度变化"没问题，问"现在微博在吵什么"不行。

服务支持两种传输模式：STDIO（推荐，配置一次持续可用，入口 `python -m mcp_server.server`）和 HTTP（`http://localhost:3333/mcp`，每次使用前手动启动；Docker 部署对应独立的 `wantcat/trendradar-mcp` 镜像，只监听本地回环地址）。

当前版本注册了 27 个工具、4 个资源，按用途分五类：

| 类别 | 代表工具 |
|------|---------|
| 数据查询 | `get_latest_news`、`get_news_by_date`、`search_news`、`get_trending_topics`、`list_available_dates` |
| 趋势分析 | `analyze_topic_trend`、`analyze_sentiment`、`find_related_news`、`compare_periods`、`generate_summary_report` |
| RSS | `get_latest_rss`、`search_rss`、`get_rss_feeds_status` |
| 系统与配置 | `get_current_config`、`get_system_status`、`trigger_crawl`、`sync_from_remote` |
| 通知直推 | `send_notification`、`get_channel_format_guide` |

`send_notification` 是 mcp-v4.0.0 的招牌：让 AI 写好的内容一键推送到全部渠道，`get_channel_format_guide` 则告诉 AI 每个渠道支持什么格式、有什么限制。组合起来是一条完整链路——让 Agent 查数据、写分析、自己发出去。MCP 的版本线从 2025-10 的 v1.0 走到 2026-02 的 v4.0，再到当前的 v4.1，独立于主程序演进，是整个项目里迭代最快的模块。

## 一次任务的完整流转

把前面的机制串起来，看默认 `morning_evening` 预设下的一天（假设 `filter.method: ai`，推送渠道配了飞书）：

1. **采集**：调度系统按 timeline 的节奏调 newsnow API 拉取 11 个平台热榜，同时抓取 RSS 源；每个平台先过 `expected_domain` 域名校验，不合格的数据整批丢弃。结果写入本地 SQLite（Docker 环境）。
2. **筛选**：新标题先由 AI 提取的标签做批量打分；上周已经分析过的新闻不再计费。某条"宁德时代扩产"的标题拿到 0.82 分，超过 `min_score: 0.7`，进入推送队列；一条"某明星 AI 数字人代言"0.31 分，被拦下。
3. **推送**：队列内容按关键词/标签分组，Markdown 渲染成飞书卡片，超 30KB 自动拆批，推到飞书群；同时在 `output/` 生成当天 HTML 报告。
4. **晚间 20:00**：进入 `evening_summary` 时段，`report_mode` 切到 `daily`，AI 对当天全量新闻做一轮汇总分析（窗口内只跑一次），和当日全部匹配新闻一起推最后一条。
5. **随时**：打开 Cherry Studio 问"本周比亚迪的热度拐点在哪天"，Agent 调 `analyze_topic_trend` 读本地库回答；你若满意它的总结，让它自己 `send_notification` 推给群里。

中途任何一步 AI 调用失败，筛选切回关键词、推送照常发出——降级的是精度，不是可用性。

## 部署选型与适用边界

三种部署方式的取舍很清晰：

| 方式 | 数据存哪 | 适合 | 注意 |
|------|---------|------|------|
| Docker（推荐） | 本地 SQLite | 有服务器、NAS 或长开的电脑 | 双镜像按需组合，MCP 服务可选 |
| GitHub Actions | 远程 S3 兼容存储（R2/OSS/COS） | 没有服务器，白嫖 GitHub 资源 | 需配云存储才有完整体验；**必须用 Use this template，不要 Fork**（Fork 可能运行异常，见 Issue #606）；原"Actions 自动存储到仓库"方案已因负载问题下线 |
| 本地 uv | 本地 SQLite | 开发调试 | `uv run python -m trendradar`，uv 自动管理 Python |

网页报告是部署之外的低成本增值：每次运行在根目录生成 `index.html`，托管到 Cloudflare Pages 或 GitHub Pages 就有了在线阅读页（前者国内访问更快，配 3 个 Secrets 后由 Actions 自动推送）。配套的可视化配置编辑器（[sansan0.github.io/TrendRadar](https://sansan0.github.io/TrendRadar/)）能在网页表单里改完 config.yaml、frequency_words.txt、timeline.yaml 再导出，免掉手写 YAML。

**适合用**：想按兴趣监控舆情 / 行业动态的投资者、自媒体人、做品牌追踪的人；不想为个人新闻聚合维护一台服务器的人；想给自己的 AI Agent 接一个新闻数据工具的人（MCP）。

**不适合或要想清楚**：需要独家或第一手信息源——它的数据上限就是热榜和你订阅的 RSS；对推送时效有硬要求——热榜更新节奏和 Actions 的定时触发决定了它做不到实时；介意数据出境——GitHub Actions 模式下热榜数据和推送凭据都在 GitHub 云上，敏感场景选 Docker 本地跑。

**起步路径**：先用 Docker 起主服务 + 配一个飞书或 ntfy 渠道，`frequency_words.txt` 写两三个词组看推送效果；一周后再决定是否开 AI 筛选（要花 token 钱）、是否部署 MCP 镜像、是否把报告托管到 Pages。

## 结尾判断

TrendRadar 的价值不在任何单项技术——热榜 API、LiteLLM、MCP 都是别人的轮子——而在它把"个人级舆情监控"的成本压到了接近零：一次模板复制，一段自然语言兴趣描述，剩下的交给 GitHub 的免费算力。本文初版成稿时（2026-04）它还是 5.4 万 star，如今已到 6.2 万，半年 8 千的增长说明这个需求此前被低估了。

它也有明显的路径依赖：数据链路系于 newsnow 一家，公共 API 的善意随时可能变成瓶颈（自部署是唯一的保险）；v6.0.0 那次 Breaking Change 也提醒用户，这个项目迭代快、配置面大，跟着升级时要读更新日志。对这些有预期之后，把"兴趣 → 筛选 → 推送"这条链路做得最完整、且免费就能跑通的开源方案里，它是目前我看过完成度最高的一个。

## 参考

- 仓库：<https://github.com/sansan0/TrendRadar>（v6.10.0，mcp-v4.1.0，2026-10-03 核对）
- 官网与文档：<https://trendradar.sandev.cc>
- 可视化配置编辑器：<https://sansan0.github.io/TrendRadar/>
- 数据源项目：[newsnext/newsnow](https://github.com/newsnext/newsnow)
- MCP 协议：<https://modelcontextprotocol.io/>
