---
title: "ChatDev 2.0 (DevAll)：零代码多智能体开发平台完全指南"
slug: "chatdev-multi-agent-platform-guide"
aliases:
  - /posts/tech/chatdev-multi-agent-platform-guide/
date: 2026-04-01T01:22:00+08:00
categories: ["技术笔记"]
tags: ["ChatDev", "DevAll", "多智能体", "Multi-Agent", "零代码", "YAML工作流", "Python SDK", "OpenClaw", "Docker", "Vue.js"]
description: "深度解析 ChatDev 2.0 DevAll (32.4k Stars)：OpenBMB开源的零代码多智能体编排平台，支持通过简单YAML配置构建数据可视化、3D生成、游戏开发、深度研究等工作流，采用FastAPI+Vue 3技术栈，提供Python SDK和OpenClaw集成，支持Docker一键部署。"
---

# ChatDev 2.0 (DevAll)：零代码多智能体开发平台完全指南

## §1 学习目标

完成本文档后，你将能够：

- ✅ 理解 ChatDev 2.0 的定位与设计理念
- ✅ 掌握 ChatDev 2.0 的核心功能与使用方法
- ✅ 部署和配置 ChatDev 2.0 开发环境
- ✅ 使用 Web 控制台设计和管理工作流
- ✅ 使用 Python SDK 编程执行工作流
- ✅ 集成 OpenClaw 实现高级自动化
- ✅ 扩展和自定义 ChatDev 2.0

---

## §2 项目概述

### 2.1 什么是 ChatDev 2.0 (DevAll)？

**ChatDev 2.0 (DevAll)**（[GitHub 仓库](https://github.com/OpenBMB/ChatDev)）是由 OpenBMB 团队开发的**零代码多智能体平台**，旨在实现"Developing Everything"——通过简单的配置快速构建和执行定制的多智能体系统。

**官方描述**：

> ChatDev 2.0 (DevAll) is a Zero-Code Multi-Agent Platform for "Developing Everything". It empowers users to rapidly build and execute customized multi-agent systems through simple configuration. No coding is required — users can define agents, workflows, and tasks to orchestrate complex scenarios such as data visualization, 3D generation, and deep research.

**官网**：[chatdev.top](https://chatdev.top) (如适用)

### 2.2 核心数据

| 指标 | 数值 |
|------|------|
| **Stars** | 32.4k (32,360) |
| **Forks** | 4k (4,000) |
| **Watchers** | 355 |
| **提交数** | 163 |
| **Releases** | 12 (latest: v2.2.0) |
| **贡献者** | 67 |
| **许可证** | Apache-2.0 |

### 2.3 语言分布

| 语言 | 占比 |
|------|------|
| **Python** | 68.2% |
| **Vue** | 28.7% |
| **JavaScript** | 2.4% |
| **CSS** | 0.4% |
| **Dockerfile** | 0.2% |
| **Makefile** | 0.1% |

### 2.4 ChatDev 1.0 vs 2.0

| 版本 | 定位 | 说明 |
|------|------|------|
| **ChatDev 2.0 (DevAll)** | 零代码多智能体编排平台 | 通过简单配置构建多智能体系统，适用于数据可视化、3D生成、深度研究等场景 |
| **ChatDev 1.0 (Legacy)** | 虚拟软件公司 | 模拟软件公司运作，CEO、CTO、程序员等智能体参与专业会议，自动化软件开发全流程 |

### 2.5 发展历程

| 日期 | 事件 |
|------|------|
| **Jan 07, 2026** | ChatDev 2.0 (DevAll) 正式发布 |
| **早期** | ChatDev 1.0 发布，作为多智能体协作的经典范式 |

---

## §3 核心功能详解

### 3.1 零代码多智能体编排

**核心理念**：无需编程，通过 YAML 配置文件定义智能体、工作流和任务。

**能力**：

| 能力 | 说明 |
|------|------|
| **可视化设计** | Web 控制台提供可视化工作流设计器 |
| **配置驱动** | 使用 YAML 文件定义智能体行为和交互 |
| **工作流编排** | 配置节点参数，定义上下文流，编排复杂智能体交互 |
| **实时监控** | 启动工作流，监控实时日志，检查中间产物 |
| **人工反馈** | 提供人在环（Human-in-the-Loop）反馈机制 |

### 3.2 Web 控制台

**DevAll 界面**提供无缝的构建和执行体验：

| 功能 | 说明 |
|------|------|
| **Tutorial** | 集成到平台的分步指南和文档 |
| **Workflow** | 可视化画布设计多智能体系统，拖拽配置节点参数 |
| **Launch** | 启动工作流，监控实时日志，检查中间产物，提供人工反馈 |

### 3.3 Python SDK

**轻量级 Python SDK**用于自动化和批量处理：

```python
from runtime.sdk import run_workflow

# 执行工作流并获取最终节点消息
result = run_workflow(
    yaml_file="yaml_instance/demo.yaml",
    task_prompt="Summarize the attached document in one sentence.",
    attachments=["/path/to/document.pdf"],
    variables={"API_KEY": "sk-xxxx"}  # 覆盖 .env 变量
)

if result.final_message:
    print(f"Output: {result.final_message.text_content()}")
```

**PyPI 包**：`chatdev` 可通过 `pip install chatdev` 安装

### 3.4 OpenClaw 集成

**OpenClaw 可以通过两种方式集成 ChatDev**：

| 集成方式 | 说明 |
|----------|------|
| **调用现有智能体团队** | 使用 ChatDev 已有的工作流 |
| **动态创建新团队** | 在 ChatDev 中动态创建新的多智能体团队 |

**安装 OpenClaw 技能**：

```bash
clawdhub install chatdev
```

**使用示例**：

| 场景 | 示例 |
|------|------|
| **自动化信息收集和发布** | 创建 ChatDev 工作流，自动收集趋势信息，生成小红书帖子并发布 |
| **多智能体地缘政治模拟** | 创建多智能体工作流，模拟中东局势的可能发展 |

### 3.5 Docker 部署

**Docker Compose 一键部署**：

```bash
# 从项目根目录
docker compose up --build
```

**访问地址**：
- 后端：http://localhost:6400
- 前端：http://localhost:5173

**特性**：
- 服务崩溃自动重启
- 本地文件变更会反映到容器内
- 简化依赖管理
- 提供一致的运行环境

---

## §4 工作流详解

### 4.1 工作流模板

**所有可运行的工作流配置位于 `yaml_instance/` 目录**：

| 类型 | 文件 | 说明 |
|------|------|------|
| **Demos** | `demo_*.yaml` | 展示特定功能或模块的示例 |
| **Implementations** | 直接命名 | 完整的内部或复现的工作流 |

### 4.2 数据可视化工作流

| 文件 | 说明 |
|------|------|
| `data_visualization_basic.yaml` | 基础数据可视化 |
| `data_visualization_enhanced.yaml` | 增强数据可视化 |

**示例 Prompt**：

> "Create 4–6 high quality PNG charts for my large real-estate transactions dataset."

### 4.3 3D 生成工作流

| 文件 | 说明 |
|------|------|
| `blender_3d_builder_simple.yaml` | 简单 3D 构建 |
| `blender_3d_builder_hub.yaml` | Hub 版本 3D 构建 |
| `blender_scientific_illustration.yaml` | 科学插图 3D 生成 |

**前提条件**：
- Blender 已安装
- blender-mcp 已安装

**示例 Prompt**：

> "Please build a Christmas tree."

### 4.4 游戏开发工作流

| 文件 | 说明 |
|------|------|
| `GameDev_v1.yaml` | 游戏开发 v1 |
| `ChatDev_v1.yaml` | ChatDev 风格游戏开发 |

**示例 Prompt**：

> "Please help me design and develop a Tank Battle game."

### 4.5 深度研究工作流

| 文件 | 说明 |
|------|------|
| `deep_research_v1.yaml` | 深度研究 v1 |

**示例 Prompt**：

> "Research about recent advances in the field of LLM-based agent RL"

### 4.6 教学视频工作流

| 文件 | 说明 |
|------|------|
| `teach_video.yaml` | 教学视频生成 |

**前提条件**：运行前需执行 `uv add manim`

**示例 Prompt**：

> "讲一下什么是凸优化"

---

## §5 部署与配置

### 5.1 环境要求

| 要求 | 版本 |
|------|------|
| **操作系统** | macOS / Linux / WSL / Windows |
| **Python** | 3.12+ |
| **Node.js** | 18+ |
| **包管理器** | uv (Python), npm (Node.js) |

### 5.2 安装步骤

**1. 后端依赖（Python，由 uv 管理）**：

```bash
uv sync
```

**2. 前端依赖（Vite + Vue 3）**：

```bash
cd frontend && npm install
```

### 5.3 配置

**1. 环境变量**：

```bash
cp .env.example .env
```

**2. 模型密钥**：在 `.env` 中设置 `API_KEY` 和 `BASE_URL`

**3. YAML 占位符**：在配置文件中使用 `${VAR}`（如 `${API_KEY}`）引用变量

### 5.4 运行应用

**使用 Makefile（推荐）**：

```bash
# 同时启动后端和前端
make dev
```

访问 Web 控制台：http://localhost:5173

**手动命令**：

| 服务 | 命令 |
|------|------|
| **启动后端** | `uv run python server_main.py --port 6400 --reload` |
| **启动前端** | `cd frontend && VITE_API_BASE_URL=http://localhost:6400 npm run dev` |

**实用命令**：

| 命令 | 说明 |
|------|------|
| `make help` | 显示帮助信息 |
| `make sync` | 同步 YAML 工作流到前端数据库 |
| `make validate-yamls` | 验证所有 YAML 文件的语法和模式错误 |

### 5.5 Docker 部署

```bash
# 从项目根目录
docker compose up --build
```

**访问地址**：
- 后端：http://localhost:6400
- 前端：http://localhost:5173

---

## §6 使用指南

### 6.1 Web 控制台使用

**基本流程**：

| 步骤 | 操作 |
|------|------|
| **1. 选择** | 在 Launch 标签页选择工作流 |
| **2. 上传** | 如需要，上传必要文件（如数据分析的 .csv 文件） |
| **3. Prompt** | 输入你的请求（如"Visualize the sales trends"） |
| **4. 执行** | 启动工作流并监控执行 |

### 6.2 Python SDK 使用

**编程方式执行工作流**：

```python
from runtime.sdk import run_workflow

# 执行工作流
result = run_workflow(
    yaml_file="yaml_instance/demo.yaml",
    task_prompt="Your task prompt here",
    attachments=["/path/to/file.pdf"],
    variables={"API_KEY": "your-api-key"}
)

# 获取结果
if result.final_message:
    print(result.final_message.text_content())
```

### 6.3 OpenClaw 集成使用

**安装技能**：

```bash
clawdhub install chatdev
```

**创建工作流示例**：

| 示例 | 描述 |
|------|------|
| **信息自动收集发布** | 创建 ChatDev 工作流，自动收集趋势信息，生成小红书帖子并发布 |
| **多智能体模拟** | 创建多智能体工作流，模拟特定场景的可能发展 |

---

## §7 技术架构

### 7.1 核心系统

| 模块 | 路径 | 说明 |
|------|------|------|
| **server/** | 后端核心 | FastAPI 后端服务器 |
| **runtime/** | 运行时 | 智能体抽象和工具执行 |
| **workflow/** | 工作流 | 多智能体逻辑编排 |
| **frontend/** | 前端 | Vue 3 Web 控制台 |
| **functions/** | 函数 | 自定义 Python 工具 |

### 7.2 编排系统

| 模块 | 说明 |
|------|------|
| **entity/** | 实体定义 |
| **yaml_template/** | 工作流模板 |
| **yaml_instance/** | 工作流实例 |

### 7.3 工具系统

| 模块 | 说明 |
|------|------|
| **tools/** | 内置工具 |
| **check/** | 检查工具 |
| **schema_registry/** | 模式注册表 |

### 7.4 MCP 集成

| 模块 | 说明 |
|------|------|
| **mcp_example/** | MCP 集成示例 |

---

## §8 开发扩展

### 8.1 添加新节点

在 `server/` 中定义新的节点类型，在 `workflow/` 中实现编排逻辑。

### 8.2 添加新工具

在 `functions/` 目录添加自定义 Python 工具：

```python
# functions/my_custom_tool.py
def my_custom_tool(param1: str, param2: int) -> str:
    """自定义工具描述"""
    # 实现逻辑
    return result
```

### 8.3 添加新工作流

在 `yaml_template/` 创建新的 YAML 工作流定义文件。

### 8.4 自定义提供商

在 `runtime/` 中添加新的 LLM 提供商支持。

---

## §9 最佳实践

### 9.1 工作流设计

| 实践 | 说明 |
|------|------|
| **模块化设计** | 将复杂任务分解为多个可组合的工作流 |
| **清晰的任务定义** | 使用明确的 prompt 和参数 |
| **中间产物检查** | 定期检查工作流执行中的中间产物 |
| **人工反馈** | 合理使用人在环反馈机制 |

### 9.2 性能优化

| 实践 | 说明 |
|------|------|
| **减少重启** | 生产环境中移除 `--reload` 标志 |
| **批量处理** | 使用 Python SDK 进行批量工作流执行 |
| **资源管理** | 合理配置容器资源限制 |

### 9.3 安全配置

| 实践 | 说明 |
|------|------|
| **API 密钥管理** | 使用环境变量而非硬编码 |
| **变量覆盖** | 使用 `${VAR}` 在配置文件中引用敏感信息 |
| **网络隔离** | 合理配置 Docker 网络 |

---

## §10 常见问题

### Q1：ChatDev 2.0 和 1.0 有什么区别？

ChatDev 2.0 是零代码多智能体编排平台，通过配置而非编程构建多智能体系统。ChatDev 1.0 是模拟软件公司的虚拟开发环境，智能体扮演 CEO、CTO、程序员等角色。

### Q2：如何选择合适的工作流模板？

根据任务类型选择：数据可视化用 `data_visualization_*.yaml`；3D 生成需要 Blender；游戏开发用 `GameDev_v1.yaml`；深度研究用 `deep_research_v1.yaml`。

### Q3：前端无法连接后端怎么办？

默认端口 6400 可能被占用。切换到可用端口：后端用 `--port 6401`，前端设置 `VITE_API_BASE_URL=http://localhost:6401`。

### Q4：如何自定义智能体行为？

通过 YAML 配置文件定义智能体的角色、工具和交互规则。具体参考 `yaml_template/` 中的示例文件。

### Q5：支持哪些 LLM 提供商？

支持任何兼容 OpenAI API 格式的 LLM 提供商。在 `.env` 中配置 `API_KEY` 和 `BASE_URL`。

### Q6：如何调试工作流执行？

使用 `make validate-yamls` 验证 YAML 语法，通过 Web 控制台查看实时日志和中间产物。

---

## §11 总结

### 11.1 核心优势

| 优势 | 说明 |
|------|------|
| **零代码** | 无需编程，通过配置构建多智能体系统 |
| **可视化** | Web 控制台提供直观的工作流设计 |
| **可扩展** | 模块化架构支持自定义节点、工具和工作流 |
| **多场景** | 支持数据可视化、3D生成、游戏开发、深度研究等 |
| **易部署** | Docker Compose 一键部署 |
| **OpenClaw 集成** | 与 OpenClaw 无缝集成实现高级自动化 |

### 11.2 适用场景

| 场景 | 适用工作流 |
|------|-------------|
| **数据分析** | data_visualization_*.yaml |
| **3D 建模** | blender_*.yaml |
| **游戏开发** | GameDev_v1.yaml |
| **学术研究** | deep_research_v1.yaml |
| **教育培训** | teach_video.yaml |
| **内容创作** | 自定义工作流 |

### 11.3 项目信息

| 项目 | 信息 |
|------|------|
| **Stars** | 32.4k |
| **Forks** | 4k |
| **许可证** | Apache-2.0 |
| **语言** | Python 68.2%, Vue 28.7% |
| **最新版本** | v2.2.0 |
| **最新更新** | Mar 22, 2026 |

### 11.4 相关链接

| 资源 | 链接 |
|------|------|
| **GitHub** | https://github.com/OpenBMB/ChatDev |
| **ChatDev 1.0 (Legacy)** | https://github.com/OpenBMB/ChatDev/tree/chatdev1.0 |
| **PyPI (SDK)** | https://pypi.org/project/chatdev/ |
| **论文** | arXiv:2307.07924 |

---

*文档版本 1.0 | 撰写日期：2026-04-01 | 基于 ChatDev 2.0 (32.4k Stars, Apache-2.0)*