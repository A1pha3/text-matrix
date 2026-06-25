---
title: "gstack：Garry Tan 的 AI 原生开发环境，23 个专家级工具装进 Claude Code"
date: "2026-05-14T20:33:50+08:00"
slug: "gstack-garry-tan-claude-code-setup"
description: "gstack 是 Y Combinator CEO Garry Tan 开源的个人开发工具集，将 Claude Code 打造成虚拟工程团队：CEO、设计师、架构师、安全审查员、QA 等 23 个专家角色，8 个强力命令，全部 MIT 协议免费使用。"
draft: false
categories: ["技术笔记"]
tags: ["AI辅助开发", "Claude Code", "YC", "生产力工具", "开源"]
---

## 快速信息卡

| 项目 | 信息 |
|------|------|
| 仓库 | [garrytan/gstack](https://github.com/garrytan/gstack) |
| Stars | 114,941+ |
| Forks | 16,992+ |
| License | MIT |
| 语言 | TypeScript |
| 依赖 | Claude Code |

## 学习目标

读完本文后，你应该能够：

1. **理解 gstack 的设计理念**：角色扮演式 AI 辅助开发框架的核心思想
2. **掌握 8 个核心命令**：`/design`、`/review`、`/test`、`/security`、`/ship`、`/explain`、`/refactor`、`/docs`
3. **评估适用性**：判断 gstack 是否适合您的开发流程
4. **理解性能数据**：看懂 Garry Tan 的 810 倍生产力数据的方法论
5. **规划采用路径**：如果决定采用，知道从哪一步开始

## 目录

1. [项目概览](#项目概览)
2. [背景：从「一个人像一支队伍」说起](#背景从一个人像一支队伍说起)
3. [核心设计理念](#核心设计理念)
4. [工具链组成](#工具链组成)
5. [性能数据](#性能数据)
6. [适用场景与局限](#适用场景与局限)
7. [常见问题](#常见问题)
8. [自测题](#自测题)
9. [进阶路径](#进阶路径)
10. [总结](#总结)

**gstack**（[garrytan/gstack](https://github.com/garrytan/gstack)）是 Y Combinator CEO Garry Tan 开源的 AI 开发工具集，旨在将 Claude Code 从一个代码补全工具扩展为完整的虚拟工程团队。23 个专家角色（CEO、设计师、架构师、安全审查员、QA、发布工程师等），8 个 slash 命令，全部 MIT 协议。⭐ 114,941 | 更新时间：2026-06-25

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

## 常见问题

### gstack 会替代我的判断吗？

不会。gstack 的每条命令都是「专家视角」的注入，不是自动执行。你需要主动调用 `/review`、`/security` 等命令，AI 才会以对应角色介入。最终决策权仍在你。

### 23 个角色是不是太多了？

对于个人开发者，不需要同时使用所有角色。Garry Tan 的建议是从 `/review` 和 `/refactor` 开始，这两个命令对代码质量的提升最直接。逐渐熟悉后，再引入 `/design`、`/security` 等。

### 为什么 LOC 数据有争议？

Garry Tan 在 [`docs/ON_THE_LOC_CONTROVERSY.md`](https://github.com/garrytan/gstack/blob/main/docs/ON_THE_LOC_CONTROVERSY.md) 中详细解释了方法论：他按「逻辑代码行」（排除注释、空行、AI 自动生成的 boilerplate）测量，而非原始 LOC。批评者混淆的正是这两个指标。

### gstack 能用于团队吗？

可以，但需要团队统一 Claude Code 的使用方式。gstack 本身是 prompt 模板和 slash 命令的集合，可以提交到版本控制，团队成员共享同一套「专家角色定义」。

### 如果 Claude Code 能力提升了，gstack 会过时吗？

不会。gstack 的设计是「角色定义 + prompt 模板」，当底层模型能力更强时，这些角色的效果会同步提升。实际上，模型越强，角色扮演越精准。

## 自测题

1. **gstack 的本质是什么？**
   - 答案：角色扮演式的 AI 辅助开发框架。每个角色都有明确的职责边界和决策视角。

2. **`/review` 和 `/refactor` 的区别是什么？**
   - 答案：`/review` 是代码审查，识别潜在 bug 和架构问题；`/refactor` 是在不改变功能的前提下优化代码结构。

3. **Garry Tan 的 810 倍数据是怎么算出来的？**
   - 答案：按逻辑代码行（排除注释、空行、AI 生成的 boilerplate）标准化后，对比 2013 年和 2026 年的产出速率。

4. **gstack 目前围绕哪个生态构建？**
   - 答案：Claude Code 生态。不支持其他模型（但 prompt 模板可迁移）。

5. **如果团队想采用 gstack，第一步应该做什么？**
   - 答案：将 gstack 的 slash 命令和 prompt 模板提交到版本控制，团队成员共享同一套配置。

## 进阶路径

### 阶段 1：熟悉单个命令

- 从 `/review` 开始，在每次提交前运行
- 逐渐加入 `/refactor`，优化已有代码
- 尝试 `/explain`，理解复杂代码段

### 阶段 2：构建个人工作流

- 将 gstack 命令集成到您的开发流程（如 Git hooks、PR 模板）
- 根据个人偏好调整 prompt 模板（在 `.Claude` 目录中）
- 结合其他 Claude Code 功能（如 `/compact`、`/cost`）

### 阶段 3：团队标准化

- 将 gstack 配置提交到团队仓库
- 定义团队统一的代码审查标准（通过 `/review` 的 prompt 模板）
- 定期同步团队对 gstack 角色的使用反馈

### 阶段 4：贡献和扩展

- 如果您的角色定义对别人也有用，提交 PR 给 gstack 上游
- 参考 gstack 的设计思路，为您自己的专业领域创建新角色（如 `/performance`、`/accessibility`）
- 在社区分享您的 prompt 工程经验

## 总结

gstack 代表了一种正在浮现的开发范式：当 AI 模型能力足够强时，工作流的组织方式开始成为新的竞争力来源。Garry Tan 将这套方法论开源，而非敝帚自珍，对于有兴趣系统化 AI 开发流程的团队和个人而言，是一份值得研究的一手素材——毕竟，这套工具的背后是一个同时运营 YC、在 60 天内交付了 3 个生产服务的人的真实工作流。