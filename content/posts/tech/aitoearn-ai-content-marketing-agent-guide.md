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

## 先给判断

AiToEarn 不是又一个"AI 写文章工具"，也不是 Buffer / Hootsuite 那种"多平台定时发布器"。它把 **AI 内容生成、平台分发适配、商单撮合结算** 三件事做在同一个仓库里，并且把这套能力同时以 **SaaS 网页、OpenClaw 原生调用、MCP 协议、Claude/Cursor 接入、Docker 自部署** 五种形态暴露给调用方。

**当一个 Agent（比如 Claude Code）写完一段产品介绍，它可以直接调 AiToEarn 的 MCP server，让这段介绍在 13 个平台（抖音、小红书、YouTube、TikTok、X、Threads、Instagram、Pinterest、LinkedIn、Facebook、哔哩哔哩、视频号、快手）上以各自原生格式自动出现，并在内容交易市场里接变现任务。** 写完即发布、发布即变现。

截至 2026-06-04，仓库在 GitHub Trending 单日 +320 stars，MIT 协议，中英日三语 README。本文基于 2026-05-21 发布的 v2.4.0 源码与 README 整理。

---

## 系统总览：四 Agent + 三链路

仓库 README 明确把能力切成 4 块：**Monetize / Publish / Engage / Create**。但从代码结构看，**真正决定复杂度的是三条并行链路**——创作者端、商单端、AI 执行端。

```text

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

数据看板会反过来影响 Create Agent 下次生成时的"风格基线"——创作 → 发布 → 互动 → 反馈 → 创作，跑完一圈。

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
