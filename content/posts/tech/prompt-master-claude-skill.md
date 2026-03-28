---
title: "Prompt Master：2.8k Stars 让提示词零浪费的 Claude Skill"
date: 2026-03-29T00:05:00+08:00
slug: "prompt-master-claude-skill"
description: "深度解读 Prompt Master：2.8k Stars 的提示词优化工具，7步生成精准提示词，30+ AI工具兼容，5大安全技术，35种浪费模式检测，让每个Token都不浪费。"
draft: false
categories: ["技术笔记"]
tags: ["Prompt Master", "提示词工程", "Claude", "AI工具", "效率优化"]
---

# Prompt Master：2.8k Stars 让提示词零浪费的 Claude Skill

> **目标读者**：使用 AI 工具（Claude/ChatGPT/Midjourney 等）的所有用户
> **核心问题**：如何写出一个精准的提示词，一次到位，不浪费 Token 和 credits？
> **难度**：⭐⭐（效率工具）
> **来源**：GitHub nidhinjs/prompt-master，2026-03-28

---

## 一、项目概览

### 1.1 为什么这个项目值得关注

[Prompt Master](https://github.com/nidhinjs/prompt-master) 是一个 **Claude Skill**，能够为任何 AI 工具写出精准的提示词，**零 Token 浪费，零 credits 浪费**。

**核心数据：**

| 指标 | 数值 |
|------|------|
| GitHub Stars | **2.8k** |
| Forks | 249 |
| Contributors | 3 |
| License | MIT |
| 最新版本 | v1.5.0（2026-03-24） |

**核心定位：**

> A Claude skill that writes the accurate prompts for any AI tool. Zero tokens or credits wasted. Full context and memory retention. No re-prompting your way to an answer you should have gotten on attempt one.

### 1.2 支持的 AI 工具

**30+ 工具全覆盖：**

| 类别 | 工具 |
|------|------|
| **LLM 对话** | Claude, ChatGPT, Gemini, o1/o3, MiniMax, Claude Code, GitHub Copilot, Windsurf, Bolt |
| **代码助手** | Cursor, v0, Lovable, Devin |
| **搜索引擎** | Perplexity |
| **图像生成** | Midjourney, DALL-E, Stable Diffusion, ComfyUI |
| **视频生成** | Sora, Runway |
| **语音合成** | ElevenLabs |
| **自动化** | Zapier, Make |

### 1.3 它解决的问题

**传统方式（浪费）：**

```
写模糊提示词 → 得到错误输出 → 重新提问 → 接近了一点 → 再提问 → 第4次才得到想要的结果
```

**这就是 3 次浪费的 API 调用。每天 50 条提示词 = 真正的钱和时间浪费。**

**核心理念：**

> "The best prompt is not the longest. It's the one where every word is load-bearing."
> 最好的提示词不是最长的，而是**每个词都承载意义的**。

---

## 二、工作原理

### 2.1 七步精准提示词生成管道

```
用户输入 → 工具检测 → 意图提取 → 澄清问题 → 框架路由 → 安全技术 → Token审计 → 交付提示词
```

| 步骤 | 说明 |
|------|------|
| **1. 工具检测** | 自动识别目标 AI 系统，静默路由到正确方法 |
| **2. 意图提取** | 从 9 个维度提取：任务、输入、输出、约束、上下文、受众、记忆、成功标准、示例 |
| **3. 澄清问题** | 最多 3 个关键问题（信息缺失时） |
| **4. 框架路由** | 自动选择正确提示词架构（PAC2026，Prompt Architecture Context 2026，用户不可见） |
| **5. 安全技术** | 仅使用可靠、有界效果的技术 |
| **6. Token 效率审计** | 删除每个不影响输出的词 |
| **7. 交付提示词** | 一个整洁的可复制块 + 一行策略说明 |

### 2.2 五大安全技术

| 技术 | 何时使用 | 说明 |
|------|----------|------|
| **Role Assignment** | 需要专业深度和词汇时 | 分配特定专家身份来校准 |
| **Few-Shot Examples** | 格式一致性比指令更重要时 | 添加 2-5 个示例 |
| **XML Structural Tags** | Claude 系列工具解析可靠时 | 用 XML 包装各部分 |
| **Grounding Anchors** | 事实和引用任务时 | 添加反幻觉规则 |
| **Chain of Thought** | 逻辑任务时（不用于 o1/o3） | 强制逐步推理 |

**明确排除的技术（不可靠）：**

- Tree of Thought（思维树）
- Graph of Thought（图思维）
- Universal Self-Consistency（通用自洽）
- Prompt Chaining（提示链）

### 2.3 35 种浪费模式检测

**六大类别：**

| 类别 | 数量 | 示例 |
|------|------|------|
| **Task Patterns** | 7 | 模糊任务描述 |
| **Context Patterns** | 6 | 缺少上下文 |
| **Format Patterns** | 6 | 格式不一致 |
| **Scope Patterns** | 6 | 范围不明确 |
| **Reasoning Patterns** | 5 | 推理链缺失 |
| **Agentic Patterns** | 5 | Agent 能力未定义 |

---

## 三、使用示例

### 3.1 图像生成提示词

**用户输入：**

```
Write me a midjourney prompt for a realistic samurai standing in the rain at night
```

**生成的提示词：**

```
lone samurai standing in heavy rain at night, traditional armor, neon reflections on wet cobblestone street, cinematic lighting, dramatic shadows, fog, ultra detailed, photorealistic, shallow depth of field --ar 16:9 --v 6 --style raw negative: blurry, low quality, watermark, cartoon, anime, extra limbs
```

**Prompt Master 附加信息：**

| 字段 | 值 |
|------|------|
| 🎯 Target | Midjourney |
| ⚡ Framework | Visual Descriptor |
| 💰 Tokens | Light (~60) |
| 💡 Strategy | Comma-separated descriptors over prose, lighting and mood anchored early, aspect ratio and version locked, negative prompt prevents style drift |

### 3.2 代码助手提示词

**用户输入：**

```
Build a claude code prompt for a landing page for a business dashboard that looks and feels exactly like notion
```

**生成的超详细提示词：**

包含：
- 精确的像素规格（背景 #ffffff，主文字 #1a1a1a 等）
- 8 个具体版块
- 动画规格（IntersectionObserver，阈值 0.15，500ms ease-out）
- 约束条件（单文件，无依赖，仅 Google Fonts）
- 完成标准（两个断点正确渲染，零控制台错误）

---

## 四、记忆块系统

### 4.1 问题

长会话中，AI 经常忘记之前已经做过的决定，导致重复劳动和浪费的重新提问。

### 4.2 解决方案

**Memory Block System** 会自动提取之前的决策，并在新提示词前附上：

```markdown
## Memory (Carry Forward from Previous Context)
- Stack: React 18 + TypeScript + Supabase
- Auth uses JWT stored in httpOnly cookies, not localStorage
- Component naming convention: PascalCase, no default exports
- Design system: Tailwind only, no custom CSS files
- Architecture: no Redux, context API only
```

这是长会话中最重要的修复。

---

## 五、安装方式

### 5.1 推荐：Claude.ai 浏览器

```bash
1. 下载此仓库为 ZIP
2. 前往 claude.ai → 侧边栏 → 自定义 → Skills → 上传 Skill
```

### 5.2 备选：Claude Code

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/nidhinjs/prompt-master.git ~/.claude/skills/prompt-master
```

---

## 六、使用方法

### 6.1 自然调用

在 Claude 中自然地调用：

```
Write me a prompt for Cursor to refactor my auth module
```

```
I need a prompt for Claude Code to build a REST API — ask me what you need to know
```

```
Here's a bad prompt I wrote for GPT-4o, fix it: [paste prompt]
```

```
Generate a Midjourney prompt for a cyberpunk city at night
```

### 6.2 显式调用

```
/prompt-master I want to ask Claude Code to build a todo app with React and Supabase
```

---

## 七、12 个自动选择的提示词模板

| 模板 | 适用场景 |
|------|----------|
| Visual Descriptor | 图像生成 |
| Code Specification | 代码任务 |
| Analysis Framework | 分析任务 |
| Creative Writing | 创意写作 |
| Data Extraction | 数据提取 |
| Conversation Design | 对话设计 |
| Agentic Workflow | Agent 工作流 |
| 3D Model | 3D 模型 |
| Agentic AI | Agent AI |
| Reference Image Edit | 参考图像编辑 |
| Prompt Decompiler | 提示词反编译 |
| Universal | 通用 |

Prompt Master 会静默路由，用户永远看不到框架名称，只看到最终提示词。

---

## 八、版本历史

| 版本 | 更新内容 |
|------|----------|
| **1.5.0** | 新增 Agentic AI 和 3D Model AI 路由，移除 token 估算输出，添加指令层和文案占位符 |
| **1.4.0** | 添加参考图像编辑检测、ComfyUI 支持、Prompt Decompiler 模式，3 个新模板 |
| **1.3.0** | 围绕 PAC2026 结构重建（30/55/15），静默路由替代用户选择，引入 References 文件夹 |
| **1.2.0** | 为注意力架构重构，移除不可靠技术（ToT/GoT/USC/提示链），模板和模式移到 references |
| **1.1.0** | 扩展工具覆盖，添加记忆块系统，35 种浪费模式 |
| **1.0.0** | 初始发布 |

---

## 九、资源链接

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/nidhinjs/prompt-master |
| Star History | https://star-history.com/#nidhinjs/claude-skills&Date |

---

## 十、总结

### 10.1 核心价值

Prompt Master 的核心价值在于**将提示词工程从艺术变成科学**，通过系统化的管道确保每次都能一次到位。

| 传统方式 | Prompt Master 方式 |
|----------|-------------------|
| 模糊 → 错误 → 重试 → 浪费 | 精准 → 一次到位 |
| 凭感觉写 | 9维度提取 |
| 反复提问 | 最多3个澄清问题 |
| 忘记上下文 | Memory Block 记忆 |
| Token 浪费 | 效率审计 |

### 10.2 技术亮点

1. **7 步管道**：结构化提示词生成
2. **30+ 工具兼容**：覆盖所有主流 AI 工具
3. **5 大安全技术**：仅用可靠技术
4. **35 种浪费模式**：自动检测和避免
5. **12 个自动模板**：智能路由无需手动选择
6. **记忆块系统**：跨会话上下文保持

---

**相关话题标签**

#Prompt Master #提示词工程 #Claude #AI工具 #效率优化

**来源**

- GitHub：https://github.com/nidhinjs/prompt-master

---

*Prompt Master 由 nidhinjs 开发，采用 MIT 许可证。*
