---
title: "garden-skills：给编程智能体装上五项生产级技能的中文开源合集"
date: 2026-08-31T03:45:00+08:00
slug: "garden-skills-agent-skills-collection"
github_repo: "ConardLi/garden-skills"
source_key: "gh:ConardLi/garden-skills"
description: "ConardLi 的 garden-skills 是一套面向 Claude Code、Cursor、Codex 等编程智能体的生产级 Agent Skills 合集，含网页演示、设计工程、图像生成、知识检索与成文五个技能。本文拆解五个技能各自的定位与机制，并给出安装与选型建议。"
draft: false
categories: ["技术笔记"]
tags: ["Agent Skills", "Claude Code", "开源", "AI 编程"]
---

# garden-skills：给编程智能体装上五项生产级技能的中文开源合集

## 核心判断

**Agent Skills（智能体技能）正在成为编程智能体生态的"包管理单位"**：一个 SKILL.md 加若干参考文件，就能把一套复杂工作流注入 Claude Code、Cursor 或 Codex。garden-skills 是这个方向上少见的、由中文开发者 ConardLi 维护并自带完整中文文档的高质量合集——五个技能各管一段真实生产力场景，不是演示品。

一句话定位：**它把"让 AI 做网页演示""让 AI 有设计品味""让 AI 检索本地知识库"这类原本要写长提示词才能凑合完成的事，固化成了可安装、可版本化、跨智能体复用的技能包。**

写作时数据：11,754 Stars / 1,452 Forks / MIT 协议，主要语言 CSS，仓库持续更新（2026 年 8 月仍有提交活跃）。

## 五个技能各是什么

| 技能 | 类别 | 一句话定位 |
|------|------|-----------|
| `web-video-presentation` | 网页视频 / 演示 | 把文章、课程、产品演示变成可录屏的 16:9 网页演示 |
| `web-design-engineer` | 设计 / 前端 | 让 AI 生成的页面从"能看"变成"有设计品味" |
| `gpt-image-2` | 图像生成 / 提示词 | 围绕 GPT-Image-2 的图像生成工作流 |
| `kb-retriever` | 检索 / 本地知识库 | 从本地 knowledge/ 目录带证据地回答问题 |
| `beautiful-article` | 内容生产 | 任意素材源 → 排版精良的成文 |

值得注意的一点：README 徽章写 "skills-5"，与目录中五个技能一一对应，不存在虚标。

## 两个代表性技能的机制拆解

### web-video-presentation：把演示做成"生产表面"

这个技能的思路不是"生成一个 PPT 网页"，而是构建一个**可录屏的视频生产环境**：

- 固定 1920×1080 舞台，随视口缩放，保证录屏画面稳定；
- 用 `(chapter, step)` 二元组做点击/键盘驱动的播放游标，每个视觉步骤对应一条旁白节拍；
- 在脚本、主题、大纲、实现模式、可选音频五个环节设硬性协作检查点，AI 不会一口气跑完才让你看结果；
- 23 套内置主题（编辑风、终端风、工程风、瑞士国际主义等），主题走 token 架构；
- TTS 可插拔：内置 MiniMax `mmx-cli` 与 OpenAI TTS（curl 直调）两个 provider，另附 ElevenLabs、edge-tts、Azure、Google Cloud、macOS `say` 的接入契约。

对内容创作者来说，这意味着"一篇文章 → 一支带旁白的演示视频"的链路被压到了几次点击。

### kb-retriever：带边界的渐进式检索

`kb-retriever` 解决的是智能体读本地知识库时的通病——一把梭把整个文件灌进上下文。它的做法：

- 用分层的 `data_structure.md` 索引文件先导航、后检索，而不是直接搜内容；
- 对 PDF 和 Excel 强制"先学后处理"：先读技能内置的参考文档，再做提取或分析；
- 精确关键词、局部窗口读、同义词与迭代精化组合使用；
- 检索轮次硬性封顶 5 轮，防止探索失控；
- 回答必须带来源，工作流覆盖 `grep`、`pdftotext`、`pdfplumber`、`pandas`。

这组约束的设计密度，是它区别于"又一个 RAG 脚本"的地方。

### 其余三个速览

- `web-design-engineer`：核心是"设计工程师"工作流——先理解产品语境，声明设计系统，出 v0，再构建完整体验；内含六派设计方向顾问与 25 套锚定风格配方（Linear、Aesop、Bloomberg Terminal、Stripe Press 等），还带一份反俗套黑名单，专门对冲 AI 生成页面的"千篇一律感"。
- `gpt-image-2`：围绕 GPT-Image-2 的图像生成与提示词工程技能。
- `beautiful-article`：任意素材源到排版精良文章的成文技能。

## 安装：四条路径

**方式 A：`skills` CLI（推荐，智能体无关）**

```bash
# 安装全部五个技能（最新版）
npx skills add ConardLi/garden-skills

# 只装一个
npx skills add ConardLi/garden-skills -s web-design-engineer

# 装到全局 ~/.skills 而非项目 ./skills
npx skills add ConardLi/garden-skills -s gpt-image-2 --global

# 指定目标智能体
npx skills add ConardLi/garden-skills -s kb-retriever -a claude-code
```

默认跟踪 `main` 最新提交，覆盖 95% 场景。生产/CI 需要锁版本时，用 tag 限定的 tree URL 精确到某次 release：

```bash
npx skills add ConardLi/garden-skills/tree/web-design-engineer-v1.0.0/skills/web-design-engineer
```

常用子命令：`npx skills list` / `find` / `update` / `remove`。

**方式 B：Claude Code 插件市场**——`/plugin marketplace add ConardLi/garden-skills` 后按包安装（presentation、web-design、knowledge-base、image-generation 四个 pack）。

**方式 C：Releases 页的固定版本 `.zip`**——每个技能的 README 链接行都有对应当前版本的下载地址，例如 web-design-engineer 当前为 v1.3.0。

**方式 D / E：手动拷贝或 git submodule**——适合需要魔改或内网分发的团队。

## 适用边界

- 这些技能的收益前提是你的智能体支持 Agent Skills 规范（SKILL.md）；不支持的运行时只能把 SKILL.md 当提示词素材手抄。
- `web-video-presentation` 产出的是网页演示，不是直接渲染的 MP4——录屏环节仍需你自己完成；TTS 音频合成依赖对应 provider 的可用性。
- `kb-retriever` 是本地目录检索，不涉及向量化语义搜索；它的价值在渐进导航与来源可溯，语义模糊匹配不是强项。
- 技能版本各自独立演进（web-design-engineer 已到 v1.3.0，kb-retriever v1.0.1），升级时按需单技能更新，不要假设合集整体同步。

## 采用建议

如果你已经在用 Claude Code、Cursor 或 Codex 做日常开发，garden-skills 的性价比很高：一条 `npx skills add` 就能试装单个技能，不满意 `remove` 即走。建议的试用顺序：先 `kb-retriever`（见效最快、无外部依赖），再 `web-design-engineer`（对前端产出质量提升最直观），最后按内容创作需求上 `web-video-presentation`。
