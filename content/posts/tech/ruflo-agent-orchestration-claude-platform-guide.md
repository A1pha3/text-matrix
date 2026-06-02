---
title: "Ruflo 完全指南：多智能体编排平台从入门到精通"
date: "2026-05-02T20:03:00+08:00"
slug: "ruflo-agent-orchestration-claude-platform-guide"
aliases:
  - "/posts/tech/ruflo-claude-code-multi-agent-swarm-guide/"
  - "/posts/tech/ruflo-claude-multi-agent-orchestration-platform/"
description: "Ruflo 是基于 Model Context Protocol 的多智能体编排平台，为 Claude Code 添加 100+ 专业化 Agent、群智协调、自学习记忆、联邦通信与企业级安全能力。本文从原理、架构、安装配置、实战演示到开发扩展，系统讲解如何用 Ruflo 搭建生产级多 Agent 工作流。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "Claude", "Agent", "MCP", "多智能体", "RAG", "自动化"]
---

# Ruflo 完全指南：多智能体编排平台从入门到精通

Ruflo（曾用名 Claude Flow）真正解决的问题不是"让 Claude 更强"，而是把多 Agent 协作从手动分派变成一套基础设施：启动任务后，Agents 自行组队、分派工作、存下经验，下一次遇到同类任务时不再从零开始。你继续写代码，协调在后台运转。

截至本文编写时，Ruflo 在 GitHub 已有约 35,800 颗星、4,090 个分支，MIT 许可证，主语言 TypeScript，核心路由与向量引擎部分由 Rust 编译的 WASM 模块驱动。

## 1. 核心概念：为什么需要多智能体编排

### 1.1 传统单 Agent 的局限

Claude Code 是一个强单 Agent 工具，但它默认在隔离环境中运行：每次会话的任务之间没有共享记忆，Agent 无法复用过去的成功路径，多个 Agent 同时工作时也没有协调机制。处理复杂项目时，你得手动分派任务、管理上下文、追踪进度。

### 1.2 多智能体编排解决什么问题

Ruflo 把协调工作从用户那里接过来。它的基础设施围绕四条独立主线运转，每条解决一类问题：

- **群智协作**：多个专业化 Agent（coding、testing、review、security……）组成团队，各司其职，自动分担工作。
- **自我学习**：成功的执行路径被存下来，下次相似任务直接复用。
- **共享记忆**：HNSW 向量索引支持毫秒级检索，Agent 之间可以共享上下文而不是各自为战。
- **联邦通信**：不同机器、不同组织边界内的 Agent 可以安全交换任务，数据在发出前自动剥离敏感信息。

此外还有一条贯穿全部主线的辅助线——**智能路由**：不是所有任务都需要调用最贵的模型，Ruflo 根据任务复杂度决定走 WASM 免费加速、便宜的 Haiku 还是最强的 Opus。

### 1.3 关键术语

| 术语 | 含义 |
|------|------|
| **Swarm（蜂群）** | 多个 Agent 以特定拓扑结构组织的协作单元，可选层级（Queen-led）或网状（mesh）模式 |
| **Queen（蜂后）** | 负责协调的主 Agent，制定战略、分派任务、维持目标一致 |
| **Worker（工蜂）** | 执行具体任务的 Agent，有 8 种类型：Researcher、Coder、Analyst、Tester、Architect、Reviewer、Optimizer、Documenter |
| **SONA** | Self-Optimizing Neural Architecture，Ruflo 的自学习引擎，子毫秒级模式匹配 |
| **AgentDB** | 内置向量数据库，基于 HNSW 索引，搜索速度比 brute force 快 150~12,500 倍 |
| **Federation（联邦）** | 跨机器、跨信任边界的 Agent 协作协议，零信任架构 |
| **MCP（Model Context Protocol）** | Anthropic 推出的 Agent 与工具之间的通信协议，Ruflo 作为 MCP Server 暴露所有能力 |
| **RuVector** | 包含 SONA、EWC++、HNSW、ReasoningBank、Hyperbolic Embeddings 等组件的向量智能层 |
| **WASM Agent Booster** | 用 WebAssembly 在浏览器或 CLI 中跳过 LLM 直接处理简单代码转换（<1ms，零成本） |

## 2. 系统架构

### 2.1 整体架构图

在深入各层之前，先记住两条关键区分：**编排层**管"谁来做什么"，**群协调层**管"多个 Agent 怎么对齐"；**RuVector 智能层**是持续运转的学习回路，不参与单次任务调度——它从任务结束后取走轨迹，下次路由时才生效。

```
用户层（CLI / Claude Code）
        │
        ▼
安全入口层（AIDefence，输入验证，路径遍历防护）
        │
        ▼
编排层（MCP Server + 路由器 + 27 个 Hooks）
        │
        ├──────────────────────┐
        ▼                      ▼
路由决策（Q-Learning 路由器 + MoE 8 专家）    技能系统（130+ Skills）
        │                      │
        ▼                      ▼
群协调层（拓扑 / 一致性 / Claims）◄──── 记忆与学习（AgentDB + HNSW）
        │
        ▼
100+ 专业化 Agent
（coder, tester, reviewer, architect, security…）
        │
        ▼
资源层（LLM Providers / 12 个后台 Worker / 存储）
        │
        ▼
RuVector 智能层（SONA / EWC++ / HNSW / ReasoningBank / LoRA）
        │
        └───► 学习闭环：RETRIEVE → JUDGE → DISTILL → CONSOLIDATE → ROUTE
```

### 2.2 各层职责详解

**用户层**：通过 CLI 或 Claude Code 交互。将 Ruflo 作为 Claude Code 插件安装时，skills、commands、agents 和 MCP tools 直接集成进 Code 上下文，不需要额外启动进程。

**安全入口层**：所有入站请求经过 AIDefence 模块处理 prompt injection 检测、PII 识别（14 种敏感数据类型）、路径遍历防护和命令注入拦截。联邦模式下，敏感数据在发出前剥离或哈希。

**编排层**：核心控制平面。MCP Server 暴露约 210 个工具，分 5 个服务器组（Core、Intelligence、Agents、Memory、DevTools）。Router 根据任务特征和历史性能选择最优路径（Q-Learning，公开报告准确率 89%）。27 个 Hook 在关键节点触发行为——如 `post-task` 保存记忆、`pre-command` 注入安全扫描。

**群协调层**：Swarm 的执行引擎。支持 4 种拓扑结构：
- `hierarchical`：Queen-led 层级结构，Queen 验证每个输出与目标的一致性，是防止目标漂移（goal drift）的推荐模式
- `mesh`：点对点无中心协调，适合去中心化场景
- `ring`：环形邻居传播，适合大规模多 Agent 协作
- `star`：中心辐射型

支持 3 种一致性算法：Majority（简单多数）、Weighted（Queen 权重 3x）、Byzantine（f < n/3 容忍拜占庭故障）。

**100+ Agent 层**：每个 Agent 被分配特定角色（coder 负责实现、tester 负责测试、reviewer 负责审查……），可以并行启动并通过共享内存交换中间结果。

**RuVector 智能层**：Ruflo 的学习引擎核心。

| 组件 | 作用 | 性能指标 |
|------|------|---------|
| **SONA** | 自优化路由学习 | <0.05ms 模式匹配 |
| **EWC++** | 弹性权重 consolidation，防止灾难性遗忘 | 保留已学模式 |
| **HNSW** | 分层可导航小世界向量索引 | 子毫秒检索 |
| **ReasoningBank** | 轨迹学习模式存储 | RETRIEVE→JUDGE→DISTILL 闭环 |
| **Flash Attention** | 优化的注意力计算 | 2.49~7.47 倍加速 |
| **Hyperbolic Embeddings** | Poincaré 球嵌入，适合层次化数据 | 更好的代码关系建模 |
| **MicroLoRA** | 低秩微调适配 | 轻量级模型定制 |
| **Int8 Quantization** | 8 位整数量化 | 约 4 倍内存压缩 |
| **9 种 RL 算法** | Q-Learning / SARSA / A2C / PPO / DQN / Decision Transformer 等 | 任务自适应学习 |

这些数字来自项目公开报告，主要在测组件自身的延迟和吞吐。注意：HNSW 的 150~12,500 倍是相对于 brute force 最近邻搜索，不代表端到端任务有同等加速；Flash Attention 的倍数是注意力计算部分的加速，不包含模型推理的其他开销；Int8 的 4 倍压缩是在特定模型上的测量，不同模型差异可能很大。

### 2.3 学习闭环

RuVector 的核心是持续运转的五步闭环。每一步都由系统触发，不需要用户介入：

1. **RETRIEVE**：从 AgentDB 通过 HNSW 检索与当前任务相关的历史轨迹。
2. **JUDGE**：评估检索到的模式是否适用于当前上下文，计算匹配度。
3. **DISTILL**：将成功的模式压缩到路由策略和 Agent 行为模板中。
4. **CONSOLIDATE**：通过 EWC++ 将新知识与已有知识整合，防止遗忘。
5. **ROUTE**：更新路由器，下一次同类任务直接使用优化后的路径。

## 3. 安装与配置

### 3.1 前置要求

- **Node.js 20+**
- **npm 9+** 或 pnpm / bun
- **Claude Code**（必须先安装）

### 3.2 安装方式对比

| 安装方式 | 速度 | 说明 |
|---------|------|------|
| **一键脚本（推荐）** | ~35s（全局） | `curl -fsSL ...install.sh \| bash` |
| **npx（免安装）** | ~3s（有缓存）/~20s（全新） | `npx ruflo@latest init` |
| **npm 全局** | ~35s | `npm install -g ruflo@latest` |
| **Claude Code 插件** | 即插即用 | `/plugin marketplace add ruvnet/ruflo` |

### 3.3 完整安装步骤

**方式一：CLI 脚本安装（推荐生产使用）**

```bash
# 基础安装
curl -fsSL https://cdn.jsdelivr.net/gh/ruvnet/ruflo@main/scripts/install.sh | bash

# 完整安装（全局 + MCP 自动配置 + 诊断检查）
curl -fsSL https://cdn.jsdelivr.net/gh/ruvnet/ruflo@main/scripts/install.sh | bash -s -- --full
```

安装脚本支持以下参数：

| 参数 | 说明 |
|------|------|
| `--global`, `-g` | 全局安装（`npm install -g`） |
| `--minimal`, `-m` | 跳过可选依赖（速度更快，约 15s） |
| `--setup-mcp` | 自动配置 MCP Server |
| `--doctor`, `-d` | 安装后运行诊断检查 |
| `--no-init` | 跳过项目初始化 |
| `--full`, `-f` | 全量：全局 + MCP + 诊断 |
| `--version=X.X.X` | 指定版本安装 |

**方式二：npm / npx**

```bash
# 不安装直接运行（适合试用）
npx ruflo@latest init --wizard

# 全局安装
npm install -g ruflo@latest
ruflo init

# 用 bun 更快
bunx ruflo@latest init
```

**方式三：Claude Code 插件（最便捷）**

如果主要在 Claude Code 中工作，插件方式最合适——安装后 skills、commands、agents 和 MCP tools 直接集成进 Code，不需要额外进程：

```bash
# 添加插件市场（一次性操作）
/plugin marketplace add ruvnet/ruflo

# 安装核心插件
/plugin install ruflo-core@ruflo         # MCP Server + 基础 Agent
/plugin install ruflo-swarm@ruflo        # Swarm 协调
/plugin install ruflo-autopilot@ruflo    # 自主循环执行
/plugin install ruflo-federation@ruflo   # 跨机器联邦通信
```

Ruflo 共发布 32 个原生插件，可按需安装，完整列表见 GitHub 仓库 README。

### 3.4 验证安装

```bash
# 检查版本
ruflo --version

# 运行诊断
ruflo doctor

# 初始化项目（创建 CLAUDE.md 等配置文件）
ruflo init

# 查看 MCP 工具列表
claude mcp list
```

### 3.5 MCP Server 手动配置

如果安装脚本没有自动配置 MCP，可以手动添加：

```bash
claude mcp add ruflo -- npx -y @claude-flow/cli@latest
```

## 4. 核心功能详解

### 4.1 Swarm（蜂群协作）

Swarm 是 Ruflo 多 Agent 协作的核心抽象。一个 Swarm 由一个 Queen（协调者）和多个 Worker（执行者）组成，Queen 负责任务分解、进度追踪和一致性验证，Worker 负责具体执行。

**初始化一个 Swarm：**

```bash
# 启动一个层级 Swarm（推荐用于防止目标漂移）
npx ruflo@latest swarm init --topology hierarchical --max-agents 8

# 启动网状 Swarm（去中心化场景）
npx ruflo@latest swarm init --topology mesh --max-agents 16
```

**拓扑结构选择建议：**

| 场景 | 推荐拓扑 | 原因 |
|------|---------|------|
| 复杂编码任务（需要严格目标一致） | `hierarchical` | Queen 验证每个输出，防止漂移 |
| 大规模研究任务 | `mesh` | 无单点故障 |
| 需要有序流水线 | `ring` | 每个节点只与邻居通信 |
| 快速并行探索 | `star` | 一个中心分发，结构简单 |

**防止目标漂移的配置：**

```javascript
// Anti-Drift 配置（所有编码任务建议使用）
swarm_init({
  topology: "hierarchical",  // 单协调器强制对齐
  maxAgents: 8,             // 团队越小漂移面越小
  strategy: "specialized",   // 清晰角色边界减少歧义
  consensus: "raft"           // Leader 维护权威状态
})
```

### 4.2 自学习与记忆

**向量记忆（AgentDB + HNSW）**

AgentDB 是 Ruflo 内置的向量数据库，基于 HNSW 索引。存储和检索的性能：

```bash
# 存储一段记忆
npx ruflo@latest memory store "用户偏好 indigo 作为主题色" --namespace user_prefs

# 检索（子毫秒级）
npx ruflo@latest memory search "主题颜色" --namespace user_prefs --top-k 5
```

**ReasoningBank（推理库）**

保存完整的任务轨迹，包括问题描述、解决方案和执行路径。下次遇到相似问题时，系统会自动检索并推荐最优路径。

**3 层 Agent 记忆作用域：**

- **Project Scope**：仅当前项目内的 Agent 可见
- **Local Scope**：当前机器上的 Agent 共享
- **User Scope**：跨项目和机器的用户级别记忆

### 4.3 智能路由

Ruflo 的路由器根据任务复杂度选择最优处理路径：

| 任务复杂度 | 处理方式 | 延迟 | 成本 |
|-----------|---------|------|------|
| 简单（变量替换、类型注解添加等） | WASM Agent Booster（正则匹配，无需 LLM） | <1ms | $0 |
| 中等（常规编码任务） | Haiku / Sonnet | ~500ms | 低 |
| 复杂（架构设计、安全分析等） | Opus + Swarm | 2-5s | 高 |

路由器持续学习历史执行数据，公开报告的准确率为 89%。

### 4.4 WASM Agent Booster

Agent Booster 使用 WebAssembly 处理简单代码转换，在 CLI 和浏览器中都可用。支持以下转换意图：

| Intent（意图） | 功能 | 示例 |
|---------------|------|------|
| `var-to-const` | 将 var/let 转为 const | `var x = 1` → `const x = 1` |
| `add-types` | 添加 TypeScript 类型注解 | `function foo(x)` → `function foo(x: string)` |
| `add-error-handling` | 包装 try/catch | 添加完整错误处理 |
| `async-await` | Promise 链转 async/await | `.then()` → `await` |
| `add-logging` | 添加 console.log | 注入调试日志 |
| `remove-console` | 清除所有 console 调用 | 安全发布前清理 |

Hook 输出中会显示 `[AGENT_BOOSTER_AVAILABLE]` 标识，表示当前任务可以使用 WASM 跳过 LLM。

### 4.5 Token 优化器

Token Optimizer 整合了 agentic-flow 的优化策略，可将 token 使用量降低 30-50%：

| 优化手段 | 节省比例 | 原理 |
|---------|---------|------|
| ReasoningBank 检索 | -32% | 拉取相关模式而非完整上下文 |
| Agent Booster 简单编辑 | -15% | 跳过 LLM |
| Cache（95% 命中率） | -10% | 复用嵌入和模式 |
| 最优批处理大小 | -20% | 分组相关操作 |

这些优化可以叠加——同时启用时，总体节省通常大于单独使用任何一项。

### 4.6 联邦通信（Federation）

Federation 让不同机器或组织边界内的 Agent 可以安全协作，核心是零信任模型：远程 Agent 默认不被信任，身份通过 mTLS + ed25519 挑战-响应机制验证。14 型 PII 检测管道在数据发出前扫描，可按信任级别配置策略（BLOCK、REDACT、HASH、PASS）。

```bash
# 初始化本地方并生成密钥对
npx claude-flow@latest federation init

# 加入对方联邦端点
npx claude-flow@latest federation join wss://team-b.example.com:8443

# 发送任务（敏感信息自动剥离）
npx claude-flow@latest federation send --to team-b --type task-request \
  --message "分析账户异常的交易模式"

# 查看对端信任等级和会话健康状态
npx claude-flow@latest federation status
```

联邦的信任评分公式：`0.4×success + 0.2×uptime + 0.2×threat + 0.2×integrity`。表现良好的 Agent 逐步提升权限；行为异常立即降级，无需人工介入。

### 4.7 Web UI（FLO）

Ruflo 提供了一个可直接在浏览器使用的 Web 界面 [flo.ruv.io](https://flo.ruv.io/)，不需要安装，不需要 API Key 即可试用。

- **多模型支持**：默认 Qwen 3.6 Max，同时支持 Claude Sonnet 4.6、Claude Haiku 4.5、Gemini 2.5 Pro/Flash、OpenAI，可接入任何 OpenAI 兼容端点（vLLM、Ollama、LM Studio、Together、Groq 等）
- **~210 个工具**：5 个服务器组，加上 18 个工具的浏览器内 WASM Gallery，完全离线可用
- **MCP 服务器可扩展**：通过聊天输入框中的 MCP (n) 按钮添加自定义 MCP 端点（HTTP、SSE 或 stdio）
- **并行工具执行**：一次模型响应可同时触发 4-6+ 个工具，界面以卡片形式展示完成状态
- **持久记忆**：背后是 AgentDB + HNSW，说"记住我喜欢 indigo"几周后依然能回想起来
- **自托管**：通过 Docker 部署，源码在 `ruflo/src/ruvocal/`，支持多阶段构建和 Google Cloud Run

### 4.8 Goal Planner（目标规划）

[goal.ruv.io](https://goal.ruv.io/) 是 Ruflo 的目标导向行动规划（GOAP）前端，用自然语言描述目标，系统会：

1. 提取成功标准与约束条件
2. 用 A* 算法在状态空间中搜索最优路径
3. 将路径拆解为带前置条件的 Action 节点
4. 调度 Agent 执行，每个节点映射到具体 MCP 工具调用

- 实时可视化计划树，可折叠节点显示进度与阻塞分支
- 失败时从当前状态重新规划（A* replay），而非从头重启
- 与 AgentDB 集成，历史计划通过 HNSW 检索，相同领域问题越规划越快

## 5. 插件系统

Ruflo 的能力通过插件扩展，目前有 32 个原生插件，分为以下几类：

### 5.1 核心与编排

| 插件 | 功能 |
|------|------|
| `ruflo-core` | MCP Server + 健康检查 + 插件发现 |
| `ruflo-swarm` | 多 Agent 团队协调 |
| `ruflo-autopilot` | 自主循环执行 |
| `ruflo-loop-workers` | 定时后台任务 |
| `ruflo-workflows` | 可复用多步骤任务模板 |
| `ruflo-federation` | 跨机器安全协作 |

### 5.2 记忆与知识

| 插件 | 功能 |
|------|------|
| `ruflo-agentdb` | 高速向量数据库 |
| `ruflo-rag-memory` | 混合搜索、图跳、多样性排序 |
| `ruflo-ruvector` | GPU 加速搜索、Graph RAG、103 个工具 |
| `ruflo-knowledge-graph` | 实体关系图构建与遍历 |

### 5.3 智能与学习

| 插件 | 功能 |
|------|------|
| `ruflo-intelligence` | 从历史成功中学习 |
| `ruflo-ruvllm` | 本地 LLM（Ollama 等）智能路由 |
| `ruflo-goals` | 目标分解与进度追踪 |

### 5.4 安全与合规

| 插件 | 功能 |
|------|------|
| `ruflo-security-audit` | 漏洞与 CVE 扫描 |
| `ruflo-aidefence` | Prompt 注入拦截、PII 检测、安全扫描 |

## 6. 实战演示

### 6.1 场景一：用 Swarm 开发一个 REST API

假设需要开发一个用户认证服务，按以下步骤用 Ruflo 执行：

**步骤 1：初始化项目与 Swarm**

```bash
# 创建项目目录并初始化
mkdir auth-service && cd auth-service
npx ruflo@latest init

# 启动层级 Swarm（architect + coder + tester + reviewer）
npx ruflo@latest swarm init --topology hierarchical --agents architect,coder,tester,reviewer
```

**步骤 2：定义任务**

在 Claude Code 中（已安装 ruflo-core 插件）直接说：

```
帮我开发一个用户认证服务，包含注册、登录、JWT 签发。
用 Express + TypeScript，包含完整单元测试和 API 文档。
```

Ruflo 接到指令后的执行流程：Architect Agent 分析需求、设计目录结构与接口 → Coder Agent 实现核心逻辑 → Tester Agent 生成测试用例并执行 → Reviewer Agent 检查代码质量。Queen Agent 在每个阶段验证输出与目标的一致性，发现漂移立即纠正。

**步骤 3：查看执行结果**

```bash
# 查看 Swarm 状态和 Agent 执行日志
npx ruflo@latest swarm status

# 查看记忆中的执行轨迹
npx ruflo@latest memory search "auth service" --namespace project
```

### 6.2 场景二：联邦协作——跨团队共享威胁情报

团队 A（安全团队）和团队 B（开发团队）分别部署了 Ruflo，现在需要共享恶意流量模式但不暴露具体用户数据：

```bash
# 团队 A：初始化联邦，生成密钥
npx claude-flow@latest federation init

# 团队 A：加入团队 B 的联邦端点
npx claude-flow@latest federation join wss://dev-team.example.com:8443

# 团队 A：发送分析任务，PII 自动剥离
npx claude-flow@latest federation send \
  --to dev-team \
  --type intelligence-request \
  --message "分析近 7 天异常登录模式，返回特征向量而非原始日志"

# 查看信任评分变化
npx claude-flow@latest federation status
```

联邦安全检查通过后，团队 B 的 Agent 执行分析并返回结果，全程有审计日志。

### 6.3 场景三：Web UI 并行工具调用

打开 [flo.ruv.io](https://flo.ruv.io/)，选择 Qwen 3.6 Max 模型，输入：

```
帮我分析这个代码仓库的测试覆盖率，并列出需要补充测试的关键模块。
仓库地址：https://github.com/your/repo
```

Ruflo 会并行调用多个 MCP 工具（代码抓取 → 分析 → 覆盖率计算 → 生成报告），结果以卡片形式在界面中呈现，"Step 1 — 2 tools completed" 指示器让你清楚看到并行执行进度。

## 7. 配置参考

### 7.1 环境变量

Ruflo 支持通过环境变量配置核心行为：

```bash
# LLM Provider 配置
ANTHROPIC_API_KEY=sk-...           # Anthropic API 密钥
OPENAI_API_KEY=sk-...              # OpenAI API 密钥
GOOGLE_API_KEY=...                 # Google API 密钥

# 向量数据库
AGENTDB_URL=http://localhost:6333  # AgentDB 连接地址

# 联邦安全
FEDERATION_TRUST_LEVEL=strict      # trust | strict | relaxed
PII_DETECTION_MODE=block           # block | redact | hash | pass

# Swarm 配置
DEFAULT_TOPOLOGY=hierarchical
MAX_AGENTS_PER_SWARM=8

# 日志级别
RUFLO_LOG_LEVEL=info              # debug | info | warn | error
```

### 7.2 配置文件结构

Ruflo 的配置文件通常位于 `~/.ruflo/config.json` 或项目根目录的 `ruflo.config.json`：

```json
{
  "providers": {
    "anthropic": { "model": "claude-sonnet-4-20250514" },
    "openai": { "model": "gpt-4o" }
  },
  "swarm": {
    "defaultTopology": "hierarchical",
    "maxAgents": 8,
    "consensusAlgorithm": "raft"
  },
  "memory": {
    "backend": "agentdb",
    "hnsw EfSearch": 128
  },
  "federation": {
    "enabled": false,
    "trustLevel": "strict"
  },
  "hooks": {
    "preTask": ["security-scan", "context-inject"],
    "postTask": ["store-memory", "update-reasoningbank"]
  }
}
```

### 7.3 推荐的 Anti-Drift 生产配置

```javascript
// ruflo.config.json — 生产环境推荐
{
  "swarm": {
    "topology": "hierarchical",
    "maxAgents": 8,
    "strategy": "specialized",
    "consensusAlgorithm": "raft",
    "checkpointInterval": 5,        // 每 5 个任务检查点一次
    "maxTaskDuration": 300          // 超过 5 分钟的任务强制评审
  },
  "hooks": {
    "postTask": [
      "validate-output-consistency",  // 验证输出与目标的一致性
      "store-memory",
      "update-telemetry"
    ],
    "preCommand": [
      "security-scan",
      "pii-detection"
    ]
  },
  "routing": {
    "strategy": "q-learning",
    "fallbackModel": "haiku",
    "complexityThreshold": 0.7      // 复杂度 > 0.7 才动用 Opus+Swarm
  }
}
```

## 8. 开发扩展

### 8.1 创建自定义插件

Ruflo 提供 `ruflo-plugin-creator` 插件用于脚手架生成：

```bash
# 安装插件创建器
npx ruflo@latest plugin install ruflo-plugin-creator@ruflo

# 创建新插件
npx ruflo@latest plugin create my-custom-plugin

# 插件目录结构
my-custom-plugin/
├── src/
│   ├── index.ts           # 入口文件
│   ├── hooks/             # 自定义 Hooks
│   ├── agents/            # 自定义 Agents
│   └── providers/         # 自定义 LLM Provider
├── tests/
├── package.json
└── README.md
```

### 8.2 自定义 Hook 示例

Hook 在关键节点触发自定义逻辑。创建一个在每次任务完成后保存上下文的 Hook：

```typescript
// src/hooks/save-context.ts
import { Hook, HookContext } from '@ruflo/core';

export const saveContextHook: Hook = {
  name: 'save-context',
  trigger: 'post-task',
  async execute(ctx: HookContext) {
    const { task, result, agentId } = ctx;
    // 将任务结果存入记忆
    await ctx.memory.store({
      type: 'task-outcome',
      task: task.description,
      outcome: result.success ? 'success' : 'failure',
      agentId,
      timestamp: Date.now()
    });
    return ctx;
  }
};
```

### 8.3 自定义 Agent 示例

```typescript
// src/agents/security-scanner.ts
import { Agent, AgentConfig } from '@ruflo/core';

export const securityScannerAgent: Agent = {
  name: 'security-scanner',
  role: 'security',
  capabilities: ['static-analysis', 'cve-scan', 'dependency-audit'],
  
  async execute(task: Task, ctx: AgentContext) {
    // 1. 静态分析源码
    const issues = await ctx.tools.run('semgrep', { target: task.filePath });
    // 2. CVE 扫描依赖
    const cvss = await ctx.tools.run('npm-audit', { format: 'json' });
    // 3. 汇总报告
    return ctx.composeReport([issues, cvss]);
  }
};
```

### 8.4 接入自定义 MCP 服务器

通过 Web UI 的 MCP 按钮添加任意 MCP 端点（HTTP、SSE 或 stdio）：

1. 点击聊天输入框左侧的 **MCP (n)** 按钮
2. 选择 *Add Server*
3. 粘贴 MCP 端点 URL（例如 `http://localhost:3000`）
4. 自定义工具自动加入并行执行流程

## 9. 从哪里开始

如果你刚知道 Ruflo，最务实的进入路线是：

1. 跑通安装和第一个 Swarm 任务（第 3、6 节），建立体感。
2. 熟悉核心功能（第 4 节），重点掌握 Swarm 拓扑选择、记忆存取和智能路由。
3. 按生产需求配置 Anti-Drift 和 Token 优化（第 7 节）。
4. 需要跨团队协同时，再碰 Federation（第 4.6 节）。

想定制行为时再看开发扩展（第 8 节）和 RuVector 底层（第 2.3 节）。

哪类团队先上？如果你的项目已用 Claude Code 且存在多步骤编码任务（需要设计→实现→测试→审查），Ruflo 的收益最直接。如果你只在 Code 里做单轮问答，可以先观望。离线场景或已有 Ollama 环境的团队，可以通过 `ruflo-ruvllm` 插件接入本地模型，但学习记忆回路仍需云端模型驱动。

## 10. 常见问题

**Q：Ruflo 和 Claude Code 是什么关系？**

Ruflo 构建在 Claude Code 之上，提供多 Agent 编排层。Claude Code 处理单次对话交互，Ruflo 负责多 Agent 协调、记忆持久化和学习。不安装任何插件的情况下也可以通过 CLI 使用 Ruflo，但作为 Claude Code 插件集成体验最完整。

**Q：需要自己管理 LLM API 费用吗？**

是的。Ruflo 本身免费（MIT 许可证），但调用 Anthropic、OpenAI 等模型的费用由用户自行承担。Ruflo 的智能路由可以帮助降低用量（简单任务用 WASM 免费处理），但 API 调用费用不在控制范围内。

**Q：Federation 的安全边界是什么？**

Federation 采用零信任模型：远程 Agent 默认不被信任。身份通过 mTLS + ed25519 验证，所有出站数据经过 14 型 PII 检测管道。拜占庭容错一致性算法确保最多 (n-1)/3 个恶意节点无法破坏整体决策。敏感数据可在配置中选择 BLOCK、REDACT 或 HASH 策略。

**Q：可以在离线环境使用吗？**

可以。Ruflo 支持本地模型（通过 `ruflo-ruvllm` 插件接入 Ollama），AgentDB 和大部分 Worker 也可离线运行。Web UI 的 WASM Gallery 完全在浏览器内运行，不需要网络。唯一需要网络的功能是调用云端 LLM API。

**Q：如何排查安装或运行问题？**

```bash
# 运行诊断检查
ruflo doctor

# 查看详细日志
RUFLO_LOG_LEVEL=debug ruflo <command>

# 检查 MCP 工具列表
claude mcp list

# 查看 Swarm 状态
ruflo swarm status
```

**Q：最多可以同时运行多少个 Agent？**

技术上没有硬性限制，但推荐每个 Swarm 最多 8 个 Agent 以防止协调开销和目标漂移。可以启动多个 Swarm 覆盖不同的任务域。

## 资源链接

- GitHub 仓库：https://github.com/ruvnet/ruflo
- 用户指南：[docs/USERGUIDE.md](https://github.com/ruvnet/ruflo/blob/main/docs/USERGUIDE.md)
- Web UI（免安装试用）：https://flo.ruv.io/
- Goal Planner：https://goal.ruv.io/
- 插件市场：https://ruvnet.github.io/ruflo
- 社区 Discord：https://discord.com/invite/dfxmpwkG2D