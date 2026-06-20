---
title: "Evolver：基于GEP协议的自进化AI Agent引擎，完全指南"
date: "2026-04-17T11:36:00+08:00"
slug: "evomap-evolver-self-evolution-engine-guide"
description: "Evolver是一款基于Genome Evolution Protocol（GEP）的自进化引擎，专为AI Agent设计，将临时性的Prompt调整转化为可审计、可复用的进化资产。本文全面介绍Evolver的安装、基本概念、架构设计、使用方法和开发扩展。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "自进化", "GEP协议", "Prompt工程", "Node.js", "Evolver"]
featuredImage: ""
extraMetadata:
  language: javascript
  version: "1.0.0"
  repo: https://github.com/EvoMap/evolver
  stars: 3862
  forks: 392
  updated_date: "2026-04-17"
---

# Evolver：基于 GEP 协议的自进化 AI Agent 引擎，完全指南

🦞 作者：钳岳星君 | 更新时间：2026-04-17

---

## §1 Evolver 解决的核心问题

Evolver 把 AI Agent 的临时 Prompt 调整改造成可审计、可复用的进化资产。它定位为 Prompt 生成器，基于 GEP（Genome Evolution Protocol）协议运行：扫描 `memory/` 目录的运行时日志，从 `assets/gep/` 选择匹配的 Gene 或 Capsule，输出协议化的 Prompt，并把每次变更记录为 EvolutionEvent。Agent 的改进方式因此从"凭经验手动调"变成"按协议自动迭代"，同时严格不触碰代码编辑和 Shell 执行——这条边界是它安全模型的基础。

本文覆盖以下内容：

1. GEP 协议的概念和设计思路
2. Evolver 的安装和配置，包括独立运行和连接 EvoMap 网络
3. Evolver 的架构设计，以及自进化机制的工作原理
4. 四种运行模式：单次运行、审核模式、循环模式、OpenClaw 集成
5. Operations 模块：生命周期管理、健康检查和自动重启
6. Evolver 的安全模型和适用边界
7. 基因（Gene）和胶囊（Capsule）的创建与使用

---

## §2 学习目标

读完本文后，你应当能够：

1. 说清 GEP 协议的三个基础概念（Gene、Capsule、EvolutionEvent）以及它们在一次进化周期里各自承担的职责
2. 区分 Evolver 的四种运行模式（Standalone、Review、Loop、OpenClaw 集成），并能为不同环境选择合适的模式
3. 解释日志分析器、选择器、Prompt 生成器三个模块如何串联成一条完整的进化流水线
4. 根据系统状态选择 `EVOLVE_STRATEGY` 的四种策略（balanced、innovate、harden、repair-only）
5. 编写一个自定义 Gene 或 Capsule，并说明它的信号匹配规则和触发条件
6. 判断 Evolver 是否适合你的场景——哪些团队应该先用，哪些场景暂时不必引入

---

## §3 系统总览

Evolver 由四个核心模块组成，按数据流向串联。下图展示了从日志输入到 Prompt 输出的完整路径，以及 EvolutionEvent 的记录回路：

```
┌─────────────┐     扫描      ┌──────────────┐     选择      ┌─────────────┐
│ memory/目录  │ ──────────> │ Analysis     │ ──────────> │ Selection   │
│ (运行时日志) │              │ (日志分析器)  │              │ (Gene/Capsule│
└─────────────┘              └──────────────┘              │  选择器)     │
                                                            └─────────────┘
                                                                  │
                                                                  v
┌─────────────┐     记录      ┌──────────────┐     输出      ┌─────────────┐
│ Evolution   │ <────────── │ Evolution    │ <───────── │ Evolution   │
│ Event日志   │             │ (事件记录器)  │             │ (Prompt生成器)│
└─────────────┘             └──────────────┘             └─────────────┘
```

四个模块的职责边界如下表。理解边界比理解功能更重要——Evolver 的安全模型就建立在这些边界之上：

| 模块 | 目录 | 输入 | 输出 | 边界 |
|------|------|------|------|------|
| Analysis（日志分析器） | `src/analysis/` | `memory/` 目录的运行时日志 | 错误模式、性能信号、行为轨迹 | 只读，不修改源码 |
| Selection（选择器） | `src/selection/` | Analysis 的输出 | 匹配的 Gene 或 Capsule | 不生成 Prompt，只做匹配 |
| Evolution（进化引擎） | `src/evolution/` | 选中的 Gene/Capsule | GEP 协议化的 Prompt | 不执行 Prompt，只输出到 stdout |
| Operations（运维模块） | `src/ops/` | 进程状态、健康指标 | 启停、重启、清理动作 | 不参与进化逻辑，只管进程生命周期 |

关键边界：Evolver 全程不编辑源代码、不执行 Shell 命令。它只生成 Prompt 并记录事件，由宿主（如 OpenClaw）决定是否执行。完整目录结构见 §5 架构分析。

---

## §4 原理分析

### 4.1 为什么需要自进化引擎？

在 AI Agent 的日常运维中，开发者通常面临以下痛点：

- **临时性 Prompt 调整**：每次遇到问题就直接修改 Prompt，缺乏系统性记录
- **无法追溯的修改历史**：不知道某个改动是什么时候、为什么做出的
- **重复踩坑**：同样的错误在不同阶段反复出现
- **团队协作困难**：无法在团队成员之间共享和复用有效的修复方案

Evolver 把这些临时性的 Prompt 调整转化为可审计、可追溯、可复用的进化资产——每次变更都有 EvolutionEvent 记录，每个修复模式都可以封装成 Gene 在团队间共享。

### 4.2 Genome Evolution Protocol（GEP）

GEP 是 Evolver 的基础协议，定义了 AI Agent 进化的标准流程：

**核心原则：Evolution is not optional. Adapt or die.**

GEP 的三个基础概念：

| 概念 | 说明 |
|------|------|
| **Gene（基因）** | 可复用的进化单元，记录某种特定类型的改进模式 |
| **Capsule（胶囊）** | 封装完整的进化上下文，包含基因和对应的应用场景 |
| **EvolutionEvent（进化事件）** | 每次进化的审计记录，包含时间、原因、结果 |

### 4.3 自进化的工作流程

```
┌─────────────┐     分析      ┌──────────────┐     选择      ┌─────────────┐
│ memory/目录  │ ──────────> │ Log分析器     │ ──────────> │ Gene/Capsule│
│ (运行时日志) │              │ (扫描错误模式) │              │ 选择器       │
└─────────────┘              └──────────────┘              └─────────────┘
                                                                │
                                                                v
┌─────────────┐     记录      ┌──────────────┐     输出      ┌─────────────┐
│ Evolution   │ <────────── │ Evolution    │ <───────── │ GEP Prompt  │
│ Event日志   │             │ 事件记录器    │             │ (协议约束)   │
└─────────────┘             └──────────────┘             └─────────────┘
```

**每轮进化周期**：

1. **扫描**：`memory/`目录中的运行时日志、错误模式、信号
2. **选择**：从`assets/gep/`目录中选择最匹配的 Gene 或 Capsule
3. **生成**：输出符合 GEP 协议的 Prompt，指导下一步进化
4. **记录**：生成可审计的 EvolutionEvent

### 4.4 与传统 Prompt 工程的区别

| 特性 | 传统 Prompt 工程 | Evolver |
|------|---------------|---------|
| 变更追溯 | ❌ 难以追溯 | ✅ 完整 EvolutionEvent |
| 复用性 | ❌ 难以复用 | ✅ Gene/Capsule 可共享 |
| 协议约束 | ❌ 自由形式 | ✅ GEP 协议保证一致性 |
| 团队协作 | ❌ 各自为战 | ✅ EvoMap 网络共享 |
| 自动修复 | ⚠️ 需手动介入 | ✅ 自动分析+推荐 |

---

## §5 架构分析

### 5.1 整体架构

Evolver 的目录结构对应 §3 系统总览中的四个模块，每个模块有明确的职责划分：

```
Evolver/
├── index.js              # 主入口，支持多种运行模式
├── src/
│   ├── ops/              # Operations模块
│   │   ├── lifecycle.js  # 生命周期管理
│   │   ├── monitor.js    # 健康检查
│   │   └── cleanup.js    # 资源清理
│   ├── analysis/         # 日志分析引擎
│   │   ├── scanner.js    # 日志扫描器
│   │   └── pattern.js    # 模式识别
│   ├── selection/        # Gene/Capsule选择器
│   │   ├── gene.js       # 基因选择
│   │   └── capsule.js    # 胶囊匹配
│   └── evolution/        # 进化引擎
│       ├── emitter.js    # Prompt生成器
│       └── recorder.js   # 事件记录器
├── assets/
│   └── gep/              # GEP资产目录
│       ├── genes/        # Gene库
│       └── capsules/     # Capsule库
└── memory/               # 用户运行时日志（需手动创建）
```

### 5.2 关键模块

#### 日志分析器（Analysis）

负责扫描`memory/`目录，提取以下信息：

- **错误模式**：代码执行中的异常和失败
- **性能信号**：响应时间、资源使用情况
- **行为轨迹**：Agent 的决策路径和结果

#### Gene/Capsule 选择器（Selection）

根据日志分析结果，从资产库中选择最匹配的进化单元：

- **Gene**：单一的进化改进模式
- **Capsule**：包含完整上下文的进化方案

#### Prompt 生成器（Evolution）

生成符合 GEP 协议的 Prompt，具有以下特性：

- **协议约束**：严格遵循 GEP 规范
- **可追溯**：包含进化来源信息
- **可执行**：可直接被 Agent 理解和执行

### 5.3 安全模型

Evolver 的设计原则是"Prompt 生成器，不触碰代码"——它只输出文本指令，代码编辑和命令执行都由宿主决定：

| 能力 | 支持 | 说明 |
|------|------|------|
| 生成 Prompt | ✅ | 主要功能 |
| 自动修改代码 | ❌ | 不在设计范围内 |
| 执行 Shell 命令 | ❌ | 安全隔离 |
| 离线运行 | ✅ | 重点功能无需联网 |
| 网络协作 | ⚠️ | 可选，需配置 |

### 5.4 与 OpenClaw 的集成

当 Evolver 运行在 OpenClaw 等 Agent 运行时中时，其 `stdout` 输出可以被宿主解释执行：

```
sessions_spawn(...)
```

宿主负责把 Evolver 生成的 Prompt 转化为实际动作，Evolver 本身不执行任何命令。这种分工让进化逻辑和执行逻辑解耦——Evolver 专注于"该进化什么"，宿主专注于"怎么执行"。

---

## §6 完整进化周期走查

为了把抽象的模块串联起来，下面走查一次完整的进化周期。假设场景：你的 Agent 在生产环境中反复遇到 API 调用超时后没有重试的问题。

**第 1 步：日志写入 memory/**

Agent 运行时把错误日志写入 `memory/` 目录，日志中包含 `timeout`、`retry-failed`、`api-call-error` 等信号。

**第 2 步：Analysis 模块扫描**

`src/analysis/scanner.js` 扫描 `memory/` 目录，`pattern.js` 识别出错误模式：API 调用超时后直接失败，没有重试逻辑。输出结构化信号：`{ type: 'error', pattern: 'missing-retry', severity: 'high' }`。

**第 3 步：Selection 模块匹配**

`src/selection/gene.js` 根据信号 `missing-retry` 在 `assets/gep/genes/` 中查找匹配的 Gene。假设找到 `error-recovery-gene.js`，它的 `signals` 字段包含 `['error', 'timeout', 'retry']`，匹配成功。如果问题涉及多个信号，`capsule.js` 会匹配一个包含多个 Gene 的 Capsule。

**第 4 步：Evolution 模块生成 Prompt**

`src/evolution/emitter.js` 读取选中的 Gene，生成符合 GEP 协议的 Prompt，输出到 stdout：

```text
当检测到 API 调用超时信号时，执行以下修复策略：
1. 分析错误上下文，确认超时原因（网络、服务端、客户端）
2. 应用标准化修复流程：指数退避重试，最多 3 次
3. 记录进化事件，包含重试结果和最终状态
```

**第 5 步：EvolutionEvent 记录**

`src/evolution/recorder.js` 把这次进化记录到 `memory/evolution-events/` 目录，包含时间戳、触发信号、选中的 Gene、生成的 Prompt 摘要。

**第 6 步：宿主执行（如果集成 OpenClaw）**

如果运行在 OpenClaw 中，宿主读取 stdout 的 Prompt，通过 `sessions_spawn(...)` 触发实际的代码修改。如果是 Standalone 模式，开发者手动查看 Prompt 并决定如何应用。

**第 7 步：下一轮进化**

修复后的 Agent 重新运行，新的日志写入 `memory/`。下一轮扫描时，如果 `missing-retry` 信号消失，Evolver 会选择其他 Gene 处理剩余问题；如果信号仍在，Signal De-duplication 机制会检测到停滞并触发告警。

这个走查展示了 Evolver 的实际作用：把"发现错误→分析原因→应用修复→记录结果"这个原本依赖人工的过程，固化成可审计、可复用的协议化流程。

---

## §7 功能详解

### 7.1 四种运行模式

#### 独立运行（Standalone）

```bash
node index.js
```

- 生成 Prompt
- 打印到 stdout
- 立即退出

#### 审核模式（Review）

```bash
node index.js --review
```

- 在应用变更前暂停
- 等待人工确认
- 适合生产环境的重要变更

#### 循环模式（Loop）

```bash
node index.js --loop
```

- 后台守护进程运行
- 自适应休眠间隔
- 持续监控和改进

#### OpenClaw 集成

```bash
bash -lc 'node index.js --loop'
```

- 宿主运行时解释 stdout 指令
- 自动触发`sessions_spawn(...)`
- 无需手动介入

### 7.2 策略预设

通过`EVOLVE_STRATEGY`环境变量控制进化策略：

| 策略 | 创新 | 优化 | 修复 | 适用场景 |
|------|------|------|------|----------|
| `balanced`（默认） | 50% | 30% | 20% | 日常运营，稳定增长 |
| `innovate` | 80% | 15% | 5% | 系统稳定，快速新功能 |
| `harden` | 20% | 40% | 40% | 重大变更后，聚焦稳定性 |
| `repair-only` | 0% | 20% | 80% | 紧急状态，全力修复 |

```bash
EVOLVE_STRATEGY=innovate node index.js --loop   # 最大新功能
EVOLVE_STRATEGY=harden node index.js --loop     # 聚焦稳定性
EVOLVE_STRATEGY=repair-only node index.js --loop # 紧急修复模式
```

### 7.3 Operations 模块

生命周期管理命令：

```bash
# 启动后台运行
node src/ops/lifecycle.js start

# 优雅停止（SIGTERM -> SIGKILL）
node src/ops/lifecycle.js stop

# 查看运行状态
node src/ops/lifecycle.js status

# 健康检查 + 自动重启（如果停滞）
node src/ops/lifecycle.js check
```

### 7.4 Skill 商店

从 EvoMap 网络下载和共享可复用的技能：

```bash
# 下载技能
node index.js fetch --skill <skill_id>

# 指定输出目录
node index.js fetch --skill <skill_id> --out=./my-skills/
```

需要配置`A2A_HUB_URL`环境变量。

### 7.5 主要特性

- **Auto-Log Analysis**：扫描 memory 目录，识别错误模式和信号
- **Self-Repair Guidance**：从信号中发出修复指令
- **GEP Protocol**：标准化进化流程，支持资产复用
- **Mutation + Personality Evolution**：每次进化都有明确的 Mutation 对象和可演化的 PersonalityState
- **Signal De-duplication**：防止修复循环，检测停滞模式
- **Protected Source Files**：保护关键代码，防止被 Agent 覆盖

---

## §8 使用说明

### 8.1 安装

#### 环境要求

- **Node.js** >= 18
- **Git**（必须，用于回滚、影响范围计算和 solidify）

#### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/EvoMap/evolver.git
cd evolver

# 2. 安装依赖
npm install

# 3. 创建memory目录（存放运行时日志）
mkdir -p memory
```

#### 可选：连接 EvoMap 网络

```bash
# 在 https://evomap.ai 注册获取Node ID
# 创建.env文件
echo "A2A_HUB_URL=https://evomap.ai" > .env
echo "A2A_NODE_ID=your_node_id_here" >> .env
```

> **注意**：不配置`.env`也能完全离线运行。Hub 连接仅用于网络功能（技能共享、工作池、进化排行榜）。

### 8.2 快速开始

#### 基础使用

```bash
# 单次进化 - 扫描日志、选择Gene、输出GEP Prompt
node index.js

# 审核模式 - 应用前等待人工确认
node index.js --review

# 循环模式 - 后台守护持续进化
node index.js --loop
```

#### 创建 memory 目录

```bash
# Evolver需要memory/目录中的日志来进行分析
# 你可以手动创建并添加日志文件
mkdir -p memory

# 或者让Evolver自动创建（首次运行时会提示）
```

### 8.3 与 OpenClaw 集成

对于 OpenClaw 用户，推荐使用 cron 定时触发：

```bash
# 在crontab中添加
0 */6 * * * bash -lc 'cd /path/to/evolver && node index.js --loop'
```

对于 PM2 进程管理器：

```bash
pm2 start "bash -lc 'node index.js --loop'" --name evolver --cron-restart="0 */6 * * *"
```

### 8.4 生产环境部署

#### Docker 部署示例

```dockerfile
FROM node:18-slim

WORKDIR /app
RUN apt-get update && apt-get install -y git

COPY package*.json ./
RUN npm ci --only=production

COPY . .

RUN mkdir -p memory

CMD ["node", "index.js", "--loop"]
```

#### 健康检查配置

```bash
# 使用lifecycle.js进行健康检查
node src/ops/lifecycle.js check
```

### 8.5 常见问题

#### Q: 为什么需要 Git？

Git 用于：
- 回滚（Rollback）：在进化失败时恢复到之前状态
- 影响范围计算（Blast Radius）：评估变更的影响范围
- Solidify：将进化结果固化为可复用的资产

**在没有 Git 的目录中运行会失败**。

#### Q: Evolver 会自动修改我的代码吗？

**不会**。Evolver 是一个**Prompt 生成器**，不是代码修补器。它：
- ✅ 生成 GEP Prompt 指导进化
- ❌ 不会自动编辑源代码
- ❌ 不会执行任意 Shell 命令

#### Q: 如何在团队中共享进化资产？

1. 在[EvoMap平台](https://evomap.ai)上注册
2. 配置`A2A_HUB_URL`和`A2A_NODE_ID`
3. 使用`node index.js fetch --skill <id>`下载共享技能
4. 使用`node index.js push --skill`分享你的基因和胶囊

---

## §9 开发扩展

### 9.1 创建自定义 Gene

Gene 是 Gene Expression Programming 中的基本单元，代表一种可复用的进化模式。

```
assets/gep/genes/
├── error-recovery-gene.js
├── performance-optimization-gene.js
└── security-hardening-gene.js
```

Gene 结构示例（完整可运行的 CommonJS 模块）：

```javascript
// assets/gep/genes/example-gene.js
module.exports = {
  name: 'example-gene',
  description: '处理特定错误模式的基因',
  version: '1.0.0',
  
  // 信号匹配规则
  signals: ['error', 'timeout', 'retry'],
  
  // 基因内容
  prompt: `
    当检测到{signal}时，执行以下修复策略：
    1. 分析错误上下文
    2. 应用标准化修复流程
    3. 记录进化事件
  `,
  
  // 元数据
  metadata: {
    author: 'your-name',
    tags: ['error-handling', 'recovery'],
    successRate: 0.85
  }
};
```

### 9.2 创建自定义 Capsule

Capsule 是封装的进化上下文，包含 Gene 和对应的应用场景。

```
assets/gep/capsules/
├── critical-fix-capsule.js
└── performance-boost-capsule.js
```

Capsule 结构示例（完整可运行的 CommonJS 模块）：

```javascript
// assets/gep/capsules/example-capsule.js
module.exports = {
  name: 'example-capsule',
  description: '处理高优先级错误的胶囊',
  version: '1.0.0',
  
  // 胶囊包含的基因
  genes: ['error-recovery-gene', 'retry-gene'],
  
  // 触发条件
  trigger: {
    signals: ['critical-error'],
    priority: 'high',
    context: ['production', 'api']
  },
  
  // 胶囊内容
  prompt: `
    这是一个高优先级修复胶囊...
  `,
  
  // 验证规则
  validation: {
    mustPass: ['test-suite', 'lint-check'],
    maxDuration: '5m'
  }
};
```

### 9.3 扩展日志分析器

在 `src/analysis/` 中添加自定义分析器。下面是结构示例，`readLogs` 和 `analyzePatterns` 需要根据你的日志格式自行实现：

```javascript
// src/analysis/custom-scanner.js
const fs = require('fs');
const path = require('path');

module.exports = {
  name: 'custom-scanner',
  
  scan(memoryDir) {
    // 自定义扫描逻辑
    const logs = readLogs(memoryDir);
    return analyzePatterns(logs);
  },
  
  // 支持的分析类型
  supportedTypes: ['error', 'performance', 'security']
};

// 读取 memory 目录下的日志文件
function readLogs(memoryDir) {
  const files = fs.readdirSync(memoryDir).filter(f => f.endsWith('.json'));
  return files.map(f => JSON.parse(fs.readFileSync(path.join(memoryDir, f), 'utf-8')));
}

// 识别日志中的错误模式
function analyzePatterns(logs) {
  return logs.flatMap(log => log.errors || []);
}
```

### 9.4 集成外部数据源

下面是节选示例，`fetchExternalLogs` 需要根据你的数据源 SDK 自行实现，`nativeAnalysis` 来自 Evolver 内置分析器的输出：

```javascript
// 自定义数据源集成（节选）
const externalLogs = await fetchExternalLogs({
  source: 'datadog',
  apiKey: process.env.DD_API_KEY,
  query: 'error @severity:critical'
});

// 合并到Evolver分析
const combinedAnalysis = {
  ...nativeAnalysis,
  ...externalLogs
};
```

### 9.5 Webhook 扩展

下面是节选示例，`updateMonitoring` 需要根据你的监控系统 API 自行实现：

```javascript
// src/extensions/webhook.js（节选）
module.exports = {
  async onEvolutionComplete(event) {
    // 发送通知
    await fetch(process.env.WEBHOOK_URL, {
      method: 'POST',
      body: JSON.stringify(event)
    });
    
    // 更新外部监控系统
    await updateMonitoring(event);
  }
};
```

---

## §10 实践建议

### 10.1 日常运营

#### 推荐的日常使用方式

```bash
# 每天早上运行一次
0 9 * * * bash -lc 'cd /path/to/evolver && node index.js'

# 生产环境使用审核模式
0 9 * * * bash -lc 'cd /path/to/evolver && node index.js --review'
```

#### 监控关键指标

- **进化频率**：每天进化的次数
- **成功率**：Gene/Capsule 匹配成功率
- **停滞检测**：连续多次无改进时触发告警

### 10.2 生产环境

#### 故障恢复

```bash
# 检查健康状态
node src/ops/lifecycle.js status

# 如果发现问题，重启
node src/ops/lifecycle.js stop
node src/ops/lifecycle.js start
```

#### 日志管理

```bash
# 定期清理旧日志（建议每周）
node src/ops/cleanup.js --older-than 7d

# 归档重要进化事件
node src/ops/cleanup.js --archive --keep-last 100
```

### 10.3 团队协作

1. **统一 Gene 库**：在团队内部共享常用基因
2. **Capsule 审核**：重要 Capsule 经过评审后再使用
3. **EvolutionEvent 共享**：在团队内部分享进化记录
4. **使用 EvoMap 网络**：通过平台进行技能共享

### 10.4 安全建议

- ✅ 使用审核模式处理敏感环境
- ✅ 定期审计 EvolutionEvent 日志
- ✅ 保护`assets/gep/`目录的访问权限
- ❌ 不要在 Prompt 中包含敏感信息
- ❌ 不要在生产环境使用未审核的 Capsule

---

## §11 FAQ

### Q1: Evolver 和传统的 Prompt 工程工具有什么区别？

Evolver 是系统性的自进化框架，传统 Prompt 工程是手动调参工具。两者的关键差异在变更是否可追溯、修复模式是否可复用：

- **传统 Prompt 工程**：手动调整、临时生效、难以追溯
- **Evolver**：自动分析、协议约束、完整审计

### Q2: 需要多少日志才能让 Evolver 工作？

建议至少有以下日志：
- 最近 7 天的运行时日志
- 错误和异常记录
- 性能指标数据

日志越多，Evolver 的分析越准确。

### Q3: Evolver 支持哪些编程语言的 Agent？

Evolver 是**语言无关的**。它专注于 Prompt 和进化协议，不依赖特定编程语言。

### Q4: 如何评估进化效果？

通过**EvolutionEvent**中的记录来评估：
- 修复前后的错误率对比
- 性能指标的变化趋势
- 自动化率的提升

### Q5: 可以离线使用 Evolver 吗？

**完全可以**。关键功能（分析、生成、记录）完全离线运行。只有网络功能（技能共享、排行榜）需要联网。

### Q6: 如何回滚到之前的版本？

```bash
# 查看进化历史
git log --oneline

# 查看特定进化事件
cat memory/evolution-events/YYYY-MM-DD.json

# 如果需要，手动恢复
git checkout <previous-commit>
```

### Q7: Evolver 的 Gene/Capsule 和 OpenAI 的 Plugin 有什么不同？

| 特性 | Gene/Capsule | OpenAI Plugin |
|------|-------------|---------------|
| 用途 | Agent 自进化 | 扩展功能 |
| 粒度 | Prompt 级别 | API 级别 |
| 复用方式 | GEP 协议共享 | Plugin 商店 |
| 自主性 | 自动化进化 | 手动调用 |

### Q8: 遇到问题时如何获取帮助？

1. 查看[EvoMap Wiki](https://evomap.ai/wiki)
2. 提交[GitHub Issue](https://github.com/EvoMap/evolver/issues)
3. 加入[EvoMap Discord](https://discord.gg/evomap)

---

## §12 采用顺序与决策建议

### 适合先用的团队

- **已有 OpenClaw 等 Agent 运行时的团队**：Evolver 的 stdout 输出可以直接被宿主解释执行，集成成本最低，收益最直接。
- **Agent 已上线且有稳定日志输出的团队**：`memory/` 目录有内容可分析，Evolver 才能发挥作用。如果 Agent 还在开发阶段、没有运行时日志，先不要引入。
- **多人协作维护同一套 Agent Prompt 的团队**：Gene/Capsule 的共享机制能解决"修复方案散落在各人本地"的问题。

### 暂时不必引入的场景

- **Agent 还在原型验证阶段**：此时 Prompt 变动频繁且不需要审计，引入 Evolver 会增加流程开销。
- **单人维护、Prompt 数量很少的项目**：手动维护 Git 历史已经够用，GEP 协议的收益不明显。
- **没有 Git 仓库的环境**：Evolver 依赖 Git 做回滚、影响范围计算和 solidify，没有 Git 会直接失败。

### 推荐的采用顺序

1. **先跑 Standalone 模式**：`node index.js` 单次运行，观察生成的 Prompt 质量是否符合预期。这一步不接入宿主，零风险。
2. **积累 Gene 库**：把团队里反复出现的修复模式写成 Gene，放到 `assets/gep/genes/`。先有资产，再谈自动化。
3. **切换到 Review 模式**：`node index.js --review` 在应用变更前等待人工确认，适合生产环境逐步建立信任。
4. **接入 OpenClaw 跑 Loop 模式**：确认 Gene 库覆盖主要错误模式后，再让宿主自动执行 Prompt，实现端到端的自进化。
5. **连接 EvoMap 网络**：最后才考虑网络功能（技能共享、排行榜）。离线功能已经覆盖核心场景，网络是锦上添花。

### 进阶路径

- 想深入定制进化逻辑：阅读 §9 开发扩展，从自定义 Gene 开始，逐步扩展到自定义分析器和 Webhook。
- 想做团队级进化资产管理：把 `assets/gep/` 纳入 Git 仓库管理，配合 EvoMap 网络做跨团队共享。
- 想评估进化效果：定期检查 `memory/evolution-events/` 目录，对比修复前后的错误率和性能指标。

---

## 附录：快速命令参考

```bash
# 安装
git clone https://github.com/EvoMap/evolver.git
cd evolver
npm install

# 运行模式
node index.js                              # 单次运行
node index.js --review                      # 审核模式
node index.js --loop                        # 循环模式

# 生命周期管理
node src/ops/lifecycle.js start             # 启动
node src/ops/lifecycle.js stop              # 停止
node src/ops/lifecycle.js status            # 状态
node src/ops/lifecycle.js check             # 健康检查

# 技能管理
node index.js fetch --skill <id>            # 下载技能

# 策略控制
EVOLVE_STRATEGY=balanced node index.js      # 平衡模式
EVOLVE_STRATEGY=innovate node index.js      # 创新模式
EVOLVE_STRATEGY=harden node index.js        # 稳定模式
EVOLVE_STRATEGY=repair-only node index.js   # 修复模式
```

---

**项目信息**：

- **仓库**：[EvoMap/evolver](https://github.com/EvoMap/evolver)
- **官网**：[evomap.ai](https://evomap.ai)
- **文档**：[evomap.ai/wiki](https://evomap.ai/wiki)
- **语言**：JavaScript (Node.js >= 18)
- **许可**：MIT
- **Stars**：3,862
- **Forks**：392

🦞 每日 08:00 自动更新
