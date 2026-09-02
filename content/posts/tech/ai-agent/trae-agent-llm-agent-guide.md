---
title: "Trae Agent：字节跳动 LLM 智能体完全指南"
slug: "trae-agent-llm-agent-guide"
github_repo: "bytedance/trae-agent"
aliases:
  - /posts/tech/trae-agent-llm-agent-guide/
date: "2026-09-01T01:16:00+08:00"
categories: ["技术笔记"]
tags: ["字节跳动", "软件工程", "Claude", "GPT", "Docker", "OpenAI", "Anthropic", "Python", "CLI"]
description: "深度解析 Trae Agent (约 1.2 万 Stars)：字节跳动开源的研究导向 LLM 智能体，支持 OpenAI/Anthropic/Doubao 等多提供商，提供 Lakeview 摘要、交互模式、轨迹录制等特性，采用透明模块化架构，适合研究智能体架构和开发新能力。"
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

**技术报告**：arXiv:2507.23370《Trae Agent: An LLM-based Agent for Software Engineering with Test-time Scaling》，2025-07-31 上传。作者把仓库级问题解决当成一个最优解搜索问题，用**生成（generation）、剪枝（pruning）、选择（selection）三个模块化 Agent** 组成集成推理（ensemble reasoning）：先用大模型生成一批候选方案，再剪掉明显不行的，最后选出最可靠的落地。在 SWE-bench 上与四种 SOTA 集成推理方法对比，Pass@1 平均提升 **10.22%**，并曾登顶 **SWE-bench Verified 排行榜第一名（Pass@1 = 75.20%）**。这解释了它的定位：不只是"能跑任务的 CLI"，更是验证"测试时扩展能否稳定提升软件工程任务完成率"的实验平台。

### 2.2 核心数据

| 指标 | 数值 |
|------|------|
| **Stars** | 12,059（约 1.2 万） |
| **Forks** | 1,344 |
| **许可证** | MIT |
| **语言** | Python（99.4%） |
| **官方主页** | trae.ai |

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
| 🚀 **Easy Installation** | git clone + `uv sync --all-extras` 即可运行 |

---

## §3 安装与配置

### 3.1 环境要求

| 要求 | 说明 |
|------|------|
| **Python** | 3.12+ |
| **UV** | 包管理器 |
| **API Key** | 需要选择提供商的 API key |

### 3.2 安装

```bash
# 克隆仓库
git clone https://github.com/bytedance/trae-agent.git
cd trae-agent

# 安装依赖
uv sync --all-extras

# 激活虚拟环境
source .venv/bin/activate
```

```bash
cp trae_config.yaml.example trae_config.yaml
```

### 3.3 配置

```yaml
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
  openrouter:
    api_key: your_openrouter_api_key
    provider: openai
    base_url: https://openrouter.ai/api/v1  # 走 OpenAI 兼容协议

models:
  trae_agent_model:
    model_provider: anthropic
    model: claude-sonnet-4-20250514
    max_tokens: 4096
    temperature: 0.5
```

参数读取优先级为：**命令行参数 > 配置文件 > 环境变量 > 默认值**。也就是说，命令行里显式传入的 `--provider` / `--model` 会覆盖 `trae_config.yaml`，配置文件覆盖环境变量。

### 3.4 环境变量

不想把所有配置写进 YAML 时，可以直接用环境变量：

```bash
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
```

和 OpenAI 兼容的服务（如 OpenRouter）填 `OPENAI_*` 即可；Doubao 走火山方舟，base URL 指向 `ark.cn-beijing.volces.com/api/v3/`。

### 3.5 接入 MCP 工具

在 `trae_config.yaml` 里声明 `mcp_servers`，让 Agent 能调用 MCP 客户端（这里以 Playwright 为例）：

```yaml
mcp_servers:
  playwright:
    command: npx
    args:
      - "@playwright/mcp@0.0.27"
```

### 3.6 命令行用法

`trae-cli` 提供三种入口：`run`（单次任务）、`show-config`（查看配置）、`interactive`（对话式交互）。

```bash
# 简单任务执行
trae-cli run "Create a hello world Python script"

# 检查配置
trae-cli show-config

# 交互模式
trae-cli interactive
```

指定提供商和模型：

```bash
# OpenAI
trae-cli run "Fix the bug in main.py" --provider openai --model gpt-4o

# Anthropic
trae-cli run "Add unit tests" --provider anthropic --model claude-sonnet-4-20250514

# Google Gemini
trae-cli run "Optimize this algorithm" --provider gemini --model gemini-2.5-flash

# OpenRouter（多提供商访问）
trae-cli run "Review this code" --provider openrouter --model "anthropic/claude-3-5-sonnet"

# Doubao
trae-cli run "Refactor the database module" --provider doubao --model doubao-seed-1.6

# Ollama（本地模型）
trae-cli run "Comment this code" --provider ollama --model qwen3
```

常用参数组合：

```bash
# 自定义工作目录
trae-cli run "Add tests for utils module" --working-dir /path/to/project

# 保存执行轨迹
trae-cli run "Debug authentication" --trajectory-file debug_session.json

# 强制生成补丁
trae-cli run "Update API endpoints" --must-patch

# 交互模式自定义设置
trae-cli interactive --provider openai --model gpt-4o --max-steps 30
```

### 3.7 Docker 模式

把任务放到容器里执行，避免污染本机环境：

```bash
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
```

`--docker-container-id` 与 `--working-dir` 不能同时使用；`--docker-keep` 默认为 true，设为 `false` 可在任务结束后删除容器。

### 3.8 轨迹录制

开启后的轨迹默认落在 `trajectories/` 目录，一份一个时间戳文件；需要固定文件名时用 `--trajectory-file` 指定：

```bash
# 自动生成轨迹文件
trae-cli run "Debug the authentication module"
# 保存到: trajectories/trajectory_YYYYMMDD_HHMMSS.json

# 自定义轨迹文件
trae-cli run "Optimize database queries" --trajectory-file optimization_debug.json
```

轨迹记录了 Agent 每一步的输入、中间动作与输出，适合排查 Agent 行为和分析失败原因。

## 常用命令速查

| 命令 | 作用 |
|------|------|
| `trae-cli run "<task>"` | 执行一次软件工程任务 |
| `trae-cli run "<task>" --trajectory-file debug.json` | 执行并把轨迹保存到指定文件 |
| `trae-cli show-config` | 查看当前生效的配置（含 API key 是否就绪） |
| `trae-cli interactive` | 进入对话式交互模式 |

`trae-cli run` 的常用参数：

| 参数 | 作用 |
|------|------|
| `--working-dir <path>` | 设定工作目录 |
| `--trajectory-file <file>` | 保存轨迹文件 |
| `--must-patch` | 强制要求生成补丁 |
| `--max-steps <n>` | 限制最大步数 |
| `--provider <name>` | 指定提供商（官方支持 OpenAI、Anthropic、Doubao、Azure、OpenRouter、Ollama、Google Gemini） |
| `--model <name>` | 指定模型 |
| `--docker-image <image>` | 在新 Docker 容器中运行任务 |
| `--docker-container-id <id>` | 附加到指定容器（与 `--working-dir` 互斥） |
| `--dockerfile-path <path>` | 用自定义 Dockerfile 构建环境 |
| `--docker-image-file <file>` | 用本地镜像文件（tar）构建环境 |
| `--docker-keep <bool>` | 任务结束后是否保留容器（默认保留） |

---

## 常见问题与排查

**API key 校验失败 / 报鉴权错误怎么办？**

用 `trae-cli show-config` 确认当前生效的 key 与 base URL 是否就是你配置的那份。注意配置优先级是命令行 > 配置文件 > 环境变量，如果某次运行用了 `--provider anthropic`，那么生效的就是 Anthropic 的 key，而不是配置文件里默认的那套。

**用 OpenRouter 需要单独折腾吗？**

不用。OpenRouter 提供 OpenAI 兼容接口，把它配置成 `model_providers` 里一个 `provider: openai`、`base_url: https://openrouter.ai/api/v1` 的条目即可，模型名写 `"anthropic/claude-3-5-sonnet"` 这样的 OpenRouter 格式。

**Docker 模式跑不起来？**

先确认本机已安装并启动 Docker。容器要能访问网络才能拉镜像；如果你的环境需要代理，先把代理配好再运行。`--working-dir` 与 `--docker-container-id` 不要同时使用，两者冲突。

**没有 Anthropic/OpenAI 的 key 也能试吗？**

可以。用 `--provider ollama` ＋本地模型（如 `qwen3`），或用 `--provider doubao` 接火山方舟的 Doubao，都能跑通基础流程。本地模型的质量取决于你的硬件，跑大任务时注意上下文长度。

---

## 相关资源

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | [bytedance/trae-agent](https://github.com/bytedance/trae-agent) |
| 技术报告 | [arXiv:2507.23370](https://arxiv.org/abs/2507.23370) |
| 官方主页 | [trae.ai](https://www.trae.ai/) |

---

*文档版本 2.0 | 更新日期：2026-09-01 | 基于 Trae Agent（约 1.2 万 Stars，截至 2026-09-01） | 论文：arXiv:2507.23370*