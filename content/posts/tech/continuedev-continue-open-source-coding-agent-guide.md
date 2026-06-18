---
title: "Continue 终版回顾：把 33k Stars 的开源 Coding Agent 留在 2.0.0 的现场"
date: "2026-06-17T21:05:57+08:00"
slug: "continuedev-continue-open-source-coding-agent-guide"
description: "continuedev/continue 是早期最具影响力的开源 AI 编程助手之一，已发布 Final 2.0.0 并归档为只读。本文解读其三端形态与仓库结构。"
draft: false
categories: ["技术笔记"]
tags: ["Coding Agent", "TypeScript", "VS Code", "CLI", "开源归档"]
---

# Continue 终版回顾：把 33k Stars 的开源 Coding Agent 留在 2.0.0 的现场

Continue 是一段值得记录的开源 AI 编程助手史。仓库 README 在开头用一行斜体写下了它今天的状态：

> _Note: The `continuedev/continue` repository is no longer actively maintained and is read-only for all users._

这句话与 GitHub 上接近 **3.4 万 Stars、4,700 Forks** 的体量形成强烈对比——它意味着项目团队主动把产品打磨到 Final 2.0.0 后关上了门，把代码、决策与社区贡献当作"开源公共财产"留给后来者。本文是一篇项目导读，帮助读者快速理解 Continue 的三端形态、最终 2.0.0 的边界，以及仓库内还能读到什么。

## 一、项目定位：先驱与终版

Continue 自述为"pioneering open-source coding agent"。从 2023 年 5 月仓库创建到 2026 年 6 月，它经历了三波重要节点：VS Code 扩展起步、JetBrains 插件补齐、CLI 单独抽出来作为"官方推荐使用方式"。这三端背后是同一套 Core 代码与同一份模型 Provider 抽象，靠一个 monorepo（单一代码仓库）统一管理。

2026 年发布的 **Final 2.0.0** 是一次"刹车式"发布，做了四件事：

1. **移除匿名遥测**（anonymous telemetry）—— 一次把"默认行为"改干净的合规动作。
2. **剥离认证模块**（pulling out authentication）—— 登录态、Token 管理从核心代码里独立出去，让用户自己掌控身份链路。
3. **批量修 Bug**（squashing bugs）—— Final 2.0.0 是一次集中清理。
4. **明确只读**（read-only）—— 仓库不再接受新功能合入，GitHub 上不再有活跃开发。

从结果看，Continue 选择把"它是什么"和"它不是什么"切干净：它是一份**可运行的代码参考**，而不再是一个被持续迭代的产品。

## 二、三种使用形态

README 在发布渠道上给得很克制，CLI 是当前推荐入口，VS Code 是历史核心载体，JetBrains 不再是首选。三者关系如下：

| 形态 | 入口包 | 状态 | 适用场景 |
|------|--------|------|----------|
| **CLI**（`cn`） | `@continuedev/cli`（npm） | ✅ 推荐 | 终端优先、脚本化、可与编辑器解耦 |
| **VS Code 扩展** | `Continue.continue`（Marketplace + OpenVSX） | ✅ 仍在用 | IDE 内联体验、习惯 GUI 的开发者 |
| **JetBrains 插件** | 仓库内 `extensions/intellij` | ⚠️ 维护但不推荐 | IntelliJ 生态用户，README 建议改用 CLI |

CLI 是最值得优先了解的一端。它的 `package.json` 暴露了 `cn` 二进制名，注册在 `extensions/cli/package.json` 的 `bin` 字段里。`build` 流程用 `build:validate` + `build:bundle` 两步走，前者跑 `node validate-aliases.mjs` 校验模块别名，后者用 `node build.mjs` 打包。开发期用 `tsx src/index.ts` 直跑，测试用 `vitest`，e2e 用单独 `vitest.e2e.config.ts`，smoke 测试有 `smoke-test.mjs` 与 `vitest.smoke-api.config.ts` 两套——这种"测试分层细致到环境"是 monorepo 项目成熟的标志。

VS Code 扩展保留了"老牌 AI 编程助手"的所有肌肉记忆：补全、聊天面板、内联编辑、上下文选择器。它在 Marketplace 与 OpenVSX 两处都有发布，README 显式标注了 `extensions/vscode` 源码位置。

JetBrains 插件没有走 Marketplace，而是通过 GitHub Releases 分发，本地安装为主。README 给出的态度很明确："我们推荐使用 Continue CLI 而不是 JetBrains 插件"——这是把 JetBrains 当作"已存在的用户基础要照顾到"，而不是"未来要继续投入的方向"。

## 三、仓库结构：一图看懂 monorepo

Continue 是一个典型的"**单仓多产物**"项目，根目录的 `tsconfig.json` 是 TypeScript 工程的统一入口，`package.json` 用 `concurrently` 并行驱动 `gui / vscode / core / binary` 四组 `tsc --watch`：

```
continuedev/continue/
├── core/                    # 核心逻辑：模型抽象、上下文工程、Agent 循环
├── extensions/
│   ├── vscode/              # VS Code 扩展
│   ├── cli/                 # CLI（cn 二进制）
│   └── intellij/            # JetBrains 插件（维护但不推荐）
├── gui/                     # 独立 GUI（可能用于桌面端或共享组件）
├── packages/                # 共享子包（config-types、fetch、llm-info、
│                            #   terminal-security、config-yaml、openai-adapters 等）
├── binary/                  # 预编译二进制发布件
├── actions/                 # GitHub Actions 自定义动作
├── eval/                    # 评估/基准测试代码
├── docs/                    # 文档源
├── skills/                  # 仓库级 Skills（与 core 解耦）
├── sync/                    # 内部同步脚本
├── scripts/                 # 杂项脚本
├── manual-testing-sandbox/  # 手动测试沙盒
├── media/                   # 仓库展示资源
├── CLA.md                   # 贡献者协议
└── CODE_OF_CONDUCT.md
```

**`core/` 是整个项目的"事实来源"**：CLI、VS Code、JetBrains 三端共享同一份模型 Provider 抽象、上下文检索与 Agent 循环逻辑。`packages/` 下都是被 `core` 复用的小型独立包，例如 `config-types`（配置类型定义）、`fetch`（统一 HTTP 客户端）、`llm-info`（模型能力元数据）、`terminal-security`（终端命令安全校验）、`config-yaml`（YAML 配置解析）、`openai-adapters`（OpenAI 兼容协议适配）。`build:local-deps` 脚本会显式按依赖顺序构建这些子包，这种"先子后父"的构建策略在 monorepo 项目里值得借鉴。

`gui/`、`vscode/`、`core/`、`binary/` 四组并行 `tsc --watch` 通过 `concurrently` 启动，配色 `cyan, magenta, yellow, green` 让本地开发一眼分清四个进程的输出——这种小细节侧面反映出项目对开发者体验的长期投入。

## 四、Final 2.0.0 的实际边界

Final 2.0.0 是一次**有取舍**的发布。理解它"不做什么"和理解它"做什么"同样重要。

**做了什么：**

- 移除匿名遥测：默认不上报任何使用数据。
- 剥离认证：身份与会话管理从核心代码解耦，方便用户在企业内网、私有部署场景里替换。
- 集中修 Bug：把历次迭代遗留的边界问题做一次清理。

**没做什么：**

- 没有引入新的模型 Provider 适配——这一层的扩展空间被留给了 fork。
- 没有继续强化 GUI 客户端——`gui/` 目录存在但已不作为产品方向。
- 没有在 JetBrains 端追加投入——CLI 取代了它的"演进优先级"。

对于想要"继续往里加东西"的开发者，Final 2.0.0 的边界就是 fork 起点。仓库明确写道："We hope this codebase continues to serve as a foundation for others." 这句话与"pioneering"的标题呼应，承认自己的角色已从"产品"切换到"基础设施"。

## 五、为什么仓库仍值得读

虽然项目不再迭代，但 `continuedev/continue` 仓库里仍然有相当多值得借鉴的工程产物：

1. **Provider 抽象层**：`packages/openai-adapters` 与 `core` 内部的 Provider 路由是少数能在 VS Code、CLI、JetBrains 三端共享同一份适配的开源实现，研究 LLM 工具链如何做到"模型无关"绕不开它。
2. **终端安全校验**：`packages/terminal-security` 是 Agent 在执行 Shell 命令前做权限/危险评估的一类工具，Continue 的实现属于早期开源参考。
3. **上下文工程**：`core/` 内对"如何把仓库内容切成 Agent 可消费的上下文"做了一整套实现，含检索、引用追溯、Token 预算控制。
4. **Config YAML 体系**：`packages/config-yaml` 是 `config.yaml` 配置的强类型解析层，是少有的把"配置即代码"做到位的小型工具库。
5. **测试分层**：`extensions/cli` 内部把 contract / unit / e2e / smoke 拆成四套配置，对想写"可验证 AI 工具"的人是个现成范式。
6. **Eval 体系**：`eval/` 目录是 Continue 团队用于回归测试的实验性评估集，本身也值得作为研究材料。

## 六、给三类读者的建议

**还在用 Continue 的用户：** Final 2.0.0 之后不必担心"明天变没"。VS Code 扩展仍可在 Marketplace 与 OpenVSX 拉到，CLI 仍可 `npm i -g @continuedev/cli` 后 `cn` 进入。JetBrains 端有历史用户基础但官方已建议切到 CLI。

**想搭一套 Coding Agent 基础设施的人：** 把 `core/` 与 `packages/` 读一遍是最快的学习路径。`Provider 抽象 + Config YAML + 终端安全校验 + 上下文工程` 这四件套基本构成了"可运行 Agent 工具链"的最小集合。

**想借鉴 monorepo 结构的团队：** `extensions/{vscode,cli,intellij}` + `core` + `packages/*` 的分层是一种"业务壳 + 共享核 + 原子包"的成熟模式，配合 `build:local-deps` 这种显式依赖顺序脚本，能在多端交付场景里少踩很多坑。

## 七、小结

Continue 在 2023–2026 这三年里，是开源 AI 编程助手最具影响力的项目之一。它的 Final 2.0.0 是一次有意识的"刹车"：把匿名遥测拿掉、把认证解耦、把所有残留 Bug 集中清理一遍，然后主动把仓库设为只读，把代码、决策与社区贡献留作开源公共财产。

对于今天再来看这个仓库的人，重点不在于"它还能不能用"——三端都还能用——而在于"它教会了我们什么"。`core/` 的 Provider 抽象、`packages/` 下的工具集、CLI 严格的测试分层、monorepo 跨端交付的组织方式，这些工程资产在 Final 2.0.0 之后仍然在被新项目参考。

如果想认真研究一个"曾经跑过完整产品周期"的开源 Coding Agent 模板，Continue 仓库仍然是 2026 年最值得读完的那一份。
