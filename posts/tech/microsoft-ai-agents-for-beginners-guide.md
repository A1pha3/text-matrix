---
title: "微软 62K Stars AI Agent 入门课：零基础搭建你的第一个智能体"
date: 2026-05-17T20:15:00+08:00
categories:
  - 技术笔记
tags:
  - AI Agent
  - Microsoft
  - Azure AI Foundry
  - 教程
  - GitHub
---

# 微软 62K Stars AI Agent 入门课：零基础搭建你的第一个智能体

> GitHub 斩获 **62,000+ Stars**，微软出品，必属精品。这门课带你从零入门 AI Agent 开发，涵盖工具调用、Agentic RAG、多智能体协作等核心设计模式。

![AI Agents for Beginners](https://github.com/microsoft/ai-agents-for-beginners/raw/main/images/repo-thumbnailv2.png)

## 📌 项目概览

| 指标 | 数据 |
|------|------|
| **仓库** | [microsoft/ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners) |
| **Stars** | 62,106 ⭐ |
| **Forks** | 20,974 |
| **课程语言** | 50+（含简体中文） |
| **代码框架** | Microsoft Agent Framework (MAF) + Azure AI Foundry Agent Service V2 |

## 🎯 这门课学什么？

18 节课程，覆盖 AI Agent 开发全链路：

| 课时 | 主题 |
|------|------|
| 01 | AI Agent 简介与使用场景 |
| 02 | 主流 Agentic 框架对比 |
| 03 | Agentic 设计模式理解 |
| 04 | **工具调用**（Tool Use）设计模式 |
| 05 | **Agentic RAG** — 检索增强生成 |
| 06 | 构建可信赖的 AI Agent |
| 07 | **规划**（Planning）设计模式 |
| 08 | **多智能体**（Multi-Agent）协作 |
| 09 | **元认知**（Metacognition）设计模式 |
| 10 | AI Agent 生产部署 |
| 11 | 代理协议：MCP、A2A、NLWeb |
| 12 | 上下文工程（Context Engineering） |
| 13 | Agent 记忆管理 |
| 14 | Microsoft Agent Framework 详解 |
| 15 | 计算机操控 Agent（CUA） |
| 16 | 可扩展 Agent 部署（Coming Soon） |
| 17 | 本地 AI Agent（Coming Soon） |
| 18 | AI Agent 安全实践 |

每节配有 Jupyter Notebook + 讲解视频，理论实战两不误。

## 🚀 快速上手（Quick Start）

### 环境要求

- Python 3.12+
- .NET 10 SDK（部分示例需要）
- Azure CLI（`az login` 认证）
- Microsoft Foundry 项目（含已部署模型，如 `gpt-4o`）
- 备选：MiniMax（支持 204K 超大上下文）

### Step 1：克隆仓库

```bash
# 推荐：浅克隆（不含历史，速度快）
git clone --depth 1 https://github.com/microsoft/ai-agents-for-beginners.git
cd ai-agents-for-beginners

# 只下载特定课时（如只需要前两节）
git clone --depth 1 --filter=blob:none --sparse https://github.com/microsoft/ai-agents-for-beginners.git
cd ai-agents-for-beginners
git sparse-checkout set 00-course-setup 01-intro-to-ai-agents
```

### Step 2：创建 Python 虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate    # Windows

pip install -r requirements.txt
```

### Step 3：配置 Azure 认证

```bash
az login
# 无浏览器环境用：
az login --use-device-code
```

### Step 4：创建 `.env` 文件

```bash
cp .env.example .env
# 填入你的项目信息：
# AZURE_AI_FOUNDRY_ENDPOINT=https://your-project.ai.azure.com
# AZURE_AI_FOUNDRY_DEPLOYMENT_NAME=gpt-4o
```

### Step 5：打开 Notebook 开始实验

```bash
# 在 VSCode 或 Jupyter Lab 中打开
code .
# 或直接启动 Jupyter
jupyter notebook
```

### 使用 MiniMax（备选方案，无需 Azure）

如不想使用 Azure，可配置 MiniMax 作为 OpenAI 兼容 provider：

```python
# 在 .env 中加入
MINIMAX_API_KEY=your_minimax_key
OPENAI_API_BASE=https://api.minimaxi.com/v1
OPENAI_MODEL=abab6.5s-chat
```

## 🔑 核心设计模式速览

### 1. 工具调用（Tool Use）
Agent 通过调用外部工具（搜索、计算、API）扩展能力，而非仅靠 LLM 自身知识。
```python
# MAF 示例
agent = AzureAIAgent(
    instructions="你是一个研究助手，可以搜索网络获取最新资讯。",
    tools=[web_search_tool, calculator_tool]
)
```

### 2. Agentic RAG
在检索-生成流程中嵌入 Agent 决策：判断是否需要检索、从哪里检索、如何融合结果。
```
Query → Agent 判断 → 检索 → Agent 融合 → 生成答案
```

### 3. 多智能体协作（Multi-Agent）
多个专精 Agent 分工合作：规划 Agent、分析 Agent、执行 Agent各司其职，通过消息传递协作完成复杂任务。

### 4. 元认知（Metacognition）
Agent 在行动前**反思**：这步合理吗？有没有更优策略？通过内置评估循环提升输出质量。

## 💬 支持与社区

- **Discord**：微软 Foundry 社区专属频道 → [加入](https://aka.ms/ai-agents/discord)
- **GitHub Issues**：发现 bug 或有建议 → [提 Issue](https://github.com/microsoft/ai-agents-for-beginners/issues)
- **多语言**：课程已翻译为 50+ 语言，简体中文版见 `translations/zh-CN/` 目录

## 📎 相关资源

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | [microsoft/ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners) |
| Azure AI Foundry | [aka.ms/ai-agents-beginners/ai-foundry](https://aka.ms/ai-agents-beginners/ai-foundry) |
| Microsoft Agent Framework | [aka.ms/ai-agents-beginners/agent-framework](https://aka.ms/ai-agents-beginners/agent-framework) |
| 关联课程：Generative AI for Beginners | [aka.ms/genai-beginners](https://aka.ms/genai-beginners) |

---

*课程持续更新中，Deploying Scalable Agents 和 Creating Local AI Agents 等课时即将上线。*