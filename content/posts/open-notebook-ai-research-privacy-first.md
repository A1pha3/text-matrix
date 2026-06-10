---
title: "Open Notebook：把 Notebook LM 式研究助手拆成本地可控系统"
date: "2026-06-05T23:12:00+08:00"
slug: "open-notebook-ai-research-privacy-first"
description: "Open Notebook 不是简单复刻 Notebook LM。它用 Esperanto 接多模型 provider，用 SurrealDB 同时承接图关系、全文搜索和向量检索，把播客生成做成可配置的 1-4 speaker 管线，重点在隐私、本地化和模型可替换性。"
draft: false
categories: ["技术笔记"]
tags: ["AI 研究工具", "Notebook LM", "多模态", "开源项目深拆", "SurrealDB", "播客生成", "LangChain", "Esperanto"]
toc: true
---

## 先说判断

Open Notebook 的看点不是“开源版 Notebook LM”，而是把研究助手拆成几个可控部件：资料放哪，模型由谁提供，播客按什么格式生成。

Notebook LM 买的是省心。Open Notebook 换来的是自托管、多 provider、REST API、Ollama 本地模型和可配置播客，适合在意数据位置和模型选择权的人。

## 架构抓主线就够了

Open Notebook 的部署拓扑不复杂：Next.js 前端跑 `8502`，FastAPI 跑 `5055`，SurrealDB 跑 `8000`。前端负责上传、搜索、聊天和播客配置；后端负责内容处理、检索和异步任务。

决定项目气质的是三层：

| 层 | 作用 |
| -- | -- |
| Esperanto | 创建 LLM、Embedding、STT、TTS 模型 |
| SurrealDB | 存 notebook、source、note，处理图关系、全文搜索和向量检索 |
| surreal-commands | 处理向量化、播客生成 |

这组合适合自托管助手：组件少，模型可换，数据不出本机。

## Provider 抽象：模型不是写死的

Open Notebook 没有维护一堆 provider 适配器，而是把模型创建交给 Esperanto。数据库里的 `model` 记录保存模型名、provider 和类型；`ModelManager` 读出后，按类型调用 `create_language()`、`create_embedding()`、`create_speech_to_text()` 或 `create_text_to_speech()`。

模型组合很自由：OpenAI 做 chat，Voyage 做 embedding，ElevenLabs 做 TTS；也可以把 LLM 和 embedding 切到 Ollama，再配本地语音服务。README 的 18+ provider，不只是列表，而是通过 Esperanto 工厂落到运行时。

凭证分新旧两条路径。新方式是在 Settings → API Keys 里保存 `Credential`；旧方式继续读环境变量。模型关联数据库凭证时优先用数据库配置，没有时回退环境变量。老部署能继续跑，新部署也不用手改 `.env`。

代价是依赖链变长。v1.9.0 升级 Esperanto 后，Ollama 默认 `num_ctx` 从 128000 降到 8192，Google embedding 默认模型从 `text-embedding-004` 换成 `gemini-embedding-001`。embedding 维度变更后，内容必须重新向量化。

## 播客：从固定模板变成可配置角色

Notebook LM 的播客是固定双人 deep-dive。Open Notebook 的 `SpeakerProfile` 支持 1-4 个 speaker，每个角色有名字、音色、背景和性格，可单独覆盖 TTS 模型。

PDF 变播客，大致是这条链路：

1. 上传 PDF，创建 `Source`。
2. `content-core` 提取文本。
3. 后台提交 `embed_source`，生成检索用 embedding。
4. 发起播客生成，提交 `generate_podcast`。
5. `EpisodeProfile` 决定大纲模型、脚本模型、段落和语言。
6. `SpeakerProfile` 决定角色、音色和 TTS。
7. `podcast-creator` 生成 outline、transcript、音频并混成 MP3。

关键在于大纲、脚本、语音可以分开选模型。结构化输出更稳的模型负责大纲，擅长对话的模型负责脚本，TTS 再按角色切 provider。这样才能做出单人讲解、访谈、辩论或圆桌，而不是同一种双人主持口吻。

## SurrealDB：少一个组件，多一点风险

Open Notebook 的数据关系不是简单的文档表。一个 notebook 可以引用多个 source，一个 source 也能被多个 notebook 复用；note、chat session、source insight、embedding chunk 又会继续挂在这些对象上。

SurrealDB 被选中，是因为它同时覆盖了四件事：

| 能力 | 在项目里的用途 |
| -- | -- |
| 文档存储 | `notebook`、`source`、`note`、`episode` |
| 图关系 | `reference`、`artifact`、`refers_to` |
| 全文搜索 | source、note、chunk、insight |
| 向量检索 | source / note / insight embedding |

PostgreSQL + pgvector 也能做，但会多出关系表、JOIN、全文搜索配置和图关系成本。Qdrant 或 Weaviate 向量检索更强，但要多部署一个服务，还要处理 source 与 embedding 的一致性。Open Notebook 面向自托管用户，少一个组件本身就是优势。

风险也别忽略。SurrealDB 的生态和运维工具远不如 PostgreSQL 成熟，社区资料少，Python 驱动还有 `RecordID` 转换细节。如果团队已有 PostgreSQL 运维体系，且不需要图关系查询，PostgreSQL + pgvector 更稳。

## 和 Notebook LM 怎么选

最短的对比是这样：

| 维度 | Notebook LM | Open Notebook |
| -- | -- | -- |
| 数据位置 | Google 云 | 自己的服务器 |
| 模型选择 | Google 模型 | 18+ provider，包含 Ollama |
| 播客格式 | 固定双人对话 | 1-4 speaker，可配置角色 |
| 使用门槛 | 打开即用 | 需要部署和维护 |
| 引用体验 | 更成熟 | 目前仍偏基础 |

所以它不是“谁全面替代谁”。Notebook LM 适合想省事的人；Open Notebook 适合愿意维护系统、换取控制权的人。

## 部署时别漏掉安全配置

Docker Compose 可以直接启动：

```bash
git clone https://github.com/lfnovo/open-notebook
cd open-notebook
docker compose up -d
# UI: http://localhost:8502
```

部署前改三处：

- 替换 `OPEN_NOTEBOOK_ENCRYPTION_KEY`，用于加密 provider 凭证。
- 设置 `OPEN_NOTEBOOK_PASSWORD`，公网或团队环境必加。
- 收紧 `CORS_ORIGINS`，再放到反向代理后面。

完全本地化不能只装 Ollama。LLM、embedding、STT、TTS 都要有本地模型或服务，否则仍会调用外部 provider。

## 适用边界

Open Notebook 适合三类人：资料多、不想上 Google 云的研究者；想生成讲解、访谈、辩论或圆桌播客的创作者；需要把资料留在内网，并接 REST API 自动化的团队。

它不适合只想零配置使用、没有容器运维经验、特别依赖精确 citation 跳转的人。这时 Notebook LM 更省事。

采用顺序可以保守些：先用 Docker + OpenAI 跑通流程；确认有用，再切 Ollama 和本地 embedding；最后做生产化部署，补认证、反代、备份和监控。

Open Notebook 的工程判断可以压成一句话：模型会变，provider 会变，但数据位置和替换权最好别交出去。代价是更长的依赖链和更多自托管责任。

项目地址：<https://github.com/lfnovo/open-notebook>  
官方站点：<https://www.open-notebook.ai>  
文档：<https://github.com/lfnovo/open-notebook/blob/main/docs/0-START-HERE/index.md>
