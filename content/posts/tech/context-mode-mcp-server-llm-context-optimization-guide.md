---
title: "Context Mode：AI 编程 Agent 上下文治理实战——从 40% 污染到零"
date: "2026-05-05T20:18:00+08:00"
slug: "context-mode-mcp-server-llm-context-optimization-guide"
description: "Context Mode 用沙箱隔离 + SQLite 事件日志 + 脚本优先范式 + 输出压缩四合一，把 AI 编程 Agent 的工具输出污染从 40% 压到接近零。这篇文章不讲概念，讲它到底做了什么、为什么能跑、你该怎么用。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "Context Mode", "MCP", "上下文优化", "AI编程", "LLM"]
---

# Context Mode：AI 编程 Agent 上下文治理实战——从 40% 污染到零

读前提醒：这篇文章不是在"介绍"一个工具——它想说明一件事情：AI 编程 Agent 的核心瓶颈已经不是模型能力，而是上下文窗口会被谁吃掉。

我们习惯纠结 prompt 怎么写、哪个模型更强，但打开一个运行了 30 分钟的 Claude Code 会话看一下，你会发现 40% 的上下文窗口根本不是你的代码，而是 MCP 工具调用吐回来的原始数据——一个 Playwright 快照 56 KB、20 个 GitHub issues 59 KB、一份 access log 45 KB。当 agent 压缩对话来腾空间，它最先丢掉的恰恰是你最后交代的那句话、正在改的文件、还没做完的任务。

Context Mode 做的事就是把这块重新设计：别把工具数据当对话输入，把它当数据——存到沙箱里，只把结论还给模型。

项目地址：[mksglu/context-mode](https://github.com/mksglu/context-mode)，Stars 12,712，MIT License，TypeScript 项目，截至 2026-05-05 仍在活跃更新。

## 目录

- [学习目标](#学习目标)
- [系统总览：四大组件如何配合](#系统总览四大组件如何配合)
- [1. 问题拆解：上下文窗口被吃掉的三条路径](#1-问题拆解上下文窗口被吃掉的三条路径)
- [2. 核心机制拆解](#2-核心机制拆解)
  - [2.1 Context Saving——工具数据不进 context](#21-context-saving工具数据不进-context)
  - [2.2 Session Continuity——压缩不丢记忆](#22-session-continuity压缩不丢记忆)
  - [2.3 Think in Code——模型不该读数据](#23-think-in-code模型不该读数据)
  - [2.4 Output Compression——输出减肥](#24-output-compression输出减肥)
- [3. 一个真实任务流过系统](#3-一个真实任务流过系统)
- [4. 支持平台](#4-支持平台)
- [5. Claude Code 安装与配置](#5-claude-code-安装与配置)
- [6. 性能数据解读](#6-性能数据解读)
- [7. 与传统 RAG 的边界](#7-与传统-rag-的边界)
- [8. 谁该用、谁不该用](#8-谁该用谁不该用)
- [9. 局限性与注意事项](#9-局限性与注意事项)
- [10. 常见问题](#10-常见问题)
- [11. 自测清单](#11-自测清单)
- [总结](#总结)

## 学习目标

| 层次 | 目标 |
|------|------|
| **基础** | 理解 MCP 工具调用为什么会"污染"上下文窗口，以及 Context Mode 的四合一方案各自解决什么问题 |
| **进阶** | 能在 Claude Code 上完成安装、验证和配置，理解脚本优先范式的思维切换要点 |
| **专家** | 能判断是否需要在团队中推广 Context Mode，知道它和传统 RAG 的边界以及不适合的场景 |

## 系统总览：四大组件如何配合

在你进入每个子机制的细节之前，先看一张职责总览表。Context Mode 不是一个单一技术，而是四条独立但协同的主线：

| 组件 | 拦截时机 | 数据放在哪里 | 模型拿到什么 | 核心效益 |
|------|----------|-------------|-------------|---------|
| **Context Saving** | MCP 工具返回时（PreToolUse / PostToolUse hook） | 沙箱文件系统 | 压缩后的摘要（原始数据 98% 不进 context） | 消灭工具数据污染 |
| **Session Continuity** | 对话压缩时（PreCompact hook） | SQLite + FTS5 事件日志 | BM25 检索到的相关事件摘要 | 压缩不丢工作记忆 |
| **Think in Code** | 每次需要读文件/分析数据时 | 不存（脚本即查即丢） | 脚本执行结果（一次调用替代 N 次 read） | 节省 100 倍 token 于批量读取 |
| **Output Compression** | 模型每次生成输出时 | 不存 | 去填充词但保留技术和安全的精准输出 | 输出 token 减少 65-75% |

单独看是四条优化手段，放在一起才是协同：Context Saving 挡住入站污染，Output Compression 压住出站膨胀，Session Continuity 兜底会话连续性，Think in Code 从范式上消灭不必要的读写。四条线的共同逻辑很简单——**把 LLM 从数据处理器的角色里解放出来，让它只做代码生成和决策。**

## 1. 问题拆解：上下文窗口被吃掉的三条路径

Context Mode README 列了四个维度，但按实际路径归纳成龙三条就够用了。

第一，**工具数据入站污染**。每次 MCP 工具调用都把原始数据直接写进 context。这不是 bug，而是设计——因为 LLM 需要看到工具输出才能做下一步决策。但当一次 Playwright 快照 56 KB、20 个 GitHub issues 59 KB 时，"看到数据"的代价是挤掉了真正重要的代码和历史对话。

第二，**压缩导致记忆断裂**。当 token 逼近上限，agent 会执行 compact——压缩之前的对话。这个压缩不是语义层面的"提炼要点"，而是粗粒度的截断加上模糊摘要。结果：模型忘了正在改哪个文件、还有几个任务没做完、你十分钟前那行重要指示是什么。

第三，**输出端膨胀**。模型在代码场景也会"说话太多"——填充词、客套话、过度保守的解释，这些从输出端反过来挤占下一轮的可用窗口。

三条路径加在一起，30 分钟会话后 40% 上下文被污染，这不是估计，是项目方的实测数据。

## 2. 核心机制拆解

### 2.1 Context Saving——工具数据不进 context

原方案下，MCP 工具返回什么，模型就看到什么。Context Mode 的做法是把工具输出重定向到沙箱文件系统，只在 context 里放一句压缩后的摘要。

具体来说，通过 Claude Code 的 PreToolUse 和 PostToolUse hook 拦截每一次工具调用，把原始输出写进沙箱，然后注入一段经过压缩的摘要代替原始数据。实测效果：315 KB 的工具原始数据 → 5.4 KB 摘要，reduction 98%。

这不是"压缩算法好"，是整个思路变了——工具输出的价值不在那些原始字节上，而在能从中推出的结论上。

沙箱暴露 6 个 MCP 工具供 agent 按需使用：

- `ctx_batch_execute`：批量执行分析脚本，适合一次处理多文件
- `ctx_execute`：执行单条分析脚本，用完即弃
- `ctx_execute_file`：执行已写好的脚本文件
- `ctx_index`：把内容编入 FTS5 索引，供后续搜索
- `ctx_search`：在已索引数据中搜索
- `ctx_fetch_and_index`：从 URL 抓取数据并自动索引

### 2.2 Session Continuity——压缩不丢记忆

对话压缩（compact）是不可回避的——token 窗口有硬上限。问题不在于压缩本身，而在于压缩后会丢掉什么。

Context Mode 的思路是：压缩前先把这些信息写到 SQLite 里——文件编辑记录、git 提交信息、当前任务栈、报错堆栈、用户的关键决策。压缩发生后，模型不再依赖被压缩掉的对话来回忆状态，而是通过 FTS5 全文搜索（BM25 评分）从 SQLite 中取相关事件。

```text
每次会话的核心事件会被打上标签存进 SQLite：
  - 文件编辑：哪个文件、改了什么、diffs
  - Git 操作：commit hash、branch、message
  - 任务状态：当前任务列表、完成状态
  - 用户决策：关键选择、显式声明的要求
  - 错误信息：堆栈、触发条件
```

两个关键行为：

- 带上 `--continue` 参数启动：从 SQLite 恢复上一 session 的事件记录，模型能"想起"上一次做到了什么程度
- 不带 `--continue`：session 结束时数据立刻清理，不会在磁盘上残留

### 2.3 Think in Code——模型不该读数据

这是整套方案里最反直觉但最有效的范式切换。

传统做法：agent 遇到"统计 src 下所有 .ts 文件的函数数量"这种需求时，会逐个 Read() 把 50 个文件全读进 context，然后在脑子里数函数。50 次 Read()，700 KB context 被吃掉，数完还要保证一个不漏。

Context Mode 的做法：写一段脚本，让沙箱执行：

```js
ctx_execute("javascript", `
  const fs = require('fs');
  const files = fs.readdirSync('src').filter(f => f.endsWith('.ts'));
  const results = files.map(f => ({
    file: f,
    lines: fs.readFileSync('src/' + f, 'utf8').split('\n').length,
    functions: (fs.readFileSync('src/' + f, 'utf8').match(/function\s+\w+/g) || []).length
  }));
  console.table(results);
`);
```

→ context 消耗从 700 KB 降到 3.6 KB。不是压缩，是不进。

这个范式的本质：**让代码处理数据，让模型只做决策。** 14 个支持的平台上都强制执行这个范式，把"先读文件再分析"的习惯改成"先写脚本再读结果"。

### 2.4 Output Compression——输出减肥

输出端压缩的规则很直接：

- 删掉冠词/填充词（just/really/basically/quite）
- 删掉客套话和过度保守的措辞
- 用 `[thing] [action] [reason] [next step]` 的结构替代冗长造句
- **自动展开保留给**：安全警告、不可逆操作、用户可能困惑的场景

实测效果：输出 token 减少约 65-75%，同时不降低技术准确性——因为删掉的是"社交语言"而非技术信息。

## 3. 一个真实任务流过系统

这里用一个常见场景展示四组件如何协同：**在大型 TypeScript 项目中修复一个跨模块的类型错误。**

```text
时间线：一次 bug 修复中的 Context Mode 流转

1. 用户说：「src/utils 下所有文件里有一个类型错误，TypeScript 编译报错」

2. PreToolUse → Context Saving 拦截：
   - Agent 调用 bash 执行 tsc --noEmit，输出 127 KB 的编译错误日志
   - 沙箱拿到原始输出，context 里只注入：
     「编译错误摘要：src/api/types.ts:42 类型不匹配，2 处警告，其余文件无错误」

3. Think in Code 切入：
   - Agent 不是逐行看 127 KB 的错误日志
   - 而是让沙箱执行脚本，提取所有报错的 import 链：
     ctx_execute("javascript", `从 tsc 输出中提取所有涉及文件的 import 关系`)

4. 上下文端节约：
   - 本该用约 800 KB 的原始工具输出 + 多次 Read()
   - 实际只用了 ~12 KB 的摘要 + 脚本输出

5. Session Continuity 记录：
   - 「[edit] src/api/types.ts L42: 将 string|null 改为 string|undefined」
   - 「[git] commit "fix: type narrowing in api types" (a3f8d1c)」
   - 「[task] 修复完成，运行 tsc 验证通过」

6. 用户说「等下，这会影响 user module 里的调用」→ compact 触发
   - 压缩后模型不记得具体改了哪行
   - 但 Session Continuity 从 SQLite 捞出：最后一次编辑在 types.ts L42，git commit a3f8d1c

7. 模型基于恢复的事件继续改 user module，上下文干净无污染
```

把这个流转看完，一句话就够了：Context Mode 不是让 agent"变聪明"，而是让 agent"不丢信息"。修复 bug 的能力本来就有，只是之前 40% 的上下文被原始数据占了，能力没机会发挥。

## 4. 支持平台

以下平台支持 hook 自动路由强制执行：

- **Claude Code**：最完整的集成。插件市场安装，自动注册 PreToolUse / PostToolUse / PreCompact / SessionStart 四个 hook，暴露 11 个 MCP 工具和 5 个 slash 命令（ctx-stats、ctx-doctor、ctx-upgrade、ctx-purge、ctx-insight）
- **Gemini CLI**：通过配置文件方式，需要 Node.js 18+
- **Cursor**：Cursor 自行管理 MCP 配置
- **Cline**：自动 hook 注册
- **Roo**：自动 hook 注册
- **Zed**：需手动复制路由文件

Claude Code 的整合深度远超其他平台——原因是 Claude Code 的插件系统在 hook 控制、状态栏扩展、slash 命令这几个维度上开放度最高。

## 5. Claude Code 安装与配置

### 前置条件

- Claude Code v1.0.33+（运行 `claude --version` 确认）
- 若版本过低：`brew upgrade claude-code` 或 `npm update -g @anthropic-ai/claude-code`

### 安装命令

```bash
/plugin marketplace add mksglu/context-mode
/plugin install context-mode@context-mode
```

重启 Claude Code，或执行 `/reload-plugins`。

### 验证安装

```
/context-mode:ctx-doctor
```

Doctor 会逐项验证：runtime 环境、hook 注册状态、FTS5 数据库是否可写、插件注册、版本号。所有检查项应显示 `[x]`。如果某条是 `[ ]`，直接看对应的修复建议——大多数是版本或路径问题。

### 启用状态栏

插件 manifest 不包含 statusLine 声明，需要手动写入 `~/.claude/settings.json`：

```json
{
  "statusLine": {
    "type": "command",
    "command": "context-mode statusline"
  }
}
```

重启后状态栏显示三组数字：`$ saved this session · $ saved across sessions · % efficient`，可以实时看到节省了多少 token。

## 6. 性能数据解读

官方报告了三组核心数据。下面不是复述，而是解释这些数字分别反映系统的哪个部分。

| 指标 | 数值 | 反映的系统部分 | 不能推出的结论 |
|------|------|--------------|--------------|
| **工具数据 reduction** | 315 KB → 5.4 KB（98%） | Context Saving 的摘要压缩有效性，只有工具输出量级大于摘要所需信息量时才有这个比例 | 不表示所有场景都能达到 98%，文件少或输出本身就短时 reduction 会显著下降 |
| **输出 token reduction** | 65-75% | Output Compression 对模型自然语言冗余度的削减效果——填充词和客套话占了模型输出的相当比例 | 不表示模型输出变短就一定更好，代码生成和精确指令本身不冗余，压缩不影响它们 |
| **30 分钟会话上下文清洁度** | 从 40% 污染到接近零 | 四组件协同的整体效果：入站拦截 + 出站压缩 + 缓存恢复，三者加在一起才能把这个数字压到接近零 | 不表示所有会话都有 40% 污染，轻度使用场景本身工具调用密度低，提升空间也小 |

关于 90 天使用数据：`ctx-insight` 命令暴露 90 个指标、37 种洞察模式、4 个复合评分（生产力、质量、委托度、上下文健康），覆盖 23 个事件类别。有这些统计样本撑着，上面的 reduction 数字不是单次快照，而是有足够收敛依据的结论。

## 7. 与传统 RAG 的边界

把 Context Mode 和传统 RAG 放一起对比容易得出"都是检索存储"的误读。实际上两者解决完全不同的问题。

| 维度 | Context Mode | 传统 RAG |
|------|-------------|----------|
| **触发时机** | 工具返回时即时拦截（不进入 context） | 用户提问时检索（已进入 context） |
| **数据结构** | SQLite 事件日志 + FTS5 全文索引 | 向量数据库 + embedding |
| **检索方式** | BM25 词频评分，精确匹配事件 | 向量相似度，语义匹配段落 |
| **输出管控** | 有（逐次模型输出压缩） | 无（RAG 本身不干预模型输出） |
| **设计意图** | 管理 Agent 会话的上下文收支 | 为问答场景补充外部知识 |

一句话边界：**RAG 往上下文里加东西，Context Mode 控制什么东西能进上下文。**

如果你的场景是"给我一个知识库问答系统"，RAG 更合适。如果你的场景是"我的 Claude Code 跑到 30 分钟后明显变蠢了"，Context Mode 才是对症的。

## 8. 谁该用、谁不该用

### 马上值得装的

- 每天用 Claude Code 超过 2 小时的开发者——token 节省直接等于 API 费用的节省
- 在大型代码库里工作、工具调用密集的团队——上下文污染会随着项目规模非线性增长
- 长期会话场景（一次任务跨数小时甚至数天）——Session Continuity 的恢复能力在这种场景下最有价值
- 关注 token 预算的团队管理者——Context Mode 的 observability 让你知道 token 花在了哪里

### 可以先等等的

- 偶尔用 AI 编程、每次会话不到 15 分钟——污染还没累积就结束了，提升有限
- 小项目、文件数量级在几十以内——Think in Code 的收益不显著
- 输出压缩的副作用对你的场景不可接受——如果你的应用要求模型输出保持"正常对话"，压缩后的穴居人风格可能不适配

### 不要用的

- 不支持 MCP hook 的 AI 编程工具——核心机制依赖 hook 拦截，平台不支持就无效
- 需要模型输出完整解释的教学/演示场景——压缩会把解释性文字删掉

## 9. 局限性与注意事项

1. **平台依赖**：目前只支持列入 README 的特定平台，走的是 MCP hook，不是通用方案
2. **Claude Code v1.0.33+ 硬性要求**：SessionStart hook 在老版本不可用，且插件注册机制也依赖这个版本
3. **`--continue` 是把双刃剑**：恢复记忆的同时也恢复了上一次未解决的问题状态，如果上一个 session 已经跑偏，继续可能只是错得更久
4. **脚本优先范式有学习成本**：习惯视觉化读文件的开发者，切换到"用脚本描述需求"需要适应期
5. **输出压缩牺牲对话自然度**：如果你需要保留模型输出的完整上下文给团队成员 review，被压缩过的输出可读性会下降

## 10. 常见问题

**Q1：Context Mode 和 RAG 能一起用吗？**

可以，而且不冲突。RAG 管"给模型补充什么知识"，Context Mode 管"什么东西不该吃掉上下文窗口"。对 Claude Code 这类 Agent，两者互补：RAG 往 context 里加项目文档，Context Mode 确保工具调用不会把这些文档挤出去。

**Q2：输出压缩后模型会变得更"笨"吗？**

实测结论：不会。压缩删的是填充词和客套话，技术信息、代码块、命令都原样保留。真正需要模型详细解释的场景（安全警告、不可逆操作）会自动展开。压缩的对象是"社交语言"，不是"技术语言"。

**Q3：不使用 `--continue` 时，数据真的完全清理了吗？**

是的。不传 `--continue` 时 session 结束立刻清理 SQLite 中的相关记录。如果你希望保留分析数据（不包含具体代码内容），可以定期运行 `ctx-purge` 手动控制清理策略。

**Q4：团队环境下，不同成员的状态栏数据会互相影响吗？**

不会。Context Mode 的数据全存在本地 `~/.claude/` 目录下，没有云端同步。每个开发者的上下文数据独立，互不干扰。

**Q5：脚本优先范式里，如果脚本写错了怎么办？**

脚本本身也会消耗 token，但写错了一个脚本重写的 token 成本（几十 KB）远低于把 50 个文件全读进 context（700 KB）。关键是：错误成本是可控的，而正确的收益是持久的。

**Q6：`ctx-doctor` 检查项显示 `[ ]` 怎么处理？**

大多数失败项有明确的修复提示。最常见的三项：
- hook 未注册 → 确认执行过 `/plugin install`
- FTS5 数据库不可写 → 检查 `~/.claude/` 目录权限
- 版本过低 → `brew upgrade claude-code`

## 11. 自测清单

装好之后，用这个清单确认一切正常：

- [ ] `ctx-doctor` 全部显示 `[x]`
- [ ] 初次会话中做一次工具调用（如 `bash ls`），状态栏显示上下文节省数据
- [ ] 用 `/context-mode:ctx-stats` 查看当前 session 的统计
- [ ] 让 agent 执行一段统计脚本（如统计文件行数），观察它是否自动使用 `ctx_execute` 而非逐个 Read()
- [ ] 开启一个新 session 并带上 `--continue`，确认 agent 能回忆起上一 session 的状态
- [ ] 结束 session 不带 `--continue`，确认 `ctx-purge` 后日志被清理

## 总结

把 Context Mode 总结成"上下文优化工具"没错，但这个说法避开了它真正做的事——它重新划分了 AI 编程 Agent 该把什么当对话、该把什么当数据。

四组件分了四条线，但背后是同一件事：把 LLM 从数据处理器变回决策者。在这种设计下，上下文窗口不再是"能塞多少塞多少"的垃圾桶，而是花钱买来的决策空间，必须精打细算。

如果你的 Claude Code 会话经常跑到一半开始"犯傻"——不是模型不行，是上下文被吃掉了。装 Context Mode，然后看状态栏上那行数字：那是你的上下文窗口真正被解放出来的额度。

---

**项目信息**

- GitHub：[mksglu/context-mode](https://github.com/mksglu/context-mode)
- Stars：12,712
- 语言：TypeScript
- License：ELv2（Elastic License v2）
- 推送时间：2026-05-05
- HN 讨论：[news.ycombinator.com/item?id=47193064](https://news.ycombinator.com/item?id=47193064)（570+ points）
- Discord：[discord.gg/DCN9jUgN5v](https://discord.gg/DCN9jUgN5v)
