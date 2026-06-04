---
title: "Open Notebook 实战指南：开源版 NotebookLM，18+ 模型 + 1-4 说话人播客的本地知识工作台"
date: "2026-06-04T23:00:00+08:00"
slug: "open-notebook-lfnovo-notebook-lm-alternative-guide"
aliases:
  - /posts/tech/open-notebook-lfnovo-notebook-lm-alternative-guide/
description: "Open Notebook 是 lfnovo 出品的 24K+ stars 开源 NotebookLM 替代，18+ 模型提供方（OpenAI/Anthropic/Ollama）+ 1-4 说话人播客 + 全 REST API + Docker 一键部署，研究数据完全私有。"
draft: false
categories: ["技术笔记"]
tags: ["Open Notebook", "NotebookLM", "RAG", "开源", "播客生成", "本地优先"]
---

# Open Notebook 实战指南：开源版 NotebookLM，18+ 模型 + 1-4 说话人播客的本地知识工作台

## 核心判断

`Open Notebook`（仓库 [lfnovo/open-notebook](https://github.com/lfnovo/open-notebook)）在 24K+ stars、227 今日 star 的热度下，回答了一个被 Google NotebookLM 锁死的问题：**「能不能把我的研究材料、PDF、视频、网页都喂给 AI，让它像 NotebookLM 一样做总结、出播客，但又完全跑在我自己的机器上、用我自己选的模型？」**

Open Notebook 的真正价值不是「又一个 RAG 工具」——它是把 **NotebookLM 的核心范式**（多模态源 + AI 摘要 + 播客 + 引用）**开源 + 解耦**的整套方案。同一个 Docker Compose 可以跑通：18+ 模型提供方、SurrealDB 持久化、多说话人播客、REST API、6 国语言 UI。

它的护城河在三件别家没拼齐的事：

1. **模型完全可选**：OpenAI / Anthropic / Ollama / LM Studio / OpenRouter / Groq 等 18+ 提供方，按 token 成本和隐私策略自由切换
2. **播客是 1-4 说话人 + 自定义 profile**，比 NotebookLM 的「固定 2 人 deep dive」灵活得多
3. **完整 REST API** + Docker 部署 + SurrealDB 本地持久化，集成到自家产品或团队工作流比 NotebookLM 顺手

## 系统地图

| 层 | 组件 | 作用 |
| --- | --- | --- |
| **数据层** | SurrealDB（rocksdb 后端） | 笔记本 / 来源 / 摘要 / 嵌入 / 对话历史全部本地持久化 |
| **应用层** | FastAPI 后端 + Streamlit 前端 | 后端 8502，前端 5055 |
| **模型层** | 18+ 提供方（OpenAI / Anthropic / Ollama / LM Studio / ...） | 摘要、问答、播客脚本、嵌入 |
| **源类型** | PDF / 视频 / 音频 / 网页 / EPUB / Office | 多模态内容摄取 |
| **AI 能力** | 摘要、洞察、播客脚本、向量检索、全文检索、AI 对话 | NotebookLM 核心动作全覆盖 |

## vs NotebookLM 能力对照

| 维度 | Open Notebook | Google Notebook LM | 谁赢 |
| --- | --- | --- | --- |
| 隐私 | 自部署，数据自己掌控 | 仅 Google Cloud | **Open Notebook** |
| 模型选择 | 18+ 提供方 | 仅 Google 模型 | **Open Notebook** |
| 播客说话人 | **1-4 个** + 自定义 profile | 固定 2 人 | **Open Notebook** |
| 内容转换 | 自定义 + 内置 | 有限 | **Open Notebook** |
| API | **完整 REST API** | 无 | **Open Notebook** |
| 部署 | Docker / 云 / 本地 | 仅 Google 托管 | **Open Notebook** |
| 引用 | 基础（持续改进） | 全面 + 来源 | NotebookLM |
| 成本 | 只付 AI 调用 | 免费 + 付费档 | **Open Notebook** |
| 定制 | 开源、随改 | 闭源 | **Open Notebook** |

## 快速开始

### 0. 准备

仅需 [Docker Desktop](https://www.docker.com/products/docker-desktop/)。模型 API key 之后在 Web UI 里配就行。

### 1. 拉起 docker-compose

```bash
curl -o docker-compose.yml https://raw.githubusercontent.com/lfnovo/open-notebook/main/docker-compose.yml
docker compose up -d
```

默认 `docker-compose.yml` 已包含 `surrealdb` + `open_notebook` 两个 service，浏览器开 `http://localhost:8502`（UI）/ `http://localhost:5055`（API）即可。

### 2. 第一次进 UI

1. 选模型提供方（Ollama = 完全本地；OpenAI/Anthropic = 强但付费）
2. 把 `OPEN_NOTEBOOK_ENCRYPTION_KEY` 改成自己生成的 32+ 字符
3. 上传 PDF / 视频 / 音频 / 网页 → 等嵌入完成
4. 点 Generate Podcast 选 1-4 说话人 → 出 mp3

### 3. 用 API 集成

```bash
# 创建笔记本
curl -X POST http://localhost:5055/api/notebooks \
  -H "Content-Type: application/json" \
  -d '{"name": "Q2-2026-RAG-Research"}'

# 喂来源
curl -X POST http://localhost:5055/api/sources \
  -H "Content-Type: application/json" \
  -d '{"notebook_id": "...", "type": "url", "url": "https://arxiv.org/abs/2406.00001"}'

# 让 AI 写 5 段播客脚本
curl -X POST http://localhost:5055/api/podcasts \
  -H "Content-Type: application/json" \
  -d '{"notebook_id": "...", "speakers": 2, "duration_min": 8}'
```

## 它在解决谁的什么问题

- **研究员 / 学生**：要把 50 篇 arXiv PDF + 自己的笔记丢给 AI 做综述；NotebookLM 仅支持 50 个 source，Open Notebook 没有硬上限
- **播客主理人**：想批量把研究材料转成多说话人访谈音频；自定义 speaker profile 让播客风格稳定
- **企业内部**：要把 RAG 系统部署在自家 VPC 满足合规；自托管 SurrealDB + REST API 是干净的接入点
- **AI 工具开发者**：要在自家产品里集成「上传资料 → AI 对话 → 播客」三件套，Open Notebook 直接当后端

## 关键事实

| 维度 | 数据 |
| --- | --- |
| Stars | 24,576（trending 截屏时） |
| 今日新增 | 227 |
| 主要语言 | TypeScript（前端）+ Python（后端） |
| 协议 | MIT |
| 数据库 | SurrealDB（rocksdb 本地） |
| 部署 | Docker Compose（推荐）/ 手动 |
| 模型提供方 | **18+**（OpenAI / Anthropic / Ollama / LM Studio / OpenRouter / Groq / ...） |
| 播客说话人 | 1-4 个 + 自定义 profile |
| UI 语言 | 英文 / 葡萄牙文 / 简体中文 / 繁体中文 / 日文 / 俄文 / 孟加拉文 |
| API | 完整 REST |

## 它和竞品的边界

- **vs Google NotebookLM**：闭云、单提供方、播客固定 2 人、无 API；Open Notebook 是开源 + 多模型 + 多说话人 + API 全开放
- **vs AnythingLLM / PrivateGPT**：偏「企业 RAG 平台」，模型固定 1-2 个，无播客能力；Open Notebook 主战场是「个人 / 团队的 NotebookLM 体验」
- **vs Khoj / Reor**：桌面级个人 RAG，无多用户、无播客；Open Notebook 是 Web 多用户 + 播客 + 完整 API
- **vs PaperQA / OpenScholar**：偏学术论文理解，结构化提问；Open Notebook 偏向 NotebookLM 那种「自由喂资料 + 对话」的工作流

## 适合与不适合

**适合**

- 想跑 NotebookLM 但拒绝把研究材料交给 Google 的研究者 / 律师 / 投行
- 想在 Ollama / LM Studio 上跑本地 LLM + Open Notebook 做完全离线 RAG
- 团队 / 团队内部知识库需要「上传 PDF / 视频 → 共享对话 + 播客」流程
- 集成 Open Notebook 的 REST API 到自家 AI 产品做内容生产

**不适合**

- 想要 NotebookLM 那种「引用直接跳转到原 PDF 高亮」的体验：Open Notebook 引用还是基础级别
- 只想要「PDF → Markdown」单条管线：直接用 Marker / Docling 性价比更高
- 极简 CLI 用户：Open Notebook 的核心价值在 Web UI + API，纯 CLI 用例不如直接调 LangChain

## 已知边界

- **首次跑需要模型 key**：Ollama 路径也要先 `ollama pull` 几个模型
- **播客质量高度依赖底模**：用小模型（<7B）生成的播客脚本会出现重复话术；推荐 70B+ 或 GPT-4o / Claude Sonnet
- **SurrealDB 单机版限制**：数据量 >10GB 后建议迁到分布式 SurrealDB
- **UI 默认英文**：其他语言需要在 settings 里手动切换
- **无原生多人协作权限**：多用户共享一个 SurrealDB，靠数据 owner 字段区分；要做企业级 RBAC 需要在前端再包一层

## 与文本矩阵的关联

文本矩阵的「AI Agent 实战」类目下，多篇文章讨论过 RAG 工程的「输入 + 嵌入 + 检索 + 生成」四件套；Open Notebook 提供的是这四件套的**完整可部署版本**——比起自己拼 LangChain + Chroma + Streamlit，Open Notebook 把它们压进了一个 Docker Compose，对个人和小团队来说省 2-3 周工程量。

## 资源

- 仓库：<https://github.com/lfnovo/open-notebook>
- 官网：<https://www.open-notebook.ai/>
- 文档：<https://github.com/lfnovo/open-notebook/blob/main/docs/README.md>
- Docker Compose：<https://raw.githubusercontent.com/lfnovo/open-notebook/main/docker-compose.yml>
- Trendshift：<https://trendshift.io/repositories/14536>
