---
title: "Gstack：Garry Tan 如何用 AI Agent 一个人跑出 810 倍生产力"
date: "2026-05-25T20:08:27+08:00"
slug: "gstack-garry-tan-claude-code-setup-productivity"
description: "Gstack 是 Y Combinator 总裁 Garry Tan 的 Claude Code 配置，23 个专家角色让 AI 承担 CEO、设计师、工程经理、QA 等职责。本文解析其设计理念和快速上手方式。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Claude Code", "Garry Tan", "YC", "生产力"]
---

# Gstack：Garry Tan 如何用 AI Agent 一个人跑出 810 倍生产力

Gstack 是一个将 Claude Code 转变为虚拟工程团队的配置系统。由 Y Combinator 总裁 Garry Tan 维护，项目获得了 102,020 颗 Stars。

Garry Tan 在 2026 年 3 月的一次访谈中提到："我大概从 2025 年 12 月以来就没手动写过几行代码了。"在此之前，他在 60 天内兼职完成 3 个生产服务、40 多个功能，效率是他 2013 年 Building Bookface（YC 内部社交网络）时的 810 倍——以逻辑代码变更量（而非 raw LOC）计算。

## 核心思路

传统的 AI 编程辅助是"你写，AI 帮你补"。Gstack 的思路是反过来的：**AI 是执行者，人是评审和决策者。**

Garry Tan 把 AI 配置成 8 种虚拟角色，每个角色负责一个专业维度：

| 角色 | 职责 |
|------|------|
| CEO | 重塑产品思路，定义做什么 |
| Designer | 识别 AI 生成的"视觉垃圾"（AI slop） |
| Engineering Manager | 锁定架构，防止技术债务 |
| Release Manager | 管理发布流程和版本 |
| Doc Engineer | 维护文档质量 |
| QA Lead | 打开真实浏览器做端到端测试 |
| Security Officer | 运行 OWASP + STRIDE 审计 |
| Code Reviewer | 找生产级 Bug |

23 个专家角色和 8 个强力工具，全部通过 slash commands 调用，输出格式为 Markdown。

## 与 ECC 的关系

Gstack 建立在 [ECC](https://github.com/affaan-m/ECC)（前文已介绍）之上。ECC 是更通用的底层系统，定义技能、本能和记忆优化的框架；Gstack 是 ECC 在编程场景的具体实现，是 Garry Tan 的个人配置。

两者都是 MIT License，可以自由 fork 和定制。

## 快速开始

**依赖：** Claude Code + Git + Bun v1.0+（Windows 额外需要 Node.js）

**步骤：**

1. 打开 Claude Code，粘贴以下命令，Claude 会自动完成安装：

```
> Install gstack: run `git clone --single-branch --depth 1 https://github.com/garrytan/gstack`
```

2. 安装完成后，运行 `/office-hours` 开始使用——描述你想构建的产品

3. 用 `/plan-ceo-review` 评审功能设计

4. 用 `/review` 审查代码变更

5. 用 `/qa` 在预发布环境做端到端测试

Garry Tan 的建议是：**先用 `/office-hours` 和 `/review` 这两个命令，如果觉得有用再继续深入。**

## slash commands 列表

Gstack 的核心是 slash commands。主要命令包括：

- `/office-hours`：产品方向咨询，AI 以 CEO 角色提问和给出方向性建议
- `/plan-ceo-review`：功能方案的正式评审，带架构和 trade-off 分析
- `/review`：代码审查，找出 Bug 和改进点
- `/qa`：在给定 URL 上运行自动化 QA 测试
- `/release`：管理发布流程

这些命令都在 `/commands` 目录下定义，可以按需裁剪和定制。

## 适用人群

Gstack 主要针对以下场景设计：

- **创始人和技术 CEO**：想持续交付产品但没有团队
- **初次使用 Claude Code 的用户**：结构化的角色比空白 prompt 更有效
- **技术负责人和 Staff Engineer**：每个 PR 都附带严格审查、QA 和发布自动化

对于已经有成熟工作流的团队，Gstack 提供的不是银弹，而是一套值得参考的实践框架——是否采纳取决于团队的具体需求。

## 争议与局限性

Garry Tan 在项目中承认 raw LOC 作为生产力指标会被 AI 膨胀放大，并提供了一个[完整的反驳文档](docs/ON_THE_LOC_CONTROVERSY.md)解释他的衡量方法。他强调的是"逻辑代码变更量"（logical code change）而非行数——即真正改变系统行为的代码量。

Gstack 本身是一个高度个人化的配置，直接采用不一定适合自己的场景。项目本身也承认这一点，建议 fork 后按需调整。

---

*本文档基于 GitHub 仓库 2026 年 5 月最新信息编写，Stars：102,020，License：MIT。*