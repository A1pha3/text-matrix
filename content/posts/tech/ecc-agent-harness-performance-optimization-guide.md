---
title: "ECC: 199k Stars 的Agent性能优化系统，跨Codex/Claude Code/Cursor的多 harness 工作流"
date: "2026-05-30T13:13:57+08:00"
slug: "ecc-agent-harness-performance-optimization-system"
description: "ECC（EveryCoding's Companion）是跨智能体编程工作流系统，182K+ Stars、28K+ Forks、170+ 贡献者，支持 Codex、Claude Code、Cursor、OpenCode、Gemini 等多种 AI 编程 harness。提供技能、本能、记忆优化、安全扫描和研究优先开发策略。"
draft: false
categories: ["技术笔记"]
tags: ["AI智能体", "Codex", "Claude Code", "Cursor", "自动化", "工程效能", "编程工具"]
---

## 核心判断

ECC 不是一个配置合集，而**一套经过 10 个月以上高强度日常使用打磨的生产级智能体操作系统**：技能、本能、记忆优化、持续学习、安全扫描和研究优先开发策略全链路覆盖，跨 Codex、Claude Code、Cursor、OpenCode、Gemini、Zed、GitHub Copilot 等主流编程智能体。

其核心价值在于：让 agent 的每次工作都能降低下次工作的难度，而不是累积更多上下文负担。

## 规模数据

- ⭐ 182K+ Stars · Fork 28K+ · 贡献者 170+
- 12+ 语言生态 · 跨 7 种 harness
- 63 个 agents · 249 个 skills · 79 个 legacy command shims

## v2.0.0-rc.1 新增内容

ECC 2.0 alpha 已进入源码树（ecc2/），基于 Rust 构建的 control-plane 原型，支持 dashboard、start、sessions、status、stop、resume、daemon 等命令，可本地构建使用（非正式发布）。

新增 Operator 体系：brand-voice、social-graph-ranker、connections-optimizer、customer-billing-ops、ecc-tools-cost-audit、google-workspace-ops、project-flow-ops、workspace-surface-audit 等 Operator 扩展了出站工作流能力。

ECC Pro 推出托管 GitHub App（私有仓库 $19/seat/月），OSS 版本永久 MIT 协议免费。

## 系统分层

### 核心模块

| 模块 | 说明 |
|------|------|
| `agents/` | 跨 harness 的核心 agent 定义 |
| `skills/` | 可复用的技能库 |
| `rules/` | 工程规则集 |
| `contexts/` | 上下文模板 |
| `hooks/` | 生命周期钩子（记忆持久化等） |
| `src/llm/` | LLM 接口层 |
| `mcp-configs/` | MCP 服务器配置 |

### 核心工作流

- **Token 优化**：模型选择、系统提示精简、后台进程管理
- **记忆持久化**：跨 session 自动保存/加载 context 的 hooks
- **持续学习**：从 session 中自动提取模式固化为可复用 skills
- **验证循环**：Checkpoint vs 连续评估、grader 类型、pass@k 指标
- **并行化**：Git worktree、cascade 方法、横向扩展时机

## 安全能力

`the-security-guide.md` 覆盖攻击向量、沙箱隔离、净化处理、CVEs 和 AgentShield。Security 是 ECC 单独维护的重要方向，不是事后补丁。

## 安装方式

```bash
# Clone
git clone https://github.com/affaan-m/ECC.git
cd ECC

# 脚本安装（支持多平台）
./install.sh          # Linux/macOS
powershell -File install.ps1  # Windows
```

## 采用建议

- 新用户从 **the-shortform-guide.md** 开始，理解核心哲学后再深入长篇指南
- `ECC Pro` 的私有仓库 PR 审计功能值得团队使用，OSS 版本已足够个人开发者
- ecc2/ 的 Rust control-plane 是 alpha 状态，可作为预览体验，但不要用于生产

---

项目地址：[affaan-m/ECC](https://github.com/affaan-m/ECC)，文档丰富，建议通读guides目录后再动手实践。