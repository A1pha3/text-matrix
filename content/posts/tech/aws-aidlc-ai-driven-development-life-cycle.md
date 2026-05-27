---
title: "AWS AI-DLC：自适应AI编码工作流规范"
date: "2026-05-09T03:25:00+08:00"
slug: "aws-aidlc-ai-driven-development-life-cycle"
aliases:
  - "/posts/tech/aidlc-workflows-ai-driven-lifecycle-automation/"
description: "AI-DLC（AI-Driven Development Life Cycle）是 AWS Labs 推出的自适应编码工作流规范，通过结构化的三阶段流程引导 AI 编码助手遵循开发最佳实践。它不是工具，而是一套可以在 Kiro、Amazon Q、Cursor、Cline、Claude Code 等主流 IDE 中使用的「方向盘规则」。"
draft: false
categories: ["技术笔记"]
tags: ["AWS", "AI编码", "工作流", "Claude Code", "Cursor"]
---

## 项目概览

AI-DLC（AI-Driven Development Life Cycle，https://github.com/awslabs/aidlc-workflows）是 AWS Labs 推出的**自适应编码工作流规范**，GitHub 星标 1,703，采用 MIT No Attribution 协议。

它的目标不是做一个新的 AI 编码工具，而是为**已有的 AI 编码助手**（Kiro、Amazon Q Developer、Cursor、Cline、Claude Code、GitHub Copilot、OpenAI Codex 等）提供一套「方向盘规则」，让它们在执行任务时遵循一致的开发流程和质量标准。

**核心思路**：AI 编码助手（如 Claude Code）的灵活度很高——你可以让它做任何事，但它可能以任何顺序、任何方式去做。AI-DLC 定义了一个工作流框架，确保它在「理解任务 → 执行方案 → 验证结果」的过程中保持一致性。

---

## 三阶段自适应工作流

AI-DLC 的核心是一个三阶段循环：

### Phase 1：理解与分析（Understand & Analyze）

AI 首先需要理解任务的上下文和约束：

- 分析代码库结构和现有依赖
- 识别任务的技术边界和风险点
- 确定是否需要外部依赖或环境变更
- 评估任务复杂度，决定是否需要分步执行

这个阶段的关键输出是一份**任务分析报告**，包括：
- 当前代码库的关键路径
- 可能的冲突或副作用
- 建议的实现方案
- 需要用户确认的关键决策点

### Phase 2：规划与执行（Plan & Execute）

基于 Phase 1 的分析，制定执行计划并逐步实施：

- 将复杂任务分解为可验证的子任务
- 每一步执行前说明意图，执行后验证结果
- 重要变更前先获取用户确认（特别是破坏性操作）
- 保持代码的可逆性，优先使用增量修改而非大范围重写

### Phase 3：验证与交付（Verify & Deliver）

执行完成后，进行系统性验证：

- 运行测试确保功能正确
- 检查代码风格与项目规范一致
- 验证没有引入新的问题（回归测试）
- 生成变更摘要供 review

---

## 使用方式：在 IDE 中加载规则

AI-DLC 通过**Kiro Steering Files**（方向盘文件）机制与主流 IDE 集成。你需要：

1. 下载最新 releases 中的 `ai-dlc-rules-v<release-number>.zip`
2. 解压到项目目录外（如 `~/Downloads`）
3. 将 `aws-aidlc-rules/` 复制到 IDE 的规则目录（如 `.kiro/steering/`）
4. 将 `aws-aidlc-rule-details/` 复制到项目根目录的 `.kiro/` 下

以 Kiro 为例（macOS/Linux）：
```bash
mkdir -p .kiro/steering
cp -R ~/Downloads/aidlc-rules/aws-aidlc-rules .kiro/steering/
cp -R ~/Downloads/aidlc-rules/aws-aidlc-rule-details .kiro/
```

支持的平台：
- **Kiro**：原生支持 Steering Files
- **Amazon Q Developer IDE Plugin**：通过规则文件引导
- **Cursor IDE**：读取 `.kiro/` 目录中的规则
- **Cline**：支持 Steering Files 格式
- **Claude Code**：通过环境变量或配置文件加载
- **GitHub Copilot**：需要额外配置
- **OpenAI Codex**：通过规则文件集成

---

## 规则结构

AI-DLC 的规则分为两层：

**核心规则（aws-aidlc-rules/）**：定义工作流的主要阶段和转换条件。这些规则在每个任务执行时都会被引用。

**条件规则（aws-aidlc-rule-details/）**：当核心规则触发时，按需加载的详细规则。比如当检测到「删除文件」操作时，加载「删除操作确认流程」；当检测到「修改依赖」时，加载「依赖变更检查清单」。

这种分层设计的好处是：核心规则是轻量的、普遍适用的，详细规则只在需要时才加载，避免每次任务都加载大量规则导致性能问题。

---

## 适用场景

### 适合使用 AI-DLC 的场景

**大型代码库的修改**：当需要在复杂代码库中做修改时，AI-DLC 的 Phase 1 分析可以避免遗漏重要的依赖关系和副作用。

**多人协作项目**：当多个开发者使用各自的 AI 编码助手时，AI-DLC 提供了一致的「交接语言」——AI 的分析报告和变更摘要都遵循同一格式，方便人类 review。

**高频 AI 辅助开发**：如果你每天大量使用 AI 编码工具，AI-DLC 的三阶段流程可以减少「做到一半发现方向错了」的情况。

### 不适合的场景

**快速探索性任务**：当你只是想让 AI 快速验证一个想法，不需要遵循完整流程。

**简单增量修改**：比如修改一个变量的命名、添加一行日志，这类简单任务不需要完整的分析-规划-验证循环。

**已有成熟流程的团队**：如果你的团队已经有完善的工作流规范和 CI/CD，AI-DLC 的价值在于补充而非替代现有流程。

---

## 与其他工具的区别

AI-DLC 不是另一个 AI 编码工具，它是一个**元工具**——用于规范其他工具的行为。

| 工具类型 | 代表 | 定位 |
|----------|------|------|
| AI 编码工具 | Claude Code、Cursor、Warp | 执行具体的编码任务 |
| AI-DLC | aidlc-workflows | 规范这些工具的执行流程 |
| CI/CD | GitHub Actions | 验证代码质量和自动化构建 |

打个比方：如果 AI 编码工具是赛车，AI-DLC 就是赛道规则——它不替代赛车，但定义了赛车应该怎么开。

---

## 总结与延伸

AI-DLC 代表了一个趋势：**随着 AI 编码工具的普及，如何规范它们的行为变得重要**。AI-DLC 通过三阶段工作流（理解 → 规划 → 执行 → 验证）提供了一套框架，适用于任何支持 Steering Files 的 AI 编码助手。

对于个人开发者，AI-DLC 提供了更好的任务执行保障；对于团队，它提供了 AI 行为的一致性语言。

**延伸阅读**：

- AWS 官方博客：https://aws.amazon.com/blogs/devops/ai-driven-development-life-cycle/
- 方法论论文：https://prod.d13rzhkk8cj2z0.amplifyapp.com/
- GitHub 仓库：https://github.com/awslabs/aidlc-workflows