---
title: "Antigravity Tools：专业级AI账号管理与协议代理系统"
date: "2026-04-12T16:57:00+08:00"
slug: antigravity-tools-ai-account-management-proxy-guide
description: "28.1k Stars专业级AI账号管理与协议代理系统，支持OAuth 2.0授权、协议转换（OpenAI/Anthropic/Gemini）、智能模型路由、Docker部署，一站式解决多账号配额管理问题。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "API代理", "账号管理", "Claude Code", "Tauri", "Rust"]
---

# Antigravity Tools：AI 账号管理与协议代理系统

## 一句话判断

Antigravity Tools 把 Google Gemini 与 Anthropic Claude 的 Web Session 转成标准 API 接口，并在前面加了一层多账号轮换、协议转换和模型路由。它适合个人开发者在合规可控的前提下，把分散的 Web 配额聚合成一个稳定的本地 API 端点；不适合作为团队生产环境的合规通道，因为 Web Session 转 API 本身就走在厂商服务条款的灰色地带。

## 它解决什么问题

直接使用 Claude Code、OpenCode 这类 CLI 工具时，常见两类痛点：

- **配额碎片化**：一个 Google 账号的 Gemini Pro/Flash 配额有限，多账号切换需要手动改环境变量，429 限流后只能人工换号。
- **协议不匹配**：Claude Code 走 Anthropic `/v1/messages` 协议，NextChat 走 OpenAI `/v1/chat/completions` 协议，想把同一个上游账号喂给两种客户端，需要中间做协议翻译。

Antigravity Tools 把这两件事打包到一个桌面应用里：左侧管理多个 OAuth 账号，右侧暴露统一的本地 HTTP 端点，由后端负责账号轮换、协议翻译和模型路由。技术栈是 Tauri + React + Rust——Tauri 提供桌面壳，React 负责配置界面，Rust（Axum）承担高性能网络层与协议转换。本地运行，不需要自建服务器。

## 总览地图

整个系统拆成三条并行机制——协议转换、账号分发、模型路由。后面所有功能细节都是在这三条线上做配置或补强：

```
┌─────────────────────────────────────────────────────────────┐
│  外部应用：Claude Code / NextChat / Kilo Code / Cherry Studio │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Axum Server (Rust)                                          │
│  ├─ 中间件层：鉴权 / 限流 / 日志                              │
│  ├─ 协议转换层：OpenAI ↔ Anthropic ↔ Gemini 三协议互转        │
│  ├─ 模型路由层：ID 映射 / 正则重定向 / 分级路由                │
│  └─ 账号分发层：轮询 / 权重分配 / 429 静默轮换                 │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  上游：Google Gemini API / Anthropic API（用 Web Session 鉴权）│
└─────────────────────────────────────────────────────────────┘
```

| 机制 | 输入 | 输出 | 关键能力 |
|------|------|------|----------|
| 协议转换 | OpenAI 格式请求 | Anthropic / Gemini 上游调用 | 三协议互转，客户端无需改代码 |
| 账号分发 | 单次推理请求 | 选中一个可用账号 | 轮询、权重、429/401 自动切换 |
| 模型路由 | 客户端原始 model ID | 实际上游模型 | 系列化映射、正则、分级降级 |

三条线互相独立：协议转换决定请求/响应的"外形"，账号分发决定"用谁的配额发"，模型路由决定"实际打到哪个上游模型"。配置时按这三条线分别调整，避免混在一起理解。

## 项目数据

| 指标 | 数值 | 说明 |
|------|------|------|
| GitHub Stars | 28.1k | 截至 2026-04-12 公开数据 |
| Forks | 3.1k | 同上 |
| 最新版本 | v4.1.31 | 文章撰写时最新 release |
| 提交数 | 570+ commits | 反映活跃维护状态 |
| 技术栈 | Tauri + React + Rust | 桌面壳 + 前端 + 后端 |

> 时效声明：上述数据为本文撰写时的快照，开源项目数据会持续变化，请以 GitHub 仓库页面为准。

## 安装指南

### 方式一：终端一键安装（推荐）

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
# 安装指定版本
curl -fsSL ... | bash -s -- --version 4.1.31

# 预览模式（不实际安装）
curl -fsSL ... | bash -s -- --dry-run
```

### 方式二：Homebrew (macOS)

```bash
# 订阅 Tap
brew tap lbjlaq/antigravity-manager https://github.com/lbjlaq/Antigravity-Manager

# 安装应用
brew install --cask antigravity-tools

# 提示：遇到权限问题添加 --no-quarantine 参数
brew install --cask --no-quarantine antigravity-tools
```

### 方式三：Docker 部署（推荐用于 NAS / 服务器）

```bash
# 方式: 直接运行 (推荐)
docker run -d --name antigravity-manager \
  -p 8045:8045 \
  -e API_KEY=sk-your-api-key \
  -e WEB_PASSWORD=your-login-password \
  -e ABV_MAX_BODY_SIZE=104857600 \
  -v ~/.antigravity_tools:/root/.antigravity_tools \
  lbjlaq/antigravity-manager:latest

# 方式: Docker Compose
cd docker
docker compose up -d
```

**访问地址：**

- 管理后台：`http://localhost:8045`
- API Base：`http://localhost:8045/v1`

**系统要求：**

- 内存：建议 1GB（最小 256MB）
- 架构：支持 x86_64 和 ARM64

### 方式四：手动下载

前往 [GitHub Releases](https://github.com/lbjlaq/Antigravity-Manager/releases) 下载对应系统的包：

| 平台 | 格式 |
|------|------|
| macOS | `.dmg`（支持 Apple Silicon & Intel） |
| Windows | `.msi` 或便携版 `.zip` |
| Linux | `.deb` / `.rpm` / `.AppImage` |

## 核心功能详解

### 1. 智能账号仪表盘

显示所有账号的平均剩余配额（Gemini Pro、Gemini Flash、Claude 等），根据配额冗余度推荐当前最佳账号，支持一键切换。活跃账号显示具体配额百分比和最后同步时间。

在没有这类工具时，开发者通常需要逐个登录 Web 控制台查看配额，或者写脚本轮询。Antigravity 把这个查询做成了常驻 UI，并按"剩余配额 + 重置频率"综合排序，省去了手动查询的往返成本。

### 2. 账号管理

**OAuth 2.0 授权（自动 / 手动）：**

添加账号时会提前生成可复制的授权链接，支持在任意浏览器完成授权；回调成功后应用会自动完成并保存（必要时可点击"我已授权，继续"手动收尾）。

**多维度导入：**

- 单条 Token 录入
- JSON 批量导入（如来自其他工具的备份）
- 从 V1 旧版本数据库自动热迁移

**网关级视图：**

支持"列表"与"网格"双视图切换。提供 403 封禁检测，自动标注并跳过权限异常的账号。

### 3. 协议转换与中继

**全协议适配（Multi-Sink）：**

| 协议格式 | 端点 | 兼容性 |
|----------|------|--------|
| **OpenAI 格式** | `/v1/chat/completions` | 兼容主流 OpenAI 客户端 |
| **Anthropic 格式** | `/v1/messages` | 支持 Claude Code CLI 全功能（如思维链、系统提示词） |
| **Gemini 格式** | - | 支持 Google 官方 SDK 直接调用 |

> 说明：原文描述为"兼容 99% 的现有 AI 应用"，该比例无公开测试数据支撑，本文改为"兼容主流 OpenAI 客户端"，具体兼容性需以实际客户端测试为准。

**智能状态自愈：**

当请求遇到 `429 (Too Many Requests)` 或 `401 (Expire)` 时，后端会触发自动重试与静默轮换，把请求切到下一个可用账号。这一机制对 CLI 工具尤其重要——Claude Code 这类工具在长会话中可能连续触发多次推理，单账号配额耗尽时无需人工介入即可继续。

### 4. 模型路由中心

**系列化映射：**

把复杂的原始模型 ID 归类到"规格家族"。例如将所有 GPT-4 请求统一路由到 `gemini-3-pro-high`，让习惯了 OpenAI 模型名的客户端无需改代码就能切到 Gemini 上游。

**正则重定向：**

支持自定义正则表达式级模型映射，控制每一个请求的落地模型。适合在系列化映射之外做精细覆盖，比如把特定版本号的请求单独指向某个实验模型。

**智能分级路由（Tiered Routing）：**

系统根据账号类型（Ultra / Pro / Free）和配额重置频率自动优先级排序，优先消耗高速重置账号。设计意图是让高频调用场景下的吞吐最大化——重置快的账号先用完，慢的账号留作兜底。

**后台任务静默降级：**

自动识别 Claude CLI 等工具生成的后台请求（如标题生成），智能重定向至 Flash 模型，保护高级模型配额不被低价值请求消耗。

### 5. 多模态与 Imagen 支持

**画质控制：**

支持通过 OpenAI `size` 参数（如 `1024x1024`、`16:9`）自动映射到 Imagen 3 的相应规格。

**大 Body 支持：**

后端支持高达 **100MB**（可配置）的 Payload，适合长上下文或图片批量上传场景。

## 任务流案例：一次请求如何流过系统

以 Claude Code 发起一次推理为例，把前面三条机制串起来：

1. **客户端发起**：Claude Code 读取环境变量 `ANTHROPIC_BASE_URL=http://127.0.0.1:8045`，向 `/v1/messages` 发送 Anthropic 格式请求，model 字段为 `claude-sonnet-4`。
2. **鉴权与限流**：Axum Server 中间件校验 `ANTHROPIC_API_KEY` 是否匹配 `API_KEY`，通过后进入限流检查。
3. **协议转换**：根据端点判断这是 Anthropic 格式，Request Mapper 把 Anthropic 的 `messages` 结构转成 Gemini 上游需要的 `contents` 结构。
4. **模型路由**：模型路由器查找 `claude-sonnet-4` 的映射规则。假设配置了系列化映射 → `gemini-3-pro-high`，请求的 model 字段被改写。
5. **账号分发**：账号分发器从可用账号池中按权重选中一个 Google 账号，把 OAuth Session 注入到请求头。
6. **上游调用**：请求发往 Google Gemini API。如果返回 `429`，分发器立即切换到下一个账号重试，整个过程对客户端透明。
7. **响应转换**：Response Mapper 把 Gemini 的响应结构转回 Anthropic 格式，Claude Code 收到符合预期的 JSON。

这条链路对应前面三条机制：第 3 步是协议转换，第 4 步是模型路由，第 5、6 步是账号分发。配置时按这三条线分别调整——模型路由表决定"请求被改写成什么"，账号分发策略决定"用哪个账号发"，协议转换决定"输入输出长什么样"。

## 快速接入示例

### 接入 Claude Code CLI

```bash
# 启动 Antigravity，并在"API 反代"页面开启服务

# 在终端配置环境变量
export ANTHROPIC_API_KEY="sk-antigravity"
export ANTHROPIC_BASE_URL="http://127.0.0.1:8045"

# 启动 Claude Code
claude
```

### 接入 OpenCode

```bash
# 配置方式与 Claude Code 类似
export ANTHROPIC_API_KEY="sk-antigravity"
export ANTHROPIC_BASE_URL="http://127.0.0.1:8045"

# 启动 OpenCode
opencode
```

### 接入 Cherry Studio

1. 打开 Cherry Studio 设置
2. 添加自定义 API 路径：`http://127.0.0.1:8045/v1`
3. 输入 API Key：`sk-antigravity`
4. 选择模型即可使用

### 接入 Kilo Code

配置方式与其他工具类似，通过环境变量指定 `ANTHROPIC_BASE_URL` 即可实现多账号轮换与模型穿透。

## Docker 部署详解

### 鉴权逻辑说明

**场景 A：仅设置 `API_KEY`**

- **Web 登录**：使用 `API_KEY` 进入后台
- **API 调用**：使用 `API_KEY` 进行 AI 请求鉴权

**场景 B：同时设置 `API_KEY` 和 `WEB_PASSWORD`（推荐）**

- **Web 登录**：必须使用 `WEB_PASSWORD`，使用 API Key 将被拒绝（更安全）
- **API 调用**：统一使用 `API_KEY`

这种分离设计的好处是：Web 后台密码泄露不影响 API 调用链路，API Key 泄露也无法直接登录后台修改配置。

### 密码优先级

| 优先级 | 来源 | 说明 |
|--------|------|------|
| 第一 | 环境变量 `WEB_PASSWORD` | 只要设置了就优先使用 |
| 第二 | 配置文件 `gui_config.json` | UI 的"保存"操作会更新此值 |
| 保底 | `API_KEY` | 若上述均未设置，则回退使用 |

### 旧版本升级指引

从 v4.0.1 及更早版本升级时，系统默认未设置 `WEB_PASSWORD`。可通过以下任一方式设置：

1. **Web UI 界面（推荐）**：使用原有 `API_KEY` 登录后，在 **API 反代设置** 页面手动设置并保存
2. **环境变量（Docker）**：启动容器时增加 `-e WEB_PASSWORD=您的新密码`
3. **配置文件（持久化）**：直接修改 `~/.antigravity_tools/gui_config.json`

## 常见问题排查

### macOS 提示"应用已损坏，无法打开"？

由于 macOS 的安全机制，非 App Store 下载的应用可能会触发此提示。

**命令行修复（推荐）：**

```bash
sudo xattr -rd com.apple.quarantine "/Applications/Antigravity Tools.app"
```

**Homebrew 安装时规避：**

```bash
brew install --cask --no-quarantine antigravity-tools
```

## v4.x 新特性

根据 v4.0.0 及后续版本的更新日志：

| 特性 | 说明 | 带来的变化 |
|------|------|------------|
| 自动化 Docker buildx 工作流 | 多架构镜像构建 | x86_64 与 ARM64 镜像同步发布，NAS 用户可直接拉取 |
| 原生 Headless 架构 | 无需显示服务器即可运行 | 服务器/NAS 部署不再依赖 Xvfb 等虚拟显示方案 |
| WebAssembly 支持 | 提升前端性能 | 配置页和仪表盘的渲染开销降低 |
| 多语言界面 | 支持简体中文、English、Arabic 等 | 非中文用户的配置门槛下降 |

## 竞品对比

| 功能 | Antigravity Tools | 传统方案（手动切换 API Key） |
|------|----------------|----------|
| 多账号管理 | 统一仪表盘 + 自动轮换 | 分散管理，手动切换 |
| 协议转换 | OpenAI / Anthropic / Gemini 三协议 | 单一协议或需多个代理 |
| 429 / 401 处理 | 自动重试 + 静默轮换 | 需人工干预 |
| 配额监控 | 实时可视化 | 需手动查询各平台 |
| 部署方式 | 桌面应用 + Docker | 通常需要自建服务 |

## 适用人群

- **开发者**：需要频繁切换 AI 账号进行开发调试
- **AI 爱好者**：使用 Claude Code、OpenCode 等 CLI 工具
- **团队管理员**：需要管理多个 AI 账号配额
- **NAS / 服务器用户**：需要 Docker 部署方案
- **API 集成开发者**：需要统一接口对接多种 AI 服务

## 资源链接

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | https://github.com/lbjlaq/Antigravity-Manager |
| 最新版本下载 | https://github.com/lbjlaq/Antigravity-Manager/releases |
| 相关项目（LSP） | https://github.com/lbjlaq/Antigravity-Tools-LS |

## 采用建议

**推荐采用的场景：**

- 个人开发者有多个 Google / Anthropic 账号，想把分散配额聚合成一个本地端点
- 主要使用 Claude Code、OpenCode 等 CLI 工具，希望 429 时无需手动换号
- 需要在 OpenAI 客户端和 Anthropic 上游之间做协议翻译

**不建议采用的场景：**

- 团队生产环境对合规性有严格要求——Web Session 转 API 走在厂商服务条款的灰色地带，生产环境应走官方付费 API
- 需要严格 SLA 保障的场景——Antigravity 依赖 Web Session，账号被封或会话过期会直接断服
- 对审计日志有完整要求的场景——本地代理的日志粒度通常不如官方 API

**采用顺序建议：**

1. 先用桌面版在本地跑通单账号接入，验证客户端兼容性
2. 配置模型路由表，把常用客户端的 model ID 映射到实际上游
3. 逐步添加多账号，观察轮换和 429 自愈是否符合预期
4. 若需要 7×24 小时运行，再迁移到 Docker 部署，并设置 `WEB_PASSWORD` 与 `API_KEY` 分离

**风险提示：**

把 Web Session 转成 API 调用，本质上是在绕过厂商的 API 付费通道，可能违反服务条款。个人开发调试场景风险可控；团队生产环境建议评估合规性后再决定，或直接走官方付费 API。
