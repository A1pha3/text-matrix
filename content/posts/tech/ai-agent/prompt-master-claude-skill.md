---
title: "Prompt Master：把提示词从「凭感觉写」变成可复查的流程"
date: "2026-03-29T00:05:00+08:00"
lastmod: "2026-09-27T00:00:00+08:00"
slug: "prompt-master-claude-skill"
github_repo: "nidhinjs/prompt-master"
source_key: "gh:nidhinjs/prompt-master"
aliases:
  - /posts/tech/prompt-master-claude-skill/
description: "Prompt Master 是一个 Claude Skill，把模糊需求变成可复制的提示词：八步管道、37 个工具档案、5 大安全技术、37 种浪费模式与记忆块。本文拆解它解决的是哪一类浪费、如何对抗模型迭代与注意力衰减，并给出该不该用的边界判断。数据口径 v1.8.0（2026-09-23 复核）。"
draft: false
categories: ["技术笔记"]
tags: ["提示词工程", "Claude", "AI 工具"]
---

## 它解决的是哪一类浪费

Prompt Master 是一个 Claude Skill，把一句模糊的需求变成可以直接粘贴的提示词。README 对它的定位是「零 Token（词元）浪费、零 credits 浪费」。这句话容易读成营销口号，但背后是一个可量化的循环：

```text
写模糊提示词 → 得到错误输出 → 重新提问 → 接近了 → 再问一次 → 第 4 次才拿到想要的结果
```

每次重试都是一次 API（应用程序接口）调用。一天 50 条提示词，浪费的是真金白银，也是把本应一次到位的事拖成四轮对话的时间。

多数提示词生成器在做加法，把你的需求扩写成更长的提示词。Prompt Master 反着做，README 里的判断是：

> The best prompt is not the longest. It's the one where every word is load-bearing.
> 最好的提示词不是最长的，而是每个词都承重的那个。

「每个词都承重」不是文采，是产出物的检查标准：成品提示词里每一个词都要能指出它存在的原因。

项目 2026 年 3 月 11 日创建，本文复核时点（2026-09-23）13.5k 星、1,569 复刻、7 位贡献者，MIT 协议，当前版本 v1.8.0。不到七个月涨到这个量级，提示词浪费是几乎所有 AI 用户的日常痛点。

它支持 37 个工具档案（README 自称 30+），覆盖通用 LLM（大语言模型）、编码智能体与 IDE（集成开发环境）、全栈生成器、自主智能体、搜索、图像生成、3D、视频生成、语音合成、自动化十类。未列出的工具走 Universal Fingerprint（通用指纹）机制，用 4 个问题摸清陌生系统的脾气，照样能写出合格提示词。完整名单：

| 类别 | 工具 |
|------|------|
| 通用 LLM | Claude 5 系列（Fable 5 / Opus 5 / Sonnet 5）、ChatGPT / GPT-5.6（Sol / Terra / Luna）、Grok 4.6、Gemini 2.x / 3 Pro、o3 / o4-mini、DeepSeek-R1、MiniMax M3 / M2.7、Qwen 2.5 / Qwen3、Llama / Mistral 等本地模型、Ollama |
| 编码智能体与 IDE | Claude Code、Codex、Cursor / Windsurf、Cline、GitHub Copilot、Antigravity |
| 全栈生成器 | Bolt / v0 / Lovable、Figma Make、Google Stitch |
| 自主智能体 | Devin / SWE-agent、Manus、OpenAI Computer Use、Perplexity Computer、OpenClaw |
| 搜索 | Perplexity / SearchGPT |
| 图像生成 | Midjourney、DALL-E 3、Stable Diffusion、SeeDream、ComfyUI |
| 3D | Meshy / Tripo / Rodin、BlenderGPT、Unity AI |
| 视频生成 | Sora / Runway、LTX / Dream Machine / Kling |
| 语音合成 | ElevenLabs |
| 自动化 | Zapier / Make / n8n |

档案不是工具名单，每个工具都编码了自己的路由规则：o3 / o4-mini 只接受短指令、绝不加 CoT（思维链），它们内部思考；Midjourney 用逗号分隔描述词而不用散文；Stable Diffusion 强制负向提示词；Claude Code 必须带停止条件和文件范围锁。工具之间的差异被翻译成了具体的生成规则。

## 技能本体：一份 SKILL.md 加两个参考文件

Prompt Master 不是一个应用，是三份文件：`SKILL.md` 承载执行逻辑，`references/patterns.md` 存 37 种浪费模式，`references/templates.md` 存模板。装进 Claude 之后，你说需求，它产出可复制的成品提示词。

`SKILL.md` 的组织方式和它生成的提示词遵守同一条原则，文件分三个区：

- PRIMACY ZONE（身份、硬规则、输出格式）放在最前
- MIDDLE ZONE（执行逻辑、工具路由、诊断清单）居中
- RECENCY ZONE（交付前验证、成功标准）收尾

关键内容放在前 30% 的位置，对抗目标模型的注意力衰减。它写提示词时要求记忆块也放在前 30%，用的是同一套逻辑。

## 八步管道：从需求到成品

README 定义的执行流程：

| 步骤 | 说明 |
|------|------|
| 1. 工具检测 | 识别目标 AI 系统，静默路由到正确方法 |
| 2. 意图提取 | 提取 9 个维度：任务、目标工具、输出格式、约束、输入、上下文、受众、成功标准、示例 |
| 3. 澄清问题 | 关键信息缺失时最多问 3 个，绝不超量 |
| 4. 框架路由 | 自动选择正确的提示词架构，用户永远看不到框架名 |
| 5. 安全技术 | 只使用效果可靠、有界的技术 |
| 6. 模型时效核查 | 涉及「最新模型」时，对照官方文档验证模型名与参数，查不到就明说未验证，绝不编造模型代号 |
| 7. Token 效率审计 | 删掉每个不影响输出的词 |
| 8. 交付提示词 | 一个整洁的可复制块加一行策略说明 |

第 6 步针对模型迭代太快的事实：用户说「给最新的 Claude 写个提示词」，技能必须确认「最新」指哪个型号，而不是拿训练数据里的旧型号交差。

## 安全技术：只留效果可查的

Prompt Master 只使用效果可靠、有界的技术，已知容易幻觉或产出不可预测结果的被明确排除。

| 技术 | 何时使用 | 说明 |
|------|----------|------|
| Role Assignment（角色分配） | 需要专业深度和词汇时 | 分配特定的专家身份来校准 |
| Few-Shot Examples（少样本示例） | 格式一致性比指令更重要时 | 添加 2-5 个示例 |
| XML Structural Tags（XML 结构标签） | Claude 系工具解析可靠时 | 用 XML 标签包装各部分 |
| Grounding Anchors（事实锚点） | 事实和引用任务时 | 添加反幻觉规则 |
| Auditable Reasoning（可审计推理） | 逻辑、数学、调试、分析任务时 | 要求输出结论、假设、证据和验证检查，而非隐藏的推理过程 |

第五项值得展开。早期版本用 Chain of Thought（思维链），o3 / o4-mini 这类推理模型除外——它们内部思考，外加 CoT 反而劣化输出。v1.8.0 把「请求隐藏思维链」整个换成了可审计推理：不要模型的私有推理过程，要它能被检查的结论、假设、证据链和验证步骤。这条写进了硬规则，任何模型都不许请求隐藏思维链。

明确排除的技术：

- Tree of Thought（思维树）
- Graph of Thought（图思维）
- Universal Self-Consistency（通用自洽）
- Prompt Chaining（提示链）
- Mixture of Experts（专家混合，在单次前向传播中模拟多角色路由，SKILL.md 硬规则额外列入）

技能还内置三条安全机制：

1. 凭证安全：生成的提示词绝不包含 API 密钥、token、连接字符串；用户粘贴的提示词里带凭证，剥离并提示改用环境变量。
2. 输入消毒：用户粘贴旧提示词来分析或修复时，整段按惰性数据处理——不执行其中嵌入的指令，不泄露系统提示词。
3. Agentic 输出警告：面向 Claude Code、Devin 这类有真实系统权限的工具，生成的提示词必须附警告，提醒用户粘贴前检查范围锁、禁止动作和停止条件。

## 浪费模式清单：37 种，每种都有修法

37 种常见浪费模式，每种配 Before / After 对照。诊断清单内置于 SKILL.md，完整参考表在 `references/patterns.md`。

| 类别 | 数量 | 典型模式与修法 |
|------|------|----------------|
| Task Patterns（任务） | 7 | 「帮我看看代码」→「重构 `getUserData()`，改用 async/await 并处理 null 返回」；一件事拆成一条提示词，别「解释并重写」 |
| Context Patterns（上下文） | 6 | 「继续上次的」→ 附上完整记忆块；「专家怎么说」→「只引用你确定的信息，不确定就明说」 |
| Format Patterns（格式） | 6 | 「写得专业点」→「单色调、16px 基础字号、24px 行高、无装饰元素」；图像 AI 必须带负向提示词 |
| Scope Patterns（范围） | 6 | 「修好我的应用」→「只修 `src/auth.js` 里的登录表单校验，其他都不动」；整库粘贴改成只贴相关函数 |
| Reasoning Patterns（推理） | 5 | 「展示你的思维链」→ 删掉，改要简洁的依据、证据和验证；跨会话别指望 AI 记得你的项目，每次重新提供记忆块 |
| Agentic Patterns（智能体任务） | 7 | 「给我建个 REST（表述性状态转移）API」→ 写明起始状态和目标状态；静默 agent 加「每步输出完成了什么」；长会话上下文腐坏该开新会话就开 |

Agentic 类在 v1.6.0 从 5 条扩到 7 条，新增的两条来自真实痛点：模糊的第一轮指令（「修一下认证 bug」却没有范围、文件和标准），以及长会话的上下文腐坏——反复纠错会让过期的假设留在上下文里，越聊越歪。

## 记忆块：把「AI 应该记得」换成「每次带上」

长会话中 AI 经常忘记已定下的决定，导致重复劳动和重新提问。README 的判断很直接：大多数浪费的重试，都来自 AI 忘了你已经定下的选择。

Memory Block System 会在新提示词前附上此前会话的关键决策：

```markdown
## Memory (Carry Forward from Previous Context)
- Stack: React 18 + TypeScript + Supabase
- Auth uses JWT stored in httpOnly cookies, not localStorage
- Component naming convention: PascalCase, no default exports
- Design system: Tailwind only, no custom CSS files
- Architecture: no Redux, context API only
```

SKILL.md 对位置有明确要求：放在提示词前 30% 的区域内，让它在注意力衰减中活下来。记忆块只承载四类信息：既定的技术栈与工具选择、已锁定的架构决策、此前轮次的约束、试过且失败过的方案。

这套机制的技术含量不高，作用是把「AI 应该记得」这个幻觉，换成「每次明确携带」的纪律。它是长会话里最大的单项修复。

## 一次流转：雨夜武士怎么变成 Midjourney 母语

用户输入一句：

```text
Write me a midjourney prompt for a realistic samurai standing in the rain at night
```

产出：

```text
lone samurai standing in heavy rain at night, traditional armor,
neon reflections on wet cobblestone street, cinematic lighting,
dramatic shadows, fog, ultra detailed, photorealistic,
shallow depth of field --ar 16:9 --v 6 --style raw

negative: blurry, low quality, watermark, cartoon, anime, extra limbs
```

附带一行策略说明：

| 字段 | 值 |
|------|------|
| Target | Midjourney |
| Framework | Visual Descriptor |
| Tokens | Light (~60) |
| Strategy | 逗号分隔描述词而非散文；光影氛围前置；画幅与版本锁定；负向提示词防止风格漂移 |

输入只有一句「雨夜写实武士」，产出是 Midjourney 的母语：逗号分隔的描述词序列、参数后置、负向提示词兜底，没有一句废话。

再看代码任务。用户要求一个「感觉完全像 Notion」的业务仪表盘落地页：

```text
Build a claude code prompt for a landing page for a business dashboard
that looks and feels exactly like notion - smooth animations, clean ui
```

产出的提示词约 380 tokens，包含：

- 精确的像素规格：背景 `#ffffff`，主文字 `#1a1a1a`，辅助文字 `#6b7280`，边框 `#e5e7eb`，主色 `#000000`，Inter 字体四档字重
- 按顺序排列的 8 个具体版块（导航栏、Hero、Logo 栏、特性、工作原理、定价、CTA、页脚），每个带布局细节
- 动画规格：IntersectionObserver，阈值 0.15，500ms ease-out，特性卡 100ms 逐个延迟
- 约束条件：单文件嵌入 CSS/JS，无依赖，仅 Google Fonts 的 Inter 字体
- 完成标准：375px 移动端与 1440px 桌面端双断点正确渲染，所有滚动动画无布局偏移，打开零控制台错误

这条提示词的策略说明点破了方法论落点：把「Notion 那种感觉」这类模糊审美线索全部翻译成精确的十六进制色值和像素规格。Claude Code 不允许猜测。模型不会读心，「像 Notion 一样干净」不是需求，`#ffffff` 背景加 6px 圆角才是。

## 模板路由：13 个自动选择

| 模板 | 适用场景 |
|------|----------|
| RTF（Role / Task / Format） | 快速单发任务 |
| CO-STAR（Context / Objective / Style / Tone / Audience / Response） | 专业文档、商业写作 |
| RISEN（Role / Instructions / Steps / End Goal / Narrowing） | 复杂多步项目 |
| CRISPE（Capacity / Role / Insight / Statement / Personality / Experiment） | 创意工作、品牌声音 |
| Auditable Reasoning | 可检查的数学、逻辑、调试与分析 |
| Few-Shot | 一致的结构化输出、模式复制 |
| File-Scope | Cursor / Windsurf / Copilot 等代码编辑 AI |
| ReAct + Stop Conditions | Claude Code / Devin / AutoGPT 等自主智能体 |
| Visual Descriptor | Midjourney / DALL-E / Stable Diffusion / Sora 生成任务 |
| Reference Image Editing | 参考图编辑，自动检测「编辑」与「生成」 |
| ComfyUI | 节点式图像工作流，正向/负向提示词分离 |
| Prompt Decompiler | 拆解、适配、简化、拆分已有提示词 |
| Current Claude Task Brief | 当前 Claude 模型上的复杂多步或 Agentic 任务 |

模板体系里既有 RTF、CO-STAR 这类社区成熟的提示词框架，也有 File-Scope、ReAct + Stop Conditions 这种针对特定工具形态的原生设计。前者负责通用任务，后者负责「写错就烧钱」的智能体场景。Prompt Master 静默路由，用户永远看不到框架名。

## 版本轨迹：从加法到减法

| 版本 | 更新内容 |
|------|----------|
| 1.8.0 | 当前模型全面刷新：Claude Fable 5 / Opus 5 / Sonnet 5、GPT-5.6 Sol / Terra / Luna、Codex、Grok 4.6 路由；隐藏思维链请求全部替换为可审计推理；新增模型时效核查步骤 |
| 1.7.0 | Opus 4.8 兼容：Claude 4.x 路由版本感知，4.6 / 4.7 / 4.8 建议通用化，新增 Opus 4.8（当时默认）档案 |
| 1.6.0 | Opus 4.7 更新：新增 Template M（Claude 任务简报），路由适配 adaptive thinking 与 xhigh effort，浪费模式扩至 37 条 |
| 1.5.0 | 新增 Agentic AI 与 3D Model AI 路由，移除 token 估算输出，添加指令层与文案占位符 |
| 1.4.0 | 参考图编辑检测、ComfyUI 支持、Prompt Decompiler 模式，references 新增 3 个模板 |
| 1.3.0 | 围绕 PAC2026 位置结构（30/55/15）重建，静默路由替代用户自选框架，引入 References 文件夹 |
| 1.2.0 | 为注意力架构重构，移除易幻觉技术（ToT / GoT / USC / 提示链），模板与模式移入 references |
| 1.1.0 | 扩展工具覆盖，添加记忆块系统，35 种浪费模式 |
| 1.0.0 | 初始发布 |

演化方向有三条：从通用提示词框架走向按工具形态深度特化；从「更长更全」走向注意力架构和 Token 效率；跟随模型迭代持续刷新路由。1.6 到 1.8 的三次更新全部集中在 2026 年 4 月底到 8 月中，追的是 Claude、OpenAI、xAI 的模型发版节奏。装上它不等于一劳永逸——模型换代时，路由档案要靠新版本跟上。

## 装与用

浏览器版（推荐）：

```text
1. 下载仓库 ZIP
2. 前往 claude.ai → 侧边栏 → Customize → Skills → Upload a Skill
```

Claude Code 命令行备选：

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/nidhinjs/prompt-master.git ~/.claude/skills/prompt-master
```

README 给 CLI（命令行工具）方式标注了「Not Suggested」，没有解释原因。技能本体只是一个 SKILL.md 加两个 references 文件，两种装法的内容完全一致。

安装后自然语言触发即可，无需记命令：

```text
Write me a prompt for Cursor to refactor my auth module
```

```text
I need a prompt for Claude Code to build a REST API — ask me what you need to know
```

```text
Here's a bad prompt I wrote for GPT-4o, fix it: [paste prompt]
```

```text
Generate a Midjourney prompt for a cyberpunk city at night
```

```text
I have a reference image — help me write a prompt to edit just the head angle
```

```text
Break this prompt down and adapt it for Stable Diffusion
```

也可以显式调用：

```text
/prompt-master I want to ask Claude Code to build a todo app with React and Supabase
```

六种触发模式对应六类任务：从零生成、带澄清的生成、修复已有提示词、图像生成、参考图编辑、跨工具改写。激活条件设计得很窄——只在用户明确要求写、修、改、适配提示词时触发，日常对话和普通编码任务不会误激活。

## 该不该用

适合立刻装上的：每天在多个 AI 工具之间切换的人。上午让 Claude Code 改代码、下午用 Midjourney 出图、晚上跑 Devin，每个工具的提示词语法都不一样，工具档案路由正是为这种用法设计的。经常写智能体提示词的人也能直接抄纪律：停止条件、范围锁、人审触发器这套写法能避开大部分烧钱坑。

可以等等的：只用单一工具且任务简单的用户，Claude 自身的提示词能力已覆盖大部分日常需求。想让 AI 替自己想清楚「到底要什么」的人也不必指望它——9 维度意图提取补全的是你没说出口的细节，不能替代你对任务本身的判断。

边界要清楚：它优化的是单个提示词的质量，不是提示词的存储、复用和团队共享，那是另一类工具的事。

## 参考来源与口径说明

- 核对时点：2026-09-23；版本锚点：v1.8.0（`SKILL.md` frontmatter `version: 1.8.0`，仓库最后推送 2026-08-24）。
- GitHub 数据（13,532 stars / 1,569 forks / 7 contributors / MIT）取自 GitHub API 当日快照。
- 工作机制、工具档案、模板清单、浪费模式均对照仓库 `README.md`、`SKILL.md`、`references/templates.md`、`references/patterns.md` 逐一核实；本文发布时原文数据口径为 v1.5.0 时期的 2.8k stars、7 步管道、35 种模式、12 个模板，现按 v1.8.0 全面更新。
- 口径差异说明：README 的 How It Works 一节写 9 维度中含 "memory"，而 SKILL.md 的意图提取表中对应维度实为 "Target tool"（目标工具），本文以 SKILL.md（实际执行逻辑）为准。
- 明确排除的技术清单：README 列 4 项（ToT / GoT / USC / 提示链），SKILL.md 硬规则额外列入 Mixture of Experts，正文按 5 项转述。
- 版本历史译自 README Version History 节；1.6.0 / 1.7.0 / 1.8.0 对应的提交日期分别为 2026-04-26、2026-06-04、2026-08-15（commits API）。
- 两处使用示例的提示词与元信息逐字取自 README 的 Full Example #1 / #2。
- 项目地址：<https://github.com/nidhinjs/prompt-master>；Star 历史：<https://star-history.dera.page/#nidhinjs/prompt-master&Date>
