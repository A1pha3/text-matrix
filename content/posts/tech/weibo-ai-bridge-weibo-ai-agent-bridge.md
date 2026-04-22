---
title: "kangjinshan/weibo-ai-bridge：微博私信与AI Agent的桥接服务，支持Claude/Codex多Agent"
slug: weibo-ai-bridge-weibo-ai-agent-bridge
date: 2026-04-22T20:57:00+08:00
description: "weibo-ai-bridge 是用 Go 语言开发的微博私信与 AI Agent 桥接服务，通过 WebSocket 连接微博和 Claude/Codex，支持多会话、流式回复、Markdown 格式化输出。"
categories: ["技术笔记"]
tags: ["Go", "微博", "AI Agent", "WebSocket"]
---

# kangjinshan/weibo-ai-bridge：微博私信与 AI Agent 的桥接服务，支持 Claude/Codex 多 Agent

## 🎯 项目概述

**weibo-ai-bridge** 是由开发者 [kangjinshan](https://github.com/kangjinshan) 开源的 Go 语言项目，实现了**微博私信与 AI Agent 的桥接服务**。通过微博开放平台的 WebSocket API，项目能够实时接收微博私信消息，并转发给配置的 AI Agent（Claude 或 Codex）进行处理，最终将 AI 的回复以流式方式返回给微博用户。

> **GitHub**: [kangjinshan/weibo-ai-bridge](https://github.com/kangjinshan/weibo-ai-bridge)  
> **Stars**: 2 ⭐  
> **语言**: Go  
> **创建时间**: 2026-04-20  
> **最新更新**: 2026-04-22

---

## 🏗️ 核心架构

### 模块化设计

项目采用清晰的**五层模块化架构**，每层职责明确，便于扩展和维护：

```
┌─────────────────────────────────────────────────────────┐
│                    Weibo AI Bridge                       │
├─────────────────────────────────────────────────────────┤
│  Platform Layer  │  微博平台 WebSocket 接入               │
├─────────────────┼──────────────────────────────────────┤
│  Router Layer    │  消息路由与命令处理                    │
├─────────────────┼──────────────────────────────────────┤
│  Agent Layer     │  AI Agent 接口封装（Claude/Codex）     │
├─────────────────┼──────────────────────────────────────┤
│  Session Layer   │  会话状态管理与上下文持久化            │
├─────────────────┼──────────────────────────────────────┤
│  Config Layer    │  配置管理与环境变量                   │
└─────────────────────────────────────────────────────────┘
```

### 数据流

```
微博私信 → WebSocket → Platform → Router → Session Manager
                                           ↓
                                      Agent Manager → Claude/Codex
                                           ↓
                                      Router → Platform → WebSocket → 微博用户

会话持久化:
Session Manager → ~/.cc-connect/sessions/
```

---

## ⚡ 核心特性

### 1. 微博私信桥接

通过微博开放平台的 **WebSocket API** 实时接收和发送私信，支持：
- 长连接保持与自动重连
- 心跳检测与超时处理
- 消息分片发送（应对微博字数限制）

### 2. 多 Agent 支持

项目同时支持 **Claude** 和 **Codex** 两种 AI Agent：

| Agent | CLI 工具 | 状态 | 说明 |
|-------|---------|------|------|
| **Claude** | `claude` | ✅ 已安装 | 通过 Claude Code CLI 调用 |
| **Codex** | `codex` | ⏳ 未安装 | 支持本地 app-server WebSocket 协议 |

**Agent 自动发现机制**：
- 系统使用 Go 的 `exec.LookPath()` 自动检测本地 CLI 工具
- 优先使用 `claude`（`/usr/local/bin/claude`）
- 备用 `cc`（`/usr/bin/cc`）

### 3. 会话管理

| 功能 | 说明 |
|------|------|
| 多会话支持 | 同时维护多个用户会话 |
| 上下文保持 | 自动在请求中注入会话历史 |
| 会话持久化 | 存储到 `~/.cc-connect/sessions/` |
| 命令切换 | 支持 `/clear` 清除会话等命令 |

### 4. 流式回复与 Markdown 优化

**流式处理流程**：
1. 收到用户消息 → 立即回一条「正在处理中」
2. 正文按流式增量持续发送
3. 优先在句号、换行、段落边界 flush

**Markdown 友好输出**：
- Bridge 引导 Agent 使用简洁 Markdown
- 中文内容按**字符**分片（非字节），避免乱码
- 长回复使用列表、小标题与自然分段

---

## 📁 项目结构

```
weibo-ai-bridge/
├── cmd/server/          # 应用入口
│   └── main.go          # 服务主程序
├── platform/weibo/      # 微博平台适配器
│   ├── client.go        # WebSocket 连接实现
│   └── message.go       # 消息定义和解析
├── agent/               # AI Agent 集成
│   ├── agent.go        # Agent 接口定义
│   ├── manager.go       # Agent 管理器
│   ├── claude.go       # Claude Agent 实现
│   └── codex.go         # Codex Agent 实现
├── session/             # 会话管理
│   └── manager.go      # 会话管理实现
├── router/              # 消息路由
│   ├── router.go       # 路由实现
│   └── command.go      # 命令处理
├── config/              # 配置管理
│   └── config.go       # 配置实现
├── scripts/             # 部署和运维脚本
├── deploy/              # systemd 部署模板
├── build/               # 编译产物
├── bin/                 # 预编译二进制
├── config.toml          # 配置文件
├── config.example.toml  # 示例配置
├── .env.example         # 环境变量示例
├── Makefile             # 构建脚本
└── agents.md            # Agent 配置文档
```

---

## 🛠️ 快速开始

### 环境要求

- **Go 1.22+**
- **Git**
- **Claude Code** 或 **Codex CLI**（至少安装一个）

### 安装 Claude Code

```bash
# 方式1：通过 npm 安装
npm install -g @anthropic-ai/claude-code

# 方式2：源码编译安装
git clone https://github.com/anthropics/claude-code.git
cd claude-code
npm install && npm run build
sudo npm install -g .
```

### 克隆与构建

```bash
# 克隆仓库
git clone https://github.com/kangjinshan/weibo-ai-bridge.git
cd weibo-ai-bridge

# 安装依赖
make deps

# 构建项目
make build

# 编译产物位于 build/weibo-ai-bridge
```

### 配置

复制环境变量配置文件并填写微博开放平台凭证：

```bash
cp .env.example .env
```

编辑 `.env`：

```bash
# 微博平台配置（必填）
WEIBO_APP_ID=your-app-id
WEIBO_APP_SECRET=your-app-secret
WEIBO_TOKEN_URL=http://open-im.api.weibo.com/open/auth/ws_token
WEIBO_WS_URL=ws://open-im.api.weibo.com/ws/stream

# Claude 配置
export ANTHROPIC_API_KEY="sk-ant-xxxxx"
CLAUDE_ENABLED=true
```

### 运行

```bash
# 直接运行预编译二进制（Linux x86_64）
chmod +x ./server
./server

# 或运行编译产物
./build/weibo-ai-bridge
```

### systemd 部署

```bash
# 1. 修改 service 文件中的路径和用户
sudo cp deploy/weibo-ai-bridge.service /etc/systemd/system/

# 2. 重载 systemd
sudo systemctl daemon-reload

# 3. 启用并启动
sudo systemctl enable --now weibo-ai-bridge.service

# 查看状态
sudo systemctl status weibo-ai-bridge.service

# 查看日志
journalctl -u weibo-ai-bridge.service -f
```

---

## 🔧 配置详解

### 微博平台配置

| 环境变量 | 说明 | 示例 |
|---------|------|------|
| `WEIBO_APP_ID` | 微博开放平台 App ID | `1234567890` |
| `WEIBO_APP_SECRET` | 微博开放平台 App Secret | `abcdef...` |
| `WEIBO_TOKEN_URL` | 微博获取 Token 的 URL | （默认已配置） |
| `WEIBO_WS_URL` | 微博 WebSocket 地址 | （默认已配置） |
| `WEIBO_TIMEOUT` | 超时时间（秒） | `30` |

### Agent 配置

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `CLAUDE_ENABLED` | 启用 Claude Agent | `true` |
| `CODEX_API_KEY` | Codex API Key | - |
| `CODEX_MODEL` | Codex 模型（留空用 CLI 默认） | 空 |
| `CODEX_ENABLED` | 启用 Codex Agent | `false` |

### 会话配置

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `SESSION_TIMEOUT` | 会话超时（秒） | `3600` |
| `SESSION_MAX_SIZE` | 最大会话历史条数 | `1000` |

### 日志配置

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `LOG_LEVEL` | 日志级别 | `info` |
| `LOG_FORMAT` | 日志格式 | `json` |
| `LOG_OUTPUT` | 日志输出 | `stdout` |

---

## 🌐 HTTP 接口

服务启动后监听 **5533 端口**（可通过 `SERVER_PORT` 修改）：

### 健康检查

```bash
GET /health
```

返回：
```json
{
  "status": "ok",
  "service": "weibo-ai-bridge"
}
```

### 统计信息

```bash
GET /stats
```

返回会话数量、处理消息数等统计。

### SSE 调试接口

```bash
GET /chat/stream
```

用于观察内部事件流，便于联调和排查问题。

---

## 🔍 命令系统

用户在微博私信中发送命令：

| 命令 | 说明 |
|------|------|
| `/clear` | 清除当前会话历史 |
| `/switch claude` | 切换到 Claude Agent |
| `/switch codex` | 切换到 Codex Agent |
| `/help` | 显示帮助信息 |

---

## 🧪 测试与质量保障

### 运行测试

```bash
# 运行所有测试
make test

# 生成覆盖率报告
make test-coverage

# 查看详细测试输出
go test -v ./...
```

### 代码质量

```bash
# 格式化代码
make fmt

# 代码检查
make lint

# 清理构建产物
make clean
```

---

## 🐛 常见问题

### WebSocket 连接断开

**症状**：频繁出现连接断开和重连

**解决方法**：
1. 检查网络稳定性
2. 检查 Token 是否过期（微博 Token 有时效性）
3. 增加心跳间隔
4. 检查微博 API 调用限制

### 性能问题

**解决方法**：
1. 查看统计信息：`curl http://localhost:5533/stats`
2. 清理过期会话：发送 `/clear` 命令
3. 调整 `session.max_size` 配置
4. 增加服务器资源

### 依赖问题

```bash
# 清理并重新下载依赖
make clean
make deps
go mod tidy
```

---

## 🔮 开发扩展

### 添加新的 AI Agent

1. 在 `agent/` 目录创建新文件，实现 `Agent` 接口：

```go
type Agent interface {
    Name() string
    Process(ctx context.Context, sessionID string, message string) error
    StreamResponse(ctx context.Context, sessionID string, callback func(delta string)) error
}
```

2. 在 `agent/manager.go` 中注册新 Agent
3. 在配置中添加新 Agent 的配置项
4. 编写测试用例

### 接口设计

```
微博私信 → WebSocket → Platform (platform/weibo/client.go)
                                         ↓
                              Router (router/router.go)
                                         ↓
                              Session Manager (session/manager.go)
                                         ↓
                              Agent Manager (agent/manager.go)
                                         ↓
                              Claude/Codex Agent
```

---

## 📚 相关资源

| 资源 | 链接 |
|------|------|
| GitHub | [kangjinshan/weibo-ai-bridge](https://github.com/kangjinshan/weibo-ai-bridge) |
| Claude Code | [anthropics/claude-code](https://github.com/anthropics/claude-code) |
| Codex CLI | [codex-cli/codex](https://github.com/codex-cli/codex) |
| 微博开放平台 | [open.weibo.com](https://open.weibo.com/) |

---

*🦞 weibo-ai-bridge：让微博私信遇见 AI Agent，开启智能对话新时代。*