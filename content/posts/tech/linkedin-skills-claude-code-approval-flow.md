---
title: "linkedin-skills：12 个让 Claude Code 替你经营 LinkedIn 的开源技能，先出草稿再等人批准"
date: 2026-09-23T04:30:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "Agent Skills", "LinkedIn", "开源项目"]
description: "sergebulaev/linkedin-skills 是一套 MIT 协议的 Claude Code / Codex 技能包：写帖、评帖、回复、去 AI 味、逆向爆款钩子、七日内容规划等 12 个技能，全部走先草稿后审批的流程。本文拆解其技能矩阵、数据读取与自动发布两层可选依赖及适用边界。"
github_repo: "sergebulaev/linkedin-skills"
source_key: "gh:sergebulaev/linkedin-skills"
slug : linkedin-skills-claude-code-approval-flow
---

## 核心判断

"用 AI 写社交媒体内容"的工具泛滥，但绝大多数有两个通病：一是发布即失控，AI 直接把内容推出去，人没有审阅机会；二是生成的东西一眼 AI 味，反而损害账号。linkedin-skills（[sergebulaev/linkedin-skills](https://github.com/sergebulaev/linkedin-skills)）针对这两点给出了工程化的答案：**每个技能都先出草稿、等人批准才行动**（README 反复强调 "waits for your OK before anything gets published"），并且专门做了一个 Humanizer 技能来处理 AI 文风特征——还诚实标注了"不承诺骗过检测器，因为没有任何编辑能可靠做到"。

这套技能包针对 Claude Code 和 Codex 设计，无需写代码，装好后直接用自然语言唤起。MIT 协议，约 3,200 Stars，同一团队还发布了 X、Instagram、YouTube、TikTok、Threads、Facebook 的姊妹技能包，共享同一套声音引擎和审批流。

## 技能矩阵：12 个技能干什么

| 类别 | 技能 | 做什么 |
|------|------|--------|
| 写 | **Post Writer** | 用 20 个 2026 年验证过的钩子公式（排比、悬念缺口、冷开场等）起草帖子，按互动目标选型 |
| 写 | **Humanizer** | 逐段评分 AI 词汇密度，处理 reveal bridge、碎句堆叠、表演式真诚等特征；附带多检测器交叉测试子工具 |
| 写 | **Repurposer** | 把推文、视频、博客改写成原生 LinkedIn 帖：重做钩子、扩到 900-1300 字符甜点区、链接移到评论区 |
| 读 | **Comment Drafter** | 给任意帖子的 URL 起草评论 |
| 读 | **Reply Handler** | 起草回复，正确处理 LinkedIn 两层评论扁平化；给一个帖子 URL 可整串扫完所有评论批量起草 |
| 读 | **Hook Extractor** | 逆向任何爆款帖的钩子公式，返回可填空的模板 |
| 读 | **Engagement Monitor** | 跟踪评论线程等作者回复；拉取点赞评论者并按 ICP 匹配度分组 |
| 运营 | **Content Planner** | 七日内容计划：每日主题、格式、钩子、发布时间、评论目标 |
| 运营 | **Profile Optimizer** | 按 2026 转化模式重写 headline、About、Featured 区 |
| 运营 | **Employee Advocacy** | 团队 LinkedIn 计划：14 天启动、发布节奏、品牌治理、ROI 追踪 |
| 基建 | **Interviewer** | 采访你并把回答存进 Story Bank（角色、真实数字、转折点），其他技能都读它，起草时不再中途追问数字 |
| 基建 | **Post Audit** | 发布前按 2026 算法规则和 AI 检测模式检查草稿 |

设计上值得注意的一笔：**Interviewer 是唯一"零发帖历史也能用"的技能**——它依赖你的职业经历而非历史帖子，冷启动用户的入口。Story Bank 作为共享素材层，让 12 个技能形成闭环而不是各自为战。

针对创始人还有专门一层：10 个创始人角度模板（重新定价品类、audience of one、稀缺机会成本等）和 4 个结构性钩子公式，优化目标从"曝光"换成"少数高价值读者的信任"。

## 两层可选依赖

技能包本身免费可用，读帖和自动发布是两个可选增强：

**Apify（读数据）**：Comment Drafter、Reply Handler、Hook Extractor、Engagement Monitor 四个技能可用 Apify 读取帖子正文、评论、互动者。没有 token 时降级为让你手动粘贴文本。免费额度每月 $5，典型创作者日评论运营 + 周互动分析月成本不到 $2。

**Publora（自动发布）**：默认模式是起草后你自己复制粘贴；接上 Publora 发布 API（免费层每月 15 帖）后可让 agent 直接发布，它处理了 LinkedIn 的三种 URL 格式、反应类型错位、评论串扁平化 bug 等坑。两种接入方式（connector 或 API key）明确定位为并列而非主次。

自检体验做得细：`python3 scripts/selftest.py` 一条命令报告 Apify / Publora / Pixfaro 各自状态，且"缺哪层、哪些技能仍可用"说得明确，而不是只报一个红叉。

## 安装

跨 agent 通用的一行命令：

```bash
npx skills add sergebulaev/linkedin-skills
```

Claude Code 内也可用 `/plugin marketplace add sergebulaev/linkedin-skills`；OpenClaw 用户按 README 说明 clone 仓库进工作目录并在系统提示词里指路即可。装好后直接说"帮我写一条关于 X 的 LinkedIn 帖子"，对应技能自动激活。

## 适用边界

- **面向 LinkedIn 运营者，不是开发者工具**：价值在于内容生产流程，不含任何编程 API 封装；
- **发布侧依赖第三方服务**：自动发布走 Publora（免费层 15 帖/月），介意第三方依赖的人停在"草稿 + 手动粘贴"模式即可，功能主体不受影响；
- **中文场景未验证**：钩子公式、AI 词汇密度评分都针对英文 LinkedIn 生态构建，直接用于中文内容的效果 README 未提及，需要自行测试；
- 团队明确说明核心包保持 11 个技能 + 1 条读写管道，社区技能（如 linkedin-outreach）放作者各自仓库，装在旁边即可——核心与扩展的边界清晰。

一句话：它是把"LinkedIn 内容经营"拆成 12 个可组合、带审批门控的技能的一次认真工程化尝试，尤其适合已经在用 Claude Code 且需要持续产出 LinkedIn 内容的创业者和运营者。
