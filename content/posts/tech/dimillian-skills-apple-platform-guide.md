---
title: "Dimillian/Skills：Apple 平台智能体技能集合完全指南"
date: "2026-04-01T01:21:00+08:00"
slug: "dimillian-skills-apple-platform-guide"
description: "深度解析 Dimillian/Skills (3.3k Stars)：专注于 Apple 平台开发的可复用智能体技能集合，包含16个核心技能，覆盖App Store发布、SwiftUI重构、代码审查、bug调查等领域，采用自包含设计，每个技能独立完整可单独使用。"
draft: false
categories: ["技术笔记"]
tags: ["Dimillian", "Skills", "Apple", "SwiftUI", "iOS", "macOS", "Codex", "智能体技能", "代码审查", "Bug调查"]
---

# Dimillian/Skills：Apple 平台智能体技能集合完全指南

## §1 学习目标

完成本文档后，你将能够：

- ✅ 理解 Dimillian/Skills 的定位与设计理念
- ✅ 掌握 16 个核心技能的功能与用途
- ✅ 安装与配置 Dimillian/Skills
- ✅ 在 Codex 环境中使用各类技能
- ✅ 根据项目需求选择合适的技能
- ✅ 为团队创建自定义技能

---

## §2 项目概述

### 2.1 什么是 Dimillian/Skills？

**Dimillian/Skills**（[GitHub 仓库](https://github.com/Dimillian/Skills)）是由开发者 Dimillian 创建的 **Codex 技能集合**，用于 Apple 平台开发、GitHub 工作流、重构、代码审查和 bug 调查等场景。

**官方描述**：

> A collection of reusable development skills for Apple platforms, GitHub workflows, refactoring, diff review swarms, bug investigation swarms, code review, React performance work, and skill curation.

**官网**：[dimillian.github.io/Skills/](https://dimillian.github.io/Skills/)

### 2.2 核心数据

| 指标 | 数值 |
|------|------|
| **Stars** | 3.3k (3,323) |
| **Forks** | 144 |
| **Watchers** | 31 |
| **提交数** | 55 |
| **Issues** | 1 |
| **Pull Requests** | 4 |
| **许可证** | MIT |
| **语言** | Shell 84.6%, Python 12.8%, Swift 2.6% |

### 2.3 设计理念

Dimillian/Skills 的设计遵循以下原则：

| 原则 | 说明 |
|------|------|
| **聚焦性** | 每个技能有清晰、单一的目的 |
| **自包含** | 每个技能独立完整，可单独使用 |
| **可复用** | 设计为通用场景，方便复用 |
| **文档完善** | 每个技能包含详细的 SKILL.md |

### 2.4 与其他 Skills 项目的区别

| 项目 | 特点 |
|------|------|
| **alirezarezvani/claude-skills** | 通用型，覆盖多个 AI 平台 |
| **slavingia/skills** | Minimalist Entrepreneur 风格 |
| **Dimillian/Skills** | 专注 Apple 平台和 SwiftUI |

---

## §3 核心技能详解

### 3.1 App Store Changelog

**文件夹**: `app-store-changelog`

**功能**: 从 git 历史创建用户友好的 App Store 发布说明。

**工作流程**:
1. 收集自上次 tag 以来的更改
2. 过滤用户可见的工作
3. 重写为简洁的"What's New"要点

**使用场景**: 自动化发布说明生成，减少手动编写工作量。

---

### 3.2 GitHub

**文件夹**: `github`

**功能**: 使用 `gh` CLI 检查和操作 GitHub issues、pull requests、workflow runs 和 API 数据。

**能力**:
- CI checks 检查
- Run logs 获取
- 高级查询

**使用场景**: 自动化 GitHub 管理和 CI/CD 监控。

---

### 3.3 iOS Debugger Agent

**文件夹**: `ios-debugger-agent`

**功能**: 使用 XcodeBuildMCP 构建、启动和调试当前 iOS 应用。

**能力**:
- UI 检查
- 交互操作
- 截图捕获
- 日志获取

**使用场景**: iOS 应用调试和 UI 检查。

---

### 3.4 macOS Menubar Tuist App

**文件夹**: `macos-menubar-tuist-app`

**功能**: 构建、重构或审查使用 Tuist 和 SwiftUI 的 macOS menubar 应用。

**重点**:
- Manifest ownership
- Store-layer architecture
- 可靠的本地启动脚本

**使用场景**: macOS menubar 应用开发。

---

### 3.5 macOS SwiftPM App Packaging (No Xcode)

**文件夹**: `macos-spm-app-packaging`

**功能**: 搭建、构建、打包、签名和可选地公证 SwiftPM基础的 macOS 应用。

**优势**: 无需 Xcode 项目即可完成打包。

**使用场景**: SwiftPM 项目的自动化打包。

---

### 3.6 Orchestrate Batch Refactor

**文件夹**: `orchestrate-batch-refactor`

**功能**: 规划和执行大型重构或重写工作。

**特点**:
- 依赖感知的并行分析
- 使用明确范围的工作数据包
- 并行实现

**使用场景**: 大型代码库的重构管理。

---

### 3.7 Project Skill Audit

**文件夹**: `project-skill-audit`

**功能**: 分析项目的 Codex 会话、memory、现有本地技能和约定。

**输出**: 推荐最高价值的新技能或对现有技能的更新建议。

**使用场景**: 技能优化和团队效率提升。

---

### 3.8 React Component Performance

**文件夹**: `react-component-performance`

**功能**: 诊断慢速 React 组件性能问题。

**诊断范围**:
- Re-render churn（重新渲染抖动）
- Expensive render work（昂贵渲染工作）
- Unstable props（不稳定 props）
- List bottlenecks（列表瓶颈）

**输出**: 有针对性的优化建议和验证步骤。

**使用场景**: React 应用性能优化。

---

### 3.9 Bug Hunt Swarm

**文件夹**: `bug-hunt-swarm`

**功能**: 运行只读四智能体 bug 调查。

**调查重点**:
- 复现（Reproduction）
- 代码路径追踪（Code-path tracing）
- 回归者（Regressors）
- 最快证明步骤（Fastest proof step）

**输出**: 排名靠前的根因路径。

**使用场景**: 复杂 bug 的系统性调查。

---

### 3.10 Review and Simplify Changes

**文件夹**: `review-and-simplify-changes`

**功能**: 审查 git diff 或显式文件范围。

**审查维度**:
- 复用性（Reuse）
- 代码质量（Code quality）
- 效率（Efficiency）
- 清晰度（Clarity）
- 标准问题（Standards issues）

**可选**: 应用安全的、保留行为的修复。

**使用场景**: 代码审查和重构。

---

### 3.11 Review Swarm

**文件夹**: `review-swarm`

**功能**: 运行只读四智能体 diff 审查。

**审查重点**:
- 行为回归（Behavioral regressions）
- 安全风险（Security risks）
- 性能或可靠性问题（Performance/reliability issues）
- 合同或测试覆盖差距（Contract/test coverage gaps）

**输出**: 优先级修复路径。

**使用场景**: 自动化代码审查。

---

### 3.12 Swift Concurrency Expert

**文件夹**: `swift-concurrency-expert`

**功能**: 审查和修复 Swift 6.2+ 并发问题。

**问题类型**:
- Actor isolation problems
- Sendable violations
- Main-actor annotations
- Data-race diagnostics

**使用场景**: Swift 并发代码审查。

---

### 3.13 SwiftUI Liquid Glass

**文件夹**: `swiftui-liquid-glass`

**功能**: 实现、审查或重构 SwiftUI 功能以正确使用 iOS 26+ Liquid Glass API。

**重点**:
- 正确的 modifier 顺序
- 分组（Grouping）
- 交互性（Interactivity）
- 回退（Fallbacks）

**使用场景**: iOS 26+ 新 API 采用。

---

### 3.14 SwiftUI Performance Audit

**文件夹**: `swiftui-performance-audit`

**功能**: 从代码和架构审核 SwiftUI 运行时性能。

**审核重点**:
- Invalidation storms（失效风暴）
- Identity churn（身份抖动）
- Layout thrash（布局抖动）
- Heavy render work（重型渲染工作）
- Profiling guidance（性能分析指导）

**使用场景**: SwiftUI 性能诊断。

---

### 3.15 SwiftUI UI Patterns

**文件夹**: `swiftui-ui-patterns`

**功能**: 为构建 SwiftUI 屏幕和组件提供最佳实践和示例驱动的指导。

**覆盖范围**:
- 导航（Navigation）
- Sheets
- App wiring
- Async state
- 可复用 UI 模式

**使用场景**: SwiftUI 开发规范。

---

### 3.16 SwiftUI View Refactor

**文件夹**: `swiftui-view-refactor`

**功能**: 将 SwiftUI 视图文件重构为更小的子视图。

**目标**:
- 更小的子视图（Smaller subviews）
- MV 风格数据流
- 稳定视图树（Stable view trees）
- 显式依赖注入（Explicit dependency injection）
- 正确的 Observation 使用

**使用场景**: SwiftUI 代码重构。

---

## §4 安装与配置

### 4.1 安装方式

**方式一：复制到 CODEX_HOME**

```bash
# 克隆仓库
git clone https://github.com/Dimillian/Skills.git

# 复制技能文件夹到 Codex skills 目录
cp -r Skills/* $CODEX_HOME/skills/
```

**方式二：直接使用**

每个技能文件夹都是独立的，可以直接复制需要的使用。

### 4.2 环境要求

| 要求 | 说明 |
|------|------|
| **Codex** | 需要 Codex 环境 |
| **gh CLI** | GitHub 技能需要 |
| **XcodeBuildMCP** | iOS Debugger Agent 需要 |
| **Swift 6.2+** | Swift Concurrency Expert 需要 |

### 4.3 目录结构

```
Skills/
├── app-store-changelog/       # App Store 发布说明生成
├── bug-hunt-swarm/           # Bug 调查 Swarm
├── docs/                       # 文档
├── github/                    # GitHub CLI 集成
├── ios-debugger-agent/        # iOS 调试 Agent
├── macos-menubar-tuist-app/   # macOS Menubar 应用
├── macos-spm-app-packaging/   # SwiftPM 打包
├── orchestrate-batch-refactor/ # 批量重构编排
├── project-skill-audit/        # 技能审计
├── react-component-performance/ # React 性能
├── review-and-simplify-changes/ # 代码审查简化
├── review-swarm/              # 审查 Swarm
├── scripts/                   # 脚本
├── swift-concurrency-expert/  # Swift 并发专家
├── swiftui-liquid-glass/     # SwiftUI Liquid Glass
├── swiftui-performance-audit/  # SwiftUI 性能审核
├── swiftui-ui-patterns/       # SwiftUI UI 模式
└── swiftui-view-refactor/    # SwiftUI 视图重构
```

---

## §5 使用方法

### 5.1 基本使用

每个技能都是自包含的，参考每个技能目录中的 `SKILL.md` 文件获取：

- 触发器（Triggers）
- 工作流程指导（Workflow guidance）
- 示例（Examples）
- 支持参考资料（Supporting references）

### 5.2 技能选择指南

| 任务类型 | 推荐技能 |
|----------|----------|
| **App Store 发布** | App Store Changelog |
| **GitHub 管理** | GitHub |
| **iOS 调试** | iOS Debugger Agent |
| **macOS Menubar 开发** | macOS Menubar Tuist App |
| **SwiftPM 打包** | macOS SwiftPM App Packaging |
| **大型重构** | Orchestrate Batch Refactor |
| **技能优化** | Project Skill Audit |
| **React 性能** | React Component Performance |
| **Bug 调查** | Bug Hunt Swarm |
| **代码审查** | Review and Simplify Changes |
| **Diff 审查** | Review Swarm |
| **Swift 并发** | Swift Concurrency Expert |
| **iOS 26 API** | SwiftUI Liquid Glass |
| **SwiftUI 性能** | SwiftUI Performance Audit |
| **SwiftUI 规范** | SwiftUI UI Patterns |
| **SwiftUI 重构** | SwiftUI View Refactor |

---

## §6 技能开发指南

### 6.1 设计原则

添加新技能时，确保：

| 原则 | 说明 |
|------|------|
| **清晰单一目的** | Have a clear, single purpose |
| **全面文档** | Include comprehensive documentation |
| **一致模式** | Follow consistent patterns with existing skills |
| **参考材料** | Include reference materials when applicable |

### 6.2 技能结构

每个技能应包含：

```
skill-name/
├── SKILL.md          # 核心文档
├── triggers.md       # 触发器（可选）
├── references/        # 参考资料（可选）
└── scripts/          # 支持脚本（可选）
```

### 6.3 SKILL.md 结构

```markdown
# Skill Name

## Purpose
[清晰描述技能目的]

## Triggers
[触发条件]

## Workflow
[工作流程]

## Examples
[使用示例]

## References
[参考资料]
```

---

## §7 Apple 平台开发技能

### 7.1 SwiftUI 相关技能

| 技能 | 用途 |
|------|------|
| SwiftUI Liquid Glass | iOS 26+ 新 API |
| SwiftUI Performance Audit | 性能诊断 |
| SwiftUI UI Patterns | 最佳实践 |
| SwiftUI View Refactor | 代码重构 |
| Swift Concurrency Expert | 并发问题 |

### 7.2 macOS 相关技能

| 技能 | 用途 |
|------|------|
| macOS Menubar Tuist App | Menubar 应用开发 |
| macOS SwiftPM App Packaging | 无 Xcode 打包 |

### 7.3 iOS 相关技能

| 技能 | 用途 |
|------|------|
| iOS Debugger Agent | iOS 应用调试 |

---

## §8 代码审查技能

### 8.1 单一审查

| 技能 | 用途 |
|------|------|
| Review and Simplify Changes | diff 审查和简化 |
| React Component Performance | React 性能审查 |

### 8.2 Swarm 审查

| 技能 | 用途 |
|------|------|
| Review Swarm | 四智能体 diff 审查 |
| Bug Hunt Swarm | 四智能体 bug 调查 |

---

## §9 DevOps 技能

### 9.1 GitHub 集成

| 技能 | 用途 |
|------|------|
| GitHub | GitHub CLI 操作 |

### 9.2 发布自动化

| 技能 | 用途 |
|------|------|
| App Store Changelog | 发布说明生成 |

---

## §10 最佳实践

### 10.1 技能选择

| 实践 | 说明 |
|------|------|
| **按需选择** | 根据任务类型选择合适的技能 |
| **组合使用** | 多个技能可以组合使用 |
| **自定义** | 根据团队需求修改技能 |

### 10.2 技能维护

| 实践 | 说明 |
|------|------|
| **定期更新** | 保持技能与最新工具同步 |
| **文档完善** | 更新 SKILL.md |
| **反馈改进** | 根据使用反馈优化 |

### 10.3 团队协作

| 实践 | 说明 |
|------|------|
| **共享技能库** | 在团队中共享自定义技能 |
| **规范命名** | 使用清晰的命名规范 |
| **版本控制** | 跟踪技能变更历史 |

---

## §11 常见问题

### Q1：如何选择技能？

根据任务类型选择合适的技能，参考第 5.2 节的技能选择指南。

### Q2：技能需要特殊配置吗？

大多数技能开箱即用，部分技能需要额外工具（如 gh CLI、XcodeBuildMCP）。

### Q3：可以自定义技能吗？

可以。每个技能都是自包含的，可以根据需求修改。

### Q4：支持其他平台吗？

Dimillian/Skills 主要专注 Apple 平台和 SwiftUI，社区可能有其他平台的技能。

### Q5：如何贡献新技能？

参考第 6 节的设计指南，确保技能有清晰目的、完善文档和一致模式。

---

## §12 总结

### 12.1 核心优势

| 优势 | 说明 |
|------|------|
| **专注 Apple** | 深度集成 Apple 平台开发 |
| **多智能体** | Review Swarm 和 Bug Hunt Swarm |
| **自包含** | 每个技能独立完整 |
| **可复用** | 设计为通用场景 |

### 12.2 适用场景

| 场景 | 适用技能 |
|------|----------|
| **iOS 开发** | iOS Debugger Agent, SwiftUI 系列 |
| **macOS 开发** | macOS Menubar Tuist App, SwiftPM Packaging |
| **代码审查** | Review Swarm, Review and Simplify Changes |
| **Bug 调查** | Bug Hunt Swarm |
| **性能优化** | React Component Performance, SwiftUI Performance Audit |
| **发布准备** | App Store Changelog |
| **GitHub 管理** | GitHub |

### 12.3 项目信息

| 项目 | 信息 |
|------|------|
| **Stars** | 3.3k |
| **Forks** | 144 |
| **许可证** | MIT |
| **语言** | Shell 84.6%, Python 12.8%, Swift 2.6% |

### 12.4 相关链接

| 资源 | 链接 |
|------|------|
| **GitHub** | https://github.com/Dimillian/Skills |
| **官网** | https://dimillian.github.io/Skills/ |

---

*文档版本 1.0 | 撰写日期：2026-04-01 | 基于 Dimillian/Skills (3.3k Stars)*