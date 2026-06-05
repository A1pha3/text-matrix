+++
date = '2026-05-17T20:15:00+08:00'
draft = false
title = 'Shannon：开源 AI 渗透测试引擎'
slug = 'keygraphhq-shannon-graph-ai-agent'
description = 'Shannon 是 KeygraphHQ 开源的自主白盒 AI 渗透测试工具，基于源码分析主动执行漏洞利用，采用 No Exploit No Report 策略压低误报率。'
categories = ['技术笔记']
+++

# Shannon：开源 AI 渗透测试引擎

在软件开发节奏越来越快的今天，渗透测试一年一次的安全差距愈发显眼。KeygraphHQ 开源的 [Shannon](https://github.com/KeygraphHQ/shannon) 正是为填补这个空白而生——一款自主运行的白盒 AI 渗透测试工具，直接分析源码、主动执行漏洞利用，报告里只有经过实战验证的发现。

## 基本信息

| 项目 | 内容 |
|------|------|
| 仓库 | [KeygraphHQ/shannon](https://github.com/KeygraphHQ/shannon) |
| 语言 | TypeScript |
| 许可证 | AGPL-3.0（Lite）/ 商业版（Pro）|
| 开发者 | Keygraph |

## 核心定位：白盒 + 主动利用

Shannon 的思路很明确：不搞理论推断，直接对着运行中的应用"真打"。它先把源码跑一遍梳理出攻击向量，再通过浏览器自动化和命令行工具实际执行注入、XSS、SSRF、身份验证绕过等攻击。只有真正打出 PoC 的漏洞才会出现在最终报告里——没打成功的直接丢弃。

这种 **"No Exploit, No Report"** 策略从根本上压低了误报率，代价是它只能用于**白盒场景**（有源码访问权限的应用）。

## 五阶段架构

Shannon 采用了多 Agent 编排架构，整个流程分五个阶段：

```
源码扫描 → 侦察 → 并行漏洞分析 → 并行利用 → 报告生成
```

**阶段 1：Pre-Reconnaissance（源码预扫描）**
分析源码，识别框架类型、入口点、潜在攻击面，为后续所有 Agent 打基础。

**阶段 2：Reconnaissance（攻击面映射）**
结合预扫描结果，用浏览器自动化对运行应用进行真实探索，输出详细的端点地图、API 接口和认证机制信息。

**阶段 3：Vulnerability Analysis（并行漏洞分析）**
5 个 Agent 并发运行，分别负责 Injection、XSS、Auth、Authz、SSRF 五个方向。对于 Injection 和 SSRF 这类漏洞，会做结构化的数据流分析，把用户输入追踪到危险 Sink，输出"可利用路径假设清单"。

**阶段 4：Exploitation（利用验证）**
继续并行，接收上一步的假设路径，通过浏览器自动化、CLI 工具和自定义脚本实际执行攻击。把"假设"变成"可复现的 PoC"。

**阶段 5：Reporting（报告生成）**
整合所有成功利用的证据，清理噪声和幻觉内容，输出专业 pentest 级别报告，每条发现都带可直接 copy-paste 的 PoC。

## 功能亮点

- **全自动运行**：一条命令启动完整渗透测试，支持 2FA/TOTP 登录（含 SSO）自动处理
- **并行处理**：5 个漏洞类别并发分析 + 5 个利用任务并发执行
- **PoC 可复现**：最终报告只含经过实战验证的漏洞，无理论风险
- **OWASP 覆盖**：Injection、XSS、SSRF、身份验证/授权四类全覆盖，持续扩展中
- **Benchmark 表现**：在 XBOW 安全基准测试的无提示源码感知变体上得分 **96.15%（100/104 exploits）**

## 双版本产品线

| | Shannon Lite | Shannon Pro |
|--|--------------|-------------|
| 许可证 | AGPL-3.0 | 商业版 |
| 分析方式 | 代码审查提示词 | CPG 全链路数据流 SAST |
| 覆盖范围 | AI 渗透测试 | SAST + SCA + Secrets + 业务逻辑安全测试 |
| 静态-动态关联 | ❌ | ✅ 静态发现注入 Exploitation 队列并验证 |
| 部署方式 | CLI / npx | 托管云或自托管 Runner |
| CI/CD 集成 | 手动 | 原生 GitHub PR 扫描 |

Shannon Pro 的亮点在于**静态-动态关联**——通过 Code Property Graph（AST + 控制流图 + 程序依赖图）做深度数据流分析，发现的漏洞不是报"理论风险"，而是被送进对应的 Exploitation Agent 实打实打一遍，打通了直接给出源码行号和 PoC。

## 快速上手

```bash
# 方式一：npx（推荐，无需本地编译）
npx @keygraph/shannon setup
npx @keygraph/shannon start -u https://your-app.com -r /path/to/repo

# 方式二：从源码编译
git clone https://github.com/KeygraphHQ/shannon.git
cd shannon
pnpm install && pnpm build
./shannon start -u https://your-app.com -r /path/to/repo
```

全程依赖 Docker，系统要求 Node.js 18+、pnpm（源码模式）、AI Provider 凭证（Anthropic API Key 推荐）。

## ⚠️ 使用注意

Shannon **会主动发起攻击**，不适合对着生产环境跑。官方强烈建议：
- 仅在沙盒、预发或本地开发环境使用
- 最高隔离级别：在 VM 里运行
- 必须持有目标系统的**明确书面授权**

此外，报告依然需要人工复核——LLM 在报告生成阶段仍可能产生幻觉内容。

## 小结

Shannon 的价值在于把渗透测试这件事从"一年一次的专业项目"变成了"随时可触发的自动化流水线"。配合 CI/CD，团队可以在每次发布前获得一份经过实战验证的安全报告，而不是一份理论风险清单。42K ⭐ 的社区认可也侧面说明了市场对这类工具的强烈需求。

如果你在维护一个需要常态化安全测试的 Web 应用或 API，Shannon 值得放进工具箱。

> 项目地址：[https://github.com/KeygraphHQ/shannon](https://github.com/KeygraphHQ/shannon)