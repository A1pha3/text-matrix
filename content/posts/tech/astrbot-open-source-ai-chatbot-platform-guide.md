---
title: "AstrBot：开源一站式 AI Agent 聊天机器人平台完全指南"
slug: "astrbot-open-source-ai-chatbot-platform-guide"
date: 2026-03-31T16:00:00+08:00
categories: ["技术笔记"]
tags: ["AstrBot", "AI聊天机器人", "开源", "IM集成", "Telegram", "Discord", "飞书", "QQ机器人", "Agent", "MCP"]
description: "全面解析 AstrBot (28.4k Stars)：开源一站式AI Agent聊天机器人平台，支持QQ/微信/Telegram/飞书等15+平台，集成OpenAI/Claude/Gemini/Ollama等模型，1000+插件，Agent Sandbox。"
---

# AstrBot：开源一站式 AI Agent 聊天机器人平台完全指南

## §1 学习目标

完成本文档后，你将能够：

- ✅ 理解 AstrBot 的核心定位与设计理念
- ✅ 掌握 AstrBot 的十大核心特性
- ✅ 熟练部署 AstrBot（Docker/uv/一键云部署/桌面应用）
- ✅ 配置多平台聊天机器人（QQ/微信/Telegram/飞书/Slack/Discord等）
- ✅ 配置多种 LLM 服务（OpenAI/Claude/Gemini/Ollama/通义/智谱等）
- ✅ 使用 Agent Sandbox 沙箱安全执行代码
- ✅ 安装和使用插件（1000+ 插件）
- ✅ 自定义人格和知识库
- ✅ 排查常见问题
- ✅ 为 AstrBot 贡献代码

---

## §2 项目概述

### 2.1 什么是 AstrBot？

**AstrBot**（官方仓库：[AstrBotDevs/AstrBot](https://github.com/AstrBotDevs/AstrBot)）是一个**开源一站式 AI Agent 聊天机器人平台**，集成主流即时通讯应用。

**官方描述**：

> AstrBot is an open-source all-in-one Agent chatbot platform that integrates with mainstream instant messaging apps. It provides reliable and scalable conversational AI infrastructure for individuals, developers, and teams. Whether you're building a personal AI companion, intelligent customer service, automation assistant, or enterprise knowledge base, AstrBot enables you to quickly build production-ready AI applications within your IM platform workflows.

**翻译**：AstrBot 是一个开源一站式 AI Agent 聊天机器人平台，集成主流即时通讯应用。它为个人、开发者和团队提供可靠且可扩展的对话式 AI 基础设施。无论你是构建个人 AI 伴侣、智能客服、自动化助手还是企业知识库，AstrBot 都能让你在 IM 平台工作流中快速构建生产级 AI 应用。

### 2.2 核心价值主张

| 价值 | 说明 |
|------|------|
| **免费开源** | 💯 AGPL-3.0 开源许可证 |
| **全功能** | LLM 对话、多模态、Agent、MCP、Skills、知识库、人格设置、上下文自动压缩 |
| **多平台集成** | QQ、微信企业号、飞书、钉钉、Telegram、Slack、Discord 等 |
| **1000+ 插件** | 一键安装丰富功能 |
| **安全沙箱** | Agent Sandbox 隔离执行代码和 Shell 调用 |
| **多种部署** | Docker/uv/云端/桌面应用/Launcher |
| **国际化** | 支持多语言 |

### 2.3 核心数据

```
Stars:     28,400 (28.4k)
Forks:     1,900 (1.9k)
Watchers:  74
贡献者:    255 人
提交数:   4,410 次
分支数:    69 个
标签数:    217 个
发布版本:  207 个
最新版本:  v4.22.2 (2026-03-28)
许可证:    AGPL-3.0
语言:     Python 69.6%, Vue 24.5%, TypeScript 3.2%
```

### 2.4 功能一览

| 功能 | 说明 |
|------|------|
| 💙 角色扮演与情感陪伴 | 情感化对话 |
| ✨ 主动 Agent | 主动执行任务 |
| 🚀 通用 Agent 能力 | 多功能 AI 助手 |
| 🧩 1000+ 社区插件 | 一键安装 |

---

## §3 支持的聊天平台

### 3.1 官方支持的平台

| 平台 | 维护者 | 说明 |
|------|--------|------|
| **QQ** | 官方 | QQ 官方机器人 |
| **OneBot v11** | 官方 | 兼容 OneBot v11 协议 |
| **Telegram** | 官方 | Telegram Bot |
| **企业微信 & 企业微信 AI Bot** | 官方 | WeChat Work |
| **微信公众号** | 官方 | WeChat Official Accounts |
| **飞书 (Lark)** | 官方 | Feishu Bot |
| **钉钉** | 官方 | DingTalk Bot |
| **Slack** | 官方 | Slack Bot |
| **Discord** | 官方 | Discord Bot |
| **LINE** | 官方 | LINE Bot |
| **Satori** | 官方 | Satori 协议 |
| **Misskey** | 官方 | Misskey 平台 |
| **WhatsApp** | 官方 | 即将支持 |

### 3.2 社区支持的平台

| 平台 | 维护者 | 说明 |
|------|--------|------|
| **Matrix** | 社区 | Matrix 协议 |
| **KOOK** | 社区 | KOOK 平台 |
| **VoceChat** | 社区 | VoceChat 平台 |

---

## §4 支持的模型服务

### 4.1 LLM 服务（语言模型）

| 服务 | 类型 | 说明 |
|------|------|------|
| **OpenAI & 兼容服务** | LLM | GPT-4o 等 |
| **Anthropic Claude** | LLM | Claude 3.5 等 |
| **Google Gemini** | LLM | Gemini 2.0 等 |
| **Moonshot AI (月之暗面)** | LLM | Kimi 等 |
| **智谱 AI** | LLM | GLM 等 |
| **DeepSeek** | LLM | DeepSeek 系列 |
| **Ollama (本地)** | LLM | 本地运行 |
| **LM Studio (本地)** | LLM | 本地运行 |
| **AIHubMix** | LLM | API 网关，支持所有模型 |
| **CompShare** | LLM | API 服务 |
| **302.AI** | LLM | API 服务 |
| **TokenPony** | LLM | API 服务 |
| **SiliconFlow** | LLM | API 服务 |
| **PPIO Cloud** | LLM | API 服务 |
| **ModelScope** | LLM | 魔搭 |
| **OneAPI** | LLM | API 管理 |

### 4.2 LLMOps 平台

| 平台 | 说明 |
|------|------|
| **Dify** | 知名 LLMOps 平台 |
| **阿里云百炼** | 阿里云 LLM 平台 |
| **Coze** | 扣子平台 |

### 4.3 语音转文本（STT）

| 服务 | 说明 |
|------|------|
| **OpenAI Whisper** | 语音识别 |
| **SenseVoice** | 硅基流动语音 |

### 4.4 文本转语音（TTS）

| 服务 | 说明 |
|------|------|
| **OpenAI TTS** | GPT-4o audio |
| **Google Gemini TTS** | Gemini 语音 |
| **GPT-Sovits-Inference** | 声音克隆 |
| **GPT-Sovits** | 声音克隆 |
| **FishAudio** | 声音克隆 |
| **Edge TTS** | 微软 Edge 语音 |
| **阿里云百炼 TTS** | 阿里云语音 |
| **Azure TTS** | 微软 Azure 语音 |
| **MiniMax TTS** | MiniMax 语音 |
| **火山引擎 TTS** | 字节跳动语音 |

---

## §5 核心功能详解

### 5.1 AI LLM 对话

- 多模型支持（OpenAI/Claude/Gemini/本地模型）
- 多模态支持（文本/图片/语音）
- 上下文自动压缩
- 长对话管理

### 5.2 Agent 能力

- 自动任务分解和执行
- 工具调用（Function Calling）
- 插件扩展
- 知识库问答

### 5.3 MCP (Model Context Protocol)

- 支持 MCP 协议
- 连接外部数据源
- 扩展 Agent 能力

### 5.4 Skills 系统

- 模块化技能设计
- 1000+ 社区插件
- 一键安装

### 5.5 Agent Sandbox（安全沙箱）

- 隔离执行代码
- 安全的 Shell 调用
- 会话级资源复用
- 防止恶意代码执行

### 5.6 知识库

- RAG（检索增强生成）
- 文档上传和分析
- 向量数据库支持

### 5.7 人格设置

- 自定义 AI 人格
- 角色扮演模式
- 情感陪伴模式

### 5.8 Web UI & Chat UI

- Web 管理界面
- Web 聊天界面
- 内置 Agent Sandbox
- 内置网页搜索

---

## §6 安装与部署

### 6.1 uv 一键部署（推荐）

**前置要求**：安装 [uv](https://docs.astral.sh/uv/)

```bash
# 首次安装
uv tool install astrbot
astrbot init

# 运行
astrbot run

# 更新
uv tool upgrade astrbot
```

**注意**：macOS 用户首次运行可能需要 10-20 秒。

### 6.2 Docker 部署（生产环境推荐）

```bash
# 使用 Docker Compose
docker compose up -d

# 或使用 Docker
docker run -d -p 20080:20080 \
  -v astrbot-data:/app/data \
  --name astrbot \
  soulter/astrbot:latest
```

详细配置请参考[官方文档](https://astrbot.app/deploy/astrbot/docker.html)。

### 6.3 RainYun 云端一键部署

适合不想管理服务器的用户：

[立即部署到 RainYun](https://app.rainyun.com/apps/rca/store/5994?ref=NjU1ODg0)

### 6.4 桌面应用部署

适合主要使用 ChatUI 的桌面用户：

[下载 AstrBot Desktop](https://github.com/AstrBotDevs/AstrBot-desktop)

### 6.5 Launcher 部署

适合需要快速部署和多实例隔离的桌面用户：

[下载 AstrBot Launcher](https://github.com/Raven95676/astrbot-launcher)

### 6.6 其他部署方式

| 方式 | 说明 |
|------|------|
| **Replit** | 适合在线演示和轻量试用 |
| **AUR** | Arch Linux 用户（`yay -S astrbot-git`）|
| **BT-Panel** | 宝塔面板部署 |
| **1Panel** | 1Panel 应用市场 |
| **CasaOS** | NAS/家庭服务器可视化部署 |
| **手动部署** | 源码安装 |

---

## §7 配置指南

### 7.1 配置 LLM 提供商

在管理界面配置 API Key 和模型选择：

```yaml
# 示例配置
llm:
  provider: openai  # 或 anthropic/gemini/ollama 等
  model: gpt-4o
  api_key: your-api-key
```

### 7.2 配置聊天平台

以 Telegram 为例：

1. 在 Telegram BotFather 创建 Bot
2. 获取 Bot Token
3. 在管理界面配置：

```yaml
telegram:
  enabled: true
  bot_token: your-bot-token
```

### 7.3 配置 Agent Sandbox

```yaml
sandbox:
  enabled: true
  max_memory_mb: 512
  timeout_seconds: 30
```

---

## §8 插件系统

### 8.1 安装插件

在管理界面或使用命令：

```bash
astrbot plugin install <plugin-name>
```

### 8.2 社区插件

1000+ 社区插件可用，包括：

- 图像生成插件
- 搜索插件
- 日程管理插件
- 办公插件
- 社交插件
- 更多...

### 8.3 开发插件

详见[官方插件开发文档](https://docs.astrbot.app/)。

---

## §9 项目结构

### 9.1 目录结构

| 目录 | 说明 |
|------|------|
| `astrbot/` | 核心代码 |
| `dashboard/` | Web 管理界面 |
| `docs/` | 文档 |
| `k8s/` | Kubernetes 配置 |
| `changelogs/` | 更新日志 |
| `samples/` | 示例 |
| `scripts/` | 脚本 |
| `tests/` | 测试 |
| `openspec/` | 开放规范 |

### 9.2 核心文件

| 文件 | 说明 |
|------|------|
| `pyproject.toml` | Python 项目配置 |
| `Dockerfile` | Docker 镜像配置 |
| `compose.yml` | Docker Compose 配置 |
| `main.py` | 主入口 |
| `requirements.txt` | 依赖列表 |
| `AGENTS.md` | Agent 说明 |

---

## §10 常见问题

### Q1：AstrBot 和 OpenClaw 有什么区别？

| 特性 | AstrBot | OpenClaw |
|------|---------|-----------|
| **定位** | IM 平台集成 | 通用 Agent 框架 |
| **聊天平台** | 15+ 平台 | 更多通用 |
| **插件系统** | 1000+ | 更多通用 |
| **主要语言** | Python | Node.js |

### Q2：需要多少硬件？

| 部署方式 | 最低要求 |
|----------|----------|
| **Docker** | 1GB RAM, 10GB 磁盘 |
| **桌面应用** | 2GB RAM, 5GB 磁盘 |
| **完整部署** | 4GB+ RAM, 20GB+ 磁盘 |

### Q3：支持私有模型吗？

**支持**。通过 Ollama 或 LM Studio 支持完全私有的本地部署。

### Q4：如何更新 AstrBot？

```bash
# uv 更新
uv tool upgrade astrbot

# Docker 更新
docker pull soulter/astrbot:latest
```

### Q5：支持中文吗？

**支持**。AstrBot 有简体中文、繁体中文、日语、法语、俄语等多语言 README。

### Q6：如何获取帮助？

- 官方文档：https://astrbot.app/
- GitHub Issues：https://github.com/AstrBotDevs/AstrBot/issues
- QQ 群：多个中文群组（详见 README）
- Discord：https://discord.gg/hAVk6tgV36

---

## §11 总结

### 11.1 核心优势

| 优势 | 说明 |
|------|------|
| **开源免费** | AGPL-3.0，完全开源 |
| **多平台集成** | 15+ 聊天平台 |
| **1000+ 插件** | 丰富的功能扩展 |
| **多模型支持** | OpenAI/Claude/Gemini/本地模型 |
| **安全沙箱** | Agent Sandbox 保护安全 |
| **多种部署** | Docker/云端/桌面/移动端 |
| **活跃社区** | 255 贡献者，28.4k Stars |

### 11.2 适用场景

| 场景 | 推荐指数 |
|------|----------|
| 个人 AI 伴侣 | ⭐⭐⭐⭐⭐ |
| 智能客服 | ⭐⭐⭐⭐⭐ |
| 团队协作助手 | ⭐⭐⭐⭐⭐ |
| 自动化工作流 | ⭐⭐⭐⭐ |
| 企业知识库 | ⭐⭐⭐⭐ |
| 情感陪伴 | ⭐⭐⭐⭐⭐ |

### 11.3 项目信息

- Stars：28.4k
- Forks：1.9k
- 贡献者：255 人
- 最新版本：v4.22.2 (2026-03-28)
- 许可证：AGPL-3.0

### 11.4 相关资源

| 资源 | 链接 |
|------|------|
| 官方网站 | https://astrbot.app |
| GitHub | https://github.com/AstrBotDevs/AstrBot |
| 文档 | https://astrbot.app/ |
| 博客 | https://blog.astrbot.app/ |
| 路线图 | https://astrbot.featurebase.app/roadmap |
| Docker Hub | https://hub.docker.com/r/soulter/astrbot |

---

*文档版本 1.0 | 撰写日期：2026-03-31 | 基于 v4.22.2 (2026-03-28) | Stars: 28.4k ⭐*