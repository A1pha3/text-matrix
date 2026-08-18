---
title: "Home Assistant Core：开源智能家居控制中心的架构与理念"
date: "2026-04-27T15:00:00+08:00"
slug: "home-assistant-core-open-source-home-automation"
github_repo: "home-assistant/core"
description: "Home Assistant Core 是开源智能家居领域最活跃的项目之一，以本地优先、私有化为核心理念。本文解析其实体/状态模型、集成架构、自动化引擎与数据流设计，支持 2000+ 设备集成的架构原理。"
draft: false
categories: ["技术笔记"]
tags: ["Home Assistant", "智能家居", "Python", "本地优先"]
---

# Home Assistant Core：把 2000 种设备统一到一台本地服务器的背后

在一台机器上跑一个 Python 程序，让它替你管所有智能家居设备。能管 2000 多种设备，靠的是数据模型和集成架构，而不是代码量。

读完你会有三条具体收获：懂为什么不同品牌设备能被塞进同一套数据结构；能描述一次「人走灯灭」从传感器到灯泡关闭的完整路径；能在自动化不生效时，按层级定位是设备、集成、规则还是服务出了问题。后两条意味着你可以不靠厂商 App、自己写自动化，也为判断「值不值得自己维护这台服务器」提供了依据。

本文从两条主线展开：数据怎么统一、控制怎么发生。然后补一个完整的自动化流转案例，再看这两条主线的工程代价和适用边界。

本文的读者是：想自建智能家居、已经决定维护一台本地服务器、并愿意看代码和概念的人。读的人期望能把概念和实际排查连接起来，而不是只看功能列表。

## 2. 学习目标

读完并动手过一遍后，你应该能独立做到四件事：

1. 解释 Entity / Domain / 状态机三者如何把一个 Zigbee 灯泡和一个 Wi-Fi 灯带统一成同一种可操作对象。
2. 在手边 Home Assistant 里新建一条 `state` 触发的自动化，说出 trigger、condition、action 各自的职责。
3. 追踪一次自动化不触发的故障：能判断问题出在集成、状态变化、规则匹配还是服务调用。
4. 权衡本地优先的代价，说明哪些设备适合接入、哪些不应该接入。

你可以带着这四条目标去读，每章的末尾也用它们自检。

## 3. 系统地图

先把 Home Assistant 的核心组件和它们的关系拉出来。下图覆盖了本文要讨论的全部关键路径：

```mermaid
flowchart TB
    subgraph 设备层
        D1[Zigbee 设备]
        D2[Wi-Fi 设备]
        D3[MQTT 设备]
        D4[云 API 设备]
    end

    subgraph 集成层
        I1[ZHA / zigpy2mqtt]
        I2[本地 API 集成]
        I3[MQTT 集成]
        I4[云端轮询集成]
    end

    subgraph 核心引擎
        SM[状态机<br/>State Machine]
        EB[事件总线<br/>Event Bus]
        AE[自动化引擎<br/>Automation Engine]
        RC[记录器<br/>Recorder]
    end

    subgraph 用户层
        SVC[服务调用<br/>Service Call]
        DB[仪表板<br/>Dashboard]
        UI[Web UI 配置]
    end

    D1 --> I1 --> SM
    D2 --> I2 --> SM
    D3 --> I3 --> SM
    D4 --> I4 --> SM
    SM --> EB
    EB --> AE
    AE --> SVC
    SVC --> SM
    SM --> RC --> DB
    UI --> I1 & I2 & I3 & I4
```

下面逐层展开。

---

## 4. 实体 / 状态模型：一切皆 Entity

Home Assistant 解决多品牌统一的方式是在数据入口做归一化——每个设备接入时被映射为一个 Entity（实体），不管底层是 Zigbee、MQTT 还是云端 HTTP，在上层都变成同一种数据结构。

### 4.1 Entity 的结构

```python
# 一个灯泡实体的状态快照
{
    "entity_id": "light.living_room",
    "state": "on",
    "attributes": {
        "brightness": 255,
        "color_temp": 400,
        "friendly_name": "Living Room Light",
        "supported_color_modes": ["brightness", "color_temp"],
    },
    "last_changed": "2026-04-27T10:30:00.000000+00:00",
    "last_updated": "2026-04-27T14:22:00.000000+00:00",
    "context": {
        "id": "01JXXXXXXXXXXXXXXX",
        "user_id": None,
        "parent_id": None,
    }
}
```

每个 Entity 的字段分工：

- `entity_id`：全局唯一标识，格式 `<domain>.<name>`。domain 决定了这个实体能接受哪些服务调用
- `state`：当前状态字符串（`"on"`/`"off"`/`"playing"` 等），所有自动化条件都基于它做匹配
- `attributes`：键值对扩展字段，放亮度、色温、设备名等属性
- `last_changed` / `last_updated`：两个时间戳分别记录"状态首次变为当前值的时间"和"任意更新时间"
- `context`：用于追踪状态变化的来源（用户操作、自动化触发、还是外部事件）

### 4.2 领域（Domain）

Entity 按类型划入不同的 Domain：

| Domain | 含义 | state 示例 |
|--------|------|-----------|
| `light` | 灯光 | on / off |
| `switch` | 开关 | on / off |
| `sensor` | 传感器 | 任意数值或字符串 |
| `climate` | 温控 | heat / cool / idle |
| `cover` | 窗帘/门 | open / closed |
| `automation` | 自动化规则 | on / off |
| `scene` | 场景 | /scene.activate |

同一 Domain 的实体共享同一套服务接口——所有 light 实体都能响应 `light.turn_on`，不管底层是 Zigbee 灯泡还是 Wi-Fi 灯带。

### 4.3 状态机（State Machine）

Home Assistant 内部用全局状态机管理所有 Entity 的状态：

```python
state = hass.states.get("light.living_room")
hass.states.set("light.living_room", "off")

hass.bus.listen("state_changed", on_state_changed)
```

状态机不只是一个键值存储。每次状态写入都会触发 `state_changed` 事件推送进事件总线，自动化引擎正是通过订阅这个事件来驱动规则匹配。

---

## 5. 集成（Integration）架构

集成是连接外部设备到状态机的通道。每个集成负责与特定品牌或协议通信，把设备数据转成 Entity 写入状态机。

### 5.1 工作原理——以 MQTT 为例

```
[物理设备] --MQTT--> [MQTT Broker] --发布主题--> [HA MQTT 集成] --> [Entity/State]
```

每个集成通常包含：

- `__init__.py`：包的入口，负责 setup 和配置验证
- `config_flow.py`：前端配置流程（Web UI 上的添加向导）
- `diagnostic.py`：诊断信息收集
- `entity.py`：一个或多个实体类，继承 `Entity` 基类
- `manifest.json`：元数据（版本、依赖、作者等）

### 5.2 两种配置模式

**YAML 配置（传统方式）：**

```yaml
# configuration.yaml
light:
  - platform: hue
    bridge: 192.168.1.100
    allow_unused: true
```

**UI 配置（推荐方式）：**

通过"设置 → 设备与服务 → 添加集成"在 Web UI 中操作，不需要编辑 YAML。UI 配置的优点是：配置实时验证、错误当场提示、可以在不重启 HA 的情况下加载或卸载集成。需要 OAuth 认证的集成也只能走这条路。

### 5.3 设备（Device）与实体（Entity）

Home Assistant 0.107 引入了 Device 概念，让同一物理设备的多个实体在 UI 中分组显示：

```
Device: "Philips Hue Bridge"
  - Entity: light.living_room
  - Entity: light.bedroom
  - Entity: sensor.living_room_temperature
```

Device 只影响前端展示和区域归类，不影响核心数据模型——状态机里仍然是平铺的 Entity。

---

## 6. 事件总线（Event Bus）

Home Assistant 内部组件通过事件总线做发布-订阅通信：

```python
hass.bus.listen("state_changed", on_state_changed)
hass.bus.listen("call_service", on_service_call)
hass.bus.fire("my_custom_event", {"key": "value"})
```

事件总线解耦了组件之间的依赖——集成只负责把设备数据写进状态机，不需要知道谁在消费这些数据。自动化引擎只订阅事件，不需要知道事件从哪个集成来。

---

## 7. 自动化引擎

自动化是 Home Assistant 的核心能力之一。用户定义规则：当某个条件满足时，自动执行一组动作。

### 7.1 三要素结构

```yaml
automation:
  - alias: "人来灯亮"
    trigger:
      - platform: state
        entity_id: binary_sensor.motion_garage
        to: "on"
    condition:
      - condition: time
        after: "06:00:00"
        before: "23:00:00"
    action:
      - service: light.turn_on
        target:
          entity_id: light.living_room
        data:
          brightness: 255
```

- **Trigger（触发器）**：什么事件启动自动化（状态变化、定时、Webhook 等）
- **Condition（条件）**：附加前置约束（时间段、设备状态、用户是否在家等）
- **Action（动作）**：触发后执行的操作（开灯、发送通知、调用服务等）

### 7.2 触发器类型

| 触发器 | 说明 |
|--------|------|
| `state` | 实体状态变化 |
| `numeric_state` | 传感器数值超过/低于阈值 |
| `time` | 指定时间触发 |
| `time_pattern` | 定时重复（如每 5 分钟） |
| `event` | 任意事件（来自总线或外部） |
| `homeassistant` | HA 启动/关闭事件 |
| `mqtt` | MQTT 主题收到消息 |
| `webhook` | HTTP Webhook 触发 |
| `geo_location` | GPS 位置进入/离开某区域 |
| `zone` | 用户进入/离开地理围栏 |

### 7.3 脚本（Script）与场景（Scene）

脚本是可重用的动作序列，自动化可以直接引用而不是写重复的 action 块：

```yaml
script:
  goodbye:
    sequence:
      - service: light.turn_off
        target:
          entity_id: light.all
      - service: climate.set_temperature
        data:
          temperature: 20
```

场景是一组实体的目标状态快照，用于一键切换：

```yaml
scene:
  - name: 观影模式
    entities:
      light.living_room:
        state: on
        brightness: 80
      light.bedroom:
        state: off
```

---

## 8. 服务（Service）机制

服务是对实体执行操作的方式。每个 Domain 暴露一组服务。

### 8.1 服务调用

```yaml
action:
  - service: light.turn_on
    data:
      brightness: 255
      color_name: red
    target:
      entity_id: light.living_room
```

```python
hass.services.call(
    domain="light",
    service="turn_on",
    {"entity_id": "light.living_room", "brightness": 255}
)
```

服务调用是"即发即忘"（fire-and-forget）语义。如果目标实体不存在，调用静默失败——这样调用方不需要预先检查实体是否已就绪。

---

## 9. 一次完整自动化：追踪「人走灯灭」

用一个具体例子把前面各节串起来——看一次"检测到无人移动后自动关灯"的完整链路。

**场景**：走廊上装有 Zigbee 人体传感器和 Zigbee 灯泡，通过 ZHA 集成接入 Home Assistant。自动化规则：传感器状态变为 `off` 后，延迟 60 秒关灯。

**步骤分解：**

1. **传感器上报**：Zigbee 人体传感器检测到无人，通过 Zigbee 网络将消息发到 ZHA 协调器。
2. **集成转换**：ZHA 集成收到消息，将 `binary_sensor.corridor_motion` 的 state 从 `"on"` 更新为 `"off"`，写入状态机。
3. **事件发布**：状态机检测到 state 变化，向事件总线推送 `state_changed` 事件，负载中包含旧状态、新状态、entity_id 和时间戳。
4. **自动化匹配**：自动化引擎订阅了 `state_changed`。它拿到事件后遍历所有已启用的自动化规则，找到 `trigger` 匹配 `binary_sensor.corridor_motion` 且 `to: "off"` 的那条。
5. **条件评估**：检查 condition 块——比如当前时间是否在 `06:00-23:00` 范围内。不满足则跳过。
6. **延迟等待**：如果配置了 `for: 00:01:00`（60 秒内状态没变回来），自动化引擎启动内部计时器。如果传感器在 60 秒内又变为 `"on"`，计时器取消。
7. **动作执行**：计时器到期，自动化引擎调用 `light.turn_off` 服务，目标 `light.corridor`。
8. **状态回写**：ZHA 集成收到服务调用，通过 Zigbee 网络向灯泡发送关灯指令。灯泡确认关闭后，集成将 `light.corridor` 的 state 更新为 `"off"`，又触发一次 `state_changed` 事件。
9. **历史记录**：记录器（Recorder）将两次状态变化写入 SQLite 数据库，后续可在仪表板上查看历史曲线。

这个链路穿过了本文讨论的全部组件：集成、状态机、事件总线、自动化引擎、服务调用、记录器。调试自动化时，可以从这个链路逐层排查——是集成没收到数据、状态没变化、自动化没匹配、还是服务调用没执行。

---

## 10. 长期数据存储

Home Assistant 内置记录器（Recorder），将状态变化历史写入本地数据库：

```yaml
recorder:
  db_url: mysql://user:pass@localhost/hass?charset=utf8mb4
  purge_keep_days: 30
  commit_interval: 5
```

默认用 SQLite，也支持 PostgreSQL 和 MariaDB。长期数据有两个实际用途：在历史面板查看设备状态曲线；在自动化中用 `numeric_state` 触发器基于历史趋势做判断（比如"温度连续上升超过 10 分钟"）。

---

## 11. 本地优先的代价

Home Assistant 的首要设计原则是本地运行、数据不上云。互联网断了本地设备照常工作、自动化不需要等云端延迟、数据完全由你控制。

但本地优先也有代价，选型前需要掂量：

- **设备兼容边界**：只支持有本地 API 或开放协议的设备。很多廉价 Wi-Fi 设备只提供厂商云 API，HA 需要通过云端集成轮询，但这破坏了本地优先的前提——厂商停服则设备不可用。
- **维护成本**：自己管服务器意味着自己负责升级、备份、SSL 证书、外网访问（Nabu Casa 付费订阅可以简化这些）。米家用户只管插电，HA 用户需要维护一台运行 Linux 的机器。
- **集成质量不齐**：2000+ 集成由社区维护，有些只是"能用"而不是"好用"。厂商改动 API 后，对应集成可能滞后数周到数月。

---

## 12. 常见问题与排查

读者带着任务来，实际动手时卡住是常态。这里列最常见的四种，按"从上游往依赖走"的顺序排查更省时间。

**为什么实体一直 unavailable？**

实体 unavailable 通常意味着集成收不到这个设备的数据，而不是设备本身坏了。先看"设置 → 设备与服务"里对应集成的诊断信息：设备离线、信号弱（Zigbee 常表现为丢包）、固件不兼容都会让实体进入 unavailable。把底层的通信层（ZHA / MQTT / 厂商桥接）先修好，实体自然恢复。

**自动化状态是 on，但到点不触发？**

先分清是"没触发"还是"触发了没执行动作"。在"开发者工具 → 事件"里监听 `automation_triggered` 事件：如果该事件没有出现，问题在 trigger 或 condition；如果出现了但没看到动作，问题在 action 或服务调用。常见的坑是 condition 里的时间段没覆盖到实际触发时刻。

**服务调用报了找不到实体？**

服务调用是"即发即忘"的，目标实体不存在会静默失败。要在配置里写成

```yaml
action:
  - service: light.turn_on
    target:
      entity_id: light.living_room
```

并先用开发者工具手动调一次 `light.turn_on`，确认 `light.living_room` 这个 id 真实存在且可控制。图标上点实体，能看到的 id 才是有用的 id。

**重启之后自动化没生效？**

自动化默认在启动时加载。改了 YAML 需要在"开发者工具 → YAML"里重新加载自动化，或直接重启 HA。"系统 → 日志"里如果有语法错误，会自动拒载并标红，检查那里的报错通常能直接定位。

---

## 参考资源

- [Home Assistant 官方文档](https://www.home-assistant.io/docs/)
- [Home Assistant 开发者文档](https://developers.home-assistant.io/)
- [集成列表](https://www.home-assistant.io/integrations/)
- [社区论坛](https://community.home-assistant.io/)
- 仓库：[github.com/home-assistant/core](https://github.com/home-assistant/core)（Apache-2.0）