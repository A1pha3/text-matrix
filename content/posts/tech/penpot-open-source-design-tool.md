---
title: "Penpot 深度解析：开放标准、Clojure 全栈与设计即代码"
date: "2026-04-27T20:00:00+08:00"
lastmod: "2026-09-26T18:00:00+08:00"
slug: "penpot-open-source-design-tool"
github_repo: "penpot/penpot"
source_key: "gh:penpot/penpot"
description: "Penpot 是西班牙公司 Kaleidos 开源的设计协作平台，以 SVG/CSS/HTML/JSON 开放标准为核心，前后端均以 Clojure 构建，渲染热点交给 Rust。本文梳理其架构、实时协作机制、2.0 到 2.18 的特性演进与自托管实践。"
draft: false
categories: ["技术笔记"]
tags: ["设计工具", "开源", "设计系统"]
---

多数「Figma 开源替代品」的介绍把 Penpot 讲成一个价格故事：免费、开源、可自托管。这些都属实，但不是它的技术个性。Penpot 真正的不同在于两点：设计资产从头到尾活在开放标准（SVG/CSS/HTML/JSON）里，不依赖私有文件格式；整个平台用 Clojure 写成，前后端共享同一套代码与数据结构，性能热点则交给 Rust 编写的渲染引擎。

到 2026 年 9 月，这个项目已在 GitHub 积累约 6 万 stars，发布到 2.18 版本，插件系统、原生设计令牌、组件变体与 MCP 服务器相继落地。本文按架构、版本演进与部署三条线拆解它，最后给出采用判断。

## 项目档案

| 项目 | 现状（2026-09 核实） |
| --- | --- |
| 仓库 | [penpot/penpot](https://github.com/penpot/penpot) |
| 许可证 | MPL-2.0 |
| 开发方 | Kaleidos（西班牙开源公司） |
| 主要语言 | Clojure（前后端）、Rust（渲染引擎）、TypeScript（插件生态） |
| Stars | 约 60,400 |
| 最新版本 | 2.18.0（2026-09-23） |
| 部署形态 | 官方 SaaS、Docker、Kubernetes（Helm）、Elestio |
| 认证 | 联合国数字公共产品（DPG）认证 |

MPL-2.0 是文件级 copyleft 许可证：可以商用、可以集成进闭源产品，只有对 Penpot 源码文件本身的修改需要开源。对想基于它做二次开发的企业，这比 GPL 类许可证的限制少得多。

## 设计即代码：开放标准如何落地

Penpot 诞生的出发点是设计工具行业的一个老问题：设计稿活在私有格式里，开发者要靠「标注」和「交接」把设计信息翻译成代码。这个翻译环节消耗时间，也制造偏差——设计稿上是一回事，实现出来是另一回事。

Penpot 的解法是把翻译环节直接消掉，具体落在三件事上：

**画布语义对齐 CSS**。布局工具直接使用 CSS Flexbox 和 Grid 的语义。设计师在画布上摆的是「一个 `display: grid` 的两列布局」，而不是一个碰巧长得像它的图形组合。开发者在 Inspect 标签页看到的代码就是画布语义的直接翻译，不需要二次解读。

**输出全是开放格式**。导出 SVG、CSS、HTML，设计令牌按 W3C 设计令牌标准（DTCG JSON 格式）导入导出。任何能解析这些标准的工具都能处理 Penpot 的输出，不依赖 Penpot 本身。

**平台本身可自托管**。Docker 或 Kubernetes 部署后，数据库、资源文件、协作数据全在自己的基础设施里。设计资产的最终控制权不在任何厂商手上。

这套思路的实际约束也要说清楚：它要求设计师对 CSS 布局模型有基本概念。对纯视觉背景的设计师，Flex/Grid 语义的学习成本是真实的；对已经有 Web 概念的设计团队，这反而是优势——设计稿和代码天然一致。

## 技术架构：Clojure 全栈与 Rust 渲染

### 为什么是 Clojure

主流设计工具几乎都建在 TypeScript 或 C++ 上（Figma 的客户端核心是 C++ 编译的 WASM，界面层是 TypeScript）。Penpot 选 Clojure 是一个刻意的技术决策，官方架构文档给出的理由很直接：前端是 ClojureScript（编译到 JavaScript），后端是 Clojure（编译到 JVM 字节码），两端可以「无障碍地共享代码和数据结构」——一个形状的数据结构在浏览器和服务端是同一个定义，序列化、校验、业务逻辑写一遍两端用。

代价同样明显：Lisp 方言的括号风格和不可变数据模型对多数开发者是陌生的，招聘池远小于主流语言。Kaleidos 本身是西班牙的 Clojure 技术咨询公司，这个选择符合团队基因——对评估项目长期健康度的读者来说，这一点比「Clojure 好不好」更有信息量：语言选择与团队能力匹配，才是它能持续交付十八个 minor 版本的原因之一。

### 架构总览

```text
┌──────────────────────────────────────────────┐
│                浏览器（编辑器）                │
│    ClojureScript + React（经 rumext 绑定）    │
│    画布渲染：SVG/DOM，可切换 WebGL（beta）      │
└───────────────┬──────────────────────────────┘
                │ HTTP / WebSocket
┌───────────────┴──────────────────────────────┐
│             后端（Clojure / JVM）             │
│    REST API · 权限 · 文件变更事件广播          │
└──────┬─────────────┬──────────────┬───────────┘
       │             │              │
 ┌─────┴─────┐ ┌─────┴──────┐ ┌────┴─────────┐
 │PostgreSQL │ │Valkey/Redis│ │  对象存储     │
 │ 用户/文件/ │ │ 协作通知协调 │ │ fs 或 S3 兼容 │
 │ 变更历史   │ │ +缓存      │ │（媒体、字体）  │
 └───────────┘ └────────────┘ └──────────────┘

┌──────────────────────────────────────────────┐
│        Exporter（独立的导出服务）              │
│    ClojureScript 运行在无头浏览器中，           │
│    与前端共享基于 Skia 的 WASM 渲染引擎         │
└──────────────────────────────────────────────┘
```

几个值得注意的设计：

**前端不是 React 全家桶**。编辑器用 ClojureScript 写，React 只作为渲染层绑定（rumext 是 Clojure 社区的 React 封装），状态管理用 potok 等函数式方案，构建工具是 shadow-cljs。读源码前要有这个预期——这不是一个典型的 React 项目。

**导出是独立的浏览器环境**。Exporter 是一个运行在无头浏览器里的 ClojureScript 实例，和真实用户共用同一套渲染代码，保证导出结果与画布所见一致。渲染热点由 `render-wasm` 承担——一个用 Rust 写的、基于 Skia 的 WASM 渲染引擎，浏览器内编辑器和无头导出器共享这套代码。2.17 起，原型查看器已从 SVG 渲染切换到这个 Skia 引擎。

**存储全部用成熟组件**。PostgreSQL 存用户、文件与变更历史；Valkey（Redis 协议兼容）负责协作通知的协调，2.11 起兼作缓存；媒体资源走可插拔对象存储后端，本地文件系统或 S3 兼容服务（如 MinIO）二选一。没有自研存储组件，运维负担可控。

### 实时协作如何工作

Penpot 的协作不是教科书式的操作变换（OT）或 CRDT。从源码看，后端的 WebSocket 服务自我描述为「文件协作编辑的通知服务」：每个编辑操作被拆解为细粒度变更（新增对象、修改属性、删除对象、移动页面等），后端将变更持久化到 PostgreSQL，同时经消息总线向同文件的所有协作者广播；各客户端应用收到的变更来保持画布同步。

这种「事件广播 + 客户端应用」的模型结构简单、易排查，但与 OT/CRDT 相比，在极端并发冲突下的合并语义更弱——这是理解 Penpot 协作边界时需要知道的取舍。日常团队协作场景（多人同时编辑同一文件的不同区域）工作良好。

### 渲染的演进路线

画布渲染最初基于 SVG/DOM。随着文件变大，Penpot 把性能热点逐步迁向 Rust：2.16 引入 WebGL 渲染（beta，用户可在偏好中开启），2.17 原型查看器切换到 Skia WASM 引擎。方向明确——用浏览器原生能力跑不动的地方，交给编译到 WASM 的 Rust 代码。

## 从 2.0 到 2.18：特性演进时间线

Penpot 2.0 于 2024 年 4 月发布，此后的版本节奏稳定在每两到三个月一个 minor 版本。把关键特性放回时间线，比孤立地谈「2.0 新特性」更有用：

| 版本 | 发布时间 | 关键特性 |
| --- | --- | --- |
| 2.0 | 2024-04 | CSS Grid 布局、组件系统重写、UI 重设计、明暗主题 |
| 2.3 | 2024-11 | 插件系统（TypeScript 插件 API） |
| 2.6 | 2025-04 | 原生设计令牌：支持引用别名、数学运算、令牌集与多维主题 |
| 2.10 | 2025-09 | 组件变体（Variants） |
| 2.11 | 2025-11 | Valkey 兼作缓存；文件数据存储后端可配置 |
| 2.15 | 2026-05 | MCP 服务器集成 |
| 2.16 | 2026-06 | WebGL 渲染（beta） |
| 2.17 | 2026-07 | 原型查看器切换 Skia WASM 渲染 |
| 2.18 | 2026-09 | Admin Console 管理控制台 |

其中三个特性值得单独展开。

**原生设计令牌（2.6）**。设计令牌是设计系统里「设计决策」的最小单元：一个颜色令牌代表「品牌主色」这个决策，改动令牌定义，所有引用它的组件自动更新。Penpot 官方称自己是第一个把设计令牌做成原生功能的设计工具——令牌作为独立面板贯穿编辑器，支持令牌引用（令牌 A 指向令牌 B）、值运算（间距 = 基准值 × 2）、令牌集分组与多维主题管理，导入导出遵循 W3C DTCG 标准。多数竞品的令牌能力靠插件补齐，Penpot 把它做进了核心数据模型，令牌因此能参与组件、样式和变体的联动。

**组件变体（2.10）**。一个按钮组件可以有 default、hover、disabled 多个状态变体，切换变体保留覆盖属性。这是设计系统工作流里补上的一块关键拼图——2024 年组件系统重写时它还没就位，等了一年半。

**MCP 服务器（2.15）**。MCP（Model Context Protocol）是 AI 代理访问外部工具的标准协议。Penpot 的 MCP 服务器让 AI 代理可以读取设计文件结构、查询组件与令牌、在画布上创建内容，把设计系统变成 AI 编码工作流可消费的上下文。自托管部署中通过 `enable-mcp` 标志开启。这一步让「设计即代码」延伸成了「设计即 AI 可读的数据」。

## 一次设计到代码的完整流转

把上面的机制串成一个真实任务：设计师要交付一个带悬停状态的按钮。

1. **建模**：设计师在画布上创建 Frame，应用 Flex 布局设定内边距与间距；颜色不直接选色值，而是应用令牌 `color/primary`；组件建好后创建 hover 变体。
2. **检查**：开发者打开 Inspect 标签页，看到的是这段布局的 CSS（`display: flex`、间距、颜色）和图形的 SVG 路径——因为画布语义就是 CSS 语义，代码不需要人工翻译。
3. **同步**：品牌色变更时，改一处令牌定义，按钮及所有引用该令牌的组件同步更新；开发者侧只需重新拉取令牌 JSON。
4. **自动化（可选）**：团队的 AI 代码助手通过 MCP 服务器读取该文件，拿到组件结构、令牌与变体定义，直接生成带状态的组件代码；设计文件更新时，webhook 通知 CI 或外部系统。

整条链路没有任何一步依赖私有格式解析，这是 Penpot 与「导出标注图」式工具的本质区别。

## 部署：SaaS 与自托管

### 官方 SaaS

访问 [design.penpot.app](https://design.penpot.app) 注册即用。Professional 计划免费，但有限制：最多 8 名编辑成员（查看者不限）、10GB 存储、7 天版本历史。超出后按 Enterprise 计划付费（25 美元/成员/月），获得 SSO、IP 白名单、25GB 存储、90 天历史与管理功能。

### Docker 自托管

官方方式是直接下载 compose 文件，不需要克隆整个仓库：

```bash
curl -o docker-compose.yaml https://raw.githubusercontent.com/penpot/penpot/main/docker/images/docker-compose.yaml

docker compose -p penpot -f docker-compose.yaml up -d
```

启动后访问 `http://localhost:9001`。三个要点：

- 用 `PENPOT_VERSION` 环境变量固定版本（如 `PENPOT_VERSION=2.18.0`），避免被动升级
- 修改 `PENPOT_SECRET_KEY` 的默认值
- 通过 HTTP（非 HTTPS）访问时需加 `disable-secure-session-cookies` 标志，但仅限测试环境——生产环境剪贴板等功能依赖安全上下文

升级建议小步进行，逐版本更新；从 1.x 升 2.x 有独立的数据迁移流程，官方文档有专门章节。

### Kubernetes

官方 Helm 仓库：

```bash
helm repo add penpot http://helm.penpot.app
helm install my-release penpot/penpot
```

生产部署需要决策的事项：外部 PostgreSQL（compose 内置实例仅适合开发）、S3 兼容对象存储、SMTP 邮件服务（注册验证与密码重置）、HTTPS 反向代理。2.18 起如需管理控制台，还要按文档添加 `penpot-admin-console` 服务并启用 `enable-admin-console`。

### 资源配置

官方推荐配置是 4 核 CPU、16GB 内存，并说明该配置足以支撑数千名用户；数据库建议初始 50–100GB 磁盘并可弹性扩展，每增加一名编辑者约追加 5GB。Valkey 实例无需磁盘，`maxmemory 128mb` 配合 `volatile-lfu` 淘汰策略即可满足大多数实例。

## 采用建议

**适合现在就上**：需要数据自持有的团队（合规、隐私要求）、开源项目做设计协作、预算受限但需要设计系统工作流的小团队、想用 AI 消费设计资产的工程组织（MCP 是当前独有卖点）。

**需要权衡**：重度依赖 Figma 生态插件链的团队——Penpot 插件生态在增长但体量仍有差距；已有大量历史 Figma 文件的团队，迁移有一次性成本，组件库、历史文件与原型交互都需要重新梳理，建议先拿一个非关键项目试点。

**可以再等等**：对实时协作有极端并发要求的超大型多人同文件场景，事件广播模型的合并语义弱于 OT/CRDT 方案，建议先做压力测试。

## 常见问题

**Penpot 和 Figma 的核心差异是什么？**

四点：许可证（MPL-2.0 开源 vs 闭源商业）、部署（可完全自托管 vs 仅云服务）、数据格式（开放标准 vs 私有格式）、商业模式（SaaS 免费加企业订阅 vs 按席位订阅）。功能面上 Figma 的成熟度与生态领先，Penpot 的差异在于资产所有权和开放性。

**Clojure 技术栈会影响性能吗？**

对日常使用影响有限——渲染热点已经逐步交给 Rust/WASM（Skia 引擎），Clojure 后端跑在成熟的 JVM 上。官方 4 核/16GB 的推荐配置支撑数千用户的说法，以及 2.16 以来的渲染架构演进，说明性能问题的解法是架构性的，不依赖换语言。

**项目终止了，我的设计资产怎么办？**

自托管场景下，PostgreSQL 数据和对象存储资源都在自己的基础设施里；SaaS 场景下，设计可导出为 SVG/CSS/HTML 与 W3C 标准的令牌 JSON。MPL-2.0 保证源码在许可证有效期内持续可用。无法保证的是没有社区维护后的功能演进——开放标准保的是「资产可用」，不是「平台永续」。

## 相关资源

- 仓库：[penpot/penpot](https://github.com/penpot/penpot)
- 用户指南：[help.penpot.app/user-guide](https://help.penpot.app/user-guide/)
- 技术文档与架构说明：[help.penpot.app/technical-guide](https://help.penpot.app/technical-guide/)
- 自托管入门：[help.penpot.app/technical-guide/getting-started](https://help.penpot.app/technical-guide/getting-started/)
- 贡献指南：[help.penpot.app/contributing-guide](https://help.penpot.app/contributing-guide/)
- 插件市场：[penpot.app/penpothub/plugins](https://penpot.app/penpothub/plugins)
- 设计令牌介绍：[penpot.dev/collaboration/design-tokens](https://penpot.dev/collaboration/design-tokens)
- 社区论坛：[community.penpot.app](https://community.penpot.app/)
