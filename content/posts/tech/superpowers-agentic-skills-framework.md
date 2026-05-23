---
title: "Superpowers 深度解析：把 AI 编程助手纳入软件工程流程"
date: "2026-05-21T13:13:00+08:00"
slug: "superpowers-agentic-skills-framework"
description: "结合官方 README、v5.1.0 仓库结构与 Jesse Vincent 的发布说明，系统解析 Superpowers 如何把 skills、worktree、TDD 与 code review 组装成 coding agent 的默认工程流程。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Claude Code", "软件工程", "Agent Skills", "TDD"]
---

<!-- markdownlint-disable-file MD003 MD041 -->

Superpowers 值得认真看，不是因为它又给 coding agent 增加了一个插件市场，而是因为它把软件工程里最容易被模型跳过的环节，写成了默认控制流：先澄清需求，再确认设计，再拆计划，再进隔离工作区，再用 TDD 推进实现，最后做 review 和分支收尾。README 里的 “Mandatory workflows, not suggestions” 基本说明了这套系统的态度。

把官方 README、当前 v5.1.0 仓库结构和 Jesse Vincent 的发布说明放在一起看，Superpowers 更准确的定位不是“提示词大全”，也不是“Claude 的外挂合集”，而是一套给 coding agent 用的软件开发方法论：skills 负责定义动作，入口提示负责强制触发，hooks 和 tests 负责验证这些动作在真实任务里会不会被跳过。

## 读完这篇文章，你应该能判断三件事

1. Superpowers 到底是“插件集合”，还是“可执行的软件工程方法论”。
2. 它为什么坚持把 brainstorming、worktree、TDD 和 review 放进默认流程。
3. 如果准备采用，应该先在哪类任务上试，观察哪些信号来判断它有没有真正生效。

## 先给判断：它解决的是工程纪律失控，不是模型不会写代码

很多 coding agent 的问题，并不出在能力上限，而是出在默认行为。需求还没讲清楚就开始实现，代码写完才想起补测试，做到一半跳过 review，最后用一句“已经完成”收尾。这些失误在人类工程师身上也常见，只是模型把它们放大了。

Superpowers 对准的正是这类失控点。它不是要把 agent 变成更会写某种框架的专家，而是要让 agent 在有时间压力、已有沉没成本、上下文不完整的情况下，仍然按工程流程走。

| 常见失控点 | 没有 Superpowers 时常见表现 | Superpowers 的对应处理 |
| ------ | ------ | ------ |
| 太快进入实现 | 直接写代码，用默认假设补齐需求 | `brainstorming` 先提问、比较方案、确认设计 |
| 任务越做越大 | 一次性生成大段实现，难以回滚 | `writing-plans` 拆成 2 到 5 分钟粒度任务 |
| 已经投入很多 | 因为“已经写了不少”而跳过规范步骤 | `using-superpowers` 要求先查技能，再决定怎么做 |
| 测试滞后 | 先写代码，最后凭感觉补几条测试 | `test-driven-development` 强制 RED → GREEN → REFACTOR |
| 完成即宣布成功 | 没有独立复查，直接声称修好 | `requesting-code-review` 与分支收尾流程阻断这种捷径 |

这一点也是 Superpowers 和“把提示词写长一点”的区别。后者主要影响回答内容，前者直接改 agent 的工作顺序。

## 一张表看清它的系统地图

| 项目 | 情况 |
| ------ | ------ |
| 定位 | 面向 coding agent 的技能框架与软件开发方法论 |
| 写作时仓库状态 | 约 203k Stars、18.1k Forks，最新公开发布为 v5.1.0 |
| 官方支持的 harness | Claude Code、Codex CLI、Codex App、Factory Droid、Gemini CLI、OpenCode、Cursor、GitHub Copilot CLI |
| 关键仓库结构 | 多平台插件目录、`skills/`、`hooks/`、`tests/`、入口引导文件 |
| 核心口号 | Mandatory workflows, not suggestions |

如果再往下拆，这套系统至少有四个层面：

| 层面 | 作用 | 对应仓库对象 |
| ------ | ------ | ------ |
| 分发面 | 把能力装进不同 harness | `.claude-plugin`、`.codex-plugin`、`.cursor-plugin`、`.opencode`、`gemini-extension.json` |
| 强制面 | 让 agent 在会话开始就知道“有技能就必须用技能” | `AGENTS.md`、`CLAUDE.md`、`GEMINI.md` 之类的入口文件 |
| 执行面 | 把设计、计划、TDD、review 等动作写成可调用技能 | `skills/` 里的 workflow、debugging、testing、meta skills |
| 验证面 | 检查这些技能在真实代理会话里是否会被遵守 | `hooks/`、`tests/`、跨 harness 的验证流程 |

这里有个容易忽略的事实：安装只是分发，真正起约束作用的是强制面和执行面。插件市场解决的是“怎么装进去”，skills 和入口引导解决的是“装进去以后 agent 会不会真的照做”。

另外，README 明确写了一个部署边界：如果你同时用多个 harness，需要分别安装。Superpowers 不是“一次安装，全平台生效”的全局层。

## 为什么技能才是主角，而不是插件市场

把 Superpowers 看成“高级提示词”只说对了一小半。更接近事实的说法是：它把一套工程动作包装成了可触发、可审查、可测试的运行时规范。

第一，技能不是查阅资料时顺手看的说明书，而是任务入口。README 直接写明，agent 会在每个任务前检查相关 skills。这个触发时机决定了技能先于实现，而不是实现卡住后再想起来补一眼文档。

第二，skill 不是一段松散建议，而是带前置条件、检查清单、失败分支和退出标准的执行脚本。像 `test-driven-development`、`systematic-debugging`、`verification-before-completion` 这几类技能，本质上已经接近“能被 agent 执行的工程规范”。

第三，Jesse Vincent 在发布说明里讲得最有价值的一点，不是又加了哪些 skill，而是这些 skill 会被放进高压场景里测试。时间紧、系统在掉、已经花了 45 分钟、代码看起来也能跑，这些时候模型最容易跳过规范。如果一条流程只在演示环境里成立，到了压力场景就失效，它就不是工作流，只是装饰。

第四，多平台支持固然实用，但它服务的是同一套方法论。Claude Code、Codex CLI、Cursor 或 GitHub Copilot CLI 只是不同入口，背后的工程动作并没有变。

## 七步主工作流，才是 Superpowers 的骨架

README 当前给出的 Basic Workflow 一共七步，顺序也很重要。很多介绍只记住 brainstorming、planning 和 TDD，实际少掉的那几步恰好是把流程从“好建议”变成“能落地”的部分。

README 对 `writing-plans` 的要求还给了一个很有代表性的标准：implementation plan 要清楚到“一个热情但品味不佳、没有判断力、没有项目上下文、而且不爱测试的初级工程师”也能照着执行。话说得不客气，但意思很明确：计划写得细，不是为了文档好看，而是为了降低 agent 在长流程里的偏航概率。

| 阶段 | 触发时机 | 作用 | 这一段为什么不能省 |
| ------ | ------ | ------ | ------ |
| `brainstorming` | 开始写代码之前 | 通过提问澄清目标、比较备选方案、分段确认设计 | 不先把需求和边界说清楚，后面的计划再精细也只是把错事做得更工整 |
| `using-git-worktrees` | 设计获批后 | 创建隔离工作区、切新分支、验证干净基线 | 没有隔离工作区，就很难把当前任务的结果和既有脏状态分开 |
| `writing-plans` | 设计确认后 | 把任务拆成 2 到 5 分钟粒度的小步骤 | 这是把 spec 变成可执行清单的关键桥梁 |
| `subagent-driven-development` 或 `executing-plans` | 有计划之后 | 调度新鲜子 agent 执行任务，或按批次推进并设置检查点 | 重点不是“多开几个 agent”，而是避免一个上下文越做越歪 |
| `test-driven-development` | 实现过程中 | 强制 RED → GREEN → REFACTOR | 官方表述很强：先看到测试失败，再写最小实现；测试之前写出来的代码该删就删 |
| `requesting-code-review` | 任务之间 | 按严重级别审查问题，阻断关键缺陷继续扩散 | 它让 review 成为阶段门，而不是结尾礼仪 |
| `finishing-a-development-branch` | 任务完成后 | 统一跑验证，并给出 merge / PR / keep / discard 等收尾选项 | 结束开发也有流程，避免“能跑就散场” |

这一套顺序里，有两个细节值得特别记住。

第一，`subagent-driven-development` 的重点不是并行，而是两阶段审查：先看 spec compliance，再看 code quality。先判断有没有做对，再判断写得好不好，这个顺序很对症，因为 agent 最常犯的错误往往是偏题，不是代码风格不好。

第二，`using-git-worktrees` 放在 brainstorming 之后，而不是一开始就建工作区。原因很简单：在需求还没定下来之前，隔离分支只是形式；设计一旦确认，隔离工作区立刻就变成了验证与回滚的边界。

## 一次真实任务，如何流过这套系统

官方和发布说明都反复用一个简单任务来演示：让 agent 做一个 React Todo List。这个例子不复杂，但足够看清 Superpowers 的运行方式。

假设你输入一句：

```text
Let's make a React todo list
```

在没有 Superpowers 的普通对话里，agent 往往会立刻开始搭项目、写组件、生成样式，顺手替你假设状态管理、数据持久化和交互范围。

Superpowers 生效时，更合理的路径会是下面这样：

1. `brainstorming` 先把问题问窄：这是单人 Todo 还是协作 Todo，要不要持久化，是否需要登录，移动端是不是目标场景。
2. 设计得到确认后，`using-git-worktrees` 才进入隔离工作区，并检查当前仓库是不是干净基线。
3. `writing-plans` 把事情拆开，例如先搭骨架，再写列表交互，再补存储，再做测试和 review。
4. 你说 “go” 之后，`subagent-driven-development` 或 `executing-plans` 才真正推进实现。
5. 每个实现步骤里，`test-driven-development` 要求先写失败测试，再写最小实现。
6. 任务切换前，`requesting-code-review` 先把关键问题拦下来，不让它滚到后面的步骤。
7. 全部完成后，`finishing-a-development-branch` 统一验证，并让你决定是合并、开 PR、保留 worktree 还是丢弃。

把这条路径走顺以后，你会发现 Superpowers 的收益不是“更会写 React”，而是“把一次编码请求变成了一个可管理、可回看、可复查的工程过程”。

## 发布说明里最有价值的一点：这些技能是按压力场景打磨的

Jesse Vincent 在发布说明里专门写了两类测试场景。一类是“生产系统正在出故障，每分钟都在烧钱”；另一类是“你已经花了 45 分钟把东西做完，而且它现在能跑”。这两类场景抓得很准，因为它们刚好对应模型最容易偏离流程的两个时刻：时间压力和沉没成本。

这也解释了为什么 Superpowers 的入口提示会写得那么硬。像“如果有 skill，就必须用 skill”“先去查技能再行动”这类措辞，看起来近乎啰嗦，但它们不是为演示写的，而是为高压下的偏航写的。发布说明里最值得记住的一句话，不是某条安装命令，而是这一层设计意图：skill 必须在“最想跳过它的时候”仍然能起作用。

从这个角度再看 Superpowers，会更容易理解它为什么不满足于“给一组提示词模板”。它在做的其实是另一件事：把容易被忽略的工程纪律，预先写进 agent 的选择架构里。

## Skill 库里真正重要的，不只是那七步

主工作流之外，README 还把技能分成几组。这个分类很有帮助，因为它说明 Superpowers 不只管实现，还管调试、审查和技能自身的维护。

| 组别 | 代表技能 | 它在流程里解决什么问题 |
| ------ | ------ | ------ |
| 测试 | `test-driven-development` | 防止“先写后补”的惯性，把验证前置 |
| 调试 | `systematic-debugging`、`verification-before-completion` | 防止凭直觉改代码，要求先找根因，再证明真的修好 |
| 协作 | `brainstorming`、`writing-plans`、`executing-plans`、`dispatching-parallel-agents`、`requesting-code-review`、`receiving-code-review`、`using-git-worktrees`、`finishing-a-development-branch`、`subagent-driven-development` | 把从设计到交付的整条协作链条拉直 |
| 元技能 | `writing-skills`、`using-superpowers` | 规范如何写新技能、如何让 agent 持续遵守技能 |

这也是它和普通“提示词仓库”的根本差别。后者大多停在内容层，Superpowers 已经把设计、实现、调试、审查和收尾装进同一套运行机制里。

## 安装与支持平台：要看的不是命令多少，而是边界是否清楚

当前 README 给出的官方支持平台和安装方式如下：

| 平台 | 官方安装方式 |
| ------ | ------ |
| Claude Code | `/plugin install superpowers@claude-plugins-official`；也可先注册 `obra/superpowers-marketplace` 再安装 |
| Codex CLI | 打开 `/plugins`，搜索 `superpowers`，再选择安装 |
| Codex App | 在 Plugins 侧栏的 Coding 分类中找到 `Superpowers` 并安装 |
| Factory Droid | `droid plugin marketplace add https://github.com/obra/superpowers`，然后 `droid plugin install superpowers@superpowers` |
| Gemini CLI | `gemini extensions install https://github.com/obra/superpowers` |
| OpenCode | 让 OpenCode 读取并执行 `.opencode/INSTALL.md` 的官方安装说明 |
| Cursor | 在 Agent 聊天中执行 `/add-plugin superpowers`，或从插件市场安装 |
| GitHub Copilot CLI | 先注册 `obra/superpowers-marketplace`，再安装 `superpowers@superpowers-marketplace` |

这里真正有用的不是把命令背下来，而是记住两个边界。

第一，安装方式因 harness 而异。Superpowers 不是一个统一二进制，而是一套要嵌入不同宿主工具的技能体系。

第二，如果你同时使用多个 harness，需要分别安装。这个细节官方写得很明白，也很容易被忽略。

## 什么时候值得上，什么时候没必要上

Superpowers 的成本主要在流程，不在安装。它会让 agent 慢下来：先问、先拆、先测、先审，再继续。这对中等以上复杂度的任务通常是赚的，对极小任务则未必。

| 更适合启用 Superpowers 的场景 | 不必急着启用 Superpowers 的场景 |
| ------ | ------ |
| 多文件、多步骤、需要连续验证的功能开发 | 二十来行的一次性脚本 |
| 你已经被 agent 的错误假设、漏测和过早宣告成功坑过 | 只想极快做个原型，不太在乎过程约束 |
| 任务需要 spec、TDD、review、branch isolation 这些工程纪律 | 当前任务没有测试、没有 Git、没有长期维护压力 |
| 希望 agent 连续工作更久，但不轻易偏航 | 只是问语法、改文案、调一个很小的样式 |

换句话说，Superpowers 不是“任何任务都更好”的默认答案。它更像是给有维护成本的开发任务加护栏，而不是给所有对话都加重量。

## 第一次采用，建议按这个顺序落地

1. 先只在你最常用的一个 harness 里安装，不要同时铺开多套入口。
2. 选一个中等复杂度的小功能做第一次验收，最好满足“有 Git、有测试、至少改 2 到 3 个文件”这三个条件。
3. 第一次只盯三个核心信号：`brainstorming` 有没有先问清需求，`writing-plans` 有没有把任务拆细，`test-driven-development` 有没有真的先看到失败测试。
4. 这三步稳定以后，再把 `using-git-worktrees`、`subagent-driven-development` 和 `requesting-code-review` 纳入日常流程。
5. 如果某一步没有出现，先查安装和入口注入是否生效，不要急着下结论说“Superpowers 没用”。

这个顺序的好处是，你先验证最核心的收益：agent 有没有从“直接开写”变成“先理解、再规划、后实现”。这件事成立了，后面的并行子 agent、worktree 和分支收尾才值得继续推。

## 第一次试用时，先看这 4 个信号

如果你想判断 Superpowers 到底有没有真正接管流程，不妨先看下面这 4 个现象。

1. 你刚提出任务，agent 是先问问题还是直接开写。前者说明 `brainstorming` 在工作，后者通常说明入口没有接管。
2. 设计确认后，agent 会不会主动切进隔离工作区并检查基线。不会的话，后面的“通过了”很可能只是工作区噪音。
3. 实现阶段，agent 会不会先让测试失败一次。没有 RED，就很难相信后面的 GREEN 真的有约束力。
4. 完成时，agent 会不会先 review 和验证，再给你 merge / PR / keep / discard 的选择。只说“我已经做完了”的流程，通常还没有进入 Superpowers 的真正节奏。

这 4 个信号比“它能不能生成代码”更重要。生成代码谁都能做；把编码过程稳定地拉回工程流程，才是 Superpowers 的分水岭。

## 读完后，可以拿这 3 个问题自测

1. 如果 agent 一上来就开始实现，你最先该怀疑的是安装没成功，还是入口引导没有把 skill 检查放在任务之前？
2. 为什么 `using-git-worktrees` 出现在 design approval 之后，而不是 brainstorming 之前？
3. README 为什么把 two-stage review 放在 `subagent-driven-development` 阶段，而不是等全部任务结束后再统一 review？

如果这 3 个问题都能回答清楚，基本就已经抓住了 Superpowers 的主线：它要解决的不是“怎么让 agent 多干活”，而是“怎么让 agent 少走错路”。

## 最后的判断

Superpowers 值得单独研究，不是因为它把 coding agent 变得更像一个会说话的 IDE，而是因为它把软件工程里最容易被跳过的动作，前移成了默认流程。

如果你真正想解决的是 agent 自作主张、计划粗糙、测试滞后、做完就宣称成功，那么 Superpowers 给出的不是又一组提示词模板，而是一套更接近工程现实的控制框架。它当然不适合每一次编码，但对需要长期维护、需要反复验证、需要多人协作的项目来说，这条路通常比继续把 prompt 写得更长更可靠。

## 参考资料

- [obra/superpowers](https://github.com/obra/superpowers)
- [Superpowers: How I'm using coding agents in October 2025](https://blog.fsck.com/2025/10/09/superpowers/)
- [Superpowers demo transcript](https://blog.fsck.com/blog/2025/superpowers/superpowers-demo.txt)
