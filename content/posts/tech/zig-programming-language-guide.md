---
title: "Zig：42.8K Stars·通用编程语言·系统级性能"
date: 2026-04-12T02:31:39+08:00
slug: zig-programming-language-guide
description: "Zig 是一个通用编程语言，提供系统级性能和精确的内存控制，无需运行时，主要用于系统编程和嵌入式开发。"
draft: false
categories: ["技术笔记"]
tags: ["Zig", "编程语言", "系统编程", "内存管理", "性能"]
---

# Zig：42.8K Stars·通用编程语言·系统级性能·内存控制·无需运行时

## 一，项目概述

### 1.1 Zig 是什么

**Zig** 是由 **Andrew Kelley (andrewrk)** 创立的** 通用编程语言**，是一门系统级编程语言，提供高性能、内存控制和无需运行时（no runtime）的特性。

> "Zig is a general-purpose programming language and an efficient tool for developers who care about their code. It provides high performance, memory control, and a toolchain that works without a runtime."

**⚠️ 重要提示**：Zig 官方仓库已从 GitHub 迁移到 **Codeberg**（https://codeberg.org/ziglang/zig）。GitHub 上的此仓库不再同步更新。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | **42.8k** ⭐ |
| Forks | 3.1k |
| Watchers | 388 |
| 贡献者 | **1,098** |
| 最新提交 | **2025-11-27** (5个月前) |
| 许可证 | **MIT** |
| 语言 | Zig 98.4%, C 1.1%, C++ 0.2% |

### 1.3 核心定位

```
┌─────────────────────────────────────────────────────────────┐
│                    Zig 核心定位                                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   C/C++ 替代                                                    │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ ✅ 高性能                                          │   │
│   │ ✅ 内存控制                                         │   │
│   │ ✅ 无运行时                                         │   │
│   │ ✅ 跨平台                                          │   │
│   │ ✅ 编译时计算                                      │   │
│   │ ✅ 简单语法                                        │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                               │
│   对比 Rust                                                  │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ Zig: 简单、可读、更易学                              │   │
│   │ Rust: 复杂、内存安全、更难学                        │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 1.4 主要贡献者

| 贡献者 | 角色 |
|--------|------|
| **andrewrk** | 创始人，核心维护者 |
| **kubkon** | 构建系统，跨平台 |
| **alexrp** | 编译器后端 |
| **Vexu** | 标准库 |
| **jacobly0** | 运行时 |
| **mlugg** | 平台支持 |
| **LemonBoy** | 调试器 |
| **Snektron** | WebAssembly |
| **Luukdegram** | 标准库 |
| **squeek502** | Windows 支持 |
| **jedisct1** | 安全 |

## 二，技术架构

### 2.1 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Zig 编译系统架构                                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   源代码 (.zig)                                                │
│       ↓                                                         │
│   ┌─────────────────────────────────────────────────────┐   │
│   │               解析器 (Parser)                                  │   │
│   │   词法分析 → 语法分析 → AST                                │   │
│   └─────────────────────────────────────────────────────┘   │
│       ↓                                                         │
│   ┌─────────────────────────────────────────────────────┐   │
│   │               AST → ZIR (Zig Intermediate Representation)          │   │
│   │   语义分析 → 类型检查 → ZIR                                 │   │
│   └─────────────────────────────────────────────────────┘   │
│       ↓                                                         │
│   ┌─────────────────────────────────────────────────────┐   │
│   │               ZIR → LLVM IR                                   │   │
│   │   优化 → 生成 LLVM IR                                     │   │
│   └─────────────────────────────────────────────────────┘   │
│       ↓                                                         │
│   ┌─────────────────────────────────────────────────────┐   │
│   │               LLVM → 目标代码                                         │   │
│   │   x86_64, aarch64, wasm32, riscv64 等                    │   │
│   └─────────────────────────────────────────────────────┘   │
│       ↓                                                         │
│   目标文件 (.o) / 可执行文件                                   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 编译流程

```
┌─────────────────────────────────────────────────────────────┐
│                    Zig 编译流程                                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   stage1: 自举编译器                                            │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ 用 C 编写的最小编译器                                     │   │
│   │ bootstrap.c → bootstrap LLVM IR → stage1              │   │
│   └─────────────────────────────────────────────────────┘   │
│       ↓                                                         │
│   stage2: 完整编译器                                            │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ 用 Zig 编写的完整编译器                                   │   │
│   │ 源码 → stage1 → stage2                                │   │
│   └─────────────────────────────────────────────────────┘   │
│       ↓                                                         │
│   stage3: 优化编译器 (可选)                                      │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ 进一步优化编译速度和代码质量                             │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 项目结构

```
ziglang/zig/
├── src/                    # 编译器源码
│   ├── Compilation.rs      # 编译主流程
│   ├── Parser.rs           # 解析器
│   ├── Ast.rs              # AST 定义
│   ├── Sema.rs            # 语义分析
│   ├── Zir.rs             # ZIR 中间表示
│   ├── CodeGen.rs         # 代码生成
│   └── target/             # 目标平台支持
├── lib/                    # 标准库
│   ├── std/               # 标准库
│   │   ├── io.zig         # I/O
│   │   ├── fs.zig         # 文件系统
│   │   ├── net.zig        # 网络
│   │   ├── fmt.zig        # 格式化
│   │   ├── mem.zig        # 内存
│   │   ├── thread.zig     # 线程
│   │   ├── crypto.zig     # 加密
│   │   └── json.zig       # JSON
│   └── core/              # 核心库
├── stage1/                # 自举编译器
│   └── bootstrap.c        # C 代码
├── test/                  # 测试套件
├── doc/                   # 文档
├── tools/                # 工具
├── build.zig             # 构建脚本
├── build.zig.zon         # 包管理器
├── CMakeLists.txt         # CMake 构建
└── bootstrap.c           # Bootstrap 入口
```

## 三，核心特性

### 3.1 内存控制

```zig
// 栈分配
var arr: [100]i32 = undefined;

// 堆分配
const allocator = std.heap.page_allocator;
const ptr = try allocator.alloc(u8, 1024);
defer allocator.free(ptr);

// 无 GC，无 runtime
```

### 3.2 编译时计算

```zig
const fibonacci: [10]u32 = blk: {
    var arr: [10]u32 = undefined;
    arr[0] = 1;
    arr[1] = 1;
    for (2..10) |i| {
        arr[i] = arr[i-1] + arr[i-2];
    }
    break :blk arr;
};
// 编译时计算完成
```

### 3.3 defer 和 errdefer

```zig
const file = try openFile("data.txt");
defer file.close();  // 函数结束时执行

// 错误时执行
const result = try doSomething();
errdefer free(result);  // 错误时执行
```

### 3.4 error unions

```zig
const error = error.NotFound;
const result: !u32 = try parseInt(u32, "123");
// ! 表示可能返回错误
```

### 3.5 comptime

```zig
fn Matrix(comptime T: type, comptime rows: usize, comptime cols: usize) type {
    return struct {
        data: [rows][cols]T,
        fn get(self: *@This(), r: usize, c: usize) T {
            return self.data[r][c];
        }
    };
}
const Mat = Matrix(f32, 4, 4);
```

## 四，语法详解

### 4.1 基本类型

```zig
// 整数
const a: i32 = 42;
const b: u64 = 100;
const c: isize = -1;

// 浮点数
const d: f32 = 3.14;
const e: f64 = 2.718;

// 布尔
const flag: bool = true;

// 字符
const ch: u8 = 'A';

// 字符串
const str: []const u8 = "Hello, Zig!";
```

### 4.2 结构体

```zig
const Point = struct {
    x: f32,
    y: f32,

    fn distance(self: *const Point, other: *const Point) f32 {
        const dx = self.x - other.x;
        const dy = self.y - other.y;
        return @sqrt(dx * dx + dy * dy);
    }
};

const p1 = Point{ .x = 0, .y = 0 };
const p2 = Point{ .x = 3, .y = 4 };
const dist = p1.distance(&p2);
```

### 4.3 枚举

```zig
const Color = enum {
    red,
    green,
    blue,

    fn isWarm(self: Color) bool {
        return self == .red or self == .blue;
    }
};

const color = Color.red;
if (color.isWarm()) {
    // ...
}
```

### 4.4 联合体

```zig
const Payload = union {
    int: i32,
    float: f64,
    string: []const u8,
};

var payload = Payload{ .int = 42 };
payload.int = 100;  // OK
```

### 4.5 可选类型

```zig
const optional: ?i32 = null;
const value: i32 = optional orelse 0;
```

## 五，标准库

### 5.1 I/O

```zig
const std = @import("std");

const allocator = std.heap.page_allocator;

pub fn main() !void {
    const stdout = std.io.getStdOut().writer();
    
    try stdout.print("Hello, {s}!\n", .{"Zig"});
    
    // 读取文件
    const content = try std.fs.cwd().readFileAlloc(
        allocator,
        "data.txt",
        1024 * 1024
    );
    defer allocator.free(content);
}
```

### 5.2 线程

```zig
const std = @import("std");

const thread = try std.Thread.spawn(.{}, worker, .{});
thread.join();

fn worker() void {
    std.debug.print("Hello from thread!\n", .{});
}
```

### 5.3 网络

```zig
const std = @import("std");

const address = try std.net.Address.parseIp4("127.0.0.1", 8080);
const server = try address.listen(.{});
defer server.close();

const stream = try server.accept();
defer stream.close();
```

### 5.4 异步 I/O

```zig
const std = @import("std");

var server = try std.net.Address.parseIp4("0.0.0.0", 8080).listen();
defer server.close();

while (true) {
    const conn = try server.accept();
    try std.Thread.spawn(.{}, handleConn, .{conn});
}
```

## 六，构建系统

### 6.1 build.zig

```zig
const Builder = @import("std").build.Builder;

pub fn build(b: *Builder) void {
    const mode = b.standardReleaseOptions();
    
    const exe = b.addExecutable("myprogram", "src/main.zig");
    exe.setBuildMode(mode);
    
    b.default_step.dependOn(&exe.step);
    
    const run_cmd = exe.run();
    run_cmd.step.dependOn(b.getInstallStep());
}
```

### 6.2 build.zig.zon

```zig
.{
    .name = "myproject",
    .version = "0.1.0",
    .dependencies = .{
        .zmath = .{
            .url = "https://github.com/mich厅/zig-zmath/archive/refs/tags/v0.1.0.tar.gz",
            .hash = "1220abc123...",
        },
    },
}
```

### 6.3 构建命令

```bash
# Debug 构建
zig build

# Release 构建
zig build -Drelease-safe

# 运行
zig build run

# 测试
zig build test

# 安装
zig build install
```

## 七，包管理

### 7.1 依赖声明

```zig
// build.zig.zon
.{
    .name = "myproject",
    .version = "0.1.0",
    .dependencies = .{
        .zlm = .{
            .url = "https://github.com/ziglings/zig-linear-algebra/archive/refs/tags/v0.0.7.tar.gz",
            .hash = "1220123456789...",
        },
    },
}
```

### 7.2 使用依赖

```zig
const zlm = @import("zlm");

pub fn main() void {
    const matrix = zlm.Mat4.identity();
    // ...
}
```

## 八，交叉编译

### 8.1 支持的目标平台

| 平台 | 架构 |
|------|------|
| **Linux** | x86_64, aarch64, riscv64, arm, thumb |
| **macOS** | x86_64, aarch64 |
| **Windows** | x86_64, aarch64 |
| **FreeBSD** | x86_64 |
| **NetBSD** | x86_64 |
| **WebAssembly** | wasm32 |
| **SPIR-V** | spirv32, spirv64 |

### 8.2 交叉编译示例

```bash
# Linux → Windows
zig build -target x86_64-windows-gnu

# Linux → macOS
zig build -target aarch64-macos-gnu

# Linux → WebAssembly
zig build -target wasm32-wasi

# 指定 CPU
zig build -target x86_64-native -Dcpu=baseline
```

## 九，标准库详解

### 9.1 容器

```zig
const std = @import("std");
const ArrayList = std.ArrayList;
const AutoHashMap = std.AutoHashMap;

// 动态数组
var list = ArrayList(i32).init(std.heap.page_allocator);
defer list.deinit();
try list.append(42);
try list.append(100);

// 哈希表
var map = AutoHashMap([]const u8, i32).init(std.heap.page_allocator);
defer map.deinit();
try map.put("answer", 42);
```

### 9.2 格式化

```zig
const std = @import("std");

const str = try std.fmt.print("{d} + {d} = {d}\n", .{
    1, 2, 3
});

// 格式化到缓冲区
var buffer: [100]u8 = undefined;
const n = try std.fmt.bufPrint(&buffer, "Pi: {.3}", .{std.math.pi});
```

### 9.3 JSON

```zig
const std = @import("std");

const Person = struct {
    name: []const u8,
    age: u32,
};

const json_str = "{\"name\": \"Alice\", \"age\": 30}";
const parsed = try std.json.parseFromSlice(
    Person,
    json_str,
    .{}
);
defer parsed.deinit();
```

## 十，开发工具

### 10.1 Zig Language Server (zls)

```bash
# 安装
zig build -Drelease-safe --prefix ~/.local

# VS Code
# 安装 "Zig" 扩展
# 设置 zls.path 为 ~/.local/bin/zls
```

### 10.2 调试器

```bash
# 使用 lldb
lldb ./zig-out/bin/myprogram

# 或使用 gdb
gdb ./zig-out/bin/myprogram
```

### 10.3 测试

```zig
const std = @import("std");

test "addition" {
    const result = 1 + 2;
    try std.testing.expect(result == 3);
}

test "division by zero" {
    try std.testing.expectError(error.DivideByZero, divide(10, 0));
}
```

## 十一，性能优化

### 11.1 Inline 函数

```zig
inline fn add(a: i32, b: i32) i32 {
    return a + b;
}
```

### 11.2 字节码优化

```zig
// 使用 @Vector 提高 SIMD 性能
const vector = @Vector(4, f32){ 1.0, 2.0, 3.0, 4.0 };
const doubled = vector * @Vector(4, f32){ 2.0, 2.0, 2.0, 2.0 };
```

### 11.3 避免延迟分配

```zig
// 使用 arena allocator 减少分配次数
var arena = std.heap.ArenaAllocator.init(std.heap.page_allocator);
defer arena.deinit();
const allocator = arena.allocator();

// 大量小分配
for (0..1000) |_| {
    const ptr = try allocator.alloc(u8, 16);
    // ...
}
```

## 十二，常见错误处理

### 12.1 error sets

```zig
const MyError = error {
    NotFound,
    PermissionDenied,
    OutOfMemory,
};

fn openFile(path: []const u8) MyError!std.fs.File {
    // ...
    if (notFound) return MyError.NotFound;
    // ...
}
```

### 12.2 try/catch

```zig
const file = try openFile("data.txt");
defer file.close();

// 或使用 catch
const file = openFile("data.txt") catch |err| {
    std.debug.print("Failed: {}\n", .{err});
    return;
};
```

## 十三，资源链接

### 13.1 官方资源

| 资源 | 链接 |
|------|------|
| 🌐 **官方仓库** | https://codeberg.org/ziglang/zig |
| 📖 **文档** | https://ziglang.org/documentation/ |
| 💬 **社区** | https://ziglang.org/community/ |
| 🐦 **Twitter** | https://twitter.com/ziglang |

### 13.2 学习资源

| 资源 | 链接 |
|------|------|
| **Ziglings** | https://ziglings.org/ |
| **Zig Cookbook** | https://ziglang.org/learn/ |
| **Zig Community** | https://github.com/ziglang/community |
| **Zig Wiki** | https://github.com/ziglang/zig/wiki |

### 13.3 工具生态

| 工具 | 说明 |
|------|------|
| **ZLS** | Zig Language Server |
| **ziggy** | Zig → JSON Schema |
| **zmath** | 线性代数库 |
| **zimg** | 图像处理 |
| **miniz** | 压缩库 |

## 十四，总结

Zig 是** 现代系统级编程语言**：

| 维度 | 说明 |
|------|------|
| ⚡ **高性能** | LLVM 后端，零成本抽象 |
| 🛡️ **内存安全** | 可选的不安全模式 |
| 📦 **无运行时** | 直接编译到机器码 |
| 🔧 **构建简单** | 自举构建，无外部依赖 |
| 🌐 **跨平台** | 支持所有主流平台 |
| 📚 **可读性强** | 简单语法，容易理解 |

---

**⚠️ 重要提示**：Zig 官方仓库已迁移到 **Codeberg**（https://codeberg.org/ziglang/zig）。GitHub 上的仓库不再同步更新。

---

**🔗 相关资源：**

| 资源 | 链接 |
|------|------|
| Codeberg | https://codeberg.org/ziglang/zig |
| 文档 | https://ziglang.org/documentation/ |
| Ziglings | https://ziglings.org/ |

---

_🦞 本文由钳岳星君撰写，基于 Zig (42.8k Stars)_
