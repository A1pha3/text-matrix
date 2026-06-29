---
title: "OpenSEO：把 Semrush/Ahrefs 装进 MCP 里的开源平替"
date: 2026-06-26T18:01:43+08:00
slug: "every-app-open-seo-semrush-alternative-guide"
description: "OpenSEO 是一个 MIT 协议的开源 SEO 工具，定位为 Semrush 和 Ahrefs 的平替。它把关键词研究、排名跟踪、外链分析、站点审计、AI 品牌可见度等 7 套工作流打包成一个自带 MCP 服务器的 Web 应用，并配套 8 个面向 Codex/Claude Code 的 Agent Skills。本文带你看清它和传统 SEO 工具的本质差异、5 分钟自托管路径与按量付费的真实成本。"
draft: false
categories: ["技术笔记"]
tags: ["SEO", "MCP", "AI Agent", "TypeScript", "开源工具"]
---

# OpenSEO：把 Semrush/Ahrefs 装进 MCP 里的开源平替

## 先给判断

OpenSEO 和 Semrush、Ahrefs 最大的差别不在功能列表，而在一个分水岭：**它的产物首先是给 AI 代理消费的**——MCP（Model Context Protocol，模型上下文协议）服务器是 7 套工作流的一等公民，Web UI 反而是它的"皮肤"。配套的 8 个 Agent Skills（`seo-project-setup` / `keyword-research` / `link-prospecting` 等）直接让 Claude Code 或 Codex 调起实时数据做出 SEO 决策，而不是让你在一个 SaaS 后台里点按钮。

如果你的工作流是"让 AI 代理自己查关键词、对比域名、规划外链"，OpenSEO 是目前 GitHub 上少数把这件事端到端做齐的开源项目。它不便宜地"卷"功能全度，而是把"按量付费 + 自托管 + AI 原生"这三件事钉死。

仓库地址：<https://github.com/every-app/open-seo>（MIT 协议，TypeScript，2.8k+ stars，最近一次推送 2026-06-24）。

## 系统地图：三层结构

| 层 | 组件 | 职责 |
|---|---|---|
| **数据采集层** | DataForSEO API + Google Search Console OAuth（可选） | 实际拿关键词、SERP、外链、域名数据 |
| **应用层** | OpenSEO Web App（Next.js）+ MCP Server | 把 DataForSEO 数据封装成 7 套工作流 + MCP 端点 |
| **AI 消费层** | Agent Skills（`seo-project-setup` 等 8 个）+ Codex/Claude Code 客户端 | 引导代理按规范消费 MCP 工具 |

数据所有权和应用控制在用户侧：DataForSEO 用你自己的 API key，Google Search Console 走你自己的 OAuth，应用跑在你自己 Docker 容器或你自己的 Cloudflare Worker 上。官方托管版 <https://openseo.so> 只是给"不想自托管"的人一个备选。

## 7 套工作流覆盖的 SEO 主场景

从 README 整理的工作流清单（每条都是 MCP 暴露的独立工具集）：

1. **关键词研究（Keyword research）**——找值得写的选题、估算搜索量、决定写哪个
2. **排名跟踪（Rank tracking）**——桌面/移动 SERP 位置 + SERP feature（精选摘要、知识面板等）检测
3. **域名洞察（Domain insights）**——看哪些页在涨/跌权重，把精力集中在直接影响收入的页
4. **外链分析（Backlinks）**——谁链了你、哪些页吸链、新链/丢链的差分
5. **站点审计（Site audits）**——抓技术问题，别让搜索引擎爬不动
6. **AI 品牌可见度（AI brand visibility）**——品牌在 ChatGPT/Google AI Overview 答案里被怎么提、竞争对手被怎么提、引用源覆盖
7. **AI 搜索提示词探索（AI search prompt explorer）**——在 AI 推荐场景里，用户可能用哪些提示词找到你

第 6、7 条是相对新的"AI 时代 SEO"维度——传统 Semrush 还在补这块，开源平替里专门做成工作流的不多。

## MCP 服务器：让代理直接读你的 SEO 数据

OpenSEO 的 MCP 端点不需要任何额外配置，启动应用后从 **AI & MCP** 面板复制 URL 即可。

Codex：

```sh
codex mcp add openseo --url https://app.openseo.so/mcp
```

Claude Code：

```sh
claude mcp add --transport http --scope user openseo https://app.openseo.so/mcp
```

MCP 客户端连上后，你的代理就能直接在对话里调用：

- 跑关键词研究、看 SERP、对比域名、查外链
- 在编辑器或聊天里把 SEO 决策端到端做完
- 走 OAuth 登录授权后，操作会自动记到你的账户

> 重要：MCP URL 携带身份凭据，不要贴到公开 issue 或截图里；自托管时务必放在反代后的 HTTPS 域名下。

## Agent Skills：把 SEO 方法论灌进代理

光有 MCP 工具还不够——AI 代理需要知道"什么时候该用哪个工具、按什么顺序出结论"。OpenSEO 用 Skills（`/Users/<你>/.codex/skills` 或 `~/.claude/skills` 下的可复用指令集）解决了这个。

安装命令：

```sh
# 全部安装
npx skills add every-app/open-seo

# 全部安装并自动接受
npx skills add every-app/open-seo --skill '*'

# 只给 Claude Code
npx skills add every-app/open-seo --skill '*' --agent claude-code

# 只给 Codex
npx skills add every-app/open-seo --skill '*' --agent codex
```

也可以手动 clone 后拷到对应目录：

```sh
git clone https://github.com/every-app/open-seo.git

# Codex
mkdir -p ~/.codex/skills
cp -R open-seo/.agents/skills/* ~/.codex/skills/

# Claude Code
mkdir -p ~/.claude/skills
cp -R open-seo/.agents/skills/* ~/.claude/skills/
```

**内置 8 个 Skill（截至 README 当前版本）**：

| Skill | 用途 |
|---|---|
| `seo-project-setup` | 起步向导：问项目背景、帮你配置工作空间（建议第一次跑） |
| `seo-coach` | 总教练视角，跨工作流串决策 |
| `keyword-research` | 关键词研究流程化 |
| `keyword-clustering` | 关键词聚类，决策"写哪一组" |
| `competitive-landscape` | 竞争格局总览 |
| `competitor-analysis` | 单个竞争对手拆解 |
| `link-prospecting` | 外链建设机会发现 |

新人建议从 `/seo-project-setup` 启动——它会问项目类型、目标市场、关心的关键词，让代理把工作空间先准备好，再去跑其他 skill。

## 5 分钟自托管：Docker 路径

> Docker 版本默认是**单用户本地模式**，没有认证，**不要**直接暴露公网。要给团队用、跨设备用，**走 Cloudflare Workers 路径**（免费 plan 兼容）。

前置：安装 Docker Desktop。

```sh
git clone https://github.com/every-app/open-seo.git
cd open-seo
cp .env.example .env
# 编辑 .env，填 DATAFORSEO_API_KEY（生成方式见下节）
docker compose up -d
```

打开 <http://localhost:3001>。更新：

```sh
docker compose up -d --pull always
```

镜像从 GHCR 拉：`ghcr.io/every-app/open-seo:latest`。

## 5 分钟自托管：Cloudflare Workers 路径

点 README 里的 Deploy to Cloudflare 按钮，会跳到 Cloudflare 部署页（没账号先注册，免费 plan 即可）。具体步骤 UI 不一定明示，按 `docs/SELF_HOSTING_CLOUDFLARE.md` 对照配置。

部署时唯一必填的运行时变量就是 `DATAFORSEO_API_KEY`（Workers UI 里配 Secrets）。

## DataForSEO API key 生成

OpenSEO 不直接对外做关键词/SERP/外链数据采集，所有 SEO 数据都来自 DataForSEO 第三方付费服务——**OpenSEO 本身完全免费**，你只为 DataForSEO 实际调用付费。

1. 申请：<https://app.dataforseo.com/api-access>，用邮箱请求 `API key by email` 或 `API password by email`
2. 拿到 login + password 后 base64 编码：

   ```sh
   printf '%s' 'YOUR_LOGIN:YOUR_PASSWORD' | base64
   ```

3. 把结果填到：
   - Docker：`.env` 的 `DATAFORSEO_API_KEY`
   - Cloudflare：Workers UI 的 Secrets
   - 本地开发：`.env.local`

**外链功能额外要求**：DataForSEO Backlinks 需要在你的账户上开通（有 2 周免费试用，但试用后是 $100/月承诺）。如果只想要外链数据不想签月度，官方托管版 <https://openseo.so> 一个月 $20 提供相同数据访问。

## 真实成本参考（按 2026-02-26 DataForSEO 公开定价）

新账户有 **$1 免费信用**测试，最低充值 **$50**。

| 操作 | 单次成本 | 备注 |
|---|---|---|
| **关键词研究**（150 结果） | $0.035 | 默认设置 |
| **关键词研究**（500 结果） | $0.07 | 公式：`0.02 + (0.0001 × 返回关键词数)` |
| **域名概览**（200 排名词） | $0.0401 | 公式：`0.0201 + (0.0001 × 排名词数)` |
| **站点审计** | $0.01 / 20 页 | 走 Lighthouse API |
| **外链-域名搜索** | ~$0.06 | 打开"引用域名"或"热门页"标签 +$0.02/个 |
| **外链-页搜索** | ~$0.04 | 同上 |
| **AI 品牌查询** | ~$0.85/次 | 6 个 AI Optimization 调用 + 24h 缓存 |
| **排名跟踪** | $2/月示例 | 50 关键词 × 单设备 × 搜 5 页深 |

实测规划示例（README 直接给）：

- 100 次关键词研究（150 结果/次）：**$3.50**
- 100 次域名概览（200 排名词/次）：**$4.01**
- 100 次完整外链域名搜索：**~$10.94**

按需使用、不是订阅，是这个项目"反 SaaS"的核心点——只为你实际跑的查询付费。

## 适用边界与何时不要用

**适合**：

- 已经在用 Claude Code 或 Codex 写 SEO 内容、希望代理直接调真实数据做决策
- 对 Semrush $139+/月或 Ahrefs $129+/月订阅敏感，想按量付费
- 能接受"自托管 + 自维护 DataForSEO 账户 + 自己装 Skill"的工程化上手过程
- 想 fork 改一套自己的内部 SEO 工具（MIT 协议允许）

**不适合**：

- 团队里没有"懂 Docker / Cloudflare Workers / DataForSEO API"的人——首次部署 + DataForSEO 凭据生成 + 镜像更新链路都需要基础的云原生经验
- 需要"零配置打开网页就能查排名"的非技术用户——SaaS 后台可能更顺手
- 需要大规模批量域名分析（1000+ 域名/天）——DataForSEO 按量计费会快速放大成本
- 想要 Semrush 那种"内容模板 + 营销日历 + 社交媒体管理"全套营销功能——OpenSEO 纯 SEO 工具，没有这部分

## 路线图（README 2026-06 公开）

官方给出的下一阶段重点：

- Google Search Console 集成 + MCP
- 本地 SEO
- 客户定制报表
- 改进并支持定时站点审计
- 内嵌 AI 代理
- 多项目支持

Roadmap 的优先级会跟用户反馈动态调整，作者在 Discord 和邮箱 `ben@openseo.so` 直接接需求。

## 一句话总结

OpenSEO 是 2026 年 GitHub 上少数把"按量付费 + 自托管 + MCP + Agent Skills"四件事钉在一起的开源 SEO 工具。如果你的 SEO 工作流是"AI 代理驱动 + 想从订阅里逃出来 + 愿意花一两天自托管"，它是最直接的 Semrush/Ahrefs 替代路径；如果不是，这个项目对你可能就只是一份 README 而已。

---

**项目信息**：

- 仓库：<https://github.com/every-app/open-seo>
- 协议：MIT
- 语言：TypeScript
- 主页：<https://openseo.so>
- 镜像：`ghcr.io/every-app/open-seo:latest`
- Discord：<https://discord.gg/c9uGs3cFXr>
