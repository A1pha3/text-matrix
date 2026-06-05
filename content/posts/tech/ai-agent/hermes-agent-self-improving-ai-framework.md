---
title: "Hermes Agent：自改进 AI Agent 框架从入门到精通"
date: "2026-03-28T16:00:00+08:00"
slug: "hermes-agent-self-improving-ai-framework"
aliases:
  - /posts/tech/hermes-agent-self-improving-ai-framework/
    - /posts/tech/hermes-agent-curator/
    - /posts/tech/hermes-agent-growing-ai-agent-framework/
    - /posts/tech/hermes-agent-nous-self-improving-ai-agent/
    - /posts/tech/hermes-agent-self-improving-ai-agent/
    - /posts/tech/hermes-agent-orange-book-complete-guide/
description: "深度解析 Hermes Agent 自改进 AI Agent 框架：内置学习循环、多平台 Gateway、Skills 系统、模型无关架构，详解原理、架构、使用与二次开发。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "自改进", "多平台", "Skills系统", "Nous Research"]
---

# Hermes Agent：自改进 AI Agent 框架

大多数 AI Agent 有一个共同的短板：每次会话都是全新的开始。Agent 学会了一个新技能，会话结束后就丢了；用户反复解释同一套偏好，Agent 每次都得从头来。Hermes Agent 的做法不同——它把从经验中学习写进了架构，不是口号。

## 目录

1. [传统 Agent 的问题](#1-传统-agent-的问题)
2. [架构：Gateway / Skills / Memory / Learning Loop](#2-架构gateway--skills--memory--learning-loop)
3. [安装与配置](#3-安装与配置)
4. [二次开发：自定义 Tool / Skill / Gateway](#4-二次开发自定义-tool--skill--gateway)
5. [与同类项目对比](#5-与同类项目对比)
6. [FAQ](#6-faq)

## 1. 传统 Agent 的问题

### 1.1 传统 Agent 的局限性

当前的 AI Agent（如 GPT-4 Code Interpreter、Claude Code Agent）普遍存在以下问题：

**知识无法积累**：每次会话都是全新的开始，Agent 无法记住之前学到的技能和经验。用户需要反复解释相同的偏好、规则和上下文。

**技能无法复用**：当 Agent 学会了一个新技能（如「如何用特定工具做 X」），这个技能只存在于当前会话，下一次又要重新学习。

**平台绑定严重**：大多数 Agent 只能在单一平台运行（如只能在 Slack 或只能在 Telegram），切换平台意味着重新配置和部署。

**模型锁定**：Agent 与特定的 LLM 提供商强耦合，切换模型往往需要大量代码改动。

### 1.2 Hermes Agent 的核心思想

Hermes Agent 提出了一个关键洞察：**Agent 应该像人类一样，能够从经验中学习并将技能传承下去**。

其核心理念：

1. **持久化知识**：Agent 的学习成果不是随着会话结束而消失，而是持久化存储
2. **技能显式化**：从经验中生成的技能可以被显式命名、描述和复用
3. **多平台统一**：通过 Gateway 架构，实现一套 Agent 代码，多平台消息接入
4. **模型无关**：支持任意 LLM 提供商，切换模型无需改动核心代码

### 1.3 内置学习循环的机制

Hermes Agent 的「内置学习循环」是其最大特色，它实现了：

**技能创建（Skill Creation）**：当 Agent 发现某个任务被重复执行时，它会自动将操作步骤封装为一个可复用的 Skill。

**技能改进（Skill Improvement）**：在 Skill 使用过程中，Agent 会根据反馈持续改进 Skill 的描述和实现。

**知识沉淀（Knowledge Persistence）**：通过 `hermes pick` 命令，Agent 可以将重要信息持久化到知识库。

**会话检索（Session Search）**：Agent 可以搜索自己过去的会话，快速找到类似问题的解决方案。

**用户建模（User Modeling）**：Agent 会在长期交互中逐渐构建对用户的认知模型，了解用户的偏好、习惯和专业领域。

---

## 2. 架构：Gateway / Skills / Memory / Learning Loop

### 2.1 整体架构

```mermaid
flowchart TB
    subgraph GW["Gateway Layer (消息网关)"]
        TG["Telegram"]
        DC["Discord"]
        SL["Slack"]
        WA["WhatsApp"]
        SG["Signal"]
    end

    subgraph CORE["Agent Core"]
        SK["Skills System"]
        TL["Tools System"]
        MM["Memory System"]
        MR["Model Router"]
    end

    subgraph LEARN["Learning Loop"]
        C1["1. Create"]
        C2["2. Validate"]
        C3["3. Improve"]
        C4["4. Persist"]
        C5["5. Retrieve"]
        C6["6. Apply"]
        C1-->C2-->C3-->C4-->C5-->C6-->C1
    end

    subgraph LLM["LLM Providers"]
        O1["OpenRouter 200+"]
        O2["OpenAI"]
        O3["Nous Portal"]
        O4["MiniMax"]
        O5["Custom Endpoint"]
    end

    GW --> CORE
    CORE --> LEARN
    CORE --> LLM
```

### 2.2 核心模块详解

#### 2.2.1 Gateway Layer（消息网关）

Gateway 是 Hermes Agent 的多平台接入层。它实现了：

**统一消息协议**：将不同平台（Telegram、Discord、Slack 等）的消息格式统一转换为内部格式，Agent 核心无需关心消息来自哪个平台。

**会话管理**：维护跨平台的用户会话状态，实现对话连续性。

**命令路由**：将用户输入的斜杠命令（如 `/help`、`/skill`）路由到对应的处理函数。

**媒体处理**：支持语音转文字、图片处理、文件上传下载等。

**支持的平台**：

| 平台 | 状态 | 特点 |
|------|------|------|
| Telegram | ✅ 稳定 | 完整支持，包括语音、文件 |
| Discord | ✅ 稳定 | 支持 slash commands |
| Slack | ✅ 稳定 | 支持 block kit UI |
| WhatsApp | ✅ 稳定 | 支持语音消息转录 |
| Signal | ✅ 稳定 | 端到端加密 |
| CLI | ✅ 稳定 | 全功能 TUI 界面 |

#### 2.2.2 Skills System（技能系统）

Skills 是 Hermes Agent 的核心创新。每个 Skill 包含：

**名称与描述**：Skill 的功能概述

**触发条件**：何时应该使用这个 Skill

**执行步骤**：具体的操作流程

**元数据**：使用次数、成功率、上次使用时间

**Skills 分类**：

1. **内置 Skills（Built-in Skills）**
   - `meet` - 会议记录与总结
   - `todo` - 任务管理与提醒
   - `web` - 网页搜索与内容提取
   - `code` - 代码编写与调试
   - `file` - 文件操作

2. **用户 Skills（User Skills）**
   - 用户通过经验创建的 Skills
   - 持久化存储在 `~/.hermes/skills/`
   - 可以导出分享给其他人

3. **可选 Skills（Optional Skills）**
   - 官方维护的高级 Skills
   - 需要单独安装
   - 如 Docker 管理、数据库操作等

**Skill 生命周期**：

```
创建 → 验证 → 使用 → 改进 → 归档/删除
```

Agent 会在使用过程中自动评估 Skill 的效果，对高频使用的 Skill 进行优化。

#### 2.2.3 Tools System（工具系统）

Tools 是 Agent 与外部世界交互的接口。

**核心 Tools**：

| Tool | 功能 | 实现方式 |
|------|------|---------|
| `bash` | 执行 shell 命令 | subprocess |
| `read` | 读取文件 | 内置 |
| `write` | 写入文件 | 内置 |
| `glob` | 文件搜索 | pathlib |
| `grep` | 内容搜索 | 内置 |
| `web_fetch` | 获取网页内容 | requests |
| `browser` | 浏览器自动化 | Playwright |
| `sqlite` | SQLite 数据库 | 内置 |

**工具调用控制**：

Hermes Agent 实现了工具调用的细粒度控制：

- **预算控制（Budget）**：限制工具调用的次数和消耗
- **超时控制（Timeout）**：防止工具长时间运行
- **审批机制（Approval）**：危险操作需要用户确认
- **沙箱隔离（Sandbox）**：在隔离环境中执行代码

#### 2.2.4 Memory System（记忆系统）

Memory System 是 Hermes Agent 实现持久化学习的关键。

**记忆分层**：

| 层级 | 内容 | 持久化 |
|------|------|--------|
| Working Memory | 当前会话上下文 | 会话结束清除 |
| Short-term | 近期重要信息 | 7 天后降级 |
| Long-term | 核心知识与技能 | 永久保留 |
| User Model | 用户偏好与习惯 | 永久保留 |

**知识检索**：

Hermes Agent 使用语义搜索来检索记忆：

```python
# 示例：从记忆中搜索相关内容
results = hermes.memory.search("Python 异步编程", top_k=5)
```

#### 2.2.5 Learning Loop（学习循环）

这是 Hermes Agent 区别于其他 Agent 的核心技术。

**学习循环流程**：

```
┌─────────────────────────────────────────────────────────────────┐
│                      Hermes Agent 学习循环                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. 经验捕捉 (Experience Capture)                                │
│     └── 监听工具调用、用户反馈、任务结果                          │
│                              ↓                                   │
│  2. 技能提取 (Skill Extraction)                                 │
│     └── 识别重复模式，提取为可复用技能                           │
│                              ↓                                   │
│  3. 技能验证 (Skill Validation)                                  │
│     └── 在小规模测试验证技能有效性                               │
│                              ↓                                   │
│  4. 技能改进 (Skill Refinement)                                 │
│     └── 根据反馈优化技能描述和参数                               │
│                              ↓                                   │
│  5. 知识归档 (Knowledge Archival)                                │
│     └── 持久化到长期记忆，供后续使用                             │
│                              ↓                                   │
│  6. 主动应用 (Proactive Application)                            │
│     └── 在新任务中主动推荐相关技能                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**自我改进机制**：

- **轨迹压缩（Trajectory Compression）**：将多轮对话压缩为简洁的技能描述
- **元学习（Meta-learning）**：学习如何更有效地学习
- **偏好对齐（Preference Alignment）**：根据用户反馈调整行为模式

### 2.3 技术选型

#### 2.3.1 为什么用 SQLite 做状态管理

Hermes Agent 选择 SQLite 作为状态存储，而非更复杂的数据库，原因在于：

**简单可靠**：SQLite 是嵌入式数据库，无需单独的服务进程，随应用一起分发。

**持久化优先**：对话历史、技能、用户模型都需要长期存储，文件系统不够结构化。

**性能足够**：对于单用户 Agent 的规模，SQLite 的性能完全足够。最新版本（v0.4.0）修复了 WAL 写入锁竞争问题。

**可移植性**：SQLite 数据库文件可以轻松迁移和备份。

#### 2.3.2 为什么支持这么多 LLM 提供商

通过 OpenRouter 集成，Hermes Agent 可以访问 200+ 模型：

**成本优化**：不同任务用不同成本的模型。简单任务用便宜模型，复杂推理用高级模型。

**能力平衡**：某些模型在特定任务上表现更好。如 Claude 在代码任务上强，GPT-4 在创意任务上优。

**避免锁定**：不依赖单一提供商，防止服务中断影响工作。

**最新支持**：v0.4.0 已添加 Hugging Face 作为一等公民的推理提供商。

### 2.4 版本演进

| 版本 | 发布日期 | 主要特性 |
|------|---------|---------|
| v0.4.0 | 2026-03-24 | Hugging Face 支持、TIRITH 改进、Nix 构建 |
| v0.3.0 | 2026-03-17 | 技能系统 2.0、记忆检索增强 |
| v0.2.0 | 2026-03-12 | 多平台 Gateway、CLI 改进 |
| v0.1.0 | 2026-02 | 初始版本 |

---

## 3. 安装与配置

### 3.1 环境准备

**系统要求**：
- Python 3.11+
- 2GB+ RAM
- 1GB+ 磁盘空间
- 网络连接（用于 LLM API 调用）

**支持的系统**：
- macOS 12+
- Linux（Ubuntu 20.04+、Debian 11+）
- Windows（通过 WSL2）
- 甚至可以在 $5/月的 VPS 上运行

### 3.2 安装步骤

**方式一：官方安装脚本（推荐）**

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

**方式二：PyPI 安装**

```bash
pip install hermes-agent
```

**方式三：源码安装**

```bash
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
./setup-hermes.sh
```

### 3.3 配置 LLM 提供商

**方式一：使用 OpenRouter（推荐，最简单）**

```bash
export OPENROUTER_API_KEY=sk-or-v1-xxxx
hermes config set model openrouter/anthropic/claude-3.5-sonnet
```

**方式二：使用 OpenAI**

```bash
export OPENAI_API_KEY=sk-xxxx
hermes config set model gpt-4-turbo
```

**方式三：使用 Nous Portal（免费额度）**

```bash
export NOUS_API_KEY=xxx
hermes config set model nous/<model-name>
```

**方式四：使用自定义端点**

```bash
export CUSTOM_API_KEY=xxx
hermes config set model custom/<model-name>
hermes config set api_base https://your-custom-endpoint.com/v1
```

**方式五：Hugging Face（v0.4.0 新增）**

```bash
export HF_TOKEN=hf-xxxx
hermes config set model huggingface/<model-id>
```

### 3.4 配置消息平台

#### 3.4.1 Telegram Bot

1. 在 Telegram 创建 Bot（@BotFather 获取 Token）
2. 配置环境变量：

```bash
export TELEGRAM_BOT_TOKEN=123456:ABC-DEF
hermes config set platform telegram
```

3. 启动 Agent：

```bash
hermes run
```

#### 3.4.2 Discord Bot

1. 在 Discord Developer Portal 创建 Application
2. 添加 Bot，获取 Token
3. 配置权限和 Intent
4. 配置环境变量：

```bash
export DISCORD_BOT_TOKEN=xxxx.xxxx.xxxx
hermes config set platform discord
```

#### 3.4.3 其他平台

WhatsApp、Slack、Signal 的配置类似，都需要先在对应平台创建应用，然后配置 Token。

### 3.5 CLI 界面详解

```bash
hermes run          # 启动 CLI 交互模式
hermes run --model  # 指定模型
hermes run --debug  # 调试模式
```

**CLI 常用命令**：

| 命令 | 功能 |
|------|------|
| `/help` | 显示帮助 |
| `/skill list` | 列出所有技能 |
| `/skill create` | 创建新技能 |
| `/memory search` | 搜索记忆 |
| `/model` | 切换模型 |
| `/exit` | 退出 |

### 3.6 Python API 调用

```python
from hermes import Hermes

# 初始化
hermes = Hermes(
    model="openrouter/anthropic/claude-3.5-sonnet",
    api_key="sk-or-v1-xxxx"
)

# 单次对话
response = hermes.chat("解释一下什么是异步编程")
print(response)

# 带上下文的对话
hermes.add_message("user", "Python 如何处理并发？")
hermes.add_message("assistant", "Python 有多种并发方式...")
response = hermes.chat("有什么区别？")

# 执行工具
result = hermes.run_tool("bash", {"command": "ls -la"})
print(result)

# 管理技能
skills = hermes.list_skills()
print(skills)

# 搜索记忆
results = hermes.search_memory("异步编程最佳实践")
```

### 3.7 自定义配置

配置文件位于 `~/.hermes/config.yaml`：

```yaml
model:
  provider: openrouter
  name: anthropic/claude-3.5-sonnet

platform:
  enabled:
    - telegram
    - discord
    - cli
  default: telegram

skills:
  auto_create: true
  auto_improve: true
  storage_dir: ~/.hermes/skills

memory:
  retention_days: 90
  vector_store: sqlite

tools:
  timeout: 300
  max_calls: 100
  require_approval:
    - bash
    - write
    - delete
```

---

## 4. 二次开发：自定义 Tool / Skill / Gateway

> **说明**：以下代码示例为教学目的设计，用于说明扩展思路。实际开发时请参考官方文档和源码。

### 4.1 创建自定义 Tool

假设你需要创建一个与公司内部系统交互的 Tool：

```python
from hermes.tools import BaseTool, ToolResult
from typing import Dict, Any

class CompanyTool(BaseTool):
    """公司内部系统集成 Tool"""

    name = "company"
    description = "访问公司内部系统：日历、邮件、文档"

    def __init__(self, api_base: str, api_key: str):
        self.api_base = api_base
        self.api_key = api_key

    async def execute(self, action: str, **kwargs) -> ToolResult:
        """执行公司系统操作"""
        endpoints = {
            "calendar": f"{self.api_base}/calendar",
            "email": f"{self.api_base}/email",
            "docs": f"{self.api_base}/documents"
        }

        if action not in endpoints:
            return ToolResult(success=False, error=f"未知操作: {action}")

        # 实现具体的 API 调用逻辑
        response = await self._make_request(
            endpoints[action],
            kwargs
        )

        return ToolResult(success=True, data=response)

# 注册 Tool
hermes.register_tool(CompanyTool(
    api_base="https://api.company.com",
    api_key="xxx"
))
```

### 4.2 创建自定义 Skill

```python
from hermes.skills import BaseSkill, SkillMetadata

class CodeReviewSkill(BaseSkill):
    """代码审查 Skill"""

    name = "code_review"
    description = "对代码进行安全性和性能审查"

    trigger_conditions = [
        "审查代码",
        "检查 bug",
        "代码审查"
    ]

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        code = context.get("code", "")
        language = context.get("language", "python")

        prompt = f"""请审查以下 {language} 代码，重点关注：
1. 安全性问题（SQL注入、XSS等）
2. 性能问题（N+1查询、内存泄漏等）
3. 代码规范（PEP8、最佳实践）

代码：
```{language}
{code}
```"""

        response = await hermes.llm.generate(prompt)

        return {
            "review": response,
            "issues": self._parse_issues(response),
            "score": self._calculate_score(response)
        }

# 注册 Skill
hermes.register_skill(CodeReviewSkill())
```

### 4.3 扩展 Gateway 支持新平台

要添加一个新的消息平台（如企业微信）：

```python
from hermes.gateway import BaseAdapter, Message, User

class EnterpriseWeChatAdapter(BaseAdapter):
    """企业微信适配器"""

    platform_name = "enterprise-wechat"

    def __init__(self, corp_id: str, corp_secret: str):
        self.corp_id = corp_id
        self.corp_secret = corp_secret
        self.token = None

    async def connect(self):
        """建立连接"""
        # 获取访问令牌
        url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken"
        params = {
            "corpid": self.corp_id,
            "corpsecret": self.corp_secret
        }
        response = await self.http_get(url, params)
        self.token = response["access_token"]

    async def disconnect(self):
        """断开连接"""
        self.token = None

    async def send_message(self, user: User, message: Message):
        """发送消息"""
        url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send"
        data = {
            "touser": user.platform_id,
            "msgtype": "text",
            "agentid": self.agent_id,
            "text": {"content": message.content}
        }
        await self.http_post(url, data, token=self.token)

    def parse_incoming(self, raw_data: dict) -> Message:
        """解析收到的消息"""
        return Message(
            content=raw_data["Content"],
            user_id=raw_data["FromUserName"],
            platform=self.platform_name,
            message_id=raw_data["MsgId"]
        )

# 注册适配器
hermes.register_adapter(EnterpriseWeChatAdapter(
    corp_id="xxx",
    corp_secret="xxx"
))
```

### 4.4 自定义学习策略

```python
from hermes.learning import BaseLearningStrategy, Experience

class ConservativeLearningStrategy(BaseLearningStrategy):
    """保守学习策略：只学习高置信度的模式"""

    min_confidence = 0.9
    min_occurrences = 5

    async def should_learn(self, experience: Experience) -> bool:
        """判断是否应该学习这个经验"""
        # 必须满足多个条件
        if experience.confidence < self.min_confidence:
            return False

        if experience.occurrence_count < self.min_occurrences:
            return False

        # 必须是成功的经验
        if not experience.outcome.success:
            return False

        return True

    async def extract_skill(self, experience: Experience) -> Dict[str, Any]:
        """从经验中提取技能"""
        return {
            "name": f"auto_skill_{experience.id[:8]}",
            "description": experience.summary,
            "trigger": experience.trigger,
            "actions": experience.action_sequence,
            "confidence": experience.confidence,
            "source": "auto_learned"
        }

# 应用学习策略
hermes.set_learning_strategy(ConservativeLearningStrategy())
```

---

## 5. 与同类项目对比

### 5.1 核心要点回顾

| 维度 | 要点 |
|------|------|
| **设计思想** | 自改进 Agent，内置学习循环 |
| **架构优势** | Gateway 多平台、Skills 可复用、Memory 持久化 |
| **技术选型** | SQLite 状态存储、OpenRouter 模型聚合 |
| **应用场景** | 个人助手、客服机器人、自动化工作流 |
| **独特功能** | 技能创建、记忆检索、多平台消息 |

### 5.2 与同类项目对比

| 项目 | Stars | 多平台 | 自学习 | 模型无关 |
|------|-------|--------|--------|---------|
| **Hermes Agent** | 14.8k | ✅ 6 平台 | ✅ 内置循环 | ✅ 200+ |
| Claude Code | - | ❌ | ❌ | ❌ |
| GPT-4 Code Interpreter | - | ❌ | ❌ | ❌ |
| AutoGPT | 165k | ❌ | ⚠️ 有限 | ⚠️ OpenAI |
| LangGraph | - | ❌ | ❌ | ✅ |

### 5.3 适用与不适用场景

**适用**：
- 需要长期记忆和多平台接入的个人 AI 助手
- 需要从经验中学习技能的自动化流程
- 需要灵活切换模型的开发环境
- 需要在廉价 VPS 上运行的 Agent

**不适用**：
- 需要实时音视频交互的场景
- 需要复杂多 Agent 协作的任务
- 需要毫秒级响应的交易系统

### 6. FAQ

**Q: Hermes Agent 的自改进和普通 LLM 的上下文学习有什么区别？**

普通 LLM 的上下文学习（in-context learning）只存活在当前会话，关闭后全部丢弃。Hermes Agent 的学习循环把经验持久化到 SQLite 数据库中——技能被显式命名、描述，下次会话可以直接复用。一个学会的「Python 代码审查」技能不会因为关掉终端就消失。

**Q: 多平台 Gateway 需要一直开着吗？**

需要。Gateway 充当消息平台和 Agent 之间的桥梁，进程停下就无法收发消息。但 Agent 的状态（技能、记忆、用户模型）都持久化在 SQLite 中，重启 Gateway 后状态恢复。

**Q: 和其他 Agent 框架（LangChain、AutoGPT）有什么本质区别？**

LangChain 是通用 Agent 构建框架，不内置自改进机制；AutoGPT 的自改进停留在提示词层面（把这次输出作为下次输入）。Hermes Agent 把学习循环写成架构级抽象——技能创建、验证、改进、归档是一条完整流水线，不依赖单次提示词。

**Q: $5/月 VPS 能跑吗？**

能。Hermes Agent 本身只是一个消息路由 + 数据库写入的进程，资源消耗很低。真正消耗资源的是 LLM API 调用，这部分成本由 LLM 提供商决定，和 Hermes 无关。
