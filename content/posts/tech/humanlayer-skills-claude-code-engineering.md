---
title: "humanlayer/skills：五个直击 Claude Code 真实痛点的工程技能"
date: 2026-09-12T03:45:00+08:00
slug: "humanlayer-skills-claude-code-engineering"
github_repo: "humanlayer/skills"
source_key: "gh:humanlayer/skills"
description: "HumanLayer 出品的 Claude Code skills 合集，只有五个技能却各自瞄准真实工程痛点：CLAUDE.md 指令遵循、React prop 类型收敛、迭代式 agent 工作流、控制回路设计与可视化解释。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "AI 工程化", "开源"]
---

# 当 skills 合集开始做减法

Agent skills 生态正在经历一场数量竞赛，而 HumanLayer 的这个合集反其道而行：**只有五个技能，每一个都对应一个可验证的工程痛点**。HumanLayer 是 12-Factor Agents 的作者团队，这个背景决定了合集的取向——不追花哨能力，专注让 coding agent 在真实代码库里更可控。

合集当前 3,755 Stars，TypeScript 为主，MIT 协议，最近一次实质性更新在 2026 年 8 月中旬。安装方式统一为 `npx skills add humanlayer/skills --skill <名称>`。

## 五个技能分别在解决什么

| 技能 | 痛点 | 一句话机制 |
|---|---|---|
| improve-claude-md | CLAUDE.md 指令遵循率低 | 用 `<important if>` 条件块重写指令 |
| narrow-react-prop-types | prop 类型被 Storybook/mock 撑宽 | 按真实代码路径收敛类型 |
| build-iterated-agentic-loop | 想要可持续迭代的 agent 工作流 | 生成 repo 内 skill + GitHub Actions 循环 |
| design-control-loop | agent 任务缺乏结构化设计 | 访谈式设计传感器/控制器/执行器回路 |
| show-me | 需要快速理解陌生话题 | 图表 + 代码形态草图 + HTML 产物解释 |

前两个是"修 bug"型技能，值得展开。

**improve-claude-md** 针对的是几乎所有 Claude Code 用户都遇到过的问题：CLAUDE.md 写了几十条指令，模型只稳定遵循其中一部分。它的思路不是加更多指令，而是把指令重构成 `<important if>` 条件块——让指令在满足前置条件时才生效，降低上下文中的指令密度。这与 HumanLayer 在 12-Factor Agents 中"小而精的提示词优于大而全"的主张一脉相承。

**narrow-react-prop-types** 处理的类型漂移问题更隐蔽：组件的 TypeScript 类型为了兼容 Storybook、测试和 mock 被不断放宽（可选属性、宽联合类型），而真实运行路径只用其中一小部分。这个技能分析实际代码路径后把类型收敛回真实使用面——本质是把类型系统从"文档"恢复为"约束"。

后三个是"建系统"型技能：build-iterated-agentic-loop 一键生成仓库级 skill 加迭代式 GitHub Actions 工作流（含 prompt、记忆文件和参考模板）；design-control-loop 用控制论框架（sensor / controller / actuator / disturbances）访谈式地为你代码库定制一个可本地运行的 agent 回路；show-me 则偏向学习场景，用简图和代码形态草图解释当前话题。

## 为什么这套合集值得看

它示范了 skills 生态里一种稀缺的品质：**每个技能都有明确的问题定义和验收标准**。improve-claude-md 的效果可以直接用指令遵循率验证；narrow-react-prop-types 的产出可以直接过类型检查。相比之下，大量"提升代码质量"类 skills 连判断是否生效的标准都没有。

从工程趋势看，这也是 12-Factor Agents 方法论落地为可安装产物的尝试——把"agent 应该小、可测试、有明确契约"的原则，压缩成五条可以直接装进 Claude Code 的命令。

## 适用边界

- **适合**：Claude Code 重度用户，尤其是 CLAUDE.md 已经膨胀、TypeScript 类型被测试代码污染的团队；想借鉴"如何写一个好 skill"的 skill 作者。
- **不适合**：期待大而全技能库的用户（去 anthropics/claude-plugins-community 或 openai/skills 更合适）；非 Claude Code 生态（合成的调用方式绑定斜杠命令）。
- **注意**：show-me 在 8 月的提交中还在调整 file-tree 示例的渲染字形，说明部分技能仍在快速打磨期，生产使用前建议先在隔离分支验证效果。

## 结语

五个技能，五个明确的工程问题，两条可度量的修复路径——humanlayer/skills 是 agent skills 从"能力展示"走向"工程工具"的一个干净样本。即使不安装，它对 CLAUDE.md 结构化和类型收敛的思路也值得直接借用到自己的工作流里。
