---
title: "SmallCode：为 8B-35B 本地小模型设计的终端编码 Agent"
date: "2026-05-22T11:42:33+08:00"
lastmod: "2026-09-29T00:00:00+08:00"
slug: "smallcode-ai-coding-agent-small-llms"
github_repo: "Doorman11991/smallcode"
source_key: "gh:Doorman11991/smallcode"
description: "SmallCode 是专为 8B-35B 本地小模型设计的终端编码 Agent：MarrowScript 认知层、两阶段工具路由、patch-first 编辑、契约验收，在消费级硬件上把小模型的不可靠一处处补齐。本文按 master 快照与源码逐项核实。"
draft: false
categories: ["技术笔记"]
tags: ["Coding Agent", "本地模型", "JavaScript", "Node.js"]
---

# SmallCode：为 8B-35B 本地小模型设计的终端编码 Agent

> **核实口径**：GitHub API 2026-09-29 读数 2,031★ / 150 forks，MIT 协议，JavaScript；npm 线上 latest 为 1.6.0（2026-05-31 发布），自 0.1.0 起共 81 个版本；源码与机制描述对照 master 分支快照（README 最后更新 2026-08-06，仓库末次推送 2026-08-12）。文中行数、工具数量均以该快照实测为准。

## 一个先说清楚的判断

SmallCode 是一个终端原生的编码 Agent，从第一行代码起就是为跑在消费级硬件上的 8B-35B 本地模型设计的。它的出发点不是「再多一个 Agent」，而是一组很具体的观察：小模型上下文只有 8k-32k，tool calling 输出格式不稳定，长对话会忘事——主流工具的默认假设在小模型身上全部失效，于是它把每个失效点都配了一套工程对策。MIT 协议，纯 JavaScript/TypeScript，`npm install -g smallcode` 即装，也提供免 Node 的预编译二进制。

值得读它的原因在于方法：它示范了「不改模型、只改 harness」能吃到多少可靠性红利。这套打法对小模型部署、隐私敏感场景、边缘设备推理都有直接参考价值。

## 为什么小模型需要一套专门的 Agent

OpenCode 这类主流工具默认你用的是 Claude、GPT-5 这个量级的模型：128k+ 上下文，JSON tool calling 几乎不出错。在这个假设下，「把所有文件塞进上下文」是合理策略，编辑文件直接整文件覆写也无所谓。

8B-35B 的本地模型不满足任何一条。上下文窗口通常 8k-32k，塞几次文件就满；tool calling 的输出格式时对时错，一段推理就能把 JSON 搞坏；对话一长就丢掉前面的约定。SmallCode README 里给的建议模型区间是 8B-35B：更小的模型（≤4B）多步工具调用明显吃力，更大的模型（>35B）不需要这套适配，直接用面向前沿模型的工具更好。

项目 README 用一张对比表交代它和 OpenCode 的分工（这是项目自己的口径，不是第三方评测）：

| | OpenCode | SmallCode |
|---|----------|-----------|
| **目标模型** | 前沿模型（Claude、GPT-5） | 8B-35B 本地模型 |
| **上下文** | 全部塞入 | 预算管理 + 摘要压缩 |
| **工具调用** | 假设 JSON 可靠 | 多格式容错解析器 |
| **规划** | 单次生成 | TODO 文件逐步分解 |
| **编辑** | 全文件写入 | search-and-replace patch |
| **隐私** | 云端 API 调用 | 完全本地，默认不联网 |

## 四个月，从 0.1.0 到 1.6.0

仓库 2026-05-18 建库，当天发出 npm 0.1.0，到 2026-05-31 已发到 1.6.0，共 81 个版本。master 分支的代码一直推到 2026-08-12。这个速度意味着：任何不带日期的 SmallCode 数据都会很快过期——包括这篇自己的旧版本（写于 5 月下旬，当时还是 1,096★，「18 个工具」）。

连带的东西也值得一提：安装时 BoneScript 和 budget-aware-mcp 作为依赖一起装进来，前者负责后端代码生成，后者管 MCP 工具的预算；MarrowScript 则是独立的声明语言仓库。三个仓库分工明确，后面逐个说。

## 架构：bin/ 交互层 + src/ 库层

代码分两层，bin/ 是命令行交互入口，src/ 是可被 `require('smallcode')` 调用的库：

```text
bin/                      23 个文件（master 快照实测）
├── smallcode.js          入口：agent 循环 + TUI 编排（实测 3,329 行）
├── executor.js           全部内置工具的执行器
├── tools.js              工具 schema + 两阶段路由
├── model_client.js       LLM API 调用、流式、校验
├── governor.js           工具评分、校验、任务分解
├── escalation.js         云端模型兜底
├── cognition_adapter.js  MarrowScript 编译层与 JS 运行时的桥
├── config.js / commands.js / tui.js / mcp_bridge.js / memory.js / ...
└── provider-wizard/      交互式 provider 配置向导

src/
├── api/index.js          程序化 API 入口
├── tools/                两阶段路由、容错解析、混合检索、去重
├── governor/             early-stop、质量监控、TDD 管控
├── compiled/             MarrowScript 编译产物（.ts + .js）
├── plugins/              插件、技能、子代理、团队运行器
├── model/                多模型档位 + 自适应路由
└── session/              会话持久化、undo、共享
```

一个能说明问题的细节：README 里的架构图仍写着入口文件「1570 lines」，而 master 快照实测是 3,329 行。文档落后于代码是这个小项目的常态，读它的时候源码比 README 可信。

默认启动是全屏 TUI（备用缓冲区 + 鼠标追踪），显示异常时用 `--classic` 退回行式界面。终端状态的恢复做得比较认真：`Ctrl+Z` 挂起、被 kill、崩溃都会还原终端设置，这是 1.5.2 专门修的坑（此前只有正常退出才恢复，挂起后 shell 会漏转义序列）。

## 核心机制

### MarrowScript：把认知层写成声明

Agent 的「认知」——任务分类、模型分档、缓存、重试——不是散落在代码里的 if-else，而是写在 `marrow/` 目录的 `.marrow` 声明文件里（7 个文件共 804 行），编译成 `src/compiled/` 下的 TypeScript 运行时。README 的说法是「50 行声明编译出 1400+ 行 TypeScript」，编译产物按构建时生成，仓库内可见的部分是分类器、工具路由、质量监控等模块。

声明长这样：

```marrow
prompt classify_task_type(user_message: string) {
  model: TinyClassifier
  timeout: 3s
  cache: { key: hash(user_message), ttl: 10m }
  retry: { max_attempts: 2, backoff: fixed, interval: 100ms }
  constraints: [output in ["coding", "editing", "search", ...]]
}
```

编译层提供五件事：内容哈希 + TTL 的 prompt 缓存（命中时零开销）；每次 LLM 调用的 trace_id/span_id 追踪（`SMALLCODE_COGNITION_LOG=stderr` 开启）；按任务复杂度分档路由（琐碎任务走 tiny 模型）；按费用类别的 token 预算强制执行；schema 校验失败自动重试修复。编译层加载失败时会退回手写的正则分类器，不至于整体不可用。

### BoneScript：一个 .bone 文件换一整个后端

面向 Node.js/TypeScript 后端场景：写一个声明式 `.bone` 文件，`bone_compile` 编译出完整项目——路由、认证、数据库、事件、迁移、SDK、管理面板、Docker、CI。编译目标不止 Express，工具 schema 里给了 express（默认）、nakama、prisma、sqlite 四个选项。项目给的理由很直接：这类任务原本要 8-15 次工具调用，压成 1-2 次，小模型连续调用超过 3 步就容易散架，减少调用次数就是提升可靠性。写之前可以先用 `bone_check` 验类型和约束。

### Context Budget：上下文不越界

小模型最怕 context overflow，SmallCode 的对策分三层：

1. **工具结果截断**：每次工具调用的结果默认保留 8,000 字符（`SMALLCODE_MAX_TOOL_RESULT_CHARS` 可调，超长部分头尾保留加截断标记）；检测到模型窗口 ≥128k 时干脆不设上限。
2. **中轮次清除**：上下文膨胀时主动丢掉旧的工具结果。
3. **语义压缩**：丢之前先做摘要，保留语义而不是硬删。

在固定截断之上还有一层 read guard：当上下文用量超预算、或单个文件就超过窗口一半时，不再默默截断文件中段，而是返回文件头 30 行（import 和签名）加一句「用 grep 或指定行范围」的提示，把读取策略教给模型。

### 两阶段工具路由

工具 schema 本身就吃上下文——源码注释里给过一笔账：十几个工具的完整 schema 约 2,000 token，占 8k 窗口的四分之一。两阶段路由的解法：模型先从一个分类选择器里挑类别（read / write / search / run / plan，另有面向「X 怎么工作、谁调用了 Y」这类语义问题的 code_intel），然后只拿该类别下的工具子集 schema。窗口 ≤16k 的模型只会收到分类选择器本身，全套 schema 根本不发。

### Patch-first 编辑

小模型复现整个文件不可靠：截断、幻觉、漂移都会发生。SmallCode 把 search-and-replace patch 作为主编辑原语，`old_str` 必须在文件中恰好匹配一处；`write_file` 反而加了上限——单次 60 行 / 8KB，大文件要求先写骨架再用 patch 补。

配套一道 read-before-write guard：对本次会话没读过的已存在文件，第一次 `write_file` 会被拒绝并提示先 `read_file`，第二次才放行（合法的整体重写不受影响），新文件始终放行，patch 本身算作已读。这套规则用 `SMALLCODE_WRITE_GUARD=false` 可关。

### 失败模式的逐个拆解

小模型的失败方式很固定，SmallCode 基本每个都配了对策：

- **Early-stop**：检测三类退化行为——相同调用的重复循环、文件写坏后反复用错误内容重写的 patch 螺旋（此时强制 rewrite）、丢失上下文后的「问候回归」（重新注入任务）。
- **Quality monitor**：每轮检查空轮次、空工具名、幻觉工具名（命中时返回最接近的真实工具名作建议）、跨轮完全重复的调用，注入纠偏提示，连续纠偏封顶 2 次防止越修越乱。
- **工具信任衰减**：同一工具会话内连败 3 次降权（schema 后移），连败 5 次直接从 schema 里移除，防止模型在一个坏掉的 MCP 服务或永远空结果的搜索上打转。
- **工具调用去重**：滑动窗口内完全相同的只读调用直接返回缓存结果；对 `memory_remember` 这类幂等写工具，同轮重复调用短路返回「本轮已存」，堵住小模型连刷 30 次记忆的口子。
- **自适应重试温度**：编辑失败重试时每次换温度——第一次调低（求确定性修复），第二次调高（探索别的写法），第三次回基准值，避免同一个错连犯三遍。

### 云端兜底（可选）

本地模型在「重试 + 分解」之后仍然硬失败时，可以升级到云端模型。完全 opt-in，配了 key 才生效。目标（`bin/escalation.js` 实测）：Claude Sonnet 4.5 / 4.6、Haiku 4.5；GPT-5.4 Mini / Nano；DeepSeek V4 / V4 Pro / V4 Flash。默认模型 claude-sonnet-4-5，可用 `SMALLCODE_ESCALATION_MODEL` 覆盖。防失控做了两层：每会话最多 5 次（`SMALLCODE_ESCALATION_MAX`），且默认升级前要确认（`SMALLCODE_ESCALATION_CONFIRM`）。

## 工具面：36 个内置工具

工具表从旧版的 15 个扩到 36 个（基础 26 + provider 2 + 复合 8），另有插件和 MCP 带来的动态工具。全列出来没有意义，按用途归组：

| 组 | 工具 | 说明 |
|------|------|------|
| 代码图谱与检索 | `list_projects` `graph_search` `explain_symbol` `search` `hybrid_search` `find_files` | 符号级图谱检索 + ripgrep 正则；1.6.0 新增的 `hybrid_search` 把精确匹配和语义排序合成一次调用，BM25 + 哈希向量，纯本地无模型下载 |
| 文件读写 | `read_file` `write_file` `append_file` `patch` | patch 为主，write_file 限 60 行 |
| 执行与测试 | `bash` `run` `run_tests` | `run_tests` 返回结构化通过/失败计数，支持 pytest `-k`、jest/vitest `-t`、go test `-run`、cargo test 等过滤 |
| 复合工具 | `read_and_patch` `create_and_run` `find_and_read` `search_and_read` | 把 2 次调用合成 1 次，直接对准小模型「多步就散」的弱点 |
| 记忆 | `memory_load` `memory_remember` `memory_list` `memory_forget` | 跨会话持久化决策、坑、约定，FTS5 全文检索 + 过期衰减 |
| 契约验收 | `contract_create` `contract_status` `contract_assert_pass/fail/skip` | 见下文 |
| 技能与子代理 | `use_skill` `spawn_agent` | 技能从 `skills/` 与项目 `.smallcode/skills/` 自动加载，兼容 `.claude/skills/`、`.agents/skills/` 目录 |
| 联网（默认关） | `web_search` `web_fetch` | 需 `SMALLCODE_WEB_BROWSE=true`，走 Playwright 隐身模式；README 建议 20B+ 模型再开 |
| BoneScript | `bone_compile` `bone_check` | 见上文 |
| Provider | `configure_provider` `provider_status` | 交互式向导，免手改 .env，key 会对着 `/v1/models` 探活 |

契约验收值得单独一说：任务开始时用 `contract_create` 声明一组可测试的断言（比如「npm test 退出码 0」），此后只要还有断言停在 pending 或 failed，Agent 就不能交付「我做完了」式的收尾回复；每条断言的通过与否都要附命令行证据，状态持久化在 `.smallcode/contracts/<id>/`。这是把「完成」从模型自报改成硬校验——小模型最爱在没做完的时候宣布做完。

## 上手

### 安装

```bash
# npm 全局安装（需要 Node.js 18+）
npm install -g smallcode

# 或直接 npx 运行
npx smallcode

# Linux/macOS 一行安装脚本（注意分支是 master）
bash <(curl -fsSL https://raw.githubusercontent.com/Doorman11991/smallcode/master/install.sh)

# Windows PowerShell
iwr -Uri https://raw.githubusercontent.com/Doorman11991/smallcode/master/install.ps1 -UseBasicParsing | iex
```

脚本方式会把打包好 Node.js 的预编译 tarball 装到 `~/.smallcode` 并加进 PATH，全程不需要编译工具链。可选依赖 `better-sqlite3` 提供 FTS5 记忆检索，Node LTS 有预编译包；编译失败也不影响使用，自动退回 JSON 存储。另外 `smolv2` 是 `smallcode` 的命令别名，`smallcode-rag-index` 负责本地 GitHub 语料的 RAG 索引。

### 配置

项目根目录建 `.env`（也支持 `smallcode.toml`）：

```bash
# 必须配置
SMALLCODE_MODEL=your-model-name
SMALLCODE_BASE_URL=http://localhost:1234/v1

# 可选：云端升级兜底
# ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...
# OPENROUTER_API_KEY=sk-or-v1-...
# DEEPSEEK_API_KEY=sk-...
```

需要任意 OpenAI 兼容的本地推理服务——LM Studio 默认端口 1234，Ollama 是 11434。每个模型档位可以指到不同端点，本地跑日常任务、复杂任务走 OpenRouter 的大模型：

```bash
SMALLCODE_MODEL=qwen3:8b
SMALLCODE_BASE_URL=http://localhost:11434/v1

SMALLCODE_MODEL_STRONG=openai/gpt-4o-mini
SMALLCODE_BASE_URL_STRONG=https://openrouter.ai/api/v1
OPENROUTER_API_KEY=sk-or-v1-...
```

CPU 推理慢的机器记得调 `SMALLCODE_MODEL_TIMEOUT`（默认 300 秒），否则会看到 `timeout: no response` 报错。

### 程序化 API

```javascript
const { SmallCode } = require('smallcode');

const agent = new SmallCode({
  model: 'qwen2.5-coder-7b',
  baseUrl: 'http://localhost:1234/v1',
});

const result = await agent.run("create hello.py that prints hello world");
console.log(result.filesCreated);   // ['hello.py']
console.log(result.toolCalls.length); // 1
console.log(result.success);        // true

agent.on('tool_start', ({ name, args }) => console.log(`Using: ${name}`));
agent.on('tool_end', ({ name, ms }) => console.log(`Done: ${name} (${ms}ms)`));
```

`RunResult` 里带响应文本、工具调用记录、创建/编辑的文件、token 用量、耗时和成败标记，适合嵌进 CI 或自己的工作流。

## 基准数字怎么读

项目最显眼的数字是 87%——这是作者自报的单文件任务基准（87/100），跑在 huihui-gemma-4-e4b（8B MoE，每次前向约 4B 激活参数）上，对照的 OpenCode 约 75%、Pi Agent 约 80% 则是作者根据社区基准做的估算，且对方用的还是 14B-27B 的模型。自家 harness、自家模型、自家打分，这组数字只能当量级参考，不能当横评结论。多文件任务同一口径下是 46%，开 BoneScript 后自报可到 60%+——复杂任务仍是小模型的硬边界。

仓库里那套可复现的 benchmark harness 反而更有信息量。polyglot-mini 套件（19 题，覆盖 Python/JS/TS/Shell/Markdown/JSON）的记录显示：gemma-4-e4b 得 16/19（84%），而 lfm2.5-8b-a1b-apex 最初只对 1/19——排查结论是工具调用格式不匹配（Liquid AI 的模板标记没被解析），不是模型不行，修好 parser 后同一模型提到 9/19。这个案例把小模型评测里「harness 背锅还是模型背锅」的问题摆得很清楚。

harness 本身也随包分发：`npm run bench:smoke`（5 题，约 30 秒）、`bench:polyglot`、`bench:tools` 三套，结果存 `.smallcode/benchmarks/`；配一个 diff 工具比较两次运行，退出码 0/1/2 对应改进/回退/噪声，可以直接进 CI。

## 适用边界

**值得选 SmallCode 的场景：**

- 在 8GB-24GB 显存的消费级硬件上跑 8B-35B 编码模型，想要开箱即用的 harness
- 隐私敏感，要求默认零外发流量（联网工具默认关闭）
- 中小型编码任务：文件编辑、单项目重构、测试生成、标准后端脚手架

**不适合的场景：**

- 已经稳定用得上前沿模型——OpenCode 等成熟工具更合适，SmallCode 的全部适配对大模型是负资产
- 巨型单体仓库需要 128k+ 上下文通读（工具结果截断会碍事）
- 需要强推理的前沿算法问题——这是模型能力上限，harness 补不动
- 预算 ≤4B 的模型——多步工具调用对它仍然吃力，项目自己也不建议

## 总结

SmallCode 的技术路径可以用一句话概括：模型不动，harness 补位。从 MarrowScript 声明式认知层、两阶段工具路由，到 patch-first 编辑、契约验收、信任衰减，每个模块都对应小模型的一个具体失效模式，没有一个是为了架构好看而存在的。

它也有清楚的成本：迭代太快导致 README 长期落后于代码（行数、工具数、默认值都有出入），基准数字全部自报，四个月 81 个版本意味着文档随时可能再变。但对要在本地把小模型用起来的开发者，它是这个细分方向上工程密度最高的开源实现——读它的源码和 bench 记录，比读它的 README 收获更大。
