---
title: "ossu/computer-science 拆解：一份 206k stars 的免费计算机科学自学路径，是怎么用课程而不是书把 CS 本科拼起来的"
date: 2026-07-17T02:58:33+08:00
lastmod: 2026-07-17T02:58:33+08:00
draft: false
categories: ["技术笔记"]
tags: ["OSSU", "Computer Science", "Curriculum", "Self-Taught"]
description: "OSSU Computer Science 是 Open Source Society University 的免费 CS 自学路径，按 CS 2013 标准选取 MIT/Princeton 公开课，4 段路径约 20 小时/周 × 2 年。"
weight: 1
slug: "ossu-computer-science-self-taught-cs-curriculum"
author: text-matrix
---

## 一句话判断

**OSSU Computer Science（[ossu/computer-science](https://github.com/ossu/computer-science)）是 Open Source Society University 维护的"用在线课程代替本科 CS 学位"自学路径，截至 2026-07 在 GitHub 上约 206k stars / 25.6k forks，MIT 许可证。** 它不是又一份书单，而是一份**严格对齐 CS 2013 课程标准**（Curriculum Guidelines for Undergraduate Degree Programs in Computer Science）的本科级路径：候选课程必须满足"开放注册、定期开课、教学质量高、对齐 CS 2013"四条标准，否则就补充书。**它和"awesome-CS-resources"类资源列表的最大差别在于——它是按"学位要求"反向设计，而不是按"主题热度"正向堆料**。

如果你在自学 CS 但一直被"该学什么、按什么顺序、用什么教材"三个问题困住，或者你已经在工作中但想系统补 CS 基础，这篇文章值得完整读完。

---

## 系统地图

OSSU 的真实结构不是 README 顶部那张 logo，而是按"课程标准 → 学位要求 → 课程编排 → 进度管理"四层组织的工程化路径：

```
┌──────────────────────────────────────────────────────────────────────┐
│  顶层标准 (Standard)                                                    │
│   CS 2013: Curriculum Guidelines for Undergraduate Degree Programs    │
│   in Computer Science  (ACMU / IEEE-CS 联合发布的本科 CS 课程指南)      │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼────────────────────────────────────┐
│  学位要求映射 (Reverse-engineered from real CS degrees)                │
│   - Intro CS   (体验 CS 是否适合自己)                                    │
│   - Core CS    (≈ 本科前 3 年必修)                                       │
│   - Advanced CS (≈ 本科最后 1 年选修)                                    │
│   - Final Project (用项目验证、巩固、展现知识)                            │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼────────────────────────────────────┐
│  课程编排 (Course selection, 四条硬标准)                                  │
│   ① 开放注册                                                            │
│   ② 定期开课 (self-paced 或每年多次)                                     │
│   ③ 教学质量高                                                          │
│   ④ 对齐 CS 2013 课程标准                                               │
│   当没有课程满足 → 用书补                                                 │
│   当书/课不符合但质量高 → 进 extras/courses 或 extras/readings           │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼────────────────────────────────────┐
│  进度管理 (Operational layer)                                            │
│   - Discord 社区 + GitHub Issues 提问                                   │
│   - 进度估算表 (Google Sheet: Timeline / Curriculum Data)               │
│   - 推荐 CS.OSSU.dev 网站 + 本仓库做权威源                              │
│   - 已知过期第三方资源警示 (Firebase / Trello / Notion)                  │
└──────────────────────────────────────────────────────────────────────┘
```

这张图最重要的一条路径：**"标准 → 学位要求 → 课程编排 → 进度管理"**。OSSU 之所以不是一份资源列表，是因为它**有顶层标准做约束**——任何不符合 CS 2013 的资源都被推到 extras/，主路径只留"对得上学位要求"的内容。

---

## 边界与角色划分

把 OSSU 拆成 5 组"不变项"，可以一次性回答它和公开课平台（Coursera / edX / MIT OCW）、书单（CS-Notes / SDE-skills）、训练营的差别：

| 维度 | OSSU 的不变项 | 工程含义 |
|------|----------------|---------|
| 顶层依据 | CS 2013 课程标准 | 不是按主题选，而是按"学位要求"反推；任一课程都必须能映射到 CS 2013 的某项要求 |
| 选课标准 | 4 条硬标准（开放、定期、高质量、对齐） | 候选课程必须全部满足，否则用书补；这条规则让 OSSU 不"卷"课程数量 |
| 内容形态 | 课程优先，课程缺位时用书 | 主干课程（哈佛 / MIT / 普林斯顿），边角主题用书或推到 extras/ |
| 学习时长 | 约 20 小时/周 × 2 年 | 不是"几个月速成"，是"用真时间堆出来"；这是它和训练营最大差别 |
| 社区形态 | Discord + GitHub Issues 双轨 | Discord 是日常交流，Issues 是课程层面的纠错与更新 |

要注意的几个边界：**OSSU 不是学位**——它的目标是把 CS 本科核心学完整，不替代正式学位；**它不是速成训练营**——它的承诺是"2 年 × 20 小时/周"，想几个月刷完的会失望；**它不是固定书单**——主干是课程，书只补课程覆盖不到的部分。

---

## 关键机制

### 1. CS 2013 作为唯一硬约束

CS 2013 是 ACM 和 IEEE-CS 联合发布的本科 CS 课程指南，把本科 CS 教育分成若干知识领域（Knowledge Areas），每个领域下有若干学习单元。OSSU 的所有内容选择都必须能映射回这张表。

这条机制的工程含义是：

- 当你学完 Core CS，你覆盖的是"所有 CS 本科生前 3 年的必修面"
- 当你学完 Advanced CS，你覆盖的是"最后 1 年的选修方向"
- "学完"不等于"精通"，但等于"本科课程覆盖到了"

这和"awesome-list 按热度堆资源"形成鲜明对比——OSSU 删过很多热门但偏离 CS 2013 的内容，把它推到 `extras/courses` 或 `extras/readings`。

### 2. 四段式路径：Intro / Core / Advanced / Final Project

OSSU 把整个学习路径切成 4 段：

| 阶段 | 时长参考 | 必修/选修 | 关键产出 |
|------|---------|----------|---------|
| Intro CS | 14 周 × 6-10 h/周 | 必修 | 用 Python 体验 CS，判断是否继续 |
| Core CS | 约 1.5 年 × 20 h/周 | 全部必修 | 本科前 3 年的所有必修面 |
| Advanced CS | 约 0.5 年 × 20 h/周 | 选修（按方向） | 一个细分方向的深度 |
| Final Project | 数周-数月 | 必修 | 一个展示、巩固所学知识的项目 |

这种分段的价值在于**给出"完成度"信号**：学完 Intro CS 你知道 CS 适不适合自己；学完 Core CS 你有"相当于 CS 本科生前 3 年"的能力底座；学完 Advanced CS 你有方向深度；做完 Final Project 你有一份能展示的作品。

### 3. Core CS 内的 8 大领域

Core CS 是 OSSU 的核心，覆盖以下 8 个领域：

| 领域 | 关键主题 | 代表课程 |
|------|---------|---------|
| Core programming | 函数式编程 / 设计模式 / 静态与动态类型 / ML/Racket | Systematic Program Design / Programming Languages / OOD |
| Core math | 离散数学 / 数学证明 / 概率 / 大 O | Calculus 1A/1B/1C (MIT) / Mathematics for CS (MIT) |
| CS Tools | Shell / Vim / 命令行环境 / 版本控制 | The Missing Semester of Your CS Education (MIT) |
| Core systems | 过程式编程 / 手动内存管理 / 布尔代数 / 门电路 / 内存 / 计算机体系结构 / 汇编 | Nand2Tetris 系列 / Computer Architecture / OS / 网络 |
| Core theory | 算法 / 计算理论 / 计算复杂度 / 形式语言与自动机 | Algorithms (Princeton) / Theory of Computation |
| Core security | 密码学 / 系统安全 / 网络安全 | Cryptography (Stanford) / Security / Web Security |
| Core applications | 函数式编程应用 / 数据库 / 并发 / 分布式 | Parallel/Concurrent/Functional Programming / DB / Cloud Computing |
| Core ethics | 科技伦理 / 法律 / 隐私 | 伦理相关课程与读物 |

8 个领域全部为必修，是 OSSU 把"广度"作为第一目标的具体落地。

### 4. Advanced CS：选一个方向做到深

Advanced CS 不是"全部学完"，而是按方向选修：

- **Advanced programming**——函数式 / 并发 / 高性能 / 系统编程
- **Advanced systems**——操作系统 / 分布式系统 / 数据库内核
- **Advanced theory**——算法进阶 / 计算理论 / 形式化方法
- **Advanced information security**——密码学进阶 / 二进制安全 / 渗透
- **Advanced math**——线性代数 / 概率 / 数论 / 信息论

选修策略是"选一个 subject 全做完"，不要"每个 subject 浅尝"。Discord 社区可以为你的自定义方向给反馈。

### 5. Final Project：把所学变成作品

Final Project 是 OSSU 把"知识 → 能力"转换的强制环节。它的要求是：

- 选一个**真实问题**而不是教学练习
- 项目要**贯穿多个领域**（不是只用了算法或只用了数据库）
- 由社区**全球同行评审**——OSSU 把"评估"环节外包给同伴，强调"show your work"

这条机制让 OSSU 区别于"读完课就结束"的路径：Final Project 是真正的产出物，可以放到简历、GitHub、个人作品集。

### 6. 进度估算表 + Discord 同行

OSSU 提供了一份 Google Sheet 帮你估算完成时间：

- `Timeline` sheet：输入开始日期和每周小时数，自动算预期完成日期
- `Curriculum Data` sheet：记录你每门课的实际完成日期，自动更新预估

**注意**：README 自己警告，这份 sheet 不一定永远跟最新课程同步，权威源是 [cs.ossu.dev](https://cs.ossu.dev) 和本仓库本身。

社区是 Discord + GitHub Issues 双轨：Discord 是日常交流、问题讨论；GitHub Issues 是课程质量反馈、课程替换建议、FAQ 更新。

### 7. 严格的过期资源警示

README 明示"几个第三方过期/废弃材料"——Firebase app、未维护的 Trello 板、第三方 Notion 模板——这些都不是权威源，**只用 cs.ossu.dev 和 GitHub 仓库**。这条警示对自学路径的稳定性很关键：网络上很多 OSSU 衍生内容是几年前的快照，跟着它们走会被坑。

---

## 一个学习者如何流过 OSSU

下面以一个 0 基础、目标"补齐 CS 本科核心"的工程师走一遍：

```
第 0 周: 加入 Discord, 在 #introductions 发自我介绍
        │
        ▼
第 1-14 周: Intro CS
  - 完成 MIT 6.00.1 (Python intro)
  - 输出: 能写出 100-300 行的小程序
        │
        ▼
第 15-50 周: Core CS - Core programming + Core math + CS Tools
  - Systematic Program Design → Class-based → Programming Languages → OOD
  - Calculus 1A/1B/1C → Mathematics for CS
  - The Missing Semester
  - 输出: 熟悉 ML/Racket/OOP, 离散数学与微积分基础, 命令行/Vim/Git
        │
        ▼
第 51-100 周: Core CS - Core systems + theory + security + applications + ethics
  - Nand2Tetris (从与非门到完整计算机) → Architecture → OS → Networks
  - Algorithms (Princeton) → Theory of Computation
  - Cryptography (Stanford) → Security 系列
  - DB / Cloud Computing / 分布式
  - 输出: 系统 + 算法 + 安全 + 应用的本科级广度
        │
        ▼
第 101-125 周: Advanced CS - 选一个方向 (e.g. Advanced systems)
  - OS 进阶 / 分布式系统 / 数据库内核
  - 输出: 一个细分方向的深度
        │
        ▼
第 126-150 周: Final Project
  - 选一个真实问题 (e.g. 写一个简化版分布式 KV store)
  - 项目公开在 GitHub, Discord 拉评审
  - 输出: 一份能放进简历的作品
        │
        ▼
完成 → LinkedIn 上加 "Open Source Society University" 学校条目
```

这个流程覆盖了 **4 段路径 × 8 个 Core CS 领域 × 1 个 Advanced 方向 × 1 个 Final Project**。关键看 4 件事：

1. **课程标准 → 学位要求 → 课程编排** 的反推链路在每个阶段都生效
2. **完成度信号明确**——学完每段你能清楚知道"我现在到哪了"
3. **Final Project 是强制产出**——区别于"读完就算学完"
4. **进度估算与同行评审是运营层**——让 2 年路径可持续

---

## 采用顺序与适用边界

### 推荐采用顺序

1. **先在 Discord 看 1-2 周**——判断社区氛围与你的预期是否吻合；OSSU 强调自学、自律、社区支持，没有"教练盯着你"
2. **先做 Intro CS**——这是 14 周的"试婚期"，避免"all in 后才发现 CS 不适合你"
3. **完成 Core CS 的编程与数学**——这是底座，没有这两块后面的领域全是空中楼阁
4. **坚持在 GitHub Issues 上报课完成情况**——把进度沉淀下来，便于社区给你反馈
5. **Advanced CS 选一个方向深扎**——不要贪多
6. **Final Project 公开化**——放到 GitHub / 个人作品集 / Discord 拉评审

### 适用边界

| 适合 | 不适合 |
|------|--------|
| 有纪律、有自学意愿、能坚持 2 年 | 想要"几个月刷完"的速成承诺 |
| 想要系统补 CS 本科级广度 | 只想学某一个具体方向（如"学点 ML"） |
| 能接受 Harvard / MIT / Princeton 等英文授课 | 英文听力 / 阅读有困难（OSSU 主路径无中文翻译） |
| 想要免费 + 不需要正式学位 | 需要正式学位 / 学历认证的场景 |
| 能投入约 20 小时/周 | 每周 < 5 小时（路径会无限延长） |
| 愿意在 Discord 提问 + 用 GitHub Issues 反馈 | 想要"教练陪跑 / 班主任" 形态 |

### 风险与未知项

- **课程链接漂移**——Cousera / edX / MIT OCW 的链接与开课节奏会变，OSSU 通过 GitHub Issues + cs.ossu.dev 维护权威源，但仍需自查当前链接是否仍可用
- **课时量级**——20 小时/周 × 2 年是相对乐观的估算，业余学习者实际可能拉到 3 年；建议把"完成度"而非"截止日期"作为目标
- **完成率极低**——OSSU 这种长路径的"完成率"在开源自学路径中普遍偏低；把它当作"课程目录"，而不是"学位承诺"，会更健康
- **替代品**——如果你只想"学点编程"，CS50 / freeCodeCamp 更合适；OSSU 的价值在"学位级广度"，不是"入门更快"
- **MIT OCW 替代**——MIT OCW 提供几乎所有 MIT 课程的全部材料，OSSU 帮你做了选择和顺序，但 OCW 本身是更底层的内容源

---

## 一处延伸阅读

如果想继续深入：

- [ossu/computer-science 仓库](https://github.com/ossu/computer-science)——主仓库，README 是路径的起点
- [OSSU CS 网站 cs.ossu.dev](https://cs.ossu.dev)——课程的官方镜像 + 进度管理入口
- [CS 2013 课程指南 CURRICULAR_GUIDELINES.md](https://github.com/ossu/computer-science/blob/master/CURRICULAR_GUIDELINES.md)——OSSU 顶层标准的源文件，理解"为什么这么排"必读
- [OSSU Discord](https://discord.gg/wuytwK5s9h)——日常交流 + Final Project 同行评审主战场
- [OSSU 进度估算 Sheet](https://docs.google.com/spreadsheets/d/1y2kMsIg9VaHMVmw35x_aH1hpty3V-ZMuV2jA13P_Cgo/copy)——按 20 小时/周 + 开始日期估完成时间（注意 README 警告：可能不总是最新）
