---
title: "Claude API基础专题（一）：认证、请求与会话管理"
date: "2026-03-25T09:30:00+08:00"
slug: "claude-api-authentication-requests-session"
github_repo: "anthropics/anthropic-sdk-python"
aliases:
  - /posts/tech/claude-api-authentication-requests-session/
description: "Claude Messages API 的工程上手：API 密钥管理与 SDK 初始化、消息请求构建、响应结构解析、多轮会话管理、系统提示词与结构化输出。"
draft: false
categories: ["技术笔记"]
tags: ["Claude", "API", "Python"]
---

# Claude API 基础专题（一）：认证、请求与会话管理

Claude Messages API 的入口是一个 `messages.create()` 调用。本文从工程实践角度梳理认证、密钥管理、多轮对话、系统提示词和结构化输出等基础问题，代码基于 `anthropic` Python SDK，模型以 `claude-sonnet-4-6` 为例。

---

## 1.1 API认证与密钥管理

### 获取API密钥

1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 注册账户
3. 在「API Keys」页面创建新密钥
4. 复制密钥并妥善保存

### 密钥管理

密钥不应硬编码在代码中。一旦提交到 Git 仓库，即使后续删除，历史记录中仍可追溯。

**开发环境：从环境变量读取**

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

**生产环境：云密钥管理服务**

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

### SDK初始化

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
    model="claude-sonnet-4-6",
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

### 同步请求

```python
from anthropic import Anthropic
import os

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

message = client.messages.create(
    model="claude-sonnet-4-6",
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

### 参数说明

**`model`**

三个模型按能力和成本递增排序（价格为每百万 token，输入/输出）：

| 模型 | 定位 | 输入 | 输出 |
|------|------|------|------|
| `claude-haiku-4-5` | 延迟最低，适合实时聊天、简单问答、大批量任务 | $1 | $5 |
| `claude-sonnet-4-6` | 平衡之选，日常对话、写作、分析的主力模型 | $3 | $15 |
| `claude-opus-4-6` | 最强能力，适合复杂推理和代码生成 | $5 | $25 |

模型名随版本迭代更新，本文示例以 `claude-sonnet-4-6` 为准。选模型先看任务对延迟和能力的敏感度：实时交互用 Haiku，兼顾性能与成本用 Sonnet，复杂推理再上 Opus。

**`max_tokens`**

控制单次请求最多生成的 token（词元）数。1 token 约等于 0.75 个英文单词或 1-2 个中文字符。按输出长度预期设置：短回答 100-200，几段话 500-1000，完整文章 2000-4096。

```python
message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    messages=[{"role": "user", "content": "写一篇2000字的文章..."}]
)
```

**`messages`**

消息列表，每条消息包含 `role`（`user` 或 `assistant`）和 `content`：

```python
messages=[
    {"role": "user", "content": "什么是Python？"},
    {"role": "assistant", "content": "Python是一种高级编程语言..."},
    {"role": "user", "content": "它适合做什么？"}
]
```

### 流式响应

```python
from anthropic import Anthropic
import os

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "讲一个关于程序员的笑话"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
    print()
```

长文本生成时，非流式模式用户需等待数秒到十几秒。流式响应是生产场景的推荐做法。

---

## 1.3 理解响应结构

### Message对象

```python
message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "解释光合作用"}]
)

print(message.id)          # msg_xxxxx
print(message.type)        # "message"
print(message.role)        # "assistant"
print(message.content)     # [ContentBlock(text='...')]
print(message.model)       # "claude-sonnet-4-6"
print(message.stop_reason) # "end_turn"
print(message.stop_sequence) # None
print(message.usage)       # Usage(input_tokens=xx, output_tokens=xx)
```

### 解析内容

```python
for block in message.content:
    if block.type == "text":
        print(block.text)
```

### 停止原因

- `"end_turn"`：正常完成
- `"max_tokens"`：达到 `max_tokens` 限制，响应可能被截断
- `"stop_sequence"`：遇到指定的停止序列

```python
if message.stop_reason == "max_tokens":
    print("响应被截断，建议增加max_tokens值")
elif message.stop_reason == "end_turn":
    print("响应正常完成")
```

### Token使用量

`usage` 给出本次请求消耗的输入和输出 token（词元），是计算成本、优化提示词长度的依据。

```python
print(f"输入token: {message.usage.input_tokens}")
print(f"输出token: {message.usage.output_tokens}")
print(f"总token: {message.usage.input_tokens + message.usage.output_tokens}")

# 计算成本（以 Sonnet 4.6 为例：输入 $3/M，输出 $15/M）
input_cost = (message.usage.input_tokens / 1_000_000) * 3
output_cost = (message.usage.output_tokens / 1_000_000) * 15

print(f"本次请求成本: ${input_cost + output_cost:.6f}")
```

### 错误处理

```python
from anthropic import Anthropic, RateLimitError, APIError
import os

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

try:
    response = client.messages.create(
        model="claude-sonnet-4-6",
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

Claude API 本身是无状态的——每次 `messages.create()` 调用都是独立的。会话由客户端维护的消息列表定义。

**无状态（无记忆）**：

```python
response1 = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "我的狗叫豆豆"}]
)
print(response1.content[0].text)

response2 = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "它喜欢吃什么？"}]
)
# Claude不记得"豆豆"
```

**有状态（有记忆）**：

```python
conversation_history = []

while True:
    user_input = input("你: ")

    conversation_history.append({"role": "user", "content": user_input})

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=conversation_history
    )

    assistant_message = response.content[0].text
    conversation_history.append({"role": "assistant", "content": assistant_message})

    print(f"Claude: {assistant_message}")
```

### 会话管理技巧

**限制历史长度**

```python
def trim_conversation(messages, max_turns=10):
    """只保留最近N轮对话"""
    system_messages = [m for m in messages if m.get("role") == "system"]
    conversation = [m for m in messages if m.get("role") != "system"]

    return system_messages + conversation[-(max_turns * 2):]

messages = trim_conversation(conversation_history, max_turns=5)
```

**摘要旧消息**

用 Haiku 模型压缩早期对话，保留关键信息：

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
        model="claude-haiku-4-5",
        max_tokens=500,
        messages=[{"role": "user", "content": summary_prompt}]
    )

    summary = summary_response.content[0].text

    return [
        {"role": "system", "content": f"对话摘要：{summary}"}
    ] + recent
```

**分离话题**

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

系统提示词（System Prompt）设置 AI 的行为和角色，作用于整个对话。

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system="你是一位专业的产品经理，用词简洁专业。",
    messages=[{"role": "user", "content": "我应该做什么产品？"}]
)
```

### 常见模式

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

回答问题时必须使用以下格式：

## 主要发现
[最重要的1-2个发现]

## 详细分析
[详细的分析内容]

## 建议
[基于分析的可执行建议]

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

### 设计要点

系统提示词应具体、一致、可验证。避免相互矛盾的指令（如同时要求"诚实"和"必要时可以说善意的谎言"），以及过于模糊的设定（如"你是AI助手，回答用户问题"）。

### 测试系统提示词

```python
def test_system_prompt(system_prompt, test_cases):
    """测试系统提示词"""
    for i, test in enumerate(test_cases):
        response = client.messages.create(
            model="claude-sonnet-4-6",
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

需要 AI 返回 JSON 等特定格式数据时，有几种方案，可靠性从低到高。只有结构化输出（方法 2、3）能保证输出格式合法，其余方案都要靠自己的代码兜底。

### 方法 1：提示词中要求 JSON

在提示词里描述期望的 JSON 结构，再手动解析返回文本。实现最直接，但 Claude 可能包裹代码块、加多余文本、漏字段或类型不对，需要自己清洗和重试。

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
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

### 方法 2：结构化输出（output_config.format）

用 `output_config.format` 声明 JSON Schema，Claude 通过受限解码保证输出是合法 JSON 且字段类型、必填项符合 schema，不再出现 `json.loads` 报错或字段缺失。

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1000,
    messages=[{
        "role": "user",
        "content": "返回3个编程语言的列表"
    }],
    output_config={
        "format": {
            "type": "json_schema",
            "schema": {
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
                },
                "required": ["languages"],
                "additionalProperties": False
            }
        }
    }
)

import json
data = json.loads(response.content[0].text)
print(data)
```

几个要点：

- 返回的 JSON 齐全时，直接把 `response.content[0].text` 交给 `json.loads` 即可，无需再清洗。
- 结构化输出保证的是**格式合规，不保证内容正确**。字段类型、必填项一定符合 schema，但值是否合理、事实是否准确仍要自己判断。
- 首次使用某个 schema 会有一次额外的语法编译延迟，之后会缓存约 24 小时，第二次起明显变快。
- schema 里 `required` 的字段会排在 `optional` 之前输出，若字段顺序对下游重要，把字段都设为必填或在解析时按关键词取值。

### 方法 3：Pydantic + messages.parse()

不写原始 JSON Schema，用 Pydantic 模型声明结构，配合 SDK 的 `client.messages.parse()`，返回的 `response.parsed_output` 直接是校验过的模型实例。

```python
from pydantic import BaseModel
from anthropic import Anthropic
import os

class Language(BaseModel):
    name: str
    year: int
    paradigm: str

class LanguageList(BaseModel):
    languages: list[Language]

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

response = client.messages.parse(
    model="claude-sonnet-4-6",
    max_tokens=1000,
    messages=[{"role": "user", "content": "返回3个编程语言的列表"}],
    output_format=LanguageList,
)

print(response.parsed_output)
print(response.parsed_output.languages[0].name)
```

`output_format` 接受一个 Pydantic 模型类，SDK 会把它转成 JSON Schema 传给 `output_config.format`，再用同一个模型校验返回结果。类型错误在解析阶段就会被拦截，省去手写 schema 和手动验证。

### 边界情况

结构化输出在两种情况下可能不满足 schema：模型因安全原因拒绝回答（`stop_reason` 为 `"refusal"`），或输出被 `max_tokens` 截断（`stop_reason` 为 `"max_tokens"`）。前者按拒绝处理，后者调大 `max_tokens` 重试。

```python
if message.stop_reason == "refusal":
    print("模型拒绝回答")
elif message.stop_reason == "max_tokens":
    print("输出被截断，建议增加max_tokens")
```

如果仍需手动解析不可靠的 JSON 文本（比如方法 1 的产物），可以用一个容错解析函数兜底：

```python
def safe_json_parse(text):
    """安全解析JSON，处理代码块和多余文本"""
    import json
    import re

    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find('{')
    end = text.rfind('}') + 1
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass

    return None
```

---

**参考资源：**
- [Anthropic Messages API 文档](https://platform.claude.com/docs/en/api/messages)
- [Structured outputs 文档](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)
- [Anthropic Python SDK（anthropic）](https://github.com/anthropics/anthropic-sdk-python)
- [Anthropic Console](https://console.anthropic.com/)

