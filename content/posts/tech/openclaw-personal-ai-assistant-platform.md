---
title: "OpenClaw：本地优先的个人 AI 助手平台"
date: "2026-04-27T15:00:00+08:00"
slug: "openclaw-personal-ai-assistant-platform"
description: "OpenClaw 是 GitHub 上备受关注的开源个人 AI 助手项目，支持 20+ 消息渠道、语音交互和 Live Canvas，可运行在 macOS/iOS/Android 等设备上。本文从架构视角解析 OpenClaw 的 Gateway 设计、多渠道消息路由、技能系统与安全沙箱模型。"
draft: false
categories: ["技术笔记"]
tags: ["OpenClaw", "AI助手", "TypeScript", "多渠道", "本地优先", "AI Agent"]
---

# OpenClaw：本地优先的个人 AI 助手平台

## 学习目标

- 理解 OpenClaw 的 Gateway 架构及其在整体系统中的角色
- 掌握 OpenClaw 的多渠道消息路由机制
- 了解技能（Skills）系统的设计思路和扩展方式
- 认识 OpenClaw 的安全模型：默认安全与沙箱隔离
- 理解 OpenClaw 与传统聊天机器人的核心区别

---

## 1. 项目概览

**OpenClaw** 是一个开源的个人 AI 助手平台，让用户能够在自己的设备上运行完全属于自己的 AI 助手。它不依赖任何云端服务（除必要的模型 API），所有对话、文件、配置都存储在本地。

OpenClaw 的核心理念：**设备自主、数据私有、渠道多样**。

OpenClaw 的核心数据：

| 指标 | 数值 |
|------|------|
| GitHub Stars | 364,936 |
| GitHub Forks | 74,731 |
| 主要语言 | TypeScript |
| License | MIT |
| 主要作者 | Peter Steinberger (@steipete) |
| 运行时要求 | Node.js 24（推荐）或 Node.js 22.14+ |
| 支持平台 | macOS, Linux, Windows (WSL2), iOS, Android |

OpenClaw 的吉祥物是太空龙虾（space lobster），项目最初为 **Molty**（一只太空龙虾 AI 助手）开发，后来演化为通用平台。项目已获得 OpenAI、GitHub、NVIDIA、Vercel、Blacksmith、Convex 等公司的赞助。

---

## 2. 架构总览：Gateway 是控制平面

OpenClaw 的架构分为两部分：

- **Gateway（网关）**：整个系统的控制平面，管理会话、渠道、工具和事件。它是一个长期运行的守护进程（daemon），通过 launchd（macOS）或 systemd（Linux）启动。
- **Assistant（助手）**：运行在 Gateway 之上的 AI 能力层，处理对话、记忆、技能调用等。

用一句话总结：**Gateway 是控制面板，产品是助手本身**。

安装 Gateway 的标准方式是：

```bash
npm install -g openclaw@latest
openclaw onboard --install-daemon
```

`openclaw onboard` 会引导用户完成 Gateway 设置、渠道配置和技能安装。

---

## 3. 多渠道消息路由

OpenClaw 最有特色的能力之一是**多渠道接入**——它支持同时连接 20+ 消息平台，同一个 AI 助手可以在所有这些渠道上回应用户。

### 3.1 支持的渠道

文本渠道：
- 即时通讯：WhatsApp, Telegram, Signal, iMessage, Microsoft Teams, IRC, Matrix, Feishu（飞书）, LINE, Mattermost, Nostr, Synology Chat, WeChat, QQ
- 社交/协作：Slack, Discord, Google Chat, Twilio, WebChat

语音渠道：
- macOS / iOS：Voice Wake（语音唤醒词）+ Talk Mode
- Android：Voice Wake + 连续语音识别（ElevenLabs + 系统 TTS fallback）

其他：
- macOS 原生应用（菜单栏 + Voice Wake）
- Live Canvas（可视化工作空间）
- Web 端（WebChat）

### 3.2 渠道配置

每个渠道在 `~/.openclaw/openclaw.json` 中独立配置：

```json5
{
  channels: {
    telegram: {
      enabled: true,
      botToken: "YOUR_BOT_TOKEN",
      dmPolicy: "pairing",  // 默认要求配对
    },
    feishu: {
      enabled: true,
      appId: "YOUR_APP_ID",
      appSecret: "YOUR_APP_SECRET",
    },
    discord: {
      enabled: true,
      botToken: "YOUR_DISCORD_BOT_TOKEN",
      dmPolicy: "pairing",
    },
  },
}
```

### 3.3 DM 安全策略

OpenClaw 的安全设计把**入站 DM 视为不可信输入**。默认行为：
- 未知发送者的 DM 会收到配对码提示，机器人不处理其消息
- 管理员通过 `openclaw pairing approve <channel> <code>` 手动审批
- 若要开放 DM 访问，需显式设置 `dmPolicy: "open"` 并加入 allowlist

这个设计反映了 OpenClaw 的安全优先理念：宁可麻烦一点，也不让恶意消息直接到达 AI。

---

## 4. 会话模型与多 Agent 路由

### 4.1 会话（Session）

OpenClaw 的核心抽象是**会话**。每个会话包含：
- 对话历史
- 当前活跃的工具列表
- Memory/Context
- 与特定渠道/用户关联

会话通过 Gateway 管理，可以同时运行多个会话（每个渠道、每个用户可以有独立会话）。

### 4.2 多 Agent 路由

OpenClaw 支持将不同渠道或用户路由到独立的 Agent 实例：

```json5
{
  agents: {
    defaults: {
      model: "openai/gpt-4o",
      workspace: "~/.openclaw/workspace",
    },
    // 为特定渠道创建独立 agent
    channels: {
      whatsapp: {
        model: "anthropic/claude-sonnet-4-20250514",
        workspace: "~/.openclaw/workspace-whatsapp",
      },
    },
  },
}
```

每个 Agent 有自己的：
- 模型配置（支持 OpenAI、Anthropic、Google、OpenRouter 等）
- Workspace（工作目录）
- 工具权限配置

---

## 5. 技能（Skills）系统

### 5.1 什么是 Skill

Skill 是 OpenClaw 的扩展单元，本质上是一个包含 `SKILL.md` 的目录。SKILL.md 使用 Markdown 格式定义技能的元信息、触发条件和执行逻辑。

```
~/.openclaw/workspace/skills/
├── github/
│   └── SKILL.md
├── weather/
│   └── SKILL.md
└── ...
```

### 5.2 SKILL.md 结构

```markdown
---
name: weather
description: "查询指定城市的天气预报"
---

# Weather Skill

当用户问天气时激活本技能。

## 触发条件
- 用户消息包含"天气"
- 用户请求"weather <city>"

## 执行逻辑
使用风 weather API 获取天气预报...
```

Skills 可以：
- 定义工具（Tool），让 AI 调用
- 定义触发器（Trigger），响应特定消息模式
- 定义工作流（Workflow），编排多步骤任务
- 打包外部工具（MCP Server 等）

### 5.3 技能注册与分发

OpenClaw 的技能可以在 [ClawHub](https://clawhub.ai/) 上发布和发现。安装技能：

```bash
openclaw skills add <skill-name>
# 或通过 npm
npx skills@latest add <author>/<skill-name>
```

---

## 6. 工具（Tools）系统

### 6.1 内置工具

OpenClaw 提供了丰富的内置工具，供 AI 在对话中调用：

| 工具 | 功能 |
|------|------|
| `exec` | 在宿主机上执行 shell 命令 |
| `read` | 读取文件内容 |
| `write` | 写入文件 |
| `edit` | 编辑文件 |
| `process` | 管理后台进程 |
| `canvas` | 控制 Live Canvas（截图、点击等）|
| `browser` | 浏览器自动化 |
| `nodes` | 控制远程节点设备 |
| `cron` | 定时任务调度 |
| `sessions_*` | 会话管理工具族 |

### 6.2 工具的安全边界

OpenClaw 的安全模型根据 Agent 类型区分权限：

- **main session**（主会话）：工具运行在宿主机上，AI 有完整访问权限——这是信任模型，因为它只属于用户本人。
- **非 main session**：默认在沙箱中运行（Docker 容器），允许的工具被严格限制。

沙箱默认允许的工具：`bash`, `process`, `read`, `write`, `sessions_list`, `sessions_history`, `sessions_send`, `sessions_spawn`
沙箱默认拒绝的工具：`browser`, `canvas`, `nodes`, `cron`, `discord`, `gateway`

可以通过配置修改沙箱规则：

```json5
{
  agents: {
    defaults: {
      sandbox: {
        mode: "non-main",  // 非 main session 进入沙箱
        backend: "docker",  // Docker 是默认沙箱后端
        allow: ["bash", "read", "write", "process"],
        deny: ["browser", "canvas"],
      },
    },
  },
}
```

---

## 7. Live Canvas

Live Canvas 是 OpenClaw 的可视化工作空间功能，允许 AI 操作一个实时的浏览器/应用界面。

典型使用场景：
- AI 在处理复杂任务时，渲染一个可视化的工作台
- 用户可以在 Canvas 上看到 AI 的工作过程，并进行交互
- 支持 A2UI（Agent-to-User Interface）协议

```bash
# 在 macOS 上触发 Canvas
openclaw agent --message "帮我分析这份数据并生成图表" --canvas
```

---

## 8. Workspace 与工作目录结构

OpenClaw 的工作空间（Workspace）默认在 `~/.openclaw/workspace`，包含：

```
~/.openclaw/workspace/
├── skills/          # 用户安装的技能
├── memory/          # 记忆数据
├── AGENTS.md        # Agent 系统提示
├── SOUL.md          # Agent 性格设定
├── TOOLS.md         # 本地工具配置
├── MEMORY.md        # 长期记忆
└── content/         # 用户内容（文档、代码等）
```

AGENTS.md、SOUL.md、TOOLS.md 是 OpenClaw 注入的特殊文件，用于配置 AI 的行为模式和工具能力。

---

## 9. 为什么 OpenClaw 值得关注

### 与其他 AI Agent 的区别

| 特性 | OpenClaw | ChatGPT | Claude Desktop |
|------|----------|---------|----------------|
| 消息渠道 | 20+（Telegram, WhatsApp等）| 仅 OpenAI App | 仅 Claude.ai |
| 运行位置 | 本地 Gateway | 云端 | 云端 |
| 多渠道并发 | ✅ | ❌ | ❌ |
| 工具扩展 | Skills + MCP | Plugins | ❌ |
| 本地文件访问 | 原生 | 受限 | 受限 |
| 消息安全 | DM 配对制 | 依赖平台 | 依赖平台 |

### OpenClaw 的设计取舍

**优势**：
- 真正的多渠道：同一个 AI 在 Telegram、WhatsApp、Discord 上同时服务
- 本地优先：数据不上云，适合隐私敏感场景
- 高度可扩展：Skills 系统让用户可以自建任何工具

**局限**：
- 需要自行管理模型 API（无内置模型补贴）
- 配置有一定门槛（需要理解 Gateway、Session、Agent 的关系）
- 终端优先的设计对非技术用户不够友好

---

## 10. 总结

OpenClaw 代表了一种 AI 助手的新范式：**以用户自己的设备为基地，以用户自己的消息渠道为入口，以用户自己的数据为边界**。它的 Gateway 架构、多渠道路由、技能系统和安全沙箱，构成了一套完整且灵活的个人 AI 基础设施。

如果你希望拥有：
- 一个可以在 Telegram/WhatsApp/Discord 上随时唤起的私人 AI
- 完全掌控自己的 AI 配置和对话数据
- 能够运行自定义工具和工作流的 AI 助手

OpenClaw 是一个值得关注的项目。

延伸资源：
- [OpenClaw 官网](https://openclaw.ai)
- [OpenClaw 文档](https://docs.openclaw.ai)
- [OpenClaw GitHub](https://github.com/openclaw/openclaw)
- [ClawHub（技能市场）](https://clawhub.ai)
- [DeepWiki 技术解析](https://deepwiki.com/openclaw/openclaw)
