---
title: "SmallCode: 为本地小模型打造的AI Coding Agent深度解析"
date: "2026-05-22T11:42:33+08:00"
slug: "smallcode-ai-coding-agent-small-llms"
description: "SmallCode是一款专为8B-35B本地模型设计的终端原生AI Coding Agent，通过MarrowScript认知层、Context Budget引擎、2-Stage Tool Routing等机制，在消费级硬件上实现可靠编码任务自动化。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "Coding Agent", "Local LLM", "JavaScript", "Node.js"]
---

# SmallCode: 为本地小模型打造的 AI Coding Agent 深度解析

## 一句话判断

SmallCode 是一款专为 **8B-35B 本地模型**（运行在消费级 GPU/内存上）设计的终端原生 AI Coding Agent，通过 MarrowScript 认知层、Context Budget 引擎、2-Stage Tool Routing 等一系列机制，**在小模型可靠性有限的前提下实现可靠的编码任务自动化**。MIT 协议，1096 Stars（截至 2026-05-22），JavaScript/TypeScript 实现，支持 npm 全局安装或预编译二进制。

---

## 核心问题：为什么小模型需要专用 Coding Agent

当前主流 AI Coding Agent（如 OpenCode、Cline）默认以 **Claude、GPT-5 等前沿模型** 为设计目标：128k+ context 窗口、可靠的 JSON tool calling、128k+ context 意味着"把所有文件内容都扔进去"也能 work。

但这与大多数开发者的实际条件存在根本矛盾：

- **本地模型受硬件限制**：消费级 GPU 通常只能跑 8B-35B 模型（Qwen2.5-Coder、DeepSeek-Coder-7B、CodeQwen1.5-7B 等），这些模型的 context 窗口通常在 8k-32k，且 tool calling 可靠性远不如 frontier 模型
- **小模型的问题**：上下文跟踪能力弱、tool calling 输出格式不稳定、长对话容易遗忘早期信息、推理 token 开销大

SmallCode 的核心定位正是：**在不改变硬件条件的前提下，通过工程手段让 8B-35B 小模型可靠地完成编码任务**。这一点从它的对比表中可以看出：

| | OpenCode | SmallCode |
|---|----------|-----------|
| **目标模型** | Claude、GPT-5（frontier） | 8B-35B 本地模型 |
| **Context 处理** | 全部塞入 | 预算管理 + 摘要压缩 |
| **Tool Calling** | 假设可靠 JSON 输出 | 多格式容错解析器 |
| **规划方式** | 单次 shot | TODO 文件逐步分解 |
| **编辑方式** | 全文件写入 | Search-and-replace patch |
| **隐私** | 云端 API 调用 | 完全本地，无需网络 |

---

## 架构解析

SmallCode 采用 bin/ + src/ 双层架构：

```
bin/
├── smallcode.js         # 入口：agent 循环 + TUI 编排（1570行）
├── config.js            # 配置加载、端点检测、认证头
├── executor.js          # 18个工具的执行器
├── tools.js             # 工具定义 + 2阶段路由
├── mcp_bridge.js        # 内置 code graph MCP 通信
├── model_client.js      # LLM API 调用、流式响应、验证
├── governor.js          # 工具评分、验证、任务分解
├── escalation.js        # 云端模型兜底（Claude/OpenAI/DeepSeek）
├── commands.js          # TUI 斜杠命令
├── tui.js               # 经典 TUI 渲染器
└── bonescript_guide.js # BoneScript 语法参考

src/
├── api/index.js         # 程序化 API（require('smallcode')）
├── tui/fullscreen.js    # 全屏交替缓冲区 TUI
├── plugins/loader.js     # 插件系统
├── plugins/skills.js    # 技能系统
├── tools/               # 工具路由、MCP 客户端、验证器
├── governor/            # Early-stop 检测、验证器、工具评分
├── model/               # 多模型配置 + 路由
└── session/            # 持久化、undo、共享、引用
```

**核心设计原则**：bin/ 面向命令行交互层，src/ 面向程序化 API 调用层，二者共享同一套工具生态和模型客户端。

---

## 关键技术机制

### MarrowScript 认知层

MarrowScript 是 SmallCode 的"灵魂声明语言"——用约 50 行 `.marrow` 声明文件，经编译生成 1400+ 行 TypeScript 代码，自动携带缓存、重试、验证、追踪和预算执行：

```marrow
prompt classify_task_type(user_message: string) {
  model: TinyClassifier
  timeout: 3s
  cache: { key: hash(user_message), ttl: 10m }
  retry: { max_attempts: 2, backoff: fixed, interval: 100ms }
  constraints: [output in ["coding", "editing", "search", ...]]
}
```

编译后的认知层提供四大能力：
- **Prompt 缓存**：cache hit 时 0ms 延迟，基于内容哈希 key + TTL
- **结构化追踪**：每次 LLM 调用记录 trace_id/span_id（`SMALLCODE_COGNITION_LOG=stderr` 开启）
- **分层模型路由**：简单任务路由至 tiny 模型，复杂任务路由至 medium/strong 模型
- **Token 预算强制执行**：按费用类别强制限额，永不超支

### BoneScript 后端编译

BoneScript 是 SmallCode 配套的"全栈代码生成语言"——写一个 `.bone` 文件，编译输出完整后端项目（路由、认证、数据库、事件、迁移、SDK、管理面板、Docker、CI）。理论上可将 8-15 次 tool call 减少至 1-2 次，显著提升小模型可靠性。

### Context Budget 引擎

小模型最怕 context overflow。SmallCode 的 Context Budget 引擎通过三层机制应对：

1. **工具结果截断**：每次 tool call 结果上限 4k 字符
2. **中轮次清除**（Mid-turn Eviction）：对话上下文膨胀时主动清除旧结果
3. **语义压缩**（Semantic Compression）：不是简单丢内容，而是做摘要压缩保留语义

### 2-Stage Tool Routing

小模型的 tool calling schema 本身就会消耗大量 context。SmallCode 引入两级路由：

**Stage 1**：模型首先选择一个分类（`read` / `write` / `search` / `run` / `plan`）

**Stage 2**：获得该分类下的**子集工具** schema，而非全部 18 个工具的 schema

这将 schema context 开销减半，对 8-16k context 的模型尤为关键。

### Patch-First Editing

小模型无法可靠地"复现完整文件"——会截断内容、产生幻觉，或偏离原始文件。SmallCode 将 **search-and-replace patch** 作为主要编辑原语，而非 `write_file` 全文件覆盖。`patch` 同时会触发 Read-Before-Write Guard，强制模型在编辑前先读取目标文件。

### Early-Stop Detection

检测并中断以下浪费 token 的循环：
- **重复循环**：相同 tool call 被重复执行
- **Patch 螺旋**：文件损坏后不断用错误内容重写（强制 rewrite）
- **Greeting 回归**：模型丢失上下文后重新注入任务

### Model Escalation（可选）

当本地模型经历"重试 + 分解"后仍然硬失败，SmallCode 可选地升级至云端模型（Claude / OpenAI / DeepSeek）。完全 opt-in，且以 session 为作用域防止费用失控：

```bash
# .env 中配置升级目标
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...
```

---

## 完整工具矩阵

| 工具 | 描述 |
|------|------|
| `bone_compile` | 编译 .bone 文件至完整后端项目 |
| `bone_check` | 验证 .bone 文件（类型错误、约束） |
| `list_projects` | 列出所有已索引项目及统计 |
| `graph_search` | 代码图谱符号搜索 |
| `explain_symbol` | 完整符号解释（调用者/被调用者） |
| `read_file` | 读取文件内容 |
| `write_file` | 创建/覆写文件 |
| `patch` | search-and-replace 编辑 |
| `bash` | 执行 shell 命令 |
| `search` | 正则搜索（ripgrep） |
| `find_files` | glob 文件搜索 |
| `memory_load` | 加载相关项目记忆 |
| `memory_remember` | 保存知识至记忆 |
| `web_search` | DuckDuckGo 网页搜索 |
| `web_fetch` | 抓取 URL 页面文本 |

---

## 快速上手

### 安装

```bash
# npm 全局安装
npm install -g smallcode

# 或直接 npx 运行
npx smallcode

# Linux/macOS 一行安装脚本
bash <(curl -fsSL https://raw.githubusercontent.com/Doorman11991/smallcode/main/install.sh)

# Windows PowerShell
iwr -Uri https://raw.githubusercontent.com/Doorman11991/smallcode/main/install.ps1 -UseBasicParsing | iex
```

### 配置

在项目根目录创建 `.env`：

```bash
# 必须配置
SMALLCODE_MODEL=your-model-name
SMALLCODE_BASE_URL=http://localhost:1234/v1

# 可选：云端模型升级兜底
# ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...
# DEEPSEEK_API_KEY=sk-...
```

需要本地 LLM 服务（LM Studio、Ollama 或任意 OpenAI 兼容端点）在 `localhost:1234`（默认端口，可配置）。

### 程序化 API

```javascript
const { SmallCode } = require('smallcode');

const agent = new SmallCode({
  model: 'qwen2.5-coder-7b',
  baseUrl: 'http://localhost:1234/v1',
});

const result = await agent.run("create hello.py that prints hello world");
console.log(result.filesCreated);   // ['hello.py']
console.log(result.success);        // true

agent.on('tool_end', ({ name, ms }) => console.log(`Done: ${name} (${ms}ms)`));
```

---

## 适用边界

**值得选择 SmallCode 的场景：**
- 在消费级 GPU（8GB-24GB 显存）上跑 8B-35B 编码模型
- 需要完全本地化（隐私敏感场景，不希望 API 调用外发）
- 任务是中小型编码任务（文件编辑、单项目重构、测试生成）

**不适合的场景：**
- 已能稳定使用 Claude-3.5/GPT-5 等 frontier 模型（此时 OpenCode 等工具更成熟）
- 需要处理巨大单体仓库（需要 128k+ context 的场景）
- 任务高度复杂、需要强推理的前沿算法问题（小模型本身能力上限）

---

## 总结

SmallCode 的技术路径很明确：**在硬件约束不变的条件下，通过工程手段让小模型可靠工作**。它不是另一个"把所有文件都扔给大模型"的 coding agent，而是一整套针对小模型弱点设计的工程解决方案——从认知层声明（MarrowScript）到编辑原语（patch-first）到观测能力（tracing/budget），每个模块都有明确的问题指向。

对于在消费级硬件上构建本地 AI 编程工作流的开发者，SmallCode 提供了目前最完整、专门的工具箱。
