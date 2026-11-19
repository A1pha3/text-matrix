---
title: "HermesEnabler：一份把「逆向结论」和「已验证事实」严格分开的 Apple Watch 表盘解锁工具"
date: "2026-11-20T01:27:19+08:00"
slug: "pookjw-hermesenabler-verified-reverse-engineering-watch-face"
description: "HermesEnabler 通过修改设备上的 MobileGestalt 缓存 plist 启用 Hermes 表盘。它的技术价值不在绕过本身，而在研究笔记的证据分级：代码 / 静态分析 / 运行时观察三档标注，加上逐构建的偏移量表与 SHA-256 溯源。"
draft: false
categories: ["技术笔记"]
tags: ["iOS", "watchOS", "逆向工程", "MobileGestalt", "研究方法"]
github_repo: "pookjw/HermesEnabler"
source_key: "gh:pookjw/HermesEnabler"
---

## 核心判断

这个项目表面上是一个「在 Apple Watch 上启用爱马仕表盘」的越狱工具。真正值得学的是它**怎么做研究记录**。

`Research/` 目录下每份笔记开头都有一段声明：

> 这些笔记记录的是截至 **2026-11-12** 的 HermesEnabler2 调查，基于 commit `78188c74d284949deb4004a96efa84eb1a7017a2` 和本地保存的真机 watchOS OTA 材料。它们描述的是**观察到的行为**和**那个时间点的实现**；它们**不是 Apple 文档**。

然后是全项目最重要的一条方法论声明：

> **证据标签**：**code** 指当前 app 行为；**静态分析** 指来自真机 OTA 二进制或 device-tree 模板的结论；**运行时观察** 描述一个已陈述的实验及其范围。**一个模板、一次成功构建、或一个匹配的 cache UUID，本身都不构成某个特性或恢复流程在特定真机上可用的证据。**

这句话可以直接搬到任何逆向工程项目里。**「我编译通过了」和「它在目标设备上工作」之间有一道鸿沟**，大多数项目的文档把前者当后者说。HermesEnabler 的笔记全程守着这条线。

需要先说清边界：**这个项目要求侧载（sideload）安装、开启设备开发者模式、并且修改系统级缓存文件。** 它不是 App Store 应用，也不适用于所有设备。仓库自己写着「Use at your own risk」，且明确说**不支持 watchOS 26**，支持范围是 watchOS 27.0 到 27.3 beta 1。

截至 2026 年 11 月 20 日，这个仓库有 2238 stars、189 forks，Objective-C 为主，MIT 许可，2024 年 12 月创建，11 月 19 日仍有更新。

## 它到底做了什么

HermesEnabler2 修改的是设备上的 **MobileGestalt 缓存 plist**。MobileGestalt 是 Apple 用来存设备特性开关的系统配置数据库 —— 表盘、分辨率类别、区域代码这些「这台设备是什么型号/什么档位」的信息都在里面。

缓存有三个相关字段：

| 字段 | 作用 |
|---|---|
| `CacheData` | 二进制数据块，缓存值和存在标记的位置**随构建版本变化** |
| `CacheExtra` | 字典，条目用与 MG key 关联的**不透明标识符** |
| `CacheUUID` | 布局标识符，配合构建号和数据长度用来**拒绝不匹配的缓存** |

笔记里特意澄清了一个常见混淆：

> 这些不透明名字在讨论中有时被称为「加密密钥」。这些笔记称它们为*不透明标识符*：**这里的观察并没有确立其编码算法**。一个值的**逻辑 MG key**、它的 `CacheExtra` 标识符、和它在 `CacheData` 中的条目偏移量，**是三件不同的事**。

不吹「加密」这个听起来更厉害的词，是对的。

## 核心机制：为什么不能只改字典键

研究笔记里有一段解释，是整个项目的技术核心：

> 对于这里研究的面值相关的键，在被调查的配置里，**添加或修改 `CacheExtra` 中的条目不足以可靠控制** `MGCopyAnswer` 返回的对应数值答案。观察到一个通过 `MGCopyAnswer` 取到的值**不等于请求的数值**。

也就是说，改字典不管用。静态分析在 `CacheData` 里找到了 `DeviceBrand` 和 `main-screen-class` 的**数值缓存槽位**。

所以当前实现的做法是：

1. 把四字节小端数值**直接写到 `CacheData` 的指定偏移**；
2. 检查存在标记（presence marker）；
3. 启用时**移除对应的 `CacheExtra` 覆盖**（因为那个覆盖还在生效，会盖掉你写的值）；
4. 写完后**读回校验**。

偏移量**来自真机 OTA 的 `libMobileGestalt.dylib` 描述符表**，不是模拟器缓存。

写之前还会检查构建号、UUID、数据长度和边界。

但笔记立刻补了一句关键限定：

> 这**不是**在说每个 MG key 都需要偏移量。**大多数布尔特性开关现在仍然是通过 `bq_setMGCacheExtraKeys` 写它们的不透明 key 到 `CacheExtra`**。只有备份恢复路径可以额外恢复它们索引化的 `CacheData` 槽位和存在标记。

这是很诚实的范围界定 —— 数值型 key（需要写四字节值 + 移除覆盖）和布尔型 key（写字典就行）走的是两条不同的路。

## 核心机制：逐构建的偏移量表

`HermesEnabler2/MGOffsets.plist` 是权威的机器可读表。表里每行是一个构建版本：

| 构建 | UUID | 长度 | Brand 值/标记 | Screen 值/标记 | Presence base |
|---|---|---|---|---|---|
| `24R363` | `6F8372B0-…` | `0x1947` | `0x348` / `0x16e1` | `0xea8` / `0x184d` | `0x1678` |
| `23R350` | `10ECA820-…` | `0x1842` | `0x320` / `0x15f4` | `0xe00` / `0x1750` | `0x1590` |
| `23S303` | `EB24BEC0-…` | `0x185d` | `0x328` / `0x160d` | `0xe10` / `0x176a` | `0x15a8` |
| `23T240` | `A38A2F0F-…` | `0x189c` | `0x338` / `0x1647` | `0xe30` / `0x17a6` | `0x15e0` |
| `23U95` | `3BE19A76-…` | `0x18a5` | `0x338` / `0x164f` | `0xe38` / `0x17af` | `0x15e8` |
| `24R5315i` | `A4A7B9EC-…` | `0x1947` | `0x348` / `0x16e1` | `0xea8` / `0x184d` | `0x1678` |

**同一代构建共用 UUID 和偏移**（`23R350` / `23R352` / `23R362` 三个共用同一行），但不同的构建世代长度和偏移都不同 —— 这就是为什么 `CacheUUID` 必须参与校验。

选中这些布尔描述符用的是**八字节槽位，位置在 `8 * index`**，存在标记在 `PresenceBase + index`。笔记特别标注：「这在别的构建上必须重新验证。」

## 核心机制：两个数值、两种语义

| 逻辑 key | `CacheExtra` 不透明标识符 | 激活值 | 当前处理 |
|---|---|---|---|
| `DeviceBrand` | `fuKL2rMywRgQF1wowOA/cg` | `1` | 在 `DeviceBrandOffset` 写四字节值；启用时移除这个覆盖 |
| `main-screen-class` | `fdh+s6j3VijuyrK7xLjd7g` | `29`（现有）或 `38`（备选） | 在 `ScreenClassOffset` 写所选四字节值；启用时移除这个覆盖 |

两个关键限定：

> 这些值是**激活覆盖值，不是出厂默认值**。

以及：

> `29` 和 `38` **都不证明**所有表盘 bundle、布局或兼容性检查都会被满足。

### Ultra 表盘那条链：29 → size class 6 → category 4

静态分析的推理链在笔记里写得很完整。对 `24R364`、`24R365`、`24S118`、`24S132`、`24S5091f`、`24S5112a`、`24S5284h` 这些构建，从真机 OTA 里提取的 ClockKit 二进制中，对 `-[CLKDevice _loadDeviceInfo]` 做静态分析发现：

- `main-screen-class` 的 **29 映射到 size class 6**，**38 映射到 size class 9**；
- 类别查找表把这两个 size class 映射到 **4 和 6**；
- 观察到的 `isUltra` 判定 `(category & ~2) == 4` **两个都接受**。

对 `24S5112a` / `Watch7,9` 还给了具体地址：`_loadDeviceInfo` 在 `0x1b7ce6d00`，类别表在 `0x1b7d20128`，判定在 `0x1b7ce7e38`。

**但笔记立刻降级**：

> 这是静态证据；**存在性偏移和真机行为仍未验证**。

以及：

> 这个分类观察**不是**保证任何特定 Ultra 表盘、bundle、伴生图库预览或布局在每个型号上都能工作。

### 溯源：逐构建的 SHA-256

每个检查过的构建都有提取出、slide 处理后的 ClockKit 二进制 SHA-256：

| 构建 | OTA 型号 | SHA-256 |
|---|---|---|
| `24R364` | `Watch7,11` | `8676743b6b1944399ec6416417f4c7777f7fbe5c1327d9b951d1491e055fad8c` |
| `24R365` | `Watch7,11` | `1d7b62f8063e980cdfcbdd9adeeeadd3d09889aeb59e79a9b3c35682eef417c7` |
| `24S118` | `Watch7,11` | `6acef83ea18f2a556dc9652284751d971d43b418bd862382532f8ff2d810fc0e` |
| `24S132` | `Watch7,11` | `908c3d1cf2c8f372af1cf8f2ff5c905be3b0c84b48b240bd5692cdcfa32ae465` |
| `24S5091f` | `Watch7,5` | `96b069b06f58aec8b757a33094412db4accf43ef69b831cdab8bd000c9fae189` |
| `24S5284h` | `Watch8,1` | `06d9fce636d972df52688c19912c1d3ff4590592293193c274f9a9cd5f85875f` |

这让结论**可复现、可证伪**。任何人拿到同样的 OTA 材料，能验证这些哈希对应的二进制是不是同一个。

笔记还提醒哈希的适用边界：「这些哈希是提取产物的，**可能依赖提取或 slide 处理工具**。」

### 38 这条路的来源

`38` 的备选路径基于 [PR #48](https://github.com/pookjw/HermesEnabler/pull/48)，其作者报告在 `Watch7,18` / `24S5284h` 上用 `35 → 38` 得到了 Modular Ultra 和红色夜间模式。

笔记对这段出处做了精确处理：

> 该 PR 的示例**没有被编译进那个 PR**；本实现改编了它的检查和已有的自动备份机制。**我们没有独立复现过它的设备测试。**

这种「引用别人的结论但明确说我们没复现」的写法，在开源逆向项目里并不常见。

## 沙箱逃逸的接口设计

`HermesEnabler2/BQCore.h` 暴露的核心接口，注释写得相当清楚：

```objc
// 逃逸到 `target`（一个 MCM 容器或其中的目录）。成功时返回一个 >= 0 的
// sandbox-extension 句柄，并把 *linkOut 设为一个解析到 `target` 的路径
// （app group 的 Library/Caches 符号链接）。调用 BQEndEscape() 释放并恢复 app group。
int64_t BQEscape(NSString *target, NSString **linkOut);
void BQEndEscape(int64_t handle);

// 实验性的 class-2 父目录回退。默认关闭，因为移动 app 自己的 Library
// 在某些构建上会被沙箱杀掉。仅在 app group 不可用时从 Settings 启用。
BOOL BQClass2ParentEnabled(void);
void BQSetClass2ParentEnabled(BOOL on);
```

三点值得注意：

**一、逃逸是有租约的。** `BQEscape` 返回句柄，`BQEndEscape` 释放并**恢复 app group** —— 这是「借出-归还」模型，不是永久突破。用完就还，异常路径也不至于留下一个敞开的沙箱。

**二、class-2 父目录回退默认关闭**，理由写得很实在：移动 app 自己的 Library 在某些构建上会被沙箱杀掉。**这是个已知有风险的路径，所以要显式开启。**

**三、错误处理独立成域。** `BQErrorDomain` 和 `BQNoSandboxTokenError` 是专门的错误标识。

## 安装

### macOS

两种方式：装预构建 IPA（Sideloadly）或直接用 Xcode 编译。**两者都要求 iPhone 与目标 Apple Watch 已配对，且手表运行受支持的 watchOS 版本。**

Sideloadly 流程的关键点：

1. 从 Releases 下载 IPA，装 Sideloadly，用数据线连 iPhone
2. 拖入 IPA、填 Apple ID，**关闭「Use automatic bundle ID」**，指定固定的 Bundle Identifier，开始签名
3. iPhone 上「设置 → 通用 → VPN 与设备管理」信任开发者证书
4. iPhone 上「设置 → 隐私与安全性 → 开发者模式」开启、重启、确认
5. iPhone 的 Watch App →「我的手表 → App」安装 HermesEnabler2 到手表
6. 手表上「设置 → 隐私与安全性 → 开发者模式」开启、重启、确认
7. 手表上打开 HermesEnabler2，按步骤走

Xcode 路线更简单：打开 `HermesEnabler2.xcodeproj`，选 Apple Watch 作为运行目标，点 Run。

### Windows

用社区工具 [WatchBridge](https://github.com/AdminZachary/iloader-for-windows)（不是 Apple 官方，也不是本项目的一部分）。它需要一个前提：装 iTunes 或 Microsoft Store 的「Apple Devices」应用以获得 **Apple Mobile Device Service**（USB 和 Wi-Fi 通信都依赖它）。

WatchBridge 有个细节做得好：**一次只支持一台已配对手表**，配了多台时准备步骤会**停下**而不是猜。

### 三个必踩的坑

**坑一：IPA 被剥掉 Watch app。** 如果 iPhone app 装上了但手表 app 没出现，查 Sideloadly 日志里的 `Watch apps will be stripped from the IPA` —— 说明内嵌的 Watch app 被移除了，**只装 iPhone app 不会装上它**。这时要用 Xcode 装 Watch app。

**坑二：Bundle ID 必须固定。** 每次更新都用**同一个 Bundle Identifier 和同一个 Apple ID**，app 才能保留已有数据和备份。

**坑三：删 app 前先恢复备份。** README 明确要求：**删除 app 之前，务必通过 HermesEnabler2 app 恢复你的 MobileGestalt 备份。**

另外，开发者模式的准备**需要 USB 连接**。USB 配对过一次之后，安装和续期可以走 Wi-Fi。

## 边界

**这是侧载工具，有真实的操作风险。** 修改系统级缓存、开启设备开发者模式、用自己的 Apple ID 签名 sideload 的 app —— 每一步都有代价。仓库自己写着「Use at your own risk」。

**watchOS 26 完全不支持。** 支持范围是 27.0 – 27.3 beta 1。不在范围内的话官方推荐用另一个项目（Clocky）。

**`DeviceBrand` 的来源是 per-device 的 `syscfg/MkBS`**，通过 `marketing-software-behavior` 分发。笔记特别指出：**一个产品类型的 OTA 并不确立某个具体设备原本是否有爱马仕品牌。** 值 `1` 是激活覆盖，不是安全的通用恢复值。

**改屏幕分类的副作用超出表盘图库。** 笔记直接说：**表盘和复杂功能可能裁切或渲染错误，在更小的物理显示屏上尤其明显。** UI 里也提示：启用 Ultra Faces 会**阻止使用爱马仕 Faubourg Party 表盘**。

**未决问题**（笔记自己列的）：

- 每个物理型号和构建上究竟需要哪些表盘 bundle 和 NanoTimeKit 检查？
- iPhone 的 Watch app 表盘图库是否使用相同的设备属性、是否与手表侧进程同时刷新？
- 改屏幕分类除了 Faubourg Party 不兼容之外还引起什么交互？
- 能否在各种屏幕尺寸和运行时显示变体上独立验证原始 `main-screen-class`？

**图库预览失败仍未解决。**

**隐私提醒**：笔记要求**永远不要**把设备的 MobileGestalt 备份、区域、序列号或其它设备特定数据作为研究报告的一部分发布。

## 采用顺序

1. **先读 `Research/README.md`**，理解三档证据标签。**不理解这个方法论，后面的内容你没法正确评估。**
2. **确认你的 watchOS 版本在支持范围内**（27.0 – 27.3 beta 1），且你的构建号在 `MGOffsets.plist` 里有对应行。**没有对应行就说明偏移量未知，别试。**
3. **先读 `Research/Recovery/README.md`**，搞清楚恢复流程和备份机制。**在改任何东西之前，你得先知道怎么改回去。**
4. **用 Xcode 路线**而不是 Sideloadly —— 至少你能看到真实的构建和错误输出，不会被 IPA 剥包坑到。
5. **先备份，再改。** 记录你的原始构建号、UUID、缓存值和做的每一步改动。
6. **改完重启手表**，让消费方重新加载。Carousel（表盘轮播）也需要重启才会读到新值。
7. **测试时记录完整矩阵**：实际手表型号、构建号、原始缓存、确切改动、重启动作、以及表盘在哪里可见。笔记明确要求了这一点。

## 排查：按现象定位

| 现象 | 先查这里 |
|---|---|
| iPhone app 装上了但手表没有 | 查 Sideloadly 日志的 `Watch apps will be stripped from the IPA`；改用 Xcode 装 Watch app |
| 手表上没有「开发者模式」选项 | 先装 Watch app，再回来看 |
| 更新后数据丢了 | Bundle Identifier 或 Apple ID 变了；必须固定 |
| 改了值但表盘没出现 | 先确认构建号在 `MGOffsets.plist` 里有对应行；写的是**激活覆盖值不是出厂默认**，`29`/`38` 都不保证所有 bundle 和兼容性检查都满足 |
| 启用了 Ultra 后 Faubourg Party 表盘消失 | **这是已知的不兼容**，UI 里也会提示 |
| 表盘或复杂功能显示错乱 | 改屏幕分类的已知副作用，小屏上更明显 |
| 需要恢复原值 | 通过 HermesEnabler2 app 恢复 MobileGestalt 备份；**删 app 前务必先恢复** |
| WatchBridge 报多台手表 | 它一次只支持一台；配多台时会停下而不是猜 |
| Windows 上 WatchBridge 起不来 | 缺 Apple Mobile Device Service（装 iTunes 或 Apple Devices）；WebView2 在 Win11 已内置 |
| 想知道某个构建到底分析出了什么 | `Research/WatchFaces/README.md` 有逐构建的偏移、地址和 SHA-256 |

## 参考

- 仓库：<https://github.com/pookjw/HermesEnabler>
- 研究笔记入口：<https://github.com/pookjw/HermesEnabler/tree/main/Research>
- 偏移量表：<https://github.com/pookjw/HermesEnabler/blob/main/HermesEnabler2/MGOffsets.plist>
- 默认值表：<https://github.com/pookjw/HermesEnabler/blob/main/HermesEnabler2/MGDefaults.plist>
- 致谢来源：<https://github.com/sasobhabha/Gester>
- 关联研究项目：<https://github.com/forcequitOS/worse_query>（沙箱逃逸方向）、<https://github.com/blacktop/ipsw>（OTA 分析工具）
