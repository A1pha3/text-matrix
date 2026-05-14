---
title: "Telegraf：300+插件的指标采集Agent完全指南"
date: "2026-05-14T10:49:00+08:00"
slug: "telegraf-metrics-collection-agent-guide"
description: "Telegraf是InfluxData开源的指标采集Agent，支持300+插件，覆盖系统监控、云服务、消息队列、数据库、日志采集等场景。Go语言开发，单一静态二进制无需外部依赖，TOML配置。适用DevOps监控、物联网数据采集、云原生指标收集等场景。本文详解其架构、插件系统与典型配置。"
draft: false
categories: ["技术笔记"]
tags: ["监控", "指标采集", "Go", "DevOps", "InfluxDB"]
---

# Telegraf：300+插件的指标采集Agent完全指南

**Telegraf** 是 InfluxData 推出的开源指标采集 Agent，使用 Go 语言开发，编译为单一静态二进制文件，无需外部运行时依赖。它通过**插件驱动**的架构，支持超过 300 种数据采集方式，涵盖系统监控、云服务、消息队列、数据库、日志等各类场景，是 InfluxDB 时序数据库生态的核心组件。

## 为什么选择 Telegraf

- **300+ 官方插件**：覆盖主流操作系统、云服务、数据库、消息队列
- **零外部依赖**：编译为静态二进制，容器化部署极简
- **TOML 配置**：声明式配置，读写门槛低
- **1,200+ 贡献者**：社区活跃，插件持续增加
- **任意数据输出**：不仅支持 InfluxDB，也支持 Kafka、Prometheus、File 等多种 Output

## 架构概览

```
Telegraf Agent
┌──────────────────────────────────────────┐
│  Input Plugins      │  Processor Plugins │  Output Plugins
│  ─────────────     │  ────────────────  │  ──────────────
│  cpu, memory       │  regex, converter  │  influxdb
│  prometheus       │  pivot, rename     │  kafka
│  mysql, postgres  │  aws, json         │  prometheus
│  http_listener   │  override         │  file
│  exec            │  ...              │  ...
└──────────────────────────────────────────┘
```

数据流向：**Input → Processor → Output**，每个阶段均由插件驱动。

## 安装

### 二进制

```bash
# 下载对应平台压缩包
curl -LO https://dl.influxdata.com/telegraf/releases/telegraf-1.30.0_linux_amd64.tar.gz
tar xf telegraf-1.30.0_linux_amd64.tar.gz
cd telegraf-1.30.0_linux_amd64
```

### Docker

```bash
docker pull telegraf:latest

# 运行（挂载配置文件）
docker run --rm \
  -v /path/to/telegraf.conf:/etc/telegraf/telegraf.conf \
  -v /var/run:/var/run \
  telegraf telegraf \
  --config /etc/telegraf/telegraf.conf
```

### apt/yum

```bash
# Ubuntu/Debian
sudo apt install telegraf

# RHEL/CentOS
sudo yum install telegraf
```

## 配置：最小示例

```toml
# telegraf.conf

# 全局配置
[agent]
  interval = "10s"
  round_interval = true
  hostname = "my-server"

# 输入：CPU 与内存
[[inputs.cpu]]
  percpu = true
  totalcpu = true

[[inputs.mem]]
  # 无额外配置，使用默认参数

# 输出：InfluxDB
[[outputs.influxdb]]
  urls = ["http://localhost:8086"]
  database = "telegraf"
  username = "telegraf"
  password = "your-password"
```

运行：

```bash
telegraf --config telegraf.conf
```

## 常用插件配置示例

### HTTP Listener（接收外部数据）

```toml
[[inputs.http_listener]]
  service_address = ":8080"
  paths = ["/telegraf"]
  data_format = "influx"
```

推送数据：

```bash
curl -XPOST http://localhost:8080/telegraf \
  -d 'cpu_load,host=server01 region=us-east 0.64'
```

### MySQL

```toml
[[inputs.mysql]]
  servers = ["root:password@tcp(localhost:3306)/"]
  metrics = ["status", "variables"]
```

### Prometheus 端点

```toml
[[inputs.prometheus]]
  urls = ["http://localhost:9100/metrics"]
```

### Exec（自定义脚本）

```toml
[[inputs.exec]]
  commands = ["/opt/scripts/get-temp.sh"]
  interval = "30s"
  data_format = "influx"
  name_override = "temperature"
```

### 日志文件监控

```toml
[[inputs.logparser]]
  files = ["/var/log/syslog"]
  [inputs.logparser.grok]
    patterns = ["%{SYSLOGTIMESTAMP:timestamp} %{HOSTNAME:host} %{SYSLOGPROG}: %{GREEDYDATA:message}"]
```

## Processor 插件：数据转换

```toml
# 添加标签
[[processors.rename]]
  [[processors.rename.tag]]
    dest = "env"
    source = "hostname"

# 正则替换
[[processors.regex]]
  [[processors.regex.tags]]
    key = "host"
    pattern = "^web(\\d+)"
    replacement = "server_${1}"

# 数据类型转换
[[processors.converter]]
  [processors.converter.fields]
    integer = ["count"]
    float = ["temperature"]
```

## 输出插件

```toml
# InfluxDB（默认）
[[outputs.influxdb]]
  urls = ["http://localhost:8086"]

# Kafka
[[outputs.kafka]]
  brokers = ["localhost:9092"]
  topic = "telegraf"
  data_format = "json"

# Prometheus Remote Write
[[outputs.prometheus_client]]
  listen = ":9273"
```

## Docker 监控完整配置

```toml
[agent]
  interval = "15s"

[[inputs.docker]]
  endpoint = "unix:///var/run/docker.sock"
  container_names = []  # 监控所有容器

[[inputs.kernel]]
[[inputs.mem]]
[[inputs.cpu]]
[[inputs.disk]]
[[inputs.diskio]]

[[outputs.influxdb]]
  urls = ["http://influxdb:8086"]
  database = "docker_metrics"
```

## 生产环境注意事项

- **配置校验**：`telegraf --config --test` 先测试配置再部署
- **输出缓冲**：启用 `flush_buffer` 避免因 Output 不可用导致数据丢失
- **日志级别**：`--logfile` 指定日志路径，生产环境建议 `error` 级别
- **资源限制**：容器运行时建议加 CPU 和内存限制

## 总结

Telegraf 凭借其**插件生态的广度**与**运维的简便性**，已经成为指标采集领域的事实标准。无论是监控一台服务器还是整个云基础设施，它都能提供开箱即用的解法。配合 InfluxDB 与 Grafana，可以快速搭建一套完整的可观测性平台。

官网：[https://www.influxdata.com/projects/telegraf/](https://www.influxdata.com/projects/telegraf/)