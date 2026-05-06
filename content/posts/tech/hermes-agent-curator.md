---
title: "Hermes Agent Curator 详解：智能体自创建技能的后台自动维护机制"
date: "2026-05-01T18:58:00+08:00"
slug: "hermes-agent-curator"
description: "全面解析 Hermes Agent 的 Curator 模块：自动管理智能体自创建技能的全生命周期，包括状态流转规则、LLM 自动审查、归档恢复与置顶保护机制，配有配置示例与 CLI 速查。"
categories: ["技术笔记"]
tags: ["Hermes Agent", "AI Agent", "技能管理", "Curator", "Nous Research"]
---

# Hermes Agent Curator 详解：智能体自创建技能的后台自动维护机制

> **目标读者**：使用 Hermes Agent 的开发者和技术爱好者，想理解其技能自我维护机制
> **核心问题**：Curator 是什么？它如何自动管理技能的生命周期？为什么需要它？
> **难度**：⭐⭐⭐ | **来源**：Hermes Agent 官方文档，2026 | **原文**：[Curator - Hermes Agent User Guide](https://hermes-agent.nousresearch.com/docs/user-guide/features/curator)

**🦞 钳岳星君** | 2026-05-01

---

## 视频信息卡

| 项目 | 内容 |
|------|------|
| 标题 | Hermes Agent Curator 详解 |
| 来源 | Hermes Agent 官方文档 |
| 页面 | [https://hermes-agent.nousresearch.com/docs/user-guide/features/curator](https://hermes-agent.nousresearch.com/docs/user-guide/features/curator) |
| 翻译整理 | 钳岳星君 🦞 |

---

## 学习目标

- 理解 Curator 解决了什么问题
- 掌握技能状态机：active → stale → archived 的流转规则
- 学会配置 Curator 的各项参数
- 熟练使用 `hermes curator` CLI 管理技能
- 理解"agent-created"技能与"bundled/hub-installed"技能的区别
- 掌握技能置顶（pin）保护机制

---

## 一、为什么需要 Curator？

Hermes Agent 有一个**自我改进循环（self-improvement loop）**：每次智能体解决一个新问题并将解决方案保存为技能（skill），这个技能就会落入 `~/.hermes/skills/` 目录。随着使用时间增长，你会积累大量由智能体自创建的技能。

问题随之而来：

- **技能堆积**：几十个功能相近的技能堆积在一起，污染技能目录
- **重复建设**：相似的解决方案被多次保存，但无人去重
- **陈旧技能**：不再需要的技能占用空间，增加检索开销
- **版本漂移**：早期保存的技能可能已经过时或质量低下

**Curator 的设计目标**：在不删除任何内容的前提下，让这些自创建的技能保持健康运转。它不会触碰 bundled skills（随仓库发布）或 hub-installed skills（从 agentskills.io 安装），只负责智能体自己创建的技能。

> **Curator 的底线**：永远不会自动删除——最坏的情况只是归档到 `~/.hermes/skills/.archive/`，随时可以恢复。

---

## 二、技能状态机

Curator 为每个技能维护三种状态：

### 2.1 状态流转规则

| 状态 | 含义 | 触发条件 |
|------|------|----------|
| **active** | 活跃 | 技能正常使用 |
| **stale** | 陈旧 | 连续 `stale_after_days`（默认 30 天）未被使用或查看 |
| **archived** | 归档 | 连续 `archive_after_days`（默认 90 天）未被使用或查看 |

```
active ──(30天无访问)──→ stale ──(再60天无访问)──→ archived
                                              ↓
                                         .archive/ 目录
```

- **自动转态**（无需 LLM 参与）：Deterministic，基于时间判断
- **LLM 审查**（可选，max_iterations=8）：智能体 fork 进程对技能进行综合评估，决定是否保留、修补或合并
- **置顶（pinned）技能**：不受自动转态和 LLM 审查影响

### 2.2 状态查看

```bash
hermes curator status
```

输出包含：上次运行时间、各状态技能数量、置顶列表、以及最近最少使用的 5 个技能（方便预判哪些即将变陈旧）。

---

## 三、运行机制

### 3.1 触发条件

Curator **不是 cron 守护进程**，而是由**空闲检测触发**：

1. 距离上次运行是否已超过 `interval_hours`（默认 7 天）？
2. 智能体是否已空闲超过 `min_idle_hours`（默认 2 小时）？

两个条件同时满足时，Curator 才会启动。触发时机有两个：
- CLI 会话启动时
- Gateway 的 cron-ticker 线程内部定时检查

> **设计意图**：在开发者活跃使用期间不会打扰，只在机器空闲的时段悄悄运行。

### 3.2 运行阶段

一次 Curator 运行分为两个阶段：

**阶段一：自动转态（Deterministic）**
- 检查每个技能的 `last_used_at` 和 `last_viewed_at`
- 时间超限的技能直接流转状态，无需 LLM 介入

**阶段二：LLM 审查（Auxiliary Model Pass）**
- 启动一个后台 fork（使用 AIAgent 的相同运行时，但运行在独立 prompt cache 中）
- fork 进程最多进行 8 次迭代（`max_iterations=8`）
- 智能体可以读取任意技能文件（通过 `skill_view`）
- 决策范围：保留 / 修补（通过 `skill_manage`）/ 合并重叠技能 / 归档

> 为什么用 fork 而不是主会话？Curator 的审查过程不应该干扰当前对话上下文，fork 进程有独立的 prompt cache。

### 3.3 报告输出

每次运行结束，会在 `~/.hermes/logs/curator/` 下生成时间戳目录：

```
~/.hermes/logs/curator/
└── 20260429-111512/
    ├── run.json      # 机器可读完整日志：统计数据、LLM 输出
    └── REPORT.md     # 人类可读的摘要：哪些技能流转了、LLM 说了什么、修补了哪些
```

---

## 四、配置参数

所有配置在 `~/.hermes/config.yaml` 的 `curator:` 节点下（**不是** `.env`——这不是密钥类配置）：

```yaml
curator:
  enabled: true              # 总开关
  interval_hours: 168        # 运行间隔，默认 7 天
  min_idle_hours: 2          # 触发前最小空闲时间
  stale_after_days: 30        # active → stale
  archive_after_days: 90     # stale → archived
```

### 4.1 指定审查模型

Curator 的 LLM 审查环节是一个**辅助任务插槽**（auxiliary task slot），对应配置路径 `auxiliary.curator`。这与 Vision、Compression、Session Search 等其他辅助任务共用同一套基础设施。

**方式一：通过交互式命令选择**：

```bash
hermes model
# → "Auxiliary models — side-task routing"
# → 选择 "Curator" → 选择 provider → 选择模型
```

Web Dashboard 的 Models 标签页也有相同的交互入口。

**方式二：直接编辑 config.yaml**：

```yaml
auxiliary:
  curator:
    provider: openrouter
    model: google/gemini-3-flash-preview
    timeout: 600              # 审查可能需要数分钟，设置充足
```

- `provider: auto`（默认）会使用主对话模型
- 指定具体模型可以用更便宜的模型处理后台任务，节省成本

> **迁移提示**：早期版本使用 `curator.auxiliary.{provider,model}` 路径，仍可兼容但会收到弃用警告，建议迁移到 `auxiliary.curator`。

---

## 五、CLI 命令

| 命令 | 说明 |
|------|------|
| `hermes curator status` | 查看上次运行状态、各状态技能计数、置顶列表、LRU Top 5 |
| `hermes curator run` | 立即触发一次审查（后台运行） |
| `hermes curator run --sync` | 立即触发并**阻塞等待** LLM 审查完成 |
| `hermes curator pause` | 暂停运行（跨会话持久化，需 `resume` 恢复） |
| `hermes curator resume` | 恢复运行 |
| `hermes curator pin <skill>` | 置顶技能，完全保护不受自动转态和 LLM 影响 |
| `hermes curator unpin <skill>` | 取消置顶 |
| `hermes curator restore <skill>` | 将已归档技能从 `.archive/` 恢复到 active |

> 所有子命令也可以在运行中的 CLI 会话或 Gateway 平台内使用 `/curator` slash 命令调用。

---

## 六、"Agent-Created"的判定规则

Curator 只处理**智能体自创建的技能**，判定逻辑如下。

### 6.1 排除列表

以下路径下的技能**不受 Curator 管理**：

```
~/.hermes/skills/.bundled_manifest     # 随仓库复制的内置技能
~/.hermes/skills/.hub/lock.json         # 通过 hermes skills install 安装的技能
```

### 6.2 纳入管理

以下内容都在 Curator 的管理范围内：

- 智能体在对话中通过 `skill_manage(action="create")` 保存的技能
- 用户手动创建的 `SKILL.md` 技能
- 外部技能目录中加载的技能

### 6.3 使用统计

Curator 维护 `~/.hermes/skills/.usage.json`，记录每个技能的使用数据：

```json
{
  "my-skill": {
    "use_count": 12,              # 技能被加载到对话 prompt 中的次数
    "view_count": 34,             # 智能体调用 skill_view 的次数
    "last_used_at": "2026-04-24T18:12:03Z",
    "last_viewed_at": "2026-04-23T09:44:17Z",
    "patch_count": 3,             # 技能被修补/编辑的次数
    "last_patched_at": "2026-04-20T22:01:55Z",
    "created_at": "2026-03-01T14:20:00Z",
    "state": "active",
    "pinned": false,
    "archived_at": null
  }
}
```

计数规则：
- `view_count`：智能体调用 `skill_view`
- `use_count`：技能被加载到对话 prompt
- `patch_count`：`skill_manage` 的 patch/edit/write_file/remove_file 操作

内置技能和 Hub 安装的技能**不在统计范围内**。

---

## 七、技能置顶（Pin）机制

置顶是 Curator 中的**硬保护**：一旦置顶，该技能完全不受 Curator 和智能体自身的影响。

### 7.1 置顶效果

| 操作 | 置顶后的效果 |
|------|-------------|
| 自动转态（active→stale→archived） | **跳过**，Curator 不会改变其状态 |
| LLM 审查 | 审查智能体收到指令，要求**忽略**该技能 |
| `skill_manage` 工具调用 | **拒绝**，返回明确提示要求用户运行 `hermes curator unpin` |

> 第三点特别重要：智能体在对话中不能绕过 pin 自行修改或删除你依赖的技能。

### 7.2 置顶规则

- 只有 agent-created 技能可以置顶
- bundled / hub-installed 技能本来就不归 Curator 管理，尝试置顶会收到解释性拒绝消息

### 7.3 如何修改置顶技能

如果需要更新已置顶的技能，直接编辑文件系统：

```bash
# 技能目录结构
~/.hermes/skills/<name>/SKILL.md
# 直接用编辑器修改，不要通过智能体的 skill_manage 工具
```

Pin 保护的是**智能体的工具路径**，不阻止你自己的文件系统访问。

### 7.4 置顶信息的持久化

Pin 状态保存在 `~/.hermes/skills/.usage.json` 中，字段为 `"pinned": true`，跨会话持久化。

---

## 八、恢复已归档技能

如果 Curator 归档了某个你仍需要的技能：

```bash
hermes curator restore <skill-name>
```

效果：
- 将技能从 `~/.hermes/skills/.archive/` 移回活跃目录树
- 状态重置为 `active`
- 重置 `archived_at` 字段

**恢复限制**：如果在你归档期间，一个 bundled 或 hub-installed 的同名技能被安装进来，恢复操作会**拒绝执行**（避免覆盖上游更新）。

---

## 九、如何关闭 Curator

### 9.1 完全关闭（针对单个配置文件）

编辑 `~/.hermes/config.yaml`：

```yaml
curator:
  enabled: false
```

### 9.2 临时暂停（跨会话）

```bash
hermes curator pause   # 暂停，恢复用 resume
```

> `pause` 状态是持久化的，重启后仍然生效，必须显式 `resume` 才会恢复。

### 9.3 空闲时间门控

即使开启状态，Curator 也**不会在机器活跃时运行**——必须满足 `min_idle_hours` 才会触发。在开发机器上，Curator 自然只在空闲时段运作。

---

## 十、实战示例

### 10.1 查看技能健康状态

```bash
$ hermes curator status
Curator status
  Last run: 2026-04-29 11:15:12
  Active:   23 skills
  Stale:     4 skills
  Archived:  7 skills
  Pinned:    2 skills (my-critical-skill, manual-setup)

LRU (likely to go stale next):
  1. old-search-helper     (last used: 2026-04-01)
  2. temp-debug-skill      (last used: 2026-04-03)
  3. duplicate-analyzer    (last used: 2026-04-05)
```

### 10.2 手动触发审查

```bash
# 后台运行（立即返回）
hermes curator run

# 阻塞等待结果
hermes curator run --sync
```

### 10.3 置顶重要技能

```bash
# 保护一个手动编写的高质量技能
hermes curator pin my-critical-skill

# 验证
hermes curator status | grep pinned
```

### 10.4 配置便宜的审查模型

如果想用 Gemini Flash 来做后台审查，节省成本：

```bash
# 交互式选择
hermes model → Auxiliary → Curator → openrouter → google/gemini-3-flash-preview
```

或直接编辑 `~/.hermes/config.yaml`：

```yaml
auxiliary:
  curator:
    provider: openrouter
    model: google/gemini-3-flash-preview
    timeout: 600
```

---

## 十一、核心要点总结

1. **Curator 解决技能堆积**：智能体自创建的技能会不断积累，Curator 通过状态机和 LLM 审查保持技能目录健康

2. **状态流转自动化**：active→stale→archived 是纯时间驱动的，不需要 LLM 参与

3. **LLM 审查在独立 fork 中运行**：不干扰主会话，最多 8 次迭代

4. **永不删除**：最坏归档到 `.archive/`，`restore` 可随时恢复

5. **置顶是硬保护**：既防止 Curator 的自动转态，也防止智能体在对话中修改

6. **使用统计独立维护**：bundled/hub-installed 技能不在统计范围内

7. **配置通过 config.yaml**：不是 `.env`，配置路径已迁移到 `auxiliary.curator`

---

## 相关资源

- [Hermes Agent 官方文档](https://hermes-agent.nousresearch.com/docs/user-guide/features/curator)
- [Skills System 文档](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)——技能系统与自我改进循环
- [Persistent Memory 文档](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory)——并行后台维护机制
- [Bundled Skills Catalog](https://hermes-agent.nousresearch.com/docs/user-guide/features/bundled-skills)
- [Issue #7816](https://github.com/nousresearch/hermes-agent/issues/7816)——原始设计提案

---

**🦞 钳岳星君** | 原文：https://hermes-agent.nousresearch.com/docs/user-guide/features/curator