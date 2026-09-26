---
title: "pm-skills 解读：69 个技能与 42 条命令怎样占住 Claude Code 的上下文"
date: "2026-06-25T21:05:13+08:00"
lastmod: "2026-09-26T04:57:36+08:00"
slug: "phuryn-pm-skills-product-management-agent-skills-guide"
github_repo: "phuryn/pm-skills"
source_key: "gh:phuryn/pm-skills"
description: "phuryn/pm-skills 把产品经理方法论拆成 9 个插件里的 69 份技能与 42 条命令，一行运行时代码都没有。本文以 main 分支 8607e3b 为基准，跑通它的校验器与测试、把 9 个插件装进隔离配置的 Claude Code 2.1.278，量出常驻开销、口径漂移与跨工具的真实边界。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "Agent Skills", "产品经理", "工作流", "开源项目解读"]
keywords: ["pm-skills", "Claude Code 插件", "技能与命令", "上下文常驻成本", "文档一致性测试", "Codex 兼容", "Product Compass"]
---

pm-skills 把 Teresa Torres、Marty Cagan、Alberto Savoia 那一整套产品经理方法论拆成 69 份技能说明和 42 条命令。装载目标是 Claude Code、Cowork 和 Codex。它没有任何运行时代码：9 个插件在 Claude Code 的组件清单里报出的 Agents、Hooks、MCP servers、LSP servers 全部是 0。于是"值不值得装"不再取决于框架收得全不全，而取决于两件可以当场量出来的事：这些文本在什么时刻被读进上下文，以及每个会话为它固定付多少。

文中的结论都来自 2026-09-26 的一次走查：克隆仓库、跑它自带的校验器和测试套件、把 9 个插件全装进一个隔离配置目录的 Claude Code 2.1.278，再逐条回读到文件与行号。核对基准是 main 分支 `8607e3b077817f89bf4a9b623246219734ac3be0`（2026-09-14 提交）。仓库创建于 2026-03-01，MIT 许可，67 次提交出自 3 人之手，当天 26,596 颗星、2,830 个复刻、26 个未关闭议题加 16 个未合并请求。这类数字只在这里出现一次。

## 目录

1. [它交付的是文本不是工具](#它交付的是文本不是工具)
2. [名词与动词两种对象](#名词与动词两种对象)
3. [一份技能被读几次](#一份技能被读几次)
4. [命令层怎么把技能串起来](#命令层怎么把技能串起来)
5. [ship-check 从六步长成八步](#ship-check-从六步长成八步)
6. [68 还是 69 的口径漂移留在哪两处](#68-还是-69-的口径漂移留在哪两处)
7. [装一遍到底发生什么](#装一遍到底发生什么)
8. [谁在做以及靠什么活](#谁在做以及靠什么活)
9. [换到别的工具还剩什么](#换到别的工具还剩什么)
10. [出错时先看哪几处](#出错时先看哪几处)
11. [该不该装全套](#该不该装全套)
12. [下一步读哪几段代码](#下一步读哪几段代码)
13. [五个自测题](#五个自测题)
14. [参考](#参考)

## 它交付的是文本不是工具

装完之后最该先看的一眼，是权限面。`claude plugin details` 报出的组件类型里只有 skills 一项非零，其余四类全为 0。它不改写工具调用，不挂外部服务，也不在会话之外执行任何东西。整个市场就是一批按约定摆放的 Markdown 文件，加一份清单。

唯一一处对工具权限的显式约束在两个静态审计命令的 frontmatter 里：

```text
allowed-tools: Read, Grep, Glob, Task, Bash(git log:*), Bash(git diff:*), Bash(git show:*), Write(reports/**)
```

读、搜、派子任务、三类只读的 git 查询，写则只允许落在 `reports/` 下。被审计的代码不在可写范围内。42 条命令里只有这一对声明了 `allowed-tools`，其余命令把工具选择留给运行时的模型。

对读者这意味着：把它装进来，风险面基本就是"多了一段常驻上下文"和"模型被引导去读你的代码"，而不是"多了一个能干的进程"。

## 名词与动词两种对象

`CLAUDE.md` 用两条规则切开了整个结构：

```text
- **Skills = nouns/concepts.** Frameworks and analytical knowledge Claude auto-loads when the topic matches (`lean-canvas`, `pre-mortem`, `market-sizing`).
- **Commands = verbs.** User-triggered workflows that chain one or more skills (`/write-prd`, `/discover`, `/plan-launch`).
```

技能是名词，描述一份框架知识，靠主题匹配被自动加载；命令是动词，是一条用户触发的流程，把一个或多个技能串起来。落到目录上，每个插件只有三样东西：`.claude-plugin/plugin.json`、`skills/<名字>/SKILL.md`、`commands/<名字>.md`。

九个插件规模差别很大，常驻成本也不同。技能与命令取自目录计数，组件与常驻词元（token）两列是 Claude Code 2.1.278 的读数：

```text
插件                       技能  命令  组件  常驻词元  覆盖的活
pm-execution                 16    11    27   ~1,546   PRD、OKR、路线图、Sprint、复盘、干系人
pm-product-discovery         13     5    18   ~1,117   创意、假设、实验、访谈、指标面板
pm-product-strategy          12     5    17   ~1,006   愿景、三类画布、定价、宏观扫描
pm-market-research            7     3    10     ~578   画像、细分、旅程图、市场规模、竞品
pm-go-to-market               6     3     9     ~527   滩头市场、ICP、增长循环、战斗卡
pm-marketing-growth           5     2     7     ~428   营销创意、定位、命名、北极星指标
pm-toolkit                    4     5     9     ~403   简历、保密协议、隐私政策、校对
pm-ai-shipping                3     5     8     ~685   反向文档化、三类审计、上线包
pm-data-analytics             3     3     6     ~335   SQL、队列分析、A/B 结论
合计                         69    42   111   ~6,625
```

组件那列把命令也算进了技能，为什么两栏数字会重合，后文"装一遍到底发生什么"一节给答案。69 与 42 这两个数与仓库自带校验器的汇总行一致：

```text
  Plugins:   9
  Skills:    69
  Commands:  42
  Total:     111 components

  ✓ ALL CHECKS PASSED (0 warnings)
```

文本量也值得知道：69 份 `SKILL.md` 共 6,589 行、平均每份 95 行，最长的一份是 `code-review` 的 253 行；42 份命令共 4,472 行。一个方法论框架的实际编码量就是这几千行，没有隐藏的实现层。

## 一份技能被读几次

技能的加载是分层的，而分层直接决定花费。`CLAUDE.md` 里写得很直白：frontmatter 保持精简，因为它常驻；细节放正文，因为它在触发时才加载。

三层各自的代价能单独量出来。`claude plugin details` 会为每个组件给两个数——常驻（always-on）与触发时（on-invoke）：

```text
component                        always-on  on-invoke
brainstorm-ideas-existing              ~80       ~660
identify-assumptions-existing          ~80       ~440
opportunity-solution-tree              ~90       ~970
metrics-dashboard                      ~70      ~1.2k
interview-script                       ~90      ~1.1k
discover                               ~30      ~1.2k
```

常驻部分只有一句话的量：69 条技能描述长度在 179 到 579 字符之间，平均 260 字符。触发时那列才是正文被读进来的估算，从四百多到一千二百词元不等。

描述怎么写不是随意的。69 条 `description` 全部含 "Use when" 引导的触发语，示例见下：

```text
name: identify-assumptions-new
description: "Identify risky assumptions for a new product idea across 8 risk categories including Go-to-Market, Strategy, and Team. Use when evaluating startup risks, assessing a new product concept, or mapping assumptions for a new venture."
```

自动加载靠的就是这半句和当前话题的匹配度，所以技能的 `name` 必须与目录名一致——校验器逐条检查，69 条全对。

第三层"引用资料"只有一个人用。69 个技能目录里，只有 `pm-ai-shipping/skills/code-review/` 带 `references/`，三个文件 267 行：正确性缺陷分类 144 行、性能 55 行、安全 68 行。渐进式披露写进了规范，真正按它做的只有最新那一个技能。

## 命令层怎么把技能串起来

命令是用户敲的那一个动作，内部是几步技能调用加检查点。`/discover` 是最好的样本，131 行里排了 7 步：

```text
Step 1  判定是已有产品还是新产品，问清探索对象、已知信息、这次要支撑什么决策
Step 2  brainstorm-ideas-existing / -new     三视角出 10 条创意，让用户挑 3-5 条
Step 3  identify-assumptions-existing / -new 逐条摊开风险假设
Step 4  prioritize-assumptions               Impact × Risk 矩阵，挑出"信念之跳"
Step 5  brainstorm-experiments-existing / -new 为最高优先级假设各设计 1-2 个实验
Step 6  把以上整理成发现计划并存成文件
Step 7  提示下一步：写 PRD / 设计访谈脚本 / 铺指标 / 估工作量
```

七步里真正调用技能的是中间四步，README 把这条链概括成"一个命令串起四个技能"。文件末尾的备注里还有一句少见的坦率：这是一个 15 到 30 分钟的结构化流程，要提前告诉用户，且每个检查点都能改道、跳过或深挖。

假设的分类口径在两个技能之间是分开的，不是同一套：

```text
identify-assumptions-existing   四类：Value / Usability / Viability / Feasibility
identify-assumptions-new        八类：以上四类 + Ethics / Go-to-Market /
                                      Strategy & Objectives / Team
```

新产品那一份的开头还写了一句它自己的前提：好的团队会假定自己至少四分之三的想法不会如所料地成。

命令之间的衔接有一条硬规则：不许跨插件硬引用。

```text
- **No cross-plugin references.** Commands suggest follow-ups in natural language only ("Want me to design growth loops?"). Never hard-reference a command from another plugin — plugins install independently, so a hard reference can break.
```

原因是插件各自独立安装，写死一个别家插件的命令名，装了一半的人会撞空。所以 42 条命令里有 36 条在结尾留下自然语言的下一步提示（在命令正文里不区分大小写地匹配 want me to、next step、offer to 三种字样），而不是生成一条可点的跨插件调用。另一个细节：真正使用 `$ARGUMENTS` 占位符的命令只有 4 条，全在 pm-ai-shipping 里——多数命令靠"没给参数就问"来起手。

## ship-check 从六步长成八步

如果只读最新一版，会以为这套东西设计得很完整。拿标签差分看，它其实一直在长。

```bash
git show v2.1.0:pm-ai-shipping/commands/ship-check.md | grep -c '^### Step'
git show HEAD:pm-ai-shipping/commands/ship-check.md   | grep -c '^### Step'
```

两条命令分别给出 5 和 7——按小节标题数，v2.1.0 是六步（第 3、4 步合成一个"并行审计"标题），main 是八步。产出清单同样从 7 栏涨到 10 栏，新增的三栏是 Correctness Summary、Independent Review、Audit Provenance。

新增的两步各有来历。第三步是正确性复查，让 `code-review` 技能只跑 correctness 维度，找"编译通过、测试通过、两处单看都合理但互相矛盾"的缺陷。第六步是独立未引导复查：把目标交给**另一个模型的干净会话**，并立下三条规矩。其一，不能是写过这段代码的那个会话；其二，不给它检查清单，也不给它前序结论；其三，审查范围机械算出来，用 `git log --oneline <上一个标签>..HEAD` 和 `git status`，不用散文描述。最后一条理由写得很实在：未引导的审阅者没有反证纪律，会自信地报出代码早已挡住的"发现"，所以入包前必须逐条回代码手工验证。

这一步带来的 `code-review` 技能本身还没进任何版本——它在 `CHANGELOG.md` 的 `## Unreleased` 段里。查一下标签就知道：

```text
v2.0.0  skills=68  code-review 不存在
v2.1.0  skills=68  code-review 不存在
main    skills=69  code-review 存在
```

## 68 还是 69 的口径漂移留在哪两处

这是全文最该抄下来的一条：同一份仓库里同时存在 68 和 69 两个说法，而它们不是随手写的。

被测试锁住的有四处，全在 `tests/test_consistency.py` 的 126 到 205 行，比对的都是这种形状的计数句：

```text
README.md:11                    "69 PM skills and 42 chained workflows across 9 plugins"
.claude-plugin/marketplace.json "69 domain-specific skills and 42 chained workflows …"
README.md:143                   "(13 skills, 5 commands)"        ← 折叠块标题行
pm-ai-shipping/README.md:15     "## Skills (3)"
```

前两处锁总量，后两处锁各插件自己的数，比对基准都是目录计数。四处都跟得上磁盘，所以 15 个用例全绿。

锁外的两处就留下了缝：

```text
CLAUDE.md:7      → "9 independent plugins (68 skills, 42 commands)"
README.md:445    → "**Skills (2):**"     # 同一块标题行写的是 (3 skills, 5 commands)
```

`CLAUDE.md` 的维护流程要求改技能后同步三处计数，没把自身列进去；README 折叠块里那行加粗的 `**Skills (N):**` 也没有断言覆盖它。于是前者停在 68，后者停在 2，而磁盘上是 3。

对读者来说，结论是引用这个项目前先定口径：装上手的 tag v2.1.0 是 68 个技能，今天克隆 main 拿到的是 69 个；而 GitHub 简介那句"100+ agentic skills, commands, and plugins"把 111 个组件合并计数，也谈不上错，只是另一种口径。

## 装一遍到底发生什么

安装是真跑的，配置目录隔离在临时路径，没动日常设置。全过程与关键输出：

```bash
export CLAUDE_CONFIG_DIR=/tmp/r20/ccfg
claude plugin marketplace add phuryn/pm-skills
claude plugin install pm-execution@pm-skills
claude plugin details pm-execution@pm-skills
```

```text
Adding marketplace…SSH not configured, cloning via HTTPS: https://github.com/phuryn/pm-skills.git
Refreshing marketplace cache (timeout: 120s)…
Cloning repository (timeout: 120s): https://github.com/phuryn/pm-skills.git
Clone complete, validating marketplace…
✔ Successfully added marketplace: pm-skills (declared in user settings)

Installing plugin "pm-execution@pm-skills"...✔ Successfully installed plugin:
  pm-execution@pm-skills (scope: user)
```

三个读数值得记下来。

第一，组件清单把命令算进了技能。pm-product-discovery 报出 `Skills (18)`，18 个名字排成一列（原文是一行，这里按宽度折行），5 条命令与 13 个技能混在一起：

```text
analyze-feature-requests, brainstorm, brainstorm-experiments-existing,
brainstorm-experiments-new, brainstorm-ideas-existing, brainstorm-ideas-new,
discover, identify-assumptions-existing, identify-assumptions-new, interview,
interview-script, metrics-dashboard, opportunity-solution-tree,
prioritize-assumptions, prioritize-features, setup-metrics,
summarize-interview, triage-requests
```

18 正好是 13 + 5。命令行侧也不分这两类，`claude --help` 里那个关闭斜杠命令的开关，说明文字写的是 Disable all skills。仓库自己的"名词/动词"分层，到了运行时归成一套注册表。

第二，装到的内容与版本标签不是一回事。安装记录里 `version` 是 2.1.0，落盘路径也叫 `.../pm-execution/2.1.0`，但同一份记录写着 `gitCommitSha: 8607e3b07781…`，即 main 的最新提交。市场缓存是一份 main 的克隆，主干最后一条提交在 2026-09-14，`code-review` 技能就在里面。版本号取清单，内容取主干。

第三，常驻开销是可累加的。9 个插件全开时，逐插件读数的合计约 6,625 词元——每个会话开头固定这一段，和你问什么无关。单插件从 pm-data-analytics 的 ~335 到 pm-execution 的 ~1,546。这是这个项目最实在的一笔成本，README 里没有提，但一条命令就能查。

它自带的守门也跑了。507 行的 `validate_plugins.py` 逐插件判定清单字段、技能与命令的 frontmatter、命令引用的技能是否存在，9 个插件全 PASS、0 warning。`tests/` 两个文件共 288 行，15 个用例全通过。CI 在每次 PR 和每次推 main 时跑这两件，Python 矩阵是 3.11 与 3.13。发布走另一条链：往 main 推一个新增的 `## vX.Y.Z` 标题，工作流先校验版本同步和测试，再打标签、发 Release，正文取 CHANGELOG 对应段。所以 `CHANGELOG.md` 是发布的真源，标签只是它的投影。

## 谁在做以及靠什么活

仓库基本是一个人做的。67 次提交，GitHub 的贡献者统计里 64 次记在 `phuryn` 名下，另外两位（`claude` 与 `fahrim`）各 1 次。署名是 Paweł Huryn，The Product Compass 通讯的作者，主页指向 productcompass.pm。

它的商业接缝在技能正文最后一节。README 末尾列出的方法论来源是 12 项、14 部作品；技能正文里 56 个带 `### Further Reading`，共 155 条链接，域名全部是 productcompass.pm，其中 14 条指向 `/p/cpdm`，即那套视频课。`CLAUDE.md` 对这件事的口径规定得比多数开源项目细：语气必须中立，不许促销语、不许行动号召、不许"订阅"，只留标题和链接；标题含 Masterclass 或 Course 的要标上 `(video course)`；模型按会话相关性决定要不要抛出这些链接，不是每次回答都推。

于是"12 项来源、14 部作品的方法论"这层叙事和"一份内容生意的入口"这层结构是同一份文件里的两件事，MIT 许可覆盖的是前者。技能正文本身没夹带推销，转化全在末尾那三五条链接上——读的时候知道这一点就够了，不必因此否定内容的组织质量。

## 换到别的工具还剩什么

Codex 与 Claude Code 共用同一份市场清单，官方口径是原生安装、不需要转换或复制文件：

```bash
codex plugin marketplace add phuryn/pm-skills
codex plugin add pm-execution@pm-skills
```

差别只有一处，但很关键：斜杠命令装了也不作为命令运行，因为 Codex 插件不暴露 commands。官方给的替代是直接用自然语言把步骤讲出来，README 里那句示例原文译过来是："对某想法跑一遍产品发现：先出创意，再摊假设，再挑最危险的，最后设计实验，每步之间停一下。" 更进一步可以要求它读插件里的命令文件，把常用几条转写成 Codex 原生技能；README 同时注明这是尽力而为的模型转写，部分 Claude 专有语法迁不过去。

其余工具只取技能：

```text
Gemini CLI   复制技能目录到 .gemini/skills/
OpenCode     复制技能目录到 .opencode/skills/
Cursor       复制技能目录到 .cursor/skills/
Kiro         复制技能目录到 .kiro/skills/
```

README 给了批量搬运的一段：

```bash
for plugin in pm-*/; do
  mkdir -p .opencode/skills/
  cp -r "$plugin/skills/"* .opencode/skills/ 2>/dev/null
done
```

这段循环会把 9 个插件的技能全铺到一个目录里，42 条命令一条不带——技能是跨工具的那一层，工作流编排不是。需要说明的是，本机没有 Codex，上面这一节取的是 `README.md` 与 `CLAUDE.md` 的记述，我没跑过。

## 出错时先看哪几处

下面按现象排查，最常见的四类占了绝大多数。

**敲 `/discover` 没有这条命令。** 先看插件是否真装上（`claude plugin list` 会列出插件名、版本、作用域和 enabled 状态）。装了还没有，就是你走的是复制技能目录那条路——命令不在技能目录里。Codex 侧则是设计如此，改用自然语言描述流程。

**技能没有被自动用上。** 自动加载只看 `description`，触发线索全在 "Use when" 那半句里，你的说法离它远就不命中。强制加载两种写法：`/pm-execution:prioritization-frameworks` 或直接 `/prioritization-frameworks`，前者带插件前缀更稳。

**会话开头比预想的胖。** 用 `claude plugin details <插件>@pm-skills` 看每组件的 always-on，按合计挑一个不用的插件关掉。装全套是 ~6,625 词元的固定支出，只为一两条命令的话不必。

**引用它的文章数字对不上。** 先分清是 tag 还是 main，以及组件口径。见前文三组数：68 / 69 / 111。

还有两处容易误判。审计命令拒绝改代码不是坏了，`allowed-tools` 只给了读和写 `reports/`。Windows 上 Cowork 起不来虚拟机的告警段落 README 仍在。它引的那条上游议题是 anthropics/claude-code 第 27010 号，2026-02-19 开、13 条评论，到 2026-09-26 已是 closed 状态。怀疑它是活故障之前，先看议题自己的状态。README 给的补救是一个每分钟检查一次 `CoworkVMService` 的 Windows 计划任务。

## 该不该装全套

先给一个便宜的验证顺序，再谈要不要铺开。

第一步只装一个插件、跑一条命令。做发现就 `pm-product-discovery` 配 `/discover`，写了 AI 生成的代码就 `pm-ai-shipping` 配 `/ship-check`。目标是看它给的中间检查点你有没有用上——这类流程的价值一半在框架，一半在"允许你中途改道"。

第二步按常驻开销决定装几个。pm-execution 一条就吃掉 ~1,546 词元常驻，但它 11 条命令覆盖 PRD、OKR、Sprint、复盘、干系人这几件最高频的事，摊薄下来最划算；pm-data-analytics 只有 ~335，不占地方；pm-toolkit 的 5 条命令里有两条落在同一份 221 行的简历复核技能上，技能层的复用比看起来紧。装到三四个插件以后再回头看 always-on 合计值不值得。

不适用的人也说清楚。只用 Notion AI 或网页端 ChatGPT 的团队没有挂载点；已经有稳定的内部模板与评审流程的人，套一层引导式提问多半是负收益；把 PM 方法论当素材自己写提示词的，直接读它的几个 `SKILL.md` 比装全套快——文本全在仓库里，MIT。

三个配套仓库各管一段，别混：pm-brain 把 PM 的上下文存成放在本地文件夹里的纯文本笔记，供模型读与写（881 星）；claude-usage 是本地跑的 Claude Code 词元用量与花费面板（2,237 星）；burnstop 是预算保险丝，按词元或金额给单次会话封顶并对目标自动挂 50 美元上限（10 星，最后一次提交停在 2026-06-22）。三者同为 MIT，与 pm-skills 的关系用作者自己的话说：技能是"做一次工作怎么做"，大脑是"你做过很多次之后知道什么"。

星数、议题数、词元数这些数都会变；上面每个数字都标了 2026-09-26 这个取数日，复算命令照抄即可。

## 下一步读哪几段代码

顺序上先读守卫，再读内容，判断会更快：

```text
tests/test_consistency.py:126-205   四道数字断言，看哪些位置被锁、哪些没被锁
validate_plugins.py:31-45           必需字段与 README 期望小节，全部约束的源头
CLAUDE.md:49-60                     名词/动词、不跨插件硬引用、技能名等于目录名
CLAUDE.md:73-79                     版本同步与 CHANGELOG 作为发布真源
pm-product-discovery/commands/discover.md   131 行，一条链式命令的完整写法
pm-ai-shipping/skills/code-review/references/correctness-taxonomy.md
                                    144 行，从真实修复历史里长出来的缺陷分类
```

## 五个自测题

1. 同一份 pm-skills 仓库里为什么能同时找到 68、69、111 三个数字？各自对应什么口径？
2. 想让一个插件不进常驻上下文，最短的命令是什么？它报的是哪两个成本列？
3. `/discover` 七步里哪几步调用了技能？为什么它不给跨插件的命令写硬引用？
4. `identify-assumptions-existing` 与 `-new` 的假设分类为什么不是同一套？多出来的四类是什么？
5. 今天克隆 main 装出来的插件清单里 `version` 写 2.1.0，但内容里有一个未发布的技能。叫什么名字？从哪条命令能看出来？

## 参考

- 仓库与清单：[phuryn/pm-skills](https://github.com/phuryn/pm-skills)（`README.md`、`CLAUDE.md`、`CONTRIBUTING.md`、`CHANGELOG.md`、`.claude-plugin/marketplace.json`、9 份 `plugin.json`）
- 本机执行记录：`python3 validate_plugins.py`、`python3 -m unittest discover -s tests`、`git ls-tree -r v2.0.0/v2.1.0/HEAD` 计数、`claude plugin marketplace add` 与 `claude plugin details`（Claude Code 2.1.278，2026-09-26）
- 配套项目：[phuryn/pm-brain](https://github.com/phuryn/pm-brain)、[phuryn/claude-usage](https://github.com/phuryn/claude-usage)、[phuryn/burnstop](https://github.com/phuryn/burnstop)
- 上游议题：anthropics/claude-code 第 27010 号（Windows Cowork 虚拟机服务未运行，2026-09-26 为 closed）
- 方法论来源（README「About」列出的 12 项）：Teresa Torres《Continuous Discovery Habits》、Marty Cagan《INSPIRED》《TRANSFORMED》、Alberto Savoia《The Right It》、Dan Olsen《The Lean Product Playbook》、Roger L. Martin《Playing to Win》、Ash Maurya《Running Lean》、Strategyzer《Business Model Generation》《Value Proposition Design》、Christina Wodtke《Radical Focus》、Anthony W. Ulwick《Jobs to Be Done》、Alistair Croll 与 Benjamin Yoskovitz《Lean Analytics》、Sean Ellis《Hacking Growth》、Maja Voje《Go-To-Market Strategist》
