---
title: "MoneyPrinterTurbo：AI大模型一键生成高清短视频"
date: "2026-05-28T15:05:00+08:00"
slug: "moneyprinterturbo-ai-short-video-generator"
description: "MoneyPrinterTurbo 只需提供一个视频主题或关键词，即可全自动生成视频文案、视频素材、视频字幕、视频背景音乐，然后合成一个高清短视频。支持竖屏9:16和横屏16:9，已斩获63,764 Stars。"
---

# MoneyPrinterTurbo：AI大模型一键生成高清短视频

🎯 **一句话概括**：输入一个主题，AI全自动生成高清短视频——包括文案、配乐、字幕、素材，全都不用你操心。

---

## 📊 基本信息

| 项目 | 信息 |
|------|------|
| **GitHub** | [harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) |
| **语言** | Python |
| **Stars** | 63,764 |
| **Forks** | 9,258 |
| **License** | MIT |
| **创建时间** | 2024-03-11 |
| **标签** | AI, Automation, ShortVideo, MoviePy |

---

## 🔥 为什么火

短视频是当下最热的内容形式，但制作一个质量过关的视频要耗费大量时间：写文案、找素材、剪辑、配字幕、选 BGM……

MoneyPrinterTurbo 把这整条流水线自动化了。你只需要给一个主题或关键词，AI 就会：

1. **自动生成文案** — 用大模型写好视频解说词，支持中文和英文
2. **自动匹配素材** — 从 Pexels 等无版权高清素材库中找匹配画面
3. **自动生成字幕** — 精确同步，支持字体、颜色、位置、大小调整
4. **自动配上音乐** — 随机或指定背景音乐，可调节音量
5. **自动合成视频** — 最终输出 1080p 高清视频，支持竖屏横屏

> 💡 **今日新增 Stars：9,257**，热度仍在高速增长。

---

## ✨ 核心功能

### 多种视频尺寸

- **竖屏 9:16**：`1080×1920` — 适合抖音、TikTok、小红书
- **横屏 16:9**：`1920×1080` — 适合 YouTube、B站

### 批量生成

支持一次生成多个视频，然后选最满意的一个。

### 多模型支持

支持以下 LLM 提供商（接入灵活）：

| 类型 | 提供商 |
|------|--------|
| **国际主流** | OpenAI、Azure、Google Gemini |
| **国内可用** | DeepSeek、Moonshot（强烈推荐国内用户）、通义千问、文心一言、MiniMax |
| **本地部署** | Ollama、ModelScope |
| **免费方案** | gpt4free、one-api、Pollinations |

> 🇨🇳 **国内用户建议使用 DeepSeek 或 Moonshot**，注册即送额度，无需 VPN 直接访问。

### 灵活的视频片段控制

可设置每个素材片段的时长，方便控制素材切换节奏。

---

## 🚀 快速上手

### 方式一：Google Colab（最简单）

点击即可运行，无需配置环境：

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/harry0703/MoneyPrinterTurbo/blob/main/docs/MoneyPrinterTurbo.ipynb)

### 方式二：本地部署

**macOS / Linux：**

```bash
# 克隆代码
git clone https://github.com/harry0703/MoneyPrinterTurbo.git
cd MoneyPrinterTurbo

# 使用 uv 安装依赖（推荐）
uv sync --frozen

# 复制配置
cp config.example.toml config.toml

# 启动 WebUI
# 先在 config.toml 中配置 llm_provider 和 API Key
python webui.py
```

**Windows：**

下载一键启动包（百度网盘 / Google Drive），解压后双击 `start.bat`。首次使用建议先执行 `update.bat` 更新到最新代码。

### 方式三：Docker 部署

```bash
docker run -d -p 8501:8501 \
  -v ./config.toml:/app/config.toml \
  harry0703/moneyprinterturbo
```

### API 方式调用

也支持纯 API 调用，方便集成到其他平台：

```python
import requests

response = requests.post("http://localhost:8501/api/generate", json={
    "subject": "如何增加生活的乐趣",
    "duration": 60,
    "ratio": "9:16"  # 或 "16:9"
})
video_url = response.json()["video_url"]
```

---

## ⚙️ 配置说明

关键配置项在 `config.toml` 中：

```toml
# LLM 提供商选择
llm_provider = "deepseek"  # deepseek / moonshot / gpt4free / ollama 等

[llm_providers.deepseek]
api_key = "your-api-key-here"

# 视频素材 API（可免费申请）
pexels_api_keys = ["your-pexels-key"]
```

---

## 💡 适用场景

- 📱 **自媒体内容创作** — 批量生成抖音/B站/小红书视频
- 🏢 **企业营销** — 快速制作产品介绍视频
- 📚 **知识科普** — 将文章内容自动转成视频
- 🤖 **AI 演示** — 为 AI 项目自动生成 demo 视频

---

## 🆚 对比同类项目

| 特性 | MoneyPrinterTurbo | 其他方案 |
|------|-------------------|---------|
| 素材来源 | Pexels 无版权高清素材 | 需自行准备 |
| 字幕生成 | 自动 + 可调样式 | 多数不支持 |
| 多平台尺寸 | 竖屏+横屏都支持 | 通常只支持一种 |
| 模型支持 | 10+ 种 LLM | 通常只支持 OpenAI |
| 部署方式 | WebUI / API / Docker | 多为命令行 |

---

## 🔗 链接

- GitHub：https://github.com/harry0703/MoneyPrinterTurbo
- 官网：https://moneyprinterturbo.com
- Discord 社区（英文）：https://discord.gg/moneyprinterturbo

---

**相关标签**：AI视频生成 · 自动化 · 短视频 · LLM应用 · 内容创作
