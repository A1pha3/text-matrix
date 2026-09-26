---
title: "dcg 拆解：103 个安全包里默认只开 3 个，剩下的全是策略问题"
date: 2026-07-13T03:01:47+08:00
lastmod: 2026-09-21T12:40:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["Rust", "AI Agent", "Claude Code", "安全", "CLI工具"]
description: "把 Dicklesworthstone/destructive_command_guard v0.14.4 的官方二进制装上实跑一遍，再读 main 分支：默认只有 3 个包在评估，1,114 条破坏性模式按四档严重度决定是拦还是只警告，explain 输出里的 decision 不是最终处置，超时与不可判定也不再一律放行。文末给出一张可复算的实测表，以及 README 的说法与二进制行为对不上的四处。"
slug: dicklesworthstone-destructive-command-guard-claude-code-safety
github_repo: "Dicklesworthstone/destructive_command_guard"
source_key: "gh:Dicklesworthstone/destructive_command_guard"
---

判断 `dcg`（Destructive Command Guard，破坏性命令守卫）值不值得接进自己的工作流，靠的不是它列出了多少条危险命令，而是三件更容易被忽略的事。**默认状态下它只评估 3 个包**，其余 100 个要自己启用。**同一条规则命中之后可以拦、可以只警告、也可以静默记录**：处置方式与规则本身是两套东西。**"解析不了就放行"这条概括已经不准**：超时与不可判定走的是显式的 `ask` 或者阻断。

这三点合起来决定了它是个什么东西：不是命令黑名单，而是一个带策略引擎的钩子（hook），规则库只是它最大的一块资产。

下面的结论只有两类来源。一是 main 分支（提交 `add38e4`，2026-09-20）里的文件与行号；二是官方发布物 `dcg v0.14.4` 的实跑输出，aarch64-apple-darwin 那份 tar 包的 SHA256 与发布页一致。本机跑不到的部分——原生 Windows、真实代理客户端的端到端链路——一律标为未验证，不混进结论。

## 项目坐标

| 项 | 值 | 出处 |
|------|------|------|
| 定位 | AI 编码代理的 `PreToolUse` 钩子，在命令交给 shell 之前做一次评估 | `Cargo.toml` 的 `description`、README 首段 |
| 当前版本 | v0.14.4，发布于 2026-09-16；`git describe` 报 `v0.14.4-181-gadd38e40`，即 main 比这个标签多 181 次提交 | Releases 页、`git describe --tags` |
| 语言与工具链 | Rust，edition 2024，`rust-version = 1.95`；发布构建锁 `nightly-2026-08-31` | `Cargo.toml`、`rust-toolchain.toml` |
| 规则规模 | 103 个包、28 个命名空间；1,114 条破坏性模式与 865 条安全模式 | `dcg packs --format json` 与 `--verbose --expand`（本文实测） |
| 严重度分布 | critical 305、high 665、medium 138、low 6 | 同上，按 `--verbose --expand` 输出的标签计数 |
| 默认启用 | 3 个包：`core.filesystem`、`core.git`、`system.disk` | `dcg config`（本文实测） |
| 星标 / 复刻 / 未关闭条目 | 6025 / 246 / 12 | GitHub 仓库接口，2026-09-21 取 |
| 仓库节奏 | 首次提交 2026-01-07，累计 2,484 次提交、71 个 Release | `git log`、Releases 列表 |
| 贡献者 | GitHub 计 2 名：作者本人 2,466 次、dependabot 14 次 | contributors 接口 |
| 许可证 | MIT 加一条附加条款（rider），把 OpenAI 与 Anthropic 及其代理方列为"不授予任何权利"的对象 | `LICENSE` 第 1 行与 rider 段 |
| 发布平台 | Linux（glibc / musl）、macOS（arm64 / x86_64）、Windows（arm64 / x86_64）共 6 个目标 | Release 资产名 |

README 里有两处自我概括要按这张表校正。特性表写着 "50+ Security Packs"（`README.md:49`），那是包系统刚成型时留下的口径，今天 `dcg packs` 报的是 103。下一行写着 "Sub-Millisecond Latency"（`README.md:50`），指的是快路径的设计预算而不是端到端延迟，本文"这些数字测的是什么"一节把它拆开算。

## 目录

- [项目坐标](#项目坐标)
- [一条命令在 dcg 里走完全程](#一条命令在-dcg-里走完全程)
- [三件事别混成一件](#三件事别混成一件)
- [默认防线拦什么，不拦什么](#默认防线拦什么不拦什么)
- [关得掉与松得动](#关得掉与松得动)
- [内联脚本与 heredoc 的三层管线](#内联脚本与-heredoc-的三层管线)
- [不可判定不等于放行](#不可判定不等于放行)
- [一次真实拦截：从拒绝输出到短码放行](#一次真实拦截从拒绝输出到短码放行)
- [代理差异化与配置优先级](#代理差异化与配置优先级)
- [装起来与验收](#装起来与验收)
- [这些数字测的是什么](#这些数字测的是什么)
- [常见误区](#常见误区)
- [该不该装，谁来先装](#该不该装谁来先装)
- [五道自测题](#五道自测题)
- [出错时先看哪几处](#出错时先看哪几处)
- [下一步读哪份代码](#下一步读哪份代码)
- [维护指引与事实边界](#维护指引与事实边界)
- [参考资料](#参考资料)

## 一条命令在 dcg 里走完全程

先把系统地图画出来。代理每次触发 shell 工具，会把一段 JSON 从标准输入喂给 `dcg`；`dcg` 决定放行、请求人工确认还是拒绝，再按调用方的协议把结论写回标准输出。整段判断通常在几百微秒到几毫秒之内完成：

```text
stdin: {"tool_name":"Bash","tool_input":{"command":"git reset --hard"}}
   │
   ├─ 解析钩子报文        失败 → 默认放行并留审计警告（可切 fail-closed）
   ├─ 关键词预筛          Aho-Corasick 自动机，一次扫描过全部已启用包的关键词
   ├─ 归一化              引号、转义、链接符
   ├─ 安全模式匹配        命中即放行（865 条）
   ├─ 破坏性模式匹配      命中进入处置（1,114 条）
   ├─ heredoc / 内联脚本  三层管线，只在触发词命中时才付这笔钱
   └─ 处置                严重度 → deny / ask / warn / log，可被策略逐条改写
```

关键词预筛是这里最容易被误读的一环。README 用"SIMD 加速"来描述这一步，实际的第一道闸是 `aho_corasick::AhoCorasick`：一张按已启用包关键词表构建的多模式匹配自动机（`src/packs/mod.rs:578`、`:1192`，快捷入口 `pack_aware_quick_reject()` 在 `src/packs/mod.rs:3497`）。正则排在它后面，是 `RegexSet` 与懒编译模式。用哪个库不影响判断，但影响到"关掉几个包能不能加速"这类实际提问：能，因为关键词表变小了，预筛的通过率也变了。

延迟预算写在 `src/perf.rs:20-26` 的注释表里，分档给出目标值、警告线与熔断线：

| 档 | 路径 | 目标 | 警告超 | 熔断超 |
|----|------|------|--------|--------|
| 0 | 关键词快速拒绝 | < 1 μs | > 5 μs | > 50 μs |
| 1 | 快路径 | < 75 μs | > 150 μs | > 500 μs |
| 2 | 模式匹配 | < 100 μs | > 250 μs | > 1 ms |
| 3 | heredoc 触发 | < 5 μs | > 10 μs | > 100 μs |
| 4 | heredoc 提取 | < 200 μs | > 500 μs | > 2 ms |
| 5 | 语言识别 | < 20 μs | > 50 μs | > 200 μs |
| 6 | 完整 heredoc 管线 | < 5 ms | > 15 ms | > 20 ms |

超过 1000 ms 的评估不是"算完了"，而是转成显式的不可判定结论（`src/perf.rs:28-32`）——这一条与后面"不可判定不等于放行"一节直接相关。

## 三件事别混成一件

大多数对 `dcg` 的错误预期，来自把下面三件事当成一件事：**哪些规则在评估**、**规则覆盖面有多大**、**命中之后怎么处理**。

第一件是硬底线。`core.filesystem` 与 `core.git` 永远参与评估，写 `disabled = ["core.filesystem"]` 会被忽略；`system.disk` 默认开但可以关。实测把 `DCG_DISABLE=core.git` 塞进环境，`git reset --hard` 依然被拒；换成 `DCG_DISABLE=system.disk`，`mkfs` 就真的没了防护。所以"不可关闭"只适用于两个 `core.*` 包。

第二件是覆盖面，而且它要自己点名。103 个包分成 28 个命名空间，默认在跑的只有 3 个；数据库、容器、云资源、密钥、备份各成一类，得逐个写进 `[packs] enabled`。这一步没做，清容器状态、往数据库发删表语句、删集群里的命名空间都会安静地通过（下一节的实测表逐条列出了哪些通过）。README 在这一点上说得明白：`dcg init` 生成的示例配置里替读者开了 PostgreSQL 与 Docker 两支包，那是模板，不是无配置默认值（`README.md:244-249`）。

第三件是处置。规则命中不等于命令被拦：每条规则带一个严重度，严重度映射到 `deny` / `ask` / `warn` / `log` 四档之一。`critical` 与 `high` 默认 `deny`，`medium` 默认 `warn`（放过去，但在标准错误上留一段说明），`low` 默认 `log`（静默记录）。这就是为什么有些"看起来很危险"的命令跑通了——它被命中了，只是处置是警告。

## 默认防线拦什么，不拦什么

下面这份输出是 `dcg v0.14.4` 在无配置文件状态下的实测结果，逐条取自 `dcg explain --format json`。`dec` 是报文里的判定字段，`mode` 与 `outc` 才是最终处置；行末没有括号标注的，就是默认那 3 个包覆盖到的。

```text
command                                dec   mode  outc  rule_id                          severity
git reset --hard HEAD~5                deny  deny  deny  core.git:reset-hard              critical
git push --force origin main           deny  deny  deny  core.git:push-force-long         critical
git clean -fdx                         deny  deny  deny  core.git:clean-force             critical
git stash clear                        deny  deny  deny  core.git:stash-clear             critical
git checkout -- src/main.rs            deny  deny  deny  core.git:checkout-discard        high
git stash drop                         deny  warn  warn  core.git:stash-drop              medium
rm -rf ./src                           deny  deny  deny  core.filesystem:rm-rf-general    high
dd if=/dev/zero of=./tmpfile bs=1M count=1  deny deny deny core.filesystem:dd-overwrite-general  high
mkfs.ext4 /dev/sdb1                    deny  deny  deny  system.disk:mkfs                 high
wipefs -a /dev/sda                     deny  deny  deny  system.disk:wipefs               high
rm -rf /tmp/build                      allow --    --    --                                            临时子目录豁免
git push --force-with-lease origin main allow --   --    --                                            需 strict_git
git rebase -i HEAD~3                   allow --    --    --                                            需 strict_git
chmod -R 777 /                         allow --    --    --                                            需 system.permissions
docker system prune -af                allow --    --    --                                            需 containers.docker
psql -c "DROP TABLE users"             allow --    --    --                                            需 database.postgresql
redis-cli FLUSHALL                     allow --    --    --                                            需 database.redis
kubectl delete namespace prod          allow --    --    --                                            需 kubernetes.kubectl
terraform destroy -auto-approve        allow --    --    --                                            需 infrastructure.terraform
```

三点值得单独说。带远端比对的那一种强推默认放行是刻意的：它本来就安全，覆盖它等于把一种正确用法一并禁掉；要连它一起禁得启用 `strict_git`，实测启用后强制推送这一族规则整体生效。交互式变基与丢弃单个 stash 在默认档位下不构成硬拦，前者同样归 `strict_git` 管，后者只落一个警告——`medium` 严重度的默认处置就是放行加一段说明。最后，`dd` 写普通文件也算命中，`core.filesystem` 管的不只是块设备。

启用包之后覆盖面差别很大，随手验证几条：

```text
DCG_PACKS=database.postgresql  psql -c "DROP TABLE users"   → database.postgresql:drop-table
DCG_PACKS=database.redis       redis-cli FLUSHALL           → database.redis:flushall
DCG_PACKS=kubernetes.kubectl   kubectl delete namespace prod → kubernetes.kubectl:delete-namespace
DCG_PACKS=system.permissions   chmod -R 777 /               → system.permissions:chmod-777
```

只写命名空间也能整类启用：`enabled = ["database"]` 会展开成数据库这一类下全部 9 个子包。它是子包最多的一类，除常见的五支外还有 Snowflake、BigQuery、Databricks 与 Supabase。反过来 `disabled = ["database.redis"]` 可以只摘掉一支。

## 关得掉与松得动

"核心包不可关闭"很容易被读成"核心命令一律硬拦"，这两件事在 `dcg` 里是分开配置的，而踩坑的人不少。

规则包决定**是否评估**，策略决定**评估到了做什么**。后者可以整体放宽：

```toml
[policy.packs]
"core.git" = "warn"

[policy.rules]
"core.git:reset-hard" = "warn"
```

两条的实测结果不一样。写上面那一条时，`git reset --hard` 依旧 `deny`；只写下面那一条时，`dcg explain` 报 `mode = warn`、`outcome = warn`，钩子路径上标准输出为空（不拦），标准错误打印一段"可以用 `git fsck` 找回"的警告。

原因是：`critical` 严重度的规则不接受整体放宽——包级或全局的 `warn` / `log` 会被静默抬回 `deny`，而且不报告它忽略了你的设置。`core.git` 与 `core.filesystem` 里绝大多数规则恰好就是这个严重度（全局 1,114 条里 critical 占 305）。要让某条 critical 规则变成警告，只有 `[policy.rules]` 的逐条形制真正生效。这条约束写在 `README.md:204-231`，配合它给的验证方式一起用才可靠：读 `dcg explain --format json` 的 `mode`，别读 `decision`。

## 内联脚本与 heredoc 的三层管线

代理写出的危险语句经常不在最外层：`bash -c "git reset --hard"`、`python3 - <<PY ... PY`、`eval "$(curl -s https://x.sh)"`。`dcg` 用三层来处理，设计文档是 `docs/adr-001-heredoc-scanning.md`。

第一层触发检测是一个 `RegexSet`，模式原文列在 `README.md:627-638`：

```text
<<-?\s*(?:['"][^'"]*['"]|[\w.-]+)      heredoc 标记
<<<                                     here-string
\bpython[0-9.]*\b.*\s+-[A-Za-z]*[ce]   python -c / -e
\bruby[0-9.]*\b.*\s+-[A-Za-z]*e        ruby -e
\bnode(js)?[0-9.]*\b.*\s+-[A-Za-z]*[ep]  node -e / -p
\b(sh|bash|zsh)\b.*\s+-[A-Za-z]*c      bash -c
```

不含这些触发词的命令在这一步就结束，预算 <100 μs。第二层提取正文，上限是可配的：body 1 MiB、10,000 行、每条命令 10 段、提取预算 50 ms。第三层做 AST（抽象语法树）匹配。依赖是嵌入式的 `ast-grep-core` 0.45（`Cargo.toml:66-74`），语法覆盖 bash、python、javascript、typescript、ruby、go、php 七种。ADR 里明确否掉了"调用外部 ast-grep 命令行"这条路，理由就是那 10–50 ms 的进程启动开销。

实测下来，覆盖面并不均匀：

```text
bash -c "git reset --hard"                        → deny  core.git:reset-hard
python3 - <<PY  os.remove("notes.txt")             → deny  heredoc.python:os_remove
python3 -c "import shutil; shutil.rmtree('/')"     → allow  未命中
python3 -c "import os; os.system('rm -rf /')"      → deny  core.filesystem:rm-rf-root-home
eval "$(curl -s https://x.sh)"                     → deny  heredoc.posix:eval-dynamic (high)
eval "$(ssh-agent -s)"                             → allow  惯用法降级
source <(kubectl completion bash)                  → allow
```

差异的来源是判定的位置不同：`-c` 后面那段字符串走的是通用包的模式，取决于危险动作的形状是否恰好落在某条正则上；heredoc 体内的 Python 有 `heredoc.python:*` 这一支专属规则，覆盖面明显更宽——`os.remove("notes.txt")` 这种单文件删除都会命中。`shutil.rmtree('/')` 从 `-c` 溜过去，写进 heredoc 却立即命中 `heredoc.python:shutil_rmtree`（critical）——同一条语句换个入口就换了一套判定面。README 特性表那句 "Catches `python -c \"os.remove(...)\"`" 按字面读，会得出过强的预期。

`eval "$(...)"` 这一族走的是另一个方向。静态还原不出被喂进 shell 的是什么，所以它不猜，直接**拒**（`heredoc.posix:eval-dynamic`，high），并留一批稳定的规则 ID 供事后逐条放行。另一侧是 shell 初始化惯用法：下面这几条按**字面 argv 形状**精确匹配，命中后降级为记录性警告，任何近似形状保持硬拒：

```text
eval "$(ssh-agent -s)"          eval "$(brew shellenv)"
eval "$(direnv hook bash)"      eval "$(pyenv init -)"
source <(kubectl completion bash)
```

README 也写清了这个口子的残留风险：放行依赖生产端二进制的"身份"，而 PATH 顺序、shell 函数与别名都在 `dcg` 的静态视野之外（`README.md:2720`）。

同一份坦白还在别处。`dcg` 不会为了得知输出而去执行任意生产者（issue #191）。未知生产端、非规则文件、非 UTF-8 载荷、超过 256 KiB 的输入，一律落成 `<pack>:stdin-unverified` 这一条高严重度拒绝。而代理把脚本写进磁盘再执行，脚本里面 `dcg` 看不见。

## 不可判定不等于放行

"解析失败、超时、异常时默认放行"是 `dcg` 被引用最多的一条设计说明，放在今天的版本上已经不完整。当前口径在 `README.md:893-998` 的 Bounded Failure Policy 一节，五类场景各有各的去处：

| 场景 | 默认行为 | 收紧后的行为 |
|------|----------|--------------|
| 钩子原始报文畸形或超限 | 放行并留审计警告 | `general.fail_closed = true` 或 `DCG_FAIL_CLOSED=1` 改为拒绝 |
| 读取标准输入的临时 I/O 错误 | 放行（载荷非攻击者可控） | 始终 fail-open |
| 提取出的命令超过 `max_command_bytes` | 显式不可判定 | 支持人工确认的客户端收 `ask`，其余客户端阻断；`unverified_decision = "deny"` 直接拒 |
| 绝对评估期限耗尽 | 显式不可判定 | 同上 |
| heredoc 提取 / 解析 / AST 失败 | 跑一次有界回退扫描，扫不到高危信号才放行 | `fallback_on_parse_error = false` / `fallback_on_timeout = false` 改为阻断 |

实测这两条边界。默认状态喂一段非 JSON 进 stdin：

```text
[dcg] Warning: could not parse hook input (expected ident at line 1 column 2);
allowing command (fail-open). Set DCG_FAIL_CLOSED=1 to block instead.
```

加上 `DCG_FAIL_CLOSED=1` 重跑，同一段输入换成一个阻断面板。注意它只改报文解析这一格：临时读取错误在这档下仍然放行，因为那不算攻击者可控的畸形载荷。

期限的默认值也值得记一笔。`dcg config` 实测报 `Hook timeout (ms): 1000 (default)`，`dcg init` 生成的模板注释里写的是 200——那是个举例用的数字，不是默认值；`careful_company_running_windows` 这套预置例外，启用后期限自动提到 3000 ms。低于 10 ms 的值会被夹到 10 ms。无人值守的会话（没有人在终端边上回答 `ask`）应该显式设 `DCG_UNVERIFIED_DECISION=deny`，否则"无法核验"会一直走成"请人来判"。

## 一次真实拦截：从拒绝输出到短码放行

把一次完整流转串起来，这里用的是被拦下来的那条命令的实际输出。代理发出 `git reset --hard`，`dcg` 在钩子路径上的处置是：退出码 0、标准错误给人看的面板、标准输出给机器看的 JSON。

Claude 这一族拿到的是兼容层形状：顶层只有 `hookSpecificOutput` 一个键，它下面带 9 个字段。Claude Code 本体、复用同一层的 Copilot Chat 与 Gemini 命令行都属此类：

```json
{"hookSpecificOutput":{
  "hookEventName":"PreToolUse",
  "permissionDecision":"deny",
  "permissionDecisionReason":"BLOCKED by dcg ... Rule: core.git:reset-hard ...",
  "allowOnceCode":"190520",
  "allowOnceFullHash":"629166102efb04e3...13fa99f8",
  "ruleId":"core.git:reset-hard",
  "packId":"core.git",
  "severity":"critical",
  "remediation":{"safeAlternative":"Consider using 'git stash' first to save your changes.",
                 "explanation":"...","allowOnceCommand":"dcg allow-once 190520"}}}
```

`ruleId` / `packId` / `severity` 这三个字段决定了后续动作的粒度：你能精确地只放行这一条规则，而不是整个 `core.git`。`remediation.explanation` 是给代理读的第二机会——实测它把"哪些东西会丢"和"先 `git status && git diff` 看看会丢什么"都写进去了。

同一条命令换成 Codex 形状的信封（带非空 `turn_id`），stdout 上的 JSON 只剩 `hookEventName`、`permissionDecision`、`permissionDecisionReason` 三个键。这不是省流，而是 Codex 的解析器拒绝未知字段：多带一个 `allowOnceCode` 就会让这条命令在 Codex 侧被报成"钩子失败"而不是"命令被拦"。识别与裁剪的行为写在 `README.md:1089`，实测两侧字段集合的差如上。命令通过时，两条路径都是退出码 0、stdout 与 stderr 全空——`dcg` 从不主动表态"允许"，静默就是允许。

短码那条路有个容易撞上的门槛。在非终端环境里执行 `dcg allow-once 759325`，它拒绝写入并原样回显：

```text
Error: Allow-once needs an interactive confirmation, but stdin is not a terminal,
so the answer can never arrive. NOTHING was written and '759325' is still pending.
Re-run from a terminal, or confirm non-interactively with: dcg allow-once 759325 --yes
```

这个行为来自 `[interactive]` 一节：终端提示默认关闭（`enabled = false`）、`verification = "code"`、`disable_in_ci = true`。要批量放行，稳定的通道是 allowlist 而不是短码：`dcg allowlist add 'core.git:reset-hard' -r "变基前的例行清理" --user`，还支持 `--expires` 与 `--condition KEY=VAL` 两种收窄写法。

## 代理差异化与配置优先级

配置来源是五层，高优先级覆盖低优先级（`README.md:797-806`）：环境变量 `DCG_*` > `DCG_CONFIG` 指定的显式文件 > 用户配置 > 系统配置 `/etc/dcg/config.toml` > 编译期默认。macOS 上用户配置有两个落点会被扫到，`~/.config/dcg/config.toml` 与 `~/Library/Application Support/dcg/config.toml`；`dcg config --format json` 会把每一层的加载状态和 `hook_timeout_source` 一起打出来，排查"我改的到底生不生效"时先看它。

仓库里的 `.dcg.toml` 是个特例，也是这个项目最有意思的一个决定：被自动发现的仓库配置**只能加严**。它可以启用内置包、加 `deny` 条目、打开 `fail_closed`、开启 heredoc 扫描或关掉 heredoc 的回退；所有"给信任、减覆盖"的键则在自动发现时被直接忽略：allow 覆写、禁用包、自定义包路径、自定义正则、资源上限、语言过滤、代理 profile、嵌套项目覆写、逐条路径豁免。要显式信任整份仓库配置，得自己点名：`DCG_CONFIG=.dcg.toml dcg ...`。原生 Windows 连自动发现都不做，直到有等价的 reparse-point 与文件身份校验（`README.md:819-824`）。这条设计的判断很清楚：仓库在刚被克隆下来的时候是不可信输入方，不能因为它自带一份配置就让被保护对象给自己发通行证。

代理 profile 的四个行为字段是真的生效的，前提是代理**被识别出来**。识别顺序是先看命令行上的显式 `--agent`，再看环境变量（`src/agent.rs:398-404`）。实测在干净 shell 里写 `[agents.claude-code] additional_allowlist = ["git reset --hard"]`，钩子路径照拦不误——因为此时识别结果是 `unknown`；换成 `dcg test --agent claude-code "git reset --hard"`，才变成 ALLOWED。同一条命令在 `[agents.unknown] extra_packs = ["kubernetes"]` 下会去评估整个 Kubernetes 类，于是删集群里命名空间的那条 `kubectl` 命令被拦。`trust_level` 自始至终只是标签，进 JSON 和日志，不参与判定（`README.md:94-97`）。

支持的代理比"几个主流工具"多得多，README 第 16 行逐名列了 16 个，覆盖深度并不相同：

```text
Claude Code          Codex CLI 0.125.0+      Gemini CLI         GitHub Copilot CLI
VS Code Copilot Chat Cursor IDE              Hermes Agent       Posit Assistant
Grok (xAI)           Antigravity CLI (agy)   OpenCode           Oh My Pi (omp)
Crush                Pi (扩展配方)            Aider (仅 git hook) Continue (仅检测)
```

各家协议靠 `dcg install` 的 `--omp` / `--crush` / `--agy` / `--opencode` / `--grok` 分别配。此外还有一个可以完全不走钩子的入口：`dcg mcp-server` 以 stdio 提供 MCP（Model Context Protocol，模型上下文协议）服务，暴露 `check_command`、`scan_file`、`explain_pattern` 三个工具。

## 装起来与验收

三条安装路径的差别不在下载，而在配完钩子之后。

```bash
# 一键：选平台、验校验和、装二进制、配检测到的代理钩子
curl -fsSL "https://raw.githubusercontent.com/Dicklesworthstone/destructive_command_guard/main/install.sh?$(date +%s)" | bash -s -- --easy-mode

# Homebrew：只装 dcg 二进制，钩子要自己再跑一次 dcg install
brew install dicklesworthstone/tap/dcg

# 原生 Windows：SHA256 必验，装了 minisign 就验长期签名，装了 cosign 再验 provenance
& ([scriptblock]::Create((irm "https://raw.githubusercontent.com/Dicklesworthstone/destructive_command_guard/main/install.ps1"))) -EasyMode -Verify
```

`install.sh` 的开关密度能说明它踩过的坑：`--version`、`--dest`、`--system`、`--from-source`、`--require-minisign`、`--no-verify`、`--offline`、`--no-configure`、`--force`。手工配钩子时有一条不是建议而是要求：命令里写 `command -v dcg` 的绝对路径。钩子跑在非交互 shell 里，`PATH` 未必含 `~/.local/bin`，写成裸 `dcg` 的后果是钩子根本起不来，而"起不来"在这套语义里等于放行。

装完之后有三件事需要验收。Codex 侧要在它的 `/hooks` 界面里信任一次这个钩子（`README.md:1089`）。Claude Code 重写 `~/.claude/settings.json` 时会顺手抹掉别人的钩子条目，`dcg` 的对策是 `self_heal_hook` 默认为真：每次调用自检并修回注册。再配一次 `dcg setup`，它会往 `~/.bashrc` / `~/.zshrc` 里加一段启动检查，钩子真被摘掉时至少有个提示。然后就是本机跑一遍：

```bash
dcg doctor                    # 二进制是否在 PATH、各家钩子注册、构建溯源、配置加载来源
dcg explain "git reset --hard"   # 看命中哪条规则、处置是什么
dcg test "rm -rf ./src"        # 退出码 0 表示允许、1 表示拒绝
dcg packs                      # 列出 103 个包与当前启用的 3 个
```

要灰度不要惊吓，用 `dcg simulate`。给它一份命令日志——一行一条，纯命令、钩子 JSON 或决策日志都行，格式自动识别——它按当前策略重放一遍。"新启用数据库这一类会不会天天打断我"这种问题，用它回答比直接开到生产上稳妥。要接进代码评审，用 `dcg scan --format sarif`——实测它吐的是 SARIF 2.1.0，`runs[0].tool.driver.rules` 里带命中的规则，可以直接推到 GitHub Code Scanning。`--format` 这个参数本身是命令相关的：除 `dcg scan` 之外所有命令上的 `sarif` 都只是 JSON 别名， unrecognized 值一律退出码 2（实测 `dcg explain --format bogus` 即 2）。

## 这些数字测的是什么

本文出现的延迟数字有两类，别混着用。

一类是 `dcg` 自己计的内部耗时：`explain --format json` 的 `total_duration_us` 字段。在这台 Apple Silicon 机器上，8 条未命中命令各取 12 个样本，最小 1.3 ms、中位 1.4 ms、95 分位 5.9 ms；4 条命中命令中位 2.6 ms。另一类是端到端墙钟：连进程启动、报文解析和输出格式化，同一条命令 50 次平均 9.4 ms。

这两类数字能说明的是：预算表里"<100 μs 快路径"确实是被单独度量的那一段，而不是整次调用；一次钩子调用的成本里，`dcg` 的匹配逻辑不是大头，进程起来再退下去才是。它每次 shell 工具调用都要付出一次，所以"能不能感觉到"的正确答案是感觉不到——9 ms 相对一次大语言模型的往返请求是噪声量级。

不能说明的也别硬套。这里没有任何"拦截率"或"漏拦率"：`dcg` 的模式匹配是正则与 AST 的静态判断，命中率取决于代理实际写出什么命令，任何跨工作流的百分比都是编的。中位数低也不表示在饱和的 CI 机器上一样低。`README.md:992-996` 专门解释过期限为什么用单调墙钟而不是 CPU 时间：进程被调度出去、或者卡在某个有界操作上时，CPU 时间预算根本不前进。真要压这台机器上的表现，工具是给好的：`dcg test --enforce-budget`。

## 常见误区

按现象列，每条都在本文里验证过。

| 现象 | 原因 | 怎么确认 |
|------|------|----------|
| 删集群命名空间的 `kubectl` 命令照样跑 | 对应的包默认没启用，默认只有 3 个包 | `dcg packs` 看 `✓` 的数量 |
| 写了 `disabled = ["core.git"]` 但没生效 | `core.*` 不参与"可关闭"这件事 | 只有 `system.disk` 与 `windows.*` 能被关 |
| 整体设了 `warn`，critical 命令仍被硬拦 | 包级 / 全局 `warn` 对 critical 被静默抬回 `deny` | `dcg explain --format json` 读 `mode` |
| `explain` 显示 `deny`，命令却还是执行了 | `decision` 不是最终处置，`mode` / `outcome` 才是 | 同上，看 `warn` 档位 |
| `python3 -c "shutil.rmtree('/')"` 没拦 | `-c` 走通用模式，heredoc 才有专属规则族 | 写成 heredoc 立即命中 `heredoc.python:shutil_rmtree` |
| `[agents.claude-code]` 的配置像没读 | 当前会话没被识别成 claude-code | `dcg test --agent claude-code` 复现 |
| `dcg allow-once` 在 CI 里报错退出 | 短码要终端确认 | 加 `--yes`，或改用 `dcg allowlist add` |
| 钩子装了几天后失效 | Claude Code 重写 `settings.json` 抹掉了条目 | 看 `self_heal_hook` 与 `dcg setup` 的启动检查 |

## 该不该装，谁来先装

按角色分比按语言分更管用。

**每天和代理一起写代码的个人开发者**：直接装，默认那 3 个包已经覆盖掉最常见的两类不可逆损失（未提交修改与历史重写），这一步的收益不需要任何配置技巧。装完先做一件事：拿自己这周真跑过的命令走一遍 `dcg simulate`，看看有没有被 `medium` 档警告刷屏，再决定要不要逐条 `warn`。

**后端 / 基础设施团队**：价值主要在按需包里。把 `database.*`、`kubernetes.*`、`cloud.*`、`infrastructure.*` 打开，并且**先以 `warn` 跑一两个迭代**——这一步就是 `dcg simulate` 加 `[policy.packs]` 的组合。等误报摸清了再按包切 `deny`，critical 那 305 条本来也不需要你操心，松不动。

**代理种类多、甚至包含不可控来源代理的团队**：这里 `dcg` 提供了别处没有的一层。仓库 `.dcg.toml` 的"只能加严"模型，加上按识别结果分派的 profile，让你能给 `unknown` 加包、把 allowlist 收紧，而不用给所有代理统一降标准。前提是先接受一条约束：profile 只在识别成功时生效。

**不急着上的情形**也具体。纯人工、不跑代理的环境里，它的价值缩到 `dcg scan` 这一个 CI 用法。把 `rm` 之类彻底禁掉的需求它满足不了——`DCG_BYPASS=1` 是给运维留的逃生门，实测它确实把整次调用的防护全部拿掉（这也是它的已知反噬：`careful_company_running_windows.guardrails` 这个包会把 `DCG_BYPASS=1`、`dcg uninstall`、`dcg allowlist add` 本身当高危命令拦下来）。需要强隔离的场合应该往上走一层：容器、虚拟机、只读挂载，或者干脆不给代理可写的生产凭据。`dcg` 自己的威胁模型写得很坦白——假设代理善意但会犯错（`README.md:2722-2724`），它不是一道边界执行点。

还有两条采用前的现实检查。许可证是 MIT 加一条针对 OpenAI 与 Anthropic 的排除条款，法务如果对上游许可敏感，这条 rider 是必读项。仓库在 GitHub 上只算 2 名贡献者、2,484 次提交、8 个多月发了 71 个 Release：节奏极快，也意味着版本边界要盯住。把 `dcg update` 关掉（`general.update_pin = true`），按 Release notes 决定什么时候升，比让一个钩子工具自己滚更新稳妥。

## 五道自测题

1. 无配置文件时 `dcg` 在评估哪三个包？其中哪个能用 `disabled` 关掉？
2. 一条 `critical` 规则命中后想让它在终端上只出警告、在代理里不阻断，能写 `[policy.packs]` 吗？正确的写法是什么？
3. `dcg explain --format json` 输出 `decision = "deny"`，命令会不会被拦？该看哪个字段？
4. 代理写出 `eval "$(some-tool)"`，`dcg` 为什么选择拒而不是放？这个口子对 shell 初始化惯用法开了什么例外，例外依赖什么假设？
5. 钩子配置里为什么必须写绝对路径而不是裸 `dcg`？写错的后果是拦得更严还是更松？

## 出错时先看哪几处

按"命令没被拦"这个最常见现象排：

1. `dcg doctor`——二进制、各家钩子注册、构建溯源、当前配置来源，一次给全。
2. `dcg packs`——确认对应包真的带 `✓`；`database`、`kubernetes` 这类需要自己点名。
3. `dcg explain "<命令>"`——先确认命中与处置，再区分"没命中"和"命中了但只是 warn"。
4. `dcg config --format json`——看 `hook_timeout_ms` 与它的来源，超时预算耗尽会走成不可判定而不是静默放行。
5. 代理侧：钩子有没有被重写掉（`dcg setup` 的启动检查）、Codex 有没有在 `/hooks` 里信任、matcher 是否覆盖了 `Bash|PowerShell`（Windows 上只写 `Bash` 等于没装）。

反过来，"被拦得太多"的排查顺序也固定：先按现象分级，分清是 `deny` 还是 `medium` 自带的 `warn`。能整体降档的写 `[policy.packs]`，critical 只能逐条 `[policy.rules]`。重复出现的合法命令进 allowlist 并写清理由，一次性的用短码，不要把 bypass 常开。

## 下一步读哪份代码

五个问题答不顺，按这个顺序读仓库最快：

1. `README.md:195-249`（Enabled by default）与 `docs/graduated-response.md`——把"关不掉"和"松得动"这两件事的定义读准，省掉后面所有绕路。
2. `src/perf.rs:16-32`——预算表和 1000 ms 绝对上限的原文，也是理解"不可判定不等于放行"那节的钥匙。
3. `docs/adr-001-heredoc-scanning.md`——三层管线的选型现场，包括为什么否掉外部 ast-grep 命令行。
4. `src/heredoc.rs`（单文件，411,836 字节）与 `src/ast_matcher.rs`——触发词、提取上限与 AST 规则都在这一对文件里；规则 ID 的 `heredoc.<语言>:` 前缀在这里定义。
5. `src/config.rs` 与 `src/agent.rs`——五层合并、`enforcement-only` 的仓库配置、`--agent` 与环境检测的先后。

只想用它的话，顺序短得多：跑一键安装，`dcg doctor` 确认接线，`dcg explain` 试几条自己真会写的命令，用 `dcg simulate` 挑包，最后把重复放行的命令落进 allowlist。

## 维护指引与事实边界

这份文里所有命令与数字都指向可复算的对象，维护时按下面几条对齐。

| 事实 | 复算方式 | 会漂移的点 |
|------|----------|------------|
| 包数 103、模式 1,114 / 865、严重度分布 | `dcg packs --format json`；`dcg packs --verbose --expand` 数标签 | 每个版本都可能加包 |
| 默认 3 个包 | `dcg config` | 默认集可能扩，`system.disk` 这类可关项要单独核 |
| 各命令的处置与规则 ID | `dcg explain --format json <命令>` | 规则 ID 相对稳定，处置档位会变 |
| 延迟 1.4 / 2.6 / 9.4 ms | 按"这些数字测的是什么"一节的口径重跑，Apple Silicon 单机 | 换机器换负载要重测，不要沿用 |
| 星标 / 版本 / 发布节奏 | GitHub 仓库接口与 Releases 页，2026-09-21 取 | 一周就会变 |

三块内容没有在本机跑过，照实留在这里：原生 Windows 的 PowerShell 与 cmd 语义、各家代理客户端的端到端钩子行为（本文只构造报文测到 `dcg` 这一侧）、以及 `install.ps1` 的签名校验分支。覆盖面之外还有两条 README 自己列的固有边界：代理把脚本写进磁盘再执行时脚本内容不受检，以及"能绕过的攻击者永远能绕过"——它的定位是防错，不是防恶意。

## 参考资料

- 仓库与源码：[Dicklesworthstone/destructive_command_guard](https://github.com/Dicklesworthstone/destructive_command_guard)，本文读取的 main 提交为 `add38e4`（2026-09-20）
- `README.md`：默认包与"关不掉不等于松不动"（`195-231`）、包展开语义（`184-190`）、环境变量表（`702-744`）、输出格式（`771-795`）、配置层级（`797-828`）、Bounded Failure Policy（`893-998`）、各家代理协议差异（`1089-1100`）
- `docs/adr-001-heredoc-scanning.md`：三层管线的选型与预算；`docs/graduated-response.md`：严重度阶梯；`docs/custom-packs.md` 与 `docs/packs/README.md`：自定义包与包 ID 索引；`docs/codex-integration.md`：Codex 协议细节与其已知限制
- `src/perf.rs`、`src/packs/mod.rs`、`src/heredoc.rs`、`src/ast_matcher.rs`、`src/config.rs`、`src/agent.rs`：本文引用的实现位置
- `LICENSE`：MIT 与针对 OpenAI / Anthropic 的 rider 条款全文
- 实测环境：macOS（Apple Silicon）、官方 `dcg v0.14.4` aarch64-apple-darwin 发布物，tar 包 SHA256 与 Release 页一致；无配置文件状态下的默认策略，除个别小节显式给出临时配置
