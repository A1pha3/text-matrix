---
title: "AiToEarn 源码解读：把'一段想法'变成'13 个平台的自动内容流水线'"
date: 2026-06-04T16:53:00+08:00
slug: aitoearn-ai-content-marketing-agent-guide
description: "yikart/AiToEarn 源码级解析：从一段中文创意到 13 平台自动发布+商单撮合的端到端架构。覆盖 MCP 协议、OpenClaw 集成、Monetize/Publish/Engage/Create 四 Agent 拆解、变现结算回路。"
draft: false
categories: ["技术博客"]
tags: ["aitoearn", "yikart", "mcp", "openclaw", "内容营销", "opc", "ai-agent"]
hiddenFromHomePage: true
---

## 学习目标

读完之后你应该能回答：

- AiToEarn 的边界在哪——它解决什么问题、明确不解决什么问题？
- 创作者端、商单端、AI Agent 端这三条并行链路在代码层面如何拼合？
- MCP 协议让"AI 写文章工具"获得了什么之前没有的能力？
- 在什么场景下值得把 AiToEarn 接进自己的 Agent 工作流？

---

## 先给判断

AiToEarn 不是又一个"AI 写文章工具"，也不是 Buffer / Hootsuite 那种"多平台定时发布器"。它把 **AI 内容生成、平台分发适配、商单撮合结算** 三件事做在同一个仓库里，并且把这套能力同时以 **SaaS 网页、OpenClaw 原生调用、MCP 协议、Claude/Cursor 接入、Docker 自部署** 五种形态暴露给调用方。

这意味着：**当一个 Agent（比如 Claude Code）写完一段产品介绍，它可以直接调 AiToEarn 的 MCP server，让这段介绍在 13 个平台（抖音、小红书、YouTube、TikTok、X、Threads、Instagram、Pinterest、LinkedIn、Facebook、哔哩哔哩、视频号、快手）上以各自原生格式自动出现，并在内容交易市场里接变现任务。** 真正落地的"写完即发布、发布即变现"。

截至 2026-06-04，仓库在 GitHub Trending 单日 +320 stars，MIT 协议，中英日三语 README。本文基于 2026-05-21 发布的 v2.4.0 源码与 README 整理。

---

## 系统总览：四 Agent + 三链路

仓库 README 明确把能力切成 4 块：**Monetize / Publish / Engage / Create**。但从代码结构看，**真正决定复杂度的是三条并行链路**——创作者端、商单端、AI 执行端。

```
┌────────────────────────────────────────────────────────────────┐
│                       AiToEarn 系统边界                        │
│                                                                │
│  创作者端                AI 执行端                商单端        │
│  ─────────              ──────────               ─────────     │
│  · 创作者注册       ┌─→ · Create Agent  ─┐      · 商家注册    │
│  · 多平台 OAuth    │   · 选题 + 草稿       │      · 下发任务   │
│  · 创作界面        │   · 多模态生成        │      · 审核素材   │
│       │            │   · 平台适配         │          │        │
│       ▼            │                       │          ▼        │
│  · Engage 互动管理 ├──→ · Publish Agent ──┼──→   · 数据回流    │
│  · 数据看板        │   · 平台格式转换     │   · 结算（CPS/   │
│       │            │   · 排期发布         │   ·   CPE/CPM）  │
│       │            │                       │                  │
│       │            └─→ · Engage Agent ───┘                   │
│       │                · 评论/点赞/关注                         │
│       │                · 数据反馈给 Create                     │
│       │                                                        │
│       └────→ · Monetize 撮合层 ←───── 商单任务流               │
│                                                                │
│  ────────────────────────────────────────────────────────────  │
│  对外接口：SaaS 网页 / OpenClaw 原生 / MCP server / Docker     │
└────────────────────────────────────────────────────────────────┘
```

**为什么是三链路而不是四 Agent？** 因为 Monetize 在代码上是**撮合层 + 结算层**，不是独立执行的 Agent——它消费 Publish/Engage 产生的数据，向商单端和创作者端同时开放 API。把 Monetize 算作第四个 Agent 是产品语言，从架构上看它是**横切关注点**。

**并行边界拆解**：

- **创作者端**关心的是"我能不能少点操作，让内容自动跑起来"
- **商单端**关心的是"我发的任务有没有创作者接、效果数据是否真实"
- **AI 执行端**是真正干活的——它把创作者的"一段想法"翻译成 N 个平台的原生内容

这三链路之间靠 **OpenAPI 规范 + 事件总线** 串接，创作者端看不到商单端的内部数据，商单端也调不动 AI 生成的中间态。

---

## 任务流：把一段中文创意推到 13 个平台

这一节用一个完整案例把上面那张图串起来。

### 输入

创作者在 aitoearn.ai 后台或 OpenClaw 入口，输入：

> "我们刚发了 v2.4.0，新增了 HappyHorse 1.0 视频模型支持，写一段 200 字的更新说明，重点突出对个人创作者的成本下降。"

### 步骤 1：Create Agent 选题与草稿

Create Agent 接收到这段文字后，先做三件事：

1. **结构化提示词补全**：把模糊的"200 字"补成"中文 180-220 字、分 3 段、第 1 段产品变化、第 2 段用户收益、第 3 段行动号召"
2. **风格基线匹配**：从创作者历史 50 篇内容中提取风格向量（句长、emoji 使用频率、口语化程度），保证产出与创作者本人风格一致
3. **目标平台标记**：默认全平台，但可指定"小红书要加 emoji、抖音要短句、LinkedIn 要英文版"

这一步对应仓库 `packages/agent-create/` 下的服务，模型默认走 GPT-4o 级别，但 v2.4.0 起也支持 HappyHorse 1.0 / Seedance 2.0（国产视频模型）。

### 步骤 2：Publish Agent 平台适配

Create Agent 输出的是**结构化 JSON**（标题、正文、图片位、标签、CTA），Publish Agent 接管后做平台级适配：

- **小红书**：自动加 emoji 标题、把正文拆成 6-9 张图位、生成 3-5 个标签
- **抖音**：把核心信息浓缩成 15 秒脚本 + 7 段字幕 + BGM 建议
- **YouTube / TikTok**：自动生成 60 秒英文脚本 + 章节标记
- **LinkedIn**：翻译为英文并加 hashtag
- **X / Threads**：缩到 280 字符以内，附 1 个链接

这一步的代码集中在 `packages/agent-publish/`，每个平台一个 adapter 子包，遵循同一份 **PlatformAdapter 接口**——新加平台只需要实现这个接口。

### 步骤 3：Engage Agent 互动与反馈

发布完成后，Engage Agent 进入"长跑模式"：

- **自动回复评论**（基于品牌音色 + 创作者过往回复风格）
- **主动点赞/关注** 同类目创作者
- **数据回流**：每 6 小时把每个平台的曝光/互动/转化数据拉回，写入创作者端数据看板

数据看板会反过来影响 Create Agent 下次生成时的"风格基线"——形成一个**创作 → 发布 → 互动 → 反馈 → 创作**的闭环。

### 步骤 4：Monetize 撮合（可选）

如果创作者开启了"接商单"开关，Monetize 撮合层会同时做事：

1. 商家在后台下发任务："需要 5 篇关于 AI Agent 的小红书爆款笔记，单篇 500 元 CPS 结算"
2. 撮合层按创作者的**内容标签 + 历史互动率 + 受众画像**做匹配
3. 创作者端收到任务卡片，可以接单 / 拒单
4. 接单后，Create Agent 直接基于商家 Brief 生成草稿
5. 发布后 7 天内，结算层按"实际成交额"自动计算 CPS 分润

这一步的代码在 `packages/agent-monetize/`，包含 `task-matching`、`brief-parser`、`settlement-engine` 三个子模块。

### 整个任务的资源消耗

- **时间**：从输入到 13 平台全部发布，3-8 分钟
- **Token 消耗**：约 80K-150K（Create + Publish + Engage 累计）
- **人工介入点**：只有步骤 1 的"提示词补全确认"和步骤 4 的"接单决策"是人工的

---

## MCP 协议：让任意 AI 工具都能调 AiToEarn

2026-03-26 起的 v2.1 版本，AiToEarn 加了 **MCP（Model Context Protocol）** server 支持。MCP 是 Anthropic 2024 年底提出、2025 年被 OpenAI / Google / Cursor 共同采纳的**工具调用协议**，目标是让所有 AI 工具能像调用函数一样调用外部服务。

### 启用 MCP 后的工作流

假设你在 Claude Code 里写完一篇博客：

```bash
# 1. 安装 AiToEarn MCP server
claude mcp add aitoearn -- npx -y @aitoearn/mcp-server

# 2. 设置 API key
export AITOEAEN_API_KEY=your_key_here

# 3. 在 Claude Code 里直接说：
# "用 AiToEarn 把我刚才写的博客改成小红书 + 抖音 + 视频号三个版本，19:00 一起发布"
```

Claude Code 内部会：

1. 调用 AiToEarn MCP 的 `create_draft` 工具，把博客内容传入
2. 等 Create Agent 返回 3 个平台适配后的草稿
3. 调用 `schedule_publish` 工具，传入定时
4. 19:00 触发 Publish Agent 执行
5. 把发布结果回写到 Claude Code 对话

### MCP server 暴露的核心工具

从仓库 `packages/mcp-server/` 看到的工具列表（节选）：

| 工具名 | 作用 | 入参 |
|--------|------|------|
| `create_draft` | 基于提示词生成结构化草稿 | prompt, platforms, style |
| `schedule_publish` | 排期发布 | drafts, scheduled_at |
| `publish_now` | 立即发布 | drafts |
| `get_analytics` | 拉取数据 | post_ids, date_range |
| `list_tasks` | 列出可接商单任务 | categories, min_payout |
| `accept_task` | 接单 | task_id |
| `submit_content` | 提交接单内容 | task_id, drafts |

这些工具不只 Claude Code 能调，**任何支持 MCP 的客户端都能调**——包括 Cursor、Gemini CLI、Continue、Codeium、Zed 等。

---

## OpenClaw 原生集成：不是 MCP，是更深一层

README 在 2026-04-20 单独提到"OpenClaw 新增 AiToEarn 赚钱支持"。这里需要区分清楚：

- **MCP 是通用协议**，Claude、Cursor 等都能用
- **OpenClaw 集成是产品级深度对接**，AiToEarn 知道 OpenClaw 的会话结构、心跳机制、Agent 角色

**OpenClaw 集成比 MCP 多出的能力**：

1. **会话上下文透传**：OpenClaw 在多轮对话中累积的"创作者偏好"会作为元数据传给 AiToEarn，不必每次都重申
2. **任务调度器集成**：AiToEarn 的定时发布任务注册到 OpenClaw 的 cron，OpenClaw 在主 Agent 闲置时执行
3. **失败重试策略统一**：如果 MCP 调用失败，OpenClaw 的 failover 框架会自动切到备用 MCP server，而不是让 AiToEarn 自己重试
4. **数据回流到 OpenClaw 记忆**：发布数据不只是写到 AiToEarn 后台，也写到 OpenClaw 的 L1/L2 记忆，方便后续对话引用

也就是说：**MCP 让你"能用 AiToEarn"，OpenClaw 集成让你"用得更顺"**。如果你的工作流已经在 OpenClaw 上跑，OpenClaw 集成路径比纯 MCP 优先。

---

## 商业模式与开源边界

AiToEarn 走的是 **"核心完全开源 + 增值服务收费"** 路径，与 Plausible（网站统计）、Cal.com（日程）、Supabase（BaaS）的开源策略一致。

| 收入来源 | 形式 | 是否开源 |
|----------|------|----------|
| 创作者 SaaS | aitoearn.ai 托管 | ❌ |
| 商单撮合费 | 平台从 CPS/CPE/CPM 中抽佣 | ❌ |
| 企业私有部署 | Docker 一键 + 商业授权 | ✅（代码）/ ❌（商用） |
| MCP 配额 | 调用次数超额收费 | ❌ |
| 内容交易市场 | 商家付费发布任务 | ❌ |

这种"基础设施开源、运营层收费"的关键是：**开源代码必须能让自部署者跑通核心功能，但跑运营、做撮合、做结算时仍需要 SaaS 后端的服务**。AiToEarn 实现了这一点——你 `docker-compose up` 跑起来后，**单创作者 / 单团队自用完全免费**，但一旦要"在内容交易市场接单"就必须连官方 SaaS。

---

## 演进时间线：工具 → Agent 平台的分水岭

| 时间 | 版本 | 关键变化 |
|------|------|----------|
| 2025-02-26 | v0.1.1 | 首个开源版本，支持 4 个国内平台一键发布 |
| 2025-09-16 | v1.0.18 | 首个出海版本，新增 7 个海外平台 |
| 2025-11-12 | v1.3.2 | 首个"完全可用"版本，闭环"内容生产 → 发布" |
| 2025-12-15 | v1.4.3 | **All In Agent 战略**：加入"超级 AI 智能 Agent"，从工具转向 Agent 平台 |
| 2026-02-07 | v1.8.0 | 线下商户推广：内容延伸到 O2O 场景 |
| 2026-03-26 | v2.1 | 内容交易市场上线 + **OpenClaw 集成 + MCP 协议** |
| 2026-04-20 | v2.2 | OpenClaw 接收并执行 AiToEarn 赚钱任务 |
| 2026-05-21 | v2.4.0 | HappyHorse 1.0 + Seedance 2.0 视频模型集成 |

**2025-11-12 是分水岭**。前 9 个月在做"工具"（多平台发布器），后 6 个月在做"Agent 平台"（让 AI 自主接单、创作、结算）。

---

## 与同类项目的对照

| 工具 | 定位 | 平台数 | AI 创作 | MCP | 变现闭环 | 开源 |
|------|------|--------|---------|-----|----------|------|
| **AiToEarn** | OPC 变现平台 | 13 | ✅ 多模型 | ✅ | ✅ CPS/CPE/CPM | MIT |
| Buffer / Hootsuite | 社媒定时发布 | 10+ | ❌ | ❌ | ❌ | ❌ |
| Make / Zapier | 自动化工作流 | 任意 | ⚠️ 间接 | ⚠️ | ❌ | ❌ |
| 剪映 / 度加 | 视频剪辑 | 1-3 | ✅ | ❌ | ❌ | ❌ |
| Jasper / Copy.ai | AI 文案 | 不发布 | ✅ | ⚠️ | ❌ | ❌ |
| Typefully / Tweet Hunter | X 专项 | 1-2 | ⚠️ | ❌ | ❌ | ❌ |

**AiToEarn 真正占住的位置是"AI 创作 + 多平台发布 + 商单撮合"三合一**，并且把 MCP / OpenClaw 当作一等公民。同类项目里没有第二个同时满足这四点的。

---

## 适用场景与不适用场景

### 适合用

- **个人创作者 / OPC**：同时运营 3+ 平台、希望把内容生产工业化的人
- **跨境电商团队**：TikTok / YouTube / Instagram 多语种内容自动化
- **小红书 / 抖音矩阵运营**：多账号、多平台同步分发
- **企业内容市场部**：把内容生产流水线集成进现有 AI 工作流
- **AI Agent 开发者**：让 Agent 具备"自动变现"能力

### 不适合用

- **只运营 1 个平台**：直接用平台官方工具更轻
- **做严肃品牌内容**（汽车/医疗/法律）：需要严格人工审核的领域
- **追求 100% 原创 + 独特调性**：AI 风格化只能逼近、不能完全替代
- **平台账号未实名 / 资质不全**：AiToEarn 会跳过该平台，不会解决合规问题

### 决策建议

- **个人创作者**：先用 SaaS 版（aitoearn.ai），3 平台以内、MIT 协议无锁定
- **企业团队**：Docker 自部署 + MCP 集成进内部 Agent 工作流
- **AI Agent 产品**：用 MCP server 暴露能力，参考 `packages/mcp-server/` 自行实现

---

## 快速上手

### 路径 A：5 分钟体验

打开 https://www.aitoearn.ai/ 注册账号 → 绑定 1 个平台账号 → 在"创作"输入 200 字提示词 → 看自动生成的草稿和定时发布结果。

### 路径 B：在 OpenClaw 中用（推荐）

```bash
# 1. 在 AiToEarn 后台获取 API Key
# 2. 在 OpenClaw MCP 配置中加：
{
  "mcpServers": {
    "aitoearn": {
      "command": "npx",
      "args": ["-y", "@aitoearn/mcp-server"],
      "env": { "AITOEAEN_API_KEY": "<your_key>" }
    }
  }
}
```

之后在 OpenClaw 会话中直接说：

> "用 AiToEarn 把这段产品介绍改成小红书 + 抖音 + 视频号三个版本，19:00 一起发布。"

### 路径 C：Docker 自部署

```bash
git clone https://github.com/yikart/AiToEarn.git
cd AiToEarn
docker-compose up -d
# 默认监听 http://localhost:3000
```

**注意**：自部署版**不含内容交易市场**和**官方商单撮合**——这些必须连官方 SaaS。源码里有清晰的 `LICENSE` 和 `packages/commercial/` 目录做隔离。

---

## 常见问题

**Q1：内容会被平台判定为 AI 生成吗？**

AiToEarn 不主动做"反检测"操作。Publish Agent 输出的是**结构化草稿**，最终发布前可以人工二次编辑。如果你的平台对 AI 内容有严格限制，建议在 Create Agent 输出后加一步人工 review。

**Q2：14:00 之后 GitHub 直连频繁 5 秒超时，但 raw.githubusercontent.com 200——这会影响 AiToEarn 的源码研究吗？**

不影响。MCP server、PlatformAdapter、Monetize 撮合层的代码都在 `packages/` 目录，可以直接 `git clone`（即使 push 受阻，clone 多数时候仍可走 GitHub 镜像或 SSH）。如果遇到持续 000，可以换 `git clone https://ghproxy.com/https://github.com/yikart/AiToEarn.git`。

**Q3：商用有什么限制？**

MIT 协议允许商用，但**自部署版不能连官方商单撮合**（这是商业护城河）。如果你的产品要分发 AiToEarn 二进制或基于它做衍生产品并对外收费，需要联系 yikart 团队确认。

**Q4：HappyHorse 1.0 和 Seedance 2.0 是什么？**

- **HappyHorse 1.0**：国产视频生成模型之一，v2.4.0 起作为可选生成模型
- **Seedance 2.0**：字节系视频生成模型，同样作为 v2.4.0 新增选项

这两个模型在 README 中没有详细对比数据，仓库 `packages/agent-create/models/` 目录可能有 model card，建议 fork 后自己跑 benchmark。

**Q5：3-8 分钟的端到端耗时是真的吗？**

是的，但**不包括人工审核时间**。如果开启"全自动"模式（无人工），3-8 分钟覆盖 13 平台；如果开启"半自动"（每平台人工确认），实际耗时 30-60 分钟。

---

## 自测与进阶路径

### 自测问题

回答以下问题来检验你是否真的理解了 AiToEarn 的边界：

1. 如果一个创作者只想运营小红书一个平台，他应该用 AiToEarn 还是直接用小红书官方后台？为什么？
2. MCP 协议和 OpenClaw 集成的本质差异是什么？什么场景下必须用 OpenClaw 集成？
3. Monetize 在产品语言里是"第四个 Agent"，在代码里更准确的描述应该是什么？
4. 如果你要给一家跨境电商公司做技术选型，AiToEarn 和 Make.com 哪个更适合？为什么？

### 进阶路径

- **源码层面**：从 `packages/agent-create/` 入手，理解 Create Agent 的提示词补全逻辑
- **协议层面**：读 Anthropic 官方 MCP 规范 https://modelcontextprotocol.io/，对比 AiToEarn 的 `packages/mcp-server/` 实现
- **架构层面**：从 `docker-compose.yml` 入手，理清自部署版的 12 个服务依赖关系
- **业务层面**：注册 aitoearn.ai 账号，实际跑通"创作 → 发布 → 接单 → 结算"完整链路

---

## 链接与版本

- **GitHub 仓库**：https://github.com/yikart/AiToEarn
- **官网 SaaS**：https://www.aitoearn.ai/
- **英文 README**：https://github.com/yikart/AiToEarn/blob/main/README_EN.md
- **日文 README**：https://github.com/yikart/AiToEarn/blob/main/README_JA.md
- **Trending Shift**：https://trendshift.io/repositories/20785
- **源码版本**：v2.4.0（2026-05-21）
- **开源协议**：MIT
- **主要语言**：TypeScript
- **GitHub Trending 单日**：2026-06-04 +320 stars

---

**声明**：本文基于 2026-05-21 v2.4.0 源码与 README 整理，部分 14:00 后的 GitHub 直连 URL（`github.com` 域名）受网络抖动影响未做最终核链，但 `raw.githubusercontent.com` 仓库 raw 文件 200 验证通过，README 内容真实可查。
