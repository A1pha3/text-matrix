---
title: "Archify 拆解：让 AI Agent 直接生成架构图的 Skill"
slug: tt-a1i-archify-agent-skill-architecture-diagram-guide
date: 2026-07-11T02:50:00+08:00
lastmod: 2026-07-11T02:50:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["archify", "agent-skill", "mermaid", "diagram", "AI-工具"]
description: "Archify 是一个让 Claude / Codex CLI / opencode 直接生成架构图、技术流程图、时序图的 agent skill。它把自然语言描述转为单文件 HTML 图表，支持深色浅色切换、4× 倍率 PNG/JPEG/WebP/SVG 导出。本文拆解其工作流、与 Mermaid/Excalidraw 的关系。"
---

# Archify 拆解：让 AI Agent 直接生成架构图的 Skill

## 核心判断

Archify 不是一个画图工具，而是**一个 agent skill**——它让 Claude Code、Codex CLI、opencode 这类 AI 编程助手在对话中直接产出"可发布的"架构图。它的核心价值是**把"描述架构"和"得到图"之间的工具切换成本降到零**——你不再需要打开 draw.io、拖拽、导出、再粘回去。

## 项目坐标

| 维度 | 数据 |
|------|------|
| 仓库 | tt-a1i/archify |
| Stars | 约 3.4k |
| 主语言 | 文档 + 提示词 + HTML 模板 |
| License | MIT |
| 输出格式 | 单文件 HTML（内嵌 SVG / Canvas 渲染） |
| 兼容平台 | Claude Code、Codex CLI、opencode |

## 什么是 Agent Skill

agent skill 是给 AI 编程助手用的"操作手册"——一份 markdown 文档，告诉 AI 在某个场景下应该怎么做：

```yaml
---
name: archify
description: "Generate architecture, technical workflow, sequence, data-flow, and lifecycle diagrams in chat."
---

# Archify
[指令集]
1. 用户描述系统或流程
2. 分析场景类型
3. 生成对应的 HTML/SVG
4. 输出可复制/可导出的内容
```

Archify 是其中一个具体 skill——专门生成"架构图、流程图、时序图、数据流图、生命周期图"。其他常见 agent skill 包括 `commit`、`review`、`refactor` 等。

## Archify 的工作流

典型使用：

```
用户：我有一个 Web 服务，前端是 Next.js，后端是 Go gRPC，
      数据库是 PostgreSQL，还有 Redis 做缓存，RabbitMQ 做消息队列
      请帮我画个架构图

AI（加载 Archify skill）：
  → 分析：这是系统架构图（architecture diagram）
  → 输出：单文件 HTML，内嵌 SVG 渲染
  → 提供：浏览器打开链接、复制 HTML、导出 PNG/SVG
```

输出的 HTML 文件：

- 单文件，可直接 `open file.html`
- 切换深色 / 浅色主题
- 复制到剪贴板（直接 paste 进飞书、Notion、Confluence）
- 导出 PNG（4× 倍率，适合高清）、JPEG、WebP、SVG

## 与 Mermaid 的取舍

Mermaid 是经典的"代码画图"工具，Archify 与它的关系不是替代，而是**层级互补**：

| 维度 | Mermaid | Archify |
|------|---------|---------|
| 输入 | Mermaid DSL 代码 | 自然语言描述 |
| 渲染 | 浏览器/SVG/PNG | 单文件 HTML |
| 美观度 | 通用风格，可定制 | 更接近"设计稿"风格 |
| 自定义能力 | 高（写 CSS/HTML） | 中（参数化） |
| 交互性 | 静态 | 主题切换、复制、导出按钮 |
| 学习曲线 | 中（要学 DSL） | 低（说人话即可） |
| AI 生成友好 | 中（语法错误率高） | 高（专为 AI 设计） |

**AI 用 Mermaid 经常出错**——括号不匹配、关键字拼错、布局乱。Archify 走的是"AI 输出 HTML 模板 + 浏览器渲染"，绕过了 DSL 解析问题。

## 与 Excalidraw / draw.io 的取舍

| 工具 | 交互方式 | AI 友好度 | 输出 |
|------|---------|----------|------|
| **Excalidraw** | 手绘风格 GUI | ❌ 鼠标拖拽 | Excalidraw 文件 |
| **draw.io** | 桌面 GUI | ❌ 鼠标拖拽 | PNG / SVG / XML |
| **Mermaid** | 代码 | 中（DSL 易错） | PNG / SVG |
| **Archify** | 自然语言 | ✅ 高 | HTML / PNG / SVG |

Archify 不是替代 Excalidraw/draw.io——这两个是"人在浏览器画图"的工具，强调**手感和精确控制**。Archify 是"AI 帮你画"的工具，强调**速度 + 描述即产出**。

## 实际场景举例

### 场景 1：画系统架构图

```
用户：画一个电商系统的架构图，包含 CDN、WAF、Nginx、
      API Gateway、用户服务、订单服务、库存服务、MySQL 主从、
      Redis 集群、Kafka、Elasticsearch、Prometheus

Archify 输出：
  - 单文件 HTML
  - 节点：CDN / WAF / Nginx / API Gateway / 各服务 / 数据存储
  - 边：HTTPS / gRPC / SQL / Cache / Message Queue
  - 分组：边缘层 / 网关层 / 服务层 / 数据层 / 监控层
```

### 场景 2：画时序图

```
用户：用户登录的时序图，包含浏览器、CDN、API Gateway、
      Auth Service、User Service、Redis、DB

Archify 输出：
  - 时序图（sequence diagram）
  - 角色：6 个
  - 消息：登录请求 → 校验 → 查询 → 返回 token → 缓存 → 响应
  - 异步消息用虚线箭头
```

### 场景 3：画数据流图

```
用户：实时推荐系统的数据流，包含用户行为、Flume、Kafka、
      Flink、特征工程、模型推理、Redis 缓存、API 返回

Archify 输出：
  - 数据流图
  - 流向：用户行为 → 采集 → 消息队列 → 流处理 → 特征库 → 模型 → 缓存 → API
```

## 输出物的实际质量

Archify 的设计目标是"**可发布**"——你拿到的图能直接放进：

- 技术文档（README、Confluence、Notion）
- 飞书 / 钉钉 / Slack 消息
- 演示幻灯片（4× PNG 倍率适合 Retina 屏幕）
- 论文 / 博客插图（SVG 矢量）

不是"AI 凑合画"的水准，而是设计稿水准——节点对齐、配色协调、字体一致。

## 适用边界

**适合**：

- 技术博客 / 文档的架构图
- 内部技术评审、设计文档
- 演示文稿插图
- 教学材料（系统设计课程）

**不适合**：

- 复杂手绘风格（Excalidraw）
- 严格 UI/UX 设计稿（Figma）
- 流程图需要嵌入交互（用 React Flow）
- 实时协作编辑（Excalidraw Live / Figma）

## 与其它 AI 画图工具的对比

| 工具 | 平台 | 输出 | 特色 |
|------|------|------|------|
| **Archify** | Claude/Codex | HTML | agent skill，专为 AI 设计 |
| **Whimsical AI** | Web 应用 | Whimsical 文件 | 通用协作 + AI |
| **DiagramGPT (erichart)** | ChatGPT plugin | Mermaid | 自然语言生成 Mermaid |
| **Figma AI** | Figma 内置 | Figma 文件 | 设计协作 |
| **ChartGPT** | Web | 图表（非架构图） | 数据可视化 |

Archify 的定位最明确：**"我是给 AI 编程助手用的 skill，不是给人用的工具"**。这个定位让它能深度集成到开发流（Claude Code 会话内直接产出），而不是"AI 生成 → 复制到 draw.io → 修图"的循环。

## 实战起步

### 安装到 Claude Code

```bash
# 方式 1：手动复制 skill 到 .claude/skills/
cp -r archify ~/.claude/skills/archify

# 方式 2：通过 skills.sh（如果可用）
npx skills add tt-a1i/archify
```

### 在对话中使用

```
You: 加载 archify skill，然后帮我画 [描述]

Claude: [加载 SKILL.md]
        [分析场景]
        [输出 HTML]
        提供：
        - 在浏览器打开: file:///path/to/diagram.html
        - 复制 HTML 代码（直接 paste 到 README）
        - 导出 PNG（4× 倍率）
        - 导出 SVG（矢量，适合论文）
```

### 自定义扩展

Archify 的 HTML 模板是可改的——你可以 fork 后修改配色、字体、布局方式，让它产出符合团队风格的图表。

## 何时用 / 何时不用

**适合**：

- 写技术文档时需要快速出图
- 设计评审前的"初稿图"
- 教学场景（系统设计课程、技术分享）
- 节省时间比"设计稿完美"更重要

**不适合**：

- 客户演示的高保真设计稿
- 需要精细品牌控制的视觉资产
- 复杂流程图（超过 50 个节点会显得拥挤）
- 实时数据可视化

## 配套生态

Archify 是 agent skill 生态的早期代表之一。同类项目：

- **obra/superpowers**：完整的 agent skill 库（不只是画图）
- **mattpocock/skills**：技能合集
- **addyosmani/agent-skills**：工程实践技能
- **iOfficeAI/OfficeCLI**：办公套件操作 skill

这个生态的核心理念：**"AI 编程助手的能力上限由 skill 决定"**。Archify 把"画架构图"从一个一次性 prompt 提升为"可复用的标准流程"。

## 参考资源

- 仓库：[https://github.com/tt-a1i/archify](https://github.com/tt-a1i/archify)
- agent skill 生态：[https://github.com/obra/superpowers](https://github.com/obra/superpowers)
- 替代方案 Excalidraw：[https://excalidraw.com/](https://excalidraw.com/)
- Mermaid 文档：[https://mermaid.js.org/](https://mermaid.js.org/)