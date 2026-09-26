+++
github_repo = "roboflow/supervision"
source_key = "gh:roboflow/supervision"
date = '2026-05-14T20:17:49+08:00'
lastmod = '2026-09-19T00:00:00+08:00'
draft = false
title = 'supervision 的模型无关，来自它放弃推理'
slug = 'supervision-computer-vision-toolbox'
description = 'supervision 常被介绍成模型无关的计算机视觉工具箱，这个说法没错但没说到点上：它之所以能接住 17 种模型输出，是因为它不做前处理、不调模型、不解码输出。本文按 0.30.4 实机核查它的 Detections、标注器、数据集工具与视频链路，并把 OpenCV 降为可选依赖之后必须重新判断的几件事一并写清。'
categories = ['技术笔记']
tags = ['计算机视觉', 'Python', '开源', '工具']
+++

supervision 常被介绍成「模型无关的计算机视觉工具箱」。这句话没错，但读者会从里面读出相反的意思：以为它费力做了一层适配，把各家模型的差异抹平了。

0.30.4 拆到运行层面，结论是反过来的：它之所以什么模型都能接，是因为它**一步推理都不做**，不前处理、不调模型、不解码输出，只接受一个已经算好的坐标数组。0.30.0 那次把 OpenCV 从必需依赖降成可选，正好把这件事挑明了。真要替你做视觉前处理的库很难离开 OpenCV，而它可以。

下面按这个判断展开：中心数据结构长什么样、哪些代码由它替省、0.30/0.31 两个版本断点上有哪些名字已经不能再用，以及什么场景不该引入它。

## 目录

- [1. 判断：它对接得多，是因为它做得少](#1-判断它对接得多是因为它做得少)
- [2. 仓库现状与核实口径](#2-仓库现状与核实口径)
- [3. 系统地图：一个类型，三圈下游](#3-系统地图一个类型三圈下游)
- [4. Detections：六个字段与薄到只有一步的连接器](#4-detections六个字段与薄到只有一步的连接器)
- [5. 后处理挂在数据结构上，而不是挂在模型上](#5-后处理挂在数据结构上而不是挂在模型上)
- [6. 32 个标注器的两条分岔](#6-32-个标注器的两条分岔)
- [7. 数据集工具：五种格式与一个必填的 yaml](#7-数据集工具五种格式与一个必填的-yaml)
- [8. 视频与显示里已经没有 VideoSource 了](#8-视频与显示里已经没有-videosource-了)
- [9. 0.30.0 的分水岭：OpenCV 从必需变成可选](#9-0300-的分水岭opencv-从必需变成可选)
- [10. 怎么读本文的性能数字](#10-怎么读本文的性能数字)
- [11. 跟踪正在被搬出库](#11-跟踪正在被搬出库)
- [12. 一次任务如何流过整个系统](#12-一次任务如何流过整个系统)
- [13. 哪些活不该交给它](#13-哪些活不该交给它)
- [14. 装不上、画不出时按症状排查](#14-装不上画不出时按症状排查)
- [15. 采用顺序：谁先上、谁再等](#15-采用顺序谁先上谁再等)
- [16. 五个自测题](#16-五个自测题)
- [17. 下一步读哪份代码](#17-下一步读哪份代码)
- [18. 维护指引：本文断言的核实方法与失效条件](#18-维护指引本文断言的核实方法与失效条件)
- [参考来源](#参考来源)

## 1. 判断：它对接得多，是因为它做得少

「模型无关」在多数库里意味着一层抽象：定义一个接口，各家实现一遍，再由调度器选一个。supervision 没有这一层。它定义的是一份**数据契约**——只要你能把结果写成 `(N, 4)` 的左上/右下角坐标数组，你就已经接进来了。

由此它的三件「不做」各自成立：

| 通常由 pipeline 库承担的一步 | supervision 的做法 | 直接后果 |
|---|---|---|
| 前处理（resize、归一化、色彩空间转换） | 不提供对应函数 | 不绑定任何输入约定，图像从哪来它不问 |
| 调模型 | 没有模型加载、没有设备管理 | 包目录内只有 3 个文件出现 `torch` 字样（不含 tests 与 examples），且 `import supervision` 不会加载它 |
| 后处理成框 | 不做解码，只接收成品框 | NMS 等反而是它做的（第 5 节），因为那一步只需要坐标 |

第三行容易被误读，值得单说：后处理它其实保留了，只是只保留**不依赖模型形态**的那部分。NMS、Soft-NMS、合并、按区域筛选，全都能在拿到坐标之后独立发生，于是这些功能可以一次实现、十七家复用。真要接一个新库，写连接器的人只需要知道对方把框放在哪个属性上。

`from_ultralytics` 与 `from_transformers` 之间没有代码结构上的区别，这个「薄」本身就是它的架构论点。所以读这套库正确的两个问法是：我的检测结果能不能被压成 `Detections`；它替我省掉的画图、几何判定与格式转换代码有多少。第 12 节给一条完整链路，把这几层串一次。

## 2. 仓库现状与核实口径

下表数字在 2026-09-19 采集，来源与方法写在第 18 节。这类清单最容易过期，所以把口径钉死在「哪个 API（应用程序接口）字段、哪个分支」上，而不是只给一个数。

| 项 | 值 | 口径 |
|---|---|---|
| 仓库 | [roboflow/supervision](https://github.com/roboflow/supervision) | — |
| Stars / Forks | 50,929 / 4,840 | GitHub API `stargazers_count` / `forks_count` |
| Contributors | 189 | contributors 接口分页计数，不含匿名 |
| Commits | 5,161 | commits 接口 `sha=develop`；`main` 是 4,619 |
| Release 总数 / 最新 | 44 / **0.30.4**（2026-09-17） | releases 接口分页 |
| 开发分支版本号 | 0.31.0.dev0 | `develop` 上的 `pyproject.toml` |
| 默认分支 | `develop` | `default_branch`，不是 `main` |
| 建仓 / 最近推送 | 2022-11-28 / 2026-09-19 | `created_at` / `pushed_at` |
| Python 下限 | **3.10**（classifiers 覆盖 3.10–3.14） | `requires-python` |
| 许可证 | MIT | `License-Expression` |
| 语言构成 | Python 100%（3,309,319 字节） | languages 接口 |
| 直接运行依赖 | 10 个，**不含 OpenCV** | wheel 的 `Requires-Dist` |
| 顶层导出名 | 137（`sv.__all__`） | 导入包后读取 |

那 10 个依赖值得列全，因为「supervision 是个薄库」这件事由它们直接决定：

```text
av>=14.2          defusedxml>=0.7.1     matplotlib>=3.6    numpy>=1.21.2
pillow>=9.4       pydeprecate>=0.9,<0.12   pyyaml>=5.3     requests>=2.26
scipy>=1.10       tqdm>=4.62.3
```

`pydeprecate` 会出现在正式依赖里，说明这个库正同时维护一批弃用与移除计划，第 9 节和第 11 节都要用到它。`av` 是 0.30.0 新加的，用于没有 OpenCV 时的视频解码路径。

## 3. 系统地图：一个类型，三圈下游

137 个导出名看着杂，实际只有一个中心类型，其余都是它的下游。先把三圈边界画清楚，后面的细节才有地方放。

| 圈层 | 成员 | 输入 | 输出 | 是否触碰模型 |
|---|---|---|---|---|
| 中心 | `sv.Detections`、`sv.KeyPoints`、`sv.Classifications` | 坐标数组 | 同一个类型 | 否 |
| 输入适配 | 17 个 `Detections.from_*` | 某家库的原始输出对象 | `Detections` | 否，只做字段搬运 |
| 结构后处理 | `with_nms` / `with_soft_nms` / `with_nmm` / `merge` / `select` | `Detections` | `Detections` | 否 |
| 空间判定 | `PolygonZone` / `LineZone` / `InferenceSlicer` | `Detections` + 几何 | 布尔数组 / 切片调度 | 否 |
| 呈现 | 32 个 `*Annotator`、`ImageWindow`、`ImageSink`、`VideoSink` | `Detections` + 图像 | 改过的图像数组 | 否 |
| 数据与评测 | `DetectionDataset` / `ClassificationDataset`、`ConfusionMatrix`、`MeanAveragePrecision` | 磁盘上的标注文件 | 训练可用的目录 | 否 |

三件事值得单独强调，因为它们决定了 supervision 与常见 pipeline 框架的分工差别：

第一，**它没有 pipeline**。没有调度、没有缓存、没有批推理管理。`InferenceSlicer` 是最接近的东西，但它只负责把大图切成小块、把你的回调叫起来、再把结果拼回去，模型仍然是你传进去的那个函数。

第二，**它几乎不持有状态**。`HeatMapAnnotator`、`TraceAnnotator`、`DetectionsSmoother` 会在实例里累积跨帧数据，0.30.0 给它们补了 `reset()`，正是为了让一个实例能复用于多条视频流。

第三，**它的依赖是一堆可选组合**。要 `from_ultralytics` 你得自己装 ultralytics，要 GeoTIFF 窗口读你得装 `supervision[geotiff]`。库本体只保证中心类型和呈现层不需要任何模型框架。

`sv.KeyPoints` 的模块路径是 `supervision.key_points`；单数拼写的 `supervision.keypoint` 是旧别名，已排进 0.31.0 的移除清单（见第 11 节），别写进新代码。

## 4. Detections：六个字段与薄到只有一步的连接器

`sv.Detections` 的构造签名就是它的全部世界观：

```python
Detections(
    xyxy:       ndarray,          # (N, 4) 左上/右下角坐标，必填
    mask:       ndarray | CompactMask | None = None,
    confidence: ndarray | None = None,
    class_id:   ndarray | None = None,
    tracker_id: ndarray | None = None,
    data:     dict = <factory>,   # 任意自定义字段，按 (N,) 对齐
    metadata: dict = <factory>,   # 整份检测共享的元信息
)
```

签名里 7 个参数，第 4 节标题却写「六个字段」，差别在 `metadata`：它是整份检测共享的，不随行切割，所以按行对齐的检测字段一共六个（`xyxy`、`mask`、`confidence`、`class_id`、`tracker_id`、`data`）。这六个里只有 `xyxy` 必填，而且校验严格到形状：只给一个 `...` 或者一维数组都会当场抛 `ValueError`。这不是吹毛求疵：`data` 里的每个值都必须能按第 0 维切成 N 份，而自定义字段错位是最容易埋进下游 bug 的地方。

一份最小可用的构造，配合它自带的只读派生量：

```python
import numpy as np
import supervision as sv

detections = sv.Detections(
    xyxy=np.array([[50.0, 40.0, 180.0, 210.0],
                   [220.0, 90.0, 330.0, 260.0]]),
    confidence=np.array([0.87, 0.64]),
    class_id=np.array([0, 2]),
)

print(len(detections))          # 2
print(detections.area)          # [22100. 18700.]
print(detections.box_area)      # [22100. 18700.]
print(detections.box_aspect_ratio)
```

`area` 与 `box_area` 都是 float64，在纯框检测上是同一个数；一旦带掩码，`area` 变成掩码像素数而 `box_area` 仍是外接框面积。写统计时选错这个，零售客流的面积分布会整体偏大。

17 个连接器的完整名单，按「输入来自哪里」分：

| 连接器 | 上游 |
|---|---|
| `from_ultralytics` | Ultralytics YOLO |
| `from_yolov5`、`from_yolo_nas` | YOLOv5（上游是 `ultralytics/yolov5`）与 Roboflow 自家的 YOLO-NAS |
| `from_transformers`、`from_deepsparse` | Hugging Face 生态 |
| `from_mmdetection`、`from_paddledet`、`from_detectron2`、`from_tensorflow`、`from_ncnn` | 其余训练/推理框架 |
| `from_inference`、`from_azure_analyze_image` | 云服务（Roboflow Inference、Azure CV AI） |
| `from_sam`、`from_sam3` | 分割模型 |
| `from_easyocr` | OCR，结果是文本框 |
| `from_vlm` | 视觉语言模型输出的坐标文本 |
| `from_lmm` | **已弃用**，指向 `from_vlm`，计划在 0.31.0 移除 |

连接器之间的差别只是「从哪个属性名把数组挖出来」，没有一件是重生活。`from_vlm` 是里面唯一有点内容的：它要解析模型用自然语言或 JSON 吐出的坐标，并且带一层拼写容错。顶层同时导出的 `edit_distance` 和 `fuzzy_match_index` 就是给它用的。这也是为什么大模型那一路值得单独有一个 `sv.VLM` 类去声明各家输出格式的差别。

## 5. 后处理挂在数据结构上，而不是挂在模型上

NMS 这一类操作在很多库里属于模型后处理，supervision 把它做成了 `Detections` 的方法。这个决定看起来只是 API 摆放位置的区别，实际带来两个结果：任何一家模型都能复用同一份去重实现；以及，你可以对着同一批框反复试阈值，不必重新推理。

```python
overlap = sv.Detections(
    xyxy=np.array([[10., 10., 110., 110.],
                   [12., 12., 112., 112.],
                   [300., 300., 400., 400.]]),
    confidence=np.array([0.9, 0.8, 0.7]),
    class_id=np.array([0, 0, 1]),
)

print(len(overlap))                              # 3
print(len(overlap.with_nms(threshold=0.5)))      # 2
softened = overlap.with_soft_nms(sigma=0.5)
print(len(softened), softened.confidence.round(4))
# 3 [0.9    0.1451 0.7   ]
```

`with_soft_nms` 是 0.30.0 加的，测出来的行为差值得留意：硬 NMS 把第二个框直接丢掉，框数从 3 变 2；Soft-NMS 三个都留着，但把重叠那个的置信度从 0.8 压到 0.1451。**框数不变、排序变了**——如果你的下游是按 `confidence` 阈值筛人，那么必须像第二个调用那样传 `score_threshold`，否则 Soft-NMS 等于没过滤。密集人群里硬 NMS 会连带砍掉真实目标，这是它的用武之地；稀疏场景里它只是给自己增加一个需要重调的阈值。

同族的还有 `with_nmm`（非最大合并，把重叠框并成一个而不是丢弃），以及函数版的 `box_soft_non_max_suppression` / `mask_soft_non_max_suppression`。判定重叠的度量可以用 `OverlapMetric` 换，实测枚举里只有 `IOU` 与 `IOS`（交集除以较小板）两项。这一项在 0.30.0 之后应当写成关键字参数：`mask_non_max_merge` 对位置传参会告警，但告警类型是库自己的 `SupervisionWarnings` 而不是 `DeprecationWarning`，值仍然生效，移除点在 0.33.0。

## 6. 32 个标注器的两条分岔

`sv.__all__` 里以 `Annotator` 结尾的名字有 32 个，按字母序从 `BackgroundOverlayAnnotator` 排到 `VertexLabelAnnotator`。把它们当成一个平铺的清单来记没有意义，真正需要知道的是两条把它们分开的轴。

第一条轴是**要不要掩码**。0.30.0 加了一个类级标志 `requires_mask`，但它挂在共同基类上，32 个标注器里有 23 个带这个属性，`sv.BaseAnnotator` 本身不在顶层导出名里。命中 `True` 的只有 3 个：`MaskAnnotator`、`HaloAnnotator`、`PolygonAnnotator`。给一份只有框的结果调用 `MaskAnnotator`，返回值与原图逐像素相同——它静悄悄什么也不画，这是「图怎么改都没变化」这类问题的第一顺位怀疑对象。不要求掩码的 29 个里，喂一份只带 `xyxy` 的结果就能跑通 16 个，把 `class_id` 与 `confidence` 补齐后是 18 个。剩下 11 个要的是别的输入：`EdgeAnnotator` 与 `Vertex*` 一族（共 6 个）收 `KeyPoints`，`LineZoneAnnotator` 要经过 `LineZone` 处理的结果，`PolygonZoneAnnotator` 构造时就得把 zone 传进去，`TraceAnnotator` 要 `tracker_id`，`ComparisonAnnotator` 的 `annotate` 一次收两张图。

第二条轴是**颜色按什么查**。32 个标注器里有 16 个带 `color_lookup` 参数，默认一律是 `ColorLookup.CLASS`，也就是需要 `class_id`；另外 16 个压根不接受这个参数。于是有一个不太符合直觉的现象：

```python
import numpy as np, supervision as sv

bare = sv.Detections(xyxy=np.array([[1.0, 2.0, 30.0, 40.0]]))
scene = np.zeros((50, 50, 3), np.uint8)

sv.MaskAnnotator().annotate(scene.copy(), bare)   # 正常返回
sv.BoxAnnotator().annotate(scene.copy(), bare)
# ValueError: Could not resolve color by class because Detections do not have
# class_id. If using an annotator, try setting color_lookup to
# sv.ColorLookup.INDEX or sv.ColorLookup.TRACK.
```

同样是缺 `class_id`，`BoxAnnotator` 抛异常而 `MaskAnnotator` 不抛。只跑无类别号的原始结果（比如单纯的人体姿态框、或跟踪阶段的临时框）时，第一件事是把 `color_lookup` 显式设成 `sv.ColorLookup.INDEX`。异常文本里同时建议了 `TRACK`，但它更窄——没有 `tracker_id` 时换成 `TRACK` 会再抛一条 `Could not resolve color by track`，而且这句提示默认你以为已经跟踪过。

`annotate(scene, detections)` 是**就地绘制**：实测返回对象与传入的 `scene` 是同一个（`out is scene` 为 `True`），只是顺手把它又还给你一次。所以串联写法是把上一环的输出当下一环的输入，而起点必须是一份副本。

```python
box_annotator = sv.BoxAnnotator()
label_annotator = sv.LabelAnnotator()

annotated = label_annotator.annotate(
    box_annotator.annotate(scene.copy(), detections),
    detections,
    labels=[f"{c} {p:.2f}" for c, p in
            zip(detections.class_id, detections.confidence)],
)
```

`scene.copy()` 不是礼貌写法，是必须的：既然绘制就地发生，不复制的话你的原图在第一帧之后就已经被框污染，下一轮循环画出来的是一张套娃图。

这一层也是 supervision 最值钱的资产所在。32 个标注器覆盖框、标签、掩码、热力图、轨迹线、模糊与像素化处理、旋转框、多边形、顶点系列、对比视图，加上区域标注器和 `PercentageBarAnnotator`。自己写到这里的人大概能估出这套东西的维护量，而它靠 NumPy、Pillow、SciPy 就能跑起来，视频那一路再加一个 PyAV，四者都不需要 OpenCV（见第 9 节）。

## 7. 数据集工具：五种格式与一个必填的 yaml

`sv.DetectionDataset` 负责标注数据的读、切、并、转，这是它区别于「只是个画图库」的理由之一。0.30.0 之后支持的格式是五种，很多文章还停在三种：

| 格式 | 读 | 写 |
|---|---|---|
| COCO | `from_coco` | `as_coco` |
| YOLO（含 OBB） | `from_yolo` | `as_yolo` |
| Pascal VOC | `from_pascal_voc` | `as_pascal_voc` |
| LabelMe | `from_labelme` | `as_labelme`（0.30.0 新增） |
| CreateML | `from_createml` | `as_createml`（0.30.0 新增） |

参数名有个不对称要小心：`as_*` 的路径参数默认是 `None`，为 `None` 时**只在内存里生成不落盘**；而标注的位置，COCO 与 CreateML 无论读写都是单文件（`annotations_path`），其余三种是目录（`annotations_directory_path`）。这两个名字只差几个字符，用错当场 `TypeError`。

`from_yolo` 还需要一个很多人漏掉的必填项：

```python
ds = sv.DetectionDataset.from_yolo(
    images_directory_path="ds/img",
    annotations_directory_path="ds/lab",
    data_yaml_path="ds/data.yaml",   # 必填，没有默认值
)
print(len(ds), ds.classes)           # 4 ['person', 'car']
```

签名上 `data_yaml_path` 没有默认值。类别名来自这个 yaml 而不是图片目录，传 `None` 会直接抛 `FileNotFoundError: 'None'`，报错信息看不出根因。这是它的一个坑点。

切分和合并：

```python
train, test = ds.split(split_ratio=0.75, random_state=7, shuffle=True)
print(len(train), len(test))         # 3 1

merged = sv.DetectionDataset.merge([ds_a, ds_b])
```

`split` 的默认比例是 0.8，且默认洗牌。生产上最要紧的是 `random_state`：不传这个参数，同一个数据集每次切出的验证集都不一样，两次实验的指标就没法直接对比。合并是静态方法，收一个列表。

真实往返可以直接验证：同一批图先 `as_coco` 再 `from_coco` 读回，类别名和图片数都对得上；`as_pascal_voc` 写出的 XML 数量等于图片数。这类往返不保真度是数据集工具的底线测试，值得在自己的数据上过一遍再信它。

## 8. 视频与显示里已经没有 VideoSource 了

**当前版本里没有 `sv.VideoSource`，也没有 `sv.ImageAnnotator`**，而网上多数 supervision 教程仍在这两个名字上写代码。两者在 0.27.0 就已经不存在：0.27.0、0.28.0、0.29.1、0.30.4 四个版本逐一装起来取，均取不到这两个属性，`supervision/utils/video.py` 的源码里也搜不到 `VideoSource` 这个符号。

视频侧现在只有这些：

| 名字 | 作用 |
|---|---|
| `sv.get_video_frames_generator(source_path, stride, start, end, iterative_seek, prefetch)` | 逐帧取图，`prefetch` 是 0.30.0 加的后台解码线程 |
| `sv.process_video(...)` | 整个视频跑一遍回调 |
| `sv.VideoInfo` | 宽高、fps、总帧数；`from_video_path` 探测 |
| `sv.VideoSink(target_path, video_info, codec="mp4v")` | 写视频 |
| `sv.FPSMonitor` | 统计吞吐，注意读 `.fps` 属性而不是调用它 |
| `sv.ImageSink`、`sv.ImageWindow` | 写图片目录；桌面窗口（0.30.0 新增） |

实时摄像头这件事变成**应用自己的事**，官方迁移指南直接建议你用 `cv2.VideoCapture(0)`。这条边界划得有意：解码器、设备路径、掉帧策略在不同场景差别太大，库替你决定反而不合适。代价是：一旦需要读摄像头，OpenCV（或另一套解码方案）就又装回来了。第 9 节那个「摆脱 OpenCV」的卖点在真实项目里能兑现多少，要先看你的输入源。

流式读帧与两种参数写法，可以直接跑通：

```python
frames = sv.get_video_frames_generator("clip.mp4", prefetch=2)
for index, frame in enumerate(frames):
    ...
```

`stride=2` 在一段 40 帧的测试视频上读到 20 帧、`prefetch=2` 仍是 40 帧（它只改解码并发，不改输出序列）。用 `for ... in generator` 的流式写法而不是先攒成列表，是这段代码不爆内存的直接原因：1080p 一帧 6 MB，一分钟素材就是几千帧。

## 9. 0.30.0 的分水岭：OpenCV 从必需变成可选

2026-08-04 发布的 0.30.0 是这套库近期最大的一次结构变动，发布说明给的标题就是「Run supervision without OpenCV」。它新建了一个私有 `supervision/_cv2/` 后端门面，用 NumPy、Pillow、SciPy 加 PyAV 重实现原先所有 OpenCV 调用。

后端选择发生在 **import 时一次，且进程存活期内不再改变**。诊断方式是：

```bash
python -c "from supervision import _cv2; print(_cv2.BACKEND_NAME)"
```

无 OpenCV 时打印 `fallback`，装了则打印 `opencv`；两条分支都跑过。改完依赖必须重启进程，否则 `cv2` 探测不到。这是个只会让人怀疑人生的失败模式：明明装了，supervision 说它在用 fallback。

0.30.0 同时带来五条 breaking change，其中真正需要动代码的是两条：

- **OpenCV 不再默认安装，`opencv-python` extra 也一并取消**。需要 OpenCV 行为就自己 `pip install opencv-python-headless supervision`，两者别混装。
- **Python 3.9 支持终止**（3.9 已于 2025 年 10 月 EOL），下限抬到 3.10。

剩下三条更隐蔽：

- `sv.JSONSink` 改吐原生 JSON 类型，原先 `"0.85"` / `"True"` 这类字符串现在是真的 `float` / `bool`。下游按字符串解析的消费方要改。`CSVSink` 仍是文本。
- `sv.mask_non_max_merge` 改为算精确掩码重叠，并忽略已弃用的 `mask_dimension` 参数。同一个阈值不再对应同一个结果，**必须重调**。
- `Detections.merge()` 在稠密掩码与 `CompactMask` 混合输入时返回 `CompactMask` 而不是 `ndarray`。发布说明称在 1080p / 40 框场景峰值内存降到约 1/2500、快约 13×，这组数是官方自测，未公开相对谁、测哪一段，本文也没有复现，所以第 10 节只报自己量到的那部分。

同期新增的东西按用途分三类。接口补充：`with_soft_nms`、`sv.ImageWindow`、`sv.load_image_from_url`。数据格式与切图：`from_labelme` / `from_createml`，`InferenceSlicer` 的 GeoTIFF 窗口读（配 `sv.WindowedRasterDataset`）与 `batch_size`。状态管理：第 6 节的 `requires_mask` 和三个 `reset()`。余下的改动看发布说明即可。

还有一条不属于 breaking 但会影响锁版本的环境：`av>=14.2` 从 0.30.0 起是必需依赖。0.30.1 又把它改成惰性导入，因为 OpenCV 后端活跃时提前加载 PyAV 会带进重复的 libavdevice。

## 10. 怎么读本文的性能数字

这一节的数字只回答一个问题：**没有 OpenCV 时，画标注到底慢多少**。测的是纯绘制耗时，不含解码、不含推理。

环境：Apple M4，Python 3.11.16，NumPy 2.4.6，`opencv-python-headless`（OpenCV 5.0.0），supervision 0.30.4。负载是一张 1920×1080 的随机噪声底图加 40 个 200×300 的框（带 `class_id` 与 `confidence`），标签文本形如 `cls 3 0.71`；每张图先 `BoxAnnotator` 再 `LabelAnnotator`，每轮 warmup 一次后取 10 轮均值，整个测量重复 5 轮。

| 后端 | `BoxAnnotator` | `Box + Label` |
|---|---|---|
| `opencv` | 0.7 ms（0.6–0.9） | 0.9 ms（0.8–0.9） |
| `fallback`（无 cv2） | 141.3 ms（138.9–142.5） | 298.2 ms（295.0–319.9） |

括号里是 5 轮的最小值与最大值，中位数在括号外。两个后端各自跑在独立进程里（后端在 import 时定死，同一进程测不了两次）。

先说这组数怎么来的：第一轮测量落在 `fallback` 319.9 ms、`opencv` 2.8 ms 这一档，绝对值比后来高出 2 到 3 倍。原因是当时机器上还有别的任务在跑。所以上表取的是安静环境下 5 轮的结果，并且把区间一起给出——**绝对毫秒值在这台机器上就会飘，比值不会**：`fallback / opencv` 在两种测量里都稳定在 200 到 330 倍之间。要引用本文的结论，引用这个量级差。

三件这些数字**支持**的事：文本渲染是开销最大的一项（40 条标签把 `fallback` 从 141 ms 推到 298 ms，而 OpenCV 后端只从 0.7 ms 涨到 0.9 ms）；OpenCV 后端下这条路径基本不花钱；只做可视化验证而不追帧率时，`fallback` 完全够用。

三件它们**不支持**的事，别顺手推过去：

1. 这不是 `fallback` 与 OpenCV 的通用性能比。随机噪声底图对绘制来说是最坏情况：每个像素都要参与，帧与帧之间没有冗余可省，真实相机帧的绝对值会明显偏低。
2. 这里没有解码、也没有模型推理。端到端里 141 ms 是否致命，取决于你的模型本身多少毫秒——模型 8 ms 时它是瓶颈，模型 200 ms 时它无所谓。
3. 帧率结论不能从本文搬到另一台机器、别的框数或别的分辨率。要决策就在自己的素材上重跑这个循环。

另一个必须一起看的结论是**两后端的输出不逐像素相同**。同一批数据用两个后端各渲染一遍，取最后一帧逐字节比对。单帧 6,220,800 个字节里有 120,352 个不同，占 1.93%，最大单字节差 255，差异集中在文本与抗锯齿边缘。这个比例本文重复测过，结果一致。官方迁移指南同样写了这一点。推论很实际：**图像级基线回归测试必须固定后端**，换个后端而不是改代码，就足够让像素 diff 全红。JPEG/WebP 的默认编码质量两侧统一（JPEG 95、WebP 无损），PNG/TIFF 都无损但字节不保证一致。

## 11. 跟踪正在被搬出库

`supervision/tracker/` 还在，但状态尴尬。`ByteTrack` 确实写进了 `sv.__all__`（第 2 节那 137 个名字里就有它），偏偏 `dir(sv)` 里查不到，只有 `getattr` 才拿得到。它是 `__init__.py` 末尾那个 `__getattr__` 惰性兜出来的，函数的文档字符串写得很直白：`Lazily resolve deprecated compatibility exports`。一个名字同时是「公开导出」和「待移除的兼容垫片」，就写在这里。

实例化它时收到的那句警告把时间表说得最清楚：`FutureWarning: The ByteTrack was deprecated since v0.28.0. It will be removed in v0.31.0.`（0.30.1 起 `import supervision` 本身不再触发这条警告，警告挪到了构造时）。按 `docs/deprecated.md` 的移除清单，它属于 **0.31.0 移除**的一批。同批的还有 `supervision.keypoint` 模块、`sv.LMM` 与 `Detections.from_lmm`、`denormalize_boxes` 的 `normalized_xyxy` 参数，以及 `create_tiles` / `overlay_image`。指定替代是外部 `trackers` 包：

```bash
pip install trackers
```

```python
from trackers import ByteTrackTracker
import supervision as sv

tracker = ByteTrackTracker()
tracked = tracker.update(detections)      # 不再是 update_with_detections(...)
```

装 `trackers` 2.6.0 核对：提供 `ByteTrackTracker`、`BoTSORTTracker`、`OCSORTTracker`、`SORTTracker`、`CBIoUTracker`、`McByteTracker` 六种，`update(detections, frame=None, timestamp=None)` 的签名与 supervision 旧接口不同。行为上更要紧的是 `minimum_consecutive_frames` 默认为 2，实测**第一帧返回的 `tracker_id` 是 -1**，第二帧起才拿到稳定编号。把 `-1` 当成有效目标来计数，是迁移时最容易写进 bug 的一行。

而仍在库内的 `sv.ByteTrack`，同一份输入跑出来是每帧 `[1]`，没有预热帧。也就是说：同一批检测、同一个算法名，两条路径的第一帧输出不同。迁移不是换个 import 就等价，验证集上的轨迹数量得重跑。

顺带一条同族的参数更名，0.23.0 就已完成：`track_buffer` / `track_thresh` / `match_thresh` 分别变成 `lost_track_buffer` / `track_activation_threshold` / `minimum_matching_threshold`。老代码里的旧名不是被忽略，而是压根不存在。

## 12. 一次任务如何流过整个系统

把前面几节拼起来看一条完整链路：读视频 → 造检测 → 跟踪 → 区域判定 → 标注 → 写视频。下面这份脚本本文实跑过。框是按帧号算出来的合成结果，不接模型，这样整条链路上的数字都是确定且可复算的。

```python
import numpy as np
import supervision as sv

ZONE = np.array([[300, 100], [600, 100], [600, 300], [300, 300]])
INFO = sv.VideoInfo(width=640, height=480, fps=10)


def make_clip(path: str, frames: int = 40) -> None:
    with sv.VideoSink(path, INFO) as sink:
        for i in range(frames):
            frame = np.full((480, 640, 3), 24, np.uint8)
            x = 30 + i * 14
            frame[120:200, x:x + 70] = (200, 120, 60)
            sink.write_frame(frame)


def run(clip: str, out: str) -> dict:
    zone = sv.PolygonZone(polygon=ZONE)
    zone_annotator = sv.PolygonZoneAnnotator(zone=zone)
    box_annotator = sv.BoxAnnotator()
    label_annotator = sv.LabelAnnotator()
    tracker = sv.ByteTrack(frame_rate=INFO.fps)

    inside, track_ids, index = 0, set(), -1
    with sv.VideoSink(out, INFO) as sink:
        for index, frame in enumerate(
                sv.get_video_frames_generator(clip, prefetch=2)):
            x = 30 + index * 14
            detections = sv.Detections(
                xyxy=np.array([[x, 120.0, x + 70.0, 200.0]]),
                class_id=np.array([0]),
                confidence=np.array([0.9]),
            )
            detections = tracker.update_with_detections(detections)
            triggered = zone.trigger(detections=detections)
            inside += int(triggered.any())
            track_ids.update(detections.tracker_id[triggered].tolist())
            annotated = label_annotator.annotate(
                box_annotator.annotate(frame, detections),
                detections,
                [f"id={t} conf={c:.2f}" for t, c in
                 zip(detections.tracker_id, detections.confidence)],
            )
            sink.write_frame(zone_annotator.annotate(annotated))
    return {"frames": index + 1, "inside": inside, "track_ids": sorted(track_ids)}


if __name__ == "__main__":
    make_clip("demo/clip.mp4")
    print("source :", sv.VideoInfo.from_video_path("demo/clip.mp4"))
    print("result :", run("demo/clip.mp4", "demo/annotated.mp4"))
    print("written:", sv.VideoInfo.from_video_path("demo/annotated.mp4"))
```

实际输出：

```text
source : VideoInfo(width=640, height=480, fps=10.0, total_frames=40)
result : {'frames': 40, 'inside': 22, 'track_ids': [1]}
written: VideoInfo(width=640, height=480, fps=10.0, total_frames=40)
```

这条链路里有几处结构信息值得单独指出。

**跟踪把身份写回同一个数据结构**。`update_with_detections` 收 `Detections`、返回 `Detections`，只多了 `tracker_id`。所以第 3 节那张表里的「中心类型」不是一句口号：区域统计、标签文本、写入 sink 用的都是同一个对象，中途不需要翻译成任何中间表示。

**`zone.trigger()` 返回的是布尔数组**，长度与检测数一致。计数、取样、只画区内目标这三件事都从同一个 `triggered` 出发，不需要三套判定逻辑。默认判定用 `BOTTOM_CENTER` 锚点，也就是对象底部中心进线才算进入；这个选择本身就是设计立场——换成框中心，框一高就会在目标还在远处时误触发。要换锚点用 `triggering_anchors`，0.30.0 又加了 `require_all_anchors` 控制「所有锚点都进」还是「任一进」。

**22 / 40 这个数是可推算的**。目标框左边缘 `x = 30 + 14i`、宽 70，底部中心横坐标 `x + 35 = 65 + 14i`；落在 `[300, 600]` 内要求 `235 ≤ 14i ≤ 535`，即 `i ∈ 17..38`，共 22 帧。代码里那行 `inside` 与手算吻合，说明 `trigger()` 的语义确实是我们读到的那样，而不需要靠猜。

**同一份脚本在两个后端上输出逐字一致**（`fallback` 与 `opencv` 各跑一次，`frames` / `inside` / `track_ids` 全等）。第 10 节说的像素差异不影响几何与计数的确定性——差异只在抗锯齿和文本笔画上。这也是判断一次改动是否安全的好方法：把统计量与像素分开看。

跑这段脚本会看到一条 `FutureWarning`，来自里面的 `sv.ByteTrack`，内容就是第 11 节那句——它是有意留着的一个即将消失的名字。把这段换成真实模型，只需在循环里把合成 `Detections` 换成 `sv.Detections.from_ultralytics(result)` 之类的一行，其余全不动。这就是这套设计真正省人的地方，也是它「模型无关」的实际形态。

## 13. 哪些活不该交给它

第 1 节的判断反过来用，就是一张排除清单。

- **不想装监督模型的数据标注平台**。`DetectionDataset` 读写五种格式，但没有任何标注 UI，也没有质检工作流。
- **想要一套自带调度与批处理的推理服务**。`InferenceSlicer` 会帮你切图、按 `batch_size` 攒批、拼回坐标，但它调用的是你传进去的回调；GPU 并发、多模型路由、动态 batch 都不在它职责里，那是 Roboflow Inference 或 Triton 的事。
- **需要精确 COCO 官方指标的评测**。`sv.MeanAveragePrecision` 在 0.31.0 起换成与 `pycocotools` 对齐的那一份实现，此前的 `metrics.detection.MeanAveragePrecision` 属于待移除的旧类。要拿分数写报告，仍建议与 `pycocotools` 或 `mean_average_precision` 对一次数。
- **实时摄像头为主、且要求低延迟视觉预览的应用**。摄像头得你自己用 `cv2.VideoCapture` 打开（第 8 节），那么 OpenCV 已经在你环境里，「零 OpenCV 依赖」的好处拿不到，反而要为 fallback 的文本渲染付钱（第 10 节）。
- **想要一个模型格式转换或量化工具**。它连一行推理代码都没有。

## 14. 装不上、画不出时按症状排查

下面每一条都是本文实际撞到的错误，按现象分类。

| 症状 | 根因 | 处置 |
|---|---|---|
| 每次画图耗时上百毫秒，且文字边缘与既往截图对不上 | 命中 `fallback` 后端（环境里没有可用 `cv2`） | `pip install opencv-python-headless supervision`，**重启进程**，再用 `from supervision import _cv2; print(_cv2.BACKEND_NAME)` 确认打印 `opencv` |
| 明明装了 OpenCV，`_cv2.BACKEND_NAME` 仍是 `fallback` | 后端在 import 时决定，装包前该进程已 import 过 supervision | 重启 Python 进程；`opencv-python` 与 `opencv-python-headless` 不要同时装 |
| 报 `Could not resolve color by class…`（现场见第 6 节） | `BoxAnnotator` 默认按类别查色，而结果没有 `class_id` | 传 `color_lookup=sv.ColorLookup.INDEX`，或在构造 `Detections` 时给上 `class_id` |
| 画了掩码、热力图、多边形的标注器什么都没画 | 结果没有 `mask`（三个 `requires_mask=True` 的标注器需要掩码） | 检查 `Detections.mask is None`；换连接器时要显式取掩码，例如 `from_inference` 的掩码相关参数 |
| `AttributeError: module 'supervision' has no attribute 'VideoSource'` | 该 API 已不存在（0.27.0 起） | 改用 `sv.get_video_frames_generator` / `sv.process_video`，写文件用 `sv.VideoSink` |
| `AttributeError: ... 'RotatedBoxAnnotator'` | 这个类从未存在 | 旋转框标注器是 `sv.OrientedBoxAnnotator`，输入用 `xyxyxyxy` 型四顶点框 |
| `read_yaml_file` 抛 `FileNotFoundError`，路径显示成 `'None'` | `from_yolo` 的 `data_yaml_path` 必填，被传成了 `None` | 给出真实的 `data.yaml` 路径，类别名就来自这里 |
| `Detections` 构造报 `xyxy must be a 2D np.ndarray with shape (_, 4)` | 只写了 `xyxy=...` 占位，或坐标是 `(N, 2)` / 一维 | 构造 `(N, 4)` 的左上右下坐标数组，并核对 `dtype` |
| 升级后 JSON 落盘解析全崩 | 0.30.0 起 `JSONSink` 写原生类型，值不再是字符串 | 下游按 `float` / `bool` 读；需要文本用 `CSVSink` |
| `mask_non_max_merge` 结果和以前差一截 | 0.30.0 起算精确掩码重叠，`mask_dimension` 被忽略 | 重新标定重叠阈值；`overlap_metric` 与 `mask_dimension` 改成关键字传参 |
| `DetectionDataset.merge` 报 `Image paths … are not unique across datasets` | 待合并的数据集共用了同名图片路径，合并前先保证路径互不重复 | 拆成不同子目录再合并，或改走 `from_coco` 之类的单入口加载 |
| 跟踪计数在启动瞬间偏大或 `tracker_id` 出现 -1 | `trackers` 的 `ByteTrackTracker` 有 `minimum_consecutive_frames=2` 的预热 | 统计时先过滤 `tracker_id > -1`，或在稳定帧之后再取数 |

版本追溯的做法就一条：**把 supervision 的版本号写进依赖锁**，并且知道 0.30.0 与 0.31.0 是两个行为断点。要回到迁移前的像素级行为，官方给的口子是 `pip install "supervision<0.30.0"`。

## 15. 采用顺序：谁先上、谁再等

按项目阶段给顺序，比按功能给顺序更有用。

**已经在用任意检测模型、正在写可视化代码的人：先只引入呈现层。**

1. 装 `supervision`，把项目里手画的框与标签替换成 `BoxAnnotator` + `LabelAnnotator`；
2. 用一家连接器接一次（`from_ultralytics` 或 `from_transformers`），确认你的输出能压成 `Detections`；
3. 加 `PolygonZone` / `LineZone` 做进出与计数，把自研的区域判断代码删掉；
4. 需要指标时用 `ConfusionMatrix` 出验证集图，别急着换掉已有评测脚本。

到这一步为止，你新增的是一个依赖、零个概念，删掉的通常是几百行绘图与区域几何代码。这是 supervision 最划算的一段。

**手上是超大图（航拍、病理、遥感）：直接把它当切图器用。** `InferenceSlicer` 配 `batch_size`，GeoTIFF 走 `supervision[geotiff]` + `WindowedRasterDataset` 的窗口读。这一类场景它的价值高于多数人估计。

**做数据集治理的团队：用它的格式往返，不用它的存储。** 五种格式互转很省事，但转换的正确性要在你自己的数据上验一遍第 7 节那种往返；`split` 固定 `random_state`。

**谁可以再等：**

- 需要 GPU 推理编排与多模型路由的团队——这不是工具箱该承担的分量。
- 严格依赖图像级回归基线的团队——0.30.0 前后端切换会让像素 diff 变红，先固定后端、再决定要不要跟版本。
- Python 3.9 环境——0.30.0 起装不上，要么钉 `<0.30`，要么升级解释器。
- 依赖 `sv.VideoSource` / `sv.ImageAnnotator` 的既有代码——它们已不在当前 API 表面，得改。

## 16. 五个自测题

答不上来就回到括号里标的小节。

1. 为什么 17 个连接器每个都很薄，而它自己几乎不依赖模型框架？（第 1、4 节）
2. `sv.Detections` 唯一的必填参数是哪个，它的形状约定为什么值得单独提？（第 4 节）
3. 掩码画不出来、热力图也画不出来，但框正常——第一顺位查什么？（第 6、14 节）
4. 从 `sv.ByteTrack` 换到 `trackers.ByteTrackTracker`，除包名外还有两处必须改，是哪两处？（第 11 节）
5. fallback 后端 `Box + Label` 量到中位数 298.2 ms/帧，能不能据此判定它只适合离线？（第 10 节）

第 3 题与第 5 题最容易答错。前者错在只想到 `MaskAnnotator`，实际是三个 `requires_mask=True` 的标注器一起失效；后者错在把这 298 ms 当成端到端占比，而它是否致命完全取决于你的模型本身要多少毫秒。

## 17. 下一步读哪份代码

想理解设计，按这个顺序读，每份都不长：

| 位置 | 读它得到什么 |
|---|---|
| `src/supervision/detection/core.py` | `Detections` 的全部字段、校验规则与 `with_*` 后处理，一个文件读完中心类型 |
| `src/supervision/annotators/core.py` | 32 个标注器的共同基类、`requires_mask` 与 `color_lookup` 的真实分支 |
| `src/supervision/_cv2/` | 原先所有 OpenCV 调用点的清单，也是「这库为什么能不要 OpenCV」的答案 |
| `src/supervision/utils/video.py` | 当前视频接口的事实边界：读帧、写帧、探测信息，没有摄像头 |
| `src/supervision/dataset/core.py` | 五种格式的共同契约，`split` 与 `merge` 的语义 |
| `docs/how_to/opencv_migration.md` | 后端选择的官方口径与回滚方式 |
| `docs/deprecated.md` | 移除时间表，决定你能把哪些名字长期写进代码 |
| `examples/` 目录 | 七个可跑示例：`count_people_in_zone`、`time_in_zone`、`speed_estimation`、`tracking`、`heatmap_and_track`、`traffic_analysis`、`compact_mask` |

## 18. 维护指引：本文断言的核实方法与失效条件

本文所有事实来自三类手段，都能重跑：

1. **元数据**：GitHub API 的 `repos`、`releases`、`contributors`、`commits`、`languages` 五个端点，以及 `develop` 上的 `pyproject.toml`。分页计数一律用 `per_page=1` 读 `Link` 头的 `last` 页码。
2. **运行时**：两个 Python 3.11 干净 venv，一个只装 `supervision==0.30.4`（`_cv2.BACKEND_NAME` 打印 `fallback`），一个额外装 `opencv-python-headless`（实测 `opencv`）。跨版本对照额外装了 0.27.0 / 0.28.0 / 0.29.1 / 0.30.4，`trackers` 为 2.6.0。所有 API 存在性用 `hasattr` / `dir` / `inspect.signature` 判定，未凭文档印象。另经 GitHub raw 与 PyPI wheel 双向比对，确认包来源一致。
3. **定量**：第 10 节的耗时是 warmup 后 15 轮均值；第 12 节的 `22` 与手算区间 `i ∈ 17..38` 互验。硬件 Apple M4，未做温度/降频控制。

失效条件按节列在这里，日后重读时先核这几处：

| 位置 | 断言 | 何时会失效 |
|---|---|---|
| 第 2 节 | 全部计数与版本号 | 每次发版；计数类最快过期 |
| 第 2、9 节 | Python 下限 3.10 | 下一次抬版（历史上 0.30.0 抬过一次） |
| 第 4 节 | 17 个连接器、`from_lmm` 弃用 | 0.31.0 移除 `from_lmm` 后变 16 个 |
| 第 5 节 | Soft-NMS 的 0.1451、`OverlapMetric` 只有 `IOU`/`IOS` | 属实现细节，`sigma` 语义或高斯核一改就变；新增重叠度量需改本句 |
| 第 6 节 | 32 个标注器、23 个带 `requires_mask`（3 个为 `True`）、16 个带 `color_lookup`、裸 `xyxy` 可跑 16 个 / 补 `class_id`+`confidence` 后 18 个 | 每次新增标注器或调整默认取色方式；这些计数是穷举跑出来的，新增类后需重数 |
| 第 8 节 | 「无 `VideoSource` / `ImageAnnotator`」 | 若被重新引入需重写本节 |
| 第 9 节 | 五条 breaking、依赖清单 | 下一大版可能再变；`av>=14.2` 是本轮引入 |
| 第 10 节 | 全部毫秒与 1.93% 像素差 | 换机、换分辨率、换框数即不可比；绝对值对机器负载敏感，本文首轮测量就被并行任务抬高了 2–3 倍，只有比值稳定 |
| 第 11 节 | 0.31.0 移除清单、`trackers` 2.6.0 行为 | 0.31.0 发布后本节改为既成事实；`trackers` 换版需重核默认参数 |
| 第 13 节 | MA 指标实现迁移 | 0.31.0 完成后，「旧类待移除」措辞失效 |
| 第 1 节 | 包目录内 3 个文件出现 `torch` | 口径是 `site-packages/supervision/**/*.py`，不含 tests 与 examples；上游若引入 torch 后端需重数 |

示例维护上另有两条约束：示例里的路径、数字、类名以实机为准，改版本必须重跑；`_cv2` 是私有模块，只当安装诊断用，不要写进应用代码。

## 参考来源

- 仓库：<https://github.com/roboflow/supervision>（默认分支 `develop`）
- 官方文档：<https://supervision.roboflow.com/latest/>
- OpenCV 可选后端迁移指南：`docs/how_to/opencv_migration.md`
- 弃用与移除时间表：`docs/deprecated.md`
- 发布说明：v0.30.0（2026-08-04，Run supervision without OpenCV）、v0.30.1（2026-08-24）、v0.30.4（2026-09-17）
- PyPI：`supervision`（元数据 `Requires-Python: >=3.10`）与 `trackers`
- 示例目录：<https://github.com/roboflow/supervision/tree/develop/examples>
- 标注器在线演示：<https://huggingface.co/spaces/Roboflow/Annotators>
- Discord：<https://discord.gg/GbfgXGJ8Bk>
