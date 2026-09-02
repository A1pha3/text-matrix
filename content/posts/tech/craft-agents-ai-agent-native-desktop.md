---
title: "Craft Agents：7K+ Stars 的 AI Agent 原生桌面应用——用自然语言操控 Linear/Gmail/Slack"
date: "2026-04-18T15:45:00+08:00"
slug: "craft-agents-ai-agent-native-desktop"
github_repo: "lukilabs/craft-agents-oss"
description: "Craft Agents 是 craft-ai-agents 出品的 AI Agent 开源桌面应用，基于 Agent Native 软件原则。用自然语言连接 Linear/Gmail/Slack 等外部服务（MCP / REST API / 本地文件），支持多 LLM 提供商，自带多会话收件箱、Skills 与自动化工作流，可自托管远程服务器与 CLI。"
draft: false
categories: ["技术笔记"]
topics: ["open-source-ai-tools"]
tags: ["AI Agent", "桌面应用", "MCP", "工作流自动化"]
---

# Craft Agents：7K+ Stars 的 AI Agent 原生桌面应用——用自然语言操控 Linear/Gmail/Slack

> **目标读者**：AI 助手重度用户、企业知识工作者、追求高效工作流的开发者
> **预计阅读时间**：40-50 分钟
> **前置知识**：了解 AI 助手基本概念，有 API/MCP 使用经验更佳
> **难度定位**：⭐⭐⭐⭐ 专家设计

---

## 目录

- [§1 读完能做什么](#§1-读完能做什么)
- [§2 Agent Native 软件原则](#§2-agent-native-软件原则)
- [§3 核心架构](#§3-核心架构)
- [§4 核心功能详解](#§4-核心功能详解)
- [§5 安装与快速开始](#§5-安装与快速开始)
- [§6 使用指南](#§6-使用指南)
- [§7 FAQ](#§7-faq)
- [§8 练习：连接外部服务](#§8-练习连接外部服务)
- [自测题](#自测题)
- [进阶学习路径](#进阶学习路径)

---

## §1 读完能做什么

1. 说清 Agent Native 软件原则和传统软件的区别
2. 用 Craft Agents 的多会话收件箱、Sources、Skills、MCP 集成跑通一个工作流
3. 连接 Linear/Slack/Gmail 等外部服务
4. 切换不同 LLM 提供商
5. 自己创建 Skills、配置自动化，并理解远程服务器与 CLI 的使用

---

## §2 Agent Native 软件原则

### 2.1 传统软件的局限

传统软件（如 Notion/Slack/Linear）设计时假设"人类是操作者"，一切交互都建立在按钮、表单和配置界面上。当 AI Agent 介入时，它需要把人类操作翻译成一连串命令：

- 需要将操作分解为 API 调用
- 需要维护上下文状态
- 需要处理错误恢复

这一层翻译工作，通常落到了复杂的 SDK、配置文件和维护成本上。

### 2.2 Agent Native 的做法

Agent Native 软件的设计出发点正好相反——把"描述目标"交给用户，把"如何执行"交给 Agent：

- **自然语言优先**：用户描述目标，AI 理解意图并执行
- **工具即服务**：外部能力通过 Skills/Sources 即插即用
- **无配置体验**：不用手写配置文件，不用重启
- **变更即时生效**：改动通过对话完成，而非改代码

### 2.3 Craft Agents 的实践

Craft Agents 是首批基于 Agent Native 原则设计的桌面应用之一，官方称其"是这类产品里的第一批"（one of the first of its kind）。它用 AI 的视角重新设计工作流，让 Agent 可以直接"驾驶"软件，而不是绕着一堆配置界面打转。

---

## §3 核心架构

### 3.1 整体架构

Craft Agents 采用 monorepo 结构，桌面端是其中一条主力入口：

```
craft-agent/ (monorepo)
├── apps/
│   ├── electron/   # 桌面 GUI（主入口）
│   │   └── src/
│   │       ├── main/       # Electron 主进程
│   │       ├── preload/    # 上下文桥接 (context bridge)
│   │       └── renderer/   # React UI（Vite + shadcn）
│   └── cli/         # 终端客户端（连接本地或远程 Server）
└── packages/
    ├── server/      # 独立服务端（支持无头服务器 headless）
    ├── core/        # 共享类型
    └── shared/      # 业务逻辑（agent/权限、auth、config、credentials 等）
```

UI 层之下，是负责推理与执行的 Agent 引擎；引擎之下，是连接外部世界的 Integration Layer（Sources + Skills + MCP Servers）。

### 3.2 Agent 引擎

Craft Agents 的 Agent 引擎建立在两大支柱之上：

- **Claude Agent SDK**：Anthropic 官方 Agent 开发工具链，和 Claude Code 同源，负责核心推理与工具调用
- **Pi SDK**：与 Claude Agent SDK **并联**使用（side by side），在官方能力之上补充 Craft 认为值得改进的部分

官方在 README 里坦言：这套工具是 craft.do 团队"给自己用"而建的，用 Claude 生态里最好的部分，再补上他们想要的改进。它还强调一个细节——**Craft Agents 自身也是用 Craft Agents 写出来的**（"building with Craft Agents only, no code editors"），所以"任何自定义都只是一句 prompt 的事"。这个理念贯穿产品设计。

### 3.3 Sources 系统

Sources 是把外部能力接进工作区的方式：

| Source 类型 | 示例 | 实现方式 |
|-----------|------|----------|
| **MCP Servers** | Craft、Linear、GitHub、Notion | 标准 MCP 协议 |
| **REST APIs** | Google（Gmail、Calendar、Drive）、Slack、Microsoft | OpenAPI 规范 / 自定义端点 |
| **本地文件** | 文件系统、Obsidian 库、Git 仓库 | Stdio MCP |

连接过程也是自然的——直接在对话里说：

```
用户：添加 Linear 作为 Source
AI → 发现 Linear 的公共 API 和 MCP 服务器 → 读文档 → 配置凭据 → 完成连接
```

一条会话里可以同时拉取 Linear 的 issue、参考 GitHub 的代码、翻 Slack 的讨论，再汇总到一篇 Craft 文档里。

---

## §4 核心功能详解

### 4.1 多会话收件箱（Multi-Session Inbox）

桌面端默认进入一种"收件箱 + 任务管理器"式界面。每个会话有自己的**状态工作流**：`Todo → In Progress → Needs Review → Done`，可以标记（Flag）、归档、重命名（支持 AI 自动命名）。会话历史完整落盘，进程重启后依然能接着聊——这正好对应 §2 里"把会话当文档"的设计意图。

### 4.2 多 LLM 提供商

不止 Anthropic，可以同时配置多个 Provider，并按工作区设置默认 LLM：

| 提供商 | 支持情况 |
|--------|----------|
| **Anthropic**（Claude） | ✅ 官方集成（API key 或 Claude Max） |
| **Google AI Studio** | ✅ |
| **ChatGPT Plus** | ✅（Codex OAuth） |
| **GitHub Copilot** | ✅（OAuth） |
| **OpenAI API** | ✅ |
| **自定义**（--base-url） | ✅ |

每个工作区可设置默认 LLM，会话级也可以灵活切换。

### 4.3 Craft MCP 集成

Craft 自家平台通过 MCP 协议向 Agent 开放 **32+ 个文档工具**，涵盖：

- **Blocks 操作**：创建、编辑、删除文档块
- **Collections 管理**：管理文档集合与分类
- **搜索**：全文搜索与语义搜索
- **Tasks**：任务创建、分配与追踪

### 4.4 Skills 系统

Skills 是"存于工作区的专用 Agent 指令"，本质是 `YAML frontmatter + markdown` 的可复用指令文件，用 `@` 提及即可调用。创建和迁移都是对话式的：

```
用户：创建一个 GitHub PR 审查 Skill
AI → 理解需求 → 生成 Skill 定义 → 保存到工作区
```

```
用户：从 Claude Code 导入我的 Skills
AI → 发现 Claude Code 配置 → 迁移所有 Skills
```

变更即时生效，同一段对话中就能用上刚刚创建的 Skill。

### 4.5 权限模式（Permission Modes）

三级权限系统，覆盖从"只读探索"到"完全自治"的信任梯度，**默认是 Ask to Edit**：

| 模式 | 界面显示 | 行为 | 适用场景 |
|------|---------|------|----------|
| `safe` | Explore | 只读，拦截所有写操作 | 新接触、只许查 |
| `ask` | Ask to Edit | 执行前逐一确认（默认） | 谨慎场景 |
| `allow-all` | Auto | 自动批准所有命令 | 信任环境 |

担心切来切去麻烦？会话输入框用 **SHIFT+TAB** 即可循环切换模式，不用点菜单。

### 4.6 自动化（Automations）

基于事件的触发器，让 Agent 不用你开口就动起来：

- **Label 变更时** 创建会话
- **定时执行**
- **工具使用时触发**

配合多会话收件箱，长任务可以在后台挂着，你做别的事。

### 4.7 键盘快捷键

日常高频操作都有快捷键：

| 快捷键 | 动作 |
|--------|------|
| `Cmd+N` | 新建会话 |
| `Cmd+1/2/3` | 聚焦侧栏/列表/对话 |
| `Cmd+/` | 快捷键帮助 |
| `SHIFT+TAB` | 循环权限模式 |
| `Shift+Enter` | 换行（Enter 发送） |

---

## §5 安装与快速开始

### 5.1 一键安装

**macOS/Linux**：

```bash
curl -fsSL https://agents.craft.do/install-app.sh | bash
```

**Windows（PowerShell）**：

```powershell
irm https://agents.craft.do/install-app.ps1 | iex
```

### 5.2 源码构建

```bash
git clone https://github.com/lukilabs/craft-agents-oss.git
cd craft-agents-oss
bun install
bun run electron:start
```

### 5.3 依赖要求

- Node.js
- Bun（用于开发）
- Electron

### 5.4 首次启动流程

1. 启动应用
2. 选择 LLM 连接：Anthropic（API key / Claude Max）、Google AI Studio、ChatGPT Plus 或 GitHub Copilot OAuth
3. 创建工作区，用于组织会话
4. （可选）连接 Sources：MCP 服务器、REST API 或本地文件
5. 开始对话

---

## §6 使用指南

### 6.1 连接 MCP 服务

**已有 MCP 配置 JSON？** 直接粘贴，AI 处理剩余配置。

**本地 MCP 服务器？** 完全支持 stdio 模式，指向 npx 命令、Python 脚本或任意本地二进制，Agent 以本地子进程运行它。

### 6.2 连接 REST API

**自定义 API？** 直接粘贴 OpenAPI 规范、端点 URL 甚至文档截图，AI 理解后引导完成配置。官方举例甚至接了一台 jumpbox 后面的 Postgres——"Skills + Sources = magic"。

### 6.3 多文件 diff

打开 VS Code 风格窗口，逐个 Turn 查看文件变更，审阅 Agent 的改动再决定要不要采用——这和 §4.5 的权限模式配合，构成"进出可审"的闭环。

### 6.4 远程服务器（Headless）与 CLI

值得单列的是：Craft Agents 不止是本地桌面应用，还可以跑成**无头服务端**，桌面端退化为瘦客户端。在远程机器（如一台 Linux VPS）上：

```bash
CRAFT_SERVER_TOKEN=$(openssl rand -hex 32) bun run packages/server/src/index.ts
```

启动后服务端打印 `CRAFT_SERVER_URL` 与会话 token，桌面端用 `CRAFT_SERVER_URL + CRAFT_SERVER_TOKEN` 以瘦客户端模式连接（thin-client）：UI 在本地渲染，但会话逻辑、工具调用和 LLM 请求全部在远端完成。好处是：长会话常驻、可多机访问、重计算任务交给强机器。跨网络暴露时务必用 `wss://`（TLS），可挂反代（nginx/Caddy）终结 TLS。

若连图形界面都不想开，可以用配套的 **CLI 客户端**（`apps/cli`）走 WebSocket 脚本化操作：`ping`、`health`、建会话、发消息流式接收、查看版本。其中自洽的 `run` 命令会自动拉起一个临时服务端、建会话、跑 prompt、流式返回再退出，典型的 CI/CD 或服务器校验场景不用单独起服务：

```bash
craft-cli run "Summarize the README"
craft-cli run --provider openai --model gpt-4o "Summarize this repo"
craft-cli --validate-server   # 21 步集成自检
```

---

## §7 FAQ

### Q1: Craft Agents 免费吗？

核心代码开源免费（Apache-2.0 许可证），可以自由 remix 和改动——README 甚至说"真的改得动"，因为团队自己就是这么用它开发它自己的。Craft 云服务另有付费计划，覆盖协作和团队管理能力。

### Q2: 与 Claude Code 有何区别？

两者共享同一底座（Claude Agent SDK），但定位不同：

| 特性 | Craft Agents | Claude Code |
|------|---------------|-------------|
| 界面 | 图形桌面应用 | 终端 CLI（Craft 是"更想要非 CLI 方式"的产物） |
| 数据源 | MCP + REST API + 本地文件 | 以 MCP 服务器为主 |
| 会话组织 | 收件箱 + 自定义状态工作流 | `.claude/` 按项目配置、`-c` 续接 |
| 配置范围 | 多工作区 | 单项目 |

### Q3: Sources 支持多少种服务？

核心是三类：任何兼容 MCP 协议的服务、任何提供 REST API 的服务、以及本地文件系统。具体数量取决于社区贡献和维护状态，官方口径是"连接到任何有 API 的东西"。

### Q4: 支持本地 MCP 服务器吗？

完全支持。stdio 模式的 MCP 服务器以本地子进程运行，可指向 npx 命令、Python 脚本或任意本地二进制。

### Q5: 如何导入 Claude Code 的 Skills？

在对话里告诉 Agent：

```
导入我在 Claude Code 的 Skills
```

Agent 会自动发现并迁移你的 Skills 配置。

### Q6: 数据存储在哪里？

这是本地优先的桌面应用：会话历史默认**落盘保存**（持久化到本地目录），不是默认传到云端。它也能自托管——无头服务器模式下，会话在你自己控制的远端持久化，桌面端只是瘦客户端。是否对接 craft.do 托管服务，取决于你的部署方式与配置。

### Q7: 支持中文界面？

界面默认以英文为主。不过界面主题、会话状态都是可配置的（Statuses / Themes 皆可通过对话调整），因此可以做一定程度的本地化定制；官方并未承诺中文版本，具体以发布说明为准。

---

## §8 练习：连接外部服务

### 练习目标

使用 Craft Agents 连接一个真实的外部服务（以 GitHub 为例）

**前置准备**：

- 已安装 Craft Agents
- 拥有 GitHub 账号
- 有一个可访问的 GitHub 仓库

### 详细步骤

**Step 1：安装并启动**

```bash
# macOS/Linux
curl -fsSL https://agents.craft.do/install-app.sh | bash

# Windows
irm https://agents.craft.do/install-app.ps1 | iex
```

**Step 2：首次配置**

1. 启动 Craft Agents
2. 创建新工作区
3. 选择默认 LLM（推荐 Claude）

**Step 3：连接 GitHub**

在 Craft Agents 对话框中输入：

```
添加 GitHub 作为 Source
```

Craft Agents 会引导你完成：

- 选择 GitHub MCP 服务器
- 完成 OAuth 授权
- 选择要访问的仓库权限

**Step 4：验证连接**

输入：

```
列出我的 GitHub 仓库
```

你应该能看到仓库列表。

**Step 5：执行实际操作**

输入：

```
为我的第一个仓库创建一个新 issue
```

### 验证标准

- [ ] 成功完成 GitHub OAuth 授权
- [ ] Agent 能列出你的仓库
- [ ] Agent 成功创建了 Issue
- [ ] 可以在 GitHub 网页上看到创建的 Issue

**进阶挑战**：

- 让 Agent 审查一个 PR
- 让 Agent 总结某个 Issue 的讨论

---

## 自测题

完成以下自测题，检查你对 Craft Agents 的理解。

### 基础概念

**问题 1**：Agent Native 软件和传统软件的区别是什么？

<details>
<summary>点击查看答案</summary>

传统软件假设"人类是操作者"，AI Agent 介入时需要把操作翻译成 API 调用、维护上下文状态、处理错误恢复。Agent Native 软件反过来——把"描述目标"交给用户，把"如何执行"交给 Agent：
- 自然语言优先：用户描述目标，AI 理解意图并执行
- 工具即服务：外部能力通过 Skills/Sources 即插即用
- 无配置体验：不用编辑配置文件，不用重启
- 变更即时生效
</details>

**问题 2**：Craft Agents 的 Agent 引擎建立在哪两大支柱之上？

<details>
<summary>点击查看答案</summary>

1. **Claude Agent SDK**：Anthropic 官方工具链，与 Claude Code 同源，负责核心推理与工具调用
2. **Pi SDK**：与 Claude Agent SDK 并联使用，补充官方能力之外的部分
</details>

**问题 3**：Sources 系统支持哪些类型？

<details>
<summary>点击查看答案</summary>

| Source 类型 | 示例 | 实现方式 |
|-----------|------|----------|
| **MCP Servers** | Craft、Linear、GitHub | 标准 MCP 协议 |
| **REST APIs** | Google、Slack、Microsoft | OpenAPI / 自定义端点 |
| **本地文件** | 文件系统、Obsidian、Git 仓库 | Stdio MCP |
</details>

### 技术实现

**问题 4**：权限模式有哪几种？默认是哪一种？

<details>
<summary>点击查看答案</summary>

| 模式 | 界面显示 | 行为 |
|------|---------|------|
| `safe` | Explore | 只读，拦截所有写操作 |
| `ask` | Ask to Edit | 执行前逐一确认（**默认**） |
| `allow-all` | Auto | 自动批准所有命令 |

会话中按 `SHIFT+TAB` 即可循环切换。
</details>

**问题 5**：如何导入 Claude Code 的 Skills？

<details>
<summary>点击查看答案</summary>

在 Craft Agents 对话里告诉 Agent：
```
导入我在 Claude Code 的 Skills
```
Agent 会自动发现并迁移你的 Skills 配置。
</details>

**问题 6**：Craft Agents 支持哪些 LLM 提供商？

<details>
<summary>点击查看答案</summary>

- Anthropic（Claude，官方集成）
- Google AI Studio
- ChatGPT Plus（Codex OAuth）
- GitHub Copilot（OAuth）
- OpenAI API
- 自定义（--base-url）

每个工作区可设置默认 LLM。
</details>

### 进阶

**问题 7**：Craft Agents 可以脱离图形界面使用吗？

<details>
<summary>点击查看答案</summary>

可以。两种方式：
1. **无头服务器**：`packages/server` 提供 headless 服务端，桌面端作瘦客户端连接；跨网络用 `wss://`（TLS）
2. **CLI 客户端**：`apps/cli` 通过 WebSocket 脚本化操作，`run` 命令可自洽拉起一次会话完成任务
</details>

---

## 进阶学习路径

当你掌握 Craft Agents 的基础使用后，可以按以下路径继续深入。

### 初级阶段（已完成基础使用）

- ✅ 完成 GitHub 连接练习（§8）
- ✅ 理解 Agent Native 软件原则
- ✅ 能配置 Sources 和 Skills

### 中级阶段（生产就绪）

- 📚 **创建自定义 Skills**：为你的工作流创建专属 Skills
- 📚 **配置自动化**：基于事件的触发器（Label 变更、定时执行、工具使用时触发）
- 📚 **多工作区管理**：为不同项目配置不同的 Agents 和 Skills
- 📚 **权限模式调优**：默认 Ask to Edit，按团队习惯选 `safe` / `allow-all`

### 高级阶段（平台贡献者）

- 🚀 **开发 MCP 服务器**：为 Craft Agents 开发新的 Sources
- 🚀 **贡献 Skills**：分享你的 Skills 到社区
- 🚀 **搭建远程服务器**：跑无头 server + CLI，接入 CI/CD 或服务器自动化
- 🚀 **参与开源**：贡献到 [craft-agents-oss](https://github.com/craft-ai-agents/craft-agents-oss)

### 相关深入学习资源

| 方向 | 推荐资源 |
|------|----------|
| **MCP 协议** | [Model Context Protocol 文档](https://modelcontextprotocol.io/) |
| **Claude Agent SDK** | Anthropic 官方文档 |
| **Agent 设计模式** | LangChain 官方博客、Andrew Ng 课程 |
| **工作流自动化** | Zapier、n8n 文档（参考自动化设计） |

---

## §9 相关资源

- [GitHub 仓库](https://github.com/craft-ai-agents/craft-agents-oss)
- [官方文档](https://agents.craft.do/docs/getting-started/introduction)
- [视频演示](https://www.youtube.com/watch?v=xQouiAIilvU)
- [Discord 社区](https://discord.gg/jn4EGJjrvv)

---

*🦞 撰写于 2026 年 4 月 18 日；数据基于仓库当期 README 与 GitHub 信息核验更新*