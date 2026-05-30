---
title: "MoneyPrinterTurbo: 一键生成高清短视频的AI工具"
date: "2026-05-30T13:13:57+08:00"
slug: "moneyprinterturbo-ai-video-generation"
description: "MoneyPrinterTurbo 只需提供一个视频主题或关键词，即可全自动生成文案、视频素材、字幕和背景音乐，合成高清短视频。支持 WebUI 和 API，覆盖竖屏/横屏，集成 DeepSeek/Moonshot/Gemini 等多模型。"
draft: false
categories: ["技术笔记"]
tags: ["AI视频", "短视频生成", "Python", "Streamlit", "LLM"]
---

## 项目概览

**MoneyPrinterTurbo** 是一个利用 AI 大模型，一键生成高清短视频的开源工具。只要输入一个视频主题或关键词，系统会自动完成：

- AI 生成视频文案
- 自动剪辑视频素材
- 生成字幕（可调整字体、位置、颜色）
- 添加背景音乐
- 输出高清合成视频

项目地址：[harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo)，⭐ 70.2k，GitHub Trending 今日上榜。

## 核心能力

### 多种视频尺寸

| 类型 | 分辨率 | 适用场景 |
|------|--------|----------|
| 竖屏 | 1080×1920 | 抖音、快手、视频号 |
| 横屏 | 1920×1080 | YouTube、B站 |

### 支持的 LLM 提供商

OpenAI、Moonshot、Azure、gpt4free、one-api、通义千问、Google Gemini、Ollama、DeepSeek、MiniMax、文心一言、Pollinations、ModelScope。

> 中国用户推荐使用 **DeepSeek** 或 **Moonshot**，国内可直接访问，注册即送额度。

### 视频素材来源

项目配套提供无版权高清素材，也支持使用本地素材。字幕生成支持 Edge（快速）和 Whisper（高质量）两种模式。

## 快速开始

### 方式一：Windows 一键启动

下载一键启动包（当前版本 v1.2.6），解压后运行 `update.bat` 更新到最新代码，再运行 `start.bat` 启动。

### 方式二：Docker 部署

```bash
git clone https://github.com/harry0703/MoneyPrinterTurbo.git
cd MoneyPrinterTurbo
docker-compose up
```

启动后访问 http://127.0.0.1:8501 打开 Web 界面，API 文档位于 http://127.0.0.1:8080/docs。

### 方式三：本地手动部署

```bash
git clone https://github.com/harry0703/MoneyPrinterTurbo.git
cd MoneyPrinterTurbo
uv python install 3.11
uv sync --frozen
# 安装 ImageMagick（字幕渲染依赖）
brew install imagemagick  # macOS
# 启动 WebUI
uv run streamlit run ./webui/Main.py --browser.gatherUsageStats=False
```

## 技术架构

项目采用 MVC 架构，核心模块：

- **webui/**：Streamlit Web 界面
- **app/**：核心业务逻辑
- **resource/**：素材资源（背景音乐、字幕字体）
- **config.example.toml**：配置文件，配置 LLM API Key 和素材源

## 适用边界

- ✅ 批量生成同主题短视频
- ✅ 快速产出营销/科普视频
- ❌ 不适合需要精确控制视频内容走向的场景
- ❌ 依赖网络访问云端 LLM 和素材源

配合 [reccloud.cn](https://reccloud.cn) 可在线直接使用，无需部署。

---

阅读路径：README → config.example.toml → webui/Main.py → app/ 核心逻辑。