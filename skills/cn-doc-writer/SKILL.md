---
name: cn-doc-writer
description: 中文技术文档工作流。适用于编写中文技术教程、README、API 文档，或把英文技术资料译成中文、优化现有技术文档、补充学习目标/练习/FAQ/进阶路径等场景。覆盖任务路由、读者建模、术语一致性、量化评估与 references 按需加载；关键词：中文技术文档、英译中、文档优化、学习元素、技术教程、README、API 文档。
version: 5.1.0
author: Sisyphus
tags: ["cn-doc", "technical", "translation", "learning"]
commands:
  - name: write-cn-doc
    description: 从零编写中文技术文档
  - name: translate-cn
    description: 英文技术资料译成中文并保留技术准确性
  - name: optimize-cn-doc
    description: 诊断并优化现有中文技术文档
  - name: enhance-learning
    description: 为现有文档补充目标、练习与进阶路径
---

## 中文技术文档工作流

核心目标：产出准确、可教、可发布的中文技术文档。优先级固定为：读者理解 > 事实准确 > 教学设计 > 文风润色。

## 1. 先做路由

收到任务后，先完成 3 个判断，再开始写。

### Step 1: 识别命令

| 输入信号 | 命令 |
| ------ | ------ |
| 从大纲、需求、空白开始写中文技术文档 | `write-cn-doc` |
| 提供英文技术文档，要求翻译为中文 | `translate-cn` |
| 提供现有中文技术文档，要求改进或润色 | `optimize-cn-doc` |
| 提供现有文档，要求补学习目标、练习、自测、进阶路径 | `enhance-learning` |

### Step 2: 判断交付深度

| 模式 | 触发条件 | 执行策略 |
| ------ | ------ | ------ |
| 快速 | 单页文档、≤3 个 H2、结构已清楚 | 直接选模板并产出 |
| 标准 | 多章节、单一路径、读者层级明确 | 选路径和级别后产出 |
| 完整 | 文档体系、多路径、跨文档关联 | 先做结构设计，再写正文 |

默认使用标准模式；只有同时满足快速条件时才降级到快速模式。

### Step 3: 判断是否需要追问

| 情况 | 动作 |
| ------ | ------ |
| `write-cn-doc` 缺主题、读者、目的中的任一关键项 | 先追问最少问题 |
| 用户明确要求“先给我一版草稿” | 声明假设并继续，不阻塞 |
| `translate-cn`、`optimize-cn-doc`、`enhance-learning` 已提供完整原文 | 不重复追问基础信息 |
| 缺少事实来源、版本、技术栈且会影响准确性 | 先追问或显式标注假设 |

不要为了礼貌重复确认已经明确的信息。只有关键输入缺失时才追问。

## 2. 按需加载

只加载当前任务需要的 reference，避免把实现细节和低频知识塞进主上下文。

| 命令 | 必须加载 | 按需加载 | 禁止预加载 |
| ------ | ------ | ------ | ------ |
| `write-cn-doc` | `references/commands.md` | 快速/标准/完整模板用 `references/templates.md`；需要学习路径时用 `references/learning-paths.md`；做文档体系设计时用 `references/tools.md`；输出前评分时用 `references/quality.md` | `scripts/`、`ci/`、`CHANGELOG.md` |
| `translate-cn` | `references/commands.md` + `references/terminology.json` | 长文档、复杂 Markdown、分片翻译用 `references/edge-cases.md`；需要语气校准时用 `references/examples.md`；做发布级评审时用 `references/quality.md` | `scripts/`、`ci/`、`CHANGELOG.md` |
| `optimize-cn-doc` | `references/commands.md` + `references/quality.md` | 术语密集时用 `references/terminology.json`；需要示例风格时用 `references/examples.md`；超长文档或跨文档优化时用 `references/edge-cases.md` | `scripts/`、`ci/`、`CHANGELOG.md` |
| `enhance-learning` | `references/commands.md` + `references/learning-paths.md` | 需要教学框架或知识组织时用 `references/knowledge.md`；需要示例风格时用 `references/examples.md`；输出评分时用 `references/quality.md` | `scripts/`、`ci/`、`CHANGELOG.md` |

只有当用户明确要求本地工具、自动化校验、脚本维护或发布流程时，才读取 `scripts/`、`ci/` 或 `CHANGELOG.md`。

## 3. 执行骨架

### Step 1: 定义任务

输入：用户请求或现有文档  
输出：命令、模式、关键约束、缺失信息列表

### Step 2: 制定方案

输入：Step 1 的任务定义  
输出：以下四种之一

- `write-cn-doc`：章节骨架 + 目标读者 + 学习路径/级别
- `translate-cn`：保留区清单 + 术语计划 + 翻译范围
- `optimize-cn-doc`：基线问题 + 优先修复项
- `enhance-learning`：可增强位置 + 学习元素方案

### Step 3: 执行命令

详细流程读取 `references/commands.md`。执行时保持下面 4 条不变：

- 代码块、命令、URL、文件路径、版本号默认保持原样
- 所有核心概念优先回答“为什么需要它”
- 术语首次出现时，优先使用中文加原文括注；把握不足时保留原文并补中文释义
- 信息不足时收缩范围，不用空章节凑结构

### Step 4: 交付前回路

先做自检，再决定是否交付：

1. 结构是否服务当前读者，而不是服务作者表达欲
2. 事实、术语、代码、链接是否可以追溯或验证
3. 若评分或关键检查不达标，先修改，再输出

## 4. 微型示例

### `write-cn-doc`

输入：帮我写一篇 Kubernetes 配置入门，读者是有 Docker 基础的后端工程师。  
执行：`write-cn-doc` + 标准模式 → 加载 `references/commands.md`、`references/templates.md` → 必要时补学习路径 → 输出完整教程。

### `translate-cn`

输入：把这份英文 API 文档翻成中文，保留 curl 示例。  
执行：`translate-cn` → 加载 `references/commands.md`、`references/terminology.json` → 保留代码与命令 → 输出译文和术语报告。

### 反例

不要输出“这很简单，只需运行一行命令”或 `...省略...` 这类贬低难度、破坏可执行性的内容。

## 5. 输出契约

| 命令 | 最低交付要求 |
| ------ | ------ |
| `write-cn-doc` | 完整 Markdown 文档；标准/完整模式必须包含学习目标 |
| `translate-cn` | 中文译文 + 术语使用报告；代码块与命令原文不变 |
| `optimize-cn-doc` | 优化后文档 + 优化前后对比；至少展示 3 个评分维度变化 |
| `enhance-learning` | 增强后文档 + 增强清单；至少补入 3 类学习元素 |

如果用户明确只要大纲、摘要或局部改写，可以缩小交付范围，但要显式说明没有提供的部分。

## 6. 输出前自检

任一项失败，都先回到正文修正，再输出。

| # | 检查项 | 失败动作 |
| ------ | ------ | ------ |
| 1 | 读者视角检查：是否存在未解释的术语、跳步或默认前置知识 | 补解释、补前提、减跳跃 |
| 2 | “为什么”检查：核心概念是否解释了存在原因、适用边界和代价 | 补“为什么”与边界 |
| 3 | 术语一致性：同一概念是否统一译法；必要时查 `references/terminology.json` | 统一译名并修正首次出现 |
| 4 | 技术完整性：代码示例、命令、路径、链接是否完整可用 | 修复后再交付 |
| 5 | 格式合规：标题层级、代码块语言、中文标点、中英文空格是否正确 | 统一格式 |
| 6 | 命令交付物完整：术语报告、评分表、增强清单等是否齐全 | 补齐缺项 |

红线：禁止把未通过自检的文档直接交付给用户。

## 7. 格式约束

### 通用规则

| # | 规则 |
| ------ | ------ |
| 1 | Markdown 顶层标题使用 `#`；若补写正文片段，从 `##` 开始继续现有层级 |
| 2 | 代码块必须指定语言 |
| 3 | 中文与英文、中文与数字、正文与行内代码之间保持空格 |
| 4 | 中文语境默认使用全角标点；代码、命令、配置键和值保持原始语法 |
| 5 | 禁止输出 `...省略...`、伪代码式占位符或不可运行的“示意代码” |

### 命令专属规则

| 命令 | 额外约束 |
| ------ | ------ |
| `write-cn-doc` | 标准/完整模式必须有学习目标；示例要完整，不要只给片段 |
| `translate-cn` | 正文按中文表达重组，不逐句硬译；首次术语格式优先为 中文（English）；结构允许小幅重排 |
| `optimize-cn-doc` | 必须先做基线评估，再给优化后结果 |
| `enhance-learning` | 从 学习目标 / 练习 / 自测 / 进阶路径 中至少覆盖 3 类 |

## 8. 必须与禁止

### 必须

- 默认用中文输出
- 只在关键输入缺失时追问；其余场景声明假设后继续
- 保留代码块、命令、URL、文件路径、版本号，除非用户明确要求改写
- 信息不足时明确边界，不补写无法验证的事实
- 超大文档或多文件文档按 H2 主题分片处理，并维护一致术语

### 禁止

- 禁止使用“简单地”“只需”“显然”等贬低难度的表达
- 禁止逐句直译、直拷英文句法或机械翻译术语
- 禁止修改代码、命令、URL、路径、配置键名以迎合中文语感
- 禁止伪造示例、版本兼容性、性能结论、错误原因或最佳实践
- 禁止预加载全部 reference，或在普通写作任务里读取 `scripts/`、`ci/`、`CHANGELOG.md`

## 9. 异常与恢复

| 情况 | 处理 |
| ------ | ------ |
| 未指定读者或技术栈 | 先追问；若用户要求先出稿，则声明假设并继续 |
| 文档超过 5000 行或明显超上下文 | 按 H2 分片，先建术语清单，再逐片处理；必要时读取 `references/edge-cases.md` |
| 术语表中没有对应词 | 保留原文；若中文释义有把握，再补简短括注 |
| 原文存在自相矛盾或版本冲突 | 以来源更强的一侧为准；无法判定时显式标注 unresolved |
| 非技术文档，或属于法律/医学/学术论文 | 告知本 skill 不适用，不强行输出 |
| 翻译后行数偏差远超预期 | 先排查是否因代码块、表格或分片导致；若不是，再压缩冗余或补遗漏 |
