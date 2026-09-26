---
title: "google/skills 解读：Google 把产品知识做成了 Agent 技能库"
date: "2026-04-25T17:53:00+08:00"
lastmod: "2026-09-25T00:00:00+08:00"
slug: "google-agent-skills-guide"
github_repo: "google/skills"
source_key: "gh:google/skills"
description: "解读 Google 官方 Agent Skills 仓库：SKILL.md 格式、description 路由、渐进式加载、配方技能与 plugin 分发，以及它和 RAG、MCP 的本质区别。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Agent Skills", "Google Cloud", "Gemini"]
---

# google/skills 解读：Google 把产品知识做成了 Agent 技能库

2026 年 3 月底，Google 开源了 [google/skills](https://github.com/google/skills) 仓库（Apache 2.0），收录官方维护的 Agent Skills。截至 2026 年 9 月，仓库里有 151 个技能，覆盖 Google Cloud、Ads、Analytics、Firebase 等产品线，还在以每周数个的速度增加。技能遵循 [Agent Skills](https://agentskills.io/home) 开放标准——一个 `SKILL.md` 加若干参考文档，装进 Claude Code、Codex、Antigravity 这类 Agent 工具后，Agent 在遇到相关任务时自动取用。

它解决的不是"让 Agent 更聪明"。模型权重里的知识停在训练截止日，API 却每周都在变：google/skills 的 gemini-api 技能里有一句写给 Agent 的大写提醒——**"Your knowledge is outdated"**，紧接着列出当前该用的模型和已废弃的旧 SDK。知识跟着 git commit 走，而不是跟着模型版本走，这是它与 RAG、微调这些知识注入方案最本质的区别：改一处仓库，所有已安装的 Agent 同时更新。

## 仓库全景

先看地图。151 个技能按产品线和主题分组，README 按下面的类别维护索引：

| 类别 | 数量级 | 代表技能 |
|------|--------|---------|
| Getting started | 3 | onboarding、auth、foundation-builder 三个配方 |
| AI/ML | 约 22 | gemini-api、agent-platform 系列、Genkit 四语言 |
| Infrastructure | 约 35 | GKE 全家桶、Cloud Storage、Cloud Build |
| Databases and analytics | 约 15 | BigQuery 系列、AlloyDB、Spanner、Cloud SQL |
| Management tools | 约 15 | Cloud Logging/Monitoring 查询生成、成本分析 |
| Well-Architected Framework | 6 | 六大 pillar 各一个技能 |
| Security and identity | 约 15 | SecOps 系列、IAM 排障、SCC 查询 |
| Advertising | 14 | Google Ads API、Mobile Ads SDK 全流程 |
| Multi-product solutions | 13 | 跨产品的参考架构方案 |
| Analytics / Identity / 其他 | 若干 | Google Analytics API、DPoP、Firebase |

两个值得注意的结构特征。

第一，拆分粒度到"专项主题"。仅 GKE 一个产品线就有 30 多个技能：basics 之外，networking、upgrades、multitenancy、cost-optimization、每个 AI 故障排查场景都是独立技能。BigQuery 有 5 个，SecOps 拆成案例管理、triage、investigate、hunt、detection-engineering 五步。粒度细是刻意设计，后面讲路由机制时会看到原因。

第二，技能不是全部内容。仓库还有 `plugins/` 目录，把技能和 MCP server 打包成完整插件（如 google-cloud-developer），外加一份 `.claude-plugin/marketplace.json`，让 Claude Code 可以把它当插件市场订阅。`index.json` 则是全部技能的机器可读索引，每条含 name、description 和 entrypoint，供工具程序化消费。

## SKILL.md：一个技能的标准形态

每个技能的核心是一个 `SKILL.md`。以 gemini-api 技能的真实文件为例：

```yaml
---
name: gemini-api
metadata:
  category: AiAndMachineLearning
description: Use when the user asks about using Gemini in an enterprise
  environment or explicitly mentions Vertex AI, Google Cloud, or Agent
  Platform. Guides the usage of the Gemini API on Agent Platform with the
  Google Gen AI SDK. Covers SDK usage (Python, JS/TS, Go, Java, C#),
  capabilities like multimodal inputs, tools, media generation, caching,
  batch prediction, and Live API.
compatibility: Requires active Google Cloud credentials and Agent Platform API enabled.
---
```

字段不多。`name` 是唯一标识；`description` 承担路由（下文详述）；`compatibility` 声明前置条件；`metadata.category` 是仓库自己的分类（如 Containers、GettingStarted）。Agent Skills 标准还定义了可选的 `license` 字段，但这个仓库的 151 个技能都没有用它——许可证信息统一放在仓库根部的 LICENSE 文件（Apache 2.0）。

一个背景知识：技能里的 "Agent Platform" 全称 Gemini Enterprise Agent Platform，就是原来的 Vertex AI。gemini-api 技能开头专门用提示块交代这次更名，因为"大量网上资料还在用旧品牌"——这本身就是"模型知识过时"的一个活例子。

### description 即路由

Agent 决定是否加载一个技能，唯一依据是 `name` 和 `description`。所以 Google 对 description 的写法有固定套路：**触发条件打头，能力概述垫后**。gemini-api 的 description 以 "Use when the user asks about..." 开始，明确列出 Vertex AI、Google Cloud、Agent Platform 这些会触发的关键词。

更关键的是负向路由。gke-basics 的 description 后半段：

> Don't use for specialized GKE networking (use gke-networking), advanced security hardening (use gke-platform-security or gke-workload-security), or cluster upgrades (use gke-upgrades).

一个技能不仅声明自己管什么，还显式声明自己不管什么、该转给谁。Agent 同时看到几十个技能的 description 时，这种正负双向的边界描述比单纯罗列能力可靠得多——这也是 GKE 要拆成 30 多个技能的原因：粒度够细，每个技能的边界才划得清。

### Core Directives：写给 Agent 的硬约束

SKILL.md 正文开头通常有一节 Core Directives，全是硬性规则。gemini-api 的两条：

```markdown
## Core Directives

- **Unified SDK**: ALWAYS use the Gen AI SDK (`google-genai` for Python,
  `@google/genai` for JS/TS, `google.golang.org/genai` for Go,
  `com.google.genai:google-genai` for Java, `Google.GenAI` for C#).
- **Legacy SDKs**: DO NOT use `google-cloud-aiplatform`, `@google-cloud/vertexai`,
  or `google-generativeai`.
```

正文随后用警告块强化：三个旧 SDK 已废弃，"urgently" 迁移到新 SDK，并附迁移指南链接。传统文档只能"建议"开发者别用旧接口，技能则把禁令写进 Agent 的指令流——Agent 生成的每一行代码都会绕开废弃 API，不需要开发者自己知道这件事。

## 渐进式加载：上下文只装需要的那部分

Agent Skills 标准的加载机制是三层递进：

1. **常驻层**：所有已安装技能的 `name` + `description` 常驻上下文，成本很低；
2. **激活层**：用户请求命中某技能的 description 后，才加载该技能的 SKILL.md 正文；
3. **参考层**：SKILL.md 保持精炼，深度内容放 `references/` 目录，按需读取。

以 gke-basics 为例，它的 SKILL.md 只有几十行正文，末尾一个 Reference Directory 列出五个参考文档：

```text
skills/cloud/gke-basics/
├── SKILL.md
└── references/
    ├── core-concepts.md           # 架构、Autopilot vs Standard、安全模型
    ├── cli-reference.md           # 工具优先级（MCP vs gcloud vs kubectl）
    ├── client-library-usage.md    # Python/Go/Node.js/Java 客户端库
    ├── iac-usage.md               # Terraform 示例
    └── mcp-usage.md               # 23 个 GKE MCP 工具的用法
```

Agent 只在用户真的问到 Terraform 时才读 iac-usage.md，问到 MCP 工具时才读 mcp-usage.md。相比把一个产品的全部文档塞进上下文（或塞进 RAG 索引），这套机制的成本曲线平缓得多：上下文占用与任务相关度成正比，而不是与文档总量成正比。

跨主题的知识组织，仓库里有两种现成做法：主题边界清晰的，拆成独立技能靠 description 路由（GKE 系是代表）；主题内还需细分资料的，在 SKILL.md 里给出按主题分类的参考文档清单。bigquery-basics 走的是后一条路，八个参考文档覆盖核心概念、CLI、客户端库、MCP、IaC、IAM 安全、连续查询和变更历史。

## 一次真实任务如何流过技能系统

把机制串起来。假设开发者对装好技能的 Agent 说："在 GKE 上建一个私有集群，部署我的服务。"

**第一步，路由。** Agent 扫描常驻的 151 条 description，命中 gke-basics（触发条件：creating GKE clusters、configuring Workload Identity、deciding between Autopilot and Standard）。加载它的 SKILL.md。

**第二步，关键规则。** 正文第一节的选型规则写着：几乎一切工作负载默认 Autopilot，只有需要自定义 sysctl、节点 taint 或 hostPath 挂载时才用 Standard。用户没提特殊内核参数，Agent 直接走 Autopilot。

**第三步，Critical Gotchas。** 正文列出四条容易踩的坑，其中私有集群一条给出完整命令：

```bash
gcloud container clusters create-auto CLUSTER_NAME --region=REGION \
  --enable-private-nodes \
  --enable-private-endpoint \
  --enable-master-authorized-networks \
  --master-authorized-networks=CIDR_BLOCK
```

另外三条：Workload Identity 必须用 KSA 注解绑定 GSA，"绝不往 Pod 里挂 GCP 服务账号 JSON key"；Autopilot 的 CPU 请求按 250m 步进向上取整；`get-credentials` 必须显式指定 `--region` 或 `--zone`。这些全是文档里散落各处、新手必然漏掉的内容，技能把它们提到了 Agent 必读的位置。

**第四步，负向路由转介。** 部署过程涉及高级网络配置，超出 gke-basics 的边界——它的 description 早就写明这种情况转给 gke-networking。Agent 加载对应专项技能继续。

**第五步，按需取参考文档。** 开发者接着问"有没有 Terraform 写法"，Agent 这才打开 references/iac-usage.md。若开发者想用 MCP 工具操作集群，references/mcp-usage.md 里有 23 个结构化 GKE MCP 工具的说明。

一次请求，三层加载各用了一次，两个技能接力，没有一行与任务无关的内容进入上下文。

## 配方技能：把流程和交互习惯一起固化

三个 Getting started 配方——onboarding（首次使用 Google Cloud）、auth（认证配置）、foundation-builder（项目基础设施搭建）——封的是多步骤流程。以 onboarding 为例，它覆盖账号验证、认证会话、项目选择、计费关联的完整链路，但真正有观察价值的是它给 Agent 立的交互规矩：

- **先查再改**：执行任何项目或计费变更前，先静默完成状态审计；
- **单问题策略**：交互执行时每次只问一个操作参数，首轮不摆参数汇总表；
- **非交互输出**：所有变更命令追加 `--quiet`、`--format="json"`，保证输出确定且可机器解析，避免终端挂起。

这已经不是检查清单，而是把有经验的 SRE 的谨慎习惯写成了 Agent 的行为协议。

Well-Architected Framework 系列则是另一个极方向：六大 pillar（Security、Reliability、Cost Optimization、Operational Excellence、Performance Optimization、Sustainability）各一个技能，把 Google 官方架构框架变成 Agent 可引用的评审依据。让 Agent 审查你的 Terraform 时，它有整套 WAF 标准可以对照。

## Gemini API 技能实战

gemini-api 在 README 的 AI/ML 组里排第一位，内容组织也最能看出这个技能库的写法风格。

### 模型推荐：直接告诉 Agent 该用什么

技能维护着当前模型清单，并按场景给出明确指令：

| 场景 | 模型 | 备注 |
|------|------|------|
| 快速、均衡、多模态（默认首选） | `gemini-3.8-flash` | 1M token 上下文 |
| 复杂推理、编码、研究 | `gemini-3.1-pro-preview` | 取代 gemini-3-pro-preview |
| 高频轻量任务 | `gemini-3.5-flash-lite` | |
| 图像生成与编辑 | `gemini-3-pro-image`（Nano Banana Pro）等 | 另有中/轻量档 |
| Live 实时音视频 | `gemini-live-2.5-flash-native-audio` | |

`gemini-3.7-flash`、`gemini-2.5` 系列被标为"仅在用户明确要求时使用"；`gemini-2.0-*`、`gemini-1.5-*`、`gemini-1.0-*`、`gemini-pro` 则是废弃名单。模型更迭不再依赖 Agent 的训练数据，仓库更新一次即可。

### 认证配置

技能要求优先用环境变量而非硬编码参数，客户端无参初始化即可自动读取。两条路径：

**应用默认凭证（ADC）**——生产环境标准方式：

```bash
export GOOGLE_CLOUD_PROJECT='your-project-id'
export GOOGLE_CLOUD_LOCATION='global'
export GOOGLE_GENAI_USE_ENTERPRISE=true
```

`GOOGLE_CLOUD_LOCATION` 默认 `global`，自动路由到有可用容量的区域；用户指定区域（如 `us-central1`）时才改成具体值。

**API Key（Express Mode）**——快速试用：

```bash
export GOOGLE_API_KEY='your-api-key'
export GOOGLE_GENAI_USE_ENTERPRISE=true
```

### 快速开始

Python 与 TypeScript 各四行：

```python
from google import genai

client = genai.Client()
response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents="Explain quantum computing",
)
print(response.text)
```

```typescript
import { GoogleGenAI } from "@google/genai";
const ai = new GoogleGenAI({ enterprise: { project: "your-project-id", location: "global" } });
const response = await ai.models.generateContent({
    model: "gemini-3.8-flash",
    contents: "Explain quantum computing"
});
console.log(response.text);
```

五种语言的 SDK 包名在 Core Directives 里已锁定：Python `google-genai`、JS/TS `@google/genai`、Go `google.golang.org/genai`、Java `com.google.genai:google-genai`、C# `Google.GenAI`。技能正文对 Java 还给了 Maven 和 Gradle 的完整配置片段。

## 安装与分发

技能库的安装有两条路。

**按技能安装**，走 skills.sh 工具：

```bash
npx skills add google/skills
```

命令会列出仓库全部技能供交互勾选，装完即可被支持 Agent Skills 标准的工具识别。不建议无脑全装——151 个技能的 description 常驻上下文，按技术栈挑相关产品线的技能才是合理用法。

**按插件安装**，走 plugin 机制。仓库通过 marketplace.json 对外提供插件订阅，三个主流 Agent 工具各有姿势：

| Agent 工具 | 安装方式 |
|-----------|---------|
| Claude Code | `claude plugin marketplace add google/skills`，然后 `claude plugin install <plugin>@google-plugins` |
| Codex | `codex plugin marketplace add google/skills`，从 /plugins 浏览器安装 |
| Antigravity CLI | `agy plugin install https://github.com/google/skills/<plugin-path>` |

插件比技能多一层：除了 SKILL.md，还捆绑 MCP server 配置。plugins/cloud/google-cloud-developer 就是一个技能加工具的完整包。

Google 各产品团队还在维护仓库之外的技能库——[android/skills](https://github.com/android/skills)、[dart-lang/skills](https://github.com/dart-lang/skills)、Flutter、Firestore、Google Maps Platform 各有官方仓库，README 里统一收录了链接。Agent Skills 标准正在变成 Google 系产品知识分发的默认格式。

## 与 MCP 的关系：知识层与工具层

先给没接触过 MCP 的读者一句铺垫：MCP（Model Context Protocol，模型上下文协议）是让模型调用外部工具的标准协议——工具由 server 进程提供，模型在运行时决定调哪个。Agent Skills 和它经常被放在一起比，但两者不在同一层：

| 维度 | Agent Skills | MCP |
|------|-------------|-----|
| 定位 | 知识与工作流的封装 | 工具与资源的调用协议 |
| 触发方式 | description 匹配，激活时机由 Agent 判断 | 运行时函数调用，由模型决定 |
| 内容形态 | 指令、规则、代码示例、参考文档 | tool schema 与 server 进程 |
| 更新方式 | 仓库同步（git pull / 重装） | server 连接时动态发现 |

这个仓库自己的做法最能说明两者如何配合：bigquery-basics 和 gke-basics 各带一个 `references/mcp-usage.md`，ads 类别还有专门的 google-ads-api-mcp-setup 技能教你怎么装 Google Ads 的 MCP server。也就是说，**技能负责"什么时候用 MCP、怎么用好"，MCP server 负责真正执行**。知识层编排工具层，而不是互相替代。

## 采用建议

谁该现在就装：在 Claude Code、Codex 或 Antigravity 里做 Google Cloud 开发的团队，几乎无需犹豫——它解决的正是 Agent 写 GCP 代码时用过时 API、漏关键配置的问题。从三个 Getting started 配方加你所用产品的 basics 技能装起，够用再加。

谁可以观望：技术栈不在 Google 系的团队。这份仓库帮不上忙，但它的写法值得借鉴——如果你要为自己的产品写 Agent Skills，google/skills 是目前规模最大的官方参考实现，有三点最值得抄：

1. **description 写正负两个方向**：声明管什么，也声明不管什么、转给谁。路由质量取决于此。
2. **专项主题拆独立技能**，而不是把一个产品的所有知识塞进一个 SKILL.md。边界清晰，路由才准。
3. **把废弃 API 和模型写成 Core Directives 禁令**，让 Agent 生成代码的第一时间绕开坑，而不是靠开发者记忆。

一个提醒：技能内容本身有时效性。模型推荐、SDK 禁令都会随仓库更新而变化，把"升级技能"纳入日常维护（重跑一次安装命令即可），否则装来的知识同样会过时——只是比模型权重里的知识过期慢得多。

## 常见问题

**装 151 个技能会不会撑爆上下文？**
常驻上下文的只有每个技能的 name 和 description，SKILL.md 正文在命中后才加载，references/ 再晚一层。但 151 条 description 的常驻开销也不小，值得按技术栈挑产品线安装，而不是全量塞入。

**和把官方文档做成 RAG 有什么区别？**
RAG 检索的是文档原文，质量取决于检索器和文档本身；技能是产品团队手工整理的指令，明确到"用哪个 SDK、禁用哪个 API、什么情况转给哪个技能"，而且更新路径是 git——两个方案不互斥，但可靠性来源不同。

**模型推荐过时了怎么办？**
仓库在持续更新，gemini-api 里的模型清单就是随版本演进改出来的。重跑一次安装命令即可把技能升级到最新版。这正是这套机制的设计意图：知识过期时改仓库，而不是等模型重新训练。

**非 Google 技术栈能用同一套标准吗？**
能。Agent Skills 是开放标准，Android、Dart、Flutter、Google Maps Platform 等已有各自的官方技能库；为自己的产品写技能时，google/skills 是目前最好的参考实现。

## 结语

google/skills 的意义不在单个技能多精巧，而在它验证了一条知识分发路径：厂商把"当前正确的做法"写成 Agent 可执行、可审计、随仓库版本化的指令，绕开了模型训练周期的滞后。文档仍然在官网，但 Agent 消费的版本是仓库里这些 SKILL.md——更短、更硬、带着明确的禁令和路由。对人类读者来说还有个副产品：想在几分钟内搞清"Google 现在推荐怎么做 X"，读对应技能的 SKILL.md 往往比翻官网文档更快，因为里面没有历史包袱，只有当前答案。

## 相关资源

- GitHub 仓库：[google/skills](https://github.com/google/skills)
- Agent Skills 开放标准：[agentskills.io](https://agentskills.io/home)
- 安装命令：`npx skills add google/skills`
- 机器可读索引：仓库根目录 `index.json`
