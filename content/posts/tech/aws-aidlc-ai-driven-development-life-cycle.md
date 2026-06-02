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

## 这篇文章在讲什么

AI-DLC（AI-Driven Development Life Cycle）是 AWS Labs 发布的一套自适应编码工作流规范，托管在 [awslabs/aidlc-workflows](https://github.com/awslabs/aidlc-workflows)（GitHub 星标 1,703，MIT No Attribution 协议）。

它解决的问题很具体：Claude Code、Cursor 这类 AI 编码助手灵活度极高，你可以让它做任何事，但执行顺序和质量完全依赖单次 prompt。同一个需求，不同的人、不同的措辞，产出可能天差地别。AI-DLC 把"好的 AI 编码流程应该长什么样"写成了一组可加载的规则文件，让 AI 每次接任务时都走同一套流程——先理解上下文，再规划步骤，最后验证结果。

你可以把它理解为 IDE 里的一组"方向盘规则"：它不改变 AI 的能力，只约束 AI 做事的顺序。目前支持的平台包括 Kiro、Amazon Q Developer、Cursor、Cline、Claude Code、GitHub Copilot 和 OpenAI Codex。

### 三阶段工作流总览

AI-DLC 的核心是一个三阶段循环，每次任务执行都会经过这三个阶段：

| 阶段 | 做什么 | 关键输出 |
|------|--------|----------|
| Phase 1：理解与分析 | 扫描代码库结构、识别依赖和风险、评估复杂度 | 任务分析报告 + 用户需确认的决策点 |
| Phase 2：规划与执行 | 分解为可验证的子任务、逐步实施、关键变更前请求确认 | 增量修改 + 每步验证记录 |
| Phase 3：验证与交付 | 运行测试、检查代码风格、回归验证 | 变更摘要 + 可 review 的交付物 |

下面展开每个阶段的具体内容，然后通过一个具体任务看这三个阶段如何串在一起。

---

## 三阶段自适应工作流

AI-DLC 的核心是一个三阶段循环：

### Phase 1：理解与分析（Understand & Analyze）

AI 接到任务后不会直接动手，而是先做一轮上下文采集：扫描代码库的目录结构和现有依赖，标记可能受影响的模块，判断任务是否需要引入外部库或环境变更。如果任务复杂度较高，Phase 1 还会给出分步建议，避免一口吃成胖子。

这一阶段的产物是一份**任务分析报告**，包含：

- 当前代码库中与任务相关的关键路径
- 可能产生冲突或副作用的区域
- 推荐的实现方案
- 需要用户拍板的关键决策点（比如：要不要升级某个依赖、是否采用破坏性 API 变更）

Phase 1 的本质是把"让我先看看"这件事变成结构化的输入，而不是让 AI 凭直觉跳进实现。

### Phase 2：规划与执行（Plan & Execute）

Phase 1 的报告通过后，进入执行。这一阶段的核心约束是：**每一步都要可验证**。

复杂任务会被拆成多个子任务，AI 在每一步开始前先说明意图，执行后立即检查结果。遇到破坏性操作（删文件、改数据库 schema、批量重命名等），规则要求 AI 在动手前等用户确认。代码修改优先走增量路线——能 patch 的不重写整个文件，降低回滚成本。

### Phase 3：验证与交付（Verify & Deliver）

所有改动完成后，AI 走一轮系统性验证：跑项目已有的测试、检查代码风格是否与项目规范一致、做一轮回归确认没有引入新问题。最后输出一份变更摘要，列出改了哪些文件、为什么改、有什么需要注意的地方，方便人类 review。

### 一个具体任务如何流过三个阶段

假设你在一个 Python 项目中要求 AI "给用户模块加上邮箱验证功能"。在 AI-DLC 规则下，AI 的执行路径大致是：

1. **Phase 1**：AI 先扫描 `users/` 目录，发现已有 `User` 模型使用 SQLAlchemy，依赖 `flask-mail` 但未配置。分析报告会标注：需要新增 `email_verified` 字段和验证令牌表，建议生成迁移脚本，并询问你"是否沿用 flask-mail 还是换成其他邮件服务"。
2. **Phase 2**：你确认方案后，AI 先创建数据库迁移、再添加验证令牌模型、再写邮件发送逻辑、最后改注册流程——每一步都先说明意图再执行，在执行"修改 User 模型"这种会影响全表的操作前等待确认。
3. **Phase 3**：AI 运行 `pytest users/`，检查 `.flake8` 规范，确认所有已有测试仍然通过，然后输出变更摘要：改了哪些文件、新增了哪些端点、迁移脚本的 up/down 逻辑。

这个例子里的关键不在于 AI 能不能写出验证逻辑（没有 AI-DLC 也能写），而在于整个过程不再依赖你单次 prompt 的质量——规则文件替你把关"先分析再动手、重要操作要确认、做完要验证"这三件事。

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

AI-DLC 的规则分两层：

**核心规则（aws-aidlc-rules/）**：定义工作流的主要阶段和阶段间的转换条件。每次任务执行都会加载这一层。

**条件规则（aws-aidlc-rule-details/）**：当核心规则触发特定场景时按需加载。比如检测到"删除文件"操作，加载删除确认流程；检测到"修改依赖"，加载依赖变更检查清单。

两层分开的原因是：核心规则本身很轻量、普遍适用；条件规则只在实际触发时才读入，避免每次任务加载全部规则导致上下文膨胀。

---

## 什么时候该用，什么时候可以跳过

**值得加载 AI-DLC 的场景：**

**改动大、依赖多的代码库**。当你需要在一个模块相互纠缠的项目里做修改时，Phase 1 的分析能提前标出可能的副作用区域，减少"改完才发现漏了五个地方"的概率。

**多人各自用 AI 编码助手的项目**。不同的人用不同的工具，但分析报告和变更摘要都走同一套格式，人类 review 时不必重新理解"AI 是怎么想的"。

**高强度 AI 辅助开发**。如果你每天大量使用 AI 编码工具，三阶段流程可以减少"做到一半发现方向错了"的返工。

**可以跳过 AI-DLC 的场景：**

- 快速验证想法——只是想看看某个 API 能不能用、某个方案能不能跑通，不需要走完整流程。
- 单行修改——改一个变量名、加一句日志，这类任务的成本在流程约束本身。
- 团队已有成熟的工作流规范和 CI/CD——AI-DLC 是补充，不是替代。如果你的 CI/CD 已经覆盖了测试和风格检查，Phase 3 的价值会打折，但 Phase 1 和 Phase 2 的约束仍然有用。

---

## 与其他工具的关系

AI-DLC 不替代任何 AI 编码工具，它工作在工具之上——约束工具的行为，而不是提供编码能力。

| 层级 | 代表 | 做什么 |
|------|------|--------|
| 编码执行层 | Claude Code、Cursor、GitHub Copilot | 生成代码、修改文件、运行命令 |
| 流程规范层 | AI-DLC (aidlc-workflows) | 定义执行顺序、检查点、确认机制 |
| 质量保障层 | GitHub Actions、CI/CD 流水线 | 自动化测试、构建、部署 |

三层各司其职：AI-DLC 管的是 AI 在动手之前和动手之后应该做什么，不替代 CI/CD 的自动化检查，也不替代编码工具本身的代码生成能力。

---

## 从哪里开始

AI-DLC 的价值取决于你的日常开发模式与三阶段流程的重合度。以下几点可以作为判断参考：

- **个人开发者**：如果你已经在用 Claude Code 或 Cursor 做日常开发，建议先试一周——把规则文件加载进去，对比加载前后的任务执行质量。重点关注"AI 是否更少跳步"和"返工率是否下降"。
- **小团队（2-5 人）**：AI-DLC 的统一分析报告格式对 review 效率的提升最明显。建议从核心规则开始，条件规则按需逐步引入。
- **已有成熟 CI/CD 的团队**：Phase 1 和 Phase 2 的约束仍然适用，Phase 3 的部分检查点可能与现有 CI/CD 重复。可以先加载前两个阶段的规则，观察效果再决定是否启用完整三阶段。

如果你只是想试试水，从 Kiro 或 Cursor 入手最简单——这两个平台对 Steering Files 的支持最原生。Claude Code 用户需要通过环境变量或配置文件加载，GitHub Copilot 和 OpenAI Codex 需要额外配置，起步成本稍高。

**延伸阅读**：

- AWS 官方博客：https://aws.amazon.com/blogs/devops/ai-driven-development-life-cycle/
- 方法论论文：https://prod.d13rzhkk8cj2z0.amplifyapp.com/
- GitHub 仓库：https://github.com/awslabs/aidlc-workflows