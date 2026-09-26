---
title: "ChatDev 2.0 (DevAll)：把多智能体协作搬进 YAML 的零代码平台"
slug: "chatdev-multi-agent-platform-guide"
github_repo: "OpenBMB/ChatDev"
source_key: "gh:OpenBMB/ChatDev"
aliases:
  - /posts/tech/chatdev-multi-agent-platform-guide/
date: "2026-04-01T01:22:00+08:00"
lastmod: "2026-09-24T00:00:00+08:00"
categories: ["技术笔记"]
tags: ["多智能体", "Multi-Agent", "OpenClaw", "Docker"]
description: "深度解析 ChatDev 2.0 DevAll (34.3k Stars)：OpenBMB 开源的零代码多智能体编排平台，支持通过简单 YAML 配置构建数据可视化、3D 生成、游戏开发、深度研究等工作流，采用 FastAPI + Vue 3 技术栈，提供 Python SDK 和 OpenClaw 集成，支持 Docker 一键部署。"
---

# ChatDev 2.0 (DevAll)：把多智能体协作搬进 YAML 的零代码平台

> ChatDev 2.0 真正解决的问题不是"又一个多智能体框架"——它把智能体协作从代码层抽到配置层，让非开发者也能用 YAML 定义工作流、用 Web 控制台拖拽编排，同时保留 Python SDK 给需要批量和定制的场景。本文从平台设计出发，拆解它的编排模型、工作流机制和扩展方式，最后给出什么时候该用它、什么时候不该用的判断。

这篇文章回答四个问题：

- ChatDev 2.0 和 1.0 在设计思路上有什么根本区别？
- 一个典型工作流从 YAML 定义到执行完成，中间经过哪些环节？
- 什么场景适合用 Web 控制台，什么场景更适合用 Python SDK？
- 如果你想在 ChatDev 里加自己的工具或节点，需要改哪些地方？

## 系统地图

ChatDev 2.0 的几块主要拼图：

| 层次 | 组件 | 角色 |
|------|------|------|
| **配置层** | `yaml_instance/`、`yaml_template/` | 工作流定义（智能体角色、工具、拓扑）；`yaml_template/design.yaml` 是配置 schema 参考 |
| **运行时** | `runtime/` (Python SDK) | 解析配置、实例化智能体、驱动执行、管理上下文 |
| **编排层** | `workflow/` | 节点调度、消息路由、中间产物管理 |
| **服务层** | `server/` (FastAPI) | REST API，连接前端与运行时 |
| **交互层** | `frontend/` (Vue 3) | Web 控制台：可视化设计、启动、监控 |
| **工具层** | `functions/`、`tools/` | 可插拔的 Python 工具和检查函数 |

分工可以压缩成一句话：**配置定义"做什么"，运行时负责"怎么做"**。用户写 YAML 描述智能体角色和工作流拓扑，运行时拿到配置后实例化智能体、注入工具、按拓扑调度执行——整个过程不需要用户写任何编排代码。

---

## 项目背景

### ChatDev 1.0 → 2.0：从模拟公司到通用平台

ChatDev 1.0 的设计思路是模拟一家软件公司：CEO 拆需求、CTO 做技术决策、程序员写代码、测试跑用例——它用多智能体对话复现了软件开发的完整流程。

ChatDev 2.0 (DevAll) 把"多智能体协作"抽象成了一套通用编排框架。它不再预设"软件公司"这个场景，而是让你用 YAML 定义任意角色和交互拓扑，跑数据可视化、3D 生成、游戏开发、深度研究等各种工作流。

| 维度 | ChatDev 1.0 | ChatDev 2.0 (DevAll) |
|------|-------------|----------------------|
| 设计理念 | 模拟软件公司运作 | 通用多智能体编排平台 |
| 使用方式 | 预定义角色和流程 | YAML 配置 + Web 控制台 + Python SDK |
| 适用场景 | 自动化软件开发 | 数据可视化、3D 生成、游戏、研究等 |
| 技术栈 | Python | Python (FastAPI) + Vue 3 |

时间线：ChatDev 2.0 (DevAll) 于 2026 年 1 月 7 日正式发布，经典版（v1.x）移入 `chatdev1.0` 分支维护。此后迭代了 v2.1.0（2026 年 1 月）和 v2.2.0（2026 年 3 月）两个版本。

### 项目概况

ChatDev 2.0 由 OpenBMB 团队开发，Apache-2.0 协议开源。以下数字核对于 2026-09-24（GitHub API）：[GitHub 仓库](https://github.com/OpenBMB/ChatDev) 34.3k Stars、4.3k Forks，main 分支 205 次提交，最新版本 v2.2.0（2026 年 3 月）。代码以 Python 为主（68.5%），前端用 Vue 3（28.7%），少量 JavaScript、CSS 和 Docker 配置。

ChatDev 1.0 代码仍保留在 [chatdev1.0 分支](https://github.com/OpenBMB/ChatDev/tree/chatdev1.0)，论文见 arXiv:2307.07924。仓库同时提供[中文 README](https://github.com/OpenBMB/ChatDev/blob/main/README-zh.md)。

> ChatDev 2.0 (DevAll) is a **Zero-Code Multi-Agent Platform** for "Developing Everything". It empowers users to rapidly build and execute customized multi-agent systems through simple configuration. No coding is required—users can define agents, workflows, and tasks to orchestrate complex scenarios such as data visualization, 3D generation, and deep research.

---

## 核心机制

### 配置模型：一个 YAML 文件就是一个工作流

ChatDev 2.0 的编排模型分三层：

**工作流层** (`yaml_instance/`)：每个 `.yaml` 文件就是一个完整的工作流定义——有哪些智能体节点、每个节点挂什么工具、节点之间怎么连接、节点角色的 system prompt 是什么。

**模板层** (`yaml_template/`)：当前仓库只有一个 `design.yaml`，它不是工作流模板，而是配置的 schema 参考——列出 `version`、`vars`、`graph`、`nodes`、`config` 等字段的合法类型与可选值，写 YAML 时对照它避免踩格式错误。

**运行时** (`runtime/`)：解析工作流文件，实例化智能体，按拓扑顺序调度执行。执行过程中产生的消息、中间文件、状态变化都通过 Web 控制台或 SDK 暴露出来。

节点类型在 schema 里有 8 种：`model`、`agent`、`human`、`subgraph`、`python`、`passthrough`、`literal`、`loop_counter`。常用的几种：`agent` 节点跑一次 LLM 调用，`python` 节点在本地执行代码，`subgraph` 节点把另一张图当作子流程嵌进来，`human` 节点把人工反馈编进流程。

`human` 节点值得单独说一句。它是显式写进 YAML 的一个节点，执行到它就暂停，等你在控制台输入；输入会作为这个节点的输出，沿着边传给下游。仓库自带的 `demo_human.yaml` 就是个三节点例子：writer 智能体生成文章 → human 节点收修改意见 → editor 智能体按意见润色，writer 的原文还会通过另一条边直接送到 editor 手里，方便对照修改。

这种"一个文件描述一个工作流"的约定带来一个直接好处：团队可以维护一套工作流文件库，不同任务只需复制现有 YAML 改参数，不改运行时逻辑。

### Web 控制台

Web 控制台（Vue 3）提供三个核心界面，本质上是对配置和运行时的图形化封装：

- **Tutorial**：内嵌的分步指南，覆盖从创建第一个工作流到调试执行的完整流程。
- **Workflow**：可视化画布（基于 Vue Flow），拖拽节点、配置参数、定义节点间的上下文传递。
- **Launch**：启动工作流，实时查看每个节点的执行日志和中间产物，并支持人工介入反馈。

画布和 YAML 是同一套配置的两个入口：`yaml_instance/` 下的 YAML 文件通过 `make sync` 上传到服务端数据库后，就可以在控制台里查看和启动；画布上保存的编排图也存进服务端数据库，启动时走的是同一个运行时入口。一次典型操作是：在 **Launch** 标签页选择工作流 → 上传必要附件（如数据分析的 `.csv`）→ 输入任务描述（如 "Visualize the sales trends"）→ 启动并监控执行过程，中间产物实时可见。

### Python SDK

当你需要批处理、CI/CD 集成或程序化控制时，Python SDK 比 Web 控制台更合适：

```python
from runtime.sdk import run_workflow

result = run_workflow(
    yaml_file="yaml_instance/demo_code.yaml",
    task_prompt="Summarize the attached document in one sentence.",
    attachments=["/path/to/document.pdf"],
    variables={"API_KEY": "sk-xxxx"},
    session_name="my_first_run",
    log_level="INFO",
)

if result.final_message:
    print(f"Output: {result.final_message.text_content()}")
```

`run_workflow` 的完整签名支持 `yaml_file`、`task_prompt`、`attachments`、`session_name`、`fn_module`、`variables` 和 `log_level` 七个参数，其中 `task_prompt` 和 `attachments` 至少给一个。返回的 `result` 对象（`WorkflowRunResult`）包含两部分：最终消息 `final_message`，以及 `meta_info`——里面有会话名、输出目录 `output_dir`（产物落在 `WareHouse/` 下）、token 用量 `token_usage` 和结构化输出 `outputs`。

SDK 也发布到了 PyPI：`pip install chatdev`（截至 2026-09-24 最新版本为 0.1.0）。

### OpenClaw 集成

OpenClaw 可以通过两种方式调用 ChatDev：

- **调用已有工作流**：把 ChatDev 里配好的智能体团队当作一个可远程调用的能力单元。
- **动态创建新团队**：让 OpenClaw 在运行时根据任务描述自动生成 ChatDev 工作流配置并执行。

```bash
clawdhub install chatdev
```

前提是 ChatDev 2.0 后端已在运行。README 给了两个官方示例，一个是"创建一个 ChatDev 工作流，自动收集热点信息、生成小红书帖子并发布"，另一个是"用多个智能体模拟中东局势的可能走向"。前者就是典型的内容自动化流水线：把日常的信息收集、成稿、发布交给固定工作流，OpenClaw 负责触发和串联。

### Docker 部署

```bash
docker compose up --build
```

启动后后端在 `http://localhost:6400`，前端在 `http://localhost:5173`（可通过 `FRONTEND_PORT` 环境变量改端口）。Compose 配置了 `restart: unless-stopped` 自动重启，并把项目目录挂载进容器，改代码后容器内同步生效。运行前记得先准备好 `.env` 文件。

---

## 一个任务如何流过系统

在罗列工作流模板之前，先看一个完整案例——用"数据可视化"工作流把一份 CSV 变成图表，理解 ChatDev 的调度链路：

1. **选择定义**：`data_visualization_enhanced_v2.yaml` 定义了一条带反馈回路的链路，主要角色有 Visualization Planner、Data Cleaner、Visualization Programmer、Visual Expert、Data Analyst，配合若干 `python` 执行器节点。
2. **创建实例**：用户在 Launch 界面选择该工作流，上传 `transactions.csv`，输入 prompt："Create 4–6 high quality PNG charts for my large real-estate transactions dataset."
3. **运行时调度**：`runtime/` 解析 YAML 实例，为每个节点实例化对应的 agent 或 python 执行器，注入配置中声明的函数工具（如 `load_file`、`read_text_file_snippet`），按拓扑顺序执行：
   - Visualization Planner：检查数据文件，输出「可视化需求单」。
   - Data Cleaner + Cleaning Executor：生成并执行清洗代码，产出 `_cleaned` 文件。
   - Visualization Programmer + Visualization Executor：生成并执行绘图代码，产出 PNG 图表。
   - Visual Expert：加载图表检查可读性和数据映射，输出 `NEXT_STEP: CONTINUE/STOP`，决定是否再迭代一轮绘图；此外还有 MetaData Analyst 负责数据画像、Concluder 负责收尾总结。
   - Data Analyst：综合元数据与清洗状态，决定下一步走 CLEAN 还是 VISUALIZE。
4. **产物交付**：PNG 文件写入工作目录，Web 控制台显示每个节点的日志和中间产物，SDK 调用者通过 `result.final_message` 拿到结果。

这个流程里，用户没有写一行 Python 代码——所有逻辑由 YAML 定义和运行时驱动。

## 内置工作流一览

所有可运行的工作流配置在 `yaml_instance/` 目录下，分为 Demo（`demo_*.yaml`）和完整实现（直接命名的文件）。`demo_*` 系列有 17 个，除了基本用法，还覆盖子图（`demo_sub_graph.yaml`）、记忆（`demo_mem0_memory.yaml`、`demo_file_memory.yaml` 等）、MCP（`demo_mcp.yaml`）、多数投票（`demo_majority_voting.yaml`）、循环（`demo_loop_counter.yaml`）、人工介入（`demo_human.yaml`）等能力，想学某种机制直接看对应的 demo 最快。

完整实现里的关键文件：

| 类型 | 关键文件 | 说明 |
|------|----------|------|
| **数据可视化** | `data_visualization_basic.yaml`、`data_visualization_enhanced_v2.yaml`、`data_visualization_enhanced_v3.yaml` | 基础版和增强版，支持 CSV → 图表 |
| **3D 生成** | `blender_3d_builder_simple.yaml`、`blender_3d_builder_hub.yaml`、`blender_scientific_illustration_image_gen.yaml` | 需要本地装 Blender + blender-mcp |
| **游戏开发** | `GameDev_with_manager.yaml`、`ChatDev_v1.yaml` | 带经理角色的协作开发流程 |
| **深度研究** | `deep_research_v1.yaml` | 面向学术文献调研和综述生成 |
| **教学视频** | `teach_video.yaml` | 基于 Manim 生成数学/算法讲解视频（运行前需 `uv add manim`） |
| **通用问题解决** | `general_problem_solving_team.yaml` | 通用问题解决专家小组（需求拆解、推理、方案、实现、审核） |
| **ReAct / Reflexion** | `react.yaml`、`reflexion_product.yaml` | ReAct 多轮工具调用、Reflexion 迭代式营销头脑风暴 |
| **技能调用** | `skills.yaml` | 演示 Agent Skills 用法的工作流 |
| **子图编排** | `MACNet_v1.yaml` | 链式组合多个 subgraph 节点的示例 |

### 各工作流示例 Prompt

| 工作流 | 示例 Prompt |
|---------|-------------|
| 数据可视化 | "Create 4–6 high quality PNG charts for my large real-estate transactions dataset." |
| 3D 生成 | "Please build a Christmas tree." |
| 游戏开发 | "Please help me design and develop a Tank Battle game." |
| 深度研究 | "Research about recent advances in the field of LLM-based agent RL" |
| 教学视频 | "讲一下什么是凸优化" |

---

## 部署与配置

### 环境要求

| 组件 | 版本要求 |
|------|----------|
| 操作系统 | macOS / Linux / WSL / Windows |
| Python | 3.12（pyproject 约束 `>=3.12,<3.13`，3.13 及以上装不上依赖；README 简写的"3.12+"以约束为准） |
| Node.js | 20.19+（Vite 7 要求；README 标 18+ 已过时） |
| 包管理器 | uv (Python), npm (Node.js) |

### 安装

```bash
uv sync                           # Python 后端依赖
cd frontend && npm install        # Vue 3 前端依赖
```

### 配置

```bash
cp .env.example .env
```

在 `.env` 中配置 `BASE_URL` 和 `API_KEY`。`.env.example` 内置了 OpenAI、Gemini、LM Studio、Ollama 四类提供商的示例地址（如 LM Studio 用 `http://localhost:1234/v1`、Ollama 用 `http://localhost:11434/v1`），凡是兼容 OpenAI API 格式的提供商都可以接入。YAML 配置文件中用 `${VAR}` 引用这些变量（如 `${API_KEY}`）。

`.env.example` 里还有两个可选项：`SERPER_DEV_API_KEY`（接 [serper.dev](https://serper.dev) 的搜索服务）和 `JINA_API_KEY`（接 [jina.ai](https://jina.ai) 的网页阅读服务）。对应运行时里的 `web_search`、`get_webpage_content` 等内置工具——深度研究这类工作流要用到联网能力，就得配这两个 key。

### 启动

```bash
make dev    # 同时启动前后端
```

访问 `http://localhost:5173`。

手动启动（适用于需要自定义端口或调试的场景）：

| 服务 | 命令 |
|------|------|
| 后端 | `uv run python server_main.py --port 6400 --reload` |
| 前端 | `cd frontend && VITE_API_BASE_URL=http://localhost:6400 npm run dev` |

`--reload` 只监视后端 Python 源码目录，智能体产物目录不会再触发重启；需要更细粒度时可以传 `--reload-dir` 或 `--reload-exclude`。

其他命令：

| 命令 | 作用 |
|------|------|
| `make help` | 显示所有可用命令 |
| `make sync` | 把 `yaml_instance/` 下的工作流上传到服务端 VueGraph 数据库（前端才能加载到最新配置） |
| `make validate-yamls` | 校验所有 YAML 文件的语法和结构 |
| `make stop` | 停掉前后端进程（释放 6400 / 5173 端口） |
| `make check-backend` | 跑后端测试 + lint（pytest + ruff） |

---

## 技术架构

| 模块 | 职责 |
|------|------|
| `server/` | 后端核心，FastAPI 服务器，REST API |
| `runtime/` | 运行时，智能体抽象、工具注入、执行调度 |
| `workflow/` | 多智能体编排逻辑，图的执行引擎 |
| `frontend/` | Vue 3 Web 控制台 |
| `functions/` | 可自定义的 Python 工具 |
| `entity/` | 智能体和节点的数据结构定义 |
| `yaml_template/` | 配置 schema 参考（`design.yaml`） |
| `yaml_instance/` | 面向具体任务的工作流配置实例 |
| `tools/` | 仓库维护脚本（YAML 校验、配置同步等） |
| `check/` | 工作流校验和诊断 |
| `schema_registry/` | 工具和节点的模式注册 |
| `mcp_example/` | MCP 集成示例 |

`docs/user_guide/en/` 下有官方开发者文档，按主题组织：工作流编写（`workflow_authoring.md`）、Web UI 指南（`web_ui_guide.md`）、执行逻辑（`execution_logic.md`）、字段规格（`field_specs.md`），以及 memory、thinking、tooling 三个模块的专项说明。二次开发前先读这一手材料，比读源码省时间。

---

## 开发扩展

### 添加新节点

在 `yaml_instance/` 中新建或修改 YAML 文件，按 `yaml_template/design.yaml` 的 schema 定义节点类型和拓扑连接。运行时类型定义在 `entity/`、调度逻辑在 `workflow/`。

### 添加新工具

工具按功能归类放在 `functions/` 的子目录（如 `function_calling/`）下：

```python
# functions/function_calling/my_custom_tool.py
def my_custom_tool(param1: str, param2: int) -> str:
    """自定义工具描述"""
    # 实现逻辑
    return result
```

在 YAML 的 `tooling.config.tools` 中按名称注册（如 `- name: my_custom_tool`），运行时即可注入给 agent 节点调用。

内置函数工具有 17 个（清单见 `design.yaml`）：文件操作类有 `load_file`、`save_file`、`move_path`、`rename_path`、`list_directory`、`iter_workspace_entries`、`search_in_files`、`read_file_segment`、`read_text_file_snippet`、`describe_available_files`；执行类有 `init_python_env`、`install_python_packages`、`uv_run`；联网类有 `web_search`、`get_webpage_content`；还有 `get_city_num`、`get_weather` 两个示例工具。自己写工具时，函数签名和 docstring 就是对 LLM 暴露的接口描述，写清楚参数含义比写实现更要紧。

### 添加新工作流

在 `yaml_instance/` 创建新的 YAML 文件，参考 `data_visualization_basic.yaml` 等现有实例的结构。改完后运行 `make validate-yamls` 检查语法，再 `make sync` 同步到服务端数据库，前端才能看到。

### 自定义提供商

若提供商兼容 OpenAI API 格式，直接配置 `.env` 中的 `BASE_URL` 和 `API_KEY` 即可；不兼容的提供商需要在 `runtime/` 的 provider 抽象下添加适配。

---

## 推荐做法

**工作流设计**：把复杂任务拆成多个可组合的小工作流，不要塞进一个大 YAML。任务描述写清楚输入、输出和约束——减少智能体误判。定期检查中间产物，大部分问题在中间节点就已经暴露。对生成类任务（图表、3D、视频），在链路里显式放一个 `human` 节点做中间确认，比整条跑完再返工便宜得多——数据可视化工作流里 Visual Expert 的 CONTINUE/STOP 回路就是同样的思路，只是把"看一眼"交给了模型。

**性能**：生产环境去掉 `--reload` 标志。批量任务走 Python SDK，比反复操作 Web 控制台高效。Docker 部署时设合理的 CPU/内存限制。

**安全**：API 密钥只放 `.env`，用 `${VAR}` 在 YAML 中引用，永远不要硬编码。Docker 网络按需配置，避免把开发端口直接暴露到公网。

---

## 常见问题

### Q1：ChatDev 2.0 和 1.0 的核心区别是什么？

1.0 是固定场景（模拟软件公司），角色和流程预定义。2.0 是通用编排平台——你用 YAML 定义任意角色和交互拓扑，平台负责调度执行。

### Q2：怎么选工作流模板？

看任务类型：数据可视化 → `data_visualization_*.yaml`；3D 生成 → `blender_*.yaml`（需要本地装 Blender）；游戏开发 → `GameDev_with_manager.yaml`；文献调研 → `deep_research_v1.yaml`。没有匹配的模板就自己写一个。

### Q3：前端连不上后端？

默认端口 6400 可能被占用。后端换端口：`--port 6401`，前端同步设置 `VITE_API_BASE_URL=http://localhost:6401`。

### Q4：怎么自定义智能体行为？

在 YAML 配置里定义智能体的角色描述、可用工具和交互规则。字段结构参考 `yaml_template/design.yaml`，完整写法参考 `yaml_instance/` 下的现有工作流。

### Q5：支持哪些 LLM？

任何兼容 OpenAI API 格式的提供商。在 `.env` 里配 `API_KEY` 和 `BASE_URL` 就行。

### Q6：怎么调试工作流？

`make validate-yamls` 检查 YAML 语法。Web 控制台的 Launch 界面可以逐节点查看日志和中间产物。

---

## 什么时候用、什么时候不用

ChatDev 2.0 适合的场景：

- 你想快速验证一个多智能体协作方案，不想从零写编排代码。
- 团队里有非开发者需要参与工作流设计和执行（Web 控制台）。
- 工作流模式相对固定，主要变化是输入数据不同（模板 + 实例分离）。
- 需要把多智能体能力嵌入到自动化流程里（Python SDK + OpenClaw）。

不太适合的场景：

- 智能体之间的交互逻辑非常复杂、需要大量条件分支和动态路由——YAML 的表达能力有上限，这类逻辑用代码写状态机更直接。
- 你对延迟和吞吐有苛刻要求——ChatDev 的调度层增加了一层抽象开销。
- 你的工作流高度依赖某个特定框架的内部机制（如 LangGraph 的状态图、AutoGen 的对话模式）——ChatDev 是独立编排模型，迁移成本不低。

如果决定用，建议的采用顺序是：

1. **先跑 Demo**：从 `demo_*.yaml` 开始，理解 YAML 结构和运行时行为。
2. **改模板**：基于 Demo 模板改一个自己场景的简单版本，验证能跑通。
3. **上 SDK**：需要批量或集成时，把流程切到 Python SDK。
4. **加自定义工具**：在 `functions/` 里写自己的工具函数，注册到工作流。
5. **考虑 OpenClaw**：当需要把 ChatDev 工作流嵌入更大的自动化系统时，再引入 OpenClaw。

回到开头那句判断：ChatDev 2.0 的价值不在"多智能体"这三个字上，而在于它把编排这件事的门槛从"会写 Python"降到了"会写配置"。如果你的场景里角色相对固定、变化的是输入，这个折中还账；如果你的场景需要复杂的动态路由，配置层的表达力反而会成为瓶颈。

---

## 相关链接

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/OpenBMB/ChatDev |
| 中文 README | https://github.com/OpenBMB/ChatDev/blob/main/README-zh.md |
| ChatDev 1.0 (Legacy) | https://github.com/OpenBMB/ChatDev/tree/chatdev1.0 |
| 开发者文档 | https://github.com/OpenBMB/ChatDev/tree/main/docs/user_guide/en |
| PyPI (SDK) | https://pypi.org/project/chatdev/ |
| 论文 | arXiv:2307.07924 |

---

*文档版本 1.3 | 仓库数据核对于 2026-09-24（GitHub API + main 分支源码）| 基于 ChatDev 2.0 (34.3k Stars, Apache-2.0)*
