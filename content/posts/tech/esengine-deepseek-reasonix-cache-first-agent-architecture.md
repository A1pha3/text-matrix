---
title: "DeepSeek-Reasonix：把 prefix-cache 字节稳定性做成可检查约束的 terminal coding agent"
date: 2026-06-21T17:55:00+08:00
lastmod: "2026-09-19T00:00:00+08:00"
slug: "deepseek-reasonix-cache-first-agent-architecture"
github_repo: "esengine/DeepSeek-Reasonix"
source_key: "gh:esengine/DeepSeek-Reasonix"
categories: ["技术笔记"]
tags: ["DeepSeek", "Coding Agent", "Go", "架构分析", "Prompt Cache"]
description: "Reasonix 把 prompt prefix cache 的字节稳定性做成可检查约束：环境探测落快照、工具 schema 由测试锁定、PR 必须声明 Cache-impact 等级。本文分清 v1 三条 Pillar 与 v2 真实实现，并核对安装通道、语义检索、成本机制的版本边界。"
draft: false
---

## 一句话判断

Reasonix 值得单独写一篇，不是因为它又做了一个终端里的 AI 编码智能体（coding agent）。它做的是另一件事：把「提示词前缀缓存」（prompt prefix cache）的字节稳定性从运行时属性改成仓库里的可检查对象。环境探测结果要先落快照才准进系统提示词，内置工具的模式声明（schema）由一条 Go 测试锁住，改动碰到缓存敏感文件的 PR 必须自己填 `Cache-impact` 等级。

另一件事得先说清楚。三条 Pillar、`<<<NEEDS_PRO>>>`、`REASONIX_PARALLEL_MAX` 这一整套说法出自 **v1 分支**（TypeScript，0.x）的 `docs/ARCHITECTURE.md`，而那条线现在只收 bug fix。把 v1 的设计当成当前产品来读，会得出「它绑死 DeepSeek」「桌面端用 Wails」「装 `@next`」这类已经失效的结论。所以本文给每一条机制都标上属于哪一代。

## 项目速览

| 项 | 值（2026-09-19 核实） |
|---|---|
| 仓库 | [esengine/DeepSeek-Reasonix](https://github.com/esengine/DeepSeek-Reasonix) |
| 默认分支 | `main-v2`（Go 线），另有维护线 `v1` 与 `studio` |
| Star 与复刻数 | 35,612 / 2,403 |
| 许可证 / 语言 | MIT / Go |
| 创建时间 | 2026-04-21 |
| 最新发布 | `v1.38.10`（2026-09-18），仓库累计 249 个 release |
| npm 通道 | `latest`、`next`、`canary` 同时指向 1.38.10 |
| 未关闭 issue / PR | 1,460 / 496（仓库 `open_issues_count` 的 1,956 是两者之和） |
| 入口 | 终端 TUI、桌面应用、浏览器（`reasonix serve`）、编辑器（ACP） |

## 目录

- [两条代码线，一次真实的重写](#两条代码线一次真实的重写)
- [安装通道：一条命令的三段历史](#安装通道一条命令的三段历史)
- [v1 文档里的三条 Pillar](#v1-文档里的三条-pillar)
- [v2：同一条不变量，换成一组合约](#v2同一条不变量换成一组合约)
- [哪些机制在 v2 里找不到](#哪些机制在-v2-里找不到)
- [任务流：一次 edit_file 穿过哪些缓存面](#任务流一次-edit_file-穿过哪些缓存面)
- [benchmark 怎么读：99.82% 与仓库里的三套 harness](#benchmark-怎么读9982-与仓库里的三套-harness)
- [并行执行：v1 靠环境变量，v2 靠调用分类](#并行执行v1-靠环境变量v2-靠调用分类)
- [采用建议](#采用建议)
- [常见故障与排查](#常见故障与排查)
- [五个自测题](#五个自测题)
- [下一步读哪份代码](#下一步读哪份代码)
- [维护指引与事实核对记录](#维护指引与事实核对记录)

---

## 两条代码线，一次真实的重写

| | v1（Legacy） | v2（Reasonix 1.0+） |
|---|---|---|
| 语言 | TypeScript / Node.js | Go |
| 版本 | `0.x`，npm 上最后一个 0.54.2（2026-05-29） | `1.0.0`（2026-06-03）起 |
| 分支 | `v1`，只收 bug fix | `main-v2`，默认分支 |
| 分发 | npm 包，需要 Node.js 运行时 | `CGO_ENABLED=0` 单静态二进制，交叉编译 darwin/linux/windows × amd64/arm64 |
| 代码智能 | 嵌入向量（embedding）语义检索 + tree-sitter 符号索引 | LSP 辅助读码 + `grep` / `read_file` / `glob`，语义索引未移植 |
| 桌面壳 | — | 1.0.0 用 Wails，现改为 Electron + Go 桌面服务 + React |

「v1 / v2」是代际标签，不是语义化版本：v1 那条线从未发布过 1.0，所以 Go 重写直接占用 `1.x` 主版本。

哪些东西保留了下来，`docs/MIGRATING.md` 写得比任何二手解读都清楚：agent 循环、内置工具、子智能体、skills、hooks、plan mode、MCP 客户端，以及「面向 DeepSeek prefix-cache 的设计」。三条 Pillar 因此没有被打翻，它换了一种存在方式——从一份写在架构文档里的设计说明，变成一组测试、CI 守卫和 provider 适配层。

## 安装通道：一条命令的三段历史

`npm i -g reasonix` 这句话的含义在四个月内变了三次，是理解这个项目版本策略最好的例子。

第一段：Go 重写发布 1.0.0（2026-06-03）时，npm 的 `latest` 仍钉在 `0.x`，作为存量用户的迁移保护，想装新版得显式写 `reasonix@next`。这条建议在 2026 年 7 月之后失效。

第二段：这个保护在 1.x 转正之后反转了——`npm update -g` 的用户会被**静默降级**回 TypeScript 版本（上游 issue #5822）。于是 `latest` 在 **1.17.5**（2026-07-06）切到 Go 线，守卫撤掉。

第三段：现在 `latest`、`next`、`canary` 是同一个官方版本的三个别名，预发布候选版不再公开发布。装旧版靠钉版本：

```sh
npm i -g reasonix          # 当前官方 1.x
npm i -g reasonix@0.53.2   # 钉住遗留的 TypeScript 版本
```

内置更新器 `reasonix upgrade` 只挑严格的 `vX.Y.Z` 非预发布 GitHub Release；旧的 channel 参数与 `--channel` 在这个兼容期内仍被接受，但一律解析到同一官方版本并打印废弃提示。桌面安装包与 release 归档是**另一条通道**，装它们不会碰你用 npm 装的命令行工具（CLI），所以 shell 里是 0.53、桌面上是 1.x 属于正常并存，不是冲突。

## v1 文档里的三条 Pillar

出处：`v1` 分支 `docs/ARCHITECTURE.md`。这一节描述的是 TypeScript 0.x 的设计，不是当前二进制里的代码。

**Pillar 1 — Cache-First Loop。** DeepSeek 的自动前缀缓存只在「上一轮请求的字节前缀与本轮完全相同」时命中。多数 agent 循环做不到：每轮都在重排 tool result、注入时间戳、改写 system prompt。文档给出的实测是命中率低于 20%。解法是把上下文切成三个生命周期不同的区域：

| 区域 | 内容 | 生命周期 |
|---|---|---|
| Immutable Prefix | system 提示词、工具声明、few-shot 示例 | 整个会话固定，是缓存命中的候选 |
| Append-Only Log | assistant 与 tool 消息交替 | 单调追加，保住上一轮的前缀 |
| Volatile Scratch | 思考过程与临时计划状态 | 每轮重置，永不上行 |

三条不变量随之成立：前缀在会话开始时算一次哈希（hash）并钉死；日志条目按追加顺序序列化，不许改写；scratch 里的信息必须先经 Pillar 2 蒸馏才能进日志。指标 `prompt_cache_hit_tokens / (hit + miss)` 每轮暴露，汇总到会话，显示在 TUI 顶栏的 cache 单元格里。

**Pillar 2 — Tool-Call Repair。** 文档列了四种有结构的失效，而不是「词元（token）乱码」那种罕见情况：tool call 的 JSON 写在 `reasoning_content` 里忘了发出；参数个数超过 10 个或嵌套过深时被吞掉；同一 `(tool, args)` 反复调用（call-storm）；触顶 `max_tokens` 导致 JSON 截断。对应四个 pass——`flatten`、`scavenge`、`truncation`、`storm`——顺序执行。

**Pillar 3 — Cost Control（标注为 v0.6 引入）。** 文档用三个 preset 交换模型层级与推理强度：`flash`（1×）、`auto`（默认，难题轮升到 pro，1–3×）、`pro`（约 12×）；所有辅助调用——摘要、子智能体、截断修复重试——硬编码 flash 加 `effort=high`，不随用户选择变化，理由是「把工具结果改写成散文」不该按顶层模型计价。工具结果超过 `TURN_END_RESULT_CAP_TOKENS`（默认 3000）时在轮末压到该上限；长多轮 turn 内另有 40% 主动压缩与 80% 紧急压缩两道阈值。最特别的是模型自报告升级：模型判定当前层级不够，就在响应首行打 `<<<NEEDS_PRO>>>`，系统中断本轮 flash 调用、整轮在 pro 上重来；已经在 pro 上时该标记什么都不做。

这一节要额外小心，因为**同一分支自己的文档已经互相不一致**。`CHANGELOG.md` 的 0.50.0（2026-05-24）写着 preset 抽象被移除（#1657、#1630），配置改为直接暴露 `model` 与 `effort`，`/pro` 开关一并删掉；每个具名 skill 可以单独覆盖 flash / pro（#1632）。也就是说上面那张 preset 表在 v1 生命周期的最后阶段也不成立了，读 `ARCHITECTURE.md` 时要把它当成设计说明而不是当前行为。还有一处小坑：这份文档的章节标题写着 "The four pillars"，正文只有 1、2、3 三节。

## v2：同一条不变量，换成一组合约

v2 没有沿用三区命名，但同一目标（让 provider 侧看到的字节前缀尽量不动）被拆进了若干处可验证的实现。下面每一条都能在当前 `main-v2` 源码或文档里指认到位置。

### 环境探测必须落快照才准进 prompt

`[environment].enabled = true` 会把 OS、shell 和常用工具链的摘要注入提示词，探测项包括 `go version`、`python3 --version`、`node --version` 等。问题在于这类输出会随进程重启而变，一变就击穿前缀。

`internal/environment/probe.go` 的处理方式是给探测加一层持久化快照：`SnapshotDir` 下按指纹存一份到 `environment/`，24 小时 TTL 内直接复用不再探测，刷新时把瞬时失败与上一份快照合并。启动时这个目录是真接上的——`internal/boot/boot.go` 把它指向 `config.CacheDir()`。代码注释把理由写明了：让渲染出的环境段落**字节稳定**，缓存的系统提示词前缀才能活过重建。快照目录属于宿主状态，不进模型可见内容，也不参与指纹。

### 指令、记忆与召回各归其位

`docs/SESSION_MEMORY_RETRIEVAL.md` 末尾的「Cache and privacy contract」是理解 v2 前缀结构最快的一份材料，它同时规定了缓存边界和隐私边界：

- 常驻指令在会话开始时并入稳定的 system 前缀；派生索引与被钉住的指引放在带版本的 `session-context` 快照里，digest 变了就在下一个真实用户轮之前刷新。
- 动态召回**只追加到当前这一条用户消息**，不插到历史里。
- provider 可见的出处标签用 `workspace/...`、`user/...`、`project/<name>.md` 这类稳定形式；绝对路径只留在本地诊断信息里。
- 诊断内容不进 provider 请求；自动召回省略存储路径并抹掉片段里的家目录前缀。

规矩可以一句话说完：进前缀的必须是不随环境漂移的内容，出处标签用固定形状；会变的，一律追加到尾部或留在本地。

### 工具声明是测试锁定的契约

前缀里最贵的一块是工具定义。v2 把它写成了一份生成出来的契约文档：`docs/TOOL_CONTRACT.md` 收录 24 个编译期内置工具的名称、只读标记与描述，并声明文档与运行时注册表走同一条 canonical schema 路径。要验证一致性，跑的不是 lint 而是测试：

```sh
go test ./internal/tool -run TestBuiltinToolContractDocumentation
```

真正影响每次请求形状的是同一份文档里的「Unified Boot Surface」。它区分两种启动面：默认全量启动发送这 24 个内置工具，再加 session、memory、skill、subagent、LSP、install 与 slash-command 工具；而**每个任务**实际拿到的是一份精简核心——`bash`、`bash_output`、`edit_file`、`kill_shell`、`read_file`、`view_image`、`wait`、`write_file`、按需注册的 `compress`，加上一个稳定的能力代理 `use_capability`。

`glob`、`grep`、`ls`、`web_fetch`、MCP、skills、子智能体、docs、会话历史、记忆写入这些可选能力仍留在宿主注册表里，由模型通过 `use_capability` 去列出、检查、调用或放弃，provider 可见的工具列表因此不变。文档把这条设计说得很直白：任务风险改变的是宿主的规划、验证与复核策略，不是 provider 能看到哪些工具。另一条测试 `internal/boot.TestBootToolContractMatchesProviderVisibleSurface` 负责核对启动注册表与实际发出的请求一致，包括只读标记与 canonical schema。

「中途不新增工具声明」于是从设计偏好变成了接口形状。

### 缓存未命中要有归因

`internal/agent/cache_shape.go` 定义了一个 `PrefixShape`，对影响缓存复用的部分取哈希：`SystemHash`、`ToolsHash`、`PrefixHash`、`SessionContextDigest`，外加 `LogRewriteVersion` 和 `ToolSchemaTokens`。工具 schema 在哈希前先按名称、描述、参数规范化排序，避免顺序抖动造成假变化。

轮与轮之间用 `CompareShape` 比对。`internal/event/session_context_diagnostics.go` 给 `PrefixChangeReasons` 举的例子是 `system`、`tools`、`log_rewrite`、`session_context`，实际列表还要拼上从会话里排空的内容重写原因（例如 `compact_auto`、`snip`、`rewind_truncate`）。这里有一条值得学的判定纪律：**只影响本地的改写不算缓存变化**。决策回执、tool-call 预览、`Edited` 消息替换都会推进 `LogRewriteVersion`，但如果排不到对应的 provider 可见重写原因，就不能报成缓存问题。

这些数字最终露在界面上。CLI 的状态栏会渲染本轮 usage（`cached <N>` / fresh tokens），并在前缀真的变了时打一条告警 `cache prefix changed: <reasons>`；`/status` 汇总 model、effort、cache、Git、后台任务与余额。也就是说 v1 那句「开发者能直接看到循环有没有违反不变量」，在 v2 里落成了带原因码的界面元素。

### 压缩阈值就写成一个缓存权衡

v2 只保留一个自动压缩触发点。`internal/agent/compact.go` 里 `defaultCompactRatio = 0.80`，注释称其为「新配置下唯一的自动维护触发」。同一文件的头注释把压缩定性为低频的缓存重置点：prompt 以只追加的方式增长，直到越过窗口的 `compactRatio`，再由压力期的工具剪枝与最多两个缓存对齐的摘要检查点腾出空间。

用户可调，范围 30–85%，内置默认 80%：

```sh
reasonix config compact-ratio             # 看生效值与来源
reasonix config compact-ratio 75          # 用户全局默认
reasonix config compact-ratio --local 75  # 写进 ./reasonix.toml
```

文档把代价说全了：调低会更早压缩，可能增加摘要调用与成本，并**降低 prompt-prefix cache 复用**；调高则在阈值以下保留完整工具结果，普通请求成本上升。项目级 `reasonix.toml` 优先于用户配置，改动只对新建会话生效。

工具结果另有字符量闸门，且只在压力下生效。`internal/agent/prune.go` 的 `pruneToolResultContent` 以 `toolPruneThresholdRunes = 8192` 为界：不超过就原样返回，超过则留头 4096 个字符与尾 1024 个字符，中间换成 `[... tool result middle pruned ...]`。触发条件写在 `shouldPruneBeforeFold` 里——维护触发是 `pressure` 或 `overflow` 时先剪再折叠，手动 `/compact` 只有在已经越过硬输入上限时才算救援、才先剪。

还有一处容易读错。`pruneToolResultsToProjectionLocked` 装的是**持久化但只改视图**的投影：剪过的内容写进 provider 可见消息，同时清空 `RawContent` 与 `ProviderContent`，注释明确写着规范存储（canonical storage）从不被修改。同一文件里的 `SnipStaleToolResults` 与 `PruneStaleToolResults` 两个公开方法如今是 no-op，只服务于兼容旧存储；按 80 / 12 行比例剪枝的那套 `snipStrategy` 属于这条遗留路径，不是当前压力期的行为。可比的另一个数是近期逐字尾部预算占窗口 16%，摘要输出上限 8192 token。

### 同一条不变量，跨 provider 有几种写法

「只绑 DeepSeek」这个判断在 v2 不成立，证据在 provider 适配层。DeepSeek 走隐式路径，Reasonix 只读响应体顶层的 `prompt_cache_hit_tokens` / `prompt_cache_miss_tokens`。Anthropic 走显式路径：`internal/provider/anthropic/session_context_cache.go` 的 `markPromptCacheBreakpoints` 给请求打 `cache_control: {"type": "ephemeral"}` 断点。注释写明 Anthropic 原生允许 4 个断点，Reasonix 只用最多 3 个——稳定的 system（无 system 时退到 tools）、最近一条有效的 session-context 消息、请求尾部——并保留默认 5 分钟 TTL。

配置面同样是多模型的。`reasonix.example.toml` 里 DeepSeek 只是一个 provider 条目（`models = ["deepseek-v4-flash", "deepseek-v4-pro"]`），旁边就是 Anthropic 与本地端点示例。仓库内置一批 curated provider 预设，Anthropic、OpenAI、Gemini、Groq、Together、OpenRouter、Ollama 与国内的 Kimi、智谱、LongCat 都在里面。双模型协作也能开：`planner_model` 与 `subagent_model` 分开配。README 那句话是准确的：DeepSeek 是预设，任何 OpenAI 兼容的应用程序接口（API）端点是一条配置而不是新代码。

## 哪些机制在 v2 里找不到

这一节把前面从 v1 文档借来的说法逐条作废。结论来自 `main-v2` 工作树的全量 grep，判据是「字面量与实现都不存在」，而不是「没找到」。

| v1 说法 | v2 现状 |
|---|---|
| `<<<NEEDS_PRO>>>` 模型自报告升级 | 全仓 0 命中，含代码、文档与站点 |
| `flatten` / `scavenge` / `truncation` / `storm` 四个修复 pass | 无对应实现；「修复」的语义换成了中断事实记录 |
| `REASONIX_PARALLEL_MAX`、`REASONIX_TOOL_DISPATCH` | 两个环境变量都不存在，并行度写死在代码里 |
| `TURN_END_RESULT_CAP_TOKENS = 3000` | 量纲换成字符（阈值 8192），且不再是每轮结束时压，而是压力下先剪再折叠 |
| 40% 主动 + 80% 紧急双阈值 | `compact_ratio` 单阈值，默认 80%，可配 30–85 |
| flash / auto / pro 三档 preset | 执行模式已取消，`/preset`、`/work-mode`、`/profile` 是隐藏的兼容命令 |
| `complete_step` 逐步签核 | 已废弃，模型用 `todo_write` 直接更新任务状态 |
| Web 仪表盘（dashboard）被移除 | 仍在：`reasonix serve` 提供本地浏览器 UI，桌面端为首选可视化入口 |
| 桌面端用 Wails | 已迁到 Electron，Wails 入口与构建依赖删除，迁移证据留在 `docs/DESKTOP_SHELL_MIGRATION.md` |

v2 里替代 Pillar 2 的那套东西叫「工具中断与恢复」（`docs/TOOL_RECOVERY.md`），关注点从「修复模型输出」变成「每个 provider 可见的 tool call 都要有一个诚实结果」。结果被记成 `not_started`、completed / failed、中断但有副作用、`unknown` 四类，其中 `unknown` 只作为执行事实写入一次，不动态改系统提示词。文档明确拒绝了几件事：不自动重放调用、不从当前状态伪造成功、不屏蔽相同参数、不装全局只读闸门，并且承认对外部服务没有 exactly-once 保证。

安装包签名的状态也变了。README 写明 Windows 安装包经 SignPath.io 签名，仓库里另有 Certum SimplySign 云签名流程与 `macos-signing-check.yml`、`apple-notary-log.yml` 两条工作流。早前流行的「未签名、要手动 `xattr -dr com.apple.quarantine`」那套说法来自另一代分发条件，按当前上游文档已经不成立。

## 任务流：一次 edit_file 穿过哪些缓存面

把上面的机制串成一次真实工作。用户说「把 `auth.go` 里的 `validateToken` 改名成 `verifyToken`」，在 v2 里发生的事是：

1. 请求出发前 `CaptureShape` 取一份前缀快照：system 提示词、规范化工具 schema、`session-context` digest。
2. 模型返回 `edit_file` 调用。`edit_file` 是写类工具（契约表里 `Read-only = false`），`parallelisableCall` 判否，于是它单独成一批；同一轮里排在它前面或后面的 `read_file` 仍会凑成并行批，上限 8。若模型想搜代码，它发出的不是 `grep` 调用而是 `use_capability` 的一次 `call`，读写属性按目标算。
3. 结构化写要求宿主侧对目标文件当前版本的观察记录，读窗口成功即建立观察；文件被外部改过会返回 `FS_STALE_VERSION`，但不阻塞无关工具。
4. 结果进会话日志，按只追加方式扩展。本轮 usage 里的 `cache_hit` / `cache_miss` 连同成本渲染成状态栏的一条回执；若 `CompareShape` 判出前缀变了，紧跟一条 `cache prefix changed: …`。
5. `edit_file` 返回的 diff 远不到 8192 字符，剪枝闸门即使触发也不碰它；而闸门本身要等到 `pressure` 或 `overflow` 才会执行。
6. 只有当会话总量越过窗口的 `compact_ratio`（默认 80%）才触发压缩；压缩点是低频的，一次折叠会带走一段可摘要的历史。
7. 下一轮：system 与环境摘要字节不变、工具声明不变、日志只在尾部追加，前缀命中。

对照 v1 的讲法，差异在于这条链路上每一步的「为什么」都有落点：不并行不是因为 `parallelSafe=false` 这个默认值，而是因为写类调用被分类器排除；不重排历史不是因为文档写了条不变量，而是因为动态内容被规定只能追加到当前用户轮。

## benchmark 怎么读：99.82% 与仓库里的三套 harness

v1 分支 README 有一行很醒目的数据：

> **Real user, single day (2026-05-01):** 435M input tokens, **99.82% cache hit**, ~$12 instead of the ~$61 the same workload would cost with no cache on `v4-flash`

它指向 `benchmarks/real-world-cache/README.md`。这个目录在 `main-v2` 上**不存在**，当前 README 也没有这句话。所以读它的正确姿势是：v1 线某位真实用户单日的输入侧命中率与按其当时定价折算的成本对比，属于历史案例，既不是 v2 的回归基线，也不是可复现的承诺。

不能从它推出的结论至少三条。推不出「任何用户都能跑到 99.82%」——工作流里只要有人往 system prompt 里塞动态内容，命中率立刻掉。推不出「换后端也一样」——隐式前缀匹配与显式断点是两种机制，v2 为此写了两套适配。推不出「成本永远是这个数」——它依赖 DeepSeek 当期价格与套餐。

v2 自己怎么衡量这件事，答案在 `benchmarks/README.md`，三套 harness 各自对准一个具体问题：

- `e2e/` 由 `cmd/e2ebench` 驱动，跑真实 provider，输出 Markdown 与 JSON 报告，字段是准确率、**cache-hit 率**、token 用量与成本，定位就是贴进 PR 里对比。
- `context-maintenance-e2e/` 是一个 seed → resume → 理解的独立装置，用来 A/B 比较冷启动时带不带上下文剪枝的缓存表现。
- `compaction/` 是 CompactionBench：一次一代地把会话撑大、每代折叠，量化反复压缩的代价与信息损失。

任务集的分层比分数更有信息量。`atomic-bugfix`、`repo-exploration`、`multi-file-bugfix`、`refactor`、`failing-test-diagnosis`、`api-integration`、`ambiguous`、`long-horizon` 都按目标数配齐。另有 11 个 `completion-integrity` 任务是**故意没有可达解**的，按诚实度而不是正确性评分——这类任务才真正测得出「模型会不会假装做完了」。仓库还留了 SWE-bench Verified 的子集与 `verification-stress`。

## 并行执行：v1 靠环境变量，v2 靠调用分类

v1 把并行度做成配置：每个工具声明 `parallelSafe`（默认 false），连续的并行安全调用成块，用 `Promise.allSettled` 竞速，遇到第一个非并行安全调用就结束当前块单独执行；`REASONIX_PARALLEL_MAX` 默认 3、硬上限 16，`REASONIX_TOOL_DISPATCH=serial` 是逃生口。

v2 的判断依据换成了「一次调用能不能被分类」。`internal/agent/execute_batch.go` 先把连续的、判定可并行的调用切成一批，其余一次一条；`parallelisableCall` 的判据按顺序是：

1. `todo_write`、`get_goal`、`create_goal`、`update_goal`、`wait`、`bash_output`、`compress` 七个名字直接判否。
2. 目标解析不到、或存在歧义，判否。
3. 实现 `BatchClassifier` 的工具，要求 `Known && ReadOnly && ParallelSafe` 三条同时成立。
4. 实现 `CallResolver`（调用时才确定目标）的工具判否。
5. 其余退到 `target.ReadOnly()`。

并发上限是代码里的 `const maxParallel = 8`（信号量容量），不再有环境变量。取消也做了约束：一个被取消的并行段最多再等 `parallelStragglerGrace = 15 * time.Second`，超过就把未返回的调用按 `unknown` 上报，而不是让整轮卡在一个不理会 context 的工具上。

经 `use_capability` 到达的能力有自己一套判定：`list` / `search` / `inspect` 三种动作直接给 `Known + ReadOnly + ParallelSafe`；`call` 要看目标，MCP 工具必须同时满足缓存里只读（读的是 server 声明的 `readOnlyHint`，没声明就按写类处理）、未标记破坏性、来自共享宿主、且该 server 没被标为串行才允许并行。`CallClass` 还带一个 `Generation`（取 schema 指纹），注释写明空值会把调用留在串行路径上——注册表在会话中变了，并行就不安全。

## 采用建议

先说谁适合现在就用。

- **要在长会话里跑自主任务，且关心 token 成本**。这是整个仓库的设计靶心，README 的标题就是「a coding agent you can leave running」。
- **要用 DeepSeek，但不想被它锁死**。DeepSeek 是预设，同一份配置里换成任何 OpenAI 兼容端点都行，Anthropic 走显式缓存断点。
- **需要终端 + 桌面 + 浏览器 + 编辑器四路入口**，或者要把 agent 嵌进现有集成开发环境（IDE），走 `reasonix acp`；VS Code 扩展的 ID 是 `SivanLiu.reasonix-agent`，源码在 SivanCola 名下。
- **在意可撤销性**：权限闸门、工作区沙箱、每轮检查点与 `--copy`（在恢复会话的可写副本上继续）都为一整夜自主跑完之后还能回读、回退而准备。

谁可以再等等，或者根本不必用。

- **大型单仓库（monorepo）依赖语义检索**。v2 目前只有 LSP 加 `grep` / `read_file` / `glob`，`docs/MIGRATING.md` 直说 v1 的语义检索与 tree-sitter 符号索引「尚未打包进 v2」，CodeGraph 也不再以内置 MCP server 形式提供。习惯 Cursor / Sourcegraph 那种检索体验的人会觉得是退步。
- **需要 v1 那套自报告升级**。`NEEDS_PRO` 在 v2 不存在，替代物是 `planner_model` / `subagent_model` 的双模型分工与按轮的任务风险判断。
- **只要一个稳定不动的工具**。发布节奏很快：npm 上从 1.32.1（2026-08-28）走到 1.38.10（2026-09-18），三周内 15 个版本，其中 1.38.6 与 1.38.7 同一天发布。配置字段会随保存被清理，兼容期过后废弃参数会报错。

落地顺序我建议这样：装 `npm i -g reasonix`，跑 `reasonix setup` 选 provider，进交互界面后用 `/status` 确认 cache 单元有读数，拿一个中等改动任务跑完，再按状态栏的 `cache prefix changed` 原因回看是哪一块前缀被打破。想调成本就先动 `compact_ratio`，动完用 `/status` 和一轮真实任务的回执对照，而不是凭感觉。

## 常见故障与排查

按现象分类，前两类是这套架构特有的，其余是版本迁移遗留。

### 1. cache 命中率低，或忽高忽低

先看状态栏有没有 `cache prefix changed:` 告警，它后面的原因码直接决定往哪查。

- 原因是 `system`：先查常驻指令文件有没有被改动（`REASONIX.md` / `AGENTS.md` / `CLAUDE.md`，含嵌套目录里的那些），再看环境摘要是否重建。前者是维护指令的正常成本，后者要确认快照目录可写。
- 原因是 `tools`：`ToolsHash` 变了，说明 provider 可见的工具集或某条 schema 变了。先查 `reasonix.toml` 的 `[tools].enabled`（空值表示全部内置工具都发）与 `compress` 是否被注册。MCP 工具本身不再改这份列表——它们藏在 `use_capability` 后面，所以「新接了一个 MCP server」不该出现在这里。
- 原因是 `session_context`：`session-context` 快照的 digest 变了，属预期刷新。
- 原因是 `compact_auto` / `snip` / `rewind_truncate`：上下文维护造成的历史重写。先跑 `reasonix config compact-ratio` 看生效值与来源，项目级 `reasonix.toml` 会盖过用户配置。
- 一条原因都没报但命中率仍低：说明前缀字节是稳的，差距出在本轮尾部新增了多少内容（超长工具输出、整份贴进来的日志）。该改的是读文件与贴日志的方式，而不是阈值。

### 2. 装了 1.x 却像装到旧版

先确认 `reasonix --version` 与 `npm ls -g reasonix` 的版本号是否一致。npm 与 GitHub release 归档、桌面安装包是三条独立通道，历史遗留的 0.53 很可能还在你的 PATH 里更早被命中。桌面端与 CLI 版本不一致是预期状态，不算故障。

### 3. 找不到 `/pro`、`/preset`、`work-mode`

这三样都已废弃。`/pro` 早在 v1 的 0.50.0 就被 sticky 的 `/model` 取代；`/preset`、`/work-mode`、`/profile` 在 v2 是隐藏兼容命令，认识它们的历史值时会告知已废弃并保持标准执行模式。当前有效的是 `/model`、`/provider`、`/effort`。

### 4. 老配置、老会话没带过来

v1.8.1 起会在首次启动做一次性、非破坏性的导入，来源包括 `~/Library/Application Support/reasonix/config.toml`、`~/.config/reasonix/config.toml`、`~/.reasonix/reasonix.toml` 与 v0.x 的 `~/.reasonix/config.json`；旧的 `config.json` 里的 API key、base URL、语言与 MCP server 都会被读，凭据补进 `<Reasonix home>/.env`。关键限制是：**只有在新配置还不存在时才导入**。如果新版已经写过 `config.toml`，缺的值就得手工搬。自动导入漏了的，在交互会话里跑 `/migrate`，Windows 上老数据在自定义目录时用 `/migrate --from "D:\OldReasonix"` 指定来源。

### 5. 编辑别的目录里的文件被拒

普通写操作受活动预设与操作系统沙箱约束。要跨目录，用 `--add-dir PATH`（可重复）显式扩权，而不是全局放开权限模式。`--dangerously-skip-permissions` 是已废弃的兼容参数，会保守地映射到 `workspace-write`；真要无限制是 `--permission-mode danger-full-access`。

### 6. 非 UTF-8 文件读出来是乱码

支持的编码是 UTF-8、UTF-8 BOM、UTF-16 LE/BE 与 GB18030（GBK 超集）。`read_file` 解码为 UTF-8 交给模型，`edit_file` / `multi_edit` 保留原编码，`write_file` 一律写 UTF-8，`grep` 先解码再匹配。这一条在 1.0.0 曾被丢掉过（CJK 字符集文件被误读或当成二进制拒绝），修复记录在 CHANGELOG 的 #2637。

## 五个自测题

1. **v2 靠什么保证「重启之后前缀仍然一样」？**
   <details>
   <summary>答案</summary>
   环境探测结果按指纹落快照，TTL 内不重探、刷新时与旧快照合并，使渲染出的环境段落字节稳定；常驻指令在会话开始并入 system 前缀，派生索引与被钉住的指引放进带版本的 `session-context` 快照；动态召回只追加到当前用户轮。
   </details>

2. **一次 cache miss 发生后，怎么知道是谁打破前缀的？**
   <details>
   <summary>答案</summary>
   `PrefixShape` 对 system、规范化工具 schema 与 `session-context` digest 取哈希，`CompareShape` 比对相邻快照并给出原因码（`system`、`tools`、`session_context`，加上 `compact_auto`、`snip`、`rewind_truncate` 这类内容重写原因），状态栏以 `cache prefix changed: …` 呈现。仅影响本地的改写（决策回执、tool-call 预览）不报为缓存变化。
   </details>

3. **为什么 v2 只留一个自动压缩阈值，还把它的代价写成缓存问题？**
   <details>
   <summary>答案</summary>
   压缩会重建 provider 可见历史，是一次低频的缓存重置点，所以触发点越少越可预期。`compact_ratio` 默认 80%、可配 30–85%：调低更早折叠，增加摘要调用与成本并降低前缀复用；调高则在阈值以下保留完整工具结果，抬高普通请求成本。工具结果的 8192 字符剪枝闸门只在 `pressure` 或 `overflow` 触发时先于折叠执行。
   </details>

4. **`reasonix@next` 现在还必要吗？为什么？**
   <details>
   <summary>答案</summary>
   不必要。`latest` 在 1.17.5 切到 Go 线，此前钉在 0.x 的迁移保护会让 `npm update -g` 被静默降级（#5822）因而撤掉；现在 `latest`、`next`、`canary` 指向同一官方版本。要装遗留 TypeScript 版得钉 `reasonix@0.53.2`。
   </details>

5. **「Reasonix 绑 DeepSeek 后端」这句话错在哪？**
   <details>
   <summary>答案</summary>
   绑的是缓存字节的稳定性，不是某家 API。DeepSeek 走响应里的 `prompt_cache_hit/miss` 隐式命中；Anthropic 走 `cache_control: ephemeral` 显式断点，原生允许 4 个而 Reasonix 只用最多 3 个（稳定 system 或 tools、最近一条有效 session-context、请求尾部），默认 5 分钟 TTL。配置面还有覆盖 Anthropic / OpenAI / Gemini / Groq / Ollama 等的 provider 预设与双模型协作字段。
   </details>

## 下一步读哪份代码

按问题入口走，比按目录浏览省时间。

| 想弄清的问题 | 读这里 |
|---|---|
| 前缀到底由什么组成 | `docs/SESSION_MEMORY_RETRIEVAL.md` 的 Cache and privacy contract |
| 工具声明怎么保持稳定 | `docs/TOOL_CONTRACT.md` 与 `go test ./internal/tool -run TestBuiltinToolContractDocumentation` |
| miss 怎么归因 | `internal/agent/cache_shape.go`、`internal/cli/status_footer.go` |
| 什么时候折叠历史 | `internal/agent/compact.go`、`internal/agent/prune.go`、`docs/CLI.md` 的 Configure automatic compaction |
| 调用能不能并行 | `internal/agent/execute_batch.go` 的 `parallelisableCall` 与 `runParallel` |
| 中断后如何交代 | `docs/TOOL_RECOVERY.md`、`internal/agent/interrupted_recovery.go` |
| 为什么从 Wails 换成 Electron | `docs/DESKTOP_SHELL_MIGRATION.md` |
| v1 的三条 Pillar 原文 | `v1` 分支 `docs/ARCHITECTURE.md` |

想改这个仓库，先读 `.github/pull_request_template.md` 与 `scripts/check-cache-impact.sh`：`Cache-impact: none|low|medium|high` 是必答项，改了常驻指令文件却填 `none` 会被守卫拦下。

## 维护指引与事实核对记录

本文的断言按下列时间点与方式核对，复核时优先看「失效条件」而不是重读全文。

| 主题 | 依据 | 何时需要重查 |
|---|---|---|
| 三条 Pillar、`NEEDS_PRO`、preset、`REASONIX_PARALLEL_MAX` | `v1` 分支 `docs/ARCHITECTURE.md` | v1 只收 bug fix，本节相对稳定；该分支若再有发布则重读 |
| v1 / v2 代际、安装通道、语义检索缺失 | `docs/MIGRATING.md` 与 npm registry `time` 字段 | `latest` tag 或版本策略再变时 |
| 环境快照、剪枝阈值、`compact_ratio`、`maxParallel` | `main-v2` 工作树源码 | 每次大版本后重跑 grep |
| 缓存契约与工具契约 | `docs/SESSION_MEMORY_RETRIEVAL.md`、`docs/TOOL_CONTRACT.md` | 内置工具数量变化时 |
| 99.82% 案例的适用范围 | `v1` 分支 README；`main-v2` 无 `benchmarks/real-world-cache` | v2 若重新发布该案例则本节要改写 |
| Star、复刻、release 与 issue 数 | GitHub 仓库接口与 search 接口，2026-09-19 | 每次引用前重取，这类数字两周就会过期 |

三个复现命令，够用来抽查本文最容易被改错的部分：

```sh
git clone -b main-v2 --depth 1 https://github.com/esengine/DeepSeek-Reasonix
cd DeepSeek-Reasonix && grep -rn "NEEDS_PRO" . ; ls benchmarks
curl -s https://registry.npmjs.org/reasonix | python3 -c "import json,sys;print(json.load(sys.stdin)['dist-tags'])"
```

第二条命令里 `grep` 没有输出、`ls` 里没有 `real-world-cache`，这两处空白正是 v2 实现与 v1 架构叙述的分界。

## 参考资料

- [esengine/DeepSeek-Reasonix](https://github.com/esengine/DeepSeek-Reasonix) — 默认分支 `main-v2`
- [v1 分支 Architecture](https://github.com/esengine/DeepSeek-Reasonix/blob/v1/docs/ARCHITECTURE.md) — 三条 Pillar 的原始出处
- [docs/MIGRATING.md](https://github.com/esengine/DeepSeek-Reasonix/blob/main-v2/docs/MIGRATING.md) — 代际差异与安装通道
- [docs/TOOL_CONTRACT.md](https://github.com/esengine/DeepSeek-Reasonix/blob/main-v2/docs/TOOL_CONTRACT.md) — 内置工具与启动面
- [docs/SESSION_MEMORY_RETRIEVAL.md](https://github.com/esengine/DeepSeek-Reasonix/blob/main-v2/docs/SESSION_MEMORY_RETRIEVAL.md) — 上下文与缓存契约
- [docs/DESKTOP_SHELL_MIGRATION.md](https://github.com/esengine/DeepSeek-Reasonix/blob/main-v2/docs/DESKTOP_SHELL_MIGRATION.md) — Wails 到 Electron
- [benchmarks/README.md](https://github.com/esengine/DeepSeek-Reasonix/blob/main-v2/benchmarks/README.md) — 三套 harness 与任务分层
