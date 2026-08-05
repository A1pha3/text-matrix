---
title: "AI Job Search：把 Claude Code 变成求职指挥中心的 30K Star 开源方案"
date: 2026-08-06T03:24:26+08:00
slug: "ai-job-search-claude-code-workflow"
github_repo: "MadsLorentzen/ai-job-search"
description: "AI Job Search 是一套基于 Claude Code 的开源求职框架，30K Stars，覆盖从简历设置、岗位搜索、匹配评估到自动投递的全流程。本文拆解其核心工作流、drafter-reviewer 双代理设计以及 PDF 验证循环。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "AI Agent", "求职自动化", "开源"]
---

## 学习目标

读完本文你能：

1. **理解** AI Job Search 的核心工作流（`/setup → /scrape → /rank → /apply → /interview`）如何串联成一套完整的求职 pipeline
2. **评估** 这套框架是否适合你的求职场景——它解决了什么问题，不解决什么问题
3. **说明** drafter-reviewer 双代理机制如何提升简历和求职信质量
4. **识别** PDF 验证循环解决的实际问题：LaTeX → PDF 渲染中常见的文字错位、字体回退、ATS 解析失败
5. **判断** 与同类工具（如 Career-Ops）的核心差异

## 一、先给判断

AI Job Search 不是"自动投简历机器人"，它是一个**结构化的求职工作流框架**，把 Claude Code 改造成一个全职的求职助理。作者 Mads Lorentzen（地球物理学家出身）在 2025 年底被裁后亲手构建了这套系统，用它完成了 69 次定制化投递、20 次首轮面试，最终在 2026 年 6 月以 AI 工程师身份入职。

这套框架目前在 GitHub 上拥有 **30K+ Stars** 和 **10K+ Forks**，MIT 协议开源，核心语言是 TypeScript（217K 行）和 Python（140K 行），附带 LaTeX 模板。

本文的核心判断是：**AI Job Search 的价值不在于"AI 帮你投简历"，而在于它把求职这个模糊、重复、情绪消耗大的过程，编码成一组可执行、可复现、可审计的 agent 工作流。**

## 二、系统地图

AI Job Search 的目录结构本身就是一张架构图。下表列出核心模块：

| 层级 | 目录/文件 | 职责 |
|------|-----------|------|
| 用户档案 | `CLAUDE.md` | 完整的候选人画像（教育、经历、技能、行为特征） |
| 工作流命令 | `.claude/commands/` | 11 个 Claude Code 命令（setup, scrape, rank, apply, interview 等） |
| 技能定义 | `.claude/skills/job-application-assistant/` | 7 份结构化 markdown 文件（从候选档案到面试准备） |
| 岗位搜索 | `.agents/skills/` | 6 个岗位搜索 CLI（LinkedIn, FreeHire, 丹麦 4 个门户） |
| 模板系统 | `cv/`, `cover_letters/`, `templates/` | LaTeX/Typst 简历模板 + 定制模板注册 |
| 验证管道 | `tests/`, `.github/workflows/ci.yml` | LaTeX 编译测试、技能 lint、CLI 类型检查 |

核心工作流是一条 5 步 pipeline：

```
/setup → /scrape → /rank → /apply → /interview
```

每一步都是一个 Claude Code 命令，定义在 `.claude/commands/` 目录下。用户通过 Claude Code 的 `/command` 语法触发，不需要手动操作任何文件。

## 三、核心工作流详解

### 3.1 /setup：初始化档案

`/setup` 命令提供三种 onboarding 路径：

- **Path A：文档导入**——把已有的简历 PDF、LinkedIn 导出、学位证书等放入 `documents/` 目录，Claude 自动解析并填充 `CLAUDE.md`
- **Path B：单份简历导入**——贴一份现有 CV，系统从中提取结构化信息
- **Path C：交互式访谈**——Claude 像招聘官一样提问，逐步构建候选人画像

`CLAUDE.md` 是整条 pipeline 的**单一事实源**，包含身份信息、教育背景、工作经历、技术栈、认证、出版物、行为特征和求职偏好。所有后续步骤（岗位匹配、简历定制、求职信撰写）都基于这份档案，不会凭空编造经历。

### 3.2 /scrape + /rank：搜索与排序

`/scrape` 命令调用 `.agents/skills/` 下的岗位搜索 CLI 工具，从不同渠道抓取岗位信息。目前内置了 6 个搜索技能：

- **linkedin-search**：LinkedIn 公开岗位（国家无关）
- **freehire-search**：freehire.me 技术岗位聚合器
- **jobindex-search**、**jobnet-search**、**jobbank-search**、**jobdanmark-search**：丹麦四个本地门户（作者的个人市场，但架构设计为可替换）

`/rank` 命令对抓取到的岗位做**评分排序**，评估维度包括：技能匹配度、经验契合度、文化适配、地理位置、职业发展空间。评分不只是一个数字，系统会给出每项评分的理由。

### 3.3 /apply：双代理投递

这是整个框架最精妙的部分。`/apply` 命令运行一个 **drafter-reviewer 双代理工作流**，包含 8 个步骤：

1. **解析**岗位信息（URL 或文本）
2. **评估匹配度**——对照候选人档案做多维评分
3. **起草**定制化的简历和求职信（LaTeX）
4. **生成审阅代理**——新开一个独立的 Claude 上下文，研究目标公司，评审初稿
5. **修订**——基于审阅反馈修改
6. **编译与检查**——`lualatex` 编译简历，`xelatex` 编译求职信，Claude 检查渲染后的 PDF 页面
7. **ATS 验证**——用 `pdftotext` 提取 PDF 文本层，检查 ATS 解析器实际看到的内容
8. **输出**——最终产物 + 验证清单

**drafter-reviewer 分离**是核心设计：起草者写初稿，第二个 Claude 代理以全新上下文研究公司并评审。这个设计避免了单次 pass 中常见的"漏掉关键词、框架太泛、语气不到位"问题。

### 3.4 /interview：面试准备

`/interview` 命令生成阶段性的面试准备包：

- 公司研究摘要
- 基于岗位描述的行为面试题预测
- 用 STAR 框架准备的回答草稿
- 反问环节建议

## 四、PDF 验证循环：为什么需要它

AI Job Search 最独特的设计是**PDF 编译后自动验证**。大多数 LaTeX 简历模板在 `.tex` 文件里看起来没问题，但渲染成 PDF 后经常出现：

- 简历标题行跨页断到下一页
- 求职信溢出到第二页
- 列表项字体静默回退到正文体
- 图标字形在 PDF 文本层变成乱码（ATS 解析时看不到邮箱地址）

`/apply` 命令做了三件事来应对：

1. **视觉检查**——Claude 读取渲染后的 PDF 页面，检查布局是否符合预期
2. **自动修复**——针对溢出行应用 `\needspace`、`\enlargethispage` 和字体匹配包装
3. **ATS 文本层验证**——用 `pdftotext` 提取 PDF 文本层，检查联系方式是否以纯文本形式存在、阅读顺序是否正常、岗位关键词覆盖度

这套循环确保每一份投递出去的 PDF 在 ATS 系统中也是可读的，而不仅仅是"看起来好看"。

## 五、与同类工具的差异

目前同类开源方案中，最接近的是 Career-Ops（santifer/career-ops，同样基于 Claude Code）。两者的核心差异在于：

| 维度 | AI Job Search | Career-Ops |
|------|--------------|------------|
| 定位 | 求职工作流框架 | Skill mode 集合 |
| 核心机制 | 5 步 pipeline + 双代理 | 15 个 skill mode + Go TUI |
| 简历生成 | LaTeX 编译 + PDF 验证循环 | Playwright 截图 + PDF 生成 |
| ATS 检查 | pdftotext 文本层验证 | 无 |
| 岗位搜索 | 6 个 portal CLI 工具 | 无内置搜索 |
| 模板系统 | LaTeX/Typst 多模板注册 | 固定模板 |

简而言之，**AI Job Search 更偏向"端到端的求职工作流"，而 Career-Ops 更偏向"在 Claude Code 中注入求职相关的 skill 能力"**。前者适合需要完整求职 pipeline 的用户，后者适合需要灵活组合 skill 的用户。

## 六、适用边界

### 适合

- 正在主动求职、愿意投入时间做定制化投递的开发者
- 熟悉 Claude Code 的命令行工作流
- 需要 LaTeX 简历且在意 ATS 兼容性的用户
- 愿意 fork 并适配自己市场（替换搜索 portal 技能）

### 不适合

- 期望"一键投递所有匹配岗位"的用户——框架明确反对 spray-and-pray 策略
- 不使用 Claude Code 的用户（虽然 `AGENTS.md` 提供了 Codex/Antigravity 的适配指引）
- 非丹麦市场的岗位搜索（内置 portal 技能以丹麦为主，需自行替换）
- 不喜欢 LaTeX 简历的用户

### 已知局限

- 岗位搜索 CLI 用 Bun 运行，需要额外安装依赖
- 简历编译依赖 LaTeX 发行版（MacTeX/TinyTeX 等），最小安装需额外安装若干宏包
- ATS 检查依赖 `pdftotext`（poppler 工具集），缺失时降级为视觉关键词检查

## 七、采用建议

如果你正在求职且使用 Claude Code，建议的采用顺序：

1. **Fork 仓库**，按 `SETUP.md` 完成 `/setup` 初始化
2. **先跑 `/scrape` + `/rank`**，看系统对市场的评估是否合理
3. **对 1-2 个高匹配岗位跑 `/apply`**，体验完整流程
4. 如果满意，再替换岗位搜索 portal 为自己的市场

不需要一开始就配置所有 portal 技能，框架的各个命令是独立可用的。

---

**项目地址**：<https://github.com/MadsLorentzen/ai-job-search>

**许可**：MIT