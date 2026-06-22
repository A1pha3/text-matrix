---
title: "Stirling-PDF 架构拆解:82k stars 的开源 PDF 平台,从单 Java 后端演化成 3 模块 Monorepo + Python AI Document Engine"
date: 2026-06-22T20:59:00+08:00
slug: "stirling-pdf-open-source-pdf-platform-architecture"
categories: ["技术笔记"]
tags: ["PDF", "Java", "Spring Boot", "FastAPI", "Monorepo", "架构分析"]
description: "Stirling-PDF 是 GitHub 上 stars 最高的 PDF 工具(82k+),从早期单 Spring Boot 应用演化成 app(Java) + frontend(TypeScript) + engine(Python) 三模块 Monorepo,新引入的 engine 用 pydantic-ai + pgvector/sqlite-vec 把 AI 文档处理接进来。"
---

# Stirling-PDF 架构拆解:82k stars 的开源 PDF 平台,从单 Java 后端演化成 3 模块 Monorepo + Python AI Document Engine

## 核心判断

`Stirling-Tools/Stirling-PDF` 是 **GitHub 上 stars 最高的 PDF 工具集**(82,443 stars / 7,215 forks,2026-06-22 数据),最早是 2023 年一个单 Java Spring Boot 应用,到现在已经演化成 **3 模块 Monorepo**:

```
Stirling-PDF/
├── app/        ← Java Spring Boot 后端(10M LOC)
├── frontend/   ← TypeScript React 编辑器(10M LOC,新)
└── engine/     ← Python FastAPI AI Document Engine(新)
```

把仓库当"一个 PDF 工具箱"会严重低估它;实际上,**这个仓库正在做一件事**:把"PDF 工具集"重新组织成 **"文档平台"**,而 AI Document Engine 是新方向的伏笔。

理解 Stirling-PDF 的关键不是 50 多个 PDF 工具,而是这 3 件事:

1. **50+ 工具如何组织** —— 26 个 API Controller(实际是 50+ 端点,有些 Controller 包 4-8 个端点)、统一的 `useBaseTool` / `useToolOperation` Hook 让前端能"插件式"接新工具;
2. **3 模块怎么协调** —— `Taskfile.yml` 顶层 include 6 个子 Taskfile(backend / frontend / engine / docker / desktop / e2e / pre-commit),`task dev` 一键起后端 + 前端且自动找空闲端口;
3. **AI Document Engine 的引入** —— `engine/` 是新增的 Python FastAPI + pydantic-ai + pgvector/sqlite-vec 服务,直接对接 RAG / embedding / agent loop,**意图明显:把 PDF 处理从"机械操作"扩展到"理解 + 操作"**。

## 项目速览

| 维度 | 数据 |
| --- | --- |
| 仓库 | [`Stirling-Tools/Stirling-PDF`](https://github.com/Stirling-Tools/Stirling-PDF) |
| Stars / Forks | 82,443 / 7,215 |
| 创建 | 2023-01-27(原 `Frooodle/Stirling-PDF`) |
| 最近 push | 2026-06-22(仍在活跃开发) |
| 主分支 | `main` |
| 最近 release | v2.13.1(2026-06-19,desktop 移动端 QR 上传 + 多工具旋转 bug 修复) |
| Open Issues | 456 |
| License | Other(open-core,具体见 `LICENSE`) |
| Topics | `pdf`、`pdf-editor`、`pdf-converter`、`pdf-tools`、`self-hosted`、`java`、`docker` |
| 部署形态 | Docker / 桌面客户端 / 浏览器 / 自托管 API |

## 语言与体量

仓库当前代码语言分布(2026-06-22):

| 语言 | 字节数 |
| --- | --- |
| **Java** | 10,037,265 |
| **TypeScript** | 10,022,140 |
| **Python** | 1,156,388 |
| CSS | 688,791 |
| Shell | 248,391 |
| Gherkin | 157,928 |
| Rust | 140,518 |
| JavaScript | 84,881 |
| HTML | 65,559 |
| Dockerfile | 50,968 |

**Java 与 TypeScript 字节数几乎相同** —— 这是 3 模块架构最直观的证据:后端、前端各占一半的工程量,Python 的引入是后期增量。

## 系统地图

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          Stirling-PDF Monorepo                                │
│                                                                                │
│  app/                         frontend/                    engine/            │
│  (Java Spring Boot)           (TypeScript React)           (Python FastAPI)    │
│  ┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────┐│
│  │ SPDFApplication.java │    │ editor/              │    │ FastAPI app      ││
│  │                      │    │   src/hooks/tools/   │    │   agents/        ││
│  │ controller/api/      │    │   src/components/    │    │   api/           ││
│  │   26 个 API 控制器   │    │   src/tools/         │    │   documents/     ││
│  │   (50+ PDF 工具)     │    │                      │    │   services/      ││
│  │   MergeController    │    │ useBaseTool Hook     │    │   models/        ││
│  │   SplitPDFController │ ←→ │ useToolOperation     │    │                  ││
│  │   Converters/*       │    │ createToolFlow()     │    │ pydantic-ai      ││
│  │   filters/*          │    │                      │    │ pgvector/        ││
│  │   pipeline/*         │    │ portal/ (落地页)     │    │ sqlite-vec       ││
│  │   security/*         │    │ shared/              │    │ OpenTelemetry    ││
│  │                      │    │   i18n (40+ 语言)    │    │ PostHog          ││
│  │ service/* (PDF 操作) │    │                      │    │                  ││
│  │ pdf/    (PDFBox 等)  │    │ .storybook/          │    │ ⚠️ AI Document   ││
│  │ config/ (SSO/审计)   │    │                      │    │   Engine (新)    ││
│  │                      │    │                      │    │                  ││
│  │ build.gradle         │    │ package.json         │    │ pyproject.toml   ││
│  │ Taskfile.yml (backend)│   │ Taskfile.yml (FE)    │    │ Taskfile.yml (E) ││
│  └──────────────────────┘    └──────────────────────┘    └──────────────────┘│
│                                                                                │
│  顶层 Taskfile.yml include 6 个子 Taskfile:                                   │
│   backend / frontend / engine / docker / desktop / e2e / pre-commit           │
│                                                                                │
│  数据库支持: SQLite (默认) / PostgreSQL + pgvector (AI Engine)                  │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Module 1:`app/` —— Java Spring Boot 后端(核心)

### 26 个 API Controller = 50+ 工具入口

`app/core/src/main/java/stirling/software/SPDF/controller/api/` 下有 26 个 Controller 文件,**每个 Controller 对应一类 PDF 操作的端点集合**:

| Controller | 端点职责 |
| --- | --- |
| `MergeController` | 合并多份 PDF |
| `SplitPDFController` | 按页数 / 书签切分 |
| `SplitPdfByChaptersController` | 按章节切 |
| `SplitPdfBySectionsController` | 按章节切 |
| `SplitPdfBySizeController` | 按文件大小切 |
| `RotationController` | 旋转 |
| `CropController` | 裁边 |
| `ScalePagesController` | 缩放 |
| `MultiPageLayoutController` | 多页合一 |
| `PosterPdfController` | 把 PDF 拆成海报块 |
| `RearrangePagesPDFController` | 重排页序 |
| `ToSinglePageController` | 全部页拼成一张 |
| `PdfOverlayController` | 叠加水印 |
| `EditTextController` | 编辑文本 |
| `EditTableOfContentsController` | 改目录 |
| `BookletImpositionController` | 装订排版 |
| `AnalysisController` | 元数据分析 |
| `AdditionalLanguageJsController` | 多语言加载 |
| `UIDataController` | UI 元数据 |
| `SettingsController` | 用户设置 |
| `converters/` | 格式转换(子目录,多种格式) |
| `filters/` | 滤镜/水印(子目录) |
| `form/` | 表单填写(子目录) |
| `misc/` | 其他杂项 |
| `pipeline/` | 管道化(批处理) |
| `security/` | 安全相关(SSO/审计) |

`controller/web/` 下还有 4 个 Web Controller:

- `ReactRoutingController` —— 把所有非 `/api/*` 路由转发到 React 前端的 SPA 入口
- `MetricsController` —— Prometheus 指标
- `SignatureImageController` —— 签名图存储
- `UploadLimitService` —— 上传大小限制

**这是典型的"按业务域垂直切片"架构**:同一类操作的所有端点集中在同一个 Controller,而不是按"读 / 写"分 Controller。优势是新增工具时影响面小,劣势是部分 Controller 文件会膨胀(参考 `ADDING_TOOLS.md` 里反复强调"如果端点多就拆子目录")。

### Spring Boot 配置体系

`SPDFApplication.java` 是入口,`config/` 目录下提供:

- SSO(LDAP / OAuth2)
- 审计日志
- 数据库备份(`DATABASE.md` 详细描述了备份机制:每日 cron 自动备份 + 管理操作触发手动备份 + Web/API 上传 SQL 恢复)
- 启动时检查 + 安全基线

## Module 2:`frontend/` —— TypeScript React 编辑器

### "加新工具"标准流程(从 `ADDING_TOOLS.md` 看架构)

`frontend/editor/src/` 下的代码组织**严格按"工具"切分**:

```
frontend/editor/src/
├── hooks/tools/[toolName]/
│   ├── use[ToolName]Parameters.ts    # 参数定义 + 校验
│   └── use[ToolName]Operation.ts     # 操作逻辑(用 useToolOperation)
│
├── components/tools/[toolName]/
│   └── [ToolName]Settings.tsx        # 设置 UI
│
└── tools/
    └── [ToolName].tsx                # 主组件(用 createToolFlow)
```

**关键抽象**:

- `useBaseTool` —— 统一管理"文件选择 + 折叠状态 + 参数 + 操作"的 Hook,所有新工具都用它,不用从零写状态机。
- `useToolOperation` —— 把"构造 FormData + 调用 endpoint + 错误处理"封装成声明式 config:
  ```typescript
  export const mergeOperationConfig = {
    toolType: ToolType.multiFile,        // 单文件 / 多文件
    buildFormData: buildMergeFormData,   // 参数 → FormData
    operationType: 'merge',              // 后端 operation 类型
    endpoint: '/api/v1/general/merge',   // 后端端点
    filePrefix: 'merged_',
  } as const;
  ```
- `createToolFlow()` —— 把 `selectedFiles + parameters + operation + result` 装进统一的页面流(文件选择区 → 设置区 → 执行按钮 → 结果展示区)。

**这一层抽象让"加一个新工具"变成 4 个文件**:

1. `useToolNameParameters.ts`(参数 schema)
2. `useToolNameOperation.ts`(调用逻辑)
3. `ToolNameSettings.tsx`(UI)
4. `ToolName.tsx`(主组件,通常 < 50 行,只是把上面 3 个 hook 串起来)

后端只新增一个 `@PostMapping` 端点,**前后端解耦**。这是 Stirling-PDF 能同时维护 50+ 工具的关键架构杠杆。

### `portal/` + `shared/` + `.storybook/`

- `portal/` —— 落地页 / 营销页,和编辑器分离。
- `shared/` —— 共享组件,i18n 配置(40+ 种语言)。
- `.storybook/` —— Storybook 组件文档,组件级别 UI 开发独立于业务集成。

## Module 3:`engine/` —— Python AI Document Engine(新方向)

这是 v2.x 周期新增的模块,**项目意图最明确的标志**。

`engine/pyproject.toml` 的依赖列表:

```toml
dependencies = [
  "fastapi>=0.116.0",                  # Web 框架
  "jinja2>=3.1.0",                     # 模板
  "pgvector>=0.3.6",                   # PG 向量扩展
  "psycopg[binary,pool]>=3.2",         # PG 驱动
  "pydantic>=2.0.0",                   # 数据建模
  "pydantic-ai>=1.67.0",               # ← AI agent 框架
  "pydantic-ai-slim[voyageai]>=1.67.0",# ← Voyage AI embedding
  "pydantic-settings>=2.0.0",
  "python-dotenv>=1.2.1",
  "sqlite-vec>=0.1.6",                 # ← SQLite 向量检索
  "uvicorn>=0.35.0",
  "opentelemetry-sdk>=1.39.0",         # ← 可观测
  "posthog>=3.0.0",                    # ← 产品分析
]
```

Python 3.13+,src layout,`src/stirling/` 下分 6 个子目录:

| 目录 | 推测职责 |
| --- | --- |
| `agents/` | pydantic-ai 智能体定义 |
| `api/` | FastAPI 路由 |
| `config/` | pydantic-settings 配置 |
| `contracts/` | 数据契约(可能是 OpenAPI 生成) |
| `documents/` | 文档处理 |
| `models/` | 数据模型 |
| `services/` | 业务服务 |
| `logging.py` | 日志配置 |

`engine` 与 `app` 的关系(README 与 DATABASE.md 推断):

- `app` 仍负责 PDF 机械操作(合并 / 拆分 / 转换 / 加密),作为底层工具库。
- `engine` 在 `app` 之上,提供**理解文档 + 多步推理** 的能力 —— 比如"读完 50 页合同后回答关于第 12 条的违约责任"。

数据库策略:**SQLite + sqlite-vec** 是默认(单文件部署,适合 self-hosted);**PostgreSQL + pgvector** 是规模部署选项。

`pyproject.toml` 里 `datamodel-code-generator[ruff]` 出现两次,加上 `ruff` 出现两次 —— 说明 engine 项目**严格用 datamodel-code-generator 从 OpenAPI / JSON Schema 自动生成 Python model**,而不是手写。

## 构建系统:Task 跨模块编排

顶层 `Taskfile.yml` 用 `includes` 引入 7 个子 Taskfile:

```yaml
includes:
  backend:   { taskfile: .taskfiles/backend.yml,   dir: . }
  frontend:  { taskfile: .taskfiles/frontend.yml,  dir: frontend }
  engine:    { taskfile: .taskfiles/engine.yml,    dir: engine }
  docker:    { taskfile: .taskfiles/docker.yml,    dir: . }
  desktop:   { taskfile: .taskfiles/desktop.yml,   dir: frontend }
  e2e:       { taskfile: .taskfiles/e2e.yml,       dir: . }
  pre-commit:{ taskfile: .taskfiles/pre-commit.yml, dir: . }
```

`task dev` 的实现:

```bash
# task dev 顶层任务
dev:
  vars:
    PORTS: "{{if eq OS \"windows\"}}powershell ... {{else}}bash scripts/find-free-port.sh{{end}} 8080 5173"
    BACKEND_PORT:  "{{index (splitList \"\\n\" .PORTS) 0}}"
    FRONTEND_PORT: "{{index (splitList \"\\n\" .PORTS) 1}}"
  deps:
    - task: backend:dev   # 在 BACKEND_PORT 启动 Spring Boot
    - task: frontend:dev  # 在 FRONTEND_PORT 启动 Vite + 配置 BACKEND_URL
```

**亮点是"自动找空闲端口"**:`scripts/find-free-port.sh` 在 8080 和 5173 都被占时会自动找下一个可用端口,避免开发机和 CI 同时跑多套环境时的端口冲突。

## 关键设计取舍

### 1. 为什么用 3 模块 Monorepo 而不是微服务?

- **共享数据库 schema**:`app` 用 SQLite/Postgres 存用户 / 备份 / 审计,`engine` 直接连同一个 DB(pgvector 扩展共存)。微服务拆分会让数据层变得复杂。
- **共享文档对象**:`engine` 操作 PDF 时直接调 `app` 的端点(而不是重新实现 PDFBox / qpdf 逻辑),通过 HTTP 而非 RPC 简化部署。
- **统一构建**:开发时一次 `task dev` 起 3 个进程,生产时 Docker Compose 编排 3 个容器。

代价:语言生态分裂(Java + TS + Python),新人上手成本高,但**3 个模块边界清晰、各自的 dependency graph 独立**,没出现"巨型单体"的问题。

### 2. 为什么新增 Python AI Engine 而不是用 Java?

- `pydantic-ai` 是 Python 生态原生 AI agent 框架,和 LangChain / LlamaIndex 同一量级,**Java 生态目前没有同等成熟度**。
- `pgvector` / `sqlite-vec` / Voyage AI / OpenTelemetry / PostHog 都在 Python 侧更顺手。
- **AI 模块独立迭代节奏** 和后端 PDF 操作不一样,Python 的开发-部署循环比 Java 快。

### 3. 为什么前端用 Hook + Config 而不是 Redux/Zustand?

每个工具的参数 + 操作都是独立的,**工具间几乎不共享状态**。React Hook + `useBaseTool` 直接在组件级别封死状态,避免引入全局 store 的复杂度。代价是"跨工具的工作流"需要自己拼,但 50+ 工具目前没有跨工具的复杂需求。

### 4. 为什么把"加新工具"文档化(`ADDING_TOOLS.md`)?

50+ 工具在长期演进中最大的风险是**风格漂移**:`useBaseTool` 引入前的旧工具可能直接用 `useState`,导致新老工具风格分裂。`ADDING_TOOLS.md` 强制要求"新工具**必须**用 `useBaseTool`",把约束写在文档里比写在 PR review 里更有效。

### 5. 为什么用 Task 而不是 Makefile / npm scripts?

Makefile 在 Windows 上体验差(默认没有 bash),npm scripts 不能跨语言(Java/Python/TS 三栈),Gradle/Maven 是 Java-only。

Taskfile 是 **YAML 配置 + 跨平台** 的中间方案,`includes` 机制让顶层 Task 能委托到子目录的子 Task,正好匹配"3 模块 Monorepo"的结构。

## 部署形态

| 形态 | 适用场景 | 入口 |
| --- | --- | --- |
| **Docker** | 生产 / 自托管 | `docker run -p 8080:8080 docker.stirlingpdf.com/stirlingtools/stirling-pdf` |
| **桌面客户端** | 个人离线 | `task desktop:dev`(在 frontend/ 里构建 Electron + Spring Boot 后端) |
| **浏览器 SaaS** | 不愿自托管的用户 | 官方 Stirling.com 托管版 |
| **Kubernetes** | 企业部署 | 见 `docs.stirlingpdf.com` 的 Helm chart |
| **私有 API** | 集成到现有系统 | 直接调 REST endpoints(几乎所有工具都有 API) |

## 适用边界

- **不要把它当"PDF 阅读器"** —— Stirling-PDF 没有阅读器界面(没有"翻页 / 高亮 / 笔记"功能),只做"修改 / 转换 / 提取"。
- **不要把它当"重型文档管理系统"** —— 它没有版本控制、协作评论、权限细粒度(只有 SSO + 审计)。
- **不要把 engine 当生产可用** —— `engine/pyproject.toml` 是 v0.1.0,AI Document Engine 仍在早期,**主要功能(PDF 工具)仍在 app 模块**。
- **桌面端企业级场景** —— 见 `WINDOWS_SIGNING.md` 和 `SHARED_SIGNING.md`,签名 / 权限模型有专章,但不是 trivial。

## 适用人群

| 你是 | 这个项目对你的价值 |
| --- | --- |
| **法律 / 财务 / 行政团队** 需要处理大量 PDF | Docker 一行起,50+ 工具覆盖合并 / 拆分 / 转换 / OCR / 签名全部场景 |
| **企业 IT** 想私有化 PDF 处理流水线 | SSO + 审计 + 数据库备份 + REST API 完备,符合合规要求 |
| **Java + Spring Boot 架构师** 找大型开源项目样本 | 50+ 端点的 Controller 组织 + 任务域垂直切片是教科书级案例 |
| **AI Agent 工程师** 想看"老牌开源项目 + AI 集成" | engine 模块用 pydantic-ai + pgvector + OpenTelemetry,是非常新的工程化范例 |
| **想学习 React Hook 抽象边界** 的前端 | `useBaseTool` / `useToolOperation` / `createToolFlow` 三件套是"加新功能 = 加新文件,不动旧代码"的范本 |

## 这篇文章不覆盖什么

- 单个 PDF 工具的具体操作流程(Merge / Split / OCR 的 UI 怎么点) —— 见官方 docs.stirlingpdf.com。
- SSO(LDAP / OAuth2)的具体配置 —— 见 `app/` 下的 config 子目录和官方文档。
- 桌面客户端(Electron 打包 + JLink + signing)的细节 —— 见 `WINDOWS_SIGNING.md` 和 `SHARED_SIGNING.md`。
- AI Engine 的 agent 设计细节(目前 engine 还是早期,文档不完整,等 v1 稳定再深入)。
- 与 Foxit / Adobe Acrobat 的横向对比 —— 那是产品分析,不是架构分析。

## 一句话总结

Stirling-PDF 不只是"GitHub 上 stars 最多的 PDF 工具" —— 它是 **"如何把单 Java 后端 + 单前端 SPA 重构成 3 模块 Monorepo + 新增 Python AI Engine" 的真实工程范本**,值得任何"工具型产品想扩展成平台 + 接入 AI"的团队研究。