---
title: "gstack：Garry Tan 的 AI 原生开发环境，23 个专家级工具装进 Claude Code"
date: "2026-05-14T20:33:50+08:00"
slug: "gstack-garry-tan-claude-code-setup"
description: "gstack 是 Y Combinator CEO Garry Tan 开源的个人开发工具集，将 Claude Code 打造成虚拟工程团队：CEO、设计师、架构师、安全审查员、QA 等 23 个专家角色，8 个强力命令，全部 MIT 协议免费使用。"
draft: false
categories: ["技术笔记"]
tags: ["AI辅助开发", "Claude Code", "YC", "生产力工具", "开源"]
---

# gstack：Garry Tan 的 AI 原生开发环境，23 个专家级工具装进 Claude Code

## 项目概览

**gstack**（[garrytan/gstack](https://github.com/garrytan/gstack)）是 Y Combinator CEO Garry Tan 开源的 AI 开发工具集，旨在将 Claude Code 从一个代码补全工具扩展为完整的虚拟工程团队。23 个专家角色（CEO、设计师、架构师、安全审查员、QA、发布工程师等），8 个 slash 命令，全部 MIT 协议。⭐ 96,207 | 更新时间：2026-05-13

## 背景：从「一个人像一支队伍」说起

Garry Tan 在 2026 年 3 月的 No Priors 播客中提到，自 2025 年 12 月以来他几乎没手动写过一行代码，却完成了「以前一个团队才能做到」的工作量。他分析了 2013 年（构建 Bookface/Y Combinator 内部社交网络）和 2026 年的代码产出对比——以标准化后的逻辑代码行计，2026 年的产出速率是 2013 年的约 810 倍。

支撑这个结果的，正是 gstack 这套工具链。

## 核心设计理念

gstack 的本质是**角色扮演式的 AI 辅助开发框架**。每个角色都有明确的职责边界和决策视角：

| 角色 | 职责 |
|------|------|
| CEO | 重新审视产品方向，挑战现有假设 |
| Architect | 锁定架构决策，确保技术选型一致 |
| Designer | 识别 AI 生成的「平庸设计」，提升体验质量 |
| Eng Manager | 分解任务、评估进度、管理依赖 |
| Security Officer | 运行 OWASP + STRIDE 安全审计 |
| QA Lead | 启动真实浏览器进行端到端测试 |
| Release Engineer | 审核 PR、把关发布流程 |
| Doc Engineer | 撰写和维护文档 |

所有角色通过 Claude Code 的 slash 命令调用，无需切换工具或改变工作流。

## 工具链组成

8 个核心 slash 命令覆盖了开发全流程的关键节点：

- `/design` — 接收产品意图，输出设计评审意见
- `/review` — 代码审查，识别潜在 bug 和架构问题
- `/test` — 生成端到端测试并执行
- `/security` — 运行安全扫描
- `/ship` — 发布审核，模拟 release engineer 把关 PR
- `/explain` — 解释复杂代码段的技术含义
- `/refactor` — 在不改变功能的前提下优化代码结构
- `/docs` — 生成和维护项目文档

每个命令背后对应一套 prompt 模板和工具调用策略，目标是让 AI 在每个环节都以「该领域的专家」而非「通才」的方式介入。

## 性能数据

Garry Tan 在 README 中公开了完整的对比数据（附原始数据链接）：

- **2026 年前四个月**：已完成 240 倍于 2013 年全年的逻辑代码产出
- **60 天内**：3 个生产服务，40+ 功能特性，半职状态，同时全职运营 YC
- **指标**：按逻辑代码行（而非 raw LOC——后者会因 AI 补全而被显著高估）标准化后测量

他特别指出，LOC 批评者没有错——raw 行数确实会被 AI 膨胀。但他认为批评者混淆了两件事：标准化后的生产效率。他明确承认并附上了[完整方法论和复现脚本](https://github.com/garrytan/gstack/blob/main/docs/ON_THE_LOC_CONTROVERSY.md)，欢迎任何人验证。

## 适用场景与局限

**gstack 适合：**
- 希望将 AI 能力系统化、而非散点式使用个人开发者
- 需要在保持代码质量可控的前提下加速产出的独立 maker
- 想验证「AI 是否真的能提升工程效率」并希望获得可量化数据的团队

**需要注意的边界：**
- gstack 的效果高度依赖 Claude Code 的能力上限——当模型能力更强时，工具链的效果同步提升
- 23 个角色意味着较高的 prompt 工程复杂度，调优需要时间投入
- 该工具链目前围绕 Claude Code 生态构建，不支持其他模型（但 prompt 模板可迁移）

## 总结

gstack 代表了一种正在浮现的开发范式：当 AI 模型能力足够强时，工作流的组织方式开始成为新的竞争力来源。Garry Tan 将这套方法论开源，而非敝帚自珍，对于有兴趣系统化 AI 开发流程的团队和个人而言，是一份值得研究的一手素材——毕竟，这套工具的背后是一个同时运营 YC、在 60 天内交付了 3 个生产服务的人的真实工作流。