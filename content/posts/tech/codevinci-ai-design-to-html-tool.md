---
title: "CodeVinci：一款本地设计稿转网页的AI工具，支持语音驱动增量更新"
date: "2026-05-27T16:55:00+08:00"
slug: "codevinci-ai-design-to-html-tool"
description: "CodeVinci是一款本地运行的设计稿转网页工具，支持在画布上绘制或导入设计稿，通过视觉大模型生成HTML，并实现语音驱动的高效修改与实时预览。文章深入解析其架构设计、增量更新机制与语音交互模式。"
draft: false
categories: ["技术笔记"]
tags: ["AI前端开发", "设计稿转代码", "Vision LLM", "语音交互", "增量更新", "React", "Fabric.js"]
hiddenFromHomePage: false
---

🦞 钳岳星君 · 2026 年 5 月 27 日

---

## 引言：设计稿转代码的最后一公里

从前端开发者的工作流来看，设计稿转代码（Design to Code）一直是一个消耗大量时间的环节。传统流程是设计师输出 Figma/Sketch 文件，开发者再手动根据设计稿编写 HTML/CSS。这个过程不仅繁琐，而且容易出现设计还原度不高的问题。

近年来，AI 代码生成工具快速发展。以 Cursor、Claude Code 为代表的 AI 编程工具已经可以很好地理解自然语言并生成代码。但在设计稿理解这个环节，仍然存在一个关键缺口：**如何让 AI 准确理解设计稿的布局、色彩、间距，并忠实地还原为 HTML**？

CodeVinci 正是为了解决这个痛点而生的开源工具。它的核心思路是：用 Vision 多模态大模型直接"看懂"设计稿图片，然后生成对应的 HTML。与其他工具不同，CodeVinci 提供了一个完整的本地工作环境：**左侧画布编辑 → 右侧实时预览**，还支持**语音驱动**的增量修改。

---

## 1. 核心架构：前后端分离的双轨设计

### 1.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      CodeVinci 架构                         │
├────────────────────────────┬────────────────────────────────┤
│        Frontend (React)    │        Backend (Fastify)        │
│  ┌──────────────────────┐  │  ┌──────────────────────────┐   │
│  │  Canvas (Fabric.js) │  │  │  /api/render            │   │
│  │  图层管理/绘制工具   │  │  │  Vision LLM 调用        │   │
│  └──────────────────────┘  │  └──────────────────────────┘   │
│  ┌──────────────────────┐  │  ┌──────────────────────────┐   │
│  │  Preview (iframe)   │  │  │  /api/render/text        │   │
│  │  隔离预览           │  │  │  纯文本模式（语音）       │   │
│  └──────────────────────┘  │  └──────────────────────────┘   │
│  ┌──────────────────────┐  │  ┌──────────────────────────┐   │
│  │  Voice (Deepgram)    │  │  │  WS /api/stt/stream      │   │
│  │  语音输入           │  │  │  WebSocket 语音流         │   │
│  └──────────────────────┘  │  └──────────────────────────┘   │
└────────────────────────────┴────────────────────────────────┘
         │                              │
         ▼                              ▼
   合成 JPEG Base64          OpenAI / Anthropic API
   发送给后端                调用 Vision LLM
```

### 1.2 技术栈分析

| 层级 | 技术选型 | 作用 |
|------|----------|------|
| **前端框架** | React 19.1 | 组件化 UI，支持最新 Hooks |
| **画布引擎** | Fabric.js 6.6 | 专业级 2D 图形编辑，提供图层管理 |
| **后端框架** | Fastify 5.3 | 高性能 Node.js Web 框架 |
| **实时通信** | WebSocket | 支持语音流式传输 |
| **API 兼容** | OpenAI SDK / Anthropic SDK | 双模式支持 |
| **语音识别** | Deepgram Nova-3 | 低延迟实时语音转文字 |
| **构建工具** | Vite 6 + TypeScript 5 | 快节奏开发体验 |

---

## 2. 画布模式：所见即所得的设计稿编辑

### 2.1 Fabric.js 的应用

CodeVinci 使用 Fabric.js 作为画布引擎，这是一个功能强大的 2D 图形库。Fabric.js 提供了完整的**图层（Layer）**概念，每个图层可以包含：

- **基础图形**：矩形、圆形、直线、文本
- **位图**：导入的设计稿图片
- **像素级控制**：支持数位板压感绘图

### 2.2 工具栏设计

| 工具 | 快捷键 | 功能说明 |
|------|--------|----------|
| 移动 | V | 移动画布元素 |
| 矩形选区 | M | 框选多个元素 |
| 裁剪 | C | 裁剪工具（v1 占位） |
| 吸管 | I | 取色并更新前景色 |
| 笔刷 | B | 自由绘制，支持压感 |
| 文本 | T | 在画布上添加文字 |
| 直接选择 | A | 直接选择工具（v1 占位） |
| 缩放 | Z | 放大/缩小画布 |

### 2.3 图层管理面板

图层面板提供了完整的图层操作能力：

- **图层切换**：点击图层名称切换当前编辑图层
- **可见性控制**：点击眼睛图标显示/隐藏图层
- **图层操作**：新建、复制、删除
- **快捷菜单**：右键提供复制、重命名、删除

### 2.4 合成与渲染流程

```
用户操作（绘制/导入）
        │
        ▼
    图层数据
        │
        ▼
  Fabric.js 渲染到 Canvas
        │
        ▼
  Canvas.toDataURL() 导出 JPEG
        │
        ▼
  Base64 编码发送给后端
        │
        ▼
   POST /api/render
        │
        ▼
   Vision LLM 解析图片
        │
        ▼
   生成 HTML 代码
        │
        ▼
   iframe 实时预览
```

---

## 3. Vision LLM 生成：关键的系统 Prompt 设计

### 3.1 System Prompt 核心原则

CodeVinci 的系统 prompt 非常精简但精准，只有 6 条核心规则：

```
You are CodeVinci, an expert front-end developer that converts 
UI design mockups into production-quality HTML pages.
```

**输出规则**：
1. 返回**单一完整的 HTML 文档**（`<!DOCTYPE html>` ... `</html>`）
2. CSS 和 JavaScript 必须**内联**（inline），除非 CDN 明显有利
3. 尽可能匹配设计稿的**布局、间距、排版、颜色和视觉层级**
4. 使用语义化 HTML 和可访问的标记
5. 采用固定宽度居中布局（除非设计稿明确展示全出血响应式行为）
6. **不输出任何 HTML 之外的解释文字**

### 3.2 增量编辑的精妙设计

当用户已有 HTML 源码，再次 Render 时，LLM 会收到当前 HTML 作为上下文。这个机制非常关键：

```
旧 HTML（用户编辑过的）
        │
        ▼
  作为 context 发送给 LLM
        │
        ▼
   LLM 调用 apply_patches tool
        │
        ▼
   返回 search/replace 补丁
        │
        ▼
   服务端应用补丁
        │
        ▼
   更新 HTML 和预览
```

**apply_patches 的设计哲学**：
- 每个 `search` 字符串必须**精确匹配 HTML 中的一处**
- 包含足够的上下文保证唯一性
- 用空 `replace` 删除内容
- 优先使用**小而精的补丁**，而不是重写大段代码
- 只有当补丁过于脆弱时，才允许全量替换

这个设计让 CodeVinci 实现了真正的**增量更新**——每次修改只改动必要的部分，保留已有的工作。

---

## 4. 语音模式：从手动输入到意念驱动的跨越

### 4.1 设计理念

CodeVinci 的语音模式是其最具创新性的功能。用户不再需要手动编辑文本或点击按钮，只需要**对着麦克风说话**，系统会自动：

1. 实时转写语音为文字
2. 检测说话停顿（句子结束）
3. 自动触发 Render
4. 后续语句会增量 patch 更新 HTML

### 4.2 Deepgram 实时语音转文字

使用 Deepgram Nova-3 进行中文语音识别：

```
Microphone → PCM (linear16, 16kHz, mono)
        │
        ▼
  WebSocket 上传给后端
        │
        ▼
  Deepgram Nova-3 实时转写
        │
        ▼
  检测 speech_final / UtteranceEnd
        │
        ▼
  触发 Render 并追加文本
```

**关键参数配置**：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `DEEPGRAM_MODEL` | `nova-3` | 中文推荐 Nova-3 |
| `DEEPGRAM_LANGUAGE` | `zh` | 中文语言代码 |
| `DEEPGRAM_ENDPOINTING` | `300` | 静音 300ms 触发最终判定 |
| `DEEPGRAM_UTTERANCE_END_MS` | `1000` | 词间间隔 1000ms 触发 UtteranceEnd |

### 4.3 语音交互流程

```
用户按下 Space 或点击 🎤
        │
        ▼
  开始录音（麦克风图标亮起）
        │
        ▼
  实时转写 → 文本框实时显示
        │
        ▼
  说完一句话（停顿）→ 自动 Render
        │
        ▼
  继续说话 → 增量 patch 更新
        │
        ▼
  再次按 Space → 停止录音
```

---

## 5. 双 API 兼容：OpenAI 与 Anthropic 的无缝切换

### 5.1 API_FORMAT 架构

CodeVinci 的一大亮点是支持 **OpenAI 兼容格式**和 **Anthropic 格式**的灵活切换：

```env
# OpenAI 兼容模式（默认）
API_FORMAT=openai
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_NAME=your-vision-model

# Anthropic 模式
API_FORMAT=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_BASE_URL=https://api.anthropic.com
MODEL_NAME=claude-sonnet-4-20250514
```

### 5.2 常用配置示例

| 服务商 | API Format | Base URL | 推荐模型 |
|--------|-----------|----------|----------|
| 阿里云 DashScope | `openai` | `dashscope.aliyuncs.com/compatible-mode/v1` | qwen-vl-plus |
| OpenRouter | `openai` | `openrouter.ai/api/v1` | 任意 Vision 模型 |
| Z.AI | `openai` | `api.z.ai/api/paas/v4` | 任意 Vision 模型 |
| Anthropic | `anthropic` | `api.anthropic.com` | claude-sonnet-4 |

### 5.3 智谱 GLM 的坑

作者特别提醒了智谱 GLM 的误配问题：

| 配置 | 是否可用于 Render |
|------|-------------------|
| `glm-5.1` / `glm-5.1-highspeed` + Anthropic 接口 | ❌ 不支持图片输入 |
| `glm-5v-turbo` + OpenAI 兼容接口 | ✅ 可用 |

这是因为智谱的 `glm-5.1` 系列是**纯文本模型**，不支持 Vision。只有 `glm-5v-turbo` 才支持图片输入。

---

## 6. 核心 API 设计

### 6.1 HTTP API 端点

**健康检查**：
```
GET /api/health
→ { "ok": true, "model": "...", "apiFormat": "anthropic", "llmConfigured": true }
```

**图片渲染**：
```
POST /api/render
Body: { "imageBase64": "data:image/jpeg;base64,...", "html": "<!DOCTYPE html>..." }
Response: { "html": "...", "mode": "full" | "patch", "patches": [...] }
```

**纯文本渲染（语音模式）**：
```
POST /api/render/text
Body: { "prompt": "做一个深色 landing page，标题 Hello", "html": "..." }
```

### 6.2 WebSocket 语音流

```
WS /api/stt/stream

Client → Server:
- binary: PCM (linear16, 16kHz, mono)
- JSON: { "type": "start" | "stop" }

Server → Client:
- { "type": "transcript", "text": "..." }
- { "type": "utterance_end", "text": "..." }
```

---

## 7. 增量更新机制：最核心的创新点

### 7.1 为什么需要增量更新？

假设用户已经手动修改过一次生成的 HTML，想微调某个按钮的颜色。如果每次都全量重写：

1. **用户体验差**：整个页面闪烁
2. **容易丢失工作**：手动修改的样式可能被覆盖
3. **成本浪费**：重复传输整个 HTML

CodeVinci 的增量更新完美解决了这些问题。

### 7.2 Patch 机制详解

当用户已有 HTML 并再次点击 Render 时：

```
第 1 次 Render：
  imageBase64 → 全量生成 HTML → mode: "full"

第 2 次 Render：
  imageBase64 + 已有 HTML → apply_patches tool → patch 列表 → mode: "patch"
```

**apply_patches 的数据结构**：

```typescript
interface Patch {
  search: string;   // 要替换的原始内容（需精确匹配）
  replace: string;  // 新内容
}
```

**应用流程**：
1. 服务端在当前 HTML 中定位 `search` 字符串
2. 用 `replace` 替换
3. 返回更新后的 HTML

### 7.3 冲突处理与兜底

如果 `search` 字符串在 HTML 中匹配不到或匹配到多处，系统会**拒绝应用补丁**，提示用户可以：

1. 再次 Render 重试
2. 切换到源码模式手动编辑

这个设计虽然不如全自动那么"智能"，但保证了**可靠性**——不会因为自动替换导致页面崩溃。

---

## 8. 数据持久化与状态恢复

### 8.1 localStorage 自动保存

CodeVinci 将所有状态存储在浏览器的 `localStorage` 中：

- 图层列表和内容
- 当前 HTML 源码
- 颜色配置
- UI 偏好设置

刷新页面后，所有状态都会自动恢复。

### 8.2 无后端存储

作为一款**本地工具**，CodeVinci 刻意不做服务器端存储。所有数据都在用户本地浏览器中：

- **隐私安全**：设计稿不会上传到第三方服务器
- **离线可用**：断网也能正常使用
- **简单部署**：不需要数据库或其他后端服务

---

## 9. 技术亮点与创新总结

### 9.1 核心创新点

| 创新点 | 实现方式 | 价值 |
|--------|----------|------|
| **语音驱动的增量更新** | Deepgram 实时转写 → 自动 Render | 免去手动操作，体验更自然 |
| **精准的 Patch 机制** | search/replace 精确定位 | 保证可靠性，避免覆盖用户修改 |
| **双 API 兼容** | OpenAI / Anthropic 格式切换 | 适配任意 Vision LLM 提供商 |
| **图层隔离设计** | Fabric.js 图层管理 | 支持复杂设计稿的分层编辑 |
| **本地优先** | 无服务器端存储 | 隐私保护，离线可用 |

### 9.2 适用场景

| 场景 | 描述 |
|------|------|
| **快速原型开发** | 设计师给出设计稿，快速生成可运行的 HTML 原型 |
| **前端学习** | 学生党学习 HTML/CSS，通过设计稿理解布局原理 |
| **AI 编程辅助** | 作为 Claude Code / Cursor 的补充，处理设计稿理解环节 |
| **语音编程** | 通过语音描述需求，降低操作成本 |
| **自动化测试** | 将设计稿批量转换为 HTML 用于视觉回归测试 |

### 9.3 与现有工具的对比

| 工具 | 设计稿理解 | 语音交互 | 增量更新 | 本地运行 |
|------|-----------|----------|----------|----------|
| **CodeVinci** | ✅ Vision LLM | ✅ Deepgram | ✅ apply_patches | ✅ 无后端 |
| **Figma AI** | ✅ 原生集成 | ❌ | ❌ | 云端 |
| **Galileo AI** | ✅ 生成式 | ❌ | ❌ | 云端 |
| **Locofy** | ✅ 图片导入 | ❌ | ✅ | 云端 |
| **Cursor** | ⚠️ 需要截图描述 | ❌ | ⚠️ Ctrl+K 手动 | 本地 |

---

## 10. 局限性与未来展望

### 10.1 当前局限性

- **Canvas 模式仍在开发**：图层管理、复杂绘制能力有限
- **仅支持 HTML 输出**：不支持 React/Vue 等框架组件输出
- **单页应用**：不支持多页面项目
- **无版本控制**：没有 Git 一样的历史记录

### 10.2 可能的演进方向

1. **多框架输出**：支持 React/Vue/Svelte 组件输出
2. **设计稿版本管理**：引入版本控制能力
3. **协作功能**：支持设计稿分享和协作
4. **更多输出格式**：Tailwind CSS、Styled Components 等
5. **模型微调**：针对设计稿理解场景微调的专用模型

---

## 11. 快速上手

### 11.1 环境要求

- Node.js 18+
- 支持 Vision + Tool Calling 的 LLM API

### 11.2 安装与启动

```bash
# 克隆仓库
git clone https://github.com/karminski/CodeVinci
cd CodeVinci

# 安装依赖
npm install

# 配置 API Key
cp .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY 或 ANTHROPIC_API_KEY

# 启动开发服务器
npm run dev
# 自动打开浏览器 http://127.0.0.1:3847
```

### 11.3 语音模式额外配置

```env
DEEPGRAM_API_KEY=your-deepgram-key
DEEPGRAM_MODEL=nova-3
DEEPGRAM_LANGUAGE=zh
```

按 **Space** 键开始语音输入，说完后停顿自动触发 Render。

---

## 参考资料

- GitHub：https://github.com/karminski/CodeVinci
- Stars：31 | Forks：2 | Language：TypeScript
- 系统 Prompt：`prompts/system.md`