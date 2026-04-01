---
title: "Token Tracker 入门到精通：纯本地 AI 编程工具 Token 用量追踪实战"
date: 2026-03-28T13:38:00+08:00
slug: "token-tracker-guide-openclaw-usage"
aliases:
  - /posts/tech/token-tracker-guide-openclaw-usage/
description: "全面介绍 Token Tracker 的技术原理、安装配置、使用方法及进阶开发，涵盖 JSONL 格式解析、多工具支持、费用优化等核心主题。"
draft: false
categories: ["技术笔记"]
tags: ["Token", "AI编程", "OpenClaw", "VibeUsage", "用量追踪"]
---

# Token Tracker 入门到精通：纯本地 AI 编程工具 Token 用量追踪实战

## 学习目标

通过本文档，你将掌握以下技能：

- 理解什么是 Token 以及为什么需要追踪 Token 用量
- 深入理解 VibeUsage 和自建 Token Tracker 的技术原理
- 独立安装、配置和使用 Token Tracker 工具
- 学会阅读和解析 JSONL 格式的 Session 日志文件
- 掌握按时间、按模型、按项目的多维度用量分析方法
- 了解如何扩展 Token Tracker 支持新的 AI 编程工具
- 学会优化 Token 用量以降低成本

---

## 一、背景与原理

### 1.1 什么是 Token？

Token（词元）是 AI 大语言模型处理文本的最小单位。在自然语言处理中，文本首先被分解成 Token，然后模型基于这些 Token 进行推理和生成。

**为什么 Token 如此重要？**

- **计费依据**：大多数 AI API 服务（如 OpenAI、Anthropic、Google）按照输入和输出的 Token 数量收费
- **性能指标**：Token 数量直接影响推理速度和响应时间
- **资源限制**：每种模型都有上下文窗口限制（Context Window），即单次最大可处理的 Token 数量

**举例说明**：假设你有一段 1000 字的中文文本，大约包含 1500-2000 个 Token（中文每字约 1.5-2 个 Token，英文每个单词约 1-1.5 个 Token）。

### 1.2 为什么需要追踪 Token 用量？

在日常使用 AI 编程工具时，我们往往专注于完成任务，而忽视了资源消耗。然而，追踪 Token 用量有以下几个重要价值：

**成本控制**

了解每个项目、每天、每月的 Token 消耗，可以帮助你：
- 预测月度 AI 支出
- 识别异常消耗模式
- 优化提示词（Prompt）以减少不必要的 Token 使用

**性能优化**

通过分析 Token 用量数据，你可以：
- 发现哪些任务消耗 Token 过多
- 评估不同模型的经济性
- 选择性价比最高的模型

**团队协作**

对于团队而言：
- 合理分配 AI 资源配额
- 避免单用户过度消耗
- 建立透明的资源使用机制

### 1.3 VibeUsage vs 自建 Token Tracker

市面上有多种 Token 追踪方案，我们来对比分析：

| 方案 | 云端依赖 | API Key | 隐私性 | 定制化 | 适用场景 |
|------|----------|---------|--------|--------|----------|
| VibeUsage | 必须 | 必须 | 中 | 低 | 需要云端仪表板 |
| 自建 Token Tracker | 无 | 无 | 高 | 高 | 本地优先，注重隐私 |

**VibeUsage 特点**

- 数据上传到 vibecafe.ai 云端
- 提供 Web 仪表板可视化
- 支持 12+ 种 AI 编程工具
- 需要注册账号和 API Key

**自建 Token Tracker 特点**

- 100% 本地运行
- 不上传任何数据
- 完全可定制
- 无需网络连接

**本文重点**：教你如何构建自己的纯本地 Token Tracker，既保护隐私又满足定制需求。

---

## 二、技术原理深度解析

### 2.1 AI 编程工具的数据存储机制

现代 AI 编程工具（如 OpenClaw、Claude Code、Codex 等）在本地保存会话记录时，通常采用 **JSONL（JSON Lines）** 格式。

**JSONL 格式特点**

- 每行是一个独立的完整 JSON 对象
- 换行符（\n）是行分隔符
- 易于流式读写
- 比标准 JSON 数组更节省内存

**为什么选择 JSONL？**

1. **流式写入**：AI 对话是持续的，数据实时追加到文件
2. **内存友好**：不需要将整个文件加载到内存
3. **断裂容忍**：部分损坏不影响其他行

### 2.2 OpenClaw Session 文件结构

OpenClaw 将会话数据存储在以下目录结构中：

```
~/.openclaw/
└── agents/
    └── <agentId>/
        ├── agent/           # Agent 配置目录
        └── sessions/        # 会话记录目录
            ├── <session1>.jsonl
            ├── <session2>.jsonl
            └── <session3>.jsonl
```

**Session 文件示例**

```jsonl
{"type":"session","version":3,"id":"10115670-855c-4603-947c-b250d43b173e","timestamp":"2026-03-06T11:30:00.220Z","cwd":"/Users/damon/.openclaw/workspace"}
{"type":"model_change","id":"1733f7b5","parentId":null,"timestamp":"2026-03-06T11:30:00.223Z","provider":"minimax-cn","modelId":"MiniMax-M2.5"}
{"type":"thinking_level_change","id":"ed264ff0","parentId":"1733f7b5","timestamp":"2026-03-06T11:30:00.223Z","thinkingLevel":"low"}
{"type":"message","id":"21d29a13","parentId":"620de98e","timestamp":"2026-03-06T11:30:00.231Z","message":{"role":"user","content":[{"type":"text","text":"Hello, world!"}],"timestamp":1772796600228}}
{"type":"message","id":"664db70e","parentId":"21d29a13","timestamp":"2026-03-06T11:30:05.754Z","message":{"role":"assistant","content":[{"type":"thinking","thinking":"This is a response..."}],"api":"anthropic-messages","provider":"minimax-cn","model":"MiniMax-M2.5","usage":{"input":36,"output":82,"cacheRead":0,"cacheWrite":16646,"totalTokens":16764,"cost":{"input":0.0000108,"output":0.0000984,"cacheRead":0,"cacheWrite":0.0019975,"total":0.0021067}},"stopReason":"toolUse","timestamp":1772796600230}}
```

**事件类型说明**

| type 值 | 说明 | 包含 usage |
|---------|------|-----------|
| `session` | 会话开始事件 | 否 |
| `model_change` | 模型切换事件 | 否 |
| `thinking_level_change` | 思考级别变更 | 否 |
| `message` | 消息事件 | 是 |

### 2.3 Message 事件结构详解

在 Message 事件中，`message` 字段包含了完整的消息内容和 Token 用量：

```javascript
{
  "type": "message",
  "id": "664db70e",                    // 消息唯一 ID
  "parentId": "21d29a13",              // 父消息 ID（用于构建对话树）
  "timestamp": "2026-03-06T11:30:05.754Z",  // 时间戳
  
  "message": {
    "role": "assistant",                // 角色：user | assistant
    "content": [                       // 消息内容（多模态）
      {
        "type": "thinking",            // 思考内容
        "thinking": "..."
      },
      {
        "type": "toolCall",           // 工具调用
        "id": "call_xxx",
        "name": "web_search",
        "arguments": {"query": "search term", "count": 10}
      }
    ],
    "api": "anthropic-messages",       // API 类型
    "provider": "minimax-cn",         // 提供商
    "model": "MiniMax-M2.5",          // 模型名称
    "usage": {                         // Token 用量 ⭐ 核心
      "input": 36,                    // 输入 Token 数
      "output": 82,                   // 输出 Token 数
      "cacheRead": 0,                 // 缓存读取 Token
      "cacheWrite": 16646,            // 缓存写入 Token
      "totalTokens": 16764,           // 总 Token 数
      "cost": {                       // 费用详情（单位：美元）
        "input": 0.0000108,
        "output": 0.0000984,
        "cacheRead": 0,
        "cacheWrite": 0.0019975,
        "total": 0.0021067
      }
    },
    "stopReason": "toolUse",          // 停止原因
    "timestamp": 1772796600230        // 消息级时间戳（毫秒）
  }
}
```

### 2.4 Token 字段的兼容性处理

不同的 AI 编程工具和模型提供商会使用不同的字段名来表示 Token 数量。Token Tracker 必须处理这种命名差异：

```javascript
// 兼容多种字段名的 Token 提取函数
function getTokenValue(usage, ...keys) {
  for (const key of keys) {
    if (usage[key] != null && usage[key] > 0) {
      return usage[key];
    }
  }
  return 0;
}

// 使用示例
const inputTokens = getTokenValue(usage, 
  'input',           // OpenClaw 标准
  'inputTokens',     // OpenAI 格式
  'promptTokens',    // Anthropic 格式
  'prompt_tokens'    // 小写下划线格式
);

const outputTokens = getTokenValue(usage,
  'output',              // OpenClaw 标准
  'outputTokens',        // OpenAI 格式
  'completionTokens',     // Anthropic 格式
  'completion_tokens'     // 小写下划线格式
);
```

**为什么需要兼容性处理？**

因为不同的工具链有不同的历史包袱和命名习惯：
- OpenClaw 使用 `input`/`output`
- OpenAI 使用 `inputTokens`/`outputTokens`
- Anthropic 使用 `promptTokens`/`completionTokens`

---

## 三、安装与使用

### 3.1 环境要求

Token Tracker 基于 Node.js 开发，需要以下环境：

- **运行时**：Node.js 18.0 或更高版本
- **操作系统**：macOS、Linux、Windows（WSL）
- **存储空间**：取决于会话数量，通常 < 100MB

**检查 Node.js 版本**

```bash
node --version
# 输出示例：v20.11.0
```

### 3.2 安装步骤

**方法一：直接运行（无需安装）**

```bash
# 克隆或下载脚本
git clone https://github.com/your-username/token-tracker.git
cd token-tracker

# 直接运行
node token-tracker.js
```

**方法二：全局安装**

```bash
# 创建符号链接到全局路径
npm link

# 然后可以在任意目录运行
token-tracker
```

### 3.3 基本用法

**运行统计**

```bash
node token-tracker.js
```

**输出说明**

```
🔧 Token Tracker - 纯本地 Token 用量统计

📂 扫描 OpenClaw...
   找到 313 条记录

════════════════════════════════════════════════════════════
  🤖 OpenClaw Token 用量统计
════════════════════════════════════════════════════════════

📊 总用量
  输入 Token:   10.42M
  输出 Token:   114.4K
  缓存读取:   5.57M
  缓存写入:   1.58M
  总费用:     $3.621138

⏰ 时段统计
  今日:  输入 9.30M | 输出 80.6K | 费用 $3.182288
  本周:  输入 9.95M | 输出 97.1K | 费用 $3.428856
  本月:  输入 10.42M | 输出 114.4K | 费用 $3.621138

🧠 按模型
  MiniMax-M2.7  输入   10.40M | 输出   110.0K | 费用 $3.589263
  MiniMax-M2.5  输入   25.6K | 输出     4.4K | 费用 $0.031875

📈 最近7天趋势
  2026-03-20 █ 457.6K
  2026-03-24 ██ 669.5K
  2026-03-28 ██████████████████████████████ 9.38M
```

### 3.4 输出格式

**终端输出（默认）**

彩色格式化输出，适合人类阅读，包含：
- 总用量统计
- 时段对比（今日/本周/本月）
- 按模型分类
- 7 天趋势图

**JSON 输出**

```bash
node token-tracker.js --json
```

```json
{
  "total": {
    "input": 10420000,
    "output": 114400,
    "cacheRead": 5570000,
    "cacheWrite": 1580000,
    "cost": 3.621138
  },
  "today": {
    "input": 9300000,
    "output": 80600,
    "cost": 3.182288
  },
  "week": { "input": 9950000, "output": 97100, "cost": 3.428856 },
  "month": { "input": 10420000, "output": 114400, "cost": 3.621138 },
  "byModel": {
    "MiniMax-M2.7": { "input": 10400000, "output": 110000, "cost": 3.589263 },
    "MiniMax-M2.5": { "input": 25600, "output": 4400, "cost": 0.031875 }
  },
  "byDay": {
    "2026-03-28": { "input": 9300000, "output": 80600, "cost": 3.182288 }
  }
}
```

JSON 格式适合：
- 程序二次处理
- 数据导入其他工具
- 自定义可视化

---

## 四、进阶用法与配置

### 4.1 时段统计详解

Token Tracker 按三个时间段聚合数据：

**今日（Today）**

- 定义：当天 00:00:00 至当前时间
- 用途：实时监控当日消耗

**本周（Week）**

- 定义：最近 7 天
- 用途：短期趋势分析

**本月（Month）**

- 定义：当月 1 日至当前时间
- 用途：月度预算规划

### 4.2 按模型分析

不同模型的 Token 单价不同，了解各模型用量有助于优化成本：

| 模型 | 输入单价 | 输出单价 | 适用场景 |
|------|----------|----------|----------|
| MiniMax-M2.7 | $0.0003/1K | $0.0012/1K | 高性能任务 |
| MiniMax-M2.5 | $0.0003/1K | $0.0012/1K | 标准任务 |
| Claude 3.5 | $0.003/1K | $0.015/1K | 高质量任务 |

### 4.3 7 天趋势图解读

趋势图使用 ASCII 条形图展示每日总 Token 消耗：

```
📈 最近7天趋势
  2026-03-20 █ 457.6K      ← 正常用量
  2026-03-24 ██ 669.5K     ← 略高，可能是复杂任务
  2026-03-28 ████████████ 9.38M  ← 异常高峰，需调查原因
```

**异常排查思路**

当日用量异常升高时，检查：
1. 是否有大规模重构任务？
2. 是否有新的复杂项目？
3. 是否误开启了循环调用？

### 4.4 定时任务配置

使用系统定时任务实现每日自动统计：

**Linux/macOS（crontab）**

```bash
# 编辑 crontab
crontab -e

# 每天早上 9 点运行统计，并保存日志
0 9 * * * /usr/bin/node /path/to/token-tracker.js >> ~/token-logs/$(date +\%Y-\%m-\%d).log 2>&1
```

**查看历史日志**

```bash
cat ~/token-logs/2026-03-28.log
```

---

## 五、开发指南

### 5.1 架构设计

Token Tracker 采用模块化架构，便于扩展：

```
token-tracker/
├── token-tracker.js      # 主入口
├── parsers/
│   ├── index.js          # 解析器接口
│   ├── openclaw.js       # OpenClaw 解析器
│   ├── claude-code.js    # Claude Code 解析器
│   └── ...               # 其他工具解析器
├── aggregators/
│   └── index.js          # 数据聚合器
└── output/
    ├── terminal.js       # 终端输出
    └── json.js           # JSON 输出
```

**核心设计原则**

1. **单一职责**：每个模块只做一件事
2. **开放封闭**：添加新工具只需新增解析器
3. **依赖注入**：便于测试和替换组件

### 5.2 解析器接口定义

所有解析器必须实现统一的接口：

```javascript
// parsers/base.js
export class BaseParser {
  /**
   * 返回解析器名称
   */
  get name() {
    return 'base';
  }
  
  /**
   * 返回支持的数据路径
   */
  getPaths() {
    throw new Error('Not implemented');
  }
  
  /**
   * 解析单个文件
   * @param {string} filePath - 文件路径
   * @returns {Array} 条目数组
   */
  parseFile(filePath) {
    throw new Error('Not implemented');
  }
  
  /**
   * 执行解析
   * @returns {Promise<Array>} 所有条目
   */
  async parse() {
    const entries = [];
    for (const path of this.getPaths()) {
      const files = await glob(path);
      for (const file of files) {
        entries.push(...this.parseFile(file));
      }
    }
    return entries;
  }
}
```

### 5.3 OpenClaw 解析器实现

以下是多工具支持的 OpenClaw 解析器完整实现：

```javascript
import { readdirSync, readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { homedir } from 'node:os';
import { aggregateToBuckets, extractSessions } from './index.js';

// OpenClaw 及兼容工具的数据路径
const POSSIBLE_ROOTS = [
  join(homedir(), '.openclaw'),
  join(homedir(), '.clawdbot'),   // 旧版本兼容
  join(homedir(), '.moltbot'),    // 旧版本兼容
  join(homedir(), '.moldbot'),    // 旧版本兼容
];

/**
 * 标准化 Token 字段提取
 * 兼容多种命名约定
 */
function getTokens(usage, ...keys) {
  for (const key of keys) {
    if (usage[key] != null && usage[key] > 0) {
      return usage[key];
    }
  }
  return 0;
}

/**
 * OpenClaw 会话解析器
 */
export async function parse() {
  const entries = [];       // Token 用量条目
  const sessionEvents = []; // 会话事件（用于元数据分析）
  
  for (const root of POSSIBLE_ROOTS) {
    const agentsDir = join(root, 'agents');
    if (!existsSync(agentsDir)) continue;
    
    let agentDirs;
    try {
      agentDirs = readdirSync(agentsDir, { withFileTypes: true })
        .filter(d => d.isDirectory());
    } catch {
      continue; // 权限不足等错误，跳过
    }
    
    for (const agentDir of agentDirs) {
      const project = agentDir.name;
      const sessionsDir = join(agentsDir, project, 'sessions');
      if (!existsSync(sessionsDir)) continue;
      
      let sessionFiles;
      try {
        sessionFiles = readdirSync(sessionsDir)
          .filter(f => f.endsWith('.jsonl'));
      } catch {
        continue;
      }
      
      for (const file of sessionFiles) {
        const filePath = join(sessionsDir, file);
        let content;
        try {
          content = readFileSync(filePath, 'utf-8');
        } catch {
          continue;
        }
        
        // 逐行解析 JSONL
        for (const line of content.split('\n')) {
          if (!line.trim()) continue;
          
          try {
            const obj = JSON.parse(line);
            
            // 只处理消息事件
            if (obj.type !== 'message') continue;
            const msg = obj.message;
            if (!msg) continue;
            
            // 提取时间戳
            const timestamp = obj.timestamp || msg.timestamp;
            if (!timestamp) continue;
            const ts = new Date(typeof timestamp === 'number' ? timestamp : timestamp);
            if (isNaN(ts.getTime())) continue;
            
            // 记录会话事件（所有消息）
            sessionEvents.push({
              sessionId: filePath,
              source: 'openclaw',
              project,
              timestamp: ts,
              role: msg.role === 'user' ? 'user' : 'assistant',
            });
            
            // 只处理助手消息（有 Token 用量）
            if (msg.role !== 'assistant') continue;
            
            const usage = msg.usage;
            if (!usage) continue;
            
            entries.push({
              source: 'openclaw',
              model: msg.model || obj.model || 'unknown',
              project,
              timestamp: ts,
              inputTokens: getTokens(usage, 'input', 'inputTokens', 
                'promptTokens', 'prompt_tokens'),
              outputTokens: getTokens(usage, 'output', 'outputTokens',
                'completionTokens', 'completion_tokens'),
              cachedInputTokens: getTokens(usage, 'cacheRead', 'cache_read',
                'cache_read_input_tokens'),
              reasoningOutputTokens: 0,
            });
          } catch {
            // 单行解析失败，跳过该行
            continue;
          }
        }
      }
    }
  }
  
  // 聚合数据
  return {
    buckets: aggregateToBuckets(entries),
    sessions: extractSessions(sessionEvents),
  };
}
```

### 5.4 添加新工具支持

假设要添加对「Kimi Code」的支持：

**步骤 1：创建解析器文件**

```javascript
// parsers/kimi-code.js
import { readdirSync, readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { homedir } from 'node:os';
import { aggregateToBuckets } from './index.js';

const KIMI_PATH = join(homedir(), '.kimi', 'sessions');

export async function parse() {
  const entries = [];
  const sessions = [];
  
  if (!existsSync(KIMI_PATH)) return { buckets: [], sessions: [] };
  
  const files = readdirSync(KIMI_PATH).filter(f => f.endsWith('.jsonl'));
  
  for (const file of files) {
    const content = readFileSync(join(KIMI_PATH, file), 'utf-8');
    
    for (const line of content.split('\n')) {
      if (!line.trim()) continue;
      try {
        const obj = JSON.parse(line);
        // Kimi Code 的格式解析逻辑
        // 此处需要根据实际日志格式进行调整
      } catch {
        continue;
      }
    }
  }
  
  return { buckets: aggregateToBuckets(entries), sessions: [] };
}
```

**步骤 2：注册到解析器索引**

```javascript
// parsers/index.js
export { parse as parseOpenClaw } from './openclaw.js';
export { parse as parseClaudeCode } from './claude-code.js';
export { parse as parseKimiCode } from './kimi-code.js';
```

**步骤 3：更新主程序**

```javascript
// 主程序中添加
import { parseKimiCode } from './parsers/kimi-code.js';

const allEntries = [
  ...(await parseOpenClaw()),
  ...(await parseClaudeCode()),
  ...(await parseKimiCode()),
];
```

---

## 六、最佳实践

### 6.1 数据安全

**本地优先原则**

- Token Tracker 不上传任何数据到网络
- 所有计算和存储都在本地完成
- 定期备份 Session 文件以防丢失

**敏感信息处理**

Session 文件可能包含：
- 提示词中的 API Key（避免在提示词中硬编码 Key）
- 项目内部信息
- 调试输出

**建议**

1. 将 Session 目录加入 .gitignore
2. 定期清理旧 Session 文件
3. 使用文件系统加密（如 macOS FileVault）

### 6.2 费用优化

**选择合适的模型**

| 场景 | 推荐模型 | 理由 |
|------|----------|------|
| 简单问答 | MiniMax-M2.5 | 便宜快速 |
| 代码补全 | MiniMax-M2.7 | 性能强 |
| 复杂推理 | Claude 3.5 | 质量最高 |

**优化提示词**

- 移除冗余的上下文
- 使用简洁的指令
- 避免重复示例

**监控异常**

设置费用阈值告警：

```javascript
const DAILY_COST_LIMIT = 10; // 美元

if (stats.today.cost > DAILY_COST_LIMIT) {
  console.warn('⚠️ 今日费用超过阈值 $10，请检查是否异常');
}
```

### 6.3 性能调优

**大量 Session 文件时的处理**

当 Session 文件很多时（如 > 1000 个），解析可能较慢：

**优化策略 1：并行处理**

```javascript
import { Worker } from 'worker_threads';

async function parseParallel(files, workerCount = 4) {
  const chunks = splitArray(files, workerCount);
  const workers = chunks.map(chunk => new Worker('./parser-worker.js', {
    workerData: { files: chunk }
  }));
  return Promise.all(workers.map(w => new Promise(resolve => {
    w.on('message', resolve);
  })));
}
```

**优化策略 2：增量更新**

不每次重新解析所有文件，而是：
1. 记录上次解析的位置
2. 只解析新增加的记录
3. 使用内存缓存中间结果

---

## 七、FAQ

**Q1：Session 文件占用空间很大怎么办？**

A：Session 文件过大会影响解析性能。建议：
- 设置 Session 文件自动轮转（如每 10000 行新建文件）
- 定期归档旧 Session 到外部存储
- 使用 gzip 压缩历史文件

**Q2：解析失败怎么排查？**

A：首先检查错误类型：
- 权限错误：`chmod 644 ~/.openclaw/agents/*/sessions/*.jsonl`
- 格式错误：使用 `head -1 file.jsonl | jq` 验证 JSON 格式
- 路径错误：确认工具已正确安装并使用过

**Q3：如何支持新的 AI 工具？**

A：参考本文档「第五章 开发指南 - 添加新工具支持」部分。主要工作：
1. 找到该工具的 Session 文件路径
2. 分析其 JSONL 格式
3. 编写对应的解析器
4. 注册到主程序

**Q4：统计结果和官方仪表板不一致？**

A：可能原因：
1. 统计时间范围不同（如时区差异）
2. 计费方式差异（如某些工具按请求计费而非 Token）
3. 缓存 Token 是否计入

建议以官方数据为准，本工具用于趋势分析。

**Q5：能否导出到 Excel？**

A：可以。使用 JSON 输出后，用以下方式转换：

```bash
node token-tracker.js --json > stats.json
# 使用 jq 或其他工具转换格式
```

---

## 八、术语表

| 术语 | 英文 | 说明 |
|------|------|------|
| Token | Token | AI 模型处理的最小文本单位 |
| 输入 Token | Input Tokens | 用户发送的提示词消耗的 Token |
| 输出 Token | Output Tokens | AI 生成的回答消耗的 Token |
| 缓存读取 | Cache Read | 从上下文缓存中读取的 Token |
| 缓存写入 | Cache Write | 写入上下文缓存的 Token |
| JSONL | JSON Lines | 每行一个 JSON 的文件格式 |
| 上下文窗口 | Context Window | 模型单次最大处理的 Token 数量 |
| 会话 | Session | 一段完整的对话交互 |
| 思考级别 | Thinking Level | OpenClaw 的推理深度配置 |

---

## 九、总结

Token Tracker 是一个轻量、隐私友好的 Token 用量追踪工具。通过阅读本文档，你应该已经：

- ✅ 理解了 Token 和用量追踪的概念
- ✅ 掌握了 OpenClaw Session 文件的结构
- ✅ 能够独立安装和使用 Token Tracker
- ✅学会了按时间、按模型分析用量数据
- ✅ 了解了如何扩展支持新的工具
- ✅ 掌握了数据安全和费用优化技巧

**下一步建议**

1. 运行一次 Token Tracker，了解你的用量模式
2. 设置定时任务，建立每日统计习惯
3. 根据数据分析结果优化 AI 使用习惯
4. 如有需要，尝试扩展支持其他工具

**参考资料**

- VibeUsage 官方仓库：https://github.com/vibe-cafe/vibe-usage
- OpenClaw 官方文档：https://docs.openclaw.ai
- JSONL 格式说明：https://jsonlines.org/

---

*🦞 由钳岳星君撰写 · 2026年3月28日*
