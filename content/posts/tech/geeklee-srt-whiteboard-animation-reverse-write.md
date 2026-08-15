---
title: "SRT 白板动画：把字幕变成一支会画画的笔"
subtitle: "深入解析 geeklee/srt-whiteboard-animation 的 mask 编排 × stream 画法"
date: "2026-08-15T14:30:00+08:00"
draft: false
slug: "geeklee-srt-whiteboard-animation-reverse-write"
github_repo: "geeklee/srt-whiteboard-animation"
source_key: "gh:geeklee/srt-whiteboard-animation"
description: "这不是又一个 AI 视频生成项目，而是一份把 SRT 字幕变成 16:9 白板手绘动画的协作剧本：mask 编排管顺序，stream 画法管笔触，7 个 stop-and-wait gate 把 AI 拽回可控范围。"
categories: ["技术笔记"]
tags: ["开源项目", "白板动画", "OpenCV", "Python", "AI Agent", "skill", "流式笔迹"]
keywords: ["srt-whiteboard-animation", "白板动画", "手绘视频", "mask 编排", "stream 画法", "OpenCV", "AI Agent skill", "张-苏细化", "骨架追踪", "墨迹聚类"]
toc: true
---

## 一句话判断

这不是一个 AI 视频生成项目，而是一个**让 AI 像真人画师一样、按你节奏画白板动画的协作剧本**。它的真贡献不在渲染算法，而在"mask 编排 + stream 画法"两条主线的对齐，外加七道 stop-and-wait 关卡——后者才是它拒绝变成"全自动出片机"的核心防御。

如果你需要的不是"一键生成 50 条短视频"，而是"把口播字幕转成教学/科普用的白板动画、且每一步都能停在人手里"，这个仓库值得读完。

---

## 系统地图：一张图看清两条主线

| 主线 | 解决什么问题 | 在哪个文件 | 关键数据/不变量 |
|---|---|---|---|
| **mask 编排** | 哪个区域、在什么时间、可以露多少 | `render_stream_whiteboard.py`（`RegionStreamRenderer`） | 允许掩码 = 矩形 `region` - 后续区域 - `protectedRegions` |
| **stream 画法** | 笔尖怎么沿真实墨迹走、落墨顺序是什么 | `stream_render.py`（`cluster_ink_streams` / `trace_8connected`） | 主体 → 文字 → 局部轮廓 三档优先级 + 张-苏细化骨架 |
| **字幕分镜** | 把一段口播切成 25–35 秒一幕 | `parse_srt.py` | `target=30s / min=25s / max=35s` 三档默认 |
| **可视化编辑** | 让人在浏览器里改 `annotation.json` 的区域/顺序/时序 | `assets/preview.html`（用 File System Access API） | 编辑框是矩形代理，不是动画画面 |
| **多幕拼接** | 把各幕 MP4 顺序合并 | `merge_scenes.py` | 优先 ffmpeg `-c copy` 无损，回退 PyAV 重编码 |

两条主线的**接缝**只有一个文件：`render_stream_whiteboard.py` 把 `stream_render.py` 的笔迹算法包装成"按 mask 时序逐区域作画"。接缝处的关键不变量是 `allowed_mask = region − later_regions − protectedRegions`——后续区域天然不会被提前露线。**mask 不变量是这套编排的核心防线，没有它，整套 mask 机制就会塌成"逐区域矩形擦除"那种老把戏。**

仓库仅 ~3050 行（Python 1792 行 + SKILL.md 154 行 + README.md 169 行），没有任何训练/推理/外部 LLM 调用——它全部依赖 OpenCV + NumPy + ffmpeg/PyAV，纯本地可跑通。

---

## 一段 30 秒字幕会流过哪些代码

为了把抽象机制串成具体的链路，我用 README 自带的"猴子山抢香蕉"案例走一遍。源 SRT 大致是：

> 字幕 1：猴子山上，一只小猴子坐在假山顶端，手里拿着一根香蕉。
> 字幕 2：突然，一只大猴子从旁边冲了过来，一把抢走了香蕉。
> 字幕 3：旁边围观的小朋友们都惊呆了，纷纷鼓掌大笑起来。

整段口播被 `parse_srt.py` 切成 3 幕，每幕 25–35 秒。`scene-01-monkey-mountain-banana.annotation.json` 是第一幕的真实标注：

```json
{
  "canvas": { "width": 1672, "height": 941 },
  "sceneDurationMs": 8600,
  "elements": [
    { "id": "left",   "sequence": 1, "region": { "x": 20,   "y": 120, "width": 540, "height": 780 }, "reveal": { "startMs": 300,  "durationMs": 2600 } },
    { "id": "center", "sequence": 2, "region": { "x": 560,  "y": 100, "width": 560, "height": 800 }, "reveal": { "startMs": 3000, "durationMs": 2600 } },
    { "id": "right",  "sequence": 3, "region": { "x": 1120, "y": 140, "width": 532, "height": 760 }, "reveal": { "startMs": 5700, "durationMs": 2400 } }
  ]
}
```

这段标注里的三件事值得拎出来：

1. **`sequence` 是事件顺序，不是从左到右**——这里刚好左右分布，但仓库反复警告：标注顺序必须来自字幕叙事，不能来自视觉坐标。左右分布只是本案例的巧合。
2. **`startMs` 在同一幕内不重叠**——`300 → 3000 → 5700` 串行作画（stream 是一支笔在动，不是多支并发）。每个区域的 `durationMs` 由该区域对应字幕长度决定（README 默认 150 像素/秒 × 绘制距离为初始估算）。
3. **`protectedRegions` 在本例空数组**——因为三个主体左右不相交。一旦主体交叠（比如人站在树前），就必须把"会被遮挡的部分"加到先画元素的 `protectedRegions` 里，否则笔尖会"穿透"遮挡物把后续元素提前露线。SKILL.md 对此有专门说明（"对于相互遮挡的对象，在较早元素的 `protectedRegions` 中标出需要延后显示的区域，避免后续内容提前露出"）。

走一次 `render_stream_whiteboard.py` 时，一次渲染会话的具体动作是：

1. 把原图按 `cap_long_edge=1080` 缩放，并对齐到 `grid_edge=10` 的偶数倍（视频编码要求偶数尺寸）。
2. 对每个元素：算 `allowed_mask` → 按 `cfg.ink_path_mode`（`grid` 或 `skeleton`）生成笔迹路径 → 起笔段按 ink:color = 2:1 切分帧 → 添彩段用 `contour-wipe`（默认）或 `brush`。
3. 全部画完后补 `sceneDurationMs`，并保证结尾至少停留 0.5 秒完整原图。
4. mp4v 原始流再交给 `transcode_h264`——优先 ffmpeg CRF=20，回退 PyAV CRF=28。

每一步都做最朴素的事，但**只有当 mask 不变量在每帧都成立**，这套朴素才能拼出"笔尖沿线滑行"那种连续感。

---

## stream 画法的细节：不是把所有墨迹串成一条

第一次读 `cluster_ink_streams` 时我以为它就是把墨迹格按"最近邻"串起来——但它做了四件更细的事：

**1. 先把墨迹按语义分档，再决定串法**

```python
if index == subject_index:
    kind, rank = "subject", 0
elif height >= 2 and width / height >= 2.2 and density >= 0.5:
    kind, rank = "text", 1
else:
    kind, rank = "contour", 2
```

最大连通域是主体（subject），高宽比 ≥2.2 且密度 ≥0.5 的是文字（text），其余是局部轮廓（contour）。**这三档不是装饰——它们决定下游的串法**：主体走密度梯度游走，文字横向按段扫，局部轮廓默认也走密度游走。文字按段扫是这套算法最有"人味"的一段：它把整段切成 4 列宽的小段，段内用最近邻沿墨迹走，避免"画一块字没画完就跳到下一段从顶部开始"的回头补笔感。

**2. 大块之间用"出口到入口最近"动态串联（`stream_render.py` `_chain_region_paths`，约第 501 行）**

主体画完后，算法在剩余 stream 里挑"入口离当前出口最近"的那一支，必要时整条反向。这一步把"主+局部+文字"串成一条连贯笔迹，模拟"画完大结构，落到最近的小细节"。

**3. 桥连接会自动断（`stream_render.py` `_split_bridge_connected_component`，约第 196 行）**

这是个我差点漏掉的鲁棒性细节：算法会在垂直投影的"谷"处把"只有窄桥连成一片"的大连通域劈成两块——例如一条横贯地平线把山、人物、围观人群连成一个连通域时，算法会沿最宽的稀疏带劈开，避免笔尖在三个对象之间乱跳。这条规则的最小边长阈值是 20 格（`min_side_cells=20`），远比"只看连通性"更稳。

**4. 网格路径里藏了一个"抬笔"信号**

`_build_stroke_samples`（`stream_render.py` 第 1216 行附近）里有个细节：相邻两格的中心距如果超过 √2（约 1.41 格），就把这一段标为"抬笔"——渲染器跳过这一段，不插值、不落墨。这是为了处理"非相邻连通域"（比如两个独立小对象被同一个 path 串起来），中间留一段空白，避免笔尖"飞过去"画出诡异直线。

更精细的笔迹则来自 `_lay_down_ink_skeleton`（skeleton 模式）：先用 `_zhang_suen_skeleton` 把线稿细化到 1px 骨架（`_build_skeleton_path`，`stream_render.py` 第 1098 行附近），再用 `trace_8connected` 做 8 邻接追踪——关键在于交叉点选"最直的未访问边"继续走（`_choose_next` 用余弦相似度），所以 T 型/十字交叉处不会冒出三角形碎笔画。骨架追踪后再用 Chaikin 平滑 + 等距重采样（`_resample_stroke_points` + `_chaikin_smooth`），去掉像素锯齿。

---

## mask 不变量为什么是编排层防塌的关键

把 `allowed_mask` 单独拎出来说，是因为它**承担了"未开始区域不会提前露出"这一整套防御**——一旦它失守，后面所有精巧的笔迹算法都会暴露在"画面穿帮"的尴尬里。

计算式只有一行：

```python
mask[y0:y1, x0:x1] = True  # 本区域的矩形
for later in later_elements: mask[ly0:ly1, lx0:lx1] = False  # 扣除后续区域
for prot in element["reveal"]["protectedRegions"]: mask[py0:py1, px0:py1] = False  # 扣除保护区
```

但这个式子的工程含义需要拆三层：

1. **未来区域天然被屏蔽**——渲染器按 `sequence` 排序遍历，后续区域对应的像素在 `allowed_mask` 里为 False，落墨时直接被 `& allowed` 过滤掉。这意味着你**不需要在每个区域单独判断"我会不会碰到未来的内容"**，mask 帮你做完了。
2. **本区域内的交叠用 `protectedRegions` 显式声明**——比如人站在树前，先画树时把"会被人的身体盖住的部分"加进 `protectedRegions`，画完后这块被 `allowed_mask` 屏蔽——画人时再揭。少了这一步，渲染器只会按墨迹像素走，完全不"知道"哪些是背景、哪些是遮挡物。
3. **预览台用 destination-out 演示同一不变量**——`assets/preview.html` 的矩形代理在画布上用 `destination-out` 把后续区域擦掉，等价于 mask 机制在视觉上的演示。这样编辑时看到的"未画区域不显示"和最终成片一致，不会出现"预览看起来对、成片穿帮"。

更妙的是 `direction` 字段：**它只控制预览台的矩形代理演示方向，不决定真实笔迹路径**。真实笔迹由骨架/网格自动生成，方向是算法的副产品。这是把"编排层"和"画法层"做正交解耦的关键——改笔迹风格不需要改 mask，改 mask 时序不需要重算笔迹。

---

## contour-wipe：让颜色沿着线蔓延，而不是沿着笔迹刷

添彩段的默认模式 `contour-wipe` 是个反直觉的设计：

```python
# 阻力场：轮廓处阻力≈1，逐行按 decay=0.86 指数衰减
# 揭示前沿遇高阻力被扣减 delay_px=12~52 像素
threshold = lead + wave[None, :] - resistance * delay_px
reveal = ys <= threshold
self.drawn[reveal] = color_src[reveal]
```

它不是"颜色沿笔迹轨迹刷"，而是"颜色从屏幕顶部向下扫一道水波前沿"。这道前沿遇轮廓先卡住（阻力≈1 → 扣减像素 → 卡一会儿），再随着下方的指数衰减阴影缓慢越过，形成"颜色沿着线蔓延"的观感。

为什么选这种风格而不是 `brush`（沿轨迹刷）？因为**对于白板动画，颜色"沿墨迹蔓延"比"沿笔迹刷过"更接近真人画师加水彩/马克笔的视觉直觉**——画师不是一笔一笔把颜色涂完，而是先让墨线干一会儿，再用大笔蘸色从顶部漫过去。

水波前沿由双频正弦叠加（`wave_px1 = max(24, W/20)` + `wave_px2 = max(8, W/72)`），不是平直的横线——这是为了让"涂色前沿"在视觉上不像 PPT 切换。笔尖同时做 `wipe_blocks=18` 趟横向来回扫动（奇数趟反向），并把光标 y 设为"当前列已揭示的最底行"，形成"笔尖贴着涂色前沿走"的视觉一致。

decay=0.86 意味着每行下方约 4.6px 阻力减半——这是经验值调出来的（`Config.wipe_decay = 0.86`，`stream_render.py` 第 77 行）。太快（0.95+）颜色会一口气越过轮廓，太慢（0.7-）颜色卡在轮廓上方不动。SKILL.md 里没写为什么是这个数，但从仓库 622 stars / 115 forks 的社区反馈看，这个值是大量实践后的稳态。

---

## 七道 stop-and-wait 关卡：协作剧本的真正防御

读完脚本层之后，**真正让这个项目区别于"AI 出片流水线"的是 SKILL.md 的工作流**。它把整套流程切成 7 步，每步完成后必须停止并等待用户明确确认：

1. 读字幕、出配图策略（不生成图片）
2. 生成线稿
3. 标注 + 打开预览台
4. 生成区域编号预览图
5. 在预览台调整并保存
6. 命令行渲染成片
7. 多幕合并

SKILL.md 用非常硬的措辞禁止把"未回复""此前的笼统授权""用户没有反对"视为确认：

> 用户要求修改上一步时，只重做该步，并在完成后再次等待确认。

唯一的连带动作是第 3 步标注 JSON 创建完成后**自动打开预览台**——这是第 3 步的交付，不需要为"打开预览台"另行等待确认（"若浏览器的 File System Access API 要求用户手势，使用浏览器界面选择这个已确定的目录；不得因此向用户索要额外确认或改为让用户自行打开预览台"）。

**这套防御的意义在哪儿？** 因为 AI 在多模态创作里有两个反复犯的错：
- 在分镜/线稿/标注未定稿时就开始渲染，浪费算力和人审稿时间。
- 把"我默认用户接受这个分镜"作为推进理由，结果成片和用户预期差十万八千里。

七道关卡用工程化的方式把这两种错堵死。**它本质上是把"AI 应该每步确认"的工程直觉变成了一份可机械执行的 SOP**——任何想把这个 skill 用成"全自动出片流水线"的人，在第 3 步就会被预览台挡住。

---

## 这套设计适合谁用、谁可以等等

**适合：**

- 把口播字幕/课程/科普内容转白板动画的人。`sceneDurationMs` 自动来自字幕跨度，分镜建议由 25-35 秒节奏生成，标注字段直接对应"场景铺垫 → 关键人物 → 动作冲突 → 反应结果"叙事四段。
- 不信任 AI 自动出片、但愿意用 AI 加速中间环节（解析/标注/调时序）的创作者。预览台的存在意味着你拿到的不是"AI 替你拍的片"，而是"AI 按你节奏画的分镜"。
- 想把白板动画做成团队标准交付物的小型工作室。`agents/openai.yaml` 直接给 OpenAI Agent 用，可以塞进更大的内容生产流水线。

**可以等等：**

- 需要"一键生成 50 条短视频"的人——这不是它的设计目标，强行自动化会破坏七道关卡的防御。
- 没有"先看字幕、再看图、再标注"耐心的人——这套工作流的代价是你必须先当半个分镜师。
- 想做电影级复杂构图的项目——`#F5EBD7` 暖米黄底 + 深灰素描线 + 红橙蓝点缀的视觉规范明确锁定在 Notion 涂鸦美学，不适合复杂场景。

**从哪里开始：**

1. `python scripts/prepare_env.py` 建虚拟环境（第一次跑可能要几分钟装 opencv/numpy/av）。
2. 拿一段 1-2 分钟的口播 SRT 试 `parse_srt.py`，看分镜建议是否符合你的内容节奏。
3. 用一张简单的线稿 + 3-4 个元素跑 `render_stream_whiteboard.py`，先不调参数，看默认效果。
4. 再打开 `assets/preview.html` 加载目录，调区域/顺序/时序。
5. 多幕场景再加 `merge_scenes.py`。

---

## 常见坑与排错

下面这些是 README + SKILL.md 没明说、但跑起来一定会撞上的事：

| 坑 | 现象 | 修复 |
|---|---|---|
| **预览台加载文件夹失败** | `assets/preview.html` 点"打开文件夹"无反应或报权限错 | 仅 Chrome / Edge 支持 File System Access API；Safari / Firefox 必须下载 JSON 后手动覆盖原文件（SKILL.md 第 6 节），没有 in-place 编辑 |
| **笔尖不贴合原图墨迹** | 默认 `--ink-path grid` 让笔尖走网格中心，看起来"沿格跳" | 改用 `--ink-path skeleton` 走骨架追踪，更贴合原图线条，但渲染更慢 |
| **上色看起来"涂过墨线"** | 颜色一把刷过轮廓、没有"沿墨线蔓延"感 | 默认 `--color-fill contour-wipe` 已经做了阻力场；如果还像"涂"，调高 `--wipe-delay-ratio`（如 0.06）让前沿在轮廓处多停一会 |
| **`transcode_h264` 回退到 mp4v** | 视频某些播放器（如微信内置）播不出来 | 装系统 ffmpeg 或 `pip install av`，mp4v 不是 H.264 |
| **预览台编辑保存了 JSON 但成片没变** | `direction` 改了但笔迹路径没变 | `direction` 仅控制预览台矩形代理演示方向，**真实笔迹由骨架/网格自动生成**——SKILL.md 第 6 节明确写了这条约束 |
| **时序重叠** | 两个区域 `startMs` 设成相同 | 渲染器仍按 `sequence` 顺序处理（不是并发），但视觉上不再是"两支笔同时画"——SKILL.md 写明"stream 是一支笔在动"，重排 `startMs` 不重叠即可 |
| **画到一半蓝屏 / 内存爆** | 1920×1080 全画渲染时 Python 进程吃掉几 GB | 调 `--cap-long-edge 720` 压低输出尺寸；`grid_edge=10` 决定内存占用，谨慎降到 5 以下会变慢 |
| **元素区域超出画布** | `region` 像素越界 | 渲染器会在 `_scaled_rect` 里 clamp 到画布内，但效果会裁掉；SKILL.md 第 4 节明确要求 `region` 必须是画布内整数像素坐标 |
| **bridge split 把一个对象劈成两半** | 垂直投影有"假谷"，导致一个物体被错断 | `min_side_cells=20` 阈值对极小对象不友好，把单元素尺寸调到 ≥ 20 格以上，或临时把 `--ink-path` 切到 skeleton 模式 |

`scripts/prepare_env.py` 的 `--check` 是先看依赖是否齐——失败时末行输出 `ENV_PY=<路径>`，捕获后所有渲染命令前都加这个解释器，能避免"系统 Python 有 cv2 但 venv 没有"的常见踩坑。

---

## 收尾判断：把协作剧本和"AI 出片机"区分开

今天打开 GitHub Trending，能看到两类白板动画项目：一类是纯算法 demo（视频很炫、但需要你写大量脚手架），另一类是 SaaS 平台（视频很丑、但声称一键生成）。**geeklee/srt-whiteboard-animation 走的是第三条路——它承认白板动画本质是"人画"而非"机器生成"，于是把渲染算法打磨到能稳定画出像样的笔迹，又用七道 stop-and-wait 关卡把 AI 牢牢钉在"协作"而非"替代"的位置。**

如果把它的四个核心约束摆出来——mask 不变量（编排层防塌）、stream 算法（画法层笔迹）、七道关卡（协作层强制 stop-and-wait）、暖米黄视觉规范（输出层美学锁定）——它们组合起来解决的不是"如何画得更像"，而是"如何让 AI 介入得刚好"——多一步就越权，少一步就回到纯人工。这种把克制写成工程的纪律，比任何"全自动"承诺都更值得借鉴。

如果你正在做 AI 内容生产工具，最值得从它身上学的不是 contour-wipe 算法，也不是张-苏细化——而是**"哪一步必须停下来等人"这个问题，必须在 SKILL.md 写死，不能让 LLM 自己判断**。

---

## 附录：仓库关键事实卡

| 项 | 值 |
|---|---|
| 仓库 | `github.com/geeklee/srt-whiteboard-animation` |
| 创建时间 | 2026-07-27 |
| Stars / Forks | 622 / 115（截至 2026-08-15） |
| 主语言 | Python（1792 行）+ HTML（preview）+ YAML（agent metadata） |
| 依赖 | opencv-python、numpy、av（PyAV，备选转码） |
| 系统依赖 | ffmpeg（可选，PyAV 缺失时回退） |
| 协议 | MIT |
| 视觉规范 | 暖米黄 `#F5EBD7` + 深灰素描 + 红/橙/蓝少量点缀 |
| 默认节奏 | 每幕 30 秒（min 25 / max 35） |
| 默认渲染参数 | fps=60、grid_edge=10、ink:color=2:1、color_fill=contour-wipe |
| 配套工具 | `agents/openai.yaml` 适配 OpenAI Agent |
| 视觉样例 | `examples/scene-01-monkey-mountain-stream.gif`（README 主图） |

---

## 参考资料

- 仓库主页：https://github.com/geeklee/srt-whiteboard-animation
- 仓库 SKILL.md：https://github.com/geeklee/srt-whiteboard-animation/blob/main/SKILL.md
- 仓库 README：https://github.com/geeklee/srt-whiteboard-animation/blob/main/README.md
- 真实标注样例：https://github.com/geeklee/srt-whiteboard-animation/blob/main/examples/scene-01-monkey-mountain-banana.annotation.json
- Zhang-Suen 细化算法原始论文：Zhang, T. Y., & Suen, C. Y. (1984). A fast parallel algorithm for thinning digital patterns.
- Chaikin 切角平滑：Chaikin, G. (1974). An algorithm for high-speed curve generation.
- File System Access API（浏览器）：https://developer.mozilla.org/en-US/docs/Web/API/File_System_Access_API
- OpenCV `cv2.connectedComponents`（8 连通域标记）：https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html
