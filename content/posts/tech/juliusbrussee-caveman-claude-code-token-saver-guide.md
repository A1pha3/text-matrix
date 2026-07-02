---
title: "caveman：让 Claude Code 用 1/4 的 token 把话说完"
date: "2026-07-02T21:08:42+08:00"
lastmod: "2026-07-02T21:08:42+08:00"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "AI Agent", "MCP", "提示词工程", "开源工具"]
description: "caveman 让 Claude Code 等 30+ 编程代理以洞穴人体回复，输出 token 削减 65-75%，技术准确性不变。本文拆解多档强度、钩子持久化与 Auto-Clarity 边界。"
weight: 1
author: text-matrix
---

# caveman：让 Claude Code 用 1/4 的 token 把话说完

`JuliusBrussee/caveman` 是 GitHub 上 Star 增速最快的 AI Agent 工具之一（截至 2026-07-02 达 79,671 Star，单日新增 866）。它做的事情非常窄：让 Claude Code、Codex、Gemini CLI、Cursor、Windsurf、Cline、Copilot 等 30+ 编程代理在保持技术准确性的同时，把自然语言回复压缩成"洞穴人"风格——砍掉冠词、连接词、客套话、修饰性副词，只保留结论与关键路径。

表面上看这是一个"提示词调优"项目，往深看却是一个完整的"代理行为持久化 + 跨厂商分发"工程。它的真正价值不在那句 `useMemo` 怎么压成 5 个 token，而在三个常被忽略的设计选择：

1. **多档强度 + 用户母语保留**：lite / full / ultra / wenyan 四档压缩力度，且压缩的是"风格"不是"语言"，写葡萄牙语的开发者拿到的依然是葡萄牙语洞穴人。
2. **钩子级持久化**：Claude Code 的 `SessionStart` + `UserPromptSubmit` 钩子写一个 flag 文件，让代理从会话第一条消息就处于压缩模式，不需要每轮说"请用 caveman 模式回复"。
3. **Auto-Clarity 自动降级**：碰到安全警告、不可逆操作、容易歧义的多步序列时，自动退回到正常语言描述关键步骤，说完再回到洞穴体。

## 系统地图：caveman 不是单个 skill，是一套

`caveman` 的 `skills/` 目录下挂着 7 个独立子技能，互不依赖但共用同一套风格 DNA：

| 子技能 | 触发命令 | 职责 |
|---|---|---|
| `caveman` | `/caveman [lite\|full\|ultra\|wenyan]` | 压缩每一次回复，强度档位黏附到会话结束 |
| `caveman-commit` | `/caveman-commit` | Conventional Commit 消息，主题行 ≤50 字符，强调 Why 而不是 What |
| `caveman-review` | `/caveman-review` | PR 一行式评审：`L42: 🔴 bug: user null. Add guard.` |
| `caveman-stats` | `/caveman-stats` | 读取 Claude Code 会话日志，统计本会话与累计节省 token，含 USD 折算 |
| `caveman-compress` | `/caveman-compress <file>` | 把 `CLAUDE.md` 这类记忆文件改写成洞穴体，代码 / URL / 路径字节级保留 |
| `caveman-shrink` | MCP middleware | 包装任意 MCP server，压缩工具描述 |
| `cavecrew-*` | 子代理 | investigator / builder / reviewer 三种洞穴人子代理，比 vanilla 少约 60% token |

子技能之间通过同一个 `bin/install.js` 安装入口分发，钩子配置在 `src/hooks/`，对外只暴露一份 install 命令：

```bash
# macOS / Linux / WSL
curl -fsSL https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.sh | bash
```

~30 秒扫描本机已装的代理，逐个走代理原生安装路径（plugin / extension / rule file / `npx skills add`），未装的代理自动跳过，可重复运行。

## 关键机制一：四档强度 + 母语保留

`skills/caveman/SKILL.md` 把规则分成两个互不冲突的维度——**档位（强度）** 与 **语言（保留用户母语）**。

### 档位维度

| 档位 | 处理逻辑 |
|---|---|
| `lite` | 只去填充词和模糊语，保留冠词与完整句。适合刚开始使用、怕读不懂压缩结果的开发者 |
| `full`（默认） | 去冠词、接受片段、用短同义词（big / fix / drop）。经典洞穴体 |
| `ultra` | 缩写散文词（DB / auth / config / req / res / fn / impl），但代码符号、函数名、API 名、错误字符串**绝不缩写** |
| `wenyan-lite` / `wenyan-full` / `wenyan-ultra` | 文言文三档，最多可压到原长 10-20%。古典句式、动词前置、之主语省略 |

一个关于 React 重渲染的解释在三档之间的对照：

```text
lite:   "Your component re-renders because you create a new object reference each render. Wrap it in `useMemo`."
full:   "New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`."
ultra:  "Inline obj prop → new ref → re-render. `useMemo`."
```

文言文档则把 `useMemo` 之外的连接词也都换成古典结构：

```text
wenyan-full:  "每繪新生對象參照，故重繪；以 useMemo 包之則免。"
wenyan-ultra: "新參照→重繪。useMemo Wrap。"
```

### 语言维度

规则里有一条专门处理语言保留："Preserve user's dominant language. User write Portuguese → reply Portuguese caveman. Compress the style, not the language."

葡萄牙语版的同一个解释：

> "Novo ref de objeto cada render. Prop inline = novo ref = re-render. Envolva com `useMemo`."

这一条的实际意义是：洞穴体不是一个"翻译器"，而是"句式改写器"。压缩的边界严格框定在 **句式与冗余**，技术术语、代码块、API 名、CLI 命令、Conventional Commit 类型关键字（feat / fix / ...）以及报错原文一律保留原文。

## 关键机制二：钩子级持久化（Claude Code 特供）

对于按次命令触发（`/caveman`）的代理，每次开新会话都要喊一次。caveman 在 Claude Code / Codex / Gemini CLI 上实现了**自动激活**：

```text
SessionStart hook ──writes "full"──▶ $CLAUDE_CONFIG_DIR/.caveman-active ◀──writes mode── UserPromptSubmit hook
                                                       │
                                                    reads
                                                       ▼
                                              caveman-statusline.sh
                                            [CAVEMAN] / [CAVEMAN:ULTRA] / ...
```

`SessionStart` 在每个会话开始时往 `$CLAUDE_CONFIG_DIR/.caveman-active` 写一个 flag 文件（fallback 到 `~/.claude/.caveman-active`），`UserPromptSubmit` 钩子负责把当前强度档位同步到同一个文件，`caveman-statusline.sh` 读取后渲染到 Claude Code 状态栏：`[CAVEMAN] ⛏ 12.4k`（12.4k 是累计节省 token 数）。

`src/hooks/package.json` 里固定声明 `{"type": "commonjs"}`，因为当用户 `~/.claude/package.json` 来自另一个 ESM 插件时，`require()` 会抛 `ReferenceError: require is not defined in ES module scope`。这是一个看起来很边缘、但实际每天都在踩的坑。

对 OpenClaw 这类不自动注入 skill 的网关，caveman 走另一条路：在 `~/.openclaw/workspace/SOUL.md` 末尾追加 marker-fenced 块，保留 sentinel `Respond terse like smart caveman`，块大小远低于 OpenClaw 12K/文件 的限制。这样 lobster 从第一条消息就是洞穴体，不需要每会话 `/caveman`。

## 关键机制三：Auto-Clarity 自动降级

洞穴体的最大风险是**压缩掉关键安全信息**。caveman 用一条显式规则处理这个边界——"Drop caveman when"：

- 安全警告
- 不可逆操作确认
- 多步序列、片段顺序与省略连词会导致误读的场合
- 压缩本身制造了技术歧义（例如 `"migrate table drop column backup first"` 这种没有冠词和连词就无法判断顺序的句子）
- 用户主动要求澄清

降级处理不是关闭洞穴体，而是**在该段回到正常语言、说完再回到洞穴体**：

```text
> **Warning:** This will permanently delete all rows in the `users` table and cannot be undone.
> ```sql
> DROP TABLE users;
> ```
> Caveman resume. Verify backup exist first.
```

这条规则让洞穴体的安全边界比它看上去更清晰：**压缩的是冗余表达，不是关键判断**。

## 任务流案例：压缩一份 CLAUDE.md

`caveman-compress` 子技能是这套工具链里最容易被低估的一个。CLAUDE.md 是 Claude Code 每会话注入的项目级 system prompt——它**每会话都会被读一次**，所以每会话的输入 token 都跟它的长度成正比。

`caveman-compress` 的工作流：

1. 用户执行 `/caveman-compress CLAUDE.md`
2. 读取目标文件，对散文段落做风格压缩，对代码块 / URL / 文件路径做字节级保留
3. 写回原文件
4. `/caveman-stats` 在下一次会话开始时显示"input tokens reduced by N%"

仓库 README 给出的真实压缩样本：

| 文件 | 原长 | 压缩后 | 节省 |
|---|---:|---:|---:|
| `claude-md-preferences.md` | 706 | 285 | 59.6% |
| `project-notes.md` | 1145 | 535 | 53.3% |
| `claude-md-project.md` | 1122 | 636 | 43.3% |
| `todo-list.md` | 627 | 388 | 38.1% |
| `mixed-with-code.md` | 888 | 560 | 36.9% |
| **平均** | **898** | **481** | **46%** |

平均 46% 节省直接体现在**每一次会话的输入侧**——这是单次会话节省几十 token 的回复侧压缩无法达到的杠杆效应。

## benchmark 解读：65% 平均、范围 22-87%

`benchmarks/` 目录里跑的是真 Claude API 计数，`evals/` 跑的是三臂对照（baseline / terse / caveman），caveman 不跟 verbose 默认比，跟 `Answer concisely.` 这种 terse 提示比——这样得到的差值才是洞穴体相对**已经做简洁优化的回复**的额外收益。

| 任务 | Normal | Caveman | Saved |
|---|---:|---:|---:|
| Explain React re-render bug | 1180 | 159 | 87% |
| Fix auth middleware token expiry | 704 | 121 | 83% |
| Set up PostgreSQL connection pool | 2347 | 380 | 84% |
| Explain git rebase vs merge | 702 | 292 | 58% |
| Refactor callback to async/await | 387 | 301 | 22% |
| Architecture: microservices vs monolith | 446 | 310 | 30% |
| Review PR for security issues | 678 | 398 | 41% |
| Docker multi-stage build | 1042 | 290 | 72% |
| Debug PostgreSQL race condition | 1200 | 232 | 81% |
| Implement React error boundary | 3454 | 456 | 87% |
| **平均** | **1214** | **294** | **65%** |

理解这些数字时需要分清三件事：

- **测的是什么**：是**输出 token**，不是 thinking / reasoning token。caveman 只让"嘴"变小，不让"脑"变小。
- **范围说明**：22% 是把已有强结构的目标（"Refactor callback to async/await"）再压只能压出 22%；87% 来自"Explain React re-render bug"这种以解释为主、原答案本就啰嗦的任务。
- **不可外推**：这些数字不是单一任务的最终答案，而是在 10 个固定任务上的平均。把洞穴体套到你的实际任务上，效果取决于**原回复里的冗余比例**——冗余越多，省得越多。

README 还引用了 2026 年 3 月的一篇论文 [Brevity Constraints Reverse Performance Hierarchies in Language Models](https://arxiv.org/abs/2604.00025)，结论是约束大模型回答简短时部分 benchmark 上准确率反而提高 26 点。"Verbose not always better" 不是口号，是论文结果。

## 适用边界与采用顺序

caveman 不是银弹，更适合作为**组合工具**而不是默认风格。建议的采用顺序：

1. **从 `caveman-stats` 开始**。先跑一周，看到底有多少 token 浪费在冗余表达上。如果会话量本身不大，节省金额小于安装成本，不必装。
2. **先开 `lite`**。让代理去掉填充词和模糊语，但保留句式。这一档对可读性影响最小，是验证工具链健康度的好起点。
3. **再切 `full`**。这是默认档，也是大部分团队最终会停留的档位。可读性下降明显但仍在可读范围内。
4. **`ultra` 与 `wenyan` 按团队文化取用**。`ultra` 适合 DevOps / 故障响应场景；`wenyan` 适合个人审美偏好，对协作可读性挑战较大。
5. **用 `caveman-compress` 处理 `CLAUDE.md`**。这是 ROI 最高的一步——输入侧杠杆效应远大于输出侧。
6. **保留 `/caveman off` 出口**。安全审计、对外汇报、合规披露等场景必须切回正常语言。

需要明确**不适合 caveman** 的场景：

- 给非技术读者的解释性回复（洞穴体没有客套与铺垫，可能被认为不礼貌）
- 教学场景（学习者需要看到完整的推理链）
- 跨文化团队的正式沟通（被误读的概率上升）

## 仓库元信息

| 字段 | 值 |
|---|---|
| 仓库 | `JuliusBrussee/caveman` |
| 主语言 | JavaScript |
| Stars | 79,671（2026-07-02，单日 +866） |
| 协议 | MIT |
| 子技能数 | 7（caveman / caveman-commit / caveman-review / caveman-help / caveman-stats / caveman-compress / cavecrew） |
| 支持代理数 | 30+ |
| 相关项目 | `JuliusBrussee/caveman-code`（完整终端编码代理，全链路洞穴化） |

如果对"洞穴人风格在 Claude Code 里到底能不能稳定生效"有疑问，仓库 `benchmarks/` 与 `evals/` 都有可复现脚本——这一点比大多数"AI 写代码提效"工具的"我们有数据但不给脚本"要扎实。