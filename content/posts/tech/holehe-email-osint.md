---
title: "holehe：借忘记密码机制探测邮箱注册的网站——OSINT 利器与边界"
date: 2026-08-15T03:24:06+08:00
slug: "holehe-email-osint"
github_repo: "megadose/holehe"
source_key: "gh:megadose/holehe"
description: "holehe 是一个 OSINT（开源情报）工具，通过注册、登录与忘记密码入口的非侵入式探测，判断一个邮箱注册过哪些平台，覆盖 Twitter、Instagram、imgur 等 120+ 网站，且不会给目标邮箱发提醒。本文讲清原理、用法与合规边界。"

categories: ["技术笔记"]
tags: ["OSINT", "安全", "邮箱", "开源情报", "Python"]
---

# holehe：用"忘记密码"机制探测邮箱注册了哪些网站

**核心判断**：holehe 的价值不在"检查邮箱有没有账号"这个简单动作，而在于它用的探测手段非常隐蔽——借助各平台注册、登录、找回密码接口的差异化响应来推断邮箱是否注册，全程不会给目标邮箱发送任何提醒。这让它成为 OSINT（开源情报，Open Source Intelligence）工具链里一个高效又安静的枚举器。但它是一个**探测工具**，不是身份验证系统，合规与伦理边界必须前置。

读完本文，你将了解三件事：holehe 的探测为什么不会惊动目标邮箱、123 个站点模块如何组织、以及把它当 CLI（命令行工具）或 Python 库用的完整路径。

## 目录

- [为什么值得看](#为什么值得看)
- [探测机制：三类非侵入式入口](#探测机制三类非侵入式入口)
- [模块版图：123 个模块，23 个分类](#模块版图123-个模块23-个分类)
- [输出格式与字段](#输出格式与字段)
- [快速上手](#快速上手)
- [适用边界与合规](#适用边界与合规)
- [动手练习](#动手练习)
- [常见问题](#常见问题)
- [下一步](#下一步)
- [参考文献](#参考文献)

## 为什么值得看

holehe 由 megadose 开源，是一个 Python 3 工具，检查某个邮箱是否在 Twitter、Instagram、imgur 等 **120+ 个网站**上注册过账号，并能返回部分脱敏的恢复邮箱、恢复手机号等附加信息。截至 2026 年 8 月，项目约 13,600 star、1,700+ fork（派生仓库），采用 GPL-3.0 许可。

需要明确：这个仓库**自 2024 年 9 月起维护节奏明显放缓**（最后一次推送在 2024-09-10），应把它看作"成熟但低维护"的工具——核心机制稳定，但新站点适配基本停滞。

## 探测机制：三类非侵入式入口

holehe 对每个支持的站点运行一个独立模块，通过服务端返回的差异化响应判断该邮箱在该平台是否存在账号。README 概述里把这套机制归纳为"借助忘记密码功能"，但翻一遍仓库的模块清单会发现，实际探测入口分三类：

| 探测方式 | 模块数 | 原理 |
|------|------|------|
| register（注册） | 100 | 尝试注册流程，若提示"邮箱已被占用"则账号存在 |
| login（登录） | 15 | 登录接口对"账号不存在"与"密码错误"给出不同响应 |
| password recovery（找回密码） | 3 | 找回密码流程的差异化响应 |

核心特性是**不会给目标邮箱发送提醒**——探测只读取接口的响应差异，不触发平台的通知流程。这正是它被 OSINT 从业者看重的原因。

运行时，CLI 用 trio 并发调度所有模块、带进度显示，结果按模块名排序输出；启动时还会检查 PyPI 上的最新版本并自动升级。

## 模块版图：123 个模块，23 个分类

仓库的 `holehe/modules/` 目录按站点类型组织，共 123 个模块文件，覆盖 23 个分类。数量较多的几类：

| 分类 | 模块数 | 代表站点 |
|------|------|------|
| forum（论坛） | 25 | 各类技术、游戏论坛 |
| social_media（社交媒体） | 22 | Twitter、Instagram、Snapchat |
| crm（客户管理） | 10 | 各类 CRM 平台 |
| shopping（购物） | 9 | 电商平台 |
| software（软件） | 7 | 开发者工具、SaaS（软件即服务） |
| music（音乐） | 6 | 音乐流媒体 |
| programing（编程） | 6 | 代码托管与技术社区 |

其余分类还包括邮件服务（mails）、媒体（medias）、CMS、求职（jobs）、学习（learning）、医疗（medical）、支付（payment）等。README 里附有完整的模块清单，标注了每个站点的域名、探测方式和是否容易触发限流。

## 输出格式与字段

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

被限流时，README 给的处理方式很直接：换 IP。

## 快速上手

安装（PyPI）：

```bash
pip3 install holehe
```

从源码安装：

```bash
git clone https://github.com/megadose/holehe.git
cd holehe/
python3 setup.py install
```

或用 Docker：

```bash
docker build . -t my-holehe-image
docker run my-holehe-image holehe test@gmail.com
```

CLI 直接查：

```bash
holehe test@gmail.com
```

常用参数（以 CLI 当前版本 1.61 为准）：

| 参数 | 作用 |
|------|------|
| `--only-used` | 只显示目标邮箱注册过的站点 |
| `-NP`、`--no-password-recovery` | 跳过找回密码类探测 |
| `-C`、`--csv` | 把结果导出为 CSV 文件 |
| `-T`、`--timeout` | 设置请求超时秒数（默认 10） |
| `--no-color`、`--no-clear` | 关闭终端着色 / 不清屏显示结果 |

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

这个例子只调用 Snapchat 单个模块；CLI 则会并发跑全部模块。

## 适用边界与合规

- **适用**：安全研究、账号归属排查、社工防御自查——例如确认自己的邮箱是否被注册到意外平台。
- **边界**：项目定位"仅供教育目的"（built for educational purposes only），GPL-3.0 许可。
- **合规红线**：用它批量探测他人邮箱注册情况可能触及隐私与相关法律。请仅用于自己拥有或获授权检查的邮箱。作者明确声明项目仅为教育用途，使用者需自行承担合规责任。
- **成熟度**：功能稳定、star 高，但 2024 年后维护放缓，部分新站点可能未覆盖，个别模块对站点改版的适配也可能失效。

## 动手练习

三条自查路线，全部针对自己的邮箱：

1. **跑一次全量探测**：`holehe 你的邮箱 --only-used`，看结果里有没有你已遗忘或从未主动注册的平台。
2. **导出留档**：加上 `-C` 参数导出 CSV，对比两次运行结果，体会限流（`rateLimit`）对结果完整性的影响。
3. **读一个模块**：打开 `holehe/modules/social_media/snapchat.py`，看它如何构造请求、从哪个响应字段判断账号存在——读懂一个模块就读懂了全部 123 个。

## 常见问题

**Q：为什么探测不会惊动目标邮箱？**
模块只读取注册、登录、找回密码接口的响应差异，不提交会触发通知的操作（如真正发送重置邮件）。

**Q：某些站点返回 `rateLimit: true` 怎么办？**
说明该站点对你的来源 IP 限流了。README 的建议是更换 IP；也可以调大 `--timeout` 或分批重试。

**Q：结果里没有我关心的站点？**
模块列表定格在 2024 年 9 月。之后上线的站点不会覆盖，已有站点若改版了探测接口，对应模块也可能失效。

**Q：能用来查别人的邮箱吗？**
技术上能，合规上不建议。未经授权探测他人账号注册情况可能触及隐私相关法律，这也是作者声明"仅供教育目的"的原因。

## 下一步

把 holehe 跑通之后，可以继续探索三个方向：

- **Maltego 集成**：官方提供 [holehe-maltego](https://github.com/megadose/holehe-maltego) Transform，把邮箱探测接进 Maltego 的关系图谱分析流程。
- **在线版本**：作者托管的 [osint.industries](https://osint.industries/) 提供同类能力，适合不想本地部署的场景。
- **同类工具对比**：README 致谢里提到的 [socialscan](https://pypi.org/project/socialscan/) 与 [UhOh365](https://github.com/Raikia/UhOh365) 采用类似思路，可对比它们的探测方式与覆盖范围。

## 参考文献

- holehe 官方仓库与 README：[github.com/megadose/holehe](https://github.com/megadose/holehe)
- "不会提醒目标邮箱"的说明：[github.com/megadose/holehe/issues/12](https://github.com/megadose/holehe/issues/12)
- Maltego Transform：[github.com/megadose/holehe-maltego](https://github.com/megadose/holehe-maltego)
- 在线版本：[osint.industries](https://osint.industries/)
- 同类工具 socialscan：[pypi.org/project/socialscan](https://pypi.org/project/socialscan/)
- 同类工具 UhOh365：[github.com/Raikia/UhOh365](https://github.com/Raikia/UhOh365)

本文中的 star 数、推送时间与许可信息来自 GitHub API（应用程序接口，查询时间 2026 年 8 月），探测方式统计与 CLI 参数核对自仓库源码与 README。
