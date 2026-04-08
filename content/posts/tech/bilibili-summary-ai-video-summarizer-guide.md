---
title: "BiliSummary：B站视频AI摘要与知识管理工具"
slug: "bilibili-summary-ai-video-summarizer-guide"
date: 2026-04-08T13:10:00+08:00
lastmod: 2026-04-08T13:10:00+08:00
categories: ["技术笔记"]
tags: ["Python", "B站", "AI摘要", "FastAPI", "Bilibili", "知识管理"]
description: "BiliSummary 是一个桌面优先的 B站视频 AI 摘要工具，支持视频字幕提取、AI 摘要生成、收藏夹批量管理、统一阅读体验。"
draft: false
---

# BiliSummary：B站视频AI摘要与知识管理工具

## 1. 学习目标

通过本文你将掌握：

- 理解 BiliSummary 的设计理念和核心价值
- 熟练安装和配置工具
- 掌握各种使用模式（URL、UP主、收藏夹）
- 理解 AI 摘要生成和 ASR 降级策略
- 定制和扩展工具功能
- 最佳实践和常见问题解决

## 2. 项目概述

### 2.1 什么是 BiliSummary

BiliSummary 是一个桌面优先的 B站视频摘要工具：

> **"Desktop-first Bilibili summarizer with AI-generated Markdown output, favorites workflow, and unified browse/reading UX."**

**一句话解释**：输入 B站视频 URL 或 UP主，获取 AI 生成的 Markdown 摘要，支持收藏夹批量管理。

### 2.2 核心价值

| 痛点 | 解决方案 |
|------|---------|
| B站视频信息难以沉淀 | 转换为本地 Markdown 文件 |
| 批量视频处理繁琐 | 收藏夹批量摘要功能 |
| 视频没有字幕 | ASR 语音识别降级处理 |
| 分散的观看体验 | 统一卡片式阅读界面 |

### 2.3 技术栈

```
├── Python 36.7% — 后端核心
├── JavaScript 35.8% — 前端交互
├── CSS 20.6% — 样式设计
├── HTML 6.7% — 页面结构
└── Shell 0.2% — 构建脚本
```

**核心技术**：

| 组件 | 技术 |
|------|------|
| 后端 | FastAPI + Uvicorn |
| 前端 | Vanilla JS + CSS（令牌化设计系统） |
| 桌面壳 | pywebview |
| B站集成 | bilibili-api-python |
| AI 摘要 | Anthropic 兼容 API |
| ASR | GLM ASR 集成 |
| 音频处理 | PyAV |

## 3. 系统架构

### 3.1 整体架构

```
┌─────────────────────────────────────┐
│           桌面应用层 (pywebview)           │
│  用户界面 ←→ 窗口管理 ←→ 系统集成          │
└─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────┐
│           前端层 (Vanilla JS/CSS)          │
│  卡片系统 ←→ 阅读界面 ←→ 收藏夹管理        │
└─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────┐
│           后端层 (FastAPI)                 │
│  /routes/ ←→ /summarize.py ←→ AI API    │
└─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────┐
│           服务集成层                      │
│  bilibili-api-python ←→ GLM ASR        │
└─────────────────────────────────────┘
```

### 3.2 模块结构

**项目目录**：

```
bilibili-summary/
├── app.py              # 桌面应用入口 (pywebview)
├── server.py           # FastAPI 应用
├── summarize.py        # 摘要生成管道
├── routes/             # API 路由模块
│   ├── __init__.py
│   ├── favorites.py    # 收藏夹相关
│   ├── video.py        # 视频相关
│   └── asr.py          # ASR 相关
├── static/             # 前端资源
│   ├── index.html
│   ├── app.js
│   └── style.css
├── docs/                # 设计文档
├── config.toml         # 配置文件
└── requirements.txt    # 依赖
```

### 3.3 工作流程

**URL 模式**：

```
1. 用户粘贴 B站视频 URL
   ↓
2. 后端解析 URL，提取视频 ID
   ↓
3. 调用 bilibili-api-python 获取视频信息
   ↓
4. 检查字幕：
   - 有字幕 → 直接提取字幕文本
   - 无字幕 → 触发 ASR 降级流程
   ↓
5. 将字幕发送给 AI API 生成摘要
   ↓
6. 输出 Markdown 文件
```

**ASR 降级流程**：

```
1. 检测视频无字幕
   ↓
2. 下载视频音频流（DASH/FLV/MP4）
   ↓
3. 提取音频片段
   ↓
4. 调用 GLM ASR 进行语音识别
   ↓
5. 将识别结果发送 AI API 生成摘要
   ↓
6. 输出 Markdown 文件
```

## 4. 安装与配置

### 4.1 环境要求

- Python 3.8+
- Node.js 18+（可选，用于开发前端）
- Chrome/Chromium（用于渲染页面）

### 4.2 安装步骤

**克隆仓库**：

```bash
git clone https://github.com/jackwener/bilibili-summary.git
cd bilibili-summary
```

**创建虚拟环境**：

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
.\venv\Scripts\activate   # Windows
```

**安装依赖**：

```bash
pip install -r requirements.txt
```

**配置环境变量**：

创建 `.env.local` 文件：

```bash
# .env.local
ANTHROPIC_AUTH_TOKEN=your_api_key
ANTHROPIC_BASE_URL=https://open.bigmodel.cn/api/anthropic
```

**启动桌面应用**：

```bash
python app.py
```

### 4.3 配置

**config.toml**：

```toml
[app]
mode = "desktop"           # desktop / server
port = 8000               # 服务端口

[bilibili]
cookie = ""               # 可选，登录态 Cookie
quality = "follow_page"    # 视频画质

[ai]
model = "glm-4"           # AI 模型
temperature = 0.7           # 创造性
max_tokens = 2000           # 最大输出

[asr]
enabled = true             # 启用 ASR 降级
model = "glm-asr"          # ASR 模型
```

## 5. 使用指南

### 5.1 URL 模式

**基础用法**：

```
1. 启动应用后，在 URL 输入框粘贴 B站视频链接
2. 点击「开始摘要」
3. 等待 AI 生成摘要
4. 查看/编辑生成的 Markdown
```

**支持的 URL 格式**：

| 格式 | 示例 |
|------|------|
| 普通视频 | https://www.bilibili.com/video/BV1xx411c7mD |
| 弹幕视频 | https://www.bilibili.com/video/BV1xx411c7mD?p=1 |
| 收藏视频 | 同上 |

### 5.2 UP 主模式

**功能**：

- 按 UP主名称或 UID 获取近期视频
- 批量生成摘要
- 增量更新（只处理新视频）

**使用步骤**：

```
1. 输入 UP主名称或 UID
2. 点击「获取视频列表」
3. 选择要摘要的视频
4. 点击「批量摘要」
5. 等待完成
```

### 5.3 收藏夹模式

**功能**：

- 二维码登录 B站账号
- 加载收藏夹和视频
- 批量摘要未处理视频
- 短期撤销取消收藏

**登录**：

```
1. 点击「登录」
2. 扫描显示的二维码
3. 确认授权
4. 登录成功
```

**批量摘要**：

```bash
# 命令行批量处理
python -m summarize --mode favorites --uid 12345678
```

### 5.4 阅读界面

**统一卡片系统**：

```
┌─────────────────────────────────────┐
│ [缩略图]                        │
│ 视频标题                        │
│ UP主 · 播放量 · 时长            │
│ [摘要预览...]                   │
│                                │
│ [查看摘要] [原始视频]           │
└─────────────────────────────────────┘
```

**视图切换**：

| 模式 | 说明 |
|------|------|
| 缩略图模式 | 大图卡片，适合浏览 |
| 紧凑模式 | 小卡片，适合批量管理 |

## 6. AI 摘要功能

### 6.1 摘要生成

**调用流程**：

```python
# summarize.py
async def generate_summary(text: str, model: str = "glm-4") -> str:
    prompt = f"""请为以下内容生成简洁的摘要：

{text}

要求：
1. 提取核心观点
2. 按逻辑结构组织
3. 保留关键细节
4. 输出 Markdown 格式
"""
    
    response = await ai_client.chat(prompt, model=model)
    return response
```

### 6.2 字幕处理

**字幕提取**：

```python
# 检查字幕可用性
subtitle = video.get_subtitle()
if subtitle:
    text = subtitle.extract_text()
else:
    # 触发 ASR 降级
    text = await asr_process(video)
```

### 6.3 ASR 降级

**支持的格式**：

| 格式 | 说明 |
|------|------|
| DASH | B站默认格式 |
| FLV | 备用格式 |
| MP4 | 部分视频支持 |

**处理流程**：

```python
async def asr_process(video):
    # 1. 获取音频流
    audio_url = video.get_audio_url(format="mp4")
    
    # 2. 下载音频
    audio_data = await download_audio(audio_url)
    
    # 3. ASR 识别
    text = await gl_asr.recognize(audio_data)
    
    # 4. 生成摘要
    summary = await generate_summary(text)
    
    return summary
```

## 7. 开发指南

### 7.1 添加新的 AI 提供商

```python
# routes/ai.py
class AIProvider:
    async def chat(self, prompt: str, model: str) -> str:
        raise NotImplementedError

class AnthropicProvider(AIProvider):
    async def chat(self, prompt: str, model: str) -> str:
        # 调用 Anthropic API
        ...

class OpenA IProvider(AIProvider):
    async def chat(self, prompt: str, model: str) -> str:
        # 调用 OpenAI API
        ...

# 注册提供商
ai_registry.register("anthropic", AnthropicProvider())
ai_registry.register("openai", OpenAIProvider())
```

### 7.2 添加新的 ASR 提供商

```python
# routes/asr.py
class ASRProvider:
    async def recognize(self, audio_data: bytes) -> str:
        raise NotImplementedError

class GLMProvider(ASRProvider):
    async def recognize(self, audio_data: bytes) -> str:
        # 调用 GLM ASR
        ...

# 注册提供商
asr_registry.register("glm", GLMProvider())
```

### 7.3 路由开发

```python
# routes/favorites.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/favorites/{uid}")
async def get_favorites(uid: str):
    favorites = await bilibili.get_favorites(uid)
    return favorites

@router.post("/favorites/{fid}/summarize")
async def summarize_favorite(fid: str):
    videos = await bilibili.get_favorite_videos(fid)
    results = []
    for video in videos:
        summary = await summarize.generate_summary(video)
        results.append(summary)
    return results
```

### 7.4 前端开发

**静态资源**：

```
static/
├── index.html    # 主页面
├── app.js       # 应用逻辑
├── style.css    # 样式
└── components/  # 组件
```

**本地开发服务器**：

```bash
# 启动前端开发服务器
cd static
python -m http.server 8080

# 修改 API 地址
# app.js
const API_BASE = "http://localhost:8000"
```

## 8. 最佳实践

### 8.1 批量处理

| 场景 | 建议 |
|------|------|
| 收藏夹批量摘要 | 使用 `--favorite` 模式 |
| 增量更新 | 添加 `--since` 参数 |
| 并发限制 | 设置 `--concurrency` 控制 |

```bash
# 批量摘要收藏夹（限速 12 并发）
python -m summarize --mode favorites --uid 12345678 \
    --concurrency 12 --favorite
```

### 8.2 性能优化

| 优化项 | 方法 |
|--------|------|
| 缓存字幕 | 存储到本地 `.subtitle/` |
| 并发处理 | 使用 `asyncio` 并发摘要 |
| 音频压缩 | 降低采样率再 ASR |
| API 限流 | 添加延迟和重试 |

### 8.3 错误处理

```python
try:
    summary = await summarize(video)
except VideoNotFoundError:
    return {"error": "视频不存在或已被删除"}
except SubtitleUnavailableError:
    # 触发 ASR 降级
    summary = await asr_summarize(video)
except AIAPIError as e:
    # 重试或降级到备用 API
    summary = await summarize_with_backup(video)
```

### 8.4 登录状态

```python
# 保持登录态
bilibili = BilibiliAPI(cookie=os.getenv("BILIBILI_COOKIE"))

# 刷新登录态
if not bilibili.is_logged_in():
    bilibili.refresh_login()
```

## 9. 常见问题

**Q: 桌面应用启动失败？**

```bash
# 确保 pywebview 已安装
pip install pywebview

# 或使用服务器模式
python server.py
# 然后浏览器访问 http://localhost:8000
```

**Q: 视频获取失败？**

```bash
# 检查 Cookie 是否过期
# 重新登录获取新 Cookie
# 更新 .env.local
ANTHROPIC_AUTH_TOKEN=new_token
```

**Q: ASR 识别效果差？**

```bash
# 检查音频质量
# 使用更高码率的音频流
bilibili.set_quality("80")

# 或手动提供字幕文件
bilibili.upload_subtitle(video_id, "subtitle.srt")
```

**Q: AI 摘要质量不好？**

```bash
# 调整参数
summarize.set_temperature(0.5)   # 降低创造性
summarize.set_max_tokens(3000)     # 增加输出
```

**Q: 批量处理被限流？**

```bash
# 降低并发数
python -m summarize --concurrency 3

# 添加延迟
python -m summarize --delay 2
```

## 10. 与类似工具对比

| 工具 | 平台 | AI 摘要 | ASR | 收藏夹 |
|------|------|---------|-----|--------|
| BiliSummary | B站 | ✅ | ✅ | ✅ |
| B站助手 | 浏览器插件 | ❌ | ❌ | 部分 |
| 视频笔记 | 移动端 | ✅ | ❌ | ❌ |

**BiliSummary 优势**：
- 桌面应用，离线可用
- AI 摘要生成
- ASR 语音识别降级
- 收藏夹批量管理
- 开源可扩展

## 11. 总结

BiliSummary 是 B站视频知识管理的利器：

| 特性 | 说明 |
|------|------|
| 桌面优先 | pywebview 跨平台应用 |
| AI 摘要 | Anthropic 兼容 API |
| ASR 降级 | 无字幕视频自动识别 |
| 收藏夹 | 批量管理，一键摘要 |
| 开源免费 | MIT 许可证 |

**适用场景**：
- B站视频学习笔记
- 批量视频内容沉淀
- UP主视频跟踪
- 知识库建设

---

*🦞 每日08:00自动更新*
