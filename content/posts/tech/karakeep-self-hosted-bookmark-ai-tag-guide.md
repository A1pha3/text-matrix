---
title: "Karakeep：自托管书签 + AI 自动打标签的「数字囤积者」工具完全指南"
date: "2026-07-07T03:00:12+08:00"
slug: "karakeep-self-hosted-bookmark-ai-tag-guide"
description: "Karakeep（前身 Hoarder）是一个自托管、开源的书签 + 笔记 + 高亮 + 全文搜索 + AI 自动打标签的「数字囤积者」工具。支持 Chrome/Firefox/Safari 扩展、iOS/Android app、CLI + Agent Skills、与 RSS 自动归档、monolith 整页存档、yt-dlp 视频存档。NextJS + Drizzle + tRPC + Meilisearch 栈，AGPL-3.0。"
draft: false
categories: ["技术笔记"]
tags: ["Self-Hosted", "Bookmark Manager", "AI Tagging", "Agent Skills", "Karakeep"]
---

# Karakeep：给"数字囤积者"的自托管书签 + AI 工具

如果你是那种"看到好东西就存起来、然后永远不会再翻"的人——Karakeep（前身 Hoarder）就是为这种行为模式设计的。它不只是一个书签工具，而是一个**自托管的全文知识库**：存链接、存笔记、存图片、存 PDF、自动抓标题/缩略图、AI 自动打标签、LLM 自动总结、与 Meilisearch 全文搜索、Chrome/Firefox/Safari 扩展一键存、iOS/Android app、CLI、官方 Agent Skills。本文拆它的功能边界、部署栈与和同类工具的差异。

## 它要解决的具体场景

README 作者的 use case 写得很清楚：

> 我每天在手机上刷 Reddit / Twitter / HackerNews，看到很多有意思的文章和工具，想存下来在电脑前看。Pocket 之类的 read-it-later app 我用过，但是我想 self-host。然后我尝试过 memos，缺 link preview + 自动打标签这两个核心能力。

所以 Karakeep 是 Pocket + memos + Linkwarden + Wallabag 这类工具的**自我重写**——功能上比 Pocket 强（自托管、AI、整页存档），比 memos 强（link preview、自动 tag、整页存档），比 Linkwarden 强（多媒体、AI、高亮、协作）。

## 功能边界（一图速览）

README 列了 30+ features，挑最关键的说：

### 必须有的核心能力

- 🔗 存链接 + 简单笔记 + 图片 + PDF
- ⬇️ 自动抓链接的 title / description / image
- 📋 整理到 lists（类似文件夹，但更灵活）
- 👥 多人协作同一 list
- 🔎 全文搜索（Meilisearch 后端）
- ✨ LLM-based 自动打标签 + 总结（支持本地 Ollama）
- 🤖 AI Agent 友好（CLI + 官方 Agent Skills）
- ⚙️ Rule-based 自动管理（"含 X tag 的链接自动归档到 Y list"）
- 🎆 OCR 抽图片里的文字
- 🔖 Chrome / Firefox / Safari 扩展一键存
- 📱 iOS / Android app
- 📰 RSS 自动归档
- 🔌 REST API + 多客户端（CLI、Skills、Web、Mobile）

### 让它和其他 bookmark manager 拉开差距的细节

- 🖍️ **高亮**——存网页里的某段文字，类似 Readwise 的高亮
- 🗄️ **整页归档**（monolith）——防链接腐烂，原页面下架也能读
- ▶️ **视频自动归档**（yt-dlp）——存 YouTube / 视频源，离线可看
- ☑️ **批量操作**——多选批量 tag / archive / delete
- 🔐 **SSO 支持**——公司内部部署可接企业 SSO
- 🌙 **Dark mode**
- 💾 **自托管优先**——demo 在线版只读，全部功能要自托管
- 🔄 **浏览器书签自动同步**（floccus）——不用手动一个个导入
- ⬇️ **多种书签导入器**：Chrome、Pocket、Linkwarden、Omnivore、Tab Session Manager

### 计划中（README 标 [Planned]）

- Offline reading on mobile
- Semantic search across bookmarks（语义搜索）
- ...

## 技术栈

```
┌──────────────────────────────────────────┐
│ Frontend:  NextJS 14 (app router)        │
├──────────────────────────────────────────┤
│ API:       tRPC (type-safe RPC)          │
│ Auth:      NextAuth                       │
├──────────────────────────────────────────┤
│ ORM:       Drizzle                        │
│ DB:        SQLite / PostgreSQL            │
│ Search:    Meilisearch                    │
│ Crawler:   Puppeteer (with monolith)      │
│ AI:        OpenAI API or local Ollama     │
└──────────────────────────────────────────┘
```

这个栈选得很务实——全 TypeScript 单体，没有微服务、没有 K8s、Drizzle ORM 让 schema 直观、tRPC 让前端类型安全。**单机能跑、单机扛得住个人使用**。

## AI 集成的两个细节

Karakeep 的 AI 集成点很克制——只做两件事：

1. **自动打标签**：抓 link 时自动打几个 tag（如"AI"、"Python"、"工具"），用户后续可以编辑。
2. **自动总结**：对长文章生成 1-2 句 summary，搜索结果里直接显示。

两件事都用同一个 LLM endpoint 配置，支持 OpenAI 兼容协议 + 本地 Ollama——后者意味着你完全可以在自托管时用本地 Llama 3 / Qwen，**零 API 费用、零数据外泄**。

不要指望它做"知识图谱"、"实体抽取"、"自动分类"这类高级功能——它就是把"AI 加进 bookmark manager"做成的最简形态。

## Agent Skills：让 Karakeep 被 AI agent 直接用

Karakeep 提供官方 Agent Skills（[docs.karakeep.app/integrations/agentic-skills](https://docs.karakeep.app/integrations/agentic-skills)）——这意味着 Claude Code / Codex / Cursor / Continue 等 agent 可以直接通过 Skill 协议调 Karakeep：

```bash
# 装到 Claude Code
npx skills add karakeep-app/karakeep -a claude
```

之后 agent 多了几个 tool：`karakeep_search` / `karakeep_save` / `karakeep_tag` / `karakeep_list`——你跟 Claude Code 说"把我刚打开的论文存到 Karakeep 的"AI 阅读"list，自动打 tag"，它就能直接做。

这是 Karakeep 在 2026 年被纳入"AI agent 友好的 bookmark manager"梯队的关键——Pocket / Raindrop / mymind 都还没做这层。

## 与同类工具的对比

| 工具 | 类型 | AI | 自托管 | Agent Skills | 整页存档 |
|------|------|----|--------|--------------|----------|
| **Karakeep** | 开源 + 自托管 | ✅（自动 tag + summary） | ✅（核心卖点） | ✅ | ✅（monolith） |
| **memos** | 开源 + 自托管 | ❌ | ✅ | ❌ | ❌ |
| **mymind** | 商业 SaaS | ✅ | ❌ | ❌ | ✅ |
| **raindrop** | 开源但主要 SaaS | 部分 | ❌ | ❌ | ❌ |
| **Pocket** | 已死 (Mozilla 2025 关停) | ❌ | ❌ | ❌ | ✅ |
| **Linkwarden** | 开源 + 自托管 | ❌ | ✅ | ❌ | ✅ |
| **Wallabag** | 开源 + 自托管 | ❌ | ✅ | ❌ | ✅ |
| **Shiori** | 开源 + 自托管 | ❌ | ✅ | ❌ | ❌ |

Karakeep 在开源 + 自托管 + AI + Agent Skills 这四个维度**同时满足**的赛道里几乎没有对手——这是它能维持热度的根本原因。

## 部署方式

最简部署（docker-compose）：

```bash
# 1. 克隆仓库
git clone https://github.com/karakeep-app/karakeep.git && cd karakeep

# 2. 复制 env 模板
cp .env.example .env
# 编辑 .env，至少设置 NEXTAUTH_SECRET

# 3. 启动
docker compose up -d

# 4. 访问 http://localhost:3000
```

要启用 AI 能力，在 `.env` 里设：

```env
# 用 OpenAI
OPENAI_API_KEY=sk-...
INFERENCE_LANG=en

# 或用本地 Ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
INFERENCE_LANG=en
```

Meilisearch 默认已经跑在 compose 里——不用额外配。

## 适用边界

**适合**：

- 想完全自托管个人知识库
- 已经用 Pocket 但想 escape（Pocket 已死）
- 想用 AI 自动打标签但又不想数据出公司
- 想用 Agent Skills 让 Claude Code 直接存
- 在多设备（desktop / mobile / iPad）需要统一书签
- 想存视频、PDF、图片，不只是链接

**不适合**：

- 想要"开箱即用 + 不在乎数据出公司"——直接用 mymind 或 raindrop。
- 想要企业级团队协作（Karakeep 不是为团队设计的）。
- 想要"中文语义搜索"——Meilisearch 默认 BM25，中文分词要自己配 jieba。
- 想要"知识图谱"——Karakeep 是 bookmark manager，不是 Roam Research / Obsidian。

## 关键事实

- **仓库**：`karakeep-app/karakeep`
- **协议**：AGPL-3.0（Localhost Labs Ltd 拥有）
- **主语言**：TypeScript（NextJS）
- **stars**：GitHub 显示 self-host 友好（确切数字未在 meta 中）
- **前身**：Hoarder（2025 改名 Karakeep，源于阿拉伯语"كراكيب"——零碎杂物）
- **状态**：⚠️ README 警告"under heavy development"

## 名字背后的故事

Karakeep 这个名字取自阿拉伯语 كراكيب（karakeeb）——口语里指"乱七八糟的杂物"，就像一个塞满你舍不得扔的小物件的抽屉。中文大概对应"杂物间"。作者自嘲："这名字就是承认我们都是 hoarder。"

## 总结

Karakeep 是当下**自托管 + AI + Agent Skills** 三者兼备的少数 bookmark manager 之一。如果你已经用 Claude Code / Cursor / Codex 做日常工作流，让 agent 直接通过 Skill 协议把"看到的好东西"自动存到 Karakeep，是当前把 bookmark manager 接入 AI 工作流摩擦最低的路径。