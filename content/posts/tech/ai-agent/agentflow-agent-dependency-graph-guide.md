---
title: "AgentFlow：智能体依赖图编排框架完全指南"
slug: "agentflow-agent-dependency-graph-guide"
aliases:
  - /posts/tech/agentflow-agent-dependency-graph-guide/
date: "2026-04-01T01:09:00+08:00"
categories: ["技术笔记"]
tags: ["AgentFlow", "智能体编排", "依赖图", "并行处理", "Fanout", "Claude", "Codex", "SSH", "远程执行", "Python"]
description: "智能体依赖图编排框架，支持并行扇出、迭代循环和零配置远程执行 SSH/EC2/ECS，通过 Graph 管道符实现高效的 AI 智能体工作流编排。"
---

# AgentFlow：智能体依赖图编排框架完全指南

> 预计阅读时间：30 分钟 | 难度：⭐⭐⭐

---

## 学习目标

阅读本文后，你将能够：

1. **理解 AgentFlow 的核心概念**：掌握依赖图编排、并行扇出、迭代循环等基本机制
2. **设计智能体管道**：使用 `>>` 管道符连接节点，构建清晰的依赖链
3. **实现并行处理**：使用 `fanout()` 实现整数模式、列表模式、字典模式的并行扇出
4. **配置远程执行**：使用零配置 SSH/EC2/ECS 远程执行智能体
5. **应用迭代优化**：使用 `on_failure` 和 `success_criteria` 实现自动重试循环

---

## 目录

- [§2 项目概述](#§2-项目概述)
- [§3 核心概念](#§3-核心概念)
- [§4 并行扇出（Fanout）](#§4-并行扇出 fanout)
- [§5 迭代循环](#§5-迭代循环)
- [§6 远程执行](#§6-远程执行)
- [§7 Scratchboard](#§7-scratchboard)
- [§8 安装与部署](#§8-安装与部署)
- [§9 CLI 命令](#§9-cli-命令)
- [§10 示例管道](#§10-示例管道)
- [§11 项目结构](#§11-项目结构)
- [§12 推荐做法](#§12-推荐做法)
- [§13 常见问题](#§13-常见问题)
- [§14 总结](#§14-总结)
- [§15 附录：API 参考](#§15-附录 api-参考)

---

## §2 项目概述

### 2.1 什么是 AgentFlow？

**AgentFlow**（[GitHub 仓库](https://github.com/shouc/agentflow)）是一个用于编排代码智能体的框架，支持在依赖图中并行扇出、迭代循环和远程执行。

**官方描述**：

> Orchestrate codex, claude, and kimi agents in dependency graphs with parallel fanout, iterative cycles, and remote execution on SSH/EC2/ECS.

**核心功能**：将多个 AI 智能体（Codex、Claude、Kim）编排为依赖图，实现并行处理、迭代优化和远程执行。

### 2.2 核心数据

| 指标 | 数值 |
|------|------|
| **Stars** | 277 |
| **Forks** | 52 |
| **提交数** | 715 |
| **分支数** | 2 |
| **贡献者** | 3 (@shouc, @claude, @n-WN) |

### 2.3 技术栈

| 类别 | 技术 | 占比 |
|------|------|------|
| **核心语言** | Python | 90.6% |
| **前端** | JavaScript | 6.7% |
| **标记** | HTML | 1.9% |

### 2.4 核心特性

| 特性 | 说明 |
|------|------|
| **依赖图编排** | 使用 `>>` 管道符连接节点 |
| **并行扇出** | 三种模式：整数/列表/字典 |
| **迭代循环** | 失败时自动重试直到成功 |
| **远程执行** | 零配置 SSH/EC2/ECS |
| **共享内存** | Scratchboard 跨智能体文件共享 |
| **结果归约** | merge 支持批量和分组 |

---

## §3 核心概念

### 3.1 依赖图

AgentFlow 使用有向无环图（DAG）组织智能体节点。节点之间通过 `>>` 管道符连接，表示依赖关系。

**基本语法**：

```python
from agentflow import Graph, codex, claude

with Graph("my-pipeline", concurrency=3) as g:
    plan = codex(task_id="plan", prompt="Inspect the repo and plan the work.", tools="read_only")
    impl = claude(task_id="impl", prompt="Implement the plan:\n{{ nodes.plan.output }}", tools="read_write")
    review = codex(task_id="review", prompt="Review:\n{{ nodes.impl.output }}")

    plan >> impl >> review  # 依赖链

print(g.to_json())
```

### 3.2 节点类型

| 节点类型 | 说明 | 典型用途 |
|----------|------|----------|
| **codex** | Codex 智能体 | 代码生成/审查 |
| **claude** | Claude 智能体 | 复杂推理/审查 |
| **fanout** | 并行扇出 | 批量处理 |
| **merge** | 结果归约 | 汇总结果 |

### 3.3 管道操作符

`>>` 用于连接节点，表示「前一个节点的输出作为后一个节点的输入」：

```python
plan >> impl >> review
# plan 的输出 → impl 的输入 → review 的输入
```

### 3.4 模板语法

使用 `{{ nodes.<node_id>.output }}` 引用上游节点的输出：

```python
impl = claude(
    task_id="impl",
    prompt="Implement the plan:\n{{ nodes.plan.output }}"
)
```

---

## §4 并行扇出（Fanout）

### 4.1 Fanout 概述

`fanout()` 是 AgentFlow 的核心功能之一，将单个节点扇出为多个并行执行实例。

**三种扇出模式**：

| 模式 | 参数类型 | 说明 |
|------|----------|------|
| **整数模式** | `int` | N 个相同副本 |
| **列表模式** | `list` | 每个元素一个副本 |
| **字典模式** | `dict` | 笛卡尔积 |

### 4.2 整数模式

整数模式创建 N 个完全相同的并行副本：

```python
fanout(codex(task_id="fuzz", prompt="..."), 128)
# 创建 128 个完全相同的 codex 实例
```

### 4.3 列表模式

列表模式为每个元素创建一个副本：

```python
fanout(
    codex(task_id="review", prompt="Review {{ item.file }}:\n{{ nodes.scan.output }}"),
    [
        {"file": "api.py"},
        {"file": "auth.py"},
        {"file": "db.py"}
    ]
)
```

### 4.4 字典模式

字典模式创建笛卡尔积：

```python
fanout(
    codex(task_id="test", prompt="..."),
    {"axis1": ["a", "b"], "axis2": [1, 2]}
)
# 4 个组合: (a,1), (a,2), (b,1), (b,2)
```

### 4.5 代码审查示例

```python
from agentflow import Graph, codex, fanout, merge

with Graph("code-review", concurrency=8) as g:
    scan = codex(task_id="scan", prompt="List the top 5 files to review.")

    review = fanout(
        codex(task_id="review", prompt="Review {{ item.file }}:\n{{ nodes.scan.output }}"),
        [{"file": "api.py"}, {"file": "auth.py"}, {"file": "db.py"}]
    )

    summary = codex(
        task_id="summary",
        prompt="Merge findings:\n{% for r in fanouts.review.nodes %}{{ r.output }}\n{% endfor %}"
    )

    scan >> review >> summary
```

---

## §5 迭代循环

### 5.1 迭代概述

`on_failure` 属性实现迭代循环，当节点失败时自动重试上游节点，直到满足成功条件或达到最大迭代次数。

### 5.2 成功条件

通过 `success_criteria` 定义成功条件：

```python
review = claude(
    task_id="review",
    prompt="Review:\n{{ nodes.write.output }}\nIf complete, say LGTM. Otherwise list issues.",
    success_criteria=[{"kind": "output_contains", "value": "LGTM"}]
)
```

### 5.3 迭代示例

```python
from agentflow import Graph, codex, claude

with Graph("iterative-impl", max_iterations=5) as g:
    write = codex(
        task_id="write",
        prompt="Write a Python email validator.\n{% if nodes.review.output %}Fix: {{ nodes.review.output }}{% endif %}",
        tools="read_write"
    )

    review = claude(
        task_id="review",
        prompt="Review:\n{{ nodes.write.output }}\nIf complete, say LGTM. Otherwise list issues.",
        success_criteria=[{"kind": "output_contains", "value": "LGTM"}]
    )

    write >> review
    review.on_failure >> write  # 失败时循环回 write

print(g.to_json())
```

**执行流程**：
1. write 生成代码
2. review 审查
3. 如果 review 失败（不是 LGTM），重试 write
4. 重复直到 review 成功或达到 5 次迭代

---

## §6 远程执行

### 6.1 远程执行概述

AgentFlow 支持零配置远程执行，无需手动设置基础设施。

### 6.2 EC2 执行

```python
codex(
    task_id="remote",
    prompt="...",
    target={"kind": "ec2", "region": "us-east-1"}
)
```

**自动发现**：AMI、密钥对、VPC。

### 6.3 ECS Fargate 执行

```python
codex(
    task_id="remote",
    prompt="...",
    target={"kind": "ecs", "region": "us-east-1"}
)
```

**自动发现**：VPC，构建智能体镜像。

### 6.4 SSH 执行

```python
codex(
    task_id="remote",
    prompt="...",
    target={"kind": "ssh", "host": "server", "username": "deploy"}
)
```

### 6.5 共享实例

使用 `shared` 参数让多个节点共享同一远程实例：

```python
plan = codex(
    task_id="plan",
    prompt="...",
    target={"kind": "ec2", "shared": "dev-box"}
)
impl = codex(
    task_id="impl",
    prompt="...",
    target={"kind": "ec2", "shared": "dev-box"}
)
plan >> impl  # 同一 EC2 实例，文件持久化
```

---

## §7 Scratchboard

### 7.1 Scratchboard 概述

Scratchboard 是跨所有智能体共享的内存文件，用于在并行任务间共享数据。

### 7.2 使用示例

```python
with Graph("campaign", scratchboard=True) as g:
    shards = fanout(
        codex(task_id="fuzz", prompt="..."),
        128
    )
    # 所有 128 个并行任务可以读写同一文件
```

---

## §8 安装与部署

### 8.1 一键安装（推荐）

```bash
curl -fsSL https://raw.githubusercontent.com/shouc/agentflow/master/install.sh | bash
```

这会安装 agentflow、添加到 PATH，并安装 Codex 和 Claude Code 的 skill。

### 8.2 手动安装

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
```

---

## §9 CLI 命令

### 9.1 核心命令

| 命令 | 说明 |
|------|------|
| `agentflow run pipeline.py` | 运行管道 |
| `agentflow run pipeline.py --output summary` | 运行并输出摘要 |
| `agentflow inspect pipeline.py` | 显示展开的图 |
| `agentflow validate pipeline.py` | 验证但不运行 |
| `agentflow templates` | 列出起始模板 |
| `agentflow init > pipeline.py` | 脚手架起始模板 |

---

## §10 示例管道

### 10.1 基础管道

```python
# airflow_like.py - Basic pipeline: plan → implement → review → merge
```

### 10.2 代码审查

```python
# code_review.py - Fan out code review across files, merge findings
```

### 10.3 依赖审计

```python
# dep_audit.py - Audit each dependency for security/license issues
```

### 10.4 测试覆盖

```python
# test_gap.py - Find untested modules, suggest tests per module
```

### 10.5 多智能体辩论

```python
# multi_agent_debate.py - Codex vs Claude: independent solve + cross-critique
```

### 10.6 发布检查

```python
# release_check.py - Parallel release gate: tests + security + changelog
```

### 10.7 迭代实现

```python
# iterative_impl.py - Write → review → fix cycle until LGTM
```

### 10.8 批量扇出

```python
# airflow_like_fuzz_batched.py - 128-shard fanout with batch merge + periodic monitor
```

### 10.9 分组扇出

```python
# airflow_like_fuzz_grouped.py - Matrix fanout with grouped reducers
```

### 10.10 远程 EC2

```python
# ec2_remote.py - Run codex on a remote EC2 instance
```

### 10.11 远程 ECS

```python
# ecs_fargate.py - Run codex on ECS Fargate
```

---

## §11 项目结构

### 11.1 目录结构

```
agentflow/
├── agentflow/           # 核心源代码
├── docs/                # 文档
├── examples/            # 示例管道
├── skills/
│   └── agentflow/       # AgentFlow skill
├── tests/               # 测试
├── .github/workflows/   # GitHub Actions
├── pyproject.toml       # Python 项目配置
├── Makefile            # 构建脚本
├── install.sh          # 一键安装脚本
└── README.md          # 项目文档
```

### 11.2 核心模块

| 模块 | 说明 |
|------|------|
| **agentflow/** | 核心 Graph 和节点实现 |
| **skills/agentflow/** | AgentFlow skill for Codex/Claude |
| **examples/** | 各种示例管道 |

---

## §12 推荐做法

### 12.1 管道设计

| 原则 | 说明 |
|------|------|
| **单一职责** | 每个节点只做一件事 |
| **适度并行** | 并行数不要超过实际需求 |
| **明确依赖** | 使用清晰的管道连接 |

### 12.2 远程执行

| 建议 | 说明 |
|------|------|
| **共享实例** | 同项目节点使用 shared 参数 |
| **区域选择** | 选择靠近数据的区域 |

### 12.3 迭代循环

| 建议 | 说明 |
|------|------|
| **设置上限** | 始终设置 max_iterations |
| **明确条件** | 使用具体的 success_criteria |

---

## §13 常见问题

### Q1：如何选择智能体类型？

| 场景 | 推荐 |
|------|------|
| **代码生成** | codex |
| **复杂推理** | claude |
| **批量处理** | fanout + codex/claude |

### Q2：如何控制并行度？

通过 `Graph` 的 `concurrency` 参数：

```python
with Graph("my-pipeline", concurrency=8) as g:
    ...
```

### Q3：如何调试管道？

使用 `agentflow inspect` 查看展开的图：

```bash
agentflow inspect pipeline.py
```

---

## §14 总结

### 14.1 核心优势

| 优势 | 说明 |
|------|------|
| **图编排** | 清晰的依赖关系 |
| **并行处理** | 高效批量任务 |
| **迭代优化** | 自动修复直到成功 |
| **零配置远程** | 一行代码部署到云 |
| **共享内存** | 并行任务数据共享 |

### 14.2 适用场景

| 场景 | 适用性 |
|------|--------|
| **代码审查** | 并行审查多文件 |
| **自动化测试** | 迭代修复直到通过 |
| **数据处理** | 大规模批量处理 |
| **模型评估** | 多配置并行实验 |

### 14.3 项目信息

| 项目 | 信息 |
|------|------|
| **Stars** | 277 |
| **Forks** | 52 |
| **提交数** | 715 |
| **贡献者** | 3 |

### 14.4 相关链接

| 资源 | 链接 |
|------|------|
| **GitHub** | https://github.com/shouc/agentflow |
| **安装** | `curl -fsSL https://raw.githubusercontent.com/shouc/agentflow/master/install.sh \| bash` |

---

## 自测题

### 问题 1：AgentFlow 的核心编排机制是什么？

<details>
<summary>查看答案</summary>

AgentFlow 使用有向无环图（DAG）组织智能体节点，节点之间通过 `>>` 管道符连接，表示依赖关系。

</details>

### 问题 2：如何实现并行扇出？

<details>
<summary>查看答案</summary>

使用 `fanout()` 函数，支持三种模式：
- 整数模式：创建 N 个相同副本
- 列表模式：为每个元素创建一个副本
- 字典模式：创建笛卡尔积组合

</details>

### 问题 3：如何实现迭代循环？

<details>
<summary>查看答案</summary>

使用 `on_failure` 属性实现迭代循环，当节点失败时自动重试上游节点，直到满足成功条件（`success_criteria`）或达到最大迭代次数（`max_iterations`）。

</details>

### 问题 4：如何配置远程执行？

<details>
<summary>查看答案</summary>

通过 `target` 参数配置远程执行，支持三种方式：
- EC2：`{"kind": "ec2", "region": "us-east-1"}`
- ECS Fargate：`{"kind": "ecs", "region": "us-east-1"}`
- SSH：`{"kind": "ssh", "host": "server", "username": "deploy"}`

</details>

### 问题 5：Scratchboard 的作用是什么？

<details>
<summary>查看答案</summary>

Scratchboard 是跨所有智能体共享的内存文件，用于在并行任务间共享数据。通过 `Graph(scratchboard=True)` 启用。

</details>

---

## 练习

### 练习 1：构建基础代码审查管道

**任务**：创建一个 AgentFlow 管道，使用 Codex 扫描代码文件，然后并行审查多个文件，最后汇总审查结果。

**提示**：
- 使用 `codex(task_id="scan", prompt="List files to review.")` 扫描文件
- 使用 `fanout()` 并行审查多个文件
- 使用 `codex(task_id="summary", prompt="Merge findings: ...")` 汇总结果

**参考答案**：
```python
# 参考示例代码在 §4.5 代码审查示例
```

### 练习 2：实现迭代实现循环

**任务**：创建一个迭代循环，使用 Codex 生成代码，Claude 审查，如果审查不通过（不是 LGTM），则重新生成代码。

**提示**：
- 使用 `success_criteria=[{"kind": "output_contains", "value": "LGTM"}]` 定义成功条件
- 使用 `review.on_failure >> write` 实现循环

**参考答案**：
```python
# 参考示例代码在 §5.3 迭代示例
```

### 练习 3：配置远程 EC2 执行

**任务**：修改示例管道，使其在远程 EC2 实例上运行代码生成任务。

**提示**：
- 使用 `target={"kind": "ec2", "region": "us-east-1"}` 配置远程执行
- 使用 `shared` 参数让多个节点共享同一实例

**参考答案**：
```python
# 参考示例代码在 §6.2 EC2 执行 和 §6.5 共享实例
```

---

## 进阶路径

如果你已经掌握本文内容，可以继续深入以下方向：

1. **贡献到 AgentFlow 项目**：阅读 `CONTRIBUTING.md`，了解如何贡献代码、文档或示例
2. **探索高级模式**：研究 `examples/` 目录中的高级示例（如多智能体辩论、批量模糊测试）
3. **集成到 CI/CD**：将 AgentFlow 管道集成到 GitHub Actions 或 Jenkins，实现自动化代码审查
4. **自定义智能体类型**：扩展 AgentFlow 以支持其他 AI 智能体（如 Kimi、GPT）
5. **性能优化**：研究如何优化大规模并行执行的性能和成本
6. **监控和调试**：构建管道执行监控系统，实时查看节点状态和日志
7. **生产化部署**：将 AgentFlow 部署到生产环境，考虑高可用、容错、安全等因素

---

## 资料口径说明

本文档基于以下来源和假设：

1. **信息来源**：本文基于 AgentFlow GitHub 仓库（https://github.com/shouc/agentflow）的 README、示例代码和 API 文档。
2. **版本时效性**：本文描述的是 AgentFlow 主分支（master）的代码，可能与你使用的版本存在差异。建议对照官方文档验证。
3. **代码示例**：本文的代码示例来自官方示例，未经完整运行验证。在实际使用前，请先在小规模场景中测试。
4. **性能数据**：本文未提供性能基准测试数据。实际性能取决于智能体类型、并行度、远程执行配置等因素。
5. **限制说明**：AgentFlow 是一个相对年轻的项目（Stars 277，提交数 715），可能存在未发现的 Bug 或未完成的功能。生产使用前请充分测试。
6. **更新记录**：本文最后更新于 2026-04-01。如果项目有重大更新，请及时更新本文档。

---

## §15 附录：API 参考

### 15.1 Graph 类

```python
Graph(name, concurrency=1, max_iterations=None, scratchboard=False)
```

### 15.2 节点函数

| 函数 | 说明 |
|------|------|
| `codex(task_id, prompt, tools, target, success_criteria)` | Codex 节点 |
| `claude(task_id, prompt, tools, target, success_criteria)` | Claude 节点 |
| `fanout(node, source)` | 并行扇出 |
| `merge(node, source, size, by)` | 结果归约 |

### 15.3 管道操作

| 操作 | 说明 |
|------|------|
| `>>` | 连接节点 |
| `.on_failure` | 失败时循环 |
