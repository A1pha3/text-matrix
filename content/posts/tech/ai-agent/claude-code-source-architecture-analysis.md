---
title: "Claude Code 源码架构全解析：Tool、Command、MCP 与权限系统"
date: "2026-03-31T21:54:05+08:00"
slug: "claude-code-source-architecture-analysis"
aliases:
  - /posts/tech/claude-code-source-architecture-analysis/
description: "基于 instructkr/claude-code 镜像说明与 Anthropic 官方资料，系统拆解 Claude Code 的 Tool、Command、MCP、Bridge、权限模型与扩展机制，帮助你从入门一路看懂到架构层。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "Anthropic", "TypeScript", "MCP", "智能体架构"]
---

# Claude Code 源码架构全解析：Tool、Command、MCP 与权限系统

> 预计阅读时间：50 分钟 | 难度：⭐⭐⭐⭐

---

> **目标读者**：希望系统理解 Claude Code 产品定位、源码快照价值、架构分层与扩展机制的开发者
> **核心问题**：Claude Code 为什么不是普通聊天工具，而更像一个可扩展的软件工程代理平台？
> **难度**：⭐⭐⭐⭐（架构分析）
> **事实口径**：官方产品能力以 Anthropic 官方资料为准；源码组织分析以 instructkr/claude-code 镜像说明为准
> **延伸阅读**：[Claude Code 推荐做法大全：22.9k Stars 的 AI 编程指南解读]({{< relref "claude-code-best-practice-guide.md" >}}) ｜ [Claude Code Skills & Plugins：AI 编程智能体技能库完全指南]({{< relref "claude-code-skills-agent-plugins-guide.md" >}}) ｜ [Awesome Claude Code：从入门到精通 Claude Code 资源大全]({{< relref "awesome-claude-code-resources-guide.md" >}})

如果你最近正好看到了 `instructkr/claude-code` 这个镜像仓库，最容易产生的两个误解是：第一，Claude Code 是不是已经“完全开源”；第二，这个项目的核心到底只是一个终端聊天器，还是一个真正的工程代理平台。本文会把这两个问题拆开讲清楚：哪些内容来自 Anthropic 官方公开资料，哪些内容来自公开快照镜像说明，以及 Tool、Command、MCP、Bridge、权限系统与多智能体机制是如何共同组成 Claude Code 的。

## §0 先看结论

如果你时间有限，先把下面 6 个核心判断记住：

- Claude Code 的官方定位是**智能体式编程工具**，不是普通聊天助手。
- `instructkr/claude-code` 是**公开快照镜像**，不是 Anthropic 官方开源仓库。
- 真正决定 Claude Code 工程价值的，是**工具系统 + 权限系统 + 工作流编排**，不是"回答效果"。
- 命令系统面向用户意图，工具系统面向执行动作，服务层负责隔离外部复杂性。
- MCP、插件、技能、hooks 与 subagents 共同构成了 Claude Code 的扩展生态。
- 这份公开快照很适合学架构，但不应被误读为“今天线上版本的完整真相”。

## §1 阅读说明与事实边界

这篇文章讨论的是两个相关但不能混为一谈的对象：

- **Claude Code 官方产品**：Anthropic 官方发布的智能体式编程工具，官方 README 明确说明它可在终端、IDE 以及 GitHub 中使用。
- **instructkr/claude-code 镜像仓库**：一个公开暴露快照的镜像与研究档案，不是 Anthropic 官方开发仓库。

为了严格尊重事实，本文采用以下写法原则：

- **官方文档能确认的内容**，直接作为事实陈述。
- **镜像仓库 README 明确写出的内容**，视为“镜像维护者公开声明”，不会写成 Anthropic 官方承诺。
- **无法从公开材料稳定核验的内容**，不写成确定事实，不做脑补。
- **时间敏感数据**（如 stars、forks、watchers）不作为核心结论。

如果你想把这篇文章当作学习材料，最稳妥的理解方式是：

- **产品能力、安装与使用方式**，优先看 Anthropic 官方资料。
- **架构拆解与源码组织分析**，把 instructkr/claude-code 当作公开快照研究材料。

---

## §2 学习目标

完成本文档后，可以：

- ✅ 分清 Claude Code 官方产品与公开镜像快照的边界
- ✅ 理解这次公开事件的研究价值与伦理边界
- ✅ 从入门视角理解 Claude Code 的定位、基本使用方式与核心能力
- ✅ 从架构视角掌握 Tool System、Command System、Service Layer、Bridge System、Permission System 的职责划分
- ✅ 从开发者视角理解 Claude Code 的插件、技能、命令、MCP 与 hooks 扩展路径
- ✅ 从实践视角判断 Claude Code 适合什么场景，不适合什么场景
- ✅ 建立一条从“能用”到“能分析”再到“能扩展”的学习路径

---

## §2.5 按你的目标选择阅读路径

如果你打开这篇文章，是带着不同任务来的，可以直接这样读：

- **想快速建立整体认识**：优先阅读 §0、§3、§8、§21
- **想理解内部架构**：重点阅读 §7、§8、§9、§10、§11、§12、§13、§14
- **想研究扩展开发**：重点阅读 §16、§17、§18、§22
- **想判断是否适合自己团队**：重点阅读 §5、§17、§19、§20

如果你读完本文后准备继续深入：

- 先去读 [Claude Code 推荐做法大全：22.9k Stars 的 AI 编程指南解读]({{< relref "claude-code-best-practice-guide.md" >}})
- 再去读 [Claude Code Skills & Plugins：AI 编程智能体技能库完全指南]({{< relref "claude-code-skills-agent-plugins-guide.md" >}})
- 最后用 [Awesome Claude Code：从入门到精通 Claude Code 资源大全]({{< relref "awesome-claude-code-resources-guide.md" >}}) 做资源索引

---

## §3 Claude Code 是什么

### 3.1 官方产品定位

Anthropic 官方 README 对 Claude Code 的描述很直接：它是一个**运行在终端中的智能体式编程工具**，能够理解代码库，通过自然语言帮助开发者：

- 执行常规开发任务
- 解释复杂代码
- 处理 Git 工作流
- 在终端、IDE 与 GitHub 场景中协作

这一定义明确区分了 Claude Code 与两类常见工具：它不是单纯的聊天助手，也不是只会“生成一段代码”的补全工具，而是一个带有**上下文感知、工具调用、工作流编排**能力的工程代理。

### 3.2 instructkr/claude-code 是什么

`instructkr/claude-code` 的仓库首页说明写得很清楚：它是一个**公开暴露的 Claude Code 源码快照镜像**，维护目的包括：

- 教育用途
- 防御性安全研究
- 软件供应链分析

它同时强调：

- **不拥有原始代码**
- **不代表官方**
- **不应被解读为 Anthropic 官方仓库**

因此，研究这个仓库时，最正确的态度是把它当作公开快照研究材料，而不是“这是 Claude Code 正式开源了”：

> 这是一次公开快照，为外界提供了观察一个真实世界 AI 工程代理系统内部结构的窗口。

### 3.3 为什么这个项目值得研究

即使不讨论事件本身，这个快照仍然有很高的工程学习价值，因为它同时覆盖了现代 AI 编程工具最重要的几个维度：

- **CLI 产品形态**：如何在终端里做出可交互、可扩展的复杂产品
- **工具编排**：如何把文件、搜索、网络、子智能体、MCP 等能力统一到一个框架里
- **权限治理**：如何让高权限工具在真实用户环境里安全运行
- **多通道集成**：如何同时支持终端、IDE、GitHub、远程控制
- **扩展能力**：如何为命令、插件、技能、hooks、MCP 留出边界清晰的扩展点

---

## §4 公开事件背景与研究边界

### 4.1 公开事件的已知事实

根据镜像仓库 README 的公开说明，以及对外传播的公开线索，可以确认以下信息：

- 公开时间点为 **2026 年 3 月 31 日**
- 对外传播线索指向 X 上的公开帖子
- 镜像说明称，npm 分发中的 source map 暴露了可追溯到未混淆 TypeScript 源码的路径
- 镜像仓库保存的是一个 `src/` 快照，而不是完整、连续的官方开发历史

也就是说，我们能研究到的是：

- 一次具体时刻的源码组织方式
- 当时的产品能力结构
- 工具、命令、服务、权限、扩展模型的大体设计

但我们不能自动推导出：

- 这是当前官方最新实现
- 所有细节都与今天上线版本完全一致
- 所有 README 中的摘要描述都已通过逐文件人工复核

### 4.2 这类研究的价值在哪里

这类材料的价值，不在于“八卦”，而在于它能帮助我们认真回答几个工程问题：

- 一个真实的 AI 编程代理，到底有哪些核心模块？
- 它如何把自然语言请求转成工具调用和结果回传？
- 为什么权限系统必须是架构核心，而不是附属能力？
- 为什么扩展体系通常要同时包含命令、插件、技能、MCP、hooks？
- 为什么终端产品最后会长成“CLI + UI + 服务层 + 协议层 + 权限层”的形态？

### 4.3 伦理边界

这类公开快照只能用于：

- 教学研究
- 防御性分析
- 软件供应链安全讨论
- 工程架构学习

不应该用于：

- 伪装为官方代码
- 商业性复制
- 绕过安全控制
- 构造恶意衍生工具

这一点是研究边界问题，不是礼貌问题。

---

## §5 从入门开始：Claude Code 怎么用

这一节先不谈源码，先回答最实际的问题：**如果你只是想把 Claude Code 用起来，官方公开材料告诉了你什么？**

### 5.1 官方定位的三种使用入口

官方 README 明确提到，Claude Code 可以在以下场景中使用：

- **终端**
- **IDE**
- **GitHub**

这三种入口背后，对应的是三种截然不同的工作方式：

- **终端模式**：最适合日常编码、调试、阅读代码、执行命令
- **IDE 模式**：更适合在编辑器上下文中边看边改
- **GitHub 模式**：更适合让代理参与 PR、Issue、代码评审、自动化协作

### 5.2 官方安装方式

官方 README 列出了多种安装方式，其中值得注意的一点是：

- **npm 安装已被标记为 Deprecated**
- 官方更推荐使用安装脚本、Homebrew、PowerShell 或 WinGet

示例：

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

```bash
brew install --cask claude-code
```

```powershell
irm https://claude.ai/install.ps1 | iex
```

```powershell
winget install Anthropic.ClaudeCode
```

```bash
npm install -g @anthropic-ai/claude-code
```textbash
claude
```

```bash
claude "explain this project"
```

```bash
claude -p "explain this function"
```

```bash
claude -c -p "Check for type errors"
```texttext
src/
├── main.tsx
├── commands.ts
├── tools.ts
├── Tool.ts
├── QueryEngine.ts
├── context.ts
├── cost-tracker.ts
```texttext
commands/
tools/
components/
hooks/
services/
screens/
types/
utils/
bridge/
coordinator/
plugins/
skills/
remote/
server/
tasks/
state/
schemas/
```texttext
用户输入
  ↓
CLI / IDE / GitHub 入口
  ↓
命令解析与上下文收集
  ↓
Query Engine 调用模型
  ↓
模型决定是否调用工具
  ↓
权限系统检查
  ↓
工具执行 / 服务访问 / 外部协议调用
  ↓
结果回流给 Query Engine
  ↓
格式化输出给用户
```texttext
plugin-name/
├── .claude-plugin/
│   └── plugin.json
├── commands/
├── agents/
├── skills/
├── hooks/
├── .mcp.json
└── README.md
```textmarkdown
---
description: Generate documentation for file
argument-hint: [source-file]
---

Generate comprehensive documentation for @$1
```textbash
claude mcp add <name> <command> [args...]
```

这说明 Claude Code 并没有把外部工具接入做成“内置耦合”，而是通过 MCP 把它协议化。这样做的好处非常明显：

- 外部工具可以独立演进
- Claude Code 不必内置所有能力
- 团队可以按需接自己的数据源和自动化系统

### 16.6 hooks 适合做什么

官方 hooks 参考页的公开摘要至少能看到一些事件名，例如：

- `UserPromptSubmit`
- `Notification`
- `Stop`
- `SubagentStop`

这已经足够说明，hooks 的目标是让 Claude Code 支持**事件驱动型自动化**。典型用途包括：

- 用户提交请求前做预处理
- 任务结束后做通知
- 子智能体结束后补充记录
- 在关键节点执行统一团队规则

### 16.7 自定义 subagents 的方向

官方 CLI 参考页的公开摘要提到，CLI 支持 `--agents` 标志，通过 JSON 动态定义自定义 subagents。

也就是说， Claude Code 的可扩展性并不局限于“扩工具”或“扩命令”，还包括“扩角色”。这对团队化使用非常关键，因为不同团队常常需要：

- 审查型代理
- 文档型代理
- 测试型代理
- 基础设施型代理
- 安全型代理

把角色扩展做成一等能力，是智能体系统比传统 CLI 更先进的地方。

---

## §17 使用场景：Claude Code 适合拿来做什么

### 17.1 适合的场景

基于官方产品定位与镜像快照体现出的能力边界，Claude Code 特别适合以下场景：

- **大型代码库理解**：搜索、上下文、命令、解释联动
- **多步骤工程任务**：定位问题、编辑代码、执行命令、检查结果
- **代码评审与修复建议**：尤其是 `/review` 这类命令式入口
- **环境诊断与维护性工作**：如配置检查、依赖分析、工作流整理
- **团队标准化工作流**：借助技能、命令、插件、hooks、MCP 沉淀规范
- **IDE / CLI / GitHub 贯通协作**：适合需要跨环境一致体验的团队

### 17.2 不适合或需要谨慎的场景

同时，它并不是所有任务的最佳选择：

- **高风险生产操作**：必须有清晰权限边界与人工确认
- **极强确定性要求的任务**：仍然需要传统自动化与测试兜底
- **对数据流转极度敏感的环境**：需要先明确组织策略和合规边界
- **仅需要单一命令的小工具场景**：Claude Code 可能显得过重

### 17.3 最能发挥价值的组织类型

如果从团队视角看，Claude Code 特别适合：

- 代码库较大、上下文复杂的团队
- 希望把工程知识沉淀为技能与命令的团队
- 需要在终端、IDE 与代码托管平台之间统一体验的团队
- 对工具治理、权限治理、流程标准化有要求的团队

---

## §18 从入门到精通的学习路径

如果你想真正学透 Claude Code，建议按下面的顺序走，而不是一上来就钻到大文件里。

### 18.1 第一阶段：先会用

目标：

- 理解官方定位
- 理解安装方式
- 理解终端、IDE、GitHub 三种使用入口
- 理解“命令”“工具”“权限”的基本概念

建议问题：

- Claude Code 与普通聊天助手有什么本质差异？
- 为什么工程代理必须拥有工具系统？
- 为什么 npm 安装被官方标记为已弃用？

### 18.2 第二阶段：再看架构

目标：

- 搞清 `main.tsx`、`commands.ts`、`Tool.ts`、`QueryEngine.ts` 的角色分工
- 理解服务层、桥接层、权限层的边界
- 理解为什么长会话必须有 compact 之类的能力

建议问题：

- 命令系统与工具系统如何协作？
- 为什么权限控制必须发生在每次工具调用时？
- 为什么 CLI 产品会需要 React + Ink？

### 18.3 第三阶段：进入扩展开发

目标：

- 读懂插件目录结构
- 学会定义命令、技能、代理、hooks
- 理解 MCP 为什么是高扩展性的关键

建议问题：

- 自定义命令适合做什么？
- Skill 与 Command 的边界是什么？
- 什么样的能力应该做成 MCP，而不是内置工具？

### 18.4 第四阶段：站在产品与平台视角复盘

目标：

- 从“功能列表”上升到“平台架构”
- 理解 Claude Code 为什么能同时支持终端、IDE、GitHub
- 理解它为什么要做团队协作、权限治理、策略限制与遥测

这一阶段真正要回答的问题是：

> Claude Code 为什么看起来像一个 CLI，内部却更像一个软件工程操作系统？

---

## §19 自测与练习

### 19.1 基础理解题

请尝试不用看原文，直接回答下面 3 个问题：

1. Claude Code 与普通聊天助手最大的差异是什么？
2. 为什么工具系统比“回答文本”更能决定 Claude Code 的实际价值？
3. 为什么本文必须把官方产品与镜像快照区分开来？

### 19.2 架构分析题

如果你已经具备一些工程经验，可以继续思考：

1. 如果拿掉权限系统，Claude Code 会在哪些地方立即变得危险？
2. 如果拿掉服务层，`QueryEngine.ts` 最容易被哪些外部复杂性污染？
3. 如果没有 Bridge 与 MCP，Claude Code 的扩展上限会卡在哪里？

### 19.3 迁移实践题

假设你要为自己的团队做一个内部 AI 工程代理，请先写出你的最小架构草图，并至少回答：

- 你的工具抽象怎么设计？
- 你的权限模型放在哪一层？
- 你的命令、技能、插件、MCP 是否都需要，为什么？
- 你如何处理长会话中的上下文压缩与任务状态？

如果这 4 个问题暂时回答不清，说明你需要先回头把 §9、§11、§13 的架构层看懂，再回来画自己的设计图。

---

## §20 常见问题

### 20.1 这是不是 Claude Code 官方开源？

不是。公开镜像仓库明确强调它是镜像快照与研究档案，不应被视为 Anthropic 官方仓库。

### 20.2 这份快照能代表今天的官方实现吗？

不能直接这么理解。它更像某个时间点的公开快照，适合做架构研究，不适合被当成“当前官方实现的逐行真相”。

### 20.3 为什么这篇文章既讲官方产品，又讲镜像快照？

因为两者回答的是不同问题：

- **官方资料**回答“它怎么安装、怎么用、有哪些正式扩展面”
- **镜像快照**回答“它内部大概是怎么组织起来的”

只讲一边，结论都会失真。

### 20.4 我能直接照着这份快照去做自己的产品吗？

你可以学习其中的架构思想，但不要把一次公开快照等同于推荐做法模板。真正值得迁移的，是这些原则：

- 工具抽象要统一
- 权限控制要动作级
- 服务层要隔离外部复杂性
- 扩展机制要有清晰边界
- 长会话系统必须考虑上下文压缩与任务状态

---

## §21 架构总结

如果把本文内容压缩成几个最重要的结论，那就是：

1. **Claude Code 的本质是工程代理平台，不是聊天工具**
2. **工具系统是执行核心，命令系统是产品入口，服务层是外部复杂性的隔离带**
3. **权限系统是架构级核心，不是附属能力**
4. **Bridge、MCP、插件、技能、hooks 共同构成了它的扩展生态**
5. **公开镜像快照适合做研究材料，但不能替代官方文档与官方实现**

如果你从这篇文章只带走一句话，我希望是：

> Claude Code 值得认真研究的不是它套了哪个模型，而是它把模型、工具、权限、协议、UI 与扩展机制组合成一个可运行的工程系统的方式。

---

## §22 下一步行动建议

如果你准备把“看懂”转成“真正用起来”，建议直接选一条路径继续：

- **想把 Claude Code 用顺手**：下一篇去读推荐做法文章，把命令、工作流与常见使用误区补齐。
- **想自己做扩展**：下一篇去读 Skills & Plugins 文章，把命令、技能、插件与跨平台转换链路搞明白。
- **想系统追踪生态**：下一篇去读 Awesome 资源大全，把常用扩展、社区项目与资料入口收集完整。
- **想做自家 AI 工程代理**：回看本文 §9、§11、§13、§16，再把工具抽象、权限模型与扩展边界画成你自己的架构图。

你不一定要一次看完所有内容，但最好立即选一条路径继续，否则这篇文章带来的理解很容易停留在“知道有这些概念”。

---

## §23 延伸阅读

如果你接下来想继续把 Claude Code 学深，建议按下面的顺序延伸：

- [Claude Code 推荐做法大全：22.9k Stars 的 AI 编程指南解读]({{< relref "claude-code-best-practice-guide.md" >}})：适合从“会用”走向“用得更稳、更快”。
- [Claude Code Skills & Plugins：AI 编程智能体技能库完全指南]({{< relref "claude-code-skills-agent-plugins-guide.md" >}})：适合理解 Skills、Plugins 与跨平台复用。
- [Awesome Claude Code：从入门到精通 Claude Code 资源大全]({{< relref "awesome-claude-code-resources-guide.md" >}})：适合系统收集生态资源、扩展项目与工作流资料。

如果你的目标是：

- **学产品与架构**：优先读本文
- **学推荐做法与工作流**：优先读推荐做法那篇
- **学扩展与技能生态**：优先读 Skills & Plugins 那篇
- **找更多资料入口**：优先读 Awesome 资源大全

---

## §24 参考来源

### 24.1 官方来源

- Anthropic 官方 README：`https://github.com/anthropics/claude-code/blob/main/README.md`
- Anthropic 官方文档站：`https://docs.anthropic.com/en/docs/claude-code/`
- 官方插件目录与示例：`https://github.com/anthropics/claude-code/tree/main/plugins`

### 24.2 镜像与公开线索

- 镜像仓库：`https://github.com/instructkr/claude-code`
- 公开传播线索：`https://x.com/Fried_rice/status/2038894956459290963`

### 24.3 本文的取材说明

本文优先依据以下几类公开材料进行整理：

- 镜像仓库 README 中明确写出的目录、技术栈与架构摘要
- Anthropic 官方 README 中明确写出的产品定位与安装方式
- 官方插件与文档资料中可确认的扩展方式，例如命令、技能、hooks、MCP、插件目录结构

凡是缺乏稳定公开来源支撑的内容，本文一律不写成确定事实。

---

文档版本 2.0 | 撰写日期：2026-03-31 | 基于公开镜像说明与 Anthropic 官方资料整理 | 仅供教育研究用途
