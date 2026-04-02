---
title: "tech 现有文章子目录迁移规划表"
date: 2026-04-01T13:20:00+08:00
draft: false
tags: ["Hugo", "迁移规划", "信息架构", "内容治理", "技术笔记"]
categories: ["系统基建"]
---

> **🎯 学习目标**
>
> 读完本文，你将了解：
>
> 1. 当前 `content/posts/tech/` 旧文适合如何按主题迁移。
> 2. 哪些子目录应该优先建设，哪些应暂缓推进。
> 3. 哪些文章适合直接迁移，哪些更适合继续平铺并依赖标签聚合。
> 4. 后续批量迁移时应遵循什么顺序与风险控制策略。

本文档是 `tech` 目录第一阶段治理后的第二阶段规划产物，用于回答一个具体问题：**现有文章如果要逐步归入稳定子目录，应该先迁哪些，暂缓哪些，为什么？**

---

## 1. 规划原则

本规划采用以下 4 条判断标准：

1. **按读者心智归类**：优先看文章的第一主题，而不是它顺带用了什么技术。
2. **按长期主题归类**：只有未来仍会持续产出的主题，才值得形成稳定子目录。
3. **按风险分批推进**：先迁主题最清晰的内容，再处理交叉型文章。
4. **按旧链接兼容执行**：正式迁移旧文时，需要补 `aliases` 保留旧路径。

推荐的稳定子域当前调整为 5 个：

- `ai-agent`
- `llm`
- `tools`
- `quant`

---

## 2. 总体判断

从当前内容密度和主题稳定性来看，这 4 个子域不适合平均发力，而应该分层推进。

| 子域 | 当前成熟度 | 是否优先建设 | 说明 |
| --- | --- | --- | --- |
| `ai-agent` | 很高 | 是 | 当前内容密度最高，且所有 Claude 相关文章统一归入这里 |
| `llm` | 很高 | 是 | 模型训练、提示工程、评测类文章较集中 |
| `quant` | 高 | 是 | 金融研究、量化交易与平台类内容已形成稳定簇 |
| `tools` | 中高 | 第二批 | 工具链、CLI、OCR、BI 与工作流类内容较稳定 |

一句话结论：**优先建设 `ai-agent / llm / quant`，再推进 `tools`。**

---

## 3. 第一批迁移建议

第一批只迁移“主题明确、长期价值高、后续仍会持续积累同类内容”的文章。

### 3.1 `ai-agent`

| 当前文件 | 建议目标目录 | 迁移建议 | 原因 |
| --- | --- | --- | --- |
| `agentscope-ai-agent-framework.md` | `tech/ai-agent/` | 建议优先迁移 | 典型 Agent 框架分析文 |
| `agency-agents-multi-agent-framework-guide.md` | `tech/ai-agent/` | 建议优先迁移 | 多 Agent 框架主题明确 |
| `anthropic-claude-api-agent.md` | `tech/ai-agent/` | 建议优先迁移 | 核心问题是 Agent 架构 |
| `anthropic-claude-api-mcp.md` | `tech/ai-agent/` | 建议优先迁移 | 用户已明确将 Claude 相关文章统一归入 `ai-agent` |
| `trae-agent-llm-agent-guide.md` | `tech/ai-agent/` | 建议优先迁移 | 用户已明确归入 `ai-agent` |
| `2026-let-s-vision-ai-agent-engineering.md` | `tech/ai-agent/` | 建议迁移 | 用户已明确归入 `ai-agent` |
| `hermes-agent-self-improving-ai-framework.md` | `tech/ai-agent/` | 建议优先迁移 | Agent 自演化主题稳定 |
| `openviking-context-database-ai-agents.md` | `tech/ai-agent/` | 建议优先迁移 | 上下文数据库服务于 Agent 系统 |

### 3.2 `llm`

| 当前文件 | 建议目标目录 | 迁移建议 | 原因 |
| --- | --- | --- | --- |
| `minimind-llm-training-from-scratch.md` | `tech/llm/` | 建议优先迁移 | 模型训练主题明确 |
| `promptfoo-llm-evaluation-testing-guide.md` | `tech/llm/` | 建议优先迁移 | 主主题是 LLM 评测 |
| `quantization-llm-model-compression-guide.md` | `tech/llm/` | 建议优先迁移 | 模型压缩属于 LLM 核心议题 |
| `ai-advanced-technology-learning-notes-2026-03.md` | 暂不迁移 | 暂缓 | 更像综合综述，跨域过强 |

### 3.3 `quant`

| 当前文件 | 建议目标目录 | 迁移建议 | 原因 |
| --- | --- | --- | --- |
| `qlib-ai-quantitative-investment-platform-guide.md` | `tech/quant/` | 建议优先迁移 | 量化投资平台主题明确 |
| `daily-stock-analysis-ai-stock-system.md` | `tech/quant/` | 建议优先迁移 | 虽涉及 AI，但主问题是股票分析 |
| `tradingagents-multi-agent-framework.md` | `tech/quant/` | 建议优先迁移 | Agent 服务于交易研究场景 |
| `tradingagents-cn-multi-agent-stock-platform.md` | `tech/quant/` | 建议优先迁移 | 面向股票平台的量化主题稳定 |
| `valuecell-multi-agent-finance-platform-guide.md` | `tech/quant/` | 建议优先迁移 | 金融平台导向明显 |
| `openbb-open-data-platform-guide.md` | `tech/quant/` | 建议迁移 | 用户已明确将其归入 `quant` |

---

## 4. 第二批迁移建议

第二批适合迁移那些“主题较明确，但仍带有一定交叉属性”的文章。

### 4.1 `tools`

| 当前文件 | 建议目标目录 | 迁移建议 | 原因 |
| --- | --- | --- | --- |
| `ripgrep-recursive-search-guide.md` | `tech/tools/` | 建议迁移 | 典型开发工具文章 |
| `worktrunk-git-worktree-manager-guide.md` | `tech/tools/` | 建议迁移 | Git 工作流工具主题稳定 |
| `lark-cli-feishu-command-line-tool-guide.md` | `tech/tools/` | 建议迁移 | CLI 工具主题明确 |
| `neovim-vim-fork-guide.md` | `tech/tools/` | 建议迁移 | 编辑器工具类文章 |
| `apache-superset-bi-dashboard-guide.md` | `tech/tools/` | 建议迁移 | 用户已明确归入 `tools` |
| `paddleocr-pdf-image-to-structured-data.md` | `tech/tools/` | 建议迁移 | 用户已明确归入 `tools` |
| `paddleocr-ocr-document-ai-engine-guide.md` | `tech/tools/` | 建议迁移 | 用户已明确归入 `tools` |
| `chandra-ocr-complex-document-recognition.md` | `tech/tools/` | 建议迁移 | 用户已明确归入 `tools` |

### 4.2 Claude 归类规则

与 `Claude` 直接相关的文章，统一归入 `tech/ai-agent/`，不再放入 `tools` 或其他子目录。

| 当前文件 | 建议目标目录 | 迁移建议 | 原因 |
| --- | --- | --- | --- |
| `claude-code-skills-agent-plugins-guide.md` | `tech/ai-agent/` | 建议迁移 | 用户已明确：凡与 Claude 相关的文章统一归类为 `ai-agent` |

---

## 5. 暂缓迁移项

以下文章当前不建议强制放入某个子目录，继续保留在 `tech/` 平铺层并依赖标签聚合更稳妥。

| 当前文件 | 暂缓原因 | 后续建议 |
| --- | --- | --- |
| `ai-advanced-technology-learning-notes-2026-03.md` | 同时覆盖 LLM、Agent、RAG、多模态 | 继续平铺，依赖标签 |
| `papers-we-love-cs-papers-community.md` | 泛计算机科学资源，不属于六类稳定子域 | 保持平铺 |

这类文章的处理原则是：**不为了目录完整而牺牲语义准确性。**

---

## 6. 关于移除 `python` 子域

根据最新归类决策，`python` 不再作为 `tech` 的稳定子目录存在。

原因主要有 3 个：

1. 许多文章虽然使用了 Python，但第一主题其实是 Agent、量化、OCR 或工具。
2. 把这些文章强行归到 `python`，会弱化它们真正的主题域。
3. 当前 `Python` 更适合作为高质量标签，而不是目录层级。

因此更合理的策略是：

- 继续把 `Python` 作为高质量标签使用
- 不再为旧文迁移单独保留 `python` 目录

---

## 7. 迁移执行顺序

建议按下面顺序推进：

1. 建立 `ai-agent / llm / quant` 子目录
2. 从每个目录各选 3 到 5 篇高价值旧文先做试迁移
3. 为迁移文章补 `aliases`
4. 本地构建验证链接、taxonomy 页与 section 页
5. 再推进 `tools`

这样做的优点是：**先拿主题最清晰的内容验证迁移流程，而不是一次性大搬家。**

---

## 8. 可执行的第一批试迁移清单

如果下一步要真正开始迁移，建议先从下面这 9 篇开始：

| 目标目录 | 推荐试迁移文件 |
| --- | --- |
| `tech/ai-agent/` | `agentscope-ai-agent-framework.md` |
| `tech/ai-agent/` | `agency-agents-multi-agent-framework-guide.md` |
| `tech/ai-agent/` | `hermes-agent-self-improving-ai-framework.md` |
| `tech/llm/` | `minimind-llm-training-from-scratch.md` |
| `tech/llm/` | `promptfoo-llm-evaluation-testing-guide.md` |
| `tech/llm/` | `quantization-llm-model-compression-guide.md` |
| `tech/quant/` | `qlib-ai-quantitative-investment-platform-guide.md` |
| `tech/quant/` | `tradingagents-multi-agent-framework.md` |
| `tech/quant/` | `valuecell-multi-agent-finance-platform-guide.md` |

这 9 篇的共同特点是：主题清晰、目录归属稳定、迁移收益高、争议相对小。

---

## 9. 一句话结论

`tech` 旧文迁移不应该追求“把所有文章平均塞进多个目录”，而应该优先把最清晰的主题簇沉淀下来。当前最合理的顺序是：**先做 `ai-agent / llm / quant`，再补 `tools`。**
