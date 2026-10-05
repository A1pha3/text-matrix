---
title: "awesome-go：3000 多个条目背后，是一台持续运转的筛选机"
date: "2026-08-20T20:00:00+08:00"
lastmod: 2026-09-30T00:00:00+08:00
slug: "awesome-go-go-ecosystem-curated-list"
github_repo: "avelino/awesome-go"
source_key: "gh:avelino/awesome-go"
description: "awesome-go 是 GitHub 星标数最高的 Go 语言资源列表（186,145 stars），收录 70 多个分类、3000 多个项目。它的价值不在收录量，而在每一条目都要过的人工与 CI 双重筛选门槛。"
draft: false
categories: ["技术笔记"]
tags: ["Go", "开源"]
---

# awesome-go：3000 多个条目背后，是一台持续运转的筛选机

> 整理：钳岳星君 🦞｜更新时间：2026 年 9 月 30 日
>
> 项目地址：https://github.com/avelino/awesome-go
>
> 官方网站：https://awesome-go.com/

用 awesome-go 找库，真正值钱的不是那 3000 多个条目——搜索引擎随便一搜也能给你一堆 Go 库的名字。值钱的是每个条目背后那道门槛：仓库至少 5 个月历史、有开源许可证和 `go.mod`、打过一个 SemVer 标签、测试覆盖率达标、Go Report Card 评分不低于 A-，而且这些条件大半由 CI 自动验证。达不到的项目，PR 会被直接关掉。

所以把它当"导航站"理解会低估它：它更像一台持续运转的筛选机。条目进来要过闸，进来之后还要持续达标——一年内没发过正式版本、issue 还挂着没人理的项目，社区可以开 PR 把它移出列表。logrus 这个曾经最流行的 Go 日志库，如今已经不在这份列表里。

## 项目档案

| 项目 | 值 |
|------|-----|
| Stars / Forks | 186,145 / 13,591（截至 2026-09-30） |
| 创建时间 | 2014 年 7 月 |
| 开源协议 | MIT |
| 维护者 | [Avelino](https://github.com/avelino) 与社区维护者团队 |
| 载体 | 单个 README，约 4100 行 |
| 分类规模 | 70 多个工具分类、8 个资源分类、3000 多个条目 |

它有一句官方自我定位，写在贡献指南开头：这份列表存在的意义是"与优秀的 Go wiki Projects 页面互补"（complement the excellent Go wiki Projects page）。[Go wiki Projects](https://go.dev/wiki/Projects) 收录宽松、接近全量；awesome-go 收录严格、人工筛选。两者的分工写在纸面上。

## 分类地图

整个列表按"先分类、后字母序"组织。70 多个分类里，日常后端开发用得到的集中在下面这些：

| 场景 | 分类 | 里面的常见面孔 |
|------|------|----------------|
| 命令行 | Command Line | cobra、urfave/cli、bubbletea |
| 配置 | Configuration | viper、koanf、cleanenv |
| 日志 | Logging | zap、zerolog |
| Web | Web Frameworks | Gin、Echo、Fiber、Chi |
| ORM | ORM | GORM、ent、bun、SQLBoiler |
| 数据库 | Database（Caches、Schema Migration、SQL Query Builders 等子栏） | ristretto、bigcache、golang-migrate、Squirrel |
| 消息与任务 | Messaging | Asynq、machinery、sarama、nats.go |
| 认证授权 | Authentication and Authorization | casbin、oauth2、go-jose、scs |
| 安全 | Security | age、nacl、memguard |
| 测试 | Testing | testify、GoConvey、mockery |

再往外一圈：Artificial Intelligence 分类收录 langchaingo、LocalAI、Ollama 这些 AI 应用基础设施；Machine Learning 和 Science and Data Analysis 收录 Gorgonia、GoLearn、Gonum；工具链方向的 Go Tools、Code Analysis 收录 gopls、staticcheck、golangci-lint，SQL Query Builders 里还有能从 SQL 生成类型安全代码的 sqlc。更特殊的领域——Blockchain（go-ethereum、cosmos-sdk）、Game Development（Ebitengine）、GUI（fyne）、Financial（techan、shopspring/decimal）、WebAssembly（tinygo）——各自成栏。

用法上有个省力的细节：分类内条目严格按字母序排列，这是 CI 强制检查项。所以翻列表时不用怕漏，从上到下扫一遍就是全量；反过来，这也意味着列表不会告诉你"哪五个最值得用"——排序只反映字母，不反映质量。

## 列表是活的

判断一份 awesome 列表还值不值得信，最直接的办法是看它动不动。awesome-go 的维护痕迹在条目描述里就能看到：

- [kingpin](https://github.com/alecthomas/kingpin) 的条目写着 "superseded by `kong`"——被取代的库不会悄悄躺着，描述里直接指路后继者。
- sarama 的条目链接还是 `github.com/Shopify/sarama`，点击后 301 跳转到 `IBM/sarama`——2023 年 Shopify 把这个 Kafka 客户端移交给了 IBM，列表链接保留了历史路径。
- drone 的条目旁边能看到 [woodpecker](https://github.com/woodpecker-ci/woodpecker)，描述里明说它是 "community fork of the Drone CI system"——drone 被 Harness 收购后社区分叉，两者同栏并存。
- logrus 曾经是 Go 生态最常用的结构化日志库，如今列表里只剩两个集成插件在描述里引用它，条目本身已被移除——它 2021 年起进入维护模式，最终被清出了列表。

这四个例子合起来说明一件事：这份列表的条目会过期，但过期项会被处理。选型时仍然要自己看最后一次 commit 时间，但"列表里还在"至少意味着某个维护者近期确认过它达标。

## 收录门槛：一个 PR 要过哪些关

awesome-go 的 [CONTRIBUTING.md](https://github.com/avelino/awesome-go/blob/main/CONTRIBUTING.md) 把收录标准写成了可执行的清单。一个 PR 提交后，先过 CI 自动检查，再过人工审查。

**CI 自动拦截项**（任一失败无法合并）：

- 仓库可访问且未归档；根目录有 `go.mod`；有至少一个 `vX.Y.Z` 格式的 tag
- pkg.go.dev 链接可访问；Go Report Card 评分达到 A-、A 或 A+
- 一个 PR 只加一个项目；条目按字母序插入；链接不与现有条目重复；描述以句号结尾

**人工审查项**：

- 仓库至少 5 个月历史，有开源许可证
- 测试覆盖率：非数据类包 ≥80%，数据类包 ≥90%（维护者会人工核实覆盖率是不是真跑出来的，拿 benchmark 数字充数会被识破）
- 文档是英文的：README 加上公共 API 的 doc comments
- issue 和 PR 一般在两周内有响应（已完成且稳定的项目，以"没有超过 6 个月未处理的 bug"替代）
- 功能与文档描述一致，且"对更广泛的 Go 社区普遍有用"

**进了列表不等于终身制**。在榜项目要维持质量：持续开发的，每年至少发一个正式版本；停止开发的，得证明项目稳定（没有超过 6 个月无人处理的 bug 报告）。移除流程也写得很克制——开移除 PR 后要在原项目提 issue 通知作者，留出两周响应期，给临时陷入维护低谷的项目留缓冲。

这套门槛的直接后果是收录率不高：新分类至少要有 3 个项目才能设立，维护者 15 天等不到作者补充材料就会关闭 PR。反过来，过了这一整套流程的条目，至少排除了"没有许可证""没有版本号""文档残缺""无人维护"这四类最常见的坑。

## 任务流案例：给 Go 服务选一个任务队列

用一个具体场景走一遍完整路径。需求：Go 后端要加任务队列，要求能持久化、支持重试、有 Web 监控面板。

**第一步，定位分类。** 打开 [awesome-go.com](https://awesome-go.com/)，这个需求对应 Messaging 分类——分布式任务队列和消息客户端都收在这一栏。旁边的 Job Scheduler 分类是定时任务（cron 语义），跟"投递任务给 worker 消费"不是一回事，别走错栏。

**第二步，列候选。** Messaging 一栏里和"任务队列"直接相关的条目：

- [Asynq](https://github.com/hibiken/asynq) - Redis 之上的分布式任务队列，最新版 v0.26.0（2026 年 2 月发布）
- [machinery](https://github.com/RichardKnop/machinery) - 基于分布式消息传递的异步任务队列
- [NATS Go Client](https://github.com/nats-io/nats.go) - NATS 消息总线的官方客户端
- [sarama](https://github.com/Shopify/sarama) - Apache Kafka 客户端（偏流处理，不是任务队列）

**第三步，按需求砍。** 四个维度过一遍：

| 候选 | 持久化 | 内置重试 | Web 面板 | 定位 |
|------|--------|----------|----------|------|
| Asynq | Redis | 有 | asynqmon | 任务队列 |
| machinery | Redis/AMQP/MongoDB 等 | 有 | 无 | 任务队列 |
| nats.go | 视部署配置 | 需自建 | 无 | 消息总线 |
| sarama | Kafka | 需自建 | 无 | Kafka 客户端 |

"消息总线"和"任务队列"的区别在这一步很关键：nats.go、sarama 给你的是消息传递原语，重试、退避、死信这些语义要自己往上搭；Asynq 和 machinery 把这些做成了开箱即用的功能。需求里明确要重试和监控面板，砍掉后两个。

**第四步，验证关键假设。** asynqmon 是不是真的开箱即用？看 [asynqmon 仓库](https://github.com/hibiken/asynqmon)——一个独立的 Web UI 项目，一条 `docker run` 就能跑起来，未归档、持续维护。假设成立。

**第五步，落地。** `go get github.com/hibiken/asynq`，Redis 用 6 以上版本，写代码（见下一节），部署 asynqmon 容器看面板。

这个流程里 awesome-go 起的作用是第二步：候选集一开始就限定在经过筛选的 Go 原生方案里，不会被搜索引擎带到语言不匹配或者早已停维护的博客推荐上。至于第三步往后的判断——那是列表给不了的，得自己读 README 和 issue。

## 最小可运行示例

沿用上面的选型结果，跑通 Asynq 的最小闭环。两个进程：client 投递任务，worker 消费。

**项目结构**：

```text
asynq-demo/
├── go.mod
├── client.go
└── worker.go
```

**go.mod**：

```text
module asynq-demo

go 1.24

require github.com/hibiken/asynq v0.26.0
```

**client.go**：投递一个带重试和超时设置的任务。

```go
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"time"

	"github.com/hibiken/asynq"
)

const TaskEmailWelcome = "email:welcome"

func main() {
	client := asynq.NewClient(asynq.RedisClientOpt{Addr: "localhost:6379"})
	defer client.Close()

	payload, err := json.Marshal(map[string]any{"user_id": 42})
	if err != nil {
		log.Fatalf("marshal payload: %v", err)
	}

	task := asynq.NewTask(
		TaskEmailWelcome,
		payload,
		asynq.MaxRetry(3),
		asynq.Timeout(30*time.Second),
	)

	info, err := client.Enqueue(task)
	if err != nil {
		log.Fatalf("enqueue: %v", err)
	}
	fmt.Printf("enqueued: id=%s queue=%s\n", info.ID, info.Queue)
}
```

**worker.go**：注册处理器并阻塞消费。

```go
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"

	"github.com/hibiken/asynq"
)

func handleEmailWelcome(ctx context.Context, t *asynq.Task) error {
	var p struct {
		UserID int `json:"user_id"`
	}
	if err := json.Unmarshal(t.Payload(), &p); err != nil {
		return fmt.Errorf("unmarshal payload: %w", err)
	}
	fmt.Printf("sending welcome email to user %d\n", p.UserID)
	return nil
}

func main() {
	srv := asynq.NewServer(
		asynq.RedisClientOpt{Addr: "localhost:6379"},
		asynq.Config{Concurrency: 5},
	)

	mux := asynq.NewServeMux()
	mux.HandleFunc(TaskEmailWelcome, handleEmailWelcome)

	if err := srv.Run(mux); err != nil {
		log.Fatal(err)
	}
}
```

**运行**：

```bash
# 1. 启动 Redis（需要 6+ 版本）
docker run -d -p 6379:6379 redis:7

# 2. 启动 worker
go run worker.go

# 3. 另开终端投递任务
go run client.go

# 4. 启动 asynqmon 监控面板（连接宿主机上的 Redis）
docker run --rm -p 8080:8080 hibiken/asynqmon --redis-addr=host.docker.internal:6379
# 浏览器打开 http://localhost:8080 查看任务状态
```

## 谁该用，怎么用

**当第一站用，不当终审用。** 遇到"Go 有没有现成的 X"这类问题，先翻对应分类，候选集几小时内就能收敛到两三个；最终决策仍然要读候选库的 README、issue 响应和最近 commit——列表保证了下限，选型判断还得自己做。

**三类场景它帮不上忙**：找某个领域最新的库（收录依赖社区 PR，新项目要攒满 5 个月历史才有资格提名）；找中文文档（收录标准要求英文文档，中文资料得去别处找）；找应用层的完整方案（列表收的是框架和库，不是脚手架和产品）。

**贡献者视角**值得一提：如果你的库想进列表，PR 描述里直接附上 forge 链接、pkg.go.dev、Go Report Card 和覆盖率报告四个链接，一个 PR 只改一个条目，描述一句话说清解决什么问题、以句号结尾。缺什么维护者会留言，15 天内补齐即可——这套流程的每一步都写在贡献指南里，照着做能省掉大部分往返。

回到开头那台筛选机的比喻：186,145 个 star 给 awesome-go 投的票，与其说是"这列表好用"，不如说是"有人替我把关这件事值得持续存在"。70 多个分类、3000 多个条目、一套写进 CI 的准入规则，加上 logrus 出列这样的持续清理——它解决的从来不是"找到库"，而是"筛掉不值得看的库"。
