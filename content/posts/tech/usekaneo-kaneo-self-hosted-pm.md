---
title: "Kaneo：以\"少即是多\"为信条的自托管项目管理工具"
date: 2026-08-02T02:59:48+08:00
slug: "usekaneo-kaneo-self-hosted-pm"
description: "usekaneo/kaneo 是一个 MIT 许可、自托管的项目管理平台，作者把它定位为\"减法设计\"：界面克制、真正快、数据留在自己手里；提供核心任务/看板/团队协作能力，不堆叠企业 SaaS 的多余工作流。"
draft: false
categories: ["技术笔记"]
tags: ["项目管理", "自托管", "看板", "开源", "Kanban"]
---

## 一句话判断

`usekaneo/kaneo` 是一个把"少即是多"贯彻到底的自托管项目管理工具：作者先指出主流 PM 工具的真正问题是"功能太多"，再把核心能力（看板、任务、协作）做成一个 MIT 许可、真正快、数据留在本地的应用。

## 自我陈述

README 把核心哲学写得很直接：

> The problem with most tools isn't that they lack features—it's that they have **too many**. Every notification, every unnecessary button, every complex workflow pulls your team away from what matters: **building great products**.
>
> We believe the best tools are **invisible**. They should amplify your team's natural workflow, not force you to adapt to theirs. Kaneo is built on the principle that **less is more**—every feature exists because it solves a real problem, not because it looks impressive in a demo.

## 差异化定位

| 维度 | Jira / Linear / Notion 风格 | Kaneo |
|------|---------------------------|-------|
| 部署 | SaaS（部分支持自托管） | 完全自托管 |
| 通知 | 多渠道 + 多种类 | 只保留必要的 |
| 按钮/菜单 | 复杂 | 克制 |
| 数据归属 | 服务商 | 自己的服务器 |
| License | 商业 | MIT |
| 性能优化 | 兼顾多租户 | 单部署即单租户 |

README 反复强调的几条：

- **Clean interface** that focuses on your work, not the tool
- **Self-hosted** so your data stays yours
- **Actually fast** because we care about performance
- **Open source** with a permissive MIT license

## 核心能力（来自文档站）

文档 [kaneo.app/docs/core](https://kaneo.app/docs/core) 列出的核心模块覆盖：

- 项目与任务
- 看板视图
- 团队成员协作
- 通知系统（节制版）

云版本 [cloud.kaneo.app](https://cloud.kaneo.app) 提供托管服务，但仓库的核心价值始终是自托管。

## 安装与启动

```bash
# 仓库提供的最简路径（README 中给出的核心步骤）
git clone https://github.com/usekaneo/kaneo
cd kaneo
# 按官方文档配置环境变量
docker compose up -d
```

启动后访问 `http://localhost:3000` 即可。CI 在 [GitHub Actions](https://github.com/usekaneo/kaneo/actions) 上运行；社区入口是 [Discord](https://discord.gg/rU4tSyhXXU)。

## 适用边界与不适用边界

**适用**：

- 小到中型团队（3–30 人）需要 PM 工具但拒绝给 Jira/Linear 付费
- 对"工具让团队分心"有切身感受的工程团队
- 已经在自托管 GitLab/Plane/Outline/BookStack 的团队，把 Kaneo 加进同一套部署体系
- 想要"数据在自己服务器上"满足合规要求的团队

**不适用**：

- 需要精细时间追踪、预算管理、计费功能的咨询/外包公司
- 需要复杂权限矩阵（部门→项目→任务→字段级）的企业
- 需要原生移动端体验（Kaneo 当前以 Web 为核心）

## 与 Plane / Focalboard / OpenProject 的对比

- **Plane**：同类自托管 PM 工具，社区规模更大；Kaneo 走的是更小、更克制路线
- **Focalboard**：Mattermost 出品，强看板弱任务层级
- **OpenProject**：企业级，传统甘特图 + Agile 双栈

Kaneo 的真正位置是"对 Linear 的克制感向往、又想要自托管"的团队——这个细分赛道过去一年几乎被它和 Plane 占满。