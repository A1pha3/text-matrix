+++
github_repo = "francescopace/espectre"
source_key = "gh:francescopace/espectre"
date = '2026-06-09T21:07:02+08:00'
lastmod = '2026-10-04T00:00:00+08:00'
draft = false
title = '从 ESPHome 组件到 Wi-Fi 感知平台：espectre 四个月复盘'
slug = 'espectre-wifi-csi-motion-detection-esp32'
description = 'espectre（francescopace/espectre）把一块约 10 欧元的 ESP32 变成无摄像头、无麦克风的本地 Wi-Fi 动检传感器。发文四个月后，项目从单一 ESPHome 组件长成感知平台：四条固件路线（ESPHome / Native / Matter / Micro-ESPectre）、C++ SDK 上架 ESP Component Registry、浏览器工具链与 CLI、GPLv3 + 商业双许可；检测器整体换代——Gain Lock 与 NBVI 退役，MVS / ML 更名 Lightweight / High Accuracy，改用增益不变特征与时间时隙调度。9,462 stars（2026-10-04 读数）。'
categories = ['技术笔记']
tags = ['Home Assistant', '智能家居', '隐私', '开源']
+++

# 从 ESPHome 组件到 Wi-Fi 感知平台：espectre 四个月复盘

> 本文首发于 2026-06-09，当时项目最新版本是 v2.8.0，形态是"一个 ESPHome 组件 + 一个 Python 研发端"。2026-10-04 复核时，espectre 已经走到 v3.0.0-rc3，仓库、检测器、部署方式全部换代。正文按双时点写：先讲现在是什么，再讲四个月里换了什么，涉及已退役机制的地方明确标注 v2 口径（原文留档见 [2.8.0 tag](https://github.com/francescopace/espectre/blob/2.8.0/README.md)）。

espectre（GitHub：[francescopace/espectre](https://github.com/francescopace/espectre)，官网 [espectre.dev](https://espectre.dev)）是 Francesco Pace 在 2025 年 10 月 26 日建仓开发的 Wi-Fi CSI 动检系统，GPL-3.0。它做的事一句话能说完：用一块约 10 欧元的 ESP32 开发板，检测房间里有没有人在动——不装摄像头、不装麦克风、不戴任何设备、数据不出内网。

四个问题决定了它和 PIR 传感器、毫米波雷达、摄像头的区别：

- **穿墙**：Wi-Fi 信号穿墙，传感器不必与被监测区域通视；
- **无可识别采集**：CSI（信道状态信息）只反映无线电信道的物理特征，不含图像、语音、人脸。毫米波雷达能从微多普勒谱推算呼吸心率，摄像头采集的是生物特征，CSI 采集的是信道统计——三者暴露面不同；
- **零云端**：检测全部在设备上完成，README 明言 "Nothing needs to go to the cloud"；
- **成本**：一块开发板 + 家里现成的 2.4 GHz 路由器，没有订阅费。

## 一、当前读数与版本状态

| 指标 | 数值 |
|---|---|
| 仓库 | [francescopace/espectre](https://github.com/francescopace/espectre) |
| Stars / Forks | 9,462 / 716（2026-10-04 API 读数；发文时为 8,019 / 626） |
| 主语言 | C++（固件与 SDK）+ Python（工具链、训练、Micro-ESPectre） |
| 许可证 | GPLv3，另有面向闭源固件的商业许可（见第六节） |
| 创建时间 | 2025-10-26 |
| 最近推送 | 2026-10-03（持续活跃） |
| 最新正式版 | 2.8.0（2026-05-21） |
| 预发布线 | 3.0.0-rc1（09-05）、rc2（09-16）、rc3（09-26），正式版进行中 |
| 支持芯片 | ESP32、S2、S3、C3、C5、C6 |
| 检测档 | Lightweight（默认）/ High Accuracy |
| 检测输出 | 运动概率 0.0–1.0，二值 IDLE / MOTION |

它不能做的事同样要摆在前面：不识别人数、身份、姿态、动作类型，不能证明房间是空的，官方 README 原话是 "does not identify people, count them, prove that a room is empty, or replace a safety-certified security, medical, or emergency system"。

## 二、四个月里发生了什么：从组件到平台

发文时的 espectre 是"双平台"仓库：`components/espectre/` 放 ESPHome C++ 组件，`micro-espectre/` 放 Python 研发端，根目录摊着 PERFORMANCE.md、SETUP.md、TUNING.md、ALGORITHMS.md 七八份文档。README 有 493 行，什么都写在里面。

现在 clone 下来，看到的是另一回事：README 只有 113 行，源码收进 `src/cpp/` 按三层分目录，文档移进 `docs/`（共 192 个文件），全库约 1,033 个文件。3.0.0-rc1 的发布说明把这次重构的意图写得很直白——"makes Wi-Fi sensing a building block for your own products"。

### 三层架构

```
src/cpp/
├── core/       检测器与信号处理，可移植，不碰平台代码
├── runtime/    检测器的执行环境：Wi-Fi、CSI 采集、校准、事件
│   └── esp_idf/    ESP-IDF 后端实现
└── frontend/   接入具体生态：esphome / native / matter
```

依赖只许从上往下：frontend → runtime → core。检测器和 runtime 接口可以在没有 ESP-IDF 的电脑上编译；前端永远经过 `RuntimeFrontendController`，不许绕过去直接碰 Wi-Fi 服务。这套约束是 SDK 可以独立发布的前提——rc3 已把 SDK 以 `francescopace/espectre` 组件的身份上架 [ESP Component Registry](https://components.espressif.com/components/francescopace/espectre)，并支持 ESP-IDF 6.x（官方固件暂留在 5.5.5）。

SDK 有两个公开入口：`espectre_core_sdk.h` 暴露检测器和时间采样器，给已经自己处理 CSI 采集的产品；`espectre_sdk.h` 在此之上加感知、校准、事件和 ESP-IDF 运行时后端。日志是可选的、由前端注册——共享代码不依赖 `esp_log`，没注册就保持沉默，这个细节决定了它能不能干净地嵌进别人的固件。

### 四条固件路线

| 路线 | 适合 | 现状要点 |
|---|---|---|
| **ESPHome** | Home Assistant 用户：YAML 配置、原生实体、自动发现 | 弃用 BLE 配网，改 Improv Serial + Captive Portal；官方镜像主机名带 MAC 后缀（`espectre-a1b2c3.local`） |
| **Native** | 独立传感器：浏览器工具管理，可选 MQTT / HA MQTT Discovery | 标准 Improv Serial 配网，无 BLE 依赖，HTTPS OTA（仅接受签名更新） |
| **Matter** | Matter 控制器：标准占用传感器设备类型 | 占用位只读（静止坐着 = 未占用）；BLE 配网，故不支持无蓝牙的 ESP32-S2；无 OTA，用开发 VID/PID 和示例 attestation 凭据，控制器验证有限 |
| **Micro-ESPectre** | MicroPython 感知研究 | 转为只读：Lightweight 检测 + Direct HTTP 监控，ML 模型不上设备；固件基于 mainline MicroPython |

前两条是文章发表时的主路径的延伸，后两条是新的。Micro-ESPectre 的变化值得单独说：v2 时代它依赖作者自维护的 MicroPython fork（`micropython-esp32-csi`）才能拿到 CSI；作者的 CSI 贡献已通过 [micropython/micropython#18460](https://github.com/micropython/micropython/pull/18460) 合入 mainline，`network.WLAN` 现在有直接的 CSI 方法，fork 退役。主线 MicroPython 项目合入一个第三方仓库的 CSI 采集补丁，这件事本身就是对项目信号处理质量的背书。

### 工具链：浏览器、CLI、协议

- **浏览器工具**（[espectre.dev/tools](https://espectre.dev/tools/)）：[Flash](https://espectre.dev/tools/flash/) 烧录（桌面 Chrome 151+ 或 Edge）、Device settings 配置、Monitor 实时监控调参。需要 Chrome/Edge 是因为 Web Serial；
- **CLI**：`./espectre`（Windows 用 `.\espectre.cmd`）覆盖完整生命周期——`esphome` / `native` / `matter` / `micro` 四个构建命名空间，加 `monitor`、`devices`（发现）、`provision`（Improv 配网）、`direct`、`collect`（CSI 采集）、`mqtt`、`doctor`。本地构建要求 Python 3.14；PlatformIO 构建线在 v3 移除；
- **统一协议**：Direct HTTP（端口 62587，资源挂在 `/espectre/v1` 下）、SSE 事件流、可选 MQTT 共用一套资源模型；设备通过 DNS-SD 广播 `_espectre._tcp.local.`，浏览器和 `./espectre devices` 都按这条记录发现设备；
- **签名与合规**：rc2 起官方 Native/ESPHome 固件要求签名 OTA，Release 附件带 SBOM、notice 和许可证档案包。官方镜像和个人构建之间切换必须走 USB（OTA 拒绝未签名镜像）。

还有个实用的中间件：rc3 加了 [ESPectre Traffic Generator add-on](https://github.com/francescopace/espectre/blob/3.0.0-rc3/tools/ha_traffic_generator_addon/DOCS.md)（64 位 Home Assistant OS），可以让 HA 集中发感知流量、看 CSI 诊断，不用每块板子自己 ping 网关。

## 三、检测器换代：MVS / ML 成为历史名词

对已读过 v2 介绍的读者，这是最重要的一节。3.0.0-rc1 的迁移说明原文：`mvs` → `lightweight`、`ml` → `high_accuracy`，无兼容别名。换的不只是名字，算法本体、增益策略、调度模型都换了。

### 3.1 v2 机制回顾（已退役，原文留档）

v2.8.0 的管道是：Gain Lock → NBVI 自动选子载波 → 湍流 → 移动方差 → 自适应阈值。两个机制当时是文章的主角：

**Gain Lock**——ESP32 的自动增益控制（AGC）和 FFT scaling 会随信号强度自动调整，同一物理运动在 CSI 幅度上呈现不同数值。v2 的解法来自 Espressif esp-csi 例程：启动后采 300 个包的 AGC/FFT 增益值，取中位数（抗异常包），然后调用两个未写入官方文档的 PHY 函数把增益锁死：

```c
extern void phy_fft_scale_force(bool force_en, int8_t force_value);
extern void phy_force_rx_gain(int force_en, int8_t force_value);

if (packet_count < 300) {
    agc_samples[packet_count] = phy_info->agc_gain;
    fft_samples[packet_count] = phy_info->fft_gain;
} else if (packet_count == 300) {
    median_agc = calculate_median(agc_samples, 300);
    median_fft = calculate_median(fft_samples, 300);
    phy_fft_scale_force(true, median_fft);
    phy_force_rx_gain(true, median_agc);
    on_gain_locked_callback();
}
```

老款 ESP32 和 S2 没有这两个函数，v2 的退路是改用变异系数（CV，σ/μ）做归一化——CV 对线性增益缩放数学不变。

**NBVI**——HT20 有 64 个子载波，不是每个都适合动检。v2 启动时花约 10 秒计算每个子载波的三个互补分数（经典 NBVI、熵惩罚版、MAD 鲁棒版），从四条候选策略里选出 12 个非连续子载波，官方口径 F1 > 96% 且零人工配置。代价是启动后 10 秒内房间必须保持静止，否则校准基线偏掉。

### 3.2 v3 现状：AGC 常开 + 固定子载波集

v3 把这两步都拆了，逻辑反过来：

- **AGC 保持开启**。文档原话："ESPectre leaves it on, so features must not depend on signal scale"。共享湍流信号定义为 CV 形式 `turbulence = std(amplitudes) / mean(amplitudes)`，AGC 把所有幅度乘以系数 k 时湍流不变；High Accuracy 的另外七个特征也全是增益不变的比值、相关率或归一化信道形状几何。不再需要锁增益，也就不再依赖未公开的 PHY 函数——工程上这比 v2 干净得多；
- **子载波不再逐会话选择**。两代检测器用同一个固定 12 子载波集 `[4, 8, 13, 18, 23, 28, 36, 41, 46, 51, 56, 60]`（即 ±4、±9、±14、±19、±24、±28，按 bin 32 为 DC 的居中约定）。选择依据写进了 [ADR](https://github.com/francescopace/espectre/blob/main/docs/adr/2026-07-25-select-the-classic-band-from-channel-coherence.md)：运动扰动在约 10 个子载波上保持相干，静默噪声在各频点近独立，把采样点铺满频带就能拿到独立观测——这是从信道相干性推出来的固定结论，不是每家路由器现算的。算法文档明说 "The active runtime no longer selects subcarriers for each session"。

启动"保持安静"的要求没有完全消失，只是换了主体：Lightweight 的启动阈值校准仍需要约 10 秒有效证据（校准期间走动会延长甚至重启校准，约 30 秒仍不干净就放弃、用基础阈值）；High Accuracy 用训练好的固定阈值 0.5，窗口填满即开始检测，完全不需要安静期。

### 3.3 两代检测器

**Lightweight**（默认）——注意它已经不是 v2 的"移动方差"。现在的形态是两特征加权融合：

- `turb_autocorr`：湍流序列的滞后 1 自相关（捕捉运动的时序结构）；
- `turb_iqr_over_mean_aggr`：相邻五频点聚合湍流的稳健相对 IQR（Q75−Q25 除以均值绝对值，压单频点噪声）。

两者经训练统计量标准化后进一个两项线性模型，logit 转概率输出。系数来自按类别、芯片、会话分组的去重叠 out-of-fold 训练，全局工作点在顺序生产回放上选定。运行时没有任何投票或恢复分支，全部分析在阈值层做。

**High Accuracy**——生产神经检测器，不再是 v2 的"实验性"标签。八特征输入进一个紧凑 MLP：

```
Input (8 features) -> Dense(24, ReLU) -> Dense(12, ReLU) -> Dense(1, Sigmoid)
```

共 529 参数（v2 的模型是 9→32→16→1，816 次乘加）。阈值固定 0.5，无启动校准。八个特征里前三个来自湍流路径，第四个是归一化轮廓位移，后四个共享一个物理时间信道轨迹跟踪器（`chan_shape_*` 系列读完整 56 频点 live band，即去掉保护带和 DC 空置后的 bins 4–31 与 33–60）。每个候选特征的公式、物理解释、实现位置和留任证据都记录在 [feature ledger](https://github.com/francescopace/espectre/blob/main/docs/FEATURES.md)——包括被否决的实验。项目把"哪些特征试过没用"公开出来，这在同类项目里很少见。

**怎么选**：官方排查指南给的判据很朴素——Lightweight 吃更少的 CPU 和内存，适合与其他任务共用芯片；High Accuracy 检测更好且免校准，代价是更多算力。校准后出现 noisy-link 警告（静止时指标仍高，通常是信号弱或干扰）时，Lightweight 会漏较弱的运动，应改善信号或切 High Accuracy。切换通过 `detector_select` 实体运行时完成，选择跨重启记忆。

### 3.4 从数包到数时间：时隙调度

v2 的窗口按包数计（默认 100 包），v3 改成固定时间网格：窗口 1000 ms、评估间隔 250 ms、CSI 目标速率 100 pps。运行时按 `csi_target_pps` 把时间切成固定时隙，每时隙最多采纳一个包（选最接近时隙中心的，且这个选择要等下一个时隙有包到来才最终敲定，晚到但更好的包不会丢）；两个包争一个槽时，输家可以占用旁边三 quarters 槽宽内的空槽。窗口内有效时隙至少 70% 检测器才算就绪。

动沿去抖沿用 v2 的 hits 机制，语义更精确了——hits 计的是评估次数不是窗口：连续 4 次 MOTION 评估才切换 `IDLE → MOTION`（默认配置下确认延迟约 0.75–1.0 秒），连续 3 次 IDLE 切回（约 0.50–0.75 秒）。检测器未就绪期间的评估不给读数、保持现态和计数，短暂覆盖下降不会把 MOTION 打掉。

Hampel 滤波（默认开，窗口 7、5.0 MAD）与一阶 Butterworth 低通（默认关，截止 11 Hz）沿用，作用对象从"原始幅度"明确为"检测器评估之前的标量湍流流"。

## 四、性能：口径换了，数字要重新读

v2 文章引用的"多芯片 F1 表"出自 era 的 PERFORMANCE.md；v3 的性能报告改由 `tools/generate_performance_report.py` 从数据集生成（[docs/performance/README.md](https://github.com/francescopace/espectre/blob/main/docs/performance/README.md)，2026-10-03 版），口径变成三段：正常 Wi-Fi 信号、弱 Wi-Fi 信号、长静默录音，外加主机资源基准。验证门槛是 Recall > 95%、FP < 5%。

正常信号下：Lightweight 五款芯片 F1 在 97.9%–99.8%（C5 最弱，Precision 95.9%），High Accuracy 全 100.0%；弱信号下 Lightweight 的 C5 掉到 F1 96.4%（最大 FP 率 5.4%），High Accuracy 仍保持 99.5%–100%。长静默录音专测"没人时乱报警"：Lightweight 在 C6/S3 上分别有 3 次有效误报（最大 FP 率 1.45% / 1.03%），High Accuracy 只有 0.15% 量级、零误报。主机基准（非设备实测）：Lightweight 持久内存 2,008 B、每秒建模检测器 CPU 15.57 µs；High Accuracy 5,060 B、49.84 µs——名义负载 100 pps、4 次推理/秒。

两组数字都标着"自报、未经独立复现"，但有两点比 v2 时代更可信。其一，数据集与训练/评估的隔离有了明确纪律：14 个真实配对数据集加 5 个长静默数据集，High Accuracy 的回放结果只用训练语料之外的录音；新采集必须带环境和数据角色元数据，selection 与 holdout 严格分开。其二，也是原文漏掉的重要事实——**v2.8.0 的 PERFORMANCE.md 自己就登过一份难看的表**：60 秒连续长录音测试里，C6 的 MVS+NBVI 误报率 21.8%（691 次误报）、C5 达 7.9%，和同一份文档里统一配置表的 0.0% FP 相去甚远。官方把两份表并排放着，等于自己承认"短片段指标好看，长时真实场景另说"。v3 把长静默单独立段、给 Lightweight 在弱信号下标 N/A（经典 ESP32 无弱信号数据），是同一种诚实的延续。跨家庭、跨路由器、跨墙体的实际表现，仍然要自己验证。

## 五、部署：从 ESPConnect 到官方浏览器工具

v2 时代的流程是：Releases 下载 `.bin` → 第三方工具 ESPConnect 烧录 → BLE 或 web.esphome.io 配网。现在收拢进官方浏览器套件，全程不需要装任何东西：

1. 桌面 Chrome 或 Edge 打开 [espectre.dev/tools/flash](https://espectre.dev/tools/flash/)，连上开发板，选固件路线和发布渠道（Release / Preview / Development 三选一）；
2. 安装器内完成 Wi-Fi 配置（Native 与 ESPHome 走 Improv Serial；Matter 用控制器的 QR 码或手动码配对）；
3. 打开 [Device settings](https://espectre.dev/tools/device-settings/) 确认连接、命名设备（Native 可在此配 MQTT）；
4. 打开 [Monitor](https://espectre.dev/tools/monitor/) 看感知数据、调检测参数。

ESPHome 路线仍保留 Captive Portal 兜底（连 `ESPectre Fallback` 热点配置），但 BLE 配网已从 ESPHome 镜像移除。Home Assistant 侧的接入方式不变：ESPHome 自动发现，实体有 `Motion Detected`（二值，边沿触发）、`Movement Score`（0.0–1.0，按评估节律推送）、`Threshold`（可调）等，Direct API 与 ESPHome API 并行运行、控制状态即时互通。一条最小自动化还是老样子：

```yaml
automation:
  - alias: "客厅动检 → 开灯"
    trigger:
      platform: state
      entity_id: binary_sensor.living_room_motion
      to: "on"
    action:
      service: light.turn_on
      target:
        entity_id: light.living_room
      data:
        brightness_pct: 80
```

默认感知流量是设备 ping 网关拿 ICMP 应答做 CSI，网络得放行这类流量（有 `dns`、`dns_tcp` 和实验性的 `wifi_raw` 备选；`wifi_raw` 在 ESP32-C6 上因 [esp-idf#19062](https://github.com/espressif/esp-idf/issues/19062) 的 ACK CSI 问题整体禁用）。摆放建议没变：离 AP 3–8 米起步，避开金属遮挡与角落，离地 1–1.5 米，官方另有一份可执行的 [placement guide](https://espectre.dev/guides/placement/)。覆盖口径从 v2 的"约 50 m²、每 50–70 m² 一块"收紧为"一块板管一个区域，按每房间一块规划"——后者更保守，也更符合穿墙衰减的物理现实。

两个 v2 用户容易踩的坑：ESPHome 官方镜像升级后主机名变成 MAC 后缀形式，OTA 和实体 ID 都要跟着改；C5 的频带策略默认 AUTO，自建 `RuntimeConfig{}` 时若想钉死 2.4 GHz 要显式设 `BAND_2G`。

## 六、许可：GPLv3 之外多了一条商业轨道

发文时 espectre 是纯 GPLv3。v3 起改为双轨：第一方代码 GPLv3，合格的闭源集成可购商业许可（经 Mercurius Platform 销售），覆盖共享 core/runtime 层与 Native、Matter 前端；ESPHome 前端保持 GPL-only，商业许可不覆盖。贡献需 DCO 签名加一次性 CLA——CLA 的存在正是为了同一份代码能走双轨分发。

对普通家庭用户没有任何影响：私有使用和内部修改本来就不触发 GPL 义务，MQTT/HTTP 交换报文的独立应用也不被传染。受影响的是想把 espectre 嵌进闭源固件出货的厂商——这恰恰是 rc1 把 SDK 独立出来、rc3 上架 Component Registry的商业逻辑闭环。开源感知引擎 + 付费闭源授权，是这个项目从"个人作品"走向"可嵌入产品的部件"的标志。

## 七、隐私与伦理：从 README 声明到工程约束

作者在伦理上的克制是一贯的。v2 README 里那段加粗警告值得原文照录：

> **WARNING**: Despite the intrinsic anonymity of CSI data, this system can be used for:
> - **Non-consensual monitoring**: Detecting presence/movement of people without their explicit consent
> - **Behavioral profiling**: With advanced AI models, inferring daily life patterns
> - **Domestic privacy violation**: Tracking activities inside private homes

> **警告**：尽管 CSI 数据本身具有匿名性，本系统仍可能被用于：未经同意监测他人的存在与移动；借助更高级的 AI 模型推断日常生活模式；追踪私人住宅内的活动。

配套的六条用户责任（获得明确同意、遵守当地法规、明确告知、限于合法用途、加密保护数据、不得用于非法监视）在 v2 README 的 Security and Privacy 一节，v3 精简进了官网的 [security 与负责任使用指南](https://espectre.dev/security/)，并把这类约束做进了工程面：

- 原始 CSI 采集是可选项，定位为研究与调试用途；
- 感知只在与 AP 关联时进行，绝不用混杂模式；CSI 指南里有一句说得极直白的话："having the Wi-Fi password is not consent to sensing"——有 Wi-Fi 密码不等于有感知的同意；
- 发布固件附 SBOM 与许可档案，算法、测试结果、局限与计划全部公开。

CSI 本身不含可识别信息是隐私模型的物理基础，但"运动数据能暴露作息、睡眠与家中无人的时段"——现行 README 自己就这么写——意味着部署位置和访问控制同样重要。这个项目把滥用风险当成设计输入而不是免责声明，在开源 IoT 动检项目里仍属少数。

## 八、采用建议

**适合**：Home Assistant 用户的房间级存在检测（开灯、关空调、夜报离家）；隐私敏感房间（卧室、浴室）的无摄像头监测；想给自家产品加感知能力的固件开发者（SDK + Component Registry + 商业许可这条链现在是完整的）；做 CSI 信号处理研究的开发者（数据集、模型权重、feature ledger、ADR 全部公开，MicroPython 主线已原生支持 CSI）。

**不适合**：人数统计、身份识别、动作类型识别——两代检测器都只输出运动二值；< 100 ms 延迟的硬实时控制——即便默认配置的确认延迟约 0.75–1.0 秒起；跌倒检测——它分不清"坐下"和"摔倒"，官方在 v2 时代就列过此边界，现在的措辞更严：不能替代任何带安全认证的安防、医疗或紧急系统。

**现在该用哪条线**：家庭用户等 3.0.0 正式版再大规模部署不亏（正式版的发布门槛是数据集定稿加全前端测试矩阵），但 rc3 已可直接用，Release 渠道镜像带签名 OTA；生产嵌入式集成从 Component Registry 拉 SDK 起步；研究用途直接看 `data/` 的数据集和 `docs/ML_TRAINING.md`。已经按旧文部署了 v2.8.0 的读者：v3 无兼容别名，检测器标识、指标尺度（0–10 → 0.0–1.0）、YAML 配置键都变了，官方镜像走 OTA 升级即可，自建 YAML 要按 [SDK 文档](https://github.com/francescopace/espectre/blob/main/docs/SDK.md)的共享配置表重写。

**后续路线**（ROADMAP，2026-10-01 更新）：v3.1 验证 Matter 控制器兼容并定义量产路径；v3.2 Arduino 支持（需求门控）；v3.3 Apple Home 专用前端（视 Matter 测试结果）；v3.4 静止存在检测——把"有人坐着不动"和"空房间"分开，这是对现有能力边界最关键的扩展；v3.5 手势或非医疗呼吸微动（研究门控，允许负结果）；v4.0 多设备本地协同；v5.0 视 IEEE 802.11bf 硬件成熟度接入标准化感知。研究管线 R0–R6 每一步都允许"做了、没成、记下来"的出口。

## 结语

四个月前写 espectre 的拆解时，它是一个把研究算法封装成 ESPHome 组件的优秀单点方案；今天复核，它已经是带三层架构、四条固件路线、独立 SDK 和双轨许可的平台，检测器也从"移动方差 + 自动选频"换代为"增益不变特征 + 固定频带 + 时间时隙调度"。换代的方向高度一致：把不可控的（AGC、逐会话选频、按包计数）换成可证明的（尺度不变性、信道相干性论证、固定时间契约），把单点方案拆成可独立演进的层。

边界也没有变宽的错觉：它仍然只告诉你"有东西在动"，仍然一块板管一个房间，性能数字仍然全部出自作者自己的数据集。对智能家居玩家，它是当下最完整的开源 Wi-Fi 动检方案；对做边缘感知的工程师，它新增了一个更有价值的身份——一套公开了全部推导、实验记录和失败案例的可学习工程参考。
