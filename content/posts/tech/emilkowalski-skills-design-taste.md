---
title: "emilkowalski/skills：把 UI 动画与设计品味的微决策交给代理"
date: 2026-08-02T02:59:48+08:00
slug: "emilkowalski-skills-design-taste"
description: "emilkowalski/skills 是一个面向设计与前端工程师的 Agent Skills 集合，覆盖动画缓动、阴影/边框、留白、图标等 UI 微决策，作者来自 Vercel/Linear 等团队；目标是把\"代理没品味\"这件事压到最小。"
draft: false
categories: ["技术笔记"]
tags: ["Agent Skills", "UI 设计", "前端", "动画", "品味"]
---

## 一句话判断

`emilkowalski/skills` 的作者在 Linear/Vercel 待过，技能内容是他在公司里学到的"小到不值得专门讲、大到毁掉整个 UI"的微决策——缓动方向选错、阴影写实、留白不均衡、图标粗细不一。技能让代理按需加载这条经验库，把"AI 写 UI 就是差点意思"这件事压到最少。

## 项目定位

仓库自我定位很克制：

> Skills For Design Engineers.
> For designers and engineers to help them build better user interfaces.
> Knowing whether you made a right choice when it comes to animations, or design in general, is hard. These skills aim to help you get to those right decisions faster.

作者明确说：

> Agents don't have great taste.
> ... an `ease-in` easing for an enter animation when it's supposed to be `ease-out`. Or they choose a solid border instead of a semi-transparent shadow for your UIs.

他把所有这些"代理会做错的微决策"汇总成 SKILL 描述，并在文章 [Agents with Taste](https://emilkowal.ski/ui/agents-with-taste) 里展开。

## 安装

```bash
npx skills@latest add emilkowalski/skills
```

也可以通过 [skills.sh/b/emilkowalski/skills](https://skills.sh/emilkowalski/skills) 浏览。

## 技能颗粒度

和一般"框架级"前端技能不同，`emilkowalski/skills` 的颗粒度细到单条决策：

| 主题 | 例子 |
|------|------|
| 缓动 | enter 动画必须 `ease-out`，exit 必须 `ease-in`；列表项 stagger 不超过 50ms |
| 阴影 | 优先半透明阴影而非实色边框；阴影模糊与 Y 偏移成比例 |
| 留白 | 8/12/16/24 节奏，避免任意 px |
| 图标 | stroke-width 与字号同步；线性图标用 1.5/2/2.5 三档 |
| 排版 | 行高与字号比例恒定；首屏段落不超过 3 行 |
| 配色 | 文本层级靠透明度而非新颜色 |

每一条都是 README 里"Agents don't have great taste"那一段的对应补丁。

## 一次完整使用流

把"用 Claude Code 重做一个 onboarding 弹窗"当样本：

1. 用户提需求："做一个三步 onboarding 弹窗，要 Linear 那种克制感"
2. 代理激活 `emilkowalski/skills`，按当前任务匹配"enter 动画 + 阴影 + 留白"三条微决策
3. 代理生成组件代码，自动把 enter 动画设成 `ease-out`、阴影用半透明、留白走 8/12/16 节奏
4. 用户拿到组件后无需再"调一调颜色""调一调间距"

如果不用这套技能，代理经常交出"动起来了但方向不对 / 颜色太多 / 留白忽大忽小"的结果，需要人手动擦一遍。

## 与同类项目的位置

| 项目 | 覆盖域 | 颗粒度 |
|------|-------|--------|
| `pbakaus/impeccable` | 通用前端品味 | 中（按主题划分） |
| `emilkowalski/skills` | 动画 + UI 微决策 | 细（按具体决策点） |
| `ayghri/i-have-adhd` | 输出形态 | 跨域（不限于 UI） |

三件套常常一起装：impeccable 提供审美骨架，emilkowalski 填充动画与留白细节，i-have-adhd 把"代理回答的形态"压成可执行步骤。

## 适用边界与不适用边界

**适用**：

- 已经在用 Claude Code/Codex 做 UI 编码，并被"AI 写 UI 就是差点意思"反复消耗的人
- 团队希望把"什么是 Linear 级别的克制感"沉淀成可复用资产
- 想让代理对 Figma 设计稿有更接近设计师意图的实现

**不适用**：

- 高端品牌设计 / 平面海报 / 插画（这些仍需要设计师本人）
- 完全没碰过 UI 工程的纯后端人（技能不会教你读设计稿）
- 期待它替代 Linear/Vercel 的 Design System：技能解决的是"判断"，不是组件库

## 一句话总结

`emilkowalski/skills` 把"代理为什么写不出有品味的 UI"这个问题拆成几十条可加载的微决策补丁；它对代理的提升等同于把资深设计师的经验切片喂给模型。