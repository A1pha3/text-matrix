---
title: "Onyx 中文指南：自托管 AI 平台的入门到精通"
date: "2026-03-28T13:30:00+08:00"
lastmod: "2026-09-23T10:00:00+08:00"
slug: "onyx-ai-platform-guide"
github_repo: "onyx-dot-app/onyx"
source_key: "gh:onyx-dot-app/onyx"
aliases:
  - /posts/tech/onyx-ai-platform-guide/
description: "Onyx 是开源可自托管的 AI 平台，支持任意 LLM、Agentic RAG、50+ 连接器、MCP 双向集成与代码执行沙箱。本文基于 v4.7.8 讲解原理、架构、部署与扩展。"
draft: false
categories: ["技术笔记"]
tags: ["RAG", "AI Agent", "MCP", "自托管", "企业搜索"]
---

# Onyx 中文指南：自托管 AI 平台的入门到精通

> 预计阅读时间：33 分钟 | 难度：⭐⭐⭐⭐

---

> **目标读者**：想为企业或团队搭建私有 AI 助理平台的开发者与运维
> **前置知识**：Docker 基础、对 LLM 与 RAG 有基本认知
> **版本口径**：Onyx v4.7.8（2026-09-21 发布），数据核实于 2026-09-23
> **项目地址**：https://github.com/onyx-dot-app/onyx

---

## 章节导航

| 小节 | 主题 | 难度 |
|------|------|------|
| §1 | 学习目标 | ⭐ |
| §2 | 原理分析：为什么需要 Onyx 这样的平台 | ⭐⭐ |
| §3 | 架构分析：服务组成与索引机制 | ⭐⭐⭐ |
| §4 | 核心功能：Actions、MCP、Connectors 与 Craft | ⭐⭐⭐ |
| §5 | 安装与部署（CLI / Docker / Kubernetes / Terraform） | ⭐⭐ |
| §6 | 使用指南：从首次启动到日常管理 | ⭐⭐ |
| §7 | 开发扩展：OpenAPI、MCP 与 API | ⭐⭐⭐⭐ |
| §8 | 推荐做法 | ⭐⭐⭐ |
| §9 | 常见问题（FAQ） | ⭐⭐ |

---

## §1 学习目标

完成本文后，可以：

- 判断 Onyx 是否适合你的场景，以及它与 Dify、Langflow 这类工具的定位差异
- 说出 Onyx 的服务组成、混合索引机制和两种部署模式的取舍
- 用 Onyx CLI 或 Docker Compose 完成一次可用的部署
- 在管理界面接入 LLM、配置连接器、创建自定义 Agent
- 通过 OpenAPI 或 MCP 为 Agent 扩展外部工具，或把 Onyx 本身暴露为 MCP 服务器
- 按团队规模规划资源，并了解社区版与企业版的功能边界

---

## §2 原理分析：为什么需要 Onyx 这样的平台

### 2.1 直接调 API 差在哪

大语言模型的 API 已经足够便宜和快，但企业要把 AI 用起来，问题从来不在"能不能对话"：

- **数据不出内网**。文档、工单、会议记录散落在 Confluence、Google Drive、Slack、Jira 里，直接贴给第三方 API 既慢又不合规。
- **知识会过期**。模型的知识有截止日期，而组织内的信息每天在变。
- **权限要跟着人走**。同一个问题，实习生和部门负责人应该看到不同的答案来源。
- **工具要联动**。查内部知识库、搜外网、跑一段 Python 画图——纯对话接口覆盖不了这些动作。

Onyx 对这四个问题的回答是：自托管平台 + 连接器索引 + 权限同步 + Actions 工具体系。

### 2.2 Onyx 是什么

Onyx（前身 Danswer，LICENSE 中的公司名 DanswerAI 和 CDN 路径里的 `/danswer/` 还留着这段历史）把自己定义为 "the application layer for LLMs"——LLM 之上的应用层。这个定位在 v3 时期还写作 "a feature-rich, self-hostable Chat UI that works with any LLM"，v4 起官方口径从"聊天界面"升格为"AI 平台"。

它解决的事情可以归成三层：

| 层 | 能力 | 一句话说明 |
|------|------|------|
| 知识层 | 50+ 索引型连接器、文件上传、Ingestion API | 把组织知识同步进来，近实时更新，附带权限信息 |
| 对话层 | Chat、Search、Custom Agents、Deep Research、Voice | 多个入口共用同一套知识层与权限体系 |
| 动作层 | 5 个内置 Actions、OpenAPI/MCP 自定义扩展、Craft | 让模型能搜外网、跑代码、调外部系统、产出交付物 |

模型侧不锁定供应商：OpenAI、Anthropic、Gemini 等商业 API，以及 Ollama、vLLM、LiteLLM 等自托管推理，都在支持之列，全部在管理界面配置。

### 2.3 与 Dify、Langflow、Flowise 的定位差异

这三者常被拿来和 Onyx 比较，但它们回应的是不同的问题。看各家 README 的自述：Dify 是 "open-source LLM app development platform"（LLM 应用开发平台），Langflow 是 "building and deploying AI-powered agents and workflows"（可视化构建 Agent 与工作流，还内置 API 和 MCP 服务器），Flowise 的口号是 "Build AI Agents, Visually"。它们的共同点是**面向开发者**——你用它们从零搭建一个应用或工作流。

Onyx 不是开发框架，而是**开箱即用的成品**：部署之后就是一个带连接器生态、检索体系和权限管理的组织知识平台，普通员工直接用浏览器访问，不需要先"搭"一个应用。如果你要为特定业务拼装定制流程，Dify/Langflow/Flowise 更顺手；如果你要给全公司一个"能答公司内部问题的 AI"，Onyx 这类知识平台是另一个物种。

许可证方面值得一提：Onyx 采用社区版（CE）+ 企业版（EE）双版本，仓库根 LICENSE 声明 `ee/` 目录之外的代码遵循 MIT Expat，`ee/` 目录遵循单独的 Onyx Enterprise License。Dify 和 Flowise 的许可证同样是"基础协议 + 附加条款"（GitHub 因此标记为 NOASSERTION），对比时别只看协议缩写。

---

## §3 架构分析：服务组成与索引机制

### 3.1 技术栈

仓库语言占比（GitHub API，2026-09-23 实测）：Python 约 64%、TypeScript 约 26%、Go 约 6%，其余为 HCL、Shell 等。后端是 Python（FastAPI 体系），前端是 Next.js，另有一批 Go 写的周边工具（CLI、Terraform provider）。

### 3.2 服务组成

官方 docker-compose 部署起 9 类服务。理解每个容器干什么，排障时才知道日志该看哪里：

| 服务 | 镜像 | 职责 |
|------|------|------|
| api_server | onyxdotapp/onyx-backend | 同步 API：鉴权、对话、管理界面后端 |
| background | onyxdotapp/onyx-backend | 后台任务：连接器同步、索引构建（Celery 队列） |
| web_server | onyxdotapp/onyx-web-server | Next.js 前端 |
| indexing_model_server | onyxdotapp/onyx-model-server | 索引期深度学习模型（embedding 等） |
| inference_model_server | onyxdotapp/onyx-model-server | 推理期模型（rerank 等） |
| relational_db | postgres:15.2-alpine | 关系数据：用户、对话、连接器配置、文档元数据 |
| opensearch | opensearchproject/opensearch:3.6.0 | 关键词 + 向量混合索引 |
| cache | redis:7.4-alpine | 缓存与任务队列 |
| minio | quay.io/minio | 文件对象存储 |
| code-interpreter | onyxdotapp/code-interpreter | 独立的 Python 沙箱容器，版本线独立（当前 0.4.7） |
| nginx | nginx:1.25.5-alpine | 反向代理入口 |

Onyx Lite 模式则只保留聊天必需的最小集合（无向量索引、无后台 worker、无模型服务器），文件直接存 PostgreSQL。

### 3.3 索引层：一套代码，两个引擎

Onyx 的检索是关键词 + 向量的混合索引。有意思的是索引引擎有两个实现，按部署形态区分：

- **Docker Compose 部署用 OpenSearch**。v4.0.0（2026-05-26）起 compose 栈默认带 OpenSearch，官方还提供了从旧引擎（Vespa）迁移索引的指南与后台迁移任务（源码里的 `opensearch_migration` Celery 任务）。
- **Kubernetes/Helm 部署用 Vespa**。Helm chart 官方描述是 "packages all the required services (API, web, PostgreSQL, Vespa, etc.)"，源码中 `document_index/vespa` 的实现仍在活跃维护。

混合检索的真实机制以 OpenSearch 路径为例：关键词查询与向量查询作为两路独立的 Search phase 并行执行，互不感知，再由 normalization processor 把两路分数归一化融合——某路没有命中的文档在该路记 0 分（源码中 `document_index/opensearch/README.md` 专门解释了这个 "minimum value clipping" 行为及其对时间衰减加权的影响）。评估或复现检索效果时，以这套双路归一化机制为准。

顺带说明：v3 时期官方 README 宣传 RAG 特性时还带有 "knowledge graph" 字样，v4.7.8 的 README 已经只提混合索引，评估时以现行口径为准。

### 3.4 一次请求会发生什么

以对话中上传一份销售 CSV 并要求"画出月度趋势图"为例，整个链路是：

```text
用户上传 sales.csv + 提问
  → api_server 鉴权，LLM 判断需要代码执行（无需显式调用）
  → 代码发送到 code-interpreter 沙箱容器
      沙箱内预装 numpy/pandas/scipy/matplotlib
      无外网访问，只能触达随代码传入的文件
  → 生成的图表随 stdout/文件返回
  → Chat UI 直接在对话里渲染图表
```

如果问题触发的是知识检索（比如"我们公司的退货政策是什么"），走的则是另一条路：LLM 发起 Internal Search → 混合索引召回 → 重排 → 生成答案并附引用。两个 Action 可以在同一次对话里先后触发。

---

## §4 核心功能：Actions、MCP、Connectors 与 Craft

### 4.1 五个内置 Actions

Actions 是 Agent 与外部系统交互的通道。官方内置 5 个：

| Action | 用途 | 需要配置 | 服务商选项 |
|------|------|------|------|
| Internal Search | 检索已索引的组织知识 | 是 | 内置，组件可替换 |
| Web Search | 实时外网搜索 | 是 | Google PSE、Serper、Exa、Brave、SearXNG，爬虫可选内置或 Firecrawl |
| Code Execution | 沙箱内执行 Python、分析数据、产出图表 | 否 | 内置，所有部署开箱可用 |
| Image Generation | 文生图 | 是 | OpenAI、Azure OpenAI |
| Coding Agent（Beta） | 调查公开 GitHub 代码库 | 是 | 内置，默认关闭 |

几点容易踩坑的边界：图像生成只支持 OpenAI 和 Azure OpenAI 两家（没有 Stable Diffusion）；Web Search 的"搜索"与"抓取网页"是两个独立配置项；代码执行沙箱**没有外网访问**，也不能读沙箱外的文件系统。

### 4.2 MCP：双向集成

Onyx 对 MCP（Model Context Protocol）的支持是双向的，这是它区别于多数自托管平台的一点：

- **作为 MCP 客户端**：在管理界面把任意外部 MCP 服务器注册为自定义 Action，Agent 就能调用它的工具。认证支持共享凭据或按用户走各自的 OAuth/token 流程。
- **作为 MCP 服务器**：把 Onyx 的知识库检索暴露给 Claude Desktop、Claude Code、Cursor、Windsurf 等任意 MCP 客户端，让它们在各自的界面里直接查公司知识。配置就是在客户端的 MCP 配置里加一项：

```jsonc
{
  "mcpServers": {
    "onyx": {
      "url": "https://your-onyx-domain/mcp",  // 自托管填自己的域名；云版为 https://cloud.onyx.app/mcp
      "headers": {
        "Authorization": "Bearer YOUR_ONYX_TOKEN_HERE"
      }
    }
  }
}
```

权限体系在 MCP 路径上同样生效——每个 token 背后的用户能看到什么，检索结果就只有什么。

### 4.3 Connectors：知识从哪来

连接器负责把外部系统的文档、元数据和权限信息同步进 Onyx。仓库 `backend/onyx/connectors/` 目录实测有 58 个子目录，扣除工具与测试目录后，与官方"50+ indexing based connectors"的口径一致，覆盖 Confluence、Google Drive、Slack、Jira、GitHub、GitLab、Notion、Salesforce、SharePoint、Gmail、Outlook、Zoom 等常见系统。没有现成连接器的场景，可以用文件上传、Ingestion API 推送，或自己实现一个连接器包。

连接器是增量轮询同步的（由 background 容器的 Celery 队列驱动），文档、元数据、访问权限近实时保持更新。**注意权限同步是企业版功能**：社区版索引文档时不镜像源系统的 ACL，企业版才能做到"用户在源系统看不到的文档，在 Onyx 也检索不到"。

### 4.4 Custom Agents

Agent 是"指令 + 知识范围 + Actions"的组合，在 Admin Panel → Agents 里创建：起名、写指令（system prompt）、配 Conversation Starters，然后勾选知识来源和可用 Actions。

知识范围有个值得理解的默认行为：**什么都不显式选择时，Agent 能检索"当前使用者可见的一切"**——包括用户自己上传的文件、所有公开连接器的文档、以及权限同步连接器里该用户有权访问的文档。一旦显式勾选了某些知识源，范围就收窄为仅这些来源。官方文档给出的理由是搜索质量随规模缓慢衰减，大组织里收窄范围反而提升答案质量。

### 4.5 Craft：v4 的重头戏

Craft 是 v4 引入的"AI 同事"，把一个目标直接变成成品交付物：调研报告、演示文稿、表格、可交互的 dashboard 或小型 web 应用，甚至跨系统完成工作（草拟邮件、更新 issue、提交 PR）。它与普通对话的区别在于拥有独立 workspace：规划任务、写代码、跑代码、迭代产出，全部在隔离沙箱中进行，沙箱与本机和 Onyx 基础设施隔离。

支撑 Craft 的是四个功能面，各自解决一个重复使用的问题：

- **Skills**——可复用的指令、示例与文件，让同类任务不必每次从头交代。源码里已内置 pptx 等 skill。
- **Apps**——连接外部工具，Craft 由此取实时上下文、执行获批动作。
- **Scheduled Tasks**——按计划周期性运行 Craft 提示词。
- **Coding Agent**——调查 GitHub 代码库并回答问题。

部署上 Craft 默认关闭。Docker Compose 需要追加官方 overlay（`docker-compose.craft.yml`，额外引入沙箱容器与出口代理 egress proxy）；Kubernetes 模式则启用每用户沙箱 pod、NetworkPolicy、出口代理与定时任务 worker。Compose 模式下沙箱容器通过宿主 Docker socket 创建，这等价于 root 权限，官方明确要求仅用于受信主机。

### 4.6 其他值得知道的能力

- **Deep Research**：多步研究流程，产出深度报告。官方自称在自建的 onyx_deep_research_bench 榜单上截至 2026 年 2 月排名第一——这是官方自述，榜单也在官方仓库，参考即可。
- **Onyx Anywhere**：除了浏览器，同一套知识还可通过桌面应用、Chrome 扩展、网站 Widget、Slack Bot、Discord Bot、CLI、MCP 服务器访问，移动端应用文档标注"即将推出"。
- **LLM Gateway**：把你自己应用里的 LLM 请求路由到 Onyx 已配置的模型与访问控制上，让平台顺便充当组织级的 LLM 网关。
- **企业版功能清单**：SSO（Google OAuth、OIDC、SAML）与 SCIM 用户供给、RBAC、按团队/模型/Agent 维度的用量分析、Query History 审计、白标定制，以及通过自定义代码做 PII 清除、敏感查询拦截等。

---

## §5 安装与部署（CLI / Docker / Kubernetes / Terraform）

### 5.1 先选模式

| | Onyx Lite | Onyx Standard |
|------|------|------|
| 定位 | 轻量 Chat UI | 完整平台 |
| 内存基线 | 不足 1 GB | 见下方资源表 |
| RAG 混合索引 | 无 | 有 |
| 连接器后台同步 | 无 | 有 |
| 模型推理服务器 | 无 | 有 |
| 适合 | 快速试用、只要聊天和 Agent | 正式使用、更大规模的团队 |

### 5.2 推荐方式：Onyx CLI

官方当前的首选安装方式是 CLI 引导安装（v4 起提供，安装脚本只是它的薄包装）：

```bash
uv tool install onyx-cli && onyx-cli deploy install
```

安装器会检查系统资源（Linux 上缺 Docker 可代装）、让你选 Lite 还是 Standard、选版本，然后把部署配置放在 `~/.config/onyx`，拉镜像起容器并等全部服务健康。后续生命周期也归它管：

```bash
onyx-cli deploy upgrade    # 升级
onyx-cli deploy status     # 状态
onyx-cli deploy logs       # 日志
onyx-cli deploy stop       # 停止
onyx-cli deploy uninstall  # 卸载
```

一键脚本等价于 CLI 安装，适合复制粘贴场景：

```bash
curl -fsSL https://onyx.app/install_onyx.sh | bash
```

### 5.3 Docker Compose 手动部署

```bash
git clone --depth 1 https://github.com/onyx-dot-app/onyx.git
cd onyx/deployment/docker_compose
docker compose up -d
```

compose 文件从 `env.template` 读配置（复制为 `.env` 即可），注释写明"No edits necessary, works out of the box"——**LLM API key 不在 .env 里配**，`.env` 管的是部署层（镜像 tag、Craft 开关、沙箱资源限制等），模型、连接器全部进管理界面配。容器就绪后访问 `http://localhost:3000` 完成初始化。

要启用 Craft，追加官方提供的 overlay：

```bash
docker compose -f docker-compose.yml -f docker-compose.craft.yml up -d
```

### 5.4 Kubernetes / Helm

Helm 仓库与安装：

```bash
helm repo add onyx https://onyx-dot-app.github.io/onyx/
helm repo update
kubectl create namespace onyx
helm install onyx onyx/onyx -n onyx
```

chart 会打包全部依赖服务（含 Vespa 索引引擎），有状态服务默认创建持久卷。本地验证可以端口转发：

```bash
kubectl -n onyx port-forward service/onyx-nginx 8080:80
```

定制走 `deployment/helm/charts/onyx/values.yaml`，改完 `helm upgrade` 生效。chart 有独立的版本线（如 onyx-0.8.29），与 Onyx 应用版本号不同步，升级时注意区分。

### 5.5 Terraform：建基础设施与管运行配置是两回事

Onyx 的 Terraform 资产有两套，容易混：

1. **Terraform modules**（仓库 `deployment/terraform/modules/aws`）：在 Onyx 存在之前**建 AWS 基础设施**——VPC、EKS、RDS for PostgreSQL、ElastiCache for Redis、S3，可选 OpenSearch 与 WAF。官方定位是"参考实现"，明确建议 fork 后按自己的账号、网络与合规要求改造，而不是当黑盒直接用。要求 Terraform ≥ 1.12.0。infra 起来之后再装 Onyx 工作负载（用上面的 Helm chart）。
2. **Terraform provider**（仓库 `terraform-provider-onyx`）：对**已在运行的 Onyx 实例**做配置管理——LLM 提供商、连接器、Document Set、Agent 等，面向想用基础设施即代码的方式管 Onyx 配置的团队。

### 5.6 资源规划

官方资源指南给出：

| 模式 | 最低 | 建议 |
|------|------|------|
| Lite | 2 vCPU / 2 GB RAM / 10 GB 磁盘 | 4 vCPU / 4 GB / 50 GB |
| Standard | 4 vCPU / 10 GB / 32 GB + 约 2.5 倍索引数据量 | 8+ vCPU / 16+ GB / 500 GB（5000 用户以内组织） |

两个运维要点：OpenSearch 在磁盘用量到达 flood stage 水位（默认 95%）时会把索引切为只读，**写入全部被拒**，务必监控磁盘；模型服务器会把 HuggingFace 模型缓存进 Docker 卷，首次启动拉模型需要时间和磁盘。

### 5.7 不想自己部署：Onyx Cloud

托管版带全部企业版功能，2 周免费试用（不要信用卡），SOC 2 Type II 与 GDPR 合规。对没有运维人力的团队，这往往是评估 Onyx 的最快路径。

---

## §6 使用指南：从首次启动到日常管理

### 6.1 初始化顺序

1. 部署完成后访问站点，按引导创建管理员账户。
2. **Admin Panel → Language Models** 接入至少一个 LLM。界面按三类组织：直连供应商（OpenAI、Anthropic）、云平台与聚合器（Azure OpenAI、Amazon Bedrock、Google Vertex AI、OpenRouter、LiteLLM Proxy、Bifrost）、自托管推理（Ollama、LM Studio、自定义推理供应商）。同一页可设置默认模型与快速模型。
3. 配置 Actions：Web Search 选服务商并填 key；代码执行开箱即用，无需配置。
4. 建连接器，等第一轮索引同步完成。
5. 按部门或场景创建 Custom Agents。

### 6.2 日常使用的三个入口

- **Chat**：默认对话界面，Auto 模式下系统自动判断是问答还是找文档。
- **Search**：纯检索视图，带时间范围、作者、标签过滤，适合"我要找那份文档"而非"帮我回答"的场景。
- **Craft**：目标导向的交付物生产，见 §4.5。

对话里可以随时开关某个 Action（输入框下方按 MCP 服务器/OpenAPI schema 分组），比如临时关掉 Web Search 强制走内部知识。

### 6.3 升级

```bash
# CLI 部署
onyx-cli deploy upgrade

# Docker Compose 部署
docker compose pull && docker compose up -d

# Helm 部署
helm upgrade onyx onyx/onyx -n onyx -f values.yaml
```

升级前看 Release Notes。**特别提醒跨 v4.0.0 的升级**：v4.0.0 起文档索引默认迁移到 OpenSearch，官方在发布说明里警告——如果没有先在 v3.x 上完成索引迁移就升级，已索引的文档会保不住。老部署先跑迁移，再动版本。

---

## §7 开发扩展：OpenAPI、MCP 与 API

### 7.1 给 Agent 加自定义 Action

两条路，都不需要改 Onyx 源码：

- **OpenAPI**：把符合 OpenAPI Specification 的 API schema 注册进 Onyx，schema 里的每个 endpoint 变成 Agent 可调用的动作。适合接内部 REST 服务。
- **MCP**：注册任意外部 MCP 服务器，见 §4.2。

两者共享同一套认证模型：管理员可配全局共享凭据，也可强制每个用户各自走一遍授权（token 或 OAuth），后者保证动作以用户自己的身份与权限执行。

### 7.2 把 Onyx 当 API 用

- **REST API**：文档站 developers 区提供完整 OpenAPI 规格（108 个接口页面）。
- **Ingestion API**：程序化推文档进索引，配合标准连接器覆盖不到的内部系统。
- **MCP Server**：§4.2 的对外出口。

### 7.3 开发者生态位

源码仓库对开发者友好的几个信号：`AGENTS.md`/`CLAUDE.md` 在仓库根部为 AI 编码工具提供上下文；`Makefile` 收敛了开发命令；官方维护 `onyx-cli`、Terraform provider、桌面端（`desktop/`）、移动端（`mobile/`）、网站组件（`widget/`）多个子项目。想深入检索内部，`backend/onyx/document_index/opensearch/README.md` 是少见的把搜索引擎怪癖写清楚的内部文档，值得通读。

---

## §8 推荐做法

**权限同步是企业版的，社区版要先想清楚。** 社区版会把连接器指定源的文档全部索引，检索时不按源系统 ACL 过滤。把含敏感内容的系统接进来之前，确认你的合规边界，必要时用 Document Set 或（OpenSearch 迁移后的）知识范围控制收窄可见面。

**从 Lite 或 Cloud 开始验证，再上 Standard。** Standard 模式最小的常驻内存也要 10 GB 量级，加上索引数据是 2.5 倍膨胀，先跑通业务价值再扩容更稳。

**给 OpenSearch 留足磁盘并设告警。** 95% 水位触发只读是"静默故障"的典型来源——服务还活着，但索引写入全部失败，表现为连接器同步报错。

**Craft 打开前评估沙箱边界。** Compose 模式下沙箱经宿主 Docker socket 创建容器，等价 root 权限；官方的替代是 Kubernetes 模式（独立沙箱节点 + NetworkPolicy + 出口代理）。对安全敏感的环境，直接用 K8s 部署 Craft。

**模型策略从"一个默认 + 一个快速"起步。** Language Models 页支持多供应商并存与默认/快速模型分工，先用默认模型跑通场景，再按成本与延迟细化，避免一开始就陷入多模型运维。

---

## §9 常见问题（FAQ）

### Q1：遇到问题去哪求助？

按序尝试：官方文档 [docs.onyx.app](https://docs.onyx.app)；GitHub Issues 搜历史问题；[Discord 社区](https://discord.gg/TDJ59cGV2X) 实时交流（活跃，核心开发者常在）；企业版用户走专属支持渠道。

### Q2：能完全离线（气隙）部署吗？

可以。官方从 v3 起就声明支持完全气隙环境运行，仓库里也有 airgap 测试用的 compose 文件。要点：提前在能联网的环境拉齐全部镜像，LLM 用自托管推理（Ollama/vLLM 等），外网搜索与外部连接器在气隙下自然不可用，MinIO/PostgreSQL/Redis 本就是 compose 内置服务不依赖外网。

### Q3：社区版和企业版怎么分？

社区版（MIT）覆盖 Chat、RAG、Agents、Actions 的核心能力，个人与中小团队够用。企业版（`ee/` 目录，单独许可）主要补组织级能力：RBAC、权限自动同步、SSO 高级配置、高级知识管理等。完整对照见官网 pricing 页。判断标准很简单：检索结果要不要跟源系统权限走，要，就在企业版或 Cloud 里。

### Q4：和直接买 ChatGPT 企业版比，选它的理由是什么？

答案取决于知识在哪里。如果组织知识主要在 SaaS（Notion、Google Drive）且不介意数据出境，托管方案更省事。如果知识在内网系统、合规要求数据不出去、或者要把检索能力嵌进自己的工具链（MCP/API），自托管 Onyx 才是那个选项。

### Q5：升级会丢数据吗？

关系数据在 PostgreSQL 卷、文件在 MinIO 卷、索引在 OpenSearch/Vespa 卷，常规小版本升级不动数据。跨 v4.0.0 之前必须先完成索引迁移（见 §6.3），否则已索引文档不保。任何升级前做一次卷备份都是廉价保险。

---

## 扩展阅读

| 资源 | 链接 | 说明 |
|------|------|------|
| 官方文档 | [https://docs.onyx.app](https://docs.onyx.app) | 部署、管理、开发全量文档，312 页 |
| GitHub 仓库 | [https://github.com/onyx-dot-app/onyx](https://github.com/onyx-dot-app/onyx) | 源码、Issue、PR |
| Release Notes | [GitHub Releases](https://github.com/onyx-dot-app/onyx/releases) | 版本变更，升级前必读 |
| OpenSearch 索引迁移 | [迁移指南](https://docs.onyx.app/admins/advanced_configs/opensearch_document_index_migration) | v3.x → v4 的必做功课 |
| MCP 规范 | [https://modelcontextprotocol.io](https://modelcontextprotocol.io) | MCP 协议官方站点 |
| Discord 社区 | [discord.gg/TDJ59cGV2X](https://discord.gg/TDJ59cGV2X) | 官方社区 |

---

## 参考来源与口径说明

- 本文数据与机制核实于 2026-09-23，版本锚点为 **v4.7.8**（2026-09-21 发布）；写作时点的 v3.0.5（2026-03-25）距今已跨一个大版本，全文按现行口径重写。
- 关键事实来源：GitHub API（stars 32,200、forks 4,497、语言占比、release 时间线）、仓库 main 分支源码与文件树（`deployment/docker_compose/docker-compose.yml` 服务组成、`backend/onyx/connectors/` 58 个子目录、`document_index/{opensearch,vespa}` 双实现、`env.template` 配置面）、官方文档站 docs.onyx.app（Quickstart、Actions & MCP、Code Execution、Connectors、Craft、Resourcing、Kubernetes、Terraform、MCP Server 等 20 余页，经 `llms.txt` 索引逐页核对）。
- 原文（v3.0.5 时点）写作时的部分口径今已变化：官方定位句 "feature-rich, self-hostable Chat UI" 在 v4 README 中已改为 "the application layer for LLMs"；v3 README 宣传的 "knowledge graph" 在 v4 已不再提及；连接器数量从 40+ 增至 50+。这些属于上游演进，非原文错误。
- 本轮修订替换的原文失实内容，此处留档备查：`VECTOR_DB_TYPE`/`LLM_PROVIDER`/`PII_FILTER_ENABLED` 等 .env 环境变量（Onyx 的 LLM 与搜索配置在管理界面完成，.env 仅管部署层）；`onyx.actions`/`onyx.connectors` Python 扩展 API（真实扩展面为 OpenAPI/MCP 配置与连接器包开发）；Terraform Registry module 写法；`charts.onyx.app` Helm 仓库地址（实际为 `onyx-dot-app.github.io/onyx/`）；`discord.gg/onyx` 之外的 `blog.onyx.app` 与 YouTube 频道链接（实测无效或无关）；混合检索"RRF + alpha 权重"伪代码（实际为 OpenSearch 双路查询 + normalization processor）；"支持 DALL-E、Stable Diffusion"的图像生成（实际仅 OpenAI/Azure OpenAI）。
