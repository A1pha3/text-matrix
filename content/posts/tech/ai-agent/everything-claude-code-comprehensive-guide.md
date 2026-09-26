---
title: "Everything Claude Code：从入门资料库到跨终端 Agent 工作流系统"
date: "2026-04-02T07:35:00+08:00"
lastmod: "2026-09-26T12:00:00+08:00"
slug: everything-claude-code-comprehensive-guide
github_repo: "affaan-m/ECC"
source_key: "gh:affaan-m/ECC"
author: "钳岳"
canonical: "https://txtmix.com/posts/tech/ai-agent/everything-claude-code-comprehensive-guide/"
aliases:
  - /posts/tech/everything-claude-code-comprehensive-guide/
  - /posts/tech/everything-claude-code-agent-harness-performance/
categories: ["技术笔记"]
topics: ["coding-agent"]
tags: ["Claude Code", "AI 编程", "Anthropic", "Agent"]
description: "基于 affaan-m/ECC 当前公开仓库状态，讲清这个项目如何从一份 Claude Code 入门资料演进为跨 Codex、Claude Code、Cursor 等终端的 Agent 工作流系统，以及 skills、instincts、memory、security 这些资产各自解决什么问题。"
---

# Everything Claude Code：从入门资料库到跨终端 Agent 工作流系统

> 预计阅读时间：18 分钟 | 难度：⭐⭐⭐

无论你最初是被"Everything Claude Code"这个名字吸引，还是已经在用 Claude Code 想找一套更完整的配置，都可能低估了这个仓库现在的样子。它早已不是一份"怎么装、怎么用"的资料合集，而是一套跨终端的 Agent 工作流系统——同一份 skills、hooks、rules，经过各自的适配层，能落到 Claude Code、Codex、Cursor、Gemini 等十几种 editing harness 上。

下文先给一张系统地图，再拆开里面的机制，用一个真实任务把它们串起来，最后说清楚哪些人该用、怎么入手。文中所有数字与引用均以 2026-09-26 实测的仓库 main 分支为口径。

---

## 一、先看这张地图

仓库里规整的内容，大致按四层组织。每一层回答一个不同的问题：

| 层 | 装在哪 | 回答的问题 |
|------|----------|----------|
| 基础使用 | 引导式安装、`install.sh`、`npx ecc-universal` | 怎么把系统装进某个 harness |
| 工作流资产 | `.claude/skills`、instincts、memory hooks | 怎么让 Agent 用得有章法 |
| 安全边界 | AgentShield、密钥扫描、`.gitignore` | 怎么让 Agent 不踩坑 |
| 跨终端扩展 | `.codex`、`.cursor`、`.gemini` 等十几个适配器目录 | 怎么让同一套资产换工具也能用 |

这套结构的思路是**核心资产只写一份，各终端靠适配器分发**：仓库根目录是唯一事实来源，`.cursor/`、`.codex/` 这些平台目录负责把同一份技能和钩子翻译到各家 harness 的目录约定里，而不是各自维护一套副本。

不过"装到多个终端"不等于"功能完全一样"。README 的平台支持矩阵把这层意思说得很直白：各 harness 的状态从 stable 到 instruction-only 分了五档，并注明这些是"capability statements, not marketing tiers"（能力声明，不是营销分层）。本文第六节展开这张矩阵。

---

## 二、这个仓库到底是什么

### 2.1 项目基本信息（GitHub API 2026-09-26 实测）

| 属性 | 值 |
|------|-----|
| GitHub | [affaan-m/ECC](https://github.com/affaan-m/ECC) |
| 原仓库名 | affaan-m/everything-claude-code（已更名） |
| Stars | 267,612 |
| Forks | 39,975 |
| Open Issues + PR | 235 |
| Commits | 2,812 |
| License | MIT |
| 主要语言 | JavaScript |
| 默认分支 | main（最新提交 e482e57，2026-09-24） |
| 官网 | [ecc.tools](https://ecc.tools) |

仓库描述自述为 "the agent harness performance optimization system"，覆盖 Claude Code、Codex、Opencode、Cursor 等。README 里自称 **Agent Harness Operating System**，当前目录实测是 68 个 agents、292 个 skills、94 个 commands。这个项目的活跃度值得注意：它基本由一位维护者（GitHub ID affaan-m）以周更节奏推进，README 原话是 "a single maintainer ships weekly across 7 harnesses"——一个人维护着横跨七种 harness 的安装与适配层。

另一个对中文读者友好的事实：README 有包括简体中文在内的 13 种语言版本，仓库根目录的 `README.zh-CN.md` 即中文版。

### 2.2 从"资料库"到"操作系统"

这个改名的过程，恰好说明了项目定位的迁移。早期它确实是一份 Claude Code 的社区资料库，收录命令、规则和技巧。但随着内容膨胀，作者发现真正值钱的不是"一条条命令说明"，而是把 skills、hooks、rules、memory 组合成一套**可复用的工作流层**，并且能装到不同 harness 上。

所以现在你看到的是：

- 一份原始代码仓库（README 原话："This repo is the raw code. The guides explain everything."），真正的讲解在配套的 The Shorthand Guide、The Longform Guide、The Security Guide 三份指南里。
- 一个按 harness 分层的目录：`.claude`、`.codex`、`.cursor`、`.gemini`、`.kimi`、`.opencode`、`.codebuddy`、`.hermes`、`.trae`、`.zed`、`.qwen`、`.openclaw` 等十几个适配器目录，加上 `.claude-plugin`（插件市场清单）。
- 一套 npm 包（`ecc-universal`、`ecc-agentshield`）和一个 GitHub App（ECC Tools），把仓库能力变成可安装、可升级的产物。

ECC 对外有三个刻意不同名的标识符，README 专门用一节解释它们不可互换：GitHub 源仓库叫 `affaan-m/ECC`，Claude 插件市场的标识是 `ecc@ecc`（为了压短工具名和斜杠命令的命名空间），npm 包则沿用 `ecc-universal`。老的教程里出现的长标识符只作为历史别名存在。

版本方面有一个值得留意的小脱节：截至 2026-09-26，仓库 `VERSION` 文件是 2.2.2，CHANGELOG 记录 2.2.2 于 2026-09-15 发布；而 npm registry 上 `ecc-universal` 的 latest 还是 2.2.1（2026-09-08 更新）。README 推荐 `npx ecc-universal@2.2.2 setup` 这个写法正是为了绕开这种脱节——显式锁版本，不依赖 latest 标签。

## 三、核心资产：skills、instincts、memory、security

仓库反复提到的四类资产，不是四个并列的功能，而是四个不同职责的模块。

### 3.1 Skills——按需加载的工作流

Skills 是最容易理解的一层：一个 skill 就是一套提示词、规则和有时会带上脚本的文件夹（`SKILL.md` 加 YAML frontmatter）。调用它，等于给 Agent 一份"这个任务该怎么做"的完整说明。

当前 main 分支实测 292 个 skill，覆盖 TypeScript、Python、Go、Java、Kotlin、Rust、C++、Swift、Perl 等多个语言生态，也包含市场研究、投资人材料、内容引擎、视频处理（VideoDB）、前端幻灯片等业务领域的技能。官方列表上排在前面的通用工作流是 `tdd-workflow`（测试驱动开发）、`security-review`（安全审查）、`verification-loop`（持续验证）这几个。

值得注意的两点：其一，skill 是按任务类型组织的，不是按工具组织的，同一个 `SKILL.md` 格式在 Claude Code、Codex、OpenCode 里都能被识别，只是落在各自的目录约定里；其二，这个仓库正在向"skills-first"迁移——`commands/` 里的 94 个斜杠命令被官方定位成"便利入口和兼容垫片"（compatibility shims），`/tdd`、`/eval` 这类已退役的短名命令被挪进 `legacy-command-shims/` 归档，需要显式 opt-in 才会启用，新工作流一律先落在 `skills/`。

### 3.2 Instincts——带置信度的行为惯性

Instincts 和 skills 的区别在"显式与隐式"。Skill 是用户主动点名调用的；Instinct 是 Agent 从真实会话中沉淀下来的默认行为，比如"这个项目改完代码要跑某条测试命令"。README 的定义是 "patterns learned from real sessions with confidence scores"——从真实会话学到的模式，带置信度分数。

它的机制比早期版本工程化得多：continuous-learning-v2 管道在会话结束时提取模式，存为带置信度的 instinct；下次会话开始时（SessionStart hook）按"置信度 + 与当前项目和语言栈的相关性"排序，只把得分最高的一小批注入上下文。注入行为全部可以用环境变量调节：`ECC_MAX_INJECTED_INSTINCTS` 控制条数（默认 6 条），`ECC_INSTINCT_CONFIDENCE_THRESHOLD` 控制置信度门槛（默认 0.7），`ECC_INSTINCT_RELEVANCE_RANKING` 控制是否开启相关性加权。

配套还有一组管理命令：`/instinct-status` 查看学到的 instinct，`/instinct-import`、`/instinct-export` 负责导入导出，`/evolve` 把反复出现的 instinct 聚类升级成 skill，`/prune` 清理过期的待定项。从 instinct 到 skill 的这条晋升通道，是这个系统"越用越顺手"的核心机制。

### 3.3 Memory——跨会话的两层记忆

Memory 是仓库里最工程化的一块，现在分成两层。

第一层是 hooks 驱动的会话摘要：会话开始（SessionStart）时把上次的上下文加载进来，会话结束（Stop）时把摘要写回，这样下次会话不用重新解释一遍项目背景。这些数据默认存在 `~/.claude` 下的 `session-data/` 等目录里；如果你在同一台机器上同时用 Claude Code 和 Cursor，可以设 `ECC_AGENT_DATA_HOME` 给两个环境各划一个数据根目录，避免互相覆盖。

第二层是 2.2 版新增的统一 Memory Vault：一条 `ecc memory` 命令行界面，把持久上下文存成 `ecc.memory.v1` 格式的本地 Markdown 文档——项目记忆在 `.ecc/memory/`，用户记忆在 `~/.ecc/memory/`。它的卖点是跨 harness 搬运：Claude、Codex、Hermes、Kimi 等终端共用同一种可检查的 Markdown 格式，`ecc memory search "authentication migration" --target-harness codex` 这样的命令可以把一段上下文定向投递给另一个终端。项目记忆由 fail-closed 的 `.gitignore` 保护，防止敏感内容被无意提交。

Vault 有条信任边界声明值得记住：README 原话是 "Memory is unreviewed context, not executable policy"——记忆是未经审查的上下文，不是可执行的策略，重要结论要对回权威来源，再把采纳的知识固化进受治理的项目文档。可选的 `ecc-memory-mcp` 服务器暴露同样的 save/search/read/doctor 接口，默认不自启。

### 3.4 Security——Agent 的安全边界

Agent 能读文件、跑命令，安全就变成硬需求。仓库这一层包含：

- **AgentShield**：独立的 npm 包 `ecc-agentshield`，扫描对象是 harness 配置本身——提示词、hooks、MCP 配置、权限设置、密钥和 agent 文件。
- **密钥检查**：扫描代码里的硬编码 token、API key。
- **`.gitignore` 与 `.mcp.json` 治理**：避免敏感信息进版本库。2.2 起默认启用的 MCP 连接器收缩到只留 `chrome-devtools` 一个，此前的六个默认连接器全部转为 opt-in。
- 配套的 Security Guide，讲攻击向量、沙箱、CVE、审批边界、可观测性和 kill switch。

README 顶部有一条 WARNING 级别的声明：非官方渠道的转发和镜像不被维护也不被审查，可能带恶意软件，安装只走官方渠道——GitHub 仓库、两个 npm 包、GitHub App（`github.com/apps/ecc-tools`）、插件标识 `ecc@ecc`、官网 ecc.tools。

## 四、一个任务如何流过系统

用一个具体例子把上面四层串起来：你接手一个不熟悉的 TypeScript 项目，想让它修一个 bug。

1. **启动**：SessionStart hook 加载上次会话摘要，按置信度挑出相关的 instinct 一并注入，Agent 恢复对项目的记忆，不用你重新交代背景。
2. **读上下文**：Agent 读取仓库根目录的 `AGENTS.md`——README 把它定为跨工具的通用指令文件，Claude Code、Cursor、Codex、OpenCode 都读它（GitHub Copilot 例外，用 `.github/copilot-instructions.md`）——拿到技术栈、代码规范、约束。
3. **复现并调用 skill**：按官方工作流，先写一个能复现 bug 的失败测试，然后进入 `tdd-workflow` skill，Agent 收到"先测试后实现"的完整流程说明。
4. **执行并验证**：Agent 按流程走 RED → GREEN → REFACTOR，改完跑测试、lint 和类型检查；hooks 在工具事件上做确定性检查（比如拦截 `console.log`），不依赖模型自觉。
5. **收尾**：Stop 阶段 hook 把这次会话的摘要写回，continuous-learning 管道评估本次会话有没有值得沉淀的模式，有则存为候选 instinct，下次会话能接着用。

这个流程里，四层资产各司其职：memory 管前后衔接，instincts 管默认行为，skills 管任务方法，security 在背后防止它乱动不该动的东西。README 把这套节奏压缩成一行：

```text
plan -> test -> implement -> review -> verify -> remember -> improve
```

## 五、数据与规模怎么读

仓库公开了几个数字，需要分清它们各自说明什么：

- **Stars 26.8 万 / Forks 4 万**：反映的是关注度和二次开发的规模，**不能**直接推出"它的配置在你的项目里也一定好用"。
- **68 agents / 292 skills**：说明覆盖面广，但**不能**推出"每个都适合你"——大量技能是作者在真实产品迭代中为特定场景沉淀的，与你的技术栈无关的部分装了也是负担。
- **"battle-tested across multiple production applications"**：这是作者的自我描述。他在多个生产项目里跑过这套配置，2025 年 9 月还拿过 Anthropic x Forum Ventures 黑客松冠军（用 Claude Code 做出 zenith.chat）。但"他的生产项目"终究不是"你的项目"，迁移前仍需按自己的技术栈裁剪。

一句话：这些数字说明"系统性"和"覆盖面"，不说明"拿来即用"。

## 六、什么时候该用，怎么入手

### 适合用的人

- **已经在用某款 AI 编程工具**，想从"偶尔用一下"升级到"有方法地用"。
- **在多款工具之间切换**（比如 Claude Code 和 Codex 混用），想要一套统一的配置和记忆。
- **团队想沉淀**可复用的审查、测试、技术栈规则，而不是每人各写一份。

### 不适合一上来就全量用的人

- **只想快速查一个命令**：官方文档更直接。
- **项目极其简单**：装一套近 300 个 skills 的系统，多半是在给一个用不着复杂度的项目增加维护负担。

### 跨终端支持的真实水位

在决定"装到几个终端"之前，值得先看 README 平台矩阵给出的分层，这里摘录主档：

| Harness | 状态 | 说明 |
|---|---|---|
| Claude Code | Stable primary | 主参考实现，插件或选择性安装 |
| Codex | 原生插件（supported） | 市场插件或仓库配置，hooks 需显式信任 |
| Cursor、OpenCode | Beta | 适配器可用，hook 集合与 Claude 版不完全一致 |
| GitHub Copilot | Instruction-only | 只有指令与提示词文件，无 hooks、无运行时 agent |
| Gemini、Zed、Kimi、Qwen、Hermes、OpenClaw、CodeBuddy、JoyCode、Antigravity 等 | Experimental/minimal | 文件放置与指令可移植性已测试，不宣称功能对等 |

操作系统层面，Linux、macOS、Windows（含 WSL）都是受支持的核心平台，个别可选功能有已知的平台缺陷（如 macOS 自带 Bash 3.2 不兼容 GAN shell 路径、Windows 原生环境下 continuous-learning v2 的 observer 守护进程有问题），重度依赖前建议查一下仓库 issues 里对应编号的现状。

### 建议的采用顺序

1. **走引导式安装**：`npx ecc-universal@2.2.2 setup`（2.2 起支持 Claude Code、Codex、Kimi Code 的清单驱动安装，自带 install-state 记录、doctor 体检、repair 修复和 uninstall 卸载；若 npm 上该版本尚未发布，先 `npm view ecc-universal version` 查 latest 再锁版本）。注意不要敲 `npx ecc`——npm 上叫 `ecc` 的是一个与本项目无关的椭圆曲线加密库。Claude Code 用户也可以用原生插件命令 `/plugin marketplace add https://github.com/affaan-m/ECC` 加 `/plugin install ecc@ecc`。
2. **只挑一两个 skill 试**：从你最常用的任务类型里选一个 skill（比如 `tdd-workflow`），跑一次真实任务，看输出是否贴合你的项目。
3. **按项目裁剪**：把不需要的语言规则、无关技能删掉，只保留与你技术栈相关的部分。官方特别提醒 Claude Code 插件不能分发 rules，`rules/common` 和语言包要手动复制进 `~/.claude/rules/ecc/`。
4. **用环境变量控制上下文占用**：`ECC_SESSION_START_MAX_CHARS`（默认 8000 字符）限制会话启动注入量，`ECC_HOOK_PROFILE` 切换 hook 严格程度，低配或本地模型场景可以整体关掉 SessionStart 注入。
5. **稳定后再扩展**：确认第一套资产稳定了，再考虑 Memory Vault、GitHub App 等更重的部分。

另外交代一下成本边界：仓库本身 MIT 免费，ECC Pro 是托管在 ecc.tools 的付费 GitHub App，面向私有仓库（定价页标价每人每月 19 美元起），负责私有仓库分析、PR 触发的审计和 AgentShield 扫描。开源与托管的关系，README 的说法是 "OSS stays free"——Pro 订阅者和赞助者供养开源开发。

## 七、结尾

Everything Claude Code 最值得看的地方，不是它有多少个 skill，而是它把"怎么让 Agent 工作得有章法"这件事，从一堆散落的技巧整理成了一层可跨终端复用的系统，并配套了安全边界和采用路径。292 个 skills、68 个 agents 这些数字会继续涨，更重要的是它给出的组织方式：核心资产单一来源，适配器负责分发，instinct 沉淀为技能，记忆跨终端搬运。

它仍在快速增长，数据和定位都会继续变化。阅读时以仓库当前状态为准，把它当作"工作流组织方式的参考"，而不是一份需要照抄的配置清单。

---

## 八、延伸阅读

- [仓库 README](https://github.com/affaan-m/ECC)（[简体中文版](https://github.com/affaan-m/ECC/blob/main/README.zh-CN.md)）
- [官网 ecc.tools](https://ecc.tools)
- [`the-shortform-guide.md`](https://github.com/affaan-m/ECC/blob/main/the-shortform-guide.md)｜从安装、基础到设计哲学，官方建议最先读
- [`the-longform-guide.md`](https://github.com/affaan-m/ECC/blob/main/the-longform-guide.md)｜上下文经济学、记忆、evals、并行化
- [`the-security-guide.md`](https://github.com/affaan-m/ECC/blob/main/the-security-guide.md)｜攻击向量、沙箱、CVE、审批边界、kill switch
- [`CHANGELOG.md`](https://github.com/affaan-m/ECC/blob/main/CHANGELOG.md)｜版本演进全记录，各版本详情见 `docs/releases/`
