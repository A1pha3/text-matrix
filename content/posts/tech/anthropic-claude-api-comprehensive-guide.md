---
title: "Claude API全解析：从入门到生产级AI应用开发"
date: 2026-03-25
draft: false
categories:
  - 技术笔记
tags:
  - Claude
  - API
  - Anthropic
  - RAG
  - MCP
  - Agent
  - 函数调用
  - 工具调用
hiddenFromHomePage: true
author: 钳岳星君
---

# Claude API全解析：从入门到生产级AI应用开发 ⭐⭐⭐⭐

> **目标读者**：软件工程师，希望将Claude集成到生产应用的开发者
> **核心问题**：如何系统性地掌握Claude API开发能力？
> **前置知识**：Python编程基础、JSON数据处理经验、Anthropic API密钥

---

## 学习目标

完成本课后，你将能够：
- 向Claude模型发送API请求并处理响应
- 实现多轮对话、流式响应和结构化输出生成
- 使用自动化测试流水线系统化构建和评估Prompt
- 创建自定义工具并集成Claude与外部服务
- 设计和实现RAG系统（混合搜索+重排序）
- 使用MCP（Model Context Protocol）连接Claude到各种数据源
- 理解常见的工作流和Agent架构模式

---

## 一句话定义

**Claude API** 是Anthropic提供的编程接口，允许开发者将Claude模型集成到应用程序中，实现聊天机器人、自动化工具、AI功能等各种应用场景。

---

## 课程结构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                   Claude API 全解析（84节课，8.1小时）            │
├─────────────────────────────────────────────────────────────────┤
│  第1章：API基础 ──────── 认证、请求、会话管理、结构化输出          │
│  第2章：提示词工程 ───── 策略、评估框架、系统化测试               │
│  第3章：工具调用 ─────── 函数调用、多轮交互、批处理                │
│  第4章：RAG系统 ──────── 分块、嵌入、混合搜索、重排序              │
│  第5章：MCP协议 ──────── 模块化AI应用、自定义工具                  │
│  第6章：Claude Code ──── 开发自动化、Computer Use                 │
│  第7章：Agent架构 ────── 并行执行、条件路由、调试策略              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 第1章：API基础

### 1.1 认证与API密钥

Claude API使用API密钥进行认证。你可以在Anthropic Console获取密钥。

**安全最佳实践：**
- 永远不要将API密钥直接硬编码在代码中
- 使用环境变量或密钥管理服务
- 定期轮换密钥
- 设置使用限额防止意外超支

```python
import os
from anthropic import Anthropic

# 从环境变量获取API密钥
api_key = os.environ.get("ANTHROPIC_API_KEY")

client = Anthropic(api_key=api_key)
```

### 1.2 基本请求与响应

**同步请求示例：**

```python
message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": "解释什么是量子纠缠，用简单的语言"
        }
    ]
)

print(message.content)
```

**响应结构：**
```python
# message 对象包含：
# - content: AI生成的文本内容
# - id: 消息唯一标识
# - model: 使用的模型
# - role: 角色（assistant）
# - stop_reason: 停止原因（end_turn, max_tokens, stop_sequence）
# - stop_sequence: 停止序列（如果指定了）
# - type: 消息类型（message）
# - usage: token使用量
```

### 1.3 多轮对话管理

多轮对话通过维护消息历史实现：

```python
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
    
    # 添加助手回复
    assistant_message = {
        "role": "assistant",
        "content": response.content[0].text
    }
    conversation_history.append(assistant_message)
    
    print(f"Claude: {assistant_message['content']}")
```

### 1.4 系统提示词

系统提示词用于设定AI的行为和角色：

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    system="你是一位专业的产品经理，负责为用户提供清晰、实用的产品建议。",
    messages=[
        {"role": "user", "content": "我应该选择哪个项目管理工具？"}
    ]
)
```

### 1.5 结构化输出

使用特定格式约束AI输出，或使用JSON模式：

**方法1：直接要求JSON**

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": """返回一个JSON对象，包含用户信息：
            {"name": "姓名", "age": 年龄, "city": "城市"}"""
        }
    ]
)
```

**方法2：使用response_format参数（如果可用）**

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "返回一个水果列表"}],
    response_format={"type": "json_object"}
)
```

---

## 第2章：提示词工程

### 2.1 提示词策略

**核心原则：**

| 原则 | 说明 | 示例 |
|------|------|------|
| **清晰** | 明确说明你想要什么 | ❌ "帮我写代码" → ✅ "用Python写一个函数，接受列表返回最大值" |
| **具体** | 提供足够的上下文 | 说明背景、约束、格式要求 |
| **分步** | 复杂任务拆分成步骤 | "首先...然后...最后..." |
| **验证** | 要求AI解释推理过程 | "一步步解释你的推理" |

### 2.2 Few-shot提示词

通过示例让AI理解期望的输出格式：

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=500,
    messages=[
        {
            "role": "user",
            "content": """将以下句子改写成正式商务邮件风格：

示例1：
输入："嘿，明天下午能见吗？"
输出："尊敬的先生/女士：请问明日下午方便安排一次会议吗？此致敬礼"

示例2：
输入："这个价格太高了"
输出："尊敬的负责人：关于您提供的报价，我们认为有一定的商议空间。不知是否方便进一步沟通？此致敬礼"

现在请将以下句子改写：
输入："嗨，能把文档发我吗？"
输出："""
        }
    ]
)
```

### 2.3 提示词评估框架

系统化测试和优化提示词：

```python
def evaluate_prompt(prompt_template, test_cases):
    """评估提示词在不同测试用例上的表现"""
    results = []
    
    for test_case in test_cases:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt_template.format(**test_case)}]
        )
        
        results.append({
            "input": test_case,
            "output": response.content[0].text,
            "expected": test_case.get("expected"),
            "evaluation": evaluate_response(response.content[0].text, test_case.get("expected"))
        })
    
    return results

def evaluate_response(actual, expected):
    """简单的响应评估函数"""
    # 根据具体需求实现评估逻辑
    return {
        "correct": expected in actual if expected else None,
        "length": len(actual),
        "format_check": check_format(actual)
    }
```

### 2.4 系统化测试方法

**A/B测试提示词：**

```python
def ab_test_prompts(prompt_a, prompt_b, test_inputs, n=10):
    """对比两个提示词的表现"""
    results = {"prompt_a": [], "prompt_b": []}
    
    for _ in range(n):
        for test_input in test_inputs:
            # 测试prompt_a
            response_a = client.messages.create(
                model="claude-sonnet-4-20250514",
                messages=[{"role": "user", "content": prompt_a.format(**test_input)}]
            )
            results["prompt_a"].append(response_a.content[0].text)
            
            # 测试prompt_b
            response_b = client.messages.create(
                model="claude-sonnet-4-20250514",
                messages=[{"role": "user", "content": prompt_b.format(**test_input)}]
            )
            results["prompt_b"].append(response_b.content[0].text)
    
    return aggregate_results(results)
```

---

## 第3章：工具调用

### 3.1 函数调用基础

工具调用允许Claude调用外部函数：

**定义工具：**

```python
tools = [
    {
        "name": "get_weather",
        "description": "获取指定城市的天气信息",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称，如北京、上海"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "温度单位"
                }
            },
            "required": ["city"]
        }
    }
]
```

**调用示例：**

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=tools,
    messages=[
        {"role": "user", "content": "北京今天多少度？"}
    ]
)

# 处理工具调用
for content_block in response.content:
    if content_block.type == "tool_use":
        tool_name = content_block.name
        tool_input = content_block.input
        
        if tool_name == "get_weather":
            # 执行实际的天气查询
            weather_result = get_weather_api(tool_input["city"], tool_input.get("unit", "celsius"))
            
            # 将结果返回给Claude
            follow_up = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                tools=tools,
                messages=[
                    {"role": "user", "content": "北京今天多少度？"},
                    response,
                    {
                        "role": "user",
                        "content": f"weather result: {weather_result}"
                    }
                ]
            )
```

### 3.2 多轮工具交互

```python
def chat_with_tools(user_message):
    """支持工具调用的多轮对话"""
    messages = [{"role": "user", "content": user_message}]
    
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            tools=tools,
            messages=messages
        )
        
        # 检查是否有工具调用
        tool_uses = [block for block in response.content if block.type == "tool_use"]
        
        if not tool_uses:
            # 没有工具调用，返回最终回复
            return response.content[0].text
        
        # 处理工具调用
        for tool_use in tool_uses:
            result = execute_tool(tool_use.name, tool_use.input)
            messages.append({
                "role": "user",
                "content": f"<result>{json.dumps(result)}</result>"
            })

def execute_tool(name, input_args):
    """执行工具并返回结果"""
    # 根据工具名称执行对应函数
    pass
```

### 3.3 批处理工具调用

```python
def batch_tool_calls(requests):
    """处理多个工具调用请求"""
    results = []
    
    for request in requests:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            tools=tools,
            messages=[{"role": "user", "content": request}]
        )
        
        # 收集工具调用结果
        for content_block in response.content:
            if content_block.type == "tool_use":
                result = execute_tool(content_block.name, content_block.input)
                results.append(result)
    
    return results
```

### 3.4 内置工具与MCP工具

```python
# Anthropic提供的一些内置工具
builtin_tools = [
    {
        "name": "web_search",
        "description": "搜索网络获取实时信息",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索查询"}
            }
        }
    }
]

# MCP工具（通过Model Context Protocol连接）
# 见第5章MCP专题
```

---

## 第4章：RAG系统

### 4.1 RAG核心概念

**检索增强生成（Retrieval-Augmented Generation）** 是一种结合检索和生成的AI架构：

```
┌─────────────────────────────────────────────────────────────┐
│                      RAG 系统架构                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│   │ 文档库   │───▶│ 检索器   │───▶│ 生成器   │              │
│   └──────────┘    └──────────┘    └──────────┘              │
│        │               │               │                    │
│        ▼               ▼               ▼                    │
│   分块/向量化      相似度匹配      结合上下文生成            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 文本分块策略

| 策略 | 描述 | 适用场景 |
|------|------|----------|
| **固定大小分块** | 按字符或token数切分 | 简单场景，快速实现 |
| **语义分块** | 按段落或句子切分 | 保留语义完整性 |
| **层次分块** | 多级粒度（文档→段落→句子） | 复杂文档结构 |
| **递归分块** | 按层级递归切分 | 通用场景 |

```python
def chunk_text(text, chunk_size=500, overlap=50):
    """固定大小分块，带重叠"""
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    
    return chunks

def semantic_chunking(text):
    """语义分块 - 按段落切分"""
    # 分割段落
    paragraphs = text.split("\n\n")
    
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) < 500:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks
```

### 4.3 向量化与嵌入

```python
from anthropic import Anthropic
import numpy as np

client = Anthropic()

def embed_text(text):
    """使用Anthropic嵌入API获取文本向量"""
    response = client.embeddings.create(
        model="claude-embedding-3-haiku",
        input=text
    )
    return response.embedding

def create_vector_store(documents):
    """创建向量存储"""
    vectors = []
    for doc in documents:
        embedding = embed_text(doc)
        vectors.append(embedding)
    return np.array(vectors)
```

### 4.4 混合搜索

结合稠密检索和稀疏检索（BM25）：

```python
def hybrid_search(query, documents, alpha=0.5):
    """
    混合搜索：结合向量相似度和BM25
    alpha: 0=纯BM25, 0.5=混合, 1=纯向量
    """
    # 1. 向量检索
    query_vector = embed_text(query)
    vector_scores = cosine_similarity(query_vector, document_vectors)
    
    # 2. BM25检索
    bm25_scores = calculate_bm25(query, documents)
    
    # 3. 加权混合
    final_scores = alpha * vector_scores + (1 - alpha) * bm25_scores
    
    # 4. 返回排序结果
    ranked_indices = np.argsort(final_scores)[::-1]
    
    return [(documents[i], final_scores[i]) for i in ranked_indices]
```

### 4.5 重排序

```python
def rerank_results(query, documents, top_k=10):
    """使用Claude对检索结果进行重排序"""
    # 获取初始检索结果（top_k * 2，保留更多候选）
    initial_results = hybrid_search(query, documents, top_k * 2)
    
    # 使用Claude进行相关性评估
    reranked = []
    
    for doc, score in initial_results[:top_k * 2]:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": f"""评估以下文档与查询的相关性：

查询：{query}

文档：{doc[:500]}

请只返回一个0-10的相关性分数，10表示高度相关。
只返回数字。"""
            }]
        )
        
        try:
            relevance_score = float(response.content[0].text.strip())
        except:
            relevance_score = 0
        
        reranked.append((doc, relevance_score * score))
    
    # 按最终分数排序
    reranked.sort(key=lambda x: x[1], reverse=True)
    
    return reranked[:top_k]
```

### 4.6 上下文检索增强

```python
def contextual_retrieval(query, document, window_size=3):
    """为每个chunk生成上下文描述，增强检索准确性"""
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": f"""为以下文档片段生成一个简短的上下文描述：

原始文档：{document}

请用一句话说明这段文字的主题和作用，10-20字左右。
只返回描述，不要其他内容。"""
        }]
    )
    
    context = response.content[0].text.strip()
    
    # 将上下文与文档结合
    enhanced_document = f"{context}\n\n{document}"
    
    return enhanced_document
```

---

## 第5章：MCP协议

### 5.1 MCP概述

**Model Context Protocol (MCP)** 是一种开放协议，用于构建模块化AI应用程序：

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP 架构                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌──────────┐         ┌──────────┐         ┌──────────┐   │
│   │ Claude   │◀───────▶│  MCP     │◀───────▶│  本地/    │   │
│   │ Client   │         │  Server  │         │  远程工具  │   │
│   └──────────┘         └──────────┘         └──────────┘   │
│                                                             │
│   MCP Server 可以连接：文件系统、数据库、API等各种资源        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 MCP核心概念

| 概念 | 说明 |
|------|------|
| **MCP Host** | 启动连接的应用程序（如Claude Code） |
| **MCP Client** | 与MCP Server保持1:1连接的客户端 |
| **MCP Server** | 提供工具和资源的服务器 |
| **Resources** | 可读取的数据（如文件、数据库记录） |
| **Tools** | 可调用的函数 |
| **Prompts** | 预定义的提示词模板 |

### 5.3 MCP服务器开发

```python
# mcp_server.py - 使用Python构建MCP服务器
from mcp.server import MCPServer
from mcp.types import Tool, Resource

server = MCPServer("my-server")

@server.tool()
def get_weather(city: str) -> str:
    """获取城市天气"""
    return f"{city}今天晴天，25度"

@server.resource("docs://readme")
def get_readme() -> str:
    """返回README内容"""
    with open("README.md", "r") as f:
        return f.read()

server.run()
```

### 5.4 MCP客户端连接

```python
from anthropic import Anthropic

client = Anthropic()

# 连接MCP服务器
# 注意：具体API取决于使用的MCP客户端库
mcp_tools = client.mcp.connect(
    servers=["my-weather-server", "my-filesystem-server"]
)

# 使用MCP工具就像使用普通工具一样
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=mcp_tools,
    messages=[{"role": "user", "content": "帮我查一下上海的天气"}]
)
```

---

## 第6章：Claude Code与Computer Use

### 6.1 Claude Code概述

Claude Code是Anthropic推出的命令行AI助手，深度集成到开发工作流中。

**核心功能：**
- 文件读取、编辑、命令执行
- Git操作
- 代码搜索和修改
- MCP服务器集成
- GitHub PR和Issue处理

### 6.2 Claude Code工作流集成

```python
# Claude Code可以在以下场景辅助开发：
# 1. 代码审查
# 2. Bug修复
# 3. 功能开发
# 4. 测试生成
# 5. 文档编写
# 6. 代码重构
```

### 6.3 Computer Use

Computer Use是Claude的UI自动化能力，可以控制鼠标和键盘：

```python
# Computer Use允许Claude：
# - 点击按钮
# - 填写表单
# - 截取屏幕截图
# - 执行复杂的多步骤UI操作

# 示例工作流：
# 1. 打开浏览器
# 2. 导航到网站
# 3. 填写搜索框
# 4. 点击搜索按钮
# 5. 分析结果
```

---

## 第7章：Agent架构

### 7.1 Agent基础概念

**Agent** 是能够自主决策和执行动作的AI系统：

```
┌─────────────────────────────────────────────────────────────┐
│                     Agent 架构                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌──────────┐                                             │
│   │   LLM    │◀─── 指令/工具/上下文                         │
│   └────┬─────┘                                             │
│        │                                                    │
│        ▼                                                    │
│   ┌──────────┐    ┌──────────┐                             │
│   │  Planner │───▶│ Executor │                             │
│   └──────────┘    └──────────┘                             │
│        │               │                                   │
│        │               ▼                                   │
│        │         ┌──────────┐                             │
│        └────────▶│  Memory   │                             │
│                  └──────────┘                             │
│                                                             │
│   Planner: 分解任务，规划执行步骤                            │
│   Executor: 执行具体动作                                     │
│   Memory: 存储中间状态和历史                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 并行执行

```python
import asyncio
from anthropic import Anthropic

client = Anthropic()

async def parallel_agent(tasks):
    """并行执行多个任务"""
    async def execute_task(task):
        response = await client.messages.create_async(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": task}]
        )
        return response.content[0].text
    
    # 使用asyncio并发执行
    results = await asyncio.gather(
        *[execute_task(task) for task in tasks]
    )
    
    return results

# 使用示例
tasks = [
    "解释什么是Python的装饰器",
    "解释什么是Python的生成器",
    "解释什么是Python的上下文管理器"
]

results = asyncio.run(parallel_agent(tasks))
```

### 7.3 操作链

```python
def chain_operations(initial_input, operations):
    """顺序执行一系列操作"""
    current_result = initial_input
    
    for i, operation in enumerate(operations):
        print(f"步骤 {i+1}: 执行 {operation['name']}")
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": f"""任务：{operation['description']}
输入：{current_result}

请执行任务并返回结果。"""
            }]
        )
        
        current_result = response.content[0].text
    
    return current_result

# 使用示例
workflow = [
    {"name": "分析", "description": "分析用户提供的产品反馈，识别主要问题"},
    {"name": "分类", "description": "将问题分类为：功能Bug体验优化"},
    {"name": "优先级", "description": "根据影响范围建议处理优先级"},
    {"name": "总结", "description": "生成简短的执行建议"}
]

result = chain_operations(user_feedback, workflow)
```

### 7.4 条件路由

```python
def route_based_on_intent(user_message):
    """根据用户意图路由到不同的处理流程"""
    
    # 1. 分析用户意图
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        messages=[{
            "role": "user",
            "content": f"""分析以下用户消息的意图：

"{user_message}"

请选择一个最匹配的类别：
- technical_support: 技术支持/故障排除
- sales_inquiry: 销售咨询
- account_help: 账户帮助
- feedback: 反馈建议
- other: 其他

只返回类别名称。"""
        }]
    )
    
    intent = response.content[0].text.strip().lower()
    
    # 2. 根据意图路由
    if "technical_support" in intent:
        return handle_technical_support(user_message)
    elif "sales" in intent:
        return handle_sales(user_message)
    elif "account" in intent:
        return handle_account(user_message)
    else:
        return handle_general(user_message)
```

### 7.5 调试策略

**Agent系统调试最佳实践：**

| 问题 | 调试方法 |
|------|----------|
| Agent陷入循环 | 添加最大迭代次数限制 |
| 工具调用失败 | 详细的错误处理和重试机制 |
| 上下文丢失 | 显式传递关键状态 |
| 输出质量差 | 逐步验证每个步骤的输出 |
| 工具选择错误 | 添加工具选择理由的解释 |

```python
def debug_agent(agent, max_iterations=10):
    """带调试功能的Agent执行"""
    iteration = 0
    history = []
    
    while iteration < max_iterations:
        print(f"\n=== 迭代 {iteration + 1} ===")
        
        # 执行一步
        result = agent.step()
        history.append(result)
        
        # 检查是否完成
        if result.is_final:
            print("Agent任务完成")
            return result.output
        
        # 打印中间状态
        print(f"当前状态: {result.state}")
        print(f"下一步计划: {result.next_action}")
        
        iteration += 1
    
    print("达到最大迭代次数限制")
    return {"error": "max_iterations_reached", "history": history}
```

---

## 课程总结

### 技能图谱

```
┌─────────────────────────────────────────────────────────────────┐
│                      Claude API 开发者技能图谱                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   基础技能                    进阶技能                    专家技能   │
│   ─────────                  ─────────                  ─────────   │
│   • API认证                   • Few-shot提示词           • Agent架构 │
│   • 基本请求                   • 结构化输出               • RAG系统  │
│   • 多轮对话                   • 提示词评估               • MCP开发  │
│   • 系统提示词                 • A/B测试                  • 混合部署  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 关键知识点

| 领域 | 核心内容 | 应用场景 |
|------|----------|----------|
| **API基础** | 认证、请求、响应结构 | 所有Claude应用 |
| **提示词工程** | 清晰表达、Few-shot、测试 | 提升输出质量 |
| **工具调用** | 函数定义、工具执行 | 扩展AI能力 |
| **RAG** | 分块、嵌入、搜索、重排序 | 知识库问答 |
| **MCP** | 协议、服务器、客户端 | 系统集成 |
| **Agent** | 规划、执行、记忆 | 复杂任务自动化 |

---

## 下一步

恭喜你完成了Claude API全解析！

**推荐学习路径：**

| 方向 | 课程 | 说明 |
|------|------|------|
| **实战** | Claude Code实战 | 在真实项目中应用所学 |
| **进阶** | MCP专题（入门+进阶） | 深入系统集成 |
| **垂直** | Agent Skills开发 | 创建可复用指令集 |

---

## 参考来源

- [Building with the Claude API](https://anthropic.skilljar.com/claude-with-the-anthropic-api)（Anthropic官方课程，84节，8.1小时）
- [Model Context Protocol](https://modelcontextprotocol.io/)（MCP官方文档）
- [Anthropic API Reference](https://docs.anthropic.com/)

---

**文档元信息**
难度：⭐⭐⭐⭐ | 类型：专家设计 | 更新日期：2026-03-25 | 预计阅读时间：60 分钟
