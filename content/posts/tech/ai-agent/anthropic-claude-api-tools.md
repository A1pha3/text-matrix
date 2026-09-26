---
title: "Claude API 基础专题（三）：工具调用"
date: "2026-03-25T11:30:00+08:00"
lastmod: "2026-09-23T10:00:00+08:00"
slug: "claude-api-tools-function-calling"
aliases:
  - /posts/tech/claude-api-tools-function-calling/
description: "讲解 Claude API 的工具调用机制：客户端工具与服务器工具的区别、工具定义与描述写法、tool_use 与 tool_result 的往返格式、多轮与并行调用，以及 tool_choice 与 strict 对工具选择的控制。"
draft: false
categories: ["技术笔记"]
tags: ["Claude", "工具调用", "MCP", "Python"]
---

# Claude API 基础专题（三）：工具调用

> 本文以 2026 年 9 月的官方文档为口径，示例模型用 `claude-sonnet-5`（同系列其他篇同理）。工具调用是 Claude API 迭代最快的区域之一，强制工具调用等行为随模型代次有变化，实际开发请以[官方文档](https://platform.claude.com/docs/en/agents-and-tools/tool-use)为准。

## 工具调用是什么

工具调用（Tool Use）让 Claude 在响应中请求调用你定义的函数。没有它，Claude 的答案只能来自训练记忆——查不了天气、读不了数据库、执行不了代码。工具调用是 Claude 从"会回答"走向"能做事"的分水岭。

要理解工具调用，先分清两种工具。区分标准只有一个：代码在哪一侧执行。

| 类型 | 代码执行位置 | 调用方式 | 典型例子 |
|------|------|------|------|
| 客户端工具 | 你的应用里 | Claude 返回 `tool_use` 块，你执行后回传 `tool_result` | 你自己定义的工具、数据库查询、HTTP 请求；`bash`、`text_editor`、`memory` 这类 schema 由 Anthropic 定义但代码仍由你执行的工具 |
| 服务器工具 | Anthropic 基础设施上 | Claude 直接调用，执行结果随响应返回 | `web_search`、`web_fetch`、`code_execution`、`tool_search` |

本文主要讲客户端工具的完整往返。服务器工具只需在 `tools` 里声明，Anthropic 会在服务端执行，你直接拿结果，省掉手动处理 `tool_use` 的那一段。

一个最简单的客户端工具定义：

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
    model="claude-sonnet-5",
    max_tokens=1024,
    tools=tools,
    messages=[{
        "role": "user",
        "content": "计算 15 * 23 + 45 的值"
    }]
)

print(response.content)
```

这段代码只发起了请求。Claude 是否真的调用 `calculator`，取决于它判断这个工具是否对完成用户请求有帮助。完整的调用流程见下一节。

值得一提：请求里带上 `tools` 参数后，API 会自动把工具定义组装进一段系统提示（工具的 JSON Schema + 使用说明），官方按模型给出了这段的开销表——如 `claude-sonnet-5` 在 `auto`/`none` 下为 354 token（`any`/`tool` 下 474），现行模型整体在 264-804 token 之间。工具定义本身也计入上下文，所以工具不是免费挂载的——后面"控制工具选择"一节会回到这一点。

### 工作流程

客户端工具调用是一个多轮往返，不是你发一次请求就结束：

```text
用户提问
    ↓
Claude 判断需要调用工具
    ↓
返回 tool_use 块（stop_reason 为 "tool_use"）
    ↓
你的代码执行工具，构造 tool_result 块
    ↓
把 tool_result 作为 user 消息回传
    ↓
Claude 整合结果，生成最终回答（stop_reason 为 "end_turn"）
```

关键点在于：`tool_result` 不是 API 的独立字段，而是以 `user` 消息的 `content` 数组里一个块的形式回传。下面两节分别讲工具怎么定义、结果怎么回传。

## 定义工具

### 工具结构

自定义客户端工具是一个字典，包含三个字段：

```python
tool = {
    "name": "工具名称",           # 唯一标识符
    "description": "工具描述",      # 描述用途，Claude 据此决定是否调用
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

`input_schema` 决定 Claude 调用工具时能传什么参数。它是一份标准的 JSON Schema（模式），Claude 会按它生成参数对象。

对格式有强约束需求时，可以在工具定义的顶层加 `strict: true`（与 `name`、`description` 并列）。它通过语法约束采样（grammar-constrained sampling）保证 `tool_use` 块里的 `input` 严格符合 schema——不会出现 `"2"` 与 `2` 的类型偏差，也不会漏掉必填字段。两点代价要清楚：schema 必须使用官方支持的 JSON Schema 子集（对象类型要求 `additionalProperties: false`）；开启后 schema 会在服务端编译并缓存最长 24 小时，且缓存的 schema 不享受与消息内容同等的隐私保护，官方明确要求不要把隐私数据（如医疗信息）写进 schema 的字段名、enum 值或 pattern 里——隐私数据应只出现在消息内容中。

对参数结构复杂、格式敏感的工具，还可以加 `input_examples` 字段，给几个通过 schema 校验的输入示例，帮助 Claude 理解用法。

### 命名规范

工具名是 Claude 识别它的依据，必须匹配官方正则 `^[a-zA-Z0-9_-]{1,128}$`——字母、数字、下划线、连字符，最长 128 个字符。拼写形式上仍建议用小写下划线分隔：

```python
# 正确：清晰，见名知意
tools = [{"name": "get_weather", "description": "获取指定城市的天气信息"}]
tools = [{"name": "search_database", "description": "从数据库搜索用户信息"}]

# 不正确：包含空格或特殊字符
tools = [{"name": "get weather", "description": "获取天气"}]

# 不够：名称太短，看不出输什么、做什么
tools = [{"name": "calc", "description": "计算"}]
```

工具一多，官方建议给名字加命名空间前缀（如 `github_list_prs`、`slack_send_message`），让归属一目了然。另一个减法是合并：与其为 `create_pr`、`review_pr`、`merge_pr` 各建一个工具，不如合成一个带 `action` 参数的工具——工具越少，Claude 选择的歧义越小。

### 描述是关键

工具描述是 Claude 决定是否调用该工具的依据。描述越具体，Claude 的选择越准确：

```python
# 太模糊 - Claude 不清楚何时该用
{
    "name": "search",
    "description": "搜索功能"
}

# 具体 - 写明使用场景、参数和返回
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

描述里写清"什么情况下该用"和"能返回什么"，比只写"搜索商品"更能引导 Claude 正确选择。官方对此给过量化口径：每个工具描述至少 3-4 句话，复杂的工具写更多——描述是官方明确认定的影响工具表现的头号因素，值得多花笔墨。同样值得做的还有收敛返回值：只返回 Claude 做下一步判断需要的字段，用语义稳定的标识符（slug、UUID），而不是把数据库原始行整个吐回去。

### 参数类型定义

`input_schema` 支持 JSON Schema 的常用类型和约束：`string`、`number`、`integer`、`boolean`、`array`、`object`，以及 `pattern`、`minimum`、`maximum`、`enum` 等约束：

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

## 处理工具调用

### 识别工具调用

当 Claude 决定调用客户端工具时，响应的 `stop_reason` 是 `"tool_use"`，`content` 里会出现一到多个 `tool_use` 块。每个块包含 `id`、`name`、`input` 三个字段：

```python
response = client.messages.create(
    model="claude-sonnet-5",
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

`id` 很重要，后面回传 `tool_result` 时要用它把结果和这次调用对应起来。

### 工具结果格式

拿到 `tool_use` 后，你的代码执行真实函数，然后把结果以 `tool_result` 块的形式回传。`tool_result` 必须满足三条格式要求：

1. 放在 `user` 消息的 `content` 数组里，作为独立块。
2. 紧跟对应的 `tool_use` 块之后，中间不能插入其他消息。
3. 在 `content` 数组里必须排在所有文本块之前——文本只能出现在全部 `tool_result` 之后。

另有第四条只在混用服务器工具时生效：如果上一轮 assistant 响应里还有未出结果的服务器工具调用，这条 `user` 消息只能放 `tool_result` 块，后面跟文本会提前终结本轮，请求会收到点名未决服务器工具的 400 错误。纯客户端工具不受此限。

```python
# 正确：作为 content 数组里的一个块
tool_result = {
    "type": "tool_result",
    "tool_use_id": "toolu_xxxxx",
    "content": "晴天，15°C"
}

# 正确：content 可以是 JSON 字符串
tool_result = {
    "type": "tool_result",
    "tool_use_id": "toolu_xxxxx",
    "content": '{"temp": 15, "condition": "晴天"}'
}

# 正确：content 可以是嵌套内容块列表
tool_result = {
    "type": "tool_result",
    "tool_use_id": "toolu_xxxxx",
    "content": [{"type": "text", "text": "晴天，15°C"}]
}

# content 也可以整个省略，表示执行完成但没有输出
tool_result = {
    "type": "tool_result",
    "tool_use_id": "toolu_xxxxx"
}

# 标记工具执行出错
tool_result = {
    "type": "tool_result",
    "tool_use_id": "toolu_xxxxx",
    "content": "Error: 数据库连接失败",
    "is_error": True
}
```

执行出错时，把 `is_error` 设为 `True`，Claude 会据此调整策略，而不是把错误文本当成正常结果。

不要把 `tool_result` 放在 `user` 消息的顶层字段，也不要把它塞进 `system` 消息。它会破坏 Claude 对消息结构的解析，导致 `tool_use` 找不到对应的 `tool_result`。

### 完整流程

把识别、执行、回传串起来，就是一次完整的工具调用：

```python
import os
import json

from anthropic import Anthropic

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
    model="claude-sonnet-5",
    max_tokens=1024,
    tools=tools,
    messages=messages
)

# 处理 tool_use，构造 tool_result
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
            "content": json.dumps(result, ensure_ascii=False)
        })

# 把 assistant 响应回填进历史，再把工具结果作为 user 消息追加
messages.append({"role": "assistant", "content": response.content})
messages.append({"role": "user", "content": tool_results})

# 第二轮：Claude 整合结果
final_response = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1024,
    tools=tools,
    messages=messages
)

print(final_response.content[0].text)
```

注意第二轮的 `messages` 里，`tool_result` 块通过 `content` 数组传入，且排在文本之前。这是官方要求的格式。

## 多轮与并行调用

### 连续工具调用

一个任务可能需要多个工具先后配合。比如先查股价，再算投资组合：

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
    model="claude-sonnet-5",
    max_tokens=1024,
    tools=tools,
    messages=[{
        "role": "user",
        "content": "我持有 10股苹果、5股谷歌、20股微软，计算我的投资组合总价值"
    }]
)
```

第一次调用可能只返回 `get_stock_price` 的 `tool_use`。你把结果回传后，Claude 再决定是否调用 `calculate_portfolio_value`。这就是上一节的循环逻辑要处理的事。

### 循环处理工具调用

把上一节的单轮流程包进循环，就能处理任意多轮调用，直到 Claude 不再请求工具：

```python
# get_stock_price、calculate_portfolio_value 的函数体与 get_weather 同理，此处从略
def execute_tool(tool_name, tool_input):
    if tool_name == "get_weather":
        return get_weather(tool_input["city"])
    if tool_name == "get_stock_price":
        return get_stock_price(tool_input["symbol"])
    if tool_name == "calculate_portfolio_value":
        return calculate_portfolio_value(tool_input["holdings"])
    return f"Error: 未实现的工具 {tool_name}"

def process_message_with_tools(user_message, tools, max_iterations=10):
    messages = [{"role": "user", "content": user_message}]

    for _ in range(max_iterations):
        response = client.messages.create(
            model="claude-sonnet-5",
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

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    return "达到最大迭代次数，未完成"
```

`max_iterations` 是必要的兜底。工具循环没有上限时，一旦 Claude 反复调用工具，可能拖很久。设一个合理的上限，超出就返回错误信息。

### 并行工具调用

Claude 可以在同一次响应里请求调用多个工具，此时 `content` 里会出现多个 `tool_use` 块。Claude 4 及之后的模型在任务受益时会默认并行调用，无需特别开启。

上面的循环天然支持并行：它遍历所有 `tool_use` 块，逐个执行，再把所有 `tool_result` 一起回传。两点执行语义值得注意：API 不规定这些调用的执行顺序，并发跑（`asyncio.gather`）、按顺序跑都由你的代码决定；但每个 `tool_use` 块都必须有对应的 `tool_result`——即使你选择跳过某个调用（比如顺序执行时前面的调用失败了），也要回传一个 `is_error: true` 的结果说明原因，比如 `"Not executed: the preceding write_file call failed."`，不能留空。

并行适合互不依赖的工具：同时查天气和查日历，两个结果在同一个数组里一次返回，Claude 一次整合。判断标准是依赖关系——有依赖的工具（先查股价再算组合）Claude 会拆成多轮，不会塞进同一次响应。

需要限制并行时，在 `tool_choice` 对象里加 `disable_parallel_tool_use: true`（注意它不是顶层参数）。`tool_choice` 为默认的 `auto` 时，这个开关的含义是"每次响应最多一个工具调用"，Claude 仍可以直接用文本回答。

## 控制工具选择

默认情况下，Claude 自己判断要不要调用工具、调用哪个。需要更精确控制时，用 `tool_choice` 参数，共四种取值：

```python
# 强制 Claude 必须调用某个工具（不包含文本回答）
response = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1024,
    tools=tools,
    tool_choice={"type": "tool", "name": "get_weather"},
    messages=messages
)

# 强制 Claude 调用工具，但由它自己选调用哪个
response = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1024,
    tools=tools,
    tool_choice={"type": "any"},
    messages=messages
)

# 禁止调用工具，只做文本回答
response = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1024,
    tools=tools,
    tool_choice={"type": "none"},
    messages=messages
)
```

四个取值的分工：`auto` 是提供了 `tools` 时的默认值，由 Claude 自己决定；`any` 强制调用其中一个工具但不指定哪个；`tool` 强制调用指定工具；`none` 禁止调用任何工具（未提供 `tools` 时这也是默认值）。

**一个必须知道的版本边界**：强制工具调用正在随模型代次收紧。官方文档明确，Claude Opus 5.5、Fable 5.1、Mythos 5.1 已不支持 `any` 和 `tool`，请求会直接返回 400 错误；手动扩展思考（`thinking: {type: "enabled"}`）模式下同样不支持。这些场景官方给的替代方案是：用 `auto` 配合 `strict: true` 保证入参合规，或改用结构化输出（structured outputs）拿固定 JSON；仍然可以用提示词引导 `auto` 选哪个工具。`none` 在所有模型上都可用。未列入这份受限名单的模型（如 `claude-sonnet-5`）四种取值均可正常使用。

还有两个使用细节：`any` 和 `tool` 是靠预填充 assistant 消息实现强制的，所以 Claude 不会在 `tool_use` 块之前输出任何自然语言，即使你明确要求；另外改动 `tool_choice` 会使 prompt caching 里的消息缓存失效（工具定义和系统提示的缓存不受影响），在高频调用且依赖缓存的场景里，频繁切换 `tool_choice` 会推高成本。

`none` 适合已经拿到结果、只想让 Claude 收尾总结的场景。`tool` 模式适合"这个请求必须走某个工具"的固定流程。但多数情况用默认的 `auto` 就好。

另一个控制手段是少传工具。工具传得越多，Claude 选错的概率越大。只在请求里传当前场景相关的工具，而不是把全部工具一股脑塞进去——每个工具定义都占上下文，这同时也是省 token：

```python
# 不要每次请求都把全部工具传进去（示意）
all_tools = ["get_weather", "search_db", "send_email", "create_calendar_event"]

# 按场景只传相关的：用户问天气时只给天气和时间的工具
relevant_tools = [t for t in all_tools if t in ("get_weather", "get_time")]

response = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1024,
    tools=relevant_tools,
    messages=messages
)
```

## 错误处理

工具执行有两种出错情况，处理方式不同。

工具本身执行失败（网络超时、数据库异常），应在 `tool_result` 里返回错误信息并设置 `is_error: True`，让 Claude 知道这次调用没成功，可以换策略或让用户换个方式问：

```python
def safe_execute_tool(tool_name, tool_input):
    try:
        result = execute_tool(tool_name, tool_input)
        return {"ok": True, "result": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# 处理工具调用时
for content in response.content:
    if content.type == "tool_use":
        outcome = safe_execute_tool(content.name, content.input)
        if outcome["ok"]:
            tool_result = {
                "type": "tool_result",
                "tool_use_id": content.id,
                "content": str(outcome["result"])
            }
        else:
            tool_result = {
                "type": "tool_result",
                "tool_use_id": content.id,
                "content": f"Error: {outcome['error']}",
                "is_error": True
            }
        tool_results.append(tool_result)
```

工具调用无效（Claude 生成的调用缺了必填参数，或请求了你这里没有实现的工具分支），通常说明描述给的信息不够。官方给出的第一选择是把工具 `description` 写得更详细再重试；也可以先回传一个说明错误的 `tool_result`（置 `is_error: True`，如 `"Error: Missing required 'location' parameter"`），Claude 会带着补充信息自动重试，一般重试 2-3 次才会放弃并向用户道歉。分发逻辑有缺口（`execute_tool` 没覆盖某个分支）同样会走到这里，一并补齐。

错误信息本身也有讲究：写清哪里出错、下一步该做什么（如 `"Rate limit exceeded. Retry after 60 seconds."`），比一个干巴巴的 `"failed"` 更能让 Claude 自行恢复，而不是瞎猜。

外部工具调用要设超时，避免某个慢接口拖住整个循环：

```python
import concurrent.futures

def execute_tool_with_timeout(tool_name, tool_input, timeout=30):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(execute_tool, tool_name, tool_input)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            return f"Error: 工具执行超过{timeout}秒"
```

安全方面有一个容易被忽略的点：工具的返回内容来自外部，可能是网页、邮件、第三方 API。这些内容对 Claude 而言是不可信数据，可能夹带试图劫持 Claude 的指令（间接提示注入）。始终把外部内容放在 `tool_result` 块里按数据对待，不要把它拼进 `system` 提示词或当作普通用户文本。

## 推荐做法

把上面的要点收拢成几条可执行的原则：

- **命名见名知意**：`get_user_info`、`search_products` 比 `user`、`do` 更能让 Claude 判断何时调用；工具一多就加服务前缀（`github_list_prs`）。
- **描述写场景**：在 `description` 里写清"什么情况下该用"和"能返回什么"，每个工具至少 3-4 句，比只写一句话更好。
- **只传相关工具**：按当前场景裁剪 `tools`，减少选错概率，也省上下文。
- **正确回传 `tool_result`**：放在 `user` 消息的 `content` 数组里，紧跟 `tool_use` 块，排在所有文本之前；并行调用的每个 `tool_use` 都要有对应结果。
- **错误标记 `is_error`**：工具执行失败时回传错误信息并置 `is_error: True`，错误文本写清原因和下一步建议。
- **循环设上限**：给多轮调用设 `max_iterations`，避免无界循环。
- **外部内容当数据**：工具返回内容一律视为不可信，放 `tool_result` 块，不拼进 `system`。

## 进阶方向

- **Tool Runner（SDK 内置，beta）**：让 SDK 替你跑整个工具循环。用 `@beta_tool` 装饰器从类型提示和 docstring 自动生成工具定义，再交给 `client.beta.messages.tool_runner()`，`tool_use` 解析、执行、结果回传全部自动完成。原型验证阶段值得先试它，再决定是否需要手动控制。
- **MCP（Model Context Protocol）**：通过 MCP 协议连接外部工具，无需在每次请求里手动定义每个工具。Anthropic 也提供 MCP 连接器，可在 Messages API 里直接连远程 MCP 服务器，不必自建 MCP 客户端。
- **服务器工具**：`web_search`、`web_fetch`、`code_execution`、`tool_search` 等由 Anthropic 在服务端执行，省掉手动处理 `tool_use` 的循环。
- **RAG 系统**：结合检索增强生成，让 Claude 查询知识库。
- **多 Agent 协作**：多个 Claude 实例协同，各自负责不同的工具集。
- **并行与缓存**：并行执行独立工具、缓存工具结果，减少等待和 token（词元）消耗。

**参考资源：**
- [Anthropic Tool use 文档](https://platform.claude.com/docs/en/agents-and-tools/tool-use)
- [Define tools（工具定义与 tool_choice）](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools)
- [Handle tool calls（tool_result 格式）](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)
- [Parallel tool use（并行调用与执行语义）](https://platform.claude.com/docs/en/agents-and-tools/tool-use/parallel-tool-use)
- [Strict tool use（严格模式）](https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use)
- [Tool Runner（SDK 工具循环）](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner)
- [MCP 协议规范](https://modelcontextprotocol.io/)