---
title: "ego lite：把浏览器同时让给人与代理的并行工作站"
date: 2026-08-02T02:59:48+08:00
slug: "citrolabs-ego-lite-agent-browser"
description: "citrolabs/ego-lite 是一个原生 macOS 浏览器，让人和 AI 代理并行使用同一份登录态与同一组标签页；代理跑在独立的 Spaces 里，互不抢 tab，并通过 ego-browser 接口访问用户的真实会话。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Browser Automation", "browser-use", "Mac 工具", "浏览器自动化"]
---

## 一句话判断

`citrolabs/ego-lite` 的核心命题是"**人和 AI 代理应该共享同一个浏览器，而不是各跑各的**"——它的解法是把浏览器改造成原生 macOS 应用：人的标签和代理的标签物理隔离在不同的 Spaces，代理始终能拿到你的真实登录态和真实 DOM，并通过 `ego-browser` 这个本地接口把"我能做什么"暴露给任意代理框架。

## 为什么不是 browser-use / agent-browser

README 第一段就把对手列得很清楚：

> Existing tools like browser-use and agent-browser are browser automation frameworks: they need a separate browser to drive, logins never carry cleanly, and you and the agent end up fighting for the same tabs.

这三件事是体验层面的硬伤：

1. **额外浏览器** —— browser-use / agent-browser 通常启动独立 Chromium 实例，意味着 cookies 不在用户的常规会话里
2. **登录态迁移失败** —— 银行、Notion、Slack 这类对指纹敏感的站点一旦发现浏览器画像对不上就直接拦截
3. **tab 资源争抢** —— 代理在后台打开 20 个 tab 时，你的前台 tab 就被挤掉，或者反过来

`ego lite` 把这三条都拆掉：人和代理共用一个浏览器进程，但活在不同的 Spaces，并通过 macOS 系统层做资源隔离。

## 架构与运行模型

ego lite 的运行模型可以拆成三层：

| 层 | 角色 | 技术细节 |
|---|------|----------|
| **Browser Core** | 原生 macOS 浏览器 | 基于 WebKit/Chromium 内核（README 未明示，但作为 .dmg 原生应用直接绑定系统 WebKit 通道） |
| **Spaces 隔离** | 人/代理标签分区 | 每个代理任务分配独立 Space，前台 tab 不被抢占 |
| **ego-browser 接口** | 暴露给代理的本地 API | 任意 agent 框架通过 HTTP/CDP 协议接入，复用用户真实登录态 |

这意味着任何 agent 框架——browser-use、Playwright、LangChain、Claude Computer-Use——都可以挂到 `ego-browser` 上享受"真实登录态 + 不抢 tab + 并行 Spaces"三个特性。

## 一次真实任务流：让代理帮你做供应商尽调

把"用代理帮你在供应商门户下载一批合同 PDF"当成样本：

1. 你已经在浏览器里登录了供应商 portal（多因素认证已经做完）
2. 让 Claude Code 接管任务："帮我下载 portal 上 2024 年全部合同"
3. 代理通过 `ego-browser` 拿到"真实登录态 + 当前会话"引用
4. 代理在自己的 Space 里开新 tab，避开你前台正在编辑的 Notion 页面
5. 代理逐个打开合同 PDF，下载到 `/Users/.../Contracts/2024/`
6. 下载过程你完全感知不到——前台的 tab、滚动位置、登录态都保持不动
7. 任务结束后代理在它自己的 Space 里关闭 tab，前台你看到的状态没有任何变化

如果换成 browser-use，这套流程要么得重新跑一遍登录（被 MFA 拦），要么得强行把代理 tab 塞到前台 tab 之间（你编辑到一半被迫看到下载进度条）。

## 安装与平台

```bash
# Apple Silicon
curl -L -O https://cdn.ego.app/channel/github_github_referral/setup/macos/arm64/egolite.dmg
# Intel
curl -L -O https://cdn.ego.app/channel/github_github_referral/setup/macos/x64/egolite.dmg
```

打开 `.dmg` 拖到 `/Applications` 即可。**当前仅支持 macOS**，Windows 和 Linux 在 roadmap 上。

## 适用边界与不适用边界

**适用**：

- 已经在用 browser-use / agent-browser 但被"登录态丢失"卡住的团队
- 每天都有"代理能不能帮我在 portal 上点一堆按钮"诉求的运营/采购/财务
- 不想再多装一个 Chromium 但又不想让代理挤占前台工作的人

**不适用**：

- Windows / Linux 工作站（README 明示 roadmap）
- 把浏览器当成"完全无人的自动化脚本运行环境"的纯 RPA 场景（这一类反而是 Playwright + headless 简单点）
- 期待它内置某个 agent 大脑：ego lite 只提供"浏览器 + 代理接口"，不负责让代理"知道该做什么"

## 它的真正贡献

过去一年所有 browser-use 类项目的努力都集中在"让代理能控制浏览器"；`ego lite` 把这个问题反过来：**让浏览器主动把代理请进来**。这个反转决定了它在架构层面的不可替代性——一旦你的工作流真的依赖"代理 + 真实登录态 + 不抢 tab"，其他方案就只能靠外置 profile/cookie 注入来打补丁，而补丁永远追不上指纹检测。