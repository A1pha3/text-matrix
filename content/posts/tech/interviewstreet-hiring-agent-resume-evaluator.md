---
title: "Hiring Agent：InterviewStreet 开源的简历评分 Agent 管线，PDF→JSON→GitHub 增强→公平评分"
date: 2026-06-24T20:55:27+08:00
slug: "interviewstreet-hiring-agent-resume-evaluator"
description: "Hiring Agent 是 InterviewStreet 开源的简历智能评估 Agent：用 pymupdf_rag 把 PDF 转 Markdown，按 section 用 LLM 抽 JSON，再用 GitHub 信号补强，最后跑严格约束下的多维评分。Ollama 本地或 Gemini 云端双后端，本文拆解其架构、Pydantic 数据模型与公平性约束。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "简历评估", "Hiring", "Python", "Pydantic", "Ollama", "Gemini"]
---

# Hiring Agent：InterviewStreet 开源的简历评分 Agent 管线，PDF→JSON→GitHub 增强→公平评分

> **阅读时间**：约 15 分钟
>
> **适用读者**：对 AI Agent 编排、LLM 抽结构化数据、招聘公平性、prompt 模板工程感兴趣的开发者
>
> **前置知识**：了解 Python 异步、Pydantic 基本用法、Ollama / Gemini 任意一种 LLM 后端的调用方式

## 这篇文章解决什么问题

招聘里"AI 筛简历"这件事，过去几年已经有一堆尝试——但大多数停在"用 ChatGPT 把简历贴进去问一句这个人行不行"。这套做法有两个根本问题：① **不可复现**——同样的简历问两次答案不一样；② **不可审计**——HR 拿不出"为什么这个人不合格"的证据链。

[Hiring Agent](https://github.com/interviewstreet/hiring-agent) 的解法是**把它当成一条严格的 ETL 管线**：PDF → Markdown → 分节抽 JSON → GitHub 信号补强 → 跑多维评分 → 输出带 evidence 的报告。整条管线每个环节都是显式的、可调试的、可复现的。

这是**原理拆解 / 架构分析**形态——本文重点不是"它能干什么"，而是"为什么这么拆"。

## 项目身份卡

- **仓库**：[interviewstreet/hiring-agent](https://github.com/interviewstreet/hiring-agent)
- **主语言**：Python 3.11+
- **License**：MIT
- **Stars / Forks**：1.9k / 569
- **首发**：2025-07-29
- **最近更新**：2026-06-22
- **体积**：106 KB（仓库很轻，纯 Python + Jinja + Pydantic）

## 核心判断：这是"管线化 Agent"，不是"对话式 Agent"

**对比维度**：

| 维度 | 对话式 Agent（典型） | Hiring Agent（管线式） |
|------|---------------------|----------------------|
| 入口 | 用户在 chat 里给指令 | CLI 命令行 + PDF 批量 |
| 中间状态 | LLM 自己维护 | 显式落盘到 JSON / CSV |
| 失败处理 | 整轮重跑 | 节点级重跑 + 失败定位 |
| 可审计性 | 难（黑盒） | 高（每步有产物） |
| 评分依据 | LLM 直觉 | 评分 prompt + fairness 约束 + evidence 引用 |

**核心方法论**：把"评估"这个看起来主观的任务，拆成"提取（extraction）→ 增强（enrichment）→ 评分（evaluation）"三段，每段独立 prompt、独立模型调用、独立数据 schema。

## 系统地图

```
                    ┌──────────────────┐
   resume.pdf ────▶ │  pymupdf_rag.py  │ ──▶ Markdown-like text
                    └──────────────────┘
                                       │
                                       ▼
                    ┌──────────────────┐
                    │     pdf.py       │ ──▶ sectioned JSON (per-section LLM call)
                    │  + prompts/      │     {education, work, projects, skills, ...}
                    └──────────────────┘
                                       │
                                       ▼
                    ┌──────────────────┐
                    │   github.py      │ ──▶ enriched JSON
                    │  (GitHub API +   │     + repos classified, top-7 selected
                    │   LLM select)    │
                    └──────────────────┘
                                       │
                                       ▼
                    ┌──────────────────┐
                    │  evaluator.py    │ ──▶ evaluation JSON
                    │  (strict-scored  │     {categories, scores, evidence,
                    │   + fairness)    │      bonus_points, deductions}
                    └──────────────────┘
                                       │
                                       ▼
                    ┌──────────────────┐
                    │    score.py      │ ──▶ final report (CSV in dev mode)
                    │   (orchestrator) │
                    └──────────────────┘
```

**5 个核心模块的角色**：

| 文件 | 角色 | 关键产物 |
|------|------|----------|
| `pymupdf_rag.py` | PDF → 文本 | Markdown 化文本（保留分节结构） |
| `pdf.py` | 文本 → 分节 JSON | 按 section 调 LLM，输出 JSON Resume 兼容 schema |
| `github.py` | 增强信号 | 拉 GitHub profile / repos，让 LLM 选 top 7 仓库 |
| `evaluator.py` | 严格评分 | 多维类别分 + 证据 + bonus / deduction |
| `score.py` | 编排器 | 串起以上所有步骤；dev 模式下写 CSV 便于调试 |

## 关键设计选择逐条拆解

### 设计 1：分节抽取（per-section LLM call）

为什么不一次性让 LLM 输出整个 JSON？项目方选择**按"教育 / 工作 / 项目 / 技能"分节独立调用**：

- **降低单次 prompt 复杂度**——一次只抽一类字段，错误率显著下降
- **支持失败定位**——某节抽坏了可以单独重跑
- **支持并行**——四节可以并发请求 LLM

### 设计 2：Jinja 模板驱动 prompt 工程

所有抽取和评分 prompt 都放在 `prompts/templates/` 下，**prompt 和 Python 代码解耦**：

```text
prompts/
├── extract_education.j2
├── extract_work.j2
├── extract_projects.j2
├── extract_skills.j2
├── github_repo_classify.j2
├── github_top7_select.j2
├── evaluate_*.j2     # 每个评分维度一个模板
└── fairness_constraints.j2
```

**好处**：调整评分口径不需要改 Python，重新跑就行；版本管理 prompt 和管理代码一样重要。

### 设计 3：Pydantic 强 schema + JSON Resume 标准化

`models.py` 定义了所有数据 schema——这部分直接决定整个管线的"可审计性"上限。中间产物必须是合法 JSON，否则评分步骤不会启动。

**Pydantic 的关键作用**：
- 字段类型校验（`start_date: date` 自动解析）
- 必填字段强约束（缺 education 直接报错）
- 自动生成 OpenAPI / JSON Schema 文档

抽取出的 JSON 目标是 **JSON Resume 标准**（[jsonresume.org](https://jsonresume.org/)）——这是个开放的简历数据 schema，意味着输出可以直接喂给其他工具。

### 设计 4：GitHub 信号增强

`github.py` 是这个项目最聪明的一步：

1. 抽出的 JSON 里有 `profiles[].username` 字段
2. 用 GitHub API 拉该用户的 profile + 全部 public repos
3. 让 LLM 对 repos 做分类（"这个仓库是个人玩具 / 公司项目 / 开源贡献 / 学习练习"）
4. 再让 LLM 选 **top 7** 与简历最相关的仓库

**这一步骤把"简历自述"和"客观代码证据"做了交叉验证**——这是绝大多数"AI 筛简历"工具没做的工作。

### 设计 5：Fairness 约束（项目方明确提到）

`evaluator.py` 跑的是"strict-scored evaluation with fairness constraints"。README 没有展开具体实现，但从命名可以推断：

- **同一份简历跑 N 次取分位数**——降低 LLM 随机性
- **评分 prompt 里显式约束"不要因为姓名 / 性别 / 毕业学校打分"**
- **每个 score 都必须引用 evidence**（"基于第 X 段工作经历 / GitHub 仓库 Y"）

这是这个项目**区别于 ChatGPT 随意打分**的核心护城河。

## 双 LLM 后端：Ollama 本地 / Gemini 云端

`.env` 里一个变量切换：

```bash
LLM_PROVIDER=ollama  # 或 gemini
DEFAULT_MODEL=gemma3:4b  # 或 gemini-2.5-pro
```

| 维度 | Ollama | Gemini |
|------|--------|--------|
| 隐私 | 完全本地，简历不出网 | 数据走 Google |
| 成本 | 0（吃自己 GPU） | 按 token 计费 |
| 模型选择 | 自由（gemma3 / qwen / llama 都行） | Gemini 系列 |
| 速度 | 取决于本机 | 稳定快 |
| 适用 | HR 公司内网 / 隐私要求高 | 临时试用 / 不想配本地 |

**推荐组合**：

- **Mac M2/M3 + 16GB 内存** → `gemma3:4b`（甜点级）
- **Mac M3 Pro/Max + 32GB+** → `gemma3:12b`（质量提升明显）
- **Linux + 24GB 显存** → `gemma3:12b` 或 `qwen2.5:14b`
- **隐私严格 + 算力不够** → `gemma3:1b`（凑合用）

## 数据流案例：单份简历跑完整管线

假设你有一份 `candidate.pdf`，跑完一次评分总共会发生几次 LLM 调用？

```
1. pymupdf_rag → 转 Markdown（无 LLM）

2. pdf.py 抽取（4 次 LLM 调用，并行）：
   - extract_education.j2 → education JSON
   - extract_work.j2 → work JSON
   - extract_projects.j2 → projects JSON
   - extract_skills.j2 → skills JSON

3. github.py 增强（2 次 LLM 调用，可选，因为依赖 GitHub username）：
   - github_repo_classify.j2 → repos 分类
   - github_top7_select.j2 → top 7 仓库

4. evaluator.py 评分（5-8 次 LLM 调用，每维度一次）：
   - evaluate_technical_depth.j2
   - evaluate_experience_relevance.j2
   - evaluate_project_impact.j2
   - evaluate_communication.j2
   - evaluate_career_trajectory.j2
   + 加权汇总 + fairness 校验

5. score.py 写最终报告（无 LLM）
```

**总数**：约 11-14 次 LLM 调用。Ollama 跑一份简历大概 1-3 分钟，Gemini 大概 30-60 秒。

## CLI 用法（基于 README 推断）

```bash
# 装依赖
git clone https://github.com/interviewstreet/hiring-agent
cd hiring-agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 配环境
cp .env.example .env
# 编辑 .env：选 LLM_PROVIDER / DEFAULT_MODEL / GEMINI_API_KEY / GITHUB_TOKEN

# 跑评估（dev 模式会写 CSV）
python score.py --resume candidate.pdf --dev

# 跑评估（生产模式只输出最终报告）
python score.py --resume candidate.pdf
```

## 适用边界

**适合**：

- 技术招聘的初筛（特别是有大量投递的岗位）
- 内部转岗评估（已有员工的历史项目评估）
- HR 想用 AI 但被"不可解释"卡住时
- 研究 prompt engineering / agent 编排的样本项目

**不适合**：

- 创意 / 设计 / 文科岗位（评分维度不匹配）
- 求职数量 < 50 的小公司（搭管线成本不划算）
- 完全不能接受 AI 介入招聘流程的合规场景
- 没有 GitHub 活跃度的候选人（评分维度权重会偏）

## 自测题

1. 这个项目为什么选择"分节抽取"而不是一次性让 LLM 输出整个 JSON？这种选择牺牲了什么换来了什么？
2. Pydantic 在这个项目里扮演什么角色？如果中间产物不是合法 JSON，评分步骤会怎样？
3. `github.py` 增强这一步的"top 7 仓库"选择，依赖 LLM 还是确定性规则？这种"软选择"的风险是什么？
4. 如果同一份简历用 `gemma3:4b` 跑 3 次，会得到 3 个相同的分数吗？为什么？项目如何应对？

## 进阶阅读

- JSON Resume 标准：[jsonresume.org](https://jsonresume.org/)
- Pydantic 文档：[docs.pydantic.dev](https://docs.pydantic.dev/)
- Ollama 模型库：[ollama.com/library](https://ollama.com/library)
- Prompt 模板化实践：[github.com/danielmiessler/fabric](https://github.com/danielmiessler/fabric)
- Hiring 公平性研究（学术）：[AAAI/ACM AIES 会议论文集](https://dl.acm.org/conference/aies)

## 常见问题

**Q：能不能评估非技术岗简历？**
A：prompt 模板和评分维度都按技术岗设计，硬用到销售 / 行政岗会失真。改 `prompts/templates/` 里的 j2 文件可以适配。

**Q：本地 Ollama 跑出来的评分和 Gemini 差异大吗？**
A：在大方向上一致，细节上 `gemma3:4b` 会比 `gemini-2.5-pro` 给出更"宽松"的分数。建议做交叉验证。

**Q：项目方怎么解决"AI 偏见"问题？**
A：见 `evaluator.py` 的 fairness constraints——具体实现需要读源码，README 没完全展开，但这是项目的关键差异化点。

**Q：能不能直接接企业 ATS（Applicant Tracking System）？**
A：项目本身没集成，但你可以在 `score.py` 后加一个上传到 Greenhouse / Lever 的 adapter，输出已经是结构化 JSON。
