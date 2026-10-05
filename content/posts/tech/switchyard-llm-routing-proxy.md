---
title: "Switchyard：让编码智能体无缝对接开源模型的 LLM 路由代理"
date: 2026-08-15T03:24:06+08:00
lastmod: 2026-10-01T00:00:00+08:00
slug: "switchyard-llm-routing-proxy"
github_repo: "NVIDIA-NeMo/Switchyard"
source_key: "gh:NVIDIA-NeMo/Switchyard"
description: "Switchyard 是 NVIDIA 开源的 Rust 路由层，帮 AI 智能体决定每个请求交给哪个模型：高效模型跑机械轮次，强模型处理探索与纠错，同时在 OpenAI 与 Anthropic API 之间做协议翻译。本文按 v0.3.0 拆解其路由算法、三种接入方式与成熟度边界。"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "路由", "Rust", "OpenAI API", "Anthropic API", "NVIDIA"]
---

# Switchyard：让编码智能体无缝对接开源模型的 LLM 路由代理

**核心判断**：编码智能体每一次模型调用，其实都在回答一个没有被问出口的问题——这步该用贵模型还是便宜模型。读代码、探索方案的时候需要强模型兜底；连续改文件、跑测试的机械阶段，高效模型就够。Switchyard 做的就是把这个判断从智能体手里接过来：它坐在客户端和模型后端之间，按路由算法给每个请求挑模型，顺手把 OpenAI 与 Anthropic 两种 API 格式互相翻译，让 Claude Code、Codex 这类只会说"母语"的智能体可以直接跑在 vLLM、NVIDIA NIM、Ollama 或任何 OpenAI 兼容端点上。项目是纯 Rust，Apache-2.0，2026 年 5 月 19 日开源，最新版 v0.3.0（2026-09-22 发布），2026 年 10 月初约 3,250 stars。

**给读过旧版介绍的读者**：v0.3.0 是一次破坏性升级。此前的 `switchyard launch claude` 一键启动器、`switchyard serve` Python 服务端、YAML 路由配置，在 0.3.0 里全部删除，官方要求改用独立 Rust 代理直接对接客户端。本文全部按 v0.3.0 之后的形态写。

## 系统地图

```text
Clients（Claude Code / Codex / pi / 任何 OpenAI 或 Anthropic SDK）
      │  保持各自原生 API（OpenAI Chat / Responses / Anthropic Messages）
      ▼
┌─────────────────────────────────────────────────┐
│  Switchyard                                     │
│  ① 解码为中立请求  ② 路由算法选模型  ③ 编码转发 │
│  配套：协议翻译 · 重试 · 回退 · 指标 · 路由日志  │
└─────────────────────────────────────────────────┘
      │  以 backend 原生格式转发（openai_chat / openai_responses / anthropic_messages）
      ▼
Backends（vLLM / NVIDIA NIM / Ollama / OpenRouter / 其他 OpenAI 兼容端点）
```

客户端看到的一直是自己的原生 API；每个后端用哪种协议，由配置里的 LLM client 显式声明，Switchyard 不会去探测。请求进来先解码成中立类型，路由算法在协议无关的层面做决策，再编码成目标后端的格式发出去，响应和流式事件原路翻译回来。

## 用一个 TOML 文件说清三层概念

Switchyard 的部署配置只有三层，各管一件事：

| 层 | 定义什么 | 关键字段 |
|------|---------|---------|
| `llm_clients` | 怎么到达一个提供方 | `base_url`、协议 `format`、`api_key_env` |
| `targets` | 一个具体的上游模型 | 模型 ID + 用哪个 client 调 |
| `routes` | 客户端请求的"模型名"和它的路由算法 | 路由 `id` + 算法 `type` |

最小的自动路由部署长这样（出自官方 getting started）：

```toml
schema_version = 1

[llm_clients.openrouter]
format = "openai_chat"
base_url = "https://openrouter.ai/api/v1"
api_key_env = "OPENROUTER_API_KEY"

[targets.weak]
id = "openai/gpt-4o-mini"
llm_client = "openrouter"

[targets.strong]
id = "openai/gpt-4o"
llm_client = "openrouter"

[routes.smart]
id = "switchyard"
type = "auto"
capable_target = "strong"
efficient_target = "weak"
```

有个容易混淆的点：`[routes.smart]` 里的 `smart` 只是文件内的表名，真正暴露给客户端的是 `id = "switchyard"` 这个字段——它就是请求里 `model` 字段要填的名字，服务器在 `GET /v1/models` 里列出的也是它。密钥不进 TOML 文件，`api_key_env` 只写环境变量的名字，启动时读取。

## 路由算法：从两条主线到一张完整目录

v0.3.0 给路由策略起了对外的新名字，TOML 配置键保持不变。README 的建议是从 Auto 起步：

| 选择 | 怎么决策 | 配置 `type` |
|------|---------|------------|
| Auto | 官方推荐预设，见下文 | `auto` |
| Task | 由一个模型当裁判，判断这次任务高效模型能不能胜任 | `llm_classifier`（capability 模式） |
| Execution | 看会话里已有的工具活动与结果信号来选档 | `stage_router` |
| Composite | 二者组合：信号拿不准时，由分类器定默认档位 | `composite` |

Auto 不是新算法，只是个固定预设：等价于 `stage_router` 配 `picker = "efficient_first"`、`confidence_threshold = 0.5`、不调分类器。它不会在运行时对比多种策略，想调参就直接用 `stage_router`。

在这四条之外，完整目录里还有几种按需启用的策略：Plan/Execute（强模型读代码做规划，首次改动文件后切高效模型）、Escalation（每轮先跑高效模型，裁判读答案决定是否升级重跑）、Custom（自带分类 schema 在多个模型间路由）、Advisor Gate、Sub-Agent 感知路由、Random（固定权重切分，适合 A/B 和基线实验）。不加路由决策的 `passthrough` 则把一个模型 ID 原样注册成一个路由。另有一个 checkpoint 驱动的 Prefill Router，v0.3.0 标注为实验性，官方不提供也不支持任何 checkpoint 与导出工具。

### Execution（stage_router）是核心机制，值得展开

它的赌注是：编码智能体的运行会经过能力需求不同的阶段，强模型应该花在探索和纠错上，常规机械劳动交给高效模型。每个请求进来，stage_router 从会话的工具结果历史里估当前状态，沿两个方向打分：

- **恢复信号，推向强档**：错误严重度（窗口内的加权）、空转（长时间既不读也不写的深度反复）、探索（只在读和规划、不产出）。
- **推进信号，推向高效档**：产出强度——近期被识别的操作里写入和编辑的占比。

两个方向的证据是相互印证的：带符号的分数经 tanh 压缩到 0 到 1 的置信度，单一维度拉满大约到 0.46，两方向同向才会稳过 0.5 的阈值。置信度落在模糊带里就交给可选的分类器裁判，裁判也判不了就落到 picker 的默认档。重复失败、严重错误、上下文压缩这几种情况是硬覆盖，直接上强档。有个细节能看出校准的功夫：内建 read、search 工具的正常返回内容不计入信号，只有工具报告失败才算——翻文件多不等于在挣扎，报错多才是。

### Advisor Gate：换一种花钱方式

前面所有策略都在回答"这轮谁来做"，Advisor Gate 回答的是"做完后谁验收"。它配一个执行模型服务所有可见轮次，再配一个更强的顾问模型，但顾问只当裁判、永远不直接服务请求：执行者给出计划或声称任务完成时（终端轮次），顾问审一遍会话记录，批准就放行，否则把这一轮丢掉、附上具体修改意见打回去重做。触发时机默认是"第一个不带工具调用的轮次"——函数调用型智能体说"我做完了"的自然时刻，也可以配置成文本协议的完成标记，或按轮数设置中途检查点，专治闷头空转不报完成的执行者。

## 一次编码任务如何流过 Switchyard

把机制串起来看一个常规场景。Claude Code 连上本地 Switchyard，路由配 `type = "auto"`，强档挂 Claude、高效档挂本地 vLLM 上的开源模型：

1. 用户描述 bug。头几轮智能体在读代码、搜索符号，工具历史里全是观察类信号，探索方向得分把置信度推过阈值，请求走向强档模型——理解问题不省钱。
2. 定位完成，开始连续编辑五个文件。工具历史变成一连串写入和编辑，产出强度占上风，签名分数转负且稳过阈值，后续请求自动落到高效模型——机械修改不花冤枉钱。
3. 跑测试，三条失败。错误严重度触发硬覆盖，无视置信度直接回强档；强档修完后测试通过，`capable_hold_turns`（默认 2 轮）让接下来两个请求留在强档观察，确认稳定再放回高效档。
4. 全程客户端只看到一个模型名（路由 ID），`/v1/stats` 里却有每个路由、每个候选模型的请求、token 与延迟记录。

这套流程里没有一次"请智能体自己选模型"的提示词工程——分档判断完全发生在会话数据上，这也是它和提示词里写"自己判断用哪个模型"那类方案的本质区别。

## 三种接入方式

### 1. 接进现成网关

LiteLLM 有官方路由插件示例（固定 pin 在 LiteLLM 1.102.0），目前只支持 Stage 和 Random 路由，且是"checkout-only"的实验状态——分类器和 Escalation 需要的中间裁判调用它服务不了。NeMo Relay 则有原生插件，加载标准 TOML 部署、在进程内执行路由，要求 Relay 版本 0.8.0 以上、1.0.0 以下。注意一个已知问题：Relay 0.8.x 和 0.9.0 在插件启用时会丢失上游错误的状态码和详情，连路由之外模型的请求也不例外，官方文档建议开启前先读兼容性说明。

### 2. 独立 Rust 代理（演示与评估的标准路径）

```bash
cargo install --locked switchyard-server
export OPENROUTER_API_KEY="your-openrouter-key"
switchyard-server --config routes.toml --dry-run
switchyard-server --config routes.toml --host 127.0.0.1 --port 4000
```

`--dry-run` 不绑端口，校验配置 schema、环境变量引用和路由构建，是排查配置的第一步。起服务后，任何说 OpenAI Chat、Anthropic Messages 或 OpenAI Responses 的客户端都能连，路由 ID 当模型名用，`curl http://localhost:4000/health` 验活。v0.3.0 的发布验证范围只有 Ubuntu 24.04 的 Linux x86_64，macOS 和 Windows 只保证源码可构建，不在验证范围内。

值得一提的是 `forward_auth` 选项：路由可以不配 `api_key_env` 而是把每个调用者自己的凭据转发给上游，适合网关背后是多租户的场景。代价是约束——同一路由上的所有目标（包括高效档和强档）必须属于同一提供方。

### 3. 嵌入自己的 Rust 应用

`switchyard-libsy`（Beta）把路由算法嵌进你的进程，但它自己从不调用模型：算法决定用哪个 target，模型调用交还给你的代码——请求、重试、凭据都归你管，因此能塞进已有的 proxy、gateway 或 agent runtime。想让库替你完成调用，再配 `switchyard-llm-client`（Alpha）。Python 侧通过 PyO3 绑定拿到同一套算法（`switchyard.libsy`），仓库里 `examples/libsy.py` 是可直接跑的流式示例。

官方还写了两份编码智能体对接指南：[pi](https://github.com/earendil-works/pi)（经 `~/.pi/agent/models.json` 配置，实测 pi 0.84.3）和基于 pi 的 Oh My Pi（`~/.omp/agent/models.yml`，实测 18.1.21）——这两个智能体都不读 `OPENAI_BASE_URL`，所以必须用 provider 条目指向代理。

至于旧版的 `switchyard launch claude` 一键启动器：v0.3.0 已连同整套 Python 服务端栈一起删除，官方口径是把客户端直连独立 Rust 代理。网上还能搜到大量旧教程里的 launcher 命令，现在照抄会直接报错。

## 观测：路由这件事要能被看见

流量分给多个模型后，"哪个路由省钱、哪个在瞎跑"只能靠指标回答。独立代理暴露：

- `GET /metrics`：Prometheus 文本格式，覆盖请求、错误、延迟、token、缓存、重试与路由开销；
- `GET /v1/stats`（配 `/v1/stats/reset`）：JSON 统计与重置；
- 可选的持久化路由日志（JSONL）：逐请求记录路由决策，v0.3.0 起带 `route_id` 和算法名，同一后端模型被两条路由共用时也能分清用量；
- GenAI OpenTelemetry span：宿主装好 OTel 订阅器后，`libsy.run` span 记录路由决策、选中模型与证据字段；库本身不安装 exporter、不外发遥测。

## 成熟度：四档分级与已知问题

README 不再用早期的"pre-alpha"一句话定性（0.2.x 时代原文如此），而是按组件分档：

| 组件 | 稳定性 | 用途 |
|------|--------|------|
| `switchyard-libsy` | Beta | 嵌入自己的网关或 harness，模型调用、凭据、重试归你 |
| `switchyard-llm-client` | Alpha | 配合 libsy 做 HTTP 模型调用与协议翻译 |
| `switchyard-runner` | Alpha | 在其他运行时（如 NeMo Relay）内执行配置好的路由 |
| `switchyard-server` | Demo | 独立 OpenAI/Anthropic 兼容代理，仅用于演示与评估 |

整体口径是"Pre-1.0 软件，API、配置和路由行为在版本间都会变，集成时锁定版本"。评估期值得知道的已知问题（截至 v0.3.0 的 issue 清单）：客户端断开后，已缓冲的上游调用会继续执行完，取消的请求仍可能产生费用；超时返回 504 且不尝试其他模型；对 OpenAI Responses 的会话状态做了按提供方的粘性记录（每路由上限 65,536 条，重启丢失）——带着 `previous_response_id` 的请求不会被误路由到另一个提供方。Codex 用户还有个好消息：0.3.0 的 Responses 编解码已理解 GPT-5 系的 freeform 工具，Codex 会话可以原生路由；Claude Code 的子代理路由则要求 2.1.139 以上版本。

## 怎么读它的评估图

README 放了一张任务完成率对成本的散点图，对比 Stage、分类器、Escalation 三种路由与 Opus 4.8、GLM 5.2 两个单模型基线。读之前先记住官方自己写的两句限定：结果取决于 benchmark、模型池、serving 栈和路由配置；一次更便宜的模型调用不保证一次更便宜的**成功完成**的任务——把任务跑砸再重跑，省的钱就赔回去了。这两句决定了图的正确用法：它证明的是"路由开销在特定工作负载下可接受、质量不掉"，而不是"路由必然省钱"。想自己复现，`benchmark/` 目录提供了 Harbor Terminal-Bench Lite 的两条对照路径（直连上游 vs 经 Switchyard 路由，同一数据集、同一 agent 版本、同一产物布局），另有 NeMo Gym 的小型 MMLU-Redux 示例和 soak 测试流程测路由延迟开销。

## 适用边界与采用建议

- **适合**：正在评估"编码智能体跑开源/低成本模型"可行性的团队；需要跨 OpenAI/Anthropic 协议桥接；想给现有智能体挂一套信号驱动的分档路由并能量化对比成本收益。
- **不适合**：直接上生产——独立代理是 Demo 级组件，发布验证仅覆盖 Ubuntu 24.04 x86_64；需要稳定 API 长期依赖的集成方，等 1.0 并锁版本。
- **采用顺序**：先用独立代理在本地把 `auto` 路由跑通，拿自己的真实工作负载对比单模型基线（官方反复强调"更便宜的调用不等于更便宜的成功任务"，别用别人的图替自己的负载做决定）；确认收益后再决定走嵌入路线（libsy，Beta）还是网关路线（LiteLLM 示例仍实验、Relay 插件需盯错误传播问题）；生产化之前锁定版本，订阅 release notes 跟踪破坏性变更——这个项目的 0.3.0 就删掉了一整条使用路径。
- **关联澄清**：它虽放在 NVIDIA-NeMo 组织下并与 NeMo Relay 有插件关系，但与 NVIDIA NeMo 主框架、SkillSpector（AI agent skill 安全扫描器）互不重叠，是三个独立项目。

## 进一步阅读

- 快速上手与完整部署：`docs/getting_started.md`
- 路由算法总览与逐策略文档：`docs/routing_algorithms/overview.md`
- TOML 配置全字段：`docs/reference/toml_schema.md`
- 已知问题清单：`docs/known_issues.md`
- 请求生命周期与架构：`docs/architecture.md`、`docs/core_concepts.md`
- 基准复现：`benchmark/README.md`
- 智能体对接：`docs/integrations/pi.md`、`docs/integrations/oh_my_pi.md`、`examples/litellm/`
- crates 文档：`switchyard-libsy` / `switchyard-protocol` / `switchyard-translation` / `switchyard-server`
