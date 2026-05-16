---
title: "Anthropic Skills 仓库进阶实战：18个技能覆盖研发全链路"
date: "2026-05-16T15:10:00+08:00"
slug: "anthropics-skills-18-skills-full-stack-guide"
description: "Anthropic 官方 Skills 仓库已积累超过 13.5 万颗 Stars，成为 AI Agent 技能生态的标杆资源库。本文聚焦 18 个官方技能的进阶用法，重点解析 MCP Builder 的四阶段开发流程、frontend-design 的反 AI 美学设计原则，以及 PDF/DOCX/PPTX/XLSX 等文档技能的内部实现架构。"
draft: false
categories: ["技术笔记"]
tags: ["Claude", "Agent Skills", "Anthropic", "MCP", "工作流自动化"]
---

# Anthropic Skills 仓库进阶实战：18个技能覆盖研发全链路

> 仓库地址：[anthropics/skills](https://github.com/anthropics/skills)
>
> Stars：135,404 | Forks：15,958 | 语言：Python
>
> 定位：从「会用」到「会改、会写」的 Agent Skills 进阶实战指南

---

## 前言

两周前（2026-05-02），我们曾深入解析过 [Anthropics Skills 仓库的整体架构](/thoughts/anthropics-skills-repository-guide)，涵盖了 Skills 的核心原理、三层加载机制和在 Claude Code / Claude.ai / API 三种场景下的安装方式。

两周过去，该仓库 Stars 从 **126,950** 增长到 **135,404**（周均增速约 6,000），热度不减反增。Anthropic 也在此期间对多个技能做了更新，尤其是 **mcp-builder** 和 **skill-creator** 两个工程导向技能的内容大幅扩充。与此同时，仓库新增了 `frontend-design` 等技能，并对 PDF/DOCX 等文档技能的实现细节做了补充。

本文面向已有 Agent Skills 基础认识的读者，聚焦以下三个核心主题：

1. **MCP Builder 技能**：Anthropic 官方出品的 MCP 服务器开发指南，四阶段完整流程
2. **Frontend Design 技能**：如何用 Skill 约束模型生成「反 AI 味」的独特设计
3. **文档技能（PDF/DOCX/PPTX/XLSX）**：支撑 Claude 文档能力的幕后实现架构
4. **Skill Creator 迭代工作流**：从编写到评估到优化的完整闭环

---

## 一、MCP Builder：MCP 服务器开发的系统性方法论

MCP（Model Context Protocol）是 Anthropic 主推的 AI 与外部工具交互协议。`mcp-builder` 技能将 MCP 服务器开发拆解为四个阶段：**深度调研 → 规划 → 实现 → 测试**，每一步都有明确的交付物和检查点。

### 1.1 Phase 1：深度调研与规划

#### 1.1.1 理解 MCP 设计哲学

MCP 服务器的质量取决于两个维度的平衡：

- **API 覆盖度**：提供完整的 API 端点覆盖，给 Agent 最大组合自由度
- **工作流工具**：针对高频场景封装高层工具，降低 Agent 操作复杂度

两者并不矛盾——Agent 能力强的客户端（如 Claude Code）可以直接组合基础工具完成复杂任务，而能力较弱的客户端则依赖封装好的工作流工具。

#### 1.1.2 工具命名规范

工具命名采用 `前缀_动作_资源` 的三段式结构，例如 `github_create_issue`、`github_list_repos`。清晰的命名帮助 Agent 快速定位所需工具，而非在大量同名工具中迷失。

错误消息设计同样关键：每条错误应包含**具体建议**和**下一步操作**，而不是仅仅返回"失败"。

#### 1.1.3 框架选择

技能推荐使用 **TypeScript**（基于 `@modelcontextprotocol/typescript-sdk`）作为首选语言，原因有三：

- AI 模型生成 TypeScript 代码质量高（静态类型 + 广泛使用）
- 远程服务器推荐 **Streamable HTTP**（无状态，易于扩展）
- 本地服务器推荐 **stdio**（简单直接）

Python 开发者可使用官方 `python-sdk`，行为模式一致。

#### 1.1.4 调研阶段交付物

| 交付物 | 说明 |
|--------|------|
| API 端点清单 | 优先级排序，标注核心与辅助端点 |
| 认证方案 | API Key、OAuth 或其他认证方式 |
| 数据模型 | 请求/响应结构，关键字段类型 |
| 错误处理策略 | 各端点可能的错误码与重试逻辑 |

### 1.2 Phase 2：项目结构规划

```
my-mcp-server/
├── src/
│   ├── index.ts          # 入口文件，导出 server 实例
│   ├── tools/            # 各端点对应的工具实现
│   │   ├── repo-tools.ts
│   │   └── issue-tools.ts
│   ├── types/            # 共享类型定义
│   └── utils/            # 通用工具函数
├── package.json
└── tsconfig.json
```

核心原则：**每个文件职责单一，工具函数按资源类型分目录组织**。

### 1.3 Phase 3：实现要点

#### 工具描述（description）的艺术

工具的 `description` 字段是 Agent 决策的关键依据。好的描述应该：

- 说明工具的**用途**而非实现细节
- 列举典型的**输入格式**和**输出示例**
- 指明**适用场景**和**禁忌场景**

#### 分页与过滤支持

设计工具时，应支持 `limit`、`page`、`filter` 等通用参数，让 Agent 可以灵活控制返回数据量。例如：

```typescript
{
  name: "list_repositories",
  description: "List repositories for the authenticated user. " +
    "Supports pagination with limit (max 100) and filter by visibility.",
  inputSchema: {
    type: "object",
    properties: {
      limit: { type: "integer", default: 30, maximum: 100 },
      page: { type: "integer", default: 1 },
      visibility: { type: "string", enum: ["all", "public", "private"] }
    }
  }
}
```

#### 错误规范化

所有工具应返回统一格式的错误：

```json
{
  "error": true,
  "code": "RESOURCE_NOT_FOUND",
  "message": "Repository not found: owner/repo",
  "suggestion": "Check the repository name and ensure you have access"
}
```

### 1.4 Phase 4：测试验证

使用 Playwright 进行端到端测试：

```bash
# 安装 MCP 服务器到 Claude Code
claude mcp add my-server ./path/to/server

# 在 Claude Code 中执行集成测试
/claude-code-test "list the first 5 repositories"
```

---

## 二、Frontend Design：对抗 AI 美学滑失的设计技能

`frontend-design` 是仓库中最具特色的技能之一，它的核心目标是**解决 AI 生成界面同质化问题**。

### 2.1 问题诊断：什么是「AI 味」界面？

Anthropic 的工程师在技能文档中指出，当前 AI 生成的 Web 界面普遍存在以下特征：

- 背景渐变 + 大量留白
- 蓝色/紫色为主色调
- 使用 Inter / Arial 等无特征字体
- 卡片式布局 + 圆角
- 「Get Started」「Learn More」式按钮文案

这些特征本身不是问题，问题是**它们出现在每一个 AI 生成的项目中**，导致界面失去品牌辨识度。

### 2.2 设计约束的三个层次

Frontend Design 技能通过三步约束来解决这个问题：

#### 第一步：明确设计方向

在写代码之前，Agent 必须先确认：

- **目的（Purpose）**：这个界面解决什么问题？谁来用？
- **基调（Tone）**：选择一种极端风格——极简主义、复古未来、杂志风、工业风、奢华精致、卡通玩具……风格没有对错，但必须**极端且一致**
- **约束（Constraints）**：技术限制（框架、性能、无障碍）是什么？
- **差异化（Differentiation）**：用户会记住这个界面的什么？

#### 第二步：字体选择

技能要求 Agent **避免使用 Arial、Inter、Roboto** 等常见字体，改用具有独特气质的字体：

| 类型 | 推荐字体 | 适用场景 |
|------|----------|----------|
| 展示字体 | Syne、Clash Display、Fustig | 大标题，强调个性 |
| 正文字体 | Instrument Sans、Outfit、PP Neue Montreal | 界面正文，高可读性 |
| 等宽字体 | JetBrains Mono、Geist Mono | 代码、数据展示 |

关键原则：**展示字体 + 正文字体的配对比正文内容本身更重要**。

#### 第三步：配色克制

避免使用 AI 偏爱的蓝紫渐变。推荐策略：

- 主色：选择一个**有情感倾向**的颜色（如 `#D97757` 的温暖橙，而非中性的蓝）
- 背景：考虑非白色（如 `#faf9f5` 的米白）或非纯黑（如 `#141413` 的深灰）
- 强调色：通过 2-3 个辅色构建色彩系统，而非随机添加

### 2.3 代码质量标准

技能对生成的代码有明确要求：

- **可用性优先**：生成的界面必须是可以正常运行的完整代码，而非设计稿
- **细节打磨**：光标样式、过渡动画、`hover` 状态、`focus` 可见性等微交互必须到位
- **响应式布局**：至少覆盖 375px（移动端）和 1440px（桌面端）
- **无障碍基础**：`aria-label`、`keyboard navigation`、色彩对比度合规

---

## 三、文档技能：支撑 Claude 文件能力的幕后架构

Claude 的「创建文件」能力（Word、PDF、PPT、Excel）背后，是一组 Anthropic **Source-Available**（而非开源）的文档技能。它们位于仓库的 `skills/docx`、`skills/pdf`、`skills/pptx`、`skills/xlsx` 目录下。

### 3.1 DOCX 技能：.docx 是 ZIP + XML

DOCX 技能的核心知识是：**.docx 文件本质上是一个 ZIP 压缩包，内部是结构化的 XML 文件**。

```
document.docx
├── word/document.xml       # 正文内容
├── word/styles.xml         # 样式定义
├── word/numbering.xml      # 编号列表
├── word/header.xml         # 页眉
├── word/footer.xml         # 页脚
├── word/settings.xml       # 文档设置
├── [Content_Types].xml     # 文件类型声明
└── _rels/.rels             # 内部关系
```

技能的指令覆盖了完整的操作矩阵：

| 操作 | 工具/方法 |
|------|-----------|
| 读取内容 | `pandoc --track-changes=all` 提取文本和变更记录 |
| 读取原始 XML | `python scripts/office/unpack.py` 解包后直接读 XML |
| 创建新文档 | `docx-js`（npm 包）生成结构化文档 |
| 编辑现有文档 | 解包 → 编辑 XML → 重新打包 |
| 转换为 PDF | `python scripts/office/soffice.py --headless --convert-to pdf` |
| 接受修订 | `python scripts/accept_changes.py` 接受所有追踪修改 |

### 3.2 PDF 技能：表单字段提取

PDF 技能的亮点是对**表单字段**的处理能力：

```bash
# 提取 PDF 中的表单字段
python scripts/pdf/extract_form_fields.py document.pdf

# 输出示例
{
  "fields": [
    {"name": "full_name", "type": "text", "page": 1, "rect": [72, 650, 288, 678]},
    {"name": "email", "type": "text", "page": 1, "rect": [72, 600, 288, 628]},
    {"name": "agree_terms", "type": "checkbox", "page": 1, "rect": [72, 550, 96, 574]}
  ]
}
```

这使得 Agent 可以识别 PDF 表单的结构并进行批量填充，而非仅仅做文字提取。

### 3.3 PPTX 技能：基于 python-pptx 的结构化构建

PPTX 技能使用 `python-pptx` 库构建幻灯片，核心模式是：

```python
from pptx import Presentation
from pptx.util import Inches, Pt

prs = Presentation()
slide = prs.slides.add_slide(prs.slide_layouts[6])  # 空白布局

# 添加标题
title = slide.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(9), Inches(1))
title.text = "Title Here"

# 添加内容
content = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(9), Inches(5))
tf = content.text_frame
p = tf.paragraphs[0]
p.text = "Content here"
p.font.size = Pt(18)
```

技能的指令中包含**模板主题系统**，支持快速应用品牌色和字体。

### 3.4 XLSX 技能：结构化数据处理

XLSX 技能的核心依赖是 `openpyxl` 库，覆盖以下场景：

- **样式应用**：单元格颜色、边框、合并、列宽、行高
- **公式处理**：插入和验证 Excel 公式（VLOOKUP、SUMIF、INDEX/MATCH 等）
- **图表生成**：基于数据范围创建柱状图、折线图、饼图
- **批量操作**：多 sheet 管理、数据透视表

### 3.5 许可证说明

这四个文档技能采用 **Proprietary 许可证**（见各 SKILL.md 顶部的 `license` 字段），Anthropic 将其描述为「Source-Available」——代码已公开，但使用受限。这与仓库中其他技能的 Apache 2.0 许可证不同，需要注意区分。

---

## 四、Skill Creator：从编写到评估的完整迭代闭环

`skill-creator` 技能本身就是用 Agent Skills 工作流构建技能的示范。它将技能开发划分为四个阶段，循环迭代直到满意。

### 4.1 四阶段迭代流程

```
意图捕获 → SKILL.md 编写 → 测试用例运行 → 评估分析 → 重写优化 → 重复
```

#### Stage 1：捕获意图（Capture Intent）

从对话历史中提取：

- 技能要完成什么任务？
- 什么时候触发？（用户说什么时激活）
- 期望的输出格式是什么？
- 是否需要测试用例？

#### Stage 2：编写 SKILL.md

基于意图，编写符合规范的 SKILL.md，包含：

- **`name`**：小写 + 连字符，唯一标识
- **`description`**：触发条件 + 功能描述。注意：描述要略微「激进」，因为 Claude 有「技能触发不足」的问题
- **`compatibility`**：所需工具和依赖（可选）
- **正文**：指令、示例、指南

**description 的优化技巧**：用 `skill-creator` 技能中的 `description-optimizer` 脚本分析触发准确率，持续优化描述文本。

#### Stage 3：测试与评估

创建测试 prompt（eval queries），确保覆盖：

- 技能应该触发的场景（正例）
- 技能不应触发的场景（负例）
- 边界条件和极端输入

使用 `eval-viewer/generate_review.py` 脚本生成评估报告。

#### Stage 4：迭代优化

根据评估结果重写 SKILL.md，重复流程直到：

- 触发准确率达标
- 输出质量稳定
- 测试用例覆盖主要场景

### 4.2 渐进式披露实践

技能描述（description）的大小预算遵循 LLM 上下文的经济学原则：

| 层级 | 内容 | 大小 |
|------|------|------|
| L1 | `name` + `description` | ~100 词，始终加载 |
| L2 | 完整 SKILL.md 正文 | ~500 行，触发时加载 |
| L3 | 脚本/模板/参考文件 | 无限制，按需加载 |

技能创建者需要在**信息充分性**和**上下文成本**之间找到平衡。`description` 应极度精炼——只描述「何时触发、做什么」，不解释「如何实现」。

---

## 五、18个技能速览与分类索引

以下是仓库 `skills/` 目录下 18 个技能的快速索引，按应用场景分类：

### 创意与设计类

| 技能 | 描述 | 许可证 |
|------|------|--------|
| `algorithmic-art` | 使用 p5.js 创建程序化艺术，输出 .md + .html + .js | Apache 2.0 |
| `canvas-design` | 设计哲学 → 视觉表达的完整流程，输出 PDF/PNG | Apache 2.0 |
| `slack-gif-creator` | Slack 优化的 GIF 创建工具包（128×128 / 480×480） | Apache 2.0 |
| `theme-factory` | 10 个预设主题（配色 + 字体），支持自定义生成 | Apache 2.0 |

### 研发与工程类

| 技能 | 描述 | 许可证 |
|------|------|--------|
| `claude-api` | Claude API / Anthropic SDK 开发指南，含多语言支持 | Apache 2.0 |
| `frontend-design` | 避免 AI 味的独特界面设计系统 | Apache 2.0 |
| `mcp-builder` | MCP 服务器四阶段开发方法论 | Apache 2.0 |
| `skill-creator` | 从意图捕获到评估优化的技能构建框架 | Apache 2.0 |
| `webapp-testing` | Playwright + Python 的 Web 应用测试工具包 | Apache 2.0 |

### 企业与沟通类

| 技能 | 描述 | 许可证 |
|------|------|--------|
| `brand-guidelines` | Anthropic 官方品牌配色与字体应用 | Proprietary |
| `internal-comms` | 内部沟通文档模板（3P 更新、公司通讯、事件报告等） | Apache 2.0 |

### 文档类（Source-Available）

| 技能 | 描述 | 许可证 |
|------|------|--------|
| `doc-coauthoring` | 文档协作工作流：上下文收集 → 迭代精炼 → 读者测试 | Apache 2.0 |
| `docx` | Word 文档创建、编辑与分析 | Proprietary |
| `pdf` | PDF 读取、表单字段提取、创建与转换 | Proprietary |
| `pptx` | PowerPoint 幻灯片生成与编辑 | Proprietary |
| `xlsx` | Excel 电子表格处理、公式与图表 | Proprietary |

---

## 六、安装与使用

### 在 Claude Code 中安装

```bash
# 方式一：注册为 Plugin 市场
/plugin marketplace add anthropics/skills

# 安装示例技能集
/plugin install document-skills@anthropic-agent-skills
/plugin install example-skills@anthropic-agent-skills

# 方式二：直接安装
/plugin install document-skills@anthropic-agent-skills
/plugin install example-skills@anthropic-agent-skills
```

安装后，直接在对话中提及技能即可触发，例如：

> 「Use the PDF skill to extract form fields from `contract.pdf`」

### 在 Claude.ai 中使用

付费用户可直接使用仓库中所有示例技能。上传自定义技能参考官方文档中的[使用指南](https://support.claude.com/en/articles/12512180-using-skills-in-claude#h_a4222fa77b)。

### 通过 API 上传自定义技能

参考 [Skills API Quickstart](https://docs.claude.com/en/api/skills-guide#creating-a-skill)。

---

## 总结

两周前我们对仓库做了整体鸟瞰，这一次我们深入了三个具体技能的实现细节。核心收获可以归纳为三点：

**第一，Skills 是工程化的，不是灵感式的。** MCP Builder 的四阶段方法论、Skill Creator 的迭代评估闭环，都在说同一件事：高质量技能需要系统性开发，而非靠一次 prompt 搞定。

**第二，文档技能的「Source-Available」模式值得关注。** Anthropic 将最核心的生产级技能（PDF/DOCX/PPTX/XLSX）公开了源码但不开放使用许可，这既维护了商业利益，又为开发者提供了研究材料。这种中间态的开放策略在 AI 原生应用中可能是常态。

**第三，「反 AI 味」是 Skill 约束设计的试金石。** Frontend Design 技能的核心洞察——用设计风格约束对抗模型的同质化倾向——这个思路可以迁移到任何需要创造力的技能设计中：写作风格约束、代码架构约束、业务流程约束。本质上都是**在模型灵活性上叠加人类偏好**。

如果你想从「会用 Skills」进化到「会构建 Skills」，强烈建议从 `template/SKILL.md` 开始，基于 `skill-creator` 的流程迭代一个自己的技能——过程中对 Skill 的理解会远比只读文档深刻得多。

---

## 相关资源

- 仓库地址：[github.com/anthropics/skills](https://github.com/anthropics/skills)
- Agent Skills 规范：[agentskills.io](https://agentskills.io)
- 官方博客：[Equipping Agents for the Real World with Agent Skills](https://anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- 入门指南：[Anthropics Skills 仓库全解析：从入门到精通的 Agent Skills 实战指南](/tech/anthropics-skills-agent-skills-repository-guide)
- Skill Creator 专题：[Skill Creator：Anthropic 出品的 AI Agent 技能开发框架完全指南](/tech/skill-creator-anthropic-skill-authoring-guide)
- Agent Skills 规范专题：[Agent Skills：AI Agent 能力扩展开放规范完全指南](/tech/agent-skills-ai-agent-open-specification-guide)