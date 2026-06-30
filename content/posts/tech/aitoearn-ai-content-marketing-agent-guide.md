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

---

## 目录

- [先给判断](#先给判断)
- [学习目标](#学习目标)
- [系统总览：四 Agent + 三链路](#系统总览四-agent--三链路)
- [任务流：把一段中文创意推到 13 个平台](#任务流把一段中文创意推到-13-个平台)
- [MCP 协议：让任意 AI 工具都能调 AiToEarn](#mcp-协议让任意-ai-工具都能调-aitoearn)
- [常见问题](#常见问题)
- [采用建议与适用边界](#采用建议与适用边界)
- [自测与进阶路径](#自测与进阶路径)
- [资料口径说明](#资料口径说明)
- [链接与版本](#链接与版本)

---

## 先给判断

AiToEarn 把 **AI 内容生成、平台分发适配、商单撮合结算** 三件事做在同一个仓库里，并以 **SaaS 网页、OpenClaw 原生调用、MCP 协议、Claude/Cursor 接入、Docker 自部署** 五种形态暴露给调用方。它的定位介于"AI 写作工具"和"Buffer/Hootsuite 多平台定时发布器"之间——前者只管生成不管分发，后者只管分发不管生成，AiToEarn 把两端连同变现层一起打包。

**核心场景**：当一个 Agent（比如 Claude Code）写完一段产品介绍，它可以直接调 AiToEarn 的 MCP server，让这段介绍在 13 个平台（抖音、小红书、YouTube、TikTok、X、Threads、Instagram、Pinterest、LinkedIn、Facebook、哔哩哔哩、视频号、快手）上以各自原生格式自动出现，并在内容交易市场里接变现任务。

截至 2026-06-04（据 README 与 Trending Shift 页面显示），仓库在 GitHub Trending 单日新增约 320 stars，MIT 协议，中英日三语 README。本文基于 2026-05-21 发布的 v2.4.0 源码与 README 整理；文中涉及的具体耗时、Token 消耗、星数等数字均来自 README 描述或作者公开声明，未经独立复测。

---

## 学习目标

读完本文，你应该能够：

1. **理解 AiToEarn 的定位**：说清它和"AI 写作工具""多平台发布器"的核心差异，以及它把哪三件事做在同一个仓库里。
2. **拆解四 Agent 架构**：区分 Create / Publish / Engage 三个执行 Agent 和 Monetize 撮合层的职责边界，能画出一个创意从输入到 13 平台发布的流向图。
3. **解释 MCP 协议的价值**：说清 MCP 解决的是什么问题，以及接入 MCP 后 Claude Code / Cursor / OpenClaw 等工作流会发生什么变化。
4. **评估适用场景**：面对"多平台运营团队""单平台品牌号""MCN 商单撮合"三类读者，能分别给出"先用/可以等等"的判断理由。
5. **独立运行最小闭环**：按照文中的步骤，用 Docker 自部署或官方 SaaS，实际跑通一次"输入创意 → 生成草稿 → 多平台发布"的完整流程。

---

## 系统总览：四 Agent + 三链路

仓库 README 把能力切成 4 块：**Monetize / Publish / Engage / Create**。从代码结构看，真正决定复杂度的是三条并行链路——创作者端、商单端、AI 执行端。Monetize 在代码上是**撮合层 + 结算层**，消费 Publish/Engage 产生的数据，向商单端和创作者端同时开放 API。把 Monetize 算作第四个 Agent 是产品语言，从架构上看它是**横切关注点**。

### 三链路职责对照

| 链路 | 关心的问题 | 主要代码位置 | 对外暴露 |
| --- | --- | --- | --- |
| 创作者端 | 如何减少手动操作，让内容自动跑起来 | `packages/agent-create/` 等 Agent 包的调用入口 | SaaS 后台、OpenClaw 入口 |
| 商单端 | 任务有没有人接、效果数据是否真实 | `packages/agent-monetize/`（撮合 + 结算） | 商家后台 API |
| AI 执行端 | 把"一段想法"翻译成 N 个平台的原生内容 | `packages/agent-create/`、`packages/agent-publish/`、`packages/agent-engage/` | MCP server、OpenClaw 原生调用 |

三链路之间靠 **OpenAPI 规范 + 事件总线** 串接：创作者端看不到商单端的内部数据，商单端也调不动 AI 生成的中间态。这种隔离让商单撮合可以独立升级，而创作者工作流不受影响。Monetize 没有自己的执行体，因此被归为横切关注点，不作为独立 Agent 看待——撮合逻辑由 `task-matching` 触发，结算逻辑由 `settlement-engine` 在发布事件后异步执行，两者都依附于 Publish/Engage 产生的事件流。

---

## 任务流：把一段中文创意推到 13 个平台

这一节用一个完整案例把三链路串起来，看抽象机制在一次真实工作里如何配合。

### 输入

创作者在 aitoearn.ai 后台或 OpenClaw 入口，输入：

> "我们刚发了 v2.4.0，新增了 HappyHorse 1.0 视频模型支持，写一段 200 字的更新说明，重点突出对个人创作者的成本下降。"

### 步骤 1：Create Agent 选题与草稿

Create Agent 接收到这段文字后，先做三件事：

1. **结构化提示词补全**：把模糊的"200 字"补成"中文 180-220 字、分 3 段、第 1 段产品变化、第 2 段用户收益、第 3 段行动号召"。补全规则写在 `packages/agent-create/prompts/` 下，目的是把人类自然语言里的模糊量词映射成模型可执行的硬约束。
2. **风格基线匹配**：从创作者历史内容中提取风格向量（句长、emoji 使用频率、口语化程度），保证产出与创作者本人风格一致。这一步需要创作者先授权读取历史发布数据，未授权时退化为平台默认风格。
3. **目标平台标记**：默认全平台，但可指定"小红书要加 emoji、抖音要短句、LinkedIn 要英文版"。

这一步对应仓库 `packages/agent-create/` 下的服务，模型默认走 GPT-4o 级别，v2.4.0 起也支持 HappyHorse 1.0 / Seedance 2.0（国产视频模型，README 未给出与 GPT-4o 的对比数据）。

### 步骤 2：Publish Agent 平台适配

Create Agent 输出的是**结构化 JSON**（标题、正文、图片位、标签、CTA），Publish Agent 接管后做平台级适配：

- **小红书**：自动加 emoji 标题、把正文拆成 6-9 张图位、生成 3-5 个标签
- **抖音**：把核心信息浓缩成 15 秒脚本 + 7 段字幕 + BGM 建议
- **YouTube / TikTok**：自动生成 60 秒英文脚本 + 章节标记
- **LinkedIn**：翻译为英文并加 hashtag
- **X / Threads**：缩到 280 字符以内，附 1 个链接

这一步的代码集中在 `packages/agent-publish/`，每个平台一个 adapter 子包，遵循同一份 **PlatformAdapter 接口**。新加平台实现这个接口即可，不必改动 Create 或 Engage 的代码——这是 AiToEarn 能快速扩展到 13 个平台的根本原因。

### 步骤 3：Engage Agent 互动与反馈

发布完成后，Engage Agent 进入"长跑模式"：

- **自动回复评论**（基于品牌音色 + 创作者过往回复风格）
- **主动点赞/关注** 同类目创作者
- **数据回流**：定期把每个平台的曝光/互动/转化数据拉回，写入创作者端数据看板（README 未给出具体拉取频率，需查 `packages/agent-engage/` 源码确认调度配置）

数据看板会反过来影响 Create Agent 下次生成时的"风格基线"——创作 → 发布 → 互动 → 反馈 → 创作，跑完一圈。这个闭环让风格匹配从"一次性快照"变成"持续校准"。

### 步骤 4：Monetize 撮合（可选）

如果创作者开启了"接商单"开关，Monetize 撮合层会同时做事：

1. 商家在后台下发任务："需要 5 篇关于 AI Agent 的小红书爆款笔记，单篇 500 元 CPS 结算"
2. 撮合层按创作者的**内容标签 + 历史互动率 + 受众画像**做匹配
3. 创作者端收到任务卡片，可以接单 / 拒单
4. 接单后，Create Agent 直接基于商家 Brief 生成草稿
5. 发布后 7 天内，结算层按"实际成交额"自动计算 CPS 分润

这一步的代码在 `packages/agent-monetize/`，包含 `task-matching`、`brief-parser`、`settlement-engine` 三个子模块。撮合层只读 Publish/Engage 的数据，不直接调用 AI 生成——这保证了商单流程可以独立审计。

### 整个任务的资源消耗

以下数字来自 README 描述，实际消耗取决于平台数量、内容长度和模型选择：

- **时间**：从输入到 13 平台全部发布，3-8 分钟（全自动模式，不含人工审核）
- **Token 消耗**：约 80K-150K（Create + Publish + Engage 累计）
- **人工介入点**：只有步骤 1 的"提示词补全确认"和步骤 4 的"接单决策"是人工的

---

## MCP 协议：让任意 AI 工具都能调 AiToEarn

2026-03-26 起的 v2.1 版本，AiToEarn 加了 **MCP（Model Context Protocol）** server 支持。MCP 是 Anthropic 2024 年底提出、2025 年被 OpenAI / Google / Cursor 共同采纳的**工具调用协议**，目标是让所有 AI 工具能像调用函数一样调用外部服务。

### 为什么需要 MCP

在 MCP 之前，要让 Claude Code 调 AiToEarn，得手写一段 HTTP 调用代码或装一个专用插件。MCP 把"外部服务能做什么"标准化成一份工具清单，AI 工具按清单调用即可。对 AiToEarn 来说，接入 MCP 意味着任何支持 MCP 的客户端（Claude Code、Cursor、OpenClaw 等）都能零集成成本调用它的发布、生成、撮合能力。

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

OpenClaw MCP 配置示例：

```json
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

自部署方式：

```bash
git clone https://github.com/yikart/AiToEarn.git
cd AiToEarn
docker-compose up -d
# 默认监听 http://localhost:3000
```

**注意**：自部署版**不含内容交易市场**和**官方商单撮合**——这些必须连官方 SaaS。源码里有清晰的 `LICENSE` 和 `packages/commercial/` 目录做隔离。这是作者的商业护城河：开源核心引擎，闭源撮合网络。

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

是的，但**不包括人工审核时间**。如果开启"全自动"模式（无人工），3-8 分钟覆盖 13 平台；如果开启"半自动"（每平台人工确认），实际耗时 30-60 分钟。该数字来自 README 声明，实际表现取决于网络状况和各平台 API 限流。

---

## 采用建议与适用边界

### 谁该先用

- **多平台内容运营团队**：已经在 5 个以上平台手动维护账号，每周重复"改写-排版-发布"流程，AiToEarn 能把这部分工时压缩一个数量级。
- **AI Agent 开发者**：需要在 Agent 工作流里嵌入"发布到社交平台"能力，MCP server 提供了零集成成本的接入路径。
- **有商单撮合需求的 MCN**：官方 SaaS 的撮合层可以省去自建任务匹配和结算引擎的工作。

### 谁可以等等

- **单平台运营者**：只做小红书或只做 YouTube，直接用平台官方后台更可控，AiToEarn 的多平台适配价值发挥不出来。
- **对内容原创性要求极高的品牌**：AI 生成的草稿即使经过人工 review，风格一致性仍弱于纯人工创作，品牌主账号建议谨慎。
- **需要严格数据合规的团队**：自部署版不含撮合层，但 SaaS 版的数据流向（尤其是创作者历史内容被用于风格匹配）需要单独评估合规风险。

### 接入顺序建议

1. 先用官方 SaaS 跑通"创作 → 发布"最小闭环，验证内容质量是否达标
2. 再启用 MCP server，把发布能力嵌入现有 Agent 工作流
3. 最后评估是否开启商单撮合，这一步涉及资金流，建议法务先介入
4. 若决定自部署，从 `docker-compose.yml` 入手，先跑核心三 Agent，再按需引入商业模块

---

## 自测与进阶路径

### 自测问题

以下问题可以检验你对 AiToEarn 边界的理解：

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

## 资料口径说明

为确保本文的技术准确性和适用范围清晰，特此说明以下边界：

1. **信息来源与时效性**：本文基于 2026-05-21 发布的 v2.4.0 源码与 README 整理。AiToEarn 仍在快速迭代，后续版本可能在 Agent 职责划分、MCP server 配置、PlatformAdapter 接口等方面发生变化。若你阅读时版本已更新，请以最新源码为准。
2. **技术细节验证**：文中涉及的耗时（3-8 分钟）、Token 消耗（80K-150K）、星数（+320 stars）等数字均来自 README 描述或作者公开声明，未经独立复测。实际表现取决于网络状况、平台 API 限流、内容长度和模型选择。
3. **判断与建议的边界**：本文给出的"谁该先用""谁可以等等""接入顺序建议"等判断，基于公开文档和架构分析得出，不代表 AiToEarn 官方立场，也不构成商业建议。实际技术选型请结合团队现状和评估结果。
4. **未覆盖的内容**：本文聚焦架构解读和 MCP 协议接入，未深入覆盖：自部署版 `docker-compose.yml` 的完整 12 个服务依赖配置、Monetize 撮合层的结算引擎具体实现、`packages/agent-engage/` 的调度配置细节、HappyHorse 1.0 与 Seedance 2.0 的 benchmark 对比数据。
5. **术语使用说明**：本文保留 MCP（Model Context Protocol）、SaaS（Software as a Service）、MCP server、PlatformAdapter、Docker、Claude Code、Cursor、OpenClaw 等专有名词不翻译，因为它们在 AI 工具链和开源社区中有固定英文表述。首次出现时已附中文说明。
6. **更新记录**：本文初稿基于 v2.4.0（2026-05-21），若 AiToEarn 后续版本有架构变化，将同步更新对应章节。

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
- **GitHub Trending 单日**：2026-06-04 约 +320 stars（据 Trending Shift 页面）

---

**声明**：本文基于 2026-05-21 v2.4.0 源码与 README 整理。文中涉及的耗时、Token 消耗、星数等数字来自 README 描述或作者公开声明，未经独立复测；部分 14:00 后的 GitHub 直连 URL（`github.com` 域名）受网络抖动影响未做最终核链，但 `raw.githubusercontent.com` 仓库 raw 文件 200 验证通过，README 内容真实可查。
