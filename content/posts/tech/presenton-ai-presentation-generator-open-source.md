---
title: "Presenton：开源 AI 演示文稿生成器，Gamma/Beautiful.ai 的免费替代"
date: "2026-05-23T20:17:28+08:00"
slug: "presenton-open-source-ai-presentation-generator"
description: "Presenton 是一款开源 AI 演示文稿生成工具，支持自托管、本地运行、多模型提供商（OpenAI/Gemini/Claude/Ollama），可导出完整可编辑的 PPTX 文件，Apache 2.0 开源，适合需要数据隐私或避免 SaaS 订阅的团队。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "演示文稿", "开源", "自托管", "PPTX", "Electron"]
---

# Presenton：开源 AI 演示文稿生成器，Gamma/Beautiful.ai 的免费替代

做演示文稿不想被 Gamma 绑订阅？Presenton 是个值得看的选项。

这是一个开源的 AI 演示文稿生成工具，Stars 6042，Apache 2.0 许可，可以自托管、用本地模型、导出完整可编辑的 PPTX。最直接的对比：Gamma 收费版的功能，它基本都有，但不用付月费。

---

## 学习目标

读完本文后，你应该能够：

1. **理解 Presenton 的核心定位**：知道它解决什么痛点（SaaS 锁定、格式锁定），明确它的适用边界
2. **掌握部署方法**：能够通过 Docker、Electron Desktop 或云端一键部署 Presenton
3. **配置模型提供商**：能够配置 OpenAI、Gemini、Claude、Ollama 等模型提供商
4. **评估是否采用**：根据你的场景判断 Presenton 是否适合你（数据隐私、避免订阅费、本地部署）
5. **集成到工作流**：能够通过 MCP 协议将 Presenton 集成到 AI 工作流（如 Cursor、Claude Desktop）

## 目录

1. [解决什么问题](#解决什么问题)
2. [支持的模型提供商](#支持的模型提供商)
3. [部署方式](#部署方式)
   - 3.1 [Docker 部署（推荐，生产环境）](#docker-部署推荐生产环境)
   - 3.2 [Desktop 应用（Electron）](#desktop-应用electron)
   - 3.3 [云端一键部署](#云端一键部署)
4. [核心功能](#核心功能)
5. [适用边界](#适用边界)
6. [与 Gamma 的核心差异](#与-gamma-的核心差异)
7. [快速体验](#快速体验)
8. [自测题](#自测题)
9. [练习](#练习)
10. [进阶路径](#进阶路径)
11. [资料口径说明](#资料口径说明)
12. [更多资源](#更多资源)

---

## 1. 解决什么问题

AI 演示工具的痛点有两个：
- **SaaS 锁定**：Gamma、Beautiful.ai 都是云服务，数据得上传到别人服务器，有些公司出于合规不允许。
- **格式锁定**：多数 AI 演示工具只给预览或 PDF，导出的 PPTX 样式受限，想在 PowerPoint 里继续改很麻烦。

Presenton 的核心定位就是解决这两个问题：全部跑在你自己环境里，导出真正的 PPTX 文件。

---

## 2. 支持的模型提供商

Presenton 不绑任何一家 AI 提供商，支持以下方式接入：

| 类型 | 提供商 |
|------|-------|
| 云端商业模型 | OpenAI（GPT-4o）、Google Gemini、Vertex AI、Azure OpenAI、Amazon Bedrock、Anthropic Claude、Fireworks、Together AI |
| 本地开源模型 | Ollama、LM Studio |
| OpenAI API 兼容 | 任何兼容 OpenAI API 格式的端点（包括本地部署的开源模型） |

这意味着团队可以完全在本地跑，用 Ollama 跑个 Llama 3，不需要外部网络连接，适合对数据隐私有要求的环境。

---

## 3. 部署方式

### Docker 部署（推荐，生产环境）

一行命令起服务，支持 GPU 加速本地模型：

```bash
docker run -d -p 3000:3000 \
  -e OPENAI_API_KEY=your_key \
  presenton/presenton
```

然后浏览器打开 `http://localhost:3000` 即可使用。

### Desktop 应用（Electron）

支持 macOS（Apple Silicon + Intel）、Windows、Linux，有桌面客户端。可以本地配置 API key 和模型，界面和 Web 版一致。

安装步骤（macOS/Linux/Windows 通用）：

```bash
git clone https://github.com/presenton/presenton.git
cd presenton/electron
npm run setup:env   # 安装依赖、配置 uv 环境
npm run dev         # 启动开发模式
```

生成跨平台安装包：

```bash
npm run build:all
npm run dist        # 输出到 electron/dist/
```

### 云端一键部署

支持 Railway 和 DigitalOcean 一键部署，适合不想自己维护基础设施的团队：

```bash
# Railway
railway link https://github.com/presenton/presenton

# DigitalOcean
cloud.digitalocean.com/apps/new?repo=https://github.com/presenton/presenton
```

---

## 4. 核心功能

### AI 生成演示文稿

输入一段文字描述或上传文档，Presenton 会自动生成整套演示结构。可以指定风格、主题，或者让 AI 自己发挥。

### 内置 MCP 服务器

支持 Model Context Protocol（MCP），可以通过 MCP 协议调用生成演示的 API，适合在 AI 工作流里集成（比如配合 Cursor、Claude Desktop 等工具做自动化）。

### 自定义模板

支持 HTML + Tailwind CSS 创建自定义模板，可以把公司品牌样式导入进来，而不是用默认皮肤。

### 多媒体支持

- DALL-E 3 / Gemini Flash 生成配图
- Pexels / Pixabay 图库
- Icon、图表等视觉元素

### 导出格式

- **PPTX**：完整可编辑的 PowerPoint 文件，在 PowerPoint 里改没有任何限制
- **PDF**：静态导出

---

## 5. 适用边界

**适合：**
- 对数据隐私有要求（不想把内容上传到第三方 SaaS）
- 想避免订阅费（Gamma 月费不便宜）
- 需要本地部署给公司内部团队用
- 想把生成结果在 PowerPoint 里继续深度编辑
- 接入 Claude / GPT 等模型做自动化工作流（MCP 协议）

**不适合：**
- 想要开箱即用的最简部署体验（虽然 Docker 相对简单，但仍需配置）
- 完全不想碰代码/命令行，纯非技术用户（Desktop 应用体验比 Gamma 粗糙）
- 需要团队协作实时编辑（Presenton 目前偏向单人使用场景）

---

## 6. 与 Gamma 的核心差异

| 维度 | Gamma | Presenton |
|------|-------|-----------|
| 许可证 | 专有 SaaS | Apache 2.0（开源） |
| 部署 | 仅云端 | 可自托管 / 本地 / Docker |
| 数据 | 上传到 Gamma 服务器 | 可完全本地处理 |
| 导出 | PDF 为主，PPTX 有限制 | **完整可编辑 PPTX** |
| 订阅 | 月费 $10-$30 | 免费 |
| 模型 | 仅自家集成 | 自由选择（BYOK） |

---

## 7. 快速体验

不想装任何东西的可以直接访问 https://presenton.ai/ 用云端版本。最有价值的使用方式是：

1. 本地 Ollama 跑一个模型
2. Docker 起服务
3. 浏览器打开，配置 Ollama 为 provider
4. 输入提示词，让 AI 生成演示

全程不需要访问任何外部 API，数据不离开你的机器。

---

## 自测题

1. **Presenton 解决什么核心痛点？**
   <details>
   <summary>点击查看答案</summary>
   解决两个痛点：1) SaaS 锁定（数据上传到第三方服务器，合规问题）；2) 格式锁定（多数 AI 演示工具只给预览或 PDF，导出的 PPTX 样式受限）。
   </details>

2. **Presenton 支持哪些模型提供商？**
   <details>
   <summary>点击查看答案</summary>
   支持：OpenAI（GPT-4o）、Google Gemini、Vertex AI、Azure OpenAI、Amazon Bedrock、Anthropic Claude、Fireworks、Together AI、Ollama、LM Studio、任何兼容 OpenAI API 格式的端点。
   </details>

3. **如何用 Docker 部署 Presenton？**
   <details>
   <summary>点击查看答案</summary>
   ```bash
   docker run -d -p 3000:3000 \
     -e OPENAI_API_KEY=your_key \
     presenton/presenton
   ```
   然后浏览器打开 `http://localhost:3000`。
   </details>

4. **Presenton 导出的 PPTX 有什么特点？**
   <details>
   <summary>点击查看答案</summary>
   导出的是完整可编辑的 PowerPoint 文件，在 PowerPoint 里改没有任何限制（不像 Gamma 导出的 PPTX 样式受限）。
   </details>

5. **Presenton 如何通过 MCP 协议集成到 AI 工作流？**
   <details>
   <summary>点击查看答案</summary>
   在 MCP 配置中添加 Presenton 服务器：
   ```json
   {
     "mcpServers": {
       "presenton": {
         "url": "https://presenton.ai/api/mcp"
       }
     }
   }
   ```
   然后就可以通过 MCP 协议调用生成演示的 API。
   </details>

---

## 练习

### 练习 1：Docker 部署 Presenton

1. 确保 Docker 已安装
2. 运行 Presenton：`docker run -d -p 3000:3000 presenton/presenton`
3. 浏览器打开 `http://localhost:3000`
4. 配置 OpenAI API Key（或使用本地 Ollama）
5. 输入提示词，生成演示文稿
6. 导出 PPTX，在 PowerPoint 中编辑

### 练习 2：配置本地 Ollama 模型

1. 安装 Ollama：`curl -fsSL https://ollama.com/install.sh | sh`
2. 拉取模型：`ollama pull llama3.2:3b`
3. 配置 Presenton 使用 Ollama（在设置中选择 Ollama 为 provider）
4. 生成演示文稿，观察本地模型的效果

### 练习 3：通过 MCP 协议调用 Presenton

1. 在 Claude Desktop 的 MCP 配置中添加 Presenton
2. 在 Claude Desktop 中调用 Presenton 生成演示文稿
3. 观察 AI 工作流中的集成效果

---

## 进阶路径

1. **深入学习 AI 演示生成**：理解 AI 如何生成演示结构、如何设计提示词以获得更好的结果
2. **自定义 Presenton 模板**：学习 HTML + Tailwind CSS，创建自定义模板，导入公司品牌样式
3. **集成到团队工作流**：部署 Presenton 给团队使用，配置身份验证、权限管理
4. **研究 MCP 协议**：理解 Model Context Protocol，学习如何开发 MCP 服务器和客户端
5. **对比其他开源 AI 演示工具**：尝试 Rows AI、Beautiful.ai（非开源）、SlidesAI，评估优缺点

---

## 资料口径说明

1. **项目成熟度**：Presenton 是一个开源项目，成熟度可能不如 Gamma 等商业产品。本文基于 GitHub 仓库的 README 和文档，未进行深入的功能测试。
2. **模型效果**：AI 生成演示的效果取决于所使用的模型。本地模型（如 Ollama）的效果可能不如云端商业模型（如 GPT-4o）。
3. **Docker 镜像**：`presenton/presenton` 镜像可能更新频繁，请以 [Docker Hub](https://hub.docker.com/r/presenton/presenton) 的最新信息为准。
4. **MCP 协议**：MCP（Model Context Protocol）是 Anthropic 推出的协议，本文撰写时可能仍在演进，具体集成方式请参考 [MCP 官方文档](https://modelcontextprotocol.io/)。
5. **导出格式**：本文提到支持 PPTX 和 PDF，但具体导出效果可能因版本而异，以实际测试为准。
6. **许可证**：项目采用 Apache 2.0 许可证，允许自由使用、修改和分发。

---

## 8. 更多资源

- GitHub：https://github.com/presenton/presenton
- 官方文档：https://docs.presenton.ai/
- 下载 Desktop 应用：https://presenton.ai/download
- Discord 社区：https://discord.gg/9ZsKKxudNE
- YouTube 频道：https://www.youtube.com/@presentonai