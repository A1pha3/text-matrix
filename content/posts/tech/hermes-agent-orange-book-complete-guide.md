---
title: "Hermes Agent 橙皮书：从入门到精通的完整指南"
date: "2026-04-11T10:30:00+08:00"
slug: "hermes-agent-orange-book-complete-guide"
description: "Nous Research开源的Hermes Agent是首个内置自进化学习循环的AI Agent框架。本文基于橙皮书，涵盖17章节5大部分，从核心概念到实战，再到与OpenClaw/Claude Code的三方对比。"
categories: ["技术笔记"]
tags: ["Hermes Agent", "Nous Research", "AI Agent", "自进化", "橙皮书", "花叔"]
draft: false
---

# Hermes Agent 橙皮书：从入门到精通 ⭐⭐⭐

> **难度**：⭐⭐⭐（进阶）
> **类型**：实战指南 + 深度分析
> **适合人群**：希望深入理解 Hermes Agent 的开发者、想构建个人 AI Agent 的爱好者
> **前置知识**：有 AI Assistant 使用经验（Claude Code / OpenClaw / Cursor 任一即可）
> **作者**：钳岳星君 🦞
> **参考资源**：橙皮书 v260408 | Hermes Agent v0.7.0

---

## 🎯 学习目标

完成本指南后，你将能够：

- [ ] **理解** Hermes Agent 的核心创新点（内置自进化循环）
- [ ] **掌握** 三层记忆系统的原理和作用
- [ ] **运用** 内置 Skill 创建和演化机制
- [ ] **部署** Hermes Agent 到多平台（CLI、Telegram、Discord 等）
- [ ] **对比** Hermes Agent、OpenClaw、Claude Code 的优劣
- [ ] **构建** 属于自己的个人 AI Agent

---

## 📚 目录

1. [第一章：什么是 Hermes Agent](#第一章什么是-hermes-agent)
2. [第二章：为什么 Hermes 是革命性的](#第二章为什么-hermes-是革命性的)
3. [第三章：核心机制——自进化循环](#第三章核心机制自进化循环)
4. [第四章：三层记忆系统](#第四章三层记忆系统)
5. [第五章：Skill 创建与演化](#第五章skill-创建与演化)
6. [第六章：工具生态](#第六章工具生态)
7. [第七章：实战上手——安装与配置](#第七章实战上手安装与配置)
8. [第八章：多平台部署](#第八章多平台部署)
9. [第九章：定制化与调优](#第九章定制化与调优)
10. [第十章：实战场景——知识助手](#第十章实战场景知识助手)
11. [第十一章：实战场景——开发自动化](#第十一章实战场景开发自动化)
12. [第十二章：实战场景——内容创作](#第十二章实战场景内容创作)
13. [第十三章：多 Agent 协作](#第十三章多-agent-协作)
14. [第十四章：深度思考——三方对比](#第十四章深度思考三方对比)
15. [第十五章：自进化 Agent 的边界](#第十五章自进化-agent-的边界)
16. [常见问题与资源](#常见问题与资源)

---

## 第一章：什么是 Hermes Agent ⭐

### 1.1 一句话解释

> **Hermes Agent** 是由 Nous Research 于 2026 年 2 月发布的开源 AI Agent 框架，与 OpenClaw 和 Claude Code 不同的是——它**内置自进化学习循环**，让 Agent 能够"边干边学"，而且这个"缰绳"还在不断生长。

### 1.2 与传统 Agent 的本质区别

```
传统 Agent（OpenClaw / Claude Code）：

启动时：加载系统提示词
    ↓
执行任务：按照预设流程工作
    ↓
结束：Agent 遗忘所有经验
    ↓
下次：还是从零开始

Hermes Agent：

启动时：加载系统提示词 + 历史记忆（Skills）
    ↓
执行任务：按照预设流程工作
    ↓
过程中：自动记录新知识、更新 Skills
    ↓
结束：Skills 已经进化，下次更强
```

### 1.3 核心数据

| 指标 | 数值 |
|------|------|
| **发布** | 2026 年 2 月 |
| **Stars** | 1.5k+ |
| **版本** | v0.7.0 |
| **文档** | hermes-agent.nousresearch.com |
| **开源** | GitHub/NousResearch/hermes-agent |

---

## 第二章：为什么 Hermes 是革命性的 ⭐⭐

### 2.1 Harness Engineering 的产品化

Hermes 是《Harness Engineering》橙皮书概念的第一个**落地产品**。

《Harness Engineering》提出的五组件框架：

```
Harness Engineering 五组件：

1. Instructions（指令）—— 告诉 Agent 怎么做
2. Constraints（约束）—— 限制 Agent 不能做什么
3. Feedback（反馈）—— 让 Agent 知道做得好不好
4. Memory（记忆）—— 存储经验和知识
5. Orchestration（编排）—— 协调各组件工作

Hermes 实现了全部五组件：
- Instructions → Skills
- Constraints → 内置安全约束
- Feedback → 自进化循环
- Memory → 三层记忆系统
- Orchestration → Agent 协调器
```

### 2.2 三个关键创新

```
Hermes 的三大创新：

┌─────────────────────────────────────────┐
│  创新 1：内置学习循环                      │
│  不是靠外部框架，是 Agent 自己记录、自己学习  │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  创新 2：三层记忆系统                      │
│  L0/L1/L2 分层记忆，按需加载              │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  创新 3：Skill 自动演化                   │
│  高频使用的模式自动固化为可复用 Skills      │
└─────────────────────────────────────────┘
```

### 2.3 与竞品的定位差异

| 维度 | Claude Code | OpenClaw | Hermes Agent |
|------|-------------|----------|-------------|
| **定位** | AI 编程助手 | 多平台 Agent | 自进化 Agent |
| **学习方式** | 会话内学习 | 通过 Skills | 自动演化 |
| **记忆持久化** | 无 | Skills 可选 | 内置三层记忆 |
| **多平台** | 仅 CLI | 主流平台 | 全部支持 |
| **适合人群** | 程序员 | 开发者 | 所有人 |

---

## 第三章：核心机制——自进化循环 ⭐⭐⭐

### 3.1 什么是自进化循环？

```
自进化循环的工作流程：

┌──────────────┐
│   执行任务     │
└──────┬───────┘
       ↓
┌──────▼───────┐
│   记录反馈     │ ← 成功/失败/改进点
└──────┬───────┘
       ↓
┌──────▼───────┐
│   更新记忆     │ ← 写入三层记忆系统
└──────┬───────┘
       ↓
┌──────▼───────┐
│   演化 Skills │ ← 高频模式固化为 Skill
└──────┬───────┘
       ↓
┌──────▼───────┐
│   下次更强     │
└──────────────┘
```

### 3.2 自进化的三个阶段

```python
# Hermes Agent 的自进化三个阶段

# 阶段 1：即时反馈（Execution Phase）
# Agent 执行任务时，实时记录反馈
feedback = {
    'task': '写一个 Python 函数',
    'result': 'success',
    'quality': 'good',
    'improvements': ['用了更简洁的写法']
}

# 阶段 2：记忆沉淀（Reflection Phase）
# 任务完成后，将反馈写入记忆系统
memory_store.write(
    layer='L1',  # 根据反馈重要性选择层级
    content=feedback,
    tags=['python', 'code-quality']
)

# 阶段 3：Skill 演化（Evolution Phase）
# 当某个模式出现多次，自动创建/更新 Skill
if pattern_frequency > threshold:
    skill = create_skill(
        name='python-clean-code',
        trigger='写 Python 函数',
        content=feedback['improvements']
    )
```

### 3.3 自进化的优势

```
自进化 vs 静态 Agent：

静态 Agent（Claude Code / OpenClaw）：
- 每次新会话都是从零开始
- 需要手动创建 Skills
- Skills 可能过时

自进化 Hermes：
- 自动识别高频模式
- 主动更新已有 Skills
- 越用越懂你
```

---

## 第四章：三层记忆系统 ⭐⭐⭐

### 4.1 为什么需要三层记忆？

```
记忆管理的挑战：

太少的记忆 → Agent 记不住关键信息
太多的记忆 → Agent 被淹没，找不到重点

解决方案：分层记忆，按需加载

┌────────────────────────────────────┐
│  L0 工作记忆（Working Memory）        │
│  - 只保留当前任务的上下文            │
│  - 每次会话重置                     │
│  - Token 消耗最低                   │
└────────────────────────────────────┘
              ↓
┌────────────────────────────────────┐
│  L1 情景记忆（Episodic Memory）      │
│  - 近期任务的反馈和经验              │
│  - 按时间衰减                        │
│  - 有选择性地保留                    │
└────────────────────────────────────┘
              ↓
┌────────────────────────────────────┐
│  L2 语义记忆（Semantic Memory）      │
│  - 固化的 Skills 和知识              │
│  - 长期保留                          │
│  - Agent 的"智慧结晶"               │
└────────────────────────────────────┘
```

### 4.2 各层详解

| 层级 | 名称 | 内容 | 生命周期 | Token 消耗 |
|------|------|------|----------|-----------|
| **L0** | Working | 当前任务上下文 | 会话内 | ~50 tokens |
| **L1** | Episodic | 近期反馈和经验 | 1-4 周 | ~500 tokens |
| **L2** | Semantic | Skills 和知识 | 长期 | ~2K tokens |

### 4.3 记忆加载机制

```python
# Hermes 的智能记忆加载

class MemoryLoader:
    """根据任务类型动态加载记忆"""
    
    def load(self, task_context):
        # 1. 始终加载 L0（工作记忆）
        l0 = self.load_working_memory()
        
        # 2. 根据任务相关性加载 L1
        l1_relevant = self.filter_by_relevance(
            self.load_episodic_memory(),
            task_context
        )
        
        # 3. 加载相关的 L2 Skills
        l2_skills = self.load_skills(
            tags=self.extract_tags(task_context)
        )
        
        # 4. 组装上下文
        return self.assemble_context(l0, l1_relevant, l2_skills)
```

---

## 第五章：Skill 创建与演化 ⭐⭐⭐

### 5.1 什么是 Skill？

```
Skill = 可复用的任务模板

没有 Skill：
"写一个 Python 函数来处理 JSON"
  → 每次都要解释细节

有 Skill：
"写 Python 函数"
  → 自动应用预设的格式、风格、最佳实践
```

### 5.2 Skill 的结构

```yaml
# example-skill.yaml
name: python-json-handler
description: 处理 JSON 数据的 Python 函数

trigger:
  - "写 Python 函数"
  - "处理 JSON"
  - "Python JSON"

template: |
  import json
  from typing import Any, Optional

  def {{ function_name }}(data: {{ input_type }}) -> {{ output_type }}:
      """{{ description }}"""
      try:
          # 你的代码
          result = json.loads(data) if isinstance(data, str) else data
          return result
      except json.JSONDecodeError as e:
          # 错误处理
          print(f"JSON 解析错误: {e}")
          return None

examples:
  - input: '{"key": "value"}'
    output: {'key': 'value'}

tags:
  - python
  - json
  - data-processing
```

### 5.3 Skill 的自动演化

```
Skill 演化流程：

第 1 次：检测到"处理 JSON"模式
    ↓
第 2 次：再次出现"处理 JSON"
    ↓
第 3 次：第三次出现 → 创建 Skill
    ↓
后续：Skill 被引用时，观察使用效果
    ↓
效果差：自动调整 Skill 模板
    ↓
效果好：Skill 固化，L1 记忆减少
```

---

## 第六章：工具生态 ⭐⭐

### 6.1 支持的平台

Hermes Agent 支持多种运行平台：

| 平台 | 支持情况 | 特点 |
|------|---------|------|
| **CLI** | ✅ 完全支持 | 最基础、最灵活 |
| **Telegram** | ✅ 完全支持 | 随时随地对话 |
| **Discord** | ✅ 完全支持 | 团队协作 |
| **Slack** | ✅ 完全支持 | 企业集成 |
| **WhatsApp** | ✅ 完全支持 | 日常沟通 |
| **Web** | 开发中 | 即将支持 |

### 6.2 工具调用能力

```python
# Hermes Agent 的工具调用示例

# 内置工具
tools = [
    'bash',      # 执行 shell 命令
    'grep',      # 文件搜索
    'read',      # 读取文件
    'write',     # 写入文件
    'edit',      # 编辑文件
    'web_search', # 网页搜索
    'browser',   # 浏览器控制
]

# 通过 MCP 扩展
mcp_tools = [
    'filesystem',  # 文件系统
    'database',   # 数据库
    'api',        # API 调用
    'memory',     # 记忆管理
]
```

---

## 第七章：实战上手——安装与配置 ⭐

### 7.1 安装要求

```bash
# 环境要求
- Python >= 3.10
- Node.js >= 18 (用于某些插件)
- Git
- 至少 4GB RAM

# 推荐
- 8GB+ RAM（用于大模型）
- GPU（可选，加速推理）
```

### 7.2 快速开始

```bash
# 1. 安装 Hermes Agent
npm install -g @nousresearch/hermes-agent

# 2. 配置 API Key（支持多种模型）
export OPENAI_API_KEY=sk-xxxx
export ANTHROPIC_API_KEY=sk-ant-xxxx

# 3. 启动 CLI 版本
hermes

# 4. 首次运行，自动初始化
# - 创建配置目录 ~/.hermes
# - 初始化三层记忆系统
# - 下载基础 Skills
```

### 7.3 配置文件

```yaml
# ~/.hermes/config.yaml

model:
  provider: anthropic  # anthropic | openai | local
  model: claude-sonnet-4-20250514
  
memory:
  l0_size: 50        # tokens
  l1_size: 500        # tokens
  l1_decay: 2weeks   # 自动衰减周期
  
skills:
  auto_evolution: true  # 自动演化
  evolution_threshold: 3  # 触发阈值
  
platforms:
  cli: enabled
  telegram: disabled
  discord: disabled
```

---

## 第八章：多平台部署 ⭐⭐

### 8.1 Telegram 部署

```bash
# 1. 创建 Telegram Bot
# - 找 @BotFather 获取 token

# 2. 配置
export TELEGRAM_BOT_TOKEN=your_token

# 3. 启动
hermes --platform telegram
```

### 8.2 Discord 部署

```bash
# 1. 创建 Discord Application
# - https://discord.com/developers/applications

# 2. 获取 Bot Token

# 3. 配置
export DISCORD_BOT_TOKEN=your_token
export DISCORD_GUILD_ID=your_guild

# 4. 启动
hermes --platform discord
```

### 8.3 多平台同时运行

```bash
# 可以同时启用多个平台
hermes \
  --platform cli \
  --platform telegram \
  --platform discord
```

---

## 第九章：定制化与调优 ⭐⭐

### 9.1 自定义 System Prompt

```yaml
# ~/.hermes/custom-prompt.yaml

persona: |
  你是一个专业的产品经理 AI 助手。
  - 擅长需求分析和PRD撰写
  - 熟悉敏捷开发流程
  - 说话简洁有条理

rules:
  - 先确认需求再开始写代码
  - 每个功能都要有测试
  - 代码要符合 PEP 8
```

### 9.2 调整记忆参数

```python
# 根据使用场景调整

# 场景 1：日常对话（低资源消耗）
memory_config = {
    'l0_size': 50,
    'l1_size': 200,
    'l1_decay': '1week'
}

# 场景 2：专业开发（高质量输出）
memory_config = {
    'l0_size': 100,
    'l1_size': 1000,
    'l1_decay': '1month',
    'auto_evolution': True
}
```

---

## 第十章：实战场景——知识助手 ⭐⭐

### 10.1 场景描述

构建一个个人知识助手，可以：
- 回答关于你项目的问题
- 记住你的代码风格和习惯
- 主动推荐改进建议

### 10.2 配置示例

```yaml
# knowledge-assistant.yaml

name: 我的知识助手

skills:
  - name: project-context
    description: 项目背景知识
    trigger:
      - "这个项目是做什么的"
      - "项目背景"
    content: |
      这是一个 Python Web 项目，使用 FastAPI 框架。
      数据库是 PostgreSQL，缓存用 Redis。
      代码风格遵循 PEP 8。
      
  - name: code-style
    description: 我的代码风格
    trigger:
      - "代码风格"
      - "怎么写"
    content: |
      - 使用类型注解
      - 函数要写 docstring
      - 错误处理用自定义异常类
```

### 10.3 使用效果

```
用户：Hermes，这个函数可以怎么改进？

Hermes（加载了 project-context + code-style）：
根据你的代码风格（类型注解 + docstring），
建议将函数改为：

def get_user(user_id: int) -> Optional[User]:
    """
    获取用户信息
    
    Args:
        user_id: 用户 ID
        
    Returns:
        User 对象或 None
        
    Raises:
        UserNotFoundError: 用户不存在
    """
    ...
```

---

## 第十一章：实战场景——开发自动化 ⭐⭐

### 11.1 场景描述

Hermes Agent 可以帮助：
- 自动化代码审查
- 自动生成测试
- 持续集成集成

### 11.2 代码审查 Skill

```yaml
# code-review-skill.yaml

name: python-code-review
description: Python 代码审查

trigger:
  - "审查代码"
  - "review"
  - "代码有什么问题"

template: |
  ## 代码审查报告
  
  ### 1. 安全性
  {{ security_analysis }}
  
  ### 2. 性能
  {{ performance_analysis }}
  
  ### 3. 可读性
  {{ readability_analysis }}
  
  ### 4. 建议
  {{ suggestions }}
```

---

## 第十二章：实战场景——内容创作 ⭐

### 12.1 场景描述

Hermes Agent 可以：
- 写博客文章
- 生成社交媒体内容
- 创作技术文档

### 12.2 内容创作 Skill

```yaml
# blog-writer-skill.yaml

name: tech-blog-writer
description: 技术博客写作助手

trigger:
  - "写博客"
  - "写文章"
  - "写文档"

template: |
  ## {{ title }}
  
  ### 背景
  {{ background }}
  
  ### 核心内容
  {{ main_content }}
  
  ### 总结
  {{ conclusion }}
  
  ### 相关链接
  {{ related_links }}
```

---

## 第十三章：多 Agent 协作 ⭐⭐⭐

### 13.1 多 Agent 架构

```
多 Agent 协作示例：

用户请求：分析这个 Python 项目并写测试

┌─────────────────┐
│  Orchestrator   │  ← 主 Agent，协调任务
│  Agent          │
└────────┬────────┘
         ↓
┌────────▼────────┐
│  Code Analyst   │  ← 分析代码结构
│  Agent           │
└────────┬────────┘
         ↓
┌────────▼────────┐
│  Test Writer    │  ← 编写测试用例
│  Agent          │
└─────────────────┘
```

### 13.2 协作配置

```yaml
# multi-agent.yaml

agents:
  - name: orchestrator
    role: 任务协调
    model: claude-sonnet-4
    
  - name: coder
    role: 代码编写
    model: claude-sonnet-4
    expertise:
      - python
      - javascript
      
  - name: reviewer
    role: 代码审查
    model: claude-haiku
    expertise:
      - security
      - performance
```

---

## 第十四章：深度思考——三方对比 ⭐⭐⭐

### 14.1 核心对比

| 维度 | Claude Code | OpenClaw | Hermes Agent |
|------|-------------|----------|-------------|
| **学习方式** | 会话级 | Skills 可选 | 内置自动演化 |
| **记忆持久化** | ❌ | ✅ Skills | ✅ 三层记忆 |
| **多平台** | CLI | 全平台 | 全平台 |
| **上手难度** | 低 | 中 | 中 |
| **定制化** | 有限 | 高 | 高 |
| **社区生态** | 官方 | 丰富 | 新兴 |

### 14.2 各自优势场景

```
Claude Code 适合：
- 快速原型开发
- 单人小项目
- 不想配置的用户

OpenClaw 适合：
- 需要多平台协作
- 企业环境
- 深度定制

Hermes Agent 适合：
- 长期项目（记忆累积）
- 自动化工作流
- 想让 Agent 不断进化
```

### 14.3 未来展望

```
三大 Agent 的演进方向：

Claude Code：
- 更强的代码理解能力
- 更好的上下文窗口

OpenClaw：
- 更多平台集成
- 更丰富的 Skills 市场

Hermes Agent：
- 更智能的 Skill 演化
- 多 Agent 协作
- 开源生态建设
```

---

## 第十五章：自进化 Agent 的边界 ⭐⭐⭐

### 15.1 当前限制

```
Hermes Agent 的局限性：

1. 记忆可能过时
   - 需要定期清理 L1 记忆
   - Skills 可能需要手动审核

2. 演化阈值难调
   - 太低 → Skill 泛滥
   - 太高 → 错过好模式

3. 隐私考虑
   - 记忆包含敏感信息
   - 需要加密存储
```

### 15.2 使用建议

```
最佳实践：

1. 定期审查 Skills
   - 每月检查一次
   - 删除不再适用的 Skill

2. 分层管理敏感信息
   - L2 只存通用知识
   - 敏感信息放 L0，用完即焚

3. 设置演化边界
   - 避免 Agent 生成危险操作
   - 定义 Skill 的使用范围
```

---

## 常见问题与资源 ⭐⭐

### Q1：Hermes 和 OpenClaw 哪个更好？

**A**：取决于你的需求。
- 想快速上手 → Claude Code
- 需要多平台 + 深度定制 → OpenClaw
- 想要 Agent 不断进化 → Hermes

### Q2：记忆会无限增长吗？

**A**：不会。
- L0 每会话重置
- L1 有时间衰减（默认 2 周）
- L2 手动管理

### Q3：如何导出/备份记忆？

```bash
# 导出所有记忆
hermes memory export --format yaml --output backup.yaml

# 导入记忆
hermes memory import --file backup.yaml
```

### Q4：支持本地模型吗？

**A**：支持！
```yaml
model:
  provider: local
  endpoint: http://localhost:11434  # Ollama
  model: llama3
```

### Q5：如何参与贡献？

**A**：访问官方资源：
- GitHub：github.com/NousResearch/hermes-agent
- 文档：hermes-agent.nousresearch.com/docs/
- 橙皮书系列：huasheng.ai/orange-books

---

## 📚 参考资源

| 资源 | 链接 |
|------|------|
| **官方文档** | hermes-agent.nousresearch.com/docs/ |
| **GitHub** | github.com/NousResearch/hermes-agent |
| **橙皮书 PDF（英）** | [PDF 下载](https://github.com/alchaincyf/hermes-agent-orange-book/raw/main/Hermes-Agent-The-Complete-Guide-v260407.pdf) |
| **橙皮书 PDF（中）** | [PDF 下载](https://github.com/alchaincyf/hermes-agent-orange-book/raw/main/Hermes-Agent-%E4%BB%8E%E5%85%A5%E9%97%A8%E5%88%B0%E7%B2%BE%E9%80%9A-v260407.pdf) |
| **橙皮书系列** | huasheng.ai/orange-books |

---

## ✅ 学习成果检验

完成本指南后，请自我评估：

- [ ] 能够解释 Hermes Agent 的三大创新
- [ ] 能够部署到至少一个平台
- [ ] 能够配置三层记忆系统
- [ ] 能够创建自定义 Skill
- [ ] 能够对比三大 Agent 的优劣

如果以上都能做到，恭喜你成为 **Hermes Agent 进阶用户**！🎉

---

*🦞 本文由钳岳星君基于花叔橙皮书 v260408 撰写 | CC BY-NC-SA 4.0 | 更新日期：2026-04-11*
