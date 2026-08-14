---
title: "holehe：用"忘记密码"机制探测邮箱注册了哪些网站——OSINT 的利器与边界"
date: 2026-08-15T03:24:06+08:00
slug: "holehe-email-osint"
github_repo: "megadose/holehe"
source_key: "gh:megadose/holehe"
description: "holehe 是一个 OSINT（开源情报）工具，通过各大网站的"忘记密码"功能探测一个邮箱注册过哪些平台，覆盖 Twitter、Instagram、imgur 等 120+ 网站，且不会给目标邮箱发提醒。本文讲清原理、用法与合规边界。"
draft: true
categories: ["技术笔记"]
tags: ["OSINT", "安全", "邮箱", "开源情报", "Python"]
---

# holehe：用"忘记密码"机制探测邮箱注册了哪些网站

**核心判断**：holehe 的价值不在"检查邮箱有没有账号"这个简单动作，而在于它用的探测手段非常隐蔽——借助各平台的"忘记密码"回复来推断邮箱是否注册，全程不会给目标邮箱发送任何提醒。这让它成为 OSINT（开源情报，Open Source Intelligence）工具链里一个高效又安静的枚举器。但它是一个**探测工具**，不是身份验证系统，合规与伦理边界必须前置。

## 为什么值得看

holehe 由 megadose 开源，是一个 Python 3 工具，通过"忘记密码"功能检查某个邮箱是否在 Twitter、Instagram、imgur 等 **120+ 个网站**上注册过账号。它能返回部分脱敏的恢复邮箱、恢复手机号等附加信息。当前约 1.3 万 star（GPL-3.0）。

需要明确：这个仓库**自 2024-09 起维护节奏明显放缓**（最新合并提交在 2024 年 9 月），写文章时应把它看作"成熟但低维护"的工具，新站点适配可能滞后。

## 工作方式

holehe 对每个支持的站点运行一个模块。以"忘记密码"流程为入口，通过服务端返回的差异化响应判断该邮箱在该平台是否存在账号。核心特性是**不会给目标邮箱发送提醒**——这正是它被 OSINT 从业者看重的原因。

模块输出统一为标准字典：

```json
{
  "name": "example",
  "rateLimit": false,
  "exists": true,
  "emailrecovery": "ex****e@gmail.com",
  "phoneNumber": "0*******78",
  "others": null
}
```

字段含义：
- `rateLimit`：是否被限流。
- `exists`：该邮箱在该服务上是否存在账号。
- `emailrecovery`：有时返回部分脱敏的恢复邮箱。
- `phoneNumber`：有时返回部分脱敏的恢复手机号。
- `others`：其它附加信息。

被限流时，换 IP 即可。

## 快速上手

安装（PyPI）：

```bash
pip3 install holehe
```

或从源码 / Docker：

```bash
git clone https://github.com/megadose/holehe.git
cd holehe/
python3 setup.py install
```

CLI 直接查：

```bash
holehe test@gmail.com
```

作为 Python 库嵌入（基于 `trio` + `httpx`）：

```python
import trio
import httpx

from holehe.modules.social_media.snapchat import snapchat


async def main():
    email = "test@gmail.com"
    out = []
    client = httpx.AsyncClient()
    await snapchat(email, client, out)
    print(out)
    await client.aclose()

trio.run(main)
```

## 适用边界与合规

- **适用**：安全研究、账号归属排查、社工防御自查——例如确认自己的邮箱是否被注册到意外平台。
- **边界**：项目定位"仅供教育目的"（built for educational purposes only），GPL-3.0 许可。
- **合规红线**：用它批量探测他人邮箱注册情况可能触及隐私与相关法律。请仅用于自己拥有或获授权检查的邮箱。作者明确声明项目仅为教育用途，使用者需自行承担合规责任。
- **成熟度**：功能稳定、star 高，但 2024 年后维护放缓，部分新站点可能未覆盖。

## 进一步阅读

- 在线版本（作者托管）：<https://osint.industries/>
- Maltego 集成：<https://github.com/megadose/holehe-maltego>
