---
title: "CLIProxyAPI：25K Stars的AI编程工具统一API代理平台"
date: "2026-04-12T18:00:00+08:00"
slug: cliproxyapi-openai-compatible-api-proxy-guide
description: "25.2k Stars的AI编程工具统一代理平台，支持Claude Code/Gemini/Codex/Qwen/iFlow多账号轮询负载均衡、OAuth登录认证、OpenAI兼容API接口，让免费AI模型通过API调用。"
draft: false
categories: ["技术笔记"]
tags: ["AI代理", "API网关", "Claude Code", "Gemini", "OAuth", "负载均衡", "Go"]
---

# CLIProxyAPI：25K Stars的AI编程工具统一API代理平台

## 📋 学习目标

- 理解CLIProxyAPI的核心定位——统一多平台AI编程工具的API接口
- 掌握安装部署方法（Docker/二进制/源码编译）
- 理解OAuth认证流程如何简化账号管理
- 掌握多账号负载均衡配置与轮询策略
- 学会在16+主流IDE和CLI工具中接入CLIProxyAPI
- 了解基于CLIProxyAPI的生态衍生项目

---

## 📖 项目概述

### 什么是CLIProxyAPI

**CLIProxyAPI**是一个用Go语言编写的高性能代理服务器，它将多个AI编程平台的API统一包装成**OpenAI/Gemini/Claude/Codex兼容接口**，让用户无需管理API Key即可在各种AI工具中灵活切换和负载均衡。

通过本项目，您可以：
- 将**Gemini 2.5 Pro、GPT 5、Claude、Qwen**等模型的API免费额度统一管理
- 通过**OAuth登录**自动获取各平台会话权限
- 使用**多账号轮询**避免单账号配额限制
- 在任何**OpenAI兼容客户端**中使用这些模型

### 核心数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | **25.2k** |
| Forks | 4.2k |
| Watchers | 66 |
| 贡献者 | 160人 |
| 最新版本 | v6.9.24 (2026-04-12) |
| Releases | 556个 |
| 提交数 | 2,268次 |
| 许可证 | MIT |
| 开发语言 | Go 99.9% |

### 技术亮点

- **纯Go实现**：高性能、跨平台（Linux/macOS/Windows/FreeBSD）
- **多协议兼容**：OpenAI API / Gemini API / Claude API / Codex API
- **零API Key**：通过OAuth自动获取平台会话权限
- **智能路由**：多账号轮询 + 模型映射 + 自动降级
- ** Streaming支持**：支持流式和非流式响应
- **Function Calling**：完整支持工具调用
- **多模态输入**：支持文本和图像输入

---

## 🛠️ 安装部署

### 方式一：Docker部署（推荐）

```bash
# 快速启动
docker run -d \
  --name cliproxyapi \
  -p 8080:8080 \
  -v $(pwd)/config.yaml:/app/config.yaml \
  routerfor/me:6.9.24

# 使用docker-compose（推荐生产环境）
curl -fsSL https://raw.githubusercontent.com/router-for-me/CLIProxyAPI/main/docker-compose.yml
docker compose up -d
```

### 方式二：二进制安装

```bash
# macOS/Linux
curl -fsSL https://get.router-for.me | bash

# Windows (PowerShell)
irm https://get.router-for.me/win | iex

# 或手动下载最新Release
# https://github.com/router-for-me/CLIProxyAPI/releases/latest
```

### 方式三：源码编译

```bash
# 克隆仓库
git clone https://github.com/router-for-me/CLIProxyAPI.git
cd CLIProxyAPI

# 编译
go build -o cliproxyapi ./cmd

# 或使用Makefile
make build
```

### 验证安装

```bash
# 检查版本
./cliproxyapi --version

# 查看帮助
./cliproxyapi --help
```

---

## 🔐 OAuth认证配置

### 支持的平台

| 平台 | OAuth状态 | 多账号支持 |
|------|----------|------------|
| **Claude Code** | ✅ 支持 | ✅ 轮询 |
| **Gemini CLI** | ✅ 支持 | ✅ 轮询 |
| **OpenAI Codex** | ✅ 支持 | ✅ 轮询 |
| **Qwen Code** | ✅ 支持 | ✅ 轮询 |
| **iFlow** | ✅ 支持 | ✅ 轮询 |
| **Antigravity** | ✅ 支持 | ✅ 轮询 |

### OAuth登录流程

```bash
# 1. 启动代理服务
./cliproxyapi serve

# 2. 访问管理界面
# 打开浏览器访问 http://localhost:8080

# 3. 点击"添加账号" → 选择平台
# 系统会生成OAuth授权链接

# 4. 在浏览器中完成OAuth授权

# 5. 授权成功后会显示账号信息
```

### 配置示例（config.yaml）

```yaml
server:
  host: 0.0.0.0
  port: 8080

providers:
  claude:
    enabled: true
    accounts:
      - name: "账号1"
        oauth_token: "./tokens/claude_token1.json"
      - name: "账号2"
        oauth_token: "./tokens/claude_token2.json"
    load_balance: "round_robin"  # 轮询策略

  gemini:
    enabled: true
    accounts:
      - name: "主账号"
        oauth_token: "./tokens/gemini_token.json"

  codex:
    enabled: true
    accounts:
      - name: "Codex账号"
        oauth_token: "./tokens/codex_token.json"
```

---

## 🔌 API接口使用

### OpenAI兼容接口

```bash
# 设置API地址
export OPENAI_API_BASE="http://localhost:8080/v1"
export OPENAI_API_KEY="dummy"  # 任意值，代理不验证

# 使用OpenAI SDK
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Claude API接口

```bash
# Claude原生接口
curl http://localhost:8080/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: dummy" \
  -d '{
    "model": "claude-sonnet-4",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Gemini API接口

```bash
# Gemini接口
curl http://localhost:8080/v1beta/models \
  -H "Authorization: Bearer $(cat ./tokens/gemini_token.json)"

# 发送Gemini请求
curl http://localhost:8080/v1beta/models/gemini-2.5-pro:generateContent \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{"parts": [{"text": "Hello!"}]}]
  }'
```

---

## ⚖️ 负载均衡策略

### 轮询模式（Round Robin）

默认策略，多账号按顺序轮询请求：

```yaml
providers:
  claude:
    load_balance: "round_robin"
    accounts:
      - name: "账号1"
        weight: 1
      - name: "账号2"
        weight: 1
```

### 加权轮询（Weighted Round Robin）

根据账号配额比例分配权重：

```yaml
providers:
  claude:
    load_balance: "weighted_robin"
    accounts:
      - name: "高配额账号"
        weight: 3
      - name: "低配额账号"
        weight: 1
```

### 自动降级（Auto Fallback）

当主账号不可用时自动切换：

```yaml
providers:
  claude:
    fallback:
      enabled: true
      retry_count: 3
      timeout: 30s
```

---

## 🛠️ 客户端接入

### Claude Code

```bash
# 设置环境变量
export ANTHROPIC_API_KEY="dummy"
export ANTHROPIC_BASE_URL="http://localhost:8080/v1"

# 启动Claude Code
claude
```

### Cursor IDE

1. 打开Cursor → Settings → Models
2. 添加自定义API端点：`http://localhost:8080/v1`
3. API Key填写任意值
4. 选择模型即可使用

### Cline / Roo Code

```bash
# 配置API端点
export OPENAI_API_BASE="http://localhost:8080/v1"
export OPENAI_API_KEY="dummy"

# 启动工具
cline
```

### VS Code (GitHub Copilot Chat)

```json
// settings.json
{
  "github.copilot-chat.apiBaseUrl": "http://localhost:8080/v1",
  "github.copilot-chat.apiKey": "dummy"
}
```

---

## 📊 模型映射与路由

### 模型别名映射

```yaml
models:
  aliases:
    # Claude映射
    "claude-opus-4.5": "claude-sonnet-4"
    "claude-5": "claude-sonnet-4"

    # Gemini映射
    "gemini-ultra": "gemini-2.5-pro"
    "gemini-pro-2": "gemini-2.5-flash"

    # Codex映射
    "gpt-5": "gpt-4o"
```

### 智能路由规则

```yaml
routing:
  rules:
    - match: "claude-code-standard"
      provider: "claude"
      model: "claude-sonnet-4"

    - match: "gemini-fast"
      provider: "gemini"
      model: "gemini-2.5-flash"

    - match: "codex-heavy"
      provider: "codex"
      model: "gpt-4o"
```

---

## 🐳 Docker深度配置

### docker-compose.yml示例

```yaml
version: '3.8'

services:
  cliproxyapi:
    image: routerfor/me:6.9.24
    container_name: cliproxyapi
    ports:
      - "8080:8080"      # API端口
      - "8081:8081"      # 管理界面端口
    volumes:
      - ./config.yaml:/app/config.yaml
      - ./tokens:/app/tokens
      - ./logs:/app/logs
    environment:
      - TZ=Asia/Shanghai
    restart: unless-stopped
    networks:
      - cliproxy

networks:
  cliproxy:
    driver: bridge
```

### 环境变量配置

```bash
# 基础配置
SERVER_PORT=8080
MANAGEMENT_PORT=8081

# OAuth配置
OAUTH_CALLBACK_URL=https://your-domain.com/callback

# 日志配置
LOG_LEVEL=info
LOG_FORMAT=json

# 安全配置
API_KEY_REQUIRED=false
CORS_ENABLED=true
```

---

## 🔧 SDK集成

### Go SDK

```go
package main

import (
    "github.com/router-for-me/CLIProxyAPI/sdk"
)

func main() {
    // 创建客户端
    client := sdk.NewClient("http://localhost:8080")

    // 添加账号
    client.AddAccount("claude", &sdk.Account{
        Name:  "my-claude",
        Token: "./tokens/claude.json",
    })

    // 发送请求
    resp, err := client.ChatCompletion(&sdk.ChatRequest{
        Model: "claude-sonnet-4",
        Messages: []sdk.Message{
            {Role: "user", Content: "Hello!"},
        },
    })
}
```

### Python SDK

```python
from cliproxyapi import CLIPClient

client = CLIPClient(base_url="http://localhost:8080")

# 添加账号
client.add_account("claude", token_file="./tokens/claude.json")

# 发送请求
response = client.chat_completion(
    model="claude-sonnet-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response)
```

---

## 🌟 生态衍生项目

CLIProxyAPI拥有丰富的开源生态，基于它构建的项目包括：

### 桌面应用

| 项目 | 平台 | 特色功能 |
|------|------|----------|
| **Vibeproxy** | macOS | 菜单栏应用，无需API Key |
| **Quotio** | macOS | 实时配额追踪 + 智能故障转移 |
| **Zero Limit** | Windows | Tauri + React，配额监控 |
| **CodMate** | macOS | SwiftUI，Git review + 项目组织 |
| **ProxyPilot** | Windows | TUI + 系统托盘 |

### 浏览器扩展

| 项目 | 特色功能 |
|------|----------|
| **All API Hub** | 余额仪表盘 + 自动签到 + API导出 |

### CLI工具

| 项目 | 特色功能 |
|------|----------|
| **CCS** | 账号即时切换 |
| **霖君** | 跨平台桌面应用 |

### 面板管理

| 项目 | 特色功能 |
|------|----------|
| **CPA-XXX Panel** | 健康检查 + 资源监控 + systemd服务 |
| **CLIProxyAPI Dashboard** | Next.js + PostgreSQL，实时日志 |

---

## 📚 资源链接

| 资源 | 链接 |
|------|------|
| GitHub仓库 | https://github.com/router-for-me/CLIProxyAPI |
| 官方文档 | https://help.router-for.me/ |
| 最新下载 | https://github.com/router-for-me/CLIProxyAPI/releases |
| 中文文档 | README_CN.md |
| 日语文档 | README_JA.md |

### 赞助商

| 赞助商 | 服务内容 |
|--------|----------|
| **Z.ai** | GLM CODING PLAN，$10/月起 |
| **PackyCode** | Claude Code/Codex/Gemini中继，9折优惠码 |
| **AICodeMirror** | 企业级并发，38%/2%/9%官方价格 |
| **BmoPlus** | 90% OFF官方GPT订阅价格 |
| **LingtrueAPI** | 全球LLM API中继服务 |

---

## ✅ 总结

CLIProxyAPI是AI编程工具生态的**统一接入层**，其核心价值在于：

1. **零API Key**：通过OAuth直接使用各平台官方免费额度
2. **多协议兼容**：OpenAI/Gemini/Claude/Codex统一接口
3. **智能负载均衡**：多账号轮询 + 自动降级
4. **开箱即用**：Docker一键部署，支持16+主流IDE
5. **丰富生态**：60+基于CLIProxyAPI的衍生项目

无论您是个人开发者还是企业团队，CLIProxyAPI都能帮助您**更高效、更低成本**地使用AI编程工具。

🦞
