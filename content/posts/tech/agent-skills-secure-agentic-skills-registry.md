---
title: Agent Skills - 安全验证的AI编码智能体技能注册表
date: 2026-05-18
slug: agent-skills-secure-agentic-skills-registry
categories: ["技术笔记"]
description: "据 Snyk 统计，市场上 13% 以上的智能体技能包含高危漏洞。Agent Skills 通过静态分析、锁定文件完整性和人工审核三重关卡，确保每个技能的代码安全性。"
tags:
  - AI Agent
  - 安全
  - Claude Code
  - Cursor
  - 开源生态
---

# Agent Skills：安全验证的 AI 编码智能体技能注册表

GitHub: [tech-leads-club/agent-skills](https://github.com/tech-leads-club/agent-skills)

## 一句话评价

一个有安全底线的 AI 编码 Agent 技能库——据 Snyk 统计，市场上 13% 以上的智能体技能包含高危漏洞；Agent Skills 通过静态分析、锁定文件完整性和人工审核三重关卡，确保每个技能的代码安全性，支持 Antigravity、Claude Code、Cursor 等主流 Agent。

## 为什么需要安全的技能注册表

AI 编码 Agent 依赖"技能"（Skills）来扩展能力——它们相当于 AI 的插件，可以赋予 Agent 特定的工作流和领域知识。然而：

- Snyk Agent Scan 报告：**市场 13.4% 的技能包含关键漏洞**
- 大多数技能市场缺乏安全审核流程
- 恶意或漏洞技能一旦安装，可直接访问文件系统、网络、甚至凭据

## Agent Skills 的安全机制

**五层防御**：
1. **100% 开源**：无二进制，可审计
2. **CI/CD 静态分析**：每次发布前自动扫描
3. **不可变完整性**：通过 lockfile + 内容哈希验证
4. **人工审核**：Prompt 内容由人工审查
5. **Snyk Agent Scan 扫描**：发布前强制检测

**CLI 纵深防御**：
- 输入清理（sanitization）
- 路径隔离
- 符号链接防护
- 原子锁文件
- 审计日志

完整威胁模型见 [SECURITY.md](https://github.com/tech-leads-club/agent-skills/blob/main/SECURITY.md)。

## 支持的 AI Agent

- Antigravity
- Claude Code
- Cursor
- 更多陆续支持中

## 技能结构

```
packages/skills-catalog/skills/
  (category-name)/
    skill/
      SKILL.md          ← 主要指令
      templates/        ← 文件模板
      references/       ← 按需文档
```

## 快速开始

```bash
# 查看官方文档
https://tech-leads-club.github.io/agent-skills/

# 安装某个技能（以对应 Agent 的方式安装）
# 参考各 Agent 的技能安装文档
```

## 适用人群

- 企业安全团队（需要管控 AI Agent 使用的工具）
- 开发团队（确保 AI 编码助手使用的技能无漏洞）
- Agent 框架开发者（参考安全技能的设计规范）