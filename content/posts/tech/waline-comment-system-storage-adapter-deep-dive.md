---
title: "Waline：静态博客的评论区，为什么值得像换数据库一样挑后端"
date: "2026-08-26T15:30:00+08:00"
slug: "waline-comment-system-storage-adapter-deep-dive"
description: "walinejs/waline 深度解析：一个把评论系统拆成「客户端—服务端—存储适配器」三层的开源项目。从 storage/base.js 的五个抽象方法讲到七种存储实现（SQLite/MySQL/PostgreSQL/MongoDB/TiDB/LeanCloud/GitHub），从一条评论落库前要过的五道反垃圾闸讲到通知矩阵，最后给出按场景选后端的决策建议。"
draft: false
categories: ["技术笔记"]
tags: ["Waline", "评论系统", "静态博客", "ThinkJS", "存储适配器", "Serverless", "开源项目", "Valine", "XSS", "反垃圾"]
github_repo: "walinejs/waline"
source_key: "gh:walinejs/waline"
---

## 开场：它解决的不是评论区 UI，是"静态博客缺一个自带后端"

静态博客（Hugo、Hexo、VuePress、VitePress）天生没有服务端。页面是构建时生成的静态文件，而评论区偏偏是需要写、需要存、需要管的一类功能——这是静态站唯一的"动态"需求，也是它始终绕不开的最后一公里。

Waline 对这件事的回答是：把评论系统拆成三层，让"服务端"和"存储"都变成可以随意替换的组件，然后给出一个不需要自己买服务器就能跑的默认路径。它挂在 [walinejs/waline](https://github.com/walinejs/waline) 下，作者是 lizheming 与 Mr.Hope，GPL-2.0 协议，README 的第一句话是"A simple comment system with backend support"——注意，它没有把自己包装成"下一代评论平台"，而是老老实实说自己是"带后端的评论系统"。

它真正的工程价值，不在评论区长什么样，而在那条把"评论"做成可插拔适配链的架构：

```text
客户端（前台组件）→ 服务端（REST API + 业务流水线）→ 存储适配器（数据库/文件/第三方）
```

## 总览地图：三层架构 + 243 种组合

Waline 在 README 里给了一张三列表格，把可替换性写进了门面。我把它整理成下面的职责对照表：

| 层 | 可选实现 | 作用 |
|---|---|---|
| **Client** | `@waline/client`、MiniValine、sodesu | 前台渲染：评论表单、列表、表情、@、赞、置顶 |
| **Server** | Vercel、CloudBase、Railway、Render、Zeabur、Netlify、阿里云计算巢、Docker、自托管 | 评论落库前的所有业务逻辑 + API |
| **Storage** | PostgreSQL、MySQL、SQLite、TiDB、MongoDB、CloudBase、GitHub | 评论/用户/计数数据的持久化 |

三层各自可换，组合起来 README 声称"at least 243 deployment choice"。这个数字是把"你选一个前端 × 选一个部署平台 × 选一个存储"的自由度量化了——对站长来说，它意味着"免费 + 自控"这件事真的能落地，而不是只能选一条被绑死的路。

后面每一节都在讲同一件事：这三层之间到底怎么接、接得稳不稳。

## 它在评论系统的谱系里站在哪

Waline 不是从零发明了"静态站 + 评论区"这个需求，它继承了一个明确的生态位。

它的存储后端列表里保留了 **LeanCloud**（`LEAN_KEY` 环境变量就能激活），这是 Valine 时代静态博客最常用的后端；官方文档专门留了"从 Valine 迁移"（Migration from Valine）的向导和"数据迁移助手"，README 也挂出了中文入口。这些证据拼在一起，Waline 的定位就很清楚了：它站在 Valine 的延长线上，补上了 Valine 生态里"服务端太薄、存储被绑死"的那一块。

Valine 的经典问题是：它本身只是个前端组件，数据依赖 LeanCloud，一旦 LeanCloud 免费额度收紧或者你想换存储，整套评论就动不了。Waline 的回应是把"存储"从一件默认绑定的事变成一层可插拔接口——这正是本文接下来要拆的核心机制。

## 服务端：一个 ThinkJS 应用，四层结构

先纠正一个容易误判的点：Waline 的服务端**不是**一个薄薄的 Node server 包装，而是一个完整的 **ThinkJS** 应用。

从源码能直接看到这点——`controller/comment.js` 里到处是 `think.Service`、`think.config`、`think.ip2region`、`think.uaParser`、`think.logger` 这类 ThinkJS 全局注入的调用。这意味着评论服务天生自带 ThinkJS 那套 MVC + 中间件 + hook 生态，而不是作者从零手搓路由。

服务端源码按 `packages/server/src/` 组织成清晰的四层：

| 层 | 目录 | 职责 |
|---|---|---|
| **Controller** | `controller/` | HTTP 出入口：comment / article / user / oauth / token / db / rest |
| **Logic** | `logic/` | 与 controller 一一对应的业务逻辑 |
| **Service** | `service/` | 可复用能力：storage / notify / akismet / avatar / markdown |
| **Middleware** | `middleware/` | 横切关注点：dashboard / plugin / version / prefix-warning |

`controller/comment.js` 通过继承 `BaseRest`（`controller/rest.js`）拿到 REST 语义，然后按 HTTP 方法分发：

- `getAction` → 三种列表：普通评论列表、`type=count` 的计数、`type=recent` 的最近评论、管理员列表
- `postAction` → 评论落库前跑完整条防垃圾流水线
- `putAction` → 更新（点赞、审核状态流转）
- `deleteAction` → 删除评论及其所有子回复

评论对象在返回前会经过 `formatCmt` 处理：解析 UA 得到浏览器/操作系统、根据 `AVATAR_PROXY` 加工头像、非管理员一律剥掉 `mail` 字段、把 markdown 渲染成 HTML、把 `insertedAt` 转成毫秒时间戳。这一串动作决定了"管理员和访客看到的是同一份数据的不同侧面"。

## 存储适配器：五个抽象方法，七种实现

`service/storage/base.js` 定义了存储层的抽象接口，全部是空实现占位：

```js
async select(where, options)      // 查询
async count(where, options)       // 计数
async add(data, options)          // 新增
async update(data, where)         // 更新
async delete(where)               // 删除
```

只要实现这五个方法，你的存储后端就能被 Waline 接进去。当前实现有七个：`leancloud`、`mongodb`、`postgresql`、`sqlite`、`mysql`、`tidb`、`github`，再加上 CloudBase 特化——每个都是这套接口的一个具体落点。

存储的选择不是靠配置文件手动指定的，而是靠 `config/config.js` 里一段按优先级走的自动检测链：

```text
LEAN_KEY → MONGO_DB → PG_DB/POSTGRES_DATABASE → SQLITE_PATH
→ MYSQL_DB → TIDB_DB → GITHUB_TOKEN → CloudBase(TCB_ENV)
```

谁的环境变量先存在，谁就是存储后端；一个都没有，直接 `throw new Error('No valid storage found')`。JWT 密钥也顺带从对应存储的密码环境变量里兜底派生——这是"少一个配置就少一个出错点"的取舍。

这套抽象在 `service/storage/order.js` 里有实际支撑：排序归一化工具（`normalizeOrder` / `toSqlOrder` / `compareByOrder`），把"asc/desc + NULLS FIRST/LAST"这套 SQL 语义统一成各后端都能消费的形式；MySQL、PostgreSQL 这类 SQL 后端各自把 where 条件编译成对应方言，GitHub 后端则完全换了一种活法。

### 特写：GitHub 后端，把数据库存成三个 CSV 文件

在七个实现里，`storage/github.js` 是最反直觉也最能说明"适配器"精神的一个。

它把整张表存成一个 CSV 文件，挂在某个 GitHub 仓库里：

- `Comment.csv`——评论主表
- `Counter.csv`——评论计数 / 浏览量
- `Users.csv`——用户表

读写靠 GitHub Contents API（`/repos/{owner}/{repo}/contents/{path}`），用 `fast-csv` 做序列化。源码里有个细节直接暴露了这套方案的边界：

```js
// content api can only get file < 1MB
async get(filename) { ... }
async getLargeFile(filename) { ... }  // 超过 1MB 走 git/trees + blob API
```

也就是说，GitHub Contents API 的 1MB 单文件上限是代码里明确处理的：小文件走 Contents API，大文件回退到 blob 接口。查询也不是数据库引擎干的，而是 `parseWhere` 把 where 条件翻译成一串内存过滤函数——`IN`、`NOT IN`、`LIKE`（含 `%` 前缀/后缀/两侧匹配）、`!=`、`>`，甚至 `_complex` 的 and/or 组合逻辑都是手写的数组 filter。

这套实现的取舍很清楚：**它是给"零成本、低并发、数据量小"的场景设计的**。GitHub API 的请求频率限制和单文件体积限制天然决定了它不是生产级高并发的选项，但它把一个评论系统的全部数据放进一个 Git 仓库里，等于顺带拿到了版本历史、免费托管、和"随时能看见数据"的透明性——对个人博客来说，这三样恰恰是刚需。

## 一条评论落库前，要过五道闸

`postAction` 的防垃圾流水线是理解 Waline 安全观的最佳切片。访客发一条评论，按顺序撞上五道检查，每一道都能让评论直接打回或标记为 spam：

1. **IP 黑名单**（`disallowIPList`）——命中直接 `ctx.throw(403)`。
2. **重复内容检查**——同一个人（按 mail+nick+link+comment）发过相同内容，拒绝。
3. **IP 频率限制**——环境变量 `IPQPS`（默认 60），60 秒内同 IP 再发，拒绝。这是源码里的默认值，可调。
4. **Akismet**——已批准的评论会送进 Akismet 判垃圾，命中则状态设为 `spam`。这里特意用了 `.catch()` 吞掉 Akismet 服务异常——第三方挂了不影响评论主流程。
5. **关键词过滤**（`forbiddenWords`）——配置里的禁用词表拼成正则，命中即 `spam`。

另外还有一个总开关：环境变量 `COMMENT_AUDIT` 打开审核模式后，新评论初始状态是 `waiting` 而不是 `approved`，只有管理员在后台通过才公开。

注意这套流水线的顺序：便宜的先跑，贵的后跑。IP 黑名单是内存里的数组查找，几乎零成本；Akismet 是外部 HTTP 调用，放在靠后的位置，还专门做了失败容错。把最贵的外部调用放在最后，就算它挂了，前四道本地闸也已经把绝大多数垃圾挡在门外。

落库前后还各有一次 hook 调用（`preSave` / `postSave`，以及 `putAction` 里的 `preUpdate` / `postUpdate` / `preDelete` / `postDelete`）——plugin 系统就是挂在这几个 hook 上的（2023-05 的 CHANGELOG 里写着"add plugin system support"）。

## 通知矩阵：一条评论能跑到七个渠道

评论通过审核后，`notify.js` 会把"有新评论 / 有人回复你"这件事推送出去。它支持的渠道和对应的环境变量，从 `config.js` 和 `notify.js` 里能完整对上：

| 渠道 | 关键环境变量 | 实现要点 |
|---|---|---|
| **邮件** | `SMTP_*`、`SENDER_*` | nodemailer，支持 host/port/secure 或 service 两种配置 |
| **微信（Server酱）** | `SC_KEY` | 走 `sctapi.ftqq.com`，表单提交 text+desp |
| **QQ** | `QQ_TEMPLATE` | 模板渲染后走对应通道 |
| **Telegram** | `TG_TEMPLATE` | 同上 |
| **Discord / 飞书（Lark）** | `DISCORD_TEMPLATE` / `LARK_TEMPLATE` | 同上 |
| **Bark** | — | iOS 推送 |

通知内容用 **nunjucks 模板**渲染，模板里注入 `self`（当前评论）、`parent`（父评论）、`site`（站点名/URL/评论锚点）三个上下文对象——所有渠道共用同一套数据模型，只是模板不同。`config.js` 里 `MAIL_SUBJECT` / `MAIL_TEMPLATE` / `WX_TEMPLATE` / `TG_TEMPLATE` 这些环境变量允许站长覆盖默认模板，等于把"通知文案"也做成了可配置项。

## 安全底线：markdown 渲染前的 XSS 加固

评论允许完整 markdown，意味着服务端必须把"渲染出的 HTML"当成不可信输入处理。Waline 用的是 `markdown/xss.js`：`DOMPurify` + `JSDOM` 做消毒。

关键不在"用了 DOMPurify"，而在它怎么用：

```js
DOMPurify.sanitize(content, {
  FORBID_TAGS: ['form', 'input', 'style'],
  FORBID_ATTR: ['autoplay', 'style'],
  ...think.config('domPurify'),
});
```

禁掉表单、输入框、style 标签，禁掉 autoplay 属性，并且允许通过 `domPurify` 配置继续叠加约束。两个 hook 值得一提：

- `uponSanitizeElement`——专门移除 `annotation` 标签（修过 GitHub issue #3238，属于 math 渲染引发的现实问题）。
- `afterSanitizeAttributes`——给所有外链强制加 `target="_blank"` 和 `rel="ugc nofollow noreferrer noopener"`。`ugc` 告诉搜索引擎"这是用户生成内容"，`nofollow` 断了评论区的 SEO 权重通道，`noopener noreferrer` 堵住 `window.opener` 反向劫持。

`preload` 属性统一设成 `none`，则是不让评论里的媒体预加载拖垮页面。这些细节是"评论系统安全"和"评论系统能用"的分水岭——很多同类项目死在评论区变成 SEO 垃圾场或钓鱼入口。

## 一次评论的完整旅程

把上面所有机制串起来，一次真实的评论提交长这样：

1. 访客在博客页填好昵称、邮箱、内容，`@waline/client` 把数据 `POST /api/comment` 发给服务端。
2. `CommentController.postAction` 收到请求，组装 `data`（含 `ip`、`insertedAt`、`user_id`）。
3. 非管理员路径下，撞上五道反垃圾闸：IP 黑名单 → 重复检查 → IPQPS 频率 → Akismet → 关键词。全部通过，状态定为 `approved`（或审核模式下为 `waiting`）。
4. 触发 `preSave` hook（插件可在此拦截）。
5. `storage.add(data)`——数据落到你选的存储后端：SQLite 写一行、MySQL 执行一条 INSERT、或者 GitHub 后端把新行写进 `Comment.csv` 并 PUT 回仓库。
6. 触发 `new_comment` webhook，再触发 `postSave` hook。
7. 状态非 spam 时，`notify.js` 按配置把"新评论"推给站长（和/或父评论作者）：邮件、微信、Telegram……模板渲染出各渠道格式。
8. 浏览器收到格式化后的评论对象，`formatCmt` 已经完成 UA 解析、头像代理、markdown 渲染、敏感字段剥离。

这条链路里，第 3 步的防垃圾和第 7 步的通知是"业务逻辑"，第 5 步是"存储差异"，其余全是框架和模板的固定动作。Waline 的价值恰恰在于：**把"业务逻辑"和"存储差异"切成两半，换存储时业务逻辑一行不用动**。

## 怎么选后端：这是决策，不是营销

对不同场景，正确的后端选择差异很大。把源码里能看到的约束摆出来，比给一张"推荐榜"更有用：

- **零成本个人博客**：Vercel + Neon（PostgreSQL 免费层）是官网文档的主推路径——Vercel 模板一键部署，Neon 里执行 `waline.pgsql` 建表，配个域名就是一套免费评论服务。
- **极简自托管**：SQLite。一个文件就是全部数据，备份=拷贝文件。代价是单实例、并发能力弱——从 `config.js` 里"CloudBase 平台不能用 SQLite"的硬性报错能看出它默认是单机场景。
- **生产级 / 多实例**：PostgreSQL / MySQL / MongoDB。有真正的并发和事务语义，适合流量上来以后。
- **“把数据放进 Git”**：GitHub 后端。免费、透明、有版本历史，但受 GitHub API 频率和 Contents API 单文件 1MB 上限约束——只适合低流量。
- **Valine 老用户**：LeanCloud 后端直接保留，官方还有迁移助手。

反过来，"什么时候不该用 Waline"同样值得说清：如果你的需求是完整社区（点赞聚合、徽章体系、多管理员协作、企业级 SLA），Waline 的定位是"评论系统"而不是"讨论平台"，admin 面板（`packages/admin`，React 写的）能管评论和用户，但不会替你解决社区运营。它最适合的场景是**静态博客的评论区这个精确需求**。

## 结尾：一条适配链，补上静态站的最后一公里

回到开头那个判断。Waline 真正被低估的不是"它是个评论系统"，而是它把评论系统拆成了**可以各自替换的三层**，并且用五个抽象方法把存储做成了插拔接口——这让"静态博客缺一个自带后端的评论服务"这个老问题，第一次有了"免费 + 自控 + 可选后端"的完整答案。

它的代码没有炫技，但有几处决定性的工程取舍：反垃圾流水线把最贵的外部调用放在最后、Akismet 挂了不拖垮主流程、GitHub 存储明知道有 1MB 限制仍然做了大文件回退、XSS 消毒连 `annotation` 标签这种边角都修过。这些细节加在一起，才撑得起 README 里那句带着强调的 "**Really** Safe"。

对想给博客加评论区的站长，决策路径是现成的：先按官方 Vercel + Neon 跑通，再根据流量和隐私需求决定要不要换 SQLite 自托管或换回自己熟悉的数据库。静态站的最后一公里，从"要不要"变成了"怎么选"。

> 本文事实全部来自 walinejs/waline 仓库 README、packages 源码（`controller/comment.js`、`service/storage/*.js`、`service/notify.js`、`service/markdown/xss.js`、`config/config.js`）、`openapi.yaml`、CHANGELOG 与官方文档 Vercel 部署页，写作时未引用仓库外资料。Waline 官网文档在 https://waline.js.org/ 。
