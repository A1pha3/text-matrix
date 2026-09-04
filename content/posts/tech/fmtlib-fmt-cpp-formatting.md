---
title: "fmt：C++ 格式化的事实标准库"
date: 2026-09-05T03:40:00+08:00
slug: "fmtlib-fmt-cpp-formatting"
github_repo: "fmtlib/fmt"
source_key: "gh:fmtlib/fmt"
description: "fmt（{fmt}）是 C++ 最广泛使用的开源格式化库，快速、安全、可扩展，是 C++20 std::format 与 C++23 std::print 的参考实现。本文讲解其核心 API、编译期格式串检查、性能与代码膨胀数据，以及为什么它比 iostreams 和 printf 都更值得选。"
draft: false
categories: ["技术笔记"]
tags: ["C++", "格式化", "开源库", "性能"]
---

## 核心判断

如果你在写 C++ 且还在用 `printf` 或 `iostreams` 做字符串格式化，{fmt} 是最直接的升级路径。它比两者都快（数值格式化场景比 iostreams 快 20–30 倍），完全类型安全，格式串错误在**编译期**报错，最小配置只需三个头文件。更重要的是它的行业地位：C++20 标准库的 `std::format` 和 C++23 的 `std::print` 就是以它为蓝本制定的——学 {fmt} 等于提前用上了下一代标准库，还附带标准库没有的颜色输出、编译期格式串编译（FMT_COMPILE）等能力。

截至本文写作时，仓库 25.4k stars，MIT 许可，无外部依赖。用户名单足以说明其生产成熟度：PyTorch、ClickHouse、MongoDB、FoundationDB、Windows Terminal、spdlog、Envoy、Folly、Ceph、MariaDB、Blizzard Battle.net。

## 为什么不用 printf / iostreams

三个老方案的痛点 {fmt} 逐一解决：

| 方案 | 问题 | {fmt} 的答案 |
|------|------|--------------|
| printf | 无类型安全（格式符与实参不匹配是 UB），缓冲区溢出风险 | 完全类型安全，自动内存管理 |
| iostreams | 慢（比 printf 慢一个量级的场景常见）、代码膨胀、语法冗长 | 数值格式化快 20–30 倍，编译产物与 printf 相当 |
| to_string / to_chars | 只处理单一类型转字符串 | 统一格式语法，支持用户自定义类型 |

一个直观的对比数据（README 引用 format-benchmark，Apple M5 Max / Apple Clang 21，-O3，100 个翻译单元各调用 5 次）：printf 编译 1.2s、产物 54 KiB；iostreams 编译 21.8s、98 KiB；{fmt} 12.2 编译 4.2s、54 KiB；Boost Format 1.88 编译 43.4s、550 KiB。{fmt} 的编译速度和二进制尺寸都与 printf 打平，同时保留了完整的类型安全和现代语法。

## 格式语法：Python 风格

核心语法接近 Python 的 `str.format`：

```cpp
#include <fmt/base.h>

int main() {
  fmt::print("Hello, world!\n");
}
```

```cpp
std::string s = fmt::format("The answer is {}.", 42);
// s == "The answer is 42."

// 位置参数（本地化场景）
std::string s = fmt::format("I'd rather be {1} than {0}.", "right", "happy");
// s == "I'd rather be happy than right."
```

## 编译期检查：错误在 build 时暴露

```cpp
std::string s = fmt::format("{:d}", "I am not a number");
```

这一行在 C++20 下直接**编译失败**——`d` 对字符串是非法格式符。对比 printf 的同类错误（`%d` 传字符串）要到运行时才崩，这是安全模型上的代差。

## 常用能力速览

**日期时间**（`fmt/chrono.h`）：

```cpp
auto now = std::chrono::system_clock::now();
fmt::print("Time: {:%H:%M}\n", now);
```

**容器直接打印**（`fmt/ranges.h`）：

```cpp
std::vector<int> v = {1, 2, 3};
fmt::print("{}\n", v);  // [1, 2, 3]
```

**彩色与文本样式**（`fmt/color.h`）：

```cpp
fmt::print(fg(fmt::color::crimson) | fmt::emphasis::bold,
           "Hello, {}!\n", "world");
```

**单线程写文件**（`fmt/os.h`）：`fmt::output_file("guide.txt")` 返回的 writer 比多次调用 `fprintf` 快最多 9 倍（官方 benchmark 数据，来自缓冲区尺寸优化）。

**用户自定义类型**：为自己的类型实现 `formatter` 特化即可接入全部格式语法——这是 printf 家族做不到的扩展点。

## 浮点：Dragonbox 算法

浮点转字符串是格式化库的硬骨头。{fmt} 使用 Dragonbox 算法，同时保证**正确舍入、最短表示、往返一致**（round-trip：打出来再解析回去得到同一个 double）。这是它比 sprintf 系实现快一个量级的核心来源之一，benchmark 见仓库 dtoa-benchmark。

## 集成方式

- CMake FetchContent / find_package(fmt) 常规接入
- 最小配置：只拷 `base.h`、`format.h`、`format-inl.h` 三个文件
- 定义 `FMT_HEADER_ONLY` 宏启用 header-only 模式
- 无外部依赖，MIT 许可；`-Wall -Wextra -pedantic` 下无警告
- 持续 fuzz：接入 oss-fuzz 长期模糊测试，OpenSSF Best Practices 认证通过

## 与 std::format 的关系

`std::format`（C++20）与 `std::print`（C++23）以 {fmt} 为参考实现进入标准。如果你的工具链已支持，标准库版本可以满足基本需求；{fmt} 的增量价值在于：更早的编译器支持（{fmt} 兼容老编译器）、FMT_COMPILE 编译期格式化、颜色/样式、ranges、chrono 扩展，以及在新标准落地前的过渡期。官方提供 Compiler Explorer 在线体验与 fmt.dev 完整文档。

## 适用边界

{fmt} 不解决本地化格式（默认 locale 无关，本地化通过位置参数支持）；极少数需要与既有 printf 格式串完全兼容的场景可以用它的安全 printf 实现（含 POSIX 位置参数扩展），但新代码不建议再写 printf 风格。

仓库地址：[fmtlib/fmt](https://github.com/fmtlib/fmt)，文档：[fmt.dev](https://fmt.dev)
