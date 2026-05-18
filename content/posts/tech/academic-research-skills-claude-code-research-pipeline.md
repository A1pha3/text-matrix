---
title: "academic-research-skills：Claude Code学术研究全套工作流"
date: "2026-05-18T19:56:00+08:00"
slug: "academic-research-skills-claude-code-research-pipeline"
description: "面向Claude Code的学术研究技能套件，覆盖从文献调研、论文写作、同行评审到定稿的完整学术研究流程，支持多智能体协作与引用真实性核验。"
categories: ["技术笔记"]
tags: ["Claude Code", "学术研究", "AI辅助写作", "文献综述", "论文评审", "Python", "智能体工作流"]
---

## 概述

[academic-research-skills](https://github.com/Imbad0202/academic-research-skills) 是一套为 Claude Code 打造的学术研究技能包，当前版本 v3.9.3，基于 CC BY-NC 4.0 协议开源。这套工具覆盖了学术研究的完整生命周期——从选题调研、文献综述、论文撰写、同行评审到最终定稿，提供了 13 个专项智能体协同工作。

该项目的核心设计理念是**人机协作而非全自动替代**。正如项目文档所引用的 Lu et al. (2026, Nature) 的研究结论，完全自主的 AI 研究系统存在实现 bug、结果幻觉、捷径依赖、bug 即洞见重新框架化、方法论伪造、帧锁定、引用幻觉等多种失效模式。ARS 正是基于这一前提，通过 Stage 2.5 和 Stage 4.5 两道Integrity Gate（完整性门控），在关键节点引入人类判断，避免上述问题。

## 核心功能

### 多阶段研究流水线

ARS 构建了一条 10 阶段的学术研究流水线：

1. **Deep Research** — 13 智能体研究团队，支持 Socratic 引导模式、PRISMA 系统性综述、意图检测与对话健康监控，可选跨模型双重确认
2. **Paper Writing** — 12 智能体论文写作引擎，包含风格校准（Style Calibration）、写作质量检查（Writing Quality Check）、LaTeX 强化、可视化生成与审稿教练
3. **Peer Review** — 7 智能体多视角同行评审，附 0–100 质量量表（EIC + 3 动态评审 + 魔鬼代言人），保留 concession 阈值协议
4. **Integrity Gate** — Stage 2.5 和 Stage 4.5 双门控，运行 7 模式拦截清单（含 claim-not-supported、fabricated-reference、anchorless 等高危类）

### 引用真实性核验

v3.8 引入了一个重要的功能：`ARS_CLAIM_AUDIT=1` 开关。开启后，系统会逐条拉取每个引用锚点对应的原始文献，判断论文中的 claim 是否被实际引用所支持。五类新增 HIGH-WARN 类（L3 风险等级）会硬性阻断格式化终端输出。项目使用三层引用定位符（locator anchors）实现可审计的引用链。

### 数据访问级别标注

v3.3.2 引入了一套元数据规范：每个技能需声明 `data_access_level`（`raw` / `redacted` / `verified_only`）与 `task_type`（`open-ended` 或 `outcome-gradable`），由 `scripts/check_data_access_level.py` 在 CI/CD 中强制执行。

## 安装与使用

```bash
# 通过 Claude Code plugin marketplace 安装
/plugin marketplace add Imbad0202/academic-research-skills
/plugin install academic-research-skills

# 启动 Socratic 引导式论文规划
/ars-plan

# 快速文献综述
/ars-lit-review "your research topic"
```

前置依赖：Claude Code CLI（v3.7.0+）、`ANTHROPIC_API_KEY` 环境变量。可选 Pandoc（DOCX 输出）与 tectonic + Source Han Serif TC（APA 7.0 PDF）。

## 性能与成本

完整流水线约消耗 450K–750K tokens（15K 词论文），按 Anthropic API 费率估算约 **$4–6 美元**。项目文档提供了详细的逐模式 token 预算与推荐配置（Skip Permissions；Agent Team 可选）。

## 实验智能体扩展

如果研究涉及代码实验或人类受试者实验，项目配套的 [experiment-agent](https://github.com/Imbad0202/experiment-agent) 技能填补了 Stage 1（RESEARCH）到 Stage 2（WRITE）之间的空缺——执行并管理实验、运行 IRB 伦理清单、解析统计结果并验证可复现性。

## 小结

academic-research-skills 是一套成熟的学术研究 AI 辅助框架，其分层门控设计（Integrity Gate）和引用审计机制（Claim Audit）直击当前 AI 辅助学术写作的核心痛点。对于需要严肃对待研究诚信的研究者而言，这套工具提供了可配置的防线，而非一把梭的"AI 代写"。当前 GitHub 星标约 3,800，今日新增约 1,400，仍在活跃维护中。