---
title: "everything-claude-code：AI Agent 性能优化系统完全指南"
date: 2026-04-30T20:00:00+08:00
slug: "everything-claude-code-agent-harness-performance"
description: "everything-claude-code 是 GitHub 斩获 17 万星标的开源 AI Agent 性能优化系统，汇聚 48 个专用子智能体、182 项 Skills、68 个遗留命令垫片，深度整合 Claude Code、Cursor、Codex、OpenCode 等主流 Harness。文章剖析其 Skills 工作流、Instincts 本能学习、内存持久化、安全扫描等核心机制，并给出最小化安装与生产级配置实践。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "Agent Harness", "AI Agent", "性能优化", "Skill 工作流"]
---

## 项目概览

[affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code) 是当前 GitHub 星标数最高的 AI 编码辅助工具之一，截至 2026 年 4 月已积累 **170,624 颗星标**、21,000+ 分叉、170+ 贡献者，覆盖 **12 个语言生态**。该项目的核心定位并非单纯的配置包，而是一套经过 **10 个月以上高频日常使用**打磨出来的 Agent Harness 性能优化系统（Performance Optimization System for AI Agent Harnesses）。

### 核心数字一览

| 维度 | 数量 |
|------|------|
| Stars | 170,624 |
| Forks | 21,000+ |
| Contributors | 170+ |
| 语言生态 | 12（TypeScript、Python、Go、Java、Swift、Perl、PHP、C++、Rust、Kotlin 等） |
| 子智能体（Agents） | 48 |
| Skills | 182 |
| 遗留命令垫片（Legacy Commands） | 68 |
| AgentShield 安全规则 | 102 条 |

> **获奖背景：** 该项目在 2025 年 9 月 Anthropic × Forum Ventures 黑客松中斩获冠军。

### 版本演进脉络

- **v1.2.0**（2026 年 2 月）：新增 Python/Django 和 Java Spring Boot 支持，引入基于 Instinct 的连续学习 v2
- **v1.6.0**（2026 年 2 月）：新增 Codex CLI 支持和 AgentShield 安全扫描集成（1,282 条测试，102 条规则），GitHub Marketplace 上线
- **v1.8.0**（2026 年 3 月）：正式确立 **Harness Performance System** 定位，引入 Hook 运行时控制（`ECC_HOOK_PROFILE`、`ECC_DISABLED_HOOKS`）
- **v2.0.0-rc.1**（2026 年 4 月）：新增 Rust 原型控制面（`ecc2/`），Dashboard GUI 全面改版，公开 Hermes 运营工作流

---

## 核心问题与解决思路

在高频使用 Claude Code 等 Agent Harness 的过程中，开发者通常会面临以下几类挑战：

1. **上下文窗口耗尽** — 长会话中模型可用上下文急剧缩减
2. **重复工作流无法复用** — 每开启一个新会话，积累的经验和模式全部丢失
3. **跨语言/跨框架质量不一致** — 同一个 Agent 在不同技术栈下输出质量差异显著
4. **安全风险积累** — Agent 操作文件系统、网络请求、MCP 工具时缺乏统一的审计层
5. **多 Agent 编排效率低下** — 复杂任务缺乏结构化的委托与验证机制

ECC 的设计哲学是将这些问题抽象为可配置的子系统：**Skills（技能工作流）**、**Instincts（本能模式）**、**Memory（内存持久化）**、**Rules（始终遵循的准则）** 和 **Security（安全扫描）**，统一服务于跨 Harness 的性能优化目标。

---

## 架构解析

### 整体组件结构

```
everything-claude-code/
├── agents/              # 48 个专用子智能体（planner、architect、code-reviewer 等）
├── skills/              # 182 项工作流定义（前端、后端、安全、测试等）
├── commands/            # 68 个维护中的斜杠命令（逐步迁移至 Skills）
├── rules/               # 始终生效的开发准则（common/ + 语言特定目录）
├── hooks/               # 触发式自动化（PreToolUse、PostToolUse、Stop 等）
├── scripts/             # 跨平台 Node.js 脚本（hooks 实现、package manager 等）
├── tests/               # 完整测试套件
├── contexts/            # 动态系统提示注入（dev.md、review.md、research.md）
├── mcp-configs/         # MCP 服务器配置（GitHub、Supabase、Vercel 等）
├── ecc_dashboard.py     # Tkinter 桌面 Dashboard GUI
├── ecc2/                # Rust 原型控制面（ECC 2.0 alpha）
└── .claude-plugin/      # 插件与 marketplace 清单
```

### 子智能体体系（Agents）

ECC 提供了 48 个专用子智能体，覆盖软件生命周期的各个环节：

| 智能体 | 职责 |
|--------|------|
| `planner` | 特性实现的计划分解与蓝图生成 |
| `architect` | 系统设计与架构决策 |
| `tdd-guide` | 测试驱动开发工作流 |
| `code-reviewer` | 通用代码质量与安全审查 |
| `security-reviewer` | 漏洞分析与攻击向量评估 |
| `build-error-resolver` | 修复构建错误（通用） |
| `e2e-runner` | Playwright 端到端测试 |
| `refactor-cleaner` | 死代码清理 |
| `database-reviewer` | 数据库查询与 Supabase 审查 |
| `typescript-reviewer` | TypeScript/JavaScript 专项审查 |
| `python-reviewer` | Python PEP 8、安全、类型提示审查 |
| `go-reviewer` / `go-build-resolver` | Go 专项审查与构建修复 |
| `java-reviewer` / `java-build-resolver` | Java/Spring Boot 专项 |
| `kotlin-reviewer` / `kotlin-build-resolver` | Kotlin/Android/KMP 专项 |
| `cpp-reviewer` / `cpp-build-resolver` | C++ 专项 |
| `rust-reviewer` | Rust 专项 |
| `pytorch-build-resolver` | PyTorch/CUDA 训练错误修复 |
| `loop-operator` | 自主循环执行模式 |
| `harness-optimizer` | Harness 配置调优 |

**委托工作流示例：**

```
/everything-claude-code:plan "Add user authentication with OAuth"
    → planner 生成实现蓝图
→ tdd-workflow skill
    → tdd-guide 强制先写测试
→ /code-review
    → code-reviewer 质量把关
```

### Skills 工作流体系

Skills 是 ECC 的**主要工作流表面**（primary workflow surface），每个 Skill 是一个独立的工作流定义文件（SKILL.md），可被直接调用、自动建议或在 Agent 间复用。

#### 核心 Skill 分类

**开发方法论：**

- `tdd-workflow` — 测试驱动开发，要求 80% 以上测试覆盖率
- `e2e-testing` — Playwright E2E 测试与 Page Object Model 模式
- `eval-harness` — 验证循环评估框架
- `verification-loop` — 持续验证（构建→测试→lint→类型检查→安全）

**语言与框架专项：**

- `golang-patterns` / `golang-testing`
- `python-patterns` / `python-testing`
- `django-patterns` / `django-security` / `django-tdd` / `django-verification`
- `laravel-patterns` / `laravel-security` / `laravel-tdd`
- `springboot-patterns` / `springboot-security` / `springboot-tdd`
- `cpp-coding-standards` / `cpp-testing`
- `swift-actor-persistence` / `swift-protocol-di-testing`

**工程实践：**

- `backend-patterns` — API 设计、数据库、缓存模式
- `frontend-patterns` — React、Next.js 模式
- `frontend-slides` — 零依赖 HTML 演示文稿生成
- `docker-patterns` — Docker Compose、网络、卷、安全
- `deployment-patterns` — CI/CD、Docker、健康检查、回滚
- `api-design` — REST API 分页、错误响应设计
- `database-migrations` — Prisma、Drizzle、Django、Go 迁移模式
- `cost-aware-llm-pipeline` — LLM 成本优化、模型路由、预算追踪

**研究与运营（ECC 2.0 Operator lane）：**

- `search-first` — 研究优先于编码的工作流
- `market-research` — 市场与竞品调研
- `investor-materials` — 融资材料生成
- `brand-voice` — 品牌调性内容生成
- `social-graph-ranker` — 社交图谱排序
- `connections-optimizer` — 人脉优化
- `customer-billing-ops` — 客户账务运营
- `ecc-tools-cost-audit` — 成本审计

**智能化进化：**

- `continuous-learning-v2` — 基于 Instinct 的学习系统，含置信度评分
- `iterative-retrieval` — 子 Agent 渐进式上下文精炼
- `strategic-compact` — 手动上下文压缩建议

#### Skill 创建工具

ECC 内置了 `/skill-create` 命令，可以从 Git 仓库历史自动分析并生成 SKILL.md 文件：

```bash
/skill-create                    # 分析当前仓库，生成 Skills
/skill-create --instincts       # 同时为 continuous-learning-v2 生成 Instincts
```

进阶用户可通过 GitHub App（[ecc.tools](https://ecc.tools)）在 Issue 中评论 `/skill-creator analyze` 触发自动分析，支持 10,000+ 提交的大型仓库和团队共享。

### Hooks 触发式自动化

Hooks 在每次工具调用前后触发，实现强制性的运行时行为：

```json
{
  "matcher": "tool == \"Edit\" && tool_input.file_path matches \"\\.(ts|tsx|js|jsx)$\"",
  "hooks": [{
    "type": "command",
    "command": "#!/bin/bash\ngrep -n 'console\\.log' \"$file_path\" && echo '[Hook] Remove console.log' >&2"
  }]
}
```

**内置 Hook 类型：**

| 事件 | 用途 |
|------|------|
| `PreToolUse` | 阻止危险操作（如未加密的密钥读取） |
| `PostToolUse` | 自动格式化、类型检查、日志清理 |
| `Stop` | 会话结束提取学习模式 |
| `SessionStart` | 加载上次会话上下文 |
| `SessionEnd` | 保存会话状态 |
| `PreCompact` | 压缩前保存状态 |
| `SuggestCompact` | 智能建议压缩时机 |

**运行时控制：**

```bash
# Hook 严格级别（默认 standard）
export ECC_HOOK_PROFILE=minimal|standard|strict

# 禁用特定 Hook
export ECC_DISABLED_HOOKS="pre:bash:tmux-reminder,post:edit:typecheck"
```

### Rules 始终生效的准则

Rules 是跨语言、跨项目的通用开发准则，放在 `rules/common/`；语言专项规则放在对应子目录下：

```
rules/
├── common/         # 不可变姓、文件组织、Git 工作流、测试、性能、安全
├── typescript/     # TS/JS 特定模式
├── python/         # Python 特定模式
├── golang/         # Go 特定模式
├── swift/          # Swift 特定模式
└── php/            # PHP 特定模式
```

每个语言目录可独立安装，插件路径下需手动复制到 `~/.claude/rules/ecc/`。

---

## 安全体系：AgentShield

AgentShield 是 ECC 在 2026 年 2 月 Anthropic 黑客松中构建的安全审计工具，核心数据：

- **1,282 条测试用例**
- **102 条静态分析规则**
- **98% 覆盖率**

### 扫描范围

AgentShield 对以下配置进行 5 大类安全审查：

1. **密钥泄露检测**（14 种模式）：检测 `sk-`、`ghp_`、`AKIA` 等敏感前缀
2. **权限审计**：MCP 服务器权限范围评估
3. **Hook 注入分析**：检测恶意 Hook 链
4. **MCP 服务器风险画像**：第三方 MCP 的信任边界
5. **Agent 配置审查**：指令注入风险

### 使用方式

```bash
# 快速扫描（无需安装）
npx ecc-agentshield scan

# 自动修复安全项
npx ecc-agentshield scan --fix

# 深度分析（启动 3 个 Claude Opus 4.6 Agent）
npx ecc-agentshield scan --opus --stream

# 从零生成安全配置
npx ecc-agentshield init
```

`--opus` 模式采用红蓝对抗架构：攻击方 Agent 寻找利用链，防守方 Agent 评估防护层，审计方 Agent 综合输出优先级风险评估。这不是简单的模式匹配，而是**对抗性推理**。

**输出格式：** 终端（颜色分级 A-F）、JSON（CI 流水线集成）、Markdown、HTML。发现严重问题时退出码为 2，可直接作为构建门禁。

在 Claude Code 内可直接运行 `/security-scan`。

---

## Instincts 与连续学习

### Instinct 是什么

Instinct 是 ECC v1.4 引入的**会话级模式提取**机制。传统 Hook 在 `Stop` 阶段自动从会话历史中提取有价值的模式，并以结构化形式保存，供后续会话参考。

### v2 进化版本

`continuous-learning-v2` 相比 v1 的核心改进：

- **置信度评分**：每个 Instinct 附带置信度，区分高置信可复用模式与实验性模式
- **导入/导出**：可在团队间分享 Instinct 集合
- **聚类进化**：`/evolve` 命令将相关 Instinct 聚类为正式 Skill

### 相关命令

| 命令 | 功能 |
|------|------|
| `/instinct-status` | 查看已学习的 Instinct 及置信度 |
| `/instinct-import <file>` | 从外部导入 Instinct |
| `/instinct-export` | 导出个人 Instinct 集合 |
| `/evolve` | 将相关 Instinct 聚类为 Skills |
| `/prune` | 删除超过 30 天 TTL 的过期 Instinct |
| `/learn-eval` | 提取、评估、确认后保存模式 |

### Strategic Compact

`strategic-compact` Skill 提供智能压缩时机建议，避免在实现中途压缩导致变量名、文件路径、部分状态丢失。推荐的压缩时机：

- 研究/探索阶段完成后
- 里程碑完成、下一阶段开始前
- 调试完成后
- 失败方案放弃、新方案开始前

---

## 内存持久化与会话管理

ECC 通过 Hook 体系实现了跨会话的内存持久化：

```bash
# Hook: SessionStart
# 自动加载上次会话上下文

# Hook: SessionEnd
# 自动保存当前会话状态

# Hook: SuggestCompact
# 在逻辑断点建议压缩而非依赖 95% 自动压缩
```

### Token 优化策略

| 设置 | 默认值 | 推荐值 | 影响 |
|------|--------|--------|------|
| `model` | opus | **sonnet** | 约 60% 成本降低 |
| `MAX_THINKING_TOKENS` | 31,999 | **10,000** | 约 70% 隐藏思维成本降低 |
| `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` | 95 | **50** | 更早压缩，长会话质量更稳定 |

```bash
# ~/.claude/settings.json 建议配置
{
  "model": "sonnet",
  "env": {
    "MAX_THINKING_TOKENS": "10000",
    "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "50"
  }
}
```

### MCP 上下文窗口管理

每个 MCP 工具描述都会消耗 200k 上下文窗口的 token，实际可用可能降至 70k。ECC 建议：

- 启用 MCP 不超过 **10 个**
- 活跃工具数不超过 **80 个**
- 使用 `/mcp` 禁用不需要的 MCP（设置写入 `~/.claude.json`，非 `settings.json`）

---

## 跨平台支持

ECC 是**首个最大化覆盖主流 AI 编码工具**的插件，支持矩阵如下：

| 功能 | Claude Code | Cursor IDE | Codex CLI | OpenCode |
|------|------------|------------|-----------|----------|
| Agents | 48 | 通过 AGENTS.md 共享 | 通过 AGENTS.md 共享 | 12 |
| Commands | 68 | 通过 AGENTS.md 共享 | 基于指令 | 31 |
| Skills | 182 | 共享 | 10（原生格式） | 37 |
| Hook 事件类型 | 8 | 15 | 暂不支持 | 11 |
| Rules | 34（common + 语言） | 34（YAML frontmatter） | 基于指令 | 13 |
| 自定义工具 | 通过 Hooks | 通过 Hooks | 不支持 | 6 原生工具 |
| MCP Servers | 14 | 共享 mcp.json | 7（TOML 自动合并） | 完整支持 |

### 各平台安装要点

**Claude Code（推荐路径）：**

```bash
# 添加 marketplace
/plugin marketplace add https://github.com/affaan-m/everything-claude-code

# 安装插件
/plugin install everything-claude-code@everything-claude-code

# 手动复制规则（插件不自动分发 rules/）
mkdir -p ~/.claude/rules/ecc
cp -R rules/common ~/.claude/rules/ecc/
cp -R rules/typescript ~/.claude/rules/ecc/  # 按需选择语言
```

**OpenCode：**

```bash
npm install -g ecc-universal
# 或在仓库根目录运行 opencode
```

**Codex：**

```bash
bash scripts/sync-ecc-to-codex.sh
```

### Cursor 的 DRY Adapter 模式

Cursor 支持比 Claude Code 更多的 Hook 事件类型（20 vs 8）。ECC 为 Cursor 提供 `.cursor/hooks/adapter.js`，将 Cursor 的 stdin JSON 转换为 Claude Code 格式，使 `scripts/hooks/*.js` 可以在两个平台间复用，无需重复实现：

```
Cursor stdin JSON → adapter.js → scripts/hooks/*.js（与 Claude Code 共享）
```

---

## 安装与最小示例

### 推荐安装路径（插件路径）

```bash
# 1. 添加 marketplace
/plugin marketplace add https://github.com/affaan-m/everything-claude-code

# 2. 安装插件
/plugin install everything-claude-code@everything-claude-code

# 3. 手动复制规则（插件无法自动分发）
mkdir -p ~/.claude/rules/ecc
cp -R rules/common ~/.claude/rules/ecc/
cp -R rules/typescript ~/.claude/rules/ecc/
cp -R rules/python ~/.claude/rules/ecc/

# 4. 验证安装
node scripts/ecc.js list-installed
node scripts/ecc.js doctor
```

### 低上下文路径（无 Hooks）

如果只需要 Rules、Agents 和核心 Skills，不想引入全局 Hook：

```bash
./install.sh --profile minimal --target claude
```

### 交互式安装向导

不确定该安装哪些组件？使用顾问工具预览安装计划：

```bash
npx ecc consult "security reviews" --target claude
# 返回匹配的组件、相关 Profile 和预览/安装命令
```

### Dashboard GUI

安装完成后可启动可视化 Dashboard：

```bash
npm run dashboard
# 或
python3 ./ecc_dashboard.py
```

功能：分标签页（Agents、Skills、Commands、Rules、Settings）、深色/浅色主题切换、字体定制、项目 Logo 显示、全局搜索与过滤。

---

## 使用边界与已知限制

1. **插件不自动分发 Rules**：Claude Code 插件系统不支持通过插件分发 `rules/`，必须手动复制。这在 README 中有明确说明，是上游设计限制，非 ECC bug。

2. **Hooks 自动加载行为**：Claude Code v2.1+ 会**自动加载**插件内的 `hooks/hooks.json`，请勿在 `plugin.json` 中显式声明 `"hooks"` 字段，否则触发重复检测错误。

3. **多安装路径互斥**：不要同时使用 `/plugin install` 和 `./install.sh --profile full`。最常见的损坏配置就是两种路径叠加安装导致重复。

4. **multi-* 命令需要额外运行时**：`/multi-plan`、`/multi-execute` 等多 Agent 命令依赖 `ccg-workflow` 运行时（提供 `~/.claude/bin/codeagent-wrapper` 等），未安装该运行时前这些命令无法正常运行。

5. **MCP 令牌消耗**：启用超过 10 个 MCP 会显著消耗上下文窗口，实际可用空间可能从 200k 降至 70k。

6. **Codex 缺少 Hook 执行**：当前 Codex 构建尚未提供 Claude 风格的 Hook 执行能力，ECC 在 Codex 上的安全防护依赖 `AGENTS.md` 指令和沙箱权限配置实现。

---

## 总结

everything-claude-code 的核心价值在于将**真实的开发经验系统化**：不是配置文件，而是经过 10 个月高频使用打磨出来的、涵盖 48 个专用智能体、182 项 Skills、102 条安全规则的完整 Agent 工作流体系。

其设计遵循几个重要原则：

- **可组合性**：每个组件（Agents、Skills、Rules、Hooks）均可独立安装，按需取用
- **跨平台一致**：同一套 Skills 在 Claude Code、Cursor、Codex、OpenCode 间尽量保持功能对等
- **安全内建**：AgentShield 不是事后扫描，而是集成在每次 `security-scan` 调用中的对抗性推理管道
- **持续进化**：Instincts 机制使系统能从日常使用中自动提取和积累模式

如果你是 Claude Code（或其他 Agent Harness）的重度用户，ECC 提供的不是更多配置，而是**一套经过验证的 Agent 协作与质量保障框架**，让 AI 编码辅助从"一次性的工具调用"进化为"可持续优化的智能工作流"。

---

## 参考链接

- GitHub 仓库：https://github.com/affaan-m/everything-claude-code
- Shorthand 入门指南：https://x.com/affaanmustafa/status/2012378465664745795
- Longform 进阶指南：https://x.com/affaanmustafa/status/2014040193557471352
- Security 安全指南：https://x.com/affaanmustafa/status/2033263813387223421
- ECC Tools GitHub Marketplace：https://github.com/marketplace/ecc-tools
- AgentShield npm：https://www.npmjs.com/package/ecc-agentshield
