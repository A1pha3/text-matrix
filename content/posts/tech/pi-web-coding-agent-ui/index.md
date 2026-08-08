---
title: "Pi Web：为 pi 编程代理打造的可视化工作空间"
date: 2026-08-09T03:22:48+08:00
slug: "pi-web-coding-agent-ui"
github_repo: "agegr/pi-web"
source_key: "gh:agegr/pi-web"
description: "Pi Web 是 pi 编程代理的本地 Web 界面，提供会话浏览、实时聊天、模型配置和项目管理功能。本文介绍其核心能力、安装方式与适用场景。"
draft: true
categories: ["技术笔记"]
tags: ["Pi Web", "AI编程代理", "开发者工具", "TypeScript", "开源"]
---

## 项目定位

[Pi Web](https://github.com/agegr/pi-web) 是 [pi 编程代理](https://github.com/badlogic/pi-mono)的本地 Web 界面。它读取 pi 在本地的会话文件，在浏览器中提供会话浏览、实时对话、模型配置、技能管理和项目文件预览等功能。截至本文写作时，项目在 GitHub 上获得约 3800 Star，用 TypeScript 编写，以 MIT 许可发布，当前版本 v0.8.7。

pi 是一个终端编程代理（类似 Claude Code 的 CLI 工具），会话以 JSONL 文件存储在 `~/.pi/agent/sessions/` 目录下。Pi Web 的价值在于：不用在终端历史里翻找对话，而是通过浏览器界面按项目浏览、搜索和继续之前的会话。

## 核心能力

### 会话管理

Pi Web 的主界面按项目分组展示会话列表。每条会话完整保留结构化的 Markdown 渲染、工具调用记录和代理响应，比终端中的原始输出更易读。

几个实用功能：

- **从历史消息继续**：在会话中选一条早前的消息，直接从那里接着对话
- **会话分叉（Fork）**：把当前会话复制一份，在新分支里尝试不同方向，不影响原始会话
- **工作区切换**：在侧边栏切换 Git worktree，会话列表和文件浏览器自动跟随当前检出分支
- **运行状态指示**：工作区选择器显示哪些会话正在运行或有未读活动

### 项目文件浏览

左侧面板提供文件树浏览，右侧面板支持源代码、文档、图片、音频和 PDF 的预览。这意味着你可以在代理工作的同时查看项目文件，无需在编辑器和终端之间来回切换。

### 模型与配置管理

Models 面板读取和写入 pi 代理目录下的 `models.json` 配置文件。可以在 Web 界面中管理模型列表、API 密钥、测试模型连通性，以及切换技能（Skill）开关，不必手动编辑配置文件。

### 上下文可视化

顶栏展示当前会话的上下文使用量、费用、压缩状态（Compaction）和系统提示词详情，让代理的运行状态一目了然。

## 安装与运行

Pi Web 需要 Node.js 22.19.0 或更高版本。最简单的方式是免安装直接运行：

```bash
npx @agegr/pi-web@latest
```

或者全局安装：

```bash
npm install -g @agegr/pi-web
pi-web
```

运行后自动打开 `http://127.0.0.1:30141`。服务默认绑定 `127.0.0.1`，仅本机可访问。

### 常用选项

```bash
pi-web --port 8080              # 自定义端口
pi-web --hostname 0.0.0.0       # 暴露到可信网络
pi-web --no-open                # 不自动打开浏览器

# 环境变量等效写法
PORT=8080 pi-web
PI_WEB_HOSTNAME=0.0.0.0 pi-web
PI_WEB_NO_OPEN=1 pi-web
```

### 安全注意事项

当通过 `--hostname 0.0.0.0` 或 `PI_WEB_HOSTNAME` 暴露到网络时，建议设置 Basic Auth：

```bash
PI_WEB_PASSWORD='a-long-random-password' pi-web
```

用户名固定为 `pi`。但 Basic Auth 的密码以明文传输，不应直接暴露在公网。远程访问应通过 HTTPS 反向代理或可信 VPN。

如果使用了反向代理且外部域名与绑定地址不同，需要通过 `PI_WEB_ALLOWED_HOSTS` 指定允许的 Host header：

```bash
PI_WEB_ALLOWED_HOSTS=pi-web.internal pi-web
```

### HTTP 代理

Pi Web 支持标准代理环境变量，用于服务端的模型 API 请求：

```bash
HTTP_PROXY=http://127.0.0.1:7890 \
HTTPS_PROXY=http://127.0.0.1:7890 \
NO_PROXY=localhost,127.0.0.1 \
npx @agegr/pi-web@latest
```

## 数据与文件结构

Pi Web 不自建数据存储，它直接读取 pi 代理的本地文件：

| 数据类型 | 路径 | 说明 |
|---------|------|------|
| 会话文件 | `~/.pi/agent/sessions/<encoded-cwd>/<timestamp>_<uuid>.jsonl` | 编码后的项目路径下按时间戳排列 |
| 模型配置 | `~/.pi/agent/models.json` | 模型列表、API 密钥、默认值 |
| 数据目录 | `PI_CODING_AGENT_DIR` 环境变量 | 可指向其他 pi 代理目录 |

文件浏览和预览的范围限定在当前选中项目的目录以及会话中出现的工作目录内，不会越界访问。

会话分叉（Fork）会创建一个新的 `.jsonl` 文件，与原始会话完全独立。"从此处编辑"（Edit from here）则在同一会话文件内创建新分支。

## 适用场景

**适合**：

- 使用 pi 编程代理作为日常开发工具，希望有更直观的会话管理界面
- 需要同时在多个项目中切换、对比不同会话上下文
- 想在浏览器里完成模型配置和技能管理，不想手动编辑 JSON
- 团队成员需要通过共享工作区查看代理的工作过程

**不适合**：

- 不使用 pi 代理的用户（Pi Web 本身不提供代理功能，只是界面层）
- 需要多用户协同编辑的场景（当前设计是单用户本地工具）

---

*项目地址：[github.com/agegr/pi-web](https://github.com/agegr/pi-web) · 许可证：MIT · 当前版本：v0.8.7*
