---
title: "DeerFlow 2.0：字节跳动 Super Agent Harness 从入门到精通"
date: "2026-03-28T16:20:00+08:00"
slug: "deerflow-super-agent-harness"
aliases:
  - /posts/tech/deerflow-super-agent-harness/
description: "深度解析 DeerFlow 2.0 字节跳动 Super Agent Harness：Sub-Agent 并行执行、Markdown Skills 技能系统、Docker 沙箱隔离、LangGraph+LangChain 架构、IM 渠道集成，详解原理、架构、使用与二次开发。"
draft: false
categories: ["技术笔记"]
tags: ["DeerFlow", "Super Agent", "LangGraph", "多智能体", "字节跳动"]
---

# DeerFlow 2.0：字节跳动 Super Agent Harness 从入门到精通

> 预计阅读时间：40分钟 | 难度：⭐⭐⭐⭐

---

> **目标读者**：想要深入理解多智能体编排、可扩展 Agent 技能系统、沙箱隔离执行环境的开发者与研究者
> **核心问题**：如何构建一个可以分解复杂任务、跨会话记忆、多种 IM 渠道接入的可扩展 Super Agent 平台？
> **难度**：⭐⭐⭐⭐（专家设计）
> **预计阅读时间**：55 分钟

---

## 一、原理分析：为什么需要 Super Agent Harness

### 1.1 传统 Agent 的局限性

当前的 AI Agent 框架普遍存在以下问题：

**工具单一**：只能执行预定义的几个工具，无法灵活扩展。

**上下文隔离不足**：主 Agent 和子 Agent 共享上下文，导致子 Agent 被主 Agent 的思路干扰，无法专注任务本身。

**缺乏长期记忆**：会话结束即遗忘，无法积累跨会话的知识。

**执行环境不安全**：直接在宿主机执行代码，存在安全风险。

**无法协作**：复杂的端到端任务（如研究→报告→演示）需要多个 Agent 协作，但大多数框架不支持。

### 1.2 DeerFlow 的核心思想

DeerFlow 2.0 提出了 **Super Agent Harness** 的理念：**不只是一个框架，而是一个完整的运行时基础设施**。

**核心理念**：

1. **Harness 而非 Framework**：不是让你拼凑代码，而是提供完整的基础设施——文件系统、记忆、技能、沙箱、执行环境。

2. **Sub-Agent 协作**：复杂任务自动分解为多个子任务，并行执行后汇总结果。

3. **技能可组合**：每个技能是一个 Markdown 文件，定义了工作流、最佳实践和参考资料。可以自由组合。

4. **安全隔离**：每个任务在独立的 Docker 容器中执行，文件系统隔离，零污染。

5. **开箱即用**：LangGraph + LangChain 提供核心能力，加上技能系统、记忆系统、IM 渠道，开箱即用。

### 1.3 从 Deep Research 到 Super Agent

DeerFlow 起源于 Deep Research（深度研究）框架，但社区的用法远超预期：

- 构建数据管道
- 生成幻灯片
- 启动数据仪表盘
- 自动化内容工作流

这让团队意识到：**DeerFlow 不只是一个研究工具，而是一个 Harness——一个让 Agent 完成实际工作的运行时**。

---

## 二、架构分析：系统是如何设计的

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DeerFlow 2.0 系统架构                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         Frontend (Node.js)                            │  │
│  │                    http://localhost:2026                              │  │
│  └──────────────────────────────┬───────────────────────────────────────┘  │
│                                 │                                            │
│                                 ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Gateway API (Python)                               │  │
│  │                    http://localhost:8001                               │  │
│  │                                                                       │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │    IM      │  │   Skills    │  │   Memory    │  │   Threads   │  │  │
│  │  │  Channels  │  │   Loader    │  │   Store     │  │   Manager   │  │  │
│  │  │ Telegram   │  │             │  │             │  │             │  │  │
│  │  │ Slack      │  │             │  │             │  │             │  │  │
│  │  │ Feishu     │  │             │  │             │  │             │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  └──────────────────────────────┬───────────────────────────────────────┘  │
│                                 │                                            │
│                                 ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                  LangGraph Agent Server (Python)                      │  │
│  │                    http://localhost:2024                              │  │
│  │                                                                       │  │
│  │  ┌───────────────────────────────────────────────────────────────┐   │  │
│  │  │                    Lead Agent (主智能体)                         │   │  │
│  │  │                                                               │   │  │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │   │  │
│  │  │  │  Planner │  │ Executor │  │ Memory   │  │  Tools   │      │   │  │
│  │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │   │  │
│  │  │                    │                                           │   │  │
│  │  │                    ▼                                           │   │  │
│  │  │            ┌──────────────────┐                               │   │  │
│  │  │            │   Sub-Agents     │  ← 按需生成，并行执行           │   │  │
│  │  │            │   (隔离上下文)    │                               │   │  │
│  │  │            └──────────────────┘                               │   │  │
│  │  └───────────────────────────────────────────────────────────────┘   │  │
│  │                                                                       │  │
│  │  ┌───────────────────────────────────────────────────────────────┐   │  │
│  │  │              Skills System (Markdown 技能定义)                  │   │  │
│  │  │   research/ │ report/ │ slide/ │ web-page/ │ image-gen/       │   │  │
│  │  └───────────────────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────┬───────────────────────────────────────┘  │
│                                 │                                            │
│                                 ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Sandbox (Docker 隔离执行环境)                        │  │
│  │                                                                       │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │  │
│  │  │ /mnt/user-data/uploads  │  /mnt/user-data/workspace  │  /mnt/user-data/outputs  │  │
│  │  │     用户上传文件    │        工作目录        │       最终产出物      │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 核心模块详解

#### 2.2.1 LangGraph Agent Server

DeerFlow 的核心决策引擎。基于 LangGraph 构建，支持：

**多模型支持**：OpenAI、OpenRouter、Claude、DeepSeek、Kimi 等任意 OpenAI 兼容 API。

**推理能力**：支持 Thinking Mode、Reasoning Effort 等高级推理配置。

**递归限制**：防止 Agent 进入死循环（默认 recursion_limit: 100）。

#### 2.2.2 Sub-Agents（子智能体）

DeerFlow 的核心创新之一。当主 Agent 遇到复杂任务时，会自动分解为多个子 Agent：

**并行执行**：多个子 Agent 可以同时工作，加速任务完成。

**隔离上下文**：每个子 Agent 运行在独立的上下文中，不会被主 Agent 或其他子 Agent 的思路干扰。

**结构化结果**：子 Agent 返回结构化结果，主 Agent 汇总整合。

**应用场景**：

```
研究任务 → 子 Agent A：搜索技术细节
       → 子 Agent B：搜索市场数据
       → 子 Agent C：搜索竞品分析
       → 主 Agent：汇总成完整报告
```

#### 2.2.3 Skills System（技能系统）

DeerFlow 的技能是**Markdown 文件**，定义了工作流、最佳实践和参考资料。

**内置技能**：

| 技能 | 功能 |
|------|------|
| `research` | 研究搜索与分析 |
| `report-generation` | 报告生成 |
| `slide-creation` | 幻灯片创建 |
| `web-page` | 网页创建 |
| `image-generation` | 图片生成 |
| `video-generation` | 视频生成 |

**技能加载机制**：按需渐进加载，只在任务需要时加载，保持上下文精简。

**自定义技能**：

```markdown
# My Custom Skill

## 触发条件
当用户要求 [特定任务] 时触发

## 工作流程
1. 第一步：...
2. 第二步：...

## 最佳实践
- ...
```

#### 2.2.4 Sandbox & File System

DeerFlow 每个任务在**独立 Docker 容器**中执行：

**隔离的文件系统**：

```
/mnt/user-data/
├── uploads/     ← 用户上传的文件
├── workspace/   ← Agent 工作目录
└── outputs/     ← 最终产出物
```

**安全特性**：

- 会话间零污染
- 所有操作可审计
- 支持 Kubernetes 沙箱

#### 2.2.5 Memory System（记忆系统）

跨会话持久记忆：

- **用户画像**：自动构建和维护用户偏好
- **偏好记忆**：写作风格、技术栈、习惯
- **知识积累**：随着使用越来越了解用户

**Memory 更新机制**：自动跳过重复事实，避免记忆无限累积。

#### 2.2.6 IM Channels（即时通讯渠道）

DeerFlow 支持多种 IM 渠道的接入：

| 渠道 | 传输方式 | 难度 |
|------|---------|------|
| **Telegram** | Bot API (long-polling) | 简单 |
| **Slack** | Socket Mode | 中等 |
| **Feishu/Lark** | WebSocket | 中等 |

**IM 命令**：

| 命令 | 功能 |
|------|------|
| `/new` | 开始新对话 |
| `/status` | 显示当前线程信息 |
| `/models` | 列出可用模型 |
| `/memory` | 查看记忆 |
| `/help` | 显示帮助 |

### 2.3 技术选型

#### 2.3.1 为什么选择 LangGraph

**状态机抽象**：LangGraph 的状态机模型非常适合 Agent 的多步骤任务执行。

**多 Agent 支持**：内置对 Sub-Agent 的支持，简化了复杂任务的编排。

**可持久化**：状态可以持久化，支持断点续传。

#### 2.3.2 为什么选择 Docker 沙箱

**安全隔离**：容器间的文件系统、网络完全隔离。

**一致性**：开发、测试、生产环境一致。

**资源控制**：可以限制 CPU、内存使用。

### 2.4 版本演进

| 版本 | 发布 | 主要变化 |
|------|------|---------|
| v1.x | 2024 | Deep Research 框架 |
| **v2.0** | 2026-02 | 完全重写，Super Agent Harness |

---

## 三、使用说明：从安装到实战

### 3.1 环境准备

**系统要求**：

- Node.js 22+
- Python 3.11+
- Docker（用于沙箱执行）
- pnpm、uv、nginx

### 3.2 安装步骤

#### 3.2.1 克隆并配置

```bash
# 克隆仓库
git clone https://github.com/bytedance/deer-flow.git
cd deer-flow

# 生成配置文件
make config
```

#### 3.2.2 配置模型

编辑 `config.yaml`：

```yaml
models:
  - name: gpt-4
    display_name: GPT-4
    use: langchain_openai:ChatOpenAI
    model: gpt-4
    api_key: $OPENAI_API_KEY
    max_tokens: 4096
    temperature: 0.7

  - name: deepseek-v3
    display_name: DeepSeek V3 (OpenRouter)
    use: langchain_openai:ChatOpenAI
    model: deepseek/deepseek-v3
    base_url: https://openrouter.ai/api/v1
    api_key: $OPENROUTER_API_KEY
```

#### 3.2.3 配置 API Keys

编辑 `.env` 文件：

```bash
# OpenAI
OPENAI_API_KEY=sk-xxxx

# OpenRouter
OPENROUTER_API_KEY=sk-or-v1-xxxx

# 搜索（可选）
TAVILY_API_KEY=xxx

# InfoQuest（字节自家搜索）
INFOQUEST_API_KEY=xxx
```

### 3.3 启动方式

#### 3.3.1 Docker 部署（推荐）

**开发模式（热重载）**：

```bash
# 仅首次或镜像更新时拉取沙箱镜像
make docker-init

# 启动服务
make docker-start
```

**生产模式**：

```bash
make up    # 构建并启动所有服务
make down  # 停止并移除容器
```

**访问地址**：`http://localhost:2026`

#### 3.3.2 本地开发

```bash
# 检查依赖
make check

# 安装依赖
make install

# 可选：预拉取沙箱镜像
make setup-sandbox

# 启动服务
make dev
```

### 3.4 Python 客户端

DeerFlow 提供嵌入式 Python 客户端，无需启动 HTTP 服务即可使用：

```python
from deerflow.client import DeerFlowClient

client = DeerFlowClient()

# 单次对话
response = client.chat("Analyze this paper for me", thread_id="my-thread")

# 流式响应
for event in client.stream("hello"):
    if event.type == "messages-tuple":
        print(event.data["content"])

# 列表操作
models = client.list_models()
skills = client.list_skills()

# 文件上传
client.upload_files("thread-1", ["./report.pdf"])
```

### 3.5 Claude Code 集成

通过 `claude-to-deerflow` 技能，可以在 Claude Code 中直接调用 DeerFlow：

```bash
npx skills add https://github.com/bytedance/deer-flow --skill claude-to-deerflow
```

在 Claude Code 中使用 `/claude-to-deerflow` 命令：

- 发送消息获取流式响应
- 选择执行模式：flash（快速）/ standard / pro（规划）/ ultra（子 Agent）
- 查看健康状态、模型列表、技能列表
- 管理线程和对话历史

### 3.6 IM 渠道配置

#### 3.6.1 Telegram

1. 与 @BotFather 对话，创建 Bot，获取 Token
2. 配置 `.env`：

```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
```

3. 编辑 `config.yaml`：

```yaml
channels:
  telegram:
    enabled: true
    bot_token: $TELEGRAM_BOT_TOKEN
    allowed_users: []  # 空 = 允许所有人
```

#### 3.6.2 Slack

1. 在 api.slack.com 创建 App
2. 配置 Bot Token Scopes：`app_mentions:read`、`chat:write`、`im:history` 等
3. 启用 Socket Mode
4. 配置 `.env`：

```bash
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
```

#### 3.6.3 Feishu/Lark

1. 在飞书开放平台创建应用
2. 启用**机器人**能力
3. 添加权限：`im:message`、`im:message.p2p_msg:readonly`、`im:resource`
4. 配置事件订阅：选择**长连接**模式
5. 配置 `.env`：

```bash
FEISHU_APP_ID=cli_xxxx
FEISHU_APP_SECRET=your_app_secret
```

---

## 四、开发扩展：如何基于 DeerFlow 做二次开发

> **说明**：以下代码示例为教学目的设计，用于说明扩展思路。实际开发时请参考官方文档。

### 4.1 创建自定义技能

在 `/mnt/skills/custom/` 目录下创建新的技能：

```markdown
# my-custom-skill

## 触发条件
当用户要求执行 [特定任务类型] 时触发

## 执行流程
1. 理解用户需求
2. 规划执行步骤
3. 调用必要工具
4. 返回结构化结果

## 工具要求
- web_search
- file_read
- bash

## 最佳实践
- 保持步骤简洁
- 每步验证结果
- 错误处理完善
```

### 4.2 添加自定义工具

```python
from deerflow.tools import BaseTool, ToolResult

class MyCustomTool(BaseTool):
    name = "my_tool"
    description = "执行自定义任务"

    async def execute(self, **kwargs) -> ToolResult:
        # 实现工具逻辑
        result = await self.do_something(kwargs)

        return ToolResult(
            success=True,
            data=result,
            metadata={"tool": "my_tool"}
        )
```

### 4.3 自定义 IM 渠道

DeerFlow 的 IM 渠道架构支持扩展。要添加新渠道：

```python
from deerflow.channels import BaseChannel

class MyChannel(BaseChannel):
    name = "my_channel"

    async def connect(self):
        """建立连接"""
        pass

    async def disconnect(self):
        """断开连接"""
        pass

    async def send_message(self, user: str, message: str):
        """发送消息"""
        pass

    def parse_incoming(self, raw_data: dict) -> Message:
        """解析收到的消息"""
        return Message(...)
```

### 4.4 扩展模型支持

DeerFlow 基于 LangChain，支持任意 OpenAI 兼容 API。要添加新模型：

```yaml
models:
  - name: my-model
    display_name: My Model
    use: langchain_openai:ChatOpenAI
    model: my-model-name
    api_key: $MY_MODEL_API_KEY
    base_url: https://my-model-endpoint.com/v1
    max_tokens: 4096
```

---

## 五、总结与展望

### 5.1 核心要点回顾

| 维度 | 要点 |
|------|------|
| **设计思想** | Super Agent Harness，开箱即用的完整运行时 |
| **核心创新** | Sub-Agent 并行、Skills 系统、沙箱隔离、IM 渠道 |
| **技术栈** | LangGraph + LangChain + Docker |
| **适用场景** | 复杂多步骤任务、跨会话记忆、团队协作 |
| **安全特性** | Docker 沙箱隔离、127.0.0.1 本地部署 |

### 5.2 与同类项目对比

| 项目 | Stars | Sub-Agent | Skills | 沙箱 | IM 渠道 |
|------|-------|-----------|--------|------|---------|
| **DeerFlow** | **50.5k** | ✅ | ✅ Markdown | ✅ Docker | ✅ 3种 |
| AutoGPT | 165k | ⚠️ 有限 | ❌ | ❌ | ❌ |
| LangGraph | - | ✅ | ⚠️ | ⚠️ | ⚠️ |
| OpenAI Swarm | - | ✅ | ⚠️ | ❌ | ❌ |

### 5.3 适用与不适用场景

**适用**：
- 需要复杂多步骤研究任务的场景
- 需要团队协作和多 Agent 配合的场景
- 需要跨会话记住用户偏好的个人助理
- 需要从多种 IM 渠道接入的企业应用

**不适用**：
- 需要毫秒级响应的实时交互
- 完全无网络的纯本地环境（需要 Docker）
- 简单的一次性问答

### 5.4 安全注意事项

⚠️ **重要**：DeerFlow 设计为**本地可信环境**部署（默认仅 127.0.0.1 访问）。

如需跨设备/跨网络部署，必须：

1. **IP 白名单**：使用 iptables 或硬件防火墙配置
2. **认证网关**：配置 nginx 反向代理 + 强认证
3. **网络隔离**：将 Agent 放在专用 VLAN
4. **保持更新**：跟进安全更新

---

## 参考资源

| 资源 | 链接 |
|------|------|
| 官方主页 | https://deerflow.tech |
| GitHub | https://github.com/bytedance/deer-flow |
| 官方文档 | https://deerflow.tech/docs |
| 配置指南 | /backend/docs/CONFIGURATION.md |
| MCP Server | /backend/docs/MCP_SERVER.md |
| Discord | https://discord.gg/deerflow |
| 官方公众号 | 字节跳动方舟 |

---

**文档信息**

- 难度：⭐⭐⭐⭐ | 类型：专家设计 | 更新日期：2026-03-28 | 预计阅读时间：55 分钟
