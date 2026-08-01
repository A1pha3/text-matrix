---
title: "i-have-adhd：让编码代理停止堆话、立刻动手的输出风格"
date: 2026-08-02T02:59:48+08:00
slug: "ayghri-i-have-adhd-agent-output-style"
description: "ayghri/i-have-adhd 是一个 Agent Skills 标准下的输出风格插件，安装后让 Claude Code/Codex 等编码代理先给动作、再给步骤、不再讲礼貌套话；本质是把\"代理如何回答\"这件事从模型层移到技能描述层。"
draft: false
categories: ["技术笔记"]
tags: ["Agent Skills", "Claude Code", "Codex", "输出风格", "Prompt 工程"]
---

## 一句话判断

`ayghri/i-have-adhd` 不教代理"更聪明地写代码"，而是把"先给一句动作命令、再给三步可执行步骤、最后再补一句 Next"的输出形态**编码成一项标准技能**——任何遵循 Agent Skills 开放标准的代理（Claude Code、Codex 等）装上它就会自动切换输出风格，不需要修改模型或系统提示。

## 项目定位

仓库自我描述很直接：

> ADHD-friendly outputs. No ADHD diagnosis needed!

它的产品形态是一个 **输出风格插件**，不是文档库也不是工具集。README 里给出的 Before/After 对比把这个意图点得非常明白：

> **Before**：Great question! Let me think about this. Your auth flow has a few moving pieces: the middleware, the token verification, and the cookie handling. Looking at `src/auth.ts`, the `verifyToken` function (around lines 42-58) seems to be using an older `jsonwebtoken` API. One approach would be to update the package and rewrite that function. After making the change, you'd want to run the auth tests to confirm nothing breaks. By the way, you might also want to look at your dependency versions overall. Hope this helps! Let me know if you want to dig deeper.
>
> **After**：Run `npm install jsonwebtoken@latest`, then edit `src/auth.ts:42`.
>
> 1. Open `src/auth.ts`
> 2. Replace `verifyToken` (lines 42–58) with the snippet below
> 3. Run `npm test -- auth.spec.ts`
>
> Next: paste the first failing line if any test fails.

注意 After 形态的四要素：**Action first**（一句命令）、**Steps numbered**（3 步以内）、**No "Hope this helps!"**（去礼貌话）、**Next**（失败时该贴什么）。

## 安装与触发

```bash
# Claude Code
claude plugin marketplace add ayghri/i-have-adhd
claude plugin install i-have-adhd@i-have-adhd

# Codex
codex plugin marketplace add ayghri/i-have-adhd --ref main
codex plugin add i-have-adhd@i-have-adhd
```

触发方式有两种：

- **显式**：在 Claude Code 里输入 `/i-have-adhd`；在 Codex 里输入 `$i-have-adhd`
- **隐式**：代理在判断任务"适合这种输出"时自动加载该技能

如果想要"每次会话都自动开"，Claude Code 的做法是 `touch ~/.claude/.i-have-adhd-always`，详细说明在 `INSTALL.md`。

## 真正解决的问题：把风格搬出模型

过去想强制代理"少废话、直接动手"，只能改系统提示或定制一个模型副本。这种方式有两个问题：

1. **不可移植** —— 你在 Claude Code 上调好的风格，搬到 Cursor/Aider/Codex 又得重来
2. **很难分享** —— 个人偏好型的 prompt 没法进团队工具链

`i-have-adhd` 的解法是走 **Agent Skills 开放标准**：技能以描述文件 + 可选脚本的形式存在，代理在判断任务匹配时按需加载。这意味着：

- 同一份技能能在 Claude Code、Codex、Cursor、未来任何遵循标准的代理之间迁移
- 团队可以把"我们偏好的输出风格"做成内部 skill 仓库，新人 onboarding 时一键加载
- 风格本身是可读的 Markdown，可以放进 code review

## 与 `pbakaus/impeccable`、`emilkowalski/skills` 的关系

- `pbakaus/impeccable`：前端设计的品味/审美技能
- `emilkowalski/skills`：动画/UI 微决策技能
- `ayghri/i-have-adhd`：回答结构/信息密度的技能

三件套一起用，代理在写 UI 代码时会同时拿到"漂亮"（impeccable + emilkowalski）、"清晰"（i-have-adhd）两套约束。

## 适用边界与不适用边界

**适用**：

- 已经被 Claude/Codex 的"长篇套话"消耗太多耐心的工作流
- 团队希望统一所有成员看到的代理输出形态
- 需要把 prompt 工程沉淀成可分享的资产（而不是每次重新写）

**不适用**：

- 必须让代理"先做计划再行动"的教学/演示场景（After 形态跳过了 Plan 段）
- 需要保留大量礼貌话术来通过外部审查的产品发布场景
- 期待它影响模型自身行为（它只影响 *回答形态*，不改变模型判断）