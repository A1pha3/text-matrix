---
title: "Career-Ops：把 AI 编程 CLI 改造成求职指挥中心的开源方案"
date: "2026-07-02T21:02:26+08:00"
lastmod: "2026-07-02T21:02:26+08:00"
draft: false
slug: "santifer-career-ops-ai-job-search-automation-guide"
description: "Career-Ops 把任意 AI 编程 CLI 改造为求职指挥中心，包含 15 个 skill mode、Go TUI 仪表盘、Playwright PDF 与 ATS 渠道扫描，作者用其评估 740+ 岗位后落地 Head of Applied AI。"
categories: ["技术笔记"]
tags: ["AI Agent", "Claude Code", "Playwright", "求职自动化", "Go TUI"]
author: text-matrix
---

## 本文导读

读完本文你将能够：

- 看清 Career-Ops 解决的问题不是「自动投简历」，而是「在大量岗位中筛选出值得投递的那几个」
- 说出 15 个 skill mode 是怎么被一组 `modes/*.md` 文件和 `AGENTS.md` 路由串起来的
- 在 Claude Code / Codex / OpenCode / Gemini CLI 中挑一种完成 `npx @santifer/career-ops init` 启动
- 用 Go TUI 仪表盘浏览、按状态过滤 740+ 个评估记录
- 判断这套工具是否符合你的求职场景与风险偏好

适合读者：正在用 AI 编程 CLI、想把求职流程从 Excel 搬到 AI agent 里的工程师或技术负责人。

---

## 一、先给判断

Career-Ops 不是一个「投递机器人」，它把自己定位成 filter——作者 Santiago 在 README 里把这一点写得很直接：

> This is NOT a spray-and-pray tool. Career-ops is a filter -- it helps you find the few offers worth your time out of hundreds. The system strongly recommends against applying to anything scoring below 4.0/5.

整套系统的设计重心因此放在三件事上：

1. **评估**：用一个 6-block + A-F 评分体系（10 个加权维度）判断岗位与候选人之间的匹配度，而不是用关键词匹配
2. **生成**：基于评估结果按岗位定制 ATS-friendly PDF 简历与 Cover Letter
3. **追踪**：把所有评估、PDF、状态合并到一个数据源上，配合 dedup、归一化、健康检查避免漏投或重复投递

作者本人在「About the Author」里写明：他用这套系统评估了 740+ 岗位、生成 100+ 份定制简历，最后落地了一个 Head of Applied AI 岗位。这不是 marketing copy，是写在 README 里的可追溯案例（[完整 case study](https://santifer.io/career-ops-system)）。

---

## 二、项目地图：哪些东西值得拆开看

Career-Ops 不是一个普通的 Node.js CLI。它把 skill 路由、ATS 抓取、PDF 渲染、状态追踪拆成了若干子系统，下表先列出主要模块和它们各自负责什么：

| 子系统 | 目录 / 文件 | 负责什么 |
| --- | --- | --- |
| 技能路由 | `modes/`（15 个 `*.md`） | 每个 mode 是一个独立 skill：`oferta.md`（单岗评估）/ `pdf.md`（CV 生成）/ `cover.md`（求职信）/ `scan.md`（渠道扫描）/ `batch.md`（批量处理）等 |
| 通用上下文 | `modes/_shared.md` | 所有 mode 共享的指令、状态机、输出格式 |
| 配置文件 | `config/profile.example.yml`、`templates/portals.example.yml` | 候选人信息 + 扫描目标公司列表 |
| 简历输入 | `cv.md`（用户自填） | markdown 形式的候选人简历，被评估与 PDF 生成反复读取 |
| PDF 渲染 | Playwright + `templates/cv-template.html` + `templates/cover-template.html` | 把评估结果按 ATS 友好的版式渲染成 PDF（Space Grotesk + DM Sans） |
| 批处理 | `batch/batch-prompt.md` + `batch/batch-runner.sh` | 启动 headless 工作进程（`claude -p` / `opencode run`）并行评估 |
| 仪表盘 | `dashboard/`（Go + Bubble Tea） | TUI（终端 UI）浏览、过滤、分组 pipeline 状态 |
| 数据层 | `data/`、`reports/`、`output/` | 评估报告、PDF 输出、追踪 TSV，全部 gitignored |
| 扫描器 | `scan.mjs`（Playwright + Greenhouse/Ashby/Lever API） | 跨 19 类查询、45+ 公司抓取新岗位 |
| 法律边界 | `LEGAL_DISCLAIMER.md`、`TRADEMARK.md` | 明确数据归属、禁止垃圾投递、商标策略 |

读源码时，你会发现 `AGENTS.md` 是所有 CLI 的统一入口，`CLAUDE.md` / `CODEX.md` / `OPENCODE.md` / `GEMINI.md` 只是引用它的轻量包装——这种「一个真相源 + 多个薄适配层」的做法，是这套系统能在 8 套不同 AI CLI 之间互通的根因。

---

## 三、15 个 skill mode 是什么

modes/ 目录里有 15 个 markdown 文件，每个就是一个独立的 skill。下面把它们按用途分组，并挑 3 个最值得展开的 mode 做具体说明。

按用途分组：

| 分组 | Mode | 用途 |
| --- | --- | --- |
| 评估 | `oferta.md`、`oferta-loop.md` | 单岗位评估 / 批量多岗评估 |
| 生成 | `pdf.md`、`cover.md` | ATS CV 与求职信 PDF 生成 |
| 扫描 | `scan.md` | 跨 ATS / 公司官网抓取新岗位 |
| 投递 | `apply.md`、`contacto.md` | 自动填表 + LinkedIn 触达话术 |
| 追踪 | `tracker.md`、`pipeline.md` | 看 pipeline 状态、处理待办 |
| 调研 | `deep.md`、`training.md`、`project.md` | 公司深度调研 / 课程评估 / 作品项目评估 |
| 谈判 | `salary.md`、`negotiation.md` | 薪资谈判框架、地理折扣应对、竞争 offer 杠杆 |

具体展开：

1. **oferta.md（核心评估 mode）**：分 6 个 block 评估一个岗位——Role summary、CV match、Level strategy、Comp research、Personalization、Interview prep（STAR+），再加 Block G 做岗位真伪检查，识别骗子岗与 ghost job。最后给出 A 到 F 的总体评分与加权维度拆解。整个评估读 `cv.md` 而非关键词匹配，这点和 LinkedIn Easy Apply 类工具根本不是同一类产物。
2. **scan.md（跨 ATS 扫描）**：自带 45+ 公司（Anthropic、OpenAI、ElevenLabs、Retool、n8n、LangChain、Weights & Biases、Factorial、Travelperk…）和 19 类搜索查询，覆盖 Greenhouse、Ashby、Lever、Wellfound 四种主流 ATS。21 个 provider 模块负责不同数据源（API / XML / RSS / 本地解析）。如果担心 ATS API 返回过期岗位，可以加 `--verify` 让 Playwright 做一次存活校验，把过期条目在进 pipeline 前过滤掉。
3. **batch.md（批处理 mode）**：把岗位列表放进 `data/pipeline.md`，然后 `npm run batch` 启动一个 orchestrator，并行 spawn `claude -p` / `opencode run` 这类 headless 工作进程。每个 worker 拿到自包含 prompt，独立完成评估与 PDF。orchestrator 负责把结果合并、去重、状态归一化。

> 注意：所有 mode 都设计成「AI 给评估与建议、人类决定是否行动」——README 的 human-in-the-loop 段明确写明，系统永远不会替用户投递。这是它的产品定位边界。

---

## 四、快速上手：5 步把 Claude Code 变成求职中心

下面以 Claude Code 为例，演示从零开始的全流程。其他 CLI（Codex / OpenCode / Gemini / Antigravity CLI / Grok Build CLI）的启动命令不同，但目录结构与 mode 名称完全一致。

### Step 1：一行初始化

```bash
npx @santifer/career-ops init
```

这条命令会克隆最新 release 到 `./career-ops` 目录，并安装依赖。它不会做任何全局安装——`npx` 临时下载、用完即丢。Node.js 没装的话先装。

### Step 2：进入目录并启动 Claude Code

```bash
cd career-ops
claude
```

第一次启动时，Claude Code 会自动读取 `CLAUDE.md` → `AGENTS.md` → `modes/_shared.md`，进入 onboarding 对话。它会问你：CV 怎么提供、目标岗位是什么、地理偏好、薪资范围。**所有这些都以对话形式完成，不需要手填 YAML**。

### Step 3：（可选）手动精调

如果你想绕过 onboarding，或者对 onboarding 输出不满意：

```bash
git clone https://github.com/santifer/career-ops.git
cd career-ops && npm install
npx playwright install chromium   # 只在需要 PDF 时跑
npm run doctor                    # 校验前置依赖
cp config/profile.example.yml config/profile.yml
cp templates/portals.example.yml portals.yml
# 在 cv.md 里贴上你的 markdown 简历
```

### Step 4：第一次评估

把一个岗位 URL 或 JD 文本直接粘进 Claude Code 对话框，Career-Ops 会自动识别意图、调用 `oferta.md`、输出评分报告 + PDF + tracker 条目。或者使用 slash 命令：

```text
/career-ops                # 列出所有可用命令
/career-ops <粘贴 JD 文本> # 完整 auto-pipeline
/career-ops scan           # 扫描 portal
/career-ops pdf            # 给最新评估生成 ATS CV
/career-ops cover          # 给最新评估生成求职信
/career-ops tracker        # 看当前 pipeline 状态
```

### Step 5：批处理 + 仪表盘

当你有 10+ 个待评估岗位时：

```bash
# 把 URL 一行一个塞进 data/pipeline.md
npm run batch
npm run serve:dashboard   # 启 TUI 看结果
npm run build:dashboard   # 可选：编成单文件二进制
```

TUI 有 6 个过滤 tab、4 种排序模式、分组/扁平视图、lazy-load 预览、内联改状态——基本是一个 terminal 版 Kanban。

---

## 五、跨 CLI 的设计取舍

Career-Ops 之所以能同时跑在 Claude Code、Codex、OpenCode、Gemini、Antigravity CLI、Grok Build CLI 上，是因为它刻意避开了任何专有 API，转而使用 open standard（`.agents/skills/career-ops/SKILL.md` 作为统一入口）。README 里把它叫做「agent-skill-standard CLI」——只要某个 CLI 实现了这个标准，就能加载同一套 skill 集。

代价是什么？

- Codex 不保证 slash 命令可用，所以 fallback 是用自然语言告诉 Codex「run the career-ops scan mode」——`codex exec "Evaluate this JD with career-ops auto-pipeline: https://..."` 是它的一键入口
- Antigravity CLI 会同时读 `AGENTS.md` 与 `GEMINI.md`，所以仓库里有一个 `GEMINI.md` 的 no-op 兼容守卫，避免上下文被复制粘贴两遍
- Grok Build CLI 的批处理用 `grok -p "prompt" --yolo` 实现（`--yolo` 让它跳过权限确认），针对批量任务做了体验优化

这套设计的代价是：用户必须自己挑选 CLI 并安装，文档里也明确列出了 7 款 CLI 的具体启动方式（见 `docs/SUPPORTED_CLIS.md`）。但好处是——一旦 CLI 厂商涨价或停止维护，迁移到下一个 CLI 几乎不写迁移代码。

---

## 六、风险与边界

这套工具解决的是「求职流程自动化」，但 README 把风险与边界写得很硬：

1. **数据归用户所有**：CV、个人信息全在本地机器上，直接发给用户选的 AI provider（Anthropic、OpenAI 等）。Career-Ops 不托管、不存储、看不到数据
2. **AI 行为不可预测**：默认 prompt 禁止自动投递，但用户改 prompt 或换模型后的行为，作者不承担责任——每次提交前都需要人工 review
3. **第三方 ToS 合规**：Greenhouse / Lever / Workday / LinkedIn 等 ATS 都有 ToS，禁止用本工具做批量投递或绕过限速
4. **AI 可能 hallucinate**：评估是建议，不是事实。模型可能虚构技能或经历，提交前必须人工复核
5. **质量下限**：评分低于 4.0/5 的岗位，系统强烈不建议投递——这不是技术限制，是产品哲学

商业风险也写在了 `TRADEMARK.md`：「career-ops」这个名称与品牌归 Santiago 管，社区允许个人使用，商业产品命名或代言需要单独授权。代码本身是 MIT。

---

## 七、什么场景适合用，什么场景不适合

适合：

- 你已经在用 Claude Code / Codex / OpenCode 之一做日常开发
- 你的求职目标明确（目标公司列表、目标岗位类型、目标地理范围），想批量评估
- 你愿意花 1-2 周把 `cv.md`、`profile.yml`、`portals.yml` 养起来——系统对初始用户了解得越多，评估越准
- 你想保留「投递决策权」在手里，只让 AI 做评估与生成

不适合：

- 你完全没装过 AI CLI、没耐心装 Node.js / Playwright Chromium
- 你想「全自动投递」——这违反本工具的产品定位，也会触发 ATS 反垃圾机制
- 你的目标是不限行业、海投——这种场景下评分系统会变成噪音
- 你对 AI 输出 0 信任、希望 100% 自己写评估——那直接用 Excel 即可

---

## 八、读完能做什么

| 你现在能做的事 | 下一步动作 |
| --- | --- |
| 评估是否值得尝试 | 先 clone 仓库、跑 `npm run doctor`、读 `modes/_shared.md` 看 mode 列表 |
| 启动第一次评估 | `npx @santifer/career-ops init` + `cd career-ops && claude` + 粘贴一个 JD |
| 自定义扫描目标 | 编辑 `portals.yml`，把自己关注的公司加进 `portals` 列表 |
| 跑批处理 | 把 10+ URL 塞 `data/pipeline.md`，跑 `npm run batch` + `npm run serve:dashboard` |
| 切换 CLI | 选 Claude Code / Codex / OpenCode / Gemini 任一种，按 `docs/SUPPORTED_CLIS.md` 启动 |

工具地址：[github.com/santifer/career-ops](https://github.com/santifer/career-ops)，57,365 Stars（今日 +322）。作者案例研究：[santifer.io/career-ops-system](https://santifer.io/career-ops-system)。