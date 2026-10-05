---
title: "Cloudflare security-audit-skill：把编码 Agent 变成一支对抗式安全审计团队"
date: 2026-09-19T03:25:00+08:00
slug: "cloudflare-security-audit-skill"
github_repo: "cloudflare/security-audit-skill"
source_key: "gh:cloudflare/security-audit-skill"
description: "Cloudflare 开源的 security-audit-skill 是一个面向编码 Agent 的安全审计 skill：用六阶段工作流（侦察、覆盖账本驱动狩猎、候选验证、结构化输出、独立复核、中立报告）和对抗式验证纪律，把单个 Agent 编排成一支互相质疑的审计团队。本文拆解其证据契约、覆盖账本与预算模型。"
draft: false
categories: ["技术笔记"]
tags: ["Cloudflare", "安全审计", "AI Agent", "LLM", "Skills", "漏洞挖掘"]
---

## 核心判断

[cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill)（23.8k stars，2026-10 读数，JavaScript，MIT）解决的问题很具体：让 Claude Code、Cursor 这类支持子代理的编码 Agent，能对任意代码库跑一次**结构化、可复核、证据先行**的安全审计，而不是让模型自由发挥写一份"看起来像审计报告"的散文。

它是 Cloudflare 内部漏洞发现 harness（见官方博客 [Build your own vulnerability harness](https://blog.cloudflare.com/build-your-own-vulnerability-harness)）开源出的单仓库起点。harness 长成了多阶段、车队级系统，这个 skill 则是你可以一条命令装到本地 Agent 里的最小完整版。

它最有价值的不是某个提示词，而是把"审计质量"变成了**可验证的工程约束**：机器可读的中间产物 + 独立校验器 + 对抗式验证纪律。整篇文章围绕这三样展开，先给一张地图：

| 角色 | 职责 | 关键产物 |
|---|---|---|
| 父代理（编排者） | 分配任务、记账、跑校验器，自己不做结论 | `coverage-ledger.json`、`findings.json`、`run-metadata.json` |
| hunter（狩猎者） | 认领账本单元，只查自己那一块，返回检查记录和候选 | 单元级检查记录、候选漏洞（带指纹） |
| coverage critic（覆盖批评者） | 只找覆盖缺口，不提漏洞发现 | 缺口清单、重分配建议 |
| verifier（验证者） | 全新 Agent，任务是推翻候选而非确认 | `confirmed` / `needs_validation` / `rejected` 三种裁决 |
| 校验器（Node 脚本） | 拒绝任何不符合 schema 的记录和账本 | 通过 / 报错清单 |

指纹（fingerprint）是后文反复出现的概念：它是一条候选漏洞**源码根因的稳定标识**，同一根因在发现、验证、复核、跨运行携带的每个状态里都保持同一个指纹，是全系统去重和追溯的锚点。

## 六阶段工作流

skill 把一次完整审计拆成六个阶段，每个阶段有明确的输入输出：

1. **侦察（Reconnaissance）**——映射架构、信任边界、输入面和历史证据，产出 `architecture.md` 和 `coverage-ledger.json`（覆盖账本）。
2. **账本驱动狩猎（Coverage-led hunting）**——按账本单元派出**相互隔离的 hunter**子代理，每个 hunter 只负责自己的单元；随后由 coverage critic 检查账本缺口。
3. **候选验证（Candidate validation）**——每个候选漏洞交给一个**全新的 verifier**，它的任务是**试图推翻**这个发现，而不是确认它。
4. **结构化输出（Structured output）**——写入 `findings.json`，用 `validate-findings.cjs` 对照 `report-schema.json` 校验。
5. **独立记录复核（Independent record verification）**——第三批新 Agent 对最终记录逐条复核源码声明；有实质性替换的记录再过一轮独立验证。
6. **中立报告（Target-neutral reporting）**——从验证过的记录和账本推导出 `REPORT.md`、`FINDINGS-DETAIL.md`、`NEEDS-VALIDATION.md`。

两个零依赖 Node 校验器贯穿全程：父代理每次创建或更新账本后跑 `validate-coverage-ledger.cjs`，在 Phase 4 和每次 Phase 5 替换后跑 `validate-findings.cjs`。校验器本身也有硬边界——超过 5 MiB、超过 1,000 条记录、嵌套超过 64 层的输入直接拒收，错误输出截断在 100 条以内。一次账本无效，后续任务分配直接停摆。

三个裁决等级的语义被严格区分，这是整个证据契约的核心：

| 等级 | 含义 | 门槛 |
|---|---|---|
| `confirmed` | 已确认 | 完整的源码追踪链 + 有边界的实际观测结果 |
| `needs_validation` | 待验证 | 记录精确的未决事实，**不标严重级别** |
| `rejected` | 已否决 | 记录被推翻的候选，及其被推翻的原因 |

语义区分之外，schema 把字段也做了互斥锁定（`additionalProperties: false`）：`confirmed` 必须带 `root_cause`、复现条件、`execution`、`remediation`、`severity`、`confidence`，不许出现 `blockers` 或 `validation_plan`；`needs_validation` 只许用 `claimed_root_cause`，禁止携带 severity、修复建议或确定的根因；`rejected` 必须写明 `reason`。三条裁决的公共字段只有指纹、标题、描述和仓库相对路径。一个"半确认"的记录在格式层面就写不出来——这不是靠提示词劝出来的，是校验器拒收出来的。

注意 `needs_validation` 的设计：当部署配置、代理行为这类仓库外事实无法从源码确认时，Agent 不许瞎猜，只能记下"缺的具体事实是什么 + 安全的验证计划"（`validation_plan` 必须至少含一个本地或有主方观测的部署步骤）。这直接消灭了 LLM 审计最常见的失败模式——把猜测包装成结论。`rejected` 的保留同样有用途：未来运行在没有新证据时，不会重复这条已被推翻的主张。

## 三个值得抄的工程决策

### 1. 覆盖账本：让"没查过"成为一等公民

`coverage-ledger.json` 是整个系统的状态机。狩猎不是"扫一遍代码"，而是把目标拆成确定性的覆盖单元，逐单元分配 hunter、记录检查结果。每个单元有 `covered`（已覆盖，须有负责人、检查路径和检查记录）、`candidate`（发现候选，唯一允许挂指纹的状态）、`blocked`（查了但有未决事实）、`deferred`（明确记录为何没查）四种状态——**预算够不着的单元不许静默消失，必须以带理由的 `deferred` 落账**。critic 子代理专门找账本里的洞：未映射的入口点、没查的并行路径、缺失的生命周期模式、没有理由的排除项。文档里写明 critic "propose coverage, not findings"——它只对覆盖负责，不产出漏洞。

README 里有一句大实话：

> 在测试中，单次运行找到的漏洞大约只有多次运行总量的一半。

所以账本设计成**增量式**：对同一仓库的多次运行是叠加的——读取历史账本和 findings，只针对缺口狩猎、对变更源码重新验证，旧证据按指纹携带但不把过期工作当已覆盖。这把"审计"从一次性事件变成了可持续的资产。

`standard` 和 `deep` 档还要求双 critic 收口：每波 hunter 之后立刻跑一个全新的 post-wave critic，全部单元关闭后还要再跑一个**不同的** final-clean critic，两轮都提不出缺口才算覆盖完成。提前收工必须逐单元标注 `deferred` 并在报告中披露，静默的波次或数量上限不能当作覆盖完整的证据。

### 2. 对抗式验证：找到漏洞的 Agent 永远不负责确认它

发现者和验证者必须是不同的 Agent。verifier 的提示词第一句就是 "You did not write this candidate. Try to refute it"。输入侧同样隔离：verifier 拿到的是候选本身、关联的检查记录、schema 三个分支的原文，以及同指纹的历史记录——**它看不到 hunter 的原始文笔，也看不到其他 verifier 的结论**。

一个容易忽略的细节是证据的提升机制：verifier 只能写自己的 `scratch/` 目录，沙箱里跑出来的任何文件在执行后一律视为"目标可控内容"；只有可信的父端代码按预声明的允许清单，把文件从 `scratch/` 提升到 `artifacts/`，它才有资格当证据。沙箱进程全部退出之后才执行提升——被审计代码没有机会伪造自己想要的证据文件。

再加上 Phase 5：每个最终记录由一个全新的 `research` 类 verifier 并行复核，逐项核对路径、行号、输入形状、条件和观测结果。如果复核者给出了**实质性替换**——比如把记录提升为 `confirmed`，或者改动了根因、追踪链、影响面、严重级别——这份替换不能直接生效，必须交给一个既没狩猎过、也没做过 Phase 3 验证、也没提出这份替换的第三个新 Agent 再验一次。预算或独立性凑不齐时，宁可把争议记录从 `findings.json` 里删掉、账本单元退回未决候选、标记运行不完整。一个 `confirmed` 至少经过两双独立的"眼睛"，有争议时是三双。这是对"模型自我确认偏误"的直接工程化对抗——LLM 很擅长给自己找到的理由圆场，那就干脆不给它这个机会。

### 3. 证据纪律：严重性需要影响，纵深防御缺口不算漏洞

skill 的反模式清单写得很清楚：

- **只确认已成立的边界失效**——没有具体的低信任主体、越过的边界、受影响的资源，就不算 finding；
- **严重性 = 可能性 × 影响**，且总体严重级别不得超过已证实的影响，不是"偏离了 checklist"；
- **纵深防御缺口不是漏洞**——如果 A 层已经挡住了攻击，缺 B 层只是加固建议；
- **执行必须进沙箱**——目标代码只能在 OS 级沙箱里跑（断外网、白名单环境、资源限额、只写 scratch 目录），允许的是离线构建、隔离回环进程、单元测试、有界 fuzz 这类本地工作；真实流量、真实凭据、生产数据、发布操作全部禁止。沙箱不全就降级为 `needs_validation`，宁可不执行。

追踪链本身也有格式约束：多步 trace 必须从 `entrypoint` 开始、到 `sink` 结束，中间步骤标注 `propagation`——"我觉得这里有问题"写不成一条合法的追踪链。

最后一条尤其务实：它承认 Agent 环境不一定具备安全执行条件，与其冒险跑不可信代码，不如诚实记录阻塞点。

## 跟着一个候选走一遍

把六阶段串起来看一个候选漏洞的完整路径。假设某个 hunter 在"认证模块"这个账本单元里发现一个疑似漏洞：

1. hunter 返回一个 `candidate` 状态的单元，附上候选记录和一个**源码指纹**。指纹由根因决定——同一个根因暴露多条入口路径只算一个候选（取证据链最完整的那条），互不相关的缺失防护各用各的指纹。父代理按指纹合并去重，重复的候选不送验证。
2. 合并后的每个唯一候选交给一个全新 verifier。它的活是证伪：核对追踪链上每个引用的文件和行号、重建路径上真实存在的校验和控制、能安全复现的观测就独立复跑一遍。三种出口——证伪成功写 `rejected` 并给出理由；源码层面就能推翻的直接毙掉；确实卡在仓库外事实上的保留 `needs_validation`，写清 blocker 和验证计划。
3. 活下来的记录按指纹排序写入 `findings.json`，过校验器。
4. Phase 5 的第三方复核逐条过堂，实质性替换触发再验证（见上一节）。
5. Phase 6 只从最终记录推导报告，且报告是**目标中立**的：复现步骤用目标自身的原生接口写——库发现给函数调用，解析器发现给 fixture，CLI 发现给命令行。HTTP 只是可能的接口之一，不是默认假设，报告不会要求目标根本不存在的 endpoint 或外部账号。

## 预算模型：把 token 花在明处

skill 内置一套 agent 调用预算模型：一个账本单元 ≈ 一次 hunter 调用，一个存活候选 ≈ 1–2 次 verifier 调用（取决于 profile）。预算门禁在**第一次侦察之前**就要过——先预留 4 次基线侦察调用、每波 critic、终审 critic 和验证储备；预算连这个最小配置都付不起时，一个 Agent 都不启动，标记 `run_status: "incomplete"` 并写明原因（`budget_cannot_fund_reconnaissance_and_reserves`），而不是悄悄缩水。开跑前必须先声明 profile（`quick`/`standard`/`deep`，默认 `standard`）；预算中途见底时按指纹顺序验证幸存候选，剩下的保持未决，原因记 `validation_budget_exhausted`。

文档里有一条底线："profile 只改变广度和冗余，绝不改变证据门槛"——`quick` 可以合并 Phase 3 和 Phase 5（每个候选一个独立复核者而不是两个），但任何 profile 下 `confirmed` 记录的独立复核都不能跳过。预算的另一个纪律是**只有两种合法终态**：全部产物写完且两个校验器通过，或者 `run_status: "incomplete"` 带精确原因、缺口在报告里披露。不存在"跑到一半算了"这个状态。

这套设计对任何"多 Agent 编排"场景都有参考价值：**冗余和验证是预算项，不是空气**。

## 上手

```bash
npx skills add https://github.com/cloudflare/security-audit-skill \
  --skill security-audit
```

加 `--global` 可装成用户级，对所有项目可用。然后在目标代码库里对编码 Agent 说一句 `security audit this codebase`、`find security vulnerabilities in ./src` 这类话即可触发完整审计。注意两种模式：默认是**guidance 模式**（只回答安全问题、不落盘），只有明确要求审计/渗透测试/完整审查时才进**full audit 模式**跑六阶段。输出目录默认在 `~/security-audit-skill/<repo>/run-<N>`，多轮运行天然隔离；想写进目标仓库，必须显式选一个被版本控制忽略的目录。

前置要求：支持工具调用和并行子代理的编码 Agent、Node.js（跑零依赖校验器）、以及一个 OS 级沙箱（没有它，skill 会把需要执行验证的线索全部降级为 `needs_validation`）。

拿到报告后建议按这个顺序读：`REPORT.md` 第一节先交代运行元数据——profile、范围、预算花费对计划、是否用了历史运行、哪些单元 `deferred` 或范围外，`quick`、范围受限或预算不足的运行会明说自己是**部分覆盖**；然后是安全姿态摘要和 `confirmed` 发现表；`NEEDS VALIDATION` 表单独列出，只有精确的 blocker 和验证计划，没有严重级别。最后一节是从账本汇总的覆盖统计。解读时还有一条关键：干净的运行可以零 `confirmed`——报告会如实说"没找到"，并列出剩余的覆盖和验证局限，**不会为了凑数发明 LOW 级发现**。被否决的记录不会出现在发现表里，只在需要解释历史分歧时提到指纹。

## 边界与评价

它不是 SAST 扫描器的替代品——没有规则库、没有数据流引擎，本质是一套**编排协议 + 证据契约**，挖掘能力上限取决于底层模型。攻击类知识被拆成 11 个领域文件（Web 协议与认证、内存安全与二进制、AI/LLM 注入、供应链、云与部署、资源耗尽、租户隔离与数据生命周期、桌面与本地 IPC 等），本质是结构化的提示词资产。

采用顺序上：个人开发者或小仓库，直接跑一次 `quick` profile 看输出质量，这一步零成本且能立刻判断模型底子够不够；团队代码库先 `standard` 加范围限定（只审一个子系统或一次 diff），确认报告可读、误报可接受后再放大范围；`deep` 模式按子系统拆单元、critic 跑到干净通过，token 成本需要认真对待，留给高风险目标。反过来说，如果你的诉求是已知漏洞模式的快速扫描（依赖 CVE 比对、密钥泄漏检测），规则型扫描器更便宜也更合适——这个 skill 的价值在"发现未知边界失效"，不在"核对已知清单"。

但它示范了一个重要方向：当 LLM 参与高风险判断时，质量不靠提示词祈祷，而靠**结构化中间产物 + 独立校验 + 对抗式复核**这三件套。这套纪律移植到代码评审、合规检查、数据分析等任何"需要可问责结论"的场景都成立。

---

**参考**：[仓库 README](https://github.com/cloudflare/security-audit-skill) · [Cloudflare 博客：Build your own vulnerability harness](https://blog.cloudflare.com/build-your-own-vulnerability-harness)
