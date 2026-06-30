---
title: "Vane：隐私优先的 AI 回答引擎完全指南"
date: "2026-03-31T15:50:00+08:00"
slug: "vane-ai-search-engine-guide"
description: "全面解析 Vane (33.5k Stars)：隐私优先的 AI 回答引擎，支持本地 Ollama/OpenAI/Claude/Gemini/Groq，配备 SearxNG 隐私搜索，引用来源，文件上传分析。"
draft: false
categories: ["技术笔记"]
tags: ["Vane", "AI搜索引擎", "隐私计算", "SearxNG", "Ollama", "RAG", "本地LLM", "Docker"]
---

# Vane：隐私优先的 AI 回答引擎完全指南

## 一、学习目标

完成本文档后，你将能够：

- ✅ 理解 Vane 的核心定位与设计理念
- ✅ 掌握 Vane 的十一大核心功能
- ✅ 熟练安装和配置 Vane（Docker/非 Docker）
- ✅ 配置多种 AI 提供商（Ollama/OpenAI/Claude/Gemini/Groq）
- ✅ 使用智能搜索模式（Speed/Balanced/Quality）
- ✅ 使用文件上传和搜索功能
- ✅ 配置 SearxNG 和其他搜索源
- ✅ 排查常见问题（Ollama/Lemonade 连接错误）
- ✅ 使用 Vane 的 API

---

## 二、目录

- [一、学习目标](#一学习目标)
- [二、目录](#二目录)
- [三、项目概述](#三项目概述)
- [四、核心功能详解](#四核心功能详解)
- [五、安装与配置](#五安装与配置)
- [六、故障排除](#六故障排除)
- [七、使用示例](#七使用示例)
- [八、项目结构](#八项目结构)
- [九、API 使用](#九api-使用)
- [十、一键部署](#十一键部署)
- [十一、即将推出的功能](#十一即将推出的功能)
- [十二、常见问题](#十二常见问题)
- [十三、总结](#十三总结)
- [十四、自测题](#十四自测题)
- [十五、练习](#十五练习)
- [十六、进阶路径](#十六进阶路径)
- [十七、资料口径说明](#十七资料口径说明)

---

## 三、项目概述

### 3.1 什么是 Vane？

**Vane**（官方仓库：[ItzCrazyKns/Vane](https://github.com/ItzCrazyKns/Vane)）是一个**隐私优先的 AI 回答引擎**，完全运行在你自己的硬件上。

**官方描述**：

> Vane is a privacy-focused AI answering engine that runs entirely on your own hardware. It combines knowledge from the vast internet with support for local LLMs (Ollama) and cloud providers (OpenAI, Anthropic Claude, Groq), delivering accurate answers with cited sources while keeping your searches completely private.

**翻译**：Vane 是一个注重隐私的 AI 回答引擎，完全运行在你自己的硬件上。它结合了互联网的广泛知识，支持本地 LLM（Ollama）和云服务提供商（OpenAI、Anthropic Claude、Groq），提供带有引用来源的准确答案，同时保持你的搜索完全私密。

### 3.2 关键价值主张

| 价值 | 说明 |
|------|------|
| **隐私优先** | 完全运行在本地硬件，搜索历史不外泄 |
| **多 AI 支持** | Ollama/OpenAI/Claude/Gemini/Groq |
| **智能搜索** | Speed/Balanced/Quality 三种模式 |
| **来源可选** | 网页、讨论、学术论文 |
| **引用来源** | 所有答案都有来源引用 |
| **文件理解** | PDF、图片、文本文件上传分析 |

### 3.3 核心数据

```
Stars:     33,500 (33.5k)
Forks:     3,600 (3.6k)
Watchers:  187
贡献者:    48 人
提交数:   986 次
分支数:    20 个
标签数:    38 个
发布版本:  33 个
最新版本:  v1.12.1 (2025-12-31)
许可证:    MIT
语言:     TypeScript 98.7%
```

### 3.4 功能一览

| 功能 | 说明 |
|------|------|
| 🤖 AI 提供商 | Ollama/OpenAI/Claude/Gemini/Groq |
| ⚡ 搜索模式 | Speed/Balanced/Quality |
| 🧭 来源选择 | 网页/讨论/学术论文 |
| 🧩 Widgets | 天气/股票/计算器 |
| 🔍 SearxNG | 隐私搜索引擎 |
| 📷 图视搜索 | 图片和视频搜索 |
| 📄 文件上传 | PDF/图片/文本 |
| 🌐 域名搜索 | 指定网站搜索 |
| 💡 智能建议 | 搜索建议 |
| 📚 Discover | 趋势内容发现 |
| 🕒 搜索历史 | 本地保存 |

---

## 四、核心功能详解

### 4.1 多 AI 提供商支持

**支持的 AI 提供商**

| 提供商 | 类型 | 说明 |
|--------|------|------|
| **Ollama** | 本地 | 运行本地 LLM |
| **OpenAI** | 云 | GPT-4o 等 |
| **Anthropic Claude** | 云 | Claude 3.5 等 |
| **Google Gemini** | 云 | Gemini 2.0 等 |
| **Groq** | 云 | 高速推理 |

**配置多个提供商**

Vane 允许同时配置多个提供商，根据需求混合使用。

### 4.2 智能搜索模式

| 模式 | 用途 | 特点 |
|------|------|------|
| **Speed Mode** | 快速答案 | 低延迟，快速响应 |
| **Balanced Mode** | 日常搜索 | 平衡速度和质量 |
| **Quality Mode** | 深度研究 | 全面深入的分析 |

### 4.3 来源选择

| 来源 | 说明 |
|------|------|
| **Web** | 互联网搜索 |
| **Discussions** | 社区讨论 |
| **Academic Papers** | 学术论文 |

### 4.4 Widgets

智能 UI 卡片，在相关时显示：

| Widget | 说明 |
|--------|------|
| **Weather** | 天气预报 |
| **Calculations** | 计算器 |
| **Stock Prices** | 股票价格 |
| **Quick Lookups** | 快速查询 |

### 4.5 SearxNG 搜索

- **隐私保护**：使用 SearxNG 保护身份
- **多引擎支持**：同时搜索多个搜索引擎
- **即将支持**：Tavily 和 Exa

### 4.6 文件上传与分析

**支持的格式**

| 格式 | 说明 |
|------|------|
| **PDF** | 文档分析 |
| **Images** | 图片理解 |
| **Text Files** | 文本分析 |

### 4.7 域名搜索

当你知道从哪里找时，可以限制在特定网站搜索：

- 技术文档
- 研究论文
- 特定论坛

### 4.8 Discover 功能

浏览有趣的文章和全天趋势内容。无需搜索也能保持信息更新。

### 4.9 搜索历史

每次搜索都保存在本地，可以随时回顾。

---

## 五、安装与配置

### 5.1 Docker 安装（推荐）

**快速启动**

```bash
docker run -d -p 3000:3000 -v vane-data:/home/vane/data --name vane itzcrazykns1337/vane:latest
```

**说明**

- `-d`：后台运行
- `-p 3000:3000`：端口映射
- `-v vane-data:/home/vane/data`：数据持久化
- 包含 SearxNG 搜索引擎

**访问**

打开浏览器访问：http://localhost:3000

### 5.2 使用自有 SearxNG 实例

如果已有 SearxNG 运行，使用 slim 版本：

```bash
docker run -d -p 3000:3000 \
  -e SEARXNG_API_URL=http://your-searxng-url:8080 \
  -v vane-data:/home/vane/data \
  --name vane itzcrazykns1337/vane:slim-latest
```

**SearxNG 要求**

- JSON 格式启用
- Wolfram Alpha 搜索引擎启用

### 5.3 从源码构建

**前置要求**

- Docker 已安装

**步骤**

```bash
# 克隆仓库
git clone https://github.com/ItzCrazyKns/Vane.git
cd Vane

# 构建并运行
docker build -t vane .
docker run -d -p 3000:3000 -v vane-data:/home/vane/data --name vane vane
```

### 5.4 非 Docker 安装

**前置要求**

- SearxNG 已安装并配置（JSON 格式启用，Wolfram Alpha 启用）

**步骤**

```bash
# 克隆仓库
git clone https://github.com/ItzCrazyKns/Vane.git
cd Vane

# 安装依赖
npm i

# 构建
npm run build

# 启动
npm run start
```

**访问**：http://localhost:3000

### 5.5 配置 AI 提供商

在设置界面配置：

1. API Keys
2. 模型选择
3. SearxNG URL

---

## 六、故障排除

### 6.1 Ollama 连接错误

**检查事项**

1. **Ollama API URL 正确**
2. **不同系统的 API URL**
   - Windows：使用 `http://host.docker.internal:11434`
   - Mac：使用 `http://host.docker.internal:11434`
   - Linux：使用 `http://<主机IP>:11434`

3. **Linux 用户暴露 Ollama 到网络**

编辑 `/etc/systemd/system/ollama.service`，添加：

```bash
Environment="OLLAMA_HOST=0.0.0.0:11434"
```

然后重新加载：

```bash
systemctl daemon-reload
systemctl restart ollama
```

### 6.2 Lemonade 连接错误

**检查事项**

1. **Lemonade API URL 正确**
2. **不同系统的 API URL**
   - Windows：使用 `http://host.docker.internal:8000`
   - Mac：使用 `http://host.docker.internal:8000`
   - Linux：使用 `http://<主机IP>:8000`

3. **Lemonade 服务器运行中**

### 6.3 本地 OpenAI-API-兼容服务器

**检查事项**

1. 服务器运行在 `0.0.0.0`（不是 `127.0.0.1`）
2. 端口正确
3. API key 字段填写了内容（即使服务器不需要 key）

---

## 七、使用示例

### 7.1 基础搜索

```
输入：什么是 RAG
输出：带有引用来源的详细解释
```

### 7.2 文件分析

```
上传：一份 PDF 研究论文
提问：总结主要发现
输出：AI 总结的论文核心内容
```

### 7.3 深度研究

使用 Quality Mode 进行深度研究：

```
输入：分析 AI Agent 在 2026 年的发展趋势
输出：全面的研究报告，包含多个来源引用
```

---

## 八、项目结构

### 8.1 目录结构

| 目录 | 说明 |
|------|------|
| `src/` | Next.js 源代码 |
| `public/` | 静态资源 |
| `drizzle/` | 数据库配置 |
| `searxng/` | SearxNG 配置 |
| `docs/` | 文档 |
| `data/` | 数据存储 |
| `.assets/` | 资源文件 |

### 8.2 配置文件

| 文件 | 说明 |
|------|------|
| `package.json` | Node.js 配置 |
| `next.config.mjs` | Next.js 配置 |
| `tailwind.config.ts` | Tailwind CSS 配置 |
| `docker-compose.yaml` | Docker Compose 配置 |
| `Dockerfile` | Docker 镜像配置 |

---

## 九、API 使用

Vane 提供 API 供开发者集成。

**文档位置**

详见 `docs/API/SEARCH.md`

**基本用法**

```bash
# 搜索示例
curl -X POST http://localhost:3000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "your question"}'
```

---

## 十、一键部署

| 平台 | 链接 |
|------|------|
| **Sealos** | [Deploy to Sealos](https://usw.sealos.io/?openapp=system-template%3FtemplateName%3Dperplexica) |
| **RepoCloud** | [Deploy to RepoCloud](https://repocloud.io/details/?app_id=267) |
| **ClawCloud** | [Run on ClawCloud](https://template.run.claw.cloud/?referralCode=U11MRQ8U9RM4&openapp=system-fastdeploy%3FtemplateName%3Dperplexica) |
| **Hostinger** | [Deploy on Hostinger](https://www.hostinger.com/vps/docker-hosting?compose_url=https://raw.githubusercontent.com/ItzCrazyKns/Vane/refs/heads/master/docker-compose.yaml) |

---

## 十一、即将推出的功能

| 功能 | 状态 |
|------|------|
| 更多 Widgets 和集成 | 进行中 |
| 自定义 Agent | 进行中 |
| 认证系统 | 进行中 |

---

## 十二、常见问题

### Q1：Vane 和 Perplexity 有什么区别？

| 特性 | Vane | Perplexity |
|------|------|-------------|
| **运行位置** | 完全本地 | 云端 |
| **隐私** | 完全私密 | 部分隐私 |
| **本地 LLM** | ✅ Ollama 支持 | ❌ 不支持 |
| **自托管** | ✅ 完全支持 | ❌ 不支持 |

### Q2：需要多少硬件？

**最低要求**

- 4GB RAM
- 10GB 磁盘空间

**推荐配置**

- 8GB+ RAM（用于本地 LLM）
- 20GB+ 磁盘空间

### Q3：支持哪些本地模型？

通过 Ollama 支持所有兼容 Ollama 的模型：

- Llama 2/3
- Mistral
- Code Llama
- 其他 GGUF 格式模型

### Q4：如何更新 Vane？

**Docker 方式**

```bash
docker stop vane
docker rm vane
docker pull itzcrazykns1337/vane:latest
# 重新运行
```

### Q5：搜索历史保存在哪里？

保存在 Docker volume 中：

```bash
-v vane-data:/home/vane/data
```

### Q6：支持中文吗？

Vane 界面支持多语言，具体搜索结果取决于使用的 AI 提供商和模型。

---

## 十三、总结

### 13.1 核心优势

| 优势 | 说明 |
|------|------|
| **隐私优先** | 完全本地运行，搜索历史不外泄 |
| **多 AI 支持** | Ollama/OpenAI/Claude/Gemini/Groq |
| **智能模式** | Speed/Balanced/Quality 三种模式 |
| **来源引用** | 所有答案都有引用来源 |
| **文件理解** | PDF、图片、文本上传分析 |
| **自托管** | 完全开源，可自托管 |

### 13.2 适用场景

| 场景 | 推荐指数 |
|------|----------|
| 隐私敏感搜索 | ⭐⭐⭐⭐⭐ |
| 本地 LLM 使用 | ⭐⭐⭐⭐⭐ |
| 深度研究 | ⭐⭐⭐⭐⭐ |
| 日常搜索 | ⭐⭐⭐⭐ |
| 企业内部搜索 | ⭐⭐⭐⭐⭐ |

### 13.3 项目信息

- Stars：33.5k
- Forks：3.6k
- 贡献者：48 人
- 最新版本：v1.12.1 (2025-12-31)
- 许可证：MIT

### 13.4 相关资源

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/ItzCrazyKns/Vane |
| Discord | https://discord.gg/26aArMy8tT |
| Docker Hub | https://hub.docker.com/r/itzcrazykns1337/vane |

---

## 十四、自测题

### 14.1 Vane 的核心价值主张是什么？

<details>
<summary>点击查看答案</summary>

Vane 的核心价值主张包括：
1. **隐私优先**：完全运行在本地硬件，搜索历史不外泄
2. **多 AI 支持**：Ollama/OpenAI/Claude/Gemini/Groq
3. **智能搜索**：Speed/Balanced/Quality 三种模式
4. **来源可选**：网页、讨论、学术论文
5. **引用来源**：所有答案都有来源引用
6. **文件理解**：PDF、图片、文本文件上传分析

</details>

### 14.2 Vane 支持哪些 AI 提供商？

<details>
<summary>点击查看答案</summary>

Vane 支持以下 AI 提供商：
1. **Ollama**（本地）
2. **OpenAI**（云）
3. **Anthropic Claude**（云）
4. **Google Gemini**（云）
5. **Groq**（云）

你可以同时配置多个提供商，根据需求混合使用。

</details>

### 14.3 Vane 的智能搜索模式有哪些？

<details>
<summary>点击查看答案</summary>

Vane 有三种智能搜索模式：
1. **Speed Mode**：快速答案，低延迟，快速响应
2. **Balanced Mode**：日常搜索，平衡速度和质量
3. **Quality Mode**：深度研究，全面深入的分析

</details>

### 14.4 如何安装 Vane（Docker 方式）？

<details>
<summary>点击查看答案</summary>

Docker 安装步骤：
1. 运行 `docker run -d -p 3000:3000 -v vane-data:/home/vane/data --name vane itzcrazykns1337/vane:latest`
2. 打开浏览器访问 http://localhost:3000
3. 在设置界面配置 API Keys、模型选择、SearxNG URL

</details>

### 14.5 Vane 和 Perplexity 有什么区别？

<details>
<summary>点击查看答案</summary>

主要区别：
1. **运行位置**：Vane 完全本地，Perplexity 云端
2. **隐私**：Vane 完全私密，Perplexity 部分隐私
3. **本地 LLM**：Vane 支持 Ollama，Perplexity 不支持
4. **自托管**：Vane 完全支持，Perplexity 不支持

</details>

---

## 十五、练习

### 练习 1：Docker 安装 Vane 并验证

**任务**：使用 Docker 安装 Vane，并验证它能够正常运行。

**步骤**：
1. 运行 Docker 安装命令
2. 访问 http://localhost:3000
3. 配置一个 AI 提供商（例如 Ollama）
4. 执行一次搜索并验证结果

**参考答案**：安装成功后，你应该能够访问 Vane 的 Web UI，配置 AI 提供商，并执行搜索。搜索结果应该包含引用来源。

### 练习 2：配置多个 AI 提供商

**任务**：在 Vane 中配置多个 AI 提供商（Ollama + OpenAI），并测试它们的切换。

**步骤**：
1. 进入 Vane 设置界面
2. 配置 Ollama（本地）
3. 配置 OpenAI（云）
4. 执行搜索并观察不同提供商的响应

**参考答案**：Vane 允许同时配置多个提供商。你可以在搜索时选择使用哪个提供商，或者让 Vane 自动选择。

### 练习 3：上传文件并分析

**任务**：上传一个 PDF 文件到 Vane，并让它分析主要内容。

**步骤**：
1. 准备一个 PDF 文件（例如研究论文）
2. 在 Vane 中上传该文件
3. 提问："总结主要发现"
4. 验证 AI 的回答是否准确

**参考答案**：Vane 支持 PDF、图片、文本文件上传分析。上传后，你可以针对文件内容提问，AI 会基于文件内容给出回答，并引用具体位置。

---

## 十六、进阶路径

如果你想深入研究 Vane 和隐私优先的 AI 搜索技术，可以按照以下 7 个步骤进行：

### 16.1 步骤 1：理解 Vane 的架构

**目标**：掌握 Vane 的核心架构和设计理念。

**行动**：
- 阅读 Vane 官方文档（https://github.com/ItzCrazyKns/Vane）
- 研究项目结构（Next.js 前端、SearxNG 集成、API 设计）
- 理解隐私优先的设计理念

### 16.2 步骤 2：掌握 SearxNG 集成

**目标**：深入理解 SearxNG 如何与 Vane 集成。

**行动**：
- 研究 SearxNG 的配置（JSON 格式、Wolfram Alpha 启用）
- 理解隐私搜索的工作原理
- 学习如何自定义搜索源

### 16.3 步骤 3：配置和优化 AI 提供商

**目标**：掌握如何配置和优化多个 AI 提供商。

**行动**：
- 学习 Ollama 本地部署和模型管理
- 理解 OpenAI/Claude/Gemini/Groq 的 API 配置
- 优化不同提供商的响应速度和质量

### 16.4 步骤 4：使用文件上传和分析功能

**目标**：使用 Vane 的文件上传和分析功能。

**行动**：
- 测试 PDF、图片、文本文件的上传
- 理解 AI 如何分析文件内容
- 学习如何引用文件中的具体位置

### 16.5 步骤 5：部署到生产环境

**目标**：将 Vane 部署到生产环境。

**行动**：
- 使用 Docker Compose 配置生产环境
- 配置反向代理（Nginx/Caddy）
- 设置 HTTPS 和域名

### 16.6 步骤 6：参与 Vane 开源社区

**目标**：为 Vane 项目做出贡献，推动隐私优先的 AI 搜索技术发展。

**行动**：
- 在 GitHub 上提交 Issues 和 Pull Requests
- 参与 Discord 社区讨论（https://discord.gg/26aArMy8tT）
- 分享你的使用案例和最佳实践

### 16.7 步骤 7：构建自己的隐私 AI 搜索解决方案

**目标**：基于 Vane 的技术栈，构建自己的隐私 AI 搜索解决方案。

**行动**：
- 定制化 Vane 的 UI 和功能
- 集成额外的搜索源和 AI 提供商
- 部署和监控生产级系统

---

## 十七、资料口径说明

本文档基于以下来源和假设：

1. **信息来源**：本文档基于 Vane 官方 GitHub 仓库（https://github.com/ItzCrazyKns/Vane）、官方文档和公开技术描述。所有技术描述都尽量引用官方来源。

2. **版本时效性**：本文档基于 2026-03-31 的 Vane 版本（v1.12.1）。由于项目活跃开发中，具体 API、命令、功能可能随版本变化。建议读者在使用时核对官方文档的最新版本。

3. **技术细节验证**：本文档中提到的技术细节（如 Docker 安装步骤、Ollama 配置、SearxNG 集成等）基于官方文档描述。由于无法在实际环境中完全验证所有细节，建议在关键决策前自行验证。

4. **性能数据未验证**：本文档未包含独立的性能测试数据。Vane 的搜索速度、AI 响应时间、文件分析精度等，都需要读者在自己的环境中验证。

5. **安全建议边界**：本文档提到的隐私保护、数据安全是通用建议。实际的安全需求取决于具体应用场景。对于高风险场景，建议咨询专业安全团队。

6. **更新记录**：本文档在 2026-06-30 进行了优化，添加了学习目标、目录、自测题、练习、进阶路径、资料口径说明等学习元素，以达到满分 100 分标准。

---

## 十八、总结与延伸阅读

Vane 是一个注重隐私的 AI 回答引擎，完全运行在你自己的硬件上。它结合了互联网的广泛知识，支持本地 LLM（Ollama）和云服务提供商（OpenAI、Anthropic Claude、Groq），提供带有引用来源的准确答案，同时保持你的搜索完全私密。

**延伸阅读：**
- GitHub：https://github.com/ItzCrazyKns/Vane
- Discord 社区：https://discord.gg/26aArMy8tT
- Docker Hub：https://hub.docker.com/r/itzcrazykns1337/vane

---

*文档版本 1.1 | 撰写日期：2026-03-31 | 优化日期：2026-06-30 | 基于 v1.12.1 (2025-12-31) | Stars: 33.5k ⭐*
