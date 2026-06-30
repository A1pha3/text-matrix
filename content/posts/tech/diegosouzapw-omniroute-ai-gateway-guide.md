---
title: "diegosouzapw/OmniRoute：聚合 236 家 AI 提供商的免费 AI 网关深度拆解"
date: "2026-06-30T21:10:22+08:00"
slug: "diegosouzapw-omniroute-ai-gateway-guide"
description: "OmniRoute 是一个聚合 236 家 AI 厂商（含 50+ 免费层）的统一 AI 网关，8k Stars、TypeScript、MIT 协议，支持 Claude Code、Codex、Cursor、Cline 等 16+ 编程代理通过单一端点接入，包含 RTK+Caveman 压缩、4 级自动回退、A2A/MCP 协议适配，本文拆解其定位、4 层路由策略、压缩机制与运行边界。"
draft: false
categories: ["技术笔记"]
tags: ["OmniRoute", "AI 网关", "Claude Code", "OpenAI Codex", "路由策略", "MCP"]
---

# diegosouzapw/OmniRoute：聚合 236 家 AI 提供商的免费 AI 网关深度拆解

## 这篇文章解决什么问题

2026 年的 AI 开发工具生态有一个结构性问题：Claude Code、Codex、Cursor、Cline、Copilot、Antigravity 这些编程代理各自有独立的接入配置、不同的协议面（OpenAI Chat Completions / Responses / Claude Messages / Gemini）、各自的 API key 管理方式。手上同时跑 3 个以上代理的时候，光是配置切换就够烦的，更不用说每个代理背后还要选模型厂商。

OmniRoute 把这件事压成一个统一端点：本地起一个 `http://localhost:20128/v1`，所有代理都指向这里，背后由 OmniRoute 决定调哪家厂商、哪个模型、怎么回退、怎么压 token。

读完后你能：

1. 看清 OmniRoute 在 AI 网关生态里的位置（不是替代品，而是统一接入层）
2. 理解 4 级自动回退（Subscription → API → Cheap → Free）的触发条件
3. 知道 RTK + Caveman 压缩在哪些场景下能省 token，哪些场景不能
4. 评估在你的工作流里接 OmniRoute 的工程代价与收益

## 项目基本事实

| 指标 | 数值 |
|---|---|
| 仓库 | [diegosouzapw/OmniRoute](https://github.com/diegosouzapw/OmniRoute) |
| Stars / Forks | 8.1k / 1.4k |
| 语言 | TypeScript |
| License | MIT |
| Node 要求 | ≥ 22.0.0 |
| 测试 | 14,965 tests |
| 首次提交 | 2026-02-13 |

仓库创建于 2026 年 2 月，仅 4 个多月就积累 8k Stars——增长曲线本身就说明这个痛点被大量开发者认领。它跟 CLIProxyAPI、9Router 等是同代产品，但功能维度上比单一中转工具覆盖更广：除了多协议翻译外，还内置路由策略、压缩、监控、A2A/MCP 适配。

## 系统地图

```
┌──────────────────────────────────────────────────────────┐
│        你的 IDE / CLI  (Claude Code, Cursor, Cline…)       │
└─────────────────────────┬──────────────────────────────────┘
                          │ http://localhost:20128/v1
                          ▼
┌──────────────────────────────────────────────────────────┐
│                  OmniRoute — 智能路由器                    │
│  RTK + Caveman 压缩 · 17 种路由策略                        │
│  Circuit breaker · TLS stealth · MCP · A2A · Guardrails   │
└─────────────────────────┬──────────────────────────────────┘
        ┌─────────────┬────┴────────┬─────────────┐
        ▼ Tier 1      ▼ Tier 2      ▼ Tier 3       ▼ Tier 4
   SUBSCRIPTION     API KEY        CHEAP          FREE
   Claude Code,     DeepSeek,      GLM $0.5,      Kiro, Qoder,
   Codex, Copilot   Groq, xAI      MiniMax $0.2   Pollinations
   配额耗尽 ─▶     预算触顶 ─▶    预算触顶 ─▶   永远在线
```

OmniRoute 不是单一组件，它是一个聚合运行时：HTTP 服务端 + 路由引擎 + 压缩管道 + 协议翻译层 + Dashboard + 客户端 CLI 工具，一站式打包。

## 核心能力

### 一端点统一所有代理

`/v1` 端点对外同时支持：

- OpenAI Chat Completions 协议
- OpenAI Responses 协议
- Anthropic Claude Messages 协议
- Google Gemini 协议

这意味着 Claude Code（默认 Anthropic 协议）、Cursor（OpenAI 协议）、Codex（OpenAI Responses）、Cline（OpenAI）、Copilot（OpenAI）全部指向同一个 `localhost:20128/v1`，剩下的协议翻译由 OmniRoute 内部完成。

### 4 级自动回退（核心路由策略）

OmniRoute 把所有可用的 provider 归到 4 个 tier，按顺序尝试：

| Tier | 类别 | 例子 | 触发回退条件 |
|---|---|---|---|
| 1 | SUBSCRIPTION | Claude Code、Codex、Copilot 订阅 | 配额耗尽 / rate limit |
| 2 | API KEY | DeepSeek、Groq、xAI | 预算上限 / 月度 cap |
| 3 | CHEAP | GLM、MiniMax（按 token 极低价计费） | 预算上限 |
| 4 | FREE | Kiro、Qoder、Pollinations、LongCat | 永远在线（不主动回退） |

每级回退在毫秒级完成——Tier 1 报 429 或 quota exceeded 的瞬间，Tier 2 顶上；Tier 2 预算耗尽，Tier 3 顶上；Tier 3 不可用，Tier 4 顶上。对于使用者来说，看到的体验是"一直在响应"，但背后实际调了哪家是动态决定的。

OmniRoute 提供了 17 种路由策略（README 中列出），覆盖按成本、按延迟、按模型能力、按 fallback 顺序等不同维度。具体策略组合通过命令行参数选择。

### RTK + Caveman 压缩

RTK（Request Token Knife）和 Caveman 是 OmniRoute 内置的两套 token 压缩管道：

- **RTK**：针对 `git diff`、`grep` 输出、stack trace、日志这类"工具输出"的压缩，通过去除冗余行、统一格式、去除无信息字符的方式压低 token 数。
- **Caveman**：基于语言模型的语义压缩，把冗长的工具输出压缩成"紧凑但语义可还原"的格式。

README 给出的数字是 **15–95% 的 eligible token 节省，平均约 89%**（基于工具调用密集的会话）。节省幅度取决于会话中工具输出占比——纯对话型会话几乎不受益，工具密集型会话能显著压低 token 用量。

压缩是在请求送出前在 OmniRoute 这一层做的，对代理和上游厂商透明。但要注意：压缩有损语义边界（尤其是 Caveman 的语义压缩），对某些任务（如代码评审、长文档分析）的实际效果需要自己验证。

### MCP（87 tools）+ A2A 适配

OmniRoute 内置了 MCP（Model Context Protocol）server，对外暴露 87 个工具，覆盖文件操作、shell、网络搜索、记忆检索等。同时实现了 A2A（Agent-to-Agent）协议，让多个代理之间能互相调用。这两点是把 OmniRoute 从"网关"升级成"代理运行时"的关键能力。

### 协议层细节

- TLS stealth：通过 TLS 指纹伪装，让被地域限制的厂商认为请求来自允许地区
- Circuit breaker：上游持续报错时自动熔断，避免无效重试放大故障
- Guardrails：可配置的内容安全规则
- Memory：跨会话的简单记忆存储
- Evals：内置评估管道，可对路由结果做 A/B 对比

### Dashboard

OmniRoute 提供 Web Dashboard（`/dashboard/free-tiers`），实时显示：

- 当前 40+ 免费池的聚合可用 token 数（约 1.6B/月稳态，新户最高约 2.1B）
- 各 provider 的当前已用/剩余配额
- 每个模型的实时使用统计
- Provider 的 terms flag（标注哪些免费池有使用限制）

这是 README 中特别强调的"诚实计数"——不做 rate-limit 24/7 假设，把每个共享池只计一次。

## 安装与运行

OmniRoute 提供三种分发：

```bash
# npm
npm install -g omniroute
omniroute

# Docker
docker run -d -p 20128:20128 diegosouzapw/omniroute

# Electron 桌面客户端（GitHub releases 下载）
```

启动后默认监听 `localhost:20128`，HTTP API 端口和 Dashboard 端口共用（路径区分）。然后把 Claude Code、Cursor 等代理的 base URL 改成 `http://localhost:20128/v1` 即可。

## 工程取舍

**优势**：

- 一套配置接管所有代理，代理层零修改
- 4 级回退让"代理突然断流"的体验问题基本消失
- 压缩对工具密集型会话省 token 显著
- MIT 协议，自部署无授权问题
- 测试覆盖 14,965 条，路由逻辑可靠性较高

**劣势**：

- 本地网关意味着多一跳网络延迟（虽然很小，但加上压缩管道后端到端延迟会增加 50–200ms）
- 协议翻译层是个故障点——如果 OmniRoute 的某条协议翻译 bug，会影响所有指向它的代理
- RTK + Caveman 是有损压缩，对代码评审、文档分析类任务可能引入误判
- Free tier 池的稳定性由各上游厂商决定，OmniRoute 只能做聚合和监控
- 项目活跃度高，但创建时间短（2026-02），长期维护风险未知

## 适用边界

**适合**：

- 同时使用 3+ AI 编程代理，希望统一管理 base URL 和 key
- 经常碰到 rate limit / quota 耗尽，需要自动回退到备用 provider
- 工具调用密集型工作流（agent + 工具调用），希望显著压低 token 成本
- 愿意自部署本地网关，承担额外的运维复杂度

**不适合**：

- 只有一个代理、一个 provider 的简单场景——直接配代理原生 base URL 更省事
- 对延迟极敏感的场景（如实时语音、毫秒级交易）——多一跳+压缩管道延迟不可忽略
- 对语义完整性要求极高的场景（如合同评审、代码安全审计）——Caveman 压缩可能引入误判
- 完全依赖订阅制 provider 的场景——Tier 1 已经够用，多一层回退反而引入复杂度

## 阅读路径

1. 先在自己机器上 `npm install -g omniroute` 跑通默认配置
2. 把 Claude Code 的 base URL 指向 `localhost:20128/v1`，验证一次对话
3. 打开 Dashboard 看免费池配额和路由命中统计
4. 启用 RTK 压缩，对比自己之前会话的 token 消耗
5. 跑一周看 Tier 1→Tier 2→Tier 3 的回退是否真的发生
6. 根据真实回退路径调路由策略

OmniRoute 在 8k Stars 这个量级已经算热门项目，但距离"工业级基础设施"还有差距——它更适合个人开发者和小团队的统一接入方案，而不是企业级 SLAs 保障。如果你的代理工作流涉及生产系统，先评估自己能否接受本地网关的故障域扩展。