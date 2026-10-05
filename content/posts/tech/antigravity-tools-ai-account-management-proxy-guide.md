---
title: "Antigravity Tools：专业级AI账号管理与协议代理系统"
date: "2026-04-12T16:57:00+08:00"
lastmod: "2026-09-30T00:00:00+08:00"
slug: antigravity-tools-ai-account-management-proxy-guide
github_repo: "lbjlaq/Antigravity-Manager"
source_key: "gh:lbjlaq/Antigravity-Manager"
description: "31.8k+ Stars 的本地 AI 网关：把 Google/Anthropic 的 Web Session 转成标准 API，提供 OpenAI/Anthropic/Gemini 三协议互转、多账号轮换与模型路由。本文覆盖安装部署、客户端接入与合规边界。"
draft: false
categories: ["技术笔记"]
tags: ["API代理", "Claude Code", "Tauri", "Rust"]
---

# Antigravity Tools：AI 账号管理与协议代理系统

## 快速信息卡

> **GitHub 仓库**: [lbjlaq/Antigravity-Manager](https://github.com/lbjlaq/Antigravity-Manager)
>
> | 指标 | 数值 |
> |------|------|
> | ⭐ Stars | 31,828+ |
> | 🍴 Forks | 3,429+ |
> | 📜 License | CC BY-NC-SA 4.0（禁止商用） |
> | 💻 主要语言 | Rust |
> | 📅 创建时间 | 2025-11-26 |
> | 📅 最后更新 | 2026-09-30 |
> | 🔗 在线预览 | [GitHub Pages](https://lbjlaq.github.io/Antigravity-Manager/) |

---

## 学习目标

- 判断 Antigravity Tools 是否适合自己的场景：个人开发、团队使用、商业用途各有不同边界
- 跑通脚本、Homebrew、Docker 三种安装方式中的至少一种，完成首个账号接入
- 配置协议转换、模型路由与账号分发这三条核心机制
- 识别 Web Session 转 API 的服务条款风险，以及 CC BY-NC-SA 4.0 许可对使用方式的约束

---

## 目录

- [快速信息卡](#快速信息卡)
- [学习目标](#学习目标)
- [一句话判断](#一句话判断)
- [它解决什么问题](#它解决什么问题)
- [总览地图](#总览地图)
- [项目数据](#项目数据)
- [安装指南](#安装指南)
- [Docker 部署详解](#docker-部署详解)
- [核心功能详解](#核心功能详解)
- [任务流案例：一次请求如何流过系统](#任务流案例一次请求如何流过系统)
- [快速接入示例](#快速接入示例)
- [版本演进要点](#版本演进要点)
- [采用建议](#采用建议)
- [常见问题](#常见问题)
- [自测题](#自测题)
- [练习](#练习)
- [进阶路径](#进阶路径)
- [资源链接](#资源链接)
- [资料口径说明](#资料口径说明)

---

## 一句话判断

Antigravity Tools 把 Google Gemini 与 Anthropic Claude 的 Web Session 转成标准 API 接口，并在前面加了一层多账号轮换、协议转换和模型路由。它适合个人开发者在合规可控的前提下，把分散的 Web 配额聚合成一个稳定的本地 API 端点；不适合作为团队生产环境的合规通道——Web Session 转 API 本身走在厂商服务条款的灰色地带，而项目的 CC BY-NC-SA 4.0 许可又明确禁止商业使用，两条约束叠加，生产场景应当直接走官方付费 API。

## 它解决什么问题

直接使用 Claude Code、OpenCode 这类 CLI 工具时，常见两类痛点：

- **配额碎片化**：一个 Google 账号的 Gemini Pro/Flash 配额有限，多账号切换需要手动改环境变量，429 限流后只能人工换号。
- **协议不匹配**：Claude Code 走 Anthropic `/v1/messages` 协议，NextChat 走 OpenAI `/v1/chat/completions` 协议，想把同一个上游账号喂给两种客户端，需要中间做协议翻译。

Antigravity Tools 把这两件事打包进一个桌面应用：左侧管理多个 OAuth 账号，右侧暴露统一的本地 HTTP 端点，由后端负责账号轮换、协议翻译和模型路由。README 对它的定位是"本地 AI 中转站"。技术栈是 Tauri + React + Rust——Tauri 提供桌面壳，React 负责配置界面，Rust（Axum）承担网络层与协议转换。本地运行，不需要自建服务器；服务器场景可以走 Docker 无头模式。

## 总览地图

整个系统拆成三条并行机制——协议转换、账号分发、模型路由。后面的功能细节都是在这三条线上做配置或补强：

```
┌─────────────────────────────────────────────────────────────┐
│  外部应用：Claude Code / OpenCode / NextChat / Cherry Studio  │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Antigravity Axum Server (Rust)                              │
│  ├─ 中间件层：鉴权 / 限流 / 日志                              │
│  ├─ 模型路由层：ID 映射 / 正则重定向 / 分级路由                │
│  ├─ 账号分发层：轮询 / 权重 / 429 与 401 静默轮换              │
│  └─ 协议转换层：OpenAI ↔ Anthropic ↔ Gemini 三协议互转        │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  上游：Google / Anthropic API（以 Web Session 鉴权）           │
└─────────────────────────────────────────────────────────────┘
```

| 机制 | 输入 | 输出 | 关键能力 |
|------|------|------|----------|
| 协议转换 | OpenAI / Anthropic / Gemini 格式请求 | 对应上游的调用与响应回转 | 三协议互转，客户端无需改代码 |
| 账号分发 | 单次推理请求 | 选中一个可用账号 | 轮询、权重、429/401 自动切换 |
| 模型路由 | 客户端原始 model ID | 实际上游模型 | 系列化映射、正则、分级降级 |

三条线各管一件事：协议转换决定请求和响应的"外形"，账号分发决定"用谁的配额发"，模型路由决定"实际打到哪个上游模型"。

## 项目数据

| 指标 | 数值 | 说明 |
|------|------|------|
| GitHub Stars | 31,828 | 2026-09-30 GitHub API 读数 |
| Forks | 3,429 | 同上 |
| 最新稳定版 | v4.8.4（2026-09-27） | Beta 预发布滚动至 v4.8.6-beta.8 |
| 提交数 | 1,084 commits | 反映高频维护状态 |
| 开源时间 | 2025-11-26 | 仓库 created_at |
| 许可证 | CC BY-NC-SA 4.0 | 作者明确"严禁任何形式的商业行为" |
| 技术栈 | Tauri + React + Rust | 桌面壳 + 前端 + 后端 |

> 时效声明：上述数据为 2026-09-30 快照，项目发版频繁（稳定版之外每天都有 Beta 构建），请以 GitHub 仓库页面为准。

## 安装指南

### 方式一：终端一键安装（推荐）

**Linux / macOS：**

```bash
curl -fsSL https://raw.githubusercontent.com/lbjlaq/Antigravity-Manager/main/install.sh | bash
```

**Windows (PowerShell)：**

```powershell
irm https://raw.githubusercontent.com/lbjlaq/Antigravity-Manager/main/install.ps1 | iex
```

脚本会自动检测操作系统、架构和包管理器。**高级用法：**

```bash
# 安装指定版本
curl -fsSL https://raw.githubusercontent.com/lbjlaq/Antigravity-Manager/main/install.sh | bash -s -- --version 4.8.4

# 预览模式（不实际安装）
curl -fsSL https://raw.githubusercontent.com/lbjlaq/Antigravity-Manager/main/install.sh | bash -s -- --dry-run
```

**Arch Linux** 另有专用脚本：

```bash
curl -sSL https://raw.githubusercontent.com/lbjlaq/Antigravity-Manager/main/deploy/arch/install.sh | bash
```

### 方式二：Homebrew (macOS)

```bash
# 订阅 Tap
brew tap lbjlaq/antigravity-manager https://github.com/lbjlaq/Antigravity-Manager

# 安装应用
brew install --cask antigravity-tools
```

按 README 的说法，现在通过 Homebrew 安装时会在安装末尾自动清理 macOS 的隔离属性（quarantine），不需要再手动执行 `xattr` 命令。

### 方式三：Docker 部署（推荐用于 NAS / 服务器）

```bash
# 方式一: 直接运行 (推荐)
docker run -d --name antigravity-manager \
  -p 8045:8045 \
  -e API_KEY=sk-your-api-key \
  -e WEB_PASSWORD=your-login-password \
  -e ABV_MAX_BODY_SIZE=104857600 \
  -v ~/.antigravity_tools:/root/.antigravity_tools \
  lbjlaq/antigravity-manager:latest

# 方式二: Docker Compose
cd docker
docker compose up -d
```

Compose 配置默认将 JSON 日志限制为单文件 100MB、保留 3 个文件。Beta 预览版镜像独立发布 tag（如 `lbjlaq/antigravity-manager:v4.8.4-beta.1`），不会覆盖 `latest` 稳定版标签。

**访问地址：**

- 管理后台：`http://localhost:8045`
- API Base：`http://localhost:8045/v1`

**系统要求：**

- 内存：建议 1GB（最小 256MB）
- 架构：支持 x86_64 和 ARM64
- 持久化：需挂载 `/root/.antigravity_tools` 保存数据

### 方式四：手动下载

前往 [GitHub Releases](https://github.com/lbjlaq/Antigravity-Manager/releases) 下载对应系统的包：

| 平台 | 格式 |
|------|------|
| macOS | `.dmg`（支持 Apple Silicon & Intel） |
| Windows | `.msi` 或便携版 `.zip` |
| Linux | `.deb` / `.rpm` / `.AppImage` |

## Docker 部署详解

### 鉴权逻辑说明

**场景 A：仅设置 `API_KEY`**

- **Web 登录**：使用 `API_KEY` 进入后台
- **API 调用**：使用 `API_KEY` 进行 AI 请求鉴权

**场景 B：同时设置 `API_KEY` 和 `WEB_PASSWORD`（推荐）**

- **Web 登录**：必须使用 `WEB_PASSWORD`，使用 API Key 将被拒绝（更安全）
- **API 调用**：统一使用 `API_KEY`。按 README 的建议，这样可以把 API Key 分发给成员，而密码仅管理员持有

这种分离设计的好处是：Web 后台密码泄露不影响 API 调用链路，API Key 泄露也无法直接登录后台修改配置。

### 密码优先级

| 优先级 | 来源 | 说明 |
|--------|------|------|
| 第一 | 环境变量 `ABV_WEB_PASSWORD` 或 `WEB_PASSWORD` | 只要设置了就始终使用，覆盖 UI 中的任何修改 |
| 第二 | 配置文件 `gui_config.json` 的 `admin_password` 字段 | UI 的"保存"操作会更新此值 |
| 保底 | `API_KEY` | 若上述均未设置，则回退使用 |

### 旧版本升级指引

从 v4.0.1 及更早版本升级时，系统默认未设置 `WEB_PASSWORD`。可通过以下任一方式设置：

1. **Web UI 界面（推荐）**：使用原有 `API_KEY` 登录后，在 **API 反代设置** 页面手动设置并保存
2. **环境变量（Docker）**：启动容器时增加 `-e WEB_PASSWORD=您的新密码`
3. **配置文件（持久化）**：直接修改 `~/.antigravity_tools/gui_config.json`，在 `proxy` 对象中修改或添加 `"admin_password"` 字段

忘记密钥时，执行 `docker logs antigravity-manager` 查看启动日志，或在宿主机上 `grep -E '"api_key"|"admin_password"' ~/.antigravity_tools/gui_config.json`。

## 核心功能详解

### 1. 智能账号仪表盘

显示所有账号的平均剩余配额（Gemini Pro、Gemini Flash、Claude 与 Gemini 绘图），系统根据当前所有账号的配额冗余度实时推荐"最佳账号"，支持一键切换；活跃账号会显示具体配额百分比和最后同步时间。

在没有这类工具时，开发者通常需要逐个登录 Web 控制台查看配额，或者自己写脚本轮询。Antigravity 把这个查询做成了常驻 UI，省掉手动查询的往返成本。

### 2. 账号管理

**OAuth 2.0 授权（自动 / 手动）：**

添加账号时会提前生成可复制的授权链接，支持在任意浏览器完成授权；回调成功后应用会自动完成并保存（必要时可点击"我已授权，继续"手动收尾）。注意授权链接包含一次性回调端口，始终使用弹窗里生成的最新链接。

**多维度导入：**

- 单条 Token 录入
- JSON 批量导入（如来自其他工具的备份）
- 从 V1 旧版本数据库自动热迁移

**网关级视图：**

支持"列表"与"网格"双视图切换。提供 403 封禁检测，自动标注并跳过权限异常的账号。

**数据安全**：按 README 的安全声明，所有账号数据加密存储于本地 SQLite 数据库，除非开启同步功能，否则数据不离开本机。

### 3. 协议转换与中继

**全协议适配（Multi-Sink）：**

| 协议格式 | 端点 | 兼容性 |
|----------|------|--------|
| **OpenAI 格式** | `/v1/chat/completions` | 官方称兼容 99% 的现有 AI 应用（README 口径，未附测试数据） |
| **Anthropic 格式** | `/v1/messages` | 支持 Claude Code CLI 全功能（如思维链、系统提示词） |
| **Gemini 格式** | - | 支持 Google 官方 SDK 直接调用 |

**智能状态自愈：**

当请求遇到 `429 (Too Many Requests)` 或 `401 (Expire)` 时，后端会触发自动重试与静默轮换，把请求切到下一个可用账号。这一机制对 CLI 工具尤其重要——Claude Code 这类工具在长会话中可能连续触发多次推理，单账号配额耗尽时无需人工介入即可继续。

### 4. 模型路由中心

**系列化映射：**

把复杂的原始模型 ID 归类到"规格家族"。例如将所有 GPT-4 请求统一路由到 `gemini-3-pro-high`，让习惯了 OpenAI 模型名的客户端无需改代码就能切到 Gemini 上游。

**正则重定向：**

支持自定义正则表达式级模型映射，控制每一个请求的落地模型。适合在系列化映射之外做精细覆盖，比如把特定版本号的请求单独指向某个实验模型。

**智能分级路由（Tiered Routing）：**

系统根据账号类型（Ultra / Pro / Free）和配额重置频率自动排定优先级，优先消耗高速重置的账号。设计意图是让高频调用场景下的吞吐最大化——重置快的账号先用，慢的账号留作兜底。

**后台任务静默降级：**

自动识别 Claude CLI 等工具生成的后台请求（如标题生成），智能重定向至 Flash 模型，保护高级模型配额不被低价值请求消耗。

### 5. 多模态与图片生成

**画质控制：**

支持通过 OpenAI `size` 参数（如 `1024x1024`、`1920x1080`）自动计算宽高比并映射到上游模型支持的规格（21:9、16:9、4:3、1:1 等）；`quality` 参数按 `standard`/`medium`/`hd` 对应标准、2K、4K 三档分辨率。Chat API 还支持直接传 Gemini 原生的 `imageSize`（`1K`/`2K`/`4K`），或使用模型后缀（如 `gemini-3-pro-image-16-9-4k` 表示 16:9 比例 + 4K 分辨率）。

**大 Body 支持：**

后端支持高达 **100MB**（可通过 `ABV_MAX_BODY_SIZE` 配置）的 Payload，适合长上下文或图片批量上传场景。

## 任务流案例：一次请求如何流过系统

以 Claude Code 发起一次推理为例，把前面三条机制串起来：

1. **客户端发起**：Claude Code 读取环境变量 `ANTHROPIC_BASE_URL=http://127.0.0.1:8045`，向 `/v1/messages` 发送 Anthropic 格式请求，model 字段为 `claude-sonnet-4-5-thinking`。
2. **鉴权与限流**：Axum Server 中间件校验 `ANTHROPIC_API_KEY` 是否匹配 `API_KEY`，通过后进入限流检查。
3. **模型路由**：模型路由器查找 `claude-sonnet-4-5-thinking` 的映射规则。假设配置了系列化映射 → `gemini-3-pro-high`，请求的 model 字段被改写。
4. **账号分发**：账号分发器从可用账号池中按权重选中一个 Google 账号，把 OAuth Session 注入到请求头。
5. **协议转换**：Request Mapper 把 Anthropic 的 `messages` 结构转成 Gemini 上游需要的 `contents` 结构。
6. **上游调用**：请求发往 Google API。如果返回 `429`，分发器立即切换到下一个账号重试，整个过程对客户端透明。
7. **响应转换**：Response Mapper 把 Gemini 的响应结构转回 Anthropic 格式，Claude Code 收到符合预期的 JSON。

这条链路与 README 的架构图一一对应：第 3 步是模型路由，第 4 步是账号分发，第 5、7 步是协议转换。排障时也可以按这个顺序定位问题——先看请求有没有进网关（鉴权日志），再看 model 被改写成了什么（路由规则），最后看是哪个账号的配额出了状况（分发日志）。

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

OpenCode 不用手动改环境变量。进入 **API 反代** 页面 → **外部 Providers** → 点击 **OpenCode Sync** 卡片的 **Sync** 按钮，应用会自动生成 `~/.config/opencode/opencode.json`：

- 创建独立的 `antigravity-manager` provider，不覆盖 google/anthropic 原生配置
- 可选勾选 **Sync accounts**，导出 `antigravity-accounts.json`（plugin-compatible v3 格式）供 OpenCode 插件直接导入
- **Clear Config** 一键清除配置，**Restore** 从备份恢复；Windows 用户路径为 `C:\Users\<用户名>\.config\opencode\`

**快速验证：**

```bash
opencode run "test" --model antigravity-manager/claude-sonnet-4-5-thinking --variant high
```

### 接入 Kilo Code

1. **协议选择**：建议优先使用 **Gemini 协议**，Base URL 填 `http://127.0.0.1:8045`
2. **注意**：Kilo Code 在 OpenAI 模式下会叠加出 `/v1/chat/completions/responses` 这种非标准路径，导致 Antigravity 返回 404，因此务必在填入 Base URL 后选择 Gemini 模式
3. **模型映射**：Kilo Code 的模型名可能与默认设置不一致，连不上时在"模型映射"页面设置自定义映射，并查看日志文件调试

### 接入 Cherry Studio 等 OpenAI 客户端

1. 打开客户端的网络设置
2. 添加自定义 API 路径：`http://127.0.0.1:8045/v1`
3. 输入 API Key：`sk-antigravity`
4. 选择模型即可使用

### 在 Python 中调用

```python
import openai

client = openai.OpenAI(
    api_key="sk-antigravity",
    base_url="http://127.0.0.1:8045/v1"
)

response = client.chat.completions.create(
    model="gemini-3-flash",
    messages=[{"role": "user", "content": "你好，请自我介绍"}]
)
print(response.choices[0].message.content)
```

## 版本演进要点

项目从 2025 年 11 月创建至今发版密集，几个影响使用方式的版本节点：

| 版本节点 | 内容 | 对使用者的意义 |
|------|------|------------|
| v4.0.0（2026-01） | 迁移至 Tauri v2，引入原生 Headless Docker 模式与 Web 管理界面 | 服务器/NAS 部署不再依赖桌面环境，镜像自动托管前端静态资源，浏览器直接管理 |
| 后续 4.x | 多语言界面迭代至 12 种语言（简繁中文、英、日、韩、西、葡、俄、阿拉伯、土耳其、越南、缅甸），并支持跟随系统语言 | 非中文用户的配置门槛下降 |
| v4.8.4（2026-09） | Tool Call ID 全链路规范化，根治多轮工具调用 400 签名缺失报错（Fixes #3529、#3531）；根除 Claude 适配层的 Base64 误解码，支持原生 Protobuf 签名 | 在 OpenCode、Antigravity IDE 等客户端做多轮工具调用时稳定性明显提升 |

发版节奏是稳定版之外持续滚动 Beta 预发布（写作时 Beta 序列已到 v4.8.6-beta.8），追新功能可以拉 Beta 镜像，求稳用 `latest` 标签。

## 采用建议

**推荐采用的场景：**

- 个人开发者有多个 Google / Anthropic 账号，想把分散配额聚合成一个本地端点
- 主要使用 Claude Code、OpenCode 等 CLI 工具，希望 429 时无需手动换号
- 需要在 OpenAI 客户端和 Anthropic/Gemini 上游之间做协议翻译

**不建议采用的场景：**

- 团队生产环境对合规性有严格要求——Web Session 转 API 走在厂商服务条款的灰色地带，生产环境应走官方付费 API
- 商业产品或对外收费服务——项目采用 CC BY-NC-SA 4.0 许可，作者明确禁止商业使用
- 需要严格 SLA 保障的场景——Antigravity 依赖 Web Session，账号被封或会话过期会直接断服
- 对审计日志有完整要求的场景——本地代理的日志粒度通常不如官方 API

**采用顺序建议：**

1. 先用桌面版在本地跑通单账号接入，验证客户端兼容性
2. 配置模型路由表，把常用客户端的 model ID 映射到实际上游
3. 逐步添加多账号，观察轮换和 429 自愈是否符合预期
4. 若需要 7×24 小时运行，再迁移到 Docker 部署，并设置 `WEB_PASSWORD` 与 `API_KEY` 分离

**风险提示：**

把 Web Session 转成 API 调用，本质上是在绕过厂商的 API 付费通道，可能违反服务条款。个人开发调试场景风险自担；团队与商业场景请评估许可证与服务条款的双重约束，或直接走官方付费 API。

## 常见问题

### macOS 提示"应用已损坏，无法打开"？

macOS 安全机制对非 App Store 应用的常规拦截。命令行修复：

```bash
sudo xattr -rd com.apple.quarantine "/Applications/Antigravity Tools.app"
```

通过 Homebrew 安装则无需此步骤，安装程序会自动清理隔离属性。

### Linux 下窗口全黑或透明框？

在 niri、Hyprland、Sway 等 Wayland 合成器上，旧版本会因会话中存在 `DISPLAY` 而强制走 X11，导致 WebKit 界面渲染异常。先升级到包含修复的版本；临时解决：

```bash
env WEBKIT_DISABLE_DMABUF_RENDERER=1 ANTIGRAVITY_FORCE_WAYLAND=1 antigravity-tools
```

仍需走 X11 时改用 `ANTIGRAVITY_FORCE_X11=1`。

### Web Session 会过期吗？过期后怎么办？

会过期。Antigravity 会在请求失败时自动把账号标记为异常，需要重新授权刷新 Session。建议定期检查账号状态，避免使用时才发现问题。

### 支持团队多人共享一个实例吗？

技术上可以（部署 Docker 版本，多人指向同一个 API Base URL），但有三点约束：配额是共享的；Web Session 转 API 可能违反服务条款；请求日志会混杂多人数据。加上 CC BY-NC-SA 4.0 的非商业许可，团队场景建议先做合规评估。

### 如何调试协议转换问题？

设置 `RUST_LOG=debug` 启动，可查看完整请求/响应 JSON（CHANGELOG 官方口径）。也可以用 curl 直接向网关端点发请求，对比上游 API 的响应格式定位转换差异。

### 和直接购买官方 API 有什么区别？

Antigravity Tools 利用 Web Session 的配额，成本低，适合个人开发调试；官方 API 按调用量付费，有 SLA 与合规保障，适合生产环境。两者定位不同，不是替代关系。

## 自测题

1. **Antigravity Tools 的三条并行机制是什么？各自解决什么问题？**
   - 参考答案：协议转换（解决客户端协议不匹配）、账号分发（解决多账号配额管理）、模型路由（解决模型 ID 映射）。三条机制互相独立，排障时按请求流经顺序定位。

2. **为什么 Antigravity Tools 适合个人开发但不适合团队生产环境？**
   - 参考答案：个人开发场景风险可控，且能充分利用 Web 配额；团队生产环境需要合规保障和 SLA，而 Web Session 转 API 走在服务条款灰色地带，项目的 CC BY-NC-SA 4.0 许可也禁止商业使用，且 Web Session 的稳定性无法保证。

3. **让 Claude Code 通过 Antigravity 调用 Gemini 上游，需要配置哪些部分？**
   - 参考答案：1) 设置环境变量 `ANTHROPIC_BASE_URL` 指向网关；2) 模型路由表（把 `claude-sonnet-4-5-thinking` 映射到 `gemini-3-pro-high`）；3) 账号分发策略（选择哪个 Google 账号的配额）。协议转换层对 Anthropic 端点是自动的，无需手动配置。

4. **429 自愈机制的工作流程是什么？对客户端有什么影响？**
   - 参考答案：请求返回 429 时，账号分发器立即切换到下一个可用账号重试，整个过程对客户端透明——客户端收到正常响应，不知道后端换了账号。

5. **Docker 部署时，`API_KEY` 和 `WEB_PASSWORD` 的区别是什么？**
   - 参考答案：`API_KEY` 是客户端调用 API 时的鉴权凭据；`WEB_PASSWORD` 是登录管理界面的密码。两者分开设置后，API Key 泄露无法登录后台，后台密码泄露不影响 API 调用链路。

## 练习

### 练习 1：部署到本地并跑通首个请求

1. 从脚本、Homebrew、Docker 三种方式中选一种完成安装
2. 通过 OAuth 添加一个 Google 账号，观察仪表盘的配额显示
3. 按本文示例接入 Claude Code 或任意 OpenAI 客户端，发送一条测试消息
4. 在管理界面找到这次请求的日志，核对模型路由前后的 model 字段变化

**目标**：完整走一遍"安装 → 接入 → 验证"链路，并在日志里亲眼看到协议转换和模型路由的效果。

### 练习 2：配置模型路由与降级策略

1. 为常用客户端的模型名配置系列化映射
2. 添加一条正则重定向规则，把特定请求指向指定模型
3. 观察"后台任务静默降级"是否把标题生成类请求分到了 Flash 模型
4. 记录路由前后的配额消耗差异，评估策略是否达到预期

**目标**：理解三条机制中"模型路由"一条的配置空间与实际收益。

### 练习 3：做一次合规评估

假设有三个场景：个人开发调试、五人团队内部工具、对外收费的 SaaS 服务。逐场景回答"该不该用 Antigravity Tools"，依据包括：

1. Web Session 转 API 与 Google/Anthropic 服务条款的关系
2. CC BY-NC-SA 4.0 许可的非商业约束
3. SLA 与账号封禁风险对不同场景的实际影响

**目标**：把本文"采用建议"一节变成自己的判断，而不是照搬结论。

## 进阶路径

### 阶段一：单账号跑通（1 周）

安装桌面版，添加一个账号，接入一个客户端，发送测试请求。验收标准：客户端能收到响应，仪表盘配额数字有变化。

### 阶段二：多账号与路由（2-4 周）

添加 2-3 个账号，配置模型路由表，手动制造 429 场景验证自动切换。验收标准：单账号配额耗尽时客户端无感知，日志里能看到静默轮换记录。

### 阶段三：Docker 长期运行（1 个月）

迁移到 Docker 部署，配置 `WEB_PASSWORD` 与 `API_KEY` 分离，设置日志轮转与资源限制。验收标准：容器稳定运行，日志可查，重启后配置不丢。

想深入实现的话，可以从 Axum Server 的协议转换层源码读起（`claude/streaming.rs`、`claude/response.rs` 是 v4.8.4 更新日志点名的模块），对照本文任务流案例理解请求在网关内的完整路径。

## 资源链接

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | https://github.com/lbjlaq/Antigravity-Manager |
| 版本下载 | https://github.com/lbjlaq/Antigravity-Manager/releases |
| Docker 镜像 Tags | https://hub.docker.com/r/lbjlaq/antigravity-manager/tags |
| 相关项目（LSP） | https://github.com/lbjlaq/Antigravity-Tools-LS |

## 资料口径说明

1. **来源标注**：本文以 [lbjlaq/Antigravity-Manager](https://github.com/lbjlaq/Antigravity-Manager) 仓库 main 分支 README（v4.8.4）、CHANGELOG.md、v4.0.0 release notes 与 Docker 配置为准，并通过 GitHub API 核对了仓库元数据。
2. **时效性**：项目发版频繁（稳定版之外每日滚动 Beta），文中数据为 2026-09-30 核查快照：31,828 Stars、3,429 Forks、1,084 commits、最新稳定版 v4.8.4。后续请以仓库页面为准。
3. **示例数据**：文中涉及的账号、密码、API Key 等均为说明性内容，非真实凭证。
4. **功能边界**：本文描述仓库当前状态，作者可能随时调整功能、增加或下线某些特性。
5. **许可约束**：项目采用 CC BY-NC-SA 4.0 许可，仓库明确"严禁任何形式的商业行为"；同时 Web Session 转 API 可能违反上游服务条款。生产环境请使用官方 API 并遵守相关条款。
