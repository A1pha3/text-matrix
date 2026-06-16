---
title: "Trae Agent：字节跳动 LLM 智能体完全指南"
slug: "trae-agent-llm-agent-guide"
aliases:
  - /posts/tech/trae-agent-llm-agent-guide/
date: "2026-04-01T01:16:00+08:00"
categories: ["技术笔记"]
tags: ["Trae Agent", "LLM智能体", "字节跳动", "软件工程", "Claude", "GPT", "Docker", "轨迹录制", "OpenAI", "Anthropic", "Python", "CLI"]
description: "深度解析 Trae Agent (11.2k Stars)：字节跳动开发的 LLM 智能体，支持 OpenAI/Anthropic/Doubao 等多提供商，提供 Lakeview 摘要、交互模式、轨迹录制等特性，采用透明模块化架构，适合研究智能体架构和开发新能力。"
---

# Trae Agent：字节跳动 LLM 智能体完全指南

> 预计阅读时间：30 分钟 | 难度：⭐⭐⭐⭐

---

## 学习目标

本文档覆盖以下内容：

- ✅ 理解 Trae Agent 的核心定位与研究导向设计理念
- ✅ 掌握 Trae Agent 的安装与配置方法
- ✅ 理解 Trae Agent 的架构设计与模块化思想
- ✅ 使用 Trae Agent 执行各类软件工程任务
- ✅ 配置多种 LLM 提供商（OpenAI/Anthropic/Doubao 等）
- ✅ 使用交互模式和 Docker 模式
- ✅ 利用轨迹录制进行调试和分析

---

## §2 项目概述

### 2.1 什么是 Trae Agent？

**Trae Agent**（[GitHub 仓库](https://github.com/bytedance/trae-agent)）是字节跳动开发的基于 LLM 的智能体，专为通用软件工程任务设计。

**官方描述**：

> Trae Agent is an LLM-based agent for general purpose software engineering tasks. It provides a powerful CLI interface that can understand natural language instructions and execute complex software engineering workflows using various tools and LLM providers.

**技术报告**：arXiv:2507.23370

### 2.2 核心数据

| 指标 | 数值 |
|------|------|
| **Stars** | 11.2k (11,215) |
| **Forks** | 1.2k (1,200+) |
| **Watchers** | 59 |
| **提交数** | 289 |
| **Issues** | 85 |
| **Pull Requests** | 32 |
| **许可证** | MIT |
| **语言** | Python 99.4% |

### 2.3 与其他 CLI 智能体的区别

**研究导向设计**是 Trae Agent 的核心特点：

> Trae Agent offers a transparent, modular architecture that researchers and developers can easily modify, extend, and analyze, making it an ideal platform for **studying AI agent architectures, conducting ablation studies, and developing novel agent capabilities**.

这使得 Trae Agent 成为：
- 研究智能体架构的理想平台
- 做消融实验的优秀工具
- 开发新智能体能力的起点

### 2.4 核心特性

| 特性 | 说明 |
|------|------|
| 🌊 **Lakeview** | 对智能体步骤提供简短摘要 |
| 🤖 **Multi-LLM Support** | 支持 OpenAI、Anthropic、Doubao、Azure、OpenRouter、Ollama、Google Gemini |
| 🛠️ **Rich Tool Ecosystem** | 文件编辑、bash 执行、顺序思考等 |
| 🎯 **Interactive Mode** | 对话式迭代开发界面 |
| 📊 **Trajectory Recording** | 详细记录所有操作用于调试分析 |
| ⚙️ **Flexible Configuration** | YAML 配置 + 环境变量支持 |
| 🚀 **Easy Installation** | pip 安装 |

---

## §3 安装与配置

### 3.1 环境要求

| 要求 | 说明 |
|------|------|
| **Python** | 3.12+ |
| **UV** | 包管理器 |
| **API Key** | 需要选择提供商的 API key |

### 3.2 安装步骤

```bash
# 克隆仓库
git clone https://github.com/bytedance/trae-agent.git
cd trae-agent

# 安装依赖
uv sync --all-extras

# 激活虚拟环境
source .venv/bin/activate
```textbash
cp trae_config.yaml.example trae_config.yaml
```textyaml
agents:
  trae_agent:
    enable_lakeview: true
    model: trae_agent_model  # 模型配置名称
    max_steps: 200  # 最大步数

model_providers:
  anthropic:
    api_key: your_anthropic_api_key
    provider: anthropic
  openai:
    api_key: your_openai_api_key
    provider: openai

models:
  trae_agent_model:
    model_provider: anthropic
    model: claude-sonnet-4-20250514
    max_tokens: 4096
    temperature: 0.5
```textyaml
openai:
  api_key: your_openrouter_api_key
  provider: openai
  base_url: https://openrouter.ai/api/v1
```textbash
# OpenAI
export OPENAI_API_KEY="your-openai-api-key"
export OPENAI_BASE_URL="your-openai-base-url"

# Anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export ANTHROPIC_BASE_URL="your-anthropic-base-url"

# Google Gemini
export GOOGLE_API_KEY="your-google-api-key"
export GOOGLE_BASE_URL="your-google-base-url"

# OpenRouter
export OPENROUTER_API_KEY="your-openrouter-api-key"
export OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"

# Doubao
export DOUBAO_API_KEY="your-doubao-api-key"
export DOUBAO_BASE_URL="https://ark.cn-beijing.volces.com/api/v3/"
```textyaml
mcp_servers:
  playwright:
    command: npx
    args:
      - "@playwright/mcp@0.0.27"
```text
命令行参数 > 配置文件 > 环境变量 > 默认值
```textbash
# 简单任务执行
trae-cli run "Create a hello world Python script"

# 检查配置
trae-cli show-config

# 交互模式
trae-cli interactive
```textbash
# OpenAI
trae-cli run "Fix the bug in main.py" --provider openai --model gpt-4o

# Anthropic
trae-cli run "Add unit tests" --provider anthropic --model claude-sonnet-4-20250514

# Google Gemini
trae-cli run "Optimize this algorithm" --provider google --model gemini-2.5-flash

# OpenRouter（多提供商访问）
trae-cli run "Review this code" --provider openrouter --model "anthropic/claude-3-5-sonnet"

# Doubao
trae-cli run "Refactor the database module" --provider doubao --model doubao-seed-1.6

# Ollama（本地模型）
trae-cli run "Comment this code" --provider ollama --model qwen3
```textbash
# 自定义工作目录
trae-cli run "Add tests for utils module" --working-dir /path/to/project

# 保存执行轨迹
trae-cli run "Debug authentication" --trajectory-file debug_session.json

# 强制生成补丁
trae-cli run "Update API endpoints" --must-patch

# 交互模式自定义设置
trae-cli interactive --provider openai --model gpt-4o --max-steps 30
```textbash
# 在新容器中运行任务
trae-cli run "Add tests for utils module" --docker-image python:3.11

# 新容器并挂载目录
trae-cli run "Write a script to print helloworld" --docker-image python:3.12 --working-dir test_workdir/

# 附加到现有容器（按 ID）
trae-cli run "Update API endpoints" --docker-container-id 91998a56056c

# 指定 Dockerfile 构建环境
trae-cli run "Debug authentication" --dockerfile-path test_workspace/Dockerfile

# 指定本地 Docker 镜像文件
trae-cli run "Fix the bug in main.py" --docker-image-file test_workspace/trae_agent_custom.tar

# 任务完成后删除容器
trae-cli run "Add tests for utils module" --docker-image python:3.11 --docker-keep false
```textbash
trae-cli interactive
```textyaml
agents:
  trae_agent:
    enable_lakeview: true
```textbash
# 自动生成轨迹文件
trae-cli run "Debug the authentication module"
# 保存到: trajectories/trajectory_YYYYMMDD_HHMMSS.json

# 自定义轨迹文件
trae-cli run "Optimize database queries" --trajectory-file optimization_debug.json
```text
trae-agent/
├── .github/              # GitHub 配置
├── .vscode/              # VS Code 配置
├── docs/                 # 文档
├── evaluation/           # 评估框架
├── server/               # 服务器组件
├── tests/                # 测试
├── trae_agent/           # 核心源代码
├── pyproject.toml        # Python 项目配置
├── Makefile             # 构建脚本
├── trae_config.yaml.example  # 配置示例
├── trae_config.json.example # JSON 配置示例
└── uv.lock              # 依赖锁定
```textbash
# 验证 API keys
trae-cli show-config
```textbash
# 查看 CONTRIBUTING
cat CONTRIBUTING.md
```textbash
trae-cli run "Your task" --trajectory-file debug.json
```textbash
trae-cli run "<task>"           # 执行任务
trae-cli show-config            # 显示配置
trae-cli interactive            # 交互模式
```textbash
--working-dir <path>            # 工作目录
--trajectory-file <file>        # 轨迹文件
--must-patch                    # 强制补丁
--max-steps <n>                 # 最大步数
--provider <name>               # 提供商
--model <name>                  # 模型
```textbash
--docker-image <image>          # Docker 镜像
--docker-container-id <id>      # 容器 ID
--dockerfile-path <path>         # Dockerfile 路径
--docker-image-file <file>      # 镜像文件
--docker-keep <bool>            # 保留容器
```

---

*文档版本 1.0 | 撰写日期：2026-04-01 | 基于 Trae Agent (11.2k Stars) | 论文：arXiv:2507.23370*