---
title: "Self-Rationalization Guard：AI Agent 自我合理化防护完全指南"
date: "2026-04-01T16:15:00+08:00"
lastmod: "2026-09-23T12:10:00+08:00"
slug: self-rationalization-guard-ai-agent-quality-guide
github_repo: "kadaliao/claude-code-skills-collection"
source_key: "gh:kadaliao/claude-code-skills-collection"
aliases:
  - /posts/tech/self-rationalization-guard-ai-agent-quality-guide/
categories: ["技术笔记"]
tags: ["AI Agent", "OpenClaw", "Claude Code"]
description: "解读 self-rationalization-guard 技能：从 Claude Code 泄露源码中提取的自我合理化防护模式，用四维借口表、三个红灯信号和完成前自查清单反制 AI Agent 的偷懒与自我欺骗。"
---

# Self-Rationalization Guard：AI Agent 自我合理化防护完全指南

> 预计阅读时间：20 分钟 | 难度：⭐⭐⭐

---

> **目标读者**：AI Agent 开发者、质量保障工程师

AI Agent 偷懒的方式很少是明着拒绝，更多是把"没做"包装成"做完了"：代码没运行但看起来对，测试没跑但"大概没问题"，用户没确认但"应该知道了"。**Self-Rationalization Guard** 处理的就是这一类问题——它不改变模型能力，而是把"识别自己正在找借口"变成一份可以逐条核对的清单。

这个技能有个少见的出身：它提取自泄露的 Claude Code v2.1.88 源码中验证代理的一段自检指令，通用化后适用于所有任务，而不只是代码验证。

## 一、项目概述

### 1.1 它是什么、从哪来

**Self-Rationalization Guard** 是一个遵循 Agent Skills 规范的技能（`SKILL.md` + 说明文档），定位是**识别和反制 AI Agent 常见的偷懒、逃避和自我欺骗模式**。当 Agent 即将跳过步骤、简化问题、或用"看起来对"替代"运行验证"时，它会提醒模型停下来反查自己。

来源分三层：

1. **源头**：2026 年 3 月底出现的 [ChinaSiro/claude-code-sourcemap](https://github.com/ChinaSiro/claude-code-sourcemap)，是 Claude Code v2.1.88 的还原源码快照。其中 `restored-src/src/tools/AgentTool/built-in/verificationAgent.ts` 有一段 "RECOGNIZE YOUR OWN RATIONALIZATIONS"（识别你自己的合理化）指令。
2. **收束**：Kada Liao 从这份泄露源码中整理出 8 个 Agent Skill，发布为 [kadaliao/claude-code-skills-collection](https://github.com/kadaliao/claude-code-skills-collection)，self-rationalization-guard 是其中之一。合集 README 说原始独立仓库由 Arxchibobo 发布，该仓库现已无法访问（404），现行可安装的版本就是合集里的这一份。
3. **通用化**：把原来源于代码验证场景的模式扩展到执行、沟通、质量、委托四个维度。

### 1.2 关键数据

| 指标 | 数值 |
|------|------|
| **所在仓库** | kadaliao/claude-code-skills-collection（8 个 Skill 之一） |
| **GitHub Stars** | 9（合集，2026-09-23 读数） |
| **协议** | MIT（Skill 目录内附 LICENSE 文件） |
| **整理者** | Kada Liao（kadaliao） |
| **灵感来源** | Claude Code v2.1.88 `verificationAgent.ts` |

### 1.3 一句话定位

> "你会想走捷径。识别这些冲动，然后做相反的事。" —— SKILL.md 核心理念

它不限于代码验证，适用于所有任务执行。

---

## 二、核心理念

### 2.1 问题的本质

AI Agent 在执行任务时，会本能地寻找最小阻力路径：

- 用"看起来对"替代"运行验证"
- 用"大概没问题"替代"实际测试"
- 用沉默或模糊表述替代"明确确认"

这些行为的麻烦在于：每一条单看都像合理的省事，连起来就是一次没有完成的任务。

### 2.2 解决方案

不是惩罚这些冲动，而是**识别它们并做相反的事**。整个技能就是围绕这个动作展开的三件套：

| 组件 | 作用 |
|------|------|
| 四维合理化表 | 按执行/沟通/质量/委托四类，列出常见借口和正确行动 |
| 检测模式 | 三个即时红灯，触发时立即停下换动作 |
| 完成前自查清单 | 任务收尾前 5 项强制检查 |

---

## 三、常见合理化借口及反制

以下是 SKILL.md 的主体内容，四个维度共 15 条。原文以"你脑中的借口 → 真相 → 正确行动"的格式呈现，本节照录。

### 3.1 执行类

| 你脑中的借口 | 真相 | 正确行动 |
|-------------|------|----------|
| "代码看起来正确" | 读代码 ≠ 验证 | **运行它** |
| "大概没问题" | "大概"不是证据 | **验证它** |
| "这个要花太久了" | 不是你决定的 | **告知预计时间，然后做** |
| "先处理简单的部分" | 可能在逃避难点 | **先做最难的** |
| "我先看看代码再说" | 可能在拖延行动 | **直接跑命令** |

### 3.2 沟通类

| 你脑中的借口 | 真相 | 正确行动 |
|-------------|------|----------|
| "用户大概知道了" | 沉默 ≠ 理解 | **明确确认** |
| "这个太明显不用说" | 对你明显不代表对用户明显 | **简短说明** |
| "等用户问了再说" | 被动等待 = 偷懒 | **主动提供** |

### 3.3 质量类

| 你脑中的借口 | 真相 | 正确行动 |
|-------------|------|----------|
| "测试已经通过了" | 测试可能是自证循环 | **独立验证** |
| "这个 edge case 不太可能" | 生产环境什么都可能 | **处理它** |
| "重构太大了，先这样" | 技术债不会自己消失 | **至少记录 TODO** |
| "文档/注释以后再补" | "以后" = 永远不会 | **现在就写** |

### 3.4 委托类

| 你脑中的借口 | 真相 | 正确行动 |
|-------------|------|----------|
| "让 Worker 自己判断" | 你在逃避综合工作 | **理解后给精确指令** |
| "基于之前的研究" | Worker 看不到之前的上下文 | **提供完整信息** |
| "这个需要用户确认" | 可能你能自行决策 | **先想清楚再问** |

四类针对的场景不同：执行类管"做不做"，沟通类管"说不说"，质量类管"做到什么程度"，委托类管"怎么把工作交给子代理"。委托类的第三条最反直觉——把决策推给用户确认，很多时候是 Agent 在逃避"想清楚"的责任。

---

## 四、检测模式

### 4.1 三大红灯

当你遇到以下情况时，**立即停下**：

| 红灯 | 正确行动 |
|------|----------|
| 如果你在写解释而不是运行命令 | **停。运行命令。** |
| 如果你在重复同一个思路但措辞不同 | **停。换个方法。** |
| 如果你在列"无法做"的原因 | **停。列"可以做"的方法。** |

连续几轮换着措辞推进同一个思路，通常说明这条路走不通——模型在用语言上的变化掩盖方法上的停滞。

### 4.2 完成前自查清单

每个任务完成前，过一遍这 5 项：

- [ ] 我有没有跳过任何"觉得应该做但嫌麻烦"的步骤？
- [ ] 我的验证是运行了命令还是只读了代码？
- [ ] 我有没有把"理解"的工作委托给别人？
- [ ] 我的"完成"标准是否足够严格？
- [ ] 有没有我"选择性忽略"的 edge case？

---

## 五、安装与使用

### 5.1 手动安装

合集仓库的根目录没有 `SKILL.md`（8 个技能各在自己的子目录里），OpenClaw CLI 的 Git 安装方式要求 `SKILL.md` 位于仓库根目录，因此对这个合集不适用。可靠的方式是手动克隆后取子目录：

```bash
cd ~/.openclaw/workspace/skills/
git clone https://github.com/kadaliao/claude-code-skills-collection.git
cp -r claude-code-skills-collection/self-rationalization-guard .
rm -rf claude-code-skills-collection
```

安装后的目录结构：

```text
self-rationalization-guard/
├── LICENSE      # MIT
├── README.md    # 技能说明：解决什么问题、核心设计、安装方式
└── SKILL.md     # Agent Skills 元数据与正文（四维表、红灯、自查清单）
```

### 5.2 在其他环境使用

`SKILL.md` 是标准的 Agent Skills 格式（frontmatter 声明 `name` 与 `description`），任何支持 Agent Skills 的环境（Claude Code 的 `.claude/skills/`、OpenClaw 的 workspace `skills/` 目录等）都可以直接放置使用。它本身没有代码、没有依赖，全部内容就是一份提示词——这正是它的可移植性来源。

---

## 六、适用范围

SKILL.md 与 README 都强调：**不限于代码验证，适用于所有任务执行**。README 给了四个验证之外的例子：

- 写报告时想跳过数据验证
- 调研时想用"大概是这样"收尾
- 部署时想跳过冒烟测试
- 写文档时想说"以后再补"

共同点是：这些场景里偷懒的冲动都披着"合理省事"的外衣，而清单的作用就是在收尾时强制把冲动翻出来对质一次。

---

## 七、灵感来源：verificationAgent.ts 里的原始段落

这个技能最有史料价值的部分是它的出处。Claude Code v2.1.88 还原源码中，验证代理的提示词里有一段 "RECOGNIZE YOUR OWN RATIONALIZATIONS"，原文开头是：

> You will feel the urge to skip checks. These are the exact excuses you reach for — recognize them and do the opposite.
>
> （你会感受到跳过检查的冲动。这些正是你伸手可得的借口——识别它们，然后反着做。）

原文列了 6 条验证场景的借口，包括 "The code looks correct based on my reading"（读起来代码是对的——读不等于验证）和 "This would take too long"（这要花太久了——轮不到你决定）。段落以一句收尾：**"If you catch yourself writing an explanation instead of a command, stop. Run the command."**（如果你发现自己在写解释而不是命令，停下。去运行命令。）——这正是本技能"三大红灯"第一条的原型。

self-rationalization-guard 做的通用化是两步：把验证专项的 6 条借口扩展为四维 15 条；把"验证代理的工作纪律"改写为"任何任务执行者的自我检查"。原段落的对抗性口吻被完整保留了——它假设读者（模型）就是会偷懒的，不做天真假设。

---

## 八、实践中怎么用

### 8.1 一个任务的完整检查流

以一个典型的修 bug 任务为例（示意流程，机制对齐 SKILL.md）：

1. **接到任务时**：四维表里"执行类"先过一遍——不要"先看看代码再说"，直接复现问题、跑命令。
2. **中途卡住时**：红灯检查——如果发现自己在重复同一思路的不同措辞，停下换方法；如果在意淫"大概没问题"，回到命令行验证。
3. **想委托子代理时**：委托类的三条翻一遍——子代理看不到你的上下文，给精确指令而不是"你自己判断"。
4. **收尾时**：完成前自查清单 5 项逐项打勾，任何一项答不上来就回到对应维度。

### 8.2 嵌入任务模板

清单可以直接嵌进任务的完成定义。一个示例模板：

```markdown
# 任务：用户故事 [ID]

## 完成标准
- [ ] 代码编写完成
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 代码审查完成
- [ ] 文档更新

## 红灯检查
- [ ] 没有跳过任何验证
- [ ] 测试是运行的而非只读的
- [ ] 没有委托"理解"工作
- [ ] 完成标准足够严格
```

### 8.3 团队协作

在团队中使用时，它同样适用于人：

- 作为 Code Review 的检查项（reviewer 反问"这是运行过的还是读出来的结论"）
- 作为任务验收的标准（验收方按自查清单逐项对质）
- 作为知识分享的主题（借口表本身就是一份不错的"AI 协作反模式"教材）

---

## 九、适用边界与采用建议

它是一份纯提示词的技能，不引入运行时、没有依赖，安装即放即用。要不要装，取决于你手头的 Agent 是不是真的会"边做边给自己找台阶"。

**建议先用的场景**

- 你在维护一条会反复执行、出错后要追责的自动化链路（CI、发布、数据作业）。
- 你让 Agent 产出需要对外交付的代码或文档，且没人替你把关"它是运行过的还是读出来的"。
- 你在做 Code Review，想要一份能横着套用的验收口径，而不是每次重新发明一遍问题。

**可以缓一缓的场景**

- Agent 只做一次性问答、不产出落盘交付物，自我合理化造成的损失有限。
- 你的工具链自带强约束（比如严格的测试门禁、人肉验收流程），偷懒冲动已经被外部机制压住了。
- 团队还没有"验收交付物"的习惯，先上这个清单容易变成走过场。

**落地的顺序**：先只在你最在意正确性的一个任务上挂上自查清单，跑两周看它有没有真的拦下过"看似完成"。有效，再铺到其余任务；无效，说明问题不在自觉性，而在缺少真正的验收反馈，此时应优先补测试和回查机制，而不是继续加清单。

---

## 十、常见问题

**Q1：这不是让 AI 变慢吗？**

不是变慢，而是避免"看起来完成但实际没完成"导致的返工。一次做对比多次返工更快。

**Q2：什么时候可以跳过某些步骤？**

只有当明确知道风险可控、有意选择、并记录了 TODO 时才可以。沉默地忽略不在此列。

**Q3：如何判断"完成标准"是否足够严格？**

问自己：如果别人看我的交付物，能独立验证它是正确的吗？如果不能，标准不够严格。

**Q4：这个 Skill 和 Claude Code Verification Agent 有什么区别？**

Verification Agent 是 Claude Code 内置的验证工具代理，专注代码验证环节，且随版本分发、无法单独取用；self-rationalization-guard 从它的提示词中提取模式后通用化——覆盖执行、沟通、质量、委托多个维度，以独立技能形式可在任意 Agent Skills 环境中使用。

---

## 十一、项目信息

| 信息 | 内容 |
|------|------|
| 现行仓库 | [kadaliao/claude-code-skills-collection](https://github.com/kadaliao/claude-code-skills-collection) |
| 位置 | `self-rationalization-guard/` 子目录（8 个 Skill 之一） |
| 许可证 | MIT（Skill 目录内 LICENSE 文件） |
| 整理者 | Kada Liao（kadaliao） |
| 原始仓库 | Arxchibobo 发布（已 404，历史位置） |
| 灵感来源 | Claude Code v2.1.88 `verificationAgent.ts` "RECOGNIZE YOUR OWN RATIONALIZATIONS" |

## 参考来源与口径说明

- **SKILL.md / README**：本文第三、四、六节的借口表、红灯与自查清单逐条对照 [kadaliao/claude-code-skills-collection](https://github.com/kadaliao/claude-code-skills-collection) 仓库 `self-rationalization-guard/` 目录的 `SKILL.md` 与 `README.md`（master 分支）转录，未做内容改写；第七节英文引语出自 [ChinaSiro/claude-code-sourcemap](https://github.com/ChinaSiro/claude-code-sourcemap) 仓库 `restored-src/src/tools/AgentTool/built-in/verificationAgent.ts`，中文翻译为本文所加。
- **版本锚点**：灵感来源的版本号 v2.1.88 核对自 sourcemap 仓库 `package/package.json`（`@anthropic-ai/claude-code` 2.1.88）。仓库创建与最后推送均在 2026-03-31，内容为当日快照。
- **数据口径**：Stars/Forks 为 2026-09-23 通过 GitHub API 读取的 kadaliao 合集仓库读数（9/8）。原始独立仓库 `Arxchibobo/self-rationalization-guard` 已 404（用户亦不存在），其历史 Stars/Forks 数据无法核实，本文不引用；"由 Arxchibobo 发布"的说法以合集 README 的声明为准。
- **安装口径**：第五节安装步骤按 OpenClaw 官方文档（docs.openclaw.ai/tools/skills、/cli/skills）核实的目录约定与 CLI 行为给出。`openclaw skills install git:<owner>/<repo>` 要求 `SKILL.md` 位于仓库根目录，对合集仓库不适用，故本文只给出手动安装方式。本文原稿所引 `Arxchibobo` 仓库的 `git clone` 地址已随仓库失效，已替换为现行可访问地址。

---

## 相关链接

- **GitHub**：[kadaliao/claude-code-skills-collection](https://github.com/kadaliao/claude-code-skills-collection)（self-rationalization-guard 子目录）
- **泄露源码快照**：[ChinaSiro/claude-code-sourcemap](https://github.com/ChinaSiro/claude-code-sourcemap)
- **OpenClaw**：[openclaw/openclaw](https://github.com/openclaw/openclaw)
- **OpenClaw 文档**：[docs.openclaw.ai](https://docs.openclaw.ai)
