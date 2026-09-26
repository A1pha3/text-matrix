---
title: "S-UI 上手与源码核对：把 sing-box 嵌进面板里，会省下哪些麻烦"
date: "2026-05-22T03:00:00+08:00"
lastmod: "2026-09-25T23:40:00+08:00"
slug: "s-ui-sing-box-web-panel-quickstart"
github_repo: "alireza0/s-ui"
source_key: "gh:alireza0/s-ui"
author: text-matrix
description: "S-UI 是构建在 SagerNet/Sing-Box 之上的多协议 Web 管理面板。把 v1.6.3 整个仓库读完之后可以确认一件事：它不是「面板 + 外部 sing-box」，而是把 sing-box 1.14.1 当 Go 库嵌在自己进程里——所以安装脚本会主动停掉 sing-box.service，改入站是直接调用内核的对象管理器。本文按这个事实重写安装、订阅、配额三条主线，并给出 2095/2096 之外的真实默认值来源。"
draft: false
categories: ["技术笔记"]
tags: ["网络工具", "代理", "Go", "sing-box", "运维"]
---

S-UI 要解决的问题很窄：sing-box 的配置是一份 JSON，节点多了以后，改端口、加用户、算流量都得回头编辑文件并重启进程。S-UI 把这份 JSON 拆进数据库，按对象逐个管起来，再给一层网页界面。

读完 `alireza0/s-ui` v1.6.3 之后，最需要先纠正的一条认知是：**它不调用外部 sing-box 的服务接口，而是把 sing-box 作为 Go 库编译进自己的二进制**（`go.mod:16` 锁 `github.com/sagernet/sing-box v1.14.1`）。`core/box.go` 自己实现了内核的生命周期，`core/endpoint.go:15-33` 里新建入站的做法是把 JSON 反序列化成 `option.Inbound`，然后直接调用 `box.inbound.Create(...)`。

这个前提一旦立住，下面几件事就是必然结果，而不是巧合：

- 只需要装一个二进制。README 的「手动安装」第 7 步还留着 `systemctl enable sing-box --now`，但 `install.sh:458-465` 的做法相反：检测到已有的 sing-box 服务单元就 `systemctl stop sing-box`，并删掉 `/usr/local/s-ui/bin/` 下遗留的 `sing-box`、`runSingbox.sh`、`signal`。两处冲突时以脚本和代码为准。
- 面板改完入站不需要重启任何东西，配置是当场推进运行中的内核的。
- 不存在「面板版本和外层 sing-box 版本对不上」这类故障，二者永远同一次编译产出。`/usr/local/s-ui/sui -v` 会把两者一起打印出来（`cmd/cmd.go:66-78`）。

本文的每条断言都标了出处：文件名加行号、仓库原文，或者下面这张坐标表里注明取值时间的计数。本机没有 Go 工具链，凡是需要把程序跑起来才能定案的（例如接口的实际应答体），一律显式写成未验证，不当成结论。

## 项目坐标

| 项 | 值 | 来源与口径 |
|------|------|------|
| 最新版本 | `v1.6.3`，2026-09-16 发布 | `git ls-remote --tags`、`config/version` |
| 内嵌内核 | sing-box `v1.14.1`（上游已到 `v1.14.2`，2026-09-24） | `go.mod:16`、上游 releases 接口 |
| 许可证 | GPL-3.0 | `LICENSE` 全文为第三条正文 |
| 默认分支 | `main` | 仓库分支列表只有一个分支 |
| 建仓时间 | 2024-02-13 | 仓库元数据 |
| 星标 / 复刻 | 9,966 / 1,860 | 仓库接口，2026-09-25 取 |
| 未关闭条目 | 7 | 同一接口的 `open_issues_count`，含拉取请求 |
| 贡献者 | 24 名，含 1 个依赖机器人 | 贡献者接口，2026-09-25 取 |
| 2026 年发布次数 | 17 个版本（2026-02-08 至 2026-09-16） | releases 列表按发布日期计数 |
| 前端 | 独立仓库 `alireza0/s-ui-frontend`，Vue 3 + Vite + Vuetify | `.gitmodules`、该仓库 `package.json` |

README 开头那句免责声明值得原样搬过来，因为它直接决定了后面的适用边界怎么划：

> **Disclaimer:** This project is only for personal learning and communication, please do not use it for illegal purposes, please do not use it in a production environment

## 目录

- [项目坐标](#项目坐标)
- [三层结构：数据、服务、内核](#三层结构数据服务内核)
- [装之前先确认三件事](#装之前先确认三件事)
- [四条安装路径](#四条安装路径)
- [首次登录与改密](#首次登录与改密)
- [界面上真正要理解的四个对象](#界面上真正要理解的四个对象)
- [一个 VLESS 入站的完整流程](#一个-vless-入站的完整流程)
- [订阅输出的三种格式](#订阅输出的三种格式)
- [配额与到期是怎么生效的](#配额与到期是怎么生效的)
- [参数改在哪里](#参数改在哪里)
- [命令行与接口](#命令行与接口)
- [按现象排查](#按现象排查)
- [适用边界](#适用边界)
- [自测题](#自测题)
- [练习](#练习)
- [下一步读哪份代码](#下一步读哪份代码)
- [资料口径与核查方法](#资料口径与核查方法)
- [参考链接](#参考链接)

## 三层结构：数据、服务、内核

后端目录的分工可以直接从包名读出来，下面这份是按 `main` 分支的实际内容整理的（原文照抄目录名，便于对照）：

```text
api/         HTTP 处理层：/api 与 /apiv2 两组路由、会话与令牌校验
app/         进程装配：Init/Start/Stop，只有一个 app.go
cmd/         命令行子命令与数据库迁移脚本
config/      编译期内嵌的 version、name，以及环境变量读取
core/        内嵌 sing-box 的内核：生命周期、注册表、会话跟踪
cronjob/     六个定时任务：统计、配额、可选全局重置、清理、内核看门狗、WAL 检查点
database/    GORM 打开 SQLite、模型定义、备份
logger/      日志
middleware/  只有 CSRF 与域名校验两个中间件
network/     监听器与 TLS 自动重定向
service/     业务层：入站、出站、客户端、设置、订阅、WARP
sub/         订阅生成：link、JSON、Clash 三种输出
util/        链接生成、Base64、证书、请求头
web/         前端静态资源的挂载与路由兜底
windows/     WinSW 服务定义，以及安装、卸载、构建用的批处理
```

对照下来，几个容易误解的位置：`app/` 不是业务逻辑层，业务全在 `service/`（服务层）；定时任务不在 `service/`，在 `cronjob/`；`database/`（数据库层）用的驱动是 `gorm.io/driver/sqlite`（`go.mod:27`），落盘是单个 `s-ui.db`。

一次「保存入站」的真实调用链是这样的：

```text
POST /app/api/save
  → service.ConfigService 分派 → InboundService.Save    # inbounds.go:104
  → corePtr.AddInbound(序列化后的配置)                    # inbounds.go:150
  → box.inbound.Create(...)                              # 直接调运行中内核的管理器
  → tx.Save(&inbound)                                    # 落库，inbounds.go:161
```

顺序值得留意：**先推内核，后写数据库**，两步处在同一个事务里，任何一步失败整体回滚，不会出现「库里有了、内核里没有」。客户端绑定变化时走的是另一条路：`UpdateInboundsUsers`（`inbounds.go:354`）先试就地换用户——用 `CloseInboundUserSessions` 关掉已被停用那些人的现有连接；协议不支持就地更新时，才退回 `RemoveInbound` 加 `AddInbound` 整条重建（`:394-399`）。这也是「停用即断连」能成立的原因，连接是被显式关掉的，不是等它自己超时。

启动时内核按库里的记录整体重建，所以数据库仍然是唯一的真相来源。

反方向的数据流同样值得看一眼。对账由面板主动发起，每 10 秒一轮（`cronjob/cronJob.go:48`），内核从不上报：`SaveStats` 从 `box.SessionTracker().GetStats()` 取走增量，按 `statsBucketSeconds`（默认 60 秒）聚合成行写进 `stats` 表，同时累加到客户端的 `Up`/`Down`。取走但没提交成功的批次不会丢，它们进 `pendingStats`，等下一个 10 秒重新拼进去（`service/stats.go:52-56`、`:78-84`）。

内核本身也有看门狗：每 5 秒跑一次 `StartCore()`（`cronjob/cronJob.go:65`），挂了会被自动拉起来。

## 装之前先确认三件事

**第一件：机器是不是 Linux。** 这一点比 README 的表述要窄。安装脚本的架构映射表覆盖 `amd64`、`386`、`arm64`、`armv7`、`armv6`、`armv5`、`s390x` 七种（`install.sh:321-329`），不在表内直接报「不支持的架构」退出；下载文件名硬编码成 `s-ui-linux-$(arch).tar.gz`（`install.sh:534`）。而 v1.6.3 的发行产物正好是这七个 Linux 包，加上 `s-ui-windows-amd64.zip`、`s-ui-windows-arm64.zip` 和一份 `SHA256SUMS`——**没有任何 macOS 产物**。README 一边把 macOS 标成「🚧 Experimental」，一边又在安装小节写着 `Linux/macOS`，实际跑在 macOS 上的话，脚本连 `/etc/os-release` 都读不到，会在操作系统检测那一步退出（`install.sh:295-306`）。

**第二件：2095 与 2096 是否空闲。** 安装脚本全程不做端口占用检查，冲突要等到服务起来才暴露。

**第三件：机器上有没有独立的 sing-box 服务。** 有的话会被停掉并删除遗留文件，见前文 `install.sh:458-465`。如果你的 sing-box 还承载着别的配置，先备份。

## 四条安装路径

### 一键脚本

```sh
bash <(curl -Ls https://raw.githubusercontent.com/alireza0/s-ui/master/install.sh)
```

这条命令要求 root，按下面的顺序做完才会退出。先说一个对判断「能不能信这条路径」有用的事实：CI 只测 Go 代码（`go test ./...`，外加一轮 `-race` 短测，覆盖接口、服务、订阅、数据库、工具、日志、网络七个包），`install.sh` 本身不在任何测试里，只在 `release.yml` 的一句注释里被提到。所以脚本的行为只能靠读。

1. 用包管理器补上 `wget`、`curl`、`tar`，覆盖 `yum`/`dnf`/`pacman`/`zypper`/`apk`/`apt-get` 六类发行版家族。
2. 探测初始化系统：Alpine 走 OpenRC，其余按 `systemctl` 与 `/run/systemd/system` 判定，兜底当 systemd（`install.sh:310-317`）。
3. 下载架构对应的 `s-ui-linux-*.tar.gz` 到临时目录，同时取发行版的 `SHA256SUMS`，**在解包之前**做校验；老版本没有这个文件时只告警不拦截，仍然继续装（`install.sh:542-543`、`:476-488`）。
4. 若 `/usr/local/s-ui/` 已存在，先停掉正在跑的 s-ui，再解包，然后 `cp s-ui/s-ui.sh /usr/bin/s-ui`、`cp -rf s-ui /usr/local/`（`install.sh:546-564`）。
5. 跑一次 `/usr/local/s-ui/sui -v` 确认二进制真能执行。失败时删掉的是临时目录，已经复制到位的东西不会回滚，`/usr/local/s-ui` 与 `/usr/bin/s-ui` 会原样留着（`install.sh:511-513`、`:568-573`）。
6. 把 `s-ui.service` 复制进 `/etc/systemd/system/`，跑 `sui migrate`。
7. 交互式询问是否现在改端口、面板路径、订阅端口、订阅路径，以及是否设置管理员账号密码；密码用 `read -s` 读，不落终端回显。
8. `systemctl enable s-ui --now`（OpenRC 下改成 `rc-update add s-ui default` 加 `rc-service s-ui restart`），最后打印面板地址（`/usr/local/s-ui/sui uri`）。

安装脚本与面板界面共用一套 6 种语言的文案，靠 `SUI_LANG` 选，未设置时拿系统 `$LANG` 猜：

```sh
SUI_LANG=zhcn bash <(curl -Ls https://raw.githubusercontent.com/alireza0/s-ui/master/install.sh)
```

要装指定旧版本，把版本号同时给到脚本路径和参数（README 原样写法，以 `v1.5.0` 为例）：

```sh
VERSION=v1.5.0 && bash <(curl -Ls https://raw.githubusercontent.com/alireza0/s-ui/$VERSION/install.sh) $VERSION
```

Alpine 需要先 `apk add bash`，装完用 `rc-service s-ui start|stop|restart` 与 `rc-update add s-ui default` 管理。

### Windows

1. 从 [GitHub Releases](https://github.com/alireza0/s-ui/releases/latest) 下载 `s-ui-windows-amd64.zip`（或 `arm64`）。
2. 解压到任意目录。
3. 以管理员身份运行 `install-windows.bat`，跟向导走完。
4. 打开 http://localhost:2095/app 。

`windows/` 目录里除了批处理，还有一份 `s-ui-windows.xml`，那是 WinSW 的服务定义。安装脚本会在需要时从 WinSW 的发布页下载 `winsw.exe`（写死的版本是 v2.12.0）并注册成名为 `s-ui` 的 Windows 服务；下载失败只打一行警告并跳过服务安装，面板本身仍可前台运行。也就是说，Windows 上「装成服务」这一步是有外部依赖的，离线机器上要提前放好 `winsw.exe`。

### Docker

```shell
mkdir s-ui && cd s-ui
wget -q https://raw.githubusercontent.com/alireza0/s-ui/master/docker-compose.yml
docker compose up -d
```

`docker-compose.yml` 的实际内容比 README 的 `docker run` 示例窄，值得逐条看清：镜像是 `alireza7/s-ui`，只映射 **2095 和 2096** 两个端口，挂载 `./db:/app/db` 与 `./cert:/app/cert`，`restart: unless-stopped`，入口是 `./entrypoint.sh`。443 和 80 只出现在 `docker run` 那段示例里，compose 文件没有——照着 compose 部署却指望反代直通是不成立的。另一个不一致处是证书目录：compose 挂到 `/app/cert`，`docker run` 示例挂到 `/root/cert`。

容器默认以 root 运行不是疏忽。`entrypoint.sh:13-16` 把理由写得很直白：TUN 入站需要 `CAP_NET_ADMIN`，1024 以下的面板端口需要 `CAP_NET_BIND_SERVICE`，降到普通用户这两样都会丢。真要降权，用官方留的口子：

```yaml
environment:
  - SUI_UID=1000
  - SUI_GID=1000
```

`entrypoint.sh:21-31` 会先把 `$SUI_DB_FOLDER`、`/app/sui`、`/app/libcronet.so` 的属主改过去，再用 `su-exec` 降权启动；如果容器本来就不是以 root 起来的，它会打一行提示并忽略这组变量。数据库所在目录被固定成 `0700`（`database/db.go:37-49`），这一点在排查写库失败时要记得。

### systemd 单元里值得看的四行

```ini
LimitNOFILE=1048576
NoNewPrivileges=true
PrivateTmp=true
ProtectHome=read-only
```

`LimitNOFILE` 那行的注释说明了动机：一个代理连接占两个文件描述符，默认 1024 在几百个客户端时就会耗尽，症状只是日志里一句 too many open files。`ProtectHome` 用 `read-only` 而非 `true`，因为 `s-ui.sh` 会把 acme.sh 签发的证书放进 `/root/cert`，面板需要读它。

## 首次登录与改密

装完先让面板自己报地址：

```sh
/usr/local/s-ui/sui uri
```

它按数据库里的设置拼地址：证书齐全就是 https，设了 `webDomain` 就用域名，否则用本机地址。端口段只在「443 且 TLS」或「80 且无 TLS」两种组合下省略，因此默认的 2095 一定会出现在地址里。

初始账号密码是 `admin` / `admin`，但准确说法是：**只在 `users` 表为空时**才会插入这一对（`database/db.go:21-33`）。删库重装会重新出现，升级不会覆盖你已经改过的密码。

改密码有两条路：登录后在「管理员」页改，或者用下面这组命令。

```sh
/usr/local/s-ui/sui admin -username <用户名> -password <新密码>
/usr/local/s-ui/sui admin -show          # 查看当前管理员账号名
/usr/local/s-ui/sui admin -reset -yes    # 恢复成 admin/admin，跳过确认
```

两种改法写的是同一条记录。密码用 bcrypt 存储；从 1.5.x 之前升级上来的明文密码，迁移会自动补哈希（`cmd/migration/1_5_2.go:9`）。

还有一条容易踩的机制：**同一来源 IP 连续失败 10 次，会被锁 10 分钟**，失败记录保留 30 分钟（`service/login_limit.go:17-20`）。计数按来源地址而不是按用户名——注释里给的理由是，按用户名计数会让任何人凭猜用户名就把机器的管理员锁在门外。所以「密码明明对却进不去」先想是不是刚试过几次，等十分钟比查数据库快。

## 界面上真正要理解的四个对象

中文界面（`src/locales/zhcn.ts`）的导航项是：主页、入站管理、出站管理、服务管理、节点管理、用户管理、路由列表、TLS 设置、基础信息、DNS、管理员、设置。要管住一个节点，只需要理解其中四个对象。

**入站（inbound）** 是监听端口和协议本身。`database/model/inbounds.go:7-19` 只固定了 `id`、`type`、`tag`、`tls_id`、`addrs`、`out_json` 六个字段，其余全部原样塞进 `Options` 存起来，读取时再摊平回去。这意味着 sing-box 入站选项的字段结构不需要面板逐个适配——新字段能直接穿过。代价是 `users` 在反序列化时被剥掉（`:44`），由面板自己按客户端重新拼。

**TLS 对象** 是独立的一张表，入站用 `tls_id` 外键指向它。所以「给入站加 TLS」的正确顺序是先在 TLS 设置页建对象，再回到入站把它选上。

**客户端（client）** 才是配额与到期的载体。`database/model/model.go:25-55` 里它的字段可以分四组读：

```text
身份     Name（同时是订阅标识）、Remark、Group、Desc、Enable
绑定     Inbounds（可绑多个入站）、Links（订阅正文来源）、Config
配额     Volume（上限）、Up / Down（本周期已用）、Expiry（到期 Unix 秒）
滚动     AutoReset / ResetDays / NextReset、DelayStart、TotalUp / TotalDown（历史累计）
```

界面上这一页叫「用户管理」。把配额放在客户端而不是入站上是有意为之：一个入站服务很多人，限额只能落到人。

**令牌（token）** 是给外部程序调接口用的凭据，存 `tokens` 表，绑定创建者，可设过期。

## 一个 VLESS 入站的完整流程

下面这条路径按面板的真实对象关系来走，创建完成后应当能逐项验收。

1. 先有证书。可以用 acme.sh，也可以照 README 给的 certbot 一条命令：

   ```bash
   certbot certonly --standalone --register-unsafely-without-email --non-interactive --agree-tos -d <你的域名>
   ```

    standalone 模式要占 80 端口，签之前先停掉监听它的服务。

2. 「TLS 设置」页新建一个 TLS 对象，填证书与私钥路径，必要时设 ALPN 与最小最大版本。
3. 「入站管理」页新建入站：类型选 `vless`，给一个全局唯一的 `tag`（数据库上是唯一索引），填监听地址与端口。
4. 把第 2 步的 TLS 对象关联到这个入站。要用 reality，它仍然是 TLS 对象上的一个分支而不是独立协议：生成客户端链接时，服务端 TLS 里的 `reality` 会被合进客户端参数，并在链接上追加 `security=reality`（`util/genLink.go:137-147`、`:762-763`）。
5. 「用户管理」页新建客户端：设置名字，勾选要绑定的入站，需要限额就填上限字节数，需要到期就填到期时间。UUID 由面板生成，客户端名字同时就是它的订阅标识。
6. 保存。服务端写完数据库立刻调用 `core.AddInbound`，新端口当场开始监听，不用重启面板。

每一步的验收：

- 第 6 步之后，`/usr/local/s-ui/sui healthcheck` 应当以 0 退出。它从数据库读当前端口，然后只做一次 TCP 拨通、单次超时 3 秒——故意不发 HTTP 请求，因为配了证书就是 HTTPS、没配就是 HTTP，任何一侧写死都会误报（`cmd/healthcheck.go:16-30`）。Dockerfile 把它用作健康检查。
- 在「主页」看内核状态：状态接口返回的 `sbd` 字段给出内核是否在跑、已运行时长、协程数与已分配内存（`service/server.go:139-159`），这是内核对账用的。
- 客户端连上之后，10 秒内「在线」列表里应当出现这个用户。注意这个列表给的是名字集合，不是连接数（`service/stats.go:17-21`、`:225-234`），统计粒度就是那个 10 秒的采样周期。
- 想确认落进内核的配置长什么样，可以直接读面板生成的完整配置，动作名是 `singbox-config`。

## 订阅输出的三种格式

订阅跑在一个单独的 HTTP 服务上（`app/app.go:22` 的 `subServer`），监听 `subPort`，全部路由只有两条（`sub/subHandler.go:25-28`）：

```text
GET   <scheme>://<host>:<subPort><subPath><subid>
HEAD  <scheme>://<host>:<subPort><subPath><subid>
```

默认即 `http://<host>:2096/sub/<client 名>`。三种输出共用同一个路径，靠查询参数分流：

| 请求 | 生成方 | 正文 |
|------|--------|------|
| 不带 `format` | `SubService.GetSubs` | 节点链接按行拼接，默认再做一次 Base64 |
| `?format=json` | `JsonService.GetJson` | sing-box 客户端配置 |
| `?format=clash` | `ClashService.GetClash` | Clash.Meta 配置 |

`format` 只认 `json` 与 `clash` 两个字面值，写成别的会直接 400（`sub/subHandler.go:33-46`）。README 特性表里那个 `link/json/clash + info`，`+ info` 指的是随响应头给出的用量信息，并没有第四种格式。

四个响应头都在同一处写死（`sub/subHandler.go:77-81`）：

```text
Subscription-Userinfo:    upload=<上行字节>; download=<下行字节>; total=<配额>; expire=<Unix 秒>
Profile-Update-Interval:  12
Profile-Title:            客户端备注，没填则用客户端名
Content-Disposition:      attachment; filename="..."; filename*=UTF-8''...
```

`Profile-Update-Interval` 原样透传设置项 `subUpdates`（默认 12），面板侧不解释单位，按小时理解是客户端与文档的约定；`Subscription-Userinfo` 的四个数值直接取自客户端记录。客户端名字或备注含非 ASCII 字符时，`Content-Disposition` 会同时给一份 ASCII 退化名和一份 RFC 5987 编码名（`sub/subHandler.go:84-131`）。

两个默认值值得记住。`subEncode` 默认 `true`，也就是链接格式的正文是 Base64 过的，开关在「设置 → 订阅」里，而不是在订阅链接上加参数。`subShowInfo` 默认 `false`；开启后每条链接的名字尾巴会追加剩余量（📊）与剩余天数（⏳），两者都没得显示时才落到 `♾`（`sub/subService.go:62-77`），所以「有配额、无到期」出现的是 📊 而不是 ♾。

订阅地址的生成顺序是：设置了 `subURI` 就整条用它；否则用 `subDomain`（没有则用请求带来的主机名）拼上 `subPort` 与 `subPath`，证书齐全时协议变 https。这里有一处源码事实值得提防：那个「默认端口不写进 URL」的判断，拿带冒号的 `:2096` 去和字面量 `80`/`443` 比较，永远不成立（`service/setting.go:407-415`），所以生成的订阅地址始终显式带端口。

最要紧的一条：**URL 里那段 `<subid>` 就是客户端名字**（查询条件 `enable = true and name = ?`，`sub/subService.go:50-52`）。改名等于换一条订阅链接，停用客户端会让原链接直接返回 400。

## 配额与到期是怎么生效的

没有事件通知，也没有连接级拦截。一个每分钟跑一次的定时任务做全表扫描，判据就是这条条件（`service/client.go:506`）：

```sql
enable = true AND ((volume > 0 AND up+down > volume) OR (expiry > 0 AND expiry < ?))
```

命中的客户端被置 `enable = false`，涉及到的入站收集起来，由 `InboundService.UpdateInboundsUsers` 重建它们的用户列表，也就是把这个人从运行中的内核里摘掉。整个过程会在 `changes` 表留下执行者为 `DepleteJob` 的记录，「基础信息」页的变更列表能看到。

所以「超了限额还能连」最常见的解释是还没来得及跑这一轮，最长等一分钟，不必怀疑配额没生效。要立刻断，可以在界面上手动停用该客户端，那条路径是同步的。

顺带两个同族机制：

- `DelayStart`（延迟开始）配 `ResetDays` 使用时，客户端第一次产生流量才把到期时间定成「此刻 + N 天」（`service/client.go:549-556`），执行者记为 `ResetJob`。
- `AutoReset`/`NextReset` 支持按周期滚动清零 `Up`/`Down`，历史累计另存在 `TotalUp`/`TotalDown`，所以「本周期用量」和「历史总量」是两个数。
- 全局重置另有一条 cron 表达式配置（`globalReset`），留空即关闭。

## 参数改在哪里

这里有个必须先讲清的区分：**面板的运行参数存在数据库里，不在环境变量里**。端口、路径、时区、订阅行为都在「设置」页，或者用 `sui setting` 改。环境变量只有三个真正被读取：

| 变量 | 作用 | 读取位置 |
|------|------|----------|
| `SUI_LOG_LEVEL` | `debug`/`info`/`warn`/`error`，`SUI_DEBUG=true` 时强制 debug | `config/config.go:39` |
| `SUI_DEBUG` | 值为字符串 `true` 才生效 | `config/config.go:47` |
| `SUI_DB_FOLDER` | 数据库目录，未设置时取可执行文件同级的 `db/` | `config/config.go:51` |

三项之外都不必期待有作用。Windows 那句「兜底到 `C:\Program Files\s-ui\db`」也有前提：只有当程序算不出自身可执行文件路径时才走到它，正常情况下用的仍是同级 `db/`。

`SUI_BIN_FOLDER` 只在 1.2 的那次迁移里被读一次（`cmd/migration/1_2.go:22`），`SINGBOX_API` 在 Go 源码里搜不到任何引用——README 的环境变量表把这两行留着了，但设置它们不会改变运行中的面板。数据库文件名固定为 `s-ui.db`（`s-ui` 这个名字来自 `config/name`）。

以下是排查和迁移时最常用的一组默认值（`service/setting.go:61-94`）：

```text
webPort               2095          面板端口
webPath               /app/         面板路径
subPort               2096          订阅端口
subPath               /sub/         订阅路径
secret                随机 32 位字母数字  会话 Cookie 的签名密钥
sessionMaxAge         0             会话超时时限
trafficAge            30            流量记录保留天数
statsBucketSeconds    60            流量采样分桶秒数
timeLocation          Asia/Tehran   时区
subUpdates            12            订阅自动更新时间
subEncode             true          订阅正文 Base64
subShowInfo           false         订阅正文附带用量与到期
maintenance           false         维护模式
```

两项需要特别注意。`secret` 是会话 Cookie 的签名密钥，生成方式是 `crypto/rand` 从 62 个字母数字里逐位取 32 次，取到系统随机数报错时退回 `math/rand`（`util/common/random.go:12-40`）；随机值意味着换库或重建后所有已登录会话一起作废。`timeLocation` 默认 `Asia/Tehran`，这是作者侧的默认值而非中性选择。它传给 cron（`cronjob/cronJob.go:26` 的 `loc` 参数），所以全局流量重置的触发时刻按它算；到期与限量的判断本身用的是 Unix 秒，不受时区影响，受影响的只有界面上读到的时间。中国区部署建议在「设置」里改成 `Asia/Shanghai`。

## 命令行与接口

这里有两个同名命令，先分清再抄命令。`/usr/local/s-ui/sui` 是 Go 二进制，不带参数就是启动面板，带子命令时是运维工具（`cmd/cmd.go:52-58`）；`/usr/bin/s-ui` 是另一回事：它是 `s-ui.sh` 那份菜单脚本被 `install.sh:560-561` 复制过去的产物，只处理服务控制类的动词——`start`、`stop`、`restart`、`status`、`enable`、`disable`、`log`、`update`、`install`、`uninstall`，不带参数就进交互菜单，认不出的参数打印用法。它不会转发 `admin`、`setting`、`backup` 这类配置子命令，脚本内部调的一直是全路径的 `/usr/local/s-ui/sui`（`s-ui.sh:164-218`、`:1009-1046`）。所以下面这些命令要用前者来跑：

```text
admin          设置 / 查看 / 重置管理员账号密码
uri            打印面板访问地址
migrate        执行数据库迁移
setting        改设置：-port -path -subPort -subPath -show -reset
healthcheck    面板在配置的端口上监听则退出码 0
backup         导出数据库：-output 路径（- 表示标准输出），-exclude changes,stats
-v             打印面板版本与内嵌的 sing-box 版本
```

改端口不需要碰配置文件：

```sh
/usr/local/s-ui/sui setting -port 8443 -path /panel/ -subPort 8444 -subPath /s/
```

面板的接口（API，应用程序接口）分成两组用途：`/app/api` 给前端用，靠会话 Cookie 认证，并且挂在 `SameOrigin` 中间件后面；`/app/apiv2` 给外部程序用，靠请求头 `Token` 认证（`web/web.go:134-142`）。令牌在面板的「API 令牌」对话框里创建（文案键 `admin.api`），提示原文是「请复制令牌并保存到安全的地方。它将不再显示。」创建与删除都走 `/api/addToken`、`/api/deleteToken`，之后立刻热重载进内存（`api/apiHandler.go:59-63`）。校验用 `subtle.ConstantTimeCompare`，过期条目只跳过不从切片里删（`api/apiV2Handler.go:113-137`，注释解释了早先就地删除会导致后一个有效令牌被跳过的缺陷）。

动作名是路由参数，可用的取值如下（两份清单略有差异：`tokens` 与 `singbox-config` 只在 `/api` 侧）：

```text
GET   load | inbounds | outbounds | endpoints | services | tls | clients | config
      users | settings | stats | status | onlines | sessions | logs | changes
      keypairs | getdb | checkOutbound | tokens | singbox-config
POST  login | changePass | save | restartApp | restartSb | maintenance
      resetTraffic | linkConvert | subConvert | importdb | addToken | deleteToken
      closeSessions | getCertPing
```

三个和「重启」相关的动作语义不同，别混用：`restartApp` 是**原地重启**——给自己的 PID 在三秒后发一个 `SIGHUP`，主循环收到信号后 `Stop()` 再 `Start()`，进程不换、PID 不变，systemd 全程不参与（`service/panel.go:15-31`、`main.go:27-40`）；`restartSb` 只重启内嵌内核；`maintenance` 是「停住内核并保持停住」——注释里写得很明白，因为 5 秒一轮的看门狗会把单纯 stop 撤销掉，所以这是唯一能让内核长期停下的入口（`api/apiService.go:362-383`）。界面上的提示是「内核已停止：在重新启动之前客户端无法连接」。

下面是用 curl 走通一次只读调用的写法（登录 → 建令牌 → 查状态）：

```bash
BASE=http://127.0.0.1:2095/app
curl -sc cookie.txt -d 'user=admin&pass=<密码>' $BASE/api/login
curl -b cookie.txt -d 'desc=ci&expiry=0' $BASE/api/addToken
curl -H "Token: <上一步返回的令牌>" $BASE/apiv2/status
```

登录接口读的是表单字段 `user` 和 `pass`（`api/apiService.go:306`），这一步在源码里能定案；**令牌接口的实际应答体本文未验证**——本机没有 Go 工具链，也没跑起过真实面板，只核到路由与字段名这一层。

## 按现象排查

下面每一条都对应上面核过的代码位置，按现象找。

**面板打不开。** 先 `/usr/local/s-ui/sui uri` 看当前配置到底把地址拼成了什么，再 `sui healthcheck` 看是否真在监听。这两步能区分「进程没起来」和「端口或路径与你以为的不一样」。改了 `webPath` 之后必须带完整路径访问：面板不会把根路径重定向过去，访问 `/` 拿到的是一个空体的 404（`web/web.go:143-152`）。

**登录报失败，但密码是对的。** 十分钟内累计失败 10 次会锁来源 IP 十分钟（`service/login_limit.go`）。计数按 `c.ClientIP()` 取（`api/utils.go:22-24`），所以反向代理没传真实来源地址时，所有用户会共用代理那一个计数器；换客户端 IP 能立刻进得去，但正确反应是等一轮，或者去查代理头。

**Docker 里报写库失败。** 数据库目录是 `0700`，容器内进程身份若拿不到该目录的写权限就会失败。用 `SUI_UID`/`SUI_GID` 让入口脚本先改属主再降权，不要手工 `chmod 777`。

**订阅在客户端里一片空白。** 三个原因按顺序排：正文默认是 Base64，某些客户端要求明文；`subURI`/`subDomain` 没设对，下发出去的地址指向了内网或错误端口；客户端被停用或改了名，`<subid>` 段与名字对不上就是 400。

**改了限额或到期，客户端还在跑。** 判据每分钟跑一次，最长一分钟延迟。

**升级后面板起来了但域名解析行为变了。** 1.6.0 那次迁移对 sing-box 1.14 的废弃项做了明确切分（`cmd/migration/1_6_0.go:65-80`、`:283-320`）：

```text
会自动改写（无损）
  dns.independent_cache                 直接丢弃，1.14 不再读它
  experimental.cache_file.store_rdrc    改名 store_dns
  route.rule_set[].download_detour      改名 http_client
  TLS 配置里内联的 acme 块              改写成 certificate_provider

只打印提示、不代改（会重排 DNS 规则、改变解析结果）
  DNS 规则里的传统地址过滤器（ip_cidr、ip_is_private、ip_accept_any 或 IP 规则集）
  DNS 规则动作里的 strategy 选项
```

提示原文会附上 sing-box 官方迁移页地址，并说明后两项在 1.16 移除。这两项属于错误必须由人来处理的场景，别等它自动修。

**流量数字对不上。** 面板只统计穿过本机入站的字节。客户端的订阅里如果混了类型是 `external` 或 `sub` 的条目（指向别人的服务器），那部分用量永远不会计入这里的 `Up`/`Down`。另外统计是 10 秒一轮的增量聚合，不是实时连接表。

**内核停了又自己起来。** 那是 5 秒看门狗在做的事，不是错误。要保持停机就用维护模式。

## 适用边界

适合的场景：一个人或一个小团队，管若干台机器上的自建节点，需要按人分配配额和到期，需要给别人发一条订阅链接就完事。这些恰好是「改配置文件 + 手抄 UUID」最容易出错的环节。

不适合的场景，按证据说：

- 生产环境。README 的免责声明原话就包含「please do not use it in a production environment」，这不是套话：数据库权限、默认口令、维护模式全为单人运维设计。
- 把面板直接暴露到公网。管理员口令是唯一屏障，虽然有登录限速，但仍应给它套 TLS 加反向代理，或只在内网可达。
- 需要复杂路由策略。路由列表页覆盖常见分流，但 sing-box 的路由语义比面板表单宽，`Options` 那份透传只保证「字段能存下」，不保证界面提供编辑。深度定制仍需直接改「配置」项。
- 多实例高可用。状态全在一个 SQLite 文件里，`cronjob/WALCheckpointJob.go` 每 10 分钟做一次 WAL 检查点，架构上没有主从这一层。

## 自测题

**问题 1**：S-UI 与 sing-box 的进程关系是什么？这个前提决定了哪三件事？

<details>
<summary>查看答案</summary>

sing-box 以 Go 库的形式编译进 `sui` 这一个二进制里，同进程运行，面板直接调用内核的对象管理器。因此：只装一个二进制；改配置即时生效不需要重启；不存在面板与外层内核版本不匹配。`install.sh` 甚至会主动停掉机器上原有的 sing-box 服务。

</details>

**问题 2**：端口、路径、时区这些参数，改环境变量有用吗？该改哪里？

<details>
<summary>查看答案</summary>

没用。它们存在数据库的 `settings` 表里，改法有两种：界面「设置」页，或 `/usr/local/s-ui/sui setting -port ... -path ... -subPort ... -subPath ...`。真正被读取的环境变量只有 `SUI_LOG_LEVEL`、`SUI_DEBUG`、`SUI_DB_FOLDER` 三个；`SINGBOX_API` 在源码里没有任何引用。

</details>

**问题 3**：`/sub/` 下三种订阅输出是怎么区分的？`format=abc` 会怎样？

<details>
<summary>查看答案</summary>

同一个路径，靠查询参数区分：不带 `format` 是链接列表，`?format=json` 是 sing-box 配置，`?format=clash` 是 Clash.Meta 配置。只认 `json` 和 `clash` 两个字面值，写成别的返回 400。`HEAD` 请求只回响应头。

</details>

**问题 4**：客户端超了流量限额之后，最坏情况多久才断？依据是什么？

<details>
<summary>查看答案</summary>

最长约一分钟。判据由每分钟一轮的 deplete 任务扫描，命中本节那条 SQL（设了上限且上下行之和越过上限，或到期时间早于当前时刻）后置 `enable = false`，再重建相关入站的用户列表。手工在界面上停用是同步的。

</details>

**问题 5**：为什么订阅链接里的标识符不能随便改名？

<details>
<summary>查看答案</summary>

因为 URL 里那段就是 `clients` 表的 `name`，查询条件是 `enable = true and name = ?`。改名等于换链接，停用等于让原链接返回 400。

</details>

## 练习

三条练习的目标各不相同：第一条查清参数落在哪一层，第二条把订阅链路完整走通，第三条自己把配额判据复算一遍。每条都给了可判定的完成标准。

### 练习 1：确认参数到底存在哪

**任务**：把面板端口从 2095 改成别的值，并解释为什么改环境变量不行。

**步骤**：

1. `/usr/local/s-ui/sui setting -show` 记下当前值。
2. 用 `sui setting -port <新端口>` 修改，重启服务。
3. 再 `-show` 一次，比较前后差异。
4. 试着只设 `SUI_DB_FOLDER` 到一个空目录再启动，观察它是否重新插入 `admin/admin`。

**完成标准**：`-show` 的输出确实变了；空目录下出现了新的 `s-ui.db`，并且旧面板数据不再可见。第 4 步能复现出「只有 users 表为空时才种默认账号」这条规则。

### 练习 2：一个带 TLS 的入站与它的订阅

**任务**：走完「TLS 对象 → 入站 → 客户端 → 订阅地址」这条链，并验证配额字段真的出现在响应头里。

**步骤**：

1. 准备一份证书（acme.sh 或 certbot 均可）。
2. 「TLS 设置」建对象，「入站管理」建 `vless` 入站并关联它。
3. 「用户管理」建客户端，绑上这个入站，限额填 1 GB、到期填 30 天后。
4. 取订阅地址，先看 `HEAD`：

   ```sh
   curl -sI "http://127.0.0.1:2096/sub/<客户端名>"
   ```

5. 再看正文是不是 Base64：

   ```sh
   curl -s "http://127.0.0.1:2096/sub/<客户端名>" | base64 -d | head
   ```

**完成标准**：`Subscription-Userinfo` 里的 `total` 等于 1 GB 对应的字节数，`expire` 是一个未来的 Unix 秒；第 5 步能解出以 `vless://` 开头的行。解不出来就说明 `subEncode` 被关过。

### 练习 3：把配额判据跑出来

**任务**：用只读 SQL 复算面板的停用判断，理解「最长一分钟」这个数从哪来。

**步骤**：

1. `-output` 是必填项（不给就只打一行失败提示），产物本身就是一个 SQLite 文件：`/usr/local/s-ui/sui backup -output backup.db`，或写 `-output -` 把字节流重定向到文件。之后的查询都在副本上做，别碰运行中的库。
2. 用 `sqlite3` 查：

   ```sql
   SELECT name, enable, volume, up+down AS used, expiry
   FROM clients
   WHERE (volume > 0 AND up+down > volume) OR (expiry > 0);
   ```

3. 对照「基础信息」页的变更列表，找执行者为 `DepleteJob` 的行，看它们的时刻间隔。

**完成标准**：能解释查询结果里每一行为什么是（或不是）被停用的对象；变更列表里相邻两轮 `DepleteJob` 的时间差约等于 60 秒。若第 3 步一行都找不到，说明还没有客户端触顶，先手动把某个客户端的配额上限调到低于它的已用流量，再等一轮。

## 下一步读哪份代码

按顺序读，每份都能在十几分钟内读完，且能直接回答一个上文留白。

1. `core/endpoint.go`，128 行。面板与内核的全部交互面就是里面那八个函数：入站、出站、节点、服务四类，各一个 Create 一个 Remove，没有第五类动作。读完也就知道「即时生效」的边界在哪。
2. `service/inbounds.go` 的 `Save`（`:104` 起）：事务边界、用户拼装、先摘旧 tag 再加新入站的顺序都在这里，也解释了 `tag` 为什么必须唯一。
3. `service/client.go` 里的 `DepleteClients` 与 `ResetClients`。配额、到期、延迟开始、周期重置四件事的实现集中在这一处，`changes` 表的审计习惯也是从这里开始的。
4. `cmd/migration/` 从 `1_2.go` 一路翻到 `1_6_3.go`。这是最快的项目历史课，每个文件对应一次破坏性变更，也是排查存量部署时最可能被引用的一批代码。
5. 前端仓库 `alireza0/s-ui-frontend` 的 `src/locales/en.ts` 与 `src/locales/zhcn.ts`。界面字段到底对应哪个配置键，查这里比猜快。

进阶方向不在面板这一侧：面板只保证字段能存下、能推给内核，路由与传输层的语义要去读 sing-box 的 `option` 包和它的迁移文档。

## 资料口径与核查方法

**代码口径**：`alireza0/s-ui` 的 `main` 分支，提交 `13abbdc431ae`，标签 `v1.6.3`（2026-09-16）。克隆深度 50 个提交，`git ls-remote --tags` 与 releases 列表一起取。文中所有 `文件:行号` 都按这一版本复核过。

**界面文案口径**：前端仓库 `alireza0/s-ui-frontend` 的 `main` 分支，`src/locales/` 下 `en`、`fa`、`ru`、`vi`、`zhcn`、`zhtw` 六种，与 README 声明的语言数量一致；`package.json` 的版本号与后端同为 1.6.3。

**计数口径**：星标、复刻、未关闭条目、贡献者取自带认证的 GitHub 接口，取值时间 2026-09-25。`open_issues_count` 是议题与拉取请求的合计，不要当成「积压缺陷数」。

**未验证的部分**，明确列在这里：

- 本机无 Go 工具链，`go build` 与 `./sui` 都没跑过，所以本文没有任何一条来自实跑的运行时结论。行为判断全部来自源码、脚本与官方文档，接口应答体格式未核实。
- sing-box 上游 `v1.14.1` 与 `v1.14.2` 之间的差异未展开，只核到版本号。
- 「面板 UI 里每个表单字段的完整清单」未展开，只核到与本文流程相关的 TLS 关联、tag、监听、配额、到期几项。
- README 与代码冲突之处，本文一律以代码为准，并把冲突写出来（macOS 产物、compose 的端口、环境变量的两行、`systemctl enable sing-box`）。这类冲突在快速迭代的个人项目里是常态，不是错误。

**给后来改这篇的人**：最值得复查的是这三处。一是 `service/setting.go` 的 `defaultValueMap`，加默认项或改默认值都会让本文的表失效；二是 `install.sh` 的架构映射与下载文件名，它决定「支持哪些平台」这句结论；三是 `cronjob/cronJob.go` 里那几个 `@every`，配额延迟、在线列表粒度、看门狗三处排查全靠它。改标题或加小节后要重算目录锚点。

## 参考链接

- 仓库：<https://github.com/alireza0/s-ui>
- 前端仓库：<https://github.com/alireza0/s-ui-frontend>
- 官方 Wiki（六个页面均在 README 的文档表里列出）：<https://github.com/alireza0/s-ui/wiki>
- 订阅服务说明：<https://github.com/alireza0/s-ui/wiki/Subscription-Service>
- 设置项参考：<https://github.com/alireza0/s-ui/wiki/Settings-Reference>
- 接口文档（`/apiv2`，令牌认证）：<https://github.com/alireza0/s-ui/wiki/API-Documentation>
- 内嵌内核：<https://github.com/sagernet/sing-box>
- sing-box 迁移指引（1.14 废弃项）：<https://sing-box.sagernet.org/migration/>
