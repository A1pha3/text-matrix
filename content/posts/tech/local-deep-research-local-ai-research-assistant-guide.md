---
title: "local-deep-research: 本地优先的 AI 科研助手完整指南"
date: "2026-05-06T10:08:31+08:00"
slug: "local-deep-research-local-ai-research-assistant-guide"
description: "local-deep-research（LDR）是一个本地优先的 AI 科研助手，支持任意 LLM 和 10+ 搜索引擎，在 SimpleQA 基准上达到约 95% 准确率。本文详解其架构、部署方式、支持模型、搜索能力与隐私安全特性。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "本地部署", "科研工具", "Ollama", "RAG", "搜索增强", "隐私"]
---

# local-deep-research: 本地优先的 AI 科研助手完整指南

在 AI 搜索与科研助手这个赛道上，大多数工具都依赖云端 API——你的查询记录、研究内容、文档数据都会流经第三方服务器。这对关心数据隐私的研究人员和开发者来说，一直是个隐患。

**local-deep-research**（以下简称 LDR）试图解决这个问题。它是一个完全本地运行的 AI 科研助手，支持任意本地或云端大模型、对接 10+ 搜索数据源、用 SQLCipher AES-256 加密每个用户的数据，并在 SimpleQA 基准测试中取得了约 95% 的准确率。本文从项目概览、核心架构、安装配置、支持模型、搜索能力、隐私安全和适用场景出发，提供一份完整的使用指南。

> **信息来源**：本文所有事实均来自 [LearningCircuit/local-deep-research](https://github.com/LearningCircuit/local-deep-research) 仓库的 README、文档和源码。如有信息在仓库中未明确说明，会单独标注。

## 项目概览

LDR 定位为一个**本地优先的 AI 研究助手**，核心理念是：数据留在本地、模型由你选择、过程完全透明。

关键数据一览：

| 维度 | 内容 |
|------|------|
| **仓库** | [LearningCircuit/local-deep-research](https://github.com/LearningCircuit/local-deep-research) |
| **开源协议** | MIT License |
| **主要语言** | Python（Flask 后端） |
| **Stars** | 参见 GitHub 页面（badge 显示活跃） |
| **最新提交** | 持续活跃（badge 显示月均提交） |

项目在 GitHub 上维护了完整的 CI/CD 流程，包括 CodeQL、Semgrep、OpenSSF Scorecard 等安全扫描，并在 Docker 镜像中集成了 Cosign 签名、SLSA 溯源和 SBOM。

## 核心概念与工作原理

### 研究流程

LDR 的研究流程分为三个阶段：

1. **问题生成**：根据用户提问，自动生成若干子问题（sub-questions），从而将复杂查询分解为可并行的子任务。
2. **并行搜索**：通过选择的搜索引擎（可多引擎组合）并行抓取结果，提取关键信息。
3. **综合报告**：将所有搜索结果整合，生成带引用（citations）的结构化报告，支持 Markdown、PDF、LaTeX 等输出格式。

这个流程支持 20+ 种**研究策略（strategies）**，包括 `quick_summary`（30 秒到 3 分钟出结果）、`detailed_research`、`report_generation` 和 `analyze_documents` 等。README 还特别提到了一种新兴的 **LangGraph Agent Strategy**——在这种模式下，大模型自主决定使用哪个搜索引擎、搜索什么内容、什么时候停止并综合报告；早期测试显示它能自适应的在多个搜索引擎间切换，并收集比管道式策略更多的信息源。

### 知识库构建

LDR 不仅是搜索引擎，还是一个可积累的**本地知识库**：

```mermaid
flowchart LR
    R[Research] --> D[Download Sources]
    D --> L[(Library)]
    L --> I[Index & Embed]
    I --> S[Search Your Docs]
    S -.-> R
```

每次研究过程中发现的优质资源（arXiv 论文、PubMed 文章、网页）可以一键下载到本地加密库，LDR 自动提取文本、建立向量索引，让你的下一次研究可以同时覆盖私有文档和实时网络结果。长期使用下来，研究积累的知识会不断复合增长。

### 架构总览

根据仓库中 [architecture.md](https://github.com/LearningCircuit/local-deep-research/blob/main/docs/architecture.md) 的描述，系统分为以下层：

- **用户界面**：Web 浏览器访问 `localhost:5000`
- **Flask 后端**：REST API + WebSocket，支持认证与 CSRF 保护
- **研究引擎**：策略选择器 → 问题生成器 → 搜索执行器 → 报告综合器
- **LLM 层**：支持本地（Ollama、LM Studio、llama.cpp）和云端（OpenAI、Anthropic、Google、OpenRouter 100+ 模型）
- **搜索层**：本地搜索（SearXNG、Elasticsearch、文档库）和网络/学术搜索（Tavily、Brave、arXiv、PubMed、Semantic Scholar 等）
- **存储层**：SQLCipher 加密数据库 + 向量存储 + 文件存储
- **输出层**：Markdown、PDF、LaTeX、Quarto、RIS/BibTeX

部署模式可分为三类：**全本地**（Ollama + SearXNG，最大隐私）、**混合**（本地 LLM + 云端搜索 API，平衡性能）和**云端全力**（OpenAI/Claude + Tavily，最大速度）。

## 安装方式

### Docker Compose（推荐）

最简单的方式，一行命令启动完整栈：

**CPU 版本（所有平台）：**
```bash
curl -O https://raw.githubusercontent.com/LearningCircuit/local-deep-research/main/docker-compose.yml && docker compose up -d
```

**NVIDIA GPU 版本（Linux）：**
```bash
curl -O https://raw.githubusercontent.com/LearningCircuit/local-deep-research/main/docker-compose.yml && \
curl -O https://raw.githubusercontent.com/LearningCircuit/local-deep-research/main/docker-compose.gpu.override.yml && \
docker compose -f docker-compose.yml -f docker-compose.gpu.override.yml up -d
```

启动后访问 http://localhost:5000，约 30 秒后可用。

### pip 安装

面向开发者或需要与现有 Python 项目集成的用户：

```bash
pip install local-deep-research
```

SQLCipher 加密通过预编译 wheel 提供，无需本地编译。Windows 上的 PDF 导出需要 Pango（[安装指南](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html)）。如果遇到加密问题，可设置 `export LDR_BOOTSTRAP_ALLOW_UNENCRYPTED=true` 回退到标准 SQLite。

### Docker 手动启动

三个容器分别启动，适合需要单独管理组件的场景：

```bash
# SearXNG（搜索代理）
docker run -d -p 8080:8080 --name searxng searxng/searxng

# Ollama（本地模型服务）
docker run -d -p 11434:11434 --name ollama ollama/ollama
docker exec ollama ollama pull gpt-oss:20b

# LDR 应用
docker run -d -p 5000:5000 --network host \
  --name local-deep-research \
  --volume 'deep-research:/data' \
  -e LDR_DATA_DIR=/data \
  localdeepresearch/local-deep-research
```

### Unraid

仓库提供了预配置的 Unraid 模板，支持自动 SearXNG/Ollama 集成和 NVIDIA GPU 直通，具体步骤见 [Unraid 部署文档](https://github.com/LearningCircuit/local-deep-research/blob/main/docs/deployment/unraid.md)。

## 支持的大模型

### 本地模型

| 提供商 | 说明 |
|--------|------|
| **Ollama** | 默认连接 `http://localhost:11434`，支持 Llama 3、Mistral、Gemma、DeepSeek、Qwen 等常见模型 |
| **LM Studio** | 连接其 OpenAI 兼容服务器（默认 `http://localhost:1234/v1`） |
| **llama.cpp** | 通过 `llama-server` 的 OpenAI 兼容端点（默认 `http://localhost:8080/v1`）；启动示例：`llama-server -m <model.gguf>` |

README 明确说明：LLM 处理完全在本地进行，只有搜索查询会发送到外部网络，没有 API 调用成本。

> 💡 **模型选择参考**：仓库维护了一个 [Hugging Face Benchmark 数据集](https://huggingface.co/datasets/local-deep-research/ldr-benchmarks)，社区提交了各种 Ollama / LM Studio / llama.cpp 模型在不同配置下的准确率数据，在下载大模型文件之前可以先来这里比较。

### 云端模型

- **OpenAI**：GPT-4、GPT-3.5 系列
- **Anthropic**：Claude 3 系列
- **Google**：Gemini 系列
- **OpenRouter**：100+ 模型，通过 OpenAI 兼容端点访问

云端模型的配置推荐通过 Web UI（Settings → LLM Provider）完成，也可以通过环境变量注入（如 `LDR_LLM_OPENAI_API_KEY`）。注意：空字符串（如 `LDR_LLM_OPENAI_API_KEY=""`）会被视为未设置而非清空——如果需要明确禁用某个 key，需设为任意无效值（如 `DISABLED`）。

### 值得注意的版本变更

从 v1.7 开始，`llm.model` 不再自动填充默认值。之前未配置时会静默下载多 GB 的 `gemma3:12b`，现在默认值为空，research 会在没有配置模型时报明确的错误。另外 `llamacpp` provider 从进程内加载改为 HTTP 端点调用，如果之前设置了 `llm.llamacpp_model_path` 指向本地 `.gguf` 文件，需要改用 `llama-server -m <your-model.gguf>` 启动服务来替代。

## 搜索能力详解

### 搜索引擎列表

LDR 支持的搜索源可分为三类：

**免费学术/通用引擎：**
- 学术：arXiv、PubMed、Semantic Scholar
- 通用：Wikipedia、SearXNG
- 技术/文档：GitHub、Elasticsearch
- 历史存档：Wayback Machine
- 新闻：The Guardian、Wikinews

**付费/需 API Key 的引擎：**
- Tavily（AI 优化搜索）
- Google（通过 SerpAPI 或 Programmable Search Engine）
- Brave Search（隐私导向搜索）

**自定义源：**
- 本地文档（用自己的文件进行 AI 搜索）
- LangChain Retriever（任意向量存储或数据库）
- 元搜索（智能组合多个引擎）

### LangChain 集成

LDR 支持接入任意 LangChain 兼容的 Retriever（FAISS、Chroma、Pinecone、Weaviate、Elasticsearch 等），可以在企业知识库场景中使用。具体配置见 [LangChain Retriever Integration 文档](https://github.com/LearningCircuit/local-deep-research/blob/main/docs/LANGCHAIN_RETRIEVER_INTEGRATION.md)。

### 爬虫策略

README 特别指出，LDR 遵守 `robots.txt` 并在抓取网页时如实表明身份（User-Agent），不采用任何隐蔽或反检测技术。这意味着某些明确阻止自动化访问的页面可能无法被抓取，但项目认为这是正确的权衡。

### 搜索结果验证

README 中提供了早期 SimpleQA 基准测试数据（样本量有限，结果为初步数据）：

| 配置 | 准确率 | 备注 |
|------|--------|------|
| gpt-4.1-mini + SearXNG + focused_iteration | 90–95% | 有限样本 |
| gpt-4.1-mini + Tavily + focused_iteration | 90–95% | 有限样本 |
| gemini-2.0-flash-001 + SearXNG | 82% | 单次运行 |

README 也明确标注这些是**初步结果**，性能受查询类型、模型版本和配置影响较大。完整社区排行榜在 [LearningCircuit/ldr-benchmarks](https://github.com/LearningCircuit/ldr-benchmarks) 持续更新。

## 隐私与安全

### 数据加密

每个用户拥有独立的 SQLCipher 数据库，采用 AES-256 加密（Signal 级安全）。README 特别说明：**没有密码恢复机制**，这意味着真正的零知识——即使服务器管理员也无法读取你的数据。

关于内存中的凭据，项目解释：像所有在运行时需要解密的应用（包括密码管理器、浏览器、API 客户端）一样，凭据在活动会话期间以明文形式保存在进程内存中。这是行业普遍接受的事实，而非 LDR 特有的问题。项目通过会话作用域的凭据生命周期和核心转储排除来缓解这一风险。

### 供应链安全

Docker 镜像使用 Cosign 签名，包含 SLSA 溯源声明和 SBOM。验证命令：

```bash
cosign verify localdeepresearch/local-deep-research:latest
```

### 无遥测、无追踪

README 明确声明：LDR 包含**零遥测、零分析、零追踪**。不收集、不传输、不存储任何关于用户或使用情况的数据。唯一的网络调用来自用户主动操作——搜索查询（到你配置的引擎）、LLM API 调用（到你选择的提供商）和通知（仅在你配置了 Apprise 时）。使用指标存储在你的本地加密数据库中。

### 安全扫描

仓库维护了非常详细的安全扫描体系，包括 CodeQL、Semgrep、DevSkim、Bearer、Gitleaks、OSV-Scanner、npm-audit、Retire.js、Container Security、Dockle、Hadolint、Checkov、Zizmor、OWASP ZAP 等。扫描抑制项的说明文档包括 [Security Alerts Assessment](https://github.com/LearningCircuit/local-deep-research/blob/main/.github/SECURITY_ALERTS.md)、[Scorecard Compliance](https://github.com/LearningCircuit/local-deep-research/blob/main/.github/SECURITY_SCORECARD.md)、[Container CVE Suppressions](https://github.com/LearningCircuit/local-deep-research/blob/main/.trivyignore) 和 [SAST Rule Rationale](https://github.com/LearningCircuit/local-deep-research/blob/main/bearer.yml)。

## 高级功能

### MCP Server

LDR 提供了一个 MCP（Model Context Protocol）服务器，允许 Claude Desktop、Claude Code 等 AI 助手通过 STDIO 传输执行深度研究。安装方式：

```bash
pip install "local-deep-research[mcp]"
```

可用工具包括：`search`（针对特定引擎的原始结果，无 LLM 成本）、`quick_research`、`detailed_research`、`generate_report`、`analyze_documents` 等。注意该 MCP 服务器设计用于本地使用（STDIO 传输），没有内置认证或速率限制，如有网络暴露需求需自行实现安全控制。

### REST API

LDR 提供经过认证的 HTTP API，适合与现有系统集成。API 使用需要 CSRF token 处理，仓库在 `examples/api_usage/http/` 目录中提供了完整的可运行示例，包括自动用户创建、认证处理、结果重试逻辑和进度监控。

### 分析与监控

内置分析仪表板跟踪成本、性能和使用情况。CLI 工具支持基准测试和速率限制管理：

```bash
# 运行基准测试
python -m local_deep_research.benchmarks --dataset simpleqa --examples 50

# 速率限制状态
python -m local_deep_research.web_search_engines.rate_limiting status
```

### 期刊质量系统

一个值得注意的功能是内置的**期刊质量评分系统**，数据来源包括：
- **OpenAlex**（CC0）：约 280K 来源和 120K 机构的学术元数据
- **DOAJ**（CC0）：开放获取期刊验证
- **Stop Predatory Journals**（MIT）：掠夺性期刊/出版商黑名单

系统自动对 212K+ 收录来源打分，识别掠夺性期刊，并提供质量仪表板。

### 新闻与研究订阅

LDR 支持自动化研究摘要订阅，可以按主题设置定期（每日/每周/自定义）接收 AI 过滤后的研究更新，支持 Markdown 报告和结构化摘要两种格式。

### 输出格式

报告可以导出为：Markdown、PDF、LaTeX、Quarto、RIS 和 BibTeX。

## Python API 示例

```python
from local_deep_research.api import LDRClient, quick_query

# 方式一：一行研究
summary = quick_query("username", "password", "What is quantum computing?")
print(summary)

# 方式二：客户端（多次操作）
client = LDRClient()
client.login("username", "password")
result = client.quick_research("What are the latest advances in quantum computing?")
print(result["summary"])
```

## 适用场景与局限性

### 适合的场景

- **隐私敏感研究**：医疗、法律、商业敏感话题的调查不希望经过第三方服务器
- **学术文献调研**：arXiv、PubMed、Semantic Scholar 的综合搜索与本地知识积累
- **开发者集成**：通过 REST API 或 LangChain Retriever 接入现有知识管理系统
- **本地实验**：在没有网络 API 成本的情况下测试大模型研究能力

### 局限性

- **SimpleQA ~95% 是初步数据**：README 明确说明样本量有限，性能因查询类型、模型版本和配置差异较大
- **本地模型效果依赖硬件**：在消费级 GPU（如 RTX 3090）上运行 20B+ 参数模型是可行的，但更大模型可能需要更专业硬件
- **某些页面无法抓取**：尊重 robots.txt，部分页面可能被阻止
- **安全限制**：MCP server 无内置认证，不适合直接网络暴露
- **无密码恢复**：AES-256 加密无后门，遗忘密码将无法恢复数据

### 与其他工具的对比

README 被 Medium 文章引用时特别提到：LDR 对于注重隐私的用户"值得特别关注"，它针对可以在消费级 GPU 甚至 CPU 上运行的开源 LLM 进行了调优，记者、研究人员或处理敏感话题的公司可以在不经过外部服务器的情况下调查信息。

## 总结

local-deep-research 是一个功能完整的本地 AI 科研助手，核心优势在于：

1. **真正的本地运行**：数据从不离开你的机器，支持 Ollama、LM Studio、llama.cpp 全本地推理
2. **广泛的数据源覆盖**：10+ 搜索引擎，包括主要学术数据库和主流网络搜索
3. **可积累的知识库**：研究过程中发现的内容可本地化存储和向量索引，下次研究可跨私有文档与网络
4. **隐私优先的设计**：SQLCipher AES-256 加密、零遥测、无追踪
5. **丰富的集成选项**：REST API、MCP Server、LangChain Retriever、多种输出格式

如果你在寻找一个可以完全控制数据、不依赖云端 API 的 AI 研究工具，LDR 值得一试。完整的文档、示例和社区基准测试数据都可以在 [GitHub 仓库](https://github.com/LearningCircuit/local-deep-research) 中找到。

---

**延伸资源：**

- [GitHub 仓库](https://github.com/LearningCircuit/local-deep-research)
- [Hugging Face 基准测试数据集](https://huggingface.co/datasets/local-deep-research/ldr-benchmarks)
- [社区基准测试仓库](https://github.com/LearningCircuit/ldr-benchmarks)
- [Docker Compose 部署指南](https://github.com/LearningCircuit/local-deep-research/blob/main/docs/docker-compose-guide.md)
- [完整配置参考](https://github.com/LearningCircuit/local-deep-research/blob/main/docs/CONFIGURATION.md)
- [架构文档](https://github.com/LearningCircuit/local-deep-research/blob/main/docs/architecture.md)