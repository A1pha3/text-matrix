---
title: "React Doctor：给 AI 编码智能体把脉的 React 代码质量工具"
date: 2026-05-14T12:10:00+08:00
lastmod: 2026-09-19T00:00:00+08:00
slug: "react-doctor-ai-agent-react-code-quality"
github_repo: "millionco/react-doctor"
source_key: "gh:millionco/react-doctor"
aliases:
  - "/posts/tech/react-doctor-ai-coding-agent/"
  - "/posts/tech/react-doctor-react-code-health-score-guide/"
description: "React Doctor 用 800 多条确定性规则扫描 AI 智能体生成的 React 代码，给出 0-100 健康分和修复建议，并通过 agent 技能、pre-commit 钩子和 GitHub Actions 把质检嵌进写码、提交、评审三个环节，另有运行时性能追踪补静态分析的盲区。"
draft: false
categories: ["技术笔记"]
tags: ["React", "AI Agent", "TypeScript", "自动化"]
---

## 先说判断

AI 智能体把 React 代码的生产成本压到新低，代价是审查成了新瓶颈：agent 交代码的速度，已经超过人能读代码的速度。[millionco/react-doctor](https://github.com/millionco/react-doctor) 切的就是这一段——用确定性规则扫出问题、打出健康分，再让 agent 自己学会修。仓库主页的自我介绍相当直白："Your agent writes bad React. This catches it."

容易把它当成"又一个 linter"。实际拆开看，它是四件工具的组合，各自卡在开发流程的一个环节上：

| 组成部分 | 入口命令 | 对应环节 |
|---|---|---|
| 本地审计 CLI | `npx react-doctor@latest` | 写码后：全量扫描，输出问题清单和健康分 |
| Agent 技能安装器 | `npx react-doctor@latest install` | 写码时：给 Claude Code、Cursor 等装技能，让 agent 改完自查 |
| CI/PR 审查 | `npx react-doctor@latest ci install` | 评审时：GitHub Actions 只报 PR 新引入的问题 |
| 运行时性能追踪 | `npx react-doctor@latest scan <url>` | 调试时：录 Chrome DevTools 性能轨迹，补静态分析的盲区 |

另有一项容易被忽略的能力：依赖供应链检查，对接 Socket.dev，可用 `--supply-chain` 开关控制。

项目现状：截至 2026 年 9 月 19 日，14,888 Stars、484 Forks，主要语言 TypeScript，2026 年 2 月创建，最近一次提交在 9 月 18 日，迭代很快。官方规则页当前列出 802 条激活规则。官网：[react.doctor](https://react.doctor)。

## 本地审计：规则、评分与配置

在项目根目录运行：

```bash
npx react-doctor@latest
```

CLI 自动探测框架和 React 版本，应用对应的规则集。支持 React、Next.js、Vite、Astro、TanStack、React Native、Expo、Preact。

问题按类别组织：状态与副作用、性能、架构、安全、无障碍、可维护性。默认报告聚焦两类高价值发现——过于复杂的 React 函数，和值得抽取成共享组件的重复 JSX 树；未使用的文件、导出、类型、依赖和循环导入等全项目规则可以主动开启。

规则可以精细管理：

```bash
npx react-doctor@latest rules list --category performance
npx react-doctor@latest rules explain react-doctor/jsx-key
npx react-doctor@latest rules set react-doctor/jsx-key error
```

也可以在 `doctor.config.ts` 里统一配置；项目里已有 JSON 格式的 ESLint 或 oxlint 配置时会被直接采纳。想把诊断并入现有 lint 命令，仓库还提供独立的 `eslint-plugin-react-doctor` 和 `oxlint-plugin-react-doctor`。

### 健康分怎么来的

扫描结束会输出 0-100 的健康分和文字标签。有一个架构事实值得知道：分数不是本地算的。客户端把脱敏后的诊断数据——规则命中、严重级别、抹掉敏感信息的文件路径——发送到官方评分 API，由它返回分数和标签，并生成一个分享链接。

对分数的解读建议保持克制：它反映的是静态规则命中的严重度分布，不能证明运行时行为正确。内存泄漏这类跑起来才暴露的问题，静态扫描只能覆盖其中可静态识别的模式。另外，CI 挡合并的依据是问题严重级别而非分数，分数更适合当作观察趋势的相对指标。

在意数据边界的话，开关都是现成的：`--no-score` 跳过评分 API 和分享链接；`--no-telemetry` 关闭发往 Sentry 的崩溃与用量遥测，这项默认开启。

## Agent 集成：从工具变成习惯

```bash
npx react-doctor@latest install
```

这条命令把 `/react-doctor` 技能装进安装器探测到的编码智能体（Claude Code、Cursor、Codex、OpenCode 等），教 agent 在改动 React 文件后主动跑扫描，把问题消化在任务完成之前，而不是留给 reviewer。

提交环节的兜底是 pre-commit 钩子：机器上没有钩子管理器时，直接写 `.git/hooks/pre-commit`，对暂存文件按 `--staged --blocking warning` 执行；已有 Husky、Lefthook、pre-commit 等管理器则复用现有链路。Claude Code 和 Cursor 还支持原生 hooks（`--agent-hooks` 启用，默认关闭），agent 每次编辑文件后自动收到扫描结果，可以在会话内即时自纠。

## CI：只审增量，不翻旧账

```bash
npx react-doctor@latest ci install
```

命令生成 `.github/workflows/react-doctor.yml`，走官方 Action `millionco/react-doctor@v2`。这套设计里最有价值的一条：PR 上只报这次变更新引入的问题。扫描以 merge base 为基准做对比，存量债务不计入，结果以一条会随新提交更新的 PR 总结评论（问题计数、分数、`file:line` 链接）加行内评论（带修复建议）呈现。push 到 main 则全量扫描、只记录分数，不对旧问题报警。

默认是咨询模式：报而不挡。要当门禁，`ci config --blocking error` 让新增错误挡合并，`warning` 档连新警告一起挡。扫描范围支持 `full / changed / files / lines` 四档，monorepo 可用 `directory` 和 `project` 参数圈定子项目。

文档里明确写了两个坑：workflow 没配 `fetch-depth: 0` 时，存量问题会被误报为新增；fork 发起的 PR 拿不到评论（GitHub 限制写权限），但扫描和门禁照常工作。

## 运行时追踪：scan 补上静态分析的盲区

```bash
npx react-doctor@latest scan http://localhost:3000
```

这条命令打开系统 Chrome 的临时隔离 profile，录制最长五分钟的性能轨迹；录制期间 React 每次渲染，对应组件会闪现紫色轮廓和组件名。结束后返回一份可读摘要加一个压缩的 DevTools 轨迹文件，`--format json` / `--format jsonl` 输出可以直接喂给编码智能体。

隐私边界 README 写得很清楚：轨迹只存本地、不上传，但内容包含页面 URL、源码路径和 React profiling 细节，应按敏感数据处理。要复用登录态，可以用 `--cdp` 接一个开了远程调试的专用 Chrome profile。

## 一次 PR 的完整流转

把四条线串起来看一次典型任务：工程师让 Claude Code 给列表组件加分页。装过技能的 agent 改完代码自己跑一遍扫描，发现新写的 `useEffect` 依赖数组缺了一项，当场修掉。提交时 pre-commit 钩子对暂存文件再扫一遍。PR 打开后，Action 对比 merge base，只把这次新引入的两条问题贴进评论，并在变更行上给出修复建议。reviewer 看到的是增量风险，不是几百条存量债——在"人读不过来"的前提下，这正是最要紧的设计取舍。

## 采用建议

按介入深度递进：

1. **先本地跑一次基线**：`npx react-doctor@latest`，看健康分和问题分布，判断规则集与团队代码风格的相容性。
2. **有 agent 工作流的团队装技能**：`npx react-doctor@latest install`，把修复动作前移到写码时。
3. **CI 用默认咨询模式跑一两周**：确认误报率可接受后，再切 `blocking: error` 当门禁。
4. **已有 lint 体系想平滑接入的**：先试独立的 ESLint/oxlint 插件，不必整体替换。

不适合的情形同样明确：非 React 技术栈（Vue、Svelte 无覆盖）；不接受任何代码元数据出网的团队（评分 API 和遥测默认开启，需显式关闭）；对许可证敏感的场景需要先读一遍 LICENSE——它是一份标注为 "Modified MIT License" 的修改版协议（版权方 Million Software, Inc.），不是未改动的标准 MIT 文本。

## 结语

lint 生态从来不缺查 bug 的工具，React Doctor 的差异化在于把质检点搬进了 agent 的工作流：写完就扫、提交就拦、PR 只看增量。当写代码的边际成本趋近于零，验证就成了新的瓶颈——这个项目占的正是瓶颈上的位置。
