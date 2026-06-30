---
title: "TeslaMate：自托管 Tesla 车辆数据记录器，把爱车的每一次出行变成可分析的数据"
date: "2026-06-15T21:02:07+08:00"
slug: "teslamate-self-hosted-tesla-data-logger-guide"
description: "TeslaMate 是一款基于 Elixir + Postgres + Grafana + MQTT 的自托管 Tesla 数据记录器，8148+ Stars。它能高精记录行车与充电数据，零额外耗电（vampire drain），并通过 MQTT 接入 Home Assistant。本文覆盖架构、关键特性、docker-compose 部署路径与适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["Tesla", "Elixir", "自托管", "Grafana", "MQTT"]
---

# TeslaMate：自托管 Tesla 车辆数据记录器

## 学习目标

通过本文，你将能够：

- 理解 TeslaMate 的项目定位：自托管 Tesla 车辆数据记录器，不是"另一款 Tesla App"
- 读懂 TeslaMate 的架构：TeslaMate (Elixir) + PostgreSQL + Grafana + Mosquitto
- 理解 vampire drain 的设计取舍：车一进入睡眠就停止轮询
- 知道 TeslaMate 的关键能力：高精度行驶数据记录、约 20 张预置 Grafana 仪表盘、MQTT 集成
- 能够评估 TeslaMate 是否适合你的使用场景

## 目录

1. [项目定位](#一项目定位)
2. [为什么要自托管 Tesla 数据](#二为什么要自托管-tesla-数据)
3. [架构总览](#三架构总览)
4. [关键能力清单](#四关键能力清单)
5. [部署路径](#五部署路径)
6. [典型使用场景](#六典型使用场景)
7. [适用边界与不适用人群](#七适用边界与不适用人群)
8. [与其他 Tesla 数据方案对比](#八与其他-tesla-数据方案对比)
9. [开始之前](#九开始之前)
10. [自测题](#自测题)
11. [练习](#练习)
12. [进阶路径](#进阶路径)
13. [资料口径说明](#资料口径说明)

---

## 一、项目定位

TeslaMate 是一款自托管（self-hosted）的 Tesla 车辆数据记录器，把官方 API 没有持续提供的细粒度数据——每一次充电、每一度消耗、每一次行驶——持续落盘到本地 Postgres，再用 Grafana 仪表盘可视化，最后通过本地 MQTT Broker 把车况广播给 Home Assistant / Node-RED / Telegram 等自动化系统。

| 维度 | 数据 |
|------|------|
| 仓库 | [teslamate-org/teslamate](https://github.com/teslamate-org/teslamate) |
| Stars | 8,148+ ⭐ |
| Forks | 943+ |
| 主语言 | Elixir |
| 数据库 | PostgreSQL（TimescaleDB 扩展） |
| 可视化 | Grafana |
| 消息总线 | Mosquitto MQTT |
| 许可证 | AGPL-3.0 |
| 维护者 | JakobLichterfeld 等 |
| 最近更新 | 持续维护，最近一次提交在 2026-06 |

值得先点出来的两个判断：

1. **它不是"另一款 Tesla App"**——它跑在你自己的机器上（树莓派、NixOS、Synology、Unraid、Mac mini 都行），所有数据本地存储，不依赖任何第三方云服务，也不收取订阅费。
2. **它的核心约束不是"记录数据"，而是"不打扰车"**——Tesla 官方 API 一旦被频繁唤醒会显著增加所谓的 vampire drain（驻车耗电），TeslaMate 的设计目标是把车辆尽可能快地放回睡眠状态，同时记录足够细的数据。

## 二、为什么要自托管 Tesla 数据

Tesla 官方 App 提供的功能集中在"控车"（开锁、空调、定位），并不提供：

- **高精度的行驶数据**：每一段行程的里程、能耗、车速、海拔、起止点
- **完整的充电记录**：充电桩类型、起始/结束 SOC（State of Charge，电量百分比）、充电功率曲线、费用核算
- **电池健康度趋势**：长期 SOC 曲线、放电深度、估算的电池容量衰减
- **历史轨迹回放**：终身行驶地图、地址解析、地理围栏触发记录
- **驻车耗电（vampire drain）分析**：什么时候车在耗电、耗了多少、是不是某个新安装的 app 引起的

TeslaMate 把这些"官方不给你看"的数据，全部按 1Hz 级别的精度记录下来，并提供约 20 张预置 Grafana 仪表盘做切片分析。

> ⚠️ **安全提醒**：项目方在 README 顶部明确警告，社区里出现过伪装成 TeslaMate 的恶意分支与第三方 App Store 应用。务必只从官方仓库 `teslamate-org/teslamate` 和官方文档 `docs.teslamate.org` 获取。

## 三、架构总览

TeslaMate 的设计哲学是"小而专的多个容器 + 单一事实源数据库"。整套系统由四个核心组件构成：

| 组件 | 角色 | 实现 |
|------|------|------|
| TeslaMate 主程序 | 数据采集 / 持久化 / Web UI | Elixir（Phoenix + LiveView） |
| PostgreSQL | 唯一事实源；车辆事件、行程、充电、地址 | Postgres + TimescaleDB（时序扩展） |
| Grafana | 数据可视化，提供约 20 张预置仪表盘 | Grafana OSS |
| Mosquitto | MQTT Broker，对外广播车况 | Eclipse Mosquitto |

数据流是这样的：

```
Tesla Cloud API
    │
    │  (OAuth Token, REST/Streaming)
    ▼
TeslaMate (Elixir) ──► PostgreSQL (持久化)
    │              ╲
    │               ╲► Grafana (可视化)
    │
    └──► Mosquitto (MQTT, topic: teslamate/...)
              │
              ▼
       Home Assistant / Node-RED / 自定义订阅者
```

### 3.1 关于 vampire drain 的设计取舍

TeslaMate 不会持续 polling（轮询）Tesla API。它采用流式订阅（streaming）模式，只在车辆主动 wake（被唤醒）时才向云端拉数据，一旦车辆进入 sleep 状态就立刻断开连接。这种"被动式采集"是它和早期社区项目（如 tesla-apiscraper）的关键差异——后者往往配置不当就会让车一夜掉 5% 电。

代价是：它不主动"召唤"你想要的任何数据。所有的"现在 SOC 是多少"查询都要么走缓存，要么走 Home Assistant 主动唤醒路径。

### 3.2 MQTT 集成的边界

所有由 TeslaMate 发布到 MQTT 的主题都遵循统一前缀 `teslamate/`，例如：

- `teslamate/<car_id>/state` —— 车辆状态（在线/睡眠/驾驶中）
- `teslamate/<car_id>/battery_level` —— 实时 SOC
- `teslamate/<car_id>/location` —— 经纬度
- `teslamate/<car_id>/charging_energy_added` —— 单次充电已加入电量

Home Assistant 集成不需要自己写 MQTT 订阅——官方提供了 HACS 集成（[teslamate/custom-component](https://github.com/teslamate/hass-teslamate)），直接拉 MQTT 主题映射成 HA 实体。

## 四、关键能力清单

以下分类与仪表盘对应，全部基于仓库 README 与官方文档。

### 4.1 通用能力

- 高精度行驶数据记录（位置、海拔、速度、SOC、能耗、车内/外温度）
- 零额外 vampire drain：车一进入睡眠就停止轮询
- 自动地址反查（基于 OpenStreetMap）
- 通过 MQTT 一键接入 Home Assistant、Node-RED、Telegram
- 地理围栏（geofencing）：自定义地点与进入/离开触发
- 多车辆支持：同一个 Tesla 账号下多辆车
- 充电费用跟踪：电费单价、充电桩识别
- 从 TeslaFi、tesla-apiscraper 导入历史数据
- 主题模式：浅色 / 深色 / 跟随系统

### 4.2 预置仪表盘（Grafana，约 20 张）

按 README 列出的顺序：

| 仪表盘 | 主要回答的问题 |
|--------|----------------|
| Battery Health | 电池组实际容量 vs 标称容量，估算衰减 |
| Charge Level | 不同时间尺度下的 SOC 趋势 |
| Charges | 累计/单次充入电量 |
| Charge Details | 充电功率曲线、电压电流、Phase 切换 |
| Charging Stats | 充电桩使用频次与平均时长 |
| Database Information | 库大小、写入速率（运维健康度） |
| Drive Stats | 行程数、总里程、平均速度 |
| Drives | 每次行程的距离/净能耗 |
| Drive Details | 单次行程的功率曲线、海拔变化 |
| Efficiency | 净/毛能耗、Wh/km |
| Locations | 停车/到达的地址反查 |
| Mileage | 累计里程趋势 |
| Overview | 整车的多维概览 |
| Projected Range | 剩余里程 vs 电池健康度 |
| States | 在线/睡眠/驾驶时长分布 |
| Statistics | 全部指标的统计分布 |
| Timeline | 时间轴视图 |
| Trip | 单次行程细节 |
| Updates | 整车 OTA 升级历史 |
| Vampire Drain | 驻车耗电量化分析 |
| Visited | 终身行驶地图（基于 OpenStreetMap） |

### 4.3 数据导入

如果你曾经用过 TeslaFi（已停服）或 tesla-apiscraper，TeslaMate 提供了一键导入工具，迁移成本相对低。

## 五、部署路径

### 5.1 推荐方式：docker-compose

最稳的部署路径是官方 `docker-compose.yml`（仓库根目录）。它会一次性拉起 4 个容器：teslamate、postgres（含 TimescaleDB）、grafana、mosquitto。文件结构大致如下：

```yaml
services:
  teslamate:
    image: teslamate/teslamate:latest
    restart: always
    environment:
      - DATABASE_USER=teslamate
      - DATABASE_PASSWORD=***      # 设置强密码
      - DATABASE_NAME=teslamate
      - DATABASE_HOST=database
      - MQTT_HOST=mosquitto
      - VIRTUAL_HOST=teslamate.example.com  # 可选，反代域名
      - CHECK_TOKEN=true          # 启动时校验 Tesla Token
    ports:
      - 4000:4000                 # Web UI
    depends_on:
      - database
      - mosquitto

  database:
    image: timescale/timescaledb:latest-pg16
    restart: always
    environment:
      - POSTGRES_USER=teslamate
      - POSTGRES_PASSWORD=***      # 与上面一致
      - POSTGRES_DB=teslamate
    volumes:
      - teslamate-db:/var/lib/postgresql/data

  grafana:
    image: teslamate/grafana:latest
    restart: always
    environment:
      - DATABASE_URL=...          # 指向 postgres
    ports:
      - 3000:3000
    volumes:
      - teslamate-grafana-data:/var/lib/grafana

  mosquitto:
    image: eclipse-mosquitto:2
    restart: always
    ports:
      - 1883:1883
    volumes:
      - mosquitto-conf:/mosquitto/config
      - mosquitto-data:/mosquitto/data

volumes:
  teslamate-db:
  teslamate-grafana-data:
  mosquitto-conf:
  mosquitto-data:
```

部署完成后：

1. 浏览器打开 `http://<host>:4000`，首次访问会引导你完成 Tesla OAuth 授权
2. Grafana 在 `http://<host>:3000`，默认账号 `admin`，首次登录会被要求改密
3. 等待车辆下一次主动唤醒（开车门、插充电枪、行驶）后，数据就开始入库

### 5.2 Nix Flake

仓库根目录还提供了 `flake.nix`，适合在 NixOS 上做声明式部署。Nix 用户可以走 `nix run github:teslamate-org/teslamate` 起步。

### 5.3 树莓派部署

TeslaMate 镜像（`teslamate/teslamate:latest`）也支持 arm64，树莓派 4 / 5 可以跑，但官方建议数据库放外接 SSD，因为持续写入会消耗 SD 卡寿命。

## 六、典型使用场景

| 场景 | 怎么用 |
|------|--------|
| 关心电池衰减 | 装好 6 个月后看 Battery Health 仪表盘 |
| 通勤能耗分析 | Drives + Drive Details 按周/月对比 |
| 自动化场景 | MQTT → Home Assistant：充电完成通知、低电量自动关空调 |
| 多车家庭 | 单实例支持多辆 Tesla，按 `car_id` 区分主题 |
| 旧数据迁移 | 从 TeslaFi 导出 CSV，用项目内置 `import` 工具导入 |

## 七、适用边界与不适用人群

### 7.1 适合

- 已经拥有 Tesla（或计划长期持有），想把行车数据"留底"自用
- 已经在用 Home Assistant / Node-RED 做家庭自动化
- 有一台常开的 Linux 主机或 NAS
- 关心电池健康、能耗优化、vampire drain 控制

### 7.2 不适合

- **只有一辆 Tesla、且只在乎控车功能**——用官方 App 即可
- **不愿意自行维护服务器**——每次 TeslaMate 升级、Postgres 备份、SSL 证书续期都要自己动手
- **商用 fleet（车队）管理**——AGPLv3 的 copyleft 条款会让二次分发或 SaaS 化变得复杂
- **Tesla 政策变动敏感**——Tesla 偶尔会调整 API（如流式 endpoint 限流），需要等社区 PR 修复

### 7.3 已知限制

- Tesla 账号必须开启"第三方应用访问"（在车主后台）才能 OAuth
- 流式连接对网络稳定性敏感，国内访问 Tesla API 经常需要稳定的低延迟出口
- 充电费用统计依赖你手动配置电价，跨电价区或商用电桩需要分次记录

## 八、与其他 Tesla 数据方案对比

| 方案 | 部署 | 数据所有权 | 维护成本 | 关键差异 |
|------|------|------------|----------|----------|
| TeslaMate | 自托管 | 完全本地 | 中（需自维护） | 全功能、零耗电、MQTT、20+ 仪表盘 |
| TeslaFi（已停服） | 第三方云 | 第三方 | 低 | 已被 Tesla 终止服务 |
| Tessie | 第三方 SaaS | 第三方 | 低（订阅） | 主打控车 + 通知，无自托管选项 |
| tesla-apiscraper | 自托管 | 本地 | 高 | 早期项目，频繁 polling 会增加 vampire drain |

## 九、开始之前

- 一台能 7×24 运行的机器（树莓派 4B+ / 旧笔记本 / NAS / 旧台式机 / NUC）
- Docker 与 docker-compose（或 NixOS）
- Tesla 车主账号，能登录官方账号门户
- 反向代理（Nginx / Caddy / Traefik）—— 如果想从公网访问
- 心理准备：第一次 OAuth 流程对国内网络不一定友好

## 常见问题（FAQ）

### TeslaMate 会增加车辆的 vampire drain（驻车耗电）吗？

不会。TeslaMate 采用流式订阅模式，只在车辆主动 wake 时才向云端拉数据，一旦车辆进入 sleep 状态就立刻断开连接。设计目标是把车辆尽可能快地放回睡眠状态。

### TeslaMate 的 License 是 AGPL-3.0，对我有什么影响？

AGPL-3.0 是强 copyleft 许可证。如果你修改 TeslaMate 代码并提供网络服务（SaaS 化），你需要开源你的修改。个人自托管使用没有问题。

### TeslaMate 和 TeslaFi 有什么区别？

TeslaFi 是第三方云服务（已停服），数据存在第三方；TeslaMate 是自托管，所有数据本地存储。TeslaMate 提供更完整的数据记录、零耗电、MQTT 集成、20+ 仪表盘。

### 我需要什么硬件来运行 TeslaMate？

一台能 7×24 运行的机器：树莓派 4B+、旧笔记本、NAS、旧台式机、NUC 都可以。需要 Docker 和 docker-compose。

### TeslaMate 的数据库会多大？

取决于记录精度和时长。一般每天新增几 MB 数据。PostgreSQL + TimescaleDB 可以高效存储时序数据，运行一年可能在 GB 级别。

---

## 十、参考资源

- 官方仓库：[github.com/teslamate-org/teslamate](https://github.com/teslamate-org/teslamate)
- 官方文档：[docs.teslamate.org](https://docs.teslamate.org/)
- Home Assistant 集成：[github.com/teslamate/hass-teslamate](https://github.com/teslamate/hass-teslamate)
- 仪表盘截图：[docs.teslamate.org/docs/screenshots/](https://docs.teslamate.org/docs/screenshots/)
- 商标策略：[TRADEMARK.md](https://github.com/teslamate-org/teslamate/blob/main/TRADEMARK.md)
- CLA：[teslamate-org/legal/CLA.md](https://github.com/teslamate-org/legal/blob/main/CLA.md)

---

## 自测题

1. **TeslaMate 的核心定位是什么？**
   <details>
   <summary>点击查看答案</summary>
   自托管 Tesla 车辆数据记录器，跑在你自己的机器上，所有数据本地存储，不依赖任何第三方云服务。
   </details>

2. **TeslaMate 的架构由哪几个组件构成？**
   <details>
   <summary>点击查看答案</summary>
   4 个核心组件：TeslaMate (Elixir)、PostgreSQL (TimescaleDB)、Grafana、Mosquitto (MQTT)。
   </details>

3. **TeslaMate 怎么解决 vampire drain 问题？**
   <details>
   <summary>点击查看答案</summary>
   采用流式订阅模式，只在车辆主动 wake 时才向云端拉数据，一旦车辆进入 sleep 状态就立刻断开连接。
   </details>

4. **TeslaMate 提供多少张预置 Grafana 仪表盘？**
   <details>
   <summary>点击查看答案</summary>
   约 20 张，包括 Battery Health、Charge Level、Drives、Efficiency、Vampire Drain 等。
   </details>

5. **TeslaMate 的 License 是什么？有什么影响？**
   <details>
   <summary>点击查看答案</summary>
   AGPL-3.0。如果是商用 fleet（车队）管理或要做 SaaS 化，需要谨慎评估 copyleft 条款。
   </details>

---

## 练习

### 练习 1：部署 TeslaMate
1. 准备一台 Linux 主机或 NAS
2. 安装 Docker 和 docker-compose
3. 复制本文的 docker-compose.yml 示例
4. 修改密码和配置
5. 运行 `docker-compose up -d`
6. 访问 `http://<host>:4000` 完成 Tesla OAuth 授权

### 练习 2：配置 Home Assistant 集成
1. 在 Home Assistant 安装 HACS
2. 通过 HACS 安装 TeslaMate 集成
3. 配置 MQTT Broker 地址
4. 查看 Home Assistant 中是否出现 TeslaMate 实体
5. 创建自动化：当充电完成时发送通知

### 练习 3：分析电池健康
1. 让 TeslaMate 运行至少 6 个月
2. 打开 Grafana，查看 Battery Health 仪表盘
3. 分析电池组实际容量 vs 标称容量
4. 估算电池衰减程度

---

## 进阶路径

1. **深入研究 TeslaMate 架构**：理解 Elixir/Phoenix/LiveView、PostgreSQL/TimescaleDB、Grafana、MQTT 的技术栈
2. **自定义 Grafana 仪表盘**：基于 TeslaMate 数据库，创建自己的 Grafana 仪表盘
3. **开发 TeslaMate 扩展**：基于 TeslaMate 的 MQTT 输出，开发自己的应用或集成
4. **研究 Tesla API**：深入理解 Tesla 官方 API，理解 TeslaMate 的数据采集原理
5. **参与 TeslaMate 社区**：提交 PR、报告 bug、改进文档

---

## 资料口径说明

1. **信息来源**：本文基于 teslamate-org/teslamate 仓库的 README（2026-06 版本）、官方文档和社区讨论
2. **版本时效性**：TeslaMate 仍在活跃维护中，本文描述的功能和部署方式可能在未来版本中变化
3. **技术准确性**：本文的技术描述基于公开文档，未验证所有功能在实际环境中的表现
4. **Tesla API 限制**：Tesla 偶尔会调整 API，TeslaMate 的兼容性取决于社区维护
5. **使用风险**：使用 TeslaMate 需要 Tesla 账号授权，请遵守 Tesla 的使用条款

---

**一句话总结**：如果你既想"看穿"自己那辆 Tesla 的能耗与电池健康，又想把车况接到自己的家庭自动化系统里，TeslaMate 是目前社区里最成熟、文档最完整的中文/英文可读性都好的自托管方案。它的"零 vampire drain"设计是它和早期同类工具最大的区别，也是它能在一台机器上稳定跑一两年的关键。
