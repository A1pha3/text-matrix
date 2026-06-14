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

> 预计阅读时间：40分钟 | 难度：⭐⭐⭐⭐

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
| **最新版本** | v2.2.0 (2026年3月) |
| **最新提交** | 2026年3月31日 |
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
```

**创建自定义 Slash Command：**
```markdown
<!-- .claude/commands/custom.md -->
# Custom Slash Command

This command does something useful.

@slack.notify "Task completed: {{task}}"
```

### 2.3 模块 2：Memory（记忆系统）

**难度：** 初学者+ | **时长：** 45 分钟

Claude Code 的 Memory 系统让 AI 能够跨会话记住项目上下文。

**CLAUDE.md 示例：**
```markdown
# Project Context

## 技术栈
- Frontend: React 18 + TypeScript
- Backend: Node.js + Express
- Database: PostgreSQL + Redis

## 代码规范
- 使用 ESLint + Prettier
- 提交信息遵循 Conventional Commits
- 所有 API 返回统一格式 { success, data, error }
```

**工作原理：**
```
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
```

### 2.4 模块 3：Checkpoints（检查点）

**难度：** 中级 | **时长：** 45 分钟

Checkpoints 允许你保存和恢复上下文区域，避免超出上下文限制。

**核心概念：**
- **Hard Zone**：已归档的旧上下文，可恢复
- **Active Zone**：当前活跃上下文
- **Overflow Zone**：超出活跃限制的待归档内容

**使用场景：**
```bash
# 保存检查点
/checkpoint save "完成模块A开发"

# 列出检查点
/checkpoint list

# 恢复到检查点
/checkpoint restore "完成模块A开发"
```

### 2.5 模块 4：CLI Basics（命令行基础）

**难度：** 初学者+ | **时长：** 30 分钟

Claude Code 提供完整的命令行接口。

**常用命令：**
```bash
# 启动会话
claude

# 直接执行命令
claude -p "Explain this code"

# 指定项目
claude --project ./my-project

# 查看帮助
claude --help
```

### 2.6 模块 5：Skills（技能系统）

**难度：** 中级 | **时长：** 1 小时

Skills 是可复用的 AI 行为模块，定义在 `.claude/skills/` 目录。

**目录结构：**
```
.claude/skills/
├── code-review/
│   ├── SKILL.md          # 技能定义
│   ├── system-prompt.md   # 系统提示词
│   └── tools/             # 关联工具
└── security-audit/
    └── ...
```

**SKILL.md 示例：**
```yaml
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
```

### 2.7 模块 6：Hooks（钩子系统）

**难度：** 中级 | **时长：** 1 小时

Hooks 允许你在 Claude Code 生命周期的关键点插入自定义逻辑。

**钩子类型：**
| 钩子 | 触发时机 | 用途 |
|------|-----------|------|
| `PreToolUse` | 工具执行前 | 权限检查、日志记录 |
| `PostToolUse` | 工具执行后 | 结果验证、通知 |
| `PreMessage` | 消息发送前 | 内容过滤、格式化 |
| `PostMessage` | 消息发送后 | 归档、备份 |

**使用示例：**
```typescript
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
```

### 2.8 模块 7：MCP（Model Context Protocol）

**难度：** 中级+ | **时长：** 1 小时

MCP 是一种标准化协议，允许 Claude 与外部工具和数据源交互。

**支持的 MCP 服务器：**
| 服务器 | 功能 |
|--------|------|
| GitHub | Issue/PR/代码管理 |
| Slack | 团队通知 |
| Database | 数据库查询 |
| Filesystem | 增强文件操作 |
| Web Search | 联网搜索 |

**MCP 配置示例：**
```yaml
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
```

### 2.9 模块 8：Subagents（子智能体）

**难度：** 中级+ | **时长：** 1.5 小时

Subagents 允许你创建专门的 AI Agent 来处理特定任务。

**架构图：**
```
        主 Agent
           │
           ├──► 子 Agent 1（代码审查）
           │
           ├──► 子 Agent 2（安全扫描）
           │
           └──► 子 Agent 3（文档生成）
```

**使用示例：**
```typescript
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
```

### 2.10 模块 9：Advanced Features（高级功能）

**难度：** 高级 | **时长：** 2-3 小时

高级功能涵盖性能优化、生产部署、安全配置等。

**性能优化配置：**
```yaml
# .claude/config.yaml
performance:
  context_window: 200000
  max_tokens: 4096
  temperature: 0.7
  
cache:
  enabled: true
  ttl: 3600
  max_size: 1000
```

**安全配置：**
```yaml
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
```

### 2.11 模块 10：Plugins（插件系统）

**难度：** 高级 | **时长：** 2 小时

Plugins 允许你打包和分发完整的 Claude Code 扩展。

**插件结构：**
```
my-plugin/
├── plugin.json          # 插件元数据
├── skills/              # 技能
├── hooks/               # 钩子
├── commands/            # 命令
└── resources/           # 资源文件
```

**plugin.json 示例：**
```json
{
  "name": "my-code-review-plugin",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "Comprehensive code review plugin",
  "skills": ["./skills/code-review"],
  "hooks": ["./hooks/security-scanner"],
  "commands": ["./commands/review"]
}
```

---

## 三、实战工作流

### 3.1 自动化代码审查

**组合功能：** Slash Commands + Subagents + Memory + MCP

```yaml
# .claude/commands/code-review.md
# /code-review - 自动代码审查工作流

## 工作流
1. 读取 CLAUDE.md 了解项目规范
2. 使用 code-review skill 进行基础审查
3. 启动 security-subagent 进行安全扫描
4. 汇总结果并输出报告
```

### 3.2 团队入职助手

**组合功能：** Memory + Slash Commands + Plugins

```markdown
# CLAUDE.md - 团队入职助手

## 团队信息
- 团队成员：Alice (PM), Bob (Dev), Carol (DevOps)
- 工作时间：9:00-18:00 PST
- 紧急联系：Slack #emergency

## 入职流程
1. 环境配置 → 参考 docs/setup.md
2. 代码规范 → 参考 .eslintrc.js
3. 提交流程 → 使用 /git-workflow 命令
```

### 3.3 CI/CD 自动化

**组合功能：** CLI + Hooks + Background Tasks

```bash
# Git hook 配置
# .git/hooks/pre-commit
claude --command "lint-and-test"

# 自动部署
claude --background --watch "src/**/*.ts" "npm run build && deploy.sh"
```

### 3.4 安全审计

**组合功能：** Subagents + Skills + Hooks（只读模式）

```typescript
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
```

### 3.5 复杂重构

**组合功能：** Checkpoints + Planning Mode + Hooks

```bash
# 保存检查点
/checkpoint save "重构前状态"

# 启用规划模式
/planning on

# 执行重构...

# 验证后保存新检查点
/checkpoint save "重构完成"
```

---

## 四、安装与配置

### 4.1 快速开始（15 分钟）

```bash
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
```

### 4.2 完整开发环境设置（1 小时）

```bash
# Slash Commands (15 分钟)
cp 01-slash-commands/*.md ~/.claude/commands/

# 项目 Memory (15 分钟)
cp 02-memory/project-CLAUDE.md ./CLAUDE.md

# 安装 Skill (15 分钟)
cp -r 03-skills/code-review ~/.claude/skills/

# 配置 Hooks (15 分钟)
cp -r 06-hooks/* ~/.claude/hooks/
```

### 4.3 目录结构规范

```
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
```

---

## 五、自定义开发

### 5.1 开发自定义 Skill

```yaml
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
```

### 5.2 开发自定义 Hook

```typescript
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
```

### 5.3 开发 MCP 服务器

```typescript
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
```

---

## 六、最佳实践

### 6.1 项目结构最佳实践

```markdown
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
```

### 6.2 Hooks 安全配置

```typescript
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
```

### 6.3 性能优化

```yaml
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
```

---

## 七、常见问题解答

### Q1: Claude How To 是免费的吗？

**是的。** MIT 协议，永久免费。可用于个人项目、工作、团队，无限制（只需保留许可证声明）。

### Q2: 这个项目还在维护吗？

**是的，活跃维护。** 与每个 Claude Code 版本同步更新（最新：v2.2.0，2026年3月）。

### Q3: 我需要先掌握什么基础知识？

- 基本命令行操作
- 了解 AI/LLM 基本概念
- 有编程经验（任意语言）

### Q4: 学习完需要多长时间？

完整学习路径：**11-13 小时**

- 初学者模块：~2.5 小时
- 中级模块：~3.5 小时
- 高级模块：~5 小时

### Q5: 如何获取帮助？

- GitHub Issues：https://github.com/luongnv89/claude-howto/issues
- 社区讨论：参与 Fork 项目提交 PR

---

## 八、总结

### 8.1 Claude How To 价值

| 价值 | 说明 |
|------|------|
| **结构化** | 不需要自己摸索学习路径 |
| **可视化** | Mermaid 图表理解底层原理 |
| **可复制** | 生产级模板直接可用 |
| **自测** | 交互式测验找准缺口 |
| **活跃维护** | 与 Claude Code 版本同步 |

### 8.2 成功关键

1. **循序渐进** - 不要跳级，先掌握基础
2. **动手实践** - 每个模块都亲自尝试
3. **组合使用** - 真正力量在于功能组合
4. **持续迭代** - 根据项目需求定制

### 8.3 下一步行动

```bash
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

*🦞 每日08:00自动更新*
