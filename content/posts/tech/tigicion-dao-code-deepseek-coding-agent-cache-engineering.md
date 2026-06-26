---
title: "DAO Code：在 DeepSeek V4 上做 cache engineering 的终端编码 agent"
date: 2026-06-27T02:28:00+08:00
draft: false
categories:
  - 技术笔记
tags:
  - AI-Agent
  - 终端工具
  - DeepSeek
  - 开源项目
slug: tigicion-dao-code-deepseek-coding-agent-cache-engineering
author: 钳岳星君
description: "tigicion 的 DAO Code v0.2.0（MIT 协议，420 stars），中文优先的终端编码 agent；用 prompt-cache-aware 字节稳定前缀、反思层复用热缓存、CC 1:1 权限引擎、影子 git 检查点，把 DeepSeek V4 性价比压到 ¥0.15 / 次功能开发。"
---

# DAO Code：在 DeepSeek V4 上做 cache engineering 的终端编码 agent

## 核心判断

[tigicion/dao-code](https://github.com/tigicion/dao-code) 是 2026 年 6 月初开源的中文优先终端编码 agent，发布 3 周到 420 stars / 5 forks。命令名 `dao`，道家美学（Ink TUI + 太极开屏 + 亮暗自适应），目标单一：**在 DeepSeek V4（1M 上下文）上做 cache engineering，把高性价比模型的体验和成本都拉到 Claude Code 水平**。

支撑这个判断的是 README 里 7 道真实开源 bug-fix 评测的实测数据：

| 任务（真实开源 repo） | 输入 tok | 命中率 | DeepSeek Pro |
|---|---:|---:|---:|
| t7-sqlglot-sqlite-autoinc | 1,218,385 | 97.7% | ¥0.213 |
| t6-sqlglot-comment-on | 625,772 | 96.3% | ¥0.144 |
| t9-hono-compress | 699,479 | 96.0% | ¥0.209 |
| **合计** | **3,886,037** | **95.8%** | **¥1.07** |

同一 token 轨迹按 Claude 官方单价算一遍：**比 Claude Opus 4.8 省 ~30×、比 Sonnet 4.6 省 ~18×**。这不是营销话术——`evals/runs/<task>/run-1/agent.log` 留了完整证据链，`/cost` 命令可现场复看。

把这份成本数据和技术架构合起来看，DAO Code 的工程取舍和其他 agent（Claude Code / Codex CLI / Gemini CLI）走的是不同方向：

- **不走贵模型路线**——靠 DeepSeek 的低价位 + 高 prefix-cache 命中率撑起体验
- **不走纯 prompt engineering 路线**——把「系统前缀字节稳定」「反思 fork 复用主缓存」「增量压缩不破前缀」当成工程问题而不是 prompt 问题
- **不走全托管路线**——所有工程取舍在本地 26MB 单文件二进制（`bun build --compile`），MIT 协议、零云端依赖

这篇文章把这个项目当「prompt-cache-aware agent 设计的工程样本」来拆解：从架构总览、缓存纪律、反思层、权限引擎、长任务稳健性，到怎么把它接进自己团队的工作流。

## 学习目标

读完本文后，你应当能够：

1. 说出 DAO Code 的 7 大子系统（agent loop / tools / permissions / memory / session / client / hooks）的职责划分，以及每个子系统对应「真实工程问题」中的哪一个。
2. 解释为什么「系统前缀字节稳定」是 DeepSeek V4 prefix-cache 命中的必要条件，并指出哪些常见操作会破坏前缀（per-turn truncation、双向嵌入时间戳、随机化文件顺序等）。
3. 描述反思层（challenger / refocuser / reply-challenger）为什么必须走 fork 子代理而不是 in-place 反思，以及「复用主前缀缓存」在这里的精确含义。
4. 列出 CC 1:1 权限引擎的优先级链（deny > bypassPermissions > sensitive target > ask > allow > mode default），并解释「auto 模式 + 危险 shell 命令 + 触及敏感目标」三者同时出现时如何裁决。
5. 区分影子 git 检查点（`/restore` `/rewind`）和主 git 的关系，以及为什么它要独立成 git 而不直接 commit 到项目 git。
6. 把 DAO Code 当 Claude Code 的本地替代品来用，并理解其成本结构里 cache hit rate 的边际效应。

## 目录

- [核心判断](#核心判断)
- [学习目标](#学习目标)
- [DAO Code 在 agent 生态里的位置](#dao-code-在-agent-生态里的位置)
- [总览图：一次回合的 7 个子系统协作](#总览图一次回合的-7-个子系统协作)
- [缓存纪律：DeepSeek prefix-cache 命中的工程化](#缓存纪律deepseek-prefix-cache-命中的工程化)
- [反思层：fork 子代理复用主前缀缓存](#反思层fork-子代理复用主前缀缓存)
- [CC 1:1 权限引擎：从 deny 到默认值的完整优先级链](#cc-11-权限引擎从-deny-到默认值的完整优先级链)
- [压缩策略：增量摘要 + 硬截断兜底](#压缩策略增量摘要--硬截断兜底)
- [长任务稳健：影子 git 检查点 + 双工通信](#长任务稳健影子-git-检查点--双工通信)
- [任务如何流过系统：一次完整回合](#任务如何流过系统一次完整回合)
- [决策启示：独立开发者 / 团队 lead / 量化研究者各看什么](#决策启示独立开发者--团队-lead--量化研究者各看什么)
- [采用顺序与边界](#采用顺序与边界)
- [参考资料](#参考资料)

## DAO Code 在 agent 生态里的位置

DAO Code 的卡位有两层。一层是 agent 生态（Claude Code / Codex CLI / Gemini CLI / Aider / Cursor）里「中文优先 + 廉价模型」的位置，另一层是开发工具生态里「终端原生」的位置。

第一层是定位问题。Claude Code 强在体验，国内可用性靠运气；Codex CLI 强在 OpenAI 模型覆盖；Gemini CLI 是 Google 系的中段选择。DAO Code 把可用性赌在 DeepSeek V4 上——大陆直连、按量付费、注册即用，配合 prompt-cache 命中率把单位成本拉到 Claude 的 1/18 到 1/30。

第二层是形态问题。终端原生 agent 的核心约束是「所有信息流必须在终端里、不破坏 shell 工作流」。具体落地有四点：

- 输入必须支持多行编辑、slash 命令、steering（回合运行中排队打字）
- 输出必须支持 streaming、thinking block、tool call 折叠、行号+语法高亮的 diff
- 中断必须支持 ESC 一键（模型流和 shell 都停）
- 非 TTY 必须自动回退纯文本 REPL

DAO Code 用 Ink（React for CLI）+ 自定义 ESC 处理满足这些约束。`tui/app/App.tsx` 是 Ink 主组件，把 streaming、approval modal、slash command dispatch 装进 React state。

两个卡位合起来决定了一件事：**DAO Code 的工程复杂度主要花在「让 DeepSeek 用得爽」上，而不是「让 LLM 更聪明」上**。这一点下面会反复看到。

## 总览图：一次回合的 7 个子系统协作

```text
              用户输入
                │
                ▼
    ┌───────────────────────┐
    │  src/index.ts         │ 启动/装配
    └───────────┬───────────┘
                │
                ▼
    ┌───────────────────────┐
    │  agent/loop.ts        │ runTurn(deps)
    │  - 回合循环           │ TurnDeps 注入所有依赖
    │  - 信号透传           │ 可单测
    └───────────┬───────────┘
                │
       ┌────────┼────────┬──────────┬──────────┐
       ▼        ▼        ▼          ▼          ▼
   permissions  tools   memory  approval    client
   (引擎)      (24 个)  (3 层)  (审批门)   (DeepSeek SSE)
       │        │        │          │          │
       └────────┴────────┴──────────┴──────────┘
                          │
                          ▼
                  会话状态 (session)
                  - log (持久化)
                  - checkpoint (影子 git)
                          │
                          ▼
                  hooks (5 生命周期事件)
                  - PreToolUse / PostToolUse 等
```

`runTurn` 是入口。它接收一个 `TurnDeps` 对象（session、config、registry、ctx、gate、streamChat、executeToolCalls、write、events、maxTurns、signal、drainPending、drainAdvisories、drainNotifications、compact、shouldCompact、fallbackModel、diagnose、background、auditSink、auditId、reflect、longTask）——几乎所有可变的运行时依赖都走注入，让 `runTurn` 可以在测试里完全 mock，也可以在子代理里替换 fork 的行为。

7 个子系统的精确职责：

| 子系统 | 路径 | 职责 | 失败兜底 |
|---|---|---|---|
| **agent/loop** | `src/agent/loop.ts` | 回合循环、信号透传、回合健康 | 强制 stop + commit 当前 todo |
| **tools** | `src/tools/*.ts` | 24 个工具，capability + zod schema | 工具异常转 tool result 给模型 |
| **permissions** | `src/permissions/engine.ts` | CC 1:1 权限裁决 | deny 永远拦截 |
| **memory** | `src/memory/*.ts` | 3 层记忆 + 反思蒸馏 + 校验 | 启动校验失败剔除过期 |
| **session** | `src/session/*.ts` | 日志持久化 + 影子 git | 崩溃恢复用 `dao -c` |
| **client** | `src/client/*.ts` | DeepSeek SSE 流式客户端 | 上下文超限 → compactMessages 重试 |
| **hooks** | `src/hooks/*.ts` | 5 生命周期事件 | hook 失败降级为默认行为 |

## 缓存纪律：DeepSeek prefix-cache 命中的工程化

DAO Code 设计里最值得拆解的是缓存纪律。DeepSeek V4 的 prefix-cache 命中价约为未命中的 1/10——这是它在中文场景里能压住成本的关键。但 prefix-cache 是字节级精确匹配，任何在前缀里的随机变化（时间戳、UUID、动态环境变量）都会让缓存失效。

DAO Code 把这条纪律写到了 `loop.ts` 注释里：

> **廉价稳定哈希（djb2）**：只用于「是否变化」的缓存归因指纹，不求抗碰撞。

「字节稳定」四个字的具体含义是：**从主对话开始到第一个用户消息之间的所有内容（system prompt + 工具表 + 记忆注入 + 项目指令），每次请求必须字节相同**。DAO Code 通过三类工程手段守住这条线：

**1. 系统 prompt 模板固定**

`src/prompt/system_prompt.ts` 输出一个固定模板，唯一变量是项目指令插槽 `{project_instruction_files}`，由 `loadProjectInstructions()` 在每次请求时填充——但填充的内容来自 `DAO.md` 或 `CLAUDE.md`，文件不变就不变。如果模型在回话中插入时间戳、运行 ID、随机数，会让前缀失效。

**2. 工具表静态**

`apiToolsForMode(mode)` 返回当前模式（normal / plan / acceptEdits / auto）对应的工具描述列表。**模式切换会让工具表变化**——所以 DAO Code 不在「回合内」自动切模式，只在 `/mode` 命令切；切模式等于破一次前缀缓存。这是设计取舍。

**3. 反思 fork 不破前缀**

反思层（challenger / refocuser）的实现是 fork 子代理——继承主对话的消息历史、工具表、thinking 配置，但因为是新调用，前缀缓存是从「system 开头」开始重新算的。这里的关键不是 fork 本身，而是 `fork: true` 让 DeepSeek 把这次调用的前缀判定为「主对话的延续」，而不是「新对话」。这条路径上的 cache hit 由 DeepSeek 服务端控制，但 DAO Code 通过让 fork 调用复用完全相同的 messages 数组确保命中。

违反这些纪律的常见反模式：

- ❌ 在 system prompt 里嵌入 `Date.now()` 拿到的当前时间
- ❌ 把每次请求的 UUID 放到工具描述里
- ❌ 动态随机化 memory 注入顺序
- ❌ 在 prompt 里嵌入 `process.pid`
- ❌ 用 `setSystemMessage` 在每回合开头追加「你已经在第 N 轮」的提示

**测的是什么、不能推出什么**：字节稳定纪律测的是「连续请求前缀缓存命中率」。**不能推出**「单次请求便宜」——单次请求无论前缀是否稳定都按全价算。成本优势只在多轮会话里显现。

DAO Code 提供 `/audit cache` 用「四维指纹」（系统前缀 / 工具表 / 记忆注入 / 消息累计 hash）定位「谁破了缓存」——这是 95.8% 命中率能持续保持的运维工具。

## 反思层：fork 子代理复用主前缀缓存

反思层是 DAO Code 的第二大设计亮点。它解决三个具体问题：

| 触发条件 | 反思角色 | 行为 |
|---|---|---|
| 连续失败 / 同错复发 | **challenger** | 派独立视角怀疑性复核、质疑前提 |
| 长任务每 N 轮 | **refocuser** | 复述最初目标、揪 scope 蔓延 |
| 用户重复同一问题 | **reply-challenger** | 自动介入 |

三者都走 fork 子代理。为什么必须 fork 而不是 in-place 反思？

**in-place 反思的失败模式**：

1. 反思 prompt 塞进主对话的 system prompt → 前缀缓存被破坏
2. 反思输出塞进主对话 → 主对话被反思结论污染，模型被「牵着鼻子走」
3. 反思和主任务共享同一上下文 → 反思可能干扰主任务

**fork 反思的优势**：

1. 反思 fork 完全复用主对话前缀 → cache hit
2. 反思输出通过 `drainAdvisories()` 在回合边界作为 system advisory 注入，不污染主对话历史
3. 反思和主任务并行，但成本主要花在 thinking tokens（DeepSeek 的 thinking 走的是输出侧，输出侧没缓存但单价比输入贵，10x）

`unified_reflect.ts` 把三个反思角色合并成一个统一反射器——一个 fork 既做进展反思（产出 advisory）又抽记忆（产出 memories with mergeInto 合并意图）。合并到统一反射器是因为：

- 同样的工具表、同样的 thinking 配置、同样的 fork 路径
- 同样的缓存前缀复用
- 同一个 JSON 输出格式（`{onTrack, advisory, memories[]}`）

实战中反射成本几乎为零——根据 README 的评测，95.8% 缓存命中时，flash 模型跑一次反思大约 0.001 元（按 DeepSeek V4 Flash 现价）。

「反射结果可信吗」是另一个问题——`REFLECT_TAIL` 提示词里特意写了「一切在轨或只是新任务 → onTrack=true、advisory=null，绝不硬找茬」，避免模型「找茬强迫症」。`SALIENCE_MIN = 4` 把 importance < 4 的琐碎记忆丢弃，和 `distill` 模块保持一致。

## CC 1:1 权限引擎：从 deny 到默认值的完整优先级链

DAO Code 的权限引擎是 Claude Code 的 1:1 复刻。`src/permissions/engine.ts` 的 `decide()` 函数实现了一条严格的优先级链：

```
deny 规则
  > bypassPermissions (yolo: deny 之外全过)
  > 安全敏感目标确认 (mustConfirm)
  > ask 规则
  > allow 规则
  > 模式 / 能力默认
```

任何调用按顺序走，第一条命中的决策生效。`mustConfirm` 是硬性兜底——即使在 `bypassPermissions` 模式下，触及敏感目标或执行危险 shell 命令也会被拦截。

**敏感目标**（`SENSITIVE_TARGET`）的正则覆盖：

```regex
.ssh/|id_rsa|id_ed25519|id_ecdsa|authorized_keys|
.aws/|.npmrc|.netrc|credentials|.gitconfig|.git/|.bashrc|.zshrc|.bash_profile|.zprofile|/etc/|.dao/config.json
```

**危险 shell 命令**（`bash_safety.ts` 的 `dangerSegment`）包括但不限于：

- `rm -rf /` / `rm -rf ~` / `rm -rf *` 等递归删除根/家目录/通配
- `dd of=/dev/disk` / `mkfs` / `tee of=/dev/disk` 写裸磁盘
- `chmod -R 0?777` / `chown -R /` 递归改权限/属主到危险目标
- `>` 覆盖 `/etc/` 系统配置
- `find ... -delete` / `find ... -exec rm` 批量删除
- `git push --force` / `git reset --hard` / `git clean -fdx` 毁 git 历史
- `kill -9 -1` / `killall` / `pkill -9` 批量杀进程
- `sudo` / `eval` 提权 / 动态执行
- `curl | sh` / `wget | bash` 远程代码执行

这套设计的关键是**「安全敏感目标 + 危险命令」是 hard block，不是 ask**——任何模式（包括 yolo）都不能跳过。这避免了一类常见 bug：用户为了方便开了 yolo，结果 agent 不小心 `rm -rf` 把家目录清了。

auto 模式有一个白名单快速路径（`AUTO_ALLOWLIST`）：

```ts
const AUTO_ALLOWLIST = new Set([
  "read_file", "grep_files", "file_search", "list_dir",
  "todo_write", "ask_user", "memory_read", "skill", "verify_done", "echo",
]);
```

只读类工具直接放行，省一次分类器调用。`exec_shell` 在 auto 模式下如果命令是 `isReadOnlyShellCommand` 白名单（如 `ls` `cat` `pwd`），也走快速路径。

**测的是什么、不能推出什么**：权限引擎测的是「按规则集给出确定性裁决」。**不能推出**「所有危险操作都被覆盖」——`isDangerousCommand` 是启发式正则，复合命令、unicode 混淆、未列举的新攻击模式都可能漏判。这是纵深防御的一层，不是唯一防线。

## 压缩策略：增量摘要 + 硬截断兜底

长任务最大的敌人是上下文溢出。DAO Code 的压缩策略写在 `compact.ts` 注释里，思路比 CC 更激进：

```ts
// 为何不再保留"最近 N 轮原文"：
// 压缩后前缀本就从【新摘要】处断开缓存，
// tail 落在冷区、留原文对缓存无益；
// 续接改由摘要的"当前工作/下一步（附原话引用）"小节承载
// （对标 CC 的整段摘要）。这也根除了"最近轮含大工具输出 → 
// tail 膨胀、压不动"的结构性问题。
```

压缩流程：

1. **反应式压缩**（L2.2）：`streamChat` 报「上下文超限」时调 `compactMessages` 压缩后重试本轮
2. **轮内主动压缩**（§4）：每个工具轮前若 `shouldCompact()` 返回 true 则先压缩，防长回合中途撞上限
3. **增量压缩**：若 `rest[0]` 是上次压缩留下的摘要（以 `[早期对话摘要` 开头），把它的文本原样保留，只把新增内容拼上。**不二次摘要 → 免转述磨损**。早期要点逐字不衰减
4. **硬截断兜底**（L2.3）：摘要失败（模型挂 / 熔断）→ 直接截断旧对话 + 保留系统提示 + 提示任务清单，绝不让「压缩本身」把长任务搞崩
5. **pinned 任务清单**：压缩后把活任务清单作为 system message 注入，防止目标漂移

关键的工程取舍是「不保留最近 N 轮原文」。CC 这么做是因为 tail 落在冷区对缓存无益；DAO Code 跟进，但加了一个细节：**摘要必须包含「当前工作/下一步（附原话引用）」**——原文不是被丢掉，而是被引用进摘要。

**踩坑笔记（README 里的）：**

> **microcompact 只在 `compactMessages` 内调用**——别做「每回合独立裁剪」，否则破坏 DeepSeek 前缀缓存、净亏。

这是一个具体教训：DAO Code 早期版本做过每回合裁剪旧工具结果，结果发现裁剪过的前缀不再命中缓存，每回合重新算一遍，反而比「不裁剪、走整段压缩」更贵。

## 长任务稳健：影子 git 检查点 + 双工通信

DAO Code 借鉴了 CC 的几条长任务稳健机制，又加了自己的实现：

**1. 影子 git 检查点**

`src/session/checkpoint.ts` 用独立 git（`~/.dao/checkpoints/<session>/`）管理快照。`/restore` `/rewind` 命令从这个影子 git 拉回历史快照。**它不碰项目的 `.git`**——这是关键，避免 agent 操作污染项目 git 历史。

影子 git 的 commit 不带 message，纯 snapshot，由 session ID + turn number 索引。`dao -c`（continue）从上次中断恢复会话时，影子 git 让「回到 N 轮前」变成 1 个命令。

**2. todo 穿越压缩**

压缩时把 `todo_write` 当前状态 pin 进 system message。这样模型在压缩后仍知道「还在做哪些事、做到了第几步」。

**3. DoD 验收**

`/dod` 命令 + `verify_done` 工具——给一个 Definition of Done 的描述，agent 派 `verify` 子代理（bundled agents 里的对抗性验证）真跑命令验证。这条特别有意思：`verify` 的 prompt 里写明「**不是**确认能用，而是**试图证明它是坏的**——对抗性找反例、边界、回归」。

`verify` 子代理拒绝「代码看起来是对的」「实现者的测试已经过了」「这个大概没问题」这类自我合理化借口。它必须：

- 真跑构建（失败直接判不通过）
- 真跑测试套件（失败直接判不通过）
- 真跑 linter / 类型检查
- 试 happy path 之外的边界（并发、边界值、幂等、孤儿）
- 在签发「通过」前至少贴一条真跑了的对抗性探测 + 结果

这是 DAO Code 设计哲学的浓缩——**「通过」必须有可复现的命令输出，不是模型自评**。

**4. 子代理双工通信**

`src/agent/subagent.ts` + `tasks.ts` 提供后台子代理队列，父↔子双向通信（`task_send` 工具 + `message_parent` 工具）。`drainNotifications()` 在主回合边界注入后台完成结果——这是 `--goal` 长任务模式的关键，不至于 headless 跑长任务时后台结果丢失。

默认 max turns 150，Coordinator 模式 500。`DAO_MAX_TURNS` 环境变量可覆盖——eval / 自动化场景常用。

## 任务如何流过系统：一次完整回合

为了让 7 个子系统抽象落地，看一个具体的「读 / 改 / 测 / 自审完整 bug 修复任务」怎么走 DAO Code 的管道。

**用户输入：**「修一下 hono compress middleware 的 cookie dup 问题」

**Step 1：`runTurn` 启动**

`runTurn` 接收 TurnDeps——所有依赖已注入。从 session 加载历史消息，构造本次回合上下文。`cheapHash(messages[0])` 计算系统前缀指纹，作为 cache audit 起点。

**Step 2：DeepSeek 流式响应**

`streamChat()` 调用 DeepSeek V4 Pro。第一次请求前缀命中率为 0（冷启动），成本按未命中价算。`consumeStream()` 接收 SSE delta，把 thinking block 和 text content 分别喂给 Ink 渲染。

模型返回 `tool_call: read_file({path: "src/middleware/compress/index.ts"})`。

**Step 3：权限裁决**

`decide({toolName: "read_file", capability: "read", mode: "normal"})`：

- 不是敏感目标
- 不是危险命令
- 规则集没有匹配
- 模式默认 = read_file + read capability = allow

`PermissionGate` 直接放行。`executeToolCalls` 把 read_file 加入并行池。

**Step 4：工具执行**

`readFileTool.handler` 跑：

- `classifyPath` 验证路径在工作区
- `fs.stat` 检查文件大小（5MB 上限）
- `fs.readFile` 读 utf-8
- 检测 NUL 字节确认不是二进制
- `ctx.readFiles.add(abs)` 记录「写工具必须先 read_file」的依赖链
- 2000 行默认上限（超出提示用 offset/limit）

返回带行号的内容给模型。

**Step 5：模型再次响应**

流式返回，这次带 2 个 tool_call：

- `edit_file({path, old_text, new_text})`
- `exec_shell({command: "npm test"})`

**Step 6：权限裁决（关键）**

`decide(edit_file)`：write capability，模式 normal → 默认 ask。但项目工作区内 + 用户在 DoD 描述里写了「修 cookie dup bug」→ ask 规则匹配 → ask。

`decide(exec_shell, "npm test")`：exec capability，但 `isReadOnlyShellCommand("npm test")` 返回 false（`npm test` 不在只读白名单）。规则集匹配 → ask。

两条都进 `ApprovalGate`，弹出 Ink modal 等用户 Y/N。

**Step 7：用户审批 + 工具执行**

用户在终端按 Y，两条工具并行跑：

- `edit_file.handler` 调 `resolveWritePath`（区外写走授权），改 compress middleware 的相关行
- `exec_shell.handler` fork 子进程跑 `npm test`

**Step 8：诊断钩子**

`edit_file` 触发 `diagnose` 回调（PostToolUse hook），跑 `tsc --noEmit` 检查类型，把诊断信息作为 `[诊断]` system message 回灌给模型。模型看到诊断可能会自改。

**Step 9：verify 子代理**

模型声明完成。`/dod` 触发 verify 子代理——根据 bundled_agents.ts 的定义，verify 是 `read-only thorough + exec_shell` 工具集，但 prompt 明确「试图证明它是坏的」。它会跑 `npm test` + 故意构造边界输入（比如空 cookie、unicode cookie、超长 cookie）+ 抓 dev server console 看错误。

verify 输出「判定:通过」或「判定:不通过」。

**Step 10：反思 + 记忆**

回合末触发 `unified_reflect.ts`：

- 进展反思：onTrack=true（任务完成 + verify 通过）
- 记忆抽取：「hono 用户偏好 npm test 在中间件目录跑」→ memory_write 到 user 层
- mergeInto 判断：是否有同名条目 → 有则 update，无则 add

**Step 11：cost 报告**

`/cost` 命令（也可在状态栏）显示：

- 本回合输入 tok、输出 tok、cache hit rate
- 累计花费（按 DeepSeek V4 Pro 现价算）
- 累计命中 vs 未命中占比

整个回合的 cache hit 率大概是 95-97%——主前缀（system + tools + memory + project_doc）每回合都复用，只增量部分（用户消息 + 模型新增消息 + 工具结果）按未命中算。

## 决策启示：独立开发者 / 团队 lead / 量化研究者各看什么

DAO Code 对三类读者的信号不同。

**独立开发者**——如果你的日常工作流在终端、且对 Claude Code 的成本敏感，DAO Code 是当前性价比最高的中文替代。具体路径：

- 一键安装脚本一行启动，按量付费 ¥0.07-0.21 / 次功能开发
- `~/.dao/config.json` 存 DeepSeek API key，无需每次配
- `/init` 扫描仓库生成 `DAO.md`，下次会话自动加载项目约定
- `/goal <目标>` 跑长任务，自动批准 + 连续推进
- `/cost` 随时看命中率，缓存设计出问题立刻能定位

**团队 lead**——DAO Code 的工程取舍有两点值得借鉴：

- **字节稳定纪律**：把它做成 lint 规则（检测 system prompt / 工具描述里的随机源），任何 agent 框架都应该有
- **fork 反思模式**：challenger / refocuser 不要 in-place，跑子代理 + drainAdvisory 注入；这避免「反思污染主对话」+「反思破坏前缀缓存」两个 bug
- **影子 git 检查点**：所有 agent 都应该有这个机制；不碰项目 `.git` 是底线
- **`mustConfirm` 兜底**：敏感目标 / 危险命令无论 yolo 还是默认都要人工确认——纵深防御的最内层

**量化研究者 / 数据团队**——DAO Code 不是为数据场景设计的（不像 [FTShare Python SDK](https://txtmix.com/posts/tech/ftshare-python-sdk-financial-data-agent-access-layer/) 那样专攻金融数据），但它的几个工程机制可以借用到 quant 工具链：

- **cache engineering**：如果你的 agent 跑 OpenAI / Anthropic API，prefix cache 同样存在。字节稳定 + 反思 fork 这套思路可以直接搬
- **`verify` 子代理**：让 LLM 验证自己的输出，而不是它自己评。「真跑命令 + 贴输出 + 对抗性边界」这套 prompt 模板可以复制到任何量化代码生成工作流
- **影子 git**：量化 notebook 的版本管理是个长期痛点——影子 git 检查点能解决「昨晚那个回测结果我想恢复」的常见需求

## 采用顺序与边界

对想用 DAO Code 的读者，按以下顺序最经济：

**第一步：装 + 跑一次最小任务**——一键安装脚本一行启动，跑一次「读 README 然后改一行无关紧要的注释」，验证 pipeline 通。

**第二步：配 API key + 走 `/init`**——`DAO.md` 是项目级记忆的源头，在真实项目里跑一次 `/init` 看生成了什么。

**第三步：监控 `/cost`**——跑 5-10 个真实任务，观察 cache hit rate。如果低于 80%，说明字节稳定纪律被破坏，用 `/audit cache` 定位。

**第四步：配自定义权限规则**——`~/.dao/permissions.json` 加项目特定的 ask / allow 规则（比如「npm test 永远 allow」），减少回车次数。

**第五步：接 CI 或长任务**——长任务走 `--goal` 或 `/goal <描述>`，配合 verify 子代理验证。

**不一定要做的事**：

- 不要把 DAO Code 当通用 agent 框架——它的设计高度绑 DeepSeek prefix-cache 模型，换模型（如 Claude）会失去成本优势
- 不要在 system prompt 里嵌时间戳 / PID / 随机数——破坏缓存后成本会涨 10x
- 不要绕过权限引擎直接调工具——引擎的「敏感目标 / 危险命令」覆盖是 hard block，跳过的代价是数据丢失
- 不要在长任务里改 `.dao/` 目录——影子 git 在那里，污染会让 `dao -c` 恢复失败

**边界**：DAO Code 主要覆盖「终端编码工作流」，对以下场景只能部分覆盖：

- **GUI 应用**——没有桌面 GUI 自动化能力
- **实时协作**——单用户 agent，多人协作要走 git worktree 子代理模式
- **大文件 / 二进制**——read_file 有 5MB 上限，二进制文件主动报错
- **非 DeepSeek 模型**——cache engineering 思路可以搬，但 prefix-cache 实现各家不同，字节稳定纪律要重新验证

最后一个边界对国内开发者反而是优势——DeepSeek 国内直连、不需要额外网络配置。

## 参考资料

- [tigicion/dao-code GitHub 仓库](https://github.com/tigicion/dao-code)，MIT 协议，截至 2026-06-27 共 420 stars / 5 forks，v0.2.0
- [DAO.md 项目指令](https://github.com/tigicion/dao-code/blob/master/DAO.md)——开发约定与踩坑笔记（中文）
- [README.en.md 英文版](https://github.com/tigicion/dao-code/blob/master/README.en.md)——成本数据 + 7 任务评测表
- [src/agent/loop.ts](https://github.com/tigicion/dao-code/blob/master/src/agent/loop.ts)——回合循环核心 + 缓存指纹 djb2
- [src/agent/compact.ts](https://github.com/tigicion/dao-code/blob/master/src/agent/compact.ts)——增量摘要压缩策略
- [src/agent/unified_reflect.ts](https://github.com/tigicion/dao-code/blob/master/src/agent/unified_reflect.ts)——统一反思器 fork 模式
- [src/permissions/engine.ts](https://github.com/tigicion/dao-code/blob/master/src/permissions/engine.ts)——CC 1:1 权限裁决优先级链
- [src/permissions/bash_safety.ts](https://github.com/tigicion/dao-code/blob/master/src/permissions/bash_safety.ts)——危险 shell 命令启发式黑名单
- [src/agent/bundled_agents.ts](https://github.com/tigicion/dao-code/blob/master/src/agent/bundled_agents.ts)——explore / verify / plan / general-purpose 4 个内置子代理
- [src/memory/store.ts](https://github.com/tigicion/dao-code/blob/master/src/memory/store.ts)——3 层记忆 + 校验 + GC
- [DeepSeek V4 定价](https://platform.deepseek.com/api_pricing)——prefix-cache 命中价 ≈ 未命中的 1/10
- [Claude Code 权限系统](https://docs.claude.com/en/docs/claude-code/iam)——DAO Code 复刻的目标
- [NVIDIA SkillSpector：让 26% 不安全的 agent skill 无处藏身](https://txtmix.com/posts/tech/nvidia-skillspector-agent-skill-security-scanner/)——agent skill 安全扫描（系列）
- [Meta 挖角 Virtue AI 三位创始人](https://txtmix.com/posts/tech/meta-poaches-virtue-ai-agent-security-talent-war/)——agent 安全人才战（系列）
- [FTShare Python SDK](https://txtmix.com/posts/tech/ftshare-python-sdk-financial-data-agent-access-layer/)——agent skill 数据接入（系列）
