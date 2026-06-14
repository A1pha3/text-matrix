---
title: "Hermes Desktop：把 Hermes Agent 装成开箱即用的桌面 App，14 个工具集 + 16 个 IM 网关"
date: "2026-06-09T17:59:00+08:00"
slug: "hermes-desktop-gui-wrapper"
aliases:
  - "/posts/tech/hermes-desktop-gui-wrapper/"
description: "Hermes Desktop 是 NousResearch Hermes Agent 的官方 Electron 桌面外壳，覆盖安装引导、22 个 slash 命令、14 个工具集、16 个 IM 网关、调度任务、记忆系统、SOUL.md 编辑。Windows / macOS / Linux 三端 native 安装包，自带中文 i18n。"
draft: false
categories: ["技术笔记"]
tags: ["HermesDesktop", "HermesAgent", "Electron", "AIAssistant", "NousResearch", "GUI"]
---

# Hermes Desktop：把 Hermes Agent 装成开箱即用的桌面 App，14 个工具集 + 16 个 IM 网关

> **目标读者**：想用 Hermes Agent 但嫌 CLI 起步成本高的用户，以及需要把 Agent 接到 IM 平台做团队助手的开发者
> **要解决的问题**：CLI 形态的 Hermes Agent 怎么变成本地 / 远端双模式、能管 Provider / Profile / Skill / Schedule / Gateway 的桌面 App？
> **难度**：⭐（下载装包即可）
> **来源**：GitHub [fathah/hermes-desktop](https://github.com/fathah/hermes-desktop)，11,389 ★ / MIT / 2026-06-09

---

## 一、定位判断

Hermes Desktop 做的事情在产品形态上很明确：

1. **本地模式**（默认）：在 `~/.hermes` 拉起 Hermes 后端，前端 Electron 走 `127.0.0.1:8642` + SSE 流式协议
2. **远端模式**：填 API URL + Key，桌面端直接连远端 Hermes 服务，跳过本地安装
3. **外壳功能**：安装引导、Provider 配置、Profile 切换、Skill 管理、记忆系统可视化、Persona 编辑、调度任务、IM 网关、Settings

它不是"另一个 AI 聊天客户端"，而是 **Hermes Agent 的官方 GUI 包装**——把命令行里需要编辑 YAML / 跑 cron 表达式 / 配 webhook 的活，全部变成按钮 + 表单。

---

## 二、项目概览

| 维度 | 数据 |
|---|---|
| **仓库** | [fathah/hermes-desktop](https://github.com/fathah/hermes-desktop) |
| **Stars** | 11,389 ★（2026-06-09 抓取） |
| **License** | MIT |
| **底层 Agent** | [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) |
| **桌面壳** | Electron 39 |
| **支持平台** | Windows、macOS、Linux（含 Fedora .rpm） |
| **i18n** | en、zh-CN、ja-JP、es-LATAM |
| **状态** | 活跃开发，README 显式标"active development" |

---

## 三、安装路径

| 平台 | 命令 |
|---|---|
| macOS | 下载 `hermes-desktop-<version>.dmg`（[hermesagents.cc](https://hermesagents.cc/)） |
| Windows | 下载 installer；首次启动会被 SmartScreen 拦，点 "More info" → "Run anyway"（未签名） |
| Fedora / RHEL | `sudo dnf install ./hermes-desktop-<version>.rpm`（未 GPG 签名，需要 `--nogpgcheck`） |
| 源码开发 | `npm install && npm run dev`（需 Node.js + Unix-like shell） |

WSL 用户在 Playwright 等步骤可能卡 sudo，README 给了一段临时免密 sudo 的解法。

---

## 四、12 个主要屏幕

| 屏幕 | 作用 |
|---|---|
| **Chat** | 流式聊天 UI，SSE 实时渲染、工具进度、markdown、语法高亮、token 用量显示 |
| **Sessions** | 全文本搜索（SQLite FTS5）、按日期分组、断点续聊 |
| **Agents** | 创建 / 删除 / 切换 Hermes 配置文件（独立环境） |
| **Skills** | 浏览、安装、管理 bundled 和用户安装的 skill |
| **Models** | 跨 Provider 增删改查模型配置 |
| **Memory** | 增删改查记忆条目、用户画像、配置记忆提供者 |
| **Soul** | 编辑 `SOUL.md` 人格 |
| **Tools** | 启停单个工具集（toolset） |
| **Schedules** | cron 表达式构造器、15 个投递目标 |
| **Gateway** | 16 个 IM 平台集成配置 |
| **Office (Claw3d)** | 3D 视觉界面 + dev server / adapter 管理 |
| **Settings** | Provider 配置、凭据池、备份导入、日志、网络、主题 |

---

## 五、22 个 slash 命令

直接在 Chat 面板输入：

```
/new /clear /fast /web /image /browse /code /shell
/usage /help /tools /skills /model /memory /persona
/version /compact /compress /undo /retry /debug /status
```

每条命令对应 Hermes Agent 后端的能力——`/web` 调 Exa / Tavily、`/browse` 调 Browserbase、`/image` 调 FAL.ai。`/usage` 实时显示 prompt / completion token + 费用。

---

## 六、14 个工具集（toolsets）

- web（Exa Search / Parallel API / Tavily / Firecrawl）
- browser（Browserbase）
- terminal
- file
- code execution
- vision
- image gen（FAL.ai）
- TTS
- skills
- memory
- session search
- clarify
- delegation
- MoA（Mixture-of-Agents）
- task planning

Tools 屏幕可单独启停——对"安全场景"特别有用（关掉 code execution / terminal，仅留 web + memory）。

---

## 七、16 个 IM 网关（这是它的杀手锏）

| 类别 | 平台 |
|---|---|
| 海外主流 | Telegram、Discord、Slack、WhatsApp、Signal、Matrix / Element、Mattermost |
| 邮件 | Email（IMAP / SMTP） |
| 短信 | Twilio、Vonage |
| Apple | iMessage（BlueBubbles） |
| 国内 | 钉钉、飞书 / Lark、企业微信、微信（iLink Bot） |
| 自动化 | Webhooks、Home Assistant |

**飞书 / 钉钉 / 企微 / 微信都在列**——这是给国内团队做 AI 助手最直接的方式，免去自己写 Bot 适配。

Schedules 屏幕 15 个投递目标，覆盖同样的 IM 列表 + Webhook。

---

## 八、记忆系统：6 个可插拔 provider

| Provider | 特点 |
|---|---|
| **Honcho** | 对话级长期记忆 |
| **Hindsight** | 时序记忆 |
| **Mem0** | 通用长记忆 |
| **RetainDB** | 轻量本地 |
| **Supermemory** | 云端 |
| **ByteRover** | 字节内部方案（开源） |

Hermes Desktop 让你在 Settings 里**直接切换 provider**，不必改 Hermes 后端配置。对"我想用 Mem0 但不想动 YAML"的用户是直接体验升级。

---

## 九、Provider 矩阵

| Provider | 备注 |
|---|---|
| **OpenRouter** | 200+ 模型，推荐 |
| **Anthropic / OpenAI / Google (Gemini) / xAI (Grok)** | 直连官方 |
| **Nous Portal** | 有免费层 |
| **Qwen / MiniMax / Hugging Face / Groq** | 国内 / 推理快 |
| **本地** | LM Studio、Atomic Chat、Ollama、vLLM、llama.cpp（OpenAI 兼容 endpoint） |

Atlas Cloud 是 README 显式列的赞助商——OpenAI 兼容网关，DeepSeek / Qwen / GLM / Kimi / MiniMax 都有，base URL 预填。

---

## 十、技术栈

- **Electron 39** 桌面壳
- **SSE** 流式协议（本地 `http://127.0.0.1:8642` 或远端 URL）
- **SQLite FTS5** 全文搜索会话
- **electron-updater** 自动更新
- **Vitest** 测试套件

---

## 十一、适用边界

**适合**：
- 想本地跑 Hermes Agent 但不想动 CLI 的用户
- 需要"一键把 Agent 接到飞书 / 钉钉 / 企微" 的团队
- 想可视化地管理多 Profile / 多 Provider / 多 Skill 的高级用户
- AI 助手"自托管 + 桌面可控" 场景（敏感数据不出内网）

**不适合**：
- 服务端大规模部署（Electron 桌面形态不适合无头服务器场景）
- 对稳定性要求 100% 工业级——README 明确写"active development, some things might break"
- 需要 Windows 代码签名（installer 未签名会被 SmartScreen 拦）

---

## 十二、阅读路径

```bash
# 1. 下载
open https://hermesagents.cc/

# 2. 装完第一次启动 → 选 Local / Remote
# 3. 配 Provider（OpenRouter 一行 key 即可）
# 4. 在 Chat 跑 /help 看所有命令
# 5. 去 Gateway 配飞书机器人
# 6. 去 Schedules 建个每天 9 点的早报 cron
```

如果已经在用 Hermes Agent 跑 CLI，Hermes Desktop 给你"装进系统托盘 + 接飞书" 这最后一公里；如果没在用 Hermes Agent，它也是当下**最容易上手的本地 AI 助手桌面形态之一**——14 个 toolset + 16 个网关开箱即用，省去从零集成。
