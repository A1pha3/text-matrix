---
title: "reverse-skill：给编码代理的逆向与渗透技能路由"
date: 2026-08-02T02:59:48+08:00
slug: "zhaoxuya520-reverse-skill-cybersecurity-router"
description: "zhaoxuya520/reverse-skill 是一个面向 AI 编码代理（Claude Code/Codex/Cursor）的网络安全技能路由包，根据代理遇到的 APK/二进制/前端 JS 加密/CTF 题目/渗透目标自动选择对应方法论、检查可用工具并执行可重复流程，而不是让代理凭直觉猜命令。"
draft: false
categories: ["技术笔记"]
tags: ["Agent Skills", "网络安全", "逆向工程", "渗透测试", "CTF", "Claude Code"]
---

## 一句话判断

`zhaoxuya520/reverse-skill` 的核心价值是"**不让代理凭直觉猜命令**"——它把逆向与渗透工程中常见的目标类型（APK、二进制、前端 JS 加密、CTF 题目、渗透目标）逐一拆成技能路由：代理遇到输入先匹配路由、检查工具可用性、再按可重复流程执行，把"AI 做安全的不可控"压到最低。

## 路由架构

仓库的核心入口是：

- [skills/MASTER-ROUTING.md](https://github.com/zhaoxuya520/reverse-skill/blob/main/skills/MASTER-ROUTING.md)：快速路由
- [skills/routing.md](https://github.com/zhaoxuya520/reverse-skill/blob/main/skills/routing.md)：完整路由规则
- [skills/ops/](https://github.com/zhaoxuya520/reverse-skill/tree/main/skills/ops)：操作契约

README 给代理的指引写在 README_AI.md 里：

> If you are an AI Agent, jump to README_AI.md and follow the instructions strictly.

这意味着这个仓库同时面向两类读者：

1. **人类安全研究员**：作为工具集合
2. **AI 代理**：作为技能描述源（README_AI.md）

## 输入与路由分流

| 输入 | 路由到 |
|------|--------|
| APK | Android 反编译（apktool、jadx、frida） |
| 二进制 | 平台识别（file、checksec）+ 调试（gdb、pwndbg、IDA 注释） |
| 前端 JS 加密 | 静态分析（sourcemap、AST）+ 动态 hook |
| CTF 题目 | 按 category（crypto/pwn/web/reverse/misc）路由到对应模板 |
| 渗透目标 | 信息收集 → 漏洞扫描 → 利用 → 后渗透 标准流程 |

每个分支都检查"工具是否已安装 / 是否需要 sudo / 是否需要联网更新规则"，并在工具缺失时给出具体安装命令而不是直接失败。

## 一次端到端使用：CTF Reverse 题目

把"代理拿到一个 ELF 二进制，要求找出 flag"当样本：

1. 代理激活 reverse-skill 的 reverse-CTF 路由
2. 路由要求代理先做 `file` / `checksec` / `strings`，记录基线
3. 路由根据基线选择路径：动态调试（gdb/pwndbg）vs 静态分析（Ghidra/IDA）
4. 路由把"加壳检测 / 反调试绕过 / 加密函数识别"拆成 4 步可重复操作
5. 代理按 4 步执行，每步在路由里查"这是不是当前应该走的分支"
6. 命中关键函数后由路由调用 `decompile-explain` 子技能给人类可读解释

如果代理"猜命令"，常见反模式是直接丢进 IDA 等待结果；reverse-skill 强制先做基线、再选路径，每步都有检查点。

## 适用边界与不适用边界

**适用**：

- 已经把 Claude Code / Codex / Cursor 当成安全工作流一部分的人
- 团队希望统一"AI 看到二进制应该做什么"的应对策略
- CTF 比赛训练（题目类型稳定、流程可模板化）

**不适用**：

- 红队实战（路由的"可重复流程"会暴露在对手面前，需更动态的对抗策略）
- 高敏生产环境（AI 代理做安全操作缺乏审计链路，需要人工监督）
- 完全不懂安全的纯前端开发者（路由里的很多术语需要基础功底）

## 与同类项目的位置

| 项目 | 偏向 |
|------|------|
| `NomaDamas/k-skill` | 公共服务技能 |
| `emilkowalski/skills` | UI 品味技能 |
| `virgiliojr94/book-to-skill` | 文档蒸馏技能 |
| `earthtojake/text-to-cad` | CAD/机器人技能 |
| `zhaoxuya520/reverse-skill` | 网络安全/逆向技能路由 |

这条路线再次印证一个趋势：**Agent Skills 这条赛道正在把"AI 不擅长判断"的所有领域逐一补齐**——从设计师品味到本地公共服务，从文档检索到逆向安全。

## 记忆

仓库自我引用的一句拉丁风短语很准确：

> *Navigate the dark waters, sail against the stream.*

这正是安全/逆向类代理任务的真实写照：在没有固定地图的水域里，靠一份可靠的路由保持方向感。