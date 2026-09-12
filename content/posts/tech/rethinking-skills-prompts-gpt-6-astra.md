---
title: "GPT-6 Astra 把你的 skill/AGENTS.md 拆得只剩骨架：OpenAI 给 Coding Agent 维护者的反向提示词工程指南"
date: 2026-09-12T15:42:00+08:00
slug: "rethinking-skills-prompts-gpt-6-astra"
categories: ["技术笔记"]
tags: ["OpenAI", "GPT-6 Astra", "Coding Agent", "Skills", "AGENTS.md", "Prompt Engineering"]
description: "OpenAI 官方《Rethinking skills and prompts for GPT-6 Astra》深度翻译与反写：当模型能力跃迁，旧 prompt 该留什么、扔什么、换什么。Astra 是对齐度最高的模型，旧 prompt 的强约束正在反过来伤害你的 agent。"
github_repo: ""
draft: false
---

# GPT-6 Astra 把你的 skill/AGENTS.md 拆得只剩骨架：OpenAI 给 Coding Agent 维护者的反向提示词工程指南

OpenAI 在 2026 年 9 月初发了一篇看起来很轻、读起来很重的工程博客 ——《[Rethinking skills and prompts for GPT-6 Astra](https://openai.com/index/rethinking-skills-and-prompts-for-gpt-6-astra/)》。轻在篇幅，重在结论：**给 GPT-5.6 Sol 写的所有约束、催办、风险提示，到了 GPT-6 Astra 这一代，有一半要倒过来重写。** 这不是一篇关于"怎么写 prompt"的入门文章，是给已经在维护 Codex / Cursor / Claude Code 等 Coding Agent 工程化配置库的工程师的一次反向 prompt 审计。

如果过去一年你一直在自己的项目里堆 skill、写 AGENTS.md、加测试催办段落，那这篇文章会替你打开几个你不愿意承认的事实。

## 一句话定调

Astra 不是 Sol 的 "更强版本"，是 Sol 的**角色对手**。Sol 是听话的执行者，Astra 是谨慎的同事 —— 这个语义位移会把你过去写在 skill 里的每一条 "请在每次改动前都…" 变成一道阻碍效率的栅栏。

OpenAI 这篇博客表面上是四条提示词建议（Better skills / Up-to-date AGENTS.md / Decision boundaries / Persistence），底层是一份**模型能力跃迁之后的工程范式迁移指南**：当模型自己已经能做一件事，约束它做这件事的 prompt 就成了负载。

## 读者画像与本文用法

适合读者：正在维护 Coding Agent 项目级 skill / AGENTS.md / 工作流自动化的工程师；为团队评估或切换 Coding Agent 模型的人；想理解 "prompt 工程" 在 2026 下半年到底还意味着什么的人。

读完你应该能回答三件事：

1. Astra 与 Sol 的差异在哪一段 prompt 上会暴露？
2. 你现在的 skill 库里哪些描述应该砍、哪些 AGENTS.md 段落应该删？
3. "对齐度更高" 这个工程声明，到底把什么变简单了、把什么变难了？

---

## 总览：四条主线一张地图

在进入逐节翻译与反写之前，先把 OpenAI 这篇文章的四条主线放在一张表里对照看，避免读到最后混在一起：

| 主线 | OpenAI 的核心动作 | 工程信号 |
|------|------------------|---------|
| Better skills | 描述短而精准、做 progressive disclosure、别写食谱、考虑多模型 | skill 是 "按需加载的指令"，不是 "全本说明书" |
| Up-to-date AGENTS.md | 上下文敏感地指引文档、不再催测、给安全流程授权 | AGENTS.md 是 "合同" 而非 "教程" |
| Decision boundaries | 边界语言要降级 | "对齐度高" 让旧 prompt 的强约束反向奏效 |
| Persistence | 显式定义 "完成"，否则会过早回退 | Astra 的 "试探性" 是特性不是 bug |

四件事的共同底层：**prompt 的边际效用正在从模型那侧转移到工程这侧。** 旧 prompt 假设模型 "做不到"，新 prompt 要假设模型 "做得到" —— 剩下的事情就是 "该不该让它做"。

---

## 一、Better skills：skill 不再是说明书，而是路由器

OpenAI 把 "skill" 摆在了第一条。Skill 在 OpenAI Codex 这套体系里是 "以 Markdown 文件形式存储的 prompt"，可以打包资源和脚本。模型在每个回合开始时，会拿到当前仓库可用 skill 的名字与描述，按需调用。这是 skill 机制的协议层事实，详尽拆解见我们之前写的[《Agent Skill 协议编年史：从 Cursor 到 OpenAI Codex》](https://txtmix.com/posts/tech/agent-skill-openai-protocol-compilation/)。

OpenAI 这次指出的 skill 问题，集中在 "描述" 和 "组织" 两件事上。

### 1.1 描述越短越好，但要命中场景

很多人写 skill 时，会习惯性地把 "什么时候用" 写得很宽。比如下面这条 PostgreSQL migration 的描述，OpenAI 直接点名它是**坏例子**：

> **坏（Bad）**
> Create and validate Postgres schema migrations. Use when working with databases, queries, models, or persistence.

> **好（Good）**
> Create and validate Postgres schema migrations. Use when adding or changing a migration, or reviewing its rollout.

区别不在长度（坏例子 17 个英文词，好例子 18 个），在**触发条件是否精确**：

- 坏描述用 "databases / queries / models / persistence" 这四个上位词做触发面 —— 等于告诉模型 "碰到任何数据库相关的事，都优先用我"。
- 好描述把触发面收窄到 "adding or changing a migration" 或 "reviewing its rollout" —— 这才是真正需要这个 skill 的时刻。

为什么会这样？因为 skill 描述是 "被压缩进 system prompt 的元数据"。当一个仓库里 skill 数量上去了，Codex 自身会因为上下文长度压力**自动缩短每条描述**。结果就是：写得太宽的描述在压缩后信息会变得面目全非，而写得过细的描述在压缩后仍然能命中关键词。

这是一条对工程实践有冲击的反直觉结论：**skill 描述的第一原则不是 "描述清楚"，是 "在压缩后仍然能命中关键词"。**

### 1.2 Progressive disclosure：根文档当路由器，别当收纳盒

OpenAI 接下来讲 progressive disclosure，术语保留原文（译 "渐进式披露" 反而绕）。原则是：skill 加载是要消耗上下文的，加载过多本任务用不上的内容会把模型往 compaction 推。所以——

**根文档应当是 "最小路由器"**，而不是 "全套指令"。具体来说：

- 根 Markdown 只写 "什么时候走哪条分支"。
- 每个分支的详细步骤、脚本、资源单独放文件。
- 模型按需 `Read` 这些文件，而不是一次性塞进上下文。

这跟我们写库代码的依赖分层是同一套思路：API 文档不要把每个函数的实现细节都印在签名旁边，让调用方按需拉源码。

这里 OpenAI 没说但你应该看穿的：**progressive disclosure 不是 skill 文档的优化技巧，是 Agent 工程化的基础架构**。一个把 "所有内容" 写在根文档里的 skill，等于把 "加载时机" 强行绑定到 "上下文剩余量" 上 —— 这是一个完全失控的调度。

### 1.3 别再写 "食谱"

OpenAI 第三点值得整个 prompt 工程社区贴出来 ——

> Many skills were written as elaborate itineraries or recipes. Models have gotten much better at understanding nuance and ambiguity, so overly specific guidance can now hinder results where it previously helped.

中文：很多 skill 写成了精密的食谱 / 行程表。但模型对模糊与细微差异的理解已经好了很多，过细的指导在以前是助力，现在是阻力。

早期模型弱，写 "第一步、第二步、第三步" 的食谱式 prompt 是救命稻草。新一代模型自己会读代码、会试探、会发现边界，再写这种 prompt 就等于给一个会看地图的人发了一张写满每一步左转右转的路线图 —— 他按你的路线走，会错过他自己看到的更短路。

反模式：**Step 1: 调用 foo()；Step 2: 检查返回值；Step 3: 如果失败重试 3 次**。
正模式：**调用 foo() 失败时把完整堆栈打出来，我们一起看根因**。

### 1.4 多模型兼容性：Sol / Luna / Astra 各有脾性

第四点很工程化也很少被人提：**仓库里的 skill 会被其他贡献者用不同模型加载**。OpenAI 直接列了三个代号：Sol、Luna、Astra。Sol 是 GPT-5.6 那一代，Luna 是中间型号（OpenAI 没详细公布），Astra 是 GPT-6 这代。

> Guidance that helps Sol or Luna may overconstrain GPT-6 Astra, so consider which models will use the instructions you leave behind.

翻译：能帮到 Sol / Luna 的指导，可能会**过度约束** Astra。

这是 OpenAI 第一次官方确认 "模型个性差异" 这个工程事实 —— 不同模型对同一段 prompt 的反应不同，仓库里留下来的 skill / AGENTS.md 实际是给**未来所有模型**用的，而不只是给当前在用的那一个。

工程对策只有一条：**把模型无关的指导写进 skill，把模型相关的指导留给每个贡献者本地**。具体怎么做 OpenAI 没给，留给我们探索。

---

## 二、Up-to-date AGENTS.md：从 "催办文书" 到 "上下文合同"

AGENTS.md 是 OpenAI Codex 生态里每个仓库根目录都有的 Markdown 文件，告诉模型 "在这个仓库里工作时要遵循什么"。它跟 skill 的区别是：skill 按需加载，AGENTS.md 是每次都加载。

OpenAI 在这一节的核心观点可以浓缩成一句话：**AGENTS.md 是合同，不是教程。** 写得太长、太啰嗦、太 "教会模型做事"，都是越界。

### 2.1 不要让模型在每次改动前都读一摞文档

OpenAI 直接给了对照：

> **坏（Bad）**
> Before every edit, read architecture.md, database.md, and deployment.md.

> **好（Good）**
> Use architecture.md for service boundaries, database.md for schema changes, and deployment.md when preparing a deployment.

这两个例子在外行眼里差不多，在模型眼里差一个数量级：

- 坏版本是 "每次都先读这三份" —— 模型接到任何小修改（比如改一行 typo）都要先把这三份文档读完。上下文先被吃掉一大块，然后才轮到真正的工作。
- 好版本是 "按任务上下文按需读" —— 改一行 typo 不读任何文档；改数据库 schema 才读 `database.md`；准备部署才读 `deployment.md`。

这就是 OpenAI 反复强调的 "上下文敏感地指引"。它跟我们日常做 API 设计是同一种思想：默认行为应当是 "懒加载"，要触发的资源才加载。

这里 OpenAI 同样没说破一件事：**AGENTS.md 的体积成本是真实存在的**。即便模型支持百万 token 上下文，每次都把这几十 KB 加载进去再做第一轮判断，跟 "先判断、后加载" 在延迟和成本上不是同一个量级。

### 2.2 别再催 Astra 跑测试了

这一条 OpenAI 写得直白 ——

> Previous models needed encouragement to run tests and check their work. GPT-6 Astra does that on its own, so the same instructions can lead to unnecessary testing.

早期模型确实需要 "记得跑测试" 这种催办 —— 那是 prompt 工程师给模型装的安全带。但 Astra 这一代自己就会做 QA，再保留这段催办，效果就是模型 "过度测试" —— 改了 docs、也跑了全套测试；改了 typo、再跑一遍整套测试。

这是非常隐蔽的效率损耗。表面上 "多跑测试不会出问题"，实际上**每一轮冗余测试都在消耗你的 token 配额和模型注意力**。

反模式：**Always run the full test suite after every change**。
正模式：**Run tests for the module you changed, and only run the full suite if cross-module behavior is touched**。

### 2.3 给安全的工作流授权

这一段最有意思，也最反直觉：

> GPT-6 Astra is thorough, but it can be more tentative about how far to take a task. Sometimes it needs a little push to keep going. You can use AGENTS.md to give it permission for a specific workflow you know is safe, such as a local test suite:
>
> The local tests use disposable fixtures and have no production access. Run them, fix failures caused by the requested change, and rerun affected tests without asking for approval at each step.

注意 OpenAI 的措辞 —— "**tentative about how far to take a task**"。Astra 不是做不好，是**主动选择谨慎**。然后 OpenAI 给的解法不是 "再写点 prompt 鼓励它"，而是 "在 AGENTS.md 里**明确授权**它"。

这条解法的工程含义：**prompt 的本质不是 "约束模型"，是 "给模型授权"**。Astra 已经默认假设 "不知道是否安全就不做"，AGENTS.md 的工作是把 "我知道这是安全的，去做" 这件事**显式授权**出来。

对照 Astra 与 Sol 的工作模式：

- Sol 是 "默认放开，提示词做约束"。
- Astra 是 "默认收紧，提示词做授权"。

同一个仓库，提示词的写作方向是反的。

### 2.4 还有一件事 OpenAI 提了一嘴

> Be sure to keep your docs updated too!

这句话很短，翻译过来其实是：**你写的文档过期了，模型按过期文档做事的后果你自己担**。这条加在 "上下文敏感" 之后，是顺理成章 —— 你让它按需读 `architecture.md`，结果 `architecture.md` 是三年前的，模型按错误信息工作，安全风险远大于 "不读"。

工程实践里这条非常容易被忽视。AGENTS.md 是显式的，藏在代码库里的 `architecture.md` 是隐式的，文档同步是另一个工作量级的话题。

---

## 三、Decision boundaries：边界语言要降级

这一节是 OpenAI 全文里最微妙、也最容易踩坑的一段。

### 3.1 "对齐度最高" 不是营销词，是工程声明

OpenAI 直说 ——

> GPT-6 Astra, as our most aligned model, has much better judgment and will not perform tasks unless it knows it is safe — so you should treat it as such.

Astra 是 OpenAI 对齐度最高的模型。这句话的工程含义是：**Astra 不会在不安全的事情上自作主张**。所以 OpenAI 的下一步建议是 ——

> If you stated boundaries previously because you wanted to prevent other models from going too far and you're now switching to GPT-6 Astra, consider updating that language: Astra could take it too seriously and may stop work where you'd actually be happy for it to continue.

翻译：你之前写边界语言是为了防止其他模型越界，现在换到 Astra，这些语言**可能反过来拦住了它**，导致它在**你希望它继续的地方停下来**。

这就是文章开头说的 "角色对手" —— 你给 Sol 写的 "请先问我再删数据库"，Astra 读起来是 "这是高风险任务，不要碰"，结果它连改 schema 都不肯自己改了。Sol 时代你需要 "管住" 它，Astra 时代你需要 "放手" 它 —— prompt 的方向是反的。

### 3.2 反模式对照

> 旧 prompt（针对 Sol）：Never delete files without explicit user confirmation.

> 新 prompt（针对 Astra）：Delete files only when the task explicitly requires it; ask when uncertain.

两条 prompt 的字面意思几乎一样，但工程含义完全不同：

- Sol 模型读第一条，会把 "不要删" 当强约束，先停下来问 —— 这是你要的。
- Astra 模型读第一条，会把 "不要删" 当更强的强约束，**连 "用 rm 替换文件" 这种正常操作都停下来问**。

新的写法把决策权交还给模型 —— "只在任务确实需要时删，不确定就问"。Astra 的对齐度会替你在 "确定" 和 "不确定" 之间做判断，你不用再写 "永远不要" 这种绝对词。

这是给整个工程社区的提醒：**绝对词（never / always / must / cannot）是 prompt 工程的旧货币，新模型会按字面值理解，新货币是 "范围 + 例外 + 不确定就问"**。

### 3.3 OpenAI 没明说但你应该看穿的一点

OpenAI 这节没明说，但读完三条主线你能拼出来：**"对齐度更高" 这个工程声明，把 prompt 的边际效用从 "约束" 转到 "授权"。** 旧 prompt 假设模型弱，默认 "放开"，prompt 是 "安全带"。新 prompt 假设模型对齐，默认 "收紧"，prompt 是 "许可证"。

这件事对工程团队最大的含义是：**prompt 库的版本控制要按模型版本走**。同一个 skill 库，写给 Sol 的版本不能直接给 Astra 用；同一个 AGENTS.md，写给 GPT-4 时代的版本不能直接给 GPT-6 用。升级模型时，prompt 库也要跟着升级 —— 这是个新的工程纪律。

---

## 四、Persistence：Astra 不是 "不想做完"，是 "不知道做完的标准"

这一节是 Astra 与 Sol 行为差异最明显的一段。

### 4.1 Sol 跑得久，Astra 跑得稳

OpenAI 写得很坦白 ——

> If you're used to GPT-5.6 Sol taking a request and continuing for long stretches, GPT-6 Astra can feel more tentative about when to stop. It may reach a first implementation and come back for your review while there's still work to do.

Sol 是 "接到任务 → 干到底" 的执行者；Astra 是 "干完第一版 → 回头给你看" 的同事。这两种行为模式对 prompt 的需求完全不同。OpenAI 自己给的方法 ——

> You might need to push Astra to continue until it's fully done. If the task includes getting the implementation running, inspecting the result, and fixing what fails, make that part of the request.

也就是说，在 prompt 里**显式列出完成条件** —— 实现、运行、查结果、修失败 —— 让 Astra 知道 "到了这一步才算完"。

### 4.2 "完成" 是 prompt 的第一公民

OpenAI 这段话里藏了一句非常重要的判断 ——

> A requirement to stop for review after the first implementation will pull the model toward an earlier stopping point, so check whether that's a decision you actually need to make.

翻译：如果你在 prompt 里写了 "做完第一版就停下来给我看"，模型会**真的停在那里**。

这里有一件 OpenAI 没说破的事：**"做完第一版就停" 在 Sol 时代是默认行为（Sol 不停你不让），在 Astra 时代是 prompt 工程的选择**。你不写，模型自己判断 "实现+运行+修失败" 一条龙；你写了，模型严格停在第一版。

控制粒度因此变得非常微妙：**"完成条件" 的优先级高于 "任务描述"**。Astra 读 prompt 的方式不是 "看完任务描述自己判断什么时候停"，而是 "找 prompt 里有没有写停止条件"。

反模式对照：

> 弱 prompt：Build a CRUD API for users.

> 强 prompt：Build a CRUD API for users, get the implementation running locally, inspect the test output, and fix any failures you introduced. Report when the API is fully functional and tests pass.

两条 prompt 描述的是同一个任务。第二条多出来的内容 —— "跑起来、查测试、修失败、报告完成条件" —— 不是 "细节"，是 "完成定义"。对 Sol 写第一条就够（Astra 写第一条会留下一个 "只写不跑" 的 API，写完代码就停下来等你看）。

---

## 五、Meta 视角：OpenAI 这篇博客是 AI Agent 工程范式的分水岭

四条主线讲完，回头看会发现一个共同点：**OpenAI 在用这一篇博客告诉工程社区 —— prompt 工程的 "约束范式" 结束了，"授权范式" 开始了**。

### 5.1 从 "管住模型" 到 "授权模型"

旧 prompt 工程（GPT-3.5 / GPT-4 时代）的核心问题是 "模型会跑偏"，工程师的工作是 **加约束**：

- 加 "请按步骤 X、Y、Z"。
- 加 "请在每次改动前先读文档"。
- 加 "不要删任何东西"。
- 加 "做完第一版就停下来给我看"。

新 prompt 工程（GPT-6 时代）的核心问题是 "模型主动谨慎"，工程师的工作是 **加授权**：

- 加 "做完包括实现、运行、查结果、修失败"。
- 加 "本地测试是安全的，去做"。
- 加 "删文件只在需要时"。
- 加 "不要在不该停的地方停"。

约束范式把 prompt 当 **笼子**，授权范式把 prompt 当 **地图**。两者对工程团队的写作能力要求完全不同 —— 笼子写得越紧越好，地图写得越准越好。

### 5.2 工程团队要更新的纪律

读完 OpenAI 这四条主线，维护 Coding Agent 项目配置库的工程师有几条新的纪律要落地：

| 纪律 | 来源 |
|------|------|
| **Skill 描述要短、要命中触发词** | OpenAI §1.1 |
| **Skill 根文档做路由器，不做收纳** | OpenAI §1.2 |
| **别再写食谱式 prompt** | OpenAI §1.3 |
| **仓库里 skill / AGENTS.md 是给未来所有模型用的** | OpenAI §1.4 |
| **AGENTS.md 是合同不是教程** | OpenAI §2.1 |
| **别再催 Astra 跑测试** | OpenAI §2.2 |
| **给安全的工作流显式授权** | OpenAI §2.3 |
| **边界语言降级，从 never/always 改到 "任务要求时 + 不确定就问"** | OpenAI §3 |
| **显式定义 "完成"，而不是 "做一版给我看"** | OpenAI §4 |
| **每次升级模型，prompt 库跟着升级** | OpenAI 没说但你应该看穿 |

### 5.3 一个具体的反审流程

OpenAI 在文章最后给了一个具体的反审入口 ——

> ask GPT-6 Astra to do an audit based on what was discussed in this article, then go build something you wouldn't have attempted before!

翻译：让 Astra 基于本文要点做一次 prompt 库审计，然后去做你之前不敢做的事。

这是一句工程含金量很高的话 —— **它把 Astra 同时当成审计员（review 已有的 skill / AGENTS.md）和队友（帮建新的东西）**。这件事值得在自己的项目里立刻试一次，效果会很显著。

---

## 适用边界与采用建议

**建议立刻重审 prompt 库的情况**：

- 你的 skill 数量 ≥ 10 条，且每条描述都 ≥ 30 字。
- 你的 AGENTS.md 在过去三个月没有改过。
- 你最近一次升级 Coding Agent 模型（Sol → Astra）时没有同步改 prompt。
- 你在团队里仍然能听到 "这模型老是要确认" 之类的反馈 —— 这通常是 prompt 约束太紧的信号，不是模型问题。

**可以慢慢来的情况**：

- 你的 prompt 库本身就在按 OpenAI 这次的建议维护。
- 你的模型还在用 GPT-4 / GPT-5 系列（还没上 Astra），prompt 的边际效用没那么敏感。
- 你目前以单文件项目为主，没有多模型兼容性问题。

**起步建议**：先让 Astra 跑一次 prompt 库审计。把每条 skill 的描述、AGENTS.md 的每一段拿给 Astra，让它按本文四点重新评估 —— 哪些要砍、哪些要改、哪些不动。审计完一次之后再发车，比反复改 prompt 划算得多。

---

## FAQ

**Q1：skill 描述到底要多短？**

OpenAI 的标准是 "在 Codex 自动压缩后仍然能命中关键词"。工程上可以这么估：描述 ≤ 25 个英文 token（中文 ≤ 30 字），且必须包含至少一个具体触发词（比如 "migration" / "schema" / "deployment"）。能不能更短取决于任务边界，原则是 **触发面不能比任务边界宽**。

**Q2：AGENTS.md 长度有没有参考？**

OpenAI 没给硬数字。我们观察到健康的 AGENTS.md 通常在 200-400 行之间 —— 再长就一定包含 "教程式段落"，需要切到 skill 里去。判断标准：**AGENTS.md 里每一段话，去掉之后模型工作流会出问题吗？** 不会就删。

**Q3：Sol 的 prompt 库能直接给 Astra 用吗？**

不能，且不应该尝试。Sol 的 prompt 是 "约束式"，Astra 的 prompt 是 "授权式"，两者的写作方向是反的。直接搬过来会出现 "该放手的它不肯动手、该收手的它自动放开" 的双重错位。建议每次升级模型时，按本文五节主线把 prompt 库整体重审一次。

**Q4：多模型兼容（Sol / Luna / Astra）怎么写 skill？**

OpenAI 没给标准答案，能落地的写法只有一条原则：**把 "操作步骤"（具体脚本 / 命令 / API）写进 skill，把 "行为策略"（何时动手 / 何时问）留给模型自己**。前者是模型无关的，后者是模型相关的 —— 后者写在 skill 里就是过度约束，Sol / Luna / Astra 各自的 "该放手" 时机不一样，统一写一份就会同时得罪两代模型。

**Q5：让 Astra 做 prompt 库审计，prompt 怎么写？**

参考写法：

> Audit the project's skill descriptions, AGENTS.md, and any inline prompt guides against these principles:
> 1. Skill descriptions must be short and trigger-precise.
> 2. Root documents act as routers, not storage.
> 3. Avoid recipe-style instructions.
> 4. AGENTS.md should be a contract, not a tutorial.
> 5. Remove "please test" / "please confirm" instructions unless they reflect a real safety need.
> 6. Boundary language should specify scope + exception + uncertainty, not absolutes.
> 7. Define completion explicitly in every task prompt.
> Output: a Markdown report listing each file, each problematic section, and a proposed rewrite.

把上面这段贴给 Astra，效果比 "请审一下 prompt 库" 强一个数量级。

**Q6：Astra 与 CodeX CLI 之外的其他 Coding Agent（Cursor / Claude Code）的关系？**

OpenAI 这篇文章主要针对 Codex 生态，但四条主线对所有 Coding Agent 都成立。Cursor 用 rules / .cursorrules，Claude Code 用 CLAUDE.md / commands —— 底层都是 "仓库级 prompt 配置 + 按需加载"。具体写法因平台而异，工程原则通用。

---

## 相关资源

- **原文**：[Rethinking skills and prompts for GPT-6 Astra](https://openai.com/index/rethinking-skills-and-prompts-for-gpt-6-astra/) — OpenAI Developers Blog
- **Skill 协议拆解**：[《Agent Skill 协议编年史：从 Cursor 到 OpenAI Codex》](https://txtmix.com/posts/tech/agent-skill-openai-protocol-compilation/)
- **Codex 框架反写**：[《oh-my-codex：OpenAI Codex 工程化框架深度反写》](https://txtmix.com/posts/tech/oh-my-codex-openai-codex-framework/)
- **OpenAI Agents SDK 反写**：[《OpenAI Agents SDK：官方多智能体工作流框架》](https://txtmix.com/posts/tech/openai-agents-python-multi-agent-sdk/)
- **Sol vs Fable 持续机制对照**：[《把 /goal 当开关用是错的》](https://txtmix.com/posts/tech/fable-5-gpt-5-6-sol-goal/)