+++
date = '2026-05-23T13:09:23+08:00'
draft = false
title = 'honcho：为有状态 Agent 打造的记忆库'
slug = 'honcho-memory-library-stateful-agents'
description = 'honcho 是 Plastic Labs 开源的有状态 Agent 记忆库，通过对话历史持久化存储让 AI Agent 在跨会话场景中保持上下文连续性。'
categories = ['技术笔记']
tags = ['AI', 'Agent', '记忆框架', '开源']
+++
# honcho: 为有状态 Agent 打造的记忆库，让 Agent 记住一切

**🏷️ 分类：** AI Agent · 记忆框架  
**⭐ Stars：** 4,032  
**🔗 地址：** https://github.com/plastic-labs/honcho  
**🌐 官网：** https://plasticlabs.ai

**一句话总结：** 一个专为有状态 Agent 设计的记忆库，让 AI Agent 能跨会话记住用户偏好、对话历史、关键事实，打造真正个性化的 AI 体验。

---

## 🎯 这个工具解决什么问题？

AI Agent 每次对话都是从零开始——不记得上次说了什么、不知道用户的习惯偏好、无法持续跟踪复杂任务的进度。honcho 通过**结构化记忆系统**，让 Agent"活"在对话之间，每次交互都能利用历史积累，真正做到"越来越懂你"。

---

## ⚡ 核心特性

### 1. 多层次记忆架构
- **短期记忆**：当前会话上下文
- **中期记忆**：最近几次会话的关键信息
- **长期记忆**：用户偏好、背景信息、跨会话事实

### 2. 向量检索
基于 embeddings 的语义搜索，快速找到相关记忆

### 3. 记忆融合
自动整合多条相关记忆，生成连贯的上下文

### 4. 隐私优先
本地优先，数据完全归用户所有

### 5. 多语言支持
Python/JavaScript/TypeScript 多语言 SDK

---

## 📦 安装

```bash
pip install honcho
# 或
npm install @plastic-labs/honcho
```

---

## 🚀 快速上手

### Python
```python
from honcho import Memory

mem = Memory(user_id="user123")

# 记住用户偏好
mem.remember("user_likes_pizza", "用户喜欢意大利辣香肠披萨")

# 检索相关记忆
context = mem.retrieve("用户今天点了什么？")
print(context)
```

### Node.js
```javascript
import { Memory } from '@plastic-labs/honcho';

const mem = new Memory({ userId: 'user123' });
await mem.remember('preference', { theme: 'dark', language: 'zh' });
const context = await mem.retrieve('用户的界面偏好是什么？');
```

---

## 💡 适用场景

| 场景 | 说明 |
|------|------|
| 个人 AI 助手 | 记住用户习惯，提供个性化服务 |
| 客服机器人 | 跨会话跟踪用户问题和解决方案 |
| 研究助手 | 长期跟踪课题进展和文献笔记 |
| 教育 AI | 记住学生学习进度，提供针对性辅导 |

---

## 🆚 对比同类

| 工具 | 记忆深度 | 隐私性 | Stars | 特点 |
|------|---------|--------|-------|------|
| **honcho** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 4K | 专为 Agent 设计 |
| MemGPT | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 15K | 记忆层级管理 |
| langchain-memories | ⭐⭐⭐ | ⭐⭐⭐ | - | LangChain 生态 |
| Superpowers | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 203K | Agent 技能框架 |

---

## ⚠️ 注意事项

- 记忆库会随时间增长，需要定期清理低价值记忆
- 建议设置记忆过期策略，避免信息过时
- 本地部署需要配置向量数据库（可选）

---

**相关工具：** [Hermes Agent](hermes-agent-growing-ai-agent-framework) · [Superpowers](superpowers-agentic-development-methodology) · [Academic Research Skills](academic-research-skills-claude-code-scientific-writing)