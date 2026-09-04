---
title: "PPT Master：AI 从 PDF/DOCX/URL/Markdown 生成真正可编辑的 PPTX（不是图片）"
date: "2026-04-27T01:04:00+08:00"
slug: ppt-master-ai-editable-pptx
github_repo: "hugohe3/ppt-master"
description: "PPT Master 是一个开源工作流，运行在 Claude Code/Cursor 等 AI IDE 里，把 PDF、DOCX、URL 或 Markdown 转成真正的 PPTX——每个元素都是 DrawingML 原生形状，不是图片，可逐个点击编辑。工具免费，唯一成本是你的 AI 模型用量。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "Python", "开源工具"]
---

# PPT Master：AI 从 PDF/DOCX/URL/Markdown 生成真正可编辑的 PPTX（不是图片）

做 PPT 这件事，AI 工具已经很多了——Gamma、Copilot、各种生成式 PPT 产品。但它们有一个共同的问题：**输出的是图片或网页截图，不是真正的 PPTX**。

PPT Master 解决了这个问题。

GitHub 51k+ stars，MIT 协议，一个运行在 AI IDE 里的工作流技能，把 PDF、DOCX、URL 或 Markdown 转成真正可编辑的 PowerPoint——每个元素都是 DrawingML 原生形状（real shapes, real text boxes, real charts），不是图片拼接。剪任何元素，直接在 PowerPoint 里改文字、调颜色、改布局。

**作者是投融资从业者（注册会计师 · 资产评估师 · 咨询工程师），每天被 PPT 折磨，自己动手写了工具。**

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

除了从源材料生成新 deck，它还处理这些场景：

- **旁白与视频**：把演讲者备注合成本地语音（默认 edge-tts，约 90 种语言），嵌回 PPTX 后可直接用 PowerPoint 导出带旁白的 MP4
- **复刻音色**：支持 ElevenLabs、MiniMax、Qwen、CosyVoice 的复刻音色，整份 deck 用同一把声音讲
- **转场与动画**：导出带原生页间转场（默认 fade），元素动画可按需开启（200+ 个 OOXML 预设，默认关闭）
- **改已有 PPT**：把新内容填进现有 .pptx 并保留设计，或为成品追加转场、动画与旁白

**支持的 AI IDE：**

| 类型 | 示例 |
|------|------|
| IDE 内置 agent | VS Code 生态（Cursor、Trae、Codebuddy、Windsurf、Void）+ Zed |
| IDE 插件/扩展 | GitHub Copilot、Claude Code 扩展、Cline、Continue、Roo Code |
| CLI agent | Claude Code CLI、Codex CLI、Aider、Gemini CLI |

**推荐模型：** 作者的建议是 Kimi K3 或 Claude——上下文窗口大（约 100 万 token），能完整读完 PDF 或长文再规划叙事；配合 AI 生图（`gpt-image-2` 或 `gemini-3.1-flash-image`）效果最好。GPT、Gemini、DeepSeek 等主流模型也能跑通流程，但产出质量有明显差距。模型越便宜，生成后需要手工打磨的部分越多。

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

除了 clone 整个仓库，也支持按 skill 单独安装（`npx skills add hugohe3/ppt-master`）或走 AI 工具自带的插件/市场安装路径。两种方式下，把 AI agent 的工作目录设在你自己选定的文件夹即可，不必是 skill 安装目录。

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

**输出位置：** AI 会在工作目录下新建 `projects/<项目名>/` 作为当前生成工程，成品落在其 `exports/` 子目录，文件名带时间戳：
- `.pptx`：原生可编辑版本（Office 2016+）
- `_svg.pptx`：SVG 快照（视觉参考用）

生成过程中会起一个本地预览页（默认 `http://localhost:5050`），边生成边翻页查看。也可以不动 AI，直接选中元素改文字、颜色、大小或拖动位置，或点选元素写一句"改为 XX"交给 AI 重新生成该区域。如果 AI 丢失上下文，告诉它读取 `skills/ppt-master/SKILL.md`。

---

## 四、可选：AI 图片生成

PPT Master 支持 AI 生成配图，配置 `.env` 即可（也可以直接用环境变量，`.env` 只是兜底）：

```env
IMAGE_BACKEND=gemini
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-3.1-flash-image
```

推荐核心后端：OpenAI（`gpt-image-2`）、Gemini（`gemini-3.1-flash-image`）、通义（`qwen-image-2.0-pro`）、智谱（`glm-image`）、火山引擎（`doubao-seedream`）。另支持 Stability、Ideogram、SiliconFlow、Fal、Replicate 等扩展后端，运行以下命令查看完整列表：

```bash
python3 skills/ppt-master/scripts/image_gen.py --list-backends
```

切换提供商时只改 `IMAGE_BACKEND` 一个变量，其余各家的 Key 和模型名配置不变。

---

## 五、模板与设计系统

默认走自由设计（free design），不需要模板。示例仓库里可参考的设计风格包括：杂志风（建筑摄影 + 排版网格）、新闻/财经数据风（深色仪表盘、图表驱动）、瑞士风（严格栅格、红色点缀）、毛玻璃 SaaS（半透明叠层、渐变景深）、孟菲斯波普（高饱和原色、几何图形）、Risograph Zine（双色印刷质感）等。

当一份 deck 必须复用既有品牌或固定版式时，有两条路线：

| 你想要 | 路线 | 行为 |
|------|------|------|
| 保留现有 .pptx 的页面版式，换新内容 | Edit Native PPTX | 导入可往返编辑的工作空间，未改的页面逐字节还原，只编辑选中的页 |
| 提炼一套可复用的设计系统，以后反复生成 | Create Template → Generate | 从参考资料创建经过校验的 Brand / Style / Layout / Deck 工作空间，再生成全新 deck |

用自然语言告诉 AI 即可，例如"把新内容填进这份 .pptx 并保留它的设计"，或"用 projects/brand/our_deck.pptx 建一个可复用的 Deck 模板"。走模板路线时，生成的 deck 会带真正的母版与版式继承（`p:sldMaster` / `p:sldLayout`），而不是扁平文本框。

---

## 六、成本

PPT Master 本身免费开源（MIT），不卖订阅。唯一的成本是你的 AI 模型用量——就是你平时用 Claude Code、Cursor 这类工具时按 token 计费的钱，流程本身不额外收费。一份 deck 的消耗取决于材料长度和页数：模型越贵，生成质量越高、需要手工返工的部分越少；想压低成本就选便宜模型，代价是生成后要自己多改几轮。

如果拿不准，可以从便宜模型起步跑通全流程，再决定要不要升级到 Kimi K3 / Claude。

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

流程上先替你把叙事逻辑理顺（结构、重点、页数），再做视觉设计，而不是上来就排版面。

最终输出是 DrawingML（原生 PPTX 格式），每个形状都可独立选中、编辑、调整大小；转场和动画也是真实的 OOXML 对象，不是嵌入的视频。目前覆盖带调节手柄的原生形状与连接符、按需的数据驱动图表与表格、完整的文本/图片/填充/效果模型，走模板路线还能输出带母版/版式继承的 deck。SmartArt 是刻意排除的能力，不是缺口——官方文档明确说明这一点。

官方文档用一份逐条对照的 PowerPoint ↔ SVG 映射指南（`docs/powerpoint-svg-mapping.md`）记录当前能力覆盖到哪，避免用户对"原生"二字产生超出实际的预期。

---

## 八、Gallery 示例

示例已迁到独立仓库（hugohe3/ppt-master-examples），目前收录十余个完整工程，每个都带浏览器翻页预览和可下载的 .pptx。画廊里的示例生成于 2026 年 5 月，用的是 Claude Opus 4.7 + `gpt-image-2`，每份都是一次性生成、未经手工精修——下载任意一份在 PowerPoint 里打开，是判断真实产出水平最快的方式。

- 在线翻页：https://hugohe3.github.io/ppt-master-examples/
- 示例源码：https://github.com/hugohe3/ppt-master-examples
- 风格覆盖：杂志风、新闻/财经数据风、瑞士风、毛玻璃 SaaS、孟菲斯波普、Risograph Zine 等

---

## 九、与 Gamma / Copilot 的核心区别

| 对比 | PPT Master | Gamma / Copilot 等 |
|------|-----------|-------------------|
| 输出格式 | 原生 PPTX，DrawingML 形状 | 图片式或模板填充 |
| 可编辑性 | 每个元素都可点选编辑 | 受限于模板或图片 |
| 运行方式 | 在 AI IDE 里跑工作流 | Web 应用或插件 |
| 成本 | 工具免费，唯一成本是模型用量 | 订阅制 |
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

PPT Master 解决的问题很具体：现有 AI PPT 工具要么输出图片（无法编辑），要么套模板填空（受限于模板），都不适合"生成后还要继续改"的工作。它换了个做法——不在网页上做 PPT，而是在你自己的机器上、由 AI agent 按工作流产出真正的 PPTX 文件。

作者是投融资从业者，日常要审阅和修改 deck，被图片式输出坑过才写了这个工具。如果你也需要一份生成完还能继续编辑的 PowerPoint，下载示例仓库里的 .pptx 打开看看，比读任何介绍都直观。工具 MIT 开源，唯一成本是自己的模型用量。

## 遇到问题怎么办

- 官方 FAQ 持续从真实用户反馈更新：https://github.com/hugohe3/ppt-master/blob/main/docs/faq.md
- 生成质量不满意，先升级模型，再对照官方快速入门和示例工程检查用法——模型越便宜，需要手工补的部分越多
- 文档与安装指引：`docs/zh/getting-started.md`（中文）、`docs/zh/windows-installation.md`（Windows 手把手）

**相关链接：**

- GitHub：https://github.com/hugohe3/ppt-master（51k+ stars）
- 示例 Gallery：https://hugohe3.github.io/ppt-master-examples/（在线翻页 + 下载 .pptx）
- 官方 FAQ：https://github.com/hugohe3/ppt-master/blob/main/docs/faq.md
- 作者：Hugo He（[@hugohe3](https://github.com/hugohe3)）

🦞 每日 08:00 自动更新