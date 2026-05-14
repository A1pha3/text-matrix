---
title: "React Doctor：给你的编码Agent把脉，一键扫描React代码健康度"
date: "2026-05-14T16:05:00+08:00"
slug: "react-doctor-ai-coding-agent"
description: "React Doctor是一个开源CLI工具，通过一条命令扫描React代码库并输出0-100健康评分，涵盖状态与副作用、性能、架构、安全、无障碍和死代码六个维度，支持Next.js、Vite和React Native，可作为编码Agent的行为约束器。"
draft: false
categories: ["技术笔记"]
tags: ["React", "AI Coding Agent", "代码质量", "TypeScript", "静态分析"]
---

# React Doctor：给你的编码Agent把脉，一键扫描React代码健康度

## 项目概览

**React Doctor** 是由 millionco 开发的开源工具，星数 9,435，Forks 296，定位非常明确：Your agent writes bad React, this catches it。

它是一个 CLI 工具，一条命令对整个代码库进行扫描，输出一个 **0 到 100 的健康评分**，并附有可操作的诊断建议。评分标准为：75+ 优秀，50-74 需改进，50 以下为危险级别。检查维度覆盖 state & effects、性能、架构、安全、无障碍和死代码，且规则会根据框架（Next.js/Vite/React Native）和 React 版本自动切换。

## 核心功能

### 一键健康评分

在项目根目录运行：

```bash
npx -y react-doctor@latest .
```

输出包括：综合评分、问题列表（按严重程度分级）、针对所在框架的上下文建议。

### 集成进编码Agent的行为约束

不仅给人用，React Doctor 还能「教育」编码 Agent，让它在写代码时就避免低质量模式：

```bash
npx -y react-doctor@latest install
```

运行后会提示选择要为其安装的编码 Agent，支持 Claude Code、Cursor、Codex、OpenCode 等50+种 Agent。`--yes` 参数可跳过交互式确认。

### GitHub Actions 集成

随仓库提供了一个 Composite Action，配置到 `.github/workflows/react-doctor.yml` 即可在 PR 和 push 时自动运行，并在 PR 下发布评论（当设置了 `github-token` 时）：

```yaml
name: React Doctor

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read
  pull-requests: write

jobs:
  react-doctor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0
      - uses: millionco/react-doctor@main
        with:
          diff: main
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

Action 还暴露一个 `score` 输出（0-100），可在后续步骤中用于门禁判断。

### 支持的输入参数

| 参数 | 说明 |
|------|------|
| `directory` | 扫描目录 |
| `verbose` | 输出详细日志 |
| `project` | 指定项目类型（next/vite/react-native） |
| `diff` | 与哪个分支对比（生成 diff 报告） |
| `github-token` | 用于 PR 评论 |
| `fail-on` | 低于阈值则失败：`error` / `warning` / `none` |
| `offline` | 离线模式 |
| `node-version` | 指定 Node.js 版本 |

## 技术实现

React Doctor 是一个 TypeScript 项目，发布在 npm 上（包名 `react-doctor`）。它通过静态分析检测常见 React 反模式，覆盖六个主要维度：

- **State & Effects**：useEffect 依赖缺失、状态冗余
- **Performance**：不必要的重新渲染、memo 缺失
- **Architecture**：组件职责不清、prop drilling
- **Security**：dangerouslySetInnerHTML、XSS 风险
- **Accessibility**：缺失 aria 属性、键盘导航问题
- **Dead Code**：未使用组件、导入但未使用

## 为什么需要它

主流编码 Agent（Claude Code、Cursor 等）在生成 React 代码时，往往能跑通，但不一定符合最佳实践。React Doctor 扮演的是「质量门禁」角色——Agent 写完代码，自动跑一遍体检，不合格就打回。它比人工 review 快，比规则引擎更精准（基于 AST 分析而非正则匹配）。

## 适用场景

- 团队使用 AI 辅助开发 React 项目，需要质量兜底
- CI/CD 中集成代码健康度门禁
- 给编码 Agent 建立 React 编码规范约束
- 存量 React 代码库的快速诊断

---

**延伸阅读**：[官网与演示](https://react.doctor) · [GitHub 仓库](https://github.com/millionco/react-doctor)