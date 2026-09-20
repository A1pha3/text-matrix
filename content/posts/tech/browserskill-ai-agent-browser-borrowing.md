---
title: "BrowserSkill：让 AI Agent 借用你已登录的浏览器，而不是接管它"
date: 2026-09-21T04:00:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["BrowserSkill", "AI Agent", "浏览器自动化", "Tencent"]
description: "腾讯开源的 BrowserSkill 通过 CLI 守护进程加浏览器扩展，让任意 shell 型 AI Agent 复用真实登录态操作浏览器，以独立 Agent Window 和借还确认机制避免打断人的工作。"
github_repo: "Tencent/BrowserSkill"
source_key: "gh:Tencent/BrowserSkill"
slug : browserskill-ai-agent-browser-borrowing
---

## 核心判断

BrowserSkill 处理的是 AI Agent 落地里最别扭的一环：浏览器操作。现有方案要么让 Agent 驱动一个干净的自动化浏览器（没有登录态，什么都干不了），要么直接接管用户正在用的浏览器（Agent 一动，人就没法工作）。BrowserSkill 的答案是"借用"——Agent 在独立的可见窗口里操作，复用真实登录态，但必须显式借还标签页，其余浏览器活动不受干扰。

它的第二个关键决策是不绑定任何 Agent 框架：只要有 shell 就能用 `bsk` CLI。Cursor、Claude Code、Codex、OpenClaw、CodeBuddy 等均已适配，这个"Agent 无关"的定位让它更接近基础设施，而非某个生态的插件。

## 项目概览

| 项 | 数据（2026-09-20 取自 GitHub） |
|---|---|
| 仓库 | [Tencent/BrowserSkill](https://github.com/Tencent/BrowserSkill) |
| 定位 | Let AI agents use your real, logged-in browser without interrupting your work |
| Stars / Forks | 6,017 / 429 |
| 主语言 | TypeScript |
| License | MIT |
| 活跃度 | 当天（2026-09-20）仍有多个 PR 合入，迭代密集 |
| 运行形态 | `bsk` CLI/守护进程 + 浏览器扩展，两部分本地运行 |

运行环境覆盖 macOS（Apple Silicon 与 Intel）、Linux（x64/ARM64）、Windows x64；浏览器支持 Chrome 与 Edge，Firefox 在计划中。

## 架构：三个设计点

### 1. 借用而非接管

Agent 需要操作你已打开的某个标签页时，必须显式借用（borrow），任务完成后归还，期间你的浏览器其余部分照常使用。浏览器任务跑在独立的、可见的 Agent Window 中——你可以全程盯着 Agent 在做什么，而不是黑盒里猜。

### 2. 内建 human-in-the-loop

任务撞上验证码、登录、确认对话框这类只有人能处理的步骤时，Agent 可以发起求助（request help），人处理完后 Agent 继续完成余下任务。注意 0.3.0 起的变更：`--unattended`、`tab borrow --no-confirm` 等 CLI 参数不再绕过确认——是否确认借用、是否允许求助，改由扩展设置中的两个独立开关控制，且以用户保存的浏览器设置为准。这是明显把控制权从 Agent 侧收回用户侧的安全收紧。

### 3. Skill 分发机制

`bsk install-skill` 把官方 SKILL.md 安装进各 Agent 框架的 skills 目录，教会框架如何调用 `bsk`。值得留意其同步策略：守护进程启动、会话建立和 `doctor` 会自动更新托管技能，但只更新内容仍与上次安装版本一致的副本——用户本地改过就暂停自动更新并保留修改。对定制工作流的人来说，这比"每次升级覆盖"友好得多。

## 快速上手

已经用 Cursor / Claude Code / Codex 等 shell 型 Agent 的用户，官方推荐把这一行直接发给 Agent，让它照文档完成安装：

```text
Set up browser-skill on this machine by following https://raw.githubusercontent.com/Tencent/BrowserSkill/main/AGENT_INSTALL.md
```

手动安装三步（命令取自 README）：

```bash
# 1. 安装 bsk CLI（macOS/Linux）
curl -fsSL https://raw.githubusercontent.com/Tencent/BrowserSkill/main/install.sh | sh
export PATH="${BSK_INSTALL_DIR:-$HOME/.local/bin}:$PATH"

# 2. 从 Chrome Web Store / Edge Add-ons 安装浏览器扩展

# 3. 安装 skill 到你的 Agent 框架（交互选择 harness）
bsk install-skill

# 验证连接
bsk doctor
```

验证方式：开一个新 Agent 会话，让它打开 `https://example.com` 并总结页面内容。Agent 沙箱环境（每条命令后回收后台进程的那种）需要按官方 sandboxed-agents 文档把守护进程放到宿主机持久运行，用共享 `BSK_HOME` 连接。

## 能做什么：一个例子

全页长截图是文档里的典型场景：在扩展的 Quick actions 里点 Full-page screenshot，或让 Agent 执行 `bsk screenshot --session <id> --full-page --out page.png`——对内容抓取、页面归档类任务，这比手动拼接截图省事得多。

## 适用边界

- **权限意识**：Agent 复用的是你的真实登录态，等于把你的会话凭证交给 Agent 操作。借用确认默认开启（建议保持），高敏感账号场景要谨慎评估。
- **Chromium 限定**：Firefox 尚未支持；其他 Chromium 系浏览器理论可装 unpacked 扩展，但属"预期可用"而非官方承诺。
- **CLI 与扩展需版本匹配**：全页截图等新特性要求 CLI 与扩展同时为新版本，升级时用 `bsk status` / `bsk doctor` 核对。

## 结语

BrowserSkill 的价值不在浏览器自动化本身，而在它给"人与 Agent 共用一台浏览器"定了一套可执行的规矩：显式借还、独立窗口、人可随时接管。这套交互契约配合 Agent 无关的 CLI 设计，使它适合作为各类 Agent 工作流的通用浏览器层来评估。
