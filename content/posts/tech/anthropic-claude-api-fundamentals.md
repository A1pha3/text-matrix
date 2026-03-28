---
title: "Claude API基础专题（一）：认证、请求与会话管理"
date: 2026-03-25
slug: "claude-api-authentication-requests-session"
description: "本文详细介绍了Claude API的认证方式（API Key与Bearer Token）、HTTP请求构建、会话管理机制，以及如何实现结构化输出。适合入门开发者阅读。"
draft: false
categories: ["技术笔记"]
tags: ["Claude", "API", "Python"]
---

# Claude API基础专题（一）：认证、请求与会话管理 ⭐⭐⭐⭐

> **目标读者**：刚开始学习Claude API开发的工程师
> **前置知识**：Python基础、HTTP基本概念
> **学习提醒**：本文非常详细地讲解每个知识点，建议动手实践

---

## 章节导航

本文对应课程第1章「Fundamentals」，涵盖以下内容：

| 小节 | 主题 | 重要程度 |
|------|------|----------|
| 1.1 | API认证与密钥管理 | ⭐⭐⭐⭐⭐ |
| 1.2 | 发送第一个请求 | ⭐⭐⭐⭐⭐ |
| 1.3 | 理解响应结构 | ⭐⭐⭐⭐⭐ |
| 1.4 | 多轮对话与会话管理 | ⭐⭐⭐⭐⭐ |
| 1.5 | 系统提示词 | ⭐⭐⭐⭐ |
| 1.6 | 结构化输出 | ⭐⭐⭐⭐ |

---

## 1.1 API认证与密钥管理

### 什么是API密钥

API密钥（API Key）是Anthropic分配给你的唯一标识符，用于验证你的请求来源。每个API密钥关联到你的账户，可以追踪使用量并控制访问权限。

**获取API密钥的步骤：**

1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 注册账户（需要信用卡用于计费，但有免费额度）
3. 在「API Keys」页面创建新密钥
4. 复制密钥并妥善保存

### 为什么不能硬编码密钥

很多初学者会这样写：

```python
# ❌ 错误示范 - 密钥暴露在代码中
client = Anthropic(api_key="勿硬编码")
```

这样做有三个严重问题：

| 问题 | 后果 | 案例 |
|------|------|------|
| **代码泄露** | 密钥进入Git仓库，被他人获取 | 某公司员工将密钥提交到GitHub，被恶意利用 |
| **历史记录** | Git历史会永久保存密钥 | 某人3年前的代码仍可被克隆 |
| **生产事故** | 密钥在日志中打印，被监控系统捕获 | 大规模加密货币挖矿攻击 |

### 正确做法：环境变量

```python
# ✅ 正确做法 - 从环境变量读取
import os
from anthropic import Anthropic

api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY环境变量未设置")

client = Anthropic(api_key=api_key)
```

### 多种环境变量设置方法

**方法1：命令行临时设置（仅当前终端）**

```bash
export ANTHROPIC_API_KEY=<your-real-key>
python your_script.py
```

**方法2：.env文件（推荐用于开发）**

```bash
# .env文件（不要提交到Git！）
ANTHROPIC_API_KEY=<your-real-key>
```

```python
# 使用python-dotenv加载
from dotenv import load_dotenv
import os

load_dotenv()  # 加载.env文件
api_key = os.environ.get("ANTHROPIC_API_KEY")

from anthropic import Anthropic
client = Anthropic(api_key=api_key)
```

```bash
# 安装dotenv
pip install python-dotenv
```

**方法3：AWS Secrets Manager / 云密钥服务（生产环境）**

```python
# ✅ 生产环境推荐
import boto3
import json
from anthropic import Anthropic

# 从AWS Secrets Manager获取密钥
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

### 密钥安全检查清单

在使用API密钥之前，做一个安全检查：

```
□ 密钥不在代码中硬编码
□ .env文件在.gitignore中
□ 不用真实密钥测试（用mock）
□ 日志中不打印密钥
□ 生产环境用密钥管理服务
□ 定期轮换密钥
```

### SDK初始化最佳实践

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
                timeout=30,  # 请求超时30秒
                max_retries=3,  # 最多重试3次
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

### 安装SDK

```bash
pip install anthropic
```

### 同步请求完整示例

```python
from anthropic import Anthropic
import os

# 初始化客户端
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# 发送请求
message = client.messages.create(
    model="claude-sonnet-4-20250514",  # 使用的模型
    max_tokens=1024,  # 最大生成的token数
    messages=[
        {
            "role": "user",
            "content": "用一句话解释什么是量子计算"
        }
    ]
)

# 打印响应
print(message.content[0].text)
```

### 参数详解

#### `model` 参数

| 模型 | 特点 | 适用场景 |
|------|------|----------|
| `claude-opus-4-20250514` | 最强能力，适合复杂任务 | 复杂分析、代码生成 |
| `claude-sonnet-4-20250514` | 平衡之选，性价比高 | 日常对话、写作、分析 |
| `claude-haiku-3-20250514` | 快速响应，适合简单任务 | 实时聊天、简单问答 |

#### `max_tokens` 参数

`max_tokens` 控制单次请求最多生成的token数。

**重要概念**：
- Token是文本处理的最小单位（1个token约等于0.75个英文单词或1-2个中文字符）
- 如果`max_tokens`太小，响应会被截断
- 如果`max_tokens`太大，会浪费token（因为按使用量收费）

```python
# 设置足够的max_tokens以获得完整响应
message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,  # 适合生成长文章
    messages=[{"role": "user", "content": "写一篇2000字的文章..."}]
)
```

**如何估算需要的token**：

| 预期输出长度 | 建议max_tokens |
|-------------|---------------|
| 短回答（几个字） | 100-200 |
| 中等回答（几段话） | 500-1000 |
| 长回答（文章） | 2000-4096 |
| 超长回答（长文） | 4096以上 |

#### `messages` 参数

`messages` 是一个消息列表，每条消息包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| `role` | string | `user`（用户）或 `assistant`（助手） |
| `content` | string | 消息内容 |

```python
messages=[
    {"role": "user", "content": "什么是Python？"},
    {"role": "assistant", "content": "Python是一种高级编程语言..."},
    {"role": "user", "content": "它适合做什么？"}
]
```

### 流式响应

对于需要实时显示打字效果的场景，使用流式响应：

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
        print(text, end="", flush=True)  # 实时打印
    print()  # 最后换行
```

**流式响应的优势**：

| 场景 | 非流式 | 流式 |
|------|--------|------|
| 用户体验 | 等待完整响应 | 实时看到输出 |
| 长文本 | 长时间无反馈 | 逐步显示 |
| 交互性 | 一次性 | 可中断 |

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

**响应结构**：

```python
# message 是 Message 对象，完整属性：
print(message.id)          # msg_xxxxx - 消息唯一ID
print(message.type)        # "message" - 消息类型
print(message.role)        # "assistant" - 角色
print(message.content)      # [ContentBlock(text='...')] - 内容块列表
print(message.model)       # "claude-sonnet-4-20250514" - 使用的模型
print(message.stop_reason) # "end_turn" - 停止原因
print(message.stop_sequence) # None - 停止序列
print(message.usage)        # Usage(input_tokens=xx, output_tokens=xx) - token使用量
```

### 解析响应内容

```python
# ✅ 正确获取文本内容
if message.content and len(message.content) > 0:
    text = message.content[0].text
    print(text)

# ✅ 安全的方式
for block in message.content:
    if block.type == "text":
        print(block.text)
```

### 停止原因详解

```python
print(message.stop_reason)  # 可能的值：

# "end_turn" - 正常完成，Claude认为应该停止
# "max_tokens" - 达到max_tokens限制，可能被截断
# "stop_sequence" - 遇到指定的停止序列
# "only_stop_reason" - 仅当stop_reason是唯一有效停止信号时
```

**如何判断响应是否完整**：

```python
if message.stop_reason == "max_tokens":
    print("⚠️ 警告：响应被截断，可能不完整")
    print("建议：增加max_tokens值或优化提示词")
elif message.stop_reason == "end_turn":
    print("✅ 响应正常完成")
```

### Token使用量

```python
print(f"输入token: {message.usage.input_tokens}")
print(f"输出token: {message.usage.output_tokens}")
print(f"总token: {message.usage.input_tokens + message.usage.output_tokens}")

# 计算成本（以 Sonnet 模型为例）
input_cost_per_1k = 0.003  # $0.003/1K输入tokens
output_cost_per_1k = 0.015  # $0.015/1K输出tokens

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

### 什么是多轮对话

多轮对话是指多次请求之间保持上下文，让Claude能够理解对话历史。

**单轮对话（无记忆）**：

```python
# 每次请求都是独立的，没有上下文
response1 = client.messages.create(
    messages=[{"role": "user", "content": "我的狗叫豆豆"}]
)
print(response1.content[0].text)  # "真可爱的名字！"

response2 = client.messages.create(
    messages=[{"role": "user", "content": "它喜欢吃什么？"}]
)
print(response2.content[0].text)  # "对不起，我不知道你的狗是谁..."
# ❌ Claude不记得"豆豆"
```

**多轮对话（有记忆）**：

```python
# 维护消息历史
conversation_history = []

while True:
    user_input = input("你: ")
    
    # 添加用户消息
    conversation_history.append({
        "role": "user",
        "content": user_input
    })
    
    # 发送请求
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=conversation_history
    )
    
    # 获取助手回复
    assistant_message = response.content[0].text
    
    # 添加助手回复到历史
    conversation_history.append({
        "role": "assistant",
        "content": assistant_message
    })
    
    print(f"Claude: {assistant_message}")
```

### 会话管理的进阶技巧

#### 技巧1：限制历史消息长度

对话太长会消耗更多token，需要限制历史长度：

```python
def trim_conversation(messages, max_turns=10):
    """只保留最近N轮对话"""
    # 保留系统消息（如果有）
    system_messages = [m for m in messages if m.get("role") == "system"]
    conversation = [m for m in messages if m.get("role") != "system"]
    
    # 只保留最近max_turns * 2条（每轮有user和assistant）
    trimmed = conversation[-(max_turns * 2):]
    
    return system_messages + trimmed

# 使用
messages = trim_conversation(conversation_history, max_turns=5)
```

#### 技巧2：摘要旧消息

对于超长对话，可以将旧消息摘要：

```python
def summarize_old_messages(messages, summary_turns=5):
    """将早期对话摘要，保留最近的消息"""
    if len(messages) <= summary_turns * 2 + 2:  # 留点余量
        return messages
    
    # 分离早期消息和最近消息
    early = messages[:-summary_turns * 2]
    recent = messages[-summary_turns * 2:]
    
    # 摘要早期对话
    early_text = "\n".join([f"{m['role']}: {m['content']}" for m in early])
    
    summary_prompt = f"""将以下对话摘要成一段话，保留关键信息：

{early_text}

摘要："""

    summary_response = client.messages.create(
        model="claude-haiku-3-20250514",  # 用便宜的模型做摘要
        max_tokens=500,
        messages=[{"role": "user", "content": summary_prompt}]
    )
    
    summary = summary_response.content[0].text
    
    # 返回摘要 + 最近对话
    return [
        {"role": "system", "content": f"对话摘要：{summary}"}
    ] + recent
```

#### 技巧3：分离不同话题

```python
class ConversationManager:
    """会话管理器：支持多话题"""
    
    def __init__(self):
        self.conversations = {}  # {conversation_id: [messages]}
        self.current_id = None
    
    def start_new(self, conversation_id):
        """开始新对话"""
        self.current_id = conversation_id
        self.conversations[conversation_id] = []
    
    def add_message(self, role, content):
        """添加消息"""
        if self.current_id is None:
            self.start_new("default")
        self.conversations[self.current_id].append({
            "role": role,
            "content": content
        })
    
    def get_messages(self, conversation_id=None):
        """获取对话历史"""
        cid = conversation_id or self.current_id
        return self.conversations.get(cid, [])
    
    def switch_conversation(self, conversation_id):
        """切换对话"""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        self.current_id = conversation_id

# 使用示例
manager = ConversationManager()
manager.start_new("技术支持")
manager.add_message("user", "我的代码报错了")
manager.add_message("assistant", "请告诉我错误信息")
manager.add_message("user", "NameError: name 'x' is not defined")

# 切换到另一个话题
manager.start_new("产品咨询")
manager.add_message("user", "你们的产品有什么特点")

# 回到技术支持
manager.switch_conversation("技术支持")
messages = manager.get_messages()
```

---

## 1.5 系统提示词

### 什么是系统提示词

系统提示词（System Prompt）是设置AI行为和角色的方式。它告诉Claude应该如何表现。

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    system="你是一位专业的产品经理，用词简洁专业。",
    messages=[{"role": "user", "content": "我应该做什么产品？"}]
)
```

### 系统提示词 vs 用户消息

| 特性 | 系统提示词 | 用户消息 |
|------|-----------|----------|
| 优先级 | 最高 | 相对较低 |
| 持久性 | 影响整个对话 | 只影响当前轮 |
| 可见性 | 对用户不可见 | 用户能看到 |
| 用途 | 设置角色/行为 | 具体请求 |

### 有效的系统提示词模式

#### 模式1：角色设定

```python
# 设定角色
system = """你是一位拥有20年经验的高级Python工程师。
你的特点：
- 代码风格遵循PEP 8
- 喜欢用类型提示
- 注重性能优化
- 说话直接，有话直说
"""
```

#### 模式2：输出格式指定

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

#### 模式3：约束条件

```python
system = """你是一位财经记者。

约束条件：
- 不预测具体股价
- 引用数据时注明来源
- 风险提示必须清晰
- 不使用"一定"、"保证"等绝对词汇
"""
```

#### 模式4：示例注入（Few-shot in System）

```python
system = """你是一个翻译助手。

翻译示例：
- "Hello, how are you?" → "你好，你怎么样？"
- "The weather is nice today." → "今天天气很好。"
- "I can't understand." → "我无法理解。"

注意：
- 中文翻译用"你"而不是"您"
- 保持原文的语气和情感
"""
```

### 系统提示词最佳实践

#### ✅ 应该做的

```python
# 清晰具体
system = """你是一位医疗助手。

职责：
1. 回答常见健康问题
2. 提供健康生活方式建议
3. 解释医学术语

限制：
- 不做具体诊断
- 不开处方
- 遇到严重症状建议就医
"""

# 给出具体例子
system = """你是一个代码审查助手。

审查要点：
1. 安全性（SQL注入、XSS等）
2. 性能问题
3. 代码可读性

反馈格式：
[安全问题]: 描述 + 建议修复
[性能问题]: 描述 + 优化建议
"""
```

#### ❌ 不应该做的

```python
# 太模糊
system = "你是AI助手，回答用户问题"  # 太泛了

# 太长太复杂
system = """你要扮演一个在某个领域有很多年经验的人，
从很早以前就开始学习和工作...
[1000字介绍]...
现在请回答用户的问题"""  # 太长了，效果反而差

# 指令冲突
system = """你是一个诚实的AI助手。
但有时候为了用户体验可以说善意的谎言。"""  # 指令冲突
```

### 调试系统提示词

当系统提示词效果不好时，调试方法：

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

### 什么是结构化输出

有时候你需要AI返回特定格式的数据（如JSON），而不是自由文本。

### 方法1：在提示词中要求JSON

最简单但不太可靠的方法：

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

# 解析响应
import json
text = response.content[0].text
# 尝试提取JSON（可能有markdown格式）
if "```json" in text:
    text = text.split("```json")[1].split("```")[0]
elif "```" in text:
    text = text.split("```")[1].split("```")[0]

data = json.loads(text.strip())
print(data)
```

### 方法2：使用response_format参数

```python
# Anthropic API支持直接指定JSON Schema
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

### 方法3：使用工具调用（最可靠）

```python
# 定义工具，让Claude调用
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

# 处理工具调用
for content in response.content:
    if content.type == "tool_use":
        result = content.input
        print(f"Status: {result['status']}")
        print(f"Result: {result['result']}")
```

### 结构化输出应用场景

| 场景 | 输出格式 | 示例 |
|------|----------|------|
| 数据提取 | JSON | 从文本提取人名、日期 |
| 分类任务 | 带标签的JSON | {"category": "positive", "confidence": 0.95} |
| 表格数据 | JSON数组 | [{"name": "...", "age": 25}, ...] |
| API响应 | 标准化JSON | 统一的错误码和消息格式 |
| 代码生成 | 结构化 | {"function": "...", "tests": "..."} |

### 处理边界情况

```python
def safe_json_parse(text):
    """安全解析JSON，处理各种格式"""
    import json
    import re
    
    # 清理markdown代码块
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()
    
    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # 尝试提取JSON对象
    try:
        # 找第一个{和最后一个}
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
    except:
        pass
    
    return None
```

---

## 本章总结

### 核心知识点

| 知识点 | 掌握程度 | 关键点 |
|--------|----------|--------|
| API认证 | ⭐⭐⭐⭐⭐ | 环境变量、永不硬编码 |
| 基本请求 | ⭐⭐⭐⭐⭐ | model、max_tokens、messages |
| 响应结构 | ⭐⭐⭐⭐⭐ | content、stop_reason、usage |
| 多轮对话 | ⭐⭐⭐⭐⭐ | 维护历史、trim、摘要 |
| 系统提示词 | ⭐⭐⭐⭐ | 角色设定、格式指定 |
| 结构化输出 | ⭐⭐⭐⭐ | 工具调用最可靠 |

### 常见错误排查

| 错误 | 原因 | 解决 |
|------|------|------|
| `AuthenticationError` | API密钥无效或未设置 | 检查环境变量 |
| `RateLimitError` | 请求太频繁 | 等待+重试 |
| `InvalidRequestError` | 参数错误 | 检查文档 |
| 响应被截断 | max_tokens太小 | 增加max_tokens |
| 回答不相关 | 提示词不清晰 | 优化系统提示词 |

### 下一步

- 继续阅读：提示词工程专题（二） - 学习高级提示词技巧（待发布）
- 实践项目：用Claude API构建一个命令行聊天机器人
- 参考资料：[Anthropic API官方文档](https://docs.anthropic.com/)

---

**文档元信息**
难度：⭐⭐⭐⭐ | 类型：专家设计 | 更新日期：2026-03-25 | 预计阅读时间：45分钟 | 字数：约6000字
