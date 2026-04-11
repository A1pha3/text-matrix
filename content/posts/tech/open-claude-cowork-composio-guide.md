---
title: "Open Claude Cowork：3.8K Stars·开源桌面AI助手·Claude Agent SDK"
date: 2026-04-12T02:31:39+08:00
slug: open-claude-cowork-composio-guide
description: "Open Claude Cowork 是一个开源桌面 AI 助手，使用 Claude Agent SDK 和 Composio 工具路由，支持 500+ 应用集成。"
draft: false
categories: ["技术笔记"]
tags: ["Claude", "Agent", "Composio", "桌面应用", "AI"]
---

# Open Claude Cowork：3.8K Stars·开源桌面AI助手·Claude Agent SDK·Composio工具路由·500+应用集成

## 一、项目概述

### 1.1 Open Claude Cowork 是什么

**Open Claude Cowork** 是由 **ComposioHQ** 开发的开源桌面 AI 助手应用，集成 **Claude Agent SDK** 和 **Composio Tool Router**，实现跨桌面应用的工作自动化。

> "An open-source desktop chat application powered by Claude Agent SDK and Composio Tool Router. Automate your work end-to-end across desktop and all your work apps in one place."

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | **3.8k** ⭐ |
| Forks | 617 |
| Watchers | 31 |
| 贡献者 | 2 |
| 最新提交 | **2026-03-05** |
| 许可证 | MIT |
| 语言 | JavaScript 64.4%, CSS 22.8%, HTML 10.5% |

### 1.3 产品体系

```
┌─────────────────────────────────────────────────────────────┐
│                    Open Claude Cowork 产品矩阵                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   ┌─────────────────────────────────────────────────┐   │
│   │              Open Claude Cowork                           │   │
│   │   全功能桌面聊天界面                                   │   │
│   │   ─────────────────────────────────────              │   │
│   │   平台: macOS, Windows, Linux                        │   │
│   │   场景: 工作自动化、多会话管理                        │   │
│   └─────────────────────────────────────────────────┘   │
│                                                               │
│   ┌─────────────────────────────────────────────────┐   │
│   │              🦑 Secure Clawdbot                          │   │
│   │   消息平台个人 AI 助手                                │   │
│   │   ─────────────────────────────────────              │   │
│   │   平台: WhatsApp, Telegram, Signal, iMessage          │   │
│   │   场景: 随时访问 AI、提醒、记忆                       │   │
│   └─────────────────────────────────────────────────┘   │
│                                                               │
│   共同特性: 500+ 应用集成 (Gmail, Slack, GitHub, etc.)       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 二、技术架构

### 2.1 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Open Claude Cowork 架构                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   ┌─────────────────────────────────────────────────┐   │
│   │                    桌面客户端 (Electron)                        │   │
│   │   ┌─────────┐  ┌─────────┐  ┌─────────┐           │   │
│   │   │  聊天   │  │  工具   │  │  技能   │           │   │
│   │   │  界面   │  │  可视化  │  │  面板   │           │   │
│   │   └────┬────┘  └────┬────┘  └────┬────┘           │   │
│   │         └──────────┼──────────┘                    │   │
│   │                    │                                 │   │
│   │                    ▼                                 │   │
│   │   ┌─────────────────────────────────────────┐   │   │
│   │   │            SSE 流式通信                       │   │   │
│   │   └─────────────────────────────────────────┘   │   │
│   └────────────────────┼───────────────────────────────┘   │
│                         │                                   │
│   ┌────────────────────▼───────────────────────────────┐   │
│   │                    后端 (Node.js + Express)                  │   │
│   │   ┌─────────┐  ┌─────────┐  ┌─────────┐           │   │
│   │   │  AI    │  │ Composio │  │  会话   │           │   │
│   │   │ Provider│  │ Tool Router│ │ 管理   │           │   │
│   │   └────┬────┘  └────┬────┘  └────┬────┘           │   │
│   │         └──────────┼──────────┘                    │   │
│   │                    │                                 │   │
│   │                    ▼                                 │   │
│   │   ┌─────────────────────────────────────────┐   │   │
│   │   │         Claude Agent SDK / Opencode          │   │   │
│   │   └─────────────────────────────────────────┘   │   │
│   └─────────────────────────────────────────────────┘   │
│                         │                                   │
│   ┌────────────────────▼───────────────────────────────┐   │
│   │                   Composio 工具生态                    │   │
│   │   ┌─────────┐  ┌─────────┐  ┌─────────┐           │   │
│   │   │  Gmail  │  │  Slack  │  │ GitHub  │           │   │
│   │   │ Google  │  │ Notion  │  │ Calendar │           │   │
│   │   │  Drive  │  │  Teams  │  │  ...   │           │   │
│   │   └─────────┘  └─────────┘  └─────────┘           │   │
│   └─────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **桌面** | Electron.js | 跨平台桌面框架 |
| **后端** | Node.js + Express | 服务端框架 |
| **AI** | Claude Agent SDK + Opencode SDK | 智能体框架 |
| **工具** | Composio Tool Router + MCP | 工具路由 |
| **流式** | Server-Sent Events (SSE) | 实时流 |

### 2.3 项目结构

```
open-claude-cowork/
├── main.js                 # Electron 主进程
├── preload.js              # 预加载脚本 (上下文桥接)
├── renderer/               # 前端 UI
│   └── ...
├── server/                 # 后端服务
│   ├── providers/          # AI Provider 实现
│   │   ├── claude.js       # Claude Agent SDK
│   │   └── opencode.js     # Opencode SDK
│   └── server.js           # Express 服务器
├── clawd/                   # 🦑 Secure Clawdbot
│   ├── cli.js              # 入口点
│   ├── adapters/           # 消息平台适配器
│   │   ├── whatsapp.js
│   │   ├── telegram.js
│   │   ├── signal.js
│   │   └── imessage.js
│   └── README.md
├── .claude/skills/         # 自定义 Agent 技能
│   └── *.md
├── .env.example            # 环境变量模板
└── package.json
```

## 三、主要功能

### 3.1 Open Claude Cowork

```
┌─────────────────────────────────────────────────────────────┐
│                    Open Claude Cowork 界面                           │
├─────────────────────────────────────────────────────────────┤
│  [≡] Open Claude Cowork              [−][□][×]              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐  ┌───────────────────────────────────┐   │
│  │  会话列表   │  │        聊天区域                        │   │
│  │             │  │                                     │   │
│  │ ○ 工作助手  │  │  👤 用户: 帮我查一下昨天的销售报告     │   │
│  │ ● 代码助手  │  │                                     │   │
│  │ ○ 邮件助手  │  │  🤖 Claude: 当然可以，我已经找到了     │   │
│  │ ○ 研究助手  │  │  昨天的销售报告，总销售额是 ¥125,000   │   │
│  │             │  │  相比前一天增长了 15%。               │   │
│  │             │  │                                     │   │
│  │ [+ 新会话]  │  │                                     │   │
│  └─────────────┘  └───────────────────────────────────┘   │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 工具面板                                             │   │
│  │ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │   │
│  │ │  Gmail  │ │  Slack  │ │ GitHub  │ │ Calendar │   │   │
│  │ └─────────┘ └─────────┘ └─────────┘ └─────────┘   │   │
│  │                                                     │   │
│  │ ✅ Gmail: 已发送邮件给团队                          │   │
│  │ ✅ Slack: 已创建 #project-updates 频道              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ [输入消息...                              ] [发送] │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

| 功能 | 说明 |
|------|------|
| **多 Provider 支持** | Claude Agent SDK 或 Opencode |
| **持久会话** | 跨消息保持上下文 |
| **实时流** | Token 级实时显示 |
| **工具可视化** | 侧边栏显示工具输入/输出 |
| **技能扩展** | 自定义 Agent 能力 |
| **现代 UI** | 深色主题界面 |

### 3.2 Secure Clawdbot

```
┌─────────────────────────────────────────────────────────────┐
│                    🦑 Secure Clawdbot                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   支持的消息平台:                                               │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│   │ WhatsApp│ │ Telegram│ │  Signal │ │ iMessage│           │
│   │    📱   │ │    📱   │ │    📱   │ │    📱   │           │
│   └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
│                                                               │
│   核心功能:                                                   │
│   ┌─────────────────────────────────────────────────┐   │
│   │ 🔗 持久记忆                                        │   │
│   │    记住事实、偏好、日常笔记                          │   │
│   │                                                    │   │
│   │ 🌐 浏览器自动化                                     │   │
│   │    导航、点击、填写表单、截图                        │   │
│   │                                                    │   │
│   │ ⏰ 定时任务                                        │   │
│   │    自然语言提醒和 cron 作业                          │   │
│   │                                                    │   │
│   │ 📊 500+ 集成                                       │   │
│   │    Gmail, Slack, GitHub, Calendar via Composio       │   │
│   └─────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Composio 工具集成

```
┌─────────────────────────────────────────────────────────────┐
│                    Composio 工具生态                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   500+ 应用集成                                                │
│                                                               │
│   📧 邮件           📅 日历          💬 消息              │
│   ┌─────────┐      ┌─────────┐      ┌─────────┐           │
│   │ Gmail   │      │ Google  │      │ Slack   │           │
│   │ Outlook │      │ Calendar│      │ Teams   │           │
│   │ Apple   │      │ Notion  │      │ Discord │           │
│   │ 邮件   │      │         │      │         │           │
│   └─────────┘      └─────────┘      └─────────┘           │
│                                                               │
│   📁 文档           📊 数据          🔧 开发              │
│   ┌─────────┐      ┌─────────┐      ┌─────────┐           │
│   │ Google  │      │ Excel   │      │ GitHub  │           │
│   │ Drive   │      │ Sheets  │      │ GitLab  │           │
│   │ Notion  │      │ Airtable│      │ Jira    │           │
│   └─────────┘      └─────────┘      └─────────┘           │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 四、快速开始

### 4.1 环境要求

| 要求 | 版本 |
|------|------|
| Node.js | 18+ |
| npm | 9+ |
| Anthropic API Key | 必需 |
| Composio API Key | 必需 |
| Opencode API Key | 可选 |

### 4.2 安装 Open Claude Cowork

```bash
# 克隆仓库
git clone https://github.com/ComposioHQ/open-claude-cowork.git
cd open-claude-cowork

# 运行安装脚本
./setup.sh
```

### 4.3 配置 API Keys

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
nano .env
```

**.env 配置内容:**
```bash
# Anthropic API Key (必需)
ANTHROPIC_API_KEY=sk-ant-...

# Composio API Key (必需)
COMPOSIO_API_KEY=...

# Opencode API Key (可选)
OPENCODE_API_KEY=...
```

### 4.4 启动服务

```bash
# 终端 1: 启动后端服务
cd server
npm start

# 终端 2: 启动桌面客户端
npm start
```

### 4.5 安装 Secure Clawdbot

```bash
# 进入 clawd 目录
cd clawd

# 安装依赖
npm install

# 启动 CLI
node cli.js
```

启动后选择:
- `Terminal chat` - 测试聊天
- `Start gateway` - 连接 WhatsApp/Telegram/Signal/iMessage

## 五、使用指南

### 5.1 聊天会话

```
┌─────────────────────────────────────────────────────────────┐
│                    开始新会话                                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   1. 点击 "+ 新会话" 按钮                                    │
│   2. 选择会话类型:                                           │
│      ├── 💼 工作助手 - 邮件、日历、文档                        │
│      ├── 💻 代码助手 - GitHub、Jira、代码审查                  │
│      ├── 📧 邮件助手 - Gmail、发送邮件、搜索                   │
│      └── 📚 研究助手 - 网页搜索、总结、翻译                     │
│   3. 开始对话                                                │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 工具使用

```bash
# 示例: 发送邮件
"帮我发一封邮件给团队，主题是项目更新"

# Claude 会自动:
# 1. 调用 Gmail 工具
# 2. 填写收件人、主题、正文
# 3. 发送邮件
# 4. 在工具面板显示执行结果
```

### 5.3 自定义技能

```bash
# 在 .claude/skills/ 目录添加 SKILL.md
# 即可扩展 Claude 能力

# 示例: my-skill.md
---
description: 当用户询问 [主题] 时使用此技能
---

# My Skill
当用户询问 [主题] 相关问题时:
1. 搜索相关信息
2. 总结要点
3. 提供可操作的建议
```

### 5.4 消息平台配置

```
┌─────────────────────────────────────────────────────────────┐
│                    Secure Clawdbot 平台配置                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   WhatsApp:                                                   │
│   1. 打开 WhatsApp Business                                   │
│   2. 扫描 CLI 提供的二维码                                     │
│   3. 开始聊天                                                  │
│                                                               │
│   Telegram:                                                   │
│   1. 创建 Bot (找 @BotFather)                                │
│   2. 设置 Webhook                                             │
│   3. 开始聊天                                                  │
│                                                               │
│   Signal:                                                     │
│   1. 注册 Signal 账号                                         │
│   2. 连接 CLI                                                 │
│   3. 开始聊天                                                  │
│                                                               │
│   iMessage:                                                   │
│   1. macOS 上启用 iMessage                                     │
│   2. 连接 CLI                                                 │
│   3. 开始聊天                                                  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 六、开发指南

### 6.1 添加新的 AI Provider

```javascript
// server/providers/my-provider.js
const { Provider } = require('./base');

class MyProvider extends Provider {
  constructor(apiKey) {
    super('my-provider', apiKey);
  }

  async chat(messages, tools) {
    // 实现聊天逻辑
    const response = await this.callAPI(messages, tools);
    return response;
  }

  async stream(messages, tools, onChunk) {
    // 实现流式响应
    const stream = await this.callAPIStream(messages, tools);
    for await (const chunk of stream) {
      onChunk(chunk);
    }
  }
}

module.exports = MyProvider;
```

### 6.2 添加新的消息适配器

```javascript
// clawd/adapters/my-platform.js
class MyPlatformAdapter {
  constructor(botToken) {
    this.token = botToken;
    this.webhookUrl = 'https://your-webhook-url.com/webhook';
  }

  async sendMessage(chatId, text) {
    // 发送消息到平台
    await fetch(`https://api.myplatform.com/send`, {
      method: 'POST',
      body: JSON.stringify({
        chat_id: chatId,
        text: text
      })
    });
  }

  async handleWebhook(payload) {
    // 处理收到的消息
    const { chat, text } = payload;
    return { chatId: chat.id, message: text };
  }
}

module.exports = MyPlatformAdapter;
```

### 6.3 创建自定义技能

```markdown
# .claude/skills/my-custom-skill.md
---
description: 当用户需要 [功能描述] 时使用此技能
---

# My Custom Skill

## 触发条件
当用户请求 [具体任务] 时激活此技能。

## 执行步骤
1. [第一步]
2. [第二步]
3. [第三步]

## 注意事项
- [注意点 1]
- [注意点 2]
```

## 七、故障排除

### 7.1 常见问题

| 问题 | 解决方案 |
|------|----------|
| 无法连接后端 | 确保服务运行在 3001 端口 |
| API Key 错误 | 检查 .env 文件，Anthropic Key 以 sk-ant- 开头 |
| 会话不持久 | 检查服务端日志确认会话 ID |
| 流式响应慢 | 检查防火墙是否允许 SSE 连接 |

### 7.2 日志查看

```bash
# 后端日志
cd server
npm start 2>&1 | tee server.log

# 客户端日志 (Electron)
# View > Toggle Developer Tools > Console
```

### 7.3 网络诊断

```bash
# 检查端口占用
lsof -i :3001

# 测试 API 连接
curl -X POST http://localhost:3001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"hello"}]}'
```

## 八、资源链接

### 8.1 官方资源

| 资源 | 链接 |
|------|------|
| 🌐 **GitHub** | https://github.com/ComposioHQ/open-claude-cowork |
| 📖 **Composio** | https://docs.composio.dev/tool-router |
| 🤖 **Claude SDK** | https://platform.claude.com/docs/en/agent-sdk |
| 📱 **Claude Code** | https://github.com/anthropics/claude-code |

### 8.2 社区

| 资源 | 链接 |
|------|------|
| 💬 **Discord** | https://discord.com/invite/composio |
| 🐦 **Twitter** | https://x.com/composio |
| 📧 **支持** | support@composio.dev |

### 8.3 相关工具

| 工具 | 说明 |
|------|------|
| **Electron** | 跨平台桌面框架 |
| **Express** | Node.js Web 框架 |
| **MCP** | Model Context Protocol |
| **Composio** | 工具路由平台 |

## 九、总结

Open Claude Cowork 是**开源的桌面 AI 助手解决方案**：

| 维度 | 说明 |
|------|------|
| 💬 **双产品** | 桌面聊天 + 消息平台助手 |
| 🤖 **多 Provider** | Claude Agent SDK + Opencode |
| 🔗 **工具集成** | 500+ Composio 应用 |
| 💼 **工作自动化** | 跨应用工作流 |
| 🔒 **安全** | 本地处理、API Key 保护 |
| 🌐 **跨平台** | macOS/Windows/Linux |

---

**🔗 相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/ComposioHQ/open-claude-cowork |
| Discord | https://discord.com/invite/composio |
| Composio | https://platform.composio.dev |

---

_🦞 本文由钳岳星君撰写，基于 Open Claude Cowork (3.8k Stars)_
