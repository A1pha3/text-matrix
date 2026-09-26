---
title: "fmt：C++ 格式化的事实标准库"
date: 2026-09-05T03:40:00+08:00
slug: "fmtlib-fmt-cpp-formatting"
github_repo: "fmtlib/fmt"
source_key: "gh:fmtlib/fmt"
description: "fmt（{fmt}）是 C++ 最广泛使用的开源格式化库，快速、安全、可扩展，是 C++20 std::format 与 C++23 std::print 的蓝本。本文讲解其格式语法与格式规格、编译期格式串检查、运行时格式串、一次格式化调用的完整路径、编译时间与代码膨胀数据，以及为什么它比 iostreams 和 printf 都更值得选。"
draft: false
categories: ["技术笔记"]
tags: ["C++", "格式化", "开源库", "性能"]
---

## 核心判断

如果你在写 C++ 且还在用 `printf` 或 `iostreams` 做字符串格式化，{fmt} 是最直接的升级路径。README 的性能口径：比常见标准库实现的 `sprintf`、iostreams、`to_string`、`to_chars` 快百分之几十到 20–30 倍，数值格式化差距最大。它完全类型安全，字面量格式串的错误在**编译期**就报出来，源码最小配置只有三个文件。行业地位更是明摆着：C++20 的 `std::format` 和 C++23 的 `std::print` 以它为蓝本制定（提案作者就是 {fmt} 作者 Victor Zverovich），{fmt} 自己也提供这两个标准 API 的实现——学 {fmt} 等于提前用上下一代标准库，还附带标准库没有的颜色输出、编译期格式串编译（FMT_COMPILE）等能力。

截至本文写作时，仓库约 25.8k stars，MIT 许可，无外部依赖。用户名单足以说明其生产成熟度：PyTorch、ClickHouse、MongoDB、FoundationDB、Windows Terminal、spdlog、Envoy、Folly、Ceph、MariaDB、Blizzard Battle.net。

## 为什么不用 printf / iostreams

三个老方案的痛点 {fmt} 逐一解决：

| 方案 | 问题 | {fmt} 的答案 |
|------|------|--------------|
| printf | 无类型安全（格式符与实参不匹配是 UB），缓冲区溢出风险 | 完全类型安全，自动内存管理 |
| iostreams | 慢（比 printf 慢一个量级的场景常见）、代码膨胀、语法冗长 | 数值格式化快 20–30 倍，二进制尺寸与 printf 持平 |
| to_string / to_chars | 只处理单一类型转字符串 | 统一格式语法，支持用户自定义类型 |

编译成本是最常被拿来反对换库的理由，README 引用 format-benchmark 的 bloat-test.py 给了反证：生成 100 个翻译单元、每个各调用 5 次格式化，模拟中型工程；Apple M5 Max（macOS 26.6.2，Apple Clang 21.0.0），`-O3`，取三次运行最优，库自身构建成本不计、以共享库链接。结果（版本 12.2）：

| 方法 | 编译时间 (s) | 二进制 (KiB) | strip 后 (KiB) |
|------|-------------:|-------------:|---------------:|
| printf | 1.6 | 54 | 50 |
| IOStreams | 25.5 | 98 | 84 |
| fmt（头文件） | 5.1 | 54 | 50 |
| fmt（C++20 模块） | 3.7 | 59 | 50 |
| Boost Format 1.92 | 49.1 | 517 | 317 |

怎么读这张表：它测的是**编译时间与产物体积**，反映的是每次格式化调用摊到头文件解析和模板实例化上的开销，不是运行时速度——运行时数据要看 format-benchmark 和 dtoa-benchmark（浮点转字符串 {fmt} 领先更多，见后文）。从这张表推不出"编译也一定慢不了"的反面结论，头文件版 5.1 秒仍是 printf 的三倍，只是量级上远好于 iostreams 与 Boost Format。若工具链支持 C++20 模块，`fmt::fmt-module` 目标能把应用代码编译时间再降 27%。

## 格式语法：Python 风格

核心语法接近 Python 的 `str.format`：

```cpp
#include <fmt/core.h>

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

花括号本身是字面量时用双写转义：`fmt::format("{{{}}}", 42)` 输出 `{42}`。命名参数按名字引用，适合格式串和实参分离的写法：

```cpp
std::string s = fmt::format("{name} was born in {year}.",
                            fmt::arg("name", "Ada"), fmt::arg("year", 1815));
// s == "Ada was born in 1815."
```

## 格式规格：冒号后面才是真正的表达能力

`{...}` 内冒号后的部分称为格式规格，控制对齐、宽度、精度与进制。常用组合不多，一张表够用：

| 写法 | 含义 | 示例输出 |
|------|------|----------|
| `{:<10}` | 左对齐，宽度 10 | `"abc       "` |
| `{:>10}` | 右对齐（数字默认） | `"       abc"` |
| `{:^10}` | 居中 | `"   abc    "` |
| `{:.2f}` | 浮点保留 2 位小数 | `"3.14"` |
| `{:08d}` | 数字零填充到 8 位 | `"00000042"` |
| `{:x}` / `{:X}` | 十六进制（小写/大写） | `"2a"` / `"2A"` |
| `{:b}` | 二进制 | `"101010"` |
| `{:.2e}` | 科学计数法 | `"3.14e+00"` |
| `{:?}` | 字符串调试格式（加引号、转义） | `"\"hi\""` |

宽度可以用嵌套参数动态指定：`fmt::format("{:{}}", "abc", 10)`。零填充只对数值生效，遇到显式对齐符会被忽略。字符串默认左对齐、数字默认右对齐，这是最容易记错的一点。

## 一条格式化调用的完整路径

拿 `fmt::format("{:>8.2f} | {:08d}", 3.14159, 42)` 过一遍这个库的工作方式：

1. **编译期**：字面量格式串进入 consteval 检查——两个实参对两个占位符，`>8.2f` 合法于 double、`08d` 合法于 int，检查通过。若把实参换成字符串，检查在这里就失败，产物根本不会生成。
2. **运行时**：已通过检查的格式串以解析好的形式落地，逐个参数找到对应的 `formatter` 特化——double 走 Dragonbox 最短表示，int 走专用整数转换——直接写入内部内存缓冲，最后一次性构造出 `std::string`，没有逐字符的流操作。
3. **扩展点**：自定义类型只需提供 `formatter` 特化，这条路径从检查到缓冲复用的整套机制原样可用。

后面几节把这条路径上各环节单独展开。

## 编译期检查：错误在 build 时暴露

```cpp
std::string s = fmt::format("{:d}", "I am not a number");
```

这一行在 C++20 下直接**编译失败**——`d` 对字符串是非法格式符，编译器报 consteval 调用非常量表达式，错误信息会直接指向 `invalid format specifier`。对比 printf 的同类错误（`%d` 传字符串）要到运行时才崩，这是安全模型上的代差。

## 运行时格式串：显式标记，不默认放开

编译期检查的前提是格式串是字面量。当格式串来自运行时（配置项、用户输入、从别处读来的字符串），需要显式声明放弃编译期检查：

```cpp
std::string s = fmt::format(fmt::runtime(fmt_string), 42);
```

这个设计的取向与 printf 相反：{fmt} 不默认把任意字符串当格式串，而是要求你用 `fmt::runtime` 包装来"主动选择"运行时解析。效果是——误把变量当格式串传给 `fmt::format` 会直接编译失败，而不是留到运行期出错；反过来，真正需要动态格式串的代码点变得可检索。格式串本身的错误（如宽度非法、参数类型不匹配）在运行时抛 `fmt::format_error`，可捕获处理。

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

**写入已有缓冲区**（`fmt/format.h` 的 `fmt::format_to` / `fmt::format_to_n`）：不想产生中间 `std::string`、想复用栈上缓冲时用它。`format_to` 返回写入末尾的迭代器；固定大小数组用 `format_to_n`，带容量参数，避免溢出：

```cpp
char buf[64];
auto result = fmt::format_to_n(buf, sizeof(buf), "{} + {} = {}", 1, 2, 3);
std::string_view sv(buf, result.size);
// sv == "1 + 2 = 3"
```

注意 `result.size` 的语义是"缓冲区足够大时的总输出长度"，可能大于实际写入数——输出被截断时按它取视图会越界，稳妥的判断是先确认 `result.size < sizeof(buf)`。

**单线程写文件**（`fmt/os.h`）：`fmt::output_file("guide.txt")` 返回的 writer 比多次调用 `fprintf` 快最多 9 倍（官方数据，来自缓冲区尺寸优化的测算）。

**用户自定义类型**：为自己的类型实现 `formatter` 特化即可接入全部格式语法——这是 printf 家族做不到的扩展点。

## 浮点：Dragonbox 算法

浮点转字符串是格式化库的硬骨头。{fmt} 使用 Dragonbox 算法，同时保证**正确舍入、最短表示、往返一致**（round-trip：打出来再解析回去得到同一个 double）。这是它比 sprintf 系实现快一个量级的核心来源之一，benchmark 见仓库 dtoa-benchmark。

## 集成方式

- CMake FetchContent / find_package(fmt) 常规接入；C++20 模块用 `fmt::fmt-module` 目标
- Header-only：定义 `FMT_HEADER_ONLY` 宏；不启用时需要把 `format.cc` 一起编进目标
- 最小源码配置：只拷 `core.h`、`format.h`、`format-inl.h` 三个文件（v12 中 `base.h` 是指向 `core.h` 的兼容垫片，新代码用 `core.h`）
- 无外部依赖，MIT 许可；`-Wall -Wextra -pedantic` 下无警告
- 持续接入 OSS-Fuzz 长期模糊测试（README 明确声明），安全性有外部验证

## 验证步骤：十分钟跑通

想亲手确认"编译期报错"和编译成本数据，不需要搭工程。最快路径：打开 README 里的 [Compiler Explorer 链接](https://godbolt.org/z/8Mx1EW73v)，`fmt::format("{:d}", "x")` 直接看编译失败；把 `{:d}` 换成 `{}` 即可通过。本地验证用一组命令（`<fmt>` 换成你的源码目录，`git clone --depth 1 https://github.com/fmtlib/fmt` 或 release 包解压均可）：

```bash
mkdir -p demo/fmt && cd demo
cp <fmt>/include/fmt/core.h <fmt>/include/fmt/format.h <fmt>/include/fmt/format-inl.h fmt/
cat > main.cpp <<'EOF'
#include <fmt/format.h>
#include <cstdio>
int main() {
  std::string s = fmt::format("{:>8.2f} | {:08d}", 3.14159, 42);
  std::puts(s.c_str());
}
EOF
g++ -std=c++20 -DFMT_HEADER_ONLY -I. main.cpp && ./a.out
```

输出 `    3.14 | 00000042`。三文件加 `FMT_HEADER_ONLY` 是最小可编译组合，编译期检查也在这条命令上生效：把格式串改成 `"{:d}"` 传字符串，同样的命令会直接报错退出。

## 与 std::format 的关系

`std::format`（C++20）与 `std::print`（C++23）以 {fmt} 为蓝本进入标准，{fmt} 自身也实现了这两个 API。如果你的工具链已支持，标准库版本可以满足基本需求；{fmt} 的增量价值在于：兼容老编译器、FMT_COMPILE 编译期格式化、颜色/文本样式（标准库至今没有对应 API）、直接写文件的 `fmt/os.h`，以及编译器跟进新标准之前的过渡期。官方提供 Compiler Explorer 在线体验与 fmt.dev 完整文档。

## 适用边界

{fmt} 默认与 locale 无关，同样的代码跨平台输出一致；需要千分位等本地化数字格式时用 `{:L}`（按当前 locale 插入分隔符）；把句子翻译成不同语言带来的语序差异，用位置参数重排解决。极少数需要与既有 printf 格式串完全兼容的场景，可以用 `fmt/printf.h` 的安全 printf 实现（含 POSIX 位置参数扩展），但新代码不建议再写 printf 风格。

## 常见问题

**编译不过，报 `fmt::format_error` 相关错误？** 先查格式串与实参是否匹配：数量、类型、进制/精度符号是否合法。字面量格式串的问题在编译期就暴露，运行时抛 `fmt::format_error` 的多是 `fmt::runtime` 包装的动态串。

**中文/Unicode 输出乱码？** {fmt} 提供可移植的 Unicode 支持（README 列为特性之一），配合支持 UTF-8 的终端即可；对齐宽度的计算不合并字素簇（官方文档明确），也不按终端显示列宽度量，CJK 宽字符在终端里通常占两列，肉眼对齐偏差多半来自这里，而不是库的问题。

**该用 `std::format` 还是 {fmt}？** 工具链已支持 C++20/23 且只需基础格式化，标准库即可；需要颜色/文本样式、写文件、老编译器支持或编译期格式串编译（FMT_COMPILE）时选 {fmt}。

**担心编译变慢？** 上面的对比表显示 {fmt} 头文件版编译 5.1s，二进制 54 KiB 与 printf 完全一致，远优于 iostreams（25.5s / 98 KiB）与 Boost Format（49.1s / 517 KiB）；C++20 模块版还能再降 27% 编译时间。

## 延伸

- 完整 API 与格式语法：[fmt.dev](https://fmt.dev)
- Compiler Explorer 在线试跑：README 内置链接，无需安装
- 性能方法学：[format-benchmark](https://github.com/fmtlib/format-benchmark)、[dtoa-benchmark](https://github.com/fmtlib/dtoa-benchmark)
- 12.2 新增面向 C 的 `fmt-c` 库（`fmt/fmt-c.h`），用 C11 `_Generic` 按实参类型分发，CHANGELOG 称其快于 printf/sprintf
- 学习路径：先跑通"验证步骤"一节的示例，再对照格式规格表试写自己的格式串；需要接入项目时看 CMake 集成一节。

仓库地址：[fmtlib/fmt](https://github.com/fmtlib/fmt)
