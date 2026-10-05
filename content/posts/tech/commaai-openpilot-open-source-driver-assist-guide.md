---
title: "commaai/openpilot 深度拆解：开源 L2 驾驶辅助的真正边界在哪里"
date: "2026-06-26T21:05:21+08:00"
lastmod: "2026-10-01"
slug: "commaai-openpilot-open-source-driver-assist-guide"
github_repo: "commaai/openpilot"
source_key: "gh:commaai/openpilot"
description: "openpilot 是 comma.ai 开源的 L2 ADAS，覆盖 335 款车。本文从 cereal 消息总线、modeld/locationd/controlsd 架构、panda 安全固件到适用边界，逐层拆解这套开源 L2 系统的真实能力与局限。"
draft: false
categories: ["技术笔记"]
tags: ["自动驾驶", "Python"]
---

# commaai/openpilot 深度拆解：开源 L2 驾驶辅助的真正边界在哪里

## 1. 一句话定位：L2，不是 L4

openpilot 是 [commaai/openpilot](https://github.com/commaai/openpilot) 项目。GitHub 上的描述只有两行：

> openpilot is an operating system for robotics. Currently, it upgrades the driver assistance system in 300+ supported cars.

第一行讲野心——定位成"机器人操作系统"，设计目标承载比驾驶辅助更复杂的东西。第二行讲现状——当前在 300 多款量产车上升级原厂 ADAS（[docs/CARS.md](https://github.com/commaai/openpilot/blob/master/docs/CARS.md) 表头给出的精确数字是 335）。

再看 [docs/SAFETY.md](https://github.com/commaai/openpilot/blob/master/docs/SAFETY.md) 的开头：

> openpilot is an Adaptive Cruise Control (ACC) and Automated Lane Centering (ALC) system. Like other ACC and ALC systems, openpilot is a failsafe passive system and it requires the driver to be alert and to pay attention at all times.

关键词：`Adaptive Cruise Control`（自适应巡航）、`Automated Lane Centering`（车道居中）、`failsafe passive`（失效安全 + 被动系统）、`requires the driver to be alert`。这明确了它的能力边界：自动跟车 + 车道居中，SAE 分级里的 L2。README 末尾也明说 "THIS IS ALPHA QUALITY SOFTWARE FOR RESEARCH PURPOSES ONLY. THIS IS NOT A PRODUCT."

把它当 L4 用或当 L4 来评估，是绝大部分关于 openpilot 的误读来源。

## 2. 核心数据与硬件基线

下表所有数字均来自 GitHub 仓库 API 和 2026-10-01 当下的仓库状态。

| 维度 | 数值 / 说明 |
|------|------|
| 仓库 | [commaai/openpilot](https://github.com/commaai/openpilot) |
| Stars / Forks / Watchers | 63,786 / 11,402 / 1,322（截至 2026-10-01） |
| 主语言 | Python（panda 固件与少量内核相关代码为 C） |
| 许可证 | MIT（安全相关部分有额外约束，详见 [docs/SAFETY.md](https://github.com/commaai/openpilot/blob/master/docs/SAFETY.md)） |
| 最新 Release | `v0.11.1`，tag 发布于 2026-06-05；[RELEASES.md](https://github.com/commaai/openpilot/blob/master/RELEASES.md) 已记录 `0.11.2`（2026-08-12） |
| 仓库体积 | 约 5.0 GB（git 历史含大文件对象） |
| 支持车型 | 335 款（来自 [docs/CARS.md](https://github.com/commaai/openpilot/blob/master/docs/CARS.md) 表头） |
| 硬件 | comma four（代号 `mici`）、comma 3X（代号 `tizi`），新一代设备 chestnut 已开售，外加对应 car harness |
| 软分支 | `release-mici`（comma four）、`release-tizi`（comma 3X）、`release-chestnut`（chestnut），各自带 `-staging`；开发分支 `nightly`、`nightly-dev` |
| 安装命令 | `bash <(curl -fsSL openpilot.comma.ai)` |

数据来源：GitHub REST API `repos/commaai/openpilot`、仓库根目录 `README.md`、`RELEASES.md`、`docs/CARS.md` 顶部 "335 Supported Cars"，访问于 2026-10-01。

`openpilot` 在 GitHub 仓库 `tags` 字段里写的是 `advanced-driver-assistance-systems`、`driver-assistance-systems`、`robotics` 三项——第一个就是它在 L2 ADAS 这条赛道上的标准定位。

0.11.2 值得单独一提：驾驶模型换成 880M 参数的 big model，支持在外接 GPU 上运行，并新增了 comma connect 侧的摄像头直播、行车剪辑与 comma body 远程控制。这是模型与云端能力的一次明显跨步。

## 3. 系统地图：消息总线 + 多进程协作

openpilot 的代码组织是教科书级别的"多进程消息驱动"。[openpilot/](https://github.com/commaai/openpilot/tree/master/openpilot) 目录下大致分四个一级目录：

```text
openpilot/
├── cereal/          # 消息总线 + capnp schema（共享内存 pub/sub）
├── common/          # 通用工具：参数、实时调度、日志、GPS、硬件抽象
├── selfdrive/       # 驾驶主循环：selfdrived / controlsd / modeld / locationd / card / pandad / monitoring
└── system/          # 系统服务：camerad / sensord / loggerd / manager / athena / updated / webrtc …
```

进程之间不直接互相 import，而是通过 `cereal` 提供的 `PubMaster` / `SubMaster` 订阅发布消息。核心进程按数据流方向排开：

| 进程 | 角色 | 关键输入 | 关键输出 | 频率 |
|------|------|----------|----------|---------------|
| `camerad` | 摄像头采集，输出 YUV（亮度色度视频帧格式）帧 | 摄像头硬件 | `narrowRoadCameraState` / `wideRoadCameraState` / `cabinCameraState` | 20 Hz |
| `sensord` | IMU 采样 | 陀螺仪、加速度计 | `gyroscope` / `accelerometer`（各 104 Hz） | 104 Hz |
| `modeld` | 跑驾驶模型，输出轨迹与视觉里程计 | `narrowRoadCameraState`（+ 历史帧） | `modelV2`（规划点、`cameraOdometry`） | 20 Hz |
| `locationd` | 卡尔曼滤波融合 IMU 与视觉里程计 | `accelerometer` / `gyroscope` / `cameraOdometry` | `deviceMotion`（位姿、速度、加速度） | 20 Hz |
| `calibrationd` / `paramsd` / `torqued` / `lagd` | 安装外参、车辆参数、扭矩参数、横向延迟 | `deviceMotion` / `carState` | `extrinsicsCalibration` / `vehicleParameters` / `lateralTorqueParameters` / `lateralDelay` | 4–20 Hz |
| `radard` | 视觉雷达（外部雷达被禁后用视觉补位） | `modelV2` | `radarState` | 20 Hz |
| `card` | 车型指纹识别 + 与 opendbc（CAN 报文编解码库）交互 | CAN 帧（`can`） | `carState`、`carParams` | 100 Hz |
| `plannerd` | 纵向规划与驾驶辅助状态 | `modelV2`、`radarState`、`carState` | `longitudinalPlan`、`driverAssistance` | 20 Hz |
| `controlsd` | 横向 + 纵向控制器 | `modelV2`、`longitudinalPlan`、`deviceMotion`、`carState` | `carControl`（扭矩 / 角度 / 加速度） | 100 Hz |
| `selfdrived` | 状态机 + 告警 + 驾驶员监控仲裁 | 所有上述消息 | `selfdriveState`、`onroadEvents` | 100 Hz |
| `pandad` | 跟硬件 panda 通信，转换 `sendcan` ↔ `can` | `carControl` | CAN 帧 | 100 Hz |
| `manager` | 进程监督、启停 | 进程心跳 | 启停信号 | 持续 |

频率依据：`common/realtime.py` 定义 `DT_CTRL = 0.01`（controlsd 100 Hz）、`DT_MDL = 0.05`（modeld 20 Hz）；各服务的注册频率在 `cereal/services.py`。上面这张表回答"东西怎么分"，下面这张图给出最关键的主链路（modeld → controlsd → card → pandad → 车）：

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

`selfdrived` 没有出现在主链路里，但它订阅了 `carControl` 的所有上游，用来决定整套系统是否处于"enabled / overriding / 报警"状态。

## 4. 子系统边界

openpilot 里有四套机制容易互相串线：模型推理、视觉定位、控制器、安全仲裁。下文把它们各自的边界画清楚。

### 4.1 modeld：端到端驾驶模型

`openpilot/selfdrive/modeld/` 下的核心是 `modeld.py`，仓库内置权重是 `models/driving_supercombo.onnx`。模型在 tinygrad 框架上推理，输出三类信息：

- **规划点**（`plan`）：未来若干秒的位移、速度、加速度序列。
- **行为意图**（`meta.desire`）：车道保持 / 变道 / 转向灯等离散信号。
- **视觉侧输出**（`leaderProb`、`laneLineProb` 与视觉里程计 `cameraOdometry`）：供 `radard`、`locationd` 二次消费。

`modeld.py` 的 `get_action_from_model` 把"动作"和"规划"分了两条路径：

- 当 `model_output` 有 `action` 键时（Experimental 模式的端到端输出），直接取 `action[0,1]` 当加速度，用 `action[0,0]` 除以车速平方得到曲率。
- 否则按 `plan` 算 `desired_accel` 和 `desired_curvature`。

大模型是 0.11.2 的新变量：880M 参数的 big model 由单独的加载线程启动，与 chestnut 的外接 GPU 配套，60 秒内加载失败会自动回退到小模型（`modeld.py` 里 `BIG_MODEL_TIMEOUT = 60` 与 `load_big` 线程）。

RELEASES 显示 0.10.0 之后 Experimental 模式从"MPC（Model Predictive Control，模型预测控制）做纵向 + 学习策略做横摆"切到了"World Model 端到端规划"（[RELEASES.md 0.10.0](https://github.com/commaai/openpilot/blob/master/RELEASES.md)）。这条切换是模型层最大的变化，但闭环控制仍由 controlsd 兜底：长距规划由模型给，执行由控制器做。

### 4.2 locationd：IMU 与视觉里程计的融合

`openpilot/selfdrive/locationd/locationd.py` 是一个卡尔曼滤波器（Kalman Filter，递归状态估计算法），旧版本里它直接输出 `livePose` 等一组 `live*` 服务；现在的链路拆成了两层：

- `locationd` 订阅 `accelerometer` / `gyroscope`（sensord 出）和 `cameraOdometry`（modeld 出的视觉里程计），用 `PoseKalman` 融合后发布 `deviceMotion`：车体坐标系下的姿态、速度、角速度、加速度，外加 `inputsOK` / `posenetOK` / `sensorsOK` 三个有效性标志。
- 参数估计拆给了四个兄弟进程：`calibrationd` 发布 `extrinsicsCalibration`（摄像头安装角）、`paramsd` 发布 `vehicleParameters`（`stiffnessFactor`、`steerRatio`）、`torqued` 发布 `lateralTorqueParameters`（给 `LatControlTorque` 用）、`lagd` 发布 `lateralDelay`（横向执行延迟）。

RELEASES 0.9.8 写过一句关键的话："Localizer rewritten to remove GPS dependency at runtime"。openpilot 的行驶定位不依赖 GPS，地下车库也能跑——这对很多人来说反直觉，因为通常认为自动驾驶需要 GPS。

`locationd` 里有一组显式的 sanity check 常量，比如 `ACCEL_SANITY_CHECK = 100.0 m/s^2`、`ROTATION_SANITY_CHECK = 10.0 rad/s`、`TRANS_SANITY_CHECK = 200.0 m/s`。任何超过这个量级的输入会被视为传感器故障直接丢弃，不会污染滤波器。

### 4.3 controlsd：横纵向控制器

`openpilot/selfdrive/controls/controlsd.py` 是 L2 系统的"动力总成"。它读取的频道列表本身就是它的输入合同：

```python
self.sm = messaging.SubMaster(['lateralDelay', 'vehicleParameters', 'lateralTorqueParameters', 'modelV2', 'selfdriveState',
                               'extrinsicsCalibration', 'deviceMotion', 'longitudinalPlan', 'lateralManeuverPlan', 'carState', 'carOutput',
                               'driverMonitoringState', 'onroadEvents', 'driverAssistance'], poll='selfdriveState')
```

横向控制器（`LaC`）有四种实现，按车型参数切换：

- `LatControlAngle`：车型支持转角控制时直接发方向盘转角信号。
- `LatControlCurvature`：发曲率信号。
- `LatControlPID`：用 PID（比例-积分-微分控制器）算法。
- `LatControlTorque`：用扭矩信号，参数由 `lateralTorqueParameters` 在线更新。

纵向控制器（`LoC`）负责跟车、加减速、停车起步，它读 `longitudinalPlan.aTarget` 和 `shouldStop`——这两个字段由 `plannerd` 发布。

`controlsd` 在发布 `carControl` 前还会做一件事：遍历 `ACTUATOR_FIELDS`，对每个执行器字段做 `math.isfinite` 检查，任何 NaN/Inf 都会被强制清零。这是 L2 系统的隐性安全网之一。

### 4.4 selfdrived：状态机与告警

`openpilot/selfdrive/selfdrived/selfdrived.py`（600 行上下）做三件事：

1. **状态机**：`StateMachine`（`selfdrived/state.py`）把系统在 `disabled` / `preEnabled` / `enabled` / `overriding` / `softDisabling` 五个状态间迁移——`overriding` 是司机手扶方向盘施加力矩时的临时接管，`softDisabling` 是平滑退出，超时后落回 `disabled`。
2. **事件归并**：`Events` 类把来自 `carOutput`、`driverMonitoringState`、`pandaStates`、`onroadEvents` 等的事件统一归并，再决定 `NO_ENTRY`（不允许进入）/ `WARNING` / `USER_DISABLE`。
3. **告警文本**：`AlertManager`（`alertmanager.py`）把事件翻译成人能看的字（`alertText1`、`alertText2`）和声音（`alertSound`）。

`selfdrived` 还会做一件很关键的事：在 `self.enabled` 的前提下，如果 `pandaStates` 报告的 `controlsAllowed` 与自身状态不一致，`mismatch_counter` 自增（允许两个采样周期的容差）；超过阈值就强制 disengage。这是 panda 与 selfdrived 之间的"投票不一致"检测。

### 4.5 card + opendbc：车型接口层

`openpilot/selfdrive/car/card.py` 是车型接口层的入口。它通过 `opendbc.car.interfaces` 拿到 `CarInterfaceBase`，再调用 `opendbc.car.car_helpers.get_car` 根据 CAN 帧里的固件版本号做"车型指纹"识别（car fingerprinting）：

```python
self.CI = interfaces[self.CP.carFingerprint](self.CP)
```

这一步是 openpilot 能支持 335 款车的原因：每款车有独立的 finger-print 规则、独立的安全模型、独立的消息解码（DBC 文件是 CAN 报文与信号的对照表）。`opendbc` 是个独立子模块（仓库里以 git submodule 形式引入），`opendbc/safety/` 下的代码是用 C 写的车型安全策略。README 的 Safety and Testing 一节说得直白："The code enforcing the safety model lives in panda and is written in C"。

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

这条约束的"硬"在于：即使 openpilot 上层进程崩溃，panda 也会在心跳超时后自动切断输出。这就是 [docs/SAFETY.md](https://github.com/commaai/openpilot/blob/master/docs/SAFETY.md) 与 README 反复把 panda 当成安全模型执行者的原因。

### 4.7 monitoring：驾驶员监控

驾驶员监控分两段进程：`modeld/dmonitoringmodeld.py` 跑 `dmonitoring_model.onnx`，从舱内相机（cabin camera）估出驾驶员头部姿态、视线方向、是否在打电话 / 抽烟，发布 `driverStateV2`；`monitoring/dmonitoringd.py` 按 `policy.py` 的规则把它折算成 `driverMonitoringState`。`selfdrived` 拿到 `driverMonitoringState.alwaysOnLockout` 后会触发 `EventName.tooDistracted`，把系统挡在 `NO_ENTRY` 状态，直到下次点火循环。

openpilot 里的驾驶员监控是"必须开着"的，任何 fork 都不能禁用或削弱它，否则按 [docs/SAFETY.md](https://github.com/commaai/openpilot/blob/master/docs/SAFETY.md) "Failure to comply with these standards will get you and your users banned from comma.ai servers."

## 5. cereal：所有进程用同一种语言说话

`openpilot/cereal/` 是整个项目的"语言"。它用 [Cap'n Proto](https://capnproto.org/)（一种高性能二进制序列化协议，类似 Protocol Buffers）做序列化，底层走 [msgq](https://github.com/commaai/msgq) 共享内存 pub/sub。Schema 在 `log.capnp` 里，主结构是 `Event`，有一个 `logMonoTime`（单调时间戳，避免系统时间跳变影响因果关系）和一个 `valid` 标志位。

`cereal` 的 README 给的规矩很具体：

1. 所有字段必须使用 SI 国际单位制（米、秒、弧度等），除非字段名已经标了其他单位（比如 `steeringAngleDeg`）。这样跨进程共享时不用做单位换算。
2. 字段名在所在消息的上下文里必须无歧义，取值要易于绘制和人工读取。
3. 修改 schema 时优先"加字段 / 加结构体"，避免重命名和改类型，保证旧 log 仍能被新代码读出来。

`cereal/services.py` 把每个服务的频率和队列大小注册成枚举：

```python
class QueueSize(IntEnum):
  BIG   = 10 * 1024 * 1024   # 视频帧、大模型输出
  MEDIUM = 2 * 1024 * 1024   # 高频 CAN、直播
  SMALL = 250 * 1024         # 多数服务
```

`can` 服务跑 100 Hz、占 `BIG` 队列；`selfdriveState` 跑 100 Hz、占 `SMALL`。队列大小按"消费者最坏能承受多长的突发延迟"反推。0.11.x 期间这个注册表还在生长：`chestnutState`、`chestnutGpuState`、`cabinCameraState` 都是新面孔。

`cereal` 还有一个值得单独说的设计：`custom.capnp` 留了 `CustomReserved0` 到 `CustomReserved19` 一组保留结构体，主线 openpilot 承诺这些结构体保持为空。fork 加新事件时只改这些保留位（改结构体名可以，改 `@0x…` 标识符不行），就能保证"fork 的 log 永远能被主线代码读出来"——一个给长期演进用的兼容性保险。

## 6. 一次跟车任务如何流过系统

下面用"前车减速、openpilot 跟着减速、最后停稳"这条最日常的纵向任务，把上面这些进程串起来。时间线是示意性的，数字为说明量级而设：

```text
时刻 t=0.00s
  车辆以 80 km/h 跟车，模型与控制器进入稳态。

时刻 t=0.00s （100 Hz 控制循环开始）
  pandad            收到车上 100 Hz CAN 帧，发布到 cereal 'can' 频道。
  card              订阅 'can'，解出 vEgo=80km/h、steerAngle、brakePressed 等，
                    发布到 'carState'。
  modeld            订阅 'narrowRoadCameraState'（camerad 出），把过去若干帧叠起来送进
                    driving_supercombo.onnx，得到新的 plan / desire / leaderProb，
                    发布到 'modelV2' 与 'cameraOdometry'。
  radard            订阅 'modelV2'，根据 leaderProb + 模型给出的车距生成 'radarState'。
  plannerd          订阅 'modelV2' + 'radarState' + 'carState'，规划纵向轨迹，
                    发布 'longitudinalPlan'。
  locationd         融合 IMU 与 'cameraOdometry'，发布 'deviceMotion'。
  controlsd         订阅 'modelV2' + 'longitudinalPlan' + 'carState' + 'deviceMotion' +
                    'vehicleParameters'，调用 LaC / LoC，发布 'carControl'。
  selfdrived        订阅全部上游 + 'driverMonitoringState'，决定 'selfdriveState.enabled'
                    是否仍为 True。

时刻 t=0.05s
  pandad            把 'carControl' 里 LoC 给出的减速请求编码成 CAN 帧，写到 sendcan。
  panda 固件        校验：加速度在安全限值内、未踩刹车、未 cancel → 转发给车。

时刻 t=2.00s
  前车完全停下。
  card 报告 vEgo=0、standstill=True。
  modeld plan 输出 'shouldStop=True'，曲率清零。
  controlsd 把 LoC 状态切到 'stopping'，用小负加速度维持刹车压力。
  selfdrived 保持 enabled，不产生告警。

时刻 t=2.50s
  全部进程进入稳态：vEgo=0、shouldStop=True、carControl.enabled=True。
  pandad 只在 'carControl' 有新命令时写 CAN 帧，同时继续接收车上的停稳心跳。
  驾驶员可随时通过踩刹车或按 cancel 拿回控制权。
```

这条链路也是横向（车道居中）的翻版：模型给 `desiredCurvature`，`controlsd` 用对应的 `LatControl*` 把曲率变成转角 / 扭矩，pandad 写 CAN，横向安全约束由 panda 固件强制。

## 7. 安全模型：panda 才是"硬刹车"那一道

`docs/SAFETY.md` 把安全归结为两条：

1. 司机必须能通过踩刹车或按 cancel 立刻拿回控制权。
2. 系统给出的执行器命令必须落在合理范围内（[SAFETY.md 提到 ISO 11270 与 ISO 15622，横向最大 0.9 秒达到 1m 横向偏差](https://github.com/commaai/openpilot/blob/master/docs/SAFETY.md)）。

这两条规则的执行者不是 Python，是 C。panda 固件是 [commaai/panda](https://github.com/commaai/panda) 仓库里的代码，遵循 MISRA C:2012 风格的编码约束，专门管三件事：

- 给执行器发命令时硬限速（steer torque 上限、accel 上限）。
- 任何违反限速的输入直接丢弃。
- 心跳超时自动归零。

openpilot 上层对安全的处理方式是"信任 panda + 用 selfdrived 兜底"：

- selfdrived 不会主动做硬刹，但会在 `NO_ENTRY` 状态下阻止系统进入 enabled。
- 一旦 `selfdrived/helpers.py` 的 `ExcessiveActuationCheck` 判定执行量超阈——纵向超过 `ACCEL_MAX`/`ACCEL_MIN` 的两倍，或横向侧向加速度超过 ISO 限值的两倍并持续约 0.25 秒——会设置 `Offroad_ExcessiveActuation` 参数，下次启动直接报警。

[SAFETY.md](https://github.com/commaai/openpilot/blob/master/docs/SAFETY.md) 末尾给 fork 划了红线：

1. 不能禁用或削弱驾驶员监控。
2. 不能禁用或削弱 excessive actuation 检查。
3. 如果改了 `opendbc/safety/` 下的代码：fork 不能再使用 openpilot 商标，且必须保留完整 safety test suite 并保证所有测试通过（包括 fork 自身改动要求的新覆盖）。

`comma.ai` 的原话是 "Failure to comply with these standards will get you and your users banned from comma.ai servers."，并且官方明确"强烈不鼓励"使用安全代码缺失或不达标的 fork。这意味着你 fork 自用可以，但改安全代码会同时失去商标与 comma 服务器（含 comma connect 数据同步）的准入。

## 8. benchmark 段：测的是什么，不能推出什么

openpilot 没有像 nuScenes（自动驾驶公开数据集）或 Waymo 开放数据集那样的传统学术 benchmark。它的"成绩"由两套指标构成，混在一起读会误读。

### 8.1 release 里的模型能力指标

RELEASES.md 0.10.0 写过：

> New training architecture: ... Longitudinal MPC replaced by E2E planning from World Model in Experimental Mode. Action from lateral MPC as training objective replaced by E2E planning from World Model.

这一条对应的"性能"是模型层面的：

- 训练时把"横向 MPC 的动作"作为监督信号换成"World Model 的端到端规划"。
- 实验模式（Experimental Mode）下纵向也用 World Model 输出。

**它测的是什么**：comma 用自家数据训练、在自家 replay 与仿真体系里验证的模型迭代（0.11.0 还提到模型 "Fully trained using a learned simulator"）。这些数字的评估环境是 comma 内部的，没有公开的逐项指标。

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
- 不能推出"低功耗意味着低发热"，`RELEASES.md 0.11.1` 同时改动了 thermal policy（"Improved thermal policy for comma four"），因为功耗降下来后峰值热行为变了。

把两类数字放在一起看，结论是：openpilot 的 release notes 是在告诉你"comma 自己的硬件 + 自己的数据 + 自己的 replay 系统下，这个版本相对上一个版本进步在哪"。它不是学术意义上的 benchmark，**不能直接被引申为通用能力声明**。

## 9. 数据上传、隐私与开源边界

README 末尾的两段 collapsed block 包含以下关键信息：

1. **默认会上传驾驶数据**到 comma 服务器，可以在 comma connect 看到，使用者也可以在设置里关掉。
2. **数据范围**：road-facing 摄像头、CAN、GPS、IMU、磁力计、温度传感器、crash、操作系统日志；驾驶员摄像头和麦克风只在 opt-in 时才记录。

这意味着两件事：

- 即使你跑的是开源代码、build 自家镜像，**数据上传路径仍然是 comma 控制的**。如果你 fork 后要彻底切断上传，需要自己改 `system/athena/`（comma connect 客户端）以及 `system/loggerd/`。
- 这条规则反过来也是它能用"几百辆车贡献数据"训练模型的基础：开源不等于零数据回报。

LICENSE 是 MIT，但 [SAFETY.md](https://github.com/commaai/openpilot/blob/master/docs/SAFETY.md) 末尾对 fork 加了约束。这两件事不矛盾：MIT 允许你 fork、读、改、商用；SAFETY 附加条件要求你 fork 后的安全代码不能被削弱。边界要看清楚——随便改大部分代码都行，唯独动了 `opendbc/safety/`，商标与 comma 服务器准入就同时失效。

## 10. 适用边界与采用顺序

### 10.1 推荐采用顺序

如果你是第一次接触 openpilot，按下面的顺序走最稳：

```text
1.  读 docs/SAFETY.md、docs/CARS.md 顶部、README 末尾的 ALPHA 声明。
    目的：先确定你的车型、你的法律环境、你的安全预期。
2.  在 comma.ai/shop 确认硬件：comma four 是 README 列出的在售设备。
3.  用默认 release 分支（release-mici 或 release-tizi），不要先上 nightly。
4.  装车后先不激活控车，让设备以纯记录状态跑几天：
    校准（calibrationd）需要正常行驶才能完成，告警逻辑也在这个阶段验证。
5.  启用 ACC + ALC 后，先在熟悉路段白天跑，再扩展到夜间 / 雨天 / 高速。
6.  上传数据前在设置里关掉 / 留存，看自己能不能接受。
7.  Experimental Mode 最后开。它是 opt-in 的实验模式，不要与默认模式混用。
```

### 10.2 谁该先用，谁可以等等

| 角色 | 建议 |
|------|------|
| 北美 + comma 已有硬件 + 车型在 [docs/CARS.md](https://github.com/commaai/openpilot/blob/master/docs/CARS.md) 里 | 推荐先用默认 release 分支 |
| 关注安全代码 / 想做 fork 的工程师 | 直接读 [panda](https://github.com/commaai/panda) + `opendbc/safety/`，不要只看 Python 侧 |
| 学术研究者 | 用 `tools/replay` 跑历史 log 做开环验证；开环指标不能直接外推闭环驾驶表现，更不能当通用 L4 评估基准 |
| 不在支持列表里 | 不要硬塞。可以读 `system/` 与 `selfdrive/` 的分层设计做参考，但控车路径无法复用 |
| 当地法律明确禁止改装车辆 | 不要装。openpilot 是辅助系统，但仍会修改 CAN 流量 |
| 期望 openpilot 替代 L2+ 量产车 | 不要指望。Honda Sensing / Toyota TSS / GM Super Cruise 都有车企级安全流程覆盖，openpilot 走的是开源 + 灰度路径 |

## 11. 延伸阅读

- 仓库主页：[github.com/commaai/openpilot](https://github.com/commaai/openpilot)
- 安全文档：[docs/SAFETY.md](https://github.com/commaai/openpilot/blob/master/docs/SAFETY.md)
- 车型清单：[docs/CARS.md](https://github.com/commaai/openpilot/blob/master/docs/CARS.md)
- 消息总线：[openpilot/cereal/README.md](https://github.com/commaai/openpilot/blob/master/openpilot/cereal/README.md)
- 硬件固件：[github.com/commaai/panda](https://github.com/commaai/panda)
- 车型编解码：[github.com/commaai/opendbc](https://github.com/commaai/opendbc)
- 消息队列：[github.com/commaai/msgq](https://github.com/commaai/msgq)
- 训练方法：CVPR 论文 "Learning to Drive from a World Model"（被 RELEASES 0.10.0 引用），comma 博客：[blog.comma.ai](https://blog.comma.ai/)

正文里所有数字、命令、文件路径均可在以上链接交叉验证；信息边界已标在第 8 节"benchmark 段"。本文不覆盖 comma connect 的商业化与 comma four 的硬件 BOM（Bill of Materials，物料清单）。
