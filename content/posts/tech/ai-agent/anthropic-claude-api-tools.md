---
title: "Claude API基础专题（三）：工具调用"
date: "2026-03-25T11:30:00+08:00"
slug: "claude-api-tools-function-calling"
aliases:
  - /posts/tech/claude-api-tools-function-calling/
description: "深入探讨Claude API的工具调用机制，包括Function Calling的原理、工具定义与注册、多工具协同、批处理模式，以及MCP协议的使用方法。"
draft: false
categories: ["技术笔记"]
tags: ["Claude", "工具调用", "MCP", "Python"]
---

# Claude API 基础专题（三）：工具调用

## 工具调用概述

工具调用（Tool Use / Function Calling）允许 Claude 在响应中请求调用你定义的外部函数。这是 Claude 与外部世界交互的核心方式——没有它，Claude 只能凭训练数据回答，无法查天气、查数据库、执行代码。

```python
from anthropic import Anthropic
import os

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

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

### 工作流程

```
用户提问
    ↓
Claude 判断需要调用工具
    ↓
返回 tool_use 请求（stop_reason: "tool_use"）
    ↓
执行工具，返回结果
    ↓
Claude 整合结果，生成最终回答
    ↓
返回最终响应（stop_reason: "end_turn"）
```

---

## 定义工具

### 工具结构

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

### 命名规范

```python
# 正确：清晰、小写、下划线分隔
tools = [{"name": "get_weather", "description": "获取指定城市的天气信息"}]
tools = [{"name": "search_database", "description": "从数据库搜索用户信息"}]

# 错误：包含空格或特殊字符
tools = [{"name": "get weather", "description": "获取天气"}]

# 错误：名称过于简短
tools = [{"name": "calc", "description": "计算"}]
```

### 描述是关键

工具描述是 Claude 决定是否调用该工具的依据。描述越具体，Claude 的选择越准确。

```python
# 太模糊 - Claude 不知道何时该用
{
    "name": "search",
    "description": "搜索功能"
}

# 具体 - 包含使用场景和参数说明
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

支持的 JSON Schema 类型：`string`、`number`、`integer`、`boolean`、`array`、`object`。

---

## 处理工具调用

### 识别工具调用

当 Claude 决定调用工具时，响应的 `stop_reason` 是 `"tool_use"`：

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "查一下北京明天天气"}]
)

print(response.stop_reason)
# 输出: "tool_use"

if response.stop_reason == "tool_use":
    for content in response.content:
        if content.type == "tool_use":
            print(f"工具名称: {content.name}")
            print(f"工具输入: {content.input}")
            print(f"工具ID: {content.id}")
```

### 完整流程

```python
from anthropic import Anthropic
import json

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

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

# 处理工具调用
tool_results = []
for content in response.content:
    if content.type == "tool_use":
        tool_name = content.name
        tool_input = content.input
        tool_id = content.id

        if tool_name == "get_weather":
            result = get_weather(tool_input["city"])

        tool_results.append({
            "type": "tool_result",
            "tool_use_id": tool_id,
            "content": json.dumps(result)
        })

# 将工具结果添加到消息历史
messages.append(response)
messages.append({"role": "user", "content": "", "tool_results": tool_results})

# 第二轮：Claude 整合结果
final_response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=tools,
    messages=messages
)

print(final_response.content[0].text)
```

### 工具结果格式

```python
# 字符串
tool_result = {
    "type": "tool_result",
    "tool_use_id": "toolu_xxxxx",
    "content": "晴天，15°C"
}

# JSON 字符串
tool_result = {
    "type": "tool_result",
    "tool_use_id": "toolu_xxxxx",
    "content": '{"temp": 15, "condition": "晴天"}'
}

# 错误
tool_result = {
    "type": "tool_result",
    "tool_use_id": "toolu_xxxxx",
    "content": "Error: 数据库连接失败"
}
```

---

## 多轮工具调用

### 连续工具调用

Claude 可以连续调用多个工具，例如先查股价再算投资组合：

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

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=tools,
    messages=[{
        "role": "user",
        "content": "我持有 10股苹果、5股谷歌、20股微软，计算我的投资组合总价值"
    }]
)
```

### 循环处理工具调用

```python
def process_message_with_tools(user_message, tools):
    messages = [{"role": "user", "content": user_message}]
    max_iterations = 10

    for iteration in range(max_iterations):
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            tools=tools,
            messages=messages
        )

        if response.stop_reason != "tool_use":
            return response.content[0].text

        tool_results = []
        for content in response.content:
            if content.type == "tool_use":
                result = execute_tool(content.name, content.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": content.id,
                    "content": str(result)
                })

        messages.append(response)
        messages.append({
            "role": "user",
            "content": "",
            "tool_results": tool_results
        })

    return "达到最大迭代次数"

def execute_tool(tool_name, tool_input):
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
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)

    try:
        result = execute_tool(tool_name, tool_input)
        signal.alarm(0)
        return result
    except TimeoutError:
        return f"Error: 工具执行超过{timeout}秒"
```

---

## 代码执行工具

### 安全执行

```python
import subprocess
import tempfile
import os

class CodeExecutor:
    def __init__(self, allowed_languages=["python", "javascript"]):
        self.allowed_languages = allowed_languages
        self.timeout = 10

    def execute(self, code, language="python"):
        if language not in self.allowed_languages:
            return f"Error: 不支持的语言 {language}"

        with tempfile.NamedTemporaryFile(
            mode='w', suffix=f'.{language}', delete=False
        ) as f:
            f.write(code)
            temp_file = f.name

        try:
            if language == "python":
                result = subprocess.run(
                    ["python3", temp_file],
                    capture_output=True, text=True, timeout=self.timeout
                )
            elif language == "javascript":
                result = subprocess.run(
                    ["node", temp_file],
                    capture_output=True, text=True, timeout=self.timeout
                )

            if result.returncode == 0:
                return result.stdout
            else:
                return f"Error: {result.stderr}"
        except subprocess.TimeoutExpired:
            return f"Error: 执行超时（>{self.timeout}秒）"
        finally:
            os.unlink(temp_file)

code_executor = CodeExecutor()

tools = [{
    "name": "execute_code",
    "description": "执行Python或JavaScript代码。最大执行时间10秒。",
    "input_schema": {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "要执行的代码"},
            "language": {
                "type": "string",
                "description": "语言类型",
                "enum": ["python", "javascript"]
            }
        },
        "required": ["code", "language"]
    }
}]
```

### SQL 查询工具

```python
import sqlite3
import pandas as pd

class DatabaseTool:
    def __init__(self, db_path=":memory:"):
        self.conn = sqlite3.connect(db_path)

    def execute_query(self, query: str) -> str:
        query_upper = query.strip().upper()
        if not query_upper.startswith("SELECT"):
            return "Error: 只允许SELECT查询"
        try:
            df = pd.read_sql_query(query, self.conn)
            return df.to_string()
        except Exception as e:
            return f"Error: {str(e)}"

db_tool = DatabaseTool()
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
```

### Web 搜索工具

```python
import requests
import os

class WebSearchTool:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("SEARCH_API_KEY")
        self.base_url = "https://api.search.com/v1/search"

    def search(self, query: str, num_results: int = 5) -> str:
        if not self.api_key:
            return "Error: 未配置搜索API密钥"
        try:
            response = requests.get(
                self.base_url,
                params={"q": query, "num": num_results, "apikey": self.api_key},
                timeout=10
            )
            data = response.json()
            results = []
            for item in data.get("results", []):
                results.append(f"标题: {item['title']}\n链接: {item['url']}\n摘要: {item['snippet']}\n")
            return "\n".join(results) if results else "未找到结果"
        except Exception as e:
            return f"Error: 搜索失败 - {str(e)}"
```

---

## 推荐做法

### 命名规范

```python
# 好的命名：动词_名词
tools = [
    {"name": "get_user_info"},
    {"name": "search_products"},
    {"name": "calculate_shipping"},
    {"name": "send_email"},
]

# 差的命名：过于简短或模糊
tools = [
    {"name": "user"},      # 名词，不知道做什么
    {"name": "do"},        # 太模糊
    {"name": "search"},    # 搜索什么？
]
```

### 描述编写技巧

```python
# 好的描述：具体、包含使用场景
{
    "name": "get_order_status",
    "description": """获取订单配送状态。

触发场景：
- 用户询问"我的订单到哪了"
- 用户提供订单号查询进度
- 用户想确认预计送达时间

返回：订单状态、当前位置、预计送达时间"""
}

# 差的描述：过于笼统
{
    "name": "get_order_status",
    "description": "获取订单状态"
}
```

### 错误处理

```python
def safe_execute_tool(tool_name, tool_input):
    try:
        result = execute_tool(tool_name, tool_input)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e), "error_type": type(e).__name__}

# 处理工具调用时
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

### 控制工具选择

工具太多时，Claude 选错工具的概率会增加。只传递当前场景相关的工具：

```python
# 不要一股脑把所有工具都传进去
tools = [get_weather, search_db, send_email, create_calendar_event, ...]

# 只传相关的
relevant_tools = [get_weather, get_time]  # 用户问天气时只给天气工具

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=relevant_tools,
    messages=messages
)
```

### 限制工具调用次数

```python
def process_with_max_tools(user_message, tools, max_calls=5):
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

## 进阶方向

- **MCP（Model Context Protocol）**：通过 MCP 协议连接外部工具，无需手动定义每个工具
- **RAG 系统**：结合检索增强生成，让 Claude 查询知识库
- **多 Agent 协作**：多个 Claude 实例协同，各自负责不同的工具集
- **性能优化**：缓存工具结果、并行工具调用、减少 token 消耗
- **安全性**：沙箱执行、权限控制、审计日志

**参考资源：**
- [Anthropic Tool Use 文档](https://docs.anthropic.com/)
- [MCP 协议规范](https://modelcontextprotocol.io/)