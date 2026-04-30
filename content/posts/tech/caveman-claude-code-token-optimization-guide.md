---
title: "Caveman：让 AI 用「山顶洞人语言」说话，砍掉 65% Token 消耗"
date: 2026-04-30T11:30:00+08:00
categories: ["技术笔记"]
tags: ["Claude Code", "Token 优化", "Prompt Engineering", "AI 效率", "LLM"]
---

## 引言：一个反直觉的发现

2026 年 4 月，一个名为 **caveman** 的 Claude Code 插件在 GitHub 迅速走红——上线不到一个月斩获 **50,544 颗星**，2,680 个 Fork，话题覆盖 Hacker News 头版。这个项目的核心理念看似荒诞：

> **why use many token when few token do trick**
> （为什么用很多 token，几个 token 能搞定的事？）

简而言之：让 AI 用「山顶洞人语言」说话——去掉所有冗余的填充词、客套话、犹豫词——结果发现，**Token 消耗降低 65%，技术准确性却纹丝不动**。

这不仅仅是省钱的问题。LLM 输出的冗长程度直接决定了响应速度、上下文窗口的消耗，以及人类阅读的体验。更重要的是，2026 年 3 月的一篇论文 ["Brevity Constraints Reverse Performance Hierarchies in Language Models"](https://arxiv.org/abs/2604.00025) 证明：**约束大模型输出简短回答，在某些基准测试上准确率提升了 26 个百分点， Verbose 并不等于准确。**

本文从原理、架构、实战三方面，彻底解析 caveman 这一现象级工具。

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

Caveman 的压缩策略并非随意删字，而是基于一套系统的语言压缩规则：

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

> ⚠️ **关键说明**：Caveman 只影响输出 token（LLM 回复），思考/reasoning token 不受影响。Caveman 不是让 AI 变笨，而是让 AI「闭嘴说重点」。

### 1.4 为什么「简洁」不等于「信息丢失」

核心洞察是：**LLM 训练时大量「有帮助」的输出实际上是 filler（填充词）**。这些词帮助 LLM 生成流畅的文本，但并不携带独立的信息。Caveman 的压缩本质上是信息论中「去冗余」（de-redundancy）的应用。

更重要的是，Caveman 对以下内容**绝对不压缩**：
- 代码块（完全保持原样）
- 错误信息（逐字引用）
- 文件路径、URL、命令
- 技术术语、API 名称、库名

---

## 二、架构分析：系统是如何设计的

### 2.1 整体架构

caveman 不是一个单一脚本，而是一个**多智能体插件系统**，支持 8+ 种 AI 编程工具：

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

关键设计决策：**SKILL.md 是唯一行为定义源**，而不是在钩子中硬编码规则。这样任何对 SKILL.md 的编辑会自动反映在 SessionStart 注入中，无需修改钩子代码。

#### `hooks/caveman-mode-tracker.js` — UserPromptSubmit 钩子

这是实现「多轮对话中不丢失 caveman 模式」的关键：

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

这是 caveman 最有趣的设计——利用人类历史上 token 效率最高的书面语言「文言文」进行压缩：

| 级别 | 示例 |
|------|------|
| **wenyan-lite** | "組件頻重繪，以每繪新生對象參照故。以 useMemo 包之。" |
| **wenyan-full** | "物出新參照，致重繪。useMemo Wrap之。" |
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

## 结语

caveman 的成功揭示了一个深刻的洞察：**LLM 的冗长输出是一个可以系统性压缩的维度，而不必然伴随信息损失**。它的价值不仅是省 Token——更是在保持技术准确性的同时，大幅提升人机交互的效率。

50,544 颗星不是偶然。这是一个让开发者真正感到「相见恨晚」的工具——因为每个人都被 AI 的冗长回复折磨过，而 caveman 用最朴素的方式解决了它。

**why use many token when few token do trick.**

---

> **相关资源**
> - GitHub: [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) (50,544 ⭐)
> - 官网: [getcaveman.dev](https://getcaveman.dev/)
> - 关联项目: [cavemem](https://github.com/JuliusBrussee/cavemem) · [cavekit](https://github.com/JuliusBrussee/cavekit)
> - 论文: [Brevity Constraints Reverse Performance Hierarchies (arXiv:2604.00025)](https://arxiv.org/abs/2604.00025)
