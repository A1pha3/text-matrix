---
title: "Evolver：GEP基因组进化协议——让AI Agent实现自进化、自修复、自优化"
date: "2026-04-17T16:40:00+08:00"
slug: "evolver-gep-self-evolution-engine"
description: "3,862 Stars的Evolver是GEP（基因组进化协议）驱动的AI Agent自进化引擎。通过Gene/Capsule/Event结构化资产和Strategy Presets实现可审计的进化，支持修复/优化/创新三种模式，可选接入EvoMap网络共享技能。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "Agent", "自进化", "GEP", "JavaScript", "Node.js", "协议", "自我修复"]
---

# Evolver：GEP基因组进化协议——让AI Agent实现自进化

> **目标读者**：AI Agent开发者、Prompt工程师、对AI自我进化感兴趣的研究者
> **前置知识**：JavaScript/Node.js基础、对AI Agent概念有了解
> **技术栈**：Node.js 18+ / GEP Protocol / A2A Hub
> **难度定位**：⭐⭐⭐⭐ 专家设计

---

## §1 学习目标

完成本篇文章后，你将能够：

1. **理解GEP基因组进化协议**：为何需要结构化的进化资产
2. **掌握Evolver的核心架构**：Gene/Capsule/Event三元素体系
3. **理解四大Strategy Presets**：balanced/innovate/harden/repair-only
4. **掌握Evolver的部署方式**：独立运行/接入OpenClaw/接入EvoMap Hub
5. **能够构建自进化Agent**：使用Evolver实现Agent的自我修复与优化
6. **理解安全模型**：Evolver的验证命令白名单机制

---

## §2 背景与动机：为何AI需要自进化

### 2.1 当前AI Agent的困境

| 问题 | 描述 | 影响 |
|------|------|------|
| **Prompt漂移** | 多次迭代后Prompt质量下降 | Agent行为不稳定 |
| **错误重复** | 同样的错误反复发生 | 效率低下 |
| **缺乏记忆** | 无法从历史失败中学习 | 经验无法积累 |
| **人工维护** | 依赖人工调整Prompt | 成本高、响应慢 |

### 2.2 传统进化的局限

**无结构进化的痛点**：

```python
# 传统的"进化"方式：手动修改Prompt
# 问题：不可追溯、难以复用、风险高
prompt = "You are a helpful assistant."  # 改成这样？
prompt = "You are a helpful AI assistant."  # 还是这样？
prompt = "You are a knowledgeable AI assistant."  # 到底哪个好？
```

### 2.3 GEP的解决思路

**基因组进化协议（Genome Evolution Protocol）**：

```
传统进化：无结构的Prompt修改 → 不可追溯
GEP进化：结构化资产 + 协议约束 → 可审计、可复用、可追溯
```

**核心洞察**：
- 将进化经验封装为 **Gene**（可复用的进化基因）
- 将多步进化封装为 **Capsule**（可组合的进化胶囊）
- 所有变更记录为 **Event**（完整的审计日志）

---

## §3 核心概念：GEP三元素体系

### 3.1 Gene（进化基因）

Gene是最小的可复用进化单元：

```javascript
// assets/gep/genes.json 中的Gene结构
{
  "id": "gene-001",
  "name": "Error-Retry-Pattern",
  "description": "检测到错误时自动重试的基因",
  "signals": ["error", "retry", "failed"],
  "mutation": {
    "type": "prompt_modification",
    "template": "When you encounter an error, wait 1 second then retry up to 3 times before giving up."
  },
  "validation": ["node test/error-retry.test.js"],
  "version": "1.2.0"
}
```

**Gene的核心属性**：

| 属性 | 说明 |
|------|------|
| `id` | 唯一标识符 |
| `signals` | 触发信号（错误模式关键词） |
| `mutation` | 变异内容（Prompt修改/代码变更） |
| `validation` | 验证命令（确保变异有效） |
| `version` | 版本号（追踪演化历史） |

### 3.2 Capsule（进化胶囊）

Capsule是多步进化的组合单元：

```javascript
// assets/gep/capsules.json 中的Capsule结构
{
  "id": "capsule-001",
  "name": "Production-Hardening",
  "description": "生产环境加固套件",
  "genes": ["gene-001", "gene-015", "gene-023"],
  "order": ["gene-015", "gene-001", "gene-023"],
  "conditions": {
    "minFailureStreak": 3,
    "environment": "production"
  }
}
```

**Capsule vs Gene**：

| 维度 | Gene | Capsule |
|------|------|---------|
| **复杂度** | 单个变异 | 多个Gene组合 |
| **复用粒度** | 细粒度 | 粗粒度 |
| **适用场景** | 单点问题修复 | 系统性改进 |

### 3.3 EvolutionEvent（进化事件）

每一次进化变更都被记录为Event：

```json
// assets/gep/events.jsonl 中的Event格式
{"timestamp":"2026-04-17T08:00:00Z","type":"gene_applied","geneId":"gene-001","signal":"error_retry","status":"success","duration_ms":234}
{"timestamp":"2026-04-17T08:05:00Z","type":"capsule_applied","capsuleId":"capsule-001","status":"partial","genesApplied":2,"genesSkipped":1}
```

**Event的审计价值**：
- 追踪每次变更的原因和结果
- 分析失败模式
- 评估进化策略有效性
- 合规审计支持

---

## §4 Evolver工作原理

### 4.1 整体流程

```
┌──────────────────────────────────────────────────────────────┐
│                    Evolver Evolution Cycle                    │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  memory/ 目录                                                 │
│  (运行时日志)                                                  │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────────┐                                          │
│  │  Signal Extract │ ← 分析日志中的错误模式                   │
│  └────────┬────────┘                                          │
│           │ signals                                           │
│           ▼                                                   │
│  ┌─────────────────┐                                          │
│  │  Gene Selector  │ ← 根据signals匹配最佳Gene/Capsule        │
│  └────────┬────────┘                                          │
│           │ selector decision                                  │
│           ▼                                                   │
│  ┌─────────────────┐                                          │
│  │  GEP Prompt    │ ← 生成协议约束的进化Prompt               │
│  │  Generator     │                                          │
│  └────────┬────────┘                                          │
│           │ GEP Prompt                                         │
│           ▼                                                   │
│  ┌─────────────────┐                                          │
│  │  Solidify      │ ← 验证变更（执行validation命令）          │
│  └────────┬────────┘                                          │
│           │ EvolutionEvent                                     │
│           ▼                                                   │
│  assets/gep/events.jsonl                                       │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 Signal提取

```javascript
// src/gep/signalExtractor.js 核心逻辑
async function extractSignals(memoryDir) {
  const logs = await readLogs(memoryDir);
  const errorPatterns = [];
  
  for (const log of logs) {
    // 检测错误模式
    if (log.includes('Error:') || log.includes('Failed:')) {
      errorPatterns.push({
        type: 'error',
        message: extractErrorMessage(log),
        stack: extractStackTrace(log),
        timestamp: log.timestamp
      });
    }
    
    // 检测重试模式（可能的修复循环）
    if (log.includes('retry') && log.includes('retry')) {
      errorPatterns.push({
        type: 'retry_loop',
        message: 'Potential retry loop detected',
        timestamp: log.timestamp
      });
    }
  }
  
  // 去重和优先级排序
  return deduplicateAndPrioritize(errorPatterns);
}
```

### 4.3 Gene Selection算法

```javascript
// src/gep/selector.js
async function selectGene(signals, genes) {
  const scores = [];
  
  for (const gene of genes) {
    let score = 0;
    
    for (const signal of signals) {
      // 1. 信号匹配度
      for (const geneSignal of gene.signals) {
        if (signal.type.includes(geneSignal) || signal.message.includes(geneSignal)) {
          score += 10;
        }
      }
      
      // 2. 历史成功率（从Event中计算）
      const successRate = await getGeneSuccessRate(gene.id);
      score *= successRate;
      
      // 3. 避免重复应用（去重）
      const recentEvents = await getRecentEvents(gene.id, hours=24);
      if (recentEvents.length > 0) {
        score *= 0.5;  // 降低近期已应用Gene的分数
      }
    }
    
    scores.push({ gene, score });
  }
  
  // 返回得分最高的Gene
  return scores.sort((a, b) => b.score - a.score)[0].gene;
}
```

### 4.4 Solidify验证

```javascript
// src/gep/solidify.js
async function solidify(gene) {
  // 1. 应用Mutation
  await applyMutation(gene.mutation);
  
  // 2. 执行验证命令
  for (const validationCmd of gene.validation) {
    // 安全检查
    if (!isValidationCommandAllowed(validationCmd)) {
      throw new Error(`Unsafe validation command: ${validationCmd}`);
    }
    
    // 执行（180秒超时）
    const result = await execCommand(validationCmd, { timeout: 180000 });
    
    if (result.exitCode !== 0) {
      // 验证失败，回滚
      await rollback();
      return { status: 'failed', error: result.stderr };
    }
  }
  
  // 3. 记录Event
  await recordEvent({
    type: 'gene_applied',
    geneId: gene.id,
    status: 'success',
    timestamp: new Date().toISOString()
  });
  
  return { status: 'success' };
}
```

---

## §5 Strategy Presets：进化策略配置

### 5.1 四大策略

```bash
# 平衡模式（默认）
EVOLVE_STRATEGY=balanced node index.js --loop

# 创新模式 - 最大化新功能
EVOLVE_STRATEGY=innovate node index.js --loop

# 加固模式 - 聚焦稳定性
EVOLVE_STRATEGY=harden node index.js --loop

# 仅修复模式 - 紧急修复
EVOLVE_STRATEGY=repair-only node index.js --loop
```

### 5.2 策略对比

| 策略 | 创新 | 优化 | 修复 | 适用场景 |
|------|------|------|------|----------|
| `balanced` | 50% | 30% | 20% | 日常运行，稳定增长 |
| `innovate` | 80% | 15% | 5% | 系统稳定，快速发布 |
| `harden` | 20% | 40% | 40% | 重大变更后，聚焦稳定性 |
| `repair-only` | 0% | 20% | 80% | 紧急状态，全力修复 |

### 5.3 策略动态调整

```javascript
// src/strategy/adaptiveStrategy.js
async function getAdaptiveStrategy() {
  const recentEvents = await getRecentEvents(hours=24);
  const failureRate = calculateFailureRate(recentEvents);
  
  if (failureRate > 0.5) {
    return 'repair-only';  // 失败率 > 50% 切换到修复模式
  } else if (failureRate > 0.3) {
    return 'harden';       // 失败率 > 30% 切换到加固模式
  }
  
  return 'balanced';       // 正常使用平衡模式
}
```

---

## §6 部署模式

### 6.1 独立运行

```bash
# 单次运行
node index.js

# 审核模式（应用前等待人工确认）
node index.js --review

# 持续循环
node index.js --loop
```

### 6.2 接入OpenClaw

当Evolver运行在OpenClaw中时，`sessions_spawn(...)`输出会被OpenClaw解释执行：

```bash
# 在OpenClaw workspace中克隆
git clone https://github.com/EvoMap/evolver.git
cd evolver && npm install

# OpenClaw会自动解释stdout中的sessions_spawn指令
node index.js --loop
```

### 6.3 生命周期管理

```bash
# 启动（后台运行）
node src/ops/lifecycle.js start

# 停止（优雅关闭）
node src/ops/lifecycle.js stop

# 查看状态
node src/ops/lifecycle.js status

# 健康检查（自动重启）
node src/ops/lifecycle.js check
```

### 6.4 Cron定时任务

```bash
# 推荐方式
bash -lc 'node index.js --loop'

# 配合pm2
pm2 start "bash -lc 'node index.js --loop'" \
  --name evolver \
  --cron-restart="0 */6 * * *"
```

---

## §7 EvoMap Hub：网络协作

### 7.1 Hub连接配置

```bash
# 创建.env文件
echo "A2A_HUB_URL=https://evomap.ai" >> .env
echo "A2A_NODE_ID=your_node_id_here" >> .env

# 或注册后从evomap.ai获取Node ID
```

### 7.2 Hub功能

| 功能 | 说明 |
|------|------|
| **心跳** | 每6分钟向Hub报告状态 |
| **技能商店** | 下载/发布可复用技能 |
| **Worker Pool** | 接受网络任务 |
| **Evolution Circle** | 协作进化小组 |

### 7.3 Worker Pool模式

```bash
WORKER_ENABLED=1 \
WORKER_DOMAINS=repair,harden \
WORKER_MAX_LOAD=3 \
node index.js --loop
```

**前提条件**：
1. 本地设置 `WORKER_ENABLED=1`
2. 在 evomap.ai 网站上打开 Worker 开关
3. 两者都要开启才能接收任务

---

## §8 安全模型

### 8.1 命令白名单

`solidify.js`执行验证命令时有严格的**白名单限制**：

```javascript
// 安全检查规则
function isValidationCommandAllowed(cmd) {
  // 1. 前缀白名单：只允许node/npm/npx
  if (!cmd.match(/^(node|npm|npx)\s/)) {
    return false;
  }
  
  // 2. 禁止命令替换
  if (cmd.match(/`|\$\(/)) {
    return false;
  }
  
  // 3. 禁止shell操作符
  const unsafeOperators = /;|&&|\|\||>|</;
  const strippedCmd = cmd.replace(/"[^"]*"|'[^']*'/g, '');  // 去除引号内容
  if (strippedCmd.match(unsafeOperators)) {
    return false;
  }
  
  return true;
}
```

### 8.2 验证命令安全矩阵

| 命令 | 是否允许 | 原因 |
|------|----------|------|
| `node test.js` | ✅ | 白名单前缀 |
| `npm test` | ✅ | 白名单前缀 |
| `npx jest` | ✅ | 白名单前缀 |
| `bash script.sh` | ❌ | 非白名单前缀 |
| `rm -rf .` | ❌ | 非白名单前缀 |
| `node -e "..."` | ❌ | 禁止-e参数 |

### 8.3 A2A资产摄入安全

外部Gene/Capsule通过`scripts/a2a_ingest.js`摄入时：
- 先存入隔离的候选区（candidate zone）
- 提升到本地存储需要`--validated`标志
- Gene的验证命令会经过同样的安全检查

---

## §9 与OpenClaw集成

### 9.1 OpenClaw集成架构

```
OpenClaw Workspace
       │
       ├── memory/  ← Agent运行时日志
       │
       ├── evolver/ ← Evolver核心
       │
       └── skills/  ← 可选技能（如feishu-card）
       
       连接方式：
       1. Evolver扫描memory/目录
       2. 生成GEP Prompt
       3. 输出sessions_spawn(...)指令
       4. OpenClaw解释执行
```

### 9.2 本地覆盖机制

```bash
# 方式1：环境变量
EVOLVE_REPORT_TOOL=feishu-card node index.js --loop

# 方式2：自动检测
# Evolver自动检测skills/feishu-card是否存在
# 存在则自动升级报告行为
```

---

## §10 完整使用示例

### 10.1 场景：修复Agent的重复错误

**问题**：Agent反复在JSON解析时失败

**解决流程**：

```bash
# 1. 查看memory/中的日志
cat memory/error.log
# [2026-04-17 08:00] Error: JSON parse error at position 234
# [2026-04-17 08:05] Error: JSON parse error at position 567
# [2026-04-17 08:10] Error: JSON parse error at position 890

# 2. 运行Evolver
node index.js --review

# 输出：
# Signal detected: JSON parse error
# Gene selected: gene-042 (JSON-Validation-Enhancement)
# GEP Prompt generated...
# 
# Applying mutation? [y/N]: y
# 
# Running validation: node test/json-validation.test.js
# Test passed!
# 
# EvolutionEvent recorded: gene-042 applied successfully

# 3. 验证修复
# 下次运行时不再出现JSON解析错误
```

### 10.2 场景：系统加固

```bash
# 使用加固策略
EVOLVE_STRATEGY=harden node index.js --loop

# Evolver会优先选择：
# - 基因验证增强Gene
# - 边界检查Gene
# - 错误处理Gene
```

### 10.3 场景：紧急修复

```bash
# 紧急修复模式
EVOLVE_STRATEGY=repair-only node index.js --loop

# Evolver只关注：
# - 高频错误Gene
# - 快速修复Gene
# - 最小变更Gene
```

---

## §11 FAQ

**Q1：Evolver会自动修改我的代码吗？**
A：不会。Evolver只生成协议约束的Prompt和资产，不直接修改源代码。验证通过后才由宿主环境决定是否应用。

**Q2：需要连接EvoMap Hub吗？**
A：不需要。核心进化功能完全离线可用。Hub连接只是用于技能商店和Worker Pool网络功能。

**Q3：Evolver安全吗？**
A：安全。验证命令有严格的白名单限制（仅node/npm/npx），禁止命令替换和shell操作符。

**Q4：可以自定义Gene吗？**
A：可以。在`assets/gep/genes.json`中添加你自己的Gene即可。

**Q5：支持哪些编程语言的Agent？**
A：Evolver是语言无关的。它通过扫描日志生成Prompt，不依赖特定编程语言。

---

## 相关资源

- **GitHub仓库**：https://github.com/EvoMap/evolver
- **官网**：https://evomap.ai
- **文档**：https://evomap.ai/wiki
- **中文文档**：README.zh-CN.md
