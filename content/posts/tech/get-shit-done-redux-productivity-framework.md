---
title: "get-shit-done-redux 极速上手：用一个六指令循环把 AI 编程拉回巅峰状态"
date: "2026-05-23T03:15:00+08:00"
slug: "get-shit-done-redux-productivity-framework"
description: "get-shit-done-redux 是 open-gsd 维护的 AI 编程工作流框架。它通过结构化 planning 文件、独立子 agent 和 discuss → plan → execute → verify → ship 循环，解决长会话里的 context rot，把 AI 编程收束成可验证的交付流程。"
draft: false
categories: ["技术笔记"]
tags: ["AI编程", "Claude Code", "工作流", "上下文工程", "Spec-Driven Development"]
---

# get-shit-done-redux 极速上手：用一个六指令循环把 AI 编程拉回巅峰状态

## 先给判断

get-shit-done-redux（以下简称 GSD）解决的不是“怎么让 AI 写出第一版代码”，而是“怎么让 AI 在多轮开发里持续交付可验收的结果”。

它最强的地方，不是“比别的 AI 更会写代码”，而是把 AI 编程里最容易失控的三件事收紧了：上下文漂移、需求走样、验收缺席。它的做法也很明确：**把任务拆成 phase，把 phase 拆成 plan，把真正的执行扔到干净的子 agent 上下文里，再用文件化状态和人工验收把结果兜住。**

所以，与其说 GSD 是一个工具，不如说它是一套让 AI 编程可预测、可回放、可重启的工作流协议。它尤其适合独立开发者和 2 到 5 人的小团队，也适合那些已经被“AI 前面很能写，后面越来越飘”折腾过的人。

如果你只想用一句话理解它，可以记成这样：**GSD 不是帮你把 prompt 写得更花，而是给 AI 编程加了一套外部记忆、分工执行和验收门。**

> 参考入口：[open-gsd/get-shit-done-redux](https://github.com/open-gsd/get-shit-done-redux) · [README](https://github.com/open-gsd/get-shit-done-redux/blob/main/README.md) · [User Guide](https://github.com/open-gsd/get-shit-done-redux/blob/main/docs/USER-GUIDE.md) · [Architecture](https://github.com/open-gsd/get-shit-done-redux/blob/main/docs/ARCHITECTURE.md)

## 读完你应该能回答三件事

- GSD 解决的核心问题到底是不是 `context rot`
- discuss、plan、execute、verify 这四步各自锁定了什么风险
- 第一次上手时，应该从安装、建项目、首个 phase 还是现有代码库接入开始

## 系统地图

表面上看，GSD 是 6 条命令；真正起作用的是 3 层结构：命令层、工作流层、状态层。

### 第一层：你看到的是命令

| 指令 | 环节 | 作用 |
| ---- | ---- | ---- |
| `/gsd-new-project` | 初始化 | 提问、研究、抽需求、生成路线图 |
| `/gsd-discuss-phase N` | 讨论 | 把“你心里怎么想的”写成实现约束 |
| `/gsd-plan-phase N` | 规划 | 研究、拆任务、做计划校验 |
| `/gsd-execute-phase N` | 执行 | 按波次并行执行 plan，生成原子提交 |
| `/gsd-verify-work N` | 验证 | 逐项做人工验收，不通过就回滚到下一轮执行 |
| `/gsd-ship N` | 交付 | 从已验证的 phase 创建 PR 或进入交付动作 |

### 第二层：后台跑的是工作流

GSD 的工作流不是“一条大 prompt 从头写到尾”，而是由一组薄编排器驱动不同 agent：

- 研究 agent 负责找资料、查依赖、补风险
- planner 负责把目标拆成可执行的 plan
- plan-checker 负责拦住不够小、不够清晰、不可验证的计划
- executor 负责在干净上下文里实现每个 plan
- verifier 和 debug agent 负责把“能跑”继续压成“符合目标”

这一层的关键不是 agent 多，而是**每类 agent 都拿到刚好够用的上下文**。这也是它和纯聊天式 AI 编程最大的差别。

### 第三层：真正稳定系统的是文件化状态

在执行层面，GSD 会持续维护一组结构化文档，贯穿 session 边界：

- `PROJECT.md`：项目愿景
- `REQUIREMENTS.md`：需求范围
- `ROADMAP.md`：阶段路线图
- `STATE.md`：当前位置与决策记录
- `CONTEXT.md`：各相位的实现决策

这些文件不是“顺手生成的文档”，而是系统的外部记忆。你关掉窗口、清空上下文、隔天再回来，GSD 不是靠聊天记录回忆项目，而是靠这些 planning 文件重新定位项目状态。

## 六条命令不是重点，三条约束才是重点

很多人第一次看到 GSD，会把注意力放在命令数量上。其实 6 条命令本身并不新鲜，真正有价值的是它把 AI 编程压进了 3 条约束。

### 1. 重活放到干净上下文里

GSD 的执行阶段会把 plan 分发给独立 executor。每个 executor 都从一个干净的上下文起步，不继承主会话里那些已经变得臃肿的聊天历史。主上下文只负责协调、确认和验收，不再背着所有细节一路前进。

这件事看起来像“优化 prompt”，本质上更接近**任务调度**。你不是在一条越来越长的对话里逼 AI 同时记住需求、分支、异常、临时决定和测试结果，而是在不断给不同 agent 发一份足够小、足够明确的工单。

### 2. 决策先落文件，再进入执行

`/gsd-discuss-phase` 的价值在这里很容易被低估。很多 AI 编程翻车，不是模型不会写，而是“你脑子里有约束，但你没把它说实”。比如：

- 错误处理要不要暴露原始报错
- 这个 phase 是先追求性能，还是先把接口稳定下来
- 允许引入新依赖，还是优先用标准库
- UI 上哪些地方是品味问题，哪些地方是硬约束

这些决定如果不提前落进 `CONTEXT.md`，后面的 planner 和 executor 只能猜。GSD 做的事很朴素：先把灰区变成白纸黑字，再让 AI 按这个边界去写。

### 3. 验证不是“顺手跑一下测试”，而是单独一个 gate

不少 AI 编程流程最大的问题，是把“实现”当成“完成”。GSD 则把 verify 单独拎出来。它要求你按可观察结果去做人工验收，任何不通过的项都会被整理成新的修复计划，再回到执行阶段。

这一步非常关键，因为它在纠正一个常见错觉：**代码生成是自动化的，但“是否符合预期”仍然需要人为判断。**

## 一个 phase 是怎么流过去的

官方的 [User Guide](https://github.com/open-gsd/get-shit-done-redux/blob/main/docs/USER-GUIDE.md) 里给了一个很好的例子：做一个 Node.js 的 webhook 签名校验中间件。这个例子比“做个笔记应用”更好，因为它能清楚展示 GSD 的任务流。

### 第一步：先建项目，不先写代码

```bash
/gsd-new-project
```

GSD 会先问你要做什么、给谁用、边界在哪，然后并行跑研究，最后产出 `PROJECT.md`、`REQUIREMENTS.md` 和 `ROADMAP.md`。这一步的产物不是代码，而是项目合同。

### 第二步：在 discuss 里把“实现偏好”锁死

```bash
/gsd-discuss-phase 1
```

比如这个 webhook 中间件案例里，discuss 阶段会把下面这些信息写进 `CONTEXT.md`：

- 无效签名直接返回 `401`
- 容忍时间窗默认全局配置，但允许按路由覆盖
- HMAC 优先使用 Node 内置 `crypto`
- 错误格式固定为结构化对象，而不是随手抛字符串

这一步的意义在于：路线图里只有“做签名校验中间件”，而真正能指导实现的，是这些更细的选择。

### 第三步：plan 不是列 TODO，而是生成可执行任务单

```bash
/gsd-plan-phase 1
```

GSD 会先跑并行研究，再生成多个 plan 文件。每个 plan 都会明确到：

- 涉及哪些文件
- 要完成什么动作
- 怎样验证
- 达成什么条件才算 done

如果 plan 太大、太模糊、无法验证，plan-checker 会把它打回去。这一点很重要，因为它决定了后面的 executor 是在做“实现”，还是在继续帮你想需求。

### 第四步：execute 才是真正的并行入口

```bash
/gsd-execute-phase 1
```

这一步里，多个 plan 会按依赖关系被分成不同波次。互不阻塞的任务并行执行；存在依赖的任务顺序推进。每个任务在独立子 agent 里完成，并生成原子 commit。这样做有两个直接好处：

- 主上下文不会被实现细节塞满
- Git 历史更清楚，回滚和审查更容易

### 第五步：verify 把“看起来没问题”变成“真的过线”

```bash
/gsd-verify-work 1
```

在 webhook 案例里，verify 会逐项问你：

- 能不能正常挂到 Express 路由上
- 合法签名是否返回 `200`
- 非法签名是否稳定返回 `401`

如果你回答“第三项没有通过，我拿到的是 `500`”，GSD 就会把这个失败重新整理成 plan，再回到 execute。也就是说，**verify 不是结尾的勾选框，而是下一轮执行的输入口。**

### 第六步：ship 是把 phase 交付出去，而不是宣布大功告成

```bash
/gsd-ship 1
```

当某个 phase 通过验证后，你再创建 PR、进入下一个 phase，或者推进 milestone。这样，交付动作发生在“已验证结果”之后，而不是发生在“模型说写完了”之后。

## 为什么这个思路有效

大多数 AI 编程工具的问题，不是“模型太弱”，而是“上下文越长，约束越容易丢”。这件事通常会体现在 4 个层面。

### 第一，长会话会稀释优先级

当一个 session 里混入探索、临时修补、日志、解释、跑偏讨论和情绪化反馈以后，模型很难继续稳定地区分“真正重要的约束”和“刚刚发生但不重要的噪音”。这就是大家常说的 `context rot`。

GSD 的解法是把执行搬去 fresh context，把主会话降级为协调器。这样主会话不再承担“记住一切”的责任。

### 第二，文件化状态比聊天记录更可靠

聊天记录擅长对话，不擅长做长期项目状态。`PROJECT.md`、`REQUIREMENTS.md`、`ROADMAP.md`、`STATE.md` 这些文件看起来很“老派”，但正因为它们是显式文件，才适合在上下文重启、多人协作、PR 审查里反复引用。

### 第三，计划校验把大量返工拦在执行前

如果没有 plan-checker，executor 经常会遇到一种很尴尬的任务：目标看似明确，实际上缺边界、缺验证条件、缺依赖前提。GSD 把这类问题尽量前置到 planning 阶段解决，减少“执行到一半才发现任务定义不完整”的返工。

### 第四，人工验收重新回到了流程中央

GSD 从来没有假装“有了自动化测试就不需要人判断”。它的 verify 设计承认一件现实：产品行为、交互是否顺手、异常是否符合预期，很多时候仍然需要人来做最终裁决。

## 安装与初始化

```bash
npx @opengsd/get-shit-done-redux@latest
```

按照官方 [README](https://github.com/open-gsd/get-shit-done-redux/blob/main/README.md) 的当前说明，安装器会提示你选择运行时，例如 Claude Code、OpenCode、Gemini CLI、Codex、Copilot、Cursor、Windsurf 等，以及安装方式（全局或本地）。

如果你偏向全局安装，可以直接使用：

```bash
npm install -g @opengsd/get-shit-done-redux
```

在 Claude Code 里，官方文档仍然建议配合下面这个启动参数使用：

```bash
claude --dangerously-skip-permissions
```

这是因为 GSD 本来就面向自动化执行，很多动作默认假定 agent 有足够权限推进工作流。

GSD 还支持按 profile 安装，按需加载功能：

| 参数 | 包含内容 |
| ---- | -------- |
| `--profile=core` | 六个核心循环指令（最小集） |
| `--profile=standard` | core + phase 管理 |
| `--profile=full`（默认） | 完整功能集 |

如果你已经有现成代码库，不要一上来就跑 `/gsd-new-project`，而是先跑：

```bash
/gsd-map-codebase
```

这一步会先分析你现有项目的技术栈、结构和约定，再让后续的问题更贴近真实代码库。

GSD 的配置文件位于 `.planning/config.json`，可以通过 `/gsd-settings` 交互式更新，也可以手动编辑。几个常用配置项如下：

| 配置项 | 默认值 | 说明 |
| -------- | -------- | ---- |
| `mode` | `interactive` | `interactive` 需你确认每步，`yolo` 自动通过 |
| `parallelization.enabled` | `true` | 开启独立 plan 的并行执行 |
| `code_quality.fallow.enabled` | `false` | 开启 structural review 预检 |
| `workflow.research` / `plan_check` / `verifier` | 启用 | 控制研究、计划校验、验证 agent 是否参与流程 |

还有一个容易踩的坑：**不要手动把仓库里的 `agents/` 或 `commands/` 文件直接复制进别的运行时目录。** 官方安装器会根据不同运行时转换 frontmatter 和命令形态，例如 Gemini CLI 使用的是 `/gsd:command-name` 这种命名空间形式，而不是 Claude Code 常见的 `/gsd-command-name`。这一点在 [README 的安装说明](https://github.com/open-gsd/get-shit-done-redux/blob/main/README.md) 和 [User Guide](https://github.com/open-gsd/get-shit-done-redux/blob/main/docs/USER-GUIDE.md) 里都写得很明确。绕过安装器，往往会直接撞上 schema 校验问题。

## 第一次上手，建议这样走

如果你今天第一次试 GSD，我更建议走下面这条路径，而不是一上来就背整套命令。

1. 安装 `@opengsd/get-shit-done-redux`
2. 如果你在现有仓库试用，先跑 `/gsd-map-codebase`
3. 执行 `/gsd-new-project`，确认路线图是否说的是同一个项目
4. 只挑一个小 phase，运行 `/gsd-discuss-phase 1`
5. 紧接着跑 `/gsd-plan-phase 1`，看输出的 plan 是否够小、够清楚
6. 用 `/gsd-execute-phase 1` 完成第一轮实现
7. 用 `/gsd-verify-work 1` 做一次真正的人工验收

这样做的好处是，你能在第一个 phase 里直接理解 GSD 的节奏，而不是靠读文档想象它会怎么工作。

## 谁适合用 GSD

GSD 面向的是**已经在用 AI 编程工具，但不满足于“让它自己跑一跑”这种不稳定结果**的开发者。

它特别适合：

- solo developer，想把“灵感驱动开发”收束成可持续节奏
- 小团队，希望保留速度，但不想让 AI 把项目写散
- 已经习惯 Claude Code、Cursor、Codex 这类工具，但受够了长会话后质量下滑的人

它不太适合：

- 只写一次性脚本、临时实验、十分钟能完成的小修小补
- 已经有成熟企业研发流程，而且强依赖 Jira、Sprint ceremony、多角色审批的大组织
- 完全不想做人工验收，只想“让 AI 自己决定对不对”的使用方式

说得更直白一点：GSD 不是为了把 AI 编程变成“零管理”，而是为了把管理工作尽量沉到系统里，让你的注意力回到决策和验收上。

## 2026 年这个 fork 背景，值得单独看一眼

现在活跃维护的仓库是 `open-gsd/get-shit-done-redux`，npm 主包名是 `@opengsd/get-shit-done-redux`。这不是简单的改名，而是一次公开的项目延续。

根据维护者在 [continuity announcement](https://github.com/open-gsd/get-shit-done-redux/discussions/109) 里的公开说明，open-gsd 团队是在原上游出现信任与所有权问题之后接手继续维护的。当前 [README](https://github.com/open-gsd/get-shit-done-redux/blob/main/README.md) 也明确建议用户迁移到 `@opengsd/*` 包名，并只信任 open-gsd 维护链上的后续发布。仓库还公开给出了 [audit transparency report](https://github.com/open-gsd/get-shit-done-redux/discussions/119)，方便你自己核对后续安全说明。

对普通用户来说，这段背景最重要的现实含义只有两条：

- **安装和升级时，优先使用 `@opengsd` scope 下的包名**
- **如果你以前装的是旧包，应该尽快迁移，不要继续混用旧命名和新命名**

这类信息放进文章里，不是为了放大戏剧性，而是因为它直接影响安装命令、升级路径和信任边界。

## 常见误解和踩坑

### 误解一：装完以后就可以“完全放手”

GSD 会自动研究、自动拆任务、自动执行，但它并没有取消人的职责。你仍然需要拍板路线图、锁定 discuss 决策、做 verify 验收。它自动化的是流程推进，不是责任归属。

### 误解二：跳过 discuss 也没关系

可以跳，但你要知道你在放弃什么。跳过 discuss，planner 和 executor 会尽量给出“合理默认”，可很多项目最怕的正是这些“看起来合理”的默认值。你的产品判断、接口偏好、错误处理风格，往往就是在 discuss 里固化下来的。

### 误解三：verify 就是跑测试

不是。自动化测试很重要，但 verify 的重点是验收“实际行为是否符合目标”。很多问题恰恰发生在测试通过但交互不对、异常路径不对、输出格式不对的时候。

### 误解四：直接复制命令文件就等于安装

官方文档明确不建议这么做。GSD 安装器会为不同运行时做格式转换和命名空间调整，手动复制文件通常只会让你在非 Claude Code 运行时里踩 frontmatter 或命令格式问题。

## 如果你只读三份文档

GSD 的文档很多，但第一次上手其实盯住下面 3 份就够了：

1. **[ PROTECTED_70 ](https://github.com/open-gsd/get-shit-done-redux/blob/main/README.md)**：先确认项目定位、安装命令、支持的运行时和当前维护链
2. **[ PROTECTED_71 ](https://github.com/open-gsd/get-shit-done-redux/blob/main/docs/USER-GUIDE.md)**：把第一轮完整工作流从头到尾走一遍
3. **[ PROTECTED_72 ](https://github.com/open-gsd/get-shit-done-redux/blob/main/docs/ARCHITECTURE.md)**：在你真正想理解“为什么它这样设计”时再读

如果你已经能接受它的主张，再去看 [ PROTECTED_73 ](https://github.com/open-gsd/get-shit-done-redux/blob/main/docs/COMMANDS.md) 和 [ PROTECTED_74 ](https://github.com/open-gsd/get-shit-done-redux/blob/main/docs/CONFIGURATION.md) 就行。先把主循环跑通，比先把所有开关背下来更重要。

## 最后判断

GSD 值得关注，不是因为它承诺“AI 会替你把项目全做完”，而是因为它把一个更现实的命题做得比较完整：**怎样让 AI 在长周期开发里持续输出稳定结果。**

它抓住的核心矛盾也确实成立。AI 编程最难的部分，从来不是第一段代码，而是第二轮、第五轮、第十轮之后还能不能守住边界。GSD 给出的回答不是更长的 prompt，而是 fresh context、文件化状态、计划校验和人工验收。

如果你已经在 AI 编程里撞过 `context rot`、需求漂移、验收缺席这些墙，这套框架值得你认真试一轮。最好的试法不是读完所有文档，而是找一个真实的小 phase，从 `/gsd-new-project` 或 `/gsd-map-codebase` 开始，完整走一遍 `discuss → plan → execute → verify → ship`。
