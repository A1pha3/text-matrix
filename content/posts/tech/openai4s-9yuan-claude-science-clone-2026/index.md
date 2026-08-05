---
title: "9.9 元/月复刻 Claude Science：北大袁粒组 OpenAI4S 是怎么把科学 Agent 拉下神坛的"
date: 2026-08-05T09:00:00+08:00
draft: false
summary: "北大—元空 AI 联合实验室开源的 OpenAI4S,把 Anthropic 闭源的 Claude Science 用纯标准库 + 豆包 ¥9.9 月费重写了一遍。本文拆开它的双循环引擎、33 个科学 Skill、Seatbelt/bubblewrap 沙箱、与众不同的「账本优先」架构——以及它对科研 Agent 这条赛道的真正冲击。"
tags: ["OpenAI4S", "Claude Science", "Code-as-Action", "科学 Agent", "袁粒组", "PKU-YuanGroup", "豆包", "开源"]
categories: ["技术文章"]
authors: ["钳岳"]
github_repo: "PKU-YuanGroup/OpenAI4S"
description: "9.9 元/月复刻 Claude Science：拆开 OpenAI4S 的双循环引擎、33 个科学 Skill、Seatbelt/bubblewrap 沙箱、与众不同的「账本优先」架构,以及对科研 Agent 赛道的冲击。"
slug : index

---

## 一、9.9 元,科学 Agent 的「廉价化时刻」

2026 年 7 月 6 日,北大袁粒组(PKU-YuanGroup)把 OpenAI4S 整个代码库开源了。九天之后的 7 月 15 日,他们又推了一份 macOS `.dmg` 镜像——Apple Silicon 用户下载,拖进「应用程序」,双击就能跑。

OpenAI4S 从头到尾都在回答一个问题:**科学 Agent 凭什么要花 Claude Science 的订阅费?**

答案很直白:**不凭什么**。OpenAI4S 跑在火山方舟的豆包 Small 套餐上,¥9.9/月——折合不到一杯精品咖啡。它完整复刻了 Claude Science 的核心架构:Code-as-Action 引擎、持久 Python/R 内核、host RPC、34 个预装科学 Skill、双层沙箱、Action Ledger。一行命令,不联网,不烧 token,照样能跑 AlphaFold2 预测、DiffDock 分子对接、单细胞分析。

它不是「灵感致敬」,README 里写得很直接:

> An open-source **hybrid scientific research agent** that **replicates Claude Science** in two cuts or less.

所谓「two cuts」,指的不是两刀学术定义,是九块九的人民币。

---

## 二、双循环架构:为什么「Code-as-Action」比「工具调用」更合适做科研

OpenAI4S 的核心架构叫 **hybrid action engine**,刻意把 Agent 的动作分成两个平面:

- **JSON 控制平面**——原生 tool call 负责工作流、权限、元数据、外部服务、人类审批。这是 ReAct 那一套。
- **Python/R 科学平面**——真正的计算、探索、分析、仿真放在持久内核里跑。Python Cell 还能在执行中途**同步**反向调用 host 服务。

这两个平面走的是两个不同的循环:

### 外层循环(Outer Loop)

`openai4s/agent/engine.py` 是 provider-neutral 状态机。每轮只做三选一:

1. 一组有序的原生 JSON tool call(走控制平面)
2. 一个 Engine 自有的 `FinalizeAction`(只一次,关闭 Engine)
3. 一个完整的 Python/R Code Cell(走科学平面)

`finalize_response` 的 schema 和执行逻辑锁死在 `agent/finalize.py` 里——插件不能换,这是 Engine 的终止契约。`host.submit_output(...)` 是**唯一**能从 Python Cell 内部发出的完成信号,这意味着 R Cell 没有「自闭」能力,必须依赖外层 finalize。

### 内层循环(Inner Loop)

内层才是 OpenAI4S 的精髓。在一个 Python Cell 内部,Agent 代码可以**同步**调 `host.llm(...)`、`host.delegate(...)`、`host.compute(...)` 任意多次。每次调用走的是一条**与 stdout 捕获分开的 RPC 通道**:

```
host_call → host_ack → host_response
```

Cell 阻塞,host 服务中途响应,Cell 继续。架构文档里特地强调:

> **This inner RPC loop does not exist in a `tool_use` architecture** — there, actions are atomic and never call back into the host mid-execution.

意思是,在 ReAct 范式下,Agent 每做一步都得 round-trip 一次模型,让模型看完结果再决定下一步。对一个要处理 100k 行 DataFrame 的科学任务来说,这等于把整个内存往 context 里塞,然后再让模型决定下一步干嘛。

OpenAI4S 的解法是:把 DataFrame 留在 kernel 里,context 里只留一个 `<DataFrame 100000×20>` 描述符。Cell 自己决定「读 → 过滤 → 排序 → 画图」要多少步,中间需要 LLM 帮忙解析列名,直接 `host.llm("这一列是什么意思?")`,**不用退出 Cell**。

走一遍最常见的真实场景——人胰岛素 INS(P01308)从 UniProt 拉到结构预测:

```python
# 在一个 Python Cell 内,前后是同一个持久内核
seq = host.web_fetch("https://rest.uniprot.org/uniprotkb/P01308.fasta").text
import re
hits = [r for r in host.science.search("insulin", database="uniprot") if "human" in r["organism"]]
# 走到第 50 行才需要 LLM —— 它帮 Cell 把列名解释清楚
col_meaning = host.llm(
    f"这些字段名 {hits[0]['keys']} 各自表示什么?返回中文,每项一行。"
)
# Cell 没结束,内核 namespace 继续可用
host.save_artifact({"summary": "INS human", "interpretation": col_meaning},
                   source=hits[0]["provenance"])
host.submit_output(structured={"n_hits": len(hits), "top": hits[0]["id"]},
                   summary=f"命中 {len(hits)} 条人类胰岛素记录,top: {hits[0]['id']}")
```

`provenance` 字段带着时间戳、SHA-256 和原始请求,直接挂到 artifact 的 version 上——下个月再跑同一份分析,即使 UniProt 返回变了,artifact 仍然能解释「这份结果是当时那份数据算出来的」。这段代码在 Claude Science 里要走十几次 round-trip,在 OpenAI4S 里是**一个 Cell**。

Code-as-Action 在论文里能找到两个出处:CodeAct 把「代码作为统一动作接口」,ReAct 是「推理+动作协同」。OpenAI4S 把两者都接上了,但内层同步 RPC 是它独有的工程实现。

---

## 三、33 个科学 Skill:为什么「代码配方」比「JSON schema」更可扩展

Skills 是 OpenAI4S 的能力扩展点,跟 Claude 的「工具」完全不是一回事:

```
skills/alphafold2/
    SKILL.md      # recipe-centric doc (代码示例,不是 JSON schema)
    kernel.py     # 可 import 的 sidecar 模块
```

设计原则只有一条:**Skill 的能力以「可调用 Python」的形式落到 kernel 里**,不是又一组 JSON schema。

loader 用 progressive disclosure:模型先只看到一行摘要,真要用的时候才 `host.search_skills(query)` 把完整 `SKILL.md` 拉下来。kernel 自动把 `skills/` 加进 `sys.path`,于是 `from alphafold2.kernel import predict` 就能用。

33 个内置 Skill 分成 4 大类:

| 类别 | 代表 Skills |
|---|---|
| **结构预测**(GPU) | AlphaFold2 · OpenFold3 · Boltz · Chai-1 · ESMFold2 |
| **序列/组学/分子对接**(GPU) | ESM-2 · Evo2 · Borzoi · scGPT · scVI-tools · DiffDock |
| **蛋白质设计**(GPU) | ProteinMPNN · LigandMPNN · SolubleMPNN |
| **科研工作流** | literature-review · pdf-explore · paper-narrative · indication-dossier · retrosynthesis_planning |

GPU 重的 Skill 走 `host.compute` 派到远程 BYOC(下面单独讲);轻量的直接在本地 kernel 里跑。

用户写的 Skill 落在 `<data_dir>/user-skills`,可以编辑、可以回滚——`SkillVersionService` 用 SHA-256 内容寻址存每一次 `SKILL.md` + `kernel.py` 的字节快照,append-only 安装事件,compare-and-swap 切活跃版本。**但有一个硬约束:bundled Skill 是只读的,user Skill 不允许 shadow 同名 bundled Skill。** 这一条来自 `openai4s/skills_loader/loader.py`,你不用读源码,直接看 README 里那段就知道作者的防御态度。

`kernel.py` 在 publish 之前必须通过 compile gate;坏掉的 sidecar 只能留作 `draft`,不能发布。

---

## 四、账本优先(ledger-first):把所有动作都做成 append-only

整个架构里最容易被忽视的部分叫 **Action Ledger**。

Agent 的所有动作——JSON tool call、Python Cell 尝试、Kernel 生命周期、用量、完成记录——都以**追加**方式写进 SQLite。一行真实 ledger 长这样:

```sql
-- schema_migrations
version=12, name='add_branch_checkpoint_sidecar', checksum='9f3a…', applied_at='2026-08-01 10:23:11'

-- action_groups(按 conversation_id 顺序分配)
frame_id=42, group_id=42, kind='cell_python', language='python',
  code='import scanpy as sc; ...', generation_id=7, kernel_env='rna-py3.11',
  opened_at='2026-08-01 10:23:14', closed_at='2026-08-01 10:23:51',
  status='succeeded', wall_ms=37_104, peak_rss_kb=812_440

-- attempt_milestones
frame_id=42, milestone='pre_exec_safety', result='pass', classifier='heuristic', ts='10:23:14'
frame_id=42, milestone='kernel_spawn',     result='ok',    worker_pid=19342, ts='10:23:15'
frame_id=42, milestone='host_call',        result='ok',    method='science.search', ts='10:23:18'
frame_id=42, milestone='artifact_committed', result='ok', version_id='v_ab12…', ts='10:23:50'
frame_id=42, milestone='submit_output',    result='ok',    payload_sha='e7c1…', ts='10:23:51'

-- terminal completion_record
frame_id=42, kind='final', completion_kind='submit_output', hash_chain_prev='8d2a…'
```

每一行都是 append;attempt 字段就地更新;cell 关闭后写终态。`Store`(`openai4s/store.py`)是这个数据库的唯一所有者,一个连接、一个锁、一组迁移。`PRAGMA user_version` + `schema_migrations(version, name, checksum, applied_at)` 走单事务升级,**要么完全在版本 N,要么完全在版本 N-1,中间状态不存在**。

为什么这么较真?

因为架构文档里写了一段很朴素的话:

> This keeps terminal states, history ordering, provider replay, and action priority testable without starting infrastructure.

翻译过来:**你不需要启动内核就能验证终态、不需要重建服务器就能 replay 历史**。这跟 ReAct 那种「全靠聊天记录回放」不是一个物种。

具体怎么落:

- **执行尝试和 generation 生命周期** 可以**就地更新**(`UPDATE`),因为它们是「同一个对象的字段变更」。
- **provider 声明、canonical 工具结果、终止事件** 只追加,从不改写。
- 一个 action group 在执行前打开,工具结果和 Cell 尝试里程碑**规范化地**关闭它。

终态是 append 出来的,不是从 UI transcript 反推的。这一条决定了:你重启 daemon、换 provider、回放历史,**结构不会糊**。

`Storage` 模块的代码所有权被严格切分:frame、artifact、attempt、kernel generation、approval、capability state、snapshot、branch、recovery、metadata/settings、plan/review、connector、memory,每个 repository 各管一摊,不重复 SQL。架构文档里专门列了一张表划清边界——`agent/` 管外层循环,`tools/` 管 JSON schema,`host_dispatch.py` 管权限审批审计,`host/` 管能力实现,`sdk/` 管 worker-facing `host.*` API,**每一层都不吞下层的活**。

---

## 五、host 单例:从 Python Cell 内部能调什么

`openai4s/sdk/host.py` 是 Python kernel 启动时注入的「host 单例」。它把几乎所有外部能力都暴露成一组方法调用:

```python
host.web_search(...)   host.web_fetch(...)   host.web_download(...)
host.read_file / write_file / edit_file / grep / glob / list_dir
host.llm(...)          host.delegate(...)    host.collect(...)
host.science.list_databases(...) / search(...)
host.compute.create(...).submit_job(...)
host.save_artifact(...) host.artifacts(...) host.view_image(...)
host.skills.*  host.env.use(...)  host.mcp.call(...)  host.query(...)
host.submit_output(...)      # 科学 Cell 完成的唯一信号
```

每个调用都走 `HostDispatcher` 这一层统一的策略封装:**权限审批、审计回放、注入检测、活动事件**。Cell 不可能绕过这层。

Cell 调用 LLM 时是**同步阻塞**的——`host.llm("解释这一列")` 会让 Cell 暂停,等模型返回,Cell 继续。这就是内层 RPC 的运行时表现。

**`host.bash` 的设计是这套安全模型的样板**:Cell 想要 shell,必须先申请一个短生命周期、与当前 worker generation 绑定的 token,Host 验证命令 hash + canonical cwd + 挑战码后才授权一次;worker 验证一次后启动 subprocess,Host 永远不执行 shell。审计里只有命令 hash 和 redacted 结果,没有完整命令字符串。过期、重用、错 generation 全部 fail closed。

`host.query` 是另一个有意思的设计:它让 Agent 通过只读 SQL 视图**自查自己的 SQLite**——但 `settings`、`connectors`、`memories`、`host_call_log`、原始 ledger、permission 规则等敏感表全部 denylist。`host.query.schema()` 也隐藏同一组表,避免「我先看 schema 再拼 SQL」绕路。

---

## 六、安全模型:七层防御,每层独立

`docs/security.md` 写了一长串防御层,有几个值得拎出来:

| 层 | 默认 | 干什么 |
|---|---|---|
| **OS 内核沙箱** | `auto` | macOS Seatbelt / Linux bubblewrap 启动时**真的自检**一次;失败就显示「degraded」,不是默默放行 |
| **子进程环境 allowlist** | always on | daemon 的 LLM/API/cloud secret 不会被子进程继承——子环境按白名单重建 |
| **Pre-exec 分类器** | `heuristic` | 每个 Agent 写的 Python/R Cell 都要过一道「能不能跑」;但**用户 REPL Cell** 跳过分类器,仍然进沙箱 |
| **dlopen 审计钩子** | on | `sys.addaudithook` 拒绝从 agent-writable 路径 `.so` 加载 |
| **生物安全筛选器** | on | 蛋白质相关内容的轨迹级 ALLOW / ESCALATE / BLOCK |
| **注入检测** | on | 把 tool 返回的内容标注为「数据,不是指令」 |
| **Egress allowlist** | `off` | 应用层 `web_fetch` / `web_search` 的出网策略;OS 沙箱是另一道原始网络边界 |

Seatbelt 在 macOS 上细节特别足:`xattr` 在 macOS 上经常把文件自己的字节放在扩展属性里,所以光 deny `file-read-data` 不够,必须**同时 deny `file-read-xattr`**——这一条作者在 `security/byoc_confinement.py` 注释里专门写了,是个真实的踩坑。

持久审批的语义也很讲究:

> A durable card is not a replay token. While the daemon is still running, a decision wakes the exact blocked call. After a daemon restart that thread is gone: approving the surviving card records that the old operation **did not execute**, appends an argument-free `permission_resolution` marker to the Action Ledger, and returns `requires_continue=true`.

意思是:**重启之后的审批不能 replay 老参数**——它必须先 append 一条「老动作没执行」的账本记录,然后告诉前端「请重新发起」。`once` 授权精确到 `root_frame_id + tool + permission-target`,15 分钟过期,原子消费一次。审计和执行不是同一回事,作者把这层分得很清。

`secrets` 的处理是另一个样板:Agent 通过 `host.credentials.set(name, value)` 存的凭据**永远不进持久层**,只在内存 vault 里;RPC audit log **redact** 整个 args;replay tape 也跳过 `credentials_set`——导出的 notebook 里不会有明文凭据。

---

## 七、多 Provider:一行切换,纯 stdlib 客户端

`openai4s/llm/` 实现了四种 wire:OpenAI Chat / OpenAI Responses / Anthropic Messages / Gemini `generateContent`。传输层用 `urllib`,**不依赖 openai/anthropic SDK**。

provider 注册表是「**profile + endpoint identity**」的组合,不写硬路由分支:

- `ark`(火山方舟兼容协议):豆包 / GLM / Kimi / DeepSeek / MiniMax
- `chatgpt`(OpenAI 兼容)
- `claude`(Anthropic 兼容)
- `gemini`

UI 里加一个 endpoint 只需要在 catalog 里写一条记录,**不用碰 router 逻辑**。真要换 wire(比如 Anothropic 推了一种新的 content block 格式),还是要单独写 adapter,但代价已经被收敛到一个文件。

---

## 八、BYOC 远程 GPU:`byoc:nvidia` + SSH + 不自动重提

科研任务经常要 8×A100-80GB 这种本地没有的算力。OpenAI4S 的方案:

1. **SSH**:`ssh:<alias>`,在你已有的机器上跑
2. **BYOC**:`byoc:<id>`,从 `skills/remote-compute-<id>/` 发现 provider
3. **NVIDIA NIM**(内置):用 docker CLI(不引 SDK)拉 `nvcr.io/nim/*` 镜像,两种模式
   - `self_hosted`:本机有 GPU,跑本地 container
   - `hosted`:无 GPU,过 `integrate.api.nvidia.com` 网关

任务生命周期是 `create → submit_job → poll result()`,**没有后台轮询器**——你不 poll 它就不会 harvest。

关键的鲁棒性设计:

- **行在前,submit 在后**:job 在 SQLite 里**先写一行,再尝试 submit**——provider 收了活但响应丢了,你还有账本
- **不自动重提**:一个 `submitted` 状态可能真跑了也可能没跑,瞎猜会重复收费或丢结果;reconcile 把 receipt(sandbox id / pid)报回来,让人工决定
- **`idempotency_key`**:同一逻辑任务带同一个 key,二次 submit 返回 `duplicate_request` 而不是开新任务——这个 key 重启后还在
- **outputs 是契约不是 hint**:声明的 `outputs` glob 啥都没匹配,即使 exit code 0 也是 `failed`,reason `outputs_unverified`

`host.fold` 是个特例——单序列 Protenix(AlphaFold3 级别)推理,**严格 no-fabrication policy**:没有 GPU host 就 refuse and error,**绝不编一个结构**。ESM masked-marginal 变体打分走 `host.score_mutations`,同样不伪造。

---

## 九、Notebook 默认只读:REPL 是显式开启的 dev flag

Web 应用的右栏 Notebook **默认是只读执行 trace**——你能看到 Cell 的源码、stdout、stderr、figures,但你**不能往里写代码**。

要打开交互 REPL,必须设 `OPENAI4S_NOTEBOOK_REPL=1`。打开之后:

- Shift+Enter append 新 Cell,**永不修改已执行的 Cell**
- 用户 Cell 和 Agent 走同一个 FIFO execution coordinator(同一套执行语义,不是另起一套)
- Stop 控制只能停 `user_repl` 的 ticket,**不会**回退去打断 Agent——fail closed
- `execution_id + owner.kind + owner.id` 三元组定位中断目标,session-level SIGINT 直接拒绝

`agent/*` / `kernel/*` 这套协议是**线程敏感+死锁敏感**的:`worker.py` 持有 `_HOST_CALL_LOCK` 包裹整次 `host_call` 请求/响应事务(一次只能一个 RPC in flight),stdout 写入串行化;`manager.py` 每次重启 bump `generation` ID。CLAUDE.md 里专门警告:**碰 kernel/manager 协议时,保持单帧读取循环、id 路由 `host_response`、事务锁——然后重跑 `tests/test_kernel.py`**。

---

## 十、Artifact 版本化与 Branch/Revert

每一个 `writes_files=True` 的原生工具调用,被 Web 适配器包成 per-call workspace transaction——写/改操作 diff 之后立刻注册成**新版本 Artifact**。

复现性(provenance)的来源不是 daemon 进程,而是 **kernel generation**——`ArtifactManager.capture_environment` 查生成该 Artifact 的 frame + language 的 generation,记录运行时、解释器、conda env 名和 `generation_id`。这条在 CLAUDE.md 里被专门吐槽过:之前的实现是「零参数从 daemon 进程冻结一个 `kind: 'python'` 的快照」——结果 R Cell 的 Artifact 居然带着 Python 包列表。**作者把这种「错的来源」定性为「比没有来源更糟,因为它会被相信」。**

`kernel/provenance.py` 做的是对象级数据血缘,跑在 worker 内部——给从 artifact 读的对象贴上 source `version_id`,通过索引/slicing/`json.loads`/标量运算传播,write 时上报 `lineage_edges`(输入版本 → 输出版本)。

Branch/Checkpoint 是这套架构的**最复杂的一片**——内容寻址快照 + durable Cell/用户消息的 cursor checkpoint。**关键不变量**:只有带「proven checkpoint mapping」的记录才显示 Fork 按钮;老历史 fork 直接返回 409。Fork 失败时会显式声明 `Partial` 或 `Failed`,**绝不假装任意内存都恢复了**。

Recover Journal 走 v2 bootstrap,捕获 worker 的完整包集、locale、interpreter prefix、SDK/provenance/Host 协议版本。**loaded Skill sidecar 的字节/哈希永不进入普通 Cell 输出**——避免凭据和 bundle 字节泄露。

---

## 十一、测试纪律:离线 suite + 多 job gate + marker 政策

CLAUDE.md 上来就钉了一条:**`uv run pytest` 不是全部 gate**。CI 跑下面这些独立 job,任何一项失败都算挂:

```bash
uv run python scripts/check_directory_readmes.py            # 双语 README 覆盖率
uv run python -m harness.cli run --tier pr --offline        # 确定性场景契约
uv run python scripts/capture_response_schemas.py --check   # 冻结的 response shape 还匹配
uv run python scripts/capture_response_contract.py --check  # 每个可路由 route 都有契约
python scripts/source_secret_scan.py                        # release 源码里没有凭据字面量
node tests/browser_smoke.mjs                                # workbench E2E,需要 daemon 在 :8760
node tests/browser_admission_fault.mjs                      # 注释驱动的 admission 能在丢响应时存活
node tests/browser_matrix.mjs --browser=firefox             # 跨引擎 breadth
```

`pyproject.toml` 里有 `--strict-markers` + deselect `external/network/live_llm/gpu/ssh/lab/docker/browser`——任何要真资源的测试**必须**带相应 marker;未注册的 marker 直接报错不是跳过。**stub 服务的测试必须标 `stubbed_backend`**——否则 `capture_response_schemas.py` 会把 stub 编造的 shape 当真契约发出去。

测试 offline 模式强制:`tests/conftest.py` 把 `~/.openai4s` 重定向到 tmp,塞假 `deepseek` provider,pin `OPENAI4S_UNATTENDED_APPROVAL=deny`、`OPENAI4S_SECRET_STORE=plaintext`、loopback telemetry 端点、清空 share 变量。**新加测试不要默认要 LLM/网络**。

---

## 十二、人:谁在维护它

`.github/CODEOWNERS` 写得明明白白:

- **Lead + Security**:`@Nobody-Zhang`
- **Runtime + Platform**:`@riiiiiiin`
- **Web**:`@difficulttopickaname`
- **Science**:`@Lyu6PosHao` `@wangyu-sd`

安全敏感路径(`/openai4s/security/`、`permissions.py`、`egress.py`)全部由 `@Nobody-Zhang` 一人 review。运行时核心(agent / execution / host / kernel / sdk / storage / tools / host_dispatch.py / store.py / llm/)由 lead + runtime 双 owner。

CONTRIBUTING 还要求:**保持核心零依赖**;可选的科学 import 全部 `try/except ImportError` 包起来;新加 Skill 只能放在 `skills/` 下;PR 前 `uv run pytest` + `uv run pre-commit run --all-files` 必须全过。

---

## 十三、它对科研 Agent 意味着什么

先把账算清楚。同样跑一次「UniProt → AlphaFold 预测 → 突变打分」完整流程,假设每次需要 8×A100-80GB 跑 20 分钟:

| 维度 | Claude Science(闭源) | OpenAI4S + 豆包 |
|---|---|---|
| 模型订阅 | $200/月(Pro 估算) | **¥9.9/月**(约 $1.4) |
| GPU 算力 | 已含在订阅里 | BYOC 自带或租,按用量 |
| 一周重度使用 | $200 + GPU 弹性费用 | ¥9.9 + GPU 弹性费用(同价) |
| 单价差 | 1× | **~140×** |
| 离线跑 | 需联网验证 license | `.dmg` 离线跑,不烧 token |
| Fork / Replay | 无 | Action Ledger 全量 |
| 自托管 Skills | 仅官方支持 | `personal` + `project` 两档,带版本回滚 |

9 块 9 不是噱头,是**算力之外的所有成本**——对一个跑几百次探索性实验的研究生,这个差额意味着「实验失败也能再来」。

OpenAI4S 真正做到的,是把 Agent 的每一次输出**写进可重建、可验证、可分发的资产**——每一份 artifact 带 provenance,每一条 ledger 可 replay,每一次 fork 走 CAS 验证。这是 ReAct 那种「聊天记录即历史」做不到的。

这条赛道的下一站很清楚:**Claude Science 不会永远闭源**——OpenAI4S 的存在至少证明了一件事:它的核心架构没有不可复制的部分。当一个 9 块 9 的开源复刻能完整复现闭源架构,定价权就不再属于任何一家实验室。

至于它能不能成为「科研 Agent 的 Linux」——这个问题可能要等 2027 年再回看。

---

## 附录:快速跑起来

```bash
git clone https://github.com/PKU-YuanGroup/OpenAI4S && cd OpenAI4S
./setup.sh     # 用 uv 建环境
./start.sh     # 启动 Web UI at http://127.0.0.1:8760/
```

或者直接下载 macOS `.dmg`(Apple Silicon)/ Linux `.tar.gz` / Windows WSL2 安装包,内嵌 Python + 科学栈,首次启动不联网不 `pip`。

打开 UI 后:

1. **设置 ⚙ → 模型**:选 `ark`(豆包/GLM/Kimi/DeepSeek/MiniMax)或 OpenAI/Anthropic 兼容协议,粘 API Key,设为当前
2. **设置 ⚙ → 网络**(可选):到 [tavily.com](https://tavily.com) 注册,粘进「搜索 API Key(Tavily)」——不填也跑,只是搜索退回到免密钥抓取

不启动 UI 单跑:`uv run openai4s run "Compute the mean of [4,8,15,16,23,42] and submit it." -v`。

---

## 参考

- 仓库:[github.com/PKU-YuanGroup/OpenAI4S](https://github.com/PKU-YuanGroup/OpenAI4S)
- 文档站:[openai4s.org/docs](https://openai4s.org/docs/)
- 协议基础:CodeAct(Executable Code Actions Elicit Better LLM Agents)、ReAct(Synergizing Reasoning and Acting in Language Models)
- 复刻对象:Claude Science(Anthropic)
- 科学 Skill 底座:ColabFold / AlphaFold、ESM、OpenFold、Boltz、Chai、ProteinMPNN、DiffDock、Evo2、Borzoi、scGPT、scVI-tools
- 数据源:NCBI、UniProt、RCSB PDB、EBI、OpenAlex、Crossref