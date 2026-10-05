---
title: "Anthropic Skills 仓库进阶实战：19 个技能覆盖研发全链路"
date: "2026-05-16T15:10:00+08:00"
lastmod: "2026-09-27T12:00:00+08:00"
slug: "anthropics-skills-18-skills-full-stack-guide"
github_repo: "anthropics/skills"
source_key: "gh:anthropics/skills"
aliases:
  - "/posts/tech/anthropics-skills-agent-skills-repository-guide/"
description: "Anthropic 的 Skills 仓库真正解决的不是「AI 能做什么」，而是「怎么让 AI 稳定地产出可控结果」——19 个技能分别从方法论、品质控制和文件格式三个方向施加约束。本文拆解四个最深技能的工程细节，并给出一套按需采用的路线图。"
draft: false
categories: ["技术笔记"]
tags: ["Claude", "Agent Skills", "Anthropic", "MCP", "工作流自动化"]
---

# Anthropic Skills 仓库进阶实战：19 个技能覆盖研发全链路

[anthropics/skills](https://github.com/anthropics/skills) 仓库的分层逻辑比单个技能更值得花时间。这 19 个技能各自能做什么，单看任何一个你都能找到替代方案；但三层叠加后，Agent 的行为会从「不可预测的生成」收束到「可预期的工作流」：**用方法论技能控制开发过程，用设计约束技能控制输出品质，用文件格式技能控制交付形态**。

> 仓库持续更新，本文技术细节以 2026 年 9 月 27 日的主干为口径核对（GitHub API 当日读数）。
> **快速信息卡**
> - **Stars**: 178,612
> - **Forks**: 21,138
> - **License**: 仓库无统一许可证——多数技能 Apache 2.0，四个文档技能为 Proprietary
> - **语言**: Python
> - **最后更新**: 2026-09-24（主干最近一次提交）

**学习目标**：读完你能回答——
- MCP Builder 四阶段流程里，哪一步最容易被跳过，跳过以后会在哪一步栽跟头
- Frontend Design 怎么靠「先定计划、再对照简报自查」的流程避开 AI 默认审美
- .docx 本质是 ZIP + XML——Agent 怎么读写这个结构
- Skill Creator 的渐进式披露怎么降 token 成本

先扫一眼这张三层分类表，再进入单个技能的细节，避免把不同层级的东西混在一起理解：

**目录**
- 一、MCP Builder：MCP 服务器开发的系统性方法论
- 二、Frontend Design：用设计约束打破 AI 默认审美
- 三、文档技能：支撑 Claude 文件能力的幕后架构
- 四、Skill Creator：从编写到评估的迭代闭环
- 五、把这些技能串起来：一个完整的跨技能任务
- 六、技能速览与分类索引
- 七、安装与使用
- FAQ
- 自测
- 采用路线图

| 层级 | 解决的问题 | 代表技能 | 输入 → 输出 |
|------|-----------|----------|-------------|
| **方法论层** | Agent 的开发流程怎么规范化 | `mcp-builder`、`skill-creator`、`claude-api` | 开发规范 → 可运行的 MCP 服务器 / 可复用的技能 |
| **品质控制层** | Agent 的产出怎么避免模型默认风格 | `frontend-design`、`canvas-design`、`algorithmic-art`、`webapp-testing` | 设计约束 → 高辨识度的界面 / 可验证的测试脚本 |
| **文件格式层** | Agent 怎么读写真实世界的文件 | `docx`、`pdf`、`pptx`、`xlsx` | 自然语言指令 → .docx / .pdf / .pptx / .xlsx 文件 |

这篇文章从三层中各挑一个最深的拆开：方法论层的 MCP Builder（四阶段开发流程）、品质控制层的 Frontend Design（反 AI 美学的设计约束）、文件格式层的四个文档技能（ZIP + XML 的内部实现），再加上横跨方法论层的 Skill Creator（技能开发的迭代闭环）。

---

## 一、MCP Builder：MCP 服务器开发的系统性方法论

MCP（Model Context Protocol）是 Anthropic 主推的 AI 与外部工具交互协议。`mcp-builder` 技能把 MCP 服务器开发拆成四个阶段：**深度调研与规划 → 实现 → 评审与测试 → 创建评估**，每一步有明确的交付物和检查点。前三个阶段产出可用的服务器，最后一个阶段验证「LLM 能不能把它用好」——这是最容易被忽略、也被技能文档放在独立阶段强调的一环。

### Phase 1：深度调研与规划

#### 理解 MCP 设计哲学

MCP 服务器的质量取决于两个维度的平衡：

- **API 覆盖度**：提供完整的 API 端点覆盖，给 Agent 最大组合自由度
- **工作流工具**：针对高频场景封装高层工具，降低 Agent 操作复杂度

两者可以共存——有的客户端受益于用代码执行组合基础工具，有的更适合高层工作流。技能文档给的建议很明确：拿不准时，优先保证 API 覆盖度。

#### 工具命名规范

工具命名采用统一前缀加动作的结构，例如 `github_create_issue`、`github_list_repos`。清晰的命名让 Agent 能快速定位所需工具，避免在大量同名工具中迷失。

错误消息设计同样关键：技能文档要求每条错误都要「引导 Agent 走向解决方案，给出具体建议和下一步操作」；仅返回"失败"会让 Agent 无法决策下一步动作。

#### 框架选择

技能推荐使用 **TypeScript**（基于 `@modelcontextprotocol/typescript-sdk`）作为首选语言，理由写在文档里：SDK 质量高、在多种执行环境（如 MCPB）兼容性好，且 AI 模型生成 TypeScript 代码的质量高——静态类型和广泛使用都帮了忙。

传输方式按部署形态选：

- 远程服务器推荐 **Streamable HTTP**（无状态 JSON，比有状态会话更容易水平扩展）
- 本地服务器推荐 **stdio**

Python 开发者可使用官方 `python-sdk`（FastMCP），技能附带了对应语言的实现指南。

#### 调研阶段交付物

Phase 1 的落点是读 API 文档、列出要实现的端点。按文档原话，至少搞清三件事：

| 交付物 | 说明 |
|--------|------|
| API 端点清单 | 从最常用的操作开始排优先级 |
| 认证方案 | API Key、OAuth 或其他认证方式 |
| 数据模型 | 请求/响应结构，关键字段类型 |

调研还包括读 MCP 协议文档（从 modelcontextprotocol.io 的 sitemap 入手，抓取带 `.md` 后缀的页面）和框架文档——技能把 TypeScript SDK、Python SDK 的 README 地址直接写进了指令，要求 Agent 按需加载。

### Phase 2：实现

#### 项目结构与命名

TypeScript 实现指南规定了服务器的命名模式：`{service}-mcp-server`，小写连字符，不带版本号——官方给的例子是 `github-mcp-server`、`jira-mcp-server`。项目结构随之固定下来：

```text
{service}-mcp-server/
├── package.json
├── tsconfig.json
├── README.md
└── src/
    ├── index.ts          # 入口，完成 McpServer 初始化
    ├── types.ts          # TypeScript 类型定义与接口
    └── tools/            # 工具实现，每个领域一个文件
```

#### 实现核心基础设施与工具

先搭共享层：带认证的 API client、错误处理辅助函数、响应格式化（JSON/Markdown）、分页支持。然后逐个实现工具。工具的输入校验用 Zod（TypeScript）或 Pydantic（Python），能定义 `outputSchema` 的地方尽量定义，并在响应里带上 `structuredContent`——这是 TypeScript SDK 的特性，让客户端拿到结构化数据而不只是文本。

工具注册用现代 API `server.registerTool`（旧式 `server.tool()` 已废弃）：

```typescript
server.registerTool(
  "tool_name",
  {
    title: "Tool Display Name",
    description: "What the tool does",
    inputSchema: { param: z.string() },
    outputSchema: { result: z.string() }
  },
  async ({ param }) => {
    const output = { result: `Processed: ${param}` };
    return {
      content: [{ type: "text", text: JSON.stringify(output) }],
      structuredContent: output
    };
  }
);
```

另外四个标注（annotations）值得顺手加上：`readOnlyHint`、`destructiveHint`、`idempotentHint`、`openWorldHint`——它们告诉客户端一次调用的副作用边界。

#### 写好工具描述（description）

工具的 `description` 字段是 Agent 决策的关键依据。技能文档要求的描述包含三部分：功能的简洁摘要、每个参数的说明、返回类型的 schema。

#### 分页与过滤支持

设计工具时，应支持分页和过滤，让 Agent 可以灵活控制返回数据量。最佳实践文档还给了条实用细节：错误消息里直接教 Agent 怎么缩小结果集，比如「Try using filter='active_only' to reduce results」。

#### 错误规范化

错误作为工具结果返回（`isError: true`），而不是协议层错误——这是最佳实践文档的明确要求。官方示例长这样：

```typescript
try {
  const result = performOperation();
  return { content: [{ type: "text", text: result }] };
} catch (error) {
  return {
    isError: true,
    content: [{
      type: "text",
      text: `Error: ${error.message}. Try using filter='active_only' to reduce results.`
    }]
  };
}
```

安全边界也有明确条款：不向客户端暴露内部错误细节，安全相关错误只在服务端记录日志。

### Phase 3：评审与测试

代码评审有四条检查线：没有重复代码（DRY）、错误处理一致、类型覆盖完整、工具描述清晰。然后构建验证：TypeScript 跑 `npm run build` 确认编译通过，再用 **MCP Inspector** 做交互测试（`npx @modelcontextprotocol/inspector`）；Python 侧用 `python -m py_compile` 验证语法，同样走 Inspector。

### Phase 4：创建评估

这是 mcp-builder 区别于普通教程的一步：写完服务器不算完，还要回答「LLM 能不能用好它」。评估的做法是让模型拿着你刚写的工具去回答真实问题——技能要求出 **10 个评估问题**，流程是：列出工具清单、用只读操作探索数据、生成问题、亲自解一遍验证答案。

每个问题要满足六条要求：独立（不依赖其他问题）、只读（不需要破坏性操作）、复杂（需要多次工具调用和深入探索）、真实（人在乎的真实用例）、可验证（答案唯一且能字符串比对）、稳定（答案不随时间变化）。产出是一个 `qa_pair` 组成的 XML 文件，仓库自带的 `scripts/evaluation.py` 负责跑评估。

Phase 1 的 API 端点调研最容易被跳过——开发者常以为看过文档就够了，但实际写工具时才发现分页参数、错误码、认证刷新这些细节没理清。跳过的代价会在后两个阶段集中爆发：工具描述写不准，Agent 调用时频繁失败；评估跑不起来，因为问题设计不出可验证的答案。

---

## 二、Frontend Design：用设计约束打破 AI 默认审美

`frontend-design` 是仓库中最具特色的技能之一，它要解决的问题是**AI 生成界面同质化**。技能的开场白把自己设定成一家设计工作室的设计主管：客户已经拒掉过一版「感觉像模板」的提案，付钱买的是一个有主见的方向——palette、字体、布局都要为这份简报量身定做，必要时承担审美风险。

### 问题诊断：AI 生成的界面为什么长得一样

这一节值得整段引用式地细读，因为技能文档给出了一张「AI 味特征清单」，而且逐条带了色值：

1. 暖奶油色背景（近 `#F4F1EA`）配高对比衬线展示字体，强调色是陶土或暖泥色——**常常恰好是 `#D97757`**。文档特意点名：这是 Anthropic 自家 Claude 的交互强调色，它出现在用户的简报里，反而是一个「AI 生成」的标志
2. 近黑背景配单一的亮酸绿或朱红强调色
3. 报纸式排版：发丝级分隔线、零圆角、密排的多栏布局
4. SaaS 卡片套装：内容切成等大的圆角卡片，所有元素共用同一个圆角值，卡片下压同一层灰阴影（rgba(0,0,0,.1)），再拿渐变当装饰
5. 模板化的「chrome」：每个标题上方一条拉宽字距的全大写眉题、元信息用中点连接（`A · B · C`）、`词 — 片段` 式带空格长破折号的标签、拿 `#0B0B0B` 这类近黑代替纯黑、小数据标签用等宽字体、链接和按钮文字后面挂一个 `→`

清单后那句判断是整节的题眼：这些手法单独看都合法，某些简报用它们也确实对——问题是它们是**默认**而不是**选择**，且不管题材是什么都会出现。简报明确指定了视觉方向时，照办（哪怕指定的是其中某种「AI 味」风格）；简报留白的轴上，别把自由花在默认值上。

### 流程：先出计划，对照简报自查，再写代码

技能把工作拆成两遍（two passes）。第一遍不是写代码，是写一份紧凑的设计计划（design plan），包含四个 token：

- **Color**：4–6 个命名的色值组成核心调色板
- **Type**：用什么字体、各自承担什么角色（一个字族或两个，两个就必须拉开明显差异；行宽默认压在 80 字符以内）
- **Layout**：布局概念用一句话的散文描述加 ASCII 线框图来推敲，包括对齐方式的取舍
- **Principles**：让这一页与众不同的高层原则

第二遍开始前有个自查动作：拿一份相似简报在心里走一遍，看会不会得到一份差不多的计划——如果会，说明这部分还是「任何页面都这么生成」的默认产物，改掉它，并写下改了什么、为什么。确认计划的独特性之后，才动笔写代码。写代码环节文档只给了一条工程警告：小心 CSS 选择器特异性互相抵消，`.section` 这类类型选择器和元素选择器叠加时，分区间距经常中招。

### 克制与自评

「把大胆花在一处」：让一个元素成为被记住的东西，其余一切保持安静和纪律，砍掉不为简报服务的装饰。动效的口径类似——一次编排好的页面加载好过散落各处的效果，逐节淡入上浮和每张卡片都挂 hover 过渡，正是文档点名的通用默认。

质量底线不张扬但要守住：响应式适配到移动端、键盘焦点可见、尊重系统的 reduced motion、视觉可及、调色板和谐。构建过程中对着截图自评——文档原话是「一张图抵 1000 个 token」——还借了 Chanel 的建议：出门前照照镜子，摘掉一件配饰。

### 文案也是设计

界面上的文字只为「让人更容易理解和使用」而存在，是设计内容不是装饰。按最终用户的视角命名——用户管理的是 notifications，不是 webhook config；用主动语态，CTA 直接说会发生什么：「Save changes」而不是「Submit」；同一个动作在整条流程里保持同名，按钮说「Publish」，完成的 toast 就说「Published」。错误消息不道歉、不含糊，用界面的口吻讲清哪里坏了怎么修；空状态是行动的邀请，不是情绪的舞台。

---

## 三、文档技能：支撑 Claude 文件能力的幕后架构

Claude 的「创建文件」能力（Word、PDF、PPT、Excel）背后，是一组 Anthropic **Source-Available**（非开源）的文档技能，位于仓库的 `skills/docx`、`skills/pdf`、`skills/pptx`、`skills/xlsx` 目录。README 的说法很直白：这些技能是 source-available 而非 open source，公开出来是给开发者当参考——看看一个在生产 AI 应用里真刀真枪使用的复杂技能长什么样。

### DOCX 技能：.docx 是 ZIP + XML

DOCX 技能的关键认知：**.docx 文件本质是一个 ZIP 压缩包，内部是结构化的 XML 文件**。理解这一层，才能解释为什么 Agent 能在不依赖 Word 的前提下读写文档——它操作的是 ZIP 包里的 XML 节点。

```text
document.docx
├── word/document.xml       # 正文内容
├── word/styles.xml         # 样式定义
├── word/numbering.xml      # 编号列表
├── word/header1.xml        # 页眉（可多个，文件名带编号）
├── word/footer1.xml        # 页脚（同上）
├── word/settings.xml       # 文档设置
├── [Content_Types].xml     # 文件类型声明
└── _rels/.rels             # 内部关系
```

技能的指令按任务选路线，覆盖了完整的操作矩阵：

| 操作 | 工具/方法 |
|------|-----------|
| 读取内容 | `pandoc -t markdown file.docx`；要保留修订语境时用 `--track-changes` 的不同模式 |
| 读取原始 XML | `unzip` 解包后直接读；外部来源的 docx 视为不可信，先删符号链接条目，再跑 `scripts/merge_runs.py` 合并碎片化文本 run |
| 创建新文档 | `docx-js`（npm 包，预装）生成结构化文档 |
| 编辑现有文档 | `unzip` → 编辑 `word/document.xml` → `zip` 重打包（docx-js 打不开已有文件） |
| 转换为 PDF | `python scripts/office/soffice.py --headless --convert-to pdf` |
| 接受修订 | `python scripts/accept_changes.py in.docx out.docx` |

编辑走 XML 路线时有一条纪律值得单独说：直接在原地编辑 `document.xml`，不要重新排版或美化格式—— pretty-print 过的 XML 会让 diff 和下游工具都难以处理。接受修订也有边界：`accept_changes.py` 和 `pandoc --track-changes=accept` 在「整段被删」的场景都可能留下空段落，技能文档把这个已知缺陷写得明明白白。

### PDF 技能：分两条路线处理表单

PDF 技能对表单的处理不是一条命令，而是一个先分流、再处理的流程，入口是 `check_fillable_fields.py`：

- **可填充表单**（AcroForm）：`extract_form_field_info.py` 把字段清单导成 JSON，填好 `field_id` 对应的值后交给 `fill_fillable_fields.py` 生成填好的 PDF；
- **非填充表单**（扫描件或平面 PDF）：`extract_form_structure.py` 先从版面里提取文本标签结构，再按标注方式回填。

```bash
# 1. 判断表单类型
python scripts/check_fillable_fields.py contract.pdf
# 2. 可填充：导出字段清单（JSON 里是 field_id 等真实字段结构）
python scripts/extract_form_field_info.py contract.pdf field_info.json
# 3. 填入值
python scripts/fill_fillable_fields.py contract.pdf field_values.json filled.pdf
```

这条分流让 Agent 可以识别 PDF 表单的结构并进行批量填充，把 PDF 从「只读的最终交付物」变成「可编程的表单容器」。

### PPTX 技能：pptxgenjs 创建，XML 编辑

PPTX 技能同样把 .pptx 当 ZIP + XML 对待，但按任务分流：**从零创建新 deck 写 pptxgenjs 脚本**（JS 库，官方文档整理了一堆 gotcha，比如 `<p:presentation>` 子元素的顺序不能动——移动后同一个 deck 会直接打不开）；**编辑已有 deck 或基于模板构建**则走 `unzip → 编辑 ppt/slides/slideN.xml → zip`。

`python-pptx` 在这套流程里只是编辑场景的一个选项，且技能文档明确列了它做不到的三件事：复制幻灯片（唯一入口是 `add_slide(layout)`）、通过 `text_frame.text = "..."` 赋值还保留格式（会把段落塌缩成一个无样式 run，要用 `run.text`）、读取模板里常见的 SVG/EMF 图形（`add_picture` 直接抛 `UnidentifiedImageError`）。

配套的脚本分工也细：`thumbnail.py` 把模板每页缩略图拼成带标注的网格供挑选版式；`office/validate.py` 做 schema、关系和内容类型校验，每个失败项都指名修法；`office/helpers/pptx_theme.py` 处理主题。技能末尾还压着强制 QA：内容 QA 和文件 QA 都是必做项。

### XLSX 技能：openpyxl 加三条铁律

XLSX 技能的核心依赖是 `openpyxl`（连同 `pandas`、`markitdown` 预装），按任务分流：创建或带公式/格式编辑用 openpyxl，只读值用 `load_workbook`，读「公式和值」要跑两遍。

三条铁律写在显眼位置：

- **零公式错误**：`recalc.py` 报 `errors_found` 就不许交付——哪怕你怀疑错误本来就在，也得先证明它不是你引入的
- **写公式，不写死结果**：单元格该写 `=SUM(B2:B9)` 而不是算好的总数，输入变了表格必须跟着变
- **逐字遵守用户规格**：tab 名、列头、用户点名的公式，一个都不能改；编辑已有文件时反过来——已有文件的约定压过这里所有准则，只往标记好的输入单元格写

重算（recalc）是硬性步骤：openpyxl 写的公式没有缓存值，不重算的话 pandas 之类读到的公式格全是 `None`。图表、格式（颜色、边框、合并、列宽）和格式转换都在覆盖范围内。

### 许可证

四个文档技能采用 **Proprietary** 许可证（见各 SKILL.md 顶部的 `license` 字段），Anthropic 将其描述为「Source-Available」——代码已公开，使用受限。为什么单独这四个不开源、其他技能的许可证分布，见文末 FAQ Q1 和速览表的许可证列。

---

## 四、Skill Creator：从编写到评估的迭代闭环

`skill-creator` 本身就是用 Agent Skills 工作流构建技能的示范。它把技能开发拆成一条循环流水线：捕获意图 → 访谈与调研 → 编写 SKILL.md → 测试运行 → 定性加定量评估 → 重写，重复直到满意，再扩大测试集规模验证。

### 迭代流程

#### Stage 1：捕获意图（Capture Intent）

优先从对话历史里提取——用户说「把这个做成技能」时，工具链、步骤顺序、用户做过的修正、观察到的输入输出格式都在上下文里。需要用户补的四个问题：

- 技能要让 Claude 完成什么？
- 什么时候触发？（用户说什么时激活）
- 期望的输出格式是什么？
- 是否需要测试用例？（输出可客观验证的技能适合配测试，写作风格类的往往不需要）

#### Stage 2：访谈与调研（Interview and Research）

这是流程里容易被略过、但技能文档单独立节的一步：主动追问边界情况、输入输出格式、示例文件、成功标准和依赖；能用上的 MCP（查文档、找同类技能）就并行调研。测试 prompt 要等这一步敲定后再写。

#### Stage 3：编写 SKILL.md

基于访谈结果，编写符合规范的 SKILL.md，包含：

- **`name`**：小写 + 连字符，唯一标识
- **`description`**：触发条件 + 功能描述。注意：描述要写得略微「pushy」，因为 Claude 存在「技能触发不足」（undertrigger）的倾向——这是技能文档原话给出的实践判断，还附了改写示例：把「how to build a simple fast dashboard」扩写成「只要用户提到 dashboards、数据可视化、内部指标就要用本技能，哪怕没明说 dashboard」
- **`compatibility`**：所需工具和依赖（可选，很少用）
- **正文**：指令、示例、指南

**description 的优化技巧**：skill-creator 自带一个独立的 skill description improver（脚本 `scripts/improve_description.py`），专门优化技能的触发准确率，流程走完可以单独跑。

#### Stage 4：测试与评估

创建测试 prompt 跑真实用例，评估分两条线：定性上用 `eval-viewer/generate_review.py` 生成可视化评审页，把输出样例和定量指标一起给人看——技能文档甚至用大写强调了「先让人类看到评审页，再自己评估输入」；定量上为每条测试写断言，产出 `benchmark.json`，比较各配置的 pass_rate、耗时和 token 用量。

这一段最容易被跳过——开发者写完 SKILL.md 就上线，结果触发准确率不稳定。测试 prompt 缺了正例、负例或边界条件中的任何一类，技能就会漏触发或误触发。

#### Stage 5：迭代与扩大

根据评估结果重写 SKILL.md，重复循环直到触发达标、输出稳定；最后扩大测试集再验证一轮。

### 渐进式披露

技能用三层加载系统控制上下文成本，预算数字是技能文档的官方口径：

| 层级 | 内容 | 大小 |
|------|------|------|
| L1 | `name` + `description` | 约 100 词，始终在上下文中 |
| L2 | 完整 SKILL.md 正文 | 理想控制在 500 行以内，触发时加载 |
| L3 | 脚本/模板/参考文件 | 不限制，按需加载（脚本可以不读入直接执行） |

文档同时说明这些数字是近似值，需要时可以超。技能创建者要在**信息充分性**和**上下文成本**之间找平衡：`description` 只描述「何时触发、做什么」，把「如何实现」留给 L2 和 L3；SKILL.md 接近 500 行时就加一层层级结构，用清晰的指针告诉执行模型下一步去哪读。

---

## 五、把这些技能串起来：一个完整的跨技能任务

看完上面四个技能的细节，容易以为它们各自独立。这些技能的设计意图其实是**组合使用**——一个典型的工程任务会穿过方法论层、文件格式层和品质控制层。

举个具体例子。假设你要做一件事：**自动生成项目周报，包含任务统计表、趋势图表和展示页面**。任务流过三层技能的过程是：

1. **方法论层 — MCP Builder**：先写一个 Notion MCP 服务器，把 Notion 数据库里的「本周完成的任务」和「延期任务」拉出来。调研阶段需要搞清楚 Notion API 的分页和过滤参数（`page_size`、`filter` 的 `date` 条件），工具命名用 `notion_query_database`、`notion_get_page` 这样 Agent 能一眼看懂的模式。

2. **文件格式层 — XLSX + DOCX**：拿到结构化数据后，用 XLSX 技能生成带公式的统计表（`SUMIF` 按项目分组汇总工时），再用 DOCX 技能创建带页眉页脚的正式周报文档。这里的关键是 XLSX 输出的列名和 DOCX 里的表格标题要对齐——技能本身不校验这个，你得在 prompt 里明确字段映射。

3. **品质控制层 — Frontend Design**：为了让团队能在线看周报，用 Frontend Design 生成一个展示页面。这时候如果直接让 AI 生成，大概率落在技能点名的默认项里——SaaS 卡片套装、模板化的 chrome、甚至那抹陶土橙。把公司 VI 里真实存在的品牌色和字体写进 prompt（技能的规则是简报里的原话优先），出来的页面就有辨识度了。

4. **回到方法论 — Skill Creator**：三件事跑通后，把整个流程打包成一个 Skill——定义触发词「生成周报」、写好 SKILL.md 的 description、用渐进式披露的三层结构控制 token 成本。以后说一句「生成周报」就能复用整条链路。

这个例子里，MCP Builder 保证数据来源可靠，文件格式技能保证输出格式正规，Frontend Design 保证展示不撞脸，Skill Creator 保证下次不用重来。四者缺一环，整个流程就会在某一步断裂。

---

## 六、技能速览与分类索引

以下是仓库 `skills/` 目录下全部 19 个技能的快速索引（2026-09-27 核对；仓库持续更新，以仓库为准）。表头的「层级」对应开头那张总览表，方便回查。

### 创意与设计类

| 技能 | 层级 | 描述 | 许可证 |
|------|------|------|--------|
| `algorithmic-art` | 品质控制 | 使用 p5.js 创建程序化艺术，带种子随机与交互式参数探索 | Apache 2.0 |
| `canvas-design` | 品质控制 | 设计哲学 → 视觉表达的完整流程，输出 PDF / PNG | Apache 2.0 |
| `slack-gif-creator` | 品质控制 | Slack 优化的 GIF 创建工具包（表情 128×128 / 消息 480×480） | Apache 2.0 |
| `theme-factory` | 品质控制 | 10 个预设主题（配色 + 字体），支持自定义生成 | Apache 2.0 |

### 研发与工程类

| 技能 | 层级 | 描述 | 许可证 |
|------|------|------|--------|
| `claude-api` | 方法论 | Claude API / Anthropic SDK 参考：模型 ID、定价、流式、工具使用、缓存，覆盖多语言 | Apache 2.0 |
| `frontend-design` | 品质控制 | 避免 AI 默认审美的独特界面设计系统 | Apache 2.0 |
| `mcp-builder` | 方法论 | MCP 服务器四阶段开发方法论 | Apache 2.0 |
| `skill-creator` | 方法论 | 从意图捕获到评估优化的技能构建框架 | Apache 2.0 |
| `web-artifacts-builder` | 品质控制 | 用 React、Tailwind CSS、shadcn 等构建复杂的多组件 claude.ai HTML artifacts | Apache 2.0 |
| `webapp-testing` | 品质控制 | Playwright + Python 的 Web 应用测试工具包 | Apache 2.0 |

### 企业与沟通类

| 技能 | 层级 | 描述 | 许可证 |
|------|------|------|--------|
| `brand-guidelines` | 品质控制 | Anthropic 官方品牌配色与字体应用 | Apache 2.0 |
| `internal-comms` | 方法论 | 内部沟通文档模板（3P 更新、公司通讯、事件报告等） | Apache 2.0 |

### 文档类（Source-Available）

| 技能 | 层级 | 描述 | 许可证 |
|------|------|------|--------|
| `doc-coauthoring` | 方法论 | 文档协作工作流：上下文收集 → 迭代精炼 → 读者测试 | SKILL.md 未标注许可证 |
| `docx` | 文件格式 | Word 文档创建、编辑与分析 | Proprietary |
| `pdf` | 文件格式 | PDF 读取、表单字段提取、创建与转换 | Proprietary |
| `pptx` | 文件格式 | PowerPoint 幻灯片生成与编辑 | Proprietary |
| `xlsx` | 文件格式 | Excel 电子表格处理、公式与图表 | Proprietary |

### 两个不属于三层框架的技能

2026 年 5 月之后新增的 `academy-guide`（用户问怎么用 Claude 时推荐对应的 Claude Academy 课程与教程）和 `discernment-nudge`（在实质性回答后自动追加两三个追问，帮用户核查关键事实、审视推理）面向 Claude.ai 的对话体验本身，不落在「方法论 / 品质控制 / 文件格式」任何一层。它们各自是 marketplace 里的独立插件，安装时单独勾选。

---

## 七、安装与使用

### 在 Claude Code 中安装

先把仓库注册为 Plugin 市场：

```bash
/plugin marketplace add anthropics/skills
```

然后两种装法任选：交互式走 `Browse and install plugins` → 选 `anthropic-agent-skills` → 挑 `document-skills` 或 `example-skills` → Install；或者直接装：

```bash
/plugin install document-skills@anthropic-agent-skills
/plugin install example-skills@anthropic-agent-skills
```

marketplace 里现在是 5 个插件：`document-skills`（四个文档技能）、`example-skills`（12 个示例技能）、独立成插件的 `claude-api`，以及新增的 `academy-guide` 和 `discernment-nudge`。

安装后，直接在对话中提及技能即可触发，例如：

> 「Use the PDF skill to extract form fields from `contract.pdf`」

### 在 Claude.ai 中使用

付费用户可直接使用仓库中所有示例技能。上传自定义技能参考官方文档中的[使用指南](https://support.claude.com/en/articles/12512180-use-skills-in-claude#h_a4222fa77b)。

### 通过 API 上传自定义技能

参考 [Skills API Quickstart](https://platform.claude.com/docs/en/api/skills-guide#creating-a-skill)。

### 用之前知道的边界

README 的 Disclaimer 写得清楚：这些技能**仅供演示和教学**。同样的能力在 Claude 产品里的实际实现和行为，可能与仓库里看到的不一样——它们示范的是模式和可能性，依赖它们做关键任务前先在自己的环境里充分测试。另外，仓库把值得推荐的伙伴技能（如 Notion 的官方技能集）单独列在 Partner Skills 一节，找特定软件的技能时值得先去那里看一眼。

---

## FAQ

**Q1：四个文档技能为什么用 Proprietary 许可证，其他技能用 Apache 2.0？**

这四个技能直接支撑 Claude 的付费文件能力——PDF 表单提取、DOCX 修订追踪、PPTX 生成和 XLSX 公式引擎都是 Claude 区别于其他模型的核心交付物。开源代码让开发者能看到实现细节（比如 .docx 怎么用 ZIP + XML 构建），但保留商业使用限制。仓库里其他技能（MCP Builder、Frontend Design 等）基本都是 Apache 2.0，作为生态基础设施存在，不直接绑定付费功能；例外是 `doc-coauthoring`，它的 SKILL.md 没有 license 字段、目录里也没有 LICENSE.txt，用之前许可证状态需要自行确认。

实际影响：你可以研究四个文档技能的内部实现，但如果你要做商业产品，最好自己实现文件读写逻辑，或者用开源替代方案（如 `python-docx` + `python-pptx` + `openpyxl` 自己封装一套）。

**Q2：Frontend Design 的设计约束会不会让生成结果走向另一个极端？**

不会走向「为极端而极端」。技能要求的是有主见的选择：简报明确指定了视觉方向就照办，留白的轴上不花在默认值上；大胆集中花在一处，其余保持安静。它的靶心是「默认而非选择」的生成物，不是某种特定风格。如果你要的是稳妥的商务风，直接在 prompt 里写明——简报的原话优先于技能的一切默认倾向，这是文档自己定下的规则。

**Q3：Skill Creator 的渐进式披露三层怎么控制 token 成本？**

L1（name + description，约 100 词）始终在上下文中——这是技能被触发的判断依据。L2（完整 SKILL.md，理想 500 行以内）只在技能激活时加载。L3（脚本 / 模板 / 参考文件）在 Agent 执行到具体步骤时才按需读取，脚本甚至可以不读入上下文直接执行。

举个例子：装满 19 个技能，上下文里常驻的也只有 19 × ~100 词 ≈ 1900 词的 L1 描述。只有当你说「用 PDF 技能提取表单字段」时，PDF 技能的 L2 正文和 `fill_fillable_fields.py`（L3）才会加载。三层设计确保技能再多，上下文窗口也不会被撑满。

Skill Creator 的关键设计决策落在 L1 的 ~100 词怎么写得让触发准确率最高，详细程度反在其次——漏触发和误触发都浪费 token。

---

## 自测

1. 打开 MCP Builder 的指导文档，挑一个你日常用的工具（GitHub、Jira 或 Notion），用四阶段流程走一遍 MCP 服务器开发。记录一下哪一阶段最花时间——大概率是 Phase 1 的 API 端点调研，因为你要同时考虑覆盖度和工作流封装；别忘了最后还有 Phase 4 的评估问题要写。
2. 找一个你最近用 AI 生成的界面，对照 Frontend Design 的五组特征清单检查：是不是奶油底配陶土橙？是不是 SaaS 卡片套装？有没有全大写眉题加中点连接的 chrome？如果中了招，按「先出设计计划、对照简报自查」的流程重做一版，看看出来的效果能不能让你一眼认出「这不是 AI 默认审美」。
3. 用 DOCX 技能创建一个带修订追踪的 Word 文档。你不需要手动编辑 XML——Agent 会处理解包和重打包。分别试试 `accept_changes.py` 和 `pandoc --track-changes=accept` 接受「整段删除」型修订，观察文档尾部有没有留下空段落——技能文档承认这是两者的已知边界。
4. 用 Skill Creator 的流程写一个你自己的技能。测试评估环节最容易被跳过——你的测试 prompt 覆盖了正例、负例和边界条件吗？跑完测试后用自带的 skill description improver（`scripts/improve_description.py`）优化触发准确率。如果你发现 description 写得越长准确率反而越低，说明你在 L1 里塞了实现细节，该精简了。

---

## 采用路线图

19 个技能不需要全部学。按你当前所处的阶段，建议这样入手：

**如果你刚接触 Agent Skills**：从 `claude-api` 和 `skill-creator` 开始。先搞清楚 Claude API 的调用模式，再用 Skill Creator 把一个你重复过 3 次以上的工作流打包成技能。这两个技能是方法论层的基础，其他技能都是在这个基础上扩出来的。

**如果你在做内部工具**：`mcp-builder` + `docx` / `xlsx`。先给团队的数据源写 MCP 服务器（数据库、项目管理工具、文档系统），再用文档技能把数据变成可分发文件。这条链路最常见的使用场景就是周报生成、数据导出、合同填充。

**如果你在做对外产品**：`frontend-design` + `canvas-design` + `web-artifacts-builder`。在 UI 和品牌物料上跟 AI 默认风格拉开距离，交互原型用 web-artifacts-builder 直接搭成多组件的 claude.ai artifact。这一步的投入产出比很高——同样的功能，界面不撞脸的用户留存率和品牌记忆度完全不一样。

**如果你在做文档密集型工作**：四个文档技能（`docx`、`pdf`、`pptx`、`xlsx`）+ `doc-coauthoring`。注意许可证——四个文档技能是 Proprietary 的，如果是商业产品，建议自己封装文件读写逻辑；`doc-coauthoring` 的许可证未标注，同样先确认再用。

**你时间有限**：只盯 `skill-creator`。它能帮你把其他工具（不管是 Anthropic 技能还是你自建的）组装成一条可复用链路——这就是第五节的周报例子想说明的模式。

这些路径对应的时间投入大致是：`claude-api` + `skill-creator` 一两周见效，`mcp-builder` + 文档技能用于内部工具需要两到四周，对外产品的设计技能组合则要尽量早开始，因为界面的累积迭代比一次性返工更省事。

---

## 相关资源

- [anthropics/skills](https://github.com/anthropics/skills)
- [Agent Skills 规范](https://agentskills.io)
- [Equipping Agents for the Real World with Agent Skills](https://anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Skill Creator 开发框架完全指南](/posts/tech/skill-creator-anthropic-skill-authoring-guide/)
- [Agent Skills 开放规范完全指南](/posts/tech/agent-skills-ai-agent-open-specification-guide/)

---

## 资料口径说明

1. **来源与口径**：本文以 [anthropics/skills](https://github.com/anthropics/skills) 仓库的 README、`.claude-plugin/marketplace.json`、各技能 SKILL.md 及其参考文件为准，技术细节以 2026-09-27 的主干为口径核对；Stars、Forks 为 GitHub API 当日读数，会随时间变化。
2. **路径说明**：仓库分三部分——`skills/`（19 个技能示例）、`spec/`（Agent Skills 规范文档）、`template/`（新建技能的模板）。文中讨论的技能均在 `skills/` 下。
3. **许可证口径**：仓库本身没有统一 LICENSE 文件。各技能许可证以技能目录内 LICENSE.txt 为准：绝大多数为 Apache 2.0，`docx`/`pdf`/`pptx`/`xlsx` 四个为 Proprietary，`doc-coauthoring` 未声明许可证。
4. **示例数据**：第五节周报例子中的工具名、字段映射为说明性示例，非真实业务数字。
5. **功能边界**：README 明示这些技能仅供演示和教学，Claude 产品内的实际实现可能与之不同；Anthropic 可能在不通知的情况下调整技能内容、增删技能或插件。
6. **适用场景**：文中的采用路径和建议基于官方文档与常见开发实践，你的团队需要按实际情况调整。

---

