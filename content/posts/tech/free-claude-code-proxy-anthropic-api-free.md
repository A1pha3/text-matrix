---
title: "Free Claude Code：用免费终端代理释放Claude Code的全部潜力"
date: "2026-05-19T20:25:00+08:00"
slug: "free-claude-code-proxy-anthropic"
description: "Free Claude Code是一个开源代理服务器，它将Claude Code的Anthropic API流量路由到NVIDIA NIM、Kimi、OpenRouter、DeepSeek等免费或低成本提供商，让开发者无需付费即可使用Claude Code。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "Anthropic", "API代理", "免费LLM", "开源工具"]
---

## 先给判断

Free Claude Code解决的不是一个技术难题，而是**一个经济问题**：Claude Code很强，但Anthropic的API不是免费的。这个项目用一层轻量代理，让Claude Code改用免费的Anthropic兼容端点，从而绕过付费墙——同时保留Claude Code完整的客户端能力。

这是一个有明确适用边界的工具。对于已经熟悉Claude Code、但不想为每次coding session付费的开发者，它值得一看；但它不是银弹，配置复杂度与收益需要权衡。

<!--more-->

## 系统地图

```
┌─────────────────────────────────────────────────────────────────┐
│                        Claude Code 客户端                        │
│                    (终端 / VSCode / JetBrains ACP)               │
└────────────────────────────┬────────────────────────────────────┘
                             │ Anthropic Messages API
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Free Claude Code 代理服务器                     │
│              fcc-server (Uvicorn, Python 3.14)                   │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │
│  │ NVIDIA NIM  │  │   Kimi      │  │ OpenRouter  │  │ DeepSeek │ │
│  │  (免费额度)  │  │  (免费额度)  │  │ (付费/免费)  │  │ (付费)   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────────┘ │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │               Admin UI: http://127.0.0.1:8082/admin          ││
│  │           (本地配置提供商、验证连接、查看模型列表)             ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## 核心能力

### 1. 多提供商路由

项目支持10个后端：

| 提供商 | 免费额度 | 模型支持 |
|--------|---------|---------|
| NVIDIA NIM | 有免费tier | Opus, Sonnet, Haiku |
| Kimi | 有免费额度 | Moonshot系列 |
| OpenRouter | 免费+付费 | 大量开源模型 |
| DeepSeek | 付费 | DeepSeek Chat |
| LM Studio | 本地 | Llama/Mistral系 |
| llama.cpp | 本地 | 量化模型 |
| Ollama | 本地 | 主流开源模型 |
| OpenCode Zen | 待确认 | - |
| Wafer | 待确认 | - |
| Z.ai | 待确认 | - |

Per-model路由允许把不同任务发送给不同提供商——比如把复杂任务路由到Opus，把轻量任务路由到Haiku。

### 2. Claude Code模型选择器兼容

代理的`/v1/models`端点会返回所选提供商的模型列表，Claude Code可以在UI里直接选择。但注意：需要在Claude Code里开启Gateway模型发现（opt-in），这个功能才会生效。

### 3. 完整协议支持

- 流式响应（streaming）
- 工具调用（tool use）
- 推理/思考块（reasoning/thinking blocks）
- 本地请求优化（减少延迟）

### 4. 可选集成

- **Discord/Telegram bot**：远程coding session，通过聊天界面控制Claude Code
- **VSCode扩展**：本地Usage面板
- **语音笔记转录**：通过Whisper或NVIDIA NIM处理语音输入

### 5. 本地Admin UI

在`http://127.0.0.1:8082/admin`提供图形化配置界面，可以：
- 添加/配置提供商
- 验证API连接
- 查看每个提供商的健康状态

## 快速开始

### 环境要求

- Python 3.14
- uv 包管理器
- Claude Code CLI

### 安装步骤

```bash
# 1. 安装 Claude Code
npm install -g @anthropic-ai/claude-code

# 2. 安装 uv 和 Python 3.14
curl -LsSf https://astral.sh/uv/install.sh | sh
uv self update
uv python install 3.14

# 3. 获取 NVIDIA NIM API Key（或其他提供商）
# 访问 https://ngc.nvidia.com/ 注册并获取免费API Key

# 4. 安装代理
uv tool install --force git+https://github.com/Alishahryar1/free-claude-code.git

# 5. 启动代理
fcc-server
```

启动后，代理会输出Admin UI地址。

### 配置Claude Code使用代理

在Admin UI中添加提供商API Key，或手动配置环境变量指向`http://127.0.0.1:8080`即可。

## 任务流案例：一次完整的代理配置

假设你想用免费的NVIDIA NIM运行Claude Code：

```
1. 注册 NGC 账号，获取 NIM API Key
2. 启动 fcc-server
3. 浏览器打开 http://127.0.0.1:8082/admin
4. 添加 NVIDIA NIM 提供商，填入 API Key
5. 在 Admin UI 中验证连接（点击 Test）
6. 启动 Claude Code，设置 ANTHROPIC_BASE_URL=http://127.0.0.1:8080
7. 开始 coding session——请求会经过代理路由到 NIM
```

## 适用边界

**该用：**
- 想要免费使用Claude Code，同时不介意配置工作
- 有NVIDIA NIM或其他免费提供商账号
- 对本地模型（LM Studio/Ollama）有使用经验

**不该用：**
- 追求零配置开箱即用
- 对延迟敏感的生产环境任务
- 需要长期稳定支持而不愿自己维护（项目依赖个人维护）

## 技术细节

### 技术栈

- **语言**：Python 3.14
- **异步框架**：Uvicorn（ASGI）
- **包管理**：uv
- **代码质量**：Ruff（格式化）、Ty（类型检查）、Pytest（测试）

### 项目结构（简化）

```
free-claude-code/
├── fcc_server/          # 代理服务器核心
│   ├── __init__.py
│   ├── main.py           # Uvicorn 入口
│   ├── proxy.py          # 代理路由逻辑
│   └── providers/        # 各提供商适配器
├── fcc_cli/             # CLI 工具
├── admin/                # Admin UI (Web)
└── scripts/              # 安装脚本
```

## 限制与已知问题

1. **部分提供商描述未验证**：Wafer、Z.ai、OpenCode Zen的说明在README中没有完整验证，实际可用性需要实测
2. **模型选择器需要opt-in**：Claude Code的Gateway发现功能默认关闭，需要手动开启
3. **维护状态**：项目由个人维护，长期维护存在不确定性
4. **Windows支持**：Windows用户需要PowerShell安装uv，配置过程比macOS/Linux更复杂

## 结论

Free Claude Code是一个有明确价值的开源工具：它让Claude Code的强大能力对不想付费的开发者开放，同时保留了完整的客户端体验。适用边界清晰：愿意花时间配置、有免费API额度的用户会从中受益；追求开箱即用或需要生产级稳定性的用户应该考虑付费方案或商业替代品。

项目代码质量较高（类型检查、测试覆盖、CI流程），但维护者只有一个，长期维护存在风险。如果这个项目对你有价值，建议参与贡献或关注其长期维护状态。

---

**仓库信息**：https://github.com/Alishahryar1/free-claude-code | Stars: 25,958 | License: MIT | 语言: Python