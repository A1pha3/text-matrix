---
title: "SuperSplat：浏览器里的 3D Gaussian Splat 编辑器，v3 重写之后"
date: 2026-05-10T16:30:00+08:00
lastmod: 2026-10-01T00:00:00+08:00
slug: playcanvas-supersplat-3d-gaussian-splat-editor-guide
github_repo: "playcanvas/supersplat"
source_key: "gh:playcanvas/supersplat"
categories: ["技术笔记"]
tags: ["计算机视觉", "开源", "浏览器", "WebGPU"]
description: "PlayCanvas 开源的 SuperSplat 把 3D Gaussian Splat 的查看、清理、优化、发布搬进浏览器。2026 年 9 月的 v3.0 用 WebGPU 重写了渲染器与数据模型，本文梳理它的架构、工具链与实际用法。"
---

## 先说判断

SuperSplat 解决的不是"渲染 3DGS"——查看器已经很多——而是渲染之后的脏活：拿到一份训练输出的 PLY，删掉漂浮点、裁掉多余背景、调好相机动画、压缩体积，最后变成一个能发给别人点的链接。过去这条链路散落在 Python 脚本和桌面软件里，SuperSplat 把它装进浏览器，打开 [superspl.at/editor](https://superspl.at/editor) 就能用，编辑阶段文件不上传，计算全部发生在本地。

2026 年 9 月 8 日发布的 v3.0 值得单独一提：渲染器和数据模型基于 WebGPU 从零重写，官方实测同一个 440 万 splat 的场景（990 MB PLY），编辑器空闲时的 JS 堆内存从 1,557 MB 降到 105 MB。之前"大场景塞不进浏览器标签页"这个根本性限制，被这一版解掉了。项目目前 10,292 Stars（2026-10-01 读数），MIT 许可证，是 PlayCanvas 团队维护的独立开源项目。

## 功能地图

| 板块 | 能做什么 | 入口 |
|------|----------|------|
| 场景编辑 | 选择、变换、删除、裁切、隐藏锁定 splat | 工具栏 + 快捷键 |
| 动画 | 相机位姿关键帧、时间线、循环播放 | 时间线面板（Ctrl+T） |
| 渲染输出 | 视频（mp4/webm/mov/mkv）、截图、全景图 | Image / Video 设置对话框 |
| 导出 | PLY / 压缩 PLY / SOG / SPZ / 查看器包 | File → Export 子菜单 |
| 发布 | 一键发布为可分享的在线查看页 | File → Publish |
| 本地化 | 界面翻译成 9 种语言 | `static/locales/` |

后面按这个顺序展开。

## 三分钟看懂 3DGS

3D Gaussian Splatting 是 2023 年 SIGGRAPH 上发表的场景重建技术。给一组多角度照片，训练出一组带颜色的三维高斯椭球来表示场景：每个高斯有位置、形状（协方差矩阵）、不透明度和球谐系数（视角相关的颜色）。

它和 mesh 的区别在于没有表面拓扑：渲染时把几百万个高斯按深度排序后"泼溅"到屏幕上，直接光栅化。好处是照片级真实感加实时帧率，且训练远快于早期的 NeRF 类方法（原论文口径为几十分钟量级）；代价是数据量大——百万级高斯的 PLY 文件动辄数百 MB——而且没有显式几何，拿去做物理仿真很别扭。

这也解释了 SuperSplat 的生态位置：训练管线（ Nerfstudio、gsplat、Postshot 等）产出原始模型，SuperSplat 负责之后的清理、压缩和交付。

## v3.0 重写了什么

这是理解当前版本的关键。v3 之前（2.x，最终版本 v2.32.5，保留在 [v2 分支](https://github.com/playcanvas/supersplat/tree/v2)），SuperSplat 跑在 PlayCanvas 引擎的 WebGL2 路径上，CPU 负责深度排序，JavaScript 里保存整份场景的浮点副本。场景一大，浏览器标签页就爆内存。

v3.0 把整条渲染管线搬到了 GPU：splat 投影、视锥剔除、压缩、深度排序（GPU 基数排序）、绘制提交全部用 compute shader 每帧执行，CPU 排序 worker 和 WebGL2 路径删除。splat 数据驻留在分块的 GPU 存储里，JavaScript 侧只保留一份轻量的"实例"列表记录可编辑状态（选中、锁定、变换、颜色索引）。直方图、范围选择、颜色匹配、包围盒计算也换成了 GPU compute。

官方在 v3.0 release notes 里给了同一场景（4.4M splats，990 MB PLY）的 v2/v3 峰值 JS 堆对比：

| 操作 | v2 | v3 |
|------|------|------|
| 场景加载后空闲 | 1,557 MB | 105 MB |
| 保存 PLY | 1,722 MB | 623 MB |
| 保存压缩 PLY | 2,982 MB | 1,759 MB |
| 发布 | 1,934 MB | 741 MB |
| 渲染 1080p 视频 | 1,673 MB | 142 MB |

导出路径也改成了流式：PLY、压缩 PLY、SOG、SPZ、工程文件和发布都经由 `@playcanvas/splat-transform` 逐块写出，不再先把整个场景拼进内存。

两个值得知道的连带变化：

- **浏览器要求变了。** v3 强制要求 WebGPU——当前版本的 Chrome 和 Edge、Safari 26 或更高、开启了 WebGPU 的 Firefox。还在用旧浏览器的用户只能用 v2 分支的在线版。
- **新增无排序透明模式。** Preferences → Rendering → Stochastic Alpha 提供 Disabled / Enabled / Movement / Auto（默认）。原理是把 splat 当不透明片元做深度测试、逐片元随机覆盖率采样，省掉排序环节，让千万级高斯的场景在拖动视角时保持流畅；画面静止后再补一帧完整排序的精确渲染。Auto 档按上一帧的 GPU 耗时自动切换。

选择系统同步重构：旧版"表面/穿透"开关拆成两个独立选项——Selection Depth（快捷键 N，只选可见表面上的 splat）和 Selection Footprint（快捷键 M，按整个高斯足迹而不是中心点判定命中），所有二维和三维选择工具都遵循这两个开关。

## 编辑工具链

### 选择

九种选择工具覆盖不同清理场景：

| 工具 | 快捷键 | 适用 |
|------|--------|------|
| 矩形选择 | R | 快速框选屏幕区域 |
| 套索选择 | L | 不规则圈选 |
| 多边形选择 | P | 精确圈选 |
| 笔刷选择 | B | 涂抹选点，`[` `]` 调笔刷大小 |
| 球形笔刷 | Shift+B | 三维空间内的球体涂抹 |
| 泛洪选择 | O | 选出连通区域 |
| 球形选择 | — | 按三维包围球整体选中 |
| 盒形选择 | — | 可平移旋转的三维盒，盒内整体选中 |
| 吸管 | Ctrl+E | 点选取样，按颜色阈值选出相近颜色的所有 splat |

配合 Ctrl+A 全选、Ctrl+Shift+A 取消选择、Ctrl+I 反选、H 隐藏选中（Shift+H 取消隐藏）、Delete 删除，清理一个场景基本不用碰菜单。编辑历史完整支持撤销重做（Ctrl+Z / Ctrl+Shift+Z）。

### 变换与裁切

移动 / 旋转 / 缩放分别绑定 1 / 2 / 3，Shift+C 切换全局与局部坐标系；另有 Orient 工具，拾取场景中的一块表面后把选中对象的局部坐标轴对齐到该表面（法线按 splat 局部轴做吸附），适合把扫描件摆正。裁切用 Box Shape 或 Sphere Shape 工具框出保留区域，删除或剪掉界外内容。

菜单里还有 Duplicate（复制选中 splat 为独立对象）和 Separate（把选中部分拆成新 splat 对象）——把一个场景拆成多个可独立管理、独立导出的层。

### 相机与动画

Orbit 模式（默认）：左键环绕，右键平移，中键 Blender 风格（拖动环绕，Shift 平移，Ctrl 缩放）；按 V 切换到 Fly 模式，WASD 加 QE 飞行，Shift 加速、Alt 减速。F 聚焦选中对象，Shift+F 重置相机。

时间线面板（Ctrl+T）做相机位姿关键帧动画：摆好机位按 Enter 记一帧，空格播放，循环模式支持 none / repeat / ping-pong。这套位姿动画会同时作用于视频渲染和查看器导出——导出的查看器可以带上动画，观众打开就是一段自动巡游。

### 视频、全景与截图

视频渲染（v2 起就有，v3 大幅降低内存占用）支持 mp4 / webm / mov / mkv 四种容器，编码器可选 H.264、H.265、VP9、AV1，分辨率、帧率、码率、透明背景均可配置，源码中的编码级别表覆盖到 8K。投影模式可在标准透视和等距柱状全景（equirect）之间切换，配合水平校正直接输出 360° 全景视频。另有调色面板，参数含色温、饱和度、亮度、黑白点与着色，截图输出同样生效。

## 格式与发布

### 导入

直接拖文件进窗口，或 File → Import。支持格式相当全：

- **点云格式**：`.ply`（含压缩 PLY）、`.splat`、`.ksplat`、`.spz`、`.sog`
- **工程文件**：`.ssproj`——SuperSplat 自己的场景文档，保存/恢复完整编辑状态
- **序列帧**：`frame0001.ply` 式命名的 PLY 序列可作为动画导入
- **配套数据**：COLMAP（常用的摄影测量重建工具）的 `images.txt`、WebP 纹理、LCC / LCC2 打包格式

### 导出与压缩

File → Export 子菜单按格式直接选择，各自带参数：

| 格式 | 说明 | 关键参数 |
|------|------|----------|
| PLY | 标准未压缩格式 | SH 球谐阶数截断 |
| 压缩 PLY | 整数化量化 | 同上 |
| SOG | Spatially Ordered Gaussians：空间排序后量化压缩，纹理存 WebP，官方口径典型比同内容 PLY 小 15–20 倍 | 迭代次数 |
| SPZ | Niantic 的紧凑格式 | 版本 3 / 4 |
| 查看器 | HTML 单文件或 ZIP 包，可内置动画、背景色、FOV | 循环模式 |

其中查看器导出是最快的交付路径：不依赖 PlayCanvas 平台，发一个 HTML 文件，对方双击就能看。

### 发布

File → Publish 把场景发布到 superspl.at，生成公开链接。发布时可写标题描述、覆盖模型与动画设置；百万 splat 以上的场景默认开启 LOD 生成，发布格式从单档 SOG 切换为 Streamed SOG（源码 `publish.ts` 中的 `ssog`）——按距离分块分级的 SOG 变体，远处加载低精度数据，大场景打开更快。

一个完整的工作流大概是：训练输出 900 MB 的原始 PLY → 拖进编辑器删漂浮点、裁掉背景 → 立方体裁切收边界 → 铺几帧相机关键帧 → 存一份 `.ssproj` 留底 → 导出 SOG（可能压到几十 MB）→ 发布链接给客户预览，定稿后导出查看器 HTML 交付。同一段位姿动画在预览链接和交付文件里表现一致。

## 本地开发

要求 Node.js 20.19 或更高（2.x 时代的 README 写的是 18+，升级 v3 后提高了门槛）。

```bash
git clone https://github.com/playcanvas/supersplat.git
cd supersplat
npm install
npm run develop   # watch + serve 并行，自动重建
```

打开 `http://localhost:3000`。开发时需要禁用浏览器缓存，否则改了代码看不到更新：

- **Safari**：`Cmd+Option+E`，或 Develop → Empty Caches
- **Chrome**：DevTools → Network 勾选 Disable cache；旧版 README 曾建议在 Application → Service workers 里勾选 "Update on reload" 和 "Bypass for network"

构建脚本一览（来自 package.json）：

| 命令 | 作用 |
|------|------|
| `npm run develop` | 开发模式：watch + 本地服务并行 |
| `npm run build` | 生产构建（Rollup） |
| `npm run watch` | 监听模式持续编译 |
| `npm run serve` | 静态服务 `dist/` |
| `npm run lint` | ESLint 检查 `src/` |
| `npm run lint:locales` | 校验语言文件键完整性 |

### 技术栈

- **语言/构建**：TypeScript + Rollup，样式 Sass + PostCSS
- **渲染**：PlayCanvas 引擎（v3 起仅用其 WebGPU 路径），WebGPU 类型定义直接引入 `@webgpu/types`
- **UI**：PlayCanvas 自家 PCUI 组件库
- **视频**：mediabunny 在 WebCodecs 之上负责编码参数协商与 mp4/webm/mov/mkv 容器封装
- **导出**：`@playcanvas/splat-transform` 处理流式序列化
- **国际化**：i18next（浏览器语言检测 + HTTP 后端）

### 多语言

界面内置 9 种语言：英语、德语、西班牙语、法语、日语、韩语、巴西葡萄牙语、俄语、简体中文，文件在 `static/locales/`。加一种新语言两步：在 `static/locales/` 放一个 `<locale>.json`，再到 `src/ui/localization.ts` 注册。`npm run lint:locales` 可以检查各语言文件的键是否齐全。测试翻译访问 `http://localhost:3000/?lng=fr`。

## 横向对比与采用建议

| | SuperSplat | Blender + 插件 | 桌面 3DGS 工具（如 Postshot） |
|------|-----------|----------------|------------------------------|
| 形态 | 浏览器，免安装 | 桌面软件 | 桌面软件 |
| 操作对象 | Gaussian Splats | Mesh 为主，splat 靠插件 | splat / NeRF |
| 门槛 | 低：链接直达，拖文件即用 | 高：需 3D 软件基础 | 中：安装 + 显卡要求 |
| 交付 | 在线链接 / HTML 查看器 / SOG / SPZ | 依赖插件导出 | 视软件而定 |
| 开源 | MIT，含完整编辑器源码 | GPL | 多为闭源商业软件 |

注：Blender 本身是 GPL 开源软件；研究中常见的 Instant-NGP 源码公开但采用 NVIDIA 专有许可，不属于开源许可证范畴，引用时别混为一谈。

谁该现在用：手上有 3DGS 训练输出需要清理交付的人——它是这条链路上完成度最高的免费工具；想做 splat Web 展示的前端团队——查看器导出和 SOG 格式就是为这个准备的；想给编辑器加功能的开发者——源码结构清晰，编辑状态与渲染数据分离的设计在 v3 之后更彻底。

可以等等的：需要精确 mesh 编辑或布尔运算的场景——splat 没有拓扑，SuperSplat 也给不了；对 WebGPU 支持有硬性兼容要求（老浏览器、企业锁定的浏览器版本）的环境——用 v2 分支过渡，等浏览器基线追上来。

真正值得留意的竞争对手反而在上游：训练管线自带清理功能（比如 Nerfstudio 生态的脚本）和垂直商业工具会不断蚕食"编辑"这一环。SuperSplat 的护城河是浏览器形态加 PlayCanvas 的 Web 渲染积累——v3.0 那次重写说明这个团队打算把优势继续拉开，而不是维持一个够用的玩具。

## 链接

- 仓库：https://github.com/playcanvas/supersplat
- 在线编辑器：https://superspl.at/editor
- 用户手册：https://developer.playcanvas.com/user-manual/gaussian-splatting/editing/supersplat/
- PlayCanvas 博客：https://blog.playcanvas.com
- 论坛：https://forum.playcanvas.com
- Discord：https://discord.gg/T3pnhRTTAY
