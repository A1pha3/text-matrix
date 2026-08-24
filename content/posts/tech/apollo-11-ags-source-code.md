---
title: "Apollo-11：阿波罗11号制导计算机源码探秘——人类登月的编程遗产"
date: "2026-04-16T01:20:00+08:00"
slug: "apollo-11-ags-source-code"
github_repo: "chrislgarry/Apollo-11"
description: "Apollo-11 是保存 1969 年登月制导计算机（AGC）源码的 GitHub 仓库，55K+ Stars。详解 Comanche055（指令舱）与 Luminary099（月球舱）两套汇编程序，以及 Margaret Hamilton 等人的在 4KB RAM 约束下的软件工程取舍。"
draft: false
categories: ["技术笔记"]
tags: ["汇编", "嵌入式系统", "航空航天", "历史"]
---

# Apollo-11：阿波罗 11 号制导计算机源码探秘——人类登月的编程遗产

GitHub 仓库 [chrislgarry/Apollo-11](https://github.com/chrislgarry/Apollo-11) 保存了 1969 年人类登月时阿波罗制导计算机（AGC）的源码，截至 2026 年 8 月累计约 70,600 Stars、7,900 Forks，语言标记为 Assembly。仓库由 Chris Garry 于 2014 年把 MIT 博物馆的扫描件转录整理而成，最近一次提交停在 2023 年——它是一份历史档案，不是活跃维护的项目。

这份代码以 AGC 汇编写成，包含 Comanche055（指令舱）和 Luminary099（月球舱）两套程序，共约 110,000 行。它的价值不在怀旧，而在把"优先级调度、故障恢复、实时中断"三件事放进同一台飞行计算机，并且真的飞到了月球。在 4KB RAM、85K IPS 的约束下，工程师必须决定哪些任务要毫秒级响应、哪些可以丢弃、哪些重启后必须接着跑。这套取舍至今仍是嵌入式与航天软件的底色。

理解 AGC 源码，先分清三组关系：硬件约束如何塑造指令集和内存模型；Comanche 与 Luminary 两套程序如何分工；以及 1202 报警那几分钟里软件做了什么，让登月没有中止。

读完这篇文章，你能回答几个此前未必说得清的问题：为什么 AGC 的指令要分基础集和解释性指令集两套；为什么 4KB 内存能跑下一套实时操作系统；1201 和 1202 到底各自代表调度器的哪种过载。下文先从一张总览表铺开两套程序的边界，再逐层拆开硬件、汇编器、核心模块，用一个具体的登月下降案例把它们串起来，最后落到你能直接上手阅读仓库、用模拟器复现的路径。

## 总览地图：两套程序，一台计算机

| 维度 | Comanche055 | Luminary099 |
|------|-------------|-------------|
| 所在飞船 | 指令舱（Command Module, CM） | 月球舱（Lunar Module, LM） |
| 目录 | `Comanche055/` | `Luminary099/` |
| 核心任务 | 跨月飞行导航、再入大气层、返回地球 | 登月下降、月面停留、从月面起飞交汇 |
| 关键阶段 | 发射、地月转移、月轨、再入 | 下降、着陆、上升、交汇对接 |
| 版本号含义 | 指令舱程序第 55 次修订 | 月球舱程序第 99 次修订 |
| 代码量 | 约 50,000 行 AGC 汇编 | 约 60,000 行 AGC 汇编 |

两套程序跑在同一型号 AGC 硬件上，任务阶段不同、关键算法不同。Comanche 的难点在再入大气层——再入走廊很窄，角度偏高会被弹回太空，偏低则会在稠密大气中烧毁；Luminary 的难点在登月下降——从月轨到月面要在约 12 分钟内把速度从约 1.7 km/s 降到 0，同时避开障碍。

### AGC 硬件参数一览

| 参数 | 值 | 对照物 |
|------|------|--------|
| 字长 | 15 位 + 1 奇偶位 | 现代 CPU 通常 64 位 |
| RAM（Erasable） | 2,048 字 ≈ 4 KB | iPhone 15 标准版 6 GB，约 150 万倍 |
| ROM（Fixed） | 36,864 字 ≈ 72 KB | 一张中等分辨率 JPEG 约 100 KB |
| 主时钟 | 2.048 MHz | iPhone 15 A16 CPU 约 3.46 GHz，约 1,700 倍 |
| 指令执行速率 | 约 85,000 IPS | 现代 CPU 约数十亿 IPS |
| 重量 | 约 31.75 kg（70 磅） | — |
| 功耗 | 约 55 W | 一盏白炽灯泡 |

> 时效声明：iPhone 对照数据基于 2023 年发布的 iPhone 15 标准版公开规格；AGC 数据来自 NASA 历史档案与 Virtual AGC 项目文档。不同来源对 AGC 时钟频率的表述有差异（部分科普文章写作 0.043 MHz 或 43 kHz，实际指主时钟 2.048 MHz 分频后的某个内部节拍），本文采用 Virtual AGC 项目维护的 Block II 硬件手册数据。

---

## 登月的技术挑战与 AGC 的位置

1969 年 7 月 20 日，阿波罗 11 号成功登月。AGC 是全程参与制导与控制的唯一一台数字计算机。

| 挑战 | 说明 | AGC 的应对 |
|------|------|-----------|
| 实时计算 | 导航、制导、姿态控制需要毫秒级响应 | 优先级调度 + 硬件中断 |
| 资源极度受限 | 4KB RAM，85K IPS | 手写汇编，每条指令都算过成本 |
| 可靠性要求 | 任何故障都可能使任务失败、宇航员丧生 | 自检、报警、故障恢复、冗余设计 |
| 体积重量 | 飞船载荷有限 | 31.75 kg，55 W 功耗 |

1960 年代的地基计算机一台就要占一个房间。飞船上的计算机必须同时满足三个条件：小到能装进飞船、低到能用电池、可靠到重启不起就得接着用。MIT 仪器实验室（Instrument Laboratory，后改名 Draper Laboratory）从 1961 年开始为 AGC 做设计，最终交付的 Block II 是第一台使用集成电路的量产计算机。

AGC 不是通用计算机。它只做一件事：把飞船从 A 点送到 B 点，并在出问题时让宇航员有机会接管。这个定位决定了它的指令集、内存模型和软件架构——所有设计都围绕"实时、可靠、可恢复"展开。

---

## AGC 硬件架构

### 内存系统：Erasable 与 Fixed

AGC 把内存分成两类，这个区分直接影响了汇编编程风格。

| 类型 | 物理介质 | 用途 | 访问方式 |
|------|----------|------|----------|
| Erasable（RAM） | 磁芯存储 | 变量、临时数据、寄存器 | 可读写 |
| Fixed（ROM） | 穿线绳芯存储 | 程序代码、常量表 | 只读 |

```
Erasable: 4 KB = 2,048 个 "字"（word），每个字 16 位（1 位奇偶 + 15 位数据）
Fixed:    36 KB = 36,864 个字，存储程序代码和常量表
```

1960 年代半导体 RAM 还不可靠。磁芯在断电后仍能保留数据，且对辐射有天然抗性。Fixed 内存用穿线绳芯（wire-rope core rope）——靠导线穿过磁环的方式永久编码 0 和 1，一旦穿好就不可改写，但密度比磁芯高得多，可靠性也更高。

### 特殊内存区域

Erasable 内存的前若干字被分配给寄存器和系统状态。

| 区域 | 用途 |
|------|------|
| A | 累加器（Accumulator），所有算术指令的中心 |
| L | 链接寄存器（Link），存放下一条指令地址或乘法低位 |
| Q | 返回地址寄存器（Quarter），子程序调用用 |
| Z | 程序计数器（Zero） |
| EBANK | Erasable Bank 选择寄存器，决定当前访问哪个 erasable bank |
| FBANK | Fixed Bank 选择寄存器，决定当前访问哪个 fixed bank |
| Sandbank | Super-Bank 位存储，扩展 fixed 寻址 |

### Banking 系统：用 12 位地址访问 36 KB

AGC 的指令地址只有 12 位，最多直接寻址 4K 字，但 Fixed 内存有 36K 字。解法是 banking：把内存切成多个 1K 或 2K 字的 bank，通过 EBANK/FBANK 寄存器选择当前 bank。

这意味着同一条 `CA 02000` 指令在不同 bank 设置下会读到完全不同的内存位置。汇编程序员必须时刻知道"我现在在哪个 bank"，否则会读到错误的指令或数据。yaYUL 汇编器的一大职责就是帮程序员管理 bank 切换，但最终代码里仍会出现大量 `BANK`、`EBANK=`、`SETLOC` 指令。

### I/O 通道：与飞船对话

AGC 通过 I/O 通道（channel）与飞船各系统通信，外设寄存器映射到通道端口，每个通道是一个 16 位端口。通道分配在指令舱（Comanche）与月球舱（Luminary）之间并不相同，权威依据是仓库里的 `INPUT_OUTPUT_CHANNEL_BIT_DESCRIPTIONS.agc`。以下为月球舱（Luminary099）的常用分配：

| 通道 | 功能 | 方向 |
|------|------|------|
| 3-4 | 时间计数器（HISCALAR/LOSCALAR），任务计时 | 输入 |
| 5-6 | RCS 姿态喷口控制（俯仰/滚转） | 输出 |
| 10-11 | DSKY 显示、报警与状态灯（OUT0/DSALMOUT） | 输出 |
| 12-14 | IMU 控制、雷达、发动机万向节 | 输出 |
| 15 | DSKY 键盘输入（MNKEYIN） | 输入 |
| 16 | 光学标记与导航面板输入（NAVKEYIN） | 输入 |
| 30-33 | 雷达状态、推进器状态、温度等硬件监测 | 输入 |

I/O 通道是 AGC 实时性的关键。IMU 与雷达数据通过输入通道送入，AGC 用硬件中断响应；姿态与推进指令从输出通道下发。同一套接口在不同任务阶段被复用，程序通过通道编号与位定义区分用途。

---

## yaYUL 汇编器

AGC 的指令集与任何现代 CPU 都不同，地址空间被 banking 切碎，还有大量特殊指令（如 `EXTEND` 前缀、`INDEX` 间接寻址），通用汇编器处理不了。yaYUL 是 Virtual AGC 项目为现代开发者提供的汇编器，能把 `.agc` 源文件编译成可加载的 rope 镜像。"YUL" 在希伯来语中意为"宇宙"。

### 基本语法

```assembly
# 这是单行注释
```

```assembly
ALARM		INHINT		# "ALARM" 是一个标签，指向这条指令
```

```assembly
CA	Q		# CA = Clear and Add，清空 A 并加上 Q 的内容到 A
TS	ALMCADR	# TS = Transfer to Storage，把 A 存到 ALMCADR
INDEX	Q		# INDEX，用 Q 的内容作为下一条指令的地址修改
```

> 原仓库注释把 `CA` 写作 "Copy A" 是常见误传。AGC 手册中 `CA` 全称是 "Clear and Add"：先清空累加器 A，再加上内存地址的内容。这与"复制"语义不同——`CA` 会触发溢出检测，而单纯的复制不会。

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

```assembly
		BLOCK	02		# 声明这个代码属于 Block 2
```

```assembly
		SETLOC	FFTAG7		# 设置后续代码的地址
```

```assembly
		BANK		# 进入当前 bank
```

```assembly
		EBANK=	FAILREG		# 设置 EBANK（用于访问 erasable bank）
```

这些伪指令是 yaYUL 管理 banking 的方式。`SETLOC` 决定代码在内存中的物理位置，`BANK` 和 `EBANK=` 决定运行时访问哪个 bank。看懂这些指令是阅读 AGC 源码的前提。

---

## 核心代码模块解析

### 自检模块（AGC_BLOCK_TWO_SELF-CHECK）

文件头的功能描述比任何教程都清楚：

```text
# PROGRAM HAS TWO MAIN PARTS. THE FIRST IS SELF-CHECK WHICH RUNS AS A ZERO
# PRIORITY JOB WITH NO CORE SET, AS PART OF THE BACK-UP IDLE LOOP. THE SECOND
# IS SHOW-BANKSUM WHICH RUNS AS A REGULAR EXECUTIVE JOB WITH ITS OWN STARTING
# VERB.
#     THE PURPOSE OF SELF-CHECK IS TO CHECK OUT VARIOUS PARTS OF THE COMPUTER...
#     IN ALL THERE ARE 7 POSSIBLE OPTIONS IN THIS BLOCK.
```

SELF-CHECK 以零优先级任务的身份挂在后备空闲循环里，不占用 core set；SHOW-BANKSUM 则作为普通 Executive 任务运行，可由动词启动。它按选项逐一检查内存与计算机各部件，故障时点亮对应指示。这个"空闲时间做自检、不干扰关键任务"的思路，今天在航天器和汽车 ECU 里依然常见。

### 报警模块（ALARM_AND_ABORT）

报警是 AGC 处理异常情况的核心机制。Luminary099 的 `ALARM_AND_ABORT.agc` 文件头写明了调用约定：

```assembly
# CALLING SEQUENCE IS AS FOLLOWS:
#     TC   ALARM
#     OCT  AAANN
# ALARM NO. NN IN GENERAL AREA AAA.
# (RETURNS HERE)
		BLOCK	02
		SETLOC	FFTAG7
		BANK
		EBANK=	FAILREG
ALARM		INHINT
		CA	Q
ALARM2		TS	ALMCADR
		INDEX	Q
		CA	0
BORTENT		TS	L
```

调用方 `TC ALARM` 后在紧跟的一个字里放报警代码 `AAANN`：AAA 是报警所属区域，NN 是区域内编号。`INHINT` 先关中断，保证报警处理不会被中途打断；返回地址暂存在 Q，随后换入 L 继续处理。

报警分两类：non-abortive（非中止性）只提醒宇航员，任务可以继续；abort（中止性）会进入中止流程。下文中 1201/1202 属于非中止性报警——这正是任务控制中心判断"可以继续"的前提。

### 姿态计算（CM_BODY_ATTITUDE）

这个模块在指令舱再入大气层时计算姿态。进入解释性指令后，它把 IMU/CDU 的角度换算成再入需要的姿态角：

```assembly
CM/POSE		TC	INTPRET
		SETPD	VLOAD
			0
			VN		# KVSCALE = (12800/ .3048) /2VS
		VXSC	PDVL
			-KVSCALE
			UNITW
		VXV	VXSC		# VREL = V - WE*R
			UNITR
			KWE
		VAD	STADR
		STORE	-VREL
```

`TC INTPRET` 让 CPU 进入解释性指令执行模式：这一层指令（VLOAD、VXV、VAD 等）直接操作向量，配套的 `SETPD`/`STORE` 管理伪堆栈（PD list），再配合 `ARCCOS`、`SIN`、`COS` 等例程做三角运算。再入时 AGC 以固定周期读取 IMU 数据、更新姿态角并输出控制指令，整个循环周期不能漂移，否则控制就会失稳。

### 导航算法（ANGLFIND）

`ANGLFIND.agc`（Colossus 2A，即 Comanche055）做的事情是：由当前与目标姿态的方向余弦矩阵，求出要转过的角度和旋转轴。关键几步：

```assembly
# CALCULATE AM AND PROCEED ACCORDING TO ITS MAGNITUDE
		DLOAD	DAD
			MFI
			MFI +16D
		DSU	DAD
			DP1/4TH
			MFI +8D
		STORE	CAM		# CAM = (MFI0+MFI4+MFI8-1)/2 HALF SCALE
		ARCCOS
		STORE	AM		# AM=ARCCOS(CAM)  (AM SCALED BY 2)
		DSU	BPL
			MINANG
			CHECKMAX
		EXIT			# MANEUVER LESS THAN 0.25 DEG
```

注意这里没有 `MP`/`ADD` 这类基础指令——数学全在解释性指令层完成。AGC 有两套指令：基础指令集（34 条，含 `CA`、`TS` 及 `EXTEND` 扩展）负责控制流与数据搬运；解释性指令集（`INTPRET` 进入，含 `VLOAD`、`DLOAD`、`ARCCOS`、`SQRT` 等）负责向量与三角运算，数据在伪堆栈（PD list）里流转。AGC 没有硬件浮点单元，所有三角与开方都靠解释性例程里的定点算法完成，注释里的 `SCALED BY 2`、`HALF SCALE` 就是程序员手工维护的定点比例尺。

这段代码求出姿态机动（attitude maneuver）的角度与转轴，是再入、对接前的姿态调整的基础。

---

## 任务流案例：一次登月下降如何流过 AGC

静态看模块清单，很难理解 AGC 各部分如何配合。下面用登月下降阶段（P63 程序）把硬件、I/O、调度和算法串起来。

### 下降阶段的 12 分钟

登月下降从月球轨道开始，到月面着陆结束，约 12 分钟。这 12 分钟里，AGC 完成以下工作：

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

下降阶段开始后不久，AGC 连续触发了 5 次报警（4 次 1202、1 次 1201）。问题出在调度器，与导航或制导算法本身无关：交会雷达（rendezvous radar）作为中止预案一直保持通电，但它的角度转换电路与 AGC 的 800 Hz 参考信号相位不一致，产生了一连串虚假的计数请求，通过"周期窃取"（cycle stealing）消耗掉约 13% 的 CPU 时间。下降程序本来就把处理器跑得很满，这个额外负载把 Executive 推过了极限——没有空闲 core set 时报 1202，没有空闲 VAC（向量累加器区）时报 1201。

调度器在过载时丢弃低优先级任务、保留高优先级任务，避免崩溃。下降阶段的导航和制导是最高优先级，所以即使报警反复触发，关键计算仍在继续。机组成员在 DSKY 上看到报警代码，飞船响应正常，地面的 "GO" 也随之传来。

AGC 的可靠性体现在出错后仍能完成关键功能。这是今天谈"韧性工程"（resilience engineering）时仍在引用的经典设计。

---

## Margaret Hamilton 与登月软件工程

### 人物背景

**Margaret Hamilton** 是阿波罗计划中最重要的程序员之一。她 1936 年出生，在麻省理工学院仪器实验室担任软件工程部负责人，登月时是制导软件首席工程师。据 NASA Johnson Space Center Oral History Project 与 MIT Museum 档案，MIT 仪器实验室软件团队总规模约 350 人，Hamilton 直接领导的核心团队约数十人。不同来源对"团队规模"的定义（含不支持人员与否）有差异，此处采用广义口径。

### 她的贡献

Margaret Hamilton 领导团队编写了阿波罗制导计算机的所有飞行软件：

- 最早在 NASA 项目中系统使用 "software engineering" 一词，并推动软件作为独立工程学科被认可
- 编写 AGC 的核心操作系统和任务调度（Executive）
- 编写登月下降和着陆算法
- 编写应急逃脱系统软件

> 术语归属："software engineering" 一词的最早使用有多个候选（1965 年 NATO 会议记录、Hamilton 在 1966 年的项目备忘录等）。Hamilton 是最早在航空航天项目里把这个词落到工程实践的人之一，"发明"一词的归属在学术界有争议。

### 1202 报警的现场还原

1969 年 7 月 20 日，登月前仅剩几分钟时，AGC 触发了 **1202 报警**：

```
1202 = "Executive overflow - no core sets"
意味着调度器没有可用的核心集来排队新任务
```

> 原文与部分科普文章把 1202 解释为 "no jobs"，这是不准确的。AGC 错误代码表（来自 Virtual AGC 项目文档）明确写作 "Executive overflow - no core sets"。core set 是 AGC 调度器存放待执行任务上下文的结构，数量固定；当所有 core set 都被占用时，新任务无法入队，触发 1202。

处理过程：地面飞控在十几秒内做出判断——制导数据仍然连续、计算机在两次报警之间能自行恢复，于是由 Capcom Charlie Duke 向机组传达 "GO"；软件自动重启、排除非关键任务；最终成功登月。

**Margaret Hamilton 的回忆**：

她后来多次讲述这段经历，大意是：没人事先见过 1202，但软件里"过载时降级、保留关键任务"的设计，正是为这种没有排练过的情况准备的；如果当时需要处理的是设计之外的意外，任务很可能就失败了。

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
├── Comanche055/          # 指令舱源码（Colossus 2A）
│   ├── AGC_BLOCK_TWO_SELF-CHECK.agc   # 自检
│   ├── ANGLFIND.agc                   # 姿态机动角计算
│   ├── CM_BODY_ATTITUDE.agc           # 再入姿态计算
│   └── ...                            # 约一百多个 .agc 文件
├── Luminary099/          # 月球舱源码（Luminary 1A）
│   ├── ALARM_AND_ABORT.agc            # 报警与中止
│   ├── INPUT_OUTPUT_CHANNEL_BIT_DESCRIPTIONS.agc  # I/O 通道位定义
│   ├── PINBALL_GAME_BUTTONS_AND_LIGHTS.agc        # DSKY 交互
│   └── ...
└── README.md
```

### 阅读建议

从 `ASSEMBLY_AND_OPERATION_INFORMATION.agc` 开始。这个文件包含 AGC 编程的完整手册：指令集详解、内存布局、I/O 通道定义、编程约定。

**主要模块分类**：

| 类别 | 示例文件 | 说明 |
|------|----------|------|
| 系统 | `AGC_BLOCK_TWO_SELF-CHECK.agc` | 自检启动 |
| 异常处理 | `ALARM_AND_ABORT.agc` | 报警系统 |
| 导航 | `ANGLFIND.agc`, `ORIENTATION.agc` | 导航算法 |
| 引擎 | `ENGINFL1.agc`, `THROTTLE.agc` | 引擎控制 |
| 雷达 | `RADAR_LEADIN.agc`, `R12.agc` | 雷达接口 |
| 显示 | `DISPLAY_INTERFACE.agc` | DSKY 交互 |

阅读顺序：先读 `ASSEMBLY_AND_OPERATION_INFORMATION.agc` 建立指令集概念，再读 `AGC_BLOCK_TWO_SELF-CHECK.agc` 看启动流程，然后读 `ALARM_AND_ABORT.agc` 理解异常模型，最后按任务阶段（下降、上升、再入）选读对应模块。

### 在线资源

| 资源 | 链接 |
|------|------|
| Virtual AGC | http://www.ibiblio.org/apollo/ |
| MIT Museum | http://web.mit.edu/museum/ |
| AGC 文档 | http://www.ibiblio.org/apollo/Schults/ |
| yaYUL 模拟器 | https://github.com/rburkey2005/virtualagc |

---

## 源码编译与运行

### Virtual AGC 模拟器

```bash
git clone https://github.com/rburkey2005/virtualagc.git
cd virtualagc
```

Virtual AGC 项目维护着 AGC 模拟器、yaYUL 汇编器、DSKY 模拟器以及完整的构建工具链。clone 下来后按 README 编译即可在现代 PC 上跑 Comanche055 或 Luminary099。

### yaYUL 在线编译

Virtual AGC 项目提供在线运行环境：访问 http://www.ibiblio.org/apollo/，选择 AGC 或 Luminary 模拟器，即可加载 Comanche055 或 Luminary099，在浏览器里看到 DSKY 面板。

### 用 yaYUL 重新编译

进入 Virtual AGC 的 `yaYUL/` 目录按 README 构建后，`yaYUL` 以 `.agc` 源码为输入、输出可加载的 rope 镜像；命令行参数随版本略有差异，以项目文档为准。想零成本体验的话，用上面的在线环境更快。

---

## 历史意义与现代启示

### 软件工程从 AGC 开始成形

Margaret Hamilton 和她的团队不仅编写了代码，更让 "software engineering" 进入了工程实践：

- **优先级调度**：区分关键任务和次要任务，过载时丢弃低优先级
- **错误恢复**：在故障后自动恢复到安全状态，避免直接停机
- **实时响应**：毫秒级中断处理，控制循环周期稳定
- **测试驱动**：每个模块都有完整的测试用例，飞行前在模拟器上跑过完整任务剖面

这些今天看是常识，但在 1960 年代，"软件"还不被当作工程对象。Hamilton 团队把软件当作和硬件一样需要规格、评审、测试和签名的工程产物。

### 资源约束下的工程智慧

| AGC 约束 | 当时的应对 | 对今天的启发 |
|----------|----------|----------|
| 4KB RAM | 手写汇编，复用寄存器，bank 切换 | 嵌入式系统、IoT 设备的内存优化思路 |
| 85K IPS | 算法复杂度严格控制，查表代替计算 | 实时系统的算法选型依然重要 |
| 55 W 功耗 | 硬件逻辑分担计算，软件只做必要工作 | 边缘计算、电池供电设备的能效设计 |
| 31.75 kg | 集成电路密度提升，穿线绳芯 ROM | 嵌入式系统的体积/重量约束 |

### 可靠性设计

AGC 的可靠性设计是登月成功的关键。三条规则对应三个机制：传感器冗余切换、调度器过载降级、自检模块。1202 报警就是第二条规则的实际触发。

```assembly
如果某个传感器失败，切换到备用传感器
如果 CPU 过载，丢弃非关键任务
如果内存校验失败，停止并报警
```

---

## 采用建议与进一步学习

### 谁该读这份代码

- **嵌入式系统工程师**：AGC 是"资源约束下的实时系统"的教科书案例，比读现代 RTOS 文档更能理解为什么要有优先级继承、为什么调度器要能降级。
- **航空航天与卫星开发者**：AGC 的故障恢复模型（restart with state preservation）至今影响深空探测器的软件架构。
- **系统程序员**：AGC 的 banking、I/O 通道、中断处理是理解"计算机架构如何塑造软件形态"的样本。
- **技术管理者**：Hamilton 团队的工程实践（规格、评审、测试、签名）是软件工程早期方法论的重要参考。

### 阅读路径建议

1. **第一遍（1-2 小时）**：只读 `ASSEMBLY_AND_OPERATION_INFORMATION.agc` 和 `AGC_BLOCK_TWO_SELF-CHECK.agc`，建立指令集和启动流程的概念。
2. **第二遍（3-5 小时）**：读 `ALARM_AND_ABORT.agc` 和 `PINBALL_GAME_BUTTONS_AND_LIGHTS.agc`（DSKY 交互），理解异常模型和人机界面。
3. **第三遍（10+ 小时）**：按任务阶段选读。对登月感兴趣就读 Luminary099 的 `P63-P67` 程序，对再入感兴趣就读 Comanche055 的 `ENTRY` 程序。

### 什么时候不必深读

- 只做 Web 或移动应用开发的人，AGC 的具体指令集和 banking 机制对日常工作帮助有限，读一遍历史背景和 1202 报警案例就够。
- 已经在做现代 RTOS 项目的人，AGC 的设计思想已经隐含在用，深读源码的边际收益递减，建议读 Hamilton 的论文和 NASA 历史报告，比直接读汇编更高效。

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

> 性能对比数据为量级估算，精确倍数取决于比较口径（IPS、MIPS、主频、内存带宽等）。

**Q4: 为什么用汇编而不用高级语言？**

A：1960 年代的高级语言（如 FORTRAN）编译器生成的代码效率不如手写汇编。AGC 的 4KB RAM 和 85K IPS 意味着每条指令都要算成本，编译器无法做到这种级别的优化。直到阿波罗计划后期，部分地面支持软件才开始用高级语言。

**Q5: 1202 报警的完整含义是什么？**

A：1202 表示 "Executive overflow - no core sets"。core set 是 AGC 调度器（Executive）存放待执行任务上下文的结构，数量固定：月球舱有 7 个 core set、5 个 VAC（向量累加器）区，指令舱为 6 个 core set。当所有 core set 都被占用时，新任务无法入队，触发 1202；当调度请求还需要 VAC 区而 VAC 区也耗尽时，则触发 1201。软件设计允许在过载时丢弃低优先级任务，保留高优先级任务继续执行。1203 是类似但不同的报警："Waitlist overflow - too many tasks"。

**Q6: Luminary 和 Comanche 有什么区别？**

A：Luminary（月球舱软件）需要支持垂直下降、月面操作和独立起飞交汇；Comanche（指令舱软件）更关注跨月飞行导航和大气层再入。两套程序跑在同一型号 AGC 硬件上，但任务阶段、关键算法和 I/O 配置都不同。

---

## 相关资料口径与来源说明

本文基于 Apollo-11 仓库（[chrislgarry/Apollo-11](https://github.com/chrislgarry/Apollo-11)）公开源码整理，以下边界需要说明：

1. **源码时效性**：这份源码是 1969 年的原始代码，已经过去 50 多年，仅供历史研究和学习使用。
2. **技术准确性**：AGC 的硬件架构和编程模型已经过时，不适用于现代嵌入式系统开发。
3. **历史背景**：本文对 AGC 的历史意义和软件工程遗产的解读基于公开资料，可能存在不同观点。
4. **学习价值**：AGC 源码的主要价值在于理解在极度受限环境下的软件设计思想，而不是直接复制其技术。

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