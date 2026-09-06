---
title: "ponytail：给 AI 编程代理装上「最懒资深工程师」的七级阶梯"
date: 2026-09-07T03:23:17+08:00
draft: false
description: 129k stars 的 DietrichGebert/ponytail 用一条 YAGNI 决策阶梯让 Claude Code 等 20 种代理少写约 54% 的代码、省 20% 成本且不牺牲安全性。本文拆解它的规则设计、基准方法论与适用边界。
categories: ["技术笔记"]
tags: ["ai-agent", "claude-code", "prompt-engineering", "yagni"]
github_repo: "DietrichGebert/ponytail"
source_key: "gh:DietrichGebert/ponytail"
slug : ponytail-lazy-senior-dev-decision-ladder
---

## 核心判断

AI 编程代理最常见的浪费不是写错，而是**写多**：要一个日期选择器，它装 flatpickr、包一层组件、加一个样式表，再跟你讨论时区。ponytail 的解法是把一位「公司里资历比版本控制还老、话最少、一行顶五十行」的资深工程师形象，做成一条注入给代理的决策阶梯。

结果有基准背书：在真实 FastAPI + React 仓库上跑 12 个 feature 任务（Claude Haiku 4.5，n=4），对比无 skill 基线，代码量均值 **-54%**、token -22%、成本 -20%、耗时 -27%，安全检查 100% 保留。它不是省 token 的奇技淫巧——规则明写「目标从来不是最少 token，而是只写任务需要的代码，验证、错误处理、安全、可访问性永远不上砍刀」。

129k stars、MIT、JavaScript，2026 年内从单 skill 长成覆盖 20 种代理的插件生态，是当前 trending 周榜月榜双热门。这类项目起量快、迭代也快，本文只锚定写作时点的 README 与基准报告。

## 规则本体：七级阶梯

ponytail 的全部魔力浓缩在写代码前依次落座的七级判断上：

```
1. 这东西需要存在吗？        → 不需要：跳过（YAGNI）
2. 本代码库里已经有了？      → 复用，不重写
3. 标准库能做？              → 用标准库
4. 平台原生特性能做？        → 用原生特性
5. 已安装的依赖能做？        → 用它
6. 一行能写完？              → 一行
7. 以上都不行：写「能工作的最小实现」
```

最出名的例子是日期选择器：

```html
<!-- ponytail: browser has one -->
<input type="date">
```

没有 flatpickr，没有 wrapper，没有时区讨论。基准里这个任务从 404 行降到 23 行；颜色选择器从 287 行降到 23 行。

一个容易被误读的细节：阶梯运行在代理**理解问题之后**，不是替代理解。README 原话是「对方案懒，对读代码从不懒」——代理仍要先读改动涉及的代码、追真实调用流，再决定落在哪一级。这把它和「少写点字」式的粗暴 prompt 区分开来。

## 基准方法论：一次诚实的自我纠错

ponytail 值得一读的部分是它如何被度量，尤其是它公开修正过自己。

**现行版本（agentic 基准）**：headless Claude Code 会话编辑真实仓库 fastapi/full-stack-fastapi-template，按留下的 `git diff` 计分；12 个 feature 工单，带/不带 skill 对比，n=4，Haiku 4.5，中位数报告。设了两个对照组：caveman（简短文风控制）和裸 "YAGNI + one-liners" prompt。结果 ponytail 是唯一在 LOC/tokens/cost/time 四项全面下降且安全性保持 100% 的组；裸 prompt 虽然也砍代码（-33%），但安全项掉到 95%。

**被废弃的旧版本（单次生成基准）**：早期报告「80-94% 少写」，issue #126 指出裸模型基线会用水文和选项凑篇幅，差距部分是对话基线假象。作者没有删数据，而是把旧版折进折叠块、标注为「不可辩护的旧数字」，并把 94% 重新定位为逐任务上限而非均值。

两点值得所有做 prompt/skill 基准的人抄走：**对照组要隔离文风与规则两种变量**（caveman 的存在就是为了证明「简短」本身不够）；**承认基线缺陷并公开修正是可信度的来源**。同时注意边界：削减幅度在「本来就该最小化」的任务上趋近于零；在爱思考的推理模型上（README 点名 GPT-5.5）反而可能因为思维链里反复权衡阶梯而更贵——它优化的是「遵守阶梯的模型」。

## 安装：三行以内的事

Claude Code（两条命令分两次发送）：

```
/plugin marketplace add DietrichGebert/ponytail
/plugin install ponytail@ponytail
```

Codex / Copilot CLI 同构：`codex plugin marketplace add DietrichGebert/ponytail` 或交互内 `/plugin` 两条。此外覆盖 OpenCode（opencode.json 加 `"plugin": ["@dietrichgebert/ponytail"]`）、Gemini CLI（`gemini extensions install`）、Pi（`pi install git:github.com/DietrichGebert/ponytail`）、Qoder（零配置读 AGENTS.md）等约 20 种 harness。

前提条件只有一条：Claude Code / Codex 的生命周期钩子需要 `node` 在非交互 shell 的 PATH 上（Nix/nvm 用户注意）；缺了也不报错，只是退化为非 always-on 激活。

## 模式与命令

四个力度档位：`lite / full / ultra / off`，外加六个斜杠命令——`/ponytail-review`（对已有 diff 按阶梯复检）、`/ponytail-audit`、`/ponytail-debt`、`/ponytail-gain` 等。日常挂在 full，遇到严格规格的活切 off 或 lite，是最省心的用法。

## 适用边界

- **适合**：UI 组件类、脚手架类、容易被代理过度设计的任务；按 token 计费的代理会话；团队想统一「先查有没有」的代码习惯。
- **不适合**：任务本身就是探索性原型、需要展示多种实现路径的教学场景；以及已在规格书里写死实现方式的工作——阶梯第 7 级之上的自由度不是它要解决的。
- **风险**：基准集中在 Haiku 4.5 单模型 + 单仓库，跨模型跨域的方差 README 自己也承认；「-54%」是均值，别当成承诺。

一句话收束：ponytail 证明了一件朴素的事——让代理少写代码的最有效手段，不是让它写得更用力，而是给它一张「先别写」的检查清单。
