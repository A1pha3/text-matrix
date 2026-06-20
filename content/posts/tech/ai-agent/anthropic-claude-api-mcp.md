---
title: "Claude API基础专题（五）：MCP协议深度解析"
date: "2026-03-25T14:00:00+08:00"
slug: "claude-api-mcp-model-context-protocol"
aliases:
  - /posts/tech/claude-api-mcp-model-context-protocol/
description: "MCP（Model Context Protocol）协议的设计思想、架构组成与工作流程，如何构建 MCP 服务器与客户端，以及 MCP 与传统工具调用的区别与适用场景。"
draft: false
categories: ["技术笔记"]
tags: ["Claude", "MCP", "JSON-RPC", "Python"]
---

# Claude API 基础专题（五）：MCP 协议深度解析

> 预计阅读时间：35 分钟 | 难度：⭐⭐⭐⭐

---

> **目标读者**：希望扩展Claude能力边界的开发者
> **前置知识**：已完成第一篇《API基础》、第二篇《提示词工程》、第三篇《工具调用》、第四篇《RAG系统》
> **说明**：MCP 是 Claude 能力扩展的核心协议，建议先理解设计思想再动手实现

---

## 章节导航

| 小节 | 主题 | 重要程度 |
|------|------|----------|
| 5.1 | MCP 概述：为什么需要 MCP | ⭐⭐⭐⭐⭐ |
| 5.2 | MCP 架构详解 | ⭐⭐⭐⭐⭐ |
| 5.3 | MCP 协议工作流程 | ⭐⭐⭐⭐⭐ |
| 5.4 | 构建 MCP 服务器 | ⭐⭐⭐⭐⭐ |
| 5.5 | MCP 客户端开发 | ⭐⭐⭐⭐ |
| 5.6 | MCP 生态与实践 | ⭐⭐⭐⭐ |
| 5.7 | MCP 与工具调用的区别 | ⭐⭐⭐⭐ |

---

## 全文总览

MCP 把"工具调用"这件事从厂商私有格式抽离出来，做成一层开放协议。理解 MCP，关键是抓住三条边界：

```
┌──────────────────────────────────────────────────────────────────┐
│  边界 1：应用层 ↔ 协议层                                          │
│  Claude Desktop / IDE  ←(MCP 客户端)→  MCP 服务器                 │
│  应用只看协议，不关心服务器用什么语言实现                            │
├──────────────────────────────────────────────────────────────────┤
│  边界 2：资源 ↔ 工具                                              │
│  资源 = LLM 主动读取的数据（读权限）                                │
│  工具 = LLM 调用执行的函数（写权限）                                │
├──────────────────────────────────────────────────────────────────┤
│  边界 3：协议 ↔ 传输                                              │
│  JSON-RPC 2.0 消息层是稳定的                                       │
│  传输层可换：stdio / SSE / WebSocket                              │
└──────────────────────────────────────────────────────────────────┘
```

读完本文，你应该能回答三个问题：MCP 解决了什么厂商锁定问题、客户端与服务器如何握手并交换能力、什么场景下应该选 MCP 而不是直接写工具调用。

---

## 学习目标

读完本文后，你应当能够：

1. **说清 MCP 存在的理由**：用自己的话讲出厂商锁定、重复开发、生态割裂这三件事，以及 MCP 用开放协议怎么收口。
2. **画出 MCP 的三层架构**：应用层、客户端、服务器各承担什么职责，资源与工具的权限边界在哪里。
3. **走完一次完整握手**：从 `initialize` 到 `tools/list` 再到 `tools/call`，能解释每条 JSON-RPC 消息的字段含义。
4. **独立实现一个最小 MCP 服务器**：用 `mcp.server` 或 FastMCP 注册工具、处理调用、返回 `TextContent`，并在 Claude Desktop 中跑通。
5. **做出选型判断**：面对一个具体需求，能判断该用普通工具调用还是 MCP，并给出理由。

---

## 5.1 MCP概述：为什么需要MCP

MCP 的价值不在于"多了一种调用工具的方式"，而在于把工具定义、发现和调用从厂商私有格式收束为开放协议，让一次开发的工具能在多个 LLM 应用里复用。理解这一点，后面的协议细节才有支点。

### 问题的起源

要理解 MCP（Model Context Protocol，模型上下文协议），先看一个根本问题：**为什么 LLM 需要额外的协议来与外部工具交互？**

回顾工具调用的发展历程：

**阶段一：硬编码工具调用（2019-2022）**

在LLM发展的早期阶段，每个LLM提供者（如OpenAI、Google）都定义了各自专有的工具调用格式：

```python
# OpenAI的格式
{
    "name": "get_weather",
    "description": "获取天气",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {"type": "string"}
        }
    }
}

# Google的格式
{
    "function_declarations": [{
        "name": "get_weather",
        "description": "获取天气",
        "parameters": {...}
    }]
}

# Anthropic的格式
{
    "name": "get_weather",
    "description": "获取天气",
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "城市名称"}
        }
    }
}
```

**为什么会有这种碎片化？**

根因在生态锁定（vendor lock-in）：**每个 LLM 提供商都想把开发者绑在自己的格式上**。用 OpenAI 的格式写了一套工具，再想迁到 Google 的模型就得重写一遍，因为工具定义、参数结构、调用约定都不一样。

由此衍生出几个连锁问题：

| 问题 | 影响 |
|------|------|
| **供应商锁定** | 开发者被绑定在某一 LLM 提供商 |
| **重复开发** | 同一个工具需要为不同提供商编写不同版本 |
| **生态割裂** | 工具开发者只愿意为流行平台开发 |
| **创新受阻** | 新入局的 LLM 难以快速建立工具生态 |

### MCP的诞生

MCP 由 Anthropic 牵头，联合多个行业合作伙伴共同制定，是一个**开放标准**。它的思路是：

> **给 LLM 工具调用做一个"USB 接口"——一次开发，到处可用。**

**为什么叫"模型上下文协议"？**

这个名字本身揭示了 MCP 的本质：
- **协议（Protocol）**：一套标准化的通信规则
- **上下文（Context）**：MCP 不仅仅是调用工具，它还能为 LLM 提供持久的上下文状态
- **模型无关（Model-agnostic）**：理论上任何 LLM 都可以实现 MCP

### MCP vs 传统工具调用

| 特性 | 传统工具调用 | MCP |
|------|------------|-----|
| **标准化程度** | 各大厂商各自定义 | 统一开放标准 |
| **上下文持久化** | 无，每次请求独立 | 有，支持多轮对话状态 |
| **双向通信** | 单向（LLM调用工具） | 支持服务端主动推送 |
| **工具发现** | 手动配置 | 支持自动发现 |
| **类型安全** | 弱（JSON Schema） | 强（JSON-RPC + 类型系统） |
| **供应商锁定** | 严重 | 无（一次开发，多端使用） |

### MCP的设计原则

MCP 的设计围绕四条原则展开：

**1. 开放性（Openness）**

MCP 是一个开放标准，任何人都可以免费使用和实现。这与当年 USB 取代各种专用接口的道理一样——**标准化带来生态繁荣**。

**2. 简单性（Simplicity）**

MCP 的协议设计尽量简单，降低实现门槛。一个 MCP 服务器可以用任何语言实现，只需要支持 JSON-RPC 2.0。

**3. 可组合性（Composability）**

MCP 支持模块化设计。多个 MCP 服务器可以并行工作，共同为 LLM 提供能力。这就像搭积木——你可以根据需要组合不同的服务器。

**4. 安全性（Security）**

MCP 强调在安全沙箱环境中运行工具，避免 LLM 直接访问敏感资源。这是 MCP 与其他方案的显著区别。

---

## 5.2 MCP 架构详解

### 整体架构

MCP 采用客户端-服务器架构，包含三个核心组件：

```
┌─────────────────────────────────────────────────────────────┐
│                      LLM 应用层                             │
│                   （Claude Desktop / IDE）                  │
└─────────────────────────┬───────────────────────────────────┘
                          │ MCP协议
┌─────────────────────────▼───────────────────────────────────┐
│                     MCP 客户端                              │
│              （负责与服务器通信，管理连接）                   │
└─────────────────────────┬───────────────────────────────────┘
                          │ 
┌─────────────────────────▼───────────────────────────────────┐
│                    MCP 服务器                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 文件系统  │  │  数据库  │  │  Web API │  │ GitHub   │   │
│  │  服务器  │  │  服务器  │  │  服务器  │  │  服务器  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**为什么这样设计？**

这种架构的好处是**关注点分离（Separation of Concerns）**：

- **LLM 应用层**只需要理解如何与 MCP 客户端交互，不需要关心具体工具的实现
- **MCP 客户端**负责连接管理、协议解析、请求路由等通用功能
- **MCP 服务器**专注于提供特定能力（如文件系统、数据库等）

### MCP 服务器类型

MCP 服务器主要分为两类：

**1. 本地服务器（Local Servers）**

本地服务器直接运行在用户的机器上，访问本地资源：

| 服务器 | 用途 | 权限 |
|--------|------|------|
| filesystem | 读写本地文件 | 需要用户授权 |
| memory | 跨会话持久化记忆 | 自动获得 |
| sequential-thinking | 复杂推理辅助 | 自动获得 |
| slacker | Slack 消息操作 | 需要 OAuth 授权 |

**2. 远程服务器（Remote Servers）**

远程服务器部署在云端，通过网络访问：

| 服务器 | 用途 | 连接方式 |
|--------|------|----------|
| github | GitHub 操作 | API Token |
| google-maps | 地图服务 | API Key |
| puppeteer | 网页抓取 | 无头浏览器 |

### 资源与工具的区别

MCP 中有一个重要概念：**资源（Resources）vs 工具（Tools）**

```python
# 资源：是LLM可以读取的数据
# 类似于"文件"，LLM主动请求读取
{
    "type": "resource",
    "name": "user_profile",
    "uri": "file://./user_profile.json",
    "mimeType": "application/json"
}

# 工具：是LLM可以调用的函数
# 类似于"程序"，LLM调用执行
{
    "type": "tool",
    "name": "send_email",
    "description": "发送邮件",
    "inputSchema": {...}
}
```

**为什么要区分？**

区别在于**谁来发起操作**：

| 类型 | 发起方 | 例子 | 权限要求 |
|------|--------|------|----------|
| 资源 | LLM 主动读取 | 查看文件内容 | 读权限 |
| 工具 | LLM 调用执行 | 删除文件、发送邮件 | 写权限 |

这种区分让**权限控制更精细**：读取文件只需要读权限，删除文件需要写权限。

---

## 5.3 MCP协议工作流程

### JSON-RPC基础

MCP 底层使用 JSON-RPC 2.0 协议通信。JSON-RPC 是一种轻量级的远程过程调用协议。

**为什么选择 JSON-RPC？**

1. **简单易实现**：JSON-RPC 只定义了少数几种消息类型，任何语言都能轻松实现
2. **无状态友好**：适合 HTTP 等无状态协议
3. **广泛支持**：几乎所有编程语言都有成熟的 JSON-RPC 库
4. **调试友好**：基于 JSON，人类可读，方便调试

### 核心消息类型

MCP 定义了以下核心消息类型：

```python
# 1. 初始化请求（客户端 → 服务器）
{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "roots": {"list": True},
            "sampling": {}
        },
        "clientInfo": {
            "name": "claude-desktop",
            "version": "1.0.0"
        }
    }
}

# 2. 初始化响应（服务器 → 客户端）
{
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {"listChanged": True},
            "resources": {"subscribe": True, "listChanged": True}
        },
        "serverInfo": {
            "name": "filesystem-server",
            "version": "1.0.0"
        }
    }
}
```

### 完整交互流程

```
时间轴          客户端                          服务器
   │              │                               │
   │ ─── handshake request ──────────────────►  │
   │              │                               │
   │              │  ◄────────────────── handshake response ──
   │              │                               │
   │ ─── tools/list ─────────────────────────►  │
   │              │                               │
   │              │  ◄──────────────────── tools/list result ──
   │              │                               │
   │ ─── tools/call ─────────────────────────►  │
   │              │                               │
   │              │  ◄─────────────────────── result ──
   │              │                               │
   │ ─── resources/list ────────────────────►  │
   │              │                               │
   │              │  ◄────────────────── resources/list result ──
```

### 工具调用详解

当 LLM 决定调用一个工具时，客户端会发送：

```python
# 工具调用请求
{
    "jsonrpc": "2.0",
    "id": 42,
    "method": "tools/call",
    "params": {
        "name": "read_file",
        "arguments": {
            "path": "/Users/demo/readme.md"
        }
    }
}
```

服务器处理后会返回：

```python
# 成功响应
{
    "jsonrpc": "2.0",
    "id": 42,
    "result": {
        "content": [
            {
                "type": "text",
                "text": "# Hello World\n\nThis is a sample file."
            }
        ],
        "isError": False
    }
}

# 错误响应
{
    "jsonrpc": "2.0",
    "id": 42,
    "error": {
        "code": -32603,
        "message": "File not found: /Users/demo/readme.md"
    }
}
```

---

## 5.4 构建 MCP 服务器

### 项目结构

一个标准的 MCP 服务器项目结构：

```
my-mcp-server/
├── src/
│   ├── __init__.py
│   ├── server.py          # 主服务器代码
│   ├── tools.py           # 工具定义
│   └── resources.py       # 资源定义
├── pyproject.toml
└── README.md
```

### 基础服务器实现

```python
# src/server.py
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# 创建服务器实例
server = Server("my-filesystem-server")

@server.list_tools()
async def list_tools() -> list[Tool]:
    """
    列出服务器提供的所有工具
    
    为什么需要这个函数？
    当客户端连接时，它需要知道服务器能做什么。
    这个函数就像服务器的"产品目录"，告诉客户端有哪些工具可用。
    """
    return [
        Tool(
            name="read_file",
            description="读取文件内容。适用于需要查看文本文件内容的场景。",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "要读取的文件路径"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="write_file",
            description="写入内容到文件。如果文件存在，会覆盖原有内容。",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "要写入的文件路径"
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入的内容"
                    }
                },
                "required": ["path", "content"]
            }
        ),
        Tool(
            name="list_directory",
            description="列出目录中的文件和文件夹",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "要列出的目录路径",
                        "default": "."
                    }
                }
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """
    执行工具调用
    
    为什么分离list_tools和call_tool？
    - list_tools：定义"有什么工具"，在连接时调用一次
    - call_tool：执行"具体某个工具"，每次调用工具时都触发
    
    这种分离的好处：
    1. 工具定义和执行逻辑分离，代码更清晰
    2. 客户端可以缓存工具列表，不需要每次调用都查询
    3. 支持工具的动态注册和注销
    """
    if name == "read_file":
        return await _read_file(arguments)
    elif name == "write_file":
        return await _write_file(arguments)
    elif name == "list_directory":
        return await _list_directory(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")

async def _read_file(arguments: dict) -> list[TextContent]:
    """读取文件的实现"""
    import aiofiles
    
    path = arguments["path"]
    
    try:
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            content = await f.read()
        return [TextContent(type="text", text=content)]
    except FileNotFoundError:
        return [TextContent(type="text", text=f"Error: File not found: {path}")]
    except PermissionError:
        return [TextContent(type="text", text=f"Error: Permission denied: {path}")]

async def _write_file(arguments: dict) -> list[TextContent]:
    """写入文件的实现"""
    import aiofiles
    import os
    
    path = arguments["path"]
    content = arguments["content"]
    
    # 确保目录存在
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(content)
    
    return [TextContent(type="text", text=f"Successfully wrote to {path}")]

async def _list_directory(arguments: dict) -> list[TextContent]:
    """列出目录的实现"""
    import os
    
    path = arguments.get("path", ".")
    
    try:
        entries = os.listdir(path)
        formatted = "\n".join(f"- {entry}" for entry in sorted(entries))
        return [TextContent(type="text", text=formatted)]
    except FileNotFoundError:
        return [TextContent(type="text", text=f"Directory not found: {path}")]
    except PermissionError:
        return [TextContent(type="text", text=f"Permission denied: {path}")]

async def main():
    """服务器入口点"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### 使用 FastMCP 简化开发

FastMCP 是一个高级封装库，可以大幅简化 MCP 服务器开发：

```python
# 使用FastMCP的简化版本
from mcp.server.fastmcp import FastMCP

# 创建FastMCP实例
mcp = FastMCP("my-demo-server")

@mcp.tool()
def calculate(operation: str, a: float, b: float) -> dict:
    """
    执行数学计算
    
    为什么使用装饰器而不是显式注册？
    装饰器是一种"声明式"编程风格：
    - 优点：代码简洁，意图清晰
    - 缺点：执行顺序依赖装饰器顺序
    
    适用于：简单工具定义
    """
    operations = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y if y != 0 else "Error: Division by zero"
    }
    
    if operation not in operations:
        return {"error": f"Unknown operation: {operation}"}
    
    result = operations[operation](a, b)
    return {"operation": operation, "a": a, "b": b, "result": result}

@mcp.resource("config://app")
def get_config() -> str:
    """提供应用配置资源"""
    return '{"version": "1.0.0", "theme": "dark"}'

# 运行服务器
if __name__ == "__main__":
    mcp.run()
```

---

## 5.5 MCP客户端开发

### 连接管理

```python
# 客户端连接示例
import asyncio
from mcp.client import ClientSession
from mcp.client.stdio import stdio_client

async def main():
    async with stdio_client() as (read, write):
        async with ClientSession(read, write) as session:
            # 1. 初始化连接
            # 握手过程让客户端和服务器交换能力信息
            await session.initialize()
            
            # 2. 列出可用工具
            tools = await session.list_tools()
            print("可用工具:", [t.name for t in tools])
            
            # 3. 调用工具
            result = await session.call_tool(
                "read_file",
                arguments={"path": "/tmp/demo.txt"}
            )
            print("文件内容:", result[0].text)

asyncio.run(main())
```

### 错误处理

```python
from mcp.exceptions import MCPError

async def safe_call_tool(session, tool_name: str, arguments: dict):
    """
    带错误处理的工具调用
    
    MCP定义了标准化的错误格式，客户端应该理解这些错误
    """
    try:
        result = await session.call_tool(tool_name, arguments)
        return {"success": True, "result": result}
    except MCPError as e:
        return {
            "success": False,
            "error": "protocol_error",
            "message": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "error": "internal_error",
            "message": str(e)
        }
```

---

## 5.6 MCP 生态与实践

### 官方 MCP 服务器

Anthropic 提供了多个官方 MCP 服务器：

| 服务器 | 用途 | 位置 |
|--------|------|------|
| filesystem | 本地文件操作 | 官方维护 |
| memory | 持久化记忆 | 官方维护 |
| sequential-thinking | 推理辅助 | 官方维护 |
| slacker | Slack 集成 | 社区维护 |

### 在 Claude Desktop 中配置 MCP

```json
// ~/.claude-desktop/mcp.json
{
    "mcpServers": {
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@anthropic/mcp-server-filesystem", "/Users/username/projects", "/Users/username/documents"]
        },
        "github": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {
                "GITHUB_TOKEN": "your-github-pat"
            }
        }
    }
}
```

---

## 5.7 MCP与工具调用的区别

这是很多开发者困惑的问题：**MCP和普通的工具调用有什么区别？**

### 本质区别

| 维度 | 普通工具调用 | MCP |
|------|------------|-----|
| **架构** | LLM → 直接调用函数 | LLM → MCP客户端 → MCP服务器 |
| **协议** | 各厂商私有格式 | 统一的开放协议 |
| **上下文** | 每次请求独立 | 支持跨请求状态 |
| **工具发现** | 手动配置 | 支持自动发现 |
| **实现语言** | 必须与LLM同语言 | 任何语言 |

### 什么时候用哪个？

**使用普通工具调用**：
- 简单场景：只需要偶尔调用一两个工具
- 单次任务：不需要跨会话保持状态
- 快速原型：想快速验证想法

**使用MCP**：
- 复杂系统：需要多个工具协同工作
- 长期助手：需要在会话之间保持记忆
- 生态建设：希望工具能被多个应用复用
- 企业应用：对标准化和安全性有要求

---

## FAQ

实际开发中，下面这几个问题最常卡住人。

### Q1：Claude Desktop 启动后看不到我配置的 MCP 服务器

先确认三件事：

1. 配置文件路径对不对。macOS 上是 `~/Library/Application Support/Claude/claude_desktop_config.json`，不是 `~/.claude-desktop/mcp.json`（本文示例为简化路径）。
2. `command` 指定的可执行文件在 PATH 里能找到。`npx` 在某些环境下需要写绝对路径，比如 `/usr/local/bin/npx`。
3. `args` 数组里没有重复键。JSON 不允许同一对象出现两个同名键，第二个会被静默覆盖，导致参数丢失。

排查方法：在 Claude Desktop 菜单里查看 Developer Logs，MCP 服务器启动失败会在这里报错。

### Q2：握手时报协议版本不匹配

MCP 客户端和服务器在 `initialize` 阶段交换 `protocolVersion`。如果客户端要求 `2024-11-05`，而服务器只支持 `2024-10-07`，握手会失败。

处理方式：

- 升级 `mcp` Python 包或 `@modelcontextprotocol/sdk` npm 包到最新版本。
- 如果服务器是你自己写的，检查 `server.create_initialization_options()` 是否传了正确的版本号。
- 协议版本是双向协商的，客户端通常会向下兼容，但不要假设新特性在旧版本上可用。

### Q3：工具调用返回 `isError: true`，但 Claude 没有重试

`isError` 只是告诉客户端"这次调用失败了"，是否重试由 Claude 自己决定。如果错误信息太模糊（比如只返回 `"Error"`），Claude 可能直接放弃。

写错误信息时尽量具体：把失败原因、可恢复建议都写进去。例如 `"File not found: /tmp/demo.txt, please check the path"` 比 `"Error"` 更有利于 Claude 自我修正。

### Q4：权限被拒绝（Permission denied）

MCP 服务器访问本地资源时，权限取决于启动它的进程。在 Claude Desktop 里，服务器以当前用户身份运行；在容器里跑时，要看容器的 user 和挂载卷的权限。

常见坑：

- macOS 上 Claude Desktop 没有"完全磁盘访问权限"，访问 `~/Documents`、`~/Desktop` 等受保护目录会失败。在"系统设置 → 隐私与安全性 → 完全磁盘访问权限"里加上 Claude。
- filesystem 服务器只允许访问 `args` 里列出的目录，路径不在白名单内会被拒绝。

### Q5：stdio 传输下服务器日志去哪了

stdio 传输把 stdout/stderr 都用作协议通道，直接 `print` 会污染协议流。正确做法是用 `logging` 模块输出到 stderr，或者写到独立日志文件。FastMCP 默认会把日志发到 stderr，可以用 `tail -f` 在启动终端查看。

### Q6：多个 MCP 服务器之间会互相影响吗

不会。每个服务器在独立进程里运行，客户端为每个服务器维护独立的 `ClientSession`。工具名冲突时，客户端通常按"服务器名.工具名"做命名空间隔离，具体行为看客户端实现。

---

## 自测题

下面 6 道题用来检验你是否真的理解了 MCP。建议先自己答，再展开参考答案。

### 题 1

MCP 为什么选择 JSON-RPC 2.0 而不是直接用 HTTP REST？

<details>
<summary>参考答案</summary>

JSON-RPC 2.0 提供了统一的请求/响应/通知三种消息格式，与传输层解耦——可以跑在 stdio、SSE、WebSocket 上。REST 没有标准化的双向通知机制，也无法在一条连接上复用多个请求。MCP 需要服务器主动推送（`resources/updated`），这是 REST 不擅长的场景。
</details>

### 题 2

下面这段配置有什么问题？

```json
{
    "mcpServers": {
        "fs": {
            "command": "npx",
            "args": ["-y", "@anthropic/mcp-server-filesystem"],
            "args": ["/Users/me/projects"]
        }
    }
}
```

<details>
<summary>参考答案</summary>

`args` 出现了两次。JSON 规范不允许同一对象有重复键，第二个 `args` 会覆盖第一个，导致 `npx` 收不到 `-y` 和包名，服务器启动失败。正确写法是合并成一个数组：`"args": ["-y", "@anthropic/mcp-server-filesystem", "/Users/me/projects"]`。
</details>

### 题 3

资源（Resource）和工具（Tool）的核心区别是什么？为什么要有这个区分？

<details>
<summary>参考答案</summary>

核心区别在发起方：资源由 LLM 主动读取（读权限），工具由 LLM 调用执行（写权限）。区分的目的是让权限控制更精细——读取配置文件只需要读权限，删除文件或发送邮件需要写权限。这样即使 LLM 被诱导，也无法通过"读"操作触发副作用。
</details>

### 题 4

`list_tools` 和 `call_tool` 为什么要分成两个回调？能不能合并？

<details>
<summary>参考答案</summary>

分开是因为它们的生命周期不同：`list_tools` 在连接握手后调用一次，客户端可以缓存结果；`call_tool` 每次工具调用都触发。合并会导致客户端每次调用都要重新拉取工具列表，浪费往返。分开后还支持 `listChanged` 通知——工具增删时服务器主动告知客户端刷新缓存。
</details>

### 题 5

Claude 调用了你的 MCP 工具，但返回的 `isError: true`。Claude 没有重试就直接回复用户"操作失败"。可能的原因是什么？怎么改善？

<details>
<summary>参考答案</summary>

可能原因：错误信息太模糊（比如只返回 `"Error"`），Claude 无法判断是否可恢复。改善方式：在错误信息里写明失败原因、涉及的路径或参数、建议的下一步动作。例如 `"Permission denied: /etc/hosts, try a path under /Users/me/projects"`。信息越具体，Claude 越容易自我修正或向用户解释。
</details>

### 题 6

什么场景下不应该用 MCP，而应该直接用普通工具调用？

<details>
<summary>参考答案</summary>

三种典型场景：(1) 只需要一两个工具、且不会跨应用复用；(2) 快速原型验证，不想引入协议层复杂度；(3) 工具实现与 LLM 应用强耦合，没有多客户端需求。MCP 的价值在"一次开发，多端使用"，如果只有单一消费者，协议层的开销就不划算。
</details>

---

## 进阶路径

把本文的内容走通之后，可以按下面三个方向继续深入。

### 方向一：实现一个带状态的服务器

本文示例的工具都是无状态的。下一步可以做一个跨会话记忆服务器：用 SQLite 存储键值对，暴露 `remember`、`recall`、`forget` 三个工具，并订阅 `resources/updated` 通知客户端记忆变化。这个练习能帮你理解 MCP 的"上下文持久化"能力从何而来。

### 方向二：研究传输层切换

stdio 适合本地进程，远程场景需要 SSE 或 WebSocket。挑一个官方服务器（比如 `@modelcontextprotocol/server-github`），把它从 stdio 改造成 SSE 传输，观察握手消息和心跳机制的差异。这一步能让你分清协议层和传输层的边界。

### 方向三：参与生态建设

浏览 [MCP 服务器注册表](https://github.com/modelcontextprotocol/servers)，找一个你熟悉但没有官方实现的服务（比如 Notion、Linear、Jira），写一个社区服务器并发布。过程中你会遇到 OAuth 流程、错误码标准化、工具描述优化等真实工程问题，这是理解协议设计权衡最快的方式。

### 接下来读什么

- 继续阅读：Claude Code 与 Computer Use 专题（六）—— 了解 Claude 的计算机操控能力
- 实践项目：用 MCP 构建一个个人知识助手
- 参考资料：[MCP 官方文档](https://modelcontextprotocol.io/)

---

## 本章总结

### 要点回顾

| 知识点 | 关键内容 |
|--------|----------|
| MCP 概述 | 为什么需要 MCP、解决什么问题 |
| MCP 架构 | 客户端-服务器、资源 vs 工具 |
| 协议流程 | JSON-RPC、初始化、调用流程 |
| 服务器开发 | 定义工具、处理调用、返回结果 |
| 客户端开发 | 连接管理、错误处理 |
| MCP 生态 | 官方服务器、配置方法 |
| 选型决策 | MCP vs 普通工具调用 |

### 设计要点

| 设计思想 | 为什么重要 |
|----------|-----------|
| 开放标准 | 打破供应商锁定 |
| 关注点分离 | 架构更清晰 |
| 资源与工具分离 | 权限控制更精细 |
| 错误结果化 | 简化 LLM 处理逻辑 |
| 装饰器模式 | 开发更便捷 |

---

**文档元信息**
难度：⭐⭐⭐⭐ | 类型：专家设计 | 更新日期：2026-03-25 | 预计阅读时间：50分钟 | 字数：约6500字
