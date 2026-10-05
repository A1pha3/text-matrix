---
title: "Karakeep：自托管书签 + AI 自动打标签的「数字囤积者」工具完全指南"
date: "2026-07-07T03:00:12+08:00"
slug: "karakeep-self-hosted-bookmark-ai-tag-guide"
github_repo: "karakeep-app/karakeep"
source_key: "gh:karakeep-app/karakeep"
description: "Karakeep（前身 Hoarder）是一个自托管、开源的书签 + 笔记 + 高亮 + 全文/语义搜索 + AI 自动打标签的「数字囤积者」工具。支持 Chrome/Firefox/Safari 扩展、iOS/Android app、CLI / Agent Skills / MCP 三种 agent 接入、RSS 自动归档、monolith 整页存档、yt-dlp 视频存档。Next.js + Drizzle + tRPC + Meilisearch 栈，AGPL-3.0。"
draft: false
categories: ["技术笔记"]
tags: ["Agent Skills"]
---

# Karakeep：把「存了就忘」变成「找得回来」的自托管书签库

书签工具最常见的死法不是存不进去，而是存进去就再也没被打开——囤到最后是一堆搜不出的 URL。Karakeep（前身 Hoarder）把力气花在「存下的东西回得来」上：抓取时留副本防链接腐烂，入库时让 LLM 打标编目，检索时全文加语义双路，2026 年又补齐了 CLI、官方 Skill 和 MCP 服务器，AI agent 可以替你存、替你查。本文按摄取、防腐蚀、编目检索、agent 接入四条线拆它的机制，重点讲默认值里藏的坑，最后给选型边界。

## 系统地图：四条主线

| 主线 | 干什么 | 关键组件 |
|------|--------|----------|
| 摄取 | 把东西存进来 | Chrome/Firefox/Safari 扩展、iOS/Android app、RSS 订阅、SingleFile 导入、各平台书签导入器、floccus 浏览器书签同步 |
| 防腐蚀 | 留下原链接失效后仍能看的副本 | 截图（默认开）、monolith 整页归档（默认关）、PDF 快照（默认关）、yt-dlp 视频下载（默认关） |
| 编目与检索 | 让内容找得回来 | LLM 自动打标（默认开）、自动总结（默认关）、OCR、Meilisearch 全文 + 语义搜索 |
| Agent 接入 | 让程序和 AI agent 调用 | REST API、CLI（`@karakeep/cli`）、官方 Skill、MCP 服务器 |

后端是一个 TypeScript 单体：Next.js（app router，主仓当前 16.3.6）+ tRPC v11 + NextAuth + Drizzle ORM，数据库是 SQLite（放在 `DATA_DIR`，可选 WAL 模式），全文搜索靠 Meilisearch（官方 compose 固定 v1.41.0），抓取由 Puppeteer 驱动独立的 karakeep-chrome 容器。后台任务拆成 crawler、inference、search、feed、video、webhook、ruleEngine 等独立 worker。没有微服务，也没有消息队列，单机 docker compose 就是一等公民的部署形态。

## 一条链接的一生

用一个任务把机制串起来。你在手机上看到一篇好文章，用分享面板存进 Karakeep：

1. 去重先发生：同一个 URL 再存不会生成两条记录，已有书签会被从存档恢复并顶到列表最前面，你没手动填过的元数据保持不变。
2. crawler worker 通过 karakeep-chrome 容器打开页面，抓标题、描述和首图，并存一张截图——默认只截可见区域，全页截图要另开配置。
3. 如果你开了对应开关，crawler 会接着用 monolith 存整页副本、用 yt-dlp 抓页面视频。这两样加上 PDF 快照默认全关，因为吃磁盘。
4. inference worker 把正文发给配置好的 LLM（走 OpenAI 时默认 gpt-5.6-luna，也可指到本地 Ollama），打回几个标签；正文同时被 text-embedding-3-small 切块向量化，进语义搜索索引。
5. 三个月后你在搜索框敲 `rust is:fav after:2026-01-01`，全文索引和标签一起命中；换成语义模式，措辞完全不同的文章也能被召回。

这条流水线的每一环都有开关，其中几个默认值和直觉相反，下面单独说。

## AI 编目：默认值比功能列表重要

Karakeep 的 AI 功能不多，但哪些默认开、哪些默认关，直接决定你装完实际得到什么。

自动打标默认开启。设了 `OPENAI_API_KEY` 或 `OLLAMA_BASE_URL` 就生效，否则跳过。标签语言由 `INFERENCE_LANG` 控制，默认 english——中文用户记得改，否则打出来的标签是英文的。打标 prompt 可以在用户设置里追加自定义指令，也支持 `$tags` / `$aiTags` / `$userTags` 占位符注入已有标签。

自动总结默认关闭。`INFERENCE_ENABLE_AUTO_SUMMARIZATION` 默认 false，想要摘要必须在 `.env` 里显式打开。这是最容易「装完觉得 AI 没生效」的地方。

OCR 默认走 tesseract.js，`OCR_LANGS` 默认只有 eng，中文图片要加上 `chi_sim` 这类语言码；复杂图可以设 `OCR_USE_LLM=true` 让推理模型来做。

语义搜索默认开启，但官方标注实验性（`SEMANTIC_SEARCH_ENABLED`）。用默认 OpenAI 配置时，embedding 自动索引跟着打开；换 Ollama 就得自己配 embedding 模型和维度，否则语义模式等于没接。

成本上文档说得很直白：`INFERENCE_CONTEXT_LENGTH` 默认 2048 token，超长正文截断后打标，调大质量更好但开销更高。个人量级下这点开销通常可以忽略，真正需要花心思的是上面几个默认值。

## 检索：查询语言是被低估的部分

全文搜索跑在 Meilisearch 上，Karakeep 在上面包了一层自己的查询语言，Web、CLI、MCP 共用一套语法：

| 限定符 | 含义 |
|--------|------|
| `is:fav` / `is:archived` / `is:broken` | 收藏 / 已归档 / 抓取失败 |
| `#标签` 或 `tag:"名称"` | 按标签 |
| `list:"名称"` | 按列表 |
| `url:` / `title:` | URL 或标题子串 |
| `after:` / `before:` / `age:` | 按创建时间过滤 |
| `-is:tagged` | 取反（`-` 或 `!` 前缀） |

空格表示 and，也支持 `or` 和括号。列表还有智能形态：`karakeep lists create --name "Recent AI" --type smart --query "#ai age:<1m"` 建出来的是一个保存的搜索，满足条件的新书签会自动进入。

自动化不止于此：RSS 是双向的，既能订阅源自动收书签，也能把列表发布成 RSS 输出；规则引擎按条件给新书签自动打标、收藏或归入列表；webhook 把书签的创建和变更事件推给外部系统。这几样组合起来，Karakeep 更像一个可以编程的内容收件箱，而不只是手动存取的仓库。

## Agent 接入：CLI 是底座，Skill 和 MCP 是两种接法

这是 Karakeep 和同类工具差异最大的一层。README 已经把 LLM agent（点名了 OpenClaw、Hermes）当作一等用户，具体给了三条路：

**CLI**（`npm install -g @karakeep/cli`）覆盖书签增删改查、搜索（含语义和混合模式）、列表、标签合并、高亮、资产下载，`--json` 输出机器可读结果。API key 用 `karakeep auth init` 写入 `~/.config/karakeep/config.json`（0600 权限），也接受 `KARAKEEP_API_KEY` 环境变量。另有 docker 镜像 `ghcr.io/karakeep-app/karakeep-cli:release`。

**官方 Skill** 就是仓库里的 `skills/SKILL.md`，内容是教 agent 什么时候用哪条命令、查询语言怎么写。装法：

```bash
npx skills add karakeep-app/karakeep
```

ClawHub 上也能装。注意 Skill 本身不定义新工具，它指挥 agent 调 CLI 干活，所以 agent 环境里得有 `karakeep` 命令。

**MCP 服务器**（`npx @karakeep/mcp`）面向原生支持 MCP 的客户端（Claude Desktop、Codex 等），配置 `KARAKEEP_API_ADDR` 和 `KARAKEEP_API_KEY` 两个环境变量即可。共 20 个工具，命名直白：`search-bookmarks`、`create-bookmark`、`attach-tag-to-bookmark`、`add-bookmark-to-list` 等，覆盖书签、列表、标签三组对象。

三条路选一条就够：agent 环境能装 CLI 就用 Skill；客户端原生支持 MCP 就配 MCP；写脚本直接用 CLI 的 `--json`。

## 部署：官方流程不需要克隆仓库

按官方文档，Docker 部署三步：

```bash
mkdir karakeep-app && cd karakeep-app
wget https://raw.githubusercontent.com/karakeep-app/karakeep/main/docker/docker-compose.yml
openssl rand -base64 36   # 跑两次，生成下面两个随机串
```

compose 起三个容器：karakeep web（端口 3000）、karakeep-chrome、meilisearch。`.env` 最小集四行：

```env
KARAKEEP_VERSION=release
NEXTAUTH_SECRET=<随机串>
MEILI_MASTER_KEY=<随机串>
NEXTAUTH_URL=http://localhost:3000
```

要 AI 打标就加一行 `OPENAI_API_KEY=<key>`，或者用 `OLLAMA_BASE_URL=http://host.docker.internal:11434` 指向本机 Ollama。然后 `docker compose up -d`，访问 `http://localhost:3000`。

更新方式取决于版本策略：用 `release` 标签就 `docker compose up --pull always -d` 强制拉新；钉了具体版本就改 `KARAKEEP_VERSION` 再 up。

备份要盯的就两处：`DATA_DIR`（SQLite 数据库加抓取资产）和 meilisearch 卷。资产量大可以切 S3 兼容存储，但文档明确警告：切换存储后端后，存量资产要手工迁移，选型前想清楚。

## 和同类工具比什么

| 工具 | 自托管 | AI 自动打标 | 存档副本 | Agent 接口 |
|------|--------|-------------|----------|------------|
| **Karakeep** | ✅（另有官方云托管） | ✅ 默认开 | 截图默认，整页/PDF/视频可选 | ✅ CLI + Skill + MCP |
| **Linkwarden** | ✅ | ✅ 可选，支持本地模型 | 截图 + PDF | ❌ |
| **Wallabag** | ✅ | ❌ | ✅（read-it-later 本职） | ❌ |
| **Shiori** | ✅ | ❌ | – | ❌ |
| **memos** | ✅ | ❌ | ❌ | ❌ |
| **Raindrop** | ❌（Karakeep README 明言其不可自托管） | – | – | ❌ |
| **mymind** | ❌ 商业服务 | ✅ | – | ❌ |
| **Pocket** | – | – | – | 已死（Mozilla 2025 年宣布关停） |

「–」表示本文未逐一核实，不下断言。memos 一行依据 Karakeep 作者在 README Alternatives 一节的原话：他爱用 memos，但它缺链接预览和自动打标，这正是他写 Karakeep 的动因。

结论可以从表里直接读出来：在「自托管、AI 编目、防腐蚀副本、agent 可直接调用」四格都打勾的开源书签工具里，目前只有 Karakeep 一个。Linkwarden 是最接近的对手——存档和协作做得扎实，也有本地 AI 打标——但没有 agent 接口层。反过来，如果你的核心诉求是团队共享收藏，Linkwarden 的协作模型反而更合适。

## 适用边界与起步顺序

适合：

- 存的东西跨设备、跨类型（链接、笔记、图片、PDF、视频），并且你真的会回来找
- 想要 AI 打标但数据不出本地——Ollama 路线全程可自包含
- 已经在用 Claude Code、Codex 类 agent，希望「看到好东西存一下」变成对 agent 说的一句话

不适合：

- 想开箱即用、不在乎数据上云——mymind 或 Raindrop 更省事，官方云托管 cloud.karakeep.app 也可以先试
- 想要团队知识库——Karakeep 支持同一列表协作和 OIDC SSO 登录，但定位是个人收藏，不是共享文档库
- 想要知识图谱和双链——它是档案馆，不是 Roam Research 或 Obsidian

起步顺序建议：

1. 先玩官方只读 demo（try.karakeep.app）确认交互合不合手
2. 自托管最小配置跑起来，只开 AI 打标，顺手把 `INFERENCE_LANG` 改掉
3. 用出习惯后，按磁盘预算开防腐蚀配置：`CRAWLER_FULL_PAGE_ARCHIVE`、`CRAWLER_STORE_PDF`、`CRAWLER_VIDEO_DOWNLOAD`
4. 最后接 agent：装 CLI 加 Skill，或直接配 MCP

维护上关注两件事。一是 release 节奏很快，升级前扫一眼 release notes——v0.33.2（2026-08-11）就包含一次 chrome 基础镜像迁移公告：旧的 alpine-chrome 镜像已无人维护且拉取不到，官方换成了自建镜像（chrome 124 升到 151），用 browserless 的部署不受影响。二是 0.x 版本号意味着接口仍可能变，但项目本身已进入稳定迭代期——GitHub 读数 29,380 stars、1,551 forks（2026-10-02），主分支持续有提交。

## 关键事实与出处

- 仓库 `karakeep-app/karakeep`，AGPL-3.0，版权归 Localhost Labs Ltd，主语言 TypeScript
- GitHub 读数（2026-10-02）：29,380 stars / 1,551 forks / 727 open issues；创建于 2024-02-06；最新 release v0.33.2（2026-08-11）
- 前身 Hoarder，2025 年 4 月改名（改名 PR #1280、#1316；2025-02-02 发布的 v0.22.0 仍叫 Hoarder）
- 名字来自阿拉伯语 كراكيب（karakeeb），指抽屉里那些扔了可惜的杂物；README 补了一句：更可能的原因是，你就是个 hoarder
- 技术栈（主仓 package.json 与 README）：Next.js 16.3.6 / React 19 / tRPC v11 / NextAuth / Drizzle / SQLite / Meilisearch / Puppeteer
- 推理默认模型（v0.33 文档）：文本 gpt-5.6-luna，图像 gpt-4o-mini；embedding 默认 text-embedding-3-small（1536 维）
- 作者 Mohamed Bassem，本职系统工程师（README 自述已做七年）。项目起因：手机上刷 Reddit、Twitter、HackerNews，想存到电脑上看；Pocket 不能自托管，memos 缺链接预览和自动打标，于是自己写了一个
