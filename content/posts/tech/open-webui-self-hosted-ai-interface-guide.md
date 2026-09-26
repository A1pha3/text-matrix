---
title: "Open WebUI：自托管 AI 界面的部署、原理与扩展"
date: "2026-05-02T10:11:52+08:00"
lastmod: "2026-09-26T00:00:00+08:00"
slug: "open-webui-self-hosted-ai-interface-guide"
github_repo: "open-webui/open-webui"
source_key: "gh:open-webui/open-webui"
description: "Open WebUI 把 Ollama、OpenAI 兼容 API 与 Claude 等模型来源收进同一个自托管界面。本文拆解它的架构与 RAG 流水线，给出 Docker、pip、uv 三条安装路径和 Tools、Pipelines 两种扩展写法，并覆盖升级迁移与离线部署的注意事项。"
draft: false
categories: ["技术笔记"]
tags: ["Ollama", "RAG", "Docker", "LLM", "自托管"]
---

# Open WebUI：自托管 AI 界面的部署、原理与扩展

本地跑大模型的人，多数是从 Ollama 的命令行开始的：换模型要改参数，对话历史随服务重启消失，文档问答要自己搭检索。Open WebUI 把这些日常操作搬进了一个自托管界面——Ollama、OpenAI 兼容 API、Claude 等模型来源接在同一处，普通用户拿到的是聊天界面，运维拿到的是权限管理和审计。

本文基于 [open-webui/open-webui](https://github.com/open-webui/open-webui) 官方仓库及 [官方文档](https://docs.openwebui.com/) 编写：先讲清楚它怎么工作，再给出现成的安装命令和常见故障的排查办法，最后是 Tools 与 Pipelines 两种扩展写法。文中命令与参数以撰写时点的 `main` 分支为准，升级前建议核对官方文档。

**目录**：
1. [核心概念与原理](#1-核心概念与原理)
2. [系统架构](#2-系统架构)
3. [安装配置](#3-安装配置)
4. [实战演示](#4-实战演示)
5. [开发与扩展](#5-开发与扩展)
6. [学习路径与进阶方向](#6-学习路径与进阶方向)

---

## 1. 核心概念与原理

### 1.1 解决什么问题

在没有 Open WebUI 之前，使用本地大模型（尤其是 Ollama）通常要在终端敲命令，或者自己写一个简单的 Web 调用层。这带来了几个实际的痛点：

- **模型切换麻烦**：每次换一个模型都要改命令或代码
- **没有持久化对话上下文**：重启服务后对话历史全部丢失
- **RAG 能力缺失**：无法方便地将本地文档作为检索增强的来源
- **多人协作困难**：无法细粒度控制谁能访问哪个模型
- **界面体验差**：缺乏 Markdown 渲染、代码高亮、多模态支持

Open WebUI 把这些问题收进一个开箱即用的完整 AI 前端，并支持不依赖互联网的本地（离线）部署——前提是模型权重、嵌入（embedding）模型等资源已提前就位。

### 1.2 支持的模型来源

Open WebUI 是一个**模型无关**的接入层，支持的主流模型来源见下表：

| 模型来源 | 说明 | 连接方式 |
|--------|------|---------|
| **Ollama** | 本地运行大模型的核心运行时 | `OLLAMA_BASE_URL` 配置 |
| **OpenAI API** | OpenAI 官方及兼容 API（LMStudio、GroqCloud、Mistral、OpenRouter、vLLM 等） | `OPENAI_API_KEY` + 自定义 API URL |
| **Anthropic** | Claude 系列模型。URL 含 `api.anthropic.com` 时自动识别：模型发现走原生接口（密钥放 `x-api-key` 头），聊天请求走 Anthropic 的 OpenAI 兼容端点 | 在 **Settings → Admin → Connections** 添加连接 |
| **本地 GPU 镜像** | `:cuda` 镜像自带 NVIDIA CUDA 支持（不含 Ollama）；要单容器打包 Ollama 用 `:ollama` 镜像 | Docker 启动参数控制 |

注意区分两个带标签的镜像：`:cuda` 只是在标准镜像基础上加了 CUDA 12.8 支持，启动时需要 `--gpus all`；把 Ollama 一起塞进容器的是 `:ollama`。两者可以组合出 GPU 版一体化镜像（见 3.3），但「`:cuda` 内置 Ollama」是常见误解。

Anthropic 接入还有一个官方声明的边界值得知道：其 OpenAI 兼容 API 定位是评估与测试，而非生产负载。实践中对话、流式输出、工具调用都能正常工作；但如果依赖 Claude 的完整原生能力（PDF 处理、引用标注、extended thinking、prompt caching），官方建议走原生 `/v1/messages` 接口，可以通过 pipe 函数或 LiteLLM 之类的代理接入。

### 1.3 RAG（检索增强生成）原理

Open WebUI 内置了完整的 RAG 流水线，原理如下：

```
用户查询 ──▶ 向量化查询（Embedding） ──▶ 向量数据库检索 ──▶ 拼接上下文 ──▶ LLM 生成答案
```

具体实现上：

1. **文档提取**：支持 Tika、Docling、Document Intelligence、Mistral OCR、PaddleOCR-vl 及外部加载器（external loaders）等多种解析引擎，可处理 PDF、DOCX、PPT、Markdown 等格式
2. **向量存储**：内置 9 种向量数据库可选——ChromaDB、PGVector、Qdrant、Milvus、Elasticsearch、OpenSearch、Pinecone、S3Vector、Oracle 23ai，通过配置切换
3. **检索策略**：默认支持混合检索（BM25 关键词 + 向量相似度），可叠加重排序（reranking），另有跳过检索、直接把整个文档塞进上下文的 full-context 模式
4. **检索触发**：对话中输入 `#` 后跟文件名或 URL，即可在聊天中引用文档内容；或者将文档预先加入知识库，通过 `#` 引用
5. **Web 搜索增强**：可配置多种 Web 搜索提供商（如 SearXNG、Google PSE、Brave Search、Perplexity 等），搜索结果直接注入对话上下文

### 1.4 权限模型（RBAC）

Open WebUI 实现了基于角色的访问控制（Role-Based Access Control）：

- **管理员**：可创建用户组、分配模型权限、管理 Ollama 模型（pull/push）
- **普通用户**：在授权范围内使用已分配的模型
- **访客**：可选开启公开访问模式，无需注册登录

这种设计适合企业内部分部门授权的场景——不同部门看到不同模型，且普通用户无法自行 pull 新模型，避免带宽和算力的无序消耗。

---

## 2. 系统架构

### 2.1 整体架构图

```
┌──────────────────────────────────────────────────┐
│ Open WebUI                                       │
│ Frontend (SvelteKit) ◄► Backend (FastAPI, :8080) │
└──────────────────────────────────────────────────┘
                         │
                         ▼ 后端按模型来源分发请求、读写数据
┌────────────────┐ ┌────────────────────┐ ┌───────────────────┐ ┌───────────────────────┐
│ Ollama（本地） │ │ OpenAI 兼容 API    │ │ Pipelines（可选） │ │ 数据与文件存储        │
└────────────────┘ │ 云端 / 自建 / vLLM │ │ 独立进程 :9099    │ │ SQLite / PostgreSQL   │
                   │ / Anthropic        │ └───────────────────┘ │ 向量数据库（RAG）     │
                   └────────────────────┘                       │ S3 / GCS / Azure Blob │
                                                                └───────────────────────┘
```

### 2.2 前后端分离设计

- **前端**：基于 SvelteKit 构建，提供响应式界面（桌面 / 移动端自适应）、PWA 离线支持（localhost 范围内）、Markdown + LaTeX 完整渲染
- **后端**：Python FastAPI，提供 REST API 和 WebSocket 实时通信
- **通信协议**：默认 `8080` 端口，通过 WebSocket 实现流式输出（Streaming），前端实时逐字显示 LLM 生成内容

图中 Pipelines 是唯一画在框外的服务组件——它是独立部署的可选进程（见 5.1），Open WebUI 通过把它当成一个 OpenAI 兼容端点来接入，而不是内置模块。

### 2.3 持久化存储

Open WebUI 支持三种数据持久化方式：

| 存储方式 | 配置项 | 适用场景 |
|--------|-------|---------|
| **SQLite**（默认） | 内置，开箱即用，可选静态加密 | 个人用户、轻量部署 |
| **PostgreSQL** | `DATABASE_URL` 环境变量 | 生产环境、多用户 |
| **云存储（S3/GCS/Azure Blob）** | `S3_*` / `GCS_*` / `AZURE_*` 前缀配置 | 大规模文件、企业级 |

### 2.4 水平扩展

生产级部署通过以下机制实现水平扩展：

- **Redis 会话管理**：多 Worker 之间共享会话状态
- **WebSocket 支持**：在负载均衡器（nginx/HAProxy）后面运行多个实例
- **OpenTelemetry 集成**：内置 traces、metrics、logs 输出，可对接 Prometheus + Grafana 等监控栈

---

## 3. 安装配置

### 3.1 安装方式对比

| 安装方式 | 推荐场景 | 端口 | GPU 支持 |
|---------|---------|------|---------|
| **Docker**（推荐） | 快速体验、生产部署 | 3000:8080 | 通过 `--gpus all` |
| **pip** | 已有 Python 环境，不想用 Docker | 8080 | 依赖宿主机的推理后端（如 Ollama） |
| **uv** | 使用 uv 包管理器的用户 | 8080 | 同 pip |
| **Desktop App** | macOS / Windows / Linux 桌面用户，无需 Docker，内置 llama.cpp 引擎可选全本地推理 | — | 内置引擎或宿主机 Ollama |

> ⚠️ **版本要求**：pip/uv 安装方式需要 **Python 3.11 或 3.12**。官方暂不支持 Python 3.13——部分依赖尚未发布兼容版本，在 3.13 上安装会失败或在运行时崩溃。两个受支持版本之间也有取舍：官方最重度测试的组合是 Docker 镜像配 Python 3.11，3.12 可用但有零星未复现的异常报告，遇到说不清的问题先退回 3.11。

### 3.2 Docker 安装（最简方式）

假设 Ollama 与 Open WebUI 均运行在本地机器：

```bash
docker run -d \
  -p 3000:8080 \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

启动完成后访问 **http://localhost:3000**。

> 注意：这里将容器内端口 `8080` 映射到宿主机的 `3000`。要让容器访问宿主机上运行的 Ollama（默认 `127.0.0.1:11434`），不同平台处理方式不同：macOS / Windows 的 Docker Desktop 已内置 `host.docker.internal`；Linux 需加 `--add-host=host.docker.internal:host-gateway`。连接不上的排查见 3.7。

### 3.3 Docker + Ollama 集成安装

如果希望 Ollama 和 Open WebUI 在同一个容器中运行（不需要宿主机预装 Ollama），使用 `:ollama` 镜像：

```bash
# GPU 版本
docker run -d \
  -p 3000:8080 \
  --gpus all \
  -v ollama:/root/.ollama \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:ollama

# CPU 版本
docker run -d \
  -p 3000:8080 \
  -v ollama:/root/.ollama \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:ollama
```

> ⚠️ **GPU 前提条件**：需要宿主机的 Linux/WSL 已安装 [NVIDIA CUDA Container Toolkit](https://docs.nvidia.com/dgx/nvidia-container-runtime-upgrade/)。

### 3.4 连接远程 Ollama 或云端 API

**远程 Ollama**（Ollama 运行在其他服务器上）：

```bash
docker run -d \
  -p 3000:8080 \
  -e OLLAMA_BASE_URL=https://your-ollama-server.com \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

**仅使用 OpenAI API**：

```bash
docker run -d \
  -p 3000:8080 \
  -e OPENAI_API_KEY=sk-your-secret-key \
  -e OPENAI_API_BASE_URL=https://api.openai.com/v1 \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

Open WebUI 同时支持多个 API 来源混用，在界面中可以同时看到 Ollama 模型和 OpenAI 模型，随时切换。

### 3.5 pip / uv 安装

```bash
# pip
pip install open-webui
open-webui serve

# uv（官方文档示例，DATA_DIR 指定数据目录）
curl -LsSf https://astral.sh/uv/install.sh | sh
DATA_DIR=~/.open-webui uvx --python 3.11 open-webui@latest serve
```

服务启动后访问 **http://localhost:8080**。uv 方式务必带上 `DATA_DIR`：`uvx` 默认把数据放进临时目录，进程结束后可能被清理，对话历史会跟着丢。

### 3.6 离线环境配置

在完全隔离的内网环境中运行，需要阻止 Open WebUI 及底层依赖（Hugging Face 等）的模型下载请求外联：

```bash
export HF_HUB_OFFLINE=1
# 然后启动 open-webui serve
```

`HF_HUB_OFFLINE=1` 让依赖内置缓存离线加载模型；若环境连缓存都未预置，首启时仍可能因找不到模型而报错。用 Docker 部署时有个便利：标准 `:main` 镜像已经内置了语音转文字和 embedding 模型，离线场景不需要再单独准备这两类资源。涉密或高安全级别场景下，还应把硬件与出口网络一并纳入隔离范围，仅设环境变量不足以替代完整隔离。

### 3.7 常见安装问题排查

**Ollama 连接错误（最常见）**：

如果遇到 WebUI 无法连接 Ollama 的问题，通常是因为容器网络无法访问宿主机上的 Ollama 端点。解决方案是使用 `--network=host` 模式：

```bash
docker run -d \
  --network=host \
  -v open-webui:/app/backend/data \
  -e OLLAMA_BASE_URL=http://127.0.0.1:11434 \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

使用 `--network=host` 时，端口映射从 `3000:8080` 变为直接使用 `8080`，访问地址改为 **http://localhost:8080**。

---

## 4. 实战演示

### 4.1 首次配置：连接 Ollama

1. 启动 Open WebUI 后，首次打开界面需要注册管理员账户（第一个注册的账号自动成为管理员）
2. 在 **Settings → Admin → Connections** 中配置模型来源（各版本菜单位置略有差异，以界面为准）
3. 如果 Ollama 在宿主机上运行，在连接设置中把 Ollama 地址填为 `http://host.docker.internal:11434`（配合 3.2 的 `--add-host` 参数）
4. 也可以在模型管理界面直接拉取（pull）新模型，等价于在 Ollama 命令行执行：

```bash
# 在 Ollama 命令行中拉取模型（也可在 WebUI 界面操作）
ollama pull llama3.2:latest
ollama pull qwen2.5:14b
```

5. 拉取完成后，在左上角模型选择下拉框中切换不同模型进行对话

### 4.2 RAG 实战：基于本地文档的检索增强

**步骤 1：上传文档到知识库**

在 **Workspace** 区域的 Knowledge（知识库）部分，将 PDF、DOCX、Markdown 等格式的文档上传。系统会自动调用文档解析引擎提取文本内容，生成向量并存入指定的向量数据库。

**步骤 2：在对话中引用文档**

对话输入框中输入 `#` 触发文档引用：

```
#sales-report-2024.pdf 请总结这份报告的核心结论
```

或者先通过 `#` 将文档加载到当前对话上下文中，再提出具体问题：

```
#annual-report.pdf
```

此时文档内容已被注入上下文，向量化检索后拼接进 LLM 的 prompt 中。

**步骤 3：配置向量数据库**

向量库与检索参数在管理面板（**Admin Panel → Settings → Documents**）中配置。个人用户默认使用内置 SQLite 存储；生产环境建议切换到 PGVector（配合 PostgreSQL）或 Qdrant，以获得更好的检索性能和可扩展性。

### 4.3 多模型对比回复

Open WebUI 支持在同一任务上让多个模型各自生成回答，便于对比取舍：

1. 在 **Settings → Admin → Connections** 中添加多个模型来源（Ollama + OpenAI API 等）
2. 对话界面中选中多个模型，系统会分别调用并并排展示各方回答

这种模式适合需要对照的场景——例如用 DeepSeek 处理推理逻辑，用 Claude 处理代码生成，人工比较后择优。

### 4.4 语音 / 视频通话功能

Open WebUI 内置了免提语音通话能力，支持：

- **语音转文字（STT）**：Whisper（本地）、OpenAI、Deepgram、Azure
- **文字转语音（TTS）**：Azure、ElevenLabs、OpenAI、Transformers、WebAPI

在对话界面中点击麦克风图标即可开启语音输入，无需手动打字。

### 4.5 Python 函数调用（Workspace Tools）

Open WebUI 允许把 Python 代码注册为 Tool（工具），挂到模型上供其在对话中调用。工具在 **Workspace → Tools** 中管理，一个工具就是一个 Python 文件，由两部分组成：顶部的 docstring 元数据和名为 `Tools` 的类。

一个可用的最小示例：

```python
"""
title: Calculator
author: your-name
description: 执行安全的四则运算表达式计算
version: 0.1.0
licence: MIT
"""

from pydantic import BaseModel, Field


class Tools:
    def __init__(self):
        self.valves = self.Valves()

    class Valves(BaseModel):
        # 管理员可在界面里改的配置项
        max_length: int = Field(200, description="允许的最大表达式长度")

    async def calculate(self, expression: str) -> str:
        """
        计算一个四则运算表达式并返回结果。

        :param expression: 只含数字与 + - * / ( ) 的表达式，例如 "12 * (3 + 4)"
        """
        allowed = set("0123456789+-*/(). ")
        if len(expression) > self.valves.max_length:
            return "错误：表达式过长"
        if not set(expression) <= allowed:
            return "错误：表达式包含不允许的字符"
        try:
            result = eval(expression, {"__builtins__": {}}, {})
            return f"结果为：{result}"
        except Exception as e:
            return f"计算错误：{e}"
```

几条写法约定直接影响工具能不能被正确调用：

- **方法 docstring 就是给模型看的说明书**。`:param name:` 逐条生成参数描述，模型据此决定何时调用、传什么参数；类型标注会转成 JSON Schema，参数不标类型一律按字符串处理。
- **公共方法都会暴露给模型**，内部辅助方法名要以 `_` 开头；方法建议写成 `async`，官方明确同步函数在未来版本可能阻塞执行。
- **`Valves` 子类**定义管理员可配置项（如 API 密钥），配置在界面里改，不用动代码。

调用模式上，现在默认且唯一支持的是 Native（Agentic）模式，走模型的原生工具调用 API，要求所用模型本身具备工具调用能力；早期的 Legacy 提示词注入模式已废弃，新写的工具不要依赖它。

安全上不能含糊：**Workspace Tools 在服务器上执行任意 Python 代码**，官方文档的原话是「授予用户创建或导入 Tool 的权限，等同于把 shell 访问权限交给他」。所以工具的创建/导入权限应只给可信管理员，引入第三方工具前先读代码。上面示例用字符白名单限制了 `eval()` 的输入，`__builtins__` 也已清空，但正式环境仍建议换成真正的表达式解析器，并控制工具对网络、文件的访问。

---

## 5. 开发与扩展

### 5.1 Pipelines 插件框架

Open WebUI 支持通过 [Pipelines Plugin Framework](https://github.com/open-webui/pipelines) 扩展核心功能。官方仓库提供了多个示例：

| 示例 | 功能说明 |
|-----|---------|
| **Function Calling** | 演示如何让 LLM 调用外部工具 |
| **Rate Limiting** | 限制请求频率，防止超限 |
| **Usage Monitoring** | 对接 Langfuse、Opik 等可观测性平台 |
| **Live Translation** | LibreTranslate 实时翻译对话 |
| **Toxic Message Filtering** | 过滤恶意 / 有毒内容 |
| **Custom RAG** | 用 LlamaIndex 等实现定制检索流水线 |

部署 Pipelines 后，将 Open WebUI 的 OpenAI API URL 指向 Pipelines 实例（默认 `9099` 端口）即可启用对应功能。

### 5.2 企业认证集成

生产环境中的企业用户推荐使用以下认证方案：

- **LDAP / Active Directory**：与企业现有账号体系对接
- **SCIM 2.0**：自动化用户生命周期管理（入职 / 离职 / 权限变更），可对接 Okta、Azure AD、Google Workspace
- **SSO via Trusted Headers**：通过可信请求头实现单点登录
- **OAuth**：支持主流 OAuth 提供商

这几种方式的配置入口并不统一：LDAP、OAuth、Trusted Headers 在管理面板的设置页中配置；SCIM 则完全通过环境变量配置，官方明确没有提供 UI 界面，部署前要把 `SCIM_*` 变量写进编排配置。

### 5.3 开发环境搭建

如果你想参与 Open WebUI 本身的开发，或基于源码进行定制：

```bash
git clone https://github.com/open-webui/open-webui.git
cd open-webui
git checkout dev
```

开发需要两个终端分别跑前后端。后端（终端 1）：

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt -U
sh dev.sh
# 后端启动于 http://localhost:8080，API 文档在 /docs 路径
```

前端（终端 2，需要 Node.js 22.10+）：

```bash
cd open-webui
cp -RPp .env.example .env
npm install
npm run build
npm run dev
# 前端启动于 http://localhost:5173，后端未就绪时会显示等待画面
```

几个常见的坑：`npm install` 报兼容性警告时，按官方文档加 `--force` 重试；构建期 Node 内存不足时，先 `export NODE_OPTIONS="--max-old-space-size=4096"` 再跑前端命令；`5173` 或 `8080` 端口被占用时，可在 `vite.config.js`（前端）或 `dev.sh`（后端）里换端口。

注意一定要切到 `dev` 分支再构建——`main` 是发布日的快照，从 `main` 构建拿到的是已经落后的代码。

前端代码在 `src/` 目录（基于 SvelteKit），后端在 `backend/`（Python FastAPI）。

### 5.4 使用 `:dev` 分支体验最新功能

如果想提前测试尚未发布的新特性：

```bash
docker run -d \
  -p 3001:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui-dev:/app/backend/data \
  -e WEBUI_SECRET_KEY=your-secret-key \
  --name open-webui-dev \
  --restart always \
  ghcr.io/open-webui/open-webui:dev
```

> ⚠️ **警告**：`:dev` 对应官方 `dev` 开发分支，包含最新的不稳定变更，可能有 bug 或未完成的功能，不建议在生产环境使用。注意命令里用了独立的数据卷 `open-webui-dev` 和独立的 `WEBUI_SECRET_KEY`，避免与生产实例的数据和密钥混用（详见 5.5）。

### 5.5 数据库迁移与升级

使用 Docker 安装时，更新 Open WebUI 版本需要注意数据持久化：

```bash
# 拉取新镜像
docker pull ghcr.io/open-webui/open-webui:main

# 重启容器（数据卷 open-webui 会自动保留）
docker stop open-webui && docker rm open-webui
docker run -d \
  -p 3000:8080 \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

只要 `-v open-webui:/app/backend/data` 数据卷存在，用户数据、对话历史、配置信息都会保留。跨大版本升级前建议先备份该数据卷，避免数据库迁移异常导致数据不可回退；更新完成后刷新页面即可。

---

## 6. 学习路径与进阶方向

### 6.1 快速上手路径

第一次接触，建议按依赖顺序推进：先通过 Docker 安装并连上本地 Ollama，确认基础对话可用；再上传几份文档建知识库，用 `#` 引用语法体会 RAG 检索的效果差异；然后接入一个云端 API 来源，用多模型对比功能观察同一问题的不同回答；语音输入输出优先级最低，放在最后配置。每一步都验证通过再进下一步，出问题时容易定位是网络、模型还是配置的原因。

### 6.2 进阶方向

往生产走，四条路线按需选：

- **RAG 生产落地**：向量数据库选型（内置 9 种，见 1.3）、分块与检索策略调优。可以从 Qdrant、PGVector 的官方文档入手。
- **工具与插件开发**：按 4.5 的 Tools 规范写自定义工具，复杂编排走 [Pipelines](https://github.com/open-webui/pipelines)，参考仓库里的官方示例。
- **企业级部署**：PostgreSQL + PGVector、Redis 水平扩展、OpenTelemetry 接监控栈，配套内容在官方文档的 Advanced Topics 与 enterprise 章节里。
- **前端定制**：基于 SvelteKit 改界面，源码在仓库的 `src/` 目录，5.3 的开发环境是起点。

---

## 总结

Open WebUI 把本地 AI 部署的使用门槛降了下来，同时兼顾了功能完整度和企业级扩展。从个人笔记本到企业私有集群，一套界面就能覆盖 Ollama、OpenAI API、Claude 等主要模型来源。

部署前值得先想清楚两件事：你的模型运行在哪儿（本地 Ollama 还是云端 API），以及需要哪种数据持久化（单机 SQLite 还是生产用 PostgreSQL）。这两点决定了选什么镜像、配什么环境变量。如果团队需要频繁切换模型、用本地文档做 RAG、或者按部门管理访问权限，这些需求它都直接覆盖。

**官方资源**：
- 仓库：https://github.com/open-webui/open-webui
- 文档：https://docs.openwebui.com/
- Discord 社区：https://discord.gg/5rJgQTnV4s

