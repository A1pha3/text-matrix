---
title: "Strix：AI Agent 群跑 PoC 的渗透测试框架"
date: "2026-06-28T21:08:54+08:00"
slug: "usestrix-strix-ai-security-agent-guide"
description: "Strix 是 usestrix 开源的 AI 渗透测试框架，靠多智能体编排 + 真实 PoC 动态验证，区别于传统静态扫描。本文拆解其架构、工具栈与任务流，给出 CI/CD 接入建议。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "渗透测试", "安全自动化", "DevSecOps", "LLM 安全"]
---

# Strix：用 AI Agent 群跑 PoC，把渗透测试从周压到小时

## 一句话核心判断

Strix 不是「把扫描器套个 LLM 壳」。它把渗透测试拆成一组协同的 AI Agent（智能体），让每个 Agent 持有一部分「黑客工具栈」（HTTP 代理、浏览器、终端、Python 运行时、侦察器），再用动态可执行的 PoC（Proof of Concept，概念验证脚本）替代静态扫描的「疑似漏洞」。结果就是：同一个 web 应用，Burp/扫描器花一天出 200 条疑似，Strix 在数小时内给你一组能直接复现、能 merge 的 PR。

如果只需要静态规则扫描，Strix 不是合适选项；如果要「找出能真打进去的漏洞并自动开修复 PR」，它是当前开源生态里最完整的方案之一。

## 系统地图：四层协同

Strix 的架构可以浓缩成一张图，先放在前 20%：

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 4 │  报告与自修复  →  findings.json / PR / API 回调   │
├─────────────────────────────────────────────────────────────┤
│  Layer 3 │  Graph of Agents 协调层  →  任务派发、上下文共享  │
├─────────────────────────────────────────────────────────────┤
│  Layer 2 │  Agent 工作单元  →  Planner / Executor / Verifier │
├─────────────────────────────────────────────────────────────┤
│  Layer 1 │  黑客工具集栈  →  HTTP Proxy / Browser / Shell /  │
│           │                 Python / Recon / Code Analysis    │
└─────────────────────────────────────────────────────────────┘
```

每一层都不复杂，但缺一层就回到「扫描器 + 报告」的原点：

- **Layer 1 工具栈**：Agent 调用的是「真的黑客工具」，不是模拟器。HTTP 代理能改包重放，浏览器能跑多 tab XSS/CSRF，Shell 能直接敲命令，Python 运行时能写并执行 PoC 脚本。
- **Layer 2 Agent 单元**：每个 Agent 内部分 Planner（计划）、Executor（执行）、Verifier（验证）三段。Planner 读目标与历史，Executor 调用 Layer 1 工具，Verifier 决定是否把这条结论写进 finding。
- **Layer 3 协调层**：Graph of Agents 是 Strix 最具差异化的设计——不同 Agent 承担不同攻击面（鉴权、注入、业务逻辑、客户端），并行跑，共享攻击发现，相互触发下一步。
- **Layer 4 报告层**：findings 是结构化、可机器读的产物；和 [app.strix.ai](https://app.strix.ai) 平台打通后可一键生成修复 PR，也能直接喂给 GitHub Actions。

整体代码规模约 56 万行 Python（另有 Jinja 模板、Shell、Dockerfile），核心目录 `strix/` 承担 Agent 运行时，`containers/` 提供隔离沙箱，`benchmarks/` 存放评估数据集，`docs/` 是面向用户的文档源。

## 为什么是「AI Agent 群」，而不是「一个很长的 Prompt」

很多人会把 Strix 类工具想象成「给 GPT 一个 5 万字 prompt，让它帮我做渗透」。但实际渗透测试不是单轮推理：

1. **攻击是链式动作**：找到注入点 → 写 PoC → 验证可利用 → 升级权限 → 横向移动。这条链每一步都要看前一步的输出，单个 LLM 调用记不住也调不动。
2. **验证要可执行**：扫描器报「可能存在 SQL 注入」是「疑似」；Agent 必须真去构造 payload、真打到目标、真看回包。这是 Layer 2 Verifier 存在的理由。
3. **多攻击面要并行**：一个现代 web 应用同时存在 IDOR（Insecure Direct Object Reference，不安全直接对象引用）、SSRF（Server-Side Request Forgery，服务端请求伪造）、XSS、业务逻辑漏洞。单 Agent 串行跑要数小时，并行 Agent 群可以压缩到分钟级。

Strix 的做法是把这些特性显式建模：

- 用 Graph of Agents 表达「多攻击面 + 协同 + 共享上下文」，而不是把所有事情塞给一个超长 system prompt。
- 用沙箱 + Docker 把 Agent 的「Shell 执行 / Python 执行 / 浏览器交互」包起来，避免 LLM 在执行探测命令时把宿主机搞坏。
- 用 PoC 验证作为「采纳门槛」，Verifier 跑不通的 finding 不入库。这一条直接消除了传统 SAST（Static Application Security Testing，静态应用安全测试）/ DAST（Dynamic Application Security Testing，动态应用安全测试）报告里大量 false positive（误报）。

## 关键子系统拆解

### 1. Graph of Agents：不是「多实例」，是「协同图」

Strix 不是简单开多个 Agent 并行跑就完事。它维护一张「Agent 协同图」，节点是不同攻击面 Agent，边是「信息传递 + 触发」关系。比如：

- 鉴权 Agent 发现某端点未鉴权 → 把端点 URL 传给 IDOR Agent 深入测试。
- SSRF Agent 拿到内网 IP 段 → 派新 Agent 去探测可访问的内部服务。
- 客户端 Agent 找到 XSS sink（可触发脚本执行的输出点） → 把 sink URL 与上下文传给业务逻辑 Agent 配合测试复杂流程。

这种「一个发现驱动下一个 Agent」的设计，让 Graph 不是静态的「5 个 Agent 同时跑」，而是动态生长的任务图。这也是为什么 README 单独把它列为亮点。

### 2. 黑客工具集栈：每样都能用

Layer 1 不是装饰，每一类工具都有具体的攻击场景：

| 工具 | 调用场景 | 典型用法 |
|------|----------|----------|
| HTTP Proxy | 抓包、改包、重放 | Burp 风格的请求/响应拦截与变异，Agent 可读写请求头与 body |
| Browser Automation | 客户端漏洞、鉴权流 | 多 tab 跑 XSS、CSRF、登录态跳转 |
| Terminal | 系统层探测 | 执行命令、读配置文件、检测开放服务 |
| Python Runtime | PoC 编写 | 写并运行利用脚本，不是只生成代码片段 |
| Reconnaissance | 攻击面映射 | 子域名枚举、端口扫描、技术栈指纹 |
| Code Analysis | 源码审计 | 静态 + 动态结合，定位可疑代码段 |

这套栈让 Agent 几乎可以复现一个真实渗透工程师的工作台，而不是被限制在「只能读 README 的 LLM」。

### 3. PoC 验证：把 false positive 关在门外

这是 Strix 最值钱的工程取舍：每条 finding 必须附带可执行的 PoC。Verifier 在沙箱里跑 PoC，看目标系统是否真的「被影响」。如果 PoC 跑不通或环境不符，这条 finding 不会进报告。

代价是 Agent 要花更多时间与 token，但它换来的是「报告里的每条问题都能直接 reproduce」。DevSecOps 团队拿到这种报告的修复意愿会显著高于 SAST 报告。

### 4. CI/CD 与 Headless 模式

`strix -n`（non-interactive，无交互模式）让 Agent 不开 TUI（Terminal UI，终端用户界面），结构化输出 finding 并以非零退出码报错，能直接嵌入 GitHub Actions：

```yaml
name: strix-penetration-test
on:
  pull_request:
jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0
      - name: Install Strix
        run: curl -sSL https://strix.ai/install | bash
      - name: Run Strix
        env:
          STRIX_LLM: ${{ secrets.STRIX_LLM }}
          LLM_API_KEY: ${{ secrets.LLM_API_KEY }}
        run: strix -n -t ./ --scan-mode quick
```

在 PR 场景下，Strix 自动用 diff-scope（差异范围）把扫描限定在本次变更的文件，`--diff-base` 可手动指定基线分支（注意：`fetch-depth: 0` 必填，否则 diff-scope 解析失败）。这条 CI 集成路径让 Strix 能替代部分传统 DAST 流水线。

## 一个任务流案例：跑一次 PR 扫描

把抽象架构落到一次实际执行：

1. **触发**：GitHub PR 触发 Actions，`strix -n -t ./ --scan-mode quick` 启动。
2. **环境准备**：脚本自动拉取沙箱 Docker 镜像（首次约数分钟，后续秒级复用）。
3. **基线 diff**：读取 PR diff，确定本次变更涉及的端点与文件，作为初始攻击面。
4. **Agent 群初始化**：Graph 启动若干 Agent，对应鉴权、注入、客户端、业务逻辑等不同攻击面。
5. **第一轮探索**：各 Agent 调 Layer 1 工具（HTTP 代理、shell、code analysis）收集信息。Reconnaissance Agent 先跑攻击面映射，结果共享给其他 Agent。
6. **协同放大**：某个 Agent 发现 IDOR → 把端点与上下文写入共享存储 → 鉴权 Agent 据此深入 → 触发新 Agent 去测试关联的横向越权。
7. **PoC 验证**：每条疑似结论由 Verifier 跑一遍 PoC，不通过则丢弃。
8. **报告输出**：通过的 findings 写进 `strix_runs/<run-name>/`，结构化 JSON + 人类可读报告，非零退出码触发 CI 失败。
9. **可选修复**：若接入 app.strix.ai 平台，验证通过的 finding 可自动转 PR。

整个流程在 PR 规模下通常是分钟级；针对完整应用的「标准」扫描是小时级。

## 配置与模型选择

最小配置两个环境变量即可启动：

```bash
export STRIX_LLM="openai/gpt-5.4"
export LLM_API_KEY="your-api-key"
```

支持的 provider 通过 [LiteLLM](https://github.com/BerriAI/litellm) 接入，OpenAI、Anthropic、Google、Vertex AI、Bedrock、Azure、本地 Ollama/LMStudio 都行。README 推荐 OpenAI GPT-5.4、Anthropic Claude Sonnet 4.6、Google Gemini 3 Pro Preview。

可选配置：

- `LLM_API_BASE`：本地模型的自定义端点。
- `PERPLEXITY_API_KEY`：启用搜索增强。
- `STRIX_REASONING_EFFORT`：控制推理深度，默认 high，quick 模式为 medium。

配置会自动持久化到 `~/.strix/cli-config.json`，下次启动免重输。

## 常见使用模式

| 场景 | 命令 | 备注 |
|------|------|------|
| 本地代码扫描 | `strix --target ./app-directory` | 最常见用法 |
| 远端仓库审计 | `strix --target https://github.com/org/repo` | 直接对 GitHub 仓库 |
| 黑盒 web 评估 | `strix --target https://your-app.com` | 在线应用 |
| 灰盒鉴权测试 | `strix --target https://your-app.com --instruction "user:pass"` | 自带凭据 |
| 多目标 | `strix -t https://github.com/org/app -t https://your-app.com` | 源码 + 部署环境同时跑 |
| 白盒源码扫描 | `strix --target ./app-directory --scan-mode standard` | 深度静态 + 动态 |
| 无交互跑批 | `strix -n --target https://your-app.com` | 适合 CI |
| PR 差异扫描 | `strix -n --target ./ --scan-mode quick --scope-mode diff --diff-base origin/main` | 只看本次变更 |

## benchmark 与适用边界

仓库自带 `benchmarks/` 目录，但 README 没有公开任何「胜率/覆盖度」等对比数字。所有 benchmark 都基于自有数据集，未与 ZAP、Burp Suite、Semgrep 等做横向 PK。

**不能推出的结论**：

- Strix 在 CVE（Common Vulnerabilities and Exposures，公共漏洞编号）覆盖度上不一定优于传统 SAST/DAST 工具。
- 报告里没有 finding 并不意味着安全，仅代表当前 Graph 没找到可验证漏洞。
- 不同 LLM provider 的实际效果差异显著，简单模型（如本地 7B）很可能跑不出可用 PoC。

**应该接受的边界**：

- 仅测试你有授权的应用，否则等同于未经授权的渗透测试。
- PoC 验证要求目标系统能被沙箱访问，纯内网且无 Agent 网络的环境需要自建部署。
- 修复建议由 LLM 生成，质量参差，关键漏洞仍需人工 review。

## 采用顺序与决策建议

如果你正考虑把 Strix 引入团队，按这个顺序推进：

1. **先用 `strix --target https://your-staging-app.com` 跑一次完整扫描**，验证在你的真实应用上 false positive 率与 finding 质量。这是 PoC，决定要不要继续。
2. **接入 GitHub Actions**，用 `scan-mode quick` 跑 PR；只在 critical finding 时阻断合并，其他 finding 仅通知。这一步把 Strix 从「一次性工具」变成「持续门禁」。
3. **接入 app.strix.ai 平台**，让通过的 finding 自动开修复 PR。注意 review 这些 PR，不是所有自动修复都能直接 merge。
4. **替换部分商业 DAST 工具**：如果你目前每月烧在商业 DAST 上，Strix 能覆盖其中 60-80% 的常规扫描场景。
5. **保留人工渗透测试**：合规要求、对抗性测试、复杂业务逻辑，仍需要真人红队。Strix 是「常规扫描 + 回归验证」的加速器，不是红队替代品。

## 它适合谁、不适合谁

**适合**：

- 安全团队人手紧、需要自动化日常漏洞扫描 + PR 修复流程。
- DevSecOps 团队想在 CI 里跑「能复现的漏洞检查」而不是「疑似漏洞清单」。
- 对 AI Agent 编排感兴趣的工程师，把 Strix 当作 LLM Agent 工程化的参考实现。

**不适合**：

- 只想要静态规则扫描、不打算给 LLM 跑命令的环境（合规/数据外流顾虑）。
- 网络隔离严格、沙箱无法触达目标系统的内网场景。
- 把 Strix 当万能红队工具、对抗性测试请留给专业渗透工程师。

## 项目成熟度

- 26k+ stars、2.9k+ forks、Apache-2.0。
- v1.0.0 于 2026-05-26 发布，2026-06-09 已是 v1.0.4，迭代活跃。
- 16 个 release，版本节奏稳定。
- 最近 push 时间为 2026-06-26，维护活跃。
- 致谢里点名依赖了 LiteLLM、Caido、Nuclei、Playwright、Textual——都是成熟开源项目，工程基础扎实。

## 一句话总结

Strix 是「用 AI Agent 群 + 真实 PoC 验证」把渗透测试从「扫描器报疑似」推进到「报告里每条都能复现」的开源框架。如果你要的是「能直接 merge 的安全修复」而不是「安全团队的待办清单」，它值得先跑一次完整扫描验证效果。
