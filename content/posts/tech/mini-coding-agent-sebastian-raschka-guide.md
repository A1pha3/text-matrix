---
title: "Mini-Coding-Agent：Sebastian Raschka 的极简代码代理框架完全指南"
date: "2026-04-07T00:55:00+08:00"
slug: "mini-coding-agent-sebastian-raschka-guide"
aliases:
    - "/posts/tech/mini-coding-agent-sebastian-raschka-source-code-guide/"
description: "全面介绍 Sebastian Raschka 的 Mini-Coding-Agent 极简代码代理框架，详解六大核心组件（实时上下文、提示缓存、结构化工具、上下文缩减、对话记忆、子代理委托）、Ollama 环境配置、CLI 参数、会话管理和扩展建议。"
draft: false
categories: ["技术笔记"]
tags: ["代码代理", "AI Agent", "Ollama", "Sebastian Raschka", "Python", "LLM", "自主编程", "工具调用"]
---

## 学习目标

读完本文，你会拿到：

- 深入理解 Mini-Coding-Agent 的设计哲学和极简架构
- 学会安装配置 Ollama 环境和依赖
- 掌握六大核心组件的原理和实现
- 学会使用 CLI 工具和交互式命令
- 理解会话恢复和内存持久化机制
- 掌握批准模式和安全控制
- 了解代码代理的实际应用场景

---

## 目录

- [1. 项目概述](#1-项目概述)
- [2. 六大核心组件](#2-六大核心组件)
- [3. 环境配置](#3-环境配置)
- [4. 基本使用](#4-基本使用)
- [5. 会话管理](#5-会话管理)
- [6. 交互式命令](#6-交互式命令)
- [7. CLI 参数详解](#7-cli-参数详解)
- [8. 工具输出格式](#8-工具输出格式)
- [9. 工作流程示例](#9-工作流程示例)
- [10. 与其他框架对比](#10-与其他框架对比)
- [11. 扩展建议](#11-扩展建议)
- [12. 总结](#12-总结)
- [自测题](#自测题)
- [练习](#练习)
- [进阶路径](#进阶路径)
- [常见问题与排查](#常见问题与排查)

## 1. 项目概述

### 1.1 是什么

**Mini-Coding-Agent** 是 Sebastian Raschka（著名机器学习研究者、PyTorch 作者之一）创建的极简代码代理框架。它不是一个生产级 robust 的代理，而是一个**教学示范**，通过最小可读的代码解释代码代理的核心组件。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | **309** |
| GitHub Forks | **59** |
| Contributors | **2** (rasbt + shixy96) |
| Commits | **14** |
| License | **Apache-2.0** |
| 语言 | **Python 100%** |

### 1.3 作者背景

**Sebastian Raschka** 是知名的机器学习专家：
- 前 PyTorch 核心贡献者
- 《Python Machine Learning》作者
- 专注 AI 教育，擅长把复杂概念简单化

### 1.4 设计哲学

| 理念 | 说明 |
|------|------|
| **极简优先** | 代码量小，优先可读性而非 robustness |
| **教学导向** | 解释核心概念，非生产级实现 |
| **本地运行** | 基于 Ollama，无需云服务 |
| **无外部依赖** | 仅用 Python 标准库 |

---

## 2. 六大核心组件

### 2.1 Live Repo Context（实时仓库上下文）

代理在开始时收集稳定的仓库信息：

| 信息类型 | 说明 |
|---------|------|
| **仓库布局** | 目录结构、文件组织 |
| **指令** | README、CONTRIBUTING 等 |
| **Git 状态** | 当前分支、未提交更改 |

这确保代理理解它的工作环境，而非盲目操作。

### 2.2 Prompt Shape & Cache Reuse（提示形状与缓存复用）

```
┌─────────────────────────────────────┐
│  Static Prefix（稳定前缀）           │  ← 可缓存复用
│  - 系统指令                         │
│  - 工具定义                         │
│  - 仓库上下文                       │
├─────────────────────────────────────┤
│  Dynamic Content（动态内容）           │  ← 每轮变化
│  - 用户请求                         │
│  - 对话历史                         │
│  - 工作内存                         │
└─────────────────────────────────────┘
```

**优势**：减少每次调用的 token 消耗，提高效率。

### 2.3 Structured Tools & Validation（结构化工具与验证）

代理使用**命名工具**而非自由形式操作：

| 工具类型 | 说明 |
|----------|------|
| **Read** | 读取文件（带路径验证） |
| **Write** | 写入文件 |
| **Edit** | 编辑文件 |
| **Bash** | 执行 Shell 命令 |

**安全机制**：
- 输入验证：检查路径是否在 workspace 内
- 批准门：危险操作需要确认

### 2.4 Context Reduction（上下文缩减）

长输出被**截断**，重复读取被**去重**，旧对话被**压缩**：

```python
# 去重示例：同一文件多次读取只保留一次
seen_reads = set()  # 记录已读文件

def read_file(path):
    if path in seen_reads:
        return cached_content[path]  # 返回缓存
    content = do_read(path)
    seen_reads.add(path)
    return content
```

### 2.5 Transcripts & Memory（对话记录与记忆）

| 持久化类型 | 说明 |
|-----------|------|
| **Transcript** | 完整对话历史，可恢复 |
| **Working Memory** | 蒸馏后的关键信息，轻量 |

```
Session 保存位置：.mini-coding-agent/sessions/<session-id>/
```

### 2.6 Delegation & Bounded Subagents（委托与受限子代理）

子代理被**限制作用域**：
- 继承足够上下文以完成任务
- 但在严格限制内操作
- 防止无限递归或资源耗尽

---

## 3. 环境配置

### 3.1 安装 Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# 下载安装包：https://ollama.com/download

# 验证安装
ollama --help

# 启动 Ollama 服务（后台运行）
ollama serve
```

### 3.2 拉取模型

```bash
# 默认模型：qwen2.5-coder:7b（推荐配置）
ollama pull qwen2.5-coder:7b

# 如有足够显存，可尝试更大模型
ollama pull qwen2.5-coder:14b

# 其他可选模型
ollama pull llama3.2:3b
ollama pull codellama:7b
```

### 3.3 项目安装

```bash
# 克隆仓库
git clone https://github.com/rasbt/mini-coding-agent.git
cd mini-coding-agent

# 使用 uv 运行（推荐）
uv run mini-coding-agent

# 或直接运行
python mini_coding_agent.py
```

### 3.4 依赖要求

| 依赖 | 说明 |
|------|------|
| Python | 3.10+ |
| Ollama | 必须安装并运行 |
| uv | 可选，用于环境管理 |

---

## 4. 基本使用

### 4.1 启动代理

```bash
# 默认配置：qwen2.5-coder:7b + ask 批准模式
uv run mini-coding-agent

# 指定工作目录
uv run mini-coding-agent --cwd /path/to/project

# 指定模型
uv run mini-coding-agent --model qwen2.5-coder:14b
```

### 4.2 批准模式

| 模式 | 说明 | 安全性 |
|------|------|--------|
| `--approval ask` | 危险操作前提示确认 | ⭐⭐⭐⭐⭐ 推荐 |
| `--approval auto` | 自动执行所有操作 | ⭐ 仅可信环境 |
| `--approval never` | 拒绝危险操作 | ⭐⭐⭐⭐ |

```bash
# 自动模式（仅用于可信代码库！）
uv run mini-coding-agent --approval auto

# 严格模式
uv run mini-coding-agent --approval never
```

---

## 5. 会话管理

### 5.1 会话持久化

代理自动保存会话到：
```
.mini-coding-agent/sessions/<session-id>/
```

每个会话包含：
- `transcript.json` - 完整对话历史
- `memory.json` - 蒸馏后的工作内存
- `state.json` - 代理状态快照

### 5.2 恢复会话

```bash
# 恢复最新会话
uv run mini-coding-agent --resume latest

# 恢复指定会话
uv run mini-coding-agent --resume 20260401-144025-2dd0aa
```

### 5.3 列出历史会话

```bash
# 会话保存在 .mini-coding-agent/sessions/
ls -la .mini-coding-agent/sessions/
```

---

## 6. 交互式命令

在 REPL 内可使用斜杠命令（直接由代理处理，不发往模型）：

| 命令 | 说明 |
|------|------|
| `/help` | 显示可用命令列表 |
| `/memory` | 打印蒸馏后的会话记忆 |
| `/session` | 打印当前会话文件路径 |
| `/reset` | 清除当前会话历史和记忆，保留 REPL |
| `/exit` | 退出交互会话 |
| `/quit` | 同 `/exit` |

---

## 7. CLI 参数详解

### 7.1 核心参数

```bash
uv run mini-coding-agent --help
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--cwd` | `.` | 工作目录 |
| `--model` | `qwen2.5-coder:7b` | Ollama 模型名 |
| `--host` | `http://127.0.0.1:11434` | Ollama 服务器地址 |
| `--ollama-timeout` | `300` | 等待 Ollama 响应超时（秒） |
| `--resume` | 新会话 | 恢复会话 ID 或 `latest` |
| `--approval` | `ask` | 批准模式 |
| `--max-steps` | `6` | 单次请求最大轮次 |
| `--max-new-tokens` | `512` | 每步最大输出 token |
| `--temperature` | `0.2` | 采样温度 |
| `--top-p` | `0.9` | Nucleus 采样 |

### 7.2 高级用法

```bash
# 使用更大上下文模型
uv run mini-coding-agent --model qwen2.5-coder:14b --max-steps 10

# 增加输出长度
uv run mini-coding-agent --max-new-tokens 1024

# 更创造性响应
uv run mini-coding-agent --temperature 0.8 --top-p 0.95

# 连接到远程 Ollama
uv run mini-coding-agent --host http://remote-server:11434
```

---

## 8. 工具输出格式

代理期望模型输出特定格式：

```xml
<!-- 工具调用 -->
<tool>
{
  "name": "read_file",
  "parameters": {"path": "src/main.py"}
}
</tool>

<!-- 最终回复 -->
<final>
代理的最终回复或总结
</final>
```

**注意**：不同 Ollama 模型对这些格式的遵循程度不同。

---

## 9. 工作流程示例

### 9.1 开发新功能

```bash
$ uv run mini-coding-agent --cwd ./my-project

# 代理开始收集上下文...
# - 扫描仓库结构
# - 读取 README 和 CONTRIBUTING
# - 检查 Git 状态

# 用户输入
> 为这个项目添加一个 CLI 入口点

# 代理思考并调用工具
<tool>{"name": "read_file", "parameters": {"path": "pyproject.toml"}}</tool>
<tool>{"name": "write_file", "parameters": {"path": "src/cli.py", "content": "..."}}</tool>

<final>
已添加 CLI 入口点到 src/cli.py，包含 --help 和基本命令。
</final>
```

### 9.2 Bug 修复

```bash
$ uv run mini-coding-agent --cwd ./buggy-project --resume latest

> 继续上次的 bug 修复任务

# 代理加载之前的会话记忆
# - 之前已读取相关文件
# - 继续分析问题
```

---

## 10. 与其他框架对比

| 框架 | Stars | 复杂度 | 定位 |
|------|-------|---------|------|
| **Mini-Coding-Agent** | 309 | 极简 | 教学/入门 |
| **LangChain Agents** | 50k+ | 复杂 | 生产级 |
| **AutoGPT** | 160k+ | 中等 | 实验性 |
| **Claude Code** | - | 闭源 | 生产级 |

**Mini-Coding-Agent 的独特价值**：
- 代码量小（~500 行 vs LangChain 的~10 万行）
- 适合学习原理
- 无隐藏魔法

---

## 11. 扩展建议

### 11.1 添加新工具

```python
# mini_coding_agent.py 中添加

def execute_sql(query: str) -> str:
    """Execute SQL query on local database."""
    # 实现 SQL 执行逻辑
    pass

# 注册到工具列表
TOOLS = {
    "execute_sql": execute_sql,
    # ...
}
```

### 11.2 更换后端

当前基于 Ollama，可扩展支持：
- OpenAI API
- Anthropic Claude
- 本地模型

### 11.3 添加记忆策略

当前使用简单压缩，可改进为：
- LLM 蒸馏摘要
- 重要性评分
- 长期记忆向量存储

---

## 12. 总结

**Mini-Coding-Agent** 是一个独特的项目——它不是要做一个生产级代理，而是**用最少的代码解释代码代理的核心原理**。

| 维度 | 评价 |
|------|------|
| **可读性** | ⭐⭐⭐⭐⭐ ~500 行纯 Python |
| **教学价值** | ⭐⭐⭐⭐⭐ 清晰解释六大组件 |
| **功能完整** | ⭐⭐⭐ 基础功能齐全 |
| **生产可用** | ⭐⭐ 仅为教学设计 |

**适用场景**：

- 学习代码代理原理
- 理解六大核心组件
- 作为自定义代理起点
- 教学演示

**不适合**：

- 生产环境
- 复杂任务自动化
- 需要高 robustness 的场景

**官方资源**：

- GitHub：https://github.com/rasbt/mini-coding-agent
- 作者 Blog：https://magazine.sebastianraschka.com/p/components-of-a-coding-agent
- Sebastian Twitter：https://twitter.com/rasbt

## 自测题

**概念题**

1. Mini-Coding-Agent 的定位是「教学示范」还是「生产级代理」？它为什么坚持只用 Python 标准库、不引第三方依赖？
2. 提示缓存（Prompt Cache Reuse）把系统指令、工具定义、仓库上下文放在「稳定前缀」。这部分为什么能缓存复用，而对话历史和用户请求不能？
3. 上下文缩减（Context Reduction）做了哪三件事？为什么长输出要「截断」而不是全保留？
4. 子代理（Subagent）被「限制作用域」指的是什么？如果不加这个限制会发生什么？
5. 批准模式 `--approval` 有 ask / auto / never 三档，各自适用于什么环境？

**场景题**

6. 你用一块 4 GB 显存的老显卡跑这个代理，默认的 `qwen2.5-coder:7b` 很吃紧。你会怎么调 `--max-new-tokens` 和 `--max-steps` 让它稳定工作？

**参考答案**

1. 它是教学示范，目标是用最小可读代码讲清代码代理的核心组件，不是为生产 robustness 设计。只用标准库是为了可读性优先、零安装摩擦，读者能直接读懂每行代码。
2. 稳定前缀在多次调用间基本不变（系统指令、工具 schema、仓库结构都不随对话变），所以 KV cache 可复用，省下重复 prefill 的 token；对话历史和用户请求每轮都变，没法复用。
3. 长输出截断、重复读取去重、旧对话压缩。截断是为控制上下文窗口和 token 成本，否则长日志会把前面的关键信息挤出去。
4. 子代理只继承完成任务所需的最小上下文，且被严格限制操作边界，防止无限递归或耗光资源。不限的话，子代理可能越权访问或递归调用把自己拖死。
5. ask 适合日常和陌生代码库（危险操作先确认）；auto 只用于可信、隔离的代码库；never 拒绝一切写操作，适合只读分析。
6. 7B 模型在 4 GB 显存上很容易 OOM（量化后也接近上限）。我会把 `--max-new-tokens` 降到 256 左右、`--max-steps` 降到 4，缩短单次任务链，或者直接换更小的 `qwen2.5-coder:3b`，必要时略调 `--temperature`。

## 练习

1. 用 `uv` 把仓库跑起来，随便指一个你自己的小项目目录，让代理加一个 CLI 入口点，确认读 / 写 / 编辑工具都走通。
2. 故意触发一次危险操作（比如让代理删除某个文件），观察 `--approval ask` 模式下的确认提示；再试 `--approval never`，看它如何拒绝。
3. 跑完一轮后执行 `--resume latest`，确认它能从 `.mini-coding-agent/sessions/<session-id>/` 里的 `transcript.json` 恢复上下文，并读懂 `memory.json` 里蒸馏了什么。
4. 打开 `mini_coding_agent.py`，照第 11.1 节的示例加一个 `execute_sql` 工具，注册进 `TOOLS`，验证代理能调用它。
5. 把后端从 Ollama 换成 OpenAI 兼容接口（或本地 llama.cpp 服务），改 `--host` 指向你的端点，确认工具调用格式 `<tool>...</tool>` 仍能被模型正确产出。

## 进阶路径

读通这份代码后，可以往这几个方向深挖：

- 读 `mini_coding_agent.py` 里上下文缩减的实现，理解「去重 + 截断 + 压缩」三步怎么配合，以及压缩阈值怎么定
- 研究提示缓存的工程细节：稳定前缀的边界划在哪、哪些内容绝对不能进缓存、缓存命中率怎么影响成本
- 对比 Mini-Coding-Agent 与 Claude Code / Aider 的架构差异，重点看它们怎么处理「长任务的多轮状态」
- 把第 11 节的扩展点真正做出来：换后端、加记忆策略（向量存储 / 重要性评分）、给子代理加更细的作用域控制

## 常见问题与排查

### Q1：代理启动后一直连不上 Ollama，报超时？

先确认 `ollama serve` 在跑，且 `--host` 默认是 `http://127.0.0.1:11434`。如果用的是远程或容器里的 Ollama，把 `--host` 指向可达地址，并检查防火墙。超时还能调 `--ollama-timeout`（默认 300 秒）。

### Q2：模型不按 `<tool>` / `<final>` 格式输出怎么办？

不同模型对这些自定义标签的遵循度不同。优先选指令遵循强的模型；如果是小模型经常出错，可以调高 `--temperature`（如 0.2 → 0.4）或换更大的模型。这也正是项目的「教学性」所在——它不隐藏格式约束，而是让你看到代理对模型输出的依赖。

### Q3：`--approval auto` 真的安全吗？

不安全，除非你完全信任当前代码库且环境隔离。`auto` 会直接执行所有读写和 Bash 命令，一旦模型判断失误可能删文件或跑危险命令。日常用 `ask`，只读场景才考虑 `never`。

### Q4：会话文件存在哪，能手动清理吗？

在项目的 `.mini-coding-agent/sessions/<session-id>/` 下，含 `transcript.json`、`memory.json`、`state.json`。可以直接删整个目录来清掉某次会话；`/reset` 则在 REPL 内清当前会话的历史与记忆但保留 REPL。

### Q5：小显存机器跑不动默认模型怎么办？

换更小的模型（如 `qwen2.5-coder:3b` 或 `llama3.2:3b`），同时把 `--max-new-tokens` 和 `--max-steps` 调小，缩短单次任务链，降低显存峰值。

### Q6：它和 Claude Code、Aider 比，我该用哪个？

如果你想学「代码代理到底怎么搭」，读 Mini-Coding-Agent 的 ~500 行源码最快；真要干活、要生产级能力，用 Claude Code / Aider。Mini-Coding-Agent 的价值在「可读懂、可改、可当起点」，不在功能完备。