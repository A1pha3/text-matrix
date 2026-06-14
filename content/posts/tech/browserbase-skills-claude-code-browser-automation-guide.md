---
title: "Browserbase Skills：让 Claude Code 拥有浏览器自动化能力"
date: "2026-05-05T10:03:56+08:00"
slug: browserbase-skills-claude-code-browser-automation-guide
description: "Browserbase Skills是为Claude Code打造的浏览器自动化技能框架，支持远程Browserbase会话、反爬虫Stealth模式、CAPTCHA解决和住宅代理轮换。本文详细解析其10个核心技能的架构、安装配置与实战用法。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Claude Code", "浏览器自动化", "Browserbase", "开源"]
---

# Browserbase Skills：让 Claude Code 拥有浏览器自动化能力

## 📋 本文覆盖内容

- Browserbase Skills 的定位——将浏览器自动化能力注入 Claude Code
- 10 个技能的用途与协作关系
- 在 Claude Code 中安装和配置 Browserbase Skills
- 本地模式与远程 Browserbase 云端模式的切换方式
- site-debugger 和 browser-trace 的调试工作流
- cookie-sync 和 ui-test 在实际场景中的应用

---

## 📖 项目概述

### 什么是 Browserbase Skills

**Browserbase Skills** 是一个开源的 **Claude Agent SDK**，通过官方 `bb` CLI 和一组结构化技能，让 Claude Code 能够与浏览器进行深度交互。与传统的无头浏览器方案不同，Browserbase Skills 构建在 Browserbase 云服务之上，提供了反爬虫规避、CAPTCHA 自动解决、住宅代理轮换等开箱即用的能力。

### 核心数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | 2,131 |
| Forks | 134 |
| 主要语言 | JavaScript |
| 创建时间 | 2025-10-12 |
| 最新更新 | 2026-04-30 |
| 许可证 | 尚未声明（私有仓库 fork 来的公开项目） |

### 解决的问题

大多数 AI Agent 在处理网页操作时只能完成简单的页面读取，无法应对：

- **反爬虫机制**：Cloudflare、Distil Networks 等平台的 Bot 检测
- **需要登录态的操作**：Cookie、Session 维护
- **复杂交互**：CAPTCHA、多步表单、无头浏览器无法渲染的内容
- **性能与资源**：本地浏览器占用大量内存，远程云端浏览器按需调用

Browserbase Skills 通过 Browserbase 云端浏览器基础设施解决了以上问题，同时保留了本地开发的便捷性。

---

## 🏗️ 技术架构

### 整体架构

```
Browserbase Skills 架构图

┌─────────────────────────────────────────────────────────┐
│                    Claude Code                          │
│              (通过自然语言操控浏览器)                     │
└─────────────────────┬───────────────────────────────────┘
                      │ Skill 调用
┌─────────────────────▼───────────────────────────────────┐
│              Browserbase Skills                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │  skills/                                          │    │
│  │  ├── browser        核心浏览器自动化                │    │
│  │  ├── browserbase-cli  bb CLI 工具                │    │
│  │  ├── functions     云端无服务器自动化              │    │
│  │  ├── site-debugger 站点调试与 Bot 检测诊断        │    │
│  │  ├── browser-trace  CDP 协议全量追踪              │    │
│  │  ├── bb-usage      用量统计与成本预测             │    │
│  │  ├── cookie-sync   Cookie 同步                    │    │
│  │  ├── fetch         无浏览器静态抓取                │    │
│  │  ├── search        网页搜索                       │    │
│  │  └── ui-test       AI 对抗式 UI 测试             │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────┬───────────────────────────────────┘
                      │ bb CLI / API
        ┌─────────────┴─────────────┐
        ▼                           ▼
┌───────────────┐         ┌──────────────────────┐
│  本地浏览器    │         │  Browserbase 云端     │
│  (Chrome)     │         │  (远程浏览器实例)       │
└───────────────┘         │  - Stealth 模式       │
                          │  - 住宅代理            │
                          │  - CAPTCHA 解决       │
                          │  - 无头/有头          │
                          └──────────────────────┘
```

### 两种运行环境

Browserbase Skills 支持两种运行模式，Claude 会根据指令自动选择：

| 模式 | 触发方式 | 适用场景 |
|------|---------|---------|
| **本地模式** | `browse env local` | 开发调试、轻量任务、已有 Chrome 环境 |
| **云端模式** | 默认/远程 | 反爬虫网站、需要代理、需要 Stealth 能力 |

本地模式现在默认启动干净的隔离浏览器，不会复用已有的 Chrome 状态。如果需要复用本地登录态，使用 `browse env local --auto-connect`。

---

## 🔧 安装与配置

### 前置条件

- Node.js 18+
- Chrome 浏览器（本地模式必需）
- Browserbase 账户（云端模式必需，免费额度有限）

### 安装 Skills

通过 npm 安装到主流 Coding Agent：

```bash
npx skills add browserbase/skills
```

### Claude Code 专用安装

```bash
# 添加 marketplace 源
/plugin marketplace add browserbase/skills

# 安装 browse 插件
/plugin install browse@browserbase

# 重启 Claude Code 使配置生效
```

### 手动安装

如果偏好手动配置：

1. 在 Claude Code 中输入 `/plugin`
2. 选择选项 `3. Add marketplace`
3. 输入 marketplace source：`browserbase/skills`
4. 选择 `browse` 插件，回车安装
5. 重启 Claude Code

### 验证安装

安装完成后，Claude Code 会自动识别 `browse` 相关指令。可以直接用自然语言测试：

```
"Go to Hacker News, get the top post comments, and summarize them"
"QA test http://localhost:3000 and fix any bugs you encounter"
"Use bb to list my Browserbase projects"
```

---

## 📦 10 个核心技能详解

### 1. browser —— 核心浏览器自动化

这是最核心的技能，封装了与浏览器交互的主要能力。

**能力清单：**

- 远程 Browserbase 会话，支持反 Bot 检测
- Stealth 模式：隐藏自动化特征，模拟真实用户
- CAPTCHA 自动解决（Browserbase 内置）
- 住宅代理轮换（Residential Proxies）
- 完整 CDP（Chrome DevTools Protocol）访问

**常用命令：**

```bash
# 启动本地浏览器
browse env local

# 启动云端远程浏览器
browse env remote

# 打开指定 URL
browse goto https://example.com

# 截图
browse screenshot

# 点击元素
browse click "#submit-button"

# 填写表单
browse fill "#username" "myuser"
browse fill "#password" "mypass"

# 提取页面内容
browse extract "article h1"
```

**Stealth 配置示例：**

Browserbase 云端浏览器默认启用 Stealth，用户也可以在 Browserbase 平台配置具体参数（代理类型、地理位置、浏览器指纹等）。

### 2. browserbase-cli —— 官方 bb CLI

调用 Browserbase 平台的完整 CLI 工具，覆盖以下功能：

- **Sessions**：管理浏览器会话（创建、销毁、状态查询）
- **Projects**：项目 CRUD 操作
- **Contexts**：持久化上下文管理
- **Extensions**：浏览器扩展管理
- **Fetch**：无浏览器模式的 HTTP 请求（支持调试）
- **Dashboard**：直接打开 Browserbase 管理面板

**常用命令：**

```bash
# 查看当前使用情况
bb usage

# 列出项目
bb projects list

# 创建新会话
bb sessions create

# 查看会话详情
bb sessions list --project-id <id>

# 初始化 Browserbase Function
bb functions init
```

### 3. functions —— 无服务器浏览器自动化

将浏览器自动化函数部署到 Browserbase 云端，以无服务器方式运行。不需要维护长期运行的浏览器实例。

**工作流程：**

```bash
# 初始化一个新 Function
bb functions init

# 部署 Function
bb functions deploy

# 调用 Function
bb functions invoke <function-name>
```

适合将重复性的浏览器任务（如每日数据抓取、自动化测试）封装为 API 调用。

### 4. site-debugger —— Bot 检测诊断

这是 Browserbase Skills 中最有特色的技能之一。给定一个 URL，site-debugger 会自动：

1. 访问目标站点，分析 Bot 检测机制
2. 检查 selectors（选择器）稳定性
3. 分析时序问题（页面渲染时机）
4. 检查认证和 Session 状态
5. 检测 CAPTCHA 触发条件
6. 生成针对性的 Site Playbook

**输出示例：**

site-debugger 会生成一个经过测试的配置文件，记录该站点的最佳自动化策略。之后 Claude 可以根据这个 Playbook 稳定地操作目标站点。

### 5. browser-trace —— CDP 全量追踪

捕获完整的 Chrome DevTools Protocol 追踪数据：

- CDP firehose（全量事件流）
- 每个页面的截图
- DOM  dump
- 将追踪数据分桶存储，支持事后分析

**使用场景：**

- 调试复杂的前端交互问题
- 分析网站的网络请求行为
- 排查浏览器自动化失败原因

```bash
# 启动追踪
browse trace start

# 执行操作
browse click ".load-more"
browse scroll

# 停止追踪并分析
browse trace stop
```

### 6. bb-usage —— 用量与成本统计

在终端中展示 Browserbase 使用情况：

- 当前项目的会话数
- 已用额度 vs. 套餐限制
- 成本预测（根据历史用量估算月度账单）

```bash
bb usage
```

适合在运行大量自动化任务前评估成本，避免意外超额度。

### 7. cookie-sync —— Cookie 同步

将本地 Chrome 的登录 Cookie 同步到 Browserbase 远程浏览器：

1. 导出本地 Chrome 的 Cookie
2. 注入到 Browserbase 持久化上下文
3. 远程浏览器复用本地登录态

**典型用途：**

- 登录态复用：本地 Chrome 已经登录了某个网站，想在远程浏览器中复用
- 跨设备同步：不同 Browserbase 实例之间的 Session 共享

```bash
# 从本地 Chrome 导出 Cookie
browse cookie-export

# 同步到远程会话
browse cookie-sync --session-id <id>
```

### 8. fetch —— 无浏览器 HTTP 抓取

不需要启动浏览器，直接发送 HTTP 请求获取静态页面内容：

- 支持 HTML 和 JSON 响应
- 自动处理重定向
- 可查看状态码和响应头
- 适合快速检查页面可用性，不占用浏览器会话配额

```bash
# 抓取 HTML
browse fetch https://example.com

# 以 JSON 格式返回
browse fetch https://api.example.com/data --json
```

### 9. search —— 结构化网页搜索

无需启动浏览器，直接进行网络搜索并返回结构化结果：

- 返回标题、URL、元数据
- 不产生浏览器会话费用
- 适合信息搜集类任务

```bash
# 搜索关键词
browse search "Claude Code browser automation"

# 带结果数量限制
browse search "site:github.com browser automation" --limit 10
```

### 10. ui-test —— AI 对抗式 UI 测试

分析 Git diff 或探索性测试整个应用，发现 UI 变更引入的 Bug：

1. **Diff 驱动**：接收 Git diff，输入变更分析可能导致的问题
2. **全站探索**：AI 自主探索应用所有可交互元素，寻找异常

**特点：**

- 对抗式（Adversarial）：专门针对开发者可能忽略的边界情况
- 自动生成测试报告
- 可以与 CI/CD 集成

---

## 💡 实战示例

### 示例 1：抓取需要登录的页面

```bash
# 1. 先在本地 Chrome 登录目标网站
# 2. 同步 Cookie 到 Browserbase
browse cookie-sync --session-id <remote-session-id>

# 3. 在远程浏览器中访问已登录的页面
browse goto https://example.com/user/dashboard

# 4. 提取数据
browse extract ".dashboard-stat"
```

### 示例 2：调试被拦截的自动化脚本

```bash
# 使用 site-debugger 诊断目标站点
browse site-debugger https://example.com

# 查看诊断结果和建议
# 根据 site-debugger 生成的 Playbook 调整自动化策略

# 使用生成的配置重新访问
browse goto https://example.com --stealth --proxy residential
```

### 示例 3：创建无服务器自动化任务

```bash
# 初始化 Function
bb functions init

# 编写自动化逻辑（保存为 function.js）
# ...

# 部署到 Browserbase 云端
bb functions deploy

# 定时触发（通过 Cron 或外部 API）
bb functions invoke my-scheduled-task
```

---

## 🔍 适用场景与边界

### 适合的场景

- **数据采集**：需要从电商、社交媒体抓取数据，且目标站点有反爬虫机制
- **自动化测试**：端到端 UI 测试，特别是跨浏览器/跨环境的一致性测试
- **内容监控**：定期检查某网页内容变化并触发通知
- **Agent 增强**：为 AI Agent 添加真实的浏览器操作能力，突破纯 API 调用的限制
- **登录态管理**：跨会话复用复杂的多因素认证后状态

### 不适合的场景

- 纯 API 即可完成的数据获取（用 `fetch` 技能更省成本）
- 需要极致抓取速度的实时流处理（云端浏览器的网络延迟是瓶颈）
- 无需浏览器渲染的静态页面（直接 HTTP 请求更高效）
- 高度定制化的指纹需求（需要 Browserbase Enterprise 套餐）

---

## ⚙️ 环境变量与高级配置

Browserbase CLI 支持通过环境变量配置默认行为：

```bash
# 设置默认项目
export BROWSERBASE_PROJECT_ID=<project-id>

# 设置 API Key
export BROWSERBASE_API_KEY=<api-key>

# 配置代理
export BROWSERBASE_PROXY=<proxy-url>
```

在 Claude Code 中，这些环境变量可以通过 `.env` 文件或 Claude Code 的环境配置注入。

---

## ❓ 常见问题

### Q: 提示 "Chrome not found"

本地模式需要安装 Chrome：

- **macOS / Windows**：https://www.google.com/chrome/
- **Linux**：`sudo apt install google-chrome-stable`

### Q: 远程浏览器会话费用如何计算？

Browserbase 按会话时长和浏览器类型计费。具体价格见 Browserbase 官网定价页。`bb-usage` 技能可以实时查看当前用量和成本预测。

### Q: 如何刷新已过期的 Cookie？

```bash
rm -rf .chrome-profile
# 重新在本地 Chrome 登录目标网站
browse cookie-sync --session-id <id>
```

### Q: site-debugger 生成的 Playbook 可以自定义吗？

可以。Playbook 本质上是 JSON/YAML 格式的配置文件，site-debugger 给出建议后，用户可以手动调整其中的参数（如 selectors、stealth 级别、代理设置）。

### Q: ui-test 和普通单元测试的区别是什么？

ui-test 是对抗式的、AI 驱动的端到端测试，不需要预先编写测试用例。普通单元测试需要开发者定义断言，ui-test 则由 AI 自主发现潜在问题，更适合探索性测试阶段。

---

## 📚 总结与延伸阅读

Browserbase Skills 为 Claude Code 提供了一套完整的浏览器自动化工具链，从基础的页面交互到高级的反爬虫对抗、云端无服务器函数部署。各个技能可以独立使用，也可以组合成复杂的工作流。

**延伸阅读：**

- [Stagehand 文档](https://github.com/browserbase/stagehand)（Browserbase 的底层浏览器自动化库）
- [Claude Code Skills 官方文档](https://support.claude.com/en/articles/12512176-what-are-skills)
- [Browserbase 官方文档](https://docs.browserbase.com)
- [Browserbase Functions 部署指南](https://www.browserbase.com/docs/functions)
