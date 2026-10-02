---
title: "yoinks：把 yt-dlp 包进一个体面的终端界面"
date: "2026-10-03T03:52:00+08:00"
slug: "yoinks-terminal-video-downloader"
github_repo: "pablostanley/yoinks"
source_key: "gh:pablostanley/yoinks"
description: "pablostanley开源的终端视频下载工具yoinks（3.4K Stars，TypeScript，MIT），基于yt-dlp支持YouTube、X、TikTok等1800+站点，用Ink做出全屏React终端UI，自动管理yt-dlp/ffmpeg依赖。适合怕广告下载站的普通用户。"
draft: false
categories: ["技术笔记"]
tags: ["CLI", "TypeScript", "开源", "终端", "工具"]
---

# yoinks：把 yt-dlp 包进一个体面的终端界面

> **目标读者**：需要保存视频内容的普通用户、终端工具爱好者、想研究 Ink 全屏 TUI 的前端开发者
> **文章形态**：项目导读 / 快速上手
> **证据来源**：pablostanley/yoinks README 与提交记录（2026-10-02 取证）

## 项目概览

yoinks 的自我介绍直白到近乎挑衅："yoink any video. paste. yoink. done."——粘贴链接、选格式、拿文件，没有弹窗、没有假下载按钮、没有可疑跳转。它是一个终端视频下载工具，覆盖 YouTube、X/Twitter、Instagram、Threads、TikTok 在内的 1,800+ 站点，出自设计师 Pablo Stanley（人类设计工具 Humans for Scale 的作者）之手。

项目 2026 年 7 月中创建，当前 3,405 Stars / 305 Forks，TypeScript，MIT 协议。最近一次提交停在 2026-07-17，README 的 Roadmap 大半未勾选，这是判断其成熟度的重要信号：能用，但处于早期维护节奏。

## 它实际解决了什么问题

yt-dlp 早已是视频下载的事实标准，为什么要再包一层？答案不在能力而在**可及性**。yt-dlp 的命令行参数体系面向的是熟练用户；而搜索"视频下载"的普通人得到的是满是广告陷阱的下载站。yoinks 的定位就在这两者之间：

- 能力层完全复用 yt-dlp——1800+ 站点的支持、格式选择、音频提取都来自它；
- 体验层做了三件事：全屏居中的终端 UI（Ink 渲染）、键盘 + 鼠标双交互（↑/↓ 或 j/k 选格式，yoink 按钮可点击）、零配置依赖管理。

依赖管理值得一提：首次运行时自动下载独立 yt-dlp 二进制到 `~/.yoinks/bin`，不需要系统装 Python；ffmpeg 从 PATH 找，找不到就用捆绑的 `ffmpeg-static` 兜底。对目标用户来说，这意味着 `npm install -g yoinks` 之后不用再装任何东西。

## 快速上手

```sh
# 安装（Node 18+）
npm install -g yoinks
# 或者不装直接试
npx yoinks

# 两种用法
yoinks https://youtu.be/dQw4w9WgXcQ   # 直接进格式选择器
yoinks                                 # 交互式提示输入链接
```

进入格式选择器后，↑/↓（或数字键）选分辨率——列表带预估文件大小——也可以选纯音频 mp3。回车开始下载，文件落在 `~/Downloads`，完成后终端打印完整路径。`esc` 返回，`^c` 退出，退出时会恢复终端的滚动缓冲区（full-screen TUI 的礼貌细节，很多工具不管这个）。

主题处理也见心思：默认 `auto` 主题直接读终端自身的前景/背景色，跟随明暗主题而不靠猜测；`^t` 可在 auto / light / dark 间循环切换。

## 实现拆解：为什么前端开发者应该看一眼

从工程角度，yoinks 最有意思的部分是 UI 栈的选择：**Ink——用 React 写终端界面**。全屏居中布局、可点击的按钮与页脚提示、跟随终端主题，这些都是浏览器里 React 的常规操作，被原封不动搬进了终端。最近几条提交（"stop centering from collapsing spacer rows on odd leftover"）恰好暴露了这类布局在等宽字符网格上的典型麻烦，对想做终端 UI 的人是有参考价值的样本。

构建用 tsup 打包到 `dist/`，`npm run dev` 支持改即重建，`npm run typecheck` 类型检查——一个结构干净的小型 TypeScript CLI 项目。

## 边界与风险

**明确不覆盖**：下载速度、站点兼容性实测（本文未实测，不做推断）。

1. **维护节奏**：提交停在 2026-07-17，Roadmap 里 `--best`/`--mp3` 脚本化参数、播放列表支持、自更新 yt-dlp 二进制均未完成。需要无人值守脚本化下载的场景，现阶段直接用 yt-dlp 更稳。
2. **合规边界**：README 自己说得很清楚——这是个人存档工具，下载内容可能违反平台服务条款，"只下载你有权保存的东西，善待创作者"。这不是免责套话，是使用这类工具前应当真正读的一句话。
3. **本质是封装**：如果你已经熟练使用 yt-dlp，yoinks 提供的增量只有 UI，价值判断因人而异。

**适合人群**：想远离广告下载站、又不想学 yt-dlp 参数的普通用户；想看 Ink 全屏 TUI 实战案例的前端开发者。两类人都能各取所需。

---

**仓库信息**：[pablostanley/yoinks](https://github.com/pablostanley/yoinks) · TypeScript · MIT · 3.4K Stars / 305 Forks · 创建于 2026-07-16 · 无正式 Release（npm 包已发布）
