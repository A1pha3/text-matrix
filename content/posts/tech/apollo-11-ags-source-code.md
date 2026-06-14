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

> **目标读者**：计算机历史爱好者、系统程序员、航空航天工程师、对登月技术感兴趣的任何人
> **预计阅读时间**：45-60 分钟
> **前置知识**：对计算机历史有基本了解，知道什么是汇编语言即可（非必需）
> **难度定位**：⭐⭐⭐⭐ 专家设计

---

## §1 学习目标

完成本篇文章后，你将能够：

1. **理解 AGC 的历史地位**：为何这个 16 斤重、4KB 内存的计算机能送人类登月
2. **掌握 AGC 编程风格**：yaYUL 汇编器的语法和 AGC 的特殊指令
3. **理解关键模块**：自检、报警、姿态控制、导航算法
4. **欣赏代码之美**：60 年前的程序员如何用有限资源实现复杂功能
5. **了解历史背景**：Margaret Hamilton 和登月程序员团队的故事
6. **探索源码结构**：如何阅读这个 GitHub 仓库

---

## §2 背景：人类最伟大的工程奇迹

### 2.1 登月的技术挑战

1969 年 7 月 20 日，阿波罗 11 号成功登月。这是人类历史上最伟大的工程成就之一。

**技术挑战**：

| 挑战 | 说明 |
|------|------|
| **实时计算** | 导航、制导、姿态控制需要毫秒级响应 |
| **资源极度受限** | AGC 只有 4KB RAM，处理能力约 0.043 MHz |
| **可靠性要求** | 任何故障都可能导致任务失败和宇航员死亡 |
| **体积重量** | AGC 重量约 32.3kg（70 磅） |

### 2.2 什么是 AGC

**AGC（Apollo Guidance Computer）** 是阿波罗计划的核心：

| 参数 | 值 |
|------|------|
| **重量** | 约 32.3 kg (70 磅) |
| **体积** | 约 0.02 立方米 (2 立方英尺) |
| **RAM** | 4 KB (2,048 字) |
| **ROM** | 36 KB (74,728 字) |
| **时钟频率** | 约 0.043 MHz (43 kHz) |
| **功耗** | 约 55 瓦 |

作为对比：
- iPhone 15 的 RAM 是 AGC 的 **400,000 倍**
- iPhone 15 的处理器速度是 AGC 的 **约 700,000 倍**

### 2.3 Comanche vs Luminary

这个仓库包含两个主要部分：

| 模块 | 目录 | 用途 | 飞船 |
|------|------|------|------|
| **Comanche 055** | `Comanche055/` | 指令舱（Command Module） | 宇航员居住和返回地球 |
| **Luminary 099** | `Luminary099/` | 月球舱（Lunar Module） | 登月和从月面起飞 |

**版本编号含义**：
- Comanche055 = 指令舱 AGC 程序的第 55 次修订
- Luminary099 = 月球舱 AGC 程序的第 99 次修订

---

## §3 AGC 硬件架构

### 3.1 内存系统

**RAM（易失性）**：

```
4 KB = 2,048 个 "字" (word)
每个字 = 16 位 (bits)
```

**ROM（只读）**：

```
36 KB = 74,728 个字
存储程序代码和常量表
```

** Erasable vs. Fixed**：

| 类型 | 用途 | 访问方式 |
|------|------|----------|
| **Erasable (RAM)** | 变量、临时数据 | 可读写 |
| **Fixed (ROM)** | 程序、常量表 | 只读 |

### 3.2 特殊内存区域

**Erasable 内存的子区域**：

| 区域 | 用途 |
|------|------|
| **A** | 通用寄存器 A (Accumulator) |
| **B** | 通用寄存器 B |
| **C** | 通用寄存器 C (LP, Q) |
| **Sandbank** | Super-Bank 位存储 |
| **EBANK** | 特定 Bank 的数据 |

**Banking 系统**：

AGC 的 ROM 被分成多个 1K 字的 "banks"，通过 bank 切换来访问更多内存。

### 3.3 I/O 系统

AGC 通过 I/O 通道与飞船各系统通信：

| 通道 | 功能 |
|------|------|
| **DSKY** | 显示/键盘（宇航员界面） |
| **IMU** | 惯性测量单元 |
| **Engine** | 引擎控制 |
| **Radar** | 雷达系统 |
| **Telecom** | 通信系统 |

---

## §4 yaYUL 汇编器入门

### 4.1 什么是 yaYUL

yaYUL 是开发 AGC 程序使用的汇编器。"YUL" 在希伯来语中意为 "宇宙"，这个名字本身就是对宇宙航天的致敬。

### 4.2 基本语法

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
CA	Q		# CA = Copy A, 将 Q 的内容复制到 A
TS	ALMCADR	# TS = Transfer to Storage, 存储到指定地址
INDEX	Q		# INDEX, 使用 Q 的内容作为间接地址
```

### 4.3 核心指令集

**数据传输指令**：

| 指令 | 全称 | 说明 |
|------|------|------|
| `CA` | Copy A | 将地址内容复制到 A |
| `CS` | Clear and Subtract | 取反后复制到 A |
| `TS` | Transfer to Storage | A 的内容存储到地址 |
| `LXCH` | Exchange with C | 交换 A 和 C |

**算术指令**：

| 指令 | 全称 | 说明 |
|------|------|------|
| `ADD` | Add | A = A + 地址 |
| `ADS` | Add to Storage | 地址 = 地址 + A |
| `DIM` | Decrement and Test | 减一并测试 |
| `DOUBLE` | Double | A = A × 2 |

**逻辑指令**：

| 指令 | 全称 | 说明 |
|------|------|------|
| `MASK` | Mask | 按位与 |
| `AD` | Add | A = A + 地址（带进位） |
| `DXCH` | Double Exchange | 交换 A 和 C 的双精度 |

### 4.4 特殊语法

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

---

## §5 核心代码模块解析

### 5.1 自检模块 (AGC_BLOCK_TWO_SELF-CHECK)

这是 AGC 启动时首先运行的模块：

```assembly
# AGC_BLOCK_TWO_SELF-CHECK.agc

# Page 1
# THIS ROUTINE PERFORMS A CHECK OF THE ERASABLE MEMORY AREAS
# AND THE FIXED MEMORY AREAS.

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

### 5.2 报警模块 (ALARM_AND_ABORT)

**报警是 AGC 处理异常情况的核心机制**：

```assembly
# ALARM_AND_ABORT.agc

# Page 1493
# THE FOLLOWING SUBROUTINE MAY BE CALLED TO DISPLAY A NON-ABORTIVE ALARM
# CALLING SEQUENCE:
#		TC	ALARM
#		OCT	NNNNN		# 报警代码

ALARM		INHINT		# 禁止中断（原子操作）

		CA	Q		# 获取返回地址
ALARM2		TS	ALMCADR		# 存储报警程序地址
		INDEX	Q
		CA	0		# 获取报警代码
BORTENT		TS	L		# 存储到 L (Linkage)
```

**报警代码示例**：

| 代码 | 含义 |
|------|------|
| `OCT 00101` | IMU 未校准 |
| `OCT 00102` | 雷达数据无效 |
| `OCT 00204` | 推进剂不足 |
| `OCT 00504` | 月球表面接触 |

### 5.3 姿态控制 (CM_BODY_ATTITUDE)

**控制飞船在太空中的方向**：

```assembly
# CM_BODY_ATTITUDE.agc

# PURPOSE: TO CONTROL THE ATTITUDE OF THE COMMAND MODULE
# DURING THE ENTRY PHASE OF THE MISSION

		SETLOC	4000
		BANK

RATE-INIT	CA	0		# 读取目标角速率
		TS	OVERB		# 存储过载值
		CA	1		# 读取当前姿态
		TS	CURATT		# 存储当前值
```

### 5.4 导航算法 (ANGLFIND)

**计算飞船在太空中的位置和速度**：

```assembly
# ANGLFIND.agc

# PURPOSE: TO COMPUTE THE ANGLE BETWEEN TWO VECTORS

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

---

## §6 Margaret Hamilton：登月代码女王

### 6.1 传奇人物

**Margaret Hamilton** 是阿波罗计划中最重要的程序员之一：

| 个人信息 | 值 |
|----------|------|
| **出生** | 1936 年 |
| **职位** | 麻省理工学院仪器实验室软件工程部负责人 |
| **团队** | 约 400 名程序员 |
| **登月时职位** | 登月制导软件首席工程师 |

### 6.2 她的贡献

Margaret Hamilton 领导团队编写了阿波罗制导计算机的所有飞行软件：

**关键成就**：
- 提出了 "software engineering" 这个术语
- 编写了 AGC 的核心操作系统和任务调度
- 编写了登月下降和着陆算法
- 编写了应急逃脱系统软件

### 6.3 著名的 1202 报警

1969 年 7 月 20 日，登月前仅剩几分钟时，AGC 触发了 **1202 报警**：

```assembly
# 1202 = "Executive overflow - no jobs"
# 意味着没有足够的 CPU 时间处理所有任务
```

**处理方式**：
- 宇航员 Armstrong 保持冷静，报告 "GO"
- 软件自动重启，排除非必要任务
- 最终成功登月

**Margaret Hamilton 的回忆**：

> "当时没人知道 1202 报警意味着什么。但如果是我们设计之外的任何情况发生，我们就会失败。"

### 6.4 代码中的签名

在源码的 `CONTRACT_AND_APPROVALS.agc` 中，可以看到 Margaret Hamilton 的签名：

```
Submitted by         | Role | Date
:------------------- | :--- | :---
Margaret H. Hamilton | Colossus Programming Leader<br>Apollo Guidance and Navigation | 28 Mar 69
```

---

## §7 如何阅读这个仓库

### 7.1 目录结构

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

### 7.2 阅读建议

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

### 7.3 在线资源

| 资源 | 链接 |
|------|------|
| **Virtual AGC** | http://www.ibiblio.org/apollo/ |
| **MIT Museum** | http://web.mit.edu/museum/ |
| **AGC 文档** | http://www.ibiblio.org/apollo/Schults/ |
| **yaYUL 模拟器** | https://github.com/rburkey2005/virtualagc |

---

## §8 源码编译与运行

### 8.1 Virtual AGC 模拟器

想要实际运行这些代码？可以使用 Virtual AGC 项目：

```bash
git clone https://github.com/rburkey2005/virtualagc.git
cd virtualagc
```

### 8.2 yaYUL 在线编译

MIT 提供了一个在线 yaYUL 编译环境：
- 访问 http://www.ibiblio.org/apollo/ 
- 选择 AGC 或 Luminary 模拟器
- 加载 Comanche055 或 Luminary099

### 8.3 在真实硬件上运行

如果你有 AGC 硬件（或 FPGA 实现），可以：

```bash
# 使用 yaYUL 编译
yaYUL -o output.bin input.agc

# 在 AGC 模拟器中加载
loadAGC output.bin
```

---

## §9 历史意义与启示

### 9.1 软件工程的诞生

Margaret Hamilton 和她的团队不仅编写了代码，更创造了 "software engineering" 这个学科：

**关键实践**：
- **优先级调度**：区分关键任务和次要任务
- **错误恢复**：在故障后自动恢复到安全状态
- **实时响应**：毫秒级中断处理
- **测试驱动**：每个模块都有完整的测试用例

### 9.2 资源约束下的工程智慧

**今天的启发**：

| AGC 约束 | 现代启示 |
|----------|----------|
| 4KB RAM | 优化内存使用，避免内存泄漏 |
| 43 kHz | 算法复杂度永远重要 |
| 55 瓦 | 能效优化在边缘计算中至关重要 |
| 32 kg | 嵌入式系统的体积/重量约束 |

### 9.3 可靠性设计

AGC 的可靠性设计是登月成功的关键：

**故障检测与恢复**：
```assembly
# 如果某个传感器失败，切换到备用传感器
# 如果 CPU 过载，丢弃非关键任务
# 如果内存校验失败，停止并报警
```

---

## §10 常见问题 FAQ

**Q1: 阿波罗 11 号真的用这些代码登月了吗？**

A：不完全是。这些代码是后来从 MIT 博物馆的扫描件转录的。原始代码由 Margaret Hamilton 和她的团队在 1966-1969 年间编写。这份 GitHub 仓库是 2014 年由 Chris Garry 创建的数字版本。

**Q2: 我能在我的电脑上运行这些代码吗？**

A：可以！使用 Virtual AGC 模拟器（https://github.com/rburkey2005/virtualagc），可以在现代计算机上运行 AGC 程序。

**Q3: AGC 和今天的航天器计算机比如何？**

A：差距巨大。国际空间站的计算机比 AGC 快约 100 万倍。但 AGC 的设计哲学——简单、可靠、可预测——仍然值得学习。

**Q4: 为什么用汇编而不是高级语言？**

A：1960 年代的高级语言（如 FORTRAN）效率不如手写汇编。在资源极度受限的情况下，每一条指令都需要优化。

**Q5: 1202 报警的完整含义是什么？**

A：1202 表示 "Executive overflow - no jobs"。这意味着调度器没有可执行的任务。软件设计允许在紧急情况下忽略非关键任务。

**Q6: Luminary 和 Comanche 有什么区别？**

A：Luminary（月球舱软件）需要更多关于垂直下降、月面操作和独立起飞的功能。Comanche（指令舱软件）更关注大气层再入和返回地球。

---

## §11 相关资源

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/chrislgarry/Apollo-11 |
| Virtual AGC | http://www.ibiblio.org/apollo/ |
| yaYUL 模拟器 | https://github.com/rburkey2005/virtualagc |
| MIT Museum | http://web.mit.edu/museum/ |
| Margaret Hamilton 采访 | YouTube: Margaret Hamilton - First Woman Software Engineer |

---

**🦞 作者：钳岳星君 | 来源：GitHub chrislgarry/Apollo-11**
