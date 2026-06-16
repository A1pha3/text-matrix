---
title: "new-api：把多个 LLM API 收进一个网关，顺便把计费也做了"
date: "2026-04-14T20:30:00+08:00"
slug: "new-api-llm-gateway"
description: "new-api 在统一 OpenAI 格式的入口背后，做了三件事：格式转换与多模型适配、按渠道和模型粒度的路由、基于额度的用户计费。本文拆开这三条线，给一个请求的完整流转，并给出什么时候该用、什么时候不该用的判断。"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "API网关", "AI", "Claude", "OpenAI", "GPT"]
---

# new-api：把多个 LLM API 收进一个网关，顺便把计费也做了

如果你同时接了 OpenAI、Claude 和 Gemini 的 API，每次切模型都要改客户端代码、各自管理 Key、分别对账——这件事的麻烦不在开发量，而在运维和成本两个维度会持续累积。new-api 做的事情就是在这层麻烦上盖一个统一入口：所有模型对外暴露 OpenAI 格式，请求进入后由网关决定发给谁、怎么计费、额度还剩多少。

这篇文章不会把 README 里的功能列表重抄一遍。下面先把三条主线拆开，然后跟着一个真实请求走完整个流程，最后给出什么场景该用它、什么场景别用的判断。

> **读者**：自己维护多模型 API 调用的开发者、需要给团队做 API 分发的技术负责人。
> **前置**：写过 OpenAI SDK 的调用代码，对 Docker 和 HTTP 反向代理有基本了解。

---

## §1 三条主线：这网关到底做了什么

new-api 对外是一个兼容 OpenAI `/v1/chat/completions` 的 HTTP 服务，但内部可以拆成三条独立的主线。理解这些线之间的关系，比记住配置文件字段更重要。

```
客户端 (OpenAI SDK / curl / LangChain)
         │
         ▼
   ┌──────────────────────────────────────────┐
   │              new-api 网关                 │
   │                                          │
   │  ① 格式转换：OpenAI 请求 ↔ 各厂格式      │
   │  ② 渠道路由：按模型/渠道/权重选上游       │
   │  ③ 额度计费：扣额度 → 转发 → 回写用量    │
   │                                          │
   └──────┬──────────┬──────────┬─────────────┘
          ▼          ▼          ▼
      OpenAI     Claude     Gemini ...
```

三条线职责分明：

| 主线 | 负责什么 | 不负责什么 |
|------|----------|------------|
| **格式转换** | 把 OpenAI 格式的请求体翻译成 Claude/Gemini 等原生格式，再把响应翻译回来 | 不做语义理解、不做 prompt 改写、不做流式内容缓存 |
| **渠道路由** | 根据模型名匹配上游渠道，按权重分发，处理失败重试和降级 | 不做全局负载感知、不做跨渠道 session 亲和 |
| **额度计费** | 请求前扣额度、请求后根据实际 token 用量核销、记录流水 | 不做实时价格比对、不做跨模型预算优化 |

这三条线几乎是正交的——你可以只用格式转换而关掉计费，也可以只做路由而不开格式转换（当然全关掉网关就没意义了）。下面跟一个真实请求看看它们怎么协作。

### 一次请求的完整路径

假设团队里有个后端服务，用 `openai` Python 库发请求，但这次想打 Claude：

```python
import openai

client = openai.OpenAI(
    base_url="http://new-api:3000/v1",
    api_key="sk-user-abc123"
)

response = client.chat.completions.create(
    model="claude-3-5-sonnet",
    messages=[{"role": "user", "content": "解释一下 B+ 树的写入路径"}]
)
```

请求进入 new-api 后，依次经过以下步骤：

1. **鉴权**：`sk-user-abc123` 被解析为用户 ID `abc123`，查出该用户的可用额度和模型权限。
2. **额度预检**：系统检查用户对 `claude-3-5-sonnet` 的剩余额度是否大于零。如果额度不足，直接返回 402，不转发到上游——这在成本控制上比先转发再对账安全得多。
3. **渠道匹配**：`claude-3-5-sonnet` 被路由到 Anthropic API 渠道。如果配置了多个 Anthropic 渠道（比如不同账号的 Key），按权重选一个。
4. **格式转换**：OpenAI 格式的 `messages` 数组被转成 Anthropic 的 `messages` 格式（system prompt 提到顶层、`role` 映射、content 结构调整）。同时，`temperature`、`max_tokens` 等参数也做了字段名和取值范围的转换。
5. **转发并等待**：请求发到 Anthropic API。如果超时或返回 5xx，根据重试配置决定是换渠道重试还是直接返回错误。
6. **响应回译**：Anthropic 返回的 `content` 数组（可能包含 `text` 和 `tool_use` 两种 block）被重组为 OpenAI 格式的 `choices[0].message.content`。
7. **额度核销**：根据响应中的 `usage.input_tokens` 和 `usage.output_tokens`，按模型定价表扣减用户额度，写入流水。

整个过程对调用方透明——代码里只改了 `base_url` 和 `model` 参数。但正是这 7 步，把"聚合多模型 API"这件事从客户端代码层面的胶水，收进了网关层。

---

## §2 格式转换：不只是字段重命名

格式转换最容易被人当成"把 `messages` 换个字段名"，但实际上要处理的情况比想象中多。

### 请求体的结构差异

OpenAI 的 chat completion 请求体结构是所有厂商里最"扁平"的——参数全在顶层、messages 是统一数组。Claude 把 `system` 提到顶层字段，Gemini 把整个请求包在 `contents` 里。转换器要处理的不是 1:1 映射，而是结构的拆解与重组：

| 请求元素 | OpenAI | Claude | Gemini |
|----------|--------|--------|--------|
| system prompt | `messages[0].role="system"` | 顶层 `system` 字段 | `systemInstruction` 字段 |
| user/assistant | `messages[*].role` | `messages[*].role` | `contents[*].role` |
| tool calling | `tools` 数组 | `tools` 数组（字段名不同） | `tools` + `functionDeclarations` |
| 图片输入 | `content: [{type:"image_url",...}]` | `content: [{type:"image",source:{...}}]` | `parts: [{inlineData:{...}}]` |
| 流式 | `stream: true` | `stream: true` | `stream: true`（SSE 事件格式不同） |

其中流式（streaming）是最容易出问题的。三家都用 SSE，但事件名、data 字段结构、finish_reason 的枚举值都不一样。转换器必须在首字节到达后就开始逐事件翻译，不能等整个响应收完再处理，否则流式的实时性就丢了。

### 功能子集的取舍

不是所有 OpenAI 参数都有下游对应物。`response_format: {type: "json_object"}` 在 Claude 里要走 prompt 约束来实现，`logprobs` 在 Gemini 里没有等价功能，`seed` 参数各厂支持程度不一。转换器的策略是"能转就转，不能转就静默丢弃并记日志"，而不是硬造一个看起来能用的假参数——后者在生产环境里会制造难以排查的行为差异。

---

## §3 渠道路由：不止 weight 一个参数

路由配置在 `config.yaml` 里看起来很简单：

```yaml
routing:
  - path: /v1/chat/completions
    upstream:
      - provider: openai
        weight: 50
      - provider: claude
        weight: 50
```

但实际生效时，路由决策涉及四层信息：

1. **模型 → 渠道映射**：请求里的 `model` 字段被解析，匹配到支持的渠道列表。如果 `gpt-4o` 配置了两个 OpenAI 渠道（不同账号），两个都入选。
2. **渠道健康状态**：每个渠道维护一个"可用/不可用"标记。连续失败 N 次后自动熔断，熔断期间不参与权重分配，等冷却时间到了再试探性恢复。
3. **权重分发**：在健康渠道中按 `weight` 做加权随机。两个权重 50 的渠道，各有一半概率被选中。
4. **重试与降级**：如果选中的渠道返回 429（限流）或 5xx，可以根据配置换另一个渠道重试。降级策略是"同模型其他渠道 → 同厂商其他模型 → 报错"。

值得留意的一点是：这里的路由是**无状态**的——两次连续请求可能落到不同渠道，即使模型相同。如果需要 session 级别的亲和（比如同一个 conversation 始终走同一个渠道），需要在网关上层（负载均衡或客户端）做 sticky session，new-api 本身不提供。

### 限流保护

new-api 在渠道层面支持 QPS（每秒请求数）和 TPM（每分钟 token 数）限制。这两个值是配置在渠道上的，不是从上游 API 的 rate-limit header 里动态解析的。所以配置时需要把值设得比上游实际限制略低，给突发流量留缓冲。

---

## §4 部署：一个 docker-compose up，但要关注三件事

### 基础部署

```bash
git clone https://github.com/QuantumNous/new-api.git
cd new-api

cp config.example.yaml config.yaml
vim config.yaml

docker-compose up -d
```

Docker Compose 会拉起网关本身和 MySQL（或 PostgreSQL，取决于配置）。网关默认监听 3000 端口。

### 生产环境要额外处理的三件事

**数据库**：默认的 MySQL 容器没有持久化存储，容器重启数据全丢。生产环境要把数据库 volume 挂到宿主机，或者直接用外部数据库——new-api 的用户、额度、流水都在数据库里，这不是可选优化。

**反向代理**：网关前面的 Nginx/Caddy 至少要做两件事：一是 HTTPS 终结，API Key 不能明文过公网；二是 `client_max_body_size` 要调到足够大，因为图片输入（vision API 场景）的请求体可能超过 Nginx 默认的 1MB。

**日志与监控**：new-api 的日志默认打到 stdout，Docker 日志驱动可以采集。但额度流水和错误统计更适合从数据库直接查——`logs` 表记录了每次请求的模型、token 用量、扣费金额和状态码，定期按用户和模型聚合就能得到成本分布。

---

## §5 计费系统：额度模型比价格表更重要

new-api 的计费不是真正的"支付系统"——它不接支付宝或 Stripe，也不处理充值流水。它做的是一件更基础的事：**额度管理**。

### 额度模型

```yaml
billing:
  - user: user123
    credits: 1000
    models:
      gpt-4o: 0.01
      claude-3-5-sonnet: 0.015
```

每个用户可以设置一个总`credits`（通用额度），并对不同模型设置不同单价。单价单位由管理员自行定义（一般是美金/1K tokens，但网关不做货币语义校验）。用户每次调用后，网关把 `usage.total_tokens / 1000 * 单价` 从总额度中扣掉。

这个模型简单但有几个生产环境中容易踩的坑：

- **额度是整数**：小数精度问题意味着大量小额调用后可能出现累积误差。建议把单价乘以 10000 存整数，扣减时用整数运算，展示时再除回来。
- **预扣与实际扣**：请求发出前没法知道实际会用多少 token。new-api 的策略是：先检查额度是否大于 0（预检），请求完成后再根据实际 token 数扣减。一个只剩 1 credit 的用户仍然可能打出一个消耗 100 credit 的长回复——网关不会在请求中途掐断。
- **多模型共享额度**：上面的配置里 `credits: 1000` 是所有模型共享的。如果想让用户在每个模型上有独立限额，需要另外配置模型级额度上限。

### 用量查询

```bash
curl http://localhost:3000/admin/usage \
  -H "Authorization: Bearer $ADMIN_KEY"
```

管理端可以按用户、模型、时间范围查用量流水。对于需要对账或做成本分析的场景，建议直接从数据库查 `logs` 表做聚合，而不是依赖这个接口——接口返回的是分页列表，大规模数据下效率不高。

---

## §6 什么时候用，什么时候不用

### 明确该用的场景

- **团队内部有 3 个以上开发者在调不同厂商的 API**。统一入口带来的收益不是少写几行代码，而是 Key 不再散落在每个人的 `.env` 里、调用量不用手动汇总。
- **需要给不同用户/项目分配不同额度**。比如一个内部平台对外提供 AI 能力，不同租户有独立预算——new-api 的额度模型直接对应这个需求。
- **需要屏蔽上游 API 的变动**。OpenAI 改了 SDK 接口？客户端代码不用动，网关层兼容就行。

### 不该用或者要慎重用的场景

- **只有一个厂商、一个模型**。网关层引入的额外网络跳转和序列化开销不值得。直接用官方 SDK 更快也更少出错。
- **流式场景对延迟极度敏感**。格式转换和额度记录都是额外开销。虽然正常情况下这层开销在几十毫秒以内，但如果你在做实时语音对话这类场景，每一跳都要算。
- **需要跨请求的上下文保持**。new-api 不维护 conversation state，系统提示词和对话历史由客户端管理。如果你的产品逻辑强依赖服务端维护的多轮会话状态，网关够不到这一层。
- **需要接支付网关做真实收费**。new-api 只管额度不管钱。如果你要做面向 C 端的付费 AI 产品，还需要一个独立的支付和订单系统。

### 如果决定上车，建议的顺序

1. 先用 Docker Compose 在开发环境跑起来，配置一个 OpenAI 渠道，确认调用链路正常。
2. 把第二个厂商（比如 Claude）加上，验证格式转换在流式和非流式场景下都正常。
3. 接入你们现有的用户体系——new-api 支持通过 API Key 前缀识别用户，这一步决定额度管理能不能落地。
4. 配置额度和定价，先用少量额度验证扣费逻辑，确认 `logs` 表记录无误后再放开。
5. 上线前加反向代理和数据库持久化。

---

## §7 相关资源

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | [github.com/QuantumNous/new-api](https://github.com/QuantumNous/new-api) |