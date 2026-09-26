---
title: "小红书 MCP Skills 全集：让 AI Agent 照着规程操作小红书"
date: "2026-04-07T17:55:00+08:00"
lastmod: "2026-09-24T10:00:00+08:00"
slug: xiaohongshu-mcp-skills-complete-guide
github_repo: "autoclaw-cc/xiaohongshu-mcp-skills"
source_key: "gh:autoclaw-cc/xiaohongshu-mcp-skills"
description: "解读 autoclaw-cc/xiaohongshu-mcp-skills：8 个 Agent Skills 把 xiaohongshu-mcp 的 13 个 MCP 工具编排成登录、发布、搜索、互动、策划的操作规程，兼容 OpenClaw 与 Claude Code。"
categories: ["技术笔记"]
tags: ["小红书", "MCP", "Agent Skills", "OpenClaw"]
draft: false
---

## 目录

- [这套 Skills 解决什么问题](#这套-skills-解决什么问题)
- [系统地图：8 个 Skills 与 13 个 MCP 工具](#系统地图8-个-skills-与-13-个-mcp-工具)
- [安装与配置](#安装与配置)
- [核心 Skill 深度解析](#核心-skill-深度解析)
- [任务流案例：一篇种草笔记的完整旅程](#任务流案例一篇种草笔记的完整旅程)
- [技术架构与设计约束](#技术架构与设计约束)
- [与同类工具对比](#与同类工具对比)
- [实践建议与适用边界](#实践建议与适用边界)
- [常见问题](#常见问题)
- [项目地址](#项目地址)

---

# 小红书 MCP Skills 全集：让 AI Agent 照着规程操作小红书

## 这套 Skills 解决什么问题

[xiaohongshu-mcp-skills](https://github.com/autoclaw-cc/xiaohongshu-mcp-skills) 本身没有一行业务代码。它由 8 个目录组成，每个目录只有一份 SKILL.md，内容是把上游 [xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp) 的 13 个 MCP 工具编排成 Agent 可直接执行的操作规程：什么条件下触发、先检查什么、调用哪个工具、哪些参数从哪里拿、哪些操作必须先问过用户。理解了这一点，也就理解了这个项目的定位——它不新增任何小红书操作能力，它解决的是"Agent 拿到 MCP 工具之后仍然不会用"的问题。

这类封装之所以必要，是因为小红书自动化有两个绕不开的坑。一是上游工具的参数纪律严格：搜索、点赞、评论、查看主页，几乎每个工具都要求 `feed_id` 加 `xsec_token` 成对出现，且必须取自真实的搜索或浏览结果，编造即报错——项目根 SKILL.md 把这条写成了全局约束。二是写操作不可撤回：发布、评论以用户身份公开发表，Agent 必须先展示内容等确认。这些约束散落在 MCP 协议之外，Skills 层把它们固化成文，Agent 每次操作前都有章可循。

项目由 autoclaw-cc 团队维护，基于 MIT 许可证开源，兼容 [Agent Skills 开放标准](https://agentskills.io)，README 声明支持 OpenClaw、Claude Code 等平台。截至 2026-09-24 复核时点，仓库关键数据如下：

| 指标 | 数值 |
|------|------|
| GitHub Stars | 264 |
| Forks | 46 |
| 贡献者 | 2（xpzouying、Angiin） |
| 提交数 | 12 |
| 最近提交 | 2026-03-05 |
| 许可证 | MIT |
| 支持平台 | OpenClaw、Claude Code 等，遵循 Agent Skills 开放标准 |

仓库自 2026-03-05 起没有新提交，本文对各 Skill 机制的描述与仓库当前状态一致；上游 xiaohongshu-mcp 仍在活跃开发（2026-09-22 发布 v2.5.5），新增能力不保证会被这层 Skills 跟进。

## 系统地图：8 个 Skills 与 13 个 MCP 工具

整个系统分三层：Agent 客户端（OpenClaw 或 Claude Code）加载 Skills 层的 SKILL.md；Skills 层不包含任何实现，所有操作通过 HTTP 调用 xiaohongshu-mcp 服务（Go 编写，默认监听 `http://localhost:18060/mcp`）；MCP 服务再以浏览器方式访问小红书网页。

8 个 Skills 按职责划分如下：

| Skill | 功能 | 典型场景 |
|-------|------|----------|
| **setup-xhs-mcp** | 安装部署 MCP 服务、配置连接 | 首次使用 |
| **xhs-login** | 扫码登录、状态检查、重置登录 | 账号管理 |
| **post-to-xhs** | 发布图文/视频笔记 | 内容发布 |
| **xhs-search** | 关键词搜索，多维度筛选 | 竞品分析 |
| **xhs-explore** | 浏览推荐流、查看笔记详情和评论 | 内容研究 |
| **xhs-interact** | 点赞、收藏、评论、回复 | 互动操作 |
| **xhs-profile** | 查看用户主页和作品 | 博主研究 |
| **xhs-content-plan** | 热门内容分析、竞品研究、选题建议 | 内容规划 |

Skills 与 MCP 工具的对应关系由仓库根目录的 CLAUDE.md 维护，13 个工具按风险分成两类——ReadOnly（只读查询）和 Destructive（改动账号状态或公开发表内容）。大体上只读操作可直接执行、写操作需用户确认，个别例外（如点赞属 Destructive 但规程允许直接执行）在后文对应 Skill 处说明：

| MCP 工具 | 类型 | 对应 Skill | 说明 |
|---|---|---|---|
| `check_login_status` | ReadOnly | xhs-login | 检查登录状态 |
| `get_login_qrcode` | ReadOnly | xhs-login | 获取登录二维码 |
| `delete_cookies` | Destructive | xhs-login | 删除 cookies 重置登录 |
| `publish_content` | Destructive | post-to-xhs | 发布图文笔记 |
| `publish_with_video` | Destructive | post-to-xhs | 发布视频笔记 |
| `list_feeds` | ReadOnly | xhs-explore | 获取推荐流 |
| `search_feeds` | ReadOnly | xhs-search | 搜索笔记 |
| `get_feed_detail` | ReadOnly | xhs-explore | 获取笔记详情和评论 |
| `user_profile` | ReadOnly | xhs-profile | 获取用户主页 |
| `like_feed` | Destructive | xhs-interact | 点赞/取消点赞 |
| `favorite_feed` | Destructive | xhs-interact | 收藏/取消收藏 |
| `post_comment_to_feed` | Destructive | xhs-interact | 发表评论 |
| `reply_comment_in_feed` | Destructive | xhs-interact | 回复评论 |

这张表是理解整套系统的钥匙：每个 Skill 都是若干工具的编排说明，每个工具的参数要求都写进了对应 Skill 的执行流程。后文逐个解析时可以对照着看。

需要说明的是交互方式。Agent Skills 不是 CLI 工具，`/xhs-search` 这样的斜杠命令只是一个意图触发入口，后面跟的是自然语言，不是 `--sort` 这类命令行参数。README 里的用法示例都是这种形态：`/xhs-search 美食探店`、`/post-to-xhs`。筛选条件、笔记链接、发布内容，都用对话告知 Agent，由 Agent 按规程转换成 MCP 工具调用。

## 安装与配置

### 前置条件

- 一个可用的 xiaohongshu-mcp 服务。如尚未安装，不需要单独看上游文档——`setup-xhs-mcp` 这个 Skill 的设计目的就是引导完成从零到可用的全过程（见下文解析）。
- OpenClaw 或 Claude Code 之一。Skills 全部是 Markdown 文件，对运行环境没有额外要求。

### 安装步骤

#### OpenClaw

按仓库 README 的说法：下载本项目到本地，解压到 OpenClaw 的 SKILLS 目录，重启会话生效。

#### Claude Code

```bash
# 项目级别
cp -r skills/ .claude/skills/

# 或全局级别
cp -r skills/ ~/.claude/skills/
```

项目根目录还有一份 SKILL.md，作为统一入口：它能识别八类意图并路由到对应子 Skill，也可以绕过入口直接使用各子 Skill。

### 装好之后

重启会话让客户端扫描到新 Skills。第一次实际使用时，Agent 会先执行根 SKILL.md 规定的前置检查——确认 MCP 工具列表里存在 `check_login_status`；不存在则说明服务未连接，此时应运行 `/setup-xhs-mcp` 完成部署和配置，规程明确禁止 Agent 用 Playwright、WebFetch 等其他工具代替。

## 核心 Skill 深度解析

### post-to-xhs：智能发布笔记

这是最核心的 Skill，支持图文和视频两类笔记。

**触发条件**：用户想在小红书发布内容——发笔记、发图文、发视频、上传图片、写一篇小红书、种草笔记、好物分享，乃至只说"帮我发一下"但上下文明确是小红书。

**输入判断**：提供了视频文件走视频笔记；提供了图片走图文笔记；只有文本则提示至少提供图片或视频——小红书不允许纯文本笔记。

**参数清单**：

| 参数 | 必填 | 说明 |
|------|------|------|
| `title` | 是 | 标题，最多 20 个中文字或英文单词 |
| `content` | 是 | 正文，不包含 # 标签 |
| 图片列表或视频路径 | 二选一 | 视频仅支持本地绝对路径 |
| `tags` | 否 | 话题标签数组，MCP 服务自动处理格式 |
| `schedule_at` | 否 | 定时发布，ISO8601 格式 |
| `is_original` | 否 | 声明原创，仅图文笔记 |
| `visibility` | 否 | 公开可见 / 仅自己可见 / 仅互关好友可见 |

标题 20 字的上限来自小红书平台自身——上游 README 特别标注"小红书要求标题不超过 20 个字"，超长会被截断。正文里不要写 # 标签，标签统一通过 `tags` 参数传递。

**执行流程**五步：

1. **收集发布信息**——按上面的参数清单向用户逐项确认，缺什么问什么；
2. **内容校验**——检查标题长度，检查图片/视频路径是否为绝对路径；如果用户提供的是 URL，先用 WebFetch 提取文本和图片；
3. **确认发布**——展示标题、正文、标签、媒体列表、定时时间和可见范围的完整预览，等用户确认；
4. **执行发布**——图文调 `publish_content`，视频调 `publish_with_video`；
5. **报告结果**——告知笔记 ID 和发布状态。

**失败处理**：未登录引导用 xhs-login；标题超长提示缩短；路径无效提示检查；视频用了相对路径提示改绝对路径；发布失败则展示错误信息，建议检查内容或重试。

### xhs-login：账号登录管理

登录这件事没有任何自动化的余地——规程写明"登录需要用户手动用手机 App 扫码"。Skill 定义了三个动作：

- **检查状态**：调用 `check_login_status`，返回是否已登录及用户名；
- **扫码登录**：调用 `get_login_qrcode`，MCP 返回超时提示文本和 Base64 编码的 PNG 二维码；客户端渲染不了图片时，把 Base64 存成临时 PNG 文件让用户手动打开；
- **重新登录/切换账号**：先调用 `delete_cookies` 清除当前登录状态（Destructive 操作，执行前必须确认），再走一遍扫码。

值得注意：登录态由 MCP 服务侧的 cookies 维护，失效后走的是"删 cookies 重新扫码"，不存在什么可以刷新的 token 机制。

### xhs-search：智能搜索笔记

搜索只支持关键词检索，能力来自 `search_feeds` 工具：`keyword` 必填，`filters` 可选。可用的筛选维度全部来自 MCP 工具定义：

| 筛选维度 | 取值 |
|---------|------|
| `sort_by` | 综合 / 最新 / 最多点赞 / 最多评论 / 最多收藏 |
| `note_type` | 不限 / 视频 / 图文 |
| `publish_time` | 不限 / 一天内 / 一周内 / 半年内 |
| `search_scope` | 不限 / 已看过 / 未看过 / 已关注 |
| `location` | 不限 / 同城 / 附近 |

实际使用时不需要背这些枚举值——对 Agent 说"搜一下最近一周点赞最多的护肤笔记"，规程会把它映射成 `sort_by=最多点赞` 加 `publish_time=一周内`。

结果展示要求每条包含标题、作者、点赞/评论/收藏数，以及 `feed_id` 和 `xsec_token`——后两者是后续查看详情、互动操作的前置参数，规程要求必须从搜索结果中获取，不可编造。这个 Skill 没有按用户或按话题检索的能力，找特定用户的笔记应该走 xhs-profile。

### xhs-explore：发现内容灵感

两个入口：浏览推荐流调 `list_feeds`（无参数，返回首页推荐）；看具体笔记调 `get_feed_detail`，需要 `feed_id` 和 `xsec_token` 成对传入。后者对评论抓取有一组细化参数：

| 参数 | 说明 |
|------|------|
| `load_all_comments` | 默认 false，仅返回前 10 条评论 |
| `limit` | load_all_comments=true 时生效，默认 20 |
| `click_more_replies` | 是否展开二级回复 |
| `reply_limit` | 跳过回复数超过此值的评论，默认 10 |
| `scroll_speed` | slow / normal / fast |

这组参数暴露了实现的真相：MCP 服务是用浏览器模拟滚动抓取页面的，抓评论的速度、深度都要靠参数控制。返回内容包括笔记内容、图片、作者信息、互动数据和评论列表。

### xhs-interact：互动操作

四类互动对应四个工具，风险等级不同：

| 操作 | MCP 工具 | 关键参数 | 执行策略 |
|------|---------|---------|---------|
| 点赞/取消点赞 | `like_feed` | `feed_id` + `xsec_token`，`unlike` 可选 | 直接执行 |
| 收藏/取消收藏 | `favorite_feed` | `feed_id` + `xsec_token`，`unfavorite` 可选 | 直接执行 |
| 发表评论 | `post_comment_to_feed` | `feed_id` + `xsec_token` + `content` | 展示内容，用户确认后执行 |
| 回复评论 | `reply_comment_in_feed` | `feed_id` + `xsec_token` + `content`，`comment_id` 与 `user_id` 至少提供一个 | 展示内容，用户确认后执行 |

点赞和收藏可逆，且 MCP 服务做了幂等处理——已点赞时再点赞会自动跳过——所以规程允许直接执行；评论和回复以用户身份公开发表、无法撤回，必须先确认。所有互动都需要从搜索或详情结果里拿到的 `feed_id` + `xsec_token`，这个 Skill 没有"按话题批量点赞"或"自动回复评论"的能力。

### xhs-profile：用户主页分析

调用 `user_profile`，需要 `user_id`（来自笔记详情或搜索结果）和 `xsec_token`。返回三块内容：基本信息（昵称、头像、简介、性别、地区）、数据（粉丝数、关注数、获赞与收藏数）、最近发布的笔记列表（附带每条的 `feed_id` 和 `xsec_token`，可以接着看详情或互动）。

### xhs-content-plan：内容策划助手

这是一个纯只读的分析 Skill，规程明确约束"不执行任何发布或互动操作"。它本身不连接任何数据分析后端，策划建议完全来自用基础搜索工具做的现场调研：

1. **明确策划需求**——目标领域（美妆、旅行、美食）和目的（选题灵感/竞品分析/热门趋势）；
2. **搜索分析**——用不同关键词多次调用 `search_feeds` 覆盖领域，`sort_by` 选"最多点赞"找爆款、选"最新"看趋势；对高互动笔记调 `get_feed_detail` 分析标题写法、内容结构、话题标签使用和评论区关注点；需要时用 `user_profile` 看特定博主的内容风格和数据表现；
3. **输出策划建议**——热门选题方向、标题参考模板、推荐话题标签、内容结构建议。

换句话说，"热门分析"的真实机制是"多搜几次、按点赞排序、逐篇拆解"，没有热度数据库，也没有发布时机预测。理解这一点，对它输出的建议才会有合理预期。

### setup-xhs-mcp：服务安装部署

首次使用时这个 Skill 会引导走完五步：

1. **检测服务状态**：`curl -so /dev/null http://localhost:18060/mcp`。这里有个容易踩的坑，也是仓库历史上专门修过的问题——MCP 端点只接受 POST，GET 会返回 405，所以不能用 `curl -f` 判断服务是否存活；
2. **部署服务**：推荐 Docker Compose（镜像内置 Chrome 和中文字体，免配置；`./data` 持久化 cookies，`./images` 挂载发布图片；国内拉镜像慢可切换到阿里云镜像源）；也可从 GitHub Releases 下载二进制（需要本机已装 Chrome 或 Chromium）；源码编译仅适合 Go 开发者；
3. **检测 MCP 连接配置**：对 Claude Code，读 `~/.claude/settings.json` 和项目级 `.claude/settings.json`，查 `mcpServers` 里有无 `xiaohongshu` 配置、地址是否匹配；
4. **配置连接**：执行 `claude mcp add xiaohongshu --transport http <地址>`，或直接写配置文件（Cursor 则写 `.cursor/mcp.json`）；其他客户端告知地址后按各自文档配置；
5. **验证与提示**：提示重启会话（MCP 配置变更后必须重启客户端才能加载工具），重启后调 `check_login_status` 验证，通过后引导 `/xhs-login` 扫码。

服务端还有三个可选环境变量：`XHS_PROXY`（HTTP/HTTPS/SOCKS5 代理）、`ROD_BROWSER_BIN`（自定义 Chromium 路径）、`HEADLESS`（无头模式开关）。

## 任务流案例：一篇种草笔记的完整旅程

把机制串起来看一次真实操作。假设用户对 Claude Code 说：

> 帮我发一篇春日护肤的种草笔记，图片在 /Users/me/Pictures/spring.jpg

Agent 的处理路径是这样的：

1. **前置检查**——根 SKILL.md 要求每次执行必做：当前 MCP 工具列表里有 `check_login_status`，说明服务已连接，继续；
2. **意图路由**——"发笔记"命中发布意图，按 post-to-xhs 执行；
3. **登录检查**——全局约束"登录优先"，调 `check_login_status` 确认已登录（未登录的话，后续工具全会失败）；
4. **输入判断**——用户给了图片、没给视频，判定为图文笔记；
5. **收集与校验**——标题和正文还没给，Agent 会追问；用户答"标题：春日护肤心得｜敏感肌必入的 5 款精华"后，规程校验长度（17 字，未超上限）、路径绝对性（通过）；
6. **确认**——Agent 展示完整预览：标题、正文、图片路径、默认可见范围"公开"，等用户回复确认；
7. **执行**——调 `publish_content`，`images` 传入 `["/Users/me/Pictures/spring.jpg"]`；
8. **报告**——返回笔记 ID 和发布状态。

同样的流程换到调研场景：先 `/xhs-search 敏感肌 护肤`，让 Agent 按"最多点赞"筛选并总结爆款标题的共性；再对目标笔记 `/xhs-explore` 看评论区在关心什么；最后才发起发布。搜索结果里拿到的 `feed_id` 和 `xsec_token` 在这条链路里贯穿始终——这正是根 SKILL.md 把"参数来源"列为全局约束的原因。

## 技术架构与设计约束

### 目录结构

```
xiaohongshu-mcp-skills/
├── skills/                    # 8 个子 Skill，每个只有一份 SKILL.md
│   ├── setup-xhs-mcp/
│   ├── xhs-login/
│   ├── post-to-xhs/
│   ├── xhs-search/
│   ├── xhs-explore/
│   ├── xhs-interact/
│   ├── xhs-profile/
│   └── xhs-content-plan/
├── CLAUDE.md                  # MCP 工具映射表与 SKILL.md 编写规范
├── README.md
├── SKILL.md                   # 统一入口：意图识别与路由
├── LICENSE
└── .gitignore
```

### 根 SKILL.md 的全局约束

统一入口定义了四条所有操作都必须遵守的规则：

1. **MCP 连接优先**——执行任何操作前确认 MCP 工具可用，不可用时只提示运行 `/setup-xhs-mcp`，禁止用 Playwright、WebFetch 等其他工具替代；
2. **登录优先**——除安装部署外，操作前先用 `check_login_status` 确认登录状态，未登录时调用其他工具会失败；
3. **用户确认**——发布、评论等写操作执行前必须展示内容让用户确认，因为这些操作发出后无法撤回；
4. **参数来源**——`feed_id` 和 `xsec_token` 必须取自搜索或浏览结果，编造的参数会导致 MCP 工具报错。

这套约束可以看作 Skills 层的"安全带"：上游 MCP 工具本身并不阻止 Agent 做危险的事，约束全靠规程文本约束 Agent 的行为。

### 对 Agent Skills 标准的实现

每个 SKILL.md 遵循 Agent Skills 开放标准的 frontmatter 约定：`name` 与 `description` 必有（description 写明触发场景和触发词），部分交互型 Skill 额外带 `argument-hint`（如 xhs-search 的 `[搜索关键词]`）。CLAUDE.md 里还定了一份编写规范：每个 SKILL.md 控制在 200 行以内，正文必须包含输入判断、约束条件、执行流程、失败处理四部分，Destructive 操作必须要求用户确认，工具名和参数必须与 xiaohongshu-mcp 源码一致。

这套规范带来的实际好处是可维护性：13 个 MCP 工具的参数口径在 Skills 层与上游源码之间有一一对应的承诺，上游工具升级时，改哪个 SKILL.md 是可以定位的。

## 与同类工具对比

| 工具 | 类型 | Stars | 主要功能 | 适用场景 |
|------|------|-------|---------|----------|
| **xiaohongshu-mcp-skills** | Agent Skills 集合 | 264 | 8 个 Skill 编排 13 个工具 | AI Agent 自动化操作 |
| **xiaohongshu-mcp** | MCP 服务 | 15958 | 13 个 MCP 工具 | 开发者自行集成 |
| **小红书创作服务平台** | 官方工具 | - | 基础发布与数据 | 手动操作 |
| **新红数据等第三方平台** | 数据分析平台 | - | 行业数据与监测 | 付费数据服务 |

Stars 数据为 2026-09-24 复核值。两个开源项目的定位差异值得展开：xiaohongshu-mcp 提供"能调用的工具"，适合自己写胶水代码的开发者；xiaohongshu-mcp-skills 提供"会用工具的规程"，让不做开发的用户也能在 Claude Code 或 OpenClaw 里用自然语言完成操作。前者活跃迭代，后者自 2026 年 3 月后未再更新——考虑到 Skills 层只是薄封装，只要上游工具接口不变，这层规程就不会过时，但上游新增的能力（如新版工具）也不会自动获得规程。

## 实践建议与适用边界

**发布节奏要自己把控。** Skill 提供了 `schedule_at` 定时发布参数，但"每小时发一篇"这类批量节奏没有现成机制——发布都经用户确认，本意就是让人留在回路里。合理用法是准备好一批内容，逐篇确认发布，或明确告知定时时间由 Agent 转成 ISO8601 传参。

**竞品调研是这个项目最稳的用法。** 搜索、排序、看详情、看评论、查博主主页，全是 ReadOnly 工具，不碰写操作，没有误发布风险。让 Agent 定期调研某个关键词下的爆款并总结标题与内容规律，是这套 Skills 与自身设计意图最吻合的场景。

**互动自动化要克制。** 点赞收藏虽可直接执行，但评论和回复代表你的公开身份，规程强制人工确认——这不是缺陷而是设计。把"自动回复所有评论"当目标的话，这个项目帮不了你，它从一开始就没打算做无人值守的营销机器人。

**账号风险自担。** 用浏览器模拟方式操作个人账号，始终存在触发平台风控的可能。建议用小号先跑通流程，重要账号谨慎接入；写操作保持默认的确认机制，不要为了省事绕过。

**部署优先 Docker。** Docker 镜像内置 Chrome 和中文字体，避开了二进制方式"本机必须先装 Chrome"的依赖；国内网络环境记得切换阿里云镜像源。

## 常见问题

### Q1：MCP 服务连接失败怎么办？

按 setup-xhs-mcp 的排查路径走：先用 `curl -so /dev/null http://localhost:18060/mcp` 确认服务存活（注意不要用 `curl -f`，GET 请求对 MCP 端点返回 405 是正常的）；服务没起来就用 Docker Compose 拉起；服务在但工具不可用，检查 `~/.claude/settings.json` 里 `mcpServers` 的地址是否匹配，改过配置后必须重启客户端会话；端口被占用用 `lsof -i :18060` 找到占用进程。

### Q2：登录状态失效如何处理？

对 Agent 说"重新登录"或"切换账号"，规程会先调 `delete_cookies` 清除旧登录态（会先向你确认），再走扫码流程。登录态是 MCP 服务侧维护的 cookies，没有 token 可刷新，失效就只能重新扫码。

### Q3：图片路径必须是绝对路径吗？

是。MCP 服务需要读取本地文件，相对路径会校验失败。视频同理，且必须是本地文件。发布前 Agent 会做这项校验，不用等到发布失败才发现。

### Q4：能定时发布吗？

能，通过 `schedule_at` 参数（ISO8601 格式），图文和视频笔记都支持。使用方式是对 Agent 说"明天上午十点发布"，由 Agent 转换格式传参——没有独立的定时任务界面。

### Q5：支持哪些客户端？

README 声明支持 OpenClaw 与 Claude Code，项目遵循 Agent Skills 开放标准。理论上任何实现了该标准的 Agent 平台都可以加载这些 SKILL.md，setup-xhs-mcp 也为其他客户端留了"告知 MCP 地址、按各自文档配置"的路径，但官方只对前两者提供了安装说明。

## 项目地址

| 项目 | 地址 |
|------|------|
| xiaohongshu-mcp-skills | https://github.com/autoclaw-cc/xiaohongshu-mcp-skills |
| 依赖项目 xiaohongshu-mcp | https://github.com/xpzouying/xiaohongshu-mcp |
| Agent Skills 开放标准 | https://agentskills.io |

---

## 参考来源与口径说明

本文事实依据按信源归类如下：

1. **Skills 仓库源文件**：8 个 SKILL.md、根 SKILL.md、CLAUDE.md、README.md，均取自 autoclaw-cc/xiaohongshu-mcp-skills 的 main 分支。该仓库最近一次提交为 2026-03-05，此后无更新，各 Skill 的流程、约束、参数描述均与源文件逐条对照。
2. **上游仓库**：xiaohongshu-mcp 的 README（main 分支）用于核对 13 个 MCP 工具的定义、18060 端口、标题 20 字平台限制；最新发布版本 v2.5.5（2026-09-22）。
3. **数据口径**：Stars、Forks、贡献者、提交数、许可证均来自 GitHub API，复核时点 2026-09-24。贡献者按 GitHub contributors API 口径为 2 人；commit 作者署名中的 "zy" 对应 xpzouying 账号。
4. **转述与边界**：Docker 部署细节、环境变量、失败处理均转述自 setup-xhs-mcp 的 SKILL.md，未实际部署验证；xhs-content-plan 的输出效果属 Agent 现场调研生成，本文不对其策划质量作背书；文中任务流案例为按规程推演的典型交互，非逐字实录。
