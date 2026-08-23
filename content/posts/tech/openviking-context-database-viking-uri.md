---
title: "OpenViking：把 Agent 上下文做成一个可 ls 的数据库"
date: 2026-08-24T03:40:00+08:00
slug: "openviking-context-database-viking-uri"
github_repo: "volcengine/OpenViking"
source_key: "gh:volcengine/OpenViking"
description: "火山引擎开源的 OpenViking 把记忆、知识库和技能统一挂载为 viking:// 虚拟文件系统，用 L0/L1/L2 三层分级加载替代黑盒向量检索。本文拆解其核心设计、基准数据与上手路径。"
draft: false
categories: ["技术笔记"]
tags: ["OpenViking", "AI Agent", "上下文工程", "RAG", "向量检索"]
---
# OpenViking：把 Agent 上下文做成一个可 ls 的数据库

## 核心判断

`volcengine/OpenViking` 是火山引擎开源的**上下文数据库（Context Database）**。它要解决的不是"再造一个向量库"，而是一个更具体的问题：AI Agent 的记忆、知识库和技能散落在各种黑盒存储里，Agent 自己不知道"它知道什么"，开发者也没法调试检索过程。

OpenViking 的答案是把这一切挂载成一个 `viking://` 虚拟文件系统——Agent 用 `ls`、`tree`、`find` 浏览自己的上下文，用分层加载控制 token 开销，每次检索留下可回看的轨迹。截至本文写作，该项目在 GitHub 上已有约 3.2 万 star，采用 AGPLv3 协议，Python 实现。

## 问题：黑盒向量库的三个痛点

用传统 RAG 栈（向量库 + 检索 TopK）给 Agent 配记忆，常见三个问题：

1. **不可见**。检索发生在 embedding 空间里，Agent 拿到几段碎片，但不知道这些碎片从哪来、周围还有什么。结果对不对，全凭运气。
2. **token 失控**。要么塞摘要省 token 丢细节，要么整篇加载烧 token。没有"按需加深"的中间态。
3. **记忆被动**。会话结束，对话数据就沉没了——用户偏好、Agent 踩过的坑，都需要显式工程才能沉淀。

OpenViking 对这三点分别给出了机制化的回应。

## 设计一：viking:// 虚拟文件系统

所有上下文——资源（项目文档、仓库、网页）、用户记忆、技能——统一编址在 `viking://` URI 之下：

```text
viking://
├── resources/              # 资源：项目文档、代码库、网页
│   └── my_project/
│       ├── docs/
│       └── src/
└── user/
    └── {user_id}/
        ├── memories/       # 长期记忆（偏好、习惯）
        ├── resources/
        ├── skills/         # 技能
        └── peers/
```

这个设计的直接收益是**确定性**：定位和操作上下文像开发者操作文件一样，路径就是身份。Agent 可以先 `tree` 一层看全貌，再钻进具体目录，而不是把全部赌注押在一次向量召回上。

## 设计二：L0/L1/L2 三层分级加载

每条内容写入时被处理成三个层级：

- **L0（摘要）**：约 100 token 的一句话摘要，用于快速判断相关性；
- **L1（概览）**：约 2k token 的结构与要点，用于规划；
- **L2（详情）**：完整原文，只在真正需要时加载。

关键在于**目录也带 L0/L1 层**：每个目录有自己的 `.abstract` 和 `.overview`，Agent 可以先读目录摘要判断"这片区值不值得深入"，再决定是否下钻到具体文件的 L2。这是对 token 开销的结构性控制，而不是靠截断碰运气。

## 设计三：可观测的目录递归检索

检索流程是"向量先定位最高分目录，再逐层下钻"：向量搜索负责给出候选入口，之后的过程是文件系统式的逐层浏览。每条查询保留完整的浏览轨迹——结果不对时，你能看到是哪条路径产生的，这在调试 RAG 时是实打实的效率提升。

## 设计四：会话沉淀为记忆

会话 commit 之后，OpenViking 异步从中提取用户偏好和 Agent 经验写入长期记忆。记忆的积累从"显式工程"变成"机制默认"。

## 效果：官方基准说什么

项目在 0.3.22 版本给出了两组基准（复现脚本在仓库 `benchmark/` 目录）：

**长对话用户记忆（LoCoMo）**：三个 Agent 集成（OpenClaw、Hermes、Claude Code）原生记忆准确率分别为 24.20%、33.38%、57.21%，接入 OpenViking 后全部提升到 80–83%；同时输入 token 下降 34.3–91.0%，查询延迟下降 58–66%。

**多轮 Agent 任务（tau2-bench）**：经验记忆让同一 LLM 的任务成功率在 Retail 场景 +6.87 个百分点、Airline 场景 +11.87 个百分点。

需要注意：这组数据来自项目方自测，VLM 用的是豆包 2.0 Pro，embedding 用的豆包系模型。量级趋势可信，具体数字建议结合自己的场景复测。

## 上手路径

Python 3.10+，三步起服务：

```bash
pip install openviking --upgrade
openviking-server init      # 交互式向导：选 provider、写 ~/.openviking/ov.conf
openviking-server doctor    # 校验配置与连通性
openviking-server           # 启动
```

`init` 支持 Volcengine、OpenAI、Kimi、GLM、Codex OAuth 以及本地 Ollama（可自动检测并拉取模型）。客户端 CLI `ov` 随包附带：

```bash
ov add-resource https://github.com/volcengine/OpenViking
ov tree viking://resources/volcengine -L 2
ov find "what is openviking"
ov grep "openviking" --uri viking://resources/volcengine/OpenViking/docs/en
```

Agent 侧已有官方集成：Claude Code、Codex、OpenClaw、Hermes、Cursor、TRAE、OpenCode 等，注入召回、自动提交会话记忆。不想装任何东西，可以直接开浏览器玩 [OpenViking Studio](https://openviking.ai/studio) 在线演示。

## 适用与不适用

**适合**：长期运行的 Agent 需要跨会话记忆；知识库规模大到"一次检索塞不下上下文"；需要调试检索过程的团队。

**需要斟酌**：AGPLv3 协议对闭源商用有传染性约束；依赖 LLM 做 L0/L1 摘要，写入侧有额外模型调用成本；小规模场景（几十个文档的一次性问答）用不上这套机制，普通 RAG 反而更简单。

## 结论

OpenViking 的真正贡献不是某个算法，而是把"上下文工程"从流水线拼接提升到数据库范式：统一编址、分层加载、可观测检索、会话沉淀。对正在给 Agent 做记忆系统的团队，它的 viking:// 文件系统隐喻和 L0/L1/L2 分层设计都值得借鉴——即便不直接采用，这套思路也能回答"记忆系统到底该长什么样"这个问题。
