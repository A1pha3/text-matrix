---
title: "Claude Code Game Studios：11.5K Stars的多Agent游戏开发工作室——49个AI角色、72个技能、12个钩子的完整游戏开发工作流"
date: "2026-04-16T01:40:00+08:00"
slug: "claude-code-game-studios-multi-agent-game-dev"
description: "Claude Code Game Studios是11.5K Stars的开源项目，将Claude Code转变为完整的游戏开发工作室。49个AI agents（导演/主程/美术总监）、72个技能（设计/开发/测试/发布）、12个钩子自动化验证。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "游戏开发", "多Agent", "AI", "工作流"]
---

# Claude Code Game Studios：11.5K Stars的多Agent游戏开发工作室——49个AI角色、72个技能、12个钩子的完整游戏开发工作流

> **目标读者**：独立游戏开发者、AI应用研究者、软件开发团队、对多Agent系统感兴趣的任何人
> **预计阅读时间**：45-60分钟
> **前置知识**：对 Claude Code 有基本了解，知道什么是游戏开发流程
> **难度定位**：⭐⭐⭐⭐ 专家设计

---

## §1 学习目标

完成本篇文章后，你将能够：

1. **理解多Agent游戏开发工作室的架构**：为何需要专业化分工
2. **掌握49个AI角色的职责和层级**：从导演到专家的完整体系
3. **熟练使用72个Slash Commands**：覆盖游戏开发的全生命周期
4. **理解12个自动化钩子的机制**：提交验证、推送检查、Session管理
5. **自定义这个工作流**：根据项目需求调整agents、skills、rules
6. **应用到自己的游戏项目**：从想法到发布的完整指南

---

## §2 背景与动机

### 2.1 独自开发游戏的挑战

用 AI 辅助独自开发游戏很强大，但存在问题：

| 问题 | 描述 |
|------|------|
| **无结构** | 单个聊天会话没有组织架构 |
| **无规范** | 可以随意硬编码、跳过设计文档 |
| **无审查** | 没有 QA、没有设计评审 |
| **无愿景** | 没人问"这是否符合游戏愿景？" |

### 2.2 Claude Code Game Studios 的解决方案

给 AI 会话赋予真实工作室的结构：

```
不是：一个通用助手
而是：49个专业化 agents，组成工作室层级
```

**结果**：你仍然做所有决定，但现在有一个团队会问正确的问题、在早期发现错误、保持项目从头脑风暴到发布的组织性。

---

## §3 项目概览

### 3.1 基本信息

| 属性 | 值 |
|------|------|
| **Stars** | 11,142 ⭐ |
| **类型** | Claude Code 模板/工具包 |
| **语言** | Shell（项目本身）+ Markdown（agents配置） |
| **许可证** | MIT |
| **平台** | Windows/macOS/Linux |

### 3.2 核心组件一览

| 组件 | 数量 | 说明 |
|------|------|------|
| **Agents** | 49 | 专业化的 AI 子代理 |
| **Skills** | 72 | Slash commands 工作流 |
| **Hooks** | 12 | 自动化验证脚本 |
| **Rules** | 11 | 路径作用域编码标准 |
| **Templates** | 39 | 文档模板 |

---

## §4 工作室层级架构

### 4.1 三层架构

Agents 按三个层级组织，匹配真实工作室的运作方式：

```
Tier 1 — 导演 (Opus)
  creative-director    technical-director    producer

Tier 2 — 部门主管 (Sonnet)
  game-designer        lead-programmer       art-director
  audio-director       narrative-director    qa-lead
  release-manager      localization-lead

Tier 3 — 专家 (Sonnet/Haiku)
  gameplay-programmer  engine-programmer     ai-programmer
  network-programmer   tools-programmer      ui-programmer
  systems-designer     level-designer        economy-designer
  technical-artist     sound-designer        writer
  ...
```

### 4.2 Tier 1：导演层

| Agent | 职责 | 使用模型 |
|-------|------|----------|
| **creative-director** | 守护游戏愿景 | Opus |
| **technical-director** | 技术决策和架构 | Opus |
| **producer** | 跨部门协调和变更传播 | Opus |

### 4.3 Tier 2：部门主管

| Agent | 职责 | 使用模型 |
|-------|------|----------|
| **game-designer** | 游戏设计和平衡 | Sonnet |
| **lead-programmer** | 编程规范和代码审查 | Sonnet |
| **art-director** | 美术方向和资源管理 | Sonnet |
| **audio-director** | 音效和音乐方向 | Sonnet |
| **narrative-director** | 叙事和对话 | Sonnet |
| **qa-lead** | 测试和质量保证 | Sonnet |
| **release-manager** | 发布和版本管理 | Sonnet |
| **localization-lead** | 本地化和国际化 | Sonnet |

### 4.4 Tier 3：专家层

**编程专家**：

| Agent | 职责 |
|-------|------|
| **gameplay-programmer** | 游戏玩法逻辑 |
| **engine-programmer** | 引擎底层代码 |
| **ai-programmer** | AI 和导航系统 |
| **network-programmer** | 多人游戏网络 |
| **tools-programmer** | 开发工具 |
| **ui-programmer** | UI 和 HUD |

**设计专家**：

| Agent | 职责 |
|-------|------|
| **systems-designer** | 系统设计 |
| **level-designer** | 关卡设计 |
| **economy-designer** | 经济系统设计 |

**美术专家**：

| Agent | 职责 |
|-------|------|
| **technical-artist** | 技术美术（Shader等） |
| **ux-designer** | 用户体验设计 |

**其他专家**：

| Agent | 职责 |
|-------|------|
| **performance-analyst** | 性能分析 |
| **devops-engineer** | CI/CD 和构建 |
| **security-engineer** | 安全审计 |
| **qa-tester** | 测试执行 |
| **accessibility-specialist** | 无障碍设计 |
| **live-ops-designer** | 运营活动设计 |

### 4.5 引擎专家

模板包含三个主流引擎的专属 agents：

| 引擎 | 主管 Agent | 专家 |
|------|-----------|------|
| **Godot 4** | godot-specialist | GDScript, Shaders, GDExtension |
| **Unity** | unity-specialist | DOTS/ECS, Shaders/VFX, Addressables |
| **Unreal Engine 5** | unreal-specialist | GAS, Blueprints, Replication, UMG |

---

## §5 72个Skills详解

### 5.1 技能分类总览

| 类别 | 数量 | 示例 |
|------|------|------|
| **入职与导航** | 5 | /start, /help, /setup-engine |
| **游戏设计** | 6 | /brainstorm, /design-system, /review-all-gdds |
| **美术与资源** | 3 | /art-bible, /asset-spec |
| **架构** | 4 | /create-architecture, /architecture-decision |
| **故事与冲刺** | 7 | /create-epics, /create-stories, /dev-story |
| **评审与分析** | 10 | /design-review, /code-review, /balance-check |
| **QA与测试** | 10 | /qa-plan, /smoke-check, /regression-suite |
| **生产** | 8 | /milestone-review, /bug-report |
| **发布** | 5 | /release-checklist, /launch-checklist |
| **团队协作** | 10+ | /team-combat, /team-narrative, /team-ui |

### 5.2 核心技能详解

**/start — 项目启动**：

```bash
# 在 Claude Code 中输入
/start

# 系统会问：
# - 你在哪里？（没想法/模糊概念/清晰设计/已有项目）
# - 然后引导你到正确的工作流
```

**/brainstorm — 头脑风暴**：

探索游戏想法，从零开始：

```bash
/brainstorm

# 触发：
# - 玩法机制讨论
# - 目标用户分析
# - 竞争产品对比
# - 风险识别
```

**/setup-engine — 引擎配置**：

```bash
# 设置游戏引擎
/setup-engine godot 4.6
/setup-engine unity 2023.2
/setup-engine unreal 5.4
```

**/create-epics — 创建史诗**：

将游戏分解为大型功能模块：

```bash
/create-epics

# 输出：
# - Epic 1: 核心战斗系统
# - Epic 2: 多人系统
# - Epic 3: 存档系统
```

**/create-stories — 创建故事卡**：

将 Epic 分解为可执行的任务：

```bash
/create-stories epic-1

# 输出：
# - Story 1.1: 角色移动
# - Story 1.2: 攻击动画
# - Story 1.3: 敌人AI
```

**/dev-story — 开发故事**：

执行具体的故事卡开发：

```bash
/dev-story 1.1

# 触发：
# - 编写代码
# - 编写测试
# - 设计文档更新
```

### 5.3 团队协作技能

**/team-combat — 战斗系统团队**：

协调多个 agents 开发战斗系统：

```bash
/team-combat

# 启动：
# - gameplay-programmer
# - ai-programmer
# - ui-programmer
# - qa-tester
# 协同工作
```

---

## §6 12个Hooks详解

### 6.1 Hooks 概览

Hooks 在关键事件自动触发验证：

| Hook | 触发 | 功能 |
|------|------|------|
| `validate-commit.sh` | PreToolUse (Bash) | 提交验证 |
| `validate-push.sh` | PreToolUse (Bash) | 推送验证 |
| `validate-assets.sh` | PostToolUse | 资源验证 |
| `session-start.sh` | Session open | 显示分支和提交 |
| `detect-gaps.sh` | Session open | 检测缺失 |
| `pre-compact.sh` | Before compaction | 保存进度 |
| `post-compact.sh` | After compaction | 恢复状态 |
| `notify.sh` | Notification | Windows 通知 |
| `session-stop.sh` | Session close | 归档活动 |
| `log-agent.sh` | Agent spawn | Agent 调用记录 |
| `log-agent-stop.sh` | Agent stop | Agent 完成记录 |
| `validate-skill-change.sh` | Skill change | 建议运行测试 |

### 6.2 提交验证

`validate-commit.sh` 在 git commit 时自动检查：

```bash
# 检查项：
# - 硬编码值
# - TODO 格式
# - JSON 有效性
# - 设计文档章节
```

### 6.3 推送验证

`validate-push.sh` 在 git push 时警告：

```bash
# 检查：
# - 是否推送到受保护分支
# - 是否有未提交的更改
```

### 6.4 Session管理

```bash
# Session 启动时
session-start.sh → 显示分支和近期提交

# Session 关闭时
session-stop.sh → 归档 active.md 到 session log

# Session 压缩前
pre-compact.sh → 保存进度到 active.md

# Session 压缩后
post-compact.sh → 从 active.md 恢复状态
```

---

## §7 11个路径规则

### 7.1 规则总览

编码标准按文件位置自动执行：

| 路径 | 强制规则 |
|------|----------|
| `src/gameplay/**` | 数据驱动、Delta Time、无 UI 引用 |
| `src/core/**` | 热路径零分配、线程安全 |
| `src/ai/**` | 性能预算、可调试性 |
| `src/networking/**` | 服务器权威、版本化消息 |
| `src/ui/**` | 无游戏状态拥有权、本地化就绪 |
| `design/gdd/**` | 必须8章节、公式格式 |
| `tests/**` | 测试命名、覆盖率要求 |
| `prototypes/**` | 宽松标准、需 README |

### 7.2 规则示例

**src/gameplay/** 规则：

```
- 必须使用数据驱动值（不能硬编码）
- 必须使用 delta time
- 不能直接引用 UI 模块
```

**src/core/** 规则：

```
- 热路径禁止内存分配
- 必须线程安全
- API 必须稳定
```

---

## §8 项目结构

### 8.1 目录树

```
Claude-Code-Game-Studios/
├── CLAUDE.md                      # 主配置
├── .claude/
│   ├── settings.json              # Hooks、权限、安全规则
│   ├── agents/                   # 49个 agent 定义
│   │   ├── directors/
│   │   │   ├── creative-director.md
│   │   │   └── technical-director.md
│   │   ├── leads/
│   │   │   ├── game-designer.md
│   │   │   └── lead-programmer.md
│   │   └── specialists/
│   │       ├── gameplay-programmer.md
│   │       └── ...
│   ├── skills/                   # 72个 slash commands
│   │   ├── brainstorm/
│   │   ├── design-system/
│   │   └── ...
│   ├── hooks/                   # 12个 hook 脚本
│   │   ├── validate-commit.sh
│   │   └── ...
│   ├── rules/                   # 11个路径规则
│   │   └── gameplay-coding-standards.md
│   └── docs/
│       ├── workflow-catalog.yaml  # 7阶段管道定义
│       └── templates/            # 39个文档模板
├── src/                         # 游戏源码
├── assets/                      # 美术、音频资源
├── design/                      # GDD、叙事文档
├── docs/                        # 技术文档
├── tests/                       # 测试套件
├── tools/                       # 构建工具
├── prototypes/                  # 原型
└── production/                  # 冲刺计划、发布跟踪
```

### 8.2 CLAUDE.md

主配置文件，定义整个工作流：

```markdown
# CLAUDE.md

## 项目概述
这是一个游戏开发工作室项目...

## 当前阶段
[由 /start 或 /project-stage-detect 设置]

## 活跃史诗
[由 /create-epics 创建]

## 活跃故事
[由 /create-stories 创建]
```

---

## §9 开始使用

### 9.1 前置条件

```bash
# Git
git --version

# Claude Code
npm install -g @anthropic-ai/claude-code

# 推荐：jq（hook验证用）
# 推荐：Python 3（JSON验证用）
```

### 9.2 初始化

```bash
# 1. 克隆或使用为模板
git clone https://github.com/Donchitos/Claude-Code-Game-Studios.git my-game
cd my-game

# 2. 打开 Claude Code
claude

# 3. 运行 /start
/start

# 或直接跳到特定技能
/brainstorm
/setup-engine godot 4.6
```

---

## §10 Agent 协作机制

### 10.1 协作协议

这不是自动驾驶系统！每个 agent 遵循严格的协作协议：

```
1. Ask — 提问先于提案
2. Present options — 展示2-4个选项及优缺点
3. You decide — 你做决定
4. Draft — 展示工作成果再定稿
5. Approve — 你的签字批准才能定稿
```

### 10.2 委托模型

```
垂直委托：导演 → 主管 → 专家
水平咨询：同级 agents 可互相咨询
冲突解决：升级到共同上级
变更传播：跨部门变更由 producer 协调
```

### 10.3 域边界

Agents 不能修改其域外的文件，除非获得明确委托：

```
gameplay-programmer → 只能修改 src/gameplay/**
ui-programmer → 只能修改 src/ui/**
creative-director → 可修改 design/**
```

---

## §11 设计哲学

### 11.1 理论基础

这个模板基于专业游戏开发实践：

| 框架 | 应用 |
|------|------|
| **MDA Framework** | Mechanics/Dynamics/Aesthetics 分析 |
| **Self-Determination Theory** | 自主性/能力/相关性（玩家动机） |
| **Flow State Design** | 挑战-技能平衡 |
| **Bartle Player Types** | 受众定位和验证 |
| **Verification-Driven Development** | 测试优先 |

### 11.2 评审强度

可配置的评审强度：

| 模式 | 说明 |
|------|------|
| **full** | 所有导演门控 |
| **lean** | 仅阶段门控 |
| **solo** | 无评审 |

---

## §12 自定义指南

### 12.1 添加/删除 Agents

```bash
# 删除不需要的 agent
rm .claude/agents/specialists/legacy-programmer.md

# 添加新 agent
vim .claude/agents/specialists/blockchain-programmer.md
```

### 12.2 修改 Skills

```bash
# 修改现有 skill
vim .claude/skills/dev-story/SKILL.md

# 添加新 skill
mkdir .claude/skills/my-custom-skill
vim .claude/skills/my-custom-skill/SKILL.md
```

### 12.3 调整 Hooks

```bash
# 调整验证严格度
vim .claude/hooks/validate-commit.sh

# 添加新检查
vim .claude/hooks/validate-my-check.sh
```

---

## §13 常见问题 FAQ

**Q1: 这个和普通用 Claude Code 有什么区别？**

A：普通 Claude Code 是一个通用助手。这个项目给了它工作室结构——专业化分工、规范、自动化检查、团队协作流程。

**Q2: 需要一直运行吗？**

A：不需要。Session 关闭时自动归档状态，下次打开时恢复。

**Q3: 支持哪些游戏引擎？**

A：Godot 4、Unity、Unreal Engine 5 都有专属 agent set。也支持不使用任何引擎。

**Q4: 如何处理跨域变更？**

A：用 `/propagate-design-change` 或让 `producer` 协调。

**Q5: 可以只用部分功能吗？**

A：可以。这是一个模板，不是锁死框架。完全可自定义。

**Q6: 支持 Windows/Mac/Linux 吗？**

A：支持。主要在 Windows 10 Git Bash 上测试，所有 hooks 使用 POSIX 兼容模式。

---

## §14 相关资源

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/Donchitos/Claude-Code-Game-Studios |
| Claude Code 文档 | https://docs.anthropic.com/en/docs/claude-code |
| GitHub Discussions | https://github.com/Donchitos/Claude-Code-Game-Studios/discussions |

---

**🦞 作者：钳岳星君 | 来源：GitHub Donchitos/Claude-Code-Game-Studios**
