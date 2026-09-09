---
title: "Distilly：把一个人的思维方式蒸馏成 Agent 可用的档案"
date: 2026-09-10T03:15:00+08:00
slug: "distilly-person-profile-for-agents"
github_repo: "titanwings/distilly"
source_key: "gh:titanwings/distilly"
description: "Distilly 是一个本地优先的开源项目，把一个人的素材、工作习惯、判断力和语气蒸馏成版本化的人物档案，供编码 Agent 临时召回或长期安装为 Skill。本文解析其五工具架构、fail-closed 主机验证机制与适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "MCP", "知识蒸馏", "开源"]
---

# Distilly：把一个人的思维方式蒸馏成 Agent 可用的档案

大多数"让 AI 更懂你"的项目走的是云端路线：导入聊天记录，上传文档，换来一个托管在别处的个性化模型。Distilly 反其道而行——它把一个人的源素材、工作习惯、判断力和语气，在本地蒸馏成一份**版本化的人物档案（Person Profile）**，再以两种方式喂给编码 Agent：运行中临时召回，或显式安装为长期 Skill。存储主权留在本地，不需要额外的模型 API key。

这个项目目前 24,500+ stars、2,100+ forks，TypeScript 编写，MIT 协议。但它有一个容易被忽视的状态：仓库默认分支停留在 `0.1.0-preview.1` Developer Preview，没有打 tag，也没发 npm 包。看懂这个项目，关键不是"它能做什么"，而是它如何用一连串工程约束把自己圈在一个诚实的边界内。

## 系统地图：五工具、四层、一个权威存储

Distilly 的模型侧表面刻意收窄到**恰好五个 MCP 工具**：

| 工具 | 职责 |
|------|------|
| `distilly_get` | 读取人物档案或生成当前运行的完整提示 |
| `distilly_ingest` | 导入用户显式指定的素材 |
| `distilly_pending` | 查看待处理的研究任务 |
| `distilly_commit` | 提交一个版本化档案 |
| `distilly_correct` | 接受用户显式纠正并发起候选评审 |

往下是一个分层清晰的 pnpm workspace：`protocol`（35 个 EngineMethodMap schema 与身份类型）、`adapters`（确定性解析器边界，内置 TXT/Markdown/JSON/SRT/VTT）、`engine`（SQLite/WAL 权威存储，十九张表的私有 schema）、`runtime`（组合解析器与引擎的本地运行时）、`bindings`（各宿主的安装与生命周期）、`mcp` / `panel` / `cli`（暴露层）。依赖方向有明确 allowlist，禁止向上与互相引用。

存储侧的设计值得注意：原始字节与规范化正文放进 SHA-256 内容寻址的 blob store，元数据、不可变版本、版本范围的声明（claims）与证据（evidence）、审计事件全部收在 SQLite 单一权威里。每次变更在一个事务里提交全部结构化效果，并精确重放 RequestId——这意味着崩溃恢复不靠日志补丁，而是靠事务本身。

## 一次完整的任务流

以 Codex 上的验证流程为例，看抽象机制如何配合：

1. 用户重启宿主后，让 Agent "研究并蒸馏某个人"，只提供想纳入的文件、文本或公开 URL；
2. Distilly 解析或创建该人物（person），用确定性本地解析器导入选定素材；
3. 创建待处理研究任务和一份**证据绑定的简报（evidence-bound briefing）**；
4. 提交版本化的人物档案；
5. 返回档案，或为本次运行生成完整临时提示；
6. 接受显式纠正，把候选送审；
7. 用户在本地 Panel 里 promote、reject 或 rollback 候选；
8. 应用户要求，把获批档案安装为自包含的宿主 Skill。

注意第 6-7 步：纠正不直接改档案，而是生成候选并等待人工裁决——版本演进被设计成显式评审门，而不是静默覆盖。

## Fail-closed：把"诚实"做成机制

这个项目最有个性的部分是宿主兼容策略。Distilly 对每个宿主版本记录"真实宿主传输容量夹具（real-host transport-capacity fixture）"：用真实宿主可执行文件、模型和 MCP 传输跑确定性合成夹具，实测净预算。当前数字是 Codex/OpenClaw 65,536 序列化字节、Hermes 49,752。

对这些数字要谨慎解读：

- **测的是什么**——完整简报或档案提示能否不被截断地穿过真实宿主的 MCP 传输到达模型；
- **反映哪部分系统**——传输与序列化路径的容量下界；
- **推不出什么**——打包重启、完整产品生命周期、以及任何特定模型会话的剩余上下文。

任何未记录的宿主版本、变更的发布摘要或序列化器组合，都会在写入未验证集成**之前**返回 `host_unsupported`。没有自动降级到旧实现——Legacy Skill 兼容模式是 `dot-skill` 分支上一个显式的、独立的选择。README 甚至警告：不要在 Plugin 使用同一 `~/.distilly/` 目录时启用旧版采集器，因为旧采集器会写入凭据配置，超出 Preview 的安全评审边界。

一个 24k stars 的项目把"我不能保证的事"写进失败路径而不是宣传页，这在当前 Agent 工具生态里相当少见。

## 适用边界与采用建议

**先说现状**：只有 Codex 在发布分支上完成全流程验证；OpenClaw `2026.3.24` 和 Hermes `v0.9.0` 验证了传输容量路径，但打包重启、长期 Skill 与卸载生命周期检查仍未完成；Claude Code、DeepSeek Harness 等走 Legacy Skill 模式或等待社区绑定。素材格式目前限 TXT/Markdown/JSON/SRT/VTT、粘贴文本和公开 URL，PDF 与邮件导出是后续工作。

在此边界内：

- **适合**：重度 Codex 用户想沉淀某个专家（或自己）的判断模式为可版本化、可纠错的 Skill；对数据主权敏感、接受 Node 22.19+/pnpm 10.32+ 本地构建的团队。
- **等一等**：非 Codex 宿主用户——传输夹具不等于生命周期闭环；想接 PDF/邮件/托管连接器的用户。
- **不必上**：只需要一次性总结文档的场景——普通 RAG 或上下文塞入就够了，Distilly 的价值在版本化、可纠正、可安装的长期人格资产，不在一次性问答。

安装路径（人类）：

```bash
git clone --branch distilly-plugin https://github.com/titanwings/distilly.git
cd distilly
corepack enable
pnpm install --frozen-lockfile
pnpm run build
node packages/cli/lib/bin.js setup --host codex
node packages/cli/lib/bin.js doctor --host codex
```

## 结语

Distilly 提出的命题——"人的思维方式可以是 Agent 的可安装资产"——本身不新；新的是它对这个命题的工程化态度：五个工具收窄模型可见面、SQLite 单一权威加不可变版本管住状态、fail-closed 夹具管住宿主承诺。等它从 Developer Preview 走向 tagged release、补齐各宿主生命周期验证后，再看一遍这个仓库，会有更完整的判断。
