---
title: "Onyx：开源 AI 平台，让你的团队拥有自己的 ChatGPT"
date: "2026-04-04T14:35:00+08:00"
slug: "onyx-open-source-ai-platform-guide"
description: "Onyx 是一个开源 AI 平台，提供 RAG、Deep Research、自定义 Agent、代码执行等高级功能，支持所有主流 LLM 提供商。本文介绍其核心功能、架构设计和部署方式。"
draft: false
categories: ["技术笔记"]
tags: ["AI平台", "RAG", "Deep Research", "Agent", "开源"]
---

# Onyx：开源 AI 平台，让你的团队拥有自己的 ChatGPT

> 项目地址：[onyx-dot-app / onyx](https://github.com/onyx-dot-app/onyx)
>
> 今日 Star：23,499（今日 +1,852）| Forks：3,151 | 最新版本：v3.1.1
>
> 🌟 如果你需要一个可以私有化部署的 ChatGPT 替代品，Onyx 值得一看

## 学习目标

读完本文，你会拿到：

1. 理解 Onyx 作为 LLM 应用层平台的核心定位。
2. 掌握 Onyx 的核心功能模块（RAG、Deep Research、Agent 等）。
3. 了解 Onyx Lite 和 Standard 两种部署模式的区别。
4. 完成 Onyx 的最小化安装和基本配置。
5. 判断 Onyx 适合哪些场景（团队协作、企业搜索、个人使用）。

## 一、项目简介

**Onyx** 是 LLM 的"应用层"——一个功能丰富的 AI 聊天平台，任何人都可以私有化部署。它让 LLM 具备高级能力，如 RAG（检索增强生成）、网络搜索、代码执行、文件创建、深度研究等。

用通俗的话说：Onyx 就是**可以私有化部署的 ChatGPT**，而且还多了很多企业级功能。

### 核心特点

| 特点 | 说明 |
|------|------|
| 开源免费 | MIT 许可证，社区版免费使用 |
| 私有化部署 | Docker/Kubernetes 一键部署 |
| 支持所有 LLM | OpenAI、Anthropic、Google、Gemini，开源模型（Ollama、vLLM） |
| 企业级功能 | SSO、RBAC、审计日志、协作功能 |
| 50+ 连接器 | 支持 Confluence、Google Drive、Slack、Notion 等数据源 |

## 二、核心功能详解

### 2.1 Agentic RAG — 下一代检索增强生成

RAG（Retrieval-Augmented Generation）是企业使用 LLM 的核心场景。Onyx 提供了**混合索引 + AI Agent** 的 RAG 方案：

- **混合索引**：结合向量搜索和关键词搜索，兼顾语义匹配和精确检索
- **AI Agent 增强**：Agent 会自动判断检索策略、多次迭代搜索、验证答案质量

**工作流程示意**：query → 混合索引检索 → Agent 二次检索 → 生成答案 → 答案验证

### 2.2 Deep Research — 深度研究代理

Onyx 的 Deep Research 功能可以自动完成多步骤研究流程：

1. 分解研究问题为子问题
2. 并行执行各子问题研究
3. 综合分析并生成报告

根据官方数据，Onyx Deep Research 在 2026 年 2 月的排行榜上名列前茅。

### 2.3 自定义 Agent

构建具有独特指令、知识和行为的 AI Agent：

- **个性化指令**：为 Agent 定义系统提示词
- **知识库关联**：让 Agent 访问特定数据源
- **Actions 配置**：赋予 Agent 执行特定操作的能力

### 2.4 Web Search

支持多种搜索引擎：
- Serper
- Google PSE（自定义搜索引擎）
- Brave Search
- SearXNG
- 自托管爬虫（支持 Firecrawl、Exa）

### 2.5 代码执行

在沙箱环境中执行代码：
- 数据分析并生成图表
- 文件创建和修改
- 自动化任务执行

### 2.6 其他功能

| 功能 | 说明 |
|------|------|
| Artifacts | 生成文档、图形、可下载内容 |
| Voice Mode | 语音对话（文字转语音 + 语音转文字） |
| Image Generation | 根据提示词生成图像 |
| Actions and MCP | 与外部应用集成，支持灵活认证 |

## 三、两种部署模式

Onyx 提供两种部署模式，适合不同场景：

### 3.1 Onyx Lite — 轻量级体验

**适用场景**：快速测试、个人使用、小团队

| 要求 | 规格 |
|------|------|
| 内存 | < 1GB |
| 复杂度 | 轻量级技术栈 |

Lite 模式是简化的聊天界面，适合只想体验 Chat 和 Agents 功能的用户。

### 3.2 Standard Onyx — 完整功能集

**适用场景**：生产环境、中大型团队、企业用户

完整功能包括：
- Vector + Keyword 混合索引（RAG 必须）
- 后台容器（任务队列和 Worker，用于数据源同步）
- AI 推理服务器（用于索引和推理的深度学习模型）
- 性能优化（Redis 缓存、MinIO 对象存储）

## 四、快速安装

### 4.1 一键安装（推荐）

```bash
curl -fsSL https://onyx.app/install_onyx.sh | bash
```

### 4.2 Docker 部署

```bash
# 拉取镜像
docker pull onyxdotapp/onyx:latest

# 运行容器
docker run -d \
  --name onyx \
  -p 3000:3000 \
  -v onyx_data:/data \
  onyxdotapp/onyx:latest
```

### 4.3 Kubernetes 部署

```bash
# 添加 Helm 仓库
helm repo add onyx https://charts.onyx.app
helm repo update

# 安装
helm install onyx onyx/onyx -n onyx --create-namespace
```

## 五、企业级功能

Onyx 面向企业场景提供完整解决方案：

| 功能 | 说明 |
|------|------|
| 协作共享 | 在组织内部分享聊天和 Agent |
| SSO 单点登录 | 支持 Google OAuth、OIDC、SAML |
| SCIM 用户同步 | 自动同步用户和组 |
| RBAC 权限控制 | 基于角色的资源访问控制 |
| 使用分析 | 按团队、LLM、Agent 统计用量 |
| 查询审计 | 记录和审计 AI 使用情况 |
| 自定义代码 | 移除 PII、拒绝敏感查询 |
| 白标定制 | 自定义品牌、图标、横幅 |

## 六、支持的 LLM 提供商

Onyx 支持所有主流 LLM，包括：

闭源模型：
- OpenAI (GPT-4o, GPT-4 Turbo)
- Anthropic (Claude 3.5, Claude 3)
- Google (Gemini Pro, Gemini Ultra)
- Azure OpenAI

开源模型：
- Ollama（本地运行）
- vLLM（高吞吐量推理）
- LiteLLM（统一接口）
- LM Studio

## 七、适用场景

| 场景 | 推荐配置 |
|------|----------|
| 个人 AI 助手 | Onyx Lite，单机部署 |
| 团队协作 | Standard Onyx，共享知识库 |
| 企业知识管理 | Standard Onyx + SSO + RBAC |
| 客服机器人 | Standard Onyx + Actions + MCP |
| 代码助手 | Standard Onyx + 代码执行 |

## 八、项目结构

```
onyx/
├── backend/          # Python 后端
├── cli/              # 命令行工具
├── desktop/          # 桌面应用
├── docs/             # 文档
├── web/              # Next.js 前端
├── widget/           # 嵌入式小组件
├── extensions/       # 浏览器扩展
│   └── chrome/       # Chrome 扩展
├── deployment/        # 部署配置
│   ├── docker/       # Docker 配置
│   └── kubernetes/   # K8s Helm Chart
└── tools/            # 工具集
```

## 九、总结

Onyx 为团队提供了一个**功能完整、可私有化部署的 AI 平台**。无论是个人探索还是企业级应用，都能找到合适的方案。其核心优势在于：

1. 开源免费：MIT 许可证，无供应商锁定
2. 功能丰富：RAG、Deep Research、Agent、代码执行等
3. 部署灵活：从单机到 Kubernetes 集群
4. 企业就绪：SSO、RBAC、审计日志等
5. 生态完善：50+ 数据连接器、MCP 支持

---

**相关链接：**
- 官网：https://www.onyx.app
- 文档：https://docs.onyx.app
- GitHub：https://github.com/onyx-dot-app/onyx
- Discord：https://discord.gg/TDJ59cGV2X
