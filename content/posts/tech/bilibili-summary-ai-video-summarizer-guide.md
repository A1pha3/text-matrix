---
title: "BiliSummary：B站视频AI摘要与知识管理工具"
slug: "bilibili-summary-ai-video-summarizer-guide"
date: "2026-04-08T13:10:00+08:00"
lastmod: 2026-04-08T13:10:00+08:00
categories: ["技术笔记"]
tags: ["Python", "B站", "AI摘要", "FastAPI", "Bilibili", "知识管理"]
description: "BiliSummary 是一个桌面优先的 B站视频 AI 摘要工具，支持视频字幕提取、AI 摘要生成、收藏夹批量管理、统一阅读体验。"
draft: false
---

# BiliSummary：B 站视频 AI 摘要与知识管理工具

BiliSummary 把"B 站视频 → 可沉淀的 Markdown 摘要"这条链路做成了桌面应用。它的判断很明确：字幕优先、ASR 兜底，三种输入模式共用同一条摘要管道。需要把 UP 主连载或收藏夹里的视频批量转成可检索本地文本时，它比浏览器插件和移动端笔记应用更合适。

> **"Desktop-first Bilibili summarizer with AI-generated Markdown output, favorites workflow, and unified browse/reading UX."**

## 适合谁用，能解决什么

读完后你应该能回答三个问题：BiliSummary 的摘要管道为什么这样设计、三种输入模式各自的边界在哪、什么场景下该选它胜过其他工具。

| 痛点 | 解决方案 | 为什么这样选 |
|------|---------|-------------|
| B 站视频信息难以沉淀 | 转换为本地 Markdown 文件 | Markdown 可被 Obsidian、VS Code 等工具直接检索，不依赖平台 |
| 批量视频处理繁琐 | 收藏夹批量摘要功能 | 手动逐个处理 50+ 视频不现实，需要增量更新机制 |
| 视频没有字幕 | ASR 语音识别降级处理 | B 站约三成视频无 CC 字幕，纯字幕方案会漏掉这部分内容 |
| 分散的观看体验 | 统一卡片式阅读界面 | 在浏览器、笔记、摘要之间切换会打断阅读节奏 |

## 系统总览

### 技术栈与分层

BiliSummary 是典型的 Python 后端 + 原生前端 + 桌面壳结构。选 pywebview 不选 Electron，是为了让桌面应用和服务器模式共用同一份 FastAPI 代码，避免维护两套后端。

语言占比（数据来源：GitHub 语言统计，截至 2026-04-08）：

```
├── Python 36.7% — 后端核心
├── JavaScript 35.8% — 前端交互
├── CSS 20.6% — 样式设计
├── HTML 6.7% — 页面结构
└── Shell 0.2% — 构建脚本
```

核心技术选型：

| 组件 | 技术 | 选型理由 |
|------|------|---------|
| 后端 | FastAPI + Uvicorn | 异步原生支持，适合批量并发摘要 |
| 前端 | Vanilla JS + CSS（令牌化设计系统） | 无构建步骤，桌面应用启动快 |
| 桌面壳 | pywebview | 复用 FastAPI 后端，无需 Electron 体积 |
| B 站集成 | bilibili-api-python | 社区维护的逆向 API，覆盖视频/收藏夹/登录 |
| AI 摘要 | Anthropic 兼容 API | 可对接 GLM、Claude 等多家模型 |
| ASR | GLM ASR 集成 | 中文识别效果优于通用 Whisper |
| 音频处理 | PyAV | 处理 B 站 DASH/FLV 多种音频流封装 |

### 整体架构

```
┌─────────────────────────────────────┐
│ 桌面应用层 (pywebview)              │
│ 用户界面 ←→ 窗口管理 ←→ 系统集成    │
└─────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ 前端层 (Vanilla JS/CSS)             │
│ 卡片系统 ←→ 阅读界面 ←→ 收藏夹管理  │
└─────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ 后端层 (FastAPI)                    │
│ /routes/ ←→ /summarize.py ←→ AI API │
└─────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ 服务集成层                          │
│ bilibili-api-python ←→ GLM ASR      │
└─────────────────────────────────────┘
```

### 模块结构

```
bilibili-summary/
├── app.py          # 桌面应用入口 (pywebview)
├── server.py       # FastAPI 应用
├── summarize.py    # 摘要生成管道
├── routes/         # API 路由模块
│   ├── __init__.py
│   ├── favorites.py # 收藏夹相关
│   ├── video.py     # 视频相关
│   └── asr.py       # ASR 相关
├── static/         # 前端资源
│   ├── index.html
│   ├── app.js
│   └── style.css
├── docs/           # 设计文档
├── config.toml     # 配置文件
└── requirements.txt # 依赖
```

### 三种输入模式的边界

BiliSummary 有三套并行的输入模式，它们共用 `summarize.py` 这条摘要管道，但触发条件和适用场景不同。理解这条边界，才能选对模式。

| 模式 | 输入 | 适用场景 | 登录要求 |
|------|------|---------|---------|
| URL 模式 | 单个视频链接 | 临时摘要某个视频 | 可选 |
| UP 主模式 | UP 主名称或 UID | 跟踪特定 UP 主的连载 | 可选 |
| 收藏夹模式 | 收藏夹 ID | 处理自己收藏的视频集合 | 必须登录 |

## 摘要生成管道

### 字幕优先，ASR 降级

摘要管道的核心设计是"字幕优先 + ASR 降级"。之所以这样设计，是因为 B 站 CC 字幕的获取成本远低于音频下载 + ASR 识别：字幕接口几乎瞬时返回，而 ASR 需要下载音频流再调用识别服务，耗时和 API 成本都高一个数量级。先用字幕，拿不到再降级到 ASR，能在大多数场景下把延迟压到最低。

**URL 模式工作流**：

```
1. 用户粘贴 B 站视频 URL
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

### 摘要生成调用

`summarize.py` 里的摘要函数把字幕文本和提示词一起发给 AI API，要求输出结构化 Markdown：

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

### 字幕提取与 ASR 降级

字幕提取的逻辑直接：调用 `video.get_subtitle()`，有就直接取文本，没有就进 ASR 降级分支。

```python
# 检查字幕可用性
subtitle = video.get_subtitle()
if subtitle:
    text = subtitle.extract_text()
else:
    # 触发 ASR 降级
    text = await asr_process(video)
```

ASR 降级支持三种音频封装格式，因为 B 站不同视频的可用音频流格式不一致：

| 格式 | 说明 | 适用场景 |
|------|------|---------|
| DASH | B 站默认格式 | 大部分新视频 |
| FLV | 备用格式 | 老视频或特殊分区 |
| MP4 | 部分视频支持 | 移动端缓存视频 |

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

### 任务流案例：一个视频如何变成摘要

把上面的机制串起来看一个具体案例。假设用户粘贴了 `https://www.bilibili.com/video/BV1xx411c7mD`：

1. **URL 解析**：`routes/video.py` 提取 BV 号 `BV1xx411c7mD`
2. **视频信息**：`bilibili-api-python` 返回标题、UP 主、时长、字幕列表
3. **字幕检查**：该视频有官方 CC 字幕，直接 `extract_text()` 拿到全文
4. **摘要生成**：`summarize.py` 把字幕文本发给 GLM-4，提示词要求输出 Markdown
5. **文件落盘**：摘要写入本地 Markdown 文件，前端卡片显示预览

如果第 3 步发现没有字幕，会跳到 ASR 分支：下载音频 → GLM ASR 识别 → 再走第 4 步。整条管道对前端透明，用户只看到"生成中"和"完成"两个状态。

## 安装与配置

### 环境要求

- Python 3.8+
- Node.js 18+（可选，用于开发前端）
- Chrome/Chromium（用于渲染页面）

### 安装步骤

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
ANTHROPIC_AUTH_TOKEN=your_api_key
ANTHROPIC_BASE_URL=https://open.bigmodel.cn/api/anthropic
```

**启动桌面应用**：

```bash
python app.py
```

### 配置文件说明

`config.toml` 控制应用模式、B 站集成、AI 模型和 ASR 行为：

```toml
[app]
mode = "desktop"        # desktop / server
port = 8000             # 服务端口

[bilibili]
cookie = ""             # 可选，登录态 Cookie
quality = "follow_page" # 视频画质

[ai]
model = "glm-4"         # AI 模型
temperature = 0.7       # 创造性
max_tokens = 2000       # 最大输出

[asr]
enabled = true          # 启用 ASR 降级
model = "glm-asr"       # ASR 模型
```

`mode` 决定运行方式：`desktop` 启动 pywebview 窗口，`server` 只跑 FastAPI 供浏览器访问。`asr.enabled = false` 时，无字幕视频会被跳过，不会触发降级处理。

## 使用指南

### URL 模式

最基础的单视频摘要流程：

```
1. 启动应用后，在 URL 输入框粘贴 B 站视频链接
2. 点击「开始摘要」
3. 等待 AI 生成摘要
4. 查看/编辑生成的 Markdown
```

支持的 URL 格式：

| 格式 | 示例 |
|------|------|
| 普通视频 | `https://www.bilibili.com/video/BV1xx411c7mD` |
| 弹幕视频 | `https://www.bilibili.com/video/BV1xx411c7mD?p=1` |
| 收藏视频 | 同上 |

### UP 主模式

按 UP 主名称或 UID 获取近期视频，适合跟踪连载更新。功能包括批量生成摘要和增量更新（只处理新视频）。

```
1. 输入 UP 主名称或 UID
2. 点击「获取视频列表」
3. 选择要摘要的视频
4. 点击「批量摘要」
5. 等待完成
```

### 收藏夹模式

收藏夹模式需要登录 B 站账号，因为收藏夹接口要求鉴权。登录通过扫码完成，不存储明文密码。

**功能**：

- 二维码登录 B 站账号
- 加载收藏夹和视频
- 批量摘要未处理视频
- 短期撤销取消收藏

**登录流程**：

```
1. 点击「登录」
2. 扫描显示的二维码
3. 确认授权
4. 登录成功
```

**命令行批量处理**：

```bash
python -m summarize --mode favorites --uid 12345678
```

### 阅读界面

统一卡片系统把摘要和原视频放在同一界面，避免在浏览器和笔记之间切换：

```
┌─────────────────────────────────────┐
│ [缩略图]                            │
│ 视频标题                            │
│ UP 主 · 播放量 · 时长               │
│ [摘要预览...]                       │
│                                     │
│ [查看摘要] [原始视频]               │
└─────────────────────────────────────┘
```

视图切换：

| 模式 | 说明 |
|------|------|
| 缩略图模式 | 大图卡片，适合浏览 |
| 紧凑模式 | 小卡片，适合批量管理 |

## 开发指南

### 扩展 AI 提供商

AI 调用通过 `AIProvider` 抽象基类统一接口。新增提供商的步骤是继承并实现 `chat` 方法，再注册到 `ai_registry`：

```python
# routes/ai.py
class AIProvider:
    async def chat(self, prompt: str, model: str) -> str:
        raise NotImplementedError

class AnthropicProvider(AIProvider):
    async def chat(self, prompt: str, model: str) -> str:
        # 调用 Anthropic API
        ...

class OpenAIProvider(AIProvider):
    async def chat(self, prompt: str, model: str) -> str:
        # 调用 OpenAI API
        ...

# 注册提供商
ai_registry.register("anthropic", AnthropicProvider())
ai_registry.register("openai", OpenAIProvider())
```

### 扩展 ASR 提供商

ASR 同样用抽象基类隔离具体实现。如果 GLM ASR 不满足需求，可以接入 Whisper 或其他识别服务：

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

### 路由开发

新增 API 路由遵循 FastAPI 标准模式。下面是收藏夹相关路由的示例：

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

### 前端开发

前端是纯静态资源，无构建步骤，直接修改 `static/` 下的文件即可：

```
static/
├── index.html      # 主页面
├── app.js          # 应用逻辑
├── style.css       # 样式
└── components/     # 组件
```

**本地开发服务器**：

```bash
cd static
python -m http.server 8080
```

修改 `app.js` 中的 API 地址指向后端：

```javascript
const API_BASE = "http://localhost:8000"
```

## 实践建议

### 批量处理参数

批量场景下需要控制并发和增量范围，避免触发 B 站或 AI API 的限流：

| 场景 | 建议 |
|------|------|
| 收藏夹批量摘要 | 使用 `--favorite` 模式 |
| 增量更新 | 添加 `--since` 参数 |
| 并发限制 | 设置 `--concurrency` 控制 |

```bash
python -m summarize --mode favorites --uid 12345678 \
  --concurrency 12 --favorite
```

### 性能优化

| 优化项 | 方法 | 收益 |
|--------|------|------|
| 缓存字幕 | 存储到本地 `.subtitle/` | 重复处理同一视频时跳过网络请求 |
| 并发处理 | 使用 `asyncio` 并发摘要 | 批量场景吞吐量提升明显 |
| 音频压缩 | 降低采样率再 ASR | 减少 ASR API 调用成本和延迟 |
| API 限流 | 添加延迟和重试 | 避免触发 429 限流 |

### 错误处理模式

摘要管道会遇到三类常见错误，分别对应不同的恢复策略：

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

`VideoNotFoundError` 直接返回错误，`SubtitleUnavailableError` 触发 ASR 降级，`AIAPIError` 走重试或备用 API。这种分层处理避免了把所有错误都丢给用户。

### 登录态维护

B 站 Cookie 会过期，需要定期刷新。`BilibiliAPI` 封装了登录态检查和刷新逻辑：

```python
# 保持登录态
bilibili = BilibiliAPI(cookie=os.getenv("BILIBILI_COOKIE"))

# 刷新登录态
if not bilibili.is_logged_in():
    bilibili.refresh_login()
```

## 常见问题

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
# 检查 Cookie 是否过期，重新登录获取新 Cookie
# 更新 .env.local
ANTHROPIC_AUTH_TOKEN=new_token
```

**Q: ASR 识别效果差？**

```bash
# 检查音频质量，使用更高码率的音频流
bilibili.set_quality("80")

# 或手动提供字幕文件
bilibili.upload_subtitle(video_id, "subtitle.srt")
```

**Q: AI 摘要质量不好？**

```python
# 调整参数
summarize.set_temperature(0.5)   # 降低创造性
summarize.set_max_tokens(3000)   # 增加输出
```

**Q: 批量处理被限流？**

```bash
# 降低并发数
python -m summarize --concurrency 3

# 添加延迟
python -m summarize --delay 2
```

## 与类似工具对比

| 工具 | 平台 | AI 摘要 | ASR | 收藏夹 |
|------|------|---------|-----|--------|
| BiliSummary | 桌面应用 | ✅ | ✅ | ✅ |
| B 站助手 | 浏览器插件 | ❌ | ❌ | 部分 |
| 视频笔记 | 移动端 | ✅ | ❌ | ❌ |

BiliSummary 的差异点集中在三处：桌面应用离线可用、ASR 降级覆盖无字幕视频、收藏夹批量管理。浏览器插件受限于沙箱无法做 ASR，移动端应用受限于系统权限难以批量处理。

## 采用建议

按以下顺序判断是否采用 BiliSummary，每一步对应一种使用模式：

1. **单视频临时摘要**：URL 模式足够，无需登录，适合试用。如果只是偶尔摘要几个视频，到这里就够了。
2. **跟踪特定 UP 主**：UP 主模式 + 增量更新，适合连载跟踪。需要定期跑批处理脚本。
3. **构建本地知识库**：收藏夹模式 + 批量摘要，适合把分散收藏沉淀为可检索文本。需要登录 B 站账号。

不适合的场景：需要实时摘要（管道延迟在秒级以上）、需要处理非 B 站视频（仅支持 B 站）、需要团队协作（单机桌面应用无多用户支持）。

许可证状态为 NOASSERTION（SPDX 标识，表示许可证未明确声明），商用前需联系作者确认。
