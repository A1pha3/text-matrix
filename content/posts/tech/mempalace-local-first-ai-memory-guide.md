---
title: "MemPalace：本地优先的 AI 记忆系统，96.6% R@5 背后的设计逻辑"
date: 2026-05-21T12:37:56+08:00
slug: "mempalace-local-first-ai-memory-guide"
description: "MemPalace 是一款本地优先的 AI 记忆系统，采用原文存储（verbatim）和语义搜索，检索层可插拔，默认后端为 ChromaDB。它通过 wing/room/drawer 三级索引结构组织记忆，支持 Claude Code、Gemini CLI 和 MCP 工具，在 LongMemEval 上以 96.6% R@5（无需 LLM）取得当前最高开源得分。"
draft: false
categories: ["技术笔记"]
tags: ["AI Memory", "Local-First", "ChromaDB", "MCP", "Semantic Search", "MemPalace"]
---

# MemPalace：本地优先的 AI 记忆系统，96.6% R@5 背后的设计逻辑

MemPalace 解决的不是"怎么调用模型"，而是"怎么让 AI 在多轮对话里记住真正重要的东西"。它把对话历史存成原文，用语义搜索召回，不需要任何 API key 就能跑出 96.6% R@5 的检索得分。这个数字来自纯语义搜索，没有任何 LLM 参与的启发式重排或摘要步骤——这是它和同类项目最本质的区别。

## 系统地图

MemPalace 不是一个平坦的向量数据库。它用一套三级索引结构把记忆组织成"宫殿"，每一级对应不同的语义粒度：

| 层级 | 名称 | 语义角色 |
|------|------|----------|
| wing | 翼 | 人或项目，是最高维度的记忆容器 |
| room | 房间 | 话题或项目内的子领域，用来缩小搜索范围 |
| drawer | 抽屉 | 原始内容本身——对话原文、文件片段、工具调用记录 |

记忆以原文形式存入 drawer，系统不做摘要、不提取、不 paraphrase。检索时，先用 wing 定位人/项目，再用 room 收窄话题范围，最后在 drawer 层做语义匹配。这种分层的结构化召回，是它能跑出 96.6% R@5 的关键之一——它把"在全部记忆里做向量相似度搜索"这件暴力的事，压缩到了更小、更相关的搜索空间里。

## 核心机制：原文存储与可插拔检索

MemPalace 遵循**原文存储**（verbatim）原则。这和 Mem0、Mastra 等"提取关键信息再存"的方案正好相反。原文存储的优点是信息不丢失，代价是存储体积更大，但 ChromaDB 默认的嵌入模型只需要约 300 MB 磁盘空间，对于个人项目级别的记忆库来说完全可以接受。

检索层通过 [`mempalace/backends/base.py`](https://github.com/MemPalace/mempalace/blob/main/mempalace/backends/base.py) 定义抽象接口，可以接入任意向量后端。当前默认是 ChromaDB，但换成其他向量库不需要改动核心代码。这是一个有意为之的工程选择：把"记忆怎么组织"和"记忆怎么存"分开。

## 知识图谱：时间维度的事实管理

除了向量检索，MemPalace 还内置了一张**时序实体关系图**（temporal entity-relationship graph）。这张图用本地 SQLite 存储，支持 add、query、invalidate 和 timeline 四类操作，每条边自带有效期窗口（validity window）。

这解决了一个向量搜索天然不擅长的问题：**事实的时效性**。当团队改了一个架构决策、换了一套工具链，向量库里"过去说过的话"不会自动失效。图谱层提供了显式的失效机制，让记忆系统在"我知道有过这个决定"之外，还能区分"这个决定现在还作不作数"。

## MCP 服务：29 个工具覆盖 palace 全操作

MemPalace 提供了 29 个 MCP（Model Context Protocol）工具，覆盖：

- palace 读写操作
- 知识图谱操作
- 跨 wing 导航
- drawer 管理
- agent diary 写入与读取

安装 MCP 服务后，大模型可以直接调用这些工具来访问记忆，而不需要在每次请求里把所有历史上下文都塞进 prompt。这是 memory 层设计上真正有价值的地方：**让 AI 自己决定什么时候查记忆、查哪些维度**，而不是由开发者手动把所有东西都拼进 system prompt。

## Benchmark 解读：测了什么，不能推出什么

MemPalace 在 LongMemEval（500 questions）上报告了两个关键数字：

| 配置 | R@5 | LLM 是否必需 |
|------|-----|-------------|
| Raw（纯语义搜索，无启发式，无 LLM） | 96.6% | 否 |
| Hybrid v4，held-out 450q | 98.4% | 否 |

两个数字都值得关注，但边界不同：

**96.6%** 是最诚实的可复现基线。它代表一套不加任何 trick 的语义搜索系统，在固定评测集上能达到的最高召回。测的是"纯向量相似度在长对话记忆上的召回能力上限"。

**98.4%** 是 Hybrid v4 在 held-out 450 questions 上的结果——模型先用 50 条 dev 样本调参，然后在完全 unseen 的 450 条上测。这个数字更接近"泛化后的真实性能"，但仍然是 recall 指标，不代表 QA 准确率。

MemPalace 明确拒绝和 Mem0、Mastra、Hindsight、Supermemory、Zep 做横向对比，理由是这些项目测的是不同的指标（end-to-end QA accuracy vs. retrieval recall），放在同一张表里不是诚实比较。这是少见的做法，在开源社区里值得单独点名。

## 安装与核心命令

```bash
# 推荐用 uv 安装
uv tool install mempalace

# 初始化一个项目
mempalace init ~/projects/myapp

# 挖掘项目文件或 Claude Code 会话
mempalace mine ~/projects/myapp
mempalace mine ~/.claude/projects/ --mode convos --wing myproject

# 语义搜索
mempalace search "why did we switch to GraphQL"

# 为新会话加载上下文
mempalace wake-up
```

## Auto-save Hooks：Claude Code 的上下文保全

MemPalace 提供两个 Claude Code hooks，在上下文压缩前自动保存会话。这是它针对 Claude Code 场景的特殊设计——30 天不登录 Claude Code 会话就会过期，hooks 保证了在压缩前把记忆写入 MemPalace，用户下次登录时可以通过 `mempalace wake-up` 恢复完整上下文。

如果需要比文件级 chunks 更细粒度的记忆，可以用 `mempalace sweep <transcript-dir>` 对整个 transcript 目录做扫描，系统会以每条 user/assistant message 为单位各建一个 drawer，实现逐轮召回。

## 适用边界

MemPalace 最适合以下场景：

- 个人或团队使用 **Claude Code / Gemini CLI** 做长期项目开发，需要跨会话记忆
- 对数据隐私有硬性要求，记忆必须留在本地，不能上云
- 需要比"把历史全塞进 prompt"更聪明的上下文管理机制
- 研究或评测 AI 记忆系统，需要可复现的 benchmark 基线

不太适合：

- 需要实时多人协作记忆的场景（当前架构偏向单用户本地存储）
- 需要 LLM 做自动摘要或信息抽取的记忆系统（MemPalace 不做这件事）
- 存储量级达到百万级会话的企业级应用（单用户 SQLite 图谱在后端扩展性上需要评估）

## 结论

MemPalace 真正值得看的不是 96.6% 这个数字本身，而是它背后的设计哲学：**记忆应该以原始形式保存，让检索层负责理解，而不是让存储层负责摘要**。这套设计把"记忆系统"的核心责任从"信息提取"转移到"索引结构"和"召回精度"上，换来了更高的召回上限和更清晰的可解释性。

对于已经在用 Claude Code 或 Gemini CLI 的个人开发者来说，MemPalace 是目前门槛最低、集成最顺的记忆层方案之一——本地存储，不需要 API key，安装一个 CLI 就能跑起来。