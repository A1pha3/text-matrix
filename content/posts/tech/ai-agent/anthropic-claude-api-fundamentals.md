---
title: "Claude API基础专题（一）：认证、请求与会话管理"
date: "2026-03-25T09:30:00+08:00"
slug: "claude-api-authentication-requests-session"
aliases:
  - /posts/tech/claude-api-authentication-requests-session/
description: "本文详细介绍了Claude API的认证方式（API Key与Bearer Token）、HTTP请求构建、会话管理机制，以及如何实现结构化输出。适合入门开发者阅读。"
draft: false
categories: ["技术笔记"]
tags: ["Claude", "API", "Python"]
---

# Claude API 基础专题（一）：认证、请求与会话管理

Claude 的 Messages API 设计非常简洁——一个 `messages.create()` 调用就能完成一次对话。但简洁不等于简单。认证怎么做、密钥怎么放、多轮对话怎么维护上下文、结构化输出用什么方案最稳——这些问题在官方文档里都有答案，但答案和答案之间缺少一层"工程判断"：什么场景该用什么模式、什么做法会踩坑。

本文从工程实践角度梳理这几个基础问题，代码基于 `anthropic` Python SDK，版本以 `claude-sonnet-4-20250514` 为例。

---

## 1.1 API认证与密钥管理

### 什么是API密钥

API密钥（API Key）是Anthropic分配给你的唯一标识符，用于验证请求来源。每个密钥关联到你的账户，追踪使用量并控制访问权限。

获取步骤：

1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 注册账户（需要信用卡用于计费，但有免费额度）
3. 在「API Keys」页面创建新密钥
4. 复制密钥并妥善保存

### 密钥管理的工程实践

密钥硬编码是新手最常见的错误，但后果远不止"不规范"——一旦密钥被提交到 Git 仓库，即使后续删除，Git 历史里仍然可查。某团队曾因三年前提交中的一个密钥被自动化脚本扫描到，导致账户被用于加密货币挖矿，损失数千美元。

**正确做法：从环境变量读取**

```python
import os
from anthropic import Anthropic

api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY环境变量未设置")

client = Anthropic(api_key=api_key)
```

**开发环境推荐：.env 文件**

```bash
# .env文件（不要提交到Git！）
ANTHROPIC_API_KEY=<your-real-key>
```

```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.environ.get("ANTHROPIC_API_KEY")

from anthropic import Anthropic
client = Anthropic(api_key=api_key)
```

```bash
pip install python-dotenv
```

**生产环境推荐：云密钥管理服务**

```python
import boto3
import json
from anthropic import Anthropic

secret_name = "anthropic-api-key"
region_name = "us-east-1"

session = boto3.session.Session()
client_secrets = session.client(
    service_name='secretsmanager',
    region_name=region_name
)

response = client_secrets.get_secret_value(SecretId=secret_name)
api_key = json.loads(response['SecretString'])['api_key']

anthropic_client = Anthropic(api_key=api_key)
```

### SDK初始化推荐做法

```python
from anthropic import Anthropic
import os

class AnthropicClient:
    """Anthropic API客户端封装"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._client = Anthropic(
                api_key=os.environ.get("ANTHROPIC_API_KEY"),
                timeout=30,
                max_retries=3,
            )
        return cls._instance

    @property
    def client(self):
        return self._client

# 使用单例模式
anthropic = AnthropicClient()
response = anthropic.client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
)
```

---

## 1.2 发送第一个请求

### 安装 SDK

```bash
pip install anthropic
```

### 同步请求完整示例

```python
from anthropic import Anthropic
import os

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": "用一句话解释什么是量子计算"
        }
    ]
)

print(message.content[0].text)
```

### 参数详解

**`model` 参数**

三个模型按能力和成本排序：

- `claude-opus-4-20250514`：最强能力，适合复杂分析和代码生成。成本最高，响应最慢。
- `claude-sonnet-4-20250514`：平衡之选，日常对话、写作、分析的主力模型。大多数场景下够用。
- `claude-haiku-3-20250514`：快速响应，适合实时聊天和简单问答。延迟最低，成本最低。

选型建议：如果响应时间敏感（如聊天机器人），用 Haiku；如果任务复杂要推理质量，用 Opus；拿不准就从 Sonnet 开始。

**`max_tokens` 参数**

控制单次请求最多生成的 token 数。Token 是文本处理的最小单位（1 个 token 约等于 0.75 个英文单词或 1-2 个中文字符）。

```python
message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    messages=[{"role": "user", "content": "写一篇2000字的文章..."}]
)
```

一个常见误区是把 `max_tokens` 设得很大来"保证完整输出"——这会浪费 token（按量计费）。更好的做法是根据输出长度预期设置合理值：短回答 100-200，几段话 500-1000，完整文章 2000-4096。

**`messages` 参数**

消息列表，每条消息包含 `role`（`user` 或 `assistant`）和 `content`（字符串内容）：

```python
messages=[
    {"role": "user", "content": "什么是Python？"},
    {"role": "assistant", "content": "Python是一种高级编程语言..."},
    {"role": "user", "content": "它适合做什么？"}
]
```

### 流式响应

需要实时显示打字效果时使用流式响应：

```python
from anthropic import Anthropic
import os

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

with client.messages.stream(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "讲一个关于程序员的笑话"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
    print()
```

流式响应的核心价值在于用户体验——用户不需要对着空白屏幕等待。对于长文本生成，流式几乎是必须的，因为非流式模式下用户会在数秒到十几秒内看不到任何反馈。

---

## 1.3 理解响应结构

### Message对象的完整结构

```python
message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "解释光合作用"}]
)
```

响应结构：

```python
print(message.id)          # msg_xxxxx - 消息唯一ID
print(message.type)        # "message" - 消息类型
print(message.role)        # "assistant" - 角色
print(message.content)     # [ContentBlock(text='...')] - 内容块列表
print(message.model)       # "claude-sonnet-4-20250514" - 使用的模型
print(message.stop_reason) # "end_turn" - 停止原因
print(message.stop_sequence) # None - 停止序列
print(message.usage)       # Usage(input_tokens=xx, output_tokens=xx) - token使用量
```

### 解析响应内容

```python
# 安全获取文本内容
for block in message.content:
    if block.type == "text":
        print(block.text)
```

### 停止原因

`stop_reason` 的值告诉你为什么响应停止了：

- `"end_turn"`：正常完成，Claude 认为应该停止
- `"max_tokens"`：达到 `max_tokens` 限制，响应可能被截断
- `"stop_sequence"`：遇到指定的停止序列
- `"only_stop_reason"`：仅当 `stop_reason` 是唯一有效停止信号时

```python
if message.stop_reason == "max_tokens":
    print("响应被截断，建议增加max_tokens值")
elif message.stop_reason == "end_turn":
    print("响应正常完成")
```

### Token使用量

```python
print(f"输入token: {message.usage.input_tokens}")
print(f"输出token: {message.usage.output_tokens}")
print(f"总token: {message.usage.input_tokens + message.usage.output_tokens}")

# 计算成本（以 Sonnet 模型为例）
input_cost_per_1k = 0.003
output_cost_per_1k = 0.015

input_cost = (message.usage.input_tokens / 1000) * input_cost_per_1k
output_cost = (message.usage.output_tokens / 1000) * output_cost_per_1k
total_cost = input_cost + output_cost

print(f"本次请求成本: ${total_cost:.6f}")
```

### 错误处理

```python
from anthropic import Anthropic, RateLimitError, APIError
import os

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

try:
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hello"}]
    )
except RateLimitError:
    print("速率限制：请求太频繁，等待后重试")
    import time
    time.sleep(5)
except APIError as e:
    print(f"API错误: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

---

## 1.4 多轮对话与会话管理

多轮对话的核心问题不是"怎么发请求"，而是"怎么维护上下文"。Claude API 本身是无状态的——每次 `messages.create()` 调用都是独立的。所谓"会话"完全由客户端维护的消息列表定义。

**单轮对话（无记忆）**：

```python
response1 = client.messages.create(
    messages=[{"role": "user", "content": "我的狗叫豆豆"}]
)
print(response1.content[0].text)

response2 = client.messages.create(
    messages=[{"role": "user", "content": "它喜欢吃什么？"}]
)
# Claude不记得"豆豆"
```

**多轮对话（有记忆）**：

```python
conversation_history = []

while True:
    user_input = input("你: ")

    conversation_history.append({
        "role": "user",
        "content": user_input
    })

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=conversation_history
    )

    assistant_message = response.content[0].text

    conversation_history.append({
        "role": "assistant",
        "content": assistant_message
    })

    print(f"Claude: {assistant_message}")
```

### 会话管理的进阶技巧

**限制历史消息长度**

对话太长会消耗大量 token，需要限制历史长度：

```python
def trim_conversation(messages, max_turns=10):
    """只保留最近N轮对话"""
    system_messages = [m for m in messages if m.get("role") == "system"]
    conversation = [m for m in messages if m.get("role") != "system"]

    trimmed = conversation[-(max_turns * 2):]

    return system_messages + trimmed

messages = trim_conversation(conversation_history, max_turns=5)
```

**摘要旧消息**

对于超长对话，可以将旧消息摘要——用更便宜的模型（Haiku）压缩早期对话：

```python
def summarize_old_messages(messages, summary_turns=5):
    """将早期对话摘要，保留最近的消息"""
    if len(messages) <= summary_turns * 2 + 2:
        return messages

    early = messages[:-summary_turns * 2]
    recent = messages[-summary_turns * 2:]

    early_text = "\n".join([f"{m['role']}: {m['content']}" for m in early])

    summary_prompt = f"""将以下对话摘要成一段话，保留关键信息：

{early_text}

摘要："""

    summary_response = client.messages.create(
        model="claude-haiku-3-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": summary_prompt}]
    )

    summary = summary_response.content[0].text

    return [
        {"role": "system", "content": f"对话摘要：{summary}"}
    ] + recent
```

**分离不同话题**

```python
class ConversationManager:
    """会话管理器：支持多话题"""

    def __init__(self):
        self.conversations = {}
        self.current_id = None

    def start_new(self, conversation_id):
        self.current_id = conversation_id
        self.conversations[conversation_id] = []

    def add_message(self, role, content):
        if self.current_id is None:
            self.start_new("default")
        self.conversations[self.current_id].append({
            "role": role,
            "content": content
        })

    def get_messages(self, conversation_id=None):
        cid = conversation_id or self.current_id
        return self.conversations.get(cid, [])

    def switch_conversation(self, conversation_id):
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        self.current_id = conversation_id

# 使用示例
manager = ConversationManager()
manager.start_new("技术支持")
manager.add_message("user", "我的代码报错了")
manager.add_message("assistant", "请告诉我错误信息")
manager.add_message("user", "NameError: name 'x' is not defined")

manager.start_new("产品咨询")
manager.add_message("user", "你们的产品有什么特点")

manager.switch_conversation("技术支持")
messages = manager.get_messages()
```

---

## 1.5 系统提示词

系统提示词（System Prompt）是设置 AI 行为和角色的方式，影响整个对话而非单次请求。它的优先级高于用户消息，且对用户不可见。

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    system="你是一位专业的产品经理，用词简洁专业。",
    messages=[{"role": "user", "content": "我应该做什么产品？"}]
)
```

### 有效的系统提示词模式

**角色设定**

```python
system = """你是一位拥有20年经验的高级Python工程师。
你的特点：
- 代码风格遵循PEP 8
- 喜欢用类型提示
- 注重性能优化
- 说话直接，有话直说
"""
```

**输出格式指定**

```python
system = """你是一个数据分析师。

当回答问题时，必须使用以下格式：

## 主要发现
[最重要的1-2个发现]

## 详细分析
[详细的分析内容]

## 建议
[基于分析的 actionable 建议]

## 数据来源
[使用的数据]
"""
```

**约束条件**

```python
system = """你是一位财经记者。

约束条件：
- 不预测具体股价
- 引用数据时注明来源
- 风险提示必须清晰
- 不使用"一定"、"保证"等绝对词汇
"""
```

**示例注入（Few-shot in System）**

```python
system = """你是一个翻译助手。

翻译示例：
- "Hello, how are you?" → "你好，你怎么样？"
- "The weather is nice today." → "今天天气很好。"

注意：
- 中文翻译用"你"而不是"您"
- 保持原文的语气和情感
"""
```

### 系统提示词设计要点

好的系统提示词应该具体、一致、可验证。一个常见的反面模式是给相互矛盾的指令——比如同时要求"诚实"和"必要时可以说善意的谎言"，模型会无所适从。另一个是过于模糊的设定，比如"你是AI助手，回答用户问题"——这几乎不提供任何有效约束，和没有系统提示词没有区别。

### 调试系统提示词

```python
def test_system_prompt(system_prompt, test_cases):
    """测试系统提示词"""
    for i, test in enumerate(test_cases):
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=system_prompt,
            messages=[{"role": "user", "content": test}]
        )
        print(f"测试{i+1}: {test}")
        print(f"响应: {response.content[0].text[:200]}...")
        print("-" * 50)
```

---

## 1.6 结构化输出

需要 AI 返回特定格式的数据（如 JSON）时，有三种方案，可靠性从低到高排列。

### 方法 1：在提示词中要求 JSON

最简单但最不可靠的方法——模型可能不遵循格式，或者在 JSON 前后加额外文字：

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1000,
    messages=[{
        "role": "user",
        "content": """返回一个JSON对象，包含水果信息：
        {"name": "水果名", "color": "颜色", "taste": "味道"}"""
    }]
)

import json
text = response.content[0].text
if "```json" in text:
    text = text.split("```json")[1].split("```")[0]
elif "```" in text:
    text = text.split("```")[1].split("```")[0]

data = json.loads(text.strip())
print(data)
```

### 方法 2：使用 response_format 参数

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1000,
    messages=[{
        "role": "user",
        "content": "返回3个编程语言的列表"
    }],
    response_format={
        "type": "json_object",
        "json_schema": {
            "type": "object",
            "properties": {
                "languages": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "year": {"type": "integer"},
                            "paradigm": {"type": "string"}
                        }
                    }
                }
            }
        }
    }
)

data = json.loads(response.content[0].text)
print(data)
```

### 方法 3：使用工具调用（最可靠）

```python
tools = [{
    "name": "return_data",
    "description": "返回结构化数据",
    "input_schema": {
        "type": "object",
        "properties": {
            "result": {
                "type": "string",
                "description": "处理结果"
            },
            "status": {
                "type": "string",
                "enum": ["success", "error"],
                "description": "处理状态"
            }
        },
        "required": ["result", "status"]
    }
}]

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1000,
    tools=tools,
    messages=[{"role": "user", "content": "处理用户注册"}]
)

for content in response.content:
    if content.type == "tool_use":
        result = content.input
        print(f"Status: {result['status']}")
        print(f"Result: {result['result']}")
```

### 处理边界情况

```python
def safe_json_parse(text):
    """安全解析JSON，处理各种格式"""
    import json
    import re

    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    try:
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
    except:
        pass

    return None
```

---

## 常见错误排查

| 错误 | 原因 | 解决 |
|------|------|------|
| `AuthenticationError` | API密钥无效或未设置 | 检查环境变量 |
| `RateLimitError` | 请求太频繁 | 等待后重试，或实现指数退避 |
| `InvalidRequestError` | 参数错误 | 对照文档检查参数 |
| 响应被截断 | max_tokens 太小 | 增加 max_tokens |
| 回答不相关 | 提示词不清晰 | 优化系统提示词，增加具体示例 |

---

掌握认证、请求构建和会话管理之后，下一步可以深入提示词工程——如何设计高质量的系统提示词、如何利用工具调用实现复杂工作流。这些内容将在本系列后续文章中展开。