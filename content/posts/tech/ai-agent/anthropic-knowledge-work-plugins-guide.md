---
title: "Anthropic Knowledge Work Plugins：把 Claude 变成岗位专家的完整指南"
date: 2026-03-24T17:30:00+08:00
slug: "anthropic-knowledge-work-plugins-guide"
aliases:
  - /posts/tech/anthropic-knowledge-work-plugins-guide/
description: "详细介绍 Anthropic 官方推出的 11 款 Knowledge Work Plugins，解析其结构与功能，帮助用户为 Claude 安装“岗位操作系统”，提升各行业的工作效率。"
draft: false
categories: ["技术笔记"]
tags: ["Claude", "MCP", "工作流", "AI工具"]
---

# Anthropic Knowledge Work Plugins：把 Claude 变成岗位专家的完整指南

> 预计阅读时间：25分钟 | 难度：⭐⭐⭐

---

## 学习目标

读完这篇文章，你可以做到三件事：

1. 看懂 `knowledge-work-plugins` 的核心结构和运行方式。
2. 快速判断 11 个插件分别适合什么场景。
3. 作为新手，按步骤装上插件并在真实工作里用起来。

## 先建立一个正确认知

这个仓库的重点不是“把 Claude 变得无所不能”，而是“给不同岗位一套标准化能力包”。

每个插件都包含四类资产：

- skills：岗位知识、方法论、执行步骤
- commands：可直接触发的任务命令
- connectors（MCP）：连接企业工具与数据源
- sub-agents：把复杂任务拆成更稳定的协作单元

你可以把它理解成：给 Claude 安装“岗位操作系统”。

## 安装与启动（新手必看）

### 在 Claude Code 安装

```bash
claude plugin marketplace add anthropics/knowledge-work-plugins
claude plugin install productivity@knowledge-work-plugins
```

你也可以把 `productivity` 替换为 `sales`、`data` 等具体插件名。

### 安装后如何生效

- 自动生效：当你提问命中某个场景，相关 skills 会自动参与。
- 手动触发：你可以直接使用该插件的命令入口，例如 `/sales:call-prep`、`/data:write-query`。
- 逐步扩展：新手建议先装 1-2 个插件，用顺后再加，不要一次装满 11 个。

## 插件结构（懂这个就不容易用错）

```text
plugin-name/
├── .claude-plugin/plugin.json
├── .mcp.json
├── commands/
└── skills/
```

- `.claude-plugin/plugin.json`：插件元数据和能力声明
- `.mcp.json`：连接你们工具栈
- `commands/`：显式动作入口，适合重复任务
- `skills/`：隐式“经验库”，提升默认输出质量

## 11 个插件完整指南（功能、特点、用法、场景）

下面每个插件都按同一结构讲解：**做什么、为什么强、怎么用、什么时候用**。

## 1. productivity

### productivity：详细功能

- 汇总个人与团队任务状态
- 结合日历安排工作优先级
- 自动生成每日计划、周计划、跟进清单
- 统一管理来自 Slack、Notion、Jira 等多处待办

### productivity：特点

- 强在“个人执行系统”搭建，而不是单条内容生成
- 能减少上下文切换，避免任务遗漏
- 适合作为多数人的第一个插件

### productivity：用法

- 早上让它输出“今天最重要的 3 件事”
- 下午让它基于进度自动改计划
- 下班前让它总结完成项与次日待办

### productivity：使用场景

- 任务太多、优先级混乱
- 工作跨多个工具，经常漏回复或漏跟进
- 需要固定节奏的日/周复盘

## 2. sales

### sales：详细功能

- 线索调研与画像补全
- 电话前准备材料生成
- 外联邮件与话术草拟
- 管道健康检查与机会优先级建议
- 竞品对比卡（battlecard）整理

### sales：特点

- 强在“销售动作前置准备”与“沟通材料标准化”
- 能显著缩短从线索到首轮触达的准备时间

### sales：用法

- 输入目标客户名称，生成调研简报
- 调用通话准备命令，产出开场、问题清单、异议处理
- 周度让它复盘 pipeline，标出高风险机会

### sales：使用场景

- 新销售上手慢，不知道如何做 call prep
- 团队外联话术质量不稳定
- 管道会议前准备成本太高

## 3. customer-support

### customer-support：详细功能

- 工单自动分流与优先级建议
- 回复草稿生成（按语气和 SLA 要求）
- 升级（escalation）信息打包
- 关联历史上下文，减少重复询问用户
- 已解决问题自动沉淀为知识库候选

### customer-support：特点

- 强在“从响应到沉淀”的闭环
- 兼顾效率和一致性，特别适合高并发支持场景

### customer-support：用法

- 批量归类当天工单并标风险等级
- 对高优工单生成“可直接发送”的回复草稿
- 把重复问题汇总成 FAQ 草案

### customer-support：使用场景

- 客服团队峰值时段压力大
- 回复风格不统一、升级信息不完整
- 已解决问题没有形成组织记忆

## 4. product-management

### product-management：详细功能

- 生成需求规格与评审材料
- 路线图候选项梳理
- 用户研究与反馈总结
- 跨部门状态同步与周报整理
- 竞品与市场动态追踪

### product-management：特点

- 强在“把需求、数据、设计、用户反馈串成一条线”
- 让 PRD 更有证据链，而不是纯主观描述

### product-management：用法

- 汇总工单、访谈、埋点变化后生成 spec 初稿
- 自动补齐目标、边界、指标、风险、验收标准
- 生成不同角色版本的同步摘要

### product-management：使用场景

- PM 信息源分散，写文档成本高
- 需求评审反复来回，缺少统一上下文
- 利益相关方更新频率高

## 5. marketing

### marketing：详细功能

- 内容选题、文案与多渠道发布素材
- 活动策划与节奏编排
- 品牌语调一致性控制
- 竞品营销动作扫描
- 渠道效果汇总报告

### marketing：特点

- 强在“内容生产 + 运营分析”的一体化
- 能把“品牌调性”从口头要求变成可执行规范

### marketing：用法

- 给一个活动目标，产出多渠道内容包
- 按品牌语调重写素材
- 周报自动汇总渠道表现并给优化建议

### marketing：使用场景

- 内容团队多角色协作，口径经常不一致
- 活动复盘靠手工拼数据
- 需要更快响应市场热点

## 6. legal

### legal：详细功能

- 合同条款快速审阅与风险提示
- NDA 分流与模板化处理
- 合规问题初步归类
- 会议前法律要点准备
- 常见法律问询的标准回复草拟

### legal：特点

- 强在“高频标准场景提速”，不是替代律师判断
- 能降低重复性文书工作负担

### legal：用法

- 上传合同要点，输出风险摘要与关注条款
- 对 NDA 做快速检查并给出处理建议
- 生成法务沟通会前清单

### legal：使用场景

- 合同处理量大，人工初筛吃力
- 业务团队经常问相似合规问题
- 法务资源紧张，需要先做预处理

## 7. finance

### finance：详细功能

- 分录准备与对账辅助
- 财务报表草稿生成
- 差异分析（variance analysis）
- 月结流程协助
- 审计资料准备支持

### finance：特点

- 强在“流程化财务动作”与“结构化输出”
- 对 close 期间提效明显

### finance：用法

- 基于数据仓库结果生成对账说明草稿
- 月结期让它列出异常项与排查顺序
- 输出审计问答准备清单

### finance：使用场景

- 月末结账节奏紧、重复动作多
- 报表解释需要跨系统取数
- 审计季资料组织压力大

## 8. data

### data：详细功能

- SQL 编写与改写
- 指标口径解释与统计分析
- 图表和仪表盘建议
- 分析结论自检与验证提醒
- 面向业务方的结果说明生成

### data：特点

- 强在“从提问到验证”的分析链路
- 能减少“只给结论不做校验”的分析风险

### data：用法

- 先让它把业务问题翻译成分析问题
- 生成 SQL 后先做口径与边界检查
- 输出结论时附上假设和验证状态

### data：使用场景

- 非数据同学需要快速做自助分析
- 数据团队要提升分析交付一致性
- 需要给管理层做可解释汇报

## 9. enterprise-search

### enterprise-search：详细功能

- 跨邮件、聊天、文档、知识库统一检索
- 结果去重、聚合、摘要
- 主题化问题回答与证据出处整理
- 跨系统知识定位

### enterprise-search：特点

- 强在“找得到”而不是“写得漂亮”
- 特别适合作为其他插件的前置插件

### enterprise-search：用法

- 输入业务问题，先统一检索全公司上下文
- 把结果按来源和可信度分层展示
- 再交给对应岗位插件做后续产出

### enterprise-search：使用场景

- 信息分散在多个系统，找资料很慢
- 新员工入职需要快速建立上下文
- 会议前要快速拉齐历史信息

## 10. bio-research

### bio-research：详细功能

- 文献检索与初步整理
- 早期研发相关信息聚合
- 靶点优先级讨论支持
- 研究路径对比与总结

### bio-research：特点

- 强在“生物医药早研语境”的专门能力
- 连接了该领域常见数据库与研究工具

### bio-research：用法

- 针对研究问题生成文献检索与筛选提纲
- 汇总候选方向的证据与争议点
- 形成团队讨论稿

### bio-research：使用场景

- 研究线索太多，不知如何快速收敛
- 需要加速文献扫读与方向评估
- 跨学科团队需要统一讨论底稿

## 11. cowork-plugin-management

### cowork-plugin-management：详细功能

- 新建插件脚手架
- 改造现有插件结构
- 管理命令、skills、连接配置
- 规范化插件版本演进

### cowork-plugin-management：特点

- 强在“插件工程化”，适合平台团队或高级用户
- 是“把一次经验变成长期资产”的关键插件

### cowork-plugin-management：用法

- 基于现有岗位模板快速复制新插件
- 为公司流程新增专属命令
- 统一维护多个插件的配置与规范

### cowork-plugin-management：使用场景

- 你们有定制化流程，通用插件不够用
- 需要内部沉淀多个岗位插件
- 想建立插件治理机制

## 新手怎么选：一张决策表

| 你的问题 | 优先插件 |
| --- | --- |
| 我今天事情太多，不知道先做什么 | productivity |
| 我需要准备客户沟通、写外联话术 | sales |
| 工单太多，回复和升级质量不稳定 | customer-support |
| 我要写需求规格、做路线图沟通 | product-management |
| 我要做内容/活动/品牌一致性输出 | marketing |
| 我要做合同初审或 NDA 处理 | legal |
| 我要对账、做月结与财务解释 | finance |
| 我要写 SQL、做分析并验证结论 | data |
| 我先要把公司资料快速找全 | enterprise-search |
| 我做生物医药早期研究相关工作 | bio-research |
| 我要自己搭或改公司内部插件 | cowork-plugin-management |

## 新手上手路径（建议照做）

1. 先选一个你每周都会重复做的场景。
2. 只安装 1 个主插件，连续使用 1 周。
3. 把高频任务固化成命令调用习惯。
4. 再补装一个“配套插件”形成组合。

推荐组合示例：

- 销售团队：`enterprise-search + sales`
- 产品团队：`enterprise-search + product-management + data`
- 客服团队：`customer-support + enterprise-search`
- 管理岗位：`productivity + enterprise-search`

## 如何把它们用出“团队级价值”

- 先统一术语：把你们内部说法写进 skills
- 先统一输出模板：让命令结果有固定结构
- 先统一连接范围：优先接高价值数据源
- 先统一验收标准：输出必须可复核、可落地

## 总结

`knowledge-work-plugins` 最有价值的地方是把“岗位经验”变成“可安装、可复用、可迭代”的协作系统。

对新手来说，记住一句话就够了：**先按场景选插件，再按流程用插件，最后按团队实践改插件。**
