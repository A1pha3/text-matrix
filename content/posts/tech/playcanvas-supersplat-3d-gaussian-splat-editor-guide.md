---
title: "SuperSplat：浏览器里的 3D Gaussian Splat 编辑器完全指南"
date: 2026-05-10T16:30:00+08:00
slug: playcanvas-supersplat-3d-gaussian-splat-editor-guide
categories: ["技术笔记"]
tags: ["3D", "计算机视觉", "开源", "浏览器"]
description: "深入解析 PlayCanvas 开源的 SuperSplat——一款完全基于浏览器的 3D Gaussian Splat 编辑器，涵盖技术原理、本地开发环境搭建、多语言支持及实机体验。"
---

## 什么是 SuperSplat

[SuperSplat](https://github.com/playcanvas/supersplat) 是 PlayCanvas 团队开源的免费工具，用于**查看、编辑、优化和发布 3D Gaussian Splats（3D 高斯泼溅）**。项目目前拥有 **6,400+ GitHub Stars**，完全基于 Web 技术构建，直接运行在浏览器中，无需下载安装任何软件。

**实机地址：** [https://superspl.at/editor](https://superspl.at/editor)

![SuperSplat Editor 界面](https://github.com/user-attachments/assets/b6cbb5cc-d3cc-4385-8c71-ab2807fd4fba)

## 3D Gaussian Splatting 是什么原理

3D Gaussian Splatting（3DGS）是 2023 年 SIGGRAPH 大会上提出的一种革命性场景重建技术。与传统 mesh 或点云不同，它用**三维高斯分布**来表示场景：

- 每个高斯函数定义了一个**位置（均值）、形状（协方差矩阵）和颜色/透明度**
- 渲染时将这些 3D 高斯"泼溅"（splat）到 2D 图像平面，生成高质量新视角图像
- 核心创新：结合了**可微渲染**与**自适应密度控制**，既保证渲染质量，又支持实时交互

**优点：**
- 无需 mesh 拓扑，适合任意形状的真实场景重建
- 训练速度快（几十分钟而非几天）
- 支持实时渲染新视角（60fps+ 在消费级显卡上）
- 编辑相对直观（以 splat 为单位操作）

**缺点：**
- 文件体积大（百万级 splats）
- 对遮挡和镜面反射处理仍有局限
- 无显式几何定义，物理仿真困难

## 本地开发环境搭建

SuperSplat 要求 **Node.js ≥ 20.19.0**，推荐 Node.js 18+。

```bash
# 1. 克隆仓库
git clone https://github.com/playcanvas/supersplat.git
cd supersplat

# 2. 安装依赖
npm install

# 3. 启动开发服务器（自动编译 + 静态服务）
npm run develop

# 4. 打开浏览器访问
# http://localhost:3000
```

> ⚠️ **重要：** 首次使用需**禁用浏览器缓存**：
> - **Safari：** `Cmd+Option+e` 或 `Develop → Empty Caches`
> - **Chrome：** Application → Service workers → 勾选 "Update on reload" 和 "Bypass for network"

改动代码后编辑器会自动重建，刷新浏览器即可看到更新。

### 构建脚本一览

| 命令 | 作用 |
|------|------|
| `npm run build` | 生产构建 |
| `npm run watch` | 监听模式持续编译 |
| `npm run serve` | 静态文件服务（默认 `dist/`） |
| `npm run develop` | **推荐** 同时运行 watch + serve |
| `npm run lint` | 代码风格检查 |

## 核心功能一览

### 编辑能力

SuperSplat 提供了完整的 splat 场景编辑工具链：

- **选择与变换**：框选、点选 splats，支持平移/旋转/缩放变换手柄
- **撤销/重做**：完整的 Edit History 系统
- **场景裁切**：Box Shape、Sphere Shape 等裁切工具
- **序列帧导出**：PLY 序列导出为视频
- **发布优化**：压缩、块级剔除等优化选项
- **相机轨迹**：关键帧动画、轨道相机绑定

### 多语言国际化

SuperSplat 内置了 **9 种语言**，本地化文件位于 `static/locales/` 目录：

| 语言 | 文件 |
|------|------|
| 英语 | `en.json` |
| 德语 | `de.json` |
| 西班牙语 | `es.json` |
| 法语 | `fr.json` |
| 日语 | `ja.json` |
| 韩语 | `ko.json` |
| 巴西葡萄牙语 | `pt-BR.json` |
| 俄语 | `ru.json` |
| 简体中文 | `zh-CN.json` |

**添加新语言只需两步：**

1. 在 `static/locales/` 创建 `<locale>.json`
2. 在 `src/ui/localization.ts` 的语言列表中注册

**测试翻译：**
```bash
npm run develop
# 然后访问
http://localhost:3000/?lng=fr
```

### 技术栈

SuperSplat 基于一套成熟的开源 Web 技术：

- **渲染引擎**：PlayCanvas（WebGL/WebGPU）
- **构建工具**：Rollup
- **语言**：TypeScript
- **UI 组件库**：@playcanvas/pcui（PlayCanvas 自家 PCUI）
- **国际化**：i18next
- **样式**：Sass + PostCSS

## 对比传统 3D 编辑器

| 特性 | SuperSplat | Blender / Maya | InstantNGP |
|------|-------------|----------------|------------|
| 平台 | 浏览器（跨平台） | 桌面应用 | 桌面应用 |
| 编辑对象 | Gaussian Splats | Mesh / 视频 | NeRF / 3DGS |
| 操作门槛 | 低（拖拽为主） | 高（复杂 3D 技能） | 中 |
| 实时预览 | ✅ 原生 WebGL | ⚠️ 插件支持 | ⚠️ 需 CUDA |
| 开源 | ✅ MIT | ✅ GPL | 部分开源 |

SuperSplat 的核心优势在于**零门槛访问**——任何人打开浏览器即可开始编辑 3DGS 场景，无需配置 CUDA 或安装大型软件。

## 实际使用体验

访问 [https://superspl.at/editor](https://superspl.at/editor)，加载一个 .splat 文件（PlayCanvas 提供[示例文件](https://playcanvas.com/supersplat/editor)），即可体验：

- **拖拽旋转**：按住左键拖拽场景，右键拖拽旋转视角
- **框选删除**：用选择工具框选不需要的 splats，按 Delete 移除
- **优化发布**：File → Export 可导出压缩后的 splat 文件

编辑器支持 `.ply`、`.splat` 等格式，拖拽文件到窗口即可加载。

## 总结

SuperSplat 是 3D Gaussian Splatting 生态中一个重要的里程碑——它把过去只能在专业研究工具中操作的 splat 编辑能力，带到了任何有浏览器的地方。开源、Web 原生、多语言支持，加上 PlayCanvas 团队成熟的 WebGL 积累，使得 SuperSplat 成为 3DGS 入门和实际生产的有力工具。

如果你对 3DGS 感兴趣，不妨现在就打开 [superspl.at/editor](https://superspl.at/editor) 试试，或 clone 仓库本地跑起来：

```bash
git clone https://github.com/playcanvas/supersplat.git
cd supersplat && npm install && npm run develop
```