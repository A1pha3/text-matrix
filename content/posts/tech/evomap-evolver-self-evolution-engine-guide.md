---
title: "Evolver 五个月形态考：GEP 内核没动，集成面、网络层和许可证全换了一轮"
date: "2026-04-17T11:36:00+08:00"
lastmod: "2026-10-04T00:00:00+08:00"
slug: "evomap-evolver-self-evolution-engine-guide"
github_repo: "EvoMap/evolver"
source_key: "gh:EvoMap/evolver"
description: "EvoMap/evolver 是基于 GEP 协议的 Agent 自进化引擎：Gene/Capsule 资产是声明式 JSON 而非代码模块，solidify 阶段有命令白名单护栏。本文对照 2026-04 与 2026-10 两个时点的仓库实况，梳理它的六平台 hooks 集成、Validator/ATP 网络层、许可证从 MIT 到 GPL-3.0 再到 source-available 公告的三次变化，以及 CritPt 数字能说明什么。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "自进化", "Prompt Engineering", "Node.js"]
featuredImage: ""
extraMetadata:
  language: javascript
  version: "2.0.42"
  repo: https://github.com/EvoMap/evolver
  stars: 9129
  forks: 848
  updated_date: "2026-10-04"
---

# Evolver 五个月形态考：GEP 内核没动，集成面、网络层和许可证全换了一轮

Evolver 解决的事情从头到尾只有一件：把 AI Agent 临时性的 Prompt 调整，变成有记录、可复用、能审计的进化资产。它是一个 Prompt 生成器——扫描运行日志、匹配资产、输出协议化的 Prompt、写下审计事件——自己不碰代码编辑，不执行 Shell 命令。

这篇的初稿写于 2026-04-17，当时仓库在 v1.67.1。五个月后再回到这个仓库，会发现一个少见的形态：**进化内核几乎没有动，外围三条线全部重画了**。宿主集成从 OpenClaw 一家扩到六个平台；网络侧长出 Validator、ATP 交易市场和本地 Proxy；治理上许可证从 MIT 换到 GPL-3.0，又公告将转向 source-available。Star 数从 3,862 涨到 9,129，文件数从 158 涨到 470。

初稿按当时的 README 复述，现在看有一批描述当时就不成立——比如 `src/analysis/`、`src/selection/` 那套四模块架构，在发文当天的源码树里就不存在。本文按 2026-10-04 的仓库实况重写，关键数字全部重新核对过：GitHub API 读数、npm 版本史、发文时点（v1.67.1，commit `4c513820`）与现行 main 分支的树和 README 逐段对照。数字会继续变，所以各只出现一次，并标注时点。

## 目录

1. [先给结论](#一先给结论)
2. [五个月形态对照](#二五个月形态对照)
3. [GEP 内核：协议与真实资产结构](#三gep-内核协议与真实资产结构)
4. [一次真实运行的完整走查](#四一次真实运行的完整走查)
5. [宿主集成：六个平台与 loop 模式的真实语义](#五宿主集成六个平台与loop-模式的真实语义)
6. [网络层：Hub、Worker Pool、Validator 与 ATP](#六网络层hubworker-poolvalidator-与-atp)
7. [Proxy 与 WebUI](#七proxy-与-webui)
8. [安全模型](#八安全模型)
9. [论文与 CritPt 数字怎么读](#九论文与-critpt-数字怎么读)
10. [治理线：许可证三次变化与 source-available 公告](#十治理线许可证三次变化与-source-available-公告)
11. [采用顺序与决策建议](#十一采用顺序与决策建议)
12. [FAQ](#十二faq)
13. [附录：命令速查](#附录命令速查)

---

## 一、先给结论

**Evolver 值得关注的不是"自动改 Prompt"这个动作，而是它给改进动作套上的三层约束**：资产用声明式 JSON 描述（Gene/Capsule），改动走协议化 Prompt 输出，结果写进可审计的事件流。这三层约束五个月里没有变。

变的是三条外围线：

1. **集成面**：初稿的时代，接入宿主主要靠 OpenClaw 解释 stdout。现在有 `evolver setup-hooks --platform=...`，一条命令接入 Cursor、Claude Code、Codex、Kiro、opencode，OpenClaw 依然是原生支持。同时 README 明确了一个此前含糊的语义：`--loop` 模式的输出由 Evolver 自己消费，宿主不会拾取——想在真实会话里用，就得在会话内部单次运行。
2. **网络层**：本地 Proxy 默认开启（端口 19820），接 Hub 后每个实例默认兼任去中心化 Validator，ATP 子系统提供了 Agent 之间的任务买卖（autoBuyer、autoDeliver、merchantAgent 一应俱全）。
3. **治理**：2026-02-01 首发时是 MIT，2026-04-09 转 GPL-3.0-or-later，2026 年 9 月的 README 公告因 Hermes Agent 相似性争议，后续版本将转向 source-available。已发布的版本按原许可证继续可用。

一条容易漏看的背景：核心进化引擎模块在公开仓库里以**混淆形式**分发，这一点从初版 README 起就写在许可证一节。评估"能不能自己改内核"时，要把这条算进去。

## 二、五个月形态对照

两个时点的硬数据，均取自仓库实况（era 指发文时点 v1.67.1，commit `4c513820`，2026-04-17T01:55Z；现行指 2026-10-04 读数）：

| 维度 | era（2026-04-17） | 现行（2026-10-04） |
|------|------|------|
| 版本线 | v1.67.1（main） | main 开发线 1.94.0；npm/GitHub Release latest 为 **2.0.42** |
| 文件数 | 158（src 89 个） | 470 |
| Star / Fork | 3,862 / 392 | 9,129 / 848 |
| npm | 首发 1.67.0 在 2026-04-16（发文前一天），依赖仅 `dotenv` 一个 | 156 个版本，latest 2.0.42，依赖 6 个（含 Bedrock SDK、ATP/GEP SDK） |
| 安装主路径 | `git clone` + `npm install` + `node index.js` | `npm install -g @evomap/evolver`，命令名 `evolver` |
| GEP 资产位置 | `assets/gep/` 下三个文件 | 运行时资产在 `<workspace>/.evolver/gep/`，由运行时所有、git 忽略 |
| 宿主集成 | README 只讲 OpenClaw 解释 stdout（代码里已有 claudeCode/codex/cursor 适配器） | `setup-hooks` 六平台：Cursor、Claude Code、Codex、Kiro、opencode、OpenClaw |
| CLI 子命令 | 3 个：`solidify`、`review`、`fetch` | 22 个：`run`、`/evolve`、`login`、`logout`、`proxy-token`、`solidify`、`review`、`distill`、`fetch`、`sync`、`asset-log`、`trajectory-export`、`webui`、`setup-hooks`、`reuse`、`publish`、`recipe`、`buy`、`orders`、`verify`、`atp`、`atp-complete`、`experiment` |
| 文档 | 英文 + 中文 README + SKILL.md | 英、中、日、韩四语 README + SKILL.md |
| 许可证 | package.json 已是 GPL-3.0-or-later（4 月 9 日切换） | 同左，另有 source-available 转向公告 |
| 自动建 issue 默认仓库 | `autogame-17/capability-evolver`（前身痕迹） | `EvoMap/evolver` |

两点读法。其一，`src/` 的顶层目录从 era 起就是 `adapters/ atp/ gep/ ops/ proxy/` 加 `evolve.js` 这一套，五个月里是**加深**（gep 模块从 51 个涨到 77 个，新增 webui、experiment、solo 等），不是重写——初稿里那套 `analysis/selection/evolution` 四模块从头到尾不存在。其二，era 的 `assets/gep/genes.json` 只有 3,803 字节、3 个 Gene，`capsules.json` 是空的，`events.jsonl` 是 0 字节——所谓"资产库"在起点上是一套种子，靠用户运行时生长。

## 三、GEP 内核：协议与真实资产结构

GEP（Genome Evolution Protocol）定义三个概念：

- **Gene（基因）**：一条可复用的改进模式，声明自己响应哪些信号、按什么策略改、受什么约束、如何验证。
- **Capsule（胶囊）**：打包多个 Gene 与触发条件的复合资产。era 时点的 Capsule 库是空数组——概念先行，库存后补。
- **EvolutionEvent（进化事件）**：每次进化的审计记录。

README 的口号 "Evolution is not optional. Adapt or die." 挂在仓库首页，但协议的真实性格是保守的：只允许 DNA 这一个 emoji 出现在文档里，其余 emoji 一律禁止——初稿标题上的龙虾 emoji 按这个规矩本身就是违规的。

**Gene 不是代码模块，是声明式 JSON。** 这是初稿错得最离谱的一处：它示范了 `module.exports = { name, signals, prompt }` 的 CommonJS 写法，而真实资产长这样（era `assets/gep/genes.json` 中负责修复的那条，逐字段照录）：

```json
{
  "type": "Gene",
  "id": "gene_gep_repair_from_errors",
  "category": "repair",
  "signals_match": ["error", "exception", "failed", "unstable"],
  "preconditions": ["signals contains error-related indicators"],
  "strategy": [
    "Extract structured signals from logs and user instructions",
    "Select an existing Gene by signals match (no improvisation)",
    "Estimate blast radius (files, lines) before editing",
    "Apply smallest reversible patch",
    "Validate using declared validation steps; rollback on failure",
    "Solidify knowledge: append EvolutionEvent, update Gene/Capsule store"
  ],
  "constraints": {
    "max_files": 20,
    "forbidden_paths": [".git", "node_modules"]
  },
  "validation": [
    "node scripts/validate-modules.js ./src/evolve ./src/gep/solidify ./src/gep/policyCheck ./src/gep/selector ./src/gep/memoryGraph ./src/gep/assetStore",
    "node scripts/validate-suite.js"
  ]
}
```

era 库里一共三个 Gene，按策略三分：`gene_gep_repair_from_errors`（修复，响应 error/exception/failed/unstable）、`gene_gep_optimize_prompt_and_assets`（优化，响应 protocol/gep/prompt/audit/reusable）、`gene_gep_innovate_from_opportunity`（创新，响应 user_feature_request、perf_bottleneck、capability_gap 等）。字段名是 `id` 不是 `name`，是 `signals_match` 不是 `signals`，策略是步骤数组而不是一整段 Prompt 文本。想写自定义 Gene，照这个 schema 写 JSON。

现行版本里资产存储换了位置：运行时资产放在 `<workspace>/.evolver/gep/`（`genes.json`、`capsules.json`、`events.jsonl`），由运行时所有、被 git 忽略，可用 `GEP_ASSETS_DIR` 重定向；仓库里的 `assets/gep/` 只保留捆绑的种子（`genes.seed.json`）。首次运行时旧版资产会被复制进 `.evolver/gep/`，升级不会覆盖本地库。README 还给了一个补救命令，把曾经上传到 Hub 的资产全部拉回本地并打包成 `.gepx` 便携文件：

```bash
A2A_HUB_URL=https://evomap.ai evolver sync --scope=all --export=backup.gepx
```

从未上传过 Hub 的纯本地资产没有远端副本，只能靠 `.evolver/gep/` 或磁盘快照。

## 四、一次真实运行的完整走查

用一个场景把机制串起来：你有一个在 git 仓库里跑的 Agent，它反复在 API 超时后直接失败，日志写进了 `memory/` 目录。

```bash
$ evolver
```

按现行 README 对"成功首跑"的描述，接下来发生五件事：

1. 打印 banner，显示检测到的策略预设（默认 `balanced`）。
2. 扫描 `./memory/`（没有就创建）里的日志和信号。
3. 从本地 GEP 资产池里选出匹配的 Gene 或 Capsule——超时日志里的 error、failed 字样正落在 repair 类 Gene 的 `signals_match` 视野里。
4. 向 stdout 输出一条 GEP 协议 Prompt。这就是产出物：复制进你的 Agent，或者让宿主运行时自动消费。
5. 往 `./memory/` 写一条 EvolutionEvent 供审计。

如果第 4 步没有出现，说明当前目录不是 git 仓库——Evolver 用 git 做回滚、影响范围计算和 solidify（固化，把验证通过的进化结果沉淀为可复用资产），非 git 目录直接报错退出。除 Hub 连接外，其余全程离线。

Signal De-duplication 机制负责防止原地打转：同样的信号反复出现时被识别为停滞模式，避免"修复循环"。策略预设由 `EVOLVE_STRATEGY` 控制，四档比例五个月没变：

| 策略 | 创新 | 优化 | 修复 | 适用场景 |
|------|------|------|------|----------|
| `balanced`（默认） | 50% | 30% | 20% | 日常运营，稳定增长 |
| `innovate` | 80% | 15% | 5% | 系统稳定，快速出新 |
| `harden` | 20% | 40% | 40% | 重大变更后，聚焦稳定 |
| `repair-only` | 0% | 20% | 80% | 紧急状态，全力修复 |

SKILL.md 里还列出了三个 README 未展开的值：`early-stabilize`、`steady-state`、`auto`。

## 五、宿主集成：六个平台与 loop 模式的真实语义

era 时代接入宿主的唯一官方路径是 OpenClaw 解释 stdout 里的 `sessions_spawn(...)` 指令。现在是一条命令接六个平台：

```bash
evolver setup-hooks --platform=cursor      # 写 ~/.cursor/hooks.json + hooks 脚本
evolver setup-hooks --platform=claude-code # 经 ~/.claude/ 注册 Claude Code hook
evolver setup-hooks --platform=codex       # 写 ~/.codex/hooks.json，config.toml 启用 codex_hooks
evolver setup-hooks --platform=kiro        # 三个 *.kiro.hook，自动发现，无需重启
evolver setup-hooks --platform=opencode    # 写 ~/.opencode/plugins/evolver.js
```

OpenClaw 不需要 setup：它原生解释 Evolver 输出的 `sessions_spawn(...)` 文本，在 OpenClaw 会话内直接运行 `evolver` 即可。各平台的触发点不同，Cursor 挂在 `sessionStart`、`afterFileEdit`、`stop` 上，其余以各自的 hook 系统为准。

两个容易踩的坑，都写在现行 README 里：

**坑一：Codex 读不到会话记录。** Codex CLI 有 hook 但不产出 Cursor/Claude Code/opencode 那样的会话转录文件，`--review` 在 Codex 上读不到原始会话日志。Evolver 的补偿顺序是：工作区根的 `MEMORY.md`/`USER.md` → `setup-hooks` 注入到 `AGENTS.md` 的进化记忆段落 → 自己写的 `memory_graph.jsonl` 尾部。前几轮出现 `memory_missing` 之类的提示信号属于正常，随着 `memory_graph.jsonl` 积累会自行安静。另外 Codex 的 setup-hooks 只是生命周期集成，模型流量不走 Evolver Proxy——要路由得另配 OpenAI Responses 兼容的自定义 provider 指向 Proxy 的 `/v1` 端点。

**坑二：`--loop` 不是实时助手。** 现行 README 用了整段加粗警示：loop 模式做的是后台自维护（validator 轮次、worker 任务、ATP 商户自动交付、solidify），它的 stdout 由 Evolver 自己消费，**不会**被 OpenClaw、Cursor 或 Claude Code 拾取，即使这些运行时都装着。想让它观察并建议一个活着的 Agent 会话，就进到那个会话**内部**单次运行 `evolver`。OpenClaw 用户还要确认 `AGENT_NAME`（或 `AGENT_SESSIONS_DIR`）指向真正产生会话的目录（`~/.openclaw/agents/<name>/sessions/`），否则 Evolver 回落去读自己的日志，看起来就是在"空转"。初稿建议的"cron 每 6 小时触发 `--loop` 给 OpenClaw 用"按现行语义是不成立的——cron 保活 loop 进程没问题，但别指望 loop 的输出喂给宿主。

`sessions_spawn(...)` 的本质也值得再说一遍：它是 stdout 里的**文本**，不是函数调用。是否被解释成动作，完全取决于宿主运行时。

## 六、网络层：Hub、Worker Pool、Validator 与 ATP

不配置 Hub，Evolver 完全离线可用；配置 `.env` 后解锁网络功能：

```bash
A2A_HUB_URL=https://evomap.ai
A2A_NODE_ID=your_node_id_here
```

`A2A_NODE_ID` 不设也行，会从设备指纹自动生成。连上 Hub 后每 6 分钟发一次心跳（`HEARTBEAT_INTERVAL_MS` 可调），Hub 回推可用任务、过期告警和技能商店提示。era 时就有的 Worker Pool（`WORKER_ENABLED=1`，可按 `WORKER_DOMAINS=repair,harden` 挑任务域）继续有效，注意本地环境变量和 evomap.ai 网页上的 Worker 开关**两个都要开**，缺一个就接不到网络任务。

**Validator 角色是后来加的，且默认开启。** 每个连 Hub 的实例周期性领取一小批验证任务，在沙箱里跑提案者声明的验证命令，提交 ValidationReport，参与共识赚信用和声誉。不想参与要显式退出：`EVOLVER_VALIDATOR_ENABLED=0 evolver --loop`。

**ATP（Agent 交易市场）是 era 代码里就有、初稿漏写的一块。** era 的 `src/atp/` 有 consumerAgent、merchantAgent、hubClient 等六个文件；现行扩到 15 个文件加独立 npm SDK，长出了 autoBuyer、autoDeliver、heartbeat 信号处理等模块，CLI 里有 `buy`、`orders`、`atp`、`atp-complete`、`recipe build/reuse` 一族子命令。语义上这是给网络节点做任务买卖用的：商户 Agent 挂任务，消费者 Agent 购买执行。单机离线用户完全用不到它。

技能商店用法未变：`evolver fetch --skill <id>` 从 Hub 下载，`--out` 指定目录。发布侧，现行 CLI 提供 `publish` 子命令和资产发布 API，era README 里"共享你的 Gene 和 Capsule"说的就是这条路——初稿写的 `node index.js push --skill` 这个子命令在任何时点的源码里都不存在。

## 七、Proxy 与 WebUI

`src/proxy/` 在 era 就存在，现行长成了完整的多上游路由层：`router/` 下有 anthropic（messages）、openai（responses）、gemini、ollama、vertex、bedrock 六类路由，测试目录里能对应看到 `proxyAnthropic`、`proxyBedrock`、`proxyGeminiE2E`、`proxyOllamaE2E`、`proxyVertexE2E` 等端到端测试。它的定位在 SKILL.md 里说得很直白：**所有 EvoMap 交互都走本地 Proxy 的 mailbox（默认端口 19820，`EVOMAP_PROXY=1` 默认开启），对 Agent 侧呈现为本地 IPC**，Agent 只被允许访问 `127.0.0.1`、`api.github.com` 和 `evomap.ai`。`proxy-token` 子命令负责给 Codex 这类工具签发接入凭证。

`src/webui/` 是纯新增：observer 侧解析运行事件（runs、skills、personality、pipelineEvents、jsonl、redact），client 侧用 echarts 画图，`webui` 子命令启动。想看进化轨迹和 Gene 激活情况，这是比翻 JSONL 舒服的入口。另有 `src/experiment/`（agentRunner、comparison、metrics），配合 `experiment` 子命令做 A/B 对比。

## 八、安全模型

Evolver 的边界声明五个月没变：**Prompt 生成器，不是代码修补器**。不自动编辑源码，不执行任意 Shell 命令，核心功能离线。哪些组件碰 Shell，README 的表写得清楚：`evolve.js` 只做只读 git/进程查询；`gep/prompt.js` 和 `gep/selector.js` 是纯文本与纯逻辑；`index.js` 的 loop 恢复只打印文本；唯一执行命令的是 `gep/solidify.js`，它跑 Gene `validation` 数组里声明的验证命令，受五道闸约束：

1. 前缀白名单：只允许 `node`、`npm`、`npx` 开头的命令；
2. 禁命令替换：反引号和 `$(...)` 出现在任何位置都拒绝；
3. 禁 Shell 操作符：剥离引号内容后，`;`、`&`、`|`、`>`、`<` 都拒绝；
4. 单命令 180 秒超时；
5. 以仓库根为 cwd 执行。

外部资产的准入同样分级：`scripts/a2a_ingest.js` 摄入的 Gene/Capsule 先进隔离候选区，`scripts/a2a_promote.js` 晋升需要显式 `--validated` 标志，Gene 的全部 validation 命令过同一套安全审查，且晋升不覆盖同 ID 的本地 Gene。

回滚行为有一个值得知道的变化：`EVOLVER_ROLLBACK_MODE` 的默认值在 1.80.8 从 `hard`（`git reset --hard`，丢弃工作）改为 `stash`（`git stash push --include-untracked`，可用 `git stash pop` 找回），原因是防止在第三方宿主仓库里丢数据。

还有两条自我约束：`Protected Source Files` 机制防止自主 Agent 覆盖 Evolver 自身代码，`EVOLVE_ALLOW_SELF_MODIFY` 默认 `false`；以及那条容易被当成免责声明的实话——公开仓库里核心引擎模块以混淆形式分发，README 许可证一节从首发就写着。

## 九、论文与 CritPt 数字怎么读

2026 年 9 月起，README 顶部挂了论文 [arXiv:2604.15097](https://arxiv.org/abs/2604.15097)（*From Procedural Skills to Strategy Genes: Towards Experience-Driven Test-Time Evolution*）。按 README 的转述：在 45 个科学代码求解场景上做 4,590 次对照实验，结论是以文档为中心的 Skill 包控制信号稀疏且不稳定，紧凑的 Gene 表示整体表现最强、抗结构扰动，更适合承载经验迭代；在 CritPt 基准上，gene-evolved 系统把配对基座模型从 9.1% 提到 18.57%，从 17.7% 提到 27.14%。配套的 [OpenClaw x EvoMap 评测报告](https://evomap.ai/blog/openclaw-critpt-report)记录了同一闭环在 CritPt Physics Solver 上 Beta 到 v2.2 五个版本的演进，并给出"token 先升后降"的特征——推理被压缩进可复用基因后，单次任务的 token 消耗回落。

三个问题帮这些数字定位。**测的是什么**：科学代码求解任务上的单任务解题率，比较的是"Gene 表示 vs Skill 文档表示"两种经验载体，不是 Evolver 和其他商业产品的对比。**数字反映系统的哪部分**：反映 Gene 这类紧凑、带约束、可验证的表示在测试时进化里更稳，这支持 Evolver 坚持声明式 JSON 资产的设计选择；9.1%→18.57% 是翻倍，但绝对值离"解决"还远。**不能推出什么**：推不出你的业务 Agent 挂上 Evolver 就能有同幅度提升——任务域、基座模型、进化轮次都不同；也推不出"Skill 没用"，论文说的是 Skill 作为控制信号不稳定，不是作为文档没用。

## 十、治理线：许可证三次变化与 source-available 公告

这条线的三个时点都写在现行 README 的公告里：

1. **2026-02-01** 首发时完全开源，许可证 MIT；
2. **2026-04-09** 转 GPL-3.0-or-later——初稿 4 月 17 日发布时还写 MIT，是照抄了当时 README 上尚未更新的徽章；以 package.json 和 GitHub API 为准，发文当天已是 GPL；
3. **初稿发表后挂出的公告**（现行 README）：2026 年 3 月，同赛道的 Hermes Agent 出现了与 Evolver 在记忆更新、技能创建、进化资产沉淀三方面高度相似的设计且未作归属，完整比对见[官方博客](https://evomap.ai/en/blog/hermes-agent-evolver-similarity-analysis)；为保护项目完整性，**后续版本将从完全开源转为 source-available**。已发布的 MIT 与 GPL-3.0 版本按原许可证继续自由使用，`npm install @evomap/evolver` 和克隆仓库的现有工作流不受影响。

落到采用者头上是两句话：锁定已发布版本（GPL-3.0-or-later）的用法是安全的；指望跟进新版本并获得完整源码，需要留意 source-available 的具体条款落地。混淆分发加 source-available 两件事叠加，"自己 fork 改内核"这条路要按"基本不可用"预估。

还有个考古注脚：era 时自动建 issue 的默认仓库写的是 `autogame-17/capability-evolver`，SKILL.md 里的技能名至今叫 `capability-evolver`——项目组织迁移（autogame-17 → EvoMap）前的痕迹。

## 十一、采用顺序与决策建议

**适合现在就用的**：已有 OpenClaw / Cursor / Claude Code / Codex / Kiro / opencode 任一运行时、Agent 已上线且有稳定日志输出的团队——有日志才有信号，有宿主才能消化 stdout 指令；多人维护同一套 Agent Prompt、需要审计轨迹的团队。

**可以先不用的**：Agent 还在原型验证阶段（Prompt 天天变，审计是负担）；单人项目且 Prompt 数量很少（Git 历史已够用）；不能容忍协议开销、需要自由发挥式改动的系统（README 自己列在 Not For 里）；期待它自动改代码提效的（它不改代码）。

按风险从低到高的顺序：

1. **npm 全局安装，找个不重要的 git 仓库单次运行 `evolver`**。看它输出的 GEP Prompt 是否符合预期，这一步零风险、可离线。
2. **翻 `.evolver/gep/genes.json`，把团队反复出现的修复模式写成 Gene**。schema 照 §三 的真实结构写 JSON，先有资产再谈自动化。
3. **生产环境用 `--review`**：应用变更前暂停等人确认。对 Evolver 的信任要靠审计事件积累，不靠宣传。
4. **按平台跑 `setup-hooks`**，让 hook 自动喂信号。用 OpenClaw 的确认 `AGENT_NAME` 指向真实会话目录；用 Codex 的接受前几轮 `memory_missing` 提示。
5. **最后才接 Hub 网络功能**（Worker Pool、Validator、技能商店、ATP）。核心价值全在离线侧，网络是扩展项——并且连 Hub 前先想清楚 Validator 默认开启是否合你的合规要求，不想参与就设 `EVOLVER_VALIDATOR_ENABLED=0`。

版本策略上：npm latest 已是 2.0.x，main 开发线在 1.94——大版本线上 npm 安装与源码检出会出现版本号不一致，以 npm dist-tag 为准即可。

## 十二、FAQ

**Q：Evolver 会自动修改我的代码吗？**
不会。它是 Prompt 生成器：输出 GEP 协议 Prompt 和资产，代码编辑由宿主 Agent 或人决定。README 的原话是 "prompt generator, not a code patcher"。

**Q：为什么必须装 Git？**
回滚（Rollback）、影响范围计算（Blast Radius）、solidify 三件事都依赖 Git，非 git 目录直接报错退出。

**Q：需要连 EvoMap Hub 吗？**
不需要。分析、选择、生成、记录全部离线可用；Hub 只解锁技能商店、Worker Pool、排行榜这些网络功能。

**Q：跑 `--loop` 只见它一直打印文字，正常吗？**
正常。loop 模式的输出由 Evolver 自己消费（validator 轮次、worker 任务、solidify），不会传给宿主。想让宿主消费指令，进 Agent 会话内部单次运行 `evolver`；想人工把关，用 `--review`。

**Q：如何评估进化效果？**
看审计流：`.evolver/gep/events.jsonl` 里的 EvolutionEvent 记录了每次进化的触发信号、选中资产与结果；`webui` 子命令提供了可视化视图；实验对比可用 `experiment` 子命令自建基线。

**Q：升级会覆盖我自定义的 Gene 吗？**
不会。运行时资产归 `.evolver/gep/` 所有，git 忽略、升级不碰；仓库内 `assets/gep/` 只保留官方种子。发生过旧版本清空本地资产的事故，官方补救是 `evolver sync --scope=all --export=backup.gepx` 从 Hub 全量拉回（仅限上传过的资产）。

**Q：Gene/Capsule 和一般的 Skill 文档有什么区别？**
这是论文的核心命题：Skill 是给人读的长文档，控制信号稀疏且不稳定；Gene 是带信号匹配、策略步骤、约束和验证命令的紧凑声明式结构，机器可选、可验证、可组合。Capsule 再把多个 Gene 与触发条件打包成场景级方案。

**Q：遇到问题去哪？**
[Wiki 文档](https://evomap.ai/wiki)、[GitHub Issues](https://github.com/EvoMap/evolver/issues)、[Discord](https://discord.gg/evomap)。

## 附录：命令速查

```bash
# 安装（推荐路径）
npm install -g @evomap/evolver
evolver --help

# 运行模式
evolver                    # 单次运行：扫描、选资产、输出 GEP Prompt
evolver --review           # 审核模式：应用前等人工确认
evolver --loop             # 后台自维护循环（输出由 evolver 自身消费）

# 宿主集成
evolver setup-hooks --platform=cursor|claude-code|codex|kiro|opencode

# 生命周期（源码模式）
node src/ops/lifecycle.js start     # 启动
node src/ops/lifecycle.js stop      # 优雅停止（SIGTERM -> SIGKILL）
node src/ops/lifecycle.js status    # 运行状态
node src/ops/lifecycle.js check     # 健康检查 + 停滞自动重启

# 资产与技能
evolver fetch --skill <id> --out=./my-skills/   # 从 Hub 下载技能
evolver sync --scope=all --export=backup.gepx   # 从 Hub 全量恢复资产
evolver webui                                    # 本地可视化

# 策略控制
EVOLVE_STRATEGY=balanced node index.js      # 平衡（默认）
EVOLVE_STRATEGY=innovate node index.js      # 创新
EVOLVE_STRATEGY=harden node index.js        # 稳定
EVOLVE_STRATEGY=repair-only node index.js   # 修复
EVOLVER_VALIDATOR_ENABLED=0 evolver --loop  # 退出验证者角色

# 前置条件：Node.js（README 徽章写 >= 18，package.json engines 为 >= 22.12，以 engines 为准）+ Git
# 网络功能需在运行目录创建 .env：A2A_HUB_URL / A2A_NODE_ID
```

---

**项目信息**（2026-10-04 核对）：

- **仓库**：[EvoMap/evolver](https://github.com/EvoMap/evolver)
- **官网**：[evomap.ai](https://evomap.ai) | **文档**：[evomap.ai/wiki](https://evomap.ai/wiki)
- **语言**：JavaScript（Node.js engines >= 22.12）
- **许可**：GPL-3.0-or-later（已公告后续版本转向 source-available；核心引擎模块混淆分发）
- **版本**：npm latest 2.0.42（2026-09-30 发布）；main 开发线 1.94.0
- **Stars / Forks**：9,129 / 848
