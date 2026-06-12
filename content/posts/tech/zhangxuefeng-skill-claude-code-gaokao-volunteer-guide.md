---
title: "张雪峰.skill：把一位高考志愿名师的认知框架打包成 Agent Skill"
date: "2026-06-12T15:12:00+08:00"
slug: "zhangxuefeng-skill-claude-code-gaokao-volunteer-guide"
description: "alchaincyf/zhangxuefeng-skill 把张雪峰的高考志愿思维蒸馏成 SKILL.md，5 心智模型 + 8 决策启发式，50+ runtime 一行安装。"
draft: false
categories: ["技术笔记"]
tags: ["AgentSkill", "ClaudeCode", "PromptEngineering", "高考志愿", "AI"]
---

# 张雪峰.skill：把一位高考志愿名师的认知框架打包成 Agent Skill

> **类型**：典型 Agent Skill 项目解读（快速上手 + prompt/工具设计点评）
> **适合读者**：在 Claude Code、Codex、Cursor、OpenClaw 等 AI 编程/对话工具里使用自定义 Skills 的工程师与产品经理；对「把人物认知蒸馏成 prompt」这件事感兴趣的从业者。
> **本文立场**：纯技术视角，评测 SKILL.md 工程实现、prompt 设计、数据来源声明；**不替读者下任何高考/考研/职业规划建议**。

---

## 一句话判断

`alchaincyf/zhangxuefeng-skill`（下文简称「张雪峰.skill」）的工程价值不在于「用 AI 模仿张雪峰说话」，而在于它把一个真实人物的多源素材（5 本著作、15+ 篇深度采访、30+ 条一手语录、11 条关键决策、完整时间线）压成了一份**可以被任何 Skills 协议 runtime 加载的 SKILL.md**——8k+ stars 的成绩说明「人物认知蒸馏为 Agent Skill」这条路在中文社区已经被验证。

它由同作者的 `nuwa-skill`（女娲.skill）按一套「6 agent 并行调研 → 交叉验证 → 提心智模型 → 写 SKILL.md → 跑回归测试」的流水线自动生成，仓库本身也是这条流水线的**产物样本**。

---

## 仓库基本面

| 字段 | 值 |
| ---- | -- |
| 仓库 | [alchaincyf/zhangxuefeng-skill](https://github.com/alchaincyf/zhangxuefeng-skill) |
| Stars / Forks / Watch | 8,071 / 2,423 / 42（缓存抓取时刻 2026-06-12 15:14 BJT） |
| License | MIT |
| 主语言 | 无（仓库为纯 Markdown + YAML frontmatter 资产） |
| 最新提交 | 2026-06-12（持续维护中） |
| 协议 | 开放的 Agent Skills 协议（Claude Code / Codex / Cursor / OpenClaw / Hermes / CodeBuddy / Workbuddy / Gemini CLI / OpenCode 等 50+ runtime 兼容） |
| 关联项目 | `alchaincyf/nuwa-skill`（蒸馏器）、`steve-jobs-skill` / `elon-musk-skill` / `naval-skill` / `munger-skill` / `feynman-skill` / `taleb-skill`（同流水线产物） |

> 说明：文章里所有「现在」「截至」之类措辞，都以缓存时间为准；下次复测请以 GitHub 实时数为准。

---

## 文章形态选择

按 `github-article-writer/references/article-shapes.md` 的路由判断：

- README 完整、安装命令清晰、examples/ 里给完整对话记录 → 倾向「快速上手」
- 仓库价值集中在 SKILL.md 的 prompt 设计、心智模型提炼、调研方法论 → 需要附一段「prompt/工具设计点评」
- **不是**架构分析：没有并行机制、没有 benchmark、没有系统分层需要拆
- **不是**源码分析：没有可读源码，全是 Markdown 资产

所以走 **「快速上手 + prompt/工具设计点评」** 组合形态：先用一节把安装/调用路径跑通，再用一节剖析 SKILL.md 的内部结构、心智模型表、调研方法，结尾给适用边界与采用顺序。

---

## 第一部分：快速上手

### 1.1 安装

README 提供三种安装方式，**推荐**第一条：

```bash
# 方式一：跨 runtime 自动检测（推荐）
npx skills add alchaincyf/zhangxuefeng-skill

# 指定 runtime（可选）
npx skills add alchaincyf/zhangxuefeng-skill -a claude-code
npx skills add alchaincyf/zhangxuefeng-skill -a codex
npx skills add alchaincyf/zhangxuefeng-skill -a cursor
npx skills add alchaincyf/zhangxuefeng-skill -a openclaw
```

`npx skills` 是 [vercel-labs/skills](https://github.com/vercel-labs/skills) 这个通用 CLI 安装器，它会探测当前 runtime 并把 SKILL.md 放到对应目录（Claude Code → `~/.claude/skills/`，Cursor → `~/.cursor/skills/`，Codex → `~/.codex/skills/`，OpenClaw → `~/.openclaw/workspace/skills/`，依此类推）。

```bash
# 方式二：手动 clone（适用于不被自动安装器识别的 runtime）
git clone https://github.com/alchaincyf/zhangxuefeng-skill <runtime_skills_dir>/zhangxuefeng-skill

# 方式三：直接当参考资料（最差方案）
# 把 SKILL.md 内容贴进对话，让 LLM 临时按里面的 prompt 行为作答
```

### 1.2 调用

装好之后，对话里说人话就行：

```text
用张雪峰的视角帮我分析这个专业选择
张雪峰会怎么看这个职业方向？
切换到张雪峰，我孩子要填志愿了
```

Agent runtime 会按 Skills 协议自动把 `SKILL.md` 注入到 system prompt（具体时机取决于 runtime 的「auto-load / slash command / on-demand」策略——Claude Code 是「描述匹配即自动激活」类）。

### 1.3 最小验证用例

README 给了 4 个对照场景，这里只摘一个，看一下激活前后回答风格的差异：

```text
问：我孩子今年高考，560分，河南的，想学金融，你怎么看？

未激活 SKILL：泛泛而谈「金融是个好专业，但要结合孩子兴趣和职业规划……」

激活 SKILL 后的回答节选（README 原文）：
  「停停停，你先别急着说金融。我问你几个问题。
   家里是做金融的吗？爸妈在银行、证券公司、基金公司？
   有没有亲戚在这个行业里？没有？那我跟你说，金融这个行业，千万别碰。
   你去看看每年金融专业毕业的学生，中位数去了哪？……」
```

提示词里同时触发了 README 自报的三个心智模型：`就业倒推法`（看中位数去向）、`家庭背景分流`（先问家里资源）、`社会筛子论`（双非金融 vs 985 的竞争现实）。这就是后面要讲的「为什么 SKILL.md 写得好，模型就会按框架思考，而不只是换语气」。

### 1.4 常见坑

- **runtime 不识别 Agent Skills 协议**：fallback 到「方式三 粘贴 SKILL.md」，但效果会下降——上下文没有协议层的自动激活机制，模型容易在长对话里漂移回通用语气。
- **跟其他 persona skill 冲突**：仓库作者还出了乔布斯/马斯克/纳瓦尔/芒格/费曼/塔勒布 6 个 skill。如果一次会话里同时激活多个，模型会做平均，反而失去张力。**建议**一次只装一个用一段时间，确实稳定了再换。
- **当 ChatGPT 套皮用**：README 自己声明「**这不是 ChatGPT 套了个张雪峰面具**」——意思是判断点不在「像不像」，而在「能不能稳定调用 5 个心智模型」。如果发现回答只有语气像，框架没出来，回退看 SKILL.md 是不是被 runtime 正确加载。

---

## 第二部分：SKILL.md 工程结构拆解

仓库根目录非常干净：

```
zhangxuefeng-skill/
├── README.md
├── SKILL.md                 # 可直接安装使用
├── references/
│   └── research/            # 6 个调研文件
│       ├── 01-writings.md   # 著作与系统思考
│       ├── 02-conversations.md  # 深度采访与对谈
│       ├── 03-expression-dna.md # 表达风格 DNA
│       ├── 04-external-views.md# 他者视角与批评
│       ├── 05-decisions.md  # 重大决策分析
│       └── 06-timeline.md   # 完整人生时间线
└── examples/
    └── demo-conversation.md # 实战对话记录
```

注意三个细节：

1. **SKILL.md 是契约**，6 个 `references/research/*.md` 是**证据链**。这跟普通 README-as-prompt 的最大区别：模型激活 skill 时，runtime 可以选择只注入 SKILL.md，也可以按需把 `references/` 拉进上下文（取决于 runtime 实现）。这种「轻量契约 + 重证据库」的分层，是 Agent Skills 协议的典型用法。
2. **examples/ 不冗余**：`demo-conversation.md` 同时承担两个职责——既给用户做效果示例，也给模型做 few-shot 锚点（少样本示例）。README 里那句「完整对话记录在 examples/ 目录」实际是个隐式机制说明。
3. **MIT + 显式允许再蒸馏**：「随便用，随便改，随便蒸馏」——这跟后面要讲的 nuwa 流水线是一对配套工程：蒸馏器允许基于本 skill 再蒸馏新人物。

### 2.1 SKILL.md 内核：5 × 8 × 5 结构

公开 README 透露的 SKILL.md 内部组织是一个**3 段 18 元素**结构：

| 段 | 元素 | 角色 |
| -- | ---- | ---- |
| 心智模型 | 5 个（社会筛子论 / 选择>努力 / 就业倒推法 / 阶层现实主义 / 争议即传播） | **判断框架**——决定模型怎么分析问题 |
| 决策启发式 | 8 条（灵魂追问法 / 中位数原则 / 不可替代性检验 / 500 强测试 / 家庭背景分流 / 城市优先原则 / 10 年后压迫测试 / 认态度不认事实道歉法） | **可操作清单**——遇到具体问题怎么拆 |
| 表达 DNA | 5 个维度（句式 / 词汇 / 节奏 / 幽默 / 确定性） | **风格控制**——决定模型怎么说话 |
| 内在张力 | 5 对（寒门代言人 vs 亿万富翁 / 自己跨专业成功 vs 劝人选对专业 / 喊「注意身体」 vs 每天工作十几小时 / 说要克制 vs 嘴比脑快 / 争议是策略还是性格） | **反扁平化**——防止模型简化成单线人格 |

**工程点评**：5×8×5 这个数字组合的隐藏含义是「**框架不互斥**」。同一个问题可以同时触发多个心智模型（比如「560 分学金融」同时命中社会筛子论、就业倒推法、家庭背景分流），多个模型之间用**张力表**兜底，防止模型挑一个最顺手的简单回。这种「多框架 + 显式张力」的设计，是 SKILL.md 比「一张 prompt 卡片」更稳的关键。

### 2.2 数据来源声明（不取代原始材料）

README 显式排除了知乎/微信公众号/百度百科三类来源。剩余一手 + 二手来源合计 13 个，全部是出版著作、官方演讲或主流媒体深度对谈：

- **一手（8）**：《你离考研成功，就差这本书》(2016) · 《方向比努力更重要》(2021) · 《选择比努力更重要》(2021/2023 修订) · 《决胜大学》(2024) · 《从就业看专业》(2025 遗作) · B 站《演说家》完整版 · 新浪财经 CEO 邓庆旭深度对谈 · 界面新闻 / 中国新闻周刊采访
- **二手（5）**：钛媒体 / 虎嗅 / 三联生活周刊 / 36 氪 / 21 经济网

> 这条来源声明在 Agent Skill 类项目里其实是个**工程信号**——它告诉我们 SKILL.md 的事实判断锚点是哪几本书，模型遇到超出这 13 个来源的问题时，应该回退还是应该拒绝，prompt 里有据可查。

### 2.3 Prompt 设计点评

把 SKILL.md 当 prompt 文本读，有几条值得抄：

1. **可被 runtime 索引的 frontmatter**：所有 Skills 协议 runtime 都会先解析 SKILL.md 的 YAML frontmatter，再决定激活条件。README 隐含了 frontmatter 至少有 `name`、`description` 两个字段，否则 Claude Code 不会做描述匹配。**注意**：本文作者从公开页面只能确认 SKILL.md 存在，不能确认 frontmatter 字段细节；要写新 skill 时请直接看本仓库的 `SKILL.md` 源文件。
2. **框架优先于语料**：5 个心智模型是「思维工具」，8 条决策启发式是「操作步骤」，表达 DNA 是「语气」。**先定框架，再定语料，最后定语气**——这比直接喂语料稳得多。
3. **显式张力避免单线人格**：5 对内在张力是反 prompt 漂移的护栏——很多「名人 persona prompt」用着用着就退化成单线金句复读机，张力表就是拿来打断这个过程的。
4. **冷启动 few-shot**：`examples/demo-conversation.md` 给了 4 段完整对话作为少样本锚点。**注意点**：README 自报在效果示例里就把触发了哪些心智模型标在对话后面，这种「例题 + 解题思路」的形式比单纯「例题 + 答案」对模型推理更友好。

---

## 第三部分：女娲（nuwa）流水线——SKILL 是怎么造出来的

仓库 README 末尾直接给出了**元仓库** `alchaincyf/nuwa-skill` 的入口和女娲的工作流：

```text
输入一个名字
  → 6 个 Agent 并行调研（著作 / 对话 / 表达 / 批评 / 决策 / 时间线）
  → 交叉验证提炼心智模型
  → 构建 SKILL.md
  → 质量验证（3 个已知测试 + 1 个边缘测试 + 风格测试）
```

把这条流水线映射回仓库结构：

| 流水线阶段 | 产物 | 在本仓库的位置 |
| ---------- | ---- | -------------- |
| 6 个并行调研 | 一手 + 二手材料落库 | `references/research/01-writings.md` ~ `06-timeline.md` |
| 交叉验证 | 5 个心智模型 + 8 条决策启发式 | `SKILL.md`（心智模型段 / 启发式段） |
| 构建 SKILL.md | 5 对张力 + 表达 DNA | `SKILL.md`（张力段 / 表达段） |
| 质量验证 | 4 个 demo 对话 | `examples/demo-conversation.md` + README 里的「效果示例」 |
| 蒸馏器本身 | nuwa-skill 仓库 | （外链，README 给 `npx skills add alchaincyf/nuwa-skill`） |

**工程意义**：这条流水线意味着「张雪峰.skill」不是手工雕出来的 prompt 艺术品，而是一个**可复制的工程产物**。同作者下乔布斯、马斯克、纳瓦尔、芒格、费曼、塔勒布 6 个 skill，理论上都可以由 nuwa 用相同步骤蒸馏出来——这是 Agent Skills 生态里「人物即包」范式的真正工程底座。

---

## 第四部分：适用边界与采用顺序

### 4.1 适合用

- 你的 runtime 支持 Agent Skills 协议自动加载（Claude Code / Cursor / Codex / OpenClaw / Gemini CLI / OpenCode 等）
- 你需要给团队配一个**语气稳定、框架可解释**的对话 persona（比如「产品评审视角」「风控视角」），并且愿意用 SKILL.md + research/ 的分层来管理事实锚点
- 你想研究「人物认知蒸馏」这条 pipeline 自己复制——直接装 nuwa-skill 跑一遍就能拿到一个新人物的 SKILL.md

### 4.2 不适合用

- 你的 runtime 不识别 Skills 协议，只能用「方式三 粘贴 SKILL.md」——这时效果会明显下降，建议直接放弃或先升级 runtime
- 你期待 SKILL.md 给出**超出 13 个公开来源的事实判断**——prompt 里没有的东西，模型编不出来
- 你在做**真实的高考志愿决策**——SKILL.md 是工程产物不是职业咨询，本文作者无法替读者承担任何决策责任；具体报考请以高校官方招生章程和省级考试院政策为准

### 4.3 团队采用顺序建议

1. **先装 nuwa-skill**，跑一遍它的 demo，熟悉 6 agent 调研流水线的输出格式
2. **再装一个你熟的人物 skill**（推荐芒格或费曼，结构化程度高），用它写一份工作周报或代码评审，观察 SKILL.md 是否被 runtime 真正激活
3. **最后才装张雪峰.skill**——它带「社会筛子论 / 阶层现实主义」这类强观点框架，更适合**有判断场景**的对话，不适合「随便聊聊」

### 4.4 这篇文章刻意不覆盖

- 真实张雪峰本人的观点是否完全被 SKILL.md 复刻——这是人物本人 / 家属的事，本文无法核证
- 张雪峰的具体志愿建议是否适用于某一年的某一分数段——边界外，省考试院政策每年都在变
- 8k+ stars 是否能持续——流量本身不是工程指标，看后续 PR / Issue 活跃度更准
- nuwa-skill 的具体 prompt 与代码实现——属于另一仓库，本仓库 README 只给安装命令

---

## 参考与延伸阅读

- 仓库本体：[alchaincyf/zhangxuefeng-skill](https://github.com/alchaincyf/zhangxuefeng-skill)
- 蒸馏器（女娲）：[alchaincyf/nuwa-skill](https://github.com/alchaincyf/nuwa-skill)
- 同流水线其他产物：乔布斯 / 马斯克 / 纳瓦尔 / 芒格 / 费曼 / 塔勒布（README「更多 .skill」一节列出安装命令）
- 通用 Skills CLI：[vercel-labs/skills](https://github.com/vercel-labs/skills)（`npx skills add` 来源）
- 本文站内延伸：[Agent Skills：addyosmani 的生产级 AI 编程工程技能框架]({{</* relref "agent-skills-addyosmani-production-engineering-guide.md" */>}}) · [9arm-skills：让 AI 编程助手按流程干活的合约式 Skills]({{</* relref "9arm-skills-claude-code-agent-skills-guide.md" */>}})

---

> **数据来源声明**：本文所有事实点（stars / forks / license / 仓库结构 / SKILL.md 元素 / 13 个调研来源 / nuwa 流水线）均来自上文 GitHub 仓库 README 与缓存抓取（2026-06-12 15:14 BJT），未补充任何外部未在仓库中公开声明的信息。
