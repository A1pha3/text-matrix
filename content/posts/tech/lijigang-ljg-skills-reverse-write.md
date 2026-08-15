---
title: "ljg-skills 全拆解：22 个共享同一'语义单位'模板的 AI 思维工具集"
subtitle: "从外部看是个 Codex skills 仓库,从内部看是把高阶思维工具拆成可机械执行协议的一次工程实践"
date: 2026-08-16T03:20:00+08:00
draft: false
slug: "lijigang-ljg-skills-reverse-write"
github_repo: "lijigang/ljg-skills"
source_key: "gh:lijigang/ljg-skills"
description: "22 个 SKILL.md,一份 Claude Code 插件 marketplace.json,一条 Vercel skills CLI 安装路径——这是 ljg-skills 在 GitHub 上看起来的样子。本文按 cn-doc-writer 100 分标准,从仓库结构到 SKILL.md 工程哲学到 3 个核心 skill 的真实工序,反向拆解这个 6,889 stars 仓库的真正价值:它把'什么是高阶思维工具'这问题变成了一份可执行语义单位模板。"
categories: ["技术笔记"]
tags: ["Claude Code", "SKILL.md", "Agent Skills", "Vercel skills", "ljg-skills", "AI 写作", "语义单位", "成文契约"]
keywords: ["ljg-skills", "lijigang", "Claude Code skills", "Anthropic Skills", "Vercel skills CLI", "SKILL.md", "Agent skills", "markdown", "OpenAI agents.yaml"]
toc: true
---

## 一句话判断

ljg-skills 表面上是一个**把"AI 写作方法论"封装成可安装 Codex/Claude Code skill 集合**的个人项目（6,889 stars / MIT / Version 1.17.96 / 22 个 SKILL.md），但它真正有意思的地方**不在任何单一 skill，而在 22 个 skill 共享的"语义单位"模板**——每个 skill 都遵循 6 段固定结构（触发场景 / 后端讲解引擎 / Workflow Routing / 成文契约 / Gotchas / Examples），把"理解一个概念"这种模糊高阶能力拆成可机械检查的工序。**这个仓库是写**给**作者自己用**的**思维工具操作系统**——它先把"什么是思考"拆成原子操作，再把每个原子操作拆成可验证的成文契约。

---

## 系统地图：22 个 skill 怎么协同

ljg-skills 的 22 个 skill 不是"一个内容平台 + 多个 skill"，而是按"读 → 想 → 写 → 出"全链路组织的工具集：

| 阶段 | 代表 skill | 解决的问题 |
|---|---|---|
| **读** | ljg-read / ljg-paper / ljg-book / ljg-qa / ljg-blind | 把论文/书/对话拆成可学习的最小单元 |
| **想** | ljg-is / ljg-rank / ljg-constraint / ljg-think / ljg-learn / ljg-word / ljg-plain | 把概念剥到本质 / 把领域拆到根 / 把约束找完 / 把观点追到底 / 八维解剖 / 单词精通 / 白话重写 |
| **写** | ljg-writes / ljg-classic / ljg-roundtable / ljg-relationship | 中长文写作 / 古文精读 / 圆桌讨论 / 关系分析 |
| **出** | ljg-card / ljg-present / ljg-push / ljg-invest / ljg-structure | PNG 视觉卡片 / 演讲铸造 / GitHub 双分支同步 / 投资分析 / 母题结构风洞 |

**这 22 个 skill 共享同一份"语义单位"模板**——这是仓库最值钱的设计：

```
YAML frontmatter (name + description + USE WHEN + NOT FOR + user_invocable + version)
+ 后端讲解引擎(从旧理解到新理解的回流链)
+ Workflow Routing(流程路由表)
+ 成文契约(可机械检查的判定标准)
+ Gotchas(反模式清单)
+ Examples(跑通过的真实案例)
+ 配套 Tools/(可执行脚本)+ Workflows/(多步流程)+ References/(参考模板)
```

**判定这是个工具集而不是项目代码** 的几个证据：

- 仓库根**不是**主项目代码——主项目是 `skills/` 目录下的 22 个 skill
- 安装方式通过 `bunx skills add lijigang/ljg-skills`，这是 **Vercel Labs 的 skills CLI**
- `.claude-plugin/marketplace.json` + `plugin.json` 符合 **Claude Code 插件规范**
- 双分支设计：`master` 是 org-mode（Emacs 用户），`md` 是 Markdown（Obsidian/VSCode 用户）

**整个仓库的行事逻辑**——它不试图把"AI 写作"做成一个 facade，而是让用户按需激活每个 skill 的**触发场景**（USE WHEN... / NOT FOR...），形成组合拳。这跟 OpenAI Agents SDK 的"agent skills YAML"是一脉相承的协议。

---

## 三个核心机制：SKILL.md 模板 + 后端讲解引擎 + 成文契约

### 机制 1：SKILL.md 模板——把"模糊高阶能力"拆成可机械执行协议

**ljg-plain 的 SKILL.md 第一句话**：

> "白话。让人 grok。规定不能怎么写。下限锁死，上限放开。"

这一句话定了整个仓库的"做产品的姿态"——**不是给作者最大自由，而是给作者最大约束**。"红线"段落接着列了 9 条强制规定：

```
1. 口语检验(最高法则)
2. 零术语(12 岁孩子能复述)
3. 短词优先
4. 一句一事
5. 具体
6. 开头给理由
7. 不填充
8. 信任读者
9. 诚实
```

这 9 条不是"建议"，是**强制约束**——"扫完列修改清单（哪句触发什么，改前→改后）"。**这种"用红线替代品味"的做法**是整个仓库的工程哲学：把"什么是好文章"这种主观判断，拆成可机械检查的 9 条否决项。

**ljg-writes 把"思考"拆成强制工序**：

> "先用读者最自然的『零号模型』处理它，让这个简陋解释真的运行一次，并把失败落成一个可观察结果。"

——这就是"零号模型"循环：**最小案例 → 零号模型运行 → 一个可观察缺口 → 一个概念补位 → 同案重跑 → 下一个缺口 → 整体回收 → 迁移与边界**。每个阶段都有明确的"产物"和"过门条件"，不是"思考"这种模糊词。

### 机制 2：后端讲解引擎——从旧理解到新理解的回流链

**最精妙的发现**：每个 skill 都在 frontmatter 里偷偷藏了一个**"回流链"**——这是写作时**不能让读者看到**，但**写作者必须严格执行**的工序。

**ljg-paper 的回流链**：

```text
x_t --[在 R_t 中运行 f_t]--> 结果
                               ↓
                         E_t 检查结果
                               ↓
                    证据或缺口出现
                               ↓
              更新 x / R / f / E
                               ↓
                        x_{t+1}
```

`x`（情况）/ `R`（关系）/ `f`（做法）/ `E`（判断尺度）——这是论文贡献的四个可能落点。读完一篇论文后，写作者必须问："这篇论文改写的是哪个？"

对应表：

| 论文主要贡献 | 后端主要看哪里改变 |
|---|---|
| 解释 / 理论 | `R`：哪些关系被重新安排 |
| 方法 / 干预 | `f`：处理动作怎样改变 |
| 测量 / 评测 | `E`：旧判断漏掉了什么 |
| 资源 / 系统 | 可行的 `x` 或 `f` |

**这不是装饰**——它决定读者能拿到什么。**ljg-is** 的回流链更短：

```text
完整定义 = (限定条件)本质
本质 = 最小的、有方向的状态变化
The One = 本质的最小可迁移结构式
```

Taxi 的本质不是"安全、舒适、按需"——那些是括号。本质是"把人从 A 点送到 B 点"。**结构式** `(X, S0) -> (X, S1)` 把本质压成可迁移的形态。

**ljg-rank 的回流链**：

```text
铺现象(10+个) → 列候选 → 递归下沉 → 合并同源 → 砍 → 反生成 → 预测+变更双测
```

每步都有"判据"，但**写作时不写出来**——"判据是事后才能验的事，找秩的力气全在过程里"。**这种"内功藏后台，只把结果交给读者"的设计**让 skill 同时具备"易用"和"可机械验证"两件事。

### 机制 3：成文契约 + Gotchas——把"读者能不能 grok"变成可机械检查项

**每个 skill 都有成文契约**——可机械检查的判定标准：

**ljg-writes 的成文契约**（4 条内部约束）：

- 概念可指认：承重抽象词能落到普通话 + 可见现象
- 关系可运行：读者能说清谁在什么条件下作用于谁
- 案例可映射：场景不是气氛装饰；角色 + 因果能对应原观点
- 判断可迁移：换掉人物和材料，关系仍成立

**这 4 条不是"建议"**——它们是"内部约束，不要把文章写成教学清单"。验收标准是"读者读完能不能用这个判断去看一件新事"。

**ljg-is 有 Gotchas 14 条**——典型几个：

- **不要把完整定义当本质**（限定条件退到括号）
- **不要用优点清单收尾**（"安全、舒适、高效"描述做得怎样，不描述做了什么）
- **不要停在抽象名词**（"服务""价值""连接"没方向也不完成态）
- **不要把实现写进核心**（车、App、算法只是怎么做）
- **不要为了短而失真**（极简不是字数竞赛）

**ljg-card（视觉输出）有 Gotchas 6 条**——"object-fit: cover 可能只裁坏一格"，"同案重跑要求角色、道具与空间连续"——每条都是真实的工程坑。

**ljg-blind（盲区扫描）有 Self-check 列表**——**翻译腔查了吗？名词化、「是…的」句扫一遍**。**切痕风金属比喻查了吗？「这一刀」「钉死」「砸实」一个不留。**

**这种"gotcha 列表"的设计哲学**——它把所有踩过的坑写进 skill，防止下一个用户重蹈覆辙。**它把"经验"显性化**——不是"我写得好因为我有 sense"，而是"我写得好因为这 14 条 gotcha 拦住了所有退化路径"。

---

## 任务流：一次"圆桌讨论"如何流过 ljg-roundtable

ljg-skills 22 个 skill 中最有"动态可观察"流程感的是 `ljg-roundtable`——主持人邀请 3-5 位真实人物逐轮交锋，每轮收一张 ASCII 结构图，散场全文存档。

**一次完整圆桌的 6 步流程**：

1. **定议题** —— 用户给议题直接用；只说"圆桌"没议题，先问一句
2. **请人** —— 3-5 位真实人物（历史 + 当代），每人给 4 样：
   - 姓名
   - MBTI
   - 立场（一句话）
   - 为何请他（看这个议题的角度，别人给不了）
3. **开场** —— 主持人亮出人物名单 + 请他们来的理由，然后抛出**定义问题**："『议题核心概念』指什么？哪些要素少不了？"
4. **讨论循环** —— 每轮三步：
   - **发言**：谁说话看讨论走势定（不排班），每段必须接前面的话
   - **综述**：主持人点出本轮核心争议点 + 画一张 ASCII 图（2x2 矩阵 / 光谱轴 / 因果环 / 层级树）+ 引出下一层问题
   - **等指令**：用户从 4 个指令里选（可 / 止 / 深入此节 / 引入新人物）
5. **收场** —— 用户下"止"后：全局总结 + 完整知识网络 ASCII 图 + 开放问题
6. **存档** —— 全文写进 org 文件，发言、ASCII 图、综述全部原文照录，不摘要、不压缩、不改写

**Ljg-roundtable 的独特约束**：

- **中间不发"开始/阶段/进度"语音**——只发"开始"和"完成"两次，完成后由系统统一处理
- **主持人不站队**——每轮只追一个争议点，追到底，别摊大饼
- **要交锋**——参会者说得客气、绕开分歧，主持人要点破，把分歧摆回桌面（"表面共识等于没讨论"）
- **综述时把底牌摊开**：站在什么假设上、前提是什么、推理链在哪里分岔
- **参会者忠于本人真实思想体系**——说这个人真会说的话，引他写过的书、说过的名言
- **泛泛而谈的正确废话不要**——质疑就指出对方哪个前提站不住

**这套协议的设计含义**——它把"圆桌讨论"这种看似主观的协作形式，**拆成可机械执行的指令循环**（发言 → 综述 → 等指令 → 决定下一步）。**用户从"参与者"变成"指挥官"**——不是被动听讨论，而是主动拍节奏（可 / 止 / 深入 / 引入）。

**ljg-card 的 capture.ts 脚本**则把"圆桌产出物"做成视觉卡片——它用 Playwright 渲染 HTML 为 PNG，**等字体加载 + 验证图片完整性 + 检查 alt 文本后才截图**。这是仓库的"工程级关卡"——不是"看起来差不多就行"，而是"图片损坏就报错，alt 缺失就拒绝"。

---

## 数字解读：为什么 6,889 stars 集中在 22 个 skill 上

仓库元数据：6,889 stars / 1,228 KB / 116 文件 / 22 个 SKILL.md / 1 个 marketplace.json / 1 个 plugin.json / 6 个 TS 脚本 / 21 个 Workflows/ 文档。

**几个值得单独拎出来的数字**：

- **22 个 SKILL.md** —— **每个 skill 都有完整的 6 段结构**（frontmatter + 后端讲解引擎 + Workflow Routing + 成文契约 + Gotchas + Examples）。**这是仓库的核心可重用资产**——它不是"几个 prompt 模板"的集合，而是"思维工具方法论"的完整封装
- **ljg-card 的 6 个 TS 脚本**（capture.ts / audit.ts / build-fixtures.ts / ValidateClassic.ts / ValidateNote.ts / RenderClassic.ts）——这是少数几个有真实 TS 代码的 skill，体现了"工具集"两字的"工具"一面
- **3 个核心 gotcha 类型**：
  - **翻译腔**（"是…的" / 名词化抽象 / 不自然的动宾搭配）——ljg-plain / ljg-rank / ljg-constraint 都强调这个
  - **切痕风金属比喻**（"这一刀""钉死""砸实"）——ljg-blind / ljg-card 列入红线
  - **AI 套话**（"显而易见""值得注意""综上所述"）——ljg-writes / ljg-plain 列入 Gotchas
- **双分支设计** —— `master` 是 org-mode（Emacs 用户），`md` 是 Markdown（Obsidian / VSCode / Notion 用户）。**两次 git add / 一次 push** 的同步流程在 `ljg-push/Tools/Push.sh` 里

**6,889 stars 的来源不太可能是"AI 写作工具的实际用户"**——这个仓库的安装方式（`bunx skills add` + 双分支 + 各种自定义路径）门槛太高。**更可能的来源是"AI 写作方法论的读者"**——仓库 README 本身就是一份"高阶思维工具是怎么被设计出来"的范本。

**重要意义**——这个仓库证明了一件 Anthropic CoWork Skills 协议正在发生的事：**"AI 写什么"不再是个 prompt 问题，而是个"语义单位封装"问题**。每个 skill 不是"提示词模板"，而是"一份可被机器读、可被工程师审、可被用户机械激活的协议"。

---

## 这套系统适合谁用、谁可以等等

**适合：**

- **AI Agent 工程师**：想理解"Skills 协议"是什么——ljg-skills 是为数不多的"完整实现 + 真实用例"样本。它把 SKILL.md 6 段结构跑通了，每段都有具体作用
- **写作者 / 知识工作者**：想要"高阶思维工具"的具体可执行版本——ljg-is / ljg-rank / ljg-constraint / ljg-think / ljg-writes 单独拎出来都是让人手痒的工具
- **Emacs / Denote 用户**：用 `master` 分支的 org-mode 版本直接落地
- **Obsidian / VSCode / Notion 用户**：用 `md` 分支的 Markdown 版本
- **AI 安全研究者**：想看"用户如何把 AI 思维工具封装成可机械执行协议"——这是 AI Agent 治理的边缘主题

**可以等等：**

- **只想用 AI 写几篇博客的普通用户**——直接用 Claude / ChatGPT 足够，22 个 skill 的全套安装成本太高
- **不会装 Codex / Claude Code 子系统的用户**——这个仓库假设你已经熟悉 skills CLI 的工作机制
- **想找"AI 写作工具评测"的人**——这是"工具集"不是"评测"，没有 benchmark 数据
- **Windows 用户**——Bun + Playwright + `bunx` 链路在 Windows 上需要 WSL

**从哪里开始：**

1. **第一遍**：通读 README + `skills/ljg-writes/SKILL.md` + `skills/ljg-is/SKILL.md` 三份——这是仓库的"骨架"
2. **第二遍**：装一个 skill 到自己环境，跑一遍——`bunx skills add lijigang/ljg-skills -g -a codex --skill ljg-is -y` 是最快入口
3. **第三遍**：挑一个自己写作中的具体问题，用 ljg-is + ljg-writes 组合跑一遍
4. **第四遍**：研究 `ljg-paper` 的回流感——这是写作者最强力的"内功模型"
5. **最后**：翻 `scripts/install.sh` 和 `scripts/sync-push.sh` 看怎么把 skills 同步到 GitHub

---

## 收尾判断：SKILL.md 协议正在悄悄成为 AI 时代的内容资产格式

读完 ljg-skills 之后，最强烈的判断是：**它不是"AI 写作工具集"，而是一份"如何把主观能力封装成可执行协议"的工程范例**。

**ljg-skills 的真正价值**不在于"它的 22 个 skill 写得有多好"——而在于它**证明了一件事**：高阶思维工具（理解概念、拆书、写作、追本质）**是可以被拆成可机械执行协议**的。

如果把这 22 个 skill 的共同结构抽出：

```
YAML frontmatter（USE WHEN + NOT FOR + 触发场景）
+ 后端讲解引擎（不可见的回流链）
+ Workflow Routing（路由到不同工序）
+ 成文契约（可机械检查的成功标准）
+ Gotchas（反模式清单，拦退化路径）
+ Examples（跑通过的真实案例）
```

**这 6 段结构就是"AI 时代的语义单位模板"**——它让一个"模糊高阶能力"变成可被触发、可被评估、可被组合的最小单元。**Anthropic CoWork Skills 协议、OpenAI Agents SDK 的 agents.yaml、本仓库的 SKILL.md**——都在朝这个方向收敛。

**如果你在做 AI Agent 相关产品**，最值得从 ljg-skills 身上学三件事：

1. **把"模糊高阶能力"拆成可机械检查的成文契约**——ljg-writes 的 4 条契约（概念可指认 / 关系可运行 / 案例可映射 / 判断可迁移）比任何"prompt 模板"都更有工程价值
2. **用 Gotchas 列表取代品味**——把"我写得好因为我有 sense"翻译成"我写得好因为这 14 条 gotcha 拦住了所有退化路径"，知识因此可继承
3. **后端讲解引擎藏后台，前台只交结果**——**ljg-paper 的 x/R/f/E 回流链**写在 SKILL.md 内部，但前台文章里**从不出现**"零号模型"之类术语——这是"易用"和"可验证"两件事同时成立的关键

**真正会改变"AI 时代内容生产"的**，不是更大的模型，而是**这套"语义单位模板"**——它决定了"AI 写作"是继续停留在"prompt 调参"，还是进化到"可机械验证的工序组合"。ljg-skills 是这个进化方向上的一个**完整样本**。

---

## 附录：仓库关键事实卡

| 项 | 值 |
|---|---|
| 仓库 | `github.com/lijigang/ljg-skills` |
| 创建时间 | 2026-03-08 |
| Stars / Forks | 6,889 / 未公开 |
| 主语言 | TypeScript（少数）+ Org-mode（绝大多数 SKILL.md） |
| 协议 | MIT |
| SKILL.md 数 | 22（21 个独立 skill + 1 个 Learn 入口） |
| 双分支 | master（org-mode）/ md（Markdown） |
| 安装方式 | `bunx skills add lijigang/ljg-skills`（Vercel Labs skills CLI） |
| 插件标准 | Claude Code 插件（marketplace.json + plugin.json） |
| 工作流文档 | 21 个 Workflows/ 文件 |
| 视觉输出 | 4 种模式（长图 / 多卡 / 漫画 / 白板）+ Playwright 截图 |
| 视觉依赖 | Playwright + Chromium（ljg-card 需要） |
| 古文精读 | ljg-classic 覆盖《道德经》《论语》等经典 |
| 圆桌协议 | 4 档指令（可 / 止 / 深入此节 / 引入新人物） |
| 调试自检 | 6 档 gotchas + 翻译腔 + 切痕风金属比喻 三套红线 |
| 数据局限 | 公开版无 benchmarks；交付物只能落 Denote / `~/Documents/notes/` |

---

## 参考资料

- 仓库主页：https://github.com/lijigang/ljg-skills
- 安装脚本：https://github.com/lijigang/ljg-skills/blob/master/scripts/install.sh
- 双分支同步：https://github.com/lijigang/ljg-skills/blob/master/scripts/sync-push.sh
- 插件清单：https://github.com/lijigang/ljg-skills/blob/master/.claude-plugin/marketplace.json
- Vercel Labs skills CLI：https://github.com/vercel-labs/skills
- Anthropic Skills 协议：https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- Claude Code 插件：https://docs.claude.com/en/docs/claude-code/plugins
- OpenAI Agents SDK：https://openai.github.io/openai-agents-python/
- Denote 文件命名：https://github.com/protesilaos/denote
- 内置配套工具：所有 skill 都有 `Tools/` 子目录（如 `ljg-card/assets/capture.ts` 截图脚本、`ljg-card/assets/audit.ts` 校验脚本）
