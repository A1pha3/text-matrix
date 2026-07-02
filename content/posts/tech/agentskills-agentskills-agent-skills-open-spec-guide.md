---
title: "agentskills/agentskills 原理拆解：Agent Skills 开放规范是怎么设计的"
date: "2026-07-02T21:02:26+08:00"
lastmod: "2026-07-02T21:02:26+08:00"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Open Standard", "LLM", "Prompt Engineering"]
description: "拆解 Agent Skills 开放规范的核心设计：SKILL.md frontmatter 字段语义、渐进披露三阶段、42 个兼容客户端、参考实现 skills-ref 的取舍。"
weight: 1
author: text-matrix
---

# agentskills/agentskills 原理拆解：Agent Skills 开放规范是怎么设计的

Agent Skills 是一个开放的格式标准，由 Anthropic 起草并交给 `agentskills/agentskills` 仓库托管。它的目标很简单：让任何 AI agent 都能用同一个目录约定加载"专家技能"。Skills 不是产品、不是 SDK、也不是某个 agent 的私有配置——它是一份跨厂商可移植的能力清单。

仓库本身（按 README 与 `docs/specification.mdx` 来看）只承担三件事：定义规范、托管文档站 `agentskills.io`、提供 `skills-ref` 参考实现。`CONTRIBUTING.md` 明确写了"我们目前不维护社区 skill 目录"，也不接受大规模架构改动。这是一份设计优先于实现的开放标准。

## 核心判断

把它当成 LLM 工具链的"VS Code 扩展目录"会更容易理解：一个 skill 是一个带元数据的文件夹，agent 在启动时只看 `name` 与 `description`（≈100 tokens），匹配任务时才把完整 `SKILL.md` 读进上下文（<5000 tokens 推荐），需要时再去翻 `scripts/`、`references/`、`assets/`。这种三段式加载（progressive disclosure）是整个规范的设计核心——它决定了 frontmatter 字段为什么是 6 个而不是 30 个，也决定了为什么 `SKILL.md` 推荐 500 行以内。

## 系统地图：规范的四层结构

Agent Skills 规范一共由四个层次组成，按"必选到可选"的顺序排：

| 层次 | 位置 | 是否必选 | 角色 |
| --- | --- | --- | --- |
| 1. 元数据 | `SKILL.md` 的 YAML frontmatter | 必选（name/description），其余可选 | agent 启动时只读这一层（约 100 tokens） |
| 2. 指令正文 | `SKILL.md` 的 Markdown body | 必选（与 frontmatter 一起） | skill 激活后整段加载 |
| 3. 可选目录 | `scripts/`、`references/`、`assets/` | 可选 | 按需加载的执行代码、参考资料、静态资源 |
| 4. 验证工具 | `skills-ref` 库 | 独立工具链 | 本地校验 `SKILL.md` 字段合规 |

对应到 quickstart 里的"roll-dice"示例，目录就是：

```
my-skill/
├── SKILL.md          # 必选
├── scripts/          # 可选
├── references/       # 可选
├── assets/           # 可选
└── ...               # 任何额外内容
```

整个规范刻意保持"目录即接口"的形态：没有 JSON schema、没有中央注册表、没有任何强制元数据。它走的是文件系统约定这条最朴素的路子。

## Frontmatter 字段语义

`docs/specification.mdx` 列出了六个字段，其中 `name` 与 `description` 是必选，其余四个可选。下面逐个拆它的设计意图。

### `name`（必选，1-64 字符）

约束相当硬：

- 只能是小写字母、数字、连字符
- 不能以连字符开头或结尾
- 不能有连续连字符 `--`
- 必须匹配父目录名

为什么这么严？因为 agent 在文件系统里找 skill 时，是按目录名加载的。如果目录名和 frontmatter 里写的 `name` 不一致，agent 不知道该信谁；同时 `name` 还会出现在用户可见的"skill 列表"里，约束成小写+连字符能让它直接当 slug 用。

### `description`（必选，1-1024 字符）

这是规范里最被强调的字段。README 与 best-practices 反复讲：description 要"既说做什么也说何时用"，并且要塞进 agent 能识别的关键词。

对比一下官方给的例子：

```yaml
# 不及格
description: Helps with PDFs.
```

```yaml
# 及格
description: Extracts text and tables from PDF files, fills PDF forms, and
merges multiple PDFs. Use when working with PDF documents or when the user
mentions PDFs, forms, or document extraction.
```

"及格"版多出来的内容不是凑字数：前半句让 agent 知道 skill 的能力边界（不能处理扫描件就别指望），后半句给 agent 提供触发关键词（用户提到 PDF/forms/extraction 时应该激活）。`description` 是 progressive disclosure 里第一段（discovery）唯一会进 agent 上下文的字段，它的命中率决定了这个 skill 能不能被"看见"。

### `license`、`compatibility`、`metadata`、`allowed-tools`（可选）

四个可选字段的设计逻辑可以一句话概括："尽量不增加实现者的负担"。

- `license`：把 license 写进 frontmatter 只是顺手；具体条款可以指向 bundled 的 LICENSE 文件。
- `compatibility`：上限 500 字符，写明"这个 skill 需要 Python 3.14+ 或 docker"这类环境前提。规范明确说"大多数 skill 不需要这个字段"。
- `metadata`：任意 key-value map，给实现者留扩展位。规范建议 key 名取得独特一点，避免与未来规范字段冲突。
- `allowed-tools`：实验性字段，标注该 skill 已被授权运行的工具（`Bash(git:*) Bash(jq:*) Read`）。这是规范里唯一一处对工具调用做约束的地方，并且明示"在不同 agent 上支持度可能不一致"。

`CONTRIBUTING.md` 里那句"it is much easier to add things to a specification than to remove them"映射到字段表上，就是这四个字段目前都还挂在"可选"位置上的原因。

## 渐进披露三阶段

`docs/specification.mdx` 用一段话讲清了 agent 怎么读 skill：

1. **Discovery（启动时）**：扫描默认目录，只读每个 skill 的 `name` 与 `description`，对应 ~100 tokens 的元数据。这步完全是在 agent 启动时一次性完成的。
2. **Activation（任务匹配时）**：当用户请求匹配到某 skill 的 description，agent 把整个 `SKILL.md` 加载进上下文。规范建议 `<5000 tokens`、`<500 行`。
3. **Execution（执行时按需）**：agent 按指令正文执行；指令里如果引用 `scripts/extract.py` 或 `references/api-errors.md`，agent 才去加载这些文件。

quickstart 的"roll a d20"任务流恰好把三阶段都走了一遍：

1. 用户在 VS Code 打开 Copilot Chat 的 Agent 模式，agent 启动时扫了 `.agents/skills/` 目录，发现 `roll-dice`。
2. 用户说"Roll a d20"，agent 把请求和 `roll-dice` 的 description 做匹配——"Roll dice using a random number generator"显然命中。
3. agent 把 `SKILL.md` 的整段 body 读进上下文，按里面的指令执行 `echo $((RANDOM % 20 + 1))`。

每一步都是按需读取，没有一步把仓库全量灌进上下文。

## 文件引用规则

规范对 `SKILL.md` 里如何引用其他文件有明确要求：

- 用相对路径，从 skill 根目录算起，例如 `references/REFERENCE.md`。
- 引用深度建议只有一层（`SKILL.md` → `references/xxx.md`），不要做 `references/a.md → references/a/b.md` 这种链式引用。

为什么限制深度？因为链式引用会让 agent 在加载时多走几次 IO、还要在上下文里维护"我已读了哪些文件"的状态。一层引用让 agent 一眼看清"什么时候该读什么"。

## scripts/、references/、assets/ 的角色差异

这三个可选目录不是同质的，规范里给了相对清晰的分工：

- `scripts/`：可执行代码，agent 真的会跑它。规范建议脚本自带依赖声明、错误信息友好、处理边界情况。
- `references/`：纯文档，agent 只读不跑。规范建议按领域分文件（如 `finance.md`、`legal.md`），保持单文件聚焦。
- `assets/`：静态资源（模板、图片、查表），agent 按指令引用。

这三类边界很微妙但很重要：脚本执行有副作用（写文件、调用 API），references 是只读的扩展阅读材料，assets 是被引用而不是被解读的素材。混淆这三者会让 agent 在 progressive disclosure 时做错决策。

## 42 个兼容客户端意味着什么

`docs/snippets/clients.jsx` 列出了 42 个已经接入 Agent Skills 格式的 agent 产品（README 里说 "a large number of AI tools and agentic clients"）。从里面挑几个有代表性的：

- **Claude Code** 与 **Claude**：Anthropic 自家主力，是规范的原始实现方。
- **GitHub Copilot** 与 **VS Code**：仓库自身的 quickstart 教程就是用 VS Code Copilot 的 Agent 模式。
- **OpenAI Codex** 与 **OpenCode**：另一家主流 LLM 厂商的代码 agent。
- **Cursor**、**Amp**、**Roo Code**、**Qodo**：独立 AI 编辑器/agent 产品。
- **Junie**：JetBrains 出品，跑在 IntelliJ 平台上。
- **Gemini CLI**、**Databricks Genie Code**、**Snowflake Cortex Code**：终端/平台型 agent。
- **Letta**：带状态记忆的 agent 平台。
- **Firebender**：Android-native 编码 agent。

这些客户端分别落在 IDE、终端、平台、云端、移动端。规范能跨到这种程度，是因为它刻意把"必备字段"压到了最小（`name` + `description`），把"可选扩展"挂在了 metadata/allowed-tools 这种不破坏向后兼容的位置。任何一个客户端只要实现"读 frontmatter + 按需加载"这一对操作，就算兼容了 Skills 格式。

## 参考实现：skills-ref 库

`CONTRIBUTING.md` 写到 "We're still determining the direction for the reference library and are not accepting code contributions to it at this time"。但仓库里 `skills-ref/` 目录确实存在，并且 `docs/specification.mdx` 提到了它的用法：

```bash
skills-ref validate ./my-skill
```

这步校验做的是 frontmatter 字段合规性、命名约定、目录结构。把它当成"写完 skill 后的本地 lint"会比较合适——比提交到 CI 跑一遍再让产品报错更省时间。

## 写一个 skill 的最小闭环

把 quickstart 展开成更细的步骤，可以照着写：

```bash
mkdir -p .agents/skills/roll-dice
```

`.agents/skills/` 是 VS Code Copilot 的默认扫描路径；其他客户端扫描位置不同（仓库 README 链接的 `agentskills.io` 文档站里有各客户端的扫描路径说明）。

写 `SKILL.md`：

````markdown
---
name: roll-dice
description: Roll dice using a random number generator. Use when asked to
roll a die (d6, d20, etc.), roll dice, or generate a random dice roll.
---

To roll a die, use the following command that generates a random number from 1
to the given number of sides:

```bash
echo $((RANDOM % <sides> + 1))
```

```powershell
Get-Random -Minimum 1 -Maximum (<sides> + 1)
```

Replace `<sides>` with the number of sides on the die.
````

跑一次 `skills-ref validate .agents/skills/roll-dice`，确认 frontmatter 合法。在 agent 里说"Roll a d20"，观察 agent 是否走 shell 命令还是试图自己回答。

best-practices 里特别提示了一句："Tool-use reliability varies across models — some follow skill instructions and run commands consistently, while others may attempt to answer on their own." 所以验证步骤不是一次性的，而是要在不同模型上各跑一遍。

## 它不是什么

写到这里值得把边界划清楚：

- **不是产品**。仓库没有 release artifact，没有 CLI 提供给终端用户，没有"skill 市场"。
- **不是 SDK**。没有 Python/Node 包，不存在 `import agent_skills` 这种用法。
- **不是 agent 配置**。Skill 应该是跨 agent 可移植的；如果一个 skill 只能在某个 agent 上工作，说明它带了私有约定。
- **不是 prompt 模板**。Prompt 模板是单段文字，skill 是个目录，里面可以有脚本和参考资料。
- **不是中央注册表**。`CONTRIBUTING.md` 明示不维护社区 skill 目录，skill 放在哪里、用什么版本控制，完全由作者决定。

## 与几个相邻概念的区别

open-standards 设计中常见的混淆在这里值得一提，因为它直接决定要不要引入 Skills：

- **vs. System prompt**：系统 prompt 是单段文字，运行时占用上下文，没有"按需加载"机制。Skill 是有元数据与可选目录的文件夹，启动时只读元数据。它俩可以并存——系统 prompt 设全局基调，Skill 提供具体领域知识。
- **vs. MCP（Model Context Protocol）**：MCP 解决的是"agent 怎么调用外部工具"，重点在工具调用协议与服务发现。Skill 解决的是"agent 怎么获得领域知识"，重点在指令文本与可选脚本。一个 agent 通常同时用 MCP 与 Skills：前者负责"做事"，后者负责"知道怎么做"。
- **vs. Function calling / Tool use**：function calling 是模型能力，描述模型怎么输出结构化调用。Skill 内部可以用 function calling 来执行 scripts/，但 function calling 本身不是 Skills 的替代品。
- **vs. RAG / 向量检索**：RAG 用相似度检索把上下文塞进 prompt。Skills 是显式触发（description 匹配任务），不是相似度召回。两者可以互补——RAG 提供"事实召回"，Skills 提供"程序知识"。
- **vs. `.cursorrules` / `.github/copilot-instructions.md` 等私有配置**：这些是单文件的 agent 私有指令，没有规范化的元数据约束，也没有 progressive disclosure。Skills 的优势是格式公开、客户端兼容、字段有校验。

## `metadata` 与 `allowed-tools` 的扩展使用

按规范说法，`metadata` 是"任意 key-value map"，但 best-practices 给出的两个示例已经暗示了用法：`author` 与 `version`。这两个 key 实际承担了"作者归属"与"版本语义"，是私域扩展位最常见的填充方式。建议团队内部约定类似 `internal:team`、`internal:owner` 这样的命名空间前缀，避免与未来规范字段冲突。

`allowed-tools` 是规范里唯一触及"权限"概念的字段。`Bash(git:*) Bash(jq:*) Read` 这种写法让 skill 自我声明它需要的工具子集。规范标了"Experimental"，并且明说"支持度可能不一致"。实务上建议：宁可先不写，等目标客户端稳定支持再加——它一旦写错，skill 在某些 agent 上激活反而会被拒绝执行。

## 多 skill 组合与冲突处理

规范没有规定多 skill 同时激活时的合并策略，但 README 与 best-practices 透露出两条隐含规则：

1. **按 description 独立激活**：每个 skill 的激活判断只看自己的 description，互相不感知。如果两个 skill 的 description 重叠，agent 可能会同时激活两者；这时 `SKILL.md` 的指令要足够清晰，避免歧义。
2. **共享 references 文件要谨慎**：如果两个 skill 都引用 `references/api-errors.md`，修改这个文件会影响两边。设计上更建议把 references 复制到各自的 skill 目录里，或者放在公共位置并在 description 里注明"参见 common skill X"。

`CONTRIBUTING.md` 那句"Skills scoped too narrowly force multiple skills to load for a single task, risking overhead and conflicting instructions"也是这条原则的另一面：粒度太细会引发冲突与加载开销，粒度太粗又难以精准激活。判断标准参考 best-practices："deciding what a skill should cover is like deciding what a function should do: you want it to encapsulate a coherent unit of work that composes well with other skills"。

## description 的优化是一个独立课题

仓库的 `docs/skill-creation/optimizing-descriptions.mdx` 把 description 单独拎出来讲。几个核心点：

- description 要把"做什么"和"何时用"写在一句话里。
- 在 description 里塞进用户最可能提到的关键词（库名、文件格式、错误信息、动词），agent 才能在有限上下文里命中。
- 描述太长（接近 1024 上限）会让 discovery 阶段读多个 skill 时挤占上下文；太短又容易被忽略。
- 测试方法：跑一组典型用户请求，看每个 skill 的激活率与误激活率，根据 trace 调整 description。

best-practices 里给了一个细节："Read agent execution traces, not just final outputs"——如果 agent 走了不必要的步骤、或者根本没激活 skill，问题大概率出在 description，不在 body。

## 仓库结构与文档站的运作方式

仓库本身并不大，主要由四块组成：

- `docs/`：Mintlify 文档站源文件，部署到 `agentskills.io`。`docs.json` 里的 `navigation.pages` 数组决定侧边栏顺序。
- `skills-ref/`：参考实现库，提供 `validate` 子命令做 frontmatter 校验。具体支持哪些命令需要看当前实现（`CONTRIBUTING.md` 明说"还在定方向，暂不接受代码贡献"）。
- `package.json`：仓库根有一份，主要是文档站依赖。
- `.claude/`：仓库自身用 Claude 维护的元数据。

仓库的 npm 命令入口是 `npm run dev`（`docs/CLAUDE.md` 写了），本地预览 `http://localhost:3000`。

## 适用边界与采用顺序

按当前规范的状态，建议这样判断要不要采用：

- **个人 / 小团队**：从 quickstart 起步，把 1-2 个真正高频的领域知识（团队代码规范、内部 API 文档）做成 skill，比堆 20 个空架子有用。
- **企业内部**：用 metadata 字段加公司/团队前缀，避免 skill 跨部门重名。借助 references/ 目录把内部 runbook 装进去。
- **开源项目作者**：把"如何贡献代码"的规则做成 skill，比塞进 README 的"贡献指南"更可能被 agent 真的读完并遵守。
- **平台方 / agent 提供方**：接入 Skills 格式的边际成本低（实现 discovery + activation 两个阶段即可），但要先在文档里说清默认扫描目录、允许的 allowed-tools 子集。

最后一点：所有 `CONTRIBUTING.md` 没明示的设计变更（例如增加强制字段、改 description 字符上限），都不要指望被快速接受。规范的高门槛是有意为之——这是它能成为"开放标准"而不是"另一个配置 DSL"的前提。