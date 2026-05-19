---
title: "Shadowbroker：开源情报一站式工具——飞机轨迹、间谍卫星、地震数据尽在掌握"
date: "2026-05-19"
tags:
  - 开源情报
  - OSINT
  - 数据分析
  - Python
  - 安全研究
---

# Shadowbroker：开源情报一站式工具

**Stars: 7,773** | **今日: +767** | **Forks: 1,194** | **Language: Python**

GitHub: [BigBodyCobain/Shadowbroker](https://github.com/BigBodyCobain/Shadowbroker)

## 一句话评价

Shadowbroker 是一个开源情报（OSINT）聚合平台，连接航班追踪（ADS-B）、舰船追踪（AIS）、间谍卫星数据库、地震监测、社交媒体等多源数据，让你用 AI 发现传统搜索无法找到的关联信息。

## 核心问题：什么是开源情报？

OSINT（Open Source Intelligence）指从公开可获取的信息源中收集、整理和分析情报的技术。传统上分析师需要分别访问数十个网站、数据库和 API，数据碎片化严重。Shadowbroker 的核心价值：**一个平台，多源数据，AI 辅助关联**。

```
数据源                          可发现内容
─────────────────────────────────────────────────
ADS-B 航班数据        →          私人飞机轨迹、富豪行踪、军事飞行
AIS 船舶数据          →          货轮/游艇位置、海上活动
Satellite Catalog     →          在轨卫星轨道、侦察卫星过境时间
USGS 地震数据         →          全球地震实时监测、异常事件
MarineTraffic         →          船舶历史轨迹、港口停靠记录
OpenSky Network       →          实时航班状态、航班历史
```

## 核心功能

### 飞机追踪（ADS-B / OpenSky）

通过 ADS-B（广播式自动相关监视）数据追踪飞机：

```python
from shadowbroker import AircraftTracker

tracker = AircraftTracker()
# 获取某飞机最近24小时轨迹
track = tracker.get_flight_history("N12345")  # 注册号
for point in track:
    print(point.timestamp, point.latitude, point.longitude, point.altitude)
```

典型应用场景：
- 追踪特定私人飞机的行踪（富豪、政治人物）
- 分析特定航线的历史航班模式
- 军事/政府飞机活动监测

### 船舶追踪（AIS）

AIS（自动识别系统）数据追踪全球船舶：

```python
from shadowbroker import ShipTracker
tracker = ShipTracker()
# 查询在某海域出现的船只
ships = tracker.get_ships_in_region(lat_min=30, lat_max=35, lon_min=120, lon_max=130)
```

### 卫星数据库

整合多种卫星编目数据：

- ** NORAD TLE 数据**：所有在轨物体的轨道参数
- **侦察卫星**：计算特定侦察卫星何时过境某地上空
- **卫星碰撞预警**：计算接近事件（conjunction analysis）

### 地震监测

接入 USGS 实时地震数据：

```python
from shadowbroker import SeismicMonitor
monitor = SeismicMonitor()
# 获取最近24小时4.0级以上地震
quakes = monitor.get_quakes(min_magnitude=4.0, hours=24)
```

### AI 关联分析（核心亮点）

Shadowbroker 的差异化特性：内置 LLM 辅助分析模块，让 AI 帮助发现数据间的关联：

> "Hook an AI agent up to have it parse through data and find previously unseen correlations."

```python
from shadowbroker import AIAnalyzer

analyzer = AIAnalyzer()
# 询问："过去一周，富豪X的私人飞机轨迹和某地地震事件是否有关联？"
result = analyzer.query(
    "Find correlations between flight N12345 and seismic events near coordinates X,Y in the past week"
)
print(result.insights)
```

这使得 Shadowbroker 不仅是数据聚合器，还是一个**智能 OSINT 分析助手**。

## 安装

```bash
pip install shadowbroker
```

或源码安装：

```bash
git clone https://github.com/BigBodyCobain/Shadowbroker.git
cd Shadowbroker
pip install -e .
```

需要获取以下数据源的 API Key（部分免费）：
- OpenSky Network（免费）
- ADSBExchange（免费层可用）
- MarineTraffic（需注册）
- USGS（免费）

## 应用场景

| 领域 | 具体使用 |
|------|---------|
| 调查报道 | 追踪特定人物的私人飞机/游艇活动轨迹 |
| 安全研究 | 分析某地区的军事活动模式 |
| 供应链分析 | 追踪货船航线，发现异常停靠 |
| 学术研究 | 历史航班/船舶数据的统计分析 |
| 灾害响应 | 实时获取灾区附近的航班和船舶信息 |

## 注意事项

- **数据合法性**：ADS-B/AIS 数据均为公开广播数据，但使用目的需遵守当地法律
- **隐私考量**：追踪个人行踪涉及隐私问题，仅用于合法研究和报道
- **数据延迟**：部分数据源有不同延迟，实时性有限
- **覆盖范围**：部分区域（尤其是海上和偏远地区）数据覆盖不完整

## 总结

Shadowbroker 解决了 OSINT 分析师数据碎片化的痛点，将航班、船舶、卫星、地震等多源公开数据整合到一个平台，并引入 AI 辅助关联分析。对于调查记者、安全研究员、数据新闻从业者，这是一个值得关注的工具。

## 参考链接

- 仓库：[BigBodyCobain/Shadowbroker](https://github.com/BigBodyCobain/Shadowbroker)
- OpenSky Network API：https://opensky-network.org/apidoc/
- USGS 地震数据：https://earthquake.usgs.gov/fdsnws/event/1/
- ADSBExchange：https://www.adsbexchange.com/