+++
github_repo = "KeygraphHQ/shannon"
source_key = "gh:KeygraphHQ/shannon"
date = '2026-05-17T20:15:00+08:00'
draft = false
title = 'Shannon：开源 AI 渗透测试引擎'
slug = 'keygraphhq-shannon-graph-ai-agent'
description = 'Shannon 是 KeygraphHQ 开源的自主白盒 AI 渗透测试工具，坚持 No Exploit No Report：只有打出可复现 PoC 的漏洞才进报告。本文按 v3.3.0 解析其双线六阶段架构、Doyensec 对比数据与 CI/CD 集成。'
categories = ['技术笔记']
tags = ['安全', '渗透测试', 'AI Agent', '开源']
+++

# Shannon：开源 AI 渗透测试引擎

团队用 Claude Code 和 Cursor 日以继夜地发版，渗透测试却一年只做一次——剩下 364 天，漏洞可能正随每次发布悄悄进入生产环境。KeygraphHQ 在 2025 年 9 月底开源的 [Shannon](https://github.com/KeygraphHQ/shannon) 对准的正是这段空档：一款自主运行的白盒 AI 渗透测试工具，读你的源码找攻击路径，再对运行中的应用真实执行利用，报告里只收有可复现 PoC 的漏洞。项目一年拿下 48,456 stars（2026-09-29 核实），增速背后是同一个痛点在大量团队身上重演。

本文数据按 v3.3.0（2026-09-21 发布）核实。Shannon 迭代极快，5 月写作本文时的 v1.2 与今天的 3.x 已是两代产品，文中会注明关键分野。

## 基本信息

| 项目 | 内容 |
|------|------|
| 仓库 | [KeygraphHQ/shannon](https://github.com/KeygraphHQ/shannon) |
| 语言 | TypeScript |
| 许可证 | AGPL-3.0（开源版）；商业许可另谈 |
| 最新版本 | v3.3.0（2026-09-21） |
| 开发者 | [Keygraph](https://keygraph.io) |

版本演进的一条主线值得先交代：v1.x 构建在 Anthropic 的 Claude Agent SDK 上，官方推荐 Anthropic API Key，也提供 AWS Bedrock 和 Google Vertex AI 路线；v1.9.0（2026-07-04）是最后一个 SDK 版本，此后的 2.x/3.x 转到底层开源的 [Pi](https://github.com/earendil-works/pi) harness 上（README 致谢名单里的第一位），模型从此随便换。2026-09-02 的 v3.0.0 加入 agentic SAST（静态应用安全测试），并重建了 CLI、补上原生 CI/CD 和 SARIF 输出。

## 定位：No Exploit, No Report

传统扫描器的痛点是误报：一份"理论风险清单"扔过来，工程师逐条排查后发现大半打不通，几次之后清单就没人看了。Shannon 的应对是把"证明"设为硬门槛——**No Exploit, No Report**：源码分析和运行时侦察产出的都只是"可利用路径假设"，每个假设必须由利用 Agent 实际打出可复现的 PoC 才能进报告，打不出来的直接丢弃。

代价同样明确：它只能用于**白盒场景**——你得提供目标应用的源码仓库；而且它是主动攻击工具，不是被动扫描器（详见后文使用注意）。

官方对边界也很坦白：Shannon 不替代人类渗透测试专家。关键系统仍需要懂业务的专家做深度评估，Shannon 补的是覆盖不到的长尾——大量内部应用、API 和快速迭代的服务，此前几乎从未被测过。它的目标是把渗透测试左移进 SDLC，跟着发布节奏跑。

## 架构：两条分析线，六步流水线

v3.x 的架构比 v1.x 的"五阶段串行"多出一条独立的代码分析线和一道汇合工序：

```
             ┌─→ 侦察 + 并行漏洞分析 ─┐
  源码仓库 ──┤                        ├→ 发现汇合（合并去重）→ 利用队列 → 利用 Agent ─┬→ 报告（PDF/Markdown/SARIF）→ CI/CD 门禁
             └─→ Agentic 代码分析 ───┘            （对照运行中的应用）               └→ 打不出来的丢弃
```

**第一步：侦察 + 并行漏洞分析。** 用浏览器自动化真实探索运行中的应用，把运行时行为关联回源码；随后 5 个专项 Agent 并发跑 Injection、XSS、SSRF、Authentication、Authorization 五个方向，对注入和 SSRF 还会做结构化数据流分析，把用户输入一路追到危险的汇聚点（Sink）。

**第二步：Agentic 代码分析（v3.0 新增）。** 独立于动态侦察，直接读源码映射应用架构、信任边界、暴露接口、依赖、数据流和高风险资产，再对可疑点发起针对性调查。这条线是 3.0 "deeper security code analysis" 的实体。

**第三步：发现汇合。** 两条线各产出一批候选，合并、去重、按可打性分组，汇成利用队列。

**第四、五步：利用与验证。** 利用 Agent 对着运行中的应用执行真实攻击——浏览器自动化、命令行工具、自定义脚本都上；任何证明不了的候选在验证环节被丢弃。只有验证存活的发现才计入报告和 CI/CD 严重度门禁。

**第六步：报告。** 输出带证据的 PDF 和 Markdown 报告，外加结构化 JSON 和 SARIF 2.1.0（exploit 模式扫描默认输出 SARIF，下游代码扫描平台直接可读）。

整次扫描跑在一个临时 Docker 容器里：目标仓库以只读方式挂载，结果写入本地 workspace，扫描中断可从 workspace 恢复，不重复已完成的工作。

### 一次扫描的完整路径

用 Doyensec 对比研究中 Shannon 打 Photoview 2.4.0 的真实案例把流水线串起来：侦察阶段拿到登录后的应用地图，注入分析 Agent 在相册下载路由的数据流里发现用户输入未经充分过滤直通 SQL 语句，产出一条"布尔盲注"假设；利用 Agent 构造 payload 实际执行，把端点变成布尔 oracle——请求返回的真假逐位还原出整库数据，PoC 成立；最终报告记录为 INJ-01，与 Photoview 维护者随后修复的 CVE 级问题（CVSS 9.8，PR #1453）对上了号。三个不同模型跑出的三次扫描都抓住了这颗 Critical，这是"假设 → 验证 → 报告"全链路的一次完整走通。

## Benchmark：先看测的是什么

Shannon 当前 README 引用的核心数据来自 [Doyensec 对比研究](https://doyensec.com/resources/ComparingAIApplicationSecurityTestingPlatforms_Doyensec.pdf)的跟进实验：Doyensec 先用 Aikido 和 XBOW 两个商业平台（每台 **$4,000/次**）测试了开源相册应用 Photoview 2.4.0，Shannon 团队随后用 v3 对同一部署、同一版本跑了三个模型，人工核验所有发现：

| | Shannon v3（DeepSeek v4 Flash） | Shannon v3（Grok 4.6） | Shannon v3（Claude Opus 5） | Aikido | XBOW |
|--|--|--|--|--|--|
| 成本 | $6.10 | $35.07 | $115 | $4,000 | $4,000 |
| 耗时 | 2h 37m | 5h 26m | 2h 24m | < 8h | 约 2 天 |
| 报告数 | 18 | 10 | 24 | 32 | 7 |
| 真阳性 | 18 | 10 | 23 | 32 | 7 |
| 假阳性 | 0 | 0 | 1 | 0 | 0 |

怎么读这组数字：

- **测的是什么**：单一应用（Photoview 2.4.0）、固定部署、只给管理员凭据，比拼的是"给定源码和运行实例后的发现质量与成本"，不是扫描器的全面覆盖能力。
- **数字反映系统的哪部分**：假阳性控制主要来自 No Exploit, No Report 机制——三次 Shannon 扫描合计 52 个报告仅 1 个假阳性；模型强弱则决定覆盖深度，以 Photoview 后来实际修复的 7 个漏洞为参照，Opus 抓到 6/7，Grok 和 DeepSeek 各 3/7，但那颗 CVSS 9.8 的预认证 SQL 注入三个模型全部命中。
- **不能推出什么**：单应用样本推不出对任意技术栈的召回率；成本差 35–656 倍的对比也不完全等价——Aikido/XBOW 是含人工流程的商业服务，Shannon 是需要自己搭环境、自付模型费的工具；耗时口径也不一致（XBOW 从启动到交付报告跨了两天）。

唯一那个假阳性能说明短板所在：Opus 把一个仅管理员可用的目录注册功能（`userAddRootPath`）误读为漏洞——同一段代码在这个应用里是特性、在另一个应用里可能是可利用点，区分二者需要业务语境，这正是当前模型理解的薄弱处。

顺带修正一个历史数据：本文初版引用的"XBOW 基准 96.15%（100/104 exploits）"出自 v1.2.0 时代的 README，测的是无提示、源码感知的 XBOW 变体，属项目自测口径；v3.x 的 README 已撤下这组数字，改用上述可独立验证的对比实验。旧数据在当时的文档里属实，但今天评估 Shannon 应以上面的新数据为准。

另一个实用结论来自官方对 ensembling 的讨论：Grok 与 DeepSeek 各自抓到 7 个修复漏洞中的 3 个、重叠不全，合并两份报告即可以 **$41** 覆盖 4/7。Shannon 尚未内置多模型编排，但 BYOM 加标准 SARIF 输出让"多模型各跑一遍再合并去重"在 CI 里并不难实现。

## 隐私与模型：BYOK 是底线设计

Shannon 在数据面上做得很干净：扫描跑在你自己的基础设施里，结果存本地，模型请求从你的机器直连你配置的 endpoint——Keygraph 不经手源码，也不代理模型流量。把 endpoint 指向本地服务，流量甚至不出内网。

模型选择完全放开：Anthropic、OpenAI、xAI、AWS Bedrock 内置直连，Pi harness 目录里的其他 provider 按同一 `<provider>:<model-id>` 格式配置；Ollama、vLLM、LM Studio 起的本地模型走 OpenAI 兼容接口即可，OpenRouter、LiteLLM 这类网关经自定义 base URL 接入。一次扫描全程用同一个模型配置。留意一点：Anthropic 和 OpenAI 对网络安全类工作负载有实时安全策略，首次使用前需按官方指引完成合规流程，否则扫描可能中途被打断。

订阅用户还有捷径：ChatGPT Plus/Pro 和 xAI 订阅可直接用作模型后端；Claude Code 订阅不支持，得退回 v1.9.0。

## CI/CD：从手动命令到发布门禁

v3.0 之后 CI/CD 不再是商业版专属。官方提供 [GitHub Action](https://github.com/KeygraphHQ/shannon-action) 和 GitLab CI 组件，支持 PR、发布、定时三种触发：

```yaml
- name: Run Shannon
  uses: KeygraphHQ/shannon-action@v1
  with:
    url: https://staging.example.com
    api-key: ${{ secrets.SHANNON_AI_API_KEY }}
    fail-on-severity: high
    upload-sarif: true
```

门禁的判定口径和直觉一致：代码分析产出的**假设**不会让流水线失败，只有 `status: exploited` 的确认发现才计入严重度阈值——`fail-on-severity: high` 意味着流水线只被实证的高危漏洞卡住，误报不再阻塞发布。报告（PDF/Markdown/SARIF）与扫描日志都保留为 pipeline artifact，SARIF 可直接发布到 GitHub code scanning。

## 快速上手

```bash
# 交互式 launcher，引导完成配置和首次渗透测试
npx @keygraph/shannon@latest

# 或分步执行
npx @keygraph/shannon@latest setup
npx @keygraph/shannon@latest start -u https://your-app.com -r /path/to/repo
```

依赖 Docker（worker 容器）和 Node.js 18+。`start` 会从 Docker Hub 拉取 worker 镜像，启动本地基础设施，把目标仓库只读挂载进临时容器，结果写入本地 workspace。想改源码则走 `git clone` + `pnpm install && pnpm build` 路线。

## 使用注意

Shannon **会真实发起攻击**：利用 Agent 会注册用户、提交表单、修改应用状态、触发对外请求。官方红线很清楚：

- 只对沙盒、staging 或本地开发环境跑，用可丢弃的数据
- 只测你拥有或拿到**明确书面授权**的系统，切勿对准生产环境
- 完整扫描约 1–1.5 小时，按模型定价产生 API 费用
- 不要扫描不可信或带敌意的代码库——读源码的 AI 工具可能被仓库内容注入指令
- 报告仍需人工复核，LLM 生成的细节可能有弱依据或错误

## 采用建议

把上面这些拼起来，Shannon 的合理用法是一条**分层测试策略**：

1. **日常高频**：用 DeepSeek 这档便宜模型（单次约 $6）对 staging 环境常态扫描，配合 CI 门禁卡住高危发现——它抓得住最要命的漏洞，成本允许每天甚至每次发布都跑。
2. **定期深扫**：每周或每个重要版本用 Opus 这档强模型跑一轮（单次约 $115），覆盖更隐蔽的高危问题——参照实验里它抓到了 7 个已修复漏洞中的 6 个。
3. **进阶玩法**：多模型各跑一遍再合并 SARIF 结果，用几十美元逼近单一强模型的覆盖率。

适合先上的是维护着持续交付 Web 应用/API、又养不起全职红队的小团队——这正是"长尾无人测试"的重灾区。重合规、要集中治理和多团队统一漏洞管理的组织，看的应该是托管的 Keygraph Enterprise Platform 而非这份开源代码。至于指望它替代渗透测试专家：官方自己都不这么宣称，你也别这么指望。

> 项目地址：[https://github.com/KeygraphHQ/shannon](https://github.com/KeygraphHQ/shannon)
