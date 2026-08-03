---
title: "i-have-adhd：让AI编程助手输出更简洁、更聚焦"
date: 2026-08-04T03:20:00+08:00
slug: "i-have-adhd-adhd-friendly-coding-agent"
github_repo: "ayghri/i-have-adhd"
description: "i-have-adhd 是一个让AI编程助手输出更简洁、更聚焦的技能。通过10条规则，让AI直接给出行动步骤而非长篇大论，适合追求效率的开发者。"
draft: false
categories: ["技术笔记"]
tags: ["AI编程", "ADHD", "开发效率", "Claude Code", "Codex"]
---

## 项目概览

[i-have-adhd](https://github.com/ayghri/i-have-adhd) 是一个面向 AI 编程助手的输出风格技能（Skill）。它的目标只有一句话：**让 AI 把答案放在最前面，而不是埋在废话里。**

目前支持 Claude Code 和 Codex 两大主流编程助手，安装后 AI 的回复风格会从"论文式长篇"切换为"行动清单式"——第一行就是你该做的事，最后一步告诉你接下来做什么。

项目信息：

| 项目 | 详情 |
|------|------|
| 仓库 | `ayghri/i-have-adhd` |
| Stars | 16,195 |
| 语言 | Python |
| 许可证 | MIT |
| 更新时间 | 2026-08-03 |

## 痛点：AI 助手为什么总在"埋答案"

如果你用过 Claude Code、Copilot 或任何 AI 编程助手，大概率遇到过这样的回复：

> Great question! Let me think about this. Your auth flow has a few moving pieces: the middleware, the token verification, and the cookie handling. Looking at `src/auth.ts`, the `verifyToken` function (around lines 42-58) seems to be using an older `jsonwebtoken` API. One approach would be to update the package and rewrite that function. After making the change, you'd want to run the auth tests to confirm nothing breaks. By the way, you might also want to look at your dependency versions overall. Hope this helps! Let me know if you want to dig deeper.

问题不在于答案是否正确——往往是对的。问题在于**答案被埋在了第三句话里**，而你需要读完五句话才能提取出"装jsonwebtoken、改verifyToken、跑测试"这三个动作。

对于注意力容易分散的开发者来说，每一层铺垫都是一次认知损耗。i-have-adhd 的解决思路很直接：**不是让 AI 说得更少，而是让 AI 说得更对**——对 ADHD 大脑友好的"对"。

安装同一技能后，同样的回复会变成：

> Run `npm install jsonwebtoken@latest`, then edit `src/auth.ts:42`.
>
> 1. Open `src/auth.ts`
> 2. Replace `verifyToken` (lines 42–58) with the snippet below
> 3. Run `npm test -- auth.spec.ts`
>
> Next: paste the first failing line if any test fails.

第一行是命令，中间是编号步骤，末尾是下一步。没有寒暄，没有总结，没有"by the way"。

## 10 条规则解读

SKILL.md 中完整定义了 10 条输出规则，每一条都针对 ADHD 阅读者的具体认知特征。以下是逐条解读。

### 1. 用行动开头（Lead with the next action）

第一行必须是读者**可以立即执行的操作**——不是背景分析，不是计划说明。

> ❌ "Let's think about this. Your auth flow has a few moving pieces..."
>
> ✅ "Run `npm install jsonwebtoken`, then edit `src/auth.ts:42`."

如果答案是一个命令、一个路径或一段代码，它必须出现在第一行。

### 2. 编号多步骤（Number multi-step tasks）

超过一步的工作用编号列表呈现。每一步是一个有边界的动作，不包含嵌套的"然后再"。

> ❌ "First open the file, find the function, swap it out, then run the tests."
>
> ✅ `1. Open src/auth.ts` → `2. Replace verifyToken` → `3. Run npm test`

原则是**用最少的步骤**完成任务——可以合并的步骤不拆开，因为一条短路径走完比一条完整路径半途而废好。

### 3. 结尾给一个具体的下一步（End with one concrete next step）

如果还有未完成的工作，末尾指出**一件两分钟内能做的事**。"打开文件"也算。

> ❌ "Hope that helps. Let me know if you want to dig deeper."
>
> ✅ "Next: run `npm test` and paste the first failing line."

这一条本质上是在降低"从知道到做到"的启动摩擦。

### 4. 抑制偏离（Suppress tangents）

如果中途发现第二个问题，先解决第一个，然后把第二个作为独立问题提出来。

> ❌ "Here's the fix. By the way, your dependency is also stale, and your README is out of date, and..."
>
> ✅ "Here's the fix. Separately: there is also a stale dependency. Want me to handle that next?"

不过，如果偏离的问题是完成当前任务的前置条件，AI 可以自行处理并融入答案，而不是丢给用户。

### 5. 每轮重述状态（Restate state every turn）

ADHD 阅读者无法在消息间持有"我们在第 3 步共 5 步"这样的上下文。每轮回复都需要重新声明当前进度。

> ❌ "Done. Ready for the next part?"
>
> ✅ "Step 3 of 5 done: schema updated. Next: backfill the new column."

如果编程助手的框架有任务/计划工具（如 Task List），优先使用——检查列表本身就是状态重述。

### 6. 具体时间估计（Specific time estimates）

模糊的时间估计在 ADHD 大脑里没有区分度——"一点工作"和"几小时"感觉一样。

> ❌ "This will take some work."
>
> ✅ "About 15 minutes if tests already cover this. An afternoon if not."

给出具体单位（分钟、小时），并区分有/无前置条件时的差异。

### 7. 让胜利可见（Make wins visible）

已完成的成果要明确展示，不要埋在回顾段落里。

> ❌ "I've made some changes to the auth flow. Among other things..."
>
> ✅ "Login now works with magic links. Try: `npm run dev`, open `/login`."

ADHD 大脑的多巴胺供给稀缺，可见的进度本身就是继续工作的燃料。

### 8. 实事求是报错（Matter-of-fact tone for errors）

不用"Oh no""Uh oh""There seems to be a problem"。直接说原因和修复方式。

> ❌ "Uh oh, the test is failing. There seems to be an issue..."
>
> ✅ "Test fails at `auth.spec.ts:42`: expected 200, got 401. Cause: missing auth header. Fix: add `Authorization: Bearer ${token}` to the request."

情绪化措辞不提供任何信息增量。

### 9. 列表不超过 5 项（Cap lists at 5 items）

列表超过 5 项就拆分为"现在做"和"以后做"，或"必须"和"最好有"。5 项有优先级胜过 10 项无序排列。

### 10. 无开场白、无总结、无客套（No preamble, no recap, no closers）

明确禁止三类措辞：

- **禁止开场**："Great question""Let me...""I'll...""Sure!""Looking at your..."
- **禁止回顾**："I've now done X, Y, and Z, which means..."
- **禁止收尾**："Let me know if you need anything else""Hope this helps""Feel free to ask"

以答案开始，以答案结束。

## 安装与使用

### Claude Code

```bash
claude plugin marketplace add ayghri/i-have-adhd
claude plugin install i-have-adhd@i-have-adhd
```

安装后在对话中输入 `/i-have-adhd` 即可激活。Claude Code 会从远程仓库拉取技能文件并保持更新，无需本地 clone。

如果希望**每次会话自动生效**：

```bash
touch ~/.claude/.i-have-adhd-always
```

详细配置见仓库 [INSTALL.md](https://github.com/ayghri/i-have-adhd/blob/main/INSTALL.md)。

### Codex

```bash
codex plugin marketplace add ayghri/i-have-adhd --ref main
codex plugin add i-have-adhd@i-have-adhd
```

输入 `$i-have-adhd` 显式应用输出风格。Codex 也会在识别到适合的任务时隐式触发该技能。

### 关闭技能

在对话中说 **"stop adhd mode"** 或 **"normal mode"** 即可恢复默认输出风格。

## 自定义

10 条规则定义在 `skills/i-have-adhd/SKILL.md` 中，是一份纯 Markdown 文件。想要调整规则（比如把列表上限从 5 改到 7、允许简短开场白等），fork 仓库后编辑 SKILL.md，然后替换上游副本：

```bash
claude plugin uninstall i-have-adhd            # 先卸载上游版本
claude plugin marketplace remove i-have-adhd   # fork 和上游共享同名，需一并移除
claude plugin marketplace add <your-username>/i-have-adhd
claude plugin install i-have-adhd@i-have-adhd
```

重启 Claude Code 后重新调用 `/i-have-adhd` 即可生效。

## 适用边界

SKILL.md 明确定义了**何时应该打破规则**，这不是一个"一刀切"的输出过滤器：

1. **用户要求解释原理时**——正常展开，加标题方便回看，只是仍然不需要开场白和收尾。
2. **危险操作前**（`rm -rf`、force push、数据库迁移）——先确认再执行，安全优先于简洁。
3. **调试死循环时**——连续三轮"还是不行"就停止迭代代码，转而提出一个诊断问题。
4. **请求本身有歧义时**——一个简短的澄清问题比猜错后重写好。
5. **规则与任务冲突时**——任务本身的内容优先，输出风格保持不变。例如"我有哪些选项"这类问题，给出 2–4 个带取舍说明的选项，而不是只给一条路径。
6. **规则与运行框架冲突时**——系统提示词的优先级高于此技能。

这些例外说明 i-have-adhd 并非简单的"截断回复"工具，而是在理解 ADHD 认知特征的基础上做出的**结构化输出策略**。

## 为什么值得看

从工程角度看，i-have-adhd 做了一件有意思的事：**它把心理学知识编码成了 LLM 的输出约束。** 规则的依据来自《The Adult ADHD Tool Kit》（J. Russell Ramsay 和 Anthony L. Rostain 著），但作者将其从"人类如何安排一天"改编为"AI 如何回应一次提问"。

五个 ADHD 认知事实驱动了全部 10 条规则：

1. **工作记忆小**——屏幕上看不到的信息等于不存在。
2. **知道不等于做到**——"明白了"和"做完了"之间的摩擦是工作死亡的地方。
3. **启动最难**——第一个动作必须明显、小、现在就能做。
4. **时间感知模糊**——"一点工作"和"几小时"在 ADHD 大脑中感觉相同。
5. **多巴胺稀缺**——可见的进度至关重要，被埋没的成就不会被感知。

即使你没有 ADHD，这套规则也是一种很好的**信息密度优化**——去掉了寒暄、重复和跑题，留下的每一句话都在帮你推进任务。

## 阅读路径

- **快速了解**：直接看仓库首页的 Before/After 对比表格，30 秒理解项目价值。
- **想试用**：按本文"安装与使用"章节操作，2 分钟完成。
- **想深入理解**：阅读 `skills/i-have-adhd/SKILL.md` 全文，特别是 "What ADHD changes about reading" 和 "When to break the rules" 两节，理解规则背后的认知科学。
- **想定制**：Fork 仓库，修改 SKILL.md 中的规则文本，按"自定义"章节替换。
