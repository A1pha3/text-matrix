---
title: 'kangarooking/cangjie-skill 原理拆解：用 RIA-TV++ 流水线把书 / 长视频 / 播客蒸馏成可被 agent 调用的方法论 skill 仓库'
date: 2026-07-17T02:57:12+08:00
lastmod: 2026-07-17T02:57:12+08:00
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "Skills", "知识蒸馏", "RIA", "AI Agent", "方法论"]
description: "cangjie-skill 是 kangarooking 维护的开源 skill 蒸馏流水线，3.2k stars，用 RIA-TV++ 七阶段方法（Adler 整体阅读 → 5 路并行提取 → 三重验证 → RIA++ 构造 → Zettelkasten 链接 → 压力测试 → 交付）把书 / 长视频 / 播客转成可被 Claude Code / Cursor 调用的 skill 仓库。本文拆解它的方法论骨架、5 个并行 extractor、三重验证筛、21 个已生成 skill pack 实战案例。"
weight: 1
slug: "kangarooking-cangjie-skill-methodology-distillation"
author: text-matrix
---

## 一句话判断

**cangjie-skill（[kangarooking/cangjie-skill](https://github.com/kangarooking/cangjie-skill)）是一个 3.2k stars 的方法论蒸馏流水线，作者 kangarooking**。它解决一个具体痛点：你看了很多书、收藏了很多长视频、听过很多播客，但"就是用不起来"——知识停留在"看过 / 听过 / 收藏过"层面，没法在真实决策里被调用。cangjie-skill 用 **RIA-TV++** 七阶段流水线（Adler 整体阅读 → 5 路并行提取 → 三重验证 → RIA++ 构造 → Zettelkasten 链接 → 压力测试 → 交付）把任意长篇原始内容（书、长视频字幕、播客文字稿、访谈）转成一个多 skill 仓库（`BOOK_OVERVIEW.md` + `INDEX.md` + `DIGEST.md` + `GLOSSARY.md` + 若干 `*/SKILL.md` + `test-prompts.json`），让 Claude Code / Cursor 真正能在 agent loop 里调用这些方法论。区别于 [nuwa-skill](https://github.com/alchaincyf/nuwa-skill)（蒸馏人）与 [darwin-skill](https://github.com/alchaincyf/darwin-skill)（让 skill 自我进化），cangjie-skill 是"蒸馏书"，形成完整的 skill 三件套生态。

如果你想"系统读完一本书不是写读书笔记、而是产出能用的 skill 工具包"，这篇文章值得读完整。

---

## 系统地图

```
┌────────────────────────────────────────────────────────────────────────┐
│                  cangjie-skill (RIA-TV++ 流水线)                          │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Stage 0  整体内容理解（Adler 分析阅读）                            │ │
│  │    └─ 借鉴 Mortimer Adler：结构 / 解释 / 批判 / 应用                │ │
│  │    └─ 输出 BOOK_OVERVIEW.md                                        │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                  ↓                                       │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Stage 1  并行提取（5 个 extractor 同时跑）                        │ │
│  │    ├─ framework-extractor        框架                              │ │
│  │    ├─ principle-extractor        原则                              │ │
│  │    ├─ case-extractor             案例                              │ │
│  │    ├─ counter-example-extractor  反例                              │ │
│  │    └─ glossary-extractor         术语                              │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                  ↓                                       │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Stage 1.5  三重验证筛选（Triple Verification）                     │ │
│  │    ├─ V1 跨域验证    原内容中至少 2 处独立佐证（跨域）              │ │
│  │    ├─ V2 预测力测试  能回答内容里未明说的新问题                      │ │
│  │    └─ V3 独特性检验  不是"任何聪明人都会说的常识"                    │ │
│  │    通过率通常 25-50%                                                │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                  ↓                                       │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Stage 2  RIA++ 构造                                                │ │
│  │    R = 原文引用 / I = 用自己的话重写                                 │ │
│  │    A1 = 书中案例 / A2 = 未来触发场景                                │ │
│  │    E = 可执行步骤 (Execution)  / B = 边界与盲点 (Boundary)          │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                  ↓                                       │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Stage 3  Zettelkasten 链接                                        │ │
│  │    └─ 找出 skill 间的依赖 / 对比 / 组合关系                         │ │
│  │    └─ 生成 INDEX.md 和引用图                                       │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                  ↓                                       │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Stage 4  压力测试                                                  │ │
│  │    └─ 为每个 skill 设计测试用例（含诱饵题、跨 skill 混淆）           │ │
│  │    └─ 未通过的回炉重做                                              │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                  ↓                                       │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Stage 5  交付                                                      │ │
│  │    ├─ DIGEST.md        面向读者的精华长文（不想读全书？看这篇）    │ │
│  │    ├─ BOOK_OVERVIEW.md 全局理解                                      │ │
│  │    ├─ INDEX.md         技能地图                                      │ │
│  │    ├─ GLOSSARY.md      术语词典                                      │ │
│  │    ├─ */SKILL.md       独立模块                                      │ │
│  │    └─ test-prompts.json 验证触发场景                                  │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                  ↓                                       │
│                  ┌───────────────────────────────┐                       │
│                  │ Claude Code / Cursor skills/  │                       │
│                  │ （真正可被 agent 调用）         │                       │
│                  └───────────────────────────────┘                       │
└────────────────────────────────────────────────────────────────────────┘
```

这张图最重要的一条路径：**Stage 1.5 三重验证是 cangjie-skill 区别于"书摘工具"的核心质量门**。没有这一步，所有 extractor 的输出都会沦为金句堆砌；有了这一步，通过率只剩 25-50%——把真正"作者花长时间打磨出来的方法论"留下，把"看起来漂亮但只是常识"的内容淘汰。

---

## 边界与角色划分

cangjie-skill 的工程边界可以按"角色 + 决策门"分四组：

| 阶段 | 角色 | 谁负责 | 谁不允许 |
|---|---|---|---|
| Stage 0–1 | 内容理解 + 提取 | LLM agent 按 prompt 跑 | 跳过 Adler 直接抽金句 |
| Stage 1.5 | 质量筛选（决策门） | Triple Verification | 把"看着漂亮但常识"当 skill |
| Stage 2–3 | 构造 + 链接 | LLM 按模板生成 | 跳过 Zettelkasten 直交付 |
| Stage 4–5 | 测试 + 交付 | LLM 跑 test-prompts.json | 跳过压力测试直接装 |

不变项之外，**cangjie-skill 明确不做**的事：

- ❌ **不**做内容总结 / 摘要压缩。"系统会把内容拆成多个带触发条件、适用边界、使用方式和关联关系的 skills，而不是把整份内容压缩成一篇泛化总结"——目标是**结构化复用**，不是**压缩**。
- ❌ **不**照单全收。README 写："高价值内容里真正值得变成工具的内容只有一小部分——需要严格的筛选而不是照单全收"——三重验证就是筛选门。
- ❌ **不**面向人消费、面向 agent 执行。RIA-TV++ 的两个 `++`（E = Execution / B = Boundary）是给 agent 看的，不是给读者看的。
- ❌ **不**做视频下载 / 字幕提取。如果源材料是长视频，要先配 [video-downloader](https://github.com/kangarooking/kangarooking-skills/tree/main/video-downloader) skill；cangjie-skill 只负责"拿到转写文本之后"那一步。

这四条"不做"恰好决定了 cangjie-skill 的设计取舍——下面拆开看。

---

## 关键机制：七阶段流水线是怎么把一本书变成 skill 仓库的

### 1. Stage 0 — Adler 分析阅读做整体理解

`methodology/01-stage0-adler.md` 借鉴 Mortimer Adler 的分析阅读法，把"读一本书"拆成四步：

- **结构**：骨架是什么？章节怎么组织？
- **解释**：作者在每章说了什么？
- **批判**：作者说的对吗？有没有漏洞？
- **应用**：我能不能用这个？

输出 `BOOK_OVERVIEW.md`，是后续所有 extractor 的"全局地图"。如果跳过这一步直接抽金句，5 个 extractor 互相矛盾的概率非常高。

### 2. Stage 1 — 5 路并行 extractor

`methodology/02-stage1-parallel-extract.md` 同时派 5 个专项提取器：

| Extractor | 抓什么 | 输出 |
|---|---|---|
| `framework-extractor` | 作者的框架（"X 分三层" / "四步流程"） | 框架候选 |
| `principle-extractor` | 作者的原则（"永远先 X 再 Y"） | 原则候选 |
| `case-extractor` | 书中案例（故事、人物、场景） | 案例库 |
| `counter-example-extractor` | 反例（作者用来证明"这样做会失败"的例子） | 边界条件 |
| `glossary-extractor` | 术语（作者自创 / 重新定义的词） | 术语词典 |

5 个 extractor 并行跑、互不知道对方输出——这是避免"互相污染"的关键。如果串行跑，第二个 extractor 会受第一个影响，倾向于强化第一个的判断而不是独立发现。

### 3. Stage 1.5 — 三重验证（核心质量门）

`methodology/03-stage1.5-triple-verify.md` 是整套流水线最值得读的一节：

**V1 跨域验证（Cross-domain）**

> 这个单元在书中至少 2 个独立的语境下有佐证吗？

通过案例：《穷查理宝典》中"逆向思维"在投资决策、避免灾难、教学方法三个独立场景中都出现 → 通过。

不通过案例：某个漂亮句子只在一章里出现过一次，没有书内的独立证据 → 降级为金句 example。

**V2 预测力测试（Predictive Power）**

> 能用这个单元，推导出书里没明说的某个问题的答案吗？

- 自己设计一个书中没直接讨论过的场景
- 用这个方法论去分析
- 通过：得出有意义、非平庸的结论
- 不通过：只能得出"努力就会成功"之类的废话 → 降级

**V3 独特性检验（Exclusivity）**

> 这个单元是否是"任何聪明人都会说的常识"？

通过案例：段永平的"stop doing list"——主动列出不做什么，反常识 → 通过。

不通过案例："要尊重时间"——太常识了，没人需要一个 skill 来告诉自己这个。

**通过率通常 25-50%**——这意味着如果 extractor 抽了 100 个候选，最终进入 Stage 2 构造的可能只有 25-50 个。这是质量门，不是 throughput 门。

**失败模式**（README 直接列了三类作弊）：

1. **V1 作弊**——把同一例子换个说法算两处。要求：必须不同章节 + 不同对象 + 不同结论。
2. **V2 作弊**——用一个其实书里讨论过的类似问题冒充"新问题"。要求：新问题应该让人第一眼不知道书里怎么说。
3. **V3 过松**——只要"说得比较文雅"就认为不是常识。要求：看**内容**本身是否反直觉，而不是措辞。

**用户轻确认**：通过 Triple Verification 后，agent 问用户一句"这 N 个会做成 skill，有想捞回或砍掉的吗？"——得到确认再进入 Stage 2-4。这一句话的成本能避免大量返工。

### 4. Stage 2 — RIA++ 构造（六个维度结构化）

`methodology/04-stage2-ria-plus.md` 把验证通过的候选按六个维度结构化：

- **R**（Reading）——原文引用
- **I**（Interpretation）——用自己的话重写
- **A1**（书中案例）——作者自己举的例子
- **A2**（未来触发场景）——未来什么场景下我会调用这个 skill
- **E**（Execution，可执行步骤）——这是 `++` 的第一个 `+`，给 agent 看的执行步骤
- **B**（Boundary，边界与盲点）——这是 `++` 的第二个 `+`，什么场景下不能用

注意 **RIA 来源于赵周《这样读书就够了》的便签拆书法**——这是 cangjie-skill 不是凭空发明方法论、而是把成熟读书方法工程化的明证。E + B 是给 agent 加的两个新维度，不是人读卡片的标配。

### 5. Stage 3 — Zettelkasten 链接

`methodology/05-stage3-zettelkasten.md` 找 skill 之间的依赖、对比、组合关系。德国社会学家 Niklas Luhmann 的卡片盒笔记法（Zettelkasten）原本是给学者做知识管理用的，cangjie-skill 把它改造成"skill 间链接"——找出 `skill_a.md` 依赖 `skill_b.md` 的前提、A 和 B 在某种场景下可以组合使用、A 和 C 是同一思路在不同领域的应用。

输出 `INDEX.md`（技能地图）和引用图。这一步决定了 skill 仓库是不是"一堆独立 SKILL.md"还是"互相连通的知识网络"。

### 6. Stage 4 — 压力测试（Stage 4 含诱饵题）

`methodology/06-stage4-pressure-test.md` 为每个 skill 设计测试用例，**含跨 skill 混淆测试**——故意给出"这个 skill 不该被触发"的诱饵题，验证 skill 不会被错误激活。

未通过的 skill 回炉重做，不是直接删除。

### 7. Stage 5 — 交付（真正安装到 Claude Code）

`methodology/07-stage5-deliver.md` 把通过测试的 skill 安装到 `~/.claude/skills/`（或 Cursor skills 目录），让它们真正可被 agent 调用。同时输出：

- `DIGEST.md`（面向读者的精华长文，**人类视角**的总结）
- `BOOK_OVERVIEW.md`（全局理解）
- `INDEX.md`（技能地图）
- `GLOSSARY.md`（术语词典）
- `*/SKILL.md`（独立模块，给 agent 用的 SKILL.md）
- `test-prompts.json`（验证触发场景，给测试 agent 用）

DIGEST.md 和 SKILL.md 是双产物——前者给人看、后者给 agent 看。这一步让 cangjie-skill 不只是"内部工具"，也对外可读。

---

## 任务流案例：把《穷查理宝典》蒸馏成 skill 仓库

`kangarooking/poor-charlies-almanack-skill`（12 skills）是 README 列出的实战案例。把上面七阶段串起来跑：

**Step 0：准备原文本**

《穷查理宝典》PDF 或 EPUB 转纯文本，长度通常 30-50 万字。

**Step 1：Stage 0 Adler 整体阅读**

Agent 跑 Stage 0 prompt，输出 `BOOK_OVERVIEW.md`：作者是芒格，全书 11 讲，主要议题是多元思维模型、逆向思维、心理学误判、跨学科学习。

**Step 2：Stage 1 5 路并行 extractor**

- framework-extractor 抽到"多元思维模型 80/20"、"lollapalooza 效应"等框架候选
- principle-extractor 抽到"反过来想"、"避免心理误判"、"能力圈"等原则候选
- case-extractor 抽到芒格 / 巴菲特的具体投资案例
- counter-example-extractor 抽到"致命的几次投资失败"
- glossary-extractor 抽到芒格自创术语

**Step 3：Stage 1.5 三重验证**

100+ 候选经过 V1（跨域）+ V2（预测力）+ V3（独特性），通过 30 个左右（25-50% 通过率）。"逆向思维"通过——V1 在 3 个独立场景有佐证、V2 能解释"如何面试一个不知道答案的问题"、V3 是反直觉的排序。"要努力工作"被淘汰——V3 过不了（常识）。

**Step 4：Stage 2 RIA++ 构造**

通过的 30 个候选按 R/I/A1/A2/E/B 六个维度结构化，写成 30 个 `*/SKILL.md`。

**Step 5：Stage 3 Zettelkasten 链接**

找出"逆向思维" ↔ "能力圈"（组合使用）、"lollapalooza 效应" ↔ "误判心理学"（依赖关系）、"多元思维模型" ↔ "能力圈"（同一思路的不同切面）。生成 `INDEX.md`。

**Step 6：Stage 4 压力测试**

为"逆向思维" skill 设计诱饵题："'逆向思维' 是不是说 '反过来想就一定对'？"——skill 应该拒绝触发并澄清"逆向思维是优先反着想，但反着想之后还要正向验证"。未通过的 skill 回炉。

**Step 7：Stage 5 交付**

输出最终 skill 仓库：

```text
poor-charlies-almanack-skill/
├── BOOK_OVERVIEW.md
├── INDEX.md
├── DIGEST.md           # 面向读者
├── GLOSSARY.md
├── 01-inversion-thinking/SKILL.md
├── 02-lollapalooza/SKILL.md
├── 03-multiple-models/SKILL.md
├── ...
└── test-prompts.json
```

安装到 `~/.claude/skills/`，Claude Code 在 agent loop 里能直接调用这些 skill。

---

## 与同类项目的横向对照

| 维度 | cangjie-skill | nuwa-skill | darwin-skill | 通用读书笔记工具（如 Obsidian + Readwise） |
|---|---|---|---|---|
| 蒸馏对象 | 书 / 长视频 / 播客 | 人（思维方式、表达 DNA） | 任意 skill | 书 / 文章 / 推文 |
| 输出形态 | 多 skill 仓库 + DIGEST.md | 单个 skill（人格） | skill 进化机制 | 笔记 + 标签 |
| 方法论骨架 | RIA-TV++（7 阶段） | 个人风格建模 | skill 自我迭代 | 用户自定义 |
| 质量门 | Triple Verification（3 重） | 风格一致性 | 评估指标 | 无 |
| 目标消费者 | Agent + 人（双产物） | Agent | Agent | 人 |
| 通过率 | 25-50% | n/a | n/a | n/a |
| 并行提取器 | 5 个 | 1 个（人格建模） | 1 个（进化策略） | 无 |
| 跨 skill 链接 | Zettelkasten | 无 | 无 | 反向链接 |
| 压力测试 | 含诱饵题 | 风格一致性 | 性能基准 | 无 |
| License | MIT | n/a（开源） | n/a（开源） | MIT / 商业 |
| Stars | 3.2k | n/a | n/a | n/a |

这张表想表达一件事：**cangjie-skill 是少数把"读书方法论"（Adler + 拆书法 + Zettelkasten）工程化成 7 阶段流水线、并加上 Triple Verification 质量门 + 跨 skill 压力测试的开源 skill**。它的工程深度（通过率 25-50% + 5 路并行 extractor + Zettelkasten 链接 + 双产物交付）不是通用笔记工具或简单 prompt 模板能复刻的。

---

## 适用边界

**推荐使用**：

- 读完一本书 / 长视频 / 播客，希望产出"能被 agent 调用"的方法论 skill 仓库
- 团队在做知识管理、想用 agent 把"高价值长内容"自动化蒸馏
- 已经在用 Claude Code / Cursor，希望把 skill 真正安装到本地 skills 目录
- 想做"蒸馏人 + 蒸馏书 + skill 自我进化"三件套（cangjie-skill + nuwa-skill + darwin-skill 配套使用）
- 想用 Zettelkasten 思路做 skill 间链接、避免一堆独立 SKILL.md

**不推荐使用**：

- 只是想写读书笔记 / 摘要 → 用 Obsidian / Readwise 更轻量，cangjie-skill 是 overkill
- 内容短（推文 / 短文 / 短博客）→ RIA-TV++ 流水线对小内容不适用
- 源材料没有字幕 / 转写文本（纯视频纯音频无文本）→ 配 [video-downloader](https://github.com/kangarooking/kangarooking-skills/tree/main/video-downloader) skill 先处理
- 团队不需要 agent 调用、只想要可读长文 → cangjie-skill 的 7 阶段是为"agent + 人"双产物设计的，纯人读场景太重
- 没耐心做 Triple Verification → 没有质量门，cangjie-skill 就退化成"金句收集器"，不如直接读 DIGEST.md

---

## 决策建议

按目标选：

1. **个人 / 小团队、想把 N 本书蒸馏成 skill 工具包** → 直接装 cangjie-skill，按 README 给的 7 阶段跑
2. **中型团队、有专门知识管理需求** → 配 video-downloader 一起用，统一处理书 + 视频 + 播客
3. **AI 工程师 / prompt 工程师、研究"如何让 agent 真正用上知识"** → 看 `methodology/03-stage1.5-triple-verify.md` + `methodology/06-stage4-pressure-test.md` 是少数公开的"agent 知识质量门"参考实现
4. **内容创作者、想把自己的内容蒸馏成可被 AI 引用的 skill** → 用 cangjie-skill 跑自己写的书 / 课程，配 `darwin-skill` 做迭代
5. **已经在用 nuwa-skill** → cangjie-skill 是补"蒸馏书"那一维，三件套一起用
6. **完全不需要 agent、只想要书摘** → 用通用笔记工具，不要硬上 cangjie-skill

---

## 阅读路径

按需读：

- **只想上手**：README + `methodology/00-overview.md` + `SKILL.md`
- **想理解方法论骨架**：`methodology/01-stage0-adler.md` → `02-stage1-parallel-extract.md` → `03-stage1.5-triple-verify.md` → `04-stage2-ria-plus.md`
- **想理解 skill 链接**：`methodology/05-stage3-zettelkasten.md`
- **想理解测试**：`methodology/06-stage4-pressure-test.md` + `templates/test-prompts.json`
- **想理解交付**：`methodology/07-stage5-deliver.md` + `templates/SKILL.md` + `templates/INDEX.md`
- **想看实战案例**：[poor-charlies-almanack-skill](https://github.com/kangarooking/poor-charlies-almanack-skill) + [buffett-letters-skill](https://github.com/kangarooking/buffett-letters-skill) + [huangdi-neijing-skill](https://github.com/kangarooking/huangdi-neijing-skill)（22 skills 跨《素问》《灵枢》）
- **想看生态**：[nuwa-skill](https://github.com/alchaincyf/nuwa-skill) + [darwin-skill](https://github.com/alchaincyf/darwin-skill)

---

## 边界声明

本文基于 `kangarooking/cangjie-skill` 仓库 README（2026-07-16 抓取）、`methodology/00-overview.md`、`methodology/03-stage1.5-triple-verify.md`、GitHub API 仓库元数据（3.2k stars、490 forks、Python 主语言、MIT license）。仓库处于活跃迭代期，7 阶段流水线与 5 个 extractor prompt 在持续微调；已生成的 21 个 skill pack（[buffett-letters-skill](https://github.com/kangarooking/buffett-letters-skill) 20 skills、[cognitive-dividend-skill](https://github.com/kangarooking/cognitive-dividend-skill) 15 skills、[huangdi-neijing-skill](https://github.com/kangarooking/huangdi-neijing-skill) 22 skills 等）作为实战案例展示方法论有效性。

cangjie-skill 是少数把"读书方法论"（Adler 分析阅读 + 拆书法 + Zettelkasten）工程化成 7 阶段流水线的开源 skill，Triple Verification 质量门 + 跨 skill 压力测试是它区别于"书摘工具"的核心特征；如果你的工作流强依赖某本特定书的特定章节，需要评估 cangjie-skill 在该维度的抽取通过率（25-50%）是否影响最终交付。
