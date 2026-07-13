---
title: "coreyhaines31/marketingskills：把 50 个营销技能塞进 Claude Code / Cursor / Codex 的开源技能库"
date: 2026-07-14T03:13:08+08:00
slug: "coreyhaines31-marketingskills-marketing-skill-library"
description: "coreyhaines31/marketingskills 是为 Claude Code、OpenAI Codex、Cursor、Windsurf 等 AI 编码代理准备的 50 个营销技能包（覆盖 CRO、SEO、文案、付费投放、A/B 测试、留存、增长工程、Sales/RevOps 等），遵循 Agent Skills 规范，product-marketing 作为所有技能的前置上下文，安装方式覆盖 npx skills、Claude Code plugin、git submodule、SkillKit 等多种路径。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Claude Code", "Cursor", "Agent Skills", "营销自动化"]
---

## 本文导读

读完本文你将能够：

- 理解 `marketingskills` 是一个 **AI Agent Skills 集合**，不是"营销工具箱"——它由 50 个 markdown 技能文件组成，每个技能告诉代理"遇到这类任务时该按什么框架思考"。
- 看清 `product-marketing` 作为"前置上下文"的依赖关系，以及 50 个技能是如何按 8 大类（转化、文案、SEO、付费、测试、留存、增长、战略、销售）组织的。
- 在 Claude Code / Cursor / Codex / Windsurf 中任选一种方式完成安装，避开 v1.x → v2.0 的 17 个技能重命名坑。
- 判断它和"Notion 营销模板""MCP 营销工具""Prompt 集合"的差异——它是 **可被代理自动识别并触发** 的程序化工作流。
- 知道它的适用边界：技术型营销人 / 创始人自己用代理干活，而不是"用代理替代营销团队"。

适合读者：会自己开 Claude Code / Cursor、想把"营销活儿"系统化塞进代理的 SaaS 创始人、技术型增长负责人、独立开发者。

---

## 一、先给判断：这不是 prompt 集合，而是「让代理自带营销肌肉」的技能库

仓库 `coreyhaines31/marketingskills` 的官方定位非常明确：

> A collection of AI agent skills focused on marketing tasks. Built for technical marketers and founders who want AI coding agents to help with conversion optimization, copywriting, SEO, analytics, and growth engineering. Works with Claude Code, OpenAI Codex, Cursor, Windsurf, and any agent that supports the Agent Skills spec.

把它和"营销相关的 AI 资源"摆在一起看：

| 形态 | 典型代表 | 与 marketingskills 的差异 |
|------|----------|--------------------------|
| Prompt 集合 | GitHub 上各种 `awesome-prompts` | 一次性输入；marketingskills 是 **被代理自动识别 + 触发的程序** |
| 营销 SaaS 工具 | Jasper、Copy.ai | 闭源 / 订阅；marketingskills MIT 开源，本地可改 |
| Notion 营销模板 | 各种 growth playbook | 人读为主；marketingskills 是 **agent 读** 的 markdown |
| MCP 营销工具 | 一些 `mcp-marketing-xxx` 服务 | 走协议对接外部 API；marketingskills 不调外部 API，纯本地工作流 |
| 单体 Claude Code 插件 | 各家自建 plugin | 多数聚焦一个任务；marketingskills 50 个技能 + 显式依赖图 |

核心关键词是 **Agent Skills spec**（[agentskills.io](https://agentskills.io)）。简单说：把"特定任务的工作流"封装成 markdown 文件，代理在识别到任务上下文时自动加载并按它执行。marketingskills 是目前覆盖面最广的营销向技能集合。

作者是 **Corey Haines**（`corey.co`），同时主理 `Conversion Factory`（增长代理）、`Swipe Files`（文案档案订阅）、`Magister`（自动 CMO 产品）。这层背景决定了技能库偏 **实战 SaaS 营销**，不是"营销理论"。

---

## 二、系统地图：50 个技能 × 8 大类 × 一张依赖图

README 里直接给出了一张 ASCII 依赖图。把它翻译成更易读的形态：

```
                        product-marketing（所有技能的前置）
                                  │
   ┌──────────┬───────────┬──────┴──────┬───────────┬──────────┬──────────┬──────────┐
   ▼          ▼           ▼             ▼           ▼          ▼          ▼          ▼
 SEO &     CRO       Content &    Paid &        Growth &    Sales &    Strategy   ...
 Content              Copy       Measurement    Retention   GTM
```

`product-marketing` 是 **唯一必读的前置技能**——它承载你的产品、用户、定位信息，其他技能在执行前先来读它，**避免每个技能各自问一遍"你产品是啥"**。README 的原话：

> The `product-marketing` skill is the foundation — every other skill checks it first to understand your product, audience, and positioning before doing anything.

50 个技能按类别组织，README 列出的 8 大类（按官方分类顺序）：

| 类别 | 典型技能 |
|------|----------|
| Conversion Optimization（转化优化） | `cro`、`signup`、`onboarding`、`popups`、`paywalls` |
| Content & Copy（内容与文案） | `copywriting`、`copy-editing`、`cold-email`、`emails`、`social`、`image` |
| SEO & Discovery（SEO 与发现） | `seo-audit`、`ai-seo`、`programmatic-seo`、`site-architecture`、`competitors`、`schema` |
| Paid & Distribution（付费与分发） | `ads`、`ad-creative` |
| Measurement & Testing（衡量与测试） | `analytics`、`ab-testing` |
| Retention（留存） | `churn-prevention` |
| Growth Engineering（增长工程） | `co-marketing`、`free-tools`、`referrals` |
| Strategy & Monetization（战略与变现） | `marketing-ideas`、`marketing-psychology`、`launch`、`pricing`、`marketing-loops`、`marketing-plan` |
| Sales & RevOps（销售与营收运营） | `revops`、`sales-enablement` |
| 其他工具型 | `competitor-profiling`、`directory-submissions`、`customer-research`、`marketing-council`、`offers`、`public-relations`、`sms`、`video` |

把 50 个全部列出来会很长，README 的 SKILLS 表里给了完整清单，本节不再重复。下面看几个 **典型技能做什么**：

- `cro`：优化任何营销页或表单的转化率（首页、落地页、表单）。
- `copywriting`：写或改任何营销页文案（首页、落地页、产品页）。
- `cold-email`：写 B2B 冷邮件与跟进序列。
- `ads`：Google Ads / Meta / LinkedIn / X 的付费广告活动。
- `ai-seo`：面向 AI 搜索引擎（AEO / GEO / LLMO）的优化。
- `ab-testing`：设计 / 实施 A/B 测试或搭建增长实验体系。
- `churn-prevention`：降低流失率、构建取消流程、设置挽留优惠、恢复失败支付。
- `marketing-council`：模拟一个"营销顾问委员会"，从多专家视角回答营销问题。
- `marketing-loops`：搭建可重复运行的营销工作流（agent 周期性跑）。

### 2.1 显式的跨技能引用

README 给出的几个例子：

- `copywriting` ↔ `cro` ↔ `ab-testing`
- `revops` ↔ `sales-enablement` ↔ `cold-email`
- `seo-audit` ↔ `schema` ↔ `ai-seo`
- `customer-research` → `copywriting`, `cro`, `competitors`

意思是：技能不是 50 个孤岛，而是 **按真实营销工作流互相引用的网络**。每个技能自身的 SKILL.md 里都有 "Related Skills" 段落，给出完整依赖图。

---

## 三、安装：6 条路径按场景挑

README 给出了 6 种安装方式，按"上手难度 × 可定制度"排序：

### 3.1 路径 1：`npx skills` CLI（推荐）

```bash
# 装全部
npx skills add coreyhaines31/marketingskills

# 装指定技能
npx skills add coreyhaines31/marketingskills --skill cro copywriting

# 看可装列表
npx skills add coreyhaines31/marketingskills --list
```

CLI 会 **自动检测你装好的代理**，问装到哪个目录。Claude Code 走 `.claude/skills/`，通用代理走 `.agents/skills/`。

> ⚠️ README 给出的关键陷阱：如果你 **从代理会话内部** 跑这个命令（比如让 Claude Code 自己装），CLI 会走非交互模式，可能只装到通用的 `.agents/skills/`，而 Claude Code 不会读那个目录。**显式指定代理**：
> ```bash
> npx skills add coreyhaines31/marketingskills -a claude-code
> ```

### 3.2 路径 2：Claude Code Plugin

```bash
/plugin marketplace add coreyhaines31/marketingskills
/plugin install marketing-skills
```

走 Claude Code 自带插件系统。

### 3.3 路径 3：克隆 + 拷贝

```bash
git clone https://github.com/coreyhaines31/marketingskills.git
cp -r marketingskills/skills/* .agents/skills/
```

最朴素，**适合离线 / 内网 / 不能用 npx 的环境**。

### 3.4 路径 4：Git Submodule

```bash
git submodule add https://github.com/coreyhaines31/marketingskills.git .agents/marketingskills
```

技能源作为子模块，**上游更新用 `git submodule update --remote` 一键同步**。**这是最"工程师友好"的路径**——既享受上游更新，又能把团队自定义写进仓库的 `.agents/skills/`。

### 3.5 路径 5：Fork + 改

Fork → 自定义 → 克隆你的 fork 进项目。**适合需要深度定制（比如把内部品牌话术写进 `product-marketing`）的团队**。

### 3.6 路径 6：SkillKit 多代理一键装

```bash
npx skillkit install coreyhaines31/marketingskills
npx skillkit install coreyhaines31/marketingskills --skill cro copywriting
npx skillkit install coreyhaines31/marketingskills --list
```

[SkillKit](https://github.com/rohitg00/skillkit) 是另一个工具，**面向"在 Claude Code + Cursor + Copilot 等多代理里同步装技能"** 的场景。

### 3.7 选哪条？

| 你的场景 | 推荐路径 |
|----------|----------|
| 个人开发 / 试一下 | 路径 1（`npx skills add`） |
| 团队共用一套基线 | 路径 4（git submodule） |
| 没法用 npm / 内网 | 路径 3（克隆 + 拷贝） |
| 跨代理（Cursor + Claude Code + Copilot） | 路径 6（SkillKit） |
| 需要深度定制 | 路径 5（Fork） |

---

## 四、v1.x → v2.0 升级：17 个重命名别踩坑

仓库当前主版本是 **v2.0**。v2.0 的核心变化：

- **17 个技能被改名**（重命名表见下）。
- **`page-cro` + `form-cro` 合并成单一的 `cro`**。
- **上下文文件搬家**：从 `.claude/product-marketing-context.md` → `.agents/product-marketing.md`。

升级时 README 给出的清单：**装新之前先删旧**，否则你会看到 `skills/page-cro/` 和 `skills/cro/` 同时存在这种"新旧并存"的状态：

```bash
rm -rf page-cro form-cro \
       ab-test-setup analytics-tracking aso-audit competitor-alternatives \
       email-sequence free-tool-strategy launch-strategy onboarding-cro \
       paid-ads paywall-upgrade-cro popup-cro pricing-strategy \
       product-marketing-context referral-program schema-markup \
       signup-flow-cro social-content
```

完整重命名映射（README 原表）：

| v1.x（旧名） | v2.0（新名） |
|--------------|--------------|
| `ab-test-setup` | `ab-testing` |
| `analytics-tracking` | `analytics` |
| `aso-audit` | `aso` |
| `competitor-alternatives` | `competitors` |
| `email-sequence` | `emails` |
| `form-cro` | 合并入 `cro` |
| `free-tool-strategy` | `free-tools` |
| `launch-strategy` | `launch` |
| `onboarding-cro` | `onboarding` |
| `page-cro` | `cro` |
| `paid-ads` | `ads` |
| `paywall-upgrade-cro` | `paywalls` |
| `popup-cro` | `popups` |
| `pricing-strategy` | `pricing` |
| `product-marketing-context` | `product-marketing` |
| `referral-program` | `referrals` |
| `schema-markup` | `schema` |
| `signup-flow-cro` | `signup` |
| `social-content` | `social` |

`product-marketing` 上下文文件的迁移命令：

```bash
mkdir -p .agents
# v2.0 文件（或已用新名的 v1.x 文件）
mv .claude/product-marketing.md .agents/product-marketing.md 2>/dev/null
# 旧文件名
mv .claude/product-marketing-context.md .agents/product-marketing.md 2>/dev/null
```

> 兼容兜底：技能仍会回退去读 `.claude/` 和旧的 `product-marketing-context.md` 文件名，**不迁移也不会立刻挂**，但 README 推荐尽快迁到 v2.0 路径。

---

## 五、使用：装上之后代理会自动认

README 强调：**装上之后，代理会自己识别你问的任务属于哪个技能**，不需要你每次手动点名。例子：

```
"Help me optimize this landing page for conversions"
→ 触发 cro 技能

"Write homepage copy for my SaaS"
→ 触发 copywriting 技能

"Set up GA4 tracking for signups"
→ 触发 analytics 技能

"Create a 5-email welcome sequence"
→ 触发 emails 技能
```

也可以直接命令式调用：

```
/cro
/emails
/seo-audit
```

**真正决定"代理识不识别得对"的，是 `product-marketing` 上下文文件**。README 把这层关系放在 README 的开头图里，意思是：你写得越清楚，技能组合出来的输出越准。

---

## 六、典型使用流：四个常见任务怎么跑

下面 4 个任务把"装好之后"实际怎么用拆开来看：

### 6.1 优化首页转化

触发技能：`product-marketing` → `cro` → `copywriting`（按需）→ `ab-testing`（按需）。

代理会先去读 `.agents/product-marketing.md` 拿产品和定位，然后按 `cro` 技能里的框架（价值主张层级、CTA 密度、社会证明、转化漏斗诊断）输出建议；如果你让它直接改文案，则切到 `copywriting`；如果你想验证，它会切到 `ab-testing` 给实验设计。

### 6.2 写一封 B2B 冷邮件

触发技能：`customer-research`（了解目标客户）→ `cold-email`。

`customer-research` 先给目标客户画像，`cold-email` 再按框架（钩子—价值—证据—CTA）写正文与跟进序列。

### 6.3 给网站做 SEO 体检

触发技能：`seo-audit` → `ai-seo` → `schema`（按需）。

`seo-audit` 跑技术 / 站内 SEO 清单；`ai-seo` 处理"被 LLM 引用"的优化（AEO / GEO / LLMO）；`schema` 处理结构化数据。

### 6.4 跑一次"顾问委员会"得到多角度看法

触发技能：`marketing-council`。

README 把这个技能描述为"a simulated board of advisors staffed by specialized agents"——一组专家角色代理对一个营销问题分别给意见。**这个技能在没有 `product-marketing` 上下文时也能跑**，但有上下文时输出更聚焦。

---

## 七、适用边界与决策建议

### 7.1 适合用 marketingskills 的人群

- **技术型营销人 / 增长负责人**：自己写 SQL、改落地页、配 GA4 事件，AI 代理是日常工具。
- **SaaS 创始人（早期）**：自己没有专职营销，希望代理先顶上"基本盘"（SEO 体检、文案初稿、A/B 测试设计）。
- **AI Agent Builder**：在搭自己的"营销垂直 agent"，希望拿到一份高质量 baseline 技能库，再做领域定制。
- **团队希望统一"营销话术 / 框架"**：通过 `product-marketing` 集中维护品牌话术，所有技能自动引用，避免每个人用不同 prompt 出来的文案不一致。

### 7.2 不太适合的场景

- **完全没有技术背景的"纯营销"同学**。技能库假设你会用 Claude Code / Cursor 这类工具。如果你连终端都不熟，先去 `codingformarketers.com`（README 里也提了）。
- **希望代理完全替代营销团队**。技能库是 **框架与脚手架**，不是策略与判断——CRO 测试、付费投放预算、增长方向还得人来定。
- **B2C 强创意型工作**（比如大预算 TVC、social 大片）。技能库覆盖到 `image` / `video` 这类 AI 生成层，但真正的创意方向仍要人拍板。
- **要严格审计的合规场景**。技能输出是 LLM 文本，受幻觉（hallucination）影响——医疗 / 金融 / 法律行业的对外文案要二次人工审。

### 7.3 与同类资源的边界

| 你想要的 | 选什么 |
|----------|--------|
| 一份能立刻用上、覆盖最广营销任务的"代理技能包" | **marketingskills**（本文主角） |
| 一个"产品上下文 + 营销技能"二合一的工程化包 | Corey Haines 的 `Conversion Factory` 商业服务 |
| 自动 CMO 产品（直接跑代理） | `Magister`（magistermarketing.com） |
| 文案灵感与档案 | `Swipe Files`（swipefiles.com） |
| 单个营销任务的 Claude Code plugin | `plugin marketplace add` 其他社区 plugin |

### 7.4 起步建议

按这个顺序上手最省力：

1. **写好 `product-marketing` 上下文**。把你产品、用户、定位、关键话术写进 `.agents/product-marketing.md`。这是 50 个技能的"事实来源"。
2. **先装 3–5 个高频技能**：`cro` / `copywriting` / `analytics` / `ab-testing` / `seo-audit`。**不要一次装满 50 个**——会拖代理识别。
3. **用 git submodule 接入团队仓库**（路径 4）。后续上游更新 `git submodule update --remote` 即可。
4. **把内部品牌话术 / 数据仪表盘定义 / 实验节奏表写进 `product-marketing`**，让所有技能自动继承。
5. **v1.x 老用户先按 README 清单删旧**。否则新旧技能并存会让代理识别错乱。

---

## 八、参考与延伸

- 仓库主页：<https://github.com/coreyhaines31/marketingskills>
- 规范：[Agent Skills spec](https://agentskills.io)
- 安装工具：
  - [npx skills](https://github.com/vercel-labs/skills)
  - [SkillKit](https://github.com/rohitg00/skillkit)
- 作者：[Corey Haines](https://corey.co) / [Conversion Factory](https://conversionfactory.co) / [Swipe Files](https://swipefiles.com) / [Magister](https://magistermarketing.com) / [AI Marketing Training](https://conversionfactory.co/offers/ai-marketing-training)
- 配套入门：[Coding for Marketers](https://codingformarketers.com)
- 贡献指南：[CONTRIBUTING.md](CONTRIBUTING.md)
- 许可证：MIT
