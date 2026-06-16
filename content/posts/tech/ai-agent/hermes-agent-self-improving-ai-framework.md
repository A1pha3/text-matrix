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

大多数 AI Agent 有一个共同的短板：每次会话都是全新的开始。Agent 学会了一个新技能，会话结束后就丢了；用户反复解释同一套偏好，Agent 每次都得从头来。Hermes Agent 把从经验中学习写进了架构，不是停留在口号层面。

## 目录

1. [传统 Agent 的问题](#1-传统-agent-的问题)
2. [架构：Gateway / Skills / Memory / Learning Loop](#2-架构 gateway--skills--memory--learning-loop)
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

1. **持久化知识**：Agent 的学习成果持久化存储，不会随会话结束而消失
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
```text
创建 → 验证 → 使用 → 改进 → 归档/删除
```textpython
# 示例：从记忆中搜索相关内容
results = hermes.memory.search("Python 异步编程", top_k=5)
```text
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
```textbash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```textbash
pip install hermes-agent
```textbash
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
./setup-hermes.sh
```textbash
export OPENROUTER_API_KEY=sk-or-v1-xxxx
hermes config set model openrouter/anthropic/claude-3.5-sonnet
```textbash
export OPENAI_API_KEY=sk-xxxx
hermes config set model gpt-4-turbo
```textbash
export NOUS_API_KEY=xxx
hermes config set model nous/<model-name>
```textbash
export CUSTOM_API_KEY=xxx
hermes config set model custom/<model-name>
hermes config set api_base https://your-custom-endpoint.com/v1
```textbash
export HF_TOKEN=hf-xxxx
hermes config set model huggingface/<model-id>
```textbash
export TELEGRAM_BOT_TOKEN=123456:ABC-DEF
hermes config set platform telegram
```textbash
hermes run
```textbash
export DISCORD_BOT_TOKEN=xxxx.xxxx.xxxx
hermes config set platform discord
```textbash
hermes run          # 启动 CLI 交互模式
hermes run --model  # 指定模型
hermes run --debug  # 调试模式
```textpython
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
```textyaml
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
```textpython
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
```textpython
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
3. 代码规范（PEP8、推荐做法）

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
```textpython
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
```textpython
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
