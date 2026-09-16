---
title: "Rowboat：将工作沉淀为知识图谱的本地优先 AI 同事"
slug: "rowboat-ai-knowledge-graph-coworker-guide"
github_repo: "rowboatlabs/rowboat"
source_key: "gh:rowboatlabs/rowboat"
description: "深入解析 Rowboat——Apache-2.0 开源、本地优先的 AI 同事：把邮件、会议、Slack 沉淀为带背链的 Markdown 知识图谱，数据留在本机，可自行接入任意模型。"
date: "2026-04-11T00:00:00+08:00"
categories: ["技术笔记"]
tags: ["知识图谱", "Obsidian", "LLM", "Claude", "MCP", "本地优先", "rowboat"]
---

# Rowboat：将工作沉淀为知识图谱的本地优先 AI 同事

## 1 这篇文章解决什么问题

AI 助手只有拿到够用的上下文才有价值。多数工具是在你提问时去检索历史记录，把邮件、文档、通话记录一次性丢给模型，既慢又有信息损耗，而且你只能问出你想到的问题。Rowboat 走的是另一条路：它先在本地把工作素材沉淀成一张持续更新的知识图谱，再让助手在这个图谱上替你干活。

读完你会知道：

- Rowboat 的定位与「本地优先 + Obsidian 风格知识图谱」是什么意思
- Brain 记忆、Email、Meeting Notes、Browser、Code Mode、Apps 各自做什么
- 多人协作部分 Space 与自托管服务器 Harbor 的关系
- 如何安装、接模型（本地 Ollama / LM Studio 或自带 API（应用程序接口）Key）
- 如何通过 MCP 扩展外部工具；哪些能力成熟、哪些还在迭代

## 2 项目概述

[Rowboat](https://github.com/rowboatlabs/rowboat) 是开源、本地优先（local-first）的 AI 同事（AI coworker），Apache-2.0 许可。它把邮件、会议、Slack、对话记录提炼成普通 Markdown 笔记，笔记之间用背链相互连接，供助手持续使用。所有个人数据都留在本机，不绑定某个云端账号。

| 项目 | 信息 |
|------|------|
| 仓库 | [rowboatlabs/rowboat](https://github.com/rowboatlabs/rowboat) |
| 许可证 | Apache-2.0 |
| 定位 | 开源的多人 AI 工作助手，本地优先 |
| 安装方式 | 桌面应用，提供 Mac / Windows / Linux 下载 |
| 模型接入 | Ollama、LM Studio 本地模型，或自带 API Key 的托管模型 |

它采用客户端与服务器同仓的结构：`apps/x` 是桌面端（Electron）、无头的 `rowboat-server` 与手机端；`apps/harbor` 是 Spaces 服务器。项目在 2026 年初上线时登顶过 GitHub Trending。

### 2.1 核心理念：先沉淀记忆，再替你干活

Rowboat 的出发点很直接：检索式工具只能回答你想到的问题，而一份会积累的上下文能追踪跨对话的决策、承诺与关系，还能浮现你没意识到要问的模式。它的工作由两部分组成：

1. **动态上下文图（Brain）**：连接 Gmail 与会议笔记（如 Granola、Fireflies），抽取决策、承诺、截止日期和人物关系，写成本地可编辑、用 `[[wikilink]]` 关联的 Markdown。新对话（包括语音随记）进来，相关笔记自动更新。某个截止日期在站会里改了，它会回溯到最初的承诺并同步更新。
2. **本地助手**：在这张图上，Rowboat 带一个有本机 shell 访问权限、支持 MCP 的智能体，能按需执行，也能跑定时后台任务。

一句话总结它在解决什么问题：不把海量邮件和过程性材料每次原样塞给模型，而是让有用的上下文先沉淀下来、再复用。

## 3 Brain：知识图谱是怎么长出来的

### 3.1 长什么样子

Rowboat 记忆的每一份内容都是一个纯 Markdown 文件。这些文件对 Obsidian 兼容，用 `[[wikilink]]` 相互关联——打开 Obsidian 就能读、能改。没有专有 schema（数据结构），也就不被任何托管服务锁定。

```markdown
# Sarah Chen

## Activity Log
- Jan 16: Sent term sheet draft, wants to close by Friday
- Jan 14: Sent partnership proposal
- Jan 12: Intro call — interested in Series B
```

人物、公司、项目、主题会变成图谱里的节点。上游来源更新时，相关笔记跟着刷新，不需要你手动整理。这也意味着知识图谱的质量直接取决于上游数据的完整性：邮件、会议转录进来得越全，关联越靠谱。

### 3.2 为什么用图谱而不是向量库

Rowboat 的判断是：对个人工作记忆来说，一张可遍历的知识图谱比嵌入向量（embedding）的检索精度更划算，去掉向量库还能降低本地运行的硬件与运维成本。代价是检索质量依赖链接密度——图里链接越密，召回越准；笔记之间缺少关联时，图谱的价值就打折扣。这是它与 GraphRAG 这类"图 + 向量"混合方案的取舍，不是简单的高下之分。

## 4 内置工作台

### 4.1 邮件（Email）

自带邮件客户端。把收件箱分流成「重要」与「其他」，并自动为重要的邮件起草回复，草稿会用到你对上下文的理解：过往笔记、会议、历史线程。你编辑或发送草稿时，它从你的改动里学习，让下一次草稿更像你写的。

### 4.2 会议笔记（Meeting Notes）

本地会议记录器，接麦克风和扬声器，不需要机器人进会。开会时给实时转写，会后生成 Markdown 摘要和行动项，并同步刷新 Brain。与会相关的人和事，其笔记会随会议结束自动更新。

### 4.3 内置浏览器（Browser）

Rowboat 带一个浏览器，你和助手可以一起处理网页任务。它与你日常浏览器隔离，只登录你希望助手访问的账号——想在网页上给助手开几个受限账号，而不把你的主账号暴露给它。

### 4.4 后台智能体（Background Agents）

可以配置按事件触发（如新邮件、会议结束）或按计划运行的常驻智能体。它们能联网搜索、驱动内置浏览器、连接工具，也能用 Claude Code 或 Codex 写代码。分类收件箱、跟进会议、写投资人周报这类事可以挂着让它干，出活后你再审。

### 4.5 编码模式（Code Mode）

用 Claude Code 或 Codex 拉起并行编码智能体，由 Rowboat 用工作上下文驱动它们。少量需求即可建立分支和可审查的 diff，避免把工作背景重新解释一遍。

### 4.6 应用（Apps）

向 Rowboat 的助手描述一个个人应用（融资 CRM、现金流跟踪、客户健康看板之类），它会在 Rowboat 内构建一个本地运行的小型 Web 应用，由智能体和你的数据持续更新。这样一些临时性看板不必自建系统。

## 5 多人协作：Space 与 Harbor

> 如果你只需要单机使用，这一节的优先级不高。多人或想把「提问与文件共享」放到一个房间时再往下看。

Space 是它多人协作的部分：一个频道加一个共享文件夹。消息、线程、私信、反应、投票、定时消息、@mention 在一侧；Markdown 渲染的 wiki、上传与白板在另一侧。对话、想法、知识与工作本身放在同一处。

每个成员在自己的机器上跑各自版本的 Rowboat，拥有自己的工作记忆与模型密钥。在 Space 里输入 `@rowboat`，只会唤起你本机的 Rowboat，用你自己的上下文处理，再把结果以「你的名字（via Rowboat）」发回房间。它读到的数据始终留在你机器上，需要发送的内容必须经过你显式选择。

**Space 由名为 Harbor 的小型服务器承载**，开源、在本仓库的 `apps/harbor` 下。它有一个核心加三扇门：HTTP、WebSocket 和 MCP 服务器。Rowboat 自己的智能体不享特权路径，跟任何外部智能体一样从 MCP 这道门进入——所以别的智能体能做的事，你自带的智能体也能做。

### 5.1 隐私规则

它进 Space 的内容会出现在团队面前，它读到的内容可能只属于你，因此有几条默认约束：

- 只读任务需要的内容，不读无关数据。
- 只回答被问的问题，沿途看到的文件、私信、邮件不进回复。
- 私人内容跨到共享端时只以摘要形式发生，且仅在应请求时。它从不把邮件或聊天原文粘进 Space。
- 回执说明它做了什么，而不是它读到了什么。

### 5.2 如何得到一个 Space 与自托管 Harbor

- **创建服务器**：应用内打开 Spaces → *Create a server*，用 Rowboat 账号登录，就有一个托管服务器和第一个 Space；用 *Copy invite link* 拉同事。
- **加入服务器**：粘贴邀请链接，注册绑定成员关系；服务器可限定某个邮箱域名。
- **自托管 Harbor**：源码在仓库 `apps/harbor`，本地跑通只需几分钟，`DATABASE_URL` 让它持久化：

```bash
cd apps/harbor
pnpm install && pnpm build
cd packages/server && pnpm dev
```

开发入口会启动一个带种子数据（一个小团队和一个 Roadboard Space）的内存 Harbor，端口 4272，用开发者令牌替换真实登录。在应用里打开 Spaces → *Add a dev server*，指向 `http://localhost:4272` 并填一个种子成员 ID 即可。

生产部署走 `apps/harbor/Dockerfile`，以组织（org）对应主机名建号、用 OpenID Connect（OIDC）登录、新成员只能通过接受邀请加入。关键环境变量如下：

| 变量 | 作用 |
|------|------|
| `HARBOR_MODE=deployment` | 多组织模式，按请求主机解析归属 |
| `DATABASE_URL` | Postgres，版本化追加式迁移 |
| `APEX_DOMAIN` | 组织地址形如 `<slug>.<APEX_DOMAIN>` |
| `AUTH_ISSUER` | 受信任的 OIDC 颁发者（JWKS 校验），缺省回退为不应公开的开发令牌 |
| `AUTH_PUBLISHABLE_KEY` | 启用登录/授权页（社交登录） |
| `HARBOR_ALLOWED_DOMAINS` | 允许接受邀请的邮箱域名（单组织模式） |
| `BLOBS_DIR` 或 `BLOBS_S3_BUCKET` | 上传存储位置：本地或任意 S3 兼容桶 |
| `PORT` | 端口，默认 4272 |

任何组织都在 `https://<org address>/mcp` 暴露一个 MCP 服务器（streamable HTTP），与它内置的智能体共用同一接口。Harbor 发布 OAuth 保护资源元数据，讲 OAuth 2.1 的 MCP 客户端可自行发现登录流程。用 Claude Code 接入一个 Space 大致如此：

```bash
claude mcp add --transport http my-team https://<org address>/mcp
```

> 该协议仍在 v0，`apps/harbor/CONTRACT.md` 是其说明文档，包含合并语义、邀请流程和仍需打磨之处，接口可能发生破坏性变更。

## 6 安装与配置

### 6.1 安装

Rowboat 以桌面应用形式分发，不是命令行工具。从 [rowboatlabs.com/downloads](https://www.rowboatlabs.com/downloads) 下载对应系统的安装包（Mac / Windows / Linux 的 `.deb` 等），所有历史版本在 [GitHub Releases](https://github.com/rowboatlabs/rowboat/releases/latest)。

**Google 服务（Gmail、Calendar、Drive）**接入按仓库内 [google-setup.md](https://github.com/rowboatlabs/rowboat/blob/main/google-setup.md) 操作。

### 6.2 可选功能与 API Key

可选能力统一放在 `~/.rowboat/config/` 下，每个文件只放一个 JSON 键值对：

```json
{
  "apiKey": "<key>"
}
```

| 能力 | 配置文件 | 说明 |
|------|----------|------|
| 语音输入 / 语音随记 | `~/.rowboat/config/deepgram.json` | Deepgram API Key，可选 |
| 语音输出 | `~/.rowboat/config/elevenlabs.json` | ElevenLabs API Key，可选 |
| 网页搜索 | `~/.rowboat/config/exa-search.json` | Exa 研究搜索 API Key，可选 |
| 外部工具 | `~/.rowboat/config/composio.json` | Composio 工具与任意 MCP 服务器，可选 |

### 6.3 换模型（Bring Your Own Model）

Rowboat 不绑定供应商：本地模型走 Ollama 或 LM Studio，托管模型用你自己带的 API Key / 服务商。可以随时切换，数据始终留在本地的 Markdown 库，也不需要把密钥共享给同事。

## 7 MCP 集成：把外部工具接进来

最重要的一条扩展路径是 **MCP**。借此可接入搜索、数据库、CRM、客服、自动化与内部工具。README 列出的接入示例包括 Exa（网页搜索）、Twitter/X、ElevenLabs（语音）、Slack、Linear/Jira、GitHub 等。

以接入一个无需账号的网页搜索 MCP 为例：打开 **Settings → MCP Servers**，在现有 `mcpServers` 对象里加一条并保存：

```json
{
  "mcpServers": {
    "parallel": {
      "url": "https://search.parallel.ai/mcp"
    }
  }
}
```

该配置经由 Rowboat 现有的 Streamable HTTP 客户端连接。保存后让助手把 `parallel` 服务器上可用工具列出来，再试一次要求它用 Parallel 查找官方 MCP 文档。Rowboat 的工作中会调用这些工具，受你设置的 MCP 权限约束；查询内容、请求的 URL 与上下文会发送给 Parallel。要移除就删掉这条并保存。

## 8 局限与适用场景

**适用的人**：希望 AI 持续积累对邮件、会议与项目背景的理解，且在意数据不出本机、不绑定订阅的个人或团队；尤其适合决策、承诺、关系比较密集的工作。

**局限**：

- 知识图谱质量依赖上游数据完整性：邮件与会议转录不完整时，关联会失真。
- 纯图检索优于向量搜索的前提是链接足够密；笔记之间很少相互关联时，召回会变弱。
- Spaces/Harbor 协议仍是 v0，自托管会遇到破坏性变更。
- 语音、语音输出、网页搜索等能力依赖外部 API Key，真正的全离线语音体验需要自备模型与密钥。

**值得先试用再决定**。行前先跑通官方的交互式 demo，再在一个真实小团队（或一个自用 DM）里试两周，确认它读、写数据的边界符合你的隐私预期。

## 9 参考资料

- 官方站点：[rowboatlabs.com](https://www.rowboatlabs.com)
- 源码与 README：[rowboatlabs/rowboat](https://github.com/rowboatlabs/rowboat)
- Google 接入：[google-setup.md](https://github.com/rowboatlabs/rowboat/blob/main/google-setup.md)
- 演示视频：[知识图谱 demo](https://www.youtube.com/watch?v=7xTpciZCfpw)、[Apps→编码 demo](https://www.youtube.com/watch?v=et5yQABJ3xI)