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

[cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill)（约 13k stars，JavaScript，MIT）解决的问题很具体：让 Claude Code、Cursor 这类支持子代理的编码 Agent，能对任意代码库跑一次**结构化、可复核、证据先行**的安全审计，而不是让模型自由发挥写一份"看起来像审计报告"的散文。

它是 Cloudflare 内部漏洞发现 harness（见官方博客 [Build your own vulnerability harness](https://blog.cloudflare.com/build-your-own-vulnerability-harness)）开源出的单仓库起点。harness 长成了多阶段、车队级系统，这个 skill 则是你可以一条命令装到本地 Agent 里的最小完整版。

它最有价值的不是某个提示词，而是把"审计质量"变成了**可验证的工程约束**：机器可读的中间产物 + 独立校验器 + 对抗式验证纪律。

## 六阶段工作流

skill 把一次完整审计拆成六个阶段，每个阶段有明确的输入输出：

1. **侦察（Reconnaissance）**——映射架构、信任边界、输入面和历史证据，产出 `architecture.md` 和 `coverage-ledger.json`（覆盖账本）。
2. **账本驱动狩猎（Coverage-led hunting）**——按账本单元派出**相互隔离的 hunter**子代理，每个 hunter 只负责自己的单元；随后由 coverage critic 检查账本缺口。
3. **候选验证（Candidate validation）**——每个候选漏洞交给一个**全新的 verifier**，它的任务是**试图推翻**这个发现，而不是确认它。
4. **结构化输出（Structured output）**——写入 `findings.json`，用 `validate-findings.cjs` 对照 `report-schema.json` 校验。
5. **独立记录复核（Independent record verification）**——第三批新 Agent 对最终记录逐条复核源码声明；有实质性替换的记录再过一轮独立验证。
6. **中立报告（Target-neutral reporting）**——从验证过的记录和账本推导出 `REPORT.md`、`FINDINGS-DETAIL.md`、`NEEDS-VALIDATION.md`。

三个裁决等级的语义被严格区分，这是整个证据契约的核心：

| 等级 | 含义 | 门槛 |
|---|---|---|
| `confirmed` | 已确认 | 完整的源码追踪链 + 有边界的实际观测结果 |
| `needs_validation` | 待验证 | 记录精确的未决事实，**不标严重级别** |
| `rejected` | 已否决 | 记录被推翻的候选，及其被推翻的原因 |

注意 `needs_validation` 的设计：当部署配置、代理行为这类仓库外事实无法从源码确认时，Agent 不许瞎猜，只能记下"缺的具体事实是什么 + 安全的验证计划"。这直接消灭了 LLM 审计最常见的失败模式——把猜测包装成结论。

## 三个值得抄的工程决策

### 1. 覆盖账本：让"没查过"成为一等公民

`coverage-ledger.json` 是整个系统的状态机。狩猎不是"扫一遍代码"，而是把目标拆成确定性的覆盖单元，逐单元分配 hunter、记录检查结果。critic 子代理专门找账本里的洞。README 里有一句大实话：

> 在测试中，单次运行找到的漏洞大约只有多次运行总量的一半。

所以账本设计成**增量式**：对同一仓库的多次运行是叠加的——读取历史账本和 findings，只针对缺口狩猎、对变更源码重新验证，旧证据按指纹携带但不把过期工作当已覆盖。这把"审计"从一次性事件变成了可持续的资产。

### 2. 对抗式验证：找到漏洞的 Agent 永远不负责确认它

发现者和验证者必须是不同的 Agent，验证者的任务是证伪。再加上 Phase 5 的第三方复核，一个 `confirmed` 至少经过两双独立的"眼睛"。这是对"模型自我确认偏误"的直接工程化对抗——LLM 很擅长给自己找到的理由圆场，那就干脆不给它这个机会。

### 3. 证据纪律：严重性需要影响，纵深防御缺口不算漏洞

skill 的反模式清单写得很清楚：

- **只确认已成立的边界失效**——没有具体的低信任主体、越过的边界、受影响的资源，就不算 finding；
- **严重性 = 可能性 × 影响**，不是"偏离了 checklist"；
- **纵深防御缺口不是漏洞**——如果 A 层已经挡住了攻击，缺 B 层只是加固建议；
- **执行必须进沙箱**——目标代码只能在 OS 级沙箱里跑（断外网、白名单环境、资源限额、只写 scratch 目录），沙箱不全就降级为 `needs_validation`，宁可不执行。

最后一条尤其务实：它承认 Agent 环境不一定具备安全执行条件，与其冒险跑不可信代码，不如诚实记录阻塞点。

## 预算模型：把 token 花在明处

skill 内置了一套 agent 调用预算模型：一个账本单元 ≈ 一次 hunter 调用，一个存活候选 ≈ 1–2 次 verifier 调用。开跑前必须先预留侦察基线、每波 critic、终审 critic 和验证储备；预算不够就不启动，或者降级 profile（`quick`/`standard`/`deep`），而不是悄悄砍掉证据环节。预算耗尽时诚实标记 `run_status: "incomplete"`，报告首节必须声明哪些候选没验证完。

这套设计对任何"多 Agent 编排"场景都有参考价值：**冗余和验证是预算项，不是空气**。

## 上手

```bash
npx skills add https://github.com/cloudflare/security-audit-skill \
  --skill security-audit
```

然后在目标代码库里对编码 Agent 说一句 `security audit this codebase` 即可触发完整审计。注意两种模式：默认是**guidance 模式**（只回答安全问题、不落盘），只有明确要求审计/渗透测试/完整审查时才进**full audit 模式**跑六阶段。输出目录默认在 `~/security-audit-skill/<repo>/run-<N>`，多轮运行天然隔离。

前置要求：支持工具调用和并行子代理的编码 Agent、Node.js（跑零依赖校验器）、以及一个 OS 级沙箱（没有它，skill 会把需要执行验证的线索全部降级为 `needs_validation`）。

## 边界与评价

它不是 SAST 扫描器的替代品——没有规则库、没有数据流引擎，本质是一套**编排协议 + 证据契约**，挖掘能力上限取决于底层模型。攻击类知识被拆成 11 个领域文件（Web 协议与认证、内存安全与二进制、AI/LLM 注入、供应链、云与部署、资源耗尽等），本质是结构化的提示词资产。对个人开发者，单仓库跑一次 `quick` profile 是现实的；`deep` 模式的 token 成本需要认真对待。

但它示范了一个重要方向：当 LLM 参与高风险判断时，质量不靠提示词祈祷，而靠**结构化中间产物 + 独立校验 + 对抗式复核**这三件套。这套纪律移植到代码评审、合规检查、数据分析等任何"需要可问责结论"的场景都成立。

---

**参考**：[仓库 README](https://github.com/cloudflare/security-audit-skill) · [Cloudflare 博客：Build your own vulnerability harness](https://blog.cloudflare.com/build-your-own-vulnerability-harness)
