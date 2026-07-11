---
title: "spdlog 深度拆解:29K stars 的 C++ header-only 日志库如何做到 30M msg/sec"
slug: gabime-spdlog-fast-cpp-logging-library-guide
date: 2026-07-12T02:58:14+08:00
lastmod: 2026-07-12T02:58:14+08:00
draft: false
categories: ["技术笔记"]
tags: ["spdlog", "cpp", "logging", "header-only", "fmt", "performance"]
description: "spdlog 是 C++ 最快的 header-only 日志库之一,29K+ stars。本文拆解 spdlog 的 fmt 集成、异步模式、sinks 架构、性能基准与适用场景。"
---

# spdlog 深度拆解:29K stars 的 C++ header-only 日志库如何做到 30M msg/sec

## 核心判断

spdlog 是 C++ 生态的事实标准日志库,29K+ stars 来自一个清晰的定位:**Header-only、零依赖(可选 fmt)、纳秒级延迟**。在游戏服务器、高频交易、低延迟系统等场景下,日志库的写入速度直接决定吞吐量——spdlog 通过异步模式 + 预格式化 + 内存池,把日志写入从「阻塞业务」变成「旁路观测」。

## 项目速览

- 仓库: [gabime/spdlog](https://github.com/gabime/spdlog)
- Stars / 语言: 29K+ / C++ (header-only)
- 主页: <https://github.com/gabime/spdlog>
- 定位: Fast C++ logging library
- License: MIT

## 为什么值得看

C++ 日志库有很多选择,但 spdlog 的优势是「**简单到极致**」——单一头文件,无需编译,集成时间从小时降到分钟。29K+ stars 来自 C++ 社区对「**OpenCV / gRPC / TensorFlow 等大型 C++ 项目都依赖 spdlog**」的认可——它是产业级默认选项,不是玩具库。

## 系统地图

```
┌──────────────────────────────────────────────────────────┐
│                    User API                              │
│  spdlog::info("Hello {}!", name)                         │
│  spdlog::warn("Failed to connect to {}", host)           │
├──────────────────────────────────────────────────────────┤
│                    Logger                                │
│  - level (trace/debug/info/warn/error/critical)          │
│  - pattern formatter (%Y-%m-%d %H:%M:%S.%e [%l] %v)     │
│  - sinks[] (multiple output targets)                     │
├──────────────────────────────────────────────────────────┤
│                    Sinks                                 │
│  - stdout_color_sink   - daily_file_sink                 │
│  - rotating_file_sink  - syslog_sink                     │
│  - tcp_sink            - ostream_sink                    │
├──────────────────────────────────────────────────────────┤
│              Async mode (optional)                       │
│  - thread_pool + mpsc_queue                              │
│  - blocking vs non-blocking vs overrun                   │
└──────────────────────────────────────────────────────────┘
```

## 关键机制

### 1. Header-only + fmt 集成

spdlog 把所有实现放在 `.h` 头文件里(`#include <spdlog/spdlog.h>`),无需编译 `.a` / `.so`。代价是**编译时间增加**(每个 translation unit 都要 include 整个实现),收益是**集成简单**(无需修改 CMakeLists.txt,无需链接库)。

格式化使用 [fmt](https://github.com/fmtlib/fmt) 库(也是 C++ 主流的字符串格式化库),语法类似 Python:

```cpp
spdlog::info("Welcome to {}", "spdlog");
spdlog::error("Something went wrong: {}", error_msg);
spdlog::warn("Positional args: {0} {1} {0}", "foo", "bar");
```

可选使用 printf 风格:`spdlog::info("printf style %d %s", 42, "hello")`。

### 2. 异步模式(Async Mode)

spdlog 的核心性能优势。**同步模式**下,业务线程直接写日志(到文件 / 控制台),I/O 阻塞业务;**异步模式**下,业务线程只把日志消息 push 到内存队列,**后台线程池负责实际写入**。

```cpp
#include <spdlog/async.h>
#include <spdlog/sinks/stdout_color_sinks.h>

auto async_logger = spdlog::create_async<spdlog::sinks::stdout_color_sink_mt>(
    "async_logger",
    8192,    // queue size
    spdlog::async_overflow_policy::block  // 队列满时阻塞业务线程
);
spdlog::set_default_logger(async_logger);
```

三种溢出策略:

- `block`:队列满时业务线程等待(保证日志不丢,但阻塞业务)
- `overrun_oldest`:丢弃最老的消息(最新日志优先)
- `discard`:直接丢弃新消息(性能最高,但可能丢日志)

异步模式的代价:**进程崩溃时队列里的日志丢失**——所以生产环境通常结合 `flush_every` 定时强制刷盘。

### 3. Sinks:多目标输出

一个 logger 可以挂多个 sink,每个 sink 独立处理:

```cpp
auto console_sink = std::make_shared<spdlog::sinks::stdout_color_sink_mt>();
auto file_sink = std::make_shared<spdlog::sinks::basic_file_sink_mt>("logs/app.log");
auto rotating_sink = std::make_shared<spdlog::sinks::rotating_file_sink_mt>(
    "logs/rotating.log", 1024 * 1024 * 5, 3  // 5MB × 3 files
);

std::vector<spdlog::sink_ptr> sinks = {console_sink, file_sink, rotating_sink};
auto logger = std::make_shared<spdlog::logger>("multi_sink", sinks.begin(), sinks.end());
```

常用 sink:

- **stdout_color_sink**:控制台带 ANSI 颜色
- **basic_file_sink**:简单文件输出
- **rotating_file_sink**:按大小轮转(5MB × 3 个文件)
- **daily_file_sink**:按天轮转(每天一个文件)
- **syslog_sink**:系统 syslog
- **tcp_sink**:网络发送(集中式日志收集)

### 4. Pattern Formatter

日志格式可自定义,常用占位符:

- `%Y`:年(2026)
- `%m`:月(07)
- `%d`:日(12)
- `%H:%M:%S`:时分秒
- `%e`:毫秒
- `%l`:日志级别
- `%v`:消息内容
- `%t`:线程 ID
- `%n`:logger 名称

```cpp
spdlog::set_pattern("[%Y-%m-%d %H:%M:%S.%e] [%l] [%t] %v");
```

输出:`[2026-07-12 03:00:00.123] [info] [thread-1] Server started on port 8080`

### 5. Conditional Logging

条件日志在 release 构建中完全跳过:

```cpp
SPDLOG_TRACE("This won't be logged in release");  // 默认级别 info,trace 被跳过
SPDLOG_DEBUG_IF(debug_mode, "Verbose: {}", x);
```

这避免了 `if (debug) log()` 的样板代码,debug 构建中详细日志,release 构建零开销。

## 性能基准

spdlog 官方 benchmark(同步模式,单线程):

| 实现 | 速度 |
|------|------|
| spdlog (fmt) | ~30M msg/sec |
| spdlog (printf) | ~12M msg/sec |
| glog | ~8M msg/sec |
| Boost.Log | ~3M msg/sec |

异步模式可达到 **80M+ msg/sec**(几乎不受 I/O 限制)。

## 适用边界

**适合 spdlog 的场景**:

- C++ 服务端、游戏服务器、高频交易等**对延迟敏感**的系统。
- 需要**快速集成**(不想为了日志库改 build system)的项目。
- 多线程 C++ 应用,需要线程安全的日志。

**不适合 spdlog 的场景**:

- 嵌入式系统(资源受限,header-only 编译时间长)。
- 已经使用 ROS / Qt 生态——这些框架有自己的日志系统。
- 不需要纳秒级延迟的脚本工具——直接用 `std::cerr` 更简单。

## 上手示例

```bash
# 安装(Ubuntu)
apt-get install libspdlog-dev

# 或 Homebrew(macOS)
brew install spdlog

# 或 vcpkg / conan
vcpkg install spdlog
```

```cpp
#include <spdlog/spdlog.h>

int main() {
    spdlog::info("Welcome to spdlog!");
    spdlog::error("Some error message with arg: {}", 42);
    
    // 设置全局日志级别
    spdlog::set_level(spdlog::level::debug);
    
    // 异步 logger
    spdlog::init_thread_pool(8192, 1);  // queue 8192, 1 worker thread
    auto async_logger = spdlog::create_async<spdlog::sinks::basic_file_sink_mt>(
        "async_logger", "logs/async.log"
    );
    async_logger->info("Async message");
    
    spdlog::drop_all();  // 清理
    return 0;
}
```

## 总结

spdlog 的真正价值不是「更快的日志」,而是「**把日志变成 C++ 的零成本工具**」——29K+ stars 来自 C++ 社区对「无编译依赖、纳秒级延迟、多 sink、可异步」这四个特性的同时满足。如果你用 C++ 写服务端且尚未选日志库,spdlog 是默认选项。

## 参考

- GitHub: <https://github.com/gabime/spdlog>
- 文档: <https://github.com/gabime/spdlog/wiki>
- 基准测试: <https://github.com/gabime/spdlog#benchmarks>