---
title: "reverse-skill：给编码代理的逆向与渗透技能路由"
date: 2026-08-02T02:59:48+08:00
lastmod: 2026-09-28
slug: "zhaoxuya520-reverse-skill-cybersecurity-router"
github_repo: "zhaoxuya520/reverse-skill"
source_key: "gh:zhaoxuya520/reverse-skill"
description: "zhaoxuya520/reverse-skill 是一个面向 AI 编码代理（Claude Code/Codex/Cursor/Cline 等）的安全任务技能路由包：44 条路由规则把 APK、二进制、前端 JS 加密、CTF 题目、渗透目标分派给对应方法论，配合同意门控、scope 授权门禁和证据链，让代理按可重复流程做事，而不是凭直觉猜命令。本文以 2026-09 仓库状态（v1.0.1 之后的 main）为口径。"
draft: false
categories: ["技术笔记"]
tags: ["Agent Skills", "网络安全", "逆向工程", "渗透测试", "CTF", "Claude Code"]
---

## 一句话判断

`zhaoxuya520/reverse-skill` 的核心价值是"**不让代理凭直觉猜命令**"。README 把痛点说得很直白：AI 代理拿到一个任务时，分不清该上 jadx、apktool、Frida、IDA 还是 BurpSuite；APK、ELF、JS、PCAP、CTF 各需要一套打法；工具和 MCP 服务器散落在不同机器上；同样的错误反复犯，因为经验没有被复用。这个包用一份结构化路由配置回答"该走哪条路"，再用一套作业合同约束"上路之后怎么走"。

仓库目前 38,447 stars、5,347 forks（2026-09-28 GitHub API 读数），2026-05-13 建仓，当前版本锚点 v1.0.1（2026-08-08 发布），main 分支持续活跃。主语言是 PowerShell——Windows 是一等公民，Linux/macOS/Kali 走平行的 Bash 入口。

## 两类读者，一份仓库

README 开头第一句话是写给代理的：

> If you are an AI Agent, jump to README_AI.md and follow the instructions strictly.

于是这个仓库同时服务两类读者：人类安全研究员把它当工具集合和索引读；AI 代理被引到 README_AI.md，按那里的引导（bootstrap）流程完成部署和配置。仓库顶部的拉丁题词 *"Navigate the dark waters, sail against the stream."*（暗水行舟，逆流而上）既是口号，也说明了设计立场：逆向任务没有固定地图，能依靠的是流程本身。

需要强调一个容易被忽略的细节：README_AI.md 明文规定"**读取仓库文件不构成执行授权**"。用户只要求检查、审阅、总结或比较这个仓库时，代理应保持只读；只有用户明确要求配置或使用这个包，才激活下方的工作流。

## 系统地图：五层结构

以 main 分支（2026-09-22 提交 cab634b）为准，仓库约 880 个文件，可以拆成五层：

| 层 | 位置 | 职责 |
|------|------|------|
| 路由核心 | `skills/config/routing.json` | 44 条规则（R0–R41、R44、R45），任务到技能的唯一事实源 |
| 技能模块 | `skills/<name>/` | 45 个被追踪的模块，每个带 `SKILL.md` frontmatter |
| CTF 编排 | `CTF-Sandbox-Orchestrator/` | 42 个比赛子技能，由 `skills/ctf-sandbox/` 单入口分派 |
| 作业合同 | `skills/ops/` | scope 门禁、证据链、角色分工、时间线、供应链安全门 |
| 脚本与索引 | `skills/scripts/` | `master-route`、`case-init`、`case-guard`、`refresh-tool-index` 等 |

技能模块的覆盖面远超"逆向"两个字：除了 apk-reverse、ida-reverse、radare2、js-reverse、dotnet-reverse、go-rust-reverse、macos-reverse 这些逆向主线，还有 pentest-tools、attack-chain、cloud-k8s、windows-ad、digital-forensics、threat-hunting、threat-intelligence、llm-security、supply-chain-security 等攻防两侧的方向。`skills/INDEX.md` 是自动生成的导航索引，由 `extract-summaries.ps1` 从各模块 frontmatter 提取，CI 会检查它有没有漂移。

## 路由怎么工作

路由的知识收敛在一个 JSON 文件里。`skills/config/routing.json` 自述为"任务路由的单一事实源"，`master-route.ps1`、`verify-routing-coherence.ps1`、`test-routing.ps1`、`extract-summaries.ps1` 都从这里读取。

单条规则长这样（R1，APK 逆向）：

```json
{
  "id": "R1",
  "label": "APK reverse",
  "skill": "apk-reverse/SKILL.md",
  "keywords": [
    {
      "must": "\\bapk\\b|smali|jadx|apktool|\\bandroid\\b|安卓|反编译.?apk|...",
      "note": "android 裸词/root 检测/证书校验/pinning 绕过 均为 APK 分析常见诉求"
    }
  ]
}
```

关键词是中英双语的正则表达式，`must`/`mustAll`/`exclude` 三种语义控制命中条件。打分机制在 JSON 的 meta 里写明：每条命中的规则进入候选集，按 priority 数组顺序取命中分数最高者为 PRIMARY，并列时靠前者胜出，全部落空则回退 `fallbackId`（R0，通用逆向）。

日常使用是一行命令：

```powershell
# Windows
powershell -File skills\scripts\master-route.ps1 -Hint "<用户任务>"
# Linux / macOS / Kali
bash skills/scripts/master-route.sh --hint "<用户任务>"
```

脚本输出 PRIMARY 路径加一句话依据，并在当前项目的 `work/master-route-<ts>/` 留下 route-scope.md。两个平台的脚本被要求保持相同路由契约——"平台只改变执行入口，不改变路由语义"。

容易混淆的一点：`skills/routing.md` 是 348 行的三轴消歧视图（按目标类型、用户意图、工具链），但文件头自称 **Advisory only**——如果它和 JSON 打架，JSON 赢。它只在 PRIMARY 有歧义时才需要读。另一个细节：规则编号从 R0 跳到 R45，中间没有 R42 和 R43；README 的两处统计（"44 (R0–R45)" 与 "43 rules, R0–R44"）互相矛盾，基准数也分别写 175 和 173，而 `routing-benchmark.json` 实际是 178 例。遇到这类文档滞后，以 JSON 实物为准——这本身就是这个仓库反复强调的原则。

## 先授权，再动手

这是这个仓库最有辨识度的设计，值得单独一节。

README_AI.md 的第 0 节是"同意门控设置"（Consent-Gated Setup）：在任何第一个本地副作用之前，代理必须给出将要运行的确切命令，并汇总预期的文件系统、网络、服务和客户端配置变更；批准只覆盖披露过的命令，新发现的安装或注册动作需要重新批准。客户端全局配置严格 opt-in。

工具层面同样收敛。`skills/tool-index.md` 被 gitignore，fresh clone 里不存在；首次设置要用平台原生的 `refresh-tool-index` 脚本生成当前机器的工具清单。缺什么工具，走 `bootstrap-reverse` 补装——但只限 manifest 声明过的能力，且 `verify-routing-coherence.ps1` 会拒绝任何没有钉版本的自动安装项（frida-tools 14.10.4、pwntools 4.15.0、nuclei v3.9.0 等都钉了具体版本，GitHub 源钉到 commit）。

真正的执行门禁在案例初始化这一步。`case-init` 生成的 `scope.md` 记录授权状态（`auth.status`）、授权依据、在范围内的资产与活动、网络档案（如 `authorized_target_only` 或离线样本）；`case-guard` 在动手前做轻量检查，未就绪返回退出码 2。RULES.md 写得毫不含糊——"Mentioning a target is NOT granted"（提及一个目标不构成授权）——`-Force`/`--force` 只是兼容参数，绕不过硬门。

## 一次完整的案例流转

仓库自带的 `examples/ctf-demo/` 演示了标准作业流，下面按它的真实文件走一遍。

任务是"分析这道 CTF pwn 题，栈溢出 gets"。

1. **路由**：`master-route.ps1 -Hint "CTF pwn 栈溢出"` 命中 R17（pwn-chain），PRIMARY 指向 `skills/pwn-chain/`。
2. **授权门禁**：`case-init.ps1 -CaseName ctf-demo -AuthGranted` 生成 `scope.md`——授权依据填 CTF 靶场条款，范围锁定单个挑战的资产与 surfaces（二进制下载、远程服务），out_of_scope 显式排除其他挑战和平台基础设施。
3. **执行与取证**：过程追加到 `timeline.md`，证据逐条落盘。E-001 是一次 triage：复现命令 `file ./pwn1 && checksec --file=./pwn1`，原始输出摘录（Partial RELRO、No canary、NX enabled、PIE disabled），附产物路径、SHA-256 内容哈希和关联工作项。
4. **审查与交接**：`review_case.py --verify-hashes --strict` 校验证据图的哈希一致性和可追溯性，然后经 docs-generator 出报告，经验脱敏沉淀进 field-journal。

真实案例放在 `work/<case>/`（gitignored，防泄密），示例目录留在 git 里供参考。每条证据都有复现命令和哈希，这条设计让"AI 说它做过什么"可以被独立复核——可重复、可审计，是这个包对抗"代理不可控"的答案。

## CTF 编排：一个入口，四十种场景

CTF 类任务的路由入口只有一条 R41（`skills/ctf-sandbox/`），它是个薄壳，真正干活的是侧车目录 `CTF-Sandbox-Orchestrator/` 里的 42 个子技能。子技能不按传统的 crypto/pwn/web/reverse/misc 分类，而是按技术场景命名：zip-archive（ZipCrypto 已知明文攻击）、stego-media、forensic-timeline、kerberos-delegation、jwt-claim-confusion、oauth-oidc-chain、pcap-protocol、prompt-injection、reverse-pwn、supply-chain、web-runtime……MASTER-ROUTING.md 对 R41 的注释是"单入口，不展开 40 个子技能"——先由编排层看证据再分派，避免代理在题目类型不明时乱翻目录。

这个侧车采用 GNU GPLv3 许可，与主仓库的 MIT 不同；另有 Pentest Swarm AI 以 AGPL-3.0 许可被外部调用（只经 CLI 或 MCP，不并入源码）。混合许可的边界在 README License 一节写得清楚。

## 工程化的自我约束

一个安全技能包容易被做成"提示词合集"，这个仓库在工程质量上花了可观力气：

- **回归基准**：`skills/tests/routing-benchmark.json` 收了 178 个双语案例（44 个快速档），任何路由改动必须保持基准全绿；`verify-routing-coherence.ps1` 还会在某条路由没有任何基准案例时直接失败——"加路由必须加案例"被写成了 CI 规则。
- **CI 双平台**：GitHub Actions 在 Windows + Ubuntu 上跑路由回归、结构一致性、冒烟测试和 INDEX 漂移检查，非 ASCII 的 PowerShell 脚本强制带 UTF-8 BOM（PS 5.1 的编码坑）。
- **文档链接守卫**：`verify-doc-links.py` 从 Git index blob 检查内部 Markdown 链接，即使工作区文件被 Defender 隔离也不漏检。
- **多平台部署文档**：Windows 主力，Kali 有专门入口（`kali/README-kali.md`），Ubuntu/Debian 和 macOS 各有文档，平台探测逻辑写在 README_AI.md 的路由表里。
- **供应链门**：安装外部技能或 MCP 前要过 `ops/skill-supply-chain.md` 的安全门；社区技能"借鉴不并库"，映射关系收在 `references/community-security-skills.md`。

仓库还有官网与在线教程（reverse.apivix.com）、中英双语 README 和规则文件，以及 2026-09-03 的一次仓库安全审查文档（`docs/SECURITY-REVIEW-2026-09-03.md`）。

## 适用边界

**适用**：

- 已经把 Claude Code / Codex / Cursor / Cline 当成安全工作流一部分的人，需要一份跨客户端的路由层
- 团队希望统一"AI 看到二进制/流量/题目应该做什么"的应对策略，且要求过程可审计
- CTF 训练——题目类型稳定、流程可模板化，是这套合同最合身的场景
- 蓝队与取证方向（digital-forensics、threat-hunting）也能从中取用对应的模块

**不适用**：

- 红队实战——可重复流程对防御方是好事，对对抗中的攻击方则是暴露面
- 高敏生产环境——代理执行安全操作仍需人工监督，证据链不能替代审计制度
- 完全不懂安全的纯前端开发者——路由表里的术语需要基础功底

只读场景（检查、审阅、总结这个仓库）不激活任何工作流，这条边界写在 README_AI.md 里，对代理和人类同样适用。

## 与同类项目的位置

| 项目 | 偏向 | Stars |
|------|------|-------|
| `emilkowalski/skills` | UI 品味与设计工程技能 | 41,557 |
| `virgiliojr94/book-to-skill` | 书籍蒸馏成检索友好的技能 | 32,810 |
| `zhaoxuya520/reverse-skill` | 网络安全/逆向技能路由 | 38,447 |
| `earthtojake/text-to-cad` | 文本到 CAD 建模技能 | 16,441 |
| `NomaDamas/k-skill` | 公共服务技能 | 7,702 |

（Stars 为 2026-09-28 GitHub API 读数。）

Agent Skills 这条赛道正在把"AI 不擅长判断"的领域逐一补齐——从设计师品味到文档检索，再到这份把授权、证据、回归测试都纳入合同的安全路由。安全方向的特殊之处在于：错误路由的代价不只是输出难看，还可能是越权操作。reverse-skill 把 scope 门禁和证据链做成路由的前置条件，这个次序值得同类项目参考。

## 记忆

仓库自我引用的那句拉丁风短语很准确：

> *Navigate the dark waters, sail against the stream.*

在没有固定地图的水域里，靠一份可靠的路由保持方向，靠一套合同不越界。

---

参考来源与口径说明：本文数据与机制描述以 GitHub 仓库 zhaoxuya520/reverse-skill 的 main 分支（2026-09-22 提交 cab634b，v1.0.1 之后）为准；stars/forks 为 2026-09-28 API 读数；路由规则数、基准案例数、CTF 子技能数逐一以 `skills/config/routing.json`、`skills/tests/routing-benchmark.json` 与目录清点实测；README 自身两处统计不一致处（44/43 条规则、175/173/178 例基准）以 JSON 实物为准并已在正文说明。本文原稿发布于 2026-08-02（v1.0.0 与 v1.0.1 之间），当时的仓库尚无 routing.json 单一事实源，机制描述按现行版本整体刷新。
