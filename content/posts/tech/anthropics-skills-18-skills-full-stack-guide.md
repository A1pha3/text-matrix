---
title: "Anthropic Skills 仓库进阶实战：18个技能覆盖研发全链路"
date: "2026-05-16T15:10:00+08:00"
slug: "anthropics-skills-18-skills-full-stack-guide"
aliases:
  - "/posts/tech/anthropics-skills-agent-skills-repository-guide/"
description: "Anthropic 的 Skills 仓库真正解决的不是「AI 能做什么」，而是「怎么让 AI 稳定地产出可控结果」——18 个技能分别从方法论、品质控制和文件格式三个方向施加约束。本文拆解四个最深技能的工程细节，并给出一套按需采用的路线图。"
draft: false
categories: ["技术笔记"]
tags: ["Claude", "Agent Skills", "Anthropic", "MCP", "工作流自动化"]
---

Anthropic Skills 仓库进阶实战： 个技能覆盖研发全链路

[anthropics/skills](https://github.com/anthropics/skills) 仓库的关键价值不在这 18 个技能各自能做什么——单看任何一个，你都能找到替代方案。值得看的是它的分层逻辑：**用方法论技能控制开发过程，用设计约束技能控制输出品质，用文件格式技能控制交付形态**。三层叠加后，Agent 的行为才从「不可预测的生成」收束到「可预期的工作流」。

以下是这 18 个技能的三层分类——建议先扫一眼这张表，再进入单个技能的细节，否则很容易把不同层级的东西混在一起理解：

| 层级 | 解决的问题 | 代表技能 | 输入 → 输出 |
|------|-----------|----------|-------------|
| **方法论层** | Agent 的开发流程怎么规范化 | `mcp-builder`、`skill-creator`、`claude-api` | 开发规范 → 可运行的 MCP 服务器 / 可复用的技能 |
| **品质控制层** | Agent 的产出怎么避免模型默认风格 | `frontend-design`、`canvas-design`、`algorithmic-art`、`webapp-testing` | 设计约束 → 高辨识度的界面 / 可验证的测试脚本 |
| **文件格式层** | Agent 怎么读写真实世界的文件 | `docx`、`pdf`、`pptx`、`xlsx` | 自然语言指令 → .docx / .pdf / .pptx / .xlsx 文件 |

这篇文章从三层中各挑一个最深的拆开：方法论层的 MCP Builder（四阶段开发流程）、品质控制层的 Frontend Design（反 AI 美学的设计约束）、文件格式层的四个文档技能（ZIP + XML 的内部实现），再加上横跨方法论层的 Skill Creator（技能开发的迭代闭环）。

读完你能回答：

- MCP Builder 四阶段流程里，哪一步最容易跳过，跳过以后会在哪一步栽跟头
- Frontend Design 怎么用字体、配色、布局三个维度的约束让 AI 生成不像 AI 的界面
- .docx 本质是 ZIP + XML——Agent 怎么读写这个结构
- Skill Creator 的渐进式披露怎么降 token 成本

---

一、MCP Builder：MCP 服务器开发的系统性方法论

MCP（Model Context Protocol）是 Anthropic 主推的 AI 与外部工具交互协议。`mcp-builder` 技能把 MCP 服务器开发拆成四个阶段：**深度调研 → 规划 → 实现 → 测试**，每一步有明确的交付物和检查点。

. Phase ：深度调研与规划

.. 理解 MCP 设计哲学

MCP 服务器的质量取决于两个维度的平衡：

- **API 覆盖度**：提供完整的 API 端点覆盖，给 Agent 最大组合自由度
- **工作流工具**：针对高频场景封装高层工具，降低 Agent 操作复杂度

两者不矛盾——Agent 能力强的客户端（如 Claude Code）可以直接组合基础工具完成复杂任务，能力较弱的客户端依赖封装好的工作流工具。

.. 工具命名规范

工具命名采用 `前缀_动作_资源` 的三段式结构，例如 `github_create_issue`、`github_list_repos`。清晰的命名帮助 Agent 快速定位所需工具，而非在大量同名工具中迷失。

错误消息设计同样关键：每条错误应包含**具体建议**和**下一步操作**，而不是仅仅返回"失败"。

.. 框架选择

技能推荐使用 **TypeScript**（基于 `@modelcontextprotocol/typescript-sdk`）作为首选语言，原因有三：

- AI 模型生成 TypeScript 代码质量高（静态类型 + 广泛使用）
- 远程服务器推荐 **Streamable HTTP**（无状态，易于扩展）
- 本地服务器推荐 **stdio**（简单直接）

Python 开发者可使用官方 `python-sdk`，行为模式一致。

.. 调研阶段交付物

| 交付物 | 说明 |
|--------|------|
| API 端点清单 | 优先级排序，标注核心与辅助端点 |
| 认证方案 | API Key、OAuth 或其他认证方式 |
| 数据模型 | 请求/响应结构，关键字段类型 |
| 错误处理策略 | 各端点可能的错误码与重试逻辑 |

. Phase ：项目结构规划

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

每个文件职责单一，工具函数按资源类型分目录组织。

. Phase ：实现要点

写好工具描述（description）

工具的 `description` 字段是 Agent 决策的关键依据。好的描述应该：

- 说明工具的**用途**而非实现细节
- 列举典型的**输入格式**和**输出示例**
- 指明**适用场景**和**禁忌场景**

分页与过滤支持

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

错误规范化

所有工具应返回统一格式的错误：

```json
{
  "error": true,
  "code": "RESOURCE_NOT_FOUND",
  "message": "Repository not found: owner/repo",
  "suggestion": "Check the repository name and ensure you have access"
}
```

. Phase ：测试验证

使用 Playwright 进行端到端测试：

```bash
安装 MCP 服务器到 Claude Code
claude mcp add my-server ./path/to/server

在 Claude Code 中执行集成测试
/claude-code-test "list the first 5 repositories"
```

---

二、Frontend Design：用设计约束打破 AI 默认审美

`frontend-design` 是仓库中最具特色的技能之一，它要解决的问题是**AI 生成界面同质化**。

. 问题诊断：AI 生成的界面为什么长得一样

Anthropic 工程师在技能文档里指出，AI 生成的 Web 界面普遍带有以下特征：

- 背景渐变 + 大量留白
- 蓝色/紫色为主色调
- 使用 Inter / Arial 等无特征字体
- 卡片式布局 + 圆角
- 「Get Started」「Learn More」式按钮文案

这些特征单个看没问题，问题是**它们出现在每一个 AI 生成的项目里**，界面就失去了品牌辨识度。

. 设计约束的三个层次

Frontend Design 技能通过三步约束来解决这个问题：

第一步：明确设计方向

在写代码之前，Agent 必须先确认：

- **目的（Purpose）**：这个界面解决什么问题？谁来用？
- **基调（Tone）**：选择一种极端风格——极简主义、复古未来、杂志风、工业风、奢华精致、卡通玩具……风格没有对错，但必须**极端且一致**
- **约束（Constraints）**：技术限制（框架、性能、无障碍）是什么？
- **差异化（Differentiation）**：用户会记住这个界面的什么？

第二步：字体选择

技能要求 Agent **避免使用 Arial、Inter、Roboto** 等常见字体，改用具有独特气质的字体：

| 类型 | 推荐字体 | 适用场景 |
|------|----------|----------|
| 展示字体 | Syne、Clash Display、Fustig | 大标题，强调个性 |
| 正文字体 | Instrument Sans、Outfit、PP Neue Montreal | 界面正文，高可读性 |
| 等宽字体 | JetBrains Mono、Geist Mono | 代码、数据展示 |

展示字体和正文字体的配对比正文内容本身更重要。

第三步：配色克制

避免使用 AI 偏爱的蓝紫渐变。推荐策略：

- 主色：选择一个**有情感倾向**的颜色（如 `#D97757` 的温暖橙，而非中性的蓝）
- 背景：考虑非白色（如 `#faf9f5` 的米白）或非纯黑（如 `#141413` 的深灰）
- 强调色：通过 2-3 个辅色构建色彩系统，而非随机添加

. 代码质量标准

技能对生成的代码有明确要求：

- **可用性优先**：生成的界面必须是可以正常运行的完整代码，而非设计稿
- **细节打磨**：光标样式、过渡动画、`hover` 状态、`focus` 可见性等微交互必须到位
- **响应式布局**：至少覆盖 375px（移动端）和 1440px（桌面端）
- **无障碍基础**：`aria-label`、`keyboard navigation`、色彩对比度合规

---

三、文档技能：支撑 Claude 文件能力的幕后架构

Claude 的「创建文件」能力（Word、PDF、PPT、Excel）背后，是一组 Anthropic **Source-Available**（非开源）的文档技能，位于仓库的 `skills/docx`、`skills/pdf`、`skills/pptx`、`skills/xlsx` 目录。

. DOCX 技能：.docx 是 ZIP + XML

DOCX 技能的关键认知：**.docx 文件说到底是一个 ZIP 压缩包，内部是结构化的 XML 文件**。

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

. PDF 技能：表单字段提取

PDF 技能的亮点是对**表单字段**的处理能力：

```bash
提取 PDF 中的表单字段
python scripts/pdf/extract_form_fields.py document.pdf

输出示例
{
  "fields": [
    {"name": "full_name", "type": "text", "page": 1, "rect": [72, 650, 288, 678]},
    {"name": "email", "type": "text", "page": 1, "rect": [72, 600, 288, 628]},
    {"name": "agree_terms", "type": "checkbox", "page": 1, "rect": [72, 550, 96, 574]}
  ]
}
```

这使得 Agent 可以识别 PDF 表单的结构并进行批量填充，而非仅仅做文字提取。

. PPTX 技能：基于 python-pptx 的结构化构建

PPTX 技能使用 `python-pptx` 库构建幻灯片：

```python
from pptx import Presentation
from pptx.util import Inches, Pt

prs = Presentation()
slide = prs.slides.add_slide(prs.slide_layouts[6])  # 空白布局

添加标题
title = slide.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(9), Inches(1))
title.text = "Title Here"

添加内容
content = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(9), Inches(5))
tf = content.text_frame
p = tf.paragraphs[0]
p.text = "Content here"
p.font.size = Pt(18)
```

技能的指令中包含**模板主题系统**，支持快速应用品牌色和字体。

. XLSX 技能：结构化数据处理

XLSX 技能的核心依赖是 `openpyxl` 库，覆盖以下场景：

- **样式应用**：单元格颜色、边框、合并、列宽、行高
- **公式处理**：插入和验证 Excel 公式（VLOOKUP、SUMIF、INDEX/MATCH 等）
- **图表生成**：基于数据范围创建柱状图、折线图、饼图
- **批量操作**：多 sheet 管理、数据透视表

. 许可证

四个文档技能采用 **Proprietary** 许可证（见各 SKILL.md 顶部的 `license` 字段），Anthropic 将其描述为「Source-Available」——代码已公开，使用受限。这跟仓库里其他技能的 Apache 2.0 许可证不同。

---

四、Skill Creator：从编写到评估的迭代闭环

`skill-creator` 本身就是用 Agent Skills 工作流构建技能的示范。它把技能开发拆成四个阶段，循环迭代直到满意。

. 四阶段迭代流程

```
意图捕获 → SKILL.md 编写 → 测试用例运行 → 评估分析 → 重写优化 → 重复
```

Stage ：捕获意图（Capture Intent）

从对话历史中提取：

- 技能要完成什么任务？
- 什么时候触发？（用户说什么时激活）
- 期望的输出格式是什么？
- 是否需要测试用例？

Stage ：编写 SKILL.md

基于意图，编写符合规范的 SKILL.md，包含：

- **`name`**：小写 + 连字符，唯一标识
- **`description`**：触发条件 + 功能描述。注意：描述要略微「激进」，因为 Claude 有「技能触发不足」的问题
- **`compatibility`**：所需工具和依赖（可选）
- **正文**：指令、示例、指南

**description 的优化技巧**：用 `skill-creator` 技能中的 `description-optimizer` 脚本分析触发准确率，持续优化描述文本。

Stage ：测试与评估

创建测试 prompt（eval queries），确保覆盖：

- 技能应该触发的场景（正例）
- 技能不应触发的场景（负例）
- 边界条件和极端输入

使用 `eval-viewer/generate_review.py` 脚本生成评估报告。

Stage ：迭代优化

根据评估结果重写 SKILL.md，重复流程直到：

- 触发准确率达标
- 输出质量稳定
- 测试用例覆盖主要场景

. 渐进式披露

技能描述的大小预算遵循 LLM 上下文的经济学原则：

| 层级 | 内容 | 大小 |
|------|------|------|
| L1 | `name` + `description` | ~100 词，始终加载 |
| L2 | 完整 SKILL.md 正文 | ~500 行，触发时加载 |
| L3 | 脚本/模板/参考文件 | 无限制，按需加载 |

技能创建者需要在**信息充分性**和**上下文成本**之间找到平衡。`description` 应极度精炼——只描述「何时触发、做什么」，不解释「如何实现」。

---

五、把这些技能串起来：一个完整的跨技能任务

看完上面四个技能的细节，你可能会觉得它们各自独立。但实际上这些技能的设计意图是**组合使用**——一个典型的工程任务会穿过方法论层、文件格式层和品质控制层。

举个具体例子。假设你要做一件事：**自动生成项目周报，包含任务统计表、趋势图表和展示页面**。任务流过三层技能的过程是：

1. **方法论层 — MCP Builder**：先写一个 Notion MCP 服务器，把 Notion 数据库里的「本周完成的任务」和「延期任务」拉出来。调研阶段需要搞清楚 Notion API 的分页和过滤参数（`page_size`、`filter` 的 `date` 条件），工具命名用 `notion_query_database`、`notion_get_page` 这样 Agent 能一眼看懂的模式。

2. **文件格式层 — XLSX + DOCX**：拿到结构化数据后，用 XLSX 技能生成带公式的统计表（`SUMIF` 按项目分组汇总工时），再用 DOCX 技能创建带页眉页脚的正式周报文档。这里的关键是 XLSX 输出的列名和 DOCX 里的表格标题要对齐——技能本身不校验这个，你得在 prompt 里明确字段映射。

3. **品质控制层 — Frontend Design**：为了让团队能在线看周报，用 Frontend Design 生成一个展示页面。这时候如果直接让 AI 生成，大概率是蓝紫渐变 + Inter 字体 + 卡片布局。在 prompt 里约束「用公司品牌色 #D97757、字体配 Syne（标题）+ Instrument Sans（正文）、背景用 #faf9f5」，出来的页面就有辨识度了。

4. **回到方法论 — Skill Creator**：三件事跑通后，把整个流程打包成一个 Skill——定义触发词「生成周报」、写好 SKILL.md 的 description、用渐进式披露的三层结构控制 token 成本。以后说一句「生成周报」就能复用整条链路。

这个例子里，MCP Builder 保证数据来源可靠，文件格式技能保证输出格式正规，Frontend Design 保证展示不撞脸，Skill Creator 保证下次不用重来。四者缺一环，整个流程就会在某一步断裂。

---

六、 个技能速览与分类索引

以下是仓库 `skills/` 目录下全部 18 个技能的快速索引。表头的「层级」对应开头那张总览表，方便回查。

创意与设计类

| 技能 | 层级 | 描述 | 许可证 |
|------|------|------|--------|
| `algorithmic-art` | 品质控制 | 使用 p5.js 创建程序化艺术，输出 .md + .html + .js | Apache 2.0 |
| `canvas-design` | 品质控制 | 设计哲学 → 视觉表达的完整流程，输出 PDF / PNG | Apache 2.0 |
| `slack-gif-creator` | 品质控制 | Slack 优化的 GIF 创建工具包（128×128 / 480×480） | Apache 2.0 |
| `theme-factory` | 品质控制 | 10 个预设主题（配色 + 字体），支持自定义生成 | Apache 2.0 |

研发与工程类

| 技能 | 层级 | 描述 | 许可证 |
|------|------|------|--------|
| `claude-api` | 方法论 | Claude API / Anthropic SDK 开发指南，含多语言支持 | Apache 2.0 |
| `frontend-design` | 品质控制 | 避免 AI 默认审美的独特界面设计系统 | Apache 2.0 |
| `mcp-builder` | 方法论 | MCP 服务器四阶段开发方法论 | Apache 2.0 |
| `skill-creator` | 方法论 | 从意图捕获到评估优化的技能构建框架 | Apache 2.0 |
| `webapp-testing` | 品质控制 | Playwright + Python 的 Web 应用测试工具包 | Apache 2.0 |

企业与沟通类

| 技能 | 层级 | 描述 | 许可证 |
|------|------|------|--------|
| `brand-guidelines` | 品质控制 | Anthropic 官方品牌配色与字体应用 | Proprietary |
| `internal-comms` | 方法论 | 内部沟通文档模板（3P 更新、公司通讯、事件报告等） | Apache 2.0 |

文档类（Source-Available）

| 技能 | 层级 | 描述 | 许可证 |
|------|------|------|--------|
| `doc-coauthoring` | 方法论 | 文档协作工作流：上下文收集 → 迭代精炼 → 读者测试 | Apache 2.0 |
| `docx` | 文件格式 | Word 文档创建、编辑与分析 | Proprietary |
| `pdf` | 文件格式 | PDF 读取、表单字段提取、创建与转换 | Proprietary |
| `pptx` | 文件格式 | PowerPoint 幻灯片生成与编辑 | Proprietary |
| `xlsx` | 文件格式 | Excel 电子表格处理、公式与图表 | Proprietary |

---

七、安装与使用

在 Claude Code 中安装

```bash
方式一：注册为 Plugin 市场
/plugin marketplace add anthropics/skills

安装示例技能集
/plugin install document-skills@anthropic-agent-skills
/plugin install example-skills@anthropic-agent-skills

方式二：直接安装
/plugin install document-skills@anthropic-agent-skills
/plugin install example-skills@anthropic-agent-skills
```

安装后，直接在对话中提及技能即可触发，例如：

> 「Use the PDF skill to extract form fields from `contract.pdf`」

在 Claude.ai 中使用

付费用户可直接使用仓库中所有示例技能。上传自定义技能参考官方文档中的[使用指南](https://support.claude.com/en/articles/12512180-using-skills-in-claude#h_a4222fa77b)。

通过 API 上传自定义技能

参考 [Skills API Quickstart](https://docs.claude.com/en/api/skills-guide#creating-a-skill)。

---

FAQ

**Q1: 四个文档技能为什么用 Proprietary 许可证而不是 Apache 2.0？**

从商业角度看，这四个技能直接支撑 Claude 的付费文件能力——PDF 表单提取、DOCX 修订追踪、PPTX 生成和 XLSX 公式引擎都是 Claude 区别于其他模型的核心交付物。开源代码让开发者能看到实现细节（比如 .docx 怎么用 ZIP + XML 构建），但保留商业使用限制。仓库里其他技能（MCP Builder、Frontend Design 等）都是 Apache 2.0，原因是它们不直接绑定付费功能，而是作为生态基础设施存在。

实际影响：你可以研究四个文档技能的内部实现，但如果你要做商业产品，最好自己实现文件读写逻辑，或者用开源替代方案（如 `python-docx` + `python-pptx` + `openpyxl` 自己封装一套）。

**Q2: Frontend Design 的设计约束会不会让生成结果走向另一个极端？**

会的。技能文档明确要求「极端且一致的风格」——极简主义就极简到底，复古未来就复古到底。它的目标不是「最好看的设计」，而是「拉开和 AI 默认审美的最大距离」。如果你要的是更温和的设计变量，在 prompt 里覆盖技能的默认约束就行，例如把「极端风格」改成「专业企业风格，但避免蓝紫渐变和 Inter 字体」。

**Q3: Skill Creator 的渐进式披露三层怎么控制 token 成本？**

L1（name + description，约 100 词）始终在上下文中——这是技能被触发的判断依据。L2（完整 SKILL.md，约 500 行）只在技能激活时加载。L3（脚本 / 模板 / 参考文件）在 Agent 执行到具体步骤时才按需读取。

举个例子：如果你装了 18 个技能，上下文里常驻的只有 18 × ~100 词 ≈ 1800 词的 L1 描述。只有当你说「用 PDF 技能提取表单字段」时，PDF 技能的 ~500 行 L2 正文和对应的 `extract_form_fields.py`（L3）才会加载。三层设计确保 18 个技能同时存在时，上下文窗口不会被撑满。

也就是 Skill Creator 的关键设计决策不是「写多详细」，而是「L1 的 ~100 词怎么写得让触发准确率最高」——漏触发和误触发都浪费 token。

自测

1. 打开 MCP Builder 的指导文档，挑一个你日常用的工具（GitHub、Jira 或 Notion），用四阶段流程走一遍 MCP 服务器开发。记录一下哪一阶段最花时间——大概率是 Phase 1 的 API 端点调研，因为你要同时考虑覆盖度和工作流封装。
2. 找一个你最近用 AI 生成的界面，对照 Frontend Design 的三步约束检查：字体是不是 Arial / Inter / Roboto？配色是不是蓝紫渐变？如果是，用技能里推荐的字体和配色重做一版，看看出来的效果能不能让你一眼认出「这不是 AI 默认审美」。
3. 用 DOCX 技能创建一个带修订追踪的 Word 文档。你不需要手动编辑 XML——Agent 会处理解包和重打包。验证 `pandoc --track-changes=all` 能不能正确提取追踪内容。如果你发现提取器漏了某些类型的修订（比如格式修订），记下来，这是技能当前已知的边界。
4. 用 Skill Creator 四阶段流程写一个你自己的技能。Stage 3 是最容易被跳过的——你的测试 prompt 覆盖了正例、负例和边界条件吗？用 `description-optimizer` 检查触发准确率。如果你发现 description 写得越长准确率反而越低，说明你在 L1 里塞了实现细节，该精简了。

采用路线图

18 个技能不是需要全部学的。按你当前所处的阶段，建议这样入手：

**如果你刚接触 Agent Skills**：从 `claude-api` 和 `skill-creator` 开始。先搞清楚 Claude API 的调用模式，再用 Skill Creator 把一个你重复过 3 次以上的工作流打包成技能。这两个技能是方法论层的基础，其他技能都是在这个基础上扩出来的。

**如果你在做内部工具**：`mcp-builder` + `docx` / `xlsx`。先给团队的数据源写 MCP 服务器（数据库、项目管理工具、文档系统），再用文档技能把数据变成可分发文件。这条链路最常见的使用场景就是周报生成、数据导出、合同填充。

**如果你在做对外产品**：`frontend-design` + `canvas-design` + `algorithmic-art`。在 UI 和品牌物料上跟 AI 默认风格拉开距离。这一步的投入产出比很高——同样的功能，界面不撞脸的用户留存率和品牌记忆度完全不一样。

**如果你在做文档密集型工作**：四个文档技能（`docx`、`pdf`、`pptx`、`xlsx`）+ `doc-coauthoring`。注意许可证——文档技能是 Proprietary 的，如果是商业产品，建议自己封装文件读写逻辑。

**如果你时间有限**：只盯 `skill-creator`。因为它能帮你把其他工具（不管是 Anthropic 技能还是你自建的）组装成一条可复用链路——这就是第五节的周报例子想说明的模式。

相关资源

- [anthropics/skills](https://github.com/anthropics/skills)
- [Agent Skills 规范](https://agentskills.io)
- [Equipping Agents for the Real World with Agent Skills](https://anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Anthropics Skills 仓库全解析（入门篇）](/tech/anthropics-skills-agent-skills-repository-guide)
- [Skill Creator 开发框架完全指南](/tech/skill-creator-anthropic-skill-authoring-guide)
- [Agent Skills 开放规范完全指南](/tech/agent-skills-ai-agent-open-specification-guide)