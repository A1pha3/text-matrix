---
title: "Windows 环境下 Discord 与 YouTube 的 DPI 穿透工具：从原理到实战的完整指南"
date: "2026-05-02T15:03:48+08:00"
slug: "zapret-discord-youtube-windows-dpi-bypass-guide"
description: "zapret-discord-youtube 是一款专为 Windows 平台打造的 DPI（深度包检测）穿透工具，聚焦解决 Discord 语音聊天与 YouTube 访问受限问题。本文从 DPI 工作原理出发，深入解析 nfqws/winws 的多策略去同步（DPI Desync）机制，涵盖 general*.bat 策略体系、service.bat 服务管理、游戏过滤器与 IPSet 过滤器的架构设计，并提供从安装配置、实战调试到自定义策略开发的完整路径。"
draft: false
categories: ["技术笔记"]
tags: ["DPI", "Windows", "Discord", "YouTube", "网络代理", "zapret", "WinDivert"]
---

# Windows 环境下 Discord 与 YouTube 的 DPI 穿透工具：从原理到实战的完整指南

## 学习目标

读完本文后，你将掌握：

1. **DPI（深度包检测）的运作机制**以及它为何能阻断特定网络连接
2. **掌握 zapret 的 DPI Desync（去同步）原理**，了解 fake、multisplit 等攻击手法的本质区别
3. **正确安装并配置 zapret-discord-youtube**，包括 Secure DNS 的必要性
4. **根据实际网络环境选择合适的策略文件**（ALT 系列、FAKE TLS 系列等）
5. **熟练使用 service.bat 进行服务管理**、诊断与故障排除
6. **根据自身网络情况自定义策略文件**，扩展屏蔽列表

---

## 一、背景与问题域

### 1.1 什么是 DPI，为什么它会挡住你

DPI（Deep Packet Inspection，深度包检测）是一种运行在网络运营商侧的系统，它不仅读取数据包的头部信息（源 IP、目标 IP、端口），还深入检查数据包的载荷（payload），甚至分析 TCP/UDP 流的上下文。

对于 HTTP/HTTPS 流量，DPI 可以看到 TLS 握手阶段 ClientHello 中的 SNI（Server Name Indication）字段，从而在加密通道建立之前就判断出你要访问的目标域名。YouTube 的 IP 段、Discord 的网关服务器 IP 和 CDN 域名都属于常见的"不希望用户访问"的目标，DPI 可以在不解密 HTTPS 的情况下完成识别与拦截。

更激进的做法是**连接重置**（RST 注入）：DPI 发现违规请求后，向客户端和服务器双方注入伪造的 TCP RST（Reset）包，导致连接被强制中断。另一种做法是**TLS 握手干扰**：在 ClientHello 中植入伪造的 ALPN（Application-Layer Protocol Negotiation）值或修改 SNI，使服务器端 TLS 握手失败。

**zapret 项目**（原始仓库 bol-van/zapret）正是针对这类 DPI 而设计。其核心思路不是加密流量（VPN），而是**故意发送 DPI 无法正确解析的畸形或分段请求**，让 DPI 的状态机陷入混乱，从而放弃拦截。这种方法的优点是不需要任何代理服务器，属于纯本地方案。

### 1.2 zapret-discord-youtube 的定位

Flowseal/zapret-discord-youtube 是面向 Windows 普通用户的**开箱即用分发版**，将 zapret 核心（winws.exe + WinDivert）与 Discord / YouTube 的屏蔽列表和预调好的策略文件打包在一起。原始 zapret 项目面向 Linux 路由器，需要手动编译和配置；本项目则通过 `general*.bat` 一键策略切换、`service.bat` 可视化服务管理，大幅降低了使用门槛。

该项目 Star 数接近 2.7 万（截至 2026 年 5 月），Fork 数超过 2100，是同类项目中社区活跃度最高的 Windows DPI bypass 工具之一。

### 1.3 系统要求

| 组件 | 要求 |
|------|------|
| 操作系统 | Windows 10/11（64 位） |
| 权限 | 管理员权限（启动时自动请求） |
| 网络 | ISP 使用 DPI 进行流量审查的环境 |
| 前置条件 | 启用 Secure DNS（见下一节） |

> ⚠️ **兼容性说明：** Windows 7 用户需要从 [zapret-win-bundle/win7](https://github.com/bol-van/zapret-win-bundle/tree/master/win7) 获取专用版 WinDivert 驱动文件（带数字签名）才能正常加载。Windows 7 已经不受微软支持，建议升级。

---

## 二、原理分析：DPI Desync 机制详解

### 2.1 DPI 的基本工作流程

以访问 YouTube 为例，一个正常握手的简化流程：

1. 客户端发送 TCP SYN → 服务器
2. 服务器回复 SYN-ACK → 客户端
3. 客户端发送 ACK，同时发起 TLS ClientHello，其中包含 SNI=`www.youtube.com`
4. DPI 设备在第 3 步读取到 SNI，查表发现 youtube.com 在屏蔽列表，发射 TCP RST 同时给两端
5. 客户端收到 RST，连接被掐断

步骤 3 是关键：**TLS 握手本身是明文的**（只是后续通信加密），SNI 字段以明文编码在 ClientHello 中。DPI 靠这个字段就能完成识别，不需要解密。

### 2.2 nfqws / winws 的核心：TCP 分段攻击（TCP Segmentation）

zapret 核心程序在 Linux 上叫 `nfqws`（NFQUEUE + ws），在 Windows 上对应 `winws.exe`（Windows Service 的缩写）。其核心原理是**修改 TCP 分段的序号和载荷，让 DPI 无法拼凑出完整的 HTTP/TLS 请求头**。

#### 2.2.1 TCP 多段分割（Multisplit）

正常情况下，一个 HTTP 请求会这样发送：

```
[ TCP Segment 1 ] GET / HTTP/1.1\r\nHost: www.youtube.com\r\n
[ TCP Segment 2 ] User-Agent: Mozilla/5.0\r\n...
```

`nfqws/winws` 将其改写为：

```
[ TCP Segment 1 ] GET /
[ TCP Segment 2 ]  HTTP/1.1\r\nHost: www.youtube.com\r\n...
```

注意第二段以**空格开头**，而不是继续第一段的文本。第一段末尾没有完整的 HTTP 语义，DPI 在看到第一段时无法判断这是 HTTP 请求（它只看到 `GET /`），看到第二段时序号已经不对（DPI 试图重组时会发现 sequence number mismatch）。DPI 的重组逻辑要么漏过这段流量，要么产生解析错误，从而放弃拦截。

 `--dpi-desync=multisplit` 参数控制这个行为，`--dpi-desync-split-seqovl` 和 `--dpi-desync-split-pos` 控制分段的起始位置和 sequence overlap 长度。

#### 2.2.2 伪造包攻击（Fake）

Fake 模式不依赖 TCP 分段，而是向客户端或服务器方向**主动注入一个伪造的 QUIC/TLS 响应包**。

以 QUIC 为例：客户端发出初始包（Initial Packet），DPI 看到目标端口是 443/UDP，就知道这是 QUIC 流量。`winws.exe` 可以注入一个伪造的 QUIC 握手响应，让 DPI 误以为服务器已经回复，状态机推进到"连接已建立"，从而停止分析。

```
--dpi-desync=fake
--dpi-desync-fake-quic=<path-to-quic_initial.bin>
--dpi-desync-repeats=6
```

`--dpi-desync-repeats=6` 表示发送 6 个伪造包，确保 DPI 有足够的机会接收到伪造响应。配合精心构造的二进制载荷文件（`.bin`），可以让 DPI 误判协议类型或版本。

#### 2.2.3 分段位置与 Sequence Overlap

```
--dpi-desync-split-seqovl=681
--dpi-desync-split-pos=1
--dpi-desync-split-seqovl-pattern=<path-to-tls_clienthello.bin>
```

- `split-pos=1`：从数据载荷的第 1 个字节处开始分割（0-based index）
- `split-seqovl=681`：在序号空间中重叠 681 个字节，使 DPI 的重组缓冲产生混乱
- `pattern` 参数指定一个预录制的 TLS ClientHello 模板，用于填充伪造分段的实际内容

### 2.3 为什么需要"策略"这个概念

没有万能策略。不同 ISP 的 DPI 实现版本不同（华为、ZTE、中兴、思科等），对 TCP 分段的容忍度和重组算法各异。同一个 multisplit 参数，在运营商 A 可能完美绕过，在运营商 B 可能完全无效。

因此 zapret-discord-youtube 提供了大量预设策略文件（`general*.bat`），每一种对应不同的 DPI 攻击组合：

| 策略文件 | 核心手段 | 适用场景 |
|----------|----------|----------|
| `general (SIMPLE FAKE).bat` | 纯 fake QUIC | DPI 版本老，fake 最省力 |
| `general (FAKE TLS AUTO).bat` | Fake TLS 握手自动检测 | 较新 DPI，TLS 层拦截 |
| `general (ALT).bat` | 多策略组合 ALT | 中等复杂度 DPI |
| `general (ALT10).bat` | ALT 变体 | 难搞的 ISP |
| `general (FAKE TLS AUTO ALT3).bat` | Fake TLS + ALT3 组合 | 最顽固的 DPI |

> 💡 **实操经验**：大多数中国用户反馈 `FAKE TLS AUTO ALT3` 或 `ALT10` 在 2025 年后仍有较高成功率，但需要多试几个版本，因为 ISP 的 DPI 会持续升级。

### 2.4 WinDivert 的角色

`nfqws` 在 Linux 上依赖 iptables + NFQUEUE，将特定流量拦截到用户态处理。Windows 没有 iptables，WinDivert 承担了相同职责：**在 Windows 驱动层（WFP）注册回调，截获符合条件的网络数据包，交给 winws.exe 处理后放行或丢弃**。

```
WinDivert64.sys  ←── 内核驱动（数字签名加载）
WinDivert.dll    ←── 用户态动态库
winws.exe        ←── zapret 核心逻辑
```

WinDivert 驱动是整个系统的底层枢纽。由于它是一个通用的流量过滤驱动，部分杀毒软件会将其识别为"潜在有害程序"（PUP，Potentially Unwanted Program）。**WinDivert 本身不是病毒**，它只是一个流量挂钩工具——是否用于绕过 DPI 完全取决于调用它的上层程序。将 zapret 目录加入杀毒软件白名单是标准操作。

---

## 三、架构分析

### 3.1 文件结构

解压后的 zapret-discord-youtube 目录结构：

```
zapret-discord-youtube/
├── general.bat                          # 默认策略（最通用）
├── general (ALT).bat                   # ALT 系列策略
├── general (ALT2~ALT11).bat            # ALT 进阶变体
├── general (FAKE TLS AUTO ALT).bat      # FAKE TLS + ALT 组合
├── general (SIMPLE FAKE ALT).bat        # 简化 fake + ALT
├── service.bat                         # 服务管理脚本（菜单界面）
├── bin/
│   ├── winws.exe                       # zapret Windows 核心程序
│   ├── WinDivert64.sys                 # 内核驱动（64位）
│   ├── WinDivert.dll                   # 用户态库
│   ├── cygwin1.dll                      # Cygwin 兼容层
│   ├── quic_initial_www_google_com.bin  # Google QUIC 伪造包
│   ├── quic_initial_dbankcloud_ru.bin  # Discord QUIC 伪造包
│   ├── stun.bin                         # STUN 伪造包
│   └── tls_clienthello_*.bin            # TLS ClientHello 模板
├── lists/
│   ├── list-general.txt                # 通用屏蔽域名列表
│   ├── list-google.txt                  # Google/YouTube 专用列表
│   ├── list-exclude.txt                # 排除域名列表
│   ├── ipset-all.txt                   # 已知被屏蔽的 IP 段列表
│   ├── ipset-exclude.txt               # IP 排除列表
│   └── *-user.txt                     # 用户自定义列表（首次运行后生成）
└── utils/
    ├── targets.txt                     # 测试目标 URL 列表
    ├── check_updates.enabled           # 自动更新标志文件
    └── test zapret.ps1                 # PowerShell 测试脚本
```

### 3.2 流量处理流程

当用户执行 `general (ALT).bat` 时，实际发生的调用链路：

```
general (ALT).bat
  ├── service.bat status_zapret    （检查 zapret 服务状态）
  ├── service.bat check_updates    （检查更新，若 check_updates.enabled 存在）
  ├── service.bat load_game_filter （加载游戏过滤器端口范围）
  └── bin/winws.exe --wf-tcp=... --wf-udp=...
                              │
                              ▼
                    WinDivert64.sys（WFP 驱动）
                              │
                              ▼
                    匹配 list-general.txt / list-google.txt
                              │
                              ▼
                    注入 DPI Desync 攻击（multisplit / fake）
                              │
                              ▼
                    放行/修改后的数据包 → 到达目标服务器
```

### 3.3 策略文件的内部结构

以 `general.bat` 为例，关键参数解析：

```batch
@echo off
chcp 65001 > nul

cd /d "%~dp0"
call service.bat status_zapret
call service.bat check_updates
call service.bat load_game_filter
call service.bat load_user_lists

set "BIN=%~dp0bin\"
set "LISTS=%~dp0lists\"
cd /d %BIN%

start "zapret: %~n0" /min "%BIN%winws.exe" --wf-tcp=80,443,2053,2083,2087,2096,8443,%GameFilterTCP% --wf-udp=443,19294-19344,50000-50100,%GameFilterUDP% ^
--filter-udp=443 --hostlist="%LISTS%list-general.txt" --hostlist="%LISTS%list-general-user.txt" --hostlist-exclude="%LISTS%list-exclude.txt" --hostlist-exclude="%LISTS%list-exclude-user.txt" --ipset-exclude="%LISTS%ipset-exclude.txt" --ipset-exclude="%LISTS%ipset-exclude-user.txt" --dpi-desync=fake --dpi-desync-repeats=6 --dpi-desync-fake-quic="%BIN%quic_initial_www_google_com.bin" --new ^
--filter-udp=19294-19344,50000-50100 --filter-l7=discord,stun --dpi-desync=fake --dpi-desync-fake-discord="%BIN%quic_initial_dbankcloud_ru.bin" --dpi-desync-fake-stun="%BIN%quic_initial_dbankcloud_ru.bin" --dpi-desync-repeats=6 --new ^
--filter-tcp=2053,2083,2087,2096,8443 --hostlist-domains=discord.media --dpi-desync=multisplit --dpi-desync-split-seqovl=681 --dpi-desync-split-pos=1 --dpi-desync-split-seqovl-pattern="%BIN%tls_clienthello_www_google_com.bin" --new ^
--filter-tcp=443 --hostlist="%LISTS%list-google.txt" --ip-id=zero --dpi-desync=multisplit --dpi-desync-split-seqovl=681 --dpi-desync-split-pos=1 --dpi-desync-split-seqovl-pattern="%BIN%tls_clienthello_www_google_com.bin" --new ^
--filter-tcp=80,443 --hostlist="%LISTS%list-general.txt" --hostlist="%LISTS%list-general-user.txt" --hostlist-exclude="%LISTS%list-exclude.txt" --hostlist-exclude="%LISTS%list-exclude-user.txt" --ipset-exclude="%LISTS%ipset-exclude.txt" --ipset-exclude="%LISTS%ipset-exclude-user.txt" --dpi-desync=multisplit --dpi-desync-split-seqovl=568 --dpi-desync-split-pos=1 --dpi-desync-split-seqovl-pattern="%BIN%tls_clienthello_4pda_to.bin" --new ^
--filter-udp=443 --ipset="%LISTS%ipset-all.txt" --hostlist-exclude="%LISTS%list-exclude.txt" --hostlist-exclude="%LISTS%list-exclude-user.txt" --ipset-exclude="%LISTS%ipset-exclude.txt" --ipset-exclude="%LISTS%ipset-exclude-user.txt" --dpi-desync=fake --dpi-desync-repeats=6 --dpi-desync-fake-quic="%BIN%quic_initial_www_google_com.bin" --new ^
--filter-tcp=80,443,8443 --ipset="%LISTS%ipset-all.txt" --hostlist-exclude="%LISTS%list-exclude.txt" --hostlist-exclude="%LISTS%list-exclude-user.txt" --ipset-exclude="%LISTS%ipset-exclude.txt" --ipset-exclude="%LISTS%ipset-exclude-user.txt" --dpi-desync=multisplit --dpi-desync-split-seqovl=568 --dpi-desync-split-pos=1 --dpi-desync-split-seqovl-pattern="%BIN%tls_clienthello_4pda_to.bin" --new ^
--filter-tcp=%GameFilterTCP% --ipset="%LISTS%ipset-all.txt" --ipset-exclude="%LISTS%ipset-exclude.txt" --ipset-exclude="%LISTS%ipset-exclude-user.txt" --dpi-desync=multisplit --dpi-desync-any-protocol=1 --dpi-desync-cutoff=n3 --dpi-desync-split-seqovl=568 --dpi-desync-split-pos=1 --dpi-desync-split-seqovl-pattern="%BIN%tls_clienthello_4pda_to.bin" --new ^
--filter-udp=%GameFilterUDP% --ipset="%LISTS%ipset-all.txt" --ipset-exclude="%LISTS%ipset-exclude.txt" --ipset-exclude="%LISTS%ipset-exclude-user.txt" --dpi-desync=fake --dpi-desync-repeats=12 --dpi-desync-any-protocol=1 --dpi-desync-fake-unknown-udp="%BIN%quic_initial_dbankcloud_ru.bin" --dpi-desync-cutoff=n2
```

每个 `--new` 分隔一个独立的**策略阶段**（stage），每个 stage 可以有独立的协议过滤条件和 DPI desync 方式。这种设计允许对不同类型的流量（UDP QUIC、TCP Discord Media、TLS Google）应用不同的攻击策略。

### 3.4 service.bat 的菜单系统

`service.bat` 提供了一个交互式菜单，包含以下功能模块：

| 选项 | 功能 | 关键文件 |
|------|------|----------|
| 1. Install Service | 将选中策略注册为 Windows 自启动服务 | `sc create zapret binPath=...` |
| 2. Remove Services | 卸载 zapret + WinDivert 服务 | `sc delete zapret && sc delete WinDivert` |
| 3. Check Status | 查看 zapret / WinDivert 运行状态 | `sc query zapret`, `tasklist` |
| 4. Game Filter | 切换游戏/高端口 UDP+TCP 过滤器 | `utils/game_filter.enabled` |
| 5. IPSet Filter | 切换 `ipset-all.txt` 的加载模式（none/loaded/any） | `lists/ipset-all.txt` |
| 6. Auto-Update Check | 开关自动更新检查 | `utils/check_updates.enabled` |
| 7. Update IPSet List | 从 GitHub 拉取最新的 ipset 列表 | `.service/ipset-service.txt` |
| 8. Update Hosts File | 修复 Telegram Web 和 Discord 语音 | `.service/hosts` |
| 9. Check for Updates | 检查 zapret-discord-youtube 新版本 | `version.txt` |
| 10. Run Diagnostics | 运行全套兼容性诊断 | PowerShell 多项检查 |
| 11. Run Tests | 运行 `test zapret.ps1` 脚本进行策略有效性测试 | `utils/test zapret.ps1` |

---

## 四、安装配置

### 4.1 前置条件：Secure DNS

**这一步必不可少，且必须在启动 zapret 之前完成。**

DPI 有时候也会截获 DNS 查询（UDP 53 明文）。即使流量被 zapret 保护，DNS 请求本身也可能泄露你想访问的真实域名。最简单的方法是启用 DoH（DNS over HTTPS）：

**Chrome：**
1. 设置 → 隐私和安全 → 安全
2. 启用"使用安全 DNS"
3. 选择提供商（不要选 Cloudflare，选 Google：`https://dns.google/dns-query`）

**Firefox：**
1. 设置 → 隐私与安全 → DNS over HTTPS
2. 选择"最大保护"，手动输入 `https://dns.google/dns-query`

**Windows 11：**
1. 设置 → 网络 → 网络属性 → DNS 设置
2. 选择"编辑" → 改为 `https://dns.google/dns-query`

> 💡 Windows 10 不支持系统级 DoH，需要在浏览器层面配置。Windows 11 用户可以在系统设置中一步到位。

### 4.2 下载与解压

1. 前往 [Releases 页面](https://github.com/Flowseal/zapret-discord-youtube/releases/latest) 下载最新版本的 zip 或 rar 压缩包
2. 下载完成后，右键点击压缩文件 → 属性 → **勾选"解除锁定"**（Windows 安全机制，防止从互联网下载的文件被执行）
3. 如果使用 7-Zip 或 PeaZip 解压，第 2 步可以跳过（这些解压工具不受 Windows Zone Identifier 限制）
4. **解压路径中不能包含中文字符、空格或特殊符号**。推荐路径：`C:\zapret\` 或 `D:\zapret\`

```
❌ C:\Users\用户名\下载\zapret（中文用户名 + 空格）
❌ D:\我的工具\zapret（中文路径）
✅ C:\zapret\（推荐）
✅ D:\zapret-discord-youtube\
```

### 4.3 首次运行策略

1. 双击任意 `general*.bat` 文件（建议从 `general.bat` 或 `general (FAKE TLS AUTO).bat` 开始）
2. 系统会弹出"用户账户控制（UAC）"提示，点击"是"授权管理员权限
3. 等待数秒，任务栏右下角会出现一个小锁图标（winws.exe 的托盘图标）
4. 打开浏览器，访问 YouTube 和 Discord，检查是否正常

### 4.4 策略试错

不同策略针对不同 ISP DPI 版本。如果默认 `general.bat` 无效，依次尝试：

```
general (SIMPLE FAKE).bat
general (FAKE TLS AUTO).bat
general (ALT).bat
general (ALT2).bat ... ALT11
general (FAKE TLS AUTO ALT3).bat
```

> 试错时每次只开一个策略文件，不要同时运行两个策略。如果不确定哪个有效，先关掉当前的（关掉任务栏中的 winws.exe 锁图标或结束进程），再启动新的。

### 4.5 安装为系统服务（开机自启）

当某个策略确认有效后，想要开机自动启动：

1. 双击 `service.bat`
2. 输入 `1`（Install Service）
3. 选择要自启动的策略编号（会列出目录下所有 `general*.bat`）
4. 等待服务创建完成，提示成功后按 Enter 返回菜单
5. 下次开机时，zapret 会自动在后台运行

卸载自启：`service.bat` → 输入 `2`（Remove Services）。

---

## 五、实战演示

### 5.1 场景：Discord 语音频道一直卡在"正在连接"

**问题现象**：Discord 文字功能正常，但加入语音频道时一直显示"正在连接"或"重新连接"。

**排查步骤：**

1. **确认 DNS 是否已配置 Secure DNS**（参照 4.1 节）
2. 运行 `service.bat` → 输入 `8`（Update Hosts File）
   - 如果提示需要更新，手动将显示的内容追加到系统 `hosts` 文件末尾
   - `hosts` 文件路径：`C:\Windows\System32\drivers\etc\hosts`
   - 用管理员权限的记事本打开并编辑
3. 尝试不同的策略（如 `ALT2`、`ALT5`、`FAKE TLS AUTO ALT3`）
4. 如果仍不行，运行 `service.bat` → 输入 `10`（Run Diagnostics）
   - 查看是否有 AdguardSvc.exe（Adguard 会干扰 Discord UDP 语音）
   - 确认 WinDivert 服务是否正常加载

**原理说明**：Discord 语音使用基于 UDP 的 SRTP（Secure Real-time Transport Protocol），端口范围 19294-19344 和 50000-50100。`general.bat` 的第二个策略阶段专门针对这些 UDP 端口注入 fake QUIC 响应。如果你的 ISP DPI 对 QUIC 有特殊处理，这个阶段就会失效，换用 ALT 系列往往有效。

### 5.2 场景：YouTube 播放卡在"正在加载"或直接打不开

**问题现象**：YouTube 首页能打开，但视频播放时一直转圈。

**排查步骤：**

1. **先确认 Secure DNS 已启用**
2. **关闭浏览器广告拦截插件**。YouTube 官方从 2024 年起开始与广告拦截器对抗，某些情况下会导致播放异常
3. 尝试 `general (ALT).bat` → `general (ALT6).bat` 系列
4. 确认 Game Filter 未意外开启（`service.bat` → `4` → 选择 `0. Disable`）
5. 运行 `service.bat` → `10`（Run Diagnostics），检查 hosts 文件是否被污染

**原理说明**：YouTube 视频流主要走 QUIC（UDP 443）和 HTTP/2（TCP 443）。`general.bat` 的第四阶段针对 `list-google.txt` 中的域名使用 multisplit + `--ip-id=zero` 参数，将 IP ID 置零用于对抗某些 DPI 的序号追踪。不同 ISP 对 IP ID 的检查策略不同，切换 ALT 变体可以找到适合的参数组合。

### 5.3 场景：玩网络游戏时掉线或延迟升高

**问题现象**：开启 zapret 后，特定游戏出现高延迟、掉线或无法连接服务器。

**问题原因**：zapret 默认会对所有匹配规则的 UDP 高端口进行 DPI desync 处理，包括游戏客户端使用的 UDP 端口。

**解决方案：**

1. `service.bat` → `4`（Game Filter）
2. 选择游戏端口过滤模式：
   - `0. Disable`：完全关闭游戏过滤器（所有 UDP 流量不经过 zapret 处理）
   - `1. TCP and UDP`：对所有 1024 以上端口启用过滤
   - `2. TCP only`：只过滤 TCP 高端口
   - `3. UDP only`：只过滤 UDP 高端口
3. 修改后需要重启 zapret 策略（关闭并重新打开对应的 general*.bat）

> ⚠️ 如果游戏仍然有问题，同时将 `service.bat` → `5`（IPSet Filter）切换为 `none` 模式，这样只有明确在 `list-general.txt` 和 `list-google.txt` 中的域名会受到保护，其他所有 IP 都不会被拦截。

### 5.4 Run Tests：验证策略有效性

`service.bat` → `11`（Run Tests）会启动 PowerShell 测试脚本 `utils/test zapret.ps1`，该脚本会依次检测：

- **Standard tests**：用 `utils/targets.txt` 中的 URL 列表测试 HTTP/HTTPS 连通性
- **DPI checkers**：探测当前 ISP 的 DPI 类型与能力

测试结果会显示哪些 URL 可达、哪些 DPI 检查点触发了拦截，为选择策略提供客观依据。

---

## 六、开发扩展

### 6.1 添加自定义域名

编辑 `lists/list-general-user.txt`（首次运行后自动生成），每行一个域名：

```
myproblem-domain.example
another-site.com
*.wildcard.example.com  <!-- 通配符可自动匹配子域名 -->
```

重启当前策略（关掉 winws.exe 并重新打开对应的 `general*.bat`）即可生效。

### 6.2 添加自定义 IP 段

编辑 `lists/ipset-exclude-user.txt`，添加不需要 zapret 处理的 IP 段（即使它们在 `ipset-all.txt` 中）：

```
203.0.113.0/24
198.51.100.5
```

> 格式：`ipset-exclude-user.txt` 与 `ipset-all.txt` 中的项互斥：ipset 是"需要处理的 IP"，exclude 是"从 ipset 中排除的 IP"。

### 6.3 排除特定域名

如果某个域名匹配了 `list-general.txt` 中的规则但你不想让它走 zapret，添加到 `lists/list-exclude-user.txt`：

```
bank.example.com
work-internal.example.com
```

### 6.4 自定义策略参数

如果预设策略都无法满足你的 ISP，可以参考 zapret 原始文档的参数说明，基于某个现有的 `general*.bat` 进行修改。

关键参数速查：

| 参数 | 含义 | 常用值 |
|------|------|--------|
| `--dpi-desync=fake` | 注入伪造响应包 | `fake`, `multisplit`, `synack`, `syndata` |
| `--dpi-desync-repeats=N` | 伪造包发送次数 | 6-12 |
| `--dpi-desync-fake-quic=<bin>` | QUIC 伪造包文件路径 | `quic_initial_www_google_com.bin` |
| `--dpi-desync-split-seqovl=N` | 分段重叠字节数 | 568, 681 |
| `--dpi-desync-split-pos=N` | 分段起始位置（字节偏移） | 1 |
| `--dpi-desync-split-seqovl-pattern=<bin>` | TLS ClientHello 模板 | `tls_clienthello_*.bin` |
| `--ip-id=zero` | 将 IP ID 字段置零 | `zero`, `rand` |
| `--dpi-desync-any-protocol=1` | 对任意协议启用 desync（不只 HTTP/TLS） | 0, 1 |
| `--filter-l7=<protocol>` | 第 7 层协议过滤（winws 扩展） | `discord`, `stun` |

更多参数请参阅 [bol-van/zapret 官方文档](https://github.com/bol-van/zapret/blob/master/docs/readme.md#nfqws)。

### 6.5 与 GoodbyeDPI 的对比

| 维度 | zapret-discord-youtube | GoodbyeDPI |
|------|----------------------|------------|
| 多策略支持 | ✅ 大量预设 + 自定义 | ❌ 仅内置几种模式 |
| Windows 服务化 | ✅ service.bat 一键安装 | ⚠️ 手动注册服务 |
| Discord 语音 | ✅ 专用 UDP 处理 | ⚠️ 有限 |
| 游戏过滤 | ✅ Game Filter 模式 | ❌ |
| IPSet 支持 | ✅ 大量 IP 段列表 | ❌ |
| 维护活跃度 | ✅ 持续更新 | ⚠️ 维护放缓 |

---

## 七、常见问题速查

| 问题 | 最可能原因 | 解决方式 |
|------|-----------|----------|
| 启动 `general*.bat` 后任务栏没有出现锁图标 | `bin/` 目录未正确解压，或 winws.exe 被杀毒软件拦截 | 检查 bin/ 目录完整性；将整个 zapret 目录加入白名单 |
| Discord 文字频道可用，但语音一直"正在连接" | hosts 文件未更新；或 DPI 对 QUIC 拦截策略较新 | 运行 `service.bat` → `8` 更新 hosts；换用 ALT5 以上策略 |
| YouTube 视频转圈加载不出来 | Secure DNS 未配置；广告拦截插件干扰 | 配置 DoH；暂时禁用广告拦截插件 |
| zapret 运行后游戏掉线/高延迟 | Game Filter 意外开启；IPSet 意外加载 | `service.bat` → `4` 禁用；`5` 设为 none |
| 某策略曾经有效，突然失效 | ISP DPI 更新了检测算法 | 尝试其他 ALT 策略；关注 GitHub Releases 更新 |
| 杀毒软件报 WinDivert 为病毒 | 正常现象 | 将 WinDivert64.sys 和 winws.exe 加入排除列表 |
| 运行诊断提示 Base Filtering Engine 未运行 | Windows 防火墙服务未启动 | 运行 `services.msc` 启动 `Base Filtering Engine` 服务 |

---

## 八、总结

zapret-discord-youtube 并不是一个"科学上网"工具，而是一个**精准的 DPI 对抗工具**。它做到三件事：

1. **不需要代理服务器**，纯本地处理，对网络延迟的影响极小
2. **高度可配置**，通过策略组合和用户列表扩展，可以适应不同国家和地区的 DPI 实现差异
3. **开源透明**，所有二进制文件的来源在 GitHub 上可查证哈希，防止被篡改

如果你正面临 Discord 语音不通、YouTube 无法加载、或类似场景下的网络问题，在确认 DNS 配置正确后，zapret-discord-youtube 是最值得尝试的解决方案。按照本文的流程从安装、策略试错到自定义配置，大多数问题都能在 30 分钟内得到解决。
