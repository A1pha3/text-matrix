---
title: "commaai/openpilot 深度拆解：开源 L2 驾驶辅助的真正边界在哪里"
date: "2026-06-26T21:05:21+08:00"
slug: "commaai-openpilot-open-source-driver-assist-guide"
description: "openpilot 是 comma.ai 开源的 L2 ADAS，覆盖 332 款车。本文拆解 cereal 总线、modeld/controlsd/locationd 架构、安全模型与适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["openpilot", "自动驾驶", "commaai", "Python", "ADAS"]
---

# commaai/openpilot 深度拆解：开源 L2 驾驶辅助的真正边界在哪里

## 学习目标

读完之后，你应该可以回答下面五件事：

1. openpilot 的核心定位是 L2 ADAS（Advanced Driver Assistance System，先进驾驶辅助系统）而不是 L4 自动驾驶，它的安全模型、硬件要求和"300+ 车型"三个词背后各自承担什么。
2. cereal 消息总线 + capnp（Cap'n Proto 序列化协议） + msgq（基于共享内存的发布订阅总线）这套"消息驱动多进程"骨架，让 modeld、controlsd、selfdrived、locationd、pandad、card 各自独立运行的机制。
3. 一次"车道内自动跟车 + 居中"任务，从摄像头帧到 CAN 总线（Controller Area Network，控制器局域网，是车载设备之间通信的协议）字节的真实流转路径。
4. 为什么 panda 这个用 C 写的安全固件要单独存在，以及 ISO 26262（汽车功能安全国际标准）和 MISRA C（针对嵌入式 C 语言的编码规范）这两条规则链在 openpilot 里卡的是什么。
5. 什么样的人适合在自己的车上装 openpilot，什么样的人应该立刻走开。

## 目录

- [1. 一句话定位：L2，不是 L4](#1-一句话定位l2-不是-l4)
- [2. 核心数据与硬件基线](#2-核心数据与硬件基线)
- [3. 系统地图：消息总线 + 七大进程](#3-系统地图消息总线--七大进程)
- [4. 子系统边界：把容易混淆的并行机制拆开](#4-子系统边界把容易混淆的并行机制拆开)
  - [4.1 modeld：端到端驾驶模型](#41-modeld端到端驾驶模型)
  - [4.2 locationd：纯视觉定位](#42-locationd纯视觉定位)
  - [4.3 controlsd：横纵向控制器](#43-controlsd横纵向控制器)
  - [4.4 selfdrived：状态机与告警](#44-selfdrived状态机与告警)
  - [4.5 card + opendbc：车型接口层](#45-card--opendbc车型接口层)
  - [4.6 pandad：CAN 总线桥](#46-pandadcan-总线桥)
  - [4.7 monitoring：驾驶员监控](#47-monitoring驾驶员监控)
- [5. cereal：所有进程用同一种语言说话](#5-cereal所有进程用同一种语言说话)
- [6. 一次跟车任务如何流过系统](#6-一次跟车任务如何流过系统)
- [7. 安全模型：panda 才是"硬刹车"那一道](#7-安全模型panda-才是硬刹车那一道)
- [8. benchmark 段：测的是什么，不能推出什么](#8-benchmark-段测的是什么不能推出什么)
- [9. 数据上传、隐私与开源边界](#9-数据上传隐私与开源边界)
- [10. 适用边界与采用顺序](#10-适用边界与采用顺序)
- [11. 常见问题与排查指引](#11-常见问题与排查指引)
- [12. 延伸阅读](#12-延伸阅读)

## 1. 一句话定位：L2，不是 L4

openpilot 是 [commaai/openpilot](https://github.com/commaai/openpilot) 项目。它在 GitHub 上的描述只有两行：

> openpilot is an operating system for robotics. Currently, it upgrades the driver assistance system in 300+ supported cars.

把第一行和第二行分开读很重要。第一行讲野心：把整套系统定位成"机器人操作系统"，暗示它的设计目标是承载比驾驶辅助更复杂的东西。第二行讲现状：当前在 332 款车上升级原厂 ADAS。

理解这两句之后，再看 [docs/SAFETY.md](https://github.com/commaai/openpilot/blob/master/docs/SAFETY.md) 的开头：

> openpilot is an Adaptive Cruise Control (ACC) and Automated Lane Centering (ALC) system. Like other ACC and ALC systems, openpilot is a failsafe passive system and it requires the driver to be alert and to pay attention at all times.

注意几个关键词：`Adaptive Cruise Control`（自适应巡航）、`Automated Lane Centering`（车道居中）、`failsafe passive`（失效安全 + 被动系统）、`requires the driver to be alert`。这就把它的能力边界说死了：自动跟车 + 车道居中，是 SAE 分级里的 L2。README 末尾也明说 "ALPHA QUALITY SOFTWARE FOR RESEARCH PURPOSES ONLY. THIS IS NOT A PRODUCT"。

把它当 L4 用，或者把它当 L4 来评估，是绝大多数关于 openpilot 的误读来源。下文会回到这一边界反复强调。

## 2. 核心数据与硬件基线

下表所有数字均来自 GitHub 仓库 API 和 2026-06-26 当下的仓库状态。

| 维度 | 数值 / 说明 |
|------|------|
| 仓库 | [commaai/openpilot](https://github.com/commaai/openpilot) |
| Stars / Forks / Watchers | 61,636 / 11,038 / 1,314（截至 2026-06-26） |
| 主语言 | Python（panda 固件与少量内核相关代码为 C） |
| 许可证 | MIT（安全相关部分有额外约束，详见 [docs/SAFETY.md](https://github.com/commaai/openpilot/blob/master/docs/SAFETY.md)） |
| 最新 Release | `v0.11.1`，发布于 2026-06-05；`RELEASES.md` 中已记录 `0.11.2`（2026-06-15） |
| 仓库体积 | 1,152,088 KB（含 LFS 大模型权重） |
| 支持车型 | 332 款（来自 [docs/CARS.md](https://github.com/commaai/openpilot/blob/master/docs/CARS.md) 表头） |
| 硬件 | comma four（代号 `mici`） / comma 3X（代号 `tizi`），外加对应 car harness |
| 软分支 | `release-mici`（comma four 正式版）、`release-tizi`（comma 3X 正式版）、`nightly`、`nightly-dev` |
| 安装命令 | `bash <(curl -fsSL openpilot.comma.ai)` |

数据来源：GitHub REST API `repos/commaai/openpilot`、仓库根目录 `README.md`、`RELEASES.md`、`docs/CARS.md` 顶部 "332 Supported Cars"，访问于 2026-06-26 21:05 BJT。

`openpilot` 在 GitHub 仓库 `tags` 字段里写的是 `advanced-driver-assistance-systems`、`driver-assistance-systems`、`robotics` 三项。第一个就是它在 L2 ADAS 这条赛道上的标准定位。

## 3. 系统地图：消息总线 + 七大进程

openpilot 的代码组织是教科书级别的"多进程消息驱动"。[openpilot/](https://github.com/commaai/openpilot/tree/master/openpilot) 目录下大致分四个一级目录：

```text
openpilot/
├── cereal/          # 消息总线 + capnp schema（共享内存 pub/sub）
├── common/          # 通用工具：参数、实时调度、日志、GPS、硬件抽象
├── selfdrive/       # 驾驶主循环：selfdrived / controlsd / modeld / locationd / card / pandad / monitoring
└── system/          # 系统服务：camerad / sensord / loggerd / manager / athena / updated / webrtc …
```

这张表是后面所有讨论的骨架，记住它就够在源码里找东西了。

| 进程 | 角色 | 关键输入 | 关键输出 | 频率 / 实时性 |
|------|------|----------|----------|---------------|
| `camerad` | 摄像头采集，输出 YUV（亮度色度视频帧格式）帧 | 摄像头硬件 | `roadCameraState` / `driverCameraState` / `wideRoadCameraState` | 20 Hz |
| `modeld` | 跑 driving model，输出轨迹/行为 | `roadCameraState`（+ 历史帧） | `modelV2`（规划点序列、`desiredCurvature`、`shouldStop`） | 约 5 Hz 模型前向，100 Hz 控制读取 |
| `locationd` | 纯视觉自定位 + IMU 卡尔曼滤波（IMU 即惯性测量单元） | IMU、`roadCameraState` | `livePose`、`liveCalibration`、`liveParameters`、`liveTorqueParameters`、`liveDelay` | 100 Hz |
| `radard` | 视觉雷达（可选，外部雷达被禁后用视觉补位） | `modelV2`、车距摄像头 | `radarState` | 20 Hz |
| `card` | 车型指纹识别 + 与 opendbc（Comma DBC，CAN 报文编解码库） 交互 | CAN 帧（`can`） | `carState`、`carParams` | 100 Hz |
| `controlsd` | 横向 + 纵向控制器 | `modelV2`、`liveParameters`、`livePose`、`carState` | `carControl`（扭矩 / 角度 / 加速度） | 100 Hz |
| `selfdrived` | 状态机 + 告警 + 驾驶员监控仲裁 | 所有上述消息 | `selfdriveState`、`onroadEvents` | 100 Hz |
| `pandad` | 跟硬件 panda 通信，转换 `sendcan` ↔ `can` | `carControl` | CAN 帧 | 100 Hz |
| `manager` | 进程监督、热更新、报警 | 进程心跳 | 启停信号 | 持续 |

进程之间不直接互相 import，而是通过 `cereal` 提供的 `PubMaster` / `SubMaster` 订阅发布消息。这条总线是整个 openpilot 的"神经系统"，下面专门拆一节。

下面这张图给出最关键的三个进程（modeld → controlsd → card → pandad → 车）的关系：

```text
┌─────────────────┐    图像帧     ┌──────────────────┐
│  camerad        │ ───────────► │  modeld          │
│  (camera HW)    │              │  (tinygrad ONNX) │
└─────────────────┘              └────────┬─────────┘
                                          │ modelV2
                                          ▼
┌─────────────────┐   carState    ┌──────────────────┐
│  card           │ ───────────► │  controlsd       │
│  (opendbc)      │              │  LaC / LoC       │
└────────┬────────┘              └────────┬─────────┘
         │ CAN 帧                         │ carControl
         ▼                                ▼
┌─────────────────┐               ┌──────────────────┐
│  pandad         │ ◄──────────── │  selfdrived      │
│  (panda 固件)   │  sendcan      │  (状态机)        │
└────────┬────────┘               └──────────────────┘
         │ CAN
         ▼
      [ 车辆 ]
```

`selfdrived` 没有出现在主链路里，但它订阅了 `carControl` 的所有上游，用来决定整套系统是否处于"enabled / active / 报警"状态。

## 4. 子系统边界：把容易混淆的并行机制拆开

openpilot 里至少有四套机制容易互相串线：模型推理、视觉定位、控制器、安全仲裁。下文把它们各自的边界画清楚。

### 4.1 modeld：端到端驾驶模型

`openpilot/selfdrive/modeld/` 下的核心是 `modeld.py`，模型权重是 `models/driving_supercombo.onnx` 或更新版本（如 `big_driving_supercombo.onnx`）。模型在 tinygrad 框架上推理，输出三类信息：

- **规划点**（`plan`）：未来若干秒的位移、速度、加速度序列。
- **行为意图**（`meta.desire`）：车道保持 / 变道 / 转向灯等离散信号。
- **视觉侧输出**（`leaderProb`、`laneLineProb` 等）：供 `radard` 与 `controlsd` 二次过滤。

`modeld.py` 把"动作"和"规划"分了两条路径：

- 当 `model_output` 有 `action` 键时（如 Experimental 模式的 E2E 端到端），直接用 `action[0,0]` 算曲率，用 `action[0,1]` 算加速度。
- 否则按 `plan` 算 `desired_accel` 和 `desired_curvature`。

RELEASES 显示 0.10.0 之后 Experimental 模式从"MPC（Model Predictive Control，模型预测控制）做纵向 + 学习策略做横摆"切到了"World Model 端到端规划"（[RELEASES.md 0.10.0](https://github.com/commaai/openpilot/blob/master/RELEASES.md)）。这条切换是模型层最大的变化，但本车纵向控制默认仍是 MPC，长距规划由模型给、闭环控制由 controlsd 做。

### 4.2 locationd：纯视觉定位

`openpilot/selfdrive/locationd/locationd.py` 是一个卡尔曼滤波器（Kalman Filter，递归状态估计算法）：

- 状态量：IMU 在车体坐标系中的位置、速度、姿态。
- 观测：摄像头来的 `posenet` 视觉位姿估计，加速度计、陀螺仪。
- 输出：`livePose`（位姿）、`liveCalibration`（roll/pitch 安装偏差）、`liveParameters`（`stiffnessFactor`、`steerRatio`）、`liveDelay`（横向延迟）、`liveTorqueParameters`（用于 `LatControlTorque`）。

RELEASES 0.9.8 写过一句关键的话："Localizer rewritten to remove GPS dependency at runtime"。这意味着 openpilot 的定位不依赖 GPS，地下车库也能跑。这条性质对很多人来说反直觉，因为大家都以为自动驾驶需要 GPS。

`locationd` 里有一组显式的 sanity check 常量，比如 `ACCEL_SANITY_CHECK = 100.0 m/s^2`、`ROTATION_SANITY_CHECK = 10.0 rad/s`、`TRANS_SANITY_CHECK = 200.0 m/s`。任何超过这个量级的输入会被视为传感器故障直接丢弃，不会污染滤波器。

### 4.3 controlsd：横纵向控制器

`openpilot/selfdrive/controls/controlsd.py` 是 L2 系统的"动力总成"。它读取的频道列表本身就是它的输入合同：

```python
self.sm = messaging.SubMaster([
  'liveDelay', 'liveParameters', 'liveTorqueParameters', 'modelV2', 'selfdriveState',
  'liveCalibration', 'livePose', 'longitudinalPlan', 'lateralManeuverPlan',
  'carState', 'carOutput', 'driverMonitoringState', 'onroadEvents', 'driverAssistance'
], poll='selfdriveState')
```

横向控制器（`LaC`）有四种实现，按 `CP.steerControlType` 切换：

- `LatControlAngle`：直接发方向盘转角信号。
- `LatControlCurvature`：发曲率信号。
- `LatControlPID`：用 PID（比例-积分-微分控制器）算法。
- `LatControlTorque`：用扭矩信号，参数由 `liveTorqueParameters` 在线更新。

纵向控制器（`LoC`）负责跟车、加减速、停车起步，它读 `longitudinalPlan.aTarget` 和 `shouldStop`。

`controlsd` 在发布 `carControl` 前还会做一件事：把 `actuators` 所有字段做 `math.isfinite` 检查，任何 NaN/Inf 都会被强制清零。这一点在 `controlsd.py` 第 142 行附近，是 L2 系统的隐性安全网之一。

### 4.4 selfdrived：状态机与告警

`openpilot/selfdrive/selfdrived/selfdrived.py`（562 行）做三件事：

1. **状态机**：`StateMachine` 类把整个系统从 `disabled` → `preEnabled` → `enabled` → `softDisabling` → `disengaged` 串起来。
2. **事件归并**：`Events` 类把来自 `carOutput`、`driverMonitoringState`、`pandaStates`、`onroadEvents` 等的事件统一归并，再决定 `NO_ENTRY`（不允许进入）/ `WARNING` / `USER_DISABLE`。
3. **告警文本**：`AlertManager` 把事件翻译成人能看的字（`alertText1`、`alertText2`）和声音（`alertSound`）。

`selfdrived` 还会做一件很关键的事：在 `self.enabled` 的前提下，如果 `pandaStates` 里有任何一个非 silent 模式的 panda 不报 `controlsAllowed`，`mismatch_counter` 自增；超过阈值就强制 disengage。这是 panda 与 selfdrived 之间的"投票不一致"检测。

### 4.5 card + opendbc：车型接口层

`openpilot/selfdrive/car/card.py` 是车型接口层的入口。它通过 `opendbc.car.interfaces` 拿到 `CarInterfaceBase`，再调用 `opendbc.car.car_helpers.get_car` 根据 CAN 帧里的固件版本号做"车型指纹"识别（car fingerprinting）：

```python
self.CI = interfaces[self.CP.carFingerprint](self.CP)
```

这一步是 openpilot 能支持 332 款车的原因：每款车有独立的 finger-print 规则、独立的安全模型、独立的消息解码（DBC 文件是 CAN 报文与信号的对照表）。`opendbc` 是个独立子模块（仓库里以 git submodule 形式引入），`opendbc/safety/` 下的代码是用 C 写的车型安全策略，正是 [docs/SAFETY.md](https://github.com/commaai/openpilot/blob/master/docs/SAFETY.md) 里说的"the code enforcing the safety model lives in panda and is written in C"。

`card` 还会处理 OBD 多路复用：

```python
def obd_callback(params: Params) -> ObdCallback:
  def set_obd_multiplexing(obd_multiplexing: bool):
    if params.get_bool("ObdMultiplexingEnabled") != obd_multiplexing:
      ...
```

这是很多车（特别是较新的 GM、Ford）必须经过的一步，没它就拿不到完整 CAN 流。

### 4.6 pandad：CAN 总线桥

`openpilot/selfdrive/pandad/` 把上层抽象的 `sendcan`（一个 cereal 服务）转成 panda 硬件能识别的 CAN 帧，再送到车上；同时反向把车上的 CAN 帧解码成 cereal `can` 消息。panda 硬件本身有自己的 STM32 固件，里面固化了对"安全扭矩上限"的硬约束：

- 横向最大力矩限制。
- 纵向最大加速度限制。
- "司机踩刹车 / 按键 cancel → 立刻取消一切 control" 优先于一切。

这条约束的"硬"在于：即使 openpilot 上层进程崩溃，panda 也会在固定时间窗内自动切断输出。这就是为什么 [docs/SAFETY.md](https://github.com/commaai/openpilot/blob/master/docs/SAFETY.md) 把 panda 当成 "the code enforcing the safety model"。

### 4.7 monitoring：驾驶员监控

`openpilot/selfdrive/monitoring/` 跑一个独立的 DMSC（Driver Monitoring System Controller，驾驶员监控系统控制器）模型 `dmonitoring_model.onnx`，从 `driverCameraState` 估出当前驾驶员的头部姿态、视线方向、是否在打电话 / 抽烟。`selfdrived` 拿到 `driverMonitoringState.alwaysOnLockout` 后会触发 `EventName.tooDistracted`，把系统挡在 `NO_ENTRY` 状态，直到下次点火循环。

注意一件事：openpilot 里的驾驶员监控是"必须开着"的，任何 fork 都不能禁用或削弱它，否则按 [docs/SAFETY.md](https://github.com/commaai/openpilot/blob/master/docs/SAFETY.md) "Failure to comply with these standards will get you and your users banned from comma.ai servers."

## 5. cereal：所有进程用同一种语言说话

`openpilot/cereal/` 是整个项目的"语言"。它用 [Cap'n Proto](https://capnproto.org/)（一种高性能二进制序列化协议，类似 Protocol Buffers）做序列化，底层走 [msgq](https://github.com/commaai/msgq) 共享内存 pub/sub。Schema 在 `log.capnp` 里，主结构是 `Event`，有一个 `logMonoTime`（单调时间戳，避免系统时间跳变影响因果关系）和一个 `valid` 标志位。

`cereal` 的 README 明确两条规矩：

1. 所有字段必须使用 SI 国际单位制（米、秒、弧度等），除非字段名已经标了其他单位（比如 `steeringAngleDeg`）。这样跨进程共享时不用做单位换算。
2. 修改 schema 时优先"加字段 / 加结构体"，避免重命名和改类型，保证旧 log 仍能被新代码读出来。

`cereal/services.py` 把每个服务的频率和队列大小注册成枚举：

```python
class QueueSize(IntEnum):
  BIG   = 10 * 1024 * 1024   # 视频帧、大模型输出
  MEDIUM = 2 * 1024 * 1024   # 高频 CAN、直播
  SMALL = 250 * 1024         # 多数服务
```

`can` 服务跑 100 Hz、占 `BIG` 队列；`selfdriveState` 跑 100 Hz、占 `SMALL`。队列大小不是随便定的，是按"消费者最坏能承受多长的突发延迟"反推的。

`cereal` 还有个值得单独说的设计：`custom.capnp` 留了一组保留事件 ID，专门给 fork 用。主线 openpilot 不会动这些 ID，fork 加新事件时如果只用这些 ID 就能保证"fork 的 log 永远能被主线代码读出来"。这是一个给长期演进用的兼容性保险。

## 6. 一次跟车任务如何流过系统

下面用"前车减速、openpilot 跟着减速、最后停稳"这条最日常的纵向任务，把上面六个进程串起来。

```text
时刻 t=0.00s
  车辆以 80 km/h 跟车，模型与控制器进入稳态。

时刻 t=0.00s （100 Hz 控制循环开始）
  pandad            收到车上 100 Hz CAN 帧，发布到 cereal 'can' 频道。
  card              订阅 'can'，解出 vEgo=80km/h、steerAngle、brakePressed、leadDistance 等，
                    发布到 'carState'。
  modeld            订阅 'roadCameraState'（camerad 出），把过去若干帧叠起来送进
                    driving_supercombo.onnx，得到新的 plan / desire / leaderProb，
                    发布到 'modelV2'。
  radard            订阅 'modelV2'，根据 leaderProb + 模型给出的车距生成 'radarState'。
  controlsd         订阅 'modelV2' + 'carState' + 'radarState' + 'liveParameters' +
                    'livePose'，调用 LaC / LoC，发布 'carControl'。
  selfdrived        订阅全部上游 + 'driverMonitoringState'，决定 'selfdriveState.enabled'
                    是否仍为 True。

时刻 t=0.05s
  pandad            把 'carControl' 里 LoC 给出的 accel=-1.8 m/s^2 编码成 CAN 帧，写到 sendcan。
  panda 固件        校验：accel 在安全限值内、未踩刹车、未 cancel → 转发给车。

时刻 t=2.00s
  前车完全停下。
  card 报告 vEgo=0、standstill=True。
  modeld plan 输出 'shouldStop=True'，曲率清零。
  controlsd 把 LoC 状态切到 'stopping'，actuators.accel → 维持 ~ -0.4 m/s^2（保持刹车压力）。
  selfdrived 发布 selfdriveState.alertStatus="hold"。

时刻 t=2.50s
  全部进程进入稳态：vEgo=0、shouldStop=True、carControl.enabled=True。
  pandad 不再写新 CAN 帧，只接收车上"停稳确认"的心跳。
  selfdrived 在 'selfdriveState.experimentalMode=True' 时会允许用户在仪表上"resume"。
```

把这条链路看清楚就够了，因为它基本就是横向（车道居中）的翻版：模型给 `desiredCurvature`，`controlsd` 用对应的 `LatControl*` 把曲率变成转角 / 扭矩，pandad 写 CAN，剩下的横向安全约束也由 panda 固件强制。

## 7. 安全模型：panda 才是"硬刹车"那一道

`docs/SAFETY.md` 把安全归结为两条：

1. 司机必须能通过踩刹车或按 cancel 立刻拿回控制权。
2. 系统给出的执行器命令必须落在合理范围内（[SAFETY.md 提到 ISO 11270 与 ISO 15622，横向最大 0.9 秒达到 1m 横向偏差](https://github.com/commaai/openpilot/blob/master/docs/SAFETY.md)）。

这两条规则的执行者不是 Python，是 C。panda 固件是 [commaai/panda](https://github.com/commaai/panda) 仓库里的代码，用 MISRA C 风格约束，专门管三件事：

- 给执行器发命令时硬限速（steer torque 上限、accel 上限）。
- 任何违反限速的输入直接丢弃。
- 心跳超时自动归零。

openpilot 上层对安全的处理方式是"信任 panda + 用 selfdrived 兜底"：

- selfdrived 不会主动做硬刹，但会在 `NO_ENTRY` 状态下阻止系统进入 enabled。
- 一旦检测到 selfdrived 自身定义的 `ExcessiveActuationCheck` 超阈（[selfdrived/helpers.py](https://github.com/commaai/openpilot/blob/master/openpilot/selfdrive/selfdrived/helpers.py)），会设置 `Offroad_ExcessiveActuation` 参数，下次启动直接报警。

[SAFETY.md](https://github.com/commaai/openpilot/blob/master/docs/SAFETY.md) 末尾给 fork 划了三条红线：

1. 不能禁用或削弱驾驶员监控。
2. 不能禁用或削弱 excessive actuation 检查。
3. 如果改 `opendbc/safety/`，必须保留并通过所有 safety tests。

`comma.ai` 的原话是 "Failure to comply with these standards will get you and your users banned from comma.ai servers."。这意味着你 fork 自用可以，但你 fork 的合规问题会直接影响能不能用 comma connect 同步数据。

## 8. benchmark 段：测的是什么，不能推出什么

openpilot 没有像 nuScenes（自动驾驶公开数据集）或 Waymo 开放数据集那样的传统学术 benchmark。它的"成绩"由两套指标构成，混在一起读会误读。

### 8.1 release 里的纵向 / 横向性能指标

RELEASES.md 0.10.0 写过：

> New training architecture: ... Longitudinal MPC replaced by E2E planning from World Model in Experimental Mode. Action from lateral MPC as training objective replaced by E2E planning from World Model.

这一条对应的"性能"是模型层面的：

- 训练时把"横向 MPC 的动作"作为监督信号换成"World Model 的端到端规划"。
- 实验模式（Experimental Mode）下纵向也用 World Model 输出。

**它测的是什么**：comma 内部用近 300+ 用户上传的真实驾驶片段做 replay，模型在 replay 帧上的预测误差。

**不能推出什么**：

- 不能推出"openpilot 在你所在城市 / 你开的车型 / 你遇到的特定施工场景里一样好"。模型是数据驱动的，comma 的数据集中在北美。
- 不能推出"Experimental Mode 一定比默认模式更稳"。Experimental 是 opt-in，默认是更保守的 MPC + 模型混合路径。

### 8.2 release 里的硬件 / 功耗指标

RELEASES.md 0.11.0 写过：

> Reduce comma four standby power usage by 77% to 52 mW
> comma four support

RELEASES.md 0.9.8 写过：

> Image processing pipeline moved to the ISP ... Power draw reduced 0.5W

**它测的是什么**：在 comma 自己的硬件上、用 comma 自己的固件版本测出的功耗。

**不能推出什么**：

- 不能推出"你买的别的设备跑 openpilot 也是这个功耗"。ISP 优化、电源管理策略都是与 comma four 芯片绑定的。
- 不能推出"低功耗意味着低发热"，`RELEASES.md 0.11.1` 同时改动了 thermal policy，因为功耗降下来后峰值热行为变了。

把两类数字放在一起看，结论是：openpilot 的 release notes 是在告诉你"comma 自己的硬件 + 自己的数据 + 自己的 replay 系统下，这个版本相对上一个版本进步在哪"。它不是学术意义上的 benchmark，**不能直接被引申为通用能力声明**。

## 9. 数据上传、隐私与开源边界

README 末尾的两段 collapsed block 是常被忽略的关键信息：

1. **默认会上传驾驶数据**到 comma 服务器，可以在 comma connect 看到，使用者也可以在设置里关掉。
2. **数据范围**：road-facing 摄像头、CAN、GPS、IMU、磁力计、温度传感器、crash、操作系统日志；驾驶员摄像头和麦克风只在 opt-in 时才记录。

这意味着两件事：

- 即使你跑的是开源代码、build 自家镜像，**数据上传路径仍然是 comma 控制的**。如果你 fork 后要彻底切断上传，需要自己改 `system/athena/`（comma connect 客户端）以及 `system/loggerd/`。
- 这条规则反过来也是它能用"几百辆车贡献数据"训练模型的基础：开源不等于零数据回报。

LICENSE 是 MIT，但 [SAFETY.md](https://github.com/commaai/openpilot/blob/master/docs/SAFETY.md) 末尾对 fork 加了约束。这两件事不矛盾：MIT 允许你 fork、读、改、商用；SAFETY 附加条件要求你 fork 后的安全代码不能被削弱。冲突的极端情况是：你可以 fork 出来改任何东西，但你不能再用 openpilot 商标，也不能再上传到 comma.ai 的服务器（会被 ban）。

## 10. 适用边界与采用顺序

### 10.1 推荐采用顺序

如果你是第一次接触 openpilot，按下面的顺序走最稳：

```text
1.  读 docs/SAFETY.md、docs/CARS.md 顶部、README 末尾的 ALPHA 声明。
    目的：先确定你的车型、你的法律环境、你的安全预期。
2.  在 comma.ai/shop 确认硬件：comma four（新车首选）或 comma 3X（已有设备）。
3.  用默认 release 分支（release-mici 或 release-tizi），不要先上 nightly。
4.  装车后先开一周 dashcam 模式（被动模式，不控车），只跑 selfdrived 自身的告警逻辑。
5.  启用 ACC + ALC 后，先在熟悉路段白天跑，再扩展到夜间 / 雨天 / 高速。
6.  上传数据前在设置里关掉 / 留存，看自己能不能接受。
7.  Experimental Mode 最后开。它是 opt-in 的实验模式，不要与默认模式混用。
```

### 10.2 谁该先用，谁可以等等

| 角色 | 建议 |
|------|------|
| 北美 + comma 已有硬件 + 车型在 [docs/CARS.md](https://github.com/commaai/openpilot/blob/master/docs/CARS.md) 里 | 推荐先用默认 release 分支 |
| 关注安全代码 / 想做 fork 的工程师 | 直接读 [panda](https://github.com/commaai/panda) + `opendbc/safety/`，不要只看 Python 侧 |
| 学术研究者 | 用 `tools/replay` 跑历史 log，注意 model 输出 `action` 字段是相对值，不能直接当通用 L4 评估基准 |
| 不在支持列表里 | 不要硬塞。可以看 [comma_ai/voyage](https://github.com/commaai/voyage)（非 ADAS 项目）做参考 |
| 当地法律明确禁止改装车辆 | 不要装。openpilot 是辅助系统，但仍会修改 CAN 流量 |
| 期望 openpilot 替代 L2+ 量产车 | 不要指望。Honda Sensing / Toyota TSS / GM Super Cruise 都有车企级安全流程覆盖，openpilot 走的是开源 + 灰度路径 |

### 10.3 决策检查清单

在动键盘买硬件之前，先把这十条过一遍：

1. 我的车在 `docs/CARS.md` 列表里吗？
2. 列表里对应行的"Hardware Needed"我可以一次性买齐吗？
3. 我所在地区对"非 OEM 厂商提供的 L2 系统"有没有明确法律限制？
4. 我能否接受 comma 默认上传驾驶数据？如果不能，我是否愿意自己改 `system/athena`？
5. 我能不能保持注意力（驾驶员监控是硬约束）？
6. 我有没有在事故 / 异响 / 急刹时立即人工接管的能力？
7. 我是否接受 "ALPHA QUALITY SOFTWARE FOR RESEARCH PURPOSES ONLY" 这条免责声明？
8. 我有没有至少一次回到 dashcam 模式的回退计划？
9. 我知不知道 `nightly` 分支是会"do not expect this to be stable"的？
10. 我知不知道 `Experimental Mode` 与默认模式背后的训练数据不同？

十题中有任何一题答"否"，就先把那一题解决再说。

## 11. 常见问题与排查指引

下面这些不是 FAQ 答案，是 openpilot 这类 L2 系统部署里**真正会反复出现**的工程问题，对应排查方向。

| 现象 | 排查方向 |
|------|----------|
| 装好后 `selfdriveState.enabled` 一直是 false | 99% 是 `NO_ENTRY` 事件未消。最常见三类：`carUnrecognized`（车型 fingerprint 失败）、`tooDistracted`（驾驶员监控未通过）、`calibrationIncomplete`（`locationd` 还在累计 roll/pitch） |
| `pandaStates` 一直报 `controlsAllowed=False` | 大概率是 harness 接反、CAN 速率不匹配、或车辆本身在某种 fail-safe 状态。先看 `pandaStates.safetyModel` 是否是 `silent` |
| 模型输出曲率震荡、方向盘来回抖 | 先看 `liveParameters.stiffnessFactor` 与 `steerRatio` 是否收敛；再看 `liveDelay` 数值是否合理（方向盘机械延迟通常 0.05-0.2s）。这两个参数未收敛前不要用 Experimental Mode |
| Experimental Mode 在某条路特别激进 | 这是数据驱动的副作用。回到默认模式，或在 `OnroadEvents` 里看是不是有 `Experimental longitudinal unavailable on this car` 之类的提示 |
| 升级后摄像头画面偏色 / 帧率掉 | 看 `system/camerad/` 的 commit log。0.9.8 之后 ISP 流水线整体迁移过，camera tuning 参数也调整过 |
| 上传数据失败 | `system/athena/` 客户端的网络与认证分支；不在本文展开 |
| fork 后跑 `openpilot selfdrive test process_replay` 报与主线不一致 | `process_replay` 是给开发者保证"我的改动不破坏已知 replay 输出"的 CI 流程，按需加载 `references/blog-deep-dive.md` 的自检项也类似思路 |

## 12. 延伸阅读

- 仓库主页：[github.com/commaai/openpilot](https://github.com/commaai/openpilot)
- 安全文档：[docs/SAFETY.md](https://github.com/commaai/openpilot/blob/master/docs/SAFETY.md)
- 车型清单：[docs/CARS.md](https://github.com/commaai/openpilot/blob/master/docs/CARS.md)
- 消息总线：[openpilot/cereal/README.md](https://github.com/commaai/openpilot/blob/master/openpilot/cereal/README.md)
- 硬件固件：[github.com/commaai/panda](https://github.com/commaai/panda)
- 车型编解码：[github.com/commaai/opendbc](https://github.com/commaai/opendbc)
- 消息队列：[github.com/commaai/msgq](https://github.com/commaai/msgq)
- 训练基础设施：[blog.comma.ai "Learning to Drive from a World Model"](https://blog.comma.ai/)（CVPR 论文，被 RELEASES 0.10.0 引用）

正文里所有数字、命令、文件路径均可在以上链接交叉验证；信息边界已标在第 8 节"benchmark 段"。本文不覆盖 comma connect 的商业化、comma four 的硬件 BOM（Bill of Materials，物料清单）以及 openpilot 与 Voyage（comma.ai 旗下自动驾驶公司）的关系。
