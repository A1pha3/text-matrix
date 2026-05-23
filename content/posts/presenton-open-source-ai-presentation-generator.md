---
title: "Presenton：开源 AI 演示文稿生成器，Gamma 和 Decktopus 的自托管替代"
date: "2026-05-23T20:00:00+08:00"
slug: "presenton-open-source-ai-presentation-generator"
description: "Presenton 是开源 AI 演示文稿生成工具，支持自托管部署和桌面客户端，可在 Docker 或本地运行，支持 OpenAI、Gemini、Claude 等多模型提供商，以 Apache 2.0 开源，可导出可编辑的 PPTX 文件，适合需要数据隐私和避免 SaaS 订阅的团队。"
draft: false
categories: ["技术笔记"]
tags: ["TypeScript", "AI", "演示文稿", "开源", "自托管", "Electron"]
---

# Presenton：开源 AI 演示文稿生成器

做 PPT 这件事，本质上是把想法结构化输出。但当你把这件事交给 Gamma 或 Beautiful.ai 时，数据要上云、模板被锁定、价格按席位数计费。Presenton 想要解决的是：能不能在本地跑一个 AI 工具，把文档或 Prompt 变成 PPTX 文件，全程不离开你的机器，模型提供商自己选，模板自己改？

答案是能。

## 先判断这个工具值不值得看

如果你或你的团队有以下任何一个痛点，Presenton 值得评估：

- 需要在文档上传后自动生成 PPTX，而不是手动复制粘贴
- 对数据隐私有要求，演示内容不能上传到第三方 SaaS
- 想用自己购买的 API key 按量付费，不想按席位数订阅
- 想自己托管一个 Presentation-as-a-Service 给团队用

如果只是偶尔需要一个人做个 PPT，Gamma 的 Web 界面更省事，不需要折腾 Docker 或 Electron。

## 系统地图

Presenton 的技术栈分三层：

| 层级 | 技术选型 | 职责 |
|------|----------|------|
| 前端/桌面 | Electron + Next.js | UI、模板编辑、本地模型配置 |
| 后端 | FastAPI（Python） | PPTX 生成逻辑、模板渲染 |
| AI 层 | 统一接口（OpenAI compatible） | 调用各模型提供商的 API |

支持的部署方式：Docker（推荐，一行命令起服务）、Electron 桌面客户端（macOS/Windows/Linux）、自托管 API。

支持的模型提供商包括：OpenAI、Gemini、Vertex AI、Azure OpenAI、Amazon Bedrock、Fireworks、Together AI、Anthropic Claude、LM Studio、Ollama，以及任何 OpenAI API 兼容端点。

## 核心能力

### 支持多模型的自托管 AI 演示

不绑死模型是 Presenton 和 SaaS 产品最大的区别。你可以在同一个界面上切换"用 GPT-4o 生成内容、用 DALL-E 3 生成配图"，也可以把 Text Provider 换成 Gemini、Image Provider 换成 Pexels。所有配置通过环境变量或 UI 完成，不需要改代码。

对于 Ollama 用户，本地跑开源模型完全支持，适合不想走外网的隐私敏感场景。

### 可编辑 PPTX 导出

这是关键差异点。Gamma 导出的 PPTX 元素往往是图片化后的静态对象，编辑能力受限。Presenton 导出的 PPTX 是结构化的 PowerPoint 文件，文字、图表、布局各自独立，可直接在 PowerPoint 或 LibreOffice 里编辑。这对于需要后续修改的团队很重要。

### 模板系统

演示模板用 HTML + Tailwind CSS 构建，可以通过 UI 上传已有的 PPTX 文件作为"风格来源"，AI 会提取设计元素应用到生成的演示文稿中。这相当于把一个你喜欢的 PPT 的视觉风格迁移到 AI 生成的内容上。

### 内置 MCP Server

Model Context Protocol（MCP）是 Anthropic 主导的 AI 工具调用标准。Presenton 内置了 MCP Server，意味着 AI 助手（比如 Claude Desktop）可以直接调用 Presenton 的接口来生成演示，集成工作流可以做到更自动化。

### Docker 一键部署

官方推荐用 Docker 部署，一个 `docker compose up` 即可拉起完整服务，包含 GPU 支持（如果本地跑开源模型）。文档和部署示例在 [docs.presenton.ai](https://docs.presenton.ai)。

## 应用场景

**企业内网演示服务**：部署一台服务器，团队成员通过 Web 界面上传文档或输入 Prompt 生成 PPTX，全程数据不外流。

**本地创作工作室**：用 Ollama 本地跑开源模型，配合本地 PPTX 导出，不需要网络。

**AI 应用集成**：通过 MCP 或 REST API 把 PPT 生成能力集成到已有的 AI Agent 工作流里。

**桌面离线使用**：Electron 客户端适合没有服务器管理能力的用户，安装即用。

## 快速开始

### Docker（推荐）

```bash
git clone https://github.com/presenton/presenton.git
cd presenton
docker compose up
```

然后浏览器打开 `http://localhost:3000`。

### Electron 桌面客户端

从 [presenton.ai/download](https://presenton.ai/download) 下载对应平台的安装包（macOS/Windows/Linux 均支持），安装后直接运行。

### 开发模式

需要 Node.js（LTS）、npm、Python 3.11、uv。

```bash
cd electron
npm run setup:env   # 安装依赖、配置环境
npm run dev         # 启动 Electron（同时跑后端和前端）
```

## 局限性与边界

- **模板质量依赖 AI 输出**：生成效果和模型能力强相关，不是总能一次生成完美的演示
- **不支持实时协作**：这是纯离线工具，团队协作需要用文件流转
- **PPTX 渲染兼容性**：导出的文件在 Microsoft PowerPoint 里表现最好，部分 LibreOffice 场景可能有细微格式差异
- **桌面客户端消耗资源**：Electron 本身比较重，内存有限的机器建议用 Docker

## 项目元数据

| 项目 | 信息 |
|------|------|
| 仓库 | [presenton/presenton](https://github.com/presenton/presenton) |
| 语言 | TypeScript（主） + Python（后端） |
| Stars | 6,040 |
| Forks | 1,098 |
| 许可证 | Apache 2.0 |
| 官网 | [presenton.ai](https://presenton.ai) |
| 文档 | [docs.presenton.ai](https://docs.presenton.ai) |

---

*Presenton 是 Apache 2.0 开源项目，欢迎 PR 和贡献。*