---
title: "Claude Code Harness：给AI编程助手加一套有约束的交付流程"
date: 2026-05-28T09:15:00+08:00
slug: "claude-code-harness-disciplined-delivery-loop"
aliases:
  - "/posts/tech/chachamaru127-claude-code-harness-delivery-loop/"
description: "Claude Code Harness为Claude Code设计了一套有约束的交付流程：写Spec→实施→验证→独立Review→打包证据，支持Go原生内核和5个Skill动词，覆盖从首次提交到PR发布的完整交付闭环。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "AI编程", "工作流", "Skill", "软件开发"]
---

# Claude Code Harness：给AI编程助手加一套有约束的交付流程

Claude Code很强大，但原始的Agent工作容易漂移：计划在聊天里分散、测试变成可选项、Review来得很晚、发布证据靠记忆重建。**Claude Code Harness** 把这个过程收束成一条可重复的交付路径：写Spec → 实施 → 验证 → 独立Review → 打包证据。

这是一个Go语言原生内核的项目，支持Claude Code v2.1+、Codex和OpenCode。

## 核心循环：从"让AI写代码"到"让AI按合约交付"

Harness安装后，默认行为从"问Agent写代码"切换为：

1. **写Spec和Plan** —— Harness生成`spec.md`和`Plans.md`草稿，供你审查
2. **只实施已批准的切片** —— 不是一股脑全交给AI
3. **验证结果** —— 有明确的验证步骤
4. **独立Review** —— Review过程独立于实施过程
5. **为PR或Release打包证据** —— 输出物是可复查的文档

整个循环用一句话概括：**Plan. Work. Review. Ship.**

## 安装：30秒入门

```bash
claude
/plugin marketplace add Chachamaru127/claude-code-harness
/plugin install claude-code-harness@claude-code-harness-marketplace
/harness-setup
```

下一步，运行`/harness-plan`处理一个小请求：

```bash
/harness-plan Improve the README onboarding flow
```

Harness会为你生成`spec.md`和`Plans.md`草稿，你负责审批或纠正，再让AI按批准的内容执行。

## 前15分钟做什么

1. 通过你的工具路线安装
2. 运行`/harness-setup`或等效的安装脚本
3. 用一个小请求运行`/harness-plan`—— Harness生成合同草稿，你检查 Small typo、文档更新、状态变更保持轻量
4. 批准生成的合同，或回复你的修正意见
5. 运行最小已批准任务，例如`/harness-work 1.1.1`
6. 运行`/harness-review`，保留验证输出

**你的职责不是手写计划，而是批准或纠正生成的合同，再让执行继续。**

## 适用边界

- 适合：希望AI编程有纪律约束、需要可验证交付物、有明确PR/Sprint流程的团队
- 不适合：探索性原型快速验证（会拖慢速度）、完全不需要审查的简单脚本任务

## 关键Skill动词（5个）

| 动词 | 作用 |
|------|------|
| `/harness-plan` | 生成Spec和Plan合同草案 |
| `/harness-work` | 按批准切片执行任务 |
| `/harness-review` | 独立验证实施结果 |
| `/harness-setup` | 初始化Harness环境 |
| `/plugin` | 管理Marketplace上的Harness插件 |

## 总结

Claude Code Harness解决的不是"让AI写代码"的问题，而是"让AI按约束交付可验证代码"的问题。87颗星不算高，但它抓住了一个真实痛点：AI编程助手缺乏交付纪律。Go原生内核让它足够轻量，5个Skill动词覆盖了从计划到发布的完整闭环。

如果你在团队中使用Claude Code或类似工具感到"AI很能写但交付很散"，Harness是一套值得试的约束机制。