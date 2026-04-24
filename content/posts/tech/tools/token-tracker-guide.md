---
title: "Token Tracker 入门到精通：纯本地 AI 编程工具 Token 用量追踪实战"
date: 2026-03-28T13:38:00+08:00
slug: "token-tracker-guide-openclaw-usage"
aliases:
  - /posts/tech/token-tracker-guide-openclaw-usage/
summary: "以 OpenClaw 本地会话日志为例，讲清纯本地 Token Tracker 的设计边界、JSONL 解析、字段归一化、时间聚合与多工具扩展路径。"
description: "这是一篇面向工程实践的本地 Token 用量追踪指南：先对比 Vibe Usage 与自建方案，再用可运行的 Node.js 脚本示范如何从 OpenClaw 日志提取 usage、做多字段归一化，并说明多工具扩展与统计误差边界。"
draft: false
categories: ["技术笔记"]
tags: ["Token", "AI编程", "OpenClaw", "VibeUsage", "用量追踪"]
---

> 定位：这篇文章不教你“怎么接一个现成云面板”，而是把“纯本地 Token Tracker”拆成几个可验证的工程问题：日志在哪里、哪些字段该信、怎样做归一化、怎样避免把示意代码写成事实。
> 适合读者：想追踪 AI 编程工具 Token 消耗的个人开发者、团队负责人，以及需要本地优先方案的工程团队。
> 实操范围：以 OpenClaw 的本地会话日志为教学样本，用 Node.js 实现一个最小可用版本地统计脚本；同时说明扩展到 Claude Code、Copilot CLI、OpenCode 等工具时为什么不能继续假设“一切都是 JSONL”。
> 预计阅读时间：20 到 30 分钟。

## 学习目标

读完本文，你应该能做到：

1. 分清 Vibe Usage 和纯本地 Tracker 分别适合什么场景。
2. 知道哪些 AI 编程工具把数据写成 JSONL，哪些直接写进 SQLite。
3. 读懂 OpenClaw 会话日志里真正该计数的记录。
4. 用一段可运行的 Node.js 脚本产出按时间、按模型、按项目的本地统计结果。
5. 知道多工具扩展时应该抽象什么，哪些地方最容易重复计数。
6. 理解为什么本地统计结果和官方账单经常不会完全一致。

## 阅读路径

| 你的目标 | 建议优先阅读 |
| ---- | ---- |
| 先做一个能跑的本地版本 | §4 |
| 判断要不要自建 | §1 |
| 扩展到多工具 | §5 |
| 排查统计误差 | §6 |

## 一、先判断：你到底该直接用现成工具，还是自己做

### 1.1 为什么 Token 追踪值得单独做

Token（词元）是模型处理输入与输出时的计量单位。对 AI 编程工具来说，Token 统计至少能回答三类问题：

1. 成本问题：今天、这周、这个月到底烧了多少量。
2. 运行问题：哪些模型或项目出现了异常高峰。
3. 治理问题：团队是否需要预算、审计或本地留痕。

如果你只是偶尔问几个简单问题，系统账单页面通常已经够用。真正需要额外做 Tracker 的，往往是下面几种情况：

1. 你同时使用多个 AI 编程工具，账单分散，难以横向比较。
2. 你更关心本地日志里的真实运行轨迹，而不是供应商提供的单一账单视图。
3. 你有隐私或合规要求，不希望把使用数据再同步到第三方服务。
4. 你想按项目、按模型、按时间窗做自定义聚合，而官方面板不一定支持。

### 1.2 Vibe Usage 和纯本地 Tracker 的取舍

Vibe Usage（仓库名是 vibe-usage）已经把“从多个本地日志中抓 Token 数据，再同步到仪表板”这件事做成了现成产品。它的价值不是“会不会读日志”，而是“把多工具解析、同步、后台服务和展示面板都包好了”。

| 维度 | Vibe Usage | 纯本地 Tracker |
| ---- | ---- | ---- |
| 数据来源 | 本地日志 | 本地日志 |
| 是否需要 API Key | 需要 | 不需要 |
| 是否上传数据 | 会把聚合结果同步到 vibecafe.ai | 不上传 |
| 多工具支持 | 开箱即用，支持较多工具 | 需要自己逐个实现解析器 |
| 展示方式 | Web 仪表板 + 后台同步 | 终端、JSON、你自定义的面板 |
| 适合场景 | 想快速接入、想要现成可视化 | 本地优先、可离线、可定制、可审计 |

一句话概括：

1. 你要的是现成看板、多工具自动同步和后台守护进程，直接上 Vibe Usage。
2. 你要的是完全本地、能改统计口径、能嵌进自己的工作流，再做自建 Tracker。

### 1.3 本文的范围与非目标

为了把问题讲透，这篇文章只做一件事：以 OpenClaw 本地日志为样本，做一个纯本地、可运行、可扩展的最小版本。

本文明确不做下面几件事：

1. 不把本地统计伪装成财务结算系统。
2. 不把所有工具都写成同一种日志格式。
3. 不给出未经版本锚定的模型单价表。
4. 不提供“克隆一个并不存在的仓库就能跑”的占位式说明。

## 二、数据从哪里来：先搞清楚格式，再谈解析器

### 2.1 不是所有 AI 编程工具都把数据写成 JSONL

这是原始资料里最容易被写错的一点。很多 CLI 风格工具确实会把会话写成本地 JSONL，但并不是全部。按照 Vibe Usage README 当前公开的支持列表，至少可以分成两类：

| 工具 | 常见本地数据位置 | 存储形态 | 解析要点 |
| ---- | ---- | ---- | ---- |
| Claude Code | `~/.claude/projects/`、`~/.claude/transcripts/` | JSONL | `projects` 里有 Token，`transcripts` 更偏会话元数据 |
| Codex CLI | `~/.codex/sessions/` | JSONL | 逐文件解析会话记录 |
| GitHub Copilot CLI | `~/.copilot/session-state/*/events.jsonl` | JSONL | 事件流格式，需要按事件类型取 usage |
| OpenClaw | `~/.openclaw/agents/`、`~/.openclaw-<profile>/agents/` | JSONL | 重点看 assistant 消息里的 `usage` |
| OpenCode | `~/.local/share/opencode/opencode.db` | SQLite | 不能再用逐行 JSONL 解析 |
| Hermes | `~/.hermes/state.db` | SQLite | 需要 SQL 查询而不是文本切行 |

因此，设计本地 Tracker 时，第一原则不是“先写一个 JSONL parser”，而是“先确认这个工具到底把数据存成了什么”。

### 2.2 为什么本文选 OpenClaw 当教学样本

OpenClaw 适合作为第一站，不是因为它代表所有工具，而是因为它具备三个教学优势：

1. 本地目录结构清楚，容易定位会话文件。
2. 公开解析器实现已经展示了真实字段命名和兼容策略。
3. `message.role === 'assistant'` 且带 `usage` 的记录，足够构成最小可用的统计口径。

Vibe Usage 当前公开解析器对 OpenClaw 的路径假设是：

```text
~/.openclaw/agents/<agentDir>/sessions/*.jsonl
~/.openclaw-<profile>/agents/<agentDir>/sessions/*.jsonl

Legacy paths:
~/.clawdbot/
~/.moltbot/
~/.moldbot/
```

这里有个细节值得记住：解析器把 `agents` 下的目录名直接当成 `project` 标签使用。这个标签足够用于本地统计，但它未必等于真实仓库名。如果你后续需要“项目路径”而不是“代理目录名”，就要继续读取更完整的会话元数据，例如 `session` 事件里的 `cwd`。

### 2.3 JSON Lines（JSONL）真正要记住的规则

JSON Lines 官方规范只讲三件事：

1. 文件应当使用 UTF-8 编码。
2. 每一行都必须是一个合法的 JSON 值；空白行本身不是合法值。
3. 行终止符是换行符 `\n`，文件扩展名通常使用 `.jsonl`。

这三条在工程上分别意味着：

1. 你可以逐行读取，而不必先加载整个 JSON 数组。
2. 遇到单行损坏时，可以跳过这一行，尽量别让整份日志报废。
3. 历史文件适合直接压缩成 `.jsonl.gz` 保存。

规范并不鼓励空白行，但实际 parser 往往会宽容处理。工程上更稳的做法是：读取时允许 `continue` 跳过空行，写入时不要主动生成空行。

## 三、统计口径：什么该算，什么不该算

### 3.1 真正该计数的是 assistant 消息里的 usage

对 OpenClaw 这类日志，最核心的判断不是“这一行是不是 message”，而是“这是不是带 usage 的 assistant message”。一个足够说明问题的简化样本如下：

```jsonl
{"type":"session","timestamp":"2026-03-06T11:30:00.220Z"}
{"type":"message","timestamp":"2026-03-06T11:30:00.231Z","message":{"role":"user","content":[{"type":"text","text":"Hello"}]}}
{"type":"message","timestamp":"2026-03-06T11:30:05.754Z","message":{"role":"assistant","model":"MiniMax-M2.5","usage":{"input":36,"output":82,"cacheRead":0,"cacheWrite":16646,"totalTokens":16764,"cost":{"total":0.0021067}}}}
```

在这个例子里，真正应该进入 Token 统计的只有第三行，原因很简单：

1. 第一行是会话元数据，不是模型调用结果。
2. 第二行虽然是用户消息，但通常不直接携带最终 usage。
3. 第三行已经包含这一轮模型响应对应的输入、输出、缓存与费用信息。

换句话说，用户消息不是“不重要”，而是它的成本通常已经体现在随后那条 assistant 消息的 `input` 字段里。

### 3.2 归一化字段是多工具统计的起点

不同工具、不同 provider、甚至同一工具的不同版本，字段名都可能不一样。你真正要做的不是记住某一种命名，而是把它们归一到你自己的 canonical schema。

一个实用的最小字段映射如下：

| 逻辑指标 | 常见候选字段 |
| ---- | ---- |
| 输入 Token | `input`、`inputTokens`、`input_tokens`、`promptTokens`、`prompt_tokens` |
| 输出 Token | `output`、`outputTokens`、`output_tokens`、`completionTokens`、`completion_tokens` |
| 缓存读取 | `cacheRead`、`cache_read`、`cache_read_input_tokens` |
| 缓存写入 | `cacheWrite`、`cache_write`、`cache_creation_input_tokens` |
| 总量 | `totalTokens`、`total_tokens`，或自行求和 |
| 费用 | `cost.total`、`totalCost`，没有就保持 `0` |

这一步比你想象中更重要，因为一旦归一化没做稳，后面按模型、按项目、按时间聚合出来的报表都会掺假。

### 3.3 时间窗定义要和标题保持一致

很多文档把“最近 7 天”写成“本周”，代码却只是从当前时间往前减 6 天。这个差别看起来小，实际会影响读者对数据的理解。

本文示例统一使用三种口径：

1. 今日：本地时区当天 `00:00:00` 到当前时间。
2. 近 7 天：滚动窗口，不叫“本周”。
3. 本月：本地时区当月 1 日 `00:00:00` 到当前时间。

如果你的团队要做财务报表，最好把时区和窗口规则写进代码注释或配置项，不要默认大家理解一致。

## 四、做一个最小可用的本地 Token Tracker

### 4.1 目标和环境

这版示例只追求三件事：

1. 扫描 OpenClaw 及 profile 部署目录。
2. 读取带 `usage` 的 assistant 消息并归一化字段。
3. 输出按时间、按模型、按项目的本地统计结果，以及可二次处理的 JSON。

环境要求很简单：

| 项目 | 要求 |
| ---- | ---- |
| 运行时 | Node.js 18 或更高版本 |
| 依赖 | 仅使用 Node.js 内置模块 |
| 适用场景 | 个人使用、小团队、日志规模中等 |

### 4.2 可直接运行的 Node.js 脚本

下面这段脚本假设文件名是 `token-tracker.mjs`。它不是伪代码，而是能直接运行的最小版本。

```js
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';

const args = new Set(process.argv.slice(2));
const outputJson = args.has('--json');

function getPossibleRoots() {
  const home = homedir();
  const roots = [
    join(home, '.clawdbot'),
    join(home, '.moltbot'),
    join(home, '.moldbot'),
  ];

  try {
    for (const entry of readdirSync(home, { withFileTypes: true })) {
      if (!entry.isDirectory()) continue;
      if (entry.name === '.openclaw' || /^\.openclaw-.+/.test(entry.name)) {
        roots.push(join(home, entry.name));
      }
    }
  } catch {
    // ignore unreadable entries in home directory
  }

  return roots;
}

function getTokenValue(usage, ...keys) {
  for (const key of keys) {
    if (usage[key] != null && usage[key] > 0) return usage[key];
  }
  return 0;
}

function emptyStats() {
  return {
    input: 0,
    output: 0,
    cacheRead: 0,
    cacheWrite: 0,
    total: 0,
    cost: 0,
  };
}

function addStats(target, entry) {
  target.input += entry.input;
  target.output += entry.output;
  target.cacheRead += entry.cacheRead;
  target.cacheWrite += entry.cacheWrite;
  target.total += entry.total;
  target.cost += entry.cost;
}

function parseOpenClaw() {
  const entries = [];

  for (const root of getPossibleRoots()) {
    const agentsDir = join(root, 'agents');
    if (!existsSync(agentsDir)) continue;

    let agentDirs;
    try {
      agentDirs = readdirSync(agentsDir, { withFileTypes: true }).filter(
        entry => entry.isDirectory()
      );
    } catch {
      continue;
    }

    for (const agentDir of agentDirs) {
      const project = agentDir.name;
      const sessionsDir = join(agentsDir, project, 'sessions');
      if (!existsSync(sessionsDir)) continue;

      let files;
      try {
        files = readdirSync(sessionsDir).filter(name => name.endsWith('.jsonl'));
      } catch {
        continue;
      }

      for (const file of files) {
        const filePath = join(sessionsDir, file);
        let content;
        try {
          content = readFileSync(filePath, 'utf8');
        } catch {
          continue;
        }

        for (const line of content.split('\n')) {
          if (!line.trim()) continue;

          try {
            const obj = JSON.parse(line);
            if (obj.type !== 'message') continue;

            const message = obj.message;
            if (!message || message.role !== 'assistant' || !message.usage) continue;

            const rawTs = obj.timestamp ?? message.timestamp;
            if (!rawTs) continue;

            const timestamp = new Date(rawTs);
            if (Number.isNaN(timestamp.getTime())) continue;

            const usage = message.usage;
            const input = getTokenValue(
              usage,
              'input',
              'inputTokens',
              'input_tokens',
              'promptTokens',
              'prompt_tokens'
            );
            const output = getTokenValue(
              usage,
              'output',
              'outputTokens',
              'output_tokens',
              'completionTokens',
              'completion_tokens'
            );
            const cacheRead = getTokenValue(
              usage,
              'cacheRead',
              'cache_read',
              'cache_read_input_tokens'
            );
            const cacheWrite = getTokenValue(
              usage,
              'cacheWrite',
              'cache_write',
              'cache_creation_input_tokens'
            );

            const total =
              usage.totalTokens ??
              usage.total_tokens ??
              input + output + cacheRead + cacheWrite;

            const cost =
              usage.cost?.total ??
              usage.cost?.amount ??
              usage.totalCost ??
              0;

            entries.push({
              project,
              model: message.model || obj.model || 'unknown',
              timestamp,
              input,
              output,
              cacheRead,
              cacheWrite,
              total,
              cost,
            });
          } catch {
            continue;
          }
        }
      }
    }
  }

  return entries;
}

function localDayKey(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function summarize(entries) {
  const now = new Date();
  const todayStart = new Date(now);
  todayStart.setHours(0, 0, 0, 0);

  const weekStart = new Date(now);
  weekStart.setDate(now.getDate() - 6);
  weekStart.setHours(0, 0, 0, 0);

  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);

  const total = emptyStats();
  const today = emptyStats();
  const week = emptyStats();
  const month = emptyStats();
  const byModel = new Map();
  const byProject = new Map();
  const byDay = new Map();

  for (const entry of entries) {
    addStats(total, entry);

    if (entry.timestamp >= todayStart) addStats(today, entry);
    if (entry.timestamp >= weekStart) addStats(week, entry);
    if (entry.timestamp >= monthStart) addStats(month, entry);

    if (!byModel.has(entry.model)) byModel.set(entry.model, emptyStats());
    addStats(byModel.get(entry.model), entry);

    if (!byProject.has(entry.project)) byProject.set(entry.project, emptyStats());
    addStats(byProject.get(entry.project), entry);

    const dayKey = localDayKey(entry.timestamp);
    if (!byDay.has(dayKey)) byDay.set(dayKey, emptyStats());
    addStats(byDay.get(dayKey), entry);
  }

  return {
    scannedMessages: entries.length,
    total,
    today,
    week,
    month,
    byModel: Object.fromEntries(
      [...byModel.entries()].sort((a, b) => b[1].total - a[1].total)
    ),
    byProject: Object.fromEntries(
      [...byProject.entries()].sort((a, b) => b[1].total - a[1].total)
    ),
    byDay: Object.fromEntries([...byDay.entries()].sort()),
  };
}

function shortNumber(value) {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(2)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return `${value}`;
}

function printStats(label, stats) {
  console.log(
    `${label.padEnd(8)} 输入 ${shortNumber(stats.input).padStart(8)} | 输出 ${shortNumber(stats.output).padStart(8)} | 总量 ${shortNumber(stats.total).padStart(8)} | 费用 $${stats.cost.toFixed(4)}`
  );
}

function main() {
  const entries = parseOpenClaw();
  const result = summarize(entries);

  if (outputJson) {
    console.log(JSON.stringify(result, null, 2));
    return;
  }

  console.log('Token Tracker（OpenClaw 本地版）');
  console.log('');
  console.log(`解析到 ${result.scannedMessages} 条带 usage 的 assistant 消息`);
  console.log('');
  printStats('总计', result.total);
  printStats('今日', result.today);
  printStats('近 7 天', result.week);
  printStats('本月', result.month);

  console.log('');
  console.log('按模型');
  for (const [model, stats] of Object.entries(result.byModel).slice(0, 10)) {
    printStats(model, stats);
  }

  console.log('');
  console.log('按项目');
  for (const [project, stats] of Object.entries(result.byProject).slice(0, 10)) {
    printStats(project, stats);
  }
}

main();
```

### 4.3 运行方式与输出示例

```bash
node token-tracker.mjs
node token-tracker.mjs --json
```

终端输出大致会长这样：

```text
Token Tracker（OpenClaw 本地版）

解析到 313 条带 usage 的 assistant 消息

总计      输入   10.42M | 输出   114.4K | 总量   17.68M | 费用 $3.6211
今日      输入    9.30M | 输出    80.6K | 总量   15.91M | 费用 $3.1823
近 7 天   输入    9.95M | 输出    97.1K | 总量   16.94M | 费用 $3.4288
本月      输入   10.42M | 输出   114.4K | 总量   17.68M | 费用 $3.6211
```

JSON 输出则更适合接给 `jq`、DuckDB、Grafana 或你自己的内部脚本。

### 4.4 这段代码为什么这样写

这版脚本看起来直白，但几个设计点是故意保留下来的：

1. 目录发现是动态的。除了 `~/.openclaw`，还会扫描 `~/.openclaw-<profile>`，并兼容老目录名。
2. 统计入口是 assistant 消息，不是所有 message。
3. 归一化优先做在 parser 层，而不是渲染层。
4. 按天分桶使用本地日期，而不是 `toISOString()` 的 UTC 日期，避免跨时区后把深夜请求算到第二天。
5. 遇到单行损坏直接跳过，避免整份文件失败。
6. 输出同时保留“总量”和分组结果，方便后续二次消费。

这版脚本也刻意省略了两件事：

1. 没有做 session 元数据统计。Vibe Usage 会额外提取 active time、总时长、消息数等信息；这里先不展开，避免第一版就把抽象做重。
2. 没有使用流式读取。对个人或中小规模日志，`readFileSync + split('\n')` 足够简单；如果你已经有成千上万份大文件，再换成 `readline` 流式解析更合适。

### 4.5 如果你需要 30 分钟粒度，而不是按天聚合

Vibe Usage 当前公开口径是把 Token 聚合到 30 分钟 bucket。这个思路很好，因为它天然适合做趋势图和增量同步。你只要把 `byDay` 的 key 换成半小时 bucket 即可：

```js
function halfHourBucketKey(date) {
  const bucket = new Date(date);
  bucket.setMinutes(bucket.getMinutes() < 30 ? 0 : 30, 0, 0);
  return bucket.toISOString();
}
```

然后把 `bucketKeyByDay(entry.timestamp)` 替换成 `halfHourBucketKey(entry.timestamp)`。第一版为什么我没有直接这么写？因为教学上更重要的是先把“口径是否正确”讲清楚，再把颗粒度细化。

## 五、扩到多工具时，别把整套逻辑重写一遍

### 5.1 先定义统一条目结构

真正该复用的不是某个工具的路径，而是解析完成后的统一条目结构。一个够用的 canonical entry 可以长这样：

```js
{
  source: 'openclaw',
  project: 'demo-project',
  model: 'MiniMax-M2.5',
  timestamp: new Date(),
  input: 36,
  output: 82,
  cacheRead: 0,
  cacheWrite: 16646,
  total: 16764,
  cost: 0.0021067,
}
```

只要各个 parser 最终都吐出这个形状，后面的聚合器和输出层就不用为每种工具重写一遍。

### 5.2 JSONL 工具和 SQLite 工具，应该分成两条实现路线

多工具扩展最常见的错误，是把 OpenClaw 的解析方式复制到一切工具上。正确做法是按存储形态分层：

| 存储形态 | 代表工具 | 建议策略 |
| ---- | ---- | ---- |
| JSONL | OpenClaw、Claude Code、Copilot CLI | 逐行读取，按事件类型和 usage 字段提取 |
| SQLite | OpenCode、Hermes | 用 SQL 查询抽取所需字段，再映射成 canonical entry |

Claude Code 就是一个很好的反例。它不仅有 `projects` 目录，还会把会话转录写到 `transcripts`；前者更适合提 Token，后者更适合补会话元数据。换句话说，多工具支持不是“多扫几个目录”，而是“搞清这个工具把什么信息拆到了哪里”。

### 5.3 三个最容易踩的坑

扩展到多工具后，下面三个问题几乎一定会出现：

1. 重复计数：同一 session 可能被多个目录、多个副本或子代理文件重复记录。
2. 字段漂移：不同工具的 usage key 名称不一致，甚至同工具不同版本也会变。
3. 幂等更新：如果你做增量同步或每日快照，必须保证重复导入不会把总量越加越大。

因此，一个稍微像样的多工具版本通常都会补这几件事：

1. 去重键，例如 UUID、sessionId 或文件路径组合。
2. 统一 entry schema。
3. 明确的 bucket 粒度和时间窗定义。
4. “原始日志解析”与“报表输出”解耦。

## 六、准确性边界：本地统计为什么经常和官方账单不一致

### 6.1 本地 Tracker 更像运行信号系统，不是结算系统

本地 Tracker 的强项是观察趋势，不是给财务做最终对账。出现差异时，通常不是代码错了，而是统计对象本来就不同。常见原因包括：

1. 官方账单会考虑供应商侧重试、舍弃请求、隐藏折扣或特殊计费规则。
2. 本地日志可能只记录成功写回的 usage，不一定覆盖所有失败请求。
3. 有些工具会记录缓存字段，有些不会；你计不计缓存，结果都会变。
4. 时间窗和时区不一致时，“今日”与“本月”的边界也会不同。

更稳的心态是：

1. 用本地 Tracker 做运行监控、项目归因和异常排查。
2. 用官方账单做最终结算和采购核对。

### 6.2 费用字段不一定可靠，价格表最好独立版本化

有些日志会直接把 `cost.total` 写出来，有些只给 Token 数，没有费用字段。即便有费用字段，也可能随着 provider 版本、地区、折扣策略变化而变化。

因此，费用统计有两条更稳的实践：

1. 日志里有 `cost` 就直接累加，同时保留原始 Token 数。
2. 日志里没有 `cost` 时，把价格表独立成配置，不要把单价硬编码在 parser 里。

后者的好处是：你升级模型、切换 provider 或补历史价格时，不必重写解析逻辑。

### 6.3 事实锚点优先级：本机日志 > 解析器源码 > 宣传页

写这类技术文档时，最稳的事实来源顺序通常是：

1. 你自己机器上的真实日志样本。
2. 公开 parser 源码或 README 中明确给出的路径与字段。
3. 产品官网和宣传页。

原因不复杂：官网讲的是产品能力，parser 关心的却是“具体文件在什么路径、哪条字段可读、哪种格式要兼容”。这两类信息并不总在同一层。

## 七、把它变成能长期使用的工具

### 7.1 一份够用的落地清单

如果你准备把本文示例从“能跑”升级到“能长期用”，优先补下面几项：

1. 把时间窗、时区和 bucket 粒度写进配置。
2. 增加去重策略，避免重复 session 或子代理日志重复统计。
3. 为多工具 parser 建立统一测试样本，至少覆盖 3 到 5 份真实日志。
4. 把历史 JSONL 压缩归档，避免长期增长拖慢解析速度。
5. 为敏感日志目录加访问控制，并避免把日志纳入 Git 仓库。
6. 如果要团队使用，优先定义“什么数字拿来做监控，什么数字拿来做结算”。

### 7.2 四个常见问题

**Q1：为什么我明明发了很多消息，统计条数却不高？**

因为这版口径统计的是“带 usage 的 assistant 消息”，不是所有消息条数。用户消息多，不代表模型调用就多。

**Q2：为什么某些工具完全没有数据？**

先确认两件事：

1. 这个工具的本地数据位置是不是你以为的路径。
2. 它到底写的是 JSONL，还是 SQLite、二进制缓存或别的格式。

**Q3：为什么项目名看起来不像仓库名？**

因为很多 parser 直接用目录名作为 `project` 标签。对 OpenClaw 来说，这个标签常常只是 `agents` 下的子目录名，不一定是实际工作区名称。

**Q4：什么时候该放弃自建，直接用 Vibe Usage？**

当你已经明确需要：

1. 多工具统一面板。
2. 后台持续同步。
3. 跨设备追踪。
4. 少维护、快交付。

这时候继续自建，往往是在重复造已经成熟的轮子。

## 八、总结

如果只保留三条结论，我会留这三条：

1. 纯本地 Token Tracker 最重要的不是界面，而是统计口径和事实锚点。
2. OpenClaw 这类 JSONL 工具适合做教学起点，但多工具扩展一定要承认 SQLite 等异构存储的存在。
3. 本地统计更适合做运行监控和行为分析，不适合冒充最终账单。

你可以把本文的最小脚本当成一个稳定起点。先把 OpenClaw 跑通，再决定是继续补多工具 parser，还是直接切换到 Vibe Usage 这类已经把同步、看板和后台服务做好的方案。

## 相关资源

- [Vibe Usage 仓库](https://github.com/vibe-cafe/vibe-usage)
- [Vibe Usage 的 OpenClaw 解析器](https://github.com/vibe-cafe/vibe-usage/blob/main/src/parsers/openclaw.js)
- [JSON Lines 官方规范](https://jsonlines.org/)
