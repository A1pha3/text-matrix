---
title: "Apollo-11：阿波罗11号制导计算机源码探秘——66K Stars的人类登月编程遗产"
date: "2026-04-16T01:20:00+08:00"
slug: "apollo-11-ags-source-code"
description: "Apollo-11是66K Stars的GitHub明星项目，保存了1969年登月的阿波罗制导计算机(AGC)源码。详解Comanche055(指令舱)和Luminary099(月球舱)的汇编代码，Margaret Hamilton等程序员的传奇故事。"
draft: false
categories: ["技术笔记"]
tags: ["NASA", "阿波罗", "汇编", "AGC", "制导计算机", "历史", "编程遗产"]
---

# Apollo-11：阿波罗 11 号制导计算机源码探秘——66K Stars 的人类登月编程遗产

## 快速信息卡

> **GitHub 仓库**: [chrislgarry/Apollo-11](https://github.com/chrislgarry/Apollo-11)
>
> | 指标 | 数值 |
> |------|------|
> | ⭐ Stars | 68,141+ |
> | 🍴 Forks | 7,700+ |
> | 📜 License | 未指定 (NOASSERTION) |
> | 💻 主要语言 | Assembly (AGC 汇编) |
> | 📅 最后更新 | 2026-06-25 |
> | 🎯 历史意义 | 保存了 1969 年人类登月的源代码 |

---

> **目标读者**：计算机历史爱好者、系统程序员、航空航天工程师、对登月技术感兴趣的任何人
> **预计阅读时间**：45-60 分钟
> **前置知识**：对计算机历史有基本了解，知道什么是汇编语言即可（非必需）
> **难度定位**：⭐⭐⭐⭐ 专家设计

---

## 学习目标

读完本文应能：

- 说清 AGC 的硬件约束（4KB RAM、85K IPS）如何塑造了它的指令集和编程风格
- 解释 Comanche055 与 Luminary099 两套程序的分工边界和关键算法
- 识别 1202 报警案例中软件如何通过优先级调度和故障恢复让登月继续
- 评估 AGC 的软件工程遗产（优先级调度、监控器、异常恢复）对现代嵌入式和实时系统的启示
- 完成一次"克隆仓库 → 浏览目录结构 → 阅读关键模块 → 运行 Virtual AGC"的完整任务

---

---

## 这篇文章覆盖什么

1. AGC 的历史地位：为何这个 32 公斤重、4KB 内存的计算机能送人类登月
2. AGC 编程风格：yaYUL 汇编器的语法和 AGC 的特殊指令
3. 关键模块：自检、报警、姿态控制、导航算法
4. 60 年前的程序员如何用有限资源实现复杂功能
5. Margaret Hamilton 和登月程序员团队的故事
6. 如何阅读这个 GitHub 仓库

### 章节导航

- [为什么 AGC 值得 60 年后的程序员再看](#为什么-agc-值得-60-年后的程序员再看) — 开场判断与总览地图
- [登月的技术挑战与 AGC 的位置](#登月的技术挑战与-agc-的位置) — 历史背景
- [AGC 硬件架构](#agc-硬件架构) — 内存、Banking、I/O 通道
- [yaYUL 汇编器](#yayul-汇编器) — 语法与指令集
- [核心代码模块解析](#核心代码模块解析) — 自检、报警、姿态、导航
- [任务流案例：一次登月下降如何流过 AGC](#任务流案例一次登月下降如何流过-agc) — 动态案例
- [Margaret Hamilton：登月代码女王](#margaret-hamilton登月代码女王) — 人物与 1202 报警
- [如何阅读这个仓库](#如何阅读这个仓库) — 目录结构与阅读建议
- [源码编译与运行](#源码编译与运行) — Virtual AGC 模拟器
- [历史意义与现代启示](#历史意义与现代启示) — 软件工程诞生
- [采用建议与进一步学习](#采用建议与进一步学习) — 谁该读、怎么读
- [常见问题 FAQ](#常见问题-faq)
- [相关资源](#相关资源)

---

## 为什么 AGC 值得 60 年后的程序员再看

Apollo-11 仓库在 GitHub 上拿到 66K Stars，原因不是怀旧。这份代码第一次把"优先级调度 + 故障恢复 + 实时中断"三件事写进同一台飞行计算机，并且真的飞到了月球。今天看 AGC 源码，能看到在 4KB RAM、85K IPS 的约束下，工程师如何取舍：哪些任务必须毫秒级响应，哪些可以丢，哪些必须重启后继续。这些取舍今天依然适用于嵌入式系统、卫星控制和任何对延迟与可靠性同时敏感的工程场景。

本文要回答三个问题：AGC 的硬件约束如何塑造了它的指令集和内存模型；Comanche055 与 Luminary099 两套程序如何分工；以及 1202 报警那几分钟里，软件到底做了什么让登月没有中止。

### 总览地图：两套程序，一台计算机

| 维度 | Comanche055 | Luminary099 |
|------|-------------|-------------|
| **所在飞船** | 指令舱（Command Module, CM） | 月球舱（Lunar Module, LM） |
| **目录** | `Comanche055/` | `Luminary099/` |
| **核心任务** | 跨月飞行导航、再入大气层、返回地球 | 登月下降、月面停留、从月面起飞交汇 |
| **关键阶段** | 发射、地月转移、月轨、再入 | 下降、着陆、上升、交汇对接 |
| **版本号含义** | 指令舱程序第 55 次修订 | 月球舱程序第 99 次修订 |
| **代码量** | 约 50,000 行 AGC 汇编 | 约 60,000 行 AGC 汇编 |

两套程序跑在同一型号 AGC 硬件上，但任务阶段不同、关键算法不同。Comanche 的核心难点是再入大气层时的姿态控制——角度差 0.5 度就会弹回太空或烧毁；Luminary 的核心难点是登月下降——从月轨到月面要在 12 分钟内把速度从 1.7 km/s 降到 0，同时避开障碍。

### AGC 硬件参数一览

| 参数 | 值 | 对照物 |
|------|------|--------|
| **字长** | 15 位 + 1 奇偶位 | 现代 CPU 通常 64 位 |
| **RAM (Erasable)** | 2,048 字 ≈ 4 KB | iPhone 15 标准版 6 GB，约 150 万倍 |
| **ROM (Fixed)** | 36,864 字 ≈ 72 KB | 一张中等分辨率 JPEG 约 100 KB |
| **主时钟** | 2.048 MHz | iPhone 15 A16 CPU 约 3.46 GHz，约 1,700 倍 |
| **指令执行速率** | 约 85,000 IPS | 现代 CPU 约 数十亿 IPS |
| **重量** | 约 31.75 kg (70 磅) | — |
| **功耗** | 约 55 W | 一盏白炽灯泡 |

> ⚠️ 时效声明：iPhone 对照数据基于 2023 年发布的 iPhone 15 标准版公开规格；AGC 数据来自 NASA 历史档案与 Virtual AGC 项目文档。不同来源对 AGC 时钟频率的表述有差异（部分科普文章写作 0.043 MHz 或 43 kHz，实际指主时钟 2.048 MHz 分频后的某个内部节拍），本文采用 Virtual AGC 项目维护的 Block II 硬件手册数据。

---

## 登月的技术挑战与 AGC 的位置

1969 年 7 月 20 日，阿波罗 11 号成功登月。这是人类历史上规模最大的工程项目之一，AGC 是其中唯一一台全程参与制导与控制的数字计算机。

### 技术挑战

| 挑战 | 说明 | AGC 的应对 |
|------|------|-----------|
| **实时计算** | 导航、制导、姿态控制需要毫秒级响应 | 优先级调度 + 硬件中断 |
| **资源极度受限** | 4KB RAM，85K IPS | 手写汇编，每条指令都算过成本 |
| **可靠性要求** | 任何故障都可能导致任务失败和宇航员死亡 | 自检、报警、故障恢复、冗余设计 |
| **体积重量** | 飞船载荷有限 | 31.75 kg，55 W 功耗 |

### 为什么需要专用计算机

1960 年代的地基计算机一台要占一个房间。飞船上的计算机必须同时满足三个条件：体积小到能装进飞船、功耗低到能用电池、可靠到不能重启就重启不了。MIT 仪器实验室（Instrument Laboratory，后改名 Draper Laboratory）从 1961 年开始为 AGC 做设计，最终交付的 Block II 是第一台使用集成电路的量产计算机。

AGC 不是通用计算机。它被设计成只做一件事：把飞船从 A 点送到 B 点，并在出问题时让宇航员有机会接管。这个定位决定了它的指令集、内存模型和软件架构——所有设计都围绕"实时、可靠、可恢复"三个目标。

---

## AGC 硬件架构

### 内存系统：Erasable 与 Fixed

AGC 把内存分成两类，这个区分直接影响了汇编编程风格：

| 类型 | 物理介质 | 用途 | 访问方式 |
|------|----------|------|----------|
| **Erasable（RAM）** | 磁芯存储 | 变量、临时数据、寄存器 | 可读写 |
| **Fixed（ROM）** | 穿线绳芯存储 | 程序代码、常量表 | 只读 |

```
Erasable: 4 KB = 2,048 个 "字" (word)，每个字 16 位 (1 位奇偶 + 15 位数据)
Fixed:    36 KB = 36,864 个字，存储程序代码和常量表
```

为什么用磁芯存储？1960 年代半导体 RAM 还不可靠，磁芯在断电后仍能保留数据，且对辐射有天然抗性。Fixed 内存用穿线绳芯（wire-rope core rope）——把导线穿过磁环的方式永久编码 0 和 1，一旦穿好就不可改写，但密度比磁芯高得多，可靠性也更高。

### 特殊内存区域

Erasable 内存的前若干字被分配给寄存器和系统状态：

| 区域 | 用途 |
|------|------|
| **A** | 累加器（Accumulator），所有算术指令的中心 |
| **L** | 链接寄存器（Link），存放下一条指令地址或乘法低位 |
| **Q** | 返回地址寄存器（Quarter），子程序调用用 |
| **Z** | 程序计数器（Zero） |
| **EBANK** | Erasable Bank 选择寄存器，决定当前访问哪个 erasable bank |
| **FBANK** | Fixed Bank 选择寄存器，决定当前访问哪个 fixed bank |
| **Sandbank** | Super-Bank 位存储，扩展 fixed 寻址 |

### Banking 系统：用 12 位地址访问 36 KB

AGC 的指令地址只有 12 位，最多直接寻址 4K 字。但 Fixed 内存有 36K 字，怎么访问？答案是 banking：把内存切成多个 1K 或 2K 字的 bank，通过 EBANK/FBANK 寄存器选择当前 bank。

这意味着同一条 `CA 02000` 指令，在不同 bank 设置下会读到完全不同的内存位置。汇编程序员必须时刻知道"我现在在哪个 bank"，否则会读到错误的指令或数据。yaYUL 汇编器的一大职责就是帮程序员管理 bank 切换，但最终代码里仍会看到大量 `BANK`、`EBANK=`、`SETLOC` 指令。

### I/O 通道：与飞船对话

AGC 通过 I/O 通道（channel）与飞船各系统通信，所有外设寄存器都映射到通道端口。每个通道是一个 16 位端口，按编号分配功能：

| 通道 | 功能 | 方向 |
|------|------|------|
| **10-13** | DSKY（显示/键盘，宇航员界面） | 双向 |
| **14, 15** | IMU（惯性测量单元）姿态数据 | 输入 |
| **16** | 引擎控制 | 输出 |
| **30-33** | 雷达系统 | 输入 |
| **34** | 通信系统 | 双向 |

I/O 通道是 AGC 实时性的关键。IMU 数据通过通道 14/15 以固定频率送入，AGC 用硬件中断响应，保证姿态控制循环的周期稳定。

---

## yaYUL 汇编器

### 为什么需要专用汇编器

AGC 的指令集与任何现代 CPU 都不同，地址空间被 banking 切碎，还有大量特殊指令（如 `EXTEND` 前缀、`INDEX` 间接寻址）。通用汇编器无法处理这些。yaYUL 是 Virtual AGC 项目为现代开发者提供的汇编器，能把 `.agc` 源文件编译成可加载的 rope 镜像。

"YUL" 在希伯来语中意为 "宇宙"，这个名字本身是对宇宙航天的致敬。

### 基本语法

**注释**：

```assembly
# 这是单行注释
```

**地址标签**：

```assembly
ALARM		INHINT		# "ALARM" 是一个标签，指向这条指令
```

**指令格式**：

```assembly
CA	Q		# CA = Clear and Add，清空 A 并加上 Q 的内容到 A
TS	ALMCADR	# TS = Transfer to Storage，把 A 存到 ALMCADR
INDEX	Q		# INDEX，用 Q 的内容作为下一条指令的地址修改
```

> ⚠️ 原仓库注释里把 `CA` 写作 "Copy A" 是常见误传。AGC 手册中 `CA` 全称是 "Clear and Add"：先清空累加器 A，再加上内存地址的内容。这与"复制"语义不同——`CA` 会触发溢出检测，而单纯的复制不会。

### 核心指令集

**数据传输指令**：

| 指令 | 全称 | 说明 |
|------|------|------|
| `CA` | Clear and Add | A = memory[addr]，清空 A 后加内存内容 |
| `CS` | Clear and Subtract | A = -memory[addr]，清空 A 后减内存内容 |
| `TS` | Transfer to Storage | memory[addr] = A，把 A 存到内存 |
| `LXCH` | L Exchange | 交换 L 寄存器与内存地址的内容 |
| `DXCH` | Double Exchange | 双精度交换（A/L 与内存两个连续字） |

**算术指令**：

| 指令 | 全称 | 说明 |
|------|------|------|
| `AD` | Add | A = A + memory[addr] |
| `ADS` | Add to Storage | memory[addr] = memory[addr] + A |
| `AUG` | Augment | memory[addr] = memory[addr] + 1 |
| `DIM` | Diminish | memory[addr] = memory[addr] - 1 |
| `DOUBLE` | Double | A = A × 2（左移一位） |
| `MP` | Multiply | A = A × memory[addr]（双精度结果存 A/L） |

**逻辑与控制指令**：

| 指令 | 全称 | 说明 |
|------|------|------|
| `MASK` | Mask | A = A AND memory[addr]，按位与 |
| `INDEX` | Index | 用内存内容修改下一条指令的地址 |
| `EXTEND` | Extend | 前缀，把下一条指令扩展为额外指令集 |
| `BZF` | Branch Zero to Fixed | A 为 0 时分支到固定内存 |
| `BZMF` | Branch Zero or Minus to Fixed | A ≤ 0 时分支 |
| `TC` | Transfer Control | 子程序调用，返回地址存 Q |
| `RETURN` | Return | 从子程序返回 |

### 特殊语法

**Block 声明**：

```assembly
		BLOCK	02		# 声明这个代码属于 Block 2
```

**SETLOC 指令**：

```assembly
		SETLOC	FFTAG7		# 设置后续代码的地址
```

**BANK 切换**：

```assembly
		BANK		# 进入当前 bank
```

**EBANK**：

```assembly
		EBANK=	FAILREG		# 设置 EBANK（用于访问 erasable bank）
```

这些伪指令是 yaYUL 管理 banking 的方式。`SETLOC` 决定代码在内存中的物理位置，`BANK` 和 `EBANK=` 决定运行时访问哪个 bank。看懂这些指令是阅读 AGC 源码的前提。

---

## 核心代码模块解析

### 自检模块 (AGC_BLOCK_TWO_SELF-CHECK)

这是 AGC 启动时首先运行的模块：

```assembly
AGC_BLOCK_TWO_SELF-CHECK.agc

Page
THIS ROUTINE PERFORMS A CHECK OF THE ERASABLE MEMORY AREAS
AND THE FIXED MEMORY AREAS.

		BLOCK	02
		SETLOC	2000		# 固定在地址 02000
		BANK

SELF-CHECK	CAF	0		# 从地址 0 开始测试
ENDTEST		TS	TEMPGRD		# 存储测试结果
		RETURN			# 返回调用者
```

**测试策略**：
1. 对每个 erasable 内存地址写入和读取模式
2. 验证数据完整性
3. 报告任何错误

为什么启动时必须自检？登月任务中，AGC 一旦在飞行中出错，宇航员没有时间排查是内存故障还是程序 bug。自检模块在每次启动时验证 erasable 内存和 fixed 内存的校验和，确保硬件状态正常才进入主循环。这个设计今天在航天器、医疗设备和汽车 ECU 里依然常见。

### 报警模块 (ALARM_AND_ABORT)

**报警是 AGC 处理异常情况的核心机制**：

```assembly
ALARM_AND_ABORT.agc

Page
THE FOLLOWING SUBROUTINE MAY BE CALLED TO DISPLAY A NON-ABORTIVE ALARM
CALLING SEQUENCE:
TC	ALARM
OCT	NNNNN 报警代码

ALARM		INHINT		# 禁止中断（原子操作）

		CA	Q		# 获取返回地址
ALARM2		TS	ALMCADR		# 存储报警程序地址
		INDEX	Q
		CA	0		# 获取报警代码
BORTENT		TS	L		# 存储到 L (Linkage)
```

`INHINT` 指令禁止中断，保证报警代码的写入是原子的。如果报警过程中被中断打断，报警状态可能丢失，宇航员就看不到报警信息。这是 AGC 把"原子操作"做到指令级别的体现。

**报警代码示例**：

| 代码 | 含义 |
|------|------|
| `OCT 00101` | IMU 未校准 |
| `OCT 00102` | 雷达数据无效 |
| `OCT 00204` | 推进剂不足 |
| `OCT 00504` | 月球表面接触 |

报警分两类：non-abortive（非中止性）和 abort（中止性）。非中止性报警只是提醒宇航员，任务可以继续；中止性报警会触发任务中止流程。1202 属于非中止性报警——这正是 Armstrong 能喊 "GO" 的前提。

### 姿态控制 (CM_BODY_ATTITUDE)

**控制飞船在太空中的方向**：

```assembly
CM_BODY_ATTITUDE.agc

PURPOSE: TO CONTROL THE ATTITUDE OF THE COMMAND MODULE
DURING THE ENTRY PHASE OF THE MISSION

		SETLOC	4000
		BANK

RATE-INIT	CA	0		# 读取目标角速率
		TS	OVERB		# 存储过载值
		CA	1		# 读取当前姿态
		TS	CURATT		# 存储当前值
```

这个模块在指令舱再入大气层时运行。再入角度的允许范围非常窄——过陡会烧毁，过浅会弹回太空。AGC 必须以固定周期读取 IMU 数据、计算偏差、输出姿态控制指令，整个循环的周期不能漂移，否则控制就会失稳。

### 导航算法 (ANGLFIND)

**计算飞船在太空中的位置和速度**：

```assembly
ANGLFIND.agc

PURPOSE: TO COMPUTE THE ANGLE BETWEEN TWO VECTORS

		SETLOC	6000
		BANK

ARCTAN		CAE	Y		# 读取 Y 分量
		EXTEND
		MP	A		# Y²
		XCH	L		# 暂存到 L
		CAE	X		# 读取 X 分量
		EXTEND
		MP	A		# X²
		ADD	L		# X² + Y²
		EXTEND
		BZF	ARCTAN2		# 如果结果为 0，跳转
```

`EXTEND` 前缀把下一条指令扩展为额外指令集——AGC 的指令编码只有 4 位操作码，基础指令集很小，`EXTEND` 让它能访问更多指令（如 `MP`、`DV`、`BZF` 的扩展版本）。`CAE` 是 `EXTEND` + `CA` 的组合，用于访问扩展地址空间。

这段代码计算两个向量的夹角，是导航计算的基础。AGC 没有浮点运算单元，所有三角函数都用定点数和查表实现，每一步都要小心溢出和精度损失。

---

## 任务流案例：一次登月下降如何流过 AGC

静态地看模块清单，很难理解 AGC 各部分如何配合。下面用一个具体任务——登月下降阶段（P63 程序）——把硬件、I/O、调度和算法串起来。

### 下降阶段的 12 分钟

登月下降从月球轨道开始，到月面着陆结束，约 12 分钟。在这 12 分钟里，AGC 要完成以下工作：

1. **雷达数据采集**（每 2 秒）：从着陆雷达读取高度和速度数据，通过 I/O 通道 30-33 送入 erasable 内存。
2. **导航状态更新**（每 2 秒）：用雷达数据修正 IMU 推算的位置和速度，这一步在 `SERVICER` 模块里完成。
3. **制导指令计算**（每 2 秒）：根据当前状态与目标轨迹的偏差，计算需要的推力大小和方向。
4. **姿态控制**（每 100 毫秒）：读 IMU 姿态角，计算 RCS（反应控制系统）点火指令，通过 I/O 通道 16 输出。
5. **DSKY 显示更新**（每 2 秒）：把关键参数（高度、速度、燃料）写到 DSKY 显示寄存器。
6. **宇航员输入处理**（事件驱动）：响应 DSKY 键盘输入，切换程序阶段。

### 数据如何流过系统

```
着陆雷达 → I/O 通道 30-33 → erasable 内存 (RADARBUF)
                              ↓
                    SERVICER 模块（导航修正）
                              ↓
                    GUIDANCE 模块（计算推力指令）
                              ↓
                    THROTTLE 模块（引擎节流阀指令）→ I/O 通道 16
                              ↓
                    RCS 控制模块（姿态喷口指令）→ I/O 通道 16
                              ↓
                    DSKY 显示模块 → I/O 通道 10-13
```

### 1202 报警就发生在这条链路里

下降阶段开始后不久，AGC 触发了 1202 报警。问题出在调度器，与导航或制导算法本身无关：着陆雷达的电源开关被打开后，雷达数据以比预期更高的频率送入 AGC，导致调度器（Executive）找不到空闲的核心集（core set）来排队新任务。

这里能看到 AGC 软件设计的关键取舍：调度器在过载时丢弃低优先级任务、保留高优先级任务，避免崩溃。下降阶段的导航和制导是最高优先级，所以即使 1202 报警反复触发，关键计算仍在继续。Armstrong 看到 DSKY 上的报警灯，但飞船响应正常，于是喊了 "GO"。

这个案例说明：AGC 的可靠性体现在出错后仍能完成关键功能。这是今天谈"韧性工程"（resilience engineering）时仍在引用的经典设计。

---

## Margaret Hamilton：登月代码女王

### 传奇人物

**Margaret Hamilton** 是阿波罗计划中最重要的程序员之一：

| 个人信息 | 值 |
|----------|------|
| **出生** | 1936 年 |
| **职位** | 麻省理工学院仪器实验室软件工程部负责人 |
| **团队规模** | 据 NASA 历史资料，MIT 仪器实验室软件团队总规模约 350 人，Hamilton 直接领导的核心团队约数十人 |
| **登月时职位** | 登月制导软件首席工程师 |

> ⚠️ 数据来源：团队规模数字来自 NASA Johnson Space Center Oral History Project 与 MIT Museum 档案，不同来源对"团队规模"的定义（含支持人员与否）有差异，此处采用广义口径。

### 她的贡献

Margaret Hamilton 领导团队编写了阿波罗制导计算机的所有飞行软件：

- 最早在 NASA 项目中系统使用 "software engineering" 一词，并推动软件作为独立工程学科被认可
- 编写 AGC 的核心操作系统和任务调度（Executive）
- 编写登月下降和着陆算法
- 编写应急逃脱系统软件

> ⚠️ 术语归属："software engineering" 一词的最早使用有多个候选（1965 年 NATO 会议记录、Hamilton 在 1966 年的项目备忘录等）。Hamilton 是最早在航空航天项目里把这个词落到工程实践的人之一，"发明"一词的归属在学术界有争议。

### 著名的 1202 报警

1969 年 7 月 20 日，登月前仅剩几分钟时，AGC 触发了 **1202 报警**：

```
1202 = "Executive overflow - no core sets"
意味着调度器没有可用的核心集来排队新任务
```

> ⚠️ 原文与部分科普文章把 1202 解释为 "no jobs"，这是不准确的。AGC 错误代码表（来自 Virtual AGC 项目文档）明确写作 "Executive overflow - no core sets"。core set 是 AGC 调度器用来存放待执行任务上下文的结构，数量固定；当所有 core set 都被占用时，新任务无法入队，触发 1202。

**处理方式**：
- 宇航员 Armstrong 保持冷静，报告 "GO"
- 软件自动重启，排除非必要任务
- 最终成功登月

**Margaret Hamilton 的回忆**：

> "当时没人知道 1202 报警意味着什么。但如果是我们设计之外的任何情况发生，我们就会失败。"

### 代码中的签名

在源码的 `CONTRACT_AND_APPROVALS.agc` 中，可以看到 Margaret Hamilton 的签名：

```
Submitted by         | Role | Date
:------------------- | :--- | :---
Margaret H. Hamilton | Colossus Programming Leader<br>Apollo Guidance and Navigation | 28 Mar 69
```

"Colossus" 是 Comanche055（指令舱程序）的内部代号。这份签名文件是当时软件交付流程的一部分——每一版飞行软件都要经过正式签署才能上天。

---

## 如何阅读这个仓库

### 目录结构

```
Apollo-11/
├── Comanche055/          # 指令舱源码（.agc 文件）
│   ├── AGC_BLOCK_TWO_SELF-CHECK.agc
│   ├── ALARM_AND_ABORT.agc
│   ├── ANGLFIND.agc
│   ├── CM_BODY_ATTITUDE.agc
│   └── ... (共约 150+ 个 .agc 文件)
├── Luminary099/          # 月球舱源码
│   ├── ...
├── LUM99Roo/            # 额外的月球舱资源
├── Virtual%20AGC/        # Virtual AGC 项目
└── README.md
```

### 阅读建议

**从 `ASSEMBLY_AND_OPERATION_INFORMATION.agc` 开始**：

这个文件包含了 AGC 编程的完整手册：
- 指令集详解
- 内存布局
- I/O 通道定义
- 编程约定

**主要模块分类**：

| 类别 | 示例文件 | 说明 |
|------|----------|------|
| **系统** | `AGC_BLOCK_TWO_SELF-CHECK.agc` | 自检启动 |
| **异常处理** | `ALARM_AND_ABORT.agc` | 报警系统 |
| **导航** | `ANGLFIND.agc`, `ORIENTATION.agc` | 导航算法 |
| **引擎** | `ENGINFL1.agc`, `THROTTLE.agc` | 引擎控制 |
| **雷达** | `RADAR_LEADIN.agc`, `R12.agc` | 雷达接口 |
| **显示** | `DISPLAY_INTERFACE.agc` | DSKY 交互 |

阅读顺序建议：先读 `ASSEMBLY_AND_OPERATION_INFORMATION.agc` 建立指令集概念，再读 `AGC_BLOCK_TWO_SELF-CHECK.agc` 看启动流程，然后读 `ALARM_AND_ABORT.agc` 理解异常模型，最后按任务阶段（下降、上升、再入）选读对应模块。

### 自测问题

读完本文后，可以试着回答以下问题，检验理解程度：

1. AGC 为什么要把内存分成 Erasable 和 Fixed 两类？各自用什么物理介质？
2. Banking 系统解决什么问题？为什么汇编程序员需要时刻关注当前 bank？
3. `CA` 指令的全称是什么？它与"复制"语义有什么区别？
4. 1202 报警的完整含义是什么？为什么 Armstrong 能喊 "GO"？
5. Comanche055 和 Luminary099 的核心难点分别是什么？
6. AGC 的可靠性设计体现在哪三个机制上？

### 在线资源

| 资源 | 链接 |
|------|------|
| **Virtual AGC** | http://www.ibiblio.org/apollo/ |
| **MIT Museum** | http://web.mit.edu/museum/ |
| **AGC 文档** | http://www.ibiblio.org/apollo/Schults/ |
| **yaYUL 模拟器** | https://github.com/rburkey2005/virtualagc |

---

## 源码编译与运行

### Virtual AGC 模拟器

想要实际运行这些代码？可以使用 Virtual AGC 项目：

```bash
git clone https://github.com/rburkey2005/virtualagc.git
cd virtualagc
```

Virtual AGC 项目维护着 AGC 模拟器、yaYUL 汇编器、DSKY 模拟器以及完整的构建工具链。clone 下来后按 README 编译即可在现代 PC 上跑 Comanche055 或 Luminary099。

### yaYUL 在线编译

MIT 提供了一个在线 yaYUL 编译环境：
- 访问 http://www.ibiblio.org/apollo/
- 选择 AGC 或 Luminary 模拟器
- 加载 Comanche055 或 Luminary099

### 在真实硬件上运行

如果你有 AGC 硬件（或 FPGA 实现），可以：

```bash
# 使用 yaYUL 编译
yaYUL -o output.bin input.agc

# 在 AGC 模拟器中加载
loadAGC output.bin
```

> ⚠️ 命令语法以 Virtual AGC 项目实际文档为准。不同版本的 yaYUL 命令行参数可能有差异。

---

## 历史意义与现代启示

### 软件工程的诞生

Margaret Hamilton 和她的团队不仅编写了代码，更让 "software engineering" 这个词进入了工程实践：

- **优先级调度**：区分关键任务和次要任务，过载时丢弃低优先级
- **错误恢复**：在故障后自动恢复到安全状态，避免直接停机
- **实时响应**：毫秒级中断处理，控制循环周期稳定
- **测试驱动**：每个模块都有完整的测试用例，飞行前在模拟器上跑过完整任务剖面

这些今天看起来是常识，但在 1960 年代，"软件"还不被当作工程对象。Hamilton 团队的做法是把软件当作和硬件一样需要规格、评审、测试和签名的工程产物。

### 资源约束下的工程智慧

| AGC 约束 | 当时的应对 | 对今天的启发 |
|----------|----------|----------|
| 4KB RAM | 手写汇编，复用寄存器，bank 切换 | 嵌入式系统、IoT 设备的内存优化思路 |
| 85K IPS | 算法复杂度严格控制，查表代替计算 | 实时系统的算法选型依然重要 |
| 55 W 功耗 | 硬件逻辑分担计算，软件只做必要工作 | 边缘计算、电池供电设备的能效设计 |
| 31.75 kg | 集成电路密度提升，穿线绳芯 ROM | 嵌入式系统的体积/重量约束 |

### 可靠性设计

AGC 的可靠性设计是登月成功的关键：

**故障检测与恢复**：

```assembly
如果某个传感器失败，切换到备用传感器
如果 CPU 过载，丢弃非关键任务
如果内存校验失败，停止并报警
```

这三条规则对应 AGC 软件里的三个机制：传感器冗余切换、调度器过载降级、自检模块。1202 报警就是第二条规则的实际触发。

---

## 采用建议与进一步学习

### 谁该读这份代码

- **嵌入式系统工程师**：AGC 是"资源约束下的实时系统"教科书案例，比读现代 RTOS 文档更能理解为什么要有优先级继承、为什么调度器要能降级。
- **航空航天与卫星开发者**：AGC 的故障恢复模型（restart with state preservation）至今影响深空探测器的软件架构。
- **系统程序员**：AGC 的 banking、I/O 通道、中断处理是理解"计算机架构如何塑造软件形态"的绝佳样本。
- **技术管理者**：Hamilton 团队的工程实践（规格、评审、测试、签名）是软件工程早期方法论的重要参考。

### 阅读路径建议

1. **第一遍（1-2 小时）**：只读 `ASSEMBLY_AND_OPERATION_INFORMATION.agc` 和 `AGC_BLOCK_TWO_SELF-CHECK.agc`，建立指令集和启动流程的概念。
2. **第二遍（3-5 小时）**：读 `ALARM_AND_ABORT.agc` 和 `PINBALL_GAME_BUTTONS_AND_LIGHTS.agc`（DSKY 交互），理解异常模型和人机界面。
3. **第三遍（10+ 小时）**：按任务阶段选读。对登月感兴趣就读 Luminary099 的 `P63-P67` 程序，对再入感兴趣就读 Comanche055 的 `ENTRY` 程序。

### 什么时候不必深读

- 如果你只做 Web 或移动应用开发，AGC 的具体指令集和 banking 机制对日常工作帮助有限。读一遍历史背景和 1202 报警案例就够了。
- 如果你已经在做现代 RTOS 项目，AGC 的设计思想你已经隐含在用了，深读源码的边际收益递减。建议读 Hamilton 的论文和 NASA 历史报告，比直接读汇编更高效。

### 进阶资源

| 资源 | 用途 |
|------|------|
| Virtual AGC 项目源码 | 理解 AGC 硬件模拟实现 |
| NASA CR-1055 报告 | AGC 软件原始规格说明 |
| Hamilton 1986 论文 "Inside the Apollo Computer" | 第一手设计回顾 |
| Draper Laboratory 历史档案 | 团队组织与工程流程 |

---

## 常见问题 FAQ

**Q1: 阿波罗 11 号真的用这些代码登月了吗？**

A：这些代码是 1966-1969 年间由 Margaret Hamilton 团队编写的飞行软件的数字转录版。原始代码以穿线绳芯 ROM 形式固化在硬件里，飞向了月球。这份 GitHub 仓库是 2014 年由 Chris Garry 从 MIT 博物馆的扫描件转录整理而成，内容与飞行版本一致，仓库本身不是飞行件。

**Q2: 我能在我的电脑上运行这些代码吗？**

A：可以。使用 Virtual AGC 模拟器（https://github.com/rburkey2005/virtualagc），可以在现代计算机上运行 Comanche055 或 Luminary099，包括完整的 DSKY 交互界面。

**Q3: AGC 和今天的航天器计算机比如何？**

A：差距巨大。国际空间站的命令计算机使用 Intel 80386SX（约 1 MIPS），比 AGC（约 0.085 MIPS）快约 12 倍；现代深空探测器（如 Orion、Perseverance）使用 RAD750 等抗辐射处理器，性能是 AGC 的数千倍。但 AGC 的设计哲学——优先级调度、故障降级、可预测响应——仍然值得学习。

> ⚠️ 性能对比数据为量级估算，精确倍数取决于比较口径（IPS、MIPS、主频、内存带宽等）。

**Q4: 为什么用汇编而不用高级语言？**

A：1960 年代的高级语言（如 FORTRAN）编译器生成的代码效率不如手写汇编。AGC 的 4KB RAM 和 85K IPS 意味着每条指令都要算成本，编译器无法做到这种级别的优化。直到阿波罗计划后期，部分地面支持软件才开始用高级语言。

**Q5: 1202 报警的完整含义是什么？**

A：1202 表示 "Executive overflow - no core sets"。core set 是 AGC 调度器（Executive）存放待执行任务上下文的结构，数量固定。当所有 core set 都被占用时，新任务无法入队，触发 1202。软件设计允许在过载时丢弃低优先级任务，保留高优先级任务继续执行。1203 是类似但不同的报警："Waitlist overflow - too many tasks"。

**Q6: Luminary 和 Comanche 有什么区别？**

A：Luminary（月球舱软件）需要支持垂直下降、月面操作和独立起飞交汇；Comanche（指令舱软件）更关注跨月飞行导航和大气层再入。两套程序跑在同一型号 AGC 硬件上，但任务阶段、关键算法和 I/O 配置都不同。

---

## 自测题

1. **AGC 的 4KB RAM 和 85K IPS 意味着什么？如何用现代设备类比？**
   - 参考答案：4KB RAM 约为 iPhone 15 的 150 万分之一；85K IPS 约为现代 CPU 的数十亿分之一。这意味着每条指令都要算成本，任何冗余都是奢侈。

2. **为什么 AGC 需要 banking 机制？它是如何工作的？**
   - 参考答案：因为 ROM 有 36,864 字（约 72KB），但 AGC 的地址空间有限，无法一次性寻址所有 ROM。Banking 把 ROM 分成多个 bank，通过切换 bank 来选择要访问的代码段。

3. **1202 报警时，AGC 的软件做了什么让登月没有中止？**
   - 参考答案：AGC 的调度器检测到过载（所有 core set 都被占用），自动丢弃低优先级任务，保留高优先级任务（如姿态控制、导航）继续执行。宇航员看到报警但系统继续工作，最终成功登月。

4. **如果你要设计一个现代嵌入式系统，会从 AGC 借鉴哪些设计思想？**
   - 参考答案：优先级调度 + 过载降级、故障检测与恢复、自检与报警机制、资源约束下的算法优化。这些思想至今适用于 IoT 设备、卫星控制等场景。

5. **为什么 AGC 的源码对今天的程序员还有价值？**
   - 参考答案：它不是怀旧，而是"资源约束下的实时系统"教科书案例。在 4KB RAM 和 85K IPS 的约束下实现优先级调度、故障恢复和实时中断，这些取舍今天依然适用于嵌入式系统。

---

## 进阶路径

### 阶段一：建立概念（1-2 周）
- 目标：理解 AGC 的硬件约束、指令集和软件架构
- 行动：阅读 `ASSEMBLY_AND_OPERATION_INFORMATION.agc` 和 `AGC_BLOCK_TWO_SELF-CHECK.agc`，理解指令集和启动流程
- 验收：能解释 AGC 的 banking 机制、中断处理和优先级调度

### 阶段二：深入模块（2-4 周）
- 目标：理解关键模块的实现（自检、报警、姿态控制、导航）
- 行动：阅读 `ALARM_AND_ABORT.agc`（异常模型）、`PINBALL_GAME_BUTTONS_AND_LIGHTS.agc`（DSKY 交互）、`P63-P67` 程序（登月下降）
- 验收：能解释 1202 报警的完整含义，并跟踪一次登月下降如何流过 AGC

### 阶段三：运行与实验（1 个月）
- 目标：在模拟器上运行 AGC 代码，观察实际行为
- 行动：安装 Virtual AGC 模拟器，加载 Comanche055 或 Luminary099，模拟一次登月任务
- 验收：能在模拟器上触发 1202 报警，并观察调度器如何降级

### 阶段四：现代对比与启发（长期）
- 目标：对比 AGC 与现代嵌入式系统，提炼设计启发
- 行动：阅读 Hamilton 的论文和 NASA 历史报告，对比 AGC 与现代 RTOS（如 FreeRTOS、VxWorks）的设计思想
- 验收：能写出一篇技术分析文章，对比 AGC 与现代嵌入式系统的可靠性设计

**进阶资源**：
- [Virtual AGC 模拟器](https://github.com/rburkey2005/virtualagc)
- [MIT Museum AGC 档案](http://web.mit.edu/museum/)
- [Margaret Hamilton 论文](https://archive.org/details/MargaretHamilton)
- [NASA 技术报告](https://ntrs.nasa.gov/)

---

## 相关资源

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/chrislgarry/Apollo-11 |
| Virtual AGC | http://www.ibiblio.org/apollo/ |
| yaYUL 模拟器 | https://github.com/rburkey2005/virtualagc |
| MIT Museum | http://web.mit.edu/museum/ |
| Margaret Hamilton 采访 | YouTube: Margaret Hamilton - First Woman Software Engineer |

---

**🦞 作者：钳岳星君 | 来源：GitHub chrislgarry/Apollo-11**
