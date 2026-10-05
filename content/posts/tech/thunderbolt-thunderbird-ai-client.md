---
title: "Thunderbolt：Mozilla 系开源 AI 客户端，发布半年后的真实进度与采用边界"
date: "2026-04-19T21:02:00+08:00"
lastmod: "2026-10-03T09:30:00+08:00"
slug: "thunderbolt-thunderbird-ai-client"
github_repo: "thunderbird/thunderbolt"
source_key: "gh:thunderbird/thunderbolt"
description: "Thunderbolt 是 MZLA（Thunderbird 同一主体）开源的跨平台 AI 客户端：本地 SQLite 为源头、PowerSync 同步、可选端到端加密、自托管后端五件套，外加一个同名终端编码智能体。本文对照 2026-04 发布时点与 10 月 HEAD 逐项核实其真实进度。"
draft: false
categories: ["技术笔记"]
tags: ["Tauri", "MCP", "端到端加密", "自托管"]
---

# Thunderbolt：Mozilla 系开源 AI 客户端，发布半年后的真实进度与采用边界

> 本文首发于 2026-04-19，即 Thunderbolt 公开发布当周。半年里版本号从 0.1.x 早期走到 v0.1.134（2026-09-29 发布），stars 从发布当天的 1,808（Wayback 2026-04-19 快照）涨到 4,771（2026-10-03 GitHub API 读数），架构和功能边界都有实质变化。文中数据以 2026-10-03 的仓库 HEAD 为准；涉及发表时点与现状差异之处，均按双时点标注。

Thunderbolt 解决的问题很具体：企业想把 AI 客户端放在自己的服务器上，数据不出门，模型随便换，客户端还不能只做一个网页壳。它给出的答案是三件东西——一个跑在 Tauri 2 上的跨平台客户端（web、macOS、Windows、Linux、iOS、Android 共用一套 React 代码）、一套可自托管的后端（Bun + PostgreSQL + PowerSync + Keycloak），以及一个同名的终端编码智能体 CLI。口号写在仓库描述里："AI You Control: Choose your models. Own your data. Eliminate vendor lock-in."

它不是 Thunderbird 的功能。FAQ 原话说得很清楚：Thunderbolt 由 MZLA Technologies 开发，与 Thunderbird 同属一个主体，"It is not part of Thunderbird's existing products"。资金来自 Mozilla 的专项资助（grant）。定位是企业客户，官网反复强调 on-prem、主权云、物理隔离三种数据主权形态。

## 系统地图

| 层 | 构成 | 说明 |
|---|---|---|
| 客户端 | React 19 + Vite + Tauri 2 + Radix UI + Zustand + TanStack Query + Drizzle | 浏览器用 WA-SQLite，Tauri 下用原生 SQLite；桌面与移动共用一套代码 |
| AI 层 | Vercel AI SDK v6 + MCP 客户端 | 对话、工具调用、远程 MCP 服务器 |
| 同步 | PowerSync（可选） | 本地 SQLite 先写，增量流到后端 PostgreSQL；行级 last-writer-wins |
| 加密 | 可选端到端加密（Preview） | 服务器只存密文和封装好的密钥 |
| 后端 | Elysia on Bun + Better Auth + Drizzle + PostgreSQL | 推理代理、认证、同步令牌签发；自托管时配 Keycloak 做 OIDC |
| 外部 | Anthropic/OpenAI/Mistral/Fireworks/OpenRouter 等模型端点；Google/Microsoft OAuth；PostHog（可选）；Resend 邮件 | 推理走后端代理，密钥由用户自带 |
| 终端 | `thunderbolt` CLI | 单二进制编码智能体，与客户端是两条独立产品线 |

## 离线优先：目标是真的，现状有保留

仓库架构文档写明"Local SQLite is the source of truth"，所有对话、设置、模型配置先落本地库。但 README 从发布起就挂着一条没撤掉的告警：离线优先是最终计划，客户端目前仍依赖后端的认证与搜索功能（网页搜索可以在设置里单独关掉）。这条告警到 2026-10-03 的 introduction.md 里还在。

落到实际体验上：断网时客户端不瘫痪，本地照常读写；但首次注册登录、账号设备管理这些路径绕不开在线后端。把它当成"纯本地应用"来宣传是不准确的，官方也没这么宣传。

## 同步与端到端加密：设计最完整的部分

同步是整个项目工程质量最可见的地方。基于 PowerSync，客户端写本地 SQLite，后台把增量推给后端（`PUT /v1/powersync/upload`），后端在一个 PostgreSQL 事务里落库，再经逻辑复制流回其他设备。同步范围是 11 张表：对话线程、消息、任务、模型配置、提示词模板、模型参数档案、MCP 服务器、自动化规则、设备、项目工作区、用户偏好。默认数据用 `(id, user_id)` 复合主键，让每个账号都能播种同一份默认行。

实现上有个值得注意的细节：浏览器端跑了两条同步管道。Chrome/Edge/Firefox 走 SharedWorker，多标签页共享一条同步连接；Safari/iOS/Tauri 走主线程 transformer，因为 PowerSync 的 OPFSCoopSyncVFS 不支持 SharedWorker，Tauri 也阻止它。两条管道最终都把解密后的行写进本地 SQLite。后端签发短命 JWT 给 PowerSync，轮换 `POWERSYNC_JWT_SECRET` 即可让所有在途令牌失效。

端到端加密目前是 Preview，官方明说尚未做密码学审计。设计本身相当正经：每台设备生成 ECDH P-256 + ML-KEM-768 两对密钥，私钥不出设备；一个账号一把 AES-256-GCM 内容密钥（CK）加密全部数据；CK 用混合信封按设备分别封装；恢复密钥是 24 个词的 BIP-39 助记词，首次设置时只显示一次，设备全丢时是唯一恢复途径；服务器上另存一份 canary 密文用于校验恢复密钥是否正确。线上格式是 `__enc:<iv>:<密文>`，哪些列加密由一张集中配置表决定。

开关在后端：`E2EE_ENABLED=true` 打开（默认关闭），前端从 `GET /v1/config` 读这个标志并缓存在本地。开启后同步前必须走设备信任流程。发布初期有过一个真实漏洞——设备撤销时缺少 canary 所有权证明，攻击者可以借机重置 E2EE 状态——在 4 月下旬修掉了（PR #632）。

## 模型接入：自带密钥是常态，托管模型是新增

常规路径是自带密钥：设置界面里加模型，选 provider（Anthropic、OpenAI、Mistral、Fireworks、OpenRouter 或任意 OpenAI 兼容端点），填密钥和 base URL，想用本地推理就指到 Ollama 或 llama.cpp。没有官方公共推理端点，README 原话："we don't yet have a public inference endpoint"。

两个实现细节值得知道。其一，API 密钥只存本地 SQLite 的 `models_secrets` 表，类型系统从结构上阻止密钥出现在任何服务端载荷里——`SharedModel` 类型干脆不含 `apiKey` 字段。其二，Anthropic 的模型目录接口不是 OpenAI 兼容的，客户端专门写了原生调用（`x-api-key` 头 + 版本头）。

2026 年 9 月起出现了一个新东西：仓库内置三个系统默认模型。Opus 5（上下文 100 万）由后端代理托管，服务端预认证，用户不用填密钥，走 Messages API 并启用了提示缓存；GLM 5.3 和 GLM 5.3 Flash（默认模型）经 Tinfoil 的机密计算环境提供，客户端在调用前做远程证明，校验 enclave 指纹和发布摘要（15 秒超时），UI 上标记为"机密"。这两个 GLM 模型由智谱训练。注意 introduction.md 还写着"无官方推理端点"，与代码已经不一致——以代码为准，文档滞后是这个小密度团队的常态。

## 扩展：MCP 是窄门，ACP 是新路

MCP 支持比想象中窄。设置 → Connections 里添加 MCP 服务器，方式是粘贴一段 `mcpServers` JSON——表单提示原文："Only remote (http/sse) servers are supported; non-Bearer auth headers are ignored"。也就是说：只支持远程服务器，走 Streamable HTTP 或 SSE 传输，认证只认 Bearer 头，本地 stdio 进程跑不了（4 月的源码里就写着 "TODO: Add support for stdio servers"，半年过去没变）。请求经后端 `/v1/mcp-proxy` 透传，配置本身作为同步表跨设备携带。有个例外通道：服务器地址也可以填 iroh NodeId，走 P2P 连本地桥。

宽的那条路是 ACP（Agent Client Protocol）。客户端内嵌 ACP 主机，可以接入兼容的编码智能体——官网列举了 Claude、Codex、OpenClaw、DeepSeek、OpenCode。智能体的能力协商里有会话恢复（resume）支持，技能定义通过 Thunderbolt 命名空间的会话元数据扩展传入，远端智能体产出的工件渲染成卡片。传输层用 iroh：默认走 n0 公共中继，可用 `VITE_IROH_RELAY_URL` 指到自托管中继。这条线 4 月 roadmap 标"In Development - Release Planned: April 2026"，10 月的 introduction.md 里仍是"targeting April 2026"，属于官方节奏慢的例子。

`thunderbolt` CLI 是独立的一条线：单二进制终端编码智能体，基于 Pi harness（`@earendil-works/pi-agent-core`），五个工具——bash、read、write、edit、webfetch——外加 provider 原生网页搜索，接 Anthropic/OpenAI/Google/xAI 的模型，无守护进程，一条 `curl … | sh` 装进 `~/.local/bin`。它与客户端共享品牌但不共享代码，是仓库里最像"另一个项目"的部分。

## 自托管：三条路径，五个容器，一个前置警告

官方部署文档开头就是加粗警告："Under active development — not production ready"，整体安全审计仍在进行中。三条部署路径共享同一套镜像：

| 路径 | 用途 | 说明 |
|---|---|---|
| Docker Compose | 本地开发/评估 | `make doctor && make setup && make up && make run` 一套命令起全栈 |
| Kubernetes（Helm） | 本地或 on-prem 生产意向 | 9 月刚补了多架构镜像、PVC 存储类、nodeSelector、PowerSync 独立 Ingress |
| Pulumi | AWS（Fargate 或 EKS） | IaC 方式铺同一种拓扑 |

五个容器：frontend（nginx，带 COEP/COOP 头给 PowerSync WASM 用）、backend（Bun 自动跑迁移）、PostgreSQL（开 WAL 逻辑复制，兼存 PowerSync 的 bucket 库）、Keycloak（预配置 realm 的 OIDC 提供方，可换成任意 OIDC 兼容 IdP）、PowerSync。注册本身有 waitlist 门槛——自托管也不例外，`POST /v1/waitlist/join` 加入、审批后才能登录。客户端版本也有门：后端设了 `MIN_APP_VERSION`，低于下限的客户端拿 426。

面向消费者的托管版在 FAQ 里确认"planning to launch"，没有日期。想现在用，只有自托管一条路。

## 一条消息的旅程

把机制串起来看一条消息的生命周期。用户在 iPhone 上发出提问：客户端经后端推理代理调模型（假设用的是默认的 GLM 5.3 Flash，则先过 Tinfoil 远程证明，再走加密通道拿到流式响应）。回复逐 token 流入本地 SQLite 的 `chat_messages` 表——这一步不依赖网络稳定性，断网时消息和回复都先落本地。

开了同步的话，这条消息进入上传队列，经 `PUT /v1/powersync/upload` 进 PostgreSQL；Mac 端的 PowerSync 客户端随即收到增量。如果两端都开了端到端加密，iOS 上传前消息已被 CK 加密成 `__enc:` 密文，Mac 在同步管道的 transform 环节用本机信封解出的同一把 CK 解密——全程服务器只见过密文。之后用户在 Mac 上追问一句，同样的路径反向走一遍；若两端离线各自写了数据，重连后同一行按 last-writer-wins 合并，后写的赢。

这个案例也暴露了架构的取舍：行级 LWW 简单可靠，但对"两端同时编辑同一条长对话"的场景，丢的是先写那端的整行更新。官方没给更细的冲突策略，这属于自托管前要想清楚的点。

## 采用建议

**可以认真评估的**：有数据主权或合规诉求、且养得起 Postgres + Keycloak + PowerSync 运维的企业团队；想要一套 MPL-2.0 的跨平台 AI 客户端当底子改造成内部工作台的；研究离线优先 + E2EE 架构的工程师（同步双管道和混合信封设计都值得读）。

**先别碰的**：把"经过安全审计"当硬性门槛的——E2EE 未审计、整体审计进行中，文档自己承认 not production ready；想要开箱即用消费体验的——托管版无日期，注册还要过 waitlist；只想日常聊天的个人用户——五个容器的运维成本换不来对应收益。

上手顺序建议：先 `make up` 起本地 Compose 栈，接 Ollama 验证基础对话；然后加一个远程 MCP 服务器试工具调用；确有跨设备需求再开同步和 E2EE（记住它是 Preview）；要在工作流里接编码智能体，再看 ACP 和 CLI。每一步都可回退，因为客户端的本地数据始终在手。

## 结语

半年下来，Thunderbolt 最扎实的部分是同步与加密的设计深度，最诚实的部分是它从不掩饰未完成——README 的告警、部署文档的警告、roadmap 里排着队的 Planned。它不适合现在就承载关键业务，但作为"企业自托管 AI 客户端"这个命题的开源参考实现，它已经是同类里被最认真做的一个。接下来值得盯的节点有两个：安全审计的结论，以及托管版是否真的落地。

## 相关资源

- GitHub 仓库：<https://github.com/thunderbird/thunderbolt>
- 官网：<https://thunderbolt.io>
- 架构文档：<https://github.com/thunderbird/thunderbolt/blob/main/docs/architecture/README.md>
- 自托管部署：<https://github.com/thunderbird/thunderbolt/blob/main/deploy/README.md>
- 常见问题（与 Thunderbird 的关系、托管版计划）：<https://github.com/thunderbird/thunderbolt/blob/main/docs/faq.md>
