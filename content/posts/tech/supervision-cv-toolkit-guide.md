---
title: "Supervision：把「模型输出之后」的脏活收敛进一个 sv.Detections"
date: "2026-05-14T20:33:15+08:00"
lastmod: "2026-10-04T10:00:00+08:00"
slug: "supervision-cv-toolkit-guide"
github_repo: "roboflow/supervision"
source_key: "gh:roboflow/supervision"
description: "Supervision 是 Roboflow 推出的模块化计算机视觉 Python 工具库，用统一的 sv.Detections 承接十几家模型的推理输出，覆盖标注、区域计数、目标追踪、大图切片推理和数据集格式互转。本文基于 0.30.6（2026 年 9 月）核查其 API 与版本演进。"
draft: false
categories: ["技术笔记"]
tags: ["计算机视觉", "Python", "开源工具"]
---

# Supervision：把「模型输出之后」的脏活收敛进一个 sv.Detections

Supervision（[roboflow/supervision](https://github.com/roboflow/supervision)）解决的是计算机视觉工程里一个具体而反复出现的痛点：模型推理已经跑通，但不同模型的输出格式各不相同，后续的过滤、标注、计数、追踪、数据集转换全部要针对每种模型重写一遍。它用 `sv.Detections` 这个统一数据结构承接 Ultralytics、Transformers、MMDetection、Detectron2、Roboflow Inference 等来源的推理结果，把模型输出到业务逻辑之间的胶水代码收敛到一处。截至 2026 年 10 月初，最新版本 0.30.6（2026 年 9 月 29 日），Python >= 3.10，MIT 协议，约 5.1 万 star。

## 视觉技术栈中的定位

视觉应用大致分四层：数据层（图片、视频、标注文件）、模型层（YOLO、DETR、SAM、Grounding DINO 等）、后处理与应用逻辑层（结果转换、过滤、可视化、追踪、区域计数、数据集转换、指标评估）、业务系统层（交通分析、工业质检、机器人、安防）。Supervision 位于第三层，向下适配各种模型输出格式，向上给业务系统提供稳定的中间表示。

模型库关心"推理结果是什么"，Supervision 关心"拿到结果之后怎么办"。Ultralytics 返回 `Results` 对象，Transformers 返回张量和字典，SAM 返回 mask。一个项目里如果同时接入多个模型，业务代码很快会被各种私有输出格式绑死。Supervision 的做法是先把不同来源转换成统一的 `sv.Detections`，下游的标注、过滤、统计、评估只围绕这个对象写。

## sv.Detections：统一中间表示

`sv.Detections` 是整个库的基础数据结构，承载检测和分割结果：

| 字段 | 含义 | 类型 |
|------|------|------|
| `xyxy` | 目标框坐标，左上右下 | `np.ndarray[N, 4]` |
| `confidence` | 置信度 | `np.ndarray[N]` |
| `class_id` | 类别 ID | `np.ndarray[N]` |
| `tracker_id` | 追踪 ID（可选） | `np.ndarray[N]` |
| `mask` | 实例分割掩码（可选） | `np.ndarray[N, H, W]` 或 `CompactMask` |
| `data` | 扩展字段（类别名、自定义属性、VLM 解析结果） | `dict` |

转换接口按模型来源命名，调用一次即可：

```python
import supervision as sv

# Ultralytics YOLO
detections = sv.Detections.from_ultralytics(result)

# Hugging Face Transformers（id2label 可选，用于填充类别名）
detections = sv.Detections.from_transformers(result, id2label=id2label)

# Roboflow Inference
detections = sv.Detections.from_inference(result)

# Detectron2
detections = sv.Detections.from_detectron2(result)

# MMDetection
detections = sv.Detections.from_mmdetection(result)
```

`from_` 系列不止这五个：源码里还有 `from_yolov5`、`from_yolo_nas`、`from_tensorflow`、`from_deepsparse`、`from_paddledet`、`from_ncnn` 等，加上解析 VLM 输出的 `from_vlm`、解析 SAM3 文本提示分割的 `from_sam3`、OCR 场景的 `from_easyocr`，共十余种。适配面跟着下游生态走：解析通用 LMM 输出的 `from_lmm` 在 0.30.6 还在，开发分支已经把它删了，下一个版本会正式移除。

RF-DETR（roboflow 自家的实时检测模型）比较特殊，它的 `predict` 方法直接返回 `sv.Detections`，不需要转换：

```python
from rfdetr import RFDETRSmall
from PIL import Image

model = RFDETRSmall()
image = Image.open("input.jpg")
detections = model.predict(image, threshold=0.5)

len(detections)
# 5
```

转换之后，过滤操作用 NumPy 布尔索引完成，和操作数组没有区别：

```python
# 按置信度过滤
detections = detections[detections.confidence > 0.5]

# 按类别过滤（假设类别 0 是人）
person_detections = detections[detections.class_id == 0]
```

这个设计的关键在于：下游代码（标注器、区域计数、追踪器）只认 `sv.Detections`，不关心数据来自哪个模型。从 YOLO 切到 Transformers 或 Detectron2，只要转换接口存在，下游逻辑不必推倒重写。

分割场景还有一层内存账。分割模型每给一个实例就输出一张全分辨率位图，1920×1080 画面上 28 个实例约 55 MB 掩码数据。0.28.0 引入的 `sv.CompactMask` 只存每个掩码的外接框裁剪并做 RLE 编码，同样 28 个实例降到约 237 KB；标注器和 `area` 过滤照常工作，0.30.0 起 `from_inference(compact_masks=True)` 还能让 Inference 的结果直接以紧凑形式进来。

## 一次完整的检测-标注-计数流程

以视频中的车辆区域计数为例，展示任务如何流过 Supervision 的各个组件：

```python
import cv2
import numpy as np
import supervision as sv
from ultralytics import YOLO

model = YOLO("yolo11n.pt")
box_annotator = sv.BoxAnnotator()
label_annotator = sv.LabelAnnotator()

# 定义多边形计数区域（必须是 np.array，传入 Python list 会在 astype 处报错）
zone = sv.PolygonZone(
    polygon=np.array([[0, 400], [1280, 400], [1280, 720], [0, 720]]),
)

def callback(frame: np.ndarray, frame_index: int) -> np.ndarray:
    # 1. 模型推理
    result = model(frame)[0]
    # 2. 转换为统一结构
    detections = sv.Detections.from_ultralytics(result)
    # 3. 区域判定：trigger 返回布尔数组，用它做区域内过滤；
    #    current_count 每帧重算，是"当前帧在区域内的目标数"
    detections = detections[zone.trigger(detections=detections)]
    # 4. 标注
    annotated = box_annotator.annotate(scene=frame.copy(), detections=detections)
    annotated = label_annotator.annotate(scene=annotated, detections=detections)
    return annotated

sv.process_video(
    source_path="input.mp4",
    target_path="output.mp4",
    callback=callback,
)
```

数据流是：模型输出 → `sv.Detections` 转换 → 区域判定与过滤 → 标注器叠加 → 写出新视频。每一步都只处理 `sv.Detections`，模型可以随时替换。`sv.process_video` 的 callback 收到 `(frame, frame_index)` 两个参数，逐帧顺序执行，帧间没有并行。

## Annotator 体系

标注器是 Supervision 里数量最多的一组组件。`annotators/core.py` 里定义了 23 个标注器类，`BoxAnnotator`、`LabelAnnotator`、`MaskAnnotator`、`TraceAnnotator`、`RoundBoxAnnotator`、`EllipseAnnotator`、`HaloAnnotator`、`ColorAnnotator`、`CircleAnnotator`、`DotAnnotator`、`TriangleAnnotator`、`BlurAnnotator`、`PixelateAnnotator`、`HeatMapAnnotator`、`BoxCornerAnnotator`（注意不叫 `CornerAnnotator`）、`OrientedBoxAnnotator`、`PercentageBarAnnotator`、`CropAnnotator` 等；多边形区域和穿线计数线各有配套的 `PolygonZoneAnnotator`、`LineZoneAnnotator`；关键点标注在 `key_points` 模块，0.29.0 又加了 `VertexEllipseArea/Outline/HaloAnnotator` 三个用协方差椭圆可视化关键点不确定性的标注器。

标注器的意义不只是"画得好看"。误检、漏检、追踪 ID 跳变、区域判断错误，这些问题只有画出来才容易定位。手写 OpenCV 绘图代码时，标签超出画面边界、同类目标同色、不同 `tracker_id` 配色、mask 半透明叠加、多行标签排版这些细节会逐渐堆积成样板代码。标注器把这些封装成可组合的调用，每个标注器只接收 `scene` 和 `detections` 两个核心参数。

两个使用细节：`LabelAnnotator` 的 `labels` 参数可选，不传就只画类别 ID；`HeatMapAnnotator`、`TraceAnnotator` 这类有内部累积状态的标注器，0.30.0 起提供 `reset()`，同一路视频文件分多段处理或多路摄像头复用一个实例时，先重置再喂下一路，否则上一路的轨迹会污染下一段画面。

## 区域计数与穿线计数

`PolygonZone` 和 `LineZone` 处理两类常见业务逻辑。

`PolygonZone` 回答"区域内有多少目标"：给定多边形顶点，`trigger` 返回每个检测是否落在区域内的布尔数组，`zone.current_count` 是当前帧区域内的目标数。目标框用哪个点判断由 `triggering_anchors` 决定，默认 `Position.BOTTOM_CENTER`——行人用脚底位置，车辆用框中心，各场景判定标准不同。0.30.0 补了一个 `require_all_anchors` 开关（默认 `True`）：配多个锚点时，"所有锚点都在区域内才算"还是"任一锚点在即算"，边界目标跨两个相邻区域统计时用得上。

`LineZone` 回答"有多少目标从左往右（或反方向）穿过了这条线"：它维护 `in_count` 和 `out_count` 两个计数器，另有按类别细分的 `in_count_per_class` / `out_count_per_class`。穿线计数本身的边界问题不少：目标在边界上抖动导致反复跨线、目标框中心点判定不准、遮挡后重新出现 ID 跳变。Supervision 把这些封装在 `LineZone` 内部，调用方要做的是定义线和方向——前提是检测结果带着稳定的 `tracker_id`。

## 目标追踪：sv.ByteTrack 的退场与 trackers 包

检测告诉你"这一帧有多少辆车"，追踪告诉你"这辆车是不是刚才那辆"。只有有了稳定的 `tracker_id`，才能做穿线计数、区域停留、轨迹分析和速度估计。

Supervision 自带的 ByteTrack 正处在退场流程中，时间线值得注意：

- 0.28.0（2026 年 4 月）：`sv.ByteTrack` 标记 deprecated，原计划 0.30.0 移除；
- 0.30.0（2026 年 8 月）：移除推迟一个版本，改到 0.31.0，源码标注 `remove_in="0.31.0"`；
- 截至 0.30.6（2026 年 9 月底）它还能用，但每次调用会收到弃用警告；开发分支已经把整个 `tracker/` 目录删了。

官方给的去处是独立的 [trackers](https://github.com/roboflow/trackers) 包（Apache 2.0，约 3,900 star）：`pip install trackers` 之后用 `ByteTrackTracker`，注意方法名从 `update_with_detections()` 改成了 `update()`。trackers 还带一个 CLI，可以直接指定检测模型和追踪算法处理视频或 RTSP 流。从旧教程复制代码时别再引入 `sv.ByteTrack`，新项目直接用 trackers 包。

## InferenceSlicer：大图切片推理

工业质检、遥感、航拍、医学影像中，4K 或 8K 图片里的小目标直接缩放到模型输入尺寸会丢失。常见做法是把大图切成多个重叠 patch，分别推理，再把结果合并回原图坐标系。这种 tiled inference 的工程量不小：切片尺寸与重叠率、边界目标去重、坐标变换、批量推理。

`sv.InferenceSlicer` 把这套流程封装起来——推理回调在构造时传入，调用时喂整图：

```python
import numpy as np
import supervision as sv
from ultralytics import YOLO

model = YOLO("yolo11n.pt")

def callback(slice_image: np.ndarray) -> sv.Detections:
    result = model(slice_image)[0]
    return sv.Detections.from_ultralytics(result)

slicer = sv.InferenceSlicer(
    callback=callback,
    slice_wh=640,        # 切片尺寸，默认 640
    overlap_wh=100,      # 相邻切片重叠像素，默认 100
)
detections = slicer(image)
```

重叠区域的重复检测由 `overlap_filter` 收口，默认 `NON_MAX_SUPPRESSION`，可换 `NON_MAX_MERGE`（按 IoU 合并相邻检测的掩码）或 `NONE`。0.30.0 给它加了两件事：`batch_size` 让回调按批接收切片，模型吞吐能吃满；GeoTIFF 支持（`pip install "supervision[geotiff]"`）通过 `sv.WindowedRasterDataset` 按窗口读取多 GB 的遥感影像，不用把整幅图载入内存。

小目标检测不只是模型能力问题，输入策略同样关键。

## 数据集加载与格式转换

`sv.DetectionDataset` 支持五种标注格式的加载和保存——COCO、YOLO、Pascal VOC 之外，0.30.0 新增 LabelMe 和 CreateML：

```python
# 从 YOLO 格式加载
dataset = sv.DetectionDataset.from_yolo(
    images_directory_path="data/images",
    annotations_directory_path="data/labels",
    data_yaml_path="data/data.yaml",
)

# 转换为 COCO 格式保存
dataset.as_coco(
    images_directory_path="output/images",
    annotations_path="output/annotations.json",
)

# 数据集划分
train_ds, test_ds = dataset.split(split_ratio=0.7)
test_ds, valid_ds = test_ds.split(split_ratio=0.5)

# 多个数据集合并
merged = sv.DetectionDataset.merge([ds_1, ds_2])
```

合并时类别名会自动去重并按序重排索引。数据集对象支持按索引访问，图像按需加载，不会一次性读入内存。

## 0.28 到 0.30：三个版本的主线

Supervision 的迭代节奏很快，把最近三个大版本的主线并排看，能看出它在往哪个方向走：

| 版本 | 时间 | 主线 |
|------|------|------|
| 0.28.0 | 2026-04 | `CompactMask` 稀疏掩码（28 个实例约 55 MB → 237 KB）；`from_sam3` 接入 SAM3 文本提示分割 |
| 0.29.0 | 2026-06 | 关键点不确定性可视化三件套（协方差椭圆）；旋转框 NMS |
| 0.30.0 | 2026-08 | OpenCV 变为可选依赖；Soft-NMS；LabelMe/CreateML 格式；GeoTIFF 窗口读取与 `batch_size`；Python 下限升到 3.10 |
| 0.30.1–0.30.6 | 2026-08/09 | 缺陷修复 |

0.30.0 的变化面最大。它给库加了一个私有的 `_cv2` 后端，用 NumPy、Pillow 加 PyAV 重新实现了库内用到的每一个 OpenCV 调用：装了 OpenCV 就优先用，没装也能正常 import——此前的行为是 import 直接崩溃，深度学习环境里 OpenCV 轮子冲突由此不再波及 supervision。代价是安装依赖多了 `av>=14.2`，需要弹窗展示时用 `sv.ImageWindow` 替代 `cv2.imshow`。同版还有 Soft-NMS（`detections.with_soft_nms(sigma=0.5)`），拥挤场景下不再粗暴丢弃重叠框，而是按衰减重缩放置信度。

## 与 torchvision / detectron2 后处理工具的对比

| 维度 | torchvision | detectron2 | Supervision |
|------|-------------|------------|-------------|
| 定位 | 通用视觉工具库 | 端到端检测/分割框架 | 模型无关的后处理工具库 |
| 模型输出处理 | 各模型自带 `Result` 结构，需手动提取 | 绑定 detectron2 自己的 `Instances` | 统一 `sv.Detections`，适配十余种来源 |
| 可视化 | `torchvision.utils.draw_bounding_boxes` 等基础函数 | `DefaultPredictor` + `Visualizer`，绑定 detectron2 格式 | 23 个标注器，可组合 |
| 区域计数 | 无内置 | 无内置 | `PolygonZone` / `LineZone` |
| 追踪 | 无内置 | 无内置 | trackers 包（ByteTrack 等） |
| 数据集格式 | 需自定义 | 绑定 detectron2 注册表 | COCO / YOLO / VOC / LabelMe / CreateML 互转 |
| 模型耦合 | 低，但需手写适配 | 高，与 detectron2 训练流程绑定 | 零，不参与训练 |

torchvision 提供的是基础积木（NMS、`draw_bounding_boxes`），需要自己组装成完整流程。detectron2 的后处理和可视化绑定它自己的 `Instances` 结构，换模型就要换处理代码。Supervision 的差异在于模型无关——它不训练模型，不定义模型结构，只处理"模型输出之后"的事情。

## Roboflow 生态协作

Supervision 是 Roboflow 工具链的一环，和几个项目形成上下游配合：

- [Autodistill](https://github.com/autodistill/autodistill)：自动标注。用大模型（如 Grounding DINO、SAM）给未标注数据生成初始标签，输出可直接用 Supervision 加载的格式。
- [Inference](https://github.com/roboflow/inference)：推理服务器。提供 HTTP API 和 Python SDK，`sv.Detections.from_inference()` 直接承接其输出。部署时 Inference 负责模型服务和硬件加速，Supervision 负责后处理。
- [Maestro](https://github.com/roboflow/maestro)：原 multimodal-maestro，现已独立成多模态模型微调框架，覆盖 PaliGemma 2、Florence-2、Qwen2.5-VL 的微调与评测，和 Supervision 的 VLM 解析器各管一段。

这条链路覆盖"标注 → 训练 → 推理 → 后处理"的本地化工作流。Supervision 本身不依赖 Roboflow 平台，可以独立使用，但接入生态后能减少格式转换的摩擦。

## 性能边界

Supervision 是纯 Python 库，数据结构基于 NumPy。它的性能边界由几个因素决定：

- `sv.Detections` 的字段是 NumPy 数组，过滤和索引操作是向量化的，单帧检测结果的过滤开销可忽略。
- 视频处理的瓶颈在模型推理，不在 Supervision 的标注和计数。`process_video` 逐帧调用 callback，帧间没有并行；0.30.0 给 `get_video_frames_generator` 加了 `prefetch` 参数，解码在后台线程跑，算力充裕时能喂饱 GPU。
- `InferenceSlicer` 会成倍增加推理次数（取决于切片数量），适合离线分析，实时场景要评估吞吐量。
- 追踪器和标注器的状态在内存里，长视频或多路流复用实例时，`TraceAnnotator` 的 `trace_length`（默认保留最近 30 帧）和热力图累积都会占内存，0.30.0 起可以用 `reset()` 清空。

对于实时性要求高的场景（>30 FPS），Supervision 的后处理开销通常不是瓶颈，模型推理才是。但如果单帧检测目标数量极大（数千个框），标注器的绘制开销会上升，这时可以先用 `sv.Detections` 过滤再标注；分割掩码的内存大头则交给 `CompactMask`。

## 采用建议

Supervision 适合的团队：已经跑通模型推理，需要在业务系统中集成视觉能力，不想把后处理代码绑死在某个模型的私有输出格式上。尤其是需要视频分析、区域计数、目标追踪的项目，Supervision 能省去大量重复工程。

不适合的场景：需要端到端训练流程（Supervision 不训练模型）、对后处理有极低延迟要求且目标数量极大（纯 Python 绘制可能成为瓶颈）、模型来源单一且不会变化（直接用模型库自带的后处理更轻量）。

采用顺序上，先从 `sv.Detections` 的转换接口开始，把现有模型输出统一进来；再按需引入 Annotator 做可视化调试；区域计数和追踪等业务逻辑组件按场景逐步加入。几个当前的注意点：环境是 Python 3.9 的先升级，0.30.0 起不再支持；OpenCV 冲突频发的环境现在可以直接装 supervision 不装 OpenCV；追踪需求直接用 trackers 包，不要基于 `sv.ByteTrack` 写新代码；用了 `from_lmm` 的集成注意 0.31.0 会把它移除，届时迁到 `from_vlm`。如果项目里已经在用 Roboflow Inference 做推理服务，Supervision 是自然的后处理搭档。

本文数据核查于 2026 年 10 月 4 日：版本、API 签名以 GitHub 0.30.6 tag 与 develop 分支源码为准，star 数为当日读数。
