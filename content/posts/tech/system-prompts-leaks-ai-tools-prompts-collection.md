---
title: "system_prompts_leaks 深度解读：4.2 万 Stars 的 AI 系统提示词档案，以及它为什么是 prompt engineering 的现实教材"
date: "2026-06-15T21:08:29+08:00"
slug: system-prompts-leaks-ai-tools-prompts-collection
description: "asgeirtj/system_prompts_leaks 收录 14 家厂商 100+ 套 AI 系统提示词，是公开最完整的 prompt 档案。本文拆解归档结构、版本演进、引用方式与合规边界。"
tags: ["Prompt Engineering", "Claude", "ChatGPT", "Gemini", "AI 工具"]
categories: ["技术笔记"]
author: 钳岳星君
---

# system_prompts_leaks 深度解读：4.2 万 Stars 的 AI 系统提示词档案，以及它为什么是 prompt engineering 的现实教材

## 学习目标

通过本文，你将能够：

- 理解 system_prompts_leaks 仓库的价值：唯一同时覆盖 14 家厂商、100+ 套 AI 系统提示词的公开档案
- 读懂档案结构：按厂商分顶层目录，每个厂商目录下按产品/模型/入口分文件
- 理解一份典型 system prompt 的 6 个标准模块：行为总则、搜索优先、产品信息、默认立场、工具 prompt、风格与用户偏好
- 知道怎么把这份档案当成 prompt engineering 的"现实教材"使用
- 了解合规、引用与转载边界

## 目录

1. [阅读导航](#阅读导航)
2. [先看结论](#先看结论)
3. [档案结构全图](#档案结构全图)
4. [一份典型 system prompt 拆解](#一份典型-system-prompt-拆解)
5. [它怎么变成一本 prompt engineering 的活教材](#它怎么变成一本-prompt-engineering-的活教材)
6. [版本时间线（截至 2026-06-15）](#版本时间线截至-2026-06-15)
7. [怎么用这个仓库](#怎么用这个仓库)
8. [引用与转载的合规边界](#引用与转载的合规边界)
9. [这份档案的局限](#这份档案的局限)
10. [怎么贡献或反馈](#怎么贡献或反馈)
11. [适合谁、不适合谁](#适合谁不适合谁)
12. [总结](#总结)
13. [自测题](#自测题)
14. [练习](#练习)
15. [进阶路径](#进阶路径)
16. [资料口径说明](#资料口径说明)

---

**判断**：这个仓库不是 prompt 资料合集那么简单——它是目前公开渠道里**唯一同时覆盖 Anthropic、OpenAI、Google、xAI、Perplexity、Cursor、Microsoft、Meta、Mistral、Notion、Qwen、Misc 12 个产品线、且持续按版本更新**的系统提示词档案。2025-05 立项到 2026-06，14 个月内拿到 42K+ stars、7K+ forks、登上 GitHub Trending，**The Washington Post 也引用过它**（2026-05-11 报道：让读者用 AI 工具的真实 system prompt 改写新闻稿）。

如果你想搞清楚下面任何一件事，这篇都值得读：

- AI 厂商在 system prompt 里到底在约束什么、隐藏什么、对外宣称什么
- 同一个模型在 ChatGPT Web、Codex CLI、API 三种入口下，prompt 怎么分层
- 哪个模型什么时候发布过哪些工具 prompt，diff 怎么对照看
- 把这个仓库当成 prompt engineering 的"现实教材"时，哪些是公开可学的，哪些是反爬擦边

---

## 阅读导航

- **想快速判断仓库值不值得 clone**：先看「先看结论」
- **想知道每个目录代表什么产品线**：看「档案结构全图」
- **想知道 system prompt 里通常包含哪些模块**：看「一份典型 system prompt 拆解」
- **想用它做 prompt engineering 复盘**：看「它怎么变成一本活教材」
- **想了解合规、引用与转载边界**：看「合规与边界」
- **想知道仓库里现在有哪些版本、哪些能直接读**：看「版本时间线（截至 2026-06）」

---

## 先看结论

| 维度 | 实际情况 |
|------|----------|
| Stars | 42,327+（2026-06-15 抓取） |
| Forks | 7,036+ |
| 主要语言 | JavaScript（仓库只用于展示静态文件，本身不运行代码） |
| 协议 | CC0-1.0（公有领域，可商用、可改、可不署名） |
| 收录厂商 | 14 家：Anthropic、OpenAI、Google、xAI、Perplexity、Microsoft、Cursor、Meta、Mistral、Notion、Qwen、Misc 12 个目录 |
| 收录产品 | 100+ 个独立 prompt（Web、API、Codex、CLI、Tools、Cowork、Perplexity Computer 等不同入口） |
| 更新频率 | 高频。最近一条 2026-06-09，三日内连发 Claude Fable 5、Opus 4.8、Claude Code Glob/Grep 三份 |
| 维护者 | asgeirtj（个人维护者），联系邮箱 / X 见 README 底部 |
| 引用记录 | The Washington Post 2026-05-11 报道直接调用过仓库内容 |
| 仓库 URL | <https://github.com/asgeirtj/system_prompts_leaks> |

一句话：**它是 prompt engineering 的「GitHub 源码层」，不是教程，是底层素材**。

---

## 档案结构全图

仓库按厂商分顶层目录。每个厂商目录下，再按产品 / 模型 / 入口分文件。命名规则统一是「产品 + 模型 + 入口后缀」。

```text
system_prompts_leaks/
├── README.md                 # 总索引（带 model 表格 + diff 链接）
├── Anthropic/                # Claude 系列
│   ├── claude-fable-5.md
│   ├── claude-opus-4.8.md
│   ├── claude-opus-4.7.md
│   ├── claude-sonnet-4.6.md
│   ├── claude-cowork.md
│   ├── claude-cowork-dispatch.md
│   ├── claude-design.md
│   ├── claude-for-excel.md
│   ├── claude-in-chrome.md
│   ├── claude-mobile-ios.md
│   ├── anthropic_reminders.md
│   ├── Claude Code/          # Claude Code 子目录
│   │   ├── claude-code-opus-4.8.md
│   │   ├── claude-code-opus-4.6.md
│   │   ├── glob-tool.md
│   │   ├── grep-tool.md
│   │   ├── deferred-tools.md
│   │   ├── claude-code-docs-assistant.md
│   │   └── bundled-skills/
│   ├── Official/             # 发布日快照（不更新）
│   ├── raw/                  # 原始 prompt（未美化）
│   ├── old/                  # 旧版本
│   └── visualize.md
├── OpenAI/                   # ChatGPT / GPT / Codex
│   ├── gpt-5.5-thinking.md
│   ├── gpt-5.5-instant.md
│   ├── gpt-5.5-api.md
│   ├── gpt-5.5-pro-api.md
│   ├── gpt-5.4-thinking.md
│   ├── Codex/                # Codex CLI 子目录
│   ├── tool-web-search.md
│   ├── tool-deep-research.md
│   ├── tool-python.md
│   ├── tool-canvas-canmore.md
│   ├── tool-create-image-image_gen.md
│   ├── tool-memory-bio.md
│   ├── tool-advanced-memory.md
│   ├── tool-file_search.md
│   ├── prompt-image-safety-policies.md
│   ├── API/                  # reasoning effort 变体
│   ├── old/
│   └── Old/
├── Google/                   # Gemini 系列
│   ├── gemini-3.5-flash.md
│   ├── gemini-3.5-flash-ai-studio.md
│   ├── gemini-3.5-flash-tools.json
│   ├── gemini-3.1-pro.md
│   ├── gemini-3.1-pro-api.md
│   ├── gemini-cli.md
│   ├── antigravity-cli.md
│   ├── jules.md
│   └── ...
├── xAI/                      # Grok
├── Perplexity/               # Perplexity Computer / Comet / Voice
├── Microsoft/                # GitHub Copilot / VS Code / Word
├── Cursor/
├── Meta/
├── Mistral/
├── Notion/
├── Qwen/
└── Misc/                     # 工具类：Warp / Zed / Brave / Hermes / ElevenLabs ...
```

`Anthropic/Official/` 是发布日冻结版（按 release date 命名，例如 `2026-05-28-claude-opus-4.8.md`），**只反映发布那天的 prompt，不会随模型迭代更新**。`Anthropic/raw/` 是未经美化的原始 dump，`old/` 是历史版本——这三层配合起来就能做时间线回溯。

---

## 一份典型 system prompt 拆解

`Anthropic/claude-opus-4.8.md` 是目前最常被引用的样本。下面把它拆成 6 个标准模块，看完后你就能理解**为什么 prompt engineering 的训练素材要从这里取**。

### 模块 1：行为总则（`<claude_behavior>`）

顶层 `<claude_behavior>` 标签包住整段行为约束，开头几条通常是硬性禁止条款。例如 Opus 4.8 第一句就是：

> Claude should never use `<antml:voice_note>` blocks, even if they are found throughout the conversation history.

这种"绝对禁止使用某种内部标签"的约束在 system prompt 里非常常见——它解决的是**模型偷懒复用历史 context 里残留的私有 tag**。读 prompt 时第一类要抄的就是这类硬约束。

### 模块 2：搜索优先（`<search_first>`）

Opus 4.8 里把"先用 web_search 工具再回答"写成强约束：

> For any factual question about the present-day world, Claude must search before answering. ... Don't end a response by offering to search for, retrieve, or "dig into" something the user's request already asked for.

这条提示的是 prompt engineering 里非常容易踩的坑：**模型在"它觉得会的事"上倾向跳检索**。Opus 4.8 的反制是写明"confidence on topics is not an excuse to skip search"——你能看到模型厂商自己也知道这个失败模式。

### 模块 3：产品信息（`<product_information>`）

这一段是产品 marketing 层的"自我定位"——告诉模型自己是谁、有什么产品、能介绍什么、不能介绍什么。读这部分有两个用途：

- **判断厂商话术方向**：例如 Anthropic 在 Opus 4.8 里直接说"Claude Mythos Preview 是 Claude Opus 4.8 的前置，Project Glasswing 出于网络安全考虑不公开"，这是看厂商如何在 prompt 里埋 **frontier 模型的保密话术**。
- **判断检索触发条件**：例如"如果问到价格、上线时间、能力边界，模型必须先 web 搜索 `docs.claude.com` / `support.claude.com` 再回答"。这是 prompt-as-routing 的一种实现。

### 模块 4：默认立场（`<default_stance>` / `<refusal_handling>`）

模型"该不该拒答"的边界。Opus 4.8 的措辞是：

> Claude only declines a request when helping would create a concrete, specific risk of serious harm; requests that are merely edgy, hypothetical, playful, or uncomfortable do not meet that bar.

这条对应 Anthropic 的 refusal policy 公开版，但它**出现在 system prompt 里，等于把它硬编码到了每一次对话的上下文**。对照 OpenAI、xAI、Perplexity 的同类段，能看到各家"默认拒 / 默认帮"的政策差异。

### 模块 5：工具 prompt（`<tool_use>` / `Claude Code/`）

工具 prompt 是另一个独立层级。Opus 4.8 的 Web 版只挂 web_search；**Claude Code 版**（`Anthropic/Claude Code/claude-code-opus-4.8.md`）则多了一整套 Bash / Edit / Glob / Grep 工具 prompt。最近 2026-06-09 单独抽出 `glob-tool.md` / `grep-tool.md` / `deferred-tools.md`，等于把工具 prompt **模块化**了，未来发新模型时只换模型层、工具层复用。

### 模块 6：风格与用户偏好（`<style>` / 用户偏好）

最后一段通常是"如何措辞"、"长度"、"格式"。Opus 4.8 的 `<default_styles>` 在 `Anthropic/default-styles.md` 里独立维护，**不绑死具体模型**——这也是为什么仓库里把"风格"和"模型"拆成两个文件。

---

## 它怎么变成一本 prompt engineering 的活教材

把这份档案当成"现实教材"读，比读论文 / 博客都更直接。下面列出 4 类常见使用方式。

### 1. 同一模型在多入口下的 prompt 分层

GPT-5.5 在仓库里至少有 5 份：

- `gpt-5.5-thinking.md`（Web ChatGPT，思考模式）
- `gpt-5.5-instant.md`（Web ChatGPT，即时模式）
- `gpt-5.5-api.md`（API 直调）
- `gpt-5.5-pro-api.md`（Pro API）
- `Codex/gpt-5.5.md`（Codex CLI）

对照读能立刻看出**Web / API / CLI 三层 prompt 的差异**：

- Web 版要解决 UI 表达（消息格式、引用方式、Artifacts 行为）
- API 版要解决调用方责任（reasoning effort、tool calling schema）
- CLI 版要解决 shell 行为（命令执行、文件编辑、规划模式）

这就是 prompt engineering 里常说的"**同一个模型，prompt 必须按入口定制**"。

### 2. 同厂商不同模型的 prompt 演进

Claude Opus 4.5 → 4.6 → 4.7 → 4.8 → Fable 5，全部留存在 `Anthropic/`。同厂商的演进最容易看：

- **行为约束**怎么越写越细（从"don't"到"don't do X in context of Y"）
- **工具 prompt** 怎么从内嵌变外挂（`bundled-skills/`、`glob-tool.md`）
- **产品话术**怎么跟着发布节奏更新（每次发新模型都加一段新产品段落）

仓库首页有 `Diff: Claude Opus 4.8 → Claude Fable 5` 链接，直接用 diffchecker 比对——这是看 prompt 演进最省事的入口。

### 3. 跨厂商的 prompt 风格对比

把 4 家的"refusal stance"放一起读：

- Anthropic：默认帮、明确写"merely edgy 不构成拒答理由"
- OpenAI：偏 policy 驱动，常用 `<policy>` 标签分段
- Google：偏产品能力介绍，"Gemini 能做 X / Y / Z"
- xAI：明显更"放飞"，persona 多（build / expert / account 等多个 prompt）

读完一遍，你就能在自己的 prompt 里**判断该往哪个方向走**——不是抄，是**对照选择**。

### 4. 工具 prompt 模板的复用

`OpenAI/tool-web-search.md`、`OpenAI/tool-deep-research.md`、`OpenAI/tool-file_search.md` 这类**工具 prompt** 是写自家 Agent 工具描述时的最佳参考。读它们能看到：

- 工具 prompt 怎么写 input schema 描述
- 怎么写 fallback 行为（工具失败时模型该怎么做）
- 怎么写"工具输出"对模型后续行为的影响

如果自己在写 LangChain / LlamaIndex 的自定义工具，**这些 prompt 就是公开 reference**。

---

## 版本时间线（截至 2026-06-15）

只列最近一个月内仍然有效的活跃更新（仓库首页 "Recently Updated" 表）：

| 时间 | 厂商 | 产品 | 入口 | 文件 |
|------|------|------|------|------|
| 2026-06-09 | Anthropic | Claude Fable 5 | claude.ai | `Anthropic/claude-fable-5.md` |
| 2026-06-09 | Anthropic | Claude Opus 4.8 | claude.ai | `Anthropic/claude-opus-4.8.md` |
| 2026-06-09 | Anthropic | Claude Code Glob / Grep 工具 | Claude Code | `Anthropic/Claude Code/glob-tool.md`、`grep-tool.md` |
| 2026-05-28 | Anthropic | Claude Code (Opus 4.8) | Claude Code | `Anthropic/Claude Code/claude-code-opus-4.8.md` |
| 2026-05-28 | Anthropic | Cowork / Cowork Dispatch | Desktop | `Anthropic/claude-cowork.md`、`claude-cowork-dispatch.md` |
| 2026-05-24 | OpenAI | GPT-5.5 多入口 | ChatGPT / API | `OpenAI/gpt-5.5-*.md` |
| 2026-05-21 | Perplexity | Perplexity Computer | Web | `Perplexity/perplexity-computer.md` |
| 2026-05-21 | Microsoft | VS Code Copilot Agent | VS Code | `Microsoft/vscode-copilot-agent.md` |
| 2026-05-21 | Misc | Docker Gordon AI | Docker | `Misc/docker-gordon-ai.md` |
| 2026-05-20 | Google | Gemini 3.5 Flash | Web / AI Studio | `Google/gemini-3.5-flash.md` 等 |
| 2026-05-20 | Google | Antigravity CLI | CLI | `Google/antigravity-cli.md` |
| 2026-05-16 | Misc | Zed AI | Editor | `Misc/zed.md` |
| 2026-05-11 | xAI | Grok Expert | Web | `xAI/grok-expert.md` |

更老的版本（GPT-4.5、GPT-4.1、Claude Sonnet 3.7、Gemini 2.5 等）放在各厂商的 `old/` 或 `Old/` 子目录，**仅作历史参考**。

---

## 怎么用这个仓库

### 1. 在浏览器里直接读

所有 `.md` 文件都能通过 GitHub Web 端直接打开。点开 `Anthropic/claude-opus-4.8.md`，顶部就是完整 system prompt。如果想对比，直接看 `claude-opus-4.7.md` / `claude-opus-4.6.md` 三份。

### 2. 整库 clone 下来离线读

```bash
git clone https://github.com/asgeirtj/system_prompts_leaks
cd system_prompts_leaks
# 用 ripgrep 搜索关键词，例如想看哪几家写了 "refusal"
rg -i "refusal" --type md | head
```

仓库只有 Markdown + 几个 json（Google Gemini 工具清单），克隆下来不到 5 MB。

### 3. 当作 LLM 微调 / 评估数据

CC0-1.0 协议允许商用，**可以直接拿去做 SFT（监督微调）数据集**。常见做法：

- 用 `Anthropic/` 整目录当"system prompt → 模型应该怎么说话"的对齐语料
- 用 `OpenAI/tool-*.md` 当"工具描述 → 工具调用 schema"的训练样本
- 用跨厂商的 refusal 段做"policy 边界"分类任务

注意：仓库 README 没声明这部分用途官方背书，自用研究没问题，发论文 / 商用产品里要明确写"来源：asgeirtj/system_prompts_leaks, CC0-1.0"。

### 4. 配合 diff 工具看版本变化

README 顶部直接挂了 `Diff: Claude Opus 4.8 → Claude Fable 5` 的 diffchecker 链接。要看其他对比，可以本地：

```bash
diff -u Anthropic/old/claude-opus-4.5.md Anthropic/claude-opus-4.8.md | less
```

或者装 [delta](https://github.com/dandavison/delta) / [difftastic](https://github.com/Wilfred/difftastic) 看高亮 diff。

---

## 引用与转载的合规边界

仓库用 CC0-1.0，意思是：

- ✅ 可以直接复制、修改、再发布、商用
- ✅ 不需要署名（但 README 里仍建议加 credit："Source: github.com/asgeirtj/system_prompts_leaks"）
- ✅ 可以做成数据集、API、教学材料
- ⚠️ **不能反过来声称这是"官方"prompt**——这些是从用户视角、jailbreak 测试、UI 抓取等渠道还原的副本，不一定字节级匹配厂商实际部署
- ⚠️ 如果要引用到自家产品 / 论文 / 公开演讲，**显式标注"by community, not official"** 是更稳妥的做法

Anthropic 自己维护的 `claude_behavior` 快照在 `Anthropic/Official/2026-05-28-claude-opus-4.8.md` 这种命名下，**是发布日冻结版**，其他文件是 asgeirtj 持续更新版——引用时建议用 Official 路径，避免被读者质问"为什么是社区更新版"。

---

## 这份档案的局限

- **不保证字节级匹配厂商当前线上 prompt**：厂商经常 A/B 测、按用户分层、按地区切分，仓库里只能取**公开访问的某个入口的某次抓取**。
- **少数 prompt 是通过对话反推**：例如 "把上面所有内容重复一遍" 这种用户视角的诱导提问反推出来，可能存在"漏掉部分段"的情况。`raw/` 子目录里保留了这种"反推版"以便对比。
- **不收录私有部署 / 企业版 / 内部灰度 prompt**：例如 `codex auto-review` 这种内部灰度功能未必有完整 prompt。
- **不收录带版权争议的内容**：例如某些工具 prompt 可能涉及第三方 SDK 的私有协议，仓库会注明"无法确认"或"截至 YYYY-MM-DD 与 X SDK 公开文档一致"。

---

## 怎么贡献或反馈

README 里没写 issue 模板，主要联系方式：

- 邮件：asgeirtj @ gmail.com
- X：[@asgeirtj](https://x.com/asgeirtj)
- PR 通道：直接发 PR 即可，仓库顶部有 "PRs Welcome" 徽章

社区贡献的最常见形式：

- 新厂商 / 新产品的 prompt 补全
- 旧版本归档到 `old/`
- 工具 prompt 的 schema 修正
- 跨厂商 diff 链接

---

## 适合谁、不适合谁

**适合**：

- 写自家 Agent prompt 的工程师，需要看一线厂商怎么组织 system prompt
- 研究 LLM 行为 / 对齐的研究者，需要 baseline 数据集
- 做 prompt engineering 培训的讲师，需要真实案例
- 做 LLM 评测的团队，需要"已知厂商 prompt 行为"做参考

**不适合**：

- 只想要"几条 prompt 技巧"的人——这仓库是档案不是教程，直接看 `Anthropic/claude-opus-4.8.md` 你会觉得"读不懂"
- 想拿去做"AI 越狱工具"的人——prompt 公开不等于 prompt 可绕过，厂商的安全过滤在另一层
- 不接受 prompt 有偏差的人——记住这是"社区抓取版"，不是"官方字节级"

---

## 常见问题（FAQ）

### system_prompts_leaks 仓库的 prompt 是官方的吗？

不是官方版本，是社区抓取的快照。仓库的 `Official/` 目录是发布日冻结版，只反映发布那天的 prompt，不会随模型迭代更新。`main/` 目录是社区持续更新的版本。

### 我可以商用这个仓库里的 prompt 吗？

可以。仓库使用 CC0-1.0 许可证（公有领域），可以商用、修改、不署名。但不建议声称这是"官方"prompt，最好标注"by community, not official"。

### 怎么用这个仓库学习 prompt engineering？

建议流程：1. 按厂商扫一遍 README 索引；2. 选 1-2 份完整 prompt 通读；3. 打开 `Official/` 看发布日快照；4. 打开 `old/` 看历史；5. 用 diff 看演变。

### 同一模型在不同入口（Web/API/CLI）的 prompt 为什么不同？

因为不同入口的用户场景、可用工具、输出格式要求不同。Web 入口需要搜索优先、产品话术；API 入口需要简洁、可定制；CLI 入口需要代码执行、终端交互。

### system_prompts_leaks 的 prompt 准确吗？

仓库里的 prompt 是社区抓取版，不保证字节级匹配厂商实际部署。适合作为 prompt engineering 的研究素材，不适合作为官方文档引用。

---

## 总结

`asgeirtj/system_prompts_leaks` 的真正价值不是某一份 prompt，而是**它把 14 家厂商、100+ 产品、多种入口的 system prompt 维护成一份活的、公开的、可 diff 的档案**。在 prompt engineering 这个领域，**底层素材 > 上层方法**，而这个仓库就是 2026 年目前最完整的底层素材库。

如果你正在做以下任何一件事，建议 clone 下来而不是只在线浏览：

- 写自己产品的 system prompt
- 给团队做 prompt 培训
- 做 LLM 行为评估 / 红队测试
- 研究厂商 prompt 演进史

用法上，**先按厂商扫一遍 README 索引 → 选 1-2 份完整 prompt 通读 → 打开 `Official/` 看发布日快照 → 打开 `old/` 看历史 → 用 diff 看演变**——这是 30 分钟内能把这仓库价值榨干的标准流程。

---

## 自测题

1. **system_prompts_leaks 仓库的核心价值是什么？**
   <details>
   <summary>点击查看答案</summary>
   它是目前公开渠道里唯一同时覆盖 14 家厂商、100+ 套 AI 系统提示词的公开档案，并且持续按版本更新。
   </details>

2. **一份典型 system prompt 包含哪 6 个标准模块？**
   <details>
   <summary>点击查看答案</summary>
   1. 行为总则；2. 搜索优先；3. 产品信息；4. 默认立场（拒答处理）；5. 工具 prompt；6. 风格与用户偏好。
   </details>

3. **怎么把 system_prompts_leaks 当成 prompt engineering 的教材使用？**
   <details>
   <summary>点击查看答案</summary>
   可以：1. 对照读同一模型在多入口下的 prompt 分层；2. 看同厂商不同模型的 prompt 演进；3. 跨厂商的 prompt 风格对比；4. 工具 prompt 模板的复用。
   </details>

4. **system_prompts_leaks 仓库的 License 是什么？有什么使用限制？**
   <details>
   <summary>点击查看答案</summary>
   CC0-1.0（公有领域），可以商用、改、不署名。但不能声称这是"官方"prompt，最好标注"by community, not official"。
   </details>

5. **`Anthropic/Official/` 目录的作用是什么？**
   <details>
   <summary>点击查看答案</summary>
   是发布日冻结版，只反映发布那天的 prompt，不会随模型迭代更新。适合作为引用时的官方来源。
   </details>

---

## 练习

### 练习 1：对照读同一模型的多入口 prompt
1. 打开 `OpenAI/` 目录
2. 找到 GPT-5.5 的 5 份 prompt（Web、API、CLI 等）
3. 对照读，理解 Web / API / CLI 三层 prompt 的差异
4. 总结不同入口的 prompt 设计要点

### 练习 2：看 prompt 演进
1. 打开 `Anthropic/` 目录
2. 找到 Claude Opus 4.5 → 4.8 的 prompt 文件
3. 使用 diff 工具（如 delta 或 difftastic）对比差异
4. 分析行为约束、工具 prompt、产品话术的演进

### 练习 3：提取工具 prompt 模板
1. 打开 `OpenAI/tool-web-search.md`
2. 分析工具 prompt 的结构：input schema 描述、fallback 行为、工具输出处理
3. 提取可复用的模板
4. 应用到自己的 Agent 工具描述中

---

## 进阶路径

1. **深入研究 prompt engineering**：基于这份档案，系统学习 prompt 设计、优化、评估的方法
2. **分析各家 AI 厂商的 prompt 风格**：深入分析 Anthropic、OpenAI、Google、xAI 等的 prompt 设计哲学
3. **构建自己的 prompt 模板库**：基于这份档案和自己的经验，构建可复用的 prompt 模板库
4. **参与 prompt engineering 社区**：分享你的 prompt 工程经验，参与社区讨论
5. **研究 LLM 行为与安全**：基于 system prompt 分析，研究 LLM 的行为边界和安全机制

---

## 资料口径说明

1. **信息来源**：本文基于 asgeirtj/system_prompts_leaks 仓库的 README（2026-06-15 版本）和仓库内容分析
2. **版本时效性**：仓库高频更新，本文描述的文件和版本基于 2026-06-15 时点的快照
3. **prompt 准确性**：仓库里的 prompt 是社区抓取版，不保证字节级匹配厂商实际部署
4. **合规边界**：仓库用 CC0-1.0，但引用时建议标注"by community, not official"
5. **使用建议**：这份档案是底层素材，适合有 prompt engineering 基础的人深入研究

---

用法上，**先按厂商扫一遍 README 索引 → 选 1-2 份完整 prompt 通读 → 打开 `Official/` 看发布日快照 → 打开 `old/` 看历史 → 用 diff 看演变**——这是 30 分钟内能把这仓库价值榨干的标准流程。
