---
title: "SEO Machine：把一套 SEO 内容工作室装进 Claude Code 的开源工作区"
slug: "seomachine-seo-ai-agent-guide"
date: "2026-04-08T16:35:00+08:00"
lastmod: 2026-10-03
categories: ["技术笔记"]
tags: ["Claude Code", "SEO", "Python", "内容营销", "开源"]
description: "7,400+ star 的开源 Claude Code 工作区 SEO Machine 解读：24 个斜杠命令、11 个专项 agent、24 个 Python 分析模块和 GA4/GSC/DataForSEO 三路数据，从选题研究、长文写作、去 AI 味到 WordPress 发布的完整内容流水线，以及采用前要想清楚的边界。"
draft: false
github_repo: "TheCraigHewitt/seomachine"
source_key: "gh:TheCraigHewitt/seomachine"
---

## 一句话说清它是什么

SEO Machine 不是一款可以 `npm install` 的 CLI 工具，也不是一个独立运行的 Agent 框架。它是一套专门为 Claude Code 准备的工作区（workspace）：仓库里放好了 24 个斜杠命令、11 个专项 agent、26 个营销技能和 24 个 Python 分析模块，你在这个目录里打开 Claude Code，它就变成一台按流程运转的 SEO 内容机器——研究关键词、写两三千词的长文、给内容打分、清除 AI 痕迹、最后通过 WordPress REST API 发布。

作者 Craig Hewitt 是播客托管公司 Castos 的创始人，这套系统原本是 Castos 内部的内容生产工具，2025 年 10 月底开源（仓库首个提交 2025-10-29），到 2026-10-03 已有 7,470 星、982 个 fork。整个仓库只有 27 个提交，主线非常清晰：首发时只有 5 个命令、4 个 agent，2026 年 2 月 2 日一天并入 10 个提交，补齐了落地页系统、CRO agent、26 个营销技能和 WordPress 发布管道，3 月加了主题聚类和内容日历命令，8 月补上 Docker 支持。它不是那种日更的大型项目，更像一个人把自家用了很久的内容流程整理出来分享。

## 先看地图：三层结构

| 层 | 位置 | 数量 | 干什么 |
|------|------|------|------|
| 命令层 | `.claude/commands/` | 24 个 | 编排工作流，每个命令是一份 Markdown 指令 |
| Agent 层 | `.claude/agents/` | 11 个 | 专项分析角色，被命令调用 |
| 分析层 | `data_sources/modules/` | 24 个 Python 模块 | 真正算数的代码：评分、聚类、可读性 |
| 技能库 | `.claude/skills/` | 26 项 | 文案、CRO、定价、邮件序列等营销方法 |
| 上下文 | `context/` | 11 个文件 | 你的品牌声音、关键词、内链地图 |

分层的逻辑值得说一句：命令负责"做什么、按什么顺序"，agent 负责"从什么专家视角看"，Python 模块负责"客观指标怎么算"。Markdown 命令里可以用 `@context/brand-voice.md` 这样的引用把配置文件喂给模型，Python 模块则由命令直接以脚本方式调用。AI 的部分和确定性计算的部分分得很开——关键词密度、Flesch 阅读分这类可以用代码算的绝不交给模型感觉。

这个仓库所有 622 KB 的 Python 代码承担了全部实际计算，仓库里没有一行 TypeScript——从语言构成看它约 99% 是 Python，外加一个 WordPress 的 PHP 插件和一个 Dockerfile。

## 装起来要几分钟

前置条件只有两样：装好 Claude Code，有 Anthropic API 账号。仓库克隆下来之后：

```bash
git clone https://github.com/TheCraigHewitt/seomachine.git
cd seomachine
pip install -r data_sources/requirements.txt
claude-code .
```

依赖清单里是 pandas、numpy、textstat、nltk、scikit-learn、beautifulsoup4 这类常规组合，全部服务于分析模块。2026 年 8 月的更新加了 Docker 路径：`docker-compose build` 之后 `docker-compose run seomachine bash`，context、drafts、published 这些内容目录都以卷挂载留在宿主机，容器里跑的其实是同一套东西。

Python 依赖不装也能用基本命令，但分析模块和后面说的数据集成都需要它。数据集成的凭据是三套独立的：GA4 要在 Google Cloud Console 建服务账号、下载 JSON 密钥放到 `data_sources/config/`，并把服务账号邮箱加进 GA4 属性；Search Console 用同一个服务账号；DataForSEO 是付费的第三方 SEO 数据服务，登录名和密码写进 `.env`。没有这三样，写、改、优化的本地闭环照常运转，缺的是两块：按真实流量排内容优先级，以及 SERP 竞品数据。

注意仓库从未发布过任何版本号或 release，所有改动都直接落在 main 分支上——使用时记下你克隆的提交号，升级前先看一遍 27 个提交的 diff，是这个项目的使用纪律。

## 主流水线：从选题到发布

日常内容生产走这条线：

```text
/research 主题        →  研究简报，存入 research/
/write 主题           →  2000-3000+ 词长文，存入 drafts/
   （写作完成后自动触发 4 个 agent 分析）
/optimize 文件        →  发布前终审，输出 0-100 分 SEO 评分报告
/publish-draft 文件   →  经 WordPress REST API 发布，带 Yoast 元数据
```

`/write` 的命令定义里有几处设计颇能看出作者的实战经验。第一是"直接回答前置"：对 best/how 类搜索意图，要求文章头一两句就给出直接答案，理由写得很直白——ChatGPT、Perplexity、Gemini 抓取的是页面顶部内容，答案藏在故事后面就进不了 AI 引用。第二是写作前强制回读五个上下文文件（品牌声音、写作范例、风格指南、SEO 规范、目标关键词），文章的"像不像你的品牌"完全取决于这几个文件填得是否认真。

写作完成后自动执行的质量循环是整套系统里最诚实的部分：先跑 `content_scorer.py` 给草稿打分，五个维度加权——

| 维度 | 权重 | 及格线含义 |
|------|------|------|
| 人味/声音 | 30% | 无 AI 套话，使用口语缩写 |
| 具体性 | 25% | 有具体例子、数字、名字 |
| 结构均衡 | 20% | 40-70% 是成段散文，不能全是列表 |
| SEO 合规 | 15% | 关键词、元信息、标题层级 |
| 可读性 | 10% | Flesch 60-70，8-10 年级水平 |

复合分低于 70 就按评分器给出的优先修复项自动改写。一个用来批量生产 AI 内容的系统，把"人味"设为权重最高的单项，这件事本身就是对当前搜索生态的判断。

配套的 `/scrub` 命令专门做最后一道清洁：删除 AI 模型可能嵌入的零宽字符水印（U+200B、U+FEFF、U+2060 等 Unicode Cf 类格式字符），再把滥用的长破折号按上下文替换——引语署名处换逗号、连接独立分句换分号、强断句换句号。这套规则写进了命令定义，底层实现在 `content_scrubber.py`，2025 年 10 月底（开源第三天）就有了雏形，4 月 10 日还专门修过一轮 Unicode 字符覆盖和空白处理。

发布一端，`/publish-draft` 走 WordPress REST API，配合仓库自带的 PHP 代码把 Yoast SEO 的三个关键字段（焦点关键词、SEO 标题、元描述）一并写入。官方给两种安装方式二选一：作为 MU-plugin 放进 `wp-content/mu-plugins/`（推荐，主题更新不丢），或把一小段代码贴进主题的 functions.php。WordPress 凭据用应用密码，写进 `.env`。

## 另外半边：用真实数据决定写什么

研究和写作解决"怎么写"，这个仓库另一半价值在"该写什么"。`/performance-review` 和 `/priorities` 把三路数据合到一起：GA4 的流量与转化、Search Console 的排名与点击率、DataForSEO 的竞品排名，由 `data_aggregator.py` 聚合成统一视图，再经 `opportunity_scorer.py` 按 8 个因子给每篇候选内容打机会分。快速赢面（quick wins）的定义很具体：排在 11-20 位、离首页一步之遥的页面，改动收益最高。

2026 年 8 月的一组提交专门处理了接数据的现实摩擦：GA4 和 Search Console 会拒绝服务账号邮箱，README 里补了 workaround；竞品差距脚本里的 ZeroDivisionError 也在同一批修掉。这类补丁本身就说明数据集成路径是被真实使用过的——纯展示项目不会长出这种 fix。

## 改旧文与扩展命令

对已有内容，流水线是 `/analyze-existing` 先体检（输出 0-100 的内容健康分、快赢清单、改写优先级），再 `/rewrite` 按体检结论重写——更新过时的数据和例子、补竞品有而你没有的章节，产出到 `rewrites/`，附带变更摘要和前后对比。

围绕主线还有三组扩展。研究系六个：SERP 分析、内容差距、趋势机会、表现优先级、主题簇研究，以及 4 月新增的 AI 引用审计——生成 100 多个用户可能会问 AI 的提示词，聚类后抽 10-15 个实际去问 ChatGPT、Perplexity 这类引擎，看哪些来源被引用、你在不在场，再给出补位的内容清单。落地页系五个：写、审、调研、竞品深析、发布，背后是 CTA、信任信号、首屏有效性等六个 CRO 分析模块。剩下三个管规划：`/cluster` 出主题簇的支柱文+支撑文+内链地图，`/content-calendar` 排月度日历，`/repurpose` 把一篇长文改写成 LinkedIn、Medium、Reddit、Quora 的分发版本。

26 个营销技能（copywriting、定价策略、邮件序列、A/B 测试设置等）则以独立技能目录的形式挂在 `.claude/skills/` 下，供 Claude Code 按需调用。

## 值得学的不只是工具

抛开"是否好用"，这个仓库把"AI 内容如何过编辑关"拆成了可检查的机制：写前回读品牌上下文、写后跑五维评分、不过线自动重写、发布前 scrub 清痕迹、发布后用搜索表现反推下一轮选题。每一环都有对应的文件和代码，拿任何技术栈都可以借鉴这套结构。

上下文文件系统是它的灵魂所在。`context/` 下 11 个文件里，`brand-voice.md`（声音支柱、语气规范、术语偏好）和 `writing-examples.md`（3-5 篇你最好的旧文全文）决定生成质量的上限，`internal-links-map.md` 和 `target-keywords.md` 决定 SEO 动作的准确性。仓库提供了完整实例：`examples/castos/` 里是 Castos 真实使用的四个配置文件，包括 5 篇全文范例，官方建议新用户照抄结构替换内容。QUICK-START 给的路径是 10 分钟：2 分钟装依赖，5 分钟填三个关键上下文文件，3 分钟跑第一篇。

## 采用之前

适合的场景：已经在用 Claude Code（有订阅或 API 额度）、内容站跑 WordPress、写英文长文、愿意花半天填上下文文件。它对 SEO 团队的意义是把"研究-写作-优化-发布"的手工协作变成单人流水线。

不适合或需要改造的场景也要说清楚。整套体系按英文 SEO 标准内建：Flesch 阅读分、8-10 年级水平、元标题 50-60 字符、主关键词密度 1-2%——中文站点这些指标要么失义要么要重写评分逻辑；不想用 WordPress 的话发布环节要自己接；DataForSEO 是付费服务，性能分析模块的持续使用有真金成本。

风险项同样明确：截至 2026-10-03，仓库最后一次提交停在 2026-08-05，近两个月没有动静；没有版本号和 release，坏了只能自己 pin 提交；27 个提交里作者本人占了 18 个，是典型的单维护者项目。另外它的文档有明显的分层滞后：NEXT-STEPS.md 还停留在首版的"5 命令 4 agent"，README 的命令参考列了 19 个、目录树漏了 4 个实际存在的命令，官网首页写"7 个 agent"（实际 11 个），只有 CLAUDE.md 与目录实况一致——查这个项目的功能，以 CLAUDE.md 和 `.claude/` 目录为准，README 做参考。

还有一个小提醒：README 的 License 一节至今留着 "[Add your license information]" 的占位符，但仓库根目录的 LICENSE 文件是标准 MIT（版权归 Castos 和 SEO Machine Contributors），GitHub 也按 MIT 识别，商用无碍。

同类商业工具里，Semrush、Ahrefs 是数据平台，Surfer 一类是内容优化 SaaS；SEO Machine 不生产数据（它自己也要接 DataForSEO），它把数据、品牌上下文和模型能力编排成一条可以自己持有和修改的生产线。对于内容是其获客主线的团队，这套结构比工具本身更值得带走。
