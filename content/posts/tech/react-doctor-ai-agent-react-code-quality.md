---
title: "React Doctor：给 AI 编码智能体把脉的 React 代码质量工具"
date: 2026-05-14T12:10:00+08:00
slug: "react-doctor-ai-agent-react-code-quality"
aliases:
  - "/posts/tech/react-doctor-ai-coding-agent/"
  - "/posts/tech/react-doctor-react-code-health-score-guide/"
description: "React Doctor 是一款专注于检测 AI 编码智能体生成的 React 代码质量问题的工具，运行后对整个代码库打分（0-100），输出具体问题和修复建议。支持 Next.js、Vite、React Native，已集成 GitHub Actions。"
categories: ["技术笔记"]
tags: ["React", "AI Agent", "代码质量", "TypeScript", "自动化"]
---

## 项目概览

[millionco/react-doctor](https://github.com/millionco/react-doctor) 是一款专门给 AI 编码智能体「把脉」的 React 代码质量工具，当前已获得约 **9,348 颗 Stars** 和 291 个 Forks，采用 MIT 许可证，主要语言为 TypeScript。

核心定位一句话：**AI 编码智能体写的 React 代码容易出问题，React Doctor 来抓。**

官网：https://react.doctor

| 指标 | 数值 |
|------|------|
| Stars | ~9,348 |
| Forks | 291 |
| 语言 | TypeScript |
| 许可证 | MIT |

## 痛点背景

随着 Claude Code、Cursor、Codex 等 AI 编码智能体在 React 开发中大规模使用，一个新问题浮现：AI 生成代码速度快，但质量参差不齐，常见问题包括：

- 不安全的 `useEffect` 依赖
- 未处理的边缘情况
- 内存泄漏
- 欠佳的状态管理
- 缺失的错误边界
- React 18/19 新版 API 的误用

React Doctor 正是为解决这个痛点而生。

## 核心功能

### 扫描并打分（0-100）

在项目根目录运行：

```bash
npx -y react-doctor@latest .
```

输出示例：

```
Score: 87/100 (Great)

Issues found:
- [Performance] Unnecessary re-render in UserCard component
- [Accessibility] Missing aria-label on icon button
- [Security] Potential XSS in dangerouslySetInnerHTML usage
...
```

评分标准：

| 分数段 | 评级 | 说明 |
|--------|------|------|
| 75-100 | Great | 优秀，可合并 |
| 50-74 | Needs Work | 需要修复后再合并 |
| <50 | Critical | 关键问题，必须修复 |

### 规则自动适配框架和 React 版本

React Doctor 会自动检测你使用的是 Next.js、Vite 还是 React Native，以及 React 版本，自动应用对应的实践建议规则，无需手动配置。

### GitHub Actions 集成

通过 GitHub Actions 在 PR 中自动运行检测：

```yaml
name: React Doctor

on:
  pull_request:
    paths:
      - '**.tsx'
      - '**.ts'
      - '**.jsx'
      - '**.js'

jobs:
  react-doctor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npx -y react-doctor@latest .
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

`github-token` 参数用于在 PR 评论中自动发布检测结果。

### 支持的 AI 编码智能体

README 列出了已验证支持的智能体：

- Claude Code
- Cursor
- Codex
- OpenCode
- 以及 50+ 其他智能体

## 技术实现

从仓库结构看（`packages/react-doctor/`），这是一个典型的 npm 包项目：

```
packages/react-doctor/
├── src/          # 核心检测逻辑
├── tests/        # 测试用例
├── bin/          # CLI 入口
├── vite.config.ts
└── tsconfig.json
```

基于 Vite + TypeScript 构建，提供了完整的 CLI 工具。

## 应用场景

- **PR 检查**：AI 编码智能体提交 PR 后，自动运行 React Doctor 给出质量报告
- **本地调试**：开发者在本地手动运行，快速定位 AI 生成代码的问题
- **CI 门禁**：将分数作为合并门禁，防止低质量代码进入主干
- **Code Review 辅助**：给人类 reviewer 提供量化参考

## 局限性

- **专注 React**：仅针对 React 代码，其他框架暂不支持
- **静态分析为主**：部分问题（如运行时内存泄漏）需要实际运行才能发现
- **规则覆盖**：规则库随版本更新，实践建议在演进

## 总结

随着 AI 编码智能体成为开发工作流的一部分，「AI 生成代码的质量保障」成了一个新需求。React Doctor 填补了这个空白——给 AI 的输出做质检。大量使用 AI 智能体开发 React 项目的团队，可以试试。

仓库：https://github.com/millionco/react-doctor  
官网：https://react.doctor