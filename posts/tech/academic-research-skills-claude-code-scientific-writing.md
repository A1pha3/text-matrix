---
title: Academic Research Skills - 科研全流程AI辅助工具（面向Claude Code）
date: 2026-05-18
tags:
  - 科研
  - AI辅助写作
  - Claude Code
  - 论文发表
  - 开源工具
---

# Academic Research Skills：科研全流程 AI 辅助工具（面向 Claude Code）

**Stars: 10,578** | **今日: +1,132** | **Python**

GitHub: [Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills)

## 一句话评价

为 Claude Code 打造的完整学术研究工作流，从文献检索、综述写作、同行评审到引用核查，覆盖科研论文全生命周期，v3.9.3 内置幻觉检测、信任链溯源和事实审计功能，避免 AI 辅助写作的常见陷阱。

## 核心问题：AI 辅助科研的边界在哪里？

作者引用 Lu et al. 2026 (Nature 651:914-919) 的研究指出：The AI Scientist 是首个以盲审同行评审在顶会发表论文的 AI 系统（ICLR 2025 workshop），但其 Limitations 章节枚举了全自主 AI 研究管道的共同失败模式：实现 bug、幻觉结果、捷径依赖、bug 即洞察的重新框架、方法论伪造、框架锁定、引用幻觉。

**ARS 的前提**：人类研究者 + AI 辅助，比纯 AI 或纯人类都更可靠。v3.9 版本重点针对 Zhao et al. (2026-05) 对 1.11 亿条引用的审计发现（2025 年单年估计 146,932 条幻觉引用）进行了专项优化。

## 核心功能

### Deep Research（13 Agent 研究团队）
- Socratic 引导式研究模式
- PRISMA 系统综述支持
- 语义 Scholar API 验证
- 跨模型验证（可选）
- 对话健康监控

### Academic Paper（12 Agent 论文写作）
- **Style Calibration**：学习你的写作风格
- **Writing Quality Check**：检测"AI 味"表达
- LaTeX 加固、图表可视化
- 修订辅导（Revision Coaching）
- 引用转换、泄露检测
- VLM 图表验证

### Academic Paper Reviewer（7 Agent 同行评审）
- 多视角评审（0-100 质量量表）
- Devil's Advocate 质疑机制
- 让步阈值协议
- R&R 追踪矩阵

### v3.8 / v3.9 新增：引用事实审计（ARS_CLAIM_AUDIT=1）
针对 Zhao et al. 的研究发现，v3.8 新增可选审计通道：逐条抓取引用来源、验证声明是否被实际支持。五个 HIGH-WARN 类别（claim-not-supported / fabricated-reference / anchorless 等）通过硬门禁拒绝输出。

## 安装

```bash
# Claude Code 插件方式安装（推荐，30秒）
/plugin marketplace add Imbad0202/academic-research-skills
/plugin install academic-research-skills

# 然后运行
/ars-plan    # Socratic 对话规划论文结构
/ars-lit-review "your topic"  # 快速文献综述
```

**前提**：Claude Code 最新版 + `ANTHROPIC_API_KEY` 环境变量

## 成本估算

完整流程（约 15,000 字论文）预计消耗 $4–6（Token 预算见 `docs/PERFORMANCE.md`）。

## 设计理念

> "AI 是副驾驶，不是飞行员。这个工具不会替你写论文。它处理苦活累活——找文献、整理引用格式、验证数据、检查逻辑一致性——让你专注于真正需要大脑的部分：定义问题、选择方法、解读数据、写好每一句论点。"

## 适用人群

- 研究生 / 博士生（论文写作阶段）
- 研究工程师（技术报告）
- 学术写作者（希望保持学术诚信）