---
title: "React Doctor：一键诊断 React 代码健康度"
date: "2026-05-13T20:20:00+08:00"
slug: "react-doctor-react-code-health-score-guide"
description: "React Doctor 是一款开源的 React 代码健康度诊断工具，一行命令对你的 React 项目打分（0-100），并输出状态管理、性能、安全、无障碍等六个维度的可操作诊断建议。支持 Next.js / Vite / React Native，可集成到 Claude Code、Cursor 等 AI 编程工具中。"
draft: false
categories: ["技术笔记"]
tags: ["React", "TypeScript", "代码质量", "AI 编程", "静态分析"]
---

# React Doctor：一键诊断 React 代码健康度

AI 编程工具写代码很快，但它们往往不理解 React 的最佳实践——`useEffect` 的依赖数组填错了、状态直接修改而非通过 `setState`、冗余的 re-render 累积……这些问题通常要等到线上出问题才会被发现。

**React Doctor** 正是为解决这个问题而生的：它像一个 React 版的"体检报告"，对你的代码进行多维度扫描，输出 0-100 的健康分数，并给出可操作的修复建议。

## 项目速览

| 维度 | 内容 |
|------|------|
| 仓库 | [millionco/react-doctor](https://github.com/millionco/react-doctor) |
| Stars | 9,032（截至 2026-05-13） |
| 主要语言 | TypeScript |
| 安装方式 | `npx -y react-doctor@latest .` |
| 支持框架 | Next.js、Vite、React Native |

## 核心功能：代码健康度评分

运行命令后，React Doctor 会扫描整个项目，评估以下六个维度：

1. **State & Effects**：`useEffect` 依赖数组、最佳 state 管理模式
2. **Performance**：不必要的 re-render、缺失的 `memo`、低效的列表渲染
3. **Architecture**：组件拆分合理性、prop drilling、context 滥用
4. **Security**：XSS 风险、`dangerouslySetInnerHTML`、不安全的直接赋值
5. **Accessibility**：缺失的 `aria-label`、图片无 `alt`、对比度问题
6. **Dead Code**：未使用的 import、废弃的组件、冗余逻辑

评分标准：

| 分数 | 含义 |
|------|------|
| 75+ | Great |
| 50–74 | Needs work |
| < 50 | Critical |

输出示例会包含每个问题的文件路径、行号、问题描述和修复建议。

## 安装与使用

### 基础使用

```bash
npx -y react-doctor@latest .
```

无需配置文件，无需 API Key，纯本地运行。

### 集成到 AI 编程工具

```bash
npx -y react-doctor@latest install
```

运行后可以选择将 React Doctor 作为 skill 安装到以下工具中：

- Claude Code
- Cursor
- Codex
- OpenCode
- 以及 50+ 其他 AI 编程工具

这意味着 AI 在编写 React 代码时，会主动参考 React Doctor 的规则，从源头减少低质量代码的产生。

### GitHub Actions 集成

```yaml
name: React Doctor

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read
  pull-requests: write  # required to post PR comments

jobs:
  react-doctor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0  # required for `diff`
      - uses: millionco/react-doctor@main
        with:
          diff: main
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

设置 `github-token` 后，React Doctor 会在 PR 中自动评论，指出新增代码中的问题。

## 适用场景

- **团队代码审查**：作为人工审查的辅助工具，快速发现 React 专项问题
- **AI 编程质量控制**：将 React Doctor 的规则注入 AI 编程工具，让 AI 生成更规范的代码
- **老项目体检**：接手维护一个缺少规范的 React 项目时，快速了解技术债分布
- **CI/CD 流水线**：在 GitHub Actions 中作为 PR check 的一部分

## 总结

React Doctor 的核心价值是**降低 React 代码问题的发现成本**——把它从"用户线上反馈"提前到"代码提交阶段"，甚至是"AI 编程工具生成代码时"。对于 React 开发者来说，这是一个值得加入工具箱的低摩擦质量保障工具。

一行安装，一行运行：

```bash
npx -y react-doctor@latest .
```

> **延伸阅读：**
> - [React Doctor 官网与在线演示](https://react.doctor)
> - [GitHub 仓库](https://github.com/millionco/react-doctor)