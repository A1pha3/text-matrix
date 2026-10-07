---
title: "Spotify Portal AI Plugins：把开发门户装进编码代理，以及一个省 token 的三层委托机制"
date: 2026-10-08T03:25:32+08:00
slug: "spotify-portal-ai-plugins-guide"
github_repo: "spotify/portal-ai-plugins"
source_key: "gh:spotify/portal-ai-plugins"
description: "Spotify 官方把 Portal 开发门户接进 Claude Code、Codex 与 Cursor 的插件集：skills 单一来源封装鉴权、搜索与动作调用，shunt 用钩子-脚本-技能三层把大文件读取与代码生成委托给 AiKA 低成本模式，可省 82%-94% token。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "开发门户", "Claude Code", "插件", "Backstage"]
---

# Spotify Portal AI Plugins：把开发门户装进编码代理，以及一个省 token 的三层委托机制

## 先给判断

Spotify 开源的这个仓库，真正解决的不是"多一个 AI 插件"，而是两个更具体的问题：**把公司内部的开发门户（Developer Portal）从浏览器操作，变成编码代理可以审计、可以安全调用的工作流**；以及**让大文件读取和样板代码生成这种 I/O 密集活，不再吃掉主模型的高价 token**。

第一个问题靠 `portal` 插件解决，第二个问题靠同仓的 `shunt` 插件解决。两者共享同一个底座：Portal CLI 的 actions 注册表。所以这篇文章先拆清"工作流模型"，再拆"委托机制"，最后用一个具体任务把两条线串起来。

## 系统地图

仓库不是单插件，而是一个插件市场（marketplace），目前装了两支插件：

| 插件 | 定位 | 机制核心 |
|------|------|----------|
| `portal` | 把 Portal CLI 封装成编码代理工作流 | 6 个 skills，全部通过 `npx @spotify/portal-cli` 执行 |
| `shunt` | 把 I/O 重活委托给 AiKA 低成本模式 | 钩子拦截 → 脚本调用 → 技能引导，三层结构 |

两者依赖关系明确：`shunt` 本身不含 CLI，它通过 `portal` 插件提供的 Portal CLI 做 `aika:invoke-chat` 委托。换句话说，`shunt` 是 `portal` 之上的一个省钱层。

仓库根目录只放元数据（`.claude-plugin/`、`.codex-plugin/`、`.cursor-plugin/` 三个宿主适配目录），业务逻辑全部收敛在两处：`skills/`（工作流）与 `plugins/shunt/`（委托机制）。

## 工作流模型：skills 是唯一来源

`portal` 插件的设计有一个明确取向：**工作流全部以 skills 形式存在，脚本不是另一个真相源**。仓库一次提交的标题直接点破这一点——`refactor: use skills as the only workflow source`（"把 skills 作为唯一工作流来源"）。

六个 skills 对应六条工作流：

| Skill | 职责 | 关键动作 |
|-------|------|----------|
| `setup` | 配置鉴权 | 校验 CLI 命令、检查实例、登录、验证五个必需命令 |
| `doctor` | 只读诊断 | 检查插件版本、CLI、鉴权、动作可用性，不改变任何状态 |
| `search` | 检索目录与文档 | `search <query> --limit 10 --json`，区分 catalog 与 techdocs |
| `service` | 生成服务简报 | 汇总 ownership、health、incident、文档 |
| `actions` | 发现并安全调用动作 | `--dry-run --json` 预览，变异操作需显式授权 |
| `feedback` | 反馈 CLI 体验 | 面向 Portal 团队 |

### 一个值得注意的工程约束

`actions` skill 的调用纪律几乎像一份安全清单：读操作直接用 JSON 输出；变异操作必须先看生成式帮助、再 `--dry-run` 预览、展示将要改什么、**用户授权后才执行**、只有标记为 destructive 且用户授权时才加 `--yes`。并且有一条明确警告：`Never infer successful execution from a dry run`（绝不从 dry run 推断执行成功）。

`setup` skill 的纪律更硬：**绝不要求用户把 access token、授权码这类凭据粘贴进聊天**。鉴权走 CLI 的登录流程，插件只负责引导。

这些约束说明这仓库不是"能调就调"的玩具，而是把"操作生产系统的安全边界"写进了技能指令里——这恰恰是编码代理接开发门户时最容易被忽略的部分。

## 委托机制：shunt 的三层结构

`shunt` 是仓库里最值得拆的部分。它的目标明确：把 I/O 密集型工作委托给 AiKA 模式下更便宜的 worker 模型，官方给出的节省区间是 **82%-94% token**（针对大文件读取与样板代码生成）。

它有三层，从硬到软：

1. **钩子层（hooks）——硬拦截**：`PreToolUse` 钩子拦两个入口。`check-file-size` 阻止 `Read` 超过 350 行的文件；`check-bash-read` 阻止 `cat` / `head` / `tail` 读取大文件。拦截后不直接放行，而是把请求重定向到 bulk-reader 技能。
2. **脚本层（scripts）——执行委托**：`bulk-read` 与 `code-write` 两个脚本负责调用 AiKA。关键设计是**参数化**：Claude 从不根据自然语言拼接 bash 管道，而是用命名参数调用脚本，管道逻辑全部藏在脚本内部。
3. **技能层（skills）——软引导**：`bulk-reader` 与 `code-writer` 两个 SKILL.md 告诉 Claude 何时该调用脚本、怎么传参。

这里有个明确的职责划分哲学：**钩子负责"不许"，技能负责"改走哪条路"，脚本负责"把路走完"**。三层各自只做一件事，避免了把策略和实现混在钩子里。

### 委托的底座：AiKA 模式注册表

委托不是直连某个模型，而是走 Portal CLI 的 actions 注册表——一次委托 = 一次 `aika:invoke-chat` 调用。模式按名字寻址，解析在服务端完成：大小写不敏感，优先你自己的模式，再是你的群组，然后是公共模式；名字匹配不到、或同时匹配多个模式时，调用失败并返回候选 ID 列表。

默认场景是直接用实例上已存在的两个公共模式 `bulk-reader` 与 `code-writer`；也可以自己建私有模式（自定义模型或指令），因为名字解析优先你自己的模式，所以自定义版本会自动遮蔽公共版本，无需任何额外配置。

## 一次真实任务怎么流过系统

把机制串起来看一次大文件分析任务：

1. 用户在 Claude Code 里问"这个 602 行的 websocket handler 导出了什么"。
2. `Read` 请求触发 `check-file-size` 钩子——文件超过 350 行，读取被拦截。
3. 钩子把请求重定向到 `bulk-reader` 技能。
4. 技能指示 Claude 调用 `scripts/bulk-read`，并带上 `--question` 与 `--paths` 命名参数。
5. 脚本内部拼出一次 `aika:invoke-chat` 委托，把文件交给 `bulk-reader` 模式处理，输出回来后脚本做清理。
6. Claude 拿到的是整理后的结构化摘要，而不是 600 行原文——上下文窗口里只占一小块。

仓库自带的 evals 恰好验证了这套行为的边界：任务 1 要求"应该被钩子拦截然后调用 bulk-read"，任务 3 反着来——**修 bug 这种需要推理的活不应该被委托**，Claude 应该自己带 offset/limit 读相关段落。这说明委托是有适用边界的，不是"所有读都甩出去"。

## benchmark 怎么看

仓库 `evals/benchmarks.json` 定义了四个基准场景：单文件读取、多文件交叉读取、源码+测试配对理解、代码生成。官方声称的 82%-94% 节省来自这些场景的 token 对比。

读这份数字要守住三个边界：

- **测的是上下文 token 占用**，不是端到端延迟或成本价。节省百分比基于"字符数/4"的保守估算，反映的是主模型上下文里少了多少内容，不代表总账单一定同比例下降——`aika:invoke-chat` 本身也在消耗资源。
- **数字反映的是"委托成功且模式正确"时的收益**，对应的是 I/O 密集任务。对需要推理链的任务（调试、设计取舍），委托没有收益，仓库的 evals 也明确断言这种任务不应该委托。
- **不能推出"所有 token 问题都该用这个插件解决"**。它省的是特定任务类型的主模型上下文，省不了任务规划、代码生成质量这类问题。

## 适用边界与采用建议

这仓库适合什么场景：

- **你已经在用 Backstage 或 Spotify Portal 一类的开发门户**，并且希望编码代理能安全地查目录、看归属、调动作——`portal` 插件是现成的接入层。
- **你的 Claude Code 会话被大文件读取反复烧上下文**——`shunt` 的委托层值得试，前提是 Portal 实例开了 AiKA 且存在 `bulk-reader` / `code-writer` 模式。
- 对不需要这些能力的团队，插件集本身价值有限——它不是通用的 token 优化器，离开 Portal 生态就用不起来。

采用顺序建议：先装 `portal`，跑 `/portal:setup` 完成鉴权，用 `search` 和 `service` 确认工作流可用；确认 Portal 侧 AiKA 模式就绪后，再装 `shunt` 观察委托是否带来实际收益。安装方式上，Claude Code 走 marketplace 命令、Codex 走 `/plugins` 面板、Cursor 走团队市场注册——三个宿主各自的适配目录已经备好。

## 结尾判断

这个仓库的价值不在功能多，而在它示范了一种姿态：**编码代理接生产系统时，安全边界和成本控制应该被设计进工作流，而不是事后靠提示词约束**。skills 唯一来源保证了行为可审计，shunt 的三层委托把"省 token"做成了有明确适用边界的机制，而不是一刀切的偷懒开关。对正在建设"代理可操作内部系统"这一层能力的团队，它是一份值得参考的工程样本。
