---
title: "ai-memory：给 AI 编码 Agent 的跨会话长期记忆"
date: 2026-08-21T03:26:00+08:00
slug: "ai-memory-agent-long-term-memory"
github_repo: "akitaonrails/ai-memory"
source_key: "gh:akitaonrails/ai-memory"
description: "ai-memory 用 Rust 实现一个基于 MCP 的长期记忆服务器，把 AI 编码 Agent 的会话观察编译成 git 版本化的 Markdown 知识库，为 20 多种 harness（Claude Code、Codex、Cursor 等）提供跨工具交接。本文解析其架构、2.0 的格式迁移与检索质量数据。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "MCP", "长期记忆", "Rust"]
---
# ai-memory：给 AI 编码 Agent 的跨会话长期记忆

## 核心判断

各家编码 Agent 的记忆都是孤岛：Claude Code 的笔记留在本机、只属于 Claude Code，切到 Codex 就看不见了。ai-memory（[akitaonrails/ai-memory](https://github.com/akitaonrails/ai-memory)）把这些孤岛接进同一个服务器：单个 Rust 二进制，跑一个 MCP/HTTP 服务，各 Agent 的生命周期钩子（lifecycle hook）把脱敏（sanitized）过的观察报上来，会话结束时编译成 git 版本化的 Markdown wiki。中途退出 Claude Code，在同一目录启动 Codex，下一位 Agent 开场就能拿到一份「接着上次的进度」的交接——架构、失败过的方案、悬而未决的问题，都不用你重述。

它的设计内核是 **compile-not-retrieve**（编译而非检索）：不做「每次对话都全量查向量库」，而是把零散观察固化成结构化页面，检索走 SQLite FTS5、实体与图邻居的混合召回。README 明确把 Karpathy 的 LLM Wiki 思路列为源头，把 agentmemory、basic-memory、cognee、Hermes Agent、A-MEM 列为先例。

这个项目 2026 年 5 月 21 日创建，迭代极快：8 月下旬还在 v1.38，9 月 12 日已发布 v2.2.1。**2.0 是个分水岭**：wiki 格式切换到 Open Knowledge Format（OKF）v0.2、本地嵌入默认开启、官方首次公布检索质量基准。本文事实核对截至 v2.2.1。

| 项 | 值 |
|------|------|
| Stars / Forks | 6,727 / 454（2026-09-14 观测） |
| 语言 / 协议 | Rust / MIT |
| 最新版本 | v2.2.1（2026-09-12 发布） |
| 支持的 harness | 20 多种（一方集成，CI 保持同步） |

## 系统地图：一个二进制，一个数据目录

```
ai-memory（单个 Rust 二进制）
└── <data_dir>/
    ├── wiki/    # Markdown 源数据（真源），git 版本化
    ├── raw/     # 不可变的 sanitized managed-workstream 转录片段
    ├── db/      # SQLite 索引（FTS5 + 实体 + 嵌入）
    ├── models/  # 预留给本地嵌入模型
    └── logs/    # 滚动日志
```

数据流是单向的：

```
各 Agent 生命周期钩子
    │  POST 观察（sanitized）
    ▼
MCP/HTTP 服务器
    │  单个 SQLite writer actor 串行写入
    ▼
编译成 Markdown 页面（wiki/）
    │
    ▼
检索：FTS5 + 实体 + 图邻居（可选向量 RRF）
    ▼
下一位 Agent 会话开头收到 bounded handoff
```

## 架构要点

### 1. 单一 writer 与「编译而非检索」

所有观察经钩子 POST 到服务器，由**单个 SQLite writer actor** 串行落盘。坚持单一 writer，是把 SQLite 的写锁竞争挡在设计外：所有写入排进一个消息队列串行执行，读走可克隆的只读连接池，会话高并发时只需考虑读扩展。检索侧是四路混合召回——FTS5 全文、实体匹配、图邻居 RRF（Reciprocal Rank Fusion，倒数排名融合），可选再加向量 RRF——候选生成后统一做一次有界的来源权威度调整；非全局检索在编译后的页面没命中时，退回有界的原始观察兜底。嵌入改善相关性召回，但不决定哪条来源是权威版本。

### 2. 捕获是有边界的，这是刻意的取舍

钩子采用 fire-and-forget 设计，只上报受限的、脱敏过的观察：用户 prompt 与压缩后摘要最多 16 KiB，通知与工具摘录上限 2 KB，每条持久观察正文另有 16 KiB 的兜底上限。它**不是完整的原生转录**。捕获成本低，代价是保真度有上限——后文检索基准那一节会回到这个代价。

### 3. 按项目隔离是「构造上」保证的

每个项目落在 `<wiki_root>/<workspace_id>/<project_id>/…`，由稳定 UUID 定位。项目身份从 `$cwd` 推导：CLI 子命令会向上走到主 git 仓库根，让同一仓库的所有 worktree 共享一个项目身份；钩子路由默认用 `basename($cwd)`，也可 opt-in 仓库根规则。在任意祖先目录放一个 `.ai-memory.toml` 标记文件即可显式覆盖——适合多客户咨询、工作/个人分离、monorepo 或链接的 git worktree。同一页面路径可在两个项目并存而不冲突；重命名是改一列；清理是一次 `rm -rf`。

v1.39 起，「当前项目」指针默认按调用方隔离：两个 Agent 同时在同一个项目里干活，或者队友共用一台服务器，开箱即用，不串记忆。

### 4. 交接是协议，不是约定

「退出 Claude Code 中途换 Codex，几小时后在相同目录启动，下一位 Agent 在第一条 prompt 前看到 where you left off 区块」——这是它的招牌场景。README 对此的说法是：handoff 在这里是一种协议（typed、owned、claimed exactly once），有类型、有归属、只能被认领一次，而不是各工具间的君子协定。

进一步，`ai-memory run` 提供可选的 **managed workstreams**：对 Claude Code、Codex、OpenCode（含 2.0 beta）、Pi、Crush、Kimi Code、Command Code、Kiro CLI v2/v3、OMP、Grok Build CLI、Antigravity CLI 这十来套 harness 做透明的跨工具连续性——自动选 harness、原生会话恢复、参数透传、会话账本（ledger）检索。直接启动（direct launch）的轻量路径不受影响。

### 5. 捕获豁免与后台自动完善

「编译」不是只在会话结束时跑一次，两条机制保证 wiki 越用越新。

**捕获豁免有两档，取舍相反。** 默认档按 `.ai-memory.toml` 里 `[capture] ignore_paths` 的黑名单工作，匹配的 file-tool 事件在进入本地 spool、队列、传输、日志之前就被丢弃——敏感文件连轨迹都不落盘。`install-hooks --capture-mode allowlist` 则反转为白名单：仓库里没放 marker，钩子就完全不产生任何生命周期事件。默认档漏掉 marker 只损失覆盖率；白名单档漏掉 marker 损失的是召回，保住的是机密。后者的豁免只由原生 `ai-memory hook` 命令强制执行。配合按项目隔离，这是数据本地化诉求的又一道闸。

后台调度让记忆持续固化。会话结束时先生成一条**规则式**（不调 LLM）的 `sessions/<id>.md` 摘要，不消耗 token，没有 LLM 配置也不阻塞会话结束；配了 `AI_MEMORY_LLM_PROVIDER` 后，`memory_consolidate` 再把摘要重写成更持久的页面，或按 `concepts/`、`decisions/`、`gotchas/` 拆成多页并互加 wikilink。一个后台调度器遍历新完成的会话，把审过的提议写进 pending-writes 审计、默认自动合并回 wiki；共享/团队服务器建议设 `[auto_improve] require_approval = true` 改为人工审批，`[auto_improve.scheduler] enabled = false` 可整体关闭。每个 consolidation 与每个 session-end 都在 `wiki/` 落一次持久 git commit——**编译因此是增量维护，不是一次性快照。**

### 6. 2.0 换了三块地基

**wiki 成了标准格式文件。** 2.0 把 wiki 的磁盘格式切换到 Open Knowledge Format v0.2——Google 发布的开放知识格式，ai-memory 成为它的服务器级实现。每个页面的 frontmatter 就是 OKF 字段，`tier`、`kind`、`entities`、TTL 作为扩展字段共存。对存量用户，升级是自动的、备份门控的：首次以 2.0 启动时先把整个数据目录压缩成带时间戳的档案（`~/ai-memory-backup-okf-v0.2-<date>.tar.gz`）并验证可读，验证不过就拒绝启动、数据不动；档案里的 `db/` 仍是 1.x schema，随时可以退回旧版二进制。2.0.3 修复了早期版本备份时序的一个缺陷，现在跑 2.0.x 应升级到最新补丁版。

**本地嵌入默认开启。** 没配过嵌入提供商的安装，首次启动会在后台下载一个约 87 MB 的模型（校验和固定），用进程内的 all-MiniLM 做嵌入——无 API key、无外联。语义检索从此是默认能力，不再是可选项。

**知识有了类型和时间。** 类型化的关系边（`causes` / `fixes` / `contradicts`）进入图检索与 lint；实体索引和页面版本带摄取时间有效期，支持 `as_of` 时间旅行查询——「当时我们怎么认为」和「现在我们认为」可以分开查。

## 一次跨 CLI 交接：断点在哪，记忆如何跟上

把这套抽象落到一条真实工作线里，比单看机制图更接近使用时的判断：

```
① 搭环境：ai-memory run claude（Claude Code）
② 会话 1：修一个 flaky 集成测试
   PreToolUse/PostToolUse 钩子上报 sanitized 观察
   prompt 与压缩后摘要 ≤16 KiB，通知与工具摘录 ≤2 KB
   单个 SQLite writer 串行落盘，wiki/ 落一次 git commit
③ 退出：SessionEnd → 规则式 sessions/<id>.md 摘要
   + 开一条 handoff；若配了 LLM provider，
   memory_consolidate 展开成 concepts/decisions/gotchas 页
④ 半天后：同一目录 ai-memory run codex --yolo
   Codex 原生会话恢复 + 未消费 handoff 注入（带版本化 origin marker）
   第一条 prompt 前读到 "where you left off"
⑤ 提问：memory_query 走 FTS5 + 实体 + 图邻居 RRF
   编译结果 miss 时退回有界的原始观察检索
```

交接的真实成色取决于各家 harness 的钩子能力，第 ④ 步见分晓。Codex 从 CLI 0.145.0 起有了真正的 SessionEnd 事件（openai/codex#33895），会话结束自动出摘要和交接；更老的版本上这个事件是死的，退路是手动 `ai-memory finalize-session --agent codex`。注入通道也有差异：Grok、Zero、Pool 根本不消费 session-start 的 stdout，只能经 MCP 的 `memory_handoff_list` 看到交接、再用 `memory_handoff_accept` 按手取回；Kimi Code 丢弃 SessionStart stdout，ai-memory 改从 UserPromptSubmit 注入；Crush 没有 SessionStart，走一条临时受支持的 global-context 通道；ZCode 的 SessionStart stdout 注入可用，但 `Stop` 只是每轮边界，收尾仍要 `finalize-session`。Kiro CLI 与 Antigravity CLI 同样没有真正的 session-end，需要手动收尾。

## 检索质量：官方基准说了什么，不能推出什么

2.0 之前这个项目没有公布过检索指标，2.0 的第一件事就是建了仓库内评测框架，用 LongMemEval-S（v1）数据集给出可复现的数字（commit、数据集哈希、硬件齐全，`docs/benchmarks/` 可查）：

| 模式 | 整体 hit@5 |
|------|-----------|
| pre-2.0 零 LLM FTS | 0.617 |
| 2.0 零 LLM FTS（去停用词） | 0.668 |
| 2.0 默认（本地嵌入 + FTS 混合） | **0.823** |

测的是「给定历史会话，检索器能否把相关记忆召回进前 5」。0.617 → 0.823 的提升来自两步实测改动：FTS 的 OR 连接去掉停用词（hit@5 +5.1），再用修正了 masked-mean 池化的进程内本地嵌入器（约 +6.6）——每一步都先测再合，作为后续所有 2.0 特性的回归门槛。

不能推出的：agentmemory 在同一数据集上公布过 0.967 R@5，高于 ai-memory 的 0.823，但两者不可直接比。对方是对原始聊天日志做嵌入式检索；ai-memory 的捕获在 2 KB 隐私边界裁剪过，长 turn 深处的证据根本进不了索引。官方自己的表述是：基准测的是出货系统，不是理想检索器——这个代价是真实且故意的。反过来，0.668 这个「零 LLM 确定性下限」说明：不配任何 LLM/embedding key，检索质量也有一个可用的下限。

## 从单人工具到团队基础设施

v1.x 基本是单人单机的形态，2.0 前后补齐了团队这一层：服务器放在 homelab 或 LAN 主机上，每台机器、每个队友指向同一个数据目录——桌面上没做完的项目，笔记本上接着做。知识按项目共享，个人交接保持私有；每次写入带操作者归属、进审计日志；多用户认证（密码、API 凭证）内置，不设付费墙。写入吞吐的上限是实测的约 700 条/秒，不是估算值。README 给的唯一硬规则：一个数据目录只能有一台服务器，绝不能两台。

## 支持矩阵（节选）

完整矩阵见 [docs/support-matrix.md](https://github.com/akitaonrails/ai-memory/blob/main/docs/support-matrix.md)，全部为一方集成并有 CI 保持同步。

| 客户端 | 形态 | 说明 |
|--------|------|------|
| Claude Code | MCP + 生命周期钩子 | `--capture-assistant` 双 opt-in，仅 Claude Code 与原生平台 |
| Codex | MCP + 生命周期钩子 | CLI 0.145.0 起 SessionEnd 自动；旧版手动 `finalize-session` |
| Cursor / Gemini CLI / Devin CLI / OpenCode | MCP + 生命周期钩子 | — |
| Kimi Code | MCP + 生命周期钩子 | 交接经 UserPromptSubmit stdout 注入 |
| Grok Build CLI / Zero | MCP + 生命周期钩子 | 不消费 session-start stdout，经 MCP `memory_handoff_accept` 取回 |
| ZCode | MCP + 生命周期钩子 | 6 个触发器；`Stop` 为轮次边界，收尾需 `finalize-session` |
| Kiro CLI / Antigravity CLI | MCP + 生命周期钩子 | 无 true session-end，手动 `finalize-session` |
| Crush | Managed-only | 无 SessionStart，经临时 global-context 通道注入 |
| Pool | 仅钩子 | 无一方 MCP 客户端；SessionStart stdout 注入未验证 |
| OpenClaw | MCP + 原生插件钩子 | — |
| VS Code Copilot / Zed / Muse Code / Swival CLI | 仅 MCP | Copilot 尚无生命周期钩子 |
| Claude Desktop | 仅 MCP | 经 `mcp-remote` |
| Hermes Agent | 社区支持 | 社区维护插件，需自行审查 |

LLM 提供商（可选，仅用于升级摘要与语义检索）：Anthropic、OpenAI（含 OAuth/Codex）、GitHub Copilot、Gemini、OpenCode Go/Zen，以及任意 OpenAI 兼容端点（Ollama、LM Studio、vLLM）。嵌入提供商：OpenAI、Voyage、Gemini、无 key 的 OpenAI 兼容端点，以及 2.0 起默认的进程内本地模型。OIDC 设备认证用于原生钩子的身份验证，属认证通道而非 LLM 提供商。**默认路径零 LLM 调用**：捕获、搜索、交接都不需要任何 API key。

## 快速上手路径

1. 装服务器，三选一：Docker（发布 `linux/amd64` 与 `linux/arm64` 镜像，默认绑定 `127.0.0.1:49374`，单用户笔记本上无需认证即可用）；macOS 原生 release 二进制（官方推荐，无需 Docker）；Arch Linux 走 AUR 的 `ai-memory-bin` 或 `ai-memory` 包（自带 systemd 单元）。Windows 支持 WSL2，原生 Windows 为实验性。
2. 给目标 Agent 装两条配置：`ai-memory install-mcp --client <name> --apply` 与 `ai-memory install-hooks --agent <name> --apply`。装别的 Agent 就是换名字重跑这两条。
3. 正常干活。会话结束自动编译；下一位 Agent 开头收到 handoff。接手一个有几个月历史的老项目时，先跑一次 `ai-memory bootstrap`。
4. 需要网页查看时，以 `--enable-web` 启动，得到一个只读的 wiki 浏览视图和 `/api/v1` 下的 JSON API。
5. 把服务暴露到局域网/多用户场景时，按 `docs/deploy.md` 配 bearer token，按 `docs/https-via-proxy.md` 配 TLS；多用户与归属管理见 `docs/users.md`。

卸载用 `ai-memory uninstall --apply`，只删它自己装过的东西；所有安装命令幂等，动过的文件旁都会留时间戳备份。

## 适用边界

**适合**：经常在多套 AI 编码 CLI 间切换、厌倦反复重述项目架构的开发者与团队；希望记忆以可 grep 的 Markdown + git 形式存在、而非黑盒向量库的用户；自托管、重视数据本地化的场景——默认路径零 LLM 调用，不配任何 API key 也能用满核心功能。

**需注意**：钩子捕获是有边界的（非完整转录），保真度上限明确；managed workstreams 是 opt-in，直接启动才是默认路径；各家 harness 的交接能力差异大（有的没有注入通道，只能经 MCP 取回）；多用户场景的 per-user slot 是上下文注入隔离，不是 RBAC。项目迭代极快（截至 2026-09-14 已到 v2.2.1），使用前留意 release 变更；存量 1.x 数据升级 2.0 会触发格式迁移，虽有自动备份与回滚路径，关键数据先手动备份一次不亏。

**采用建议**：个人开发者、多 CLI 重度切换的小团队，现在就可以从 Docker 快启 + 两条 install 命令开始，零 LLM 配置先用起来，再按需加嵌入与 LLM。把 wiki 当合规档案、要求格式长期稳定的团队，可以等 2.x 再稳两三个补丁版——迁移可回滚，但越早采用，承担的兼容性风险越高。

## 持久化与运维边界

wiki 是普通 Markdown + git：可 `grep`、可在 Obsidian 打开、可用 `rsync` 备份；SQLite 数据库只是随时可以从这些文件重建的派生索引。没有要伺候的向量库，没有「remember this」仪式，没有手动装载上下文的步骤。

运行状态操作（purge / rename / backup / restore / reset / reindex）动的是真数据：执行前先读 `docs/lifecycle-ops.md` 的安全矩阵与每项目磁盘布局，里面有「全新开始」「危险操作前快照」「只删一个项目」「从 wiki 文件重建 SQLite」这几条现成的操作路径。

## 一句话总结

ai-memory 用「git 版本化的 Markdown wiki + SQLite 混合检索」这个极简内核，把跨 Agent、跨会话的记忆交接做成了一等能力；2.0 又把 wiki 变成开放格式、把语义检索变成默认能力、补上了团队协作层——它是「Karpathy LLM Wiki 思路」在 Rust 生态里一个相当完整的工程化落地。
