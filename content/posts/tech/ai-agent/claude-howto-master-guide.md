---
title: "Claude How To：Claude Code 精通学习指南"
date: "2026-04-01T13:00:00+08:00"
slug: "claude-howto-master-guide"
aliases:
  - /posts/tech/claude-howto-master-guide/
  - /posts/tech/ai-agent/claude-howto-master-claude-code-guide/
  - /posts/tech/ai-agent/claude-howto-visual-guide/
categories: ["技术笔记"]
tags: ["Claude Code", "Claude How To", "AI编程", "Skills", "Hooks", "MCP", "Subagents"]
description: "Claude How To 是 GitHub 上最受欢迎的 Claude Code 学习指南，13.7k Stars。涵盖10大学习模块（Slash Commands、Memory、Skills、Hooks、MCP、Subagents等），提供11-13小时从入门到精通的完整学习路径和可复制的生产级模板。"
---

# Claude How To：Claude Code 精通学习指南

> 预计阅读时间：40 分钟 | 难度：⭐⭐⭐⭐

---

## 学习目标

阅读本文后，您将能够：

- ✅ 理解 Claude How To 的核心理念与定位
- ✅ 掌握 10 大 Claude Code 功能模块的完整学习路径
- ✅ 熟练使用 Slash Commands、Memory、Skills、Hooks、MCP 等核心功能
- ✅ 构建生产级自动化工作流（代码审查、CI/CD、文档生成）
- ✅ 从初学者进阶为 Claude Code 高级用户（11-13 小时学习路径）

---

## 一、项目概述

### 1.1 什么是 Claude How To

**Claude How To** 是由 **luongnv89** 创建的**结构化、可视化、以实例为驱动的 Claude Code 学习指南**。与官方文档不同，它不仅描述功能特性，还展示如何将多个功能组合成真正节省时间的自动化工作流。

> 官网：https://github.com/luongnv89/claude-howto

**核心理念：** 从输入 `claude` 到掌握 Agent、Hooks、Skills 和 MCP 服务器——配以可视化教程、Mermaid 图表、直接可复制的模板，以及循序渐进的学习路径。

### 1.2 关键数据

| 指标 | 数值 |
|------|------|
| **GitHub Stars** | 13,700+ |
| **GitHub Forks** | 1,500+ |
| **Commits** | 127+ |
| **最新版本** | v2.2.0 (2026 年 3 月) |
| **最新提交** | 2026 年 3 月 31 日 |
| **协议** | MIT |

### 1.3 Claude How To vs 官方文档对比

| 维度 | 官方文档 | Claude How To |
|------|----------|---------------|
| **格式** | 参考文档 | 可视化教程 + Mermaid 图表 |
| **深度** | 功能描述 | 底层原理讲解 |
| **示例** | 基础片段 | 生产级模板直接可用 |
| **结构** | 按功能组织 | 渐进式学习路径 |
| **入门** | 自主探索 | 带时间估计的引导路线图 |
| **自测** | 无 | 交互式测验找准缺口 |

### 1.4 学习路径概览

| 阶段 | 时长 | 内容 |
|------|------|------|
| **初学者（Beginner）** | ~2.5 小时 | Slash Commands、基础 Memory |
| **中级（Intermediate）** | ~3.5 小时 | Skills、Hooks、CLI、MCP 进阶 |
| **高级（Advanced）** | ~5 小时 | Subagents、高级功能、Plugins |

**总学习时间：** 11-13 小时从入门到精通

---

## 二、十大学习模块详解

### 2.1 模块总览

| 序号 | 模块 | 难度 | 时长 | 核心技能 |
|------|------|------|------|----------|
| 01 | Slash Commands | 初学者 | 30 分钟 | 快捷命令 |
| 02 | Memory | 初学者+ | 45 分钟 | 持久化上下文 |
| 03 | Checkpoints | 中级 | 45 分钟 | 上下文快照 |
| 04 | CLI Basics | 初学者+ | 30 分钟 | 命令行接口 |
| 05 | Skills | 中级 | 1 小时 | 技能扩展 |
| 06 | Hooks | 中级 | 1 小时 | 生命周期钩子 |
| 07 | MCP | 中级+ | 1 小时 | Model Context Protocol |
| 08 | Subagents | 中级+ | 1.5 小时 | 多智能体协作 |
| 09 | Advanced Features | 高级 | 2-3 小时 | 高级配置 |
| 10 | Plugins | 高级 | 2 小时 | 插件开发 |

### 2.2 模块 1：Slash Commands（斜杠命令）

**难度：** 初学者 | **时长：** 30 分钟

Slash Commands 允许你通过 `/` 前缀快速触发预定义命令。

**常用 Slash Commands：**
```bash
# 代码优化
/optimize

# 代码审查
/review

# 解释代码
/explain

# 生成测试
/test

# 修复错误
/fix
```textmarkdown
<!-- .claude/commands/custom.md -->
# Custom Slash Command

This command does something useful.

@slack.notify "Task completed: {{task}}"
```textmarkdown
# Project Context

## 技术栈
- Frontend: React 18 + TypeScript
- Backend: Node.js + Express
- Database: PostgreSQL + Redis

## 代码规范
- 使用 ESLint + Prettier
- 提交信息遵循 Conventional Commits
- 所有 API 返回统一格式 { success, data, error }
```text
┌─────────────┐      读取       ┌─────────────┐
│  CLAUDE.md  │◄────────────►│  Claude     │
│  (项目上下文)  │              │  Code       │
└─────────────┘              └──────┬──────┘
                                 │
                    写入 ◄───────┘
                    │
              ┌─────▼─────┐
              │  Memory   │
              │  (向量存储) │
              └───────────┘
```textbash
# 保存检查点
/checkpoint save "完成模块A开发"

# 列出检查点
/checkpoint list

# 恢复到检查点
/checkpoint restore "完成模块A开发"
```textbash
# 启动会话
claude

# 直接执行命令
claude -p "Explain this code"

# 指定项目
claude --project ./my-project

# 查看帮助
claude --help
```text
.claude/skills/
├── code-review/
│   ├── SKILL.md          # 技能定义
│   ├── system-prompt.md   # 系统提示词
│   └── tools/             # 关联工具
└── security-audit/
    └── ...
```textyaml
name: code-review
description: Perform comprehensive code review
triggers:
  - "/review"
  - "/code-review"
tools:
  - read
  - grep
  - bash
instructions: |
  Review code for:
  1. Logic errors
  2. Security vulnerabilities
  3. Performance issues
  4. Style consistency
```texttypescript
// hooks/pre-tool-use.ts
import { HookRegistry } from '@claude-code/hooks';

export const preToolUse: HookRegistry['preToolUse'] = async (tool, input) => {
  // 检查危险操作
  if (tool.name === 'Bash' && input.command.includes('rm -rf')) {
    throw new Error('Dangerous delete operation blocked');
  }
  
  // 记录操作日志
  await logToolUse(tool.name, input);
  
  return { allowed: true };
};
```textyaml
# .claude/mcp.yaml
mcp_servers:
  github:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_TOKEN: "${GITHUB_TOKEN}"
  
  slack:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-slack"]
    env:
      SLACK_BOT_TOKEN: "${SLACK_BOT_TOKEN}"
```text
        主 Agent
           │
           ├──► 子 Agent 1（代码审查）
           │
           ├──► 子 Agent 2（安全扫描）
           │
           └──► 子 Agent 3（文档生成）
```texttypescript
// 创建子 Agent 处理代码审查
const reviewer = await claude.spawnAgent({
  name: 'code-reviewer',
  instructions: 'You are an expert code reviewer.',
  skills: ['code-review'],
  hooks: [securityScanner],
});

// 主 Agent 协调
const task = await reviewer.review(pullRequest);
await task.waitForCompletion();
const results = await task.getResults();
```textyaml
# .claude/config.yaml
performance:
  context_window: 200000
  max_tokens: 4096
  temperature: 0.7
  
cache:
  enabled: true
  ttl: 3600
  max_size: 1000
```textyaml
security:
  read_only_mode: false
  allowed_paths:
    - /workspace/src
    - /workspace/tests
  denied_patterns:
    - "*.env"
    - "*.pem"
  tool_restrictions:
    Bash:
      max_duration: 300
      require_confirmation: true
```text
my-plugin/
├── plugin.json          # 插件元数据
├── skills/              # 技能
├── hooks/               # 钩子
├── commands/            # 命令
└── resources/           # 资源文件
```textjson
{
  "name": "my-code-review-plugin",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "Comprehensive code review plugin",
  "skills": ["./skills/code-review"],
  "hooks": ["./hooks/security-scanner"],
  "commands": ["./commands/review"]
}
```textyaml
# .claude/commands/code-review.md
# /code-review - 自动代码审查工作流

## 工作流
1. 读取 CLAUDE.md 了解项目规范
2. 使用 code-review skill 进行基础审查
3. 启动 security-subagent 进行安全扫描
4. 汇总结果并输出报告
```textmarkdown
# CLAUDE.md - 团队入职助手

## 团队信息
- 团队成员：Alice (PM), Bob (Dev), Carol (DevOps)
- 工作时间：9:00-18:00 PST
- 紧急联系：Slack #emergency

## 入职流程
1. 环境配置 → 参考 docs/setup.md
2. 代码规范 → 参考 .eslintrc.js
3. 提交流程 → 使用 /git-workflow 命令
```textbash
# Git hook 配置
# .git/hooks/pre-commit
claude --command "lint-and-test"

# 自动部署
claude --background --watch "src/**/*.ts" "npm run build && deploy.sh"
```texttypescript
// 安全审计子 Agent
const securityAuditor = await claude.spawnAgent({
  name: 'security-auditor',
  instructions: 'Perform security audit only. No modifications allowed.',
  skills: ['security-scan'],
  hooks: [{
    type: 'PreToolUse',
    action: (tool) => {
      if (tool.category === 'write') {
        throw new Error('Write operations forbidden in audit mode');
      }
    }
  }]
});
```textbash
# 保存检查点
/checkpoint save "重构前状态"

# 启用规划模式
/planning on

# 执行重构...

# 验证后保存新检查点
/checkpoint save "重构完成"
```textbash
# 1. 克隆指南仓库
git clone https://github.com/luongnv89/claude-howto.git
cd claude-howto

# 2. 复制第一个 Slash Command
mkdir -p /path/to/your-project/.claude/commands
cp 01-slash-commands/optimize.md /path/to/your-project/.claude/commands/

# 3. 在 Claude Code 中试用
# /optimize

# 4. 设置项目 Memory
cp 02-memory/project-CLAUDE.md /path/to/your-project/CLAUDE.md

# 5. 安装一个 Skill
cp -r 03-skills/code-review ~/.claude/skills/
```textbash
# Slash Commands (15 分钟)
cp 01-slash-commands/*.md ~/.claude/commands/

# 项目 Memory (15 分钟)
cp 02-memory/project-CLAUDE.md ./CLAUDE.md

# 安装 Skill (15 分钟)
cp -r 03-skills/code-review ~/.claude/skills/

# 配置 Hooks (15 分钟)
cp -r 06-hooks/* ~/.claude/hooks/
```text
project/
├── .claude/
│   ├── commands/           # Slash Commands
│   │   ├── optimize.md
│   │   ├── review.md
│   │   └── explain.md
│   ├── skills/            # Skills
│   │   └── code-review/
│   │       └── SKILL.md
│   ├── hooks/             # Hooks
│   │   └── pre-tool-use.ts
│   ├── memory/            # Memory 数据
│   └── cache/             # 缓存
├── CLAUDE.md              # 项目上下文（重要！）
├── CLAUDE.local.md        # 本地特定配置
└── .claudeignore          # 忽略文件
```textyaml
<!-- .claude/skills/my-skill/SKILL.md -->
name: my-custom-skill
description: Custom skill for project-specific tasks
version: 1.0.0

trigger:
  commands:
    - /my-skill
    - /custom

capabilities:
  tools:
    - read
    - write
    - bash
    - web_search
  
  file_patterns:
    - "*.py"
    - "*.js"
    - "*.ts"

system_prompt: |
  You are a specialized assistant for [project name].
  Focus on [specific domain or task type].
  Always follow [project-specific guidelines].

instructions: |
  1. First, read the CLAUDE.md for project context
  2. Check relevant documentation in docs/
  3. Follow the coding standards in STYLE_GUIDE.md
  4. Output results in the standard format
```texttypescript
// .claude/hooks/notification-hook.ts
import { Hook, HookContext, HookResult } from '@claude-code/hooks';

export const postMessage: Hook = async (
  message: string,
  context: HookContext
): Promise<HookResult> => {
  // 发送通知
  await slack.notify({
    channel: '#claude-updates',
    message: `New message: ${message.substring(0, 100)}...`,
  });

  return { success: true };
};
```texttypescript
// 自定义 MCP 服务器
import { MCPServer, Tool } from '@modelcontextprotocol/server';

const server = new MCPServer({
  name: 'my-custom-server',
  version: '1.0.0',
});

server.addTool({
  name: 'query_database',
  description: 'Execute SQL query',
  inputSchema: {
    type: 'object',
    properties: {
      query: { type: 'string' },
    },
    required: ['query'],
  },
  handler: async ({ query }) => {
    const result = await db.query(query);
    return { rows: result };
  },
});

server.listen();
```textmarkdown
<!-- 推荐的 CLAUDE.md 结构 -->

# [项目名称]

## 一句话描述
[项目是什么、解决什么问题]

## 技术栈
- Frontend: [技术]
- Backend: [技术]
- Database: [技术]
- Infrastructure: [技术]

## 代码规范
- 风格指南: [链接]
- 提交规范: [Conventional Commits]
- PR 流程: [链接]

## 架构决策
- [ ADR 链接]

## 常用命令
- 开发: `npm run dev`
- 测试: `npm test`
- 构建: `npm run build`

## 联系人
- 技术负责人: [邮箱]
- 文档维护: [邮箱]
```texttypescript
// 生产环境 Hooks 安全配置
const secureHooks = {
  preToolUse: async (tool, input) => {
    // 白名单检查
    if (!isToolAllowed(tool.name)) {
      throw new Error(`Tool ${tool.name} is not allowed`);
    }
    
    // 危险命令确认
    if (isDangerousCommand(tool, input)) {
      const confirmed = await prompt.confirm(
        `Execute dangerous command: ${tool.name}?`
      );
      if (!confirmed) {
        throw new Error('Operation cancelled');
      }
    }
    
    return { allowed: true };
  },
  
  preMessage: async (message) => {
    // 内容过滤
    const filtered = contentFilter(message);
    return { filtered, wasModified: filtered !== message };
  },
};
```textyaml
# .claude/config.yaml - 性能优化配置

# 上下文管理
context:
  max_tokens: 180000
  checkpoint_threshold: 150000
  auto_checkpoint: true

# 缓存策略
cache:
  enabled: true
  provider: redis
  ttl: 7200
  max_entries: 500

# 并发控制
concurrency:
  max_parallel_tools: 5
  max_parallel_subagents: 3
  queue_timeout: 300
```textbash
# 1. 立即开始（15分钟）
git clone https://github.com/luongnv89/claude-howto.git
cd claude-howto

# 2. 选择你的起点
# - 初学者：01-slash-commands
# - 中级：05-skills 或 06-hooks
# - 高级：09-advanced-features

# 3. 在 Claude Code 中运行自测
/self-assessment

# 4. 开始学习！
```

---

## 相关链接

- 🌐 官网：https://github.com/luongnv89/claude-howto
- 📖 学习路径：https://github.com/luongnv89/claude-howto/blob/main/LEARNING-ROADMAP.md
- 📚 功能目录：https://github.com/luongnv89/claude-howto/blob/main/CATALOG.md
- 🧪 快速参考：https://github.com/luongnv89/claude-howto/blob/main/QUICK_REFERENCE.md

---

*🦞 每日 08:00 自动更新*
