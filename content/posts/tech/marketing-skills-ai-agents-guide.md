---
title: "Marketing Skills：20.3K Stars·40+营销技能·AI Agent营销助手"
date: 2026-04-12T02:31:39+08:00
slug: marketing-skills-ai-agents-guide
description: "Marketing Skills 收录了 40+ 营销技能，是一个 AI Agent 营销助手，提供转化优化、SEO、内容创作等多种营销功能。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "营销", "SEO", "内容创作", "Agent"]
---

# Marketing Skills：20.3K Stars·40+营销技能·AI Agent营销助手·转化优化·SEO·内容创作

## 一、项目概述

### 1.1 Marketing Skills 是什么

**Marketing Skills** 是一个面向 AI Agent 的**营销技能集合**，专注于营销任务。

> "A collection of AI agent skills focused on marketing tasks. Built for technical marketers and founders who want AI coding agents to help with conversion optimization, copywriting, SEO, analytics, and growth engineering."

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | **20.3k** ⭐ |
| Forks | 3.2k |
| 技能数量 | **40+** |
| 最新版本 | **v1.7.0** (2026-04-13) |
| 许可证 | MIT |
| 语言 | JavaScript 98.4%, Shell 1.6% |

### 1.3 核心定位

| 维度 | 说明 |
|------|------|
| 🎯 **营销技能** | 转化优化、文案、SEO |
| 🤖 **AI Agent** | 适配 Claude Code、Codex 等 |
| 📊 **数据分析** | 分析、实验、指标追踪 |
| 🚀 **增长工程** | 引流、裂变、留存 |

### 1.4 支持的 AI 平台

| 平台 | 说明 |
|------|------|
| **Claude Code** | Anthropic AI 编码助手 |
| **OpenAI Codex** | OpenAI 代码助手 |
| **Cursor** | AI 代码编辑器 |
| **Windsurf** | AI 编程工具 |
| **其他 Agent** | 支持 Agent Skills 规范即可 |

## 二、核心架构

### 2.1 技能层次结构

```
┌─────────────────────────────────────────────────────────────┐
│                    Marketing Skills 架构                             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   ┌─────────────────────────────────────────────────┐   │
│   │              product-marketing-context                 │   │
│   │              (所有技能的根基，首先读取)                  │   │
│   └───────────────────────┬─────────────────────────────┘   │
│                           │                                     │
│   ┌───────────────────────┼───────────────────────────────┐   │
│   ▼                       ▼                               ▼   │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ │
│ │ 转化优化 │ │ 内容文案 │ │ SEO搜索 │ │ 付费推广 │ │ 策略分析 │ │
│ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ │
│      │            │            │            │            │        │
│ ┌────┴────┐ ┌────┴────┐ ┌────┴────┐ ┌────┴────┐ ┌────┴────┐ │
│ │page-cro │ │copywrite│ │seo-audit│ │paid-ads│ │mkt-ideas│ │
│ │signup   │ │cold-emal│ │ai-seo  │ │ad-creat │ │pricing  │ │
│ │onboard  │ │email-seq│ │programm │ │social   │ │launch   │ │
│ │form-cro │ │copy-edit│ │site-arch│ │         │ │psych    │ │
│ │popup    │ │social   │ │schema   │ │         │ │revops   │ │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 技能依赖关系

```
product-marketing-context（基础上下文）
    │
    ├── copywriting ↔ page-cro ↔ ab-test-setup
    ├── revops ↔ sales-enablement ↔ cold-email
    ├── seo-audit ↔ schema-markup ↔ ai-seo
    └── customer-research → copywriting, page-cro, competitor-alternatives
```

## 三、全部技能列表

### 3.1 转化优化（Conversion Optimization）

| 技能 | 触发场景 |
|------|----------|
| `page-cro` | 优化任何营销页面（首页、着陆页） |
| `signup-flow-cro` | 优化注册、账户创建流程 |
| `onboarding-cro` | 优化注册后激活、首次体验 |
| `form-cro` | 优化表单（除注册外的所有表单） |
| `popup-cro` | 优化弹窗、模态框、横幅 |
| `paywall-upgrade-cro` | 优化付费墙、应用内升级界面 |

### 3.2 内容文案（Content & Copy）

| 技能 | 触发场景 |
|------|----------|
| `copywriting` | 撰写营销文案（首页、landing page） |
| `copy-editing` | 编辑、润色现有文案 |
| `cold-email` | 撰写 B2B 冷启动邮件 |
| `email-sequence` | 创建自动化邮件序列 |
| `social-content` | 社交媒体内容创作 |

### 3.3 SEO 与发现（SEO & Discovery）

| 技能 | 触发场景 |
|------|----------|
| `seo-audit` | 技术SEO审计与诊断 |
| `ai-seo` | 优化 AI 搜索引擎（GEO/AEO/LLMO） |
| `programmatic-seo` | 规模化页面生成 |
| `site-architecture` | 网站结构、导航、URL 规划 |
| `competitor-alternatives` | 竞品对比页面 |
| `schema-markup` | 结构化数据标记 |

### 3.4 付费推广（Paid & Distribution）

| 技能 | 触发场景 |
|------|----------|
| `paid-ads` | Google Ads、Meta、LinkedIn 广告 |
| `ad-creative` | 广告创意生成和迭代 |
| `social-content` | 社交媒体内容 |

### 3.5 分析与测试（Measurement & Testing）

| 技能 | 触发场景 |
|------|----------|
| `analytics-tracking` | 设置分析追踪（GA4） |
| `ab-test-setup` | 设计 A/B 测试实验 |

### 3.6 留存与增长（Retention & Growth）

| 技能 | 触发场景 |
|------|----------|
| `churn-prevention` | 减少流失、构建挽留流程 |
| `free-tool-strategy` | 营销工具和计算器策略 |
| `referral-program` | 推荐和联盟计划 |

### 3.7 策略与变现（Strategy & Monetization）

| 技能 | 触发场景 |
|------|----------|
| `marketing-ideas` | 140+ SaaS 营销创意 |
| `marketing-psychology` | 心理学原理和心理模型 |
| `launch-strategy` | 产品发布和公告 |
| `pricing-strategy` | 定价、包装和变现策略 |

### 3.8 销售与运营（Sales & RevOps）

| 技能 | 触发场景 |
|------|----------|
| `revops` | 客户生命周期、销售营销对接 |
| `sales-enablement` | 销售 deck、一页纸、反对处理 |

### 3.9 其他技能

| 技能 | 触发场景 |
|------|----------|
| `customer-research` | 客户调研和分析 |
| `content-strategy` | 内容策略规划 |
| `community-marketing` | 社区建设和运营 |
| `lead-magnets` | 线索磁铁创建 |

## 四、安装指南

### 4.1 CLI 安装（推荐）

```bash
# 安装所有技能
npx skills add coreyhaines31/marketingskills

# 安装特定技能
npx skills add coreyhaines31/marketingskills --skill page-cro copywriting

# 列出可用技能
npx skills add coreyhaines31/marketingskills --list
```

### 4.2 Claude Code 插件安装

```bash
# 添加市场
/plugin marketplace add coreyhaines31/marketingskills

# 安装所有营销技能
/plugin install marketing-skills
```

### 4.3 克隆复制

```bash
# 克隆仓库
git clone https://github.com/coreyhaines31/marketingskills.git

# 复制技能到项目
cp -r marketingskills/skills/* .agents/skills/
```

### 4.4 Git 子模块

```bash
# 添加为子模块
git submodule add https://github.com/coreyhaines31/marketingskills.git .agents/marketingskills
```

### 4.5 SkillKit（多 Agent）

```bash
# 安装所有技能
npx skillkit install coreyhaines31/marketingskills

# 安装特定技能
npx skillkit install coreyhaines31/marketingskills --skill page-cro copywriting

# 列出可用技能
npx skillkit install coreyhaines31/marketingskills --list
```

### 4.6 目录结构

```
.agents/
├── skills/
│   ├── page-cro/
│   │   └── SKILL.md
│   ├── copywriting/
│   │   └── SKILL.md
│   ├── seo-audit/
│   │   └── SKILL.md
│   └── ... (40+ skills)
└── product-marketing-context.md
```

## 五、使用方法

### 5.1 自然语言触发

```
"帮我优化这个着陆页的转化率"
→ 使用 page-cro 技能

"为我的 SaaS 写首页文案"
→ 使用 copywriting 技能

"设置 GA4 追踪注册事件"
→ 使用 analytics-tracking 技能

"创建一个 5 封邮件的欢迎序列"
→ 使用 email-sequence 技能
```

### 5.2 斜杠命令触发

```bash
# 直接调用技能
/page-cro
/email-sequence
/seo-audit
/cold-email
```

## 六、核心技能详解

### 6.1 product-marketing-context（基础上下文）

**所有技能的根基**，定义产品、受众和定位。

```markdown
---
name: product-marketing-context
description: 当用户想创建或更新产品营销上下文文档时使用
---

# 产品信息

## 产品名称
[你的产品名称]

## 核心价值
[一句话描述核心价值]

## 目标受众
[描述你的理想客户画像]

## 竞争优势
[与竞品相比的独特卖点]
```

### 6.2 page-cro（页面转化优化）

**适用场景**：优化任何营销页面的转化率

```markdown
---
name: page-cro
description: 当用户想优化营销页面（首页、landing page）时使用
---

# 页面 CRO 分析框架

## 1. 价值主张
- 首要卖点是否清晰？
- 是否在 5 秒内传达价值？

## 2. 社会证明
- 是否有客户评价、Logo、案例研究？
- 信任信号是否充分？

## 3. 行动号召（CTA）
- CTA 按钮是否突出？
- 表单字段是否最少必要？
```

### 6.3 copywriting（文案撰写）

**适用场景**：撰写营销文案

```markdown
---
name: copywriting
description: 当用户想撰写或改进任何页面的营销文案时使用
---

# 文案撰写框架

## AIDA 模型
1. Attention（注意力）- 吸引眼球的开头
2. Interest（兴趣）- 建立联系
3. Desire（欲望）- 展示价值
4. Action（行动）- 明确的 CTA

## 标题公式
- 问题 + 解决方案
- 数字 + 结果
- 情绪 + 行动
```

### 6.4 seo-audit（SEO 审计）

**适用场景**：诊断网站 SEO 问题

```markdown
---
name: seo-audit
description: 当用户想审计网站的 SEO 问题时使用
---

# SEO 审计清单

## 技术 SEO
- [ ] 页面是否可被抓取？
- [ ] meta 标签是否优化？
- [ ] 结构化数据是否正确？

## 内容 SEO
- [ ] 关键词策略是否清晰？
- [ ] 内容质量是否足够？
- [ ] 内链结构是否合理？
```

### 6.5 cold-email（冷启动邮件）

**适用场景**：B2B 冷启动邮件

```markdown
---
name: cold-email
description: 当用户想写 B2B 冷启动邮件时使用
---

# 冷邮件框架

## 前提条件
- 目标客户画像清晰
- 价值主张明确

## 邮件结构
1. Hook（钩子）- 引起注意
2. Problem（问题）- 痛点共鸣
3. Solution（方案）- 你的解决方案
4. CTA（行动）- 明确下一步
```

## 七、最佳实践

### 7.1 技能组合使用

| 场景 | 技能组合 |
|------|----------|
| 新客获取 | page-cro + copywriting + paid-ads |
| 用户激活 | signup-flow-cro + onboarding-cro + email-sequence |
| 留存提升 | churn-prevention + analytics-tracking + ab-test-setup |
| SEO 优化 | seo-audit + ai-seo + schema-markup |
| 内容营销 | content-strategy + copywriting + social-content |

### 7.2 技能使用顺序

```
1. product-marketing-context（先读取）
    ↓
2. 相关技能（根据任务选择）
    ↓
3. 交叉引用（如需要）
```

### 7.3 自定义技能

```bash
# Fork 仓库后定制
git clone https://github.com/YOUR_USERNAME/marketingskills.git

# 修改特定技能
vim skills/page-cro/SKILL.md

# 在项目中使用
npx skills add YOUR_USERNAME/marketingskills --skill page-cro
```

## 八、版本升级

### 8.1 从 v1.0 升级

```bash
# 移动产品营销上下文文件
mkdir -p .agents
mv .claude/product-marketing-context.md .agents/product-marketing-context.md
```

> 注意：技能仍会检查 `.claude/` 作为回退，不会破坏现有设置。

## 九、资源链接

### 9.1 官方资源

| 资源 | 链接 |
|------|------|
| 🌐 **GitHub** | https://github.com/coreyhaines31/marketingskills |
| 📖 **技能列表** | https://github.com/coreyhaines31/marketingskills#available-skills |
| 📚 **文档** | https://github.com/coreyhaines31/marketingskills#readme |

### 9.2 相关工具

| 工具 | 说明 |
|------|------|
| **Claude Code** | AI 编码助手 |
| **SkillKit** | 多 Agent 技能管理 |
| **Agent Skills** | 技能规范 |

### 9.3 作者资源

| 资源 | 说明 |
|------|------|
| **Corey Haines** | 作者网站 |
| **Conversion Factory** | 转化优化代理服务 |
| **Swipe Files** | 营销洞察订阅 |
| **Magister** | AI CMO 助手 |

## 十、总结

Marketing Skills 是**AI Agent 营销助手技能库**：

| 维度 | 说明 |
|------|------|
| 📊 **40+ 技能** | 覆盖营销全链路 |
| 🤖 **AI Native** | 原生适配 AI Agent |
| 🔗 **技能联动** | 相互引用、协同工作 |
| 📈 **增长导向** | 转化优化、留存、裂变 |
| 🛠️ **开箱即用** | 多种安装方式 |

---

**🔗 相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/coreyhaines31/marketingskills |
| 技能规范 | https://agentskills.io |

---

_🦞 本文由钳岳星君撰写，基于 Marketing Skills (20.3k Stars)_
