---
title: "Minimalist Entrepreneur：Claude Code 创业技能套件专家级技术文档"
date: 2026-03-30T16:05:00+08:00
slug: slavingia-skills-minimalist-entrepreneur
categories: ["技术笔记"]
tags: ["Claude Code", "SKILL", "创业", "Minimalist", "Entrepreneur"]
description: "Minimalist Entrepreneur Skills 是基于《The Minimalist Entrepreneur》的Claude Code技能套件，涵盖从找社区到建公司的10个创业技能。"
---

# Minimalist Entrepreneur：Claude Code 创业技能套件专家级技术文档

> **目标读者**：想要用 Claude Code 构建商业项目的创业者、开发者和技术爱好者
> **核心问题**：这套 Skills 如何帮助创业？每个 Skill 的使用场景是什么？如何用它从零开始打造产品？

---

## 1. 学习目标

完成本文档后，你将掌握：

- ✅ 理解 Minimalist Entrepreneur Skills 的核心定位与创业方法论
- ✅ 掌握 10 个 Skill 的功能与使用时机
- ✅ 学会在创业不同阶段选择正确的 Skill
- ✅ 能够将 Skills 集成到自己的 Claude Code 工作流
- ✅ 理解「先手工，再产品化」的核心理念
- ✅ 了解如何自定义和扩展这些 Skills

---

## 2. 原理分析

### 2.1 什么是 Minimalist Entrepreneur Skills？

**Minimalist Entrepreneur Skills** 是一套基于《The Minimalist Entrepreneur》书籍的 Claude Code 技能扩展，由 Sahil Lavingia（ Gumroad 创始人）提出，slavingia 开发维护。

> 💡 **核心理念**：「先手工交付价值，再把成功过程产品化」—— 不要一开始就想着构建复杂产品，先用人工方式验证商业模式。

这套 Skills 包含 10 个 Claude Code 命令，覆盖从「找方向」到「建公司」的全流程。

### 2.2 核心创业方法论

Minimalist Entrepreneur 的创业路径是一条**渐进式验证之路**：

| 阶段 | 核心问题 | Skill |
|------|---------|-------|
| **Community** | 谁是我的用户？ | /find-community |
| **Validate** | 问题值得解决吗？ | /validate-idea |
| **Build** | 如何最小化可行产品？ | /mvp |
| **Processize** | 如何手工交付价值？ | /processize |
| **Sell** | 如何获得前 100 个客户？ | /first-customers |
| **Price** | 如何定价？ | /pricing |
| **Market** | 如何通过内容增长？ | /marketing-plan |
| **Grow** | 如何可持续增长？ | /grow-sustainably |
| **Culture** | 如何建立公司文化？ | /company-values |
| **Review** | 如何用极简原则决策？ | /minimalist-review |

### 2.3 为什么选择这套 Skills？

| 传统创业方式 | Minimalist Entrepreneur |
|-------------|------------------------|
| 先融资再做事 | 用最小成本验证 |
| 先建产品再找用户 | 先手工交付再产品化 |
| 追求大规模增长 | 追求盈利和可持续 |
| 秘密开发 | 公开分享建立社区 |
| 快速扩张 | 小步迭代 |

### 2.4 技术边界

| 支持 | 不支持 |
|------|--------|
| ✅ Claude Code | ❌ 其他 IDE/Agent |
| ✅ 商业全流程指导 | ❌ 融资咨询 |
| ✅ 内容创作辅助 | ❌ 法律/税务咨询 |
| ✅ 决策框架 | ❌ 代替人工判断 |

---

## 3. 架构分析

### 3.1 整体架构

```
Minimalist Entrepreneur Skills
├── 安装配置层
│   ├── Claude Code Plugin System
│   ├── Marketplace 安装
│   └── 本地 Clone 安装
├── 10 个 Skill 模块
│   ├── /find-community          # 找社区
│   ├── /validate-idea          # 验证想法
│   ├── /mvp                    # 最小可行产品
│   ├── /processize             # 流程化
│   ├── /first-customers        # 前100客户
│   ├── /pricing               # 定价策略
│   ├── /marketing-plan         # 内容营销
│   ├── /grow-sustainably      # 可持续增长
│   ├── /company-values         # 公司文化
│   └── /minimalist-review      # 极简复盘
└── 输出层
    ├── 结构化文档
    ├── 清单列表
    └── 行动建议
```

### 3.2 Skill 结构

每个 Skill 都是一个 Markdown 文件，包含：

```yaml
---
name: Skill 名称
command: /skill-command
description: 简短描述
when_to_use: 何时使用
---

# 引导问题

1. [问题1]
2. [问题2]
3. [问题3]

# 输出格式

## 发现总结
...

## 行动清单
- [ ] 行动1
- [ ] 行动2
```

### 3.3 与 Claude Code 的集成

Skills 通过 Claude Code 的 `/` 命令系统调用：

```
用户输入: /find-community
    ↓
Claude Code 识别为 Skill 命令
    ↓
读取 skills/find-community/SKILL.md
    ↓
按照引导问题与用户对话
    ↓
生成结构化输出
```

---

## 4. 10 个 Skill 详解

### 4.1 Find Community（/find-community）

**何时使用**：正在寻找创业方向，想找到自己的目标用户群

**核心问题**：
- 你对什么话题充满热情？
- 你经常和谁讨论这些话题？
- 现有的解决方案哪里让你不满？

**输出**：
- 社区定位建议
- 潜在用户画像
- 第一步行动清单

### 4.2 Validate Idea（/validate-idea）

**何时使用**：有一个想法，想测试它是否值得追求

**核心问题**：
- 这个问题的痛苦程度有多深？
- 用户现在如何解决它？
- 他们愿意为此付多少钱？

**输出**：
- 想法验证报告
- 风险评估
- 是否继续的建议

### 4.3 MVP（/mvp）

**何时使用**：准备构建第一个产品，但在范围上挣扎

**核心问题**：
- 最小可行的功能是什么？
- 如何不用代码就能交付？
- 如何验证用户真的想要它？

**输出**：
- MVP 范围定义
- 手工验证方案
- 构建优先级

### 4.4 Processize（/processize）

**何时使用**：有一个产品想法，想在写代码之前用手工方式交付价值

**核心问题**：
- 手工交付的完整流程是什么？
- 哪些步骤最耗时？
- 如何逐步用代码替代？

**输出**：
- 手工流程文档
- 可产品化的环节
- 渐进式自动化路径

### 4.5 First Customers（/first-customers）

**何时使用**：有产品，需要找到前 100 个客户

**核心问题**：
- 谁是你的理想客户？
- 如何一个一个地获得他们？
- 如何建立长期关系？

**输出**：
- 客户获取策略
- 外联模板
- 100 客户路线图

### 4.6 Pricing（/pricing）

**何时使用**：设置价格，或考虑价格变动

**核心问题**：
- 你的成本结构是什么？
- 用户认知价值是多少？
- 竞争对手如何定价？

**输出**：
- 定价策略建议
- 价格测试方案
- 定价文案模板

### 4.7 Marketing Plan（/marketing-plan）

**何时使用**：有了产品-市场契合，准备通过内容扩展

**核心问题**：
- 你的内容主题是什么？
- 你计划在哪些平台发布？
- 如何将内容转化为客户？

**输出**：
- 内容日历
- 平台策略
- 内容模板

### 4.8 Grow Sustainably（/grow-sustainably）

**何时使用**：在做关于支出、招聘或扩张的决策

**核心问题**：
- 你的单位经济学是什么？
- 何时是招聘的正确时机？
- 如何保持盈利能力？

**输出**：
- 增长策略评估
- 财务健康检查清单
- 扩张决策框架

### 4.9 Company Values（/company-values）

**何时使用**：定义文化，准备招聘

**核心问题**：
- 你代表什么？
- 你想让公司以什么闻名？
- 早期的招聘标准是什么？

**输出**：
- 公司价值观文档
- 招聘标准清单
- 文化建设建议

### 4.10 Minimalist Review（/minimalist-review）

**何时使用**：对任何业务决策进行直觉检查

**核心问题**：
- 这个决策是否符合我们的价值观？
- 最小化路径是什么？
- 我们能从这次经历中学到什么？

**输出**：
- 决策分析框架
- 风险/收益评估
- 下一步行动

---

## 5. 使用说明

### 5.1 安装方式

**方式一：Marketplace 安装（推荐）**

在 Claude Code 中运行：

```
/plugin marketplace add slavingia/skills
/plugin install minimalist-entrepreneur
```

Claude Code 会自动获取仓库并注册所有 10 个 Skills。

**方式二：本地 Clone 安装**

```bash
# 克隆仓库
git clone https://github.com/slavingia/skills.git

# 手动复制到 Claude Code 目录
cp -r skills/skills ~/.claude/skills/
```

### 5.2 使用流程

**第一步：选择合适的 Skill**

根据你当前的创业阶段选择：

| 阶段 | 推荐 Skill |
|------|-----------|
| 找方向 | /find-community |
| 验证想法 | /validate-idea |
| 构建产品 | /mvp |
| 交付验证 | /processize |
| 获取客户 | /first-customers |

**第二步：调用 Skill**

```
/find-community
```

**第三步：与 Claude 对话**

Claude 会问你一系列引导问题。认真回答每个问题。

**第四步：获得结构化输出**

Claude 会生成：
- 发现总结
- 行动清单
- 后续建议

### 5.3 典型对话示例

```
用户: /find-community

Claude: 让我们一起找到你的创业社区。

问题1：你对什么话题充满热情，而且愿意无偿深入研究？

用户: AI 工具和自动化

Claude: 问题2：你经常在哪里和同好讨论这些话题？

用户: Twitter、Reddit 的 r/SideProject

Claude: 问题3：现有的 AI 工具哪里让你最不满意？

用户: 大部分工具太复杂，需要太多配置...

[继续引导问题...]

## 发现总结

🎯 你的社区定位：
- 主题：面向非技术用户的简单 AI 自动化工具
- 潜在用户：博主、小企业主、自由职业者
- 痛点：现有工具学习曲线太陡

## 下一步行动

- [ ] 在 Twitter 上关注 20 个 AI 工具爱好者
- [ ] 加入 r/SideProject 并参与讨论
- [ ] 找到 3 个最常被抱怨的 AI 工具痛点
```

---

## 6. 开发扩展

### 6.1 自定义 Skill

基于现有结构创建新的 Skill：

```markdown
---
name: My Custom Skill
command: /my-custom
description: 我的自定义技能
when_to_use: 在特定场景使用
---

# 引导问题

1. [你的问题1]
2. [你的问题2]

# 输出格式

## 总结
...

## 行动清单
- [ ] 行动1
```

### 6.2 Skill 组合使用

根据创业阶段组合多个 Skills：

**阶段一：探索期**
```
/find-community
 ↓
/validate-idea
```

**阶段二：构建期**
```
/mvp
 ↓
/processize
```

**阶段三：增长期**
```
/first-customers
 ↓
/pricing
 ↓
/marketing-plan
```

**阶段四：成熟期**
```
/grow-sustainably
 ↓
/company-values
 ↓
/minimalist-review
```

### 6.3 集成到现有工作流

将 Skills 与其他 Claude Code 功能结合：

```markdown
# 结合 Code 命令

1. 用 /find-community 确定方向
2. 用 /mvp 定义产品范围
3. 用 Claude Code 实现代码

# 结合研究能力

1. 用 /validate-idea 验证想法
2. 让 Claude 研究竞争对手
3. 用 /pricing 制定定价策略
```

---

## 7. 最佳实践

### 7.1 如何获得最佳效果

| 建议 | 说明 |
|------|------|
| **按顺序使用** | 从 Community 开始，不要跳步 |
| **认真回答问题** | 问题设计有深意，敷衍回答会失去价值 |
| **记录对话历史** | 保存输出，便于后续复盘 |
| **迭代使用** | 不同阶段反复使用同一 Skill |
| **分享给他人** | 这些 Skills 可以帮助团队对齐 |

### 7.2 常见误区

| 误区 | 正确做法 |
|------|---------|
| 跳过 Community 直接 Build | 找到社区是成功的基础 |
| 一次使用多个 Skills | 一个一个来，深入每个阶段 |
| 跳过 Processize 直接 Coding | 手工交付验证商业模式 |
| 忽视 Pricing | 从第一天就要收费 |

### 7.3 与其他工具的配合

| 工具 | 配合方式 |
|------|---------|
| **Notion** | 保存 Skills 输出作为笔记 |
| **Linear** | 将行动清单转为 Issue |
| **GitHub** | 用 Projects 管理产品路线图 |
| **Slack** | 团队共享决策和价值观 |

---

## 8. 常见问题

### Q1: 这些 Skills 和普通对话有什么区别？

Skills 提供了**结构化的引导框架**。普通对话可能绕远路或遗漏关键问题，Skills 确保你系统性地思考每个创业环节。

### Q2: 我需要按顺序使用所有 Skills 吗？

不需要。按需选择你当前阶段需要的 Skill。但 Community → Validate → Build 的顺序是经过验证的路径。

### Q3: Skills 的建议是否可信？

Skills 来自《The Minimalist Entrepreneur》的方法论，这本书基于 Sahil Lavingia 创立 Gumroad 的真实经验。Skills 只是把这些经验工具化。

### Q4: 我可以修改这些 Skills 吗？

✅ 可以。这些是开源的，你可以根据自己需求定制。

### Q5: 支持中文吗？

Skills 本身是英文的，但可以用中文与 Claude 对话。Claude 会理解中文并用中文回复。

---

## 9. 总结

### 9.1 核心要点

| 要点 | 说明 |
|------|------|
| **核心理念** | 先手工交付，再产品化 |
| **覆盖全流程** | 从找方向到建公司，10 个 Skills 覆盖 |
| **简单易用** | 一个命令启动结构化对话 |
| **基于实战** | 方法论来自 Gumroad 创始人 |
| **可扩展** | 开源可定制 |

### 9.2 快速参考卡

```
📍 找方向：/find-community
🎯 验想法：/validate-idea
🏗️ 建产品：/mvp
⚙️ 流程化：/processize
👥 获客户：/first-customers
💰 定价格：/pricing
📣 做营销：/marketing-plan
📈 稳增长：/grow-sustainably
🏛️ 建文化：/company-values
🔍 做复盘：/minimalist-review
```

### 9.3 资源链接

| 资源 | 链接 |
|------|------|
| **GitHub 仓库** | https://github.com/slavingia/skills |
| **原书** | https://www.minimalistentrepreneur.com/ |
| **Gumroad** | https://gumroad.com/ |

---

*文档信息：Minimalist Entrepreneur Skills | 更新日期：2026-03-30 | 难度：⭐⭐*
