---
title: "PPT Master：AI 从 PDF/DOCX/URL/Markdown 生成真正可编辑的 PPTX（不是图片）"
date: "2026-04-27T01:04:00+08:00"
slug: ppt-master-ai-editable-pptx
description: "PPT Master 是一个开源工作流，运行在 Claude Code/Cursor 等 AI IDE 里，把 PDF、DOCX、URL 或 Markdown 转成真正的 PPTX——每个元素都是 DrawingML 原生形状，不是图片，可逐个点击编辑。最低 $0.08/份，支持 22 种模板。"
draft: false
categories: ["技术笔记"]
tags: ["PPT", "AI", "PowerPoint", "Claude Code", "Python", "开源工具"]
---

# PPT Master：AI 从 PDF/DOCX/URL/Markdown 生成真正可编辑的 PPTX（不是图片）

做 PPT 这件事，AI 工具已经很多了——Gamma、Copilot、各种生成式 PPT 产品。但它们有一个共同的问题：**输出的是图片或网页截图，不是真正的 PPTX**。

PPT Master 解决了这个问题。

GitHub 8.2k stars，MIT 协议，一个运行在 AI IDE 里的工作流技能，把 PDF、DOCX、URL 或 Markdown 转成真正可编辑的 PowerPoint——每个元素都是 DrawingML 原生形状（real shapes, real text boxes, real charts），不是图片拼接。剪任何元素，直接在 PowerPoint 里改文字、调颜色、改布局。

**作者是金融从业者（CPA · CPV · 咨询工程师），每天被 PPT 折磨，自己动手写了工具。**

---

## 一、问题：为什么现有 AI PPT 工具不够用

AI PPT 工具有四类：

| 类型 | 输出 | 可在 PowerPoint 里逐元素编辑吗？|
|------|------|:---:|
| 模板填充 | 基于固定模板构建 PPTX | 部分可编辑，受限于模板 |
| 图片式 | 每页一张大图，打包进 PPTX | ❌ 每页就是一张图 |
| HTML 演示 | 网页格式的幻灯片 | ❌ 不是 PPTX |
| **原生可编辑（PPT Master）** | **真实 DrawingML 形状、文本框、图表** | ✅ 每个元素都可点击编辑 |

前三种工具更快更便宜，但如果你做完 PPT 后还需要：**合并到正式材料、做 pitch deck、写报告、做定制化修改**——图片式输出就无法满足需求。

PPT Master 面向的是：**需要在生成后继续编辑 PowerPoint 的场景**。输出本身就是一个更昂贵的工件（更复杂的结构、更精细的排版），生成成本自然比模板填充高。

---

## 二、工作原理：在 AI IDE 里跑一个工作流

PPT Master 是一个运行在 AI IDE 里的"skill"（工作流），不是独立的 Web 应用：

```
你 → 告诉 AI："请根据这个 PDF 生成 PPT"
AI → 读取 SKILL.md → 按工作流执行
    → 分析文档内容 → 设计视觉结构
    → 生成 SVG 布局 → 导出为 PPTX
```

**你只需要对话，AI 完成所有操作。** 你提供源文件（PDF/DOCX/URL/Markdown），AI 完成内容分析、视觉设计、SVG 生成、PPTX 导出。

**支持的 AI IDE：**

| 类型 | 示例 |
|------|------|
| IDE 内置 agent | VS Code 生态（Cursor、Trae、Codebuddy、Windsurf、Void）+ Zed |
| IDE 插件/扩展 | GitHub Copilot、Claude Code 扩展、Cline、Continue、Roo Code |
| CLI agent | Claude Code CLI、Codex CLI、Aider、Gemini CLI |

**推荐模型：** Claude Opus / Sonnet（经过最多测试）；GPT、Gemini、Kimi、MiniMax 等主流模型也可以使用。

---

## 三、快速开始

### 3.1 安装（唯一依赖：Python 3.10+）

```bash
# macOS / Linux
brew install python
pip install -r requirements.txt

# Windows：下载 Python → 安装时勾选 "Add to PATH" → pip install -r requirements.txt
```

如需处理微信文章且 `curl_cffi` 无预编译轮子，需要额外安装 Node.js 18+。
如需转换 .doc/.odt/.rtf/.tex 等旧格式，需要安装 Pandoc。

### 3.2 下载 PPT Master

**方式 A（推荐）：** Git clone
```bash
git clone https://github.com/hugohe3/ppt-master.git
cd ppt-master
pip install -r requirements.txt
```

**方式 B：** GitHub 点击 Code → Download ZIP → 解压

### 3.3 生成 PPT

把源文件（PDF、DOCX、图片等）放入 `projects/` 目录，然后告诉 AI：

```
你：请根据 projects/q3-report/sources/report.pdf 生成一份 PPT
```

AI 会先确认设计规范，然后自动完成全流程。也可以直接粘贴文本内容让 AI 生成。

**输出位置：** `exports/` 目录，包含两个文件：
- `.pptx`：原生可编辑版本（Office 2016+）
- `_svg.pptx`：SVG 快照（视觉参考用）

如果 AI 丢失上下文，告诉它读取 `skills/ppt-master/SKILL.md`。

---

## 四、可选：AI 图片生成

PPT Master 支持 AI 生成配图，需要配置 `.env`：

```env
IMAGE_BACKEND=gemini
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-3.1-flash-image-preview
```

支持 Core / Extended / Experimental 多个后端，运行以下命令查看完整列表：

```bash
python3 skills/ppt-master/scripts/image_gen.py --list-backends
```

生成后在 Gemini 下载完整尺寸图片，用 `scripts/gemini_watermark_remover.py` 去水印。

---

## 五、模板与设计系统

PPT Master 内置 22 种设计模板，涵盖多种场景：

| 模板 | 风格 | 适用场景 |
|------|------|---------|
| Magazine | 温暖大地色调，照片丰富布局 | 建筑指南、生活方式 |
| Academic | 结构化研究格式，数据驱动 | 学术报告、医学研究 |
| Dark Art | 电影感深色背景，画廊美学 | 音乐视频分析、艺术评论 |
| Nature Documentary | 沉浸式摄影，最小化 UI | 野生动物、自然纪录片 |
| Tech / SaaS | 简洁白色卡片，定价表布局 | 产品介绍、订阅方案 |
| Product Launch | 高对比度，醒目规格突出 | 新品发布 |

还支持自定义模板，通过内置的 `/create-template` 工作流创建自己的品牌或行业模板，详细说明在 `workflows/create-template.md`。

---

## 六、成本估算

PPT Master 本身是免费开源的，唯一成本是你的 AI 编辑器费用。

| AI 工具 | 估算成本 |
|--------|---------|
| VS Code Copilot | **$0.08/份** |
| Claude Code | 因模型而异，Opus 最贵 |
| 其他主流模型 | 因 provider 而异 |

作为参考，Claude Opus 级别的生成质量，成本仍然非常低。

---

## 七、技术设计：为什么用 SVG 作为中间层

PPT Master 的架构核心是**SVG 作为布局中间层**：

```
源文档 → 内容分析 → SVG 布局（绝对坐标）→ DrawingML 形状 → PPTX
```

SVG 提供了：
- 绝对坐标系，精确控制每个元素的位置
- 支持复杂路径和形状，适合设计级排版
- 易于被 AI 生成（文本描述 → SVG 坐标）

最终输出是 DrawingML（原生 PPTX 格式），每个形状都可独立选中、编辑、调整大小。

技术细节见 `docs/technical-design.md`。

---

## 八、Gallery 示例（22 个项目，309 页）

Live Demo：https://hugohe3.github.io/ppt-master/

已发布的示例包括：

- **12 页 PPT**：从单篇微信公众号文章用 Claude Opus 4.7 生成（hero 示例）
- **10 页 dark-tech deck**：从 Anthropic 的 Claude Code Auto Mode 工程博客生成
- Magazine / Academic / Dark Art / Nature Documentary / Tech / Product Launch 等多种风格

---

## 九、与 Gamma / Copilot 的核心区别

| 对比 | PPT Master | Gamma / Copilot 等 |
|------|-----------|-------------------|
| 输出格式 | 原生 PPTX，DrawingML 形状 | 图片式或模板填充 |
| 可编辑性 | 每个元素都可点选编辑 | 受限于模板或图片 |
| 运行方式 | 在 AI IDE 里跑工作流 | Web 应用或插件 |
| 成本 | 工具免费，AI 编辑器自选 | 订阅制 |
| 数据隐私 | 本地运行（除 AI 模型通信外）| 需要上传到服务器 |
| 适用场景 | 需要生成后继续精细编辑 | 快速生成"能用就行"的版本 |

---

## 十、适用场景

- **金融/咨询报告**：需要生成后继续调整数据和格式
- **学术演示**：需要嵌入真实图表，数据可编辑
- **产品发布**：需要品牌级定制化排版
- **Pitch Deck**：需要精细调整每一页的视觉和内容
- **正式材料**：需要合并到更大的文档体系中

---

## 总结

PPT Master 解决的是一个很具体的问题：现有 AI PPT 工具输出的要么是图片（无法编辑），要么是模板填充（受限于模板），对于需要生成后继续精细编辑的真实工作场景不适用。

作者作为金融从业者，每天被 PPT 折磨，自己动手写了工具——这种"真实痛点驱动"的项目，解决方案往往比纯技术团队做的更贴合实际需求。

如果你需要的是一份生成后还能继续改的 PowerPoint，而不是一张截图，PPT Master 值得一试。成本低至 $0.08/份，MIT 开源，无平台锁定。

**相关链接：**

- GitHub：https://github.com/hugohe3/ppt-master（8.2k stars）
- Live Demo：https://hugohe3.github.io/ppt-master/
- 示例 Gallery：https://hugohe3.github.io/ppt-master/（22 个项目，309 页）
- 作者：Hugo He（[@hugohe3](https://github.com/hugohe3)）

🦞 每日 08:00 自动更新