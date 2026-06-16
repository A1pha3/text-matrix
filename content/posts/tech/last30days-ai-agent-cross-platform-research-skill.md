---
title: "last30days-skill 解析：一个 AI agent skill 如何把 Reddit / X / YouTube / Polymarket 跨 13 个平台的事实拼成一份 30 天简报"
date: "2026-06-07T15:03:00+08:00"
slug: "last30days-ai-agent-cross-platform-research-skill"
description: "2026-06-07 GitHub Trending 当日榜 #1，29,164 stars / 单日 +439。它不是一个 search 工具，而是把'人投票过的事'——Reddit upvote、X like、YouTube view、Polymarket 真金白银——做成交叉信号源，给 agent 喂事实。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Claude Code", "Skill", "OpenClaw", "深度研究", "开源项目深拆", "MCP", "搜索"]
toc: true
---

## 这篇文章在回答什么

`mvanhorn/last30days-skill` 是 2026-06-07 GitHub Trending 当日榜第一名（29,164 stars / 单日 +439），也是过去两周反复出现在榜首的"长青项目"。它做的事情用一句话讲就是：

> 你给一个 topic，agent 自动去 Reddit / X / YouTube / Hacker News / TikTok / Polymarket / GitHub / 小红书 / Bluesky 等 13 个平台查过去 30 天，再用"人用 upvote/like/真金白银投出来的事实"做交叉信号，最后由一个 judge agent 写成一份带引用的简报。

听起来像"加个 Google + 几个 API"，但项目 README 自己的总结反而是：

> Google aggregates editors. /last30days searches people.

——它在和 Google 抢的不是"搜索"，是**信号源**。每个平台都是 walled garden：Google 不抓 Reddit 评论、ChatGPT 拿了 Reddit 数据但看不到 X、TikTok 永远是黑洞。但 agent 可以带着你自己的 cookie / API key 一次性跨过这些墙，让"人们在哪儿投票"这件事可以被交叉比对和量化。

这篇文章回答三个问题：

1. **它怎么决定"该查哪些平台、查哪些人"**——v3 的 pre-research 引擎（`@j-sperling` 贡献）做了什么
2. **怎么把"upvote 1500 的 Reddit 帖"和"3.6M 播放的 TikTok"放在同一张榜上比较**——engagement scoring + cross-source cluster merging
3. **它怎么跨 50+ agent harness 工作**——Claude Code 插件、Codex、Cursor、OpenClaw、`agentskills.io` 规范、`.skill` 文件

## 它不是一个产品，是一个 Skill

第一件要理解的事：**`last30days-skill` 不是一个独立 CLI 工具，它是一个 [Agent Skill](https://agentskills.io)**。也就是说，它本身不直接搜索，而是给一个 agent（Claude Code / Codex / Cursor / OpenClaw 等）注入一份行为规范，agent 在执行 `/last30days Peter Steinberger` 这类命令时按规范去调度底层脚本。

入口在 `skills/last30days/SKILL.md`——README 里就明说"this README tracks the current v3 pipeline. The runtime skill spec lives in `skills/last30days/SKILL.md`, which is the source of truth"。

### 跨 50+ harness 的安装矩阵

| 入口 | 安装命令 | 更新方式 |
|------|---------|---------|
| **Claude Code** | `/plugin marketplace add mvanhorn/last30days-skill` | marketplace 自动更新 |
| **Codex / Cursor / Copilot / Gemini CLI 等 50+ harness** | `npx skills add mvanhorn/last30days-skill -g` | `npx skills update last30days -g` |
| **claude.ai Web** | 下载 `.skill` 文件 → Settings > Capabilities 上传 | 重新下载 |
| **OpenClaw** | `clawhub install last30days-official` | `clawhub update` |
| **手装（开发者）** | `git clone` + 软链到 `~/.claude/skills/last30days` | git pull |

注意一个细节：**Claude Code 上 marketplace 插件和 `npx skills` 不去重**，两个都装的话 `/last30days` 会出现两次。建议一台机器只用一种安装方式。

## 13 个数据源，按"信号强度"分层

`last30days` 的真正功夫在于**它怎么把异构信号归一化**。从 README 的"Source → What the people tell you"表格可以直接看到设计哲学：

| 数据源 | 归一化信号 | 成本 |
|--------|-----------|------|
| **Reddit** | upvote 排序 + top comments，公开 JSON，免费 | $0 |
| **Hacker News** | points / comments | $0 |
| **Polymarket** | % 赔率（不是美元成交额） | $0 |
| **GitHub** | stars / PR velocity / release notes | $0 |
| **X / Twitter** | like 排序的 thread | 浏览器 cookie 免费 |
| **YouTube** | 全字幕里筛出 5 句 quote 级别的话 | `yt-dlp` 免费 |
| **TikTok / Instagram / Threads** | engagement 排序 + 字幕 | ScrapeCreators API，100 次免费后 PAYG |
| **Bluesky** | AT Protocol posts | App password 免费 |
| **Perplexity Sonar** | 带 citation 的 grounding web search | OpenRouter PAYG |
| **Web** | 编辑型内容，但 README 直说"one signal of many" | Brave Search 2000 次/月免费 |
| **小红书（RED）** | 社区贡献接入 | 视上游 key |
| **Truth Social** | 社区贡献接入 | 视上游 key |
| **Digg**（`digg-pp-cli`） | X 上 1000 个高信噪比 AI 账号的 leaderboard，免 X auth | 视上游 |

几个**反常识**的设计点：

1. **Polymarket 显示 % 赔率而不是美元成交额**——理由是"$66K 成交量"对没做交易的人没意义，"74% 停火可能性"才有信号
2. **Per-author cap = 3**——防止任何一个大 V 单一声音主导
3. **`EXCLUDE_SOURCES=tiktok,instagram,threads`**——付费源按查询粒度关闭，避免意外账单
4. **Pinterest 单独 opt-in**——`--search=pinterest` 才会触发，因为"看图找感觉"和"找事实"是两种任务

## v3 的核心升级：pre-research 引擎

v2 的痛点：搜 "OpenClaw" 命中了一堆拼写相似的不相关项目。v3 加了 `j-sperling` 写的 **Python pre-research brain**，先做 entity resolution，再触发搜索：

```
"OpenClaw"
  → 解析为 @steipete (Peter Steinberger) + openclaw/openclaw 仓库
  → 找到 r/openclaw、r/ClaudeCode
  → 找到正确 YouTube channel、TikTok hashtag
  → 才发 API 请求
```

README 给了几个反例，差异是戏剧性的：

- 旧引擎搜 "Paperclip" 命中 1990s 电影、办公用品
- 新引擎 → @dotta → Paperclip org chart 仓库
- 旧引擎搜 "Dave Morin" 命中 LinkedIn、Farzad
- 新引擎 → @davemorin + @OpenClaw + TWiST 播客（双向：人→公司，产品→创始人）
- 旧引擎搜 "Peter Steinberger" 命中 ESET 老博客
- 新引擎 → @steipete (X) + steipete (GitHub) → 22 个 PR、3 个仓库、85% merge rate

这就是 README 那句"v3 finds content v2 never could" 的实际含义。

## Cross-source cluster merging

v2 把同一个故事在 Reddit + X + YouTube 上报成 3 条，v3 用 entity-based overlap detection 合并成 1 个 cluster。这和"搜 13 个平台然后 paste 13 个结果"是两套逻辑。

`/last30days "Iran vs USA"` 实际输出形式是：

> Day 38 of the war. Trump's Tuesday deadline for Iran to reopen the Strait of Hormuz. Two US warplanes downed. Oil at $126/barrel... Polymarket: ceasefire by Dec 31 at 74%. **27 X posts, 10 YouTube videos, 20 prediction markets** ——folded into one narrative.

## 几个 v3 的 killer feature

1. **GitHub person-mode**：`/last30days Peter Steinberger --github-user=steipete` 切到 author-scoped 查询，显示"他/她最近在 ship 什么"
2. **Auto-discovered competitors**：`/last30days OpenAI --competitors` 让推理模型先 WebSearch 找两个 peer（Anthropic、xAI），然后用同一个 engine 并行跑 3 个 pipeline，做 3-way 对比
3. **Best Takes**：v3 加了第二个 judge 给每条结果打"幽默分"，把 Reddit 那些高赞金句嵌进简报——"Tommy Lloyd's 'My Michael Jordan is Steve Kerr' scores low on relevance to 'Arizona Basketball' but off the charts on fun"
4. **ELI5 mode**：`/last30days Nano Banana Pro prompting eli5 on` 把同一份数据用大白话重写
5. **Shareable HTML brief**：`/last30days OpenClaw --emit=html` 输出一份自包含 dark-mode 文件，可以拖进 Slack/邮箱/Notion，无 JS 离线可看

## "为什么能 #1"——和当前 agent 生态的契合点

把时间线拉长看，`last30days-skill` 持续占据 trending 榜首，背后踩中了 2026 年 agent 生态的几个转折点：

- **agent skill marketplace 标准化**：`agentskills.io` 规范被 Claude Code / Codex / Cursor / Gemini CLI 等 50+ harness 采纳，让"一个 skill 一次写、跨平台用"成为可能
- **数据墙花园被自有 cookie / key 攻破**：X 不开放 API 但用户可以登入浏览器，agent 用 vendored Bird 客户端（项目里直接 vendored Node.js 包）拿 X 数据，这是合规的灰色但合法区域
- **真实信号优先于 SEO**：Google 2014 年后基本不索引 Reddit 评论，ChatGPT 有 Reddit deal 但看不到 X，"跨平台并行"是 2026 年唯一一个把这件事做到产品化的开源项目
- **judge agent 模式落地**：早期 deep research 产品（如 perplexity）"用 LLM 总结"是黑盒，`/last30days` 公开了 cross-source clustering + 多 judge 评分，是开源领域少有的"工程细节可审计"的研究 skill

## 谁该用、谁不该用

**适合**：

- 做销售/BD 的——`/last30days <目标公司 CEO>` 5 分钟拿到对方最近在 X / YouTube / HN 说什么
- 做投资研究的——`/last30days <赛道> --competitors` 自动跑出 3-way 对比
- 做内容创作的——直接拿到"社区在 30 天里达成共识的金句 + prompt 范式"
- 跟人开会/旅行前——`/last30days <对方姓名>` 30 天事实简报

**不适合**：

- 需要实时（< 1 小时）数据——这是 30 天窗口，不是新闻流
- 学术研究——需要正式 citation 链的场合（但 Perplexity Sonar + Brave 后端可以补）
- 不想配 key 也不想提供 cookie 的"开箱即用"用户——Reddit/HN/Polymarket/GitHub 之外，X 要 cookie、YouTube 要 `yt-dlp`、TikTok 要 ScrapeCreators

## 安装与试用

```bash
# Claude Code (推荐, 自动更新)
/plugin marketplace add mvanhorn/last30days-skill
/plugin install last30days

# Codex / Cursor / Gemini CLI 等 (npx skills, 全局)
npx skills add mvanhorn/last30days-skill -g

# OpenClaw
clawhub install last30days-official
```

第一次跑 `/last30days <topic>` 会触发 30 秒的 setup wizard，配置 X / YouTube / TikTok 等源的 cookie 和 key。零配置时 Reddit / HN / Polymarket / GitHub 立刻可用。

## 参考

- 仓库：[github.com/mvanhorn/last30days-skill](https://github.com/mvanhorn/last30days-skill)
- 安装矩阵 & key 配置：[CONFIGURATION.md](https://github.com/mvanhorn/last30days-skill/blob/main/CONFIGURATION.md)
- v3 pre-research 引擎贡献者：[@j-sperling](https://github.com/j-sperling)
- Agent Skills 规范：[agentskills.io](https://agentskills.io)
