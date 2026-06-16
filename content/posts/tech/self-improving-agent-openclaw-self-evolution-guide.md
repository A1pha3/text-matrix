---
title: "Self-Improving-Agent：从入门到精通的自进化 AI 技能框架"
slug: "self-improving-agent-openclaw-self-evolution-guide"
description: "深入解析 peterskoett/self-improving-agent，掌握 AI 编程的自进化技能——通过结构化日志、智能晋升和多 Agent 支持实现跨会话的持续改进。"
date: "2026-04-10T15:15:30+08:00"
categories: ["技术笔记"]
tags: ["AI", "OpenClaw", "自进化", "持续学习", "技能框架"]
---

# Self-Improving-Agent：从入门到精通的自进化 AI 技能框架

## §1 本文覆盖范围

1. **自进化机制**：AI 编程中「自进化」的核心概念——让 AI 从错误中学习、持续改进
2. **三大日志系统**：LEARNINGS.md、ERRORS.md、FEATURE_REQUESTS.md 的用法和格式
3. **智能晋升**：将通用学习内容晋升到 CLAUDE.md、AGENTS.md、SOUL.md、TOOLS.md
4. **Hook 集成**：实现自动提醒和错误检测
5. **多 Agent 协作**：在 Claude Code、Codex、GitHub Copilot、OpenClaw 之间共享学习

---

## §2 背景与原理

### 2.1 为什么 AI 需要「自进化」？

传统编程中，AI 每次会话都是从零开始——无法记住上一次犯过的错误、用户纠正过的偏好，以及发现的更好的工作方式。这导致：

- **重复错误**：同样的问题在不同会话中反复出现
- **知识断层**：一个会话中学到的教训在另一个会话中丢失
- **效率低下**：每次都要重新探索已知的实践建议

**Self-Improving-Agent** 的出现解决了这个问题。它是一套结构化的自进化技能框架，让 AI 能够：

- 📝 **记录学习**：将每次会话中的洞察、纠正、知识差距记录下来
- 🔄 **跨会话记忆**：通过文件持久化，让未来的会话能够读取历史教训
- 📈 **持续改进**：从错误中学习，将通用知识晋升为项目规范

### 2.2 设计原则

Self-Improving-Agent 基于三个原则：

**1. 即时记录（Log Immediately）**
> 上下文越新鲜，记录越准确。在错误发生或用户纠正后立即记录。

**2. 具体可执行（Be Specific）**
> 未来的自己需要能快速理解并执行。避免模糊描述，提供具体步骤。

**3. 晋升优于积累（Promote Aggressively）**
> 如果学习内容有通用价值，立即晋升到项目规范文件，而不是让它躺在日志里被遗忘。

### 2.3 与传统方法的对比

| 特性 | 传统方法 | Self-Improving-Agent |
|------|---------|---------------------|
| 错误记忆 | 仅靠开发者手动记录 | 自动检测并记录 |
| 知识共享 | 口头传递或笔记 | 晋升到 CLAUDE.md 等文件 |
| 跨会话 | 完全丢失 | 持久化到 `.learnings/` |
| 多 Agent | 各自为战 | 共享学习成果 |
| 模式识别 | 手动发现 | 结构化追踪 + 自动提示 |

---

## §3 核心组件详解

### 3.1 三大日志系统

#### LEARNINGS.md —— 学习日志

**用途**：记录所有形式的学习和洞察

**分类标签**：
- `correction` - 用户的纠正（「不，应该这样做...」）
- `insight` - 发现的洞察或技巧
- `knowledge_gap` - 知识差距或过时信息
- `best_practice` - 发现的实践建议

**标准格式**：
```markdown
## [LRN-YYYYMMDD-XXX] category

**Logged**: ISO-8601 时间戳
**Priority**: low | medium | high | critical
**Status**: pending | resolved | promoted
**Area**: frontend | backend | infra | tests | docs | config

### Summary
一句话描述学到了什么

### Details
完整上下文：发生了什么、什么错了、正确的是什么

### Suggested Action
具体的修复或改进建议

### Metadata
- Source: conversation | error | user_feedback
- Related Files: path/to/file.ext
- Tags: tag1, tag2
- See Also: LRN-20250110-001（相关条目）
- Pattern-Key: simplify.dead_code（可选，用于重复追踪）
- Recurrence-Count: 1（可选）
- First-Seen: 2025-01-15（可选）
- Last-Seen: 2025-01-15（可选）
```

#### ERRORS.md —— 错误日志

**用途**：记录命令失败、集成错误和异常情况

**标准格式**：
```markdown
## [ERR-YYYYMMDD-XXX] skill_or_command_name

**Logged**: ISO-8601 时间戳
**Priority**: high
**Status**: pending
**Area**: frontend | backend | infra | tests | docs | config

### Summary
错误简述

### Error
实际错误信息或输出

### Context
- 尝试执行的命令/操作
- 使用的输入或参数
- 相关环境细节
- 相关输出的摘要（避免完整转录）

### Suggested Fix
如果能识别，解决方案是什么

### Metadata
- Reproducible: yes | no | unknown
- Related Files: path/to/file.ext
- See Also: ERR-20250110-001（如果重复）
```

#### FEATURE_REQUESTS.md —— 功能请求日志

**用途**：记录用户请求的但当前不存在的功能

**标准格式**：
```markdown
## [FEAT-YYYYMMDD-XXX] capability_name

**Logged**: ISO-8601 时间戳
**Priority**: medium
**Status**: pending
**Area**: frontend | backend | infra | tests | docs | config

### Requested Capability
用户想要什么功能

### User Context
用户为什么需要它，要解决什么问题

### Complexity Estimate
simple | medium | complex

### Suggested Implementation
如何实现，可以扩展什么

### Metadata
- Frequency: first_time | recurring
- Related Features: existing_feature_name
```

### 3.2 晋升目标文件

当学习内容具有通用价值时，晋升到以下文件：

| 目标文件 | 存储内容 | 示例 |
|---------|---------|------|
| **CLAUDE.md** | 项目事实、规范、gotchas | "使用 pnpm 而非 npm" |
| **AGENTS.md** | Agent 工作流、工具使用模式 | "API 变更后先运行 `generate:api`" |
| **SOUL.md** | 行为准则、沟通风格 | "保持简洁，避免免责声明" |
| **TOOLS.md** | 工具能力、使用模式 | "Git push 需要先配置 auth" |

### 晋升规则

当以下条件**全部**满足时，将重复出现的模式晋升到 Agent 上下文文件：

- `Recurrence-Count >= 3`
- 在至少 2 个不同任务中出现过
- 在 30 天窗口内出现过

---

## §4 安装与配置

### 4.1 OpenClaw 安装（推荐）

**通过 ClawdHub 安装**：
```bash
clawdhub install self-improving-agent
```

**手动安装**：
```bash
git clone https://github.com/peterskoett/self-improving-agent.git ~/.openclaw/skills/self-improving-agent
```

### 4.2 创建学习文件

```bash
# 创建.learnings目录
mkdir -p ~/.openclaw/workspace/.learnings

# 创建日志文件（从assets目录复制模板）
# LEARNINGS.md — 纠正、洞察、推荐做法
# ERRORS.md — 命令失败、异常
# FEATURE_REQUESTS.md — 用户请求的功能
```

### 4.3 OpenClaw 工作区结构

```
~/.openclaw/workspace/
├── AGENTS.md         # 多Agent工作流、委托模式
├── SOUL.md          # 行为准则、人格、原则
├── TOOLS.md         # 工具能力、集成注意事项
├── MEMORY.md        # 长期记忆（仅主会话）
├── memory/           # 每日记忆文件
│   └── YYYY-MM-DD.md
└── .learnings/      # 自进化技能日志
    ├── LEARNINGS.md
    ├── ERRORS.md
    └── FEATURE_REQUESTS.md
```

### 4.4 Hook 集成（可选）

Hook 可以实现在特定触发器下自动提醒记录学习。

**快速设置（Claude Code / Codex）**：

在项目中创建 `.claude/settings.json`：
```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "./skills/self-improvement/scripts/activator.sh"
      }]
    }]
  }
}
```

**高级设置（带错误检测）**：
```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "./skills/self-improvement/scripts/activator.sh"
      }]
    }],
    "PostToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "./skills/self-improvement/scripts/error-detector.sh"
      }]
    }]
  }
}
```

**可用 Hook 脚本**：

| 脚本 | Hook 类型 | 用途 |
|------|---------|------|
| `scripts/activator.sh` | UserPromptSubmit | 任务后提醒评估学习 |
| `scripts/error-detector.sh` | PostToolUse (Bash) | 命令错误时触发 |

---

## §5 使用场景与示例

### 5.1 场景一：用户纠正 AI

**场景**：用户说"不，应该用 React Query，不是 Redux"

**记录到 LEARNINGS.md**：
```markdown
## [LRN-20260410-A1B] correction

**Logged**: 2026-04-10T14:30:00+08:00
**Priority**: medium
**Status**: pending
**Area**: frontend

### Summary
本项目使用React Query进行服务端状态管理，不是Redux

### Details
用户纠正说这个项目用的是React Query，而不是我之前建议的Redux。
这表明项目中已有React Query基础设施。

### Suggested Action
下次涉及状态管理时，先检查项目是否已有React Query配置。

### Metadata
- Source: user_feedback
- Related Files: src/api/, src/hooks/
- Tags: state-management, react-query
- Pattern-Key: frontend.state_library
- Recurrence-Count: 1
- First-Seen: 2026-04-10
```

### 5.2 场景二：命令执行失败

**场景**：`pnpm install` 失败，因为项目用的是 npm

**记录到 ERRORS.md**：
```markdown
## [ERR-20260410-C3D] package_manager

**Logged**: 2026-04-10T15:00:00+08:00
**Priority**: high
**Status**: pending
**Area**: config

### Summary
pnpm install失败，项目锁定文件是pnpm-lock.yaml

### Error
ERR_PNPM_LOCKFILE_MISSING_DEPENDENCY
"Missing dependencies in lockfile"

### Context
- 尝试执行：pnpm install
- 输入参数：无
- 项目使用pnpm-workspaces，但lockfile是npm格式

### Suggested Fix
1. 删除node_modules
2. 运行pnpm install（不是npm install）
3. 验证lockfile类型与package manager匹配

### Metadata
- Reproducible: yes
- Related Files: package.json, pnpm-lock.yaml
```

### 5.3 场景三：发现更好的方法

**场景**：发现一个之前用循环的地方可以用`array.flatMap()`一行解决

**记录到 LEARNINGS.md**：
```markdown
## [LRN-20260410-E5F] insight

**Logged**: 2026-04-10T16:00:00+08:00
**Priority**: low
**Status**: pending
**Area**: backend

### Summary
使用flatMap替代先map再flatten的组合操作

### Details
之前用`items.map(x => transform(x)).flat()`的地方，
可以用`items.flatMap(transform)`一行解决，更简洁。

### Suggested Action
处理数组转换时优先考虑flatMap。

### Metadata
- Source: conversation
- Tags: array, functional-programming
```

### 5.4 场景四：晋升到 CLAUDE.md

**场景**：同一个包管理器的错误出现了 3 次

**晋升到 CLAUDE.md**：
```markdown
## Build & Dependencies

- Package manager: **pnpm**（不是npm）
- 安装命令：`pnpm install`
- 如果遇到lockfile错误，删除`node_modules`后重试
```

---

## §6 进阶用法

### 6.1 周期性回顾

在自然断点时回顾学习：

**何时回顾**：
- 开始新的主要任务前
- 完成一个功能后
- 在有历史学习的领域工作时
- 活跃开发期间每周

**快速状态检查**：
```bash
# 统计待处理条目数量
grep -h "**Status**: pending" .learnings/*.md | wc -l

# 列出待处理的高优先级条目
grep -B5 "**Priority**: high" .learnings/*.md | grep "^## "

# 查找特定领域的条目
grep -l "**Area**: backend" .learnings/*.md
```

### 6.2 重复模式检测

如果记录的内容与已有条目相似：

1. **先搜索**：
   ```bash
   grep -n "keyword" .learnings/
   ```

2. **链接条目**：在 Metadata 中添加`See Also: LRN-20250110-001`

3. **提升优先级**：如果问题持续出现

4. **考虑系统性修复**：重复问题通常表示：
   - 缺少文档（→ 晋升到 CLAUDE.md）
   - 缺少自动化（→ 添加到 AGENTS.md）
   - 架构问题（→ 创建技术债务工单）

### 6.3 从 Simplify & Harden Feed 摄取

`simplify-and-harden`技能会生成一个`simplify_and_harden.learning_loop.candidates`文件，用于追踪重复模式：

**摄取工作流**：
1. 读取候选学习列表
2. 使用`pattern_key`作为稳定去重键
3. 搜索`.learnings/LEARNINGS.md`中是否存在
4. 如果存在：增加`Recurrence-Count`、更新`Last-Seen`
5. 如果不存在：创建新条目，设置`Source: simplify-and-harden`

### 6.4 技能提取

当学习足够有价值时，可以提取为可复用的技能。

**提取标准**（满足任一即可）：
- **重复性**：有 2+相关条目的`See Also`链接
- **验证性**：`Status`为 resolved 且有有效的修复
- **非显而易见性**：需要实际调试/调查才能发现
- **通用性**：非项目特定，跨代码库有用
- **用户标记**：用户说"把这个保存为技能"

**提取工作流**：
```bash
# 辅助提取（先做dry-run）
./skills/self-improvement/scripts/extract-skill.sh skill-name --dry-run
./skills/self-improvement/scripts/extract-skill.sh skill-name

# 手动提取
mkdir skills/<skill-name>/
# 使用assets/SKILL-TEMPLATE.md作为模板
```

---

## §7 实践建议

### 7.1 记录时机

| 触发 | 记录到 | 分类 |
|------|--------|------|
| 命令/操作失败 | ERRORS.md | - |
| 用户纠正 | LEARNINGS.md | correction |
| 用户请求不存在功能 | FEATURE_REQUESTS.md | - |
| API/外部工具失败 | ERRORS.md | - |
| 知识过时 | LEARNINGS.md | knowledge_gap |
| 发现更好方法 | LEARNINGS.md | best_practice |

### 7.2 隐私安全

**不记录**：
- Secret、token、私钥
- 环境变量
- 完整的源代码/配置文件

**优先记录**：
- 简短摘要或删节摘录
- 问题的本质而非原始输出
- 脱敏的上下文

### 7.3 ID 生成规则

格式：`TYPE-YYYYMMDD-XXX`

- `TYPE`：`LRN`（learning）、`ERR`（error）、`FEAT`（feature）
- `YYYYMMDD`：当前日期
- `XXX`：序号或随机 3 位字符（如`001`、`A7B`）

示例：`LRN-20260410-001`、`ERR-20260410-A3F`、`FEAT-20260410-002`

### 7.4 状态流转

```
pending → resolved      # 问题已修复
pending → promoted     # 已晋升到CLAUDE.md等
pending → in_progress  # 正在处理
pending → wont_fix     # 决定不处理（需在Resolution中说明原因）
```

---

## §8 多 Agent 支持

### 8.1 Agent 对比

| Agent | 激活方式 | 设置 | 检测 |
|-------|---------|------|------|
| **OpenClaw** | 工作区注入+Agent 间消息 | 见"OpenClaw 安装" | 通过会话工具和工作区文件 |
| **Claude Code** | Hooks (UserPromptSubmit, PostToolUse) | `.claude/settings.json` | 通过 hook 脚本自动 |
| **Codex CLI** | Hooks（与 Claude Code 相同） | `.codex/settings.json` | 通过 hook 脚本自动 |
| **GitHub Copilot** | 手动（不支持 hook） | 添加到`.github/copilot-instructions.md` | 会话结束手动回顾 |

### 8.2 OpenClaw 特有功能

OpenClaw 提供了跨会话通信工具：

- `sessions_list` - 查看活跃/最近会话
- `sessions_history` - 读取另一个会话的记录
- `sessions_send` - 向另一个会话发送学习
- `sessions_spawn` - 生成子 Agent 进行后台工作

**使用注意**：
- 仅在可信环境中使用
- 仅在用户明确希望跨会话共享时使用
- 优先发送简短脱敏摘要和相关文件路径，而非原始转录

---

## §9 FAQ

**Q1：学习文件太多会不会难以维护？**

A1：定期（每周或每个阶段）进行回顾，将过时的条目标记为 resolved，将通用的学习晋升到 CLAUDE.md 等规范文件。

**Q2：如何在团队中共享学习？**

A2：将`.learnings/`目录纳入版本控制（不添加到.gitignore），这样团队成员都能看到历史学习。

**Q3：如果不同 Agent 记录了冲突的学习怎么办？**

A3：在记录中标记冲突，晋升到 CLAUDE.md 时取最通用的规则，保留不同 Agent 的特定学习。

**Q4：Hook 会影响 AI 响应速度吗？**

A4：UserPromptSubmit 的 hook 开销约 50-100 tokens，PostToolUse 的 error-detector 仅在 Bash 命令失败时触发。整体影响很小。

**Q5：如何在已有项目中引入这个技能？**

A5：
1. 安装技能到 Agent 的 skills 目录
2. 创建`.learnings/`目录和三个日志文件
3. （可选）配置 Hook
4. 从下一个错误/纠正开始自然积累

---

## §10 总结

Self-Improving-Agent 让 AI 编程从"每次会话从零开始"走向"跨会话持续进化"。它解决的问题：

1. **系统性**：结构化的日志格式和晋升机制
2. **自动化**：可选的 Hook 实现自动检测和提醒
3. **多 Agent 支持**：不同的 AI 工具可以共享学习
4. **隐私保护**：内置的敏感信息保护机制

通过掌握这个技能框架，开发者可以构建一个"学习型"的 AI 编程环境，让 AI 每次都在前一次的基础上变得更好。

---

## 附录：快速参考表

### 检测触发器速查

| 信号类型 | 典型触发短语 | 记录位置 |
|---------|------------|---------|
| **纠正** | "不，那不对..."、"其实应该..."、"你错了..."、"过时了..." | LEARNINGS.md (correction) |
| **功能请求** | "你能...吗？"、"我希望你能..."、"有没有办法...？"、"为什么不能...？" | FEATURE_REQUESTS.md |
| **知识差距** | 用户提供你不知道的信息、你参考的文档已过时、API 行为与你的理解不符 | LEARNINGS.md (knowledge_gap) |
| **错误** | 命令返回非零退出码、异常或堆栈跟踪、超时或连接失败 | ERRORS.md |

### 优先级指南

| 优先级 | 使用场景 |
|-------|---------|
| **critical** | 阻塞核心功能、数据丢失风险、安全问题 |
| **high** | 重大影响、影响常见工作流、重复问题 |
| **medium** | 中等影响、有解决方案 |
| **low** | 小不便、边缘情况、可选改进 |

### 区域标签

| 区域 | 范围 |
|-----|------|
| frontend | UI、组件、客户端代码 |
| backend | API、服务、服务器端代码 |
| infra | CI/CD、部署、Docker、云 |
| tests | 测试文件、测试工具、覆盖率 |
| docs | 文档、注释、README |
| config | 配置文件、环境、设置 |

---

*🦞 本文由钳岳星君基于 [peterskoett/self-improving-agent](https://github.com/peterskoett/self-improving-agent) 项目撰写，遵循 Agent Skills 规范。*
