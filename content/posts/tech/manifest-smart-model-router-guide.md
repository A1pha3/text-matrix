---
title: "Manifest：7.5K Stars·开源 LLM Gateway·一个端点接管 300+ 模型"
date: "2026-04-12T02:31:39+08:00"
lastmod: 2026-10-01
slug: manifest-smart-model-router-guide
github_repo: "mnfst/llm-gateway"
source_key: "gh:mnfst/llm-gateway"
description: "Manifest 是开源 LLM Gateway：把 API key、订阅套餐和本地模型接到一个 OpenAI 兼容端点后面，按规则路由、失败自动回退和修复、按 harness 限额记账。本文按 2026-10 源码与文档核实其架构与半年转型过程。"
draft: false
categories: ["技术笔记"]
tags: ["LLM Gateway", "AI Agent", "成本优化", "OpenClaw", "API"]
---

# Manifest：7.5K Stars·开源 LLM Gateway·一个端点接管 300+ 模型

Manifest 真正解决的不是"帮你挑便宜的模型"，而是把**模型选择、故障切换、用量记账**这三件每个 agent 都要重复造的轮子，抽到 agent 进程外面，变成一个可以独立部署、独立审计的网关层。你的 agent 只面对一个 OpenAI 兼容端点，发 `"model": "auto"`，网关决定这次请求落在哪个模型上；失败了在网关里换模型重试，甚至修复请求本身。

这篇文章有两个值得读的理由。其一，它半年内完成了一次完整转型：2026 年 4 月它以"OpenClaw 专用模型路由器"的姿态走红（当时的口号是 "Take control of your OpenClaw costs"），如今仓库已改名 `mnfst/llm-gateway`，定位是面向所有 agent 和应用的通用 LLM Gateway——仓库名都换了，网上大量 4 月前后的解读文已经过时。其二，它的可靠性机制（回退链、请求自愈、硬限额）不是营销词，源码里逐条可查，本文全部按 2026-10-01 的源码与官方文档重新核实过。

## 一、先看半年之变：你读到的旧文可能已经过时

先把新旧口径摆在一张表里。左边是本文 2026 年 4 月初版引用的读数，右边是 2026-10-01 通过 GitHub API、main 分支源码和官方文档重新核实的结果：

| 维度 | 2026-04（初版口径） | 2026-10（当次核查） |
|------|------|------|
| 定位 | OpenClaw 智能模型路由器 | 通用 LLM Gateway（"AI Agents that don't break"） |
| 仓库 | `mnfst/manifest` | `mnfst/llm-gateway`（旧地址 301 重定向） |
| Stars | 4.3k | 7,550 |
| 最新版本 | manifest@5.45.1（2026-04-09） | manifest@6.28.0（2026-09-30） |
| 安装 | `openclaw plugins install manifest` | Docker 一键脚本（npm 自托管路径已废弃） |
| 路由故事 | 23 维评分算法，<2ms | 默认按 harness 配置路由；31 维评分变为可选开关 |

两点提醒。第一，这个项目不是蹭 OpenClaw 热度起家的新仓库——GitHub 记录显示它创建于 2022 年 9 月，OpenClaw 时代只是它生命周期里的一段。第二，转向不是推倒重来：4 月那套"评分→分级→选模型"的机制还在源码里（`packages/backend/src/scoring/`，维度从 23 个增加到 31 个），只是从"唯一卖点"降级成了"可选开关"。下文会分别讲清楚这两套机制的现状。

## 二、系统总览：一次请求在网关里经历什么

Manifest 的后端是 NestJS + TypeScript（TypeScript 占 96.1%），对外暴露两类兼容端点：OpenAI 的 `/v1/chat/completions`（及 Responses API）和 Anthropic 的 `/v1/messages`。所有客户端——Claude Code、Codex、OpenClaw、n8n、你自己的脚本——都指向同一个地址，用同一个 `auto` 别名触发路由。

```text
客户端（Claude Code / Codex / OpenClaw / n8n / openai SDK）
        │  model: "auto" 或具体模型 ID
        ▼
┌─────────────────────────────────────────────────────┐
│                Manifest LLM Gateway                 │
│                                                     │
│  1. 头部路由（header tier）：请求头匹配则直接命中      │
│  2. 具体模型 ID：绕过路由直连（X-Manifest-Tier: direct）│
│  3. auto → 复杂度路由（可选）→ simple/standard/       │
│     complex/reasoning 四档之一 → default tier 兜底   │
│  4. 每档 = 1 个主模型 + 最多 5 个回退模型             │
│  5. 失败处理：Autofix 单次修复 → 回退链逐个尝试       │
│  6. 全程记账：Request / Attempt 两层日志             │
└─────────────────────────────────────────────────────┘
        ▼
OpenAI / Anthropic / Google / DeepSeek / 订阅套餐 / Ollama 本地模型 …
```

三组概念先分清，后文不再混淆：

- **Harness（agent）**：接入网关的一个客户端，比如一个 Claude Code 实例。路由规则、限额都按 harness 配置。
- **Tier（路由档）**：一组"主模型 + 回退模型"。有固定的四档评分档（simple/standard/complex/reasoning），加一个 default 档兜底，再加自定义的 header 档。
- **Request 与 Attempt**：官方术语表里的关键区分。客户端发出的一个逻辑请求是一个 Request；网关为它对上游的每次调用（包括回退和修复重试）是一个 Attempt。失败不丢——完整链路都在日志里。

## 三、接入：改一行 base_url 就够了

接入的本质是把客户端的 base_url 指向网关，再把模型名换成 `auto`。仓库 `packages/shared/src/setup-snippets.ts` 是官方各平台接入配置的唯一来源，注释里连已知坑都写明了。五种典型接法：

**OpenClaw**——4 月那篇旧文写的 `openclaw plugins install manifest` 是 v5 时代的插件方式，现已废弃。现在的接法是把 Manifest 配置成 OpenClaw 的一个 provider（源码注释特别说明：必须用 `openai-completions` API，因为 Manifest 的代理尚未提供原生 `/v1/responses` 端点，用 `openai-responses` 解析会导致气泡空白）：

```bash
openclaw config set models.providers.manifest '{"baseUrl":"…","api":"openai-completions","apiKey":"…","models":[{"id":"auto","name":"Manifest Auto"}]}'
openclaw config set agents.defaults.model.primary manifest/auto
openclaw gateway restart
```

**Claude Code**——写进 `~/.claude/settings.json` 的 `env` 块，每次启动自动生效。模型固定写 `auto`，防止 Claude Code 把内置的 Anthropic 模型 ID 发给网关：

```json
{
  "model": "auto",
  "env": {
    "ANTHROPIC_BASE_URL": "https://你的网关地址",
    "ANTHROPIC_AUTH_TOKEN": "你的 Manifest key"
  }
}
```

**Codex CLI/Desktop**——写 `~/.codex/config.toml`，这里反而用 `wire_api = "responses"`：

```toml
model = "auto"
model_provider = "manifest"

[model_providers.manifest]
name = "Manifest"
base_url = "https://你的网关地址"
env_key = "MANIFEST_API_KEY"
wire_api = "responses"
```

**n8n**——安装社区节点 `n8n-nodes-manifest`（npm 包名），在 Manifest Chat Model 节点里填 base_url、key、模型填 `auto`。

**任意 OpenAI SDK**——不改代码，只改 base_url。需要注意：**Manifest 没有官方 Python SDK**。PyPI 上的 `manifest` 包（"Use an LLM to execute code"，Andrew Moffat 的项目）与本项目无关，装了也对不上。Python 客户端直接用 `openai` 库指向网关即可：

```python
from openai import OpenAI

client = OpenAI(
    api_key="你的 Manifest key",
    base_url="http://localhost:2099/v1",
)
resp = client.chat.completions.create(
    model="auto",
    messages=[{"role": "user", "content": "用 Python 写一个快速排序"}],
)
```

另有一个独立的 npm 包 `manifest`（仓库 `mnfst/manifest-node`），那是给普通 Node.js 应用做 API 调用观测与修复的 SDK，和本文讲的网关是同一团队的两个产品，别混淆。

## 四、路由规则：auto 背后的三层决策

`auto` 触发的决策链有三层，优先级从高到低：

**第一层：header 路由。** 你可以在 Routing 页定义"请求头匹配规则"：请求携带指定 header 时，直接固定到某个 tier。源码注释明确它是运维有意配置的覆盖规则——**header 命中时，即使 body 里写了具体模型 ID 也以 header 为准**。保留字（`authorization`、`cookie`、`x-api-key`）不允许做 header 名。

**第二层：具体模型 ID。** body 里的 model 不是 `auto` 时直连该模型（provider 前缀写法如 `openai/gpt-4o`），完全绕过路由和回退；响应头带 `X-Manifest-Tier: direct`，模型不可用返回 M302 错误。适合"这次就要用指定模型"的场景。

**第三层：default tier 或复杂度路由。** 每个 harness 有一个 default 档（1 个主模型 + 最多 5 个回退），Routing 页随时可改。这是**默认行为**——复杂度路由关闭时，所有 `auto` 请求都走 default 档。

复杂度路由是按 harness 开启的可选项（agent 实体的 `complexity_routing_enabled` 字段，源码默认 `false`）。开启后，评分器对每个 `auto` 请求实时打分，映射到 simple / standard / complex / reasoning 四档，各档分别绑定模型。这套机制就是 4 月旧文的主角，如今仍在演进：

- 维度从 23 个增加到 **31 个**（4 月的 23 = 14 个关键词维 + 9 个结构维；此后新增了 webBrowsing、dataAnalysis、imageGeneration、videoGeneration、socialMedia、emailManagement、calendarManagement、trading 八个任务类维），权重写在 `packages/backend/src/scoring/config.ts`，不是黑盒。
- **Specificity 检测**会先于评分短路：识别出 coding、web_browsing、image_generation、trading 等 9 类明确任务时，直接按类别路由，不走总分。工具名也参与判断——`browser_`、`midjourney_`、`gmail_` 这类前缀会给对应类别加分。
- **Session momentum**：同一会话最近命中的档位会参与打分，避免一次长对话在相邻请求间来回跳档。
- **心跳请求直通 simple 档**：检测到 OpenClaw 式心跳（`HEARTBEAT_OK`）的请求不做评分。

旧文引用的"23 维评分、2ms 内完成、省 70%"出自 2026-04 的官方 README 原话，当时准确；现在 README 已不再宣传这些数字，官方文档改用一句更朴素的表述：路由在网关进程内完成，**不产生额外网络调用**。"省 70%"从来是官方自述口径而非独立测评，本文不再转引。

## 五、可靠性：回退链与 Autofix 自愈

这是当前 README 的第一卖点（"AI Agents that don't break"），也是源码里实现最完整的部分。

**回退链**：每个 tier 是"1 主 + ≤5 回退"的有序列表，自上而下尝试。官方文档明确了触发条件——**任何 HTTP 状态码 ≥400 都触发回退**（429 限流、401 失效、500/502/503/529 全算），没有"只对 5xx 回退"的例外。挂死的上游有单次尝试超时（默认 180 秒），超时以合成 504 计入，然后继续走链。链耗尽返回 M101。成功发生回退时，响应头 `X-Manifest-Fallback-From` 和 `X-Manifest-Fallback-Index` 会告诉你实际用了第几个备选。

**Autofix（请求自愈）**处理的是另一类失败：请求本身格式有问题，重试多少次都不会好。典型场景是 agent 发了上游不认识的参数名（比如把 `max_output_tokens` 写成 `max_tokens`）。网关截获这类"可修复"错误后，把失败请求和上游响应交给修复服务 Phoenix，拿回修补后的请求，**重发一次**——文档强调这是单次尝试（one heal, one reforward），没有重试循环。时序上 Autofix 在回退链**之前**执行。三点边界值得知道：

- 修复服务是官方托管 constant（`autofix.manifest.build`），不支持自建替换；开发/测试环境走进程内 mock，不会把真实失败发到生产修复服务。介意"失败请求内容出网"的，可以用 `AUTOFIX_GLOBAL_ENABLED=false` 全局关掉。
- 默认状态分环境：cloud 部署默认开，自托管默认关，都是 agent 级开关可改。
- 修复尝试完整记录在请求日志里：首次错误、每次改了什么、最终结果可回放。

**硬限额**：按 harness 配置，维度选 tokens 或 cost，周期选 hour/day/week/month。超限后的行为是拦截而非告警——网关在**联系任何上游之前**直接返回一个 HTTP 200，assistant 消息内容是阻断提示（错误码 M200），agent 的对话流不会断，但一分钱不花。阈值调高或进入下一周期即自动恢复。另外 cloud 免费计划每月 10,000 次路由请求，超了返回 M204（HTTP 402）。

## 六、可观测：每一分钱和每一次尝试都有账

日志分两层，与 Request/Attempt 概念对应：一个 Request 记录客户端可见的最终结果；每个 Attempt 记录网关到上游的一次调用，包括被回退跳过的失败尝试、本地路由拒绝（如上游冷却期）也保留为失败 Attempt。错误请求会记录完整请求/响应体（README 说的 "Full Body Logs for Success and Error Messages"），所以排障时能看到 agent 到底发了什么。

仪表板按 harness 汇总花费、模型分布和失败；可配置消费告警通知。对跑着多个 agent、混用多个 provider 和订阅的团队，这层账本是比路由本身更刚需的存在——路由错了顶多贵一点，账不清才是真麻烦。

## 七、Provider 矩阵：key、订阅、本地三条路

按当前 README（manifest@6.28.0 时代）的官方口径：**300+ 模型，35 个内置 provider 连接，18 种订阅流**，另支持任何 OpenAI/Anthropic 兼容自定义端点。三条接入路径对应三种资源：

| 路径 | 代表 | 说明 |
|------|------|------|
| API key | OpenAI、Anthropic、DeepSeek、Mistral、Groq、Fireworks、NVIDIA NIM… | 自己的 key 自己的账单，网关只管路由 |
| 订阅复用 | ChatGPT Plus/Pro、Claude Max/Pro、Grok 订阅、GitHub Copilot、GLM Coding Plan… | 把已付月费的套餐当 provider 用，这是 Manifest 区别于多数网关的卖点 |
| 本地模型 | Ollama、LM Studio（端口 1234）、llama.cpp（端口 8080） | 自托管专属 |

订阅复用值得多说一句：对已经付了 Claude Max 或 ChatGPT Pro 的用户，让 agent 直接消费订阅额度而不是另开 API 账单，是省钱的最短路径。README 的 provider 表逐行列出了各家的订阅形态（如 Anthropic 行标注 "Claude Max / Pro"）。

一个限制要记住：**cloud 版够不到你机器上的本地模型**，官方文档原话是 "it can't reach local models running on your machine"。要用 Ollama/LM Studio，必须自托管。

## 八、一次 429 的完整流转

把机制串起来。假设 Claude Code 指向了 Manifest，default 档配置为"主模型 `claude-sonnet-5`，回退 `openai/gpt-5.5`、`deepseek/v4-pro`"：

1. Claude Code 发出请求，`ANTHROPIC_BASE_URL` 指向网关，`model: auto`。网关的 `/v1/messages` 兼容层接住。
2. 无 header 规则命中，模型是 `auto`，复杂度路由未开——命中 default 档。
3. 网关以 Anthropic key 调用主模型，上游返回 429（限流）。
4. 回退触发，尝试第二个模型 `openai/gpt-5.5`（OpenAI key），返回 200。
5. 响应回给 Claude Code，带 `X-Manifest-Fallback-From: claude-sonnet-5`、`X-Manifest-Fallback-Index: 1`。客户端无感知。
6. 日志里这次 Request 有两个 Attempt：一个 429，一个 200，各自的 token 与费用分别记账。若第 4 步失败原因是请求带了不认识的参数，则会先走一次 Autofix 修复再重发，全部记录在案。

## 九、部署：cloud、Docker 与一键云平台

三选一，官方文档按上手速度排序：

**Cloud**：打开 [app.manifest.build](https://app.manifest.build) 注册即用。免费计划每月 10,000 次路由请求。适合先试水。

**Docker 自托管**：官方一键脚本（下载 compose 文件、生成 `BETTER_AUTH_SECRET` 与 `MANIFEST_ENCRYPTION_KEY`、拉起应用 + PostgreSQL）：

```bash
bash <(curl -sSL https://raw.githubusercontent.com/mnfst/llm-gateway/main/docker/install.sh)
```

然后打开 [http://localhost:2099](http://localhost:2099)，**你注册的第一个账号就是管理员**，没有预置演示凭据。注意两点：compose 默认只绑 `127.0.0.1`，要局域网访问需按文档显式放开；手动 `docker run` 的写法与 4 月旧文不同——镜像**必须**外接 PostgreSQL 和认证密钥，不是挂个数据卷就能跑：

```bash
docker run -d \
  -p 2099:2099 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/manifest \
  -e BETTER_AUTH_SECRET=$(openssl rand -hex 32) \
  -e BETTER_AUTH_URL=http://localhost:2099 \
  manifestdotbuild/manifest
```

**一键云部署**：Railway（官方推荐路径，模板含 Manifest + PostgreSQL + 请求录制存储）、Render、DigitalOcean、AWS CloudFormation、GCP、Fly.io、Coolify、Easypanel、Heroku、Koyeb、Apple Containers 都有官方模板。共同要求是要给请求录制配持久存储（云平台走 S3 兼容桶），卷挂载方案只能单实例。

旧文写的 npm 自托管路径（`npm` 全局安装后运行）已被官方明确废弃："The old npm-based self-hosting path is no longer supported."

## 十、Manifest 与 OpenRouter：不重合的两道题

4 月的 README 里有一张 Manifest vs OpenRouter 对照表，要点是：本地部署对云端代理、免费对收费、MIT 开源对专有、路由透明对不可见。引用这张表需要注明两点。

第一，它是 **Manifest 官方自述**，措辞天然偏向己方（当前 README 已删除此表）。第二，其中"OpenRouter 对每次 API 调用收 5% 手续费"的说法与 OpenRouter 官方口径不符——OpenRouter 的费率是**充值手续费**（刷卡 5.5%、加密货币 5%），推理价格本身按上游原价转付不加价，另有超出额度的 BYOK 使用收 5%。两者架构差异是真实的（OpenRouter 的流量确实经过其服务器，Manifest 自托管时流量不出你的机器），但费率对比应以双方官方文档为准。

更本质的区别在生态位：OpenRouter 是聚合分销商——一个 key 调所有模型，按量计费；Manifest 是你自己的网关层——key、订阅、本地模型都留在你手里，它管路由、回退、记账和限额。前者赢在零运维，后者赢在数据边界和订阅复用。开源世界还有 LiteLLM 等同类自托管网关，选型时值得并列比较，本文不展开。

## 十一、采用建议

**建议现在就上**：同时跑多个 agent harness（Claude Code + Codex + n8n…）、已经付了不止一份模型订阅、或者需要按团队/项目设预算硬闸的团队。Manifest 的账本和限额是运维刚需，接入成本只有改一个 base_url。

**可以等等**：单一 provider、用量不大、或主要诉求是"prompt 智能分流"的场景——default 档 + 回退已经覆盖你，复杂度路由不必开；cloud 免费额度跑不满之前不必自托管。

**上手顺序**：先用 cloud 试 `auto` 与账本是否契合你的工作流；需要本地模型或数据不出机器时，用官方脚本自托管；把不同 harness 分开建 agent，各自配 default 档与限额；跑稳后再考虑开复杂度路由和 header 档这类进阶配置。

**风险提示**：项目发版极快（仅 2026 年 3 月底至 10 月初就发了上百个版本，累计 300+，主要贡献者 55 人），接口与文档同步有滞后——以仓库 `docker/DOCKER_README.md` 与 [官方文档](https://manifest.build/llm-gateway/docs/introduction/) 为准；4 月前后的旧解读文（包括本文初版）中的安装命令已失效。

---

**🔗 相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/mnfst/llm-gateway |
| 官方文档 | https://manifest.build/llm-gateway/docs/introduction/ |
| Cloud 版 | https://app.manifest.build |
| Docker 镜像 | https://hub.docker.com/r/manifestdotbuild/manifest |
| Discord | https://discord.gg/FepAked3W7 |

---

_🦞 本文由钳岳星君撰写，基于 Manifest（mnfst/llm-gateway，7.5k Stars）_

## 自测题

1. **接入 Manifest 后，客户端如何触发自动路由？**
   <details>
   <summary>查看答案</summary>
   把 base_url 指向网关，模型名写 `auto`。触发的是该 harness 的 default 档（或开启复杂度路由后的评分档）。写具体模型 ID 则直连，绕过路由。
   </details>

2. **哪些 HTTP 状态码会触发回退？回退链最多几个模型？**
   <details>
   <summary>查看答案</summary>
   任何 ≥400 的状态码都触发，没有只对 5xx 回退的例外；每个 tier 最多 1 个主模型加 5 个回退，链耗尽返回 M101。
   </details>

3. **Autofix 和回退分别解决什么问题？谁先执行？**
   <details>
   <summary>查看答案</summary>
   回退解决"模型不可用/限流"，Autofix 解决"请求本身格式错误，重试无用"（如参数名写错）。Autofix 单次修复先于回退链执行。
   </details>

4. **硬限额超限后会发生什么？**
   <details>
   <summary>查看答案</summary>
   网关在联系上游之前直接返回 HTTP 200，assistant 消息内容为阻断提示（M200），不产生任何费用；阈值调高或进入下一周期自动恢复。
   </details>

5. **Manifest 没有官方 Python SDK，Python 客户端该怎么接？**
   <details>
   <summary>查看答案</summary>
   直接用 openai 库，把 base_url 指向网关（如 http://localhost:2099/v1），模型填 auto。注意 PyPI 上的 manifest 包是无关项目，不要安装。
   </details>

## 进阶路径

1. **跑通第一次路由**：cloud 注册 → 接一个客户端（Claude Code 或 openai SDK）→ 观察 auto 路由与账单页
2. **自托管**：官方 Docker 脚本部署，创建管理员，接上 Ollama 本地模型
3. **按 harness 治理**：为每个 agent 建 default 档与回退链，配置 tokens/cost 硬限额与告警
4. **进阶路由**：按需开启复杂度路由（31 维评分），用 header 档为特定流量钉死模型
5. **读源码**：`packages/backend/src/scoring/`（评分器）、`routing/proxy/`（代理与回退）、`routing/autofix/`（自愈）与 `docs/glossary.md`（Request/Attempt 术语）

## 资料口径说明

本文初版写于 2026-04-12（manifest@5.45.1 时代），2026-10-01 按当次源码与文档全面核实修订。数据锚点：

1. **GitHub API（2026-10-01）**：mnfst/llm-gateway 7,550 stars / 514 forks / 55 名贡献者（含匿名 59）/ 6,256 commits / 300+ releases / 最新 manifest@6.28.0（2026-09-30）/ MIT / TypeScript 96.1%。仓库 2022-09-27 创建；`mnfst/manifest` 旧地址 301 重定向。
2. **源码（main，浅克隆）**：评分维度 31 个（`scoring/config.ts`，5.45.1 tag 为 23 个）、`complexity_routing_enabled` 默认 false、tier 常量与档位描述（`shared/src/tiers.ts`）、 specificity 九类、回退与 M101/M200/M204/M302 错误码、Autofix 单次修复与托管修复地址（`routing/autofix/`）、限额规则实体（tokens/cost × hour/day/week/month）。
3. **官方文档（2026-10-01 读取）**：路由/回退/限额行为、免费计划 10,000 请求/月、cloud 无法触达本地模型、22 家 API key provider 与订阅 provider 清单。
4. **README（main 与 manifest@5.45.1 tag）**：35 内置连接、18 订阅流、300+ 模型、部署矩阵；"省 70%"、"23 维评分"、"2ms" 为 4 月 README 原话，现已不再宣传，文中已标注历史口径。
5. **外部口径**：OpenRouter 费率（充值手续费刷卡 5.5%/加密 5%，推理不加价）引自 OpenRouter 官方 FAQ；Manifest 4 月 README 对 OpenRouter 的"每调用 5%"说法与该口径不符，文中已指出。
