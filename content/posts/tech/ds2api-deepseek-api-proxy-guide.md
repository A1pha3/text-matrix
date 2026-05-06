---
title: "DS2API：为 DeepSeek Web 对话装上 OpenAI/Claude/Gemini 兼容接口"
slug: "ds2api-deepseek-api-proxy-guide"
description: "DS2API 是一个轻量级 Go 全栈中间件，将 DeepSeek Web 对话能力转换为 OpenAI、Claude 与 Gemini 兼容 API。支持多账号轮询、Vercel Serverless 和 Docker 部署，兼容主流 AI SDK。"
date: "2026-04-28T11:35:00+08:00"
categories: ["技术笔记"]
tags: ["ds2api", "DeepSeek", "API代理", "OpenAI兼容", "Go"]
hiddenFromHomePage: false
draft: false
---

# DS2API：为 DeepSeek Web 对话装上 OpenAI/Claude/Gemini 兼容接口

## 项目概览

DS2API（DeepSeek to API）是一个轻量级、高性能的 Go 全栈中间件，核心功能是将 DeepSeek Web 对话能力转换为兼容 OpenAI、Claude 与 Gemini 格式的 API 接口。对于已经基于这些 SDK 构建应用的开发者，DS2API 提供了无需修改代码即可接入 DeepSeek 的路径。

项目地址：[https://github.com/CJackHwang/ds2api](https://github.com/CJackHwang/ds2api)

**核心定位**：充当 DeepSeek Web 与主流 AI SDK 之间的协议翻译层。

## 读者收益

阅读本文后，你将了解：

- DS2API 的架构设计与核心模块划分
- 如何在本地、Docker 或 Vercel 上完成部署
- OpenAI、Claude、Gemini 三大兼容接口的使用方式
- 多账号轮询与并发控制的使用场景与配置方法

## 核心问题与解决思路

### 问题背景

DeepSeek 提供了 Web 界面和 API 两种访问方式，但 API 需要申请且有调用限制。部分开发者希望直接使用 DeepSeek 的 Web 对话能力，同时保留使用现有 AI SDK（OpenAI SDK、Anthropic SDK、Google Gemini SDK）的代码。

DS2API 的解决思路是：在 DeepSeek Web 对话与各大厂商 SDK 之间架设协议兼容层，让使用这些 SDK 的代码无需修改即可调用 DeepSeek。

### 技术选型

- **后端**：Go 全量实现，不依赖 Python 运行时，部署产物为单一二进制
- **前端**：React WebUI 管理台（`webui/` 目录），构建后以静态文件托管在 `/admin` 路径
- **部署**：支持本地运行、Docker、Linux systemd、Vercel Serverless

## 架构设计

DS2API 4.x 采用模块化 HTTP surface + PromptCompat 内核的设计：

```
客户端（OpenAI / Claude / Gemini）
    ↓
chi Router（RequestID / RealIP / Logger / Recoverer / CORS）
    ↓
┌─────────────────────────────────────┐
│  HTTP API Surface                   │
│  ├─ OpenAI: /v1/chat/completions   │
│  ├─ Claude: /anthropic/v1/messages  │
│  ├─ Gemini: /v1beta/models/*        │
│  └─ Admin: /admin（WebUI）          │
└─────────────────────────────────────┘
    ↓
PromptCompat（协议兼容性核心）
    ↓
DeepSeek Client
    ↓
DeepSeek Web API
```

关键模块职责：

| 模块 | 职责 |
|------|------|
| `PromptCompat` | 将各厂商请求格式转换为 DeepSeek Web 可处理的纯文本上下文 |
| `Account Pool + Queue` | 多账号轮询与并发槽位控制 |
| `DeepSeek Client` | 处理 Session、Auth、Completion、文件上传 |
| `PoW 实现` | DeepSeek 的工作量证明，毫秒级 Go 实现 |
| `Tool Sieve` | 工具调用解析，防泄漏处理 |

## 安装与最小示例

### 方式一：Docker 部署（推荐）

```bash
docker pull ghcr.io/cjackhwang/ds2api:latest
docker run -d -p 8080:8080 \
  -e DEEPSEEK_COOKIES="your_cookies_here" \
  ghcr.io/cjackhwang/ds2api:latest
```

### 方式二：Vercel Serverless

支持一键部署到 Vercel，获得免费的 Serverless 边缘节点。

### 方式三：本地二进制

从 [Release 页面](https://github.com/CJackHwang/ds2api/releases) 下载对应平台的二进制文件，然后：

```bash
./ds2api --port 8080
```

### OpenAI SDK 调用示例

```python
from openai import OpenAI

client = OpenAI(
    api_key="anything",  # DS2API 不校验 api_key
    base_url="http://localhost:8080/v1"
)

response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[{"role": "user", "content": "Hello"}]
)
print(response)
```

### Claude SDK 调用示例

```python
from anthropic import Anthropic

client = Anthropic(
    api_key="anything",
    base_url="http://localhost:8080/anthropic"
)

message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
)
```

## 多账号轮询配置

DS2API 支持配置多个 DeepSeek 账号，自动轮询使用：

1. 访问 DeepSeek Web，登录账号
2. 打开开发者工具，复制 `Cookie` 和 `NATIVE_TOKEN`
3. 在 Admin UI（`/admin`）中添加账号
4. 系统会自动在多个账号间轮询分发请求

并发控制方面，Admin UI 提供可视化配置：每个账号的 in-flight 上限、等待队列长度、动态并发建议值。

## 适用场景与优势

**适用场景**：

- 已有基于 OpenAI/Claude SDK 的项目，想切换到 DeepSeek 降低成本
- 需要同时使用多个 AI 能力，统一接口方便切换
- 开发者调试 AI 应用，需要 Web UI 可视化对话记录

**优势**：

- 零代码改造：现有 SDK 代码直接可用
- 轻量级：Go 编译后单文件，无 Python 依赖
- 多 SDK 兼容：OpenAI / Claude / Gemini 三大生态全覆盖
- 多账号轮询：提高并发上限，避免单账号限流

**边界与局限**：

- 依赖 DeepSeek Web 对话能力，非官方 API，稳定性受 DeepSeek Web 影响
- 部分高级功能（如 Vision）可能受限
- 需要维护 Cookie 和 Token，有一定上手成本

## 总结

DS2API 是一个解决协议兼容层的实用工具。它的价值在于让开发者无需重写代码，即可将现有的 AI 应用迁移到 DeepSeek Web 对话后端。如果你正在寻找一种低成本的 DeepSeek 接入方案，DS2API 值得尝试。

项目仍在活跃维护中（最近更新：2026-04-28），文档和示例较为完整。如需了解更多技术细节，建议阅读项目自带的[架构说明文档](https://github.com/CJackHwang/ds2api/blob/main/docs/ARCHITECTURE.md)。

---

*本文基于 GitHub 仓库 v4.x 版本编写，Stars 1,904，Forks 579。*
