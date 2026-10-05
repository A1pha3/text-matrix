---
title: "n8n：开源工作流自动化平台指南"
date: "2026-04-06T22:16:00+08:00"
slug: "n8n-workflow-automation-guide"
github_repo: "n8n-io/n8n"
source_key: "gh:n8n-io/n8n"
description: "n8n 的真正差异化不在集成数量，而在代码可扩展、自托管、AI LangChain 原生三者结合。本文从系统地图、任务流案例、与 Zapier/Make 的工程取舍、自托管部署、企业级功能到采用顺序，给出一份工程视角的落地指南。"
draft: false
categories: ["技术笔记"]
tags: ["n8n", "工作流自动化", "AI Agent", "LangChain", "开源"]
---

## 目录

- [学习目标](#学习目标)
- [n8n 在企业场景里靠什么站住脚](#n8n-在企业场景里靠什么站住脚)
- [n8n 的系统地图](#n8n-的系统地图)
- [与 Zapier、Make 的工程取舍](#与-zapiermake-的工程取舍)
- [快速上手：从 npx 到 Docker](#快速上手从-npx-到-docker)
- [工作流的核心抽象](#工作流的核心抽象)
- [一次 AI Agent 工作流的完整路径](#一次-ai-agent-工作流的完整路径)
- [集成背后的工程取舍](#集成背后的工程取舍)
- [自托管部署的真实考量](#自托管部署的真实考量)
- [企业级功能：什么时候需要](#企业级功能什么时候需要)
- [自定义节点开发：何时该写、何时不该写](#自定义节点开发何时该写何时不该写)
- [实战场景与适用边界](#实战场景与适用边界)
- [排查与运维](#排查与运维)
- [采用顺序与决策建议](#采用顺序与决策建议)
- [练习与自测](#练习与自测)
- [进阶路径](#进阶路径)

## 学习目标

读完本文后，你应当能够：

1. 说清 n8n 与 Zapier、Make 在数据流向、代码扩展、AI 集成上的三处工程差异，并据此判断自己的场景该选哪一类平台。
2. 画出 n8n 的五层系统地图（触发器、节点、凭证、执行引擎、持久化），解释 item 数组模型为什么是批量语义的默认行为。
3. 用 Docker 单机部署跑通一个非关键工作流，正确配置 `WEBHOOK_URL`、`N8N_ENCRYPTION_KEY` 和 HTTPS，并避开三个常见踩坑点。
4. 判断什么场景该用原生集成节点、什么场景该用 HTTP Request、什么场景才值得投入写自定义节点，并给出采用顺序。
5. 为 AI Agent 工作流设计显式的错误处理与超时策略，避免工具失败导致 LLM 幻觉或 Webhook 超时。

阅读建议：先看「n8n 的系统地图」建立整体认知，再按「快速上手」跑通一个 Docker 部署，最后根据「采用顺序与决策建议」对照自己的场景取舍。已经熟悉 n8n 的读者可以直接跳到「排查与运维」和「进阶路径」。



---

## n8n 在企业场景里靠什么站住脚

把 n8n 放到 Zapier、Make（原 Integromat）旁边比较时，集成数量并不构成护城河。n8n 官方维护 400+ 核心节点，集成中心（含社区节点）目前收录超过 2000 项，但 Zapier 的应用目录已经超过 1 万，Make 的可视化编排也更顺。比数量比不过。n8n 在企业场景里能站住脚，靠的是代码扩展、自托管、AI LangChain 原生集成这三者同时具备。

这三者组合起来，直接影响采购决策：当工作流需要处理客户数据、内部知识库或受合规约束的凭证时，Zapier 和 Make 的云端模型会让数据必须经过第三方 SaaS，而 n8n 自托管可以把数据流限制在企业网络内；工作流逻辑复杂到无代码表达式无法表达时，n8n 的 Code 节点允许直接写 JavaScript 或 Python，自托管还能按文档启用额外的 npm 模块；而工作流的核心是 LLM 调用而非传统 API 编排时，n8n 内置的 LangChain 节点把 Agent、Tool、Memory、Vector Store 做成了一等公民，而不是通过 HTTP Request 节点拼装。

代价是运维投入：n8n 自托管意味着要自己管 Docker、PostgreSQL、Redis、备份和升级。Sustainable Use License 也不是纯 OSS——它允许内部和商业使用，但禁止把 n8n 本身打包成 SaaS 转售，这与 MIT/Apache 的许可范围有明确差异，采购前需要法务确认。

适合正在评估工作流平台的工程师和架构师。



---

## n8n 的系统地图

n8n 的核心可以拆成五层，理解这五层的边界，比记集成数量更有用：

```text
┌─────────────────────────────────────────────────────────┐
│  触发器层  Webhook / Schedule / Email / Manual / Form   │
│           / 第三方应用事件（GitHub、Slack、Shopify…）   │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  节点层    集成节点（OpenAI、PostgreSQL、Slack…）        │
│           Code 节点（JS / Python + 可选外部模块）          │
│           AI 节点（LangChain Agent / Tool / Memory）     │
│           逻辑节点（IF / Switch / Merge / Loop）         │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  凭证层    独立于节点存储，加密保存                      │
│           支持 OAuth2、API Key、Basic Auth、JWT 等       │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  执行引擎  编排节点顺序、传递 item 数组、错误重试        │
│           支持子工作流、并发控制、超时                   │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  持久化层  工作流定义、执行历史、凭证密文                │
│           SQLite（默认）/ PostgreSQL                     │
└─────────────────────────────────────────────────────────┘
```

**凭证独立于节点存储**。一个 Slack 凭证可以被任意多个 Slack 节点引用，轮换 Token 时只改一处。这和直接在节点里写 API Key 的做法相比，安全性高一个量级——后者在节点配置里到处散落密钥，轮换一次得改几十处。

**Code 节点补的是集成节点的空白**。集成节点处理"调用某个 API 的标准姿势"，Code 节点处理"集成节点覆盖不到的转换逻辑"。能用集成节点就别写 Code，因为集成节点的字段映射、分页、重试已经处理好，自己写 Code 等于把这些都重造一遍。

**AI 节点和普通节点走的是同一套执行引擎**。LangChain Agent 节点是一个会多次回调工具节点的特殊节点，它的执行历史、错误处理、数据流转和普通节点一致，因此可以用同一套调试和监控手段管理 AI 工作流。

**触发器决定工作流的执行模型**。Webhook 触发器默认是异步的：Respond 选项的默认值是 Immediately，收到请求立即返回 "Workflow got started"，工作流在后台继续跑；把 Respond 改成 When Last Node Finishes，或者接一个 Respond to Webhook 节点，才变成调用方等待结果的同步模式。Schedule 触发器是异步批处理；第三方应用事件触发器（如 GitHub Webhook、Slack Event）依赖 n8n 实例的公网可达性。选错触发器类型是新手最常见的坑。



---

## 与 Zapier、Make 的工程取舍

把三个平台放在一起时，差异不在功能数量，而在数据流向和扩展模型：

| 维度 | n8n | Zapier | Make |
|------|-----|--------|------|
| 部署模型 | 自托管或 n8n Cloud | 仅云端 | 仅云端 |
| 数据流向 | 可限制在企业网络内 | 必须经过 Zapier 云 | 必须经过 Make 云 |
| 代码扩展 | Code 节点支持 JS/Python + npm | 仅表达式 | 有限的表达式和模块 |
| AI 集成 | LangChain 节点原生 | 通过 OpenAI 应用 | 通过 HTTP 和模块组合 |
| 计费模型 | 自托管免费 / Cloud 按执行 | 按任务数 | 按操作数 |
| 凭证管理 | 独立加密存储 | 平台托管 | 平台托管 |
| 运维成本 | 自托管需投入 | 零运维 | 零运维 |

Zapier 和 Make 的零运维对小团队是实打实的好处——如果工作流只有十几条、数据不敏感、预算允许按量付费，云端方案的上线速度远快于自托管。n8n 的优势在另一端：工作流数量上百、数据受合规约束、需要写复杂转换逻辑、需要把 LLM 编排进流程——这些场景下自托管的控制权和代码扩展能力才用得上。

计费模型也值得拆开看。Zapier 按任务数收费，Make 按操作数收费，两者都会在工作流规模放大时出现成本不可控。n8n 自托管的成本是固定的服务器费用，但需要把运维人力算进去。一个常见的误判是只看 SaaS 的标价，忽略自托管的隐性人力成本。



---

## 快速上手：从 npx 到 Docker

n8n 的安装方式按"测试 → 单机生产 → 集群"递进，选哪种取决于用途而非偏好。

### 测试用途：npx 一行启动

```bash
# 需要 Node.js
npx n8n
```

适合本地试一下编辑器和节点配置，数据存在 `~/.n8n`，不要用于生产。

### 单机生产：Docker

```bash
# 创建持久化卷
docker volume create n8n_data

# 启动容器
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  docker.n8n.io/n8nio/n8n

# 访问编辑器
# http://localhost:5678
```

`-it --rm` 适合临时跑，生产环境改成 `-d` 并配合 `restart: unless-stopped`。`n8n_data` 卷里存着工作流定义、执行历史和加密凭证，丢了不可恢复，必须备份。

### 单机生产：Docker Compose

```yaml
services:
  n8n:
    image: docker.n8n.io/n8nio/n8n
    ports:
      - "5678:5678"
    volumes:
      - n8n_data:/home/node/.n8n
    environment:
      - N8N_SECURE_COOKIE=false
    restart: unless-stopped
volumes:
  n8n_data:
```

`N8N_SECURE_COOKIE=false` 只适合本地调试，生产环境必须配合 HTTPS 改成 `true`。

### 从源码构建

```bash
# 克隆仓库
git clone https://github.com/n8n-io/n8n.git
cd n8n

# 安装依赖
pnpm install

# 构建
pnpm build

# 启动
pnpm start
```

只有需要改 n8n 本身或调试自定义节点时才走这条路。日常使用没必要从源码构建。



---

## 工作流的核心抽象

### 节点（Node）

节点是工作流的最小执行单元。每个节点接收一个 item 数组，处理后输出一个 item 数组。item 是 n8n 的数据载体，结构是 `{ json: {...}, binary?: {...} }`。理解 item 数组这个模型很关键——它决定了节点之间如何传递数据，也决定了批量处理时的行为。

n8n 选择 item 数组而不是单个对象，是因为工作流自动化的典型场景就是批量处理：一次 Webhook 可能带 10 条订单，一次数据库查询可能返回 100 行。如果节点只处理单个对象，用户就得自己在每个节点里写循环逻辑。item 数组让批量语义成为默认行为，节点内部不用写 for 循环。

一个常见误区是把节点当成函数。节点更接近 map 操作：如果输入是 10 个 item，节点会对每个 item 执行一次，输出 10 个 item。Code 节点里写 `return [transformed]` 只会输出 1 个 item，要保留批量语义应该写 `return items.map(...)`。

### 触发器（Trigger）

触发器决定工作流何时启动。几类触发器的执行语义不同：

- **Webhook**：默认异步，收到请求立即返回；配置 Respond 模式或接 Respond to Webhook 节点后可同步等待。适合做 API 代理或即时响应。
- **Schedule**：异步，按 cron 表达式触发。适合批处理。
- **Email**：异步，IMAP 轮询新邮件。适合邮件驱动的流程。
- **Manual**：只在编辑器里手动点击执行。用于调试。
- **Form**：n8n 自带的表单页面提交触发。适合内部工具。
- **第三方应用事件**：依赖 Webhook URL 公网可达，配置时要把 `WEBHOOK_URL` 设对。

`WEBHOOK_URL` 配错是第三方触发器不工作的最常见原因。n8n 在向 GitHub、Slack 等平台注册 Webhook 时会用这个值，如果设成 `localhost`，平台回调时根本到不了你的实例。

### 凭证（Credential）

凭证独立于节点存储，加密保存在数据库里。解耦带来的直接收益是复用：同一个凭证可以被多个节点复用（一个 Slack Token 能被几十个 Slack 节点引用），轮换凭证时只改一处，凭证的加密和权限管理可以单独做，不和具体节点的配置混在一起。

加密密钥由 `N8N_ENCRYPTION_KEY` 控制，默认自动生成并存在 `~/.n8n/config`。生产环境必须显式设置这个环境变量，否则密钥丢失后所有凭证不可解密。

凭证支持 OAuth2、API Key、Basic Auth、JWT 等常见类型。OAuth2 凭证会自动处理 Token 刷新，不需要在节点里手动管理过期。



---

## 一次 AI Agent 工作流的完整路径

分层图是静态的，光看图记不住执行引擎怎么工作。用一个 AI 客服工作流把节点、触发器、凭证、执行引擎串起来，看一次任务实际怎么流过 n8n。

### 场景

客户在网站提交问题，n8n 接收后用 LLM 判断是否需要人工，需要则创建工单并通知 Slack，不需要则直接回复。

### 工作流结构

```text
[Webhook 触发]
    │  接收 POST /ask，body 含 question 和 user_id
    ▼
[LangChain Agent 节点]
    │  系统提示词：判断问题类型，决定调用哪些工具
    │  绑定工具：知识库检索、工单查询、工单创建
    ▼
[工具节点分支]
    ├── [Vector Store 检索]
    │     从 Pinecone 检索相关文档片段
    ├── [PostgreSQL 工单查询]
    │     查询该用户最近的工单状态
    └── [PostgreSQL 工单创建]
          当 Agent 判断需要人工时调用
    ▼
[LangChain Agent 节点（继续）]
    │  汇总工具返回结果，生成最终回复
    ▼
[IF 节点]
    │  判断回复中是否包含 "需要人工" 标记
    ├── 是 → [Slack 通知] → [Respond to Webhook 返回工单号]
    └── 否 → [Respond to Webhook 返回回复]
```

### 一次执行的内部流转

1. **Webhook 触发器**收到 HTTP 请求，Respond 模式配置为 Respond to Webhook 节点（调用方同步等待结果），把 `question` 和 `user_id` 包成 item 传给下游。
2. **LangChain Agent 节点**接收 item，把 `question` 作为用户消息发给 LLM。LLM 根据 system prompt 决定调用工具。
3. 假设 LLM 决定先检索知识库：Agent 节点暂停，调用 **Vector Store 检索**节点，传入查询词。检索节点返回 top-3 文档片段给 Agent。
4. Agent 把片段塞进上下文，再次调用 LLM。LLM 判断信息不足，决定再查工单历史。Agent 调用 **PostgreSQL 工单查询**节点。
5. 工单查询节点用预存的 PostgreSQL 凭证连接数据库，执行参数化查询，返回该用户最近 3 条工单。
6. Agent 把所有上下文交给 LLM 生成最终回复。回复里包含 "需要人工：是" 标记。
7. **IF 节点**解析回复，走 "是" 分支。
8. **Slack 通知**节点用 Slack 凭证发消息到 `#support` 频道，附带问题、用户 ID、Agent 的分析。
9. **Respond to Webhook** 节点返回工单号给调用方。
10. 整个执行过程被写入执行历史，包含每个节点的输入输出、耗时、状态。

### 从这个案例能看到的几件事

**Agent 节点会多次回调工具节点**。Agent 节点在内部循环：调用工具 → 拿到结果 → 再问 LLM → 决定是否继续调用。执行历史里会看到工具节点被多次执行，这是正常行为，不是重试。

凭证在多个节点间共享是这个工作流的关键设计。PostgreSQL 凭证被工单查询和工单创建两个节点引用，Slack 凭证被通知节点引用。轮换数据库密码时只改一处，所有引用该凭证的节点自动生效。

**错误处理需要显式设计**。如果 Vector Store 检索失败，Agent 会拿到错误信息继续推理，可能产生幻觉。生产环境应该在工具节点里加 try-catch，返回结构化错误给 Agent，而不是让 LLM 自己猜。

还有一点容易忽略：同步 Webhook 的耗时受调用方超时约束。这个案例用了 Respond to Webhook 节点，调用方要一直等到工作流结束——LLM 多轮推理加工具调用很容易超过 HTTP 客户端常见的 30 秒超时，表现是调用方报错、n8n 执行历史里却显示成功。长任务应该改成异步——Webhook 用默认的立即响应先返回 "处理中"，后台工作流完成后通过另一个 Webhook 或 Slack 通知。



---

## 集成背后的工程取舍

n8n 的集成不是单一形态，理解三种集成方式的差异，比数集成数量重要。

**原生集成节点**：n8n 官方维护的节点，如 OpenAI、Slack、PostgreSQL、GitHub。字段映射、分页、错误处理已经处理好，能用就用。

**HTTP Request 节点**：通用 HTTP 客户端，可以调用任何 REST API。适合原生节点没覆盖的服务，或需要精细控制请求的场景。配合通用凭证类型（Generic Credential Type）下的 OAuth2 API 凭证，可以给任意 API 加 OAuth2 支持。

**自定义节点**：用 TypeScript 写的节点包，发布到 npm。适合内部系统或高频使用的第三方服务。开发成本高于前两者，但复用性最好。

### OpenAI 集成示例

OpenAI 节点发一条聊天消息的配置路径：Resource 选 `Text`，Operation 选消息类操作，Model 下拉会加载凭证账号可用的模型（官方文档的建议是低成本高速用 `gpt-4o-mini`，更高质量用 `gpt-4o`），在 Messages 里配置 role 和 content——一条 System 消息定行为，一条 User 消息放输入。随机性用 Options 里的 Temperature 控制，客服分流这类确定性场景压到 0.3 以下更稳，且 Temperature 和 Top P 只调其中一个。

注意 n8n 版本之间这个节点的操作名称和参数有过调整（1.117.0 引入 V2 后，Chat Completions API 和 Responses API 分成了两个操作），部署时以编辑器里的实际字段为准。

### Slack 集成示例

Slack 节点发一条频道消息：Resource 选 `Message`，Operation 选 `Send`，Send Message To 选 `Channel` 并用 ID、名称或 URL 指定目标频道，Message Text 里写正文，可以内嵌表达式：

```text
工作流执行完成！
状态：{{ $json.status }}
时间：{{ $now }}
```

`{{ $now }}` 是 n8n 的表达式语法，运行时求值，返回 Luxon 的 DateTime 对象。表达式可以引用上游节点的输出，比如 `{{ $json["workflow_name"] }}`。

### 数据库集成示例

PostgreSQL 节点执行一条参数化查询：Operation 选 `Execute Query`，Query 里写 SQL，用 `$1`、`$2` 占位：

```sql
SELECT * FROM users WHERE created_at > $1;
```

参数值放在 Options → Query Parameters 里（逗号分隔），也可以用表达式从上游 item 取：

```text
{{ $json.since }}
```

参数化查询是硬性要求。直接拼字符串会导致 SQL 注入；PostgreSQL 节点对查询参数做了消毒处理，配合 `$1`、`$2` 占位符使用就能挡住注入。

### 集成分类速查

| 分类 | 代表集成 |
|------|---------|
| AI & ML | OpenAI、Anthropic Claude、LangChain、Hugging Face |
| 通信 | Slack、Discord、Teams、Email |
| 云服务 | AWS、Google Cloud、Azure |
| 数据库 | PostgreSQL、MySQL、MongoDB、Redis |
| CRM | Salesforce、HubSpot |
| 电商 | Shopify、WooCommerce、Stripe |
| 社交 | Twitter/X、LinkedIn、Instagram |
| 开发 | GitHub、GitLab、Jira |

这个表只用于快速定位。具体某个服务是否支持某个操作，查 [n8n 集成中心](https://n8n.io/integrations) 比记表格靠谱。



---

## 自托管部署的真实考量

### 为什么自托管对企业重要

自托管把数据流限制在企业控制的边界内。Zapier 和 Make 的工作流执行时，数据会经过它们的云端服务器——这对个人或小团队无伤大雅，但对处理客户 PII、内部财务数据、医疗记录的企业，可能直接违反 GDPR、HIPAA 或行业合规要求。n8n 自托管后，数据流可以完全在内网完成，只有需要调用外部 API 时才出境。

数据流收窄之后，凭证也跟着落到企业自己的加密存储里——云端方案下所有 API Key、OAuth Token 都存在 SaaS 平台侧，平台被攻破意味着所有凭证泄露，自托管把攻击面收窄到企业自己的基础设施。

成本方面：SaaS 按执行或操作收费，工作流规模放大后成本会非线性增长，自托管的成本是固定的服务器和运维人力，规模越大单位成本越低。

但运维投入省不掉：备份、升级、监控、安全补丁都要自己做。如果团队没有专职运维，自托管的隐性成本可能超过 SaaS 的显性成本。

### Docker 部署

**基础部署**：

```bash
docker run -d \
  --name n8n \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  -e N8N_HOST=your-domain.com \
  -e N8N_PROTOCOL=https \
  -e WEBHOOK_URL=https://your-domain.com/ \
  docker.n8n.io/n8nio/n8n
```

`WEBHOOK_URL` 必须设成外部可访问的地址，否则第三方 Webhook 注册会失败。

**使用代理**：

```bash
docker run -d \
  --name n8n \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  -e HTTP_PROXY=http://proxy:8080 \
  -e HTTPS_PROXY=http://proxy:8080 \
  docker.n8n.io/n8nio/n8n
```

企业内网通常需要走代理才能访问外部 API。注意 n8n 调用 OpenAI、Slack 等 SaaS 时会走这个代理，但调用内网服务时不应该走——需要配合 `NO_PROXY` 环境变量排除内网域名。

### 关键环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `N8N_HOST` | 主机名 | localhost |
| `N8N_PORT` | 端口 | 5678 |
| `N8N_PROTOCOL` | 协议 | http |
| `WEBHOOK_URL` | Webhook 基础 URL | - |
| `N8N_ENCRYPTION_KEY` | 加密密钥 | 自动生成 |
| `EXECUTIONS_DATA_SAVE_ON_ERROR` | 错误时保存数据 | all |
| `EXECUTIONS_DATA_SAVE_ON_SUCCESS` | 成功时保存数据 | all |
| `EXECUTIONS_DATA_PRUNE` | 自动清理旧执行历史 | true |
| `EXECUTIONS_DATA_MAX_AGE` | 执行历史保留时长（小时） | 336 |
| `EXECUTIONS_DATA_PRUNE_MAX_COUNT` | 执行历史保留条数上限（0 为不限） | 10000 |
| `N8N_METRICS` | 暴露 Prometheus 指标端点 | false |

`N8N_ENCRYPTION_KEY` 在生产环境必须显式设置并妥善保管。丢失后所有凭证不可解密，等于工作流全部失效。执行历史的自动清理默认开启（保留 336 小时、上限 10000 条），高频工作流要留意两个相反的问题：清理跟不上写入时数据库持续膨胀；留存窗口太短时又满足不了审计要求。按需调 `EXECUTIONS_DATA_MAX_AGE` 或 `EXECUTIONS_DATA_PRUNE_MAX_COUNT`；真正用不到执行数据的高频工作流，把 `EXECUTIONS_DATA_SAVE_ON_SUCCESS` 改成 `none` 最直接。

Code 节点默认禁止导入第三方模块。自托管需要跑外部 npm 包时，用 `NODE_FUNCTION_ALLOW_EXTERNAL` 按包名放行（内置模块用 `NODE_FUNCTION_ALLOW_BUILTIN`），逗号分隔，`*` 表示全部放行。放行等于把任意代码执行能力交给能编辑工作流的用户，范围越小越好。

### 数据持久化

```bash
# 创建命名卷
docker volume create n8n_data

# 查看卷位置
docker volume inspect n8n_data
```

默认用 SQLite，数据存在 `n8n_data` 卷里。生产环境建议改用 PostgreSQL，性能和并发能力都更好——这是 n8n 仅支持的两个数据库，MySQL 支持已随 1.0 弃用。切换数据库时数据不会自动迁移，需要导出工作流和凭证后在新数据库重新导入，具体步骤见[排查与运维](#排查与运维)的 Q3。

### HTTPS 配置

生产环境必须 HTTPS。用 Traefik 做反向代理和自动证书：

```yaml
# docker-compose.yml
services:
  traefik:
    image: traefik:v3
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./traefik.yml:/traefik.yml
      - ./certs:/certs

  n8n:
    image: docker.n8n.io/n8nio/n8n
    environment:
      - N8N_HOST=n8n.example.com
      - N8N_PROTOCOL=https
      - WEBHOOK_URL=https://n8n.example.com/
    labels:
      - traefik.enable=true
      - traefik.http.routers.n8n.rule=Host(`n8n.example.com`)
      - traefik.http.routers.n8n.tls.certresolver=letsencrypt
```

`N8N_SECURE_COOKIE` 在 HTTPS 下必须设回 `true`，否则 Cookie 可能在中间节点被截获。



---

## 企业级功能：什么时候需要

n8n 的企业级功能按需开启，单团队用不上就别开。注意这一节的功能多数是付费计划能力，规划预算前先对照官方定价页：项目权限（RBAC）从低阶付费计划起步，SSO 和 LDAP 需要自托管 Business 及以上，审计日志、外部密钥库、多 main 高可用是 Enterprise。

### 权限管理

n8n 的角色分两层。实例层（Instance roles）管整个 n8n：

| 角色 | 权限 |
|------|------|
| Owner | 完全控制，每个实例唯一 |
| Admin | 管理用户和实例设置 |
| Member | 创建并编辑自己的工作流 |

项目层（Project roles）管单个项目内的工作流和凭证：

| 角色 | 权限 |
|------|------|
| Project Admin | 管理项目、成员和工作流 |
| Project Editor | 编辑项目内工作流 |
| Project Viewer | 只读 |

实例层角色免费版就有；项目隔离（Projects）是付费功能，不同计划的共享项目数不同。角色系统在多团队共用一个 n8n 实例时才有价值，单团队使用时全员 Member/Project Admin 反而更顺手，权限分层带来的管理成本可能超过收益。

**项目隔离**：按项目分组工作流和凭证，独立权限控制。适合多业务线共用平台的中大型组织。

### SSO 配置

SSO 支持 SAML 2.0 与 OIDC（OpenID Connect），另有独立的 LDAP/Active Directory 登录。计划归属：自托管需要 Business 及以上，n8n Cloud 只有 Enterprise 计划提供。企业已有身份提供商时强制走 SSO，把认证收口到一处，避免本地账号泄露后在多用户间横向移动。

SSO 默认在编辑器的 **Settings → SSO** 界面配置：选择协议、填入 IdP 提供的元数据或发现端点、Client ID 与密码，保存后激活即可，不需要碰环境变量（操作者需要是实例 Owner 或 Admin）。只有当你想用基础设施即代码（IaC）自动批铺实例时，才需要把 SSO 交给环境变量管理——这是 n8n v2.18.0 才支持的能力，且必须先把主开关打开，否则对应变量会被忽略：

```yaml
# 环境变量（生产环境通过密钥管理服务注入，不要写进 docker-compose.yml）
N8N_SSO_MANAGED_BY_ENV=true
N8N_SSO_OIDC_LOGIN_ENABLED=true
N8N_SSO_OIDC_CLIENT_ID=your-client-id
N8N_SSO_OIDC_CLIENT_SECRET=your-client-secret
N8N_SSO_OIDC_DISCOVERY_ENDPOINT=https://your-idp.com/.well-known/openid-configuration
N8N_SSO_USER_ROLE_PROVISIONING=instance_role
```

开启 env 管理后，UI 里对应的 SSO 控件会变成只读，n8n 每次启动都用环境变量覆盖配置。走 SAML 时把 `N8N_SSO_OIDC_*` 换成 `N8N_SSO_SAML_LOGIN_ENABLED` 与 `N8N_SSO_SAML_METADATA_URL`（或以 `N8N_SSO_SAML_METADATA` 直接传 XML）。`N8N_SSO_OIDC_CLIENT_SECRET` 这类敏感值必须通过密钥管理服务注入，不要写进 docker-compose.yml 提交到 Git。SSO 相关环境变量名在不同 n8n 版本间有调整，部署前以 [n8n 官方环境变量文档](https://docs.n8n.io/deploy/host-n8n/configure-n8n/basic-configuration/use-environment-variables/) 为准。

### 空中隔离部署

n8n 支持 Air-Gapped 环境部署：无需互联网连接，完全离线运行，企业内部数据安全（自托管即可行，不需要额外 license）。代价是装不了社区节点、收不到版本更新，升级靠人工搬运镜像。适合金融、军工、能源等强隔离行业。

### 审计日志

用户操作记录、工作流执行历史、敏感操作告警（Enterprise 功能）。需要长期合规留存时，用 Log streaming（同为 Enterprise）把日志持续推送到 Datadog 这类外部系统，或导出到 SIEM（如 ELK、Splunk），n8n 自身的日志存储不适合长期留存。



---

## 自定义节点开发：何时该写、何时不该写

写自定义节点之前先问三个问题：

1. HTTP Request 节点能不能解决？能就别写。
2. 是不是高频复用的内部系统？是才值得写。
3. 团队有没有维护 npm 包的能力？没有就先用 HTTP Request 顶着。

自定义节点的好处是把内部系统的 API 调用标准化，让非开发同事也能在编辑器里拖拽使用。如果只是某个工作流用一次，HTTP Request 节点更合适。

### 创建自定义节点

官方脚手架是 `@n8n/node-cli`（工具名 `n8n-node`），开发环境要求 Node.js 22.22.0 以上：

```bash
# 交互式创建节点项目（推荐）
npm create @n8n/node@latest

# 或者直接用 CLI 建项目
npx @n8n/node-cli new n8n-nodes-my-app --template declarative/custom
```

模板有三类：`declarative/custom` 是 REST API 场景的声明式骨架（默认推荐），`declarative/github-issues` 是带凭证和资源划分的完整示例，`programmatic/example` 是程序化风格骨架（适合复杂逻辑）。

### 节点结构

```text
n8n-nodes-my-app/
├── nodes/
│   └── MyApp/
│       ├── MyApp.node.ts
│       └── myapp.svg
├── credentials/
│   └── MyAppApi.credentials.ts
├── package.json
└── tsconfig.json
```

凭证和节点分开存放是有意设计：一个凭证类型可以被多个节点复用，比如内部 API 网关的 Token 可能被十几个内部服务节点共用。

### 节点代码示例

官方脚手架默认生成声明式（declarative）风格——用路由描述 API 调用，代码量少，适合标准 REST 服务。需要自定义执行逻辑时用程序化（programmatic）风格，两种风格可以共存于同一个包。下面是程序化风格的骨架：

```typescript
import {
  IExecuteFunctions,
  INodeExecutionData,
  INodeType,
  INodeTypeDescription,
} from 'n8n-workflow';

export class MyCustomNode implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'My Custom Node',
    name: 'myCustomNode',
    icon: 'fa:rocket',
    group: ['transform'],
    version: 1,
    description: 'A custom node I built',
    defaults: {
      name: 'My Custom Node',
    },
    inputs: ['main'],
    outputs: ['main'],
    properties: [
      {
        displayName: 'API Key',
        name: 'apiKey',
        type: 'string',
        default: '',
      },
      {
        displayName: 'Operation',
        name: 'operation',
        type: 'options',
        options: [
          { name: 'Get', value: 'get' },
          { name: 'Post', value: 'post' },
        ],
        default: 'get',
      },
    ],
  };

  async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
    const items = this.getInputData();
    const returnData: INodeExecutionData[] = [];

    for (let i = 0; i < items.length; i++) {
      const apiKey = this.getNodeParameter('apiKey', i) as string;
      const operation = this.getNodeParameter('operation', i) as string;

      // 执行操作
      const result = { operation, timestamp: new Date().toISOString() };
      returnData.push({ json: result });
    }

    return [returnData];
  }
}
```

`execute` 方法里的 `for` 循环是 n8n 节点的标准模式：对每个输入 item 执行一次操作，保持批量语义。如果只处理第一个 item，会丢失批量数据。

### 发布节点

```bash
# 构建（脚手架内置 npm script，底层跑 n8n-node build）
npm run build

# 登录 npm
npm login

# 发布到 npm
npm publish --access public
```

脚手架生成的 `package.json` 已带 `n8n` 字段，通过 `credentials` 和 `nodes` 数组声明编译产物入口，n8n 靠它识别节点包——改包名时别动这个字段。内部节点可以发到私有 npm registry，不必公开；开发过程中在实例的 Settings → Community nodes 里用包名安装即可测试。



---

## 实战场景与适用边界

### AI 客服机器人

```text
[Webhook 触发] 
  → [LangChain Agent] 
    → [Tool: Slack] 
    → [Tool: 数据库查询]
```

适合：知识库相对稳定、问题类型可枚举的客服场景。

不适合：需要多轮深度对话、需要情感判断的高敏感场景——这类场景用专门的对话框架（如 Rasa）更合适，n8n 做后端编排。

### 数据同步管道

```text
[Schedule 触发]
  → [PostgreSQL 查询]
  → [数据转换]
  → [Elasticsearch 索引]
  → [发送 Slack 通知]
```

适合：定时全量或增量同步、ETL 轻量场景。

不适合：实时 CDC（变更数据捕获）、超大规模数据（千万级以上）——前者用 Debezium + Kafka，后者用 Spark 或 Flink。

### 社交媒体管理

```text
[RSS 触发]
  → [内容提取]
  → [AI 生成摘要]
  → [多平台发布]
    → Twitter
    → LinkedIn
    → Facebook
```

适合：内容运营团队的发布自动化。

不适合：需要严格审核流程的场景——AI 生成内容直接发布有合规风险，应该加人工审核节点。

### 电商订单处理

```text
[Shopify 新订单]
  → [验证库存]
  → [创建发货单]
  → [发送邮件通知]
  → [更新 CRM]
```

适合：中小电商的订单流转自动化。

不适合：高频交易、强一致性要求的场景——n8n 的工作流不是事务性的，中间节点失败不会自动回滚上游操作，需要显式设计补偿逻辑。



---

## 排查与运维

### 调试工作流

1. 用 Manual 触发器逐步测试，不要直接用 Webhook 触发器调试。
2. 在每个节点后加 Code 节点打印 `JSON.stringify($input.all(), null, 2)`，看实际数据结构。
3. 执行后在编辑器里点开任意节点，面板直接展示这一步的输入输出数据，比翻执行日志直观。
4. 执行历史里点开失败节点，看错误堆栈和当时的输入数据——大多数错误是数据结构不匹配，不是节点本身的问题。

### 处理大文件

- 用流式处理（Streaming），不要把整个文件读进内存。
- 给慢节点设超时：HTTP Request 节点在 Options 里配 Timeout；整个工作流的上限用 `EXECUTIONS_TIMEOUT` 控制（默认 -1 不限制），避免长任务无限占用执行引擎。
- 用 Loop Over Items 节点（旧名 SplitInBatches）分批处理，每批控制在几百条。

### 错误处理与重试

n8n 的错误处理有三种模式：

- **节点级重试**：在节点设置里开启 Retry On Fail，配置间隔和次数。适合网络抖动类错误。
- **错误工作流**：在工作流 Settings 里指定一个含 Error Trigger 节点的工作流，原工作流出错时自动触发，转发到告警。适合集中监控。
- **Try-Catch 模式**：用 `Execute Workflow` 节点调用子工作流，子工作流失败时走补偿逻辑。适合需要事务性的场景。

```javascript
// 错误告警工作流（第一个节点是 Error Trigger）
const execution = $json.execution;
const workflow = $json.workflow;

return [{
  json: {
    alert: 'Workflow Failed',
    workflow: workflow.name,
    failedNode: execution.lastNodeExecuted,
    error: execution.error.message,
    executionUrl: execution.url,
    time: new Date().toISOString()
  }
}];
```

Error Trigger 的输出结构是 `execution.error`（含 `message`、`stack`）、`execution.lastNodeExecuted` 和 `workflow.name`，告警消息里带上执行链接（`execution.url`），值班的人点开就能定位到失败节点。

### 常见问题速查

| 症状 | 排查方向 | 解决办法 |
|------|---------|---------|
| 第三方 Webhook 不触发 | `WEBHOOK_URL` 配成 `localhost` 或内网地址 | 改成外部可访问的 HTTPS 地址，重启 n8n |
| 凭证全部失效 | `N8N_ENCRYPTION_KEY` 丢失或被重置 | 从备份恢复原密钥；无法恢复则需重新录入所有凭证 |
| 执行历史暴涨 | 保存粒度全开，留存窗口又调得太长 | 调低 `EXECUTIONS_DATA_MAX_AGE` / `EXECUTIONS_DATA_PRUNE_MAX_COUNT`，高频流改 `SAVE_ON_SUCCESS=none` |
| 工作流执行到一半卡住 | 下游 HTTP 请求没设超时，长任务阻塞执行 | HTTP Request 节点 Options 里配 Timeout，或设 `EXECUTIONS_TIMEOUT`；长任务改异步子工作流 |
| Code 节点只输出 1 条 | 写了 `return [transformed]` 而非 `return items.map(...)` | 改成 map 写法保留批量语义 |
| 升级后工作流行为异常 | 用了 `latest` 标签，大版本有不兼容变更 | 锁定具体版本号，先在测试环境验证再上生产 |
| 多副本下 Webhook 重复执行 | Webhook 触发器未做幂等 | 在业务层用唯一 ID 去重，或用 `EXECUTIONS_MODE=queue` 配合 Redis 分发 |

### 进阶 Q&A

速查表覆盖的是单点症状。生产环境里更常见的是复合问题，挑四个展开说。

**Q1：工作流在生产环境偶发失败，但本地用 Manual 触发器跑完全正常，怎么定位？**

本地跑通不代表生产没问题，两者的差异通常在触发器和数据上。先按这个顺序排查：

1. 看执行历史里失败那次的输入数据。生产环境的真实数据往往比测试数据大几个量级，item 数组可能有几百上千条，某个字段的 null 或类型变化都会让节点炸掉。
2. 检查触发器的响应模式。配置成同步（When Last Node Finishes 或 Respond to Webhook）时，如果下游节点耗时超过调用方 HTTP 客户端的超时（常见 30 秒），调用方会断开，但 n8n 这边的工作流还在跑——表现为"调用方说失败，执行历史显示成功"。长任务改成异步，参考[一次 AI Agent 工作流的完整路径](#一次-ai-agent-工作流的完整路径)末尾的超时处理。
3. 看监控的执行成功率趋势。如果是某天突然下降，多半是上游 API 变更或凭证过期，不是工作流本身的问题。

**Q2：工作流处理大批量数据时越来越慢，瓶颈在哪？**

先确认慢在哪一层，再动手。常见的三个瓶颈：

- **item 数组全量加载**。如果 PostgreSQL 查询返回几万行，n8n 会把所有 item 放进内存，节点之间的传递也是全量拷贝。改用分页查询或 Limit 节点先截断，处理完一批再查下一批。
- **Code 节点里写了同步循环**。Code 节点对每个 item 执行一次，如果循环里有 HTTP 调用，N 个 item 就是 N 次串行请求。改成批量 API 或用 `Promise.all` 并发。
- **执行历史写入拖慢**。`EXECUTIONS_DATA_SAVE_ON_SUCCESS=all` 在高频工作流下会让数据库写入成为瓶颈，参考[自托管部署](#自托管部署的真实考量)的关键环境变量一节，改成 `none` 或配 prune。

如果数据量到千万级，n8n 不是合适的工具，参考[实战场景与适用边界](#实战场景与适用边界)里数据同步管道的适用边界，换 Spark 或 Flink。

**Q3：从 SQLite 迁移到 PostgreSQL，执行历史和凭证会一起迁过去吗？**

不会自动迁移。n8n 的数据库切换不搬数据，正确做法：

1. 在新 PostgreSQL 实例上启动 n8n，让它自动建表。
2. 从旧实例导出工作流和凭证：`n8n export:workflow --all`、`n8n export:credentials --all --decrypted`（明文导出，文件要妥善保管）。
3. 在新实例导入：`n8n import:workflow`、`n8n import:credentials`。两个实例的 `N8N_ENCRYPTION_KEY` 相同时，加密凭证可以不解密直接迁；密钥不同就必须走 `--decrypted` 明文导出，导入时由新实例用新密钥重新加密。
4. 如果执行历史有合规留存需求，单独用 `sqlite3` 导出成 CSV 存档，不要指望 n8n 帮你迁。

凭证是这条迁移路上最容易踩的坑：直接搬数据库文件，上线后所有工作流报错——加密密钥和凭证密文是绑定的，参考[工作流的核心抽象](#工作流的核心抽象)里凭证一节。

**Q4：AI Agent 工作流里工具节点偶尔失败，LLM 拿到错误后开始编造结果，怎么处理？**

这是 AI 工作流最典型的幻觉来源。工具失败时，n8n 默认把错误信息塞回给 Agent，LLM 会尝试"理解"这个错误并继续回答，结果往往是编造一个看起来合理但不存在的结果。处理方式：

1. 在工具节点里包 try-catch，失败时返回结构化错误对象（如 `{ error: true, message: "检索服务不可用", retryable: true }`），而不是让原始错误字符串直接进 LLM 上下文。
2. 在 Agent 的 system prompt 里明确约定：收到 `error: true` 的工具返回时，必须告知用户"该功能暂时不可用"，不要猜测答案。
3. 对关键工具加节点级重试（参考[排查与运维](#排查与运维)的错误处理与重试一节），网络抖动类错误重试两三次往往就过了。
4. 用 Error Trigger 节点把工具失败事件转发到告警工作流，让人知道有工具在出问题，而不是等用户投诉。

这套设计在[一次 AI Agent 工作流的完整路径](#一次-ai-agent-工作流的完整路径)的"错误处理需要显式设计"部分有提到，生产环境必须落地。

### 高可用部署

单机 n8n 进程退出，工作流就停。规模化的正确形态是 queue 模式：main 进程负责编辑器、定时调度和接收 Webhook（只生成执行，不执行），worker 进程从 Redis 队列取任务真正执行，状态写回 PostgreSQL。worker 无状态，按负载增减即可；SQLite 不适合这个形态，数据库必须换成 PostgreSQL。

```yaml
# docker-compose.yml（queue 模式最小可用形态）
services:
  redis:
    image: redis:7-alpine

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_USER=n8n
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=n8n
    volumes:
      - pg_data:/var/lib/postgresql/data

  n8n-main:
    image: docker.n8n.io/n8nio/n8n
    ports:
      - "5678:5678"
    environment: &n8n_env
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_USER=n8n
      - DB_POSTGRESDB_PASSWORD=${POSTGRES_PASSWORD}
      - DB_POSTGRESDB_DATABASE=n8n
      - EXECUTIONS_MODE=queue
      - QUEUE_BULL_REDIS_HOST=redis
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
    depends_on:
      - redis
      - postgres

  n8n-worker:
    image: docker.n8n.io/n8nio/n8n
    command: worker
    environment: *n8n_env
    depends_on:
      - redis
      - postgres

volumes:
  pg_data:
```

几个关键点：

- 所有进程共享同一个 `N8N_ENCRYPTION_KEY`，否则 worker 解不开凭证。
- worker 默认并发 10 个执行，用 `n8n worker --concurrency=5` 调整；官方建议并发不低于 5，过低的并发反而会耗尽数据库连接池。
- Webhook 量大了再加独立的 `n8n webhook` 进程做接入层（`command: webhook`），用负载均衡把 `/webhook/*` 和 `/webhook-waiting/*` 路由过去，编辑器流量留在 main。
- 定时触发器只在 main 上调度，天然不会重复执行；Webhook 的重复投递靠业务层幂等（唯一 ID 去重）。
- 想让 main 本身跑多个副本互为热备（multi-main setup），那是企业版能力；社区版把 main 做成单点、配好自动拉起和备份即可。

### 升级

```bash
# Docker 方式
docker pull docker.n8n.io/n8nio/n8n:latest
docker stop n8n
docker rm n8n
# 重新启动（数据保持）
```

升级前必须备份 `n8n_data` 卷和数据库。n8n 的大版本升级（如 1.x → 2.x）可能有不兼容变更，先在测试环境验证。生产环境建议锁定版本号，不要用 `latest` 标签。

### 监控

监控三个指标就够了：

- **执行成功率**：低于 95% 说明工作流有稳定性问题。设 `N8N_METRICS=true` 打开 `/metrics` 端点（默认关闭，不要暴露到公网）接 Prometheus；也可以用 Public API 的 `/api/v1/executions` 拉每次执行的状态做补充。
- **执行耗时 P95**：突然变长通常是上游 API 变慢或数据库索引缺失。关注 P95 而非平均值，长尾任务会拖垮整体体验。
- **队列积压**：queue 模式下设 `N8N_METRICS_INCLUDE_QUEUE_METRICS=true`，Prometheus 里会多出 `n8n_scaling_mode_queue_jobs_waiting`（排队中）、`n8n_scaling_mode_queue_jobs_active`（处理中）、`n8n_scaling_mode_queue_jobs_failed`（失败）三个指标，waiting 持续增长说明 worker 数量不够。main 和 worker 都能暴露指标。

告警建议接 PagerDuty 或飞书机器人，不要只靠邮件——工作流故障往往在非工作时间发生，邮件告警的响应速度不够。



---

## 采用顺序与决策建议

### 谁该先用 n8n

**适合先上的团队**：

- 有运维能力的中大型企业，工作流涉及敏感数据，需要自托管满足合规。
- AI 应用团队，需要把 LLM 编排进业务流程，且不想从零搭 Agent 框架。
- 内部工具团队，需要快速搭建跨系统数据流转，且逻辑复杂到无代码表达式不够用。

**可以等等的团队**：

- 工作流只有几条、数据不敏感的小团队——Zapier 或 Make 上线更快，零运维。
- 需要严格事务一致性的场景——n8n 的工作流不是事务性的，金融交易类场景不合适。
- 需要超低延迟的场景——n8n 的执行引擎有调度开销，毫秒级响应用代码直接写更快。

### 落地顺序

1. **先跑通一个非关键工作流**。选一个数据不敏感、失败可接受的工作流（如每日报告推送），用 Docker 单机部署验证。这一步验证的是 Docker 部署、`WEBHOOK_URL` 配置、凭证加密存储是否正常工作。
2. **再迁移一个 AI 工作流**。把一个现有的 LLM 调用脚本改造成 n8n 工作流，体验 LangChain 节点的编排能力。重点看 Code 节点在自托管下如何启用外部模块（`NODE_FUNCTION_ALLOW_EXTERNAL`）、LangChain Agent 节点的工具回调机制、以及 Webhook 的响应模式与超时行为。
3. **然后做凭证和权限治理**。把散落在各处的 API Key 收敛到 n8n 凭证系统，按团队划分项目。这一步验证的是凭证的 OAuth2 Token 刷新、项目隔离的权限模型、以及 `N8N_ENCRYPTION_KEY` 的备份策略。
4. **最后做高可用和监控**。工作流数量上 50 条、有核心业务依赖后，再上 queue 模式扩 worker 和监控。盯三个指标：执行成功率、P95 耗时、队列积压，分别对应工作流稳定性、长尾任务和 Redis 队列健康度。

### 不要做的事

- 不要把 n8n 当数据库用。工作流定义和执行历史不是业务数据，该存业务库的还是要存业务库。
- 不要在 Code 节点里写复杂业务逻辑。Code 节点适合数据转换，复杂逻辑应该抽成独立服务，n8n 通过 HTTP Request 调用。
- 不要忽略执行历史的增长。默认 prune 保留 14 天、1 万条，按自己的审计要求显式调整，别让默认值替你做决定。
- 不要用 `latest` 标签跑生产。版本漂移会导致工作流行为突然变化。

### Sustainable Use License 的边界

n8n 的许可证是 Sustainable Use License，属于 fair-code 范畴，不是 OSI 认可的开源许可证。具体边界：

- ✅ 内部使用：企业内部跑工作流，无限制。
- ✅ 商业使用：把 n8n 集成进自己的产品提供给客户，可以。
- ❌ 转售 n8n 本身：把 n8n 改个名字作为 SaaS 卖给别人，不行。
- ❌ 移除许可证限制：去除 fair-code 限制后重新分发，不行。

采购前让法务确认这个许可证是否符合公司政策。部分企业对非 OSI 开源许可证有统一禁令，需要提前沟通。

### 官方资源

- GitHub：https://github.com/n8n-io/n8n
- 文档：https://docs.n8n.io
- 集成中心：https://n8n.io/integrations
- 模板库：https://n8n.io/workflows
- 社区论坛：https://community.n8n.io
- AI 指南：https://docs.n8n.io/build/integrate-ai/



---

## 练习与自测

下面六道题用来检验你是否真的把上文消化了。建议先动手再做答，对照执行历史和官方文档验证。

### 动手题

1. **触发器选型**。你要做一个"客户下单后 30 分钟未付款自动发提醒"的工作流，应该选 Webhook、Schedule 还是第三方应用事件触发器？写出你的选择和理由，并说明这个工作流的执行模型是同步还是异步。

2. **item 数组语义**。写一个 Code 节点，输入是 10 条订单（含 `order_id` 和 `amount` 字段），输出每条订单的 `amount` 翻倍后的结果。故意写成 `return [{ json: { doubled: items[0].json.amount * 2 } }]`，观察输出 item 数量，再改成正确的 map 写法对比。

3. **凭证治理**。在一个工作流里同时用 PostgreSQL 凭证查询用户、用 Slack 凭证发通知。手动轮换一次 PostgreSQL 密码（在凭证管理界面改），观察工作流是否需要重新配置——这验证了凭证独立存储的好处。

4. **AI 工作流的错误处理**。把上文 AI 客服案例里的 Vector Store 检索节点故意配错（比如 Pinecone API Key 写错），观察 Agent 节点拿到错误后的行为。然后在工具节点里加 try-catch 返回结构化错误，对比两种情况下 LLM 的回复质量。

### 思考题

5. **采用决策**。你的团队有 5 条工作流、数据不敏感、没有专职运维，但其中一条工作流需要调用内部知识库做 RAG。你会选 Zapier、Make 还是 n8n？如果选 n8n，是自托管还是 n8n Cloud？给出取舍依据。

6. **适用边界**。电商订单处理场景里，"n8n 的工作流不是事务性的"这句话具体意味着什么？如果"验证库存"成功但"创建发货单"失败，会出现什么状态？你会如何设计补偿逻辑？

### 自测对照

- 第 1 题考察触发器执行模型的理解，关键在"30 分钟未付款"这个条件需要轮询或延迟，不是事件驱动。
- 第 2 题考察 item 数组的 map 语义，错误写法会丢 9 条数据。
- 第 3 题验证凭证独立存储的实际收益。
- 第 4 题考察 AI 工作流的错误处理设计，幻觉往往来自工具失败后 LLM 自行猜测。
- 第 5 题没有标准答案，关键看你是否能把数据敏感性、运维成本、AI 集成需求三个维度拆开权衡。
- 第 6 题考察事务边界的理解，补偿逻辑可以用 `Execute Workflow` 调用回滚子工作流。



---

## 进阶路径

按下面四步推进，每一步都对应一个可验证的产出物：

### 第一步：跑通单机部署并迁移一个真实工作流

- 产出物：一个 Docker 单机部署的 n8n 实例 + 一个从现有脚本迁移过来的工作流。
- 验证标准：工作流连续运行 7 天无中断，执行历史可追溯，凭证加密存储可备份恢复。
- 关键卡点：`WEBHOOK_URL` 配置、`N8N_ENCRYPTION_KEY` 备份、HTTPS 证书。

### 第二步：把 LLM 编排进工作流

- 产出物：一个 LangChain Agent 工作流，至少调用 2 个工具节点。
- 验证标准：Agent 能根据输入决定调用哪个工具，工具失败时有结构化错误返回，长任务改成异步。
- 关键卡点：Webhook 超时限制、工具节点的 try-catch、Agent 的 system prompt 设计。

### 第三步：做凭证和权限治理

- 产出物：所有 API Key 收敛到 n8n 凭证系统，按团队划分项目，SSO 接入身份提供商。
- 验证标准：凭证轮换只改一处，跨项目无法互相编辑工作流，SSO 登录可用。
- 关键卡点：OAuth2 Token 刷新机制、项目隔离的权限模型、SSO 环境变量名版本差异。

### 第四步：上高可用和监控

- 产出物：queue 模式部署（main + 多 worker + Redis + PostgreSQL）+ Prometheus 监控 + 告警接入。
- 验证标准：单个 worker 宕机不影响其余 worker 继续执行，执行成功率、P95 耗时、队列积压三个指标有告警阈值。
- 关键卡点：`EXECUTIONS_MODE=queue` 配置、`N8N_ENCRYPTION_KEY` 多进程共享、Webhook 的幂等设计、队列指标监控。

### 不建议走的路

- 工作流数量没到 50 条就上多副本——运维成本远超收益，单机 + 备份足够。
- 把核心业务逻辑写在 Code 节点里——Code 节点适合数据转换，复杂业务逻辑应该抽成独立服务。
- 用 n8n 替代专业 ETL 工具做大规模数据同步——千万级以上数据用 Spark 或 Flink，n8n 的执行引擎不是为这个设计的。
- 跳过测试环境直接上生产升级——大版本升级有不兼容变更，先在测试环境跑一遍全量工作流。


