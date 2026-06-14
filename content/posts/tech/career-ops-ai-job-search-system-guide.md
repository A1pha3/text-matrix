+++
date = '2026-04-30T11:30:00+08:00'
draft = false
title = 'Career-Ops：用 AI 打造智能化求职流水线'
slug = 'career-ops-ai-job-search-system-guide'
description = 'Career-Ops 是基于 Claude Code 的 AI 求职系统，涵盖 14 种技能模式、Go Dashboard、PDF 生成、批量处理与多平台支持，让求职者用 AI 对抗 AI 筛选。'
categories = ['技术笔记']
tags = ['AI', 'Claude', '自动化', '求职']
+++

# Career-Ops：用 AI 打造智能化求职流水线

> **项目地址：** [santifer/career-ops](https://github.com/santifer/career-ops) · MIT · 创建于 2026-04-04
> **官方主页：** [career-ops.org](https://career-ops.org) · **Discord：** [discord.gg/8pRpHETxa4](https://discord.gg/8pRpHETxa4)

## 一、项目背景与核心定位

Career-Ops 诞生于一次真实的求职经历。作者 Santiago 在经历数月的海投之后，厌倦了手动管理电子表格、反复调整简历、被低质量职位浪费时间的恶性循环。于是他决定：**用 AI 来对抗 AI 筛选**，打造一套完整的求职自动化流水线。

该系统最终帮助 Santiago 评估了 740+ 个职位，生成了 100+ 份定制化简历，并成功拿下 Head of Applied AI 职位。整个系统以开源方式发布。

Career-Ops 的核心哲学：

> 公司用 AI 过滤候选人 → 候选人用 AI 来挑选公司。

系统并非「撒网式群发工具」，而是一个**高质量过滤器**——帮助用户从成百上千个职位中，快速筛选出真正值得投入时间的少数 offer。系统内置规则：**评分低于 4.0/5 的职位，系统会明确建议放弃申请**，避免浪费用户和招聘方双方的时间。

**重要约束：** 系统设计上，**AI 永远不自动提交申请**。所有内容（简历、cover letter、申请答案）均由 AI 生成，最终决策权始终在用户手中。

---

## 二、系统架构总览

### 2.1 技术栈

| 层次 | 技术选型 | 职责 |
|------|----------|------|
| **AI Agent** | Claude Code / OpenCode / Gemini CLI | 核心推理、模式判断、内容生成 |
| **PDF 生成** | Playwright + HTML 模板 | ATS 优化的简历 PDF |
| **职位扫描** | Playwright + Greenhouse/Ashby/Lever API | 批量抓取职位信息 |
| **数据存储** | Markdown + YAML + TSV | 追踪器、报告、配置 |
| **Dashboard** | Go + Bubble Tea + Lipgloss | 终端可视化流水线 |
| **脚本引擎** | Node.js (ESM 模块 .mjs) | 自动化任务编排 |

### 2.2 完整工作流

```
用户粘贴职位 URL 或描述
        │
        ▼
┌──────────────────────────┐
│   原型检测（Archetype）   │  →  判定角色属于 6 大原型之一
└────────────┬─────────────┘
             │
┌────────────▼─────────────┐
│   A-G 七区块评估         │  →  角色摘要 / CV匹配 / 级别策略 / 薪酬研究 / 个性化方案 / 面试故事 / 合法性验证
└────────────┬─────────────┘
             │
    ┌────────┼────────┐
    ▼        ▼        ▼
 报告.md   PDF.pdf  tracker.tsv
    │        │        │
    └────────┴────────┘
              │
       data/pipeline.md
       data/applications.md
```

### 2.3 项目目录结构

```
career-ops/
├── CLAUDE.md                    # Agent 指令集（最核心的系统说明）
├── cv.md                        # 用户简历（用户创建，格式 markdown）
├── article-digest.md            # 用户成就亮点（可选）
│
├── config/
│   └── profile.example.yml      # 用户配置模板
│
├── modes/                       # ★ 14 种技能模式（核心）
│   ├── _shared.md               # 共享上下文（系统层）
│   ├── _profile.md              # 用户个性化配置（用户层）
│   ├── oferta.md                # 单个职位评估（A-F 评分）
│   ├── ofertas.md               # 多职位对比排名
│   ├── pdf.md                   # PDF 简历生成
│   ├── scan.md                  # 职位门户扫描
│   ├── batch.md                 # 批量并行处理
│   ├── tracker.md               # 申请状态总览
│   ├── apply.md                 # 填写申请表单（AI 辅助）
│   ├── pipeline.md              # 处理待办 URL 队列
│   ├── contacto.md              # LinkedIn 外联消息
│   ├── deep.md                  # 深度公司调研
│   ├── training.md              # 课程/证书评估
│   ├── project.md               # 作品集项目评估
│   ├── patterns.md              # 拒绝模式分析
│   ├── followup.md              # 跟进提醒
│   ├── interview-prep.md        # 面试专项准备
│   ├── auto-pipeline.md         # 全自动流水线（URL → 全部产出）
│   └── latex.md                 # LaTeX 格式简历导出
│
│   ├── de/                      # 德国市场专用模式（DACH 词汇）
│   ├── fr/                      # 法语市场专用模式
│   └── ja/                      # 日语市场专用模式
│
├── batch/
│   ├── batch-prompt.md           # 批量 worker 的完整 prompt
│   └── batch-runner.sh           # 批量调度脚本
│
├── dashboard/                   # Go TUI 可视化仪表盘
│   ├── main.go                  # 入口
│   └── internal/
│       ├── data/                # 数据解析（applications.md / reports/）
│       ├── model/               # 数据模型
│       ├── theme/               # 主题（Catppuccin Mocha）
│       └── ui/screens/          # UI 界面（Bubble Tea）
│
├── templates/
│   ├── cv-template.html          # ATS 优化简历 HTML 模板
│   ├── cv-template.tex          # LaTeX/Overleaf 模板
│   └── states.yml               # 标准申请状态定义
│
├── generate-pdf.mjs             # Playwright HTML → PDF 转换
├── scan.mjs                     # 零 token 职位扫描（直接调 API）
├── update-system.mjs            # 系统自动更新检查
│
├── docs/                        # 完整文档（SETUP / 定制化 / 架构）
├── examples/                    # 示例文件
├── fonts/                       # Space Grotesk + DM Sans 字体
│
├── .claude/                     # Claude Code 技能定义
│   └── skills/career-ops/
├── .opencode/commands/          # OpenCode 斜杠命令
└── .gemini/commands/            # Gemini CLI 斜杠命令
```

---

## 三、核心概念：AI 原型（Archetypes）系统

### 3.1 六大原型分类

Career-Ops 不做泛化的「职位匹配」，而是将所有 AI 相关职位分为**六大原型**，每个原型对应不同的评估侧重点和 CV 定制策略：

| 原型 | 主题方向 | 核心能力 | CV 重点 |
|------|----------|----------|----------|
| **AI Platform / LLMOps Engineer** | 评估、观测、可观测性、可可靠性、流水线 | 建立生产级 AI 系统的指标与闭环质量 | article-digest.md + cv.md |
| **Agentic Workflows / Automation** | HITL（人机回环）、工具编排、多智能体 | 构建可靠的多智能体系统 | article-digest.md + cv.md |
| **Technical AI Product Manager** | GenAI/Agents、PRD、需求发现 | 将业务需求翻译为 AI 产品 | cv.md + article-digest.md |
| **AI Solutions Architect** | 超自动化、企业级、集成 | 设计端到端 AI 架构 | article-digest.md + cv.md |
| **AI Forward Deployed Engineer** | 客户端交付、快速交付、原型到生产 | 快速向客户交付 AI 解决方案 | cv.md + article-digest.md |
| **AI Transformation Lead** | 变革管理、采纳增强、组织变革 | 领导企业级 AI 变革 | cv.md + article-digest.md |

### 3.2 原型如何影响评估

每个原型会调整以下内容：

- **Block B（CV 匹配）：** 优先展示与原型最相关的项目经历和技能
- **Block E（个性化方案）：** 根据原型决定对简历和 LinkedIn 的修改优先级
- **Block F（面试故事）：** STAR+R 故事的选择和叙述框架
- **Block C（级别策略）：** 不同的「升 Senior」话术和谈判策略

**自适应包装策略：** 所有原型共享一个核心叙事——「技术型建设者」（Technical Builder），只是根据目标职位调整包装方式：

- 面向 PM 时：*「通过原型降低不确定性，然后以工程纪律推进生产的建设者」*
- 面向 FDE 时：*「从第一天起就以可观测性和指标驱动快速交付的建设者」*
- 面向 SA 时：*「在真实集成经验基础上设计端到端系统的建设者」*

---

## 四、七区块评估体系（A-G）深度解析

### 4.1 区块总览

```
Block A — 角色摘要（Role Summary）
Block B — CV 匹配（CV Match）
Block C — 级别与策略（Level & Strategy）
Block D — 薪酬与需求（Comp & Demand）
Block E — 个性化方案（Personalization Plan）
Block F — 面试计划（Interview Plan）
Block G — 职位真实性（Posting Legitimacy）
```

### 4.2 Block A — 角色摘要

提取职位描述的核心信息，结构化输出为表格：

| 字段 | 内容 |
|------|------|
| 原型 | 检测到的角色原型 |
| Domain | platform / agentic / LLMOps / ML / enterprise |
| Function | build / consult / manage / deploy |
| Seniority | L3~L8 或对应级别 |
| Remote | full-remote / hybrid / onsite |
| Team size | 团队规模（若提及）|
| TL;DR | 一句话总结 |

### 4.3 Block B — CV 匹配

核心步骤：读取 `cv.md`，将 JD 的每个需求精确映射到简历中的具体行。

**对于每个要求：**
1. 指出匹配行（或 i18n.ts 中的键）
2. 若存在差距，给出缓解策略（gap 是硬性要求还是加分项？候选人有无相邻经验？作品集能否覆盖？）

**按原型调整优先级：**
- FDE → 突出快速交付和客户对接经验
- SA → 突出系统设计和集成能力
- LLMOps → 突出 evals、可观测性和生产强化经验
- Agentic → 突出多智能体编排和人机回环设计

### 4.4 Block C — 级别与策略

**两个策略路径：**

**「卖 Senior 但不撒谎」路线：**
- 针对目标职位，列出候选人在该原型下天然对应的级别
- 准备具体成就话术，将创始人经历包装为优势
- 如何将 founder 经验定位为加分项而非劣势

**「被 downlevel 后的应对」路线：**
- 若薪酬合理，接受降级
- 谈判 6 个月后评审
- 明确晋升标准

### 4.5 Block D — 薪酬与需求

使用 WebSearch 查询真实薪酬数据（Glassdoor、Levels.fyi、Blind 等），输出：

| 公司 | 职位 | 薪酬范围 | 来源 |
|------|------|----------|------|
| ... | ... | ... | ... |

**注意：** 若无可靠数据，明确说明而非捏造数字。

### 4.6 Block E — 个性化方案

针对该职位，对简历和 LinkedIn 各提出 **Top 5 修改建议**，以表格形式呈现：

| # | 位置 | 当前状态 | 建议修改 | 原因 |
|---|------|----------|----------|------|
| 1 | Summary | ... | ... | ... |

### 4.7 Block F — 面试计划（STAR+R）

这是 Career-Ops 最具特色的功能之一——**面试故事银行（Story Bank）**。

系统会从历史评估中积累 5~10 个**主故事**（Master Stories），每个故事格式为：

| 列 | 说明 |
|----|------|
| **S**（Situation） | 背景情境 |
| **T**（Task） | 具体任务 |
| **A**（Action） | 采取的行动 |
| **R**（Result） | 最终结果 |
| **Reflection** | 学到的教训或改进方向 |

> **Reflection 列是 seniority 的信号：** 初级候选人描述发生了什么，高级候选人提取教训。AI 会根据这一列判断候选人的成熟度。

**故事银行工作流：**
1. 每次评估新职位时，从现有故事库中选择最相关的 6~10 个
2. 若缺少覆盖某个 JD 要点的故事，**自动建议创作新故事**并追加到 `interview-prep/story-bank.md`
3. 随着使用，故事库越来越丰富，几乎可以回答任何行为面试问题

### 4.8 Block G — 职位真实性评估（Posting Legitimacy）

这是防止用户在「幽灵职位」上浪费时间的机制。系统从 5 个维度评估职位真实性：

| 评估维度 | 分析内容 |
|----------|----------|
| **发布新鲜度** | 发布日期、申请按钮状态（活跃/关闭/重定向）|
| **描述质量** | 技术细节具体性、团队规模、薪酬范围、职位特定内容占比 |
| **公司招聘信号** | 裁员历史、招聘冻结公告（通过 WebSearch）|
| **重发检测** | 通过 scan-history.tsv 检测公司是否反复发布相似职位 |
| **市场背景** | 该类职位正常招聘周期（政府/学术/高管职位时间线更长）|

**三级评估结论：**

- **High Confidence** — 多重信号指向真实活跃职位
- **Proceed with Caution** — 混合信号，值得注意
- **Suspicious** — 多个幽灵职位指标，建议投资前进一步调查

> **伦理原则：** 系统仅呈现观察结果，不做指控。每个信号都有合理解释。用户自行决定如何权衡。

---

## 五、14 种技能模式全景

### 5.1 模式速查表

| 模式 | 文件 | 功能 | 触发场景 |
|------|------|------|----------|
| **oferta** | `oferta.md` | 单个职位 A-G 评估 | 「帮我评估这个职位」「这个 JD 怎么样」 |
| **ofertas** | `ofertas.md` | 多职位对比排名 | 「对比一下这三个 offer」 |
| **pdf** | `pdf.md` | 生成 ATS 优化 PDF 简历 | 「生成一份简历 PDF」 |
| **latex** | `latex.md` | 导出 LaTeX/Overleaf 格式 | 「给我 Overleaf 版本」 |
| **scan** | `scan.md` | 扫描门户寻找新职位 | 「扫一下有没有新职位」 |
| **batch** | `batch.md` | 并行批量评估 | 「批量处理这 20 个职位」 |
| **tracker** | `tracker.md` | 查看申请状态总览 | 「我现在申请进度怎么样了」 |
| **apply** | `apply.md` | AI 辅助填写申请表单 | 「帮我填这个申请表」 |
| **pipeline** | `pipeline.md` | 处理待办 URL 队列 | 「处理一下 pipeline 里的职位」 |
| **contacto** | `contacto.md` | LinkedIn 外联消息 | 「帮我写一封 recruiter 的消息」 |
| **deep** | `deep.md` | 深度公司调研 | 「深度调研一下这家公司」 |
| **training** | `training.md` | 课程/证书评估 | 「这个 AI 证书值不值得考」 |
| **project** | `project.md` | 作品集项目评估 | 「这个项目想法怎么样」 |
| **patterns** | `patterns.md` | 拒绝模式分析 | 「为什么我总被拒？有什么规律」 |
| **followup** | `followup.md` | 跟进提醒 | 「我应该什么时候 follow up」 |
| **interview-prep** | `interview-prep.md` | 公司专项面试准备 | 「准备一下 Stripe 的面试」 |
| **auto-pipeline** | `auto-pipeline.md` | 全自动流水线（URL → 全部产出）| 粘贴任意职位 URL，系统自动跑完整个流程 |

### 5.2 核心模式详解

#### `auto-pipeline` — 全自动流水线

粘贴任意职位 URL 或 JD 文本，系统自动：
1. 获取职位描述
2. 检测原型
3. 执行 A-G 评估
4. 生成 PDF 简历
5. 更新 tracker

**零人工干预**，一行命令搞定完整流程。

#### `batch` — 并行批量处理

使用 `claude -p` 启动多个 worker 子进程，并行评估 10+ 个职位：

```
batch/batch-prompt.md  ← 自包含 worker prompt（内置所有评估逻辑）
batch/batch-runner.sh  ← 调度脚本
batch/tracker-additions/{num}-{company-slug}.tsv  ← 每个 worker 输出一个 TSV 行
```

**TSV 格式（9 列，严格顺序）：**

```
序号 | 日期 | 公司 | 职位 | 状态 | 评分 | PDF | 报告链接 | 备注
```

**合并流程：** 每次批量评估后，运行 `node merge-tracker.mjs` 合并所有 TSV，避免重复条目。

#### `scan` — 零成本职位扫描

`scan.mjs` 不依赖 LLM token，直接调 **Greenhouse / Ashby / Lever API** 批量查询职位，支持：

- **45+ 预配置公司**（Anthropic、OpenAI、Mistral、Cohere、ElevenLabs、Retool、n8n 等）
- **19 种搜索查询** 覆盖 Ashby、Greenhouse、Lever、Wellfound、Workable、RemoteFront
- **扫描历史去重**（scan-history.tsv 记录已扫过的公司+职位组合）

---

## 六、PDF 生成技术原理

### 6.1 工作原理

Career-Ops 的 PDF 生成流程：

```
HTML 模板（cv-template.html）
    + 动态内容注入
    ↓
Playwright (Chromium headless)
    ↓
normalizeTextForATS()  ← ATS 兼容性处理
    ↓
PDF 输出（output/）
```

### 6.2 ATS 兼容性处理

ATS（Applicant Tracking System）解析器对特殊字符处理极差，`generate-pdf.mjs` 内置了 `normalizeTextForATS()` 函数，对正文文本进行以下转换：

| 问题字符 | 处理方式 |
|----------|----------|
| em-dash（—）| → 替换为 `-` |
| en-dash（–）| → 替换为 `-` |
| 智能引号（" '）| → 替换为 ASCII 引号 |
| 省略号（…）| → 替换为 `...` |
| 零宽字符 | → 全部删除 |
| 不间断空格（\u00A0）| → 替换为空格 |

**关键点：** CSS、JS、URL 和 HTML 标签属性**不受影响**，仅处理正文文本内容。

### 6.3 使用方式

```bash
# 基础用法
node generate-pdf.mjs input.html output.pdf

# 指定纸张格式
node generate-pdf.mjs input.html output.pdf --format=letter
node generate-pdf.mjs input.html output.pdf --format=a4
```

### 6.4 双模板支持

Career-Ops 提供两套简历模板：

| 模板 | 用途 | 技术 |
|------|------|------|
| `cv-template.html` | 数字申请 + ATS | Playwright → PDF |
| `cv-template.tex` | Overleaf / LaTeX 用户 | LaTeX 编译器 |

---

## 七、Go Dashboard TUI — 流水线可视化

### 7.1 技术选型

Dashboard 使用纯 **Go** 构建，核心依赖：

| 库 | 作用 |
|----|------|
| **Bubble Tea** | 构建终端 TUI 的 Elixir 风格框架 |
| **Lipgloss** | 终端样式库（颜色、边框、布局）|
| **Catppuccin Mocha** | 暗色主题配色 |

### 7.2 构建与运行

```bash
cd dashboard
go build -o career-dashboard .
./career-dashboard --path ..    # 指定 career-ops 根目录
```

### 7.3 功能特性

| 功能 | 说明 |
|------|------|
| **6 个过滤器标签页** | 按状态、公司、评分等维度过滤 |
| **4 种排序模式** | 按评分/日期/公司/状态排序 |
| **分组/平铺视图切换** | 结构化或扁平化展示 |
| **懒加载预览** | 点击条目时按需加载报告摘要 |
| **内联状态修改** | 在 TUI 内直接更新申请状态 |
| **富报告查看器** | 在 TUI 内直接阅读完整评估报告 |

### 7.4 核心架构

```go
// main.go — 顶层状态机
type viewState int
const (
    viewPipeline viewState = iota   // 主列表视图
    viewReport                       // 报告查看器
    viewProgress                     // 进度统计视图
)

type appModel struct {
    pipeline        screens.PipelineModel  // 列表模型
    viewer          screens.ViewerModel    // 报告查看模型
    progress        screens.ProgressModel   // 进度模型
    careerOpsPath   string                  // career-ops 根目录
    theme           theme.Theme             // Catppuccin 主题
}
```

数据层通过读取 `career-ops/data/applications.md` 解析申请记录，并从 `reports/` 目录按需加载评估报告。状态更新通过 `data.UpdateApplicationStatus()` 写入文件。

---

## 八、多 AI 平台支持

Career-Ops 实现了对三大主流 AI Coding CLI 的完整支持，核心逻辑（modes/*.md）三者共享。

### 8.1 Claude Code

```bash
claude    # 在 career-ops 目录启动

# 使用斜杠命令
/career-ops "粘贴职位描述..."
/career-ops oferta
/career-ops scan
```

### 8.2 OpenCode

```bash
opencode
```

支持 15 个斜杠命令（`.opencode/commands/`），与 Claude Code 的 `/career-ops-*` 命令一一对应：

| OpenCode 命令 | Claude Code 等效 |
|---------------|------------------|
| `/career-ops` | `/career-ops` |
| `/career-ops-evaluate` | `/career-ops oferta` |
| `/career-ops-compare` | `/career-ops ofertas` |
| `/career-ops-pdf` | `/career-ops pdf` |
| `/career-ops-scan` | `/career-ops scan` |
| `/career-ops-batch` | `/career-ops batch` |
| `/career-ops-tracker` | `/career-ops tracker` |
| `/career-ops-apply` | `/career-ops apply` |
| `/career-ops-pipeline` | `/career-ops pipeline` |
| `/career-ops-contact` | `/career-ops contacto` |
| `/career-ops-deep` | `/career-ops deep` |
| `/career-ops-training` | `/career-ops training` |
| `/career-ops-project` | `/career-ops project` |
| `/career-ops-patterns` | `/career-ops patterns` |
| `/career-ops-followup` | `/career-ops followup` |

### 8.3 Gemini CLI

两种使用方式：

**方式 A（推荐）：原生 CLI**

```bash
npm install -g @google/gemini-cli
gemini auth        # 免费 OAuth 认证
cd career-ops
gemini             # 启动后自动加载 GEMINI.md 上下文

# 同样的斜杠命令
/career-ops "Senior AI Engineer at Anthropic..."
/career-ops-evaluate --file ./jds/openai.txt
```

**方式 B：API 脚本（无需安装 CLI）**

```bash
# 1. 获取免费 API key：https://aistudio.google.com/apikey
cp .env.example .env
# 编辑 .env → GEMINI_API_KEY=your_key_here

# 2. 使用 API
node gemini-eval.mjs "We are looking for a Senior AI Engineer..."
node gemini-eval.mjs --file ./jds/my-job.txt
```

> **免费层级：** 两种方式均可免费使用（原生 CLI 用 Google OAuth；API 脚本用 `gemini-2.0-flash`：15 RPM、每天 100 万 tokens 免费额度）。

---

## 九、安装与配置

### 9.1 前置条件

| 依赖 | 版本/说明 |
|------|-----------|
| Node.js | ≥ 18.x（.mjs 模块需要）|
| npm | 随 Node.js 附带 |
| Playwright + Chromium | `npx playwright install chromium` |
| Claude Code / OpenCode / Gemini CLI | 至少安装一种 |

### 9.2 快速安装

```bash
# 1. 克隆仓库
git clone https://github.com/santifer/career-ops.git
cd career-ops

# 2. 安装依赖
npm install

# 3. 安装 Playwright（必须，PDF 生成依赖）
npx playwright install chromium

# 4. 验证环境
npm run doctor         # 检查所有前置依赖

# 5. 配置用户信息
cp config/profile.example.yml config/profile.yml
# 编辑 config/profile.yml

# 6. 添加简历
# 在项目根目录创建 cv.md（Markdown 格式简历）

# 7. 配置职位扫描
cp templates/portals.example.yml portals.yml
# 编辑 portals.yml（可选，预配置 45+ 公司）
```

### 9.3 首次启动引导

若检测到必要文件缺失，系统会引导用户逐步完成配置：

```
Step 1: 简历 → 创建 cv.md
Step 2: 配置 → 创建 config/profile.yml
Step 3: 扫描 → 创建 portals.yml
Step 4: 追踪器 → 创建 data/applications.md
Step 5: 了解用户 → 收集职业目标、独门优势、禁忌等
Step 6: 确认就绪 → 展示可用命令
```

**系统会在每次新会话自动检查更新：**

```bash
node update-system.mjs check
# 输出示例：{"status": "up-to-date"} 或
# {"status": "update-available", "local": "1.0.0", "remote": "1.1.0", "changelog": "..."}
```

### 9.4 多语言模式

除默认英文外，还支持三个本地化市场：

| 市场 | 目录 | 特色 |
|------|------|------|
| **德国（DACH）** | `modes/de/` | 13. Monatsgehalt、Probezeit、Kündigungsfrist、AGG |
| **法国** | `modes/fr/` | CDI/CDD、SYNTEC 集体协议、RTT、mutuelle、intéressement |
| **日本** | `modes/ja/` | 正社員、業務委託、賞与、退職金、みなし残業、年俸制 |

**触发方式：** 在 `config/profile.yml` 设置 `language.modes_dir: modes/ja`，或直接在对话中告诉 AI「使用日语模式」。

---

## 十、流水线完整性保障

Career-Ops 在数据层实现了严格的完整性约束，防止追踪数据出现重复、混乱：

### 10.1 数据合同（双层架构）

| 层级 | 文件 | 规则 |
|------|------|------|
| **用户层**（永不自动覆盖）| `cv.md`、`config/profile.yml`、`modes/_profile.md`、`article-digest.md`、`portals.yml`、`data/*`、`reports/*` | 系统更新不会覆盖用户数据 |
| **系统层**（可自动更新）| `modes/_shared.md`、`CLAUDE.md`、`*.mjs`、`dashboard/*` | 系统更新时安全覆盖 |

**黄金法则：** 用户个性化内容（原型映射、目标职位偏好、谈判话术）永远写入 `modes/_profile.md` 或 `config/profile.yml`，**绝不**写入 `modes/_shared.md`。

### 10.2 TSV → 合并流程

批量评估时，每个 worker 产生一个独立 TSV 文件：

```
batch/tracker-additions/
├── 001-openai-2026-04-30.tsv
├── 002-anthropic-2026-04-30.tsv
└── 003-cohere-2026-04-30.tsv
```

评估结束后运行：

```bash
node merge-tracker.mjs
```

自动合并所有 TSV，去重（`公司+职位` 唯一键），输出到 `data/applications.md`。

### 10.3 管道健康检查

```bash
node verify-pipeline.mjs       # 验证数据完整性
node normalize-statuses.mjs    # 标准化所有状态值
node dedup-tracker.mjs         # 去除重复条目
```

---

## 十一、开发与扩展

### 11.1 系统层可定制项

Career-Ops 设计上鼓励用户通过 AI 直接修改，常见的定制需求：

| 需求 | 修改文件 |
|------|----------|
| 「把原型改成数据工程方向」| `modes/_profile.md` 或 `config/profile.yml` |
| 「把模式翻译成英文」| 编辑 `modes/` 下所有文件 |
| 「添加我的目标公司」| `portals.yml` |
| 「修改评分权重」| `modes/_shared.md`（系统默认）或 `modes/_profile.md`（用户偏好）|
| 「修改简历模板设计」| `templates/cv-template.html` |
| 「修改谈判脚本」| `modes/_shared.md` |

### 11.2 添加自定义技能模式

创建新模式只需在 `modes/` 下新建 `.md` 文件，例如 `modes/salary-negotiation.md`，在 `CLAUDE.md` 的模式路由表中添加映射即可：

```markdown
| 询问薪资谈判 | `salary-negotiation` |
```

### 11.3 CI/CD 与质量保障

| 检查项 | 说明 |
|--------|------|
| **测试套件** | `test-all.mjs`（63+ 项检查）|
| **PR 标签机器人** | 基于风险自动打标签（🔴core-architecture / ⚠️agent-behavior / 📄docs）|
| **分支保护** | main 分支必须通过 CI 才能合并 |
| **Dependabot** | 自动监控 npm / Go / GitHub Actions 安全更新 |

### 11.4 社区与治理

| 方面 | 说明 |
|------|------|
| **许可证** | MIT |
| **Discord** | [discord.gg/8pRpHETxa4](https://discord.gg/8pRpHETxa4) |
| **行为准则** | Contributor Covenant 2.1 |
| **治理模式** | BDFL（作者 Santiago 主导）+ 贡献者阶梯 |
| **安全漏洞** | 私下报告至 hi@santifer.io |

---

## 十二、实战演示

### 场景：评估一个职位（完整流程）

```bash
# 1. 启动 Claude Code
cd career-ops
claude

# 2. 粘贴职位 URL，系统自动识别并启动全流水线
#（或直接输入）
/career-ops https://boards.greenhouse.io/anthropic/jobs/xxxxx

# 3. 系统输出：
#   ✓ 原型检测 → AI Platform / LLMOps Engineer
#   ✓ A-G 评估报告 → reports/001-anthropic-2026-04-30.md
#   ✓ ATS 优化 PDF → output/cv-001-anthropic-2026-04-30.pdf
#   ✓ 追踪器更新 → data/applications.md

# 4. 查看结果
./career-dashboard --path .    # 启动 Go TUI
```

### 场景：批量评估 10 个职位

```bash
# 1. 准备批量输入文件
# jds/
#   ├── 01-openai.txt
#   ├── 02-anthropic.txt
#   └── ...

# 2. 运行批量处理
/career-ops batch jds/

# 3. 系统自动：
#   - 启动 N 个 claude -p worker 进程
#   - 每个 worker 独立评估一个职位
#   - 生成各自的报告 + PDF + TSV

# 4. 合并结果
node merge-tracker.mjs

# 5. 可视化
./career-dashboard --path ..
```

### 场景：扫描目标公司新职位

```bash
# 扫描所有预配置公司的新职位（零 LLM token 成本）
node scan.mjs

# 或通过 Claude
/career-ops scan
```

---

## 十三、总结与评价

Career-Ops 是当前 AI 求职工具领域**工程化程度最高**的开源项目之一。它不是简单地将 LLM 包装成聊天机器人，而是构建了一套完整的**自动化流水线系统**，在多个维度实现了工程级质量：

**核心优势：**

1. **原型驱动的精准匹配** — 6 大原型分类让 AI 每次都能针对具体职位调整评估和包装策略，而非泛化的关键词匹配
2. **七区块结构化评估** — 将职位评估从「感觉差不多」变成有据可查的结构化分析，覆盖从真实性验证到面试故事银行的全链路
3. **多 AI 平台抽象** — Claude Code / OpenCode / Gemini CLI 三平台共用同一套 modes 文件，切换成本极低
4. **零依赖的职位扫描** — scan.mjs 直接调 Greenhouse/Ashby/Lever API，扫描 45+ 公司不花一分 LLM token
5. **Go TUI 仪表盘** — 专业的终端 UI，让流水线状态一目了然
6. **本地优先的数据架构** — 所有用户数据（简历、追踪器、报告）都在本地，不经过任何第三方服务器

**适用人群：**

- AI/ML 领域求职者（尤其是 Engineers、PM、Architect 等角色）
- 希望将求职流程系统化的中级以上专业人士
- 对 AI Coding CLI（Claude Code 等）有一定了解的工程师

**不适用场景：**

- 非 AI 领域职位（系统预置的原型和评分体系高度针对 AI 相关职位）
- 完全不熟悉命令行的用户（需要一定的 CLI 基础）

**相关项目：** 作者的 portfolio 网站 [cv-santiago](https://github.com/santifer/cv-santiago) 也是开源的，可作为配套作品集参考。

---

*本文基于 career-ops v1.x（截至 2026-04-30）编写。最新信息请参考 [GitHub 仓库](https://github.com/santifer/career-ops)。*
