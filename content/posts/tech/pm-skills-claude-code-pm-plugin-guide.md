---
title: "pm-skills：把 Teresa Torres / Marty Cagan / Alberto Savoia 的 PM 框架做成 AI 工作流，68 个 skill + 42 条 command"
date: "2026-06-09T17:59:00+08:00"
slug: "pm-skills-claude-code-pm-plugin"
aliases:
  - "/posts/tech/pm-skills-claude-code-pm-plugin/"
description: "pm-skills 是面向 Claude Code / Codex / Cowork 的 PM 操作系统，9 个插件覆盖 discovery / strategy / execution / GTM 全周期，68 个 skill 编码了 OST / RICE / JTBD 等真实 PM 框架，42 条 command 把它们串成端到端工作流。"
draft: false
categories: ["技术笔记"]
tags: ["PM", "ClaudeCode", "ClaudeCowork", "ProductManagement", "OST", "Plugins"]
---

# pm-skills：把 Teresa Torres / Marty Cagan / Alberto Savoia 的 PM 框架做成 AI 工作流，68 个 skill + 42 条 command

## 读完这篇文章你会知道

- pm-skills 的项目定位和三层结构
- 如何安装和使用 pm-skills
- 典型 Discovery 链的工作流
- 9 个 Plugin 的覆盖全景
- 如何选择合适的采用顺序

---

## 目录

- [核心判断](#核心判断)
- [项目概览](#项目概览)
- [三层结构](#三层结构)
- [9 个 Plugin 与典型入口](#9-个-plugin-与典型入口)
- [典型例子](#典型例子)
- [安装](#安装)
- [适用边界](#适用边界)
- [阅读路径](#阅读路径)
- [常见问题与故障排查](#常见问题与故障排查)
- [自测](#自测)
- [进阶路径](#进阶路径)

---

## 一、核心判断

pm-skills 不教你"AI 怎么写 PRD"——它把 PM 圈**最经得起验证的框架**做成 AI 能直接执行的指令文件：

- **Teresa Torres 的 Opportunity Solution Tree（OST）**
- **Marty Cagan 的产品战略 Canvas / SVPG 框架**
- **Alberto Savoia 的 Pretotype（精益创业实验设计）**
- **RICE / ICE / MoSCoW / Kano / WSJF / Impact-Effort 等 9 个优先级模型**

三件事值得特别说：

1. **Skill = 框架，Command = 工作流**——一个 `/discover` 把 brainstorm-ideas → identify-assumptions → prioritize-assumptions → brainstorm-experiments 四步串起来，对应"发现 → 假设 → 优先级 → 实验" 的 PM 黄金链路
2. **完整覆盖 9 个 PM 域**：discovery、strategy、execution、market-research、data-analytics、marketing-growth、GTM、AI-shipping、toolkit
3. **平台兼容好**：Claude Code 原生 Plugin，Codex CLI 直读同 marketplace 文件，Gemini CLI / OpenCode / Cursor / Kiro 都吃通用 skill 格式

它把 PM 工作**从"用 AI 写文本"升级到"用 AI 走框架"**。

---

## 二、项目概览

| 维度 | 数据 |
|---|---|
| **仓库** | [phuryn/pm-skills](https://github.com/phuryn/pm-skills) |
| **Stars** | 13,085 ★（2026-06-09 抓取） |
| **License** | MIT |
| **规模** | 68 skills + 42 commands + 9 plugins |
| **设计目标** | Claude Code / Cowork 优先，skill 格式通用 |
| **配套** | [phuryn/pm-brain](https://github.com/phuryn/pm-brain)（个人/团队记忆层） |

---

## 三、三层结构：Skill / Command / Plugin

```
Plugin = 一个 PM 域的安装包
  ├── Command = 端到端工作流（如 /discover、/write-prd）
  │     └── Skill = 框架 / 决策树 / 检查清单
  └── Skill = 可被多个 Command 复用的基础（如 prioritize-assumptions）
```

- **Skill** 是构建块——给 Claude 领域知识、分析框架或引导式 workflow。Claude 在对话中**自动加载相关 skill**（不需显式调用），需要强制加载可用 `/plugin-name:skill-name`
- **Command** 是用户主动触发的端到端流程——`/command-name` 启动，串 1 到多个 skill
- **Plugin** 把相关 skill / command 打包为可装单元——装 marketplace 一次拿 9 个 plugin

---

## 四、9 个 Plugin 与典型入口

| 入口 | 完整链路 |
|---|---|
| `/discover` 新点子 | `brainstorm-ideas` → `identify-assumptions` → `prioritize-assumptions` → `brainstorm-experiments` |
| `/strategy` 战略 | 9 段 Product Strategy Canvas（愿景 → 防御性） |
| `/write-prd` PRD | 8 段 PRD 模板 |
| `/plan-launch` 上线 | GTM 计划 + 风险 + 成功指标 |
| `/north-star` 指标 | North Star + 输入指标 + 告警阈值 |
| `/plan-okrs` 目标 | 公司目标对齐到团队 OKR |
| `/sprint plan` 迭代 | 容量估算 + 故事选择 + 风险识别 |
| `/retro` 复盘 | 结构化 retrospective |
| `/release-notes` 公告 | 票 / PRD / changelog → 用户面 release notes |
| `/red-team-prd` 红队 | 对抗式压力测试 + 假设降权 |
| `/stakeholder-map` 干系人 | Power × Interest 网格 + 沟通计划 |
| `/meeting-notes` 会议 | 转录 → 决策 + 行动项 |

---

## 五、典型例子：完整 Discovery 链

```bash
/discover AI-powered meeting summarizer for remote teams
```

Claude 会按顺序执行：
1. `brainstorm-ideas-new` — 多角度发散（PM / Designer / Engineer 三视角）
2. `identify-assumptions-new` — 8 类风险（Value / Usability / Viability / Feasibility + GTM / Strategy / Team / 等等）
3. `prioritize-assumptions` — Impact × Risk 矩阵 + 实验建议
4. `brainstorm-experiments-new` — Alberto Savoia 风格的 pretotype 设计

每步完成会建议下一步命令——`/discover` 完了提示是否要 `/write-prd`、`/plan-launch`、`/north-star`，**符合真实 PM 工作流的串联**。

---

## 六、安装

### 6.1 Claude Cowork（最简单，PM 非技术岗推荐）

1. 左下 **Customize**
2. **Browse plugins** → **Personal** → **+**
3. **Add marketplace from GitHub**
4. 填 `phuryn/pm-skills`
5. 9 个 plugin 全装好，command 和 skill 都能用

### 6.2 Claude Code（CLI）

```bash
# 1. 加 marketplace
claude plugin marketplace add phuryn/pm-skills

# 2. 装 plugin（按需）
claude plugin install pm-toolkit@pm-skills
claude plugin install pm-product-strategy@pm-skills
claude plugin install pm-product-discovery@pm-skills
claude plugin install pm-market-research@pm-skills
claude plugin install pm-data-analytics@pm-skills
claude plugin install pm-marketing-growth@pm-skills
claude plugin install pm-go-to-market@pm-skills
claude plugin install pm-execution@pm-skills
claude plugin install pm-ai-shipping@pm-skills
```

### 6.3 Codex CLI（OpenAI）

Codex 直读同 marketplace 文件：

```bash
codex plugin marketplace add phuryn/pm-skills
codex plugin add pm-execution@pm-skills
```

注意：Codex 不会把 `/slash` 命令注册成原生 slash command，README 建议**用自然语言描述 workflow**（"Run product discovery on X: brainstorm, map assumptions, prioritize, then design experiments — pause between each step"）。可以请 Codex 把命令文件转成 Codex skill。

### 6.4 其他工具（仅 skill）

把 `skills/*/SKILL.md` 复制到对应目录即可：

| 工具 | 路径 |
|---|---|
| Gemini CLI | `~/.gemini/skills/` |
| OpenCode | `.opencode/skills/` |
| Cursor | `.cursor/skills/` |
| Kiro | `.kiro/skills/` |

---

## 七、9 个 Plugin 的覆盖全景

| Plugin | Skill 数量 | Command 数量 | 关键框架 |
|---|---|---|---|
| **pm-product-discovery** | 13 | 5 | OST（Teresa Torres）、JTBD、假设矩阵 |
| **pm-product-strategy** | 12 | 5 | Product Strategy Canvas、Lean Canvas、BMC、PESTLE、Porter's 5 |
| **pm-execution** | 16 | 11 | PRD 8 段、OKR、sprint、retro、release notes、pre-mortem |
| **pm-market-research** | — | — | 用户访谈、竞品扫描、市场细分 |
| **pm-data-analytics** | — | — | North Star、A/B 测试设计、漏斗分析 |
| **pm-marketing-growth** | — | — | 增长假设、渠道矩阵、留存曲线 |
| **pm-go-to-market** | — | — | 定位、定价、launch plan、stakeholder map |
| **pm-ai-shipping** | — | — | AI 产品特有的 eval / 安全 / cost / iteration |
| **pm-toolkit** | — | — | 通用 9 个优先级框架（Opportunity Score / RICE / ICE / MoSCoW / Kano 等） |

具体 skill 列表看 README，9 个 plugin 总共 68 skill + 42 command。

---

## 八、和"提示工程式 PM 模板"的差别

- **Prompt 模板**：每次粘贴文本，AI 知道"框架"但不会真做
- **pm-skills**：framework 是 SKILL.md 文件，Claude 自动加载相关 skill，结合用户语境产出**结构化、可执行、可追溯**的输出（不是泛泛建议）

例如 `/write-prd` 跑出来的 PRD 是 8 段标准结构（问题 / 用户 / 目标 / 非目标 / 需求 / 验收 / 风险 / 里程碑），不是自由发挥的散文。

---

## 九、适用边界

**适合**：
- 产品经理 / 创始团队需要"框架式"产出（PRD / OKR / 战略 / launch plan）
- 用 Claude Code / Cowork / Codex 做 PM 决策辅助
- 想让团队统一 PM 工作流（一次装，全员一致）
- 投资 / 咨询 / 内审场景——把 OST / Porter's 5 / PESTLE 跑在 Claude 上

**不适合**：
- 想要"AI 替我做所有 PM 决定"——pm-skills 给框架，决策还是你做
- 完全不接受 Claude Code 生态——skill 通用格式可以用，但 command 是 Claude 专有
- 没有基本 PM 基础认知——理解 OST / JTBD 需要前置知识

---

## 十、阅读路径

```bash
# 1. Claude Cowork 装
Customize → Browse plugins → + → Add marketplace from GitHub → phuryn/pm-skills

# 2. 跑一遍发现链
/discover 你的产品/想法

# 3. 把骨架写实
/strategy
/write-prd
/north-star
/plan-launch

# 4. 串联成工作流
/discover → /write-prd → /plan-launch → /north-star
```

如果你做 PM 但 Claude 一直在"自由发挥"——pm-skills 是把"PM 思维框架" 注入 AI 的最直接方式。
