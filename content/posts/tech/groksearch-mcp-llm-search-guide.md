---
title: "GrokSearch 拆解：它没让搜索变聪明，只是让 Claude 少了别的选择"
date: "2026-05-11T20:25:00+08:00"
lastmod: "2026-09-19T00:00:00+08:00"
slug: "groksearch-mcp-llm-realtime-search"
github_repo: "GuDaStudio/GrokSearch"
source_key: "gh:GuDaStudio/GrokSearch"
description: "按 main 分支源码逐行拆解 GuDaStudio/GrokSearch：实际注册 13 个 MCP 工具而 README 写八个、信源剥离与进程内 LRU 缓存的半径、写进 permissions.deny 的确切权限名、TAVILY_ENABLED 为什么不起作用、extra_sources 全给 Firecrawl 的那行算术，以及 README 对比截图能证明什么、不能证明什么。"
draft: false
categories: ["技术笔记"]
tags: ["MCP", "Claude Code", "Grok", "AI Agent", "Python"]
hiddenFromHomePage: true
---

## 一句话判断

GrokSearch 通常被介绍成"给 Claude 接上 Grok 的实时搜索"。把 `main` 分支读完——10 个 Python 文件、2244 行，其中 `server.py` 独占 891 行——会发现它真正改动的三处都不在检索质量上：把 Claude Code 官方的 `WebSearch` 和 `WebFetch` 写进项目权限文件的 `deny` 表；在工具描述里写死调用顺序（`web_search` 的 description 第一句是 `Before using this tool, please use the plan_intent tool`）；把 Grok 回答尾部的信源剥出来存进服务端，只把正文交回模型。

检索本身仍然整个发生在 Grok 那一侧，形状是一次 `POST {GROK_API_URL}/chat/completions`，流式返回，system 提示词（prompt）是仓库里那段要求"每个论断后面必须跟一个引用"的长文本。这个服务器做的事情，是把"要不要联网查"从模型每轮自己权衡的决定，改成环境里已经没剩几个选项的默认路径。

所以本文的重点放在它用什么手段搭出这层约束、这些手段各自的失效边界在哪，以及逐条标出的 README 与代码不一致之处——它们会直接影响安装决策。

## 目录

- [一句话判断](#一句话判断)
- [系统地图：四条主线，十三个工具](#系统地图四条主线十三个工具)
- [搜索主线：一次 web_search 的六个动作](#搜索主线一次-web_search-的六个动作)
- [抓取主线：Tavily 和 Firecrawl 分工不对称](#抓取主线tavily-和-firecrawl-分工不对称)
- [规划主线：六个 plan_* 一次模型都不调](#规划主线六个-plan_-一次模型都不调)
- [三处约束手段](#三处约束手段)
  - [deny 表的确切形状](#deny-表的确切形状)
  - [工具描述里的调用顺序](#工具描述里的调用顺序)
  - [信源不进正文](#信源不进正文)
- [一个任务的完整流转](#一个任务的完整流转)
- [安装：先确认自己装的是哪个分支](#安装先确认自己装的是哪个分支)
  - [两条安装命令指向不同语义](#两条安装命令指向不同语义)
  - [配置示例](#配置示例)
- [环境变量：14 个，其中一个不起作用](#环境变量14-个其中一个不起作用)
  - [重试、超时与镜像站兼容](#重试超时与镜像站兼容)
  - [日志、配置落点与版本锚点](#日志配置落点与版本锚点)
- [常见故障与排查](#常见故障与排查)
- [README 那张对比图能说明什么](#readme-那张对比图能说明什么)
- [边界：什么时候不值得装，以及采用顺序](#边界什么时候不值得装以及采用顺序)
- [五个自测题](#五个自测题)
- [下一步可以读哪几段代码](#下一步可以读哪几段代码)
- [资料口径与维护指引](#资料口径与维护指引)
- [参考资料](#参考资料)

## 系统地图：四条主线，十三个工具

四条主线的边界不同，混着读会误判这套工具的能力。搜索、抓取、规划各占一节，配置与控制散在安装与排查两节里。

| 主线 | 工具 | 是否出网 | 后端 |
|------|------|----------|------|
| 搜索 | `web_search`、`get_sources` | 是 | Grok 兼容端点；`extra_sources` 大于 0 时并行多打一次 Tavily 或 Firecrawl 检索 |
| 抓取 | `web_fetch`、`web_map` | 是 | Tavily Extract 与 Tavily Map；只有前者有 Firecrawl 托底 |
| 规划 | `plan_intent`、`plan_complexity`、`plan_sub_query`、`plan_search_term`、`plan_tool_mapping`、`plan_execution` | 否 | 进程内状态机，一次网络请求都不发 |
| 配置与控制 | `get_config_info`、`switch_model`、`toggle_builtin_tools` | 只有 `get_config_info` 出网 | 读写 `~/.config/grok-search/config.json` 与项目 `.claude/settings.json` |

README 的中英文版本都把工具数写成"八个"（中文版第 159 行、英文版第 161 行），并在第 235 / 237 行用一个 `search_planning` 小节概括规划能力。代码实际注册的是 13 个，`@mcp.tool` 在 `server.py` 里出现 13 次，六个 `plan_*` 各自独立：

```bash
# 在仓库根目录自查
grep -c '@mcp.tool' src/grok_search/server.py          # 13
grep -o 'name="[a-z_]*"' src/grok_search/server.py | sort -u
```

这条差异不是文档瑕疵而已：`search_planning` 这个名字在服务端根本不存在，模型按 README 去调它会直接失败；反过来，真正的规划入口 `plan_intent` 在 README 中英文两版里一次都没出现过。规划链的其余五站都要求先拿到它返回的会话号。

## 搜索主线：一次 web_search 的六个动作

`web_search` 只有四个参数：`query`（查询语句）、`platform`（聚焦平台，如 `Twitter`）、`model`（本次请求临时换模型）、`extra_sources`（额外补充信源条数，默认 0）。服务端按顺序做六件事。

**一、校验模型。** 传了 `model` 时先用 `GET {GROK_API_URL}/models`（10 秒超时）拉一次可用列表并缓存；列表拿到了但里面没有这个 ID，直接返回 `无效模型: <model>`；列表拉不到就跳过校验，把值原样发出去。

**二、组装提示词。** system 是 `utils.py` 里的 `search_prompt`，要求写得很硬：先发散出 5 个以上角度并行搜、再挑至少 2 个角度深挖、每个论断后面跟一个 `citation_card`、没有参考来源就宁可不答，检索语言优先英文。user 内容 = 本地时间块 + 查询语句 + 平台附加句。

**三、注入时间。** 时间块是无条件拼上去的，形如 `[Current Time Context]` 加日期、中文星期、时刻、时区。这一步曾经是条件判断：2026-01-19 的 PR #7 引入 `_needs_time_context()`，用 24 个中文关键词加 21 个英文关键词（"最新""今天""recent"之类）决定要不要注入；2026-03-09 之后判断被去掉，函数留在 `providers/grok.py` 里没有任何调用点。README 仍在描述"自动检测时间相关关键词"。

**四、并行取数。** `extra_sources > 0` 时用 `asyncio.gather` 同时跑 Grok 与 Tavily/Firecrawl 检索。配额怎么分，决定 Tavily 会不会被用到：

```python
if has_firecrawl and has_tavily:
    firecrawl_count = round(extra_sources * 1)
    tavily_count = extra_sources - firecrawl_count
```

`round(n * 1)` 就是 `n`，于是 `tavily_count` 恒为 0——两把密钥都配了的时候，补充信源全部来自 Firecrawl，Tavily 的检索接口一次都不会被调用。只配其中一把时才会落到那一侧。

这不是设计意图。`main` 那个合并提交的说明正文里，v1.4.0 那一条写的是"Firecrawl 占 70% 配额、Tavily 占 30%"，同一条还把 `extra_sources` 的默认值记成 20；当前代码里乘数是 1、默认值是 0。中间过程被压进了一个 squash 提交，追不到改坏的落点，issue #46 只能报出现象。

**五、剥离信源。** Grok 返回的是一整篇带引用的 Markdown。`sources.py` 的 `split_answer_and_sources()` 按四种切法依次尝试，把回答与信源列表拆开：函数调用式（`sources(`、`citation_card(`）、Markdown 标题行（`Sources`、`参考资料`、`信源`、`引用`…）、`<details>` 块、尾部纯链接块。

但四种切法都要求引用先成块：函数调用式要求那个调用一直闭合到字符串结尾，`<details>` 式要求块后面不许再有任何正文，只有标题式允许标题块后面还有几句话。而 `search_prompt` 要的形状是引用散在句子之间，一把都对不上。把两种写法各喂一次这个函数就能看出错位：末尾整块的 `sources(citation_card(...), citation_card(...))` 切出 2 条、正文干净；同样两条引用内联到句子后面，切出 0 条，`citation_card` 原样留在 `content` 里，`sources_count` 报 0。也就是说 Grok 越照提示词写，信源越剥不出来。PR #37 与 PR #50 要补的都是这条缝。

**六、缓存并返回。** 返回结构只有三个字段，源码里就一行：

```python
return {"session_id": session_id, "content": answer, "sources_count": len(all_sources)}
```

`session_id` 是 `uuid4().hex` 的前 12 位。信源存进 `_SOURCES_CACHE`，一个 `max_size=256` 的进程内 LRU，**没有过期时间**。模型要查出处时拿这个会话号调 `get_sources`，换回 `sources` 列表（每项至少含 `url`，可能含 `title`、`description`、`provider`）。

把几十个 URL 从正文里挪走，是为了让上下文不被链接挤占，也让模型专注于转述结论而不是转述清单；代价是缓存半径只有一次进程生命周期加 256 次新搜索。`get_sources` 取不到时的错误串是 `session_id_not_found_or_expired`，其中 "expired" 属于误导：代码里没有任何时间过期逻辑，条目只会被容量顶掉或随进程重启消失。

还有一处容易漏看的：包 Grok 调用的 `_safe_grok()` 捕获所有异常并返回空字符串。Grok 端超时、5xx 重试耗尽、返回体解析不出内容，都会让 `web_search` "成功"返回一个 `content` 为空的对象，不带任何错误提示。issue #28、#42 和 PR #34 描述的现象不同，技术面都指向这里。

## 抓取主线：Tavily 和 Firecrawl 分工不对称

`web_fetch` 的降级链条与 README 一致：先 Tavily Extract，`POST {TAVILY_API_URL}/extract`，请求体 `{"urls": [url], "format": "markdown"}`，60 秒超时，读 `results[0].raw_content`；拿不到内容就转 Firecrawl Scrape，`POST {FIRECRAWL_API_URL}/scrape`，`formats: ["markdown"]`。

不对称发生在重试条件上。Firecrawl 这一跳会重试，但只对"请求成功而 markdown 为空"这一种情况重试，等待时间逐次加长：

```python
"waitFor": (attempt + 1) * 1500,   # 三次尝试依次等 1500 / 3000 / 4500 毫秒
```

次数取 `GROK_RETRY_MAX_ATTEMPTS`（默认 3）。请求本身抛异常时立刻 `return None`，不再重试——降级链条在异常路径上只有一跳。

两条失败分支的返回值都是中文字符串而不是结构化错误码：两把密钥都没配返回 `配置错误: TAVILY_API_KEY 和 FIRECRAWL_API_KEY 均未配置`；配了但都没取到返回 `提取失败: 所有提取服务均未能获取内容`。模型看到的是自然语言，能不能据此改变策略取决于它读不读得懂。

`web_map` 与 Firecrawl 完全无关，只走 Tavily Map（`POST {TAVILY_API_URL}/map`）：

| 参数 | 取值范围 | 默认 |
|------|----------|------|
| `max_depth` | 1–5 | 1 |
| `max_breadth` | 1–500 | 20 |
| `limit` | 1–500 | 50 |
| `timeout` | 10–150 秒 | 150，客户端超时再加 10 秒 |

没配 Tavily 密钥时它直接返回一句配置提示，不会像 `web_fetch` 那样尝试别的出路。README 的架构简图把 `web_fetch` 画成双服务、`web_map` 画成单服务，这一点是准确的。

`web_fetch` 的描述自称 "Maintains 100% content fidelity without summarization"，与它直接回传 `raw_content` 的实现相符。这也意味着抓取长度完全不受控：一整篇文档会原样进上下文。工具描述同时承认抓不到需要执行 JavaScript 才出现的内容。

顺带一提，Grok 侧其实还有一条自己的抓取路径：`providers/grok.py` 的 `fetch()` 配一份要求"零删减"的长提示词。它在 `main` 里没有任何调用者，`describe_url()`、`rank_sources()`、`utils.py` 的 `format_extra_sources()` 同样只定义未接线。别按"可以让 Grok 直接读网页并摘要"来规划工作流，这条能力目前不存在。

## 规划主线：六个 plan_* 一次模型都不调

六个规划工具全部落到 `planning_engine.process_phase()`，读写一个进程内字典，不发网络请求。每个阶段该填什么，`planning.py` 里有一份 Pydantic 定义，`server.py` 里又把这些字段摊平成工具参数写在 `Annotated` 描述里。下表是摊平后的样子，最右一列是 `REQUIRED_PHASES`：`plan_complexity` 里报的等级决定哪几个阶段必须走完。

| 阶段 | 定义模型 | 参数描述里写明的要求 | 必需等级 |
|------|----------|----------------------|----------|
| 意图 | `IntentOutput` | 核心问题、查询类型（`factual` / `comparative` / `exploratory` / `analytical`）、时间敏感度、前提是否成立、歧义清单、待验证的外部分类 | 1 / 2 / 3 |
| 复杂度 | `ComplexityOutput` | 1–3 级，附估算的子查询数与调用总数 | 1 / 2 / 3 |
| 子查询 | `SubQuery` | 每个都要写 `goal`、`expected_output`，以及 `boundary`——描述里明写必须说明与兄弟子查询互斥，不能只复述所属领域 | 1 / 2 / 3 |
| 搜索词 | `SearchTerm` | 不超过 8 个词，只能绑定一个子查询 ID，带执行轮次 | 2 / 3 |
| 工具映射 | `ToolPlanItem` | 子查询到 `web_search` / `web_fetch` / `web_map` 的一一映射及理由 | 2 / 3 |
| 执行顺序 | `ExecutionOrderOutput` | 并行分组、串行序列、预计轮次 | 仅 3 |

要说清一件事：这些要求全在描述文字里，服务端不校验。`plan_intent` 签名里的 `query_type` 类型就是普通 `str`，填 `poetic` 也收；`planning.py` 那六个模型在运行时一次都没被实例化，`phase_data` 直接按字典存进会话。所以规划链提供的是"照着字段名想一遍"的推力，加上一份阶段完成度回执，质量仍然完全由模型自己负责。

等级 1 对应"1–2 次搜索就能收口"，2 是"3–5 次"，3 是"6 次以上"。等级由模型自己报，报 1 级就只用走完前三个阶段，因此这条链路无法证明自己被认真走过。

每调一次返回一份回执：`completed_phases`、`complexity_level`、`plan_complete`，没走完时附 `phases_remaining`，走完时附 `executable_plan`。子查询与工具映射两个阶段是累加语义（每次调用 append 一条，`is_revision=true` 才整表替换），搜索策略阶段会把多次调用的 `search_terms` 合并进同一个记录。

顺序约束在这里是真强制的：除 `plan_intent` 外的五个工具都先查 `planning_engine.get_session(session_id)`，查不到就返回 `Session '<id>' not found. Call plan_intent first.`。但**规划完成与否并不影响 `web_search`**——它不检查任何计划状态，唯一的推动力是 description 里那句"先用 `plan_intent`"。

这套设计的实际作用是把"先想清楚再搜"变成一串带类型、带必填项、带阶段回执的调用，服务器只保证字段没填完，填得对不对仍然由模型自己产出。issue #38 提的正是这个疑问：模型本来就会规划，六个工具多了什么。从代码看，它多出来的是可检查的中间状态，不是新的规划能力。

规划会话的字典没有淘汰机制，`PlanningEngine._sessions` 是个普通 `dict`，进程活多久就留多久。长跑的 MCP 服务会稳定积内存，与信源缓存那 256 条上限的行为完全不同。

## 三处约束手段

### deny 表的确切形状

`toggle_builtin_tools` 做的方法很简单：找到项目根的 `.claude/settings.json`，把两个权限名追加进 `permissions.deny`。

```json
// .claude/settings.json（由 toggle_builtin_tools 写入，保留文件里原有的其它键）
{
  "permissions": {
    "deny": ["WebFetch", "WebSearch"]
  }
}
```

写进去的是 `WebFetch`、`WebSearch` 这两个权限名，首字母大写、无连字符。转述成 `web-search`、`web-fetch` 是无效规则，Claude Code 不会据此拦下任何调用。

三种 `action`：`on` / `enable` 追加并落盘，`off` / `disable` 从 `deny` 里移除并落盘，其它值（含默认 `status`）只报告不改文件。返回体里带 `blocked`、`deny_list`、`file`、`message` 四个字段，`file` 直接告诉你写去哪了。

项目根的定位方式是 `Path.cwd()` 逐级向上找存在 `.git` 的目录。在一个不是 Git 仓库的目录里运行，循环会一路走到文件系统根，然后把 `.claude/settings.json` 写到根目录上去——这个函数没有 `try`，写不进去就抛原始异常，模型侧看到的是一条 MCP 工具调用失败。也就是说，这套路由控制只在 Git 工作区内按预期工作，返回体里的 `file` 字段是判断它到底挑中了哪一层的唯一线索。

为什么这一招比提示词可靠：`deny` 生效的位置是 Claude Code 的权限层，与模型本轮想不想用无关。它不消除模型"凭记忆作答"的倾向，只是让那条倾向不再能通过内置工具得到满足。

### 工具描述里的调用顺序

工具描述本身就是文档。五个抓取与控制类工具（`web_fetch`、`web_map`、`get_config_info`、`switch_model`、`toggle_builtin_tools`）的 description 都带 `Key Features` 与 `Edge Cases & Best Practices` 两段，把使用前提和局限直接写进工具签名；六个 `plan_*` 的 description 各是一行阶段说明，其中 `plan_intent` 那行写明了必经流程：`plan_intent → plan_complexity → plan_sub_query(×N) → plan_search_term(×N) → plan_tool_mapping(×N) → plan_execution`；剩下 `web_search` 与 `get_sources` 用自由文本描述返回字段，其中 `web_search` 开篇那句 "Before using this tool, please use the plan_intent tool" 是全仓库唯一一处把规划和检索连起来的文字。

这类文字是提示，不是校验。同一个仓库里有个反例能说明作者自己清楚这条界线：`web_search` 的 `model` 参数会对着 `/models` 列表校验，而 `switch_model` 完全不校验，直接把值写进配置文件，工具描述里自己写着 `Invalid model IDs may cause API errors in subsequent requests`（模型 ID 无效时，报错发生在后续那次应用程序接口调用上，而不是切换的那一刻）。切换默认模型时要自己去 `get_config_info` 看可用列表。

### 信源不进正文

`web_search` 只报 `sources_count`，URL 一概留在服务端；出处要不要拿回来由模型决定，服务端不会替你把引用补上。把这一层和上面的切分失败合起来看，会得到一个更麻烦的组合：如果 Grok 把 `citation_card` 内联在句子之间，这些引用既没进缓存（于是 `sources_count` 为 0），又留在 `content` 里占上下文——此时"`sources_count: 0`"并不等于"没有来源"。读结果时先分辨是哪一种，再决定要不要追问出处。

## 一个任务的完整流转

把上面四条线串起来，看一次带时效的提问在系统里实际经过什么。假设你在 Claude Code 里问："FastAPI 最新稳定版改了什么，和我项目里那版差在哪？"

1. 模型按 `web_search` 描述的要求先调 `plan_intent`，填 `core_question`、`query_type`（`comparative`）、`time_sensitivity`（`recent`），拿回一个 12 位十六进制的 `session_id`。
2. 调 `plan_complexity`，`level` 填 1，同时填 `estimated_sub_queries` 与 `estimated_tool_calls`。回执里 `phases_remaining` 只剩 `query_decomposition`。
3. 连调两次 `plan_sub_query`，分别对应"最新版变更"和"本地版本差异"，每个都带 `goal`、`expected_output` 与 `boundary`。回执变成 `plan_complete: true` 并附 `executable_plan`。
4. 调 `web_search`，`extra_sources` 保持 0。一次 `POST /chat/completions`，Grok 在 `search_prompt` 的约束下做广度与深度检索，返回整篇带 `citation_card` 的回答；服务端剥出信源、缓存，只回 `{session_id, content, sources_count}`。
5. 你要看出处，模型拿第 4 步那个新的 `session_id` 调 `get_sources`，换回按 URL 去重后的列表。
6. 你要求核对官方发布说明，模型调 `web_fetch` 打那一页的 URL，Tavily Extract 回 `raw_content`；这一页 Tavily 取不到时 Firecrawl 顶上。
7. 整个过程里，如果模型试着调官方 `WebSearch`，它会在权限层被直接拦掉——`deny` 表一节里那两个权限名已经写进了当前项目的 `.claude/settings.json`。

规划阶段与检索调用之间没有任何服务端关联：`web_search` 不知道这些查询出自哪份计划，计划也不会因为写完就被执行。

## 安装：先确认自己装的是哪个分支

### 两条安装命令指向不同语义

README 教的是从 `grok-with-tavily` 分支装，而仓库默认分支是 `main`，两者是两个不同提交。差异只有两个文件、65 增 21 删，改的恰好是 `README.md` 与 `config.py`——也就是说搜索、抓取、规划的全部代码行为一致，**不一致的只有配置派生**。

`grok-with-tavily`（提交说明 v1.9.1，2026-03-09 10:49）保留一个单密钥模式：只配 `GUDA_API_KEY` 时，Grok 地址自动派生成 `https://code.guda.studio/grok/v1`，Tavily 与 Firecrawl 的地址与密钥同时指向该站点的 `/tavily` 与 `/firecrawl`，三服务共用同一把密钥；默认模型是 `grok-4.20-beta`。

`main`（同日 11:22 的合并提交，标题 `Grok with tavily clean (#27)`，说明正文里列着 `v1.9.2: remove guda key的应用`）删掉了这层派生：`GROK_API_URL` 与 `GROK_API_KEY` 回到必填，缺任一个就抛错，默认模型回到 `grok-4-fast`。

`config.py` 里还藏着一处更直接影响安装的不一致：那段"配置缺失时打印给你的安装命令"用的是 `git+https://github.com/GuDaStudio/GrokSearch`，不带分支后缀。照错误提示装会拿到 `main`，照 README 装会拿到 `grok-with-tavily`，两者的必填项集合不同。

对读者的含义：如果你打算直连自建端点或官方兼容端点，把安装命令里的分支换成 `@main`，然后必须自己配 `GROK_API_URL` 和 `GROK_API_KEY`；如果接受查询词、待抓取 URL 与那把密钥经一个第三方聚合入口中转，README 原样可用。后一种选择里，三条本来各自独立的服务被折叠成一个域名，这是选型时该先确认的点，不是实现细节。

### 配置示例

先按 `main` 的口径装（自配端点，行为与仓库默认分支一致）：

```bash
# 装过就先清掉，避免同名 server 配置互相覆盖
claude mcp remove grok-search

claude mcp add-json grok-search --scope user '{
  "type": "stdio",
  "command": "uvx",
  "args": [
    "--from",
    "git+https://github.com/GuDaStudio/GrokSearch@main",
    "grok-search"
  ],
  "env": {
    "GROK_API_URL": "https://your-openai-compatible-endpoint/v1",
    "GROK_API_KEY": "your-key",
    "TAVILY_API_KEY": "tvly-your-key",
    "TAVILY_API_URL": "https://api.tavily.com",
    "FIRECRAWL_API_KEY": "fc-your-key"
  }
}'

claude mcp list    # 期望看到 grok-search 处于连接成功状态
```

`FIRECRAWL_API_KEY` 可省；省掉时 `web_fetch` 只有 Tavily 一条路。装完在对话里说一句"显示 grok-search 配置信息"，`get_config_info` 会打印全量配置（密钥只留首尾各 4 位）、实测 `/models` 的往返毫秒数、以及端点返回的模型列表——这是唯一一处能一次确认三件事的入口。

之后决定是否禁用官方工具：

```text
调用 grok-search 的 toggle_builtin_tools，action 设为 on
```

企业网络或代理下若 `uvx` 报证书校验不过，在 `args` 最前面加一项 `"--native-tls"`，让它改用系统证书库。

## 环境变量：14 个，其中一个不起作用

下表按 `main` 的 `config.py` 逐项核对，默认值全部来自代码字面量。

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `GROK_API_URL` | 是 | 无 | OpenAI 兼容端点，需支持 `/chat/completions` 与 `/models` |
| `GROK_API_KEY` | 是 | 无 | 上述端点密钥 |
| `GROK_MODEL` | 否 | `grok-4-fast` | 优先级高于 `~/.config/grok-search/config.json` 里的 `model` |
| `TAVILY_API_KEY` | 否 | 无 | 缺省时 `web_fetch` 失去首选路径、`web_map` 不可用 |
| `TAVILY_API_URL` | 否 | `https://api.tavily.com` | |
| `TAVILY_ENABLED` | 否 | `true` | **实际不起作用**，见下 |
| `FIRECRAWL_API_KEY` | 否 | 无 | Tavily 取不到内容时的托底 |
| `FIRECRAWL_API_URL` | 否 | `https://api.firecrawl.dev/v2` | |
| `GROK_DEBUG` | 否 | `false` | 只控制是否写日志文件 |
| `GROK_LOG_LEVEL` | 否 | `INFO` | |
| `GROK_LOG_DIR` | 否 | `logs` | 三级回退，见下 |
| `GROK_RETRY_MAX_ATTEMPTS` | 否 | `3` | Grok 请求是它加 1，Firecrawl 抓取是它本身 |
| `GROK_RETRY_MULTIPLIER` | 否 | `1` | 指数退避乘数 |
| `GROK_RETRY_MAX_WAIT` | 否 | `10` | 单次退避上限秒数 |

`TAVILY_ENABLED` 只被 `get_config_info` 读回去显示，全部 Tavily 调用点检查的是 `TAVILY_API_KEY` 在不在。设成 `false` 之后 `web_fetch` 与 `web_map` 照旧走 Tavily。真要停掉抓取路径，办法是把密钥去掉。

### 重试、超时与镜像站兼容

重试的实际形状：tenacity 的 `stop_after_attempt(GROK_RETRY_MAX_ATTEMPTS + 1)`，默认即最多 4 次 Grok 请求；可重试条件是连接超时、网络错误、协议错误，以及 HTTP 408 / 429 / 500 / 502 / 503 / 504；`Retry-After` 头只在 429 时被读，支持整数秒和 HTTP-date 两种格式；协议错误的等待时间是在指数退避之外再加 3 秒。单次请求的超时固定为连接 6 秒、读 120 秒、写 10 秒，读超时不可配置（PR #49 在改这一点）。

流式解析对镜像站的兼容度值得一提：`data: {...}` 与 `data:{...}` 两种 SSE（Server-Sent Events，服务器推送事件）写法都能解；若整个响应里一行都解不出 `delta.content`，它会把所有行拼起来按非流式 JSON 再解一次，读 `choices[0].message.content`。

### 日志、配置落点与版本锚点

日志落点是三级回退：`~/.config/grok-search/logs` → 当前工作目录的 `logs/` → `/tmp/grok-search/logs/`，文件名 `grok_search_YYYYMMDD.log`。`GROK_DEBUG` 不为真时不写文件，但消息仍会通过 MCP 的 `ctx.info` 发给客户端。配置目录本身创建失败时回退到 `./.grok-search/config.json`。

版本锚点这块要小心：仓库没有 tag、没有 release，`pyproject.toml` 里的 `version` 从 2025-11 建仓至今一直是 `0.1.0`，`v1.x` 只出现在提交说明和分支名里。要锁行为只能锁提交号。依赖声明四项，Python 要求 3.10 以上：

```toml
[project]
requires-python = ">=3.10"
dependencies = [
    "fastmcp>=2.3.0",
    "httpx[socks]>=0.28.0",
    "mcp[cli]>=1.21.2",
    "tenacity>=8.0.0",
]
```

README 徽章写的 "FastMCP 2.0.0+" 比代码里的实际下限低三个补丁版本，`dev` 分支的依赖串确实还是 `fastmcp>=2.0.0`；以 `pyproject.toml` 的 `>=2.3.0` 为准。

## 常见故障与排查

按现象分类，每条给出可自查的判断依据。

| 现象 | 原因 | 怎么确认 |
|------|------|----------|
| `web_search` 返回 `content` 为空、无报错 | `_safe_grok()` 吞掉全部异常并返回空串 | 设 `GROK_DEBUG=true` 复现，看日志里 `content:` 那一行；正文若是 `<think>…` 包裹，那是引用剥离不认这个标签（PR #37） |
| 补充信源里全是 Firecrawl 来源 | `round(n * 1)` 让 Tavily 配额恒为 0 | 看 `get_sources` 返回项的 `provider` 字段；或临时只留一把密钥 |
| `get_sources` 报 `session_id_not_found_or_expired` | LRU 上限 256 或进程重启，非时间过期 | 在同一段对话里紧跟着取；需要留档就让模型立即 `web_fetch` 关键页 |
| `web_map` 一上来就返回配置提示 | 它只认 Tavily，没有 Firecrawl 托底 | 检查 `TAVILY_API_KEY`；`get_config_info` 里 Tavily 那一项是否脱敏显示 |
| 关闭官方工具没生效 | 当前目录不在 Git 仓库内，`deny` 落到了别处 | 看返回 JSON 的 `file` 字段指向哪个 `settings.json` |
| 切了 `switch_model` 但模型没变 | `GROK_MODEL` 环境变量优先级高于配置文件 | `get_config_info` 里 `GROK_MODEL` 的取值 |
| 频繁 429 | 端点侧限流，而退避上限默认只有 10 秒、读超时固定 120 秒 | 看响应是否带 `Retry-After`（只有 429 会被读），再抬 `GROK_RETRY_MAX_ATTEMPTS` 与 `GROK_RETRY_MAX_WAIT` |
| OpenRouter 上模型名与配置值不一样 | URL 含 `openrouter` 时模型名被自动补上 `:online` 后缀 | 用 `get_config_info` 返回的 `GROK_MODEL` 核对补后缀后的名字 |

日志文件路径本身也是排查线索之一，`get_config_info` 的 `GROK_LOG_DIR` 会直接打印实际落点。

## README 那张对比图能说明什么

README 的效果展示写明了客户端："以在 `cherry studio` 中配置本 MCP 为例"，模型是 `claude-opus-4.6`，问题是查 FastAPI 官方文档的最新示例。两张截图分别是只开 Claude 内置搜索（模型按内部常识作答）和接上 `grok-search`（模型主动多次调用搜索）。

这组对比测的是：一次交互里模型有没有调用可用的搜索工具、调了几次。不涉及返回内容的正确性与相关性评分。

它反映的是系统的哪一部分：新增一个搜索工具之后，模型调用意愿的变化。这条链路里没有 `deny` 表参与——`toggle_builtin_tools` 改的是 `.claude/settings.json`，Cherry Studio 并不读这个文件。所以截图能支持的结论是"换一份写得更强势的工具描述就足以让模型去搜"，而不是"必须禁用官方工具才能让模型去搜"。

四条推不出来的东西。一，幻觉率下降：没有任务集、没有重复次数、没有对照提示词，两张截图不构成一次实验。二，Grok 的检索质量高于官方 `WebSearch`：回答质量根本没被度量。三，禁用官方工具这一步的价值：它压根不在实验条件里，README 反而是在两套工具同时在场时做的对比。四，把内置搜索仍不被调用外推成"内置搜索无用"——对照里缺了同样把内置工具禁掉、换成别家搜索 MCP 的那一格。

README 那句"为公平实验，我们打开了 claude 模型内置的搜索工具"点出了机制的另一面：内置工具在场时模型有第二条更省事的出口。这组对比里两条出口都在，所以调用次数的上升里有多少来自 Grok 的检索能力、多少来自工具描述里的措辞压力，分不开。本文没有复现这组实验。

## 边界：什么时候不值得装，以及采用顺序

它合用的情形相当具体：工作主要在 Claude Code 里，查询有明确时效（版本变更、接口签名、发布节奏），并且你能接受查询词与待抓取 URL 流向所配端点的持有方。

以下情形可以先跳过。

- 检索目标是仓库内的字符串定位，`rg` 更直接，走一次大模型往返只是增加延迟。
- 你已经在用会强制联网的客户端，或你的模型确实每次都主动调内置搜索——那这套约束对你是空转。
- 需要抓取必须执行 JavaScript 才渲染出的页面，工具描述自己写明不支持。
- 需要跨会话的检索留档与引用审计：信源缓存在进程内，重启即消失。
- 无法确认 `GROK_API_URL` 归属：这一项必填，等于把密钥和全部查询交给它。

采用顺序按风险从小到大排：先只装、用 `get_config_info` 确认连通与模型列表；再单用 `web_search` 与 `get_sources`，`extra_sources` 保持 0，此时新增依赖面只有 Grok 端点；然后按需加 Tavily 打开抓取，并清楚 `web_map` 会随 Tavily 一起可用；最后才决定要不要 `toggle_builtin_tools` 上 `on`——这一步会改掉整个项目的搜索出口，建议单独提一个提交，方便回退。规划那六个工具是可选的：如果你的模型本来就会把查询拆开，它只多花若干轮调用。

## 五个自测题

**1. `web_search` 返回 `sources_count: 0`，能说明这次回答没有来源吗？**

<details>
<summary>参考答案</summary>

不能。两种情况都会报 0：Grok 确实没给引用；或者引用以内联 `citation_card` 的形式散在句子之间，而切分函数要求引用成块出现在文本末尾，于是既没进缓存也留在正文里。分辨方法是看 `content` 里有没有 `citation_card(` 字样。
</details>

**2. `permissions.deny` 里应该出现哪两个字符串？写错会怎样？**

<details>
<summary>参考答案</summary>

`WebFetch` 与 `WebSearch`，首字母大写、无连字符。写成 `web-search` 之类的规则不会命中任何工具，Claude Code 的权限层拦不下来，表现为"禁了但模型还在用内置搜索"。
</details>

**3. 配好 Tavily 与 Firecrawl 两把密钥后，`extra_sources=6` 实际会拿到谁的补充信源？为什么？**

<details>
<summary>参考答案</summary>

全部来自 Firecrawl。配额算式 `firecrawl_count = round(6 * 1)` 把额度吃满，`tavily_count` 剩 0。目前想让 Tavily 参与补充检索，只能只配它的密钥。
</details>

**4. 六个 `plan_*` 工具里，哪一步会真正失败、哪一步不会？原因是什么？**

<details>
<summary>参考答案</summary>

跳过 `plan_intent` 直接调其余五个会失败，因为它们先查会话是否存在，查不到就返回 `Call plan_intent first`。不走规划直接调 `web_search` 不会失败，它不检查计划状态，推动力只在工具描述那句提示里。
</details>

**5. 一条 `web_search` 调用返回空的 `content` 且没有报错，最可能的原因是什么，下一步查哪里？**

<details>
<summary>参考答案</summary>

`_safe_grok()` 捕获全部异常后返回空串，超时、重试耗尽、流式解析不出内容都会走到这里。下一步是分清请求层还是解析层：设 `GROK_DEBUG=true` 复现，日志里连 `content:` 那一行都没有，说明请求就没成功；有这一行但内容为空，则要看返回体是不是被 `<think>` 一类标签包住了（PR #37）。
</details>

## 下一步可以读哪几段代码

顺序建议按"约束在哪生效"来读，比按文件顺序省时间。

- `src/grok_search/server.py` 的 `web_search`：六个动作的顺序、并行取数、以及那段把 Tavily 配额算成 0 的算术。
- `src/grok_search/sources.py` 的 `split_answer_and_sources`：四种切法依次降级，配合 `utils.py` 里的 `search_prompt` 读，能看懂提示词与解析器怎么互相锁定。
- `src/grok_search/planning.py` 的 `REQUIRED_PHASES` 与 `process_phase`：累加语义、合并语义、以及 `plan_complete` 是怎么算出来的。
- `src/grok_search/providers/grok.py` 的 `_WaitWithRetryAfter` 与 `_parse_streaming_response`：镜像站兼容性集中在这里，读超时的硬编码也在同一段。
- 上游依赖：[FastMCP](https://github.com/jlowin/fastmcp) 负责工具注册，把 `Annotated` 参数描述编译成模型可见的工具模式（schema）；[tenacity](https://pypi.org/project/tenacity/) 负责退避与停止条件。想自己搭一个同类的强制联网入口，先照 `plan_intent` 的参数表看它怎么把"想清楚"拆成字段，再决定哪些约束值得写成 `deny`、哪些留在描述里就够。

## 资料口径与维护指引

本文事实来自三类材料，边界不同，读者可按需要单独复核。

代码与配置断言（工具数、参数、默认值、降级链条、重试条件、`deny` 写入形状、各分支差异）以仓库源码为准，核对时间 2026-09-19，对应提交 `afcdbcc6882213f41068d1d0c343b757e6a57688`（`main`，标题 `Grok with tavily clean (#27)`，2026-03-09 11:22 +0800）与 `8f0ae3c7f25ec419631ade7e431fa2531503433e`（`grok-with-tavily`，同日 10:49 +0800）。仓库最后一次推送是 2026-03-09，`main` 上共 33 次提交、6 位署名贡献者，其中 28 次出自同一人。当日仓库公开数据为 Star 1853、开放 issue 19、开放 PR 7，无 tag、无 release。

效果断言只来自 README 的两张截图，本文未复现，也未把任何"降低幻觉"的表述当作事实引用。issue 编号后的现象描述转述自报告者，未逐个复现验证——本文只保证这些现象与源码里可指认的行为对得上。

失效条件按优先级排：`main` 出现新提交时重点看 `config.py` 的单密钥派生是否回来、README 是否把工具数改到与代码一致；出现第一个 release 时应把安装建议从"锁分支"改为"锁标签"；`fastmcp` 大版本升级时工具注册的写法可能变。

## 参考资料

以下链接均在 2026-09-19 逐条访问确认可达（HTTP 200）。

- 仓库主页与 README（中/英文）：<https://github.com/GuDaStudio/GrokSearch>、<https://github.com/GuDaStudio/GrokSearch/blob/main/docs/README_EN.md>
- 逐行核对过的源码（`main` 提交 `afcdbcc`，用同一提交号可复查任意文件）：[server.py](https://github.com/GuDaStudio/GrokSearch/blob/afcdbcc6882213f41068d1d0c343b757e6a57688/src/grok_search/server.py)、[config.py](https://github.com/GuDaStudio/GrokSearch/blob/afcdbcc6882213f41068d1d0c343b757e6a57688/src/grok_search/config.py)、[sources.py](https://github.com/GuDaStudio/GrokSearch/blob/afcdbcc6882213f41068d1d0c343b757e6a57688/src/grok_search/sources.py)、[planning.py](https://github.com/GuDaStudio/GrokSearch/blob/afcdbcc6882213f41068d1d0c343b757e6a57688/src/grok_search/planning.py)、[providers/grok.py](https://github.com/GuDaStudio/GrokSearch/blob/afcdbcc6882213f41068d1d0c343b757e6a57688/src/grok_search/providers/grok.py)、[utils.py](https://github.com/GuDaStudio/GrokSearch/blob/afcdbcc6882213f41068d1d0c343b757e6a57688/src/grok_search/utils.py)
- 安装分支与 `main` 的配置差异：<https://github.com/GuDaStudio/GrokSearch/blob/8f0ae3c7f25ec419631ade7e431fa2531503433e/src/grok_search/config.py>
- 文中引用的讨论：issue [#46](https://github.com/GuDaStudio/GrokSearch/issues/46)（Tavily 与 Firecrawl 同时配置时的信源偏向）、[#42](https://github.com/GuDaStudio/GrokSearch/issues/42)（智能体类模型返回空正文）、[#28](https://github.com/GuDaStudio/GrokSearch/issues/28)（返回结果为空）、[#38](https://github.com/GuDaStudio/GrokSearch/issues/38)（规划工具是否多余）；PR [#37](https://github.com/GuDaStudio/GrokSearch/issues/37)（清理 `<think>` 标签）、[#50](https://github.com/GuDaStudio/GrokSearch/issues/50)（增强来源解析）、[#34](https://github.com/GuDaStudio/GrokSearch/issues/34)（修复间歇性空返回）、[#49](https://github.com/GuDaStudio/GrokSearch/issues/49)（可配置读超时）
- 时间注入的来龙去脉：关键词判断 `_needs_time_context()` 由 #7 那次提交引入（[e82a908](https://github.com/GuDaStudio/GrokSearch/commit/e82a908cd65c1c37617d514a2b92929ef7ef8869)，2026-01-19），去掉判断、改成无条件注入发生在 `afcdbcc` 这次合并提交（2026-03-09）
- 依赖项目：FastMCP <https://github.com/jlowin/fastmcp>、uv <https://docs.astral.sh/uv/getting-started/installation/>、tenacity <https://pypi.org/project/tenacity/>
- 抓取后端：Tavily <https://api.tavily.com>、Firecrawl <https://api.firecrawl.dev>

核对方式记一句：结构断言靠把仓库浅克隆到本地逐文件比对，分支差异用 `git diff --stat main <安装分支>` 确认只有 README 与 config；行为断言以两个分支共有的 `server.py`、`sources.py`、`grok.py` 为准；配置项默认值只看 `config.py` 里的字面量，不看 README 表格——文档给结论，代码给事实。
