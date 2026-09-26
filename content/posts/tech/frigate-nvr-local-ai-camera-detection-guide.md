---
title: "Frigate NVR：先用运动检测决定在哪里跑 AI，再谈本地摄像头识别"
date: "2026-05-25T09:12:29+08:00"
lastmod: "2026-09-21T00:00:00+08:00"
slug: "frigate-nvr-local-ai-camera-detection-guide"
github_repo: "blakeblackshear/frigate"
source_key: "gh:blakeblackshear/frigate"
description: "对照 blakeblackshear/frigate 的 dev 分支（提交 285dd5a）与 v0.18.0 发布说明拆解 Frigate：运动检测如何决定推理次数、12 个检测器插件背后的真实运行时、record 保留策略的当前字段、frigate/events 的载荷结构，以及 0.18 把配置搬进界面之后哪些旧写法已经失效。"
draft: false
categories: ["技术笔记"]
tags: ["Home Assistant", "NVR", "目标检测", "边缘计算"]
---

> **目标读者**：已经在跑或准备跑 Home Assistant、想把摄像头从「录像机」变成「传感器」的人，以及在 Coral、Hailo、Intel 核显、NVIDIA 独显之间做选型的工程师。
> **核心问题**：Frigate 为什么能在家用小主机上带起多路摄像头，以及这套设计的代价落在哪几处。
> **事实边界**：本文核对的是 `blakeblackshear/frigate` 默认分支 `dev` 的提交 `285dd5a`（2026-09-19）、GitHub Release `v0.18.0`（2026-09-12 发布）的说明，以及 2026-09-21 通过 GitHub 应用程序接口（API）读到的仓库数据。机制描述尽量指到仓库内的具体文件与字段；官方未给出的延迟、准确率数字本文一律不给。

## 一句话判断

Frigate 的关键设计不是「能识别物体」，而是**尽量不识别**：它先用一次像素级差分判断画面哪里动了，只把那块区域送去跑模型。这条链路决定了它全部的性格——家用级 CPU 加一根 Coral 棒就能带起几路 1080p，误报和漏报的开关几乎都在「运动」这一层，而存储只保留真正有过活动的时间段。

代价同样具体。运动检测是启发式的，树影、雨丝、时间戳跳动都会消耗推理额度；模型只看得到被框出来的局部区域，所以它对「站着一动不动的人」需要额外机制；而因为录像段是直接从摄像头流写出的，摄像头的编码质量就是最终证据质量，Frigate 不会替你重编码。

如果你的需求是「远程看一眼门口」，装它属于过度工程。如果是「家里来人要有记录、要能按区域和对象类型触发自动化、并且影像不出内网」，它是我见过把这条链路做得最完整的开源方案之一。

## 项目坐标（2026-09-21 核对）

| 字段 | 值 |
|------|------|
| 仓库 | [blakeblackshear/frigate](https://github.com/blakeblackshear/frigate)，默认分支 `dev`，建仓 2019-01-26，最近推送 2026-09-20 |
| Stars / Forks | 36,017 / 3,612（GitHub API 当日读数） |
| 开放议题与合并请求 | 105（该字段是两者之和，需按 `type:issue` / `type:pr` 分开取） |
| 最新发布 | `v0.18.0`（2026-09-12），上一个功能版本 `v0.17.0`（2026-02-27），中间两次维护版 `0.17.1`、`0.17.2` |
| 镜像 | `ghcr.io/blakeblackshear/frigate:stable`，另有 `-standard-arm64`、`-tensorrt`、`-tensorrt-jp6`、`-rk`、`-rocm`、`-synaptics` 六个变体 |
| License | MIT（`LICENSE` 首行为 `The MIT License`，版权行已写成 `Copyright (c) 2026 Frigate, Inc.`） |
| 语言构成 | TypeScript 4,732,628 字节（49.7%）、Python 4,664,314（49.0%）、Shell 43,945、CSS 29,483、Dockerfile 21,711 |
| 官方文档 | [docs.frigate.video](https://docs.frigate.video)，站点 `i18n.locales` 只有 `en` |
| 中文文档 | 导航栏「简体中文（社区翻译）」指向 [docs.frigate-cn.video](https://docs.frigate-cn.video)，是社区站点而非官方构建 |
| 界面语言 | `web/public/locales/` 下共 58 个语言目录，含 `zh-CN` 与 `zh-Hant`，Web 界面的简中是官方自带 |

语言条那一行值得多说一句：界面代码就住在同一个仓库的 `web/` 下，`web/package.json` 的包名仍是 `web-new`，技术栈是 React 19 加 TypeScript，体量与 `frigate/` 的 Python 几乎对半。再说「这是个 Python 项目」只描述了一半。

## 系统地图：三条彼此独立的链路

Frigate 内部最容易搞混的地方，是把三条不同目的的链路看成一条。看代码或者调参数之前，先把它们分开。

```text
① 取流与解码
   摄像头 RTSP ──FFmpeg──┐
   其他协议     ──go2rtc──┴─→ main / sub 两路 → 按 detect 目标尺寸缩放 → 共享内存帧池

② 判断「值不值得看」
   与滑动平均帧差分（OpenCV）→ 运动像素 → 合并成运动框 → 运动区域

③ 识别与沉淀
   运动区域 + 解码帧 → 检测器插件（Coral / ONNX / OpenVINO / TensorRT / RKNN …）
        → 对象过滤器与区域 → 追踪目标 → 核查项（alert / detection）
        → 快照、录像段、MQTT 发布
```

官方的 [Video pipeline](https://docs.frigate.video/frigate/video_pipeline/) 给的五步（取流、解码、运动、识别、录像）就是这个结构的另一种切法。**录像写入并不经过模型**：它从取流那一步直接分叉，按运动与事件标记决定保留哪几段。理解了这一点，「为什么关掉检测还在涨磁盘」这类疑问会自己消失。

三条链路各自有独立的失败模式和独立的调参入口：①出问题表现为丢帧与花屏，②出问题表现为误报和 CPU 占用异常，③出问题表现为漏检或事件分类不对。把它们混为一谈，是新手调 Frigate 最常见的时间黑洞。

## 拆开四组常被混用的概念

| 概念 | 实际是什么 | 不是什么 |
|------|------|------|
| 运动框 / 运动区域 | 差分后合并出的矩形，决定下一帧在哪里跑模型 | 不是「检测到物体」 |
| 追踪目标（tracked object） | 一个被持续关联的物体实例，有 id、起止时间、区域轨迹 | 不是一次警报 |
| 核查项（review item） | 一段时间窗口，可包含任意多个追踪目标 | 不是事件列表里的单条记录 |
| 警报（alert，不少中文材料写作「告警」） / 检测（detection） | 核查项的优先级分类，默认 person 与 car 为警报 | 不是模型标签 |

「核查项」这一层是 0.14 引入的语义变化，官方 [Review 文档](https://docs.frigate.video/configuration/review/)讲得很直白：0.13 及以前界面里的 event 与追踪目标同义，两个人牵一条狗、街对面过一辆车，界面给你 4 条互相重叠的记录；0.14 之后这被合成一条核查项，看完一次即标记已阅，同一摄像头的核查项不允许重叠。

还有一组容易踩的：区域（zone）与掩码（mask）。官方 [Masks 文档](https://docs.frigate.video/configuration/masks/)专门列了对照表，结论是**多数想「屏蔽某块画面」的诉求应该改用区域加 `required_zones`**。运动掩码只是让那块区域不产生运动，若同一帧别处有运动触发了识别，掩码区内的物体照样会被检出；对象过滤掩码则按包围盒**底边中心点**判定，画错位置就完全没有效果。掩码画多了还会伤跟踪——运动信息同时用于在下一帧收窄识别范围。

## 取流与解码：角色只有四个

摄像头输入用「角色」声明这条流是给谁用的。`frigate/config/camera/ffmpeg.py` 的 `CameraRoleEnum` 当前只有四个值：

```python
class CameraRoleEnum(str, Enum):
    audio = "audio"
    record = "record"
    record_sub = "record_sub"
    detect = "detect"
```

老教程里常见的 `rtmp` 角色已经不在这个枚举内了。仓库根目录那份 `config/config.yml.example` 仍写着 `rtmp`，它自身已经滞后，不要照抄——遇到「文档里的字段在源码枚举中找不到」，以枚举为准。

一路摄像头通常给两条流：高分辨率的 main 用于录像，低分辨率的 sub 用于识别。识别流会被下采样到 `detect` 指定的尺寸并按 `fps` 抽帧。`frigate/config/camera/detect.py` 的默认值值得记一下：

- `enabled` 默认 **False**，识别必须显式打开；
- `fps` 默认 5，官方注释写明只有追踪极快物体时才上调，且最多到 10；
- `width` / `height` 默认留空即使用原生分辨率，且两者必须同时给或同时不给，否则配置校验直接报错；
- `min_initialized` 默认为空、解析时按 `fps` 的一半取值，即连续命中多少帧才建立追踪目标——想压掉「一闪而过的误检」，这里是第一个旋钮。

## 运动检测：真正省算力的地方

`frigate/motion/improved_motion.py` 的实现是经典视觉那套，顺序很直白：帧缩放后先用 `gaussian_filter`（scipy）做一次模糊压掉细碎噪声，再 `cv2.absdiff` 对当前帧与滑动平均帧取差、`cv2.threshold` 二值化、`cv2.dilate` 补上空洞，最后 `cv2.findContours` 按轮廓面积把运动像素聚成矩形。默认 `threshold` 是 30，取值区间 1 到 255，越大越迟钝。

官方调优路径也全部围绕这一层，顺序很明确：先看 [Debug 视图](https://docs.frigate.video/usage/live/)打开运动框，知道到底什么东西在产生运动；再给时间戳、天空、屋檐、晃动的树做运动掩码；最后用内置的 **Motion Tuner**（`设置 > 摄像头配置 > 画面变动调整`）边改边看效果。识别层的阈值往往是第二步手段——运动层过敏感时，你会同时看到 CPU 占用上去和误检上去，这时先修运动。

这里有一个决策级的推论：**如果你只在纯 CPU 上跑 Frigate，误报的代价不只是通知烦人，而是整机卡顿**，因为每个误报运动框都要过一遍模型。反过来，配了加速卡之后，运动层迟钝一点的代价变小，可以先放宽再收紧。

## 检测器：12 个插件，运行时不止一个

`frigate/detectors/plugins/` 下当前有 12 个插件，`DETECTOR_KEY` 分别是：

| 键 | 面向的硬件 | 实际运行时 |
|------|------|------|
| `edgetpu` | Google Coral（USB / Mini PCIe / M.2） | TFLite，走 `tflite_runtime` 或 `ai_edge_litert` |
| `cpu` | 任意 x86/ARM 的 CPU | 同上，官方定位是「仅用于测试」 |
| `teflon_tfl` | 带专用 TFLite delegate 的加速卡 | TFLite 加厂商 delegate（`tflite_load_delegate_interpreter`） |
| `openvino` | Intel 核显、Arc 独显、CPU、NPU | `import openvino as ov` |
| `onnx` | 跨平台的通用路径 | `onnxruntime`，按硬件挑执行提供者 |
| `tensorrt` | NVIDIA 显卡与 Jetson | 直接 `ctypes` 挂 TensorRT 库 |
| `rknn` | 瑞芯微 NPU | RKNN 运行时，支持在容器内自动转换模型 |
| `hailo` | Hailo-8 / 8L / 8R | HailoRT，不在镜像内，首次启动时联网下载 |
| `memryx` | MemryX MX3 | 社区维护 |
| `axengine` | AXERA | 社区维护，0.18 新增 |
| `synaptics` | Synaptics NPU | 社区维护 |
| `zmq` | 把推理交给外部进程 | REQ/REP 套接字，默认端点 `ipc:///tmp/cache/zmq_detector`，`/tmp/cache` 同时是录像段的写入缓存目录 |

关于这一层，有三件事和常见描述不一样。

第一，**Frigate 文档首页仍写着 "Uses OpenCV and Tensorflow"**，那是从早期版本沿用至今的一句话。核对源码可知，OpenCV 确实还在，运动检测与图像处理都在用；但目标检测的推理运行时没有一个走 TensorFlow。`frigate/detectors/plugins/` 里是 TFLite/LiteRT、ONNX Runtime、OpenVINO、TensorRT、RKNN、HailoRT。依赖清单 `docker/main/requirements-wheels.txt` 仍然装着 `tensorflow` 与 `tensorflow-cpu`，但它写在一行注释 `# Classification Model Training` 之下，服务的是自定义分类模型的训练路径，不是每帧都在跑的识别推理。

第二，**华为昇腾 NPU 不在支持列表内**。12 个插件里没有 Ascend 相关实现，`docs/docs/configuration/object_detectors.md` 的硬件清单也没有它。国内用户如果拿着昇腾卡来找接入点，现在没有——能走的是把推理放到外部服务、或者选列表内的卡。

第三，**「CPU 也能跑」这句话要看谁说的**。官方对 CPU 检测器的标题就叫 "CPU Detector (not recommended for actual use)"，并且补了一句：多数情况下 OpenVINO 的 CPU 模式效果更好。Intel 迷你主机走 OpenVINO CPU 模式，与树莓派走 CPU TFLite，是两件差别很大的事。

模型的声明方式现在统一在顶层 `models` 列表，一个条目描述一个模型跑在哪些设备上：

```yaml
models:
  - devices:
      - openvino:GPU
    path: /config/model_cache/yolov9-s.onnx
    model_type: yolo-generic
    width: 320
    height: 320
```

`devices` 的每一项是「检测器类型，可选冒号加设备」，例如 `edgetpu:pci:0`、`openvino:NPU`、`tensorrt:0`。同一设备写两遍会起两个推理进程，那在跑得动多路的硬件上能提高吞吐；Coral 与 MemryX 只能被一个进程打开，因此不可重复。一个模型不能横跨两种检测器类型。多模型按 `scene` 分场景，摄像头用 `detect -> scene` 认领，室内外分别配模型就靠它。

## 对象过滤与默认跟踪清单

`objects -> track` 默认只有一项：`frigate/config/camera/objects.py` 里 `DEFAULT_TRACKED_OBJECTS = ["person"]`。想识别车、狗、猫必须自己加。默认模型可选的标签来自 `labelmap.txt`，共 90 行（COCO 那一套，其中 `truck` 被默认改名为 `car`，因为两者常被混淆）。

每类对象的过滤参数与默认值（同文件 `FilterConfig`）：

| 字段 | 默认 | 作用 |
|------|------|------|
| `min_area` | 0 | 包围盒面积下限，像素 |
| `max_area` | 24000000 | 面积上限 |
| `min_ratio` / `max_ratio` | 0 / 24000000 | 宽高比，用来排除细长误检 |
| `threshold` | 0.7 | 判定为该类对象的分数 |
| `min_score` | 0.5 | 低于此分数直接丢弃 |

`threshold: 0.7` 就是默认值，很多文章把它当「调高以降误报」的示范写进配置里，其实那行什么都没改。真要压误报，`min_area` 与 `min_ratio` 通常比 `threshold` 更有效，因为它们排除的是「形状不对」而非「不够自信」的框。

## 录像与保留：旧字段已经失效

录像配置在 0.14 之后重写过一轮，当前结构（`frigate/config/camera/record.py` 的 `RecordConfig`）是按「为什么保留」分层的：

```yaml
record:
  enabled: True
  continuous:
    days: 3      # 全时录像保留天数，默认 0 即不保留
  motion:
    days: 7      # 有运动的段保留天数，默认 0
  alerts:
    retain:
      days: 30
      mode: all
  detections:
    retain:
      days: 30
      mode: motion
```

`mode` 有三个取值：`all`、`motion`、`active_objects`（`RetainModeEnum`）。事件层的 `retain` 默认是 10 天、`mode: motion`，而 `continuous` 与 `motion` 的天数默认都是 0。也就是说：**开启录像后的出厂默认是「只留有警报和检测的那部分运动段，保 10 天」**，既不是全时录像，也不是什么「motion 是推荐默认」。

早先那种写法已经不被接受：

```yaml
# 旧结构，当前版本的配置校验不会认它
record:
  enabled: True
  retain:
    days: 7
    mode: motion
  events:
    retain:
      default: 14
```

顶层 `record.retain` 与 `record.events` 这两个字段在 `RecordConfig` 里都不存在。网上大量教程仍贴这一段，这是读旧文章时最需要提防的一处。

落盘形态也有几个值得记住的约束：段文件写在 `/media/frigate/recordings`，目录层级是 `YYYY-MM-DD/HH/<摄像头名>/MM.SS.mp4`，时间为 UTC；**这些段直接从摄像头流复制而来，不重编码**，所以 H.265 流只有 Chrome 108+、Edge、Safari 能看，其他浏览器要求 H.264。段先写入 `/tmp/cache`，通过校验且符合保留策略后才搬到正式目录——官方建议把这个路径挂成 `tmpfs`，这也是为什么「换块慢速 U 盘当存储」常常比「CPU 不够」更早成为瓶颈。

保留窗口之外还想留住某段视频，官方给的答案是导出（export）而不是调大保留天数：导出走独立路径，不受保留策略清理。

## 事件出口：MQTT 的真实形状

MQTT 在 Frigate 里是可选的，但要接 Home Assistant 就必须有。官方安装文档把它列在依赖里，并要求 Frigate 与 Home Assistant 连同一个 broker。`mqtt.enabled` 默认为真，`topic_prefix` 默认 `frigate`。

常见话题：

- `frigate/available`：`online` / `stopped` / `offline`，后两者分别来自正常停止与遗嘱消息，适合做可用性探针；
- `frigate/restart`：让 Frigate 退出，交给 Docker 重启策略拉起来；
- `frigate/events`：追踪目标状态变化时发布，`type` 取 `new` / `update` / `end`；
- 0.18 起新增 `frigate/<camera>/<role>/status`，以及按名字启停掩码与区域、切换配置模板（profile）的话题。

`frigate/events` 的载荷是 `{type, before, after}`，其中对象字段包括 `id`、`camera`、`label`、`sub_label`、`score`、`top_score`、`box`、`area`、`ratio`、`region`（本轮识别所用的画面区域）、`current_zones`、`entered_zones`、`has_clip`、`has_snapshot`、`active`、`stationary`、`motionless_count`、`position_changes`、`attributes`、`current_attributes`、`current_estimated_speed` 等。下面是一条 `after` 的节选，字段名与嵌套结构与文档一致：

```json
{
  "type": "update",
  "after": {
    "id": "1607123955.475377-mxklsc",
    "camera": "front_door",
    "label": "person",
    "score": 0.7890625,
    "top_score": 0.958984375,
    "box": [424, 500, 536, 712],
    "area": 23744,
    "ratio": 2.113207,
    "current_zones": ["driveway"],
    "entered_zones": ["yard", "driveway"],
    "active": true,
    "stationary": false,
    "has_clip": false,
    "has_snapshot": false
  }
}
```

置信度字段的真名是 `score`，包围盒是像素坐标的四元组而不是归一化值——这两点在二手教程里错得最多。同一个 `id` 会因为更好的快照或区域变化重复发布，收到重复不要当成新目标。

Home Assistant 侧的官方集成 [frigate-hass-integration](https://github.com/blakeblackshear/frigate-hass-integration) 仍是 HACS 默认仓库里的第三方集成，不是 HA 内核自带。安装前置是 HA 的 `mqtt` 集成已装好并手工配置过，`media_source` 若要媒体浏览则需启用；配置时要填 Frigate 的地址，指向内部免认证端口 `5000` 或带认证的 `8971` 都可以。另有一个可选的配套卡片 `dermotduffy/frigate-hass-card`。

## 端口与直播：8971 才是主入口

| 端口 | 用途 | 备注 |
|------|------|------|
| `8971` | 带认证的界面与 API | 反向代理应该指向这个；0.18 在 nginx 打开 HTTP/2 后，走 8971 的直播与历史视图明显更快 |
| `5000` | 内部免认证的界面与 API | 供 docker 网络内的服务集成用，访问范围要收紧 |
| `8554` | RTSP 重流 | 默认无认证，认证在 `go2rtc` 段配 |
| `8555` | WebRTC | 双向对讲与 WebRTC 连接都走它，TCP 与 UDP 都要映射 |

直播有三种承载方式，官方 [Live View 配置](https://docs.frigate.video/configuration/live/)给了对照：

| 方式 | 分辨率与帧率 | 音频 | 备注 |
|------|------|------|------|
| `jsmpeg` | 720p，帧率跟 `detect -> fps`、上限 10 | 无 | 未配 go2rtc 时的默认 |
| `mse` | 原生 | 有，取决于编解码器 | 配了 go2rtc 时的默认；iPhone 需 iOS 17.1+，Firefox 只支持 H.264 |
| `webrtc` | 原生 | 有，取决于编解码器 | 需要额外配置；`mse` 失败或双向对讲时才会用到 |

WebRTC 不是默认路径：它要 `go2rtc.webrtc` 下的 `candidates` 或 `ice_servers`，要 8555 可达，还要编解码器被浏览器支持。不满足时界面里那个选项直接置灰并写明原因，播放自动退回 mse 或 jsmpeg。

另一件默认开着的事是**智能流媒体**：画面静止时摄像头约每分钟更新一次，一旦有活动才切成完整直播流。这解释了为什么「没人时看着像卡住」，也是它能省下行数带宽的主要原因。想在手机上一直看到实时画面，得 per-camera 关掉这个行为。

## 官方 compose 长什么样

安装文档给出的示例（可裁剪，但字段是对的）：

```yaml
services:
  frigate:
    container_name: frigate
    restart: unless-stopped
    stop_grace_period: 30s
    image: ghcr.io/blakeblackshear/frigate:stable
    shm_size: "512mb"   # 按摄像头数量与分辨率算，见下文
    devices:
      - /dev/bus/usb:/dev/bus/usb           # USB Coral
      - /dev/dri/renderD128:/dev/dri/renderD128  # Intel / AMD 核显独显
    volumes:
      - /etc/localtime:/etc/localtime:ro
      - /path/to/your/config:/config
      - /path/to/your/storage:/media/frigate
      - type: tmpfs
        target: /tmp/cache
        tmpfs:
          size: 1000000000
    ports:
      - "8971:8971"
      # - "5000:5000"   # 内部免认证端口，暴露要谨慎
      - "8554:8554"
      - "8555:8555/tcp"
      - "8555:8555/udp"
    environment:
      FRIGATE_RTSP_PASSWORD: "password"
```

`shm_size` 那一项有明确算法而不是随手写：Docker 默认给 64 MB，Frigate 的 128 MB 默认值够 2 路 720p；容器还会把日志也放进共享内存，最多占 40 MB。所以「三路 1080p 用默认 shm」几乎一定以 `Bus error` 收场。

`version: "3.8"` 这一行在 Compose v2 里已经没有意义，官方示例也不写。推荐的安全加固是 `security_opt: ["no-new-privileges:true"]` 加 `cap_drop: ["ALL"]`；代价是 `telemetry.stats.network_bandwidth` 这项统计要 nethogs，需要 `NET_ADMIN`/`NET_RAW`。真正需要 `privileged: true` 的只有 MemryX 和个别 QNAP 环境。

## 一条警报如何流过系统

把上面几条串起来。设一台 N100 小主机跑 4 路 1080p，用 Coral USB 做检测器。前院那路摄像头命名为 `front_yard`，它的 `objects.track` 加了 `person`，并定义了一个 `yard` 区域、要求警报必须落在该区域内。

晚上 23:14，一个人走进前院。

1. **取流**：识别流的 sub 编码持续解码，按 `fps: 5` 抽帧写入 `/dev/shm` 的帧池。
2. **运动**：第 3 帧起，人体轮廓的像素差超过 `threshold: 30`，`cv2` 轮廓把散点连成运动框。因为时间戳已被运动掩码盖掉，画面右上角不再产生额外运动。
3. **识别**：模型只在运动区域外扩出的那块区域上推理，返回 `person`、`score: 0.61`。`min_score` 是 0.5，因此没被丢掉；但 `threshold` 0.7 还没过，此时只作为候选，`min_initialized`（默认约等于 `fps` 的一半）要求连续命中才建立追踪目标。下一帧 `score: 0.78`，追踪目标建立，拿到 id。
4. **区域与分类**：目标包围盒底边中心进入 `yard`，`entered_zones` 记上该区域。person 是默认警报标签，于是这次时间窗口被标为警报（alert），`frigate/front_yard/record/status` 一类的状态话题同时更新。
5. **沉淀**：快照以不带标注框的 WebP 落到 `/media/frigate/clips`（这是 0.18 的变化，带框的 JPEG 不再落盘）；这一段视频因为匹配保留策略从 `/tmp/cache` 搬到 `/media/frigate/recordings/2026-09-21/15/front_yard/*.mp4`；`pre_capture` 的 5 秒把「人还没进画面」的那几秒也带上了。
6. **出口**：`frigate/events` 发一条 `new`。Home Assistant 的 Frigate 集成把它变成 `binary_sensor` 与媒体浏览条目，触发一条「亮前院灯并推送手机」的自动化；推送里可以带 `/api/events/<id>/snapshot.jpg`，该端点在 0.18 起支持 `bounding_box`、`crop`、`quality` 等查询参数。
7. **回放**：第二天早上你在核查页看到一条红色（警报）核查项，点开进入历史视图，拖动时间轴时相邻摄像头的预览同步跟着走，因为这几路段的时钟对齐在同一时间轴上。

这条链路上任何一环失败，症状都不同：没有事件先看第 2 步的运动框，有事件但分类错看第 4 步的区域与警报标签，有画面没录像看第 5 步的 `record` 层级与磁盘。

## 数字该怎么读

Frigate 在 `/api/metrics` 暴露 Prometheus 指标（受 telemetry 配置控制），把「数字」锚到指标名上比对着界面猜要可靠得多。摄像头侧有 `frigate_camera_fps`（从摄像头吃到多少帧）、`frigate_process_fps`（进入处理链的帧率）、`frigate_skipped_fps`（被跳过的帧率）、`frigate_detection_fps`（每秒跑了几次识别）；检测器侧则是 `frigate_detector_inference_speed_seconds` 与 `frigate_detection_start` 两项。

`detect -> fps` 是**采样上限**，不是实际吞吐。画面静止时 `frigate_detection_fps` 接近 0 而 `frigate_skipped_fps` 很高，这正是设计目的，所以「5 fps 的摄像头识别帧率只有 0.4」不是故障。反过来，如果 `detection_fps` 长期贴着上限，说明运动层在持续误触发，先去 Debug 视图看运动框，而不是加检测器。

`frigate_detector_inference_speed_seconds` 的官方定义就是「跑目标检测花掉的时间」，不含解码与帧跳过。所以同一个 Coral 在 2 路和 8 路上的单次耗时可能差别很小，整机却明显更忙。多出来的开销在 FFmpeg 解码与共享内存帧池上——这也正是安装文档要按摄像头数量和分辨率算 `shm_size` 的原因。**「一张 Coral 能带 N 路」这种结论没法通用**，它随分辨率、帧率与画面运动量而变。官方给的都是定性判断：把推理交给加速卡比 CPU 快一个数量级，能大幅降低 CPU 负载。量化部分只出现在按机型写的承载能力表里，例如某 N100 迷你主机是「几路 1080p、中低活动量」，125H 的机型是「大量 1080p、高活动量」。

存储指标还有一个坑：`frigate_storage_free_bytes` / `_used_bytes` 报的是操作系统对整个文件系统的数字（和 `df` 一致），不是 Frigate 自己录像占了多少。拿它们做「录像涨了多少」的监控报警会失真。

不能从这些数字里推出的：识别准确率。仓库里没有准确率基准，官方提升准确率的路线是换更适合自己场景的模型。默认模型是 `mobiledet` 架构，Coral 与 CPU 都能跑；Frigate+ 另提供 `yolonas`（Intel / NVIDIA / AMD，对小物体更好）与 `yolov9`（硬件覆盖更宽），订阅后可以上传自家摄像头拍到的画面做微调训练。同一个模型在自家院子和在测试集上的差距，主要来自遮挡、夜间与安装高度，这些都不在任何统计页里。

## 0.18 改了哪些边界

如果你是从旧教程接手一套现网 Frigate，v0.18（2026-09-12）的这几处值得逐条比对。它带自动配置迁移，但迁移失败时要手改。

- 带标注的 JPEG 快照不再落盘，只存 `WebP` 干净图，`snapshots.quality` 默认从 70 变 60，`clean_copy` 选项删除；要带框的图改走 `/api/events/<id>/snapshot.jpg`。
- 区域与掩码的配置格式变了，新增 `enabled` 与 `friendly_name`。
- FFmpeg 升到 8（`-rk` 镜像除外），FFmpeg 5 已弃用、0.19 移除；配合 go2rtc 硬件转码有一处已知问题，需要改 `go2rtc` 配置。
- Intel 显卡统计改为直接读内核 DRM 每客户端计数器，不再需要 `intel_gpu_top`、`CAP_PERFMON` 或 privileged，但要求宿主内核 6.5 以上，且数值口径与旧版不同。
- `sync_recordings`、`timelapse_args`、`ui.date_format`、`ui.time_format` 删除；`DELETE /api/export` 换成 `POST /api/exports`。
- DeGirum 检测器移除（该公司 2026-08-01 停止运营），DeepStack 检测器已标记弃用、0.19 移除。
- 在 GPU 上跑 JinaV2 语义搜索模型的要重跑嵌入索引。

同期新增的能力里，对采用决策影响最大的三个：

1. **全量界面配置**。`设置` 覆盖了配置的所有分区，带逐字段校验与文档回链，多数选项（富化、运动、ONVIF、GenAI、go2rtc 流）改完即时生效不用重启。YAML 路线仍然完整保留。
2. **配置模板（Profiles）**。在基础配置之上定义命名的覆盖集，覆盖识别、运动、录像、快照、核查、区域、通知、对象、富化、音频、birdseye 乃至摄像头启停，可在界面或 `frigate/profile/set` 话题上热切。白天/夜间两套参数不用再靠重启。
3. **对话与 VLM 监控**。GenAI 支持多供应商并按 `roles` 分工，自带 llama.cpp 供应商；界面里的 Chat 是一个会调工具的代理，能搜索追踪目标、做相似检索、看当前摄像头上下文、开关摄像头功能、启动 VLM 监控、总结近期活动。VLM 监控会把供应商循环跑在摄像头实时流上。

还有一项对调参价值极高：**Debug Replay**，把已录制的视频当作直播摄像头灌回识别与运动管线。这意味着你可以拿上周那段误报去反复试参数，而不是等下一次真实发生。0.18 同时加了运动搜索（画出区域、找该区域有运动的时间段）和热力图筛选。

## 排查：七类常见故障

| 症状 | 先看什么 |
|------|------|
| 容器起不来、日志里 `Bus error` | `shm_size` 太小。按摄像头数与分辨率重算，同时检查进程与文件句柄上限 |
| `RuntimeError: can't start new thread` 后紧跟 Bus error | 不是 shm，是 PID 上限。容器内比 `pids.current` 与 `pids.max`，用 `--pids-limit` 提高 |
| `OSError: [Errno 24] Too many open files` | 文件句柄。Compose 里给 `ulimits.nofile` 65535 |
| 完全没有事件 | 按顺序确认 `detect.enabled`、`objects.track` 是否只有默认 `person`、运动框是否出现、区域是否要求了 `required_zones` |
| 手机上直播打不开或只有画面没声音 | 音频编解码：mse 要 PCMA/PCMU 或 AAC，webrtc 要 PCMA/PCMU 或 opus。在 go2rtc 里补一路转码流即可两者兼容 |
| H.265 录像在某些浏览器黑屏 | 换 Chrome 108+/Edge/Safari，或让摄像头出 H.264 |
| 配了 webrtc 仍走 mse | `go2rtc.webrtc` 的 `candidates`/`ice_servers` 缺失、8555 不可达、STUN 需要外网、或浏览器不支持该编码。选项置灰时会写原因，浏览器控制台有细节 |

## 采用顺序与不划算的地方

按这个顺序推进，每一步都有可验证的产出：

1. **先确认摄像头值不值**。官方对摄像头的第一要求是 H.264 加 AAC 音频、且能出多路子码流；Wi-Fi 摄像头不推荐（多路同时用时掉线与丢数据明显），Reolink 的 4K 机型问题报告较多、建议 5MP 及以下。这一步没做好，后面所有调参都是在补漏。
2. **单机单路跑通**。`docker compose up` 后打开 `http://<host>:8971`（该端口提供不带 TLS 的认证界面，TLS 交给反代），先用界面配置向导加一路摄像头，只开 `detect`，不急着开录像。
3. **打开 Debug 视图看运动框**，把时间戳、天空、树叶做运动掩码，用 Motion Tuner 定下阈值。这一步决定后面所有的误报量。
4. **配检测器**。有 Intel 核显就用 OpenVINO，有 NVIDIA 用对应 `-tensorrt` 镜像或 ONNX 路径，想低待机功耗就上 Coral 或 Hailo。只有 CPU 就把这步当成临时验证，别当生产形态。
5. **再开录像与保留策略**，按 `continuous` / `motion` / `alerts` / `detections` 四层分别定天数，并给 `/tmp/cache` 挂 tmpfs。
6. **最后接 Home Assistant**：确认 HA 与 Frigate 同 broker、装 HACS 里的官方集成、填 `8971` 地址，然后从「识别到人推送一条通知」开始，再扩到灯与锁。

不适合用 Frigate 的情形也说得清楚：只需要远程看实时画面；摄像头只有 Wi-Fi 且无法改善；环境里没有任何可加速的硬件又要求多路高分辨率；需要把录像托管到对象存储。最后这一条要说明依据——本文核对的 v0.18.0 代码与文档中没有对象存储后端，录像目录只按本地路径或挂载卷处理。走网络存储的官方路径是 Home Assistant 的网络挂载存储（SMB/NFS），不是 S3。

## 五个自测题

**1. 画面里树叶一直在晃，误报很多。第一个该动的参数是哪个，为什么？**

<details>
<summary>参考答案</summary>

先动运动层，不是识别层。给树冠画运动掩码，或用 Motion Tuner 把 `threshold`（默认 30）调大，让晃动不再产生运动框。若只提高 `objects.filters.person.threshold`，模型仍然每帧都在推理，CPU 与加速器的占用不会降下来，而且树叶一旦和别的运动连成一片，误检照样进来。
</details>

**2. 关掉目标检测之后，磁盘还在稳定增长。这矛盾吗？**

<details>
<summary>参考答案</summary>

不矛盾。录像段从取流那一步直接分叉，不经过模型。只要 `record.enabled` 为真且 `continuous.days` 大于 0，全时录像就一直在写。要只留事件段，把 `continuous.days` 与 `motion.days` 归 0，靠 `alerts.retain` / `detections.retain` 保留。
</details>

**3. `objects` 什么都不配时，Frigate 会识别哪些对象？**

<details>
<summary>参考答案</summary>

只跟踪 `person`，因为 `DEFAULT_TRACKED_OBJECTS = ["person"]`。同时 `detect.enabled` 全局默认是 False，所以既不开识别也不加标签时，它实际上是一台纯粹的录像机。此外给核查项配 `alerts.labels` 并不会让模型多识别新物体，那只是分类。
</details>

**4. 为什么有人走进行李箱大小的画面范围后就不再更新位置了？**

<details>
<summary>参考答案</summary>

大概率被判定为静止物体。一个追踪目标在 `detect -> stationary -> threshold` 那么多帧里位置几乎不变就算静止，默认是 10 倍帧率（也就是 10 秒）；`5` fps 下即 50 帧。静止之后识别不再连续跑，只按 `stationary -> interval`（默认同样 50 帧）抽查一次，目标一旦自己动了才恢复常规识别。省算力就是它的目的，副作用正是「不动的东西不再被频繁更新」。另外 `stationary -> classifier` 默认为真，会用一个视觉分类器去判断框抖动但其实静止的物体。
</details>

**5. 想在 Web 界面里画一块「不要检测」的区域，应该用掩码还是区域？**

<details>
<summary>参考答案</summary>

用区域加 `required_zones`。掩码解决的不是「我关心哪块」而是「这块的运动/检出不该触发」，两类掩码分别作用于运动判定和包围盒底边中心；用它来划关注区会导致别处的运动仍触发识别，而目标一旦从关注区外进入就可能不会成为警报。官方对照表把 zone 列为这类诉求的正解。
</details>

## 下一步读哪份代码

按目的选，不按顺序：

- 想看三条链路怎么落地：`frigate/video/`（取流与解码）→ `frigate/motion/improved_motion.py`（差分与轮廓）→ `frigate/object_detection/` 与 `frigate/detectors/`（推理）。
- 想确认某个配置字段还在不在：直接读 `frigate/config/camera/` 下对应的 pydantic 模型，`Field(default=...)` 比任何教程都可信。当前 `camera/` 里有 22 个模块，`record.py`、`detect.py`、`objects.py`、`onvif.py` 是决策最常碰到的四个。
- 想知道某个检测器到底怎么跑：`frigate/detectors/plugins/` 里那 12 个文件，每个都短，`DETECTOR_KEY` 与 `input_tensor` 两件事一眼看完；跨硬件的公共路径在 `detection_runners.py`（ONNX Runtime、OpenVINO、RKNN、CUDA graph 四种 runner）。
- 想找热重载的入口：`frigate/jobs/` 与 `frigate/service_manager/`，以及 0.18 新加的通用进程看门狗。
- 想看事件分类怎么定：`frigate/review/`（核查项与 alert/detection 判定）、`frigate/events/`（追踪目标生命周期）。
- 界面一侧：`web/src/views/` 按页面分目录，`web/public/locales/zh-CN/` 可以直接对照中文文案读键名。

ONVIF 值得单独说，因为它在 Frigate 里有两个完全不同的落点，二手教程常把它们当成一件事。运行时侧看 `frigate/config/camera/onvif.py`，那里只有 `PtzAutotrackConfig`，用途是**云台自动跟踪**：绝对或相对移动、缩放模式与缩放系数，启动时标定电机会把测得的 `movement_weights` 写回配置。装机侧看 0.18 新加的摄像头向导（`web/src/components/settings/wizard/`），`OnvifProbeResults.tsx` 会用 ONVIF 探一批 RTSP 候选地址、逐个试连通再让你挑。所以「ONVIF 能帮你找到流地址」是真的，「配一次就自动发现全部摄像头、之后不用再管」不是。0.18 还顺手重构了运行时那侧，加了 profile 选择与免重启的动态更新。

## 参考

- 仓库与机制：[blakeblackshear/frigate](https://github.com/blakeblackshear/frigate) `dev@285dd5a`（2026-09-19），`frigate/detectors/plugins/`、`frigate/config/camera/`、`frigate/motion/improved_motion.py`、`labelmap.txt`、`LICENSE`
- 官方文档：[Video pipeline](https://docs.frigate.video/frigate/video_pipeline/)、[Installation](https://docs.frigate.video/frigate/installation/)、[Hardware](https://docs.frigate.video/frigate/hardware/)、[Object Detectors](https://docs.frigate.video/configuration/object_detectors/)、[Recording](https://docs.frigate.video/configuration/record/)、[Masks](https://docs.frigate.video/configuration/masks/)、[Motion Detection](https://docs.frigate.video/configuration/motion_detection/)、[Live View](https://docs.frigate.video/configuration/live/)、[Review](https://docs.frigate.video/configuration/review/)、[MQTT](https://docs.frigate.video/integrations/mqtt/)、[Home Assistant](https://docs.frigate.video/integrations/home-assistant/)
- 版本信息：GitHub Release [`v0.18.0`](https://github.com/blakeblackshear/frigate/releases/tag/v0.18.0)（2026-09-12）的 Breaking Changes 与 New Features 全文
- 集成：[blakeblackshear/frigate-hass-integration](https://github.com/blakeblackshear/frigate-hass-integration)、[dermotduffy/frigate-hass-card](https://github.com/dermotduffy/frigate-hass-card)
- 统计口径：GitHub API 于 2026-09-21 读取（stars 36,017、forks 3,612、issue 与 PR 合计 105、created 2019-01-26、pushed 2026-09-20、语言字节数）
