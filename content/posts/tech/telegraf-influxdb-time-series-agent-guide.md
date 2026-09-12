---
title: "Telegraf：InfluxDB 开源时序数据采集 Agent，300+ 插件生态实战指南"
date: "2026-05-16T15:10:00+08:00"
slug: "telegraf-influxdb-time-series-agent-guide"
github_repo: "influxdata/telegraf"
source_key: "gh:influxdata/telegraf"
aliases:
  - "/posts/tech/telegraf-agent-time-series-collection/"
  - "/posts/tech/telegraf-agent-300-plugins-time-series/"
  - "/posts/tech/telegraf-metrics-collection-agent-guide/"
description: "Telegraf 是 InfluxDB 官方开源的指标采集 Agent，支持 300+ 输入/输出插件，覆盖系统监控、云服务、消息队列等场景。本文从核心架构、插件生态、快速配置到生产部署进行完整解读，助你搭建现代化可观测性基础设施。"
draft: false
categories: ["技术笔记"]
tags: ["DevOps", "可观测性", "Golang", "插件系统"]
---

# Telegraf：InfluxDB 开源时序数据采集 Agent，300+ 插件生态实战指南

做可观测性堆栈时，数据采集层最容易演变成"每个数据源一个脚本"的局面。Telegraf 解决的就是这件事：用一套统一的 TOML 配置、一条处理流水线，把系统指标、云服务、消息队列、IoT 协议全部收敛到同一个 Agent 里。

项目由 InfluxData 官方维护，截至 2026 年已获得 **15,000+ Stars**、**1,200+ 贡献者**、**300+ 插件**。两个核心特点：零外部依赖——编译出一个静态二进制就能跑；插件架构——换一个 TOML 块就切数据源或输出目标，不改代码。

## 核心架构：四阶段数据处理流水线

Telegraf 把数据处理拆成四个阶段：

```
Inputs → Processors → Aggregators → Outputs
```

| 阶段 | 作用 | 示例插件 |
|------|------|---------|
| **Input** | 数据源采集 | cpu, mem, kafka, mqtt |
| **Processor** | 数据转换/过滤 | regex, converter, pivot |
| **Aggregator** | 数据聚合/统计 | basicstats, minmax, valuecounter |
| **Output** | 数据输出目标 | influxdb, prometheus, file |

每个阶段可配置多个实例，并行处理。数据通过两个间隔解耦——`interval` 控制采集频率，`flush_interval` 控制写出频率。下面用一个具体场景说明四阶段如何协作。

### 一次采集的全路径：CPU 指标从诞生到入库

配置 `[[inputs.cpu]]` 和 `[[outputs.influxdb]]`，`interval = "10s"`，`flush_interval = "10s"`。一条 CPU 指标在 Telegraf 内部要经历这样一条路径：

1. **采集**——CPU Input 插件通过 `/proc/stat`（Linux）或系统调用拉取当前 CPU 时间片数据，生成 InfluxDB 行协议格式的指标：`cpu,host=node1,cpu=cpu0 usage_idle=95.0,usage_system=2.5,usage_user=2.5`。
2. **处理**——数据进入 Processor 链。如果配了 `[[processors.converter]]`，字段类型会从字符串转成 float64；没配 Processor 就原样透传。
3. **聚合**——Aggregator 插件（如果开启）在各自的 `period` 窗口内做聚合：比如 `basicstats` 每 30 秒算一次均值、方差和最值，把窗口内多条原始数据压成一条。
4. **写出**——每到一个 `flush_interval`，Output 插件把暂存的指标按批次批量写入 InfluxDB。

### 收集间隔与刷新间隔

`interval` 和 `flush_interval` 都要配在 `[agent]`，作用不同：

```toml
[agent]
  interval = "10s"          # 每 10s 从 inputs 收集一次数据
  flush_interval = "10s"    # 每 10s 将数据刷新到 outputs
  metric_batch_size = 1000  # 每批最多写出多少条
  metric_buffer_limit = 10000  # 每个 output 的内存缓冲区上限（条）
```

官方文档明确要求：**`flush_interval` 不应小于 `interval`**。原因不是"数据来不及采完"，而是写密度问题——如果刷新比采集还勤，会有很多次 flush 手里的数据是空的，白白做了无用功。一般保持两者相等，或刷新稍慢于采集。

### 每个 Output 独立的内存缓冲区

Telegraf 为**每个 Output 插件**维护一块独立的内存缓冲（`metric_buffer_limit`），数据先落缓冲区、再按批写出：

- 缓冲区只在**写目标失败**时才会堆积，不是常驻积压。
- 一旦 InfluxDB 恢复、某次写入成功，缓冲区内积压的数据会一并刷出。
- 当缓冲区写满而目标仍不可达时，最老的指标被优先丢弃，并计入 `metrics_dropped`。

生产环境里 `telegraf_metrics_dropped` 应当始终处于可观测状态——它一旦涨起来，说明你的缓冲或写目标出问题了。

## 插件生态详解

### Input 插件（数据采集源）

**系统监控**
```toml
[[inputs.cpu]]
  percpu = true
  totalcpu = true
[[inputs.mem]]
[[inputs.disk]]
  paths = ["/", "/data"]
[[inputs.net]]
  interfaces = ["eth0", "en0"]
[[inputs.diskio]]
[[inputs.processes]]
```

**云服务与中间件**
```toml
# Docker 容器指标
[[inputs.docker]]
  endpoint = "unix:///var/run/docker.sock"

# Kubernetes
[[inputs.kubernetes]]
  url = "http://127.0.0.1:10255"

# MySQL
[[inputs.mysql]]
  servers = ["root:password@tcp(127.0.0.1:3306)/"]

# Kafka
[[inputs.kafka_consumer]]
  brokers = ["localhost:9092"]
  topics = ["metrics"]
```

**消息队列与协议**
```toml
[[inputs.mqtt_consumer]]
  servers = ["tcp://localhost:1883"]
  topics = ["device/+/data"]

[[inputs.amqp_consumer]]
  servers = ["amqp://localhost:5672"]
  queue = "telegraf"

[[inputs.snmp]]
  agents = ["udp://localhost:161"]
  version = "2c"
  community = "public"
```

**IoT 与工业协议**
```toml
# OPC UA 工业物联网
[[inputs.opcua]]
  endpoint = "opc.tcp://localhost:4840"
  security_policy = "None"

# Modbus TCP
[[inputs.modbus]]
  name = "PLC1"
  type = "tcp"
  address = "localhost:502"
  slave_id = 1
  [[inputs.modbus.requests]]
    device_id = 1
    byte_order = "ABCD"
    data_type = "INT16"
    address = [0, 1]
    quantity = 2
```

### Output 插件（数据导出目标）

```toml
# InfluxDB 1.x（时序数据库）
[[outputs.influxdb]]
  urls = ["http://localhost:8086"]
  database = "telegraf"
  username = "telegraf"
  password = "password"

# InfluxDB 2.x / 3.x（推荐新部署用 v2 协议）
[[outputs.influxdb_v2]]
  urls = ["http://localhost:8086"]
  token = "your-token"
  organization = "your-org"
  bucket = "telegraf"

# Prometheus（指标抓取）
[[outputs.prometheus_client]]
  listen = ":9273"
  metric_version = 2

# Kafka
[[outputs.kafka]]
  brokers = ["localhost:9092"]
  topic = "telegraf"

# MQTT
[[outputs.mqtt]]
  brokers = ["tcp://localhost:1883"]
  topic = "telegraf/all"
```

注意：`token` / `organization` / `bucket` 是 `outputs.influxdb_v2` 的参数；如果要连老式 v1 InfluxDB，用 `outputs.influxdb` + `database` / `username` / `password`，不要混在一起。

### Processor 插件（数据转换）

```toml
# 正则提取字段
[[processors.regex]]
  [[processors.regex.tags]]
    key = "uri"
    pattern = "^/api/v([0-9]+)"
    replacement = "v${1}"

# 类型转换
[[processors.converter]]
  [processors.converter.fields]
    integer = ["value", "count"]
    float = ["rate"]
    string = ["status"]

# 顶点数过滤
[[processors.topk]]
  [processors.topk.config]
    topk = 5
    period = "30s"
    metric_version = 2
    fields = ["cpu"]
```

### Aggregator 插件（数据聚合）

```toml
# 基础统计聚合
[[aggregators.basicstats]]
  period = "30s"
  stats = ["count", "min", "max", "mean", "s2", "sum"]

# 分位数聚合（用于告警异常检测）
[[aggregators.quantile]]
  period = "60s"
  quantile = 0.99
  metric_version = 2
```

## 快速上手：5 分钟跑通第一个配置

### 1. 安装（macOS）

```bash
# Homebrew
brew install telegraf

# 或从官方下载页获取对应平台的二进制
curl -LO https://dl.influxdata.com/telegraf/releases/telegraf_latest_darwin_amd64.tar.gz
tar xzf telegraf_latest_darwin_amd64.tar.gz
```

### 2. 最小配置示例

```toml
# telegraf.conf
[agent]
  interval = "10s"
  flush_interval = "10s"
  round_interval = true

# 输入：CPU + 内存 + 磁盘
[[inputs.cpu]]
  percpu = true
[[inputs.mem]]
[[inputs.disk]]

# 输出：标准输出（调试用）
[[outputs.file]]
  files = ["stdout"]
  data_format = "influx"
```

### 3. 启动与验证

```bash
# 前台运行一次并打印指标（调试）
telegraf --config telegraf.conf --test

# 后台运行
telegraf --config telegraf.conf

# 查看输出
telegraf --config telegraf.conf --test | head -20
```

正确输出类似：

```
> cpu,cpu=cpu0 usage_idle=98.5,usage_system=1.2,usage_user=0.3 1700000000000000000
> mem,host=localhost free=16384,used=8192 1700000000000000000
```

### 4. 配置 InfluxDB 输出

生产环境中通常将数据写入 InfluxDB（v2/v3 用 token 鉴权）：

```toml
[[outputs.influxdb_v2]]
  urls = ["http://192.168.1.100:8086"]
  token = "your-token"
  organization = "your-org"
  bucket = "telegraf"
  timeout = "5s"
  content_encoding = "gzip"   # 节省带宽
```

## 配置文件规范与实践建议

### TOML 语法要点

Telegraf 使用 TOML 格式，以下是常见坑点：

**正确写法**
```toml
[[inputs.cpu]]
  percpu = true          # 布尔值
  totalcpu = true

[[inputs.mysql]]
  servers = ["root:password@tcp(127.0.0.1:3306)/"]  # 字符串数组
```

**错误写法（单位与类型）**
```toml
# ❌ 错误：interval 是数字
interval = 10
# ✅ 正确：interval 是带单位的字符串
interval = "10s"
```

### 插件顺序与全局设置

```toml
# 全局 [agent] 设置必须在 [[inputs]] 之前
[agent]
  interval = "10s"
  flush_interval = "10s"
  metric_buffer_limit = 10000
  collection_jitter = "0s"

# 顺序：agent → inputs → processors → aggregators → outputs
[[inputs.cpu]]
  percpu = true
```

### 环境变量注入

Telegraf 把环境变量语法从旧版的 `$VAR` 统一成了 `${VAR}`，支持默认值和必填检查。字符串要加引号，数字/布尔不加。

**InfluxDB v1 输出**
```toml
[[outputs.influxdb]]
  urls = ["${INFLUX_URL}"]
  database = "${INFLUX_DB}"
  username = "${INFLUX_USER}"
  password = "${INFLUX_PASSWORD}"
```

**InfluxDB v2/v3 输出**
```toml
[[outputs.influxdb_v2]]
  urls = ["${INFLUX_HOST}"]
  token = "${INFLUX_TOKEN}"
  organization = "${INFLUX_ORG}"
  bucket = "${INFLUX_BUCKET}"
```

启动时传入环境变量：
```bash
INFLUX_TOKEN=my-token \
telegraf --config telegraf.conf
```

### 多配置文件拆分

`--config-directory` 会把指定目录下所有 `.conf` 结尾的文件一并加载：

```bash
/etc/telegraf/
├── telegraf.conf          # 主配置
├── conf.d/
│   ├── inputs.conf        # 输入插件
│   ├── processors.conf    # 处理器
│   └── outputs.conf       # 输出目标
```

启动时显式指定配置目录：
```bash
telegraf --config telegraf.conf --config-directory /etc/telegraf/conf.d
```

> 每个子文件本身必须是合法配置；Telegraf 会分别解析后取并集，而不是先拼接再解析。

## 生产环境部署

### Systemd 守护进程（Linux）

```toml
# /etc/telegraf/telegraf.conf
[agent]
  interval = "10s"
  flush_interval = "10s"
```

```ini
# /etc/systemd/system/telegraf.service
[Unit]
Description=Telegraf Agent
After=network-online.target

[Service]
ExecStart=/usr/bin/telegraf --config /etc/telegraf/telegraf.conf
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
sudo systemctl enable telegraf
sudo systemctl start telegraf
sudo journalctl -u telegraf -f
```

### Docker 部署

```yaml
# docker-compose.yml
services:
  telegraf:
    image: telegraf:1.40
    container_name: telegraf
    restart: unless-stopped
    volumes:
      - ./telegraf.conf:/etc/telegraf/telegraf.conf:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    environment:
      - HOST_PROC=/host/proc
      - HOST_SYS=/host/sys
      - HOST_ETC=/host/etc
    network_mode: host
    pid_mode: host
```

> Docker 部署时需要挂载 `HOST_PROC`、`HOST_SYS` 等路径以访问宿主机指标。

### 多 Agent + 多个后端节点

多个 InfluxDB 节点对外暴露时，推荐把一组 `urls` 配在同一个 output 里作为冗余：

```toml
[[outputs.influxdb_v2]]
  urls = [
    "http://influx1:8086",
    "http://influx2:8086",
    "http://influx3:8086"
  ]
  token = "${INFLUX_TOKEN}"
  organization = "${INFLUX_ORG}"
  bucket = "telegraf"
  content_encoding = "gzip"   # 节省带宽
  timeout = "5s"
```

### 性能调优参数

```toml
[agent]
  # 内存缓冲（按指标量调大）
  metric_buffer_limit = 100000

  # 采集抖动：错开各 input 的采集时刻，避免同时打系统
  collection_jitter = "3s"

  # 刷新间隔与抖动：配合 buffer 使用
  flush_interval = "10s"
  flush_jitter = "1s"

  # 监控自身性能
  debug = false
  logtarget = "file"
  logfile = "/var/log/telegraf/telegraf.log"
```

关键调优项：

- **`metric_batch_size`**：默认 1000，每批写出的条数。吞吐高时调大可减少写请求次数。
- **`metric_buffer_limit`**：默认 10000，每个 output 的内存缓冲区上限。高速采集场景（Kafka、物联网）建议调到 50000–100000。
- **`collection_jitter`**：错开**各 Input 插件**的采集时刻，避免多个插件同时读 sysfs 等造成瞬时负载。
- **`flush_jitter`**：错开**各 Output 插件**的写出时刻，避免写目标在某刻被打满——多实例部署时尤为关键。

### 监控自身健康状况

```toml
# 开启 Telegraf 自监控
[[inputs.internal]]
  collect_memstats = true

# 输出到 Prometheus（可被 Prometheus 抓取）
[[outputs.prometheus_client]]
  listen = ":9273"
```

Prometheus 抓取规则：
```yaml
- job_name: telegraf
  static_configs:
    - targets: ['telegraf:9273']
```

## 常见问题排查

### 问题 1：指标数据丢失

**症状**：InfluxDB 中数据不连续，存在丢点。

**排查步骤**：
```bash
# 1. 检查 Telegraf 日志
journalctl -u telegraf | grep -i "dropped\|buffer\|error"

# 2. 查看 dropped 指标
curl -s localhost:9273/metrics | grep telegraf_metrics_dropped

# 3. 调大缓冲 or 减少 batch_size 压力
[agent]
  metric_buffer_limit = 200000
```

### 问题 2：插件启动失败

**症状**：`Error: plugin inputs.xxx: not found`

**排查**：确认插件是否被打进二进制。
```bash
# 查看已启用插件列表
telegraf --test --config /dev/null 2>&1 | grep "inputs\."

# 特定插件测试
telegraf --test --config <(cat telegraf.conf) 2>&1
```

### 问题 3：Kafka Consumer 重复消费

**排查**：确认 consumer group 配置唯一。
```toml
[[inputs.kafka_consumer]]
  brokers = ["localhost:9092"]
  topics = ["metrics"]
  consumer_group = "telegraf-cluster-1"  # 集群内唯一
  offset = "oldest"
```

### 问题 4：时间戳偏差

**症状**：指标时间与实际时间偏差几分钟。

**原因**：`precision` 配置缺失或精度不匹配。
```toml
# 在 agent 或 output 中指定时间精度
[agent]
  precision = "ms"
```

## 插件开发：自定义 Input 实战

Telegraf 支持编写自定义插件。以下是一个最小 Input 插件示例：

```go
// plugins/inputs/example/example.go
package example

import (
	"github.com/influxdata/telegraf"
	"github.com/influxdata/telegraf/plugins/inputs"
)

type Example struct {
	URL string `toml:"url"`
}

func (e *Example) SampleConfig() string {
	return `url = "http://localhost:8080"`
}

func (e *Example) Gather(acc telegraf.Accumulator) error {
	acc.AddFields("example", map[string]interface{}{
		"value": 42,
	}, map[string]string{
		"url": e.URL,
	})
	return nil
}

func init() {
	inputs.Add("example", func() telegraf.Input {
		return &Example{URL: "http://localhost:8080"}
	})
}
```

编译进 Telegraf：
```bash
# 在 plugins/inputs/example/ 目录开发后
go build -o telegraf ./cmd/telegraf
```

## 何时用、何时不用

**适合 Telegraf 的场景：**

- 搭建 InfluxDB + Telegraf + Grafana 可观测性栈——Telegraf 对 InfluxDB 写入有原生优化，省掉中间层。
- 多源异构数据需要统一采集——系统指标、Docker、Kafka、MQTT、OPC UA 混在一起，不希望为每种源维护一套采集脚本。
- 需要插件式扩展——300+ 插件覆盖不了你的私有协议时，写一个 Go 插件嵌进去，比维护一套独立采集服务轻量得多。
- 时序数据需要在本地做聚合（去噪、降采样）再上报，不想到存储端再做开销较大的后期处理。

**不适合 Telegraf 的场景：**

- 纯日志采集——用 Vector 或 Fluentd，它们在日志解析和路由上更专业。
- 实时流处理——需要窗口 join、复杂 CEP 逻辑的，应该走 Kafka → Flink 这条线。
- 单机轻量监控——Prometheus node_exporter 更简单，不需要为它引入 InfluxDB 的额外依赖。

### 采用顺序建议

正在评估是否引入 Telegraf 的话，按这个顺序推进：

1. **先跑一个最小配置**：CPU + mem + disk → file output 到 stdout，5 分钟确认能采到指标。
2. **接到 InfluxDB**：把 output 从 file 换成 influxdb_v2，确认能写入、能在 Grafana 里查到。
3. **梯度接入数据源**：先接 Docker、MySQL、Kafka 这类常见源，再考虑 SNMP、Modbus、OPC UA 等工业协议。
4. **上 Processor 和 Aggregator**：等数据量上来以后再配，不要一开始就把所有阶段全开——先确认 Input→Output 通路稳定，再逐步加转换和聚合。
5. **部署高可用**：最后考虑多 Agent + 多后端节点架构。大部分场景下，单 Agent 足够撑到十万级指标/秒。

## 进阶路径

深入掌握 Telegraf 并在生产环境中熟练运用，建议按 5 步逐步深入：

### 步骤 1：入门实践
- 用 `--test` 模式跑通快速上手配置，观察 InfluxDB 行协议格式的输出
- 尝试修改 `interval` 和 `flush_interval`，观察对数据采集和写入的影响
- 通读 [Telegraf 官方文档](https://docs.influxdata.com/telegraf/)

### 步骤 2：应用部署
- 把 `outputs.file` 换成 `outputs.influxdb_v2`，接入真实 InfluxDB + Grafana
- 搭建第一块监控面板，可视化系统指标（CPU、内存、磁盘、网络）
- 使用 `telegraf --config test.conf --test` 调试配置

### 步骤 3：扩展插件
- 在现有配置里添加 `processors.converter` 做类型转换，观察字段变化
- 接入 Docker、MySQL、Kafka 等常见数据源，理解不同插件的配置要点
- 翻阅 [Telegraf 插件列表](https://docs.influxdata.com/telegraf/v1/plugins/)，了解可用插件生态

### 步骤 4：深入源码
- 阅读 [Telegraf 插件开发文档](https://github.com/influxdata/telegraf/blob/master/docs/developers/PLUGIN_DEV.md)
- 理解 `telegraf.Input` 接口和 `telegraf.Accumulator` 方法
- 给一个私有 HTTP API 编写自定义 Input 插件，编译进 Telegraf

### 步骤 5：生产运维
- 部署多 Agent + 多后端节点架构
- 掌握性能调优参数（`metric_batch_size`、`metric_buffer_limit`、`collection_jitter`、`flush_jitter`）
- 建立监控体系（Telegraf 自监控 + Prometheus 抓取 + 告警规则）

**参考资源**：
- [Telegraf 官方文档](https://docs.influxdata.com/telegraf/)
- [GitHub 仓库](https://github.com/influxdata/telegraf)
- [插件列表](https://docs.influxdata.com/telegraf/v1/plugins/)
- [InfluxDB 文档](https://docs.influxdata.com/influxdb/)