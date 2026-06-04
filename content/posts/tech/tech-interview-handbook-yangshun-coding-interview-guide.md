---
title: "Tech Interview Handbook 深度解读：yangshun 大神 10 年心血，盲刷 75 题的演化史"
date: 2026-06-04T13:54:00+08:00
slug: tech-interview-handbook-yangshun-coding-interview-guide
description: "Tech Interview Handbook：超 100 万人受益的免费技术面试准备手册，Blind 75 → Grind 75 的演化，与 Cracking the Coding Interview 的差异。"
draft: false
categories: ["技术博客"]
tags: ["tech-interview-handbook", "yangshun", "blind-75", "grind-75", "面试", "算法"]
hiddenFromHomePage: true
---

## 一句话定位

Tech Interview Handbook 是前 Facebook / Quora / Grab 工程师 **yangshun** 维护的 **免费技术面试准备手册**，覆盖从简历、算法、行为面试到薪资谈判的**全流程**。超过 100 万人从中受益，**Blind 75**（最经典 75 题）就是出自作者之手。

> GitHub: https://github.com/yangshun/tech-interview-handbook
> 官网: https://www.techinterviewhandbook.org/
> 6 月 4 日 trending +116 stars

---

## 为什么这个项目经久不衰？

### 1. 它是「实用主义」的代表

相比 Cracking the Coding Interview（CTCI）那种"大部头教科书"，Tech Interview Handbook 的核心定位是：

> Not everyone has the time to do a few hundred LeetCode questions. Here are _free and curated_ technical interview preparation materials for busy engineers.

**给忙碌工程师用的精选内容**，而不是"穷举所有题目"。yangshun 明确说自己"不想用太多话烦你"，每个主题只给你**最关键的 20% 内容**。

### 2. 覆盖"全流程"而非只覆盖"算法题"

其他面试仓库基本只刷算法题，Tech Interview Handbook 覆盖 8 大主题：

1. **Best practice questions**（精选练习题）
2. **Grind 75**（Blind 75 的进化版，更大更全）
3. **How to prepare**（如何准备）
4. **Coding interview best practices**（面试中做与不做）
5. **Algorithm cheatsheets and tips**（按主题分类的速查表）
6. **Resume guide**（FAANG 级简历指南）
7. **Behavioral questions**（大厂行为面试题）
8. **Front end interview**（前端专项，已迁到子站）

### 3. Blind 75 → Grind 75：8 年演化的成果

- **Blind 75**（2017）：yangshun 在 Blind（美国匿名职场社区）发布的精选 75 题
- **Tech Interview Handbook**（2018-）：基于 Blind 75 扩展的完整手册
- **Grind 75**（2024）：Blind 75 的"v2"，题量更大，按时间安排分级

**Grind 75 的关键创新**：把题目按"时间投入"和"难度"分类，让学习者可以根据自己的备战时间（4 周 / 8 周 / 12 周）选择不同路径。这对"找工作 + 在职准备"的人尤其重要。

---

## 核心内容速览

### 1. 算法部分（最经典）

按主题分类的速查表覆盖：

- **数组 / 字符串 / 链表**
- **栈 / 队列**
- **树 / 图 / BFS / DFS**
- **动态规划**（最难的专题，给出"识别 DP 题的 5 个信号"）
- **回溯 / 贪心 / 二分搜索**
- **堆 / 优先队列**
- **设计题**（TinyURL、Twitter、Uber 等）

每个主题都给出：**核心套路 + 必刷题 + 套路总结**——这是"题海战术"和"系统掌握"的分水岭。

### 2. 简历部分

> Step-by-step Software Engineer resume guide to prepare a FAANG-ready resume.

特别值得国内工程师借鉴的几点：

- **格式**：单页 PDF，11pt 字体，Calibri / Roboto
- **项目描述公式**：`动词 + 对象 + 技术栈 + 量化结果`（如 "Reduced API latency by 40% by implementing Redis caching layer using Node.js and ioredis"）
- **不要写"熟悉 / 了解"**：直接写"Built / Designed / Led"
- **必须有数字**：99% 的 FAANG 简历都带 %/×/$/ms 数字

### 3. 行为面试部分

整理了 Google / Meta / Amazon / Apple 等大厂的高频行为题，附带 **STAR 法则**（Situation, Task, Action, Result）模板：

> "Tell me about a time when you had a conflict with a teammate."
> 答：Situation（背景）+ Task（你的具体任务）+ Action（你做了啥）+ Result（量化结果）

### 4. 算法套路

**最值得看的"识别题型的 5 个信号"**：

| 信号 | 通常题型 |
|------|----------|
| "Find all / count all" | DFS / 回溯 |
| "Minimum / maximum" | DP / BFS / 二分 |
| "Sorted array" | 二分 / 双指针 |
| "Tree / Graph" | DFS / BFS |
| "Substring / subsequence" | 滑动窗口 / DP |

---

## 与 Cracking the Coding Interview（CTCI）的差异

| 维度 | Tech Interview Handbook | CTCI |
|------|------------------------|------|
| **形式** | 免费 GitHub 仓库 + 网站 | 实体书 / Kindle |
| **价格** | 免费 | $30-50 |
| **题目量** | 75-200（精选） | 189（全） |
| **更新频率** | 持续更新（周/月级） | 不更新（已 6 版） |
| **覆盖范围** | 简历 + 算法 + 行为 + 谈判 | 只覆盖算法 + 行为 |
| **社区** | Discord 13k+ 成员 | 较少 |
| **语言支持** | EN + 中文翻译（部分） | EN |

**结论**：CTCI 是"经典教科书"，Tech Interview Handbook 是"现代生存手册"——后者更适合 2026 年的求职者。

---

## 适用人群

1. **3-10 年经验工程师**：准备跳槽 FAANG / 字节 / 阿里 / 腾讯
2. **应届生**：从算法零基础到能进大厂面试
3. **在职转码者**：时间有限，需要最高效的题目清单
4. **资深面试官**：想知道候选人怎么准备，反向优化面试设计
5. **国内 HR / 招聘**：对照检查自己的 JD / 面试流程是否合理

---

## 快速上手（4 周冲刺计划）

仓库给出的"标准 4 周备战"：

### Week 1：基础 + 简单题
- 看算法速查表，建立套路库
- 刷 Grind 75 中的所有 Easy 题
- 整理 STAR 故事 5 个

### Week 2：中等题
- 刷 Grind 75 的 Medium 题
- 每天 1 道"行为面试口头练习"
- 找人 mock interview 1 次

### Week 3：难题 + 系统设计
- 刷 Grind 75 的 Hard 题
- 开始准备系统设计（如果面 senior+）
- 找人 mock interview 2 次

### Week 4：模拟 + 收尾
- 全真模拟面试 2-3 次
- 整理 10 个最强 STAR 故事
- 优化简历 + LinkedIn
- 公司文化 / 价值观研究

---

## 国内借鉴意义

1. **"精选 75 题" 的思路对国内 LeetCode 刷题者也适用**。国内很多 LeetCode 刷题群已经有人整理"字节 75 题"、"阿里 75 题"，都是受 Blind 75 启发。
2. **STAR 法则对国内面试同样重要**。但要注意：国内大厂（尤其阿里、字节）还会追问"你在这个项目里具体做了什么"，需要更深的细节准备。
3. **简历公式对国内同样适用**。特别是"必须有数字"这一点，国内简历普遍欠缺。
4. **薪资谈判**章节也值得看——国内 offer 谈判经验帖满天飞，但很少有人把"如何反 offer"系统化。

---

## 项目生态

Tech Interview Handbook 已经发展成"系列项目"：

- **主站**（tech-interviewhandbook.org）：算法 + 行为 + 简历
- **Front End Interview Handbook**（frontendinterviewhandbook.com）：前端专项
- **Grind 75**（grind75.io）：题库
- **System Design Primer**（github.com/donnemartin/system-design-primer，已 fork 5w+）：系统设计

这些项目形成了一个"求职方法论生态"，互相导流。

---

## 链接

- GitHub 仓库: https://github.com/yangshun/tech-interview-handbook
- 官网（推荐阅读）：https://www.techinterviewhandbook.org/
- Grind 75 题库：https://www.techinterviewhandbook.org/grind75/
- 简历指南：https://www.techinterviewhandbook.org/resume/
- 算法速查表：https://www.techinterviewhandbook.org/algorithms/study-cheatsheet/
- Front End 子站：https://frontendinterviewhandbook.com
- Discord 社区：https://discord.com/invite/usMqNaPczq
- Twitter：https://twitter.com/techinterviewhb

**主要语言**：Markdown（文档），TypeScript（网站代码）
**开源协议**：MIT
**GitHub Trending**：2026-06-04 +116 stars
**作者**：yangshun（前 Facebook 工程师）
