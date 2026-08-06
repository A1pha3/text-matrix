---
title: "LoopX：给长程 AI Agent 造一个本地控制平面"
date: 2026-08-04
categories: ["技术文章"]
tags: ["Loop Engineering", "AI Agent", "控制平面", "Codex", "Claude Code"]
description: "LoopX 是轻量 Python 状态内核，为 Codex、Claude Code、Cursor 等编码 Agent 提供跨轮次的目标管理、证据留存、配额调度和可审计交接，MIT 协议，附 200+ 小时真实运行证据。"
slug: index
---

## 仓库信息卡

| 项目 | 详情 |
|------|------|
| 仓库 | [huangruiteng/loopx](https://github.com/huangruiteng/loopx) |
| Stars / Forks | 1,491 / 101 |
| 语言 | Python 3.11+（零运行时依赖） |
| 许可证 | MIT |
| 首次提交 | 2026-05-31 |
| 最近 push | 2026-08-04 |
| 当前版本 | v0.4.1 |
| 仓库大小 | 31 MB |
| Topics | agent-control-plane, agent-ops, ai-agents, codex, long-running-agents, loop-engineering |

## 一句话定调

README 里有一句中文标语：「把会干活的 Agent，接成可管理、可复盘、可持续改进的数字员工。」

这句话浓缩了 LoopX 的设计意图。它不制造新的 Agent 运行时，也不替代 Codex 或 Claude Code 的执行能力。它做的事情更基础设施化：在 Agent 和人之间插入一层持久的控制状态，让目标、门控、待办、证据、配额和交接这些管理对象跨轮次存活。

## 问题：长程工作中的失控

单个 Agent 在单次会话内完成任务——这是 2025 年已经解决的问题。真正的困难出现在工作周期拉长到几天、几周的时候：

**目标漂移。** 用户在第 3 天修改了优先级，第 1 天的 Agent 执行结果已经过时。聊天记录里翻不到明确的决策点。

**证据失序。** 每轮 Agent 产出的 diff、测试结果、review 意见散落在不同会话中。下一次续跑时，Agent 不知道哪些已被验证、哪些已失效。

**交接断裂。** Agent A 做完一轮，Agent B 接手时缺少结构化的上下文包。"你接着做"这句话背后藏着多少未显式传递的状态。

**调度器空转。** 定时器每 30 分钟触发一次 Agent，但当前没有有效的状态迁移可执行。Token 在燃烧，产出为零。

**权限模糊。** 谁有权合并 PR？谁可以执行生产部署？当多个 Agent 并行工作时，权限边界如果不显式定义，后果不可预测。

这些问题不是某个 Agent 运行时的 bug。它们是长程协作中天然出现的管理问题——只不过管理者变成了混合的 Agent-人类团队。

## 解法：一层薄的状态核

LoopX 的方案是引入一层持久化的控制状态。这层状态不参与 Agent 的推理过程，不替代 Agent 的执行能力，它在 Agent 完成一轮有界执行后，负责记录"发生了什么"、"下一步做什么"、"谁来决策"。

核心状态由六个元素组成：

```
objective   — 当前目标及其边界
gates       — 需要人类判断的检查点
todos       — 有序的用户/Agent 待办
scope       — 当前轮次的写权限边界
evidence    — 紧凑的运行历史和验证记录
quota       — 每个 Agent 可消耗的计算配额
```

这六个元素被组织在一个紧凑的本地状态文件中。Agent 每轮执行前读取状态，执行后写回证据和下一个待办。配额模块决定是否继续下一轮。

控制流的完整路径如下：

```
目标 / Issue / 项目
    │
    ▼
LoopX 状态：objective + gates + todos + scope + evidence + quota
    │
    ├─ 需要人类判断？ —— 是 → 提出具体问题并等待
    │
    ├─ 有安全侧路？ ——————————→ 执行一个有界 Agent 切片
    │
    ▼
Codex / Claude Code / Cursor / shell agent 执行一轮
    │
    ▼
写回证据 + 交接 + 下一条待办 → 配额决定下一次 tick
```

关键设计决策在这条控制流里清晰可见：

- **人类判断优先。** 如果当前状态需要用户决策，Agent 不会强行执行。系统会生成一个具体的问题（不是"等待 owner"这种模糊表述），然后暂停。
- **安全侧路可选。** 当主车道被门控阻塞，但存在经过审计的不触敏感操作的工作可做时，Agent 可以在侧路执行一个有界切片，而非空等。
- **配额是硬约束。** 每轮执行前先检查 `quota should-run`，只有完成验证和回写后才记录消耗。静默跳过、预检失败和预览模式不消耗配额。

## 心智模型：面向 Agent 的看板

LoopX README 用了一个精确的类比来帮助理解：**agent-native Kanban**（面向 Agent 的看板）。

传统看板的要素是卡片和泳道。LoopX 的对应关系是：

- **卡片 = 待办项**。每张卡片携带稳定身份标识、权限信息、证据指针和续跑上下文。
- **移动卡片 = 验证过的操作符**。你不能随意把卡片拖到"完成"。移动必须经过 claim（认领）、gate（门控检查）、monitor（监控）、validate（验证）、writeback（回写）这些有类型约束的操作符。
- **看板是投影，状态核才是真相源。** 你看到的 Kanban 面板——包括飞书看板适配器投影出的飞书多维表格——都是从 LoopX 状态文件渲染出来的只读视图。在面板上改状态不会影响真相。

这个设计有一个直接推论：**LoopX 不需要额外的状态存储来支撑看板**。状态文件本身就是唯一真相源，所有 UI、仪表盘、飞书投影都是它的消费者。

## Peer Agent 架构：没有 Leader 的协作

多 Agent 协作时，一个常见的模式是选出一个 leader Agent 来统筹全局。LoopX 不采用这种模式。

README 和架构文档明确声明：**Registered agents are peers. No durable leader identity is required.**（注册 Agent 是平级的。不需要持久的 Leader 身份。）

具体来说：

**每个注册 Agent 拥有平等的身份权限。** 一个 Agent 只拥有它已经 claim（认领）或 lease（租约）的工作，在当前目标边界内行动。Agent 可以检查或认领有资格的待办，推进一个有界的实现、验证、监控或修复切片，创建普通的后继任务，以及为自己的任务结果写回证据。

**谁来执行由四个机制决定：** claim/lease（谁认领了这条待办）、task boundaries（任务边界约束）、capabilities（能力门控）、typed continuation（有类型的续跑策略）。这四个机制替代了 leader 的角色。

**临时协调者是可选的、受限的。** 当需要编排一组任务（bounded orchestration），LoopX 会确定性选择一个临时协调者。这个协调者可以激活或恢复符合条件的 peer 车道，聚合已接受的证据。但它不会变成持久的 leader，不获得隐式的 review、merge、发布或重规划权限。

源码中的 `LoopXTurnRoute` 枚举定义了 Agent 执行前的路由决策：

```python
class LoopXTurnRoute(str, Enum):
    READY_FOR_HOST = "ready_for_host"
    REPAIR_REQUIRED = "repair_required"
    REPLAN_REQUIRED = "replan_required"
    USER_ACTION_REQUIRED = "user_action_required"
    WAIT = "wait"
    BLOCKED = "blocked"
    CONTRACT_ERROR = "contract_error"
```

执行后的结果分类由 `LoopXTurnResultKind` 枚举定义：

```python
class LoopXTurnResultKind(str, Enum):
    VALIDATED_PROGRESS = "validated_progress"
    VALIDATED_COMPLETION = "validated_completion"
    REPAIR_REQUIRED = "repair_required"
    REPLAN_REQUIRED = "replan_required"
    USER_ACTION_REQUIRED = "user_action_required"
    WAIT = "wait"
    HOST_FAILURE = "host_failure"
    VALIDATION_FAILED = "validation_failed"
    WRITEBACK_FAILED = "writeback_failed"
    QUOTA_SPEND_FAILED = "quota_spend_failed"
```

注意区分：口语化的"交付"在类型系统中拆分为 `validated_progress`（验证通过的进展）和 `validated_completion`（验证通过的完成）。"保持安静"是通知层面的行为，不属于 Turn 决策枚举的成员。

这些枚举来自 `loopx/control_plane/turn_driver/` 模块。它们不是文档概念，是实际运行的代码契约。

## 六层控制面架构

架构文档（`docs/architecture.md`）定义了六层持久控制面，外加一个可选的探测面：

**1. Registry（注册表）**。列出已知目标、它们的仓库、适配器、权限来源、状态和守卫。

**2. Goal State（目标状态）**。一个目标的活跃状态文件，包含当前信念、优先级栈、非目标和下一步行动。

**3. Run Log（运行日志）**。每个目标的 JSON 和 Markdown 报告。

**4. Run History（运行历史）**。紧凑索引，供 Agent、心跳和 UI 消费。

**5. Status / Attention Queue（状态/关注队列）**。首屏摘要，显示谁需要下一步行动。

**6. Compute Quota（计算配额）**。本地策略，控制每个目标可以消耗多少自动 Agent 计算。

四层运行时职责在架构文档中也有明确划分：

| 职责 | 拥有什么 | 不能拥有什么 |
|------|---------|-------------|
| Agent | 方案、分析、工具使用和一次有界执行 | 持久目标生命周期、无界效果权限 |
| Provider | 外部调用、有界观察、效果结果和回读 | 领域迁移策略或待办状态 |
| Capability | 调用者结果契约、领域策略、验证和类型化迁移提案 | 持久调度、claim、gate |
| Kernel | 目标、待办、claim、gate、监控、配额、回写、恢复和调度 | 领域特定推理 |

请求路径和结果路径方向相反：

```
Agent → Capability → Provider → 外部系统
外部观察/效果回读 → Provider → Capability
类型化迁移提案 → Kernel → 下一条待办/gate/监控/Turn
```

一个观察结果不是一次迁移。Provider 的回执不被视为已接受的进展，直到 Capability 验证它、Kernel 提交结果状态变更。这个设计避免了"Agent 说做完了就算做完"的信任问题。

## 四种 Turn 决策词汇

架构文档区分了操作员简写词汇和类型化决策枚举。面向操作员的文档和心跳提示常用六词简写：deliver（交付）、wait（等待）、ask（询问）、replan（重规划）、repair（修复）、stay quiet（保持安静）。

但实际的 Turn 契约使用两组枚举。执行前用 `LoopXTurnRoute`（7 个成员），执行后用 `LoopXTurnResultKind`（10 个成员）。简写遮蔽了几个重要区分：

- 口语"交付"拆成 `validated_progress` 和 `validated_completion`——进展和完成是两种不同结果。
- 失败种类（`host_failure`、`validation_failed`、`writeback_failed`、`quota_spend_failed`）是一等公民，不是笼统的"出错了"。
- "保持安静"是通知行为（如 `monitor_quiet_skip` 或心跳 `DONT_NOTIFY`），不属于 Turn 决策枚举。

实现或审查 Turn 适配器时，应优先参考枚举定义而非六词简写。

## 200+ 小时的真实运行证据

LoopX 提供了两条各跨越 200+ 小时自然时长的真实轨迹。这里的自然时长是项目从启动到最新证据的 wall-clock 时间，不等于 200 小时连续模型执行，也不代表无人值守的生产自治。

### OpenViking Issue-Fix 轨迹

LoopX 的创建者以 OpenViking 贡献者身份，使用 Issue-Fix 能力持续进行 issue-to-PR 修复。这条公开贡献序列从首个 PR 创建到最后一次 review 或 update，跨越 200+ 小时。

关键特征：Issue-Fix 能力将三件事分开管理——rolling repository context（滚动仓库上下文）、带 revision 标记的修复知识、reviewer-facing preference（面向审阅者的偏好）。所链接的 PR 与当前 checkout 的源码、测试始终具有最高权威。

这意味着：当一个 issue 在第 7 天被重新打开时，Agent 看到的不是第 1 天的旧上下文，而是经过 revision 标记的当前修复知识库。

### Auto ML Experiment 轨迹

owner-run 的机器学习实验，跨越 200+ 小时。在这条轨迹中，假设、matched evidence（匹配的证据）、无效谱系、运行中的复现、promote/stop gate 都保留在同一张决策图中。

这张经过脱敏的 public-safe graph 保留了自然时间窗口中的决策谱系。可以检查为什么某条假设被废弃，为什么某条谱系被判无效，以及什么时候触发了 promote 或 stop 决策。

### Auto Research 多 Agent 轨迹

第三条证据展示了多 Agent 并行迭代：Proposer（提议者）、Executor（执行者）、Evaluator/Promoter（评估者/晋升者）同时工作。待办、配额、证据和 targeted wake 在同一屏可见。

## 五行核心 Tick

LoopX 的核心 Agent 交互循环刻意保持简小。自定义 runner 集成指南展示了五个命令组成的 tick：

```bash
loopx quota should-run      # 当前注册 Agent 是否应该执行？
loopx todo claim            # 谁拥有这个切片？
loopx todo update           # 发生了什么？
loopx refresh-state         # 下一轮应该看到什么？
loopx quota spend-slot      # 为完成并验证的切片记账
```

这五行命令构成一个完整的 Agent 执行周期：检查配额、认领工作、更新状态、刷新视图、记录消耗。任何自定义 runner——无论是 shell 脚本、cron 任务还是 Agent 运行时——只需要实现这五行调用的等价逻辑。

## 日常操作

日常检查从三个命令开始：

```bash
loopx status                              # 当前目标、门控和下一条待办
loopx history --goal-id your-goal         # 紧凑运行历史
loopx quota should-run --goal-id your-goal # 是否应该执行
```

自动轮次必须先检查配额。只有完成验证和回写后才记录消耗。当一个车道被用户门控阻塞时，经过独立审计的安全侧路可以继续，但不能绕过门控。

公开发布前运行边界扫描：

```bash
loopx check \
  --scan-path README.md \
  --scan-path docs/ \
  --scan-path examples/
```

这个扫描检查公共文档中是否泄露了私有路径、凭据、内部链接等敏感信息。扫描规则在 `loopx/contract.py` 中定义，覆盖 private doc URL、credential pattern、local private path、internal task ID、private IP 五类泄露模式。

## Host 集成：一行安装，多平台

LoopX 的安装刻意不依赖 Git clone：

```bash
curl -fsSL https://raw.githubusercontent.com/huangruiteng/loopx/main/scripts/install-from-github.sh | bash
export PATH="$HOME/.local/bin:$PATH"
loopx doctor
```

Python package 除标准库外没有运行时依赖。`pyproject.toml` 的 `dependencies = []` 是字面意义的空列表。

连接到项目后，LoopX 支持多种 Host：

| Host | 推荐入口 | Loop 驱动 |
|------|---------|----------|
| Codex App | 在项目中连接 LoopX，运行 `loopx doctor`，使用 `$loopx <任务>` | Codex App heartbeat |
| Codex CLI | 在项目中启动 `codex`，连接并诊断 LoopX | 可见 `/goal <任务>` |
| Claude Code | 安装可选适配器，运行 `/loopx <任务>`，再运行 `/loop` | LoopX gate 驱动的原生 Claude Code `/loop` |
| Cursor / shell / 自定义 | 使用同一 installer 和 `loopx doctor` | 你的 shell、scheduler 或 runner |

跨 runtime 的协作演示在仓库中有记录：Claude 负责实现，Codex 负责审查，LoopX 保持所有权、证据、配额和交接的显式追踪。

## 能力体系：五个用户可行动的问题

LoopX 把控制面归结为五个用户可以直接行动的问题：

| 问题 | LoopX 保持可见的状态 |
|------|---------------------|
| 当前目标是什么？ | Active goal、明确 scope 和当前 authority |
| 下一步是什么？ | 有序 user/agent todo、ownership、claim 和 lease |
| 哪一步需要人判断？ | 具体 user gate，不是模糊的"等待 owner" |
| 证据发生了什么变化？ | 紧凑 run history、验证、blocker 和已接受 writeback |
| Loop 是否可以继续？ | Quota、capability、安全侧路、scheduler hint 和停止条件 |

这五个问题对应的控制面能力包括：Goal state 与 status、Quota 与 interaction contract、Agent runtime bridge、Operator surface、External projection（飞书看板适配器）、Domain capability（Issue Fix、内容运营、ML 实验、benchmark、Explore）。

实验性上下文学习能力（Reward Memory）默认关闭，需要通过项目配置显式 opt in。

## 边界：LoopX 不做的事

LoopX 的 README 和架构文档反复强调一条红线：

> LoopX is not an autonomous production controller.

具体而言：

- **不自行获取凭据。** 不会替用户去拿 credential。
- **不批准危险操作。** destructive、production action 需要人类显式批准。
- **不未授权发布。** 不会在用户未授权时进行公开发布。
- **不把未验证的 run 当成功证据。** 一个 run 必须通过 Capability 验证、Kernel 提交才算 accepted progress。

治理文档（`GOVERNANCE.md`）进一步明确：Agent 和自动化可以准备变更、运行验证、出现在 commit 来源中，但它们不会变成人类维护者，不能自行授予仓库权限。人类维护者对 merge、release 和边界决策保持最终责任。

## 技术实现

**Python 3.11+，零运行时依赖。** `pyproject.toml` 中 `dependencies = []` 是空列表。测试依赖包括 pytest、jsonschema、ruff、mypy，但这些都是开发时依赖。

**Monorepo 结构：**

```
loopx/          核心 kernel 包（80+ 模块）
  control_plane/  控制面子系统（goals, todos, quota, handoff, scheduler, turn_driver）
  capabilities/   领域能力（issue-fix, explore, auto-research, content-ops）
  extensions/     可选扩展（lark, openviking）
  presentation/   渲染器
apps/           应用层（dashboard）
packages/       独立分发包
skills/         项目级 skill（loopx-self-repair, loopx-pr-review 等 6 个）
docs/           完整文档（architecture, concepts, guides, operations）
examples/       460+ 示例和 smoke 测试
tests/          测试套件
regression/     回归测试
```

`control_plane/` 目录的结构直接映射架构文档的六层模型。`turn_driver/` 模块包含 Turn 决策的完整实现：driver（路由决策）、executor（执行）、transaction（事务）、codex_cli（Codex CLI 集成）。

mypy strict 模式覆盖核心模块。架构测试强制约束依赖方向：`control_plane` 不允许依赖 presentation、CLI、capability 或 benchmark-adapter 层。

## Lifetime Goal：年的尺度，不是分钟的尺度

架构文档定义了一个产品级不变量，叫做 Lifetime Goal Invariant（终身目标不变量）：

> LoopX should optimize for lifetime goals: durable intentions that may outlive a single thread, executor, project phase, or plan.

一个 lifetime goal 必须满足两个条件：

1. **足够稳定**——未来的 Agent 或人类可以恢复目标是什么、当前定义是什么、谁可以修改、下一个安全迁移是什么。
2. **足够窄**——自动化可以做一次有界的、可验证的移动，而不是声称无界的权限。

这个不变量映射到架构的每一层：Registry 提供稳定身份和边界，Goal State 记录当前信念，Authority Sources 替代隐式模型记忆，Run History 保留跨会话证据，Todos 将终身目标分解为有界义务，Gates/Quota 将人类判断和计算消耗绑定到具体迁移。

结果是：一个目标可以存活数年，但每一轮 Agent Turn 仍然必须通过当前的 authority、boundary、quota、validation 和 writeback，才能算作进展。

## 本地服务器路线图

CLI 是当前的兼容基线。未来的本地服务器路线图分六步落地：

1. **写入正确性**：在引入服务器之前，让现有 CLI 写入在并发条件下安全（per-goal 锁、幂等键、乐观版本检查）。
2. **租约采纳**：可选的本地 `task_lease_v0` CLI 提供 owner、TTL、写范围、幂等性、冲突、转移和释放语义。
3. **回环协调者**：扩展现有本地状态服务器为回环协调者，集中 per-goal 锁、租约、配额决策和心跳调度。
4. **心跳调度器**：将周期性心跳簿记移到协调者后面（在配额/消耗幂等性被证明之后）。
5. **规划和 dreaming 队列**：让后台规划产生排名待办提案、证据探测和重构警告作为建议记录。
6. **Host 适配器**：通过 MCP、hook 或小型本地 HTTP API 暴露相同契约。

验收标准：同一操作在 daemon 停止后仍可通过 CLI 完成；重复心跳、重复配额消耗或过期待办更新成为显式 no-op 或冲突；状态显示活跃租约和当前 owner；所有紧凑服务器响应通过公共/私有边界扫描。

## 应用场景

基于 README 和两类证据轨迹，LoopX 适合的场景包括：

- **多日或多周的工程目标**——issue/PR 循环、功能开发、重构项目
- **研究目标**——ML 实验、benchmark 运行、假设验证
- **Recurring 监控**——心跳驱动的 PR watch、依赖扫描、changelog 草拟
- **带门控的项目**——需要 owner 审批、安全检查、发布门控的工作流
- **平级 Agent 团队**——多 Agent 认领、租约、交接、并行执行
- **创作者/研究/运营工作流**——进展需要清晰呈现给非工程人员的项目

## Takeaway

**1. 控制面不是运行时。** LoopX 的核心洞察是把"谁在执行"和"什么状态在跨轮次持久"分离。Codex、Claude Code、Cursor 负责前者，LoopX 负责后者。这种分离让 Agent 可以替换，而管理状态不丢失。

**2. 看板是投影，状态文件是真相。** 所有 UI——仪表盘、飞书看板、frontstage——都是从状态文件渲染的只读视图。在投影上修改不会影响真相。这个设计避免了多源同步问题。

**3. Peer Agent 不需要 Leader。** 通过 claim/lease/task-boundaries/capabilities/typed-continuation 五个机制，平级 Agent 可以协作而不需要选出持久的协调者。临时协调者的权限受到严格限制。

**4. 配额是硬约束，不是建议。** 每轮执行前检查配额，验证通过后才记录消耗。这防止了"调度器空转烧 token"的问题。一个被门控阻塞的车道不会消耗配额。

**5. 200+ 小时的证据比任何 demo 有说服力。** LoopX 没有停留在"理论上可以工作"。两条各跨越 200+ 小时自然时长的真实轨迹——一条在公开开源项目中，一条在 ML 实验中——展示了控制面在真实长程工作中的价值。
