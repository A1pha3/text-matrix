---
title: "Claude API基础专题（五）：MCP协议深度解析"
date: 2026-03-25
slug: "claude-api-mcp-model-context-protocol"
description: "本文深度解析了MCP（Model Context Protocol）协议的设计思想、架构组成与工作流程，详细介绍了如何构建MCP服务器与客户端，并探讨了MCP与传统工具调用的区别与适用场景。"
draft: false
categories: ["技术笔记"]
tags: ["Claude", "MCP", "JSON-RPC", "Python"]
---

# Claude API基础专题（五）：MCP协议深度解析 ⭐⭐⭐⭐

> **目标读者**：希望扩展Claude能力边界的开发者
> **前置知识**：已完成第一篇《API基础》、第二篇《提示词工程》、第三篇《工具调用》、第四篇《RAG系统》
> **学习提醒**：MCP是Claude能力扩展的核心协议，建议先理解其设计思想再动手实现

---

## 章节导航

| 小节 | 主题 | 重要程度 |
|------|------|----------|
| 5.1 | MCP概述：为什么需要MCP | ⭐⭐⭐⭐⭐ |
| 5.2 | MCP架构详解 | ⭐⭐⭐⭐⭐ |
| 5.3 | MCP协议工作流程 | ⭐⭐⭐⭐⭐ |
| 5.4 | 构建MCP服务器 | ⭐⭐⭐⭐⭐ |
| 5.5 | MCP客户端开发 | ⭐⭐⭐⭐ |
| 5.6 | MCP生态与实践 | ⭐⭐⭐⭐ |
| 5.7 | MCP与工具调用的区别 | ⭐⭐⭐⭐ |

---

## 5.1 MCP概述：为什么需要MCP

### 问题的起源

要理解MCP（Model Context Protocol，模型上下文协议），我们需要先理解一个根本问题：**为什么LLM需要额外的协议来与外部工具交互？**

让我们回顾一下工具调用的发展历程：

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

原因很简单：**每个LLM提供商都想建立自己的生态锁定（vendor lock-in）**。当你用OpenAI的格式写了一套工具，你就很难迁移到Google的模型，因为需要重写所有工具定义。

这就带来了几个严重问题：

| 问题 | 影响 |
|------|------|
| **供应商锁定** | 开发者被绑定在某一LLM提供商 |
| **重复开发** | 同一个工具需要为不同提供商编写不同版本 |
| **生态割裂** | 工具开发者只愿意为流行平台开发 |
| **创新受阻** | 新入局的LLM难以快速建立工具生态 |

### MCP的诞生

MCP是由Anthropic牵头，与多个行业合作伙伴共同制定的一个**开放标准**。它的核心思想是：

> **为LLM工具调用建立一个"USB接口"标准——一次开发，到处可用。**

**为什么叫"模型上下文协议"？**

这个名字实际上揭示了MCP的本质：
- **协议（Protocol）**：一套标准化的通信规则
- **上下文（Context）**：MCP不仅仅是调用工具，它还能为LLM提供持久的上下文状态
- **模型无关（Model-agnostic）**：理论上任何LLM都可以实现MCP

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

MCP的设计遵循了几个核心原则：

**1. 开放性（Openness）**

MCP是一个开放标准，任何人都可以免费使用和实现。这与当年USB取代各种专用接口的道理一样——**标准化带来生态繁荣**。

**2. 简单性（Simplicity）**

MCP的协议设计尽量简单，降低实现门槛。一个MCP服务器可以用任何语言实现，只需要支持JSON-RPC 2.0。

**3. 可组合性（Composability）**

MCP支持模块化设计。多个MCP服务器可以并行工作，共同为LLM提供能力。这就像搭积木——你可以根据需要组合不同的服务器。

**4. 安全性（Security）**

MCP强调在安全沙箱环境中运行工具，避免LLM直接访问敏感资源。这是MCP与其他方案的显著区别。

---

## 5.2 MCP架构详解

### 整体架构

MCP采用客户端-服务器架构，包含三个核心组件：

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

- **LLM应用层**只需要理解如何与MCP客户端交互，不需要关心具体工具的实现
- **MCP客户端**负责连接管理、协议解析、请求路由等通用功能
- **MCP服务器**专注于提供特定能力（如文件系统、数据库等）

### MCP服务器类型

MCP服务器主要分为两类：

**1. 本地服务器（Local Servers）**

本地服务器直接运行在用户的机器上，访问本地资源：

| 服务器 | 用途 | 权限 |
|--------|------|------|
| filesystem | 读写本地文件 | 需要用户授权 |
| memory | 跨会话持久化记忆 | 自动获得 |
| sequential-thinking | 复杂推理辅助 | 自动获得 |
| slacker | Slack消息操作 | 需要OAuth授权 |

**2. 远程服务器（Remote Servers）**

远程服务器部署在云端，通过网络访问：

| 服务器 | 用途 | 连接方式 |
|--------|------|----------|
| github | GitHub操作 | API Token |
| google-maps | 地图服务 | API Key |
| puppeteer | 网页抓取 | 无头浏览器 |

### 资源与工具的区别

MCP中有一个重要概念：**资源（Resources）vs 工具（Tools）**

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
| 资源 | LLM主动读取 | 查看文件内容 | 读权限 |
| 工具 | LLM调用执行 | 删除文件、发送邮件 | 写权限 |

这种区分让**权限控制更精细**：读取文件只需要读权限，删除文件需要写权限。

---

## 5.3 MCP协议工作流程

### JSON-RPC基础

MCP底层使用JSON-RPC 2.0协议进行通信。JSON-RPC是一种轻量级的远程过程调用协议。

**为什么选择JSON-RPC？**

这是MCP设计中的又一个"为什么"：

1. **简单易实现**：JSON-RPC只定义了少数几种消息类型，任何语言都能轻松实现
2. **无状态友好**：适合HTTP等无状态协议
3. **广泛支持**：几乎所有编程语言都有成熟的JSON-RPC库
4. **调试友好**：基于JSON，人类可读，方便调试

### 核心消息类型

MCP定义了以下核心消息类型：

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

当LLM决定调用一个工具时，客户端会发送：

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

## 5.4 构建MCP服务器

### 项目结构

一个标准的MCP服务器项目结构：

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

### 使用FastMCP简化开发

FastMCP是一个高级封装库，可以大幅简化MCP服务器开发：

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

## 5.6 MCP生态与实践

### 官方MCP服务器

Anthropic提供了多个官方MCP服务器：

| 服务器 | 用途 | 位置 |
|--------|------|------|
| filesystem | 本地文件操作 | 官方维护 |
| memory | 持久化记忆 | 官方维护 |
| sequential-thinking | 推理辅助 | 官方维护 |
| slacker | Slack集成 | 社区维护 |

### 在Claude Desktop中配置MCP

```json
// ~/.claude-desktop/mcp.json
{
    "mcpServers": {
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@anthropic/mcp-server-filesystem"],
            "args": ["/Users/username/projects", "/Users/username/documents"]
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

## 本章总结

### 核心知识点

| 知识点 | 掌握程度 | 关键点 |
|--------|----------|--------|
| MCP概述 | ⭐⭐⭐⭐⭐ | 为什么需要MCP、解决什么问题 |
| MCP架构 | ⭐⭐⭐⭐⭐ | 客户端-服务器、资源vs工具 |
| 协议流程 | ⭐⭐⭐⭐⭐ | JSON-RPC、初始化、调用流程 |
| 服务器开发 | ⭐⭐⭐⭐⭐ | 定义工具、处理调用、返回结果 |
| 客户端开发 | ⭐⭐⭐⭐ | 连接管理、错误处理 |
| MCP生态 | ⭐⭐⭐⭐ | 官方服务器、配置方法 |
| 选型决策 | ⭐⭐⭐⭐ | MCP vs 普通工具调用 |

### 关键设计思想

| 设计思想 | 为什么重要 |
|----------|-----------|
| 开放标准 | 打破供应商锁定 |
| 关注点分离 | 架构更清晰 |
| 资源与工具分离 | 权限控制更精细 |
| 错误结果化 | 简化LLM处理逻辑 |
| 装饰器模式 | 开发更便捷 |

### 下一步

- 继续阅读：Claude Code与Computer Use专题（六）- 了解Claude的计算机操控能力
- 实践项目：用MCP构建一个个人知识助手
- 参考资料：[MCP官方文档](https://modelcontextprotocol.io/)

---

**文档元信息**
难度：⭐⭐⭐⭐ | 类型：专家设计 | 更新日期：2026-03-25 | 预计阅读时间：50分钟 | 字数：约6500字
