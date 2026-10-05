---
title: "openai/skills 谢幕解读：Agent Skills 官方样本库的遗产与迁移路径"
date: "2026-09-11T03:45:00+08:00"
lastmod: "2026-10-03T00:00:00+08:00"
slug: "openai-skills-deprecated-catalog-legacy-migration"
github_repo: "openai/skills"
source_key: "gh:openai/skills"
aliases:
  - "/posts/tech/openai-skills-deprecated-catalog-legacy-migration/"
description: "openai/skills 是 OpenAI 为 Codex 建立的官方技能目录，2026 年 6 月废弃，由 openai/plugins 接替。本文解读它留下的技能包契约、skill-installer 分发机制与新旧货架的迁移对照。"
draft: false
categories: ["技术笔记"]
tags: ["OpenAI", "Codex", "Agent Skills", "AI Agent", "开源项目"]
---

# openai/skills 谢幕解读：Agent Skills 官方样本库的遗产与迁移路径

openai/skills 已经停止演进，但它仍是 Agent Skills 这个开放格式最完整的官方实现样本：一个技能包长什么样、SKILL.md 怎么写才能被智能体可靠触发、安装器怎么发现和落盘技能——这些约定在它废弃后原样延续到了 openai/plugins 和 agentskills.io 标准里。把它的 39 个精选技能当作教材读一遍，比读任何二手转述都接近这套机制的本义。

仓库的现状（2026-10-03 读数）：27,854 星、1,895 fork，未加归档标记，main 分支最后一次提交停在 2026-06-24，此后没有实质演进。README 顶部挂着废弃横幅，把现成的技能与插件示例指向 [openai/plugins](https://github.com/openai/plugins)，把自定义技能的开发流程指向官方 [Build plugins](https://developers.openai.com/codex/plugins/build) 指南。

## 从创建到封笔的七个月

这个仓库的活跃期只有七个月，节奏却很能说明官方对技能生态的经营方式：

| 时间 | 事件 |
|---|---|
| 2025-11-25 | 仓库创建，首提交只是占位 |
| 2025-12-17 | 首个实质提交（#1）：README 初稿与 .gitignore |
| 2025-12-18~19 | skill-creator 等首批系统技能与 gh、linear 等首批精选技能入库 |
| 2026-01-27~31 | 精选技能批量上架：figma、jupyter、playwright、sentry 等 |
| 2026-02-02 | 安全三件套入库（threat-model、ownership-map、best-practices） |
| 2026-03-04 | openai/plugins 仓库创建，接替者入场 |
| 2026-04-27 | migrate-to-codex 上架：从 Claude Code 迁移技能与配置的官方工具 |
| 2026-05-21 | define-goal 上架，最后一个新增的精选技能 |
| 2026-06-22 | "Deprecate skills repository"（#496），正式废弃 |
| 2026-06-24 | skill-installer 安装后引导更新（#507），main 分支封笔 |

废弃提交之后 main 分支再无动静，个别 agent/ 前缀的自动化分支最后活动停在 7 月中旬。它死后留下的东西分两层：一层是货架上的技能本身，一层是技能得以运转的契约与分发机制。后一层才是真正值得读的。

## 货架结构：两排货架，两种身份

技能全部放在 `skills/` 目录下，分两排：

| 货架 | 数量 | 身份 | 安装方式 |
|---|---|---|---|
| `skills/.system/` | 5 | Codex 内置技能的镜像，随最新版 Codex 自动安装 | 无需安装 |
| `skills/.curated/` | 39 | 官方精选货架 | Codex 内用 `$skill-installer` 按名安装 |

`.system` 的五个是 skill-creator（创建技能）、skill-installer（安装技能）、plugin-creator、imagegen、openai-docs。提交历史里大量以 `[codex]` 或 "Mirror" 开头的条目说明它们的源在 Codex 产品侧，仓库里只是同步副本——所以仓库废弃封存的是货架，安装器本身活在 Codex 里，这也是 `skill-installer` 至少在纸面上仍可用的原因。

`.curated` 的 39 个按职能大致分几类：Figma 设计转码 8 个、Notion 知识管理 4 个、部署 4 个（Vercel / Netlify / Cloudflare / Render）、安全分析 3 个、GitHub 工作流 2 个（`gh-fix-ci`、`gh-address-comments`），其余是 Playwright 自动化、sentry 排障、语音转写、jupyter、`migrate-to-codex` 之类的单项工具。openai-docs 在两排货架上各有一份，系统版随 Codex 内置，精选版提交记录显示定期与系统版对齐。

还有第三排货架曾经存在过：`skills/.experimental/` 在 2026 年 2 月短暂开放，一个多月后开始清退，如今这个目录已从仓库里完全消失，README 却仍保留着从 `.experimental` 安装技能的示例命令。读废弃仓库要有这个心理准备——横幅、示例和目录实况三者对不上是常态，以目录为准。

## 遗产一：技能包的写作契约

以 `gh-fix-ci` 为例，一个精选技能的标准结构是：

```text
skills/.curated/gh-fix-ci/
├── LICENSE.txt      # 每个技能独立授权
├── SKILL.md         # 入口说明书
├── agents/openai.yaml
├── assets/          # 静态资源（logo 等）
└── scripts/
    └── inspect_pr_checks.py
```

整个仓库没有根级 LICENSE，授权下沉到 44 个技能目录各自的 LICENSE 文件（绝大多数叫 `LICENSE.txt`，个别 Figma 系技能用大写 `.TXT` 扩展名，写脚本扫描时注意大小写）。引用任何一段脚本前，先看它所属技能的许可。

SKILL.md 的 frontmatter 通常只有两个字段：`name` 和 `description`。系统技能多一个 `metadata.short-description` 用于列表展示。真正的设计功力在 description 的写法上——它不是摘要，是触发条件。`gh-fix-ci` 的 description 原文值得整段抄下来研究：

> Use when a user asks to debug or fix failing GitHub PR checks that run in GitHub Actions; ... draft a fix plan, and implement only after explicit approval. Treat external providers (for example Buildkite) as out of scope and report only the details URL.

一句话里装了四层信息：何时激活（用户要求调试 GitHub Actions 的 PR 检查失败）、用什么工具（`gh` 查看检查与日志）、行为约束（先拟计划、明确批准后才动手）、职责边界（Buildkite 等外部 CI 只报告 URL，不越界处理）。把边界和门控写进触发条件而非正文，智能体在读到正文的很早之前就知道不该做什么——这是这批官方样本里最值得抄的写法。

skill-creator 技能把这个契约背后的方法论讲得更直白。它的核心原则是"The context window is a public good"：技能的元数据与其他技能的说明、对话历史共用一个上下文窗口，每一段解释都要回答"这段配得上它的 token 成本吗"。默认假设是"模型已经够聪明"，只写模型不知道的部分——公司内部流程、私有 schema、脆弱操作的固定顺序。落到写作上，它给出一个自由度三级的选择框架：

- **高自由度**（文本指令）：多条路径都可行、需要看情况判断的任务；
- **中自由度**（伪代码或带参数的脚本）：有首选模式但允许变化的任务；
- **低自由度**（固定脚本、极少参数）：操作脆弱易错、一致性压倒一切的任务。

这套框架后来原样进入了 [agentskills.io](https://agentskills.io) 的最佳实践文档。标准的规范也很克制：一个技能就是一个文件夹，必须含 SKILL.md（metadata 至少 name 和 description），可选挂 scripts、references、assets——与这个仓库的实际形态完全一致。

## 遗产二：skill-installer 的分发机制

精选技能的安装统一走 Codex 内置的 `$skill-installer`：

```text
$skill-installer gh-address-comments
```

按名字安装，默认从 `skills/.curated` 解析。装到哪、怎么装，答案在 skill-installer 自己的 SKILL.md 和脚本里：技能落到 `$CODEX_HOME/skills/<skill-name>`（默认 `~/.codex/skills`），三个脚本各管一段——`list-skills.py` 列出可装清单（支持 `--format json`），`install-skill-from-github.py` 负责实际下载（`--repo <owner>/<repo> --path <技能路径>` 或直接给 GitHub 目录 URL），`github_utils.py` 处理底层请求。

几个实现细节能看出这套设计的务实：安装默认走直接下载，遇到鉴权或权限错误时回退到 git sparse checkout，只拉需要的子目录；目标目录已存在则中止而不是覆盖，避免静默改动用户已有的技能；`--ref` 默认 main，也支持私有仓库。脚本的 `--repo/--path` 参数并不限定 openai/skills 本身，指向任何 GitHub 仓库的技能目录都能装——这一点在仓库废弃后反而重要，后文迁移一节会用到。

安装后何时生效，仓库自己留了一个时间胶囊：README 至今写着"重启 Codex 生效"，而封笔的那次提交（#507）恰好把 SKILL.md 里的口径改成了"下一回合可用"。半天的时差里官方改了安装体验，README 没跟上——废弃仓库的文档冻结在 6 月 24 日，读的时候要知道自己站在哪个时点。

## 一个任务流案例：gh-fix-ci 怎么修一次 CI

把上面的契约和机制串起来，看一次真实的 CI 修复如何流过这套系统。

用户在 Codex 里说"帮我看看这个 PR 的检查为什么挂了"。技能匹配靠 description：这句话命中 `gh-fix-ci` 的触发条件，Codex 读入 SKILL.md，按 Workflow 的八步走：

1. **验证认证**：跑 `gh auth status`，未认证就让用户先 `gh auth login`（repo 和 workflow 权限通常都要）；
2. **解析 PR**：优先取当前分支的 PR（`gh pr view --json number,url`），用户给了 PR 号就直接用；
3. **检查失败项**：优先跑自带的 `inspect_pr_checks.py --repo "." --pr <编号>`——脚本处理了 `gh` 输出字段变动和日志回退；也可以手工 `gh pr checks --json` 逐项看，从 `detailsUrl` 提取 run id 后 `gh run view --log` 拉日志；
4. **划定边界**：`detailsUrl` 不是 GitHub Actions 的（比如 Buildkite），只标记为外部并报告 URL，不尝试处理；
5. **总结失败**：给出失败的检查名、run 链接和关键日志片段，缺日志要明说；
6. **做计划**：环境里有 create-plan 技能就调用它，没有就内联拟一份简明计划，请求用户批准；
7. **批准后实施**：按批准的计划改代码，总结 diff 与测试，询问是否开 PR；
8. **复查**：建议重跑相关测试和 `gh pr checks` 确认恢复。

这个案例里能看到技能形态的几个本质特征：没有常驻进程，每一步都是现成 CLI 命令的编排；脚本是给智能体的提效工具而非黑盒，手工回退路径写在同一份文档里；最危险的一步（改代码）被 description 里的审批门控拦住。对比同一场景下的 MCP（Model Context Protocol，模型上下文协议）服务器方案——常驻进程、协议握手、工具调用——技能包几乎是零成本的扩展方式，代价是它只适合"读文档、跑脚本"类的能力，做不了需要长连接或服务端状态的集成。这正是后来 plugins 时代用 bundle 把两者拼起来的原因。

## 迁移路径：三条去向与新旧货架对照

如果你的工作流还依赖这个仓库，按场景对号入座：

| 你的场景 | 去向 |
|---|---|
| 找现成技能/插件示例 | [openai/plugins](https://github.com/openai/plugins) |
| 给 Codex 写自定义技能或插件 | [Build plugins](https://developers.openai.com/codex/plugins/build) 指南 |
| 理解技能概念与标准 | [Using skills in Codex](https://developers.openai.com/codex/skills) 与 [agentskills.io](https://agentskills.io) |

openai/plugins 不是旧货架的平移，而是一次形态升级。它 2026-03-04 创建，现有 62 个插件（2026-10-03 读数 7,275 星），每个插件是一个 bundle：必需的 `.codex-plugin/plugin.json` manifest，可选挂 `skills/`、`.mcp.json`、`commands/`、`hooks.json`、`agents/` 等目录。以 figma 插件为例，plugin.json 里的字段包括版本（2.0.20）、作者（Figma 官方署名）、独立许可（LicenseRef-Figma-Developer-Terms）、`skills` 与 `apps` 指针和 interface 元信息——第三方厂商以自己的名义共建货架，这是旧仓库没有过的模式。分发也换成了 marketplace 清单：默认清单 `.agents/plugins/marketplace.json` 名为 "openai-curated"，每个条目带分类和安装策略，部分插件标注 `authentication: ON_INSTALL`——装插件时要现场完成第三方服务认证，技能时代"拷个文件夹"的分发模型到此结束。

新旧货架的对应关系，抽几个代表看清走向：

| 旧货架 | 新货架 | 关系 |
|---|---|---|
| figma 系 8 个技能 | figma 插件（内含 12 个技能） | 扩充重组，名称非一一对应 |
| notion 系 4 个技能 | notion 插件 | 延续，纳入官方亮点名单 |
| 安全三件套 | codex-security 插件（OpenAI 官方，带 mcpServers） | 职能延续，形态从文档技能变为 bundle |
| `gh-fix-ci`、pdf、screenshot、playwright 等 | 62 个插件中无同名条目 | 未见平移 |

最后一行需要展开说。通用工程技能没有跟着搬进新货架，有名字上的疑似的（github 插件未必涵盖 `gh-fix-ci` 的职能），也有彻底消失的。官方没有提供新旧对照表，本文也不做逐个推断——动手迁移前，以 [plugins 仓库](https://github.com/openai/plugins)的 `plugins/` 目录实际清单为准。如果你依赖的旧技能确实无处可去，两条退路都在：一是手动把技能目录拷贝到 `~/.codex/skills`，二是按 skill-installer 脚本的用法指定本仓库路径安装（`--repo openai/skills --path skills/.curated/<技能名>`），仓库未删除、raw 文件仍可访问，脚本本身也支持任意仓库。这是权宜之计——冻结的技能不会跟进 API 变化，只适合过渡期使用。

官方文档体系自身也在迁移：README 里 "Create custom skills in Codex" 的链接现在 308 重定向到 learn.chatgpt.com 的 build-skills 页面。技能、插件、文档三层都在动，引用任何一条链接前先验一次。

## 适用边界与维护指引

- **它是历史样本库**。新的扩展开发一律从 openai/plugins 和 Build plugins 指南起步，不要基于本仓库构建。
- **授权按技能目录逐个确认**。无仓库级 LICENSE，44 个技能目录各自的 LICENSE 文件才算数，Figma 系等第三方技能的许可条款各不相同。
- **语言构成别误读**。GitHub 语言榜上 Python 占最高（约 40 万字节），容易让人以为这是个代码仓库；实际上 42 个 Python 文件全部是技能自带的脚本——`migrate-to-codex` 一个技能就占 15 个，安装器只有 3 个。仓库本体没有任何基础设施代码，内容是 Markdown 和目录约定。
- **现状自查三件事**：README 废弃横幅是否仍在、main 分支最后提交日期、plugins 仓库的 marketplace 清单。本文读数锚定 2026-10-03，此后的变化以三处自查为准。

## 结尾判断

这个仓库今天的正确用法是一本绝版教材。三类人值得花时间翻：给智能体写技能的人，读 `.curated` 里几个 SKILL.md 的 description 写法和 skill-creator 的自由度框架，半小时能省掉很多无效摸索；在 MCP 和技能包之间做选型的人，`gh-fix-ci` 的八步工作流是"文档编排型扩展"的完整样本；做智能体扩展生态的人，从技能到插件 bundle 的形态升级过程——第三方署名共建、marketplace 策略、安装时认证——就是一份现成的演进路线图。

采用顺序很简单：装能力走 openai/plugins，写扩展走 Build plugins 指南，旧的 `.curated` 技能当范文读。从单一仓库里的两排货架，到 62 个第三方署名的插件 bundle，再到 agentskills.io 的开放规范——货架一直在换，而 SKILL.md 那两个 frontmatter 字段定义的契约贯穿始终。读懂它，换多少次货架都不慌。
