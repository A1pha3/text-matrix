---
title: "spdlog 深度拆解:29.6K stars 的 C++ header-only 日志库"
slug: gabime-spdlog-fast-cpp-logging-library-guide
github_repo: "gabime/spdlog"
source_key: "gh:gabime/spdlog"
date: 2026-07-12T02:58:14+08:00
lastmod: 2026-09-14T00:00:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["C++", "日志库", "性能优化", "Header-only"]
description: "spdlog 是 C++ 生态最流行的 header-only 日志库,29.6K stars。本文拆解它的 fmt 集成、异步模式、sinks 架构与适用场景,并给出可运行的示例代码。"
---

# spdlog 深度拆解:29.6K stars 的 C++ header-only 日志库

## 它解决什么问题

C++ 程序迟早要打日志,直接 `std::cout` 有几个绕不开的坑:多线程输出会乱序、没有级别区分、文件轮转要自己写、磁盘 I/O 会阻塞业务线程。spdlog 把这些事打包成一个 header-only 库,让日志从「麻烦事」变成「两行代码的事」。

spdlog 是 GitHub 上最流行的 C++ 日志库,约 29.6K stars(2026 年 9 月数据)。它的核心设计是 **logger 与 sink 分离**:logger 负责接收日志、决定格式和级别,一个或多个 sink 负责把日志写到具体目标(控制台、文件、syslog、网络)。想加一个输出目标,就为 logger 挂一个 sink,业务代码不用动。

## 项目速览

- 仓库: [gabime/spdlog](https://github.com/gabime/spdlog)
- 定位: Fast C++ logging library
- 语言: C++(C++11 起),header-only 与编译两种用法
- 当前版本: v1.17.0(2026-01 发布,捆绑 fmt 12.1.0,主要变更集中在 `%z` 时区偏移格式化的修复)
- License: MIT

## 四个角色,一张地图

看 spdlog 的任何机制,先把四个角色分清楚:

| 角色 | 职责 | 典型对象 |
|------|------|----------|
| logger | 接收调用、检查级别、持有名称 | `spdlog::info` 背后的默认 logger |
| sink | 把一条日志写到具体目标,各自有独立的级别和格式 | stdout、rotating file、syslog |
| pattern formatter | 定义一条日志长什么样 | `[%H:%M:%S] [%l] %v` |
| 线程池(异步模式) | 后台取出消息并写盘 | 全局共享,默认 8192 格队列 + 1 线程 |

下面按这条主线展开。

## 三个最值得注意的设计

### 1. Header-only,但也支持编译安装

spdlog 的实现都在 `.h` 头文件里,`#include <spdlog/spdlog.h>` 即可用,不需要链接 `.a` / `.so`。代价是每个包含它的翻译单元(translation unit)都要重新编译一遍实现,拖慢编译时间;收益是集成零成本,不用动构建系统。

两种取舍都支持:项目大、编译慢,就编译安装,把 spdlog 编成库链接进来(官方推荐,`spdlog::spdlog` 目标);项目小、想快速跑起来,直接拷贝 include 目录即可。

### 2. 格式化内建 fmt,类型安全

格式化用的是 fmt 库(默认捆绑,v1.17.0 内置 fmt 12.1.0,也可切换系统 fmt),语法类似 Python 的 `{}` 占位符,编译期检查类型,比 printf 安全:

```cpp
spdlog::info("Welcome to {}", "spdlog");
spdlog::error("Something went wrong: {}", error_msg);
spdlog::warn("Positional args: {0} {1} {0}", "foo", "bar");
```

项目统一用 C++20 时,可以定义 `SPDLOG_USE_STD_FORMAT` 把格式化后端从 fmt 切到标准库 `std::format`,日志 API 不变。

### 3. 异步模式:把日志挪出业务路径

同步模式下,业务线程直接调 sink 写文件/控制台,I/O 时间算进业务线程。异步模式把它拆成两段:业务线程只把日志消息丢进一个有界队列,后台线程池负责取出并写入。业务线程的日志调用从「磁盘 I/O」变成「一次入队」。要注意参数本身的格式化(`{}` 占位符展开)仍发生在业务线程,异步省掉的是 pattern 拼装和磁盘 I/O,不省参数展开。

官方推荐两种创建异步 logger 的方式:

```cpp
#include <spdlog/async.h>
#include <spdlog/sinks/basic_file_sink.h>

// 方式一:async_factory 模板参数
auto async_file = spdlog::basic_logger_mt<spdlog::async_factory>(
    "async_file", "logs/async.log");

// 方式二:create_async 指定 sink
auto async_file2 = spdlog::create_async<spdlog::sinks::basic_file_sink_mt>(
    "async_file2", "logs/async2.log");
```

spdlog 默认有一个全局线程池,队列 8192 格、1 个后台线程,所有异步 logger 共享它;因此创建异步 logger 很便宜——它不持有自己的线程或队列。要调整,必须在创建任何异步 logger 之前调用:

```cpp
spdlog::init_thread_pool(8192, 1);  // 队列 8192 格,1 个后台线程
```

#### 队列满了怎么办:两种溢出策略

队列固定大小,生产速度超过消费速度时会满。spdlog 只有两种处理策略(`spdlog::async_overflow_policy`):

- `block`(默认):队列满时业务线程阻塞等待,直到有空间。保证日志不丢,代价是极端峰值下业务被拖住。
- `overrun_oldest`:直接覆盖队列里最旧的消息,业务线程永不阻塞。性能最好,但会丢「最旧」的日志。

选哪种,取决于你更怕丢日志还是更怕延迟:对账、审计类日志用 `block`;海量且允许少量丢失的统计类日志用 `overrun_oldest`。想用后者又不显式传参,可以走 `spdlog::create_async_nb<Sink>(...)` 工厂。

异步还有一个代价:**进程崩溃(非正常退出)时,队列里还没写盘的日志会丢**。生产环境通常配合 `spdlog::flush_every` 定时刷盘:

```cpp
spdlog::flush_every(std::chrono::seconds(3));
```

## 日志是怎么流出去的:Logger → Sink

一条日志的生命周期:

```
业务线程 -> logger.log(level, fmt, args...)
            -> logger 检查级别阈值(不够直接返回)
            -> 把消息递给挂载的每个 sink(每个 sink 还有一道自己的级别检查)
                -> 每个 sink 用自己的 formatter 按 pattern 拼出最终文本
                    -> stdout_color_sink: 控制台输出
                    -> rotating_file_sink: 按大小轮转写文件
                    -> syslog_sink / tcp_sink: 系统日志 / 网络发送
```

格式化发生在 sink 内部,而不是 logger。`spdlog::set_pattern` 设的是 logger 级格式,内部会克隆给每个 sink;每个 sink 也可以单独 `set_pattern`——同一个 logger,控制台 sink 带颜色、文件 sink 用朴素格式,互不影响。

一个 logger 可以挂多个 sink,各自独立工作。典型做法是控制台 + 文件双输出:开发时看控制台,线上留文件:

```cpp
#include <spdlog/spdlog.h>
#include <spdlog/sinks/stdout_color_sinks.h>
#include <spdlog/sinks/rotating_file_sink.h>

auto console_sink = std::make_shared<spdlog::sinks::stdout_color_sink_mt>();
auto file_sink = std::make_shared<spdlog::sinks::rotating_file_sink_mt>(
    "logs/rotating.log", 1024 * 1024 * 5, 3);  // 单文件 5MB,最多保留 3 份

std::vector<spdlog::sink_ptr> sinks = {console_sink, file_sink};
auto logger = std::make_shared<spdlog::logger>("multi_sink", sinks.begin(), sinks.end());
spdlog::register_logger(logger);
```

常用内置 sink:

- `stdout_color_sink` / `stderr_color_sink`:控制台输出,带 ANSI 颜色
- `basic_file_sink`:追加写单个文件
- `rotating_file_sink`:按大小轮转
- `daily_file_sink` / `hourly_file_sink`:按时间轮转
- `syslog_sink` / `systemd_sink`:写系统 syslog / systemd journal
- `kafka_sink` / `mongo_sink`:直写 Kafka / MongoDB,用于集中式日志收集
- `tcp_sink` / `udp_sink`:网络发送
- `qt_sink` / `msvc_sink`:输出到 Qt 界面 / Visual Studio 输出窗口
- `ringbuffer_sink`:环形缓冲,保留最近 N 条,崩溃时提取现场
- `callback_sink`:每条日志回调你的函数,方便接自己的日志系统

## 日志格式:Pattern Formatter

格式由 pattern 控制,常用占位符:

| 占位符 | 含义 | 示例 |
|--------|------|------|
| `%Y-%m-%d %H:%M:%S` | 日期时间 | `2026-07-12 03:00:00` |
| `%e` | 毫秒 | `123` |
| `%l` | 级别(短名) | `info` |
| `%n` | logger 名称 | `async_file` |
| `%t` | 线程 ID | `140234` |
| `%v` | 消息正文 | `Server started` |
| `%^` / `%$` | 颜色作用范围标记 | — |

```cpp
spdlog::set_pattern("[%Y-%m-%d %H:%M:%S.%e] [%^%l%$] [%t] %v");
```

输出形如:`[2026-07-12 03:00:00.123] [info] [140234] Server started on port 8080`

## 日志级别与编译期裁剪

spdlog 有六个运行时级别:trace、debug、info、warn、err、critical,外加 off 表示关闭输出。运行时用 `set_level` 调阈值,影响所有级别检查。

`SPDLOG_*` 系列宏则由 `SPDLOG_ACTIVE_LEVEL` 在编译期决定去留,默认是 `info`,所以 `SPDLOG_TRACE`、`SPDLOG_DEBUG` 调用在 release 构建里被整体删除,连参数求值都不会发生:

```cpp
SPDLOG_TRACE("entering process()");   // 默认(ACTIVE_LEVEL=info)展开为空,不编译
SPDLOG_DEBUG("x = {}", x);            // 同上,不加编译选项这行等于没写
```

这比 `if (debug) log(...)` 干净:没有运行时分支,也没有样板代码。代价是没有运行时开关——想在 debug 构建里保留这些日志,只能重新编译,加 `-DSPDLOG_ACTIVE_LEVEL=SPDLOG_LEVEL_DEBUG` 即可。

另一个实用的特性是 **backtrace**:把最近 N 条消息缓存在环形缓冲里,出错时一次性打印「现场」,常用于 dump 错误发生前的上下文:

```cpp
spdlog::enable_backtrace(32);   // 记住最近 32 条
spdlog::dump_backtrace();       // 打印缓存内容
```

## 性能:快,但别信没有出处的数字

官方仓库的 `bench/` 目录提供可复现的基准,README 贴的是 Ubuntu 64 位、Intel i7-4770 @ 3.40GHz 上的结果:同步模式下 `basic_st` 单线程写文件约 5.8M 条/秒,`empty_logger`(丢弃输出、只剩级别检查与格式化)约 14.1M 条/秒。两个数的差距就是「测量对象」的差别:前者包含真实文件 I/O,后者把 I/O 摘掉了。看任何 spdlog 性能数字,先问三件事:什么 CPU?输出到哪——文件、终端还是空 sink?什么溢出策略?这三项不同,结论没有可比性。

还有一个常被误读的点:**异步模式不是「写得更快」,而是「返回得更快」**。它把 I/O 挪到后台线程,业务线程只付出入队成本;在 `overrun_oldest` 策略下,消费端吞吐通常比同步写盘高一截,但代价是可能丢弃日志。

需要自己对比时,直接跑 `bench/bench.cpp`,用同一份源码得出的数字才有讨论价值。

## 上手示例

安装(Ubuntu / macOS / Windows):

```bash
sudo apt-get install libspdlog-dev   # Debian/Ubuntu
brew install spdlog                  # macOS
vcpkg install spdlog                 # Windows / vcpkg
```

用 CMake 集成时,`find_package` 或 FetchContent 后链接 `spdlog::spdlog`:

```cmake
find_package(spdlog REQUIRED)
target_link_libraries(myapp PRIVATE spdlog::spdlog)
```

完整的最小程序:

```cpp
#include <spdlog/spdlog.h>
#include <spdlog/sinks/rotating_file_sink.h>

int main() {
    spdlog::set_level(spdlog::level::debug);
    spdlog::set_pattern("[%Y-%m-%d %H:%M:%S.%e] [%^%l%$] %v");

    spdlog::info("Welcome to spdlog!");
    spdlog::debug("A debug message with arg: {}", 42);

    // 按大小轮转的文件 logger:单文件 5MB,保留 3 份
    auto logger = spdlog::rotating_logger_mt(
        "rotating", "logs/rotating.log", 1024 * 1024 * 5, 3);
    logger->warn("Rotating logger ready");

    spdlog::shutdown();  // 刷新并清理所有 logger
    return 0;
}
```

## 适用边界

**适合**:

- 对延迟敏感、不想让日志拖慢主流程的 C++ 服务端与游戏服务器。
- 需要线程安全日志的多线程应用——`_mt`(multi-thread)后缀的 logger 和 sink 都是线程安全的。
- 想快速集成、不想为日志库改构建系统的项目。

**不适合**:

- 嵌入式等资源受限场景:header-only 拖慢编译,库本身也有开销。
- 已经在用 Qt、ROS 等自带日志体系的框架——重复造轮子。
- 只是偶尔打印几条调试信息:直接用 `std::cerr`,别引依赖。

## 常见问题

- **异步 logger 退出时丢日志?** 进程崩溃会丢队列里的日志;正常退出记得 `spdlog::shutdown()`,它会刷空队列。生产环境配合 `flush_every` 定期落盘。
- **release 构建里没有 debug 日志?** 默认 `SPDLOG_ACTIVE_LEVEL=info`,需要 debug 时编译期加 `-DSPDLOG_ACTIVE_LEVEL=SPDLOG_LEVEL_DEBUG`。
- **多线程写同一个文件乱序?** 用 `_mt` 变体,不要用 `_st`;异步 logger 只开一个后台线程时,出队顺序与入队一致。
- **和项目里的 fmt 版本冲突?** spdlog 默认捆绑自己的 fmt;项目已有 fmt 时,用 `SPDLOG_FMT_EXTERNAL` 切换到系统 fmt,避免符号冲突。

## 总结

spdlog 的价值不在某个炫目的数字,而在四个同时满足的特性:header-only 好集成、fmt 类型安全格式化、多 sink 灵活输出、异步模式把日志挪出业务路径。落地顺序可以很简单:先用同步的默认 logger 跑起来,行为稳定后再把 I/O 最重的路径换成异步 logger,最后按需调整 pattern 和轮转策略;已经在 Qt、ROS 体系里的项目,用自带日志就够了。29.6K 个 star 反映的正是这种低门槛——不需要先读完整个库,两行代码就能开始打日志。

## 参考

- GitHub 仓库: <https://github.com/gabime/spdlog>
- Wiki(异步、sink、自定义格式): <https://github.com/gabime/spdlog/wiki>
- 官方基准与示例: <https://github.com/gabime/spdlog/blob/v1.x/README.md>
- 异步用法与溢出策略: <https://github.com/gabime/spdlog/wiki/Asynchronous-logging>
