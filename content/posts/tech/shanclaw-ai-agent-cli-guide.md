# ShanClaw：macOS 智能交互式 AI Agent CLI 指南

## 学习目标

阅读本文后，您将能够：

- ✅ 理解 ShanClaw 的核心定位与设计理念
- ✅ 掌握 ShanClaw 的本地工具集（18类 + 50+工具）
- ✅ 熟练使用命名 Agent 与独立指令/记忆机制
- ✅ 配置 MCP 客户端连接第三方服务（GitHub、Slack、数据库等）
- ✅ 使用 Daemon 模式实现跨平台消息通道（Telegram、Slack、LINE）
- ✅ 配置定时任务与心跳保持机制
- ✅ 通过 /research 和 /swarm 命令进行远程研究与多智能体协作
- ✅ 理解 ShanClaw 的技术架构与源码结构
- ✅ 完成从安装到生产环境部署的完整流程
- ✅ 开发自定义 Skills 与 MCP 工具集成

---

## 一、项目概述

### 1.1 什么是 ShanClaw

**ShanClaw**（命令名 `shan`）是由 [Kocoro-lab](https://github.com/Kocoro-lab) 开发的 **macOS 原生交互式 AI Agent CLI**，由 [Shannon Gateway](https://github.com/Kocoro-lab/Shannon) 提供 LLM 推理能力支持。

> 官网：https://shan.run

ShanClaw 不是又一个聊天机器人，而是一个**有名字、有记忆、能操控电脑的 AI Agent 运行时**。您可以创建多个命名 Agent，每个 Agent 拥有独立的指令系统、记忆存储和工具权限，通过 TUI 与之交互，也可以让 Agent 在后台运行，通过 Telegram、Slack、LINE 等渠道发送消息。

### 1.2 核心定位

| 特性 | 描述 |
|------|------|
| **交互方式** | TUI 终端界面 + Daemon 后台服务 + 消息渠道 |
| **Agent 模式** | 支持多个命名 Agent，每个 Agent 独立指令/记忆 |
| **工具生态** | 本地 macOS 工具（文件/系统/截图/自动化）+ MCP 扩展 |
| **消息通道** | 支持 Telegram、Slack、LINE 等消息平台 |
| **调度能力** | 本地定时任务（launchd） + 心跳保活 |
| **远程协作** | /research 远程研究 + /swarm 多智能体 P2P 协作 |
| **隐私优先** | 所有数据本地存储，无云端依赖 |

### 1.3 关键数据

| 指标 | 数值 |
|------|------|
| **GitHub Stars** | 74 |
| **GitHub Forks** | 25 |
| **最新版本** | (持续更新中) |
| **最新提交** | 2026-04-01：`fix: correct cache ratio formula for Anthropic token semantics` |
| **主要语言** | Go |
| **协议** | MIT |
| **依赖项** | Shannon Gateway（LLM 推理）, macOS 系统能力 |
| **源码目录** | `internal/` 下 20+ 模块 |

### 1.4 ShanClaw vs 竞品对比

| 特性 | ShanClaw | Claude Code | OpenAI Codex |
|------|----------|-------------|--------------|
| **平台** | macOS 原生 | 跨平台 | 跨平台 |
| **交互方式** | TUI + Daemon + 消息渠道 | CLI + IDE 集成 | CLI + API |
| **Agent 数量** | 多 Agent（独立记忆） | 单会话 | 单会话 |
| **MCP 支持** | ✅ 原生 | ✅ | ✅ |
| **消息通道** | Telegram/Slack/LINE | ❌ | ❌ |
| **本地工具** | macOS 深度集成 | 基础文件操作 | 基础文件操作 |
| **定时任务** | ✅ launchd | ❌ | ❌ |

---

## 二、核心概念与原理分析

### 2.1 Agent 是什么

在 ShanClaw 中，**Agent** 是一个有名字、有身份、有记忆的 AI 智能体。您可以创建多个 Agent：

```bash
# 创建 Agent
shan agent create dev "后端开发助手，擅长 Go 和系统设计"

# 切换 Agent
shan agent switch dev

# 查看所有 Agent
shan agent list
```

每个 Agent 拥有：
- **独立指令系统**（Instructions）：定义 Agent 的角色、能力范围和行为规范
- **独立记忆存储**（Session History）：跨会话积累上下文
- **独立工具权限**（Tool Permissions）：控制 Agent 能调用哪些工具

### 2.2 Shannon Gateway 架构

ShanClaw 的推理能力依赖于 **Shannon Gateway**：

```
┌─────────────────────────────────────────────────────────┐
│                    Shannon Gateway                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  OpenAI    │  │ Anthropic  │  │  Custom    │     │
│  │  Provider  │  │  Provider  │  │  LLM API   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                          │                               │
│                   ┌──────┴──────┐                       │
│                   │  LLM Router  │                       │
│                   └──────┬──────┘                       │
│                          │                               │
│  ┌──────────────────────┼──────────────────────────┐   │
│  │              ShanClaw CLI / Daemon                │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌───────┐ │   │
│  │  │  TUI    │  │ Agent  │  │  Tools  │  │ MCP   │ │   │
│  │  │ Console │  │ Engine │  │ System  │  │ Client│ │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └───────┘ │   │
│  └───────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**Gateway 的核心职责：**
- LLM 提供商路由（OpenAI/Anthropic/Gemini/本地模型等）
- Token 计数与缓存管理
- 远程工具调用（当 Agent 需要调用非本地工具时）
- Swarm 多智能体协作协调

### 2.3 本地工具系统架构

ShanClaw 的本地工具分为四大类：

#### 文件操作工具（File Operations）

| 工具名 | 功能 | 示例 |
|--------|------|------|
| `file_read` | 读取文件内容 | `file_read path=/tmp/demo.txt` |
| `file_write` | 写入文件内容 | `file_write path=/tmp/demo.txt content="hello"` |
| `file_edit` | 原地编辑文件 | `file_edit path=/tmp/demo.txt find="hello" replace="world"` |
| `glob` | 通配符文件搜索 | `glob pattern="**/*.go"` |
| `grep` | 内容搜索 | `grep path=/workspace keyword="TODO"` |
| `directory_list` | 列出目录 | `directory_list path=/workspace recursive=true` |

#### 系统与 Shell 工具（System & Shell）

| 工具名 | 功能 | 示例 |
|--------|------|------|
| `bash` | 执行 Shell 命令 | `bash command="ls -la"` |
| `system_info` | 获取系统信息 | `system_info` |
| `process` | 进程管理 | `process list` |
| `http` | HTTP 请求 | `http method=GET url="https://api.example.com"` |

#### macOS 控制工具（macOS Control）

| 工具名 | 功能 | 示例 |
|--------|------|------|
| `clipboard` | 读写剪贴板 | `clipboard read=true` |
| `notify` | 发送系统通知 | `notify title="任务完成" body="已生成报告"` |
| `applescript` | 执行 AppleScript | `applescript script="tell app \"Finder\" to open POSIX file \"/\" "` |
| `screenshot` | 屏幕截图 | `screenshot path=/tmp/screen.png` |
| `computer` | 获取电脑信息 | `computer` |
| `browser` | 浏览器自动化 | `browser url="https://github.com"` |

#### 调度与搜索工具（Schedule & Search）

| 工具名 | 功能 | 示例 |
|--------|------|------|
| `schedule_create` | 创建定时任务 | `schedule_create name="daily-report" cron="0 9 * * *"` |
| `schedule_list` | 列出定时任务 | `schedule_list` |
| `schedule_update` | 更新定时任务 | `schedule_update name="daily-report" enabled=false` |
| `schedule_remove` | 删除定时任务 | `schedule_remove name="daily-report"` |
| `session_search` | 搜索历史会话 | `session_search query="之前的 API 设计"` |

### 2.4 MCP 集成原理

MCP（Model Context Protocol）允许 ShanClaw 连接第三方服务：

```yaml
# ~/.shanclaw/config.yaml
mcp:
  servers:
    github:
      command: npx
      args: ["-y", "@modelcontextprotocol/server-github"]
      env:
        GITHUB_TOKEN: "your-token-here"
    slack:
      command: npx
      args: ["-y", "@modelcontextprotocol/server-slack"]
```

**MCP 工作流程：**
```
ShanClaw Agent → MCP Client → MCP Server → 第三方 API
                                    ↓
                              GitHub / Slack / DB / etc.
```

**ShanClaw 内置的 MCP 工具：**
- `mcp__github__create_issue` - 创建 GitHub Issue
- `mcp__github__search_repos` - 搜索代码仓库
- `mcp__slack__post_message` - 发送 Slack 消息
- 数据库 MCP 服务器连接

### 2.5 Daemon 模式与消息通道

ShanClaw 支持 **Daemon 模式**，Agent 可以在后台运行，响应来自不同消息渠道的消息：

```
┌──────────────────────────────────────────────────────────┐
│                    ShanClaw Daemon                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │  Telegram  │  │   Slack    │  │   LINE     │        │
│  │   Bot      │  │   Bot      │  │   Bot      │        │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘        │
│        └───────────────┼───────────────┘                 │
│                        ↓                                 │
│               ┌────────────────┐                        │
│               │  Message Router │                       │
│               └───────┬────────┘                        │
│                       ↓                                  │
│               ┌────────────────┐                        │
│               │  Agent Engine  │                        │
│               └───────┬────────┘                        │
│                       ↓                                  │
│              ┌─────────────────┐                        │
│              │ ShanClaw Tools  │                        │
│              └─────────────────┘                        │
└──────────────────────────────────────────────────────────┘
```

**Daemon 模式特点：**
- 持续运行，响应消息
- 支持 Telegram/Slack/LINE 多渠道同时在线
- 本地 launchd 定时任务调度
- 心跳机制保持 Agent 活跃状态

---

## 三、技术架构深度解析

### 3.1 源码目录结构

```
ShanClaw/
├── cmd/                    # CLI 入口
├── internal/
│   ├── agent/            # Agent 核心引擎
│   ├── agents/          # 多 Agent 管理
│   ├── audit/            # 审计日志
│   ├── client/          # Shannon Gateway 客户端
│   ├── config/          # 配置管理
│   ├── context/         # 会话上下文管理
│   ├── daemon/           # 后台服务
│   ├── heartbeat/        # 心跳保活
│   ├── hooks/           # 生命周期钩子
│   ├── instructions/     # Agent 指令模板
│   ├── mcp/             # MCP 客户端实现
│   ├── permissions/      # 工具权限控制
│   ├── prompt/          # Prompt 工程
│   ├── schedule/         # 定时任务调度
│   ├── session/          # 会话管理
│   ├── skills/          # Skills 系统
│   ├── tools/           # 本地工具实现
│   ├── tui/             # 终端 UI
│   ├── update/          # 自动更新
│   └── watcher/         # 文件监听
├── npm/                  # npm 发布包
├── test/                 # 测试用例
├── main.go               # 程序入口
├── go.mod               # Go 模块定义
└── install.sh           # 安装脚本
```

### 3.2 核心模块详解

#### 3.2.1 Agent Engine (`internal/agent/`)

Agent Engine 是 ShanClaw 的大脑，负责：
- 管理 Agent 的生命周期（创建、切换、销毁）
- 构建 LLM 请求的 Prompt
- 处理工具调用的循环
- 管理对话历史与上下文窗口

```go
// Agent Engine 核心流程（伪代码）
func (a *Agent) Run(ctx context.Context, input string) error {
    // 1. 加载 Agent 指令
    instructions := a.LoadInstructions()
    
    // 2. 获取对话历史
    history := a.Session.GetHistory()
    
    // 3. 构建 Prompt
    prompt := BuildPrompt(instructions, history, input)
    
    // 4. 调用 LLM
    response, err := a.client.Complete(ctx, prompt)
    if err != nil {
        return err
    }
    
    // 5. 处理工具调用
    for _, toolCall := range response.ToolCalls {
        result, err := a.tools.Execute(ctx, toolCall)
        // 将工具结果追加到对话历史
        history.AddToolResult(toolCall, result)
    }
    
    // 6. 返回最终响应
    return a.tui.Render(response.Content)
}
```

#### 3.2.2 Tools System (`internal/tools/`)

工具系统采用**接口化设计**：

```go
// 工具接口定义
type Tool interface {
    Name() string           // 工具名称
    Description() string    // 工具描述
    Schema() InputSchema    // 输入参数 schema
    Execute(ctx context.Context, input json.RawMessage) (json.RawMessage, error)
}

// 工具注册表
type ToolRegistry struct {
    tools map[string]Tool
}

func (r *ToolRegistry) Register(tool Tool) error
func (r *ToolRegistry) Get(name string) (Tool, error)
func (r *ToolRegistry) List() []Tool
```

**ShanClaw 内置的工具实现：**
- `FileTool` - 文件操作（读、写、编辑、搜索）
- `BashTool` - Shell 命令执行
- `ClipboardTool` - macOS 剪贴板
- `NotifyTool` - 系统通知
- `AppleScriptTool` - AppleScript 自动化
- `ScreenshotTool` - 屏幕截图
- `ScheduleTool` - 定时任务
- `BrowserTool` - 浏览器自动化

#### 3.2.3 MCP Client (`internal/mcp/`)

MCP 客户端负责：
- 发现并连接 MCP 服务器
- 协议握手与能力协商
- 工具调用路由
- 结果返回

```go
// MCP 客户端核心
type MCPClient struct {
    servers  map[string]*MCPConnection
    session  *MCPSession
}

func (c *MCPClient) Connect(ctx context.Context, server Config) error {
    // 1. 启动 MCP 服务器进程
    // 2. 建立 stdio 通信
    // 3. 协议握手
    // 4. 获取可用工具列表
}

func (c *MCPClient) CallTool(ctx context.Context, server, tool string, args json.RawMessage) (json.RawMessage, error)
```

#### 3.2.4 Daemon (`internal/daemon/`)

Daemon 模块提供后台服务能力：
- 接收来自 Telegram/Slack/LINE 的消息
- 消息路由到对应的 Agent
- 管理 Agent 的后台运行状态
- 处理心跳任务

### 3.3 数据流架构

```
┌─────────────────────────────────────────────────────────────────┐
│                          用户输入                                  │
│                    (TUI / 消息渠道 / CLI)                          │
└─────────────────────────┬───────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                     Message Router                                │
│              (TUI 输入 / Telegram / Slack / LINE)                 │
└─────────────────────────┬───────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Agent Selector                               │
│                  (根据消息来源选择 Agent)                          │
└─────────────────────────┬───────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Prompt Builder                               │
│        (Agent 指令 + Session History + 工具描述 + 上下文)           │
└─────────────────────────┬───────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Shannon Gateway                                │
│                    (LLM 推理调用)                                  │
└─────────────────────────┬───────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Tool Executor                                  │
│              (本地工具 / MCP 工具 / Shannon 远程工具)              │
└─────────────────────────┬───────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Response Renderer                             │
│                 (TUI 渲染 / 消息回复 / 文件输出)                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 四、安装与配置

### 4.1 环境要求

| 要求 | 详情 |
|------|------|
| **操作系统** | macOS（Linux/Windows 暂不支持） |
| **Shell** | macOS 原生工具链（clipboard、notifications、AppleScript、screencapture） |
| **LLM 推理** | Shannon Gateway（必须运行在后台） |
| **权限** | macOS Accessibility 权限（系统偏好设置 → 隐私与安全性 → 辅助功能） |
| **可选** | Chrome（浏览器自动化）、Ghostty >= 1.3.0（终端模拟器） |

### 4.2 安装方式

#### 方式一：npm 安装（推荐）

```bash
npm install -g @kocoro/shanclaw
```

#### 方式二：安装脚本

```bash
curl -fsSL https://raw.githubusercontent.com/Kocoro-lab/ShanClaw/main/install.sh | sh
```

#### 方式三：源码编译

```bash
# 克隆仓库
git clone https://github.com/Kocoro-lab/ShanClaw.git
cd ShanClaw

# 确认 Go 版本 >= 1.25
go version

# 编译安装
go build -o shan
sudo mv shan /usr/local/bin/
```

### 4.3 Shannon Gateway 配置

ShanClaw 依赖 Shannon Gateway 提供 LLM 推理能力：

```yaml
# ~/.shanclaw/config.yaml
gateway:
  url: "http://localhost:8080"  # Shannon Gateway 地址
  api_key: "your-gateway-api-key"  # Gateway API Key

# LLM 提供商配置
providers:
  openai:
    api_key: "sk-..."
    model: "gpt-4o"
  anthropic:
    api_key: "sk-ant-..."
    model: "claude-sonnet-4-20250514"
  google:
    api_key: "..."
    model: "gemini-2.0-flash"
```

### 4.4 MCP 服务器配置

```yaml
# ~/.shanclaw/config.yaml
mcp:
  servers:
    # GitHub 集成
    github:
      command: npx
      args: ["-y", "@modelcontextprotocol/server-github"]
      env:
        GITHUB_TOKEN: "${GITHUB_TOKEN}"  # 支持环境变量

    # Slack 集成
    slack:
      command: npx  
      args: ["-y", "@modelcontextprotocol/server-slack"]
      env:
        SLACK_BOT_TOKEN: "${SLACK_BOT_TOKEN}"
        SLACK_TEAM_ID: "${SLACK_TEAM_ID}"

    # 数据库（以 PostgreSQL 为例）
    postgres:
      command: npx
      args: ["-y", "@modelcontextprotocol/server-postgres"]
      env:
        DATABASE_URL: "postgresql://user:pass@localhost:5432/mydb"
```

### 4.5 权限配置

```yaml
# ~/.shanclaw/config.yaml
permissions:
  # Agent 工具权限控制
  agents:
    default:
      allow:
        - file_read
        - file_write
        - bash
        - notify
      deny:
        - screenshot
        - applescript

    dev:
      allow:
        - "*"  # 允许所有工具
```

### 4.4 首次配置向导

```bash
# 启动配置向导
shan setup

# 交互式配置流程：
# 1. 输入 Shannon Gateway 地址
# 2. 输入 API Key
# 3. 选择默认 LLM 提供商
# 4. 配置 MCP 服务器（可选）
# 5. 授予 Accessibility 权限
```

---

## 五、快速开始

### 5.1 基本使用流程

```bash
# 1. 确保 Shannon Gateway 运行中
shan gateway status

# 2. 创建第一个 Agent
shan agent create myagent "我的助手，可以帮我处理日常任务"

# 3. 启动交互式会话
shan

# 在 TUI 中输入：
# /myagent
# 你好，帮我查看当前目录下的所有 Go 文件
```

### 5.2 命令行用法

```bash
# 直接执行命令
shan run "帮我写一个 Hello World 的 Go 程序"

# 指定 Agent 执行
shan --agent myagent "帮我 review 这段代码"

# 非交互模式（CI/CD 用）
shan --yes "执行测试"
shan --agent dev "部署到生产环境"
```

### 5.3 交互式命令

在 ShanClaw TUI 中可使用以下命令：

| 命令 | 功能 | 示例 |
|------|------|------|
| `/research` | 远程深度研究 | `/research "调研 macOS 上的 AI Agent 框架"` |
| `/swarm` | 多智能体协作 | `/swarm dev:实现功能 qa:review代码` |
| `/copy` | 复制上次输出 | `/copy` |
| `/model` | 切换 LLM 模型 | `/model claude-sonnet` |
| `/config` | 编辑配置 | `/config` |
| `/sessions` | 列出历史会话 | `/sessions` |
| `/session` | 切换会话 | `/session abc123` |
| `/search` | 搜索会话内容 | `/search "之前的 API 设计"` |
| `/clear` | 清屏 | `/clear` |
| `/update` | 检查更新 | `/update` |
| `/setup` | 重新配置 | `/setup` |
| `/quit` | 退出 | `/quit` |

### 5.4 使用 /research 进行远程研究

`/research` 命令通过 Shannon Gateway 进行深度研究：

```
/research 调研 2024 年最火的 AI Agent 框架

# ShanClaw 会：
# 1. 联网搜索相关信息
# 2. 阅读相关文档和论文
# 3. 整理成结构化报告
# 4. 保存到本地供后续参考
```

### 5.5 使用 /swarm 进行多智能体协作

`/swarm` 允许同时运行多个 Agent 协作完成任务：

```bash
# 语法：/swarm <agent1>:<任务1> <agent2>:<任务2> ...

# 示例 1：开发 + Review
/swarm dev:实现用户登录功能 qa:review 代码逻辑

# 示例 2：研究 + 实现
/swarm research:调研支付系统最佳实践 dev:实现支付模块

# 示例 3：数据 + 分析
/swarm data:收集竞品数据 analyst:生成对比报告
```

---

## 六、Agent 进阶配置

### 6.1 创建有特殊能力的 Agent

```bash
# 创建代码助手
shan agent create coder \
  "资深 Go 开发者，擅长高并发系统设计，熟悉 Kubernetes" \
  --tools "file,grep,glob,bash" \
  --mcp "github,postgres"

# 创建写作助手
shan agent create writer \
  "专业技术写手，擅长写清晰的技术文档和博客" \
  --no-mcp  # 不启用 MCP

# 创建全栈助手
shan agent create fullstack \
  "全栈工程师，精通前后端开发和 DevOps" \
  --tools "*"  # 所有工具
```

### 6.2 Agent 指令模板

```markdown
<!-- ~/.shanclaw/agents/coder/instructions.md -->

# {{agent_name}}

## 角色
你是一名资深软件工程师，专注于 {{language}} 开发。

## 能力范围
- 编写高质量、可维护的代码
- 设计可扩展的系统架构
- Code Review 和性能优化
- 编写测试和文档

## 工作原则
1. 代码优先：先生成代码，再解释
2. 测试驱动：关键逻辑必须有测试
3. 文档完善：公共 API 必须有注释

## 限制
- 不生成可能有安全漏洞的代码
- 不执行破坏性的数据库操作
- 重大决策先询问用户
```

### 6.3 多 Agent 协作

```bash
# 创建 Agent 组
shan group create dev-team --agents "crawler,parser,saver"

# 并行执行任务
shan group run dev-team "抓取并解析新闻保存到数据库"
```

---

## 七、MCP 集成实战

### 7.1 GitHub MCP 集成

```yaml
# 配置 GitHub MCP
mcp:
  servers:
    github:
      command: npx
      args: ["-y", "@modelcontextprotocol/server-github"]
```

**可用工具：**

```bash
# 在 ShanClaw 中直接使用 GitHub：
shan --agent dev "帮我创建一个 Issue，标题是 '性能优化'，标签是 enhancement"
shan --agent dev "搜索最近 star 数超过 1000 的 Go 项目"
```

### 7.2 Slack MCP 集成

```yaml
mcp:
  servers:
    slack:
      command: npx
      args: ["-y", "@modelcontextprotocol/server-slack"]
      env:
        SLACK_BOT_TOKEN: "xoxb-..."
        SLACK_TEAM_ID: "T0123456789"
```

```bash
# 发送消息到 Slack 频道
shan --agent notify "发送消息到 #engineering 频道：部署完成"
```

### 7.3 数据库 MCP 集成

```yaml
mcp:
  servers:
    postgres:
      command: npx
      args: ["-y", "@modelcontextprotocol/server-postgres"]
      env:
        DATABASE_URL: "postgresql://user:pass@localhost:5432/mydb"
```

```bash
# 执行 SQL 查询
shan --agent data "查询过去一周的活跃用户数"
```

---

## 八、Daemon 模式与消息通道

### 8.1 启动 Daemon

```bash
# 启动 Daemon（后台运行）
shan daemon start

# 查看 Daemon 状态
shan daemon status

# 停止 Daemon
shan daemon stop
```

### 8.2 配置 Telegram Bot

```bash
# 1. 创建 Telegram Bot
#    在 Telegram 中找 @BotFather，发送 /newbot

# 2. 获取 Bot Token
#    BotFather 会返回类似 xoxb-... 的 token

# 3. 配置 ShanClaw
shan config set telegram.enabled true
shan config set telegram.bot_token "your-bot-token"
shan config set telegram.allowed_users "user_id_1,user_id_2"
```

### 8.3 配置 Slack App

```bash
# 1. 在 Slack API 创建 App
# 2. 配置 Bot Token 和 Signing Secret
# 3. 启用 Event API 和 Message permissions

shan config set slack.enabled true
shan config set slack.bot_token "xoxb-..."
shan config set slack.signing_secret "your-signing-secret"
```

### 8.4 Daemon 消息路由

```
Telegram 消息 (@myagent hello)
       ↓
ShanClaw Daemon
       ↓
Message Router
       ↓
查找 @myagent 对应的 Agent
       ↓
执行 Agent 处理
       ↓
通过 Telegram 返回结果
```

---

## 九、开发扩展指南

### 9.1 开发自定义工具

```go
// 示例：创建自定义天气工具
package tools

import (
    "context"
    "encoding/json"
    "net/http"
)

type WeatherTool struct{}

func (t *WeatherTool) Name() string {
    return "weather"
}

func (t *WeatherTool) Description() string {
    return "获取指定城市的天气预报"
}

func (t *WeatherTool) Schema() InputSchema {
    return InputSchema{
        Type: "object",
        Properties: map[string]SchemaProperty{
            "city": {
                Type:        "string",
                Description: "城市名称（中文或英文）",
            },
            "days": {
                Type:        "integer",
                Description: "预报天数（1-7）",
                Default:     3,
            },
        },
        Required: []string{"city"},
    }
}

func (t *WeatherTool) Execute(ctx context.Context, input json.RawMessage) (json.RawMessage, error) {
    var args struct {
        City string `json:"city"`
        Days int    `json:"days"`
    }
    if err := json.Unmarshal(input, &args); err != nil {
        return nil, err
    }
    
    // 调用天气 API
    url := fmt.Sprintf("https://api.weather.com/v3/forecast?city=%s&days=%d", args.City, args.Days)
    resp, err := http.Get(url)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    
    var result map[string]interface{}
    json.NewDecoder(resp.Body).Decode(&result)
    
    return json.Marshal(result)
}
```

### 9.2 开发自定义 MCP 服务器

```go
// 示例：简单的自定义 MCP 服务器
package main

import (
    "context"
    "github.com/modelcontextprotocol/sdk/go/server"
)

func main() {
    s := server.NewStdioServer("my-custom-server")
    
    // 注册工具
    s.RegisterTool("custom_tool", "我的自定义工具", handleCustomTool)
    
    // 运行
    s.Serve()
}

func handleCustomTool(ctx context.Context, args map[string]interface{}) (interface{}, error) {
    // 实现工具逻辑
    return map[string]string{"result": "success"}, nil
}
```

### 9.3 开发自定义 Skill

```markdown
<!-- ~/.shanclaw/skills/my-skill/SKILL.md -->

# My Skill

## 描述
这是一个自定义 Skill，用于...

## 使用场景
- 场景 1
- 场景 2

## 使用方法
```
/my-skill <参数>
```

## 实现代码
```python
def my_skill_impl(args):
    # 工具逻辑
    pass
```
```

### 9.4 发布到社区

```bash
# 1. 整理 Skill 结构
~/.shanclaw/skills/
├── my-skill/
│   ├── SKILL.md
│   ├── README.md
│   └── src/
│       └── skill.py

# 2. 创建 README（包含使用说明、截图等）

# 3. 发布到 GitHub

# 4. 提交到 ShanClaw Skills 索引
```

---

## 十、最佳实践

### 10.1 安全配置

```yaml
# ~/.shanclaw/config.yaml
security:
  # 禁止危险操作
  deny_patterns:
    - "rm -rf /"
    - "DROP TABLE *"
    - "format.*drive"
  
  # 文件访问限制
  allowed_paths:
    - "~/workspace"
    - "~/projects"
  
  # API Key 保护
  env_vars_strict: true
```

### 10.2 性能优化

```yaml
# ~/.shanclaw/config.yaml
performance:
  # 上下文窗口大小
  context_window: 128000
  
  # 历史会话保留数
  max_history: 100
  
  # 工具并行执行
  parallel_tools: true
  max_parallel: 5
  
  # 缓存配置
  cache:
    enabled: true
    ttl: 3600
```

### 10.3 生产环境部署

```bash
# 1. 使用 launchd 管理 Daemon
cat > ~/Library/LaunchAgents/com.kocoro.shanclaw.plist <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "...">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.kocoro.shanclaw</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/shan</string>
        <string>daemon</string>
        <string>start</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
EOF

# 2. 加载服务
launchctl load ~/Library/LaunchAgents/com.kocoro.shanclaw.plist

# 3. 设置开机自启
launchctl enable gui/$(id -u)/com.kocoro.shanclaw
```

### 10.4 故障排查

| 问题 | 解决方案 |
|------|----------|
| `Accessibility permission denied` | 系统偏好设置 → 隐私与安全性 → 辅助功能 → 添加 ShanClaw |
| `Gateway connection failed` | 确保 Shannon Gateway 运行在 localhost:8080 |
| `MCP tool not found` | 检查 MCP 服务器配置，确认 npx 包已安装 |
| `Agent response slow` | 减少上下文窗口大小，或切换到更快的 LLM |
| `Permission denied on file` | 检查文件权限，或在配置中添加路径到 allowed_paths |

---

## 十一、常见问题解答

### Q1: ShanClaw 和 Claude Code 有什么区别？

| 对比 | ShanClaw | Claude Code |
|------|----------|-------------|
| **交互方式** | TUI + 消息渠道 + Daemon | 纯 CLI |
| **多 Agent** | ✅ 支持多 Agent 协作 | ❌ 单会话 |
| **消息通道** | Telegram/Slack/LINE | ❌ 不支持 |
| **定时任务** | ✅ launchd 集成 | ❌ 不支持 |
| **平台** | macOS 深度集成 | 跨平台 |
| **MCP** | ✅ 原生支持 | ✅ 支持 |

### Q2: Shannon Gateway 是必须的吗？

**是的**。ShanClaw 本身不包含 LLM 推理能力，所有 LLM 调用都通过 Shannon Gateway。Gateway 负责：
- 多 LLM 提供商路由
- Token 计数与缓存
- 远程工具调用

### Q3: 如何让 ShanClaw 响应 Telegram 消息？

```bash
# 1. 配置 Telegram Bot Token
shan config set telegram.enabled true
shan config set telegram.bot_token "xoxb-your-token"

# 2. 启动 Daemon
shan daemon start

# 3. 添加 Bot 到频道/群组
# 4. @mention Bot 即可对话
```

### Q4: Agent 的记忆是如何存储的？

```bash
# 会话历史存储位置
~/.shanclaw/sessions/
├── myagent/
│   ├── history.jsonl   # 对话历史
│   ├── memory.md       # 长期记忆
│   └── context/        # 上下文文件
```

### Q5: 如何备份和恢复配置？

```bash
# 备份
tar -czvf shanclaw-backup.tar.gz ~/.shanclaw/

# 恢复
tar -xzvf shanclaw-backup.tar.gz -C ~/
```

---

## 十二、总结

ShanClaw 是一个专为 macOS 设计的**交互式 AI Agent CLI**，它不仅仅是另一个聊天机器人，而是一个**有名字、有记忆、能操控电脑的多功能 Agent 运行时**。

**核心优势：**
- 🎯 **多 Agent 系统**：每个 Agent 独立指令/记忆，可同时运行多个专业 Agent
- 🔧 **丰富工具集**：50+ 本地工具 + MCP 扩展，覆盖文件操作、系统控制、自动化
- 💬 **多渠道消息**：支持 Telegram/Slack/LINE，Agent 可以随时响应
- ⏰ **定时任务**：本地 launchd 调度，无需额外服务
- 🔒 **隐私优先**：所有数据本地存储，无云端依赖
- 🚀 **可扩展**：支持自定义工具、Skills 和 MCP 服务器

**适用场景：**
- 日常 macOS 任务自动化
- 多 Agent 协作开发
- 远程服务器管理（通过消息渠道）
- 定时报告生成与推送
- 企业内部 AI 助手

---

## 相关链接

- 🌐 官网：https://shan.run
- 🐙 GitHub：https://github.com/Kocoro-lab/ShanClaw
- 📦 npm：https://www.npmjs.com/package/@kocoro/shanclaw
- 🔗 Shannon Gateway：https://github.com/Kocoro-lab/Shannon
- 📖 Shannon 文档：https://docs.shan.run

---

*🦞 每日08:00自动更新*
