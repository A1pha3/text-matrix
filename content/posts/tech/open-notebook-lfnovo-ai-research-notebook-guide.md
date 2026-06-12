---
title: "Open Notebook：可自托管的 NotebookLM 替代品，2 分钟本地跑起来"
date: "2026-06-12T15:17:01+08:00"
slug: "open-notebook-lfnovo-ai-research-notebook-guide"
description: "lfnovo/open-notebook 是 Google NotebookLM 的开源替代品，支持 18+ AI 提供商、本地自托管、多模态素材、多说话人播客与完整 REST API。"
draft: false
categories: ["技术笔记"]
tags: ["Open Notebook", "NotebookLM", "RAG", "SurrealDB", "AI工具"]
---

# Open Notebook：可自托管的 NotebookLM 替代品，2 分钟本地跑起来

> **目标读者**：把 PDF / 网页 / 视频 / 音频丢进一个笔记本就让 AI 整理、提问、生成播客的研究者和团队；尤其在意数据不出本机、不想被单一模型绑定的人。
>
> **核心问题**：Google 的 NotebookLM 体验惊艳，但资料只能放在 Google 云、只能用 Google 模型、没有 API、播客被锁死在 2 说话人——如果想自己托管、能换模型、能编程调用，2026 年有什么能直接 `docker compose up` 的选择？
>
> **事实边界**：本文基于 `lfnovo/open-notebook` 仓库 README、Provider Support Matrix 与 Quick Start 整理；未在仓库中明确列出的内部实现细节、未验证的性能数字、未出现的功能不写成事实。

## 阅读导航

- 想 2 分钟把它跑起来：直接看 `§3 快速开始`
- 想搞清楚它和 NotebookLM 差在哪：看 `§4 vs NotebookLM 对照表`
- 想知道哪些 AI 提供商能直接用：看 `§5 Provider 支持矩阵`
- 想理解 6 个核心能力是什么：看 `§6 核心能力拆解`
- 想知道它适合谁、不适合谁：看 `§8 谁该用它，谁该跳过`

## §1 核心判断

`lfnovo/open-notebook` 是一个**完全自托管、模型无关、API 完整**的研究型 Notebook 工具，它做的事和 Google NotebookLM 几乎一样：把多模态资料收进一个 Notebook，让 AI 摘要、问答、生成播客——但它把"在哪里跑、用什么模型、怎么集成"这三件事全部交回给你。

如果你满足下面任一条件，Open Notebook 是当前最直接的开源选项：

- 研究资料不能上云（合规、内部文档、客户合同）
- 想在 OpenAI / Anthropic / Ollama / DeepSeek / Gemini 之间随时换模型
- 需要 REST API 把 Notebook 接入自己的工作流（Agent、知识库、播客流水线）
- 希望播客不只是 2 个 AI 主持人，想要 1-4 个说话人并能调人设
- 愿意为"可控"多付一点部署和调参的精力

仓库当前已经 29.4k stars、739 commits，Next.js 前端、FastAPI 后端、SurrealDB 存储，是 2026 年这份赛道里事实上的主流选择。

## §2 项目基本信息

| 项目 | 信息 |
|------|------|
| **仓库** | [lfnovo/open-notebook](https://github.com/lfnovo/open-notebook) |
| **作者** | [lfnovo](https://github.com/lfnovo) |
| **Stars** | 29.4k |
| **Commits** | 739（截至 README 抓取） |
| **License** | MIT |
| **主语言** | Python（后端） + TypeScript / Next.js（前端） |
| **存储** | SurrealDB v2（本地 RocksDB） |
| **官方镜像** | `lfnovo/open_notebook:v1-latest` |
| **官网** | <https://www.open-notebook.ai> |

技术栈亮点：后端用 Python + FastAPI + LangChain，前端是 Next.js 14 + React，数据库选 SurrealDB（多模型数据库，原生支持文档+图+向量检索，恰好契合 Notebook 的"素材 + 笔记 + 关系"模型）。`docs/` 目录下还有独立的安装、用户指南、Core Concepts、AI Provider、API Reference、Troubleshooting、Development 文档体系，是少有的"文档比代码更新还勤"的中型开源项目。

## §3 快速开始

> 官方声称 2 分钟跑起来，对应 `curl` 一份 `docker-compose.yml`、改一个加密密钥、`docker compose up -d` 三步。下面以官方 `docker-compose.yml` 为准。

### 3.1 前置条件

- 安装了 [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- 端口 `8000`（SurrealDB）、`8502`（Streamlit 风格的旧版 Web UI）、`5055`（REST API + 新版 Next.js UI）不被占用
- 准备好至少一个 AI Provider 的 API Key（OpenAI / Anthropic / Google / Groq / Ollama 等）

### 3.2 拉起 `docker-compose.yml`

```bash
curl -o docker-compose.yml https://raw.githubusercontent.com/lfnovo/open-notebook/main/docker-compose.yml
```

`docker-compose.yml` 默认包含两个服务：

```yaml
services:
  surrealdb:
    image: surrealdb/surrealdb:v2
    command: start --log info --user root --pass root rocksdb:/mydata/mydatabase.db
    user: root
    ports:
      - "8000:8000"
    volumes:
      - ./surreal_data:/mydata
    restart: always

  open_notebook:
    image: lfnovo/open_notebook:v1-latest
    ports:
      - "8502:8502"
      - "5055:5055"
    environment:
      - OPEN_NOTEBOOK_ENCRYPTION_KEY=change-me-to-a-secret-string
      - SURREAL_URL=ws://surrealdb:8000/rpc
      - SURREAL_USER=root
      - SURREAL_PASSWORD=root
      - SURREAL_NAMESPACE=open_notebook
      - SURREAL_DATABASE=open_notebook
    volumes:
      - ./notebook_data:/app/data
    depends_on:
      - surrealdb
    restart: always
```

### 3.3 改加密密钥

`OPEN_NOTEBOOK_ENCRYPTION_KEY` 是用于加密 API Key、Provider 配置等敏感字段的密钥。**必须改成自己的强随机字符串**，否则你重启容器后会读不回旧 Key。建议一次性写好并备份：

```bash
# 改 docker-compose.yml 里这一行
- OPEN_NOTEBOOK_ENCRYPTION_KEY=change-me-to-a-secret-string
# 替换成例如
- OPEN_NOTEBOOK_ENCRYPTION_KEY=my-super-secret-key-123
```

### 3.4 启动

```bash
docker compose up -d
```

等 15-20 秒后访问：

- Web UI（新版 Next.js）：<http://localhost:5055>
- Web UI（Streamlit 风格）：<http://localhost:8502>
- REST API 文档：<http://localhost:5055/docs>

### 3.5 配置第一个 AI Provider

UI 里 `Settings → API Keys → Add Credential`，选一个 Provider（OpenAI / Anthropic / Google / Groq / Ollama / DeepSeek / Mistral / OpenRouter 等）粘进 Key，`Save` → `Test Connection` → `Discover Models` → `Register Models`。完成这一步之后，才可以开始新建 Notebook 并上传素材。

### 3.6 用 Ollama 跑完全本地（可选）

不想付 API 费用，可以参考 `examples/docker-compose-ollama.yml`，在 `services` 里加一个 `ollama` 服务，让 `open_notebook` 通过本地 `http://ollama:11434` 调用。这样所有数据、所有模型推理都在你自己的机器上完成。

## §4 vs NotebookLM 对照表

下面这张表直接来自 README，**所有"Open Notebook 优势"列都是仓库自身的宣称**，不是中立基准，引用时建议交叉验证。

| 能力 | Open Notebook | Google Notebook LM | Open Notebook 自宣优势 |
|------|---------------|-------------------|---------------------|
| 隐私与控制 | 自托管，数据本地 | 仅 Google 云 | 数据完全自主 |
| AI Provider 选择 | 18+ 提供商 | 仅 Google 模型 | 灵活、按成本优化 |
| Podcast 说话人 | 1-4 个，自定义人设 | 仅 2 个 | 极大灵活性 |
| Content Transformations | 自定义 + 内置 | 选项有限 | 处理能力无上限 |
| API | 完整 REST API | 无 API | 可全自动化 |
| 部署 | Docker / 云 / 本地 | 仅 Google 托管 | 任意地方部署 |
| Citations | 基础引用（官方承认会改进） | 完整来源 | 研究可信度（Google 占优） |
| 定制 | 开源，可深度改造 | 闭源 | 可扩展性无上限 |
| 成本 | 只付 AI 用量 | 免费层 + 月费 | 透明可控 |

> **怎么读这张表**：Open Notebook 的强项在"控制、灵活、API"；NotebookLM 的强项在"开箱即用、引用质量、Google 模型集成"。这两者并不直接竞争——NotebookLM 更像"开箱即用的产品"，Open Notebook 更像"你可以拿来自托管的底座"。

## §5 Provider 支持矩阵

> 这张表是 Open Notebook 的"多模型"主张的硬证据。同一份 Provider 在不同能力上的支持情况不同——选择 Provider 时先看你要用它做哪件事。

| Provider | LLM | Embedding | STT | TTS |
|----------|:---:|:--------:|:---:|:---:|
| OpenAI | ✅ | ✅ | ✅ | ✅ |
| Anthropic | ✅ | ❌ | ❌ | ❌ |
| Groq | ✅ | ❌ | ✅ | ❌ |
| Google (GenAI) | ✅ | ✅ | ✅ | ✅ |
| Vertex AI | ✅ | ✅ | ❌ | ✅ |
| Ollama | ✅ | ✅ | ❌ | ❌ |
| Perplexity | ✅ | ❌ | ❌ | ❌ |
| ElevenLabs | ❌ | ❌ | ✅ | ✅ |
| Deepgram | ❌ | ❌ | ❌ | ✅ |
| Azure OpenAI | ✅ | ✅ | ✅ | ✅ |
| Mistral | ✅ | ✅ | ✅ | ✅ |
| DeepSeek | ✅ | ❌ | ❌ | ❌ |
| Voyage | ❌ | ✅ | ❌ | ❌ |
| xAI | ✅ | ❌ | ❌ | ✅ |
| OpenRouter | ✅ | ✅ | ❌ | ❌ |
| DashScope（Qwen） | ✅ | ❌ | ❌ | ❌ |
| MiniMax | ✅ | ❌ | ❌ | ❌ |
| OpenAI 兼容* | ✅ | ✅ | ✅ | ✅ |

*含 LM Studio 和任意 OpenAI 兼容端点。所有这些 Provider 由作者开源的 `esperanto` 库统一接入，Open Notebook 自己只做调用层和上层工作流。

**几个值得留意的点**：

- 想要"一套 Provider 全包"：Google（GenAI）、Azure OpenAI、Mistral、OpenAI 兼容端点是唯一同时支持 LLM + Embedding + STT + TTS 的选项
- 想要"完全本地、零 API 费用"：Ollama（LLM + Embedding）+ Deepgram / ElevenLabs（TTS，可选）
- 想要"中文模型便宜"：DashScope（Qwen）已支持 LLM；Embedding 暂时需要 OpenAI / Google / Ollama
- Anthropic 只支持 LLM，不支持 Embedding/STT/TTS——做 RAG 时还要再配一个 Embedding Provider

## §6 核心能力拆解

Open Notebook 把 NotebookLM 的能力拆成了 6 个可独立使用的功能模块，每个模块背后都是一条独立的"素材 → 处理 → 存储"链路。

### 6.1 Sources（多模态素材库）

支持 PDF、视频、音频、网页、Office 文档等多种内容类型。添加 Source 后系统会自动：

1. 解析内容（PDF 抽文本、视频抽转写、网页抽正文）
2. Embedding + 分块进向量库
3. 生成摘要和关键洞察
4. 进入搜索和 Chat 的可引用范围

这是后面所有功能（Chat、Podcast、Search、Transformations）的内容池。

### 6.2 Notes（笔记）

两种用法并存：

- 手动笔记：自己写的 Markdown 笔记，可以挂到任意 Notebook
- AI 辅助笔记：对一份或一组 Source 用 Transformation 生成笔记

笔记在 Chat 和 Podcast 中可以像 Source 一样被引用，等价于"用户整理好的上下文"。

### 6.3 Chat（多会话问答）

`Chat` 不是单条对话，而是"在一个 Notebook 内开多个独立会话"。会话可以指定：

- 上下文范围（哪些 Source、哪些 Note）
- 引用的粒度（按段、按页、按整篇）
- LLM 模型（包括 Reasoning Model：DeepSeek-R1、Qwen3 等已验证可用）
- 是否返回引用（citations）

把 Notebook 理解成"主题包"、Chat 理解成"主题包内的多次独立研究"，这套模型比 NotebookLM 单一对话流更接近真实研究工作。

### 6.4 Search（全文 + 向量混合）

同时支持全文搜索和向量搜索，跨所有 Notebook 跨所有 Source。Open Notebook 没有做 RAG-as-a-service，Search 仍然把"命中段"喂给 LLM 重新生成答案——这一点和 NotebookLM 的"只基于来源"原则一致。

### 6.5 Transformations（自定义处理）

这是 Open Notebook 比 NotebookLM 多出来的一个能力。`Transformation` 是一段"对素材做什么"的定义，可以是：

- 内置模板：摘要、提纲、要点、问答对
- 自定义 Prompt：自由定义输入/输出

典型用途：把 5 篇 PDF 一次性转成结构化笔记、按客户模板生成提案草稿、把英文素材翻译并改写为中文播客脚本。

### 6.6 Podcast（多说话人播客生成）

这是 Open Notebook 最有差异化的能力，对照 NotebookLM 唯一的 2 说话人：

- 支持 1-4 个说话人
- 每个说话人有独立的 Episode Profile（角色、性格、语速、表达风格）
- 选 18+ Provider 中支持 TTS 的那些合成语音
- 生成结果存为音频文件，可下载可嵌入

官方提供了一段 4 说话人的 [Podcast Demo on YouTube](https://www.youtube.com/watch?v=D-760MlGwaI)，可以先听后决定要不要为这个能力迁移过来。

## §7 常见坑点

把仓库里反复出现、容易卡住人的点集中到这里。

### 7.1 加密密钥忘了改 / 换了机器

`OPEN_NOTEBOOK_ENCRYPTION_KEY` 是加密 Provider 凭证的密钥。**换一台机器或重装时如果用了不同密钥，旧的 API Key 全读不出来。** 一定要把密钥记在密码管理器里。

### 7.2 Anthropic 没有 Embedding

Anthropic 不提供 Embedding API。选 Anthropic 作为 LLM 之后，必须再选一个 Embedding Provider（OpenAI / Google / Voyage / Ollama）。来源已经在 Provider 矩阵里标出，部署时按表选。

### 7.3 Ollama 跑 LLM 还行，跑 Embedding 看模型

本地 Ollama 跑 LLM 没问题，但 Embedding 效果高度依赖选的具体模型。仓库推荐用 `nomic-embed-text` 或 `mxbai-embed-large`，默认 `all-minilm` 偏弱。

### 7.4 端口冲突

`8000`（SurrealDB）、`8502`（Streamlit 风格 UI）、`5055`（API + 新版 UI）三个端口都要空。如果已经部署了别的服务（比如 SurrealDB 自己的实例、MosaicML Model Server 等），改 `docker-compose.yml` 里的 ports 映射。

### 7.5 `Dockerfile.single`

仓库里除了 `docker-compose.yml` 还提供一个 `Dockerfile.single`，把 SurrealDB 和 Open Notebook 装到同一个容器里，部署更省事但失去隔离——生产环境一般不推荐，开发试用可以。

### 7.6 MCP 集成边界

`docs/5-CONFIGURATION/mcp-integration.md` 描述了怎么把 Open Notebook 作为 MCP Server 接入 Claude Desktop / VS Code。但 MCP 暴露的是有限动作集（主要是查 Source / 写 Note），**不要把它当成完整 RAG 后端来用**。

## §8 谁该用它，谁该跳过

### 8.1 适合先用 Open Notebook 试一把的场景

- 内部研究、合规要求文档不能出本机的团队
- 想把 NotebookLM 的工作流接到自己 Agent / 工作流里、但 NotebookLM 没有 API
- 想自己掌控"用哪个模型"和"模型能访问哪些上下文"
- 喜欢自定义 Transformation 的工作流（生成固定模板的客户提案、周报等）
- 需要 1-4 个说话人的播客来覆盖多视角讨论

### 8.2 不建议立刻迁移的场景

- 团队已经在用 NotebookLM 协作，且对"引用质量"非常敏感——Open Notebook 官方承认它的 Citations 还在改进
- 想要完全 SaaS、不愿意维护 Docker / 数据库 / 备份的——NotebookLM 是更省心的选择
- 只用 NotebookLM 最基础的"上传 PDF → 听播客"——Open Notebook 第一次配置需要 30 分钟左右
- 生产级多用户 / 多租户——Open Notebook 的权限模型还在 Roadmap 里（"Live Front-End Updates"、"Async Processing"、"Cross-Notebook Sources" 等是 Recently Completed 之外仍在 Upcoming 的项）

## §9 稳妥的采用顺序

1. **先在单机 `docker compose up` 跑起来**，确认 UI 能访问、Provider 联通、第一个 Notebook 跑通
2. **把 Ollama 接入**，做一份"完全本地"的备份方案，避免 API 厂商出问题时整个工作流瘫痪
3. **整理 1-2 个真实工作的 Source 集合**（比如本季度的研究主题、本周客户资料），走一遍"上传 → Chat 问答 → Podcast 生成"完整闭环，验证它真的能替代你现在的 NotebookLM 工作流
4. **再考虑接入 MCP / REST API**，把 Open Notebook 嵌入更大的 Agent / 工作流
5. **最后再做数据备份和恢复演练**——`./notebook_data` 和 `./surreal_data` 是核心，把它们加入你的常规备份流程

这个顺序把"先验证个人体验 → 再自动化 → 最后才考虑生产化"拆开，每一步都能独立 rollback。

## §10 风险与未覆盖项

写在最前面让你知道它的边界：

- **API 兼容性**：仓库还未承诺 OpenAI 兼容端点之外的兼容矩阵，自定义 LLM 接入前先在 UI 里 `Test Connection`
- **Citation 质量**：官方承认 Citations 是"基础引用（will improve）"，如果你的工作流对引用质量非常敏感，先做小规模测试
- **多用户/权限**：仓库 Upcoming Features 里有"Live Front-End Updates""Async Processing""Cross-Notebook Sources""Bookmark Integration"——这些都没说多用户模型怎么设计，团队用之前先在 UI 里看权限设置
- **MCP 边界**：MCP 暴露的动作是只读为主的笔记查询，不是完整 CRUD，做"在 Agent 里写笔记到 Open Notebook"前先看 API Reference
- **MCP 之外的自动化**：自动化走 REST API（`http://localhost:5055/docs`），但官方不保证所有 UI 操作都对应一个公开 API endpoint

## §11 一句话总结

Open Notebook 不是 NotebookLM 的"功能复制版"，而是"把 NotebookLM 的能力放回你自己机器上、换上你自己的模型、接上你自己的工作流"的底座。愿意为可控多花 30 分钟部署和调参的人，2026 年很难再找到比它更完整的选择。

---

> 本文基于 `lfnovo/open-notebook` 仓库 README 与 Provider Support Matrix 整理。
> 抓取时间：2026-06-12，版本对应 `lfnovo/open_notebook:v1-latest` 镜像与 `surrealdb/surrealdb:v2`。
> 详细安装、Provider 配置、API Reference、Troubleshooting 见仓库 `docs/` 目录。
