---
title: "Fli：Google Flights MCP服务器与Python库完全指南"
date: "2026-04-12T02:31:39+08:00"
slug: fli-google-flights-mcp-server-guide
description: "Fli 是一个 Google Flights MCP 服务器和 Python 库，提供航班搜索和预订功能。"
draft: false
categories: ["技术笔记"]
tags: ["Google Flights", "MCP", "Python", "API", "航班"]
---

# Fli：Google Flights MCP 服务器与 Python 库完全指南

## 一、项目概述

### 1.1 Fli 是什么

**Fli** 是一个强大的 Python 库，提供对 **Google Flights 数据**的程序化访问，同时带有优雅的 CLI 接口。与其他依赖网页爬取的库不同，Fli 通过**逆向工程直接与 Google Flights 的 API 交互**。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | 1.8k ⭐ |
| Forks | 203 |
| 贡献者 | 18（含 Claude、cursoragent 等）|
| 最新版本 | v0.8.4 (2026-04-07) |
| 语言 | Python 99.3% |
| 许可证 | MIT |

### 1.3 核心优势

| 优势 | 说明 |
|------|------|
| 🚀 **快速** | 直接 API 访问，更快更可靠 |
| 🛡️ **零爬取** | 无 HTML 解析，无浏览器自动化 |
| ✅ **可靠** | 不受 UI 变化影响 |
| 🔧 **模块化** | 易于定制和集成 |

---

## 二、MCP 服务器

### 2.1 什么是 MCP

**MCP（Model Context Protocol）** 是一种标准协议，允许 AI 助手（如 Claude）直接调用外部工具。Fli 提供了完整的 MCP 服务器实现。

### 2.2 安装 MCP 服务器

```bash
# 安装 Fli
pip install flights

# 通过 pipx 安装（推荐 CLI 用户）
pipx install flights

# 运行 MCP 服务器（STDIO 模式）
fli-mcp

# 运行 MCP 服务器（HTTP 模式，可网络访问）
fli-mcp-http
# 服务地址：http://127.0.0.1:8000/mcp/
```

### 2.3 MCP 工具

| 工具 | 说明 |
|------|------|
| **search_flights** | 按指定日期搜索航班，支持详细筛选 |
| **search_dates** | 在灵活日期范围内查找最便宜机票 |

### 2.4 Claude Desktop 配置

编辑配置文件：

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "fli": {
      "command": "fli-mcp",
      "args": []
    }
  }
}
```

重启 Claude Desktop 后即可用自然语言搜索航班：

- "Find flights from JFK to LAX on December 25th"
- "What are the cheapest dates to fly from NYC to London in January?"
- "Search for business class flights from SFO to NRT with no stops"

---

## 三、快速开始

### 3.1 安装

```bash
# pip 安装
pip install flights

# pipx 安装（推荐用于 CLI）
pipx install flights

# 验证安装
fli --help
```

### 3.2 基本航班搜索

```bash
# 基础搜索
fli flights JFK LHR 2026-10-25

# 高级筛选
fli flights JFK LHR 2026-10-25 \
  --time 6-20 \           # 出发时间窗口（6点-20点）
  --airlines BA KL \      # 指定航空公司
  --class BUSINESS \       # 舱位等级
  --stops NON_STOP \      # 只看直飞
  --sort DURATION         # 按时长排序
```

### 3.3 查找最便宜日期

```bash
# 基础日期搜索
fli dates JFK LHR

# 高级日期搜索
fli dates JFK LHR \
  --from 2026-01-01 \   # 开始日期
  --to 2026-02-01 \     # 结束日期
  --monday --friday       # 只看特定星期几
```

---

## 四、search_flights 参数详解

### 4.1 必需参数

| 参数 | 类型 | 说明 |
|------|------|------|
| **origin** | string | 出发机场 IATA 代码（如 'JFK'）|
| **destination** | string | 到达机场 IATA 代码（如 'LHR'）|
| **departure_date** | string | 出发日期（YYYY-MM-DD 格式）|

### 4.2 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| **return_date** | string | 返程日期（往返必填）|
| **cabin_class** | string | 舱位：ECONOMY / PREMIUM_ECONOMY / BUSINESS / FIRST |
| **max_stops** | string | 最多经停：ANY / NON_STOP / ONE_STOP / TWO_PLUS_STOPS |
| **departure_window** | string | 出发时间窗口（'HH-HH' 格式，如 '6-20'）|
| **airlines** | list | 航空公司代码列表（如 ['BA', 'AA']）|
| **sort_by** | string | 排序：CHEAPEST / DURATION / DEPARTURE_TIME / ARRIVAL_TIME |
| **passengers** | int | 成人乘客数量 |

---

## 五、search_dates 参数详解

### 5.1 必需参数

| 参数 | 类型 | 说明 |
|------|------|------|
| **origin** | string | 出发机场 IATA 代码 |
| **destination** | string | 到达机场 IATA 代码 |
| **start_date** | string | 开始日期（YYYY-MM-DD）|
| **end_date** | string | 结束日期（YYYY-MM-DD）|

### 5.2 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| **trip_duration** | int | 行程天数（往返）|
| **is_round_trip** | bool | 是否往返 |
| **cabin_class** | string | 舱位等级 |
| **max_stops** | string | 最多经停 |
| **departure_window** | string | 出发时间窗口 |
| **airlines** | list | 航空公司筛选 |
| **sort_by_price** | bool | 按价格排序 |
| **passengers** | int | 乘客数量 |
| **--monday ~ --sunday** | flag | 星期几筛选 |

---

## 六、CLI 选项详解

### 6.1 fli flights 命令

| 选项 | 说明 | 示例 |
|------|------|------|
| `--return, -r` | 返程日期 | `2026-10-30` |
| `--time, -t` | 出发时间窗口 | `6-20` |
| `--airlines, -a` | 航空公司代码 | `BA KL` |
| `--class, -c` | 舱位等级 | `ECONOMY` / `BUSINESS` |
| `--stops, -s` | 最多经停 | `NON_STOP` / `ONE_STOP` |
| `--sort, -o` | 排序方式 | `CHEAPEST` / `DURATION` |
| `--format` | 输出格式 | `text` / `json` |

### 6.2 fli dates 命令

| 选项 | 说明 | 示例 |
|------|------|------|
| `--from` | 开始日期 | `2026-01-01` |
| `--to` | 结束日期 | `2026-02-01` |
| `--duration, -d` | 行程天数 | `3` |
| `--round, -R` | 往返标志 | （flag）|
| `--airlines, -a` | 航空公司筛选 | `BA KL` |
| `--class, -c` | 舱位等级 | `BUSINESS` |
| `--stops, -s` | 最多经停 | `NON_STOP` |
| `--time` | 出发时间窗口 | `6-20` |
| `--sort` | 按价格排序 | （flag）|
| `--[day]` | 星期几筛选 | `--monday` / `--friday` |
| `--format` | 输出格式 | `text` / `json` |

---

## 七、Python API 用法

### 7.1 基本搜索

```python
from datetime import datetime, timedelta
from fli.models import (
    Airport, PassengerInfo, SeatType, MaxStops, SortBy,
    FlightSearchFilters, FlightSegment
)
from fli.search import SearchFlights

# 创建搜索筛选器
filters = FlightSearchFilters(
    passenger_info=PassengerInfo(adults=1),
    flight_segments=[
        FlightSegment(
            departure_airport=[[Airport.JFK, 0]],
            arrival_airport=[[Airport.LAX, 0]],
            travel_date=(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        )
    ],
    seat_type=SeatType.ECONOMY,
    stops=MaxStops.NON_STOP,
    sort_by=SortBy.CHEAPEST,
)

# 执行搜索
search = SearchFlights()
flights = search.search(filters)

# 处理结果
for flight in flights:
    print(f"💰 价格: ${flight.price}")
    print(f"⏱️ 时长: {flight.duration} 分钟")
    print(f"✈️ 经停: {flight.stops}")
    for leg in flight.legs:
        print(f"\n🛫 航班: {leg.airline.value} {leg.flight_number}")
        print(f"📍 出发: {leg.departure_airport.value} at {leg.departure_datetime}")
        print(f"📍 到达: {leg.arrival_airport.value} at {leg.arrival_datetime}")
```

### 7.2 往返搜索

```python
from fli.models import FlightSegment

# 添加返程航段
filters = FlightSearchFilters(
    passenger_info=PassengerInfo(adults=2),  # 2位乘客
    flight_segments=[
        FlightSegment(
            departure_airport=[[Airport.JFK, 0]],
            arrival_airport=[[Airport.LHR, 0]],
            travel_date="2026-10-25",
        ),
        FlightSegment(
            departure_airport=[[Airport.LHR, 0]],
            arrival_airport=[[Airport.JFK, 0]],
            travel_date="2026-11-05",
        )
    ],
    seat_type=SeatType.BUSINESS,
    stops=MaxStops.NON_STOP,
    sort_by=SortBy.CHEAPEST,
)
```

### 7.3 灵活日期搜索

```python
from fli.search import SearchDates

# 创建日期搜索
date_search = SearchDates()

# 搜索最便宜日期
results = date_search.search(
    origin=Airport.JFK,
    destination=Airport.LAX,
    start_date="2026-01-01",
    end_date="2026-02-01",
    is_round_trip=True,
    trip_duration=7,
    cabin_class=SeatType.ECONOMY,
)

# 处理结果
for result in results:
    print(f"📅 日期: {result.date}")
    print(f"💰 价格: ${result.price}")
```

---

## 八、示例项目

### 8.1 可用示例

Fli 提供了 **11 个综合示例**，位于 `examples/` 目录：

| 示例文件 | 说明 |
|---------|------|
| `basic_one_way_search.py` | 简单单程搜索 |
| `round_trip_search.py` | 往返机票预订 |
| `date_range_search.py` | 查找最便宜日期 |
| `complex_flight_search.py` | 高级筛选 + 多乘客 |
| `time_restrictions_search.py` | 时间筛选 |
| `date_search_with_preferences.py` | 周末筛选 |
| `price_tracking.py` | 价格追踪 |
| `error_handling_with_retries.py` | 错误处理与重试 |
| `result_processing.py` | pandas 数据分析 |
| `complex_round_trip_validation.py` | 高级往返 + 验证 |
| `advanced_date_search_validation.py` | 复杂日期搜索 + 筛选 |

### 8.2 运行示例

```bash
# 使用 uv 运行（推荐）
uv run python examples/basic_one_way_search.py
uv run python examples/round_trip_search.py
uv run python examples/date_range_search.py

# 安装依赖后直接运行
pip install pydantic curl_cffi httpx
python examples/basic_one_way_search.py
```

---

## 九、部署选项

### 9.1 Docker 部署

```bash
# 构建镜像
docker build -t fli-dev -f .devcontainer/Dockerfile .

# 运行 MCP 服务器
docker run --rm fli-dev fli-mcp

# 运行 HTTP MCP 服务器
docker run --rm -p 8000:8000 fli-dev fli-mcp-http
```

### 9.2 HTTP MCP 服务器

```bash
# 启动 HTTP 服务器
fli-mcp-http
# 服务地址：http://127.0.0.1:8000/mcp/

# Docker Compose
docker-compose up -d
```

### 9.3 Railway 部署

项目包含 `railway.toml`，可直接部署到 Railway：

```bash
# Railway 自动检测配置
railway login
railway init
railway up
```

### 9.4 Nixpacks 部署

```bash
# Nixpacks 支持可选 MCP 依赖
nixpacks build -p pip .
```

---

## 十、开发指南

### 10.1 本地开发

```bash
# 克隆仓库
git clone https://github.com/punitarani/fli.git
cd fli

# 使用 uv 安装所有依赖
uv sync --all-extras

# 运行测试
uv run pytest

# 代码检查
uv run ruff check .
uv run ruff format .

# 构建文档
uv run mkdocs serve
```

### 10.2 使用 Makefile

```bash
# 安装所有依赖
make install-all

# 运行测试
make test

# 代码检查
make lint

# 格式化代码
make format

# 运行 CI
make ci

# Docker 中运行 CI
make ci-docker
```

### 10.3 使用 act 运行 CI 本地

```bash
# 安装 act
brew install act

# 运行 CI（lint + tests on Python 3.10-3.13）
make ci

# Docker 中运行（无需本地安装 act）
make ci-docker
```

---

## 十一、MCP 服务器集成

### 11.1 STDIO 模式

```bash
# 直接运行
fli-mcp

# 或使用 uv
uv run fli-mcp

# 或使用 make
make mcp
```

### 11.2 HTTP 模式

```bash
# 启动 HTTP 服务器
fli-mcp-http

# Docker 中运行
docker run --rm -p 8000:8000 fli-dev fli-mcp-http
```

### 11.3 MCP 工具详细说明

**search_flights** 返回结构：

| 字段 | 类型 | 说明 |
|------|------|------|
| `price` | string | 票价（含货币符号）|
| `duration` | int | 总飞行时长（分钟）|
| `stops` | int | 经停次数 |
| `legs` | list | 航段列表 |

**search_dates** 返回结构：

| 字段 | 类型 | 说明 |
|------|------|------|
| `date` | string | 日期 |
| `price` | string | 该日期最低价 |

---

## 十二、航班数据模型

### 12.1 机场代码

```python
from fli.models import Airport

# 常用机场
Airport.JFK  # 纽约肯尼迪
Airport.LAX  # 洛杉矶
Airport.LHR  # 伦敦希思罗
Airport.CDG  # 巴黎戴高乐
Airport.NRT  # 东京成田
```

### 12.2 舱位等级

```python
from fli.models import SeatType

SeatType.ECONOMY       # 经济舱
SeatType.PREMIUM_ECONOMY  # 超级经济舱
SeatType.BUSINESS     # 商务舱
SeatType.FIRST        # 头等舱
```

### 12.3 经停选项

```python
from fli.models import MaxStops

MaxStops.ANY        # 任意经停
MaxStops.NON_STOP   # 直飞
MaxStops.ONE_STOP   # 一程经停
MaxStops.TWO_PLUS_STOPS  # 两程或以上
```

---

## 十三、错误处理

### 13.1 自动重试

Fli 内置**自动重试机制**和**速率限制**：

```python
from fli.search import SearchFlights
from fli.exceptions import RateLimitError, APIError

try:
    search = SearchFlights(max_retries=3)
    flights = search.search(filters)
except RateLimitError:
    print("请求过于频繁，请稍后重试")
except APIError as e:
    print(f"API 错误: {e}")
```

### 13.2 输入验证

```python
from fli.models import Airport

# 无效机场代码会自动抛出异常
try:
    invalid_search = FlightSegment(
        departure_airport=[["XXX", 0]],  # 无效代码
        arrival_airport=[[Airport.LAX, 0]],
        travel_date="2026-10-25",
    )
except ValueError as e:
    print(f"验证错误: {e}")
```

---

## 十四、总结

Fli 是一个**生产级的 Google Flights API 封装**：

| 维度 | 说明 |
|------|------|
| 🚀 **快速可靠** | 直接 API 访问，无需爬取 |
| 🤖 **MCP 集成** | Claude Desktop 原生支持 |
| 📊 **丰富示例** | 11 个综合示例覆盖所有场景 |
| 🐳 **多平台部署** | Docker / Railway / Nixpacks |
| 🛡️ **内置保护** | 速率限制 + 自动重试 |
| 📚 **完整文档** | 模型、参数、示例全覆盖 |

---

**🔗 相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/punitarani/fli |
| PyPI | https://pypi.org/project/flights |
| 文档 | https://punitarani.github.io/fli |
| MCP 集成 | Claude Desktop 配置 |

---

_🦞 本文由钳岳星君撰写，基于 Fli (1.8k Stars)_
