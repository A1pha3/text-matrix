---
title: "YourMemory: 基于艾宾浩斯遗忘曲线的 Agentic AI 记忆系统深度解析"
date: "2026-04-27T08:17:54+08:00"
slug: "yourmemory-ebbinghaus-agent-memory"
description: "YourMemory 将艾宾浩斯遗忘曲线工程化为可配置的衰减算法，配合混合 BM25+向量+图检索两轮 pipeline，在 LoCoMo-10 基准上取得 59% Recall@5，大幅领先 Zep Cloud 等同类产品。默认本地存储零配置，5 步接入任意 MCP 客户端，适合需要跨会话记忆的 AI 开发工作流。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "Agent", "MCP", "记忆系统", "艾宾浩斯"]
---


## 📋 目录

- [项目概览](#项目概览)
- [核心问题：AI Agent 的记忆困境](#核心问题：ai-agent-的记忆困境)
- [遗忘曲线机制：艾宾浩斯方程的工程实现](#遗忘曲线机制：艾宾浩斯方程的工程实现)
- [混合检索：两轮召回 pipeline](#混合检索：两轮召回-pipeline)
- [存储架构：默认本地，按需扩展](#存储架构：默认本地，按需扩展)
- [快速开始：5 步接入任意 MCP 客户端](#快速开始：5-步接入任意-mcp-客户端)
- [MCP 工具：三个核心 API](#mcp-工具：三个核心-api)
- [多 Agent 共享记忆](#多-agent-共享记忆)
- [性能基准：59% Recall@5 的含义](#性能基准：59%-recall@5-的含义)
- [适用场景与边界](#适用场景与边界)

---


## 项目概览

**YourMemory** 是一个为 AI Agent 提供持久记忆能力的开源项目，核心特性是将人类记忆的遗忘机制——艾宾浩斯遗忘曲线（Ebbinghaus Forgetting Curve）——工程化为可配置的衰减算法。与传统记忆系统不同，YourMemory 让重要的记忆缓慢衰减、无关的记忆自动淡出，模拟人类认知的实际工作方式。

| 基础信息 | |
|---------|------|
| 仓库 | [sachitrafa/YourMemory](https://github.com/sachitrafa/YourMemory) |
| Stars | 66 |
| 语言 | Python |
| 许可证 | CC BY-NC 4.0 |
| 最新版本 | 1.4.1 |
| 基准测试 | Recall@5: **59%**（Zep Cloud 仅 28%） |

在 LoCoMo-10 基准测试中，YourMemory 以 59% 的 Recall@5 得分大幅领先同类产品，相比 Zep Cloud 提升超过 31 个百分点，且在全部 10 个多会话对话样本中均保持领先。

---

## 核心问题：AI Agent 的记忆困境

每一次新的对话，AI 助手都从零开始：重复询问相同的问题、遗忘用户的偏好设置、重新学习技术栈。现有解决方案要么依赖外部云服务（增加成本与隐私风险），要么采用简单的向量检索（无法捕捉记忆间的语义关联，更无法区分重要与不重要信息）。

YourMemory 的解决思路是：让记忆系统像人类一样工作——重要的事情记得更久，不重要的自然淡忘。通过将记忆按类别（strategy/fact/assumption/failure）分配不同的衰减速率，系统实现了"生物启发式"的记忆管理。

---

## 遗忘曲线机制：艾宾浩斯方程的工程实现

YourMemory 的核心创新在于将记忆衰减建模为可配置的数学方程。核心公式位于 `src/services/decay.py`：

```python
effective_λ = base_λ × (1 - importance × 0.8)
strength    = importance × e^(−effective_λ × days) × (1 + recall_count × 0.2)
```

其中：
- **base_λ** 是类别基础衰减率，由 `DECAY_RATES` 字典定义
- **importance** 是记忆重要性（0-1），越高衰减越慢
- **recall_count** 是被召回次数，每次召回都强化记忆（+20%）

四种类别对应不同的衰减速度：

| 类别 | 衰减率 λ | 不召回存活期（约） | 典型用途 |
|------|---------|-----------------|---------|
| **strategy** | 0.10 | ~38 天 | 成功模式、常用工作流 |
| **fact** | 0.16 | ~24 天 | 用户偏好、身份信息 |
| **assumption** | 0.20 | ~19 天 | 推断上下文 |
| **failure** | 0.35 | ~11 天 | 错误记录、环境问题 |

Failure 类别衰减最快——三个月前的限速错误现在很可能已经失效，不应继续占用记忆空间。Strategy 衰减最慢——经过验证的成功模式值得长期保留。

低于强度阈值 `0.05` 的记忆会在每日自动 job 中被裁剪（由 APScheduler 驱动）。

---

## 混合检索：两轮召回 pipeline

单纯依赖向量相似度的检索容易遗漏"词汇不同但语义相关"的记忆。YourMemory 采用两轮混合检索：

**第一轮：向量搜索**
使用 `sentence-transformers`（`all-mpnet-base-v2`，768 维）将记忆内容编码为向量，通过余弦相似度在 DuckDB 向量存储中检索 top-k 结果。

**第二轮：图扩展**
以第一轮结果为种子，通过 BFS 图遍历（NetworkX）寻找语义相关但词汇不同的记忆——连接阈值设为余弦相似度 ≥ 0.4。这解决了"问 Python 后端但返回 Docker/Kubernetes 相关信息"的问题。

最终得分：`score = cosine_similarity × strength`，即相似度与记忆强度的乘积。频繁被召回的记忆在强度层面获得加持，排名自然靠前。

```python
# recall_memory("Python backend")

## 🎯 学习目标

完成本文档后，你将能够：

- ✅ 理解项目的核心功能与应用场景
- ✅ 掌握安装配置和基本使用方法
- ✅ 了解技术架构和实现原理
- ✅ 能够解决实际使用中的问题
- ✅ 具备扩展和定制的能力

---

#   Round 1 → [1] Python/MongoDB    (sim=0.61)
#              [2] DuckDB/spaCy     (sim=0.19)
#   Round 2 → [5] Docker/Kubernetes (sim=0.29 — below cut-off, surfaced via graph)
```

---

## 存储架构：默认本地，按需扩展

YourMemory 默认使用本地存储，零配置即可运行：

| 组件 | 技术 | 路径 |
|------|------|------|
| 向量存储 | **DuckDB**（内置） | `~/.yourmemory/memories.duckdb` |
| 图存储 | **NetworkX**（pickle） | `~/.yourmemory/graph.pkl` |
| NLP 处理 | **spaCy**（本地） | 首次运行时下载 |
| 嵌入模型 | **sentence-transformers** | `all-mpnet-base-v2`，768 维 |
| 定时任务 | **APScheduler** | 每日内存修剪 |

可选扩展至生产级基础设施：

```python
# PostgreSQL + pgvector（团队场景）
pip install 'yourmemory[postgres]'
# DATABASE_URL=postgresql://user@localhost:5432/yourmemory

# Neo4j（图数据库）
pip install 'yourmemory[neo4j]'
```

---

## 快速开始：5 步接入任意 MCP 客户端

**Step 1 — 安装**
```bash
pip install yourmemory
```

**Step 2 — 初始化（一次性）**
```bash
yourmemory-setup
```
下载 spaCy 模型并创建本地数据库。

**Step 3 — 获取配置路径**
```bash
yourmemory-path
```
返回完整可执行文件路径，用于配置 MCP 客户端。

**Step 4 — 配置 MCP 客户端**

Claude Code：`~/.claude/settings.json` 添加：
```json
{
  "mcpServers": {
    "yourmemory": {
      "command": "yourmemory"
    }
  }
}
```

Claude Desktop：`~/Library/Application Support/Claude/claude_desktop_config.json` 添加相同配置。

其他客户端（Cline、Cursor、OpenCode、Windsurf 等）配置方式类似，详见 README。

**Step 5 — 加载记忆工作流**
```bash
cp sample_CLAUDE.md CLAUDE.md
```
编辑 `CLAUDE.md`，替换 `YOUR_NAME` 和 `YOUR_USER_ID`。之后 Claude 会自动遵循 recall → store → update 的记忆工作流。

---

## MCP 工具：三个核心 API

YourMemory 作为标准 stdio MCP 服务器，向 AI 客户端暴露三个工具：

| 工具 | 调用时机 | 功能 |
|------|---------|------|
| `recall_memory(query)` | 每个任务开始 | 按相似度 × 强度召回相关记忆 |
| `store_memory(content, importance, category)` | 学习新信息后 | 嵌入存储，应用生物衰减 |
| `update_memory(id, new_content)` | 信息过时 | 重新嵌入并替换原有记忆 |

示例：
```python
# 存储偏好
store_memory("Sachit 在 Python 中偏好 Tab 而非空格", importance=0.9, category="fact")

# 下次会话自动召回——无需重复告知
recall_memory("Python 格式化")
# → {"content": "Sachit 在 Python 中偏好 Tab 而非空格", "strength": 0.87}
```

---

## 多 Agent 共享记忆

多个 Agent 可以共享同一个 YourMemory 实例，通过 `register_agent` 实现权限隔离：

```python
from src.services.api_keys import register_agent

result = register_agent(
    agent_id="coding-agent",
    user_id="sachit",
    can_read=["shared", "private"],
    can_write=["shared", "private"],
)
# 返回 {"api_key": "ym_xxxx"}，仅显示一次
```

传递 `api_key` 参数后，Agent 访问记忆时会返回 shared 记忆加自身 private 记忆；其他 Agent 只能看到 shared 记忆。

---

## 性能基准：59% Recall@5 的含义

YourMemory 在 LoCoMo-10（Snap Research 发布的 10 个多会话对话数据集，共 1,534 个 QA 对）上的表现：

| 系统 | Recall@5 | 完成样本 |
|------|:--------:|:--------:|
| **YourMemory** | **59%** | 10/10 |
| Zep Cloud | 28% | 10/10 |
| Supermemory | 31% | 4/10（免费配额耗尽） |
| Mem0 | 18% | 6/10（免费配额耗尽） |

YourMemory 在全部 10 个样本中均领先 Zep Cloud，相对提升达 111%。除了解析准确性的因素外，核心原因是 YourMemory 的混合 BM25 + 向量 + 图检索 pipeline 保留了完整的会话摘要，而 Zep Cloud 等基于 LLM 摘要的系统在压缩过程中丢失了具体的日期、姓名和事件细节——恰恰是 LoCoMo QA 对测试的目标。

Token 效率方面，3 个会话累计节省 19.7% tokens；30 个会话后成本降幅达 84.1%——因为记忆块大小稳定在 76-91 tokens，而无记忆方案的历史上下文线性增长。

---

## 适用场景与边界

**适合的场景：**
- 需要跨会话记忆的 AI 编程助手（Claude Code、Cline、Cursor 等）
- 长期运行的 Agent 项目，需要区分重要与过时信息
- 多 Agent 协作，需要 shared + private 记忆隔离
- 对数据隐私有要求，不想使用第三方云服务

**不适合的场景：**
- 需要毫秒级响应的实时系统（本地向量检索有延迟）
- 需要处理超大规模记忆（>10 万条）的场景（建议扩展至 PostgreSQL + pgvector）
- 商业产品（CC BY-NC 许可证禁止未经授权的商业使用）

---


---

## 自测题

1. **本项目的主要功能是什么？**
   <details>
   <summary>查看答案</summary>
   请根据文章内容回答。
   </details>

2. **如何安装和配置本项目？**
   <details>
   <summary>查看答案</summary>
   请根据文章内容回答。
   </details>

3. **本项目的技术栈是什么？**
   <details>
   <summary>查看答案</summary>
   请根据文章内容回答。
   </details>

4. **如何使用本项目？**
   <details>
   <summary>查看答案</summary>
   请根据文章内容回答。
   </details>

5. **本项目适合什么场景？**
   <details>
   <summary>查看答案</summary>
   请根据文章内容回答。
   </details>

---

## 练习

### 练习 1：安装并运行项目

按照文章中的步骤，安装并运行项目，验证基本功能是否正常。

### 练习 2：自定义配置

根据文章中的说明，修改配置文件，尝试自定义功能。

### 练习 3：扩展开发

参考文章中的扩展指南，尝试开发自定义功能模块。

---

## 进阶路径

1. **深入理解项目架构**
   - 阅读项目源码
   - 理解核心模块的设计思路
   - 掌握关键技术栈

2. **掌握高级功能**
   - 学习高级配置选项
   - 掌握性能优化方法
   - 了解最佳实践

3. **参与开源贡献**
   - 提交 Issue 报告问题
   - 提交 Pull Request 贡献代码
   - 参与社区讨论

4. **应用到实际项目**
   - 在实际工作中使用本项目
   - 根据需求进行定制开发
   - 分享使用心得和经验

---

## 资料口径说明

本文基于以下来源编写：

1. **项目信息**：来自项目的 GitHub 仓库和官方文档
2. **技术描述**：基于相关技术的官方文档和社区最佳实践
3. **代码示例**：部分为说明性示例，实际使用时需要参考官方 API 文档
4. **局限性**：
   - 未实际部署和运行部分功能，技术细节可能需要进一步验证
   - 代码示例为说明性目的，可能需要根据实际情况调整
   - 部分功能描述基于文档和源码分析，实际效果需要验证

---

## 总结

YourMemory 将认知科学中经典的艾宾浩斯遗忘曲线转化为可工程的记忆衰减算法，配合混合 BM25 + 向量 + 图检索两轮 pipeline，在 LoCoMo-10 基准上以 59% Recall@5 大幅领先同类产品。默认本地存储、零配置启动、5 步接入任意 MCP 客户端的设计，大幅降低了 AI Agent 记忆系统的使用门槛。

对于需要在多会话中保持上下文一致性的 AI 开发工作流，YourMemory 提供了一套有科学依据、可配置、按重要性分层的记忆管理方案。

- 仓库地址：[github.com/sachitrafa/YourMemory](https://github.com/sachitrafa/YourMemory)
- 在线演示：[yourmemoryai.vercel.app](https://yourmemoryai.vercel.app/)
- 技术解读：[I built memory decay for AI agents using the Ebbinghaus forgetting curve](https://dev.to/sachit_mishra_686a94d1bb5/i-built-memory-decay-for-ai-agents-using-the-ebbinghaus-forgetting-curve-1b0e)