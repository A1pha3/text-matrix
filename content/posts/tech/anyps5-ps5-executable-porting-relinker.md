---
title: "AnyPS5：把 PS5 可执行文件移植到 Linux 与 Windows 的重链接器"
date: 2026-10-07T03:24:10+08:00
slug: "anyps5-ps5-executable-porting-relinker"
github_repo: "boykopovar/AnyPS5"
source_key: "gh:boykopovar/AnyPS5"
description: "AnyPS5 是一个将 PS5 可执行文件自动移植到 Linux 与 Windows 的工具，核心是一个重链接器（relinker），把目标系统原生格式的 ELF 转为对应可执行文件，并提供系统 PRX 库实现，不依赖模拟器。"
draft: false
categories: ["技术笔记"]
tags: ["逆向工程", "二进制移植", "C++", "开源"]
---

## 核心判断

AnyPS5 走的不是模拟器路线,也不是源码重编译路线,而是**二进制移植**:**重链接器(relinker)直接读取 PS5 的 ELF 可执行文件,把它转换成 Linux 或 Windows 的原生可执行格式,再配上系统库实现,让程序在目标系统上以原生进程运行**。

项目描述只有一句话:"Tool for automatic PS5 executables porting to Linux and Windows"。没有模拟层,没有独立的运行时进程——转换后的程序直接跑在目标操作系统上。

## 系统地图

```
PS5 可执行文件 (ELF)
        │
        ▼
   ┌─────────────┐
   │  relinker   │  ← 核心:格式转换 + 指令转换
   └─────────────┘
        │
        ▼
   Linux ELF / Windows PE 可执行文件
        │
        ▼
   libs/*.prx  ← 系统 PRX 库实现(动态链接用)
```

三个关键组成部分:

1. **relinker**(`core/relinker`):把可执行文件转换成目标系统原生格式
2. **系统 PRX 库**(`core/libs/prx`):PS5 系统库的实现,适合动态链接
3. **shader 重编译器**(`core/shader/recompiler`):把 shader 编译成 SPIR-V

## 转换流程

输入是一个干净的 ELF 可执行文件,它的捆绑 ELF 模块放在旁边的 `sce_module/`、`sce_modules/` 或 `prx/` 目录:

```text
source/
    input.elf
    sce_module/
        <bundled ELF modules>
```

转换命令:

```sh
relinker source/input.elf app.elf        # Linux 输出
relinker --windows source/input.elf app.exe   # Windows 输出
```

`--to-intel` 用于 Intel 主机——转换时把支持的 AMD 专属指令转成对应形式,不支持的指令或无法到达的转换桩会直接报错,而不是静默产出坏文件。

输出布局:

```text
app.elf (Linux) / app.exe (Windows)
libs/
    *.prx            # 系统库,从 build/core/libs/libs/*.prx 复制
app0/
    <app resources>  # 应用资源
    sce_module/      # 转换后的模块
```

## 关键机制

**导入裁剪(unused-filter)**。这是设计上最讲究的部分,分三档:

- `unused-filter=0`:保留所有导入的 NID 引用(NID 是 PS5 系统函数的稳定标识符)
- `unused-filter=1`:用控制流和 GOT 访问分析过滤未使用的非 PLT 导入,保留 PLT 导入
- `unused-filter=2`:严格未使用导入分析并压缩 PLT;无法分析的情况直接报错

裁剪导入能显著缩小输出体积、减少运行时依赖,但过度裁剪会破坏程序——所以设计成"宁可报错,不可静默错"。

**错误策略**。不支持的或意外的状态**严格抛 `std::runtime_error`**,`what()` 打印到 stderr 后进程终止。这个策略贯穿整个项目:转换遇到无法处理的情况就明确失败,不给用户一个看起来成功实际损坏的产物。

**不打包受版权保护内容**。项目声明:不包含、不分发、不要求受版权保护的软件、固件、加密密钥或专有库。用户有责任确保使用的二进制文件来源合法。定位是互操作性、研究、保存与兼容性目的。

## 现状与进度

- 系统库覆盖以"已知函数占比"衡量(见项目页的 progress 徽章),不是 PS5 每个系统函数的完整覆盖
- 已有一份验证过的游戏兼容列表
- 示例:Dreaming Sarah(2D 平台游戏)在 GTX 1050 Ti / i5-7500 上稳定跑 60 fps
- shader 重编译器能成功产出 SPIR-V(启用 `ANYPS5_ENABLE_SPIRV_TOOLS` 时用 Spirv-Tools 验证)
- 项目活跃:近期提交包含 kernel AIO 批处理、HTTP 离线 no-op、ngs2 系统状态等功能,2026-09-28 发布 v0.1.0 与 v0.1.1

## 适用边界

- **这不是模拟器**:没有模拟层或独立运行时进程,转换后的程序是原生进程
- **不是全自动的银弹**:系统库覆盖在增长但未完整;不支持的指令或转换情况会明确报错
- **有法律与合规边界**:项目声明为互操作/研究/保存/兼容用途,不附带受版权保护内容;用户需自行确保二进制来源合法
- **适合谁**:逆向工程研究者、PS5 游戏的互操作与保存实践者、对二进制移植感兴趣的工程师

## 采用建议

如果你对"如何把游戏机可执行文件搬到桌面系统"这个工程问题感兴趣,AnyPS5 的 relinker + 系统库实现 + shader 重编译三件套是目前少见的完整开源实现。先读 `docs/user/USAGE.md` 理解转换流程,再看 `docs/dev/BUILD.md` 了解构建方式,最后对照兼容列表评估实际覆盖度。
