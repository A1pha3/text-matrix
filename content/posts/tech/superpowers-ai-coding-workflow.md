---
title: "Superpowers 入门到精通：AI 编码工作流的完整开发框架"
date: "2026-03-28T13:49:00+08:00"
slug: "superpowers-ai-coding-workflow"
description: "深入解析 Superpowers 框架，涵盖 Skills 系统、子代理驱动开发、TDD 流程与多平台安装配置指南。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "Claude Code", "Cursor", "工作流", "编码助手"]
---

# Superpowers 入门到精通：AI 编码工作流的完整开发框架

> **难度**：⭐⭐⭐（进阶分析 / 专家设计）
> **目标读者**：希望借助 AI 编码助手提升开发效率的中高级工程师
> **前置知识**：了解 AI 编码助手（Claude Code / Cursor 等）的基本用法，熟悉 Git 工作流
> **预计阅读时间**：约 30 分钟

---

## 🎯 学习目标

完成本文后，你将能够：

- 理解为什么 AI 编程需要结构化工作流框架
- 掌握 Superpowers 的核心设计理念和六步开发流程
- 深入理解 Skills 系统的架构原理与组合机制
- 熟练使用 7 个核心 Skills 完成完整开发周期
- 在 Claude Code、Cursor、Codex 等主流平台安装和配置 Superpowers
- 学会编写自定义 Skill，将个人开发方法论工具化

---

## 1. 原理分析：为什么需要 AI 编程工作流框架

### 1.1 AI 编码助手的"快"陷阱

当你第一次使用 Claude Code 或 Cursor 时，可能会被它的能力震惊——几秒钟生成一个组件，几分钟完成一个小功能。但随着使用深入，一个 pattern 开始反复出现：

**场景 A（冲动型）**：
```
用户：帮我给这个 API 加个缓存
AI：马上写！✓ 已添加 cache 模块
用户：等等，这个缓存在集群环境下会怎样？
AI：呃……
```

**场景 B（碎片型）**：
```
用户：实现用户注册功能
AI：写完了！
用户：测试在哪？
AI：哦，补上。（写了一个 import unittest 但从未运行的测试）
用户：异常处理呢？
AI：马上加。（又产生了新的 bug）
```

问题的根源不在于 AI 不够强大，而在于**没有足够的结构来约束 AI 的行为边界**。AI 天生地倾向于快速给出"看起来正确"的答案，而不是"真正正确"的答案。

### 1.2 Superpowers 的核心洞察

Superpowers 的作者 Jesse Vincent（HashiCorp、Best Practical 的早期工程师）提出了一个关键问题：

> **"与其训练更好的模型，不如给模型更好的指令结构。"**

Superpowers 并不修改 AI 模型本身，而是通过一套**初始指令（Initial Instructions）** 和**可组合的 Skills** 来规范 AI 编码助手的行为。它的核心主张是：

1. **后退一步**：在写代码之前，先理解用户真正想要什么
2. **系统化优先于临时发挥**：有纪律的开发流程优于靠灵感的开发
3. **证据优于声明**：测试通过才算完成，而不是"看起来没问题"
4. **简单性是主要目标**：YAGNI（You Aren't Gonna Need It）原则贯穿始终

### 1.3 六步开发流程

当 Superpowers 激活时，它不会立即跳入写代码，而是遵循以下六步：

```
┌─────────────────────────────────────────────────────────┐
│  步骤 1：后退一步（Step Back）                            │
│  "我想确认一下，你是想实现 XXX 吗？具体来说……"              │
├─────────────────────────────────────────────────────────┤
│  步骤 2：提炼规格（Extract Spec）                         │
│  将对话转化为结构化的 SPEC.md                              │
├─────────────────────────────────────────────────────────┤
│  步骤 3：分块展示（Chunked Presentation）                 │
│  将规格拆分为短小、可消化的段落，逐段确认                  │
├─────────────────────────────────────────────────────────┤
│  步骤 4：制定计划（Make a Plan）                          │
│  创建足够清晰的实现计划，可供"热情的初级工程师"执行        │
├─────────────────────────────────────────────────────────┤
│  步骤 5：子代理驱动开发（Subagent-Driven Development）     │
│  调度子代理处理每个工程任务，审查后继续                    │
├─────────────────────────────────────────────────────────┤
│  步骤 6：TDD 优先（Test-First）                           │
│  红→绿→重构，强调真正的测试驱动开发                        │
└─────────────────────────────────────────────────────────┘
```

这套流程确保了 AI 的输出始终与用户意图对齐，并且经过了充分的验证。

---

## 2. 架构分析：Skills 系统与子代理驱动开发

### 2.1 Skills 系统的设计哲学

Superpowers 的核心抽象是 **Skill（技能）**。一个 Skill 是：

> **一组结构化的指令，使 AI 编码助手能够在特定情境下执行特定类型的任务。**

这听起来很像"提示词模板"，但关键区别在于：**Skill 不是一段静态文本，而是一个包含触发条件、执行步骤和退出标准的最小执行单元。**

### 2.2 Skill 的内部结构

每个 Skill 包含以下核心组成部分：

```
┌──────────────────────────────────────────────────────┐
│  Skill 元信息（Metadata）                             │
│  - name: 技能名称                                     │
│  - trigger: 触发时机（自动激活 / 手动调用）            │
│  - description: 功能描述                             │
│  - dependencies: 依赖的其他 Skills                    │
├──────────────────────────────────────────────────────┤
│  前置条件（Pre-conditions）                           │
│  - 检查环境状态、文件状态、变量状态                    │
├──────────────────────────────────────────────────────┤
│  核心指令（Core Instructions）                         │
│  - 详细的执行步骤（通常为 5-15 个步骤）                │
│  - 每个步骤都有明确的验收标准                          │
├──────────────────────────────────────────────────────┤
│  后置验证（Post-verification）                        │
│  - 验证任务是否真正完成                                │
│  - 失败时提供具体的修复建议                            │
└──────────────────────────────────────────────────────┘
```

### 2.3 Skills 的组合机制

Skills 之间的关系不是线性链式的，而是**图结构**的：

- Skill A 可以在执行过程中调用 Skill B
- Skill B 完成后，控制权返回给 Skill A
- 部分 Skills 可以并行执行（如独立的测试任务）

这种设计带来了极强灵活性：用户可以像搭积木一样组合 Skills，构建适合自己的开发流程。

### 2.4 子代理驱动开发（Subagent-Driven Development）

Superpowers 的另一个核心创新是**子代理驱动开发模式**。

当制定好计划后，Superpowers 不是让一个 AI 代理完成所有工作，而是：

1. 将计划中的每个任务**封装为一个独立的子代理调用**
2. 每个子代理在**隔离的 Git Worktree** 中执行
3. 主代理负责**调度、审查和协调**
4. 子代理完成后，主代理审查其输出，然后才推进下一步

```
主代理（Main Agent）
  ├── 任务 1 → 子代理 A（独立 Worktree）
  │             └── 结果：审查通过 ✓ → 进入下一步
  ├── 任务 2 → 子代理 B（独立 Worktree）
  │             └── 结果：审查发现问题 → 打回重做
  └── 任务 3 → 子代理 C（独立 Worktree，可与 B 并行）
                └── 结果：审查通过 ✓ → 进入下一步
```

这种模式的三大好处：

- **隔离性**：每个任务在独立工作空间执行，不会相互干扰
- **可审查性**：每个任务的输出都必须经过主代理审查
- **并行性**：独立任务可以同时执行，大幅提升效率

---

## 3. 核心 Skills 详解

Superpowers 提供了一系列核心 Skills，覆盖了开发的完整生命周期。

### 3.1 brainstorming——编码前的想法打磨

**何时触发**：在开始写代码之前激活

**核心作用**：通过提问完善想法，避免过早进入实现细节

**工作方式**：

```
用户：我想给这个 API 加缓存
↓
brainstorming 激活：
  "让我确认一下：你想给哪个端点加缓存？缓存策略是什么？
   是本地内存缓存还是分布式缓存？
   缓存的 key 如何设计？
   缓存失效策略是什么？
   你希望缓存命中和未命中时的行为分别是什么？"
↓
用户回答后 → 想法被精炼为清晰的规格
```

**关键原则**：brainstorming 的每一个问题都服务于**减少歧义**和**暴露假设**。它不是在审问用户，而是在帮助用户发现自己的想法中尚未考虑周全的部分。

### 3.2 writing-plans——将工作分解为可执行的任务

**何时触发**：规格确认后，设计方案批准后激活

**核心作用**：将规格文档拆解为 2-5 分钟可完成的小任务

**输出格式**：

```markdown
## 实现计划

### 任务 1：添加缓存配置文件（2 分钟）
- 创建 `cache_config.py`
- 定义 CacheStrategy 枚举（LRU / LFU / TTL）
- **验收标准**：文件可被 import 且无语法错误

### 任务 2：实现内存缓存后端（5 分钟）
- 实现 InMemoryCache 类
- 支持 get / set / delete / clear
- **验收标准**：单元测试覆盖所有方法，覆盖率 > 90%

### 任务 3：集成缓存层到 API 层（5 分钟）
- 修改 `api/handlers.py` 注入缓存
- **验收标准**：现有集成测试全部通过
```

**关键原则**：每个任务的粒度都经过精心设计——太小（< 2 分钟）会导致频繁切换成本过高，太大（> 5 分钟）会导致验收标准模糊。"2-5 分钟"是一个经过大量实践验证的黄金区间。

### 3.3 subagent-driven-development/executing-plans——子代理执行与验证

**何时触发**：计划制定完成后激活

**核心作用**：按照计划逐个调度子代理执行任务，并在每步进行验证

**执行循环**：

```
for task in plan:
    subagent = spawn_fresh_subagent(task)
    result = subagent.execute()
    
    if verify(result):
        continue  # 进入下一步
    else:
        subagent.fix(feedback)  # 打回修复
        retry_until_pass()       # 重试直到通过
```

**关键原则**：Superpowers 的"软性失败"哲学——测试失败不是灾难，而是信息。子代理遇到失败时，会得到具体的修复建议，而不是简单的"重试"。

### 3.4 test-driven-development——红 / 绿 / 重构循环

**何时触发**：编写功能代码之前或同时激活

**核心作用**：实施真正的 TDD，确保测试先行

**TDD 循环**：

```
┌────────────────────────────────────────────┐
│  阶段 1：红（RED）                          │
│  写一个首先会失败的测试                      │
│  "这个功能还不存在，测试应该失败"            │
├────────────────────────────────────────────┤
│  阶段 2：绿（GREEN）                         │
│  只写通过测试所需的最少代码                  │
│  "不追求完美，只追求通过"                    │
├────────────────────────────────────────────┤
│  阶段 3：重构（REFACTOR）                    │
│  在测试保护下改进代码质量                    │
│  "删除重复、提升清晰度、保持功能不变"         │
└────────────────────────────────────────────┘
```

**Superpowers 对 TDD 的特殊强调**：

- AI 编码助手天生倾向于"先实现后测试"，TDD Skill 强制扭转这一习惯
- 测试必须是**可运行的**，而不是"已写好但从未运行"
- 覆盖率不是目标，**测试质量**才是目标

### 3.5 using-git-worktrees——隔离工作空间

**何时触发**：设计方案批准后，创建实现分支时激活

**核心作用**：为每个功能或修复创建独立的 Git Worktree，避免分支切换开销

```bash
# 传统的分支开发
git checkout -b feature/cache     # 切换分支
# ...工作...
git checkout main                # 切换回来
git merge feature/cache          # 合并

# 使用 worktree 的 Superpowers 方式
git worktree add ../wt-feature-cache feature/cache
cd ../wt-feature-cache
# ...工作...
# 主仓库不受影响，随时可以开始另一个 worktree
```

**关键原则**：Worktree 解决了 Git 分支切换的"上下文丢失"问题。在 Superpowers 中，每个子代理在独立的 Worktree 中工作，主代理始终保持在主分支，不会因为频繁切换而丢失上下文。

### 3.6 requesting-code-review——任务间的代码审查

**何时触发**：每个任务完成后、下一个任务开始前激活

**核心作用**：在继续推进之前，强制进行代码审查

**审查维度**：

- **正确性**：代码逻辑是否正确处理了规格中的所有 case
- **可读性**：变量命名是否清晰，函数是否职责单一
- **测试覆盖**：是否有遗漏的边界 case
- **安全性**：是否有潜在的安全风险

**关键原则**：代码审查不是"找茬"，而是**第二双眼睛**。Superpowers 鼓励审查者用"热情的初级工程师"视角提问——如果一个初级工程师看不懂某段代码，那么这段代码就需要改进。

### 3.7 finishing-a-development-branch——完成时的规范化收尾

**何时触发**：开发分支完成所有任务后激活

**核心作用**：规范化地完成分支的生命周期

**收尾检查清单**：

```
□ 所有测试通过（包括新测试和回归测试）
□ 代码符合项目编码规范
□ 文档已更新（如有必要）
□ Commit 消息符合规范（conventional commits）
□ 推送到远程仓库
□ 创建 Pull Request / Merge Request
□ 关联相关 Issue
□ 通知相关人员审查
□ 清理不再需要的 Worktree
```

---

## 4. 安装与配置：各平台指南

Superpowers 支持主流 AI 编码平台。以下是各平台的安装方法。

### 4.1 Claude Code（推荐）

Claude Code 是 Superpowers 的首发支持平台，提供官方插件市场安装。

**安装步骤**：

1. 确保已安装 Claude Code：`npm install -g @anthropic-ai/claude-code`
2. 在 Claude Code 中执行：
   ```
   /plugin install superpowers@claude-plugins-official
   ```
3. 重启 Claude Code，会话中执行 `/superpowers init` 完成初始化

**验证安装**：

```
/superpowers status
# 预期输出：Superpowers v5.0.6 ✓ 已激活
```

### 4.2 Cursor

Cursor 用户可以通过插件市场安装。

**安装步骤**：

1. 打开 Cursor Settings → Extensions
2. 搜索「Superpowers」
3. 点击 Install
4. 在 Cursor 的 AI Settings 中启用 Superpowers 工作流

**安装命令（备选）**：

```bash
# 如果通过命令行安装
/cursor plugin add superpowers
```

### 4.3 Codex（OpenAI）

Codex 用户从官方仓库获取安装脚本。

**安装步骤**：

1. 访问安装指南：
   ```bash
   Fetch and follow instructions from \
   https://raw.githubusercontent.com/obra/superpowers/refs/heads/main/.codex/INSTALL.md
   ```
2. 按照脚本提示完成配置
3. 在 Codex 会话中执行 `superpowers init`

### 4.4 OpenCode

**安装步骤**：

```bash
# 通过 npm 全局安装
npm install -g superpowers-opencode

# 或通过 pip 安装（如果 OpenCode 环境支持）
pip install superpowers
```

在 OpenCode 配置文件中添加：

```json
{
  "superpowers": {
    "enabled": true,
    "defaultSkills": ["brainstorming", "writing-plans", "tdd"]
  }
}
```

### 4.5 Gemini CLI

**安装步骤**：

```bash
gemini plugin install superpowers
```

在 Gemini CLI 中激活：

```
> superpowers enable
> superpowers configure
```

### 4.6 安装后配置建议

无论哪个平台，建议在初始化后进行以下配置：

| 配置项 | 说明 | 推荐值 |
|--------|------|--------|
| `superpowers.defaultBranch` | 默认工作分支 | `main` |
| `superpowers.worktreePrefix` | Worktree 目录前缀 | `./worktrees/` |
| `superpowers.tddThreshold` | TDD 覆盖率阈值 | `80%` |
| `superpowers.maxSubagents` | 最大并行子代理数 | `3` |

---

## 5. 使用指南：完整工作流示例

下面通过一个具体场景，展示 Superpowers 的完整工作流。

### 5.1 场景设定

> **任务**：为一个 Python FastAPI 项目实现 JWT 认证中间件

### 5.2 第一阶段：Brainstorming

```
用户：帮我实现 JWT 认证中间件

Superpowers（brainstorming 激活）：
"让我确认一下需求：
1. 你想使用哪种 JWT 库？（PyJWT / python-jose / python-jwt）
2. Token 的存储位置？Header（Bearer）？Cookie？还是两者都支持？
3. Token 刷新策略？Access Token + Refresh Token 双 Token？还是单一 Token + 过期时间？
4. 错误响应格式？是返回 JSON 还是重定向？
5. 是否需要支持黑名单 / 注销功能？"

用户：PyJWT，Bearer Header，支持刷新，黑名单暂不需要。

Superpowers：明白了，开始创建规格文档。
```

### 5.3 第二阶段：编写 SPEC.md

```markdown
# JWT 认证中间件规格文档

## 功能需求
- 使用 PyJWT 库
- Bearer Token 在 Authorization Header 中传输
- Access Token 有效期 15 分钟，Refresh Token 有效期 7 天
- Token 刷新接口：`POST /auth/refresh`
- 未授权时返回 401 JSON 响应

## 非功能需求
- 异步支持（使用 async/await）
- 依赖注入，易于测试
- 错误消息不泄露敏感信息

## 验收标准
- [ ] Access Token 过期后正确返回 401
- [ ] 有效 Refresh Token 可以获取新 Access Token
- [ ] 无 Token 或格式错误返回 401
- [ ] 所有路径（除 `/auth/*`）均受保护
- [ ] 单元测试覆盖率 > 85%
```

### 5.4 第三阶段：制定计划

```
Writing-plans 输出：

任务 1：创建 auth 配置模块（2 分钟）
  - 新建 config/auth_settings.py
  - 定义 JWTSetting 模型（Pydantic）
  - 验收：配置可被导入，字段验证生效

任务 2：实现 JWT 工具函数（3 分钟）
  - encode_jwt / decode_jwt / refresh_jwt
  - 验收：单元测试通过，覆盖率 100%

任务 3：实现认证中间件（5 分钟）
  - JWTAuthMiddleware 类
  - verify_token 依赖注入
  - 验收：集成测试通过

任务 4：实现认证路由（3 分钟）
  - POST /auth/login（生成 Token）
  - POST /auth/refresh（刷新 Token）
  - 验收：API 测试通过

任务 5：集成测试与文档（2 分钟）
  - 端到端测试
  - 更新 README
```

### 5.5 第四阶段：子代理驱动执行

```
Subagent-driven-development 激活：

[任务 1] → 子代理 A（Worktree: wt-auth-1）
  → 完成：config/auth_settings.py
  → 主代理审查：✓ 通过

[任务 2] → 子代理 B（Worktree: wt-auth-2）
  → 完成：auth/jwt_utils.py + tests/test_jwt_utils.py
  → 主代理审查：发现覆盖率不足 → 打回
  → 子代理 B 修复：补充边界 case 测试
  → 主代理审查：✓ 通过

[任务 3] + [任务 4]（可并行）
  → 子代理 C + D 并行执行
  → 两个 Worktree 同时工作
  → 各自审查通过后进入任务 5

[任务 5] → 子代理 E（Worktree: wt-auth-final）
  → 完成端到端测试 + README 更新
  → TDD Skill 激活：确认覆盖率 87% > 85% ✓
  → Finishing-a-branch Skill 激活：合并到 main
```

### 5.6 第五阶段：完成分支

```
Finishing-a-branch 激活：

□ 所有测试通过：✓（47 个测试，绿灯）
□ 覆盖率检查：✓（87.3%）
□ Commit 消息：✓（conventional commits 格式）
□ PR 创建：✓（PR #42: feat: add JWT authentication middleware）
□ 通知相关人员：✓（@reviewer）
□ 清理 Worktree：✓（删除了 5 个临时 worktree）
```

---

## 6. 开发扩展：创建自定义 Skill

Superpowers 的 Skills 库是开放的，你完全可以创建自己的 Skill，将个人开发方法论工具化。

### 6.1 Skill 文件结构

```
skills/
  └── my-custom-skill/
        ├── SKILL.md          # Skill 定义文件（必需）
        ├── references/        # 参考文档（可选）
        │     ├── examples.md
        │     └── templates.md
        ├── scripts/           # 辅助脚本（可选）
        │     └── validate.sh
        └── tests/             # Skill 自身测试（可选）
              └── test_skill.py
```

### 6.2 SKILL.md 格式

```markdown
---
name: "my-custom-skill"
description: "描述这个 Skill 的功能，什么时候应该使用它"
version: "1.0.0"
author: "你的名字"
tags: ["workflow", "custom"]
trigger: "manual"   # 可选值：automatic | manual | conditional
---

# My Custom Skill

## 概述

一句话描述这个 Skill 做什么，以及它为什么有用。

## 前置条件

- 已安装 [某依赖]
- 当前在 Git 仓库根目录

## 触发条件

详细描述在什么情况下应该激活这个 Skill。

## 执行步骤

### 步骤 1：[动作名称]

**做什么**：描述这一步要做什么

**验证标准**：这一步骤完成时应该满足什么条件

```bash
# 执行命令
some_command --flag value
```

### 步骤 2：[动作名称]

**做什么**：……

## 异常处理

| 异常情况 | 处理方式 |
|----------|----------|
| 命令失败 | 显示错误信息，提供修复建议 |
| 条件不满足 | 说明缺失的条件，提供解决方法 |

## 验收标准

- [ ] 条件 A 满足
- [ ] 条件 B 满足
```

### 6.3 创建示例：documentation-check Skill

假设你经常需要在代码变更后检查文档同步情况，可以创建一个 `documentation-check` Skill：

```markdown
---
name: "documentation-check"
description: "在代码变更后检查相关文档是否同步更新"
trigger: "automatic"
---

# Documentation Check Skill

## 触发条件

当检测到以下文件变更时自动激活：
- `*.py` / `*.ts` / `*.js` → 检查 `docs/` 中是否有相关文档
- `API*.md` 变更 → 检查代码中是否有对应实现
- `CHANGELOG.md` 变更 → 检查版本号是否正确

## 执行步骤

### 步骤 1：识别变更文件

列出本次变更涉及的所有文件。

### 步骤 2：查找相关文档

对于每个代码文件，查找名称相似的 `.md` 文件或 `docs/` 目录下的相关文档。

### 步骤 3：检查同步状态

```
相关文档存在？
├── 是 → 检查最后修改时间是否在代码变更之后
│         ├── 是 → ✓ 同步
│         └── 否 → ⚠️ 文档可能过期
└── 否 → 📝 建议添加文档（如果公共 API 变更）
```

### 步骤 4：输出报告

```markdown
## 文档同步报告

| 文件 | 相关文档 | 同步状态 |
|------|----------|----------|
| auth/jwt.py | docs/auth.md | ⚠️ 过期（代码新于文档 3 天） |
| api/users.py | docs/api/users.md | ✓ 同步 |
```

## 验收标准

- [ ] 所有公共 API 变更都有对应文档更新记录
- [ ] 报告清晰标识了需要关注的文档
```

### 6.4 Skill 的注册与分发

创建好 Skill 后，在项目的 `superpowers.json` 中注册：

```json
{
  "skills": [
    "brainstorming",
    "writing-plans",
    "subagent-driven-development/executing-plans",
    "test-driven-development",
    "my-custom-skill"
  ]
}
```

你也可以将 Skill 发布到社区（参考 Superpowers 官方仓库的 `skills/` 目录结构）。

---

## 7. 最佳实践

### 7.1 Skill 组合的最佳顺序

```
编码前           → brainstorming
                  → writing-plans
                  → using-git-worktrees

编码中（循环）    → subagent-driven-development/executing-plans
                  → test-driven-development（RED-GREEN-REFACTOR）
                  → requesting-code-review

编码后           → finishing-a-development-branch
                  → documentation-check（如果使用了自定义 Skill）
```

### 7.2 避免常见反模式

| 反模式 | 问题 | 正确做法 |
|--------|------|----------|
| **跳过 brainstorming** | 需求不清就开始写，返工率高 | 无论如何先走 brainstorming，哪怕只有 2 分钟 |
| **跳过 TDD** | "测试太慢了，先写功能" | 测试先行，小步快跑 |
| **跳过审查** | "看起来没问题，直接合并" | 每个任务必须经过审查才能继续 |
| **任务粒度过大** | 一个任务超过 15 分钟 | 拆分任务，每个任务 2-5 分钟 |
| **忽视 worktree 清理** | Worktree 堆积，仓库混乱 | finishing-a-branch 必须包含清理步骤 |

### 7.3 团队协作建议

- **共享 Skill 库**：团队可以维护一套标准的 Skills，在 `.superpowers/skills/` 中共享
- **Code Review 作为 Social Contract**：Review 不是批评，而是集体对代码质量的承诺
- **定期回顾 Skill 效果**：每两周回顾一次 Skill 使用效果，持续改进

### 7.4 Superpowers 与现有工具链的整合

Superpowers 不是要替代你现有的工具链，而是整合其中：

- **Git**：通过 `using-git-worktrees` 和 `finishing-a-development-branch` 与 Git 深度整合
- **测试框架**：TDD Skill 与 pytest、unittest、Jest 等框架兼容
- **CI/CD**：Superpowers 的验证步骤可以在 CI 中重复执行，确保每次合并都符合标准
- **文档工具**：与 Markdown 文档、OpenAPI 规范等无缝衔接

---

## 8. FAQ

### Q1：Superpowers 和普通的提示词工程有什么区别？

**A**：Superpowers 的本质不是"写更好的提示词"，而是**建立一套规范 AI 行为的系统**。普通的提示词工程依赖单次调用，而 Superpowers 通过 Skills 的组合和子代理的调度，在多个调用之间维持状态和上下文的连贯性。

可以这样理解：提示词工程是"告诉 AI 一次做什么"，Superpowers 是"告诉 AI 在一个完整的开发周期里如何系统地工作"。

### Q2：Superpowers 适合什么规模的项目？

**A**：Superpowers 最适合**中型项目**（数千行代码，多个模块协作）和**需要长期维护的项目**。对于一次性的小脚本（< 50 行），Superpowers 的流程可能过于重量。

但值得注意的是，即使是小项目，也可以只使用部分 Skills（如 `brainstorming` + `test-driven-development`），而不必启用全套流程。

### Q3：必须使用 Git Worktree 吗？

**A**：不是必须。`using-git-worktrees` 是一个可选的 Skill，如果你不习惯 Worktree 的工作方式，可以跳过它，Superpowers 会回退到传统的分支开发模式。

但如果你使用 `subagent-driven-development`（子代理驱动开发），Worktree 是强烈推荐的，因为子代理需要隔离的工作空间。

### Q4：子代理失败时怎么办？

**A**：Superpowers 的设计哲学是"失败即信息"。当子代理失败时：

1. 主代理分析失败原因（通常在 `verify` 阶段发现）
2. 主代理向子代理提供具体的修复建议（不是简单地说"重试"）
3. 子代理根据建议修复后重新提交
4. 如果连续失败 3 次，建议人工介入

### Q5：Superpowers 与其他 AI 编程框架（如 Swe-agent、Aider）的关系是什么？

**A**：Superpowers 专注于**工作流和流程规范**，而不是具体的代码生成能力。它与这些工具是互补关系：

- **Swe-agent** 专注于软件工程任务的自动化执行
- **Aider** 专注于代码编辑的交互式体验
- **Superpowers** 专注于建立可靠的、可重复的开发流程

Superpowers 可以作为这些工具的"上层调度层"，为它们提供结构化的开发流程。

### Q6：自定义 Skill 有数量限制吗？

**A**：没有硬性限制。但实践经验表明：

- **3-5 个核心 Skills** 足以覆盖大多数开发场景
- **超过 10 个自定义 Skill** 需要考虑是否过度复杂化
- Skill 的价值在于**复用**，而不是数量

如果发现需要大量自定义 Skills 才能工作，可能说明项目的复杂度已经超出 AI 辅助开发的最佳适用范围。

### Q7：Superpowers 的版本更新频率如何？

**A**：根据 GitHub 仓库信息，当前版本为 **v5.0.6**（2026 年 3 月 25 日发布）。Superpowers 保持了活跃的迭代，建议定期执行更新命令以获取最新功能和修复。

---

## 📋 总结

Superpowers 的核心价值在于：**它不提升 AI 的能力上限，但它提升了 AI 输出的可靠性下限。**

在 AI 编程中，最大的浪费不是 AI 写得慢，而是：

- 写错了方向（需求不清）
- 写了没测试（质量无保障）
- 测了没审查（问题漏到线上）
- 审查后没规范（技术债累积）

Superpowers 通过结构化的 Skills 系统和子代理驱动开发模式，系统性地堵住了这些漏洞。

---

**文档元信息**

- 难度：⭐⭐⭐
- 类型：进阶分析 / 专家设计
- 更新日期：2026-03-28
- 预计阅读时间：30 分钟
