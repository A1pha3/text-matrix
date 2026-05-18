---
title: "agent-skills：面向专业AI coding Agent的安全技能注册表"
date: "2026-05-18T19:56:00+08:00"
slug: "agent-skills-secure-validated-skill-registry"
description: "Tech Leads Club 开源的安全技能注册表，为 AI coding 智能体提供经过安全扫描、验证测试的标准化技能包，支持 Claude Code、Cursor、Windsurf 等主流平台。"
categories: ["技术笔记"]
tags: ["AI智能体", "技能注册表", "TypeScript", "Claude Code", "Cursor", "安全扫描", "MCP"]
---

## 概述

[agent-skills](https://github.com/tech-leads-club/agent-skills) 是由 Tech Leads Club 维护的一个安全技能注册表，专为专业 AI coding 智能体提供经过验证的技能包。项目使用 Nx Cloud 做多包管理，TypeScript 100%，MIT/CC-BY-4.0 双许可证，当前 npm 包版本持续更新。

当前 AI 技能市场存在严峻的安全问题——根据 Snyk Agent Scan 的报告，**超过 13% 的市集技能包含关键级漏洞**。agent-skills 正是针对这一痛点，提供了一套 hardening 方案：100% 开源（无二进制）、CI/CD 静态分析、不可变完整性（lockfile + content hash）、人类策展的 prompts，以及 CLI 层面的防御纵深（sanitization、路径隔离、symlink guards、原子 lockfile、审计日志）。

## 核心架构

### 技能包结构

每个技能遵循统一目录结构：

```
packages/skills-catalog/skills/
  (category-name)/
    skill/
      SKILL.md          ← 主指令文件
      templates/        ← 文件模板
      references/       ← 按需文档
```

### 安全模型

CLI 安全实现包含以下层次：

- **输入清理（Sanitization）** — 过滤恶意输入
- **路径隔离（Path Isolation）** — 防止路径遍历攻击
- **Symlink Guards** — 阻止符号链接劫持
- **原子 Lockfile** — 安装过程原子化，失败回滚
- **审计日志（Audit Trail）** — 每次操作可溯源

每个技能在发布前都经过 [Snyk Agent Scan](https://github.com/snyk/agent-scan)（原 mcp-scan）扫描。

## 支持的智能体平台

项目将支持的智能体分为三个层级：

| 层级 | 平台 |
|------|------|
| Tier 1（主流） | Claude Code, Cline, Cursor, GitHub Copilot, Windsurf |
| Tier 2（上升期） | Aider, Antigravity, Gemini CLI, Kilo Code, Kiro, OpenAI Codex, Roo Code, TRAE |
| Tier 3（企业级） | Amazon Q, Augment, Droid (Factory.ai), OpenCode, Sourcegraph Cody, Tabnine |

## 精选技能

| 技能 | 类别 | 说明 |
|------|------|------|
| tlc-spec-driven | 开发 | 四阶段项目规划：Specify → Design → Tasks → Implement，跨会话持久化记忆 |
| aws-advisor | 云 | AWS 架构设计、安全评审与实现指导，集成 AWS MCP 工具 |
| playwright-skill | 自动化 | 完整浏览器自动化，页面测试、表单填写、截图、UX 验证 |
| figma | 设计 | 从 Figma 获取设计上下文并将节点转译为生产代码 |
| security-best-practices | 安全 | 语言/框架专项安全评审，检测漏洞并生成修复建议 |

## 快速上手

```bash
# 交互式安装向导
npx @tech-leads-club/agent-skills

# 列出所有技能
agent-skills list

# 安装单个技能
agent-skills install -s tlc-spec-driven

# 安装到指定智能体
agent-skills install -s aws-advisor -a cursor windsurf

# 全局安装（到 ~/.gemini, ~/.claude 等）
agent-skills install -s my-skill -g

# 更新已安装的技能
agent-skills update

# 查看审计日志
agent-skills audit
```

本地缓存目录：`~/.cache/agent-skills/`。

## MCP 服务器

项目还提供了一个 MCP 服务器 `@tech-leads-club/agent-skills-mcp`，支持 AI 智能体通过渐进式披露（progressive disclosure）直接查询技能目录——先搜索，确需时再拉取完整内容。

```json
{
  "mcpServers": {
    "agent-skills": {
      "command": "npx",
      "args": ["-y", "@tech-leads-club/agent-skills-mcp"]
    }
  }
}
```

提供四个工具：`list_skills`（按类目浏览）、`search_skills`（模糊搜索）、`read_skill`（读取技能主指令）、`fetch_skill_files`（拉取指定参考文件）。

## 小结

agent-skills 的核心价值在于**安全可信**——不是追求最多技能，而是确保每个技能都经过扫描验证。对于企业在 AI coding 智能体落地时关注供应链安全的团队，这是一个值得关注的基础设施层组件。当前 GitHub 星标约 3,800，今日新增约 225，保持稳健增长。