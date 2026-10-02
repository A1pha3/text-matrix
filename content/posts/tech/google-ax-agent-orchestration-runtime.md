---
title: "google/ax：把自治智能体当成一种工作负载来编排"
date: "2026-10-03T03:50:00+08:00"
slug: "google-ax-agent-orchestration-runtime"
github_repo: "google/ax"
source_key: "gh:google/ax"
description: "Google开源的agentic编排运行时ax（12.8K Stars，Go，Apache-2.0），用Task/Workspace/Model三个声明式原语在Kubernetes集群上运行沙箱化智能体任务，提供suspend/resume检查点与ax ssh观测能力。本文拆解其架构、概念模型与上手路径。"
draft: false
categories: ["技术笔记"]
tags: ["Google", "智能体", "Kubernetes", "Go", "开源", "编排"]
---

# google/ax：把自治智能体当成一种工作负载来编排

> **目标读者**：平台工程师、智能体基础设施团队、需要在集群规模上跑自治任务的技术决策者
> **文章形态**：原理拆解 / 架构分析
> **证据来源**：google/ax 仓库 README 与 docs/（2026-10-02 取证），版本 v0.3.1

## 核心判断

AX 是 Google 开源的智能体编排运行时（agentic orchestration runtime），它的核心主张可以用一句话概括：**自治智能体是一种新的工作负载类型，需要专门的控制平面，而不是塞进现有容器编排或工作流引擎里凑合**。

这个判断值得认真对待。智能体既不是无状态微服务，也不是跑完即退的批处理任务——它会积累状态、需要严格隔离、会持续调用模型 API 和工具服务，而且"没人盯着就在循环里烧钱"是真实风险。现有基础设施对这四种特性的支持都是间接的：Kubernetes 管生命周期但不懂模型凭证，工作流引擎管步骤但不提供沙箱。

AX 的解法是给出三个声明式原语（Workspace、Task、Model），加上一组 kubectl 风格的动词，跑在 Kubernetes 之上。仓库目前 12,879 Stars、639 Forks，主语言 Go，Apache-2.0 协议，2026 年 3 月创建，最新版本 v0.3.1（2026-09-25 发布）。需要 upfront 说明：README 顶部有明确的 WARNING——核心概念、协议和规范仍在快速演进，稳定版之前很可能有破坏性变更。

## 系统地图：三个原语 + 一个沙箱层

理解 AX 先记住这张对照表（来自 README 的"Why?"一节）：

| 你想要 | AX 给你的原语 |
|---|---|
| 在带 CPU/内存限制的隔离沙箱里跑不受信任的智能体代码 | `Task` |
| 预接好 Git 仓库、MCP 服务器、技能包，让每个智能体"热启动" | `Workspace` |
| 声明平台自身用哪个 LLM，凭证来自 Kubernetes Secret | `Model` |
| 暂停空闲智能体，之后从断点精确恢复 | `ax suspend` / `ax resume` |
| 钻进运行中的智能体里看它在干什么 | `ax ssh` |

分层看，AX 的架构是：

- **下层：Agent Substrate**。AX 不自己做沙箱，每个任务被调度为 Substrate 上的沙箱化 actor（substrate 是独立仓库 `agent-substrate/substrate`），获得执行隔离与资源限制。这是部署 AX 的硬前置——Substrate 必须先在集群里跑起来，AX 通过其 Control API（`api.ate-system.svc.cluster.local:443`）通信。
- **中层：AX 控制平面**。负责解析 `ax.io/v1alpha1` 声明、调度任务到 actor、维护任务状态机（phase 与 condition）。
- **上层：`ax` CLI**。gRPC 连控制平面，刻意做成 kubectl 手感：`apply` / `get` / `describe` / `watch` / `delete`，外加几个智能体专属动词。

一个值得注意的架构决策记录在 2026-09-26 的提交里：*"Replace Redis Streams queue and controller with direct execution and resource locking"*——用直接执行加资源锁替换了原先基于 Redis Streams 的队列与控制器。这说明 v0.3.x 阶段核心执行路径仍在做减法，选型时要把"接口可能变"计入成本。

## 一个任务的一生：从 YAML 到沙箱

AX 的声明式体验长这样。先定义 Workspace（预接代码）和 Task（要跑的智能体）：

```yaml
# task.yaml
apiVersion: ax.io/v1alpha1
kind: Workspace
metadata:
  name: golang
spec:
  git:
    - repo: https://github.com/golang/go.git
      branch: "my-fix"
---
apiVersion: ax.io/v1alpha1
kind: Task
metadata:
  name: test
spec:
  workspaces:
    - name: golang
      goal: "Ensure that Go tool chain is available and is built from source"
  debug: true   # 开了才能 ax ssh 进沙箱
```

然后是一组对 Kubernetes 用户毫无学习成本的命令：

```bash
ax apply -f task.yaml
ax get tasks
# NAME      ATESPACE   PHASE     ACTOR           WORKER-IP    AGE
# task123   default    Running   task123         10.20.3.67   1m

ax watch task task123                # 流式看 phase / condition 变化
ax ssh task123 -- ls -la /workspace  # 进沙箱执行命令
ax suspend task task123              # 打检查点并暂停
ax resume task task123               # 从断点恢复
```

`suspend`/`resume` 是最能体现"智能体是特殊工作负载"的一对命令：自治任务经常进入长空闲（等外部事件、等人工确认），checkpoint 暂停再精确恢复，直接对应成本问题——空闲的 actor 不必一直占着资源。

## 上手路径与真实成本

前置条件比一般开源项目重：你需要一个 Kubernetes 集群、装好 Agent Substrate、Go 工具链、`ko`，以及一个集群能拉取镜像的 registry。之后三步：

```bash
# 1. 装 CLI
go install github.com/google/ax/cmd/ax@latest

# 2. 部署控制平面（会部署 Redis，镜像推到你指定的 registry）
make deploy AX_IMAGE_REPO=<your-registry>

# 3. 跑第一个任务
ax apply -f examples/task.yaml
```

README 明确说 AX "如果用过 Kubernetes 会感到相似"——这既是优点也是门槛：它不试图降低 K8s 的复杂度，而是在 K8s 之上加一层智能体语义。没有集群运维能力的团队，上手成本是真实的。

文档是这套系统的强项：`docs/concepts.md` 讲三个原语与任务 phase/condition 生命周期，`docs/manifests.md` 给每种 kind 的完整注解示例，`docs/sandbox.md` 说明沙箱启动时runner 做了什么、能依赖哪些 guest 服务，`docs/runner.md` 定义控制平面与任务容器之间的契约（可替换默认 runner 镜像），`docs/networking.md` 讲通过 atenet 路由从集群、笔记本或 gRPC 客户端触达运行中的任务。DESIGN.md 提供架构全文与 API 参考。这套文档密度在 v0.3 阶段的开源项目里不多见。

## 边界与采用建议

**本文不覆盖**：AX 内部控制平面源码、与 LangGraph/CrewAI 等编排框架的横向对比（它们解决的是单进程内的流程编排，AX 解决的是集群级的工作负载运行，层次不同）、以及任何性能数据——仓库目前没有公开 benchmark，本文不做推断。

**风险清单**：

1. 官方 WARNING 级的不稳定承诺：v1 之前可能有破坏性变更，接口级依赖要谨慎。
2. 强依赖外部项目 Agent Substrate，两个仓库的版本耦合需要一起评估。
3. v0.3.1 距 v0.3.0（2026-09-20）仅 5 天，迭代节奏快，升级策略要提前想好。

**采用顺序建议**：如果你在构建内部智能体平台、需要批量跑不受信任的自治任务，AX 的"声明式 + 沙箱 + 检查点"组合是目前这个方向上最完整的开源尝试之一，值得在非生产环境跟踪其概念演进；如果只是想编排单个智能体的工具调用流程，AX 的集群级抽象是杀鸡用牛刀，选轻量框架更合适。

---

**仓库信息**：[google/ax](https://github.com/google/ax) · Go · Apache-2.0 · 12.8K Stars / 639 Forks · 创建于 2026-03-30 · 最新 Release v0.3.1（2026-09-25）· 主页 [agentexecutor.io](https://agentexecutor.io)
