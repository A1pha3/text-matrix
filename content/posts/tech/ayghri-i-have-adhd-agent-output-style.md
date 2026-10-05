---
title: "i-have-adhd：让编码代理停止堆话、立刻动手的输出风格"
date: 2026-08-02T02:59:48+08:00
lastmod: "2026-09-27T12:00:00+08:00"
slug: "ayghri-i-have-adhd-agent-output-style"
github_repo: "ayghri/i-have-adhd"
source_key: "gh:ayghri/i-have-adhd"
description: "ayghri/i-have-adhd 是一个 Agent Skills 标准下的输出风格技能，显式调用后让 Claude Code/Codex 等编码代理先给动作、再给步骤、不再讲礼貌套话；本质是把\"代理如何回答\"这件事从模型层移到技能描述层。"
draft: false
categories: ["技术笔记"]
tags: ["Agent Skills", "Claude Code", "Codex", "输出风格", "Prompt 工程"]
---

## 一句话判断

`ayghri/i-have-adhd` 不教代理"更聪明地写代码"，而是把"先给一句动作命令、再给三步可执行步骤、最后再补一句 Next"的输出形态**编码成一项标准技能**——遵循 Agent Skills 开放标准的代理装上它，显式调用后就切换到这套输出风格，不需要修改模型或系统提示。项目 2026 年 5 月中旬创建，到 9 月下旬已积累 5 万 star，说明"代理太啰嗦"是公认痛点。

## 项目定位

仓库自我描述很直接：

> ADHD-friendly outputs. No ADHD diagnosis needed!

它的产品形态是一个**输出风格技能**，不是文档库也不是工具集。名字里的 ADHD 不是医疗声明——README 的 Credits 一节写明，规则"松散基于" J. Russell Ramsay 与 Anthony L. Rostain 的《The Adult ADHD Tool Kit》，且"改编针对 LLM 应该如何回答，而不是人应该如何安排日程"。任何人不需要确诊就能用，它只是借用了一套应对注意力碎片化的成熟方法。

README 里给出的 Before/After 对比把这个意图点得非常明白：

> **Before**：Great question! Let me think about this. Your auth flow has a few moving pieces: the middleware, the token verification, and the cookie handling. Looking at `src/auth.ts`, the `verifyToken` function (around lines 42-58) seems to be using an older `jsonwebtoken` API. One approach would be to update the package and rewrite that function. After making the change, you'd want to run the auth tests to confirm nothing breaks. By the way, you might also want to look at your dependency versions overall. Hope this helps! Let me know if you want to dig deeper.
>
> **After**：Run `npm install jsonwebtoken@latest`, then edit `src/auth.ts:42`.
>
> 1. Open `src/auth.ts`
> 2. Replace `verifyToken` (lines 42–58) with the snippet below
> 3. Run `npm test -- auth.spec.ts`
>
> Next: paste the first failing line if any test fails.

After 形态浓缩了技能的核心：**Action first**（一句命令开头）、**Steps numbered**（编号步骤）、**No "Hope this helps!"**（去礼貌话）、**Next**（失败时该贴什么）。完整的规则体系是 10 条，见下文。

## 安装与触发

```bash
# Claude Code
claude plugin marketplace add ayghri/i-have-adhd
claude plugin install i-have-adhd@i-have-adhd

# Codex
codex plugin marketplace add ayghri/i-have-adhd --ref main
codex plugin add i-have-adhd@i-have-adhd
```

**触发只有显式一种**。在 Claude Code 里输入 `/i-have-adhd`，在 Codex 里输入 `$i-have-adhd`，规则对本次会话生效，直到你说 "stop adhd mode" 或 "normal mode" 才关闭。这个技能特意禁用了自动加载——SKILL.md frontmatter 写了 `disable-model-invocation: true`，Codex 侧的 `agents/openai.yaml` 写了 `allow_implicit_invocation: false`。INSTALL.md 对 Claude Code、Qwen Code、Codex、Grok 的表述是 no middle ground——你不主动打开，它就不生效。输出风格是强个人偏好，让代理自己判断"这个任务适不适合"只会造成不稳定。

想每次会话都自动开，Claude Code 的做法是创建一个标志文件：

```bash
touch ~/.claude/.i-have-adhd-always
```

插件带的 `SessionStart` hook（匹配 startup、resume、clear、compact 四种会话事件）看到这个文件就把完整规则集注入会话；删掉文件即回到按需模式。用了自定义配置目录的，在 `$CLAUDE_CONFIG_DIR` 下创建同名文件。即便 always-on，"stop adhd mode" 仍然能在当前会话关掉它。

对其他代理的支持是这个项目铺得很宽的一块：INSTALL.md 按 15 个平台逐家写了安装、验证、更新、卸载四段，多数平台另配 always-on 可选段——Claude Code、Codex、Gemini CLI、GitHub Copilot、Cursor、Zed、OpenCode、Grok、Qwen Code、Kimi Code、Pi、Antigravity 等，末段还顺带覆盖 Amp 和任意读 Agent Skills 的 harness。同一个 `SKILL.md`，各平台按自己的插件机制接入，Copilot 和 Zed 甚至原生读 Agent Skills 格式、无需转换。

## 规则本体：10 条与 6 条例外

完整规则在 `skills/i-have-adhd/SKILL.md`，每条都配了 Bad/Good 对照。10 条规则按 SKILL.md 的编号顺序依次是：

- **动作先行**——第一行必须是读者现在就能做的事，不是背景也不是计划；如果答案是命令、路径或代码片段，它第一个出现，解释放到后面
- **多步任务编号**——超过一步的工作写成编号列表，每步一个动作，一步里不允许出现两次"然后"；步骤以最少可用为准，短路径跑完胜过完整路径放弃
- **收尾给一个 Next**——还有未尽事项时，点名一件两分钟内能做的事，哪怕只是"打开文件"
- **抑制支线**——发现第二个问题时，先完成第一个，再把第二个作为单独问题提出；工作中自己答得掉的问题就地处理，答不掉的留到结尾提一次
- **每轮重述进度**——读者记不住"我们在 5 步里的第 3 步"，所以每轮都要说"第 3 步完成：schema 已更新"
- **给出具体时间**——"要花一些功夫"和"要几个小时"在读者那里是同一个词，改成"约 15 分钟，如果测试已覆盖；否则要一下午"
- **让完成可见**——不说"我改了一些东西"，说"魔法链接登录现在可用了，跑 `npm run dev` 打开 `/login` 试试"
- **错误平铺直叙**——不说"Uh oh"，直接给位置、原因、修法三段
- **列表封顶 5 项**——相关条目分组、按相关性排序，可见工作集不超过 5 项；这条只管呈现，相关条目在内部保留，不因展示规则丢失分析
- **无开场白、无总结、无收尾客套**——"Great question""I'll...""Hope this helps" 全部在禁用清单上

Before/After 里那个例子正好把前三条用全了：首行 `Run npm install jsonwebtoken@latest` 是动作先行，中间三步是编号步骤，结尾 "Next: paste the first failing line" 是收尾 Next。

规则之外还有 6 条明确的例外条款，防止风格压过任务：用户要求 "explain" 或 "walk me through" 时完整展开；`rm -rf`、force push 这类破坏性操作前必须确认；连续三轮 "still broken" 的调试螺旋要停下来点名可疑假设而不是继续改代码；请求有真歧义时问一个短问题；规则与任务冲突时任务赢、形态留下；规则与代理 harness 的系统提示冲突时，系统提示优先。

技能末尾还附了一张发送前自检清单：删掉"宣布自己要做什么"的首句、删掉"还有什么要问的吗"式的尾句、删掉 "by the way" 支线、删掉不含信息的对冲副词、把比喻换成字面动作。最后验证一遍：读者只读第一行和最后一行，能不能知道接下来做什么、刚刚发生了什么。

## 一次典型会话的完整流转

把触发、规则、关闭三段机制串成一条链路，一次典型的使用是这样的：

1. 首次使用先在会话里输入 `/i-have-adhd`（Codex 是 `$i-have-adhd`），规则集对当前会话生效。
2. 之后的每次回复都按 10 条规则整形：首行动作、多步编号、收尾给 Next 或直接结束。
3. 中途冒出第二个需求时，规则第 4 条要求先完成当前任务，再把新需求作为单独问题提出。
4. 会话结束，规则随会话失效；想每次会话自动开启的人，会在安装阶段就创建 `~/.claude/.i-have-adhd-always` 标志文件，SessionStart hook 在 startup、resume、clear、compact 四种事件上注入规则集。
5. 任何时候说 "stop adhd mode" 或 "normal mode"，规则即关闭，插件用一行确认后回到默认风格。

这条链路的关键约束：规则只对当前会话生效，不随会话残留；always-on 改变的只是注入时机，关闭出口始终保留。

## 为什么叫 ADHD：五条设计假设

SKILL.md 用五条"ADHD 如何改变阅读"的事实解释每条规则的来历：

1. 工作记忆很小——屏幕外的东西等于不存在，别让读者"记住 X"
2. 知道答案不等于做到答案——"懂了"和"做完"之间的摩擦力才是工作停摆的地方
3. 启动是最难的一步——第一个动作必须显而易见、足够小、现在就能做
4. 时间感知是均匀的——"一点活"和"几小时"登记为同一个词，模糊估计必然失效
5. 多巴胺稀缺——看不见的进展等于没进展

这五条假设都有认知科学或临床传统背书（工具书出处见上文 Credits），但项目没有止步于"把人类方法搬给 LLM"：时间估计、进度重述这些规则，是按对话代理的交互形态重新设计的。

效果也不是自说自话——仓库的 `evals/` 目录带了一套盲评框架，RESULTS.md 记录的首次正式评测（2026-08-02，claude-opus-4-8，14 个案例 × 3 次试验 × 基线/技能两组）里，加权分从基线 4.045 升到 4.473，其中简明度（Concision）提升最大（+1.143），可操作性（Actionability）+0.714。它测的是同一模型在技能开与关两种形态下的输出差异，裁判与被测同为 claude-opus-4-8，属于自评口径——数字看趋势比看绝对值有意义，能推出的是规则确实改变了输出形态、方向与设计意图一致；推不出的是跨模型、跨任务分布的推广结论。

比总分更有信息量的是 RESULTS.md 里作者自己写下的两条发现。收益集中在"报告状态"类案例：multi-step-progress +2.53、error-report +2.40，两者贡献了大部分加权增量；带固定输出契约的案例（代码作答、长文请求）分数纹丝不动——例外条款在任务规定形态的地方守住了。唯一的回归是 partial-success（−0.63），作者的机制猜测指向第 8 条"先原因、后修法"的错误格式：它可能压着模型在证据不足时也报出一个确定的原因。作者把它标为唯一值得加试验证的回归——同时有一致的方向和说得通的机制。

## 真正解决的问题：把风格搬出模型

过去想强制代理"少废话、直接动手"，只能改系统提示或定制一个模型副本。这种方式有两个问题：

1. **不可移植** —— 你在 Claude Code 上调好的风格，搬到 Cursor/Aider/Codex 又得重来
2. **很难分享** —— 个人偏好型的 prompt 没法进团队工具链

`i-have-adhd` 的解法是走 **Agent Skills 开放标准**：技能是一份带 frontmatter 的 Markdown（`SKILL.md`），各代理按自己的插件机制加载。换成这套标准后，三件之前做不到的事变得直接：

- 同一份技能能在十几个代理之间迁移——INSTALL.md 的平台矩阵就是可移植性的直接证据
- 团队可以把"我们偏好的输出风格"做成内部 fork——README 官方支持 fork 后改 `SKILL.md` 再换源安装的工作流，四条命令完成切换
- 风格本身是可读的 Markdown，可以进 code review，规则改动了什么一目了然

## 与 `pbakaus/impeccable`、`emilkowalski/skills` 的关系

- `pbakaus/impeccable`：设计语言技能，官方描述是"让你的 AI harness 更擅长设计的语言"
- `emilkowalski/skills`：面向设计师与工程师的技能集（作者 Emil Kowalski 以 Web 动画课程知名，仓库内多为动画与 UI 细节技能）
- `ayghri/i-have-adhd`：回答结构/信息密度的技能

三者管的是不同层：impeccable 管"产出的 UI 漂不漂亮"，emilkowalski 管"动效与微交互的分寸"，i-have-adhd 管"代理话说得清不清楚"。一起装上，代理写 UI 时同时拿到审美与表达两套约束；三者都是 Agent Skills 技能，安装方式互通。

## 适用边界与采用建议

**适用**：

- 已经被 Claude/Codex 的"长篇套话"消耗太多耐心的工作流
- 团队希望统一所有成员看到的代理输出形态（fork 一份内部版本即可收敛）
- 需要把 prompt 工程沉淀成可分享、可版本化的资产

**不适用**：

- 需要代理默认展开推理过程的教学/演示场景——默认形态只给动作与步骤；不过它留了口子，你说 "explain" 时它会完整展开并加小标题
- 输出契约依赖固定礼貌话术的对外场景——它会删除开场白与收尾客套，且无法按受众放宽
- 期待它改变模型判断的场合——它管的是回答形态；例外条款里"调试螺旋停下提问""歧义时先问一句"已是最深的干预，分析本身不受规则约束

**采用顺序**：先在 Claude Code 装上，手动 `/i-have-adhd` 用几天，验证这套形态是否合自己口味；顺手就 `touch ~/.claude/.i-have-adhd-always` 常开；想微调规则就直接改 fork 里的 `SKILL.md`（10 条规则全是可读 Markdown）；团队统一输出风格，把 fork 发成内部 marketplace 一键分发。

## 参考来源与口径说明

- 仓库地址：<https://github.com/ayghri/i-have-adhd>。本文安装命令、规则条文、例外条款、评测数字均对照其 README、INSTALL.md、`skills/i-have-adhd/SKILL.md`、`evals/RESULTS.md` 与 `.claude-plugin/` 清单原文，核对时点为 2026-09-27（插件版本 v0.3.0，MIT 许可，仓库 created 2026-05-13）。
- star 数（51436）、姊妹仓库 star 数（impeccable 71627、skills 41344）为 2026-09-27 经 GitHub API 核对的瞬时值，仅作热度参考。
- `evals/RESULTS.md` 的评测由项目作者自录：裁判模型与被测模型同为 claude-opus-4-8，属自评口径；不同模型与任务分布下结果会不同。
- "在 Cursor/Aider/Codex 上风格不可移植"的表述是背景性概括；Aider 不在 INSTALL.md 的平台清单内，其 skills 支持状况未在本文核查范围。
- 想读完整规则与例外条款：仓库 `skills/i-have-adhd/SKILL.md`；平台接入细节在 `INSTALL.md`；盲评方法与原始分数在 `evals/RESULTS.md`；Before/After 对比与 Credits 在 `README.md`。
