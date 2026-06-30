---
title: "在 Cloudflare 免费层自托管一个跨 AI 工具的记忆层：rahilp/second-brain-cloudflare 仓库深度拆解"
slug: "rahilp-second-brain-cloudflare-mcp-memory-layer-guide"
date: 2026-06-29T02:01:00+08:00
draft: false
author: 钳岳星君
description: "深度拆解 rahilp/second-brain-cloudflare 仓库——用 Cloudflare Workers + D1 + Vectorize + Workers AI 全家桶搭一个跨 Claude/ChatGPT/Cursor/Codex 共享记忆的 MCP 服务，看 380 star 项目的工程创新。"
categories: ["技术分析"]
tags: ["Cloudflare", "MCP", "LLM", "第二大脑", "技术写作", "反向写作", "rahilp"]
---

# 在 Cloudflare 免费层自托管一个跨 AI 工具的记忆层：rahilp/second-brain-cloudflare 仓库深度拆解

`rahilp/second-brain-cloudflare` 是 2026 年 GitHub 上最值得拆解的 AI 工具型仓库之一——380 stars / 50 forks、TypeScript / MIT、上过 Product Hunt #3。它做了一件很多人想做但没做成的事：**在 Cloudflare 免费层上自托管一个跨 AI 工具共享记忆的 MCP 服务。**

你用 Claude 写文档、ChatGPT 答问题、Cursor 写代码——但你的项目背景、过往决策、个人偏好，每次都要从头解释。这不是因为 AI 不够聪明，而是因为每个 AI 工具的记忆都锁在自己平台里。

这个仓库给出了一个解法：**把记忆从 AI 工具手里夺回来，放进你自己的 Cloudflare 账号，再用 MCP 协议让所有工具都能调用。**

但如果你只把它当成"又一个 AI 记忆工具"看，会错过它真正值钱的部分——**整套工程设计**：用 reserved tag 而非 schema 改动的状态层/类型层、混合召回（RRF 算法）、绕过 Cloudflare Deploy Button UX bug 的 postinstall 黑科技、9 条强制约束 Claude 行为的 AI_Instructions。

这篇文章是对这个仓库的工程化拆解：从架构、关键设计、AI 行为约定、接入生态到部署边界。

---

## 一句话定位与三个核心问题

作者在 README 里把仓库定位写得很清楚：

> **One shared memory for Claude, ChatGPT, Cursor, Codex, and every other AI tool you use.**
>
> Unlike memory built into a single app, this memory belongs to you. It runs in your own Cloudflare account, stays under your control, and cannot be locked inside one AI platform.

它要解决三个问题：

1. **工具间记忆不互通**。每次切换 AI 工具都要重新解释自己——这是因为每个 AI 平台的记忆只对自己可见。
2. **记忆被平台锁定**。Claude 的内建记忆、ChatGPT 的 Memory 都是平台所有，你换平台或者账号被封，记忆就没了。
3. **自托管成本太高**。传统自托管要租服务器、装数据库、配向量引擎——个人用户根本折腾不起。

这个仓库的解法：**用 Cloudflare 免费层把记忆跑在你的账号里，用 MCP 协议让任何 AI 工具都能调用**。

---

## 架构总览：Cloudflare 全家桶 5 件套

整个仓库的架构极其简洁——**单文件 104 KB（src/index.ts）跑在 Cloudflare Workers 上**，后端用 Cloudflare 全家桶：

| 组件 | Cloudflare 服务 | 作用 |
|---|---|---|
| 计算 | Cloudflare Workers | 跑单文件 TypeScript（104 KB），处理所有 HTTP/MCP 请求 |
| 结构化数据 | D1（serverless SQLite） | 存记忆条目、元数据、用户状态 |
| 向量检索 | Vectorize（serverless 向量数据库） | 存 384 维 BGE 嵌入向量，做语义检索 |
| 大模型推理 | Workers AI（`@cf/meta/llama-4-scout-17b-16e-instruct`） | 分类、合并、压缩记忆等"轻 LLM 任务" |
| 鉴权 | Workers OAuth Provider + KV | 用 OAuth 让 AI 客户端安全访问，KV 存 OAuth 状态 |

外加一个每天凌晨 1 点（`0 1 * * *`）的 cron 任务——跑记忆压缩、健康检查、夜间 digest。

整个栈完全在 Cloudflare 免费层上跑。**没有服务器、没有数据库、没有向量引擎要单独维护**——这是这套仓库能 Product Hunt #3 的核心原因。

---

## 6 个记忆工具：MCP 接口设计

MCP（Model Context Protocol）是当前 AI 工具互联的事实标准。这个仓库把记忆操作抽象成 6 个 MCP tool：

| Tool | 作用 |
|---|---|
| `remember` | 存储新记忆（想法、决策、偏好、项目上下文） |
| `append` | 给已有记忆追加更新 |
| `update` | 完全替换已有记忆（用于纠正过期信息） |
| `recall` | 语义检索——按含义而非字面词匹配 |
| `list_recent` | 按时间浏览最近记忆，用于拿到 ID |
| `forget` | 永久删除某条记忆（需用户显式指令） |

注意 `recall` 的设计哲学——**按含义而非字面匹配**。README 里给了一个例子：

> 问："What did I decide about the pricing model?"
>
> 即便原始笔记里写的是"定价策略"，"收入模式"，"收费方法"——任何同义表述都能召回正确记忆。

这种语义检索是 Vectorize 向量数据库的功劳。384 维 BGE 小模型嵌入后存进 Vectorize，recall 时按余弦相似度排序。

---

## 关键设计创新 1：reserved tag 表达状态和类型

这是整套仓库最值得学习的工程设计——**状态和类型用 reserved tag 表达，不改 schema**。

### 状态层（issue #119）

```typescript
export const STATUS_VALUES = ["canonical", "draft", "deprecated"] as const;
export type MemoryStatus = (typeof STATUS_VALUES)[number];
const STATUS_PREFIX = "status:";

export function getStatus(tags: string[]): MemoryStatus | null {
  const tag = tags.find(t => t.startsWith(STATUS_PREFIX));
  if (!tag) return null;
  const value = tag.slice(STATUS_PREFIX.length) as MemoryStatus;
  return (STATUS_VALUES as readonly string[]).includes(value) ? value : null;
}
```

记忆状态（canonical / draft / deprecated）直接编码到 tags 数组里，以 `status:` 前缀开头。这种设计的好处：

- **无 schema migration**：旧的 D1 数据库不用改字段，新老数据兼容
- **多维标签共存**：一条记忆可以同时有 status:canonical + kind:episodic + personal + website
- **查询透明**：用 SQL 的 `json_each` 拆 tags，就能查询

### 类型层（issue #12）

同样模式——`kind:episodic` / `kind:semantic` 用 reserved tag 表达（issue #12）。episodic 是事件性的（"昨天我开会时……"），semantic 是事实性的（"用户住在上海"）。

这两个 issue 的注释明确写道："Status lives as a reserved tag on entries.tags — no schema change. Absent status = unspecified = default behavior."

——**这是"在不破坏兼容性的前提下扩展系统"的标准工程范式**。如果哪天这个仓库要加更多状态（比如 `status:archived`），只需要扩展 STATUS_VALUES 数组，数据库不动。

---

## 关键设计创新 2：混合召回（RRF 算法）

recall 工具的背后是**关键词 + 语义双路召回 + RRF 融合**。源码里有几个关键常数：

```typescript
const RRF_K = 60;                    // Reciprocal Rank Fusion dampening constant
const KEYWORD_CANDIDATE_LIMIT = 100; // max rows the LIKE keyword query scans
const KEYWORD_MIN_TOKEN_LEN = 2;     // ignore 1-char tokens
const KEYWORD_STOPWORDS = new Set([
  "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", ...
]);
```

**RRF（Reciprocal Rank Fusion）** 是一种不依赖分数归一化的多路召回融合算法——把每路召回的结果按排名打分（`score = 1 / (k + rank)`），再按记忆 ID 求和排序。

为什么用 RRF 而非传统加权融合？因为关键词召回（SQL LIKE）输出 BM25-like 分数，向量召回（Vectorize）输出余弦相似度——**两个分数不可比**。RRF 不依赖分数大小，只看排名位置，所以天然兼容异构召回源。

同时还做了 `TAG_BOOST_STEP = 0.15` 的标签加权——如果记忆有匹配的 tag，最终得分会按 0.15 步长逐步加分（最高 1.5 倍）。这种"tag 命中加分"的机制在个性化推荐系统里也常见。

---

## 关键设计创新 3：重要性 + 矛盾机制

每条记忆有一个 1-5 的 `importance_score`，还有两个布尔字段：`contradiction_wins` / `contradiction_losses`。源码里的设计意图是：

```typescript
// Each net contradiction (win or loss) shifts a memory's effective importance by
// log1p(|net|) * this step, clamped to the [1,5] importance band. Tunable.
const CONTRADICTION_IMPORTANCE_STEP = 1.0;
```

机制是：**当新记忆与旧记忆矛盾时，让两个记忆进入"竞赛"——胜者重要性 +1、败者 -1（clamp 到 [1,5] 区间）**。这种"对抗性遗忘"避免了矛盾信息永远堆积——错的记忆会随时间自然衰减。

这是非常前沿的记忆系统设计——大多数记忆工具（mem0、Zep/Graphiti）都没有显式的矛盾处理机制。

---

## 关键设计创新 4：压缩 eligibility（cron 任务）

每天凌晨 1 点（`0 1 * * *`）的 cron 任务会跑记忆压缩，把低重要性、低引用率、老旧的记忆合并成 digest。

但压缩 eligibility 检查非常严格（注释里写"Strictly more protective than the old filter — it can only exempt MORE"）：

```typescript
export const COMPRESSION_IMPORTANCE_THRESHOLD = 4;   // importance >= 4 → protected
export const COMPRESSION_MIN_RECALL = 2;             // recalled >= 2 times → protected
export const COMPRESSION_MIN_AGE_MS = 60 * 86400000; // < 60 days protected unless recalled >= 2

export function compressionEligibilitySql(columnPrefix = ""): string {
  return `(${p}importance_score IS NULL OR ${p}importance_score < ${COMPRESSION_IMPORTANCE_THRESHOLD})
      AND (${p}recall_count = 0 OR (${p}recall_count < ${COMPRESSION_MIN_RECALL} AND ${p}created_at < ?))
      AND (${p}contradiction_wins IS NULL OR ${p}contradiction_wins = 0)`;
}
```

只有**同时满足**三个条件的记忆才会被压缩：

1. 重要性 < 4（即未被用户主动标注重要）
2. 被召回次数 < 2 次 OR 创建时间 < 60 天
3. 没有赢得过矛盾对抗（即信息一直是对的）

这种"严格 default to keep"的策略避免误删重要记忆——一个 60 天前的小笔记，即便没被召回，只要创建时间不足 60 天就受保护。

注释里专门指出："Contains exactly one `?` placeholder — bind `Date.now() - COMPRESSION_MIN_AGE_MS`"——这是 SQL 参数绑定的安全实践，避免 SQL 注入。

---

## AI 行为约定：CLAUDE_INSTRUCTIONS.md 的 9 条强制规则

仓库根目录有一个 `AI_Instructions/` 文件夹，里面有 3 个针对不同 AI 的 prompt 模板：

- `CLAUDE_INSTRUCTIONS.md`（4926 字节，最详细）
- `CODEX_INSTRUCTIONS.md`（4962 字节）
- `CHATGPT_INSTRUCTIONS.md`（1581 字节）

CLAUDE 版本定义了 9 条 MANDATORY RULES（"no exceptions"）。最核心的几条：

**Rule 1（每次会话开始必做）**：

> At the start of EVERY conversation, call recall with a natural language query that describes both the topic AND what the user is trying to do. Frame it as 'User wants to X about Y – what should I know?' rather than just the topic keyword.

——不让 AI 用单个关键词查询，而是要求描述"主题 + 意图"。这是召回质量的根本改进。

**Rule 3（把自己的回答也存）**：

> Store important content from YOUR OWN responses too — call remember after responding whenever your response contains:
> - A recommendation or decision you made on the user's behalf
> - A plan, strategy, or approach you proposed
> - A summary or conclusion you reached
> - A technical solution, architecture, or code pattern you designed

——**AI 不仅存用户信息，还把自己的"决策 + 推理"也存起来**。这样下次类似问题能直接 recall 自己之前的方案。

**Rule 5（禁用内建记忆）**：

> NEVER use Claude's built-in memory system. If you would normally save a memory, call remember instead. Always.

——强制 AI 走 second-brain，不用平台内建记忆。这避免了记忆分流到 Claude 内部系统。

**Rule 7（推荐前先 recall 避免重复）**：

> Before making ANY recommendation, suggestion, or action item, first recall from memory to check if you have already made that recommendation or if the user has already completed it.

——防止 AI 重复推荐。这是真实痛点——大部分 AI 会重复给同样的建议。

9 条规则总的精神：**让 AI 主动建立"客户档案"和"自我档案"，并在每次响应前/后自动同步**。这种设计把 AI 从"被动工具"升级成"有持续记忆的合作者"。

---

## 5 个接入入口：覆盖所有 AI 使用场景

仓库提供了 5 个独立的接入入口，覆盖 PC、移动、命令行各场景：

| 入口 | 适用场景 | 安装方式 |
|---|---|---|
| **MCP clients** | Claude Code / Codex CLI / Cursor | `curl -fsSL .../connect-ai-clients.sh \| bash` |
| **CLI** (`brain`) | 终端用户 | `npm install -g second-brain-cf-cli` |
| **Obsidian 插件** | 笔记用户 | `Second Brain Sync` from Community Plugins |
| **浏览器扩展** | 网页收藏 | Chrome Web Store |
| **iOS Shortcuts** | iPhone / iPad | 仓库 `integrations/ios-shortcuts/` 提供 |

每个入口都是独立仓库或独立子目录，核心数据全部走 Cloudflare 上你的账号——**多端共享同一份记忆**。

iOS Shortcuts 特别有意思——`Brain Dump` / `Text Brain Dump` / `Save to Brain` 三个 shortcut 让用户在 Siri、Widget、Apple Watch 上快速录入。这种"AI 记忆工具的最后一公里"被移动场景覆盖了。

---

## 关键设计创新 5：Vectorize 绑定的巧妙 workaround（绕过 Cloudflare Deploy Button UX bug）

这是整套仓库里最让我"哦"出声的设计——一个**对 Cloudflare Deploy Button UX bug 的工程化绕过**。

`wrangler.jsonc` 里有这样一段注释：

> The VECTORIZE binding is intentionally NOT declared here. When a vectorize binding is present in this file, the one-click "Deploy to Cloudflare" form prompts for index dimensions/metric with no way to preset them, leaving users stuck on blank fields (cloudflare/workers-sdk#14075). Instead, scripts/prepare-wrangler.mjs (run on postinstall) creates the index (384 dims / cosine), writes the binding into a generated wrangler.deploy.jsonc, and drops a .wrangler/deploy/config.json redirect so wrangler uses that generated config. The redirect means even a bare `wrangler deploy` — what the one-click flow runs by default — picks up the VECTORIZE binding, no special deploy command required.

**问题**：Cloudflare 一键部署表单不支持预填 Vectorize 索引参数，用户卡在空白字段（cloudflare/workers-sdk#14075）。

**解法**：

1. 在 `wrangler.jsonc` 里**故意不声明** VECTORIZE binding
2. `scripts/prepare-wrangler.mjs` 在 postinstall 时跑——创建索引（384 维、cosine）
3. 把 binding 写入生成的 `wrangler.deploy.jsonc`
4. 放一个 `.wrangler/deploy/config.json` redirect 文件让 wrangler 用生成的 config
5. 这样连裸的 `wrangler deploy`（一键部署的默认命令）都能 pick up VECTORIZE binding

——**遇到 SaaS 平台的 UX 限制，不去等平台修，而是用 postinstall + config 重定向绕过**。这是非常成熟的工程思维。

Cloudflare 这边应该是已知 issue（#14075 链接都写好了），但作者不等，自己用脚本绕开。这种"主动克服平台摩擦"的态度，是个人开发者项目能跑赢大厂同类产品的核心能力。

---

## 部署流程：3 步 2 分钟

README 里把部署流程压缩到极致：

1. **选 AUTH_TOKEN**（一个你自己记得住的密码）
2. **点 Deploy to Cloudflare 按钮**——表单填 AUTH_TOKEN 即可
3. **连接 AI 客户端**——curl 一行命令搞定

总耗时约 2 分钟。

整套部署不需要写一行 wrangler 命令、不需要理解 D1 schema、不需要手算 Vectorize 维度——**所有工程复杂度都被藏在 postinstall 脚本和单文件 Worker 里**。这是"开发者友好型"产品的最高境界。

## 反例对比：常见 AI 工具 vs 这套仓库

| 常见做法 | 这套仓库 |
|---|---|
| 记忆状态用新加 schema 字段（如 `status` 列） | 用 reserved tag `status:canonical` —— 不改 schema、不破坏兼容 |
| 单路向量检索（仅 semantic） | 关键词 + 语义双路 + RRF 融合——异构分数天然兼容 |
| 让 AI 自己决定何时存记忆 | 9 条 MANDATORY RULES + 自动 recall/remember + 禁用平台内建记忆 |
| 遇到 Cloudflare Deploy Button UX bug 等平台修 | postinstall 脚本 + config 重定向绕过——**主动克服平台摩擦** |
| 记忆越多越占空间，没压缩策略 | 严格压缩 eligibility：重要性 + 召回次数 + 矛盾胜场三重保护 |

## 自查清单：你想做的 AI 工具能不能通过这几条

- [ ] 是否在 Cloudflare 免费层跑完整套后端（D1 + Vectorize + Workers AI）？
- [ ] 状态/类型扩展是否用 reserved tag 而非 schema migration？
- [ ] 召回是否用混合策略（keyword + semantic fusion）？
- [ ] 是否给 AI 写了显式的 MANDATORY RULES 行为契约？
- [ ] 遇到 SaaS 平台 UX 限制时，是否主动用脚本绕开？
- [ ] 压缩/删除策略是否"严格 default to keep"？

这套仓库是 6/6 的样本。

---

## 价值与边界

### 这套仓库能给到你什么

- **跨 AI 工具共享记忆**：Claude、ChatGPT、Cursor、Codex 用同一份记忆
- **完全自托管**：记忆在你的 Cloudflare 账号里，平台无法访问、无法锁定
- **零成本**：Cloudflare 免费层跑完整套系统
- **设计参考**：reserved tag / RRF 混合召回 / 矛盾机制 / 严格压缩策略 都是可学习的工程模式

### 这套仓库给不了你什么

- **多用户**：设计上就是单用户（一个 AUTH_TOKEN），不是 SaaS
- **企业级协作**：没有团队、权限、审计——这是个人工具
- **超大规模**：免费层有请求上限，超出要付费升级 Workers Paid Plan
- **本地部署**：必须跑在 Cloudflare 上，没有 self-hosted 到 NAS 的选项

---

## 这套仓库给我们的启示

最后给想做 AI 工具的开发者几句话。这套仓库之所以 Product Hunt #3、380 star，是因为它做对了几件难的事：

1. **解决真实痛点而非炫技**。"每次切换 AI 工具都要重新解释自己"是几乎每个重度用户的痛——不是凭空的"AI 记忆工具"概念。
2. **Cloudflare 全家桶是个人项目的最佳载体**。Workers + D1 + Vectorize + Workers AI + KV 五件套全部免费层可用，**个人开发者能做出大厂级基础设施的体验**。
3. **设计决策写在代码注释里**。reserved tag 的设计、压缩 eligibility 的 SQL 注释、Vectorize workaround 的 GitHub issue 链接——**工程决策的可追溯性比代码本身更重要**。
4. **AI 行为约定是产品的灵魂**。CLAUDE_INSTRUCTIONS.md 的 9 条 MANDATORY RULES 让 AI 从"被动工具"变"有记忆的合作者"——这种"AI 行为契约"的工程化是大多数同类项目缺的。
5. **遇到平台 bug 不等，自己绕**。Cloudflare Deploy Button 的 UX bug，作者用 postinstall 脚本绕过——**这是个人项目能跑赢大厂的关键能力**。

如果有一天你想做一个类似"AI 工具型产品"——记忆、知识库、协作、自动化——这套仓库的工程结构（Cloudflare 全家桶架构 + reserved tag 扩展 + RRF 混合召回 + AI 行为契约 + 平台 bug 绕过）是值得抄作业的样本。

---

## 实战：如何用 second-brain 做你自己的项目

如果你想基于这套仓库做自己的"AI 记忆/知识工具"，我建议这样入手：

1. **第一周**：部署一份到自己 Cloudflare 账号（10 分钟）。配置 Claude / Codex / Cursor 的 MCP 连接。在 iPhone 上安装 iOS Shortcut。先用 1 周感受"AI 自动 recall/remember"的行为契约。
2. **第二周**：观察自己高频 recall 的 query 类型——是"过去决定过的事"还是"待办任务"还是"代码片段"？这决定你要不要扩展自己的标签体系。
3. **第三到四周**：尝试修改 `CLAUDE_INSTRUCTIONS.md` 的 9 条规则——按你的工作流定制。例如你做开发，可以让 AI 自动 remember"用户经常踩的坑"；你做内容，可以让 AI 自动 remember"用户的写作风格偏好"。
4. **长期**：观察 cron 每天 1 点的压缩效果。如果发现重要记忆被误压缩，调整 `COMPRESSION_IMPORTANCE_THRESHOLD` 等参数——这套仓库的所有阈值都在源码里有明确注释，方便你理解后调优。

**局限**：这套仓库是单用户（一个 AUTH_TOKEN）。如果要做团队协作，需要自己 fork 改造加多用户/权限层。

---

## 参考资料

- **本仓库**：[rahilp/second-brain-cloudflare](https://github.com/rahilp/second-brain-cloudflare)
- **官方主页**：[www.thesecondbrain.dev](https://www.thesecondbrain.dev)
- **Cloudflare Workers**：[workers.cloudflare.com](https://workers.cloudflare.com/)
- **MCP 协议**：[modelcontextprotocol.io](https://modelcontextprotocol.io/)
- **Cloudflare Vectorize**：[developers.cloudflare.com/vectorize](https://developers.cloudflare.com/vectorize/)
- **Cloudflare Workers AI**：[developers.cloudflare.com/workers-ai](https://developers.cloudflare.com/workers-ai/)
- **作者**：Rahil P ([rahilp](https://github.com/rahilp))
- **姊妹仓库**：[second-brain-obsidian-plugin](https://github.com/rahilp/second-brain-obsidian-plugin) / [second-brain-browser-extension](https://github.com/rahilp/second-brain-browser-extension)
- **演示视频**：[YouTube demo](https://youtu.be/h0JqRM0UxHE)
- **许可**：MIT

---

> 写于 2026-06-29 · 反向写作工作流 v3 · 钳岳星君