---
title: "Skill Prompt Generator：三层各自声明、互不校验，漂移就成了结论"
date: 2026-05-10T00:00:00+08:00
lastmod: "2026-09-26T03:20:00+08:00"
draft: false
slug: "skill-prompt-generator-skills-architecture-2026"
github_repo: "huangserva/skill-prompt-generator"
source_key: "gh:huangserva/skill-prompt-generator"
aliases: ["/posts/skill-prompt-generator-12-skills-architecture-2026/", "/posts/video/skill-prompt-generator-skills-architecture-reverse-write-2026/"]
author: text-matrix
categories: ["技术笔记"]
tags: ["Skills 系统", "Claude Code", "Codex CLI", "SQLite", "提示词工程", "AI Agent", "YAML"]
description: "huangserva/skill-prompt-generator 用 12 个技能目录、1,246 个元素的 SQLite 库和八个 Python 引擎模块拼出一套提示词生成系统。本文把说明文档里的每个数字回到库与代码上重算一遍：跨域可用的 995 个元素实际可达 286 个，默认拼接模式会丢掉 53.8% 的元素已经写好的模板，而 YAML 推导出的眼型在查询层注定取空。"
keywords: ["提示词生成", "技能架构", "元素库", "跨域查询", "声明式规则", "数据漂移", "SQLite 外键"]
---

判断先给在这里：这个项目的价值和问题是同一件事。它把提示词生成分成三层——技能目录负责给智能体下指令，YAML 负责声明字段与规则，Python 加 SQLite 负责取数和拼装——三层各自写了一份关于系统的说法，彼此之间没有任何校验。于是说明文档里的统计、规则文件里的语义、代码里的实际行为可以同时存在而不冲突，读者只读其中一层就会拿到另一层兑不了的答案。

这篇文章按三层各自的口径把同一批结论对了一遍。所有数字都取自 2026-09-26 本机的一次完整走查：克隆仓库、用 `python3` 直接查询随库发行的 `extracted_results/elements.db`、逐行读那八个引擎模块、把三个生成入口各跑若干次并保留原始输出。核对基准是 main 分支 `e9512498402f6625300f42b9633d907a28dda126`，提交于 2026-05-10。这类数字会变，所以只在说明出现一次。

## 目录

1. [仓库形状与三层地图](#仓库形状与三层地图)
2. [三个「十二」各指什么](#三个十二各指什么)
3. [两套技能目录逐字节相同](#两套技能目录逐字节相同)
4. [技能层要跑的脚本不在仓库里](#技能层要跑的脚本不在仓库里)
5. [数据层的一张真实清单](#数据层的一张真实清单)
6. [声明层的两处失效](#声明层的两处失效)
7. [引擎层的一次真实调用](#引擎层的一次真实调用)
8. [一个防御性守卫如何反过来取空](#一个防御性守卫如何反过来取空)
9. [跨域查询的实际可达面](#跨域查询的实际可达面)
10. [三个入口各跑一遍](#三个入口各跑一遍)
11. [数字对照表](#数字对照表)
12. [采用建议与可抄的部分](#采用建议与可抄的部分)
13. [出错时先看哪几处](#出错时先看哪几处)
14. [下一步读哪几段代码](#下一步读哪几段代码)
15. [五个自测题](#五个自测题)
16. [参考](#参考)

## 仓库形状与三层地图

先说这层地图，因为后面每一处结论都要回到它上面定位。

```text
┌──────────────────────────────────────────────────────┐
│  技能层   .claude/skills/<name>/skill.md             │
│           .codex/skills/<name>/skill.md              │
│           12 个目录，写给智能体读，不被任何 .py 读取 │
└───────────────────────┬──────────────────────────────┘
                        │ 自然语言 → 结构化意图
┌───────────────────────▼──────────────────────────────┐
│  声明层   prompt_framework.yaml  7 类 25 字段        │
│           variables/*.yaml       配色 边框 装饰      │
│           design-logic/*/        设计原则与约束      │
└───────────────────────┬──────────────────────────────┘
                        │ 规则名与类别名（字符串约定）
┌───────────────────────▼──────────────────────────────┐
│  引擎层   intelligent_generator.py  1,075 行 人像    │
│           framework_loader.py         711 行 框架    │
│           element_db.py               751 行 读写    │
│           core/  五模块           1,772 行 跨域与设计│
└───────────────────────┬──────────────────────────────┘
                        │ SQL + 文件读取
┌───────────────────────▼──────────────────────────────┐
│  数据层   extracted_results/elements.db  1,246 元素  │
│           variables/*.yaml                10 色系    │
└──────────────────────────────────────────────────────┘
```

关键在于第三行注释：`grep` 全部 `.py` 文件，没有任何一处出现 `.claude`、`.codex` 或 `skills/` 字样。技能层和引擎层之间没有函数调用、没有配置读取，只有"智能体照着 Markdown 说的那套命令去调 Python"这一条人肉链路。同样的孤立关系还有两处：`design_templates` 表只在 `design-master` 和 `universal-learner` 两份 Markdown 里被提到，仓库里没有一行代码读它；`design-logic/` 那四个设计原则文件由一个函数体只有 `return None` 的桩函数"负责"，而唯一可能调用它的那一行还写着注释。

其余几项基本形状：

| 项目 | 值 | 取法 |
|------|-----|------|
| 提交数 | 14 | `git rev-list --count HEAD` |
| 作者 | 4 人（wangmeng 7、黄宗宁 5、Felictycf 1、huangserva 1） | `git shortlog -sne --all` |
| 标签 | 1 个，`v1.0.0` | `git tag -l` |
| 首次提交 | 2026-01-05 | `git log --reverse` |
| 最后提交 | 2026-05-10，"update: elements.db latest data" | `git log -1` |
| 跟踪文件 | 98 个，仓库 1,315 KB | `git ls-files \| wc -l` |
| Python 规模 | 12 个文件 5,145 行（含两套重复的技能脚本） | `wc -l` |
| 运行依赖 | `pyyaml`，其余全是标准库 | 见下 |
| 许可证 | README 声明 MIT，仓库无 LICENSE 文件 | `git ls-files \| grep -i licen` 无输出 |

`requirements.txt` 只有两行有效声明：`anthropic>=0.7.0` 和 `pyyaml>=6.0`。前者在仓库里只出现在三处：这一行本身，以及两份逐字节相同的 `learner.md`（`.claude` 与 `.codex` 各一份）第 384 行那段示例调用——没有任何 `.py` 导入它。想跑引擎，装一个 `pyyaml` 就够，这点值得说明文档写清楚。

许可证那格需要多说一句：README 末尾有 `## 📄 License` 和一行 `MIT License`，但没有许可文件，GitHub 的 license 字段返回 null。对使用者来说，"README 里写着 MIT" 和 "仓库带 LICENSE" 是两种确定程度不同的事。

## 三个「十二」各指什么

这个项目到处在说 12，指的不是同一批东西，而它们的一致性全靠人工维持。

**十二个技能。** `.claude/skills/` 下 13 个条目：12 个目录加一个散落的 `learner.md`。最后一次改动统计口径的提交把这件事说得很明白：

```text
0671803 fix: skill count 13→12 (no new skill added, just Codex adaptation)
```

也就是说 13 这个数在仓库自己的文档里存在过，理由是有人把 `learner.md` 数了进去。12 个目录的职责分工是：

```text
intelligent-prompt-generator  真正的入口（claude.md:278 指的就是它）
prompt-master                 自称主控，文件首行标着「⚠️ 旧架构」
domain-classifier             判断需求属于哪个领域
art-master / design-master    艺术风格 / 平面设计
product-master / video-master 产品摄影 / 视频生成
prompt-analyzer               拆解已生成提示词的结构与差异
prompt-extractor              从现有提示词里抽可复用模块
prompt-generator              通用生成器
prompt-xray                   从优秀提示词逆向"如何做 X"
universal-learner             把新提示词消化成元素写回库
```

`prompt-master` 这一格值得单独说明。把它列成"主控调度"是 README 的说法，而它自己的文件首行就是 `# ⚠️ 旧架构 - Prompt Master`，第 8 行写明数据源是一个 JSON 文件，第 10 行让新架构改用 `intelligent-prompt-generator`。这个目录里带「旧架构」标记的文件共 7 个（`skill.md` 加 `modules/core/` 下 6 个）。它说的那份 JSON 是 `extracted_results/facial_features_library.json`，不在仓库里——`.gitignore:72` 的 `extracted_results/*` 把整个目录排除，只用第 74 行的 `!extracted_results/elements.db` 把数据库单独捞回来。一个仍然占据技能目录名额的主控技能，数据源是一句指向不存在文件的说明。

**十二个领域。** 这里出现本次走查里第一处硬偏差。`elements` 表实际用到 12 个 `domain_id`，而声明领域的 `domains` 表只有 8 行：

```text
domain_id       说明            domains 表  实际元素   表内自记
portrait        人像摄影             有        502        491
common          通用摄影技术         有        208        203
design          平面设计             有        166         59
interior        室内设计             有         79         79
product         产品摄影             有         78         77
art             艺术风格             有         70         51
video           视频生成             有         49         49
prompt_writing  提示词写作           有          9          9
creative        创意综合          没有         37          —
scenario        场景描述          没有         34          —
utility         工具型提示词      没有         10          —
lifestyle       生活方式        没有          4          —
```

12 个领域求和正好 1,246，与说明文档一致；不一致的是登记表。`element_db.py` 建库时只种 7 行：

```python
    def _init_domains(self):
        """初始化7个领域"""
        domains = [
            ("portrait", "人像摄影", "Portrait photography elements"),
            ("interior", "室内设计", "Interior design elements"),
            ("product", "产品摄影", "Product photography elements"),
            ("design", "平面设计", "Graphic design elements"),
            ("art", "艺术风格", "Art style elements"),
            ("video", "视频生成", "Video generation elements"),
            ("common", "通用摄影", "Common photography techniques")
        ]
```

`prompt_writing` 是后来单独插进去的，`creative` / `scenario` / `utility` / `lifestyle` 四个则是数据长出来后没人回来登记。

"到底几个领域"这件事在仓库里有四个互不相同的答案，而且其中两个出现在同一个文件里。`domain-classifier/skill.md` 的 frontmatter 第 3 行写"准确判断所属领域（人像/艺术/设计/产品/视频）"，是 5 个；同一份文件第 18 行的标题是 `### 7大领域定义`，正文逐条列出 portrait / interior / product / design / art / video / common 共 7 个。这个 7 与 `element_db.py:151` 那句 `"""初始化7个领域"""` 完全对应——也就是说分类器实际被教去识别的，就是建库时那 7 个名字，数据里另外 5 个 `domain_id` 它压根没有判据。链路上的每一环都只知道自己那一份清单。

**十二张表。** 库里是 12 张业务表加一张 `sqlite_sequence`。仓库里没有任何一份文档列过这张清单。把 12 个表名逐个拿去 `grep` 全部 markdown，`element_tags`、`categories`、`design_variables`、`element_variables` 这四张一次都没出现过，其余八张散在 README 与技能说明里。想知道有几张表，只能把库打开数。少被提到的那几张恰好都在设计系统与统计这条线上（`design_templates`、`design_variables`、`element_variables`、`element_usage_stats`、`generated_prompts`、`prompt_elements`），也就是"模板级生成"这条路依赖的东西。

外键声明了但从未生效：`elements.domain_id` 声明 `REFERENCES domains(domain_id)`，而 Python 的 `sqlite3` 默认不开外键检查，仓库里 `PRAGMA foreign_keys` 出现 0 次。把开关手动打开再插一条 `creative` 领域的元素，立刻被拒：

```text
$ sqlite3 extracted_results/elements.db "PRAGMA foreign_keys=ON; \
    insert into elements (element_id,domain_id,category_id,name,ai_prompt_template) \
    values ('__t1','creative','poses','__t','x');"
Error: stepping, FOREIGN KEY constraint failed (19)
```

把三条外键关系逐条对一遍，结果是三条都在漏：

```text
elements.domain_id   → domains      12 个实际取值里有 4 个没有登记行
                                    （creative / scenario / utility / lifestyle）
elements.category_id → categories   70 个实际类别名里有 17 个没登记，涉及 53 行
                                    （special_effects 10、typography 8、
                                      backgrounds 7、layouts 4、hairstyles …）
categories.domain_id → domains      2 行指向未登记的 creative
                                    （style_aesthetics、rendering_techniques）
```

三条都违反表定义里写明的 `REFERENCES`，也都不会被报告：外键开关在这份代码路径上从没被打开过。一个默认关闭的约束，等于一份只用于注释的完整性声明。

## 两套技能目录逐字节相同

双平台支持这件事在 README 里只占一段目录树加一行提交记录，没有说清两套目录之间到底是什么关系。实测结果比任何描述都直接：

```text
$ diff -r .claude/skills .codex/skills
$
```

无输出，35 个技能文件逐个相同。两个 `.py` 也在其中（`prompt-xray/xray_helper.py` 158 行、`prompt-extractor/preprocessor.py` 260 行），两边各一份、内容一样，处理的是提示词的透视与抽取，跟 Codex 的输入输出无关。整个 `.codex` 树唯一的独有文件是入口 `codex.md`，而它与 `claude.md` 的全部差异是这 5 处：

```text
1c1
< # Claude Code 项目规则
---
> # Codex Code 项目规则
278c278
< **入口**：`.claude/skills/intelligent-prompt-generator/skill.md`
---
> **入口**：`.codex/skills/intelligent-prompt-generator/SKILL.md`
295c295
< Claude Code: 调用 intelligent-prompt-generator skill
---
> Codex Code: 调用 intelligent-prompt-generator skill
379c379
< - 我们是 **Skill 系统**，有 Claude AI 能力
---
> - 我们是 **Skill 系统**，有 Codex AI 能力
414c414
< - 我们在建立 skill 系统，不是展示 Claude Code 有多强！
---
> - 我们在建立 skill 系统，不是展示 Codex Code 有多强！
```

两份各 416 行，5 处差异全是把平台名原地替换。所谓"第二个平台的接入成本可控"，在这个项目里的真实形态是同义复制：没有任何一层抽象，改名即适配。这既是最便宜的迁移方式，也是维护负担最重的一种。`.claude` 与 `.codex` 各 37 个文件（35 份技能文件、1 份入口、1 份 `SKILL_ROUTING_GUIDE.md`），除入口那一份外，其余 36 份都是同一内容存两处，改一边就分叉。

顺带一处只有区分大小写的文件系统才会暴露的问题：12 个技能里 9 个的主文件叫 `skill.md`，3 个叫 `SKILL.md`（`intelligent-prompt-generator`、`prompt-analyzer`、`universal-learner`）。`git ls-files` 显示入库文件名确实是 `SKILL.md`，而 `claude.md` 第 278 行指向的是小写 `skill.md`；Codex 那份同一行已经写成大写。macOS 的 APFS 默认大小写不敏感，所以本地照旧解析成功；同一份文件放到 Linux 上就是一条指空的路径。检查这类引用时别用 shell 通配——`.claude/skills/*/SKILL.md` 在大小写不敏感的盘上会把只有小写文件的目录一起匹配进来，看着像存在两份副本。

## 技能层要跑的脚本不在仓库里

前面说过技能层不被任何代码读取。反方向的那条边更要紧：技能层写给智能体执行的命令，指向一批仓库里根本没有的文件，而 `.gitignore` 里有按名排除它们的规则。

`learner.md` 是那个"多出来的第 13 项"，它的第 38、41、96、136 行都在教智能体敲：

```text
python3 learner.py scan "A woman with long red hair, fair skin, wearing qipao"
python3 learner.py batch
```

第 494 行干脆把它列成工具清单，`CLI工具` 一栏填的就是 `learner.py`。而 `.gitignore:141` 那一行正是 `learner.py`，这个文件不在仓库里，`git ls-files` 也查不到。

同一类事实在技能层里散成一串。左边是这些提示词技能文件写给智能体的调用与数据源说明，右边是把它挡在仓库外的规则：

```text
learner.md:38,41,96,136            python3 learner.py scan / batch
learner.md:494                     CLI 工具一栏写着 learner.py
prompt-analyzer/SKILL.md:45        from prompt_analyzer import analyze_prompt_detail
prompt-generator/skill.md:100      from generator_engine import PromptGeneratorEngine
prompt-generator/skill.md:222      模板配置: templates.json
prompt-extractor/skill.md:102      module_library.json
prompt-extractor/skill.md:190      facial_features_library.json
prompt-master/skill.md 与
  modules/core/ 下三个文件          prompt_tool.py
```

这些文件为什么不在仓库里，原因分三种，都能用一条命令区分：

```text
按名排除      .gitignore:141 learner.py
              .gitignore:151 generator_engine.py
              .gitignore:160 prompt_analyzer.py
              .gitignore:161 prompt_tool.py
              .gitignore:185 templates.json
整目录排除    .gitignore:72  extracted_results/*
              （:74 的 !extracted_results/elements.db 是唯一例外；
                prompt-master/skill.md:223-224 与 learner.md:296 写的
                数据源正是 extracted_results/ 下的那两个 JSON）
从未入库      prompt-extractor 按裸名引用的 module_library.json 与
              facial_features_library.json 没有任何排除规则命中，
              它们只是从来没被提交过
```

区分的办法是 `git check-ignore -v <路径>`：命中就有规则行号，没命中而 `git ls-files` 也查不到，就是第三种。

12 个技能目录里有 4 个（`prompt-analyzer`、`prompt-generator`、`prompt-extractor`、`prompt-master`）把不存在的文件当成可用工具来写，散在旁边的那个 `learner.md` 则整份都是这种情况。

这不是遗漏，`.gitignore` 里那一段写得很清楚，标题是"临时开发脚本（Development Scripts）……这些是开发过程中的临时工具，不是项目核心"。作者对这批脚本的定位就是本地工具。问题在于技能层没有跟着收缩：上面那批 markdown 仍然按"这条命令可用"的语气在写，而读者照做的第一条就是 `python3 learner.py batch` 报文件不存在。

于是"这不是一个普通的 Python 工具，而是一个完整的 Skills 系统"这句话有了两种读法。作为架构描述它成立——知识确实主要住在 markdown 里；作为可用性描述它不成立——4 个技能目录加 `learner.md` 的主文件、连同 `prompt-master` 下 3 个子模块，指向的都是仓库里不存在的脚本与数据文件；剩下 8 个技能目录依赖的 `intelligent_generator.py` 与 `core/`，又只实现了它们说的一部分（`design_templates` 没有任何代码读取，`element_usage_stats` 的写入函数没有调用点）。技能层是完整的说明书，引擎层是它的一个子集实现。

## 数据层的一张真实清单

`extracted_results/elements.db` 的 12 张业务表，行数一次性取全：

```text
elements             1,246   核心表，每行一个可复用片段
tags                 2,324   标签，usage_count 全部非零
element_tags         5,127   元素-标签多对多
source_prompts         675   社区语料原文
categories              57   类别登记表
domains                  8   领域登记表
element_usage_stats     27   元素使用统计
generated_prompts       17   已保存的生成结果
prompt_elements         42   结果与元素的关联
design_templates         5   完整设计系统模板
design_variables         4   设计变量（SQLite 侧）
element_variables        5   元素的可变参数
```

`elements` 表结构里三处与介绍文字对不上，都在"字段名义语义"这一层。

第一处是 `reusability_score`。表定义写 `CHECK(reusability_score >= 0 AND reusability_score <= 10)`，实测 1,239 行非空、7 行为空，取值区间是 6.0 到 10.0，均值 8.50。约束给了 0 到 10，数据只住在上半区。这直接决定了下文的排序行为：一个"按分数降序取第一条"的查询，取到的是该类别里历史打分最高的那条记录，跟用户要什么无关。

第二处是 `learned_from`。建表注释写 `'manual' or 'auto_learner'`，实际非空值 18 种、另有 39 行为空：

```text
universal_learner_v2       861   migrated_from_v2        104
migrated_from_v4            81   manual_learning          39
VoxcatAI Twitter            18   universal_learner        14
Brand visual system ...     13   AUTO-OMNI Visual ...     13
现代商务科技典雅风格PPT     12   universal_learner_skill_test 11
batch_learner_v2_enhanced   10   anti_pattern_analysis     9
Premium cinematic 21:9 ...   7   prompt_extractor_analysis 5
manual_zhang_yimou_style     4   manual_period_costume     3
manual_tsui_hark_style       2   manual_cinematic_style    1
```

这是一个自由文本字段，不是枚举。它能告诉你这条记录是哪个批次灌进来的，撑不起"区分人工录入与自动学习"这个用途——同一个含义至少有 `manual_learning`、`manual_zhang_yimou_style`、`manual_period_costume` 三种写法。

第三处是登记计数与真实计数长期不一致。`_update_counts()` 会重算 `domains.total_elements` 和 `categories.total_elements`，但它只在 `add_element()` 路径上被调用；这一批数据不是逐条 `add_element` 加进来的，于是 8 行领域记录有 5 行的自计数字段是错的（`design` 记 59、真实 166，差得最远），57 行类别记录有 17 行数字陈旧。表里同时存"计数值"和"计数来源的数据"，又没有一条重算入口，是这类库最常见的腐化路径。

类别名本身的卫生问题也值得记一笔。`categories.category_id` 是全局主键、每行只登记一个所属领域，可 `elements` 里的类别名是跨领域复用的。`lighting_techniques` 登记在 `common` 名下、自计 449 条，实际 453 行里有 224 行挂在 `portrait`，另外散在 10 个领域。57 行登记中 17 行的计数字段已陈旧，4 行（`prompt_writing_best_practices` 等）对不到任何元素。`portrait` 域下还同时存在 `hair_style`（1 条）、`hair_styles`（5 条）、`hairstyles`（1 条）三种拼法，而引擎只查 `hair_styles`；117 个 `name` 值被两个以上元素共用。

语料表 `source_prompts` 的状态字段是 `learning_status`（不是 `status`），三档实测：

```text
completed        246
metadata_only    288
pending          141
```

`completed` 与说明一致。但把"待处理"写成 `pending + metadata_only = 429` 掩盖了两者性质不同：`metadata_only` 是只进了元数据、原文可能都不可用，占 288 条，比真正排着队等学习的 141 条多一倍。学习闭环的燃料存量应按 141 估，不是 429。

说明文档还给出一个类别分布：「海报设计 163、人像摄影 112、UI 设计 82、综合创意 65、产品摄影 7」。这一组数在库里复算不出来。`source_prompts.theme` 是自由文本，627 个不同取值、46 行为空、最长 90 字符，内容是单条提示词的标题（比如 `Liu Yifei Douyin Livestream Screenshot`），不承担分类。库里唯一可复算的分类信号是 `domain_classification` 这个 JSON 串里的 `primary` 键：

```text
design 321   portrait 183   creative 64   utility 45   scenario 35
art 9        product 8      lifestyle 5   common 4     misc 1
```

十项求和 675。它和"海报设计 / UI 设计 / 电商 / 广告创意"这套叙述不在同一个分类体系上。

最后两张统计表说明设计意图存在、通路断了。`element_usage_stats` 有 27 行、`usage_count` 累计 42，写它的是 `intelligent_generator.py:979` 的 `save_generated_prompt()`：插入 `generated_prompts`、写关联到 `prompt_elements`、再按增量平均更新使用统计。这套写入逻辑本身是完整的——但 `save_generated_prompt` 在全仓库只有定义，没有任何调用点。库里那 17 条 `generated_prompts` 记录的时间戳全部落在 2026-01-03 到 2026-01-13 之间，`element_usage_stats` 的 `last_used` 也停在同期，此后没有新增；读它们的代码同样不存在。

## 声明层的两处失效

`prompt_framework.yaml` 是这套系统里最干净的一块工程：`framework_version: "1.0"`，7 个大类共 25 个字段，3 条依赖规则，2 条一致性校验。7 大类依次是 subject（3 字段）、facial（6）、styling（5）、expression（2）、lighting（1）、scene（4）、technical（4）。

依赖规则确实是文档写的那样工作：

```text
规则 1  when scene.era=ancient
        then styling.clothing=traditional_chinese
             styling.hairstyle=ancient_chinese
             styling.makeup=traditional_chinese
规则 2  when subject.ethnicity=East_Asian and styling.hair_color=auto
        then styling.hair_color=black
规则 3  when subject.ethnicity=East_Asian and facial.eyes=auto
        then facial.eyes=almond
```

`framework_loader.py:78` 的 `apply_dependencies()` 跑通了这三条，实测输出与 YAML 一致。但它的实现有两处会伤到调用方，都在同一小段代码里（下面逐行照录 `:89-104`）：

```python
        updated_intent = intent.copy()

        dependencies = framework.get('dependencies', [])

        for rule in dependencies:
            # 检查条件是否满足
            if 'when' in rule:
                conditions_met = True

                for condition_field, condition_value in rule['when'].items():
                    category, field = condition_field.split('.')
                    actual_value = updated_intent.get(category, {}).get(field)

                    if actual_value != condition_value:
                        conditions_met = False
                        break
```

`intent.copy()` 是浅拷贝。当 `then` 要写入的类别在原始 `intent` 里已经存在时，赋值直接改到调用方那个嵌套字典上。实测：

```text
输入   {'scene': {'era': 'ancient'}, 'styling': {'makeup': 'k_beauty'}}
输出   {'scene': {'era': 'ancient'},
        'styling': {'makeup': 'traditional_chinese', 'clothing': 'traditional_chinese',
                    'hairstyle': 'ancient_chinese'}}
调用方原字典   styling 已变成上面那份，k_beauty 被就地覆写
```

于是"把推导前后的意图做对比"这类常规写法拿不到两个版本，只能拿到一份被改过的。修法是一行 `copy.deepcopy`，代价是没人会看见这个 bug，因为下游只消费返回值。

条件匹配用的是 `!=` 精确比较加一个 `break`，所以 `when` 里只要出现列表值（例如某条规则写成 `era: [ancient, future]`）就永远匹配不上——这条现在不影响，因为三条规则的 `when` 全是标量；它影响的是校验规则。

`framework_loader.py:122` 的 `validate_intent()` 里，一致性检查那段是这样结束的（逐行照录 `:156-169`）：

```python
                    # 如果值在条件列表中，说明有问题
                    if isinstance(condition_values, list):
                        if actual_value in condition_values:
                            issues.append({
                                'type': 'consistency_check',
                                'name': check['name'],
                                'severity': check['severity'],
                                'message': check['message'],
                                'suggestion': check.get('suggestion', '')
                            })
                    else:
                        if actual_value == condition_values:
                            # 检查其他条件字段
                            pass
```

标量条件分支的最后一句是 `pass`。也就是说：只有列表值的条件会产出问题，标量条件被求值然后丢掉。两条 YAML 校验规则各自带一个标量条件加一个列表条件，实际生效的只剩下列表那一半。三个实验：

```text
A  era=modern   + makeup=k_beauty      → error「古装场景不应该使用现代妆容」
B  完全不给 scene，只 makeup=k_beauty  → 同一条 error
C  ethnicity=European + eyes=green     → warning「东亚人通常不会有绿色/蓝色眼睛」
```

A 和 B 都不该报：时代不是 ancient。C 也不该报：人种是 European。规则文件写的是"古装场景配现代妆容算冲突""东亚人配绿蓝眼睛算可疑"，代码执行的是"妆容落在现代集合里就报错""眼色落在 green/blue 里就警告"，与时代和人种无关。`required_fields` 那两条（必须有 `lighting.lighting_type`、必须有 `styling.makeup`）逻辑正常，走的是另一个分支。

这一处值得单独标出来，因为它和前一节的登记表漂移不是同一类问题：登记表是数据没同步，这里是声明表达能力超出了求值实现。YAML 里目前没有任何一条规则用到"标量条件 + 列表条件求交"的组合，而这个组合恰好是这套声明式框架存在的理由。

## 引擎层的一次真实调用

`intelligent_generator.py` 有 1,075 行，其中人像主流程 `select_elements_by_intent()` 从 186 行开始。先把它真正读取的键列清楚，因为文档里出现的"意图字典"示例普遍写成 YAML 那套七大类嵌套，而这两个形状不是一回事：

```text
读取           intent['subject']['gender' | 'age_range' | 'ethnicity']
               intent['visual_style']['art_style']
               intent['atmosphere']['theme' | 'director_style']
               intent['clothing']      ← 顶层，默认 'modern'
               intent['hairstyle']     ← 顶层，默认 'modern'
               intent['era']           ← 顶层，默认 'modern'
               intent['lighting']      ← 顶层，默认 'natural'
不读取         intent['facial']、intent['styling']、intent['lighting']['lighting_type']
```

如果按 YAML 的形状把 `lighting` 写成 `{'lighting_type': 'cinematic'}`，不会报错，但结果会更糟。这个字典被原样 `append` 进风格关键词列表，而参数是这样拼的：`params = [f"%{kw}%" for kw in keywords]`。f-string 把字典转成了字面文本 `%{'lighting_type': 'cinematic'}%`，作为 `LIKE` 模式什么也匹配不上。实测：同一份意图，`lighting` 写成字符串 `'cinematic'` 得 21 个元素，写成那个字典只剩 9 个，而且少掉的正是全部风格元素——光影、氛围、导演特征一起消失，提示词依然能拼出来。形状不匹配在这里不抛异常，只让输出悄悄降级。所以人像引擎只吃它自己那套扁平形状，声明层的形状归 `framework_loader.py` 那半边用。

固定查询是 13 个类别，全在 `portrait` 域内：`gender`、`age_range`、`ethnicity`、`eye_types`、`hair_colors`、`clothing_styles`、`hair_styles`，以及一个循环里的 `skin_tones`、`skin_textures`、`face_shapes`、`makeup_styles`、`expressions`、`poses`。这 13 组在库里合计 87 个候选，占 1,246 的 7.0%。

13 组里带过滤条件的是 6 组。`gender` 与 `ethnicity` 用的是用户给的值；`eye_types` 与 `hair_colors` 用的值不是用户给的，是代码按 East_Asian 推出来的（分别是 `almond` 和该人种典型发色的第一项 `black`）；`clothing_styles` 与 `hair_styles` 只在用户给了非默认值时才过滤，而且先过一张同义词表——表里没有的值会被原样当作过滤条件拿去 `LIKE`。实测把 `clothing` 从 `modern` 改成 `qipao`：映射表里没有这一项，搜索键就退化成 `['qipao']`，而库里没有任何服装元素的模板含这个词。程序打印一句 `未找到'qipao'服装元素，将通过风格关键词搜索` 之后什么也没补，最终元素从 21 个变 20 个，缺的那一格正是 `clothing_styles`。用户要的衣服没穿上，默认的现代装也没了。剩下 7 组（`age_range` 和循环里那 6 个）从不带过滤条件：

```python
        if 'age_range' in subject:
            elem = self.get_element_by_category('portrait', 'age_range')
```

不带过滤时 `get_element_by_category()` 走的分支等价于"该类别里 `reusability_score` 最高的一条"。`age_range` 三条候选里 `young_adult` 恰好是 10.0 那个，所以传 `child` 也会拿到 `young_adult`。同理 `makeup_styles` 拿到的不是用户想要的 natural，而是 9.8 分的 `k_beauty`。

风格部分先汇关键词：非默认的服装与发型各自的映射表、`art_style`、`theme`、`lighting`、非 modern 的 `era`（ancient 额外补 `traditional` / `period` / `classical`），导演风格则两处相加——`load_knowledge()` 的 `lighting_keywords` 6 个，加函数内硬编码 4 个，`zhang_yimou` 得到 10 个：

```text
dramatic, shadow, rim, contrast, chiaroscuro, volumetric   ← 知识库
traditional, red, gold, period drama                        ← 硬编码
```

`load_knowledge()` 里还有三张表没在介绍里出现过：`style_types`（9 个风格到 `art_style` / `atmosphere` / `lighting` 的归类）、`director_lighting_styles`（3 位导演）、`subject_attribute_categories`（10 个类别名，用于排除）。

汇完关键词交给 `search_style_elements()`：

```python
        keyword_conditions = " OR ".join(["ai_prompt_template LIKE ?" for _ in keywords])
        query = f"""
            SELECT element_id, name, chinese_name, ai_prompt_template,
                   keywords, reusability_score, category_id
            FROM elements
            WHERE ({keyword_conditions})
              AND ai_prompt_template != ''
            ORDER BY reusability_score DESC
            LIMIT 30
        """
```

`WHERE` 里只有 `LIKE` 串和一条非空判断，**没有 `domain_id` 条件**：风格搜索是全库范围的。排除动作发生在 Python 里、在这条 SQL 之后：

```python
        elements = []
        for row in self.cursor.fetchall():
            # 过滤掉人物属性类别
            if row[6] in excluded_categories:
                continue
```

于是 30 这个窗口是按 `reusability_score` 从高到低截断的，被排除的 10 个人物属性类别只要挤进前 30 就白占名额；`ORDER BY` 用的还不是最终排序依据——相关性在这之后才算（`intelligent_generator.py:452-462`，逐行照录）：

```python
            # 综合得分 = 相关性 × 质量分
            elem['relevance'] = relevance
            elem['final_score'] = relevance * row[5]  # reusability_score

            elements.append(elem)

        # 按综合得分排序
        elements.sort(key=lambda x: x['final_score'], reverse=True)

        # 返回前10个最相关的
        return elements[:10]
```

`relevance` 由 `calculate_relevance()` 给出：命中关键词数除以关键词总数，一个关键词都不给时返回 0.5。三个数串起来看，这个函数的真实语义是"在全库质量分前 30 名里，按相关性重排，取前 10"，而不是"按相关性找最相关的 10 条"。

选完元素，最后一棒是 `compose_prompt(elements, mode='auto', keywords_limit=3)`（`intelligent_generator.py:749`）。这一步的规则比前面任何一处都更影响成品，而它只写在代码里：

```python
            if mode == 'simple':
                text = template
            elif mode == 'detailed' and keywords and len(keywords) > 0:
                text_list = keywords[:keywords_limit]
            elif mode == 'auto' and keywords and len(keywords) > 2:
                text_list = keywords[:keywords_limit]
            else:
                text = template
                text_list = None
```

默认模式下，只要一个元素带超过 2 个关键词，它的 `ai_prompt_template` 就**整个被丢掉**，进提示词的是这个元素的前 3 个关键词。库里 1,246 条元素有 670 条（53.8%）满足这个条件，`portrait` 域内是 255/502。也就是说"每行元素的 `ai_prompt_template` 才是实际拼入提示词的文本"这句话，对一半以上的库存是不成立的——真正被写进输出的，是关键词表的前三项。

这条规则还顺带解释了三件事。其一，`keywords` 列声明是 JSON 数组，实测 34 行存的是逗号分隔的裸字符串（如 `three-point lighting, dramatic lighting, key light, ...`），`json.loads` 抛错被 `except: pass` 咽下，这些元素于是走回模板分支——格式错误在这里反而成了幸运。其二，关键词是给人看的标签，不是能拼接的短语，所以取前三项拼出来的东西会退化：库里有元素的关键词就是 `real`、`life`、`scene`、`featuring` 这类单词，代码只挡住了长度小于 4 的单词，剩下的照原样进句子。其三，函数说明把 `'simple'`、`'auto'`、`'detailed'` 三种模式平列，但 `mode == 'simple'` 那一支只给 `text` 赋值、不初始化 `text_list`，紧接着的 `if text_list:` 在第一个元素上就抛 `UnboundLocalError`，实际可用的只有后两种。

`compose_prompt()` 里还有两张人工维护的表：15 组同义词用于概念去重，一个 10 项黑名单用于丢掉"明显不属于人像"的词，黑名单里包括 `'elements'` 和 `'highlighting'`。这两张表的键都是英文字面量，也就是说元素一旦改名或换词，去重与过滤会静默失效。

`check_consistency()` 实测有 **三条** 规则，不是两条，且三档严重度都用上了：

```text
ethnicity_eye_mismatch    medium   东亚人/African 的眼睛模板里出现 green/blue/violet
ethnicity_hair_mismatch   low      发色不属于该人种的典型发色集合
duplicate_category        high     同一类别出现两次（lighting_techniques、
                                   photography_techniques 两个类别豁免）
```

第三类是实际最容易触发的一类，因为它不由引擎的意图驱动，而由 `search_style_elements()` 的跨域捞取带出来。同一条 zhang_yimou 意图直接跑人像引擎，拿到 21 个元素，其中 4 个来自 `design` 域：

```text
gender            female                     10.00
age_range         young_adult                10.00
ethnicity         east_asian                 10.00
skin_tones        fair_pale                   9.50
face_shapes       oval_asian_refined         10.00
makeup_styles     k_beauty                    9.80
...（人像域属性共 11 条）
lighting_techniques  ×5                      相关性 0.25–0.33
skin_textures       realistic_textured_pores 相关性 0.17   ← 重复类别
layouts             apple_glass_card_system  相关性 0.17   ← design 域
layouts             12_column_8pt_grid_system 相关性 0.17  ← design 域
color_schemes       material_blue_theme      相关性 0.17   ← design 域
typography          material_text_color_hierarchy 0.17     ← design 域
```

一致性检查随即报两条 `high`：`skin_textures` 出现 2 次、`layouts` 出现 2 次。人像里混进 12 栏栅格和 Material Design 文字色阶，原因是 `red` / `gold` / `traditional` 这几个关键词在 `layouts` 和 `color_schemes` 的模板文本里也出现，而搜索不分域。

## 一个防御性守卫如何反过来取空

`get_element_by_category()` 里有一段值得单独讲的代码。全文数下来，它是这套系统里最典型的一处：注释把问题说清楚了，结论仍然是错的。

```python
        # 验证name是否匹配value_filter（避免子串误匹配，如female被male匹配）
        if value_filter and row[1].lower() != value_filter.lower():
            # 如果不匹配，尝试直接用name精确匹配
            query_exact = """
                SELECT element_id, name, chinese_name, ai_prompt_template,
                       keywords, reusability_score, category_id
                FROM elements
                WHERE domain_id = ? AND category_id = ? AND name = ?
                ORDER BY reusability_score DESC LIMIT 1
            """
            self.cursor.execute(query_exact, [domain, category, value_filter])
            row = self.cursor.fetchone()
            if not row:
                return None
```

要防的问题是真的。`gender` 类别里搜 `male`，`LIKE '%male%'` 会先命中 `female`：

```text
female  10.0
male    10.0
```

`ORDER BY reusability_score DESC LIMIT 1` 因此把 female 当成 male 返回。守卫用 `name` 全等复核，这个方向上是对的。

代价落在另外两个值上。`female` 之所以通过，是因为库里真有一个 `name` 恰好等于 `female` 的元素；`almond` 和 `black` 没有这种元素：

```text
LIKE '%almond%' 在 portrait/eye_types 命中：
    large_expressive_almond   9.8
    almond_brown_eyes         9.0
全库 name = 'almond' 的元素数：0

LIKE '%black%' 在 portrait/hair_colors 命中：
    black_hair   8.5
全库 name = 'black' 的元素数：0
```

第一个 `LIKE` 已经找到了语义正确的元素，守卫嫌 `name` 不完全相等，改跑 `name = 'almond'`，取回 0 行，函数返回 `None`。East_Asian 分支的两次自动推导于是双双落空：上面那次实跑的 21 个元素里没有 `eye_types`，也没有 `hair_colors`。返回 `None` 不打印任何东西，`select_elements_by_intent()` 看到空值就跳过。"东亚人默认杏仁眼、默认黑发"这条推导，在最终提示词里的表现是没有留下任何痕迹。

这条链还能往前接一步，接到声明层：YAML 规则 2、3 推导出来的目标值正是 `black` 和 `almond`。规则层负责产生这两个字符串，查询层负责消费这两个字符串，两边都按"值等于名字"的约定写，而库里 `name` 的实际命名习惯是 `large_expressive_almond`、`black_hair` 这种多词形式。三层地图里那条"字符串约定"的箭头，就是在这里断的。

复算很快，一行就够：

```text
sqlite3 extracted_results/elements.db "select count(*) from elements where name='almond'"
0
```

## 跨域查询的实际可达面

v2.0 的入口是 `core/cross_domain_generator.py` 的 `generate()`，说明文档给它的说法是"自动识别类型并路由"。类型判定确实存在，但不是按"领域特征"，而是 `parse_user_input()` 的一串关键词命中加 `classify_generation_type()` 的一条固定优先级：

```text
design        ← intent 里有 design_style 或 design_requirement
cross_domain  ← 有 action / energy，或 art_style 含 3d / wax / holographic
portrait      ← 有 subject
cross_domain  ← 兜底
```

`parse_user_input()` 里最抢眼的一处是男性判定：`['男', 'man', 'male', '男性', '悟空', 'goku']`。把某部作品的主角名硬编进性别词表，是为了让示例输入走通。

真正决定"可用元素有多少"的是 `core/cross_domain_query.py:90` 的 `analyze_required_domains()` 和 `:143` 的 `build_query_plan()`。前者用 `in` 判断，但两类判断作用在 `intent` 的**键**上：

```python
        design_keywords = ['layout', 'composition', 'typography', 'poster', 'card']
        if any(k in intent for k in design_keywords):
            domains.add('design')

        # 有产品 → product
        if 'product' in intent:
            domains.add('product')
```

`parse_user_input()` 从来不写 `layout` / `poster` / `product` 这几个键——海报类输入写的是 `design_requirement = True`。所以在自动路径上，`design` 和 `product` 两个领域永远不会进 `required_domains`。`action`、`energy` 是例外，解析器确实会写。另外函数无条件 `domains.add('common')`，所以 common 恒在。

`build_query_plan()` 给每个领域一份硬编码类别清单，25 组 `(domain, category)`。把清单原样拿去问库：

```text
portrait (11 组)    76   gender 2, age_range 3, ethnicity 8, eye_types 12,
                       face_shapes 7, skin_tones 9, makeup_styles 13,
                       hair_styles 5, hair_colors 2, expressions 8, poses 7
common   (4 组)   153   lighting_techniques 87, photography_techniques 61,
                       poses 5, technical_quality 0
video    (3 组)    28   scene_types 28, motion_effects 0, camera_movements 0
art      (2 组)    29   art_styles 19, special_effects 10
design   (3 组)    20   layout_types 0, visual_styles 2, composition_techniques 18
product  (2 组)     0   photography_styles 0, lighting_setups 0
```

25 组里 6 组在库中命中 0 行，且这些名字在库里都有近邻真实类别：`motion_effects` / `camera_movements` 不存在（`video` 域只有 `scene_types`、`lighting_techniques`、`photography_techniques`、`technical_effects`）；`layout_types` 不存在（`design` 域有 `layouts`、`layout_systems`、`layout_templates`）；`product` 两组全空（真实类别叫 `product_styles`、`product_types`）。清单与库之间也是一条没人校验的字符串约定。

把自动路径可达的四个领域（portrait、video、art、common）合起来，候选元素 286 个，占 1,246 的 23.0%；加上不可达的 design 与 product 两组，也才 306 个、24.6%。这还没有算 `query_domain()` 的接受闸门：

```python
            if best_elem and score > 20:  # 分数阈值
                elements.append(best_elem)
```

每个类别只取 `ElementSelector.select_best_element()` 选出的**一条**，且分数不超过 20 就丢弃。也就是说 286 是候选全集的上界，一次调用真正可能进结果的类别槽位是 25 个（自动路径 20 个），每个最多贡献 1 条。

说明文档里"跨 domain 可用 995 个元素 / 数据库利用率 79.9%"是另一个问题的答案：502 + 208 + 166 + 70 + 49 = 995，五个领域名下元素数之和。它衡量的是"这五个领域里存了多少东西"，不是引擎能碰到多少东西。

## 三个入口各跑一遍

同一份库、同一份代码，三个输入各跑一次，原始输出保留如下。

**输入一：`龙珠悟空打出龟派气功`**（README 用来说明跨域能力的那个例子）

```text
📌 生成类型: cross_domain
📊 分析结果：需要 3 个domain: common, video, portrait
  🔍 查询 common domain: lighting_techniques, photography_techniques, poses, technical_quality
  🔍 查询 video domain: scene_types, motion_effects, camera_movements
  🔍 查询 portrait domain: gender, age_range, ethnicity, eye_types, ...（11 项）
  📊 合并了 1 个元素来自 3 个domain
  ⚠️  元素较少，使用intelligent_generator补充...
  📊 补充后共 19 个元素
  🔍 发现 3 个一致性问题，正在修复...
     ✓ 移除重复的'skin_textures'类别元素
     ✓ 移除重复的'makeup_styles'类别元素
     ✓ 移除重复的'wood_finishes'类别元素
  TYPE: cross_domain   META: element_count 13, domains_used [common, video, portrait]
```

四个可核对的点：

- 识别出 3 个领域，不是介绍里那张四行表（人物 portrait / 动作 video / 视觉风格 art / 光影 common）里的 4 个。`art` 从未被请求，因为这条输入里没有 3D 或动漫关键词。
- 跨域查询本身只交付 1 个元素；补充后共 19 个，其中 18 个来自"元素太少就回落到人像引擎"这个兜底分支，也就是 v1.0 那条路径。
- 3 条一致性问题把元素从 19 减到 13。原因是 `resolve_conflicts()` 对 `duplicate_category` 的处理是"该类别除第一条以外全部删除"，而 `check_consistency()` 每个重复类别只报一条问题——一个类别里有三份，就是一条问题去掉两份。
- 被去掉的三个重复类别里有一个是 `wood_finishes`。这个类别名在库里只挂在 `common` 名下（共 4 条），却出现在了一条悟空的提示词里。
- 最终提示词 587 字符，全文如下。

```text
Son Goku, powerful martial artist, natural window light, soft window lighting,
diffused daylight, male, casual, modern, comfortable, ponytail with bangs, fair
skin, pale complexion, visible pores, natural imperfections, oval face, delicate
refined Asian facial structure, symmetrical features, Korean K-beauty makeup
style, fresh natural dewy skin, gradient lips, straight brows, innocent gaze,
relaxed, textile and wood combination, cozy natural pairing, soft fabrics with
warm wood, light oak, natural wood, warm blonde, floor to ceiling windows, full
height glazing, panoramic windows
```

一条"悟空发龟派气功"的提示词里，最后 9 个片段全在描述布料、木料与落地窗。成因不在跨域查询，而在兜底路径上的一个**默认值**：`parse_user_input()` 把 `lighting` 无条件初始化成 `'natural'`，这条输入又没触发任何改写，于是 `select_elements_by_intent()` 收到的风格关键词只有一个 `natural`。把它单独喂给 `search_style_elements()`，全库 `LIKE '%natural%'` 的返回是：

```text
skin_textures          realistic_textured_pores      portrait
makeup_styles          k_beauty / j_beauty / french_elegant / thai_delicate
material_combinations  textile_wood                  interior   ←
lighting_techniques    natural_window_light          common
wood_finishes          light_oak                     common     ←
wood_finishes          natural_wood_tone             common     ←
design_elements        floor_to_ceiling_windows      interior   ←
```

`relevance = 命中数 / 关键词总数`，在只有一个关键词时对所有命中项一律给 1.0，排序完全退回 `reusability_score`。所以带 `natural` 字样的室内材质与人像妆容是同分竞争，谁排前面取决于当年录入时的打分。这条链上没有任何一处写着"这是人像生成"，域隔离本来就不存在。

**输入二：`生成电影级的亚洲女性，张艺谋电影风格`**（README 的第一个示例）

```text
📌 生成类型: portrait   META: element_count 19, issues_fixed 0
```

走的是 portrait 分支，19 个元素、0 个一致性问题。`parse_user_input()` 从"电影级"里只认出 `lighting='cinematic'` 这一个风格关键词——导演风格那条分支它压根没走到，`atmosphere.director_style` 不是解析器会写的键。于是这一个词进了全库搜索，两位日本街头摄影师就这样出现在了一条张艺谋风格的人像提示词里。

拆开看，这两条命中正好把上一节那条拼接规则的两面各演示了一遍。第一条是 `portrait_visual_styles_097`：它的 `ai_prompt_template` 是一整段 1980 年代胶片快照描述（"...vintage Japanese street photography style, Nobuyoshi Araki and Daido Moriyama inspired, candid composition, shallow depth of field, cinematic color grading"），末尾那个 cinematic 让它被 `LIKE '%cinematic%'` 挑中；但因为它有 5 个关键词，`mode='auto'` 把这段模板整个丢掉，进输出的反而是它 `keywords` 数组的前三项：

```text
["1980s Japanese street photography", "Nobuyoshi Araki style",
 "Daido Moriyama aesthetic", ...]
```

也就是说作者写好的那句话读者永远看不到，看到的三个短语是标签。第二条是 `design_lighting_techniques_008`，`name` 为 `is_warm_and_cinematic`，`keywords` 恰好只有 `["warm", "cinematic"]` 两项——不超过 2，于是走模板分支，而它的 `ai_prompt_template` 字面值就是 `is warm and cinematic`。一个没有主语的句子碎片就这样被逗号接进了句子中间，而且它登记在 `design` 领域名下。

前一种是检索边界与拼接规则叠加的结果，后一种是被检索数据本身的质量问题。这个引擎里没有任何一道关口能挡住它们中的任意一个。

**输入三：`温馨可爱风格的海报卡片`**

```text
📌 生成类型: design
📊 分析结果：需要 3 个domain: common, video, portrait      ← 没有 design
📊 SQLite元素: 1 个
🎨 YAML变量: 风格=温馨可爱
PROMPT: Color scheme: 奶油色系, primary color 香草白 (#FFF8E7),
        Decorative elements: elements, soft natural window light, diffused daylight
```

这一条路上有三处可核对的偏差：`design` 域没被请求（还是 `analyze_required_domains` 那个键判断），SQLite 侧因此只贡献 1 个元素；`Decorative elements: elements` 里打印的是 YAML 的段落名而不是装饰物名；边框条款整条消失。后两处的成因都在 `core/yaml_sampler.py`——`colors.yaml` 的第二层键是色系名，而 `borders.yaml` 和 `decorations.yaml` 的第二层键是**参数名**：

```text
colors.yaml       温馨可爱 → {珊瑚粉色系, 天空蓝色系, 薄荷绿色系, 奶油色系, 文字色系}
borders.yaml      温馨可爱 → {corner_radius, box_shadow, border}
decorations.yaml  温馨可爱 → {elements, combinations}
```

采样器对三个文件用同一套"在第二层随机挑一个键"的逻辑，于是配色挑到了色系，边框挑到了 `corner_radius`，装饰挑到了 `elements` 或 `combinations`。真正把这段文字拼出来的是 `core/design_bridge.py:138`，它随后去读边框的具体值：

```python
        if 'borders' in yaml_variables:
            borders_data = yaml_variables['borders']
            border_name = borders_data.get('border_name', '')
            border_config = borders_data.get('border_config', {})
            radius = border_config.get('radius', '')
            if radius:
                merged['design'].append({
                    'type': 'border',
```

`corner_radius` 那份配置里的键是 `values` / `unit` / `default` / `description`，没有 `radius`，于是 `if radius` 不成立，边框被静默丢掉。装饰那条没有做这层判断，就直接把参数名打了出来。

顺带一个值得单独一提的细节：同样的四行判断在 `core/yaml_sampler.py:238` 里还有一份，挂在 `get_prompt_description()` 上。那个函数带自己的配色文案（写的是 `Color palette:` 而不是 `Color scheme:`），而它在整个仓库里只有一个调用点——同文件第 290 行的 `test_yaml_sampler()`，也就是仓库自带的那个演示函数。所以设计模式的真实文案出自 `design_bridge.py`，`yaml_sampler.py` 里那套格式化代码从来没被生产路径执行过，两处逻辑靠复制保持一致。

有意思的是仓库里两份文档对这段输出的记述并不一致，而它们各自记的是不同阶段的东西。`README.md:335` 的示例 3 原样保留了参数名泄漏：

```text
Color scheme: 天空蓝色系, primary color 淡紫蓝 (#C7CEEA),
Decorative elements: elements, soft natural window light,
Border style: box_shadow, round corners 20px...
```

`UPGRADE_GUIDE_v2.0.md:244` 到 253 写的却是理想形状：`border_name` 为 `大圆角`、`decoration_name` 为 `星星`。前者离实跑结果更近（连 `Border style: box_shadow` 都是同一个毛病，把参数名当成了样式名），后者与 `sample_variables()` 开头那段函数说明逐字一致——它承诺返回 `{'borders': {'style': '大圆角'}, 'decorations': {'type': '星星'}}`。所以"边框样式叫大圆角、装饰是星星"这个说法的出处是接口注释，而实现从来没做到过，因为 `borders.yaml` 里根本没有以风格命名的边框条目。引用这段示例时，需要说明取的是哪一份文档。

这条路径的采样是随机的，同一实例连跑四次得到三种色系（奶油、珊瑚粉、薄荷绿、奶油），`_get_recent_values()` 会排除该实例内最近 2 个不同的取值，所以短期内不重复；而 `CrossDomainGenerator.__init__` 只构造一次 `DesignVariableBridge`，历史挂在实例上，进程一换就清零。

设计变量库的规模也值得按文件重算一次。`colors.yaml` 是 2 种风格各 5 个色系，共 10 个色系，但 `_sample_colors()` 会跳过名字含"文字"和"背景"的那两类，实际可用 8 个色系、32 个颜色变体。全库变体总数正好 37——"37 种配色方案"里的 37 是颜色条数，不是方案数。`borders.yaml` 每个风格是 `corner_radius` 5 值 × `box_shadow` 3 值 × `border` 2 值 = 30 种组合；`decorations.yaml` 温馨可爱是 5 个元素加 5 个组合、现代简约 4 加 3。只按随库发行的 YAML 文件算，两风格的组合数是 20×30×10 + 12×30×7 = 8,520。说明文档里"20 万+ 组合"要成立，得把 SQLite 侧的设计元素一并乘进来，而这条乘法在代码里没有任何一处实现。

还有一整层设计资产在这个模式下压根没参与。三层地图里那行 `design-logic/*/`（`warm-cute` 与 `modern-minimal` 两个目录，各一份 `principles.md` 和 `constraints.md`，共 4 个文件）由 `DesignVariableBridge.load_design_logic()` 负责，而那个函数（`core/design_bridge.py:191`）的函数体只有一句注释 `# 这部分可以后续扩展` 和 `return None`；唯一可能调用它的位置在 `:67`，那一行是被注释掉的。逐个传 `温馨可爱`、`现代简约`、`warm-cute`、`modern-minimal` 四种名字进去，返回的全是 `None`。这四份文件在 README 与 `README_v2.0.md` 里被介绍过，在代码里没有任何读取方。

## 数字对照表

| 说法 | 可复算口径 | 差距出在哪 |
|------|-----------|-----------|
| 12 个 Skill | 12 个目录（另有 1 个 `learner.md`，曾被数成 13） | 一致 |
| 1,246 个元素 | 1,246 | 一致 |
| 1100+ 元素（`claude.md:282`） | 同一份库 1,246 | 入口文件与 README 各存一份计数 |
| 675 条语料 | 675 | 一致 |
| portrait 502 个 | 502，占 40.3% | 一致 |
| 12 个领域 | `elements` 用 12 个；`domains` 表 8 行；建库代码种 7 行 | 登记表未跟随数据 |
| 领域 5 个（`domain-classifier` 第 3 行） | 同一文件第 18 行写 `7大领域定义`，列了 7 个 | 一份说明文件的头与正文不一致 |
| 跨域可用 995 个（79.9%） | 查询计划候选 306，自动路径 286（23.0%） | 995 是五个领域存量之和，不是可达量 |
| 37 种配色方案 | 10 个色系 / 37 个颜色变体，采样可用 8 个色系 | 把颜色条数当成了方案数 |
| 20 万+ 组合 | 随库 YAML 自身 8,520 | 乘法未实现，出处只有 README |
| 待处理 429 条 | completed 246 / metadata_only 288 / pending 141 | 两种"未完成"性质不同 |
| 语料按类别 163/112/82/65/7 | `theme` 为自由文本（627 个值、46 行空）；可复算的是 `primary`：design 321 / portrait 183 / creative 64 … | 库里没有这套分类 |
| 260+ 位创作者 | 库内无创作者字段 | 无法从发行物复核 |
| 完整的 Skills 系统 | 4 个技能目录加 `learner.md` 的命令指向 `.gitignore` 排除的脚本 | 说明书齐全，实现是其子集 |
| 双轨制之模板级生成 | `design_templates` 有 5 行数据在册但无代码读取；`design-logic/` 4 个文件由一个 `return None` 的桩函数"负责" | 能力只在文档层 |
| 学习闭环持续积累 | `universal-learner` 是 Markdown 指令；写统计的 `save_generated_prompt()` 无调用点；批处理学习脚本全在 `.gitignore` 里 | 通路留在文档与忽略文件中 |
| MIT | README 一处声明，无 LICENSE 文件 | GitHub 的 license 字段为 null |

偏差的原因分三类。**登记表没跟随数据**：领域计数、类别计数、外键指向的 4 个孤立值，改一次重算脚本就能收敛。**统计口径换了问题**：995、37、20 万这三个数各自回答的是"存了多少"而不是"能用到多少"，要修的是措辞。**能力只存在于文档层**：模板级生成、创作者来源、学习闭环，引擎里没有对应实现。第三类最实质——它意味着"这套系统是 Skills 系统而不是 Python 工具"这句话不只是定位修辞，引擎确实没有那部分代码，而技能层也没有把自己依赖的脚本一起交出来。

## 采用建议与可抄的部分

不建议把它当现成服务接进生产链路。三个入口各跑一遍的结果已经说明输出质量不可控：风格搜索不分领域，所以人像里会混进室内材质；13 组固定查询有 7 组不带过滤，所以用户给的年龄与妆容会被高分记录顶掉；`name` 全等守卫会让推导出来的眼型与发色静默落空；`mode='auto'` 又让一半以上元素写好的模板根本不参与拼接。这四条没有一条会报错。

值得抄的是五件结构上的事：

**把元素做成带溯源的记录，而不是提示词片段集合。** `elements` 一行同时挂 `keywords`、`source_prompts`（JSON 数组）、`learned_from`、`metadata`，即便 `learned_from` 已经写成 18 种自由文本，"每条素材能查到自己从哪来"这个骨架是对的，也是这类知识库最先要定型的一件事。

**用 `reusability_score` 之类先验分做截断，用相关性做重排。** 这个两阶段思路本身站得住，只是这里实现成了"先按质量截断 30 条再算相关性"，把召回锁死在质量前 30 名内。把两阶段的顺序倒过来（先按关键词召回，再在召回集里按质量排）是同一份代码上的改动。

**声明式规则文件。** `prompt_framework.yaml` 那 7 类 25 字段、3 条依赖、2 条校验的分离方式是干净的：字段有 `db_category` 指向库、有 `search_keywords` 给出同义词表。它的问题不在表达，而在求值器只实现了表达能力的一个子集（见前文标量分支），而且没有一条规则级测试。声明式框架需要配套一组"给一条规则和一个输入，断言输出"的表驱动测试，否则规则作者写完就不知道它在不在工作。

**检索用的标签和要拼出去的文案不要放在同一行里。** 这个仓库把两件事塞进了 `elements` 的一张表：`keywords` 供检索、`ai_prompt_template` 供拼接。`mode='auto'` 那条 `len(keywords) > 2` 的规则一执行，供拼接的那一列就被供检索的那一列的前三项取代，53.8% 的元素文案因此永远不出场。如果这两列各自有用，拼接时就该只用模板列，标签只用于打分与去重；把它们做成互斥的两条路径，等于让写入方永远猜不到哪一条会生效。

**同一份资产两个运行时的零成本移植。** `.claude` 与 `.codex` 逐字节相同说明一件事：只要技能文件里不写平台特有的工具名，跨智能体产品移植可以退化成复制目录。它同时也说明反面——没有生成机制、没有一致性检查，两份副本从下一个补丁开始就会分叉，而现在 `.claude` 与 `.codex` 各有 37 个文件，其中 36 对逐字节相同，剩下那对入口文件差 5 行。

适合直接读它的对象，是要给自家提示词库建结构的人：读表结构、读 `prompt_framework.yaml`、读技能说明里那份字段清单，这三件事的成本不到一小时，而它们是这个仓库里跟运行时无关的部分。

## 出错时先看哪几处

按现象排查，每处都能用一条命令定案。最常见的是两类：生成结果里混进无关领域，以及某个人物属性莫名其妙没出现在提示词里。

**技能让你跑的命令报文件不存在。** 先确认它是否本该存在，而不是自己的路径写错了。以 `learner.py` 为例：

```text
$ git ls-files | grep -x learner.py
$ git check-ignore -v learner.py
.gitignore:141:learner.py	learner.py
```

第一条为空说明没入库，第二条给出是哪条规则把它挡掉的。`prompt_analyzer.py`、`generator_engine.py`、`narrative_prompt_generator.py`、`prompt_tool.py`、`universal_learner.py`、`templates.json` 六条同理会各自命中 `.gitignore` 的 160、151、152、161、166、185 行。这类命令在技能文件里是按"可用"写的，改不动行为，只能改用自己确实存在的入口：`intelligent_generator.py` 和 `core/` 下那五个模块。

**输出读起来像一堆标签而不像描述。** 这是 `compose_prompt()` 的 auto 分支：元素有超过 2 个关键词时，进输出的是 `keywords[:3]`，模板被丢弃。函数自己的说明列了 `'simple'`、`'auto'`、`'detailed'` 三种模式，想避开这条规则会先去试 `simple`——而它一调就抛：

```text
>>> g.compose_prompt(elements, mode='simple')
UnboundLocalError: cannot access local variable 'text_list' where it is not
associated with a value
```

原因是 `mode == 'simple'` 那一支只给 `text` 赋值，`text_list` 从未初始化，紧接着的 `if text_list:` 在第一个元素上就炸。三种模式实际可用的只有两种，而说明里三者是平列的。

想确认某条元素会不会被顶掉，直接问它的关键词个数：

```text
$ sqlite3 extracted_results/elements.db \
    "select element_id, json_array_length(keywords) from elements \
     where element_id='portrait_visual_styles_097'"
portrait_visual_styles_097|5
```

5 大于 2，所以它的模板永远不出场。对那 34 行非 JSON 的 `keywords`，同一条命令会报 `Error: stepping, malformed JSON`——报错了反而说明这条元素会走模板分支。

**输出里有与主题无关的材质、栅格、色板片段。** 先确认关键词命中的是哪几个类别：`search_style_elements()` 的 SQL 不带 `domain_id` 条件，去库里按这几个类别名反查即可。

```text
sqlite3 extracted_results/elements.db \
  "select domain_id, count(*) from elements where category_id in \
   ('layouts','color_schemes','typography','wood_finishes') group by 1"
```

**某个按人种或性别推导出的属性没出现。** 查 `name` 全等有没有命中：把 `almond`、`black` 换成你那个值。返回 0 就说明这个值在库里只以多词形式存在，守卫会把它判空。

**校验一路在报，改时代或人种都不影响结果。** 原因在标量条件那一半：`validate_intent()` 里那个以 `pass` 收尾的分支。把 YAML 对应规则的两个 `when` 项都改写成列表，或是在代码侧打印每个条件的求值结果，都能确认这不是数据问题而是求值器只实现了一半表达能力。

**跨域一次只拿到一两个元素。** 先看你那类输入落到哪个分支（`design_style` / `design_requirement` 会走 design），再确认 `required_domains` 里有没有 design：这条路径不可能有。然后逐个类别槽位看分数是否越过 20 的阈值。

**只有 YAML 里的边框配置改了没效果。** 读 `core/design_bridge.py:142` 取 `radius` 的那两行，和你的配置结构对比：它期待 `radius` 键，`borders.yaml` 给的是 `values` 与 `default`。同一处判断在 `core/yaml_sampler.py:238` 还有一份，改一处不够。

## 下一步读哪几段代码

按"越读越能看清漂移发生在哪一层"排：

1. `element_db.py:150` 的 `_init_domains()` 与 12 张表定义。七行领域清单是全系统领域概念的源头。
2. `prompt_framework.yaml` 全文（389 行）。这是唯一一份三个层次都读得懂的共同契约。
3. `intelligent_generator.py:90` 的 `get_element_by_category()`。守卫、`ORDER BY`、`LIMIT 1` 三个决定都在这 54 行里。
4. `intelligent_generator.py:408` 的 `search_style_elements()`。跨领域捞取与相关性公式在这里。
5. `intelligent_generator.py:749` 的 `compose_prompt()`。标签顶掉模板那条规则、`simple` 分支的 `UnboundLocalError`，都在这一个函数里。
6. `core/cross_domain_query.py:143` 的 `build_query_plan()`。25 组硬编码类别，逐条拿去问库，一小时能核完。
7. `core/yaml_sampler.py` 的 `:88` / `:129` / `:159` 三个 `_sample_*`。同一套"随机挑第二层键"的逻辑作用在三种不同结构上，结果一目了然。

## 五个自测题

1. `domains` 表 8 行、建库代码种 7 行、`elements` 用 12 个领域值。为什么这三件事能长期共存而不报错？
2. 为什么搜 `male` 需要一个 `name` 全等守卫，而 `almond` 却被同一个守卫取空？两者的差别在库的哪一列上？
3. `validate_intent()` 对 `era=modern` 加 `makeup=k_beauty` 报了"古装场景不应该使用现代妆容"。这条 error 是从 `when` 的哪一个条件产生的？
4. "跨域可用 995 个元素"与"查询计划候选 286 个"分别在回答什么问题？如果要一个能对外说的利用率，你需要先固定哪些变量？
5. `.claude/skills` 与 `.codex/skills` 逐字节相同，而 `claude.md:278` 指向一个磁盘上大小写不符的文件名。为什么这个不一致在今天不影响任何功能？

## 参考

- 仓库：<https://github.com/huangserva/skill-prompt-generator>，main 分支 `e951249`
- 说明文档：<https://raw.githubusercontent.com/huangserva/skill-prompt-generator/main/README.md>，以及 `README_v2.0.md`、`UPGRADE_GUIDE_v2.0.md`
- Codex 适配：第 5 号合并请求，提交 `d8c0948`（2026-01-25）合入 `bd3a491`（2026-04-26）
- 引擎：`intelligent_generator.py`、`framework_loader.py`、`element_db.py`、`core/` 下五个模块
- 数据与声明：`extracted_results/elements.db`、`prompt_framework.yaml`、`variables/` 三份 YAML、`design-logic/` 四份说明
- 本文全部数字与输出取自 2026-09-26 本机一次走查：`git log`、`git ls-files`、`git check-ignore -v`、`sqlite3` 直接查询，以及三个生成入口的实跑日志。运行环境只用 `python3` 加 `pyyaml`，未安装 `anthropic`
