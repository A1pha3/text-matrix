---
title: "SmsForwarder 深度上手：把 Android 手机变成 13 通道的短信/通知中转站"
slug: pppscn-smsforwarder-android-multi-channel-redirect-guide
date: "2026-06-20T21:00:00+08:00"
draft: false
categories: ["技术笔记"]
tags: ["Android", "Kotlin", "短信转发", "通知", "Webhook", "IoT"]
description: "SmsForwarder（pppscn/SmsForwarder）是 26K stars 的开源 Android 工具，把手机短信/来电/APP 通知按规则转发到 13 个通道（钉钉/企业微信/飞书/Telegram/Bark/邮箱/Webhook/Server酱等），支持主动控制（远程发短信/查电量）和自动任务触发。BSD-2-Clause，v3.5.0（2026-02-14），最近 commit 2026-06-11。本文从监控链路、规则匹配、通道矩阵、隐私边界四个层面拆解。"
---

## 核心判断

SmsForwarder 解决的问题不是「怎么转发短信」，而是「**把一台旧 Android 手机变成支持 13 个下游通道的短信/通知中转器**」。它用一个 4 年沉淀的规则引擎（关键词 + 正则 + 发送方 + 多重匹配）做匹配，把命中后的内容路由到钉钉群机器人、企业微信、飞书、Telegram、Bark、Server酱、邮箱、Webhook 等 13 个通道。**V3.0 之后的主动控制 + v3.3 之后的自动任务触发，让它从「被动转发器」升级成「带任务自动化的中转站」**——你可以远程查电量、查通话记录，也可以设「电池 ≥ 80% 且连接充电器时自动发通知」这类组合触发。

仓库：https://github.com/pppscn/SmsForwarder，26,410 stars / 3,270 forks，Kotlin，BSD-2-Clause 协议，v3.5.0（2026-02-14，最近 commit 2026-06-11，仍在持续迭代）。

## 关键事实表

| 维度 | 数据 |
|---|---|
| 形态 | Android 客户端（APK，4.4 ~ 13.0） |
| 监控源 | 短信（SMS）、来电（Call）、APP 通知 |
| 下游通道 | 钉钉群机器人、钉钉企业内机器人、企业微信群机器人、企业微信应用消息、飞书群机器人、飞书企业应用、邮箱、Bark、Webhook、Telegram 机器人、Server酱、PushPlus、手机短信 |
| 规则类型 | 关键词（多选）、正则、发送方匹配、多重匹配（OR/AND/正则）、SIM 卡选择 |
| 主动控制（v3.0+） | 远程发短信、查短信、查通话、查话簿、查电量 |
| 自动任务（v3.3+） | 触发条件：电池状态、充电器、SMS 接收、通话状态、位置等 |
| 隐私声明 | 不收集任何隐私数据（仅友盟统计版本信息 + 检查新版本时发版本号） |
| 关键依赖 | XUI、XUpdate、XXPermissions、frpc_android（内网穿透）、Cactus（保活）、AndServer（HTTP 服务）、Location、kmnkt（socket） |
| 镜像 | Gitee 国内镜像 + 蓝奏云网盘（README 三处下载源） |
| 协议 | BSD-2-Clause |

## 系统地图：监控 → 规则 → 通道 三段式

SmsForwarder 的工作流在 README「工作流程」段给了 PNG 示意图，三段式结构：

```
[Android 系统事件]            [规则匹配]                [13 个通道]
SMS / Call / Notification → Rule Engine → Webhook / IM / Email / SMS
   (持续监听)               (关键词/正则/发送方)       (HTTP POST / SMTP / etc.)
```

中间规则引擎是核心。规则可以设置多重匹配条件（关键词 OR/AND + 正则 + 发送方号码），命中后模板化转发——支持变量替换（`${sender}` / `${content}` / `${time}`），可以自定义卡片格式。

**v3.0 的主动控制**反向打通同一条链路：APP 启 AndServer 起 HTTP 服务（默认端口见配置页），用 frpc_android 暴露到公网，外部通过 webhook 反向调用「发短信 / 查短信 / 查通话 / 查话簿 / 查电量」。这意味着你的备用机不只是「接收方」，**也是 API 服务端**。

## 13 个通道：什么场景用什么

| 通道 | 适用场景 | 关键能力 |
|---|---|---|
| 钉钉群机器人 | 团队共享、运维告警 | 自定义关键词、加签安全 |
| 钉钉企业内机器人 | 企业内部 | 走企业内部应用 |
| 企业微信群机器人 | 团队共享、运维告警 | 类似钉钉群机器人 |
| 企业微信应用消息 | 企业内部 | 走企业内部应用 |
| 飞书群机器人 | 飞书用户 | **@指定人 / @所有人**（2026-06-10 commit `596ec8f` 新增） |
| 飞书企业应用 | 企业内部 | 飞书自建应用 |
| 邮箱 | 个人存档、跨平台 | SMTP，支持企业邮箱 |
| Bark | iOS 推送 | **AES-256-GCM 加密**（2026-06-10 commit `0ec20d9` 新增） |
| Webhook | 自定义 HTTP POST | 接 n8n / 自建服务 / 各种 webhook 接收器 |
| Telegram 机器人 | 跨境、隐私 | 走 Telegram Bot API |
| Server酱 | 微信推送（个人用） | 微信公众号通道 |
| PushPlus | 微信推送（个人用） | 公众号通道，类似 Server 酱 |
| 手机短信 | 给另一个手机号发 | 走 SIM 卡 |

**两个 2026-06 的新通道增强**特别值得提：

- **飞书群机器人支持 @指定人 / @所有人**（commit `596ec8f`）——以前飞书通道只能发纯文本，团队里其他人不会收到强提醒；现在可以指定具体 user_id 让消息带上 @ 触达，运维告警场景终于能在飞书群里真正「炸出来」。
- **Bark 走 AES-256-GCM 加密**（commit `0ec20d9`）——Bark 是 iOS 用户的首选推送通道，但 Bark 推送 URL 历史上是明文带内容，SmsForwarder 加上 AES-256-GCM 后，URL 里的 payload 是密文，iOS 端用配对密钥解密，**第三方监听 URL 拿不到内容**。

## 主动控制：备用机的 API 服务端

V3.0 之后，APP 在后台启 AndServer 起 HTTP 服务，监听本地端口。frpc_android 是个内置的 frp 客户端（依赖 [mainfunx/frpc_android](https://github.com/mainfunx/frpc_android)），把本地端口暴露到公网 frp server。配置完成后，外部调用方可以走 webhook 反向控制手机：

- **发短信** — 备用机不在手边也能远程触发
- **查短信** — 抓取最近的短信列表
- **查通话** — 通话记录
- **查话簿** — 联系人列表
- **查电量** — 当前电量、充电状态

**典型场景**：你把旧手机扔在家当监控（电费账单短信自动转发到邮箱 + 钉钉告警），出差时想远程查家里那台手机的电量、看有没有收到物业短信——直接 curl 备用机的 webhook 就行。**这功能的安全边界是 frp 服务端的认证**，frpc 配置文件要保管好。

## 自动任务：v3.3+ 的触发器

v3.3.0（2024-03-05 之后）新增「自动任务・快捷指令」——这是 SmsForwarder 从「转发器」变成「任务自动化器」的关键升级。触发条件支持多选（2026-06-11 commit `150c72f` 把电池状态和充电器改为多选）：

- **电池状态**（多选）：低电量、充满、电量变化
- **充电器**（多选）：插入、拔出、AC、USB、无线
- **SMS 接收**
- **通话状态**：响铃、接听、挂断
- **位置变化**（依赖 [jenly1314/Location](https://github.com/jenly1314/Location)）
- **App 前后台切换**

触发后可以执行「发通知 / 转发到通道 / 调用 webhook」等动作。**典型场景**：

- 「电量低于 20% 且未连接充电器」→ 给自己发邮件提醒（避免出门发现手机没电）
- 「进入公司位置」→ 自动转发当天的待办到钉钉（位置触发）
- 「晚上 11 点」→ 关闭所有转发规则（避免夜间被打扰）

## 保活机制：Cactus + 无声音乐

Android 上做后台监听最大的问题是**系统杀进程**。SmsForwarder 的保活策略是双管齐下：

1. **Cactus 框架**（[gyf-dev/Cactus](https://github.com/gyf-dev/Cactus)）—— 1 像素 Activity + 前台服务保活。
2. **播放无声音乐**（commit `32300b2` 2026-06-11 优化）—— 间隔 60~120 秒循环播放无声音乐，让系统认为「用户正在使用音频」而不进入 doze mode。

README 的 commit message 写得很直白：「间隔越大越省电，建议设到 60~120 秒（省电明显），但过大会降低保活效果」。**这是 Android 权限收紧后所有后台工具的共性妥协**——要么保活强费电，要么省电被杀。

## 隐私边界：声明与依赖风险

SmsForwarder 的隐私声明是 README 头部明文写的：

> SmsForwarder 不会收集任何您的隐私数据！！！APP 启动时发送版本信息发送到友盟统计；手动检查新版本时发送版本号用于检查新版本；除此之外，没有任何数据！！！

这意味着：

- 友盟统计只发**版本号 + 启动事件**——不带短信内容、不带设备标识符（友盟 SDK 在 Android 上获取的是匿名设备 ID）
- 「检查新版本」发的是**当前版本号**给 GitHub Releases API
- **所有监控到的短信/来电/通知都在本地处理**，只在你配置的通道里出现

**但有几个边界要注意**：

- 转发通道的**服务端**能看到全部内容——比如你配了钉钉群机器人，钉钉服务器就能看到所有短信
- 主动控制功能走 frp 暴露端口，**frp 服务端能解密所有 webhook 调用**
- 自动任务的触发器（位置、电池）也属于隐私敏感数据，**触发后只走你配置的通道**

## 适用边界与下载源

**适合用 SmsForwarder 的场景**：

- 你有一台**备用 Android 手机**（旧手机、root 过的备用机），想利用它做短信中转
- 你要**多设备同步短信**（主手机 + 平板 + 电脑）—— 通过钉钉/飞书/Telegram 群把短信推过去
- 你要**归档短信/通知**——转发到邮箱做长期存档
- 你做**IoT 监控/家庭自动化**——把传感器告警通过 APP 通知转发到 webhook
- 你需要**远程控制备用机**（V3.0+ 主动控制）

**不适合用 SmsForwarder 的场景**：

- 你要的是**iOS 端**的短信转发——SmsForwarder 只做 Android
- 你不愿意给 APP **通知读取权限 + 短信读取权限 + 电池优化白名单**——保活不开启就容易被杀
- 你**对延迟敏感**（< 1 秒）——规则匹配 + 通道推送有 1~3 秒延迟
- 你的短信**包含银行验证码**——强烈建议**不要转发到第三方 IM**，只转发到自有 webhook + 邮箱

**下载源**（README 列了 3 个）：

1. GitHub Releases：https://github.com/pppscn/SmsForwarder/releases （首发，海外用户）
2. Gitee Releases：https://gitee.com/pp/SmsForwarder/releases （国内镜像）
3. 蓝奏云网盘：https://wws.lanzoui.com/b025yl86h（访问密码 `pppscn`）

## 关键依赖与致谢

SmsForwarder 不是从零造轮子，它站在一长串 Android 开源库的肩膀上（README 末尾致谢区）：

- [xiaoyuanhost/TranspondSms](https://github.com/xiaoyuanhost/TranspondSms) — 项目原型，Java 时代的老版本
- [xuexiangjys/XUI](https://github.com/xuexiangjys/XUI) — UI 框架
- [xuexiangjys/XUpdate](https://github.com/xuexiangjys/XUpdate) — 在线升级
- [getActivity/XXPermissions](https://github.com/getActivity/XXPermissions) — 权限请求框架
- [mainfunx/frpc_android](https://github.com/mainfunx/frpc_android) — 内网穿透
- [gyf-dev/Cactus](https://github.com/gyf-dev/Cactus) — 保活措施
- [yanzhenjie/AndServer](https://github.com/yanzhenjie/AndServer) — HTTP Server
- [jenly1314/Location](https://github.com/jenly1314/Location) — 位置服务
- [xuankaicat/kmnkt](https://gitee.com/xuankaicat/kmnkt) — socket 通信

V2.x 是 Java 版，已归档到 `v2.x` 分支不再更新；V3.x 是 Kotlin 重写版，**当前主线**。

## 一句话总结

SmsForwarder 是 Android 生态里**把「短信转发 + 通知聚合 + 主动控制 + 自动任务」四件事做到一个 APK** 的开源工具——13 个下游通道、4 年迭代的规则引擎、明确的隐私声明，让它在国内备用机 + IoT 中转场景下基本没有对手。**但它的工程本质是「在 Android 权限收紧的环境下做后台监听」，保活和电量的取舍是永远的主题**——你要先想清楚「为什么需要它」，再决定要不要给一台手机长期供电跑它。
