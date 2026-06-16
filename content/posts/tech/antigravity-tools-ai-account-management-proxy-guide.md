---
title: "Antigravity Tools：专业级AI账号管理与协议代理系统"
date: "2026-04-12T16:57:00+08:00"
slug: antigravity-tools-ai-account-management-proxy-guide
description: "28.1k Stars专业级AI账号管理与协议代理系统，支持OAuth 2.0授权、协议转换（OpenAI/Anthropic/Gemini）、智能模型路由、Docker部署，一站式解决多账号配额管理问题。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "API代理", "账号管理", "Claude Code", "Tauri", "Rust"]
---

Antigravity Tools：AI 账号管理与协议代理系统

---

## 项目概述

### 什么是 Antigravity Tools

**Antigravity Tools**（曾用名 Antigravity Manager）是一个桌面应用，核心功能是把 Web 端 Session（Google Gemini / Anthropic Claude）转化为标准化的 API 接口，同时管理多账号配额和协议转换。技术栈是 Tauri + React + Rust，本地运行，不需要自建服务器。

核心数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | 28.1k |
| Forks | 3.1k |
| 最新版本 | v4.1.31 |
| 提交数 | 570+ commits |
| 技术栈 | Tauri + React + Rust |

技术架构

```
外部应用: Claude Code / NextChat / Kilo Code
 ↓
Antigravity Axum Server (Rust 高性能网络层)
 ↓
中间件: 鉴权 / 限流 / 日志
 ↓
Model Router (模型路由: ID 映射 / 正则重定向 / 分级路由)
 ↓
账号分发器: 轮询 / 权重分配
 ↓
协议转换器: Request Mapper (请求转换)
 ↓
上游请求: Google Gemini API / Anthropic API
 ↓
响应转换器: Response Mapper (响应转换)
 ↓
返回给外部应用
```

---

安装指南

方式一：终端一键安装（推荐）

**Linux / macOS：**
```bash
curl -fsSL https://raw.githubusercontent.com/lbjlaq/Antigravity-Manager/v4.1.31/install.sh | bash
```

**Windows (PowerShell)：**
```powershell
irm https://raw.githubusercontent.com/lbjlaq/Antigravity-Manager/main/install.ps1 | iex
```

**高级用法：**
```bash
安装指定版本
curl -fsSL ... | bash -s -- --version 4.1.31

预览模式（不实际安装）
curl -fsSL ... | bash -s -- --dry-run
```

方式二：Homebrew (macOS)

```bash
. 订阅 Tap
brew tap lbjlaq/antigravity-manager https://github.com/lbjlaq/Antigravity-Manager

. 安装应用
brew install --cask antigravity-tools

提示：遇到权限问题添加 --no-quarantine 参数
brew install --cask --no-quarantine antigravity-tools
```

方式三：Docker 部署（推荐用于 NAS/服务器）

```bash
方式: 直接运行 (推荐)
docker run -d --name antigravity-manager \
 -p 8045:8045 \
 -e API_KEY=sk-your-api-key \
 -e WEB_PASSWORD=your-login-password \
 -e ABV_MAX_BODY_SIZE=104857600 \
 -v ~/.antigravity_tools:/root/.antigravity_tools \
 lbjlaq/antigravity-manager:latest

方式: Docker Compose
cd docker
docker compose up -d
```

**访问地址：**
- 管理后台： http://localhost:8045
- API Base: http://localhost:8045/v1

**系统要求：**
- 内存：建议 1GB（最小 256MB）
- 架构：支持 x86_64 和 ARM64

方式四：手动下载

前往 [GitHub Releases](https://github.com/lbjlaq/Antigravity-Manager/releases) 下载对应系统的包：

| 平台 | 格式 |
|------|------|
| macOS | `.dmg` (支持 Apple Silicon & Intel) |
| Windows | `.msi` 或便携版 `.zip` |
| Linux | `.deb` / `.rpm` / `.AppImage` |

---

核心功能详解

1. 智能账号仪表盘

显示所有账号的平均剩余配额（Gemini Pro、Gemini Flash、Claude 等），根据配额冗余度推荐当前最佳账号，支持一键切换。活跃账号显示具体配额百分比和最后同步时间。

2. 账号管理

**OAuth 2.0 授权（自动/手动）：**
添加账号时会提前生成可复制的授权链接，支持在任意浏览器完成授权；回调成功后应用会自动完成并保存（必要时可点击"我已授权，继续"手动收尾）。

**多维度导入：**
- 单条 Token 录入
- JSON 批量导入（如来自其他工具的备份）
- 从 V1 旧版本数据库自动热迁移

**网关级视图：**
支持"列表"与"网格"双视图切换。提供 403 封禁检测，自动标注并跳过权限异常的账号。

3. 协议转换与中继

**全协议适配 (Multi-Sink)：**

| 协议格式 | 端点 | 兼容性 |
|----------|------|--------|
| **OpenAI 格式** | `/v1/chat/completions` | 兼容 99% 的现有 AI 应用 |
| **Anthropic 格式** | `/v1/messages` | 支持 Claude Code CLI 全功能（如思维链、系统提示词） |
| **Gemini 格式** | - | 支持 Google 官方 SDK 直接调用 |

**智能状态自愈：**
当请求遇到 `429 (Too Many Requests)` 或 `401 (Expire)` 时，后端会毫秒级触发**自动重试与静默轮换**，确保业务不中断。

4. 模型路由中心

**系列化映射：**
您可以将复杂的原始模型 ID 归类到"规格家族"（如将所有 GPT-4 请求统一路由到 `gemini-3-pro-high`）。

**正则重定向：**
支持自定义正则表达式级模型映射，控制每一个请求的落地模型。

**智能分级路由 (Tiered Routing)：**
系统根据账号类型（Ultra/Pro/Free）和配额重置频率自动优先级排序，优先消耗高速重置账号，确保高频调用下的服务稳定性。

**后台任务静默降级：**
自动识别 Claude CLI 等工具生成的后台请求（如标题生成），智能重定向至 Flash 模型，保护高级模型配额不被浪费。

5. 多模态与 Imagen 支持

**画质控制：**
支持通过 OpenAI `size` 参数（如 `1024x1024`、`16:9`）自动映射到 Imagen 3 的相应规格。

**大 Body 支持：**
后端支持高达 **100MB**（可配置）的 Payload。

---

快速接入示例

接入 Claude Code CLI

```bash
. 启动 Antigravity，并在"API 反代"页面开启服务

. 在终端配置环境变量
export ANTHROPIC_API_KEY="sk-antigravity"
export ANTHROPIC_BASE_URL="http://127.0.0.1:8045"

. 启动 Claude Code
claude
```

接入 OpenCode

```bash
配置方式与 Claude Code 类似
export ANTHROPIC_API_KEY="sk-antigravity"
export ANTHROPIC_BASE_URL="http://127.0.0.1:8045"

启动 OpenCode
opencode
```

接入 Cherry Studio

1. 打开 Cherry Studio 设置
2. 添加自定义 API 路径：`http://127.0.0.1:8045/v1`
3. 输入 API Key：`sk-antigravity`
4. 选择模型即可使用

接入 Kilo Code

配置方式与其他工具类似，通过环境变量指定 `ANTHROPIC_BASE_URL` 即可实现多账号极速轮换与模型穿透。

---

Docker 部署详解

鉴权逻辑说明

**场景 A：仅设置 `API_KEY`**
- **Web 登录**：使用 `API_KEY` 进入后台
- **API 调用**：使用 `API_KEY` 进行 AI 请求鉴权

**场景 B：同时设置 `API_KEY` 和 `WEB_PASSWORD`（推荐）**
- **Web 登录**：必须使用 `WEB_PASSWORD`，使用 API Key 将被拒绝（更安全）
- **API 调用**：统一使用 `API_KEY`

密码优先级

| 优先级 | 来源 | 说明 |
|--------|------|------|
| 第一 | 环境变量 `WEB_PASSWORD` | 只要设置了就优先使用 |
| 第二 | 配置文件 `gui_config.json` | UI 的"保存"操作会更新此值 |
| 保底 | `API_KEY` | 若上述均未设置，则回退使用 |

旧版本升级指引

从 v4.0.1 及更早版本升级时，系统默认未设置 `WEB_PASSWORD`。可通过以下任一方式设置：

1. **Web UI 界面 (推荐)**：使用原有 `API_KEY` 登录后，在 **API 反代设置** 页面手动设置并保存

2. **环境变量 (Docker)**：启动容器时增加 `-e WEB_PASSWORD=您的新密码`

3. **配置文件 (持久化)**：直接修改 `~/.antigravity_tools/gui_config.json`

---

常见问题排查

macOS 提示"应用已损坏，无法打开"？

由于 macOS 的安全机制，非 App Store 下载的应用可能会触发此提示：

**命令行修复（推荐）：**
```bash
sudo xattr -rd com.apple.quarantine "/Applications/Antigravity Tools.app"
```

**Homebrew 安装时规避：**
```bash
brew install --cask --no-quarantine antigravity-tools
```

---

🆕 v.x 新特性

根据 v4.0.0 及后续版本的更新日志：

| 特性 | 说明 |
|------|------|
| 自动化 Docker buildx 工作流 | 多架构镜像构建 |
| 原生 Headless 架构 | 无需显示服务器即可运行 |
| WebAssembly 支持 | 提升前端性能 |
| 多语言界面 | 支持简体中文、English、Arabic 等 |

---

竞品对比

| 功能 | Antigravity Tools | 传统方案（手动切换 API Key） |
|------|----------------|----------|
| 多账号管理 | 统一仪表盘 + 自动轮换 | 分散管理，手动切换 |
| 协议转换 | OpenAI/Anthropic/Gemini 三协议 | 单一协议或需多个代理 |
| 429/401 处理 | 自动重试 + 静默轮换 | 需人工干预 |
| 配额监控 | 实时可视化 | 需手动查询各平台 |
| 部署方式 | 桌面应用 + Docker | 通常需要自建服务 |

---

适用人群

- **开发者**：需要频繁切换 AI 账号进行开发调试
- **AI 爱好者**：使用 Claude Code、OpenCode 等 CLI 工具
- **团队管理员**：需要管理多个 AI 账号配额
- **NAS/服务器用户**：需要 Docker 部署方案
- **API 集成开发者**：需要统一接口对接多种 AI 服务

---

资源链接

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | https://github.com/lbjlaq/Antigravity-Manager |
| 最新版本下载 | https://github.com/lbjlaq/Antigravity-Manager/releases |
| 相关项目 (LSP) | https://github.com/lbjlaq/Antigravity-Tools-LS |

---

总结

Antigravity Tools 解决的问题是：**把 Web 端 AI Session 转成标准 API 接口，同时管理多账号配额**。它的协议转换能力（OpenAI/Anthropic/Gemini 三合一）和 429 自动轮换是主要卖点。

需要注意的风险：把 Web Session 转成 API 调用，本质上是在绕过厂商的 API 付费通道，可能违反服务条款。如果你的使用场景是个人开发调试，风险可控；如果是团队生产环境，建议评估合规性后再决定。
