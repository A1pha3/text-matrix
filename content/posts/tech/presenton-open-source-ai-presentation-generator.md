+++
date = '2026-05-24T00:00:00+08:00'
draft = false
title = 'Presenton：开源 AI 演示文稿生成器'
slug = 'presenton-open-source-ai-presentation-generator'
description = 'Presenton 是一个开源 AI 驱动的演示文稿生成工具，输入脚本或主题即可自动生成结构化幻灯片，支持实时预览和多格式导出。'
categories = ['技术笔记']
+++

# Presenton：开源 AI 演示文稿生成器

## 基本信息

- **语言**: TypeScript + Node.js
- **作者**: presenton
- **链接**: https://github.com/presenton/presenton

## 这是什么

Presenton 是一个开源的 AI 驱动演示文稿生成工具，用户只需提供脚本或主题，AI 即可自动生成结构清晰的幻灯片。项目支持实时预览、多格式导出和一键分享。

## 核心能力

### AI 脚本分析与结构化
输入任意主题或未整理的演讲稿，Presenton 会自动分析内容逻辑，拆分为多个章节与要点，生成符合演示逻辑的结构化大纲。

### 自动排版与视觉设计
基于模板引擎自动完成配色、布局和排版，无需设计经验。支持多种主题模板，可一键切换演示风格。

### 实时预览与编辑
内置实时预览窗口，生成后可随时调整文字、图片和动画效果。所有修改即时生效，方便快速迭代。

### 多格式导出
支持导出为 PPTX、PDF、HTML 和图片格式，兼容 Microsoft PowerPoint、Google Slides 和 Keynote。

### 协作与分享
生成的演示链接可直接分享，支持在线演示模式，观众通过链接即可观看无需安装任何软件。

## 🏗️ 技术架构

```
[用户输入（脚本/主题）]
         ↓
  [LLM 分析引擎] → [结构化大纲]
         ↓
  [模板渲染引擎] → [幻灯片生成]
         ↓
  [预览/导出模块] → [多格式输出]
```

技术栈：TypeScript + Node.js + LLM API，设计上强调零配置开箱即用。

## 💡 使用场景

| 场景 | 说明 |
|------|------|
| 商务演示 | 快速生成方案汇报、产品介绍等商务幻灯片 |
| 学术演讲 | 自动整理研究摘要，生成结构化演讲稿 |
| 教育培训 | 教师制作课程课件，提高备课效率 |
| 技术分享 | 开发者输出技术博客与分享演示 |
| 营销素材 | 快速制作推广方案的视觉版 |

## 🚀 快速上手

```bash
# 安装
npm install -g presenton

# 生成演示
presenton create --topic "AI未来发展趋势" --lang zh

# 导出 PPTX
presenton export --format pptx
```

## 📝 适用人群

- 📊 商务人士（快速制作汇报材料）
- 🎓 教师与培训师（高效备课）
- 🧑‍💻 技术博主与开发者（输出技术分享）
- 📢 营销团队（快速制作推广素材）

## ⭐ 亮点

- 开源免费，无使用限制
- AI 自动生成结构化演示，零设计基础也能做出专业幻灯片
- 多格式导出，兼容主流办公软件
- 支持本地部署，数据完全私有

> GitHub: https://github.com/presenton/presenton