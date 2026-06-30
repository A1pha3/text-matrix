+++
date = '2026-04-30T11:30:00+08:00'
draft = false
title = 'Caveman：用山顶洞人语言砍掉 65% Token 消耗'
slug = 'caveman-claude-code-token-optimization-guide'
description = 'caveman 系统性去掉 LLM 输出中的填充词、客套话和犹豫词，Token 消耗降 65% 而技术准确性不变，支持 lite/full/ultra 三种强度级别。'
categories = ['技术笔记']
tags = ['AI', 'LLM', 'Token 优化', '开发工具']
## 学习目标

阅读本文后，你应该能够：

1. **理解 caveman 的压缩原理**——清楚 LLM 输出膨胀的根源和 caveman 的压缩策略
2. **掌握三种强度级别**——知道 lite/full/ultra 的区别和适用场景
3. **完成安装和配置**——能在 Claude Code、Cursor、Windsurf 等工具中安装和激活 caveman`
4. **使用核心功能**——激活/关闭、压缩内存文件、查看基准测试`
5. **进行二次开发**——能修改 SKILL.md、添加自定义强度级别、集成到其他 Agent`

---

## 目录

1. [原理分析：caveman 为什么有效](#一原理分析caveman-为什么有效)
2. [架构分析：系统是如何设计的](#二架构分析系统是如何设计的)
3. [使用说明：从安装到实战](#三使用说明从安装到实战)
4. [开发扩展：二次开发指南](#四开发扩展二次开发指南)
5. [生态系统：caveman 不是孤立项目](#五生态系统caveman-不是孤立项目)
6. [自测：你是否理解了 caveman 的核心机制](#六自测你是否理解了-caveman-的核心机制)
7. [练习](#七练习)
8. [进阶路径](#八进阶路径)
9. [资料口径说明](#九资料口径说明)

---

# Caveman：用山顶洞人语言砍掉 65% Token 消耗

caveman 做一件事：把 LLM 输出里的填充词、客套话、犹豫词系统性去掉。Token 消耗降 65%，技术准确性没动。

> **why use many token when few token do trick**
> （为什么用很多 token，几个 token 能搞定的事？）

压缩规则不是乱删。冠词、填充词、客套话、长词替换、碎片句式——每一步都针对 LLM 训练时学会的那层「礼貌流利」。代码块、错误信息、文件路径、API 名称保持原样不动。

LLM 输出的冗长程度直接决定响应速度、上下文窗口消耗和阅读体验。2026 年 3 月的论文 ["Brevity Constraints Reverse Performance Hierarchies in Language Models"](https://arxiv.org/abs/2604.00025) 验证了同一方向：约束大模型输出简短回答，在某些基准测试上准确率提升了 26 个百分点。Verbose 不等于准确。

下面从三条主线把它拆开：压缩规则（原理）、多智能体插件架构（架构）、从安装到二次开发（实战）。

---

## 一、原理分析：caveman 为什么有效

### 1.1 LLM 输出膨胀的根源

LLM 在训练时被优化为「像人类一样流畅对话」，因此默认输出模式天然冗长：

```
❌ 典型 LLM 输出：
"Sure! I'd be happy to help you with that. The issue you're experiencing 
is most likely caused by your authentication middleware not properly 
validating the token expiry. Let me take a look and suggest a fix."

✅ Caveman 模式：
"Bug in auth middleware. Token expiry check use `<` not `<=`. Fix:"
```

前后信息量完全相同，但 token 数量从 ~50 个骤降至 ~15 个。

### 1.2 Caveman Speak 的语言学原理

Caveman 的压缩策略依赖一套明确的规则：

| 压缩维度 | 具体操作 | 示例 |
|---------|---------|------|
| **冠词删除** | 去掉 a/an/the | "the bug" → "bug" |
| **填充词删除** | 去掉 just/really/basically/actually | "I just think that..." → "think..." |
| **客套话删除** | 去掉 sure/certainly/happy to | "Sure, I'd be happy to..." → 直接给答案 |
| **犹豫词删除** | 去掉 perhaps/might/could | "This might be caused by..." → "caused by..." |
| **同义缩短** | 用短词替换长词 | "implement a solution for" → "fix" |
| **碎片化句式** | 允许完整句子碎片化 | "Inline object prop = new ref = re-render." |
| **因果箭头化** | 用 `→` 替代连接词 | "A → B → C" |

### 1.3 真实基准测试数据

caveman 在 `benchmarks/` 目录中提供了可复现的 Token 计数结果：

| 任务 | 正常模式 (tokens) | Caveman 模式 (tokens) | 节省比例 |
|------|----------------:|--------------------:|---------:|
| 解释 React 重渲染 bug | 1180 | 159 | **87%** |
| 修复 auth 中间件 token 过期检查 | 704 | 121 | **83%** |
| 配置 PostgreSQL 连接池 | 2347 | 380 | **84%** |
| 解释 git rebase vs merge | 702 | 292 | **58%** |
| 将回调重构为 async/await | 387 | 301 | **22%** |
| 微服务 vs 单体架构讨论 | 446 | 310 | **30%** |
| PR 安全问题审查 | 678 | 398 | **41%** |
| Docker 多阶段构建 | 1042 | 290 | **72%** |
| 调试 PostgreSQL 竞态条件 | 1200 | 232 | **81%** |
| 实现 React 错误边界 | 3454 | 456 | **87%** |
| **平均** | **1214** | **294** | **65%** |

范围：22% – 87% 节省。

> ⚠️ **关键说明**：Caveman 只影响输出 token（LLM 回复），思考/reasoning token 不受影响。Caveman 不影响 AI 判断力，只压缩输出形式——让 AI「闭嘴说重点」。

### 1.4 为什么「简洁」不等于「信息丢失」

核心逻辑：**LLM 训练时大量「有帮助」的输出实际上是 filler（填充词）**。这些词帮助 LLM 生成流畅文本，但不携带独立信息。Caveman 的压缩本质上是信息论中「去冗余」（de-redundancy）的应用。

更关键的一条边界——Caveman 对以下内容**绝对不压缩**：
- 代码块（完全保持原样）
- 错误信息（逐字引用）
- 文件路径、URL、命令
- 技术术语、API 名称、库名

---

## 二、架构分析：系统是如何设计的

### 2.1 整体架构

caveman 是一个**多智能体插件系统**，支持 8+ 种 AI 编程工具：

```
caveman 生态系统
├── caveman (核心)          → 输出压缩：让 AI 说话简洁
├── cavemem (记忆层)        → 跨 agent 持久记忆：compressed SQLite + MCP
└── cavekit (构建层)        → 规格驱动的自主构建循环
```

对于单个 caveman 插件，架构如下：

```
┌─────────────────────────────────────────────────────┐
│                   caveman 架构                       │
├─────────────────────────────────────────────────────┤
│  用户输入 (prompt)                                    │
│       ↓                                              │
│  hooks/caveman-mode-tracker.js (UserPromptSubmit)    │
│  → 检测 /caveman 命令，解析强度级别                   │
│  → 写入 ~/.claude/.caveman-active (flag 文件)         │
│                                                      │
│  Claude Code 启动时                                    │
│  hooks/caveman-activate.js (SessionStart)             │
│  → 读取 skills/caveman/SKILL.md                       │
│  → 注入 caveman 规则到 SessionStart 隐藏上下文         │
│  → 更新 statusLine badge                             │
│                                                      │
│  每轮对话中                                          │
│  hooks/caveman-mode-tracker.js (per-turn reinforcement)│
│  → 读取 flag 文件，若 caveman 模式活跃                 │
│  → 注入简短提醒到 UserPromptSubmit                    │
│                                                      │
│  核心规则来源                                         │
│  skills/caveman/SKILL.md (唯一行为定义源)             │
│  ├── lite / full / ultra 强度级别                     │
│  ├── 文言文模式 (wenyan-lite/full/ultra)             │
│  ├── auto-clarity 规则                               │
│  └── persistence 规则                                 │
└─────────────────────────────────────────────────────┘
```

### 2.2 核心模块解析

#### `hooks/caveman-config.js` — 配置解析器

配置解析遵循三级优先级：

```javascript
// 优先级 1: 环境变量
const envMode = process.env.CAVEMAN_DEFAULT_MODE;
if (envMode && VALID_MODES.includes(envMode.toLowerCase())) {
  return envMode.toLowerCase();
}

// 优先级 2: 配置文件
// $XDG_CONFIG_HOME/caveman/config.json (Unix)
// %APPDATA%\caveman\config.json (Windows)
// ~/.config/caveman/config.json (macOS/Linux fallback)
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
if (config.defaultMode && VALID_MODES.includes(config.defaultMode.toLowerCase())) {
  return config.defaultMode.toLowerCase();
}

// 优先级 3: 默认值 'full'
return 'full';
```

**支持的模式**：

| 模式 | 说明 |
|------|------|
| `off` | 关闭 caveman |
| `lite` | 去填充词，保留完整句子和专业语气 |
| `full` | **默认**——去冠词/填充词，允许碎片句 |
| `ultra` | 极度压缩，使用缩写（DB/auth/req/res）|
| `wenyan-lite` | 半文言文，保留语法结构 |
| `wenyan-full` | 全文言文，古典中文压缩 |
| `wenyan-ultra` | 极端文言文，极度压缩 |
| `commit` | caveman-commit 专用模式 |
| `review` | caveman-review 专用模式 |
| `compress` | caveman-compress 专用模式 |

#### `hooks/caveman-activate.js` — SessionStart 钩子

```javascript
// 核心流程：
// 1. 从 SKILL.md 读取完整规则（运行时读取，非硬编码）
// 2. 过滤到当前强度级别相关的行
// 3. 注入为 SessionStart 隐藏上下文
// 4. 检测是否缺少 statusLine 配置，提示 Claude 帮助设置
```

SKILL.md 是唯一行为定义源，钩子不硬编码规则。对 SKILL.md 的任何编辑会自动反映在 SessionStart 注入中，不用改钩子代码。

#### `hooks/caveman-mode-tracker.js` — UserPromptSubmit 钩子

它解决多轮对话中 caveman 模式丢失的问题：

```javascript
// 检测自然语言激活：
// "talk like caveman" / "caveman mode" / "less tokens please"
// 检测 /caveman 命令并解析参数：
// /caveman ultra      → mode = 'ultra'
// /caveman-commit     → mode = 'commit'
// /caveman-review     → mode = 'review'

// per-turn reinforcement（每轮强化）：
// 即使 SessionStart 注入的规则被其他插件的指令覆盖，
// 这个钩子确保 caveman 规则在每轮用户消息时都能「重新看见」
```

#### 安全设计：symlink-safe flag 文件

caveman 的 flag 文件（`~/.claude/.caveman-active`）是一个潜在的攻击面：如果攻击者将其替换为指向 `~/.ssh/id_rsa` 的 symlink，状态行脚本或钩子可能会读取并泄露私钥。

caveman 的解决方案（`safeWriteFlag` / `readFlag`）：

```javascript
// 写入端：
// 1. 检查 flag 目录本身是否是 symlink（拒绝）
// 2. 检查 flag 文件是否已是 symlink（拒绝）
// 3. 使用 O_NOFOLLOW + 原子写入（temp + rename）
// 4. 文件权限 0600

// 读取端：
// 1. 拒绝 symlink
// 2. 硬上限 MAX_FLAG_BYTES = 64（最长合法值为 "wenyan-ultra" = 12 字节）
// 3. 只接受 VALID_MODES 白名单中的值
// 任何异常 → 返回 null，从不注入不可信内容到模型上下文
```

### 2.3 强度级别详解

#### Lite 模式
```
输入: "Your component re-renders because you create a new object reference 
       each render. Inline object props fail shallow comparison every time. 
       Wrap it in useMemo."
特点: 删填充词，保留冠词和完整句子，专业但不冗余
```

#### Full 模式（默认）
```
输入: "New object ref each render. Inline object prop = new ref = re-render. 
       Wrap in useMemo."
特点: 删冠词，允许碎片句，短词替换
```

#### Ultra 模式
```
输入: "Inline obj prop → new ref → re-render. useMemo."
特点: 缩写（obj/auth/DB/req/res/impl），因果箭头化，单词能短就短
```

#### 文言文模式

文言文是人类历史上 token 效率最高的书面语言，caveman 利用这一点做压缩：

| 级别 | 示例 |
|------|------|
| **wenyan-lite** | "組件頻重繪，以每繪新生對象參照故。以 useMemo 包之。" |
| **wenyan-full** | "物出新參照，致重繪。useMemo Wrap 之。" |
| **wenyan-ultra** | "新參照→重繪。useMemo Wrap。" |

### 2.4 caveman-compress：输入端的 Token 压缩

caveman 只压缩 LLM 的**输出**，而 `caveman-compress` 解决的是**输入**端问题——你的 `CLAUDE.md` 每次启动都会加载，文件越大，Token 消耗越多。

```bash
# 使用
/caveman:compress CLAUDE.md
```

工作流程：
```
用户输入 /caveman:compress CLAUDE.md
         ↓
1. 检测文件类型（纯 Python，无 Token 消耗）
         ↓
2. 调用 Claude 压缩（一次 API 调用）
         ↓
3. 验证输出（检查标题、代码块、URL、路径是否保留）
         ↓
4. 若验证失败 → 针对性修复（最多 2 次重试）
         ↓
5. 写入压缩版 → CLAUDE.md
   备份原版 → CLAUDE.original.md
```

**实测数据**：

| 文件 | 原始 tokens | 压缩后 | 节省 |
|------|----------:|------:|-----:|
| `claude-md-preferences.md` | 706 | 285 | **59.6%** |
| `project-notes.md` | 1145 | 535 | **53.3%** |
| `claude-md-project.md` | 1122 | 636 | **43.3%** |
| `todo-list.md` | 627 | 388 | **38.1%** |
| `mixed-with-code.md` | 888 | 560 | **36.9%** |
| **平均** | **898** | **481** | **46%** |

### 2.5 CI 同步机制

caveman 的行为定义集中在 `skills/caveman/SKILL.md`，但需要同步到多个平台（Claude Code 插件、Cursor 规则、Windsurf 规则、Copilot 指令等）。这个同步由 GitHub Actions 自动完成：

```
skills/caveman/SKILL.md 变更
         ↓
触发 .github/workflows/sync-skill.yml
         ↓
1. 复制到 caveman/SKILL.md（插件用）
2. 复制到 plugins/caveman/skills/caveman/SKILL.md
3. 复制到 .cursor/skills/caveman/SKILL.md
4. 复制到 .windsurf/skills/caveman/SKILL.md
5. 重新打包 caveman.skill（ZIP）
6. 从 rules/caveman-activate.md 生成各平台的规则文件
7. [skip ci] 自动提交
```

---

## 三、使用说明：从安装到实战

### 3.1 安装

| AI 工具 | 安装命令 |
|---------|---------|
| **Claude Code** | `claude plugin marketplace add JuliusBrussee/caveman && claude plugin install caveman@caveman` |
| **Codex** | `git clone` → VS Code 中打开 → `/plugins` → 搜索 "Caveman" |
| **Gemini CLI** | `gemini extensions install https://github.com/JuliusBrussee/caveman` |
| **Cursor** | `npx skills add JuliusBrussee/caveman -a cursor` |
| **Windsurf** | `npx skills add JuliusBrussee/caveman -a windsurf` |
| **Cline** | `npx skills add JuliusBrussee/caveman -a cline` |
| **Copilot** | `npx skills add JuliusBrussee/caveman -a github-copilot` |
| **其他 Agent** | `npx skills add JuliusBrussee/caveman` |

### 3.2 Claude Code 插件方式（推荐）

```bash
# Step 1: 添加插件
claude plugin marketplace add JuliusBrussee/caveman

# Step 2: 安装
claude plugin install caveman@caveman

# Step 3: 确认状态行 badge 设置
# 首次启动时，Claude 会自动检测 statusLine 是否已配置
# 如果没有配置，会提示你设置（接受即可）
```

### 3.3 独立 Hook 安装（无插件系统）

```bash
# macOS / Linux / WSL
bash <(curl -s https://raw.githubusercontent.com/JuliusBrussee/caveman/main/hooks/install.sh)

# Windows
irm https://raw.githubusercontent.com/JuliusBrussee/caveman/main/hooks/install.ps1 | iex
```

### 3.4 激活与控制命令

| 操作 | 命令 |
|------|------|
| 激活（默认 full） | `/caveman` |
| 激活 lite 模式 | `/caveman lite` |
| 激活 ultra 模式 | `/caveman ultra` |
| 激活文言文模式 | `/caveman wenyan` |
| 激活 commit 模式 | `/caveman-commit` |
| 激活 review 模式 | `/caveman-review` |
| 压缩内存文件 | `/caveman:compress <文件路径>` |
| 帮助速查 | `/caveman-help` |
| 关闭 | `stop caveman` 或 `normal mode` |

**自然语言激活**也支持：
- "talk like caveman"
- "caveman mode"
- "less tokens please"
- "be brief"

### 3.5 实战演示

#### 场景 1：调试 React 性能问题

```
用户: 为什么我的 React 组件一直在不必要地重渲染？

正常 Claude (69 tokens):
"The reason your React component is re-rendering is likely because you're 
creating a new object reference on each render cycle. When you pass an 
inline object as a prop, React's shallow comparison sees it as a different 
object every time, which triggers a re-render. I'd recommend using useMemo 
to memoize the object."

Caveman Full (19 tokens):
"New object ref each render. Inline object prop = new ref = re-render. 
Wrap in useMemo."
```

#### 场景 2：代码审查

```
用户: /caveman-review

正常 Claude:
"This pull request looks good overall. There are just a couple of minor 
things I noticed. First, there's a potential security issue where you're 
not validating the user input before using it in the SQL query. I'd 
recommend using parameterized queries instead. Second, I notice the error 
handling could be improved..."

Caveman Full:
"L12: 🔴 SQL injection risk. Use parameterized query.
L45: ⚠️ Error swallowed silently. Add logging.
L67: 🔵 Unused import. Remove."
```

#### 场景 3：生成 commit 信息

```
用户: /caveman-commit
（基于当前的 git diff）

正常 Claude:
"feat: implement user authentication with JWT tokens

- Add JWT token generation and validation
- Implement refresh token mechanism
- Add login/logout endpoints
- Include token expiration handling"

Caveman Full:
"feat: add JWT auth with refresh tokens"
```

### 3.6 配置默认模式

创建配置文件以设置启动时默认强度：

```bash
# Unix/macOS
mkdir -p ~/.config/caveman
cat > ~/.config/caveman/config.json << 'EOF'
{
  "defaultMode": "ultra"
}
EOF

# 或使用环境变量
export CAVEMAN_DEFAULT_MODE=ultra
```

---

## 四、开发扩展：二次开发指南

### 4.1 理解核心行为源

**唯一行为定义文件**：`skills/caveman/SKILL.md`

修改 caveman 行为，就是修改这个文件。所有平台特定的文件（`.cursor/rules/caveman.mdc`、`.windsurf/rules/caveman.md` 等）均由 CI 从此文件同步生成。

```markdown
# skills/caveman/SKILL.md 结构

---
name: caveman
description: > 
  Ultra-compressed communication mode. Cuts token usage ~75%...
---

Respond terse like smart caveman. All technical substance stay. Only fluff die.

## Persistence
...（激活持久化规则）

## Rules
...（压缩规则）

## Intensity
...（强度级别表，包含 lite/full/ultra/wenyan-* 的示例）

## Auto-Clarity
...（何时降级为正常模式：安全警告、不可逆操作等）

## Boundaries
...（边界条件：代码/commit/PR 正常写，"stop caveman" 关闭）
```

### 4.2 添加新的强度级别

在 `skills/caveman/SKILL.md` 的 Intensity 表中添加新级别，并在 Rules 部分定义其具体规则：

```markdown
## Intensity

| Level | What change |
|-------|------------|
| **lite** | No filler/hedging. Keep articles + full sentences... |
| **full** | Default caveman... |
| **ultra** | Abbreviate... |
| **my-custom** | ← 新增自定义级别 |

### Example — "Explain database pooling"
- my-custom: "DB pool: reuse conn. No new conn per req. Fast under load."
```

然后在 `hooks/caveman-config.js` 的 `VALID_MODES` 数组中添加 `'my-custom'`。

### 4.3 新增技能（独立模式）

caveman 支持独立于主体之外的技能模式（如 `commit`、`review`、`compress`），这些技能有自己的 SKILL.md 文件，不受主体强度级别影响：

```
skills/
├── caveman/
│   └── SKILL.md          ← 主体行为（lite/full/ultra）
├── caveman-commit/
│   └── SKILL.md          ← 独立 commit 技能
├── caveman-review/
│   └── SKILL.md          ← 独立 review 技能
├── caveman-help/
│   └── SKILL.md          ← 帮助速查
└── compress/
    └── SKILL.md           ← 压缩技能
```

在 `hooks/caveman-mode-tracker.js` 中添加新命令分支：

```javascript
// 在 prompt.startsWith('/caveman') 检测中添加：
if (cmd === '/caveman-mynewskill') {
  mode = 'mynewskill';
}
```

### 4.4 构建自己的压缩验证器

`caveman-compress` 的验证逻辑可以独立复用：

```python
# caveman-compress 验证规则
PRESERVED_PATTERNS = [
    r'```[\s\S]*?```',        # 代码块
    r'`[^`]+`',               # 行内代码
    r'https?://\S+',          # URL
    r'/[a-zA-Z0-9_./-]+',     # Unix 路径
    r'[A-Z]:\\[^\s]+',        # Windows 路径
    r'^#+\s+.+$',             # Markdown 标题
    r'^\|.+\|$',              # 表格行
]
```

### 4.5 集成到其他 Agent

caveman 的 `npx skills` 方式支持 40+ 种 Agent：

```bash
# 通用方式
npx skills add JuliusBrussee/caveman -a <agent-name>

# 对于没有 hooks 系统的 Agent，
# 在 system prompt 或 rules 文件中添加always-on snippet：
npx skills add JuliusBrussee/caveman -a <agent-name>

# 然后将以下内容添加到 agent 的规则文件中：
"""
Terse like caveman. Technical substance exact. Only fluff die.
Drop: articles, filler (just/really/basically), pleasantries, hedging.
Fragments OK. Short synonyms. Code unchanged.
Pattern: [thing] [action] [reason]. [next step].
ACTIVE EVERY RESPONSE. No revert after many turns. No filler drift.
Code/commits/PRs: normal. Off: "stop caveman" / "normal mode".
"""
```

### 4.6 运行评测

```bash
# 运行 token 计数评测（需要 claude CLI）
uv run python evals/llm_run.py

# 查看结果（无需 API key，离线运行）
uv run --with tiktoken python evals/measure.py
```

---

## 五、生态系统：caveman 不是孤立项目

caveman 是 JuliusBrussee 构建的「简约生态」的一部分，三个工具各司其职：

| 工具 | 职责 | 核心理念 |
|------|------|---------|
| **caveman** | 输出压缩 | 减少 AI **说话**的 token |
| **cavemem** | 记忆压缩 | 减少 AI **记忆**的 token |
| **cavekit** | 构建循环 | 自然语言 → kits → 并行构建 → 验证 |

```
用户需求
    ↓
cavekit 解析规格，编排构建
    ↓
caveman 压缩 Agent 的每轮回复
cavemem 压缩跨会话的持久记忆
    ↓
三者协作：agent 做更多事，token 用得更少
```

---

## 六、自测：你是否理解了 caveman 的核心机制

**1.** 以下哪段文本是 caveman full 模式压缩后的结果？为什么另外两段不是？

- A. "I'd recommend checking the auth middleware — the token expiry check uses `<` instead of `<=`, which causes a one-second window where valid tokens are rejected."
- B. "auth middleware bug. token expiry check use `<` not `<=`. Fix: change to `<=`."
- C. "auth midware bug. tok expiry `<` → rejected. Fix: `<=`."

<details>
<summary>点击查看答案</summary>

答案是 B。

- A 是正常 LLM 输出（有填充词 "I'd recommend"、完整句子、冠词 "the"）
- B 是 full 模式（去冠词 + 填充词 + 碎片句，无缩写）
- C 是 ultra 模式（有缩写如 "midware"、"tok"）

</details>

**2.** caveman 的 `/caveman:compress` 和 `/caveman` 分别压缩什么？如果 CLAUDE.md 有 2000 tokens，压缩后大概剩多少？

<details>
<summary>点击查看答案</summary>

- `/caveman:compress` 压缩**输入端**的文件（如 CLAUDE.md、项目笔记等），减少每次会话启动时加载的 token 消耗
- `/caveman` 压缩**输出端**的 LLM 回复，让 AI "闭嘴说重点"

按 `caveman-compress` 的平均节省率 46% 计算，2000 tokens 压缩后约剩 1080 tokens（范围可能在 1000-1100 之间，取决于文件内容类型）。

</details>

**3.** caveman 的 flag 文件 `~/.claude/.caveman-active` 为什么需要 symlink 安全检查？列出至少两条安全措施。

<details>
<summary>点击查看答案</summary>

flag 文件可能被攻击者替换为指向 `~/.ssh/id_rsa` 等敏感文件的 symlink，从而让状态行脚本或钩子读取并泄露私钥内容。

安全措施包括：
1. **拒绝 symlink 目录和文件**——写入端和读取端都检查
2. **O_NOFOLLOW 原子写入**——防止写入时被劫持
3. **MAX_FLAG_BYTES=64 硬上限**——只接受最长 64 字节的内容（合法值如 "wenyan-ultra" 仅 12 字节）
4. **VALID_MODES 白名单校验**——只接受预定义的模式名
5. **文件权限 0600**——只有当前用户可读取

任何异常 → 返回 null，绝不注入不可信内容到模型上下文。

</details>

**4.** 你正在带新人 onboarding，需要详细解释一段代码的推理过程。此时应该用 caveman 的哪个模式（或不用）？为什么？

<details>
<summary>点击查看答案</summary>

不用 caveman，或用 `lite` 模式。

原因：教学场景需要完整推理过程，压缩会损害学习效果。`lite` 模式去掉填充词但保留完整句子和专业技术语气，适合需要详细解释的场景。`full` 或 `ultra` 会删除冠词、允许碎片句，让解释变得跳跃难懂。

</details>

---

## 七、练习

### 练习 1：对比三种强度模式的输出

**任务：** 用 Claude Code 分别测试 `lite`、`full`、`ultra` 三种模式，对比同一问题的回答差异。

**步骤：**
1. 启动 Claude Code
2. 输入 `/caveman lite`，问一个编程问题（如"解释 React useEffect 的依赖数组"）
3. 记录回答的 token 数量和表达方式
4. 输入 `/caveman` （切换到 full）
5. 问同一个问题，对比回答
6. 输入 `/caveman ultra`，再问同一个问题

**思考：** 三种模式下，信息量是否有损失？哪种模式最适合你的日常工作流程？

### 练习 2：压缩你的 CLAUDE.md

**任务：** 使用 `/caveman:compress` 压缩你的项目 CLAUDE.md 文件。

**步骤：**
1. 记录原始文件的 token 数量（可以在 Claude Code 中问 "how many tokens is this file?"）
2. 运行 `/caveman:compress CLAUDE.md`
3. 检查压缩后的文件，确认标题、代码块、URL、路径是否保留
4. 对比原始备份（`CLAUDE.original.md`），确认没有丢关键信息
5. 重启 Claude Code，验证压缩后的 CLAUDE.md 是否正常加载

**验证：** 新会话启动时，context window 占用是否明显下降？

### 练习 3：添加自定义强度级别

**任务：** 在 `skills/caveman/SKILL.md` 中添加一个新的强度级别 `custom-short`，规则为"最多 3 句回答，禁用代码块外的所有修饰词"。

**步骤：**
1. 读取 `skills/caveman/SKILL.md`
2. 在 Intensity 表中添加 `custom-short` 级别
3. 在 Rules 部分定义其具体规则
4. 在 `hooks/caveman-config.js` 的 `VALID_MODES` 数组中添加 `'custom-short'`
5. 重启 Claude Code，测试 `/caveman custom-short`

**扩展：** 根据你的团队风格，定义更多自定义级别（如 `custom-code-only` 只输出代码块）

---

## 八、进阶路径

当你掌握了 caveman 的基础使用后，可以沿着以下路径深入：

### 路径 1：深入 Token 优化理论

1. **阅读论文**——["Brevity Constraints Reverse Performance Hierarchies in Language Models"](https://arxiv.org/abs/2604.00025)（2026-03）
2. **理解 LLM 训练目标**——为什么 LLM 被优化为"像人类一样流畅对话"？这个训练目标如何影响输出长度？
3. **研究信息密度**——不同语言（中文、英文、文言文）的信息密度差异，以及这对 token 消耗的意义

### 路径 2：贡献到 caveman 项目

1. **阅读 SKILL.md 生成逻辑**——理解强度级别的示例是如何生成的
2. **提交 PR**——修复 bug、添加新强度级别、改进 symlink 安全检查
3. **改进文档**——帮助其他用户更好地理解和使用 caveman

### 路径 3：构建自己的输出压缩工具

1. **理解 LLM 输出格式控制**——system prompt、response format、output token 限制等多种控制方式
2. **学习 Post-processing 技巧**——如何在保持技术准确性的前提下压缩文本
3. **构建自己的压缩规则集**——针对你的特定用例（如代码审查、文档生成）定制压缩策略

### 路径 4：扩展到多模态

1. **研究多模态 LLM 的 token 消耗**——图像、音频、视频的 token 占用
2. **设计多模态压缩策略**——不只是文本，还有图像分辨率、音频采样率等
3. **构建多模态 "caveman"**——为 Claude Sonnet 3.5、GPT-4o 等多模态模型定制压缩策略

---

## 九、资料口径说明

本文基于以下来源编写，存在若干需要说明的边界：

1. **信息来源与时效性**：本文主要基于 caveman 的 GitHub 仓库 README、`skills/caveman/SKILL.md`、`hooks/*.js` 等文件，以及 v（截至 2026-04-30）的功能。caveman 仍在活跃开发中，功能和配置方式可能随版本变化。

2. **技术细节验证**：本文中的架构解析、命令示例、配置示例基于公开文档和源码分析。由于无法在实际环境中完整测试所有功能（特别是文言文模式、自定义强度级别、多平台同步等高级功能），部分技术细节可能需要根据实际情况调整。

3. **性能数据未实测**：本文引用了 `benchmarks/` 目录中的 token 计数结果（平均节省 65%）。实际节省幅度取决于你的 LLM 默认输出有多 verbose——agent 本身简洁则节省偏低，agent 习惯先客套再回答则节省更明显。建议先用 `/caveman lite` 试几轮，对比 token 用量变化，再决定用哪个级别。

4. **安全建议的边界**：本文提供的安全建议（如 flag 文件 symlink 检查、文件权限 0600）是基于通用最佳实践。具体的安全需求需要根据你的威胁模型调整。本文不构成专业安全审计或法律建议。

5. **未覆盖的内容**：本文未详细讨论如何编写高质量的 SKILL.md（强度级别定义）、如何调试 hooks（如 caveman-mode-tracker.js 未正确注入规则）、如何在无 hooks 系统的 Agent 中使用 caveman（需要手动添加 snippet 到 rules 文件）。这些内容的详细讨论需要单独的文章或视频教程。

6. **更新记录**：本文基于 caveman v（2026-04-30）编写。如果 caveman 发布新版本，部分内容可能需要更新。

---

## 结语：什么时候用，什么时候不用

caveman 适合这些场景：

- 日常编码问答、bug 修复、代码审查——你只需要结论和操作步骤，不需要解释过程。
- 高频交互——每轮省下的 token 累积起来，响应速度和上下文窗口占用都会明显改善。
- 上下文已经清晰的任务——问题和上下文明确时，LLM 不需要再「确认一遍」。

这些场景需要谨慎：

- 教学、新人 onboarding——解释过程本身就是价值，压缩会损害学习效果。
- 需要详细推理链的任务——用 `full` 或 `lite` 模式，别上 `ultra`。
- 安全相关操作——caveman 的 auto-clarity 机制会自动降级为正常模式，不需要手动干预。

建议采用顺序：先用 `/caveman lite` 试一两轮，感受压缩程度；不影响理解就切到 `full`（默认）；需要极致效率时用 `ultra`。文言文模式适合中文开发者和需要文言文输出的场景。压缩输入文件（`.md`、`CLAUDE.md`）时，先用 `/caveman:compress` 跑一次，对比原始备份确认没有丢关键信息，再替换。

如果团队里有人反感碎片句式，直接用 `lite` 模式——去掉填充词但保留完整句子，学习成本最低。

---

## 常见问题

**Q1: 我用了 `/caveman`，但几轮对话后 AI 又变啰嗦了，怎么办？**

这是因为其他插件或 system prompt 可能在后续轮次中覆盖了 caveman 的规则。caveman 的 `caveman-mode-tracker.js` 在每轮 UserPromptSubmit 时都会重新注入规则——但如果你的 Claude Code 版本不支持 hooks，per-turn reinforcement 就不会生效。排查：检查 statusLine 是否有 badge（确认 hooks 已安装），或者在对话中手动输入 `talk like caveman` 触发自然语言激活。

**Q2: caveman 会压缩代码块里的内容吗？**

不会。代码块（`` ``` `` 包裹的内容）、行内代码、错误信息、文件路径、URL、技术术语全部保持原样。caveman 的压缩只针对 LLM 的“说话方式”——填充词、客套话、冠词、犹豫词——不碰任何技术内容。

**Q3: 文言文模式（wenyan）的实际使用场景是什么？**

两个场景：一是处理中文技术文本时获得比 full/ultra 更高的 token 压缩率（文言文本身信息密度极高）；二是需要 LLM 输出文言文风格的技术说明（如生成中文技术文档的古风版本）。日常开发不建议用 wenyan-ultra——可读性会明显下降。

**Q4: caveman 和 cavemem、cavekit 之间是什么关系？需要三个都装吗？**

三个工具独立运作，不强依赖。caveman 压缩 AI 的**输出**（每轮回复），cavemem 压缩跨会话的**记忆**（持久化存储），cavekit 负责**构建编排**。只装 caveman 完全够用，另外两个按需选择：需要跨会话记忆时加 cavemem，需要自然语言驱动的构建循环时加 cavekit。

**Q5: caveman 的 token 节省数据（65%）是怎么算出来的？我自己的场景能省多少？**

65% 是 `benchmarks/` 中 10 个典型任务的算术平均，范围从 22%（重构 async/await）到 87%（解释 React 错误边界）。实际节省幅度取决于你的 LLM 默认输出有多 verbose——agent 本身简洁则节省偏低，agent 习惯先客套再回答则节省更明显。建议先用 `/caveman lite` 试几轮，对比 token 用量变化，再决定用哪个级别。

---

> **相关资源**
> - GitHub: [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) (50,544 ⭐)
> - 官网： [getcaveman.dev](https://getcaveman.dev/)
> - 关联项目： [cavemem](https://github.com/JuliusBrussee/cavemem) · [cavekit](https://github.com/JuliusBrussee/cavekit)
> - 论文： [Brevity Constraints Reverse Performance Hierarchies (arXiv:2604.00025)](https://arxiv.org/abs/2604.00025)
