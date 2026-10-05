---
title: "Awesome Persona Distill Skills：人格蒸馏 Agent Skills 的完整指南"
date: "2026-04-09T13:05:00+08:00"
lastmod: "2026-10-05T00:00:00+08:00"
slug: "awesome-persona-distill-skills-agent-skills-guide"
github_repo: "xixu-me/awesome-persona-distill-skills"
source_key: "gh:xixu-me/awesome-persona-distill-skills"
description: "xixu-me 收录的人格蒸馏 Agent Skills 清单解读：生态从同事.skill 到 45 再到 71 个条目的演进，女娲.skill 的真实工作流程，Agent Skills 开放标准与贡献机制，以及两条可复现的任务流。"
draft: false
categories: ["技术笔记"]
tags: ["Agent Skills", "AI助手", "记忆系统", "Claude Code", "开源项目"]
---

# Awesome Persona Distill Skills：人格蒸馏 Agent Skills 的完整指南

2026 年 3 月 30 日，一个叫"同事.skill"的仓库出现在 GitHub 上，作者的想法很直接：把前同事的工作习惯、沟通方式整理成 AI 可复用的 Skill。一周之内，这个想法长出了一整套生态——自己.skill（4 月 1 日）、女娲.skill（4 月 5 日），以及把这些散落仓库收拢起来的收录清单 [awesome-persona-distill-skills](https://github.com/xixu-me/awesome-persona-distill-skills)（4 月 6 日）。本文写作时（4 月 9 日），清单收录 45 个 Skills；到 2026 年 10 月 5 日复查时，已经涨到 71 个，主仓库拿了 4,675 个 star。

清单作者 xixu-me 对"人格蒸馏"的定义写得很克制：从对话、作品、资料或数字痕迹中提炼**表达风格、决策框架与交互方式**，"不默认等同于对真实个体的完整还原"。这句话划清了整个项目的边界——蒸馏的是方法论视角，不是人格本身。

本文基于发文时点与 2026 年 10 月两个时点的仓库快照写成，梳理五类 Skills 的分布、女娲.skill 的真实工作流程、Agent Skills 开放标准，以及两条可以照着走的任务流。

## 蒸馏的是什么，不是什么

传统 AI 助手的知识来自通用语料，风格中立。当任务变成"理解某位老板的评审偏好"或"保留与某人的对话方式"时，通用能力帮不上忙——它缺的不是知识，是**这个具体人**的判断框架。人格蒸馏做的事，是把个体化的数据整理成可调用的 Skill：输入是聊天记录、文章、决策记录，输出是一份描述"这个人如何判断、如何表达"的说明书。

它明确不做的事同样重要。清单反复强调提取对象限于表达风格与决策框架，forge-skill 在 README 里写明"严禁用于骚扰、跟踪或侵犯他人隐私"，crush-skills 也声明"仅用于个人情感分析与回忆"。完整人格复制、冒充真实人物、未经授权使用他人数据，都不在允许范围内。

生态的源头需要交代一句：同事.skill 由 titanwings 开发，现已改名为 [Distilly](https://github.com/titanwings/distilly)（25,297★），定位扩展为"把任何人的思维方式蒸馏成可复用 Skills"。后来者几乎都受它启发——自己.skill 和 crush-skills 的仓库简介里都留着"Inspired by colleague-skill"的字样。

## 五类收录：从 45 到 71

清单按数据来源与隐私敏感度分成五类。两个时点的分布如下：

| 类别 | 2026-04-08 | 2026-10-05 | 核心场景 |
|------|-----------|-----------|----------|
| 自我蒸馏与元工具 | 6 | 15 | 自我画像、记忆整理 |
| 职场与学术关系 | 7 | 7 | 理解上司同事、学术传承 |
| 亲密关系与家庭记忆 | 6 | 7 | 情感整理、纪念陪伴 |
| 公众人物与方法论视角 | 22 | 36 | 方法论学习 |
| 精神性与专门化主题 | 4 | 6 | 传统术数、佛教文献 |
| **合计** | **45** | **71** | — |

五类不是平级关系。自我蒸馏是方法论源头——女娲.skill 的提炼流程被其他类别复用；公众人物蒸馏是同一套流程的规模化应用，数据来源换成公开资料，隐私顾虑最小，所以体量最大。半年间从 45 涨到 71 的新增条目，大部分也落在这个类别。

## 自我蒸馏与元工具

这一类共 6 个 Skills（发文时点），是整个项目方法论的源头。

**自己.skill**（[notdog1998/yourself-skill](https://github.com/notdog1998/yourself-skill)，3,426★）的口号是"与其蒸馏别人，不如蒸馏自己"。它把自我蒸馏做成了完整流水线：`prompts/` 目录里是 intake（数据接入）、self_analyzer（自我分析）、persona_builder（画像构建）等分步提示词；`tools/` 目录提供了微信、QQ、社交媒体记录和照片的解析脚本；蒸馏产出放在 `selves/` 目录下，仓库自带一份 `example_me` 样例，包含画像、SKILL.md 和元数据。想看最终产物长什么样，看这个样例最快。

**女娲.skill**（[alchaincyf/nuwa-skill](https://github.com/alchaincyf/nuwa-skill)，33,566★）是生态里体量最大的仓库，也是方法论上最认真的一家。README 里写的工作流程分四步：

1. **六路并行采集**——著作、播客/访谈、社交媒体、批评者视角、决策记录、人生时间线，六个 Agent 同时跑，各自存档；
2. **三重验证提炼**——一个观点要被收录为心智模型，必须跨 2 个以上领域出现过、能推断出对新问题的立场、且不是所有聪明人都会这么想；
3. **构建 Skill**——把 3–7 个心智模型、5–10 条决策启发式、表达 DNA、价值观与反模式、诚实边界写入 SKILL.md；
4. **质量验证**——拿 3 个此人公开回答过的问题测试，方向一致才通过；再用 1 个他没讨论过的问题测试，Skill 应当表现出适度不确定，而不是斩钉截铁。

完整方法论在仓库的 `references/extraction-framework.md` 里。`examples/` 目录放着乔布斯、Paul Graham、张一鸣、Karpathy、芒格、费曼等 13 个人物加 1 个主题的完整调研数据，每个示例都能看到信息如何从原始素材变成心智模型。第三步里的"诚实边界"是个关键设计：蒸馏产物被要求知道自己只是近似，遇到本人没处理过的问题要承认不确定——这是对"AI 冒充真人"风险最直接的工程化约束。

**Forge**（[YIKUAIBANZI/forge-skill](https://github.com/YIKUAIBANZI/forge-skill)）是 local-first 的人格引擎，把蒸馏拆成两个独立流程：forge-self 蒸馏自己，看清自己的说话方式、决策模式和盲区；forge-persona 从聊天记录与记忆中蒸馏他人，留住语气与互动方式。拆开的理由很实际——两类蒸馏的数据来源和隐私要求完全不同，混在一起容易把私人数据带进分享出去的产物。

**反蒸馏 Skill**（[leilei926524-tech/anti-distill](https://github.com/leilei926524-tech/anti-distill)，2,434★）是这一类里立场最特别的：它是写给被公司要求"把工作经验整理成 Skill"的员工的。运行后输出一份看起来完整专业的"净化版" Skill 用于交差，同时生成一份保留核心知识的私有备份。清单里对它的描述是"将可公开分发的技能内容与私有经验备份分离管理"——同一件事，仓库自己的说法要直白得多。它提醒了这件事的另一面：蒸馏技术既能保存个体经验，也可能被用来把人变成可替换的组件。

这一类还有从日常数字痕迹提炼画像的**数字人生.skill**（wildbyteai/digital-life），和基于聊天记录与相关资料整理多维数字人格画像的**永生.skill**（agenmod/immortal-skill）。

## 职场与学术关系

7 个 Skills，数据来源是工作材料与学术资料，隐私敏感度居中。

- **同事.skill**（titanwings）——生态源头，从团队资料整理前同事的工作上下文、习惯与沟通方式，现已改名 Distilly；
- **老板.skill**（[vogtsw/boss-skills](https://github.com/vogtsw/boss-skills)）——从工作材料提炼管理者的判断标准、评审风格与沟通预期，适合汇报前对齐预期；
- **HR.skill**（Schlaflied/hr-skill）——从拒信与招聘流程反向拆解 HR 的筛选逻辑，帮求职者重构求职叙事；
- **骂人求职.skill**（Schlaflied/roast-cold-email-skill）——从公司公开信息生成有理有据的批评性求职邮件，用精准观察替代空洞赞美；
- **师兄.skill**（zhanghaichao520/senpai-skill）——从课题组材料提炼资深成员的指导方式与救火风格；
- **导师.skill**（[ybq22/supervisor](https://github.com/ybq22/supervisor)）——把导师的指导风格整理成面向学生与教育工作者的助手，帮新学生快速适应课题组的沟通节奏；
- **大学老师.skill**（CommitHu502Craft/professor-skill）——从课程资料整理复习重点、题型偏好与评分线索。

这一类的共同前提是数据曾在你手里：同事留下的文档、导师给你的批注。清单要求使用前获得数据主体授权，这个要求在职场场景尤其不该省。

## 亲密关系与家庭记忆

6 个 Skills，隐私敏感度最高，几乎都强调本地运行。

**暗恋对象.skill**（[xiaoheizi8/crush-skills](https://github.com/xiaoheizi8/crush-skills)，362★）做得比想象中克制：除了从聊天记录、照片、朋友圈生成关系记忆与画像，它内置了三种模式——模拟模式练习和对方说话，军师模式分析该不该说、怎么说，照镜子模式则反过来"看看 ta 眼里的你是谁"。还有一条 reality 指令做现实检验，防止过度沉溺。README 的边界声明只有一句："仅用于个人情感分析与回忆，不用于骚扰、跟踪或侵犯他人隐私。"

其余五个：**恋爱训练营.skill**（TammyTan516）基于聊天记录模拟心动对象的沟通风格，在沙盒里练习表达与关系修复；**前任.skill**（therealXiaomanChu）从私人记录整理说话方式与共同记忆，用于回忆与关系梳理；**父母.skill**（xiaoheizi8）提炼父母的语气、习惯与家庭记忆；**MamaSkill**（jiangziyan-693）从亲人的聊天记录、信件与语音整理纪念型陪伴助手；**Reunion Skill**（yangdongchen66-boop）基于已故亲友的数字遗物构建可本地运行的纪念型助手。

这一类的价值主张其实是"保存"而非"替代"：MamaSkill 和 Reunion 处理的是正在消逝或已经消逝的声音。技术上的共同点是本地运行——数据最私密的类别，不该有任何上传动作。

## 公众人物与方法论视角

发文时 22 个、如今 36 个的最大类别，数据来源是访谈、著作、演讲等公开资料，没有授权问题，适合作为入门。

投资与决策方向有巴菲特思维操作系统（will2025btc/buffett-perspective，215★）、芒格.skill、塔勒布.skill、纳瓦尔.skill；创业与科技方向有 PG.skill、马斯克.skill、乔布斯.skill、张一鸣.skill、费曼.skill、Karpathy.skill、Ilya.skill；内容与传播方向有 MrBeast.skill、张雪峰.skill、户晨风.skill、童锦程.skill、内娱.skill；还有特朗普.skill、X 导师.skill，以及求是 Skill、毛选.skill、KarlMarx Skill 这一组思想方法类条目，和"峰哥亡命天涯"这样的互联网人物视角。

这一类还有个结构性特点：22 个条目里有 13 个出自 alchaincyf 一人之手，他就是女娲.skill 的作者；加上自我蒸馏类的女娲.skill 本体，这位作者贡献了清单近三分之一的条目。也就是说，女娲先作为工具批量蒸馏了十几位公众人物，这些产物再作为条目进入清单，`examples/` 里的示例与清单条目高度重合。清单里其他人物条目则来自不同作者，质量并不均匀，采用前最好逐个看看 SKILL.md 扎不扎实。

## 精神性与专门化主题

4 个 Skills（发文时点），面向传统文化与专业文献：**赛博算命 Skill**（jinchenma94/bazi-skill）基于出生信息与传统命理典籍做四柱排盘；**月老·姻缘测算 Skills**（Ming-H/yinyuan-skills）把合婚、求签、桃花运势整理成多模式术数技能；**Numerologist Skills**（FANzR-arch）用结构化知识库与脚本化约束整理奇门遁甲、紫微斗数；**Master-skill**（xr843）基于佛教经典文献整理汉传佛教的教学风格与讲解视角。10 月复查时这一类已扩到 6 个，新增了金刚经、堪舆子等条目。

这类 Skills 的共同做法是把典籍数字化为结构化知识库，再配规则引擎约束输出——传统术数知识恰恰是 LLM 最容易一本正经胡说的领域，脚本化约束算是对症的工程手段。

## Agent Skills 标准：跨工具运行的基础

这些 Skills 能在 Claude Code、Codex、Cursor、Gemini CLI 等不同工具里运行，靠的是 [Agent Skills](https://agentskills.io) 开放格式。这个标准由 Anthropic 发起，核心极简：一个 Skill 就是一个文件夹，必须包含一个 `SKILL.md`——YAML 头部写 `name` 和 `description` 两个必需字段，正文写执行指令；`scripts/`、`references/`、`assets/` 目录可选，用来放脚本、参考文档和模板资源。

以暗恋对象.skill 的 SKILL.md 头部为例：

```markdown
---
name: create-crush
description: Distill a crush into an AI Skill. Import chat history, photos, social media, generate Relationship Memory + Persona, with continuous evolution. | 把暗恋对象蒸馏成 AI Skill，导入聊天记录、照片、朋友圈，生成 Relationship Memory + Persona，支持持续进化。
argument-hint: "[crush-name-or-slug]"
version: 1.4.1
user-invocable: true
allowed-tools: Read, Write, Edit, Bash
---
```

运行时对 Skill 的加载是渐进式的，分三步：启动时只读每个 Skill 的名字和描述（发现）；任务匹配到描述时才读入完整指令（激活）；执行中按需运行脚本或加载引用文件（执行）。这样 agent 可以随身携带大量 Skills 而不占多少上下文。`description` 字段因此格外重要——它是 Skill 被"发现"的唯一线索，写得含糊，Skill 就永远不会被触发。

清单本身的收录流程也依托这套自动化：申请新增先提交 issue 表单，维护者审核加 `approved` 标签后，工作流自动生成 PR；修复现有条目可以直接提 PR。清单以 CC0 许可发布。

## 两条任务流

把上面的材料拼起来，可以走出两条完整路径。

**蒸馏一位公众人物**（以女娲为例）：安装只需在任意兼容 runtime 里执行 `npx skills add alchaincyf/nuwa-skill`，或直接对 agent 说"帮我安装这个 skill"加仓库地址。之后输入一个人名，女娲自动跑完六路采集、三重验证、构建与质量验证四步，产出一份 SKILL.md。想先看效果再安装，直接读 `examples/` 里的现成调研数据即可。

**蒸馏自己**（以自己.skill 为例）：先用手边的导出工具把微信或 QQ 聊天记录、社交动态导出为文件，仓库的 `tools/` 脚本负责解析成结构化数据；然后按 `prompts/` 里的流程依次跑数据接入、自我分析与画像构建，产出写入 `selves/` 你的专属目录。仓库自带的 `example_me` 可以作为产出格式的参照。

两条路径的关键决策点相同：**抽象的粒度**。粒度过细，Skill 变成原始聊天记录的复读机，换个话题就失效；过粗，得到的是"任何理性的人都会这么说"的通用建议，失去个体区分度。女娲的三重验证是针对这个问题的工程答案——每条心智模型都要在跨领域出现率和排他性上过关。检验成品有个朴素标准：让熟悉本人（或本人自己）读几段 Skill 生成的回答，能分辨出"像不像"，就算及格。

## 采用顺序与边界

按隐私风险从低到高排，建议的入手顺序是：

1. **公众人物方法论**——公开资料，无授权问题，适合先熟悉 Skill 的安装与使用；
2. **自我蒸馏**——数据是自己的，风险低，方法论在这类里最完整；
3. **精神性与专门化**——典籍文献，小众但无隐私负担；
4. **职场与学术关系**——材料涉及他人，用前获得授权；
5. **亲密关系与家庭记忆**——数据最私密，坚持本地运行，纪念类场景请尊重家庭成员的意愿。

无论哪一类，有三条线不要越过：不用蒸馏产物冒充真人对外交互；不在数据主体未授权的情况下蒸馏其风格；不把含他人私人数据的 Skill 文件分享出去。清单 README 的那句限定值得再引一遍——人格蒸馏"不默认等同于对真实个体的完整还原"，也不能替代真实的关系。

## 资料来源与时效说明

- 主仓库数据：GitHub API，2026-10-05 读数（4,675★/506 forks，CC0-1.0，创建于 2026-04-06）；发文时点状态取自 commit `33404e4426`（2026-04-08）的 README 快照；
- 条目计数：两个时点的 README 逐条清点（45 = 6+7+6+22+4；71 = 15+7+7+36+6）；
- 子仓库 star 数（女娲 33,566、Distilly 25,297、自己.skill 3,426、反蒸馏 2,434、暗恋对象 362 等）均为 2026-10-05 读数；
- 女娲工作流程、Forge 定位、反蒸馏用途、crush-skills 边界声明与 SKILL.md 头部，分别引自各仓库当日 README 与源文件；Agent Skills 格式说明引自 agentskills.io 官方文档。

子仓库大多为个人项目，活跃度与可运行性随时间变化明显，安装使用前请以各仓库当前状态为准。
