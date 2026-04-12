---
title: "Claude API基础专题（三）：工具调用"
date: 2026-03-25T11:30:00+08:00
slug: "claude-api-tools-function-calling"
aliases:
  - /posts/tech/claude-api-tools-function-calling/
description: "本文深入探讨了Claude API的工具调用机制，包括Function Calling的原理、工具定义与注册、多工具协同、批处理模式，以及MCP（Model Context Protocol）协议的使用方法。"
draft: false
categories: ["技术笔记"]
tags: ["Claude", "工具调用", "MCP", "Python"]
---

# Claude API基础专题（三）：工具调用

> 预计阅读时间：35分钟 | 难度：⭐⭐⭐

---

> **目标读者**：希望让Claude调用外部工具、执行代码的开发者
> **前置知识**：已完成第一篇《API基础》和第二篇《提示词工程》
> **学习提醒**：工具调用是Claude能力扩展的核心方式，建议动手实践

---

## 章节导航

| 小节 | 主题 | 重要程度 |
|------|------|----------|
| 3.1 | 工具调用概述 | ⭐⭐⭐⭐⭐ |
| 3.2 | 定义工具 | ⭐⭐⭐⭐⭐ |
| 3.3 | 处理工具调用 | ⭐⭐⭐⭐⭐ |
| 3.4 | 多轮工具调用 | ⭐⭐⭐⭐⭐ |
| 3.5 | 代码执行工具 | ⭐⭐⭐⭐ |
| 3.6 | 工具调用的最佳实践 | ⭐⭐⭐⭐ |

---

## 3.1 工具调用概述

### 什么是工具调用

工具调用（Tool Use / Function Calling）允许Claude在响应中请求调用你定义的外部工具。这是Claude与外部世界交互的核心方式。

```python
from anthropic import Anthropic
import os

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# 定义一个计算器工具
tools = [{
    "name": "calculator",
    "description": "执行数学计算",
    "input_schema": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "数学表达式，如 '2 + 2' 或 'sqrt(16)'"
            }
        },
        "required": ["expression"]
    }
}]

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=tools,
    messages=[{
        "role": "user",
        "content": "计算 15 * 23 + 45 的值"
    }]
)

print(response.content)
```

### 工具调用 vs 普通API调用

| 特性 | 普通API调用 | 工具调用 |
|------|------------|----------|
| 交互方式 | 单次请求-响应 | 多轮对话 |
| 外部操作 | 不可 | Claude决定何时调用 |
| 灵活性 | 固定逻辑 | 动态决策 |
| 适用场景 | 简单任务 | 复杂任务 |

### 工具调用的工作流程

```
用户提问
    ↓
Claude判断需要调用工具
    ↓
返回 tool_use 请求（stop_reason: "tool_use"）
    ↓
执行工具，返回结果
    ↓
Claude整合结果，生成最终回答
    ↓
返回最终响应（stop_reason: "end_turn"）
```

---

## 3.2 定义工具

### 工具的基本结构

```python
tool = {
    "name": "工具名称",           # 唯一标识符，字母数字下划线
    "description": "工具描述",      # 描述工具用途，Claude据此决定调用
    "input_schema": {              # 参数规范（JSON Schema）
        "type": "object",
        "properties": {
            "参数名": {
                "type": "类型",
                "description": "参数描述"
            }
        },
        "required": ["必需参数"]
    }
}
```

### 工具名称规范

```python
# ✅ 正确：清晰、小写、下划线分隔
tools = [{
    "name": "get_weather",
    "description": "获取指定城市的天气信息"
}]

# ✅ 正确：描述性名称
tools = [{
    "name": "search_database",
    "description": "从数据库搜索用户信息"
}]

# ❌ 错误：包含空格或特殊字符
tools = [{
    "name": "get weather",
    "description": "获取天气"
}]

# ❌ 错误：名称过于简短
tools = [{
    "name": "calc",
    "description": "计算"
}]
```

### 描述的最佳实践

工具描述是Claude决定是否调用该工具的关键依据。

```python
# ❌ 描述太模糊 - Claude不知道何时该用
{
    "name": "search",
    "description": "搜索功能"
}

# ✅ 描述清晰具体 - 包含使用场景和参数说明
{
    "name": "search_products",
    "description": """在产品数据库中搜索商品。

适用场景：
- 用户询问某类商品的价格或库存
- 用户想找特定品牌或类型的商品
- 用户比较不同商品的规格

返回：商品名称、价格、库存状态、规格参数"""
}
```

### 参数类型定义

```python
# 完整示例
tools = [{
    "name": "book_flight",
    "description": "预订机票",
    "input_schema": {
        "type": "object",
        "properties": {
            "departure_city": {
                "type": "string",
                "description": "出发城市，如'北京'、'上海'"
            },
            "arrival_city": {
                "type": "string",
                "description": "目的地城市"
            },
            "departure_date": {
                "type": "string",
                "description": "出发日期，格式YYYY-MM-DD",
                "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
            },
            "passengers": {
                "type": "integer",
                "description": "乘客数量",
                "minimum": 1,
                "maximum": 9
            },
            "cabin_class": {
                "type": "string",
                "description": "舱位等级",
                "enum": ["economy", "business", "first"]
            }
        },
        "required": ["departure_city", "arrival_city", "departure_date", "passengers"]
    }
}]
```

### 支持的JSON Schema类型

| 类型 | 说明 | 示例 |
|------|------|------|
| string | 字符串 | "hello" |
| number | 浮点数 | 3.14 |
| integer | 整数 | 42 |
| boolean | 布尔值 | true/false |
| array | 数组 | [1, 2, 3] |
| object | 对象 | {"key": "value"} |

---

## 3.3 处理工具调用

### 识别工具调用

当Claude决定调用工具时，响应的`stop_reason`会是`tool_use`：

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "查一下北京明天天气"}]
)

print(response.stop_reason)
# 输出: "tool_use"

# 检查是否有工具调用
if response.stop_reason == "tool_use":
    for content in response.content:
        if content.type == "tool_use":
            print(f"工具名称: {content.name}")
            print(f"工具输入: {content.input}")
            print(f"工具ID: {content.id}")
```

### 完整的工具调用流程

```python
from anthropic import Anthropic
import json

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# 工具定义
tools = [{
    "name": "get_weather",
    "description": "获取城市天气信息",
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "城市名称"}
        },
        "required": ["city"]
    }
}]

def get_weather(city):
    """模拟天气查询API"""
    weather_data = {
        "北京": {"temp": 15, "condition": "晴天", "humidity": 45},
        "上海": {"temp": 18, "condition": "多云", "humidity": 65},
        "广州": {"temp": 25, "condition": "小雨", "humidity": 85}
    }
    return weather_data.get(city, {"temp": 20, "condition": "未知", "humidity": 50})

# 第一轮：发送用户请求
messages = [{"role": "user", "content": "北京今天天气怎么样？"}]

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=tools,
    messages=messages
)

print(f"停止原因: {response.stop_reason}")

# 处理工具调用
tool_results = []
for content in response.content:
    if content.type == "tool_use":
        tool_name = content.name
        tool_input = content.input
        tool_id = content.id
        
        # 执行工具
        if tool_name == "get_weather":
            result = get_weather(tool_input["city"])
        
        # 保存工具结果
        tool_results.append({
            "type": "tool_result",
            "tool_use_id": tool_id,
            "content": json.dumps(result)
        })

# 将工具结果添加到消息历史
messages.append(response)
messages.append({"role": "user", "content": "", "tool_results": tool_results})

# 第二轮：Claude整合结果
final_response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=tools,
    messages=messages
)

print(final_response.content[0].text)
```

### 工具结果的格式

```python
# 工具结果可以是字符串
tool_result = {
    "type": "tool_result",
    "tool_use_id": "toolu_xxxxx",
    "content": "晴天，15°C"
}

# 也可以是JSON字符串
tool_result = {
    "type": "tool_result",
    "tool_use_id": "toolu_xxxxx",
    "content": '{"temp": 15, "condition": "晴天"}'
}

# 如果工具执行出错
tool_result = {
    "type": "tool_result",
    "tool_use_id": "toolu_xxxxx",
    "content": "Error: 数据库连接失败"
}
```

---

## 3.4 多轮工具调用

### 连续工具调用

Claude可以连续调用多个工具：

```python
tools = [
    {
        "name": "get_stock_price",
        "description": "获取股票当前价格",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "股票代码，如AAPL、GOOGL"}
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "calculate_portfolio_value",
        "description": "计算投资组合价值",
        "input_schema": {
            "type": "object",
            "properties": {
                "holdings": {
                    "type": "array",
                    "description": "持仓列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string"},
                            "shares": {"type": "integer"}
                        }
                    }
                }
            },
            "required": ["holdings"]
        }
    }
]

# 用户请求：计算投资组合价值
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=tools,
    messages=[{
        "role": "user",
        "content": "我持有 10股苹果、5股谷歌、20股微软，计算我的投资组合总价值"
    }]
)

# Claude可能会：
# 第一轮：调用 get_stock_price 获取 AAPL, GOOGL, MSFT 的价格
# 第二轮：调用 calculate_portfolio_value 计算总价值
```

### 循环处理工具调用

```python
def process_message_with_tools(user_message, tools):
    """处理消息，自动处理多轮工具调用"""
    messages = [{"role": "user", "content": user_message}]
    max_iterations = 10  # 防止无限循环
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            tools=tools,
            messages=messages
        )
        
        # 如果不是工具调用，说明是最终响应
        if response.stop_reason != "tool_use":
            return response.content[0].text
        
        # 处理工具调用
        tool_results = []
        for content in response.content:
            if content.type == "tool_use":
                # 执行工具
                result = execute_tool(content.name, content.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": content.id,
                    "content": str(result)
                })
        
        # 添加到消息历史
        messages.append(response)
        messages.append({
            "role": "user",
            "content": "",  # 空内容，因为有tool_results
            "tool_results": tool_results
        })
    
    return "达到最大迭代次数"

def execute_tool(tool_name, tool_input):
    """执行工具并返回结果"""
    # 这里实现实际的工具逻辑
    pass
```

### 工具调用超时处理

```python
import signal

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("工具执行超时")

def execute_tool_with_timeout(tool_name, tool_input, timeout=30):
    """带超时的工具执行"""
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    
    try:
        result = execute_tool(tool_name, tool_input)
        signal.alarm(0)  # 取消闹钟
        return result
    except TimeoutError:
        return f"Error: 工具执行超过{timeout}秒"
```

---

## 3.5 代码执行工具

### 安全执行用户代码

```python
import subprocess
import tempfile
import os

class CodeExecutor:
    """安全的代码执行器"""
    
    def __init__(self, allowed_languages=["python", "javascript"]):
        self.allowed_languages = allowed_languages
        self.timeout = 10  # 10秒超时
    
    def execute(self, code, language="python"):
        """执行代码并返回结果"""
        if language not in self.allowed_languages:
            return f"Error: 不支持的语言 {language}"
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=f'.{language}',
            delete=False
        ) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            if language == "python":
                result = subprocess.run(
                    ["python3", temp_file],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
            elif language == "javascript":
                result = subprocess.run(
                    ["node", temp_file],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
            
            if result.returncode == 0:
                return result.stdout
            else:
                return f"Error: {result.stderr}"
        except subprocess.TimeoutExpired:
            return f"Error: 执行超时（>{self.timeout}秒）"
        finally:
            os.unlink(temp_file)  # 删除临时文件

# 定义代码执行工具
code_executor = CodeExecutor()

tools = [{
    "name": "execute_code",
    "description": """执行Python或JavaScript代码。

安全约束：
- 最大执行时间10秒
- 只允许读写文件、网络访问受控
- 不允许系统命令执行

返回：代码输出或错误信息""",
    "input_schema": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "要执行的代码"
            },
            "language": {
                "type": "string",
                "description": "语言类型",
                "enum": ["python", "javascript"]
            }
        },
        "required": ["code", "language"]
    }
}]

def execute_tool(tool_name, tool_input):
    if tool_name == "execute_code":
        return code_executor.execute(
            tool_input["code"],
            tool_input["language"]
        )
```

### SQL查询工具

```python
import sqlite3
import pandas as pd
from typing import Optional

class DatabaseTool:
    """SQL查询工具"""
    
    def __init__(self, db_path=":memory:"):
        self.conn = sqlite3.connect(db_path)
    
    def execute_query(self, query: str) -> str:
        """执行SQL查询"""
        try:
            # 安全检查：只允许SELECT语句
            query = query.strip().upper()
            if not query.startswith("SELECT"):
                return "Error: 只允许SELECT查询"
            
            df = pd.read_sql_query(query, self.conn)
            return df.to_string()
        except Exception as e:
            return f"Error: {str(e)}"

db_tool = DatabaseTool()

# 示例：创建表和插入数据
db_tool.conn.execute("""
    CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name TEXT,
        price REAL,
        category TEXT
    )
""")
db_tool.conn.execute("""
    INSERT INTO products (name, price, category) VALUES
    ('iPhone', 799, 'Electronics'),
    ('MacBook', 1299, 'Electronics'),
    ('Coffee', 5, 'Food')
""")

tools = [{
    "name": "sql_query",
    "description": """执行SQL SELECT查询。

约束：
- 仅支持SELECT语句
- 禁止修改数据（INSERT/UPDATE/DELETE）
- 仅支持只读操作

返回：查询结果的表格形式""",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "SQL SELECT查询语句"
            }
        },
        "required": ["query"]
    }
}]
```

### Web搜索工具

```python
import requests
from typing import Dict, Any

class WebSearchTool:
    """网页搜索工具"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("SEARCH_API_KEY")
        self.base_url = "https://api.search.com/v1/search"
    
    def search(self, query: str, num_results: int = 5) -> str:
        """搜索网页并返回结果"""
        if not self.api_key:
            return "Error: 未配置搜索API密钥"
        
        try:
            response = requests.get(
                self.base_url,
                params={
                    "q": query,
                    "num": num_results,
                    "apikey": self.api_key
                },
                timeout=10
            )
            data = response.json()
            
            results = []
            for item in data.get("results", []):
                results.append(f"标题: {item['title']}\n链接: {item['url']}\n摘要: {item['snippet']}\n")
            
            return "\n".join(results) if results else "未找到结果"
        except Exception as e:
            return f"Error: 搜索失败 - {str(e)}"

search_tool = WebSearchTool()

tools = [{
    "name": "web_search",
    "description": "搜索互联网获取最新信息",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键词"},
            "num_results": {"type": "integer", "description": "返回结果数量", "default": 5}
        },
        "required": ["query"]
    }
}]
```

---

## 3.6 工具调用的最佳实践

### 工具命名规范

```python
# ✅ 好的命名：动词_名词，清晰表达功能
tools = [
    {"name": "get_user_info"},
    {"name": "search_products"},
    {"name": "calculate_shipping"},
    {"name": "send_email"},
    {"name": "create_task"},
]

# ❌ 差的命名：过于简短或模糊
tools = [
    {"name": "user"},      # 名词，不知道做什么
    {"name": "do"},        # 太模糊
    {"name": "search"},    # 搜索什么？
]
```

### 描述的编写技巧

```python
# ✅ 好的描述：具体、包含使用场景
{
    "name": "get_order_status",
    "description": """获取订单配送状态。

触发场景：
- 用户询问"我的订单到哪了"
- 用户提供订单号查询进度
- 用户想确认预计送达时间

返回：订单状态、当前位置、预计送达时间"""
}

# ❌ 差的描述：过于笼统
{
    "name": "get_order_status",
    "description": "获取订单状态"
}
```

### 错误处理

```python
def safe_execute_tool(tool_name, tool_input):
    """安全的工具执行，带错误处理"""
    try:
        result = execute_tool(tool_name, tool_input)
        return {"success": True, "result": result}
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }

# 在处理工具调用时
for content in response.content:
    if content.type == "tool_use":
        result = safe_execute_tool(content.name, content.input)
        
        if result["success"]:
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": content.id,
                "content": str(result["result"])
            })
        else:
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": content.id,
                "content": f"Error: {result['error']}"
            })
```

### 工具选择的优化

```python
# ❌ 所有工具都传，让Claude自己判断
tools = [get_weather, search_db, send_email, create_calendar_event, ...]
# 问题：工具太多，Claude选择错误率增加

# ✅ 只传递相关的工具
relevant_tools = [get_weather, get_time]  # 用户问天气时只给天气工具

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=relevant_tools,
    messages=messages
)

# ✅ 或在系统提示词中指定使用场景
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    system="""你是一个天气助手。

当用户询问天气时，使用get_weather工具。
当用户询问时间时，使用get_time工具。
不要使用其他工具。""",
    tools=[get_weather, get_time],
    messages=messages
)
```

### 工具调用次数限制

```python
def process_with_max_tools(user_message, tools, max_calls=5):
    """处理消息，最多调用工具N次"""
    messages = [{"role": "user", "content": user_message}]
    tool_call_count = 0
    
    while tool_call_count < max_calls:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            tools=tools,
            messages=messages
        )
        
        if response.stop_reason != "tool_use":
            return response.content[0].text
        
        # 处理工具调用
        tool_results = []
        for content in response.content:
            if content.type == "tool_use":
                tool_call_count += 1
                result = execute_tool(content.name, content.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": content.id,
                    "content": str(result)
                })
        
        messages.append(response)
        messages.append({"role": "user", "content": "", "tool_results": tool_results})
    
    return "处理超时，请简化您的问题"
```

---

## 本章总结

### 核心知识点

| 知识点 | 掌握程度 | 关键点 |
|--------|----------|--------|
| 工具调用概述 | ⭐⭐⭐⭐⭐ | 工作流程、stop_reason |
| 定义工具 | ⭐⭐⭐⭐⭐ | 结构、命名、描述、Schema |
| 处理工具调用 | ⭐⭐⭐⭐⭐ | tool_use、tool_result |
| 多轮工具调用 | ⭐⭐⭐⭐⭐ | 循环处理、超时控制 |
| 代码执行 | ⭐⭐⭐⭐ | 安全沙箱、超时限制 |
| 最佳实践 | ⭐⭐⭐⭐ | 命名规范、错误处理 |

### 常用工具模板

| 工具类型 | 用途 | 注意事项 |
|----------|------|----------|
| 计算器 | 数学计算 | 表达式验证 |
| 数据库查询 | SQL执行 | 只读权限 |
| API调用 | 外部服务 | 错误处理 |
| 代码执行 | 动态计算 | 安全沙箱 |
| 文件操作 | 读写文件 | 路径限制 |

### 下一步

- 继续阅读：RAG系统专题（四）- 深入了解检索增强生成
- 实践项目：用Claude API构建一个多工具助手
- 参考资料：[Anthropic Tool Use文档](https://docs.anthropic.com/)

---

**文档元信息**
难度：⭐⭐⭐⭐ | 类型：专家设计 | 更新日期：2026-03-25 | 预计阅读时间：45分钟 | 字数：约5500字
