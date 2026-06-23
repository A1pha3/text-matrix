---
title: "Awesome Codex Skills：Codex CLI 的技能宝库，让 AI 代理真正替你干活"
date: "2026-04-27T00:58:00+08:00"
slug: awesome-codex-skills
aliases:
  - /posts/tech/awesome-codex-skills-codex-agent-skills/
description: "Codex Skills 是模块化指令包，让 Codex CLI 能执行发邮件、操作 GitHub、发 Slack 等真实任务。本文全景解析十大分类热门技能及构建方法。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "Codex", "OpenAI", "自动化", "工作流"]
---


Codex CLI 默认只输出文本。Awesome Codex Skills（以下简称 ACS）把它改造成能调外部 API、操作 GitHub、发 Slack、写 Notion 的执行器，靠的是一套"描述触发 + 按需加载"的 Skill 模块。

ACS 适合已经在用 Codex CLI 且希望它直接产出工单、消息、文档的人；如果只是想让模型回答问题，引入 Skills 反而增加维护成本。本文要回答三个问题：Skill 的触发与执行边界在哪里、哪个 Skill 该先装、什么场景不该上 ACS。

---

## 一、Skill 是什么：描述触发，按需加载

一个 Skill 是一个独立文件夹，以 `SKILL.md` 为入口。Codex 启动时只读取 frontmatter 里的 `description`，用来判断何时触发；触发后才加载 body 里的执行步骤。这样设计是为了让上下文保持轻量——100 个 Skill 不会撑爆 context window。

文件夹结构如下：

```
skill-name/
├── SKILL.md          # 必选：指令 + YAML frontmatter
├── scripts/          # 可选：确定性辅助脚本
├── references/       # 可选：长文档，仅在需要时加载
└── assets/          # 可选：模板或静态资源
```

`SKILL.md` 的最小可用形态：

```markdown
---
name: my-skill-name
description: 这个技能做什么，以及何时触发。
---

My Skill Name

执行步骤...
```

设计上的关键约束：`description` 决定触发，body 决定执行。描述写得越具体（"当用户要求把会议转录稿转成 action item 时触发"），Codex 越不会误触发；描述越泛（"处理会议相关任务"），多个 Skill 之间会打架。

---

## 二、系统地图：四条主线如何分工

ACS 里有四条容易混淆的主线，边界先拆清楚：

| 主线 | 职责 | 关键文件 / 命令 | 谁负责 |
|------|------|----------------|--------|
| 触发 | 用 `description` 匹配用户意图 | `SKILL.md` frontmatter | Codex 运行时 |
| 执行 | 加载 body 步骤、调用脚本或 references | `SKILL.md` body、`scripts/`、`references/` | Skill 作者 |
| 安装 | 把 Skill 文件夹放进 `$CODEX_HOME/skills/` | `skill-installer` 脚本或手动复制 | 用户 |
| 外部能力 | 通过 Composio CLI 接入 Slack、GitHub、Notion 等 | `connect` Skill + Composio CLI | Composio 平台 |

前三条是 ACS 自带的闭环，第四条通过 `connect` Skill 桥接到 Composio 生态。这条边界决定了 ACS 的能力上限：ACS 本身不提供 Slack API，它只告诉 Codex"何时该调 Composio CLI"。

---

## 三、快速上手：两种安装方式

### 方式一：Skill Installer（推荐）

```bash
git clone https://github.com/ComposioHQ/awesome-codex-skills.git
cd awesome-codex-skills/awesome-codex-skills

# 安装单个技能到 ~/.codex/skills/
python skill-installer/scripts/install-skill-from-github.py \
  --repo ComposioHQ/awesome-codex-skills \
  --path meeting-notes-and-actions
```

安装完毕后重启 Codex，新技能即生效。在对话中自然描述任务，Codex 自动匹配触发。

### 方式二：手动安装

1. 复制目标技能文件夹到 `$CODEX_HOME/skills/`（默认 `~/.codex/skills/`）
2. 重启 Codex 使其重新加载元数据
3. 开始对话

`skill-installer` 的内部逻辑就两步：从 GitHub 拉取指定 `--repo` + `--path` 下的文件夹，移动到 `$CODEX_HOME/skills/<skill-name>/`。维护自有技能库时，提供这两个参数就能分发；不满意默认位置，安装后手动搬运即可。

---

## 四、Skill 全景图：十大分类总览

ACS 将技能分为十大分类，下表列出每个分类下高频被引用的技能及能力。能力描述基于 ACS 仓库 README（截至 2026-04-27），具体行为以仓库最新版本为准。

### 1. 开发与代码工具（Development & Code Tools）

| 技能 | 来源 | 能力 |
|------|------|------|
| `brooks-lint` | hyhmrright | AI 代码审查，基于六本经典工程著作，输出衰减风险诊断 + 严重等级 + 四种分析模式 |
| `codebase-migrate` | 内置 | 大型代码库迁移，支持多文件重构批量审查 + CI 验证 |
| `deploy-pipeline` | 内置 | 端到端 Stripe → Supabase → Vercel 流水线，含验证和回滚 |
| `gh-address-comments` | 内置 | 用 `gh` 命令 addressing GitHub PR 上的 review/inissue 评论 |
| `gh-fix-ci` | 内置 | 检查 GitHub Actions 失败原因并给出修复建议 |
| `mcp-builder` | 内置 | 构建和评估 MCP 服务器，含实践建议和评估工具 |
| `sentry-triage` | 内置 | 诊断 Sentry 问题，自动映射堆栈帧到本地源码 |
| `webapp-testing` | 内置 |  Targeted Web 应用测试并汇总结果 |

### 2. 生产力与协作（Productivity & Collaboration）

| 技能 | 能力 |
|------|------|
| `connect` | 通过 Composio CLI 连接 1000+ 应用（Slack、GitHub、Notion 等，应用数量来自 Composio 官方宣传，实际可用性需以 dashboard.composio.dev 列表为准）|
| `linear` | 在 Linear 中管理 issue、project 和团队工作流 |
| `meeting-notes-and-actions` | 将会议转录稿转化为摘要，含决策和责任人 action item |
| `notion-meeting-intelligence` | 聚合 Notion 上下文 + Codex 研究，生成会议准备材料 |
| `invoice-organizer` | 规范化发票数据，支持追踪和报表 |
| `support-ticket-triage` | 客户工单分类、优先级排序 + 起草回复 |

### 3. 通信与写作（Communication & Writing）

| 技能 | 能力 |
|------|------|
| `email-draft-polish` | 起草、润色或压缩邮件，适配目标语气和受众 |
| `changelog-generator` | 从 commit 或摘要生成清晰的 changelog |
| `content-research-writer` | 研究 + 起草内容，含引文来源 |
| `tailored-resume-generator` | 根据岗位描述定制简历，突出量化成果 |

### 4. 数据与分析（Data & Analysis）

| 技能 | 能力 |
|------|------|
| `spreadsheet-formula-helper` | 编写和调试 Excel/Sheets 公式、透视表、数组公式 |
| `datadog-logs` | 通过 Composio CLI 过滤 Datadog 日志，输出 JSON 友好格式 |
| `lead-research-assistant` | 研究潜在客户，补充公司层面数据 |
| `langsmith-fetch` | 拉取 LangSmith 项目/测试数据用于分析 |

### 5. Meta 与工具（Meta & Utilities）

| 技能 | 能力 |
|------|------|
| `skill-creator` | 构建新技能的实践建议指导 |
| `skill-installer` | 从 GitHub 安装技能的脚本工具 |
| `template-skill` | 新技能的起步模板 |

---

## 五、任务流案例：一句"在 Slack 通知上线成功"如何流过系统

四条主线在真实任务里如何配合，看一次完整流程：

1. **用户输入**："在 Slack 的 #release 频道发一条说 v1.2.3 上线成功"
2. **触发匹配**：Codex 扫描所有已安装 Skill 的 `description`，命中 `connect` 的描述（涉及 Slack 消息发送）
3. **加载 body**：`connect/SKILL.md` 的执行步骤被加载进上下文，告诉 Codex 该调 Composio CLI 的哪个命令
4. **执行外部能力**：Codex 调用 `composio` CLI，参数包含频道名和消息内容；Composio 平台代为调用 Slack API
5. **返回结果**：Slack 消息 ID 回到 Codex，Codex 向用户确认发送成功

整个流程里，ACS 只负责第 2、3 步（触发与执行引导），第 4 步的实际 API 调用由 Composio 平台完成。这就是为什么 `connect` 必须配合 Composio CLI 使用——ACS 自己不持有 Slack token。

---

## 六、四个高频 Skill 的能力与代价

### 6.1 connect：接入外部应用的桥

`connect` 是 ACS 中调用频率最高的 Skill。它通过 Composio CLI 让 Codex 直接调外部应用 API，输出的是已发送的消息、已创建的 issue 这类真实副作用，操作步骤文本只是中间产物。

支持的生态包括：

- **协作工具**：Slack、Discord、Notion、Linear、Jira
- **代码平台**：GitHub、GitLab、Bitbucket
- **云服务**：AWS、Stripe、Supabase、Vercel
- **数据平台**：Datadog、LangSmith、Helium（实时新闻 + 市场数据）

安装后，Codex 能执行类似下面的任务："在 Slack 发一条消息说上线成功"、"在 GitHub 创建一个 issue"、"在 Notion 更新这篇文档的状态"。这些任务的前提是用户已在 Composio 平台完成对应应用的 OAuth 授权。

### 6.2 meeting-notes-and-actions：从会议记录到可执行任务

会议开完后，决策散落在聊天记录里、没人跟进——这是协作工具的常见痛点。这个 Skill 用结构化输出把转录稿变成可分配的 action item。

输入一段会议转录稿，输出包含：

- 结构化摘要（议程、讨论点、决策）
- 每个 action item 标注负责人的标签
- 清晰的跟进项列表

配合 `notion-meeting-intelligence`，还能在会前基于 Notion 中的上下文自动准备材料，会后自动同步到 Notion 知识库。两个 Skill 串联的前提是会议内容确实写在 Notion 里；如果用其他工具（飞书文档、Google Docs），需要先迁移或自建类似 Skill。

### 6.3 brooks-lint：用经典工程书做代码审查

`brooks-lint` 是一个 AI 审查框架，把六本经典工程著作（《人月神话》《代码大全》等）的判断标准编码进 prompt，对代码进行以下维度的诊断：

- **衰减风险诊断**：识别代码退化的早期信号
- **严重等级**：Critical / Major / Minor / Note 四级
- **四种分析模式**：PR review、架构审计、技术债务评估、测试质量分析

每个问题都会附带书籍引用，让审查结果有据可查。这种设计的代价是审查视角偏"工程哲学"，对纯语法错误、性能瓶颈这类问题不如专门的 linter 敏感；适合用在架构 review 或技术债盘点场景，不适合替代 ESLint、mypy 这类工具。

### 6.4 sentry-triage：自动映射堆栈帧到源码

Sentry 报警来了，传统流程是：复制堆栈帧 → 打开代码 → 手动匹配文件和行号。`sentry-triage` 把这个流程自动化：

1. 读取 Sentry 报警的堆栈信息
2. 自动映射到本地源码文件
3. 输出诊断结果和修复建议

省掉的是复制粘贴和人工匹配的误差。前提是本地源码与 Sentry 上报的版本一致；如果线上跑的是经过 minify 或 source map 处理的产物，映射会失败，需要先准备好 source map。

---

## 七、构建自己的 Skill

ACS 提供了完整的 [skill-creator](./skill-creator/) 指导，以及 [template-skill](./template-skill/) 起步模板。构建流程分三步。

### 第一步：定义触发条件（description）

```markdown
---
name: my-new-skill
description: 当用户要求 [具体任务] 时触发这个技能。
---
```

描述要具体到 Codex 能准确判断"这个技能该上场了"。避免过于泛化的描述，例如"处理会议相关任务"会与 `meeting-notes-and-actions`、`notion-meeting-intelligence` 同时命中，导致触发不稳定。

### 第二步：写执行步骤

- 保持步骤清晰、可执行
- 使用确定性脚本处理重复操作（脚本输出比让模型自由生成更稳定）
- 将长文档放进 `references/`，正文按需引用（避免一次性灌满上下文）

### 第三步：测试与调优

1. 放入 `$CODEX_HOME/skills/`
2. 重启 Codex
3. 用触发描述测试，看是否精准命中
4. 调整 description 措辞直到稳定

调优时常见的问题是描述过宽导致误触发。一个验证方法：把可能冲突的 Skill 同时安装，用边界任务测试，看 Codex 选哪个。

---

## 八、适用场景横向对比

| 场景 | 推荐技能 |
|------|---------|
| 会议管理全流程 | `meeting-notes-and-actions` + `notion-meeting-intelligence` |
| 代码审查与 CI 修复 | `brooks-lint` + `gh-fix-ci` + `pr-review-ci-fix` |
| 客户支持工单处理 | `support-ticket-triage` + `email-draft-polish` |
| 数据分析与日志查询 | `datadog-logs` + `langsmith-fetch` + `spreadsheet-formula-helper` |
| 跨应用自动化 | `connect` + `linear` + `notion-knowledge-capture` |
| 内容创作流水线 | `content-research-writer` + `changelog-generator` + `tailored-resume-generator` |

---

## 九、与 MCP 的关系：helium-mcp

ACS 中有一个值得单独关注的技能——`helium-mcp/`。它集成了实时新闻搜索（含偏差评分）、实时市场数据、ML 期权定价和平衡新闻综合，通过 MCP（Model Context Protocol）协议为 Codex 提供实时数据能力。

`helium-mcp` 与 `connect` 的区别在于数据通道：`connect` 走 Composio 平台调外部应用 API，`helium-mcp` 走 MCP 协议直接暴露实时数据工具。如果构建的代理需要实时新闻或市场行情，`helium-mcp` 比 `connect` 更直接；如果只是发消息、建 issue，仍然用 `connect`。

---

## 十、采用建议

按使用频率和上手难度，建议按以下顺序引入：

1. **第一周**：装 `connect` + `meeting-notes-and-actions`。前者打通外部工具，后者解决日常协作痛点，两个 Skill 就能覆盖大部分"让 Codex 替我做事"的场景。
2. **第二周**：根据工作流加 `gh-fix-ci`、`sentry-triage` 或 `datadog-logs`。这些 Skill 接的是已有工具链，不需要改原有流程。
3. **第三周以后**：尝试 `brooks-lint` 做架构 review，或用 `skill-creator` 自建 Skill。自建前先读 `template-skill` 的结构，避免 description 写得太泛。

不适合用 ACS 的场景：纯问答用途（不需要执行外部动作）、对数据隐私要求极高（Composio 平台代为调用 API 意味着凭证要交给第三方）、团队尚未统一 Codex CLI 版本（Skill 触发机制依赖运行时元数据扫描，版本不一致会导致行为差异）。

### 自测：判断你是否真的理解了 ACS

回答下面三个问题，能答对说明读到了机制层；答不上来建议回到第二、五章：

1. 用户说"帮我把今天会议的 action item 同步到 Linear"，Codex 会触发哪几个 Skill？触发顺序由什么决定？
2. `connect` Skill 自己持有 Slack token 吗？如果不持有，消息是怎么发出去的？
3. 你写了一个 description 为"处理代码相关任务"的 Skill，安装后发现 `gh-fix-ci` 经常被它抢触发，原因是什么？该怎么改？

第三个问题如果答得出"描述过宽导致 description 匹配冲突，需要收窄到具体任务动词和对象"，说明已经能开始自建 Skill 了。

**相关链接：**

- GitHub：https://github.com/ComposioHQ/awesome-codex-skills
- Composio 官网：https://dashboard.composio.dev
- Discord 社区：https://discord.com/invite/composio

🦞 每日 08:00 自动更新
